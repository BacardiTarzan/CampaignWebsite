# Paladin

<!-- Verified against PHB raw text (chapter 3, Paladin), not the Classes.md project reference.
     Spellcasting (cantrips, prepared spells, spell slots per the Paladin Features table) belongs to your
     existing spell-slot system, not this combat-resource seeder — same treatment as the other casters.
     Several Paladin features grant a FREE cast of a specific spell (Divine Smite via Paladin's Smite,
     Find Steed via Faithful Steed) with their own once-per-rest cap; those free-cast charges are tracked
     here since they're discrete combat resources, even though the underlying spells themselves are not. -->

## Lay on Hands
action_type: bonus_action
resource_key: lay_on_hands
min_level: 1
max_uses: 5 × Paladin level   # pool size scales every level, not fixed breakpoints
rest_type: long regain all
description: Touch a creature (which could be yourself) and draw from the pool to restore HP to it, up to the maximum remaining in the pool. Alternatively, expend 5 HP from the pool to remove the Poisoned condition from the creature (no additional HP restored). From lvl 14 (Restoring Touch), you can instead expend 5 HP from the pool for each of the following conditions you want to remove: Blinded, Charmed, Deafened, Frightened, Paralyzed, or Stunned (those points don't also restore HP).

## Paladin's Smite
action_type: bonus_action   # matches Divine Smite's own casting time: a Bonus Action taken immediately after hitting with a Melee weapon or Unarmed Strike
resource_key: paladins_smite_free_cast
min_level: 2
max_uses: 1
rest_type: long
description: You always have the Divine Smite spell prepared and can cast it without expending a spell slot once per Long Rest (further casts require a spell slot, out of scope — handled by your existing spell-slot system). Divine Smite deals an extra 2d8 Radiant damage on the triggering hit (+1d8 if the target is a Fiend or Undead; +1d8 per spell slot level above 1 if cast with a slot).

## Channel Divinity (pool)
action_type: special   # genuine edge case — pool definition only, no single trigger action; spent via Divine Sense, Abjure Foes, and the subclass options below
resource_key: channel_divinity
min_level: 3
max_uses: 2          # increases to 3 at lvl 11
rest_type: short regain 1, long regain all
description: Fuels Divine Sense, Abjure Foes, and each subclass's own Channel Divinity option(s).

## Divine Sense
action_type: bonus_action
consumes_resource: channel_divinity
min_level: 3
description: Open your awareness to detect Celestials, Fiends, and Undead. For the next 10 minutes (or until Incapacitated), know the location and creature type of any such creature within 60 ft. of yourself; also detect any place or object within that radius that's been consecrated or desecrated.

## Abjure Foes
action_type: action   # uses the Magic action specifically
consumes_resource: channel_divinity
min_level: 9
description: Present your Holy Symbol or weapon; target a number of creatures within 60 ft. equal to your Charisma modifier (minimum 1). Each makes a Wisdom save or has the Frightened condition for 1 minute or until it takes damage. While Frightened this way, a target can only move, take an action, or take a Bonus Action on its turn (not more than one of those).

<!-- Excluded base-class features (no decision point / no action / no resource, or out of scope): Weapon
     Mastery (passive proficiency; the Long-Rest swap is downtime customization), Fighting Style, Paladin
     Subclass, Ability Score Improvement, Extra Attack, Aura of Protection (passive saving-throw bonus to
     self/allies in the aura), Aura of Courage (passive Frightened immunity in the aura), Radiant Strikes
     (automatic on-hit rider, fixed damage type, no decision — unlike Divine Strike/Primal Strike's
     damage-type choice), Aura Expansion (passive radius increase, folds into Aura of Protection), Epic
     Boon. -->

---

### Subclass: Oath of Devotion

## Sacred Weapon
action_type: free_action   # rider on the Attack action — no separate action of its own
consumes_resource: channel_divinity
subclass: devotion
min_level: 3
description: When you take the Attack action, imbue one Melee weapon you're holding with positive energy for 10 minutes (or until Incapacitated, or you end it early with no action required, or you stop carrying it). While imbued, add your Charisma modifier (minimum +1) to attack rolls with it, and each hit deals its normal damage type or Radiant damage (your choice); the weapon also sheds Bright Light 20 ft. and Dim Light 20 ft. beyond that.

<!-- Excluded: Aura of Devotion (passive Charmed immunity in the aura), Smite of Protection (lvl 15 —
     automatic Half Cover for self/allies in the aura whenever you cast Divine Smite, no separate decision;
     folds conceptually into Paladin's Smite/Divine Smite but isn't tracked as its own block). -->

## Holy Nimbus
action_type: bonus_action
resource_key: holy_nimbus
subclass: devotion
min_level: 20
max_uses: 1
rest_type: long
bonus_recharge: expend 1 spell slot of level 5 (no action) to restore early
description: Imbue your Aura of Protection with holy power for 10 minutes (or until you end it early, no action required). While active: Advantage on saves forced by a Fiend or Undead; enemies starting their turn in the aura take Radiant damage equal to your Charisma modifier plus Proficiency Bonus (automatic); the aura sheds sunlight.

---

### Subclass: Oath of Glory

## Inspiring Smite
action_type: free_action   # rider taken immediately after casting Divine Smite — no separate action of its own
consumes_resource: channel_divinity
subclass: glory
min_level: 3
description: Immediately after casting Divine Smite, distribute Temporary HP (2d8 plus your Paladin level, total) among creatures of your choice within 30 ft. of yourself, which can include you.

## Peerless Athlete
action_type: bonus_action
consumes_resource: channel_divinity
subclass: glory
min_level: 3
description: For 1 hour, gain Advantage on Strength (Athletics) and Dexterity (Acrobatics) checks, and your Long/High Jump distance increases by 10 ft. (extra distance still costs movement as normal).

<!-- Excluded: Aura of Alacrity (passive Speed increase to self and allies entering/starting in the aura). -->

## Glorious Defense
action_type: reaction
resource_key: glorious_defense
subclass: glory
min_level: 15
max_uses: Charisma modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: When you or a creature within 10 ft. of you is hit by an attack roll, grant the target a bonus to AC against that attack equal to your Charisma modifier (minimum +1), potentially causing a miss. If it misses, you can also make one weapon attack against the attacker as part of this Reaction if it's within range.

## Living Legend
action_type: bonus_action
resource_key: living_legend
subclass: glory
min_level: 20
max_uses: 1
rest_type: long
bonus_recharge: expend 1 spell slot of level 5 (no action) to restore early
description: Gain the benefits below for 10 minutes (or until you end them early, no action required): Charismatic (Advantage on all Charisma checks, automatic), plus the Saving Throw Reroll and Unerring Strike options below.

## Living Legend — Saving Throw Reroll
action_type: reaction   # no separate resource — gated on Living Legend being active, unlimited uses while it lasts
subclass: glory
min_level: 20
description: While Living Legend is active, if you fail a saving throw, take a Reaction to reroll it. You must use the new roll.

## Living Legend — Unerring Strike
action_type: free_action   # once per turn, no separate resource — gated on Living Legend being active
subclass: glory
min_level: 20
description: While Living Legend is active, once on each of your turns when you make an attack roll with a weapon and miss, you can cause that attack to hit instead.

---

### Subclass: Oath of the Ancients

## Nature's Wrath
action_type: action   # uses the Magic action specifically
consumes_resource: channel_divinity
subclass: ancients
min_level: 3
description: Conjure spectral vines around nearby creatures. Each creature of your choice within 15 ft. that you can see makes a Strength save or has the Restrained condition for 1 minute (repeats the save at the end of each of its turns, ending the effect on itself on a success).

<!-- Excluded: Aura of Warding (passive Resistance to Necrotic/Psychic/Radiant in the aura). -->

## Undying Sentinel
action_type: free_action   # triggered when you're reduced to 0 HP and not killed outright
resource_key: undying_sentinel
subclass: ancients
min_level: 15
max_uses: 1
rest_type: long
description: Drop to 1 HP instead of 0 and regain HP equal to three times your Paladin level. (Also grants passive immunity to magical aging — not tracked as a resource.)

## Elder Champion
action_type: bonus_action
resource_key: elder_champion
subclass: ancients
min_level: 20
max_uses: 1
rest_type: long
bonus_recharge: expend 1 spell slot of level 5 (no action) to restore early
description: Imbue your Aura of Protection with primal power for 1 minute (or until you end it early, no action required). While active: enemies in the aura have Disadvantage on saves against your spells and Channel Divinity options (automatic); you regain 10 HP at the start of each of your turns (automatic); and you can cast any spell with a casting time of an action using a Bonus Action instead (spellcasting itself out of scope).

---

### Subclass: Oath of Vengeance

## Vow of Enmity
action_type: free_action   # rider on the Attack action — no separate action of its own
consumes_resource: channel_divinity
subclass: vengeance
min_level: 3
description: Utter a vow of enmity against a creature you can see within 30 ft. Gain Advantage on attack rolls against it for 1 minute or until you use this feature again. If the creature drops to 0 HP before the vow ends, transfer the vow to a different creature within 30 ft. (no action required).

## Relentless Avenger
action_type: free_action   # rider on a hit with an Opportunity Attack — includes a free follow-up move
subclass: vengeance
min_level: 7
description: When you hit a creature with an Opportunity Attack, reduce its Speed to 0 until the end of the current turn, then move up to half your Speed as part of the same Reaction (no Opportunity Attacks provoked).

## Soul of Vengeance
action_type: reaction   # no resource — unlimited, triggered by a creature under your Vow of Enmity
subclass: vengeance
min_level: 15
description: Immediately after a creature under your Vow of Enmity hits or misses with an attack roll, make a melee attack against it if it's within range.

## Avenging Angel
action_type: bonus_action
resource_key: avenging_angel
subclass: vengeance
min_level: 20
max_uses: 1
rest_type: long
bonus_recharge: expend 1 spell slot of level 5 (no action) to restore early
description: Gain the benefits below for 10 minutes (or until you end them early, no action required): Flight (Fly Speed 60 ft., can hover); Frightful Aura (automatic — enemies starting their turn in your Aura of Protection make a Wisdom save or are Frightened for 1 minute or until damaged; attacks against a Frightened creature this way have Advantage).
