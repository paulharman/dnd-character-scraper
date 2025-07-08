# Simple Validation Guide

Quick guide for manually verifying character data against D&D Beyond.

## What to Fill In

Each validation file has these simple fields to copy from D&D Beyond:

### Basic Info
```json
"character_id": 144986992,
"name": "Vaelith Duskthorn",
"level": 2,
"classes": [{"name": "Sorcerer", "level": 2, "subclass": ""}],
"species": "Elf",
"background": "Noble",
"is_2024_rules": true
```

### Ability Scores (copy directly from character sheet)
```json
"ability_scores": {
  "strength": 12,
  "dexterity": 14,
  "constitution": 12,
  "intelligence": 12,
  "wisdom": 6,
  "charisma": 18
},
"ability_modifiers": {
  "strength": 1,
  "dexterity": 2,
  "constitution": 1,
  "intelligence": 1,
  "wisdom": -2,
  "charisma": 4
}
```

### Key Stats
```json
"proficiency_bonus": 2,
"armor_class": 12,
"max_hp": 13,
"hit_point_type": "Fixed",
"initiative": 2,
"speed": 30
```

### Spellcasting (if applicable)
```json
"spellcasting": {
  "is_spellcaster": true,
  "spell_save_dc": 14,
  "spell_attack_bonus": 6,
  "spellcasting_ability": "charisma",
  "total_spells": 9,
  "cantrips": 5,
  "spell_slots_level_1": 3
}
```

### Proficiencies
```json
"saving_throws": ["constitution", "charisma"],
"skills": [
  {"name": "Arcana", "source": "Class"},
  {"name": "History", "source": "Background"},
  {"name": "Intimidation", "source": "Class"},
  {"name": "Perception", "source": "Species"},
  {"name": "Persuasion", "source": "Background"}
]
```

## Quick Workflow

1. **Open validation file**: `validation_data/144986992_validation.json`
2. **Open D&D Beyond**: Go to the character sheet
3. **Copy values**: Fill in the fields above
4. **Test**: Run comparison script

```bash
# Test one character
python3 enhanced_dnd_scraper.py 144986992 --output test.json
python3 create_validation_template.py --compare validation_data/144986992_validation.json --scraper-output test.json
```

## Quick Tips

- **Hit Point Type**: Check character settings - "Fixed" or "Manual"
- **2024 Rules**: Look for "Species" instead of "Race", new spell names
- **Skill Sources**: Class (from class list), Background (usually 2), Species (racial), Feat
- **Spell Count**: Count all spells in all tabs (class, racial, background, etc.)
- **Initiative**: Number only (e.g., 2, not +2)

## Priority Characters

Start with these for basic validation:
1. **144986992** (Vaelith) - Simple 2024 Sorcerer
2. **145081718** - Different class
3. **29682199** - Different complexity

Only fill in fields you can easily verify. Leave others as 0 or empty.