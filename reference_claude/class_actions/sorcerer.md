# Sorcerer

<!-- Verified against PHB raw text (chapter 3, Sorcerer), not the Classes.md project reference.
     Spellcasting (cantrips, prepared spells, spell slots per the Sorcerer Features table) belongs to your
     existing spell-slot system, not this combat-resource seeder — same treatment as the other casters.
     Sorcery Points are modeled as a `special` pool (no single trigger action of its own, like Combat
     Superiority/Channel Divinity/Monk's Focus) since they fuel Metamagic, Creating Spell Slots, and several
     subclass features below. Several Metamagic options and subclass features are riders applied to an
     already-cast spell (itself out of scope, tracked by your spell-slot system) but each still represents a
     genuine combat decision (spend Sorcery Points or not) and so gets its own block per the established
     "decision point on a rider" rule. -->

## Innate Sorcery
action_type: bonus_action
resource_key: innate_sorcery
min_level: 1
max_uses: 2
rest_type: long regain all
bonus_recharge: from lvl 7 (Sorcery Incarnate), if you have no uses left, spend 2 sorcery_points instead (no extra action — part of the same Bonus Action) to activate it anyway
description: Unleash your innate magic for 1 minute. While active, the spell save DC of your Sorcerer spells increases by 1, and you have Advantage on the attack rolls of Sorcerer spells you cast. From lvl 7 (Sorcery Incarnate), while active you can also use up to two Metamagic options on each spell you cast (instead of the usual one). From lvl 20 (Arcane Apotheosis), while active you can use one Metamagic option on each of your turns without spending Sorcery Points on it.

## Sorcery Points (pool)
action_type: special   # genuine edge case — pool definition only, no single trigger action; spent via Metamagic, Creating Spell Slots, Sorcery Incarnate's alternate activation, and the subclass options below
resource_key: sorcery_points
min_level: 2
max_uses: Sorcerer level   # equals your Sorcerer level starting at lvl 2 (2 points), up to 20 at lvl 20 — see Sorcerer Features table
rest_type: long regain all
description: Fuels Metamagic, Creating Spell Slots, Sorcery Incarnate's alternate activation of Innate Sorcery, and each subclass's own Sorcery Point options below.

## Sorcery Points — Convert from Spell Slot
action_type: free_action   # no action required
min_level: 2   # no Sorcerer-specific resource consumed — spends a spell slot (out of scope) to gain Sorcery Points
description: Expend a spell slot to gain a number of Sorcery Points equal to the slot's level (no action required).

## Creating Spell Slots
action_type: bonus_action
consumes_resource: sorcery_points   # variable cost: 2 (level 1 slot, min Sorcerer lvl 2), 3 (level 2, min lvl 3), 5 (level 3, min lvl 5), 6 (level 4, min lvl 7), 7 (level 5, min lvl 9)
min_level: 2
description: Transform unexpended Sorcery Points into one spell slot of level 1–5 (per the Creating Spell Slots cost table; you must be the listed minimum Sorcerer level to create a slot of a given level). Any spell slot created this way vanishes when you finish a Long Rest.

## Sorcerous Restoration
action_type: free_action   # no action required, triggered specifically when you finish a Short Rest
resource_key: sorcerous_restoration
min_level: 5
max_uses: 1
rest_type: long
description: When you finish a Short Rest, regain Sorcery Points up to half your Sorcerer level (round down). Usable once per Long Rest.

## Metamagic — Careful Spell
action_type: free_action   # rider on casting a spell that forces a saving throw — no separate action of its own (the cast itself is tracked by your spell-slot system)
consumes_resource: sorcery_points   # costs 1
min_level: 2
description: When you cast a spell that forces other creatures to make a saving throw, spend 1 Sorcery Point to choose a number of those creatures up to your Charisma modifier (minimum 1); each automatically succeeds on its save and takes no damage if it would normally take half on a success.

## Metamagic — Distant Spell
action_type: free_action   # rider on casting a spell with a range — no separate action
consumes_resource: sorcery_points   # costs 1
min_level: 2
description: When you cast a spell with a range of at least 5 ft., spend 1 Sorcery Point to double its range. Or when you cast a spell with a range of Touch, spend 1 Sorcery Point to make its range 30 ft.

## Metamagic — Empowered Spell
action_type: free_action   # rider on rolling damage for a spell — no separate action; usable even with another Metamagic option
consumes_resource: sorcery_points   # costs 1
min_level: 2
description: When you roll damage for a spell, spend 1 Sorcery Point to reroll a number of the damage dice up to your Charisma modifier (minimum 1); you must use the new rolls.

## Metamagic — Extended Spell
action_type: free_action   # rider on casting a spell with a duration of 1 minute+ — no separate action
consumes_resource: sorcery_points   # costs 1
min_level: 2
description: When you cast a spell with a duration of 1 minute or longer, spend 1 Sorcery Point to double its duration, to a maximum of 24 hours. If the spell requires Concentration, you have Advantage on saves to maintain it.

## Metamagic — Heightened Spell
action_type: free_action   # rider on casting a spell that forces a saving throw — no separate action
consumes_resource: sorcery_points   # costs 2
min_level: 2
description: When you cast a spell that forces a saving throw, spend 2 Sorcery Points to give one target Disadvantage on its save against the spell.

## Metamagic — Quickened Spell
action_type: bonus_action   # changes the spell's own casting time to a Bonus Action for this casting
consumes_resource: sorcery_points   # costs 2
min_level: 2
description: When you cast a spell with a casting time of an action, spend 2 Sorcery Points to change its casting time to a Bonus Action for this casting. You can't do this if you've already cast a level 1+ spell this turn, nor cast a level 1+ spell later this turn after doing so.

## Metamagic — Seeking Spell
action_type: free_action   # rider on a missed spell attack roll — no separate action; usable even with another Metamagic option
consumes_resource: sorcery_points   # costs 1
min_level: 2
description: If you miss with a spell attack roll, spend 1 Sorcery Point to reroll the d20; you must use the new roll.

## Metamagic — Subtle Spell
action_type: free_action   # rider on casting a spell — no separate action
consumes_resource: sorcery_points   # costs 1
min_level: 2
description: When you cast a spell, spend 1 Sorcery Point to cast it without any Verbal, Somatic, or Material components, except Material components consumed by the spell or with a cost specified in it.

## Metamagic — Transmuted Spell
action_type: free_action   # rider on casting a damage spell — no separate action
consumes_resource: sorcery_points   # costs 1
min_level: 2
description: When you cast a spell that deals Acid, Cold, Fire, Lightning, Poison, or Thunder damage, spend 1 Sorcery Point to change that damage to one of the other listed types.

## Metamagic — Twinned Spell
action_type: free_action   # rider on casting a spell that can target an additional creature via a higher-level slot — no separate action
consumes_resource: sorcery_points   # costs 1
min_level: 2
description: When you cast a spell that could target an additional creature using a higher-level slot, spend 1 Sorcery Point to increase the spell's effective level by 1 instead.

<!-- Excluded base-class features (no decision point / no action / no resource, or out of scope): Spellcasting
     (out of scope), Font of Magic's narrative framing (folded above into Sorcery Points), Ability Score
     Improvement, Sorcerer Subclass, Epic Boon. You gain 2 Metamagic options at lvl 2, 2 more at lvl 10, 2
     more at lvl 17, and can swap one per level gained — a character-build choice, not a combat trigger;
     only the 10 named options above are tracked as resource-consuming blocks. -->

---

### Subclass: Aberrant Sorcery

## Telepathic Speech
action_type: bonus_action   # no resource — unlimited
subclass: aberrant
min_level: 3
description: Form a telepathic connection with one creature you can see within 30 ft.; you can communicate telepathically while within a number of miles of each other equal to your Charisma modifier (minimum 1 mile), for a number of minutes equal to your Sorcerer level. Ends early if you use this to connect with a different creature.

## Psionic Sorcery
action_type: free_action   # rider on casting a Psionic Spells spell — no separate action of its own (the cast itself is tracked by your spell-slot system)
consumes_resource: sorcery_points   # variable cost equal to the spell's level
subclass: aberrant
min_level: 6
description: When you cast a level 1+ spell from your Psionic Spells feature, you can spend Sorcery Points equal to the spell's level instead of expending a spell slot. If cast this way, it requires no Verbal or Somatic components, and no Material components unless they're consumed by the spell or have a cost specified in it.

## Revelation in Flesh
action_type: bonus_action
consumes_resource: sorcery_points   # variable: 1+ points, one benefit per point spent
subclass: aberrant
min_level: 14
description: Spend 1 or more Sorcery Points to magically alter your body for 10 minutes; for each point spent, gain one benefit of your choice (lasting until the alteration ends): Aquatic Adaptation (Swim Speed = 2× Speed, breathe underwater), Glistening Flight (Fly Speed = Speed, hover), See the Invisible (see Invisible creatures within 60 ft. not behind Total Cover), or Wormlike Movement (move through spaces as narrow as 1 inch; spend 5 ft. of movement to escape nonmagical restraints or the Grappled condition).

## Warping Implosion
action_type: action   # uses the Magic action specifically
resource_key: warping_implosion
subclass: aberrant
min_level: 18
max_uses: 1
rest_type: long
bonus_recharge: expend 5 sorcery_points (no action) to restore early
description: Teleport to an unoccupied space you can see within 120 ft. Immediately after, each creature within 30 ft. of the space you left makes a Strength save against your spell save DC, taking 3d10 Force damage and being pulled toward that space on a failure (half damage only on a success).

<!-- Excluded: Psionic Spells (always-prepared spell list — out of scope), Psychic Defenses (passive
     Resistance + save Advantage). -->

---

### Subclass: Clockwork Sorcery

## Restore Balance
action_type: reaction
resource_key: restore_balance
subclass: clockwork
min_level: 3
max_uses: Charisma modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: When a creature you can see within 60 ft. is about to roll a d20 with Advantage or Disadvantage, take a Reaction to prevent that roll from being affected by either.

## Bastion of Law
action_type: action   # uses the Magic action specifically
consumes_resource: sorcery_points   # variable: 1–5 points, one d8 of ward per point
subclass: clockwork
min_level: 6
description: Expend 1 to 5 Sorcery Points to create a magical ward around yourself or another creature you can see within 30 ft., represented by a number of d8s equal to the points spent. When the warded creature takes damage, it can expend dice from the ward, roll them, and reduce the damage taken by the total. The ward lasts until you finish a Long Rest or use this feature again.

## Trance of Order
action_type: bonus_action
resource_key: trance_of_order
subclass: clockwork
min_level: 14
max_uses: 1
rest_type: long
bonus_recharge: expend 5 sorcery_points (no action) to restore early
description: Enter a trance for 1 minute. While active, attack rolls against you can't benefit from Advantage, and whenever you make a D20 Test, you can treat a roll of 9 or lower as a 10.

## Clockwork Cavalcade
action_type: action   # uses the Magic action specifically
resource_key: clockwork_cavalcade
subclass: clockwork
min_level: 18
max_uses: 1
rest_type: long
bonus_recharge: expend 7 sorcery_points (no action) to restore early
description: Summon spirits of order in a 30-ft. Cube originating from you; they create these effects before vanishing — Heal (restore up to 100 HP, divided as you choose among creatures in the Cube), Repair (instantly repair damaged objects in the Cube), and Dispel (end every spell of level 6 or lower on creatures and objects of your choice in the Cube).

<!-- Excluded: Clockwork Spells (always-prepared spell list — out of scope), Manifestations of Order (cosmetic
     flavor table, no mechanical effect). -->

---

### Subclass: Draconic Sorcery

## Dragon Wings
action_type: bonus_action
resource_key: dragon_wings
subclass: draconic
min_level: 14
max_uses: 1
rest_type: long
bonus_recharge: expend 3 sorcery_points (no action) to restore early
description: Cause draconic wings to appear on your back, granting a Fly Speed of 60 ft. for 1 hour or until you dismiss them (no action required).

## Draconic Companion
action_type: action   # matches Summon Dragon's own casting time (an Action)
resource_key: draconic_companion_free_cast
subclass: draconic
min_level: 18
max_uses: 1
rest_type: long
description: Cast Summon Dragon without a Material component and without expending a spell slot. You may forgo the spell's Concentration requirement, in which case its duration becomes 1 minute for that casting.

<!-- Excluded base-class-pattern features (passive / out of scope): Draconic Resilience (passive HP/AC
     formula), Draconic Spells (always-prepared spell list — out of scope), Elemental Affinity (passive
     Resistance + automatic flat Charisma-modifier damage add, no decision point each cast). -->

---

### Subclass: Wild Magic Sorcery

## Wild Magic Surge
action_type: free_action   # automatic on a natural 20, immediately after casting a Sorcerer spell with a spell slot — no resource, no decision, but a mechanically significant trigger (matches the Sneak Attack precedent for automatic-but-significant features)
subclass: wild_magic
min_level: 3
description: Once per turn, immediately after you cast a Sorcerer spell with a spell slot, roll 1d20; on a 20, roll on the Wild Magic Surge table to create a random magical effect (too wild to be affected by your Metamagic). From lvl 14 (Controlled Chaos), whenever you roll on the Wild Magic Surge table (from this feature or Tides of Chaos below), roll twice and use either number.

## Tides of Chaos
action_type: free_action   # declared before rolling a d20 for a D20 Test — no action required
resource_key: tides_of_chaos
subclass: wild_magic
min_level: 3
max_uses: 1
rest_type: regain on casting a Sorcerer spell with a spell slot, or on finishing a Long Rest   # non-standard recharge — not a flat short/long rest cadence
description: Give yourself Advantage on one D20 Test before you roll. If you then cast a Sorcerer spell with a spell slot before finishing a Long Rest (which restores the use), you automatically roll on the Wild Magic Surge table.

## Bend Luck
action_type: reaction
consumes_resource: sorcery_points   # costs 1
subclass: wild_magic
min_level: 6
description: Immediately after another creature you can see rolls a d20 for a D20 Test, spend 1 Sorcery Point and roll 1d4, applying the number as a bonus or penalty (your choice) to that roll.

## Tamed Surge
action_type: free_action   # rider immediately after casting a Sorcerer spell with a spell slot — no separate action
resource_key: tamed_surge
subclass: wild_magic
min_level: 18
max_uses: 1
rest_type: long
description: Immediately after casting a Sorcerer spell with a spell slot, create an effect of your choice from the Wild Magic Surge table (any row except the final one) instead of rolling for it; if the chosen effect involves a roll, you must make it.

<!-- Excluded: the Wild Magic Surge table's individual random effects (mechanical detail of an already-tracked
     trigger above, not separate abilities). -->
