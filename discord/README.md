# Discord Module

The discord module provides intelligent change detection and rich notification system for D&D Beyond character updates with comprehensive filtering and analysis capabilities.

## 🏗️ Architecture

```
discord/
├── discord_monitor.py         # Main monitoring script
├── core/                      # Core Discord components
│   ├── models/               # Discord-specific data models
│   ├── services/             # Change detection & notification services
│   └── storage/              # Data persistence & archiving
├── formatters/               # Discord message formatting
└── services/                 # Additional Discord services
    ├── change_analyzers/     # Change analysis & prioritization
    ├── change_detection/     # Change detection logic
    └── various services...   # Configuration, logging, webhooks
```

## ⚡ Key Features

- **🔍 Intelligent Change Detection**: Sophisticated analysis of character changes
- **🎯 Smart Filtering**: Configurable change type filtering and priority levels
- **📊 Rich Notifications**: Detailed Discord embeds with change summaries
- **🧠 Causation Analysis**: Understanding why changes occurred
- **📈 Change Attribution**: Tracks the source and impact of changes
- **🔒 Secure Configuration**: Environment variable webhook URL support
- **📋 Change Logging**: Persistent change history with retention policies
- **⚡ Auto-Triggering**: Automatically called by parser after character updates

## 🚀 Usage

### Automatic Integration (Recommended)
The parser automatically triggers Discord monitoring:
```bash
# This automatically includes Discord notifications
python parser/dnd_json_to_markdown.py CHARACTER_ID
```

### Direct Monitoring
```bash
# Monitor specific character
python discord/discord_monitor.py --character-id CHARACTER_ID

# Validate configuration
python discord/discord_monitor.py --validate-config

# Test webhook connectivity
python discord/discord_monitor.py --validate-webhook

# Security audit
python discord/discord_monitor.py --security-audit
```

### Programmatic Usage
```python
from discord.core.services.enhanced_change_detection_service import EnhancedChangeDetectionService

# Create service
service = EnhancedChangeDetectionService(config)

# Detect changes
changes = service.detect_changes(old_data, new_data)

# Send notification
if changes:
    notification_manager.send_notification(changes)
```

## 🔧 Configuration

Configured via `config/discord.yaml`:

### Core Settings
```yaml
# Secure webhook URL (use environment variable)
webhook_url: "${DISCORD_WEBHOOK_URL}"
character_id: YOUR_CHARACTER_ID
enabled: true
```

### Notification Filtering
```yaml
# Filter by change type
change_types:
  - "level"                    # Character level changes
  - "hit_points"              # HP/health changes
  - "armor_class"             # AC changes
  - "ability_scores"          # Ability score changes
  - "spells_known"            # New spells learned
  - "spell_slots"             # Spell slot changes
  # Remove any you don't want notifications for

# Filter by priority
min_priority: "LOW"            # Options: LOW, MEDIUM, HIGH, CRITICAL
```

### Data Management
```yaml
changelog:
  retention_days: 365          # How long to keep change logs
  enable_compression: false    # Future feature for storage optimization
  cleanup_empty_directories: true
```

## 📊 Change Detection System

### Enhanced Change Detectors
Specialized detectors for different character aspects:
- **Ability Score Detector**: STR, DEX, CON, INT, WIS, CHA changes
- **Combat Stats Detector**: HP, AC, speed, attack bonus changes
- **Spellcasting Detector**: Spell lists, save DC, spell slot changes
- **Equipment Detector**: Inventory, magical items, encumbrance
- **Level & Experience Detector**: Character progression tracking
- **Features Detector**: Class features, racial traits, feats

### Change Analysis
Each change includes:
- **Type Classification**: What kind of change occurred
- **Priority Level**: Importance assessment (LOW/MEDIUM/HIGH/CRITICAL)
- **Causation Analysis**: Why the change happened
- **Impact Assessment**: How significant the change is
- **Source Attribution**: What caused the change (level up, equipment, etc.)

### Smart Filtering
- **Noise Reduction**: Filters out insignificant changes
- **Batch Processing**: Groups related changes together
- **Priority Thresholds**: Only notify on changes above configured priority
- **Type Filtering**: Only monitor specified change types

## 🎨 Discord Notifications

### Rich Embeds
Notifications include:
- **Character Overview**: Name, level, class with thumbnail
- **Change Summary**: High-level description of what changed
- **Detailed Changes**: Specific before/after values
- **Causation Info**: Why changes occurred
- **Timestamp**: When changes were detected
- **Color Coding**: Priority-based embed colors

### Notification Formats
```yaml
format_type: "detailed"        # Options: compact, detailed, json
max_changes_per_notification: 200
timezone: "UTC"
```

### Example Notification
```
🎲 Sample Character Updated
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Level Progress
├─ Experience: 1,750 → 2,100 XP (+350)
└─ Next Level: 850 XP remaining

⚔️ Combat Changes  
├─ Hit Points: 22/22 → 25/25 (+3 max HP)
└─ Spell Save DC: 13 → 14 (+1)

🔮 Spellcasting Updates
└─ New Spell Known: Misty Step (2nd level)

Detected: 2025-08-31 13:45:30 UTC
```

## 🔒 Security Features

### Secure Configuration
- **Environment Variables**: `${DISCORD_WEBHOOK_URL}` pattern support
- **Configuration Validation**: Built-in security validation
- **Webhook Protection**: Automatic detection of hardcoded webhooks
- **Audit Tools**: Regular security scanning

### Privacy Protection
- **Local Processing**: All analysis done locally
- **No Sensitive Data**: Only public character information sent
- **Configurable Data**: Control what information is included

## 📋 Change Logging

### Persistent History
- **Change Logs**: `character_data/change_logs/`
- **Retention Policy**: Configurable retention (default: 365 days)
- **Structured Data**: JSON format for analysis and querying
- **Compression Ready**: Planned compression feature for storage optimization

### Log Format
```json
{
  "character_id": "123456789",
  "timestamp": "2025-08-31T13:45:30.123Z",
  "changes": [
    {
      "field": "hit_points.maximum",
      "old_value": 22,
      "new_value": 25,
      "change_type": "hit_points",
      "priority": "MEDIUM",
      "causation": "level_up"
    }
  ]
}
```

## 🔌 Integration Points

### Parser Integration
- **Auto-Triggering**: Called automatically after parsing
- **Data Handoff**: Receives processed character data
- **Error Handling**: Graceful failure doesn't break parser workflow

### Scraper Integration  
- **Data Source**: Uses scraper output for change comparison
- **Timestamp Tracking**: Monitors data freshness
- **Historical Comparison**: Compares against previous scrapes

### Storage Integration
- **Multiple Backends**: File, SQLite, PostgreSQL support
- **Archiving**: Automatic data archiving and cleanup
- **Caching**: Performance optimization for frequent access

## 🛠️ Development Tools

### Validation Tools
```bash
# Configuration validation
python discord/discord_monitor.py --validate-config

# Webhook testing
python discord/discord_monitor.py --validate-webhook

# Security audit
python scripts/security_audit.py
```

### Debugging
```bash
# Debug mode with detailed output
python discord/discord_monitor.py --character-id CHARACTER_ID --verbose

# Test specific features
python discord/discord_monitor.py --test-change-detection
```

## ⚠️ Important Notes

- **Rate Limiting**: Respects Discord webhook rate limits
- **Environment Variables**: Always use `${DISCORD_WEBHOOK_URL}` pattern for security
- **Change Sensitivity**: Fine-tune filtering to avoid notification spam
- **Storage Management**: Monitor change log storage with retention policies
- **Integration Dependent**: Requires scraper data to function

## 🔧 Troubleshooting

### Common Issues
- **No Notifications**: Check webhook URL and configuration validation
- **Too Many Notifications**: Adjust `change_types` and `min_priority` filtering  
- **Missing Changes**: Verify change detection sensitivity settings
- **Storage Growth**: Enable retention policies and consider compression feature

### Debug Commands
```bash
# Full configuration check
python discord/discord_monitor.py --validate-config

# Test webhook without sending notifications
python discord/discord_monitor.py --validate-webhook

# Security audit
python scripts/security_audit.py
```

## 📈 Future Enhancements

- **Compression**: Automatic compression of old change logs (planned)
- **Analytics Dashboard**: Web interface for change analysis
- **Multi-Character**: Support for monitoring multiple characters
- **Advanced Filtering**: More sophisticated change filtering rules