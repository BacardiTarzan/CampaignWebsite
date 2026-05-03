"""
Parse reference/ markdown files and seed the database.
Safe to re-run: skips records that already exist by name.
"""
import re
from pathlib import Path
from sqlalchemy.orm import Session

from ..config import settings
from ..models.content import Species, DnDClass, Subclass, Background, Feat, Spell, Equipment

REF = Path(settings.reference_dir)

# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _field(text: str, key: str) -> str | None:
    m = re.search(rf"\*\*{re.escape(key)}[:\s]*\*\*\s*(.+)", text)
    return m.group(1).strip() if m else None


def _split_list(value: str) -> list[str]:
    return [v.strip() for v in re.split(r",\s*", value) if v.strip()]


# ---------------------------------------------------------------------------
# Equipment option parser
# ---------------------------------------------------------------------------

def _parse_equipment_options(raw: str) -> list[dict]:
    """
    Parse strings like:
      (A) Chain Mail, Greatsword, 4 GP; (B) Studded Leather, 11 GP; or (C) 155 GP
    Returns:
      [{"label":"A","items":[{"name":"Chain Mail","qty":1,"type":"fixed"},...]},
       {"label":"B","gold":155,"items":[]}]
    """
    options = []
    # Split on option boundaries like "; (B)" or "; or (C)"
    parts = re.split(r";\s*(?:or\s*)?\(([A-Z])\)\s*", raw)
    # parts[0] is the content after "(A)", then pairs of (label, content)
    # Extract the first label
    first_label_m = re.match(r"\(([A-Z])\)\s*(.*)", raw, re.DOTALL)
    if not first_label_m:
        return []
    first_label = first_label_m.group(1)
    first_content = first_label_m.group(2)
    # Re-split cleanly
    raw_clean = re.sub(r"\s+", " ", raw.strip())
    # Find all option blocks: (X) content
    blocks = re.findall(r"\(([A-Z])\)\s*([^(]*?)(?=\s*;?\s*(?:or\s*)?\([A-Z]\)|$)", raw_clean)
    if not blocks:
        return []
    for label, content in blocks:
        content = content.strip().rstrip(";").strip()
        opt = {"label": label, "items": []}
        # Is this a gold-only option?
        gold_m = re.match(r"^(\d+)\s*GP$", content, re.IGNORECASE)
        if gold_m:
            opt["gold"] = int(gold_m.group(1))
        else:
            opt["items"] = _parse_item_list(content)
        options.append(opt)
    return options


def _parse_item_list(raw: str) -> list[dict]:
    """Parse a comma-separated item string into structured items."""
    items = []
    # Split by comma, but respect parentheses
    parts = _smart_split(raw)
    for part in parts:
        part = part.strip()
        if not part:
            continue
        item = _parse_single_item(part)
        if item:
            items.append(item)
    return items


def _smart_split(s: str) -> list[str]:
    """Split by comma while respecting parentheses."""
    parts = []
    depth = 0
    current = []
    for ch in s:
        if ch == "(":
            depth += 1
            current.append(ch)
        elif ch == ")":
            depth -= 1
            current.append(ch)
        elif ch == "," and depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    if current:
        parts.append("".join(current).strip())
    return parts


def _parse_single_item(s: str) -> dict | None:
    s = s.strip()
    if not s:
        return None

    # Gold: "15 GP", "8 GP"
    gp_m = re.match(r"^(\d+)\s*GP$", s, re.IGNORECASE)
    if gp_m:
        return {"name": "Gold", "qty": int(gp_m.group(1)), "type": "gold"}

    # Quantity prefix: "4 Handaxes", "2 Daggers", "20 Arrows", "8 Javelins"
    qty_m = re.match(r"^(\d+)\s+(.+)$", s)
    qty = 1
    name = s
    if qty_m:
        qty = int(qty_m.group(1))
        name = qty_m.group(2).strip()

    # Detect choices
    choice_keywords = [
        "Musical Instrument", "Artisan's Tool", "Gaming Set",
        "Tool or Instrument", "Tool/Instrument",
    ]
    for kw in choice_keywords:
        if kw.lower() in name.lower():
            return {"name": name, "qty": qty, "type": "choice", "category": kw}

    # "same as above" / "$tool_proficiency" reference
    if "same as above" in name.lower():
        return {"name": "$tool_proficiency", "qty": qty, "type": "ref"}

    # Gaming Set (any) — also a choice
    if re.search(r"gaming set", name, re.IGNORECASE) and "any" in name.lower():
        return {"name": name, "qty": qty, "type": "choice", "category": "Gaming Set"}

    return {"name": name, "qty": qty, "type": "fixed"}


# ---------------------------------------------------------------------------
# Species
# ---------------------------------------------------------------------------

def _parse_species_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    name = re.match(r"^#\s+(.+)", text).group(1).strip().title()

    creature_type = _field(text, "Creature Type") or "Humanoid"

    size_raw = _field(text, "Size") or "Medium"
    sizes = []
    if "Medium" in size_raw:
        sizes.append("Medium")
    if "Small" in size_raw:
        sizes.append("Small")
    if "Large" in size_raw:
        sizes.append("Large")
    if not sizes:
        sizes = ["Medium"]

    speed_raw = _field(text, "Speed") or "30"
    speed_m = re.search(r"(\d+)", speed_raw)
    speed = int(speed_m.group(1)) if speed_m else 30

    # Parse traits
    traits = []
    traits_section = re.search(r"### Traits\n+(.*?)(?=\n###|\Z)", text, re.DOTALL)
    if traits_section:
        for block in re.split(r"\n\n(?=\*\*)", traits_section.group(1)):
            m = re.match(r"\*\*([^*]+?):\*\*\s*(.*)", block, re.DOTALL)
            if m:
                traits.append({"name": m.group(1).strip(), "description": re.sub(r"\s+", " ", m.group(2)).strip()})

    return {
        "name": name,
        "creature_type": creature_type,
        "size_options": sizes,
        "speed": speed,
        "traits": traits,
        "source": "PHB 2024",
    }


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

SPELLCASTING_MAP = {
    "bard": ("full", "Charisma"),
    "cleric": ("full", "Wisdom"),
    "druid": ("full", "Wisdom"),
    "sorcerer": ("full", "Charisma"),
    "wizard": ("full", "Intelligence"),
    "paladin": ("half", "Charisma"),
    "ranger": ("half", "Wisdom"),
    "warlock": ("pact", "Charisma"),
}

HIT_DIE_MAP = {
    "barbarian": 12, "fighter": 10, "paladin": 10, "ranger": 10,
    "bard": 8, "cleric": 8, "druid": 8, "monk": 8, "rogue": 8, "warlock": 8,
    "sorcerer": 6, "wizard": 6,
}


def _parse_class_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    slug = path.stem
    name = re.match(r"^#\s+(.+)", text).group(1).strip().title()

    # Armor proficiencies
    armor_raw = _field(text, "Armor Training") or ""
    armors = []
    for a in ["Light", "Medium", "Heavy", "Shields"]:
        if a.lower() in armor_raw.lower():
            armors.append(a)

    # Weapon proficiencies
    weapon_raw = _field(text, "Weapon Proficiencies") or ""
    weapons = []
    for w in ["Simple", "Martial"]:
        if w.lower() in weapon_raw.lower():
            weapons.append(w)

    # Skill choices
    skill_raw = _field(text, "Skill Proficiencies")
    skill_choices = 2
    skill_options = []
    if skill_raw:
        cm = re.search(r"choose\s+(\d+)", skill_raw, re.IGNORECASE)
        if cm:
            skill_choices = int(cm.group(1))
        after_colon = re.sub(r".*?:\s*", "", skill_raw, count=1)
        skill_options = _split_list(after_colon)

    # Starting equipment
    equip_raw = _field(text, "Starting Equipment") or ""
    equipment_options = _parse_equipment_options(equip_raw)

    # Saving throws
    st_raw = _field(text, "Saving Throws") or ""
    saving_throws = _split_list(st_raw)

    # Primary abilities
    pa_raw = _field(text, "Primary Ability") or ""
    primary_abilities = [a.strip() for a in re.split(r"\s+or\s+|\s+and\s+|,", pa_raw) if a.strip()]

    # Hit die
    hd_raw = _field(text, "Hit Point Die") or f"d{HIT_DIE_MAP.get(slug, 8)}"
    hd_m = re.search(r"d(\d+)", hd_raw)
    hit_die = int(hd_m.group(1)) if hd_m else HIT_DIE_MAP.get(slug, 8)

    # Spellcasting
    sc_type, sc_ability = SPELLCASTING_MAP.get(slug, (None, None))

    # Features from Key Features section
    features = []
    kf_section = re.search(r"### Key Features\n+(.*?)(?=\n###|\Z)", text, re.DOTALL)
    if kf_section:
        for block in re.split(r"\n\n(?=\*\*)", kf_section.group(1)):
            m = re.match(r"\*\*([^*]+?)\s*\(Level\s*(\d+)\):\*\*\s*(.*)", block, re.DOTALL)
            if not m:
                continue
            feat_name = m.group(1).strip()
            level = int(m.group(2))
            desc = re.sub(r"\s+", " ", m.group(3)).strip()
            choice_required = False
            choice_key = None
            options = []
            if slug == "fighter" and "fighting style" in feat_name.lower():
                choice_required = True
                choice_key = "fighting_style"
                options = [
                    "Archery", "Defense", "Dueling", "Great Weapon Fighting",
                    "Protection", "Two-Weapon Fighting",
                ]
            elif slug == "fighter" and "weapon mastery" in feat_name.lower():
                choice_required = True
                choice_key = "weapon_mastery"
            elif slug == "cleric" and "divine order" in feat_name.lower():
                choice_required = True
                choice_key = "divine_order"
                options = ["Protector", "Thaumaturge"]
            elif slug == "cleric" and "blessed strikes" in feat_name.lower():
                choice_required = True
                choice_key = "blessed_strikes"
                options = ["Divine Strike", "Potent Spellcasting"]
            features.append({
                "name": feat_name, "level": level, "description": desc,
                "choice_required": choice_required,
                "choice_key": choice_key,
                "options": options,
            })

    # Subclasses
    subclasses = _parse_subclasses(text, slug)

    return {
        "name": name,
        "hit_die": hit_die,
        "primary_abilities": primary_abilities,
        "saving_throws": saving_throws,
        "armor_proficiencies": armors,
        "weapon_proficiencies": weapons,
        "skill_choices": skill_choices,
        "skill_options": skill_options,
        "spellcasting_type": sc_type,
        "spellcasting_ability": sc_ability,
        "equipment_options": equipment_options,
        "features": features,
        "subclasses": subclasses,
        "source": "PHB 2024",
    }


def _parse_subclasses(text: str, class_slug: str) -> list[dict]:
    subclasses = []
    sc_section = re.search(r"### Subclasses\n+(.*?)(?=\n##[^#]|\Z)", text, re.DOTALL)
    if not sc_section:
        return []

    unlock_level = 3  # most classes unlock at 3

    sc_text = sc_section.group(1)
    # Split by #### subclass headers (may have blank lines before)
    sc_blocks = re.split(r"\n+#### (.+)", sc_text)
    for i in range(1, len(sc_blocks), 2):
        sc_name = sc_blocks[i].strip()
        sc_body = sc_blocks[i + 1] if i + 1 < len(sc_blocks) else ""
        # Domain spells line (Cleric)
        desc_m = re.search(r"\*Domain Spells[^*]*\*:\s*(.+?)(?=\n|$)", sc_body)
        desc = desc_m.group(0).strip() if desc_m else ""
        # Subclass features: "- **Name (Level N):** description"
        features = []
        for block in sc_body.split("\n- "):
            m = re.match(r"\*\*([^*]+?)\s*\(Level\s*(\d+)\):\*\*\s*(.*)", block, re.DOTALL)
            if m:
                features.append({
                    "name": m.group(1).strip(),
                    "level": int(m.group(2)),
                    "description": re.sub(r"\s+", " ", m.group(3)).strip(),
                })
        subclasses.append({
            "name": sc_name,
            "unlock_level": unlock_level,
            "description": desc,
            "features": features,
        })
    return subclasses


# ---------------------------------------------------------------------------
# Backgrounds
# ---------------------------------------------------------------------------

def _parse_background_file(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    name = re.match(r"^#\s+(.+)", text).group(1).strip().title()

    ability_raw = _field(text, "Ability Scores") or ""
    ability_score_options = _split_list(ability_raw)

    feat_raw = _field(text, "Feat") or ""

    skills_raw = _field(text, "Skill Proficiencies") or ""
    skill_proficiencies = _split_list(skills_raw)

    tool_raw = _field(text, "Tool Proficiency") or None

    equip_raw = _field(text, "Equipment") or ""
    equipment_options = _parse_equipment_options(equip_raw)

    return {
        "name": name,
        "ability_score_options": ability_score_options,
        "origin_feat_name": feat_raw,
        "skill_proficiencies": skill_proficiencies,
        "tool_proficiency": tool_raw,
        "language_count": 0,
        "equipment_options": equipment_options,
        "description": "",
        "source": "PHB 2024",
    }


# ---------------------------------------------------------------------------
# Feats
# ---------------------------------------------------------------------------

CATEGORY_MAP = {
    "origin": "origin",
    "general": "general",
    "fighting-style": "fighting_style",
    "epic-boon": "epic_boon",
}


def _parse_feat_file(path: Path, category: str) -> dict:
    text = path.read_text(encoding="utf-8")
    name = re.match(r"^#\s+(.+)", text).group(1).strip().title()

    # Everything after the structured fields is the description
    body = re.sub(r"\*\*Category:\*\*.*?\n", "", text)
    body = re.sub(r"^#.+\n", "", body).strip()

    # Prerequisites
    prereq_raw = _field(text, "Prerequisite") or _field(text, "Prerequisites")
    prerequisites = _split_list(prereq_raw) if prereq_raw else None

    return {
        "name": name,
        "category": category,
        "prerequisites": prerequisites,
        "description": body,
        "source": "PHB 2024",
    }


# ---------------------------------------------------------------------------
# Spells
# ---------------------------------------------------------------------------

def _parse_spell_file(path: Path, level: int) -> dict:
    text = path.read_text(encoding="utf-8")
    name = re.match(r"^#\s+(.+)", text).group(1).strip().title()

    school = _field(text, "School") or ""
    casting_time = _field(text, "Casting Time") or ""
    spell_range = _field(text, "Range") or ""
    components = _field(text, "Components") or ""
    duration = _field(text, "Duration") or ""
    classes_raw = _field(text, "Classes") or ""
    classes = _split_list(classes_raw)

    concentration = "concentration" in duration.lower() or bool(re.search(r"Concentration", text))
    ritual = bool(re.search(r"\*\*Ritual\*\*|ritual.*?spell", text, re.IGNORECASE))

    # Description is everything after the structured fields block
    desc_m = re.search(r"\n\n(.+)", text, re.DOTALL)
    description = desc_m.group(1).strip() if desc_m else ""

    return {
        "name": name,
        "level": level,
        "school": school,
        "casting_time": casting_time,
        "spell_range": spell_range,
        "components": components,
        "duration": duration,
        "concentration": concentration,
        "ritual": ritual,
        "classes": classes,
        "description": description,
        "source": "PHB 2024",
    }


# ---------------------------------------------------------------------------
# Equipment (weapons + armor from tables)
# ---------------------------------------------------------------------------

def _parse_weapons_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    items = []
    current_category = "Simple Melee"

    for line in text.splitlines():
        # Category headers
        if "## Simple Melee" in line:
            current_category = "Simple Melee"
        elif "## Simple Ranged" in line:
            current_category = "Simple Ranged"
        elif "## Martial Melee" in line:
            current_category = "Martial Melee"
        elif "## Martial Ranged" in line:
            current_category = "Martial Ranged"

        # Table rows (not header or separator)
        if line.startswith("| ") and not re.match(r"\|[-\s|]+\|", line) and "Name" not in line:
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) < 6:
                continue
            name, damage_full, props_raw, mastery, weight, cost = cols[:6]
            if not name or name.startswith("-"):
                continue
            damage_m = re.match(r"(.+?)\s+(Slashing|Piercing|Bludgeoning|Force|Radiant)", damage_full)
            damage = damage_m.group(1) if damage_m else damage_full
            damage_type = damage_m.group(2) if damage_m else ""
            properties = [p.strip() for p in props_raw.split(",") if p.strip() and p.strip() != "—"]
            item_type = "Simple" if "Simple" in current_category else "Martial"
            items.append({
                "name": name.strip(),
                "item_type": "weapon",
                "category": current_category,
                "cost": cost.strip(),
                "weight": weight.strip(),
                "damage": damage.strip(),
                "damage_type": damage_type.strip(),
                "properties": properties,
                "mastery_property": mastery.strip() if mastery.strip() != "—" else None,
                "source": "PHB 2024",
            })
    return items


def _parse_armor_file(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    items = []
    current_category = "Light"

    for line in text.splitlines():
        if "**Light Armor**" in line:
            current_category = "Light"
        elif "**Medium Armor**" in line:
            current_category = "Medium"
        elif "**Heavy Armor**" in line:
            current_category = "Heavy"
        elif "**Shield**" in line:
            current_category = "Shield"

        if line.startswith("| ") and not re.match(r"\|[-\s|]+\|", line) and "Armor" not in line and "Weight" not in line:
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) < 5:
                continue
            name = cols[0].strip()
            if not name or name.startswith("-") or "**" in name:
                continue
            ac_raw = cols[1].strip()
            str_req_raw = cols[2].strip()
            stealth = cols[3].strip()
            weight = cols[4].strip()
            cost = cols[5].strip() if len(cols) > 5 else ""

            # Parse strength requirement
            str_req = None
            str_m = re.search(r"Str\s*(\d+)", str_req_raw)
            if str_m:
                str_req = int(str_m.group(1))

            if current_category == "Shield":
                items.append({
                    "name": "Shield",
                    "item_type": "shield",
                    "category": "Shield",
                    "cost": cost,
                    "weight": weight,
                    "ac_formula": "+2",
                    "strength_req": None,
                    "stealth_disadvantage": False,
                    "source": "PHB 2024",
                })
            else:
                items.append({
                    "name": name,
                    "item_type": "armor",
                    "category": current_category,
                    "cost": cost,
                    "weight": weight,
                    "ac_formula": ac_raw,
                    "strength_req": str_req,
                    "stealth_disadvantage": "Disadvantage" in stealth,
                    "source": "PHB 2024",
                })
    return items


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------

def seed_all(db: Session) -> dict:
    counts = {
        "species": 0, "classes": 0, "subclasses": 0, "backgrounds": 0,
        "feats": 0, "spells": 0, "equipment": 0,
    }

    # Pre-load existing names to avoid duplicate checks failing on unflushed adds
    existing_species = {r.name for r in db.query(Species.name)}
    existing_classes = {r.name for r in db.query(DnDClass.name)}
    existing_backgrounds = {r.name for r in db.query(Background.name)}
    existing_feats = {r.name for r in db.query(Feat.name)}
    existing_spells = {r.name for r in db.query(Spell.name)}
    existing_equip = {r.name for r in db.query(Equipment.name)}

    # Species
    for f in sorted((REF / "species").glob("*.md")):
        if "Zone.Identifier" in f.name:
            continue
        data = _parse_species_file(f)
        if data["name"] not in existing_species:
            db.add(Species(**{k: v for k, v in data.items()}))
            existing_species.add(data["name"])
            counts["species"] += 1

    # Classes
    for f in sorted((REF / "classes").glob("*.md")):
        if "Zone.Identifier" in f.name:
            continue
        data = _parse_class_file(f)
        subclasses_data = data.pop("subclasses", [])
        if data["name"] not in existing_classes:
            cls_obj = DnDClass(**data)
            db.add(cls_obj)
            db.flush()
            for sc in subclasses_data:
                db.add(Subclass(class_id=cls_obj.id, **sc))
                counts["subclasses"] += 1
            existing_classes.add(data["name"])
            counts["classes"] += 1

    # Backgrounds
    for f in sorted((REF / "backgrounds").glob("*.md")):
        if "Zone.Identifier" in f.name:
            continue
        data = _parse_background_file(f)
        if data["name"] not in existing_backgrounds:
            db.add(Background(**data))
            existing_backgrounds.add(data["name"])
            counts["backgrounds"] += 1

    # Feats
    for cat_dir, cat_key in [
        ("origin", "origin"), ("general", "general"),
        ("fighting-style", "fighting_style"), ("epic-boon", "epic_boon"),
    ]:
        feat_dir = REF / "feats" / cat_dir
        if not feat_dir.exists():
            continue
        for f in sorted(feat_dir.glob("*.md")):
            if "Zone.Identifier" in f.name:
                continue
            data = _parse_feat_file(f, cat_key)
            if data["name"] not in existing_feats:
                db.add(Feat(**data))
                existing_feats.add(data["name"])
                counts["feats"] += 1

    # Spells
    for lvl in range(10):
        spell_dir = REF / "spells" / f"level-{lvl}"
        if not spell_dir.exists():
            continue
        for f in sorted(spell_dir.glob("*.md")):
            if "Zone.Identifier" in f.name:
                continue
            data = _parse_spell_file(f, lvl)
            if data["name"] not in existing_spells:
                db.add(Spell(**data))
                existing_spells.add(data["name"])
                counts["spells"] += 1

    # Equipment
    weapons_file = REF / "equipment" / "weapons.md"
    if weapons_file.exists():
        for item in _parse_weapons_file(weapons_file):
            if item["name"] not in existing_equip:
                db.add(Equipment(**item))
                existing_equip.add(item["name"])
                counts["equipment"] += 1

    armor_file = REF / "equipment" / "armor.md"
    if armor_file.exists():
        for item in _parse_armor_file(armor_file):
            if item["name"] not in existing_equip:
                db.add(Equipment(**item))
                existing_equip.add(item["name"])
                counts["equipment"] += 1

    db.commit()
    return counts
