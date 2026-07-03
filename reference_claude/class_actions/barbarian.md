# Barbarian

<!-- Verified against PHB raw text (chapter 3, Barbarian), not the Classes.md project reference.
     Per the refined scope: every block below is either (a) a feature that owns a resource (resource_key +
     max_uses + rest_type), (b) a feature that spends a charge from an existing resource (consumes_resource,
     no new pool), or (c) a feature with no resource cost at all but that still represents a discrete,
     repeatable combat decision (tagged action_type: action/bonus_action/reaction/move_action/free_action,
     with a comment noting "no resource — unlimited"). Pure passive numeric bonuses with no decision point
     (AC formulas, speed bonuses, always-on advantage, proficiency access, stat floors) are excluded
     entirely — see the exclusion comments at the end of each section. -->

## Rage
action_type: bonus_action
resource_key: rage
min_level: 1
max_uses: 2          # increases to 3 at lvl 3, 4 at lvl 6, 5 at lvl 12, 6 at lvl 17
rest_type: short regain 1, long regain all
description: Enter a Rage (not while wearing Heavy armor). While active — Resistance to Bludgeoning/Piercing/Slashing; bonus to Strength weapon/Unarmed damage (+2, +3 at lvl 9, +4 at lvl 16); Advantage on Strength checks/saves; can't Concentrate or cast spells. Lasts until the end of your next turn; extends another round by attacking, forcing a save, or this Bonus Action again. Max 10 minutes. From lvl 7 (Instinctive Pounce), move up to half Speed as part of this Bonus Action. From lvl 15 (Persistent Rage), lasts 10 minutes without needing to extend, and the condition that ends it early changes from Incapacitated to Unconscious (Heavy armor still ends it).

## Extend Rage
action_type: bonus_action   # no resource — keeps an already-active Rage going for another round
min_level: 1
description: While Rage is active, take a Bonus Action to extend it another round (alternative to extending via an attack roll or forcing a save).

## Reckless Attack
action_type: free_action   # no resource — declared when making your first attack roll of the turn
min_level: 2
description: Gain Advantage on Strength attack rolls until the start of your next turn; attack rolls against you also have Advantage during that time.

## Primal Knowledge
action_type: free_action   # no resource — substitutes the ability used for certain checks while Raging
min_level: 3
description: While Raging, make Acrobatics, Intimidation, Perception, Stealth, or Survival checks as Strength checks instead of their normal ability.

## Brutal Strike
action_type: free_action   # no resource — costs forgoing Reckless Attack's Advantage on one attack roll
min_level: 9
description: Requires Reckless Attack. Forgo Advantage on one Strength attack roll; on a hit, deal +1d10 damage (+2d10 starting lvl 17) and apply one Brutal Strike effect (Forceful Blow or Hamstring Blow; add Staggering Blow and Sundering Blow at lvl 13; apply two effects at once starting lvl 17).

## Relentless Rage
action_type: free_action   # no resource — automatic check when dropped to 0 HP while Raging
min_level: 11
description: On dropping to 0 HP while Raging (and not dying outright), make a DC 10 Constitution save to instead set HP to 2x Barbarian level. DC increases by 5 each use; resets to 10 on finishing a Short or Long Rest.

## Persistent Rage
action_type: free_action   # triggered when you roll Initiative
resource_key: persistent_rage
min_level: 15
max_uses: 1
rest_type: long
description: When you roll Initiative, regain all expended uses of Rage.

<!-- Excluded base-class features (no decision point / no action / no resource): Unarmored Defense,
     Weapon Mastery, Danger Sense, Ability Score Improvement, Extra Attack, Fast Movement, Feral Instinct,
     Indomitable Might, Epic Boon, Primal Champion. -->

---

### Subclass: Path of the Berserker

## Retaliation
action_type: reaction   # no resource — unlimited
subclass: berserker
min_level: 10
description: When a creature within 5 ft. of you deals damage to you, make one melee attack against it.

## Intimidating Presence
action_type: bonus_action
resource_key: intimidating_presence
subclass: berserker
min_level: 14
max_uses: 1
rest_type: long
bonus_recharge: expend 1 rage (no action) to restore early
description: Creatures of your choice in a 30-ft. Emanation make a Wisdom save (DC 8 + Str mod + Prof.) or are Frightened for 1 minute (repeat save at end of each of their turns).

<!-- Excluded: Mindless Rage (passive Condition immunity while Raging), Frenzy (automatic extra damage
     on first Reckless Attack hit each turn while Raging — fixed damage type, no decision point). -->

---

### Subclass: Path of the Wild Heart

## Rage of the Wilds — Eagle
action_type: bonus_action   # no resource — unlimited while Raging; free the instant you activate Rage, costs a full Bonus Action on later turns
subclass: wild_heart
min_level: 3
description: Choose Eagle when you activate Rage (alternatives: Bear — passive Resistance to most damage types; Wolf — passive Advantage for allies attacking enemies near you). With Eagle active, take the Disengage and Dash actions as part of the Bonus Action used to activate Rage; on later turns while still Raging, spend a Bonus Action to take both actions again.

## Power of the Wilds — Ram
action_type: free_action   # no resource — unlimited while Raging, triggered on a melee hit
subclass: wild_heart
min_level: 14
description: Choose Ram when you activate Rage (alternatives: Falcon — passive Fly Speed; Lion — passive Disadvantage imposed on nearby enemies). With Ram active and Raging, on a melee hit you may give a Large-or-smaller target the Prone condition.

<!-- Excluded: Animal Speaker / Nature Speaker (unlimited Ritual spellcasting, no resource — same treatment
     as unlimited-use features elsewhere), Aspect of the Wilds (passive choice changeable on Long Rest,
     no combat action), Bear/Wolf (Rage of the Wilds) and Falcon/Lion (Power of the Wilds) options
     (passive-only benefits, covered as alternatives in the descriptions above). -->

---

### Subclass: Path of the World Tree

## Life-Giving Force
action_type: free_action   # no resource — unlimited, requires Rage active
subclass: world_tree
min_level: 3
description: At the start of each of your turns while Raging, choose another creature within 10 ft. to gain Temporary HP equal to a number of d6s (equal to your Rage Damage bonus) rolled together.

## Branches of the Tree
action_type: reaction   # no resource — unlimited, requires Rage active
subclass: world_tree
min_level: 6
description: When a creature you can see starts its turn within 30 ft. of you, teleport it to a nearby unoccupied space (Strength save negates) and reduce its Speed to 0 until the end of the current turn.

## Battering Roots
action_type: free_action   # no resource — unlimited, triggered on a hit with a Heavy/Versatile melee weapon
subclass: world_tree
min_level: 10
description: When you hit with a Heavy or Versatile melee weapon (reach +10 ft. on your turn), activate the Push or Topple mastery property in addition to a different mastery property you're using.

## Travel Along the Tree
action_type: bonus_action   # no resource — unlimited, requires Rage active; also triggers free when you activate Rage
subclass: world_tree
min_level: 14
description: Teleport up to 60 ft. to an unoccupied space you can see.

## Travel Along the Tree — Extended Range
action_type: bonus_action
resource_key: travel_along_tree_extended
subclass: world_tree
min_level: 14
max_uses: 1
rest_type: per_rage   # resets each time you activate Rage, not tied to a Short/Long Rest
description: Same teleport as above, but range extends to 150 ft. and you can bring up to 6 willing creatures within 10 ft. of you.

<!-- Excluded: Vitality Surge (Temp HP on Rage activation — automatic, no decision; folded into Rage). -->

---

### Subclass: Path of the Zealot

## Divine Fury
action_type: free_action   # no resource — once per turn, automatic on the first hit while Raging; damage type is a choice
subclass: zealot
min_level: 3
description: The first creature you hit each turn while Raging takes extra 1d6 + half Barbarian level (round down) Necrotic or Radiant damage (your choice each time).

## Warrior of the Gods
action_type: bonus_action
resource_key: warrior_of_the_gods_dice
subclass: zealot
min_level: 3
max_uses: 4          # d12s; increases to 5 at lvl 6, 6 at lvl 12, 7 at lvl 17
die_size: d12
rest_type: long regain all
description: Expend any number of dice from the pool, roll them, and regain that many HP.

## Fanatical Focus
action_type: free_action   # triggered on a failed save while Raging
resource_key: fanatical_focus
subclass: zealot
min_level: 6
max_uses: 1
rest_type: per_rage   # once per active Rage, not tied to a Short/Long Rest
description: Reroll a failed saving throw with a bonus equal to your Rage Damage bonus. You must use the new roll.

## Zealous Presence
action_type: bonus_action
resource_key: zealous_presence
subclass: zealot
min_level: 10
max_uses: 1
rest_type: long
bonus_recharge: expend 1 rage (no action) to restore early
description: Up to 10 creatures of your choice within 60 ft. gain Advantage on attack rolls and saving throws until the start of your next turn.

## Rage of the Gods
action_type: free_action   # triggered when you activate Rage; grants a temporary form rather than costing a separate action
resource_key: rage_of_the_gods
subclass: zealot
min_level: 14
max_uses: 1
rest_type: long
description: When you activate Rage, assume a divine warrior form for 1 minute (or until you drop to 0 HP) — Fly Speed equal to your Speed (can hover), Resistance to Necrotic, Psychic, and Radiant damage.

## Rage of the Gods — Revivification
action_type: reaction
consumes_resource: rage   # spends a Rage use, not a separate charge — no new CharacterResource row
subclass: zealot
min_level: 14
description: While in Rage of the Gods form, when a creature within 30 ft. would drop to 0 HP, expend a use of Rage to instead set its HP to your Barbarian level.
