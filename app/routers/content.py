from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..dependencies import require_user
from ..models.content import Species, DnDClass, Background, Feat, Spell, Equipment, LorePage

router = APIRouter(prefix="/api/content", tags=["content"])


@router.get("/species")
def list_species(db: Session = Depends(get_db)):
    return db.query(Species).order_by(Species.name).all()


@router.get("/species/{species_id}")
def get_species(species_id: int, db: Session = Depends(get_db)):
    obj = db.get(Species, species_id)
    if not obj:
        raise HTTPException(404)
    return obj


@router.get("/classes")
def list_classes(db: Session = Depends(get_db)):
    return db.query(DnDClass).order_by(DnDClass.name).all()


@router.get("/classes/{class_id}")
def get_class(class_id: int, db: Session = Depends(get_db)):
    obj = db.get(DnDClass, class_id)
    if not obj:
        raise HTTPException(404)
    return {
        "id": obj.id,
        "name": obj.name,
        "hit_die": obj.hit_die,
        "primary_abilities": obj.primary_abilities,
        "saving_throws": obj.saving_throws,
        "armor_proficiencies": obj.armor_proficiencies,
        "weapon_proficiencies": obj.weapon_proficiencies,
        "skill_choices": obj.skill_choices,
        "skill_options": obj.skill_options,
        "spellcasting_type": obj.spellcasting_type,
        "spellcasting_ability": obj.spellcasting_ability,
        "equipment_options": obj.equipment_options,
        "features": obj.features,
        "subclasses": [
            {"id": s.id, "name": s.name, "unlock_level": s.unlock_level,
             "description": s.description, "features": s.features}
            for s in obj.subclasses
        ],
        "source": obj.source,
        "is_homebrew": obj.is_homebrew,
    }


@router.get("/backgrounds")
def list_backgrounds(db: Session = Depends(get_db)):
    return db.query(Background).order_by(Background.name).all()


@router.get("/backgrounds/{bg_id}")
def get_background(bg_id: int, db: Session = Depends(get_db)):
    obj = db.get(Background, bg_id)
    if not obj:
        raise HTTPException(404)
    return obj


@router.get("/feats")
def list_feats(category: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Feat)
    if category:
        q = q.filter(Feat.category == category)
    return q.order_by(Feat.name).all()


@router.get("/feats/{feat_id}")
def get_feat(feat_id: int, db: Session = Depends(get_db)):
    obj = db.get(Feat, feat_id)
    if not obj:
        raise HTTPException(404)
    return obj


@router.get("/spells")
def list_spells(
    level: int | None = None,
    class_name: str | None = None,
    db: Session = Depends(get_db),
):
    q = db.query(Spell)
    if level is not None:
        q = q.filter(Spell.level == level)
    spells = q.order_by(Spell.level, Spell.name).all()
    if class_name:
        spells = [s for s in spells if class_name in (s.classes or [])]
    return spells


@router.get("/spells/{spell_id}")
def get_spell(spell_id: int, db: Session = Depends(get_db)):
    obj = db.get(Spell, spell_id)
    if not obj:
        raise HTTPException(404)
    return obj


@router.get("/equipment")
def list_equipment(item_type: str | None = None, db: Session = Depends(get_db)):
    q = db.query(Equipment)
    if item_type:
        q = q.filter(Equipment.item_type == item_type)
    return q.order_by(Equipment.name).all()


@router.get("/lore", dependencies=[Depends(require_user)])
def list_lore(db: Session = Depends(get_db)):
    pages = db.query(LorePage).filter(LorePage.player_visible == True) \
               .order_by(LorePage.category, LorePage.title).all()
    return [{"slug": p.slug, "title": p.title, "category": p.category} for p in pages]


@router.get("/lore/{slug}", dependencies=[Depends(require_user)])
def get_lore_page(slug: str, db: Session = Depends(get_db)):
    page = db.query(LorePage).filter_by(slug=slug).first()
    if not page or not page.player_visible:
        raise HTTPException(404)
    return {"slug": page.slug, "title": page.title, "category": page.category,
            "content_md": page.content_md}
