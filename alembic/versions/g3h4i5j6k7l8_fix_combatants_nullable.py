"""fix combatants character_id nullable and drop unique constraint

Revision ID: g3h4i5j6k7l8
Revises: f2a3b4c5d6e7
Create Date: 2026-05-17
"""
from alembic import op
import sqlalchemy as sa

revision = 'g3h4i5j6k7l8'
down_revision = 'f2a3b4c5d6e7'
branch_labels = None
depends_on = None


def upgrade():
    from sqlalchemy import inspect, text
    bind = op.get_bind()
    dialect = bind.dialect.name

    cols = {c['name']: c for c in inspect(bind).get_columns('combatants')}

    if dialect == 'postgresql':
        # Use raw SQL with IF EXISTS — avoids aborted-transaction issues from try/except
        # around op.drop_constraint with a wrong constraint name.
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
        # Make character_id nullable if it currently is NOT NULL
        if not cols.get('character_id', {}).get('nullable', True):
            bind.execute(text(
                "ALTER TABLE combatants ALTER COLUMN character_id DROP NOT NULL"
            ))

    else:
        # SQLite cannot ALTER COLUMN; recreate the table if character_id is NOT NULL
        char_col = cols.get('character_id')
        if char_col and not char_col.get('nullable', True):
            bind.execute(text("""
                CREATE TABLE combatants_new (
                    id INTEGER PRIMARY KEY,
                    character_id INTEGER REFERENCES characters(id) ON DELETE CASCADE,
                    monster_id INTEGER REFERENCES monsters(id) ON DELETE CASCADE,
                    custom_name VARCHAR,
                    hp_current INTEGER,
                    hp_max_override INTEGER,
                    added_at TIMESTAMP
                )
            """))
            bind.execute(text("""
                INSERT INTO combatants_new
                    (id, character_id, monster_id, custom_name, hp_current, hp_max_override, added_at)
                SELECT id, character_id, monster_id, custom_name, hp_current, hp_max_override, added_at
                FROM combatants
            """))
            bind.execute(text("DROP TABLE combatants"))
            bind.execute(text("ALTER TABLE combatants_new RENAME TO combatants"))


def downgrade():
    pass
