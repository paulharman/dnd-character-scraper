# Discord Notifier Data Group System Design

## Overview

This document defines a comprehensive data group system for the Discord notifier to support `--include` and `--exclude` options for selective change tracking. The system is based on analysis of the v6.0.0 JSON output structure and designed for real gameplay scenarios.

## Data Group Definitions

### 1. Core Groups (Top-Level)

#### `basic`
**Purpose**: Essential character identity and progression data
**Use Case**: Track fundamental character changes like leveling up, class changes, or name updates

**JSON Fields**:
```json
{
  "basic_info.name": "Character name",
  "basic_info.level": "Character level", 
  "basic_info.experience": "Experience points",
  "basic_info.inspiration": "Inspiration status",
  "basic_info.classes": "Class levels and subclasses",
  "meta.character_id": "Character ID",
  "meta.is_2024_rules": "Rule set version",
  "meta.proficiency_bonus": "Proficiency bonus"
}
```

#### `stats`
**Purpose**: Core ability scores, saves, and skills
**Use Case**: Track ability score improvements, skill proficiency changes, saving throw modifiers

**JSON Fields**:
```json
{
  "ability_scores.*": "All ability scores with modifiers and source breakdowns",
  "skills.*": "All skill values",
  "saving_throws.*": "All saving throw values",
  "proficiencies.*": "All proficiency arrays",
  "proficiency_sources.*": "Proficiency source mappings"
}
```

#### `combat`
**Purpose**: Combat-relevant statistics
**Use Case**: Track AC changes, hit point modifications, initiative bonuses, speed changes

**JSON Fields**:
```json
{
  "basic_info.armor_class": "AC calculation and modifiers",
  "basic_info.hit_points": "HP current, max, temporary, bonuses",
  "basic_info.initiative": "Initiative total and sources",
  "basic_info.speed": "All movement speeds",
  "meta.passive_senses": "Passive perception, investigation, insight"
}
```

#### `spells`
**Purpose**: All spellcasting related data
**Use Case**: Track spell learning, preparation changes, slot modifications, spellcasting ability changes

**JSON Fields**:
```json
{
  "spells.*": "All spell data by source",
  "spell_slots.*": "Spell slot information",
  "meta.primary_spellcasting_ability": "Primary casting ability",
  "meta.total_caster_level": "Total caster level"
}
```

#### `inventory`
**Purpose**: Equipment, money, and carrying capacity
**Use Case**: Track equipment changes, wealth modifications, encumbrance

**JSON Fields**:
```json
{
  "inventory.*": "All equipment with metadata",
  "meta.total_wealth_gp": "Total wealth in gold",
  "meta.individual_currencies": "Currency breakdown",
  "meta.carrying_capacity": "Carrying capacity"
}
```

#### `features`
**Purpose**: Class features, racial traits, feats, and actions
**Use Case**: Track feature acquisition, feat selection, trait modifications

**JSON Fields**:
```json
{
  "species.traits": "Racial/species traits",
  "feats.*": "All feats and descriptions",
  "actions.*": "Class features and actions",
  "background.description": "Background mechanical elements"
}
```

#### `appearance`
**Purpose**: Physical description and avatar
**Use Case**: Track cosmetic changes, avatar updates

**JSON Fields**:
```json
{
  "appearance.*": "All physical characteristics",
  "basic_info.avatarUrl": "Character avatar URL"
}
```

#### `background`
**Purpose**: Backstory, personality, and relationships
**Use Case**: Track character development, story elements

**JSON Fields**:
```json
{
  "background.personal_possessions": "Personal possessions",
  "background.other_holdings": "Other holdings",
  "background.organizations": "Organizations",
  "background.enemies": "Enemies",
  "background.ideals": "Ideals",
  "background.bonds": "Bonds", 
  "background.flaws": "Flaws",
  "background.personality_traits": "Personality traits",
  "notes.*": "All character notes"
}
```

#### `meta`
**Purpose**: System metadata and diagnostics
**Use Case**: Track processing information, warnings, errors

**JSON Fields**:
```json
{
  "meta.processed_timestamp": "Processing timestamp",
  "meta.scraper_version": "Scraper version",
  "meta.diagnostics": "All diagnostic information",
  "basic_info.lifestyleId": "Lifestyle information"
}
```

### 2. Nested Groups (Granular Control)

#### `stats.abilities`
**JSON Fields**: `ability_scores.*`

#### `stats.skills`
**JSON Fields**: `skills.*`

#### `stats.saves`
**JSON Fields**: `saving_throws.*`

#### `stats.proficiencies`
**JSON Fields**: `proficiencies.*`, `proficiency_sources.*`

#### `combat.ac`
**JSON Fields**: `basic_info.armor_class`

#### `combat.hp`
**JSON Fields**: `basic_info.hit_points`

#### `combat.initiative`
**JSON Fields**: `basic_info.initiative`

#### `combat.speed`
**JSON Fields**: `basic_info.speed`

#### `spells.known`
**JSON Fields**: `spells.*` (spell lists)

#### `spells.slots`
**JSON Fields**: `spell_slots.*`

#### `inventory.equipment`
**JSON Fields**: `inventory.*`

#### `inventory.wealth`
**JSON Fields**: `meta.total_wealth_gp`, `meta.individual_currencies`

#### `features.racial`
**JSON Fields**: `species.traits`

#### `features.feats`
**JSON Fields**: `feats.*`

#### `features.actions`
**JSON Fields**: `actions.*`

### 3. Composite Groups (Convenience)

#### `progression`
**Purpose**: All character advancement related changes
**Includes**: `basic`, `stats.abilities`, `features.feats`, `spells.known`, `spells.slots`

#### `mechanics`
**Purpose**: All mechanical game elements (excludes flavor)
**Includes**: `basic`, `stats`, `combat`, `spells`, `features`

#### `roleplay`
**Purpose**: All roleplay and character development elements
**Includes**: `appearance`, `background`

#### `resources`
**Purpose**: All expendable resources
**Includes**: `combat.hp`, `spells.slots`, `inventory.wealth`

## CLI Interface Design

### Basic Usage

```bash
# Include only specific groups
python discord_notifier.py --include combat,spells

# Exclude specific groups  
python discord_notifier.py --exclude appearance,background

# Nested group control
python discord_notifier.py --include combat.hp,spells.slots

# Composite groups
python discord_notifier.py --include progression

# Multiple specifications (include takes precedence)
python discord_notifier.py --include combat --exclude combat.speed
```

### Configuration File Support

```yaml
# discord_config.yml
notification_groups:
  default_include: ["mechanics"]  # Default: all groups
  default_exclude: ["meta"]
  
  # Custom group definitions
  custom_groups:
    essential: ["basic", "combat.hp", "spells.slots"]
    story: ["background", "appearance"]
```

### Advanced Filtering

```bash
# Use custom groups
python discord_notifier.py --include essential

# Environment-specific presets
python discord_notifier.py --preset combat_only
python discord_notifier.py --preset story_tracking
```

## Implementation Strategy

### 1. Data Structure

```python
# data_groups.py
DATA_GROUPS = {
    "basic": {
        "fields": [
            "basic_info.name",
            "basic_info.level", 
            "basic_info.experience",
            "basic_info.inspiration",
            "basic_info.classes",
            "meta.character_id",
            "meta.is_2024_rules",
            "meta.proficiency_bonus"
        ],
        "description": "Essential character identity and progression data"
    },
    "stats": {
        "fields": [
            "ability_scores.*",
            "skills.*", 
            "saving_throws.*",
            "proficiencies.*",
            "proficiency_sources.*"
        ],
        "description": "Core ability scores, saves, and skills",
        "subgroups": ["abilities", "skills", "saves", "proficiencies"]
    },
    # ... rest of groups
}

NESTED_GROUPS = {
    "stats.abilities": ["ability_scores.*"],
    "stats.skills": ["skills.*"],
    "stats.saves": ["saving_throws.*"],
    "stats.proficiencies": ["proficiencies.*", "proficiency_sources.*"],
    # ... rest of nested groups
}

COMPOSITE_GROUPS = {
    "progression": ["basic", "stats.abilities", "features.feats", "spells.known", "spells.slots"],
    "mechanics": ["basic", "stats", "combat", "spells", "features"],
    "roleplay": ["appearance", "background"],
    "resources": ["combat.hp", "spells.slots", "inventory.wealth"]
}
```

### 2. Change Detection Logic

```python
# change_detector.py
class ChangeDetector:
    def __init__(self, include_groups=None, exclude_groups=None):
        self.include_groups = self._resolve_groups(include_groups or ["*"])
        self.exclude_groups = self._resolve_groups(exclude_groups or [])
        
    def _resolve_groups(self, group_list):
        """Resolve group names to actual JSON field patterns"""
        resolved_fields = set()
        for group in group_list:
            if group == "*":
                resolved_fields.update(self._get_all_fields())
            elif group in COMPOSITE_GROUPS:
                for subgroup in COMPOSITE_GROUPS[group]:
                    resolved_fields.update(self._resolve_single_group(subgroup))
            else:
                resolved_fields.update(self._resolve_single_group(group))
        return resolved_fields
    
    def should_track_field(self, field_path):
        """Determine if a field should be tracked based on include/exclude rules"""
        if self.exclude_groups and self._field_matches_patterns(field_path, self.exclude_groups):
            return False
        if self.include_groups and not self._field_matches_patterns(field_path, self.include_groups):
            return False
        return True
    
    def filter_changes(self, changes):
        """Filter detected changes based on group settings"""
        return [change for change in changes if self.should_track_field(change.field_path)]
```

### 3. Field Path Matching

```python
# field_matcher.py
import fnmatch

def field_matches_pattern(field_path, pattern):
    """Check if a field path matches a pattern (supports wildcards)"""
    # Handle nested object notation
    if ".*" in pattern:
        base_pattern = pattern.replace(".*", "")
        return field_path.startswith(base_pattern + ".")
    
    # Handle exact matches
    return fnmatch.fnmatch(field_path, pattern)

def expand_field_pattern(pattern, json_data):
    """Expand wildcard patterns to actual field paths"""
    if ".*" not in pattern and "*" not in pattern:
        return [pattern]
    
    matching_fields = []
    for field_path in get_all_field_paths(json_data):
        if field_matches_pattern(field_path, pattern):
            matching_fields.append(field_path)
    
    return matching_fields
```

## Usage Examples

### Scenario 1: Combat Session Tracking
```bash
# Only track combat-relevant changes during a battle
python discord_notifier.py --include combat,spells.slots
```

**Tracks**: AC changes, HP modifications, initiative bonuses, spell slot usage
**Ignores**: Inventory changes, backstory updates, appearance modifications

### Scenario 2: Level-Up Session
```bash
# Track all progression-related changes
python discord_notifier.py --include progression
```

**Tracks**: Level increases, ability score improvements, new feats, new spells, spell slot increases
**Ignores**: Equipment shuffling, cosmetic changes, note updates

### Scenario 3: Roleplay-Heavy Session
```bash
# Focus on character development
python discord_notifier.py --include roleplay,inventory.wealth --exclude meta
```

**Tracks**: Appearance changes, backstory updates, wealth changes
**Ignores**: Mechanical statistics, spell changes, diagnostic information

### Scenario 4: Equipment Management
```bash
# Track only inventory and related changes
python discord_notifier.py --include inventory,combat.ac --exclude inventory.wealth
```

**Tracks**: Equipment changes, AC modifications from gear
**Ignores**: Wealth changes, other mechanical changes

### Scenario 5: Minimal Notifications
```bash
# Only track the most important changes
python discord_notifier.py --include basic,combat.hp
```

**Tracks**: Level changes, class progression, hit point modifications
**Ignores**: Everything else

### Scenario 6: Everything Except Diagnostics
```bash
# Track all gameplay changes but ignore system metadata
python discord_notifier.py --exclude meta
```

**Tracks**: All character data changes
**Ignores**: Processing timestamps, diagnostics, scraper version info

## Implementation Benefits

### 1. Flexibility
- Granular control over what changes to track
- Nested grouping for precise filtering
- Composite groups for common use cases

### 2. Performance
- Reduces processing overhead by filtering early
- Minimizes Discord API calls
- Configurable notification frequency

### 3. User Experience
- Intuitive group names matching D&D concepts
- Clear separation of mechanical vs roleplay elements
- Preset configurations for common scenarios

### 4. Maintainability
- Centralized group definitions
- Pattern-based field matching
- Easy to extend with new groups

## Future Enhancements

### 1. Priority Levels
```yaml
groups:
  combat:
    priority: high
    fields: [...]
  appearance: 
    priority: low
    fields: [...]
```

### 2. Threshold-Based Filtering
```yaml
inventory.wealth:
  threshold: 100  # Only notify for changes > 100gp
combat.hp:
  threshold_percent: 10  # Only notify for >10% HP changes
```

### 3. Time-Based Aggregation
```yaml
aggregation:
  basic: immediate
  inventory: 10_minutes
  background: 1_hour
```

### 4. Conditional Logic
```yaml
conditional_groups:
  combat_active:
    when: "in_combat"
    include: ["combat", "spells.slots"]
    exclude: ["inventory", "background"]
```

This comprehensive data group system provides the flexibility needed for different gameplay scenarios while maintaining clear organization and ease of use.