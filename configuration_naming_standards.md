# Configuration Naming Standards

## Overview

This document establishes consistent naming conventions for all configuration files in the D&D Beyond Character Scraper project. Following these standards ensures maintainability, predictability, and ease of use.

## Core Principles

1. **Consistency**: All configuration keys follow the same patterns
2. **Clarity**: Names clearly indicate their purpose and scope
3. **Hierarchy**: Nested structures reflect logical relationships
4. **Predictability**: Similar concepts use similar naming patterns

## Naming Conventions

### 1. Key Format
**Standard**: Use `snake_case` for all configuration keys

```yaml
# ✅ Correct
character_data: "character_data"
max_changes_per_notification: 200
enable_caching: false

# ❌ Incorrect
characterData: "character_data"
maxChangesPerNotification: 200
enableCaching: false
```

### 2. Boolean Flags
**Standard**: Use `enable_*` prefix for feature toggles

```yaml
# ✅ Correct
enable_caching: true
enable_compression: false
enable_validation: true

# ❌ Incorrect
caching: true
compression: false
validation_enabled: true
```

### 3. Time Values
**Standard**: Include time unit suffix (`_seconds`, `_minutes`, `_hours`, `_days`)

```yaml
# ✅ Correct
timeout_seconds: 30
check_interval_seconds: 600
retention_days: 365

# ❌ Incorrect
timeout: 30
check_interval: 600
retention: 365
```

### 4. Directory Paths
**Standard**: Use `*_directory` suffix for directory paths

```yaml
# ✅ Correct
storage_directory: "character_data/change_logs"
backup_directory: "backups"

# ❌ Incorrect
storage_dir: "character_data/change_logs"
backup_path: "backups"
```

### 5. Limits and Thresholds
**Standard**: Use `maximum_*` and `minimum_*` prefixes for limits

```yaml
# ✅ Correct
maximum_changes_per_notification: 200
minimum_priority: LOW
maximum_file_size_mb: 10

# ❌ Incorrect
max_changes_per_notification: 200
min_priority: LOW
max_file_size_mb: 10
```

## Current Configuration Analysis

Based on audit of existing configuration files, here are the naming inconsistencies found:

### Inconsistencies to Address

1. **Mixed limit prefixes**: `max_changes_per_notification` vs `maximum_*` standard
2. **Directory naming**: `storage_dir` vs `storage_directory` standard  
3. **Time units**: `check_interval` vs `check_interval_seconds` standard
4. **Boolean prefixes**: Some booleans don't use `enable_*` prefix

### Priority for Standardization

**High Priority** (user-facing, frequently used):
- `max_changes_per_notification` → `maximum_changes_per_notification`
- `min_priority` → `minimum_priority`
- `storage_dir` → `storage_directory`

**Medium Priority** (less frequently changed):
- `check_interval` → `check_interval_seconds`
- `timeout` → `timeout_seconds`
- `retry_delay` → `retry_delay_seconds`

**Low Priority** (internal/stable):
- Boolean flags that don't follow `enable_*` pattern but are well-established

## Implementation Strategy

### Phase 1: Document Standards ✅
- Create comprehensive naming standards document
- Identify all current inconsistencies
- Prioritize changes by user impact

### Phase 2: Gradual Migration (Future)
- Support both old and new names with deprecation warnings
- Update documentation to show new names
- Provide migration tools

### Phase 3: Cleanup (Future)
- Remove old names after deprecation period
- Update all examples and templates
- Validate all configurations follow standards

## Validation Rules

Configuration should follow these patterns:
- All keys use `snake_case`
- Boolean feature flags use `enable_*` prefix
- Time values include unit suffixes
- Directory paths use `*_directory` suffix
- Limits use `maximum_*`/`minimum_*` prefixes
- URLs use `*_url` suffix

## Conclusion

These naming standards will improve:
- **Consistency** across all configuration files
- **Predictability** for users and developers  
- **Maintainability** for long-term project health
- **Clarity** in configuration purpose and scope

The current configuration is already quite good (79.8% of items follow good patterns), with only targeted improvements needed for full standardization.