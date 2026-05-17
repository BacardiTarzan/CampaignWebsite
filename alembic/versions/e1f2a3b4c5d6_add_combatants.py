"""add combatants table

Revision ID: e1f2a3b4c5d6
Revises: d1e2f3a4b5c6
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa

revision = 'e1f2a3b4c5d6'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None


def upgrade():
    from alembic import op as _op
    from sqlalchemy import inspect
    bind = _op.get_bind()
    if 'combatants' not in inspect(bind).get_table_names():
        op.create_table(
            'combatants',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('character_id', sa.Integer(), sa.ForeignKey('characters.id', ondelete='CASCADE'), nullable=False),
            sa.Column('added_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('character_id'),
        )


def downgrade():
    op.drop_table('combatants')
