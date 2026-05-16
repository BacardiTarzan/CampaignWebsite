from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, Response, HTMLResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any
from ..database import get_db
from ..dependencies import require_user
from ..models.character import (
    Character, CharacterClass, StatRollSet, CharacterChoice,
    CharacterFeat, CharacterSpell, CharacterEquipment,
    SkillProficiency, ToolProficiency, LanguageProficiency, WeaponMasteryUnlock,
)
from ..models.content import DnDClass, Background, Feat, Spell, Equipment, Species, Subclass
from ..services.export import character_to_dict, character_to_sheet_dict
from ..services.levelup_rules import (
    required_steps, auto_grants, subclass_auto_grants, max_spell_level, METAMAGIC_OPTIONS, ELDRITCH_INVOCATIONS,
)
from ..config import settings
from ..services.pdf import render_character_pdf, render_character_html
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
    # Remove class-sourced skills and all language proficiencies
    for sp in list(char.skill_proficiencies):
        if sp.source == "class":
            db.delete(sp)
    for lp in list(char.language_proficiencies):
        db.delete(lp)
    db.flush()

    for skill in data.skills:
        db.add(SkillProficiency(character_id=char.id, skill_name=skill, source="class"))
    for lang in data.languages:
        db.add(LanguageProficiency(character_id=char.id, language_name=lang, source="player_choice"))

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
    return {"hp_current": char.hp_current, "hp_max": char.hp_max}


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

    # Recompute AC inline (mirrors export.py logic)
    base = char.base_attributes or {}
    asi = char.background_asi or {}
    attrs = {k: base.get(k, 10) + asi.get(k, 0) for k in ("str","dex","con","int","wis","cha")}
    dex_mod = (attrs["dex"] - 10) // 2

    ac = 10 + dex_mod
    for ce in char.equipment:
        it = ce.equipment_item
        if it and it.item_type == "armor" and ce.equipped:
            f = (it.ac_formula or "").strip()
            import re as _re
            if _re.fullmatch(r"\d+", f):
                ac = int(f)
            else:
                m = _re.match(r"(\d+)\s*\+\s*Dex(?:\s*\(max\s*(\d+)\))?", f, _re.IGNORECASE)
                ac = int(m.group(1)) + min(dex_mod, int(m.group(2)) if m and m.group(2) else 99) if m else 10 + dex_mod
            break
    for ce in char.equipment:
        it = ce.equipment_item
        if it and it.item_type == "shield" and ce.equipped:
            ac += 2
            break

    return {"ok": True, "entry_id": entry_id, "equipped": entry.equipped, "ac": ac}


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

    PREP_CASTERS = {"cleric", "druid", "paladin", "ranger", "wizard"}
    if class_lower not in PREP_CASTERS:
        raise HTTPException(400, "Class does not prepare spells")

    base = char.base_attributes or {}
    asi_bonus = char.background_asi or {}
    a = {k: base.get(k, 10) + asi_bonus.get(k, 0) for k in ("str", "dex", "con", "int", "wis", "cha")}
    ab_map = {"intelligence": "int", "wisdom": "wis", "charisma": "cha"}
    sp_ab_key = ab_map.get((cls.spellcasting_ability or "").lower(), "int")
    sp_mod = (a.get(sp_ab_key, 10) - 10) // 2

    if class_lower in ("cleric", "druid", "wizard"):
        prepared_max = max(1, sp_mod + level)
    else:
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


def _audit(char, db, feature_key: str, value: Any, level: int):
    """Save a CharacterChoice audit row."""
    db.add(CharacterChoice(character_id=char.id, feature_key=feature_key,
                           choice_value=value, level=level))


@router.get("/{char_id}/levelup-options")
def levelup_options(char_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
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

    # Build dynamic steps
    steps = required_steps(char, cc, cls, db)

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
                base[ab] = base.get(ab, 10) + gain
                if ab == "con" and gain > 0:
                    con_delta = gain // 2
                    extra_hp = con_delta * (next_level - 1)
                    char.hp_max = (char.hp_max or 0) + extra_hp
                    char.hp_current = (char.hp_current or 0) + extra_hp
        elif mode == "+1+1":
            for ab in asi.get("abilities", [])[:2]:
                if ab in base:
                    cur_total = base.get(ab, 10) + bg.get(ab, 0)
                    gain = min(1, 20 - cur_total)
                    base[ab] = base.get(ab, 10) + gain
                    if ab == "con" and gain > 0:
                        extra_hp = (gain // 2) * (next_level - 1)
                        char.hp_max = (char.hp_max or 0) + extra_hp
                        char.hp_current = (char.hp_current or 0) + extra_hp
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

    # ── Feature choices (generic) ─────────────────────────────────────────────
    for step_id, payload in choices.items():
        if step_id.startswith("feature_") and "choice" in step_id:
            _audit(char, db, f"lvlup:{next_level}:{step_id}", payload, next_level)

    # ── Auto-grants (domain/patron/oath tier spells at this level, after subclass resolved) ──
    current_subclass = db.get(Subclass, cc.subclass_id) if cc.subclass_id else None
    if current_subclass:
        grant_ids = auto_grants(char, cc, cls, current_subclass, next_level, db)
        owned_ids = {cs.spell_id for cs in char.spells}
        for sid in grant_ids:
            if sid not in owned_ids:
                db.add(CharacterSpell(character_id=char.id, spell_id=sid,
                                      source="subclass", always_prepared=True, prepared=True))
                owned_ids.add(sid)
                spell = db.get(Spell, sid)
                if spell:
                    auto_added_spells.append(spell.name)

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
