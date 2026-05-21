# WIZARD Level-Up Wizard

**Hit Die:** d6 (average: 4)
**Spellcasting:** Intelligence-based, prepared from spellbook
**See also:** `spellcasting.md` → Wizard section

---

## Universal Steps (every level)
1. **HP:** PROMPT roll d6 or take 4 + Con modifier → UPDATE `hp.maximum`
2. **Proficiency Bonus:** AUTO update at levels 5/9/13/17
3. **Spell Slots:** AUTO update from Full Caster table (see `rules/spell-slots.md`)
4. **Prepared Spells Max:** AUTO update from class table (level 1→4, 2→5, 3→6, etc.)
5. **Spellbook:** At every level gained after 1st, the wizard adds 2 spells of any level they can cast to their spellbook for free. **PROMPT:** "Choose 2 spells to add to your spellbook. You may choose any Wizard spells of levels you have slots for."  UPDATE `character.spellbook`.

---

## Level 1 — Starting Features

### Spellcasting
**AUTO:** Wizard is Intelligence-based. Spell attack = Prof + Int modifier. Spell save DC = 8 + Prof + Int modifier.
- **PROMPT (if not already done at character creation):** "Choose 3 cantrips from the Wizard cantrip list."
  - UPDATE `character.spells.cantrips` (3 cantrips)
- **AUTO:** Spellbook starts with 6 level 1 spells. **PROMPT:** "Choose 6 level 1 spells for your starting spellbook." UPDATE `character.spellbook`.
- **PROMPT:** "Choose 4 spells from your spellbook to prepare." UPDATE `character.preparedSpells`.
- **AUTO:** Spellcasting focus: Arcane Focus or spellbook.

### Ritual Adept
**AUTO:** No choice required. Record feature. Can cast any Ritual spell from spellbook without preparing it (must have book in hand).

### Arcane Recovery
**AUTO:** No choice required. Record feature. Once per Long Rest, on Short Rest recover spell slots totaling up to half Wizard level (rounded up); no recovered slot above level 5.

---

## Level 2 — Scholar

### Scholar
**PROMPT:** "Scholar: Choose one skill to gain Expertise in (your proficiency bonus is doubled for checks with this skill). You must already be proficient in the chosen skill."
- Options (only show skills the character is already proficient in): Arcana, History, Investigation, Medicine, Nature, Religion
- If the character is not proficient in any of those skills, show all options and note the character gains proficiency + expertise.
- **UPDATE** the chosen skill: set proficiency status to `expertise` (double proficiency bonus applies to checks).
- Recalculate the skill's total bonus.

**Also at Level 2:**
- **AUTO:** Prepared Spells max increases to 5. Player may update their prepared list on next Long Rest.
- **AUTO:** Add 2 spells to spellbook (see Universal Steps).

---

## Level 3 — Wizard Subclass

### Subclass Selection
**PROMPT:** "Choose your Wizard subclass (Arcane Tradition):"
- **Abjurer** — defensive specialist, wards and counter-magic
- **Diviner** — foresight, d20 replacement with Portent dice
- **Evoker** — maximum damage, sculpt spells to protect allies
- **Illusionist** — illusion expert, castings without Verbal components

Apply subclass features immediately (see below). UPDATE `character.subclass`.

#### If Abjurer:
- **AUTO (Abjuration Savant):** Add two Abjuration spells (levels 0–2) to spellbook for free. **PROMPT:** "Choose 2 Abjuration spells (levels 0–2) to add to your spellbook for free." UPDATE `character.spellbook`.
- **AUTO (Arcane Ward):** Record feature. Ward activates when casting an Abjuration spell using a spell slot. Initial HP = 2× Wizard level + Int modifier = [calculated value]. UPDATE `character.features.arcaneWard`.

#### If Diviner:
- **AUTO (Divination Savant):** Add two Divination spells (levels 0–2) to spellbook for free. **PROMPT:** "Choose 2 Divination spells (levels 0–2) to add to your spellbook for free." UPDATE `character.spellbook`.
- **AUTO (Portent):** Record feature. After each Long Rest, roll 2d20 and record results. They replace any d20 roll made by you or a visible creature (each used once).

#### If Evoker:
- **AUTO (Evocation Savant):** Add two Evocation spells (levels 0–2) to spellbook for free. **PROMPT:** "Choose 2 Evocation spells (levels 0–2) to add to your spellbook for free." UPDATE `character.spellbook`.
- **AUTO (Potent Cantrip):** Record feature. Missed cantrip attacks and successful saves against your cantrips still deal half damage.

#### If Illusionist:
- **AUTO (Illusion Savant):** Add two Illusion spells (levels 0–2) to spellbook for free. **PROMPT:** "Choose 2 Illusion spells (levels 0–2) to add to your spellbook for free." UPDATE `character.spellbook`.
- **AUTO (Improved Illusions):** Record feature. Gain Minor Illusion as a cantrip (Wizard cantrip, Int-based) if not already known. UPDATE `character.spells.cantrips` if Minor Illusion added.

**Also at Level 3:**
- **AUTO:** Prepared Spells max → 6.
- **AUTO:** Add 2 spells to spellbook.
- **AUTO:** Spell slots update (gain 4 level 1 slots, 2 level 2 slots).

---

## Level 4 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Intelligence increases: recalculate Spell Save DC and Spell Attack Bonus, Prepared Spells max (= Int modifier + Wizard level).

**Also at Level 4:**
- **PROMPT:** "You can now know 4 cantrips. Choose 1 new cantrip from the Wizard cantrip list." UPDATE `character.spells.cantrips`.
- **AUTO:** Prepared Spells max → 7.
- **AUTO:** Add 2 spells to spellbook.

---

## Level 5 — Memorize Spell

### Memorize Spell
**AUTO:** Record feature. After a Short Rest, the wizard may swap one prepared spell for another from their spellbook. No prompt needed at level-up; this is a gameplay feature.

**Also at Level 5:**
- **AUTO:** Proficiency Bonus increases to +3. Recalculate all dependent values.
- **AUTO:** Prepared Spells max → 9.
- **AUTO:** Spell slots update (gain 2 level 3 slots).
- **AUTO:** Add 2 spells to spellbook.

---

## Level 6 — Subclass Feature

#### If Abjurer (Projected Ward):
**AUTO:** Record feature. Can use Reaction to have Arcane Ward absorb damage for a creature within 30 ft.

#### If Diviner (Expert Divination):
**AUTO:** Record feature. Casting a Divination spell with a level 2+ slot regains one lower-level expended slot (max level 5).

#### If Evoker (Sculpt Spells):
**AUTO:** Record feature. When casting an Evocation spell, up to 1 + spell level creatures auto-succeed on saves and take no damage.

#### If Illusionist (Phantasmal Creatures):
**AUTO:** Record feature. Always have Summon Beast and Summon Fey prepared (add to prepared list, they don't count against the max). UPDATE `character.preparedSpells` to mark these as always-prepared.

**Also at Level 6:**
- **AUTO:** Prepared Spells max → 10.
- **AUTO:** Spell slots update (gain 1 additional level 3 slot → 3 total).
- **AUTO:** Add 2 spells to spellbook.

---

## Level 7 — No New Class Feature

**AUTO:** Prepared Spells max → 11.
**AUTO:** Add 2 spells to spellbook.

---

## Level 8 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Intelligence increases: recalculate Spell Save DC, Spell Attack Bonus, Prepared Spells max.

**Also at Level 8:**
- **AUTO:** Prepared Spells max → 12.
- **AUTO:** Spell slots update (gain level 4 slot).
- **AUTO:** Add 2 spells to spellbook.

---

## Level 9 — No New Class Feature

**AUTO:** Proficiency Bonus increases to +4. Recalculate all dependent values.
**AUTO:** Prepared Spells max → 14.
**AUTO:** Spell slots update (gain level 5 slot; 3 total level 3 slots, 1 level 5 slot).
**AUTO:** Add 2 spells to spellbook.

---

## Level 10 — Subclass Feature

#### If Abjurer (Spell Breaker):
**AUTO:** Always have Counterspell and Dispel Magic prepared (add to prepared list, don't count against max). UPDATE `character.preparedSpells`.

#### If Diviner (The Third Eye):
**AUTO:** Record feature. Bonus Action to choose Darkvision 120 ft., read any language, or cast See Invisibility; lasts until Short/Long Rest.

#### If Evoker (Empowered Evocation):
**AUTO:** Record feature. Add Intelligence modifier to one damage roll of any Wizard Evocation spell.

#### If Illusionist (Illusory Self):
**AUTO:** Record feature. Reaction to make an attack that would hit you miss instead; once per Short/Long Rest or expend a level 2+ slot.

**Also at Level 10:**
- **PROMPT:** "You can now know 5 cantrips. Choose 1 new cantrip from the Wizard cantrip list." UPDATE `character.spells.cantrips`.
- **AUTO:** Prepared Spells max → 15.
- **AUTO:** Spell slots update (2 level 5 slots).
- **AUTO:** Add 2 spells to spellbook.

---

## Level 11 — No New Class Feature

**AUTO:** Prepared Spells max → 16.
**AUTO:** Spell slots update (gain 1 level 6 slot).
**AUTO:** Add 2 spells to spellbook.

---

## Level 12 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Intelligence increases: recalculate Spell Save DC, Spell Attack Bonus, Prepared Spells max.

**Also at Level 12:**
- **AUTO:** Prepared Spells max → 16 (unchanged from 11).
- **AUTO:** Add 2 spells to spellbook.

---

## Level 13 — No New Class Feature

**AUTO:** Proficiency Bonus increases to +5. Recalculate all dependent values.
**AUTO:** Prepared Spells max → 17.
**AUTO:** Spell slots update (gain 1 level 7 slot).
**AUTO:** Add 2 spells to spellbook.

---

## Level 14 — Subclass Feature

#### If Abjurer (Spell Resistance):
**AUTO:** Record feature. Advantage on saves vs. spells; Resistance to spell damage.

#### If Diviner (Greater Portent):
**AUTO:** Record feature. Portent now rolls three d20s instead of two after Long Rest.

#### If Evoker (Overchannel):
**AUTO:** Record feature. When casting a Wizard spell using a slot of level 1–5, deal maximum damage (first use per Long Rest is free; subsequent uses deal Necrotic damage to self).

#### If Illusionist (Illusory Reality):
**AUTO:** Record feature. When casting an Illusion spell using a slot, can use Bonus Action to make one inanimate object part of the illusion real for 1 minute.

**Also at Level 14:**
- **AUTO:** Prepared Spells max → 18.
- **AUTO:** Add 2 spells to spellbook.

---

## Level 15 — No New Class Feature

**AUTO:** Prepared Spells max → 19.
**AUTO:** Spell slots update (gain 1 level 8 slot).
**AUTO:** Add 2 spells to spellbook.

---

## Level 16 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 16:**
- **AUTO:** Prepared Spells max → 21.
- **AUTO:** Add 2 spells to spellbook.

---

## Level 17 — No New Class Feature

**AUTO:** Proficiency Bonus increases to +6. Recalculate all dependent values.
**AUTO:** Prepared Spells max → 22.
**AUTO:** Spell slots update (gain 1 level 9 slot).
**AUTO:** Add 2 spells to spellbook.

---

## Level 18 — Spell Mastery

### Spell Mastery
**PROMPT:** "Spell Mastery: Choose one level 1 spell and one level 2 spell from your spellbook. These spells are always prepared and can be cast at their lowest level without expending a spell slot. You may change your choices on each Long Rest."
- Show the player their current spellbook contents, filtered to levels 1 and 2.
- **UPDATE** `character.features.spellMastery` with the two chosen spells.
- Mark those two spells as "always prepared / free cast at lowest level."

**Also at Level 18:**
- **AUTO:** Prepared Spells max → 23.
- **AUTO:** Spell slots update (level 5 slots increase to 3).
- **AUTO:** Add 2 spells to spellbook.

---

## Level 19 — Epic Boon

### Epic Boon
**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Recommended: Boon of Spell Recall. Choose one:"
[List all Epic Boon feats from `reference_claude/feats/epic-boon/`]
Apply chosen feat's effects. UPDATE `character.feats`.

**Also at Level 19:**
- **AUTO:** Prepared Spells max → 24.
- **AUTO:** Spell slots update (level 6 slots increase to 2).
- **AUTO:** Add 2 spells to spellbook.

---

## Level 20 — Signature Spells

### Signature Spells
**PROMPT:** "Signature Spells: Choose two level 3 spells from your spellbook. These spells are always prepared and can each be cast once at level 3 without expending a spell slot per Short or Long Rest."
- Show the player their spellbook contents, filtered to level 3 spells.
- **UPDATE** `character.features.signatureSpells` with the two chosen spells.
- Mark those spells as "always prepared / free cast at level 3 (1/rest each)."

**Also at Level 20:**
- **AUTO:** Prepared Spells max → 25.
- **AUTO:** Spell slots update (level 7 slots increase to 2).
- **AUTO:** Add 2 spells to spellbook.

---

## Prepared Spells Maximum Formula
`Prepared Spells Max = Wizard Level + Intelligence Modifier`

Recalculate whenever Wizard level or Intelligence modifier changes.
