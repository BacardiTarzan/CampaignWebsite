"""add glossary_terms table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa

revision = 'b2c3d4e5f6a7'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None


def upgrade():
    from alembic import op as _op
    from sqlalchemy import inspect
    bind = _op.get_bind()
    if 'glossary_terms' not in inspect(bind).get_table_names():
        op.create_table(
            'glossary_terms',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('slug', sa.String(), nullable=False),
            sa.Column('term', sa.String(), nullable=False),
            sa.Column('category', sa.String(), nullable=False),
            sa.Column('short_description', sa.Text(), nullable=False),
            sa.Column('full_description', sa.Text(), nullable=False),
            sa.Column('ability', sa.String(), nullable=True),
            sa.Column('source', sa.String(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('slug'),
        )
        op.create_index('ix_glossary_terms_slug', 'glossary_terms', ['slug'])


def downgrade():
    op.drop_index('ix_glossary_terms_slug', 'glossary_terms')
    op.drop_table('glossary_terms')
