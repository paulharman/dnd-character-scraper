# Scraper Data Directory

This directory contains processed character data from the D&D Beyond API with full calculations applied.

## File Types

- **Processed Data**: `character_{ID}_{timestamp}.json` - Complete character data with v6.0.0 calculations
- **Raw API Data**: `raw/character_{ID}_{timestamp}_raw.json` - Unprocessed API responses for debugging

## Features

- **Complete Calculations**: Ability scores, AC, HP, spell save DC, attack bonuses
- **Rule Version Support**: Automatic detection of D&D 2014 vs 2024 rules  
- **Enhanced Coordinators**: Advanced calculation logic with fallback systems
- **Rate Limited**: Respects D&D Beyond's 30-second API rate limit

## Data Structure

The processed JSON files contain:

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