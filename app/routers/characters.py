from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response, HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Any
from ..database import get_db
from ..dependencies import require_user
from ..models.character import (
    Character, CharacterClass, StatRollSet, CharacterChoice,
    CharacterFeat, CharacterSpell, CharacterEquipment,
    SkillProficiency, ToolProficiency, LanguageProficiency, WeaponMasteryUnlock,
    CharacterResource,
)
from ..models.content import DnDClass, Background, Feat, Spell, Equipment, Species, Subclass
from ..services.export import character_to_dict, character_to_sheet_dict, compute_ac
from ..services.levelup_rules import (
    required_steps, auto_grants, subclass_auto_grants, max_spell_level,
    METAMAGIC_OPTIONS, ELDRITCH_INVOCATIONS, AASIMAR_REVELATIONS, _species_lineage_spells,
    CLASS_ALWAYS_PREPARED, BATTLE_MASTER_MANEUVERS, BARD_PREPARED_BY_LEVEL,
)
from ..config import settings
from ..services.pdf import render_character_pdf, render_character_html
from .encounter import _broadcast_state
import random
import re
from sqlalchemy import func

router = APIRouter(prefix="/api/characters", tags=["characters"])


# ---------------------------------------------------------------------------
# Species spell-grant parser
# ---------------------------------------------------------------------------

_CANTRIP_RE = re.compile(
    r'\bknow(?:\s+the)?\s+([A-Z][A-Za-z ]+?)(?:\s+and\s+([A-Z][A-Za-z ]+?))?\s*(?:cantrips?|\(([^)]+)\)|(?=[.,;\n]|$))',
    re.IGNORECASE,
)
_PREPARED_RE = re.compile(
    r'Always have\s+([A-Z][A-Za-z ]+?)\s+prepared[;,.]?\s*(.*)',
    re.IGNORECASE | re.DOTALL,
)


def _parse_species_spell_grants(species, lineage_name: str | None) -> list[dict]:
    """Return [{"name": str, "notes": str|None}] for each spell the species grants."""
    grants: list[dict] = []

    def extract(text: str):
        if not text:
            return
        for m in _CANTRIP_RE.finditer(text):
            note = f"({m.group(3)})" if m.group(3) else None
            grants.append({"name": m.group(1).strip(), "notes": note})
            if m.group(2):
                grants.append({"name": m.group(2).strip(), "notes": None})
        for m in _PREPARED_RE.finditer(text):
            note_text = m.group(2).strip().rstrip('.')
            grants.append({"name": m.group(1).strip(), "notes": note_text or None})

    for trait in (species.traits or []):
        if not re.search(r'lineage|legacy|ancestry', trait.get('name', ''), re.IGNORECASE):
            extract(trait.get('description', ''))

    if lineage_name and species.lineages:
        for lineage in species.lineages:
            if lineage.get('name') == lineage_name:
                extract(lineage.get('description', ''))
                break

    return grants


# ---------------------------------------------------------------------------
# Pydantic models for step payloads
# ---------------------------------------------------------------------------

class CreateCharacterIn(BaseModel):
    created_by_display_name: str
    character_name: str


class StepIdentityIn(BaseModel):
    created_by_display_name: str
    character_name: str


class StepSpeciesIn(BaseModel):
    species_id: int
    species_lineage: str | None = None
    species_size_choice: str | None = None
    species_skill_choices: list[str] = []


class StepBackgroundIn(BaseModel):
    background_id: int
    tool_proficiency_choice: str | None = None  # resolved when background offers a choice


class StepClassIn(BaseModel):
    class_id: int


class StepStatsIn(BaseModel):
    base_attributes: dict[str, int]   # {"str":15,"dex":14,...}
    background_asi: dict[str, int]    # {"str":2,"wis":1}


class StepFeaturesIn(BaseModel):
    choices: list[dict[str, Any]]     # [{"feature_key":"fighting_style","choice_value":"Archery"}]


class StepSkillsIn(BaseModel):
    skills: list[str]                 # chosen class skills
    languages: list[str]
    class_tool_choices: list[str] = []  # tool proficiencies chosen this step (class-granted)


class StepEquipmentIn(BaseModel):
    class_option: str                 # "A", "B", "C"
    background_option: str            # "A", "B"
    resolved_items: list[dict]        # resolved item list (frontend resolves choices)


class StepSpellsIn(BaseModel):
    cantrip_ids: list[int]
    spell_ids: list[int]


class StepBioIn(BaseModel):
    alignment: str | None = None
    bio: str | None = None


class BioUpdateIn(BaseModel):
    bio: str | None = None
    age: int | None = None
    height: str | None = None
    weight: str | None = None
    deity: str | None = None
    journal: str | None = None


class HpAdjustIn(BaseModel):
    delta: int | None = None   # relative: +5 or -3
    set: int | None = None     # absolute override


class SpellSlotsIn(BaseModel):
    used: dict[str, int]       # {"1": 2, "2": 0}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_char(char_id: int, db: Session) -> Character:
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404, "Character not found")
    return char


def _check_owner(char: Character, user: dict) -> None:
    if char.owner_email and char.owner_email != user.get("email"):
        raise HTTPException(403, "Not your character")


def _check_owner_or_admin(char: Character, user: dict) -> None:
    is_owner = char.owner_email == user.get("email")
    is_admin = user.get("email") == settings.admin_email.lower()
    if not (is_owner or is_admin):
        raise HTTPException(403, "Not authorized")


def _require_admin(user: dict) -> None:
    if user.get("email") != settings.admin_email.lower():
        raise HTTPException(403, "Admin only")


def _compute_hp(char: Character, db: Session) -> int:
    cc = char.character_classes[0] if char.character_classes else None
    if not cc:
        return 0
    cls = db.get(DnDClass, cc.class_id)
    con_score = 0
    if char.base_attributes:
        con_score = char.base_attributes.get("con", 10)
    if char.background_asi:
        con_score += char.background_asi.get("con", 0)
    con_mod = (con_score - 10) // 2
    return (cls.hit_die if cls else 8) + con_mod


def _char_summary(char: Character) -> dict:
    cc = char.character_classes[0] if char.character_classes else None
    return {
        "id": char.id,
        "created_by_display_name": char.created_by_display_name,
        "character_name": char.character_name,
        "species_id": char.species_id,
        "species_name": char.species.name if char.species else None,
        "background_id": char.background_id,
        "background_name": char.background.name if char.background else None,
        "class_id": cc.class_id if cc else None,
        "class_name": cc.dnd_class.name if cc and cc.dnd_class else None,
        "level": cc.level if cc else None,
        "alignment": char.alignment,
        "bio": char.bio,
        "base_attributes": char.base_attributes,
        "background_asi": char.background_asi,
        "hp_max": char.hp_max,
        "hp_current": char.hp_current,
        "speed": char.speed,
        "stat_roll_locked": char.stat_roll_locked,
        "wizard_step": char.wizard_step,
        "is_complete": char.is_complete,
        "tool_proficiency_choice": char.tool_proficiency_choice,
        "equipment_choice": char.equipment_choice,
        "choices": [{"feature_key": c.feature_key, "choice_value": c.choice_value} for c in char.choices],
        "skill_proficiencies": [{"skill_name": s.skill_name, "source": s.source} for s in char.skill_proficiencies],
        "tool_proficiencies": [{"tool_name": t.tool_name, "source": t.source} for t in char.tool_proficiencies],
        "language_proficiencies": [{"language_name": l.language_name, "source": l.source} for l in char.language_proficiencies],
        "weapon_mastery_unlocks": [w.weapon_name for w in char.weapon_mastery_unlocks],
        "feats": [{"feat_id": f.feat_id, "feat_name": f.feat.name if f.feat else None, "source": f.source} for f in char.feats],
        "spells": [{"spell_id": s.spell_id, "spell_name": s.spell.name if s.spell else None, "level": s.spell.level if s.spell else None, "prepared": s.prepared} for s in char.spells],
        "equipment": [{"equipment_id": e.equipment_id, "name": e.equipment_item.name if e.equipment_item else e.custom_name, "quantity": e.quantity, "equipped": e.equipped} for e in char.equipment],
    }


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("")
def create_character(data: CreateCharacterIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = Character(
        created_by_display_name=data.created_by_display_name,
        character_name=data.character_name,
        owner_email=user["email"],
        wizard_step=2,
    )
    db.add(char)
    db.commit()
    db.refresh(char)
    return {"id": char.id}


@router.get("/{char_id}")
def get_character(char_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    return _char_summary(char)


# --- Step 2: Species ---
@router.post("/{char_id}/step/species")
def save_species(char_id: int, data: StepSpeciesIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    char.species_id = data.species_id
    char.species_lineage = data.species_lineage
    char.species_size_choice = data.species_size_choice
    species = db.get(Species, data.species_id)
    if species:
        char.speed = species.speed
        # Apply lineage speed override if present (e.g. Wood Elf 35 ft.)
        if data.species_lineage and species.lineages:
            for lin in species.lineages:
                if lin.get("name") == data.species_lineage and lin.get("speed"):
                    char.speed = lin["speed"]
                    break
        # Clear previous species spell grants and re-derive from new selection
        for cs in list(char.spells):
            if cs.source == "species":
                db.delete(cs)
        db.flush()
        for grant in _parse_species_spell_grants(species, data.species_lineage):
            spell = db.query(Spell).filter(
                func.lower(Spell.name) == grant["name"].lower()
            ).first()
            if spell:
                db.add(CharacterSpell(
                    character_id=char.id,
                    spell_id=spell.id,
                    prepared=True,
                    source="species",
                    notes=grant["notes"],
                ))
    # Store species trait skill choices (e.g. Keen Senses: Insight/Perception/Survival)
    # Clear old species_skill choices first so re-selecting species is idempotent
    for old in list(char.choices):
        if old.feature_key.startswith("species_skill_"):
            db.delete(old)
    db.flush()
    for skill in data.species_skill_choices:
        db.add(CharacterChoice(
            character_id=char.id,
            feature_key="species_skill_keen_senses",
            choice_value=skill,
        ))

    char.wizard_step = max(char.wizard_step, 3)
    db.commit()
    return {"ok": True}


# --- Step 3: Background ---
@router.post("/{char_id}/step/background")
def save_background(char_id: int, data: StepBackgroundIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    char.background_id = data.background_id
    char.tool_proficiency_choice = data.tool_proficiency_choice

    bg = db.get(Background, data.background_id)
    if bg:
        # Skill proficiencies from background
        for sp in list(char.skill_proficiencies):
            if sp.source == "background":
                db.delete(sp)
        for skill in (bg.skill_proficiencies or []):
            db.add(SkillProficiency(character_id=char.id, skill_name=skill, source="background"))

        # Tool proficiency
        for tp in list(char.tool_proficiencies):
            if tp.source == "background":
                db.delete(tp)
        tool = data.tool_proficiency_choice or bg.tool_proficiency
        if tool and "choose" not in (tool or "").lower():
            db.add(ToolProficiency(character_id=char.id, tool_name=tool, source="background"))

        # Origin feat
        if bg.origin_feat_name:
            feat = db.query(Feat).filter(
                Feat.name.ilike(bg.origin_feat_name)
            ).first()
            for cf in list(char.feats):
                if cf.source == "background":
                    db.delete(cf)
            if feat:
                db.add(CharacterFeat(character_id=char.id, feat_id=feat.id, source="background"))

    char.wizard_step = max(char.wizard_step, 4)
    db.commit()
    return {"ok": True}


# --- Step 4: Class ---
@router.post("/{char_id}/step/class")
def save_class(char_id: int, data: StepClassIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    # Remove existing class entries
    for cc in list(char.character_classes):
        db.delete(cc)
    cls = db.get(DnDClass, data.class_id)
    if not cls:
        raise HTTPException(400, "Class not found")
    db.add(CharacterClass(character_id=char.id, class_id=data.class_id, level=1))
    char.wizard_step = max(char.wizard_step, 5)
    db.commit()
    return {"ok": True}


# --- Step 5: Stats ---
@router.post("/{char_id}/step/stats")
def save_stats(char_id: int, data: StepStatsIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    if char.stat_roll_locked:
        raise HTTPException(403, "Stats are locked. Ask your DM to unlock.")
    char.base_attributes = data.base_attributes
    char.background_asi = data.background_asi
    char.hp_max = _compute_hp(char, db)
    char.hp_current = char.hp_max
    char.stat_roll_locked = True
    char.wizard_step = max(char.wizard_step, 6)
    db.commit()
    return {"ok": True, "hp_max": char.hp_max}


# --- Stat roll ---
@router.post("/{char_id}/roll-stats")
def roll_stats(char_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    if char.stat_roll_locked:
        raise HTTPException(403, "Stats are locked.")
    # Remove previous rolls
    for s in list(char.stat_roll_sets):
        db.delete(s)
    sets = []
    for _ in range(3):
        rolls = sorted([sum(sorted([random.randint(1, 6) for _ in range(4)])[1:]) for _ in range(6)], reverse=True)
        db.add(StatRollSet(character_id=char.id, rolls=rolls, is_manual=False))
        sets.append(rolls)
    db.commit()
    return {"sets": sets}


# --- Step 6: Features ---
@router.post("/{char_id}/step/features")
def save_features(char_id: int, data: StepFeaturesIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    # Clear existing feature choices
    for c in list(char.choices):
        db.delete(c)
    # Clear existing weapon masteries
    for wm in list(char.weapon_mastery_unlocks):
        db.delete(wm)
    db.flush()

    for choice in data.choices:
        key = choice["feature_key"]
        value = choice["choice_value"]
        if key.startswith("weapon_mastery"):
            if isinstance(value, list):
                for wname in value:
                    db.add(WeaponMasteryUnlock(character_id=char.id, weapon_name=wname))
            else:
                db.add(WeaponMasteryUnlock(character_id=char.id, weapon_name=value))
        else:
            db.add(CharacterChoice(character_id=char.id, feature_key=key, choice_value=value))

    char.wizard_step = max(char.wizard_step, 7)
    db.commit()
    return {"ok": True}


# --- Step 7: Skills ---
@router.post("/{char_id}/step/skills")
def save_skills(char_id: int, data: StepSkillsIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    # Remove class-sourced skills, tool proficiencies, and all language proficiencies
    for sp in list(char.skill_proficiencies):
        if sp.source == "class":
            db.delete(sp)
    for tp in list(char.tool_proficiencies):
        if tp.source == "class":
            db.delete(tp)
    for lp in list(char.language_proficiencies):
        db.delete(lp)
    db.flush()

    for skill in data.skills:
        db.add(SkillProficiency(character_id=char.id, skill_name=skill, source="class"))
    for lang in data.languages:
        db.add(LanguageProficiency(character_id=char.id, language_name=lang, source="player_choice"))

    # Class tool proficiencies — fixed grants + player-chosen ones
    cc = char.character_classes[0] if char.character_classes else None
    cls = cc.dnd_class if cc else None
    if cls and cls.tool_proficiencies:
        for tool_entry in cls.tool_proficiencies:
            is_choice = any(kw in tool_entry.lower() for kw in ("choose", "your choice", " or "))
            if not is_choice:
                db.add(ToolProficiency(character_id=char.id, tool_name=tool_entry, source="class"))
    # Player-chosen tool proficiencies (Bard instruments, Monk artisan/instrument pick)
    for tool_name in (data.class_tool_choices or []):
        if tool_name:
            db.add(ToolProficiency(character_id=char.id, tool_name=tool_name, source="class"))

    char.wizard_step = max(char.wizard_step, 8)
    db.commit()
    return {"ok": True}


# --- Step 8: Equipment ---
@router.post("/{char_id}/step/equipment")
def save_equipment(char_id: int, data: StepEquipmentIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    for ce in list(char.equipment):
        db.delete(ce)
    db.flush()

    char.equipment_choice = {
        "class": data.class_option,
        "background": data.background_option,
    }

    for item in data.resolved_items:
        eq = db.query(Equipment).filter(Equipment.name.ilike(item["name"])).first()
        db.add(CharacterEquipment(
            character_id=char.id,
            equipment_id=eq.id if eq else None,
            custom_name=None if eq else item["name"],
            quantity=item.get("qty", 1),
            equipped=item.get("equipped", False),
        ))

    char.wizard_step = max(char.wizard_step, 9)
    db.commit()
    return {"ok": True}


# --- Step 9: Spells ---
@router.post("/{char_id}/step/spells")
def save_spells(char_id: int, data: StepSpellsIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    for cs in list(char.spells):
        if cs.source != "species":
            db.delete(cs)
    db.flush()

    cc = char.character_classes[0] if char.character_classes else None
    src_class_id = cc.class_id if cc else None

    for sid in data.cantrip_ids + data.spell_ids:
        db.add(CharacterSpell(
            character_id=char.id,
            spell_id=sid,
            prepared=True,
            source="class",
            source_class_id=src_class_id,
        ))

    # Auto-add class always-prepared spells (e.g. Ranger Favored Enemy → Hunter's Mark)
    cls_obj = db.get(DnDClass, cc.class_id) if cc else None
    if cls_obj:
        existing_ids = {sid for sid in data.cantrip_ids + data.spell_ids}
        existing_ids |= {cs.spell_id for cs in char.spells if cs.source == "species"}
        for min_lvl, spell_names in CLASS_ALWAYS_PREPARED.get(cls_obj.name, {}).items():
            for name in spell_names:
                spell = db.query(Spell).filter(Spell.name == name).first()
                if spell and spell.id not in existing_ids:
                    db.add(CharacterSpell(
                        character_id=char.id,
                        spell_id=spell.id,
                        prepared=True,
                        always_prepared=True,
                        source="class",
                        source_class_id=cc.class_id,
                        notes="Favored Enemy",
                    ))
                    existing_ids.add(spell.id)

    char.wizard_step = max(char.wizard_step, 10)
    db.commit()
    return {"ok": True}


@router.get("/{char_id}/spells")
def get_character_spells(char_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)
    return [
        {
            "id": cs.spell.id,
            "name": cs.spell.name,
            "level": cs.spell.level,
            "source": cs.source,
            "notes": cs.notes,
            "school": cs.spell.school,
            "description": cs.spell.description,
            "casting_time": cs.spell.casting_time,
            "concentration": cs.spell.concentration,
            "ritual": cs.spell.ritual,
        }
        for cs in char.spells
    ]


# --- Step 10: Bio ---
@router.post("/{char_id}/step/bio")
def save_bio(char_id: int, data: StepBioIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    char.alignment = data.alignment
    char.bio = data.bio
    char.wizard_step = max(char.wizard_step, 10)
    char.is_complete = True
    db.commit()
    return {"ok": True}


# --- HP & spell slot tracking ---
@router.get("/{char_id}/hp")
def get_hp(char_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)
    return {
        "hp_current": char.hp_current,
        "hp_max": char.hp_max,
        "conditions": char.conditions or [],
    }


@router.post("/{char_id}/hp")
def adjust_hp(char_id: int, data: HpAdjustIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _require_admin(user)
    if data.set is not None:
        char.hp_current = max(0, min(data.set, char.hp_max or 0))
    elif data.delta is not None:
        current = char.hp_current or 0
        char.hp_current = max(0, min(current + data.delta, char.hp_max or 0))
    else:
        raise HTTPException(400, "Provide 'delta' or 'set'")
    db.commit()
    return {"hp_current": char.hp_current, "hp_max": char.hp_max}


@router.post("/{char_id}/spell-slots")
def update_spell_slots(char_id: int, data: SpellSlotsIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)
    char.spell_slots_used = data.used
    db.commit()
    return {"spell_slots_used": char.spell_slots_used}


@router.patch("/{char_id}/bio")
def update_bio(char_id: int, data: BioUpdateIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)
    is_admin = user.get("is_admin", False)
    physical_blocked = bool(char.physical_locked) and not is_admin
    if data.bio is not None:
        char.bio = data.bio
    if data.age is not None and not physical_blocked:
        char.age = data.age
    if data.height is not None and not physical_blocked:
        char.height = data.height
    if data.weight is not None and not physical_blocked:
        char.weight = data.weight
    if data.deity is not None and not physical_blocked:
        char.deity = data.deity
    if data.journal is not None:
        char.journal = data.journal
    db.commit()
    return {"ok": True}


@router.post("/{char_id}/bio/lock")
def lock_physical(char_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    from fastapi import HTTPException
    char = _get_char(char_id, db)
    _check_owner(char, user)
    if not char.height or not char.weight:
        raise HTTPException(status_code=400, detail="Height and weight must be set before locking.")
    char.physical_locked = True
    db.commit()
    return {"physical_locked": True}


@router.get("/{char_id}/sheet-data")
def sheet_data(char_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)
    return character_to_sheet_dict(char, db)


# ---------------------------------------------------------------------------
# Equipment management (admin-only)
# ---------------------------------------------------------------------------

class AddEquipmentIn(BaseModel):
    equipment_id: int | None = None
    custom_name: str | None = None
    quantity: int = 1
    item_type: str | None = None

@router.post("/{char_id}/equipment")
def add_equipment(char_id: int, data: AddEquipmentIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    _require_admin(user)
    char = _get_char(char_id, db)
    if not data.equipment_id and not (data.custom_name or "").strip():
        raise HTTPException(400, "Provide equipment_id or custom_name")
    entry = CharacterEquipment(
        character_id=char.id,
        equipment_id=data.equipment_id or None,
        custom_name=data.custom_name.strip() if data.custom_name else None,
        quantity=max(1, data.quantity),
        equipped=False,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    item = entry.equipment_item
    return {
        "entry_id": entry.id,
        "name": item.name if item else entry.custom_name,
        "quantity": entry.quantity,
        "equipped": entry.equipped,
        "item_type": item.item_type if item else data.item_type,
        "category": item.category if item else None,
        "damage": item.damage if item else None,
        "damage_type": item.damage_type if item else None,
        "properties": item.properties if item else [],
        "mastery_property": item.mastery_property if item else None,
        "ac_formula": item.ac_formula if item else None,
    }

@router.delete("/{char_id}/equipment/{entry_id}")
def remove_equipment(char_id: int, entry_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    _require_admin(user)
    char = _get_char(char_id, db)
    entry = db.get(CharacterEquipment, entry_id)
    if not entry or entry.character_id != char.id:
        raise HTTPException(404)
    db.delete(entry)
    db.commit()
    return {"ok": True}

@router.patch("/{char_id}/equipment/{entry_id}/quantity")
def update_equipment_quantity(char_id: int, entry_id: int, quantity: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    _require_admin(user)
    char = _get_char(char_id, db)
    entry = db.get(CharacterEquipment, entry_id)
    if not entry or entry.character_id != char.id:
        raise HTTPException(404)
    if quantity < 1:
        raise HTTPException(400, "Quantity must be at least 1")
    entry.quantity = quantity
    db.commit()
    return {"ok": True, "quantity": entry.quantity}


class EquipToggleIn(BaseModel):
    equipped: bool

@router.patch("/{char_id}/equipment/{entry_id}/equip")
def toggle_equipped(char_id: int, entry_id: int, data: EquipToggleIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)
    entry = db.get(CharacterEquipment, entry_id)
    if not entry or entry.character_id != char.id:
        raise HTTPException(404)

    item = entry.equipment_item
    item_type = item.item_type if item else None

    # Equipping a new armor auto-unequips any other equipped armor
    if data.equipped and item_type == "armor":
        for ce in char.equipment:
            if ce.id != entry_id and ce.equipment_item and ce.equipment_item.item_type == "armor":
                ce.equipped = False

    entry.equipped = data.equipped
    db.commit()

    # Recompute AC using shared compute_ac helper (handles Unarmored Defense)
    base = char.base_attributes or {}
    asi = char.background_asi or {}
    attrs = {k: base.get(k, 10) + asi.get(k, 0) for k in ("str", "dex", "con", "int", "wis", "cha")}
    ac, ac_source = compute_ac(char, attrs, db)

    return {"ok": True, "entry_id": entry_id, "equipped": entry.equipped, "ac": ac, "ac_source": ac_source}


# ---------------------------------------------------------------------------
# Prepared spells
# ---------------------------------------------------------------------------

class PreparedSpellsIn(BaseModel):
    spell_ids: list[int]

@router.patch("/{char_id}/prepared-spells")
def update_prepared_spells(char_id: int, data: PreparedSpellsIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)

    cc = char.character_classes[0] if char.character_classes else None
    if not cc:
        raise HTTPException(400, "No class assigned")

    cls = cc.dnd_class
    class_lower = cls.name.lower()
    level = cc.level

    PREP_CASTERS = {"bard", "cleric", "druid", "paladin", "ranger", "wizard"}
    if class_lower not in PREP_CASTERS:
        raise HTTPException(400, "Class does not prepare spells")

    base = char.base_attributes or {}
    asi_bonus = char.background_asi or {}
    a = {k: base.get(k, 10) + asi_bonus.get(k, 0) for k in ("str", "dex", "con", "int", "wis", "cha")}
    ab_map = {"intelligence": "int", "wisdom": "wis", "charisma": "cha"}
    sp_ab_key = ab_map.get((cls.spellcasting_ability or "").lower(), "int")
    sp_mod = (a.get(sp_ab_key, 10) - 10) // 2

    if class_lower == "bard":
        prepared_max = BARD_PREPARED_BY_LEVEL.get(level, 4)
    elif class_lower in ("cleric", "druid", "wizard"):
        prepared_max = max(1, sp_mod + level)
    else:  # paladin, ranger
        prepared_max = max(1, sp_mod + (level // 2))

    requested_ids = set(data.spell_ids)

    # Count non-always-prepared, non-cantrip, non-species/arcanum spells being set
    count = sum(
        1 for cs in char.spells
        if cs.spell_id in requested_ids
        and not cs.always_prepared
        and cs.source not in ("species", "arcanum")
        and cs.spell and cs.spell.level > 0
    )
    if count > prepared_max:
        raise HTTPException(400, f"Cannot prepare more than {prepared_max} spells (requested {count})")

    for cs in char.spells:
        if cs.always_prepared or cs.source in ("species", "arcanum"):
            continue
        if cs.spell and cs.spell.level == 0:
            continue
        cs.prepared = cs.spell_id in requested_ids

    db.commit()
    return {"ok": True, "prepared_count": count, "prepared_max": prepared_max}


# ---------------------------------------------------------------------------
# Mastery swap
# ---------------------------------------------------------------------------

class MasterySwapIn(BaseModel):
    remove: str
    add: str

@router.patch("/{char_id}/masteries/swap")
def swap_mastery(char_id: int, data: MasterySwapIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)

    remove_name = (data.remove or "").strip()
    add_name = (data.add or "").strip()
    if not remove_name or not add_name:
        raise HTTPException(400, "Both 'remove' and 'add' weapon names are required")
    if remove_name == add_name:
        raise HTTPException(400, "remove and add must be different weapons")

    current = {wu.weapon_name: wu for wu in char.weapon_mastery_unlocks}
    if remove_name not in current:
        raise HTTPException(400, f"'{remove_name}' is not a current mastery")

    already_mastered = set(current.keys())
    if add_name in already_mastered:
        raise HTTPException(400, f"'{add_name}' is already mastered")

    from ..models.content import Equipment as EquipmentModel
    from ..services.export import _CATEGORY_MAP
    prof_raw = [wp.proficiency_type for wp in char.weapon_proficiencies]
    prof_set: set[str] = set()
    for pt in prof_raw:
        if pt in _CATEGORY_MAP:
            prof_set |= _CATEGORY_MAP[pt]
        else:
            prof_set.add(pt)

    weapon_exists = db.query(EquipmentModel).filter(
        EquipmentModel.name == add_name,
        EquipmentModel.item_type == "weapon"
    ).first()
    if not weapon_exists:
        raise HTTPException(400, f"'{add_name}' is not a known weapon")
    if add_name not in prof_set:
        raise HTTPException(400, f"Not proficient with '{add_name}'")

    db.delete(current[remove_name])
    new_mastery = WeaponMasteryUnlock(character_id=char.id, weapon_name=add_name)
    db.add(new_mastery)
    db.commit()
    return {"ok": True, "removed": remove_name, "added": add_name}


# ---------------------------------------------------------------------------
# Level-up
# ---------------------------------------------------------------------------

class HpChoice(BaseModel):
    method: str = "average"    # "roll" | "manual" | "average"
    die_value: int | None = None   # the raw die roll (before CON mod)
    draconic_bonus: int = 0

class LevelUpIn(BaseModel):
    hp: HpChoice = HpChoice()
    choices: dict[str, Any] = {}   # step_id → payload


def _apply_hp(char, cc, cls, hp: HpChoice, next_level: int) -> int:
    """Compute HP gain, log it, and update char.hp_max/hp_current. Returns total gain."""
    base_attrs = char.base_attributes or {}
    bg_asi = char.background_asi or {}
    con_total = base_attrs.get("con", 10) + bg_asi.get("con", 0)
    con_mod = (con_total - 10) // 2
    average = cls.hit_die // 2 + 1
    draconic = hp.draconic_bonus or 0

    if hp.method == "manual" and hp.die_value is not None:
        die_value = max(1, min(hp.die_value, cls.hit_die))
    elif hp.method == "roll" and hp.die_value is not None:
        die_value = max(average, max(1, min(hp.die_value, cls.hit_die)))  # floor at average
    else:
        die_value = average

    total = die_value + con_mod + draconic

    log = list(char.hp_roll_log or [])
    log.append({"level": next_level, "method": hp.method, "die_value": die_value,
                 "con_mod": con_mod, "draconic_bonus": draconic, "total": total})
    char.hp_roll_log = log

    char.hp_max = (char.hp_max or 0) + total
    char.hp_current = (char.hp_current or 0) + total
    return total


def _recompute_hp_from_con_delta(char, old_con_mod: int, new_con_mod: int) -> int:
    """Retroactively adjust hp_max/hp_current when the Con modifier changes.

    Each entry in hp_roll_log represents one level (L2+). L1 HP (set at
    character creation) is not logged, so total levels = len(log) + 1.
    """
    delta_mod = new_con_mod - old_con_mod
    if delta_mod == 0:
        return 0
    num_levels = len(char.hp_roll_log or []) + 1
    total_delta = delta_mod * num_levels
    char.hp_max = (char.hp_max or 0) + total_delta
    char.hp_current = (char.hp_current or 0) + total_delta
    return total_delta


def _apply_capstone(char, cc, next_level: int) -> dict | None:
    """Apply L20 capstone stat boosts. Currently handles Barbarian Primal Champion."""
    if next_level != 20:
        return None
    cls_name = cc.dnd_class.name if cc.dnd_class else ""
    if cls_name != "Barbarian":
        return None
    if any(c.feature_key == "capstone:primal_champion" for c in char.choices):
        return None  # already applied (idempotent guard)

    base = dict(char.base_attributes or {})
    bg = char.background_asi or {}
    changes: dict = {}

    for ab in ("str", "con"):
        cur_total = base.get(ab, 10) + bg.get(ab, 0)
        new_total = min(25, cur_total + 4)  # cap raised to 25 for this capstone
        gain = new_total - cur_total
        if gain > 0:
            old_mod = (cur_total - 10) // 2
            base[ab] = base.get(ab, 10) + gain
            changes[ab] = gain
            if ab == "con":
                new_mod = (new_total - 10) // 2
                if new_mod != old_mod:
                    _recompute_hp_from_con_delta(char, old_mod, new_mod)

    if changes:
        char.base_attributes = base
    return changes or None


def _audit(char, db, feature_key: str, value: Any, level: int):
    """Save a CharacterChoice audit row."""
    db.add(CharacterChoice(character_id=char.id, feature_key=feature_key,
                           choice_value=value, level=level))


@router.get("/{char_id}/levelup-options")
def levelup_options(
    char_id: int,
    pending_subclass_id: int | None = None,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user),
):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)
    cc = char.character_classes[0] if char.character_classes else None
    if not cc:
        raise HTTPException(400, "No class assigned")

    level_granted = cc.level_granted if cc.level_granted is not None else cc.level
    next_level = cc.level + 1
    if next_level > level_granted:
        raise HTTPException(400, "No level-up available")

    cls = cc.dnd_class
    sp_type = cls.spellcasting_type or ""
    max_sl = max_spell_level(sp_type, next_level) if sp_type else 0

    # New features text for the "features" info step
    new_features = [f for f in (cls.features or []) if f.get("level") == next_level]
    subclass_features: list[dict] = []
    if cc.subclass:
        subclass_features = [f for f in (cc.subclass.features or []) if f.get("level") == next_level]

    # Build dynamic steps (pending_subclass_id enables mid-wizard L3 subclass step injection)
    steps = required_steps(char, cc, cls, db, pending_subclass_id=pending_subclass_id)

    # Fighting-style feats for the frontend
    fighting_styles = [
        {"id": f.id, "name": f.name, "description": f.description}
        for f in db.query(Feat).filter(Feat.category == "fighting_style").order_by(Feat.name).all()
    ]

    # General feats for ASI picker
    general_feats = [
        {"id": f.id, "name": f.name, "description": f.description, "prerequisites": f.prerequisites}
        for f in db.query(Feat).filter(Feat.category == "general").order_by(Feat.name).all()
    ]

    # Epic boon feats
    epic_boons = [
        {"id": f.id, "name": f.name, "description": f.description}
        for f in db.query(Feat).filter(Feat.category == "epic_boon").order_by(Feat.name).all()
    ]

    owned_spell_ids = [cs.spell_id for cs in char.spells]
    base_attrs = char.base_attributes or {}
    bg_asi = char.background_asi or {}

    return {
        "character_name": char.character_name,
        "class_name": cls.name,
        "current_level": cc.level,
        "next_level": next_level,
        "hit_die": cls.hit_die,
        "class_spellcasting": sp_type,
        "max_spell_level": max_sl,
        "steps": steps,
        "new_features": new_features,
        "subclass_features": subclass_features,
        "current_attributes": {k: base_attrs.get(k, 10) + bg_asi.get(k, 0)
                                for k in ["str", "dex", "con", "int", "wis", "cha"]},
        "owned_spell_ids": owned_spell_ids,
        "fighting_styles": fighting_styles,
        "general_feats": general_feats,
        "epic_boons": epic_boons,
    }


@router.post("/{char_id}/levelup")
def apply_levelup(char_id: int, data: LevelUpIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)
    cc = char.character_classes[0] if char.character_classes else None
    if not cc:
        raise HTTPException(400, "No class assigned")

    level_granted = cc.level_granted if cc.level_granted is not None else cc.level
    next_level = cc.level + 1
    if next_level > level_granted:
        raise HTTPException(400, "No level-up available")

    cls = cc.dnd_class
    sp_type = cls.spellcasting_type or ""
    max_sl = max_spell_level(sp_type, next_level) if sp_type else 0
    choices = data.choices
    auto_added_spells: list[str] = []   # names of auto-granted always-prepared spells

    # ── HP ──────────────────────────────────────────────────────────────────
    hp_gain = _apply_hp(char, cc, cls, data.hp, next_level)
    _audit(char, db, f"lvlup:{next_level}:hp", data.hp.dict(), next_level)

    # ── Subclass selection ───────────────────────────────────────────────────
    sub_step_id = f"subclass_l{next_level}"
    if sub_step_id in choices:
        subclass_id = choices[sub_step_id].get("subclass_id")
        if subclass_id:
            sub = db.get(Subclass, subclass_id)
            if not sub or sub.class_id != cc.class_id:
                raise HTTPException(400, "Invalid subclass")
            cc.subclass_id = subclass_id
            db.flush()   # so cc.subclass is accessible below
            # Auto-grant all subclass spells earned at/before this level
            grant_ids = subclass_auto_grants(char, cc, cls, cc.subclass, db)
            owned_ids = {cs.spell_id for cs in char.spells}
            for sid in grant_ids:
                if sid not in owned_ids:
                    db.add(CharacterSpell(character_id=char.id, spell_id=sid,
                                          source="subclass", always_prepared=True, prepared=True))
                    owned_ids.add(sid)
                    spell = db.get(Spell, sid)
                    if spell:
                        auto_added_spells.append(spell.name)
            _audit(char, db, f"lvlup:{next_level}:subclass", {"subclass_id": subclass_id}, next_level)
            # Draconic Sorcery: +3 HP at L3
            if cc.subclass and cc.subclass.name == "Draconic Sorcery" and next_level == 3:
                char.hp_max = (char.hp_max or 0) + 3
                char.hp_current = (char.hp_current or 0) + 3

    # ── ASI ─────────────────────────────────────────────────────────────────
    asi_step_id = f"asi_l{next_level}"
    if asi_step_id in choices:
        asi = choices[asi_step_id]
        mode = asi.get("mode", "")
        base = dict(char.base_attributes or {})
        bg = char.background_asi or {}

        if mode == "+2":
            ab = asi.get("ability")
            if ab and ab in base:
                cur_total = base.get(ab, 10) + bg.get(ab, 0)
                gain = min(2, 20 - cur_total)
                old_mod = (cur_total - 10) // 2
                base[ab] = base.get(ab, 10) + gain
                if ab == "con" and gain > 0:
                    new_mod = ((cur_total + gain) - 10) // 2
                    if new_mod != old_mod:
                        _recompute_hp_from_con_delta(char, old_mod, new_mod)
        elif mode == "+1+1":
            for ab in asi.get("abilities", [])[:2]:
                if ab in base:
                    cur_total = base.get(ab, 10) + bg.get(ab, 0)
                    gain = min(1, 20 - cur_total)
                    old_mod = (cur_total - 10) // 2
                    base[ab] = base.get(ab, 10) + gain
                    if ab == "con" and gain > 0:
                        new_mod = ((cur_total + gain) - 10) // 2
                        if new_mod != old_mod:
                            _recompute_hp_from_con_delta(char, old_mod, new_mod)
        elif mode == "feat":
            feat_id = asi.get("feat_id")
            if feat_id:
                feat = db.get(Feat, feat_id)
                if feat:
                    db.add(CharacterFeat(character_id=char.id, feat_id=feat_id, source="asi"))

        char.base_attributes = base
        _audit(char, db, f"lvlup:{next_level}:asi", asi, next_level)

    # ── Epic Boon ────────────────────────────────────────────────────────────
    epic_step_id = f"epic_boon_l{next_level}"
    if epic_step_id in choices:
        feat_id = choices[epic_step_id].get("feat_id")
        if feat_id:
            feat = db.get(Feat, feat_id)
            if feat:
                db.add(CharacterFeat(character_id=char.id, feat_id=feat_id, source="epic_boon"))
        _audit(char, db, f"lvlup:{next_level}:epic_boon", choices[epic_step_id], next_level)

    # ── Fighting Style ───────────────────────────────────────────────────────
    for prefix in [f"fighting_style_l{next_level}", f"fighter_style_swap_l{next_level}"]:
        if prefix in choices:
            feat_id = choices[prefix].get("feat_id")
            if feat_id:
                feat = db.get(Feat, feat_id)
                if feat:
                    # For fighter swap, remove old fighting style feat first
                    if "swap" in prefix:
                        for cf in list(char.feats):
                            if cf.source == "fighting_style":
                                db.delete(cf)
                                break
                    db.add(CharacterFeat(character_id=char.id, feat_id=feat_id, source="fighting_style"))
                    db.add(CharacterChoice(character_id=char.id, feature_key="fighting_style",
                                           choice_value={"feat_id": feat_id, "name": feat.name},
                                           level=next_level))
            break

    # ── Expertise ────────────────────────────────────────────────────────────
    exp_step_id = f"expertise_l{next_level}"
    if exp_step_id in choices:
        skill_names = choices[exp_step_id].get("skills", [])
        for skill_name in skill_names:
            sp = next((s for s in char.skill_proficiencies if s.skill_name == skill_name), None)
            if sp:
                sp.expertise = True
        _audit(char, db, f"lvlup:{next_level}:expertise", {"skills": skill_names}, next_level)

    # ── Cantrips (new) ───────────────────────────────────────────────────────
    cantrip_step_id = f"cantrips_l{next_level}"
    owned_ids = {cs.spell_id for cs in char.spells}
    if cantrip_step_id in choices:
        for sid in choices[cantrip_step_id].get("spell_ids", []):
            if sid not in owned_ids:
                db.add(CharacterSpell(character_id=char.id, spell_id=sid, source="class"))
                owned_ids.add(sid)
        _audit(char, db, f"lvlup:{next_level}:cantrips", choices[cantrip_step_id], next_level)

    # ── Spells / Spellbook (new) ─────────────────────────────────────────────
    spell_step_id = f"spells_l{next_level}"
    if spell_step_id in choices:
        is_wizard = cls.name == "Wizard"
        for sid in choices[spell_step_id].get("spell_ids", []):
            if sid not in owned_ids:
                # Wizard spells go to spellbook (prepared=False); others are known (prepared=True)
                db.add(CharacterSpell(character_id=char.id, spell_id=sid, source="class",
                                      prepared=not is_wizard))
                owned_ids.add(sid)
        _audit(char, db, f"lvlup:{next_level}:spells", choices[spell_step_id], next_level)

    # ── Spell swap (optional) ────────────────────────────────────────────────
    swap_step_id = f"spell_swap_l{next_level}"
    if swap_step_id in choices:
        payload = choices[swap_step_id]
        remove_id = payload.get("remove_id")
        add_id = payload.get("add_id")
        if remove_id and add_id:
            for cs in list(char.spells):
                if cs.spell_id == remove_id and cs.source == "class" and not (cs.always_prepared or False):
                    db.delete(cs)
                    break
            if add_id not in owned_ids:
                is_wizard = cls.name == "Wizard"
                db.add(CharacterSpell(character_id=char.id, spell_id=add_id, source="class",
                                      prepared=not is_wizard))
        _audit(char, db, f"lvlup:{next_level}:spell_swap", payload, next_level)

    # ── Cantrip swap (optional) ──────────────────────────────────────────────
    cswap_step_id = f"cantrip_swap_l{next_level}"
    if cswap_step_id in choices:
        payload = choices[cswap_step_id]
        remove_id = payload.get("remove_id")
        add_id = payload.get("add_id")
        if remove_id and add_id:
            for cs in list(char.spells):
                if cs.spell_id == remove_id and cs.source == "class":
                    spell_obj = db.get(Spell, remove_id)
                    if spell_obj and spell_obj.level == 0:
                        db.delete(cs)
                        break
            if add_id not in owned_ids:
                db.add(CharacterSpell(character_id=char.id, spell_id=add_id, source="class"))

    # ── Metamagic ────────────────────────────────────────────────────────────
    mm_step_id = f"metamagic_l{next_level}"
    if mm_step_id in choices:
        for key in choices[mm_step_id].get("keys", []):
            db.add(CharacterChoice(character_id=char.id, feature_key="metamagic",
                                   choice_value={"key": key}, level=next_level))
        _audit(char, db, f"lvlup:{next_level}:metamagic", choices[mm_step_id], next_level)

    # ── Eldritch Invocations (new) ────────────────────────────────────────────
    invoc_step_id = f"invocations_l{next_level}"
    if invoc_step_id in choices:
        for key in choices[invoc_step_id].get("keys", []):
            db.add(CharacterChoice(character_id=char.id, feature_key="invocation",
                                   choice_value={"key": key}, level=next_level))
        _audit(char, db, f"lvlup:{next_level}:invocations", choices[invoc_step_id], next_level)

    # ── Invocation swap (optional) ────────────────────────────────────────────
    iswap_step_id = f"invoc_swap_l{next_level}"
    if iswap_step_id in choices:
        payload = choices[iswap_step_id]
        remove_key = payload.get("remove_key")
        add_key = payload.get("add_key")
        if remove_key and add_key:
            for ch in list(char.choices):
                if ch.feature_key == "invocation" and (ch.choice_value or {}).get("key") == remove_key:
                    db.delete(ch)
                    break
            db.add(CharacterChoice(character_id=char.id, feature_key="invocation",
                                   choice_value={"key": add_key}, level=next_level))
        _audit(char, db, f"lvlup:{next_level}:invoc_swap", payload, next_level)

    # ── Mystic Arcanum ────────────────────────────────────────────────────────
    arcanum_step_id = f"arcanum_l{next_level}"
    if arcanum_step_id in choices:
        sid = choices[arcanum_step_id].get("spell_id")
        if sid and sid not in owned_ids:
            db.add(CharacterSpell(character_id=char.id, spell_id=sid, source="arcanum",
                                  notes="Mystic Arcanum — 1/long rest, no slot"))
            owned_ids.add(sid)
        _audit(char, db, f"lvlup:{next_level}:arcanum", choices[arcanum_step_id], next_level)

    # ── Weapon Mastery ────────────────────────────────────────────────────────
    wm_step_id = f"weapon_mastery_l{next_level}"
    if wm_step_id in choices:
        existing_masteries = {wu.weapon_name for wu in char.weapon_mastery_unlocks}
        for weapon_name in choices[wm_step_id].get("weapons", []):
            if weapon_name not in existing_masteries:
                db.add(WeaponMasteryUnlock(character_id=char.id, weapon_name=weapon_name))
                existing_masteries.add(weapon_name)
            db.add(CharacterChoice(character_id=char.id, feature_key="weapon_mastery",
                                   choice_value={"weapon": weapon_name, "swappable_on_long_rest": True},
                                   level=next_level))
        _audit(char, db, f"lvlup:{next_level}:weapon_mastery", choices[wm_step_id], next_level)

    # ── Primal Knowledge (Barbarian L3) ──────────────────────────────────────
    pk_step_id = f"primal_knowledge_l{next_level}"
    if pk_step_id in choices:
        skill = choices[pk_step_id].get("skill")
        if skill:
            existing_skills = {sp.skill_name for sp in char.skill_proficiencies}
            if skill not in existing_skills:
                db.add(SkillProficiency(character_id=char.id, skill_name=skill, source="class"))
            db.add(CharacterChoice(character_id=char.id, feature_key="primal_knowledge",
                                   choice_value={"skill": skill}, level=next_level))
        _audit(char, db, f"lvlup:{next_level}:primal_knowledge", choices[pk_step_id], next_level)

    # ── Blessed Strikes (Cleric L7) ───────────────────────────────────────────
    bs_step_id = f"blessed_strikes_l{next_level}"
    if bs_step_id in choices:
        choice_val = choices[bs_step_id].get("choice")
        db.add(CharacterChoice(character_id=char.id, feature_key="blessed_strikes",
                               choice_value={"choice": choice_val}, level=next_level))
        _audit(char, db, f"lvlup:{next_level}:blessed_strikes", choices[bs_step_id], next_level)

    bsd_step_id = f"blessed_strikes_damage_l{next_level}"
    if bsd_step_id in choices:
        dmg_type = choices[bsd_step_id].get("choice")
        db.add(CharacterChoice(character_id=char.id, feature_key="blessed_strikes_damage",
                               choice_value={"damage_type": dmg_type}, level=next_level))
        _audit(char, db, f"lvlup:{next_level}:blessed_strikes_damage", choices[bsd_step_id], next_level)

    # ── Battle Master Maneuvers ───────────────────────────────────────────────
    _bm_by_key = {m["key"]: m for m in BATTLE_MASTER_MANEUVERS}
    man_step_id = f"maneuvers_l{next_level}"
    if man_step_id in choices:
        for key in choices[man_step_id].get("keys", []):
            m = _bm_by_key.get(key, {})
            db.add(CharacterChoice(character_id=char.id, feature_key="maneuver",
                                   choice_value={"key": key, "name": m.get("name", key)},
                                   level=next_level))
        _audit(char, db, f"lvlup:{next_level}:maneuvers", choices[man_step_id], next_level)

    # ── Student of War (Battle Master L3) ────────────────────────────────────
    sow_step_id = f"student_of_war_l{next_level}"
    if sow_step_id in choices:
        tool  = choices[sow_step_id].get("tool")
        skill = choices[sow_step_id].get("skill")
        if tool:
            existing_tools = {tp.tool_name for tp in char.tool_proficiencies}
            if tool not in existing_tools:
                db.add(ToolProficiency(character_id=char.id, tool_name=tool, source="class"))
        if skill:
            existing_skills = {sp.skill_name for sp in char.skill_proficiencies}
            if skill not in existing_skills:
                db.add(SkillProficiency(character_id=char.id, skill_name=skill, source="class"))
        db.add(CharacterChoice(character_id=char.id, feature_key="student_of_war",
                               choice_value={"tool": tool, "skill": skill}, level=next_level))
        _audit(char, db, f"lvlup:{next_level}:student_of_war", choices[sow_step_id], next_level)

    # ── War Bond (Eldritch Knight L3) ─────────────────────────────────────────
    wb_step_id = f"war_bond_l{next_level}"
    if wb_step_id in choices:
        db.add(CharacterChoice(character_id=char.id, feature_key="war_bond",
                               choice_value={"weapons": choices[wb_step_id].get("weapons", [])},
                               level=next_level))
        _audit(char, db, f"lvlup:{next_level}:war_bond", choices[wb_step_id], next_level)

    # ── Third-caster cantrips (EK / AT) ──────────────────────────────────────
    tcc_step_id = f"third_caster_cantrips_l{next_level}"
    if tcc_step_id in choices:
        for sid in choices[tcc_step_id].get("spell_ids", []):
            if sid not in owned_ids:
                db.add(CharacterSpell(character_id=char.id, spell_id=sid,
                                      source="subclass", prepared=True))
                owned_ids.add(sid)
        # Arcane Trickster L3: auto-grant Mage Hand as a bonus cantrip
        if next_level == 3 and cc.subclass and cc.subclass.name == "Arcane Trickster":
            mh = db.query(Spell).filter(Spell.name == "Mage Hand").first()
            if mh and mh.id not in owned_ids:
                db.add(CharacterSpell(character_id=char.id, spell_id=mh.id,
                                      source="subclass", prepared=True,
                                      notes="AT bonus cantrip (Mage Hand Legerdemain)"))
                owned_ids.add(mh.id)
                auto_added_spells.append("Mage Hand")
        # Record one choice row to mark this level's cantrips done (idempotency key)
        db.add(CharacterChoice(character_id=char.id, feature_key="third_caster_cantrip",
                               choice_value=choices[tcc_step_id], level=next_level))
        _audit(char, db, f"lvlup:{next_level}:third_caster_cantrips", choices[tcc_step_id], next_level)

    # ── Third-caster spells (EK / AT) ─────────────────────────────────────────
    tcs_step_id = f"third_caster_spells_l{next_level}"
    if tcs_step_id in choices:
        for sid in choices[tcs_step_id].get("spell_ids", []):
            if sid not in owned_ids:
                db.add(CharacterSpell(character_id=char.id, spell_id=sid,
                                      source="subclass", prepared=True))
                owned_ids.add(sid)
        db.add(CharacterChoice(character_id=char.id, feature_key="third_caster_spell",
                               choice_value=choices[tcs_step_id], level=next_level))
        _audit(char, db, f"lvlup:{next_level}:third_caster_spells", choices[tcs_step_id], next_level)

    # ── Hunter's Prey (Hunter Ranger L3) ─────────────────────────────────────
    hp_step_id = f"hunters_prey_l{next_level}"
    if hp_step_id in choices:
        db.add(CharacterChoice(character_id=char.id, feature_key="hunters_prey",
                               choice_value={"choice": choices[hp_step_id].get("choice")},
                               level=next_level))
        _audit(char, db, f"lvlup:{next_level}:hunters_prey", choices[hp_step_id], next_level)

    # ── Defensive Tactics (Hunter Ranger L7) ─────────────────────────────────
    dt_step_id = f"defensive_tactics_l{next_level}"
    if dt_step_id in choices:
        db.add(CharacterChoice(character_id=char.id, feature_key="defensive_tactics",
                               choice_value={"choice": choices[dt_step_id].get("choice")},
                               level=next_level))
        _audit(char, db, f"lvlup:{next_level}:defensive_tactics", choices[dt_step_id], next_level)

    # ── Otherworldly Glamour (Fey Wanderer L3) ────────────────────────────────
    og_step_id = f"otherworldly_glamour_l{next_level}"
    if og_step_id in choices:
        skill = choices[og_step_id].get("skill")
        if skill:
            existing_skills = {sp.skill_name for sp in char.skill_proficiencies}
            if skill not in existing_skills:
                db.add(SkillProficiency(character_id=char.id, skill_name=skill, source="class"))
        db.add(CharacterChoice(character_id=char.id, feature_key="otherworldly_glamour",
                               choice_value={"skill": skill}, level=next_level))
        _audit(char, db, f"lvlup:{next_level}:otherworldly_glamour", choices[og_step_id], next_level)

    # ── Beast Companion (Beast Master L3) ────────────────────────────────────
    bc_step_id = f"beast_companion_l{next_level}"
    if bc_step_id in choices:
        db.add(CharacterChoice(character_id=char.id, feature_key="beast_companion",
                               choice_value={"choice": choices[bc_step_id].get("choice")},
                               level=next_level))
        _audit(char, db, f"lvlup:{next_level}:beast_companion", choices[bc_step_id], next_level)

    # ── Iron Mind (Gloom Stalker L7) ─────────────────────────────────────────
    im_step_id = f"iron_mind_l{next_level}"
    if im_step_id in choices:
        save = choices[im_step_id].get("save_proficiency", "Wisdom")
        db.add(CharacterChoice(character_id=char.id, feature_key="iron_mind",
                               choice_value={"save_proficiency": save}, level=next_level))
        _audit(char, db, f"lvlup:{next_level}:iron_mind", {"save_proficiency": save}, next_level)

    # ── Rage of the Wilds (Wild Heart L3) ────────────────────────────────────
    row_step_id = f"rage_of_wilds_l{next_level}"
    if row_step_id in choices:
        db.add(CharacterChoice(character_id=char.id, feature_key="rage_of_wilds",
                               choice_value=choices[row_step_id], level=next_level))
        _audit(char, db, f"lvlup:{next_level}:rage_of_wilds", choices[row_step_id], next_level)

    # ── Aspect of the Wilds (Wild Heart L6) ──────────────────────────────────
    aow_step_id = f"aspect_of_wilds_l{next_level}"
    if aow_step_id in choices:
        db.add(CharacterChoice(character_id=char.id, feature_key="aspect_of_wilds",
                               choice_value={"choice": choices[aow_step_id].get("choice")},
                               level=next_level))
        _audit(char, db, f"lvlup:{next_level}:aspect_of_wilds", choices[aow_step_id], next_level)

    # ── Power of the Wilds (Wild Heart L14) ──────────────────────────────────
    pow_step_id = f"power_of_wilds_l{next_level}"
    if pow_step_id in choices:
        db.add(CharacterChoice(character_id=char.id, feature_key="power_of_wilds",
                               choice_value={"choice": choices[pow_step_id].get("choice")},
                               level=next_level))
        _audit(char, db, f"lvlup:{next_level}:power_of_wilds", choices[pow_step_id], next_level)

    # ── Divine Fury (Zealot L3) ───────────────────────────────────────────────
    df_step_id = f"divine_fury_l{next_level}"
    if df_step_id in choices:
        db.add(CharacterChoice(character_id=char.id, feature_key="divine_fury",
                               choice_value={"choice": choices[df_step_id].get("choice")},
                               level=next_level))
        _audit(char, db, f"lvlup:{next_level}:divine_fury", choices[df_step_id], next_level)

    # ── Assassin's Tools (Assassin L3) ───────────────────────────────────────
    at_step_id = f"assassins_tools_l{next_level}"
    if at_step_id in choices:
        existing_tools = {tp.tool_name for tp in char.tool_proficiencies}
        for tool in ["Disguise Kit", "Poisoner's Kit"]:
            if tool not in existing_tools:
                db.add(ToolProficiency(character_id=char.id, tool_name=tool, source="class"))
        db.add(CharacterChoice(character_id=char.id, feature_key="assassins_tools",
                               choice_value={"acknowledged": True}, level=next_level))
        _audit(char, db, f"lvlup:{next_level}:assassins_tools", choices[at_step_id], next_level)

    # ── Druidic Warrior cantrips (Ranger L2) ─────────────────────────────────
    dw_step_id = f"druidic_warrior_cantrips_l{next_level}"
    if dw_step_id in choices:
        for sid in choices[dw_step_id].get("spell_ids", []):
            if sid not in owned_ids:
                db.add(CharacterSpell(character_id=char.id, spell_id=sid,
                                      source="class", prepared=True))
                owned_ids.add(sid)
        db.add(CharacterChoice(character_id=char.id, feature_key="druidic_warrior_cantrips",
                               choice_value={"acknowledged": True}, level=next_level))
        _audit(char, db, f"lvlup:{next_level}:druidic_warrior_cantrips", choices[dw_step_id], next_level)

    # ── Feature choices (generic) — any feature_* step not handled above ─────
    # Fixed: old filter `"choice" in step_id` never matched; now matches correctly.
    for step_id, payload in choices.items():
        if step_id.startswith("feature_") and step_id.endswith(f"_l{next_level}"):
            _audit(char, db, f"lvlup:{next_level}:{step_id}", payload, next_level)

    # ── Species revelation choice (Aasimar L3) ────────────────────────────────
    rev_step_id = f"species_revelation_l{next_level}"
    if rev_step_id in choices:
        rv = choices[rev_step_id]
        key = rv.get("key")
        if key:
            revelation = next((r for r in AASIMAR_REVELATIONS if r["key"] == key), None)
            if revelation:
                _audit(char, db, f"species_revelation_l{next_level}",
                       {"key": key, "name": revelation["name"], "description": revelation["description"]},
                       next_level)

    # ── Auto-grants (subclass tier spells + lineage spells) ──────────────────
    current_subclass = db.get(Subclass, cc.subclass_id) if cc.subclass_id else None
    grant_ids = auto_grants(char, cc, cls, current_subclass, next_level, db)
    owned_ids = {cs.spell_id for cs in char.spells}
    for sid in grant_ids:
        if sid not in owned_ids:
            # Determine source: lineage spell vs subclass
            lineage_names = _species_lineage_spells(char, next_level)
            spell_obj = db.get(Spell, sid)
            src = "lineage" if (spell_obj and spell_obj.name in lineage_names) else "subclass"
            db.add(CharacterSpell(character_id=char.id, spell_id=sid,
                                  source=src, always_prepared=True, prepared=True))
            owned_ids.add(sid)
            if spell_obj:
                auto_added_spells.append(spell_obj.name)

    # ── Prepared-caster spell list population (Bard / Cleric / Druid / Paladin / Ranger) ─
    # These classes don't pick spells at level-up; instead they always have
    # access to their full class list up to their max slot level. Populate any
    # newly available spells as prepared=False so the sheet can display them.
    PREPARED_CASTERS = {"Bard", "Cleric", "Druid", "Paladin", "Ranger"}
    if cls.name in PREPARED_CASTERS and max_sl > 0:
        owned_ids_now = {cs.spell_id for cs in char.spells}
        candidate_spells = (
            db.query(Spell)
            .filter(Spell.level <= max_sl, Spell.level > 0)
            .all()
        )
        class_spells = [s for s in candidate_spells if cls.name in (s.classes or [])]
        for sp in class_spells:
            if sp.id not in owned_ids_now:
                db.add(CharacterSpell(
                    character_id=char.id,
                    spell_id=sp.id,
                    source="class",
                    prepared=False,
                ))
                owned_ids_now.add(sp.id)

    # ── Capstone stat boosts ──────────────────────────────────────────────────
    capstone_changes = _apply_capstone(char, cc, next_level)
    if capstone_changes:
        _audit(char, db, "capstone:primal_champion", capstone_changes, next_level)

    # ── Increment level ───────────────────────────────────────────────────────
    cc.level = next_level
    cc.hit_dice_remaining = (cc.hit_dice_remaining or 0) + 1
    db.commit()

    return {
        "ok": True,
        "new_level": next_level,
        "hp_max": char.hp_max,
        "hp_gained": hp_gain,
        "auto_added_spells": auto_added_spells,
    }


# --- Exports ---
@router.get("")
def list_my_characters(db: Session = Depends(get_db), user: dict = Depends(require_user)):
    chars = db.query(Character).filter(Character.owner_email == user["email"]) \
              .order_by(Character.created_at.desc()).all()
    result = []
    for c in chars:
        cc = c.character_classes[0] if c.character_classes else None
        result.append({
            "id": c.id,
            "character_name": c.character_name,
            "created_by_display_name": c.created_by_display_name,
            "species_name": c.species.name if c.species else None,
            "species_lineage": c.species_lineage,
            "background_name": c.background.name if c.background else None,
            "class_name": cc.dnd_class.name if cc and cc.dnd_class else None,
            "level": cc.level if cc else None,
            "level_granted": cc.level_granted if cc else None,
            "is_complete": c.is_complete,
            "wizard_step": c.wizard_step,
            "hp_max": c.hp_max,
            "speed": c.speed,
            "alignment": c.alignment,
        })
    return result


@router.get("/{char_id}/export/html", response_class=HTMLResponse)
def export_html(char_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    char_dict = character_to_dict(char, db)
    cc = char.character_classes[0] if char.character_classes else None
    class_obj = db.get(DnDClass, cc.class_id) if cc else None
    return render_character_html(char_dict, class_obj=class_obj, species_obj=char.species, background_obj=char.background)


@router.get("/{char_id}/export/json")
def export_json(char_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    return character_to_dict(char, db)


@router.get("/{char_id}/export/pdf")
def export_pdf(char_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner(char, user)
    char_dict = character_to_dict(char, db)
    cc = char.character_classes[0] if char.character_classes else None
    class_obj = db.get(DnDClass, cc.class_id) if cc else None
    pdf_bytes = render_character_pdf(char_dict, class_obj=class_obj, species_obj=char.species, background_obj=char.background)
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{char.character_name}.pdf"'})


# ---------------------------------------------------------------------------
# Per-rest resource tracking
# ---------------------------------------------------------------------------

@router.get("/{char_id}/resources")
def get_resources(char_id: int, db: Session = Depends(get_db), user=Depends(require_user)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    if char.owner_email != user["email"] and not user.get("is_admin"):
        raise HTTPException(403)
    rows = db.query(CharacterResource).filter_by(character_id=char_id).all()
    return [
        {
            "id": r.id,
            "resource_key": r.resource_key,
            "label": r.label,
            "max_uses": r.max_uses,
            "used": r.used,
            "remaining": r.max_uses - r.used,
            "rest_type": r.rest_type,
        }
        for r in rows
    ]


class SpendResourceIn(BaseModel):
    resource_id: int
    amount: int = Field(default=1, ge=1)


@router.post("/{char_id}/resources/spend")
def spend_resource(
    char_id: int,
    body: SpendResourceIn,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    if char.owner_email != user["email"] and not user.get("is_admin"):
        raise HTTPException(403)
    res = db.get(CharacterResource, body.resource_id)
    if not res or res.character_id != char_id:
        raise HTTPException(404)
    new_used = res.used + body.amount
    if new_used > res.max_uses:
        raise HTTPException(400, "Not enough uses remaining")
    res.used = new_used
    db.commit()
    return {"id": res.id, "used": res.used, "remaining": res.max_uses - res.used}


class PlayerRestIn(BaseModel):
    rest_type: str  # "short" | "long"


@router.post("/{char_id}/rest")
def take_rest(
    char_id: int,
    body: PlayerRestIn,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    """Player-triggered rest. Short rest restores 'short' resources; long rest restores all."""
    if body.rest_type not in ("short", "long"):
        raise HTTPException(400, "rest_type must be 'short' or 'long'")
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    if char.owner_email != user["email"] and not user.get("is_admin"):
        raise HTTPException(403)

    resources = db.query(CharacterResource).filter_by(character_id=char_id).all()
    restored = []
    for res in resources:
        should_restore = (
            body.rest_type == "long"
            or res.rest_type in ("short", "encounter")
        )
        if should_restore and res.used > 0:
            res.used = 0
            restored.append(res.resource_key)

    # Long rest: restore all spell slots
    if body.rest_type == "long" and char.spell_slots_used:
        char.spell_slots_used = {}

    # Long rest: restore HP
    if body.rest_type == "long":
        char.hp_current = char.hp_max

    # Long rest: restore all hit dice
    if body.rest_type == "long":
        for cc in char.character_classes:
            cc.hit_dice_remaining = cc.level

    db.commit()
    return {"ok": True, "restored_resources": restored, "rest_type": body.rest_type}


# ---------------------------------------------------------------------------
# Player action economy
# ---------------------------------------------------------------------------

class PlayerActionEconomyIn(BaseModel):
    combatant_id: int
    action_used: bool | None = None
    bonus_action_used: bool | None = None
    reaction_used: bool | None = None


# Note: this endpoint lives under /api/characters but needs a separate router prefix
# We use a workaround by registering with an absolute path via the app router at main.py,
# or we accept /api/characters/encounter/action-economy as the path.
@router.post("/encounter/action-economy")
async def player_mark_action(
    body: PlayerActionEconomyIn,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    """Player marks their own action economy during their turn."""
    # TODO Task 7: add enforcement that only marks are allowed on current_turn_combatant_id
    from ..models.character import Combatant
    row = db.get(Combatant, body.combatant_id)
    if not row or not row.character_id:
        raise HTTPException(404)
    if row.character.owner_email != user["email"]:
        raise HTTPException(403, "Can only update your own character's actions")
    if body.action_used is not None:
        row.action_used = body.action_used
    if body.bonus_action_used is not None:
        row.bonus_action_used = body.bonus_action_used
    if body.reaction_used is not None:
        row.reaction_used = body.reaction_used
    db.commit()
    await _broadcast_state(db)
    return {"ok": True}


class EndTurnIn(BaseModel):
    combatant_id: int


@router.post("/encounter/end-turn")
async def player_end_turn(
    body: EndTurnIn,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    """Player ends their turn — advances initiative to the next combatant."""
    from ..models.character import Combatant, EncounterState
    row = db.get(Combatant, body.combatant_id)
    if not row or not row.character_id:
        raise HTTPException(404)
    if row.character.owner_email != user["email"]:
        raise HTTPException(403, "Can only end your own character's turn")

    state = db.get(EncounterState, 1)
    if not state or not state.encounter_active or state.initiative_phase:
        raise HTTPException(400, "No active encounter")
    if state.current_turn_combatant_id != body.combatant_id:
        raise HTTPException(400, "It is not this character's turn")

    ordered = db.query(Combatant).filter(
        Combatant.turn_order.isnot(None)
    ).order_by(Combatant.turn_order).all()
    if not ordered:
        raise HTTPException(400, "No combatants in initiative order")

    current_ids = [c.id for c in ordered]
    try:
        idx = current_ids.index(state.current_turn_combatant_id)
    except ValueError:
        idx = -1

    next_idx = idx + 1
    if next_idx >= len(ordered):
        next_idx = 0
        state.current_round += 1

    next_combatant = ordered[next_idx]
    state.current_turn_combatant_id = next_combatant.id

    # Reset action economy for the next combatant's turn
    next_combatant.action_used = False
    next_combatant.bonus_action_used = False
    next_combatant.reaction_used = False
    if next_combatant.character_id and next_combatant.character:
        next_combatant.movement_remaining = (
            next_combatant.character.speed if next_combatant.character.speed is not None else 30
        )

    db.commit()
    await _broadcast_state(db)
    return {"ok": True, "current_round": state.current_round}


class SpendMovementIn(BaseModel):
    combatant_id: int
    amount: int  # must be a positive multiple of 5


@router.post("/encounter/spend-movement")
async def player_spend_movement(
    body: SpendMovementIn,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    from ..models.character import Combatant
    if body.amount <= 0 or body.amount % 5 != 0:
        raise HTTPException(400, "Amount must be a positive multiple of 5")
    row = db.get(Combatant, body.combatant_id)
    if not row or not row.character_id:
        raise HTTPException(404)
    if row.character.owner_email != user["email"]:
        raise HTTPException(403, "Can only spend your own character's movement")
    remaining = row.movement_remaining or 0
    if body.amount > remaining:
        raise HTTPException(400, f"Only {remaining} ft remaining")
    row.movement_remaining = remaining - body.amount
    db.commit()
    await _broadcast_state(db)
    return {"ok": True, "movement_remaining": row.movement_remaining}


# ---------------------------------------------------------------------------
# Encounter action info panel
# ---------------------------------------------------------------------------

@router.get("/{char_id}/encounter-actions")
def get_encounter_actions(
    char_id: int,
    db: Session = Depends(get_db),
    user: dict = Depends(require_user),
):
    """Return available combat actions for the encounter panel (attacks + action/bonus-action spells)."""
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    if char.owner_email != user["email"] and not user.get("is_admin"):
        raise HTTPException(403)

    data = character_to_sheet_dict(char, db)

    # Compute spellcasting stats
    sp_ability = (data.get("class_spellcasting_ability") or "").lower()
    ab_map = {"intelligence": "int", "wisdom": "wis", "charisma": "cha"}
    sp_ab_key = ab_map.get(sp_ability, "int")
    attrs = data.get("attributes") or {}
    sp_mod = (attrs.get(sp_ab_key, 10) - 10) // 2
    prof = data.get("proficiency_bonus", 2)
    save_dc = 8 + prof + sp_mod if data.get("class_spellcasting_type") else None
    spell_atk = prof + sp_mod if data.get("class_spellcasting_type") else None
    spell_atk_display = (f"+{spell_atk}" if spell_atk >= 0 else str(spell_atk)) if spell_atk is not None else None

    actions = []

    # Weapon attacks — all computed attacks (from equipped weapons + unarmed)
    for atk in data.get("attacks", []):
        atk_bonus = atk.get("attack_bonus", 0)
        atk_bonus_display = f"+{atk_bonus}" if atk_bonus >= 0 else str(atk_bonus)
        actions.append({
            "type": "attack",
            "name": atk["name"],
            "cost": {"action": True, "bonus_action": False, "spell_slot": None},
            "attack_bonus": atk_bonus,
            "attack_bonus_display": atk_bonus_display,
            "damage": atk.get("damage", ""),
            "range": "5 ft." if (atk.get("category") or "").lower() == "melee" else "Ranged",
            "properties": atk.get("properties", []),
            "mastery_property": atk.get("mastery_property"),
            "save_dc": None,
            "save_ability": None,
            "description": "",
            "level": None,
            "school": None,
        })

    # Prepared spells with 1 action or bonus action casting time
    for sp in data.get("spells", []):
        is_cantrip = sp.get("level", 0) == 0
        # Cantrips are always available regardless of prepared flag
        if not is_cantrip and not sp.get("prepared") and not sp.get("always_prepared"):
            continue
        ct = (sp.get("casting_time") or "").lower()
        is_action = "1 action" in ct
        is_bonus = "bonus action" in ct
        if not is_action and not is_bonus:
            continue  # skip rituals, reactions, 1 minute, etc.
        slot_level = sp.get("level", 0) if sp.get("level", 0) > 0 else None
        actions.append({
            "type": "spell",
            "name": sp["name"],
            "cost": {"action": is_action, "bonus_action": is_bonus, "spell_slot": slot_level},
            "attack_bonus": spell_atk,
            "attack_bonus_display": spell_atk_display,
            "damage": "",  # not parsed from description (proof of concept)
            "range": sp.get("range", ""),
            "properties": [],
            "mastery_property": None,
            "save_dc": save_dc,
            "save_ability": (data.get("class_spellcasting_ability") or "").title() or None,
            "description": sp.get("description", ""),
            "duration": sp.get("duration", ""),
            "concentration": sp.get("concentration", False),
            "level": sp.get("level", 0),
            "school": sp.get("school", ""),
        })

    return actions
