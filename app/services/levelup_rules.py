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
    # Bard and Ranger are prepared casters in 2024 PHB — removed from this dict.
    # Sorcerer / Warlock / Wizard remain as Spells Known casters.
    "Sorcerer": {2:2, 3:2, 4:1, 5:2, 6:1, 7:1, 8:1, 9:2, 10:1, 11:1, 12:1, 13:1,
                 14:1, 15:1, 16:1, 17:1, 18:1, 19:1, 20:1},
    "Warlock":  {2:1, 3:1, 4:1, 5:1, 6:1, 7:1, 8:1, 9:1, 10:0, 11:1, 12:0, 13:1,
                 14:0, 15:1, 16:0, 17:1, 18:0, 19:1, 20:0},
    "Wizard":   {l: 2 for l in range(2, 21)},
}

# One-third caster tables (Eldritch Knight keyed to Fighter level; Arcane Trickster to Rogue level)
# Both subclasses share identical slot progressions and Spells Known counts.
THIRD_CASTER_SLOTS: dict[int, list[int]] = {
    # class level → [1st, 2nd, 3rd, 4th] (omit trailing zeros)
    3:  [2],
    4:  [3],
    5:  [3],
    6:  [3],
    7:  [4, 2],
    8:  [4, 2],
    9:  [4, 2],
    10: [4, 3],
    11: [4, 3],
    12: [4, 3],
    13: [4, 3, 2],
    14: [4, 3, 2],
    15: [4, 3, 2],
    16: [4, 3, 3],
    17: [4, 3, 3],
    18: [4, 3, 3],
    19: [4, 3, 3, 1],
    20: [4, 3, 3, 1],
}

# Cumulative Spells Known (not including cantrips) keyed to class level
THIRD_CASTER_SPELLS_KNOWN: dict[int, int] = {
    3: 3, 4: 4, 5: 4, 6: 4, 7: 5, 8: 6, 9: 6,
    10: 7, 11: 8, 12: 8, 13: 9, 14: 10, 15: 10,
    16: 11, 17: 11, 18: 11, 19: 12, 20: 13,
}

# Cantrip count (chosen from Wizard list, not counting AT's bonus Mage Hand)
THIRD_CASTER_CANTRIPS: dict[int, int] = {
    **{l: 2 for l in range(3, 10)},
    **{l: 3 for l in range(10, 21)},
}

# School restrictions for third-caster spells
# 2024 PHB: EK and AT have no school restrictions — any Wizard spell is valid.
THIRD_CASTER_FREE_CHOICE_LEVELS = set()  # all levels are free-choice
EK_SCHOOL_RESTRICTION: list[str] = []
AT_SCHOOL_RESTRICTION: list[str] = []

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
    if spellcasting_type == "third":
        slots = THIRD_CASTER_SLOTS.get(char_level, [])
        return len(slots)  # number of slot tiers = max spell level
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
# "tier_level" is the character level at which the tier kicks in.
# Cleric domains: tiers at 3/5/7/9 (2024 PHB). Ranger subclasses: tiers at 3/5/9/13/17.
SUBCLASS_ALWAYS_PREPARED: dict[str, dict[int, list[str]]] = {
    # ── Cleric Domains (2024 PHB — corrected from 2014 data) ──
    "Life Domain": {
        3: ["Aid", "Bless", "Cure Wounds", "Lesser Restoration"],
        5: ["Mass Healing Word", "Revivify"],
        7: ["Aura of Life", "Death Ward"],
        9: ["Greater Restoration", "Mass Cure Wounds"],
    },
    "Light Domain": {
        3: ["Burning Hands", "Faerie Fire", "Scorching Ray", "See Invisibility"],
        5: ["Daylight", "Fireball"],
        7: ["Arcane Eye", "Wall of Fire"],
        9: ["Flame Strike", "Scrying"],
    },
    "Trickery Domain": {
        3: ["Charm Person", "Disguise Self", "Invisibility", "Pass without Trace"],
        5: ["Hypnotic Pattern", "Nondetection"],
        7: ["Confusion", "Dimension Door"],
        9: ["Dominate Person", "Modify Memory"],
    },
    "War Domain": {
        3: ["Guiding Bolt", "Magic Weapon", "Shield of Faith", "Spiritual Weapon"],
        5: ["Crusader's Mantle", "Spirit Guardians"],
        7: ["Fire Shield", "Freedom of Movement"],
        9: ["Hold Monster", "Steel Wind Strike"],
    },
    # ── Ranger Subclasses ──
    # Fey Wanderer / Gloom Stalker: one spell per tier, stored source="subclass", always_prepared=True.
    # Beast Master and Hunter have no patron-style auto-prepared lists.
    "Fey Wanderer": {
        3:  ["Charm Person"],
        5:  ["Misty Step"],
        9:  ["Summon Fey"],
        13: ["Dimension Door"],
        17: ["Mislead"],
    },
    "Gloom Stalker": {
        3:  ["Disguise Self"],
        5:  ["Rope Trick"],
        9:  ["Fear"],
        13: ["Greater Invisibility"],
        17: ["Seeming"],
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

# ---------------------------------------------------------------------------
# Phase B data tables
# ---------------------------------------------------------------------------

# Weapon mastery — all mastery-property weapons, tagged by category
_ALL_WEAPONS_WITH_MASTERY = [
    # Simple Melee
    {"name": "Club",           "mastery": "Slow",   "category": "Simple Melee"},
    {"name": "Dagger",         "mastery": "Nick",   "category": "Simple Melee"},
    {"name": "Handaxe",        "mastery": "Vex",    "category": "Simple Melee"},
    {"name": "Javelin",        "mastery": "Slow",   "category": "Simple Melee"},
    {"name": "Light Hammer",   "mastery": "Nick",   "category": "Simple Melee"},
    {"name": "Mace",           "mastery": "Topple", "category": "Simple Melee"},
    {"name": "Quarterstaff",   "mastery": "Topple", "category": "Simple Melee"},
    {"name": "Sickle",         "mastery": "Nick",   "category": "Simple Melee"},
    {"name": "Spear",          "mastery": "Sap",    "category": "Simple Melee"},
    # Simple Ranged
    {"name": "Dart",           "mastery": "Vex",    "category": "Simple Ranged"},
    {"name": "Light Crossbow", "mastery": "Slow",   "category": "Simple Ranged"},
    {"name": "Shortbow",       "mastery": "Vex",    "category": "Simple Ranged"},
    {"name": "Sling",          "mastery": "Slow",   "category": "Simple Ranged"},
    # Martial Melee
    {"name": "Battleaxe",      "mastery": "Topple", "category": "Martial Melee"},
    {"name": "Flail",          "mastery": "Sap",    "category": "Martial Melee"},
    {"name": "Glaive",         "mastery": "Graze",  "category": "Martial Melee"},
    {"name": "Greataxe",       "mastery": "Cleave", "category": "Martial Melee"},
    {"name": "Greatsword",     "mastery": "Graze",  "category": "Martial Melee"},
    {"name": "Halberd",        "mastery": "Cleave", "category": "Martial Melee"},
    {"name": "Lance",          "mastery": "Topple", "category": "Martial Melee"},
    {"name": "Longsword",      "mastery": "Sap",    "category": "Martial Melee"},
    {"name": "Maul",           "mastery": "Topple", "category": "Martial Melee"},
    {"name": "Morningstar",    "mastery": "Sap",    "category": "Martial Melee"},
    {"name": "Pike",           "mastery": "Push",   "category": "Martial Melee"},
    {"name": "Rapier",         "mastery": "Vex",    "category": "Martial Melee"},
    {"name": "Scimitar",       "mastery": "Nick",   "category": "Martial Melee"},
    {"name": "Shortsword",     "mastery": "Vex",    "category": "Martial Melee"},
    {"name": "Trident",        "mastery": "Topple", "category": "Martial Melee"},
    {"name": "War Pick",       "mastery": "Sap",    "category": "Martial Melee"},
    {"name": "Warhammer",      "mastery": "Push",   "category": "Martial Melee"},
    {"name": "Whip",           "mastery": "Slow",   "category": "Martial Melee"},
    # Martial Ranged
    {"name": "Blowgun",        "mastery": "Vex",    "category": "Martial Ranged"},
    {"name": "Hand Crossbow",  "mastery": "Vex",    "category": "Martial Ranged"},
    {"name": "Heavy Crossbow", "mastery": "Push",   "category": "Martial Ranged"},
    {"name": "Longbow",        "mastery": "Slow",   "category": "Martial Ranged"},
]

# Rogue proficiency covers only simple weapons + these specific martials
_ROGUE_WEAPON_PROFICIENCY = {
    "Club", "Dagger", "Handaxe", "Javelin", "Light Hammer", "Mace",
    "Quarterstaff", "Sickle", "Spear",
    "Dart", "Light Crossbow", "Shortbow", "Sling",
    "Hand Crossbow", "Longsword", "Rapier", "Shortsword",
}

# Per-class eligible weapon catalog (Barbarian restricted to Melee per 2024 PHB)
WEAPON_MASTERY_CATALOG: dict[str, list[dict]] = {
    "Barbarian": [w for w in _ALL_WEAPONS_WITH_MASTERY
                  if "Melee" in w["category"]],
    "Fighter":   list(_ALL_WEAPONS_WITH_MASTERY),
    "Ranger":    list(_ALL_WEAPONS_WITH_MASTERY),
    "Paladin":   list(_ALL_WEAPONS_WITH_MASTERY),
    "Rogue":     [w for w in _ALL_WEAPONS_WITH_MASTERY
                  if w["name"] in _ROGUE_WEAPON_PROFICIENCY],
}

# class_name → {class_level: (mode, pick_count)}
WEAPON_MASTERY_LEVELS: dict[str, dict[int, tuple]] = {
    "Barbarian": {1: ("initial", 2), 4: ("add_one", 1), 10: ("add_one", 1)},
    "Fighter":   {1: ("initial", 3), 4: ("add_one", 1), 10: ("add_one", 1), 16: ("add_one", 1)},
    "Ranger":    {1: ("initial", 2)},
    "Rogue":     {1: ("initial", 2)},
    "Paladin":   {1: ("initial", 2)},  # out of scope but listed for completeness
}

BARBARIAN_PRIMAL_KNOWLEDGE_SKILLS = [
    "Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival",
]

BATTLE_MASTER_MANEUVERS = [
    {"key": "ambush",              "name": "Ambush",              "cost": "1 die",
     "desc": "Add the Superiority Die to an Initiative or Stealth roll."},
    {"key": "bait_and_switch",     "name": "Bait and Switch",     "cost": "1 die",
     "desc": "Swap places with an adjacent willing ally; one of you gains a bonus to AC equal to the die result until the start of your next turn."},
    {"key": "commanders_strike",   "name": "Commander's Strike",  "cost": "1 die",
     "desc": "Use a Bonus Action to direct an ally who can hear you to strike; they use their Reaction to make one attack, adding the die to the damage roll."},
    {"key": "commanding_presence", "name": "Commanding Presence", "cost": "1 die",
     "desc": "Add the Superiority Die to an Intimidation, Performance, or Persuasion check."},
    {"key": "disarming_attack",    "name": "Disarming Attack",    "cost": "1 die",
     "desc": "On hit: add the die to damage; target must succeed on a Strength save or drop one held item of your choice.",
     "save_ability": "Strength"},
    {"key": "distracting_strike",  "name": "Distracting Strike",  "cost": "1 die",
     "desc": "On hit: add the die to damage; the next attack roll against the target before the start of your next turn has Advantage."},
    {"key": "evasive_footwork",    "name": "Evasive Footwork",    "cost": "1 die",
     "desc": "Add the Superiority Die to your AC for the rest of the turn while you move."},
    {"key": "feinting_attack",     "name": "Feinting Attack",     "cost": "1 die",
     "desc": "Spend a Bonus Action to feint against one adjacent creature; you have Advantage on your next attack roll against it this turn, and add the die to the damage roll on a hit."},
    {"key": "goading_attack",      "name": "Goading Attack",      "cost": "1 die",
     "desc": "On hit: add the die to damage; target must succeed on a Wisdom save or have Disadvantage on all attack rolls against targets other than you until the end of your next turn.",
     "save_ability": "Wisdom"},
    {"key": "lunging_attack",      "name": "Lunging Attack",      "cost": "1 die",
     "desc": "Gain +5 ft. reach on one attack; add the die to the damage roll on a hit."},
    {"key": "maneuvering_attack",  "name": "Maneuvering Attack",  "cost": "1 die",
     "desc": "On hit: add the die to damage; one friendly creature within 30 ft. can use its Reaction to move up to half its Speed without provoking Opportunity Attacks."},
    {"key": "menacing_attack",     "name": "Menacing Attack",     "cost": "1 die",
     "desc": "On hit: add the die to damage; target must succeed on a Wisdom save or be Frightened until the end of your next turn.",
     "save_ability": "Wisdom"},
    {"key": "parry",               "name": "Parry",               "cost": "1 die",
     "desc": "Reaction: when a creature hits you with a melee attack, reduce the damage taken by the die result + your Dexterity modifier."},
    {"key": "precision_attack",    "name": "Precision Attack",    "cost": "1 die",
     "desc": "Add the Superiority Die to one attack roll before you know whether it hits or misses."},
    {"key": "pushing_attack",      "name": "Pushing Attack",      "cost": "1 die",
     "desc": "On hit: add the die to damage; target must succeed on a Strength save or be pushed 15 ft. directly away from you.",
     "save_ability": "Strength"},
    {"key": "rally",               "name": "Rally",               "cost": "1 die",
     "desc": "Bonus Action: choose one ally who can see and hear you; that creature gains Temporary HP equal to the die result + your Charisma modifier."},
    {"key": "riposte",             "name": "Riposte",             "cost": "1 die",
     "desc": "Reaction: when a creature misses you with a melee attack, you can make one melee attack against it and add the die to the damage roll on a hit."},
    {"key": "sweeping_attack",     "name": "Sweeping Attack",     "cost": "1 die",
     "desc": "On hit: if another creature is within your reach and adjacent to the original target, deal damage equal to the die result to it (no attack roll)."},
    {"key": "tactical_assessment", "name": "Tactical Assessment", "cost": "1 die",
     "desc": "Add the Superiority Die to a History, Insight, or Perception check."},
    {"key": "trip_attack",         "name": "Trip Attack",         "cost": "1 die",
     "desc": "On hit: add the die to damage; if the target is Large or smaller it must succeed on a Strength save or be knocked Prone.",
     "save_ability": "Strength"},
]

ARTISAN_TOOLS = [
    "Alchemist's Supplies", "Brewer's Supplies", "Calligrapher's Supplies",
    "Carpenter's Tools", "Cartographer's Tools", "Cobbler's Tools",
    "Cook's Utensils", "Glassblower's Tools", "Jeweler's Tools",
    "Leatherworker's Tools", "Mason's Tools", "Painter's Supplies",
    "Potter's Tools", "Smith's Tools", "Tinker's Tools",
    "Weaver's Tools", "Woodcarver's Tools",
]

FIGHTER_STUDENT_OF_WAR_SKILLS = [
    "Acrobatics", "Animal Handling", "Athletics", "History",
    "Insight", "Intimidation", "Persuasion", "Stealth",
]

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
# Phase B helpers
# ---------------------------------------------------------------------------

def _owned_weapon_masteries(char) -> list[str]:
    return [
        (c.choice_value or {}).get("weapon", "")
        for c in char.choices
        if c.feature_key == "weapon_mastery"
    ]


def _owned_maneuver_keys(char) -> list[str]:
    return [
        (c.choice_value or {}).get("key", "")
        for c in char.choices
        if c.feature_key == "maneuver"
    ]


# ---------------------------------------------------------------------------
# Phase B step builders
# ---------------------------------------------------------------------------

def _weapon_mastery_step(class_name: str, next_level: int, char) -> dict | None:
    mode_data = WEAPON_MASTERY_LEVELS.get(class_name, {}).get(next_level)
    if not mode_data:
        return None
    mode, pick = mode_data
    catalog = WEAPON_MASTERY_CATALOG.get(class_name, [])
    owned = _owned_weapon_masteries(char)
    eligible = catalog if mode == "initial" else [
        w for w in catalog if w["name"] not in owned
    ]
    return {
        "id":               f"weapon_mastery_l{next_level}",
        "kind":             "weapon_mastery",
        "label":            "Weapon Mastery",
        "required":         True,
        "mode":             mode,
        "pick":             pick,
        "eligible_weapons": eligible,
        "current_masteries": owned,
        "description":      (
            f"Choose {pick} weapon{'s' if pick > 1 else ''} to apply Weapon Mastery properties to. "
            "You can swap one choice on each Long Rest."
        ),
    }


def _primal_knowledge_step(char, next_level: int) -> dict:
    owned = {sp.skill_name for sp in char.skill_proficiencies}
    eligible = [s for s in BARBARIAN_PRIMAL_KNOWLEDGE_SKILLS if s not in owned]
    return {
        "id":          f"primal_knowledge_l{next_level}",
        "kind":        "primal_knowledge",
        "label":       "Primal Knowledge — Bonus Skill",
        "required":    True,
        "options":     eligible or BARBARIAN_PRIMAL_KNOWLEDGE_SKILLS,
        "description": "Gain proficiency in one additional skill from the Barbarian list.",
    }


def _blessed_strikes_step(next_level: int) -> dict:
    return {
        "id":          f"blessed_strikes_l{next_level}",
        "kind":        "blessed_strikes",
        "label":       "Blessed Strikes (permanent choice)",
        "required":    True,
        "options": [
            {"key": "divine_strike",       "name": "Divine Strike",
             "description": "Once per turn when you hit a creature with a weapon attack, deal an extra 1d8 damage of a type you choose (Necrotic or Radiant). Increases to 2d8 at level 14."},
            {"key": "potent_spellcasting", "name": "Potent Spellcasting",
             "description": "Add your Wisdom modifier to the damage roll of any Cleric cantrip you cast."},
        ],
    }


def _blessed_strikes_damage_step(next_level: int) -> dict:
    return {
        "id":          f"blessed_strikes_damage_l{next_level}",
        "kind":        "blessed_strikes_damage",
        "label":       "Divine Strike — Damage Type",
        "required":    True,
        "options":     [
            {"key": "necrotic", "name": "Necrotic"},
            {"key": "radiant",  "name": "Radiant"},
        ],
        "description": "Choose the damage type for your Divine Strike.",
    }


def _maneuvers_step(char, pick: int, next_level: int) -> dict:
    owned_keys = set(_owned_maneuver_keys(char))
    available = [m for m in BATTLE_MASTER_MANEUVERS if m["key"] not in owned_keys]
    return {
        "id":          f"maneuvers_l{next_level}",
        "kind":        "maneuvers",
        "label":       f"Combat Maneuvers — Choose {pick}",
        "required":    True,
        "pick":        pick,
        "options":     available,
        "owned":       [m for m in BATTLE_MASTER_MANEUVERS if m["key"] in owned_keys],
    }


def _student_of_war_step(char, next_level: int) -> dict:
    owned_skills = {sp.skill_name for sp in char.skill_proficiencies}
    eligible_skills = [s for s in FIGHTER_STUDENT_OF_WAR_SKILLS if s not in owned_skills]
    return {
        "id":            f"student_of_war_l{next_level}",
        "kind":          "student_of_war",
        "label":         "Student of War",
        "required":      True,
        "tool_options":  ARTISAN_TOOLS,
        "skill_options": eligible_skills or FIGHTER_STUDENT_OF_WAR_SKILLS,
        "description":   "Gain proficiency with one Artisan's Tool and one additional skill from the Fighter list.",
    }


def _war_bond_step(char, next_level: int) -> dict:
    return {
        "id":          f"war_bond_l{next_level}",
        "kind":        "war_bond",
        "label":       "War Bond",
        "required":    True,
        "max_bonds":   2,
        "description": (
            "Perform a 1-hour ritual to bond with up to 2 weapons. Bonded weapons "
            "can't be disarmed. You can summon a bonded weapon to your hand as a Bonus Action."
        ),
    }


def _third_caster_cantrips_step(subclass_name: str, pick: int, next_level: int) -> dict:
    is_at = (subclass_name == "Arcane Trickster")
    grant_mage_hand = is_at and next_level == 3
    return {
        "id":                 f"third_caster_cantrips_l{next_level}",
        "kind":               "third_caster_cantrips",
        "label":              f"New Cantrip{'s' if pick > 1 else ''} (Wizard List)",
        "required":           True,
        "pick":               pick,
        "mage_hand_auto_grant": grant_mage_hand,
        "exclude_spells":     ["Mage Hand"] if is_at else [],
        "description":        (
            f"Choose {pick} cantrip{'s' if pick > 1 else ''} from the Wizard spell list."
            + (" Mage Hand will also be granted automatically." if grant_mage_hand else "")
        ),
    }


def _third_caster_spells_step(
    char, pick: int, max_sl: int,
    school_restriction: list[str], free_choice: bool, next_level: int,
) -> dict:
    owned_ids = [cs.spell_id for cs in char.spells]
    restriction_note = (
        "" if free_choice
        else f" Must be {' or '.join(s.title() for s in school_restriction)}."
    )
    return {
        "id":                f"third_caster_spells_l{next_level}",
        "kind":              "third_caster_spells",
        "label":             f"New Spell{'s' if pick > 1 else ''} (Wizard List)",
        "required":          True,
        "pick":              pick,
        "max_spell_level":   max_sl,
        "school_restriction": [] if free_choice else school_restriction,
        "free_choice":       free_choice,
        "owned_spell_ids":   owned_ids,
        "description":       f"Choose {pick} spell{'s' if pick > 1 else ''} from the Wizard spell list.{restriction_note}",
    }


def _hunters_prey_step(next_level: int) -> dict:
    return {
        "id":       f"hunters_prey_l{next_level}",
        "kind":     "hunters_prey",
        "label":    "Hunter's Prey (permanent choice)",
        "required": True,
        "options": [
            {"key": "colossus_slayer", "name": "Colossus Slayer",
             "description": "Once per turn when you hit a creature with a weapon attack, deal an extra 1d8 damage if the creature is below its HP maximum."},
            {"key": "horde_breaker", "name": "Horde Breaker",
             "description": "Once per turn when you make a weapon attack, you can make another attack with the same weapon against a different creature within 5 ft. of the original target."},
        ],
    }


def _defensive_tactics_step(next_level: int) -> dict:
    return {
        "id":       f"defensive_tactics_l{next_level}",
        "kind":     "defensive_tactics",
        "label":    "Defensive Tactics (permanent choice)",
        "required": True,
        "options": [
            {"key": "escape_the_horde", "name": "Escape the Horde",
             "description": "Opportunity Attacks against you have Disadvantage."},
            {"key": "multiattack_defense", "name": "Multiattack Defense",
             "description": "When a creature hits you with an attack, gain +4 to AC until the end of the turn against all subsequent attacks from that creature."},
        ],
    }


def _otherworldly_glamour_step(char, next_level: int) -> dict:
    owned = {sp.skill_name for sp in char.skill_proficiencies}
    eligible = [s for s in ["Deception", "Performance", "Persuasion"] if s not in owned]
    return {
        "id":          f"otherworldly_glamour_l{next_level}",
        "kind":        "otherworldly_glamour",
        "label":       "Otherworldly Glamour — Skill Proficiency",
        "required":    True,
        "options":     eligible or ["Deception", "Performance", "Persuasion"],
        "description": (
            "You gain a bonus to Charisma checks equal to your Wisdom modifier (minimum +1). "
            "Choose one Charisma skill to gain proficiency in."
        ),
    }


def _beast_companion_step(next_level: int) -> dict:
    return {
        "id":       f"beast_companion_l{next_level}",
        "kind":     "beast_companion",
        "label":    "Primal Companion — Choose Beast",
        "required": True,
        "options": [
            {"key": "beast_of_the_land", "name": "Beast of the Land",
             "description": "Medium beast, 5 ft. Speed. Charge: Knock Prone on hit (Str save). Maul: d8 Slashing + Str bonus."},
            {"key": "beast_of_the_sea",  "name": "Beast of the Sea",
             "description": "Medium beast, 5 ft. Speed + 60 ft. Swim. Binding Strike: Restrained on hit (Str save). Maul: d6 Bludgeoning or Piercing + Str bonus."},
            {"key": "beast_of_the_sky",  "name": "Beast of the Sky",
             "description": "Small beast, 10 ft. Speed + 60 ft. Fly. Shred: d4 Slashing + Str bonus. Can't carry Medium+ riders."},
        ],
    }


def _iron_mind_step(char, next_level: int) -> dict:
    has_wis_save = any(
        (c.choice_value or {}).get("save_proficiency") == "Wisdom"
        for c in char.choices
    )
    if not has_wis_save:
        return {
            "id":           f"iron_mind_l{next_level}",
            "kind":         "iron_mind",
            "label":        "Iron Mind — Wisdom Save Proficiency",
            "required":     True,
            "auto_grant":   True,
            "granted_save": "Wisdom",
            "description":  "You gain proficiency in Wisdom saving throws.",
        }
    return {
        "id":          f"iron_mind_l{next_level}",
        "kind":        "iron_mind",
        "label":       "Iron Mind — Save Proficiency Choice",
        "required":    True,
        "auto_grant":  False,
        "options":     ["Intelligence", "Charisma"],
        "description": "You already have Wisdom save proficiency. Choose Intelligence or Charisma saves instead.",
    }


def _rage_of_wilds_step(next_level: int) -> dict:
    return {
        "id":       f"rage_of_wilds_l{next_level}",
        "kind":     "rage_of_wilds",
        "label":    "Rage of the Wilds — Animal Spirit",
        "required": True,
        "options": [
            {"key": "bear",  "name": "Bear",
             "description": "While Raging, you have Resistance to all damage types except Psychic."},
            {"key": "eagle", "name": "Eagle",
             "description": "While Raging, you can use a Bonus Action to Dash or Disengage. Opportunity Attacks against you have Disadvantage."},
            {"key": "wolf",  "name": "Wolf",
             "description": "While Raging, allied creatures within 10 ft. have Advantage on attack rolls against any enemy within 5 ft. of you."},
        ],
        "description": (
            "Your Rage channels a primal animal spirit. Choose which spirit empowers you — "
            "you can change this spirit at the end of each Long Rest."
        ),
    }


def _aspect_of_wilds_step(next_level: int) -> dict:
    return {
        "id":       f"aspect_of_wilds_l{next_level}",
        "kind":     "aspect_of_wilds",
        "label":    "Aspect of the Wilds (initial choice)",
        "required": True,
        "options": [
            {"key": "owl",    "name": "Owl",
             "description": "You gain Darkvision with a range of 60 ft. If you already have Darkvision, its range increases by 60 ft."},
            {"key": "panther","name": "Panther",
             "description": "You gain a Climb Speed equal to your Speed."},
            {"key": "salmon", "name": "Salmon",
             "description": "You gain a Swim Speed equal to your Speed."},
        ],
        "description": "Choose your Aspect of the Wilds. You can change this on each Long Rest.",
    }


def _power_of_wilds_step(next_level: int) -> dict:
    return {
        "id":       f"power_of_wilds_l{next_level}",
        "kind":     "power_of_wilds",
        "label":    "Power of the Wilds (initial choice)",
        "required": True,
        "options": [
            {"key": "falcon", "name": "Falcon",
             "description": "While not wearing Heavy armor, you have a Fly Speed equal to your Speed."},
            {"key": "lion",   "name": "Lion",
             "description": "You can make an additional attack as part of your Attack action once per turn."},
            {"key": "ram",    "name": "Ram",
             "description": "When you hit a creature with a weapon attack, push it up to 10 ft. directly away from you (Str save negates)."},
        ],
        "description": "Choose your Power of the Wilds. You can change this on each Long Rest.",
    }


def _divine_fury_step(next_level: int) -> dict:
    return {
        "id":       f"divine_fury_l{next_level}",
        "kind":     "divine_fury",
        "label":    "Divine Fury — Damage Type",
        "required": True,
        "options": [
            {"key": "necrotic", "name": "Necrotic",
             "description": "Once per turn while Raging, when you hit with a weapon attack deal extra Necrotic damage = 1d6 + half your Barbarian level."},
            {"key": "radiant",  "name": "Radiant",
             "description": "Once per turn while Raging, when you hit with a weapon attack deal extra Radiant damage = 1d6 + half your Barbarian level."},
        ],
    }


def _assassins_tools_step(char, next_level: int) -> dict:
    already_done = any(
        c.feature_key == "assassins_tools" for c in char.choices
    )
    return {
        "id":           f"assassins_tools_l{next_level}",
        "kind":         "assassins_tools",
        "label":        "Assassin's Tools",
        "required":     not already_done,
        "already_done": already_done,
        "grants": ["Disguise Kit", "Poisoner's Kit"],
        "description":  (
            "You gain proficiency with a Disguise Kit and a Poisoner's Kit. "
            "Both are added to your tool proficiencies."
        ),
    }


def _druidic_warrior_cantrips_step(next_level: int) -> dict:
    return {
        "id":          f"druidic_warrior_cantrips_l{next_level}",
        "kind":        "druidic_warrior_cantrips",
        "label":       "Druidic Warrior — 2 Druid Cantrips",
        "required":    True,
        "pick":        2,
        "spell_list":  "druid",
        "description": "Choose 2 cantrips from the Druid spell list. These cantrips use Wisdom as your spellcasting ability.",
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def required_steps(
    char, cc, cls, db: Session,
    pending_subclass_id: int | None = None,
) -> list[dict]:
    """
    Return the ordered list of step dicts for the player level-up wizard.

    pending_subclass_id: when the player has just picked a subclass during this wizard
    run but the choice hasn't been committed yet, pass the subclass id here so
    subclass-specific L3 steps are included in the same response.
    """
    from ..models.content import Subclass as SubclassModel

    next_level = cc.level + 1
    class_name = cls.name

    # Committed subclass (from DB)
    subclass = cc.subclass
    subclass_name = subclass.name if subclass else None

    # Effective subclass — may include a pending (uncommitted) pick at L3
    if pending_subclass_id and cc.subclass_id is None:
        eff_subclass = db.query(SubclassModel).filter(
            SubclassModel.id == pending_subclass_id
        ).first() or subclass
    else:
        eff_subclass = subclass
    eff_subclass_name = eff_subclass.name if eff_subclass else None

    sp_type = cls.spellcasting_type or ""
    max_sl = max_spell_level(sp_type, next_level) if sp_type else 0

    steps: list[dict] = []

    # ── 1. HP — always first ────────────────────────────────────────────────
    steps.append(_hp_step(char, cls, subclass_name, next_level))

    # ── 2. Weapon Mastery ───────────────────────────────────────────────────
    # At levels defined in WEAPON_MASTERY_LEVELS[class_name].
    if class_name in WEAPON_MASTERY_LEVELS and next_level in WEAPON_MASTERY_LEVELS[class_name]:
        mode, expected_pick = WEAPON_MASTERY_LEVELS[class_name][next_level]
        wm_at_level = [
            c for c in char.choices
            if c.feature_key == "weapon_mastery" and c.level == next_level
        ]
        if len(wm_at_level) < expected_pick:
            wm_step = _weapon_mastery_step(class_name, next_level, char)
            if wm_step:
                steps.append(wm_step)

    # ── 3. Subclass selection (L3) ──────────────────────────────────────────
    if next_level == 3 and cc.subclass_id is None:
        subclass_options = [
            {"id": s.id, "name": s.name, "description": s.description,
             "features": [f for f in (s.features or []) if f.get("level") == next_level]}
            for s in cls.subclasses
        ]
        if subclass_options:
            steps.append(_subclass_step(subclass_options, next_level))

    # ── 4. Subclass-specific L3 steps ──────────────────────────────────────
    # Fire once we know the effective subclass (committed OR pending).
    if next_level == 3 and eff_subclass_name:
        _done = lambda fk: any(c.feature_key == fk for c in char.choices)

        if eff_subclass_name == "Path of the Wild Heart":
            if not _done("rage_of_wilds"):
                steps.append(_rage_of_wilds_step(next_level))

        elif eff_subclass_name == "Path of the Zealot":
            if not _done("divine_fury"):
                steps.append(_divine_fury_step(next_level))

        elif eff_subclass_name == "Beast Master":
            if not _done("beast_companion"):
                steps.append(_beast_companion_step(next_level))

        elif eff_subclass_name == "Fey Wanderer":
            if not _done("otherworldly_glamour"):
                steps.append(_otherworldly_glamour_step(char, next_level))

        elif eff_subclass_name == "Hunter":
            if not _done("hunters_prey"):
                steps.append(_hunters_prey_step(next_level))

        elif eff_subclass_name == "Battle Master":
            if not _done("maneuver"):
                steps.append(_maneuvers_step(char, 3, next_level))
            if not _done("student_of_war"):
                steps.append(_student_of_war_step(char, next_level))

        elif eff_subclass_name == "Eldritch Knight":
            if not _done("war_bond"):
                steps.append(_war_bond_step(char, next_level))
            # Cantrips: 2 from Wizard list (no Mage Hand auto-grant for EK)
            ek_cantrips_done = any(
                c.feature_key == "third_caster_cantrip" and c.level == next_level
                for c in char.choices
            )
            if not ek_cantrips_done:
                steps.append(_third_caster_cantrips_step("Eldritch Knight", 2, next_level))
            # Spells: 3 total; 1 may be any school
            ek_spells_done = any(
                c.feature_key == "third_caster_spell" and c.level == next_level
                for c in char.choices
            )
            if not ek_spells_done:
                steps.append(_third_caster_spells_step(
                    char, 3, max_spell_level("third", next_level),
                    [], True, next_level,
                ))

        elif eff_subclass_name == "Arcane Trickster":
            # Cantrips: 2 from Wizard list + Mage Hand auto-grant
            at_cantrips_done = any(
                c.feature_key == "third_caster_cantrip" and c.level == next_level
                for c in char.choices
            )
            if not at_cantrips_done:
                steps.append(_third_caster_cantrips_step("Arcane Trickster", 2, next_level))
            # Spells: 3 total; 1 may be any school
            at_spells_done = any(
                c.feature_key == "third_caster_spell" and c.level == next_level
                for c in char.choices
            )
            if not at_spells_done:
                steps.append(_third_caster_spells_step(
                    char, 3, max_spell_level("third", next_level),
                    [], True, next_level,
                ))

        elif eff_subclass_name == "Assassin":
            steps.append(_assassins_tools_step(char, next_level))

    # ── 5. Primal Knowledge (Barbarian L3) ─────────────────────────────────
    if class_name == "Barbarian" and next_level == 3:
        if not any(c.feature_key == "primal_knowledge" for c in char.choices):
            steps.append(_primal_knowledge_step(char, next_level))

    # ── 6. ASI / Epic Boon ─────────────────────────────────────────────────
    asi_levels = _get_asi_levels(class_name)
    if next_level in asi_levels:
        if next_level == 19:
            steps.append(_epic_boon_step(next_level))
        else:
            steps.append(_asi_step(char, next_level))

    # ── 7. Fighting Style (Paladin L2, Ranger L2) ───────────────────────────
    if class_name in FIGHTING_STYLE_AT and next_level == FIGHTING_STYLE_AT[class_name]:
        steps.append(_fighting_style_step(class_name, next_level))
    # Fighter can swap fighting style on every level-up (optional)
    if class_name == "Fighter" and next_level >= 2:
        has_style = any(c.feature_key == "fighting_style" for c in char.choices)
        if next_level == 1:
            steps.append(_fighting_style_step(class_name, next_level))
        elif has_style:
            steps.append(_fighter_swap_style_step(next_level))

    # ── 8. Druidic Warrior cantrip follow-up (Ranger L2) ────────────────────
    # Only emit when the fighting style was already committed as Druidic Warrior
    # (i.e., this is a re-entry after a partial level-up, or the apply path
    # calls required_steps again mid-run).  Initial wizard runs can't see
    # in-flight choices, so the apply path handles this edge case instead.
    if class_name == "Ranger" and next_level == 2:
        druidic_already = any(c.feature_key == "druidic_warrior_cantrips" for c in char.choices)
        if not druidic_already:
            # Check if Druidic Warrior was committed as a fighting style choice
            dw_chosen = any(
                c.feature_key == "fighting_style" and c.level == 2
                and "druidic" in str(c.choice_value or "").lower()
                for c in char.choices
            )
            if dw_chosen:
                steps.append(_druidic_warrior_cantrips_step(next_level))

    # ── 9. Expertise ────────────────────────────────────────────────────────
    if class_name in EXPERTISE_GAINS:
        pick = EXPERTISE_GAINS[class_name].get(next_level, 0)
        if pick > 0:
            steps.append(_expertise_step(char, pick, next_level))

    # ── 10. Cantrip gains (class cantrips, not third-caster) ────────────────
    cantrip_gains = CANTRIP_GAINS.get(class_name, {}).get(next_level, 0)
    if cantrip_gains > 0:
        steps.append(_cantrips_step(cantrip_gains, next_level))

    # ── 11. Spell / spellbook gains (known-spell casters) ───────────────────
    if class_name in KNOWN_SPELL_GAINS:
        spell_gains = KNOWN_SPELL_GAINS[class_name].get(next_level, 0)
        if spell_gains > 0 and max_sl > 0:
            steps.append(_spells_new_step(spell_gains, next_level, max_sl, class_name))

    # ── 12. Third-caster spell/cantrip gains (EK L4+ and AT L4+) ───────────
    # L3 gains are handled in the subclass-specific block above.
    is_ek = (class_name == "Fighter" and subclass_name == "Eldritch Knight")
    is_at = (class_name == "Rogue"   and subclass_name == "Arcane Trickster")
    if (is_ek or is_at) and next_level >= 4:
        prev_spells = THIRD_CASTER_SPELLS_KNOWN.get(next_level - 1, 0)
        curr_spells = THIRD_CASTER_SPELLS_KNOWN.get(next_level, 0)
        spell_gain = curr_spells - prev_spells

        prev_cantrips = THIRD_CASTER_CANTRIPS.get(next_level - 1, 0)
        curr_cantrips = THIRD_CASTER_CANTRIPS.get(next_level, 0)
        cantrip_gain = curr_cantrips - prev_cantrips

        third_max_sl = max_spell_level("third", next_level)
        school: list[str] = []  # 2024 PHB: no school restrictions for EK/AT
        free = True  # all picks are free-choice
        sub_for_cantrip = "Eldritch Knight" if is_ek else "Arcane Trickster"

        if cantrip_gain > 0:
            steps.append(_third_caster_cantrips_step(sub_for_cantrip, cantrip_gain, next_level))
        if spell_gain > 0 and third_max_sl > 0:
            steps.append(_third_caster_spells_step(
                char, spell_gain, third_max_sl, school, free, next_level,
            ))

    # ── 13. Spell swap (known-spell casters) ───────────────────────────────
    # Bard and Ranger are prepared casters — excluded here.
    if class_name in ("Sorcerer", "Warlock", "Wizard"):
        if next_level >= 2 and max_sl > 0:
            steps.append(_spell_swap_step(next_level, max_sl))

    # ── 14. Blessed Strikes (Cleric L7) ────────────────────────────────────
    if class_name == "Cleric" and next_level == 7:
        bs_done = any(c.feature_key == "blessed_strikes" for c in char.choices)
        if not bs_done:
            bs = _blessed_strikes_step(next_level)
            bs["requires_damage_followup"] = True  # frontend chains damage-type step
            steps.append(bs)
        else:
            # Already committed — if divine_strike, check for missing damage type
            bs_choice = next(
                (c for c in char.choices if c.feature_key == "blessed_strikes"), None
            )
            if bs_choice and (bs_choice.choice_value or {}).get("choice") == "divine_strike":
                if not any(c.feature_key == "blessed_strikes_damage" for c in char.choices):
                    steps.append(_blessed_strikes_damage_step(next_level))

    # ── 15. Sorcerer Metamagic ─────────────────────────────────────────────
    if class_name == "Sorcerer":
        mm_pick = METAMAGIC_GAINS.get(next_level, 0)
        if mm_pick > 0:
            steps.append(_metamagic_step(char, mm_pick, next_level))

    # ── 16. Warlock Invocations ─────────────────────────────────────────────
    if class_name == "Warlock":
        invoc_gains = _warlock_invoc_gains(next_level)
        if invoc_gains > 0:
            steps.append(_invocations_new_step(char, invoc_gains, next_level))
        if next_level >= 2:
            steps.append(_invocation_swap_step(char, next_level))

    # ── 17. Warlock Mystic Arcanum ──────────────────────────────────────────
    arcanum_levels = {9: 6, 11: 7, 13: 8, 15: 9}
    if class_name == "Warlock" and next_level in arcanum_levels:
        steps.append(_mystic_arcanum_step(arcanum_levels[next_level], next_level))

    # ── 18. Subclass mid-level steps (L6/L7/L14) ───────────────────────────
    if subclass_name == "Path of the Wild Heart":
        if next_level == 6 and not any(c.feature_key == "aspect_of_wilds" for c in char.choices):
            steps.append(_aspect_of_wilds_step(next_level))
        if next_level == 14 and not any(c.feature_key == "power_of_wilds" for c in char.choices):
            steps.append(_power_of_wilds_step(next_level))

    if subclass_name == "Gloom Stalker" and next_level == 7:
        if not any(c.feature_key == "iron_mind" for c in char.choices):
            steps.append(_iron_mind_step(char, next_level))

    if subclass_name == "Hunter" and next_level == 7:
        if not any(c.feature_key == "defensive_tactics" for c in char.choices):
            steps.append(_defensive_tactics_step(next_level))

    # ── 19. Battle Master maneuvers (L7/L10/L15) ───────────────────────────
    if subclass_name == "Battle Master" and next_level in (7, 10, 15):
        existing_at_level = [
            c for c in char.choices
            if c.feature_key == "maneuver" and c.level == next_level
        ]
        if len(existing_at_level) < 2:
            steps.append(_maneuvers_step(char, 2, next_level))

    # ── 20. Feature choices from class features JSON (choice_required=True) ─
    # Skip choice_keys that are handled by bespoke step builders above (avoid duplicates).
    _BESPOKE_CHOICE_KEYS = {"blessed_strikes", "divine_order"}
    new_class_features = [
        f for f in (cls.features or [])
        if f.get("level") == next_level
        and f.get("choice_key") not in _BESPOKE_CHOICE_KEYS
    ]
    steps.extend(_feature_choice_steps(new_class_features, next_level))

    # ── 21. Subclass feature choices from subclass features JSON ────────────
    if subclass:
        sub_features = [f for f in (subclass.features or []) if f.get("level") == next_level]
        steps.extend(_feature_choice_steps(sub_features, next_level, prefix="sub_"))

    # ── 22. Species level-gated steps ──────────────────────────────────────
    species = char.species if hasattr(char, 'species') else None
    if species:
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


# ---------------------------------------------------------------------------
# Derived class resource counters (pure — no DB writes)
# ---------------------------------------------------------------------------

def class_resources(class_name: str, char_level: int, subclass_name: str | None = None) -> dict:
    """
    Return derived resource counters for a class at a given level.
    All values are deterministic from (class, level, subclass) — the sheet
    renders them directly rather than storing separate columns.
    """
    result: dict = {}

    if class_name == "Barbarian":
        if char_level >= 17:
            result["rage_uses"] = 6
        elif char_level >= 12:
            result["rage_uses"] = 5
        elif char_level >= 6:
            result["rage_uses"] = 4
        elif char_level >= 3:
            result["rage_uses"] = 3
        else:
            result["rage_uses"] = 2

        if char_level >= 16:
            result["rage_damage_bonus"] = 4
        elif char_level >= 9:
            result["rage_damage_bonus"] = 3
        else:
            result["rage_damage_bonus"] = 2

    elif class_name == "Cleric":
        if char_level >= 18:
            result["channel_divinity_uses"] = 4
        elif char_level >= 6:
            result["channel_divinity_uses"] = 3
        else:
            result["channel_divinity_uses"] = 2

        if char_level >= 18:
            result["divine_spark_dice"] = 4
        elif char_level >= 13:
            result["divine_spark_dice"] = 3
        elif char_level >= 7:
            result["divine_spark_dice"] = 2
        else:
            result["divine_spark_dice"] = 1

    elif class_name == "Fighter":
        if char_level >= 20:
            result["attack_count"] = 4
        elif char_level >= 11:
            result["attack_count"] = 3
        elif char_level >= 5:
            result["attack_count"] = 2
        else:
            result["attack_count"] = 1

        if char_level >= 10:
            result["second_wind_uses"] = 4
        elif char_level >= 4:
            result["second_wind_uses"] = 3
        else:
            result["second_wind_uses"] = 2

        result["action_surge_uses"] = (2 if char_level >= 17 else 1) if char_level >= 2 else 0

        if char_level >= 17:
            result["indomitable_uses"] = 3
        elif char_level >= 13:
            result["indomitable_uses"] = 2
        elif char_level >= 9:
            result["indomitable_uses"] = 1
        else:
            result["indomitable_uses"] = 0

        if subclass_name == "Champion":
            result["champion_crit_range"] = 18 if char_level >= 15 else (19 if char_level >= 3 else 20)

        elif subclass_name == "Battle Master":
            if char_level >= 15:
                result["superiority_dice"] = 6
            elif char_level >= 7:
                result["superiority_dice"] = 5
            elif char_level >= 3:
                result["superiority_dice"] = 4
            else:
                result["superiority_dice"] = 0

            if char_level >= 18:
                result["superiority_die"] = "d12"
            elif char_level >= 10:
                result["superiority_die"] = "d10"
            else:
                result["superiority_die"] = "d8"

        elif subclass_name == "Psi Warrior":
            if char_level >= 18:
                result["psionic_die"] = "d12"
            elif char_level >= 10:
                result["psionic_die"] = "d10"
            else:
                result["psionic_die"] = "d6"

    elif class_name == "Ranger":
        if char_level >= 17:
            result["hunters_mark_free_casts"] = 6
        elif char_level >= 13:
            result["hunters_mark_free_casts"] = 5
        elif char_level >= 9:
            result["hunters_mark_free_casts"] = 4
        elif char_level >= 5:
            result["hunters_mark_free_casts"] = 3
        else:
            result["hunters_mark_free_casts"] = 2

    elif class_name == "Rogue":
        result["sneak_attack_dice"] = (char_level + 1) // 2

        if subclass_name == "Soulknife":
            if char_level >= 17:
                result["psionic_die"] = "d12"
            elif char_level >= 11:
                result["psionic_die"] = "d8"
            else:
                result["psionic_die"] = "d6"

    elif class_name == "Sorcerer":
        result["sorcery_points"] = char_level if char_level >= 2 else 0

    return result
