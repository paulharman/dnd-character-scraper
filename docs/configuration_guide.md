# Configuration Guide

## Overview

The D&D Beyond Character Scraper uses a multi-file configuration system to organize settings by functionality. This guide will help you understand and customize the configuration for your needs.

## Configuration Files

### Main Configuration (`config/main.yaml`)

The primary configuration file containing project-wide settings:

```yaml
# Project information
project:
  name: "DnD Beyond Character Scraper"
  version: "6.0.0"

# Environment settings
environment: "production"  # development, testing, production
debug: false

# File paths (relative to project root)
paths:
  character_data: "character_data"
  data_folder: "data"
  baseline: "data/baseline"
  spells_folder: "obsidian/spells"
  config_dir: "config"

# Logging
logging:
  level: "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Performance
performance:
  memory_optimization: true
  enable_caching: false
```

### Discord Configuration (`config/discord.yaml`)

Controls Discord notifications and character monitoring:

```yaml
# Required: Discord webhook URL (use environment variable)
webhook_url: ${DISCORD_WEBHOOK_URL}

# Required: Character ID from D&D Beyond URL
character_id: 12345678

# Monitoring settings
check_interval_seconds: 600  # Check every 10 minutes
storage_directory: character_data

# Notification settings
discord:
  min_priority: LOW  # LOW, MEDIUM, HIGH, CRITICAL
  color_code_by_priority: true
  group_related_changes: true
  maximum_changes_per_notification: 200
```

## Quick Start

### 1. Set Up Discord Integration

1. **Create Discord Webhook:**
   - Go to your Discord server
   - Server Settings → Integrations → Webhooks
   - Create New Webhook
   - Copy the webhook URL

2. **Set Environment Variable:**
   ```bash
   # Windows
   set DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url
   
   # Linux/Mac
   export DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/your-webhook-url
   ```

3. **Find Your Character ID:**
   - Go to your D&D Beyond character page
   - Look at the URL: `dndbeyond.com/characters/[YOUR_ID]`
   - Copy the number after `/characters/`

4. **Update Configuration:**
   ```yaml
   # In config/discord.yaml
   character_id: YOUR_CHARACTER_ID_HERE
   ```

### 2. Test the Setup

Run the scraper once to test:
```bash
python discord/discord_monitor.py
```

If successful, you should see a Discord notification with your character's current state.

## Common Configuration Scenarios

### Scenario 1: Monitor Multiple Characters

```yaml
# In config/discord.yaml
character_id: 12345678  # Primary character
party:
  - character_id: '87654321'
  - character_id: '987654321'  # Add party members
  - character_id: '456789123'
```

### Scenario 2: Reduce Notification Volume

```yaml
# In config/discord.yaml
discord:
  min_priority: MEDIUM  # Only medium and high priority changes
  group_related_changes: true  # Group similar changes
  maximum_changes_per_notification: 50  # Smaller messages
```

### Scenario 3: Development/Testing Setup

```yaml
# In config/main.yaml
environment: "development"
debug: true

# In config/discord.yaml
check_interval_seconds: 300  # Check every 5 minutes
discord:
  min_priority: LOW  # See all changes during testing
```

### Scenario 4: Production Deployment

```yaml
# In config/main.yaml
environment: "production"
debug: false

# In config/discord.yaml
check_interval_seconds: 1800  # Check every 30 minutes
discord:
  min_priority: MEDIUM  # Reduce notification volume
  rate_limit:
    requests_per_minute: 2  # Conservative rate limiting
```

## Environment-Specific Overrides

The system supports environment-specific configuration overrides:

```yaml
# In config/main.yaml
environments:
  development:
    debug: true
    logging:
      level: "DEBUG"
  
  production:
    debug: false
    logging:
      level: "INFO"
```

The active environment is controlled by the `environment` setting in main.yaml.

## Change Detection and Priorities

### Priority Levels

- **HIGH (Red)**: Critical changes like level ups, ability score increases
- **MEDIUM (Yellow)**: Important changes like new spells, equipment changes
- **LOW (Blue)**: Minor changes like current HP, personality updates
- **IGNORED**: Metadata and timestamps (no notifications)

### Customizing Priorities

You can customize which fields have which priorities:

```yaml
# In config/discord.yaml
detection:
  field_patterns:
    character.hit_points.current: HIGH  # Make current HP high priority
    character.spells.*: LOW             # Make spell changes low priority
    character.custom_field: MEDIUM      # Set priority for new fields
```

## Performance Tuning

### Reduce API Calls

```yaml
# In config/discord.yaml
check_interval_seconds: 1800  # Check less frequently (30 minutes)

# In config/main.yaml
performance:
  enable_caching: true  # Cache calculation results
```

### Reduce Discord Messages

```yaml
# In config/discord.yaml
discord:
  min_priority: MEDIUM  # Only important changes
  maximum_changes_per_notification: 100  # Larger messages
  delay_between_messages: 5.0  # Longer delays between messages
```

### Optimize Storage

```yaml
# In config/discord.yaml
changelog:
  retention_days: 90  # Keep logs for 90 days instead of 365
  rotation_size_mb: 5  # Rotate files at 5MB instead of 10MB
  enable_compression: true  # Enable when available (future feature)
```

## Troubleshooting

### Common Issues

#### 1. No Discord Notifications

**Check:**
- Environment variable `DISCORD_WEBHOOK_URL` is set correctly
- Discord webhook URL is valid and accessible
- Character ID is correct (from D&D Beyond URL)
- Character has actually changed since last check

**Debug:**
```yaml
# In config/main.yaml
debug: true
logging:
  level: "DEBUG"
```

#### 2. Too Many Notifications

**Solution:**
```yaml
# In config/discord.yaml
discord:
  min_priority: MEDIUM  # Reduce notification volume
  group_related_changes: true  # Group similar changes
```

#### 3. Rate Limiting Errors

**Solution:**
```yaml
# In config/discord.yaml
check_interval_seconds: 1800  # Check less frequently
discord:
  rate_limit:
    requests_per_minute: 2  # Reduce request rate
    maximum_burst_requests: 1  # Reduce burst requests
```

#### 4. Storage Issues

**Check:**
- Storage directory exists and is writable
- Sufficient disk space available
- No permission issues

**Debug:**
```yaml
# In config/discord.yaml
storage_directory: ./character_data  # Use relative path
changelog:
  validate_on_startup: true  # Validate storage on startup
```

### Log Analysis

Enable detailed logging to diagnose issues:

```yaml
# In config/main.yaml
environment: "development"
debug: true
logging:
  level: "DEBUG"
```

Check log files in the storage directory for detailed error information.

## Advanced Configuration

### Custom Field Patterns

Add custom field patterns for new D&D Beyond fields:

```yaml
# In config/discord.yaml
detection:
  auto_add_new_fields: true  # Automatically detect new fields
  default_priority_for_new_fields: MEDIUM
  field_patterns:
    character.new_2024_feature.*: HIGH  # Custom pattern for new features
```

### Causation Analysis

Configure advanced change analysis:

```yaml
# In config/discord.yaml
causation:
  enabled: true
  confidence_threshold: 0.8  # Higher confidence required
  max_cascade_depth: 5  # Deeper analysis
  detect_feat_causation: true
  detect_level_progression: true
  detect_equipment_causation: true
```

### Change Logging

Customize change log storage:

```yaml
# In config/discord.yaml
changelog:
  enabled: true
  detail_level: comprehensive  # Store full details
  discord_detail_level: summary  # But send summaries to Discord
  retention_days: 365
  maintenance:
    enabled: true
    interval_hours: 24
    maximum_rotated_files_per_character: 100
```

## Configuration Validation

The system validates configuration on startup. Common validation errors:

- **Invalid priority levels**: Must be LOW, MEDIUM, HIGH, CRITICAL, or IGNORED
- **Invalid time values**: Must be positive numbers
- **Invalid paths**: Must be valid directory paths
- **Missing required fields**: webhook_url and character_id are required

## Migration and Updates

When updating the scraper, configuration may need migration:

1. **Backup your configuration:**
   ```bash
   cp -r config config_backup
   ```

2. **Run migration tool:**
   ```bash
   python tools/config_migration.py
   ```

3. **Review changes:**
   - Check for renamed configuration keys
   - Verify new features are configured correctly
   - Test with your Discord webhook

## Getting Help

- **Configuration Issues**: Check this guide and the troubleshooting section
- **Feature Requests**: See the project documentation
- **Bug Reports**: Include your configuration (with sensitive data removed)

## Configuration Reference

For a complete reference of all configuration options, see:
- `config/main.yaml` - Comprehensive comments for all main settings
- `config/discord.yaml` - Detailed Discord and monitoring configuration
- `docs/configuration_naming_standards.md` - Naming conventions and standards
- `config_audit_report.json` - Current configuration analysis

## Security Notes

- **Never commit webhook URLs**: Always use environment variables
- **Protect character IDs**: While not secret, avoid sharing unnecessarily
- **Secure storage directory**: Ensure proper file permissions
- **Regular backups**: Backup configuration and character data regularly

---

*This guide covers the most common configuration scenarios. For advanced use cases or custom setups, refer to the detailed comments in the configuration files themselves.*