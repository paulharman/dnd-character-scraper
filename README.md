# D&D Beyond Character Scraper

A comprehensive tool for scraping and parsing D&D Beyond character data into formatted markdown suitable for Obsidian and other note-taking applications.

## 🔐 Security-First Design

This project implements comprehensive security measures to protect your sensitive data:

- **🛡️ Environment Variable Support**: All sensitive data (webhook URLs, session cookies) use secure environment variables
- **🔍 Automatic Security Scanning**: Pre-commit hooks prevent accidental commits of sensitive data
- **✅ Configuration Validation**: Built-in tools validate configurations and detect security issues
- **📋 Security Audit Tools**: Regular security audits with detailed reporting
- **📚 Complete Security Documentation**: Step-by-step security setup and best practices

## ✨ Latest Updates (v6.0.0)

- **🔐 Comprehensive Security Enhancement**: Environment variable support, pre-commit hooks, and security audit tools
- **🛡️ Discord Webhook Protection**: Automatic detection and prevention of hardcoded webhook URLs
- **✅ Configuration Validation**: Built-in validation for Discord configurations with security warnings
- **🔧 Enhanced Error Handling**: Comprehensive error classification and recovery for Discord integration
- **🔍 Security Audit Tools**: Automated security scanning with detailed reporting and recommendations
- **📚 Complete Security Documentation**: Comprehensive guides for secure setup and GitHub repository management

## Features

- **Character Data Scraping**: Extract complete character information from D&D Beyond with v6.0.0 architecture
- **Markdown Generation**: Generate well-formatted character sheets in Obsidian-compatible markdown
- **Discord Integration**: Get notifications when character data changes with detailed change tracking
- **Rule Version Support**: Intelligent detection and support for both D&D 2014 and 2024 rules
- **Complete Equipment Processing**: Full inventory, container organization, and encumbrance tracking
- **Enhanced Spell Processing**: Comprehensive spell detection with feat spell support and intelligent per-source deduplication
- **Robust Error Handling**: Graceful fallback logic and comprehensive logging for troubleshooting

## 🚀 Quick Start

### 1. Secure Setup
```bash
# Run the setup helper (validates security and environment)
python setup_github_repo.py

# Create environment file from template
cp .env.example .env
# Edit .env with your actual Discord webhook URL and other secrets
```

### 2. Configuration
```bash
# Validate your Discord configuration
python discord/discord_monitor.py --validate-config

# Test webhook connectivity (optional)
python discord/discord_monitor.py --validate-webhook

# Run security audit
python scripts/security_audit.py
```

### 3. Character Setup

**⚠️ IMPORTANT**: Your D&D Beyond character must be set to **PUBLIC** for the scraper to access it.

1. Go to your character on D&D Beyond
2. Click **"Edit"** → **"Manage"** → **"Privacy"**
3. Set to **"Public"** (anyone can view)
4. Note your character ID from the URL: `dndbeyond.com/characters/[CHARACTER_ID]`

### 4. Usage

**Primary Workflow (Recommended)**:
```bash
# Complete pipeline: scrape → parse → Discord notification
python parser/dnd_json_to_markdown.py CHARACTER_ID

# The parser automatically:
# 1. Calls the scraper to get fresh character data
# 2. Generates Obsidian-compatible markdown
# 3. Triggers Discord change monitoring and notifications
```

**Individual Components**:
```bash
# Extract character data only
python scraper/enhanced_dnd_scraper.py CHARACTER_ID

# Generate markdown from existing data (skips scraper call)
python parser/dnd_json_to_markdown.py CHARACTER_ID --validate-only

# Monitor character changes only
python discord/discord_monitor.py --character-id CHARACTER_ID
```

## 🏗️ Architecture

The project uses a clean modular architecture with domain-specific separation:

```
├── scraper/core/          # Character data extraction & calculations
│   ├── calculators/       # D&D rule calculations & coordinators  
│   ├── clients/          # D&D Beyond API integration
│   └── services/         # Processing services
├── parser/               # Markdown generation & formatting
│   ├── formatters/       # Output format handlers
│   └── templates/        # Obsidian & UI toolkit integration
├── discord/core/         # Change detection & notifications
│   ├── services/         # Change tracking & notification logic
│   └── storage/          # Data persistence
└── shared/               # Cross-cutting concerns
    ├── config/           # Configuration management
    └── models/           # Shared data models
```

**Integrated Workflow**: The parser serves as the main entry point, orchestrating the entire pipeline automatically with proper rate limiting and error handling.

## Configuration

The system uses YAML configuration files for all settings. See **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)** for detailed documentation on all available options.

### Key Configuration Files

- **`config/discord.yaml`**: Discord notification settings, change type filtering, and data retention
- **`config/parser.yaml`**: Parser behavior, output formatting, and section ordering
- **`config/scraper.yaml`**: API rate limiting, timeout settings, and retry logic
- **`config/main.yaml`**: Project-wide settings, environment configuration, and performance options

### 🔐 Secure Discord Setup

**Environment Variables (Recommended)**:
```yaml
# config/discord.yaml
webhook_url: "${DISCORD_WEBHOOK_URL}"  # Secure environment variable
character_id: 143359582
```

**Environment File (.env)**:
```bash
# .env (never commit this file!)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
```

**Change Type Filtering**:
```yaml
change_types:
  - "level"              # Character level changes
  - "hit_points"         # HP/health changes
  - "spells_known"       # New spells learned
  - "class_features"     # Class feature changes
  # ... and more
```

### Character Sheet Sections

Customize the order of sections in your generated character sheets:

```yaml
section_order:
  - "metadata"           # Character metadata
  - "character_info"     # Basic character information
  - "abilities"          # Ability scores and modifiers
  - "combat"             # Combat stats and attacks
  # ... and more
```

## 🔒 Security Features

**This project implements comprehensive security measures to protect your sensitive data.**

### 🛡️ Built-in Protection

- **Pre-commit Hooks**: Automatically scan for webhook URLs and sensitive data before commits
- **Environment Variable Support**: Secure configuration with `${VAR}` and `%VAR%` patterns
- **Security Audit Tools**: Regular automated security scanning with detailed reports
- **Configuration Validation**: Built-in validation with security warnings
- **Comprehensive .gitignore**: Protects against accidental commits of sensitive files

### 🔧 Security Tools

```bash
# Comprehensive security audit
python scripts/security_audit.py

# Validate Discord configuration
python discord/discord_monitor.py --validate-config

# Test webhook connectivity (without sending notifications)
python discord/discord_monitor.py --validate-webhook
```

### 🌍 Environment Setup

**1. Create Environment File**:
```bash
# Copy template and customize
cp .env.example .env
```

**2. Configure Environment Variables**:
```bash
# .env (never commit this file!)
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_ID/YOUR_TOKEN
DND_SESSION_COOKIE=your_session_cookie_here
```

**3. Use in Configuration**:
```yaml
# config/discord.yaml (SECURE)
webhook_url: "${DISCORD_WEBHOOK_URL}"
character_id: 143359582  # Character IDs are public, not sensitive
```

### 🔍 Security Validation

The system automatically validates your setup:

```bash
# Run setup helper (includes security checks)
python setup_github_repo.py
python discord/discord_monitor.py --validate-config

# Test webhook safely
python discord/discord_monitor.py --validate-webhook
```

See **[docs/SECURITY.md](docs/SECURITY.md)** for complete security guidance.

## Usage

### Basic Character Scraping
```bash
# Scrape a character and save JSON data
python scraper/enhanced_dnd_scraper.py <character_id>

# Scrape with Discord notifications
python scraper/enhanced_dnd_scraper.py <character_id> --discord

# Force specific rule version
python scraper/enhanced_dnd_scraper.py <character_id> --force-2024

# Keep HTML formatting in output
python scraper/enhanced_dnd_scraper.py <character_id> --keep-html
```

### Generate Character Sheet
```bash
# Generate markdown character sheet
python parser/dnd_json_to_markdown.py <character_id> <output_file>

# Generate without enhanced spells (API only)
python parser/dnd_json_to_markdown.py <character_id> <output_file> --no-enhance-spells

# Force specific D&D rules version
python parser/dnd_json_to_markdown.py <character_id> <output_file> --force-2024
python parser/dnd_json_to_markdown.py <character_id> <output_file> --force-2014

# Verbose output for debugging
python parser/dnd_json_to_markdown.py <character_id> <output_file> --verbose
```

### Discord Monitoring
```bash
# Start Discord monitoring service
python discord/discord_monitor.py --config config/discord.yaml

# Check for changes without monitoring
python discord/discord_monitor.py --config config/discord.yaml --check-only

# Monitor party characters instead of single character
python discord/discord_monitor.py --config config/discord.yaml --party

# Run once and exit (no continuous monitoring)
python discord/discord_monitor.py --config config/discord.yaml --once
```

### Advanced Usage
```bash
# Batch process multiple characters
python scraper/enhanced_dnd_scraper.py --batch character_ids.txt

# Quick validation against baseline
python scraper/enhanced_dnd_scraper.py <character_id> --quick-compare validation.json

# Save raw API response for debugging
python scraper/enhanced_dnd_scraper.py <character_id> --raw-output raw_data.json
```

## 🐙 GitHub Repository Setup

This project is designed for secure collaboration on GitHub with comprehensive protection against accidental exposure of sensitive data.

### 📋 Repository Setup Steps

1. **Run Security Setup**:
   ```bash
   python setup_github_repo.py
   ```

2. **Create GitHub Repository**:
   - Go to [GitHub](https://github.com/new)
   - Name: `dnd-character-scraper`
   - Description: "D&D Beyond Character Scraper with Discord Integration"

3. **Connect and Push**:
   ```bash
   git remote add origin https://github.com/YOUR_USERNAME/dnd-character-scraper.git
   git branch -M main
   git push -u origin main
   ```

### 🔐 Security Features for GitHub

- **Pre-commit Protection**: Automatically blocks commits containing webhook URLs
- **Comprehensive .gitignore**: Protects sensitive files from being committed
- **Security Documentation**: Complete setup guides and best practices
- **Environment Templates**: `.env.example` for secure local setup

See **[GITHUB_SETUP_GUIDE.md](GITHUB_SETUP_GUIDE.md)** for detailed instructions.

## Project Structure

```
├── config/                 # YAML configuration files
├── src/                   # Core application source code
│   ├── calculators/       # Character calculation engine
│   ├── clients/          # D&D Beyond API clients
│   ├── models/           # Data models and structures
│   └── services/         # Business logic services
├── scraper/              # Character data scraping tools
├── parser/               # Markdown generation tools
├── discord/              # Discord integration and notifications
├── character_data/       # Stored character data and snapshots
│   ├── scraper/         # Raw scraped JSON data
│   ├── parser/          # Generated markdown files
│   └── discord/         # Discord monitoring data
├── obsidian/            # Obsidian-specific components and templates
├── scripts/             # Security and utility scripts
├── tools/               # Utility scripts and analysis tools
├── data/                # Baseline and validation data
└── docs/                # Documentation
```

## Key Features Explained

### Enhanced Spell Processing
- **Comprehensive Detection**: Finds spells from all sources (Class, Racial, Feat, Item, Background)
- **Intelligent Deduplication**: Removes duplicates within sources while preserving cross-source spells
- **Feat Spell Support**: Properly detects spells from feats like Magic Initiate
- **Fallback Logic**: Graceful handling of edge cases with comprehensive error recovery

### Complete Equipment System
- **Full Inventory**: Processes all 54+ character items with complete details
- **Container Organization**: Handles Bags of Holding, Backpacks, and nested containers
- **Encumbrance Tracking**: Calculates weight, carrying capacity, and movement penalties
- **Magic Item Support**: Tracks attunement, charges, and magical properties

### Rule Version Intelligence
- **Automatic Detection**: Identifies 2014 vs 2024 rules from character data
- **Manual Override**: Force specific rule versions when needed
- **Backward Compatibility**: Supports both rule sets seamlessly

## Installation & Requirements

### Prerequisites
- Python 3.8+
- Required packages: `requests`, `pydantic`, `pyyaml`, `beautifulsoup4`
- Optional: `aiohttp` for async operations

### Setup
```bash
# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development

# Configure the system
cp config/discord.yaml.example config/discord.yaml
# Edit configuration files as needed
```

## Security Tools

The project includes comprehensive security tools for safe operation:

```bash
# Run security audit
python scripts/security_audit.py

# Validate Discord configuration
python discord/discord_monitor.py --validate-config
```
- `tests/calculators/` - Calculator-specific tests  
- `tests/integration/` - End-to-end workflow tests
- `tests/fixtures/` - Standardized test data fixtures

See [docs/testing-workflow.md](docs/testing-workflow.md) for complete testing documentation and [tests/README.md](tests/README.md) for quick reference.

## 📚 Documentation

### Security & Setup
- **[SECURITY.md](docs/SECURITY.md)** - Comprehensive security guide with Git protection
- **[GITHUB_SETUP_GUIDE.md](GITHUB_SETUP_GUIDE.md)** - Step-by-step GitHub repository setup
- **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)** - Complete configuration documentation

### Development & Testing  
- **[testing-workflow.md](docs/testing-workflow.md)** - Testing workflow and best practices
- **[tests/README.md](tests/README.md)** - Quick testing reference
- **[testing-improvements-summary.md](docs/testing-improvements-summary.md)** - Testing improvements overview

### Project Status
- **[project-status.md](docs/project-status.md)** - Current project status and completed improvements

## Troubleshooting

### Common Issues

**Spell Detection Problems**
- Check the spell processing logs for detailed information
- Verify character has the expected spells in D&D Beyond
- See [docs/spell-processing-improvements.md](docs/spell-processing-improvements.md) for detailed troubleshooting

**Empty Inventory**
- Ensure character has items equipped/carried in D&D Beyond
- Check container organization in the character data
- Verify equipment coordinator is processing container_inventory data

**Path Issues**
- The system now uses dynamic path detection
- Ensure you're running from the project root directory
- Check that parser/ and scraper/ directories exist

### Debug Mode
```bash
# Enable verbose logging
python scraper/enhanced_dnd_scraper.py <character_id> --verbose

# Save raw API data for analysis
python scraper/enhanced_dnd_scraper.py <character_id> --raw-output debug.json
```

## Documentation

- **[CONFIG_GUIDE.md](CONFIG_GUIDE.md)**: Complete configuration documentation
- **[docs/spell-processing-improvements.md](docs/spell-processing-improvements.md)**: Spell processing enhancements and troubleshooting
- **[docs/parser-path-handling.md](docs/parser-path-handling.md)**: Parser path handling improvements
- **`config/` files**: Inline comments explaining all settings
- **Code comments**: Detailed comments throughout the codebase

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation as needed
6. Submit a pull request

## Version History

- **v6.0.0** (Current): Major overhaul with enhanced spell processing, complete inventory support, and improved portability
- **v5.2.0**: Enhanced Discord integration and rule version detection
- **v5.0.0**: Modular architecture with calculation pipeline

## Support

For configuration questions, refer to the [CONFIG_GUIDE.md](CONFIG_GUIDE.md) which contains comprehensive documentation for all available options.

For spell processing issues, see the [spell processing troubleshooting guide](docs/spell-processing-improvements.md).

For technical issues, check the logs and enable verbose mode for detailed debugging information.