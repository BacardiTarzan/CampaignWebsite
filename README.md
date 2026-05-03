# D&D 2024 Character Generator

Session Zero character creator for a home campaign. Supports the 2024 Player's Handbook ruleset.

## Running (local dev)

```bash
# Activate the venv
source venv/bin/activate

# Install dependencies (first time)
pip install -r requirements.txt

# Start the server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

On first startup the server auto-seeds the database from `reference/` markdown files.

| URL | Description |
|-----|-------------|
| http://localhost:8000/ | Player character wizard |
| http://localhost:8000/admin | DM admin panel |
| http://localhost:8000/docs | FastAPI auto-docs |

## Environment variables (`.env`)

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///campaign.db` | SQLite or `postgresql+psycopg2://...` |
| `DEBUG` | `false` | Enable debug logging |

## Re-seeding content

Hit `POST /api/admin/seed` in the admin panel (Import tab → "Seed Database" button), or via curl:

```bash
curl -X POST http://localhost:8000/api/admin/seed
```

## Alembic migrations (for schema changes)

```bash
# Generate a new migration after model changes
alembic revision --autogenerate -m "describe the change"

# Apply migrations
alembic upgrade head
```

## Project structure

```
app/
  main.py          — FastAPI app + startup seeder
  config.py        — Settings via .env
  database.py      — SQLAlchemy engine + session
  models/
    content.py     — Species, Class, Subclass, Background, Feat, Spell, Equipment
    character.py   — Character and all related join tables
  routers/
    content.py     — GET endpoints for species/classes/backgrounds/feats/spells
    characters.py  — Wizard step endpoints + JSON/PDF export
    admin.py       — DM roster, codex CRUD, JSON import, seed trigger
  services/
    seeder.py      — Parses reference/ markdown → database records
    export.py      — Character → JSON dict
    pdf.py         — WeasyPrint character sheet renderer
  templates/
    character_sheet.html — HTML template for PDF export
static/
  index.html       — Player wizard
  admin.html       — DM admin panel
  style.css        — Design system (all theming via CSS variables)
  script.js        — Wizard state machine
  admin.js         — Admin panel logic
reference/         — 2024 PHB content as markdown (authoritative seed data)
alembic/           — Database migrations
```

## Phase roadmap

- **Phase 1 (current):** Single-class level 1 creation, full wizard flow, JSON + PDF export, admin panel
- **Phase 2:** Subclass selection at appropriate levels, level-up flow, spell slot tracking
- **Phase 3:** Multiclassing, monster bestiary, deployment prep (Postgres verification)
