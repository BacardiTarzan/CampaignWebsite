# Character Creation Rules

Step-by-step character creation rules for 2024 D&D (SRD 5.2.1).

---

## Step 1: Choose Class

Choose a class. This determines your Hit Die, primary ability, armor training, weapon proficiencies, and skill choices.

| Class | Primary Ability | Complexity |
|-------|----------------|------------|
| Barbarian | Strength | Average |
| Bard | Charisma | High |
| Cleric | Wisdom | Average |
| Druid | Wisdom | High |
| Fighter | Strength or Dexterity | Low |
| Monk | Dexterity and Wisdom | High |
| Paladin | Strength and Charisma | Average |
| Ranger | Dexterity and Wisdom | Average |
| Rogue | Dexterity | Low |
| Sorcerer | Charisma | High |
| Warlock | Charisma | High |
| Wizard | Intelligence | Average |

- Record your level (typically 1) and XP (0 for level 1).
- Note your armor training from your class.

---

## Step 2: Character Origin

Choose a **Background**, a **Species**, and two **Languages**.

### Background
Your background grants:
- An **Origin Feat**
- Proficiency in **2 skills**
- Proficiency with **1 tool**
- **Starting equipment** (option A: specific items + gold, or option B: flat gold amount)
- **3 ability scores** that your background can improve (used in Step 3)

### Species
Your species determines:
- Creature Type (usually Humanoid)
- Size
- Speed
- Species traits (including any special senses, resistances, or innate abilities)
- Typically 1–2 additional languages (see species descriptions)

### Languages
You know **Common plus 2 standard languages** (chosen or rolled). See `rules/languages.md` for the full list.

---

## Step 3: Ability Scores

### Generate Scores (choose one method)

**Standard Array** — Assign these six values: 15, 14, 13, 12, 10, 8

**Random Generation** — Roll 4d6, drop the lowest die, record total. Do this 6 times.

**Point Buy** — Distribute 27 points. All scores start at 8.

| Score | Cost |
|-------|------|
| 8 | 0 |
| 9 | 1 |
| 10 | 2 |
| 11 | 3 |
| 12 | 4 |
| 13 | 5 |
| 14 | 7 |
| 15 | 9 |

Maximum score via point buy: 15 (before background ASI). Minimum: 8.

### Standard Array Suggestions by Class

| Class | Str | Dex | Con | Int | Wis | Cha |
|-------|-----|-----|-----|-----|-----|-----|
| Barbarian | 15 | 13 | 14 | 10 | 12 | 8 |
| Bard | 8 | 14 | 12 | 13 | 10 | 15 |
| Cleric | 14 | 8 | 13 | 10 | 15 | 12 |
| Druid | 8 | 12 | 14 | 13 | 15 | 10 |
| Fighter | 15 | 14 | 13 | 8 | 10 | 12 |
| Monk | 12 | 15 | 13 | 10 | 14 | 8 |
| Paladin | 15 | 10 | 13 | 8 | 12 | 14 |
| Ranger | 12 | 15 | 13 | 8 | 14 | 10 |
| Rogue | 12 | 15 | 13 | 14 | 10 | 8 |
| Sorcerer | 10 | 13 | 14 | 8 | 12 | 15 |
| Warlock | 8 | 14 | 13 | 12 | 10 | 15 |
| Wizard | 8 | 12 | 13 | 15 | 14 | 10 |

### Apply Background Ability Score Increases

Your background lists 3 ability scores. Choose one of:
- **+2 to one, +1 to a different one** (from the 3 listed)
- **+1 to all three**

No score can exceed 20 from this increase.

### Ability Score Modifiers

| Score | Modifier | Score | Modifier |
|-------|----------|-------|----------|
| 3 | −4 | 16–17 | +3 |
| 4–5 | −3 | 18–19 | +4 |
| 6–7 | −2 | 20–21 | +5 |
| 8–9 | −1 | 22–23 | +6 |
| 10–11 | +0 | 24–25 | +7 |
| 12–13 | +1 | 26–27 | +8 |
| 14–15 | +2 | 28–29 | +9 |
|  |  | 30 | +10 |

---

## Step 4: Alignment

Choose an alignment. The nine alignments combine morality (Good/Neutral/Evil) with order (Lawful/Neutral/Chaotic):

Lawful Good · Neutral Good · Chaotic Good
Lawful Neutral · True Neutral · Chaotic Neutral
Lawful Evil · Neutral Evil · Chaotic Evil

The game assumes player characters are not evil. Check with your DM before making an evil character.

---

## Step 5: Derived Statistics

### Hit Points (Level 1)
HP = Maximum Hit Die value + Constitution modifier

| Class | Hit Die | HP at Level 1 (before Con) |
|-------|---------|---------------------------|
| Barbarian | d12 | 12 |
| Fighter, Paladin, Ranger | d10 | 10 |
| Bard, Cleric, Druid, Monk, Rogue, Warlock | d8 | 8 |
| Sorcerer, Wizard | d6 | 6 |

### Armor Class (Base)
- No armor: AC = 10 + Dexterity modifier
- Some classes/species have alternative base AC calculations (e.g., Barbarian Unarmored Defense: 10 + Dex + Con)
- Armor: see `equipment/armor.md`

### Proficiency Bonus
Determined by total character level (not class level):

| Level | Proficiency Bonus |
|-------|------------------|
| 1–4 | +2 |
| 5–8 | +3 |
| 9–12 | +4 |
| 13–16 | +5 |
| 17–20 | +6 |

### Saving Throws
Add your Proficiency Bonus to saving throws your class is proficient in.

### Skill Bonuses
For each skill you're proficient in: ability modifier + Proficiency Bonus.
For Expertise: ability modifier + (2 × Proficiency Bonus).

---

## Step 6: Equipment

Your background and class each provide a starting equipment choice:
- **Option A:** Specific listed items
- **Option B:** A flat gold amount to purchase your own gear

See `equipment/` folder for full equipment details.

---

## Step 7: Level 1 Class Features

Apply all level 1 features from your class. Make any required choices (fighting style, cantrips known, skill proficiencies, etc.).

---

## Character Advancement (XP Table)

| Level | XP Required | Proficiency Bonus |
|-------|-------------|------------------|
| 1 | 0 | +2 |
| 2 | 300 | +2 |
| 3 | 900 | +2 |
| 4 | 2,700 | +2 |
| 5 | 6,500 | +3 |
| 6 | 14,000 | +3 |
| 7 | 23,000 | +3 |
| 8 | 34,000 | +3 |
| 9 | 48,000 | +4 |
| 10 | 64,000 | +4 |
| 11 | 85,000 | +4 |
| 12 | 100,000 | +4 |
| 13 | 120,000 | +5 |
| 14 | 140,000 | +5 |
| 15 | 165,000 | +5 |
| 16 | 195,000 | +5 |
| 17 | 225,000 | +6 |
| 18 | 265,000 | +6 |
| 19 | 305,000 | +6 |
| 20 | 355,000 | +6 |

---

## Gaining a Level

1. **Choose a class** — advance in current class, or take a level in a new class (see `rules/multiclassing.md`).
2. **Adjust HP and Hit Point Dice** — gain one Hit Die; roll it + Con modifier (minimum 1), OR use the fixed value:

| Class | Fixed HP per Level |
|-------|-------------------|
| Barbarian | 7 + Con modifier |
| Fighter, Paladin, Ranger | 6 + Con modifier |
| Bard, Cleric, Druid, Monk, Rogue, Warlock | 5 + Con modifier |
| Sorcerer, Wizard | 4 + Con modifier |

3. **Record new class features** from the class progression table.
4. **Adjust Proficiency Bonus** if it increased (update all rolls that include it).
5. **Adjust ability modifiers** if a feat increased an ability score.

---

## Starting at Higher Levels

If beginning above level 1, the DM sets starting equipment and magic items:

| Starting Level | Equipment & Gold | Magic Items |
|----------------|-----------------|-------------|
| 2–4 | Normal starting equipment | 1 Common |
| 5–10 | 500 GP + 1d10 × 25 GP + normal equipment | 1 Common, 1 Uncommon |
| 11–16 | 5,000 GP + 1d10 × 250 GP + normal equipment | 2 Common, 3 Uncommon, 1 Rare |
| 17–20 | 20,000 GP + 1d10 × 250 GP + normal equipment | 2 Common, 4 Uncommon, 3 Rare, 1 Very Rare |

If starting at level 3+, also choose a subclass.
