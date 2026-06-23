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
ws_router = APIRouter()  # no prefix — registers /ws/encounter at root level


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
    # Auth: session cookie is included in WS upgrade request headers
    user = websocket.session.get("user")
    if not user:
        await websocket.close(code=1008)  # 1008 = Policy Violation
        return

    await manager.connect(websocket)
    try:
        db = SessionLocal()
        try:
            state = _build_state_dict(db)
        finally:
            db.close()
        await websocket.send_json(state)

        while True:
            # Read-only push channel; clients POST to REST for writes
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as exc:
        log.warning("WS encounter error: %s", exc)
        manager.disconnect(websocket)
        try:
            await websocket.close(1011)
        except Exception:
            pass
