"""add monsters table and extend combatants

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-05-16
"""
from alembic import op
import sqlalchemy as sa

revision = 'f2a3b4c5d6e7'
down_revision = 'e1f2a3b4c5d6'
branch_labels = None
depends_on = None


def upgrade():
    from alembic import op as _op
    from sqlalchemy import inspect, text
    bind = _op.get_bind()
    tables = inspect(bind).get_table_names()

    if 'monsters' not in tables:
        op.create_table(
            'monsters',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('name', sa.String(), nullable=False),
            sa.Column('size', sa.String(), nullable=True),
            sa.Column('creature_type', sa.String(), nullable=True),
            sa.Column('alignment', sa.String(), nullable=True),
            sa.Column('ac', sa.Integer(), nullable=True),
            sa.Column('initiative', sa.String(), nullable=True),
            sa.Column('hp_max', sa.Integer(), nullable=True),
            sa.Column('hp_formula', sa.String(), nullable=True),
            sa.Column('speed', sa.String(), nullable=True),
            sa.Column('cr', sa.String(), nullable=True),
            sa.Column('xp', sa.Integer(), nullable=True),
            sa.Column('proficiency_bonus', sa.Integer(), nullable=True),
            sa.Column('str', sa.Integer(), nullable=True),
            sa.Column('dex', sa.Integer(), nullable=True),
            sa.Column('con', sa.Integer(), nullable=True),
            sa.Column('int', sa.Integer(), nullable=True),
            sa.Column('wis', sa.Integer(), nullable=True),
            sa.Column('cha', sa.Integer(), nullable=True),
            sa.Column('saving_throws', sa.String(), nullable=True),
            sa.Column('skills', sa.String(), nullable=True),
            sa.Column('resistances', sa.String(), nullable=True),
            sa.Column('immunities', sa.String(), nullable=True),
            sa.Column('vulnerabilities', sa.String(), nullable=True),
            sa.Column('senses', sa.String(), nullable=True),
            sa.Column('languages', sa.String(), nullable=True),
            sa.Column('gear', sa.String(), nullable=True),
            sa.Column('traits', sa.JSON(), nullable=True),
            sa.Column('actions', sa.JSON(), nullable=True),
            sa.Column('bonus_actions', sa.JSON(), nullable=True),
            sa.Column('reactions', sa.JSON(), nullable=True),
            sa.Column('legendary_actions', sa.JSON(), nullable=True),
            sa.Column('source', sa.String(), nullable=True),
            sa.Column('is_homebrew', sa.Boolean(), default=False),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('name'),
        )

    # Extend combatants: add monster columns
    dialect = bind.dialect.name
    if dialect == 'postgresql':
        for stmt in [
            "ALTER TABLE combatants ADD COLUMN IF NOT EXISTS monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE",
            "ALTER TABLE combatants ADD COLUMN IF NOT EXISTS custom_name VARCHAR",
            "ALTER TABLE combatants ADD COLUMN IF NOT EXISTS hp_current INTEGER",
            "ALTER TABLE combatants ADD COLUMN IF NOT EXISTS hp_max_override INTEGER",
        ]:
            op.execute(text(stmt))
    else:
        cols = {c['name'] for c in inspect(bind).get_columns('combatants')}
        for col, ddl in [
            ('monster_id', 'INTEGER REFERENCES monsters(id) ON DELETE CASCADE'),
            ('custom_name', 'VARCHAR'),
            ('hp_current', 'INTEGER'),
            ('hp_max_override', 'INTEGER'),
        ]:
            if col not in cols:
                op.execute(text(f'ALTER TABLE combatants ADD COLUMN {col} {ddl}'))


def downgrade():
    op.drop_table('monsters')
