# Configuration Guide

This guide explains the configuration options available in the D&D Beyond Character Scraper.

## Discord Configuration (`config/discord.yaml`)

### Core Settings
```yaml
enabled: true                     # Enable/disable Discord integration
webhook_url: "https://discord.com/api/webhooks/..."  # Discord webhook URL
username: "D&D Beyond Scraper"    # Bot username in Discord
avatar_url: null                  # Optional bot avatar URL
```

### Notification Settings
```yaml
format_type: "detailed"           # Options: "compact", "detailed", "json"
min_priority: "LOW"               # Options: "LOW", "MEDIUM", "HIGH", "CRITICAL"
max_changes_per_notification: 200 # Maximum changes per notification
timezone: "UTC"                   # Timezone for timestamps
```

### Change Type Filtering
You can control which types of character changes trigger Discord notifications by modifying the `change_types` list. Remove any types you don't want to monitor:

```yaml
change_types:
  - "level"              # Character level changes
  - "experience"         # Experience point changes  
  - "hit_points"         # HP/health changes
  - "armor_class"        # AC changes
  - "ability_scores"     # Strength, Dex, Con, Int, Wis, Cha changes
  - "spells_known"       # New spells learned
  - "spell_slots"        # Spell slot changes
  - "inventory_items"    # Items added/removed from inventory
  - "equipment"          # Equipment changes
  - "currency"           # Gold/currency changes
  - "skills"             # Skill proficiency changes
  - "proficiencies"      # Other proficiency changes
  - "feats"              # Feat changes
  - "class_features"     # Class feature changes
  - "appearance"         # Appearance/avatar changes
  - "background"         # Background changes
```

### Change Type to Group Mapping
The system internally maps change types to notification groups:

| Change Type | Group | Description |
|-------------|-------|-------------|
| `level`, `experience`, `class_features` | `basic` | Core character progression |
| `hit_points`, `armor_class` | `combat` | Combat-related stats |
| `ability_scores` | `abilities` | Ability score changes |
| `spells_known`, `spell_slots` | `spells` | Spellcasting changes |
| `inventory_items`, `equipment`, `currency` | `inventory` | Items and wealth |
| `skills`, `proficiencies`, `feats` | `skills` | Skills and proficiencies |
| `appearance` | `appearance` | Visual appearance |
| `background` | `backstory` | Background and story |

## Parser Configuration (`config/parser.yaml`)

### Default Behavior
```yaml
parser:
  defaults:
    enhance_spells: true           # Use enhanced spell data from local files
    use_dnd_ui_toolkit: true      # Generate DnD UI Toolkit compatible blocks
    verbose: false                # Enable verbose logging
```

### Template Settings
```yaml
  templates:
    jsx_components_dir: "z_Templates"              # Directory for JSX components
    inventory_component: "InventoryManager.jsx"   # Inventory management component
    spell_component: "SpellQuery.jsx"             # Spell management component
```

### Output Formatting
```yaml
  output:
    section_order:                # Order of sections in generated markdown
      - "metadata"                # Character metadata
      - "character_info"          # Basic character information
      - "abilities"               # Ability scores and modifiers
      - "appearance"              # Physical appearance
      - "spellcasting"            # Spells and spellcasting
      - "features"                # Class features and abilities
      - "racial_traits"           # Racial traits
      - "combat"                  # Combat stats and attacks
      - "proficiency"             # Proficiencies and skills
      - "background"              # Background information
      - "backstory"               # Character backstory
      - "inventory"               # Equipment and inventory
```

### Available Sections
You can reorder the sections in your character sheet by modifying the `section_order` list:

| Section | Description |
|---------|-------------|
| `metadata` | Character metadata and technical information |
| `character_info` | Name, level, class, race, etc. |
| `abilities` | Ability scores, modifiers, and saving throws |
| `appearance` | Physical description and appearance |
| `spellcasting` | Spells, spell slots, and spellcasting abilities |
| `features` | Class features, racial traits, and special abilities |
| `racial_traits` | Racial traits and features |
| `combat` | Combat stats, attacks, and defenses |
| `proficiency` | Proficiencies, skills, and expertise |
| `background` | Background information and features |
| `backstory` | Character backstory and personal details |
| `inventory` | Equipment, items, and wealth |

### Spell Enhancement
```yaml
  spell_enhancement:
    enabled: true                  # Enable spell enhancement features
```

### Discord Integration
```yaml
  discord:
    enabled: true                 # Enable Discord notifications when parsing
```

## Other Configuration Files

### Main Configuration (`config/main.yaml`)
- Project settings
- Environment configuration
- Global logging settings
- Feature flags

### Scraper Configuration (`config/scraper.yaml`)
- API settings
- Output preferences
- Processing options

### Rules Configuration (`config/rules/`)
- D&D 2014 rules (`2014.yaml`)
- D&D 2024 rules (`2024.yaml`)
- Game constants (`constants.yaml`)

## Usage Tips

1. **Discord Filtering**: To reduce notification noise, remove change types you don't care about from the `change_types` list in `config/discord.yaml`.

2. **Section Ordering**: Customize your character sheet layout by reordering the sections in `config/parser.yaml`.

3. **Environment Overrides**: Use files in `config/environments/` to override settings for different environments (development, production, testing).

4. **Validation**: The configuration system validates all settings when loaded. Check the logs for any configuration errors.

## Example Configurations

### Minimal Discord Notifications
```yaml
# Only monitor important changes
change_types:
  - "level"
  - "hit_points"
  - "spells_known"
  - "class_features"
```

### Combat-Focused Character Sheet
```yaml
# Put combat information first
section_order:
  - "metadata"
  - "character_info"
  - "combat"
  - "abilities"
  - "spellcasting"
  - "features"
  - "proficiency"
  - "inventory"
  - "appearance"
  - "background"
  - "backstory"
  - "racial_traits"
```