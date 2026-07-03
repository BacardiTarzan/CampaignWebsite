# Wizard

<!-- Verified against PHB raw text (chapter 3, Wizard), not the Classes.md project reference.
     Spellcasting (cantrips, prepared spells, spell slots per the Wizard Features table) belongs to your
     existing spell-slot system, not this combat-resource seeder — same treatment as the other casters.
     Ritual Adept (lvl 1 — cast any Ritual-tagged spell in your spellbook as a Ritual without preparing it)
     and Memorize Spell (lvl 5 — swap one prepared spell for another from your spellbook on finishing a
     Short Rest) are downtime spell-list/loadout customization, not combat resources, and are excluded —
     same treatment as other classes' rest-gated prepared-spell or Weapon Mastery swaps. -->

## Arcane Recovery
action_type: free_action   # no action required, triggered specifically when you finish a Short Rest
resource_key: arcane_recovery
min_level: 1
max_uses: 1
rest_type: long
description: When you finish a Short Rest, choose expended spell slots to recover, with a combined level no more than half your Wizard level (round up); none of the slots can be level 6 or higher. Usable once per Long Rest.

## Spell Mastery
action_type: action   # the rule requires the chosen spells to have a casting time of an action
min_level: 18   # no resource — unlimited; choose 1 level 1 and 1 level 2 spell in your spellbook with a casting time of an action
description: Cast your chosen level 1 spell and your chosen level 2 spell (each with a casting time of an action) at their lowest level at will, without expending a spell slot. To cast either at a higher level, you must expend a spell slot instead.

## Signature Spells
action_type: special   # the action type depends entirely on which two level 3 Wizard spells you choose, decided per character — not fixed by the class
resource_key: signature_spells
min_level: 20
max_uses: 2   # one per chosen spell — each of your two signature spells is independently castable once per rest
rest_type: short regain all, long regain all
description: Choose two level 3 spells in your spellbook as your signature spells; you always have them prepared. Cast each of them once at level 3 without expending a spell slot; once cast this way, that spell can't be cast this way again until you finish a Short or Long Rest. To cast either at a higher level, you must expend a spell slot.

<!-- Excluded base-class features (no decision point / no action / no resource, or out of scope): Spellcasting
     (out of scope), Ritual Adept (downtime ritual-casting utility — see intro comment), Scholar (passive
     Expertise), Wizard Subclass, Ability Score Improvement, Memorize Spell (downtime spell-swap — see
     intro comment), Epic Boon. -->

---

### Subclass: Abjurer

## Arcane Ward
action_type: free_action   # created/recharged as a rider when casting an Abjuration spell with a spell slot — no separate action
resource_key: arcane_ward
subclass: abjurer
min_level: 3
max_uses: 2 × Wizard level + Intelligence modifier   # an HP pool, not a charge count
rest_type: long
description: When you cast an Abjuration spell with a spell slot, create (if you don't already have one) a magical ward on yourself with HP equal to 2× your Wizard level plus your Intelligence modifier; once created, it can't be created again until you finish a Long Rest. The ward absorbs damage dealt to you instead of you taking it (apply your own Resistances/Vulnerabilities first; once it drops to 0 HP it stops absorbing, though its magic remains until you finish a Long Rest, and you take any remaining damage). Each subsequent time you cast an Abjuration spell with a spell slot, the ward automatically regains HP equal to twice that slot's level.

## Arcane Ward — Bonus Action Recharge
action_type: bonus_action
subclass: abjurer
min_level: 3   # no Wizard-specific resource consumed — spends a spell slot (out of scope) to restore the ward's HP
description: Expend a spell slot to restore your Arcane Ward's HP by an amount equal to twice the slot's level.

## Projected Ward
action_type: reaction
consumes_resource: arcane_ward   # redirects damage onto the existing ward's HP pool instead of the warded creature's
subclass: abjurer
min_level: 6
description: When a creature you can see within 30 ft. of yourself takes damage, take a Reaction to have your Arcane Ward absorb that damage instead (apply that creature's own Resistances/Vulnerabilities first); if this reduces the ward to 0 HP, the warded creature takes any remaining damage.

## Spell Breaker
action_type: bonus_action   # changes Dispel Magic's own casting time to a Bonus Action
subclass: abjurer
min_level: 10
description: You always have Counterspell and Dispel Magic prepared (out-of-scope spells). Cast Dispel Magic as a Bonus Action instead of its normal casting time, adding your Proficiency Bonus to its ability check. When you cast Counterspell or Dispel Magic with a spell slot and the spell fails to stop the targeted spell, the slot isn't expended.

<!-- Excluded: Abjuration Savant (passive spellbook addition), Spell Resistance (passive save Advantage +
     Resistance to spell damage). -->

---

### Subclass: Diviner

## Portent
action_type: free_action   # declared before a D20 Test is rolled by you or a creature you can see — no action required; once per turn
resource_key: portent
subclass: diviner
min_level: 3
max_uses: 2   # increases to 3 at lvl 14 (Greater Portent)
rest_type: long regain all
description: Replace any D20 Test made by you or a creature you can see with one of your recorded foretelling rolls; you must choose to do so before the roll, and you can replace a roll this way only once per turn. Roll two d20s (three at lvl 14) and record the results whenever you finish a Long Rest; any unused foretelling rolls are lost at that time.

## Expert Divination
action_type: free_action   # rider immediately after casting a Divination spell with a level 2+ spell slot — no separate action
subclass: diviner
min_level: 6
description: Regain one expended spell slot of a level lower than the one you just expended to cast a Divination spell (the regained slot can't be higher than level 5).

## The Third Eye
action_type: bonus_action
resource_key: the_third_eye
subclass: diviner
min_level: 10
max_uses: 1
rest_type: short regain all, long regain all
description: Choose one benefit, which lasts until you start a Short or Long Rest — Darkvision (gain Darkvision with a range of 120 ft.), Greater Comprehension (read any language), or See Invisibility (cast See Invisibility without expending a spell slot). Usable once per Short or Long Rest.

<!-- Excluded: Divination Savant (passive spellbook addition). -->

---

### Subclass: Evoker

## Sculpt Spells
action_type: free_action   # rider on casting an Evocation spell that affects multiple creatures you can see — no separate action of its own
subclass: evoker
min_level: 6
description: Choose a number of creatures equal to 1 plus the spell's level from among those affected by an Evocation spell you cast; they automatically succeed on their saving throws against it, and they take no damage if they'd normally take half damage on a success.

## Overchannel
action_type: free_action   # rider on casting a damaging Wizard spell of level 1–5 with a spell slot — no separate action
resource_key: overchannel_uses   # tracks escalating self-damage risk, not a hard cap — see description
min_level: 14
max_uses: unlimited   # no cap on uses; risk escalates with each use since your last Long Rest
rest_type: long
subclass: evoker
description: Deal maximum damage with a Wizard spell of level 1–5 that deals damage, cast with a spell slot, on the turn you cast it. The first time you do so since your last Long Rest, you suffer no adverse effect. Each time you use this feature again before finishing a Long Rest, you take 2d12 Necrotic damage (ignoring Resistance and Immunity) for each level of the spell slot used, and that Necrotic damage per spell level increases by 1d12 for each further use before your next Long Rest.

<!-- Excluded: Evocation Savant (passive spellbook addition), Potent Cantrip (automatic half-damage rider
     on a cantrip miss/save, no decision point), Empowered Evocation (automatic flat Intelligence-modifier
     damage add, no decision point — same treatment as Sorcerer's Draconic Elemental Affinity). -->

---

### Subclass: Illusionist

## Improved Illusions — Minor Illusion
action_type: bonus_action   # changes Minor Illusion's own casting time to a Bonus Action
subclass: illusionist
min_level: 3
description: You know the Minor Illusion cantrip (learn a different Wizard cantrip instead if you already know it; doesn't count against your number of cantrips known). Cast it as a Bonus Action, creating both a sound and an image with the same casting. (Also grants a passive range increase and Verbal-component waiver for your Illusion spells — not tracked as a resource.)

## Phantasmal Creatures
action_type: action   # matches Summon Beast/Summon Fey's own casting time (an Action)
resource_key: phantasmal_creatures
subclass: illusionist
min_level: 6
max_uses: 1
rest_type: long
description: Cast Summon Beast or Summon Fey (always prepared) with its school changed to Illusion, causing the summoned creature to appear spectral, without expending a spell slot — doing so halves the summoned creature's HP maximum. Usable once per Long Rest, shared between the two spells (PHB wording is ambiguous on whether casting one this way also locks out the other — modeled here as one shared use; flag to Zach if independent per-spell tracking is preferred instead).

## Illusory Self
action_type: reaction
resource_key: illusory_self
subclass: illusionist
min_level: 10
max_uses: 1
rest_type: short regain all, long regain all
bonus_recharge: expend 1 spell slot of level 2+ (no action) to restore early
description: When a creature hits you with an attack roll, interpose an illusory duplicate of yourself between the attacker and yourself; the attack automatically misses you, then the illusion dissipates.

## Illusory Reality
action_type: bonus_action   # taken on your turn while the triggering Illusion spell is ongoing — no separate resource
subclass: illusionist
min_level: 14
description: When you cast an Illusion spell with a spell slot, choose one inanimate, nonmagical object that's part of the illusion and make it real on your turn (as a Bonus Action) while the spell is ongoing. The object remains real for 1 minute, during which it can deal damage or impose conditions.

<!-- Excluded: Illusion Savant (passive spellbook addition). -->
