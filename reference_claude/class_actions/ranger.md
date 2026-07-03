# Ranger

<!-- Verified against PHB raw text (chapter 3, Ranger), not the Classes.md project reference.
     Spellcasting (cantrips, prepared spells, spell slots per the Ranger Features table) belongs to your
     existing spell-slot system, not this combat-resource seeder — same treatment as the other casters.
     Several Ranger features grant a FREE cast of a specific spell (Hunter's Mark via Favored Enemy, Summon
     Fey via Fey Reinforcements, Misty Step via Misty Wanderer) with their own once-per-rest cap; those
     free-cast charges are tracked here since they're discrete combat resources, even though the underlying
     spells themselves are not. -->

## Favored Enemy
action_type: bonus_action   # matches Hunter's Mark's own casting time
resource_key: favored_enemy_free_cast
min_level: 1
max_uses: 2          # increases to 3 at lvl 5, 4 at lvl 9, 5 at lvl 13, 6 at lvl 17 (Favored Enemy column)
rest_type: long regain all
description: You always have Hunter's Mark prepared and can cast it without expending a spell slot using one of these uses (further casts require a spell slot, out of scope). From lvl 20 (Foe Slayer), Hunter's Mark's damage die becomes 1d10 instead of 1d6.

## Tireless — Temporary HP
action_type: action   # uses the Magic action specifically
resource_key: tireless_temp_hp
min_level: 10
max_uses: Wisdom modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: Grant yourself Temporary HP equal to 1d8 + Wisdom modifier (minimum 1). (Tireless also reduces your Exhaustion level by 1, if any, whenever you finish a Short Rest — automatic, not tracked as a resource.)

## Nature's Veil
action_type: bonus_action
resource_key: natures_veil
min_level: 14
max_uses: Wisdom modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: Give yourself the Invisible condition until the end of your next turn.

<!-- Excluded base-class features (no decision point / no action / no resource, or out of scope): Weapon
     Mastery (passive proficiency; the Long-Rest swap is downtime customization), Deft Explorer (passive
     Expertise + languages), Fighting Style, Ranger Subclass, Ability Score Improvement, Extra Attack,
     Roving (passive Speed/Climb/Swim), Expertise (lvl 9, passive), Relentless Hunter (passive — Hunter's
     Mark Concentration can't be broken by damage), Precise Hunter (passive Advantage vs. marked target),
     Feral Senses (passive Blindsight), Epic Boon. -->

---

### Subclass: Beast Master

## Primal Companion — Command
action_type: bonus_action   # no resource — unlimited
subclass: beast_master
min_level: 3
description: Command your Primal Companion beast to take an action from its stat block or another action (its default without a command is the Dodge action; it moves and uses its Reaction on its own). From lvl 7 (Exceptional Training), you may instead command it to take the Dash, Disengage, Dodge, or Help action as its Bonus Action, and on a hit it can deal Force damage or its normal type (your choice). From lvl 11 (Bestial Fury), when commanded this way to use the Beast's Strike action, it can use it twice; the first time each turn it hits a creature affected by your Hunter's Mark, it also deals that spell's extra damage.

## Primal Companion — Command via Attack
action_type: free_action   # rider on the Attack action — forgo one of your own attacks instead of spending the Bonus Action
subclass: beast_master
min_level: 3
description: When you take the Attack action, forgo one of your attacks to command your Primal Companion beast to take the Beast's Strike action (in place of using your Bonus Action to do so).

## Primal Companion — Revive
action_type: action   # uses the Magic action specifically
subclass: beast_master   # no Ranger-specific resource — costs a spell slot (out of scope)
min_level: 3
description: If your Primal Companion beast died within the last hour, touch it and expend a spell slot; it returns to life after 1 minute with all HP restored.

<!-- Excluded: initial summoning of the beast and the Long-Rest beast-replacement option (downtime
     customization, not a combat action), Share Spells (lvl 15 — automatic rider extending a self-targeted
     spell to the beast, no separate decision). Stat blocks (Beast of the Land/Sea/Sky) aren't abilities. -->

---

### Subclass: Fey Wanderer

## Dreadful Strikes
action_type: free_action   # once per turn, no resource — unlimited
subclass: fey_wanderer
min_level: 3
description: When you hit a creature with a weapon, deal an extra 1d4 Psychic damage (once per turn). The extra damage increases to 1d6 at lvl 11.

## Beguiling Twist
action_type: reaction   # no resource — unlimited
subclass: fey_wanderer
min_level: 7
description: Whenever you or a creature within 120 ft. of you succeeds on a save to avoid or end the Charmed or Frightened condition, force a different creature within 120 ft. to make a Wisdom save against your spell save DC or gain the Charmed or Frightened condition (your choice) for 1 minute (repeats the save at the end of each of its turns). (Also grants passive Advantage on saves to avoid/end Charmed or Frightened — not tracked as a resource.)

## Fey Reinforcements
action_type: action   # uses the Magic action specifically (Summon Fey's own casting time)
resource_key: fey_reinforcements_free_cast
subclass: fey_wanderer
min_level: 11
max_uses: 1
rest_type: long
description: Cast Summon Fey without a Material component and without expending a spell slot. You may forgo the spell's Concentration requirement, in which case its duration becomes 1 minute for that casting.

## Misty Wanderer
action_type: bonus_action   # matches Misty Step's own casting time
resource_key: misty_wanderer_free_cast
subclass: fey_wanderer
min_level: 15
max_uses: Wisdom modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: Cast Misty Step without expending a spell slot. You may bring one willing creature within 5 ft. of yourself along, teleporting it to an unoccupied space within 5 ft. of your destination.

<!-- Excluded: Otherworldly Clamour (passive Charisma-check bonus + skill proficiency), Fey Wanderer Spells
     (always-prepared spell list — out of scope), the Feywild Gift (flavor). -->

---

### Subclass: Gloom Stalker

## Dreadful Strike (Dread Ambusher)
action_type: free_action   # once per turn, on a weapon hit
resource_key: dreadful_strike
subclass: gloom_stalker
min_level: 3
max_uses: Wisdom modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: Deal an extra 2d6 Psychic damage to a creature you hit with a weapon (once per turn). The extra damage increases to 2d8 at lvl 11 (Stalker's Flurry), at which point you may also choose one additional effect each time you use it: Sudden Strike (make another attack with the same weapon against a different creature within 5 ft. of the original target and within range) or Mass Fear (the target and each creature within 10 ft. of it make a Wisdom save against your spell save DC or are Frightened until the start of your next turn).

## Shadowy Dodge
action_type: reaction   # no resource — unlimited
subclass: gloom_stalker
min_level: 15
description: When a creature makes an attack roll against you, impose Disadvantage on that roll. Whether it hits or misses, you can then teleport up to 30 ft. to an unoccupied space you can see.

<!-- Excluded: Ambusher's Leap (automatic Speed increase at the start of your first turn of combat, no
     decision), Initiative Bonus (passive Wisdom-mod-to-Initiative), Gloom Stalker Spells (always-prepared
     spell list — out of scope), Umbral Sight (passive Darkvision/Invisible-in-Darkness), Iron Mind (passive
     saving throw proficiency). -->

---

### Subclass: Hunter

## Hunter's Prey — Colossus Slayer
action_type: free_action   # once per turn, on a weapon hit — one of two mutually exclusive options, swappable on a Short or Long Rest
subclass: hunter
min_level: 3
description: Deal an extra 1d8 damage (once per turn) to a creature you hit with a weapon if it's missing any HP. Alternative to Horde Breaker below; you can swap which one you have whenever you finish a Short or Long Rest.

## Hunter's Prey — Horde Breaker
action_type: free_action   # once per turn, rider on the Attack action — the other of the two mutually exclusive options
subclass: hunter
min_level: 3
description: Once on each of your turns when you attack with a weapon, make another attack with the same weapon against a different creature within 5 ft. of the original target, within range, and not yet attacked this turn. Alternative to Colossus Slayer above; swappable on a Short or Long Rest.

## Superior Hunter's Prey
action_type: free_action   # once per turn, rider on damaging a Hunter's Mark target
subclass: hunter
min_level: 11
description: Once per turn when you deal damage to a creature marked by your Hunter's Mark, also deal that spell's extra damage to a different creature you can see within 30 ft. of the first.

## Superior Hunter's Defense
action_type: reaction   # no resource — unlimited, triggered when you take damage
subclass: hunter
min_level: 15
description: Gain Resistance to the triggering damage type (and any other damage of that type) until the end of the current turn.

<!-- Excluded: Hunter's Lore (passive — know Immunities/Resistances/Vulnerabilities of your Hunter's Mark
     target), Defensive Tactics (lvl 7 — choice between Escape the Horde and Multiattack Defense, both fully
     passive/automatic with no decision point, swappable on rest like Divine Order). -->
