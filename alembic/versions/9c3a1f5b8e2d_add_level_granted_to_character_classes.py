"""add level_granted to character_classes

Revision ID: 9c3a1f5b8e2d
Revises: 7a1e3c9f2d08
Create Date: 2026-05-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '9c3a1f5b8e2d'
down_revision: Union[str, None] = '7a1e3c9f2d08'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('character_classes', sa.Column('level_granted', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('character_classes', 'level_granted')
