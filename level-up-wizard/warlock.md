# WARLOCK Level-Up Wizard

**Hit Die:** d8 (average: 5)
**Spellcasting:** Charisma-based, Pact Magic (all slots same level; recharge on Short/Long Rest)
**See also:** `spellcasting.md` → Warlock section

---

## Universal Steps (every level)
1. **HP:** PROMPT roll d8 or take 5 + Cha modifier → UPDATE `hp.maximum`
2. **Proficiency Bonus:** AUTO update at levels 5/9/13/17
3. **Pact Magic Spell Slots:** AUTO update (count and level) from Warlock class table
4. **Prepared Spells (Known Spells) Max:** AUTO update from class table
5. **Invocations Known:** AUTO update count from class table
6. **Cantrips Known:** AUTO update from class table

### On Every Level-Up: Invocation Replacement Option
**PROMPT:** "Would you like to replace one of your known Eldritch Invocations with a different one? (You may replace up to 1 per level-up.)"
- Show current invocations and available new ones (check prerequisites).
- If yes: update invocation list.

### On Every Level-Up: Spell Swap Option
**PROMPT:** "Would you like to swap 1 known Warlock spell for a different Warlock spell of any level you have slots for?"
- If yes: UPDATE `character.spells.known`.

---

## Level 1 — Starting Features

### Eldritch Invocations
**PROMPT:** "Eldritch Invocations: Choose 1 Eldritch Invocation. Invocations without prerequisites are available at level 1."
- Available at level 1 (no prerequisites): Armor of Shadows, Eldritch Mind, Pact of the Blade, Pact of the Chain, Pact of the Tome
- Show full list with prerequisites marked.
- **UPDATE** `character.features.eldritchInvocations` with the chosen invocation.
- Apply the invocation's effects immediately.

### Pact Magic
**AUTO:** Warlock is Charisma-based. Spell attack = Prof + Cha modifier. Spell save DC = 8 + Prof + Cha modifier.
- **PROMPT:** "Choose 2 cantrips from the Warlock cantrip list." UPDATE `character.spells.cantrips`.
- **PROMPT:** "Choose 2 spells from the Warlock spell list to know." UPDATE `character.spells.known`.
- **AUTO:** Pact Magic at level 1: 1 slot, Slot Level 1. UPDATE `character.pactMagic.slots` = 1, `character.pactMagic.slotLevel` = 1.
- Arcane Focus is the spellcasting focus.
- Note: Pact Magic slots recharge on Short Rest OR Long Rest.

---

## Level 2 — Magical Cunning & Invocations Increase

### Magical Cunning
**AUTO:** Record feature. Perform an esoteric rite for 1 minute — regain up to half max Pact Magic slots (round up). Once per Long Rest.

### Invocations Increase
**PROMPT:** "Eldritch Invocations: You can now know 3 invocations. Choose 2 additional invocations. Available (check prerequisites):"
- Any invocations with "Level 2+" prerequisite are now available.
- **UPDATE** `character.features.eldritchInvocations`.
- Apply effects of new invocations.

**Also at Level 2:**
- **AUTO:** Pact Magic → 2 slots, Slot Level 1.
- **AUTO:** Known Spells max → 3. **PROMPT:** "Choose 1 new Warlock spell to know." UPDATE `character.spells.known`.

---

## Level 3 — Warlock Subclass

**PROMPT:** "Choose your Warlock subclass (Otherworldly Patron):"
- **Archfey Patron** — fey magic, Misty Step, charm/frighten effects
- **Celestial Patron** — healing light, radiant damage, sacred spells
- **Fiend Patron** — dark power, fire damage, Temp HP on kills
- **Great Old One Patron** — telepathy, psychic manipulation, Charmed/Frightened control

Apply subclass features immediately, including Patron Spells. UPDATE `character.subclass`.

#### All Patrons — Patron Spells:
Patron spells are always prepared (don't count against Known Spells max). Apply first tier at level 3:

**AUTO (Archfey):** Always have Calm Emotions, Faerie Fire, Misty Step, Phantasmal Force, Sleep prepared. UPDATE `character.preparedSpells`.

**AUTO (Celestial):** Always have Aid, Cure Wounds, Guiding Bolt, Lesser Restoration, Light, Sacred Flame prepared. UPDATE `character.preparedSpells`.

**AUTO (Fiend):** Always have Burning Hands, Command, Scorching Ray, Suggestion prepared. UPDATE `character.preparedSpells`.

**AUTO (Great Old One):** Always have Detect Thoughts, Dissonant Whispers, Phantasmal Force, Tasha's Hideous Laughter prepared. UPDATE `character.preparedSpells`.

#### Archfey — Steps of the Fey:
**AUTO:** Record feature. Cast Misty Step without a slot (uses = Cha modifier). UPDATE `character.resources.stepsOfTheFey.uses`.
**PROMPT:** "Steps of the Fey: Choose an additional effect for Misty Step:"
- **Refreshing Step** — gain Temp HP equal to 1d10 when you teleport
- **Taunting Step** — creatures within 5 ft. of your origin have Disadvantage on attack rolls against others until your next turn
UPDATE `character.features.stepsOfTheFey.effect`.

#### Celestial — Healing Light:
**AUTO:** Record feature. d6 pool = 1 + Warlock level. Can use up to Cha modifier dice at once. Recharges on Long Rest. UPDATE `character.resources.healingLight.pool`.

#### Fiend — Dark One's Blessing:
**AUTO:** Record feature. Gain Temp HP = Cha modifier + Warlock level when you or nearby ally reduce an enemy to 0 HP.

#### Great Old One — Awakened Mind & Psychic Spells:
**AUTO:** Bonus Action — telepathic link with one creature for Warlock level minutes.
**AUTO:** Can change any Warlock spell's damage type to Psychic; cast Enchantment/Illusion Warlock spells without V/S.

**Also at Level 3:**
- **AUTO:** Pact Magic → 2 slots, Slot Level 2.
- **AUTO:** Known Spells max → 4. **PROMPT:** "Choose 1 new Warlock spell." UPDATE `character.spells.known`.

---

## Level 4 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.
If Charisma increases: recalculate Spell Save DC, Spell Attack Bonus, Healing Light pool (if Celestial), Aura of Protection bonus (if multiclassed Paladin).

**Also at Level 4:**
- **AUTO:** Pact Magic → Slot Level stays 2.
- **PROMPT:** "You can now know 3 cantrips. Choose 1 new cantrip." UPDATE `character.spells.cantrips`.
- **AUTO:** Known Spells max → 5. **PROMPT:** "Choose 1 new Warlock spell." UPDATE `character.spells.known`.

---

## Level 5 — No New Class Feature

**Also at Level 5:**
- **AUTO:** Proficiency Bonus → +3.
- **AUTO:** Pact Magic → Slot Level 3.
- **AUTO:** Known Spells max → 6. **PROMPT:** "Choose 1 new Warlock spell." UPDATE `character.spells.known`.
- **AUTO:** Invocations → 5. **PROMPT:** "Choose 2 additional invocations (level 5+ prerequisites now available):" UPDATE `character.features.eldritchInvocations`.
- **Patron Spells (Tier 2):**
  - Archfey: Blink, Plant Growth
  - Celestial: Daylight, Revivify
  - Fiend: Fireball, Stinking Cloud
  - Great Old One: Clairvoyance, Hunger of Hadar
  UPDATE `character.preparedSpells`.

---

## Level 6 — Subclass Feature

#### Archfey (Misty Escape):
**AUTO:** Record upgrade. Misty Step can now be cast as Reaction to taking damage.
**PROMPT:** "Misty Escape: Choose 2 additional effect options for Misty Step (choose from Disappearing Step or Dreadful Step, in addition to your previous choice):"
- **Disappearing Step** — become Invisible until start of next turn
- **Dreadful Step** — deal 2d10 Psychic to creatures near origin OR destination
UPDATE `character.features.stepsOfTheFey.escapeoptions`.

#### Celestial (Radiant Soul):
**AUTO:** Resistance to Radiant damage. Add Cha modifier to one Radiant or Fire damage roll per turn.

#### Fiend (Dark One's Own Luck):
**AUTO:** Record feature. Add 1d10 to one ability check or saving throw after seeing the roll. Uses = Cha modifier per Long Rest. UPDATE `character.resources.darkOnesOwnLuck.uses`.

#### Great Old One (Clairvoyant Combatant):
**AUTO:** Record feature. Force telepathically bonded creature to make Wisdom save — Disadvantage vs. you, Advantage for you. Once per Short/Long Rest or Pact slot.

**Also at Level 6:**
- **AUTO:** Known Spells max → 7. **PROMPT:** "Choose 1 new Warlock spell." UPDATE `character.spells.known`.

---

## Level 7 — Contact Patron

**AUTO:** Always have Contact Other Plane prepared. Can cast it to speak with patron without expending a slot or making a save. Once per Long Rest. UPDATE `character.preparedSpells`.

**Also at Level 7:**
- **AUTO:** Pact Magic → Slot Level 4.
- **AUTO:** Known Spells max → 8. **PROMPT:** "Choose 1 new Warlock spell." UPDATE `character.spells.known`.
- **AUTO:** Invocations → 6. **PROMPT:** "Choose 1 additional invocation (level 7+ prerequisites now available):" UPDATE `character.features.eldritchInvocations`.
- **Patron Spells (Tier 3):**
  - Archfey: Dominate Beast, Greater Invisibility
  - Celestial: Guardian of Faith, Wall of Fire
  - Fiend: Fire Shield, Wall of Fire
  - Great Old One: Confusion, Summon Aberration
  UPDATE `character.preparedSpells`.

---

## Level 8 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

**Also at Level 8:**
- **AUTO:** Known Spells max → 9. **PROMPT:** "Choose 1 new Warlock spell." UPDATE `character.spells.known`.

---

## Level 9 — Mystic Arcanum (Level 6 spell)

### Mystic Arcanum
**PROMPT:** "Mystic Arcanum: Choose one level 6 Warlock spell to know as your Mystic Arcanum. This spell can be cast once without a spell slot per Long Rest."
- Show all Warlock level 6 spells.
- **UPDATE** `character.features.mysticArcanum.level6Spell`.

**Also at Level 9:**
- **AUTO:** Proficiency Bonus → +4.
- **AUTO:** Pact Magic → Slot Level 5.
- **AUTO:** Known Spells max → 10. **PROMPT:** "Choose 1 new Warlock spell." UPDATE `character.spells.known`.
- **AUTO:** Invocations → 7. **PROMPT:** "Choose 2 additional invocations (level 9+ prerequisites now available):" UPDATE `character.features.eldritchInvocations`.
- **Patron Spells (Tier 4):**
  - Archfey: Dominate Person, Seeming
  - Celestial: Greater Restoration, Summon Celestial
  - Fiend: Geas, Insect Plague
  - Great Old One: Modify Memory, Telekinesis
  UPDATE `character.preparedSpells`.

---

## Level 10 — Subclass Feature

#### Archfey (Beguiling Defenses):
**AUTO:** Immunity to Charmed. Reaction to halve damage and deal matching Psychic damage to attacker.

#### Celestial (Celestial Resilience):
**AUTO:** Gain Temp HP = Warlock level + Cha modifier on Short/Long Rest or Magical Cunning. Up to 5 chosen creatures gain half that. UPDATE `character.features.celestialResilience`.

#### Fiend (Fiendish Resilience):
**PROMPT:** "Fiendish Resilience: Choose a damage type on each Short or Long Rest to gain Resistance to. What do you choose now?"
- Player picks any damage type (except Force).
- **UPDATE** `character.resistances` with current choice.
- Note: This changes on each Short/Long Rest. Record as a mutable field.

#### Great Old One (Eldritch Hex & Thought Shield):
**AUTO:** Always have Hex prepared. When casting Hex, the target also has Disadvantage on saves of the hexed ability. UPDATE `character.preparedSpells`.
**AUTO:** Mind cannot be read; Resistance to Psychic damage; reflected Psychic damage to attacker.

**Also at Level 10:**
- **PROMPT:** "You can now know 4 cantrips. Choose 1 new cantrip." UPDATE `character.spells.cantrips`.
- **AUTO:** Known Spells max → 10 (unchanged).

---

## Level 11 — Mystic Arcanum (Level 7 spell)

**PROMPT:** "Mystic Arcanum: Choose one level 7 Warlock spell to know as your Mystic Arcanum. Once per Long Rest."
- **UPDATE** `character.features.mysticArcanum.level7Spell`.

**Also at Level 11:**
- **AUTO:** Pact Magic → 3 slots. UPDATE `character.pactMagic.slots` = 3.
- **AUTO:** Known Spells max → 11. **PROMPT:** "Choose 1 new Warlock spell." UPDATE `character.spells.known`.

---

## Level 12 — No New Class Feature

**AUTO:** Invocations → 8. **PROMPT:** "Choose 1 additional invocation." UPDATE `character.features.eldritchInvocations`.
**AUTO:** Known Spells max → 11 (unchanged).

---

## Level 13 — Mystic Arcanum (Level 8 spell)

**PROMPT:** "Mystic Arcanum: Choose one level 8 Warlock spell to know as your Mystic Arcanum. Once per Long Rest."
- **UPDATE** `character.features.mysticArcanum.level8Spell`.

**Also at Level 13:**
- **AUTO:** Proficiency Bonus → +5.
- **AUTO:** Known Spells max → 12. **PROMPT:** "Choose 1 new Warlock spell." UPDATE `character.spells.known`.

---

## Level 14 — Subclass Feature (Capstone Part 1)

#### Archfey (Bewitching Magic):
**AUTO:** After casting an Enchantment or Illusion spell as an action, cast Misty Step for free as part of that action.

#### Celestial (Searing Vengeance):
**AUTO:** When an ally within 60 ft. would make a Death Saving Throw, restore half their max HP; nearby enemies take 2d8 + Cha modifier Radiant damage and are Blinded.

#### Fiend (Hurl Through Hell):
**AUTO:** Record feature. Once per turn on a hit — target makes Charisma save or vanishes through the Lower Planes for 1 round, taking 8d10 Psychic damage on return. Once per Long Rest or expend a Pact slot.

#### Great Old One (Create Thrall):
**AUTO:** Record feature. Summon Aberration upgrades; extra Psychic damage to Hexed creatures.

---

## Level 15 — Mystic Arcanum (Level 9 spell)

**PROMPT:** "Mystic Arcanum: Choose one level 9 Warlock spell to know as your Mystic Arcanum. Once per Long Rest."
- **UPDATE** `character.features.mysticArcanum.level9Spell`.

**Also at Level 15:**
- **AUTO:** Known Spells max → 13. **PROMPT:** "Choose 1 new Warlock spell." UPDATE `character.spells.known`.
- **AUTO:** Invocations → 9. **PROMPT:** "Choose 1 additional invocation (level 15+ prerequisites now available):" UPDATE `character.features.eldritchInvocations`.

---

## Level 16 — Ability Score Improvement

### ASI
See `_OVERVIEW.md` → Ability Score Improvement section.

---

## Level 17 — No New Class Feature

**AUTO:** Proficiency Bonus → +6.
**AUTO:** Pact Magic → 4 slots. UPDATE `character.pactMagic.slots` = 4.
**AUTO:** Known Spells max → 14. **PROMPT:** "Choose 1 new Warlock spell." UPDATE `character.spells.known`.

---

## Level 18 — No New Class Feature

**AUTO:** Invocations → 10. **PROMPT:** "Choose 1 additional invocation." UPDATE `character.features.eldritchInvocations`.

---

## Level 19 — Epic Boon

**PROMPT:** "You've reached level 19 and gain an Epic Boon feat. Recommended: Boon of Fate. Choose one:" [list Epic Boon feats]
Apply chosen feat. UPDATE `character.feats`.

**Also at Level 19:**
- **AUTO:** Known Spells max → 15. **PROMPT:** "Choose 1 new Warlock spell." UPDATE `character.spells.known`.

---

## Level 20 — Eldritch Master

**AUTO:** Record upgrade. Magical Cunning now restores ALL expended Pact Magic slots (not just half).

---

## Pact Magic vs. Regular Spellcasting — KEY RULES
- Pact Magic slots are ALL the same level (the current Slot Level column).
- There are never different tiers of Pact Magic slots open simultaneously.
- Slots recharge on both Short Rest AND Long Rest.
- Mystic Arcanum spells (levels 9, 11, 13, 15) are separate from Pact Magic slots — they have their own once-per-Long-Rest recharge.
- Patron Spells are always-prepared extras; they are NOT counted in the Known Spells total.
- Each level-up, the player may replace 1 invocation AND swap 1 known spell.
