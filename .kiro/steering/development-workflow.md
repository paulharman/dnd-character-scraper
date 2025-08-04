---
inclusion: always
---

# Development Workflow and Best Practices

## Feature Development Process

### 1. Start New Feature
```bash
# Check current project state
python test.py --setup-check

# Run quick tests to ensure clean starting point
python test.py --quick
```

### Enhanced Change Detection Development
When working on change detection features:

```bash
# Test individual detectors
python test.py --pattern "test_*_detector"

# Test causation analysis
python test.py --pattern "test_causation"

# Test change logging
python test.py --pattern "test_change_log"

# Test Discord integration
python test.py --pattern "test_discord_formatter"
```

### 2. Test-Driven Development
```bash
# Write failing test first
python test.py --file tests/unit/new_feature/test_my_feature.py

# Implement feature to make test pass
# ... code implementation ...

# Run specific tests during development
python test.py --pattern "my_feature"
```

### 3. Development Testing
```bash
# Quick feedback during development
python test.py --quick

# Test specific functionality
python test.py --spell          # For spell-related features
python test.py --calculator     # For calculation features
python test.py --integration    # For workflow features
python test.py --change-detection # For enhanced change detection features
```

### 4. Pre-commit Validation
```bash
# Run full test suite
python test.py

# Generate coverage report
python test.py --coverage-html

# Check test environment
python test.py --setup-check
```

### 5. Feature Completion Cleanup
```bash
# Run comprehensive cleanup
python .kiro/hooks/feature-completion-cleanup.py

# This will:
# - Remove temporary files
# - Validate test suite
# - Update documentation
# - Run quality checks
# - Validate project structure
```

## Testing Strategy

### Test Categories
- **Unit Tests** (`tests/unit/`) - Individual component testing
- **Calculator Tests** (`tests/calculators/`) - D&D calculation accuracy
- **Integration Tests** (`tests/integration/`) - End-to-end workflows
- **Edge Case Tests** (`tests/edge_cases/`) - Boundary conditions

### Test Data Management
```python
# Use standardized fixtures
from tests.fixtures.characters import get_character_fixture

wizard = get_character_fixture("WIZARD_SPELLCASTER")
fighter = get_character_fixture("BASIC_FIGHTER")

# Use test factories for custom data
from tests.factories import CharacterFactory

character = CharacterFactory.create_wizard(level=10)
```

### Test Organization Rules
- ✅ **DO**: Use formal test structure in `tests/`
- ✅ **DO**: Use test fixtures and factories
- ✅ **DO**: Write descriptive test names
- ❌ **DON'T**: Create temporary test files outside `tests/`
- ❌ **DON'T**: Use hardcoded character data
- ❌ **DON'T**: Skip writing tests for new features

## Code Quality Standards

### Testing Requirements
- **Unit Tests**: 90%+ coverage for core logic
- **Integration Tests**: Cover all major workflows
- **Edge Cases**: Cover error conditions
- **Overall Coverage**: Maintain 80%+ total coverage

### Documentation Requirements
- **Docstrings** for all classes and methods
- **Type hints** throughout codebase
- **README updates** for new features
- **Configuration documentation** for new settings

### Code Style
- **Black** formatting for Python code
- **flake8** linting compliance
- **mypy** type checking
- **Descriptive variable names** and function names

## Project Structure Maintenance

### Required Directories
```
├── src/                   # Core application code
├── tests/                 # Formal test suite
│   ├── unit/             # Unit tests
│   ├── calculators/      # Calculator tests
│   ├── integration/      # Integration tests
│   ├── edge_cases/       # Edge case tests
│   ├── fixtures/         # Test data fixtures
│   └── quick/            # Quick test utilities
├── config/               # Configuration files
├── docs/                 # Documentation
└── .kiro/                # Kiro IDE configuration
    ├── steering/         # Agent steering files
    └── hooks/            # Agent hooks
```

### File Organization
- **No temporary files** in root directory
- **No character-specific scripts** outside tests
- **No debug files** committed to repository
- **Proper imports** and module structure

## Agent Hook Usage

### Feature Completion Hook
**When to use:**
- After completing a feature implementation
- Before creating a pull request
- After major refactoring work
- Before release preparation

**What it does:**
- Removes temporary files and cache
- Validates test suite passes
- Updates documentation
- Runs quality checks
- Validates project structure

**How to use:**
```bash
# Manual execution
python .kiro/hooks/feature-completion-cleanup.py

# Through Kiro IDE
# Command Palette → "Run Agent Hook" → "Feature Completion Cleanup"
```

## Common Development Commands

### Quick Reference
```bash
# Development Testing
python test.py --quick            # Fast feedback
python test.py --spell            # Spell features
python test.py --calculator       # Calculator features

# Comprehensive Testing
python test.py                    # All tests
python test.py --coverage         # With coverage
python test.py --integration      # Integration only

# Utilities
python test.py --list             # Show all commands
python test.py --setup-check      # Verify environment

# Feature Completion
python .kiro/hooks/feature-completion-cleanup.py
```

### Debugging Tests
```bash
# Run specific test with debugging
python test.py --file tests/unit/test_my_feature.py --debug

# Run with verbose output
python test.py --spell --verbose

# Run with pattern matching
python test.py -k "spell and not integration"
```

## Error Handling and Troubleshooting

### Common Issues
1. **Import Errors**: Ensure `PYTHONPATH` includes project root
2. **Missing Dependencies**: Run `pip install -r requirements-dev.txt`
3. **Test Data Issues**: Use fixtures instead of hardcoded data
4. **Slow Tests**: Use quick tests for development feedback

### Getting Help
1. Check test output for specific error messages
2. Use `--verbose` flag for detailed output
3. Use `--debug` flag to drop into debugger
4. Check `cleanup_report.json` for cleanup details

## Continuous Integration

### Pre-commit Checklist
- [ ] All tests pass (`python test.py`)
- [ ] Coverage maintained (`python test.py --coverage`)
- [ ] No temporary files (`python .kiro/hooks/feature-completion-cleanup.py`)
- [ ] Documentation updated
- [ ] Code formatted and linted

### Quality Gates
- **All tests must pass** before merge
- **Coverage must not decrease** below 80%
- **No temporary files** in repository
- **Documentation must be current**

## Enhanced Change Detection Development Patterns

### Working with Detectors
- **Single Responsibility**: Each detector handles one type of change (feats, spells, etc.)
- **Consistent Interface**: All detectors extend `BaseEnhancedDetector`
- **Field Path Conventions**: Use `character.{category}.{field}` format
- **Priority Classification**: Use HIGH/MEDIUM/LOW based on user impact

### Change Logging Integration
- **Automatic Logging**: Changes are automatically logged when detected
- **Causation Analysis**: Include attribution for why changes occurred
- **Error Handling**: Graceful degradation if logging fails
- **Performance**: Async logging to avoid blocking notifications

### Configuration Management
- **Field Patterns**: Use `config/discord.yaml` field patterns for priority overrides
- **Detector Settings**: Configure individual detectors through enhanced config
- **Priority Overrides**: Override default priorities for specific field paths

This workflow ensures consistent, high-quality development practices across the entire project.