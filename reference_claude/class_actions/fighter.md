# Fighter

<!-- Verified against PHB raw text (chapter 3, Fighter), not the Classes.md project reference,
     since Classes.md is known to contain errors elsewhere.
     Retrofitted to the refined taxonomy: action_type is one of action/bonus_action/move_action/reaction/
     free_action, with "special" reserved for genuine edge cases that don't fit any of the five (e.g.
     Action Surge granting an extra action token, or a dice-pool definition with no single trigger action
     of its own). Free, no-resource triggers that represent a real combat decision are now tagged
     free_action (or move_action when the decision is specifically about movement) instead of "special". -->

## Second Wind
action_type: bonus_action
resource_key: second_wind
min_level: 1
max_uses: 2          # fixed number, increases to 3 at lvl 4 and to 4 at lvl 10. Caps at 4
rest_type: short regain 1, long regain all
description: Regain HP equal to 1d10 + your fighter level. From lvl 5 (Tactical Shift), move up to half your Speed without provoking Opportunity Attacks as part of this Bonus Action.

## Action Surge
action_type: special   # genuine edge case — grants an extra action token, not itself one of the 5 action types
resource_key: action_surge
min_level: 2
max_uses: 1, increases to 2 at lvl 17
rest_type: short regain all, long regain all
description: Take one additional Action this turn (not the Magic action). From lvl 17, usable twice before needing a rest, but only once on the same turn.

## Tactical Mind
action_type: free_action   # no action cost — triggered on a failed ability check
consumes_resource: second_wind   # spends a Second Wind charge — no new pool, no new CharacterResource row
min_level: 2
description: When you fail an ability check, expend a use of Second Wind. Instead of regaining HP, roll 1d10 and add it to the check. If the check still fails, the use is not expended.

## Indomitable
action_type: free_action   # no action cost — triggered on a failed saving throw
resource_key: indomitable
min_level: 9
max_uses: 1          # increases to 2 at lvl 13 and to 3 at lvl 17. Caps at 3
rest_type: long
description: When you fail a saving throw, reroll it with a bonus equal to your Fighter level. You must use the new roll.

## Tactical Master
action_type: free_action   # no resource — unlimited, choice made when attacking with a weapon you have mastery with
min_level: 9
description: When you attack with a weapon whose mastery property you can use, you can replace that property with the Push, Sap, or Slow property for that attack.

<!-- Excluded base-class features (no decision point / no action / no resource): Fighting Style, Weapon
     Mastery (passive proficiency; the Long-Rest swap is a downtime customization, not a combat action),
     Extra Attack/Two Extra Attacks/Three Extra Attacks, Studied Attacks (automatic on-hit rider, no
     decision), Ability Score Improvement, Epic Boon. -->

---

### Subclass: Battle Master

## Combat Superiority (Battle Master)
action_type: special   # genuine edge case — pool definition only, no single trigger action; see Maneuvers below for each one's cost
resource_key: superiority_dice
subclass: battle_master
min_level: 3
max_uses: 4          # d8s; increases to 5 at lvl 7, to 6 at lvl 15
die_size: d8         # becomes d10 at lvl 10, d12 at lvl 18
rest_type: short regain all, long regain all
description: Superiority Dice fuel Maneuvers (below). You know 3 Maneuvers at level 3, plus 2 more at levels 7, 10, and 15.

## Know Your Enemy
action_type: bonus_action
resource_key: know_your_enemy
subclass: battle_master
min_level: 7
max_uses: 1
rest_type: long
bonus_recharge: expend 1 superiority_dice (no action) to restore early
description: Learn a creature's Immunities, Resistances, and Vulnerabilities within 30 ft.

## Relentless
action_type: free_action   # free alternative to spending a die; not its own action
resource_key: relentless
subclass: battle_master
min_level: 15
max_uses: 1
rest_type: per_turn   # resets each turn, not tied to rests
description: Once per turn, when you use a Maneuver, roll 1d8 and use that result instead of expending a Superiority Die.

<!-- Improved/Ultimate Combat Superiority (lvl 10, lvl 18) are folded into Combat Superiority's die_size
     scaling above, not separate blocks. -->

#### Maneuvers (Battle Master) — each consumes 1 superiority_dice; min_level: 3 for all (actual availability also depends on which maneuvers the character has learned, tracked per-character, not by this file)

## Ambush
action_type: free_action   # triggered on a Stealth check or Initiative roll
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: Add the die to a Dexterity (Stealth) check or Initiative roll.

## Bait and Switch
action_type: move_action   # triggered as part of your move on your turn
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: Switch places with a creature within 5 ft. (5+ ft. of movement spent); you or it gains AC equal to the die roll until your next turn.

## Commander's Strike
action_type: free_action   # replaces one attack within the Attack action
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: Forgo one attack to let a willing ally use their Reaction to attack, adding the die to their damage.

## Commanding Presence
action_type: free_action   # triggered on a Charisma check
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: Add the die to a Charisma (Intimidation, Performance, or Persuasion) check.

## Disarming Attack
action_type: free_action   # triggered on a hit
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: On a hit, add the die to damage; target makes a Strength save or drops a held object.

## Distracting Strike
action_type: free_action   # triggered on a hit
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: On a hit, add the die to damage; the next attack against the target by someone else has Advantage before your next turn.

## Evasive Footwork
action_type: bonus_action
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: Take the Disengage action and add the die to your AC until your next turn.

## Feinting Attack
action_type: bonus_action
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: Gain Advantage on your next attack this turn against a creature within 5 ft.; on a hit, add the die to damage.

## Goading Attack
action_type: free_action   # triggered on a hit
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: On a hit, add the die to damage; target makes a Wisdom save or has Disadvantage attacking anyone but you until your next turn.

## Lunging Attack
action_type: bonus_action
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: Take the Dash action; if you move 5+ ft. in a line before a melee hit this turn, add the die to that attack's damage.

## Maneuvering Attack
action_type: free_action   # triggered on a hit
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: On a hit, add the die to damage; a willing ally can use their Reaction to move half their Speed without provoking an Opportunity Attack from your target.

## Menacing Attack
action_type: free_action   # triggered on a hit
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: On a hit, add the die to damage; target makes a Wisdom save or is Frightened until your next turn.

## Parry
action_type: reaction
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: Reduce damage from a melee attack against you by the die roll plus your Strength or Dexterity modifier.

## Precision Attack
action_type: free_action   # triggered on a miss
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: On a miss, add the die to the attack roll, potentially turning it into a hit.

## Pushing Attack
action_type: free_action   # triggered on a hit
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: On a hit, add the die to damage; Large or smaller target makes a Strength save or is pushed 15 ft.

## Rally
action_type: bonus_action
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: Grant an ally within 30 ft. Temporary HP equal to the die roll plus half your Fighter level (round down).

## Riposte
action_type: reaction
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: When a creature misses you with a melee attack, make a melee attack against it; add the die to damage on a hit.

## Sweeping Attack
action_type: free_action   # triggered on a melee hit
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: On a melee hit, deal the die roll (same damage type, no modifier) to another creature within 5 ft. of the target and within your reach.

## Tactical Assessment
action_type: free_action   # triggered on a mental check
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: Add the die to an Intelligence (History or Investigation) check or a Wisdom (Insight) check.

## Trip Attack
action_type: free_action   # triggered on a hit
consumes_resource: superiority_dice
subclass: battle_master
min_level: 3
description: On a hit, add the die to damage; Large or smaller target makes a Strength save or is knocked Prone.

---

### Subclass: Champion

## Remarkable Athlete — Critical Hit Movement
action_type: move_action   # no resource — unlimited, triggered immediately after scoring a Critical Hit
subclass: champion
min_level: 3
description: Immediately after you score a Critical Hit, move up to half your Speed without provoking Opportunity Attacks. (Remarkable Athlete also grants passive Advantage on Initiative rolls and Strength (Athletics) checks — not tracked as a resource.)

<!-- Excluded: Improved Critical / Superior Critical (passive crit-range expansion), Additional Fighting
     Style (passive), Heroic Warrior (free, always-beneficial — gain Heroic Inspiration at the start of
     your turn if you don't have it; no real decision/cost, and Heroic Inspiration itself is a binary flag
     rather than a countable resource), Survivor's Defy Death and Heroic Rally (both fully automatic, no
     decision point). -->

---

### Subclass: Eldritch Knight

<!-- Spellcasting (cantrips, prepared spells, spell slots per the Eldritch Knight Spellcasting table)
     looks like it belongs to your existing spell-slot system (Spell-Slots.md / multiclass spellcasting),
     not this combat-resource seeder — flagging rather than duplicating it here. Let me know if you want
     it in this file too. -->

## War Magic
action_type: free_action   # no resource — unlimited, choice made as part of the Attack action
subclass: eldritch_knight
min_level: 7
description: When you take the Attack action on your turn, replace one of the attacks with a casting of one of your Wizard cantrips that has a casting time of an action. From lvl 18 (Improved War Magic), replace two of the attacks, and the cantrip may be one of your level 1 or level 2 Wizard spells instead.

## Arcane Charge
action_type: free_action   # free rider on Action Surge — no separate action or resource cost
subclass: eldritch_knight
min_level: 15
description: When you use Action Surge, you can teleport up to 30 ft. to an unoccupied space you can see (before or after the additional action).

<!-- Excluded: War Bond (1-hour ritual performed during a Short Rest — downtime customization, not a
     combat action), Eldritch Strike (automatic Disadvantage-on-save rider on a weapon hit, no decision). -->

---

### Subclass: Psi Warrior

## Psionic Power (Psi Warrior)
action_type: special   # genuine edge case — pool definition only, no single trigger action; spent via the features below
resource_key: psionic_energy_dice
subclass: psi_warrior
min_level: 3
max_uses: 4          # increases to 6 at lvl 5, 8 at lvl 9, 10 at lvl 13, 12 at lvl 17
die_size: d6         # becomes d8 at lvl 5, d10 at lvl 11, d12 at lvl 17
rest_type: short regain 1, long regain all
description: Psionic Energy Dice fuel Protective Field, Psionic Strike, Telekinetic Movement, and the other Psi Warrior features below.

## Protective Field
action_type: reaction
consumes_resource: psionic_energy_dice
subclass: psi_warrior
min_level: 3
description: Reduce damage to yourself or a creature within 30 ft. by the die roll plus your Intelligence modifier (minimum 1).

## Psionic Strike
action_type: free_action   # once per turn, free, triggered immediately after a weapon hit
consumes_resource: psionic_energy_dice
subclass: psi_warrior
min_level: 3
description: Once per turn, immediately after hitting with a weapon attack, deal extra Force damage equal to the die roll plus your Intelligence modifier.

## Telekinetic Movement
action_type: action   # uses the Magic action specifically
resource_key: telekinetic_movement
subclass: psi_warrior
min_level: 3
max_uses: 1
rest_type: short regain all, long regain all
bonus_recharge: expend 1 psionic_energy_dice (no action) to restore early
description: Move a loose object or one creature (Large or smaller, willing if a creature other than you) up to 30 ft.

## Psi-Powered Leap
action_type: bonus_action
resource_key: psi_powered_leap
subclass: psi_warrior
min_level: 7
max_uses: 1
rest_type: short regain all, long regain all
bonus_recharge: expend 1 psionic_energy_dice (no action) to restore early
description: Gain a Fly Speed equal to twice your Speed until the end of the current turn.

## Telekinetic Thrust
action_type: free_action   # free rider on Psionic Strike, no separate resource
subclass: psi_warrior
min_level: 7
description: When Psionic Strike damages a target, it makes a Strength save or is knocked Prone or moved up to 10 ft.

## Guarded Mind
action_type: free_action   # free, no action required, triggered at the start of your turn
consumes_resource: psionic_energy_dice
subclass: psi_warrior
min_level: 10
description: If you start your turn Charmed or Frightened, expend a die to end every effect on yourself causing those conditions. (Also grants passive Resistance to Psychic damage — not tracked as a resource.)

## Bulwark of Force
action_type: bonus_action
resource_key: bulwark_of_force
subclass: psi_warrior
min_level: 15
max_uses: 1
rest_type: long regain all
bonus_recharge: expend 1 psionic_energy_dice (no action) to restore early
description: Grant Half Cover for 1 minute to creatures within 30 ft. (including yourself), up to a number equal to your Intelligence modifier (minimum 1).

## Telekinetic Master
action_type: action   # uses the Magic action specifically
resource_key: telekinesis_free_cast
subclass: psi_warrior
min_level: 18
max_uses: 1
rest_type: long regain all
bonus_recharge: expend 1 psionic_energy_dice (no action) to restore early
description: Cast Telekinesis without a spell slot or components (Intelligence-based). While concentrating on it, make one weapon attack as a Bonus Action each turn (unlimited while concentrating — not tracked separately).
