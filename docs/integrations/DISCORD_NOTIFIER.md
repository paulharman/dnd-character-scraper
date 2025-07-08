# Discord Notifier for D&D Beyond Character Changes

## Overview

The Discord Notifier is a sophisticated monitoring system that tracks changes to D&D Beyond characters and sends filtered notifications to Discord webhooks. It features a comprehensive data group system that allows fine-grained control over what changes are reported.

**⚠️ BREAKING CHANGES IN v6.0.0**: This documentation has been updated to reflect the new modular architecture. See [Migration Guide](#migration-from-pre-v60) for upgrade instructions.

## Features

### 🎯 Data Group System
- **Core Groups**: basic, stats, combat, spells, inventory, features, appearance, background, meta
- **Nested Groups**: Granular control like `combat.hp`, `spells.slots`, `stats.abilities`
- **Composite Groups**: Convenient presets like `progression`, `mechanics`, `roleplay`
- **Smart Filtering**: Include/exclude patterns with wildcard support

### 📊 Change Detection
- Automatic comparison between character snapshots
- Priority-based change classification (HIGH, MEDIUM, LOW)
- Detailed change tracking with source attribution
- Intelligent field path matching

### 🎛️ Presets
- **combat_only**: Track combat stats, spell slots, and equipment
- **level_up**: Track character advancement and progression
- **roleplay_session**: Focus on story elements and wealth changes
- **shopping_trip**: Track equipment changes, ignore wealth fluctuations
- **minimal**: Only essential changes (level, hit points)
- **debug**: Everything including system metadata

### 📝 Output Formats
- **Detailed**: Full change descriptions with priority grouping
- **Compact**: Summarized view highlighting critical changes
- **JSON**: Machine-readable format for integration

### ⚙️ Configuration
- YAML configuration file support
- Environment variable integration
- CLI argument overrides
- Flexible webhook management

## Quick Start

### 1. Installation

Ensure you have Python 3.8+ and install dependencies:

```bash
# Install main project dependencies (includes all Discord requirements)
pip install -r requirements.txt

# Verify Discord-specific dependencies are installed
pip install aiohttp pyyaml  # Usually already included in requirements.txt
```

**Note**: The v6.0.0 architecture includes all necessary dependencies in the main requirements.txt file.

### 2. Discord Webhook Setup

1. In your Discord server, go to Server Settings → Integrations → Webhooks
2. Create a new webhook or edit an existing one
3. Copy the webhook URL (it looks like: `https://discord.com/api/webhooks/123456789/abcdef...`)

### 3. Configuration

Create a configuration file:

```bash
# Copy the example configuration
cp discord_config.yml.example discord_config.yml

# Edit with your settings
nano discord_config.yml
```

Minimal configuration:

```yaml
webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_TOKEN"
character_id: "145081718"
filtering:
  preset: "level_up"
```

### 4. Basic Usage

```bash
# Check once and exit
python discord_monitor.py --test

# Monitor continuously (default: every 10 minutes)
python discord_monitor.py

# Use a specific config file
python discord_monitor.py --config my_config.yml

# Verbose logging
python discord_monitor.py --verbose
```

**Note**: The main script has been renamed from `discord_notifier.py` to `discord_monitor.py` in v6.0.0.

## Data Groups Reference

### Core Groups

| Group | Priority | Description | Example Fields |
|-------|----------|-------------|----------------|
| `basic` | HIGH | Character identity and progression | level, experience, classes |
| `stats` | HIGH | Ability scores, skills, saves | ability_scores.*, skills.* |
| `combat` | HIGH | Combat statistics | hit_points.*, armor_class.* |
| `spells` | HIGH | Spellcasting data | spell_slots.*, spells.* |
| `inventory` | MEDIUM | Equipment and wealth | inventory.*, currencies.* |
| `features` | MEDIUM | Traits, feats, actions | feats.*, species.traits.* |
| `appearance` | LOW | Physical description | appearance.*, avatarUrl |
| `background` | LOW | Backstory and personality | ideals, bonds, flaws, notes |
| `meta` | LOW | System metadata | timestamps, diagnostics |

### Nested Groups

Nested groups provide granular control within core groups:

```bash
# Combat subgroups
combat.ac          # Armor class only
combat.hp          # Hit points only
combat.initiative  # Initiative only
combat.speed       # Speed only

# Spell subgroups  
spells.known       # Known spells only
spells.slots       # Spell slots only

# Stats subgroups
stats.abilities    # Ability scores only
stats.skills       # Skills only
stats.saves        # Saving throws only

# Inventory subgroups
inventory.equipment # Equipment only
inventory.wealth    # Money only
```

### Composite Groups

Pre-defined combinations for common scenarios:

| Group | Includes | Use Case |
|-------|----------|----------|
| `progression` | basic + stats.abilities + features.feats + spells | Level-up tracking |
| `mechanics` | basic + stats + combat + spells + features | Game mechanics focus |
| `roleplay` | appearance + background | Story and character development |
| `resources` | combat.hp + spells.slots + inventory.wealth | Resource management |

## Command Line Interface

### Basic Commands

```bash
# Information commands
python discord_notifier.py --list-groups
python discord_notifier.py --describe-group combat
python discord_notifier.py --explain-preset level_up

# Monitoring commands
python discord_notifier.py <character_id> [options]
```

### Filtering Options

```bash
# Include specific groups
--include "basic,combat,spells.slots"

# Exclude specific groups  
--exclude "meta,appearance"

# Use a preset
--preset level_up

# Combine preset with custom excludes
--preset debug --exclude "meta.diagnostics"
```

### Monitoring Options

```bash
# Check once and exit
--once

# Custom check interval (seconds)
--interval 600

# Dry run (show what would be tracked)
--dry-run

# Session cookie for private characters
--session-cookie "your_cookie_here"
```

### Output Options

```bash
# Output format
--format detailed|compact|json

# Verbose logging
--verbose

# Show field paths (useful for debugging)
--show-field-paths
```

## Configuration File Reference

### Basic Configuration

```yaml
# Required settings
webhook_url: "https://discord.com/api/webhooks/ID/TOKEN"
character_id: "145081718"

# Optional settings
check_interval: 600        # 10 minutes
format_type: "detailed"    # compact, detailed, json
storage_dir: "character_data"
scraper_path: "scraper/enhanced_dnd_scraper.py"  # Updated path for v6.0.0
log_level: "INFO"

# Session cookie for private characters
session_cookie: "optional_cookie"
```

### Filtering Configuration

```yaml
filtering:
  # Use a preset
  preset: "level_up"
  
  # OR custom groups (overrides preset)
  include_groups:
    - "basic"
    - "combat"
    - "spells.slots"
  
  exclude_groups:
    - "meta"
    - "appearance"
```

### Advanced Configuration

```yaml
# Notification customization
notifications:
  username: "D&D Beyond Monitor"
  timezone: "UTC"

# Advanced settings
advanced:
  max_changes_per_notification: 20
  rate_limit:
    requests_per_minute: 3
  retry:
    max_attempts: 3
    backoff_factor: 2
```

## Usage Examples

### Combat Session Monitoring

Perfect for active gameplay sessions where you want to track combat-relevant changes:

```bash
python discord_notifier.py 145081718 --preset combat_only --interval 60
```

This tracks:
- Hit point changes
- Armor class modifications
- Spell slot usage
- Equipment swaps affecting combat

### Level-Up Tracking

Ideal for tracking character advancement:

```bash
python discord_notifier.py 145081718 --preset level_up
```

This tracks:
- Level increases
- Ability score improvements
- New feats and features
- Spell progression
- Experience gains

### Shopping Trip

Monitor equipment changes while ignoring wealth fluctuations:

```bash
python discord_notifier.py 145081718 --include "inventory,combat.ac" --exclude "inventory.wealth"
```

### Custom Session Monitoring

Track specific elements for your campaign:

```bash
python discord_notifier.py 145081718 \
  --include "basic,combat.hp,spells.slots,inventory.equipment" \
  --exclude "meta" \
  --format compact
```

## Testing and Validation

### Test the Configuration

```bash
# Validate filtering without sending notifications
python discord_notifier.py 145081718 --dry-run --show-field-paths

# Test with verbose output
python discord_notifier.py 145081718 --dry-run --verbose
```

### Run Test Suite

```bash
# Run comprehensive tests
python test_discord_notifier.py
```

The test suite validates:
- Data group filtering accuracy
- Character comparison logic
- Discord message formatting
- Storage functionality
- Integration with baseline data

## Integration with v6.0.0 Architecture

The Discord Notifier integrates seamlessly with the v6.0.0 character scraper:

### Character Data Flow

1. **Fetching**: Uses `scraper/enhanced_dnd_scraper.py` with the new modular architecture
2. **Processing**: Leverages the new calculator system and rule version management
3. **Storage**: Saves character snapshots in JSON format using the v6.0.0 data structure
4. **Comparison**: Detects changes between current and previous snapshots
5. **Filtering**: Applies data group filters to reduce noise
6. **Notification**: Sends formatted changes to Discord

### New v6.0.0 Features

- **Rule Version Detection**: Automatically detects 2014 vs 2024 rule versions for accurate calculations
- **Enhanced Calculators**: Uses specialized calculators for different character aspects (AC, HP, spells, etc.)
- **Configuration Management**: Integrated with the new YAML-based config system
- **Improved Error Handling**: Better diagnostics and error reporting
- **Modular Architecture**: Clean separation of concerns with specialized services
- **Container Inventory**: Enhanced tracking of items within bags and containers
- **Advanced Spellcasting**: Better handling of multiclass spellcasting and spell slots

### Rule Version Support

The v6.0.0 architecture includes sophisticated rule version detection:

```yaml
# Optional: Force a specific rule version
advanced:
  rule_version: "2024"  # Options: "2014", "2024", "auto" (default)
```

This ensures that character calculations (AC, HP, spells) use the appropriate rule set for accurate change detection.

### Data Group Mapping

The data groups map directly to the v6.0.0 JSON structure:

```json
{
  "basic_info": {           // basic group
    "name": "...",
    "level": 5,
    "total_level": 5,
    "classes": [...],
    "hit_points": {...},    // combat.hp group
    "armor_class": {...}    // combat.ac group
  },
  "ability_scores": {...},  // stats.abilities group
  "spells": {               // spells.known group
    "known_spells": [...],
    "spell_attack_bonus": 7,
    "spell_save_dc": 15
  },
  "spell_slots": {...},     // spells.slots group
  "inventory": {            // inventory.equipment group
    "equipment": [...],
    "containers": [...],    // New in v6.0.0
    "currencies": {...}
  },
  "features": {             // features group
    "feats": [...],
    "species": {...},
    "background": {...}
  },
  "meta": {                 // meta group
    "scraper_version": "6.0.0",
    "rule_version": "2024",
    "timestamp": "...",
    "diagnostics": {...}
  }
}
```

**New in v6.0.0:**
- Enhanced container tracking within inventory
- Rule version metadata for accurate calculations
- Improved diagnostic information
- Better class and multiclass support

## Error Handling and Logging

### Common Issues and Solutions

1. **Webhook URL Invalid**
   ```
   Error: Failed to send Discord notification
   Solution: Verify webhook URL format and permissions
   ```

2. **Character Not Found**
   ```
   Error: Failed to fetch character data
   Solution: Check character ID and session cookie for private characters
   ```

3. **Rate Limiting**
   ```
   Warning: Rate limit exceeded
   Solution: Increase check interval or reduce notification frequency
   ```

4. **Module Import Errors (v6.0.0)**
   ```
   Error: ModuleNotFoundError: No module named 'src.services'
   Solution: Update import paths to use relative imports (see Migration Guide)
   ```

5. **Scraper Path Issues**
   ```
   Error: FileNotFoundError: enhanced_dnd_scraper.py not found
   Solution: Update scraper_path to "scraper/enhanced_dnd_scraper.py" in config
   ```

6. **Configuration Format Errors**
   ```
   Error: YAML parsing error
   Solution: Verify YAML syntax and use the new v6.0.0 configuration format
   ```

7. **Rule Version Detection Issues**
   ```
   Warning: Unable to detect rule version
   Solution: Manually specify rule version in configuration or check character data
   ```

### Logging Levels

- `DEBUG`: Detailed execution information
- `INFO`: General operational messages
- `WARNING`: Non-critical issues
- `ERROR`: Error conditions

Set logging level in config file or with `--verbose` flag.

## Migration from Pre-v6.0.0

If you're upgrading from an earlier version of the Discord notifier, follow these steps:

### 1. Update Configuration Files

**Old configuration format:**
```yaml
scraper_path: "enhanced_dnd_scraper.py"
```

**New configuration format:**
```yaml
scraper_path: "scraper/enhanced_dnd_scraper.py"
```

### 2. Update Script Names

- `discord_notifier.py` → `discord_monitor.py`
- Command line interface has been updated

### 3. Update Import Paths

If you're using the Discord services programmatically:

**Old imports:**
```python
from src.services.notification_manager import NotificationManager
from src.formatters.discord_formatter import FormatType
```

**New imports:**
```python
from services.notification_manager import NotificationManager
from formatters.discord_formatter import FormatType
```

### 4. Configuration System Changes

The new v6.0.0 architecture includes:
- Enhanced configuration management with environment-aware settings
- Improved rule version detection and management
- Better error handling and diagnostics

### 5. Deprecated Features

- **Command line arguments**: Some CLI arguments have changed. Use `python discord_monitor.py --help` for current options.
- **Old scraper paths**: Hardcoded paths to the old scraper location will not work.

### 6. Verification

After migration, test your setup:

```bash
# Test Discord connection
python discord_monitor.py --test

# Run with verbose logging to check for issues
python discord_monitor.py --verbose
```

## Advanced Features

### Private Character Support

For private characters, use a session cookie:

```bash
python discord_notifier.py 145081718 --session-cookie "your_session_cookie"
```

Or in configuration:

```yaml
session_cookie: "your_session_cookie_here"
```

### Multiple Character Monitoring

While not yet implemented, the architecture supports monitoring multiple characters:

```yaml
# Future feature
characters:
  - character_id: "145081718"
    nickname: "Elara the Wizard"
    filtering:
      preset: "level_up"
  
  - character_id: "147061783"
    nickname: "Thorin Fighter"
    filtering:
      include_groups: ["combat", "inventory.equipment"]
```

### Custom Data Groups

Advanced users can define custom groups:

```yaml
# Future feature
custom_groups:
  my_combat_group:
    description: "Custom combat tracking"
    fields:
      - "basic_info.hit_points.*"
      - "basic_info.armor_class.*"
      - "spell_slots.level_1"
    priority: "HIGH"
```

## API Rate Limiting

The Discord Notifier respects API rate limits:

- **D&D Beyond**: 30-second delay between character fetches
- **Discord**: Built-in rate limiting with retry logic
- **Configurable**: Adjust intervals and retry settings

## Security Considerations

### Webhook URL Protection

- Store webhook URLs in configuration files, not command line
- Use environment variables for sensitive data
- Regularly rotate webhook URLs if compromised

### Character Data Privacy

- Character data is stored locally in JSON files
- No data is transmitted except to specified Discord webhooks
- Session cookies are stored in configuration (encrypt if needed)

### Network Security

- All HTTPS connections for API calls
- No external dependencies beyond Python standard library
- Optional PyYAML for configuration parsing

## Troubleshooting

### Debug Mode

Enable comprehensive logging:

```bash
python discord_notifier.py 145081718 --preset debug --verbose --dry-run
```

### Field Path Investigation

Understand what fields are available:

```bash
python discord_notifier.py 145081718 --dry-run --show-field-paths
```

### Test with Baseline Data

Use known character data for testing:

```bash
python test_discord_notifier.py
```

### Common Solutions

1. **No changes detected**: Verify character ID and ensure character has been modified
2. **Too many notifications**: Use more restrictive filtering or increase check interval
3. **Missing changes**: Check if fields are excluded by current filter settings
4. **Webhook failures**: Verify webhook URL and Discord server permissions

## Contributing

### Adding New Data Groups

1. Define group in `DATA_GROUPS` dictionary
2. Add field patterns matching v6.0.0 JSON structure
3. Set appropriate priority level
4. Add to nested or composite groups if applicable
5. Update documentation and tests

### Testing Changes

Always run the test suite after modifications:

```bash
python test_discord_notifier.py
```

### Code Style

- Follow PEP 8 conventions
- Use type hints for all functions
- Add comprehensive docstrings
- Include error handling for external API calls

## v6.0.0 Enhanced Capabilities

### Completed in v6.0.0
- [x] **Modular Architecture**: Clean separation of calculators, clients, and services
- [x] **Rule Version Detection**: Automatic 2014/2024 rule detection with manual override
- [x] **Enhanced Calculators**: Specialized calculators for AC, HP, spells, containers, etc.
- [x] **Container Inventory**: Detailed tracking of items within bags and containers
- [x] **Advanced Spellcasting**: Better multiclass spellcasting and spell slot calculations
- [x] **Configuration Management**: Environment-aware YAML configuration system
- [x] **Improved Error Handling**: Better diagnostics and error reporting
- [x] **Storage Abstraction**: Support for multiple storage backends (JSON, SQLite, PostgreSQL)

### Configuration Examples for v6.0.0

**Basic Configuration:**
```yaml
webhook_url: "https://discord.com/api/webhooks/..."
character_id: "145081718"
filtering:
  preset: "level_up"
```

**Advanced Configuration:**
```yaml
webhook_url: "https://discord.com/api/webhooks/..."
character_id: "145081718"
check_interval: 300  # 5 minutes
format_type: "detailed"

# v6.0.0 specific settings
advanced:
  rule_version: "auto"  # "2014", "2024", or "auto"
  storage_backend: "json"  # "json", "sqlite", "postgres"
  enable_container_tracking: true
  enable_diagnostics: true

filtering:
  preset: "combat_only"
  include_groups:
    - "combat"
    - "spells.slots"
    - "inventory.containers"  # New in v6.0.0
```

## Future Enhancements

- [ ] Multiple character monitoring
- [ ] Custom data group definitions
- [ ] Advanced webhook formatting options
- [ ] Web dashboard interface
- [ ] Slack and Teams integration
- [ ] Change history and analytics
- [ ] Campaign-wide monitoring
- [ ] Real-time character updates via WebSocket

---

*For technical support or feature requests, please check the project documentation or create an issue in the repository.*