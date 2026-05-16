"""add tool_proficiencies to classes

Revision ID: c1d2e3f4a5b6
Revises: b2c3d4e5f6a7
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa

revision = 'c1d2e3f4a5b6'
down_revision = 'b2c3d4e5f6a7'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('classes') as batch_op:
        batch_op.add_column(sa.Column('tool_proficiencies', sa.JSON(), nullable=True))


def downgrade():
    with op.batch_alter_table('classes') as batch_op:
        batch_op.drop_column('tool_proficiencies')
