"""add conditions column to characters and combatants

Revision ID: l8m9o0p1q2r3
Revises: k7l8m9o0p1q2
Create Date: 2026-06-17
"""
from alembic import op
from sqlalchemy import text, inspect as sa_inspect

revision = 'l8m9o0p1q2r3'
down_revision = 'k7l8m9o0p1q2'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    cols = [
        ("characters", "conditions", "JSON"),
        ("combatants",  "conditions", "JSON"),
    ]
    for table, col, ddl in cols:
        if dialect == "postgresql":
            op.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {ddl}"))
        else:
            existing = {c["name"] for c in sa_inspect(bind).get_columns(table)}
            if col not in existing:
                op.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))


def downgrade():
    pass
