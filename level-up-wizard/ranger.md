# RANGER Level-Up Wizard

**Hit Die:** d10 (average: 6)
**Spellcasting:** Wisdom-based, half-caster, prepared from Ranger list
**See also:** `spellcasting.md` → Ranger section

---

## Universal Steps (every level)
1. **HP:** PROMPT roll d10 or take 6 + Con modifier → UPDATE `hp.maximum`
2. **Proficiency Bonus:** AUTO update at levels 5/9/13/17
3. **Spell Slots:** AUTO update from Half-Caster table
4. **Prepared Spells Max:** AUTO update from class table
5. **Favored Enemy Uses:** AUTO update from class table

---

## Level 1 — Starting Features

### Spellcasting
**AUTO:** Ranger is Wisdom-based. Spell attack = Prof + Wis modifier. Spell save DC = 8 + Prof + Wis modifier.
- **AUTO:** Prepared Spells max = 2 (from class table). UPDATE `character.preparedSpells.max`.
- **PROMPT:** "Choose 2 spells from the Ranger spell list to prepare." UPDATE `character.preparedSpells`.
- Druidic Focus is the spellcasting focus.
- **AUTO:** Spell slots at level 1: 2 × level 1 slots.
- **AUTO:** Hunter's Mark is always prepared (from Favored Enemy). Mark as always-prepared. UPDATE `character.preparedSpells`.

### Favored Enemy
**AUTO:** Record feature. Always have Hunter's Mark prepared (see above). 2 free casts per Long Rest. UPDATE `character.resources.favoredEnemy.uses` = 2.

### Weapon Mastery
**PROMPT:** "Weapon Mastery: Choose 2 weapons you are proficient with. You can use the Mastery property of these weapons."
- UPDATE `character.weaponMastery` with the 2 chosen weapons.
- Player may change these on each Long Rest.

---

## Level 2 — Deft Explorer & Fighting Style

### Deft Explorer
**PROMPT:** "Deft Explorer: Choose 1 skill to gain Expertise in (your proficiency bonus is doubled). You must already be proficient in the chosen skill."
- Show only skills the character is already proficient in.
- **UPDATE** chosen skill to `expertise` status. Recalculate its bonus.

**PROMPT:** "Deft Explorer: Choose 2 additional languages to learn."
- Show the languages list from `reference_claude/rules/languages.md`.
- **UPDATE** `character.languages` with the 2 chosen languages.

### Fighting Style
**PROMPT:** "Choose a Fighting Style feat:"
- List all Fighting Style feats from `reference_claude/feats/fighting-style/`.
- Additionally, Ranger may choose **Druidic Warrior**: Learn 2 Druid cantrips (Wisdom-based).
- Apply chosen feat's effects immediately.
- **UPDATE** `character.feats` with chosen Fighting Style.

If **Druidic Warrior**:
- **PROMPT:** "Druidic Warrior: Choose 2 cantrips from the Druid cantrip list." UPDATE `character.spells.cantrips`.

**Also at Level 2:**
- **AUTO:** Prepared Spells max → 3. Spell slots → 3 × level 1.

---

## Level 3 — Ranger Subclass

**PROMPT:** "Choose your Ranger subclass (Ranger Conclave):"
- **Beast Master** — summoned Beast companion that fights alongside you
- **Fey Wanderer** — Psychic damage on hits, Charisma checks bonus, Feywild Gift
- **Gloom Stalker** — Darkvision, extra damage on first round, Initiative bonus
- **Hunter** — choice-based offensive/defensive options

Apply subclass features immediately. UPDATE `character.subclass`.

#### Beast Master — Primal Companion:
**PROMPT:** "Primal Companion: Choose a Beast companion type:"
- **Beast of the Land** — terrestrial, Maul attack
- **Beast of the Sea** — aquatic, Force damage
- **Beast of the Sky** — flying, Shred attack
UPDATE `character.features.primalCompanion.type`.

#### Fey Wanderer — Dreadful Strikes & Otherworldly Glamour:
**AUTO:** Record Dreadful Strikes (+1d4 Psychic on weapon hits, once per turn).

**PROMPT:** "Otherworldly Glamour: Choose 1 skill to gain proficiency in from: Deception, Performance, or Persuasion."
- Only show options the character is NOT already proficient in.
- **UPDATE** `character.skills` with the chosen proficiency.

**PROMPT:** "Fey Wanderer Spells — Feywild Gift: Choose a Feywild Gift (a cosmetic trait gained from time in the Feywild, e.g. fey-touched eyes, flower growing from hair, etc. — no mechanical effect, just flavor)."
- **AUTO:** Always have Charm Person prepared. UPDATE `character.preparedSpells`.

#### Gloom Stalker — Dread Ambusher & Umbral Sight:
**AUTO:** Record Dread Ambusher feature. Initiative bonus = Wisdom modifier. UPDATE `character.initiative` to add Wis modifier bonus.
**AUTO:** Gain Darkvision 60 ft. (or +60 ft. if already have Darkvision). UPDATE `character.senses.darkvision`.
**AUTO:** Always have Disguise Self prepared. UPDATE `character.preparedSpells`.

#### Hunter — Hunter's Lore & Hunter's Prey:
**AUTO:** Record Hunter's Lore (learn Immunities, Resistances, Vulnerabilities of Hunter's Mark target).

**PROMPT:** "Hunter's Prey: Choose one of the following (you can swap on Short or Long Rest):"
- **Colossus Slayer** — deal extra 1d8 damage to Bloodied (below half HP) creatures once per turn
- **Horde Breaker** — once per turn, make an extra attack against another creature within 5 ft. of your current target
UPDATE `character.features.huntersPrey`.

**Also at Level 3:**
- **AUTO:** Prepared Spells max → 4. Spell slots → 3 × level 1.

---

## Level 4 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Wisdom increases: recalculate Spell Save DC, Spell Attack Bonus.
If Dexterity increases: recalculate AC, attack bonuses.

**Also at Level 4:**
- **AUTO:** Favored Enemy uses → 2 (unchanged). Prepared Spells max → 5.

---

## Level 5 — Extra Attack

### Extra Attack
**AUTO:** Record feature. Character attacks twice per Attack action. UPDATE `character.features.extraAttack`.

**Also at Level 5:**
- **AUTO:** Proficiency Bonus → +3. Recalculate all dependent values.
- **AUTO:** Favored Enemy uses → 3. UPDATE `character.resources.favoredEnemy.uses`.
- **AUTO:** Prepared Spells max → 6. Spell slots → 4/2 (gain level 2 slots).

---

## Level 6 — Roving

**AUTO:** Record feature. Speed +10 ft. (not while wearing Heavy armor). Gain Climb Speed and Swim Speed = Speed. UPDATE `character.speed`, `character.speed.climb`, `character.speed.swim`.

**Also at Level 6:**
- **AUTO:** Prepared Spells max → 6 (unchanged). Spell slots → 4/2 (unchanged).

---

## Level 7 — Subclass Feature

#### Beast Master (Exceptional Training):
**AUTO:** Record feature. Companion can Dash, Disengage, Dodge, or Help as Bonus Action; damage can be Force type.

#### Fey Wanderer (Beguiling Twist):
**AUTO:** Record feature. Advantage on saves vs. Charmed/Frightened; Reaction to redirect those conditions to another creature.

#### Gloom Stalker (Iron Mind):
**AUTO:** Record feature. Gain proficiency in Wisdom saves. (If already proficient, choose Intelligence or Charisma instead.)
- **CONDITION:** Check if Wisdom save already proficient.
- If yes: **PROMPT:** "Iron Mind: You already have Wisdom save proficiency. Choose Intelligence or Charisma saves to gain proficiency in instead." UPDATE `character.savingThrows`.
- If no: UPDATE `character.savingThrows.wisdom` = proficient.

#### Hunter (Defensive Tactics):
**PROMPT:** "Defensive Tactics: Choose one of the following (you can swap on Short or Long Rest):"
- **Escape the Horde** — Opportunity Attacks against you have Disadvantage
- **Multiattack Defense** — After first hit in a turn, further attacks against you have Disadvantage until next turn
UPDATE `character.features.defensiveTactics`.

**Also at Level 7:**
- **AUTO:** Prepared Spells max → 7. Spell slots → 4/3 (gain 1 level 2 slot).

---

## Level 8 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 8:**
- **AUTO:** Prepared Spells max → 7 (unchanged). Spell slots unchanged.

---

## Level 9 — Expertise (2nd)

**PROMPT:** "Expertise: Choose 2 more skill proficiencies to gain Expertise in (proficiency bonus doubled). You must already be proficient in the chosen skills."
- Show proficient skills that don't already have Expertise.
- **UPDATE** both chosen skills to `expertise` status.

**Also at Level 9:**
- **AUTO:** Proficiency Bonus → +4. Recalculate all dependent values.
- **AUTO:** Favored Enemy uses → 4. UPDATE `character.resources.favoredEnemy.uses`.
- **AUTO:** Prepared Spells max → 9. Spell slots → 4/3/2 (gain level 3 slots).

---

## Level 10 — Tireless

**AUTO:** Record feature. Bonus Action — gain Temp HP = 1d8 + Wisdom modifier. Uses = Wisdom modifier (min 1); recharge on Long Rest. UPDATE `character.resources.tireless.uses`.
Short Rests reduce Exhaustion by 1.

**Also at Level 10:**
- **AUTO:** Prepared Spells max → 9 (unchanged).

---

## Level 11 — Subclass Feature

#### Beast Master (Bestial Fury):
**AUTO:** Record upgrade. Beast's Strike can be used twice; deals extra Force damage against Hunter's Mark targets.

#### Fey Wanderer (Fey Reinforcements):
**AUTO:** Record feature. Cast Summon Fey without material components; once without a slot per Long Rest; can make it non-Concentration.

#### Gloom Stalker (Stalker's Flurry):
**AUTO:** Record upgrade. Dreadful Strike damage becomes 2d8; can cause Sudden Strike or Mass Fear (Wisdom save or Frightened).

#### Hunter (Superior Hunter's Prey):
**AUTO:** Record feature. Once per turn when dealing Hunter's Mark damage, also deal that extra damage to another creature within 30 ft.

**Also at Level 11:**
- **AUTO:** Favored Enemy uses → 4 (unchanged). Prepared Spells max → 10. Spell slots → 4/3/3 (gain 1 level 3 slot).

---

## Level 12 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 13 — Relentless Hunter

**AUTO:** Record feature. Concentration on Hunter's Mark cannot be broken by taking damage.

**Also at Level 13:**
- **AUTO:** Proficiency Bonus → +5. Recalculate all dependent values.
- **AUTO:** Favored Enemy uses → 5. UPDATE `character.resources.favoredEnemy.uses`.
- **AUTO:** Prepared Spells max → 11. Spell slots → 4/3/3/1 (gain level 4 slot).

---

## Level 14 — Nature's Veil

**AUTO:** Record feature. Bonus Action — gain Invisible condition until end of next turn. Uses = Wisdom modifier (min 1); recharge on Long Rest. UPDATE `character.resources.naturesVeil.uses`.

---

## Level 15 — Subclass Feature

#### Beast Master (Share Spells):
**AUTO:** Record feature. Self-targeting spells also affect your Beast companion within 30 ft.

#### Fey Wanderer (Misty Wanderer):
**AUTO:** Record feature. Cast Misty Step without a slot (uses = Wisdom modifier); can bring one willing creature.

#### Gloom Stalker (Shadowy Dodge):
**AUTO:** Record feature. Reaction — impose Disadvantage on an incoming attack; then teleport 30 ft.

#### Hunter (Superior Hunter's Defense):
**AUTO:** Record feature. Reaction to gain Resistance to a damage type you just took (and same type) until end of turn.

**Also at Level 15:**
- **AUTO:** Prepared Spells max → 12. Spell slots → 4/3/3/2.

---

## Level 16 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 17 — Precise Hunter

**AUTO:** Record feature. Advantage on attack rolls against creatures marked by Hunter's Mark.

**Also at Level 17:**
- **AUTO:** Proficiency Bonus → +6. Recalculate all dependent values.
- **AUTO:** Favored Enemy uses → 6. UPDATE `character.resources.favoredEnemy.uses`.
- **AUTO:** Prepared Spells max → 14. Spell slots → 4/3/3/3/1 (gain level 5 slot).

---

## Level 18 — Feral Senses

**AUTO:** Record feature. Gain Blindsight 30 ft. UPDATE `character.senses.blindsight` = 30.

---

## Level 19 — Epic Boon

**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Recommended: Boon of Dimensional Travel. Choose one:" [list Epic Boon feats]
Apply chosen feat. UPDATE `character.feats`.

**Also at Level 19:**
- **AUTO:** Prepared Spells max → 15. Spell slots → 4/3/3/3/2.

---

## Level 20 — Foe Slayer

**AUTO:** Record upgrade. Hunter's Mark bonus damage die increases to d10 (was d6 by default).

---

## Prepared Spells Maximum
Ranger's prepared spell count is given directly by the class table.
Use the class table in `classes/ranger.md`.
