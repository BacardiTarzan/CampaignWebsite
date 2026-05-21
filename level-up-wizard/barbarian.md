# BARBARIAN Level-Up Wizard

**Hit Die:** d12 (average: 7)
**Spellcasting:** None

---

## Universal Steps (every level)
1. **HP:** PROMPT roll d12 or take 7 + Con modifier → UPDATE `hp.maximum`
2. **Proficiency Bonus:** AUTO update at levels 5/9/13/17
3. **Rages:** AUTO update from class table
4. **Rage Damage Bonus:** AUTO update from class table (+2 at levels 1–8, +3 at 9–15, +4 at 16–20)
5. **Weapon Mastery (count):** AUTO update from class table

---

## Level 1 — Starting Features

### Rage
**AUTO:** Record feature. 2 Rage uses per Long Rest. UPDATE `character.resources.rageUses`.

### Unarmored Defense
**AUTO:** Record feature. When not wearing armor: AC = 10 + Dex modifier + Con modifier (Shield still allowed). UPDATE `character.ac` formula if character is unarmored.

### Weapon Mastery
**PROMPT:** "Weapon Mastery: Choose 2 Simple or Martial Melee weapons you are proficient with. You can use the Mastery property of these weapons."
- UPDATE `character.weaponMastery` with the 2 chosen weapons.
- Note: The player may change these selections on each Long Rest (remind them of this).

---

## Level 2 — Danger Sense & Reckless Attack

### Danger Sense
**AUTO:** Record feature. Advantage on Dexterity saving throws (not while Incapacitated or unable to see).

### Reckless Attack
**AUTO:** Record feature. No choices required.

---

## Level 3 — Subclass & Primal Knowledge

### Barbarian Subclass
**PROMPT:** "Choose your Barbarian subclass (Primal Path):"
- **Path of the Berserker** — extra damage while Raging, immunity to Charmed/Frightened
- **Path of the Wild Heart** — nature-themed rage forms (Bear, Eagle, or Wolf)
- **Path of the World Tree** — Temp HP, teleportation, reach
- **Path of the Zealot** — divine damage, divine warrior form

Apply subclass features immediately (see below). UPDATE `character.subclass`.

#### If Path of the Wild Heart (Rage of the Wilds):
**PROMPT:** "Rage of the Wilds: When you activate Rage, choose one of the following forms: Bear (Resistance to all damage except Psychic and Force while Raging), Eagle (Bonus Action Dash/Disengage while Raging), or Wolf (allies within 10 ft have Advantage on attacks vs. enemies you're threatening). You choose the form each time you Rage."
- No permanent choice required — player decides each time they Rage.
- UPDATE `character.features.rageOfTheWilds`.

#### If Path of the Wild Heart (Aspect of the Wilds — Level 6):
*(Noted here for reference; applied at level 6)*

### Primal Knowledge
**PROMPT:** "Primal Knowledge: Choose 1 additional skill proficiency from the following list (you may not choose a skill you already have proficiency in):"
- Options: Acrobatics, Animal Handling, Arcana, Athletics, Insight, Intimidation, Medicine, Nature, Perception, Stealth, Survival
- **UPDATE** `character.skills` — add proficiency to the chosen skill.
- Recalculate the skill's bonus.

**Also at Level 3:**
- **AUTO:** Rages per Long Rest increases to 3. UPDATE `character.resources.rageUses`.

---

## Level 4 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Strength increases: recalculate attack bonuses. If Constitution increases: recalculate HP maximum retroactively (add the increase × Barbarian level to hp.maximum), Unarmored Defense AC.

**Also at Level 4:**
- **AUTO:** Weapon Mastery count increases to 3.
- **PROMPT:** "Weapon Mastery: Your Weapon Mastery count increased to 3. Choose 1 additional weapon." UPDATE `character.weaponMastery`.

---

## Level 5 — Extra Attack & Fast Movement

### Extra Attack
**AUTO:** Record feature. Character now attacks twice per Attack action. UPDATE `character.features.extraAttack`.

### Fast Movement
**AUTO:** Record feature. Speed +10 ft. (not while wearing Heavy armor). UPDATE `character.speed` (conditionally).

**Also at Level 5:**
- **AUTO:** Proficiency Bonus increases to +3. Recalculate all dependent values (attack bonuses, skills, saves, DCs).

---

## Level 6 — Subclass Feature

#### If Path of the Berserker (Mindless Rage):
**AUTO:** Record feature. Immunity to Charmed and Frightened while Raging.

#### If Path of the Wild Heart (Aspect of the Wilds):
**PROMPT:** "Aspect of the Wilds: Choose one of the following benefits (you may change your choice on each Long Rest):"
- **Owl:** Darkvision +60 ft. (if you have Darkvision, extend it; if not, gain 60 ft. Darkvision)
- **Panther:** Gain Climb Speed equal to your Speed
- **Salmon:** Gain Swim Speed equal to your Speed
- **UPDATE** `character.features.aspectOfTheWilds` with chosen aspect.
- UPDATE relevant movement speeds or senses accordingly.

#### If Path of the World Tree (Branches of the Tree):
**AUTO:** Record feature. Reaction to teleport a creature within 30 ft. to within 5 ft. of you.

#### If Path of the Zealot (Fanatical Focus):
**AUTO:** Record feature. Once per Rage, reroll a failed saving throw.

**Also at Level 6:**
- **AUTO:** Rages per Long Rest increases to 4. UPDATE `character.resources.rageUses`.

---

## Level 7 — Feral Instinct & Instinctive Pounce

### Feral Instinct
**AUTO:** Record feature. Advantage on Initiative rolls.

### Instinctive Pounce
**AUTO:** Record feature. Move up to half Speed as part of the Bonus Action used to enter Rage.

---

## Level 8 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 9 — Brutal Strike

### Brutal Strike
**AUTO:** Record feature. When using Reckless Attack, may forgo Advantage on one Strength attack to deal +1d10 damage and apply a Brutal Strike effect.
- **PROMPT (during gameplay, not level-up):** Player chooses Forceful Blow or Hamstring Blow each time they use Brutal Strike.
- No permanent choice at level-up; record available effects: Forceful Blow, Hamstring Blow.
- UPDATE `character.features.brutalStrike`.

**Also at Level 9:**
- **AUTO:** Proficiency Bonus increases to +4. Recalculate all dependent values.
- **AUTO:** Rage Damage bonus increases to +3.

---

## Level 10 — Subclass Feature

#### If Path of the Berserker (Retaliation):
**AUTO:** Record feature. Reaction to make a melee attack when a creature within 5 ft. damages you.

#### If Path of the Wild Heart (Nature Speaker):
**AUTO:** Record feature. Can cast Commune with Nature as a Ritual.

#### If Path of the World Tree (Battering Roots):
**AUTO:** Record feature. Melee reach +10 ft. with Heavy or Versatile weapons; can activate Push or Topple mastery in addition to another mastery.

#### If Path of the Zealot (Zealous Presence):
**AUTO:** Record feature. Bonus Action — up to 10 allies within 60 ft. gain Advantage on attacks and saves until your next turn.

**Also at Level 10:**
- **AUTO:** Weapon Mastery count increases to 4.
- **PROMPT:** "Weapon Mastery: Your count increased to 4. Choose 1 additional weapon." UPDATE `character.weaponMastery`.

---

## Level 11 — Relentless Rage

**AUTO:** Record feature. When dropping to 0 HP during Rage, make DC 10 Con save to survive with HP = 2× Barbarian level instead. DC increases by 5 per use; resets on Short/Long Rest.

---

## Level 12 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 12:**
- **AUTO:** Rages per Long Rest increases to 5.

---

## Level 13 — Improved Brutal Strike

### Improved Brutal Strike
**AUTO:** Record feature. Adds Staggering Blow and Sundering Blow to available Brutal Strike options. UPDATE `character.features.brutalStrike` to include new options.

**Also at Level 13:**
- **AUTO:** Proficiency Bonus increases to +5. Recalculate all dependent values.

---

## Level 14 — Subclass Feature

#### If Path of the Berserker (Intimidating Presence):
**AUTO:** Record feature. Bonus Action — Wisdom save (DC 8 + Str mod + Prof.) or creatures within 30 ft. become Frightened.

#### If Path of the Wild Heart (Power of the Wilds):
**PROMPT:** "Power of the Wilds: Choose one of the following benefits (you may change your choice on each Long Rest):"
- **Falcon:** Gain Fly Speed equal to your Speed while not wearing Heavy armor
- **Lion:** Enemies within your reach have Disadvantage on attack rolls against creatures other than you
- **Ram:** On a successful melee weapon attack, the target must make a Strength save (DC = Rage save DC) or be knocked Prone
- **UPDATE** `character.features.powerOfTheWilds`.

#### If Path of the World Tree (Travel Along the Tree):
**AUTO:** Record feature. Teleport up to 60 ft. when activating Rage and as a Bonus Action while Raging.

#### If Path of the Zealot (Rage of the Gods):
**AUTO:** Record feature. When activating Rage, assume divine warrior form for 1 minute (Fly Speed, Resistances, Revivification).

---

## Level 15 — Persistent Rage

**AUTO:** Record feature. Roll Initiative to regain all Rage uses (once per Long Rest). Rage now lasts 10 minutes and ends only when Unconscious or wearing Heavy armor (no longer needs extension).

**Also at Level 15:**
- **AUTO:** Rages per Long Rest increases to 5 (unchanged from 12).

---

## Level 16 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Strength increases: recalculate attack bonuses, Relentless Rage HP formula.

**Also at Level 16:**
- **AUTO:** Rage Damage bonus increases to +4.

---

## Level 17 — Improved Brutal Strike (2nd Upgrade)

**AUTO:** Record upgrade. Brutal Strike extra damage increases to 2d10. Can now use two Brutal Strike effects at once. UPDATE `character.features.brutalStrike`.

**Also at Level 17:**
- **AUTO:** Proficiency Bonus increases to +6. Recalculate all dependent values.
- **AUTO:** Rages per Long Rest increases to 6. UPDATE `character.resources.rageUses`.

---

## Level 18 — Indomitable Might

**AUTO:** Record feature. Strength checks and saves can never result in a value below the Strength score.

---

## Level 19 — Epic Boon

**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Recommended: Boon of Irresistible Offense. Choose one:" [list Epic Boon feats]
Apply chosen feat. UPDATE `character.feats`.

---

## Level 20 — Primal Champion

**AUTO:** Record feature.
**UPDATE:** Strength score +4 (max 25). Recalculate Strength modifier, attack bonuses, skills.
**UPDATE:** Constitution score +4 (max 25). Recalculate Constitution modifier, HP maximum retroactively (add Con modifier increase × 20 to hp.maximum), Unarmored Defense AC.

Note: Inform the player their Strength and Constitution maximums are now 25 (not 20) for this feature's purpose.
