"""Build character JSON dicts for export and the live sheet."""
import re
import math
from sqlalchemy.orm import Session
from ..models.character import Character
from ..models.content import DnDClass, Equipment as EquipmentModel


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


# ---------------------------------------------------------------------------
# Live sheet data — enriched, not intended for re-import
# ---------------------------------------------------------------------------

def _prof_bonus(level: int) -> int:
    return (level - 1) // 4 + 2


def _mod(score: int) -> int:
    return math.floor((score - 10) / 2)


def _calc_ac(formula: str, attrs: dict) -> int:
    dex = _mod(attrs.get("dex", 10))
    f = (formula or "").strip()
    if re.fullmatch(r"\d+", f):
        return int(f)
    m = re.match(r"(\d+)\s*\+\s*Dex(?:\s*\(max\s*(\d+)\))?", f, re.IGNORECASE)
    if m:
        base = int(m.group(1))
        cap = int(m.group(2)) if m.group(2) else 99
        return base + min(dex, cap)
    return 10 + dex


def _calc_attacks(char, attrs: dict, prof: int) -> list:
    str_mod = _mod(attrs.get("str", 10))
    dex_mod = _mod(attrs.get("dex", 10))
    attacks = []
    for ce in char.equipment:
        item = ce.equipment_item
        if not item or item.item_type != "weapon":
            continue
        props = [p.lower() for p in (item.properties or [])]
        cat = (item.category or "").lower()
        is_finesse = "finesse" in props
        is_ranged = "ranged" in cat
        stat_mod = max(str_mod, dex_mod) if is_finesse else (dex_mod if is_ranged else str_mod)
        attack_bonus = prof + stat_mod
        dmg = item.damage or "1"
        dmg_type = item.damage_type or ""
        dmg_str = (f"{dmg}+{stat_mod}" if stat_mod >= 0 else f"{dmg}{stat_mod}") + (f" {dmg_type}" if dmg_type else "")
        attacks.append({
            "name": item.name,
            "attack_bonus": attack_bonus,
            "damage": dmg_str,
            "properties": item.properties or [],
            "mastery_property": item.mastery_property,
            "category": item.category or "",
        })
    # Unarmed strike always available
    unarmed_dmg = f"1+{str_mod}" if str_mod >= 0 else f"1{str_mod}"
    attacks.append({
        "name": "Unarmed Strike",
        "attack_bonus": prof + str_mod,
        "damage": f"{unarmed_dmg} bludgeoning",
        "properties": [],
        "mastery_property": None,
        "category": "Melee",
        "is_unarmed": True,
    })
    return attacks


def character_to_sheet_dict(char: Character, db: Session) -> dict:
    cc = char.character_classes[0] if char.character_classes else None
    cls: DnDClass | None = db.get(DnDClass, cc.class_id) if cc else None
    level = cc.level if cc else 1
    prof = _prof_bonus(level)

    # Merged final ability scores
    base = char.base_attributes or {}
    asi = char.background_asi or {}
    attrs = {k: base.get(k, 10) + asi.get(k, 0) for k in ("str", "dex", "con", "int", "wis", "cha")}

    # AC: find first equipped armor, else unarmored
    ac = 10 + _mod(attrs["dex"])
    for ce in char.equipment:
        item = ce.equipment_item if ce.equipment_item else db.get(EquipmentModel, ce.equipment_id)
        if item and item.item_type == "armor" and ce.equipped:
            ac = _calc_ac(item.ac_formula or "", attrs)
            break

    # Shield bonus
    for ce in char.equipment:
        item = ce.equipment_item if ce.equipment_item else db.get(EquipmentModel, ce.equipment_id)
        if item and item.item_type == "shield" and ce.equipped:
            ac += 2
            break

    # Proficient skill names for quick lookup
    prof_skills = {s.skill_name for s in char.skill_proficiencies}
    expert_skills = {s.skill_name for s in char.skill_proficiencies if s.expertise}

    # Proficient saving throws from class
    save_profs = set(cls.saving_throws or []) if cls else set()

    # Class features at or below current level
    features = []
    if cls and cls.features:
        for f in cls.features:
            if f.get("level", 1) <= level:
                features.append({"name": f["name"], "description": f.get("description", ""), "level": f["level"]})

    # Species traits — filter the parent lineage/legacy/ancestry descriptor and
    # replace it with the selected lineage's specific description as its own entry.
    species_traits = []
    if char.species:
        selected = char.species_lineage
        for trait in (char.species.traits or []):
            if selected and re.search(r'lineage|legacy|ancestry', trait.get('name', ''), re.IGNORECASE):
                continue
            species_traits.append(trait)
        if selected and char.species.lineages:
            for lin in char.species.lineages:
                if lin.get('name') == selected:
                    species_traits.insert(0, {"name": selected, "description": lin.get('description', '')})
                    break

    # Feats with descriptions
    feats = []
    for cf in char.feats:
        if cf.feat:
            feats.append({"name": cf.feat.name, "description": cf.feat.description or "", "source": cf.source})

    # Spells with full details
    spells = []
    for cs in char.spells:
        sp = cs.spell
        if not sp:
            continue
        spells.append({
            "spell_id": cs.spell_id,
            "name": sp.name,
            "level": sp.level,
            "prepared": cs.prepared,
            "always_prepared": bool(cs.always_prepared),
            "source": cs.source or "class",
            "notes": cs.notes,
            "school": sp.school or "",
            "casting_time": sp.casting_time or "",
            "range": sp.spell_range or "",
            "components": sp.components or "",
            "duration": sp.duration or "",
            "concentration": sp.concentration,
            "ritual": sp.ritual,
            "description": sp.description or "",
        })
    spells.sort(key=lambda s: (s["level"], s["name"]))

    # Prepared spell tracking for prep casters
    PREP_CASTERS = {"cleric", "druid", "paladin", "ranger", "wizard"}
    class_lower = (cls.name if cls else "").lower()
    is_prep_caster = class_lower in PREP_CASTERS
    prepared_max = None
    prepared_count = None
    if is_prep_caster and cls:
        ab_map = {"intelligence": "int", "wisdom": "wis", "charisma": "cha"}
        sp_ab_key = ab_map.get((cls.spellcasting_ability or "").lower(), "int")
        sp_mod = (attrs.get(sp_ab_key, 10) - 10) // 2
        if class_lower in ("cleric", "druid", "wizard"):
            prepared_max = max(1, sp_mod + level)
        else:  # paladin, ranger
            prepared_max = max(1, sp_mod + (level // 2))
        prepared_count = sum(
            1 for cs in char.spells
            if cs.prepared and not cs.always_prepared
            and cs.source not in ("species", "arcanum")
            and cs.spell and cs.spell.level > 0
        )

    # Equipment with type details
    equipment = []
    for ce in char.equipment:
        item = ce.equipment_item
        eq = {
            "name": item.name if item else ce.custom_name,
            "quantity": ce.quantity,
            "equipped": ce.equipped,
            "item_type": item.item_type if item else None,
            "category": item.category if item else None,
            "damage": item.damage if item else None,
            "damage_type": item.damage_type if item else None,
            "properties": item.properties if item else [],
            "mastery_property": item.mastery_property if item else None,
            "ac_formula": item.ac_formula if item else None,
        }
        equipment.append(eq)

    return {
        "id": char.id,
        "character_name": char.character_name,
        "created_by_display_name": char.created_by_display_name,
        "owner_email": char.owner_email,
        "species_name": char.species.name if char.species else None,
        "species_lineage": char.species_lineage,
        "species_size": char.species_size_choice or (char.species.size_options[0] if char.species and char.species.size_options else "Medium"),
        "species_traits": species_traits,
        "background_name": char.background.name if char.background else None,
        "alignment": char.alignment,
        "bio": char.bio,
        "age": char.age,
        "height": char.height,
        "weight": char.weight,
        "deity": char.deity,
        "journal": char.journal,
        "physical_locked": bool(char.physical_locked),
        "currency": char.currency or {"pp": 0, "gp": 0, "sp": 0, "cp": 0},
        "class_name": cls.name if cls else None,
        "class_hit_die": cls.hit_die if cls else None,
        "class_saving_throws": list(save_profs),
        "class_spellcasting_type": cls.spellcasting_type if cls else None,
        "class_spellcasting_ability": cls.spellcasting_ability if cls else None,
        "level": level,
        "proficiency_bonus": prof,
        "ac": ac,
        "hp_max": char.hp_max,
        "hp_current": char.hp_current,
        "speed": char.speed,
        "spell_slots_used": char.spell_slots_used or {},
        "attributes": attrs,
        "prof_skills": list(prof_skills),
        "expert_skills": list(expert_skills),
        "save_profs": list(save_profs),
        "skill_proficiencies": [{"skill_name": s.skill_name, "expertise": s.expertise} for s in char.skill_proficiencies],
        "tool_proficiencies": [t.tool_name for t in char.tool_proficiencies],
        "language_proficiencies": [l.language_name for l in char.language_proficiencies],
        "weapon_mastery_unlocks": [w.weapon_name for w in char.weapon_mastery_unlocks],
        "class_features": features,
        "feats": feats,
        "spells": spells,
        "is_prep_caster": is_prep_caster,
        "prepared_max": prepared_max,
        "prepared_count": prepared_count,
        "equipment": equipment,
        "attacks": _calc_attacks(char, attrs, prof),
        "is_complete": char.is_complete,
    }
