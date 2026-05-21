# PALADIN Level-Up Wizard

**Hit Die:** d10 (average: 6)
**Spellcasting:** Charisma-based, half-caster, prepared from Paladin list
**See also:** `spellcasting.md` → Paladin section

---

## Universal Steps (every level)
1. **HP:** PROMPT roll d10 or take 6 + Con modifier → UPDATE `hp.maximum`
2. **Proficiency Bonus:** AUTO update at levels 5/9/13/17
3. **Spell Slots:** AUTO update from Half-Caster table (starts at level 1)
4. **Prepared Spells Max:** AUTO update from class table
5. **Channel Divinity Uses:** AUTO update (— at 1–2, 2 at 3–10, 3 at 11+)
6. **Lay On Hands Pool:** AUTO update (= 5 × Paladin level)

---

## Level 1 — Starting Features

### Lay On Hands
**AUTO:** Record feature. Pool = 5× Paladin level = 5. UPDATE `character.resources.layOnHands.pool` = 5.
Bonus Action: restore HP from pool, or expend 5 HP to remove Poisoned condition.

### Spellcasting
**AUTO:** Paladin is Charisma-based. Spell attack = Prof + Cha modifier. Spell save DC = 8 + Prof + Cha modifier.
- **AUTO:** Prepared Spells max = 3 (from class table at level 1). UPDATE `character.preparedSpells.max`.
- **PROMPT:** "Choose 3 spells from the Paladin spell list to prepare." UPDATE `character.preparedSpells`.
- Holy Symbol is the spellcasting focus.
- **AUTO:** Spell slots at level 1: 2 × level 1 slots. UPDATE `character.spellSlots`.

### Weapon Mastery
**PROMPT:** "Weapon Mastery: Choose 2 weapons you are proficient with. You can use the Mastery property of these weapons."
- UPDATE `character.weaponMastery` with the 2 chosen weapons.
- Player may change these on each Long Rest.

---

## Level 2 — Fighting Style & Paladin's Smite

### Fighting Style
**PROMPT:** "Choose a Fighting Style feat:"
- List all Fighting Style feats from `reference_claude/feats/fighting-style/`.
- Additionally, Paladin may choose **Blessed Warrior**: Learn 2 Cleric cantrips (Charisma-based).
- Apply chosen feat's effects immediately.
- **UPDATE** `character.feats` with chosen Fighting Style.

If **Blessed Warrior**:
- **PROMPT:** "Blessed Warrior: Choose 2 cantrips from the Cleric cantrip list." UPDATE `character.spells.cantrips`.

### Paladin's Smite
**AUTO:** Always have Divine Smite prepared (doesn't count against max). Mark as always-prepared. Can cast Divine Smite once without a spell slot per Long Rest. UPDATE `character.preparedSpells`.

**Also at Level 2:**
- **AUTO:** Spell slots update: 3 × level 1 slots.
- **AUTO:** Prepared Spells max → 5.

---

## Level 3 — Channel Divinity & Paladin Subclass (Oath)

### Channel Divinity
**AUTO:** Record feature. 2 uses; regain 1 on Short Rest, all on Long Rest. UPDATE `character.resources.channelDivinity.uses` = 2.

**AUTO:** All Paladins gain Divine Sense as a Channel Divinity option: Bonus Action — detect Celestials, Fiends, and Undead within 60 ft. for 10 minutes.

### Paladin Subclass (Sacred Oath)
**PROMPT:** "Choose your Paladin subclass (Sacred Oath):"
- **Oath of Devotion** — sacred weapons, immunity to Charmed, holy protection
- **Oath of Glory** — athleticism, Temp HP distribution, speed aura
- **Oath of the Ancients** — nature magic, damage resistance aura, undying sentinel
- **Oath of Vengeance** — hunter's focus, advantage on attacks, soul of vengeance

Apply subclass features immediately, including Oath Spells. UPDATE `character.subclass`.

#### All Oaths — Oath Spells (first tier):
**AUTO (Oath of Devotion):** Always have Protection from Evil and Good, Shield of Faith prepared. UPDATE `character.preparedSpells`.
**AUTO (Oath of Glory):** Always have Guiding Bolt, Heroism prepared. UPDATE `character.preparedSpells`.
**AUTO (Oath of the Ancients):** Always have Ensnaring Strike, Speak with Animals prepared. UPDATE `character.preparedSpells`.
**AUTO (Oath of Vengeance):** Always have Bane, Hunter's Mark prepared. UPDATE `character.preparedSpells`.

#### Oath of Devotion — Sacred Weapon:
**AUTO:** Record Sacred Weapon (Channel Divinity option). Melee weapon gains +Cha modifier to attack rolls and Radiant damage for 10 minutes.

#### Oath of Glory — Inspiring Smite & Peerless Athlete:
**AUTO:** Record both as Channel Divinity options.

#### Oath of the Ancients — Nature's Wrath:
**AUTO:** Record as Channel Divinity option (Restrain creatures within 15 ft.).

#### Oath of Vengeance — Vow of Enmity:
**AUTO:** Record as Channel Divinity option (Advantage on attacks vs. one creature for 1 minute).

**Also at Level 3:**
- **AUTO:** Spell slots: 4 × level 1, 2 × level 2. Prepared Spells max → 6.

---

## Level 4 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Charisma increases: recalculate Spell Save DC, Spell Attack Bonus.
If Strength increases: recalculate attack bonuses.

**Also at Level 4:**
- **AUTO:** Lay On Hands pool → 20. UPDATE `character.resources.layOnHands.pool`.

---

## Level 5 — Extra Attack & Faithful Steed

### Extra Attack
**AUTO:** Record feature. Character attacks twice per Attack action. UPDATE `character.features.extraAttack`.

### Faithful Steed
**AUTO:** Always have Find Steed prepared (doesn't count against max). Can cast it once without a slot per Long Rest. UPDATE `character.preparedSpells`.

**Also at Level 5:**
- **AUTO:** Proficiency Bonus → +3. Recalculate all dependent values.
- **AUTO:** Spell slots: 4/3 (gain 2 × level 2, upgrade to 3 total). Prepared Spells max → 7.
- **AUTO:** Lay On Hands pool → 25.
- **Oath Spells (5th-level spells):**
  - Devotion: Aid, Zone of Truth
  - Glory: Enhance Ability, Magic Weapon
  - Ancients: Misty Step, Moonbeam
  - Vengeance: Hold Person, Misty Step
  UPDATE `character.preparedSpells`.

---

## Level 6 — Aura of Protection

**AUTO:** Record feature. You and allies within 10 ft. gain Charisma modifier bonus (min +1) to all saving throws. UPDATE `character.features.auraOfProtection`.

**Also at Level 6:**
- **AUTO:** Lay On Hands pool → 30. Prepared Spells max → 7 (unchanged).

---

## Level 7 — Subclass Feature

#### Oath of Devotion (Aura of Devotion):
**AUTO:** Immunity to Charmed for you and allies in Aura of Protection.

#### Oath of Glory (Aura of Alacrity):
**AUTO:** Your Speed +10 ft.; allies entering/starting turns in aura gain +10 ft. Speed until next turn.

#### Oath of the Ancients (Aura of Warding):
**AUTO:** You and allies in Aura of Protection have Resistance to Necrotic, Psychic, and Radiant damage.

#### Oath of Vengeance (Relentless Avenger):
**AUTO:** On an Opportunity Attack hit, target's Speed → 0; move half Speed as part of the Reaction.

**Also at Level 7:**
- **AUTO:** Lay On Hands pool → 35. Spell slots: 4/3/— (gain level 3 slots: 2 × level 3). Prepared Spells max → 9.

---

## Level 8 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 8:**
- **AUTO:** Lay On Hands pool → 40.

---

## Level 9 — Abjure Foes

**AUTO:** Record feature. Magic Action + Channel Divinity — Frighten up to Charisma modifier creatures within 60 ft. (Wisdom save); Frightened creatures have restrictions each turn.

**Also at Level 9:**
- **AUTO:** Proficiency Bonus → +4. Recalculate all dependent values.
- **AUTO:** Lay On Hands pool → 45. Spell slots: 4/3/2 → 4/3/3 → 4/3/3/1 (gaining higher levels by half-caster table). Prepared Spells max → 10.
- **Oath Spells (9th-level):**
  - Devotion: Beacon of Hope, Dispel Magic
  - Glory: Haste, Protection from Energy
  - Ancients: Plant Growth, Protection from Energy
  - Vengeance: Haste, Protection from Energy
  UPDATE `character.preparedSpells`.

---

## Level 10 — Aura of Courage

**AUTO:** Record feature. You and allies in Aura of Protection are immune to Frightened.

**Also at Level 10:**
- **AUTO:** Lay On Hands pool → 50.

---

## Level 11 — Radiant Strikes

**AUTO:** Record feature. Melee weapon hits deal extra 1d8 Radiant damage. UPDATE `character.features.radiantStrikes`.

**Also at Level 11:**
- **AUTO:** Lay On Hands pool → 55. Prepared Spells max → 11. Channel Divinity uses → 3.

---

## Level 12 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 12:**
- **AUTO:** Lay On Hands pool → 60.

---

## Level 13 — Restoring Touch

**AUTO:** Record feature. When using Lay On Hands to heal, can also remove one condition per 5 HP: Blinded, Charmed, Deafened, Frightened, Paralyzed, or Stunned.

**Also at Level 13:**
- **AUTO:** Proficiency Bonus → +5. Lay On Hands pool → 65. Prepared Spells max → 12. Spell slots gain level 4.
- **Oath Spells (13th-level):**
  - Devotion: Freedom of Movement, Guardian of Faith
  - Glory: Compulsion, Freedom of Movement
  - Ancients: Ice Storm, Stoneskin
  - Vengeance: Banishment, Dimension Door
  UPDATE `character.preparedSpells`.

---

## Level 14 — Subclass Feature

#### Oath of Devotion (Smite of Protection):
**AUTO:** When casting Divine Smite, grant Half Cover to aura allies until your next turn.

#### Oath of Glory (Glorious Defense):
**AUTO:** Reaction — add Cha modifier to an ally's AC vs. one attack; if it misses, make a weapon attack as part of the Reaction.

#### Oath of the Ancients (Undying Sentinel):
**AUTO:** When dropped to 0 HP, drop to 1 HP and heal 3× Paladin level instead (once per Long Rest). Cannot be magically aged.

#### Oath of Vengeance (Soul of Vengeance):
**AUTO:** Reaction — make a melee attack when the Vow of Enmity target hits or misses with an attack.

**Also at Level 14:**
- **AUTO:** Lay On Hands pool → 70.

---

## Level 15 — No New Class Feature

**AUTO:** Lay On Hands pool → 75. Spell slots gain level 5. Prepared Spells max → 14.

---

## Level 16 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 16:**
- **AUTO:** Lay On Hands pool → 80.

---

## Level 17 — No New Class Feature

**AUTO:** Proficiency Bonus → +6. Lay On Hands pool → 85. Prepared Spells max → 15.
- **Oath Spells (17th-level):**
  - Devotion: Commune, Flame Strike
  - Glory: Legend Lore, Yolande's Regal Presence
  - Ancients: Commune with Nature, Tree Stride
  - Vengeance: Hold Monster, Scrying
  UPDATE `character.preparedSpells`.

---

## Level 18 — Aura Expansion

**AUTO:** Aura of Protection radius extends to 30 ft. UPDATE `character.features.auraOfProtection.radius` = 30.

**Also at Level 18:**
- **AUTO:** Lay On Hands pool → 90.

---

## Level 19 — Epic Boon

**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Recommended: Boon of Truesight. Choose one:" [list Epic Boon feats]
Apply chosen feat. UPDATE `character.feats`.

**Also at Level 19:**
- **AUTO:** Lay On Hands pool → 95.

---

## Level 20 — Subclass Capstone

#### Oath of Devotion (Holy Nimbus):
**AUTO:** Bonus Action — Advantage on saves vs. Fiends/Undead; enemies in aura take Cha modifier + Prof. Bonus Radiant damage per turn; aura filled with sunlight. 10 minutes.

#### Oath of Glory (Living Legend):
**AUTO:** Bonus Action for 10 minutes — Advantage on Charisma checks; reroll failed saves as Reaction; turn a missed attack into a hit once per turn.

#### Oath of the Ancients (Elder Champion):
**AUTO:** Bonus Action for 1 minute — enemies in aura have Disadvantage on saves; regain 10 HP at start of each turn; cast action spells as Bonus Actions.

#### Oath of Vengeance (Avenging Angel):
**AUTO:** Bonus Action for 10 minutes — 60-ft. Fly Speed; enemies in aura make Wisdom save or become Frightened.

**Also at Level 20:**
- **AUTO:** Lay On Hands pool → 100.

---

## Lay On Hands Pool Formula
`Pool = 5 × Paladin Level` — recalculate every level.

## Prepared Spells Maximum
Set directly by class table in `classes/paladin.md`.
