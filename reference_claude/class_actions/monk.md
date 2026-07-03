# Monk

<!-- Verified against PHB raw text (chapter 3, Monk), not the Classes.md project reference.
     Monk has no spellcasting of its own (aside from subclass-granted cantrips noted as out of scope
     below), so there's no blanket spellcasting exclusion here as with the other classes. -->

## Martial Arts — Bonus Unarmed Strike
action_type: bonus_action   # no resource — unlimited, requires being unarmed/wielding only Monk weapons and no armor/Shield
min_level: 1
description: Make an Unarmed Strike. Roll your Martial Arts die (1d6, scaling to 1d8 at lvl 5, 1d10 at lvl 11, 1d12 at lvl 17) in place of normal Unarmed Strike/Monk weapon damage; use Dexterity instead of Strength for the attack/damage rolls (and for Grapple/Shove save DCs).

## Monk's Focus (pool)
action_type: special   # genuine edge case — pool definition only, no single trigger action; spent via Flurry of Blows, Patient Defense, Step of the Wind, and the features below
resource_key: focus_points
min_level: 2
max_uses: 2          # increases by 1 each level starting lvl 2 (equals your Monk level from lvl 2 on)
rest_type: short regain all, long regain all
description: Fuels Flurry of Blows, Patient Defense, Step of the Wind, and other Monk/subclass features below. Save DC for any Focus Point feature requiring one equals 8 + Wisdom modifier + Proficiency Bonus.

## Flurry of Blows
action_type: bonus_action
consumes_resource: focus_points
min_level: 2
description: Make two Unarmed Strikes. From lvl 10 (Heightened Focus), make three Unarmed Strikes instead of two.

## Patient Defense
action_type: bonus_action   # no resource required for the base effect — optional Focus Point spend for the upgrade
consumes_resource: focus_points
min_level: 2
description: Take the Disengage action (free). Optionally expend 1 Focus Point to also take the Dodge action as part of the same Bonus Action. From lvl 10 (Heightened Focus), when you spend the Focus Point, also gain Temporary HP equal to two rolls of your Martial Arts die.

## Step of the Wind
action_type: bonus_action   # no resource required for the base effect — optional Focus Point spend for the upgrade
consumes_resource: focus_points
min_level: 2
description: Take the Dash action (free). Optionally expend 1 Focus Point to also take the Disengage action and double your jump distance for the turn. From lvl 10 (Heightened Focus), when you spend the Focus Point, you may also bring a willing Large-or-smaller creature within 5 ft. along with your movement (no Opportunity Attacks).

## Uncanny Metabolism
action_type: free_action   # triggered when you roll Initiative
resource_key: uncanny_metabolism
min_level: 2
max_uses: 1
rest_type: long
description: Regain all expended Focus Points and regain HP equal to your Monk level plus a roll of your Martial Arts die. From lvl 15 (Perfect Focus), as an alternative on a turn you don't use Uncanny Metabolism (no resource/cap of its own): if you have 3 or fewer Focus Points, regain expended Focus Points until you have 4.

## Deflect Attacks
action_type: reaction
consumes_resource: focus_points   # optional — only the "reduce to 0" follow-up spends a Focus Point
min_level: 3
description: When hit by an attack dealing Bludgeoning, Piercing, or Slashing damage (any damage type from lvl 13, Deflect Energy), reduce the total damage by 1d10 + Dexterity modifier + Monk level. If this reduces the damage to 0, you may expend 1 Focus Point to redirect the force: a creature you choose (within 5 ft. for a melee attack, within 60 ft. and not behind Total Cover for a ranged attack) makes a Dexterity save or takes damage equal to two rolls of your Martial Arts die plus your Dexterity modifier (same type as the original attack).

## Slow Fall
action_type: reaction   # no resource — unlimited
min_level: 4
description: When you fall, reduce the fall damage you take by five times your Monk level.

## Stunning Strike
action_type: free_action   # once per turn, rider on an Unarmed Strike/Monk weapon hit
consumes_resource: focus_points
min_level: 5
description: Expend 1 Focus Point; target makes a Constitution save or has the Stunned condition until the start of your next turn (on a success, its Speed is halved and the next attack against it before then has Advantage).

## Empowered Strikes
action_type: free_action   # no resource — choice made each time you deal Unarmed Strike damage
min_level: 6
description: Your Unarmed Strike damage can be Force damage or its normal type (choose each time).

## Self-Restoration
action_type: free_action   # automatic at the end of each of your turns — choice of which condition to remove if more than one applies
min_level: 10
description: Remove one of the following conditions from yourself: Charmed, Frightened, or Poisoned. (Also grants passive immunity to Exhaustion from forgoing food/drink — not tracked as a resource.)

## Disciplined Survivor — Reroll
action_type: free_action   # triggered on a failed saving throw
consumes_resource: focus_points
min_level: 14
description: Expend 1 Focus Point to reroll a failed saving throw. You must use the new roll. (Disciplined Survivor also grants passive proficiency in all saving throws — not tracked as a resource.)

## Superior Defense
action_type: free_action   # triggered at the start of your turn
consumes_resource: focus_points   # costs 3
min_level: 18
description: Expend 3 Focus Points to gain Resistance to all damage except Force for 1 minute (or until Incapacitated).

<!-- Excluded base-class features (no decision point / no action / no resource): Unarmored Defense,
     Dexterous Attacks (folded above into Martial Arts), Unarmored Movement, Monk Subclass, Ability Score
     Improvement, Evasion (automatic, no decision), Acrobatic Movement (passive terrain rule), Epic Boon,
     Body and Mind. -->

---

### Subclass: Warrior of Mercy

## Hand of Harm
action_type: free_action   # once per turn, rider on an Unarmed Strike hit
consumes_resource: focus_points
subclass: mercy
min_level: 3
description: Deal extra Necrotic damage equal to a Martial Arts die roll plus your Wisdom modifier. From lvl 6 (Physician's Touch), also inflict the Poisoned condition on the target until the end of your next turn.

## Hand of Healing
action_type: action   # uses the Magic action specifically
consumes_resource: focus_points
subclass: mercy
min_level: 3
description: Touch a creature to restore HP equal to a Martial Arts die roll plus your Wisdom modifier. From lvl 6 (Physician's Touch), also end one of: Blinded, Deafened, Paralyzed, Poisoned, or Stunned on that creature. You can replace one Unarmed Strike from Flurry of Blows with this feature without spending an extra Focus Point for the healing.

<!-- Excluded: Implements of Mercy (passive proficiency). -->

## Flurry of Healing and Harm
action_type: free_action   # rides on Flurry of Blows' own Bonus Action
resource_key: flurry_of_healing_and_harm
subclass: mercy
min_level: 11
max_uses: Wisdom modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: When you use Flurry of Blows, replace each Unarmed Strike with Hand of Healing without spending Focus Points for the healing, and/or use Hand of Harm on one of the strikes without spending a Focus Point for it (still only once per turn for Hand of Harm).

## Hand of Ultimate Mercy
action_type: action   # uses the Magic action specifically
resource_key: hand_of_ultimate_mercy   # plus expend 5 Focus Points
subclass: mercy
min_level: 17
max_uses: 1
rest_type: long
description: Touch the corpse of a creature dead within the past 24 hours and expend 5 Focus Points to revive it with 4d10 + Wisdom modifier HP, removing Blinded, Deafened, Paralyzed, Poisoned, and Stunned if present at death.

---

### Subclass: Warrior of Shadow

## Shadow Arts — Darkness
action_type: free_action   # no separate action — casts Darkness via Focus Point spend; moving the area each turn is free
consumes_resource: focus_points
subclass: shadow
min_level: 3
description: Expend 1 Focus Point to cast Darkness without components (you can see within it). At the start of each of your turns while it persists, you may move its area to a space within 60 ft. of yourself.

<!-- Excluded: Darkvision (passive), Shadowy Figments (grants the Minor Illusion cantrip — out of scope). -->

## Shadow Step
action_type: bonus_action   # requires being entirely within Dim Light or Darkness; optional Focus Point spend removes that requirement
consumes_resource: focus_points
subclass: shadow
min_level: 6
description: Teleport up to 60 ft. to an unoccupied space you can see (must start and end in Dim Light/Darkness); gain Advantage on your next melee attack this turn. From lvl 11 (Improved Shadow Step), optionally expend 1 Focus Point to ignore the light requirement and make an Unarmed Strike immediately after teleporting, as part of the same Bonus Action.

## Cloak of Shadows
action_type: action   # uses the Magic action specifically
consumes_resource: focus_points   # costs 3
subclass: shadow
min_level: 17
description: While entirely within Dim Light or Darkness, expend 3 Focus Points to shroud yourself for 1 minute (ends if Incapacitated or if you end your turn in Bright Light): gain the Invisible condition; move through occupied spaces as Difficult Terrain (shunted to the last unoccupied space if you end your turn in one); and use Flurry of Blows without spending Focus Points.

---

### Subclass: Warrior of the Elements

## Elemental Attunement
action_type: free_action   # triggered at the start of your turn
consumes_resource: focus_points
subclass: elements
min_level: 3
description: Expend 1 Focus Point to imbue yourself with elemental energy for 10 minutes (or until Incapacitated). While active: your Unarmed Strike reach extends 10 ft., and on a hit you may choose to deal Acid, Cold, Fire, Lightning, or Thunder damage instead of normal type (if you do, target makes a Strength save or is moved up to 10 ft. toward/away from you). From lvl 11 (Stride of the Elements), you also gain a Fly Speed and Swim Speed equal to your Speed while active. From lvl 17 (Elemental Epitome): gain Resistance to a damage type of your choice from the list above (changeable at the start of each turn), and when you use Step of the Wind, your Speed increases by 20 ft. for the turn and creatures within 5 ft. of where you enter take a Martial Arts die roll of damage (chosen type, once per turn per creature) — plus, once per turn, deal extra damage (same type as the strike) equal to a Martial Arts die roll on an Unarmed Strike hit.

<!-- Excluded: Manipulate Elements (grants the Elementalism cantrip — out of scope). -->

## Elemental Burst
action_type: action   # uses the Magic action specifically
consumes_resource: focus_points   # costs 2
subclass: elements
min_level: 6
description: Expend 2 Focus Points; choose a damage type (Acid, Cold, Fire, Lightning, or Thunder) and a point within 120 ft. Each creature in a 20-ft.-radius Sphere there makes a Dexterity save, taking three Martial Arts die rolls of that damage on a failure (half on a success).

---

### Subclass: Warrior of the Open Hand

## Open Hand Technique
action_type: free_action   # rider on a Flurry of Blows hit — no separate resource (already paid via Flurry of Blows)
subclass: open_hand
min_level: 3
description: When you hit with a Flurry of Blows strike, impose one of: Addle (target can't make Opportunity Attacks until its next turn), Push (Strength save or pushed 15 ft.), or Topple (Dexterity save or Prone).

## Wholeness of Body
action_type: bonus_action
resource_key: wholeness_of_body
subclass: open_hand
min_level: 6
max_uses: Wisdom modifier (minimum 1)   # stat-based, not a flat table value
rest_type: long regain all
description: Roll your Martial Arts die; regain that many HP plus your Wisdom modifier (minimum 1).

## Fleet Step
action_type: free_action   # no resource of its own — removes an action-economy restriction; Step of the Wind's own (optional) Focus Point cost still applies if used
subclass: open_hand
min_level: 11
description: When you take a Bonus Action other than Step of the Wind, you can also use Step of the Wind immediately after it.

## Quivering Palm — Start
action_type: free_action   # rider on an Unarmed Strike hit
consumes_resource: focus_points   # costs 4
subclass: open_hand
min_level: 17
description: Expend 4 Focus Points to start lethal vibrations lasting a number of days equal to your Monk level (only one creature affected at a time).

## Quivering Palm — End
action_type: free_action   # alternatively, forgo an attack during the Attack action; ending harmlessly requires no action
subclass: open_hand
min_level: 17
description: End the vibrations: target makes a Constitution save, taking 10d12 Force damage on a failure (half on a success). You can also end them harmlessly with no action required.
