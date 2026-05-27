"""add proficiency_base to equipment

Revision ID: j6k7l8m9o0p1
Revises: i5j6k7l8m9o0
Create Date: 2026-05-26
"""
from alembic import op
from sqlalchemy import text, inspect as sa_inspect

revision = 'j6k7l8m9o0p1'
down_revision = 'i5j6k7l8m9o0'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    if dialect == "postgresql":
        op.execute(text("ALTER TABLE equipment ADD COLUMN IF NOT EXISTS proficiency_base VARCHAR"))
    else:
        existing = {c["name"] for c in sa_inspect(bind).get_columns("equipment")}
        if "proficiency_base" not in existing:
            op.execute(text("ALTER TABLE equipment ADD COLUMN proficiency_base VARCHAR"))


def downgrade():
    pass
