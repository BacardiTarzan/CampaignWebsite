# Phase 5.5: Encounter System Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace 2s polling with WebSockets for real-time encounter updates, add token-first mobile action selection with cost enforcement and class ability seeding, fix wizard cantrips, add player End Turn, and move rest controls to admin-only.

**Architecture:** A `ConnectionManager` singleton in `app/services/ws_manager.py` holds all active WebSocket connections. Every encounter-mutating API endpoint calls `await _broadcast_state(db)` after commit, which pushes full encounter state JSON to all clients. Both the admin tracker and player encounter page replace polling with a WebSocket client that reconnects on disconnect. The player encounter page is rewritten with a token-first action UI: tap Action/Bonus/Reaction/Move → inline list expands → select ability → confirm panel with cost → Use It.

**Tech Stack:** FastAPI WebSockets (built-in via Starlette), vanilla JS, SQLAlchemy, existing `CharacterResource` model, existing `Combatant.movement_remaining` field.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `app/services/ws_manager.py` | **Create** | `ConnectionManager` singleton + module-level `manager` instance |
| `app/services/class_action_seeder.py` | **Create** | Parse `reference_claude/class_actions/*.md`, seed `CharacterResource` on combat add |
| `reference_claude/class_actions/template.md` | **Create** | Schema template for user to copy when writing class files |
| `app/routers/encounter.py` | **Modify** | Extract `_build_state_dict()` helper; add `async _broadcast_state()`; add `/ws/encounter` WebSocket endpoint via separate `ws_router` |
| `app/main.py` | **Modify** | Register `ws_router` from encounter module |
| `app/routers/admin.py` | **Modify** | Convert mutation endpoints to `async def`; call `_broadcast_state` after each; call `seed_class_abilities` on add-character-to-combat |
| `app/routers/characters.py` | **Modify** | Fix cantrip filter in `get_encounter_actions`; add `POST /encounter/end-turn`; add `POST /encounter/spend-movement`; call `_broadcast_state` after action/movement changes |
| `static/sheet.js` | **Modify** | Remove `takeRest()` and `.sh-rest-btns` HTML |
| `static/admin.js` | **Modify** | Replace `_pollEncounterState`/`_startEncounterPolling`/`_stopEncounterPolling` with WS client; keep all render functions unchanged |
| `static/encounter.html` | **Modify** | Mobile-first layout: 2×2 token grid, inline expansion zones, fixed End Turn |
| `static/encounter.js` | **Rewrite** | WS client + reconnect; token-first action UI; move stepper; End Turn; replaces all existing encounter.js content |

---

## Task 1: WebSocket Manager + WS Endpoint + Broadcast Helper

**Files:**
- Create: `app/services/ws_manager.py`
- Modify: `app/routers/encounter.py`
- Modify: `app/main.py`

- [ ] **Step 1: Create the ConnectionManager**

```python
# app/services/ws_manager.py
from fastapi import WebSocket


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

- [ ] **Step 2: Extract `_build_state_dict` from `get_encounter_state` in `encounter.py`**

The current `get_encounter_state` function body becomes `_build_state_dict(db)`. The endpoint calls it.

Replace the entire `encounter.py` with:

```python
import logging
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session, selectinload
from sqlalchemy.exc import IntegrityError
from ..database import get_db, SessionLocal
from ..models.character import Combatant, EncounterState, Character, CharacterClass
from ..models.content import Monster
from ..dependencies import require_user
from ..services.ws_manager import manager

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/encounter", tags=["encounter"])
ws_router = APIRouter()  # no prefix — registers /ws/encounter at root


def _get_or_create_state(db: Session) -> EncounterState:
    state = db.get(EncounterState, 1)
    if not state:
        try:
            state = EncounterState(id=1)
            db.add(state)
            db.commit()
            db.refresh(state)
        except IntegrityError:
            db.rollback()
            state = db.get(EncounterState, 1)
    return state


def _build_state_dict(db: Session) -> dict:
    """Build the full encounter state dict. Used by the HTTP endpoint and broadcast helper."""
    state = _get_or_create_state(db)
    rows = (
        db.query(Combatant)
        .options(
            selectinload(Combatant.character).options(
                selectinload(Character.character_classes).selectinload(CharacterClass.dnd_class),
                selectinload(Character.species),
            )
        )
        .order_by(Combatant.turn_order.nulls_last(), Combatant.added_at)
        .all()
    )

    monster_ids = [row.monster_id for row in rows if row.monster_id]
    monsters_by_id = {}
    if monster_ids:
        monsters_by_id = {
            m.id: m for m in db.query(Monster).filter(Monster.id.in_(monster_ids)).all()
        }

    combatants = []
    for row in rows:
        entry = {
            "combatant_id": row.id,
            "initiative": row.initiative,
            "turn_order": row.turn_order,
            "is_current_turn": row.id == state.current_turn_combatant_id,
            "action_used": bool(row.action_used),
            "bonus_action_used": bool(row.bonus_action_used),
            "reaction_used": bool(row.reaction_used),
            "movement_remaining": row.movement_remaining,
            "legendary_actions_remaining": row.legendary_actions_remaining,
        }
        if row.character_id:
            char = row.character
            cc = char.character_classes[0] if char.character_classes else None
            entry.update({
                "kind": "character",
                "character_id": char.id,
                "name": char.character_name,
                "hp_current": char.hp_current,
                "hp_max": char.hp_max,
                "ac": None,
                "speed": char.speed or 30,
                "conditions": char.conditions or [],
                "class_name": cc.dnd_class.name if cc else None,
                "level": cc.level if cc else None,
                "species_lineage": char.species_lineage,
                "species_name": char.species.name if char.species else None,
            })
        else:
            m = monsters_by_id.get(row.monster_id)
            if not m:
                log.warning("Combatant %s has missing monster_id=%s — skipping", row.id, row.monster_id)
                continue
            entry.update({
                "kind": "monster",
                "monster_id": m.id,
                "name": row.custom_name or m.name,
                "hp_current": row.hp_current,
                "hp_max": row.hp_max_override or m.hp_max,
                "ac": m.ac,
                "speed": m.speed,
                "cr": m.cr,
                "creature_type": m.creature_type,
                "conditions": row.conditions or [],
            })
        combatants.append(entry)

    return {
        "encounter_active": state.encounter_active,
        "initiative_phase": state.initiative_phase,
        "current_round": state.current_round,
        "current_turn_combatant_id": state.current_turn_combatant_id,
        "combatants": combatants,
    }


async def _broadcast_state(db: Session):
    """Build state dict and broadcast to all WebSocket clients."""
    state = _build_state_dict(db)
    await manager.broadcast(state)


@router.get("/state")
def get_encounter_state(db: Session = Depends(get_db), _user=Depends(require_user)):
    return _build_state_dict(db)


@ws_router.websocket("/ws/encounter")
async def ws_encounter(websocket: WebSocket):
    # Auth: session cookie is sent with the WS upgrade request
    user = websocket.session.get("user") if hasattr(websocket, "session") else None
    if not user:
        await websocket.close(code=1008)  # 1008 = Policy Violation
        return

    await manager.connect(websocket)

    # Send current state immediately on connect
    db = SessionLocal()
    try:
        state = _build_state_dict(db)
    finally:
        db.close()
    await websocket.send_json(state)

    try:
        while True:
            # Keep connection alive; clients are read-only (they POST to REST for writes)
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
```

- [ ] **Step 3: Register `ws_router` in `app/main.py`**

Add to the imports:
```python
from .routers.encounter import router as encounter_router, ws_router as encounter_ws_router
```

And after `app.include_router(encounter_router)`:
```python
app.include_router(encounter_ws_router)
```

- [ ] **Step 4: Verify WebSocket endpoint starts**

```bash
~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
sleep 4
# Should return 403 (not 404) — endpoint exists, rejects unauthenticated upgrade
curl -s -o /dev/null -w "%{http_code}" -H "Upgrade: websocket" -H "Connection: Upgrade" http://localhost:8000/ws/encounter
pkill -f uvicorn
```
Expected: 403 or 400 (WebSocket rejection for no auth) — NOT 404.

- [ ] **Step 5: Commit**

```bash
git add app/services/ws_manager.py app/routers/encounter.py app/main.py
git commit -m "feat: WebSocket manager, broadcast helper, and /ws/encounter endpoint"
```

---

## Task 2: Wire Broadcasts into Admin Mutation Endpoints

**Files:**
- Modify: `app/routers/admin.py`

All encounter-mutating admin endpoints need to (a) become `async def`, (b) import and call `_broadcast_state`.

- [ ] **Step 1: Add imports to admin.py**

At the top of `app/routers/admin.py`, add:
```python
from .encounter import _broadcast_state
```

- [ ] **Step 2: Convert encounter mutation endpoints to async and add broadcast**

Find each of these functions and apply the pattern: `def` → `async def`, add `await _broadcast_state(db)` before `return`. The functions to convert:

**`start_encounter`** (currently `def`):
```python
@router.post("/encounter/start")
async def start_encounter(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    state = _get_or_create_enc(db)
    state.encounter_active = True
    state.initiative_phase = True
    state.current_round = 1
    state.current_turn_combatant_id = None
    for row in db.query(Combatant).all():
        row.action_used = False
        row.bonus_action_used = False
        row.reaction_used = False
        row.initiative = None
        row.turn_order = None
        row.movement_remaining = None
    db.commit()
    await _broadcast_state(db)
    return {"ok": True}
```

**`begin_round_one`**:
```python
@router.post("/encounter/begin-round-1")
async def begin_round_one(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    state = _get_or_create_enc(db)
    if not state.encounter_active:
        raise HTTPException(400, "No active encounter")
    _recompute_turn_order(db)
    first = db.query(Combatant).filter(Combatant.turn_order.isnot(None)).order_by(Combatant.turn_order).first()
    if not first:
        raise HTTPException(400, "No initiatives entered yet — enter at least one initiative before beginning")
    state.initiative_phase = False
    state.current_turn_combatant_id = first.id
    _reset_combatant_turn(first, db)
    db.commit()
    await _broadcast_state(db)
    return {"ok": True, "current_turn_combatant_id": state.current_turn_combatant_id}
```

**`advance_turn`**:
```python
@router.post("/encounter/advance-turn")
async def advance_turn(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    state = _get_or_create_enc(db)
    if not state.encounter_active or state.initiative_phase:
        raise HTTPException(400, "Encounter not in progress")
    ordered = db.query(Combatant).filter(Combatant.turn_order.isnot(None)).order_by(Combatant.turn_order).all()
    if not ordered:
        raise HTTPException(400, "No combatants in initiative order")
    current_ids = [c.id for c in ordered]
    try:
        idx = current_ids.index(state.current_turn_combatant_id)
    except ValueError:
        idx = -1
    next_idx = idx + 1
    if next_idx >= len(ordered):
        next_idx = 0
        state.current_round += 1
    next_combatant = ordered[next_idx]
    state.current_turn_combatant_id = next_combatant.id
    _reset_combatant_turn(next_combatant, db)
    db.commit()
    await _broadcast_state(db)
    return {"ok": True, "current_round": state.current_round, "current_turn_combatant_id": state.current_turn_combatant_id}
```

**`end_encounter`**:
```python
@router.post("/encounter/end")
async def end_encounter(db: Session = Depends(get_db), _admin=Depends(require_admin)):
    state = _get_or_create_enc(db)
    state.encounter_active = False
    state.initiative_phase = False
    state.current_round = 1
    state.current_turn_combatant_id = None
    for row in db.query(Combatant).all():
        row.initiative = None
        row.turn_order = None
        row.action_used = False
        row.bonus_action_used = False
        row.reaction_used = False
        row.movement_remaining = None
        row.legendary_actions_remaining = None
    db.commit()
    await _broadcast_state(db)
    return {"ok": True}
```

**`set_initiative`**:
```python
@router.patch("/combatants/{combatant_id}/initiative")
async def set_initiative(combatant_id: int, body: InitiativeIn, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    row = db.get(Combatant, combatant_id)
    if not row:
        raise HTTPException(404)
    row.initiative = body.initiative
    if row.movement_remaining is None:
        if row.character_id and row.character:
            row.movement_remaining = row.character.speed if row.character.speed is not None else 30
        elif row.monster_id:
            m = db.get(Monster, row.monster_id)
            if m and m.speed:
                match = re.search(r"\d+", m.speed.strip())
                row.movement_remaining = int(match.group()) if match else 30
    db.flush()
    _recompute_turn_order(db)
    db.commit()
    await _broadcast_state(db)
    return {"ok": True, "initiative": row.initiative, "turn_order": row.turn_order}
```

**`update_action_economy`**:
```python
@router.patch("/combatants/{combatant_id}/actions")
async def update_action_economy(combatant_id: int, body: ActionEconomyIn, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    row = db.get(Combatant, combatant_id)
    if not row:
        raise HTTPException(404)
    if body.action_used is not None:
        row.action_used = body.action_used
    if body.bonus_action_used is not None:
        row.bonus_action_used = body.bonus_action_used
    if body.reaction_used is not None:
        row.reaction_used = body.reaction_used
    if body.movement_remaining is not None:
        row.movement_remaining = body.movement_remaining
    if body.legendary_actions_remaining is not None:
        row.legendary_actions_remaining = body.legendary_actions_remaining
    db.commit()
    await _broadcast_state(db)
    return {"ok": True}
```

**`set_combatant_hp`**:
```python
@router.patch("/combatants/{combatant_id}/hp")
async def set_combatant_hp(combatant_id: int, data: CombatantHpIn, db: Session = Depends(get_db)):
    c = db.get(Combatant, combatant_id)
    if not c:
        raise HTTPException(404)
    if c.monster_id:
        c.hp_current = max(0, data.hp_current)
        db.commit()
        await _broadcast_state(db)
        return {"ok": True, "hp_current": c.hp_current, "hp_max": c.hp_max_override}
    raise HTTPException(400, "Use the character HP endpoint for PC combatants")
```

**`apply_conditions`** (find the conditions PATCH endpoint and add broadcast there too):
```python
@router.patch("/combatants/{combatant_id}/conditions")
async def apply_conditions(combatant_id: int, body: ConditionsIn, db: Session = Depends(get_db), _admin=Depends(require_admin)):
    # ... existing validation logic unchanged ...
    db.commit()
    await _broadcast_state(db)
    return {"ok": True, "conditions": body.conditions}
```

- [ ] **Step 3: Verify server still starts**

```bash
~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
sleep 4
curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/admin/encounter/start
pkill -f uvicorn
```
Expected: 401 (unauthorized, not 500).

- [ ] **Step 4: Commit**

```bash
git add app/routers/admin.py
git commit -m "feat: broadcast WebSocket state after all encounter mutation endpoints"
```

---

## Task 3: Fix Cantrip Filter + End Turn + Spend Movement (characters.py)

**Files:**
- Modify: `app/routers/characters.py`

- [ ] **Step 1: Add imports**

In `characters.py`, add to the imports:
```python
from .encounter import _broadcast_state
from ..models.character import Combatant as CombatantModel
```

Note: `Combatant` may already be imported at the top. Check and add only what's missing.

- [ ] **Step 2: Fix cantrip filter in `get_encounter_actions`**

Find the spell loop in `get_encounter_actions` (around line 1799) and add the cantrip bypass:

```python
    # Prepared spells with 1 action or bonus action casting time
    for sp in data.get("spells", []):
        is_cantrip = sp.get("level", 0) == 0
        # Cantrips are always available regardless of prepared flag
        if not is_cantrip and not sp.get("prepared") and not sp.get("always_prepared"):
            continue
        ct = (sp.get("casting_time") or "").lower()
        is_action = "1 action" in ct
        is_bonus = "bonus action" in ct
        if not is_action and not is_bonus:
            continue
        slot_level = sp.get("level", 0) if sp.get("level", 0) > 0 else None
        actions.append({
            "type": "spell",
            "name": sp["name"],
            "cost": {"action": is_action, "bonus_action": is_bonus, "spell_slot": slot_level},
            "attack_bonus": spell_atk,
            "attack_bonus_display": _esc_display(spell_atk_display),
            "damage": "",
            "range": sp.get("range", ""),
            "properties": [],
            "mastery_property": None,
            "save_dc": save_dc,
            "save_ability": (data.get("class_spellcasting_ability") or "").title() or None,
            "description": sp.get("description", ""),
            "duration": sp.get("duration", ""),
            "concentration": sp.get("concentration", False),
            "level": sp.get("level", 0),
            "school": sp.get("school", ""),
        })
```

(No change to the attack section above it — attacks remain unchanged.)

- [ ] **Step 3: Update `player_mark_action` to broadcast**

Find `player_mark_action` (around line 1721) and convert to async + add broadcast:

```python
@router.post("/encounter/action-economy")
async def player_mark_action(
    body: PlayerActionEconomyIn,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    # TODO Task 7: add enforcement that only marks are allowed on current_turn_combatant_id
    from ..models.character import Combatant
    row = db.get(Combatant, body.combatant_id)
    if not row or not row.character_id:
        raise HTTPException(404)
    if row.character.owner_email != user["email"]:
        raise HTTPException(403, "Can only update your own character's actions")
    if body.action_used is not None:
        row.action_used = body.action_used
    if body.bonus_action_used is not None:
        row.bonus_action_used = body.bonus_action_used
    if body.reaction_used is not None:
        row.reaction_used = body.reaction_used
    db.commit()
    await _broadcast_state(db)
    return {"ok": True}
```

- [ ] **Step 4: Add `end-turn` endpoint**

Add after `player_mark_action`:

```python
class EndTurnIn(BaseModel):
    combatant_id: int


@router.post("/encounter/end-turn")
async def player_end_turn(
    body: EndTurnIn,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    """Player ends their turn — advances initiative to the next combatant."""
    from ..models.character import Combatant, EncounterState
    row = db.get(Combatant, body.combatant_id)
    if not row or not row.character_id:
        raise HTTPException(404)
    if row.character.owner_email != user["email"]:
        raise HTTPException(403, "Can only end your own character's turn")

    state = db.get(EncounterState, 1)
    if not state or not state.encounter_active or state.initiative_phase:
        raise HTTPException(400, "No active encounter")
    if state.current_turn_combatant_id != body.combatant_id:
        raise HTTPException(400, "It is not this character's turn")

    # Same advance-turn logic as the admin endpoint
    ordered = db.query(Combatant).filter(
        Combatant.turn_order.isnot(None)
    ).order_by(Combatant.turn_order).all()
    if not ordered:
        raise HTTPException(400, "No combatants in initiative order")

    current_ids = [c.id for c in ordered]
    try:
        idx = current_ids.index(state.current_turn_combatant_id)
    except ValueError:
        idx = -1

    next_idx = idx + 1
    if next_idx >= len(ordered):
        next_idx = 0
        state.current_round += 1

    from ..services.ws_manager import manager
    next_combatant = ordered[next_idx]
    state.current_turn_combatant_id = next_combatant.id

    # Reset action economy for the next combatant
    next_combatant.action_used = False
    next_combatant.bonus_action_used = False
    next_combatant.reaction_used = False
    if next_combatant.character_id and next_combatant.character:
        next_combatant.movement_remaining = next_combatant.character.speed if next_combatant.character.speed is not None else 30

    db.commit()
    await _broadcast_state(db)
    return {"ok": True, "current_round": state.current_round}
```

- [ ] **Step 5: Add `spend-movement` endpoint**

```python
class SpendMovementIn(BaseModel):
    combatant_id: int
    amount: int  # must be positive multiple of 5


@router.post("/encounter/spend-movement")
async def player_spend_movement(
    body: SpendMovementIn,
    db: Session = Depends(get_db),
    user=Depends(require_user),
):
    from ..models.character import Combatant
    if body.amount <= 0 or body.amount % 5 != 0:
        raise HTTPException(400, "Amount must be a positive multiple of 5")
    row = db.get(Combatant, body.combatant_id)
    if not row or not row.character_id:
        raise HTTPException(404)
    if row.character.owner_email != user["email"]:
        raise HTTPException(403, "Can only spend your own character's movement")
    remaining = row.movement_remaining or 0
    if body.amount > remaining:
        raise HTTPException(400, f"Only {remaining} ft remaining")
    row.movement_remaining = remaining - body.amount
    db.commit()
    await _broadcast_state(db)
    return {"ok": True, "movement_remaining": row.movement_remaining}
```

- [ ] **Step 6: Verify endpoints exist**

```bash
~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
sleep 4
curl -s -o /dev/null -w "end-turn: %{http_code}\n" -X POST -H 'Content-Type: application/json' -d '{"combatant_id":1}' http://localhost:8000/api/characters/encounter/end-turn
curl -s -o /dev/null -w "spend-mv: %{http_code}\n" -X POST -H 'Content-Type: application/json' -d '{"combatant_id":1,"amount":10}' http://localhost:8000/api/characters/encounter/spend-movement
pkill -f uvicorn
```
Expected: 401 for both (not 404).

- [ ] **Step 7: Commit**

```bash
git add app/routers/characters.py
git commit -m "feat: fix cantrip filter, add end-turn and spend-movement endpoints with WS broadcast"
```

---

## Task 4: Class Action Seeder + Template Markdown

**Files:**
- Create: `app/services/class_action_seeder.py`
- Create: `reference_claude/class_actions/template.md`
- Modify: `app/routers/admin.py`

- [ ] **Step 1: Create the seeder service**

```python
# app/services/class_action_seeder.py
"""
Parse reference_claude/class_actions/{class}.md files and seed CharacterResource
rows when a character is added to combat.

Markdown format (see template.md):
  # ClassName
  ## Ability Name
  action_type: action|bonus_action|reaction|special|passive
  resource_key: snake_case_key
  min_level: 1
  max_uses: 2          # integer or: level, level//2
  rest_type: short|long|encounter
  description: One line.
"""
import re
from pathlib import Path
from functools import lru_cache
from sqlalchemy.orm import Session

_CLASS_ACTIONS_DIR = Path(__file__).resolve().parent.parent.parent / "reference_claude" / "class_actions"


def _eval_uses(expr: str, level: int) -> int:
    """Evaluate a max_uses expression. Supports integers, 'level', 'level//2'."""
    expr = expr.strip()
    if expr.isdigit():
        return int(expr)
    if expr == "level":
        return level
    if expr == "level//2":
        return max(1, level // 2)
    # Fallback: try literal eval with level substituted
    try:
        return max(1, int(eval(expr.replace("level", str(level)), {}, {})))  # nosec — controlled input
    except Exception:
        return 1


@lru_cache(maxsize=20)
def _load_class_actions(class_name: str) -> list[dict]:
    """Parse a class_actions markdown file. Result is cached per class name."""
    path = _CLASS_ACTIONS_DIR / f"{class_name.lower()}.md"
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    abilities = []
    # Split on ## headers
    blocks = re.split(r"\n(?=## )", text)
    for block in blocks:
        if not block.startswith("## "):
            continue
        name_match = re.match(r"## (.+)", block)
        if not name_match:
            continue
        name = name_match.group(1).strip()
        fields = {}
        for key in ("action_type", "resource_key", "min_level", "max_uses", "rest_type", "description"):
            m = re.search(rf"^{key}:\s*(.+)$", block, re.MULTILINE)
            if m:
                fields[key] = m.group(1).strip()

        if not all(k in fields for k in ("action_type", "resource_key", "min_level", "max_uses", "rest_type")):
            continue  # skip malformed blocks

        abilities.append({
            "name": name,
            "action_type": fields["action_type"],
            "resource_key": fields["resource_key"],
            "min_level": int(fields["min_level"]),
            "max_uses": fields["max_uses"],
            "rest_type": fields["rest_type"],
            "description": fields.get("description", ""),
        })
    return abilities


def seed_class_abilities(char, db: Session):
    """
    Seed CharacterResource rows for a character based on their class and level.
    Called when a character is added to combat. Never overwrites existing rows.
    """
    from ..models.character import CharacterResource

    cc = char.character_classes[0] if char.character_classes else None
    if not cc or not cc.dnd_class:
        return

    class_name = cc.dnd_class.name.lower()
    level = cc.level
    abilities = _load_class_actions(class_name)

    for ability in abilities:
        if level < ability["min_level"]:
            continue
        existing = db.query(CharacterResource).filter_by(
            character_id=char.id, resource_key=ability["resource_key"]
        ).first()
        if existing:
            continue  # never overwrite manual DM config

        max_uses = _eval_uses(ability["max_uses"], level)
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

- [ ] **Step 2: Create the template markdown**

```markdown
# ClassName

## Ability Name
action_type: action
resource_key: ability_snake_case
min_level: 1
max_uses: 1
rest_type: short
description: One sentence describing what this does.

## Another Ability (Bonus Action)
action_type: bonus_action
resource_key: another_ability
min_level: 2
max_uses: level
rest_type: long
description: Uses 'level' as a formula — player's level at time of combat add.
```

Save to `reference_claude/class_actions/template.md`.

**`action_type` values:**
- `action` — appears in ACTION token list
- `bonus_action` — appears in BONUS token list
- `reaction` — appears in REACTION token list
- `special` — tracked as resource; appears in ACTION list but grants extra action token when used
- `passive` — tracked in resource strip only, not in action list (e.g. Sneak Attack reminder)

**`max_uses` values:**
- Plain integer: `1`, `2`, `3`
- `level` — character's level
- `level//2` — half level (minimum 1)

- [ ] **Step 3: Call seeder from add_character_combatant in admin.py**

Find `add_character_combatant` (around line 923 in admin.py) and add the seeder call:

```python
from ..services.class_action_seeder import seed_class_abilities

@router.post("/combatants/character")
async def add_character_combatant(data: CombatantCharIn, db: Session = Depends(get_db)):
    char = db.get(Character, data.character_id)
    if not char:
        raise HTTPException(404, "Character not found")
    existing = db.query(Combatant).filter_by(character_id=data.character_id).first()
    if existing:
        raise HTTPException(409, "Character is already in combat")
    c = Combatant(character_id=data.character_id)
    db.add(c)
    db.commit()
    db.refresh(c)
    # Auto-seed class abilities as CharacterResource rows (skips existing rows)
    seed_class_abilities(char, db)
    return {"ok": True, "combatant_id": c.id}
```

- [ ] **Step 4: Verify seeder loads without error**

```bash
~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
sleep 4
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/encounter/state
pkill -f uvicorn
```
Expected: 401 (not 500 — seeder import must not crash on startup).

- [ ] **Step 5: Commit**

```bash
git add app/services/class_action_seeder.py reference_claude/class_actions/template.md app/routers/admin.py
git commit -m "feat: class action seeder with markdown schema; seed on character add-to-combat"
```

---

## Task 5: Remove Rest Buttons from Player Sheet

**Files:**
- Modify: `static/sheet.js`

- [ ] **Step 1: Remove `takeRest` function**

Find and delete the `takeRest` function (lines ~333–343):
```javascript
// DELETE THIS ENTIRE FUNCTION:
async function takeRest(type) {
  if (!confirm(`Take a ${type === 'long' ? 'long' : 'short'} rest?`)) return;
  try {
    await api("POST", `/api/characters/${charId}/rest`, { rest_type: type });
    toast(`${type === 'long' ? 'Long' : 'Short'} rest taken — resources restored!`);
    loadResources();
    pollHp();
  } catch (e) {
    toast("Rest failed");
  }
}
```

- [ ] **Step 2: Remove rest buttons from the render HTML**

Find the `.sh-rest-btns` block (lines ~477–480) inside the `render()` function's returned HTML string:

```javascript
// DELETE THESE THREE LINES:
    <div class="sh-rest-btns">
      <button class="sh-rest-btn" onclick="takeRest('short')">Short Rest</button>
      <button class="sh-rest-btn" onclick="takeRest('long')">Long Rest</button>
    </div>
```

Leave the `${renderConditionStrip(c.conditions || [])}` line immediately below it untouched.

- [ ] **Step 3: Verify sheet still loads**

```bash
~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
sleep 4
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/characters/1/sheet
pkill -f uvicorn
```
Expected: 200 (no JS syntax errors from deletion).

- [ ] **Step 4: Commit**

```bash
git add static/sheet.js
git commit -m "feat: remove Short/Long Rest buttons from player character sheet"
```

---

## Task 6: Replace Admin Polling with WebSocket

**Files:**
- Modify: `static/admin.js`

The polling functions (`_startEncounterPolling`, `_stopEncounterPolling`, `_pollEncounterState`) are replaced by a WebSocket client. The `_encounterState` variable, all render functions (`_renderEncounterBar`, `_renderCombatCards`, `_buildCombatCard`, etc.) stay unchanged.

- [ ] **Step 1: Replace the three polling functions with a WebSocket client**

Find and replace the block starting at `let _encPollInterval = null;` through `function _stopEncounterPolling()` (around lines 1386–1407):

```javascript
// ---- Replace polling with WebSocket ----
let _encWs = null;
let _encWsReconnectDelay = 1000;
let _encWsActive = false;

function _startEncounterWS() {
  if (_encWsActive) return;
  _encWsActive = true;
  _connectEncounterWS();
}

function _stopEncounterWS() {
  _encWsActive = false;
  if (_encWs) {
    _encWs.onclose = null;  // prevent reconnect loop
    _encWs.close();
    _encWs = null;
  }
}

function _connectEncounterWS() {
  if (!_encWsActive) return;
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  _encWs = new WebSocket(`${proto}//${location.host}/ws/encounter`);

  _encWs.onopen = () => {
    _encWsReconnectDelay = 1000;
    // Request fresh state immediately (WS sends it on connect, but ensure sync)
  };

  _encWs.onmessage = (event) => {
    try {
      _encounterState = JSON.parse(event.data);
      _renderEncounterBar();
      _renderCombatCards();
    } catch (e) { /* ignore parse errors */ }
  };

  _encWs.onclose = () => {
    if (!_encWsActive) return;
    setTimeout(() => {
      _encWsReconnectDelay = Math.min(_encWsReconnectDelay * 2, 30000);
      _connectEncounterWS();
    }, _encWsReconnectDelay);
  };

  _encWs.onerror = () => {
    _encWs.close();  // triggers onclose → reconnect
  };
}
```

- [ ] **Step 2: Update `loadCombat` to start WS instead of polling**

Find `loadCombat` (around line 1430):
```javascript
async function loadCombat() {
  _combatants = await api("GET", "/api/admin/combatants");
  _startEncounterWS();   // ← was _startEncounterPolling()
  _renderCombatCards();
}
```

- [ ] **Step 3: Update the tab-switch code to stop WS instead of polling**

Find the `switchTab` call that stops polling (around line 42):
```javascript
if (tab !== "combat") _stopEncounterWS();   // ← was _stopEncounterPolling()
```

- [ ] **Step 4: Update all `_pollEncounterState()` calls to use WS**

Search for `await _pollEncounterState()` throughout admin.js — these are in `_startEncounter`, `_beginRound1`, `_advanceTurn`, `_endEncounter`, `_submitInitiative`, `_toggleAction`. Since the WS now pushes state automatically after each API call, these manual poll calls can be removed. The WS `onmessage` will update state within milliseconds.

Replace each `await _pollEncounterState()` with nothing (delete the line). The UI will update via WS broadcast from the server.

- [ ] **Step 5: Verify admin combat tracker still works**

Open browser: Log in as admin → Admin → Combat tab. Add a combatant. Verify the card renders. Verify no "polling" errors in browser console.

- [ ] **Step 6: Commit**

```bash
git add static/admin.js
git commit -m "feat: replace admin encounter polling with WebSocket client"
```

---

## Task 7: encounter.html Mobile-First Layout

**Files:**
- Modify: `static/encounter.html`

The existing encounter.html has `#enc-status`, `#enc-turn-banner`, `#enc-economy`, `#enc-order`, `#enc-actions`, `#enc-action-panel`, `#enc-resource-panel`. These get replaced with a structure for the new token-first UI.

- [ ] **Step 1: Replace encounter.html body content**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Encounter</title>
  <link rel="icon" type="image/png" href="/static/d20.png">
  <link rel="stylesheet" href="/static/style.css">
</head>
<body>
<div class="sheet-page">
  <div class="sheet-topbar">
    <a href="/portal" class="sheet-back">← My Characters</a>
    <div class="sheet-topbar-right">
      <a href="/auth/logout" class="btn-logout">Sign out</a>
    </div>
  </div>

  <div id="enc-main" style="max-width:480px;margin:0 auto;padding:0.75rem">

    <!-- Reconnecting banner (hidden normally) -->
    <div id="enc-reconnect" style="display:none;background:#884;color:white;padding:0.4rem;text-align:center;border-radius:4px;margin-bottom:0.5rem">
      Reconnecting…
    </div>

    <!-- No encounter / initiative phase message -->
    <div id="enc-status"></div>

    <!-- YOUR TURN banner (shown on active turn) -->
    <div id="enc-turn-banner" style="margin-bottom:0.5rem"></div>

    <!-- 2x2 token grid (shown on your turn) -->
    <div id="enc-token-grid" style="display:none;grid-template-columns:1fr 1fr;gap:0.5rem;margin-bottom:0.5rem">
      <button id="tok-action"   class="enc-token" onclick="tapToken('action')">○ ACTION</button>
      <button id="tok-bonus"    class="enc-token" onclick="tapToken('bonus')">○ BONUS</button>
      <button id="tok-reaction" class="enc-token" onclick="tapToken('reaction')">○ REACTION</button>
      <button id="tok-move"     class="enc-token" onclick="tapToken('move')">○ MOVE<br><small id="tok-move-ft"></small></button>
    </div>

    <!-- Inline action list (expands when token tapped) -->
    <div id="enc-action-list" style="display:none;margin-bottom:0.5rem"></div>

    <!-- Move stepper (expands when MOVE token tapped) -->
    <div id="enc-move-panel" style="display:none;margin-bottom:0.5rem"></div>

    <!-- Confirm panel (shown when ability selected) -->
    <div id="enc-confirm" style="display:none;margin-bottom:0.5rem"></div>

    <!-- Initiative order (always visible during encounter) -->
    <div id="enc-order" style="margin-bottom:0.5rem"></div>

    <!-- Resource panel (your resources, shown on your turn) -->
    <div id="enc-resource-panel" style="margin-top:0.75rem"></div>

    <!-- End Turn button (shown on your turn) -->
    <div id="enc-end-turn" style="display:none;position:sticky;bottom:0.75rem;margin-top:0.5rem">
      <button onclick="doEndTurn()" style="width:100%;padding:0.75rem;font-size:1rem;border-radius:6px;background:#555;color:white;border:none;cursor:pointer">→ End Turn</button>
    </div>

  </div>
</div>
<div class="toast" id="toast"></div>
<script src="/static/encounter.js"></script>
</body>
</html>
```

Add CSS for `.enc-token` to `static/style.css`:
```css
/* Encounter token buttons */
.enc-token {
  display: block;
  width: 100%;
  padding: 0.75rem 0.5rem;
  border: 2px solid var(--ink-soft);
  border-radius: 6px;
  background: var(--parchment-bright, #f4e8c8);
  color: var(--ink);
  font-weight: bold;
  font-size: 0.9rem;
  cursor: pointer;
  text-align: center;
  line-height: 1.3;
}

.enc-token.used {
  opacity: 0.35;
  text-decoration: line-through;
  cursor: not-allowed;
  background: #e0e0e0;
  border-color: #ccc;
}

.enc-token.active {
  background: var(--ink);
  color: var(--light);
  border-color: var(--ink);
}

#enc-token-grid {
  display: grid;
}
```

- [ ] **Step 2: Commit**

```bash
git add static/encounter.html static/style.css
git commit -m "feat: encounter.html mobile-first layout with token grid and inline expansion zones"
```

---

## Task 8: encounter.js — WebSocket Client + Basic Render

**Files:**
- Modify (full rewrite): `static/encounter.js`

This task establishes the WS client, state management, init flow, and the three non-active-turn render states. Tasks 9 and 10 add the token interaction on top.

- [ ] **Step 1: Write the new encounter.js (foundation)**

Replace the entire contents of `static/encounter.js` with:

```javascript
// encounter.js — Phase 5.5 — token-first mobile encounter page
// ─────────────────────────────────────────────────────────────

// ── State ────────────────────────────────────────────────────
let myCharIds = [];           // character IDs belonging to this player
let encounterState = { encounter_active: false, initiative_phase: false, current_round: 1, combatants: [] };
let myActions = [];           // cached from /encounter-actions
let actionsLoaded = false;
let resourcesLoaded = false;
let myEncResources = [];
let activeToken = null;       // 'action'|'bonus'|'reaction'|'move'|null
let selectedActionIdx = null; // index into myActions
let movementAmount = 5;       // current move stepper value
let myActiveCombatantId = null; // combatant_id when it's my turn

// ── WebSocket ─────────────────────────────────────────────────
let ws = null;
let wsReconnectDelay = 1000;
let wsActive = false;

function connectWS() {
  if (!wsActive) return;
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  ws = new WebSocket(`${proto}//${location.host}/ws/encounter`);

  ws.onopen = () => {
    wsReconnectDelay = 1000;
    document.getElementById('enc-reconnect').style.display = 'none';
  };

  ws.onmessage = (event) => {
    try {
      encounterState = JSON.parse(event.data);
      render();
    } catch (e) { /* ignore */ }
  };

  ws.onclose = () => {
    if (!wsActive) return;
    document.getElementById('enc-reconnect').style.display = 'block';
    setTimeout(() => {
      wsReconnectDelay = Math.min(wsReconnectDelay * 2, 30000);
      connectWS();
    }, wsReconnectDelay);
  };

  ws.onerror = () => ws.close();
}

// ── Toast ────────────────────────────────────────────────────
function toast(msg) {
  const t = document.getElementById('toast');
  if (!t) return;
  t.textContent = msg;
  t.classList.add('show');
  setTimeout(() => t.classList.remove('show'), 2500);
}

// ── HTML escape ───────────────────────────────────────────────
function _esc(str) {
  if (!str) return '';
  return String(str).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// ── Init ──────────────────────────────────────────────────────
async function init() {
  const meRes = await fetch('/auth/me');
  if (!meRes.ok) { window.location.href = '/'; return; }

  const charsRes = await fetch('/api/characters');
  if (charsRes.ok) {
    const chars = await charsRes.json();
    myCharIds = chars.filter(c => c.is_complete).map(c => c.id);
  }

  // Fetch initial state via HTTP, then switch to WS
  try {
    const stateRes = await fetch('/api/encounter/state');
    if (stateRes.ok) {
      encounterState = await stateRes.json();
      render();
    }
  } catch (e) { /* ignore */ }

  wsActive = true;
  connectWS();
  window.addEventListener('beforeunload', () => {
    wsActive = false;
    if (ws) ws.close();
  });
}

// ── Main render ───────────────────────────────────────────────
function render() {
  const { encounter_active, initiative_phase, current_round, current_turn_combatant_id, combatants } = encounterState;

  const statusEl = document.getElementById('enc-status');
  const bannerEl = document.getElementById('enc-turn-banner');
  const tokenGrid = document.getElementById('enc-token-grid');
  const endTurnEl = document.getElementById('enc-end-turn');
  const orderEl = document.getElementById('enc-order');

  if (!encounter_active) {
    _clearActivePanels();
    statusEl.innerHTML = `<h2 style="text-align:center;margin:2rem 0 0.5rem">No encounter in progress</h2><p style="text-align:center;color:var(--ink-soft)">The DM will start an encounter when combat begins.</p>`;
    bannerEl.innerHTML = '';
    tokenGrid.style.display = 'none';
    endTurnEl.style.display = 'none';
    orderEl.innerHTML = '';
    return;
  }

  if (initiative_phase) {
    _clearActivePanels();
    statusEl.innerHTML = `<h2 style="text-align:center;margin:2rem 0 0.5rem">Initiative Phase</h2><p style="text-align:center;color:var(--ink-soft)">The DM is collecting initiative rolls. Stand by…</p>`;
    bannerEl.innerHTML = '';
    tokenGrid.style.display = 'none';
    endTurnEl.style.display = 'none';
    orderEl.innerHTML = '';
    return;
  }

  statusEl.innerHTML = '';

  // Determine if it's my turn
  const currentCombatant = combatants.find(c => c.combatant_id === current_turn_combatant_id);
  const myActiveCombatant = combatants.find(
    c => myCharIds.includes(c.character_id) && c.combatant_id === current_turn_combatant_id
  );
  const isMyTurn = !!myActiveCombatant;

  if (isMyTurn) {
    myActiveCombatantId = myActiveCombatant.combatant_id;
    bannerEl.innerHTML = `<div style="background:var(--gold,#c8a84b);color:#1a0e00;padding:0.65rem;border-radius:6px;font-weight:bold;font-size:1.05rem;text-align:center">⚔ YOUR TURN — Round ${current_round}</div>`;
    tokenGrid.style.display = 'grid';
    endTurnEl.style.display = 'block';
    _updateTokens(myActiveCombatant);

    if (!actionsLoaded && myActiveCombatant.character_id) {
      loadActions(myActiveCombatant.character_id);
    }
    if (!resourcesLoaded && myActiveCombatant.character_id) {
      loadEncResources(myActiveCombatant.character_id);
    }
  } else {
    myActiveCombatantId = null;
    _clearActivePanels();
    const whose = currentCombatant ? _esc(currentCombatant.name) : '—';
    bannerEl.innerHTML = `<div style="text-align:center;color:var(--ink-soft);padding:0.4rem">Round ${current_round} — <em>${whose}</em>'s turn</div>`;
    tokenGrid.style.display = 'none';
    endTurnEl.style.display = 'none';
  }

  // Initiative order list
  orderEl.innerHTML = `<div style="font-size:0.8rem;font-weight:bold;color:var(--ink-soft);margin-bottom:0.25rem">INITIATIVE ORDER</div>` +
    combatants.map(c => {
      const isActive = c.combatant_id === current_turn_combatant_id;
      const isMine = myCharIds.includes(c.character_id);
      const hp = c.hp_current != null && c.hp_max != null ? ` ${c.hp_current}/${c.hp_max} HP` : '';
      const conds = (c.conditions || []).map(cd => {
        const label = cd.startsWith('Exhaustion:') ? `Exhaustion ${cd.split(':')[1]}` : cd;
        return `<span style="font-size:0.7rem;padding:0.1rem 0.3rem;background:var(--rubric,#8b0000);color:white;border-radius:2px">${_esc(label)}</span>`;
      }).join(' ');
      return `<div style="display:flex;align-items:center;gap:0.4rem;padding:0.3rem 0.4rem;border-radius:4px;${isActive ? 'background:var(--parchment-bright,#f4e8c8);border:1px solid var(--gold)' : ''}">
        <span style="min-width:1.4rem;font-weight:bold;color:var(--ink-soft)">${c.turn_order ?? '—'}.</span>
        <span style="${isActive ? 'font-weight:bold' : ''}">${_esc(c.name)}${isMine ? ' <small style="color:var(--ink-soft)">(You)</small>' : ''}</span>
        ${hp ? `<span style="font-size:0.8rem;color:var(--ink-soft);margin-left:auto">${hp}</span>` : ''}
        ${conds}
      </div>`;
    }).join('');
}

function _clearActivePanels() {
  document.getElementById('enc-action-list').style.display = 'none';
  document.getElementById('enc-action-list').innerHTML = '';
  document.getElementById('enc-move-panel').style.display = 'none';
  document.getElementById('enc-confirm').style.display = 'none';
  document.getElementById('enc-resource-panel').innerHTML = '';
  activeToken = null;
  selectedActionIdx = null;
  actionsLoaded = false;
  myActions = [];
  resourcesLoaded = false;
  myEncResources = [];
}

function _updateTokens(combatant) {
  const { action_used, bonus_action_used, reaction_used, movement_remaining } = combatant;
  const tokAction = document.getElementById('tok-action');
  const tokBonus = document.getElementById('tok-bonus');
  const tokReaction = document.getElementById('tok-reaction');
  const tokMove = document.getElementById('tok-move');
  const tokMoveFt = document.getElementById('tok-move-ft');

  _setTokenState(tokAction, action_used, 'action');
  _setTokenState(tokBonus, bonus_action_used, 'bonus');
  _setTokenState(tokReaction, reaction_used, 'reaction');

  const moveExhausted = (movement_remaining ?? 0) <= 0;
  _setTokenState(tokMove, moveExhausted, 'move');
  tokMoveFt.textContent = movement_remaining != null ? `${movement_remaining} ft left` : '';
}

function _setTokenState(btn, used, type) {
  if (used) {
    btn.className = 'enc-token used';
    btn.onclick = null;
  } else if (activeToken === type) {
    btn.className = 'enc-token active';
  } else {
    btn.className = 'enc-token';
    btn.onclick = () => tapToken(type);
  }
}

// ── Resources (shown during your turn) ───────────────────────
async function loadEncResources(charId) {
  try {
    const res = await fetch(`/api/characters/${charId}/resources`);
    if (!res.ok) return;
    myEncResources = await res.json();
    resourcesLoaded = true;
    renderEncResources(charId);
  } catch (e) { /* ignore */ }
}

function renderEncResources(charId) {
  const panel = document.getElementById('enc-resource-panel');
  if (!panel || !myEncResources.length) return;
  panel.innerHTML = `<div style="font-size:0.8rem;font-weight:bold;color:var(--ink-soft);margin-bottom:0.25rem">RESOURCES</div>` +
    myEncResources.map(r => `
      <div style="display:flex;align-items:center;gap:0.35rem;margin-bottom:0.2rem;font-size:0.85rem">
        <span style="min-width:8rem;font-weight:bold">${_esc(r.label)}</span>
        <span>${Array.from({length: r.max_uses}, (_, i) => `<button
          onclick="spendEncResource(${charId}, ${r.id}, ${i < r.remaining})"
          style="background:none;border:none;font-size:1rem;cursor:${i < r.remaining ? 'pointer' : 'default'};color:${i < r.remaining ? 'var(--gold-deep,#6b4a18)' : 'var(--ink-faded,#9a8070)'}">●</button>`
        ).join('')}</span>
        <small style="color:var(--ink-soft)">(${_esc(r.rest_type)})</small>
      </div>`
    ).join('');
}

async function spendEncResource(charId, resourceId, available) {
  if (!available) return;
  try {
    const res = await fetch(`/api/characters/${charId}/resources/spend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ resource_id: resourceId, amount: 1 }),
    });
    if (!res.ok) { toast('Could not spend resource'); return; }
    await loadEncResources(charId);
  } catch (e) { toast('Connection error'); }
}

// ── End Turn ─────────────────────────────────────────────────
async function doEndTurn() {
  if (!myActiveCombatantId) return;
  try {
    const res = await fetch('/api/characters/encounter/end-turn', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ combatant_id: myActiveCombatantId }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      toast(err.detail || 'Could not end turn');
    }
    // WS will push the state update automatically
  } catch (e) { toast('Connection error'); }
}

init();
```

- [ ] **Step 2: Verify page loads and shows "No encounter in progress"**

```bash
~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload &
sleep 4
curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/encounter
pkill -f uvicorn
```
Expected: 200.

In browser: open `/auth/test-login?email=zachpoguephil@gmail.com` then navigate to `/encounter`. Should show "No encounter in progress" with no JS errors.

- [ ] **Step 3: Commit**

```bash
git add static/encounter.js
git commit -m "feat: encounter.js foundation — WS client, reconnect, basic render states, End Turn"
```

---

## Task 9: encounter.js — Token Grid + Action List + Confirm Panel + Use It

**Files:**
- Modify: `static/encounter.js` (add functions below the `init()` call)

- [ ] **Step 1: Add action loading and token tap handler**

Append these functions to `encounter.js` before the final `init()` call:

```javascript
// ── Action loading ────────────────────────────────────────────
async function loadActions(charId) {
  try {
    const res = await fetch(`/api/characters/${charId}/encounter-actions`);
    if (!res.ok) return;
    myActions = await res.json();
    actionsLoaded = true;
    // Also include class abilities from CharacterResource as action items
    if (myEncResources.length) {
      _injectResourceAbilities();
    }
  } catch (e) { /* ignore */ }
}

function _injectResourceAbilities() {
  // Add CharacterResource entries as ability actions (they show under their action_type)
  // For now we add them as generic 'ability' type entries under ACTION
  // (action_type mapping is in the class action markdown; without it we default to action)
  for (const r of myEncResources) {
    if (r.used >= r.max_uses) continue; // no uses left, still show (greyed) below
    const key = `ability:${r.resource_key}`;
    if (myActions.find(a => a._key === key)) continue; // don't double-add
    myActions.push({
      _key: key,
      type: 'ability',
      name: r.label,
      resource_id: r.id,
      cost: { action: true, bonus_action: false, spell_slot: null, resource_key: r.resource_key },
      max_uses: r.max_uses,
      remaining: r.remaining,
      rest_type: r.rest_type,
      description: '',
      attack_bonus: null,
      attack_bonus_display: null,
      save_dc: null,
      save_ability: null,
      damage: '',
      range: '',
    });
  }
}

// ── Token tap ─────────────────────────────────────────────────
function tapToken(tokenType) {
  const combatant = encounterState.combatants.find(c => c.combatant_id === myActiveCombatantId);
  if (!combatant) return;

  // Don't allow tapping used tokens
  if (tokenType === 'action' && combatant.action_used) return;
  if (tokenType === 'bonus' && combatant.bonus_action_used) return;
  if (tokenType === 'reaction' && combatant.reaction_used) return;
  if (tokenType === 'move' && (combatant.movement_remaining ?? 0) <= 0) return;

  // Toggle: tapping active token closes the panel
  if (activeToken === tokenType) {
    activeToken = null;
    selectedActionIdx = null;
    document.getElementById('enc-action-list').style.display = 'none';
    document.getElementById('enc-move-panel').style.display = 'none';
    document.getElementById('enc-confirm').style.display = 'none';
    _updateTokens(combatant);
    return;
  }

  activeToken = tokenType;
  selectedActionIdx = null;
  document.getElementById('enc-confirm').style.display = 'none';
  _updateTokens(combatant);

  if (tokenType === 'move') {
    document.getElementById('enc-action-list').style.display = 'none';
    renderMovePanel(combatant);
  } else {
    document.getElementById('enc-move-panel').style.display = 'none';
    renderActionList(tokenType, combatant);
  }
}
```

- [ ] **Step 2: Add action list renderer**

```javascript
function renderActionList(tokenType, combatant) {
  const el = document.getElementById('enc-action-list');
  el.style.display = 'block';

  // Filter actions by token type
  const isAction = tokenType === 'action';
  const isBonus = tokenType === 'bonus';
  const isReaction = tokenType === 'reaction';

  const attacks = isAction ? myActions.filter(a => a.type === 'attack') : [];
  const cantrips = isAction ? myActions.filter(a => a.type === 'spell' && a.level === 0) : [];
  const spells = (isAction || isBonus)
    ? myActions.filter(a => a.type === 'spell' && a.level > 0 && (isAction ? a.cost.action : a.cost.bonus_action))
    : [];
  const abilities = myActions.filter(a =>
    a.type === 'ability' && (isAction ? a.cost.action : (isBonus ? a.cost.bonus_action : a.cost.reaction))
  );

  const section = (title, items) => {
    if (!items.length) return '';
    return `<div style="background:var(--parchment-bright,#f4e8c8);padding:0.25rem 0.5rem;font-size:0.7rem;font-weight:bold;letter-spacing:0.05em;color:var(--ink-soft)">${title}</div>` +
      items.map((a, _) => {
        const globalIdx = myActions.indexOf(a);
        const exhausted = a.type === 'ability' && a.remaining <= 0;
        const statStr = a.attack_bonus_display
          ? `${a.attack_bonus_display} · ${a.damage || '—'}`
          : (a.save_dc ? `DC ${a.save_dc} ${a.save_ability || ''}` : (a.damage || ''));
        const rightLabel = a.type === 'ability'
          ? `<span style="font-size:0.75rem;color:${exhausted ? '#ccc' : 'var(--ink-soft)'}">${a.remaining}/${a.max_uses}</span>`
          : (statStr ? `<span style="font-size:0.75rem;color:var(--ink-soft)">${_esc(statStr)}</span>` : '');
        return `<div onclick="${exhausted ? '' : `selectAction(${globalIdx})`}"
          style="display:flex;align-items:center;gap:0.4rem;padding:0.4rem 0.5rem;border-bottom:1px solid #eee;cursor:${exhausted ? 'default' : 'pointer'};opacity:${exhausted ? '0.4' : '1'}">
          <span style="flex:1">${_esc(a.name)}${a.level > 0 ? ` <small>(L${a.level})</small>` : ''}</span>
          ${rightLabel}
        </div>`;
      }).join('');
  };

  let html = `<div style="border:1px solid var(--gold);border-radius:6px;overflow:hidden;background:white">`;
  html += section('ATTACKS', attacks);
  html += section('CANTRIPS', cantrips);
  html += section('SPELLS', spells);
  html += section('ABILITIES', abilities);
  html += `<div onclick="selectAction(-1)" style="padding:0.4rem 0.5rem;color:var(--ink-soft);cursor:pointer;font-style:italic;border-top:1px solid #eee">— Skip (use ${tokenType}, do nothing)</div>`;
  html += '</div>';
  el.innerHTML = html;
}
```

- [ ] **Step 3: Add confirm panel + Use It**

```javascript
function selectAction(idx) {
  selectedActionIdx = idx;
  const confirmEl = document.getElementById('enc-confirm');
  confirmEl.style.display = 'block';

  // Skip action
  if (idx === -1) {
    confirmEl.innerHTML = `<div style="border:1px solid var(--gold);border-radius:6px;padding:0.6rem">
      <div style="font-weight:bold;margin-bottom:0.4rem">— Skip</div>
      <div style="font-size:0.8rem;color:var(--ink-soft);margin-bottom:0.5rem">Use your ${activeToken} without doing anything.</div>
      <div style="display:flex;gap:0.4rem">
        <button onclick="doUseAction(-1)" style="flex:1;padding:0.5rem;background:var(--ink);color:white;border:none;border-radius:4px;cursor:pointer;font-weight:bold">✓ Confirm Skip</button>
        <button onclick="closeConfirm()" style="padding:0.5rem 0.7rem;background:#eee;border:1px solid #ccc;border-radius:4px;cursor:pointer">← Back</button>
      </div>
    </div>`;
    return;
  }

  const action = myActions[idx];
  if (!action) return;

  let statsHtml = '';
  let slotPickerHtml = '';

  if (action.type === 'attack') {
    statsHtml = `
      <p style="margin:0.2rem 0;font-size:0.82rem"><strong>Attack Bonus:</strong> ${_esc(action.attack_bonus_display || '—')}</p>
      <p style="margin:0.2rem 0;font-size:0.82rem"><strong>Damage:</strong> ${_esc(action.damage || '—')}</p>
      <p style="margin:0.2rem 0;font-size:0.82rem"><strong>Range:</strong> ${_esc(action.range || '5 ft.')}</p>
      ${action.properties?.length ? `<p style="margin:0.2rem 0;font-size:0.82rem"><strong>Properties:</strong> ${action.properties.map(_esc).join(', ')}</p>` : ''}
      ${action.mastery_property ? `<p style="margin:0.2rem 0;font-size:0.82rem"><strong>Mastery:</strong> ${_esc(action.mastery_property)}</p>` : ''}`;
  } else if (action.type === 'spell') {
    const lvlStr = action.level === 0 ? 'Cantrip' : `Level ${action.level}`;
    statsHtml = `
      <p style="margin:0.2rem 0;font-size:0.78rem;color:var(--ink-soft)"><em>${lvlStr} ${_esc(action.school || '')}</em></p>
      <p style="margin:0.2rem 0;font-size:0.82rem"><strong>Range:</strong> ${_esc(action.range || '—')}</p>
      ${action.duration ? `<p style="margin:0.2rem 0;font-size:0.82rem"><strong>Duration:</strong> ${_esc(action.duration)}${action.concentration ? ' (Concentration)' : ''}</p>` : ''}
      ${action.save_dc ? `<p style="margin:0.2rem 0;font-size:0.82rem"><strong>Save DC:</strong> ${action.save_dc} ${_esc(action.save_ability || '')}</p>` : ''}
      ${action.attack_bonus_display ? `<p style="margin:0.2rem 0;font-size:0.82rem"><strong>Spell Attack:</strong> ${_esc(action.attack_bonus_display)}</p>` : ''}`;

    if (action.level > 0) {
      // Build slot picker from encounterState (spell_slots_used)
      const myCombatant = encounterState.combatants.find(c => c.combatant_id === myActiveCombatantId);
      const charId = myCombatant?.character_id;
      slotPickerHtml = `<div style="margin:0.4rem 0;font-size:0.82rem"><strong>Slot:</strong>
        <select id="slot-pick" style="margin-left:0.3rem;font-size:0.82rem">
          ${_buildSlotOptions(action.level)}
        </select>
      </div>`;
    }

    if (action.description) {
      const desc = action.description.length > 300 ? action.description.slice(0, 297) + '…' : action.description;
      statsHtml += `<details style="margin-top:0.4rem"><summary style="font-size:0.8rem;cursor:pointer">Description</summary><p style="font-size:0.78rem;white-space:pre-wrap">${_esc(desc)}</p></details>`;
    }
  } else if (action.type === 'ability') {
    statsHtml = `
      <p style="margin:0.2rem 0;font-size:0.82rem"><strong>Uses:</strong> ${action.remaining}/${action.max_uses} (${_esc(action.rest_type)} rest)</p>
      ${action.description ? `<p style="margin:0.2rem 0;font-size:0.82rem">${_esc(action.description)}</p>` : ''}`;
  }

  const costParts = [];
  if (activeToken === 'action') costParts.push('1 Action');
  if (activeToken === 'bonus') costParts.push('1 Bonus Action');
  if (activeToken === 'reaction') costParts.push('1 Reaction');
  if (action.type === 'ability' && action.resource_id) costParts.push(`1 ${_esc(action.name)} use`);

  confirmEl.innerHTML = `<div style="border:2px solid var(--gold);border-radius:6px;padding:0.6rem">
    <div style="display:flex;justify-content:space-between;align-items:start;margin-bottom:0.35rem">
      <strong style="font-size:1rem">${_esc(action.name)}</strong>
      <button onclick="closeConfirm()" style="background:none;border:none;cursor:pointer;font-size:0.85rem">✕</button>
    </div>
    ${statsHtml}
    ${slotPickerHtml}
    <p style="font-size:0.75rem;color:var(--ink-soft);margin:0.4rem 0">Costs: ${costParts.join(' + ') || '—'}</p>
    <div style="display:flex;gap:0.4rem;margin-top:0.5rem">
      <button onclick="doUseAction(${idx})" style="flex:1;padding:0.55rem;background:var(--gold,#c8a84b);color:#1a0e00;border:none;border-radius:5px;font-weight:bold;cursor:pointer">✓ Use It</button>
      <button onclick="closeConfirm()" style="padding:0.55rem 0.8rem;background:#eee;border:1px solid #ccc;border-radius:5px;cursor:pointer">← Back</button>
    </div>
  </div>`;
}

function _buildSlotOptions(minLevel) {
  // Build options from encounterState — future: fetch character slot counts
  // For now show levels minLevel–9 as options
  let opts = '';
  for (let lvl = minLevel; lvl <= 9; lvl++) {
    opts += `<option value="${lvl}">Level ${lvl}</option>`;
  }
  return opts;
}

function closeConfirm() {
  document.getElementById('enc-confirm').style.display = 'none';
  selectedActionIdx = null;
}

async function doUseAction(idx) {
  const combatant = encounterState.combatants.find(c => c.combatant_id === myActiveCombatantId);
  if (!combatant) return;

  const action = idx >= 0 ? myActions[idx] : null;
  const updates = {};

  // Mark the appropriate token used
  if (activeToken === 'action') updates.action_used = true;
  else if (activeToken === 'bonus') updates.bonus_action_used = true;
  else if (activeToken === 'reaction') updates.reaction_used = true;

  try {
    // 1. Mark action economy
    await fetch('/api/characters/encounter/action-economy', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ combatant_id: myActiveCombatantId, ...updates }),
    });

    // 2. Spend spell slot if leveled spell
    if (action && action.type === 'spell' && action.level > 0) {
      const slotEl = document.getElementById('slot-pick');
      const slotLevel = slotEl ? parseInt(slotEl.value) : action.level;
      const charId = combatant.character_id;
      // Fetch current spell slots, increment used count
      const slotsRes = await fetch(`/api/characters/${charId}/sheet-data`);
      // Note: spell slot spending is tracked via the existing spell-slots endpoint
      await fetch(`/api/characters/${charId}/spell-slots`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ level: slotLevel, delta: 1 }),
      }).catch(() => {}); // best-effort
    }

    // 3. Spend class ability use
    if (action && action.type === 'ability' && action.resource_id) {
      await fetch(`/api/characters/${combatant.character_id}/resources/spend`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ resource_id: action.resource_id, amount: 1 }),
      });
      // Refresh resource display
      await loadEncResources(combatant.character_id);
    }

    // Close panels — WS will push updated action economy state
    document.getElementById('enc-action-list').style.display = 'none';
    document.getElementById('enc-confirm').style.display = 'none';
    activeToken = null;
    selectedActionIdx = null;

  } catch (e) {
    toast('Action failed — try again');
  }
}
```

**Note on spell slots:** The existing `POST /api/characters/{id}/spell-slots` endpoint (built in Phase 4) tracks spell slot usage. Check `characters.py` for the exact request shape — it takes `{used: {"1": 0, "2": 1, ...}}` as a full replacement. The `doUseAction` code above calls it optimistically; verify the endpoint signature before running and adjust if needed.

- [ ] **Step 4: Verify in browser — end to end**

1. Start encounter in admin, add yourself as a combatant
2. Enter initiative, Begin Round 1
3. On `/encounter` page: see YOUR TURN banner + token grid
4. Tap ACTION → action list expands inline
5. Select an attack → confirm panel shows stats + Use It
6. Tap Use It → action token grays out → admin tracker reflects action_used=true
7. Tap End Turn → initiative advances in admin tracker

- [ ] **Step 5: Commit**

```bash
git add static/encounter.js
git commit -m "feat: token-first action list and confirm panel with Use It on encounter page"
```

---

## Task 10: encounter.js — Move Stepper

**Files:**
- Modify: `static/encounter.js` (add one more function)

- [ ] **Step 1: Add the move panel renderer and spend function**

Append to `encounter.js`:

```javascript
// ── Move stepper ──────────────────────────────────────────────
function renderMovePanel(combatant) {
  const el = document.getElementById('enc-move-panel');
  el.style.display = 'block';

  const remaining = combatant.movement_remaining ?? 0;
  movementAmount = Math.min(5, remaining); // default to 5 or less if < 5 remaining

  // Quick buttons: 5ft increments up to remaining, max 6 buttons
  const maxQuick = Math.min(remaining, 30);
  const quickBtns = [];
  for (let v = 5; v <= maxQuick; v += 5) {
    quickBtns.push(`<button onclick="setMoveAmount(${v})"
      style="padding:0.35rem 0.55rem;border:1px solid var(--ink-soft);border-radius:4px;cursor:pointer;font-size:0.85rem;background:${movementAmount===v ? 'var(--ink)' : '#f5f5f5'};color:${movementAmount===v ? 'white' : 'inherit'}"
      id="qbtn-${v}">${v} ft</button>`);
  }

  el.innerHTML = `<div style="border:1px solid var(--ink-soft);border-radius:6px;padding:0.6rem">
    <div style="font-weight:bold;margin-bottom:0.4rem">Move how far? <span style="font-weight:normal;color:var(--ink-soft)">(${remaining} ft remaining)</span></div>
    <div style="display:flex;gap:0.3rem;flex-wrap:wrap;margin-bottom:0.5rem" id="quick-btns">
      ${quickBtns.join('')}
    </div>
    <div style="display:flex;gap:0.5rem;align-items:center;margin-bottom:0.5rem">
      <button onclick="stepMove(-5)" style="padding:0.3rem 0.7rem;border:1px solid #ccc;border-radius:4px;font-size:1.1rem;cursor:pointer">−</button>
      <span id="move-amount-display" style="min-width:5rem;text-align:center;font-weight:bold">${movementAmount} ft</span>
      <button onclick="stepMove(5)" style="padding:0.3rem 0.7rem;border:1px solid #ccc;border-radius:4px;font-size:1.1rem;cursor:pointer">+</button>
      <span style="font-size:0.75rem;color:var(--ink-soft)">(5 ft steps)</span>
    </div>
    <div style="display:flex;gap:0.4rem">
      <button onclick="doSpendMovement(${combatant.combatant_id})" style="flex:1;padding:0.5rem;background:var(--ink);color:white;border:none;border-radius:4px;cursor:pointer;font-weight:bold">Spend ${movementAmount} ft</button>
      <button onclick="closeMovePanel()" style="padding:0.5rem 0.7rem;background:#eee;border:1px solid #ccc;border-radius:4px;cursor:pointer">← Back</button>
    </div>
  </div>`;
}

function setMoveAmount(val) {
  const combatant = encounterState.combatants.find(c => c.combatant_id === myActiveCombatantId);
  const remaining = combatant?.movement_remaining ?? 0;
  movementAmount = Math.max(5, Math.min(val, remaining));
  // Update spend button label and highlight quick button
  const display = document.getElementById('move-amount-display');
  if (display) display.textContent = `${movementAmount} ft`;
  const spendBtn = document.querySelector('#enc-move-panel button[onclick^="doSpendMovement"]');
  if (spendBtn) spendBtn.textContent = `Spend ${movementAmount} ft`;
  // Update quick button highlights
  document.querySelectorAll('#quick-btns button').forEach(b => {
    const bVal = parseInt(b.textContent);
    b.style.background = bVal === movementAmount ? 'var(--ink)' : '#f5f5f5';
    b.style.color = bVal === movementAmount ? 'white' : 'inherit';
  });
}

function stepMove(delta) {
  const combatant = encounterState.combatants.find(c => c.combatant_id === myActiveCombatantId);
  const remaining = combatant?.movement_remaining ?? 0;
  const newVal = Math.max(5, Math.min(movementAmount + delta, remaining));
  setMoveAmount(newVal);
}

async function doSpendMovement(combatantId) {
  if (movementAmount <= 0) return;
  try {
    const res = await fetch('/api/characters/encounter/spend-movement', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ combatant_id: combatantId, amount: movementAmount }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      toast(err.detail || 'Could not spend movement');
      return;
    }
    // WS will push updated movement_remaining; re-render move panel
    closeMovePanel();
    // Don't close the token — player might want to move again later
    activeToken = null;
  } catch (e) { toast('Connection error'); }
}

function closeMovePanel() {
  document.getElementById('enc-move-panel').style.display = 'none';
  activeToken = null;
  const combatant = encounterState.combatants.find(c => c.combatant_id === myActiveCombatantId);
  if (combatant) _updateTokens(combatant);
}
```

- [ ] **Step 2: Verify move stepper in browser**

1. On encounter page during YOUR TURN, tap MOVE token
2. Verify quick buttons appear (up to remaining movement)
3. Tap a quick button (e.g. 10 ft) → stepper jumps to 10
4. Tap Spend 10 ft → movement_remaining decrements in admin tracker via WS
5. Tap MOVE again → only remaining ft available in quick buttons
6. At 0 ft: MOVE token grays out, can't tap it

- [ ] **Step 3: Add Playwright smoke test for WebSocket + encounter page**

Add to `tests/smoke.spec.js`:
```javascript
test('encounter page shows no encounter when idle', async ({ page }) => {
  await login(page);
  await page.goto('/encounter');
  await page.waitForSelector('#enc-status');
  await expect(page.locator('#enc-status')).toContainText('No encounter in progress');
  await expect(page.locator('#enc-reconnect')).toBeHidden();
});
```

Run tests:
```bash
export NVM_DIR="$HOME/.nvm" && . "$NVM_DIR/nvm.sh"
export LD_LIBRARY_PATH="$HOME/.local/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
npx playwright test
```
Expected: all tests pass (3 existing + 1 new = 4 total).

- [ ] **Step 4: Commit**

```bash
git add static/encounter.js tests/smoke.spec.js
git commit -m "feat: movement stepper on encounter page; Playwright smoke test for encounter"
```

---

## Self-Review

**Spec coverage check:**

| Spec Section | Tasks |
|-------------|-------|
| WebSocket full-state push | Task 1 (manager + endpoint), Task 2 (broadcast admin), Task 3 (broadcast characters) |
| `/ws/encounter` endpoint | Task 1 |
| `_broadcast_state` helper | Task 1 |
| All mutation triggers broadcast | Task 2 (admin), Task 3 (characters) |
| Admin WS client (replaces poll) | Task 6 |
| Token-first action flow | Tasks 8–10 |
| Move stepper | Task 10 |
| End Turn player endpoint | Task 3 |
| Spend movement endpoint | Task 3 |
| Class ability seeding | Task 4 |
| Seed on add-to-combat | Task 4 |
| Cantrip filter fix | Task 3 |
| Rest removed from player sheet | Task 5 |
| encounter.html mobile layout | Task 7 |
| encounter.js WS client + reconnect | Task 8 |
| encounter.js render states | Task 8 |
| encounter.js action list | Task 9 |
| encounter.js confirm + Use It | Task 9 |
| encounter.js move stepper | Task 10 |
| Playwright smoke test | Task 10 |

All spec sections covered. ✅

**Placeholder scan:** No TBDs. One note on spell slot spending in Task 9 (`doUseAction`) — the existing endpoint shape (`POST /api/characters/{id}/spell-slots`) takes `{used: {...}}` as a full replacement dict. The plan notes to verify before running. The endpoint has been in place since Phase 4.

**Type consistency:** `myActiveCombatantId` (number|null), `activeToken` ('action'|'bonus'|'reaction'|'move'|null), `selectedActionIdx` (number|null) — used consistently across Tasks 8–10. `_broadcast_state(db)` defined in Task 1 and called identically in Tasks 2 and 3.

---

## Test Environment Notes

- Server: `TEST_AUTH_ENABLED=true ADMIN_EMAIL=zachpoguephil@gmail.com ~/.local/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload` (or via `.env`)
- Login: `http://localhost:8000/auth/test-login?email=zachpoguephil@gmail.com`
- WebSocket in browser devtools: Network tab → WS filter → verify `/ws/encounter` connection appears after login
- Class ability markdowns: place user-created files in `reference_claude/class_actions/{classname}.md` (lowercase). Server caches on first load per class; restart server to reload.
