# Druid

<!-- Verified against PHB raw text (chapter 3, Druid), not the Classes.md project reference.
     Spellcasting (cantrips, prepared spells, spell slots per the Druid Features table) belongs to your
     existing spell-slot system, not this combat-resource seeder — same treatment as the other casters.
     Not duplicated here. Note: several Druid features let you spend a spell slot as an ALTERNATE cost for
     a Wild Shape-related effect; those are noted in descriptions but the slot itself isn't tracked here. -->

## Wild Shape
action_type: bonus_action
resource_key: wild_shape
min_level: 2
max_uses: 2          # increases to 3 at lvl 6, 4 at lvl 17
rest_type: short regain 1, long regain all
bonus_recharge: from lvl 5 (Wild Resurgence), once per turn, expend 1 spell slot (no action) to gain 1 use if you have none left; from lvl 20 (Archdruid — Evergreen Wild Shape), automatically regain 1 use when you roll Initiative if you have none left
description: Shape-shift into a Beast form you know (max CR and access to Fly Speed forms scale with Druid level). Lasts for hours equal to half your Druid level, until you use Wild Shape again, or until Incapacitated/dead; you can also leave the form early as a Bonus Action. Gain Temporary HP equal to your Druid level on assuming the form. No spellcasting while shape-shifted.

## Wild Companion
action_type: action   # uses the Magic action specifically
consumes_resource: wild_shape   # alternate cost: a spell slot (out of scope) instead of a Wild Shape use
min_level: 2
description: Cast Find Familiar without Material components, expending either a spell slot or a use of Wild Shape. The familiar is Fey and disappears when you finish a Long Rest.

## Wild Shape — Convert to Spell Slot
action_type: free_action   # no action required
consumes_resource: wild_shape
min_level: 5
description: From lvl 5 (Wild Resurgence), expend 1 use of Wild Shape to gain a level 1 spell slot; once per Long Rest. From lvl 20 (Archdruid — Nature Magician), instead expend any number of unexpended Wild Shape uses to create a single spell slot, each use contributing 2 spell levels (e.g. 2 uses = a level 4 slot); still once per Long Rest, and replaces rather than stacks with the lvl 5 version.

## Elemental Fury — Primal Strike
action_type: free_action   # once per turn, automatic on a hit — damage type is a choice
min_level: 7
description: Chosen at lvl 7 as one of two Elemental Fury options (the alternative, Potent Spellcasting, is a passive cantrip-damage bonus — see exclusions below). Once on each of your turns when you hit with a weapon or Wild Shape attack, deal an extra 1d8 Cold, Fire, Lightning, or Thunder damage (choose when you hit). The extra damage increases to 2d8 at lvl 15 (Improved Elemental Fury).

<!-- Excluded base-class features (no decision point / no action / no resource, or out of scope): Druidic
     (secret language/utility, no combat use), Primal Order (one-time choice at character creation between
     Magician [extra cantrip + passive skill bonus] and Warden [proficiency] — both passive), Druid
     Subclass, Ability Score Improvement, Beast Spells (lvl 18, passive unlock — enables casting spells
     while shape-shifted, no separate decision), Epic Boon, Longevity (Archdruid, flavor/aging). Elemental
     Fury's Potent Spellcasting alternative is passive (flat cantrip range/damage bonus) — excluded. -->

---

### Subclass: Circle of the Land

## Land's Aid
action_type: action   # uses the Magic action specifically
consumes_resource: wild_shape
subclass: land
min_level: 3
description: Expend a use of Wild Shape; vitality-giving flowers and life-draining thorns appear in a 10-ft.-radius Sphere within 60 ft. Each creature of your choice there makes a Constitution save against your spell save DC, taking 2d6 Necrotic damage on a failure (half on a success); one creature of your choice there regains 2d6 HP. Damage and healing increase by 1d6 at lvl 10 (3d6) and lvl 14 (4d6).

## Natural Recovery — Free Cast
action_type: free_action   # rides on the spell's own casting time
resource_key: natural_recovery_cast
subclass: land
min_level: 6
max_uses: 1
rest_type: long
description: Cast one of your level 1+ Circle Spells (the always-prepared spells from your chosen land type) without expending a spell slot.

## Natural Recovery — Slot Recovery
action_type: free_action   # no action required, triggered specifically when you finish a Short Rest
resource_key: natural_recovery_slots
subclass: land
min_level: 6
max_uses: 1
rest_type: long
description: When you finish a Short Rest, recover expended spell slots with a combined level up to half your Druid level (round up), none of which can be level 6+.

## Nature's Sanctuary
action_type: action   # uses the Magic action specifically
consumes_resource: wild_shape
subclass: land
min_level: 14
description: Expend a use of Wild Shape to summon spectral trees and vines in a 15-ft. Cube within 120 ft. for 1 minute (or until Incapacitated/dead). You and allies there have Half Cover, and allies there gain your current Nature's Ward Resistance.

## Nature's Sanctuary — Move Cube
action_type: bonus_action   # no resource — unlimited while the Cube is active
subclass: land
min_level: 14
description: Move the Nature's Sanctuary Cube up to 60 ft. to ground within 120 ft. of yourself.

<!-- Excluded: Circle of the Land Spells (always-prepared spell list by land type — out of scope), Nature's
     Ward (passive Poison immunity + damage Resistance by land type). -->

---

### Subclass: Circle of the Moon

## Lunar Radiance
action_type: free_action   # no resource — choice made each time a Wild Shape attack hits
subclass: moon
min_level: 6
description: Each of your attacks in a Wild Shape form can deal its normal damage type or Radiant damage (choose each time you hit). From lvl 14 (Lunar Form — Improved Lunar Radiance), also deal an extra 2d10 Radiant damage once per turn when you hit with a Wild Shape attack, regardless of which type you chose.

## Moonlight Step
action_type: bonus_action
resource_key: moonlight_step
subclass: moon
min_level: 10
max_uses: Wisdom modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
bonus_recharge: expend 1 spell slot of level 2+ (no action) per use restored
description: Teleport up to 30 ft. to an unoccupied space you can see; gain Advantage on your next attack roll before the end of this turn. From lvl 14 (Lunar Form — Shared Moonlight), you can also teleport one willing creature within 10 ft. of you to an unoccupied space within 10 ft. of your destination.

<!-- Excluded: Circle Forms (lvl 3 — passive CR cap/AC formula/Temp HP rider on Wild Shape, no decision),
     Circle of the Moon Spells (always-prepared spell list — out of scope), Increased Toughness (passive
     Constitution save bonus), Full of Stars-equivalent passives n/a here. -->

---

### Subclass: Circle of the Sea

## Wrath of the Sea
action_type: bonus_action
consumes_resource: wild_shape   # from lvl 14 (Oceanic Gift), can expend 2 uses instead of 1 to center the Emanation on both yourself and an ally
subclass: sea
min_level: 3
description: Manifest a 5-ft. Emanation of ocean spray around yourself for 10 minutes (dismissable, no action required; ends early if manifested again or if Incapacitated). Emanation grows to 10 ft. at lvl 6 (Aquatic Affinity, which also grants a Swim Speed equal to your Speed). From lvl 10 (Stormborn), while active you also gain a Fly Speed equal to your Speed and Resistance to Cold, Lightning, and Thunder damage. From lvl 14 (Oceanic Gift), you may instead center the Emanation on a willing creature within 60 ft. (using your spell save DC/Wisdom modifier), or on both yourself and that creature by expending 2 uses of Wild Shape instead of 1.

## Wrath of the Sea — Target
action_type: bonus_action   # no resource — unlimited on subsequent turns while the Emanation is active
subclass: sea
min_level: 3
description: Choose another creature you can see in the Wrath of the Sea Emanation; it makes a Constitution save against your spell save DC or takes Cold damage (d6s equal to your Wisdom modifier, minimum 1) and, if Large or smaller, is pushed up to 15 ft. away.

<!-- Excluded: Circle of the Sea Spells (always-prepared spell list — out of scope). Aquatic Affinity and
     Stormborn are folded into Wrath of the Sea's description as passive scaling, not separate blocks. -->

---

### Subclass: Circle of the Stars

## Star Map — Free Guiding Bolt
action_type: action   # rides on Guiding Bolt's own casting time (an action)
resource_key: star_map_guiding_bolt
subclass: stars
min_level: 3
max_uses: Wisdom modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: Cast Guiding Bolt (always prepared while holding your Star Map) without expending a spell slot.

## Starry Form
action_type: bonus_action
consumes_resource: wild_shape
subclass: stars
min_level: 3
description: Expend a use of Wild Shape to take a starry form (retains your game statistics; sheds Bright/Dim Light) for 10 minutes (dismissable, no action required; ends early if Incapacitated or used again). Choose a constellation each time you activate it — Archer (enables a recurring ranged spell attack, see below), Chalice (automatic: when you cast a healing spell with a slot, you or a creature within 30 ft. regains 1d8 + Wisdom modifier HP), or Dragon (automatic: treat a 9-or-lower on Intelligence/Wisdom checks or Concentration saves as a 10). From lvl 10 (Twinkling Constellations), the Archer/Chalice die becomes 2d8, the Dragon grants a 20-ft. Fly Speed (hover), and you may change your active constellation at the start of each of your turns. From lvl 14 (Full of Stars), you have Resistance to Bludgeoning, Piercing, and Slashing damage while in this form.

## Starry Form — Archer Attack
action_type: bonus_action   # no resource — unlimited while in Starry Form with Archer active
subclass: stars
min_level: 3
description: Make a ranged spell attack against a creature within 60 ft., dealing 1d8 (2d8 at lvl 10) plus Wisdom modifier Radiant damage on a hit.

## Cosmic Omen
action_type: reaction
resource_key: cosmic_omen
subclass: stars
min_level: 6
max_uses: Wisdom modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: When you finish a Long Rest, roll a die to determine Weal (even) or Woe (odd) for the next day. When a creature you can see within 30 ft. is about to make a D20 Test, roll 1d6 and add it (Weal) or subtract it (Woe) from the total.

<!-- Excluded: Star Map's always-prepared Guidance/Guiding Bolt (out of scope spell prep, separate from the
     free-cast resource above), the Chalice/Dragon constellation effects (automatic, no decision — folded
     into Starry Form's description), Full of Stars (passive — folded into Starry Form's description). -->
