---
inclusion: always
---

# Testing Strategy and Guidelines

## Core Testing Principles

### Test-Driven Development (TDD)
- **Write tests first** before implementing features
- **Red-Green-Refactor** cycle: failing test → implementation → refactor
- **One test at a time** - focus on single functionality
- **Descriptive test names** that explain the expected behavior

### Test Organization
- **Use formal test structure** in `tests/` directory only
- **Never create temporary test files** outside the test suite
- **Use standardized fixtures** from `tests/fixtures/characters.py`
- **Leverage test factories** from `tests/factories.py`

## Test Suite Structure

```
tests/
├── unit/                    # Unit tests - isolated component testing
├── calculators/             # Calculator-specific tests
├── integration/             # End-to-end workflow tests
├── edge_cases/             # Boundary conditions and error handling
├── fixtures/               # Standardized test data
├── quick/                  # Quick test utilities
├── factories.py            # Test data factories
└── run_all_tests.py        # Comprehensive test runner
```

## When to Create New Tests

### For New Features
1. **Create unit tests** for individual functions/classes
2. **Create integration tests** for complete workflows
3. **Create edge case tests** for boundary conditions
4. **Update fixtures** if new character types are needed

### For Bug Fixes
1. **Write failing test** that reproduces the bug
2. **Fix the bug** to make the test pass
3. **Add regression test** to prevent future occurrences

### For Refactoring
1. **Ensure existing tests pass** before refactoring
2. **Add tests for new interfaces** if structure changes
3. **Update test fixtures** if data models change

## Test Categories and Requirements

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions and classes in isolation
- **Requirements**: 
  - Use mocked dependencies
  - Fast execution (< 1 second per test)
  - High coverage of edge cases
  - No external dependencies

**Example Structure:**
```python
# tests/unit/calculators/test_new_calculator.py
import pytest
from tests.factories import CharacterFactory
from src.calculators.new_calculator import NewCalculator

class TestNewCalculator:
    def test_basic_calculation(self):
        character = CharacterFactory.create_basic_character()
        calculator = NewCalculator()
        result = calculator.calculate(character)
        assert result > 0
    
    def test_edge_case_handling(self):
        character = CharacterFactory.create_character(level=0)
        calculator = NewCalculator()
        with pytest.raises(ValueError):
            calculator.calculate(character)
```

### Calculator Tests (`tests/calculators/`)
- **Purpose**: Test D&D calculation accuracy and rule compliance
- **Requirements**:
  - Test mathematical accuracy
  - Validate D&D rule compliance
  - Test complex character builds
  - Performance testing for complex scenarios

### Integration Tests (`tests/integration/`)
- **Purpose**: Test complete workflows end-to-end
- **Requirements**:
  - Use realistic test data
  - Test component interactions
  - Verify data flow through system
  - Test error propagation

### Edge Case Tests (`tests/edge_cases/`)
- **Purpose**: Test boundary conditions and error handling
- **Requirements**:
  - Test extreme values (level 0, level 20, ability scores 1-30)
  - Test malformed data handling
  - Test unusual character builds
  - Test system limits

## Test Data Management

### Using Test Fixtures
```python
from tests.fixtures.characters import get_character_fixture

# Get standardized test character
wizard = get_character_fixture("WIZARD_SPELLCASTER")
fighter = get_character_fixture("BASIC_FIGHTER")
multiclass = get_character_fixture("MULTICLASS_FIGHTER_WIZARD")
```

### Available Character Fixtures
- `BASIC_FIGHTER` - Simple fighter for basic testing
- `WIZARD_SPELLCASTER` - Full spellcaster for spell testing
- `MULTICLASS_FIGHTER_WIZARD` - Complex multiclass scenarios
- `ROGUE_WITH_EXPERTISE` - Skill and expertise testing
- `EDGE_CASE_CHARACTER` - Extreme values and boundary testing

### Creating New Fixtures
When adding new character types:
1. Add to `tests/fixtures/characters.py`
2. Include validation expectations
3. Update `ValidationFixtures` with expected values
4. Document the fixture purpose

## Test Execution Commands

### Development Workflow
```bash
# Quick feedback during development
python test.py --quick

# Test specific functionality
python test.py --spell
python test.py --calculator

# Test specific file
python test.py --file tests/unit/calculators/test_spell_processor.py
```

### Pre-commit Testing
```bash
# Full test suite
python test.py

# With coverage
python test.py --coverage

# Specific test suites
python test.py --unit
python test.py --integration
```

## Test Quality Standards

### Coverage Requirements
- **Unit tests**: 90%+ coverage for core logic
- **Integration tests**: Cover all major workflows
- **Edge cases**: Cover error conditions and boundary cases
- **Overall**: Maintain 80%+ total coverage

### Test Naming Conventions
```python
def test_should_calculate_correct_armor_class_when_wearing_chain_mail():
    """Test AC calculation with chain mail armor."""
    # Test implementation

def test_should_raise_error_when_character_level_is_zero():
    """Test error handling for invalid character level."""
    # Test implementation
```

### Test Documentation
- **Docstrings** for all test classes and methods
- **Comments** explaining complex test logic
- **Examples** in steering documentation
- **README** files for test directories

## Prohibited Practices

### ❌ DON'T:
- Create temporary test files outside `tests/`
- Use hardcoded character IDs or data
- Skip writing tests for new features
- Commit code without running tests
- Write tests that depend on external services
- Create character-specific test scripts
- Leave failing tests in the codebase

### ✅ DO:
- Use the formal test structure in `tests/`
- Use test factories for creating test data
- Write tests before implementing features (TDD)
- Use descriptive test names and docstrings
- Test both success and failure cases
- Use parameterized tests for multiple scenarios
- Run tests before committing changes
- Maintain good test coverage

## Integration with Development Workflow

### Feature Development Process
1. **Write failing tests** for the new feature
2. **Implement minimum code** to make tests pass
3. **Refactor** while keeping tests green
4. **Add edge case tests** for robustness
5. **Update documentation** and examples
6. **Run full test suite** before committing

### Bug Fix Process
1. **Write test that reproduces** the bug
2. **Verify test fails** with current code
3. **Fix the bug** to make test pass
4. **Add regression test** if needed
5. **Run related test suites** to ensure no regressions

### Refactoring Process
1. **Ensure all tests pass** before starting
2. **Refactor in small steps** keeping tests green
3. **Update tests** if interfaces change
4. **Add new tests** for new functionality
5. **Verify full test suite** still passes

## Performance Considerations

### Test Execution Speed
- **Unit tests**: < 1 second each
- **Integration tests**: < 10 seconds each
- **Full test suite**: < 5 minutes
- **Quick tests**: < 30 seconds total

### Test Data Efficiency
- **Reuse fixtures** instead of creating new data
- **Mock external dependencies** in unit tests
- **Use minimal data** that still validates functionality
- **Cache expensive setup** when possible

## Continuous Integration

### CI/CD Requirements
```bash
# CI command that returns proper exit codes
python tests/run_all_tests.py --output ci_results.json

# Coverage reporting
python test.py --coverage --quiet

# Specific test categories for different CI stages
python test.py --quick      # Fast feedback
python test.py --unit       # Unit test stage
python test.py --integration # Integration test stage
```

### Quality Gates
- **All tests must pass** before merge
- **Coverage must not decrease** below threshold
- **No new test warnings** or errors
- **Performance tests** must meet benchmarks

## Documentation Requirements

### Test Documentation
- **Update test README** when adding new test categories
- **Document new fixtures** and their purpose
- **Update testing workflow** documentation
- **Provide examples** for new testing patterns

### Code Documentation
- **Docstrings** for all test classes and methods
- **Inline comments** for complex test logic
- **Type hints** for test functions and fixtures
- **Examples** in module docstrings

This testing strategy ensures consistent, maintainable, and efficient testing practices across the entire project.