# Scraper Calculation Requirements

## Core Principle

The scraper should be a **standalone calculation engine** that produces complete, meaningful JSON output. All D&D mechanics calculations should be performed within the scraper itself, not deferred to downstream consumers.

## Calculation Responsibilities

### Ability Scores & Modifiers
- Calculate ability score modifiers from base scores
- Apply racial bonuses, magic item bonuses, and temporary effects
- Compute saving throw bonuses (base modifier + proficiency + magic items)
- Calculate skill bonuses (ability modifier + proficiency + expertise + magic items)

### Combat Statistics
- **Armor Class**: Base AC + Dex modifier + armor bonuses + shield + magic items
- **Hit Points**: Base HP + Con modifier per level + magic items + temporary HP
- **Attack Bonuses**: Ability modifier + proficiency + magic weapon bonuses
- **Damage Calculations**: Weapon damage + ability modifier + magic bonuses
- **Initiative**: Dex modifier + magic bonuses + class features

### Proficiency & Expertise
- Determine proficiency bonus based on character level
- Calculate skill proficiencies and expertise multipliers
- Apply tool proficiencies and language bonuses
- Compute saving throw proficiencies

### Spell Mechanics
- **Spell Attack Bonus**: Spellcasting ability modifier + proficiency bonus
- **Spell Save DC**: 8 + spellcasting ability modifier + proficiency bonus
- **Spell Slots**: Calculate available slots by class level and multiclass rules
- **Known/Prepared Spells**: Determine spell limits based on class and level

### Class Features & Abilities
- Calculate class resource pools (Ki points, Sorcery points, etc.)
- Determine feature uses per rest (short/long rest abilities)
- Apply level-based feature scaling
- Compute multiclass progression and feature interactions

## JSON Output Requirements

### Completeness
- Include all calculated values, not just raw data from D&D Beyond
- Provide both base values and final calculated results
- Include breakdown of bonuses and their sources

### Structure
```json
{
  "character_id": "12345",
  "calculated_stats": {
    "ability_scores": {
      "strength": {
        "base": 15,
        "racial_bonus": 2,
        "magic_item_bonus": 1,
        "final": 18,
        "modifier": 4
      }
    },
    "combat": {
      "armor_class": {
        "base": 10,
        "dex_modifier": 3,
        "armor_bonus": 5,
        "shield_bonus": 2,
        "magic_bonus": 1,
        "final": 21,
        "breakdown": "10 (base) + 3 (Dex) + 5 (Chain Mail) + 2 (Shield) + 1 (Magic)"
      }
    },
    "spellcasting": {
      "spell_attack_bonus": 8,
      "spell_save_dc": 16,
      "spell_slots": {
        "1": {"max": 4, "used": 1, "remaining": 3},
        "2": {"max": 3, "used": 0, "remaining": 3}
      }
    }
  }
}
```

### Standalone Nature
- JSON output should be usable by any application without additional D&D rule knowledge
- Include human-readable descriptions and breakdowns
- Provide context for calculated values (e.g., "includes +2 racial bonus")
- No external dependencies required to understand the data

## Implementation Guidelines

### Calculation Engine
- Create dedicated calculator classes for different stat categories
- Use D&D 5e rules engine with support for both 2014 and 2024 rules
- Handle edge cases and special interactions (multiclassing, feats, magic items)
- Validate calculations against known baselines

### Error Handling
- Gracefully handle missing or incomplete data from D&D Beyond
- Provide fallback calculations when possible
- Log calculation errors and assumptions made
- Include confidence levels for calculated values when uncertain

### Performance
- Cache expensive calculations within a scraping session
- Optimize for batch processing of multiple characters
- Minimize API calls by maximizing calculation from available data

### Testing
- Unit tests for all calculation functions
- Integration tests with real character data
- Regression tests to ensure calculation accuracy
- Baseline validation against known character sheets

## Integration Points

### Storage Layer
- Store both raw D&D Beyond data and calculated results
- Version calculated data separately from raw data
- Enable comparison of calculation changes over time

### Parser Layer
- Parser should consume calculated JSON without performing additional math
- Focus parser on formatting and presentation, not calculation
- Use calculated breakdowns for detailed character sheet sections

### Validation Layer
- Compare calculated values against expected baselines
- Detect and report calculation discrepancies
- Validate multiclass and complex character builds

## Quality Assurance

### Accuracy Requirements
- All calculations must match official D&D 5e rules
- Support both Player's Handbook and optional rules (Tasha's, Xanathar's, etc.)
- Handle homebrew content gracefully with clear indicators

### Documentation
- Document calculation formulas and rule sources
- Provide examples of complex calculations
- Maintain changelog of calculation logic updates

### Monitoring
- Track calculation performance and accuracy
- Alert on significant changes in calculated values
- Monitor for new D&D Beyond API changes affecting calculations