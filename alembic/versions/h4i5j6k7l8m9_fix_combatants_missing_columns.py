"""ensure combatants has all required columns and monsters table exists

Revision ID: h4i5j6k7l8m9
Revises: g3h4i5j6k7l8
Create Date: 2026-05-17
"""
from alembic import op
import sqlalchemy as sa

revision = 'h4i5j6k7l8m9'
down_revision = 'g3h4i5j6k7l8'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect, text
    bind = op.get_bind()
    dialect = bind.dialect.name
    tables = inspect(bind).get_table_names()

    # Ensure monsters table exists
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

    # Add any missing combatants columns
    existing_cols = {c['name'] for c in inspect(bind).get_columns('combatants')}
    missing = [
        ('monster_id',      'INTEGER'),
        ('custom_name',     'VARCHAR'),
        ('hp_current',      'INTEGER'),
        ('hp_max_override', 'INTEGER'),
        ('added_at',        'TIMESTAMP'),
    ]
    for col, col_type in missing:
        if col not in existing_cols:
            # monster_id FK — only add the FK clause when monsters table exists
            if col == 'monster_id':
                bind.execute(text(
                    "ALTER TABLE combatants ADD COLUMN monster_id INTEGER "
                    "REFERENCES monsters(id) ON DELETE CASCADE"
                ))
            else:
                bind.execute(text(
                    f"ALTER TABLE combatants ADD COLUMN {col} {col_type}"
                ))

    # Make character_id nullable if still NOT NULL (PostgreSQL only — SQLite
    # was handled in g3h4i5j6k7l8 via table-recreate)
    if dialect == 'postgresql':
        bind.execute(text("""
            DO $$
            BEGIN
                IF EXISTS (
                    SELECT 1 FROM information_schema.columns
                    WHERE table_name = 'combatants'
                      AND column_name = 'character_id'
                      AND is_nullable = 'NO'
                ) THEN
                    ALTER TABLE combatants ALTER COLUMN character_id DROP NOT NULL;
                END IF;
            END$$;
        """))
        # Drop any remaining unique constraints on character_id
        bind.execute(text("""
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


def downgrade():
    pass
