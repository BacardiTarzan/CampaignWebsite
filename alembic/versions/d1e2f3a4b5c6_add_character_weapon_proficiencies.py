"""add character_weapon_proficiencies table

Revision ID: d1e2f3a4b5c6
Revises: b2c3d4e5f6a7
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa

revision = 'd1e2f3a4b5c6'
down_revision = 'c1d2e3f4a5b6'
branch_labels = None
depends_on = None


def upgrade():
    from alembic import op as _op
    from sqlalchemy import inspect
    bind = _op.get_bind()
    if 'character_weapon_proficiencies' not in inspect(bind).get_table_names():
        op.create_table(
            'character_weapon_proficiencies',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('character_id', sa.Integer(), sa.ForeignKey('characters.id'), nullable=False),
            sa.Column('proficiency_type', sa.String(), nullable=False),
            sa.PrimaryKeyConstraint('id'),
        )


def downgrade():
    op.drop_table('character_weapon_proficiencies')
