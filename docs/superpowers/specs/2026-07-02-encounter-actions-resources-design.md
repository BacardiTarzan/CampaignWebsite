# Encounter Actions & Resources — Design Spec
**Date:** 2026-07-02
**Status:** Approved

## Context

Phase 5.5 shipped a token-first encounter UI and class ability seeding from markdown. Two gaps remain:

1. **`CharacterResource` has no `action_type` column.** The seeder parses `action_type` from the markdown but discards it. `_injectResourceAbilities()` in `encounter.js` hard-codes all abilities as `cost: { action: true }`, so reactions and bonus-action abilities never appear under the right token.

2. **Reactions are only accessible on your turn.** The token grid renders only when `myActiveCombatantId` is set. Players can't spend a reaction to attack of opportunity (or use Parry, Shield, etc.) while watching another combatant's turn.

3. **Reaction spells are excluded.** `get_encounter_actions` skips any spell that isn't `"1 action"` or `"bonus action"` casting time, so `Shield`, `Counterspell`, etc. never appear.

4. **Admins can't spend individual resources.** Long/Short Rest restores everything; there's no way for the DM to spend (or restore) a single resource use on behalf of a player — needed for edge cases like Indomitable triggering on a saving throw.

## Scope

This spec covers four changes that ship together (they share the migration):

| # | Area | What changes |
|---|------|-------------|
| 1 | DB + Seeder | Add `action_type` to `character_resources`; seeder stores it |
| 2 | Backend | `get_encounter_actions` includes reaction spells; resource API returns `action_type` |
| 3 | Player encounter UI | Off-turn "Use Reaction" panel; `_injectResourceAbilities` uses `action_type` |
| 4 | Admin UI | Collapsible resource panel on roster cards with Spend/Restore per resource |

**Not in scope:** `free_action`, `move_action`, `special`, and `passive` abilities do not appear in the encounter action list (player chose: skip for now). They are still seeded and tracked as resource pools.

---

## 1. DB Migration + Model + Seeder

### Migration
New migration (after `m0n1o2p3q4r5`):

```sql
-- PostgreSQL
ALTER TABLE character_resources ADD COLUMN IF NOT EXISTS action_type VARCHAR;

-- SQLite (via sa_inspect check)
ALTER TABLE character_resources ADD COLUMN action_type VARCHAR;
```

File: `alembic/versions/n1o2p3q4r5s6_resource_action_type.py`

### Model
`app/models/character.py` — `CharacterResource`:

```python
action_type = Column(String, nullable=True)
# Values: action | bonus_action | reaction | free_action | move_action | special | passive | None
```

### Seeder (`app/services/class_action_seeder.py`)
- Parse `action_type` field (already read; just not stored).
- Pass it to the `CharacterResource` constructor.
- **No filter change** — seed anything with `resource_key` + `max_uses` + `rest_type` regardless of `action_type`. The display layer decides what to show.

### Resource API
`GET /api/characters/{id}/resources` response shape gains `"action_type": str | null` per entry.

---

## 2. Backend — `get_encounter_actions` + reaction spells

### `app/routers/characters.py` — `get_encounter_actions`

**Current filter:**
```python
is_action = "1 action" in ct
is_bonus = "bonus action" in ct
if not is_action and not is_bonus:
    continue  # skip rituals, reactions, 1 minute, etc.
```

**New filter:**
```python
is_action = "1 action" in ct
is_bonus = "bonus action" in ct
is_reaction = "reaction" in ct
if not is_action and not is_bonus and not is_reaction:
    continue  # skip rituals, 1 minute, etc.
```

Add `reaction: is_reaction` to the `cost` dict on every spell action:
```python
"cost": {"action": is_action, "bonus_action": is_bonus, "reaction": is_reaction, "spell_slot": slot_level},
```

---

## 3. Player Encounter UI — off-turn reactions

### `_injectResourceAbilities()` in `encounter.js`

Use the resource's `action_type` to set cost flags. Skip resources whose `action_type` won't appear in the action list:

```js
const SKIP_ACTION_TYPES = new Set(['special', 'free_action', 'move_action', 'passive', null]);

function _injectResourceAbilities() {
  for (const r of myEncResources) {
    if (SKIP_ACTION_TYPES.has(r.action_type)) continue;  // pool definitions, free triggers
    const key = `ability:${r.resource_key}`;
    if (myActions.find(a => a._key === key)) continue;
    myActions.push({
      _key: key,
      type: 'ability',
      name: r.label,
      resource_id: r.id,
      resource_key: r.resource_key,
      cost: {
        action:        r.action_type === 'action',
        bonus_action:  r.action_type === 'bonus_action',
        reaction:      r.action_type === 'reaction',
        spell_slot: null,
      },
      max_uses: r.max_uses,
      remaining: r.remaining,
      rest_type: r.rest_type,
      description: r.description || '',
      // display fields
      attack_bonus: null, attack_bonus_display: null,
      save_dc: null, save_ability: null,
      damage: '', range: '', level: null, school: null,
    });
  }
}
```

### `renderActionList()` — reaction filtering

The existing filter for abilities already handles `a.cost.reaction`:
```js
const abilities = myActions.filter(a =>
  a.type === 'ability' && (isAction ? a.cost.action : (isBonus ? a.cost.bonus_action : a.cost.reaction))
);
```
This is correct once `_injectResourceAbilities` sets `cost.reaction` properly. No change needed here.

Add a reaction filter for spells too:
```js
const reactSpells = tokenType === 'reaction'
  ? myActions.filter(a => a.type === 'spell' && a.cost.reaction)
  : [];
```
Include `reactSpells` in the `renderActionList` output under a **REACTION SPELLS** section.

### Off-turn reaction panel

**When not your turn** (i.e., `myActiveCombatantId` is null / encounter active but it's someone else's turn), the encounter page shows a compact **"⚡ Reaction"** section below the initiative order.

Logic in `render()`:

```js
// Determine player's combatants (any character owned, regardless of whose turn)
const myCombatants = encounterState.combatants
  .filter(c => c.kind === 'character' && myCharIds.includes(c.character_id));

const reactionAvailable = myCombatants.some(c => !c.reaction_used);
```

If `!isMyTurn && encounter_active && !initiative_phase`:
- Show: `<div id="enc-reaction-zone">` with a button per combatant that still has a reaction.
- Button label: `⚡ Use Reaction` (single character) or `⚡ [Name]'s Reaction` (multiple).
- Tapping it: sets `myActiveCombatantId` to that combatant's id temporarily (just for the reaction flow), calls `tapToken('reaction')`.
- After `doUseAction()` completes, clear `myActiveCombatantId` back to null.
- If `reaction_used` is already true for all owned combatants, show a grayed `⚡ Reaction Used` indicator instead.

This reuses the entire existing `tapToken('reaction') → renderActionList → selectAction → doUseAction` flow with zero new server endpoints.

---

## 4. Admin UI — spend/restore individual resources

### New endpoints (`app/routers/admin.py`)

```
POST /api/admin/characters/{char_id}/resources/{resource_id}/spend
  body: { amount: int = 1 }
  → { id, used, remaining }
  Clamps: used cannot exceed max_uses

POST /api/admin/characters/{char_id}/resources/{resource_id}/restore
  body: { amount: int | "all" = 1 }
  → { id, used, remaining }
  Clamps: used cannot go below 0
```

Both re-fetch and re-render the character's resource list in the admin card after the POST. No WS broadcast is needed — the player's resource panel refreshes on their next interaction (Use It, End Turn). At a physical table the DM can verbally note the spend. A future iteration could include per-character resources in the WS state if real-time sync becomes important.

### Admin UI (`static/admin.js`)

In the character roster card (DM view, combat tracker), add a collapsible **Resources** section below the existing HP / rest buttons. Collapsed by default:

```
[+] Resources ▸
```

When expanded, shows a list of the character's `CharacterResource` rows:

```
Second Wind    ●●○   [− Spend]  [+ Restore]
Action Surge   ●○    [− Spend]  [+ Restore]
Superiority Dice  ●●●●○○  [− Spend]  [+ Restore]
```

- Pips: filled = remaining, hollow = spent
- `− Spend` calls `POST .../spend`; `+ Restore` calls `POST .../restore`
- Both update the card in-place (no full re-render needed — fetch latest resources, re-render just the resource list)
- Resources are loaded once per card open (lazy; not polled)

---

## Data flow summary

```
Markdown (action_type) 
  → Seeder stores to character_resources.action_type
  → GET /resources returns action_type
  → _injectResourceAbilities() sets cost.reaction / cost.bonus_action
  → renderActionList() filters correctly

Reaction spell (casting_time: "reaction")
  → get_encounter_actions includes it with cost.reaction = true
  → appears in reaction action list (both on-turn and off-turn)

Off-turn reaction tap
  → enc-reaction-zone button → tapToken('reaction') with temp combatant id
  → doUseAction() → POST action-economy (reaction_used=true) + POST resources/spend
  → WS broadcast → all clients update

Admin spend/restore
  → POST /api/admin/characters/{id}/resources/{resource_id}/spend|restore
  → admin card resource list re-renders in-place
  → player encounter page sees the change on next Use It or page reload
```

---

## Testing

1. **Seeder stores action_type:** Add Fighter to combat → check DB: `SELECT resource_key, action_type FROM character_resources WHERE character_id = X` — Second Wind should have `bonus_action`, Indomitable should have `free_action`.

2. **Reaction abilities appear:** Paladin with Absorb Elements (reaction spell) — on the `/encounter` page, REACTION token action list should show "Absorb Elements".

3. **Off-turn reaction:** Start encounter, it's Fighter's turn. On Paladin's page → see `⚡ Use Reaction` button → tap → reaction list appears → Use It → `reaction_used = true` for Paladin in WS state.

4. **Admin spend:** DM opens roster, expands Fighter's Resources → clicks `− Spend` on Indomitable → resource shows 0/1 → player's encounter page resource panel updates.

5. **Playwright smoke test:** Extend existing encounter smoke test to verify reaction zone is visible when it's not the player's turn.
