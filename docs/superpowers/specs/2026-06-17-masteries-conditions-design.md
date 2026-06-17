# Masteries Swap + Conditions System — Design Spec
**Date:** 2026-06-17

## Context

The campaign is moving away from digitally tracking rests, spell slots, and daily-use abilities in favour of real-life tokens. The web app's role shifts toward displaying character and monster information well, and tracking persistent state that benefits from being shared — primarily HP and conditions. This spec covers two features that support that shift:

1. A player-accessible **Change Masteries** button on the character sheet
2. A **Conditions** system: DM-assigned from the status tracker, visible on character sheets and monster stat blocks

---

## Feature 1 — Change Masteries (Swap One at a Time)

### Behaviour
A "⇄ Swap Mastery" button appears in the Weapon Proficiencies & Masteries section of the Stats tab. It is always visible and player-accessible. Each interaction allows exactly one swap: remove one currently mastered weapon, add one proficient weapon not yet mastered. This matches the D&D 2024 rule that a character can swap one mastery per long rest; since rest tracking is handled with physical tokens, no rest gate is enforced in the UI.

### API
**`PATCH /api/characters/{char_id}/masteries/swap`** — player-authenticated (require_user, ownership check).

Request body:
```json
{ "remove": "Longsword", "add": "Rapier" }
```

Validation:
- `remove` must exist in `WeaponMasteryUnlock` for this character
- `add` must exist in the character's weapon proficiencies and must NOT already be in `WeaponMasteryUnlock`
- Both must be non-empty strings from the known weapon list

On success: deletes the `remove` row and inserts an `add` row atomically. Returns `{"ok": true}`.

No migration required — `WeaponMasteryUnlock` table already exists.

### UI — Sheet Modal
The "⇄ Swap Mastery" button is styled like the existing "✎ Prepare Spells" button (`.prep-edit-btn` pattern). Clicking opens a `.scroll-modal` with:

- **Left column — "Remove"**: current masteries as selectable rows; click one to mark it for removal
- **Right column — "Add"**: all weapon proficiencies not already mastered, as selectable rows; click one to mark it for addition
- **"Swap" button**: activates only when both sides have a selection; calls `PATCH /masteries/swap`; on success closes modal and re-renders the Weapon Proficiencies section

---

## Feature 2 — Conditions System

### Philosophy
Conditions are DM-controlled state that persists until the DM removes them. Players see conditions on their own character sheet but cannot set or clear them. Monster conditions are session-scoped (lost when removed from tracker). Character conditions are persistent (survive across sessions).

### Condition List (D&D 2024)
15 conditions: Blinded, Charmed, Deafened, Frightened, Grappled, Incapacitated, Invisible, Paralyzed, Petrified, Poisoned, Prone, Restrained, Stunned, Unconscious, and **Exhaustion** (tiered 1–6).

Exhaustion is stored as `"Exhaustion:N"` where N is 1–6. All other conditions are stored as plain strings.

### Data Model

**`characters.conditions`** — new `TEXT` column (nullable, JSON-serialised list). Stores conditions on player characters. Persists across tracker sessions.

**`combatants.conditions`** — new `TEXT` column (nullable, JSON-serialised list). Stores conditions on monster combatants. Lost when the combatant row is deleted.

**Character combatant rule:** `Combatant.character_id` rows are thin join records; their conditions are read from and written to `Character.conditions`, not the combatant row.

**Migration:** Two `ADD COLUMN IF NOT EXISTS conditions TEXT` statements using the codebase's existing dialect-aware inspector pattern (not raw `ALTER TABLE IF NOT EXISTS`).

### API

**`PATCH /api/admin/combatants/{id}/conditions`** — admin-only.

Request body:
```json
{ "conditions": ["Grappled", "Exhaustion:3"] }
```

Behaviour:
- Validates each entry against the known 15-condition list; Exhaustion entries must match `Exhaustion:[1-6]`; returns 400 for unknown values
- If `combatant.character_id` is set: writes to `Character.conditions`
- If `combatant.monster_id` is set: writes to `Combatant.conditions`
- Send `[]` to clear all conditions

**Sheet data:** `character_to_sheet_dict` in `export.py` adds `"conditions"` (list, default `[]`) to the response. The existing 15-second HP poll at `GET /api/characters/{id}/sheet-data` carries it at no extra cost — condition updates appear on the sheet within one poll cycle.

### UI — Status Tracker (Admin)

Each combatant card gains:

1. **Condition chips row**: active conditions render as small removable pill tags below the name/HP row. Format: `Grappled ×`, `Exhausted 3 ×`. Clicking × patches the conditions list with that entry removed.

2. **"＋ Condition" button**: opens an inline popover anchored to the card (not a full modal). The popover lists all 15 conditions. Behaviour:
   - Binary conditions: single click toggles on/off and closes the popover
   - Exhaustion: clicking shows a 1–6 level picker before confirming
   - Already-active conditions appear highlighted so the DM sees current state
   - Clicking an active condition removes it

3. **Monster stat block modal**: when the monster combatant has active conditions, a read-only "Conditions" chip row appears at the top of the existing stat block modal. Editing still happens on the card.

### UI — Character Sheet

**Condition strip:** A slim row between the combat bar and the tab bar. Renders only when `conditions` is non-empty — no empty space otherwise. Each condition is a pill tag using the existing mastery-tag visual style. Hovering shows the condition's short description from the glossary (pulled from the already-loaded glossary data in `sheet.js`).

**Colour coding:**
- **Red** (`--rubric` family): Incapacitated, Paralyzed, Petrified, Stunned, Unconscious
- **Amber** (`#8b4a00` range): Exhaustion, Frightened, Poisoned
- **Gold** (`--gold` family): Blinded, Charmed, Deafened, Grappled, Invisible, Prone, Restrained

**Stat reflection in the combat bar — Speed cell only:**

| Condition(s) active | Speed display |
|---|---|
| Grappled, Restrained, Paralyzed, Petrified, Stunned, or Unconscious | `0` in rubric red |
| Exhaustion level 3 or 4 | halved value in amber, e.g. `15` |
| Exhaustion level 5 or 6 | `0` in rubric red |
| No speed-affecting conditions | normal display |

No other combat bar stats (AC, Initiative, Prof, Passive Perc) are modified by any standard condition.

---

## Out of Scope
- Player-controlled conditions (all condition writes are DM-only)
- Condition duration tracking (on/off or level is sufficient)
- Custom/homebrew conditions
- Rest-gating the mastery swap (physical tokens handle rest tracking)
- Clearing character conditions automatically when combat ends (DM clears manually)
