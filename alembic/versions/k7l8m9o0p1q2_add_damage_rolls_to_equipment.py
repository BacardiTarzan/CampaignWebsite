"""replace bonus_damage fields with damage_rolls JSON array on equipment

Revision ID: k7l8m9o0p1q2
Revises: j6k7l8m9o0p1
Create Date: 2026-05-26
"""
import json as _json
from alembic import op
from sqlalchemy import text, inspect as sa_inspect

revision = 'k7l8m9o0p1q2'
down_revision = 'j6k7l8m9o0p1'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    # Add damage_rolls column
    if dialect == "postgresql":
        op.execute(text("ALTER TABLE equipment ADD COLUMN IF NOT EXISTS damage_rolls JSON"))
    else:
        existing = {c["name"] for c in sa_inspect(bind).get_columns("equipment")}
        if "damage_rolls" not in existing:
            op.execute(text("ALTER TABLE equipment ADD COLUMN damage_rolls JSON"))

    # Backfill: build damage_rolls from legacy damage/damage_type (and bonus_damage if set)
    rows = bind.execute(text(
        "SELECT id, damage, damage_type, bonus_damage, bonus_damage_type FROM equipment WHERE damage IS NOT NULL"
    )).fetchall()
    for row in rows:
        rolls = [{"dice": row[1], "type": row[2] or ""}]
        if row[3]:  # bonus_damage
            rolls.append({"dice": row[3], "type": row[4] or ""})
        bind.execute(
            text("UPDATE equipment SET damage_rolls = :dr WHERE id = :id AND damage_rolls IS NULL"),
            {"dr": _json.dumps(rolls), "id": row[0]},
        )


def downgrade():
    pass
