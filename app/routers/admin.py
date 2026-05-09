from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import HTMLResponse, Response
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Any
from ..database import get_db
from ..dependencies import require_admin
from ..models.content import Species, DnDClass, Subclass, Background, Feat, Spell, Equipment, LorePage
from ..models.character import Character
from ..services.seeder import seed_all
from ..services.export import character_to_dict
from ..services.pdf import render_character_html, render_character_pdf

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
            "hp_max": c.hp_max,
            "hp_current": c.hp_current,
            "created_at": c.created_at,
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


@router.post("/characters/{char_id}/unlock-stats")
def unlock_stats(char_id: int, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    char.stat_roll_locked = False
    db.commit()
    return {"ok": True}


@router.post("/characters/{char_id}/rest")
def long_rest(char_id: int, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    char.hp_current = char.hp_max
    char.spell_slots_used = {}
    db.commit()
    return {"ok": True, "hp_current": char.hp_current}


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
def level_up(char_id: int, db: Session = Depends(get_db)):
    char = db.get(Character, char_id)
    if not char:
        raise HTTPException(404)
    cc = char.character_classes[0] if char.character_classes else None
    if not cc:
        raise HTTPException(400, "No class assigned")
    cc.level += 1
    db.commit()
    return {"ok": True, "new_level": cc.level}


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
