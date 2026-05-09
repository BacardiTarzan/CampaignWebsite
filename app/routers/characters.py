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
from ..models.content import DnDClass, Background, Feat, Spell, Equipment, Species
from ..services.export import character_to_dict, character_to_sheet_dict
from ..config import settings
from ..services.pdf import render_character_pdf, render_character_html
import random

router = APIRouter(prefix="/api/characters", tags=["characters"])


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
        db.delete(cs)
    db.flush()

    cc = char.character_classes[0] if char.character_classes else None
    src_class_id = cc.class_id if cc else None

    for sid in data.cantrip_ids + data.spell_ids:
        db.add(CharacterSpell(
            character_id=char.id,
            spell_id=sid,
            prepared=True,
            source_class_id=src_class_id,
        ))

    char.wizard_step = max(char.wizard_step, 10)
    db.commit()
    return {"ok": True}


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


@router.get("/{char_id}/sheet-data")
def sheet_data(char_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)
    return character_to_sheet_dict(char, db)


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
