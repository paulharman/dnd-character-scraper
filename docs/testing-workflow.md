# Testing Workflow Guide

This document outlines the comprehensive testing workflow for the D&D Beyond Character Scraper project. Follow this guide to run tests efficiently and avoid creating temporary test files.

## Overview

The project uses a structured testing approach with multiple test categories and easy-to-use commands. All tests are organized in the `tests/` directory with proper fixtures and factories.

## Test Structure

```
tests/
├── unit/                    # Unit tests for individual components
├── integration/             # Integration tests for full workflows
├── edge_cases/             # Edge case and boundary condition tests
├── calculators/            # Calculator-specific tests
├── fixtures/               # Test data fixtures and API responses
├── quick/                  # Quick test utilities and scenarios
├── factories.py            # Test data factories
└── run_all_tests.py        # Comprehensive test runner
```

## Quick Commands

### Run All Tests
```bash
# Run complete test suite with detailed output
python tests/run_all_tests.py

# Run with different verbosity levels
python tests/run_all_tests.py -v 0  # Quiet
python tests/run_all_tests.py -v 1  # Normal
python tests/run_all_tests.py -v 2  # Verbose (default)
```

### Run Specific Test Suites
```bash
# Run only unit tests
python tests/run_all_tests.py --suite unit

# Run only integration tests
python tests/run_all_tests.py --suite integration

# Run only edge case tests
python tests/run_all_tests.py --suite edge
```

### Quick Tests
```bash
# Run quick smoke tests
python -m tests.quick --smoke

# Run isolated component tests
python -m tests.quick --isolated

# Run scenario-based tests
python -m tests.quick --scenarios

# List available quick test options
python -m tests.quick --list
```

### Standard pytest Commands
```bash
# Run all tests with pytest
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/unit/calculators/test_enhanced_spell_processor.py

# Run tests matching pattern
pytest -k "spell"

# Run tests with verbose output
pytest -v
```

## Test Categories

### Unit Tests (`tests/unit/`)
- Test individual functions and classes in isolation
- Use mocked dependencies
- Fast execution
- High coverage of edge cases

**Example:**
```python
def test_ability_score_modifier():
    """Test ability score modifier calculation."""
    assert calculate_modifier(10) == 0
    assert calculate_modifier(15) == 2
    assert calculate_modifier(8) == -1
```

### Integration Tests (`tests/integration/`)
- Test complete workflows end-to-end
- Use real or realistic test data
- Verify component interactions
- Slower but comprehensive

**Example:**
```python
def test_character_processing_workflow():
    """Test complete character processing from raw data to JSON."""
    raw_data = TestDataFactory.create_spellcaster_raw_data()
    character = process_character(raw_data)
    assert character.spellcasting.is_spellcaster
    assert len(character.spells) > 0
```

### Edge Case Tests (`tests/edge_cases/`)
- Test boundary conditions
- Test error handling
- Test unusual character builds
- Test malformed data handling

**Example:**
```python
def test_extreme_ability_scores():
    """Test handling of extreme ability scores."""
    character = CharacterFactory.create_character()
    character.ability_scores.strength = 30  # Beyond normal limits
    # Should handle gracefully without errors
```

### Calculator Tests (`tests/calculators/`)
- Test specific calculator components
- Test mathematical accuracy
- Test D&D rule compliance
- Test performance with complex builds

## Test Data Management

### Using Test Factories

The `tests/factories.py` file provides factories for creating test data:

```python
from tests.factories import CharacterFactory, TestDataFactory

# Create a basic test character
character = CharacterFactory.create_basic_character()

# Create specific character types
fighter = CharacterFactory.create_fighter(level=10)
wizard = CharacterFactory.create_wizard(level=5)
rogue = CharacterFactory.create_rogue(level=8)

# Create multiclass character
multiclass = CharacterFactory.create_multiclass_character()

# Create raw API data
raw_data = TestDataFactory.create_basic_raw_data()
spellcaster_data = TestDataFactory.create_spellcaster_raw_data()
```

### Test Fixtures

Store reusable test data in `tests/fixtures/`:

```python
# tests/fixtures/characters.py
SAMPLE_FIGHTER = {
    "id": 12345,
    "name": "Test Fighter",
    "level": 5,
    # ... complete character data
}

# Use in tests
from tests.fixtures.characters import SAMPLE_FIGHTER

def test_fighter_processing():
    character = process_character(SAMPLE_FIGHTER)
    assert character.classes[0].name == "Fighter"
```

## Writing New Tests

### DO: Use the Formal Test Structure

```python
# tests/unit/calculators/test_new_feature.py
import pytest
from tests.factories import CharacterFactory
from src.calculators.new_feature import NewFeatureCalculator

class TestNewFeatureCalculator:
    """Test suite for NewFeatureCalculator."""
    
    def test_basic_calculation(self):
        """Test basic calculation functionality."""
        character = CharacterFactory.create_basic_character()
        calculator = NewFeatureCalculator()
        result = calculator.calculate(character)
        assert result > 0
    
    def test_edge_case_handling(self):
        """Test handling of edge cases."""
        character = CharacterFactory.create_character(level=0)
        calculator = NewFeatureCalculator()
        with pytest.raises(ValueError):
            calculator.calculate(character)
```

### DON'T: Create Temporary Test Files

❌ **Avoid creating files like:**
- `test_temp_feature.py` in root directory
- `quick_test_something.py` in parser/
- `validate_character_12345.py` in tools/
- Character-specific test scripts

✅ **Instead:**
- Add tests to appropriate `tests/` subdirectory
- Use test factories for character data
- Use parameterized tests for multiple scenarios
- Use fixtures for reusable test data

### Parameterized Tests

Use pytest parameterization for testing multiple scenarios:

```python
@pytest.mark.parametrize("level,expected_bonus", [
    (1, 2),
    (5, 3),
    (9, 4),
    (13, 5),
    (17, 6),
    (20, 6)
])
def test_proficiency_bonus_by_level(level, expected_bonus):
    """Test proficiency bonus calculation for different levels."""
    character = CharacterFactory.create_character(level=level)
    assert character.proficiency_bonus == expected_bonus
```

## Test Execution Workflow

### Development Workflow

1. **Write failing test first** (TDD approach)
2. **Run specific test** to verify it fails
3. **Implement feature** to make test pass
4. **Run full test suite** to ensure no regressions
5. **Commit changes** with tests included

```bash
# Step 1: Run specific test to see it fail
pytest tests/unit/calculators/test_new_feature.py::test_basic_calculation -v

# Step 2: Implement feature
# ... code changes ...

# Step 3: Run test again to see it pass
pytest tests/unit/calculators/test_new_feature.py::test_basic_calculation -v

# Step 4: Run full suite to check for regressions
python tests/run_all_tests.py

# Step 5: Commit
git add tests/unit/calculators/test_new_feature.py src/calculators/new_feature.py
git commit -m "Add new feature with tests"
```

### Pre-commit Workflow

Before committing changes:

```bash
# Run all tests
python tests/run_all_tests.py

# Run with coverage to ensure adequate test coverage
pytest --cov=src --cov-report=term-missing

# Run linting
flake8 src/ tests/

# Run type checking
mypy src/
```

### CI/CD Integration

The test suite is designed for CI/CD integration:

```bash
# CI command that returns proper exit codes
python tests/run_all_tests.py --output ci_results.json

# Check exit code
echo $?  # 0 = success, 1 = failures
```

## Performance Testing

### Quick Tests for Development

Use quick tests during development for fast feedback:

```bash
# Run smoke tests (< 30 seconds)
python -m tests.quick --smoke

# Run specific calculator tests
python -m tests.quick --calculator spell_processor

# Run specific scenario
python -m tests.quick --scenario multiclass_wizard
```

### Full Test Suite for Validation

Run the complete test suite before releases:

```bash
# Full suite with detailed reporting
python tests/run_all_tests.py -v 2 --output release_test_results.json
```

## Debugging Tests

### Running Individual Tests

```bash
# Run single test with maximum verbosity
pytest tests/unit/calculators/test_spell_processor.py::test_feat_spell_resolution -v -s

# Run with debugger
pytest tests/unit/calculators/test_spell_processor.py::test_feat_spell_resolution --pdb

# Run with print statements visible
pytest tests/unit/calculators/test_spell_processor.py::test_feat_spell_resolution -s
```

### Test Data Inspection

```python
# In test files, use factories to create consistent test data
def test_debug_character_data():
    """Debug test to inspect character data."""
    character = CharacterFactory.create_wizard(level=5)
    print(f"Character: {character.name}")
    print(f"Spells: {len(character.spells)}")
    print(f"Spell slots: {character.spellcasting.spell_slots}")
    # Add breakpoint for inspection
    import pdb; pdb.set_trace()
```

## Test Coverage

### Measuring Coverage

```bash
# Generate HTML coverage report
pytest --cov=src --cov-report=html

# View coverage report
open htmlcov/index.html  # macOS/Linux
start htmlcov/index.html  # Windows
```

### Coverage Goals

- **Unit tests**: 90%+ coverage for core logic
- **Integration tests**: Cover all major workflows
- **Edge cases**: Cover error conditions and boundary cases

## Common Testing Patterns

### Testing Calculations

```python
def test_armor_class_calculation():
    """Test AC calculation with various modifiers."""
    character = CharacterFactory.create_character()
    character.ability_scores.dexterity = 16  # +3 modifier
    
    # Test base AC
    ac_calculator = ArmorClassCalculator()
    base_ac = ac_calculator.calculate_base_ac(character)
    assert base_ac == 13  # 10 + 3 (Dex)
    
    # Test with armor
    character.equipment.append({"name": "Chain Mail", "ac_bonus": 5})
    armored_ac = ac_calculator.calculate_total_ac(character)
    assert armored_ac == 16  # 10 + 5 (armor) + 1 (max Dex for chain mail)
```

### Testing Error Handling

```python
def test_invalid_character_data_handling():
    """Test graceful handling of invalid character data."""
    invalid_data = {"id": None, "name": "", "level": -1}
    
    with pytest.raises(ValidationError) as exc_info:
        Character(**invalid_data)
    
    assert "level must be positive" in str(exc_info.value)
```

### Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_character_processing():
    """Test asynchronous character processing."""
    raw_data = TestDataFactory.create_basic_raw_data()
    
    processor = AsyncCharacterProcessor()
    character = await processor.process_character(raw_data)
    
    assert character.id == raw_data["id"]
    assert character.name == raw_data["name"]
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure `PYTHONPATH` includes project root
2. **Missing Dependencies**: Run `pip install -r requirements-dev.txt`
3. **Test Data Issues**: Use factories instead of hardcoded data
4. **Slow Tests**: Use quick tests for development, full suite for validation

### Getting Help

1. Check test output for specific error messages
2. Use `-v` flag for verbose output
3. Use `--pdb` flag to drop into debugger on failures
4. Check `test_results.json` for detailed failure information

## Best Practices Summary

### DO:
- ✅ Use the formal test structure in `tests/`
- ✅ Use test factories for creating test data
- ✅ Write tests before implementing features (TDD)
- ✅ Use descriptive test names and docstrings
- ✅ Test both success and failure cases
- ✅ Use parameterized tests for multiple scenarios
- ✅ Run tests before committing changes
- ✅ Maintain good test coverage

### DON'T:
- ❌ Create temporary test files outside `tests/`
- ❌ Use hardcoded character IDs or data
- ❌ Skip writing tests for new features
- ❌ Commit code without running tests
- ❌ Write tests that depend on external services
- ❌ Create character-specific test scripts
- ❌ Leave failing tests in the codebase

This workflow ensures consistent, maintainable, and efficient testing practices across the project.
</content>
</invoke>