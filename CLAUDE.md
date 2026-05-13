# CLAUDE.md — Character Generator

## Running locally

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

On first start the server auto-seeds from `reference/`. If you need to reseed, delete `campaign.db` and restart.

## Current status (as of 2026-05-13)

**Phase 1 is complete. Phase 2 character sheet overhaul is done.**

### Phase 1 — Wizard (complete)
The full 10-step wizard runs end-to-end:
1. Identity · 2. Species · 3. Background · 4. Class · 5. Stats · 6. Class features · 7. Skills + languages · 8. Equipment · 9. Spells · 10. Bio → complete

### Phase 1.5 — Auth + Railway hosting (complete)
Google OAuth live, Railway deployed, PostgreSQL running.

### Phase 2 — Character sheet overhaul (complete as of 2026-05-13)
4-tab live character sheet at `/characters/{id}/sheet`:

- **Stats & Attacks** — ability scores, saves, skills (left); languages, weapon attack cards, spellcasting info (right); class features + species traits below
- **Biography** — height/weight/deity editable by player (autosave on blur); backstory read-only; journal textarea with 2s autosave → `PATCH /api/characters/{id}/bio`
- **Equipment** — inventory grouped by type; currency widget (PP/GP/SP/CP)
- **Spells** (casters only) — read-only slot reference panel; spell cards show School, Cast Time, Range, Duration, Components without clicking; click to expand full description; Prepared/Spellbook/Species badges

HP polled every 15 seconds from the server (DM controls HP via admin).
Spell slot interactive toggles removed — use physical tokens at the table.

### Species spell grants (complete)
Species-granted spells (e.g. Gnome Mending/Prestidigitation, Forest Gnome Speak with Animals) are parsed from markdown at species-selection time and saved to `character_spells` with `source="species"`. They appear in the Spells tab with a gold "Species" badge and any special casting notes. They are filtered out of the class spell picker so players don't double-select. Admin Import tab has a "Backfill Species Spells" button for existing characters.

## Known issues / next steps

- **End-to-end testing not yet done for all 12 classes.** Do a full run before calling Phase 1 done.
- **PDF export** — `app/templates/character_sheet.html` exists but visual QA not done. PDF button removed from player side; admin still has export.
- **Bard skill list** — falls back to full 18-skill list (correct behavior).
- **Phase 2 major items not yet started** — see `Next Phase.md` for full list.

## Bugs fixed (cumulative)

- `skill_options` was always empty for all classes — fixed with direct regex in `_parse_class_file`.
- Bard "choose any 3" skills — second regex branch added.
- `save_species` broken `__import__` hack — fixed.
- Tool choice dropdown always showed Artisan's Tools — fixed with direct `TOOL_OPTIONS[bg.tool_proficiency]` lookup.
- Fighting style / divine order options now show inline descriptions; weapon mastery checklist shows mastery property tags with tooltips.
- Species display "Forest Gnome Gnome" — fixed to `species_lineage || species_name` throughout portal, sheet, export.
- Parent lineage trait (e.g. "Gnomish Lineage") was showing instead of the selected lineage's traits — export now filters parent trait and injects selected lineage description.
- Species cantrips were selectable again as class cantrips — class spell picker now filters owned spell IDs; species grants are a bonus, not counted against class cantrip allotment.
- `save_spells` was wiping species spells — now only deletes rows where `source != "species"`.
- Gold stored as custom equipment row — admin "Convert Gold" button moves it to `currency.gp`; sheet filters it from gear display.
- Spell stats (casting_time, range, duration) were empty on Railway from old seed — seeder now refreshes rows missing any of those fields; admin "Refresh Spells" button triggers it.
- Railway missing `source`/`notes` columns on `character_spells` and `height`/`weight`/`deity`/`journal`/`currency` on `characters` — admin "Repair Schema" button applies all missing columns via `ALTER TABLE ... IF NOT EXISTS`.

## Phase 1.5 — Google Auth + Railway (complete)

- Google OAuth via Authlib + server-side sessions (cookie-backed)
- `ALLOWED_EMAILS` controls who can log in; `ADMIN_EMAIL` controls admin access
- All `/api/characters` routes scoped to `owner_email`; all `/api/admin` routes require admin
- Railway deployed with PostgreSQL; auto-migrates via `alembic upgrade head` on startup + `create_all` safety net
- `app/config.py` `reference_dir` points to `reference_claude/`

## Architecture notes

- All theming via CSS variables in `static/style.css` `:root {}`.
- Equipment options are JSON arrays of `{label, items[], gold?}` on `DnDClass.equipment_options` and `Background.equipment_options`.
- `stat_roll_locked` on `Character` prevents re-rolling; DM unlocks via `POST /api/admin/characters/{id}/unlock-stats`.
- Seeder is idempotent for inserts; also refreshes spells missing `casting_time`/`range`/`duration`.
- `CharacterSpell` has `source` ("class" | "species") and `notes` columns. Species spells are parsed at step 2 and preserved across spell saves.
- `Character` has `height`, `weight`, `deity`, `journal`, `currency` (JSON) columns added in migration `18da8cfaf343`.
- Admin Import tab has one-shot maintenance buttons: Repair Schema, Convert Gold, Refresh Spells, Backfill Species Spells.

## Project structure

```
app/
  main.py          — FastAPI app + lifespan seeder
  config.py        — pydantic-settings from .env
  database.py      — SQLAlchemy engine + session
  models/
    content.py     — Species, DnDClass, Subclass, Background, Feat, Spell, Equipment
    character.py   — Character + all join tables
  dependencies.py  — require_user / require_admin FastAPI deps
  routers/
    content.py     — GET endpoints for content (public)
    characters.py  — Wizard step endpoints + JSON/PDF export (require_user)
    admin.py       — DM roster, codex CRUD, seed trigger (require_admin)
    auth.py        — Google OAuth login/callback/logout/me
  services/
    seeder.py      — Markdown → DB (regex parser)
    export.py      — Character → JSON dict
    pdf.py         — WeasyPrint renderer
  templates/
    character_sheet.html
static/
  index.html / script.js   — Player wizard
  portal.html / portal.js  — Player character roster
  sheet.html / sheet.js / sheet.css — Live character sheet (4-tab)
  admin.html / admin.js    — DM admin panel
  style.css                — Design system (CSS variables)
reference_claude/          — 2024 PHB markdown (authoritative source)
reference_old/             — Old reference files (do not use)
alembic/                   — Migrations
```
