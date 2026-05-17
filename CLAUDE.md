# CLAUDE.md — Character Generator

## Running locally

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

On first start the server auto-seeds from `reference/`. If you need to reseed, delete `campaign.db` and restart.

## Current status (as of 2026-05-17)

**Phase 1 complete. Phase 2 sheet overhaul complete. Physical lock complete. Level-Up Wizard Overhaul (Phase 3) complete. Rules Glossary complete. Next: Phase 4 — Sheet Spellcasting Tracking.**

### Phase 1 — Character Creation Wizard (complete)
The full 10-step wizard runs end-to-end:
1. Identity · 2. Species · 3. Background · 4. Class · 5. Stats · 6. Class features · 7. Skills + languages · 8. Equipment · 9. Spells · 10. Bio → complete

### Phase 1.5 — Auth + Railway hosting (complete)
Google OAuth live, Railway deployed, PostgreSQL running.

### Phase 2 — Character sheet overhaul (complete)
4-tab live character sheet at `/characters/{id}/sheet`:

- **Stats & Attacks** — ability scores, saves, skills (left); languages, weapon attack cards, spellcasting info (right); class features + species traits below
- **Biography** — height dropdown + weight counter + deity text (autosave); backstory read-only; journal with 2s autosave; physical details lockable by player
- **Equipment** — inventory grouped by type; currency widget (PP/GP/SP/CP)
- **Spells** (casters only) — read-only slot reference panel; spell cards with School/Cast Time/Range/Duration/Components; click to expand description; Prepared/Spellbook/Species badges

HP polled every 15 seconds. Spell slot toggles removed — use physical tokens.

### Phase 2.5 — Physical lock (complete)
Player can lock height/weight/deity once set. DM unlocks via admin panel.
- `physical_locked` Boolean on `Character` + migration `3f9a2b1c4d5e`
- `POST /api/characters/{id}/bio/lock` (player) · `POST /api/admin/characters/{id}/unlock-physical` (DM)
- `PATCH /bio` blocks height/weight/deity when locked; journal always editable
- Admin roster shows unlock button when locked

### Phase 3 — Level-Up Wizard Overhaul (complete as of 2026-05-15)
Full dynamic level-up wizard replacing the old 3-choice flow. Every D&D 2024 decision point is now wired.

**What was built:**
- `app/services/levelup_rules.py` — rules engine: `required_steps()`, `auto_grants()`, `subclass_auto_grants()`, `max_spell_level()`. Encodes all 12 classes' per-level decision tables from `level-up-wizard/*.md`.
- Migration `a1b2c3d4e5f6` — adds `character_spells.always_prepared`, `character_choices.level`, `characters.hp_roll_log`
- `app/models/character.py` — three new columns above
- `app/routers/characters.py` — `GET /api/characters/{id}/levelup-options` returns full step list; `POST /api/characters/{id}/levelup` applies all choices, audits to `CharacterChoice`, updates HP/ASI/feats/spells
- `static/levelup.js` — full rewrite: dynamic step runner, one renderer per step kind (`hp`, `subclass`, `asi`, `epic_boon`, `fighting_style`, `fighting_style_swap`, `expertise`, `cantrips_new`, `spells_new`, `wizard_spellbook`, `spell_swap`, `cantrip_swap`, `metamagic`, `invocations_new`, `invocation_swap`, `mystic_arcanum`, `feature_choice`)
- `static/levelup.css` — all new step-type styles; `--color-ink` overridden to light on dark background
- `static/levelup.html` — stripped fixed panels, single `#lu-step-host` dynamic host
- Admin Repair Schema updated with the three new columns

**Flow:**
1. DM clicks LVL+ in admin → sets `cc.level_granted += 1` (does NOT bump `cc.level`)
2. Portal shows "⬆ Level Up to N" button when `level_granted > level`
3. Player clicks → wizard at `/characters/{id}/levelup`
4. Wizard fetches options, renders steps one at a time, collects choices
5. On confirm: `POST /levelup` → bumps `cc.level`, applies all choices, returns `{ok, new_level, hp_max, hp_gained, auto_added_spells}`
6. Done panel shows result and links to character sheet

**Step types covered:**
| Step | Classes | Notes |
|---|---|---|
| HP (roll/average/manual) | All | Server floors roll at average; CON mod applied |
| Subclass | All (L3) | Auto-grants domain/patron/oath spells |
| ASI (+2/+1+1/feat) | All ASI levels | Retroactive CON HP recompute |
| Epic Boon | All (L19) | Picks from epic_boon feat category |
| Fighting Style | Paladin/Ranger L2 | Also optional swap for Fighter every level |
| Expertise | Bard/Ranger/Rogue | Picks from owned non-expertise skills |
| Cantrips | All casters at gain levels | |
| Spells (known) | Bard/Sorcerer/Warlock/Ranger | |
| Wizard Spellbook | Wizard (+2/level) | saved as `prepared=False` |
| Spell swap | Known-spell casters | Optional each level |
| Cantrip swap | Known-spell casters | Optional each level |
| Metamagic | Sorcerer (L2/10/17) | Hard-coded 10 options |
| Invocations | Warlock | Gains + optional swap each level |
| Mystic Arcanum | Warlock (L9/11/13/15) | 6th/7th/8th/9th spell, 1/long rest |
| Feature choices | All | Parsed from `choice_required=True` features |

**Audit trail:** Every choice stored in `CharacterChoice` with `level=next_level` and `feature_key="lvlup:{level}:{step_id}"`.

### Phase 3.5 — Rules Glossary (complete as of 2026-05-17)
Standalone `/glossary` page + inline tooltips on the character sheet.

**What was built:**
- `static/glossary.html` / `glossary.js` / `glossary.css` — standalone page reusing lore layout (leather sidebar + parchment content area). Sidebar shows category counts; accordion cards expand to full description; hash-anchor deep-linking (`/glossary#advantage`); search filters across all fields.
- `GET /api/content/glossary` — auth-guarded endpoint returning all `GlossaryTerm` rows.
- `GlossaryTerm` model + migration `b2c3d4e5f6a7` — `slug`, `term`, `category`, `short_description`, `full_description`, `ability`, `source`.
- 94 terms seeded from `reference_claude/rules/glossary.md` across 6 categories: combat, condition, action, weapon_property, mastery, skill.
- Sheet tooltip system (`sheet.js`) — `loadGlossary()` fetches terms on boot; `gloss(name)` wraps matching text in `<span class="gloss-term">`; `glossifyDescription(text)` auto-links descriptions. Click opens a popover; "Read full rule ›" (only shown when `full_description ≠ short_description`) opens a modal; modal footer has "View in Glossary ↗" link.
- Portal `portal.html` — added "📜 Rules Glossary" button alongside Lore Library.

**Key CSS:**
- `.gloss-term` — dotted gold underline, `cursor: help`
- `.gloss-popover` — `position: fixed`, `z-index: 2000`, `pointer-events: none` (child `.gloss-popover-more` has `pointer-events: auto`)
- Popover positioned using viewport coords from `getBoundingClientRect()` only — do NOT add `scrollX`/`scrollY` (popover is `position: fixed`, not absolute)
- `.char-card-name` on portal — `color: #fff; font-weight: 700` (was too-pale `var(--light)` against dark card background)

## Next: Phase 4 — Sheet Spellcasting Tracking

The Spells tab shows spells but has no way to manage prepared spells per long rest, no Wizard spellbook/prepared split, no Pact Magic block, no Mystic Arcanum section, and no always-prepared badges for domain/patron/oath spells.

### What to build

**Backend:**
- `PATCH /api/characters/{id}/prepared-spells` — body: `{spell_ids: [int]}`. Validates caster type, spell levels, prepared max formula. Sets `prepared=True` on listed rows + always-prepared; `False` on rest. Wizard spellbook spells stay in DB but `prepared=False`.
- Add to `sheet-data` response: `prepared_max` (formula per class), `always_prepared_ids`, `spellbook_ids` (Wizard), `prepared_count`

**Prepared max formulas (by class):**
- Cleric: `wisdom_mod + cleric_level`
- Druid: `wisdom_mod + druid_level`
- Paladin: `charisma_mod + floor(paladin_level / 2)`
- Ranger: `wisdom_mod + floor(ranger_level / 2)`
- Wizard: `intelligence_mod + wizard_level`

**Frontend (sheet.js `renderSpellsTab`):**
Restructure into sections:
1. Spellcasting header (already exists — keep)
2. Slot reference bar (already exists — keep)
3. Class resource blocks (new — Warlock Pact Magic note, Mystic Arcanum list, Paladin Lay on Hands pool, Wizard Arcane Recovery note, etc.)
4. "Prepared X / Y — ✎ Prepare Spells" row (for prep casters: Cleric/Druid/Paladin/Ranger/Wizard)
5. Spell groups with new badges:
   - `Always Prepared` silver (domain/patron/oath/subclass)
   - `Spellbook` blue (Wizard — always visible)
   - `Prepared` green (prepared=True; for Wizard means spellbook AND prepared)
6. Warlock: no prep button; known spells always available; Mystic Arcanum group at top with "1/long rest" badge
7. Bard/Sorcerer: no prep button; "Known Spells" header with note

**Prepare Spells modal:**
- Header: "Prepare Spells — Long Rest · X of Y"
- Locked always-prepared section (doesn't count against max)
- Selectable section: class list (or spellbook for Wizard), filtered by max slot level; checkboxes; disable at max
- Cantrips listed below (no checkbox)
- Save → `PATCH /prepared-spells` → re-render

**Known issues / gaps to fix in Phase 4:**
- Sheet Spells tab currently shows a static "Prepared" badge on all class spells — this is incorrect for prepared casters; Phase 4 replaces it with real prep state
- `always_prepared` rows exist in DB (added by Phase 3 level-up) but the sheet doesn't display them differently yet
- Mystic Arcanum spells (source="arcanum") need their own section on the Warlock sheet

## Known issues

- **End-to-end testing not done for all 12 classes at all levels** — spot-tested a few classes; full matrix check still needed before calling Phase 3 production-ready
- **PDF export** — `app/templates/character_sheet.html` exists but visual QA not done. PDF button removed from player side; admin still has export.
- **Bard skill list** — falls back to full 18-skill list (correct behavior).

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
- Repair Schema used `ADD COLUMN IF NOT EXISTS` (PostgreSQL-only syntax) — fixed to use dialect-aware inspector check on SQLite.
- `combatants` table created with `character_id NOT NULL` and unique constraint by migration `e1f2a3b4c5d6`; monster columns (`monster_id`, `custom_name`, `hp_current`, `hp_max_override`) never applied on Railway because `bind.execute()` silently no-ops in newer SQLAlchemy — fixed in migration `h4i5j6k7l8m9` using `op.execute()` + `ADD COLUMN IF NOT EXISTS`.
- Admin character HP endpoint read `delta` from query params but combat tracker sent it as JSON body — fixed with `AdminHpIn` Pydantic model; endpoint accepts both body and query param for backward compat.
- Fresh Railway DB failed on startup because initial schema migration is empty (`pass`) so `add_column` migrations failed on non-existent tables — fixed in `app/main.py`: run `create_all` first, then stamp alembic to head if `alembic_version` is empty (fresh DB), else run `upgrade head` for existing DBs.

## Phase 1.5 — Google Auth + Railway (complete)

- Google OAuth via Authlib + server-side sessions (cookie-backed)
- `ALLOWED_EMAILS` controls who can log in; `ADMIN_EMAIL` controls admin access
- All `/api/characters` routes scoped to `owner_email`; all `/api/admin` routes require admin
- Railway deployed with PostgreSQL; startup order: `create_all` first (idempotent), then stamp alembic to head on fresh DB or `upgrade head` on existing DB
- `app/config.py` `reference_dir` points to `reference_claude/`

## Architecture notes

- All theming via CSS variables in `static/style.css` `:root {}`.
- Equipment options are JSON arrays of `{label, items[], gold?}` on `DnDClass.equipment_options` and `Background.equipment_options`.
- `stat_roll_locked` on `Character` prevents re-rolling; DM unlocks via `POST /api/admin/characters/{id}/unlock-stats`.
- `physical_locked` on `Character` locks height/weight/deity edits; player locks via `POST /api/characters/{id}/bio/lock`; DM unlocks via `POST /api/admin/characters/{id}/unlock-physical`. Added in migration `3f9a2b1c4d5e`.
- Seeder is idempotent for inserts; also refreshes spells missing `casting_time`/`range`/`duration`.
- `CharacterSpell` has `source` ("class" | "species" | "subclass" | "arcanum"), `notes`, and `always_prepared` (Boolean) columns. Species spells preserved across spell saves. Subclass/arcanum spells added by level-up wizard.
- `Character` has `height`, `weight`, `deity`, `journal`, `currency` (JSON), `hp_roll_log` (JSON — level-up HP audit) columns.
- `CharacterChoice` has `level` (Integer) column — all level-up choices stored with `feature_key="lvlup:{level}:{step_id}"`.
- `app/services/levelup_rules.py` — pure rules engine for level-up wizard. No DB writes; only reads class/subclass/char data.
- Admin Import tab has one-shot maintenance buttons: Repair Schema, Convert Gold, Refresh Spells, Backfill Species Spells. Repair Schema covers all columns through migration `h4i5j6k7l8m9`.
- `Monster` model in `content.py`; `Combatant` model in `character.py`. `Combatant.character_id` nullable (PC combatants); `Combatant.monster_id` nullable (monster combatants). Combat tracker in admin Combat tab.
- **Migration rule:** always use `op.execute(text(...))` for raw SQL in alembic migrations — never `bind.execute()` which silently no-ops on PostgreSQL in SQLAlchemy 2.x. Use `ADD COLUMN IF NOT EXISTS` on PostgreSQL for idempotent column additions.

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
  glossary.html / glossary.js / glossary.css — Rules Glossary page
  admin.html / admin.js    — DM admin panel
  style.css                — Design system (CSS variables)
  lore.html / lore.js / lore.css — Lore Library page
reference_claude/          — 2024 PHB markdown (authoritative source)
reference_old/             — Old reference files (do not use)
alembic/                   — Migrations
```
