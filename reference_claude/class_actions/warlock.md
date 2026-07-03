# Warlock

<!-- Verified against PHB raw text (chapter 3, Warlock), not the Classes.md project reference.
     Pact Magic (cantrips, prepared spells, spell slots per the Warlock Features table — note these
     recharge on a Short OR Long Rest, unlike other casters) belongs to your existing spell-slot system,
     not this combat-resource seeder — same treatment as the other casters.
     Eldritch Invocations (lvl 1, with more gained at higher levels) are excluded as a whole from this
     catalog: it's an open-ended, 30+ option customization list functioning like Feats or Fighting Style
     (both already excluded elsewhere) rather than a fixed, universal resource every Warlock shares. A few
     individual invocations do grant their own discrete combat resource (e.g. Eldritch Smite consumes a
     Pact Magic slot, Gaze of Two Minds is a Bonus Action with a maintain mechanic), but since invocations
     are optional per-character picks rather than guaranteed class features, they aren't enumerated here —
     flag to Zach if specific chosen invocations need their own resource rows. Pact Boons (Pact of the
     Blade/Chain/Tome/Talisman) are themselves Invocations under the 2024 rules and fall under this same
     exclusion. -->

## Magical Cunning
action_type: special   # doesn't fit the 5 buckets — a 1-minute esoteric rite, not an in-combat action
resource_key: magical_cunning
min_level: 2
max_uses: 1
rest_type: long
description: Perform a 1-minute rite; at the end of it, regain expended Pact Magic spell slots, up to half your maximum (round up). From lvl 20 (Eldritch Master), regain ALL expended Pact Magic spell slots instead when you use this feature.

## Contact Patron
action_type: special   # doesn't fit the 5 buckets — Contact Other Plane's casting time is "1 minute or Ritual," not a combat action; included per the "all resources must be noted" mandate even though it's not combat-relevant
resource_key: contact_patron_free_cast
min_level: 9
max_uses: 1
rest_type: long
description: Cast Contact Other Plane (always prepared) without expending a spell slot, and automatically succeed on the spell's saving throw.

## Mystic Arcanum
action_type: special   # the action type depends entirely on which level 6–9 Warlock spell you choose as each arcanum, decided per character — not fixed by the class
resource_key: mystic_arcanum
min_level: 11
max_uses: 1   # increases to 2 at lvl 13, 3 at lvl 15, 4 at lvl 17 — each tier is a separate chosen spell (level 6 at lvl 11, then 7/8/9), each independently castable once per Long Rest
rest_type: long regain all
description: Choose one level 6 Warlock spell (level 7 at lvl 13, level 8 at lvl 15, level 9 at lvl 17) as an arcanum; cast it once without expending a spell slot. Track which arcanum spell corresponds to which use in your spell-slot system — only the once-per-Long-Rest cast count is tracked here.

<!-- Excluded base-class features (no decision point / no action / no resource, or out of scope):
     Spellcasting/Pact Magic (out of scope), Eldritch Invocations (see intro comment — build customization),
     Warlock Subclass, Ability Score Improvement, Epic Boon. -->

---

### Subclass: Archfey Patron

## Steps of the Fey
action_type: bonus_action
resource_key: steps_of_the_fey
subclass: archfey
min_level: 3
max_uses: Charisma modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: Cast Misty Step without expending a spell slot. Whenever you cast it this way, also choose one: Refreshing Step (you or a creature within 10 ft. of yourself gains 1d10 Temporary HP) or Taunting Step (creatures within 5 ft. of the space you left make a Wisdom save against your spell save DC or have Disadvantage on attack rolls against creatures other than you until the start of your next turn). From lvl 6 (Misty Escape), two more options are added to this choice — see below.

## Misty Escape
action_type: reaction   # alternate trigger for the same Steps of the Fey pool
consumes_resource: steps_of_the_fey
subclass: archfey
min_level: 6
description: Cast Misty Step (via Steps of the Fey) as a Reaction in response to taking damage, instead of spending a Bonus Action. From this level, two more options are added to the Steps of the Fey choice: Disappearing Step (gain the Invisible condition until the start of your next turn or until you make an attack roll, deal damage, or cast a spell) and Dreadful Step (creatures within 5 ft. of the space you left or the space you arrive in make a Wisdom save against your spell save DC or take 2d10 Psychic damage).

## Beguiling Defenses
action_type: reaction
resource_key: beguiling_defenses
subclass: archfey
min_level: 10
max_uses: 1
rest_type: long
bonus_recharge: expend 1 Pact Magic spell slot (no action) to restore early
description: Immediately after a creature you can see hits you with an attack roll, halve the damage you take (round down) and force the attacker to make a Wisdom save against your spell save DC; on a failure, it takes Psychic damage equal to the damage you took. (Also grants passive immunity to the Charmed condition — not tracked as a resource.)

## Bewitching Magic
action_type: free_action   # rider immediately after casting — piggybacks on the action already spent on the triggering spell, no separate resource
subclass: archfey
min_level: 14
description: Immediately after you cast an Enchantment or Illusion spell using an action and a spell slot, cast Misty Step as part of the same action without expending a spell slot (independent of the Steps of the Fey pool).

---

### Subclass: Celestial Patron

## Healing Light
action_type: bonus_action
resource_key: healing_light_dice
subclass: celestial
min_level: 3
max_uses: 1 + Warlock level   # stat/level-based, not a flat table value
die_size: d6
rest_type: long regain all
description: Heal yourself or a creature within 60 ft., expending and rolling dice from the pool (up to your Charisma modifier worth of dice per use, minimum 1 die) and restoring HP equal to the total rolled.

## Celestial Resilience
action_type: free_action   # rider on using Magical Cunning or finishing a Short/Long Rest — no separate resource, but a genuine decision point (who receives the shared share)
subclass: celestial
min_level: 10
description: Whenever you use Magical Cunning or finish a Short or Long Rest, gain Temporary HP equal to your Warlock level plus your Charisma modifier. Choose up to five creatures you can see at that time; each of them gains Temporary HP equal to half that amount.

## Searing Vengeance
action_type: free_action   # no stated action cost — a reactive trigger
resource_key: searing_vengeance
subclass: celestial
min_level: 14
max_uses: 1
rest_type: long
description: When you or an ally within 60 ft. is about to make a Death Saving Throw, unleash radiant energy: the creature regains HP equal to half its HP maximum and can end the Prone condition on itself. Each creature of your choice within 30 ft. of it takes 2d8 plus your Charisma modifier Radiant damage and has the Blinded condition until the end of the current turn.

<!-- Excluded: Celestial Spells (always-prepared spell list — out of scope), Radiant Soul (automatic flat
     Charisma-modifier damage add once per turn, no decision point — same treatment as Sorcerer's Draconic
     Elemental Affinity). -->

---

### Subclass: Fiend Patron

## Dark One's Own Luck
action_type: free_action   # used after seeing a roll but before its effects resolve
resource_key: dark_ones_own_luck
subclass: fiend
min_level: 6
max_uses: Charisma modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: After making an ability check or saving throw and seeing the roll (but before its effects occur), add 1d10 to it. Usable no more than once per roll.

## Hurl Through Hell
action_type: free_action   # once per turn, rider on a hit with an attack roll — no separate action stated
resource_key: hurl_through_hell
subclass: fiend
min_level: 14
max_uses: 1
rest_type: long
bonus_recharge: expend 1 Pact Magic spell slot (no action) to restore early
description: When you hit a creature with an attack roll, force a Charisma save against your spell save DC or transport it through the Lower Planes: it takes 8d10 Psychic damage (unless it's a Fiend) and has the Incapacitated condition until the end of your next turn, when it returns to its space (or the nearest unoccupied space).

<!-- Excluded: Dark One's Blessing (automatic Temporary HP on a kill, no decision point), Fiend Spells
     (always-prepared spell list — out of scope), Fiendish Resilience (damage-type choice made only when
     finishing a rest — downtime loadout choice, not a combat trigger). -->

---

### Subclass: Great Old One Patron

## Awakened Mind
action_type: bonus_action   # no resource — unlimited
subclass: great_old_one
min_level: 3
description: Form a telepathic connection with one creature you can see within 30 ft.; you can communicate telepathically while within a number of miles of each other equal to your Charisma modifier (minimum 1 mile), for a number of minutes equal to your Warlock level. Ends early if you use this to connect with a different creature.

## Psychic Spells
action_type: free_action   # rider on casting a Warlock spell — no separate action of its own (the cast itself is tracked by your spell-slot system); no resource — unlimited
subclass: great_old_one
min_level: 3
description: When you cast a Warlock spell that deals damage, you may change its damage type to Psychic. When you cast a Warlock spell that is an Enchantment or Illusion, you may cast it without Verbal or Somatic components.

## Clairvoyant Combatant
action_type: reaction
resource_key: clairvoyant_combatant
subclass: great_old_one
min_level: 6
max_uses: 1
rest_type: short regain all, long regain all
bonus_recharge: expend 1 Pact Magic spell slot (no action) to restore early
description: When you form a telepathic bond with a creature using Awakened Mind, force it to make a Wisdom save against your spell save DC; on a failure, it has Disadvantage on attack rolls against you, and you have Advantage on attack rolls against it for the bond's duration.

<!-- Excluded: Great Old One Spells (always-prepared spell list — out of scope), Eldritch Hex (always-prepared
     Hex + automatic rider with no separate decision beyond Hex's own out-of-scope cast), Thought Shield
     (passive Resistance + automatic damage reflection, no decision). -->

## Create Thrall
action_type: free_action   # rider on casting Summon Aberration — no separate action of its own
subclass: great_old_one
min_level: 14
description: When you cast Summon Aberration, you may forgo its Concentration requirement (duration becomes 1 minute for that casting); the summoned Aberration gains Temporary HP equal to your Warlock level plus your Charisma modifier. The first time each turn the Aberration hits a creature affected by your Hex, it deals extra Psychic damage equal to that spell's bonus damage.
