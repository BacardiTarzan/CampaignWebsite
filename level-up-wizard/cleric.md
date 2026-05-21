# CLERIC Level-Up Wizard

**Hit Die:** d8 (average: 5)
**Spellcasting:** Wisdom-based, prepared from full Cleric list
**See also:** `spellcasting.md` → Cleric section

---

## Universal Steps (every level)
1. **HP:** PROMPT roll d8 or take 5 + Wis modifier → UPDATE `hp.maximum`
2. **Proficiency Bonus:** AUTO update at levels 5/9/13/17
3. **Spell Slots:** AUTO update from Full Caster table
4. **Prepared Spells Max:** AUTO update from class table
5. **Channel Divinity Uses:** AUTO update from class table (—, 2, 2, 2, 2, 3, 3 ... 4 at level 18+)

---

## Level 1 — Starting Features

### Spellcasting
**AUTO:** Cleric is Wisdom-based. Spell attack = Prof + Wis modifier. Spell save DC = 8 + Prof + Wis modifier.
- **PROMPT:** "Choose 3 cantrips from the Cleric cantrip list." UPDATE `character.spells.cantrips`.
- **AUTO:** Prepared Spells max = Cleric level + Wisdom modifier. UPDATE `character.preparedSpells.max`.
- **PROMPT:** "Choose [max] spells from the Cleric spell list to prepare." UPDATE `character.preparedSpells`.
- Holy Symbol is the spellcasting focus.

### Divine Order
**PROMPT:** "Divine Order: Choose one of the following options:"
- **Protector** — Gain proficiency with Martial weapons and Heavy armor.
- **Thaumaturge** — Gain one additional Cleric cantrip. Add Wisdom modifier to Arcana and Religion checks (before or after you roll).

If **Protector**:
- **UPDATE** `character.proficiencies.weapons` — add Martial weapons.
- **UPDATE** `character.proficiencies.armor` — add Heavy armor.
- Recalculate AC if switching to Heavy armor.

If **Thaumaturge**:
- **PROMPT:** "Choose 1 additional cantrip from the Cleric cantrip list." UPDATE `character.spells.cantrips` (now 4 total at level 1).
- **UPDATE** `character.features.divineOrderThaumaturge` — flag that Wis modifier applies to Arcana and Religion.
- Recalculate Arcana and Religion skill bonuses.

**UPDATE** `character.features.divineOrder`.

---

## Level 2 — Channel Divinity

### Channel Divinity
**AUTO:** Record feature. 2 uses per rest (regain 1 on Short Rest, all on Long Rest). UPDATE `character.resources.channelDivinity.uses` = 2.

Cleric gains two Channel Divinity options:
- **Divine Spark** (heal or deal Radiant/Necrotic damage, 1d8 + Wis modifier, scales to 4d8 at higher levels)
- **Turn Undead** (Frighten and Incapacitate Undead within 30 ft., Wisdom save)

**AUTO:** Record both features. No choices required.

**Also at Level 2:**
- **AUTO:** Prepared Spells max → Cleric level (2) + Wis modifier.

---

## Level 3 — Cleric Subclass

**PROMPT:** "Choose your Cleric subclass (Divine Domain):"
- **Life Domain** — powerful healing amplification
- **Light Domain** — radiant damage, Warding Flare defense
- **Trickery Domain** — deception, illusion duplicate
- **War Domain** — extra attacks, guided strikes

Apply subclass features immediately, including Domain Spells. UPDATE `character.subclass`.

#### All Subclasses — Domain Spells:
Each subclass grants Domain Spells that are always prepared and don't count against the prepared max. Apply the first tier of domain spells at level 3.

**AUTO (Life Domain):** Always have Aid, Bless, Cure Wounds, Lesser Restoration prepared. UPDATE `character.preparedSpells` (mark as always-prepared).

**AUTO (Light Domain):** Always have Burning Hands, Faerie Fire, Scorching Ray, See Invisibility prepared. UPDATE `character.preparedSpells`.

**AUTO (Trickery Domain):** Always have Charm Person, Disguise Self, Invisibility, Pass without Trace prepared. UPDATE `character.preparedSpells`.

**AUTO (War Domain):** Always have Guiding Bolt, Magic Weapon, Shield of Faith, Spiritual Weapon prepared. UPDATE `character.preparedSpells`.

#### Life Domain — Disciple of Life & Preserve Life:
**AUTO:** Both features require no choices. Record Disciple of Life (healing +2 + slot level). Record Preserve Life (Channel Divinity use).

#### Light Domain — Radiance of the Dawn & Warding Flare:
**AUTO:** Record both features. Warding Flare uses = Wisdom modifier (min 1). UPDATE `character.resources.wardingFlare`.

#### Trickery Domain — Blessing of the Trickster & Invoke Duplicity:
**AUTO:** Record both features.

#### War Domain — Guided Strike & War Priest:
**AUTO:** Record both features. War Priest uses = Wisdom modifier (min 1). UPDATE `character.resources.warPriest`.

**Also at Level 3:**
- **AUTO:** Prepared Spells max → 3 + Wis modifier. Spell slots gain 2 level 2 slots.

---

## Level 4 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Wisdom increases: recalculate Spell Save DC, Spell Attack Bonus, Prepared Spells max (= Cleric level + new Wis modifier).

**Also at Level 4:**
- **PROMPT:** "You can now know 4 cantrips. Choose 1 new cantrip from the Cleric cantrip list." UPDATE `character.spells.cantrips`.
- **AUTO:** Prepared Spells max → 4 + Wis modifier.

---

## Level 5 — Sear Undead

**AUTO:** Record feature. When using Turn Undead, also deal Radiant damage = [Wisdom modifier]d8 to Undead who fail the save.

**Also at Level 5:**
- **AUTO:** Proficiency Bonus → +3. Recalculate all dependent values.
- **AUTO:** Prepared Spells max → 5 + Wis modifier.
- **AUTO:** Spell slots gain 2 level 3 slots.
- **Domain Spells (tier 2):** Add the next tier of domain spells as always-prepared:
  - Life: Mass Healing Word, Revivify
  - Light: Daylight, Fireball
  - Trickery: Hypnotic Pattern, Nondetection
  - War: Crusader's Mantle, Spirit Guardians
  UPDATE `character.preparedSpells`.

---

## Level 6 — Subclass Feature

#### Life Domain (Blessed Healer):
**AUTO:** Record feature. Regain HP = 2 + slot level when casting a healing spell on another creature.

#### Light Domain (Improved Warding Flare):
**AUTO:** Record upgrade. Warding Flare now recharges on Short or Long Rest; adds 2d6 + Wis modifier Temp HP to the protected creature.

#### Trickery Domain (Trickster's Transposition):
**AUTO:** Record feature. Can swap places with the Invoke Duplicity illusion when moving it.

#### War Domain (War God's Blessing):
**AUTO:** Record feature. Channel Divinity to cast Shield of Faith or Spiritual Weapon without a slot.

**Also at Level 6:**
- **AUTO:** Channel Divinity uses → 3. UPDATE `character.resources.channelDivinity.uses`.
- **AUTO:** Prepared Spells max → 6 + Wis modifier. Spell slots gain 1 additional level 3 slot.

---

## Level 7 — Blessed Strikes

### Blessed Strikes
**PROMPT:** "Blessed Strikes: Choose one of the following:"
- **Divine Strike** — Once per turn on a weapon hit, deal extra 1d8 Necrotic or Radiant damage (your choice of type).
- **Potent Spellcasting** — Add your Wisdom modifier to damage rolls from Cleric cantrips.

**UPDATE** `character.features.blessedStrikes` with the chosen option.

If **Divine Strike**:
- **PROMPT:** "Divine Strike: Which damage type do you prefer, Necrotic or Radiant? (You may choose per attack during play.)"
- Record both as available options.

**Also at Level 7:**
- **AUTO:** Prepared Spells max → 7 + Wis modifier. Spell slots gain 1 level 4 slot.
- **Domain Spells (tier 3):** Add next tier as always-prepared:
  - Life: Aura of Life, Death Ward
  - Light: Arcane Eye, Wall of Fire
  - Trickery: Confusion, Dimension Door
  - War: Fire Shield, Freedom of Movement
  UPDATE `character.preparedSpells`.

---

## Level 8 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Wisdom increases: recalculate Spell Save DC, Spell Attack Bonus, Prepared Spells max.

**Also at Level 8:**
- **AUTO:** Prepared Spells max → 8 + Wis modifier. Spell slots gain 1 additional level 4 slot.

---

## Level 9 — Divine Intervention

**AUTO:** Record feature. Magic Action — cast any Cleric spell of level 5 or lower without a slot or material components; once per Long Rest.

**Also at Level 9:**
- **AUTO:** Proficiency Bonus → +4. Recalculate all dependent values.
- **AUTO:** Prepared Spells max → 9 + Wis modifier. Spell slots gain 2 level 5 slots.
- **Domain Spells (tier 4):** Add next tier as always-prepared:
  - Life: Greater Restoration, Mass Cure Wounds
  - Light: Flame Strike, Scrying
  - Trickery: Dominate Person, Modify Memory
  - War: Hold Monster, Steel Wind Strike
  UPDATE `character.preparedSpells`.

---

## Level 10 — No New Class Feature

**PROMPT:** "You can now know 5 cantrips. Choose 1 new cantrip from the Cleric cantrip list." UPDATE `character.spells.cantrips`.
**AUTO:** Prepared Spells max → 10 + Wis modifier. Spell slots: level 5 increases to 2.

---

## Level 11 — No New Class Feature

**AUTO:** Prepared Spells max → 11 + Wis modifier. Spell slots gain 1 level 6 slot.

---

## Level 12 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 12:**
- **AUTO:** Prepared Spells max → 12 + Wis modifier (same as 11 if Wis unchanged).

---

## Level 13 — Subclass Feature (2nd)

Apply the second-tier subclass feature (level 13 — only Life, Light, Trickery, War domains have a level 13 feature via the domain spells; subclass combat features come at levels 3, 6, 17).

Actually, Cleric subclasses have features at levels 3, 6, and 17. Level 13 only brings domain spell tiers for some domains. Skip subclass feature prompt here.

**Also at Level 13:**
- **AUTO:** Proficiency Bonus → +5. Recalculate all dependent values.
- **AUTO:** Prepared Spells max → 13 + Wis modifier. Spell slots gain 1 level 7 slot.

---

## Level 14 — Improved Blessed Strikes

**AUTO:** Record upgrade. If Divine Strike: increases to 2d8. If Potent Spellcasting: when dealing cantrip damage, also give the cleric themselves 2× Wisdom modifier Temp HP.

---

## Level 15 — No New Class Feature

**AUTO:** Prepared Spells max → 15 + Wis modifier. Spell slots gain 1 level 8 slot.

---

## Level 16 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 17 — Subclass Capstone Feature

#### Life Domain (Supreme Healing):
**AUTO:** Record feature. Always use maximum dice values when rolling for healing spells.

#### Light Domain (Corona of Light):
**AUTO:** Record feature. Magic Action — emit sunlight in 60-ft. radius for 1 minute.

#### Trickery Domain (Improved Duplicity):
**AUTO:** Record feature. Allies also gain Advantage on attacks near the illusion; illusion heals a creature for Cleric level HP when it ends.

#### War Domain (Avatar of Battle):
**AUTO:** Record feature. Resistance to Bludgeoning, Piercing, and Slashing damage.

**Also at Level 17:**
- **AUTO:** Proficiency Bonus → +6. Recalculate all dependent values.
- **AUTO:** Prepared Spells max → 17 + Wis modifier. Spell slots gain 1 level 9 slot.

---

## Level 18 — No New Class Feature

**AUTO:** Channel Divinity uses → 4. UPDATE `character.resources.channelDivinity.uses`.
**AUTO:** Prepared Spells max → 18 + Wis modifier. Spell slots: level 5 increases to 3.

---

## Level 19 — Epic Boon

**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Recommended: Boon of Fate. Choose one:" [list Epic Boon feats]
Apply chosen feat. UPDATE `character.feats`.

**Also at Level 19:**
- **AUTO:** Prepared Spells max → 19 + Wis modifier. Spell slots: level 6 increases to 2.

---

## Level 20 — Greater Divine Intervention

**AUTO:** Record upgrade. Divine Intervention can now select Wish; recharges after 2d4 Long Rests (instead of always requiring a Long Rest).

**Also at Level 20:**
- **AUTO:** Prepared Spells max → 20 + Wis modifier. Spell slots: level 7 increases to 2.

---

## Prepared Spells Maximum Formula
`Prepared Spells Max = Cleric Level + Wisdom Modifier`

Recalculate whenever Cleric level or Wisdom modifier changes.
