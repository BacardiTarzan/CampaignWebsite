"""Add columns for level-up overhaul (always_prepared, choice level, hp_roll_log)

Revision ID: a1b2c3d4e5f6
Revises: 9c3a1f5b8e2d
Create Date: 2026-05-15

"""
from alembic import op
import sqlalchemy as sa

revision = 'a1b2c3d4e5f6'
down_revision = '9c3a1f5b8e2d'
branch_labels = None
depends_on = None


def upgrade():
    op.add_column('character_spells',
        sa.Column('always_prepared', sa.Boolean(), nullable=True, server_default='false'))
    op.add_column('character_choices',
        sa.Column('level', sa.Integer(), nullable=True))
    op.add_column('characters',
        sa.Column('hp_roll_log', sa.JSON(), nullable=True))


def downgrade():
    op.drop_column('character_spells', 'always_prepared')
    op.drop_column('character_choices', 'level')
    op.drop_column('characters', 'hp_roll_log')
