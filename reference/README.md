# D&D 2024 Reference Library

Source files for character creation, leveling, and gameplay reference, derived from the 2024 Player's Handbook.

## Folder layout

| Folder | Contents | Per-file granularity |
|---|---|---|
| `classes/` | 12 character classes (subclasses inline) | One class per file |
| `species/` | 10 PHB species | One species per file |
| `backgrounds/` | 16 PHB backgrounds | One background per file |
| `feats/origin/` | 10 origin feats | One feat per file |
| `feats/general/` | 43 general feats | One feat per file |
| `feats/fighting-style/` | 10 fighting style feats | One feat per file |
| `feats/epic-boon/` | 12 epic boon feats | One feat per file |
| `spells/level-0/` | 34 cantrips | One spell per file |
| `spells/level-1/` … `level-9/` | 354 leveled spells | One spell per file |
| `equipment/` | Weapons, armor, tools, gear, packs, mounts, services | Topic per file (tables) |
| `rules/` | Skills, actions, glossary, weapon properties, mastery properties, magic items, crafting, coins | Topic per file |

## File naming

All filenames are kebab-case slugs of the item name:
- `classes/barbarian.md`
- `species/dragonborn.md`
- `feats/origin/magic-initiate.md`
- `spells/level-3/fireball.md`

## Format conventions

Every per-item file starts with a single `# H1` heading bearing the canonical name. Structured fields appear as bold-key lines:

```markdown
# FIREBALL
**Level:** 3
**School:** Evocation
**Classes:** Sorcerer, Wizard
**Casting Time:** Action
**Range:** 150 feet
**Components:** V, S, M (a tiny ball of bat guano and sulfur)
**Duration:** Instantaneous

A bright streak flashes from you to a point you choose...
```

Class files contain a `### Class Features by Level` table, a `### Key Features` prose section, and a `### Subclasses` section with each subclass under `#### Subclass Name`.

## Rules files included

| File | Contents |
|---|---|
| `rules/character-creation.md` | Step-by-step creation, ability score methods, Standard Array by class, background ASI rules (+2/+1 or +1/+1/+1), ability score modifier table, HP at level 1, XP/Proficiency Bonus table, level-up process, starting at higher levels |
| `rules/spell-slots.md` | Full caster table (Bard/Cleric/Druid/Sorcerer/Wizard), half caster table (Paladin/Ranger), Warlock Pact Magic table, Multiclass Spellcaster table |
| `rules/multiclassing.md` | Prerequisites by class, proficiencies gained when multiclassing, Extra Attack stacking, combined spell slot calculation, Warlock Pact Magic interaction |
| `rules/languages.md` | Standard languages (Common + 9 others with d12 roll), Rare languages (9 including Primordial dialects) |
| `rules/skills.md` | All 18 skills with associated abilities |
| `rules/actions.md` | All 12 standard 2024 actions |
| `rules/glossary.md` | Complete rules glossary — conditions, AoE shapes, hazards, key terms |
| `rules/weapon-properties.md` | All weapon properties (Ammunition, Finesse, Heavy, Light, Loading, Range, Reach, Thrown, Two-Handed, Versatile) |
| `rules/mastery-properties.md` | All 8 mastery properties (Cleave, Graze, Nick, Push, Sap, Slow, Topple, Vex) |
| `rules/magic-items.md` | Identification, Attunement, Wearing/Wielding rules |
| `rules/crafting.md` | Crafting nonmagical items, brewing potions, scribing spell scrolls |
| `rules/coins.md` | Currency conversion table |
