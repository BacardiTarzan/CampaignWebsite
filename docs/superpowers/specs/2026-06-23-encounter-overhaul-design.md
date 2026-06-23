# Phase 5.5: Encounter System Overhaul — Design Spec

## Goal

Make the encounter tracker fully functional before merging to main: real-time WebSocket updates, token-first action selection with cost enforcement, class ability auto-seeding, wizard cantrip fix, player End Turn, and rest controls moved to admin.

---

## 1. WebSocket Architecture

### Approach: Full-State Push

On any encounter mutation (turn advance, HP change, action economy, movement, conditions, initiative), the server pushes the complete encounter state JSON to every connected client. Clients replace local state and re-render. No event reconciliation. No sync bugs. Payload is small (~6 combatants < 2KB).

### ConnectionManager (`app/services/ws_manager.py`)

Module-level singleton. All routers import it to call `broadcast()`.

```python
class ConnectionManager:
    def __init__(self):
        self.active: set[WebSocket] = set()

    async def connect(self, ws: WebSocket):
        await ws.accept()
        self.active.add(ws)

    def disconnect(self, ws: WebSocket):
        self.active.discard(ws)

    async def broadcast(self, data: dict):
        dead = set()
        for ws in self.active:
            try:
                await ws.send_json(data)
            except Exception:
                dead.add(ws)
        self.active -= dead

manager = ConnectionManager()
```

### WebSocket Endpoint (`app/routers/encounter.py`)

```
GET /ws/encounter  (WebSocket upgrade)
```

- Auth: reads session cookie from the WS upgrade request headers. Rejects with `1008` close code if not authenticated.
- On connect: sends current full encounter state immediately (HTTP fetch of state, same as `/api/encounter/state`).
- On disconnect: removes from connection pool.
- Receives no messages from clients (read-only push channel; clients POST to REST for writes).

### Client-Side (both `encounter.js` and `admin.js`)

1. On page load: `const ws = new WebSocket('ws://host/ws/encounter')`
2. `ws.onmessage`: parse JSON → replace `encounterState` → call `render()`
3. Reconnect: on `ws.onclose`, wait 1s then 2s then 4s (cap 30s). Show "Reconnecting…" banner during gap.
4. On reconnect: fetch `/api/encounter/state` via HTTP to catch up on missed state, then let WS take over.
5. Remove all `setInterval` polling from both files. The existing `/api/encounter/state` HTTP endpoint stays for initial load and reconnect catch-up only.

### Broadcast Trigger Points

Every endpoint that mutates encounter state must call `await manager.broadcast(state_dict)` after `db.commit()`. A shared helper `async def _broadcast_state(db)` in `encounter.py` fetches the current state dict and calls `manager.broadcast()`. Import this helper in `admin.py` and `characters.py`.

Trigger points:
- `POST /api/admin/encounter/start|begin-round-1|advance-turn|end`
- `PATCH /api/admin/combatants/{id}/initiative`
- `PATCH /api/admin/combatants/{id}/actions` (action economy)
- `PATCH /api/admin/combatants/{id}/hp`
- `PATCH /api/admin/combatants/{id}/conditions`
- `POST /api/characters/encounter/action-economy`
- `POST /api/characters/encounter/end-turn` *(new)*
- `POST /api/characters/encounter/spend-movement` *(new)*

---

## 2. Token-First Action Flow (Mobile-First)

### Encounter Page Layout

Mobile-first, single column, full viewport width. No popups or modals — everything expands inline.

```
[ YOUR TURN — Round N  ]   ← gold banner, only when active

[ ○ ACTION ] [ ○ BONUS  ]  ← 2×2 grid, large tap targets
[ ○ REACTION] [ ○ MOVE   ]    MOVE shows "30 ft left"

↓ expands inline when token tapped ↓

[ ATTACKS                ]
  ⚔ Longsword     +5 · 1d8+3
  ⚔ Unarmed        +5 · 1+3
[ CANTRIPS               ]
  ✦ Fire Bolt      +6 · 2d10
[ SPELLS                 ]
  ✦ Fireball       L3 · DC 14
  ✦ Magic Missile  L1 · auto
[ ABILITIES              ]
  ◈ Second Wind    1 left
  ◈ Action Surge   ✗ 0 left   ← grayed, not tappable
  — Skip

↓ on ability selected ↓

[ ✦ Fireball               ]
  150 ft · 20 ft radius
  DC 14 Dex save · 8d6 fire
  Slot: [ L3 (4 left) ▾ ]
  Costs: 1 Action + 1 L3 Slot
  [ ✓ Use It ]  [ ← Back ]

[ → End Turn ]   ← always visible at bottom
```

### Token States

| State | Visual |
|-------|--------|
| Available | Colored border, light background, tappable |
| Expanded (selected) | Filled background with ▼ indicator, others dimmed |
| Used | Strikethrough, grayed, `cursor: not-allowed` |
| Move at 0 ft | Same as Used |

### Action Economy Rules

- Tapping a used token does nothing.
- Abilities listed under ACTION require `action_used=False` to confirm.
- Abilities listed under BONUS require `bonus_action_used=False` to confirm.
- Leveled spells show a slot-level picker; cantrips do not.
- "Use It" marks the relevant token used, spends any resource (spell slot or CharacterResource), then broadcasts.
- The confirm step always shows: ability name, key stats (attack bonus OR save DC, damage, range), cost summary, slot picker if applicable.

### Movement Token

Tapping MOVE opens an inline stepper instead of an ability list:

```
Move how far?
[ 5 ][ 10 ][ 15 ][ 20 ][ 25 ][ 30 ]   ← quick buttons (only up to remaining)
[ − ]  10 ft  [ + ]   (5 ft steps)
[ Spend 10 ft ]  [ ← Back ]
```

- Movement can be spent in multiple chunks per turn.
- MOVE token shows current `movement_remaining` at all times.
- MOVE grays out when `movement_remaining = 0`.
- **Dash ability** (in the Action list under ABILITIES): costs 1 Action, adds `character.speed` to `movement_remaining`. Does not mark movement as "used" — it increases the pool.

New endpoint: `POST /api/characters/encounter/spend-movement`
```json
{ "combatant_id": 5, "amount": 10 }
```
Validates `amount` is a positive multiple of 5, `amount <= movement_remaining`, and the requesting player owns the combatant. Decrements `movement_remaining`, broadcasts.

### End Turn

`POST /api/characters/encounter/end-turn`
```json
{ "combatant_id": 5 }
```
- Validates `combatant.id == encounter_state.current_turn_combatant_id`.
- Validates requesting player owns that character.
- Runs `_advance_turn()` → broadcasts.
- Returns 400 if it's not this combatant's turn.
- DM's "Next Turn" button in admin tracker remains as an override (calls the same logic).

End Turn button is only visible on the encounter page when `is_current_turn=true` for the player's character.

---

## 3. Class Ability Seeding

### Markdown Schema (`reference_claude/class_actions/{class}.md`)

User creates one file per class. The seeder reads these files on server startup (or on demand) and caches the parsed result.

```markdown
# Fighter

## Second Wind
action_type: bonus_action
resource_key: second_wind
min_level: 1
max_uses: 2
rest_type: short
description: Regain HP equal to 1d10 + your fighter level.

## Action Surge
action_type: special
resource_key: action_surge
min_level: 2
max_uses: 1
rest_type: short
description: Take one additional Action this turn. Adds movement_remaining += speed as well.
```

**`action_type` values:**

| Value | Behavior |
|-------|----------|
| `action` | Listed under ACTION token |
| `bonus_action` | Listed under BONUS token |
| `reaction` | Listed under REACTION token |
| `special` | Tracked as resource; appears under ACTION as a named entry (e.g., "Action Surge") |
| `passive` | Tracked in resource strip, does not appear in action list (e.g., Sneak Attack — 1/turn reminder) |

**`max_uses` formulas:** Plain integer OR simple expressions evaluated at seeding time:
- `level` — character's current level
- `level // 2` — half level (floor)
- Fixed integer

### Seeding Flow

Called from `POST /api/admin/combatants/character` (add character to combat):

```python
def seed_class_abilities(char: Character, db: Session):
    cc = char.character_classes[0] if char.character_classes else None
    if not cc: return
    class_name = cc.dnd_class.name.lower()
    level = cc.level
    abilities = load_class_actions(class_name)  # parsed + cached from markdown
    for ability in abilities:
        if level < ability["min_level"]:
            continue
        existing = db.query(CharacterResource).filter_by(
            character_id=char.id, resource_key=ability["resource_key"]
        ).first()
        if existing:
            continue  # never overwrite manual DM config
        max_uses = eval_uses(ability["max_uses"], level)
        db.add(CharacterResource(
            character_id=char.id,
            resource_key=ability["resource_key"],
            label=ability["name"],
            max_uses=max_uses,
            used=0,
            rest_type=ability["rest_type"],
        ))
    db.commit()
```

### Minimum Abilities to Seed (at launch)

Fighter: Second Wind, Action Surge
Barbarian: Rage
Monk: Ki Points (pool, not individual uses)
Cleric: Channel Divinity
Paladin: Channel Divinity
Druid: Wild Shape
Bard: Bardic Inspiration
Ranger: Hunter's Mark free casts
Rogue: Sneak Attack (passive — 1/turn reminder)
Sorcerer: Sorcery Points
Warlock: Eldritch Invocation slots (via Pact Magic)
Wizard: Arcane Recovery (1/long rest, regain slots)

---

## 4. Spell Fix + Cantrip Bug

### Root Cause

Character creation step 9 sets `prepared = not is_wizard` for all spells, including cantrips. This incorrectly marks wizard cantrips as `prepared=False`.

### Fix 1: Character Creation (`app/routers/characters.py`, step 9)

```python
spell = db.get(Spell, sid)
is_cantrip = spell and spell.level == 0
db.add(CharacterSpell(
    character_id=char.id,
    spell_id=sid,
    source="class",
    prepared=True if is_cantrip else (not is_wizard),
))
```

Cantrips always `prepared=True` for all classes. Level 1+ wizard spells `prepared=False` (spellbook, prepared via the Prepare Spells modal on the sheet before combat).

### Fix 2: Encounter Actions Endpoint (`app/routers/characters.py`)

In `get_encounter_actions()`, always include level-0 spells regardless of `prepared` flag:

```python
for sp in data.get("spells", []):
    is_cantrip = sp.get("level", 0) == 0
    if not is_cantrip and not sp.get("prepared") and not sp.get("always_prepared"):
        continue
    # ... rest of filter
```

Wizard workflow: player opens sheet → Spells tab → "✎ Prepare Spells" → selects daily spells from spellbook → saves. Those prepared spells then appear in the encounter action list alongside cantrips.

---

## 5. Rest Controls → Admin Only

### Remove from Player Sheet (`static/sheet.js`)

Remove `takeRest()` function and the `.sh-rest-btns` HTML that renders Short/Long Rest buttons. The `POST /api/characters/{id}/rest` player endpoint can remain (used by admin), but the player-facing buttons are gone.

### Add to Admin Roster (`static/admin.js`)

In the Admin tab's character roster list, add per-character rest buttons alongside existing character rows:

```
[Character Name] [Lv 5 Fighter]   [Short Rest]  [Long Rest]
```

These call `POST /api/admin/characters/{id}/rest` with `{rest_type: "short"}` or `{rest_type: "long"}` and trigger a WS broadcast with updated resource state.

---

## 6. File Structure Summary

### New Files

| File | Purpose |
|------|---------|
| `app/services/ws_manager.py` | `ConnectionManager` singleton + `manager` instance |
| `app/services/class_action_seeder.py` | Parse class action markdowns, seed CharacterResource |
| `reference_claude/class_actions/*.md` | Class ability definitions (user-created) |

### Modified Files

| File | Changes |
|------|---------|
| `app/routers/encounter.py` | Add `/ws/encounter` WebSocket endpoint; add `_broadcast_state()` helper |
| `app/routers/admin.py` | Broadcast after mutations; call `seed_class_abilities()` on character add-to-combat; add rest buttons in roster |
| `app/routers/characters.py` | Fix cantrip prepared flag; fix `encounter-actions` cantrip filter; add `end-turn` endpoint; add `spend-movement` endpoint; broadcast after action/movement changes |
| `app/main.py` | No change needed — encounter router already registered |
| `static/encounter.js` | Full rewrite: WS client, token-first UI, move stepper, End Turn |
| `static/encounter.html` | Mobile-first layout: 2×2 grid, inline expansion, fixed End Turn |
| `static/sheet.js` | Remove `takeRest()` and rest buttons |
| `static/admin.js` | Replace polling with WS client; add rest buttons to roster |

---

## 7. Out of Scope for This Phase

- Calendar / time tracking
- Direct targeting (enter-your-roll resolution) — action list is info-display only
- Custom action creation wizard — DM can add CharacterResource entries manually; the wizard is a future feature
- Concentration tracking (spell effect duration timers)

---

## 8. Testing

1. **WebSocket connect:** Open `/encounter` and `/admin` in two tabs simultaneously. Advance a turn in admin — both tabs update instantly without page refresh.
2. **Token flow:** On the encounter page as a player on their turn, tap ACTION → list appears inline → select a leveled spell → slot picker shows → Use It → action token grays out, slot count decrements, admin tracker reflects updated action economy.
3. **Movement:** Tap MOVE → spend 10 ft → MOVE token shows "20 ft left" → spend 20 more → MOVE grays out at 0.
4. **End Turn:** Player clicks End Turn → initiative advances → next player's encounter page shows YOUR TURN banner.
5. **Cantrip fix:** Level 1 wizard in encounter → ACTION list shows cantrips.
6. **Class ability seeding:** Add a Fighter to combat → Second Wind and (at level 2+) Action Surge appear in their BONUS/ACTION list automatically.
7. **Wizard prep:** Wizard has no prepared spells → only cantrips in action list → player opens sheet, prepares spells, returns to encounter → leveled spells now appear.
8. **Rest (admin only):** No Short/Long Rest buttons visible on player sheet. Admin roster shows them per character. Clicking triggers resource restoration + WS broadcast.
9. **Reconnect:** Close and reopen `/encounter` mid-encounter → WS reconnects → correct state shows immediately.
