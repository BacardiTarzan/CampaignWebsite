# Level-Up Wizard: Overview & Universal Rules

This folder contains per-class instructions for Claude Code's level-up wizard. Each file documents every level's features, which require player prompts, and exactly what character sheet fields to update.

---

## Format Key

- **PROMPT:** Must pause and ask the player to make a selection before proceeding.
- **AUTO:** Happens automatically — no player input required. Just update the sheet.
- **UPDATE [field]:** The character sheet field(s) to modify.
- **CONDITION:** Only applies if a prior choice was made (e.g., specific subclass or option).

---

## Universal Steps at Every Level-Up

Perform these for **every** class level gained, in this order:

### 1. Hit Points
**PROMPT:** "Roll your hit die (1d[X]) or take the average ([avg]). Add your Constitution modifier. How would you like to increase your HP?"
- Present both options (roll or take average).
- **UPDATE** `character.hp.maximum` += result + Constitution modifier.
- If Constitution modifier changed this level (e.g., via ASI), recalculate retroactively.

### 2. Proficiency Bonus
**AUTO:** Check if proficiency bonus increases at this level.
- Increases at levels 5 (+3), 9 (+4), 13 (+5), 17 (+6).
- **UPDATE** `character.proficiencyBonus` if changed.
- Recalculate all dependent values: attack bonuses, skill bonuses, save DCs, etc.

### 3. Class Table Stats
**AUTO:** Update any tracked class resources shown in the class table:
- Spell slots (see per-class instructions)
- Cantrips known
- Prepared spell count
- Class-specific resources (Rage uses, Bardic Inspiration die, Focus Points, Sneak Attack dice, Sorcery Points, Invocations known, etc.)

---

## Ability Score Improvement (ASI) — Appears at Multiple Levels

When a class grants "Ability Score Improvement":

**PROMPT:** "You've gained an Ability Score Improvement. Choose one of the following:"
1. **+2 to one ability score** (max 20)
2. **+1 to two different ability scores** (max 20 each)
3. **Take a General Feat** (must meet prerequisites)

After player chooses:
- If stat increase: **UPDATE** the chosen ability score(s). Recalculate all derived stats (modifier, HP if Con increased, attack bonuses, spell save DCs, skill bonuses, saving throws, passive perception, etc.)
- If feat: See the feat's file in `reference_claude/feats/general/` for its specific prompts and updates.

---

## Subclass Selection

When a class grants "Choose a Subclass" (typically level 3, sometimes level 1 or 2):

**PROMPT:** "Choose your [Class] subclass:" [list all available subclass names with brief descriptions]

After player chooses:
- Apply all subclass features granted at that level immediately.
- Check the subclass entry in the class file for any choices within those features.
- **UPDATE** `character.subclass`.

---

## Epic Boon (Level 19 — All Classes)

**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Choose one:" [list all Epic Boon feats from `reference_claude/feats/epic-boon/`]

Each class has a recommended Epic Boon (noted in the class file), but the player may choose any.

Apply the chosen feat's effects and update the character sheet accordingly.

---

## Fighting Style Feats

When a class grants "Fighting Style":
**PROMPT:** "Choose a Fighting Style feat:" [list options from `reference_claude/feats/fighting-style/`]
- Note any class-specific additions (e.g., Paladin can choose Blessed Warrior; Ranger can choose Druidic Warrior).
- Apply the feat's effects immediately.
- **UPDATE** `character.features` with the chosen Fighting Style.
- Some classes (Fighter) allow replacing the Fighting Style on each level-up; prompt for this when applicable.

---

## Spellcasting Changes on Level-Up

For any class with spellcasting, at each level check:
1. Did spell slot counts change? → **AUTO UPDATE** `character.spellSlots`
2. Did cantrips known increase? → **PROMPT** to choose new cantrip(s) if so
3. Did prepared spell count increase? → Note new max; player updates their prepared list on their next Long Rest (for prepared-from-list casters) OR **PROMPT** for new known spell(s) (for known-spell casters)
4. Did the character unlock a new spell slot tier? → For known-spell casters, they may swap a spell for a higher-level one; PROMPT if applicable

See `spellcasting.md` for full details on how each class handles spells.
