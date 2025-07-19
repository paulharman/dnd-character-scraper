# Technology Stack

## Core Technologies

- **Python 3.8+**: Primary programming language
- **Pydantic v2**: Data validation and serialization with type hints
- **aiohttp/requests**: HTTP client libraries for API interactions
- **BeautifulSoup4**: HTML parsing and cleaning
- **PyYAML**: Configuration file management
- **asyncio**: Asynchronous programming support

## Database & Storage

- **SQLite**: Default local database storage
- **PostgreSQL**: Optional production database backend
- **JSON Files**: Alternative file-based storage
- **aiosqlite/asyncpg**: Async database drivers

## Development Tools

- **pytest**: Testing framework with async support
- **black**: Code formatting
- **flake8**: Linting
- **mypy**: Static type checking
- **pre-commit**: Git hooks for code quality
- **bandit**: Security analysis

## Common Commands

### Development Setup
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running the Application
```bash
# Scrape character data
python scraper/enhanced_dnd_scraper.py <character_id>

# Generate markdown character sheet
python parser/dnd_json_to_markdown.py <character_id>

# Start Discord monitoring
python discord/discord_monitor.py --config config/discord.yaml
```

### Testing
```bash
# Easy test commands (recommended)
python test.py                    # Run all tests
python test.py --quick            # Quick smoke tests
python test.py --spell            # Spell-related tests
python test.py --coverage         # Run with coverage

# Specific test suites
python test.py --unit             # Unit tests only
python test.py --calculator       # Calculator tests only
python test.py --integration      # Integration tests only

# Traditional pytest commands
pytest                            # Run all tests
pytest --cov=src --cov-report=html  # Generate HTML coverage
python tests/run_all_tests.py    # Comprehensive test runner

# Test environment validation
python test.py --setup-check      # Verify test setup
python test.py --list             # Show available commands
```

### Code Quality
```bash
# Format code
black .

# Lint code
flake8 src/ tests/

# Type checking
mypy src/

# Security scan
bandit -r src/
```

## Architecture Patterns

- **Factory Pattern**: Used for storage backends and service creation
- **Strategy Pattern**: Different storage implementations (JSON, SQLite, PostgreSQL)
- **Observer Pattern**: Change detection and notification system
- **Pydantic Models**: Extensive use of data validation and serialization
- **Async/Await**: Asynchronous operations for I/O bound tasks