# DRUID Level-Up Wizard

**Hit Die:** d8 (average: 5)
**Spellcasting:** Wisdom-based, prepared from full Druid list
**See also:** `spellcasting.md` → Druid section

---

## Universal Steps (every level)
1. **HP:** PROMPT roll d8 or take 5 + Wis modifier → UPDATE `hp.maximum`
2. **Proficiency Bonus:** AUTO update at levels 5/9/13/17
3. **Spell Slots:** AUTO update from Full Caster table
4. **Prepared Spells Max:** AUTO update from class table
5. **Wild Shape Uses:** AUTO update from class table (—, 2, 2, 2, 2, 3 ... 4 at level 18+)

---

## Level 1 — Starting Features

### Spellcasting
**AUTO:** Druid is Wisdom-based. Spell attack = Prof + Wis modifier. Spell save DC = 8 + Prof + Wis modifier.
- **PROMPT:** "Choose 2 cantrips from the Druid cantrip list." UPDATE `character.spells.cantrips`.
- **AUTO:** Prepared Spells max = Druid level + Wisdom modifier.
- **PROMPT:** "Choose [max] spells from the Druid spell list to prepare." UPDATE `character.preparedSpells`.
- Druidic Focus or Herbalism Kit is the spellcasting focus.
- **AUTO:** Speak with Animals is always prepared (from Druidic feature). Mark it as always-prepared; doesn't count against max.

### Druidic
**AUTO:** Record feature. Knows Druidic secret language. Speak with Animals is always prepared (see above).

### Primal Order
**PROMPT:** "Primal Order: Choose one of the following:"
- **Magician** — Gain one additional Druid cantrip. Add Wisdom modifier to Arcana and Nature checks.
- **Warden** — Gain proficiency with Martial weapons and Medium armor.

If **Magician**:
- **PROMPT:** "Choose 1 additional cantrip from the Druid cantrip list." UPDATE `character.spells.cantrips` (3 total at level 1).
- **UPDATE** `character.features.primalOrderMagician` — Wis modifier applies to Arcana and Nature skill checks.
- Recalculate Arcana and Nature skill bonuses.

If **Warden**:
- **UPDATE** `character.proficiencies.weapons` — add Martial weapons.
- **UPDATE** `character.proficiencies.armor` — add Medium armor.
- Recalculate AC if switching to Medium armor.

---

## Level 2 — Wild Shape & Wild Companion

### Wild Shape
**AUTO:** Record feature. 2 uses per Long Rest. UPDATE `character.resources.wildShape.uses` = 2.

**PROMPT:** "Wild Shape: You can transform into Beast forms you've seen. Your starting options are limited to CR 1/4 (no Fly Speed). Choose up to 4 Beast forms to record."
- Suggestions: Giant Rat (CR 1/8), Mastiff (CR 1/8), Black Bear (CR 1/2 — wait, that's CR 1/2, not 1/4, so not yet available). Typical CR 1/4 beasts: Constrictor Snake, Panther, Wolf, Giant Badger.
- UPDATE `character.wildShapeForms` with chosen forms.
- Note: Players can add forms any time they encounter and study a new Beast.

### Wild Companion
**AUTO:** Record feature. Can expend a spell slot or Wild Shape use to cast Find Familiar (familiar is Fey, disappears on Long Rest).

**Also at Level 2:**
- **AUTO:** Prepared Spells max → 2 + Wis modifier.

---

## Level 3 — Druid Subclass

**PROMPT:** "Choose your Druid subclass (Druid Circle):"
- **Circle of the Land** — terrain-based bonus spells, Natural Recovery, healing/necrotic area
- **Circle of the Moon** — powerful combat Wild Shape, high CR beasts, Radiant attacks
- **Circle of the Sea** — elemental/weather spells, Wrath of the Sea aura
- **Circle of the Stars** — starry form (Archer/Chalice/Dragon options), Guiding Bolt access

Apply subclass features immediately. UPDATE `character.subclass`.

#### Circle of the Land — Circle of the Land Spells:
**PROMPT:** "Circle of the Land: Choose a terrain type. On each Long Rest you may choose a different terrain. For now, choose your starting terrain:"
- **Arid** (desert)
- **Polar** (arctic/tundra)
- **Temperate** (forest/grassland)
- **Tropical** (jungle/coast)
- UPDATE `character.features.circleOfTheLand.currentTerrain` and apply terrain's bonus spells as always-prepared.

**PROMPT:** "Land's Aid: Record this Channel Divinity option." (Uses Wild Shape uses, not Channel Divinity.)

#### Circle of the Moon — Circle Forms:
**AUTO:** Wild Shape max CR = Druid level ÷ 3 (round down, min 1) = CR 1 at level 3. Temp HP from Wild Shape = 3× Druid level.
**AUTO:** Record Circle of the Moon spells as always-prepared: Cure Wounds, Moonbeam, Starry Wisp. UPDATE `character.preparedSpells`.

#### Circle of the Sea — Circle of the Sea Spells:
**AUTO:** Always have Fog Cloud, Gust of Wind, Ray of Frost, Shatter, Thunderwave prepared. UPDATE `character.preparedSpells`.

#### Circle of the Stars — Star Map & Starry Form:
**AUTO:** Always have Guidance and Guiding Bolt prepared. UPDATE `character.preparedSpells`.
Guiding Bolt uses without slot = Wisdom modifier. UPDATE `character.resources.guidingBolt`.

**PROMPT:** "Starry Form: When you expend a Wild Shape use to enter Starry Form, you'll choose a constellation. The options are: Archer (ranged Radiant attack each turn), Chalice (heal when casting a healing spell), or Dragon (treat d20 results of 9 or lower as 10 for Int/Wis checks and Con saves). You choose each time you activate Starry Form."
- No permanent choice — record all three options.

**Also at Level 3:**
- **AUTO:** Prepared Spells max → 3 + Wis modifier. Spell slots gain 2 level 2 slots.

---

## Level 4 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Wisdom increases: recalculate Spell Save DC, Spell Attack Bonus, Prepared Spells max.

**Also at Level 4:**
- **PROMPT:** "You can now know 3 cantrips. Choose 1 new cantrip from the Druid cantrip list." UPDATE `character.spells.cantrips`.
- **AUTO:** Prepared Spells max → 4 + Wis modifier.
- **AUTO:** Wild Shape max CR → 1/2. Wild Shape known forms can now include CR 1/2 beasts (no Fly Speed still).
- **PROMPT:** "Wild Shape: You can now use CR 1/2 Beast forms. Would you like to record any new forms?" UPDATE `character.wildShapeForms`.

---

## Level 5 — Wild Resurgence

**AUTO:** Record feature. Can give yourself one Wild Shape use by expending a spell slot (once per turn). Or expend a Wild Shape use for a level 1 spell slot (once per Long Rest).

**Also at Level 5:**
- **AUTO:** Proficiency Bonus → +3. Recalculate all dependent values.
- **AUTO:** Prepared Spells max → 5 + Wis modifier. Spell slots gain 2 level 3 slots.

---

## Level 6 — Subclass Feature

#### Circle of the Land (Natural Recovery):
**AUTO:** Record feature. Can cast one Circle Spell without a slot (once per Long Rest). Recover spell slots on Short Rest (combined level ≤ half Druid level, no level 6+).

#### Circle of the Moon (Improved Circle Forms):
**AUTO:** Record feature. Each attack in Wild Shape can deal Radiant damage; add Wis modifier to Con saves.

#### Circle of the Sea (Aquatic Affinity):
**AUTO:** Record feature. Wrath of the Sea Emanation grows to 10 ft.; gain Swim Speed = Speed. UPDATE `character.speed` to include Swim Speed.

#### Circle of the Stars (Cosmic Omen):
**AUTO:** Record feature. Roll a die after Long Rest; gain Weal (+1d6 to D20 Tests as Reaction) or Woe (−1d6) uses = Wisdom modifier. UPDATE `character.resources.cosmicOmen`.

**Also at Level 6:**
- **AUTO:** Wild Shape uses → 3. UPDATE `character.resources.wildShape.uses`.
- **AUTO:** Prepared Spells max → 6 + Wis modifier.

---

## Level 7 — Elemental Fury

### Elemental Fury
**PROMPT:** "Elemental Fury: Choose one of the following:"
- **Potent Spellcasting** — Add your Wisdom modifier to damage rolls from Druid cantrips.
- **Primal Strike** — Once per turn, when you hit with a weapon attack or Wild Shape attack, deal extra 1d8 Acid, Cold, Fire, Lightning, or Thunder damage (your choice of type).

**UPDATE** `character.features.elementalFury` with the chosen option.

**Also at Level 7:**
- **AUTO:** Prepared Spells max → 7 + Wis modifier. Spell slots gain 1 level 4 slot.

---

## Level 8 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Wisdom increases: recalculate Spell Save DC, Spell Attack Bonus, Prepared Spells max.

**Also at Level 8:**
- **AUTO:** Wild Shape max CR → 1 (with Fly Speed). Wild Shape known forms can now include CR 1 beasts and beasts with Fly Speeds.
- **PROMPT:** "Wild Shape: You can now use CR 1 Beast forms with Fly Speeds. Would you like to record any new forms?" UPDATE `character.wildShapeForms`.
- **AUTO:** Prepared Spells max → 8 + Wis modifier. Spell slots gain 1 additional level 4 slot.

---

## Level 9 — Subclass Feature

#### Circle of the Land (Nature's Ward):
**PROMPT:** "Nature's Ward: You are immune to Poisoned. Choose one damage type Resistance based on your current land type:"
- Arid: Fire
- Polar: Cold
- Temperate: Lightning
- Tropical: Poison
(This changes when the land type changes on Long Rest.)
UPDATE `character.resistances` with relevant type.

#### Circle of the Moon (Moonlight Step):
**AUTO:** Record feature. Bonus Action — teleport 30 ft. with Advantage on next attack. Uses = Wisdom modifier. UPDATE `character.resources.moonlightStep`.

#### Circle of the Sea (Control Water, Ice Storm now always-prepared):
**AUTO:** Add Control Water and Ice Storm to always-prepared. UPDATE `character.preparedSpells`.

#### Circle of the Stars (Twinkling Constellations):
**AUTO:** Record upgrade. Archer/Chalice dice become 2d8; Dragon grants 20-ft. Fly Speed. Can change constellation each turn.

**Also at Level 9:**
- **AUTO:** Proficiency Bonus → +4. Recalculate all dependent values.
- **AUTO:** Prepared Spells max → 9 + Wis modifier. Spell slots gain 2 level 5 slots.

---

## Level 10 — No New Class Feature

**PROMPT:** "You can now know 4 cantrips. Choose 1 new cantrip from the Druid cantrip list." UPDATE `character.spells.cantrips`.
**AUTO:** Prepared Spells max → 10 + Wis modifier. Spell slots: level 5 increases to 2.

---

## Level 11 — Subclass Feature

#### Circle of the Land (Nature's Sanctuary):
**AUTO:** Record feature. Expend Wild Shape — create 15-ft. Cube of spectral trees (moveable as Bonus Action), granting Half Cover; allies share Nature's Ward Resistance.

#### Circle of the Moon (Lunar Form):
**AUTO:** Record feature. Once per turn deal +2d10 Radiant on Wild Shape attack; can share Moonlight Step teleport with one willing creature.

#### Circle of the Sea (Conjure Elemental, Hold Monster now always-prepared):
**AUTO:** Add Conjure Elemental and Hold Monster to always-prepared. UPDATE `character.preparedSpells`.

#### Circle of the Stars (Full of Stars):
**AUTO:** Record feature. In Starry Form, gain Resistance to Bludgeoning, Piercing, Slashing.

**Also at Level 11:**
- **AUTO:** Wild Shape uses stay at 3. Prepared Spells max → 11 + Wis modifier. Spell slots gain 1 level 6 slot.

---

## Level 12 — No New Class Feature

**AUTO:** Prepared Spells max → 12 + Wis modifier.

---

## Level 13 — No New Class Feature

**AUTO:** Proficiency Bonus → +5. Recalculate all dependent values.
**AUTO:** Prepared Spells max → 13 + Wis modifier. Spell slots gain 1 level 7 slot.

---

## Level 14 — No New Class Feature

**AUTO:** Prepared Spells max → 14 + Wis modifier.

---

## Level 15 — Improved Elemental Fury

**AUTO:** Record upgrade. If Potent Spellcasting: range +300 ft. for cantrips with 10+ ft. range. If Primal Strike: damage increases to 2d8.

**Also at Level 15:**
- **AUTO:** Prepared Spells max → 15 + Wis modifier. Spell slots gain 1 level 8 slot.

---

## Level 16 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 17 — No New Class Feature

**AUTO:** Proficiency Bonus → +6. Recalculate all dependent values.
**AUTO:** Prepared Spells max → 17 + Wis modifier. Spell slots gain 1 level 9 slot.

---

## Level 18 — Beast Spells

**AUTO:** Record feature. Can cast spells while in Wild Shape form (except spells with costly material components).

**Also at Level 18:**
- **AUTO:** Wild Shape uses → 4. UPDATE `character.resources.wildShape.uses`.
- **AUTO:** Prepared Spells max → 18 + Wis modifier. Spell slots: level 5 increases to 3.

---

## Level 19 — Epic Boon

**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Recommended: Boon of Dimensional Travel. Choose one:" [list Epic Boon feats]
Apply chosen feat. UPDATE `character.feats`.

**Also at Level 19:**
- **AUTO:** Prepared Spells max → 19 + Wis modifier. Spell slots: level 6 increases to 2.

---

## Level 20 — Archdruid

**AUTO:** Record feature. On rolling Initiative with no Wild Shape uses remaining, regain one Wild Shape use. Can convert Wild Shape uses into spell slots (2 uses per spell level). Age 10× more slowly (cosmetic).

**Also at Level 20:**
- **AUTO:** Prepared Spells max → 20 + Wis modifier. Spell slots: level 7 increases to 2.

---

## Prepared Spells Maximum Formula
`Prepared Spells Max = Druid Level + Wisdom Modifier`
