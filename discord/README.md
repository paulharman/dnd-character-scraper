# Discord Character Monitor

A comprehensive Discord notification system for D&D Beyond character changes. Monitor single or multiple characters and receive real-time notifications in Discord when changes are detected.

## 🔄 Version Compatibility

**Current Version**: v6.0.0 Compatible  
**Breaking Changes**: This version includes breaking changes from pre-v6.0.0 versions.

### Quick Migration Checklist
- [ ] Update `scraper_path` in config: `"enhanced_dnd_scraper.py"` → `"scraper/enhanced_dnd_scraper.py"`
- [ ] Install updated dependencies: `pip install -r requirements.txt`
- [ ] Update script name: `discord_notifier.py` → `discord_monitor.py`
- [ ] Test configuration: `python discord_monitor.py --test`

See [Migration Guide](#migration-from-pre-v60) for detailed instructions.

## 🚀 Features

### Core Functionality
- **Real-time Monitoring**: Automatic character scraping and change detection
- **Smart Filtering**: Configurable data groups and priority levels
- **Rich Notifications**: Beautiful Discord embeds with emojis and color coding
- **Multiple Characters**: Monitor entire campaigns or parties
- **Rate Limiting**: Respects Discord API limits with intelligent backoff

### Notification Types
- **Level Up Alerts**: Special formatting for character level increases
- **Combat Changes**: HP, AC, spell slots, and combat stats
- **Inventory Updates**: Equipment, currency, and item changes
- **Spell Changes**: New spells, spell slot usage, spellcasting updates
- **Ability Score Changes**: Ability increases, modifier changes

### Formatting Options
- **Compact**: Brief summaries for minimal Discord clutter
- **Detailed**: Full information with categorized fields
- **JSON**: Raw data format for debugging and integration

## 📋 Prerequisites

1. **Python 3.8+** with required packages:
   ```bash
   # Install main project dependencies
   pip install -r requirements.txt
   
   # Additional Discord-specific dependencies (if not already installed)
   pip install aiohttp pyyaml
   ```

   **Note**: The v6.0.0 architecture includes all necessary dependencies in the main requirements.txt file.

2. **Discord Webhook**: Create a webhook in your Discord server
   - Go to Server Settings → Integrations → Webhooks
   - Create New Webhook and copy the URL

3. **Character Access**: Public characters work automatically
   - For private characters: D&D Beyond session cookie required

## 🔧 Quick Setup

### 1. Interactive Setup (Recommended)
```bash
python setup_discord_monitor.py
```
This guided setup will create your configuration file.

### 2. Manual Configuration
Copy the example configuration:
```bash
cp discord_config.yml.example discord_config.yml
```

Edit `discord_config.yml` with your settings:
```yaml
# Required
webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"
character_id: "145081718"

# Basic Settings
check_interval: 600  # 10 minutes
format_type: "detailed"
log_level: "INFO"

# Simple Change Types Filtering (Recommended)
filtering:
  change_types:
    - "level"
    - "hit_points"
    - "spells_known"
    # Remove types you don't want to monitor
```

## 🏃 Running the Monitor

### Test Discord Connection
```bash
python discord_monitor.py --test
```

### Start Monitoring
```bash
# Single run
python discord_monitor.py

# With custom config file
python discord_monitor.py --config my_config.yml

# Verbose logging
python discord_monitor.py --verbose
```

### Background Service
```bash
# Linux/Mac with nohup
nohup python discord_monitor.py > monitor.log 2>&1 &

# Windows with pythonw (no console)
pythonw discord_monitor.py
```

## ⚙️ Configuration Options

### Character Monitoring

**Single Character:**
```yaml
character_id: "145081718"
```

**Multiple Characters:**
```yaml
characters:
  - character_id: "145081718"
    nickname: "Elara the Wizard"
  - character_id: "147061783"
    nickname: "Thorin Fighter"
```

### Simple Change Types (Recommended)

The new filtering system uses a simple list of change types. Just remove the types you don't want to monitor:

```yaml
filtering:
  change_types:
    - "level"              # Character level changes
    - "experience"         # Experience point changes
    - "hit_points"         # HP maximum and current changes
    - "armor_class"        # AC modifications
    - "ability_scores"     # Strength, dexterity, etc.
    - "spells_known"       # Spells learned/forgotten
    - "spell_slots"        # Spell slot usage/recovery
    - "inventory_items"    # Items gained/lost
    - "equipment"          # Equipment changes
    - "currency"           # Gold, silver, copper changes
    - "skills"             # Skill proficiencies and bonuses
    - "proficiencies"      # Weapon/armor/tool proficiencies
    - "feats"              # Feats gained/lost
    - "class_features"     # Class features and abilities
    - "appearance"         # Character appearance changes
    - "background"         # Background/backstory changes
    # - "meta"             # Scraper metadata (usually excluded)
```

#### Quick Examples

**Combat Session** (remove everything except combat-relevant):
```yaml
filtering:
  change_types:
    - "hit_points"
    - "armor_class"
    - "spell_slots"
```

**Level Up Tracking** (progression-focused):
```yaml
filtering:
  change_types:
    - "level"
    - "hit_points"
    - "ability_scores"
    - "spells_known"
    - "feats"
    - "class_features"
```

**Shopping Trip** (inventory-focused):
```yaml
filtering:
  change_types:
    - "inventory_items"
    - "equipment" 
    - "currency"
```

### Legacy Filtering (Advanced)

For advanced users, the old preset and group system is still supported:

#### Filtering Presets
```yaml
filtering:
  preset: "level_up"  # Options: combat_only, level_up, roleplay_session, shopping_trip, minimal, debug
```

#### Custom Group Filtering
```yaml
filtering:
  include_groups:
    - "basic"
    - "combat" 
    - "spells"
  exclude_groups:
    - "meta"
    - "appearance"
```

### Notification Customization
```yaml
notifications:
  username: "Campaign Monitor"
  mentions:
    level_up: "@DM"
    high_priority: "@everyone"
  timezone: "America/New_York"
```

### Advanced Settings
```yaml
advanced:
  max_changes_per_notification: 15
  rate_limit:
    requests_per_minute: 3
    burst_limit: 1
  retry:
    max_attempts: 3
    backoff_factor: 2
    max_delay: 60
```

## 🎨 Message Formats

### Compact Format
```
🎲 Elara the Wizard Updated
🔴 2 high priority changes
⬆️ Level increased by 1 (2 → 3)
➕ Spell Slots Level 2 added: 2
🟡 3 medium priority changes
🔄 Hit Points Maximum changed: 16 → 22
... and 2 more changes
```

### Detailed Format
Rich embed with categorized fields:
- **Level & Experience** with progress indicators
- **Combat Stats** with health and AC changes
- **Spells & Magic** with new spells and slot changes
- **Inventory & Equipment** with item additions/removals
- **Abilities & Skills** with score improvements

### JSON Format
Raw structured data for integrations and debugging.

## 🔍 Change Types Reference

Available change types and what they monitor:

| Change Type | Monitors | Examples |
|-------------|----------|----------|
| `level` | Character level increases/decreases | Level 4 → 5 |
| `experience` | Experience point changes | 6500 XP → 7800 XP |
| `hit_points` | HP maximum and current changes | Max HP: 32 → 38 |
| `armor_class` | AC modifications from equipment/spells | AC: 15 → 17 |
| `ability_scores` | STR, DEX, CON, INT, WIS, CHA | Strength: 14 → 16 |
| `spells_known` | Spells learned or forgotten | Learned: Fireball |
| `spell_slots` | Spell slot usage and recovery | Level 1 slots: 2 → 1 |
| `inventory_items` | Items gained, lost, or quantity changes | +1 Potion of Healing |
| `equipment` | Equipped/unequipped items | Equipped: Studded Leather |
| `currency` | Gold, silver, copper changes | GP: 150 → 125 (-25) |
| `skills` | Skill proficiencies and bonuses | +Proficiency: Stealth |
| `proficiencies` | Weapon/armor/tool proficiencies | +Weapon: Longswords |
| `feats` | Feats gained or lost | Gained: Great Weapon Master |
| `class_features` | Class abilities and features | Gained: Action Surge |
| `appearance` | Character avatar and appearance | Avatar updated |
| `background` | Background and backstory changes | Background: Noble → Soldier |
| `meta` | Scraper metadata (usually excluded) | Processed: 2024-01-01 |

### Legacy Data Groups

For advanced users using the legacy group system:

| Group | Change Types Included | Priority |
|-------|---------------------|----------|
| `basic` | level, experience, class_features | High |
| `combat` | hit_points, armor_class | High |
| `abilities` | ability_scores | Medium |
| `spells` | spells_known, spell_slots | Medium |
| `inventory` | inventory_items, equipment, currency | Medium |
| `skills` | skills, proficiencies, feats | Low |
| `appearance` | appearance | Low |
| `backstory` | background | Low |
| `meta` | meta | Low |

## 🚨 Troubleshooting

### Common Issues

**"Discord webhook test failed"**
- Verify webhook URL is correct and active
- Check Discord server permissions
- Ensure webhook wasn't deleted

**"Character not found"**
- Verify character ID is correct
- Check if character is public/private
- Add session cookie for private characters

**"No changes detected"**
- Character may not have updated since last check
- Check filtering settings (may be too restrictive)
- Verify storage directory permissions

**Rate limiting errors**
- Increase `check_interval` between updates
- Reduce `requests_per_minute` in rate limit settings
- Check for multiple monitor instances

**v6.0.0 Migration Issues**
- Update `scraper_path` in configuration file
- Install updated dependencies with `pip install -r requirements.txt`
- Use `discord_monitor.py` instead of `discord_notifier.py`
- Check import paths if using programmatic integration

### Debug Mode
```bash
python discord_monitor.py --verbose
```

Enable debug logging in config:
```yaml
log_level: "DEBUG"
filtering:
  preset: "debug"
```

### Testing Changes
Force a character update by:
1. Making a small change in D&D Beyond
2. Running monitor once: `python discord_monitor.py --test`
3. Checking Discord for notification

## 🔧 Integration

### With v6.0.0 Architecture

**⚠️ BREAKING CHANGE**: The Discord integration has been updated to work with the new v6.0.0 modular architecture.

```python
# Updated imports for v6.0.0
from services.notification_manager import NotificationManager, NotificationConfig
from formatters.discord_formatter import FormatType
from services.change_detection_service import ChangePriority

# Configure notifications
config = NotificationConfig(
    webhook_url="https://discord.com/api/webhooks/...",
    format_type=FormatType.DETAILED
)

# Initialize manager
manager = NotificationManager(config)

# Send notifications for character changes
await manager.check_and_notify_character_changes(character_id)
```

### Migration from Pre-v6.0.0

If you're upgrading from an older version:

1. **Import paths changed**: Discord services now use relative imports within the `discord/` directory
2. **Configuration system**: Now uses the new v6.0.0 config manager with YAML-based configuration
3. **Scraper integration**: Automatically uses the new `EnhancedDnDScraper` class with modular architecture

### Direct Scraper Integration

```python
# Using the v6.0.0 scraper directly
from scraper.enhanced_dnd_scraper import EnhancedDnDScraper
from src.rules.version_manager import RuleVersion

# Create scraper instance
scraper = EnhancedDnDScraper(
    character_id="145081718",
    session_cookie="optional_cookie",
    force_rule_version=RuleVersion.RULES_2024  # Optional
)

# Fetch and process character data
if scraper.fetch_character_data():
    character_data = scraper.get_character_data()
```

### Scheduled Tasks

**Linux Cron:**
```bash
# Check every 10 minutes
*/10 * * * * cd /path/to/scraper && python discord_monitor.py
```

**Windows Task Scheduler:**
- Create Basic Task
- Trigger: Every 10 minutes
- Action: Start program `python`
- Arguments: `discord_monitor.py`
- Start in: Scraper directory

## 📊 Monitoring Multiple Characters

For campaign-wide monitoring:

```yaml
characters:
  - character_id: "145081718"
    nickname: "Elara (Wizard)"
    filtering:
      preset: "level_up"
      
  - character_id: "147061783" 
    nickname: "Thorin (Fighter)"
    filtering:
      include_groups: ["combat", "inventory"]
      
  - character_id: "148392847"
    nickname: "Aria (Rogue)"
    filtering:
      preset: "roleplay_session"

notifications:
  send_summary_for_multiple: true
  mentions:
    level_up: "@DM"
```

This will send:
1. **Summary message** with overview of all changes
2. **Individual notifications** for each character with changes
3. **Appropriate mentions** for significant events

## 🔄 Migration from Pre-v6.0.0

### Breaking Changes Summary

1. **Scraper Path**: Updated to reflect new project structure
2. **Script Names**: `discord_notifier.py` → `discord_monitor.py`  
3. **Import Paths**: Services now use relative imports within `discord/` directory
4. **Configuration**: Enhanced with new v6.0.0 features and rule version support

### Step-by-Step Migration

#### 1. Update Configuration File

Edit your `discord_config.yml`:

```yaml
# OLD
scraper_path: "enhanced_dnd_scraper.py"

# NEW  
scraper_path: "scraper/enhanced_dnd_scraper.py"
```

#### 2. Install Updated Dependencies

```bash
# Install main project dependencies
pip install -r requirements.txt

# Verify Discord dependencies
pip install aiohttp pyyaml
```

#### 3. Update Script Usage

```bash
# OLD
python discord_notifier.py 145081718 --once

# NEW
python discord_monitor.py --test
python discord_monitor.py  # For continuous monitoring
```

#### 4. Test Your Setup

```bash
# Test Discord connection
python discord_monitor.py --test

# Run with verbose logging
python discord_monitor.py --verbose
```

### New v6.0.0 Features Available

- **Rule Version Detection**: Automatic 2014/2024 rule detection
- **Enhanced Calculators**: Improved AC, HP, and spell calculations
- **Container Tracking**: Better inventory management
- **Advanced Configuration**: Environment-aware settings
- **Better Error Handling**: Improved diagnostics and logging

### Optional: Take Advantage of New Features

Add these to your configuration to use v6.0.0 enhancements:

```yaml
# Optional v6.0.0 features
advanced:
  rule_version: "auto"  # "2014", "2024", or "auto"
  enable_container_tracking: true
  enable_diagnostics: true
  
filtering:
  # New container tracking group
  include_groups:
    - "inventory.containers"
```

## 🔐 Security Notes

- **Never commit webhook URLs** to version control
- **Protect session cookies** - they provide account access
- **Use environment variables** for sensitive configuration:
  ```bash
  export DISCORD_WEBHOOK_URL="https://discord.com/api/webhooks/..."
  export DDB_SESSION_COOKIE="your-session-cookie"
  ```

## 📈 Performance

- **Memory usage**: ~50-100MB for typical monitoring
- **Network usage**: Minimal (character API calls + Discord webhooks)
- **CPU usage**: Low (periodic checks only)
- **Storage**: JSON files grow ~1KB per character update

## 🤝 Contributing

The Discord notification system is part of the larger D&D Character Scraper project. See the main README for contribution guidelines.

## 📄 License

MIT License - see LICENSE file for details.

---

*Happy adventuring! 🎲*