# Scraper Data Directory

This directory contains raw character data fetched from the D&D Beyond API.

## File Types

- **Calculated Data**: `character_{ID}_{timestamp}.json` - Processed character data with calculations
- **Raw API Data**: `raw/character_{ID}_{timestamp}_raw.json` - Unprocessed API responses

## Data Structure

The scraper saves comprehensive character information including:
- Basic character info (name, level, class, race)
- Ability scores and modifiers
- Skills and proficiencies
- Spells and spell slots
- Equipment and inventory
- Features and traits
- Combat statistics

## Usage

Files are automatically created when running:
```bash
python scraper/enhanced_dnd_scraper.py YOUR_CHARACTER_ID
```