# Claude Code Prompt: Level-Up Wizard Overhaul

> Paste everything below the divider line into Claude Code. Attach `levelup-guide.md` and `wizard-issues.md` to the session. Have the current `levelup_rules.py` accessible in the repo.

---

## Task

Overhaul our level-up wizard rules engine at `app/services/levelup_rules.py` (current version: 769 lines, attached). The current implementation has wrong data, missing prompts, and missing support for one-third casters. Use the two attached reference files as your source of truth:

- **`levelup-guide.md`** — the authoritative D&D 2024 spec for Barbarian, Ranger, Rogue, Cleric, and Fighter. All five classes, all subclasses, all level entries with impact-tagged decisions (🔢 STAT CHANGE, 🎯 PLAYER CHOICE, 📋 DISPLAY ONLY, ✨ NEW SPELL SLOT, 📖 PICK SPELLS, ⚔️ PICK WEAPONS).
- **`wizard-issues.md`** — diagnostic findings explaining what's currently wrong in `levelup_rules.py` and the underlying reference MDs, grouped by severity.

The other 7 classes (Bard, Druid, Monk, Paladin, Sorcerer, Warlock, Wizard) are **out of scope** for this overhaul. Do not touch their data unless a change is structurally required (e.g., the `max_spell_level` function signature).

## Scope summary

Five classes × all 20 levels × 4 subclasses each = the full surface area defined by `levelup-guide.md`. The architecture of `required_steps()` and the step-builder pattern is sound — preserve it. Add new step kinds and data tables; do not rewrite from scratch.

## Constraints

- Postgres-backed; existing models: `Character`, `CharacterChoice`, `CharacterClass` (`cc`), `DnDClass` (`cls`), `Subclass`, `Spell`, `Feat`. Use existing patterns.
- Class features JSON (referenced as `cls.features` and `subclass.features` in the current code) drives generic `feature_choice` steps via `choice_required=True`. Some features in the new spec will need bespoke step builders because the generic builder can't supply contextual data (cantrip lists, maneuver lists, Wizard spell schools, etc.).
- The current code calls `_owned_invoc_keys`, `_owned_metamagic_keys`, etc. via `char.choices` filtered by `feature_key`. Follow that pattern for any new persisted choices (e.g., `feature_key="maneuver"`, `feature_key="weapon_mastery"`, `feature_key="blessed_strikes"`).
- "Long Rest mechanics" (e.g., Wild Heart Aspect swap, Hunter's Prey swap, Weapon Mastery swap) are **out of scope** for the level-up wizard per the user. Only surface the *initial* selection at the relevant level-up.

## Plan — phased delivery

Work through these phases in order. After each phase, summarize what changed and pause for the user to review before continuing.

### Phase 1: Data correctness (no new prompts)

1. **Rebuild `SUBCLASS_ALWAYS_PREPARED`** for the 5 in-scope classes from `levelup-guide.md`:
   - Cleric: Life Domain, Light Domain, Trickery Domain, War Domain
   - Ranger: Beast Master (none — no patron-style spells), Fey Wanderer, Gloom Stalker, Hunter (none)
   - (Barbarian, Rogue, Fighter subclasses have no patron-style spell lists; Eldritch Knight and Arcane Trickster use their own Spells Known model and should NOT appear in `SUBCLASS_ALWAYS_PREPARED`.)
2. **Move Bard and Ranger out of `KNOWN_SPELL_GAINS`.** Both are prepared casters in 2024. Their prepared-spells maximum grows per the class table; the wizard does not prompt for "pick known spells" at each level. (Keep Sorcerer, Warlock, Wizard entries unchanged.) Note: Bard is out of our overhaul scope, but this fix is correct and small enough to include.
3. **Add `THIRD_CASTER_SLOTS` and `THIRD_CASTER_SPELLS_KNOWN` tables** from the Arcane Trickster / Eldritch Knight tables in `levelup-guide.md`. Both have identical slot progressions; only Spells Known and Cantrips counts differ.
4. **Extend `max_spell_level()`** to handle `spellcasting_type == "third"`. Use Fighter level for EK / Rogue level for AT (which is `char_level` of the class in question).
5. **Audit `SUBCLASS_ALWAYS_PREPARED` for the other 7 classes** (Paladin, Warlock, Sorcerer in particular) for similar bugs but DO NOT fix them in this PR — flag them in your summary so the user can scope a follow-up.

### Phase 2: New step builders

Add these step builders, following the pattern of existing builders (return a dict with `id`, `kind`, `label`, `required`, plus kind-specific fields). For each, the frontend will need a matching UI component, but that's out of scope here — just emit clean step dicts.

1. **`_weapon_mastery_step`** — supports two sub-kinds via field `mode`:
   - `mode: "initial"` with `pick: N` and `eligible_weapons: [...]` (filtered by class's permitted weapon categories)
   - `mode: "add_one"` with `current: [...]` and `pick: 1`
   Add a `WEAPON_MASTERY_LEVELS` table mapping class name → level → operation:
   ```python
   WEAPON_MASTERY_LEVELS = {
       "Barbarian": {1: ("initial", 2), 4: ("add_one", 1), 10: ("add_one", 1)},
       "Fighter":   {1: ("initial", 3), 4: ("add_one", 1), 10: ("add_one", 1), 16: ("add_one", 1)},
       "Ranger":    {1: ("initial", 2)},
       "Rogue":     {1: ("initial", 2)},
       "Paladin":   {1: ("initial", 2)},  # not in scope but listed for completeness
   }
   ```
2. **`_maneuvers_step`** — Battle Master only.
   - At L3: `pick: 3`, no exclusions
   - At L7/10/15: `pick: 2`, exclude `current` maneuvers
   - Hard-code `BATTLE_MASTER_MANEUVERS` (19 entries) with `key`, `name`, `description`, `save_ability` (where applicable). See `levelup-guide.md` → Battle Master Level 3 for the canonical list.
3. **`_primal_knowledge_step`** (Barbarian L3) — pick 1 additional skill from `["Animal Handling", "Athletics", "Intimidation", "Nature", "Perception", "Survival"]`, excluding skills already proficient in.
4. **`_divine_order_step`** (Cleric L1) — `Protector` vs `Thaumaturge`. Thaumaturge requires a follow-up cantrip pick step (use existing `_cantrips_step` with `pick: 1`).
5. **`_blessed_strikes_step`** (Cleric L7) — `Divine Strike` vs `Potent Spellcasting`. If Divine Strike, follow-up step `_blessed_strikes_damage_type` with options `["Necrotic", "Radiant"]`.
6. **`_iron_mind_step`** (Gloom Stalker Ranger L7) — conditional: if character already has Wis save proficiency, prompt for Int or Cha; otherwise auto-grant Wisdom save (no prompt, just record + apply).
7. **`_hunters_prey_step`** (Hunter Ranger L3): `Colossus Slayer` vs `Horde Breaker`.
8. **`_defensive_tactics_step`** (Hunter Ranger L7): `Escape the Horde` vs `Multiattack Defense`.
9. **`_otherworldly_glamour_step`** (Fey Wanderer Ranger L3): pick 1 of `["Deception", "Performance", "Persuasion"]`, excluding existing proficiencies.
10. **`_beast_companion_step`** (Beast Master Ranger L3): pick `Beast of the Land` / `Beast of the Sea` / `Beast of the Sky`.
11. **`_rage_of_the_wilds_step`** (Wild Heart Barbarian L3): display all three (`Bear`, `Eagle`, `Wolf`) as in-session toggle options — this step records *that the feature is gained*, not a permanent choice. UI shows expandable text per option.
12. **`_aspect_of_the_wilds_step`** (Wild Heart Barbarian L6): pick `Owl` (Darkvision) / `Panther` (Climb Speed) / `Salmon` (Swim Speed). Apply speed update on selection.
13. **`_power_of_the_wilds_step`** (Wild Heart Barbarian L14): same pattern as Aspect, with `Falcon` / `Lion` / `Ram`.
14. **`_divine_fury_step`** (Zealot Barbarian L3): pick damage type `Necrotic` or `Radiant`.
15. **`_war_bond_step`** (Eldritch Knight Fighter L3): pick up to 2 weapons from the character's owned weapons. Persist as a feature choice.
16. **`_third_caster_spells_step`** (EK + AT) — uses `THIRD_CASTER_SPELLS_KNOWN` for the count and applies school restrictions (Abjuration/Evocation for EK, Enchantment/Illusion for AT) with free-choice exceptions at class levels 3 (1 of 3), 8, 14, and 20. Add Mage Hand as a bonus cantrip for both at L3.
17. **`_student_of_war_step`** (Battle Master Fighter L3) — combined step or two separate steps: pick 1 Artisan's Tool + pick 1 skill (from the Fighter skill list, excluding existing proficiencies).
18. **`_assassins_tools_step`** (Assassin Rogue L3) — auto-grant Disguise Kit and Poisoner's Kit proficiency; surface a confirmation step (kind: `display_only` or similar pattern in the codebase) so the player sees what changed.

### Phase 3: Wire the new steps into `required_steps()`

In `required_steps()`:

1. Insert **weapon mastery** step at the relevant level for the relevant class (after HP, before subclass — early in the order makes sense).
2. Insert **Primal Knowledge** at Barbarian L3 (after subclass).
3. Insert **Divine Order** at Cleric L1 (a new branch since L1 is also a wizard-handled level when leveling INTO a class via multiclass).
4. Insert **Blessed Strikes** at Cleric L7. Insert follow-up damage type at the same level if Divine Strike was picked.
5. Insert **subclass-specific L3 steps** after the subclass selection step itself fires. Use the subclass name from the user's pick (which is committed mid-flow) to dispatch:
   - Wild Heart → `_rage_of_the_wilds_step`
   - Zealot → `_divine_fury_step`
   - Beast Master → `_beast_companion_step`
   - Fey Wanderer → `_otherworldly_glamour_step`
   - Hunter → `_hunters_prey_step`
   - Battle Master → `_maneuvers_step` + `_student_of_war_step`
   - Eldritch Knight → `_war_bond_step` + `_third_caster_spells_step`
   - Arcane Trickster → `_third_caster_spells_step`
   - Assassin → `_assassins_tools_step`
6. Insert **subclass-specific L6/L7/L14 steps** at the right levels:
   - Wild Heart L6 → `_aspect_of_the_wilds_step`
   - Wild Heart L14 → `_power_of_the_wilds_step`
   - Gloom Stalker L7 → `_iron_mind_step`
   - Hunter L7 → `_defensive_tactics_step`
7. Insert **maneuvers** at Battle Master L7, L10, L15.
8. Insert **Ranger Druidic Warrior follow-up** — if the player chose Druidic Warrior at L2, fire a cantrip pick step immediately after.
9. Insert **third-caster spell gains** for EK and AT at every level the Spells Known column increases (per `THIRD_CASTER_SPELLS_KNOWN`). Apply school restrictions in the step's `school_restriction` field; the frontend should honor it.

### Phase 4: Stat change application

Where the existing `auto_grants()` returns spell IDs, add a parallel `auto_stat_changes()` (or extend the existing apply path) that returns a list of stat changes to apply to the character sheet. These shouldn't generate prompts — they're auto-applied:

1. Resource counter increments per `wizard-issues.md` §12.
2. Subclass die-size / die-count progressions per `wizard-issues.md` §13 (Champion crit range, Battle Master Superiority Die, Psi Warrior Psionic Die, Soulknife Psionic Die).
3. **HP retroactive recalc on Con ASI**: when an ASI step records a Con increase, walk the character's class history and add `(new_con_mod - old_con_mod) × character_level` to HP max.
4. **Capstone stat boosts**: Barbarian L20 Primal Champion (Str+4, Con+4, max 25), Monk L20 Body and Mind (Dex+4, Wis+4, max 25). Out of scope classes have similar capstones — flag and skip.

### Phase 5: Replace the reference MDs

For the 5 in-scope classes, split `levelup-guide.md` into per-class files matching the existing `level-up-wizard/` naming convention. Replace:
- `level-up-wizard/barbarian.md`
- `level-up-wizard/ranger.md`
- `level-up-wizard/rogue.md`
- `level-up-wizard/cleric.md`
- `level-up-wizard/fighter.md`

Preserve the format (PROMPT / AUTO / UPDATE structure) so future Claude Code sessions reading these files get correct data. The shared spell-slot tables and the One-Third Caster tables go into an updated `spellcasting.md` or a new `one-third-casters.md`.

### Phase 6: Tests

Add tests in `tests/test_levelup_rules.py`:

1. **Spell slot table correctness**: parameterized over `(class, level, expected_slots)` — assert `max_spell_level()` and the per-level slot dicts match `levelup-guide.md` for full, half, third, pact.
2. **Subclass spell auto-grants**: for each in-scope subclass, level a fresh character through L3, L5, L7, L9, L13, L17 and assert the right spells are auto-granted at each tier.
3. **Step enumeration**: for each in-scope class × 1–20, snapshot the list of step `id`s emitted by `required_steps()` and compare to a golden file. Use `pytest-snapshot` or equivalent.
4. **Specific bug fixes**: regression tests for each entry in `wizard-issues.md` §1 (subclass spell lists), §3 (third caster support), §5–11 (missing prompts now present).

## What to read first

1. `levelup_rules.py` (current code) — understand the existing patterns, especially `required_steps`, the step builders, and how `auto_grants` interacts with `char.choices`.
2. `levelup-guide.md` — your spec.
3. `wizard-issues.md` — the diagnostic findings driving this work.
4. The class features JSON for one in-scope class (run something like `SELECT features FROM dnd_classes WHERE name = 'Barbarian'`) to confirm what's already routed through `feature_choice` vs what needs a bespoke builder.

## Output format

After each phase, present a brief summary:
- Files modified (and line counts changed)
- New data tables added
- New step builders added
- Tests added and passing
- Any unresolved questions or scope flags

Then pause and ask the user for review before moving to the next phase.

## Watch out for

- **Don't break existing classes.** Bard / Druid / Monk / Paladin / Sorcerer / Warlock / Wizard handling must keep working. If a structural change (e.g., extending `max_spell_level`) ripples into them, add tests confirming nothing broke.
- **Idempotency**: `required_steps()` is called multiple times during a level-up flow (once to plan, again to validate). New step builders must not produce different outputs on repeat calls for the same character state.
- **Subclass selection mid-flow.** L3 is the trickiest level because the player picks the subclass *during* the wizard, and follow-up steps depend on the pick. The current code uses `cc.subclass_id` to detect whether the pick has happened. New subclass-specific steps should check the same field and only emit once the subclass is committed.
- **The user has Postgres.** The maneuver list, weapon mastery list, etc. are large enough to warrant DB storage rather than Python constants. If you make that move, also create a migration. Otherwise, hard-coding is fine for v1.
- **The Long Rest swap mechanics are out of scope** for the wizard but may need a flag on the persisted choice (e.g., `swappable_on_long_rest: True`) so the character sheet UI knows to allow it.

## Final deliverable

A single PR with the changes from all 6 phases, accompanied by a CHANGELOG.md entry listing every bug fix and every new prompt the wizard now surfaces.
