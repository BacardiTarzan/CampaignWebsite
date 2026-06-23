# app/services/class_action_seeder.py
"""
Parse reference_claude/class_actions/{class}.md files and seed CharacterResource
rows when a character is added to combat.

Markdown format (see reference_claude/class_actions/template.md):
  # ClassName
  ## Ability Name
  action_type: action|bonus_action|reaction|special|passive
  resource_key: snake_case_key
  min_level: 1
  max_uses: 2          # integer, 'level', or 'level//2'
  rest_type: short|long|encounter
  description: One line.
"""
import re
import logging
from pathlib import Path
from functools import lru_cache
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)

_CLASS_ACTIONS_DIR = Path(__file__).resolve().parent.parent.parent / "reference_claude" / "class_actions"


def _eval_uses(expr: str, level: int) -> int:
    """Evaluate a max_uses expression. Supports integers, 'level', 'level//2'."""
    expr = expr.strip()
    if expr.isdigit():
        return int(expr)
    if expr == "level":
        return level
    if expr == "level//2":
        return max(1, level // 2)
    try:
        # Controlled substitution — only 'level' variable allowed
        return max(1, int(eval(expr.replace("level", str(level)), {"__builtins__": {}}, {})))
    except Exception:
        log.warning("Could not evaluate max_uses expr %r for level %d — defaulting to 1", expr, level)
        return 1


@lru_cache(maxsize=20)
def _load_class_actions(class_name: str) -> list[dict]:
    """Parse a class_actions markdown file. Result is cached per class name."""
    path = _CLASS_ACTIONS_DIR / f"{class_name.lower()}.md"
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    abilities = []
    # Split on ## headers (ability blocks)
    blocks = re.split(r"\n(?=## )", text)
    for block in blocks:
        if not block.startswith("## "):
            continue
        name_match = re.match(r"## (.+)", block)
        if not name_match:
            continue
        name = name_match.group(1).strip()
        fields = {}
        for key in ("action_type", "resource_key", "min_level", "max_uses", "rest_type", "description"):
            m = re.search(rf"^{key}:\s*(.+)$", block, re.MULTILINE)
            if m:
                fields[key] = m.group(1).strip()

        required = ("action_type", "resource_key", "min_level", "max_uses", "rest_type")
        if not all(k in fields for k in required):
            log.warning("Skipping malformed ability %r in %s", name, path.name)
            continue

        abilities.append({
            "name": name,
            "action_type": fields["action_type"],
            "resource_key": fields["resource_key"],
            "min_level": int(fields["min_level"]),
            "max_uses": fields["max_uses"],
            "rest_type": fields["rest_type"],
            "description": fields.get("description", ""),
        })
    return abilities


def seed_class_abilities(char, db: Session) -> None:
    """
    Seed CharacterResource rows for a character based on their class and level.
    Called when a character is added to combat. Never overwrites existing rows.
    """
    from ..models.character import CharacterResource

    cc = char.character_classes[0] if char.character_classes else None
    if not cc or not cc.dnd_class:
        return

    class_name = cc.dnd_class.name.lower()
    level = cc.level
    abilities = _load_class_actions(class_name)

    added = 0
    for ability in abilities:
        if level < ability["min_level"]:
            continue
        existing = db.query(CharacterResource).filter_by(
            character_id=char.id, resource_key=ability["resource_key"]
        ).first()
        if existing:
            continue  # never overwrite manual DM config

        max_uses = _eval_uses(ability["max_uses"], level)
        db.add(CharacterResource(
            character_id=char.id,
            resource_key=ability["resource_key"],
            label=ability["name"],
            max_uses=max_uses,
            used=0,
            rest_type=ability["rest_type"],
        ))
        added += 1

    if added:
        db.commit()
        log.info("Seeded %d class abilities for character %d (%s Lv%d)", added, char.id, class_name, level)
