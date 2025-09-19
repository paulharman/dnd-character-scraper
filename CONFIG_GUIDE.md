# Configuration Guide

This guide explains the configuration options available in the D&D Beyond Character Scraper v6.0.0.

The project uses a modular configuration approach with separate files for different components:
- `config/main.yaml` - Project-wide settings and environment configuration
- `config/discord.yaml` - Discord notifications and change tracking
- `config/parser.yaml` - Markdown generation and formatting
- `config/scraper.yaml` - API settings and rate limiting

## Discord Configuration (`config/discord.yaml`)

### Core Settings
```yaml
# Discord webhook for notifications
webhook_url: ${DISCORD_WEBHOOK_URL}     # Use environment variable for security
character_id: 145081718                 # D&D Beyond character ID to monitor

# Monitoring behavior
run_continuous: false                   # Run once vs continuous monitoring
check_interval_seconds: 600             # Check interval (10 minutes)
log_level: INFO                         # Logging level: DEBUG, INFO, WARNING, ERROR
```

### Party Monitoring
```yaml
# Monitor multiple characters (party mode)
party:
- character_id: '145081718'             # Add character IDs to monitor multiple
```

### Discord Message Settings
```yaml
discord:
  username: D&D Beyond Monitor          # Bot username in Discord messages
  avatar_url: null                      # Bot avatar (null = use character avatar)
  timezone: UTC                         # Timezone for timestamps
  
  # Content filtering
  min_priority: LOW                     # Minimum priority: LOW, MEDIUM, HIGH, CRITICAL
  include_attribution: true             # Show what caused each change
  include_causation: true               # Include causation analysis
  include_timestamps: true              # Show when changes occurred
  
  # Visual formatting
  use_embeds: true                      # Use rich Discord embeds
  color_code_by_priority: true          # Color by priority (red=HIGH, yellow=MEDIUM, blue=LOW)
  group_related_changes: true           # Group similar changes together
  detail_level: summary                 # summary, detailed, or comprehensive
  
  # Performance settings
  maximum_changes_per_notification: 200 # Max changes per message
  delay_between_messages: 2.0           # Seconds between multiple messages
```

### Field-Based Change Detection
The system uses field patterns to determine change priorities. You can customize which fields trigger notifications and their priority levels:

```yaml
detection:
  # HIGH PRIORITY - Critical character progression (red embeds)
  field_patterns:
    character_info.level: HIGH                    # Level changes
    character.abilityScores.*: HIGH               # Ability score changes
    character.species: HIGH                       # Species/race changes
    
    # MEDIUM PRIORITY - Important gameplay changes (yellow embeds)
    character.hit_points.maximum: MEDIUM          # Max HP changes
    character.spellcasting.spell_save_dc: MEDIUM  # Spell save DC
    equipment.*.equipped: MEDIUM                  # Equipment changes
    character.spells.*: MEDIUM                    # Spell changes
    character.feats.*: MEDIUM                     # Feat changes
    
    # LOW PRIORITY - Minor changes (blue embeds)
    character.hit_points.temporary: LOW           # Temporary HP
    character.skills.*: LOW                       # Skill bonuses
    character.personality.*: LOW                  # Personality traits
    
    # IGNORED - No notifications
    character.hit_points.current: IGNORED         # Current HP changes
    character.metadata.*: IGNORED                 # Internal metadata
```

### Field Pattern Examples
| Pattern | Matches | Priority |
|---------|---------|----------|
| `character_info.level` | Character level | HIGH |
| `character.abilityScores.*` | All ability scores | HIGH |
| `equipment.*.equipped` | Any equipment status | MEDIUM |
| `character.spells.*` | All spell changes | MEDIUM |
| `character.skills.*` | All skill changes | LOW |
| `character.metadata.*` | Metadata (ignored) | IGNORED |

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
```yaml
# Project settings
project:
  name: "DnD Beyond Character Scraper"
  version: "6.0.0"
  description: "Enhanced D&D Beyond character scraper with 2024 rules support"

# Environment configuration  
environment: "production"        # Environment: development, testing, production
debug: false                    # Enable debug mode for troubleshooting

# Global paths
paths:
  character_data: "character_data"     # Primary storage for character data
  spells_folder: "obsidian/spells"     # Enhanced spell descriptions
  config_dir: "config"                 # Configuration files directory

# Global logging
logging:
  level: "INFO"                        # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Scraper Configuration (`config/scraper.yaml`)
```yaml
# D&D Beyond API settings
api:
  base_url: "https://character-service.dndbeyond.com/character/v5/character/"
  user_agent: "DnDBeyond-Enhanced-Scraper/6.0.0"
  timeout: 30                   # Request timeout in seconds
  max_retries: 3                # Maximum retry attempts
  retry_delay: 30               # Delay between retries in seconds

# Rate limiting (respects D&D Beyond API limits)
rate_limit:
  delay_between_requests: 30    # Required 30-second delay between API calls

# Calculation constants
calculations:
  spell_save_dc_base: 8         # Base value for spell save DC (8 + prof + modifier)
```

**Important**: The 30-second delay respects D&D Beyond's API limits and should not be modified.

### Rules Configuration (`config/rules/`)
- D&D 2014 rules (`2014.yaml`)
- D&D 2024 rules (`2024.yaml`)
- Game constants (`constants.yaml`)

## Usage Tips

1. **Discord Filtering**: To reduce notification noise, set `min_priority` to MEDIUM or HIGH in `config/discord.yaml`, or set unwanted field patterns to IGNORED.

2. **Section Ordering**: Customize your character sheet layout by reordering the sections in `config/parser.yaml`.

3. **Field Pattern Customization**: Add new field patterns or change priorities in the `detection.field_patterns` section.

4. **Party Monitoring**: Add multiple character IDs to the `party` list to monitor an entire D&D party.

5. **Environment Security**: Use environment variables like `${DISCORD_WEBHOOK_URL}` for secure configuration.

6. **Validation**: The configuration system validates all settings when loaded. Check the logs for any configuration errors.

## Example Configurations

### Minimal Discord Notifications
```yaml
# Only monitor critical changes (level ups, ability scores)
discord:
  min_priority: HIGH              # Only HIGH priority changes
  
detection:
  field_patterns:
    character_info.level: HIGH
    character.abilityScores.*: HIGH
    character.species: HIGH
    # Set everything else to IGNORED
    character.spells.*: IGNORED
    equipment.*: IGNORED
    character.hit_points.*: IGNORED
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