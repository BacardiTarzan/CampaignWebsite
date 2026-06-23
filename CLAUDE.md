# CLAUDE.md — Character Generator

## Running locally

```bash
~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

On first start the server auto-seeds from `reference_claude/`. If you need to reseed, delete `campaign.db` and restart.

**Note:** No virtualenv — Python packages are installed user-local via `~/.local/bin/pip`. pip was bootstrapped with `get-pip.py --user --break-system-packages` on Python 3.14.4.

## Current status (as of 2026-06-23)

**Phase 1 complete. Phase 2 sheet overhaul complete. Physical lock complete. Level-Up Wizard Overhaul (Phase 3) complete. Rules Glossary complete. Phase 4 prepared-spell tracking complete. Conditions + Mastery Swap complete. Playwright test infrastructure in place. Next: CSS/HTML UX overhaul.**

### Phase 1 — Character Creation Wizard (complete)
The full 10-step wizard runs end-to-end:
1. Identity · 2. Species · 3. Background · 4. Class · 5. Stats · 6. Class features · 7. Skills + languages · 8. Equipment · 9. Spells · 10. Bio → complete

### Phase 1.5 — Auth + Railway hosting (complete)
Google OAuth via Authlib + server-side sessions (cookie-backed). Railway deployed, PostgreSQL running.
- `ALLOWED_EMAILS` controls who can log in; `ADMIN_EMAIL` controls admin access
- All `/api/characters` routes scoped to `owner_email`; all `/api/admin` routes require admin
- Startup order: `create_all` first (idempotent), then stamp alembic to head on fresh DB or `upgrade head` on existing DB

### Phase 2 — Character sheet overhaul (complete)
4-tab live character sheet at `/characters/{id}/sheet`:
- **Stats & Attacks** — ability scores, saves, skills (left); languages, weapon attack cards, spellcasting info (right); class features + species traits below
- **Biography** — height dropdown + weight counter + deity text (autosave); backstory read-only; journal with 2s autosave; physical details lockable by player
- **Equipment** — inventory grouped by type; currency widget (PP/GP/SP/CP)
- **Spells** (casters only) — slot reference bar; spell cards; Prepared/Spellbook/Species/Always-Prepared/Arcanum badges; "✎ Prepare Spells" modal for prep casters

HP polled every 15 seconds (same poll also carries `conditions`). Spell slot toggles removed — use physical tokens.

### Phase 2.5 — Physical lock (complete)
- `physical_locked` Boolean on `Character` + migration `3f9a2b1c4d5e`
- `POST /api/characters/{id}/bio/lock` (player) · `POST /api/admin/characters/{id}/unlock-physical` (DM)

### Phase 3 — Level-Up Wizard Overhaul (complete as of 2026-05-15)
Full dynamic level-up wizard at `/characters/{id}/levelup`.

**Key files:**
- `app/services/levelup_rules.py` — pure rules engine: `required_steps()`, `auto_grants()`, `subclass_auto_grants()`, `max_spell_level()`. Also exports `BARD_PREPARED_BY_LEVEL` (fixed table, not formula), `CANTRIP_GAINS`, `KNOWN_SPELL_GAINS`, `ELDRITCH_INVOCATIONS`, `METAMAGIC_OPTIONS`, `CLASS_ALWAYS_PREPARED`, `SUBCLASS_ALWAYS_PREPARED`, `BATTLE_MASTER_MANEUVERS`.
- `app/routers/characters.py` — `GET /api/characters/{id}/levelup-options` + `POST /api/characters/{id}/levelup`
- `static/levelup.js` / `levelup.css` / `levelup.html`
- Migration `a1b2c3d4e5f6` — `character_spells.always_prepared`, `character_choices.level`, `characters.hp_roll_log`

**Bard/Ranger are prepared casters in 2024 PHB** (not known-spell casters). Bard's prepared count comes from `BARD_PREPARED_BY_LEVEL` table (not `cha_mod + level`). Both auto-populate their full class spell list in `PREPARED_CASTERS` during level-up (like Cleric/Druid/Paladin).

**Step types covered:** `hp`, `subclass`, `asi`, `epic_boon`, `fighting_style`, `fighting_style_swap`, `expertise`, `cantrips_new`, `spells_new`, `wizard_spellbook`, `spell_swap`, `cantrip_swap`, `metamagic`, `invocations_new`, `invocation_swap`, `mystic_arcanum`, `feature_choice`

### Phase 3.5 — Rules Glossary (complete as of 2026-05-17)
Standalone `/glossary` page + inline click-to-popover tooltips on the character sheet.
- `GlossaryTerm` model + migration `b2c3d4e5f6a7`
- 94 terms across 6 categories: combat, condition, action, weapon_property, mastery, skill
- Sheet: `gloss(name)` → `<span class="gloss-term" data-slug="...">` + delegated click handler → parchment popover (position: fixed, viewport coords only — no scrollX/Y). Condition chips and mastery tags both use this system (click/tap to open, tap outside to close).

### Phase 4 — Sheet Spellcasting Tracking (complete)
- `PATCH /api/characters/{id}/prepared-spells` — validates caster type + prepared max; sets `prepared=True/False` on spell rows
- `PATCH /api/characters/{id}/masteries/swap` — player-accessible one-at-a-time mastery swap (remove one, add one from proficient weapons); no rest gate (tracked with physical tokens)
- **Prepared casters:** Cleric `wis+level`, Druid `wis+level`, Paladin `cha+level//2`, Ranger `wis+level//2`, Wizard `int+level`, Bard (table lookup via `BARD_PREPARED_BY_LEVEL`)
- Sheet Spells tab has "✎ Prepare Spells" modal for prep casters; Stats tab has "⇄ Swap Mastery" modal
- `_CATEGORY_MAP` (weapon category → set of weapon names) lives at **module scope** in `export.py` and is imported by `characters.py` for proficiency validation

### Phase 4.5 — Conditions System (complete as of 2026-06-17)
DM-assigned conditions visible on character sheets and monster stat blocks.

**Data model:**
- `Character.conditions` — JSON column (list like `["Grappled", "Exhaustion:3"]`). Persists on character across sessions.
- `Combatant.conditions` — JSON column on combatant row. Monster-only; cleared when combatant removed.
- Migration `l8m9o0p1q2r3` (latest)

**API:**
- `PATCH /api/admin/combatants/{id}/conditions` — body `{conditions: ["Grappled", "Exhaustion:3"]}`. Routes to `Character.conditions` for PC combatants; `Combatant.conditions` for monsters. Validates against `VALID_CONDITIONS` set + `Exhaustion:1–6` pattern. Empty list stores NULL.
- `GET /api/characters/{id}/hp` — now also returns `conditions: []`
- `GET /api/characters/{id}/sheet-data` — includes `conditions`
- `GET /api/admin/combatants` — includes `conditions` in each entry

**15 conditions:** Blinded, Charmed, Deafened, Frightened, Grappled, Incapacitated, Invisible, Paralyzed, Petrified, Poisoned, Prone, Restrained, Stunned, Unconscious, + Exhaustion (levels 1–6 stored as `"Exhaustion:N"`)

**Speed reflection on sheet:**
- Grappled/Restrained/Paralyzed/Petrified/Stunned/Unconscious → `0 ft` (rubric red)
- Exhaustion 3–4 → halved (amber); Exhaustion 5–6 → `0 ft` (rubric red)
- Prone: shown in condition strip but no speed effect

**Sheet UI:** `.sh-condition-strip` renders between combat bar and tabs (hidden when empty). Each chip is a `.gloss-term` (click = popover). 15-second poll updates both HP and conditions. Speed cell has `id="sh-speed-cell"` for targeted DOM updates.

**Admin tracker:** Inline condition picker per combatant card (popover, `position: fixed`). Exhaustion handled via level buttons 1–6. Monster stat block modal shows read-only condition chips at top. DM-only; players see but cannot change conditions.

**Repair Schema** covers `conditions` columns for both tables.

## Playwright test environment (as of 2026-06-23)

**Stack:** Node v24.16.0 via nvm · `@playwright/test` 1.61.0 · Chromium headless

**Prerequisites (WSL2 specific):** Linux system libs extracted without sudo to `~/.local/usr/lib/x86_64-linux-gnu/` (libnspr4, libnss3, libasound2). Required because `playwright install-deps` needs sudo. Done once; persists.

**Running tests:**
```bash
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
export LD_LIBRARY_PATH="$HOME/.local/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
npx playwright test                  # headless, all tests
npx playwright test --ui             # visual test runner
npx playwright test tests/foo.spec.js  # single file
```

**Test auth bypass:** `GET /auth/test-login?email=...` sets a session without Google OAuth. Only active when `TEST_AUTH_ENABLED=true` (set by `playwright.config.js` webServer env). Controlled by `settings.test_auth_enabled` in `app/config.py`. **Never enable on Railway/production.**

**Config:** `playwright.config.js` — baseURL `localhost:8000`, auto-starts uvicorn via `~/.local/bin/uvicorn`, `reuseExistingServer: true` in dev.

**Test files:** `tests/smoke.spec.js` — 3 passing smoke tests (server reachable, test-login → portal, portal renders).

**Shared login helper pattern:**
```js
async function login(page, email = 'zachpoguephil@gmail.com') {
  await page.goto(`/auth/test-login?email=${encodeURIComponent(email)}`);
  await page.waitForURL('/portal');
}
```

## Known issues

- **End-to-end testing not done for all 12 classes at all levels** — spot-tested; full matrix still needed
- **College of Lore "Magical Discoveries" (L6)** — player picks 2 spells from Cleric/Druid/Wizard lists; not yet a level-up wizard step (noted in `levelup_rules.py` comments as a Phase 3.6 gap)
- **PDF export** — `app/templates/character_sheet.html` exists but visual QA not done. PDF button removed from player side; admin still has export.

## Architecture notes

- **All theming** via CSS variables in `static/style.css` `:root {}`. Dark surfaces use leather variants; text on dark must use `--light`, `--light-dim`, `--gold`, or `--gold-bright`. `--gold-deep` (#6b4a18) is too dark for leather backgrounds — use only on parchment panels.
- **Parchment panels** (`.sh-section`, `.tome`, `.card`, `.modal-box`) use light parchment gradients. Dark ink (`--ink`, `--ink-soft`, `--ink-faded`) is correct here.
- **Glossary tooltip system** — `gloss(name)` / `glossifyDescription(text)` wrap text in `.gloss-term[data-slug]`; delegated click handler calls `_showGlossPopover(slug, el)`. Popover is `position: fixed` — use `getBoundingClientRect()` only, never add `scrollX`/`scrollY`. Condition chips and mastery tags both use this.
- **`_CATEGORY_MAP`** (weapon category → weapon name set) is module-scope in `export.py` and imported by `characters.py` (`from ..services.export import _CATEGORY_MAP`).
- **`BARD_PREPARED_BY_LEVEL`** in `levelup_rules.py` — exported and used by both `export.py` and `characters.py` for Bard's prepared-spell max (fixed table, not formula).
- **`VALID_CONDITIONS`** set in `app/routers/admin.py` — 14 binary conditions; Exhaustion handled separately as `"Exhaustion:N"`.
- **`Character.conditions`** JSON — persists across sessions; `Combatant.conditions` JSON — monster-scoped, lost on removal. Both default NULL (not `[]`); read with `char.conditions or []`.
- **HP poll** — `GET /api/characters/{id}/hp` returns `{hp_current, hp_max, conditions}`. `pollHp()` in `sheet.js` handles both HP and condition updates; updates condition strip and speed cell in-place without full re-render.
- **Migration rule:** always use `op.execute(text(...))` for raw SQL — never `bind.execute()`. PostgreSQL: `ADD COLUMN IF NOT EXISTS`. SQLite: inspect columns first via `sa_inspect(bind).get_columns(table)`.
- **Repair Schema button** (admin Import tab) covers all columns through migration `l8m9o0p1q2r3`. Run after Railway deploys that skip migrations.
- **`stat_roll_locked`** prevents re-rolling; DM unlocks via `POST /api/admin/characters/{id}/unlock-stats`.
- **`physical_locked`** locks height/weight/deity; player locks, DM unlocks.
- **`CharacterSpell.source`** — "class" | "species" | "subclass" | "arcanum". Species spells preserved across spell saves. Always-prepared subclass/arcanum spells added by level-up wizard.
- **`CharacterChoice.level`** — all level-up choices stored with `feature_key="lvlup:{level}:{step_id}"`.

## Project structure

```
app/
  main.py          — FastAPI app + lifespan seeder
  config.py        — pydantic-settings (.env); test_auth_enabled flag
  database.py      — SQLAlchemy engine + session
  models/
    content.py     — Species, DnDClass, Subclass, Background, Feat, Spell, Equipment, Monster, GlossaryTerm
    character.py   — Character + all join tables (CharacterSpell, WeaponMasteryUnlock, Combatant, …)
  dependencies.py  — require_user / require_admin FastAPI deps
  routers/
    content.py     — GET endpoints for content (public)
    characters.py  — Wizard steps, sheet-data, HP, prepared-spells, masteries/swap, levelup (require_user)
    admin.py       — DM roster, codex CRUD, combatants, conditions, seed trigger (require_admin)
    auth.py        — Google OAuth login/callback/logout/me + /test-login bypass
  services/
    seeder.py      — Markdown → DB (regex parser)
    export.py      — Character → JSON dict; _CATEGORY_MAP at module scope
    levelup_rules.py — Pure rules engine; exports BARD_PREPARED_BY_LEVEL, VALID_CONDITIONS, etc.
    pdf.py         — WeasyPrint renderer
  templates/
    character_sheet.html
static/
  index.html / script.js        — Player wizard (10 steps)
  portal.html / portal.js       — Player character roster
  sheet.html / sheet.js / sheet.css — Live character sheet (4-tab)
  levelup.html / levelup.js / levelup.css — Level-up wizard
  glossary.html / glossary.js / glossary.css — Rules Glossary page
  admin.html / admin.js         — DM admin panel (roster, codex, combat/status tracker, import)
  style.css                     — Design system (CSS variables, shared components)
  lore.html / lore.js / lore.css — Lore Library page
reference_claude/               — 2024 PHB markdown (authoritative source)
alembic/versions/               — Migrations (latest: l8m9o0p1q2r3_add_conditions)
tests/                          — Playwright test specs
playwright.config.js            — Playwright config (Chromium, auto-start uvicorn)
package.json                    — npm dev deps (@playwright/test)
docs/superpowers/
  specs/                        — Design specs from brainstorming sessions
  plans/                        — Implementation plans
```

## Bugs fixed (cumulative)

- `skill_options` was always empty — fixed with direct regex in `_parse_class_file`.
- Bard "choose any 3" skills — second regex branch added.
- Tool choice dropdown always showed Artisan's Tools — fixed.
- Fighting style / divine order options now show inline descriptions.
- Species display "Forest Gnome Gnome" — fixed to `species_lineage || species_name` throughout.
- Parent lineage trait was showing instead of selected lineage's traits — export filters parent.
- Species cantrips were re-selectable as class cantrips — class spell picker filters owned spell IDs.
- `save_spells` was wiping species spells — now only deletes rows where `source != "species"`.
- Gold stored as custom equipment row — admin "Convert Gold" button moves to `currency.gp`.
- Spell stats empty on Railway from old seed — seeder refreshes rows missing those fields.
- Railway missing columns — admin "Repair Schema" button applies all via dialect-aware ALTER TABLE.
- `combatants` table missing monster columns on Railway — fixed in migration `h4i5j6k7l8m9`.
- Admin HP endpoint accepted query params but tracker sent JSON body — fixed with `AdminHpIn` model.
- Fresh Railway DB failed on startup — fixed: `create_all` first, then stamp or `upgrade head`.
- `.sh-combat-label` / `.lore-nav-category` used `--gold-deep` on dark leather → near-invisible — changed to `--gold`.
- `.gloss-cat-count` used `--ink-faded` on dark leather sidebar → changed to `--light-dim`.
- `.wizard-step-pip.done .pip-label` used `--gold-deep` on leather body (darker than default!) → changed to `--gold`.
- `.spell-badge--always-prep` / `.modal-spell-always` used `#8a8040` (3:1 contrast on parchment) → changed to `#4a4510`.
- `openMonsterModal` looked up combatant by `monster_id`, always returning first instance when two of same monster are in combat — fixed to use `combatant_id` when called from tracker card.
- `removeCondition` left condition picker open (stopPropagation swallowed the once-listener) — added `closeConditionPicker()` call.
- Exhaustion label inconsistency ("Exhausted N" in admin vs "Exhaustion N" in sheet) — standardised to "Exhaustion N".
