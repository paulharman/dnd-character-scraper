# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a D&D Beyond character scraper that extracts comprehensive character data from D&D Beyond's API with production-ready support for both 2014 and 2024 rules, container inventory tracking, and advanced character processing.

## Project Status: v6.0.0 Production Ready ✅

- **Current System**: Production-ready v6.0.0 with all phases completed (0-5)
- **Main Scripts**: `scraper/enhanced_dnd_scraper.py` and `parser/dnd_json_to_markdown.py`
- **Architecture**: Fully implemented modular system in `src/` with 15+ specialized calculators
- **Archive Scripts**: Original v5.2.0 scripts preserved in `archive/v5.2.0/` (SHA256 verified)
- **Testing**: Comprehensive test suite with 50+ tests, all critical bugs resolved
- **Status**: Production ready, actively maintained, all known issues resolved

## Development Practices

- **Testing Strategy**: Use the existing test scripts for testing. If a test script does not do what you need it to, then modify it rather than creating temporary scripts.

## Directory Structure:
- `enhanced_dnd_scraper.py`: Main v6.0.0 scraper script with modular architecture
- `dnd_json_to_markdown.py`: Enhanced markdown generator with v6.0.0 integration
- `archive/v5.2.0/`: Original v5.2.0 scripts (preserved for compatibility)
- `src/`: Complete v6.0.0 modular architecture
  - `calculators/`: 15+ specialized calculators (ability scores, AC, HP, spells, containers, etc.)
  - `clients/`: API client abstraction with mock support
  - `config/`: Environment-aware configuration management
  - `models/`: Pydantic data models with validation
  - `rules/`: 2014/2024 rule version management
  - `storage/`: Multiple storage backend support (JSON, SQLite, PostgreSQL)
  - `validators/`: Comprehensive validation framework
  - `formatters/`: Output formatting (YAML, etc.)
  - `services/`: High-level service coordination
- `tests/`: Comprehensive test suite (unit, edge cases, integration)
- `config/`: YAML configuration files for all environments
- `data/baseline/`: Complete validation data for 13 test characters
- `obsidian/spells/`: User-provided spell markdown files (not included - copyright)
- `docs/`: Development documentation and guides

[Rest of the file remains unchanged]