# D&D Beyond Character Scraper

A comprehensive tool for scraping and parsing D&D Beyond character data into formatted markdown suitable for Obsidian and other note-taking applications.

## Features

- **Character Data Scraping**: Extract complete character information from D&D Beyond
- **Markdown Generation**: Generate well-formatted character sheets in Obsidian-compatible markdown
- **Discord Integration**: Get notifications when character data changes with detailed change tracking
- **Rule Version Support**: Intelligent detection and support for both D&D 2014 and 2024 rules
- **Complete Equipment Processing**: Full inventory, container organization, and encumbrance tracking
- **Enhanced Spell Processing**: Comprehensive spell detection with feat spell support and intelligent per-source deduplication
- **Robust Error Handling**: Graceful fallback logic and comprehensive logging for troubleshooting

## 🚀 Quick Start

### 1. Download & Navigate

**Example Setup:**
1. Download the project as a ZIP from GitHub (green "Code" button → "Download ZIP")
2. Extract to a folder like `C:\DndCharacterScraper\`
3. Open Command Prompt (Windows Key + R, type `cmd`, press Enter)
4. Navigate to your project folder:

```bash
# Navigate to your project directory (adjust path as needed)
cd C:\DndCharacterScraper

# Verify you're in the right place (should show README.md, config/, scraper/, etc.)
dir
```

**For other locations, adjust the path:**
```bash
# If extracted to Documents folder:
cd C:\Users\YourUsername\Documents\dnd-character-scraper

# If extracted to Desktop:
cd C:\Users\YourUsername\Desktop\dnd-character-scraper
```

### 2. Install Python

**You need Python 3.8 or newer installed first:**
- Download from: https://www.python.org/downloads/
- ✅ **IMPORTANT**: Check "Add Python to PATH" during installation
- Verify installation: open Command Prompt and type `python --version`

### 3. Installation & Setup
```bash
# Install dependencies (make sure you're in the project directory!)
pip install -r requirements.txt

# Create environment file from template
copy .env.example .env
# Edit .env with your Discord webhook URL and other configuration
```

### 4. Configuration
```bash
# Configure Discord settings
copy config\discord.yaml.example config\discord.yaml
# Edit config/discord.yaml with your settings

# Validate configuration (optional)
python discord/discord_monitor.py --validate-config
```

### 5. Character Setup

Note your character ID from the URL: `dndbeyond.com/characters/[CHARACTER_ID]`

**Option A: Public Character (Simple)**
1. Go to your character on D&D Beyond
2. Click **"Edit"** → **"Manage"** → **"Privacy"**
3. Set to **"Public"** (anyone can view)

**Option B: Private Character (Cobalt Session Token)**

If you don't want to make your character public, you can authenticate with your D&D Beyond session:

1. Open your character on D&D Beyond in Chrome/Edge
2. Press **F12** to open DevTools → **Network** tab
3. Refresh the page
4. Find any request to `character-service.dndbeyond.com`
5. In the request headers, find the **Cookie** header
6. Copy the value after `cobalt-session=` (up to the next `;`)
7. Add it to your `.env` file:
   ```
   DNDBEYOND_COBALT_TOKEN=your_token_here
   ```

> **Note:** Cobalt session tokens expire periodically. If you get a 403 error, get a fresh token from your browser.

### 6. Usage

**⚠️ Make sure you're in the project directory** before running these commands!

**Primary Workflow (Recommended)**:
```bash
# Complete pipeline: scrape → parse → Discord notification
# Output directly to your Obsidian vault:
python parser/dnd_json_to_markdown.py CHARACTER_ID "C:\path\to\obsidian\vault\characters\MyCharacter.md"

# Examples:
python parser/dnd_json_to_markdown.py 12345678 "C:\Users\YourName\Documents\MyVault\characters\Ranger.md"
python parser/dnd_json_to_markdown.py 12345678 "D:\Obsidian\DnD\characters\Wizard.md"

# The parser automatically:
# 1. Calls the scraper to get fresh character data
# 2. Generates Obsidian-compatible markdown in your vault
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

## Obsidian Setup

The generated character sheets rely on several Obsidian community plugins and a theme. You will also need to install the JSX components and CSS snippet from this repository.

### Required Plugins

| Plugin | Purpose |
|--------|---------|
| **[Datacore](https://github.com/blacksmithgu/datacore)** | Provides `datacorejsx` code blocks used by the interactive spell list, inventory, and party components |
| **[D&D UI Toolkit](https://github.com/mProjectsCode/obsidian-dnd-ui-toolkit)** | Renders the `stats`, `healthpoints`, `ability`, `badges`, `skills`, and `consumable` code blocks in the character sheet |
| **[Execute Code](https://github.com/twibiral/obsidian-execute-code)** | Runs the `run-python` code block that refreshes character data from within Obsidian |

### Required Theme

- **[ITS Theme](https://github.com/SlRvb/Obsidian--ITS-Theme)** - The character sheets are designed around this theme's styling

### JSX Components

The `obsidian/` directory contains Datacore JSX components that power the interactive parts of the character sheet. Copy these into your vault and set the directory in `config/parser.yaml`:

```yaml
parser:
  templates:
    jsx_components_dir: "z_Templates"   # Vault path where you placed the JSX files
```

| File | Description |
|------|-------------|
| `SpellQuery.jsx` | Interactive spell list with search, level, school, and component filters |
| `SpellGenerator.jsx` | Extracts spell data from the vault's spell markdown files into structured frontmatter |
| `InventoryManager.jsx` | Filterable inventory browser with category and attunement filters |
| `InfusionsManager.jsx` | Artificer infusions viewer for active and known infusions |
| `PartyInventoryManager.jsx` | Party-wide inventory view across all characters |
| `PartyLanguages.jsx` | Shows languages known across the party, organized by character |
| `sessiontracker.jsx` | Session event tracker with categorized events (combat, discovery, plot, social, travel) |
| `SessionNotesSearch.jsx` | Searchable session notes interface |

### Spell Data

The spell list and spell links in the character sheet rely on spell markdown files generated by **[TTRPG-Convert-CLI](https://obsidianttrpgtutorials.com/Obsidian+TTRPG+Tutorials/Plugin+Tutorials/TTRPG-Convert-CLI/TTRPG-Convert-CLI-UI)**, a tool that converts 5e SRD content into Obsidian-compatible markdown. The `SpellQuery.jsx` component reads frontmatter from these spell files to power filtering by level, school, and components, and the character sheet links spell names directly to their full descriptions.

The spell files location is configured in `config/main.yaml`:

```yaml
paths:
  spells_folder: "obsidian/spells"   # Path to TTRPG-Convert-CLI spell files
```

Place your generated spell markdown files in this directory (or update the path to point to where they already live in your vault).

### CSS Snippet

Copy `obsidian/dndb-scraper.css` into your vault's `.obsidian/snippets/` directory and enable it in Settings > Appearance > CSS Snippets. This handles:

- Styling the Python refresh button
- Centering ability score cards
- Badge row layout
- Navigation link positioning

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
├── obsidian/             # Obsidian vault components
│   ├── *.jsx            # Datacore JSX interactive components
│   ├── *.css            # CSS snippets for character sheet styling
│   └── spells/          # Example spell markdown files
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

### Discord Setup

**Environment Variables (Recommended)**:
```yaml
# config/discord.yaml
webhook_url: "${DISCORD_WEBHOOK_URL}"  # Environment variable
character_id: 12345678
```

**Environment File (.env)**:
```bash
# .env (gitignored)
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

## Advanced Usage Examples

### Character Scraping Options
```bash
# Basic scraping
python scraper/enhanced_dnd_scraper.py 12345678

# With Discord notifications
python scraper/enhanced_dnd_scraper.py 12345678 --discord

# Force specific rule version
python scraper/enhanced_dnd_scraper.py 12345678 --force-2024

# Keep HTML formatting and verbose output
python scraper/enhanced_dnd_scraper.py 12345678 --keep-html --verbose

# Save raw API response for debugging
python scraper/enhanced_dnd_scraper.py 12345678 --raw-output raw_data.json
```

### Parser Options
```bash
# Generate without enhanced spells (API only)
python parser/dnd_json_to_markdown.py 12345678 "C:\MyVault\character.md" --no-enhance-spells

# Force specific D&D rules version
python parser/dnd_json_to_markdown.py 12345678 "C:\MyVault\character.md" --force-2024

# Verbose output for debugging
python parser/dnd_json_to_markdown.py 12345678 "C:\MyVault\character.md" --verbose

# Generate from existing data (no scraping)
python parser/dnd_json_to_markdown.py 12345678 "C:\MyVault\character.md" --validate-only
```

### Discord Monitoring
```bash
# Test Discord webhook
python discord/discord_monitor.py --test

# Monitor continuously (default behavior)
python discord/discord_monitor.py

# Run once and exit
python discord/discord_monitor.py --once

# Check existing data without scraping
python discord/discord_monitor.py --check-only

# Monitor party characters
python discord/discord_monitor.py --party
```

## Key Features Explained

### Enhanced Spell Processing
- **Comprehensive Detection**: Finds spells from all sources (Class, Racial, Feat, Item, Background)
- **Intelligent Deduplication**: Removes duplicates within sources while preserving cross-source spells
- **Feat Spell Support**: Properly detects spells from feats like Magic Initiate
- **Fallback Logic**: Graceful handling of edge cases with comprehensive error recovery

### Complete Equipment System
- **Full Inventory**: Processes all character items with complete details
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
- Obsidian with Datacore, D&D UI Toolkit, Execute Code plugins, and ITS Theme (see [Obsidian Setup](#obsidian-setup))

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure the system
cp config/discord.yaml.example config/discord.yaml
# Edit configuration files as needed
```

## Troubleshooting

### Common Issues

**Spell Detection Problems**
- Check the spell processing logs for detailed information
- Verify character has the expected spells in D&D Beyond
- Enable verbose mode for detailed spell processing logs

**Empty Inventory**
- Ensure character has items equipped/carried in D&D Beyond
- Check container organization in the character data
- Verify equipment coordinator is processing container_inventory data

**Path Issues**
- The system uses dynamic path detection
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
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**: Comprehensive troubleshooting guide
- **[docs/ENHANCED_ARCHITECTURE_GUIDE.md](docs/ENHANCED_ARCHITECTURE_GUIDE.md)**: Architecture documentation
- **`config/` files**: Inline comments explaining all settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Update documentation as needed
6. Submit a pull request

## Version History

- **v6.1.0** (Current): Combat enhancements (initiative breakdown, weapon mastery, action economy), complete spell details, Obsidian setup documentation
- **v6.0.0**: Major overhaul with enhanced spell processing, complete inventory support, and improved portability
- **v5.2.0**: Enhanced Discord integration and rule version detection
- **v5.0.0**: Modular architecture with calculation pipeline

## Support

For configuration questions, refer to the [CONFIG_GUIDE.md](CONFIG_GUIDE.md) which contains comprehensive documentation for all available options.

For technical issues, check the logs and enable verbose mode for detailed debugging information.