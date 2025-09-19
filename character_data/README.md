# Character Data Directory

This directory contains character data organized by processing stage and module:

## Directory Structure

```
character_data/
├── scraper/           # Processed character data from D&D Beyond API  
│   └── raw/          # Unprocessed API responses (for debugging)
├── discord/          # Discord notification snapshots
├── parser/           # Generated Obsidian-compatible markdown sheets
│   └── archive/      # Historical parser outputs
└── change_logs/      # Character change tracking files
```

## Data Flow

1. **Scraper**: Fetches and processes character data from D&D Beyond API
2. **Parser**: Converts character data to Obsidian-compatible markdown  
3. **Discord**: Monitors changes and sends notifications
4. **Change Logs**: Track character changes over time

## File Retention

- **Scraper data**: Retained according to `config/discord.yaml` settings (default: 365 days)
- **Raw API data**: Kept for debugging purposes
- **Change logs**: Permanent retention for change history
- **Parser output**: Latest version plus archive of historical outputs

## Integration with Obsidian

The parser generates markdown files compatible with:
- **Obsidian**: Direct import into your vault
- **D&D UI Toolkit**: Enhanced character sheet formatting
- **Datacore**: Query and analyze character data across your vault

## Security Notes

- **No sensitive data**: Character sheets contain only public D&D Beyond information
- **Local storage**: All data remains on your local machine
- **Version control safe**: Generated files are safe to commit to Git repositories