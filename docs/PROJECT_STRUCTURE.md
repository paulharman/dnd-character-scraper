# D&D Character Scraper - Project Structure

This document outlines the organized project structure for the D&D Beyond character scraper system.

## 📁 Directory Structure

```
DnD/CharacterScraper/
├── 🎯 Core System
│   ├── src/                          # Core v6.0.0 modular architecture
│   │   ├── calculators/              # Character data calculators
│   │   ├── clients/                  # API client abstractions
│   │   ├── config/                   # Configuration management
│   │   ├── formatters/               # Output formatting (YAML, etc)
│   │   ├── interfaces/               # Abstract interfaces
│   │   ├── models/                   # Data models and schemas
│   │   ├── rules/                    # 2014/2024 rule management
│   │   ├── services/                 # High-level coordination services
│   │   ├── storage/                  # Multi-backend storage system
│   │   ├── utils/                    # Utility functions
│   │   └── validators/               # Data validation framework
│   │
│   ├── config/                       # YAML configuration files
│   ├── tests/                        # Comprehensive test suite
│   └── tools/                        # Development and analysis tools
│
├── 🤖 Scraper System
│   └── scraper/
│       └── enhanced_dnd_scraper.py   # Main v6.0.0 scraper
│
├── 📝 Parser System  
│   └── parser/
│       └── dnd_json_to_markdown.py   # JSON to markdown converter
│
├── 💬 Discord System
│   └── discord/
│       ├── services/                 # Discord notification services
│       │   ├── discord_service.py    # Discord webhook client
│       │   ├── change_detection_service.py  # Character change detection
│       │   └── notification_manager.py      # Notification coordination
│       ├── formatters/               # Discord message formatting
│       │   └── discord_formatter.py  # Rich embed formatters
│       ├── discord_monitor.py        # Main monitoring application
│       ├── setup_discord_monitor.py  # Interactive setup wizard
│       ├── quick_discord_test.py     # Quick test script
│       ├── discord_config.yml        # Configuration file
│       └── README.md                 # Discord system documentation
│
├── 📚 Data & Documentation
│   ├── data/                         # Test data and baselines
│   ├── docs/                         # Development documentation
│   ├── archive/                      # Archived v5.2.0 scripts
│   ├── test_outputs/                 # Test files and temporary outputs
│   ├── validation_output/            # Automated validation results
│   └── obsidian/                     # Obsidian integration components
│       ├── spells/                   # User-provided spell files (not included)
│       └── InventoryManager.jsx      # DataCore inventory component
│
└── 🚀 Launchers
    ├── run_discord_monitor.py        # Discord monitor launcher
    └── docs/
        └── PROJECT_STRUCTURE.md      # This file
```

## 🎯 Usage by System

### Core Character Processing
```bash
# Use the modular v6.0.0 system directly
python -m src.services.scraper_service --character-id 12345
```

### Character Scraping
```bash
# Scrape character data
python scraper/enhanced_dnd_scraper.py --character-id 12345
```

### Markdown Generation
```bash
# Convert JSON to markdown
python parser/dnd_json_to_markdown.py character_data.json
```

### Discord Monitoring
```bash
# Easy launcher (recommended)
python run_discord_monitor.py --test

# Direct execution
python discord/discord_monitor.py --config discord/discord_config.yml

# Interactive setup
python discord/setup_discord_monitor.py
```

## 🔧 Key Benefits of This Structure

### ✅ **Separation of Concerns**
- **Scraper**: Data acquisition from D&D Beyond
- **Parser**: Data transformation and formatting  
- **Discord**: Real-time monitoring and notifications
- **Core**: Shared business logic and infrastructure

### ✅ **Independent Development**
- Each system can be developed and tested independently
- Clear dependencies and interfaces
- Easier maintenance and debugging

### ✅ **Flexible Deployment**
- Use just the scraper for data collection
- Use parser alone for batch markdown generation
- Use Discord system for real-time monitoring
- Combine systems as needed

### ✅ **Clean Dependencies**
```
Discord System → Core System ← Parser System
                      ↑
               Scraper System
```

## 📋 Quick Start Guide

### 1. **Basic Character Scraping**
```bash
python scraper/enhanced_dnd_scraper.py --character-id YOUR_ID
python parser/dnd_json_to_markdown.py character_YOUR_ID.json
```

### 2. **Discord Monitoring Setup**
```bash
# Interactive setup
python discord/setup_discord_monitor.py

# Test webhook
python run_discord_monitor.py --test

# Start monitoring  
python run_discord_monitor.py
```

### 3. **Development Work**
```bash
# Run tests
python tests/run_all_tests.py

# Validate data
python tools/testing/validate_comprehensive.py
```

## 🔍 Finding Components

| I want to... | Look in... |
|--------------|------------|
| **Scrape character data** | `scraper/` |
| **Convert to markdown** | `parser/` |  
| **Monitor with Discord** | `discord/` |
| **Understand core logic** | `src/` |
| **Run tests** | `tests/` |
| **See examples** | `data/baseline/` |
| **Read documentation** | `docs/` |

This organization makes the project much more maintainable and easier to understand! 🎉