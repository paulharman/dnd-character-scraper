# Scraper Module

The scraper module handles character data extraction and calculation from the D&D Beyond API with comprehensive rule support and advanced calculation logic.

## 🏗️ Architecture

```
scraper/
├── enhanced_dnd_scraper.py    # Main entry point script
└── core/                      # Core scraper components
    ├── calculators/           # D&D rule calculations & coordinators
    ├── clients/              # D&D Beyond API integration
    ├── interfaces/           # Scraper-specific interfaces
    ├── rules/                # Game rules & versioning
    ├── services/             # Scraper services
    ├── utils/                # Utilities (HTML cleaning, etc.)
    └── validators/           # Data validation
```

## ⚡ Key Features

- **Enhanced Calculators v2.0.0**: Advanced calculation system with 2024 rule support
- **Coordinator Architecture**: Modular calculation coordinators (abilities, combat, spellcasting, etc.)
- **Rule Version Detection**: Automatic 2014 vs 2024 rule detection and application
- **Rate Limiting**: Built-in 30-second API delay compliance
- **Comprehensive Fallback**: Enhanced calculators with legacy calculation fallback
- **Error Recovery**: Robust error handling and retry logic
- **Data Validation**: Complete character data validation and cleaning

## 🚀 Usage

### Command Line
```bash
# Basic character scraping
python scraper/enhanced_dnd_scraper.py CHARACTER_ID

# With verbose output
python scraper/enhanced_dnd_scraper.py CHARACTER_ID --verbose

# Force specific rule version
python scraper/enhanced_dnd_scraper.py CHARACTER_ID --force-2024

# Batch processing
python scraper/enhanced_dnd_scraper.py --batch characters.txt
```

### Programmatic Usage
```python
from scraper.core.clients.factory import ClientFactory
from scraper.core.calculators.character_calculator import CharacterCalculator

# Create client
client = ClientFactory.create_client()

# Get character data
raw_data = client.get_character(character_id)

# Calculate enhanced data
calculator = CharacterCalculator()
character_data = calculator.calculate_character(raw_data)
```

## 🔧 Configuration

Configuration is handled via `config/scraper.yaml`:

```yaml
api:
  timeout: 30                    # Request timeout
  max_retries: 3                # Retry attempts
  retry_delay: 30               # Delay between retries

rate_limit:
  delay_between_requests: 30    # Required API delay
```

## 📊 Calculation System

### Enhanced Calculators
- **Abilities Calculator**: Ability scores, modifiers, saving throws
- **Combat Calculator**: AC, HP, attacks, damage
- **Spellcasting Calculator**: Spell save DC, attack bonus, slots
- **Proficiency Calculator**: Skills, proficiencies, expertise
- **Equipment Calculator**: Encumbrance, magical items

### Coordinator Pattern
Each calculation area has a dedicated coordinator that:
- Manages enhanced calculator integration
- Provides comprehensive fallback logic
- Handles data transformation
- Ensures calculation consistency

## 🛡️ Error Handling

The scraper includes comprehensive error handling:
- **Rate Limit Protection**: Automatic retry with proper delays
- **Private Character Support**: Session cookie authentication
- **Data Validation**: Input/output validation at every step
- **Graceful Degradation**: Fallback calculations when enhanced logic fails
- **Detailed Logging**: Comprehensive error reporting and debugging

## 🔌 API Integration

### D&D Beyond API Client
- **Authentication**: Session cookie support for private characters
- **Rate Limiting**: Enforces required 30-second delays
- **Error Recovery**: Handles API errors, timeouts, and network issues
- **Response Validation**: Validates API responses before processing

### Data Processing Pipeline
1. **Fetch**: Get raw character data from D&D Beyond API
2. **Transform**: Convert API data to internal format
3. **Calculate**: Apply enhanced calculations with coordinators
4. **Validate**: Ensure output data integrity
5. **Save**: Store processed data with timestamps

## 🧪 Testing

Test the scraper with a character:
```bash
# Test character scraping
python scraper/enhanced_dnd_scraper.py CHARACTER_ID --validate
```

## 🔍 Debugging

Enable debug mode for detailed logging:
```bash
# Debug mode
python scraper/enhanced_dnd_scraper.py CHARACTER_ID --verbose

# Or via configuration
# config/main.yaml: debug: true
```

## 📁 Output

Processed character data is saved to:
- **Processed Data**: `character_data/scraper/character_{ID}_{timestamp}.json`
- **Raw API Data**: `character_data/scraper/raw/character_{ID}_{timestamp}_raw.json`

## 🔗 Integration

The scraper integrates seamlessly with other modules:
- **Parser**: Automatically called by parser for fresh data
- **Discord**: Provides data for change detection
- **Shared**: Uses shared models and configuration

## ⚠️ Important Notes

- **Rate Limiting**: Never modify the 30-second API delay - it's required by D&D Beyond
- **Private Characters**: Require session cookies for access
- **Rule Detection**: Automatic 2014/2024 detection can be overridden with flags
- **Data Size**: Character files are ~200KB each - monitor storage usage