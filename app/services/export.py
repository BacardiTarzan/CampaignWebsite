"""Build a complete character JSON dict, suitable for re-import."""
from sqlalchemy.orm import Session
from ..models.character import Character


def character_to_dict(char: Character, db: Session) -> dict:
    species = None
    if char.species:
        species = {"id": char.species.id, "name": char.species.name}

    background = None
    if char.background:
        background = {"id": char.background.id, "name": char.background.name}

    classes = []
    for cc in char.character_classes:
        classes.append({
            "class_id": cc.class_id,
            "class_name": cc.dnd_class.name if cc.dnd_class else None,
            "level": cc.level,
            "subclass_id": cc.subclass_id,
            "subclass_name": cc.subclass.name if cc.subclass else None,
        })

    feats = []
    for cf in char.feats:
        feats.append({
            "feat_id": cf.feat_id,
            "feat_name": cf.feat.name if cf.feat else None,
            "source": cf.source,
        })

    spells = []
    for cs in char.spells:
        spells.append({
            "spell_id": cs.spell_id,
            "spell_name": cs.spell.name if cs.spell else None,
            "level": cs.spell.level if cs.spell else None,
            "prepared": cs.prepared,
            "source_class_id": cs.source_class_id,
        })

    equipment = []
    for ce in char.equipment:
        equipment.append({
            "equipment_id": ce.equipment_id,
            "name": ce.equipment_item.name if ce.equipment_item else ce.custom_name,
            "quantity": ce.quantity,
            "equipped": ce.equipped,
        })

    skills = [
        {"skill_name": s.skill_name, "source": s.source, "expertise": s.expertise}
        for s in char.skill_proficiencies
    ]
    tools = [
        {"tool_name": t.tool_name, "source": t.source}
        for t in char.tool_proficiencies
    ]
    languages = [
        {"language_name": l.language_name, "source": l.source}
        for l in char.language_proficiencies
    ]
    choices = [
        {"feature_key": c.feature_key, "choice_value": c.choice_value}
        for c in char.choices
    ]
    masteries = [w.weapon_name for w in char.weapon_mastery_unlocks]

    return {
        "schema_version": "1.0",
        "id": char.id,
        "created_by_display_name": char.created_by_display_name,
        "character_name": char.character_name,
        "species": species,
        "background": background,
        "alignment": char.alignment,
        "bio": char.bio,
        "base_attributes": char.base_attributes,
        "background_asi": char.background_asi,
        "hp_max": char.hp_max,
        "hp_current": char.hp_current,
        "speed": char.speed,
        "equipment_choice": char.equipment_choice,
        "tool_proficiency_choice": char.tool_proficiency_choice,
        "classes": classes,
        "feats": feats,
        "spells": spells,
        "equipment": equipment,
        "skill_proficiencies": skills,
        "tool_proficiencies": tools,
        "language_proficiencies": languages,
        "choices": choices,
        "weapon_mastery_unlocks": masteries,
        "wizard_step": char.wizard_step,
        "is_complete": char.is_complete,
    }
