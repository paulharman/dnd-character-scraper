# Architecture Guide

## Overview

The D&D Character Scraper uses a coordinator-based architecture with clean, purpose-driven file names. The legacy "enhanced_" prefix migration is complete and all archive files have been removed.

**Updated:** 2026-02-17
**Version:** v6.5.0

---

## Scraper Calculator Architecture

```
scraper/core/calculators/
├── coordinators/              # Entry points - orchestrate calculators
│   ├── character_info.py      # Name, level, classes, species, senses
│   ├── abilities.py           # Ability scores, modifiers, breakdowns
│   ├── proficiencies.py       # Skills, tools, languages, weapons, passives
│   ├── combat.py              # AC, HP, initiative, speed, attacks
│   ├── resources.py           # Class resources, slots, charges
│   ├── spellcasting.py        # Spell save DC, slots, caster level
│   ├── features.py            # Class features, feats, racial traits
│   └── equipment.py           # Inventory, wealth, encumbrance, infusions
├── character_calculator.py    # Main facade - runs pipeline, post-processes
├── ability_scores.py          # Ability score calculations
├── armor_class.py             # AC calculations
├── hit_points.py              # HP calculations
├── weapon_attacks.py          # Weapon attack calculations
├── attack.py                  # Attack roll helpers
├── action_attacks.py          # Action-based attack logic
├── spellcasting_calculator.py # Spellcasting calculations
├── spellcasting.py            # Spell slot/level logic
├── proficiency.py             # Proficiency classification and bonuses
├── skill_bonus_calculator.py  # Skill bonus calculations
├── encumbrance.py             # Carry weight calculations
├── speed.py                   # Movement speed calculations
├── class_features.py          # Feature extraction
├── class_resource_calculator.py # Resource tracking calculations
├── resource_tracking.py       # Resource state tracking
├── container_inventory.py     # Container/bag of holding logic
├── equipment_details.py       # Equipment property extraction
├── wealth.py                  # Currency calculations
├── character_appearance.py    # Appearance/traits extraction
├── damage_calculator.py       # Damage calculations
├── advanced_character_details.py # Additional character details
└── base.py                    # Base calculator class
```

### Usage

Always import via **coordinators** - they orchestrate the underlying calculators:

```python
from scraper.core.calculators.coordinators.abilities import AbilitiesCoordinator
from scraper.core.calculators.coordinators.combat import CombatCoordinator
from scraper.core.calculators.coordinators.proficiencies import ProficienciesCoordinator
```

---

## Discord Services

```
discord/
├── services/
│   └── notification_manager.py        # Discord webhook notifications
└── core/
    ├── services/
    │   ├── change_detection_service.py # Change detection orchestration
    │   ├── change_detectors.py         # Per-field change detectors
    │   └── config_service.py           # Discord configuration
    └── models/
        ├── change_detection_models.py  # Change types, field mappings
        └── config_models.py            # Configuration models
```

---

## Parser Formatters

```
parser/formatters/
├── metadata.py          # YAML frontmatter (all structured data)
├── character_info.py    # Character infobox and stats table
├── abilities.py         # Ability scores, saves, skills
├── proficiency.py       # Weapon/armor/tool/instrument/language sections
├── combat.py            # Actions, attacks, special abilities
├── spellcasting.py      # Spell stats, slots, spell lists
├── inventory.py         # Wealth, encumbrance, items
├── features.py          # Feats, class features, resources
├── racial_traits.py     # Species traits and abilities
└── background.py        # Appearance, background, backstory
```

---

## Obsidian JSX Components

```
obsidian/
├── PartyStatsHub.jsx          # Party dashboard (abilities, skills, saves, passives)
├── SpellGenerator.jsx         # Cross-character spell lookup
├── MonsterHub.jsx             # Monster bestiary browser
├── InventoryManager.jsx       # Character inventory viewer
├── PartyInventoryManager.jsx  # Party shared inventory
├── PartyLanguages.jsx         # Party language coverage
├── InfusionsManager.jsx       # Artificer infusions
├── SpellQuery.jsx             # Single-character spell list
├── SessionNotesSearch.jsx     # Session event search
└── sessiontracker.jsx         # Session event tracker
```

---

## Key Architectural Patterns

1. **Coordinator Pattern**: Each coordinator manages a domain of calculations, declaring dependencies for topological execution ordering.

2. **Pipeline Execution**: `CalculationPipeline` sorts coordinators by dependency/priority and executes them in order, passing results through shared context.

3. **Frontmatter Interface**: MetadataFormatter writes all structured data as YAML frontmatter, which JSX components read via DataCore's `getVal()`/`getNum()`/`getStr()`.

4. **Change Detection**: Discord notifier compares old vs new character snapshots with causation analysis for cascading changes.

---

## Related Documentation

- [DATA_PIPELINE_REFERENCE.md](DATA_PIPELINE_REFERENCE.md) - End-to-end field mapping through every pipeline stage
- [configuration_guide.md](configuration_guide.md) - Configuration reference
- [discord_configuration_guide.md](discord_configuration_guide.md) - Discord setup guide
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
