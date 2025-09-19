# Parser Module

The parser module converts character JSON data into beautifully formatted Obsidian-compatible markdown with D&D UI Toolkit integration and comprehensive customization options.

## 🏗️ Architecture

```
parser/
├── dnd_json_to_markdown.py    # Main entry point (orchestrates full pipeline)
├── config.py                  # Parser configuration management
├── core/                      # Core parser interfaces
├── factories/                 # Factory pattern for generators
├── formatters/               # Section-specific formatters
├── templates/                # Template engines (Obsidian, UI Toolkit)
└── utils/                    # Parser utilities and validation
```

## ⚡ Key Features

- **🎯 Primary Entry Point**: Orchestrates scraper → parse → Discord pipeline
- **📝 Obsidian Compatible**: Full YAML frontmatter and markdown formatting
- **🎨 D&D UI Toolkit**: Enhanced character sheet blocks and components
- **📊 Datacore Integration**: Structured frontmatter for data queries and analysis
- **🔧 Customizable Sections**: Configurable section ordering and content
- **✨ Enhanced Spells**: Rich spell descriptions with ritual/concentration flags
- **🔗 Auto-Integration**: Automatically triggers scraper and Discord monitoring

## 🚀 Usage

### Primary Workflow (Recommended)
```bash
# Complete pipeline: scrape → parse → Discord notification
python parser/dnd_json_to_markdown.py CHARACTER_ID

# This automatically:
# 1. Calls scraper for fresh character data (with rate limiting)
# 2. Generates Obsidian-compatible markdown
# 3. Triggers Discord change monitoring
```

### Individual Operations
```bash
# Use existing scraped data (skip scraping step)
python parser/dnd_json_to_markdown.py CHARACTER_ID --use-latest

# Custom output location
python parser/dnd_json_to_markdown.py CHARACTER_ID --output custom_sheet.md

# Verbose debugging
python parser/dnd_json_to_markdown.py CHARACTER_ID --verbose
```

### Programmatic Usage
```python
from parser.dnd_json_to_markdown import CharacterMarkdownGenerator

# Load character data
with open('character_data.json', 'r') as f:
    character_data = json.load(f)

# Generate markdown
generator = CharacterMarkdownGenerator(character_data)
markdown_content = generator.generate_character_sheet()
```

## 🔧 Configuration

Configured via `config/parser.yaml`:

### Section Ordering
```yaml
section_order:
  - "metadata"        # Character metadata and technical info
  - "character_info"  # Basic character information
  - "abilities"       # Ability scores and modifiers
  - "spellcasting"    # Spells and spellcasting abilities
  - "combat"          # Combat stats and attacks
  - "inventory"       # Equipment and items
  # ... customize as needed
```

### Features
```yaml
parser:
  defaults:
    enhance_spells: true         # Use enhanced spell data
    use_dnd_ui_toolkit: true     # Always enabled
    verbose: false               # Debug output
  
  discord:
    enabled: true                # Auto-trigger Discord monitoring
```

## 📋 Generated Content

### YAML Frontmatter (Datacore Compatible)
```yaml
---
character_name: "Sample Character"
level: 3
character_class: "Warlock"
subclass: "The Fiend"
species: "Tiefling"
background: "Charlatan"
armor_class: 13
hit_points: 22
spell_save_dc: 14
# ... extensive metadata for queries
---
```

### Markdown Sections
- **Character Info**: Name, level, class, race, background
- **Ability Scores**: Full ability array with modifiers and saving throws
- **Combat Stats**: AC, HP, speed, attacks, damage
- **Spellcasting**: Spell lists, slots, save DC, attack bonus
- **Features**: Class features, racial traits, background features
- **Proficiencies**: Skills, languages, tool proficiencies
- **Inventory**: Equipment, magical items, wealth
- **Appearance & Backstory**: Physical description and character details

## 🎨 D&D UI Toolkit Integration

The parser generates compatible blocks for enhanced display:

```markdown
## Ability Scores
```dnd-abilities
STR: 12 (+1)  
DEX: 15 (+2)  
CON: 15 (+2)  
INT: 13 (+1)  
WIS: 12 (+1)  
CHA: 16 (+3)  
```

## Spellcasting
```dnd-spells
**Spell Save DC:** 14  
**Spell Attack Bonus:** +6  
**Spells Known:** 4  
```

### Advanced Formatting
- **Spell Cards**: Individual spell blocks with full descriptions
- **Feature Blocks**: Class and racial feature formatting
- **Attack Cards**: Weapon and spell attack formatting
- **Inventory Organization**: Categorized equipment display

## 🔌 Pipeline Integration

### Automatic Scraper Integration
The parser automatically calls the scraper when needed:
- Checks for existing recent data
- Calls scraper with proper rate limiting if needed
- Uses fresh data for parsing

### Discord Monitoring
After successful parsing, automatically triggers:
- Change detection analysis
- Discord notification generation
- Change log updates

### Configuration Control
```yaml
# Disable auto-scraping (use existing data only)
auto_scrape: false

# Disable Discord integration
discord:
  enabled: false
```

## 🎯 Obsidian Integration

### Direct Vault Import
Generated files are ready for direct import into Obsidian:
- Proper YAML frontmatter
- Compatible markdown syntax
- Internal linking support
- Tag integration

### Datacore Queries
Query character data across your vault:
```javascript
// Find all Warlocks
TABLE character_name, level, subclass
FROM "Characters"
WHERE character_class = "Warlock"

// Compare spell save DCs
TABLE character_name, spell_save_dc
FROM "Characters"
WHERE spell_save_dc > 15
SORT spell_save_dc DESC
```

## 📊 Enhanced Spell Processing

### Spell Metadata Extraction
- **Ritual spells**: Automatically flagged
- **Concentration spells**: Identified and marked
- **Source tracking**: Spell source attribution
- **Deduplication**: Intelligent spell deduplication by source

### Local Spell Enhancement
Enhanced spell descriptions from `obsidian/spells/` directory:
- Rich spell descriptions
- Mechanical details
- Casting guidance
- Cross-references

## 🔍 Debugging and Validation

### Debug Mode
```bash
python parser/dnd_json_to_markdown.py CHARACTER_ID --verbose
```

### Validation
- Input data validation
- Output markdown verification
- Template consistency checks
- Link validation

## 📁 Output Management

### File Locations
- **Generated Sheets**: `character_data/parser/{CharacterName}.md`
- **Archive**: `character_data/parser/archive/` (historical versions)

### File Naming
- Primary output: `{CharacterName}.md` (spaces and special chars handled)
- Archive files: `{CharacterName}_{timestamp}.md`

## ⚠️ Important Notes

- **Main Entry Point**: Use the parser as your primary entry point for the full pipeline
- **Rate Limiting**: Parser respects scraper rate limits automatically
- **Data Freshness**: Always generates from latest scraped data unless `--use-latest` specified
- **Obsidian Ready**: Files are immediately importable into Obsidian vaults
- **Version Control Safe**: Generated markdown is safe to commit to repositories

## 🔗 Module Dependencies

- **Scraper**: Calls scraper for fresh character data
- **Discord**: Triggers change monitoring after parsing
- **Shared**: Uses shared configuration and models
- **D&D UI Toolkit**: External dependency for enhanced formatting