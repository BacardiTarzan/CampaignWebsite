# Cleric

<!-- Verified against PHB raw text (chapter 3, Cleric), not the Classes.md project reference.
     Spellcasting (cantrips, prepared spells, spell slots per the Cleric Features table) belongs to your
     existing spell-slot system, not this combat-resource seeder — same treatment as Fighter/Eldritch
     Knight and Bard. Not duplicated here. -->

## Channel Divinity (pool)
action_type: special   # genuine edge case — pool definition only, no single trigger action; spent via Divine Spark, Turn Undead, and the subclass Channel Divinity options below
resource_key: channel_divinity
min_level: 2
max_uses: 2          # increases to 3 at lvl 6, 4 at lvl 18
rest_type: short regain 1, long regain all
description: Fuels Divine Spark, Turn Undead, and each subclass's own Channel Divinity option(s).

## Divine Spark
action_type: action   # uses the Magic action specifically
consumes_resource: channel_divinity
min_level: 2
description: Point your Holy Symbol at a creature within 30 ft. Roll 1d8 + Wisdom modifier (additional d8 at lvl 7 [2d8], 13 [3d8], 18 [4d8]); either restore that many HP to the creature or force a Constitution save, dealing Necrotic or Radiant damage (your choice) equal to the total on a failed save (half on a success).

## Turn Undead
action_type: action   # uses the Magic action specifically
consumes_resource: channel_divinity
min_level: 2
description: Present your Holy Symbol; each Undead of your choice within 30 ft. makes a Wisdom save or has the Frightened and Incapacitated conditions for 1 minute (ends early on damage, your Incapacitation, or your death). From lvl 5 (Sear Undead), each Undead that fails its save also takes Radiant damage equal to a roll of d8s equal to your Wisdom modifier (minimum 1d8).

## Blessed Strikes — Divine Strike
action_type: free_action   # once per turn, automatic on a hit — damage type is a choice
min_level: 7
description: Chosen at lvl 7 as one of two Blessed Strikes options (the alternative, Potent Spellcasting, is a passive cantrip-damage bonus — see exclusions below). Once on each of your turns when you hit with a weapon attack, deal an extra 1d8 Necrotic or Radiant damage (your choice). The extra damage increases to 2d8 at lvl 14 (Improved Blessed Strikes).

## Divine Intervention
action_type: action   # uses the Magic action specifically
resource_key: divine_intervention
min_level: 10
max_uses: 1
rest_type: long
description: Choose any Cleric spell of level 5 or lower that doesn't require a Reaction to cast; cast it as part of this action without expending a spell slot or Material components. From lvl 20 (Greater Divine Intervention), you may choose Wish; if you do, this resource instead recharges only after you finish 2d4 Long Rests.

<!-- Excluded base-class features (no decision point / no action / no resource, or out of scope): Divine
     Order (one-time choice at character creation between Protector [proficiency] and Thaumaturge [extra
     cantrip + passive skill bonus] — both passive), Cleric Subclass, Ability Score Improvement, Epic Boon.
     Blessed Strikes' Potent Spellcasting alternative is passive (flat cantrip damage bonus; its lvl 14
     temporary-HP rider is still tied to passive cantrip damage, not a separate decision) — excluded. -->

---

### Subclass: Life Domain

## Preserve Life
action_type: action   # uses the Magic action specifically
consumes_resource: channel_divinity
subclass: life
min_level: 3
description: Present your Holy Symbol to evoke healing energy restoring HP equal to five times your Cleric level, divided among Bloodied creatures within 30 ft. (including yourself); no creature can be restored above half its HP maximum this way.

<!-- Excluded: Disciple of Life (automatic extra healing whenever you cast a spell with a slot that
     restores HP — rider on out-of-scope spellcasting, no decision), Life Domain Spells (always-prepared
     spell list — out of scope), Blessed Healer (automatic self-healing rider on casting a healing spell
     on others), Supreme Healing (automatic max-roll rider on healing dice). -->

---

### Subclass: Light Domain

## Radiance of the Dawn
action_type: action   # uses the Magic action specifically
consumes_resource: channel_divinity
subclass: light
min_level: 3
description: Emit a flash of light in a 30-ft. Emanation, dispelling magical Darkness in the area; each creature of your choice there makes a Constitution save, taking 2d10 + Cleric level Radiant damage on a failure (half on a success).

## Warding Flare
action_type: reaction
resource_key: warding_flare
subclass: light
min_level: 3
max_uses: Wisdom modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long   # upgrades to short regain all, long regain all starting lvl 6 (Improved Warding Flare)
description: When a creature you can see within 30 ft. makes an attack roll, impose Disadvantage on it. From lvl 6 (Improved Warding Flare), also grant the target of the triggering attack Temporary HP equal to 2d6 plus your Wisdom modifier.

## Corona of Light
action_type: action   # uses the Magic action specifically
resource_key: corona_of_light
subclass: light
min_level: 17
max_uses: Wisdom modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: Emit Bright Light in a 60-ft. radius and Dim Light for an additional 30 ft. for 1 minute (or until dismissed, no action required). Enemies in the Bright Light have Disadvantage on saves against your Radiance of the Dawn and against any spell you cast that deals Fire or Radiant damage.

<!-- Excluded: Light Domain Spells (always-prepared spell list — out of scope). -->

---

### Subclass: Trickery Domain

## Blessing of the Trickster
action_type: action   # uses the Magic action specifically; no resource — self-limiting (ends on reuse or Long Rest), not a charge-based pool
subclass: trickery
min_level: 3
description: Grant yourself or a willing creature within 30 ft. Advantage on Dexterity (Stealth) checks. Lasts until you finish a Long Rest or use this feature again.

## Invoke Duplicity
action_type: bonus_action
consumes_resource: channel_divinity
subclass: trickery
min_level: 3
description: Create a perfect illusion of yourself in an unoccupied space within 30 ft. for 1 minute (dismissable, no action required; ends early if Incapacitated). While it persists, you can cast spells as though you were in its space (using your own senses), and you have Advantage on attack rolls against creatures within 5 ft. of both you and the illusion. From lvl 17 (Improved Duplicity): allies also gain Advantage attacking creatures within 5 ft. of the illusion, and when the illusion ends, you or a creature of your choice within 5 ft. of it regains HP equal to your Cleric level.

## Invoke Duplicity — Move Illusion
action_type: bonus_action   # no resource — unlimited while the illusion is active
subclass: trickery
min_level: 3
description: Move the Invoke Duplicity illusion up to 30 ft. to an unoccupied space you can see within 120 ft. of yourself. From lvl 6 (Trickster's Transposition), you may instead teleport, swapping places with the illusion.

<!-- Excluded: Trickery Domain Spells (always-prepared spell list — out of scope). -->

---

### Subclass: War Domain

## Guided Strike
action_type: free_action   # free when applied to your own roll; requires a Reaction when applied to another creature's roll (noted below)
consumes_resource: channel_divinity
subclass: war
min_level: 3
description: When you or a creature within 30 ft. of you misses with an attack roll, give that roll a +10 bonus, potentially turning it into a hit. Using this on another creature's roll requires you to take a Reaction.

## War Priest
action_type: bonus_action
resource_key: war_priest
subclass: war
min_level: 3
max_uses: Wisdom modifier (minimum 1)   # stat-based, not a flat table value
rest_type: short regain all, long regain all
description: Make one attack with a weapon or an Unarmed Strike.

## War God's Blessing
action_type: free_action   # changes the cost of casting a spell, not its own action
consumes_resource: channel_divinity
subclass: war
min_level: 6
description: Cast Shield of Faith or Spiritual Weapon without expending a spell slot. The spell doesn't require Concentration; instead it lasts 1 minute, ending early if you cast that spell again, are Incapacitated, or die.

<!-- Excluded: War Domain Spells (always-prepared spell list — out of scope), Avatar of Battle (passive
     damage Resistance). -->
