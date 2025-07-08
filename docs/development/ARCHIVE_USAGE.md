# Archive Scripts Usage Guide

This guide provides instructions for using the original v5.2.0 scripts from their new archive location.

## File Locations

### Original Scripts (SHA256 Verified)
- **Scraper**: `archive/v5.2.0/enhanced_dnd_scraper_v5.2.0_original.py`
- **Parser**: `archive/v5.2.0/dnd_json_to_markdown_v5.2.0_original.py`

### Baseline Data
- **Raw JSON**: `data/baseline/raw/{character_id}.json`
- **Scraper JSON**: `data/baseline/scraper/baseline_{character_id}.json` 
- **Parser MD**: `data/baseline/parser/baseline_{character_id}.md`

## Path Dependencies

The archived scripts have hardcoded relative paths that expect to run from the project root directory:

- Parser looks for `./spells/` (enhanced spell markdown files)
- Parser looks for `./enhanced_dnd_scraper.py` (scraper script)

## Correct Usage

### Always Run From Project Root

```bash
# ✅ CORRECT - Run from project root directory
cd /path/to/CharacterScraper

# Run scraper
python3 archive/v5.2.0/enhanced_dnd_scraper_v5.2.0_original.py 144986992

# Run parser with explicit scraper path
python3 archive/v5.2.0/dnd_json_to_markdown_v5.2.0_original.py 144986992 output.md --scraper-path archive/v5.2.0/enhanced_dnd_scraper_v5.2.0_original.py

# Run parser without enhanced spells (faster)
python3 archive/v5.2.0/dnd_json_to_markdown_v5.2.0_original.py 144986992 output.md --scraper-path archive/v5.2.0/enhanced_dnd_scraper_v5.2.0_original.py --no-enhance-spells
```

### ❌ Incorrect Usage

```bash
# ❌ WRONG - Running from archive directory breaks paths
cd archive/v5.2.0
python3 enhanced_dnd_scraper_v5.2.0_original.py 144986992
# Error: ./spells not found, ./enhanced_dnd_scraper.py not found
```

## Testing Archive Scripts

To verify the archive scripts work correctly:

```bash
# Test scraper
python3 archive/v5.2.0/enhanced_dnd_scraper_v5.2.0_original.py 144986992 --output /tmp/test_archive_scraper.json

# Test parser
python3 archive/v5.2.0/dnd_json_to_markdown_v5.2.0_original.py 144986992 /tmp/test_archive_parser.md --scraper-path archive/v5.2.0/enhanced_dnd_scraper_v5.2.0_original.py
```

## Expected Warnings

When running the parser from the project root, you may see:

```
INFO: Enhanced spell data enabled, using folder: ./spells
INFO: Running scraper for character ID: 144986992
INFO: Scraper completed successfully
INFO: DnD UI Toolkit formatted character sheet for Vaelith Duskthorn written to /tmp/test_archive_parser.md
```

This is normal and indicates the scripts are working correctly.

## Troubleshooting

### "Spells folder not found" Warning
- **Cause**: Parser can't find `./spells` directory
- **Solution**: Ensure you're running from project root where `spells/` directory exists
- **Alternative**: Use `--no-enhance-spells` flag to disable spell enhancements

### "Scraper script not found" Error  
- **Cause**: Parser can't find the scraper script
- **Solution**: Use `--scraper-path archive/v5.2.0/enhanced_dnd_scraper_v5.2.0_original.py` argument

### Wrong Directory Error
- **Cause**: Running scripts from `archive/v5.2.0/` directory
- **Solution**: Always run from project root directory