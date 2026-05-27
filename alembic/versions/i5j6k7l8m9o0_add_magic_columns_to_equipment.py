"""add magic_bonus, bonus_damage, bonus_damage_type to equipment

Revision ID: i5j6k7l8m9o0
Revises: h4i5j6k7l8m9
Create Date: 2026-05-26
"""
from alembic import op
from sqlalchemy import text, inspect as sa_inspect

revision = 'i5j6k7l8m9o0'
down_revision = 'h4i5j6k7l8m9'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    new_cols = [
        ("magic_bonus",       "INTEGER"),
        ("bonus_damage",      "VARCHAR"),
        ("bonus_damage_type", "VARCHAR"),
    ]

    if dialect == "postgresql":
        for col, ddl in new_cols:
            op.execute(text(f"ALTER TABLE equipment ADD COLUMN IF NOT EXISTS {col} {ddl}"))
    else:
        existing = {c["name"] for c in sa_inspect(bind).get_columns("equipment")}
        for col, ddl in new_cols:
            if col not in existing:
                op.execute(text(f"ALTER TABLE equipment ADD COLUMN {col} {ddl}"))


def downgrade():
    pass
