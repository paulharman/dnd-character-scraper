# Shared Module

The shared module provides cross-cutting concerns and common functionality used across all other modules, including configuration management, data models, and shared interfaces.

## 🏗️ Architecture

```
shared/
├── config/           # Configuration management system
├── interfaces/       # Shared interfaces and contracts
└── models/          # Common data models and schemas
```

## ⚡ Key Components

### Configuration Management (`config/`)
Centralized configuration system for the entire application:

- **`manager.py`**: Core configuration management with environment variable support
- **`schemas.py`**: Configuration validation schemas and data structures  
- **`settings.py`**: Application settings and defaults
- **`validation_helper.py`**: Configuration validation utilities

#### Features
- **Environment Variable Support**: `${VARIABLE_NAME}` pattern resolution
- **Multi-Format Support**: YAML, JSON configuration loading
- **Validation**: Comprehensive configuration validation with helpful error messages
- **Path Resolution**: Automatic path resolution relative to project root
- **Environment Overrides**: Different configurations for development/testing/production

### Data Models (`models/`)
Common data structures shared across modules:

- **`base.py`**: Base classes and common model patterns
- **`character.py`**: Character data models (AbilityScores, CharacterClass, Species, etc.)
- **`change_detection.py`**: Change detection models (FieldChange, ChangeType, ChangePriority)
- **`storage.py`**: Storage-related models (CompressionType, storage interfaces)

#### Character Models
```python
# Core character data structures
class AbilityScores:
    strength: int
    dexterity: int
    constitution: int
    intelligence: int
    wisdom: int
    charisma: int

class CharacterClass:
    name: str
    level: int
    subclass: Optional[str]
    hit_die: str
```

#### Change Detection Models
```python
class FieldChange:
    field_name: str
    old_value: Any
    new_value: Any
    change_type: ChangeType
    priority: ChangePriority
    timestamp: datetime
```

### Interfaces (`interfaces/`)
Shared contracts and interfaces:

- **`storage.py`**: Storage backend interfaces for consistent data persistence

## 🔧 Configuration System

### Usage Example
```python
from shared.config.manager import get_config_manager

# Get configuration manager
config = get_config_manager()

# Load specific configuration
discord_config = config.load_discord_config()
parser_config = config.load_parser_config()
scraper_config = config.load_scraper_config()

# Access configuration values
webhook_url = discord_config.webhook_url
api_timeout = scraper_config.api.timeout
```

### Environment Variable Resolution
The configuration system automatically resolves environment variables:

```yaml
# In config/discord.yaml
webhook_url: "${DISCORD_WEBHOOK_URL}"  # Resolves from environment
character_id: 12345678                 # Static value
```

### Path Resolution
Automatically resolves paths relative to project root:
```python
# Configuration automatically resolves paths
paths = config.resolve_paths()
character_data_dir = paths["character_data"]  # Full absolute path
spells_dir = paths["spells"]                  # Full absolute path
```

## 📊 Data Models

### Character Data Models
Standardized data structures for character information:

```python
from shared.models.character import Character, AbilityScores, HitPoints

# Create character data
character = Character(
    name="Ilarion Veles",
    level=3,
    character_class=CharacterClass(name="Warlock", level=3, subclass="The Fiend"),
    species=Species(name="Tiefling"),
    ability_scores=AbilityScores(
        strength=12, dexterity=15, constitution=15,
        intelligence=13, wisdom=12, charisma=16
    ),
    hit_points=HitPoints(current=22, maximum=22, temporary=0)
)
```

### Change Detection Models
Structured change tracking:

```python
from shared.models.change_detection import FieldChange, ChangeType, ChangePriority

# Create change record
change = FieldChange(
    field_name="hit_points.maximum",
    old_value=19,
    new_value=22,
    change_type=ChangeType.HIT_POINTS,
    priority=ChangePriority.MEDIUM,
    timestamp=datetime.now()
)
```

## 🔌 Module Integration

### Cross-Module Usage
The shared module is used throughout the application:

#### Scraper Module
- Uses configuration management for API settings
- Uses character models for data structures
- Uses interfaces for storage backend abstraction

#### Parser Module  
- Uses configuration management for parser settings
- Uses character models for data processing
- Uses path resolution for template and output locations

#### Discord Module
- Uses configuration management for Discord settings
- Uses change detection models for tracking changes
- Uses character models for notification formatting

## 🛡️ Security Features

### Secure Configuration
- **Environment Variable Support**: Prevents hardcoding of sensitive data
- **Validation**: Comprehensive validation with security warnings
- **Path Safety**: Safe path resolution prevents directory traversal
- **Type Safety**: Strong typing with validation for all configuration values

### Example Security Patterns
```python
# Secure webhook URL configuration
webhook_url = config.get_secure_setting("webhook_url", required=True)

# Safe path resolution
output_path = config.resolve_safe_path("character_data/parser")

# Validated settings with type checking
timeout = config.get_validated_setting("api.timeout", int, default=30)
```

## 🔍 Validation System

### Configuration Validation
Comprehensive validation for all configuration files:

```python
from shared.config.validation_helper import validate_configuration

# Validate configuration
validation_result = validate_configuration(config_data)
if not validation_result.is_valid:
    for error in validation_result.errors:
        print(f"Configuration error: {error.message}")
```

### Data Model Validation
Built-in validation for all data models:
- **Type validation**: Ensures correct data types
- **Range validation**: Validates numeric ranges (ability scores 1-30, etc.)
- **Required field validation**: Ensures required fields are present
- **Format validation**: Validates URLs, IDs, timestamps

## 📁 File Organization

### Configuration Files Structure
```
config/
├── main.yaml                 # Project-wide settings
├── discord.yaml             # Discord integration settings  
├── parser.yaml              # Parser behavior settings
├── scraper.yaml             # API and scraping settings
└── rules/                   # Game rules configurations
    ├── 2014.yaml           # D&D 2014 rules
    ├── 2024.yaml           # D&D 2024 rules
    └── constants.yaml      # Game constants
```

## 🚀 Usage Patterns

### Getting Started
```python
# Basic configuration usage
from shared.config.manager import get_config_manager

config = get_config_manager()
settings = config.load_main_config()

# Character model usage  
from shared.models.character import Character

character = Character.from_dict(character_data)
```

### Advanced Usage
```python
# Custom configuration loading with validation
config = get_config_manager()
custom_config = config.load_config_file(
    "custom.yaml", 
    validate=True,
    schema=CustomConfigSchema
)

# Change detection with shared models
from shared.models.change_detection import detect_changes

changes = detect_changes(old_character, new_character)
for change in changes:
    print(f"{change.field_name}: {change.old_value} → {change.new_value}")
```

## ⚠️ Important Notes

- **Dependency Order**: Other modules depend on shared - do not import from other modules in shared
- **Configuration Security**: Always use environment variables for sensitive data
- **Model Consistency**: All modules should use shared models for consistency
- **Path Resolution**: Use shared path resolution for cross-platform compatibility
- **Validation**: Leverage built-in validation to prevent configuration errors

## 🔗 Dependencies

### Internal Dependencies
- **None**: The shared module has no dependencies on other application modules

### External Dependencies
- **pydantic**: Data validation and serialization
- **pyyaml**: YAML configuration file parsing
- **pathlib**: Path manipulation and resolution

## 📚 API Reference

### Configuration Manager
- `get_config_manager()`: Get singleton configuration manager instance
- `load_main_config()`: Load main application configuration
- `load_discord_config()`: Load Discord-specific configuration
- `load_parser_config()`: Load parser-specific configuration  
- `load_scraper_config()`: Load scraper-specific configuration
- `resolve_paths()`: Resolve all configured paths to absolute paths

### Data Models
- `Character`: Main character data model
- `AbilityScores`: Ability scores (STR, DEX, CON, INT, WIS, CHA)
- `CharacterClass`: Class information (name, level, subclass)
- `Species`: Character species/race information
- `FieldChange`: Individual change record for change detection
- `ChangeType`: Enumeration of change types
- `ChangePriority`: Change priority levels (LOW, MEDIUM, HIGH, CRITICAL)