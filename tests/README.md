# Testing Guide

Quick reference for running tests in the D&D Beyond Character Scraper project.

## Quick Commands

```bash
# Run all tests
python test.py

# Run quick smoke tests (fast feedback)
python test.py --quick

# Run specific test suites
python test.py --unit           # Unit tests only
python test.py --calculator     # Calculator tests only
python test.py --integration    # Integration tests only
python test.py --spell          # All spell-related tests

# Run with coverage
python test.py --coverage
python test.py --coverage-html  # Generate HTML report

# Run specific test file
python test.py --file tests/unit/calculators/test_spell_processor.py

# Run tests matching pattern
python test.py -k "spell and not integration"
```

## Test Structure

- `tests/unit/` - Unit tests for individual components
- `tests/calculators/` - Calculator-specific tests
- `tests/integration/` - End-to-end workflow tests
- `tests/edge_cases/` - Boundary condition tests
- `tests/fixtures/` - Test data fixtures
- `tests/quick/` - Quick test utilities

## Using Test Fixtures

```python
from tests.fixtures.characters import get_character_fixture

# Get standardized test character
wizard = get_character_fixture("WIZARD_SPELLCASTER")
fighter = get_character_fixture("BASIC_FIGHTER")
```

## Writing New Tests

✅ **DO:**
- Add tests to appropriate `tests/` subdirectory
- Use test fixtures from `tests/fixtures/characters.py`
- Use test factories from `tests/factories.py`
- Write descriptive test names and docstrings

❌ **DON'T:**
- Create temporary test files outside `tests/`
- Use hardcoded character IDs or data
- Create character-specific test scripts

## More Information

See [docs/testing-workflow.md](../docs/testing-workflow.md) for complete testing documentation.