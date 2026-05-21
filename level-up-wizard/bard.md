# BARD Level-Up Wizard

**Hit Die:** d8 (average: 5)
**Spellcasting:** Charisma-based, prepared from full Bard list
**See also:** `spellcasting.md` → Bard section

---

## Universal Steps (every level)
1. **HP:** PROMPT roll d8 or take 5 + Cha modifier → UPDATE `hp.maximum`
2. **Proficiency Bonus:** AUTO update at levels 5/9/13/17
3. **Spell Slots:** AUTO update from Full Caster table
4. **Prepared Spells Max:** AUTO update from class table
5. **Bardic Die:** AUTO update from class table (d6 at 1–4, d8 at 5–9, d10 at 10–14, d12 at 15–20)

---

## Level 1 — Starting Features

### Bardic Inspiration
**AUTO:** Record feature. Uses = Charisma modifier (minimum 1). UPDATE `character.resources.bardicInspiration.uses`.
Die: d6. UPDATE `character.resources.bardicInspiration.die` = d6.

### Spellcasting
**AUTO:** Bard is Charisma-based. Spell attack = Prof + Cha modifier. Spell save DC = 8 + Prof + Cha modifier.
- **PROMPT:** "Choose 2 cantrips from the Bard cantrip list." UPDATE `character.spells.cantrips`.
- **PROMPT:** "Choose 4 spells from the Bard spell list to prepare (max level = [highest slot level])." UPDATE `character.preparedSpells`.
- Note: Musical Instrument is a valid spellcasting focus.

---

## Level 2 — Expertise & Jack of All Trades

### Expertise
**PROMPT:** "Expertise: Choose 2 skill proficiencies to gain Expertise in (your proficiency bonus is doubled for checks with these skills). You must already be proficient in the chosen skills."
- Show only skills the character is already proficient in.
- **UPDATE** both chosen skills to `expertise` status.
- Recalculate their bonuses.

### Jack of All Trades
**AUTO:** Record feature. Add half the Proficiency Bonus (rounded down) to any ability check that doesn't already include the Proficiency Bonus. UPDATE `character.features.jackOfAllTrades`.

**Also at Level 2:**
- **AUTO:** Prepared Spells max → 5.

---

## Level 3 — Bard Subclass

**PROMPT:** "Choose your Bard subclass (Bard College):"
- **College of Dance** — Unarmored Defense (AC = 10 + Dex + Cha), unarmed strikes, movement synergy
- **College of Glamour** — enchantment/illusion, Temp HP, Charming effects
- **College of Lore** — bonus skills, Cutting Words, expanded spell access
- **College of Valor** — Martial weapons/Medium armor, Extra Attack, weapon-as-focus

Apply subclass features immediately. UPDATE `character.subclass`.

#### If College of Dance (Dazzling Footwork):
**AUTO:** Record Unarmored Defense: AC = 10 + Dex modifier + Cha modifier (only while not wearing armor or Shield). UPDATE `character.ac` formula if currently unarmored.

#### If College of Glamour (Beguiling Magic):
**AUTO:** Always have Charm Person and Mirror Image prepared (add to prepared list, don't count against max). UPDATE `character.preparedSpells`.

#### If College of Lore (Bonus Proficiencies):
**PROMPT:** "Bonus Proficiencies: Choose 3 additional skill proficiencies from any skill list."
- Show all 18 skills; player picks 3 they are NOT already proficient in.
- **UPDATE** `character.skills` with the 3 new proficiencies.

#### If College of Valor (Martial Training):
**AUTO:** Gain proficiency in Martial weapons, Medium armor, and Shields. UPDATE `character.proficiencies.weapons`, `character.proficiencies.armor`. Recalculate AC if switching to Medium armor.

**Also at Level 3:**
- **AUTO:** Prepared Spells max → 6. Spell slots gain 2 level 2 slots.

---

## Level 4 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Charisma increases: recalculate Spell Save DC, Spell Attack Bonus, Bardic Inspiration uses (= new Cha modifier, min 1).

**Also at Level 4:**
- **PROMPT:** "You can now know 3 cantrips. Choose 1 new cantrip from the Bard cantrip list." UPDATE `character.spells.cantrips`.
- **AUTO:** Prepared Spells max → 7.

---

## Level 5 — Font of Inspiration

### Font of Inspiration
**AUTO:** Record feature. Bardic Inspiration now recharges on Short or Long Rest (previously Long Rest only). Also, can expend a spell slot to regain one Bardic Inspiration use. UPDATE `character.resources.bardicInspiration` (recharge on Short Rest).

**Also at Level 5:**
- **AUTO:** Proficiency Bonus → +3. Recalculate all dependent values.
- **AUTO:** Bardic Die → d8. UPDATE `character.resources.bardicInspiration.die`.
- **AUTO:** Prepared Spells max → 9. Spell slots gain 2 level 3 slots.
- **PROMPT:** "You gained a new spell level (3rd). Choose 1 spell of 3rd level or lower from the Bard spell list to add to your prepared spells." UPDATE `character.preparedSpells`. *(Only prompt if swapping a spell; Bard's prepared count just increases so player picks which spells to now have prepared.)*

---

## Level 6 — Subclass Feature

#### If College of Dance (Inspiring Movement):
**AUTO:** Record feature. Reaction + Bardic Inspiration die: move half Speed; one ally within 30 ft. can also move.

If College of Dance (Tandem Footwork):
**AUTO:** Record feature. On rolling Initiative, can expend Bardic Inspiration to grant allies a bonus to Initiative.

#### If College of Glamour (Mantle of Majesty):
**AUTO:** Always have Command prepared (add to prepared list, doesn't count against max). UPDATE `character.preparedSpells`.

#### If College of Lore (Magical Discoveries):
**PROMPT:** "Magical Discoveries: Choose 2 spells from the Cleric, Druid, or Wizard spell list. These spells are always prepared and don't count against your max."
- Player may choose any 2 spells from those three lists (of any level they can cast).
- **UPDATE** `character.preparedSpells` — mark these as always-prepared.

#### If College of Valor (Extra Attack):
**AUTO:** Record feature. Character now attacks twice per Attack action. UPDATE `character.features.extraAttack`.

**Also at Level 6:**
- **AUTO:** Prepared Spells max → 10.

---

## Level 7 — Countercharm

**AUTO:** Record feature. Reaction — when you or a nearby creature fails a save vs. Charmed or Frightened, reroll with Advantage.

**Also at Level 7:**
- **AUTO:** Prepared Spells max → 11. Spell slots gain 1 level 4 slot.

---

## Level 8 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Charisma increases: recalculate Spell Save DC, Spell Attack Bonus, Bardic Inspiration uses.

**Also at Level 8:**
- **AUTO:** Prepared Spells max → 12. Spell slots gain 1 additional level 4 slot.

---

## Level 9 — Expertise (2nd)

### Expertise
**PROMPT:** "Expertise: Choose 2 more skill proficiencies to gain Expertise in."
- Show proficient skills that don't already have Expertise.
- **UPDATE** both chosen skills to `expertise` status.

**Also at Level 9:**
- **AUTO:** Proficiency Bonus → +4. Recalculate all dependent values.
- **AUTO:** Prepared Spells max → 14. Spell slots gain 2 level 5 slots.

---

## Level 10 — Magical Secrets

### Magical Secrets
**AUTO:** Record feature. When the prepared spell count increases at this and future levels, new spells can come from the Bard, Cleric, Druid, or Wizard spell lists.

**PROMPT:** "Your Prepared Spells maximum increased. You can now add new prepared spells from the Bard, Cleric, Druid, or Wizard spell lists (up to your max spell level). You have room for [X] new spells."
- UPDATE `character.preparedSpells`.

**Also at Level 10:**
- **PROMPT:** "You can now know 4 cantrips. Choose 1 new cantrip from the Bard cantrip list." UPDATE `character.spells.cantrips`.
- **AUTO:** Bardic Die → d10. UPDATE `character.resources.bardicInspiration.die`.
- **AUTO:** Prepared Spells max → 15.

---

## Level 11 — No New Class Feature

**AUTO:** Prepared Spells max → 16. Spell slots gain 1 level 6 slot.

---

## Level 12 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 12:**
- **AUTO:** Prepared Spells max → 16 (unchanged).

---

## Level 13 — No New Class Feature

**AUTO:** Proficiency Bonus → +5. Recalculate all dependent values.
**AUTO:** Prepared Spells max → 17. Spell slots gain 1 level 7 slot.

---

## Level 14 — Subclass Feature

#### If College of Dance (Leading Evasion):
**AUTO:** Record feature. Evasion on Dexterity saves; can share with adjacent creatures.

#### If College of Glamour (Unbreakable Majesty):
**AUTO:** Record feature. Bonus Action — attackers must make Charisma save or miss their first hit against you per turn.

#### If College of Lore (Peerless Skill):
**AUTO:** Record feature. Can expend Bardic Inspiration after failing an ability check/attack roll to potentially succeed.

#### If College of Valor (Battle Magic):
**AUTO:** Record feature. After casting a spell as an action, make one weapon attack as a Bonus Action.

**Also at Level 14:**
- **AUTO:** Prepared Spells max → 17 (unchanged from 13).

---

## Level 15 — No New Class Feature

**AUTO:** Bardic Die → d12. UPDATE `character.resources.bardicInspiration.die`.
**AUTO:** Prepared Spells max → 18. Spell slots gain 1 level 8 slot.

---

## Level 16 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 16:**
- **AUTO:** Prepared Spells max → 18 (unchanged).

---

## Level 17 — No New Class Feature

**AUTO:** Proficiency Bonus → +6. Recalculate all dependent values.
**AUTO:** Prepared Spells max → 19. Spell slots gain 1 level 9 slot.

---

## Level 18 — Superior Inspiration

**AUTO:** Record feature. On rolling Initiative, regain Bardic Inspiration uses until you have at least 2.

**Also at Level 18:**
- **AUTO:** Prepared Spells max → 20. Spell slots gain 1 additional level 5 slot.

---

## Level 19 — Epic Boon

**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Recommended: Boon of Spell Recall. Choose one:" [list Epic Boon feats]
Apply chosen feat. UPDATE `character.feats`.

**Also at Level 19:**
- **AUTO:** Prepared Spells max → 21. Spell slots: level 6 increases to 2.

---

## Level 20 — Words of Creation

**AUTO:** Record feature. Always have Power Word Heal and Power Word Kill prepared (add to prepared list, don't count against max). When casting either, can target a second creature within 10 ft. of the first. UPDATE `character.preparedSpells`.

**Also at Level 20:**
- **AUTO:** Prepared Spells max → 22. Spell slots: level 7 increases to 2.

---

## Prepared Spells Maximum
Bard's prepared spell count is set by the class table directly (not a formula). Use the class table in `classes/bard.md`.
