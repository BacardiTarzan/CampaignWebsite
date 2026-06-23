"""encounter initiative, turn state, and character resources

Revision ID: m0n1o2p3q4r5
Revises: l8m9o0p1q2r3
Create Date: 2026-06-23
"""
from alembic import op
from sqlalchemy import text, inspect as sa_inspect

revision = 'm0n1o2p3q4r5'
down_revision = 'l8m9o0p1q2r3'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    # ── 1. New columns on combatants ─────────────────────────────────────────
    new_combatant_cols = [
        ("initiative",                    "INTEGER"),
        ("turn_order",                    "INTEGER"),
        ("action_used",                   "BOOLEAN DEFAULT FALSE"),
        ("bonus_action_used",             "BOOLEAN DEFAULT FALSE"),
        ("reaction_used",                 "BOOLEAN DEFAULT FALSE"),
        ("movement_remaining",            "INTEGER"),
        ("legendary_actions_remaining",   "INTEGER"),
    ]

    if dialect == "postgresql":
        for col, ddl in new_combatant_cols:
            op.execute(text(
                f"ALTER TABLE combatants ADD COLUMN IF NOT EXISTS {col} {ddl}"
            ))
    else:
        existing = {c["name"] for c in sa_inspect(bind).get_columns("combatants")}
        for col, ddl in new_combatant_cols:
            if col not in existing:
                op.execute(text(f"ALTER TABLE combatants ADD COLUMN {col} {ddl}"))

    # ── 2. encounter_state singleton table ───────────────────────────────────
    if dialect == "postgresql":
        op.execute(text("""
            CREATE TABLE IF NOT EXISTS encounter_state (
                id INTEGER PRIMARY KEY DEFAULT 1,
                encounter_active BOOLEAN NOT NULL DEFAULT FALSE,
                initiative_phase BOOLEAN NOT NULL DEFAULT FALSE,
                current_round INTEGER NOT NULL DEFAULT 1,
                current_turn_combatant_id INTEGER
                    REFERENCES combatants(id) ON DELETE SET NULL
            )
        """))
        op.execute(text(
            "INSERT INTO encounter_state (id) VALUES (1) ON CONFLICT DO NOTHING"
        ))
    else:
        tables = sa_inspect(bind).get_table_names()
        if "encounter_state" not in tables:
            op.execute(text("""
                CREATE TABLE encounter_state (
                    id INTEGER PRIMARY KEY DEFAULT 1,
                    encounter_active BOOLEAN NOT NULL DEFAULT 0,
                    initiative_phase BOOLEAN NOT NULL DEFAULT 0,
                    current_round INTEGER NOT NULL DEFAULT 1,
                    current_turn_combatant_id INTEGER
                        REFERENCES combatants(id) ON DELETE SET NULL
                )
            """))
        # Insert singleton row (idempotent via OR IGNORE)
        op.execute(text("INSERT OR IGNORE INTO encounter_state (id) VALUES (1)"))

    # ── 3. character_resources table ─────────────────────────────────────────
    if dialect == "postgresql":
        op.execute(text("""
            CREATE TABLE IF NOT EXISTS character_resources (
                id SERIAL PRIMARY KEY,
                character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
                resource_key VARCHAR NOT NULL,
                label VARCHAR NOT NULL,
                max_uses INTEGER NOT NULL DEFAULT 1,
                used INTEGER NOT NULL DEFAULT 0,
                rest_type VARCHAR NOT NULL DEFAULT 'long'
            )
        """))
    else:
        tables = sa_inspect(bind).get_table_names()
        if "character_resources" not in tables:
            op.execute(text("""
                CREATE TABLE character_resources (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    character_id INTEGER NOT NULL REFERENCES characters(id) ON DELETE CASCADE,
                    resource_key VARCHAR NOT NULL,
                    label VARCHAR NOT NULL,
                    max_uses INTEGER NOT NULL DEFAULT 1,
                    used INTEGER NOT NULL DEFAULT 0,
                    rest_type VARCHAR NOT NULL DEFAULT 'long'
                )
            """))


def downgrade():
    pass
