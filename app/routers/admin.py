from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel
from typing import Any
from ..database import get_db
from ..dependencies import require_admin
from ..models.content import Species, DnDClass, Subclass, Background, Feat, Spell, Equipment, LorePage
from ..models.character import (
    Character, CharacterSpell, SkillProficiency, ToolProficiency,
    LanguageProficiency, WeaponMasteryUnlock, CharacterFeat, CharacterClass,
)
from ..services.seeder import seed_all
from ..services.export import character_to_dict
from ..services.pdf import render_character_html, render_character_pdf
from .characters import _parse_species_spell_grants

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


@router.post("/characters/{char_id}/rest")
def long_rest(char_id: int, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    char.hp_current = char.hp_max
    char.spell_slots_used = {}
    # 2024 RAW: all spent hit dice recovered on long rest
    for cc in char.character_classes:
        cc.hit_dice_remaining = cc.level
    db.commit()
    return {"ok": True, "hp_current": char.hp_current}


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


@router.post("/characters/{char_id}/hp")
def admin_adjust_hp(char_id: int, delta: int | None = None, set_hp: int | None = None, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    if set_hp is not None:
        char.hp_current = max(0, min(set_hp, char.hp_max or 0))
    elif delta is not None:
        char.hp_current = max(0, min((char.hp_current or 0) + delta, char.hp_max or 0))
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


@router.get("/characters/{char_id}/detail")
def admin_char_detail(char_id: int, db: Session = Depends(get_db)):
    """Return full proficiency/mastery data + available weapons/tools for the admin edit panel."""
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    # All weapons that have a mastery property (for mastery picker)
    mastery_weapons = [
        {"name": e.name, "mastery": e.mastery_property}
        for e in db.query(Equipment)
              .filter(Equipment.item_type == "weapon", Equipment.mastery_property.isnot(None))
              .order_by(Equipment.name).all()
    ]
    # All tools
    all_tools = [
        e.name
        for e in db.query(Equipment)
              .filter(Equipment.item_type == "tool")
              .order_by(Equipment.name).all()
    ]
    return {
        "id": char.id,
        "character_name": char.character_name,
        "background_id": char.background_id,
        "background_name": char.background.name if char.background else None,
        "skills": [{"name": s.skill_name, "expertise": bool(s.expertise)} for s in char.skill_proficiencies],
        "tools": [t.tool_name for t in char.tool_proficiencies],
        "languages": [l.language_name for l in char.language_proficiencies],
        "masteries": [w.weapon_name for w in char.weapon_mastery_unlocks],
        "all_mastery_weapons": mastery_weapons,
        "all_tools": all_tools,
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

@router.post("/repair-schema")
def repair_schema(db: Session = Depends(get_db)):
    """Add source/notes columns to character_spells if missing. Safe to re-run."""
    from sqlalchemy import text
    stmts = [
        "ALTER TABLE character_spells ADD COLUMN IF NOT EXISTS source VARCHAR",
        "ALTER TABLE character_spells ADD COLUMN IF NOT EXISTS notes TEXT",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS height VARCHAR",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS weight VARCHAR",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS deity VARCHAR",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS journal TEXT",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS currency JSON",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS physical_locked BOOLEAN DEFAULT FALSE",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS age INTEGER",
        "ALTER TABLE character_classes ADD COLUMN IF NOT EXISTS level_granted INTEGER",
        "ALTER TABLE character_spells ADD COLUMN IF NOT EXISTS always_prepared BOOLEAN DEFAULT FALSE",
        "ALTER TABLE character_choices ADD COLUMN IF NOT EXISTS level INTEGER",
        "ALTER TABLE characters ADD COLUMN IF NOT EXISTS hp_roll_log JSON",
        "ALTER TABLE classes ADD COLUMN IF NOT EXISTS tool_proficiencies JSON",
    ]
    for stmt in stmts:
        db.execute(text(stmt))
    # Create glossary_terms table if it doesn't exist (Phase 6)
    db.execute(text("""
        CREATE TABLE IF NOT EXISTS glossary_terms (
            id SERIAL PRIMARY KEY,
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
    db.commit()
    return {"ok": True, "applied": stmts}


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
