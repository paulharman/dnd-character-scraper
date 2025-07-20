# Character Data Directory

This directory contains character data organized by processing stage:

## Directory Structure

```
character_data/
├── scraper/        # Raw character data from D&D Beyond API
├── parser/         # Generated markdown character sheets
├── discord/        # Discord notification data
└── archive/        # Historical character data backups
```

## Data Flow

1. **Scraper** → Fetches character data from D&D Beyond and saves to `scraper/`
2. **Parser** → Converts JSON data to markdown and saves to `parser/`
3. **Discord** → Monitors changes and saves notification data to `discord/`
4. **Archive** → Automatic backups of character data over time

## File Naming Convention

- **Scraper files**: `character_{ID}_{timestamp}.json`
- **Parser files**: `{CharacterName}_Character_Sheet.md`
- **Discord files**: `character_{ID}_{timestamp}.json`
- **Raw API files**: `character_{ID}_{timestamp}_raw.json`

## Usage

The application automatically manages these directories. Character data is saved here when you run:

```bash
# Scrape character data
python scraper/enhanced_dnd_scraper.py YOUR_CHARACTER_ID

# Generate markdown
python parser/dnd_json_to_markdown.py YOUR_CHARACTER_ID
```

## Privacy Note

Your personal character data is excluded from the public repository for privacy. This directory structure shows how the application organizes data locally.