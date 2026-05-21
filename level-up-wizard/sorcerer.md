# SORCERER Level-Up Wizard

**Hit Die:** d6 (average: 4)
**Spellcasting:** Charisma-based, known-spell caster (spells known from list, not prepared daily)
**See also:** `spellcasting.md` → Sorcerer section

---

## Universal Steps (every level)
1. **HP:** PROMPT roll d6 or take 4 + Con modifier → UPDATE `hp.maximum`
2. **Proficiency Bonus:** AUTO update at levels 5/9/13/17
3. **Spell Slots:** AUTO update from Full Caster table
4. **Prepared Spells (Known Spells) Max:** AUTO update from class table
5. **Sorcery Points:** AUTO update (= Sorcerer level; 0 at level 1, 2 at level 2, etc.)
6. **Cantrips Known:** AUTO update from class table

---

## Level 1 — Starting Features

### Spellcasting (Sorcerer Knows Spells — No Daily Preparation)
**AUTO:** Sorcerer is Charisma-based. Spell attack = Prof + Cha modifier. Spell save DC = 8 + Prof + Cha modifier.
- **PROMPT:** "Choose 4 cantrips from the Sorcerer cantrip list." UPDATE `character.spells.cantrips` (4 cantrips).
- **PROMPT:** "Choose 2 spells from the Sorcerer spell list to know." UPDATE `character.spells.known`.
- Note: Sorcerers **know** a fixed list of spells and can cast any of them — no daily preparation. Each spell can only be swapped on a level-up.
- Arcane Focus is the spellcasting focus.

### Innate Sorcery
**AUTO:** Record feature. 2 uses per Long Rest. Bonus Action to activate for 1 minute: Spell save DC +1, Advantage on Sorcerer spell attack rolls. UPDATE `character.resources.innateSorcery.uses` = 2.

---

## Level 2 — Font of Magic & Metamagic

### Font of Magic
**AUTO:** Record feature. Gain 2 Sorcery Points. UPDATE `character.resources.sorceryPoints.max` = 2.
Record Sorcery Point conversion rules:
- Points → Spell Slots: 1 SP = lvl 1, 3 SP = lvl 2, 5 SP = lvl 3, 6 SP = lvl 4, 7 SP = lvl 5 (max level 5).
- Spell Slots → Points: Expend a slot to gain SP equal to the slot's level.

### Metamagic
**PROMPT:** "Metamagic: Choose 2 Metamagic options to learn from the following list:"
- Careful Spell (1 SP): Up to Cha modifier creatures auto-succeed on saves
- Distant Spell (1 SP): Double range or change Touch to 30 ft.
- Empowered Spell (1 SP): Reroll up to Cha modifier damage dice
- Extended Spell (1 SP): Double duration (max 24 hours); Advantage on Concentration saves
- Heightened Spell (2 SP): One target has Disadvantage on saves
- Quickened Spell (2 SP): Change action cast time to Bonus Action (no level 1+ spell same turn)
- Seeking Spell (1 SP): Reroll a missed attack roll spell
- Subtle Spell (1 SP): Cast without Verbal, Somatic, or unconsumed Material components
- Transmuted Spell (1 SP): Change damage type among Acid, Cold, Fire, Lightning, Poison, Thunder
- Twinned Spell (1 SP): Increase spell's effective level by 1 to target an additional creature

**UPDATE** `character.features.metamagic` with the 2 chosen options.

**Also at Level 2:**
- **PROMPT:** "You can swap 1 known spell. Would you like to swap a spell from your known list for a different Sorcerer spell of the same level or lower?" If yes: UPDATE `character.spells.known`.
- **AUTO:** Known Spells max → 4. PROMPT to choose 2 new spells. UPDATE `character.spells.known`.

---

## Level 3 — Sorcerer Subclass

**PROMPT:** "Choose your Sorcerer subclass (Sorcerous Origin):"
- **Aberrant Sorcery** — psionic spells, telepathic speech, cast via SP instead of slots
- **Clockwork Sorcery** — balance/order spells, cancel Advantage/Disadvantage, ward absorption
- **Draconic Sorcery** — Draconic Spells, HP increase, Unarmored Defense (10 + Dex + Cha)
- **Wild Magic Sorcery** — Wild Magic Surges, Tides of Chaos, unpredictable effects

Apply subclass features immediately. UPDATE `character.subclass`.

#### Aberrant Sorcery — Psionic Spells & Telepathic Speech:
**AUTO:** Record Psionic Spells (always prepared, from subclass list at levels 3, 5, 7, 9; see `classes/sorcerer.md`). Mark first tier as always-prepared at level 3: Arms of Hadar, Dissonant Whispers, Mind Sliver.
**AUTO:** Bonus Action — telepathic link with one creature for Sorcerer level minutes.

#### Clockwork Sorcery — Clockwork Spells & Restore Balance:
**AUTO:** Record Clockwork Spells at level 3: Aid, Alarm, Lesser Restoration, Protection from Evil and Good. Mark as always-prepared. UPDATE `character.preparedSpells`.
**AUTO:** Restore Balance uses = Cha modifier. UPDATE `character.resources.restoreBalance.uses`.

#### Draconic Sorcery — Draconic Resilience:
**AUTO:** Record feature. HP max increases by 3, then +1 per additional Sorcerer level gained.
- **UPDATE:** `hp.maximum` += 3 immediately (at level 3). Note: each future level-up adds +1 extra on top of the standard die roll.
- **UPDATE:** Unarmored Defense — when not wearing armor: AC = 10 + Dex modifier + Cha modifier. UPDATE `character.ac` formula.

#### Wild Magic Sorcery — Wild Magic Surge & Tides of Chaos:
**AUTO:** Record Wild Magic Surge (after casting with a slot, may roll d20; on 20, roll on Wild Magic Surge table).
**AUTO:** Record Tides of Chaos (gain Advantage on one D20 Test; must cast a spell or Long Rest to reuse).

**Also at Level 3:**
- **AUTO:** Sorcery Points → 3.
- **AUTO:** Known Spells max → 6. **PROMPT:** "Choose 2 new spells from the Sorcerer spell list to know (max level = your highest slot level)." UPDATE `character.spells.known`.
- **PROMPT:** "You may swap 1 known spell for a different Sorcerer spell." UPDATE if swapping.
- **AUTO:** Spell slots → 4/2 (gain level 2 slots).

---

## Level 4 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Charisma increases: recalculate Spell Save DC, Spell Attack Bonus.

**Also at Level 4:**
- **AUTO:** Sorcery Points → 4.
- **AUTO:** Known Spells max → 7. **PROMPT:** "Choose 1 new spell from the Sorcerer spell list to know." UPDATE `character.spells.known`.
- **PROMPT:** "You may swap 1 known spell." UPDATE if swapping.
- **PROMPT:** "You can now know 5 cantrips. Choose 1 new cantrip." UPDATE `character.spells.cantrips`.

---

## Level 5 — Sorcerous Restoration

**AUTO:** Record feature. On Short Rest, regain up to half Sorcerer level (round down) Sorcery Points. Once per Long Rest.

**Also at Level 5:**
- **AUTO:** Proficiency Bonus → +3. Recalculate all dependent values.
- **AUTO:** Sorcery Points → 5.
- **AUTO:** Known Spells max → 9. **PROMPT:** "Choose 2 new spells from the Sorcerer spell list to know." UPDATE `character.spells.known`.
- **PROMPT:** "You may swap 1 known spell." UPDATE if swapping.
- **AUTO:** Spell slots → 4/3/2 (gain level 3 slots).
- **Subclass Spells (Tier 2, where applicable):** Add next set of subclass always-prepared spells.
  - Aberrant: Detect Thoughts, Calm Emotions
  - Clockwork: Dispel Magic, Protection from Energy
  - Draconic: Command, Dragon's Breath, Fear, Fly (all 4 Draconic Spells at level 3 tier and level 5 tier)
  - Wild Magic: No additional spells
  UPDATE `character.preparedSpells` for applicable subclasses.

---

## Level 6 — Subclass Feature

#### Aberrant Sorcery (Psionic Sorcery & Psychic Defenses):
**AUTO:** Record Psionic Sorcery (cast Psionic Spells by spending SP = spell level instead of a slot; no V/S).
**AUTO:** Record Psychic Defenses: Resistance to Psychic; Advantage on saves vs. Charmed/Frightened.

#### Clockwork Sorcery (Bastion of Law):
**AUTO:** Record feature. Magic Action + 1–5 SP — create a ward on a creature (d8s = SP spent) absorbing damage.

#### Draconic Sorcery (Elemental Affinity):
**PROMPT:** "Elemental Affinity: Choose one damage type to be your Draconic Affinity:"
- Acid, Cold, Fire, Lightning, Poison
- **UPDATE** `character.features.elementalAffinity.type`.
- Gain Resistance to that damage type. UPDATE `character.resistances`.
- Add Cha modifier to one damage roll of spells dealing that damage type per turn.

#### Wild Magic Sorcery (Bend Luck):
**AUTO:** Record feature. Reaction + 1 SP — roll 1d4 and add or subtract it from another creature's D20 Test.

**Also at Level 6:**
- **AUTO:** Sorcery Points → 6.
- **AUTO:** Known Spells max → 10. **PROMPT:** "Choose 1 new spell." UPDATE `character.spells.known`.
- **PROMPT:** "You may swap 1 known spell." UPDATE if swapping.

---

## Level 7 — Sorcery Incarnate

**AUTO:** Record feature. Spend 2 SP to activate Innate Sorcery when out of uses. While Innate Sorcery is active, can use up to two Metamagic options per spell (normally one).

**Also at Level 7:**
- **AUTO:** Sorcery Points → 7.
- **AUTO:** Known Spells max → 11. **PROMPT:** "Choose 1 new spell." UPDATE `character.spells.known`.
- **AUTO:** Spell slots → 4/3/3/1 (gain level 4 slot).
- **Subclass Spells (Tier 3):**
  - Aberrant: Hunger of Hadar, Sending
  - Clockwork: Freedom of Movement, Summon Construct
  - Draconic: Arcane Eye, Charm Monster
  UPDATE `character.preparedSpells`.

---

## Level 8 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 8:**
- **AUTO:** Sorcery Points → 8.
- **AUTO:** Known Spells max → 12. **PROMPT:** "Choose 1 new spell." UPDATE `character.spells.known`.
- **PROMPT:** "You may swap 1 known spell." UPDATE if swapping.

---

## Level 9 — No New Class Feature

**AUTO:** Proficiency Bonus → +4.
**AUTO:** Sorcery Points → 9.
**AUTO:** Known Spells max → 14. **PROMPT:** "Choose 2 new spells." UPDATE `character.spells.known`.
**AUTO:** Spell slots → 4/3/3/3/1 (gain level 5 slot).
- **Subclass Spells (Tier 4):**
  - Aberrant: Rary's Telepathic Bond, Telekinesis
  - Clockwork: Greater Restoration, Wall of Force
  - Draconic: Legend Lore, Summon Dragon
  UPDATE `character.preparedSpells`.

---

## Level 10 — Metamagic (2 more options)

**PROMPT:** "Metamagic: Choose 2 additional Metamagic options to learn from the list."
- Show the full Metamagic list; exclude options already known.
- **UPDATE** `character.features.metamagic` with the 2 new options.

**Also at Level 10:**
- **AUTO:** Sorcery Points → 10.
- **AUTO:** Known Spells max → 15. **PROMPT:** "Choose 1 new spell." UPDATE `character.spells.known`.
- **PROMPT:** "You may swap 1 known spell." UPDATE if swapping.
- **PROMPT:** "You can now know 6 cantrips. Choose 1 new cantrip." UPDATE `character.spells.cantrips`.
- **AUTO:** Spell slots → 4/3/3/3/2.

---

## Levels 11–13 — Resource Scaling

At each of these levels:
- AUTO update Sorcery Points (11, 12, 13).
- AUTO update Known Spells from table. PROMPT for each new spell known.
- PROMPT to optionally swap 1 known spell.
- AUTO update Spell Slots from Full Caster table (level 11: gain level 6 slot; level 13: gain level 7 slot).

---

## Level 14 — Subclass Feature

#### Aberrant Sorcery (Revelation in Flesh):
**AUTO:** Record feature. Bonus Action + SP (1 SP per benefit) — alter body for 10 minutes: Aquatic Adaptation, Glistening Flight, See the Invisible, or Wormlike Movement.

#### Clockwork Sorcery (Trance of Order):
**AUTO:** Record feature. Bonus Action for 1 minute — attacks against you can't benefit from Advantage; treat d20 rolls ≤9 as 10.

#### Draconic Sorcery (Dragon Wings):
**AUTO:** Record feature. Bonus Action — gain 60-ft. Fly Speed for 1 hour. Once per Long Rest or 3 SP. UPDATE `character.speed.fly` (conditional).

#### Wild Magic Sorcery (Controlled Chaos):
**AUTO:** Record feature. Roll twice on Wild Magic Surge table and choose either result.

---

## Levels 15–17 — Resource Scaling

Continue updating Sorcery Points, Known Spells, Spell Slots per Universal Steps and class table.
- Level 15: Spell slots gain level 8 slot.
- Level 17: Gain 2 more Metamagic options (see Level 17 below).
- Level 17: Spell slots gain level 9 slot.

---

## Level 17 — Metamagic (2 more options)

**PROMPT:** "Metamagic: Choose 2 more Metamagic options to learn from the list."
- Show remaining unchosen Metamagic options.
- **UPDATE** `character.features.metamagic`.

**Also at Level 17:**
- **AUTO:** Proficiency Bonus → +6.

---

## Level 18 — Subclass Feature (Capstone)

#### Aberrant Sorcery (Warping Implosion):
**AUTO:** Record feature. Magic Action — teleport 120 ft.; creatures in previous space make Strength save or take 3d10 Force damage and get pulled to that space.

#### Clockwork Sorcery (Clockwork Cavalcade):
**AUTO:** Record feature. Magic Action — spectral Construct spirits appear in 30-ft. Cube: heal up to 100 HP total, repair damaged objects, end spells of level 6 or lower.

#### Draconic Sorcery (Dragon Companion):
**AUTO:** Record feature. Cast Summon Dragon without material components or a slot once per Long Rest; can make it non-Concentration (lasts 1 minute).

#### Wild Magic Sorcery (Tamed Surge):
**AUTO:** Record feature. After casting with a slot, choose any Wild Magic Surge effect instead of rolling. Once per Long Rest.

---

## Level 19 — Epic Boon

**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Recommended: Boon of Dimensional Travel. Choose one:" [list Epic Boon feats]
Apply chosen feat. UPDATE `character.feats`.

---

## Level 20 — Arcane Apotheosis

**AUTO:** Record feature. While Innate Sorcery is active, use one Metamagic option per turn for free (no SP cost).

---

## Known Spells vs. Prepared Spells — IMPORTANT
Sorcerer spells are **known**, not **prepared daily**. This means:
- The character always has all their known spells available — no morning preparation ritual.
- On each level-up, the player may swap exactly ONE known spell for another valid Sorcerer spell.
- When the Known Spells maximum increases, the player immediately chooses new spells to add.
- Subclass spells (Psionic Spells, Clockwork Spells, Draconic Spells) are always prepared separately and are NOT counted against the Known Spells maximum.
