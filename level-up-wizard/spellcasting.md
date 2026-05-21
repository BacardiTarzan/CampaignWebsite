# Spellcasting Reference for Level-Up Wizard

This document explains how each spellcasting class handles spells differently, so the level-up wizard and spell preparation feature can be implemented correctly. Classes fall into four distinct models.

---

## Model 1: Prepared-from-List (Cleric, Druid, Paladin, Ranger)

These classes prepare spells fresh each Long Rest from their entire class spell list (limited by level).

### How It Works
- The character has a **Prepared Spells Maximum** (see per-class formulas below).
- On each Long Rest, the player can freely swap any or all prepared spells for different spells from their class list.
- No spell "costs" anything to swap — full flexibility every Long Rest.
- The player can only prepare spells of levels they have spell slots for.

### Level-Up Behavior
- When Prepared Spells Max increases, the player can immediately have more spells in their prepared list.
- No "pick new spells" prompt is required at level-up for base prepared-from-list casters — they just have more room to fill on their next Long Rest.
- **Exception:** Subclass or feature spells (e.g., Domain Spells, Oath Spells) are always prepared automatically on top of the max — prompt to add these to the prepared list when unlocked.

### Prepared Spells Maximum Formulas
| Class | Formula |
|-------|---------|
| Cleric | Cleric Level + Wisdom modifier |
| Druid | Druid Level + Wisdom modifier |
| Paladin | From class table (fixed values by level) |
| Ranger | From class table (fixed values by level) |

### Spell Preparation UI Flow
1. Show current prepared spell list.
2. Show Prepared Spells Max.
3. Allow player to add/remove spells until count = Max.
4. Filter available spells to only those ≤ highest available slot level.
5. Always-prepared spells (Domain, Oath, etc.) are shown but locked; they cannot be removed and don't count against the Max.

---

## Model 2: Known Spells (Bard, Sorcerer, Warlock)

These classes learn a fixed list of spells permanently. They are always available — no daily preparation needed.

### How It Works
- The character knows a set number of spells (see class table).
- All known spells are always "prepared" and available to cast.
- Spells can only be swapped when leveling up (1 spell per level-up for Sorcerer; 1 per level-up for Warlock; Bard increases its max regularly with Magical Secrets access).
- There is no Long Rest preparation ritual for these classes.

### Level-Up Behavior
- When **Known Spells Max increases**: **PROMPT** the player to choose new spell(s) immediately.
- On **every** level-up: **PROMPT** if the player wants to swap 1 known spell for a different one of valid level.
- Sorcerer and Warlock: can only swap 1 spell per level-up.
- Bard: can add spells from Bard, Cleric, Druid, or Wizard lists after gaining Magical Secrets at level 10+.

### Subclass/Feature Always-Prepared Spells
Warlock Patron Spells and Sorcerer Subclass Spells are "always prepared" in addition to known spells. They:
- Do NOT count against the Known Spells Maximum.
- Are automatically added to the character's usable spells when unlocked.
- Cannot be removed.

### Spell Preparation UI
No daily preparation screen is needed. Instead:
- Show all known spells as always available.
- During level-up, show the swap prompt.
- Show subclass spells separately (labeled "Patron Spells" or "Subclass Spells").

---

## Model 3: Spellbook (Wizard)

The Wizard has a unique system combining a spellbook with daily preparation.

### How It Works
- The Wizard maintains a **Spellbook** containing spells they have learned/copied.
- Each Long Rest, the Wizard prepares spells from their spellbook.
- **Prepared Spells Max** = Wizard Level + Intelligence modifier.
- Only spells in the spellbook can be prepared.
- Any Wizard spell can be copied into the spellbook if the Wizard finds it (cost: 2 hours and 50 GP per spell level).

### Starting Spellbook
- Level 1: 6 level 1 spells of the player's choice.

### Adding Spells to Spellbook on Level-Up
- At **every level gained after 1st**, the Wizard adds 2 spells of any level they can cast to their spellbook for **free**.
- **PROMPT (on every level-up):** "Choose 2 spells to add to your spellbook."
- UPDATE `character.spellbook`.

### Ritual Adept Exception
The Wizard can cast any **Ritual** spell from their spellbook without preparing it (must have the spellbook in hand).

### Spell Preparation UI Flow
1. Show spellbook contents (all spells the Wizard has).
2. Show Prepared Spells Max.
3. Allow player to select up to Max spells to prepare.
4. Spells not in the spellbook cannot be selected.
5. Ritual spells are available to cast without preparing (shown as a separate note).

### Spell Mastery (Level 18)
- Choose 1 level 1 and 1 level 2 spell from the spellbook.
- These are always prepared and can be cast at lowest level for free.
- **PROMPT** at level 18 for this selection.
- These change on Long Rest; allow re-selection each Long Rest.

### Signature Spells (Level 20)
- Choose 2 level 3 spells from the spellbook.
- Always prepared; can be cast once at level 3 without a slot per Short/Long Rest.
- **PROMPT** at level 20 for this selection (permanent unless spellbook changes).

---

## Model 4: Pact Magic (Warlock)

Warlock's Pact Magic is fundamentally different from standard spellcasting.

### Key Differences from Standard Spellcasting
| Feature | Standard Slots | Pact Magic |
|---------|---------------|------------|
| Slot levels | Multiple levels (1–9) | All the same level |
| Recovery | Long Rest only | Short Rest OR Long Rest |
| Max slots | Many | 1–4 total |
| Slot level progression | Stays at unlock tier | Scales with level (1→5) |

### Pact Magic Slot Table
| Warlock Level | Slots | Slot Level |
|--------------|-------|-----------|
| 1 | 1 | 1st |
| 2–4 | 2 | 1st–2nd |
| 5–10 | 2 | 3rd–5th |
| 11–16 | 3 | 5th |
| 17–20 | 4 | 5th |

*(See `rules/spell-slots.md` for the full Warlock table)*

### Mystic Arcanum (Levels 9, 11, 13, 15)
- At each of these levels, the Warlock selects one high-level spell from the Warlock list.
- Each Mystic Arcanum spell is cast **once per Long Rest without a Pact Magic slot**.
- These are entirely separate from Pact Magic slots.
- **PROMPT** on each unlock level for the spell choice.

### Spell Preparation UI for Warlock
- Display Pact Magic slots and their shared level prominently.
- Show known spells (always available, no daily prep).
- Show Mystic Arcanum spells separately with their once-per-Long-Rest recharge.
- Show Patron Spells as always-prepared extras.

---

## Model 5: Subclass Spellcasters (Eldritch Knight, Arcane Trickster)

These non-caster classes gain limited spellcasting through their subclass.

### Eldritch Knight (Fighter) — Intelligence-based Wizard Spells

#### Mechanics
- Quarter-caster: gains spell slots at one-quarter the rate of a full caster.
- **Spells Known** (not prepared): fixed list, like Sorcerer/Warlock.
- Most spells must be Abjuration or Evocation; one spell per tier can be from any school.
- Spell attack = Prof + Int modifier. Spell save DC = 8 + Prof + Int modifier.

#### Spell Slot Progression (Eldritch Knight)
| Fighter Level | Spell Slots | Slot Levels |
|--------------|-------------|-------------|
| 3–4 | 2 lvl 1 | 1st |
| 5–6 | 3 lvl 1 | 1st |
| 7–9 | 3+1 | 1st/2nd |
| 10–12 | 4+2 | 1st/2nd |
| 13–15 | 4+2+1 | 1st/2nd/3rd |
| 16–18 | 4+2+2 | 1st/2nd/3rd |
| 19–20 | 4+3+3+1 | 1st/2nd/3rd/4th |

#### Level-Up Prompts for Eldritch Knight
- At level 3: PROMPT for 2 cantrips + 3 spells.
- On each subsequent level that increases Known Spells: PROMPT for new spell(s).
- Note which levels allow any-school choice vs. Abjuration/Evocation only.

### Arcane Trickster (Rogue) — Intelligence-based Wizard Spells

#### Mechanics
- Quarter-caster (same rate as Eldritch Knight).
- Spells Known: fixed list, like Sorcerer/Warlock.
- Most spells must be Enchantment or Illusion; one spell per tier can be from any school.
- Spell attack = Prof + Int modifier. Spell save DC = 8 + Prof + Int modifier.

#### Level-Up Prompts for Arcane Trickster
Same structure as Eldritch Knight but with Enchantment/Illusion restriction.

---

## Half-Caster Spell Slots (Paladin, Ranger)

Both Paladin and Ranger use the Half-Caster Spell Slot table from `rules/spell-slots.md`.

Key differences from full casters:
- Maximum spell slot level is 5th (never gain 6th–9th level slots).
- Spell slots advance at half the rate of full casters.
- Both Paladin and Ranger **begin casting at level 1** (2024 PHB revision — Ranger is no longer level 2 for spells).

---

## Spell Memorization / Preparation Feature — Implementation Guide

### When a Player Opens Spell Preparation

1. **Identify the class model:**
   - Wizard → show spellbook; allow prep up to Max.
   - Cleric / Druid → show full class spell list filtered to available levels; allow prep up to Max.
   - Paladin / Ranger → show full class spell list filtered to available levels; allow prep up to Max.
   - Bard / Sorcerer / Warlock → no daily prep; show known spells as always active. Offer to manage known spells list instead.

2. **Handle always-prepared spells:**
   - These are locked — show them at the top, grayed out or marked, and do NOT count them against the Prepared Spells Max.
   - Sources: Domain Spells (Cleric), Circle/Terrain Spells (Druid), Oath Spells (Paladin), Patron Spells (Warlock), Subclass Spells (Sorcerer), specific class features (Favored Enemy → Hunter's Mark for Ranger, etc.).

3. **Filter by available slot levels:**
   - Only show spells of levels the character has spell slots for (including Pact Magic slots for Warlock).
   - Exception: Ritual Adept (Wizard) — show all Ritual spells in the spellbook, even unprepared, with a "Ritual Only" tag.

4. **Confirm and save:**
   - UPDATE `character.preparedSpells` with the player's chosen list.
   - The updated list is what's used for casting until the next Long Rest.

### When a Player Casts a Spell
- Check `character.preparedSpells` (or `character.spells.known` for known-spell casters).
- Deduct the appropriate spell slot (Pact Magic slot for Warlock; standard slot for all others).
- For once-per-rest freebies (Innate Sorcery cast, Paladin's Smite free cast, etc.), track separately with recharge flags.

### Cantrips
- Cantrips are always available — no slot cost, no daily prep.
- The only changes to cantrips come at level-up (when the class's cantrip count increases).
- Subclass cantrips (e.g., Illusionist's Minor Illusion, Warrior of Shadow's Minor Illusion, Cleric Thaumaturge's extra cantrip) are added to the cantrip list and are permanent — not swappable unless a feature specifically says so.
