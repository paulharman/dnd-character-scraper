# Character Validation Guide

This guide explains how to create and use validation data to verify the accuracy of the D&D Beyond character scraper.

## Overview

The validation system works by creating "ground truth" data files that contain manually verified information from D&D Beyond character sheets. These are then compared against scraper output to detect discrepancies.

## Files

- `character_validation_template.json` - Base template with all fields
- `create_validation_template.py` - Script to create and compare validation data
- `validation_data/` - Directory containing character-specific validation files

## Quick Start

### 1. Create validation templates for all characters
```bash
python3 create_validation_template.py --create
```

This creates validation files for all 12 test characters in the `validation_data/` directory.

### 2. Fill in validation data

For each character, open their validation file (e.g., `validation_data/144986992_validation.json`) and:

1. **Open the D&D Beyond character sheet** in your browser
2. **Fill in the template** by copying values from the character sheet
3. **Focus on key fields** (you don't need to fill everything for basic validation)

#### Essential Fields to Fill:
- `basic_info`: name, level, classes, species/race, background
- `ability_scores`: all 6 scores and modifiers
- `calculated_values`: proficiency bonus, AC, HP, initiative, speed
- `spellcasting`: spell save DC, spell attack bonus, total spells, spell slots
- `proficiencies.saving_throws`: which saves are proficient
- `proficiencies.skills`: list skills with sources (Class/Background/Race)

#### Optional Fields:
- `key_features`: major class/racial features
- `inventory_summary`: basic inventory info
- `validation_notes`: any special notes or expected issues

### 3. Run the scraper and compare

```bash
# Run scraper for a character
python3 enhanced_dnd_scraper.py 144986992 --output test_results_full/144986992.json

# Compare with validation data
python3 create_validation_template.py --compare validation_data/144986992_validation.json --scraper-output test_results_full/144986992.json
```

## Validation Tips

### Rule Version Detection
- **2024 Rules**: Character sheet has updated layout, uses "Species" instead of "Race"
- **2014 Rules**: Traditional layout, uses "Race"
- Check source books used - PHB (2024) vs PHB (2014)

### HP Calculation Verification
1. Check if character uses "Fixed" or "Manual" hit points in D&D Beyond settings
2. **Fixed HP**: Level 1 = max die + CON, other levels = average die + CON
3. **Manual HP**: Player rolled or manually set values

### Ability Score Sources
- Note if scores come from point buy, rolling, racial bonuses, ASIs, magic items
- 2024 rules handle ability score increases differently than 2014

### Spellcasting Verification
- Count total spells in all spell lists (class, racial, background, feat, item)
- Verify spell save DC = 8 + prof bonus + spellcasting ability modifier
- Check spell slots match class progression and multiclassing rules

### Proficiency Sources
Common sources:
- **Class**: Skills from class skill list
- **Background**: Usually 2 skills
- **Species/Race**: Often 1-2 skills (e.g., Perception for Elves)
- **Feats**: May grant skill proficiencies

## Example Workflow

```bash
# 1. Create template for Vaelith (character 144986992)
python3 create_validation_template.py --character-id 144986992

# 2. Open D&D Beyond and fill in validation_data/144986992_validation.json

# 3. Run scraper
python3 enhanced_dnd_scraper.py 144986992 --output vaelith_scraper.json

# 4. Compare results
python3 create_validation_template.py --compare validation_data/144986992_validation.json --scraper-output vaelith_scraper.json
```

## Batch Validation

After filling in multiple validation files, you can run the comprehensive test:

```bash
# Test all characters and generate both scraper data and validation comparisons
python3 test_all_characters.py

# Then compare each character's results
for file in validation_data/*_validation.json; do
    char_id=$(basename $file _validation.json)
    python3 create_validation_template.py --compare $file --scraper-output test_results_full/$char_id.json
done
```

## Character Priority

Focus on these characters first for validation (they represent different rule sets and complexity):

1. **144986992** (Vaelith) - 2024 Sorcerer, good for spellcasting validation
2. **145081718** - Different class/complexity
3. **29682199** - Different rule set or features
4. **147061783** - Multiclass or complex character

## Troubleshooting

### Common Discrepancies
- **Rule version misdetection**: Check source books used
- **HP calculation**: Verify Fixed vs Manual setting
- **Spell counts**: Check all spell sources (class, race, background, feats, items)
- **Proficiency sources**: Verify skill source attribution

### False Positives
Some discrepancies might be expected:
- Rounding differences in calculations
- Different formatting of text descriptions
- Optional fields the scraper doesn't extract

Document these in the `validation_notes.known_issues` field.