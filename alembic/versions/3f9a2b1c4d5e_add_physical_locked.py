"""add physical_locked to characters

Revision ID: 3f9a2b1c4d5e
Revises: 18da8cfaf343
Create Date: 2026-05-14

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '3f9a2b1c4d5e'
down_revision: Union[str, None] = '18da8cfaf343'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('characters', sa.Column('physical_locked', sa.Boolean(), nullable=True, server_default='false'))


def downgrade() -> None:
    op.drop_column('characters', 'physical_locked')
