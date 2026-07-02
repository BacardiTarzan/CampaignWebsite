"""add action_type to character_resources

Revision ID: n1o2p3q4r5s6
Revises: m0n1o2p3q4r5
Create Date: 2026-07-02
"""
from alembic import op
from sqlalchemy import text, inspect as sa_inspect

revision = 'n1o2p3q4r5s6'
down_revision = 'm0n1o2p3q4r5'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        op.execute(text(
            "ALTER TABLE character_resources ADD COLUMN IF NOT EXISTS action_type VARCHAR"
        ))
    else:
        existing = {c["name"] for c in sa_inspect(bind).get_columns("character_resources")}
        if "action_type" not in existing:
            op.execute(text(
                "ALTER TABLE character_resources ADD COLUMN action_type VARCHAR"
            ))


def downgrade():
    pass
