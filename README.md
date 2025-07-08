# D&D Beyond Character Scraper v6.0.0

A production-ready D&D Beyond character data scraper with comprehensive support for both 2014 and 2024 D&D rules, featuring a modular architecture, intelligent rule detection, container inventory tracking, and complete backward compatibility.

![Version](https://img.shields.io/badge/version-6.0.0--production-brightgreen.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-production--ready-brightgreen.svg)

## 🚀 Quick Start

### Basic Usage

```bash
# Scrape character data (v6.0.0) - HTML stripped by default for clean JSON
python3 scraper/enhanced_dnd_scraper.py 144986992

# Force specific rule version
python3 scraper/enhanced_dnd_scraper.py 144986992 --force-2024

# Preserve HTML tags in descriptions (if needed)
python3 scraper/enhanced_dnd_scraper.py 144986992 --keep-html

# Convert to markdown
python3 parser/dnd_json_to_markdown.py 144986992 character_sheet.md

# Monitor character changes with Discord notifications (single character)
python3 discord/discord_monitor.py --config discord/discord_config.yml --once

# Monitor multiple characters (party mode)
python3 discord/discord_monitor.py --config discord/discord_config.yml --party --once
```

### Advanced Usage

```bash
# Private character with session cookie
python3 scraper/enhanced_dnd_scraper.py 144986992 --session "your_session_cookie"

# Verbose debugging with raw output
python3 scraper/enhanced_dnd_scraper.py 144986992 --verbose --raw-output raw_data.json

# Custom output file
python3 scraper/enhanced_dnd_scraper.py 144986992 --output my_character.json

# Batch processing with HTML preservation
python3 scraper/enhanced_dnd_scraper.py --batch character_ids.txt --keep-html

# Discord monitoring (continuous mode)
python3 discord/discord_monitor.py --config discord/discord_config.yml --monitor

# Discord party monitoring (one-shot check)
python3 discord/discord_monitor.py --config discord/discord_config.yml --party --once
```

## ✨ v6.0.0 Production Features

### 🔧 Resolved Critical Issues
- **Fixed Barbarian Unarmored Defense**: Correctly calculates `AC = 10 + DEX + CON`
- **Fixed Monk Unarmored Defense**: Correctly calculates `AC = 10 + DEX + WIS`
- **Clean JSON Output**: HTML tags stripped by default for cleaner, smaller JSON files
- **Robust Error Handling**: Professional exception handling with detailed diagnostics
- **Complete Phase 5 Integration**: All planned phases successfully implemented

### 🧠 Intelligent Rule Detection
- **Automatic 2014/2024 Detection**: Analyzes character data with 80%+ confidence
- **Manual Override Options**: `--force-2014` and `--force-2024` flags
- **Conservative Fallback**: Mixed content defaults to 2014 rules for compatibility
- **Detailed Detection Reporting**: Shows confidence levels, methods, and evidence

### 🏗️ Production Architecture
- **Modular Design**: 15+ specialized calculators with clear separation of concerns
- **Rule-Aware Components**: Each calculator adapts intelligently to 2014 vs 2024 rules
- **Container Inventory System**: Comprehensive container tracking and organization
- **Advanced Character Details**: Enhanced appearance, equipment, and resource tracking
- **Comprehensive Testing**: 50+ unit tests, edge cases, and integration tests
- **Professional Validation**: Multi-layer validation with regression testing

### 📦 Container Inventory Tracking
- **Nested Container Support**: Properly organizes items within containers
- **Weight Distribution**: Accurate weight calculations across container hierarchy
- **Equipment Integration**: Links equipment with container storage locations
- **API Data Extraction**: Comprehensive container data from D&D Beyond API

### 📢 Discord Change Monitoring
- **Real-time Notifications**: Monitor character changes and send Discord alerts
- **Smart Filtering**: 9 core data groups with granular include/exclude controls
- **Preset Configurations**: Combat-only, level-up, shopping, and more scenarios
- **Change Detection**: Intelligent comparison between character snapshots
- **Private Character Support**: Works with session cookies for private characters
- **Party Mode**: Monitor multiple characters with `--party` flag
- **Flexible Run Modes**: One-shot (`--once`) or continuous monitoring (`--monitor`)
- **Snapshot Archiving**: Automatic cleanup with configurable retention limits

### 🧹 Clean JSON Output
- **HTML Stripping by Default**: Removes `<p>`, `<strong>`, `<br>` and other HTML tags from descriptions
- **Configurable Cleaning**: Use `--keep-html` flag to preserve HTML when needed
- **Smaller File Sizes**: Significantly reduces JSON file size by removing markup
- **Better Readability**: Clean text in descriptions, snippets, and feature text
- **Entity Decoding**: Converts HTML entities (`&amp;`, `&quot;`, etc.) to readable characters

### 🔄 Complete Backward Compatibility
- **v5.2.0 API Compatible**: All existing command-line options preserved and enhanced
- **Archive Preservation**: Original v5.2.0 scripts maintained with SHA256 verification
- **Enhanced Output Format**: JSON structure includes all v5.2.0 data plus new features
- **Drop-in Replacement**: Use v6.0.0 commands exactly like v5.2.0 with superior results

## 📁 Project Structure

```
CharacterScraper/
├── scraper/                          # 🤖 Character scraping system
│   └── enhanced_dnd_scraper.py       # Main v6.0.0 scraper script
├── parser/                           # 📝 Markdown generation system  
│   └── dnd_json_to_markdown.py       # Enhanced markdown generator
├── discord/                          # 💬 Discord monitoring system
│   └── discord_monitor.py            # Discord change notifications
├── run_discord_monitor.py            # 🚀 Easy Discord launcher
├── archive/v5.2.0/                  # 📦 Original working v5.2.0 scripts
├── src/                             # 🏗️ v6.0.0 Production Architecture
│   ├── calculators/                 # 🧮 Character calculation modules (15+ calculators)
│   │   ├── character_calculator.py  # Main calculation coordinator
│   │   ├── ability_scores.py        # Ability score calculations with source tracking
│   │   ├── armor_class.py           # AC with Unarmored Defense fixes
│   │   ├── hit_points.py            # HP calculations with Constitution bonuses
│   │   ├── spellcasting.py          # Spell slot calculations with multiclass support
│   │   ├── proficiencies.py         # Skill and proficiency calculations
│   │   ├── container_inventory.py   # Container organization and weight tracking
│   │   ├── character_appearance.py  # Appearance and avatar processing
│   │   ├── equipment_details.py     # Equipment processing and organization
│   │   ├── resource_tracking.py     # Resource management and tracking
│   │   ├── class_features.py        # Class feature processing
│   │   ├── encumbrance.py           # Weight and encumbrance calculations
│   │   └── wealth.py                # Currency and wealth management
│   ├── rules/                       # 📖 Rule version management
│   │   ├── version_manager.py       # 2014/2024 rule detection
│   │   └── constants.py             # D&D game constants
│   ├── clients/                     # 🌐 API client abstraction
│   │   ├── dndbeyond_client.py      # D&D Beyond API client
│   │   └── factory.py               # Client factory pattern
│   ├── config/                      # ⚙️ Configuration management
│   │   └── settings.py              # Environment-aware settings
│   ├── models/                      # 📊 Data models
│   │   ├── base.py                  # Base Pydantic models
│   │   └── character.py             # Character data structures
│   ├── validators/                  # ✅ Comprehensive validation framework
│   │   ├── base.py                  # Base validation classes
│   │   ├── character.py             # Character data validation
│   │   ├── calculations.py          # Calculation consistency checks
│   │   ├── regression.py            # v5.2.0 regression testing
│   │   └── data_validator.py        # Advanced data validation and sanitization
│   ├── storage/                     # 💾 Storage backend abstraction
│   │   ├── memory.py                # In-memory storage
│   │   ├── file_json.py             # JSON file storage
│   │   ├── file_sqlite.py           # SQLite database storage
│   │   ├── database_postgres.py     # PostgreSQL database storage
│   │   ├── cache.py                 # Caching mechanisms
│   │   ├── archiving.py             # Shared snapshot archiving system
│   │   └── factory.py               # Storage factory pattern
│   ├── formatters/                  # 📝 Output formatting
│   │   ├── base.py                  # Base formatter classes
│   │   └── yaml_formatter.py        # YAML output formatting
│   └── services/                    # 🔧 High-level services
│       └── scraper_service.py       # Main scraper service coordination
├── tests/                           # 🧪 Comprehensive test suite
│   ├── unit/                        # Unit tests for all modules
│   ├── edge_cases/                  # Edge case and stress tests
│   ├── integration/                 # End-to-end integration tests
│   └── run_all_tests.py             # Professional test runner
├── data/baseline/                   # 📋 Validation baseline data
│   ├── raw/                         # Raw D&D Beyond API responses
│   ├── scraper/                     # v5.2.0 scraper outputs
│   └── parser/                      # v5.2.0 parser outputs
└── config/                          # 📝 Configuration files
    ├── default.yaml                 # Default configuration
    └── rules/                       # Rule-specific configs
```

## 🔍 Rule Version Detection

The scraper automatically detects whether a character uses 2014 or 2024 D&D rules:

### Detection Methods (Highest to Lowest Priority)

1. **User Override** (`--force-2014` / `--force-2024`) - Absolute priority
2. **Primary Class Analysis** - Main class source determines rule version
3. **Source Book ID Detection** - 2024 sources (142-144) vs 2014 sources
4. **Species/Race Terminology** - "species" (2024) vs "race" (2014)
5. **Default to 2024** - With informational message if uncertain

### Example Detection Output

```
Rule Version Detected: 2024
Confidence: 95.0%
Detection Method: primary_class
Evidence:
  - Primary class source ID 142 (2024 PHB)
  - Uses 'species' terminology (2024 rules)
  - Background source ID 142 (2024 PHB)
```

## 🛠️ Installation & Setup

### Prerequisites

- Python 3.8+
- pip package manager

### Dependencies

```bash
# Install required dependencies
pip install -r requirements.txt

# Install development dependencies (for testing)
pip install -r requirements-dev.txt
```

### Core Dependencies
- `requests` - HTTP client for D&D Beyond API
- `pydantic` - Data validation and parsing
- `pyyaml` - Configuration file parsing

### Development Dependencies
- `pytest` - Testing framework
- `pytest-cov` - Coverage reporting
- `mypy` - Static type checking
- `black` - Code formatting

## 📚 Command Line Reference

### Main Scraper (`scraper/enhanced_dnd_scraper.py`)

```bash
python3 scraper/enhanced_dnd_scraper.py CHARACTER_ID [OPTIONS]

# Required Arguments:
  CHARACTER_ID              D&D Beyond character ID (from character URL)

# Core Options:
  --output, -o FILE         Output JSON file (default: character name)
  --session COOKIE          Session cookie for private characters
  --verbose, -v             Enable verbose debug logging
  --html                    Preserve HTML formatting in descriptions

# v6.0.0 New Options:
  --force-2014              Force 2014 rule interpretation
  --force-2024              Force 2024 rule interpretation (recommended for 2024 characters)
  --config FILE             Path to configuration file (YAML)
  --rule-debug              Show detailed rule version detection

# Debug Options:
  --raw-output FILE         Save raw API response (debugging)
```

### Markdown Generator (`parser/dnd_json_to_markdown.py`)

```bash
python3 parser/dnd_json_to_markdown.py CHARACTER_ID OUTPUT_FILE [OPTIONS]

# Required Arguments:
  CHARACTER_ID              Character ID or JSON file path
  OUTPUT_FILE               Output markdown file path

# Options:
  --scraper-path PATH       Path to scraper script
  --no-enhance-spells       Use API spell data only (faster)
  --force-2014              Force 2014 rule interpretation
  --force-2024              Force 2024 rule interpretation
  --verbose, -v             Enable verbose logging
```

### Discord Character Monitor (`discord/discord_monitor.py`)

```bash
# Test Discord webhook
python3 discord/discord_monitor.py --config discord/discord_config.yml --test

# Monitor single character (one-shot check)
python3 discord/discord_monitor.py --config discord/discord_config.yml --once

# Monitor multiple characters (party mode, one-shot)
python3 discord/discord_monitor.py --config discord/discord_config.yml --party --once

# Continuous monitoring (single character)
python3 discord/discord_monitor.py --config discord/discord_config.yml --monitor

# Continuous party monitoring
python3 discord/discord_monitor.py --config discord/discord_config.yml --party --monitor

# Check existing snapshots without new scraping
python3 discord/discord_monitor.py --config discord/discord_config.yml --check-only

# Available Options:
  --test                    Test Discord webhook and exit
  --test-detailed           Send detailed test notification with sample data
  --config FILE             Configuration file path (default: discord_config.yml)
  --once                    Run once and exit (overrides config setting)
  --monitor                 Run continuously as a monitor (overrides config setting)
  --party                   Monitor all characters in party config instead of single character_id
  --check-only              Check existing snapshots without scraping
  --verbose                 Enable verbose logging
```

#### Discord Setup Examples

```bash
# Test webhook connection
python3 discord/discord_monitor.py --config discord/discord_config.yml --test

# Quick single character check
python3 discord/discord_monitor.py --config discord/discord_config.yml --once

# Monitor entire party for changes
python3 discord/discord_monitor.py --config discord/discord_config.yml --party --once

# Continuous monitoring (runs every 10 minutes)
python3 discord/discord_monitor.py --config discord/discord_config.yml --monitor

# Continuous party monitoring
python3 discord/discord_monitor.py --config discord/discord_config.yml --party --monitor

# Check existing snapshots without scraping new data
python3 discord/discord_monitor.py --config discord/discord_config.yml --check-only

# Monitor private character (configure session cookie in discord_config.yml)
python3 discord/discord_monitor.py --config discord/discord_config.yml --once --verbose
```

#### Discord Configuration Structure

The `discord/discord_config.yml` file supports both single character and party monitoring:

```yaml
# Discord webhook URL (required)
webhook_url: "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL"

# Single character mode (default behavior)
character_id: "143359582"

# Party mode (use --party flag to enable)
party:
  - character_id: "143359582"
  - character_id: "ANOTHER_PARTY_MEMBER_ID"
  - character_id: "THIRD_PARTY_MEMBER_ID"

# Run mode configuration
run_continuous: false  # false = one-shot, true = continuous

# Snapshot archiving (automatic cleanup)
max_snapshots_per_character: 10  # Keep 10 most recent snapshots per character

# Check interval for continuous mode (seconds)
check_interval: 600  # 10 minutes

# Filtering configuration
filtering:
  change_types:
    - "level"
    - "hit_points"
    - "armor_class"
    - "spells_known"
    # ... add other change types as needed
```

#### Discord Data Groups

**Core Groups (9 available):**
- `basic` - Character identity and progression (HIGH priority)
- `stats` - Ability scores, skills, saves (HIGH priority)  
- `combat` - Combat statistics like AC, HP, initiative (HIGH priority)
- `spells` - Spellcasting data and spell slots (HIGH priority)
- `inventory` - Equipment and wealth (MEDIUM priority)
- `features` - Class features, traits, feats (MEDIUM priority)
- `appearance` - Physical description (LOW priority)
- `background` - Backstory and personality (LOW priority)
- `meta` - System metadata (LOW priority)

**Nested Groups for Granular Control:**
- `combat.hp`, `combat.ac`, `spells.slots`, `stats.abilities`, etc.

**Composite Groups for Common Scenarios:**
- `progression` - Character advancement tracking
- `mechanics` - Game mechanics focus
- `roleplay` - Story and character development
- `resources` - Resource management

## 🧪 Testing

### Run All Tests

```bash
# Run comprehensive test suite
python3 tests/run_all_tests.py

# Run specific test suites
python3 tests/run_all_tests.py --suite unit
python3 tests/run_all_tests.py --suite edge
python3 tests/run_all_tests.py --suite integration

# Verbose output with detailed reporting
python3 tests/run_all_tests.py --verbosity 2
```

### Test Coverage

- **Unit Tests**: Individual calculator and component testing (✅ Armor Class bugs fixed)
- **Edge Cases**: Extreme stats, multiclass scenarios, unknown content
- **Integration Tests**: Complete character processing pipeline
- **Regression Tests**: Validation against v5.2.0 baseline data
- **Real Character Testing**: All 12+ test character IDs process successfully
- **Bug Verification**: Specific tests for Barbarian and Monk Unarmored Defense fixes

### Test Results Status

```
D&D Beyond Character Scraper v6.0.0 - Production Test Suite
================================================================================

✅ PRODUCTION READY - All Critical Systems Operational

Test Coverage:
────────────────────────────────────────────────────────────────────────────────
✓ Unit Tests: 50+ tests covering all calculators and core components
✓ Edge Cases: Extreme stats, multiclass scenarios, unknown content handling
✓ Integration Tests: End-to-end character processing pipeline
✓ Regression Tests: v5.2.0 baseline validation for 13 test characters
✓ Real Character Tests: All 13 known character IDs process successfully
✓ Container Tracking: Comprehensive inventory organization testing
✓ Rule Detection: 2014/2024 rule version detection with 80%+ confidence

Critical Bug Fixes Verified:
────────────────────────────────────────────────────────────────────────────────
✓ Barbarian Unarmored Defense: 10 + DEX + CON calculation working
✓ Monk Unarmored Defense: 10 + DEX + WIS calculation working
✓ Container Inventory: Proper nested container organization
✓ Spell Calculations: Multiclass spell slot calculations accurate
✓ Rule Version Detection: Intelligent 2014/2024 detection

🎉 All systems operational and production-ready!
```

## 🔧 Configuration

### Environment Variables

```bash
# API Configuration
export DNDBEYOND_API_TIMEOUT=30
export DNDBEYOND_MIN_DELAY=30.0        # Respect 30-second minimum
export DNDBEYOND_USER_AGENT="Your-App/1.0"

# Rule Detection
export DNDBEYOND_DEFAULT_RULES=auto    # auto, 2014, 2024
export DNDBEYOND_CONSERVATIVE_DETECTION=true

# Logging
export DNDBEYOND_LOG_LEVEL=INFO
export DNDBEYOND_DEBUG=false

# Paths
export DNDBEYOND_CONFIG_DIR=./config
export DNDBEYOND_SPELLS_DIR=./spells
export DNDBEYOND_DATA_DIR=./data
```

### Configuration Files

Create `config/local.yaml` for custom settings:

```yaml
api:
  timeout: 30
  min_delay: 30.0
  user_agent: "My-Custom-Scraper/1.0"

rules:
  default_version: "auto"
  conservative_detection: true

logging:
  level: "INFO"
  debug: false

archiving:
  max_snapshots_per_character: 10  # Keep 10 most recent snapshots per character
  auto_archive: true                # Enable automatic archiving
  
storage:
  character_data_dir: "./character_data"  # Directory for character snapshots
  archive_subdir: "archive"               # Subdirectory for archived snapshots
```

## 📁 Snapshot Archiving System

The v6.0.0 system includes automatic snapshot archiving to manage storage and maintain character history:

### Features

- **Automatic Cleanup**: Keeps only the most recent snapshots per character (configurable limit)
- **Shared Implementation**: Both Discord monitor and parser use the same archiving logic
- **Safe Archiving**: Moves old snapshots to `archive/` subdirectory instead of deleting
- **Configurable Retention**: Set `max_snapshots_per_character` in Discord config
- **Error Handling**: Graceful handling of archiving failures with detailed logging

### Configuration

```yaml
# In discord/discord_config.yml
max_snapshots_per_character: 10  # Keep 10 most recent snapshots

# In config/local.yaml (optional)
archiving:
  max_snapshots_per_character: 10
  auto_archive: true
  
storage:
  character_data_dir: "./character_data"
  archive_subdir: "archive"
```

### How It Works

1. **Discord Monitor**: Archives snapshots after scraping new character data
2. **Parser**: Archives snapshots after generating markdown files
3. **Archive Location**: Old snapshots moved to `character_data/archive/`
4. **Retention Logic**: Keeps N most recent files, archives older ones
5. **Logging**: Reports archiving activity with file counts

### Manual Archiving

```bash
# Check archive statistics
python3 -c "
from src.storage.archiving import SnapshotArchiver
from pathlib import Path
archiver = SnapshotArchiver()
stats = archiver.get_archive_stats(Path('character_data'))
print(f'Active: {stats[\"active_snapshots\"]}, Archived: {stats[\"archived_snapshots\"]}')
"

# Manually trigger archiving for specific character
python3 -c "
from src.storage.archiving import SnapshotArchiver
from pathlib import Path
archiver = SnapshotArchiver()
result = archiver.archive_old_snapshots(143359582, Path('character_data'))
print(f'Archived {result} snapshots')
"
```

## 🔒 Rate Limiting & Ethics

This scraper respects D&D Beyond's terms of service:

- **30-second minimum delay** between API requests
- **Random jitter** to avoid predictable patterns
- **Exponential backoff** on rate limit responses
- **User-Agent identification** for transparency
- **Session cookie support** for private characters only

### Responsible Usage

- Only scrape your own characters or those you have permission to access
- Don't attempt to bypass private character restrictions
- Respect D&D Beyond's rate limits and server resources
- Use the `--verbose` flag to monitor your request patterns

## 🐛 Troubleshooting

### System Status: ✅ PRODUCTION READY - Phase 5 Complete

The v6.0.0 system has successfully completed all planned development phases (0-5) and is fully operational with comprehensive feature set. All critical bugs from v5.2.0 have been resolved, and the system provides superior accuracy and functionality.

### Common Issues

#### Character Not Found (404)
```bash
# Check character ID and URL
https://ddb.ac/characters/144986992
#                         ^^^^^^^^^ This is your character ID
```

#### Private Character (403)
```bash
# Use session cookie from browser
python3 scraper/enhanced_dnd_scraper.py 144986992 --session "your_session_cookie"
```

#### Rate Limited (429)
```bash
# Wait and retry - the scraper handles this automatically
# Check your request frequency with --verbose
```

#### Module Import Errors
```bash
# Ensure you're running from project root
cd /path/to/CharacterScraper
python3 scraper/enhanced_dnd_scraper.py 144986992
```

#### Discord Monitor Issues
```bash
# Test webhook connection
python3 discord/discord_monitor.py --config discord/discord_config.yml --test

# Check party configuration
python3 discord/discord_monitor.py --config discord/discord_config.yml --party --test

# Verify archiving is working
python3 -c "from src.storage.archiving import SnapshotArchiver; print('Archiving system loaded successfully')"
```

#### Archiving Issues
```bash
# Check current snapshot counts
ls character_data/character_143359582_*.json | wc -l

# Check archive directory
ls character_data/archive/character_143359582_*.json | wc -l

# Test archiving manually
python3 -c "
from src.storage.archiving import SnapshotArchiver
from pathlib import Path
archiver = SnapshotArchiver()
result = archiver.archive_old_snapshots(143359582, Path('character_data'))
print(f'Manual archiving moved {result} files')
"
```

### Debug Mode

```bash
# Enable detailed logging
python3 scraper/enhanced_dnd_scraper.py 144986992 --verbose

# Save raw API response for analysis
python3 scraper/enhanced_dnd_scraper.py 144986992 --raw-output debug.json
```

### Validation Issues

```bash
# Run validation framework
python3 test_validation_framework.py 144986992

# Compare with v5.2.0 baseline
python3 tools/baseline/baseline_comparison.py 144986992
```

## 🔄 Migration from v5.2.0

### Command Compatibility

All v5.2.0 commands work unchanged in v6.0.0:

```bash
# v5.2.0 style (still works)
python3 scraper/enhanced_dnd_scraper.py 144986992 --output char.json --verbose

# v6.0.0 enhanced (new features)
python3 scraper/enhanced_dnd_scraper.py 144986992 --output char.json --verbose --force-2024
```

### Enhanced Output Format

JSON output structure preserves all v5.2.0 data with significant enhancements:

```json
{
  "basic_info": {
    "character_id": 144986992,
    "name": "Character Name",
    "level": 5,
    "armor_class": {
      "total": 16,
      "base": 10,
      "modifiers": [...],           // 🆕 Detailed AC breakdown
      "calculation": "Leather + Dex"
    },
    "hit_points": {
      "maximum": 45,
      "constitution_bonus": 10,    // 🆕 Detailed HP breakdown
      "hit_point_method": "Manual"
    }
  },
  "containers": {                   // 🆕 Container inventory system
    "container_id": {
      "name": "Backpack",
      "items": [...],
      "weight": 15.5
    }
  },
  "inventory": [...],              // 🆕 Enhanced inventory with container links
  "appearance": {...},             // 🆕 Comprehensive appearance data
  "equipment_details": {...},      // 🆕 Enhanced equipment processing
  "rule_detection": {              // 🆕 Intelligent rule detection
    "version": "2024",
    "confidence": 0.8,
    "method": "source_ids",
    "evidence": [...]
  },
  "meta": {
    "scraper_version": "6.0.0",    // 🆕 Updated version
    "processing_time": 1.2,        // 🆕 Performance metrics
    "features_used": [...]          // 🆕 Feature tracking
  }
  // ... all existing v5.2.0 fields preserved and enhanced
}
```

### Archived Scripts

Original v5.2.0 scripts remain available:

```bash
# Use original v5.2.0 scraper
python3 archive/v5.2.0/enhanced_dnd_scraper_v5.2.0_original.py 144986992

# Use original v5.2.0 parser
python3 archive/v5.2.0/dnd_json_to_markdown_v5.2.0_original.py 144986992 output.md
```

## 🤝 Contributing

### Development Setup

```bash
# Clone repository
git clone <repository-url>
cd CharacterScraper

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
python3 tests/run_all_tests.py

# Format code
black src/ tests/

# Type checking
mypy src/
```

### Testing Your Changes

```bash
# Run full test suite
python3 tests/run_all_tests.py

# Test specific character
python3 scraper/enhanced_dnd_scraper.py 144986992 --verbose

# Validate against baseline
python3 tools/baseline/baseline_comparison.py 144986992
```

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Wizards of the Coast** - For creating D&D
- **D&D Beyond** - For providing the character API
- **Community Contributors** - For testing and feedback
- **Original v5.2.0 Users** - For establishing the baseline

## 📞 Support

- **Issues**: Report bugs and request features on GitHub Issues
- **Documentation**: Additional guides in `/docs/`
- **Testing**: Comprehensive test results in `/tests/`
- **Baseline Data**: Validation data in `/data/baseline/`

---

**Made with ❤️ for the D&D community**

*This tool respects D&D Beyond's terms of service and is intended for personal use only.*