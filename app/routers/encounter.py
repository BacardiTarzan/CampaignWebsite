from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.character import Combatant, EncounterState
from ..models.content import Monster
from ..dependencies import require_user

router = APIRouter(prefix="/api/encounter", tags=["encounter"])


def _get_or_create_state(db: Session) -> EncounterState:
    """Get the singleton EncounterState (id=1), creating it if it doesn't exist yet."""
    state = db.get(EncounterState, 1)
    if not state:
        state = EncounterState(id=1)
        db.add(state)
        db.commit()
        db.refresh(state)
    return state


@router.get("/state")
def get_encounter_state(db: Session = Depends(get_db), _user=Depends(require_user)):
    state = _get_or_create_state(db)
    rows = db.query(Combatant).order_by(
        Combatant.turn_order.nulls_last(), Combatant.added_at
    ).all()

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
            m = db.get(Monster, row.monster_id)
            if not m:
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
