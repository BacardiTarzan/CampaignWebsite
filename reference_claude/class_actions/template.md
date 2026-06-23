# ClassName

<!-- Copy this file and name it {classname_lowercase}.md in this directory. -->
<!-- The seeder reads it automatically when a character of this class is added to combat. -->

## Ability Name
action_type: action
resource_key: ability_snake_case
min_level: 1
max_uses: 1
rest_type: short
description: One sentence describing what this does.

## Another Ability (Bonus Action)
action_type: bonus_action
resource_key: another_ability
min_level: 2
max_uses: level
rest_type: long
description: 'level' in max_uses is replaced by the character's level at combat-add time.

## Passive Ability (for reminders)
action_type: passive
resource_key: passive_ability
min_level: 1
max_uses: 1
rest_type: short
description: Tracked in resource strip only, not shown in action list. Good for per-turn reminders like Sneak Attack.
