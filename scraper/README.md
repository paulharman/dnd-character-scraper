# D&D Beyond Character Scraper

Enhanced character data scraper for D&D Beyond with comprehensive data extraction and processing.

## 🚀 Features

- **Multi-Rule Support**: 2014 and 2024 D&D rules
- **Comprehensive Data**: Complete character information including inventory, spells, features
- **API Integration**: Direct D&D Beyond API access
- **Modular Architecture**: Integration with v6.0.0 system
- **Caching Support**: Efficient data retrieval
- **Error Handling**: Robust error recovery and logging

## 📋 Usage

### Basic Character Scraping
```bash
# From project root
python scraper/enhanced_dnd_scraper.py --character-id 12345

# With session cookie for private characters
python scraper/enhanced_dnd_scraper.py --character-id 12345 --session-cookie "your_cookie"

# Output to specific file
python scraper/enhanced_dnd_scraper.py --character-id 12345 --output character_data.json
```

### Programmatic Usage
```python
from scraper.enhanced_dnd_scraper import DnDBeyondScraper

# Initialize scraper
scraper = DnDBeyondScraper(
    session_cookie="optional_session_cookie",
    enable_caching=True,
    rate_limit=True
)

# Scrape character
character_data = await scraper.scrape_character(12345)
```

## ⚙️ Configuration

The scraper integrates with the main project's configuration system and supports:

- **API Rate Limiting**: Respects D&D Beyond's rate limits
- **Session Management**: Handle private character access
- **Caching**: Store API responses for efficiency  
- **Logging**: Comprehensive logging for debugging
- **Error Recovery**: Retry logic for failed requests

## 🔧 Dependencies

The scraper uses the core v6.0.0 architecture:
- `src/clients/` - API client abstractions
- `src/models/` - Character data models  
- `src/config/` - Configuration management
- `src/storage/` - Data persistence

## 📊 Output Format

The scraper produces comprehensive JSON character data including:

```json
{
  "basic_info": {
    "name": "Character Name",
    "level": 5,
    "classes": [...],
    "race": "...",
    "background": "..."
  },
  "ability_scores": {...},
  "spells": {...},
  "inventory": [...],
  "features": [...],
  "meta": {
    "character_id": 12345,
    "rule_version": "2024",
    "processed_date": "...",
    "scraper_version": "6.0.0"
  }
}
```

## 🚨 Troubleshooting

**"Character not found"**
- Verify character ID is correct
- Check if character is public or requires session cookie
- Ensure D&D Beyond API is accessible

**"Rate limited"**
- Enable rate limiting: `--rate-limit`
- Increase delays between requests
- Check for multiple scraper instances

**"Session expired"**
- Update session cookie from browser
- Verify cookie is still valid
- Check D&D Beyond login status

For more help, see the main project documentation.