# CLAUDE.md — Character Generator

## Running locally

```bash
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

On first start the server auto-seeds from `reference/`. If you need to reseed, delete `campaign.db` and restart.

## Current status (as of 2026-05-08)

**Phase 1 is functionally complete.** The full 10-step wizard runs end-to-end:

1. Identity (player name + character name)
2. Species selection
3. Background selection (with tool proficiency choice where needed)
4. Class selection
5. Stats — roll 3 sets (4d6 drop lowest), drag tokens onto ability cells, assign background ASI (+2/+1 or +1/+1/+1)
6. Class features (fighting style, divine order, weapon mastery choices, etc.)
7. Skills + languages
8. Equipment (structured choice pickers for instrument/gaming set/etc.)
9. Spells (cantrips + level 1; skipped for non-casters)
10. Bio (alignment, backstory) → complete

JSON export and WeasyPrint PDF export are wired up. Admin panel has roster management, codex CRUD, grimoire, JSON import, and seed trigger.

## Known issues / next steps

- **End-to-end testing not yet done.** The wizard has not been tested all the way through for every class. Do a full run before calling Phase 1 done.
- **PDF export** — WeasyPrint renders a character sheet via `app/templates/character_sheet.html`. Visual QA still needed.
- **Bard skill list** — Bard uses "choose any 3" in markdown, so the wizard falls back to the full 18-skill list (correct behavior, implemented).
- **Phase 2** work (subclasses, level-up flow, spell slot tracking) has not started. Stop for review before beginning.

## Bugs fixed (cumulative)

- `skill_options` was always empty for all classes — `_field()` helper couldn't match `**Skill Proficiencies (choose N):**` due to `(choose N)` between the field name and closing `**`. Fixed with a direct regex in `_parse_class_file` in `app/services/seeder.py`.
- Bard-style `**Skill Proficiencies:** Choose any 3` needed a second regex branch.
- `save_species` in `app/routers/characters.py` used a broken `__import__` hack — fixed by adding `Species` to the top-level import.
- Tool choice dropdown (Step 3) always showed Artisan's Tools regardless of background — `k.split(" ")[3]` was always `"of"`, so `find()` always matched the first key. Fixed with a direct `TOOL_OPTIONS[bg.tool_proficiency]` lookup (`static/script.js`).
- Added inline descriptions to fighting style options and divine order options (Step 6) using a `FIGHTING_STYLE_DESCRIPTIONS` lookup table in `static/script.js`. Each weapon in the mastery checklist now shows its mastery property name as a tag with a hover tooltip.

## Phase 1.5 — Google Auth + Web Hosting (auth complete, hosting pending)

Auth is implemented. Hosting (Railway) still needs to be done. Google Cloud Console setup is required before auth will work end-to-end (see setup steps below).

### Status
- [x] Dependencies added (`authlib`, `httpx`, `itsdangerous`)
- [x] `app/config.py` — new settings fields
- [x] `app/routers/auth.py` — login, callback, logout, me endpoints
- [x] `app/dependencies.py` — `require_user`, `require_admin`
- [x] `app/main.py` — `SessionMiddleware` + auth router wired
- [x] `app/models/character.py` — `owner_email` column added
- [x] Alembic migration applied (`b4b8fca5bcf5`)
- [x] All `/api/characters` routes gated by `require_user`, scoped to owner
- [x] All `/api/admin` routes gated by `require_admin` (router-level dependency)
- [x] Frontend: `boot()` checks `/auth/me`, redirects to `/auth/login` if 401
- [x] Frontend: user badge (name + Sign out) shown in both wizard and admin headers
- [x] Frontend: Step 1 player name pre-filled from Google display name
- [ ] Google Cloud Console credentials entered in `.env`
- [ ] Railway deployment

### Goal
Lock the wizard behind Google OAuth so only invited players can create characters. The DM (you) can access the admin panel. Players see only their own characters. No custom password system — Google handles credentials.

### Recommended hosting: Railway
- Supports PostgreSQL natively (just add the plugin — connection string lands in `DATABASE_URL` env var automatically).
- Deploys from GitHub push. No Dockerfile needed for a basic FastAPI app.
- Free tier is enough for a home campaign group.
- WeasyPrint requires system fonts — add a `nixpacks.toml` or `Dockerfile` to install `libpango` / `fonts-liberation` if PDF export is needed on Railway. Alternatively defer PDF to local-only for now.

### Auth approach: Google OAuth via Authlib + server-side sessions

**Do not use JWT tokens stored in localStorage.** Use server-side sessions (cookie-backed) so the admin check stays on the server.

Dependencies to add:
```
authlib
httpx
itsdangerous   # for SessionMiddleware signing
```

#### Implementation steps

1. **Google Cloud Console** — create an OAuth 2.0 client ID (Web application). Add the deployed Railway URL + `http://localhost:8000` as authorized redirect URIs. Copy client ID and secret to `.env`.

2. **`.env` additions**
   ```
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
   SESSION_SECRET=<random 32-char string>
   ALLOWED_EMAILS=player1@gmail.com,player2@gmail.com,dm@gmail.com
   ADMIN_EMAIL=dm@gmail.com
   ```

3. **`app/config.py`** — add the new fields to `Settings`:
   ```python
   google_client_id: str = ""
   google_client_secret: str = ""
   session_secret: str = "dev-secret"
   allowed_emails: str = ""   # comma-separated
   admin_email: str = ""
   ```

4. **`app/main.py`** — add `SessionMiddleware` and register Authlib OAuth client:
   ```python
   from starlette.middleware.sessions import SessionMiddleware
   app.add_middleware(SessionMiddleware, secret_key=settings.session_secret)
   ```

5. **New router: `app/routers/auth.py`**
   - `GET /auth/login` — redirect to Google
   - `GET /auth/callback` — exchange code, verify email in ALLOWED_EMAILS, store `{"email": ..., "name": ...}` in `request.session["user"]`, redirect to `/`
   - `GET /auth/logout` — clear session, redirect to `/`
   - `GET /auth/me` — return current user JSON (used by the frontend to show player name)

6. **Auth dependency** — add to `app/dependencies.py` (new file):
   ```python
   def require_user(request: Request):
       user = request.session.get("user")
       if not user:
           raise HTTPException(302, headers={"Location": "/auth/login"})
       return user

   def require_admin(request: Request):
       user = require_user(request)
       if user["email"] != settings.admin_email:
           raise HTTPException(403)
       return user
   ```

7. **Wire up dependencies**
   - All `/api/characters` routes: add `user = Depends(require_user)`. Scope character creation/reads to `user["email"]` — add `owner_email` column to `Character` via Alembic migration.
   - All `/api/admin` routes: add `user = Depends(require_admin)`.
   - Content routes (`/api/content/*`) stay public — needed before login for the wizard to render.

8. **Frontend changes (`static/index.html` / `static/script.js`)**
   - On load, call `GET /auth/me`. If 401, redirect to `/auth/login`.
   - Show logged-in player name in the header.
   - Add a logout link.
   - Pre-fill Step 1 "Player Name" from the Google display name (still editable).

9. **Alembic migration** — add `owner_email VARCHAR` to the `characters` table. Existing rows get `NULL`; that's fine for dev data.

### Hosting deployment checklist (Railway)
- [ ] Push repo to GitHub (if not already there)
- [ ] Create Railway project, add PostgreSQL plugin
- [ ] Set all env vars in Railway dashboard (copy from `.env`, never commit secrets)
- [ ] Add `nixpacks.toml` if WeasyPrint PDF is needed:
  ```toml
  [phases.setup]
  nixPkgs = ["pango", "libffi", "fontconfig", "fonts-liberation"]
  ```
- [ ] Update Google OAuth redirect URI to the Railway domain
- [ ] Run `alembic upgrade head` via Railway's one-off command runner after first deploy
- [ ] Smoke-test: login, create a character, export JSON

## Architecture notes

- All theming is via CSS variables in `static/style.css` `:root {}` — easy to retheme without touching structure.
- Equipment options are JSON arrays of `{label, items[], gold?}` stored on `DnDClass.equipment_options` and `Background.equipment_options`.
- `stat_roll_locked` on `Character` prevents re-rolling after submission; DM unlocks via `POST /api/admin/characters/{id}/unlock-stats`.
- Seeder is idempotent — pre-loads existing names into sets, only inserts new records.
- Alembic was stamped (`alembic stamp head`) after `create_all` on the initial schema.

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
  admin.html / admin.js    — DM admin panel
  style.css                — Design system (CSS variables)
reference/                 — 2024 PHB markdown (authoritative)
alembic/                   — Migrations
```
