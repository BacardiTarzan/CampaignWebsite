# FIGHTER Level-Up Wizard

**Hit Die:** d10 (average: 6)
**Spellcasting:** Eldritch Knight subclass only (Intelligence-based Wizard spells)

---

## Universal Steps (every level)
1. **HP:** PROMPT roll d10 or take 6 + Con modifier → UPDATE `hp.maximum`
2. **Proficiency Bonus:** AUTO update at levels 5/9/13/17
3. **Second Wind Uses:** AUTO update from class table
4. **Weapon Mastery count:** AUTO update from class table

---

## Level 1 — Starting Features

### Fighting Style
**PROMPT:** "Choose a Fighting Style feat:"
- List all Fighting Style feats from `reference_claude/feats/fighting-style/`.
- Apply chosen feat's effects immediately.
- **UPDATE** `character.feats` with chosen Fighting Style.
- Note: Fighter may replace their Fighting Style on each level-up (Champion subclass can have two at level 7).

### Second Wind
**AUTO:** Record feature. 2 uses. Bonus Action — regain 1d10 + Fighter level HP. Recharge: regain 1 on Short Rest, all on Long Rest. UPDATE `character.resources.secondWind.uses` = 2.

### Weapon Mastery
**PROMPT:** "Weapon Mastery: Choose 3 weapons you are proficient with. You can use the Mastery property of these weapons."
- UPDATE `character.weaponMastery` with the 3 chosen weapons.
- Player may change one choice on each Long Rest.

---

## Level 2 — Action Surge & Tactical Mind

### Action Surge
**AUTO:** Record feature. 1 use per Short/Long Rest. Gain one extra action (not Magic Action) on your turn. UPDATE `character.resources.actionSurge.uses` = 1.

### Tactical Mind
**AUTO:** Record feature. Can expend Second Wind uses to add 1d10 to a failed ability check (not expended if still fails).

---

## Level 3 — Fighter Subclass

**PROMPT:** "Choose your Fighter subclass (Martial Archetype):"
- **Battle Master** — Superiority Dice, tactical Maneuvers
- **Champion** — Critical hits on 19–20, Remarkable Athlete
- **Eldritch Knight** — Intelligence-based Wizard spellcasting
- **Psi Warrior** — Psionic Energy Dice, telekinetic powers

Apply subclass features immediately. UPDATE `character.subclass`.

#### Battle Master — Combat Superiority:
**PROMPT:** "Combat Superiority: Choose 3 Maneuvers from the Battle Master list."
- See `classes/fighter.md` → Battle Master Maneuvers list.
- **UPDATE** `character.features.battleMasterManeuvers`.
- **AUTO:** 4 Superiority Dice (d8). UPDATE `character.resources.superiorityDice`.

**PROMPT:** "Student of War: Choose 1 Artisan's Tool you gain proficiency with." UPDATE `character.proficiencies.tools`.
**PROMPT:** "Student of War: Choose 1 additional skill proficiency." UPDATE `character.skills`.

#### Champion — Improved Critical & Remarkable Athlete:
**AUTO:** Critical hit range becomes 19–20. UPDATE `character.features.criticalHitRange` = 19.
**AUTO:** Advantage on Initiative and Athletics checks. Record Remarkable Athlete.

#### Eldritch Knight — Spellcasting:
**AUTO:** Eldritch Knight gains Intelligence-based Wizard spellcasting (mostly Abjuration/Evocation).
**PROMPT:** "Eldritch Knight: Choose 2 cantrips from the Wizard cantrip list (one can be from any school; the other should be Abjuration or Evocation)." UPDATE `character.spells.cantrips`.
**PROMPT:** "Choose 3 level 1 spells from the Wizard spell list (at least 2 must be Abjuration or Evocation)." UPDATE `character.spells.known`.
- Eldritch Knight uses a separate spell progression table (see `classes/fighter.md`). Spell attack = Prof + Int modifier. Spell save DC = 8 + Prof + Int modifier.

**PROMPT:** "War Bond: Choose up to 2 weapons to bond with via ritual. You cannot be disarmed of them and can summon them as a Bonus Action." UPDATE `character.features.warBond`.

#### Psi Warrior — Psionic Power:
**AUTO:** Gain Psionic Energy Dice (d6). Count = Proficiency Bonus. UPDATE `character.resources.psionicEnergyDice`.
Record available powers: Protective Field, Psionic Strike, Telekinetic Movement.

---

## Level 4 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Strength or Dexterity increases: recalculate attack bonuses.

**Also at Level 4:**
- **AUTO:** Second Wind uses → 3. UPDATE `character.resources.secondWind.uses`.
- **AUTO:** Weapon Mastery count → 4.
- **PROMPT:** "Weapon Mastery: Choose 1 additional weapon." UPDATE `character.weaponMastery`.

---

## Level 5 — Extra Attack & Tactical Shift

### Extra Attack
**AUTO:** Record feature. Character attacks twice per Attack action. UPDATE `character.features.extraAttack`.

### Tactical Shift
**AUTO:** Record feature. When using Second Wind, can move up to half Speed without provoking Opportunity Attacks.

**Also at Level 5:**
- **AUTO:** Proficiency Bonus → +3. Recalculate all dependent values.

---

## Level 6 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 7 — Subclass Feature

#### Battle Master — Know Your Enemy:
**AUTO:** Record feature. Bonus Action to learn creature Immunities, Resistances, and Vulnerabilities. Uses = once per Long Rest or expend a Superiority Die.

**PROMPT:** "Choose 2 additional Maneuvers." UPDATE `character.features.battleMasterManeuvers`.
**AUTO:** Superiority Dice count → 5. UPDATE `character.resources.superiorityDice.count`.

#### Champion — Additional Fighting Style:
**PROMPT:** "Additional Fighting Style: Choose a second Fighting Style feat."
- List Fighting Style feats; exclude the one already chosen.
- Apply chosen feat's effects. UPDATE `character.feats`.

#### Eldritch Knight — War Magic:
**AUTO:** Record feature. Can replace one attack with a Wizard cantrip.
**AUTO:** Eldritch Knight gains additional spells per their progression. **PROMPT:** "Choose 1 additional Wizard spell (Abjuration or Evocation)." UPDATE `character.spells.known`.

#### Psi Warrior — Telekinetic Adept:
**AUTO:** Record Psi-Powered Leap and Telekinetic Thrust features.

---

## Level 8 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 9 — Indomitable & Tactical Master

### Indomitable
**AUTO:** Record feature. 1 use per Long Rest. Reroll a failed saving throw; add Fighter level to the reroll. UPDATE `character.resources.indomitable.uses` = 1.

### Tactical Master
**AUTO:** Record feature. Can replace a weapon's mastery property with Push, Sap, or Slow for one attack (only the listed options, not the weapon's own mastery).

**Also at Level 9:**
- **AUTO:** Proficiency Bonus → +4. Recalculate all dependent values.
- **AUTO:** Second Wind uses → 3 (already updated at 4; unchanged here per table).

Wait, checking the Fighter table again: Second Wind = 3 at level 4, stays 3 through level 9, then increases to 4 at level 10.

---

## Level 10 — Subclass Feature

#### Battle Master — Improved Combat Superiority:
**AUTO:** Superiority Die increases from d8 to d10. UPDATE `character.resources.superiorityDice.die` = d10.

**PROMPT:** "Choose 2 additional Maneuvers." UPDATE `character.features.battleMasterManeuvers`.

#### Champion — Heroic Warrior:
**AUTO:** Record feature. Gain Heroic Inspiration at the start of your turn if you don't already have it.

#### Eldritch Knight — Eldritch Strike:
**AUTO:** Record feature. Weapon hits impose Disadvantage on the target's next save vs. your spell.
**AUTO:** Eldritch Knight gains additional spells. **PROMPT:** "Choose 1 additional Wizard spell." UPDATE `character.spells.known`.

#### Psi Warrior — Guarded Mind:
**AUTO:** Record feature. Resistance to Psychic damage; expend Psionic Die to end Charmed/Frightened.

**Also at Level 10:**
- **AUTO:** Second Wind uses → 4. UPDATE `character.resources.secondWind.uses`.
- **AUTO:** Weapon Mastery count → 5. **PROMPT:** "Weapon Mastery: Choose 1 additional weapon." UPDATE `character.weaponMastery`.

---

## Level 11 — Two Extra Attacks

**AUTO:** Record upgrade. Character now attacks THREE times per Attack action (was two). UPDATE `character.features.extraAttack` = 2 additional attacks.

---

## Level 12 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 13 — Indomitable (2 uses) & Studied Attacks

**AUTO:** Indomitable uses → 2. UPDATE `character.resources.indomitable.uses`.

### Studied Attacks
**AUTO:** Record feature. Missing an attack roll against a creature gives Advantage on the next attack roll against that creature.

**Also at Level 13:**
- **AUTO:** Proficiency Bonus → +5. Recalculate all dependent values.

---

## Level 14 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 15 — Subclass Feature

#### Battle Master — Relentless:
**AUTO:** Record feature. Once per turn, roll 1d8 instead of expending a Superiority Die.

**PROMPT:** "Choose 2 additional Maneuvers." UPDATE `character.features.battleMasterManeuvers`.
**AUTO:** Superiority Dice count → 6. UPDATE `character.resources.superiorityDice.count`.

#### Champion — Superior Critical:
**AUTO:** Critical hit range extends to 18–20. UPDATE `character.features.criticalHitRange` = 18.

#### Eldritch Knight — Arcane Charge:
**AUTO:** Record feature. When using Action Surge, can teleport up to 30 ft. before or after the extra action.

#### Psi Warrior — Bulwark of Force:
**AUTO:** Record feature. Bonus Action — grant Half Cover to up to Psi Warrior level chosen creatures within 30 ft. for 1 minute.

---

## Level 16 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 16:**
- **AUTO:** Weapon Mastery count → 6. **PROMPT:** "Weapon Mastery: Choose 1 additional weapon." UPDATE `character.weaponMastery`.

---

## Level 17 — Action Surge (2 uses) & Indomitable (3 uses)

**AUTO:** Action Surge uses → 2. UPDATE `character.resources.actionSurge.uses`.
**AUTO:** Indomitable uses → 3. UPDATE `character.resources.indomitable.uses`.

**Also at Level 17:**
- **AUTO:** Proficiency Bonus → +6. Recalculate all dependent values.

---

## Level 18 — Subclass Feature (Capstone)

#### Battle Master — Ultimate Combat Superiority:
**AUTO:** Superiority Die increases from d10 to d12. UPDATE `character.resources.superiorityDice.die` = d12.

#### Champion — Survivor:
**AUTO:** Record feature. Advantage on Death Saving Throws. Regain HP = 5 + Con modifier at start of each turn while Bloodied (below half HP).

#### Eldritch Knight — Improved War Magic:
**AUTO:** Record upgrade. Can replace two attacks with a single level 1 or 2 Wizard spell.

#### Psi Warrior — Telekinetic Master:
**AUTO:** Always have Telekinesis prepared; can cast without slot or components. Record feature.

---

## Level 19 — Epic Boon

**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Recommended: Boon of Combat Prowess. Choose one:" [list Epic Boon feats]
Apply chosen feat. UPDATE `character.feats`.

**Also at Level 19:**
- **AUTO:** Second Wind uses → 4 (already at 4 since level 10).

---

## Level 20 — Three Extra Attacks

**AUTO:** Record upgrade. Character now attacks FOUR times per Attack action (was three). UPDATE `character.features.extraAttack` = 3 additional attacks.

---

## Eldritch Knight Spell Progression

Eldritch Knights are quarter-casters. Their spell slots are separate from the Fighter's main table:
- Level 3: 2 × level 1 slots; know 3 level 1 spells + 2 cantrips
- Level 4: 3 × level 1 slots; know 4 spells
- Level 7: gain level 2 slots; know 5 spells + 1 new choice
- Level 8: know 6 spells
- Level 10: know 7 spells + 1 new choice
- Level 11: gain level 2 slots (+1)
- Level 13: gain level 3 slots; know 8 spells + 1 new choice
- Level 14: know 9 spells
- Level 16: know 10 spells + 1 new choice
- Level 19: gain level 4 slots; know 11 spells + 1 new choice
- Level 20: know 13 spells

On each of these levels, **PROMPT** the player to choose new spells. Most spells must be Abjuration or Evocation; one spell at certain levels can be from any school. See PHB for exact restrictions.
