# Discord Configuration Guide

## Overview

The Discord configuration has been enhanced to support comprehensive change tracking, change logging, and causation analysis. This guide covers the new configuration options and how to migrate from legacy configurations.

## Configuration Structure

### Basic Discord Settings (Unchanged)

```yaml
# Required: Discord webhook URL
webhook_url: "${DISCORD_WEBHOOK_URL}"

# Required: Character ID to monitor
character_id: 12345678

# Run mode and timing
run_continuous: false
check_interval: 600  # 10 minutes

# Storage and logging
storage_dir: "../character_data"
log_level: "INFO"

# Notification customization
notifications:
  username: "D&D Beyond Monitor"
  avatar_url: null
  timezone: "UTC"

# Advanced settings
advanced:
  max_changes_per_notification: 200
  delay_between_messages: 2.0
  rate_limit:
    requests_per_minute: 3
    burst_limit: 1
```

### Enhanced Change Tracking Configuration

```yaml
enhanced_change_tracking:
  # Global settings
  enabled: true                    # Enable enhanced change tracking
  detect_minor_changes: false     # Detect minor cosmetic changes
  detect_metadata_changes: false  # Detect metadata-only changes
  detect_cosmetic_changes: false  # Detect appearance/avatar changes
  
  # Individual change type configurations
  change_type_config:
    feats:
      enabled: true               # Enable feat change detection
      priority: "HIGH"            # Priority level (LOW, MEDIUM, HIGH)
      discord_enabled: true       # Send Discord notifications for this type
      causation_analysis: true    # Analyze causation for this type
    
    subclass:
      enabled: true
      priority: "HIGH"
      discord_enabled: true
      causation_analysis: true
    
    spells:
      enabled: true
      priority: "MEDIUM"
      discord_enabled: true
      causation_analysis: true
    
    inventory:
      enabled: true
      priority: "MEDIUM"
      discord_enabled: true
      causation_analysis: true
    
    # ... additional change types
```

### Change Log Configuration

```yaml
change_log:
  # Basic settings
  enabled: true                           # Enable change logging
  storage_dir: "character_data/change_logs"  # Directory for change logs
  retention_days: 365                     # Keep logs for 1 year
  rotation_size_mb: 10                    # Rotate when file exceeds this size
  backup_old_logs: true                   # Archive old logs instead of deleting
  
  # Detail levels
  detail_level: "comprehensive"           # Log detail level
  discord_detail_level: "summary"        # Discord notification detail level
  
  # Performance settings
  max_entries_per_batch: 100              # Maximum entries to process at once
  enable_compression: false               # Compress log files (future feature)
  
  # Feature toggles
  enable_causation_analysis: true         # Analyze what caused changes
  enable_detailed_descriptions: true      # Generate comprehensive descriptions
  
  # Notification integration
  notify_on_causation_detected: true      # Send Discord notification when causation is found
  include_attribution_in_discord: true    # Include attribution in Discord messages
  
  # Priority filtering
  min_priority_for_logging: "LOW"         # Log all changes
  min_priority_for_discord: "MEDIUM"     # Only notify on medium+ priority changes
```

### Causation Analysis Configuration

```yaml
causation_analysis:
  enabled: true                           # Enable causation analysis
  confidence_threshold: 0.7               # Minimum confidence for causation (0.0-1.0)
  max_cascade_depth: 3                    # Maximum depth for cascade detection
  
  # Analysis features
  detect_feat_causation: true             # Detect changes caused by feats
  detect_level_progression: true          # Detect changes from level progression
  detect_equipment_causation: true        # Detect changes from equipment
  detect_ability_score_cascades: true     # Detect cascading ability score effects
  
  # Performance settings
  analysis_timeout_seconds: 30            # Timeout for causation analysis
  cache_analysis_results: true            # Cache analysis results for performance
```

### Enhanced Notifications Configuration

```yaml
enhanced_notifications:
  # Detail levels for different outputs
  detail_level: "summary"                 # brief, summary, detailed, comprehensive
  include_attribution: true               # Include what caused the change
  include_causation: true                 # Include causation analysis
  
  # Priority filtering
  min_priority: "LOW"                     # Minimum priority to notify (LOW, MEDIUM, HIGH)
  
  # Notification behavior
  group_related_changes: true             # Group related changes together
  show_change_summaries: true             # Show summaries for multiple changes
  include_timestamps: true                # Include timestamps in notifications
  
  # Formatting options
  use_embeds: true                        # Use Discord embeds for rich formatting
  color_code_by_priority: true            # Color code messages by priority
  include_character_context: true         # Include character name and level context
```

## Change Types

### Legacy Change Types (Preserved)

- `level` - Character level changes
- `experience` - Experience point changes
- `hit_points` - HP/health changes
- `armor_class` - AC changes
- `ability_scores` - Strength, Dex, Con, Int, Wis, Cha changes
- `spells_known` - New spells learned
- `spell_slots` - Spell slot changes
- `inventory_items` - Items added/removed from inventory
- `equipment` - Equipment changes
- `currency` - Gold/currency changes
- `skills` - Skill proficiency changes
- `proficiencies` - Other proficiency changes
- `feats` - Feat changes
- `class_features` - Class feature changes
- `appearance` - Appearance/avatar changes
- `background` - Background changes

### Enhanced Change Types (New)

- `subclass` - Subclass changes
- `spells` - Comprehensive spell changes (added/removed/modified)
- `inventory` - Comprehensive inventory changes
- `max_hp` - Maximum hit points changes
- `race_species` - Race or species changes
- `multiclass` - Multiclass progression
- `personality` - Personality traits, ideals, bonds, flaws
- `spellcasting_stats` - Spell attack bonus, spell save DC
- `initiative` - Initiative bonus changes
- `passive_skills` - Passive perception and other passive skills
- `alignment` - Character alignment changes
- `size` - Character size category changes
- `movement_speed` - Movement speed changes

## Priority Levels

### HIGH Priority
- Character progression changes (level, feats, subclass, multiclass)
- Major character changes (race/species, background, ability scores)

### MEDIUM Priority
- Combat-related changes (spells, max HP, spellcasting stats, initiative)
- Equipment and inventory changes
- Proficiency changes
- Alignment and size changes

### LOW Priority
- Cosmetic changes (personality, passive skills, movement speed)
- Minor metadata changes
- Appearance changes

## Configuration Examples

### Example 1: High-Priority Changes Only

```yaml
enhanced_notifications:
  min_priority: "HIGH"
  detail_level: "brief"
  group_related_changes: false

enhanced_change_tracking:
  change_type_config:
    feats:
      enabled: true
      priority: "HIGH"
      discord_enabled: true
    multiclass:
      enabled: true
      priority: "HIGH"
      discord_enabled: true
    # Disable lower priority types
    inventory:
      enabled: false
    personality:
      enabled: false
```

### Example 2: Comprehensive Logging with Minimal Discord

```yaml
change_log:
  detail_level: "comprehensive"
  discord_detail_level: "brief"
  enable_causation_analysis: true
  min_priority_for_discord: "HIGH"

enhanced_notifications:
  min_priority: "HIGH"
  detail_level: "brief"
```

### Example 3: Character Progression Focus

```yaml
enhanced_change_tracking:
  change_type_config:
    feats:
      enabled: true
      priority: "HIGH"
      discord_enabled: true
    multiclass:
      enabled: true
      priority: "HIGH"
      discord_enabled: true
    ability_scores:
      enabled: true
      priority: "HIGH"
      discord_enabled: true
    subclass:
      enabled: true
      priority: "HIGH"
      discord_enabled: true
    # Disable non-progression changes
    personality:
      enabled: false
    passive_skills:
      enabled: false
    movement_speed:
      enabled: false
    inventory:
      enabled: false
```

### Example 4: Performance-Optimized Settings

```yaml
change_log:
  max_entries_per_batch: 50
  rotation_size_mb: 5
  maintenance:
    maintenance_interval_hours: 12
    max_rotated_files_per_character: 25

causation_analysis:
  analysis_timeout_seconds: 15
  cache_analysis_results: true

advanced:
  max_changes_per_notification: 50
```

## Migration Guide

### From Legacy Configuration

1. **Existing configurations continue to work** without changes
2. **To enable enhanced features**, add the new configuration sections
3. **Legacy change types** in `filtering.change_types` are preserved
4. **New change types** are additive to existing types

### Migration Steps

1. **Backup your current configuration**:
   ```bash
   cp config/discord.yaml config/discord.yaml.backup
   ```

2. **Add enhanced sections** to your existing configuration:
   ```yaml
   # Add to existing discord.yaml
   enhanced_change_tracking:
     enabled: true
     # ... configuration options
   
   change_log:
     enabled: true
     # ... configuration options
   ```

3. **Update change types list** to include new types:
   ```yaml
   filtering:
     change_types:
       # Existing types...
       - "level"
       - "feats"
       # New enhanced types...
       - "subclass"
       - "spells"
       - "max_hp"
   ```

4. **Test the configuration**:
   ```bash
   python discord/discord_monitor.py --config config/discord.yaml --dry-run
   ```

### Automatic Migration

The system supports automatic migration of legacy configurations:

- **Configuration version tracking** prevents repeated migrations
- **Backup creation** preserves original configurations
- **Graceful fallbacks** handle missing or invalid settings
- **Validation** ensures migrated configurations are valid

## Troubleshooting

### Common Issues

1. **Notifications stopped working**:
   - Check `enhanced_change_tracking.enabled` is `true`
   - Verify change types are enabled in `change_type_config`
   - Check `min_priority` settings aren't filtering out changes

2. **Missing change types**:
   - Verify change type is in `filtering.change_types` list
   - Check change type is enabled in `enhanced_change_tracking.change_type_config`
   - Ensure `discord_enabled` is `true` for the change type

3. **Performance issues**:
   - Reduce `causation_analysis.analysis_timeout_seconds`
   - Increase `change_log.max_entries_per_batch`
   - Enable `causation_analysis.cache_analysis_results`

4. **Storage issues**:
   - Check `change_log.storage_dir` permissions
   - Verify disk space for log files
   - Check `change_log.rotation_size_mb` settings

5. **Too many notifications**:
   - Increase `enhanced_notifications.min_priority`
   - Disable specific change types with `discord_enabled: false`
   - Reduce `advanced.max_changes_per_notification`

### Validation

The configuration system includes comprehensive validation:

```bash
# Validate configuration
python -c "
from src.services.enhanced_config_service import EnhancedConfigService
config_service = EnhancedConfigService('config/discord.yaml')
config = config_service.load_config()
errors = config.validate()
if errors:
    print('Configuration errors:', errors)
else:
    print('Configuration is valid')
"
```

## Best Practices

### Configuration Management

1. **Use version control** for configuration files
2. **Test changes** in a development environment first
3. **Monitor logs** after configuration changes
4. **Use appropriate detail levels** for different outputs
5. **Set reasonable retention policies** for change logs

### Performance Optimization

1. **Disable unused change types** to reduce processing
2. **Set appropriate timeouts** for causation analysis
3. **Use caching** for analysis results
4. **Configure log rotation** to prevent large files
5. **Monitor system resources** during operation

### Security Considerations

1. **Protect webhook URLs** using environment variables
2. **Secure log storage directories** with appropriate permissions
3. **Regularly rotate** webhook URLs if compromised
4. **Monitor access** to configuration files
5. **Use HTTPS** for all webhook communications

## Advanced Configuration

### Custom Change Type Priorities

```yaml
enhanced_change_tracking:
  change_type_config:
    custom_change_type:
      enabled: true
      priority: "MEDIUM"
      discord_enabled: true
      causation_analysis: true
```

### Conditional Notifications

```yaml
enhanced_notifications:
  min_priority: "MEDIUM"
  group_related_changes: true
  
# Only notify on causation detection
change_log:
  notify_on_causation_detected: true
  min_priority_for_discord: "HIGH"
```

### Maintenance Scheduling

```yaml
change_log:
  maintenance:
    enable_scheduled_maintenance: true
    maintenance_interval_hours: 24
    enable_health_monitoring: true
    health_check_interval_minutes: 60
```

This enhanced Discord configuration provides comprehensive control over change tracking, logging, and notifications while maintaining backward compatibility with existing setups.