# Bard

<!-- Verified against PHB raw text (chapter 3, Bard), not the Classes.md project reference.
     Spellcasting (cantrips, prepared spells, spell slots per the Bard Features table) belongs to your
     existing spell-slot system, not this combat-resource seeder — same treatment as Fighter/Eldritch
     Knight. Not duplicated here. -->

## Bardic Inspiration
action_type: bonus_action
resource_key: bardic_inspiration
min_level: 1
max_uses: Charisma modifier (minimum 1)   # stat-based, not a flat table value — recompute on ability score changes
die_size: d6         # becomes d8 at lvl 5, d10 at lvl 10, d12 at lvl 15
rest_type: long regain all   # upgrades to short regain all, long regain all starting lvl 5 (Font of Inspiration)
bonus_recharge: from lvl 5 (Font of Inspiration), expend 1 spell slot (no action) to regain 1 use early
description: Give a Bardic Inspiration die to a creature within 60 ft. who can see or hear you (max one die per creature at a time). Within the next hour, that creature can roll the die and add it to a failed D20 Test, potentially turning the failure into a success. The die is expended when rolled.

## Superior Inspiration
action_type: free_action   # triggered when you roll Initiative
min_level: 18
description: When you roll Initiative, regain expended uses of Bardic Inspiration until you have at least 2.

<!-- Excluded base-class features (no decision point / no action / no resource): Expertise, Jack of All
     Trades, Ability Score Improvement, Magical Secrets (spell-list/prep expansion), Epic Boon, Words of
     Creation (automatic rider when casting Power Word Heal/Kill, plus passive spell prep). -->

## Countercharm
action_type: reaction   # no resource — unlimited
min_level: 7
description: If you or a creature within 30 ft. of you fails a save against an effect imposing Charmed or Frightened, cause the save to be rerolled with Advantage.

---

### Subclass: College of Dance

## Agile Strikes
action_type: free_action   # no separate resource — rides on spending a Bardic Inspiration use (any method) elsewhere
subclass: dance
min_level: 3
description: When you expend a use of Bardic Inspiration as part of an action, a Bonus Action, or a Reaction, make one Unarmed Strike as part of that same action. Use Dexterity instead of Strength for the attack roll, and deal Bludgeoning damage equal to a roll of your Bardic Inspiration die plus your Dexterity modifier instead of normal damage (this roll doesn't expend the die).

## Inspiring Movement
action_type: reaction
consumes_resource: bardic_inspiration
subclass: dance
min_level: 6
description: When an enemy you can see ends its turn within 5 ft. of you, move up to half your Speed; one ally of your choice within 30 ft. can also move up to half their Speed with their own Reaction. None of this movement provokes Opportunity Attacks.

## Tandem Footwork
action_type: free_action   # triggered when you roll Initiative
consumes_resource: bardic_inspiration
subclass: dance
min_level: 6
description: When you roll Initiative (and aren't Incapacitated), roll your Bardic Inspiration die; you and each ally within 30 ft. who can see or hear you gain a bonus to Initiative equal to the number rolled.

## Leading Evasion
action_type: free_action   # no resource — automatic on a successful Dex save that would halve damage, with a sharing choice
subclass: dance
min_level: 14
description: When you succeed on a Dexterity save that would normally halve damage, take no damage instead (still half on a failed save). Extend this benefit to creatures within 5 ft. making the same save.

<!-- Excluded: Dazzling Footwork's Unarmored Defense and Dance Virtuoso (passive). -->

---

### Subclass: College of Glamour

## Beguiling Magic
action_type: free_action   # triggered immediately after casting an Enchantment/Illusion spell with a spell slot
resource_key: beguiling_magic
subclass: glamour
min_level: 3
max_uses: 1
rest_type: long
bonus_recharge: expend 1 bardic_inspiration (no action) to restore early
description: Force a creature within 60 ft. to make a Wisdom save or gain the Charmed or Frightened condition (your choice) for 1 minute (save ends at end of each of its turns).

## Mantle of Inspiration
action_type: bonus_action
consumes_resource: bardic_inspiration
subclass: glamour
min_level: 3
description: Roll your Bardic Inspiration die; choose creatures within 60 ft. (up to your Charisma modifier, minimum 1) to each gain Temporary HP equal to twice the number rolled, then each can use their Reaction to move up to their Speed without provoking Opportunity Attacks.

## Mantle of Majesty
action_type: bonus_action
resource_key: mantle_of_majesty
subclass: glamour
min_level: 6
max_uses: 1
rest_type: long
bonus_recharge: expend 1 spell slot of level 3+ (no action) to restore early
description: Cast Command without a spell slot and assume an unearthly appearance for 1 minute; while transformed, cast Command again as a Bonus Action without expending a spell slot each turn. Creatures Charmed by you automatically fail their save against this Command.

## Unbreakable Majesty
action_type: bonus_action
resource_key: unbreakable_majesty
subclass: glamour
min_level: 14
max_uses: 1
rest_type: short regain all, long regain all
description: Assume a majestic presence for 1 minute (or until Incapacitated). While active, the first time each turn a creature hits you with an attack roll, it must succeed on a Charisma save or the attack misses instead.

<!-- Excluded: Beguiling Magic's and Mantle of Majesty's always-prepared spells (passive). -->

---

### Subclass: College of Lore

## Cutting Words
action_type: reaction
consumes_resource: bardic_inspiration
subclass: lore
min_level: 3
description: When a creature you can see within 60 ft. makes a damage roll or succeeds on an ability check or attack roll, roll your Bardic Inspiration die and subtract the result from that roll, potentially reducing damage or turning a success into a failure.

## Peerless Skill
action_type: free_action   # triggered on a failed ability check or attack roll
consumes_resource: bardic_inspiration
subclass: lore
min_level: 14
description: When you fail an ability check or attack roll, roll your Bardic Inspiration die and add it to the d20, potentially turning the failure into a success. If it's still a failure, the use is not expended.

<!-- Excluded: Bonus Proficiencies (passive), Magical Discoveries (spell-list expansion, no combat action). -->

---

### Subclass: College of Valor

## Combat Inspiration — Defense
action_type: reaction   # spent by whichever creature holds the die, not necessarily the Bard
consumes_resource: bardic_inspiration
subclass: valor
min_level: 3
description: A creature holding a Bardic Inspiration die from you can, when hit by an attack roll, roll the die and add it to its AC against that attack, potentially causing a miss.

## Combat Inspiration — Offense
action_type: free_action   # spent by whichever creature holds the die, not necessarily the Bard
consumes_resource: bardic_inspiration
subclass: valor
min_level: 3
description: A creature holding a Bardic Inspiration die from you can, immediately after hitting with an attack roll, roll the die and add it to that attack's damage.

## Cantrip Strike
action_type: free_action   # no resource — unlimited, choice made as part of the Attack action
subclass: valor
min_level: 6
description: When you take the Attack action, cast one of your cantrips with a casting time of an action in place of one of your attacks.

## Battle Magic
action_type: bonus_action   # no resource — unlimited
subclass: valor
min_level: 14
description: After you cast a spell with a casting time of an action, make one attack with a weapon as a Bonus Action.

<!-- Excluded: Martial Training (passive proficiency), Extra Attack (passive attack count). -->
