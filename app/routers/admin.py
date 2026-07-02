import re

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Any
from ..database import get_db
from ..dependencies import require_admin
from ..models.content import Species, DnDClass, Subclass, Background, Feat, Spell, Equipment, LorePage, Monster
from ..models.character import (
    Character, CharacterSpell, SkillProficiency, ToolProficiency,
    LanguageProficiency, WeaponMasteryUnlock, CharacterWeaponProficiency,
    CharacterFeat, CharacterClass, Combatant, EncounterState, CharacterResource,
)
from ..services.seeder import seed_all
from ..services.export import character_to_dict
from ..services.pdf import render_character_html, render_character_pdf
from ..services.levelup_rules import CLASS_ALWAYS_PREPARED, max_spell_level
from ..services.class_action_seeder import seed_class_abilities
from .characters import _parse_species_spell_grants
from .encounter import _broadcast_state

router = APIRouter(prefix="/api/admin", tags=["admin"], dependencies=[Depends(require_admin)])


# ---------------------------------------------------------------------------
# Roster
# ---------------------------------------------------------------------------

@router.get("/characters")
def list_characters(db: Session = Depends(get_db)):
    chars = db.query(Character).order_by(Character.created_at.desc()).all()
    result = []
    for c in chars:
        cc = c.character_classes[0] if c.character_classes else None
        base_attrs = c.base_attributes or {}
        bg_asi = c.background_asi or {}
        con_total = base_attrs.get("con", 10) + bg_asi.get("con", 0)
        result.append({
            "id": c.id,
            "created_by_display_name": c.created_by_display_name,
            "character_name": c.character_name,
            "species_name": c.species.name if c.species else None,
            "background_name": c.background.name if c.background else None,
            "class_name": cc.dnd_class.name if cc and cc.dnd_class else None,
            "level": cc.level if cc else None,
            "is_complete": c.is_complete,
            "wizard_step": c.wizard_step,
            "stat_roll_locked": c.stat_roll_locked,
            "physical_locked": bool(c.physical_locked),
            "hp_max": c.hp_max,
            "hp_current": c.hp_current,
            "level_granted": cc.level_granted if cc else None,
            "bio": c.bio,
            "created_at": c.created_at,
            "hit_dice_remaining": cc.hit_dice_remaining if cc else None,
            "hit_die": cc.dnd_class.hit_die if cc and cc.dnd_class else None,
            "class_level": cc.level if cc else None,
            "con_mod": (con_total - 10) // 2,
        })
    return result


@router.get("/characters/{char_id}/export/html", response_class=HTMLResponse)
def admin_view_character(char_id: int, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    char_dict = character_to_dict(char, db)
    cc = char.character_classes[0] if char.character_classes else None
    class_obj = db.get(DnDClass, cc.class_id) if cc else None
    return render_character_html(char_dict, class_obj=class_obj, species_obj=char.species, background_obj=char.background)


@router.get("/characters/{char_id}/export/json")
def admin_export_json(char_id: int, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    return character_to_dict(char, db)


@router.get("/characters/{char_id}/export/pdf")
def admin_export_pdf(char_id: int, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    char_dict = character_to_dict(char, db)
    cc = char.character_classes[0] if char.character_classes else None
    class_obj = db.get(DnDClass, cc.class_id) if cc else None
    pdf_bytes = render_character_pdf(char_dict, class_obj=class_obj, species_obj=char.species, background_obj=char.background)
    return Response(content=pdf_bytes, media_type="application/pdf",
                    headers={"Content-Disposition": f'attachment; filename="{char.character_name}.pdf"'})


@router.delete("/characters/{char_id}")
def delete_character(char_id: int, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    db.delete(char)
    db.commit()
    return {"ok": True}


class RenameCharIn(BaseModel):
    character_name: str

@router.patch("/characters/{char_id}/rename")
def rename_character(char_id: int, data: RenameCharIn, db: Session = Depends(get_db)):
    name = data.character_name.strip()
    if not name:
        raise HTTPException(400, "Name cannot be empty")
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    char.character_name = name
    db.commit()
    return {"ok": True, "character_name": char.character_name}


@router.post("/characters/{char_id}/unlock-stats")
def unlock_stats(char_id: int, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    char.stat_roll_locked = False
    db.commit()
    return {"ok": True}


@router.post("/characters/{char_id}/unlock-physical")
def unlock_physical(char_id: int, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    char.physical_locked = False
    db.commit()
    return {"ok": True}


class ShortRestIn(BaseModel):
    dice_rolls: list[int]

@router.post("/characters/{char_id}/short-rest")
def short_rest(char_id: int, data: ShortRestIn, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    cc = char.character_classes[0] if char.character_classes else None
    if not cc:
        raise HTTPException(400, "No class assigned")
    if (char.hp_current or 0) <= 0:
        raise HTTPException(400, "Cannot short rest at 0 HP")
    if len(data.dice_rolls) > (cc.hit_dice_remaining or 0):
        raise HTTPException(400, "Not enough hit dice remaining")
    if not data.dice_rolls:
        return {"ok": True, "hp_current": char.hp_current, "hp_max": char.hp_max,
                "hp_gained": 0, "hit_dice_remaining": cc.hit_dice_remaining or 0}

    base_attrs = char.base_attributes or {}
    bg_asi = char.background_asi or {}
    con_total = base_attrs.get("con", 10) + bg_asi.get("con", 0)
    con_mod = (con_total - 10) // 2
    die_size = cc.dnd_class.hit_die

    total = 0
    for roll in data.dice_rolls:
        die = max(1, min(int(roll), die_size))
        total += max(1, die + con_mod)

    new_hp = min(char.hp_max or 0, (char.hp_current or 0) + total)
    char.hp_current = new_hp
    cc.hit_dice_remaining = (cc.hit_dice_remaining or 0) - len(data.dice_rolls)
    db.commit()
    return {"ok": True, "hp_current": new_hp, "hp_max": char.hp_max,
            "hp_gained": total, "hit_dice_remaining": cc.hit_dice_remaining}


class AdminHpIn(BaseModel):
    delta: int | None = None
    set_hp: int | None = None

@router.post("/characters/{char_id}/hp")
def admin_adjust_hp(
    char_id: int,
    data: AdminHpIn,
    delta: int | None = None,
    set_hp: int | None = None,
    db: Session = Depends(get_db),
):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    # Body takes priority over query params
    effective_set = data.set_hp if data.set_hp is not None else set_hp
    effective_delta = data.delta if data.delta is not None else delta
    if effective_set is not None:
        char.hp_current = max(0, min(effective_set, char.hp_max or 0))
    elif effective_delta is not None:
        char.hp_current = max(0, min((char.hp_current or 0) + effective_delta, char.hp_max or 0))
    db.commit()
    return {"hp_current": char.hp_current, "hp_max": char.hp_max}


@router.post("/characters/{char_id}/level-up")
def grant_level(char_id: int, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    cc = char.character_classes[0] if char.character_classes else None
    if not cc:
        raise HTTPException(400, "No class assigned")
    if cc.level_granted is None:
        cc.level_granted = cc.level
    cc.level_granted += 1
    db.commit()
    return {"ok": True, "level_granted": cc.level_granted}


# ---------------------------------------------------------------------------
# Character proficiency / mastery / background admin edits
# ---------------------------------------------------------------------------

class AdminProficienciesIn(BaseModel):
    skills: list[str] = []             # full replacement list of skill proficiency names
    expertise: list[str] = []          # subset of skills that have expertise
    tools: list[str] = []              # full replacement list of tool proficiency names
    languages: list[str] = []          # full replacement list of language names


@router.patch("/characters/{char_id}/proficiencies")
def admin_set_proficiencies(char_id: int, data: AdminProficienciesIn, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)

    # Replace all skill proficiencies
    for sp in list(char.skill_proficiencies):
        db.delete(sp)
    for name in data.skills:
        if name:
            db.add(SkillProficiency(
                character_id=char_id,
                skill_name=name,
                source="admin",
                expertise=(name in data.expertise),
            ))

    # Replace all tool proficiencies
    for tp in list(char.tool_proficiencies):
        db.delete(tp)
    for name in data.tools:
        if name:
            db.add(ToolProficiency(character_id=char_id, tool_name=name, source="admin"))

    # Replace all language proficiencies
    for lp in list(char.language_proficiencies):
        db.delete(lp)
    for name in data.languages:
        if name:
            db.add(LanguageProficiency(character_id=char_id, language_name=name, source="admin"))

    db.commit()
    return {"ok": True}


class AdminMasteriesIn(BaseModel):
    weapon_names: list[str] = []   # full replacement list


@router.patch("/characters/{char_id}/masteries")
def admin_set_masteries(char_id: int, data: AdminMasteriesIn, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    for wm in list(char.weapon_mastery_unlocks):
        db.delete(wm)
    for name in data.weapon_names:
        if name:
            db.add(WeaponMasteryUnlock(character_id=char_id, weapon_name=name))
    db.commit()
    return {"ok": True}


class AdminBackgroundIn(BaseModel):
    background_id: int


@router.patch("/characters/{char_id}/background")
def admin_set_background(char_id: int, data: AdminBackgroundIn, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    bg = db.get(Background, data.background_id)
    if not bg:
        raise HTTPException(404, "Background not found")
    char.background_id = data.background_id
    # Re-apply background skill proficiencies (preserve class/admin skills)
    for sp in list(char.skill_proficiencies):
        if sp.source == "background":
            db.delete(sp)
    for skill in (bg.skill_proficiencies or []):
        db.add(SkillProficiency(character_id=char_id, skill_name=skill, source="background"))
    # Re-apply background tool proficiency
    for tp in list(char.tool_proficiencies):
        if tp.source == "background":
            db.delete(tp)
    if bg.tool_proficiency and "choose" not in (bg.tool_proficiency or "").lower():
        db.add(ToolProficiency(character_id=char_id, tool_name=bg.tool_proficiency, source="background"))
    # Re-apply origin feat (remove old background feat first)
    for cf in list(char.feats):
        if cf.source == "background":
            db.delete(cf)
    if bg.origin_feat_name:
        from ..models.content import Feat as FeatModel
        feat = db.query(FeatModel).filter(FeatModel.name.ilike(bg.origin_feat_name)).first()
        if feat:
            db.add(CharacterFeat(character_id=char_id, feat_id=feat.id, source="background"))
    db.commit()
    return {"ok": True, "background_name": bg.name}


class AdminWeaponProficienciesIn(BaseModel):
    proficiency_types: list[str] = []  # full replacement — categories and/or specific weapon names


@router.patch("/characters/{char_id}/weapon-proficiencies")
def admin_set_weapon_proficiencies(char_id: int, data: AdminWeaponProficienciesIn, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    for wp in list(char.weapon_proficiencies):
        db.delete(wp)
    for pt in data.proficiency_types:
        if pt:
            db.add(CharacterWeaponProficiency(character_id=char_id, proficiency_type=pt))
    db.commit()
    return {"ok": True}


class AdminSpeedCurrencyIn(BaseModel):
    speed: int | None = None
    pp: int = 0
    gp: int = 0
    sp: int = 0
    cp: int = 0


@router.patch("/characters/{char_id}/speed-currency")
def admin_set_speed_currency(char_id: int, data: AdminSpeedCurrencyIn, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    if data.speed is not None:
        char.speed = data.speed
    cur = dict(char.currency or {})
    cur.update({"pp": data.pp, "gp": data.gp, "sp": data.sp, "cp": data.cp})
    char.currency = cur
    db.commit()
    return {"ok": True}


@router.get("/characters/{char_id}/detail")
def admin_char_detail(char_id: int, db: Session = Depends(get_db)):
    """Return full proficiency/mastery/weapon data for the admin edit panel."""
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    # All weapons with full stats for tooltips
    all_weapons = [
        {
            "name": e.name,
            "category": e.category or "",
            "mastery": e.mastery_property,
            "damage": e.damage or "",
            "damage_type": e.damage_type or "",
            "properties": e.properties or [],
        }
        for e in db.query(Equipment)
              .filter(Equipment.item_type == "weapon")
              .order_by(Equipment.name).all()
    ]
    # All tools
    all_tools = [
        e.name
        for e in db.query(Equipment)
              .filter(Equipment.item_type == "tool")
              .order_by(Equipment.name).all()
    ]
    # Weapon proficiencies: use explicit rows if they exist, else derive from class as defaults
    _PROF_SHORTHAND = {
        "Simple":  "Simple Weapons",
        "Martial": "Martial Weapons",
        "Simple Melee":  "Simple Melee Weapons",
        "Martial Melee": "Martial Melee Weapons",
        "Simple Ranged":  "Simple Ranged Weapons",
        "Martial Ranged": "Martial Ranged Weapons",
    }
    if char.weapon_proficiencies:
        weapon_proficiencies = [wp.proficiency_type for wp in char.weapon_proficiencies]
    else:
        # Fall back to class weapon proficiencies (seeder shorthands → full names)
        cc = char.character_classes[0] if char.character_classes else None
        cls_profs = (cc.dnd_class.weapon_proficiencies or []) if cc and cc.dnd_class else []
        weapon_proficiencies = [_PROF_SHORTHAND.get(p, p) for p in cls_profs]
        # Also include mastery weapons from character_choices (step 6 creation wizard)
        # so the mastery column reflects the character's current state without a DB entry

    # Mastery: use WeaponMasteryUnlock rows; if empty fall back to CharacterChoice records
    # from creation wizard step 6 (feature_key starts with "weapon_mastery")
    mastery_names = [w.weapon_name for w in char.weapon_mastery_unlocks]
    if not mastery_names:
        for ch in char.choices:
            if ch.feature_key and ch.feature_key.startswith("weapon_mastery"):
                val = ch.choice_value
                if isinstance(val, list):
                    mastery_names.extend(val)
                elif isinstance(val, str) and val:
                    mastery_names.append(val)

    cur = dict(char.currency or {})
    return {
        "id": char.id,
        "character_name": char.character_name,
        "background_id": char.background_id,
        "background_name": char.background.name if char.background else None,
        "skills": [{"name": s.skill_name, "expertise": bool(s.expertise)} for s in char.skill_proficiencies],
        "tools": [t.tool_name for t in char.tool_proficiencies],
        "languages": [l.language_name for l in char.language_proficiencies],
        "masteries": mastery_names,
        "weapon_proficiencies": weapon_proficiencies,
        "all_weapons": all_weapons,
        "all_tools": all_tools,
        "speed": char.speed or 30,
        "currency": {
            "pp": cur.get("pp", 0),
            "gp": cur.get("gp", 0),
            "sp": cur.get("sp", 0),
            "cp": cur.get("cp", 0),
        },
    }


# ---------------------------------------------------------------------------
# Codex — CRUD for content types
# ---------------------------------------------------------------------------

class SpeciesIn(BaseModel):
    name: str
    creature_type: str = "Humanoid"
    size_options: list[str] = ["Medium"]
    speed: int = 30
    traits: list[dict] = []
    source: str = "Homebrew"
    is_homebrew: bool = True


@router.get("/codex/species")
def admin_list_species(db: Session = Depends(get_db)):
    return db.query(Species).order_by(Species.name).all()


@router.post("/codex/species")
def admin_create_species(data: SpeciesIn, db: Session = Depends(get_db)):
    obj = Species(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/codex/species/{sid}")
def admin_update_species(sid: int, data: SpeciesIn, db: Session = Depends(get_db)):
    obj = db.get(Species, sid)
    if not obj:
        raise HTTPException(404)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    return obj


@router.delete("/codex/species/{sid}")
def admin_delete_species(sid: int, db: Session = Depends(get_db)):
    obj = db.get(Species, sid)
    if not obj:
        raise HTTPException(404)
    db.delete(obj)
    db.commit()
    return {"ok": True}


class BackgroundIn(BaseModel):
    name: str
    ability_score_options: list[str]
    origin_feat_name: str | None = None
    skill_proficiencies: list[str] = []
    tool_proficiency: str | None = None
    language_count: int = 0
    equipment_options: list[dict] = []
    description: str = ""
    source: str = "Homebrew"
    is_homebrew: bool = True


@router.get("/codex/backgrounds")
def admin_list_backgrounds(db: Session = Depends(get_db)):
    return db.query(Background).order_by(Background.name).all()


@router.post("/codex/backgrounds")
def admin_create_background(data: BackgroundIn, db: Session = Depends(get_db)):
    obj = Background(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/codex/backgrounds/{bid}")
def admin_update_background(bid: int, data: BackgroundIn, db: Session = Depends(get_db)):
    obj = db.get(Background, bid)
    if not obj:
        raise HTTPException(404)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    return obj


@router.delete("/codex/backgrounds/{bid}")
def admin_delete_background(bid: int, db: Session = Depends(get_db)):
    obj = db.get(Background, bid)
    if not obj:
        raise HTTPException(404)
    db.delete(obj)
    db.commit()
    return {"ok": True}


class FeatIn(BaseModel):
    name: str
    category: str
    prerequisites: list[str] | None = None
    description: str = ""
    source: str = "Homebrew"
    is_homebrew: bool = True


@router.get("/codex/feats")
def admin_list_feats(db: Session = Depends(get_db)):
    return db.query(Feat).order_by(Feat.name).all()


@router.post("/codex/feats")
def admin_create_feat(data: FeatIn, db: Session = Depends(get_db)):
    obj = Feat(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/codex/feats/{fid}")
def admin_update_feat(fid: int, data: FeatIn, db: Session = Depends(get_db)):
    obj = db.get(Feat, fid)
    if not obj:
        raise HTTPException(404)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    return obj


@router.delete("/codex/feats/{fid}")
def admin_delete_feat(fid: int, db: Session = Depends(get_db)):
    obj = db.get(Feat, fid)
    if not obj:
        raise HTTPException(404)
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Codex — Equipment CRUD
# ---------------------------------------------------------------------------

class EquipmentIn(BaseModel):
    name: str
    item_type: str
    category: str | None = None
    cost: str | None = None
    weight: str | None = None
    damage_rolls: list[dict] | None = None   # [{"dice":"1d8","type":"Slashing"}, …]
    properties: list[str] | None = None
    mastery_property: str | None = None
    proficiency_base: str | None = None
    ac_formula: str | None = None
    strength_req: int | None = None
    stealth_disadvantage: bool = False
    magic_bonus: int | None = None
    description: str | None = None
    source: str = "Homebrew"
    is_homebrew: bool = True


@router.get("/codex/equipment")
def admin_list_equipment(db: Session = Depends(get_db)):
    return db.query(Equipment).order_by(Equipment.item_type, Equipment.name).all()


def _sync_damage_legacy(obj: Equipment, damage_rolls):
    """Keep legacy damage/damage_type columns in sync with damage_rolls[0] for backward compat."""
    first = (damage_rolls or [None])[0]
    obj.damage = first.get("dice") if first else None
    obj.damage_type = first.get("type") if first else None


@router.post("/codex/equipment")
def admin_create_equipment(data: EquipmentIn, db: Session = Depends(get_db)):
    obj = Equipment(**data.model_dump())
    _sync_damage_legacy(obj, data.damage_rolls)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/codex/equipment/{eid}")
def admin_update_equipment(eid: int, data: EquipmentIn, db: Session = Depends(get_db)):
    obj = db.get(Equipment, eid)
    if not obj:
        raise HTTPException(404)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    _sync_damage_legacy(obj, data.damage_rolls)
    db.commit()
    return obj


@router.delete("/codex/equipment/{eid}")
def admin_delete_equipment(eid: int, db: Session = Depends(get_db)):
    obj = db.get(Equipment, eid)
    if not obj:
        raise HTTPException(404)
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# Grimoire — Spell CRUD
# ---------------------------------------------------------------------------

class SpellIn(BaseModel):
    name: str
    level: int
    school: str = ""
    casting_time: str = ""
    spell_range: str = ""
    components: str = ""
    duration: str = ""
    concentration: bool = False
    ritual: bool = False
    classes: list[str] = []
    description: str = ""
    source: str = "Homebrew"
    is_homebrew: bool = True


@router.get("/grimoire/spells")
def admin_list_spells(db: Session = Depends(get_db)):
    return db.query(Spell).order_by(Spell.level, Spell.name).all()


@router.post("/grimoire/spells")
def admin_create_spell(data: SpellIn, db: Session = Depends(get_db)):
    obj = Spell(**data.model_dump())
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.put("/grimoire/spells/{sid}")
def admin_update_spell(sid: int, data: SpellIn, db: Session = Depends(get_db)):
    obj = db.get(Spell, sid)
    if not obj:
        raise HTTPException(404)
    for k, v in data.model_dump().items():
        setattr(obj, k, v)
    db.commit()
    return obj


@router.delete("/grimoire/spells/{sid}")
def admin_delete_spell(sid: int, db: Session = Depends(get_db)):
    obj = db.get(Spell, sid)
    if not obj:
        raise HTTPException(404)
    db.delete(obj)
    db.commit()
    return {"ok": True}


# ---------------------------------------------------------------------------
# JSON import endpoints
# ---------------------------------------------------------------------------

@router.post("/import/species")
def import_species(items: list[SpeciesIn], db: Session = Depends(get_db)):
    added = 0
    for data in items:
        if not db.query(Species).filter_by(name=data.name).first():
            db.add(Species(**data.model_dump()))
            added += 1
    db.commit()
    return {"added": added}


@router.post("/import/backgrounds")
def import_backgrounds(items: list[BackgroundIn], db: Session = Depends(get_db)):
    added = 0
    for data in items:
        if not db.query(Background).filter_by(name=data.name).first():
            db.add(Background(**data.model_dump()))
            added += 1
    db.commit()
    return {"added": added}


@router.post("/import/feats")
def import_feats(items: list[FeatIn], db: Session = Depends(get_db)):
    added = 0
    for data in items:
        if not db.query(Feat).filter_by(name=data.name).first():
            db.add(Feat(**data.model_dump()))
            added += 1
    db.commit()
    return {"added": added}


@router.post("/import/spells")
def import_spells(items: list[SpellIn], db: Session = Depends(get_db)):
    added = 0
    for data in items:
        if not db.query(Spell).filter_by(name=data.name).first():
            db.add(Spell(**data.model_dump()))
            added += 1
    db.commit()
    return {"added": added}


# ---------------------------------------------------------------------------
# Lore management
# ---------------------------------------------------------------------------

@router.get("/lore")
def admin_list_lore(db: Session = Depends(get_db)):
    pages = db.query(LorePage).order_by(LorePage.category, LorePage.title).all()
    return [{"slug": p.slug, "title": p.title, "category": p.category,
             "player_visible": p.player_visible} for p in pages]


@router.get("/lore/{slug}")
def admin_get_lore(slug: str, db: Session = Depends(get_db)):
    page = db.query(LorePage).filter_by(slug=slug).first()
    if not page:
        raise HTTPException(404)
    return {"slug": page.slug, "title": page.title, "category": page.category,
            "player_visible": page.player_visible, "content_md": page.content_md}


@router.patch("/lore/{slug}/visibility")
def admin_set_lore_visibility(slug: str, visible: bool, db: Session = Depends(get_db)):
    page = db.query(LorePage).filter_by(slug=slug).first()
    if not page:
        raise HTTPException(404)
    page.player_visible = visible
    db.commit()
    return {"ok": True, "player_visible": page.player_visible}


# ---------------------------------------------------------------------------
# Schema repair — add missing columns if alembic didn't apply them
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Combat tracker
# ---------------------------------------------------------------------------

class CombatantCharIn(BaseModel):
    character_id: int

class CombatantMonsterIn(BaseModel):
    monster_id: int

class CombatantHpIn(BaseModel):
    hp_current: int

VALID_CONDITIONS = {
    "Blinded", "Charmed", "Deafened", "Frightened", "Grappled",
    "Incapacitated", "Invisible", "Paralyzed", "Petrified", "Poisoned",
    "Prone", "Restrained", "Stunned", "Unconscious",
}

class ConditionsIn(BaseModel):
    conditions: list[str]


class InitiativeIn(BaseModel):
    initiative: int


class ActionEconomyIn(BaseModel):
    action_used: bool | None = None
    bonus_action_used: bool | None = None
    reaction_used: bool | None = None
    movement_remaining: int | None = None
    legendary_actions_remaining: int | None = None


def _cr_sort_key(cr: str | None) -> float:
    if not cr:
        return -1
    if "/" in cr:
        num, den = cr.split("/")
        return int(num) / int(den)
    try:
        return float(cr)
    except ValueError:
        return -1


@router.get("/monsters")
def list_monsters(db: Session = Depends(get_db)):
    monsters = db.query(Monster).order_by(Monster.name).all()
    return [
        {
            "id": m.id,
            "name": m.name,
            "size": m.size,
            "creature_type": m.creature_type,
            "cr": m.cr,
            "xp": m.xp,
            "ac": m.ac,
            "hp_max": m.hp_max,
            "hp_formula": m.hp_formula,
            "speed": m.speed,
            "alignment": m.alignment,
        }
        for m in monsters
    ]


@router.get("/monsters/{monster_id}")
def get_monster(monster_id: int, db: Session = Depends(get_db)):
    m = db.get(Monster, monster_id)
    if not m:
        raise HTTPException(404)
    return {
        "id": m.id, "name": m.name, "size": m.size, "creature_type": m.creature_type,
        "alignment": m.alignment, "ac": m.ac, "initiative": m.initiative,
        "hp_max": m.hp_max, "hp_formula": m.hp_formula, "speed": m.speed,
        "cr": m.cr, "xp": m.xp, "proficiency_bonus": m.proficiency_bonus,
        "str": m.str_, "dex": m.dex_, "con": m.con_,
        "int": m.int_, "wis": m.wis_, "cha": m.cha_,
        "saving_throws": m.saving_throws, "skills": m.skills,
        "resistances": m.resistances, "immunities": m.immunities,
        "vulnerabilities": m.vulnerabilities, "senses": m.senses,
        "languages": m.languages, "gear": m.gear,
        "traits": m.traits or [], "actions": m.actions or [],
        "bonus_actions": m.bonus_actions or [],
        "reactions": m.reactions or [],
        "legendary_actions": m.legendary_actions or [],
    }


@router.get("/combatants")
def list_combatants(db: Session = Depends(get_db)):
    rows = db.query(Combatant).order_by(Combatant.added_at).all()
    result = []
    for row in rows:
        if row.character_id:
            char = row.character
            cc = char.character_classes[0] if char.character_classes else None
            result.append({
                "combatant_id": row.id,
                "kind": "character",
                "character_id": char.id,
                "name": char.character_name,
                "hp_current": char.hp_current,
                "hp_max": char.hp_max,
                "speed": char.speed or 30,
                "class_name": cc.dnd_class.name if cc else None,
                "level": cc.level if cc else None,
                "species_name": char.species.name if char.species else None,
                "species_lineage": char.species_lineage,
                "conditions": char.conditions or [],
            })
        else:
            m = db.get(Monster, row.monster_id)
            if not m:
                continue
            result.append({
                "combatant_id": row.id,
                "kind": "monster",
                "monster_id": m.id,
                "name": row.custom_name or m.name,
                "hp_current": row.hp_current,
                "hp_max": row.hp_max_override or m.hp_max,
                "ac": m.ac,
                "speed": m.speed,
                "cr": m.cr,
                "creature_type": m.creature_type,
                "conditions": row.conditions or [],
            })
    return result


@router.post("/combatants/character")
async def add_character_combatant(data: CombatantCharIn, db: Session = Depends(get_db)):
    char = db.get(Character, data.character_id)
    if not char:
        raise HTTPException(404, "Character not found")
    existing = db.query(Combatant).filter_by(character_id=data.character_id).first()
    if existing:
        raise HTTPException(409, "Character is already in combat")
    c = Combatant(character_id=data.character_id)
    db.add(c)
    db.commit()
    db.refresh(c)
    # Auto-seed class abilities as CharacterResource rows (skips existing rows)
    seed_class_abilities(char, db)
    await _broadcast_state(db)
    return {"ok": True, "combatant_id": c.id}


@router.post("/combatants/monster")
async def add_monster_combatant(data: CombatantMonsterIn, db: Session = Depends(get_db)):
    m = db.get(Monster, data.monster_id)
    if not m:
        raise HTTPException(404, "Monster not found")
    existing_count = db.query(Combatant).filter_by(monster_id=data.monster_id).count()
    custom_name = f"{m.name} {existing_count + 1}"
    c = Combatant(
        monster_id=data.monster_id,
        custom_name=custom_name,
        hp_current=m.hp_max,
        hp_max_override=m.hp_max,
    )
    db.add(c)
    db.commit()
    db.refresh(c)
    await _broadcast_state(db)
    return {"ok": True, "combatant_id": c.id, "name": custom_name}


@router.patch("/combatants/{combatant_id}/hp")
async def set_combatant_hp(combatant_id: int, data: CombatantHpIn, db: Session = Depends(get_db)):
    c = db.get(Combatant, combatant_id)
    if not c:
        raise HTTPException(404)
    if c.monster_id:
        c.hp_current = max(0, data.hp_current)
        db.commit()
        await _broadcast_state(db)
        return {"ok": True, "hp_current": c.hp_current, "hp_max": c.hp_max_override}
    raise HTTPException(400, "Use the character HP endpoint for PC combatants")


@router.patch("/combatants/{combatant_id}/conditions")
async def set_combatant_conditions(combatant_id: int, data: ConditionsIn, db: Session = Depends(get_db)):
    c = db.get(Combatant, combatant_id)
    if not c:
        raise HTTPException(404)

    validated: list[str] = []
    for cond in data.conditions:
        if cond in VALID_CONDITIONS:
            validated.append(cond)
        elif cond.startswith("Exhaustion:"):
            level_str = cond.split(":", 1)[1]
            if level_str.isdigit() and 1 <= int(level_str) <= 6:
                validated.append(cond)
            else:
                raise HTTPException(400, f"Invalid Exhaustion level in '{cond}'; must be Exhaustion:1 through Exhaustion:6")
        else:
            raise HTTPException(400, f"Unknown condition: '{cond}'")

    if c.character_id:
        char = db.get(Character, c.character_id)
        if not char:
            raise HTTPException(404, "Character not found")
        char.conditions = validated or None
    else:
        c.conditions = validated or None

    db.commit()
    await _broadcast_state(db)
    return {"ok": True, "conditions": validated}


@router.delete("/combatants/{combatant_id}")
async def remove_combatant(combatant_id: int, db: Session = Depends(get_db)):
    c = db.get(Combatant, combatant_id)
    if not c:
        raise HTTPException(404)
    db.delete(c)
    db.commit()
    await _broadcast_state(db)
    return {"ok": True}


@router.post("/combatants/clear")
async def clear_combatants(db: Session = Depends(get_db)):
    removed = db.query(Combatant).delete()
    db.commit()
    await _broadcast_state(db)
    return {"ok": True, "removed": removed}


# ---------------------------------------------------------------------------
# Encounter state management
# ---------------------------------------------------------------------------

def _get_or_create_enc(db: Session) -> EncounterState:
    state = db.get(EncounterState, 1)
    if not state:
        from sqlalchemy.exc import IntegrityError
        try:
            state = EncounterState(id=1)
            db.add(state)
            db.commit()
            db.refresh(state)
        except IntegrityError:
            db.rollback()
            state = db.get(EncounterState, 1)
    return state


def _recompute_turn_order(db: Session):
    """Rank combatants by initiative descending (ties keep insertion order). Caller commits."""
    rows = db.query(Combatant).order_by(
        Combatant.initiative.desc().nullslast(), Combatant.added_at
    ).all()
    rank = 1
    for row in rows:
        if row.initiative is not None:
            row.turn_order = rank
            rank += 1
        else:
            row.turn_order = None
    # No db.commit() here — caller is responsible


def _reset_combatant_turn(row: Combatant, db: Session):
    """Reset action economy at start of this combatant's turn. Caller is responsible for db.commit()."""
    row.action_used = False
    row.bonus_action_used = False
    row.reaction_used = False
    # Restore movement to full speed
    if row.character_id and row.character:
        row.movement_remaining = row.character.speed if row.character.speed is not None else 30
    # For monsters: movement was set at initiative entry; leave as-is (already set to their speed)


@router.post("/encounter/start")
async def start_encounter(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """Begin initiative phase: encounter is active, DM enters initiatives."""
    state = _get_or_create_enc(db)
    state.encounter_active = True
    state.initiative_phase = True
    state.current_round = 1
    state.current_turn_combatant_id = None
    # Reset all combatant action economy and initiative
    for row in db.query(Combatant).all():
        row.action_used = False
        row.bonus_action_used = False
        row.reaction_used = False
        row.initiative = None
        row.turn_order = None
        row.movement_remaining = None
    db.commit()
    await _broadcast_state(db)
    return {"ok": True}


@router.post("/encounter/begin-round-1")
async def begin_round_one(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """After all initiatives entered: close initiative phase and start turn 1."""
    state = _get_or_create_enc(db)
    if not state.encounter_active:
        raise HTTPException(400, "No active encounter")
    _recompute_turn_order(db)
    first = db.query(Combatant).filter(Combatant.turn_order.isnot(None)).order_by(Combatant.turn_order).first()
    if not first:
        raise HTTPException(400, "No initiatives entered yet — enter at least one initiative before beginning")
    state.initiative_phase = False
    state.current_turn_combatant_id = first.id
    _reset_combatant_turn(first, db)
    db.commit()
    await _broadcast_state(db)
    return {"ok": True, "current_turn_combatant_id": state.current_turn_combatant_id}


@router.post("/encounter/advance-turn")
async def advance_turn(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """Move to next combatant in initiative order; increment round if wrapping."""
    state = _get_or_create_enc(db)
    if not state.encounter_active or state.initiative_phase:
        raise HTTPException(400, "Encounter not in progress")

    ordered = db.query(Combatant).filter(
        Combatant.turn_order.isnot(None)
    ).order_by(Combatant.turn_order).all()
    if not ordered:
        raise HTTPException(400, "No combatants in initiative order")

    current_ids = [c.id for c in ordered]
    try:
        idx = current_ids.index(state.current_turn_combatant_id)
    except ValueError:
        idx = -1  # current combatant not in order — go to first

    next_idx = idx + 1
    if next_idx >= len(ordered):
        next_idx = 0
        state.current_round += 1

    next_combatant = ordered[next_idx]
    state.current_turn_combatant_id = next_combatant.id
    _reset_combatant_turn(next_combatant, db)
    db.commit()
    await _broadcast_state(db)
    return {
        "ok": True,
        "current_round": state.current_round,
        "current_turn_combatant_id": state.current_turn_combatant_id,
    }


@router.post("/encounter/end")
async def end_encounter(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    """Reset encounter state. Does NOT clear combatants (use /combatants/clear for that)."""
    state = _get_or_create_enc(db)
    state.encounter_active = False
    state.initiative_phase = False
    state.current_round = 1
    state.current_turn_combatant_id = None
    for row in db.query(Combatant).all():
        row.initiative = None
        row.turn_order = None
        row.action_used = False
        row.bonus_action_used = False
        row.reaction_used = False
        row.movement_remaining = None
        row.legendary_actions_remaining = None
    db.commit()
    await _broadcast_state(db)
    return {"ok": True}


@router.patch("/combatants/{combatant_id}/initiative")
async def set_initiative(
    combatant_id: int,
    body: InitiativeIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    row = db.get(Combatant, combatant_id)
    if not row:
        raise HTTPException(404)
    row.initiative = body.initiative
    # Set movement_remaining from speed if not yet set for this encounter
    if row.movement_remaining is None:
        if row.character_id and row.character:
            row.movement_remaining = row.character.speed if row.character.speed is not None else 30
        elif row.monster_id:
            m = db.get(Monster, row.monster_id)
            if m and m.speed:
                # Monster speed is a string like "30 ft., climb 20 ft."
                # Extract the first numeric value
                match = re.search(r"\d+", m.speed.strip())
                row.movement_remaining = int(match.group()) if match else 30
    db.flush()               # write initiative to session before recomputing ranks
    _recompute_turn_order(db)
    db.commit()              # single commit
    await _broadcast_state(db)
    return {"ok": True, "initiative": row.initiative, "turn_order": row.turn_order}


@router.patch("/combatants/{combatant_id}/actions")
async def update_action_economy(
    combatant_id: int,
    body: ActionEconomyIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    row = db.get(Combatant, combatant_id)
    if not row:
        raise HTTPException(404)
    if body.action_used is not None:
        row.action_used = body.action_used
    if body.bonus_action_used is not None:
        row.bonus_action_used = body.bonus_action_used
    if body.reaction_used is not None:
        row.reaction_used = body.reaction_used
    if body.movement_remaining is not None:
        row.movement_remaining = body.movement_remaining
    if body.legendary_actions_remaining is not None:
        row.legendary_actions_remaining = body.legendary_actions_remaining
    db.commit()
    await _broadcast_state(db)
    return {"ok": True}


@router.post("/repair-schema")
def repair_schema(db: Session = Depends(get_db)):
    """Add missing columns and tables. Safe to re-run on both SQLite and PostgreSQL."""
    from sqlalchemy import text, inspect as sa_inspect
    from ..database import engine

    is_pg = engine.dialect.name == "postgresql"

    # ALTER TABLE: PostgreSQL supports IF NOT EXISTS; SQLite does not, so check via inspector.
    def add_col(table, col, col_def):
        if is_pg:
            db.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {col_def}"))
        else:
            try:
                existing = {c["name"] for c in sa_inspect(engine).get_columns(table)}
            except Exception:
                return  # table doesn't exist yet; CREATE TABLE below will handle it
            if col not in existing:
                db.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {col_def}"))

    add_col("character_spells", "source", "VARCHAR")
    add_col("character_spells", "notes", "TEXT")
    add_col("characters", "height", "VARCHAR")
    add_col("characters", "weight", "VARCHAR")
    add_col("characters", "deity", "VARCHAR")
    add_col("characters", "journal", "TEXT")
    add_col("characters", "currency", "JSON")
    add_col("characters", "physical_locked", "BOOLEAN DEFAULT FALSE")
    add_col("characters", "age", "INTEGER")
    add_col("character_classes", "level_granted", "INTEGER")
    add_col("character_spells", "always_prepared", "BOOLEAN DEFAULT FALSE")
    add_col("character_choices", "level", "INTEGER")
    add_col("characters", "hp_roll_log", "JSON")
    add_col("classes", "tool_proficiencies", "JSON")
    add_col("equipment", "magic_bonus", "INTEGER")
    add_col("equipment", "proficiency_base", "VARCHAR")
    add_col("equipment", "damage_rolls", "JSON")
    add_col("characters", "conditions", "JSON")
    add_col("combatants",  "conditions", "JSON")

    # CREATE TABLE: SERIAL is PostgreSQL; INTEGER PRIMARY KEY is the SQLite equivalent.
    pk = "SERIAL" if is_pg else "INTEGER"

    db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS character_weapon_proficiencies (
            id {pk} PRIMARY KEY,
            character_id INTEGER NOT NULL REFERENCES characters(id),
            proficiency_type VARCHAR NOT NULL
        )
    """))
    db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS glossary_terms (
            id {pk} PRIMARY KEY,
            slug VARCHAR UNIQUE NOT NULL,
            term VARCHAR NOT NULL,
            category VARCHAR NOT NULL,
            short_description TEXT NOT NULL,
            full_description TEXT NOT NULL,
            ability VARCHAR,
            source VARCHAR DEFAULT 'PHB 2024'
        )
    """))
    db.execute(text("CREATE INDEX IF NOT EXISTS ix_glossary_terms_slug ON glossary_terms (slug)"))
    # monsters must be created before combatants (FK dependency)
    db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS monsters (
            id {pk} PRIMARY KEY,
            name VARCHAR UNIQUE NOT NULL,
            size VARCHAR, creature_type VARCHAR, alignment VARCHAR,
            ac INTEGER, initiative VARCHAR, hp_max INTEGER, hp_formula VARCHAR,
            speed VARCHAR, cr VARCHAR, xp INTEGER, proficiency_bonus INTEGER,
            str INTEGER, dex INTEGER, con INTEGER, "int" INTEGER, wis INTEGER, cha INTEGER,
            saving_throws VARCHAR, skills VARCHAR, resistances VARCHAR,
            immunities VARCHAR, vulnerabilities VARCHAR, senses VARCHAR,
            languages VARCHAR, gear VARCHAR,
            traits JSON, actions JSON, bonus_actions JSON, reactions JSON, legendary_actions JSON,
            source VARCHAR, is_homebrew BOOLEAN DEFAULT FALSE
        )
    """))
    # On SQLite, the combatants table may have been created with character_id NOT NULL
    # (from an earlier create_all before the model was fixed). SQLite can't ALTER COLUMN,
    # so drop and recreate. Combatants are ephemeral combat state — no data loss concern.
    if not is_pg:
        try:
            cols = sa_inspect(engine).get_columns("combatants")
            char_col = next((c for c in cols if c["name"] == "character_id"), None)
            if char_col and not char_col.get("nullable", True):
                db.execute(text("DROP TABLE IF EXISTS combatants"))
        except Exception:
            pass
    db.execute(text(f"""
        CREATE TABLE IF NOT EXISTS combatants (
            id {pk} PRIMARY KEY,
            character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
            monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
            custom_name VARCHAR,
            hp_current INTEGER,
            hp_max_override INTEGER,
            added_at TIMESTAMP
        )
    """))
    # Phase 5 — encounter and resource columns
    phase5_combatant_cols = [
        ("combatants", "initiative",                 "INTEGER"),
        ("combatants", "turn_order",                 "INTEGER"),
        ("combatants", "action_used",                "BOOLEAN DEFAULT FALSE"),
        ("combatants", "bonus_action_used",          "BOOLEAN DEFAULT FALSE"),
        ("combatants", "reaction_used",              "BOOLEAN DEFAULT FALSE"),
        ("combatants", "movement_remaining",         "INTEGER"),
        ("combatants", "legendary_actions_remaining","INTEGER"),
    ]
    for table, col, ddl in phase5_combatant_cols:
        add_col(table, col, ddl)

    # encounter_state table
    if is_pg:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS encounter_state (
                id INTEGER PRIMARY KEY DEFAULT 1,
                encounter_active BOOLEAN NOT NULL DEFAULT FALSE,
                initiative_phase BOOLEAN NOT NULL DEFAULT FALSE,
                current_round INTEGER NOT NULL DEFAULT 1,
                current_turn_combatant_id INTEGER REFERENCES combatants(id) ON DELETE SET NULL
            )
        """))
        db.execute(text("INSERT INTO encounter_state (id) VALUES (1) ON CONFLICT DO NOTHING"))
    else:
        existing_tables = sa_inspect(engine).get_table_names()
        if "encounter_state" not in existing_tables:
            db.execute(text("""
                CREATE TABLE encounter_state (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    encounter_active BOOLEAN NOT NULL DEFAULT 0,
                    initiative_phase BOOLEAN NOT NULL DEFAULT 0,
                    current_round INTEGER NOT NULL DEFAULT 1,
                    current_turn_combatant_id INTEGER REFERENCES combatants(id) ON DELETE SET NULL
                )
            """))
        db.execute(text("INSERT OR IGNORE INTO encounter_state (id) VALUES (1)"))

    # character_resources table
    if is_pg:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS character_resources (
                id SERIAL PRIMARY KEY,
                character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
                resource_key VARCHAR NOT NULL,
                label VARCHAR NOT NULL,
                max_uses INTEGER NOT NULL DEFAULT 1,
                used INTEGER NOT NULL DEFAULT 0,
                rest_type VARCHAR NOT NULL DEFAULT 'long'
            )
        """))
    else:
        existing_tables = sa_inspect(engine).get_table_names()
        if "character_resources" not in existing_tables:
            db.execute(text("""
                CREATE TABLE character_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
                    resource_key VARCHAR NOT NULL,
                    label VARCHAR NOT NULL,
                    max_uses INTEGER NOT NULL DEFAULT 1,
                    used INTEGER NOT NULL DEFAULT 0,
                    rest_type VARCHAR NOT NULL DEFAULT 'long'
                )
            """))

    db.commit()
    applied = [
        "character_spells.source", "character_spells.notes", "character_spells.always_prepared",
        "characters.height/weight/deity/journal/currency/physical_locked/age/hp_roll_log",
        "character_classes.level_granted", "character_choices.level", "classes.tool_proficiencies",
        "tables: character_weapon_proficiencies, glossary_terms, monsters, combatants",
        "phase5: combatants action economy columns, encounter_state table, character_resources table",
    ]
    return {"ok": True, "applied": applied}


# ---------------------------------------------------------------------------
# Backfill species spell grants
# ---------------------------------------------------------------------------

@router.post("/backfill-species-spells")
def backfill_species_spells(db: Session = Depends(get_db)):
    """Add missing species spell grants to existing characters. Idempotent."""
    import traceback
    try:
        chars = db.query(Character).filter(Character.species_id.isnot(None)).all()
        total_added = 0
        results = []
        for char in chars:
            if not char.species:
                continue
            grants = _parse_species_spell_grants(char.species, char.species_lineage)
            added = 0
            for grant in grants:
                spell = db.query(Spell).filter(
                    func.lower(Spell.name) == grant["name"].lower()
                ).first()
                if not spell:
                    continue
                already = db.query(CharacterSpell).filter_by(
                    character_id=char.id,
                    spell_id=spell.id,
                    source="species",
                ).first()
                if already:
                    continue
                db.add(CharacterSpell(
                    character_id=char.id,
                    spell_id=spell.id,
                    source="species",
                    notes=grant.get("notes"),
                ))
                added += 1
            total_added += added
            results.append({"character": char.character_name, "added": added})
        db.commit()
        return {"total_added": total_added, "characters": results}
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{e}\n\n{tb}")


# ---------------------------------------------------------------------------
# Backfill class always-prepared spells (e.g. Ranger → Hunter's Mark)
# ---------------------------------------------------------------------------

@router.post("/backfill-class-spells")
def backfill_class_spells(db: Session = Depends(get_db)):
    """Add missing class always-prepared spells to existing characters. Idempotent."""
    import traceback
    try:
        chars = db.query(Character).all()
        total_added = 0
        results = []
        for char in chars:
            cc = char.character_classes[0] if char.character_classes else None
            if not cc:
                continue
            cls_obj = db.get(DnDClass, cc.class_id)
            if not cls_obj or cls_obj.name not in CLASS_ALWAYS_PREPARED:
                continue
            existing_ids = {cs.spell_id for cs in char.spells}
            added = 0
            for min_lvl, spell_names in CLASS_ALWAYS_PREPARED[cls_obj.name].items():
                for name in spell_names:
                    spell = db.query(Spell).filter(func.lower(Spell.name) == name.lower()).first()
                    if not spell or spell.id in existing_ids:
                        continue
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
                    added += 1
            total_added += added
            if added:
                results.append({"character": char.character_name, "added": added})
        db.commit()
        return {"total_added": total_added, "characters": results}
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{e}\n\n{tb}")


@router.post("/backfill-prepared-caster-spells")
def backfill_prepared_caster_spells(db: Session = Depends(get_db)):
    """Populate full class spell list (prepared=False) for existing Cleric/Ranger characters."""
    import traceback
    try:
        PREPARED_CASTERS = {"Cleric", "Ranger"}
        chars = db.query(Character).all()
        total_added = 0
        results = []
        for char in chars:
            cc = char.character_classes[0] if char.character_classes else None
            if not cc:
                continue
            cls_obj = db.get(DnDClass, cc.class_id)
            if not cls_obj or cls_obj.name not in PREPARED_CASTERS:
                continue
            sp_type = cls_obj.spellcasting_type or ""
            max_sl = max_spell_level(sp_type, cc.level) if sp_type else 0
            if max_sl == 0:
                continue
            owned_ids = {cs.spell_id for cs in char.spells}
            candidate_spells = (
                db.query(Spell)
                .filter(Spell.level <= max_sl, Spell.level > 0)
                .all()
            )
            class_spells = [s for s in candidate_spells if cls_obj.name in (s.classes or [])]
            added = 0
            for sp in class_spells:
                if sp.id not in owned_ids:
                    db.add(CharacterSpell(
                        character_id=char.id,
                        spell_id=sp.id,
                        source="class",
                        prepared=False,
                    ))
                    owned_ids.add(sp.id)
                    added += 1
            total_added += added
            if added:
                results.append({"character": char.character_name, "added": added})
        db.commit()
        return {"total_added": total_added, "characters": results}
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{e}\n\n{tb}")


# ---------------------------------------------------------------------------
# Convert gold equipment rows → currency.gp
# ---------------------------------------------------------------------------

@router.post("/convert-gold")
def convert_gold(db: Session = Depends(get_db)):
    """Move custom 'Gold' equipment rows into character currency.gp. Idempotent."""
    from ..models.character import CharacterEquipment
    rows = db.query(CharacterEquipment).filter(
        CharacterEquipment.equipment_id.is_(None),
        CharacterEquipment.custom_name == "Gold",
    ).all()
    converted = 0
    for row in rows:
        char = row.character
        if not char:
            continue
        cur = dict(char.currency or {})
        cur.setdefault("pp", 0); cur.setdefault("gp", 0)
        cur.setdefault("sp", 0); cur.setdefault("cp", 0)
        cur["gp"] = cur["gp"] + (row.quantity or 0)
        char.currency = cur
        db.delete(row)
        converted += 1
    db.commit()
    return {"ok": True, "converted": converted}


# ---------------------------------------------------------------------------
# Force-refresh spell descriptions
# ---------------------------------------------------------------------------

@router.post("/refresh-spells")
def refresh_spells(db: Session = Depends(get_db)):
    """Re-parse all spell markdown files and update any spells with empty descriptions."""
    import traceback
    try:
        from ..services.seeder import seed_all
        counts = seed_all(db)
        return {"refreshed": counts.get("spells", 0)}
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{e}\n\n{tb}")


# ---------------------------------------------------------------------------
# Seed trigger
# ---------------------------------------------------------------------------

@router.post("/seed")
def trigger_seed(db: Session = Depends(get_db)):
    import traceback
    try:
        counts = seed_all(db)
        return {"seeded": counts}
    except Exception as e:
        tb = traceback.format_exc()
        raise HTTPException(status_code=500, detail=f"{e}\n\n{tb}")


# ---------------------------------------------------------------------------
# Character resource admin
# ---------------------------------------------------------------------------

COMMON_RESOURCES = [
    {"resource_key": "second_wind",        "label": "Second Wind",        "max_uses": 1, "rest_type": "short"},
    {"resource_key": "action_surge",       "label": "Action Surge",       "max_uses": 1, "rest_type": "short"},
    {"resource_key": "rage",               "label": "Rage",               "max_uses": 3, "rest_type": "long"},
    {"resource_key": "ki_points",          "label": "Ki Points",          "max_uses": 2, "rest_type": "short"},
    {"resource_key": "channel_divinity",   "label": "Channel Divinity",   "max_uses": 1, "rest_type": "short"},
    {"resource_key": "wild_shape",         "label": "Wild Shape",         "max_uses": 2, "rest_type": "short"},
    {"resource_key": "bardic_inspiration", "label": "Bardic Inspiration", "max_uses": 4, "rest_type": "short"},
    {"resource_key": "sorcery_points",     "label": "Sorcery Points",     "max_uses": 4, "rest_type": "long"},
    {"resource_key": "heroic_inspiration", "label": "Heroic Inspiration", "max_uses": 1, "rest_type": "long"},
]


@router.get("/common-resources")
def list_common_resources(_admin=Depends(require_admin)):
    return COMMON_RESOURCES


class AddResourceIn(BaseModel):
    resource_key: str
    label: str
    max_uses: int
    rest_type: str  # "short" | "long" | "encounter"
    action_type: str | None = None


@router.post("/characters/{char_id}/resources")
def add_resource(
    char_id: int,
    body: AddResourceIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    if body.rest_type not in ("short", "long", "encounter"):
        raise HTTPException(400, "rest_type must be short, long, or encounter")
    if body.max_uses < 1:
        raise HTTPException(400, "max_uses must be at least 1")
    # Upsert: if resource_key already exists for this character, update it
    existing = db.query(CharacterResource).filter_by(
        character_id=char_id, resource_key=body.resource_key
    ).first()
    if existing:
        existing.label = body.label
        existing.max_uses = body.max_uses
        existing.rest_type = body.rest_type
        if body.action_type is not None:
            existing.action_type = body.action_type
        # Clamp used so it never exceeds the new max_uses
        if existing.used > body.max_uses:
            existing.used = body.max_uses
        db.commit()
        return {"id": existing.id, "resource_key": existing.resource_key,
                "label": existing.label, "max_uses": existing.max_uses,
                "used": existing.used, "rest_type": existing.rest_type,
                "action_type": existing.action_type}
    res = CharacterResource(
        character_id=char_id,
        resource_key=body.resource_key,
        label=body.label,
        max_uses=body.max_uses,
        used=0,
        rest_type=body.rest_type,
        action_type=body.action_type,
    )
    db.add(res)
    db.commit()
    db.refresh(res)
    return {"id": res.id, "resource_key": res.resource_key, "label": res.label,
            "max_uses": res.max_uses, "used": 0, "rest_type": res.rest_type}


@router.delete("/characters/{char_id}/resources/{resource_id}")
def delete_resource(
    char_id: int,
    resource_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    res = db.get(CharacterResource, resource_id)
    if not res or res.character_id != char_id:
        raise HTTPException(404)
    db.delete(res)
    db.commit()
    return {"ok": True}


class AdminResourceAdjIn(BaseModel):
    amount: int = 1  # number of uses to spend or restore; -1 to restore all


@router.post("/characters/{char_id}/resources/{resource_id}/spend")
def admin_spend_resource(
    char_id: int,
    resource_id: int,
    body: AdminResourceAdjIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """DM spends uses of a character resource (e.g. trigger Indomitable)."""
    res = db.get(CharacterResource, resource_id)
    if not res or res.character_id != char_id:
        raise HTTPException(404)
    new_used = min(res.max_uses, res.used + body.amount)
    res.used = new_used
    db.commit()
    return {"id": res.id, "used": res.used, "remaining": res.max_uses - res.used}


@router.post("/characters/{char_id}/resources/{resource_id}/restore")
def admin_restore_resource(
    char_id: int,
    resource_id: int,
    body: AdminResourceAdjIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """DM restores uses of a character resource. amount=-1 restores all."""
    res = db.get(CharacterResource, resource_id)
    if not res or res.character_id != char_id:
        raise HTTPException(404)
    if body.amount == -1:
        res.used = 0
    else:
        res.used = max(0, res.used - body.amount)
    db.commit()
    return {"id": res.id, "used": res.used, "remaining": res.max_uses - res.used}


class AdminRestIn(BaseModel):
    rest_type: str  # "short" | "long"


@router.post("/characters/{char_id}/rest")
def admin_rest(
    char_id: int,
    body: AdminRestIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_admin),
):
    """DM-triggered rest for a character."""
    if body.rest_type not in ("short", "long"):
        raise HTTPException(400, "rest_type must be short or long")
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    resources = db.query(CharacterResource).filter_by(character_id=char_id).all()
    restored = []
    for res in resources:
        should_restore = (body.rest_type == "long" or res.rest_type in ("short", "encounter"))
        if should_restore and res.used > 0:
            res.used = 0
            restored.append(res.resource_key)
    if body.rest_type == "long":
        char.hp_current = char.hp_max
        char.spell_slots_used = {}
        for cc in char.character_classes:
            cc.hit_dice_remaining = cc.level
    else:
        for cc in char.character_classes:
            half = max(1, (cc.level + 1) // 2)
            cc.hit_dice_remaining = min(cc.level, cc.hit_dice_remaining + half)
    db.commit()
    return {"ok": True, "restored_resources": restored, "rest_type": body.rest_type}
