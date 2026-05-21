# ROGUE Level-Up Wizard

**Hit Die:** d8 (average: 5)
**Spellcasting:** Arcane Trickster subclass only (Intelligence-based Wizard spells)

---

## Universal Steps (every level)
1. **HP:** PROMPT roll d8 or take 5 + Con modifier → UPDATE `hp.maximum`
2. **Proficiency Bonus:** AUTO update at levels 5/9/13/17
3. **Sneak Attack Dice:** AUTO update from class table

---

## Level 1 — Starting Features

### Expertise
**PROMPT:** "Expertise: Choose 2 skill proficiencies to gain Expertise in (your proficiency bonus is doubled for checks with these skills). You must already be proficient in the chosen skills."
- Show only skills the character is already proficient in (Rogue starts with 4 skills).
- **UPDATE** both chosen skills to `expertise` status.
- Recalculate their bonuses.

### Sneak Attack
**AUTO:** Record feature. 1d6 extra damage. Triggers once per turn with a Finesse or Ranged weapon when you have Advantage, OR when an ally is adjacent to the target (no Disadvantage). UPDATE `character.features.sneakAttack.dice` = 1.

### Thieves' Cant
**AUTO:** Record feature. Knows Thieves' Cant (secret language).
**PROMPT:** "Thieves' Cant: Choose 1 additional language to learn." UPDATE `character.languages`.

### Weapon Mastery
**PROMPT:** "Weapon Mastery: Choose 2 weapons you are proficient with (must have the Finesse or Light property for Rogue-compatible weapons). You can use the Mastery property of these weapons."
- UPDATE `character.weaponMastery` with the 2 chosen weapons.
- Player may change these on each Long Rest.

---

## Level 2 — Cunning Action

**AUTO:** Record feature. Bonus Action — take the Dash, Disengage, or Hide action.

**Also at Level 2:**
- **AUTO:** Sneak Attack → 1d6 (unchanged at level 2).

---

## Level 3 — Rogue Subclass & Steady Aim

### Steady Aim
**AUTO:** Record feature. Bonus Action — give yourself Advantage on your next attack this turn. Speed becomes 0 ft. for the turn.

### Rogue Subclass
**PROMPT:** "Choose your Rogue subclass (Roguish Archetype):"
- **Arcane Trickster** — Intelligence-based Wizard spells, invisible Mage Hand
- **Assassin** — Advantage on Initiative, double Sneak Attack damage on first round
- **Soulknife** — Psionic Energy Dice, manifested psychic blades, telepathy
- **Thief** — Fast Hands, Climb Speed, Use Magic Device

Apply subclass features immediately. UPDATE `character.subclass`.

#### Arcane Trickster — Spellcasting:
**AUTO:** Intelligence-based Wizard spells. Spell attack = Prof + Int modifier. Spell save DC = 8 + Prof + Int modifier.
**PROMPT:** "Arcane Trickster: Choose 2 cantrips from the Wizard cantrip list. One must be Mage Hand (which gains special enhancements)."
- If player doesn't pick Mage Hand, note they automatically know it.
UPDATE `character.spells.cantrips`.
**PROMPT:** "Choose 3 level 1 Wizard spells to know (at least 2 must be Enchantment or Illusion spells)." UPDATE `character.spells.known`.
(Arcane Trickster has its own spell progression — see Arcane Trickster Spell Progression at end of this file.)

#### Assassin — Assassinate & Assassin's Tools:
**AUTO:** Record Assassinate feature. Advantage on Initiative rolls. UPDATE `character.features.initiative` (add Advantage note).
**AUTO:** Gain Disguise Kit and Poisoner's Kit with proficiency. UPDATE `character.proficiencies.tools`.

#### Soulknife — Psionic Power:
**AUTO:** Gain Psionic Energy Dice (d6). Count = Proficiency Bonus. UPDATE `character.resources.psionicEnergyDice`.
Record available powers: Psi-Bolstered Knack, Psychic Whispers.
Record Psychic Blades feature.

#### Thief — Fast Hands & Second-Story Work:
**AUTO:** Record Fast Hands feature. Bonus Action for Sleight of Hand, Use Magic Device, or Utilize action.
**AUTO:** Gain Climb Speed = Speed. Update `character.speed.climb`.
Can use Dexterity for jump distance.

**Also at Level 3:**
- **AUTO:** Sneak Attack → 2d6. UPDATE `character.features.sneakAttack.dice`.

---

## Level 4 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Dexterity increases: recalculate attack bonuses, AC.

**Also at Level 4:**
- **AUTO:** Sneak Attack → 2d6 (unchanged).

---

## Level 5 — Cunning Strike & Uncanny Dodge

### Cunning Strike
**AUTO:** Record feature. After dealing Sneak Attack damage, add one effect by removing dice from the total. DC = 8 + Dex modifier + Proficiency Bonus. Available effects:
- **Poison** (1d6 cost) — target becomes Poisoned for 1 minute (Con save negates)
- **Trip** (1d6 cost) — target falls Prone if Large or smaller (Dex save negates)
- **Withdraw** (1d6 cost) — move half Speed without provoking Opportunity Attacks
Record all three options. UPDATE `character.features.cunningStrike.dc`.

### Uncanny Dodge
**AUTO:** Record feature. Reaction — halve one attack's damage against you.

**Also at Level 5:**
- **AUTO:** Proficiency Bonus → +3. Recalculate all dependent values.
- **AUTO:** Sneak Attack → 3d6. UPDATE `character.features.sneakAttack.dice`.

---

## Level 6 — Expertise (2nd)

**PROMPT:** "Expertise: Choose 2 more skill proficiencies to gain Expertise in."
- Show proficient skills that don't already have Expertise.
- **UPDATE** both chosen skills to `expertise` status.

**Also at Level 6:**
- **AUTO:** Sneak Attack → 3d6 (unchanged).

---

## Level 7 — Evasion & Reliable Talent

### Evasion
**AUTO:** Record feature. No damage on successful Dexterity saves; half damage on failure.

### Reliable Talent
**AUTO:** Record feature. For any ability check that includes Proficiency Bonus, treat d20 rolls of 9 or lower as 10.

**Also at Level 7:**
- **AUTO:** Sneak Attack → 4d6. UPDATE `character.features.sneakAttack.dice`.

---

## Level 8 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 9 — Subclass Feature

#### Arcane Trickster (Magical Ambush):
**AUTO:** Record feature. Targets have Disadvantage on saves against your spells when you cast while Invisible.
**AUTO:** Arcane Trickster gains more spells. **PROMPT:** "Choose 1 additional Wizard spell (Enchantment or Illusion)." UPDATE `character.spells.known`.

#### Assassin (Infiltration Expertise):
**AUTO:** Record feature. Can mimic another's speech and handwriting. Steady Aim no longer reduces Speed.

#### Soulknife (Soul Blades):
**AUTO:** Record Homing Strikes and Psychic Teleportation features.

#### Thief (Supreme Sneak):
**AUTO:** New Cunning Strike option unlocked: Stealth Attack (1d6 cost — remain Invisible after attack if ending turn in cover).
UPDATE `character.features.cunningStrike` to include Stealth Attack option.

**Also at Level 9:**
- **AUTO:** Proficiency Bonus → +4. Recalculate all dependent values.
- **AUTO:** Sneak Attack → 5d6. UPDATE `character.features.sneakAttack.dice`.

---

## Level 10 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 10:**
- **AUTO:** Sneak Attack → 5d6 (unchanged).

---

## Level 11 — Improved Cunning Strike

**AUTO:** Record upgrade. Can use up to two Cunning Strike effects at once (pay both dice costs).

**Also at Level 11:**
- **AUTO:** Sneak Attack → 6d6. UPDATE `character.features.sneakAttack.dice`.

---

## Level 12 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 13 — Subclass Feature

#### Arcane Trickster (Versatile Trickster):
**AUTO:** Record feature. When using the Trip Cunning Strike option, can also Trip another creature within 5 ft. of your Mage Hand.

#### Assassin (Envenom Weapons):
**AUTO:** Record upgrade. Poison Cunning Strike also deals 2d6 Poison damage on each failed save (ignores Resistance).

#### Soulknife (Psychic Veil):
**AUTO:** Record feature. Magic Action — become Invisible for 1 hour; ends on dealing damage or forcing a save.

#### Thief (Use Magic Device):
**AUTO:** Record feature. Can attune to 4 items; roll 6 on Utilize to use charged item without expending charges; can use any Spell Scroll (Intelligence-based).

**Also at Level 13:**
- **AUTO:** Proficiency Bonus → +5. Recalculate all dependent values.
- **AUTO:** Sneak Attack → 7d6. UPDATE `character.features.sneakAttack.dice`.

---

## Level 14 — Devious Strikes

**AUTO:** Record feature. New Cunning Strike options available:
- **Daze** (2d6 cost) — Con save or target is highly restricted on their next turn
- **Knock Out** (6d6 cost) — Unconscious for 1 minute (Con save negates; ends on damage)
- **Obscure** (3d6 cost) — Blinded until end of target's next turn
UPDATE `character.features.cunningStrike` to include new options.

---

## Level 15 — Slippery Mind

**AUTO:** Record feature. Gain proficiency in Wisdom and Charisma saving throws. UPDATE `character.savingThrows.wisdom` and `character.savingThrows.charisma` = proficient.

**Also at Level 15:**
- **AUTO:** Sneak Attack → 8d6. UPDATE `character.features.sneakAttack.dice`.

---

## Level 16 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 17 — Subclass Feature (Capstone)

#### Arcane Trickster (Spell Thief):
**AUTO:** Record feature. Reaction after being targeted by a spell — caster makes Int save or you negate the effect and steal the spell for 8 hours.

#### Assassin (Death Strike):
**AUTO:** Record feature. First Sneak Attack hit in a combat forces Con save or damage is doubled.

#### Soulknife (Rend Mind):
**AUTO:** Record feature. When dealing Sneak Attack with Psychic Blades, target makes Wisdom save or is Stunned for 1 minute (once per Long Rest or expend 3 Psionic Energy Dice).

#### Thief (Thief's Reflexes):
**AUTO:** Record feature. Take two turns in the first round of combat; second turn at Initiative − 10.

**Also at Level 17:**
- **AUTO:** Proficiency Bonus → +6. Recalculate all dependent values.
- **AUTO:** Sneak Attack → 9d6. UPDATE `character.features.sneakAttack.dice`.

---

## Level 18 — Elusive

**AUTO:** Record feature. Attack rolls against you can never have Advantage (unless you are Incapacitated).

---

## Level 19 — Epic Boon

**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Recommended: Boon of the Night Spirit. Choose one:" [list Epic Boon feats]
Apply chosen feat. UPDATE `character.feats`.

**Also at Level 19:**
- **AUTO:** Sneak Attack → 10d6. UPDATE `character.features.sneakAttack.dice`.

---

## Level 20 — Stroke of Luck

**AUTO:** Record feature. Can turn a failed D20 Test into a roll of 20. Once per Short or Long Rest. UPDATE `character.resources.strokeOfLuck`.

---

## Arcane Trickster Spell Progression

Arcane Tricksters are quarter-casters:
- Level 3: 2 × level 1 slots; know 3 level 1 spells + 2 cantrips
- Level 4: 3 × level 1 slots; know 4 spells; **PROMPT** new spell choice
- Level 7: gain level 2 slots; know 5 spells; **PROMPT** new spell choice
- Level 8: 6 spells; **PROMPT** new spell choice
- Level 10: gain level 2 slots (+1); 7 spells; **PROMPT** new spell choice
- Level 11: 8 spells; **PROMPT** new spell choice
- Level 13: gain level 3 slots; 9 spells; **PROMPT** new spell choice
- Level 14: 10 spells; **PROMPT** new spell choice
- Level 16: 11 spells; **PROMPT** new spell choice
- Level 19: gain level 4 slots; 12 spells; **PROMPT** new spell choice
- Level 20: 13 spells; **PROMPT** new spell choice

Most new spells must be Enchantment or Illusion; one spell per tier (levels 3, 8, 14, 20) can be from any school.
On each of these levels, **PROMPT** the player to choose new spells.
