# Level-Up Wizard: Diagnostic Findings

A comparison of `1779383979063_levelup_rules.py` and the `*.md` reference files against the corrected `levelup-guide.md`. Issues are grouped by severity.

---

## 🔴 CRITICAL: Wrong Data in Code

These produce silently-incorrect character sheets. Fixing them is the highest priority.

### 1. Subclass auto-prepared spell lists are wrong

`SUBCLASS_ALWAYS_PREPARED` (Python lines 185–288) uses spell lists that don't match the 2024 PHB. Examples:

| Subclass | Tier | Code says | Should be (per `levelup-guide.md`) |
|---|---|---|---|
| Life Domain | 5 | Lesser Restoration, Prayer of Healing | Mass Healing Word, Revivify |
| Life Domain | 9 | Mass Healing Word, Revivify | Greater Restoration, Mass Cure Wounds |
| War Domain | 3 | Divine Favor, Shield of Faith *(2 spells)* | Guiding Bolt, Magic Weapon, Shield of Faith, Spiritual Weapon *(4 spells)* |
| War Domain | 9 | Crusader's Mantle, Spirit Guardians | Hold Monster, Steel Wind Strike |
| Light Domain | 5 | Flaming Sphere, Scorching Ray | Daylight, Fireball |
| Trickery Domain | 5 | Mirror Image, Pass Without Trace | Hypnotic Pattern, Nondetection |
| Trickery Domain | 9 | Blink, Dispel Magic | Dominate Person, Modify Memory |

The Cleric domain tiers in the code look like they were copy-pasted from a mix of 2014 rules and an incomplete pass. Every Cleric domain has wrong entries somewhere. Paladin oaths and Warlock patrons may have similar issues — they need to be regenerated from `levelup-guide.md`.

### 2. Bard and Ranger treated as known-spell casters

Lines 38–46:
```python
KNOWN_SPELL_GAINS: dict[str, dict[int, int]] = {
    "Bard":     {l: 1 for l in range(2, 21)} | {20: 2},
    ...
    "Ranger":   {2:1, 3:1, 5:1, 7:1, 9:1, 11:1, 13:1, 15:1, 17:1, 19:1},
}
```

In the 2024 PHB, both Bard and Ranger are **prepared** casters, not known-spell. The wizard should treat them like Cleric/Druid (no per-level "pick known spells" prompt; instead the prepared maximum grows and the player chooses on their next Long Rest).

Sorcerer and Warlock are correctly in this dict. Wizard's entry is also correct (spellbook additions).

### 3. No support for 1/3 casters (Eldritch Knight, Arcane Trickster)

`max_spell_level()` (lines 49–61) handles `full`, `half`, `pact` — but not `third`. EK and AT are quarter/third casters keyed to Fighter or Rogue level. The current code will return 0 max spell level for them at every level, which means:
- No spells unlock at L3 when they choose the subclass
- The Spells Known table is never used
- No spell-pick prompts fire

The PHB tables (now in `levelup-guide.md`) need to be added as `THIRD_CASTER_SLOTS` and `THIRD_CASTER_SPELLS_KNOWN` dicts, and `max_spell_level` extended to handle the `third` case.

### 4. Subclass selection at L3 is detected, but L3 subclass-specific prompts don't fire

Lines 586–594 add the subclass selection step at L3, but there's no follow-through for prompts that should happen *the same turn* the subclass is chosen:

| Class | L3 subclass | Missing prompt(s) |
|---|---|---|
| Barbarian | Wild Heart | Aspect of the Wilds (note: this is at L6, but the L3 Rage of the Wilds needs to display all 3 options) |
| Barbarian | Zealot | Divine Fury damage type (Necrotic vs Radiant) |
| Ranger | Beast Master | Primal Companion type (Land/Sea/Sky) |
| Ranger | Fey Wanderer | Otherworldly Glamour skill (Deception/Performance/Persuasion) |
| Ranger | Hunter | Hunter's Prey (Colossus Slayer vs Horde Breaker) |
| Fighter | Battle Master | 3 Maneuvers + Student of War (Artisan's Tool + skill) |
| Fighter | Eldritch Knight | Spellcasting setup (cantrips, spells, War Bond weapons) |
| Fighter | Psi Warrior | None (auto-grants only) |
| Rogue | Arcane Trickster | Spellcasting setup (cantrips + Mage Hand bonus + spells) |
| Rogue | Assassin | Assassin's Tools (auto-grant) |
| Rogue | Soulknife | None (auto-grants only) |
| Rogue | Thief | None (auto-grants only) |

The code relies on `cls.features[].choice_required=True` to drive these prompts, but most of these subclass-specific selections need bespoke step builders (because they require contextual data like the Wizard cantrip list, or the Battle Master maneuver list).

---

## 🟠 HIGH: Missing Prompts (player decisions silently skipped)

### 5. Weapon Mastery has zero coverage

The code never prompts for Weapon Mastery. This is a core 2024 mechanic. Required prompts:

| Class | Level | # weapons |
|---|---|---|
| Barbarian | 1 | 2 |
| Barbarian | 4 | +1 (now 3) |
| Barbarian | 10 | +1 (now 4) |
| Fighter | 1 | 3 |
| Fighter | 4 | +1 (now 4) |
| Fighter | 10 | +1 (now 5) |
| Fighter | 16 | +1 (now 6) |
| Ranger | 1 | 2 |
| Rogue | 1 | 2 |

A new `_weapon_mastery_step` builder is needed, with a sub-kind for "initial pick of N" vs "add 1 more."

### 6. Class L1 decisions not surfaced when leveling INTO a class

For multiclassing or character creation flows that route through the wizard, these L1 decisions need prompts:

- **Cleric Divine Order** (Protector vs Thaumaturge — Protector grants Heavy armor + Martial weapons; Thaumaturge grants extra cantrip + Wis bonus to Arcana/Religion)
- **Druid Primal Order** (Magician vs Warden)
- **Barbarian Primal Knowledge** (L3) — extra skill proficiency from a fixed list

These don't exist in the wizard.

### 7. L7 mid-class choices

- **Cleric Blessed Strikes** (L7): Divine Strike vs Potent Spellcasting. If Divine Strike, secondary prompt for damage type (Necrotic/Radiant).
- **Druid Elemental Fury** (L7): Potent Spellcasting vs Primal Strike (+ damage type for Primal Strike: Acid/Cold/Fire/Lightning/Thunder).

These may flow through `feature_choice` if the features JSON marks them `choice_required=True`, but the secondary damage-type prompt isn't supported by the generic builder.

### 8. Battle Master maneuvers

No maneuver picker exists. Required:
- L3: pick 3 from list of 19
- L7, L10, L15: pick 2 more each time (excluding already-known)

There's also Student of War at L3: 1 Artisan's Tool proficiency + 1 skill proficiency.

A `_maneuvers_step` builder and a `MANEUVERS` data table are needed.

### 9. Ranger subclass progression prompts

| Level | Subclass | Required prompt |
|---|---|---|
| 7 | Gloom Stalker | Iron Mind: gain Wisdom save proficiency, OR if already proficient, pick Int/Cha save |
| 7 | Hunter | Defensive Tactics: Escape the Horde vs Multiattack Defense |

These can flow through `feature_choice` but the Gloom Stalker conditional logic (check existing prof) requires custom handling.

### 10. Ranger Druidic Warrior follow-up

If Ranger picks Druidic Warrior at L2 (fighting style), the code should immediately prompt for 2 Druid cantrips. The current `_fighting_style_step` passes `extra_options: ["druidic_warrior"]` but no follow-up prompt fires after selection.

### 11. Wild Heart Path subclass features at L6 and L14

- **L6 Aspect of the Wilds**: Owl/Panther/Salmon — affects Darkvision or Climb/Swim Speed
- **L14 Power of the Wilds**: Falcon/Lion/Ram — affects Fly Speed or grants combat options

Both should be initial-choice at level-up. Subsequent swaps happen on Long Rest (out of scope per the user's earlier guidance).

---

## 🟡 MEDIUM: Stat Updates Not Triggered

These are calculation gaps. Some may be handled by side-effects elsewhere; the wizard's `required_steps()` returns prompts but the apply-step path needs to also push these stat changes.

### 12. Resource counter increments at level-up

The wizard returns step prompts but doesn't seem to push numerical resource updates. The class table values that should auto-update on level-up:

| Class | Resource | Increment levels |
|---|---|---|
| Barbarian | Rage uses (2→3→4→5→6) | 3, 6, 12, 17 |
| Barbarian | Rage Damage (+2→+3→+4) | 9, 16 |
| Cleric | Channel Divinity uses (2→3→4) | 6, 18 |
| Cleric | Divine Spark dice (1d8→2d8→3d8→4d8) | 7, 13, 18 |
| Fighter | Second Wind uses (2→3→4) | 4, 10 |
| Fighter | Action Surge uses (1→2) | 17 |
| Fighter | Indomitable uses (1→2→3) | 13, 17 |
| Fighter | Attack count (2→3→4) | 11, 20 |
| Rogue | Sneak Attack (1d6 → 10d6, every odd level) | 3, 5, 7, 9, 11, 13, 15, 17, 19 |
| Ranger | Favored Enemy free casts (2→3→4→5→6) | 5, 9, 13, 17 |
| Sorcerer | Sorcery Points = Sorcerer level | every level 2+ |

If these aren't already flowing through the class features JSON as `stat_change`-type entries, they need to be encoded in the level-up engine.

### 13. Subclass-specific stat changes at level-up

| Subclass | Level | Stat change |
|---|---|---|
| Champion | 3 | Crit range: 20 → 19–20 |
| Champion | 15 | Crit range: 19–20 → 18–20 |
| Battle Master | 3 | +4 Superiority Dice (d8) |
| Battle Master | 7 | +1 Superiority Die (now 5) |
| Battle Master | 10 | Die size: d8 → d10 |
| Battle Master | 15 | +1 Superiority Die (now 6) |
| Battle Master | 18 | Die size: d10 → d12 |
| Psi Warrior | 10 | Psionic Die: d6 → d10 |
| Psi Warrior | 18 | Psionic Die: d10 → d12 |
| Soulknife | 11 | Psionic Die: d6 → d8 |
| Soulknife | 17 | Psionic Die: d8 → d12 |

### 14. HP recalculation when Con increases via ASI

The wizard doesn't appear to recalculate prior HP when an ASI increases Constitution. If a character at L8 picks +2 Con (going from 14 to 16), their HP max should retroactively increase by 8 (1 per existing level). This is mentioned in `barbarian.md` reference but not actually implemented.

### 15. Primal Champion (Barbarian L20) and Body and Mind (Monk L20)

These features grant +4 to Str/Con (Barbarian) or Dex/Wis (Monk), with the max raised to 25 (not 20). The wizard needs to apply these as direct stat increases and clamp at 25.

---

## 🟢 LOW: Reference MD inconsistencies (won't affect runtime if code is corrected)

The reference `.md` files Claude Code used to build the wizard contain errors that explain *why* the code is wrong:

- **`barbarian.md`** L3 Primal Knowledge lists 11 skills (Acrobatics, Animal Handling, Arcana, Athletics, Insight, Intimidation, Medicine, Nature, Perception, Stealth, Survival). The actual list is 6: Animal Handling, Athletics, Intimidation, Nature, Perception, Survival.
- **`fighter.md`** L9 has an inline comment: *"Wait, checking the Fighter table again..."* — the doc was generated with an internal contradiction the author noted but never resolved.
- **`cleric.md`** L13 says: *"Actually, Cleric subclasses have features at levels 3, 6, and 17. Level 13 only brings domain spell tiers for some domains. Skip subclass feature prompt here."* — the author flagged this, but the resulting code skipped *all* L13 handling.
- **`rogue.md`** L3 Arcane Trickster: *"Choose 2 cantrips… One must be Mage Hand."* — Mage Hand is a **bonus** cantrip that doesn't count against the choice; the player chooses 2 *additional* cantrips. Same error appears in `fighter.md` for Eldritch Knight (which says EK doesn't get Mage Hand — also wrong per the corrected PHB tables).
- **`spellcasting.md`** EK spell slot table is wrong (says "2 lvl 1 at L3–4, 3 lvl 1 at L5–6, 3+1 at L7–9"). The corrected table from the user's PHB upload shows 2 lvl 1 at L3, 3 lvl 1 at L4–6, 4/2 at L7–9, and so on.
- **`spellcasting.md`** labels Bard as a "Known Spells" caster. In 2024 Bard is a prepared caster like Cleric/Druid.

**Recommendation:** Replace the 5 in-scope class MDs (`barbarian.md`, `ranger.md`, `rogue.md`, `cleric.md`, `fighter.md`) with the corresponding sections of `levelup-guide.md` so Claude Code has a clean source on future work.
