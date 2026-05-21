# Level-Up Guide: Barbarian, Ranger, Rogue, Cleric, Fighter

## For the Level-Up Wizard Overhaul

\---

### How to Read This Guide

Each entry is tagged with an **impact type** so the wizard knows what to do:

|Tag|Meaning|Wizard Action|
|-|-|-|
|🔢 **STAT CHANGE**|A number on the sheet changes automatically|Auto-update the field|
|🎯 **PLAYER CHOICE**|Player must pick from options|Prompt with UI input|
|📋 **DISPLAY ONLY**|Grants a new ability to show on sheet|Add to ability list|
|✨ **NEW SPELL SLOT**|Spell slots change|Update slot table|
|📖 **PICK SPELLS**|Player must select new prepared spells/cantrips|Spell picker prompt|
|⚔️ **PICK WEAPONS**|Player must choose weapon masteries|Weapon mastery picker|

\---

## Spell Slot Reference Tables

### Full Casters (Cleric)

|Class Level|1st|2nd|3rd|4th|5th|6th|7th|8th|9th|
|-|-|-|-|-|-|-|-|-|-|
|1|2|—|—|—|—|—|—|—|—|
|2|3|—|—|—|—|—|—|—|—|
|3|4|2|—|—|—|—|—|—|—|
|4|4|3|—|—|—|—|—|—|—|
|5|4|3|2|—|—|—|—|—|—|
|6|4|3|3|—|—|—|—|—|—|
|7|4|3|3|1|—|—|—|—|—|
|8|4|3|3|2|—|—|—|—|—|
|9|4|3|3|3|1|—|—|—|—|
|10|4|3|3|3|2|—|—|—|—|
|11|4|3|3|3|2|1|—|—|—|
|12|4|3|3|3|2|1|—|—|—|
|13|4|3|3|3|2|1|1|—|—|
|14|4|3|3|3|2|1|1|—|—|
|15|4|3|3|3|2|1|1|1|—|
|16|4|3|3|3|2|1|1|1|—|
|17|4|3|3|3|2|1|1|1|1|
|18|4|3|3|3|3|1|1|1|1|
|19|4|3|3|3|3|2|1|1|1|
|20|4|3|3|3|3|2|2|1|1|

\---

### Half Casters (Ranger)

Rangers begin casting at level 1. Max slot level is 5th.

|Class Level|1st|2nd|3rd|4th|5th|
|-|-|-|-|-|-|
|1|2|—|—|—|—|
|2|2|—|—|—|—|
|3|3|—|—|—|—|
|4|3|—|—|—|—|
|5|4|2|—|—|—|
|6|4|2|—|—|—|
|7|4|3|—|—|—|
|8|4|3|—|—|—|
|9|4|3|2|—|—|
|10|4|3|2|—|—|
|11|4|3|3|—|—|
|12|4|3|3|—|—|
|13|4|3|3|1|—|
|14|4|3|3|1|—|
|15|4|3|3|2|—|
|16|4|3|3|2|—|
|17|4|3|3|3|1|
|18|4|3|3|3|1|
|19|4|3|3|3|2|
|20|4|3|3|3|2|

\---

### One-Third Casters (Eldritch Knight, Arcane Trickster)

Both subclasses are one-third casters. Spell slots are keyed to the **subclass class level** (Fighter level for EK, Rogue level for AT). Spellcasting ability: **Intelligence** for both. Max slot level is 4th. Select from Wizard spell list.

**Spell list model:** Both use a **Spells Known** model — a fixed list that grows by one spell per level-up (per the Spells Known column). One spell on the list can be swapped for another whenever a class level is gained. This is different from the Cleric/Ranger prepared model where any spell from the full list can be swapped on a Long Rest.

**Cantrips:** both gain 2 cantrips from the wizard spell list. Increases to 3 at lvl 10. Arcane Trickster also gains Mage Hand as a bonus cantrip that doesn't count toward their 2 selected from the wizard spell list. **Make sure AT can't select Mage Hand from list.**



#### Arcane Trickster (Rogue level)

|Rogue Level|Cantrips|Spells Known|1st|2nd|3rd|4th|
|-|-|-|-|-|-|-|
|3|2|3|2|—|—|—|
|4|2|4|3|—|—|—|
|5|2|4|3|—|—|—|
|6|2|4|3|—|—|—|
|7|2|5|4|2|—|—|
|8|2|6|4|2|—|—|
|9|2|6|4|2|—|—|
|10|3|7|4|3|—|—|
|11|3|8|4|3|—|—|
|12|3|8|4|3|—|—|
|13|3|9|4|3|2|—|
|14|3|10|4|3|2|—|
|15|3|10|4|3|2|—|
|16|3|11|4|3|3|—|
|17|3|11|4|3|3|—|
|18|3|11|4|3|3|—|
|19|3|12|4|3|3|1|
|20|3|13|4|3|3|1|

#### Eldritch Knight (Fighter level)

|Fighter Level|Cantrips|Spells Known|1st|2nd|3rd|4th|
|-|-|-|-|-|-|-|
|3|2|3|2|—|—|—|
|4|2|4|3|—|—|—|
|5|2|4|3|—|—|—|
|6|2|4|3|—|—|—|
|7|2|5|4|2|—|—|
|8|2|6|4|2|—|—|
|9|2|6|4|2|—|—|
|10|3|7|4|3|—|—|
|11|3|8|4|3|—|—|
|12|3|8|4|3|—|—|
|13|3|9|4|3|2|—|
|14|3|10|4|3|2|—|
|15|3|10|4|3|2|—|
|16|3|11|4|3|3|—|
|17|3|11|4|3|3|—|
|18|3|11|4|3|3|—|
|19|3|12|4|3|3|1|
|20|3|13|4|3|3|1|

#### Multiclassing spell slot contribution

Per the 2024 PHB, available spell slots when multiclassing are determined by adding:

* **All** levels in Bard, Cleric, Druid, Sorcerer, and Wizard
* **Half** your levels (round up) in Paladin and Ranger
* **One-third** of your Fighter or Rogue levels (round down) if you have the Eldritch Knight or Arcane Trickster subclass

Then look up that combined total on the Multiclass Spellcaster table (same as the Full Caster table above).

**Example:** Fighter 9 (EK) / Cleric 3 = ⌊9÷3⌋ + 3 = 3 + 3 = 6 → use row 6 of the Full Caster table.

\---

\---

# BARBARIAN

**Hit Die:** d12 | **Save Proficiencies:** Strength, Constitution
**Armor:** Light, Medium, Shields | **Weapons:** Simple + Martial
**Starting Skills (choose 2):** Animal Handling, Athletics, Intimidation, Nature, Perception, Survival

\---

## Base Class — Level by Level

### Level 1 *(Character Creation)*

* 🔢 **STAT CHANGE** — HP = 12 + Con modifier
* 🔢 **STAT CHANGE** — Proficiency Bonus = +2
* 🔢 **STAT CHANGE** — Unarmored Defense: AC = 10 + Dex modifier + Con modifier *(alternate AC formula — flag as active if no armor equipped)*
* 📋 **DISPLAY ONLY** — **Rage:** 2 uses/Long Rest. Enter as Bonus Action (not in Heavy armor). Grants: Resistance to Bludgeoning/Piercing/Slashing damage; +2 Rage Damage bonus on Strength attacks; Advantage on Strength checks and saves. Cannot concentrate or cast spells. Lasts until end of next turn; extend by attacking an enemy, forcing an enemy to save, or spending a Bonus Action. Max 10 minutes per Rage.
* ⚔️ **PICK WEAPONS** — **Weapon Mastery:** Choose 2 Simple or Martial Melee weapons to use mastery properties for. Change one choice on each Long Rest.

### Level 2

* 🔢 **STAT CHANGE** — HP += d12 (or +7 fixed)
* 📋 **DISPLAY ONLY** — **Danger Sense:** Advantage on Dexterity saving throws (unless Incapacitated)
* 📋 **DISPLAY ONLY** — **Reckless Attack:** On your first attack of a turn, you can choose to attack recklessly — gain Advantage on Strength-based attack rolls until the start of your next turn, but attack rolls against you also have Advantage during that time.

### Level 3

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 🔢 **STAT CHANGE** — Rage uses: 2 → **3**
* 🎯 **PLAYER CHOICE** — **Barbarian Subclass:** Choose Path of the Berserker, Wild Heart, World Tree, or Zealot *(see subclass section — each grants immediate level 3 features)*
* 🎯 **PLAYER CHOICE** — **Primal Knowledge — Skill:** Gain proficiency in 1 additional skill from the Barbarian list: Animal Handling, Athletics, Intimidation, Nature, Perception, or Survival
* 📋 **DISPLAY ONLY** — **Primal Knowledge — Primal Rage:** While Raging, can make Acrobatics, Intimidation, Perception, Stealth, or Survival checks as Strength checks instead of their normal ability.

### Level 4

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* ⚔️ **PICK WEAPONS** — **Weapon Mastery** increases to 3 weapons *(add 1 new weapon choice)*
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement:** Choose the ASI feat (+2 to one stat, or +1 to two stats) or any other qualifying feat

### Level 5

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+3**
* 📋 **DISPLAY ONLY** — **Extra Attack:** Attack twice instead of once when you take the Attack action
* 🔢 **STAT CHANGE** — **Fast Movement:** Speed +10 ft. *(note: does not apply while wearing Heavy armor)*

### Level 6

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 🔢 **STAT CHANGE** — Rage uses: 3 → **4**
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 7

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 📋 **DISPLAY ONLY** — **Feral Instinct:** Advantage on Initiative rolls
* 📋 **DISPLAY ONLY** — **Instinctive Pounce:** When entering Rage as a Bonus Action, can also move up to half your Speed as part of that Bonus Action.

### Level 8

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 9

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+4**
* 🔢 **STAT CHANGE** — Rage Damage bonus: +2 → **+3**
* 📋 **DISPLAY ONLY** — **Brutal Strike:** When using Reckless Attack, you can forgo the Advantage on one Strength-based attack roll. If that attack hits, it deals +1d10 damage and you apply one of the following effects:

  * *Forceful Blow:* Push the target 15 ft. away and can immediately move up to 15 ft. toward them.
  * *Hamstring Blow:* Target's Speed is reduced to 0 until the start of its next turn.

### Level 10

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* ⚔️ **PICK WEAPONS** — **Weapon Mastery** increases to 4 weapons *(add 1 new weapon choice)*
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 11

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 📋 **DISPLAY ONLY** — **Relentless Rage:** When you drop to 0 HP while Raging and don't die outright, make a Con save (DC 10, +5 for each prior use since your last Short/Long Rest). On success, drop to HP = 2 × Barbarian level instead.

### Level 12

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 🔢 **STAT CHANGE** — Rage uses: 4 → **5**
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 13

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+5**
* 📋 **DISPLAY ONLY** — **Improved Brutal Strike:** You can now apply Brutal Strike even when keeping Advantage (no longer need to forgo it). Two additional options added:

  * *Staggering Blow:* Target has Disadvantage on attack rolls and saving throws until the start of your next turn.
  * *Sundering Blow:* The next attack roll made by another creature against the target before your next turn gains +1d10 damage on a hit (once per attack roll).

### Level 14

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 15

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 📋 **DISPLAY ONLY** — **Persistent Rage:** When you roll Initiative, you can regain all expended Rage uses (once per Long Rest). Additionally, your Rage now lasts 10 minutes without needing to extend it each round — it only ends if you gain the Unconscious condition or don Heavy armor.

### Level 16

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 🔢 **STAT CHANGE** — Rage Damage bonus: +3 → **+4**
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 17

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+6**
* 🔢 **STAT CHANGE** — Rage uses: 5 → **6**
* 📋 **DISPLAY ONLY** — **Improved Brutal Strike (upgrade):** Brutal Strike extra damage increases to 2d10. You can now apply two different Brutal Strike effects on the same hit.

### Level 18

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 📋 **DISPLAY ONLY** — **Indomitable Might:** If your total for a Strength check or Strength saving throw is lower than your Strength score, use your Strength score in place of the total.

### Level 19

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 🎯 **PLAYER CHOICE** — **Epic Boon:** Choose an Epic Boon feat or any other qualifying feat *(Boon of Irresistible Offense recommended)*

### Level 20

* 🔢 **STAT CHANGE** — HP += d12 (or +7)
* 🔢 **STAT CHANGE** — **Primal Champion:** Strength score +4 (max 25); Constitution score +4 (max 25). *(Recalculate: HP total, Unarmored Defense AC, attack modifiers, save modifiers, skill modifiers)*

\---

## Barbarian Subclasses

> \\\*\\\*Chosen at Level 3.\\\*\\\* Features at levels 3, 6, 10, 14.

\---

### Path of the Berserker

#### Level 3

* 📋 **DISPLAY ONLY** — **Frenzy:** When you use Reckless Attack while your Rage is active, the first target you hit on that turn with a Strength-based attack takes extra damage equal to \[Rage Damage bonus]d6 (e.g., 2d6 at level 3, growing with Rage Damage). Same damage type as the weapon or Unarmed Strike used.

#### Level 6

* 📋 **DISPLAY ONLY** — **Mindless Rage:** You have Immunity to the Charmed and Frightened conditions while Raging. If you're Charmed or Frightened when your Rage begins, those conditions end on you.

#### Level 10

* 📋 **DISPLAY ONLY** — **Retaliation:** When a creature within 5 ft. of you deals damage to you, you can use your Reaction to make one melee attack against that creature (weapon or Unarmed Strike).

#### Level 14

* 📋 **DISPLAY ONLY** — **Intimidating Presence:** As a Bonus Action, each creature of your choice within a 30-ft. Emanation must make a Wisdom saving throw (DC 8 + Strength modifier + Proficiency Bonus) or become Frightened of you for 1 minute. The Frightened creature repeats the save at the end of each of its turns, ending the effect on success. Once used, can't use again until you finish a Long Rest — unless you expend a Rage use (no action required) to restore it.

\---

### Path of the Wild Heart

#### Level 3

* 📋 **DISPLAY ONLY** — **Animal Speaker:** You can cast *Beast Sense* and *Speak with Animals* as Rituals. Wisdom is your spellcasting ability for these.
* 🎯 **PLAYER CHOICE** — **Rage of the Wilds:** Each time you activate Rage (not chosen once at level-up — chosen at the moment of activation), you choose one of the following animal spirit forms. Display all three on the sheet as in-session options:

  * *Bear Rage:* While Raging, gain Resistance to all damage types except Force and Psychic (in addition to the normal Bludgeoning/Piercing/Slashing Resistance).
  * *Eagle Rage:* While Raging, you can take the Disengage or Dash action as a Bonus Action. Opportunity Attacks against you have Disadvantage.
  * *Wolf Rage:* While Raging, allies have Advantage on melee attack rolls against any enemy that is within 5 ft. of you.

#### Level 6

* 🎯 **PLAYER CHOICE** — **Aspect of the Wilds:** Choose one of the following passive benefits. You can change your choice whenever you finish a Long Rest. *(Update the relevant speed field when a new choice is made — this is a Long Rest mechanic, out of scope for level-up wizard, so just record the initial choice at level-up.)*

  * *Owl:* Darkvision 60 ft., or +60 ft. if you already have Darkvision
  * *Panther:* Gain a Climb Speed equal to your Speed
  * *Salmon:* Gain a Swim Speed equal to your Speed

#### Level 10

* 📋 **DISPLAY ONLY** — **Nature Speaker:** You can cast *Commune with Nature* as a Ritual. Wisdom is your spellcasting ability.

#### Level 14

* 🎯 **PLAYER CHOICE** — **Power of the Wilds:** Choose one of the following. You can change your choice whenever you finish a Long Rest. *(Record initial choice at level-up; swap is a Long Rest mechanic.)*

  * *Falcon:* While Raging and not wearing Heavy armor, you gain a Fly Speed equal to your Speed.
  * *Lion:* While Raging, enemies within 5 ft. of you have Disadvantage on attack rolls against any creature other than you.
  * *Ram:* While Raging, when you hit a creature with a melee Strength attack, the target must make a Strength saving throw (DC 8 + Str mod + Prof.) or be knocked Prone.

\---

### Path of the World Tree

#### Level 3

* 📋 **DISPLAY ONLY** — **Vitality of the Tree:** When you activate your Rage, you gain Temporary Hit Points equal to your Barbarian level. While Raging, at the start of each of your turns, you can give Temporary Hit Points equal to your Rage Damage bonus to one creature you can see within 10 ft.

#### Level 6

* 📋 **DISPLAY ONLY** — **Branches of the Tree:** When a creature you can see starts its turn within 30 ft. of you while you're Raging, you can use your Reaction to force it to make a Strength saving throw (DC 8 + Str mod + Prof.). On failure, you teleport it to an unoccupied space within 5 ft. of you. On success, it is immune to this feature for 24 hours.

#### Level 10

* 📋 **DISPLAY ONLY** — **Battering Roots:** Your reach with melee attacks using Heavy or Versatile weapons increases by 10 ft. while Raging. Additionally, when you use a mastery property on such a weapon, you can also activate the Push or Topple property on the same attack (in addition to your chosen mastery).

#### Level 14

* 📋 **DISPLAY ONLY** — **Travel Along the Tree:** When you activate your Rage, you can teleport up to 60 ft. to an unoccupied space you can see. Additionally, once per turn while Raging, you can use a Bonus Action to teleport up to 60 ft. Once per Rage, one of these teleports can extend to 150 ft. and you can bring up to 6 willing creatures you can see within 10 ft., depositing them in unoccupied spaces within 6 ft. of your destination.

\---

### Path of the Zealot

#### Level 3

* 🎯 **PLAYER CHOICE** — **Divine Fury — Damage Type:** Choose Necrotic or Radiant. While Raging, the first creature you hit on each of your turns takes extra damage of that type = 1d6 + half your Barbarian level (rounded down).
* 📋 **DISPLAY ONLY** — **Warrior of the Gods:** You have a pool of healing power represented by 4d12 healing dice (grows to 7d12 at level 17). As a Bonus Action, expend any number of dice and regain HP equal to the total rolled. Dice replenish on a Long Rest. *(The d12 count increase at level 17 should auto-update.)*

#### Level 6

* 📋 **DISPLAY ONLY** — **Fanatical Focus:** Once per Rage, when you fail a saving throw, you can reroll it with a bonus equal to your Rage Damage bonus. You must use the new roll.

#### Level 10

* 📋 **DISPLAY ONLY** — **Zealous Presence:** As a Bonus Action, unleash a battle cry. Up to 10 allies you choose within 60 ft. gain Advantage on attack rolls and saving throws until the start of your next turn. Once used, can't use again until you finish a Long Rest.

#### Level 14

* 📋 **DISPLAY ONLY** — **Rage of the Gods:** When you activate your Rage, you can also enter a divine warrior form that lasts for 1 minute or until your Rage ends. While in this form: gain a Fly Speed equal to your Speed; gain Resistance to Necrotic, Psychic, and Radiant damage; once per Rage, when a creature within 30 ft. of you drops to 0 HP, you can use your Reaction to expend a Rage use — that creature instead drops to 1 HP and regains 1 HP (it doesn't fall unconscious).

\---

\---

# RANGER

**Hit Die:** d10 | **Save Proficiencies:** Strength, Dexterity
**Armor:** Light, Medium, Shields | **Weapons:** Simple + Martial
**Starting Skills (choose 3):** Animal Handling, Athletics, Insight, Investigation, Nature, Perception, Stealth, Survival

> \\\*\\\*Spellcasting Ability:\\\*\\\* Wisdom | \\\*\\\*Focus:\\\*\\\* Druidic Focus
> \\\*\\\*Spell Slots:\\\*\\\* Use the Half Caster table above, keyed to Ranger class level.

\---

## Base Class — Level by Level

### Level 1 *(Character Creation)*

* 🔢 **STAT CHANGE** — HP = 10 + Con modifier
* 🔢 **STAT CHANGE** — Proficiency Bonus = +2
* 📋 **DISPLAY ONLY** — **Spellcasting:** Wisdom-based. Prepare a spell list; change 1 prepared spell per Long Rest. Use a Druidic Focus.
* ✨ **NEW SPELL SLOT** — Spell slots: 2× Level 1 *(per Half Caster table, Level 1)*
* 📖 **PICK SPELLS** — Choose 2 prepared Level 1 Ranger spells *(Hunter's Mark is always prepared via Favored Enemy and does not count against total)*
* 📋 **DISPLAY ONLY** — **Favored Enemy:** Hunter's Mark is always prepared. Cast it **2×** per Long Rest without expending a spell slot.
* ⚔️ **PICK WEAPONS** — **Weapon Mastery:** Choose 2 proficient weapons for mastery properties. Change one choice on each Long Rest.

### Level 2

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* *(No spell slot change — slots stay at 2× Level 1)*
* 📖 **PICK SPELLS** — Prepared spells increases to 3 *(choose 1 new Level 1 spell)*
* 🎯 **PLAYER CHOICE** — **Deft Explorer — Expertise:** Choose 1 skill proficiency you have; gain Expertise in it (double Proficiency Bonus on checks using that skill)
* 🎯 **PLAYER CHOICE** — **Deft Explorer — Languages:** Learn 2 languages of your choice
* 🎯 **PLAYER CHOICE** — **Fighting Style:** Choose a Fighting Style feat, or choose *Druidic Warrior* (learn 2 Druid cantrips, Wisdom-based, scalable by total character level)

  * If *Druidic Warrior* chosen: 📖 **PICK SPELLS** — choose 2 Druid cantrips

### Level 3

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* ✨ **NEW SPELL SLOT** — Spell slots: 3× Level 1
* 📖 **PICK SPELLS** — Prepared spells increases to 4 *(choose 1 new spell)*
* 🎯 **PLAYER CHOICE** — **Ranger Subclass:** Choose Beast Master, Fey Wanderer, Gloom Stalker, or Hunter *(see subclass section — grants immediate level 3 features)*

### Level 4

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 📖 **PICK SPELLS** — Prepared spells increases to 5 *(choose 1 new spell)*
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 5

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+3**
* 🔢 **STAT CHANGE** — Favored Enemy free casts: 2 → **3**
* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 2× Level 2
* 📖 **PICK SPELLS** — Prepared spells increases to 6 *(choose 1 new spell; Level 2 spells now available)*
* 📋 **DISPLAY ONLY** — **Extra Attack:** Attack twice when you take the Attack action

### Level 6

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🔢 **STAT CHANGE** — **Roving:** Speed +10 ft. (not in Heavy armor); gain Climb Speed = Speed; gain Swim Speed = Speed *(update all three movement values)*

### Level 7

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 3× Level 2
* 📖 **PICK SPELLS** — Prepared spells increases to 7 *(choose 1 new spell)*
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 8

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 9

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+4**
* 🔢 **STAT CHANGE** — Favored Enemy free casts: 3 → **4**
* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 3× Level 2, 2× Level 3
* 📖 **PICK SPELLS** — Prepared spells increases to 9 *(choose 2 new spells; Level 3 spells now available)*
* 🎯 **PLAYER CHOICE** — **Expertise:** Choose 2 more skill proficiencies to gain Expertise in

### Level 10

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 📋 **DISPLAY ONLY** — **Tireless:** Magic Action — give yourself Temp HP = 1d8 + Wisdom modifier (minimum 1). Uses = Wisdom modifier (min 1); recharge on Long Rest. Additionally, finishing a Short Rest reduces your Exhaustion level by 1.

### Level 11

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 3× Level 2, 3× Level 3
* 📖 **PICK SPELLS** — Prepared spells increases to 10 *(choose 1 new spell)*
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 12

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 13

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+5**
* 🔢 **STAT CHANGE** — Favored Enemy free casts: 4 → **5**
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/1 (Levels 1–4)
* 📖 **PICK SPELLS** — Prepared spells increases to 11 *(choose 1 new spell; Level 4 spells now available)*
* 📋 **DISPLAY ONLY** — **Relentless Hunter:** Taking damage cannot break your Concentration on Hunter's Mark.

### Level 14

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 📋 **DISPLAY ONLY** — **Nature's Veil:** As a Bonus Action, gain the Invisible condition until the end of your next turn. Uses = Wisdom modifier (min 1); recharge on Long Rest.

### Level 15

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/2 (Levels 1–4)
* 📖 **PICK SPELLS** — Prepared spells increases to 12 *(choose 1 new spell)*
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 16

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 17

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+6**
* 🔢 **STAT CHANGE** — Favored Enemy free casts: 5 → **6**
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/3/1 (Levels 1–5)
* 📖 **PICK SPELLS** — Prepared spells increases to 14 *(choose 2 new spells; Level 5 spells now available)*
* 📋 **DISPLAY ONLY** — **Precise Hunter:** You have Advantage on attack rolls against creatures marked by your Hunter's Mark.

### Level 18

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🔢 **STAT CHANGE** — **Feral Senses:** Gain Blindsight 30 ft.

### Level 19

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/3/2 (Levels 1–5)
* 📖 **PICK SPELLS** — Prepared spells increases to 15 *(choose 1 new spell)*
* 🎯 **PLAYER CHOICE** — **Epic Boon** (Epic Boon feat or qualifying feat; Boon of Dimensional Travel recommended)

### Level 20

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 📋 **DISPLAY ONLY** — **Foe Slayer:** The damage die of Hunter's Mark is now d10 instead of d6.

\---

## Ranger Subclasses

> \\\*\\\*Chosen at Level 3.\\\*\\\* Features at levels 3, 7, 11, 15.

\---

### Beast Master

#### Level 3

* 🎯 **PLAYER CHOICE** — **Primal Companion:** Choose a Beast of the Land, Sea, or Sky. It acts on your Initiative, Dodges unless commanded, and can be commanded as a Bonus Action to take any action. It uses your Proficiency Bonus. If it dies, you can spend an action and a spell slot (any level) during a Short or Long Rest to revive it at 1 HP.

#### Level 7

* 📋 **DISPLAY ONLY** — **Exceptional Training:** Your Beast companion can Dash, Disengage, Dodge, or Help as a Bonus Action on its turns. Its attacks can deal Force damage instead of their normal damage type.

#### Level 11

* 📋 **DISPLAY ONLY** — **Bestial Fury:** Your Beast companion can make two Strike attacks instead of one when commanded. When attacking a creature marked by your Hunter's Mark, it also deals extra Force damage equal to 1d6.

#### Level 15

* 📋 **DISPLAY ONLY** — **Share Spells:** When you cast a spell targeting only yourself, you can also affect your Beast companion if it's within 30 ft. of you.

\---

### Fey Wanderer

#### Level 3

* 📋 **DISPLAY ONLY** — **Dreadful Strikes:** Your weapon attacks deal an additional 1d4 Psychic damage once per turn (increases to 1d6 at Ranger level 11).
* 📋 **DISPLAY ONLY** — **Fey Wanderer Spells (always prepared, tagged \[domain], don't count against total):** These unlock automatically as you gain the spell slots to use them:

  * Ranger level 3: *Charm Person*
  * Ranger level 5: *Misty Step*
  * Ranger level 9: *Summon Fey*
  * Ranger level 13: *Dimension Door*
  * Ranger level 17: *Mislead*
* 🎯 **PLAYER CHOICE** — **Otherworldly Glamour — Skill:** Gain proficiency in one of: Deception, Performance, or Persuasion. Additionally, add your Wisdom modifier to all Charisma checks.
* 📋 **DISPLAY ONLY** — **Feywild Gift:** You receive a minor cosmetic boon from the Feywild (chosen from a DM-determined list; display as a flavor note on the character sheet).

#### Level 7

* 📋 **DISPLAY ONLY** — **Beguiling Twist:** You have Advantage on saving throws against the Charmed and Frightened conditions. Additionally, when you or a creature you can see within 120 ft. succeeds on a saving throw against being Charmed or Frightened, you can use your Reaction to redirect that condition to a different creature within 30 ft. of you (Wisdom save to resist).

#### Level 11

* 📋 **DISPLAY ONLY** — **Fey Reinforcements:** You can cast *Summon Fey* without expending material components. Additionally, once per Long Rest, you can cast it without expending a spell slot. When you do cast it this way, you can make it non-Concentration — it lasts up to 1 minute.

#### Level 15

* 📋 **DISPLAY ONLY** — **Misty Wanderer:** You can cast *Misty Step* without expending a spell slot. You can do this a number of times equal to your Wisdom modifier (min 1); recharge on Long Rest. When you cast it this way, you can bring one willing creature you can see within 5 ft. along with you.

\---

### Gloom Stalker

#### Level 3

* 📋 **DISPLAY ONLY** — **Dread Ambusher:** On your first turn in combat: your Speed increases by 10 ft.; you can make one Dreadful Strike attack (extra 2d6 Psychic damage on a hit, uses = Wisdom modifier per Long Rest); and your Initiative roll gains a bonus equal to your Wisdom modifier.
* 📋 **DISPLAY ONLY** — **Gloom Stalker Spells (always prepared, tagged \[domain]):**

  * Ranger level 3: *Disguise Self*
  * Ranger level 5: *Rope Trick*
  * Ranger level 9: *Fear*
  * Ranger level 13: *Greater Invisibility*
  * Ranger level 17: *Seeming*
* 🔢 **STAT CHANGE** — **Umbral Sight:** Gain Darkvision 60 ft. (or +60 ft. if you already have Darkvision). While in Darkness, you are Invisible to creatures that rely on Darkvision to see you.

#### Level 7

* 🎯 **PLAYER CHOICE** — **Iron Mind:** Gain proficiency in Wisdom saving throws. If you are already proficient in Wisdom saves, choose Intelligence or Charisma saves instead.

#### Level 11

* 📋 **DISPLAY ONLY** — **Stalker's Flurry:** Your Dreadful Strike damage increases to 2d8. Additionally, you can replace the Dreadful Strike with one of these effects (once per turn):

  * *Sudden Strike:* Make one additional attack against a different creature within 5 ft. of the original target.
  * *Mass Fear:* The target and each creature of your choice within 10 ft. must make a Wisdom saving throw (spell save DC) or become Frightened of you until the end of your next turn.

#### Level 15

* 📋 **DISPLAY ONLY** — **Shadowy Dodge:** When a creature makes an attack roll against you, you can use your Reaction to impose Disadvantage on that roll. If the attack misses, you immediately teleport up to 30 ft. to an unoccupied space you can see.

\---

### Hunter

#### Level 3

* 📋 **DISPLAY ONLY** — **Hunter's Lore:** While a creature is marked by your Hunter's Mark, you know whether it has any Immunities, Resistances, or Vulnerabilities — and if so, what they are.
* 🎯 **PLAYER CHOICE** — **Hunter's Prey:** Choose one option (can swap on Short or Long Rest):

  * *Colossus Slayer:* Once per turn when you hit a creature that is below half its HP maximum (Bloodied), deal extra 1d8 damage of the weapon's type.
  * *Horde Breaker:* Once per turn when you make an attack, you can make one additional attack with the same weapon against a different creature within 5 ft. of the first target and within your weapon's range.

#### Level 7

* 🎯 **PLAYER CHOICE** — **Defensive Tactics:** Choose one option (can swap on Short or Long Rest):

  * *Escape the Horde:* Opportunity Attacks against you have Disadvantage.
  * *Multiattack Defense:* When a creature hits you with an attack, all further attacks from that creature have Disadvantage until the start of your next turn.

#### Level 11

* 📋 **DISPLAY ONLY** — **Superior Hunter's Prey:** Once per turn when you deal the extra damage from Hunter's Mark, you can deal that same extra damage to a second creature of your choice within 30 ft. of the first target.

#### Level 15

* 📋 **DISPLAY ONLY** — **Superior Hunter's Defense:** When you take damage, you can use your Reaction to gain Resistance to all instances of that damage type until the end of the current turn.

\---

\---

# ROGUE

**Hit Die:** d8 | **Save Proficiencies:** Dexterity, Intelligence
**Armor:** Light | **Weapons:** Simple + Martial weapons with Finesse or Light property
**Tools:** Thieves' Tools
**Starting Skills (choose 4):** Acrobatics, Athletics, Deception, Insight, Intimidation, Investigation, Perception, Persuasion, Sleight of Hand, Stealth

\---

## Base Class — Level by Level

### Level 1 *(Character Creation)*

* 🔢 **STAT CHANGE** — HP = 8 + Con modifier
* 🔢 **STAT CHANGE** — Proficiency Bonus = +2
* 🎯 **PLAYER CHOICE** — **Expertise:** Choose 2 skill proficiencies; gain Expertise in them (double Proficiency Bonus)
* 📋 **DISPLAY ONLY** — **Sneak Attack:** Once per turn, deal extra damage with a Finesse or Ranged weapon when you have Advantage on the attack roll, OR when an ally is within 5 ft. of the target and you don't have Disadvantage. Extra damage = 1d6, scaling up each odd Rogue level (see table).
* 📋 **DISPLAY ONLY** — **Thieves' Cant:** Know the Thieves' Cant secret language and one additional language of your choice.
* ⚔️ **PICK WEAPONS** — **Weapon Mastery:** Choose 2 proficient weapons for mastery properties. Change one on each Long Rest.

**Sneak Attack Progression:**

|Rogue Level|Sneak Attack|
|-|-|
|1|1d6|
|3|2d6|
|5|3d6|
|7|4d6|
|9|5d6|
|11|6d6|
|13|7d6|
|15|8d6|
|17|9d6|
|19|10d6|

### Level 2

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 📋 **DISPLAY ONLY** — **Cunning Action:** On your turn, take one of the following as a Bonus Action: Dash, Disengage, or Hide.

### Level 3

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Sneak Attack: 1d6 → **2d6**
* 🎯 **PLAYER CHOICE** — **Rogue Subclass:** Choose Arcane Trickster, Assassin, Soulknife, or Thief *(see subclass section — each grants immediate level 3 features, including spellcasting for AT)*
* 📋 **DISPLAY ONLY** — **Steady Aim:** As a Bonus Action, give yourself Advantage on your next attack roll this turn. Requires that you haven't moved yet this turn; after using it, your Speed is 0 for the rest of the turn.

### Level 4

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 5

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+3**
* 🔢 **STAT CHANGE** — Sneak Attack: 2d6 → **3d6**
* 📋 **DISPLAY ONLY** — **Cunning Strike:** When you deal Sneak Attack damage, you can subtract dice from the Sneak Attack total (before rolling) to add one of the following effects. The Cunning Strike DC = 8 + Dexterity modifier + Proficiency Bonus.

  * *Poison (cost 1d6):* Target makes a Constitution save or gains the Poisoned condition for 1 minute. Repeats save at end of each of its turns. *(Requires a Poisoner's Kit on your person.)*
  * *Trip (cost 1d6):* Target makes a Dexterity save or falls Prone (Large or smaller only).
  * *Withdraw (cost 1d6):* Immediately after the attack, move up to half your Speed without provoking Opportunity Attacks.
* 📋 **DISPLAY ONLY** — **Uncanny Dodge:** When an attacker you can see hits you with an attack roll, use your Reaction to halve the attack's damage (round down).

### Level 6

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🎯 **PLAYER CHOICE** — **Expertise:** Choose 2 more skill proficiencies to gain Expertise in

### Level 7

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Sneak Attack: 3d6 → **4d6**
* 📋 **DISPLAY ONLY** — **Evasion:** When subjected to an effect that allows a Dexterity saving throw for half damage: on a success you take no damage; on a failure you take only half. Cannot use if Incapacitated.
* 📋 **DISPLAY ONLY** — **Reliable Talent:** When making an ability check using a skill or tool proficiency, treat any d20 roll of 9 or lower as a 10.

### Level 8

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 9

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+4**
* 🔢 **STAT CHANGE** — Sneak Attack: 4d6 → **5d6**
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 10

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 11

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Sneak Attack: 5d6 → **6d6**
* 📋 **DISPLAY ONLY** — **Improved Cunning Strike:** When dealing Sneak Attack damage, you can apply up to two Cunning Strike effects (paying the die cost for each).

### Level 12

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 13

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+5**
* 🔢 **STAT CHANGE** — Sneak Attack: 6d6 → **7d6**
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 14

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 📋 **DISPLAY ONLY** — **Devious Strikes:** Three new Cunning Strike options are added:

  * *Daze (cost 2d6):* Target makes a Constitution save or on its next turn it can only do one of the following: move, take an action, or take a Bonus Action.
  * *Knock Out (cost 6d6):* Target makes a Constitution save or gains the Unconscious condition for 1 minute or until it takes any damage. Repeats save at end of each of its turns.
  * *Obscure (cost 3d6):* Target makes a Dexterity save or gains the Blinded condition until the end of its next turn.

### Level 15

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Sneak Attack: 7d6 → **8d6**
* 🔢 **STAT CHANGE** — **Slippery Mind:** Gain proficiency in Wisdom saving throws AND Charisma saving throws *(add both to saving throw proficiency list)*

### Level 16

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 17

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+6**
* 🔢 **STAT CHANGE** — Sneak Attack: 8d6 → **9d6**
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 18

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 📋 **DISPLAY ONLY** — **Elusive:** Attack rolls against you can never have Advantage (unless you have the Incapacitated condition).

### Level 19

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Sneak Attack: 9d6 → **10d6**
* 🎯 **PLAYER CHOICE** — **Epic Boon** (Epic Boon feat or qualifying feat; Boon of the Night Spirit recommended)

### Level 20

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 📋 **DISPLAY ONLY** — **Stroke of Luck:** Once per Short or Long Rest — if you fail a D20 Test, you can treat the roll as a 20.

\---

## Rogue Subclasses

> \\\*\\\*Chosen at Level 3.\\\*\\\* Features at levels 3, 9, 13, 17.

\---

### Arcane Trickster

> \\\*\\\*Spellcasting Ability:\\\*\\\* Intelligence | \\\*\\\*Focus:\\\*\\\* Arcane Focus or spellbook
> \\\*\\\*Spell Slots:\\\*\\\* Use the AT Spells Known table above, keyed to Rogue class level.
> \\\*\\\*Model:\\\*\\\* Spells Known — learn one new spell per level-up (per the Spells Known column); swap one known spell whenever you gain a Rogue level.
> \\\*\\\*School Restriction:\\\*\\\* New spells must be Enchantment or Illusion, except at Rogue levels 8, 14, and 20 where any Wizard school is allowed.

#### Level 3

* 📋 **DISPLAY ONLY** — **Mage Hand Legerdemain:** You can cast Mage Hand as a Bonus Action, make the spectral hand Invisible, and use it to make Sleight of Hand checks as a Bonus Action at range.
* 🎯 **PLAYER CHOICE / SPELLCASTING SETUP** — **Spellcasting (Intelligence-based):**

  * ✨ **NEW SPELL SLOT** — Spell slots: 2× Level 1
  * 📖 **PICK SPELLS** — Gain **Mage Hand** cantrip (bonus, always known, doesn't count against total) + choose **2 cantrips** from the Wizard spell list
  * 📖 **PICK SPELLS** — Learn **3 spells** from the Wizard spell list (2 must be Enchantment or Illusion; 1 may be any school)

#### Level 4

* ✨ **NEW SPELL SLOT** — Spell slots: 3× Level 1
* 📖 **PICK SPELLS** — Spells Known increases to 4 *(learn 1 new Enchantment or Illusion spell)*

#### Level 5

* *(No slot change — stays at 3× Level 1)*

#### Level 6

* *(No spell or slot change)*

#### Level 7

* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 2× Level 2
* 📖 **PICK SPELLS** — Spells Known increases to 5 *(learn 1 new spell; Level 2 spells now available; Enchantment/Illusion)*

#### Level 8

* *(No slot change — stays at 4/2)*
* 📖 **PICK SPELLS** — Spells Known increases to 6 *(learn 1 new spell — **free choice**, any Wizard school)*

#### Level 9 *(base Rogue feature + AT feature)*

* *(No slot change — stays at 4/2)*
* 📋 **DISPLAY ONLY** — **Magical Ambush:** When you cast a spell while you have the Invisible condition, targets have Disadvantage on their saving throws against that spell.

#### Level 10

* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 3× Level 2
* 📖 **PICK SPELLS** — Spells Known increases to 7 *(learn 1 new Enchantment or Illusion spell)*
* 📖 **PICK SPELLS** — Gain **3rd cantrip** *(choose 1 more from the Wizard spell list, any school)*

#### Level 11

* *(No slot change — stays at 4/3)*
* 📖 **PICK SPELLS** — Spells Known increases to 8 *(learn 1 new Enchantment or Illusion spell)*

#### Level 12

* *(No spell or slot change)*

#### Level 13 *(base Rogue feature + AT feature)*

* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 3× Level 2, 2× Level 3
* 📖 **PICK SPELLS** — Spells Known increases to 9 *(learn 1 new spell; Level 3 spells now available; Enchantment/Illusion)*
* 📋 **DISPLAY ONLY** — **Versatile Trickster:** When you use the Trip Cunning Strike option, you can also attempt to Trip a second creature within 5 ft. of your Mage Hand.

#### Level 14

* *(No slot change — stays at 4/3/2)*
* 📖 **PICK SPELLS** — Spells Known increases to 10 *(learn 1 new spell — **free choice**, any Wizard school)*

#### Level 15

* *(No spell or slot change)*

#### Level 16

* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 3× Level 2, 3× Level 3
* 📖 **PICK SPELLS** — Spells Known increases to 11 *(learn 1 new Enchantment or Illusion spell)*

#### Level 17 *(base Rogue feature + AT feature)*

* *(No slot change — stays at 4/3/3)*
* *(No spell count change this level)*
* 📋 **DISPLAY ONLY** — **Spell Thief:** When a creature casts a spell targeting you or including you in its area, use your Reaction to force the caster to make an Intelligence saving throw (DC 8 + Int mod + Prof.). On a failure, the spell has no effect on you and you steal it — you can cast it once within 8 hours using your spell slots. The stolen spell is unavailable to the caster for 8 hours.

#### Level 18

* *(No spell or slot change)*

#### Level 19

* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 3× Level 2, 3× Level 3, 1× Level 4
* 📖 **PICK SPELLS** — Spells Known increases to 12 *(learn 1 new spell; Level 4 spells now available; Enchantment/Illusion)*

#### Level 20

* *(No slot change — stays at 4/3/3/1)*
* 📖 **PICK SPELLS** — Spells Known increases to 13 *(learn 1 new spell — **free choice**, any Wizard school)*

### Assassin

#### Level 3

* 🔢 **STAT CHANGE** — **Assassinate:** Gain Advantage on Initiative rolls. *(Display as a passive initiative bonus note.)*
* 📋 **DISPLAY ONLY** — **Assassinate — Combat:** During the first round of combat, you have Advantage on attack rolls against any creature that hasn't taken a turn yet. Any hit during that first round that also qualifies for Sneak Attack deals extra damage equal to your Rogue level on top of the normal Sneak Attack damage.
* 🎯 **PLAYER CHOICE** — **Assassin's Tools:** Gain a Disguise Kit and a Poisoner's Kit with proficiency in both. *(Add both tool proficiencies to the sheet.)*

#### Level 9

* 📋 **DISPLAY ONLY** — **Infiltration Expertise:** After observing a person for at least 1 hour, you can perfectly mimic their voice and handwriting. Additionally, using your Steady Aim feature no longer reduces your Speed to 0.

#### Level 13

* 📋 **DISPLAY ONLY** — **Envenom Weapons:** When you use the Poison Cunning Strike option, the poison deals an additional 2d6 Poison damage each time the target fails its saving throw against the poison. This extra damage ignores Resistance to Poison damage.

#### Level 17

* 📋 **DISPLAY ONLY** — **Death Strike:** When you hit with a Sneak Attack on the first round of combat, the target must make a Constitution saving throw (DC 8 + Dex mod + Prof. Bonus). On a failure, the attack's damage is doubled (including Sneak Attack). You can use this feature only once per combat.

\---

### Soulknife

#### Level 3

* 📋 **DISPLAY ONLY** — **Psychic Blades:** Whenever you take the Attack action or make an Opportunity Attack, you can manifest one or two spectral blades from your mind. Each blade is a simple Melee weapon (1d6 Psychic, Finesse, Thrown 60/120 ft.); the blades vanish immediately after the attack, so they require no ammunition. As a Bonus Action immediately after the Attack action, you can manifest a second blade for an off-hand attack (1d4 Psychic, no ability modifier to damage unless negative). Blades can't be disarmed.
* 📋 **DISPLAY ONLY** — **Psionic Power:** Gain Psionic Energy Dice (d6 at level 3–10; d8 at 11–16; d12 at 17–20). Number of dice = Proficiency Bonus; regain all on Long Rest; regain 1 die on Short Rest when you use one (once per Short Rest). Three uses:

  * *Psi-Bolstered Knack:* After failing an ability check using a skill or tool you're proficient in, roll one Psionic die and add it to the result. If the check still fails, the die is not expended.
  * *Psychic Whispers:* As a Magic Action, expend one die and roll it — establish telepathic communication with up to 6 willing creatures you can see. The link lasts for hours equal to the die result. No verbal communication needed; works within 1 mile.

#### Level 9

* 📋 **DISPLAY ONLY** — **Soul Blades:**

  * *Homing Strikes:* If you miss with a Psychic Blade, expend one Psionic die and add the roll to the attack roll, potentially turning the miss into a hit.
  * *Psychic Teleportation:* As a Bonus Action, expend one Psionic die — manifest a Psychic Blade and hurl it at an unoccupied space you can see within 60 ft. You teleport to that space. The die result doesn't affect anything; it's the expend that matters.

#### Level 13

* 📋 **DISPLAY ONLY** — **Psychic Veil:** As a Magic Action, gain the Invisible condition for 1 hour. The condition ends early if you deal damage to a creature or force a creature to make a saving throw. Once used, can't use again until you finish a Long Rest — unless you expend a Psionic die (no action required) to restore it.

#### Level 17

* 📋 **DISPLAY ONLY** — **Rend Mind:** When you deal Sneak Attack damage to a creature using a Psychic Blade, you can force the target to make a Wisdom saving throw (DC 8 + Int mod + Prof. Bonus). On a failure, the target has the Stunned condition until the end of your next turn. Once used, can't use again until you finish a Long Rest — unless you expend 3 Psionic dice (no action required) to restore it.

\---

### Thief

#### Level 3

* 📋 **DISPLAY ONLY** — **Fast Hands:** As a Bonus Action, do one of the following: make a Dexterity (Sleight of Hand) check to pick a lock or disarm a trap with Thieves' Tools, or to pick a pocket; OR take the Utilize action; OR take the Magic action to use a magic item that requires that action.
* 🔢 **STAT CHANGE** — **Second-Story Work:** Gain a Climb Speed equal to your Speed. *(Update Climb Speed field.)* When determining how far you jump, use Dexterity instead of Strength.

#### Level 9

* 📋 **DISPLAY ONLY** — **Supreme Sneak:** New Cunning Strike option added:

  * *Stealth Attack (cost 1d6):* If you have the Invisible condition when you make the attack, using this option doesn't end that condition — provided you end your turn behind Three-Quarters Cover or Total Cover.

#### Level 13

* 📋 **DISPLAY ONLY** — **Use Magic Device:** Gain the following benefits:

  * *Attunement:* You can attune to up to 4 magic items at once (rather than the normal 3). *(Update attunement limit.)*
  * *Charges:* When you use a magic item property that expends charges, roll 1d6 — on a 6, the charges are not expended.
  * *Scrolls:* You can use any Spell Scroll, using Intelligence as your spellcasting ability. Cantrips and level 1 spells cast reliably. Level 2+ scrolls require an Arcana check (DC 10 + spell level); on failure the scroll is destroyed.

#### Level 17

* 📋 **DISPLAY ONLY** — **Thief's Reflexes:** You can take two full turns during the first round of any combat. You take your first turn at your normal Initiative, and your second turn at your Initiative − 10. You cannot take the second turn if you are surprised.

\---

\---

# CLERIC

**Hit Die:** d8 | **Save Proficiencies:** Wisdom, Charisma
**Armor:** Light, Medium, Shields | **Weapons:** Simple
**Starting Skills (choose 2):** History, Insight, Medicine, Persuasion, Religion

> \\\*\\\*Spellcasting Ability:\\\*\\\* Wisdom | \\\*\\\*Focus:\\\*\\\* Holy Symbol
> \\\*\\\*Spell Slots:\\\*\\\* Use the Full Caster table above, keyed to Cleric class level.
> \\\*\\\*Domain Spells:\\\*\\\* Automatically added when subclass is chosen (at level 3). Tagged \\\[domain]. Do not count against the prepared spell total. Unlock by tier as the character gains spell slots of that level.

\---

## Base Class — Level by Level

### Level 1 *(Character Creation)*

* 🔢 **STAT CHANGE** — HP = 8 + Con modifier
* 🔢 **STAT CHANGE** — Proficiency Bonus = +2
* 📋 **DISPLAY ONLY** — **Spellcasting:** Wisdom-based. Prepare from the full Cleric list; swap any number on each Long Rest. Use a Holy Symbol as a focus.
* ✨ **NEW SPELL SLOT** — Spell slots: 2× Level 1
* 📖 **PICK SPELLS** — Choose **3 cantrips** from the Cleric spell list
* 📖 **PICK SPELLS** — Choose **4 prepared Level 1 spells** from the Cleric spell list
* 🎯 **PLAYER CHOICE** — **Divine Order:** Choose one:

  * *Protector:* Gain proficiency with Martial weapons and Heavy armor training. *(Update weapon and armor proficiency fields.)*
  * *Thaumaturge:* Know 1 extra cantrip from the Cleric list *(choose it now)*; add Wisdom modifier as a bonus to Intelligence (Arcana) and Intelligence (Religion) checks.

### Level 2

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* ✨ **NEW SPELL SLOT** — Spell slots: 3× Level 1
* 📖 **PICK SPELLS** — Prepared spells increases to 5 *(choose 1 new spell)*
* 📋 **DISPLAY ONLY** — **Channel Divinity:** 2 uses; regain 1 on Short Rest, all on Long Rest. Starts with two options:

  * *Divine Spark:* Magic Action — point Holy Symbol at a creature within 30 ft. Roll 1d8 + Wisdom modifier. Either restore that many HP to the target, or deal Necrotic or Radiant damage (your choice) — target makes a Con save for half damage. Scales to 2d8 at level 7, 3d8 at level 13, 4d8 at level 18.
  * *Turn Undead:* Magic Action — each Undead of your choice within 30 ft. makes a Wisdom save. On failure: Frightened and Incapacitated for 1 minute, must flee. Ends early if the creature takes damage or you die.

### Level 3

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 2× Level 2
* 📖 **PICK SPELLS** — Prepared spells increases to 6; Level 2 spells now available
* 🎯 **PLAYER CHOICE** — **Cleric Subclass:** Choose Life Domain, Light Domain, Trickery Domain, or War Domain *(see subclass section — grants immediate level 3 features and auto-adds Domain Spells tagged \[domain])*

### Level 4

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 3× Level 2
* 📖 **PICK SPELLS** — Prepared spells increases to 7; choose **1 new cantrip** (for a total of 4 cantrips; does not count against Thaumaturge's extra)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 5

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+3**
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/2 (Levels 1–3)
* 📖 **PICK SPELLS** — Prepared spells increases to 9; Level 3 spells now available *(choose 2 new spells)*
* 📋 **DISPLAY ONLY** — **Sear Undead:** When you use Turn Undead, also deal Radiant damage to each Undead that fails its save — damage = Wisdom modifier × d8 (minimum 1d8).

### Level 6

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3 (Levels 1–3)
* 🔢 **STAT CHANGE** — Channel Divinity uses: 2 → **3**
* 📖 **PICK SPELLS** — Prepared spells increases to 10 *(choose 1 new spell)*
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 7

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/1 (Levels 1–4)
* 📖 **PICK SPELLS** — Prepared spells increases to 11; Level 4 spells now available *(choose 1 new spell)*
* 📋 **DISPLAY ONLY** — **Divine Spark** upgrades to 2d8 + Wisdom modifier
* 🎯 **PLAYER CHOICE** — **Blessed Strikes:** Choose one (permanent):

  * *Divine Strike:* Once on each of your turns when you hit with a weapon, deal +1d8 Necrotic or Radiant damage (your choice of type — also choose this now). *(Increases to 2d8 at level 14.)*
  * *Potent Spellcasting:* Add your Wisdom modifier to the damage of Cleric cantrips you cast. *(Gains a secondary effect at level 14.)*

### Level 8

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/2 (Levels 1–4)
* 📖 **PICK SPELLS** — Prepared spells increases to 12 *(choose 1 new spell)*
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 9

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+4**
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/3/1 (Levels 1–5)
* 📖 **PICK SPELLS** — Prepared spells increases to 14; Level 5 spells now available *(choose 2 new spells)*
* 📋 **DISPLAY ONLY** — **Divine Intervention:** As a Magic Action, cast any Cleric spell of Level 5 or lower without expending a spell slot or material components. Once per Long Rest.

### Level 10

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/3/2 (Levels 1–5)
* 📖 **PICK SPELLS** — Prepared spells increases to 15; choose **1 new cantrip** (for a total of 5)

### Level 11

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/3/2/1 (Levels 1–6)
* 📖 **PICK SPELLS** — Prepared spells increases to 16; Level 6 spells now available *(choose 1 new spell)*

### Level 12

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 13

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+5**
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/3/2/1/1 (Levels 1–7)
* 📖 **PICK SPELLS** — Prepared spells increases to 17; Level 7 spells now available *(choose 1 new spell)*
* 📋 **DISPLAY ONLY** — **Divine Spark** upgrades to 3d8 + Wisdom modifier
* 🎯 **SUBCLASS FEATURE** *(see subclass section — only Life, Light, and Trickery have a level 13 feature)*

### Level 14

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 📋 **DISPLAY ONLY** — **Improved Blessed Strikes:**

  * If *Divine Strike* was chosen: increases to +2d8 damage
  * If *Potent Spellcasting* was chosen: additionally, when you deal cantrip damage, you can give one creature you can see within 60 ft. Temp HP equal to 2× your Wisdom modifier

### Level 15

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/3/2/1/1/1 (Levels 1–8)
* 📖 **PICK SPELLS** — Prepared spells increases to 18; Level 8 spells now available *(choose 1 new spell)*

### Level 16

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 17

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+6**
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/3/2/1/1/1/1 (Levels 1–9)
* 📖 **PICK SPELLS** — Prepared spells increases to 19; Level 9 spells now available *(choose 1 new spell)*
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 18

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/3/3/1/1/1/1 (Levels 1–9)
* 🔢 **STAT CHANGE** — Channel Divinity uses: 3 → **4**
* 📖 **PICK SPELLS** — Prepared spells increases to 20; choose **1 new cantrip** (for a total of 5 from base, possibly more from Thaumaturge)
* 📋 **DISPLAY ONLY** — **Divine Spark** upgrades to 4d8 + Wisdom modifier

### Level 19

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/3/3/2/1/1/1 (Levels 1–9)
* 📖 **PICK SPELLS** — Prepared spells increases to 21 *(choose 1 new spell)*
* 🎯 **PLAYER CHOICE** — **Epic Boon** (Epic Boon feat or qualifying feat; Boon of Fate recommended)

### Level 20

* 🔢 **STAT CHANGE** — HP += d8 (or +5)
* ✨ **NEW SPELL SLOT** — Spell slots: 4/3/3/3/3/2/2/1/1 (Levels 1–9)
* 📖 **PICK SPELLS** — Prepared spells increases to 22 *(choose 1 new spell)*
* 📋 **DISPLAY ONLY** — **Greater Divine Intervention:** Divine Intervention can now select *Wish* as the spell cast. After use, it recharges after 2d4 Long Rests (not every Long Rest).

\---

## Cleric Subclasses

> \\\*\\\*Chosen at Level 3.\\\*\\\* Core feature levels: 3, 6, 17. Some domains have a level 13 feature.
> \\\*\\\*Domain Spells:\\\*\\\* Auto-added at level 3 with the \\\[domain] tag. They are always prepared and don't count against the Cleric's prepared spell total. They become castable as the character gains spell slots at each tier.

\---

### Life Domain

**Domain Spells (auto-add at level 3, tag \[domain]):**

|Unlocks at Cleric Level|Spells|
|-|-|
|3 (Level 1–2 slots)|*Aid*, *Bless*, *Cure Wounds*, *Lesser Restoration*|
|5 (Level 3 slots)|*Mass Healing Word*, *Revivify*|
|7 (Level 4 slots)|*Aura of Life*, *Death Ward*|
|9 (Level 5 slots)|*Greater Restoration*, *Mass Cure Wounds*|

#### Level 3

* 📋 **DISPLAY ONLY** — **Disciple of Life:** Whenever you cast a healing spell using a spell slot, that spell restores additional HP equal to 2 + the spell slot's level. (e.g., Cure Wounds with a Level 1 slot heals +3 HP.)
* 📋 **DISPLAY ONLY** — **Preserve Life:** Channel Divinity option — As a Magic Action, restore HP to any number of Bloodied (below half max HP) creatures you can see within 30 ft. Distribute up to 5× your Cleric level in HP among them; no single creature can regain more than half its HP maximum from this feature.

#### Level 6

* 📋 **DISPLAY ONLY** — **Blessed Healer:** When you cast a spell using a spell slot that restores HP to another creature, you also regain HP equal to 2 + the spell slot's level.

#### Level 17

* 📋 **DISPLAY ONLY** — **Supreme Healing:** When you would roll dice to restore HP with a spell, treat every die result as its maximum value instead (e.g., a d6 counts as 6).

\---

### Light Domain

**Domain Spells (auto-add at level 3, tag \[domain]):**

|Unlocks at Cleric Level|Spells|
|-|-|
|3|*Burning Hands*, *Faerie Fire*, *Scorching Ray*, *See Invisibility*|
|5|*Daylight*, *Fireball*|
|7|*Arcane Eye*, *Wall of Fire*|
|9|*Flame Strike*, *Scrying*|

#### Level 3

* 📋 **DISPLAY ONLY** — **Radiance of the Dawn:** Channel Divinity option — As a Magic Action, emit a flash of sunlight in a 30-ft. Emanation. Any magical Darkness in the area is dispelled. Each creature in the area that you choose must make a Constitution saving throw (spell save DC). On a failed save, the creature takes Radiant damage equal to 2d10 + your Cleric level. On a successful save, it takes half as much damage.
* 📋 **DISPLAY ONLY** — **Warding Flare:** When a creature you can see (within 30 ft.) makes an attack roll against you or another creature, use your Reaction to impose Disadvantage on that roll. Uses = Wisdom modifier (min 1); recharge on Long Rest.

#### Level 6

* 📋 **DISPLAY ONLY** — **Improved Warding Flare:** Warding Flare now recharges on a Short or Long Rest (instead of only Long Rest). Additionally, when you use it to protect another creature, that creature gains Temporary HP equal to 2d6 + your Wisdom modifier.

#### Level 17

* 📋 **DISPLAY ONLY** — **Corona of Light:** As a Magic Action, emit a sunlight aura (60-ft. radius bright light, 30-ft. dim beyond that) for 1 minute. While active, any enemy that starts its turn in the bright light has Disadvantage on saving throws against your Radiance of the Dawn and any spells that deal Fire or Radiant damage. You can end it early as a Bonus Action.

\---

### Trickery Domain

**Domain Spells (auto-add at level 3, tag \[domain]):**

|Unlocks at Cleric Level|Spells|
|-|-|
|3|*Charm Person*, *Disguise Self*, *Invisibility*, *Pass without Trace*|
|5|*Hypnotic Pattern*, *Nondetection*|
|7|*Confusion*, *Dimension Door*|
|9|*Dominate Person*, *Modify Memory*|

#### Level 3

* 📋 **DISPLAY ONLY** — **Blessing of the Trickster:** As a Magic Action, grant Advantage on Dexterity (Stealth) checks to yourself or one willing creature you touch. This lasts until you use it again or finish a Long Rest.
* 📋 **DISPLAY ONLY** — **Invoke Duplicity:** Channel Divinity option — As a Magic Action, create an illusory duplicate within 30 ft. that lasts for 1 minute or until you end it. While active: you can cast spells as though you were in its space; you have Advantage on attack rolls against creatures within 5 ft. of it; as a Bonus Action, move it up to 30 ft.

#### Level 6

* 📋 **DISPLAY ONLY** — **Trickster's Transposition:** When you move your Invoke Duplicity illusion, you can teleport to swap places with it (ending up where it was, the duplicate ending up where you were).

#### Level 13 *(this domain has a level 13 feature)*

* 📋 **DISPLAY ONLY** — *(No level 13 feature in the 2024 SRD for Trickery Domain — confirm from PHB if one was added. Record as "No feature at level 13" for now.)*

#### Level 17

* 📋 **DISPLAY ONLY** — **Improved Duplicity:** Your Invoke Duplicity illusion also grants Advantage on attack rolls to allies against creatures within 5 ft. of it. Additionally, when the duplicate ends (time expiring or you choosing to end it), one creature of your choice within 5 ft. of it regains HP equal to your Cleric level.

\---

### War Domain

**Domain Spells (auto-add at level 3, tag \[domain]):**

|Unlocks at Cleric Level|Spells|
|-|-|
|3|*Guiding Bolt*, *Magic Weapon*, *Shield of Faith*, *Spiritual Weapon*|
|5|*Crusader's Mantle*, *Spirit Guardians*|
|7|*Fire Shield*, *Freedom of Movement*|
|9|*Hold Monster*, *Steel Wind Strike*|

#### Level 3

* 📋 **DISPLAY ONLY** — **Guided Strike:** Channel Divinity option — When you or an ally you can see makes an attack roll, use your Reaction to grant a +10 bonus to that roll (applied before the outcome is determined).
* 📋 **DISPLAY ONLY** — **War Priest:** After taking the Attack action, you can use a Bonus Action to make one additional weapon attack or Unarmed Strike. Uses = Wisdom modifier (min 1); recharge on Short or Long Rest.

#### Level 6

* 📋 **DISPLAY ONLY** — **War God's Blessing:** You can use Channel Divinity to cast *Shield of Faith* or *Spiritual Weapon* without expending a spell slot. When cast this way, the spell doesn't require Concentration and lasts 1 minute.

#### Level 17

* 📋 **DISPLAY ONLY** — **Avatar of Battle:** You gain Resistance to Bludgeoning, Piercing, and Slashing damage from nonmagical attacks.

\---

\---

# FIGHTER

**Hit Die:** d10 | **Save Proficiencies:** Strength, Dexterity
**Armor:** All armor + Shields | **Weapons:** Simple + Martial
**Starting Skills (choose 2):** Acrobatics, Animal Handling, Athletics, History, Insight, Intimidation, Perception, Persuasion, Survival

\---

## Base Class — Level by Level

### Level 1 *(Character Creation)*

* 🔢 **STAT CHANGE** — HP = 10 + Con modifier
* 🔢 **STAT CHANGE** — Proficiency Bonus = +2
* 🎯 **PLAYER CHOICE** — **Fighting Style:** Choose a Fighting Style feat. *(Can be replaced with a different Fighting Style feat each time you gain a Fighter level.)*
* 📋 **DISPLAY ONLY** — **Second Wind:** As a Bonus Action, regain HP = 1d10 + Fighter level. 2 uses; regain 1 on Short Rest, all on Long Rest. Uses scale with level (see table below).
* ⚔️ **PICK WEAPONS** — **Weapon Mastery:** Choose 3 weapons (Simple or Martial) for mastery properties. Change one choice on each Long Rest.

**Second Wind Uses by Level:**

|Fighter Level|Uses|
|-|-|
|1–3|2|
|4–9|3|
|10–19|4|

### Level 2

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 📋 **DISPLAY ONLY** — **Action Surge:** On your turn, take one additional action (not the Magic action). 1 use per Short or Long Rest. *(Increases to 2 uses at level 17, but still only 1 per turn.)*
* 📋 **DISPLAY ONLY** — **Tactical Mind:** When you fail an ability check, expend one Second Wind use to roll 1d10 and add it to the total. If it still fails, the Second Wind use is not expended.

### Level 3

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🎯 **PLAYER CHOICE** — **Fighter Subclass:** Choose Battle Master, Champion, Eldritch Knight, or Psi Warrior *(see subclass section)*

### Level 4

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🔢 **STAT CHANGE** — Second Wind uses: 2 → **3**
* ⚔️ **PICK WEAPONS** — **Weapon Mastery** increases to 4 weapons *(add 1 new weapon choice)*
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 5

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+3**
* 📋 **DISPLAY ONLY** — **Extra Attack:** Attack twice per Attack action
* 📋 **DISPLAY ONLY** — **Tactical Shift:** When you activate Second Wind with a Bonus Action, you can also move up to half your Speed without provoking Opportunity Attacks.

### Level 6

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 7

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 8

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 9

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+4**
* 📋 **DISPLAY ONLY** — **Indomitable:** When you fail a saving throw, reroll it and add your Fighter level to the result; you must use the new roll. 1 use per Long Rest. *(Scales to 2 at level 13, 3 at level 17.)*
* 📋 **DISPLAY ONLY** — **Tactical Master:** When you attack with a weapon whose mastery property you can use, you can replace that property with Push, Sap, or Slow for that specific attack.

### Level 10

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🔢 **STAT CHANGE** — Second Wind uses: 3 → **4**
* ⚔️ **PICK WEAPONS** — **Weapon Mastery** increases to 5 weapons *(add 1 new weapon choice)*
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 11

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 📋 **DISPLAY ONLY** — **Two Extra Attacks:** Now attack **three** times per Attack action

### Level 12

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 13

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+5**
* 🔢 **STAT CHANGE** — Indomitable uses: 1 → **2 per Long Rest**
* 📋 **DISPLAY ONLY** — **Studied Attacks:** When you miss an attack roll against a creature, you have Advantage on your next attack roll against that same creature before the end of your next turn.

### Level 14

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 15

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 16

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* ⚔️ **PICK WEAPONS** — **Weapon Mastery** increases to 6 weapons *(add 1 new weapon choice)*
* 🎯 **PLAYER CHOICE** — **Ability Score Improvement** (ASI or feat)

### Level 17

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🔢 **STAT CHANGE** — Proficiency Bonus = **+6**
* 🔢 **STAT CHANGE** — Action Surge: 1 → **2 uses per Short/Long Rest** *(still max 1 per turn)*
* 🔢 **STAT CHANGE** — Indomitable uses: 2 → **3 per Long Rest**

### Level 18

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🎯 **SUBCLASS FEATURE** *(see subclass section)*

### Level 19

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 🎯 **PLAYER CHOICE** — **Epic Boon** (Epic Boon feat or qualifying feat; Boon of Combat Prowess recommended)

### Level 20

* 🔢 **STAT CHANGE** — HP += d10 (or +6)
* 📋 **DISPLAY ONLY** — **Three Extra Attacks:** Now attack **four** times per Attack action

\---

## Fighter Subclasses

> \\\*\\\*Chosen at Level 3.\\\*\\\* Features at levels 3, 7, 10, 15, 18.

\---

### Battle Master

#### Level 3 — Combat Superiority + Student of War

* 🎯 **PLAYER CHOICE** — **Combat Superiority — Maneuvers:** Choose **3 Maneuvers** from the full list below. Maneuver save DC = 8 + Strength or Dexterity modifier (your choice, made at this level) + Proficiency Bonus. *(Present the full list excluding any already in use.)*
* 🔢 **STAT CHANGE** — **Superiority Dice:** Gain 4× d8. Recharge on Short or Long Rest.
* 🎯 **PLAYER CHOICE** — **Student of War:** Gain proficiency with 1 Artisan's Tool (player's choice) + 1 skill proficiency from the Fighter list.

**Complete Maneuver List (19 total):**

|Maneuver|Cost|Effect|
|-|-|-|
|Ambush|1 die|Add to Initiative or Stealth rolls|
|Bait and Switch|1 die|Swap places with adjacent ally; one of you gains AC bonus|
|Commander's Strike|1 die|Use Bonus Action to grant an ally an attack|
|Commanding Presence|1 die|Add to Intimidation, Performance, or Persuasion check|
|Disarming Attack|1 die|On hit: add to damage; target makes Str save or drops held item|
|Distracting Strike|1 die|On hit: add to damage; next attack against target has Advantage|
|Evasive Footwork|1 die|Add to AC while moving this turn|
|Feinting Attack|1 die|Bonus Action: Advantage on next attack vs. adjacent creature; add to damage on hit|
|Goading Attack|1 die|On hit: add to damage; target makes Wis save or has Disadvantage attacking anyone but you|
|Lunging Attack|1 die|+5 ft. reach on one attack; add to damage on hit|
|Maneuvering Attack|1 die|On hit: add to damage; ally can use Reaction to move half Speed without Opportunity Attacks|
|Menacing Attack|1 die|On hit: add to damage; target makes Wis save or becomes Frightened until end of your next turn|
|Parry|1 die|Reaction: reduce melee damage you take by die result + Dex modifier|
|Precision Attack|1 die|Add to one attack roll before outcome determined|
|Pushing Attack|1 die|On hit: add to damage; target makes Str save or is pushed 15 ft. away|
|Rally|1 die|Bonus Action: give one ally Temp HP = die + Cha modifier|
|Riposte|1 die|Reaction: when a creature misses you with melee attack, make one attack against it; add to damage|
|Sweeping Attack|1 die|On hit: if adjacent creature is within reach, deal die result damage to it too (no attack roll)|
|Tactical Assessment|1 die|Add to History, Insight, or Perception check|
|Trip Attack|1 die|On hit: add to damage; target makes Str save or falls Prone (if Large or smaller)|

#### Level 7

* 🎯 **PLAYER CHOICE** — **Maneuvers:** Learn **2 more Maneuvers** from the list above
* 🔢 **STAT CHANGE** — Superiority Dice: 4 → **5**
* 📋 **DISPLAY ONLY** — **Know Your Enemy:** As a Bonus Action, learn one of the following about a creature you can see within 30 ft.: its Immunities, Resistances, or Vulnerabilities. Once per Long Rest or expend one Superiority Die (no action required) to restore.

#### Level 10

* 🎯 **PLAYER CHOICE** — **Maneuvers:** Learn **2 more Maneuvers** from the list above
* 🔢 **STAT CHANGE** — Superiority Die size: d8 → **d10**

#### Level 15

* 🎯 **PLAYER CHOICE** — **Maneuvers:** Learn **2 more Maneuvers** from the list above
* 🔢 **STAT CHANGE** — Superiority Dice: 5 → **6**
* 📋 **DISPLAY ONLY** — **Relentless:** Once per turn when you use a Maneuver but have no Superiority Dice remaining, roll a d8 in place of a Superiority Die (the result doesn't add dice back to your pool).

#### Level 18

* 🔢 **STAT CHANGE** — Superiority Die size: d10 → **d12**

\---

### Champion

#### Level 3

* 🔢 **STAT CHANGE** — **Improved Critical:** Weapon attacks and Unarmed Strikes score a Critical Hit on a roll of **19 or 20** (instead of 20 only).
* 📋 **DISPLAY ONLY** — **Remarkable Athlete:** You have Advantage on Initiative rolls and on Strength (Athletics) checks. Immediately after you score a Critical Hit in combat, you can move up to half your Speed without provoking Opportunity Attacks.

#### Level 7

* 🎯 **PLAYER CHOICE** — **Additional Fighting Style:** Gain a second Fighting Style feat of your choice.

#### Level 10

* 📋 **DISPLAY ONLY** — **Heroic Warrior:** At the start of each of your turns during combat, if you don't already have Heroic Inspiration, you gain it.

#### Level 15

* 🔢 **STAT CHANGE** — **Superior Critical:** Now score a Critical Hit on a roll of **18, 19, or 20**.

#### Level 18

* 📋 **DISPLAY ONLY** — **Survivor:**

  * *Defy Death:* Advantage on Death Saving Throws; rolls of 18–20 on a Death Save count as a 20.
  * *Heroic Rally:* At the start of each of your turns, if you are Bloodied (below half max HP) and have at least 1 HP, regain HP = 5 + Constitution modifier.

\---

### Eldritch Knight

> \\\*\\\*Spellcasting Ability:\\\*\\\* Intelligence | \\\*\\\*Focus:\\\*\\\* Arcane Focus
> \\\*\\\*Spell Slots:\\\*\\\* Use the EK Spells Known table above, keyed to Fighter class level.
> \\\*\\\*Model:\\\*\\\* Spells Known — learn one new spell per level-up (per the Spells Known column); swap one known spell for another whenever you gain a Fighter level.
> \\\*\\\*School Restriction:\\\*\\\* New spells must be Abjuration or Evocation, except at Fighter levels 8, 14, and 20 where any Wizard school is allowed.

#### Level 3

* 🎯 **PLAYER CHOICE / SPELLCASTING SETUP** — **Spellcasting (Intelligence-based):**

  * ✨ **NEW SPELL SLOT** — Spell slots: 2× Level 1 *(slots begin at level 3, same as AT)*
  * 📖 **PICK SPELLS** — Gain **Mage Hand** cantrip (bonus, always known, doesn't count against total) + choose **2 cantrips** from the Wizard spell list
  * 📖 **PICK SPELLS** — Learn **3 spells** from the Wizard spell list (2 must be Abjuration or Evocation; 1 may be any school)
* 🎯 **PLAYER CHOICE** — **War Bond:** Perform a 1-hour ritual to bond with up to 2 weapons. Bonded weapons can't be disarmed. Summon a bonded weapon to your hand as a Bonus Action. Can bond with magic weapons.

#### Level 4

* ✨ **NEW SPELL SLOT** — Spell slots: 3× Level 1
* 📖 **PICK SPELLS** — Spells Known increases to 4 *(learn 1 new Abjuration or Evocation spell)*

#### Level 5

* *(No slot change — stays at 3× Level 1)*

#### Level 6

* *(No spell or slot change)*

#### Level 7 *(base Fighter feature + EK spellcasting update)*

* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 2× Level 2
* 📖 **PICK SPELLS** — Spells Known increases to 5 *(learn 1 new spell; Level 2 spells now available; Abjuration/Evocation)*
* 📋 **DISPLAY ONLY** — **War Magic:** When you take the Attack action, you can replace one of those attacks with casting a Wizard cantrip that has a casting time of an action.

#### Level 8

* *(No slot change — stays at 4/2)*
* 📖 **PICK SPELLS** — Spells Known increases to 6 *(learn 1 new spell — **free choice**, any Wizard school)*

#### Level 9

* *(No spell or slot change — stays at 4/2)*

#### Level 10 *(base Fighter feature + EK spellcasting update)*

* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 3× Level 2
* 📖 **PICK SPELLS** — Spells Known increases to 7 *(learn 1 new Abjuration or Evocation spell)*
* 📖 **PICK SPELLS** — Gain **3rd cantrip** *(choose 1 more from the Wizard spell list, any school)*
* 📋 **DISPLAY ONLY** — **Eldritch Strike:** When you hit a creature with a weapon attack, that creature has Disadvantage on the next saving throw it makes against a spell you cast before the end of your next turn.

#### Level 11

* *(No slot change — stays at 4/3)*
* 📖 **PICK SPELLS** — Spells Known increases to 8 *(learn 1 new Abjuration or Evocation spell)*

#### Level 12

* *(No spell or slot change)*

#### Level 13 *(base Fighter feature + EK spellcasting update)*

* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 3× Level 2, 2× Level 3
* 📖 **PICK SPELLS** — Spells Known increases to 9 *(learn 1 new spell; Level 3 spells now available; Abjuration/Evocation)*

#### Level 14

* *(No slot change — stays at 4/3/2)*
* 📖 **PICK SPELLS** — Spells Known increases to 10 *(learn 1 new spell — **free choice**, any Wizard school)*

#### Level 15 *(base Fighter feature + EK feature)*

* *(No slot change — stays at 4/3/2)*
* *(No spell count change this level)*
* 📋 **DISPLAY ONLY** — **Arcane Charge:** When you use Action Surge, you can also teleport up to 30 ft. to an unoccupied space you can see, either before or after the additional action.

#### Level 16

* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 3× Level 2, 3× Level 3
* 📖 **PICK SPELLS** — Spells Known increases to 11 *(learn 1 new Abjuration or Evocation spell)*

#### Level 17

* *(No spell or slot change)*

#### Level 18 *(base Fighter feature + EK feature)*

* *(No slot change — stays at 4/3/3)*
* *(No spell count change this level)*
* 📋 **DISPLAY ONLY** — **Improved War Magic:** When you take the Attack action, you can replace two attacks (instead of one) with a single Wizard spell of Level 1 or 2 that has a casting time of an action.

#### Level 19

* ✨ **NEW SPELL SLOT** — Spell slots: 4× Level 1, 3× Level 2, 3× Level 3, 1× Level 4
* 📖 **PICK SPELLS** — Spells Known increases to 12 *(learn 1 new spell; Level 4 spells now available; Abjuration/Evocation)*

#### Level 20

* *(No slot change — stays at 4/3/3/1)*
* 📖 **PICK SPELLS** — Spells Known increases to 13 *(learn 1 new spell — **free choice**, any Wizard school)*

\---

### Psi Warrior

#### Level 3

* 📋 **DISPLAY ONLY** — **Psionic Power:** Gain Psionic Energy Dice. Number of dice = Proficiency Bonus. Die size: d6 (levels 3–9), d10 (levels 10–17), d12 (levels 18–20). All dice recharge on Long Rest; once per Short Rest, regain 1 die after expending one. Three powers:

  * *Protective Field:* When you or a creature you can see within 30 ft. takes damage, use your Reaction and expend 1 die — reduce the damage by the die result + your Intelligence modifier.
  * *Psionic Strike:* After hitting with a weapon attack, expend 1 die as a free action — the target takes extra Force damage equal to the die result + your Intelligence modifier.
  * *Telekinetic Movement:* As a Magic Action, expend 1 die — target one Large or smaller loose object or willing creature within 30 ft. Move it up to 30 ft. in any direction. If it's a creature, it doesn't provoke Opportunity Attacks.

#### Level 7

* 📋 **DISPLAY ONLY** — **Telekinetic Adept:** Two new psionic options:

  * *Psi-Powered Leap:* As a Bonus Action (no die cost), gain a Fly Speed equal to 2× your Speed until the end of your turn.
  * *Telekinetic Thrust:* When you use Psionic Strike and the target fails a Strength saving throw (DC 8 + Int mod + Prof.), you can push the target up to 10 ft. away or knock it Prone.

#### Level 10

* 🔢 **STAT CHANGE** — Psionic Energy Die size: d6 → **d10**
* 📋 **DISPLAY ONLY** — **Guarded Mind:** Gain Resistance to Psychic damage. Additionally, if you start your turn with the Charmed or Frightened condition, expend a Psionic die (no action required) to end that condition on yourself.

#### Level 15

* 📋 **DISPLAY ONLY** — **Bulwark of Force:** As a Bonus Action, expend 1 Psionic die — choose up to your Intelligence modifier (min 1) creatures you can see within 30 ft. (including yourself). Those creatures gain Half Cover for 1 minute or until you're Incapacitated.

#### Level 18

* 🔢 **STAT CHANGE** — Psionic Energy Die size: d10 → **d12**
* 📋 **DISPLAY ONLY** — **Telekinetic Master:** You always have the *Telekinesis* spell prepared (doesn't require a spell slot or components when you cast it this way). While concentrating on *Telekinesis*, you can make one weapon attack as a Bonus Action on each of your turns.

\---

## Implementation Notes for the Wizard Developer

### Decisions that require UI prompts (summary)

|Class|Level|Decision|
|-|-|-|
|All|4, 8 (varies)|ASI or Feat picker|
|All|1|Weapon Mastery selections (2–3 weapons)|
|All|Various|Weapon Mastery additions when column increases|
|Barbarian|3|Subclass choice|
|Barbarian|3|Primal Knowledge skill (1 from Barb list)|
|Barbarian|3|*(Wild Heart only)* Rage of the Wilds — display all 3 options, in-session toggle|
|Barbarian|6|*(Wild Heart only)* Aspect of the Wilds — initial choice|
|Barbarian|14|*(Wild Heart only)* Power of the Wilds — initial choice|
|Barbarian|3|*(Zealot only)* Divine Fury damage type choice|
|Ranger|2|Deft Explorer: 1 skill for Expertise + 2 languages|
|Ranger|2|Fighting Style feat (or Druidic Warrior + 2 cantrips)|
|Ranger|9|Expertise: 2 more skills|
|Ranger|3|Subclass choice|
|Ranger|3|*(Hunter only)* Hunter's Prey choice|
|Ranger|7|*(Hunter only)* Defensive Tactics choice|
|Ranger|3|*(Beast Master only)* Companion type choice|
|Ranger|3|*(Fey Wanderer only)* Otherworldly Glamour skill|
|Ranger|7|*(Gloom Stalker only)* Iron Mind save proficiency|
|Rogue|1|Expertise: 2 skills|
|Rogue|6|Expertise: 2 more skills|
|Rogue|3|Subclass choice|
|Rogue|3|*(Assassin only)* Tool proficiencies (auto-grant both, but surface as confirmation)|
|Rogue|3|*(AT only)* Cantrip + spell selection + spellcasting setup|
|Cleric|1|Divine Order choice|
|Cleric|1|*(Thaumaturge only)* Extra cantrip pick|
|Cleric|3|Subclass choice|
|Cleric|7|Blessed Strikes choice (permanent)|
|Cleric|7|*(Divine Strike only)* Damage type choice (Necrotic or Radiant)|
|Fighter|1|Fighting Style feat|
|Fighter|3|Subclass choice|
|Fighter|3|*(Battle Master only)* 3 Maneuver picks + 1 Artisan's Tool + 1 skill|
|Fighter|7|*(Battle Master only)* 2 Maneuver picks|
|Fighter|10|*(Battle Master only)* 2 Maneuver picks|
|Fighter|15|*(Battle Master only)* 2 Maneuver picks|
|Fighter|7|*(Champion only)* 2nd Fighting Style|
|Fighter|3|*(Eldritch Knight only)* War Bond weapon(s) + spell + cantrip setup|
|Fighter|8, 14, 20|*(Eldritch Knight only)* Free-choice spell (any Wizard school)|

### Stat fields that change mid-class (common miss areas)

* **Proficiency Bonus** — changes at levels 5, 9, 13, 17 for all classes
* **Barbarian Rage Damage** — changes at levels 9, 16
* **Barbarian Rage uses** — changes at levels 3, 6, 12, 17
* **Barbarian Weapon Mastery count** — changes at levels 4, 10
* **Ranger Favored Enemy free casts** — changes at levels 5, 9, 13, 17
* **Cleric Channel Divinity uses** — changes at levels 6, 18
* **Cleric Divine Spark dice** — changes at levels 7, 13, 18
* **Rogue Sneak Attack** — increments every odd level
* **Fighter Second Wind uses** — changes at levels 4, 10
* **Fighter Weapon Mastery count** — changes at levels 4, 10, 16
* **Fighter Indomitable uses** — changes at levels 13, 17
* **Fighter attack count** — changes at levels 5 (2), 11 (3), 20 (4)
* **Battle Master Superiority Dice count** — changes at levels 7, 15
* **Battle Master Superiority Die size** — changes at levels 10, 18
* **Psi Warrior Psionic Die size** — changes at levels 10, 18
* **Arcane Trickster/EK Psionic Die size** — changes at levels 10–11, 17–18
* **Champion Critical Hit range** — changes at levels 3 (19–20), 15 (18–20)

