"""
Level-up rules engine for D&D 2024.

Encodes per-class, per-level decision points from level-up-wizard/*.md reference files.
`required_steps()` returns the ordered list of step descriptors for the frontend wizard.
`auto_grants()` returns spell IDs that should be auto-added without player input.
"""

from __future__ import annotations
from sqlalchemy.orm import Session
from ..models.content import Feat, Spell

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

# ASI levels by class (all classes use 4/8/12/16/19 unless overridden)
ASI_LEVELS: dict[str, list[int]] = {
    "Fighter": [4, 6, 8, 12, 14, 16, 19],
    "Rogue":   [4, 8, 10, 12, 16, 19],
    "_default": [4, 8, 12, 16, 19],
}

# Cantrip gains on level-up (for classes that gain cantrips after L1)
CANTRIP_GAINS: dict[str, dict[int, int]] = {
    "Bard":     {4: 1, 10: 1},
    "Cleric":   {4: 1, 10: 1},
    "Druid":    {4: 1, 10: 1},
    "Sorcerer": {4: 1, 10: 1},
    "Warlock":  {4: 1, 10: 1},
    "Wizard":   {4: 1, 10: 1},
}

# Known-spell gains for known-spell casters (not prepared-from-list classes)
# Bard/Sorcerer/Warlock: pick new spells. Ranger: same (half-caster known).
# Wizard: +2 spellbook spells each level (kind=wizard_spellbook).
# Cleric/Druid/Paladin: prepared-from-list — no "pick known spell" step.
KNOWN_SPELL_GAINS: dict[str, dict[int, int]] = {
    "Bard":     {l: 1 for l in range(2, 21)} | {20: 2},  # L20 gains 2
    "Sorcerer": {2:2, 3:2, 4:1, 5:2, 6:1, 7:1, 8:1, 9:2, 10:1, 11:1, 12:1, 13:1,
                 14:1, 15:1, 16:1, 17:1, 18:1, 19:1, 20:1},
    "Warlock":  {2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:0, 11:1, 12:0, 13:1,
                 14:0, 15:1, 16:0, 17:1, 18:0, 19:1, 20:0},
    "Ranger":   {2:1, 3:1, 5:1, 7:1, 9:1, 11:1, 13:1, 15:1, 17:1, 19:1},
    "Wizard":   {l: 2 for l in range(2, 21)},
}

# Max spell level for each caster type and character level
def max_spell_level(spellcasting_type: str, char_level: int) -> int:
    if spellcasting_type == "full":
        return min(9, max(1, (char_level + 1) // 2))
    if spellcasting_type == "half":
        return min(5, max(1, (char_level + 3) // 4))
    if spellcasting_type == "pact":
        # Pact Magic slot level: 1@L1, 2@L2-4, 3@L5-10, 4@L7-10 → actually L7+slot4, L11+slot5
        if char_level >= 11: return 5
        if char_level >= 7:  return 4
        if char_level >= 5:  return 3
        if char_level >= 2:  return 2
        return 1
    return 0

# Warlock invocation count by level (cumulative)
_WARLOCK_INVOC_TOTAL = {1:1, 2:3, 3:3, 4:3, 5:5, 6:5, 7:6, 8:6, 9:7, 10:7, 11:7,
                        12:8, 13:8, 14:8, 15:9, 16:9, 17:9, 18:10, 19:10, 20:10}

def _warlock_invoc_gains(next_level: int) -> int:
    cur = _WARLOCK_INVOC_TOTAL.get(next_level - 1, 1)
    new = _WARLOCK_INVOC_TOTAL.get(next_level, cur)
    return max(0, new - cur)

# Classes that gain a fighting style and at what level (L2+ only for level-up wizard)
FIGHTING_STYLE_AT: dict[str, int] = {"Paladin": 2, "Ranger": 2}
# Fighter gains fighting style at L1 (creation), but may swap any level-up (handled separately)

# Expertise gains (after L1 creation)
EXPERTISE_GAINS: dict[str, dict[int, int]] = {
    "Bard":   {2: 2, 9: 2},   # 2 skills at L2, 2 more at L9
    "Ranger": {2: 1, 9: 2},   # Deft Explorer: 1 skill at L2, 2 more at L9
    "Rogue":  {6: 2},          # L1 is at creation; L6 at level-up
}

# Sorcerer metamagic options (hard-coded — not in feat DB)
METAMAGIC_OPTIONS = [
    {"key": "careful",     "name": "Careful Spell",     "cost": "1 SP",
     "desc": "Up to Charisma modifier creatures automatically succeed on saves vs. the spell."},
    {"key": "distant",     "name": "Distant Spell",     "cost": "1 SP",
     "desc": "Double the range, or change Touch to 30 ft."},
    {"key": "empowered",   "name": "Empowered Spell",   "cost": "1 SP",
     "desc": "Reroll up to Charisma modifier damage dice and keep the new result."},
    {"key": "extended",    "name": "Extended Spell",    "cost": "1 SP",
     "desc": "Double the duration (max 24 hours); Advantage on Concentration saves."},
    {"key": "heightened",  "name": "Heightened Spell",  "cost": "2 SP",
     "desc": "One target has Disadvantage on saving throws vs. the spell."},
    {"key": "quickened",   "name": "Quickened Spell",   "cost": "2 SP",
     "desc": "Change the casting time from Action to Bonus Action. Can't cast another level 1+ spell this turn."},
    {"key": "seeking",     "name": "Seeking Spell",     "cost": "1 SP",
     "desc": "Reroll a missed spell attack roll."},
    {"key": "subtle",      "name": "Subtle Spell",      "cost": "1 SP",
     "desc": "Cast without Verbal, Somatic, or unconsumed Material components."},
    {"key": "transmuted",  "name": "Transmuted Spell",  "cost": "1 SP",
     "desc": "Change the damage type among Acid, Cold, Fire, Lightning, Poison, or Thunder."},
    {"key": "twinned",     "name": "Twinned Spell",     "cost": "1 SP",
     "desc": "Increase the spell's effective level by 1 to target one additional creature."},
]

METAMAGIC_GAINS: dict[int, int] = {2: 2, 10: 2, 17: 2}

# Aasimar Celestial Revelation choices (unlocked at L3)
AASIMAR_REVELATIONS = [
    {"key": "heavenly_wings",
     "name": "Heavenly Wings",
     "description": "Spectral wings sprout from your back. Until the transformation ends, you have a Fly Speed equal to your Speed. The transformation lasts for 1 minute or until you end it (no action required). Once you use this transformation, you can't use it again until you finish a Long Rest."},
    {"key": "inner_radiance",
     "name": "Inner Radiance",
     "description": "Searing light temporarily radiates from your eyes and mouth. For 1 minute or until you end it (no action required), you shed Bright Light in a 10-foot radius and dim light for an additional 10 feet, and at the end of each of your turns each creature within 10 feet of you takes Radiant damage equal to your Proficiency Bonus. Once you use this transformation, you can't use it again until you finish a Long Rest."},
    {"key": "necrotic_shroud",
     "name": "Necrotic Shroud",
     "description": "Your eyes briefly become pools of darkness, and ghostly, flightless wings sprout from your back. Creatures other than your allies within 10 feet of you that can see you must succeed on a Charisma saving throw (DC 8 + your Charisma modifier + your Proficiency Bonus) or have the Frightened condition until the end of your next turn. This transformation lasts for 1 minute or until you end it (no action required), and once per turn when you deal damage to a creature you also deal extra Necrotic damage to it equal to your Proficiency Bonus. Once you use this transformation, you can't use it again until you finish a Long Rest."},
]

# Eldritch Invocations (hard-coded — not in feat DB)
# prereq_level: minimum warlock level; prereq_pact: "blade"/"chain"/"tome" or None
ELDRITCH_INVOCATIONS = [
    {"key": "armor_of_shadows",  "name": "Armor of Shadows",  "prereq_level": None, "prereq_pact": None,
     "desc": "Cast Mage Armor on yourself at will, without a spell slot."},
    {"key": "eldritch_mind",     "name": "Eldritch Mind",     "prereq_level": None, "prereq_pact": None,
     "desc": "Advantage on Concentration saving throws."},
    {"key": "pact_blade",        "name": "Pact of the Blade", "prereq_level": None, "prereq_pact": None,
     "desc": "Summon or bond a melee weapon; use Charisma for attack and damage rolls."},
    {"key": "pact_chain",        "name": "Pact of the Chain", "prereq_level": None, "prereq_pact": None,
     "desc": "Cast Find Familiar for free; familiar can take special monstrous forms."},
    {"key": "pact_tome",         "name": "Pact of the Tome",  "prereq_level": None, "prereq_pact": None,
     "desc": "Gain a Book of Shadows with 3 cantrips and 2 ritual spells."},
    {"key": "agonizing_blast",   "name": "Agonizing Blast",   "prereq_level": 2, "prereq_pact": None,
     "desc": "Add Charisma modifier to Eldritch Blast damage."},
    {"key": "devils_sight",      "name": "Devil's Sight",     "prereq_level": 2, "prereq_pact": None,
     "desc": "See normally in magical and nonmagical darkness up to 120 ft."},
    {"key": "fiendish_vigor",    "name": "Fiendish Vigor",    "prereq_level": 2, "prereq_pact": None,
     "desc": "Cast False Life on yourself at will (1st-level), gaining 1d4+4 Temp HP."},
    {"key": "mask_of_many_faces","name": "Mask of Many Faces","prereq_level": 2, "prereq_pact": None,
     "desc": "Cast Disguise Self at will, without a spell slot."},
    {"key": "misty_visions",     "name": "Misty Visions",     "prereq_level": 2, "prereq_pact": None,
     "desc": "Cast Silent Image at will, without a spell slot."},
    {"key": "repelling_blast",   "name": "Repelling Blast",   "prereq_level": 2, "prereq_pact": None,
     "desc": "Push creatures hit by Eldritch Blast 10 ft. away."},
    {"key": "eldritch_smite",    "name": "Eldritch Smite",    "prereq_level": 5, "prereq_pact": "blade",
     "desc": "Expend a Pact slot on a hit for extra Force damage and Prone."},
    {"key": "thirsting_blade",   "name": "Thirsting Blade",   "prereq_level": 5, "prereq_pact": "blade",
     "desc": "Gain Extra Attack with your pact weapon."},
    {"key": "one_with_shadows",  "name": "One with Shadows",  "prereq_level": 5, "prereq_pact": None,
     "desc": "Become Invisible in dim light or darkness as a Bonus Action."},
    {"key": "sign_of_ill_omen",  "name": "Sign of Ill Omen",  "prereq_level": 5, "prereq_pact": None,
     "desc": "Cast Bestow Curse once per Long Rest without a spell slot."},
    {"key": "bewitching_whispers","name": "Bewitching Whispers","prereq_level": 7, "prereq_pact": None,
     "desc": "Cast Compulsion once per Long Rest without a spell slot."},
    {"key": "dreadful_word",     "name": "Dreadful Word",     "prereq_level": 7, "prereq_pact": None,
     "desc": "Cast Confusion once per Long Rest without a spell slot."},
    {"key": "sculptor_of_flesh", "name": "Sculptor of Flesh", "prereq_level": 7, "prereq_pact": None,
     "desc": "Cast Polymorph once per Long Rest without a spell slot."},
    {"key": "lifedrinker",       "name": "Lifedrinker",       "prereq_level": 9, "prereq_pact": "blade",
     "desc": "Extra 1d6 necrotic on each pact weapon hit; expend Hit Die to heal."},
    {"key": "minions_of_chaos",  "name": "Minions of Chaos",  "prereq_level": 9, "prereq_pact": None,
     "desc": "Cast Conjure Elemental once per Long Rest without a spell slot."},
    {"key": "ascendant_step",    "name": "Ascendant Step",    "prereq_level": 9, "prereq_pact": None,
     "desc": "Cast Levitate on yourself at will, without a spell slot."},
    {"key": "chains_of_carceri","name": "Chains of Carceri", "prereq_level": 15, "prereq_pact": "chain",
     "desc": "Cast Hold Monster at will on Celestials, Fiends, and Elementals; no spell slot."},
    {"key": "shroud_of_shadow",  "name": "Shroud of Shadow",  "prereq_level": 15, "prereq_pact": None,
     "desc": "Cast Invisibility at will, without a spell slot."},
    {"key": "visions_of_distant_realms","name":"Visions of Distant Realms","prereq_level": 15,"prereq_pact": None,
     "desc": "Cast Arcane Eye at will, without a spell slot."},
]

# Class-level always-prepared spells (granted by class features, not subclass)
# class_name → {min_level: [spell_names]}
CLASS_ALWAYS_PREPARED: dict[str, dict[int, list[str]]] = {
    "Ranger": {
        1: ["Hunter's Mark"],   # Favored Enemy
    },
}

# Subclass always-prepared spell grants by subclass name → {tier_level: [spell_names]}
# "tier_level" is the character level at which the tier kicks in (3/5/7/9 for most)
SUBCLASS_ALWAYS_PREPARED: dict[str, dict[int, list[str]]] = {
    # Cleric Domains
    "Life Domain": {
        3: ["Bless", "Cure Wounds"],
        5: ["Lesser Restoration", "Prayer of Healing"],
        9: ["Mass Healing Word", "Revivify"],
        13: ["Aura of Life", "Death Ward"],
        17: ["Greater Restoration", "Mass Cure Wounds"],
    },
    "Light Domain": {
        3: ["Burning Hands", "Faerie Fire"],
        5: ["Flaming Sphere", "Scorching Ray"],
        9: ["Daylight", "Fireball"],
        13: ["Fire Shield", "Wall of Fire"],
        17: ["Flame Strike", "Scrying"],
    },
    "Trickery Domain": {
        3: ["Charm Person", "Disguise Self"],
        5: ["Mirror Image", "Pass Without Trace"],
        9: ["Blink", "Dispel Magic"],
        13: ["Dimension Door", "Polymorph"],
        17: ["Dominate Person", "Modify Memory"],
    },
    "War Domain": {
        3: ["Divine Favor", "Shield of Faith"],
        5: ["Magic Weapon", "Spiritual Weapon"],
        9: ["Crusader's Mantle", "Spirit Guardians"],
        13: ["Fire Shield", "Freedom of Movement"],
        17: ["Hold Monster", "Wall of Force"],
    },
    # Paladin Oaths
    "Oath of Devotion": {
        3: ["Protection from Evil and Good", "Shield of Faith"],
        5: ["Aid", "Zone of Truth"],
        9: ["Beacon of Hope", "Dispel Magic"],
        13: ["Freedom of Movement", "Guardian of Faith"],
        17: ["Commune", "Flame Strike"],
    },
    "Oath of Glory": {
        3: ["Guiding Bolt", "Heroism"],
        5: ["Enhance Ability", "Magic Weapon"],
        9: ["Haste", "Protection from Energy"],
        13: ["Compulsion", "Freedom of Movement"],
        17: ["Legend Lore", "Yolande's Regal Presence"],
    },
    "Oath of the Ancients": {
        3: ["Ensnaring Strike", "Speak with Animals"],
        5: ["Misty Step", "Moonbeam"],
        9: ["Plant Growth", "Protection from Energy"],
        13: ["Ice Storm", "Stoneskin"],
        17: ["Commune with Nature", "Tree Stride"],
    },
    "Oath of Vengeance": {
        3: ["Bane", "Hunter's Mark"],
        5: ["Hold Person", "Misty Step"],
        9: ["Haste", "Protection from Energy"],
        13: ["Banishment", "Dimension Door"],
        17: ["Hold Monster", "Scrying"],
    },
    # Warlock Patrons
    "Archfey Patron": {
        3: ["Calm Emotions", "Faerie Fire", "Misty Step", "Phantasmal Force", "Sleep"],
        5: ["Blink", "Plant Growth"],
        7: ["Dominate Beast", "Greater Invisibility"],
        9: ["Dominate Person", "Seeming"],
    },
    "Celestial Patron": {
        3: ["Aid", "Cure Wounds", "Guiding Bolt", "Lesser Restoration", "Light", "Sacred Flame"],
        5: ["Daylight", "Revivify"],
        7: ["Guardian of Faith", "Wall of Fire"],
        9: ["Greater Restoration", "Summon Celestial"],
    },
    "Fiend Patron": {
        3: ["Burning Hands", "Command", "Scorching Ray", "Suggestion"],
        5: ["Fireball", "Stinking Cloud"],
        7: ["Fire Shield", "Wall of Fire"],
        9: ["Geas", "Insect Plague"],
    },
    "Great Old One Patron": {
        3: ["Detect Thoughts", "Dissonant Whispers", "Phantasmal Force", "Tasha's Hideous Laughter"],
        5: ["Clairvoyance", "Hunger of Hadar"],
        7: ["Confusion", "Summon Aberration"],
        9: ["Modify Memory", "Telekinesis"],
    },
    # Sorcerer Subclasses
    "Aberrant Sorcery": {
        3: ["Arms of Hadar", "Dissonant Whispers", "Mind Sliver"],
        5: ["Detect Thoughts", "Calm Emotions"],
        7: ["Hunger of Hadar", "Sending"],
        9: ["Rary's Telepathic Bond", "Telekinesis"],
    },
    "Clockwork Sorcery": {
        3: ["Aid", "Alarm", "Lesser Restoration", "Protection from Evil and Good"],
        5: ["Dispel Magic", "Protection from Energy"],
        7: ["Freedom of Movement", "Summon Construct"],
        9: ["Greater Restoration", "Wall of Force"],
    },
    "Draconic Sorcery": {
        3: ["Command", "Dragon's Breath", "Fear", "Fly"],
        5: ["Arcane Eye", "Charm Monster"],
        9: ["Legend Lore", "Summon Dragon"],
    },
    "Wild Magic Sorcery": {},  # No fixed always-prepared spells
}

# Cleric "Blessed Strikes" choice at L7 (choose Divine Strike OR Potent Spellcasting)
# Druid "Elemental Fury" choice at L7 (Potent Spellcasting OR Primal Strike)
# These are feature_choice steps rendered from the feature JSON; no special handling needed here.

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _con_mod(char) -> int:
    attrs = char.base_attributes or {}
    bg = char.background_asi or {}
    total_con = attrs.get("con", 10) + bg.get("con", 0)
    return (total_con - 10) // 2


def _get_asi_levels(class_name: str) -> list[int]:
    return ASI_LEVELS.get(class_name, ASI_LEVELS["_default"])


def _owned_invoc_keys(char) -> list[str]:
    """Return list of invocation keys from CharacterChoice rows."""
    from ..models.character import CharacterChoice
    return [
        (c.choice_value or {}).get("key", "")
        for c in char.choices
        if c.feature_key == "invocation"
    ]


def _owned_metamagic_keys(char) -> list[str]:
    """Return list of metamagic keys from CharacterChoice rows."""
    from ..models.character import CharacterChoice
    return [
        (c.choice_value or {}).get("key", "")
        for c in char.choices
        if c.feature_key == "metamagic"
    ]


def _has_pact(char, pact_key: str) -> bool:
    """Check if warlock character has chosen a specific Pact (blade/chain/tome)."""
    invoc_keys = _owned_invoc_keys(char)
    return f"pact_{pact_key}" in invoc_keys


def _eligible_invocations(char, warlock_level: int) -> list[dict]:
    """Return invocations the character can pick (not already known, meets prereqs)."""
    owned = set(_owned_invoc_keys(char))
    eligible = []
    for inv in ELDRITCH_INVOCATIONS:
        if inv["key"] in owned:
            continue
        if inv["prereq_level"] and warlock_level < inv["prereq_level"]:
            continue
        if inv["prereq_pact"] and not _has_pact(char, inv["prereq_pact"]):
            continue
        eligible.append(inv)
    return eligible


def _draconic_hp_bonus(subclass_name: str | None, next_level: int) -> int:
    """Return the extra HP a Draconic Sorcerer gains at this level (1 per level from L4+)."""
    if subclass_name == "Draconic Sorcery" and next_level >= 4:
        return 1
    return 0

# ---------------------------------------------------------------------------
# Step builders
# ---------------------------------------------------------------------------

def _hp_step(char, cls, subclass_name, next_level) -> dict:
    con = _con_mod(char)
    avg = cls.hit_die // 2 + 1
    bonus = _draconic_hp_bonus(subclass_name, next_level)
    return {
        "id": "hp",
        "kind": "hp",
        "label": "Hit Points",
        "required": True,
        "hit_die": cls.hit_die,
        "average": avg,
        "con_mod": con,
        "draconic_bonus": bonus,
        "hint": f"d{cls.hit_die} (avg {avg}) + CON {con:+d}" + (f" + Draconic +{bonus}" if bonus else ""),
    }


def _asi_step(char, next_level) -> dict:
    attrs = char.base_attributes or {}
    bg = char.background_asi or {}
    current = {k: attrs.get(k, 10) + bg.get(k, 0) for k in ["str","dex","con","int","wis","cha"]}
    return {
        "id": f"asi_l{next_level}",
        "kind": "asi",
        "label": "Ability Score Improvement",
        "required": True,
        "current_attributes": current,
    }


def _fighting_style_step(class_name: str, next_level: int) -> dict:
    extra = []
    if class_name == "Paladin":
        extra = ["blessed_warrior"]  # allow Blessed Warrior fighting style feat
    if class_name == "Ranger":
        extra = ["druidic_warrior"]  # allow Druidic Warrior fighting style feat
    return {
        "id": f"fighting_style_l{next_level}",
        "kind": "fighting_style",
        "label": "Choose Fighting Style",
        "required": True,
        "extra_options": extra,
        "can_replace": (class_name == "Fighter"),
    }


def _fighter_swap_style_step(next_level: int) -> dict:
    return {
        "id": f"fighter_style_swap_l{next_level}",
        "kind": "fighting_style_swap",
        "label": "Fighting Style (optional swap)",
        "required": False,
        "can_replace": True,
    }


def _expertise_step(char, pick: int, next_level: int) -> dict:
    from ..models.character import SkillProficiency
    owned = [
        sp.skill_name for sp in char.skill_proficiencies
        if not sp.expertise
    ]
    return {
        "id": f"expertise_l{next_level}",
        "kind": "expertise",
        "label": "Expertise",
        "required": True,
        "pick": pick,
        "eligible_skills": sorted(owned),
    }


def _cantrips_step(pick: int, next_level: int) -> dict:
    return {
        "id": f"cantrips_l{next_level}",
        "kind": "cantrips_new",
        "label": f"New Cantrip{'s' if pick > 1 else ''}",
        "required": True,
        "pick": pick,
    }


def _spells_new_step(pick: int, next_level: int, max_sl: int, class_name: str) -> dict:
    label = "Add to Spellbook" if class_name == "Wizard" else f"New Spell{'s' if pick > 1 else ''}"
    kind  = "wizard_spellbook" if class_name == "Wizard" else "spells_new"
    return {
        "id": f"spells_l{next_level}",
        "kind": kind,
        "label": label,
        "required": True,
        "pick": pick,
        "max_spell_level": max_sl,
    }


def _spell_swap_step(next_level: int, max_sl: int) -> dict:
    return {
        "id": f"spell_swap_l{next_level}",
        "kind": "spell_swap",
        "label": "Swap a Known Spell (optional)",
        "required": False,
        "max_spell_level": max_sl,
    }


def _cantrip_swap_step(next_level: int) -> dict:
    return {
        "id": f"cantrip_swap_l{next_level}",
        "kind": "cantrip_swap",
        "label": "Swap a Cantrip (optional)",
        "required": False,
    }


def _metamagic_step(char, pick: int, next_level: int) -> dict:
    owned_keys = set(_owned_metamagic_keys(char))
    available = [m for m in METAMAGIC_OPTIONS if m["key"] not in owned_keys]
    return {
        "id": f"metamagic_l{next_level}",
        "kind": "metamagic",
        "label": f"Metamagic — Choose {pick}",
        "required": True,
        "pick": pick,
        "options": available,
    }


def _invocations_new_step(char, gains: int, next_level: int) -> dict:
    eligible = _eligible_invocations(char, next_level)
    owned = _owned_invoc_keys(char)
    return {
        "id": f"invocations_l{next_level}",
        "kind": "invocations_new",
        "label": f"Eldritch Invocation{'s' if gains > 1 else ''} — Choose {gains}",
        "required": True,
        "pick": gains,
        "options": eligible,
        "owned": [inv for inv in ELDRITCH_INVOCATIONS if inv["key"] in owned],
    }


def _invocation_swap_step(char, next_level: int) -> dict:
    eligible = _eligible_invocations(char, next_level)
    owned = _owned_invoc_keys(char)
    return {
        "id": f"invoc_swap_l{next_level}",
        "kind": "invocation_swap",
        "label": "Replace an Invocation (optional)",
        "required": False,
        "options": eligible,
        "owned": [inv for inv in ELDRITCH_INVOCATIONS if inv["key"] in owned],
    }


def _mystic_arcanum_step(spell_level: int, next_level: int) -> dict:
    ordinals = {6: "6th", 7: "7th", 8: "8th", 9: "9th"}
    return {
        "id": f"arcanum_l{next_level}",
        "kind": "mystic_arcanum",
        "label": f"Mystic Arcanum — {ordinals[spell_level]}-Level Spell",
        "required": True,
        "spell_level": spell_level,
        "description": f"Choose one {ordinals[spell_level]}-level Warlock spell. You can cast it once per Long Rest without a spell slot.",
    }


def _epic_boon_step(next_level: int) -> dict:
    return {
        "id": f"epic_boon_l{next_level}",
        "kind": "epic_boon",
        "label": "Epic Boon Feat",
        "required": True,
    }


def _feature_choice_steps(features: list[dict], next_level: int, prefix: str = "") -> list[dict]:
    """Build generic feature_choice steps from features with choice_required=True."""
    steps = []
    for f in features:
        if not f.get("choice_required"):
            continue
        key = f.get("choice_key") or f["name"].lower().replace(" ", "_")
        steps.append({
            "id": f"feature_{prefix}{key}_l{next_level}",
            "kind": "feature_choice",
            "label": f.get("name", "Choose"),
            "required": True,
            "feature_name": f.get("name", ""),
            "description": f.get("description", ""),
            "pick": 1,
            "options": [{"name": o} for o in (f.get("options") or [])],
        })
    return steps


def _subclass_step(subclass_options: list[dict], next_level: int) -> dict:
    return {
        "id": f"subclass_l{next_level}",
        "kind": "subclass",
        "label": "Choose Subclass",
        "required": True,
        "options": subclass_options,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def required_steps(char, cc, cls, db: Session) -> list[dict]:
    """
    Return the ordered list of step dicts for the player level-up wizard.
    The caller provides the character, character_class, dnd_class objects.
    """
    next_level = cc.level + 1
    class_name = cls.name
    subclass = cc.subclass
    subclass_name = subclass.name if subclass else None
    sp_type = cls.spellcasting_type or ""
    max_sl = max_spell_level(sp_type, next_level) if sp_type else 0

    steps: list[dict] = []

    # 1. HP — always first
    steps.append(_hp_step(char, cls, subclass_name, next_level))

    # 2. Subclass selection (level 3 for all classes in 2024)
    if next_level == 3 and cc.subclass_id is None:
        subclass_options = [
            {"id": s.id, "name": s.name, "description": s.description,
             "features": [f for f in (s.features or []) if f.get("level") == next_level]}
            for s in cls.subclasses
        ]
        if subclass_options:
            steps.append(_subclass_step(subclass_options, next_level))

    # 3. ASI / Epic Boon
    asi_levels = _get_asi_levels(class_name)
    if next_level in asi_levels:
        if next_level == 19:
            steps.append(_epic_boon_step(next_level))
        else:
            steps.append(_asi_step(char, next_level))

    # 4. Fighting Style (Paladin L2, Ranger L2)
    if class_name in FIGHTING_STYLE_AT and next_level == FIGHTING_STYLE_AT[class_name]:
        steps.append(_fighting_style_step(class_name, next_level))
    # Fighter can swap fighting style on every level-up (optional)
    if class_name == "Fighter" and next_level >= 2:
        has_style = any(c.feature_key == "fighting_style" for c in char.choices)
        if next_level == 1:
            steps.append(_fighting_style_step(class_name, next_level))
        elif has_style:
            steps.append(_fighter_swap_style_step(next_level))

    # 5. Expertise
    if class_name in EXPERTISE_GAINS:
        pick = EXPERTISE_GAINS[class_name].get(next_level, 0)
        if pick > 0:
            steps.append(_expertise_step(char, pick, next_level))

    # 6. Cantrip gains
    cantrip_gains = CANTRIP_GAINS.get(class_name, {}).get(next_level, 0)
    if cantrip_gains > 0:
        steps.append(_cantrips_step(cantrip_gains, next_level))

    # 7. Spell / spellbook gains
    if class_name in KNOWN_SPELL_GAINS:
        spell_gains = KNOWN_SPELL_GAINS[class_name].get(next_level, 0)
        if spell_gains > 0 and max_sl > 0:
            steps.append(_spells_new_step(spell_gains, next_level, max_sl, class_name))

    # 8. Spell swap (for known-spell casters and Wizard: optional on every level-up)
    if class_name in ("Bard", "Sorcerer", "Warlock", "Ranger", "Wizard"):
        if next_level >= 2 and max_sl > 0:
            steps.append(_spell_swap_step(next_level, max_sl))

    # 9. Sorcerer Metamagic
    if class_name == "Sorcerer":
        mm_pick = METAMAGIC_GAINS.get(next_level, 0)
        if mm_pick > 0:
            steps.append(_metamagic_step(char, mm_pick, next_level))

    # 10. Warlock Invocations
    if class_name == "Warlock":
        invoc_gains = _warlock_invoc_gains(next_level)
        if invoc_gains > 0:
            steps.append(_invocations_new_step(char, invoc_gains, next_level))
        # Optional invocation swap on every level-up from L2+
        if next_level >= 2:
            steps.append(_invocation_swap_step(char, next_level))

    # 11. Warlock Mystic Arcanum
    arcanum_levels = {9: 6, 11: 7, 13: 8, 15: 9}
    if class_name == "Warlock" and next_level in arcanum_levels:
        steps.append(_mystic_arcanum_step(arcanum_levels[next_level], next_level))

    # 12. Feature choices from class features JSON (choice_required=True)
    new_class_features = [f for f in (cls.features or []) if f.get("level") == next_level]
    steps.extend(_feature_choice_steps(new_class_features, next_level))

    # 13. Subclass feature choices from subclass features JSON
    if subclass:
        sub_features = [f for f in (subclass.features or []) if f.get("level") == next_level]
        steps.extend(_feature_choice_steps(sub_features, next_level, prefix="sub_"))

    # 14. Species level-gated steps
    species = char.species if hasattr(char, 'species') else None
    if species:
        # Aasimar Celestial Revelation at L3 (requires a pick)
        if species.name == "Aasimar" and next_level == 3:
            already_chosen = any(c.feature_key == "species_revelation_l3" for c in char.choices)
            if not already_chosen:
                steps.append({
                    "id": "species_revelation_l3",
                    "kind": "species_revelation",
                    "label": "Celestial Revelation",
                    "title": "Choose your Celestial Revelation",
                    "description": "At 3rd level your angelic nature manifests. Choose one of the following transformations, usable once per Long Rest.",
                    "options": AASIMAR_REVELATIONS,
                    "required": True,
                })

        # Lineage spell notifications (informational — actual grants happen in auto_grants)
        lineage_spells = _species_lineage_spells(char, next_level)
        for spell_name in lineage_spells:
            steps.append({
                "id": f"species_spell_info_{next_level}",
                "kind": "species_spell_info",
                "label": "Lineage Spell",
                "spell_name": spell_name,
                "required": False,
            })

    return steps


def _species_lineage_spells(char, next_level: int) -> list[str]:
    """Return spell names auto-granted by lineage at next_level (L3 and L5)."""
    species = char.species if hasattr(char, 'species') else None
    if not species or not char.species_lineage or not species.lineages:
        return []
    lineage = next((l for l in species.lineages if l.get('name') == char.species_lineage), None)
    if not lineage:
        return []
    spell_names = []
    if next_level == 3 and lineage.get('level3_spell'):
        spell_names.append(lineage['level3_spell'])
    if next_level == 5 and lineage.get('level5_spell'):
        spell_names.append(lineage['level5_spell'])
    return spell_names


def auto_grants(char, cc, cls, subclass, next_level: int, db: Session) -> list[int]:
    """
    Return spell IDs that should be auto-added as always_prepared=True
    when this character levels to next_level. Includes subclass domain/patron/oath
    spells and species lineage spells.
    """
    owned_ids = {cs.spell_id for cs in char.spells}
    spell_ids = []

    # Class always-prepared spells (e.g. Ranger Favored Enemy → Hunter's Mark)
    if cls:
        for min_lvl, spell_names in CLASS_ALWAYS_PREPARED.get(cls.name, {}).items():
            if next_level >= min_lvl:
                for name in spell_names:
                    spell = db.query(Spell).filter(Spell.name == name).first()
                    if spell and spell.id not in owned_ids:
                        spell_ids.append(spell.id)
                        owned_ids.add(spell.id)

    # Subclass tier spells
    if subclass:
        tier_spells = SUBCLASS_ALWAYS_PREPARED.get(subclass.name, {}).get(next_level, [])
        for name in tier_spells:
            spell = db.query(Spell).filter(Spell.name == name).first()
            if spell and spell.id not in owned_ids:
                spell_ids.append(spell.id)
                owned_ids.add(spell.id)

    # Species lineage spells (Elven, Tiefling, etc.)
    for name in _species_lineage_spells(char, next_level):
        spell = db.query(Spell).filter(Spell.name == name).first()
        if spell and spell.id not in owned_ids:
            spell_ids.append(spell.id)
            owned_ids.add(spell.id)

    return spell_ids


def subclass_auto_grants(char, cc, cls, subclass, db: Session) -> list[int]:
    """
    Return all auto-granted spell IDs for all tiers up to cc.level for a newly
    selected subclass (called when subclass is chosen mid-level-up at L3).
    """
    if not subclass:
        return []
    owned_ids = {cs.spell_id for cs in char.spells}
    tier_map = SUBCLASS_ALWAYS_PREPARED.get(subclass.name, {})
    spell_ids = []
    for tier_level, spell_names in tier_map.items():
        # Only grant tiers that have already been reached
        if tier_level <= cc.level + 1:  # include the level they're gaining now
            for name in spell_names:
                spell = db.query(Spell).filter(Spell.name == name).first()
                if spell and spell.id not in owned_ids:
                    spell_ids.append(spell.id)
                    owned_ids.add(spell.id)  # prevent duplicates in this batch
    return spell_ids
