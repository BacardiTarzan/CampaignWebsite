"""
Parse reference/ markdown files and seed the database.
Safe to re-run: skips records that already exist by name.
"""
import re
from pathlib import Path
from sqlalchemy.orm import Session

from ..config import settings
from ..models.content import Species, DnDClass, Subclass, Background, Feat, Spell, Equipment, LorePage, GlossaryTerm, Monster

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

def _parse_lineage_table(raw: str) -> list[dict]:
    """Parse a markdown table into a list of lineage option dicts."""
    lines = [l.strip() for l in raw.split("\n") if l.strip().startswith("|")]
    if len(lines) < 3:
        return []

    def parse_row(line: str) -> list[str]:
        return [c.strip() for c in line.strip("|").split("|")]

    # lines[0] = header, lines[1] = separator, lines[2:] = data
    result = []
    for row_line in lines[2:]:
        cols = parse_row(row_line)
        if not cols or not cols[0]:
            continue
        entry: dict = {"name": cols[0]}
        if len(cols) >= 4:
            entry["description"] = cols[1]
            entry["level3_spell"] = cols[2]
            entry["level5_spell"] = cols[3]
        elif len(cols) >= 2:
            entry["description"] = cols[1]
        # Extract speed override from description e.g. "Speed increases to 35 ft."
        if "description" in entry:
            sm = re.search(r'[Ss]peed\s+(?:increases?\s+to|is)\s+(\d+)', entry["description"])
            if sm:
                entry["speed"] = int(sm.group(1))
        result.append(entry)
    return result


def _parse_lineage_bullets(raw: str) -> list[dict]:
    """Parse a bullet list of bold-named options into lineage dicts.
    Handles both '- **Name:** desc' and '- **Name** — desc' formats.
    """
    result = []
    # Match: - **Name:** desc  OR  - **Name:optional** [separator] desc
    pattern = r"-\s+\*\*([^*]+?):?\*\*\s*[:\-—]?\s*(.+?)(?=\n-\s+\*\*|\Z)"
    for m in re.finditer(pattern, raw, re.DOTALL):
        name = m.group(1).strip().rstrip(":")
        desc = re.sub(r"\s+", " ", m.group(2)).strip()
        if name and desc:
            result.append({"name": name, "description": desc})
    return result


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

    # Check for a standalone lineage section (e.g. Dragonborn's ### Draconic Ancestry table)
    lineages: list[dict] = []
    standalone_section = re.search(r"### Draconic Ancestry\n+(.*?)(?=\n###|\Z)", text, re.DOTALL)
    if standalone_section:
        lineages = _parse_lineage_table(standalone_section.group(1))

    # Parse traits; also extract lineages from choice traits if not already found
    traits = []
    traits_section = re.search(r"### Traits\n+(.*?)(?=\n###|\Z)", text, re.DOTALL)
    if traits_section:
        for block in re.split(r"\n\n(?=\*\*)", traits_section.group(1)):
            m = re.match(r"\*\*([^*]+?):\*\*\s*(.*)", block, re.DOTALL)
            if m:
                tname = m.group(1).strip()
                tdesc_raw = m.group(2)
                # Extract unlock level from names like "Celestial Revelation (Level 3)"
                tlevel = 1
                lm = re.match(r"^(.*?)\s*\(Level\s*(\d+)\)\s*$", tname, re.IGNORECASE)
                if lm:
                    tname = lm.group(1).strip()
                    tlevel = int(lm.group(2))
                # Detect "Proficiency in X, Y, or Z (choose one)" skill-choice traits
                trait_choice_required = False
                trait_choice_key = None
                trait_options: list[str] = []
                skill_pick_m = re.search(r'Proficiency in (.+?)\s*\(choose one\)', tdesc_raw, re.IGNORECASE)
                if skill_pick_m:
                    raw_opts = skill_pick_m.group(1)
                    trait_options = [s.strip() for s in re.split(r',\s*|\s+or\s+', raw_opts) if s.strip()]
                    if trait_options:
                        trait_choice_required = True
                        trait_choice_key = "species_skill"
                traits.append({
                    "name": tname,
                    "description": re.sub(r"\s+", " ", tdesc_raw).strip(),
                    "level": tlevel,
                    "choice_required": trait_choice_required,
                    "choice_key": trait_choice_key,
                    "options": trait_options,
                })

                # Parse lineages from traits named with choice keywords
                if not lineages and any(kw in tname.lower() for kw in ("lineage", "legacy", "ancestry")):
                    parsed = _parse_lineage_table(tdesc_raw)
                    if not parsed:
                        parsed = _parse_lineage_bullets(tdesc_raw)
                    lineages = parsed

    return {
        "name": name,
        "creature_type": creature_type,
        "size_options": sizes,
        "speed": speed,
        "traits": traits,
        "lineages": lineages,
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

    # Skill choices — handles "**Skill Proficiencies (choose N):** list" and "**Skill Proficiencies:** Choose any N"
    skill_choices = 2
    skill_options = []
    skill_m = re.search(r"\*\*Skill Proficiencies[^*]*?\(choose\s+(\d+)\)[^*]*:\*\*\s*(.+)", text)
    if skill_m:
        skill_choices = int(skill_m.group(1))
        skill_options = _split_list(skill_m.group(2).strip())
    else:
        skill_m2 = re.search(r"\*\*Skill Proficiencies:\*\*\s*Choose any\s+(\d+)", text, re.IGNORECASE)
        if skill_m2:
            skill_choices = int(skill_m2.group(1))
            skill_options = []  # "any" means no restricted list

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

    # Tool proficiencies
    tool_raw = _field(text, "Tool Proficiencies") or ""
    tool_proficiencies = [t.strip() for t in tool_raw.split(",") if t.strip()] if tool_raw else []

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
            elif "weapon mastery" in feat_name.lower() and slug in ("fighter", "barbarian", "paladin", "ranger", "rogue"):
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
        "tool_proficiencies": tool_proficiencies or None,
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
    sc_blocks = re.split(r"\n*#### (.+)", sc_text)
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
# Equipment — per-item markdown database
# ---------------------------------------------------------------------------

def _normalize_ac_formula(raw: str) -> str:
    """Convert markdown AC text to the format _calc_ac() expects."""
    raw = raw.strip()
    # Heavy armor: pure number
    if re.fullmatch(r"\d+", raw):
        return raw
    # Shield bonus
    if raw == "+2":
        return "+2"
    # "X + Dexterity modifier (max +N)" or "X + Dex modifier (max +N)"
    m = re.match(r"(\d+)\s*\+\s*Dex(?:terity)?\s+modifier(?:\s*\(max\s*\+?(\d+)\))?", raw, re.IGNORECASE)
    if m:
        base = m.group(1)
        cap = m.group(2)
        return f"{base} + Dex (max {cap})" if cap else f"{base} + Dex"
    return raw


def _parse_equip_item_md(path: Path) -> dict | None:
    """Parse a single per-item markdown file into an Equipment dict."""
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()

    # Name from H1
    name = None
    for line in lines:
        if line.startswith("# "):
            name = line[2:].strip()
            break
    if not name:
        return None

    def field(key: str) -> str | None:
        m = re.search(rf"\*\*{re.escape(key)}[:\*]*\s*\*\*\s*(.+)", text)
        return m.group(1).strip() if m else None

    # Determine item_type and category from directory structure
    parts = path.parts
    # Find 'equipment-database' in parts
    try:
        idx = parts.index("equipment-database")
    except ValueError:
        return None
    sub = parts[idx + 1] if len(parts) > idx + 1 else ""
    sub2 = parts[idx + 2] if len(parts) > idx + 2 else ""

    # Description block
    desc_m = re.search(r"## Description\s*\n(.*?)(?:\n## |\Z)", text, re.DOTALL)
    description = desc_m.group(1).strip() if desc_m else None

    cost = field("Cost")
    weight = field("Weight")

    if sub == "weapons":
        cat_map = {
            "simple-melee": "Simple Melee",
            "simple-ranged": "Simple Ranged",
            "martial-melee": "Martial Melee",
            "martial-ranged": "Martial Ranged",
        }
        category = cat_map.get(sub2, sub2.replace("-", " ").title())

        damage_raw = field("Damage") or ""
        dmg_m = re.match(r"(.+?)\s+(Slashing|Piercing|Bludgeoning|Force|Radiant)", damage_raw, re.IGNORECASE)
        damage = dmg_m.group(1).strip() if dmg_m else damage_raw.split()[0] if damage_raw else None
        damage_type = dmg_m.group(2).capitalize() if dmg_m else None

        props_block = re.search(r"## Properties\s*\n(.*?)(?:\n## |\Z)", text, re.DOTALL)
        properties = []
        if props_block:
            for ln in props_block.group(1).splitlines():
                p = ln.strip().lstrip("- ").strip()
                if p and p.lower() != "none":
                    properties.append(p)

        mastery_m = re.search(r"## Mastery\s*\n-\s*(.+)", text)
        mastery = mastery_m.group(1).strip() if mastery_m else None

        damage_rolls = [{"dice": damage, "type": damage_type or ""}] if damage else None
        return {
            "name": name,
            "item_type": "weapon",
            "category": category,
            "cost": cost,
            "weight": weight,
            "damage": damage,
            "damage_type": damage_type,
            "damage_rolls": damage_rolls,
            "properties": properties,
            "mastery_property": mastery,
            "description": description,
            "source": "PHB 2024",
        }

    elif sub == "armor":
        if sub2 == "shields":
            return {
                "name": name,
                "item_type": "shield",
                "category": "Shield",
                "cost": cost,
                "weight": weight,
                "ac_formula": "+2",
                "strength_req": None,
                "stealth_disadvantage": False,
                "description": description,
                "source": "PHB 2024",
            }
        cat_map = {"light": "Light", "medium": "Medium", "heavy": "Heavy"}
        category = cat_map.get(sub2, sub2.title())

        ac_raw = field("Armor Class (AC)") or ""
        ac_formula = _normalize_ac_formula(ac_raw)

        str_req_raw = field("Strength Requirement") or ""
        str_m = re.search(r"(\d+)", str_req_raw)
        str_req = int(str_m.group(1)) if str_m else None

        props_block = re.search(r"## Properties\s*\n(.*?)(?:\n## |\Z)", text, re.DOTALL)
        stealth_dis = False
        if props_block:
            for ln in props_block.group(1).splitlines():
                if "stealth" in ln.lower() or "disadvantage" in ln.lower():
                    stealth_dis = True

        return {
            "name": name,
            "item_type": "armor",
            "category": category,
            "cost": cost,
            "weight": weight,
            "ac_formula": ac_formula,
            "strength_req": str_req,
            "stealth_disadvantage": stealth_dis,
            "description": description,
            "source": "PHB 2024",
        }

    elif sub == "adventuring-gear":
        return {
            "name": name,
            "item_type": "gear",
            "category": "Gear",
            "cost": cost,
            "weight": weight,
            "description": description,
            "source": "PHB 2024",
        }

    elif sub == "tools":
        cat_map = {"artisan": "Artisan's Tools", "other": "Tools"}
        category = cat_map.get(sub2, "Tools")
        return {
            "name": name,
            "item_type": "tool",
            "category": category,
            "cost": cost,
            "weight": weight,
            "description": description,
            "source": "PHB 2024",
        }

    # Skip mounts and unknown
    return None


def _parse_equipment_database(db_dir: Path) -> list[dict]:
    items = []
    for md_file in sorted(db_dir.rglob("*.md")):
        if "Zone.Identifier" in md_file.name:
            continue
        item = _parse_equip_item_md(md_file)
        if item:
            items.append(item)
    return items


# Equipment (weapons + armor from tables) — legacy parsers kept for fallback
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
# Monster parser
# ---------------------------------------------------------------------------

def _parse_stat_table(text: str) -> dict:
    """Extract key-value pairs from the '## Stat Block' two-column table."""
    result = {}
    for m in re.finditer(r"\|\s*\*\*([^*]+?)\*\*\s*\|\s*([^|\n]+?)\s*\|", text):
        key = m.group(1).strip().rstrip(":")
        val = m.group(2).strip()
        result[key] = val
    return result


def _parse_ability_row(text: str) -> dict[str, int]:
    """Extract ability scores from the two-row ability table."""
    scores = {}
    headers = re.findall(r"\*\*(STR|DEX|CON|INT|WIS|CHA)\*\*", text)
    values_m = re.search(
        r"\|\s*(\d+)[^|]*\|\s*(\d+)[^|]*\|\s*(\d+)[^|]*\|\s*(\d+)[^|]*\|\s*(\d+)[^|]*\|\s*(\d+)[^|]*\|",
        text
    )
    if headers and values_m:
        for i, h in enumerate(headers[:6]):
            try:
                scores[h.lower()] = int(values_m.group(i + 1))
            except (ValueError, IndexError):
                pass
    return scores


def _parse_ability_sections(text: str) -> list[dict]:
    """Parse ### section (Traits/Actions/etc.) into [{name, description}] list."""
    items = []
    for block in re.split(r"\n(?=\*\*[A-Z])", text):
        m = re.match(r"\*\*([^.*]+?)[\.\*]?\*\*[.\s]*(.*)", block.strip(), re.DOTALL)
        if m:
            desc = re.sub(r"\s+", " ", m.group(2)).strip()
            # Strip trailing separator and control characters
            desc = re.sub(r"\s*---\s*$", "", desc).strip()
            desc = re.sub(r"[\x00-\x08\x0b-\x1f\x7f]", "", desc)
            items.append({
                "name": m.group(1).strip(),
                "description": desc,
            })
    return items


def _parse_monster_file(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    name_m = re.match(r"#\s+(.+)", text)
    if not name_m:
        return None
    name = name_m.group(1).strip()

    # Stat block table
    stat = _parse_stat_table(text)

    # Size / Type — "Large Elemental"
    size_type = stat.get("Size / Type", "")
    parts = size_type.split(None, 1)
    size = parts[0] if parts else None
    creature_type = parts[1] if len(parts) > 1 else None

    # AC
    ac_m = re.search(r"^(\d+)", stat.get("AC", ""))
    ac = int(ac_m.group(1)) if ac_m else None

    # HP
    hp_str = stat.get("HP", "")
    hp_m = re.match(r"(\d+)\s*(?:\((.+?)\))?", hp_str)
    hp_max = int(hp_m.group(1)) if hp_m else None
    hp_formula = hp_m.group(2) if hp_m and hp_m.group(2) else None

    # CR / XP / PB
    cr_str = stat.get("CR", "")
    cr_m = re.match(r"CR\s*([\d/]+)", cr_str)
    cr = cr_m.group(1) if cr_m else None
    xp_m = re.search(r"XP\s*([\d,]+)", cr_str)
    xp = int(xp_m.group(1).replace(",", "")) if xp_m else None
    pb_m = re.search(r"PB\s*\+(\d+)", cr_str)
    pb = int(pb_m.group(1)) if pb_m else None

    # Ability scores
    abilities = _parse_ability_row(text)

    # Additional stats
    add = _parse_stat_table(text)

    def _section(header: str) -> str:
        m = re.search(rf"##\s+{re.escape(header)}\s*\n(.*?)(?=\n##\s|\Z)", text, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    return {
        "name": name,
        "size": size,
        "creature_type": creature_type,
        "alignment": stat.get("Alignment"),
        "ac": ac,
        "initiative": stat.get("Initiative"),
        "hp_max": hp_max,
        "hp_formula": hp_formula,
        "speed": stat.get("Speed"),
        "cr": cr,
        "xp": xp,
        "proficiency_bonus": pb,
        "str_": abilities.get("str"),
        "dex_": abilities.get("dex"),
        "con_": abilities.get("con"),
        "int_": abilities.get("int"),
        "wis_": abilities.get("wis"),
        "cha_": abilities.get("cha"),
        "saving_throws": add.get("Saving Throws"),
        "skills": add.get("Skills"),
        "resistances": add.get("Resistances"),
        "immunities": add.get("Immunities"),
        "vulnerabilities": add.get("Vulnerabilities"),
        "senses": add.get("Senses"),
        "languages": add.get("Languages"),
        "gear": add.get("Gear"),
        "traits": _parse_ability_sections(_section("Traits")) or None,
        "actions": _parse_ability_sections(_section("Actions")) or None,
        "bonus_actions": _parse_ability_sections(_section("Bonus Actions")) or None,
        "reactions": _parse_ability_sections(_section("Reactions")) or None,
        "legendary_actions": _parse_ability_sections(_section("Legendary Actions")) or None,
        "source": "MM 2024",
        "is_homebrew": False,
    }


# ---------------------------------------------------------------------------
# Main seed function
# ---------------------------------------------------------------------------

def seed_all(db: Session) -> dict:
    counts = {
        "species": 0, "classes": 0, "subclasses": 0, "backgrounds": 0,
        "feats": 0, "spells": 0, "equipment": 0, "glossary": 0, "monsters": 0,
    }

    # Pre-load existing names to avoid duplicate checks failing on unflushed adds
    existing_species = {r.name for r in db.query(Species.name)}
    existing_classes = {r.name for r in db.query(DnDClass.name)}  # kept for reference below
    existing_backgrounds = {r.name for r in db.query(Background.name)}
    existing_feats = {r.name for r in db.query(Feat.name)}
    existing_spells = {r.name for r in db.query(Spell.name)}

    # Species
    for f in sorted((REF / "species").glob("*.md")):
        if "Zone.Identifier" in f.name:
            continue
        data = _parse_species_file(f)
        if data["name"] not in existing_species:
            db.add(Species(**{k: v for k, v in data.items()}))
            existing_species.add(data["name"])
            counts["species"] += 1
        else:
            # Update lineages on existing records (added in later migration)
            sp = db.query(Species).filter_by(name=data["name"]).first()
            if sp and sp.lineages is None and data.get("lineages"):
                sp.lineages = data["lineages"]

    # Classes — insert new, refresh tool_proficiencies on existing
    existing_class_rows = {r.name: r for r in db.query(DnDClass)}
    for f in sorted((REF / "classes").glob("*.md")):
        if "Zone.Identifier" in f.name:
            continue
        data = _parse_class_file(f)
        subclasses_data = data.pop("subclasses", [])
        if data["name"] not in existing_class_rows:
            cls_obj = DnDClass(**data)
            db.add(cls_obj)
            db.flush()
            for sc in subclasses_data:
                db.add(Subclass(class_id=cls_obj.id, **sc))
                counts["subclasses"] += 1
            existing_class_rows[data["name"]] = cls_obj
            counts["classes"] += 1
        else:
            # Refresh mutable columns on existing rows
            cls_obj = existing_class_rows[data["name"]]
            cls_obj.tool_proficiencies = data.get("tool_proficiencies")
            cls_obj.features = data.get("features")
            # Upsert subclasses — insert any that don't exist yet
            existing_sc_names = {
                sc.name for sc in db.query(Subclass).filter(Subclass.class_id == cls_obj.id)
            }
            for sc in subclasses_data:
                if sc["name"] not in existing_sc_names:
                    db.add(Subclass(class_id=cls_obj.id, **sc))
                    counts["subclasses"] += 1

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

    # Spells — insert new rows; also refresh description+metadata if currently empty
    existing_spell_rows = {r.name: r for r in db.query(Spell)}
    for lvl in range(10):
        spell_dir = REF / "spells" / f"level-{lvl}"
        if not spell_dir.exists():
            continue
        for f in sorted(spell_dir.glob("*.md")):
            if "Zone.Identifier" in f.name:
                continue
            data = _parse_spell_file(f, lvl)
            if data["name"] not in existing_spell_rows:
                db.add(Spell(**data))
                existing_spell_rows[data["name"]] = None
                counts["spells"] += 1
            else:
                row = existing_spell_rows[data["name"]]
                if row and not (row.description and row.casting_time and row.spell_range and row.duration):
                    for k, v in data.items():
                        setattr(row, k, v)
                    counts["spells"] += 1

    # Equipment — per-item markdown database (upsert: insert new, update existing)
    equip_db_dir = REF / "equipment" / "equipment-database"
    existing_equip_rows = {r.name: r for r in db.query(Equipment)}
    if equip_db_dir.exists():
        for item in _parse_equipment_database(equip_db_dir):
            row = existing_equip_rows.get(item["name"])
            if row is None:
                db.add(Equipment(**item))
                existing_equip_rows[item["name"]] = None
                counts["equipment"] += 1
            else:
                # Update all fields from the authoritative per-item file
                for k, v in item.items():
                    setattr(row, k, v)
                counts["equipment"] += 1
    else:
        # Fallback to legacy table parsers if per-item dir doesn't exist
        weapons_file = REF / "equipment" / "weapons.md"
        if weapons_file.exists():
            for item in _parse_weapons_file(weapons_file):
                if item["name"] not in existing_equip_rows:
                    db.add(Equipment(**item))
                    existing_equip_rows[item["name"]] = None
                    counts["equipment"] += 1

        armor_file = REF / "equipment" / "armor.md"
        if armor_file.exists():
            for item in _parse_armor_file(armor_file):
                if item["name"] not in existing_equip_rows:
                    db.add(Equipment(**item))
                    existing_equip_rows[item["name"]] = None
                    counts["equipment"] += 1

    # Gear items not covered by per-item files
    for item in _gear_items():
        if item["name"] not in existing_equip_rows:
            db.add(Equipment(**item))
            existing_equip_rows[item["name"]] = None
            counts["equipment"] += 1

    # Monsters
    monster_dir = REF / "Monsters"
    if monster_dir.exists():
        existing_monsters = {r.name for r in db.query(Monster.name)}
        for f in sorted(monster_dir.glob("*.md")):
            if "Zone.Identifier" in f.name:
                continue
            data = _parse_monster_file(f)
            if not data:
                continue
            if data["name"] not in existing_monsters:
                db.add(Monster(**data))
                existing_monsters.add(data["name"])
                counts["monsters"] += 1
            else:
                # Refresh all fields on existing rows (idempotent update)
                row = db.query(Monster).filter_by(name=data["name"]).first()
                if row:
                    for k, v in data.items():
                        setattr(row, k, v)

    db.commit()

    # Lore pages
    counts["lore"] = _seed_lore(db)
    db.commit()

    # Glossary terms
    counts["glossary"] = _seed_glossary(db)

    return counts


def _seed_lore(db: Session) -> int:
    lore_dir = REF / "Lore"
    if not lore_dir.exists():
        return 0

    existing = {r.slug: r for r in db.query(LorePage).all()}
    added = 0

    for f in sorted(lore_dir.glob("*.md")):
        if "Zone.Identifier" in f.name:
            continue
        slug = f.stem.lower().replace("_", "-")
        raw = f.read_text(encoding="utf-8", errors="replace")

        title = slug
        for line in raw.splitlines():
            if line.startswith("# "):
                title = line[2:].strip()
                break

        stem = f.stem
        if stem.lower().startswith("species-"):
            category = "species"
        elif stem.lower().startswith("campaign-"):
            category = "campaign"
        else:
            category = "world"

        if slug not in existing:
            db.add(LorePage(slug=slug, title=title, content_md=raw,
                            player_visible=False, category=category))
            added += 1
        else:
            # Update content/title/category on re-seed; preserve player_visible
            page = existing[slug]
            page.title = title
            page.content_md = raw
            page.category = category

    return added


def _short_desc(text: str, max_len: int = 220) -> str:
    """First sentence of text, stripped of **bold** markers, capped at max_len."""
    clean = re.sub(r'\*\*([^*]+)\*\*', r'\1', text).strip()
    # Take up to first period that ends a sentence
    m = re.search(r'^(.{20,}?\.)\s', clean)
    if m and len(m.group(1)) <= max_len:
        return m.group(1)
    return clean[:max_len].rsplit(" ", 1)[0] if len(clean) > max_len else clean


# Glossary terms to pull from glossary.md (UPPERCASE heading → slug, category)
_GLOSSARY_WANTED = {
    "ADVANTAGE": "combat", "DISADVANTAGE": "combat",
    "BONUS ACTION": "combat", "REACTION": "combat",
    "CONCENTRATION": "combat", "RITUAL": "combat",
    "SAVING THROW": "combat", "CRITICAL HIT": "combat",
    "OPPORTUNITY ATTACKS": "combat", "PROFICIENCY": "combat",
    "EXPERTISE": "combat", "CANTRIP": "combat",
    "UNARMED STRIKE": "combat", "D20 TEST": "combat",
    "RESISTANCE": "combat", "VULNERABILITY": "combat",
    "IMMUNITY": "combat", "TEMPORARY HIT POINTS": "combat",
    "SPEED": "combat", "HIT POINTS": "combat", "HIT POINT DICE": "combat",
    "LONG REST": "combat", "SHORT REST": "combat",
    "HEROIC INSPIRATION": "combat", "DEATH SAVING THROW": "combat",
    "ABILITY CHECK": "combat", "ARMOR CLASS": "combat",
    "ATTACK ROLL": "combat", "DIFFICULT TERRAIN": "combat",
    "SPELL ATTACK": "combat", "DAMAGE TYPES": "combat",
    # Conditions all included via Tag: Condition detection
}


def _parse_glossary_terms(path: Path) -> list[dict]:
    text = path.read_text(encoding="utf-8")
    items = []
    # Split by ### HEADING entries
    parts = re.split(r'\n### ', text)
    for part in parts[1:]:  # skip preamble
        lines = part.strip().splitlines()
        if not lines:
            continue
        heading = lines[0].strip()
        body_lines = lines[1:]
        # Strip tag line and determine category
        tag_m = re.search(r'\*\*Tag:\*\*\s*(\w[\w ]*)', part)
        tag = tag_m.group(1).strip() if tag_m else ""

        if tag == "Condition":
            category = "condition"
        elif tag == "Action":
            category = "action"
        elif heading in _GLOSSARY_WANTED:
            category = _GLOSSARY_WANTED[heading]
        else:
            continue  # skip unwanted entries

        # Build full description (skip tag line, strip leading ---)
        body = "\n".join(l for l in body_lines
                         if not re.match(r'^\*\*Tag:\*\*', l) and l.strip() != "---").strip()
        if not body:
            body = heading.title()

        term = heading.title()
        # Fix casing for well-known terms
        _CASING = {
            "D20 Test": "D20 Test", "Hit Points": "Hit Points",
            "Hit Point Dice": "Hit Point Dice", "Long Rest": "Long Rest",
            "Short Rest": "Short Rest", "Armor Class": "Armor Class",
            "Unarmed Strike": "Unarmed Strike", "Heroic Inspiration": "Heroic Inspiration",
            "Death Saving Throw": "Death Saving Throw", "Bonus Action": "Bonus Action",
        }
        term = _CASING.get(heading.title(), heading.title())
        slug = heading.lower().replace(" ", "-")

        items.append({
            "slug": slug,
            "term": term,
            "category": category,
            "short_description": _short_desc(body),
            "full_description": body,
            "ability": None,
        })
    return items


def _seed_glossary(db: Session) -> int:
    existing = {r.slug: r for r in db.query(GlossaryTerm).all()}
    terms: list[dict] = []

    # 1. Weapon properties
    wp_path = REF / "rules" / "weapon-properties.md"
    if wp_path.exists():
        for m in re.finditer(r'\*\*([^.]+)\.\*\*\s+(.+)', wp_path.read_text(encoding="utf-8")):
            name = m.group(1).strip()
            desc = m.group(2).strip()
            terms.append({
                "slug": name.lower().replace(" ", "-"),
                "term": name,
                "category": "weapon_property",
                "short_description": _short_desc(desc),
                "full_description": desc,
                "ability": None,
            })

    # 2. Mastery properties
    mp_path = REF / "rules" / "mastery-properties.md"
    if mp_path.exists():
        for m in re.finditer(r'\*\*([^.]+)\.\*\*\s+(.+)', mp_path.read_text(encoding="utf-8")):
            name = m.group(1).strip()
            desc = m.group(2).strip()
            terms.append({
                "slug": name.lower().replace(" ", "-"),
                "term": name,
                "category": "mastery",
                "short_description": _short_desc(desc),
                "full_description": desc,
                "ability": None,
            })

    # 3. Skills
    skills_path = REF / "rules" / "skills.md"
    if skills_path.exists():
        for line in skills_path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("| ") or "---" in line or "Skill" in line:
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 3 and cols[0]:
                skill, ability, example = cols[0], cols[1], cols[2]
                desc = f"{skill} ({ability}): {example}"
                terms.append({
                    "slug": skill.lower().replace(" ", "-"),
                    "term": skill,
                    "category": "skill",
                    "short_description": desc,
                    "full_description": desc,
                    "ability": ability,
                })

    # 4. Actions (short summaries from actions.md)
    actions_path = REF / "rules" / "actions.md"
    if actions_path.exists():
        for line in actions_path.read_text(encoding="utf-8").splitlines():
            if not line.startswith("| ") or "---" in line or "Action" in line:
                continue
            cols = [c.strip() for c in line.strip("|").split("|")]
            if len(cols) >= 2 and cols[0]:
                action, summary = cols[0], cols[1]
                terms.append({
                    "slug": action.lower().replace(" ", "-"),
                    "term": action,
                    "category": "action",
                    "short_description": summary,
                    "full_description": summary,
                    "ability": None,
                })

    # 5. Selected glossary entries (conditions + combat terms)
    glossary_path = REF / "rules" / "glossary.md"
    if glossary_path.exists():
        terms.extend(_parse_glossary_terms(glossary_path))

    # 6. Wild Heart ritual spell glossary entries (Beast Sense, Speak with Animals, Commune with Nature)
    # These are referenced by name in the Wild Heart Barbarian feature description and need tooltip coverage.
    terms.extend([
        {
            "slug": "beast-sense",
            "term": "Beast Sense",
            "category": "spell",
            "short_description": "Ritual. Perceive through a willing Beast's senses (sight, hearing, special senses) for up to 1 hour (Concentration).",
            "full_description": (
                "Level 2 Divination · Casting Time: Action or Ritual · Range: Touch · Duration: Concentration, up to 1 hour\n\n"
                "You touch a willing Beast. For the duration, you can perceive through the Beast's senses as well as your own. "
                "When perceiving through the Beast's senses, you benefit from any special senses it has."
            ),
            "ability": None,
        },
        {
            "slug": "speak-with-animals",
            "term": "Speak with Animals",
            "category": "spell",
            "short_description": "Ritual. Comprehend and verbally communicate with Beasts for 10 minutes. Beasts can share info about nearby locations and creatures.",
            "full_description": (
                "Level 1 Divination · Casting Time: Action or Ritual · Range: Self · Duration: 10 minutes\n\n"
                "For the duration, you can comprehend and verbally communicate with Beasts, and you can use any of the Influence action's skill options with them. "
                "Most Beasts have little to say about topics that don't pertain to survival or companionship, but at minimum, a Beast can give you information "
                "about nearby locations and monsters, including whatever it has perceived within the past day."
            ),
            "ability": None,
        },
        {
            "slug": "commune-with-nature",
            "term": "Commune with Nature",
            "category": "spell",
            "short_description": "Ritual. Learn 3 facts about the natural area within 3 miles (outdoors) or 300 ft (underground): settlements, portals, creatures, plants, or water.",
            "full_description": (
                "Level 5 Divination · Casting Time: 1 minute or Ritual · Range: Self · Duration: Instantaneous\n\n"
                "You commune with nature spirits and gain knowledge of the surrounding area. In the outdoors, the spell gives you knowledge of the area within 3 miles. "
                "In caves and other natural underground settings, the radius is limited to 300 feet. The spell doesn't function where nature has been replaced by construction.\n\n"
                "Choose three of the following facts; you learn those facts as they pertain to the spell's area: locations of settlements; locations of portals to other planes; "
                "location of one CR 10+ Celestial, Elemental, Fey, Fiend, or Undead; the most prevalent kind of plant, mineral, or Beast; locations of bodies of water."
            ),
            "ability": None,
        },
    ])

    # Upsert by slug
    added = 0
    seen_slugs: set[str] = set()
    for item in terms:
        slug = item["slug"]
        if slug in seen_slugs:
            continue
        seen_slugs.add(slug)
        row = existing.get(slug)
        if row is None:
            db.add(GlossaryTerm(**item, source="PHB 2024"))
            added += 1
        else:
            for k, v in item.items():
                setattr(row, k, v)
            added += 1
    db.commit()
    return added


def _gear_items() -> list[dict]:
    def g(name, item_type, category, cost, description=None):
        return {"name": name, "item_type": item_type, "category": category,
                "cost": cost, "description": description, "source": "PHB 2024"}

    return [
        # Ammunition
        g("Arrows (20)",    "ammunition", "Ammunition", "1 GP"),
        g("Bolts (20)",     "ammunition", "Ammunition", "1 GP"),
        g("Sling Bullets (20)", "ammunition", "Ammunition", "4 CP"),
        g("Needles (50)",   "ammunition", "Ammunition", "1 GP"),
        # Arcane focuses
        g("Arcane Focus: Crystal",  "focus", "Arcane Focus", "10 GP"),
        g("Arcane Focus: Orb",      "focus", "Arcane Focus", "20 GP"),
        g("Arcane Focus: Rod",      "focus", "Arcane Focus", "10 GP"),
        g("Arcane Focus: Staff",    "focus", "Arcane Focus", "5 GP"),
        g("Arcane Focus: Wand",     "focus", "Arcane Focus", "10 GP"),
        # Druidic focuses
        g("Druidic Focus: Mistletoe",    "focus", "Druidic Focus", "1 GP"),
        g("Druidic Focus: Wooden Staff", "focus", "Druidic Focus", "5 GP"),
        g("Druidic Focus: Yew Wand",     "focus", "Druidic Focus", "10 GP"),
        # Holy symbols
        g("Holy Symbol: Amulet",   "focus", "Holy Symbol", "5 GP"),
        g("Holy Symbol: Emblem",   "focus", "Holy Symbol", "5 GP"),
        g("Holy Symbol: Reliquary","focus", "Holy Symbol", "5 GP"),
        # Adventuring packs
        g("Burglar's Pack",    "pack", "Pack", "16 GP", "Backpack, Ball Bearings, Bell, 10 Candles, Crowbar, Hooded Lantern, 7 Oil flasks, 5 Rations, Rope, Tinderbox, Waterskin"),
        g("Diplomat's Pack",   "pack", "Pack", "39 GP", "Chest, Fine Clothes, Ink, Ink Pen, Lamp, 2 Oil flasks, Paper (5 sheets), Perfume, Sealing Wax, Soap"),
        g("Dungeoneer's Pack", "pack", "Pack", "12 GP", "Backpack, Caltrops, Crowbar, 2 Flasks of Oil, 10 Pitons, Rope, Tinderbox, 10 Torches, 5 Rations, Waterskin"),
        g("Entertainer's Pack","pack", "Pack", "40 GP", "Backpack, Bedroll, Costume (2), Candle (5), Rations (5), Waterskin, Disguise Kit"),
        g("Explorer's Pack",   "pack", "Pack", "10 GP", "Backpack, Bedroll, 2 Torches, Tinderbox, 10 Rations, Waterskin, Rope"),
        g("Priest's Pack",     "pack", "Pack", "33 GP", "Backpack, Blanket, Candle (10), Tinderbox, Alms Box, Incense (2 blocks), Censer, Vestments, Rations (2), Waterskin"),
        g("Scholar's Pack",    "pack", "Pack", "40 GP", "Backpack, Book, Ink, Ink Pen, Parchment (10 sheets), Bag of Sand, Small Knife"),
        # Key gear
        g("Backpack",         "gear", "Gear", "2 GP",   "Holds up to 30 lb."),
        g("Bedroll",          "gear", "Gear", "1 GP"),
        g("Blanket",          "gear", "Gear", "5 SP"),
        g("Candle",           "gear", "Gear", "1 CP"),
        g("Chain (10 ft.)",   "gear", "Gear", "5 GP"),
        g("Climber's Kit",    "gear", "Gear", "25 GP"),
        g("Clothes, Fine",    "gear", "Gear", "15 GP"),
        g("Clothes, Traveler's","gear","Gear","2 GP"),
        g("Component Pouch",  "gear", "Gear", "25 GP",  "Holds material components for spells."),
        g("Crowbar",          "gear", "Gear", "2 GP"),
        g("Grappling Hook",   "gear", "Gear", "2 GP"),
        g("Healer's Kit",     "gear", "Gear", "5 GP",   "10 uses; stabilize a creature at 0 HP."),
        g("Holy Water",       "gear", "Gear", "25 GP"),
        g("Lamp",             "gear", "Gear", "5 SP"),
        g("Lantern, Hooded",  "gear", "Gear", "5 GP"),
        g("Lock",             "gear", "Gear", "10 GP"),
        g("Manacles",         "gear", "Gear", "2 GP"),
        g("Mirror",           "gear", "Gear", "5 GP"),
        g("Oil (flask)",      "gear", "Gear", "1 SP"),
        g("Potion of Healing","gear", "Gear", "50 GP",  "Regain 2d4+2 HP."),
        g("Pouch",            "gear", "Gear", "5 SP"),
        g("Quiver",           "gear", "Gear", "1 GP"),
        g("Rations (1 day)",  "gear", "Gear", "5 SP"),
        g("Rope (50 ft.)",    "gear", "Gear", "1 GP"),
        g("Tent (2-person)",  "gear", "Gear", "2 GP"),
        g("Thieves' Tools",   "gear", "Gear", "25 GP",  "Required for lockpicking and trap disarming."),
        g("Tinderbox",        "gear", "Gear", "5 SP"),
        g("Torch",            "gear", "Gear", "1 CP",   "Bright light 20 ft., dim 40 ft., for 1 hour."),
        g("Waterskin",        "gear", "Gear", "2 SP"),
    ]
