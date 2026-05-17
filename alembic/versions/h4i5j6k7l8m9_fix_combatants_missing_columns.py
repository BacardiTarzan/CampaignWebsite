"""ensure combatants has all required columns and monsters table exists

Revision ID: h4i5j6k7l8m9
Revises: g3h4i5j6k7l8
Create Date: 2026-05-17
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, inspect as sa_inspect

revision = 'h4i5j6k7l8m9'
down_revision = 'g3h4i5j6k7l8'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name
    tables = sa_inspect(bind).get_table_names()

    # Ensure monsters table exists first (FK target for monster_id)
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

    if dialect == 'postgresql':
        # ADD COLUMN IF NOT EXISTS is idempotent — no inspect caching issues.
        # bind.execute() silently no-ops in newer SQLAlchemy; op.execute() is correct.
        for stmt in [
            "ALTER TABLE combatants ADD COLUMN IF NOT EXISTS monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE",
            "ALTER TABLE combatants ADD COLUMN IF NOT EXISTS custom_name VARCHAR",
            "ALTER TABLE combatants ADD COLUMN IF NOT EXISTS hp_current INTEGER",
            "ALTER TABLE combatants ADD COLUMN IF NOT EXISTS hp_max_override INTEGER",
        ]:
            op.execute(text(stmt))

        # Drop NOT NULL on character_id (ignore error if already nullable)
        op.execute(text("""
            DO $$
            BEGIN
                ALTER TABLE combatants ALTER COLUMN character_id DROP NOT NULL;
            EXCEPTION WHEN OTHERS THEN NULL;
            END$$;
        """))

        # Drop all unique constraints on combatants (character_id had one)
        op.execute(text("""
            DO $$
            DECLARE r RECORD;
            BEGIN
                FOR r IN
                    SELECT conname FROM pg_constraint
                    WHERE conrelid = 'combatants'::regclass AND contype = 'u'
                LOOP
                    EXECUTE 'ALTER TABLE combatants DROP CONSTRAINT ' || quote_ident(r.conname);
                END LOOP;
            END$$;
        """))

    else:
        # SQLite: inspect then add only missing columns (no IF NOT EXISTS support)
        existing = {c['name'] for c in sa_inspect(bind).get_columns('combatants')}
        for col, ddl in [
            ('monster_id',      'INTEGER REFERENCES monsters(id) ON DELETE CASCADE'),
            ('custom_name',     'VARCHAR'),
            ('hp_current',      'INTEGER'),
            ('hp_max_override', 'INTEGER'),
        ]:
            if col not in existing:
                op.execute(text(f"ALTER TABLE combatants ADD COLUMN {col} {ddl}"))


def downgrade():
    pass
