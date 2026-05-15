"""add age to characters

Revision ID: 7a1e3c9f2d08
Revises: 3f9a2b1c4d5e
Create Date: 2026-05-15

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '7a1e3c9f2d08'
down_revision: Union[str, None] = '3f9a2b1c4d5e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('characters', sa.Column('age', sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column('characters', 'age')
