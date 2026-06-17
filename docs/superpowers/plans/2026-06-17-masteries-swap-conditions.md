# Masteries Swap + Conditions System — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a player-accessible "Swap Mastery" button to the character sheet and a DM-controlled condition-assignment system that propagates to character sheets and the monster stat block modal.

**Architecture:** Conditions are stored as JSON arrays on `Character` (persistent) and `Combatant` (session-scoped for monsters). The DM sets conditions via `PATCH /api/admin/combatants/{id}/conditions`; for character combatants this writes through to `Character.conditions`. The character sheet reads conditions on its existing 15-second HP poll. Mastery swaps go through a new player-facing endpoint `PATCH /api/characters/{id}/masteries/swap`.

**Tech Stack:** FastAPI + SQLAlchemy (backend), vanilla JS + CSS custom properties (frontend), Alembic (migration), SQLite/PostgreSQL dual-dialect.

---

## File Map

| File | Action | Purpose |
|---|---|---|
| `alembic/versions/l8m9o0p1q2r3_add_conditions.py` | **Create** | Migration: add `conditions JSON` to `characters` and `combatants` |
| `app/models/character.py` | **Modify** | Add `conditions` column to `Character` and `Combatant` |
| `app/routers/characters.py` | **Modify** | Add `MasterySwapIn` + `swap_mastery` endpoint; extend `get_hp` to return conditions |
| `app/services/export.py` | **Modify** | Add `conditions` to `character_to_sheet_dict` response |
| `app/routers/admin.py` | **Modify** | Add `ConditionsIn` + `set_combatant_conditions` endpoint; add conditions to `list_combatants`; update Repair Schema |
| `static/sheet.css` | **Modify** | Add condition strip and chip styles |
| `static/sheet.js` | **Modify** | Add `renderConditionStrip`, update speed cell, update `pollHp`, add swap mastery modal |
| `static/style.css` | **Modify** | Add condition chip styles used by admin tracker |
| `static/admin.js` | **Modify** | Add condition chips + picker to combat cards; add conditions to monster modal |

---

## Task 1: Migration and Model Columns

**Files:**
- Create: `alembic/versions/l8m9o0p1q2r3_add_conditions.py`
- Modify: `app/models/character.py`

- [ ] **Step 1: Create the migration file**

```python
# alembic/versions/l8m9o0p1q2r3_add_conditions.py
"""add conditions column to characters and combatants

Revision ID: l8m9o0p1q2r3
Revises: k7l8m9o0p1q2
Create Date: 2026-06-17
"""
from alembic import op
from sqlalchemy import text, inspect as sa_inspect

revision = 'l8m9o0p1q2r3'
down_revision = 'k7l8m9o0p1q2'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.dialect.name

    cols = [
        ("characters", "conditions", "JSON"),
        ("combatants",  "conditions", "JSON"),
    ]
    for table, col, ddl in cols:
        if dialect == "postgresql":
            op.execute(text(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {col} {ddl}"))
        else:
            existing = {c["name"] for c in sa_inspect(bind).get_columns(table)}
            if col not in existing:
                op.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}"))


def downgrade():
    pass
```

- [ ] **Step 2: Add `conditions` to `Character` and `Combatant` models in `app/models/character.py`**

In the `Character` class (around line 35, after `hp_roll_log`), add:
```python
conditions = Column(JSON, nullable=True)  # e.g. ["Grappled", "Exhaustion:3"]
```

In the `Combatant` class (around line 190, after `added_at`), add:
```python
conditions = Column(JSON, nullable=True)  # monster-only; cleared when combatant is removed
```

- [ ] **Step 3: Run the migration locally to verify it applies cleanly**

```bash
source venv/bin/activate 2>/dev/null || true
alembic upgrade head
```

Expected: no error, migration applies. If `venv` not found the app likely uses system Python; check `which uvicorn`.

- [ ] **Step 4: Commit**

```bash
git add alembic/versions/l8m9o0p1q2r3_add_conditions.py app/models/character.py
git commit -m "feat: add conditions JSON column to characters and combatants"
```

---

## Task 2: Masteries Swap Endpoint

**Files:**
- Modify: `app/routers/characters.py`

The existing admin endpoint (`PATCH /api/admin/characters/{id}/masteries`) replaces all masteries wholesale. This new player-facing endpoint swaps exactly one — removes one weapon, adds another — in a single transaction.

- [ ] **Step 1: Add the Pydantic model and endpoint to `app/routers/characters.py`**

After the `PreparedSpellsIn` class (around line 753), add:

```python
class MasterySwapIn(BaseModel):
    remove: str
    add: str
```

After `update_prepared_spells` (around line 808), add:

```python
@router.patch("/{char_id}/masteries/swap")
def swap_mastery(char_id: int, data: MasterySwapIn, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)

    remove_name = (data.remove or "").strip()
    add_name = (data.add or "").strip()
    if not remove_name or not add_name:
        raise HTTPException(400, "Both 'remove' and 'add' weapon names are required")
    if remove_name == add_name:
        raise HTTPException(400, "remove and add must be different weapons")

    current = {wu.weapon_name: wu for wu in char.weapon_mastery_unlocks}
    if remove_name not in current:
        raise HTTPException(400, f"'{remove_name}' is not a current mastery")

    already_mastered = {wu.weapon_name for wu in char.weapon_mastery_unlocks}
    if add_name in already_mastered:
        raise HTTPException(400, f"'{add_name}' is already mastered")

    # Verify add_name is a weapon the character is proficient with
    from ..models.content import Equipment as EquipmentModel
    from ..services.export import _CATEGORY_MAP  # reuse the existing set
    prof_raw = [wp.proficiency_type for wp in char.weapon_proficiencies]
    prof_set: set[str] = set()
    for pt in prof_raw:
        if pt in _CATEGORY_MAP:
            prof_set |= _CATEGORY_MAP[pt]
        else:
            prof_set.add(pt)

    weapon_exists = db.query(EquipmentModel).filter(
        EquipmentModel.name == add_name,
        EquipmentModel.item_type == "weapon"
    ).first()
    if not weapon_exists:
        raise HTTPException(400, f"'{add_name}' is not a known weapon")
    if add_name not in prof_set:
        raise HTTPException(400, f"Not proficient with '{add_name}'")

    # Atomic swap
    db.delete(current[remove_name])
    new_mastery = WeaponMasteryUnlock(character_id=char.id, weapon_name=add_name)
    db.add(new_mastery)
    db.commit()
    return {"ok": True, "removed": remove_name, "added": add_name}
```

The `_CATEGORY_MAP` is a module-level dict in `export.py`. Export it by moving it to module scope (it's currently inside `character_to_sheet_dict`). See Step 2.

- [ ] **Step 2: Expose `_CATEGORY_MAP` at module scope in `app/services/export.py`**

Currently `_SIMPLE_MELEE`, `_SIMPLE_RANGED`, `_MARTIAL_MELEE`, `_MARTIAL_RANGED`, `_ALL`, and `_CATEGORY_MAP` are defined inside `character_to_sheet_dict` (around line 431). Move them to module scope — before the function definitions, after the imports.

Cut the block starting with `_SIMPLE_MELEE = {` through `_CATEGORY_MAP = {` and paste it above `def character_to_dict`. Then in `character_to_sheet_dict` and `_calc_attacks`, remove the local definitions and use the module-level names directly. Also update `_calc_attacks` (line 159) which has its own inline `weapon_prof_set` computation — it already receives `weapon_prof_set` as a parameter so no change needed there.

- [ ] **Step 3: Verify the import in `characters.py` resolves**

```bash
python3 -c "from app.services.export import _CATEGORY_MAP; print(len(_CATEGORY_MAP), 'entries')"
```

Expected output: `8 entries` (the 8 category-name keys).

- [ ] **Step 4: Commit**

```bash
git add app/routers/characters.py app/services/export.py
git commit -m "feat: add PATCH /api/characters/{id}/masteries/swap player endpoint"
```

---

## Task 3: Conditions Backend — Export, HP Endpoint, Admin API, Repair Schema

**Files:**
- Modify: `app/services/export.py`
- Modify: `app/routers/characters.py`
- Modify: `app/routers/admin.py`

- [ ] **Step 1: Add `conditions` to `character_to_sheet_dict` in `app/services/export.py`**

In the return dict at the end of `character_to_sheet_dict` (around line 504), add one line after `"is_complete": char.is_complete,`:

```python
"conditions": char.conditions or [],
```

- [ ] **Step 2: Extend `GET /api/characters/{id}/hp` to return conditions**

In `app/routers/characters.py`, find `get_hp` (around line 581):

```python
@router.get("/{char_id}/hp")
def get_hp(char_id: int, db: Session = Depends(get_db), user: dict = Depends(require_user)):
    char = _get_char(char_id, db)
    _check_owner_or_admin(char, user)
    return {"hp_current": char.hp_current, "hp_max": char.hp_max}
```

Change the return to:

```python
    return {
        "hp_current": char.hp_current,
        "hp_max": char.hp_max,
        "conditions": char.conditions or [],
    }
```

- [ ] **Step 3: Add `ConditionsIn` model and `set_combatant_conditions` endpoint in `app/routers/admin.py`**

After the `CombatantHpIn` class (find it near the combatant endpoint block), add:

```python
VALID_CONDITIONS = {
    "Blinded", "Charmed", "Deafened", "Frightened", "Grappled",
    "Incapacitated", "Invisible", "Paralyzed", "Petrified", "Poisoned",
    "Prone", "Restrained", "Stunned", "Unconscious",
}

class ConditionsIn(BaseModel):
    conditions: list[str]
```

After the `set_combatant_hp` endpoint (around line 955), add:

```python
@router.patch("/combatants/{combatant_id}/conditions")
def set_combatant_conditions(combatant_id: int, data: ConditionsIn, db: Session = Depends(get_db)):
    c = db.get(Combatant, combatant_id)
    if not c:
        raise HTTPException(404)

    validated: list[str] = []
    for cond in data.conditions:
        if cond in VALID_CONDITIONS:
            validated.append(cond)
        elif cond.startswith("Exhaustion:"):
            level_str = cond.split(":", 1)[1]
            if level_str.isdigit() and 1 <= int(level_str) <= 6:
                validated.append(cond)
            else:
                raise HTTPException(400, f"Invalid Exhaustion level in '{cond}'; must be Exhaustion:1 through Exhaustion:6")
        else:
            raise HTTPException(400, f"Unknown condition: '{cond}'")

    if c.character_id:
        char = db.get(Character, c.character_id)
        if not char:
            raise HTTPException(404, "Character not found")
        char.conditions = validated or None
    else:
        c.conditions = validated or None

    db.commit()
    return {"ok": True, "conditions": validated}
```

- [ ] **Step 4: Add `conditions` to `list_combatants` response in `app/routers/admin.py`**

In the `list_combatants` function (around line 872), add `"conditions"` to both the character and monster result dicts:

Character branch (around line 891), add inside the dict:
```python
"conditions": char.conditions or [],
```

Monster branch (around line 907), add inside the dict:
```python
"conditions": row.conditions or [],
```

- [ ] **Step 5: Add conditions columns to Repair Schema in `app/routers/admin.py`**

In `repair_schema` (around line 1011, after the equipment columns), add:

```python
add_col("characters", "conditions", "JSON")
add_col("combatants",  "conditions", "JSON")
```

- [ ] **Step 6: Commit**

```bash
git add app/services/export.py app/routers/characters.py app/routers/admin.py
git commit -m "feat: conditions API — export, hp endpoint, admin PATCH, repair schema"
```

---

## Task 4: Condition Strip CSS

**Files:**
- Modify: `static/sheet.css`
- Modify: `static/style.css`

The strip lives on the character sheet (sheet.css). The chip style is also needed in the admin tracker (style.css so it's globally available).

- [ ] **Step 1: Add condition strip and chip styles to `static/sheet.css`**

Append after the last rule in sheet.css:

```css
/* ─────────────────────────────────────────────────────────────────
   CONDITION STRIP — between combat bar and tabs
   ───────────────────────────────────────────────────────────────── */
.sh-condition-strip {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  align-items: center;
  max-width: 960px;
  margin: 0 auto;
  padding: 8px 20px;
  background: rgba(0,0,0,0.12);
  border-bottom: 1px solid rgba(168,120,43,0.18);
}

.sh-condition-label {
  font-family: var(--font-display);
  font-size: 0.68rem;
  letter-spacing: 0.1em;
  text-transform: uppercase;
  color: var(--light-dim);
  flex-shrink: 0;
  margin-right: 4px;
}

.sh-cond-chip {
  font-family: var(--font-display);
  font-size: 0.72rem;
  letter-spacing: 0.06em;
  padding: 2px 8px;
  border-radius: 10px;
  border: 1px solid currentColor;
  white-space: nowrap;
  cursor: help;
}
.sh-cond-chip--red    { color: var(--rubric); background: rgba(139,26,26,0.12); }
.sh-cond-chip--amber  { color: #8b4a00; background: rgba(139,74,0,0.1); }
.sh-cond-chip--gold   { color: var(--gold); background: rgba(168,120,43,0.1); }

/* Speed cell override when condition zeroes it */
.sh-combat-big.sh-speed-zero   { color: var(--rubric); }
.sh-combat-big.sh-speed-halved { color: #8b4a00; }
```

- [ ] **Step 2: Add condition chip styles to `static/style.css`** (used by admin tracker)

Append after the `.combat-monster-tag` block (around line 1569):

```css
/* ─────────────────────────────────────────────────────────────────
   CONDITION CHIPS — admin status tracker cards
   ───────────────────────────────────────────────────────────────── */
.cond-chips-row {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin: 6px 0 2px;
  min-height: 0;
}

.cond-chip {
  font-family: var(--font-display);
  font-size: 0.68rem;
  letter-spacing: 0.05em;
  padding: 2px 7px;
  border-radius: 10px;
  border: 1px solid rgba(139,26,26,0.4);
  background: rgba(139,26,26,0.15);
  color: #e08080;
  white-space: nowrap;
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.cond-chip-x {
  cursor: pointer;
  opacity: 0.7;
  font-size: 0.8rem;
  line-height: 1;
}
.cond-chip-x:hover { opacity: 1; }

/* Condition picker popover */
.cond-picker {
  position: absolute;
  z-index: 500;
  background: linear-gradient(170deg, var(--parchment-bright) 0%, var(--parchment) 100%);
  border: 1px solid rgba(168,120,43,0.4);
  border-radius: var(--radius-md);
  padding: 8px 0;
  min-width: 180px;
  max-height: 320px;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0,0,0,0.6);
}

.cond-picker-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 14px;
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: var(--ink);
  cursor: pointer;
  transition: background 0.1s;
  border-bottom: 1px solid rgba(168,120,43,0.1);
}
.cond-picker-item:last-child { border-bottom: none; }
.cond-picker-item:hover { background: rgba(168,120,43,0.08); }
.cond-picker-item.active { font-weight: 700; color: var(--rubric); }
.cond-picker-check { font-size: 0.8rem; width: 14px; text-align: center; color: var(--rubric); }

.cond-exhaustion-picker {
  display: flex;
  gap: 4px;
  padding: 6px 14px 8px;
  flex-wrap: wrap;
}

.cond-exhaustion-btn {
  font-family: var(--font-display);
  font-size: 0.72rem;
  padding: 3px 8px;
  border: 1px solid rgba(139,74,0,0.4);
  background: rgba(139,74,0,0.08);
  color: #8b4a00;
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: background 0.1s;
  min-height: unset;
  box-shadow: none;
  text-transform: none;
  letter-spacing: 0;
}
.cond-exhaustion-btn:hover { background: rgba(139,74,0,0.18); }
.cond-exhaustion-btn.active { background: rgba(139,74,0,0.3); font-weight: 700; }
```

- [ ] **Step 3: Commit**

```bash
git add static/sheet.css static/style.css
git commit -m "feat: add condition strip and chip CSS for sheet and admin tracker"
```

---

## Task 5: Condition Strip and Speed Reflection in `sheet.js`

**Files:**
- Modify: `static/sheet.js`

- [ ] **Step 1: Add `CONDITION_COLORS` and `renderConditionStrip` near the top of sheet.js** (after the existing `ORDINAL` constant, around line 20)

```js
const CONDITION_COLORS = {
  Incapacitated: "red", Paralyzed: "red", Petrified: "red",
  Stunned: "red", Unconscious: "red",
  Exhaustion: "amber", Frightened: "amber", Poisoned: "amber",
  Blinded: "gold", Charmed: "gold", Deafened: "gold",
  Grappled: "gold", Invisible: "gold", Prone: "gold", Restrained: "gold",
};

function conditionColor(name) {
  if (name.startsWith("Exhaustion")) return "amber";
  return CONDITION_COLORS[name] || "gold";
}

function conditionLabel(name) {
  if (name.startsWith("Exhaustion:")) return `Exhaustion ${name.split(":")[1]}`;
  return name;
}

function renderConditionStrip(conditions) {
  if (!conditions || !conditions.length) return "";
  const chips = conditions.map(c => {
    const cls = `sh-cond-chip sh-cond-chip--${conditionColor(c)}`;
    const label = conditionLabel(c);
    const glossEntry = _glossaryMap ? _glossaryMap[c.replace(/:\d+$/, "")] : null;
    const tip = glossEntry ? `title="${glossEntry.short_description.replace(/"/g, '&quot;')}"` : "";
    return `<span class="${cls}" ${tip}>${label}</span>`;
  }).join("");
  return `<div class="sh-condition-strip">
    <span class="sh-condition-label">Conditions</span>${chips}
  </div>`;
}
```

The `_glossaryMap` is the glossary loaded by the existing `loadGlossary()` function in sheet.js — it stores terms keyed by slug/term. Check the current variable name; if it's different, use whatever name the existing code uses. (The existing glossary loading uses `glossaryTerms` as the array and a local `Map` for lookup — see the `gloss()` function for the variable name in use.)

- [ ] **Step 2: Verify the glossary variable name used in `sheet.js`**

```bash
grep -n "glossary\|_glossary\|glossTerms\|loadGloss" static/sheet.js | head -15
```

Use the actual variable name storing glossary terms by `term` in `renderConditionStrip` above. The lookup should be `glossaryTermsByName[name]` or equivalent — check and correct the variable reference.

- [ ] **Step 3: Add `computeSpeedDisplay` helper in `sheet.js`** (after `renderConditionStrip`)

```js
function computeSpeedDisplay(baseSpeed, conditions) {
  if (!conditions || !conditions.length) return { text: `${baseSpeed ?? "—"} ft`, cls: "" };
  const conds = new Set(conditions.map(c => c.startsWith("Exhaustion:") ? c : c));
  const speedZero = ["Grappled","Restrained","Paralyzed","Petrified","Stunned","Unconscious"]
    .some(c => conds.has(c));
  const exhaustLevel = (() => {
    for (const c of conds) {
      if (c.startsWith("Exhaustion:")) return parseInt(c.split(":")[1], 10);
    }
    return 0;
  })();
  if (speedZero || exhaustLevel >= 5) return { text: "0 ft", cls: "sh-speed-zero" };
  if (exhaustLevel >= 3) {
    const half = Math.floor((baseSpeed ?? 30) / 2);
    return { text: `${half} ft`, cls: "sh-speed-halved" };
  }
  return { text: `${baseSpeed ?? "—"} ft`, cls: "" };
}
```

- [ ] **Step 4: Update `render()` in `sheet.js` to inject condition strip and condition-aware speed**

In the `render()` function, find the template string building `document.getElementById("sheet-root").innerHTML`. Make two changes:

**a) Replace the static speed cell** (around line 307–310):
```js
      <div class="sh-combat-cell">
        <div class="sh-combat-label">Speed</div>
        <div class="sh-combat-big">${c.speed ?? "—"} ft</div>
      </div>
```
Replace with:
```js
      <div class="sh-combat-cell" id="sh-speed-cell">
        <div class="sh-combat-label">Speed</div>
        ${(() => { const sd = computeSpeedDisplay(c.speed, c.conditions); return `<div class="sh-combat-big ${sd.cls}">${sd.text}</div>`; })()}
      </div>
```

**b) Insert condition strip between combat bar and tabs** (after the closing `</div>` of `sh-combat-bar`, before `<div class="sh-tabs">`):
```js
    ${renderConditionStrip(c.conditions || [])}

    <div class="sh-tabs">
```

- [ ] **Step 5: Commit**

```bash
git add static/sheet.js
git commit -m "feat: condition strip and speed reflection on character sheet"
```

---

## Task 6: Update HP Poll to Carry Conditions

**Files:**
- Modify: `static/sheet.js`

The `pollHp` function currently only updates HP. Extend it to also refresh conditions and re-render the strip and speed cell.

- [ ] **Step 1: Replace `pollHp` in `sheet.js`** (around line 252)

Current code:
```js
async function pollHp() {
  try {
    const r = await api("GET", `/api/characters/${charId}/hp`);
    if (!r) return;
    if (r.hp_current === charData.hp_current && r.hp_max === charData.hp_max) return;
    charData.hp_current = r.hp_current;
    charData.hp_max = r.hp_max;
    const cell = document.getElementById("hp-cell");
    if (!cell) return;
    const label = cell.querySelector(".sh-combat-label").outerHTML;
    cell.innerHTML = label + renderHpWidget(charData);
  } catch (_) { /* ignore */ }
}
```

Replace with:
```js
async function pollHp() {
  try {
    const r = await api("GET", `/api/characters/${charId}/hp`);
    if (!r) return;
    const hpChanged = r.hp_current !== charData.hp_current || r.hp_max !== charData.hp_max;
    const condChanged = JSON.stringify(r.conditions || []) !== JSON.stringify(charData.conditions || []);
    if (!hpChanged && !condChanged) return;

    if (hpChanged) {
      charData.hp_current = r.hp_current;
      charData.hp_max = r.hp_max;
      const cell = document.getElementById("hp-cell");
      if (cell) {
        const label = cell.querySelector(".sh-combat-label").outerHTML;
        cell.innerHTML = label + renderHpWidget(charData);
      }
    }

    if (condChanged) {
      charData.conditions = r.conditions || [];
      // Refresh condition strip
      const existing = document.querySelector(".sh-condition-strip");
      const tabs = document.querySelector(".sh-tabs");
      if (tabs) {
        const newStrip = renderConditionStrip(charData.conditions);
        if (existing) existing.remove();
        if (newStrip) tabs.insertAdjacentHTML("beforebegin", newStrip);
      }
      // Refresh speed cell
      const speedCell = document.getElementById("sh-speed-cell");
      if (speedCell) {
        const sd = computeSpeedDisplay(charData.speed, charData.conditions);
        speedCell.querySelector(".sh-combat-big").className = `sh-combat-big ${sd.cls}`.trim();
        speedCell.querySelector(".sh-combat-big").textContent = sd.text;
      }
    }
  } catch (_) { /* ignore */ }
}
```

- [ ] **Step 2: Commit**

```bash
git add static/sheet.js
git commit -m "feat: poll conditions from hp endpoint and update strip + speed cell"
```

---

## Task 7: Mastery Swap Modal in `sheet.js`

**Files:**
- Modify: `static/sheet.js`

- [ ] **Step 1: Update `renderWeaponsSection` to add the swap button**

Find `renderWeaponsSection` (around line 568). After the closing `</div>` of the section title (inside the return template), add the button. The function currently returns:

```js
  return `<div class="sh-section">
    <h4 class="sh-section-title">Weapon Proficiencies &amp; Masteries</h4>
    ${catLine}
    <div class="sh-weapon-grid">${rows}</div>
  </div>`;
```

Change to:

```js
  const masteries = weapons.filter(w => w.mastery);
  const swapBtn = masteries.length
    ? `<button class="prep-edit-btn mt-sm" onclick="openSwapMasteryModal()" style="margin-top:10px">⇄ Swap Mastery</button>`
    : "";

  return `<div class="sh-section">
    <h4 class="sh-section-title">Weapon Proficiencies &amp; Masteries</h4>
    ${catLine}
    <div class="sh-weapon-grid">${rows}</div>
    ${swapBtn}
  </div>`;
```

- [ ] **Step 2: Add `openSwapMasteryModal`, `closeSwapMasteryModal`, and `executeSwapMastery` to `sheet.js`** (after `closePrepModal`, around line 1510)

```js
// ---------------------------------------------------------------------------
// Swap Mastery modal
// ---------------------------------------------------------------------------
function openSwapMasteryModal() {
  const c = charData;
  const weapons = c.weapons_display || [];
  const masteries = weapons.filter(w => w.mastery);
  const swappable = weapons.filter(w => w.proficient && !w.mastery);

  window._swapMasteryRemove = null;
  window._swapMasteryAdd = null;

  const removeRows = masteries.map(w => `
    <div class="modal-spell-row" id="swap-rem-${w.name.replace(/\s+/g,'-')}"
         onclick="selectSwapRemove(this, '${w.name.replace(/'/g, "\\'")}')">
      <span class="modal-spell-check-locked" id="swap-rem-check-${w.name.replace(/\s+/g,'-')}" style="visibility:hidden">✓</span>
      <span class="modal-spell-name">${w.name}</span>
      <span class="modal-spell-level">${w.mastery}</span>
    </div>`).join("") || `<p class="hint">No current masteries.</p>`;

  const addRows = swappable.length ? swappable.map(w => `
    <div class="modal-spell-row" id="swap-add-${w.name.replace(/\s+/g,'-')}"
         onclick="selectSwapAdd(this, '${w.name.replace(/'/g, "\\'")}')">
      <span class="modal-spell-check-locked" id="swap-add-check-${w.name.replace(/\s+/g,'-')}" style="visibility:hidden">✓</span>
      <span class="modal-spell-name">${w.name}</span>
    </div>`).join("") : `<p class="hint">No other proficient weapons available.</p>`;

  const overlay = document.createElement("div");
  overlay.id = "swap-mastery-overlay";
  overlay.className = "modal-overlay";
  overlay.innerHTML = `
    <div class="modal-box">
      <div class="modal-header">
        <h3>Swap Mastery</h3>
        <button class="modal-close-btn" onclick="closeSwapMasteryModal()">✕</button>
      </div>
      <div class="modal-body" style="display:grid;grid-template-columns:1fr 1fr;gap:16px">
        <div>
          <div class="modal-section-title">Remove (pick one)</div>
          ${removeRows}
        </div>
        <div>
          <div class="modal-section-title">Add (pick one)</div>
          ${addRows}
        </div>
      </div>
      <div class="modal-footer">
        <button class="prep-modal-cancel" onclick="closeSwapMasteryModal()">Cancel</button>
        <button class="prep-modal-save" id="swap-mastery-confirm" onclick="executeSwapMastery()" disabled>Swap</button>
      </div>
    </div>`;
  document.body.appendChild(overlay);
}

function selectSwapRemove(el, name) {
  document.querySelectorAll("[id^='swap-rem-']").forEach(r => {
    r.style.background = "";
    const chk = r.querySelector("[id^='swap-rem-check-']");
    if (chk) chk.style.visibility = "hidden";
  });
  el.style.background = "rgba(168,120,43,0.08)";
  const chk = el.querySelector("[id^='swap-rem-check-']");
  if (chk) chk.style.visibility = "visible";
  window._swapMasteryRemove = name;
  document.getElementById("swap-mastery-confirm").disabled =
    !(window._swapMasteryRemove && window._swapMasteryAdd);
}

function selectSwapAdd(el, name) {
  document.querySelectorAll("[id^='swap-add-']").forEach(r => {
    r.style.background = "";
    const chk = r.querySelector("[id^='swap-add-check-']");
    if (chk) chk.style.visibility = "hidden";
  });
  el.style.background = "rgba(168,120,43,0.08)";
  const chk = el.querySelector("[id^='swap-add-check-']");
  if (chk) chk.style.visibility = "visible";
  window._swapMasteryAdd = name;
  document.getElementById("swap-mastery-confirm").disabled =
    !(window._swapMasteryRemove && window._swapMasteryAdd);
}

function closeSwapMasteryModal() {
  const el = document.getElementById("swap-mastery-overlay");
  if (el) el.remove();
}

async function executeSwapMastery() {
  const remove = window._swapMasteryRemove;
  const add = window._swapMasteryAdd;
  if (!remove || !add) return;
  try {
    await api("PATCH", `/api/characters/${charId}/masteries/swap`, { remove, add });
    closeSwapMasteryModal();
    // Refresh sheet data
    const fresh = await api("GET", `/api/characters/${charId}/sheet-data`);
    if (fresh) {
      Object.assign(charData, fresh);
      const weaponSection = document.querySelector("#sh-tab-stats .sh-section:last-of-type");
      // Re-render the whole stats tab to update weapons section
      document.getElementById("sh-tab-stats").innerHTML =
        renderStatsTab(charData, charData.proficiency_bonus || 2, charData.attributes || {});
    }
  } catch(e) { toast(e.message || "Swap failed"); }
}
```

- [ ] **Step 3: Commit**

```bash
git add static/sheet.js
git commit -m "feat: swap mastery modal on character sheet"
```

---

## Task 8: Condition Chips and Picker in Admin Status Tracker

**Files:**
- Modify: `static/admin.js`

- [ ] **Step 1: Add the `ALL_CONDITIONS` list and `renderCondChips` helper near the top of the combat tracker section in `admin.js`** (just before `loadCombat`, around line 1367)

```js
const ALL_CONDITIONS = [
  "Blinded","Charmed","Deafened","Frightened","Grappled",
  "Incapacitated","Invisible","Paralyzed","Petrified","Poisoned",
  "Prone","Restrained","Stunned","Unconscious","Exhaustion",
];

function renderCondChips(combatantId, conditions) {
  if (!conditions || !conditions.length) return "";
  const chips = conditions.map(c => {
    const label = c.startsWith("Exhaustion:") ? `Exhausted ${c.split(":")[1]}` : c;
    return `<span class="cond-chip">${label}<span class="cond-chip-x" onclick="removeCondition(${combatantId},'${c}',event)">×</span></span>`;
  }).join("");
  return `<div class="cond-chips-row">${chips}</div>`;
}
```

- [ ] **Step 2: Update the combat card template in `loadCombat` to add chip row and "+ Condition" button**

Find the `return \`<div class="combat-card"` template inside `loadCombat` (around line 1390). In the `.combat-card-actions` div, add the condition section right before that div closes. The current template ends with:

```js
      <div class="combat-card-actions" onclick="event.stopPropagation()">
        <button class="combat-hp-btn" onclick="combatAdjHpBtn(...)">−1</button>
        ...
      </div>
    </div>`;
```

Change to insert conditions between the stats row and actions:

```js
      ${renderCondChips(c.combatant_id, c.conditions)}
      <div class="combat-card-actions" onclick="event.stopPropagation()">
        <button class="combat-hp-btn" onclick="combatAdjHpBtn(...)">−1</button>
        <button class="combat-hp-btn" onclick="combatAdjHpBtn(...)">+1</button>
        <input type="number" id="combat-adj-${c.combatant_id}" class="combat-hp-input" placeholder="±HP">
        <button class="combat-hp-btn" onclick="combatApplyAdj(...)">Apply</button>
        <button class="combat-hp-btn" onclick="openConditionPicker(${c.combatant_id},event)" title="Conditions">＋ Cond</button>
      </div>
    </div>`;
```

(Keep the existing `combatAdjHpBtn` and `combatApplyAdj` calls unchanged; just append the `＋ Cond` button and add `renderCondChips` above the actions div.)

- [ ] **Step 3: Add `openConditionPicker`, `closeConditionPicker`, `toggleCondition`, `removeCondition`, and `setExhaustionLevel` to `admin.js`** (after `combatApplyAdj`, around line 1455)

```js
let _condPickerCombatantId = null;

function openConditionPicker(combatantId, event) {
  event.stopPropagation();
  closeConditionPicker();
  _condPickerCombatantId = combatantId;

  const combatant = _combatants.find(c => c.combatant_id === combatantId);
  const active = new Set(combatant ? (combatant.conditions || []) : []);
  const exhaustLevel = (() => {
    for (const c of active) if (c.startsWith("Exhaustion:")) return parseInt(c.split(":")[1], 10);
    return 0;
  })();

  const picker = document.createElement("div");
  picker.className = "cond-picker";
  picker.id = "cond-picker";
  picker.onclick = e => e.stopPropagation();

  const items = ALL_CONDITIONS.map(cond => {
    const isExh = cond === "Exhaustion";
    const isActive = isExh ? exhaustLevel > 0 : active.has(cond);
    return `<div class="cond-picker-item${isActive ? " active" : ""}" onclick="toggleCondition(${combatantId},'${cond}',event)">
      <span class="cond-picker-check">${isActive ? "✓" : ""}</span>
      ${cond}${isExh && exhaustLevel > 0 ? ` (${exhaustLevel})` : ""}
    </div>`;
  }).join("");

  const exhaustPicker = `
    <div class="cond-exhaustion-picker" id="exh-picker">
      ${[1,2,3,4,5,6].map(n => `<button class="cond-exhaustion-btn${n === exhaustLevel ? " active" : ""}"
        onclick="setExhaustionLevel(${combatantId},${n},event)">${n}</button>`).join("")}
      ${exhaustLevel > 0 ? `<button class="cond-exhaustion-btn" onclick="setExhaustionLevel(${combatantId},0,event)" style="color:var(--rubric)">✕</button>` : ""}
    </div>`;

  picker.innerHTML = items + exhaustPicker;

  const btn = event.currentTarget;
  const rect = btn.getBoundingClientRect();
  picker.style.top = (rect.bottom + 4 + window.scrollY) + "px";
  picker.style.left = rect.left + "px";
  document.body.appendChild(picker);
  setTimeout(() => document.addEventListener("click", closeConditionPicker, { once: true }), 0);
}

function closeConditionPicker() {
  const el = document.getElementById("cond-picker");
  if (el) el.remove();
  _condPickerCombatantId = null;
}

async function toggleCondition(combatantId, condName, event) {
  event.stopPropagation();
  if (condName === "Exhaustion") return; // handled by level picker below
  const combatant = _combatants.find(c => c.combatant_id === combatantId);
  if (!combatant) return;
  const current = [...(combatant.conditions || [])];
  const idx = current.indexOf(condName);
  if (idx >= 0) current.splice(idx, 1);
  else current.push(condName);
  await _applyConditions(combatantId, current);
  closeConditionPicker();
  loadCombat();
}

async function setExhaustionLevel(combatantId, level, event) {
  event.stopPropagation();
  const combatant = _combatants.find(c => c.combatant_id === combatantId);
  if (!combatant) return;
  const current = (combatant.conditions || []).filter(c => !c.startsWith("Exhaustion"));
  if (level > 0) current.push(`Exhaustion:${level}`);
  await _applyConditions(combatantId, current);
  closeConditionPicker();
  loadCombat();
}

async function removeCondition(combatantId, condName, event) {
  event.stopPropagation();
  const combatant = _combatants.find(c => c.combatant_id === combatantId);
  if (!combatant) return;
  const current = (combatant.conditions || []).filter(c => c !== condName);
  await _applyConditions(combatantId, current);
  loadCombat();
}

async function _applyConditions(combatantId, conditions) {
  try {
    const r = await api("PATCH", `/api/admin/combatants/${combatantId}/conditions`, { conditions });
    const combatant = _combatants.find(c => c.combatant_id === combatantId);
    if (combatant) combatant.conditions = r.conditions;
  } catch(e) { err(e.message || "Failed to set conditions"); }
}
```

- [ ] **Step 4: Commit**

```bash
git add static/admin.js
git commit -m "feat: condition chips and picker on status tracker combat cards"
```

---

## Task 9: Conditions in Monster Stat Block Modal

**Files:**
- Modify: `static/admin.js`

The monster modal (`openMonsterModal`) is called both from the combat card (click) and the Codex monster list. In the combat context, `_combatants` holds the active conditions for that monster.

- [ ] **Step 1: Update `openMonsterModal` to show active conditions**

Find `openMonsterModal` (around line 1317). After line:
```js
async function openMonsterModal(monsterId) {
  const m = await api("GET", `/api/admin/monsters/${monsterId}`);
```

Add:
```js
  const combatant = _combatants.find(c => c.monster_id === monsterId);
  const activeConditions = combatant ? (combatant.conditions || []) : [];
```

Then, in the `document.getElementById("monster-modal-body").innerHTML` template, add a conditions row at the very top of `.monster-stat-block`, before `<div class="msb-meta">`:

```js
  document.getElementById("monster-modal-body").innerHTML = `
    <div class="monster-stat-block">
      ${activeConditions.length ? `<div class="cond-chips-row" style="margin-bottom:10px">${activeConditions.map(c => {
        const label = c.startsWith("Exhaustion:") ? `Exhausted ${c.split(":")[1]}` : c;
        return `<span class="cond-chip">${label}</span>`;
      }).join("")}</div>` : ""}
      <div class="msb-meta">...rest of existing template...
```

(Preserve the rest of the existing template exactly as is — only prepend the condition chips row.)

- [ ] **Step 2: Commit**

```bash
git add static/admin.js
git commit -m "feat: show active conditions at top of monster stat block modal"
```

---

## Self-Review

**Spec coverage check:**
- ✅ "⇄ Swap Mastery" button always visible on sheet — Task 7 Step 1
- ✅ Swap-one-at-a-time, remove + add — Task 2 endpoint + Task 7 modal
- ✅ Player-accessible endpoint — Task 2 uses `require_user` + `_check_owner_or_admin`
- ✅ DM-only condition setting — Task 3 endpoint uses admin router (no `require_admin` decorator needed — admin router already gates all routes; verify this matches the pattern in `admin.py`)
- ✅ `conditions` on `Character` (persistent) + `Combatant` (monsters only) — Task 1
- ✅ Valid condition list + Exhaustion tiered validation — Task 3 Step 3
- ✅ Condition strip between combat bar and tabs — Task 5 Step 4b
- ✅ Chip tooltip from glossary — Task 5 Step 1 (`_glossaryMap` reference)
- ✅ Color coding red/amber/gold — Task 4 Step 1 + Task 5 Step 1
- ✅ Speed reflection for 6 conditions + Exhaustion 3–6 — Task 5 Step 3
- ✅ 15-second poll carries conditions — Task 6
- ✅ Inline chip picker on combat card — Task 8
- ✅ Exhaustion level picker — Task 8 Step 3
- ✅ Monster modal shows conditions — Task 9
- ✅ Repair Schema updated — Task 3 Step 5

**Admin auth is router-level:** `app/routers/admin.py` line 21 sets `dependencies=[Depends(require_admin)]` on the router, so the new `set_combatant_conditions` endpoint is automatically admin-gated. No per-endpoint `Depends(require_admin)` needed.

**Glossary variable name in Task 5 Step 2:** The plan says to check and correct `_glossaryMap` — this is mandatory before ship. The step includes an explicit grep command for this reason.
