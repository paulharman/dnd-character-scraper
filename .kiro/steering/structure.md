# Project Structure

## Root Directory Layout

```
├── config/                 # YAML configuration files
├── src/                   # Core application source code
├── scraper/              # Character data scraping tools
├── parser/               # Markdown generation tools
├── discord/              # Discord integration and notifications
├── character_data/       # Stored character data and snapshots
├── obsidian/            # Obsidian-specific components and templates
├── tests/               # Test suite with comprehensive coverage
├── tools/               # Utility scripts and analysis tools
├── data/                # Baseline and validation data
└── docs/                # Documentation
```

## Core Source Structure (`src/`)

- **`models/`**: Pydantic data models with extensibility support
  - `base.py`: ExtensibleModel base class for unknown field handling
  - `character.py`: Character-specific models (AbilityScores, HitPoints, etc.)
  - `storage.py`: Storage metadata and configuration models
  - `change_detection.py`: Core change detection models and enums
  - `enhanced_change_detection.py`: Enhanced change detection configuration and mappings
  - `change_log.py`: Change logging models with causation and attribution

- **`storage/`**: Multiple storage backend implementations
  - `file_json.py`: JSON file storage
  - `file_sqlite.py`: SQLite database storage
  - `database_postgres.py`: PostgreSQL storage
  - `factory.py`: Storage factory pattern implementation

- **`services/`**: High-level business logic services
  - `enhanced_change_detection_service.py`: Primary change detection service (consolidated)
  - `enhanced_change_detectors.py`: Specialized detectors for different change types
  - `change_log_service.py`: Persistent change logging with causation analysis
  - `causation_analyzer.py`: Change causation and attribution analysis
  - `error_handler.py`: Comprehensive error handling and recovery
- **`validators/`**: Data validation and regression testing
- **`utils/`**: Utility classes (HTMLCleaner, etc.)
- **`interfaces/`**: Abstract base classes and protocols

## Configuration Structure (`config/`)

- **`main.yaml`**: Project-wide settings and environment configuration
- **`parser.yaml`**: Parser behavior and output formatting preferences
- **`scraper.yaml`**: API settings and scraper configuration
- **`discord.yaml`**: Discord integration and notification settings
- **`rules/`**: Rule-specific configuration files
- **`environments/`**: Environment-specific overrides

## Key Conventions

### File Naming
- Use snake_case for Python files and directories
- Configuration files use descriptive names (e.g., `discord.yaml`, `parser.yaml`)
- Test files prefixed with `test_`
- Backup files include timestamps or version numbers

### Code Organization
- Each module has clear separation of concerns
- Pydantic models use `ExtensibleModel` base class for forward compatibility
- Factory pattern for creating storage backends
- Async/await patterns for I/O operations
- Comprehensive type hints throughout

### Data Flow
1. **Scraper** → Fetches raw data from D&D Beyond API
2. **Storage** → Saves/retrieves character data with versioning
3. **Enhanced Change Detection** → Detects and analyzes character changes with causation
4. **Change Logging** → Persists changes with detailed attribution and causation analysis
5. **Parser** → Converts data to formatted markdown
6. **Discord** → Monitors changes and sends notifications using enhanced detection
7. **Validators** → Ensures data integrity and regression testing

### Change Detection Architecture
- **Single Enhanced System**: Consolidated change detection using specialized detectors
- **Causation Analysis**: Automatic detection of what caused each change
- **Change Logging**: Persistent storage of all changes with detailed context
- **Priority Classification**: Intelligent prioritization of changes for notifications
- **Field Mapping**: Comprehensive mapping of D&D Beyond API fields to logical categories

### Configuration Management
- YAML-based configuration with environment overrides
- User preferences clearly separated from system settings
- Extensive inline documentation in config files
- Validation of configuration values using Pydantic models