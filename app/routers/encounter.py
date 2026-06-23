import logging

from fastapi import APIRouter, Depends
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload
from ..database import get_db
from ..models.character import Combatant, Character, CharacterClass, EncounterState
from ..models.content import Monster
from ..dependencies import require_user

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/encounter", tags=["encounter"])


def _get_or_create_state(db: Session) -> EncounterState:
    """Get the singleton EncounterState (id=1), creating it if it doesn't exist yet."""
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


@router.get("/state")
def get_encounter_state(db: Session = Depends(get_db), _user=Depends(require_user)):
    state = _get_or_create_state(db)
    rows = (
        db.query(Combatant)
        .options(
            selectinload(Combatant.character)
            .selectinload(Character.character_classes)
            .selectinload(CharacterClass.dnd_class)
        )
        .order_by(Combatant.turn_order.nulls_last(), Combatant.added_at)
        .all()
    )

    # Batch-load all monsters referenced by combatants in one query
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
            })
        else:
            m = monsters_by_id.get(row.monster_id)
            if not m:
                log.warning(
                    "Combatant %s has missing monster_id=%s — skipping",
                    row.id,
                    row.monster_id,
                )
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
