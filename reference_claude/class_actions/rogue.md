# Rogue

<!-- Verified against PHB raw text (chapter 3, Rogue), not the Classes.md project reference.
     Arcane Trickster's spellcasting (cantrips, prepared spells, spell slots) belongs to your existing
     spell-slot system, not this combat-resource seeder — same treatment as the other casters. -->

## Sneak Attack
action_type: free_action   # once per turn, automatic when conditions are met (Advantage, or an ally within 5 ft. of the target) — no resource, but its damage dice can be partially forgone via Cunning Strike below
min_level: 1
description: Once per turn, deal extra damage (1d6, scaling to 2d6 at lvl 3, 3d6 at lvl 5, 4d6 at lvl 7, 5d6 at lvl 9, 6d6 at lvl 11, 7d6 at lvl 13, 8d6 at lvl 15, 9d6 at lvl 17, 10d6 at lvl 19) to one creature you hit with an attack roll, if you have Advantage on the roll and the attack uses a Finesse or Ranged weapon. You don't need Advantage if an ally (not Incapacitated) is within 5 ft. of the target and you don't have Disadvantage.

## Cunning Strike
action_type: free_action   # rider on a Sneak Attack hit — no separate resource; the "cost" is forgoing some of that hit's own Sneak Attack dice before rolling
min_level: 5
description: When you deal Sneak Attack damage, forgo some of its damage dice (removed before rolling) to add one of these effects, occurring immediately after damage is dealt — Poison (cost 1d6, requires a Poisoner's Kit on you: Constitution save or Poisoned 1 minute, save repeats each turn); Trip (cost 1d6: Large-or-smaller target makes a Dexterity save or is knocked Prone); Withdraw (cost 1d6: move up to half your Speed with no Opportunity Attacks); Knock Out (cost 6d6: Constitution save or Unconscious 1 minute, save repeats each turn, ends on damage); Obscure (cost 3d6: Dexterity save or Blinded until end of its next turn). From lvl 14 (Devious Strikes), also: Daze (cost 2d6: Constitution save or, on its next turn, only move OR take an action OR a Bonus Action, not more than one). From lvl 11 (Improved Cunning Strike), you can apply up to two of these effects to the same Sneak Attack, paying each die cost. (Save DC for any of these options equals 8 + Dexterity modifier + Proficiency Bonus. Thief subclass lvl 9, Supreme Sneak, adds a Stealth Attack option, cost 1d6: doesn't end your Hide-granted Invisible condition if you end the turn behind Three-Quarters/Total Cover. Assassin subclass lvl 13, Envenom Weapons: the Poison option's failed save also deals 2d6 Poison damage that ignores Poison Resistance.)

## Cunning Action
action_type: bonus_action   # no resource — unlimited
min_level: 2
description: Take the Dash, Disengage, or Hide action.

## Steady Aim
action_type: bonus_action   # no resource — unlimited, but requires not having moved this turn and zeroes your Speed for the rest of the turn
min_level: 3
description: Give yourself Advantage on your next attack roll this turn. Usable only if you haven't moved this turn; your Speed becomes 0 until the end of the current turn. (Assassin subclass lvl 9, Infiltration Expertise — Roving Aim: your Speed is no longer reduced to 0 by this feature.)

## Uncanny Dodge
action_type: reaction   # no resource — unlimited
min_level: 5
description: When an attacker you can see hits you with an attack roll, halve that attack's damage against you (round down).

## Stroke of Luck
action_type: free_action   # triggered on a failed D20 Test
resource_key: stroke_of_luck
min_level: 20
max_uses: 1
rest_type: short regain all, long regain all
description: Turn a failed D20 Test's roll into a 20.

<!-- Excluded base-class features (no decision point / no action / no resource): Expertise (lvl 1 and lvl
     6, passive), Thieves' Cant (passive language), Weapon Mastery (passive proficiency; the Long-Rest swap
     is downtime customization), Rogue Subclass, Ability Score Improvement, Evasion (automatic, no
     decision), Reliable Talent (passive), Slippery Mind (passive proficiency), Elusive (passive — denies
     Advantage against you), Epic Boon. -->

---

### Subclass: Arcane Trickster

## Mage Hand Legerdemain — Control Hand
action_type: bonus_action   # no resource — unlimited
subclass: arcane_trickster
min_level: 3
description: Control your spectral Mage Hand (cast as a Bonus Action and Invisible per this feature) as a Bonus Action, including to make Dexterity (Sleight of Hand) checks through it.

## Versatile Trickster
action_type: free_action   # rider on the Trip option of Cunning Strike — no separate resource
subclass: arcane_trickster
min_level: 13
description: When you use the Trip option of Cunning Strike on a creature, also apply it to another creature within 5 ft. of your Mage Hand.

## Spell Thief
action_type: reaction
resource_key: spell_thief
subclass: arcane_trickster
min_level: 17
max_uses: 1
rest_type: long
description: Immediately after a creature casts a spell targeting you or including you in its area, force an Intelligence save (your spell save DC). On a failure, negate the spell against you and steal the knowledge of it (if level 1+ and a level you can cast); you have it prepared for 8 hours, during which the creature can't cast it.

<!-- Excluded: Spellcasting (out of scope), Magical Ambush (automatic Disadvantage rider on a save against
     a spell you cast while Invisible, no separate decision). -->

---

### Subclass: Assassin

## Surprising Strikes
action_type: free_action   # automatic during the first round of combat only — no resource
subclass: assassin
min_level: 3
description: During the first round of combat, you have Advantage on attack rolls against any creature that hasn't taken a turn yet. If your Sneak Attack hits a target during that round, it takes extra damage (of the weapon's type) equal to your Rogue level.

## Death Strike
action_type: free_action   # rider on a Sneak Attack hit during the first round of combat — no resource
subclass: assassin
min_level: 17
description: When you hit with Sneak Attack on the first round of combat, the target makes a Constitution save (DC 8 + Dexterity modifier + Proficiency Bonus) or the attack's damage is doubled against it.

<!-- Excluded: Initiative advantage (passive, folded out of Surprising Strikes above), Assassin's Tools
     (passive kit proficiencies), Infiltration Expertise's Masterful Mimicry (passive; its Roving Aim half
     is folded into Steady Aim's description above). -->

---

### Subclass: Soulknife

## Psionic Power (pool)
action_type: special   # genuine edge case — pool definition only, no single trigger action; spent via the powers below
resource_key: psionic_energy_dice
subclass: soulknife
min_level: 3
max_uses: 4          # increases to 6 at lvl 5, 8 at lvl 9, 8 at lvl 11, 10 at lvl 13, 12 at lvl 17
die_size: d6         # becomes d8 at lvl 5, d10 at lvl 11, d12 at lvl 17
rest_type: short regain 1, long regain all
description: Psionic Energy Dice fuel Psi-Bolstered Knack, Psychic Whispers, and the Soulknife powers below.

## Psi-Bolstered Knack
action_type: free_action   # triggered on a failed ability check using a proficient skill or tool
consumes_resource: psionic_energy_dice   # only expended if the reroll then succeeds
subclass: soulknife
min_level: 3
description: Roll a Psionic Energy Die and add it to a failed ability check using a skill or tool you're proficient with, potentially turning the failure into a success. The die is expended only if the check then succeeds.

## Psychic Whispers
action_type: action   # uses the Magic action specifically
consumes_resource: psionic_energy_dice   # the first use after each Long Rest doesn't expend the die
subclass: soulknife
min_level: 3
description: Choose creatures you can see (up to your Proficiency Bonus) and roll a Psionic Energy Die; for that many hours, you and they can speak telepathically within 1 mile of each other (no action required to send/receive). The first use after a Long Rest doesn't expend the die.

## Psychic Blades
action_type: free_action   # rider on the Attack action or an Opportunity Attack — no resource
subclass: soulknife
min_level: 3
description: Manifest a Psychic Blade in your free hand and attack with it (Simple Melee, Finesse, Thrown 60/120 ft., Vex mastery, 1d6 Psychic + ability modifier on a hit) instead of a normal weapon. The blade vanishes after it hits or misses.

## Psychic Blades — Bonus Attack
action_type: bonus_action   # no resource — unlimited, requires a free hand
subclass: soulknife
min_level: 3
description: After attacking with a Psychic Blade on your turn, make a melee or ranged attack with a second blade (1d4 instead of 1d6) if your other hand is free.

## Homing Strikes
action_type: free_action   # triggered on a Psychic Blade miss; only expended if it then hits
consumes_resource: psionic_energy_dice
subclass: soulknife
min_level: 9
description: On a missed Psychic Blade attack roll, roll a Psionic Energy Die and add it, potentially turning the miss into a hit. The die is expended only if it then hits.

## Psychic Teleportation
action_type: bonus_action
consumes_resource: psionic_energy_dice
subclass: soulknife
min_level: 9
description: Manifest a Psychic Blade, expend and roll a Psionic Energy Die, and throw the blade to an unoccupied space you can see up to 10 × the roll in feet away; teleport to that space (the blade vanishes).

## Psychic Veil
action_type: action   # uses the Magic action specifically
resource_key: psychic_veil
subclass: soulknife
min_level: 13
max_uses: 1
rest_type: long
bonus_recharge: expend 1 psionic_energy_dice (no action) to restore early
description: Gain the Invisible condition for 1 hour or until dismissed (no action required); ends early immediately if you deal damage or force a save.

## Rend Mind
action_type: free_action   # rider when Psychic Blades deal Sneak Attack damage
resource_key: rend_mind
subclass: soulknife
min_level: 17
max_uses: 1
rest_type: long
bonus_recharge: expend 3 psionic_energy_dice (no action) to restore early
description: Force a Wisdom save (DC 8 + Dexterity modifier + Proficiency Bonus) or the target has the Stunned condition for 1 minute (save repeats each turn).

---

### Subclass: Thief

## Fast Hands
action_type: bonus_action   # no resource — unlimited
subclass: thief
min_level: 3
description: Make a Dexterity (Sleight of Hand) check to pick a lock, disarm a trap with Thieves' Tools, or pick a pocket, or take the Utilize action, or take the Magic action to use a magic item that requires it.

<!-- Excluded: Second-Story Work (passive Climb Speed + Dex-based jumping), Use Magic Device (passive
     attunement/charges/scroll-use utility, no combat trigger), Thief's Reflexes (lvl 17 — automatic extra
     turn in the first round of combat, no decision point). -->
