"""fix combatants character_id nullable and drop unique constraint

Revision ID: g3h4i5j6k7l8
Revises: b2c3d4e5f6a7
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
        # Drop unique constraint on character_id (name varies; try common patterns)
        for constraint_name in ('combatants_character_id_key', 'uq_combatants_character_id'):
            try:
                op.drop_constraint(constraint_name, 'combatants', type_='unique')
                break
            except Exception:
                pass

        # Make character_id nullable
        if not cols.get('character_id', {}).get('nullable', True):
            op.alter_column('combatants', 'character_id', nullable=True)

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
