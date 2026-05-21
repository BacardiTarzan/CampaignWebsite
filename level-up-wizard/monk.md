# MONK Level-Up Wizard

**Hit Die:** d8 (average: 5)
**Spellcasting:** None (some subclasses have limited spell-like abilities)

---

## Universal Steps (every level)
1. **HP:** PROMPT roll d8 or take 5 + Con modifier → UPDATE `hp.maximum`
2. **Proficiency Bonus:** AUTO update at levels 5/9/13/17
3. **Martial Arts Die:** AUTO update from class table (d6 at 1–4, d8 at 5–10, d10 at 11–16, d12 at 17–20)
4. **Focus Points:** AUTO update (= Monk level; 0 at level 1, 2 at level 2, etc.)
5. **Unarmored Movement Bonus:** AUTO update from class table

---

## Level 1 — Starting Features

### Martial Arts
**AUTO:** Record feature.
- Unarmed Strike uses Martial Arts die (d6).
- Can use Dexterity for attack/damage with Monk weapons and Unarmed Strikes when not wearing armor or using a Shield.
- As a Bonus Action, make one additional Unarmed Strike after attacking with a Monk weapon or Unarmed Strike.
UPDATE `character.features.martialArts`.
Recalculate Unarmed Strike damage: d6 + Str or Dex modifier (whichever the player prefers, or set to Dex if using Dex build).

### Unarmored Defense
**AUTO:** Record feature. When not wearing armor or a Shield: AC = 10 + Dex modifier + Wisdom modifier. UPDATE `character.ac` formula if currently unarmored.

---

## Level 2 — Monk's Focus, Unarmored Movement, Uncanny Metabolism

### Monk's Focus
**AUTO:** Record feature. Focus Points = 2. UPDATE `character.resources.focusPoints.max` = 2.
Focus Point Save DC = 8 + Wisdom modifier + Proficiency Bonus. Record available powers:
- Flurry of Blows (1 FP): Two Unarmed Strikes as Bonus Action.
- Patient Defense (free Disengage; or 1 FP for Disengage + Dodge).
- Step of the Wind (free Dash; or 1 FP for Disengage + Dash + doubled jump distance).

### Unarmored Movement
**AUTO:** Record feature. Speed +10 ft. when not wearing armor or a Shield. UPDATE `character.speed` (add +10 ft. conditional bonus).

### Uncanny Metabolism
**AUTO:** Record feature. On rolling Initiative, regain all Focus Points and heal 1 Monk level + 1 Martial Arts die HP. Once per Long Rest.

---

## Level 3 — Deflect Attacks & Monk Subclass

### Deflect Attacks
**AUTO:** Record feature. Reaction — reduce Bludgeoning/Piercing/Slashing damage by 1d10 + Dex modifier + Monk level. If reduced to 0, spend 1 FP to redirect the attack at another creature.

### Monk Subclass
**PROMPT:** "Choose your Monk subclass (Monastic Tradition):"
- **Warrior of Mercy** — healing and harming touch, Insight/Medicine proficiencies
- **Warrior of Shadow** — Darkness casting, Shadow Step teleportation
- **Warrior of the Elements** — elemental attunement, reach, elemental burst
- **Warrior of the Open Hand** — Open Hand Technique (Push/Topple/Addle), Wholeness of Body

Apply subclass features immediately. UPDATE `character.subclass`.

#### Warrior of Mercy:
**AUTO:** Gain proficiency with Insight, Medicine, and Herbalism Kit. UPDATE `character.skills` (Insight and Medicine if not already proficient) and `character.proficiencies.tools`.
Record Hand of Harm and Hand of Healing features.

#### Warrior of Shadow:
**AUTO:** Record Shadow Arts. Gain 60-ft. Darkvision (or +60 ft. if already have Darkvision). UPDATE `character.senses.darkvision`.
Know Minor Illusion cantrip (Wisdom-based). UPDATE `character.spells.cantrips`.

#### Warrior of the Elements:
**AUTO:** Know Elementalism cantrip (Wisdom-based). UPDATE `character.spells.cantrips`.
Record Elemental Attunement feature.

#### Warrior of the Open Hand:
**AUTO:** Record Open Hand Technique (Push/Topple/Addle options after Flurry of Blows hit).

**Also at Level 3:**
- **AUTO:** Focus Points → 3. UPDATE `character.resources.focusPoints.max`.

---

## Level 4 — Ability Score Improvement & Slow Fall

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Dexterity increases: recalculate attack bonuses and Deflect Attacks reduction.
If Wisdom increases: recalculate Monk's Focus Save DC, Unarmored Defense AC.

### Slow Fall
**AUTO:** Record feature. Reaction — reduce falling damage by 5× Monk level.

**Also at Level 4:**
- **AUTO:** Focus Points → 4.

---

## Level 5 — Extra Attack & Stunning Strike

### Extra Attack
**AUTO:** Record feature. Character attacks twice per Attack action. UPDATE `character.features.extraAttack`.

### Stunning Strike
**AUTO:** Record feature. After hitting with a Monk weapon or Unarmed Strike, spend 1 FP — target makes Con save (DC = Focus Point Save DC) or is Stunned until your next turn; on success, Speed halved and next attack roll against target has Advantage.

**Also at Level 5:**
- **AUTO:** Proficiency Bonus → +3. Recalculate all dependent values (Focus Point Save DC, attack bonuses, Deflect Attacks).
- **AUTO:** Martial Arts Die → d8. UPDATE `character.features.martialArts.die`.
- **AUTO:** Focus Points → 5.

---

## Level 6 — Empowered Strikes & Subclass Feature

### Empowered Strikes
**AUTO:** Record feature. Unarmed Strikes can deal Force damage or their normal type (player's choice each time).

### Subclass Feature (Level 6)

#### Warrior of Mercy (Physician's Touch):
**AUTO:** Record upgrade. Hand of Harm can Poison the target. Hand of Healing can end Blinded, Deafened, Paralyzed, Poisoned, or Stunned.

#### Warrior of Shadow (Shadow Step):
**AUTO:** Record feature. Bonus Action — teleport 60 ft. between dim/dark areas; Advantage on next melee attack.

#### Warrior of the Elements (Elemental Burst):
**AUTO:** Record feature. Magic Action + 2 FP — elemental burst in 20-ft. Sphere within 120 ft. (Dexterity save; damage = 3× Martial Arts die).

#### Warrior of the Open Hand (Wholeness of Body):
**AUTO:** Record feature. Bonus Action — heal yourself for 1 Martial Arts die + Wisdom modifier HP. Uses = Wisdom modifier (min 1); recharge on Long Rest. UPDATE `character.resources.wholenessOfBody`.

**Also at Level 6:**
- **AUTO:** Unarmored Movement bonus → +15 ft. UPDATE `character.speed`.
- **AUTO:** Focus Points → 6.

---

## Level 7 — Evasion

**AUTO:** Record feature. No damage on successful Dexterity saves; half damage on failure.

**Also at Level 7:**
- **AUTO:** Focus Points → 7.

---

## Level 8 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Wisdom increases: recalculate AC (Unarmored Defense), Focus Point Save DC.

**Also at Level 8:**
- **AUTO:** Focus Points → 8.

---

## Level 9 — Acrobatic Movement

**AUTO:** Record feature. Can run along vertical surfaces and across liquids during your turn (movement must end on solid ground or fall).

**Also at Level 9:**
- **AUTO:** Proficiency Bonus → +4. Recalculate all dependent values.
- **AUTO:** Unarmored Movement bonus → +15 ft. (unchanged from level 6).
- **AUTO:** Focus Points → 9.

---

## Level 10 — Heightened Focus & Self-Restoration

### Heightened Focus
**AUTO:** Record upgrades:
- Flurry of Blows now grants 3 Unarmed Strikes (still costs 1 FP).
- Patient Defense (FP version) also grants Temp HP = Martial Arts die + Wisdom modifier.
- Step of the Wind (FP version) can also move a willing creature within 5 ft. alongside you.

### Self-Restoration
**AUTO:** Record feature. At the end of each turn, automatically remove one of: Charmed, Frightened, or Poisoned condition.

**Also at Level 10:**
- **AUTO:** Unarmored Movement bonus → +20 ft. UPDATE `character.speed`.
- **AUTO:** Focus Points → 10.

---

## Level 11 — Subclass Feature

#### Warrior of Mercy (Flurry of Healing and Harm):
**AUTO:** Record upgrade. Can freely replace Flurry of Blows strikes with Hand of Healing or Hand of Harm (limited by Wisdom modifier uses per Long Rest). UPDATE `character.resources`.

#### Warrior of Shadow (Improved Shadow Step):
**AUTO:** Record upgrade. Spend 1 FP to remove the dim/dark requirement from Shadow Step; make an Unarmed Strike as part of the teleport.

#### Warrior of the Elements (Stride of the Elements):
**AUTO:** Record feature. While Elemental Attunement is active, also gain Fly Speed and Swim Speed equal to Speed. UPDATE conditional speed entries.

#### Warrior of the Open Hand (Fleet Step):
**AUTO:** Record feature. When taking a Bonus Action other than Step of the Wind, can also take Step of the Wind as part of that same turn.

**Also at Level 11:**
- **AUTO:** Martial Arts Die → d10. UPDATE `character.features.martialArts.die`.
- **AUTO:** Focus Points → 11.

---

## Level 12 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 12:**
- **AUTO:** Focus Points → 12.

---

## Level 13 — Deflect Energy

**AUTO:** Record upgrade. Deflect Attacks now reduces and redirects damage of any type (not just Bludgeoning/Piercing/Slashing).

**Also at Level 13:**
- **AUTO:** Proficiency Bonus → +5. Recalculate all dependent values.
- **AUTO:** Unarmored Movement bonus → +20 ft. (unchanged).
- **AUTO:** Focus Points → 13.

---

## Level 14 — Disciplined Survivor

**AUTO:** Record feature. Gain proficiency in all saving throws (if not already proficient). Can spend 1 FP to reroll a failed save. UPDATE `character.savingThrows` — mark all as proficient.

**Also at Level 14:**
- **AUTO:** Unarmored Movement bonus → +25 ft. UPDATE `character.speed`.
- **AUTO:** Focus Points → 14.

---

## Level 15 — Perfect Focus

**AUTO:** Record feature. When rolling Initiative with fewer than 4 Focus Points (and not using Uncanny Metabolism), regain Focus Points up to 4.

**Also at Level 15:**
- **AUTO:** Focus Points → 15.

---

## Level 16 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 16:**
- **AUTO:** Focus Points → 16.

---

## Level 17 — Subclass Feature (Capstone)

#### Warrior of Mercy (Hand of Ultimate Mercy):
**AUTO:** Record feature. Touch a corpse dead ≤24 hours, spend 5 FP — revive it with 4d10 + Wis modifier HP. Once per Long Rest.

#### Warrior of Shadow (Cloak of Shadows):
**AUTO:** Record feature. Magic Action + 3 FP — Invisible and partially incorporeal for 1 minute while in dim/dark; Flurry of Blows costs no FP.

#### Warrior of the Elements (Elemental Epitome):
**AUTO:** Record feature. While Attuned: Resistance to chosen element type; Destructive Stride (deal damage to creatures you move past); extra Martial Arts die on one Unarmed hit per turn.

#### Warrior of the Open Hand (Quivering Palm):
**AUTO:** Record feature. After hitting with Unarmed Strike, spend 4 FP — set vibrations on target (lasts Monk level days); Action to trigger (Con save or 10d12 Force damage).

**Also at Level 17:**
- **AUTO:** Proficiency Bonus → +6. Recalculate all dependent values.
- **AUTO:** Martial Arts Die → d12. UPDATE `character.features.martialArts.die`.
- **AUTO:** Unarmored Movement bonus → +25 ft. (unchanged).
- **AUTO:** Focus Points → 17.

---

## Level 18 — Superior Defense

**AUTO:** Record feature. Spend 3 FP at the start of your turn — gain Resistance to all damage types except Force for 1 minute.

**Also at Level 18:**
- **AUTO:** Unarmored Movement bonus → +30 ft. UPDATE `character.speed`.
- **AUTO:** Focus Points → 18.

---

## Level 19 — Epic Boon

**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Recommended: Boon of Irresistible Offense. Choose one:" [list Epic Boon feats]
Apply chosen feat. UPDATE `character.feats`.

**Also at Level 19:**
- **AUTO:** Focus Points → 19.

---

## Level 20 — Body and Mind

**AUTO:** Record feature.
**UPDATE:** Dexterity score +4 (max 25). Recalculate Dexterity modifier, attack bonuses, AC, skills.
**UPDATE:** Wisdom score +4 (max 25). Recalculate Wisdom modifier, AC (Unarmored Defense), Focus Point Save DC, skills.

Note: Inform the player their Dexterity and Wisdom maximums are now 25 (not 20) for this feature's purpose.

**Also at Level 20:**
- **AUTO:** Focus Points → 20.
