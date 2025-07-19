# Discord Module Test Suite

This document describes the comprehensive test suite created for the Discord module functionality, addressing the issues outlined in the Discord module fixes specification.

## Test Structure

### Unit Tests (`tests/unit/services/`)

#### 1. `test_discord_service.py`
- **Purpose**: Tests core Discord service functionality
- **Coverage**: 
  - Webhook URL validation and connectivity testing
  - Message sending (text and embeds)
  - Rate limit handling and error responses
  - Network error handling and timeouts
  - Security features (webhook URL masking)
  - Concurrent message sending

#### 2. `test_change_detection_service.py`
- **Purpose**: Tests change detection accuracy and D&D rule compliance
- **Coverage**:
  - Basic character info changes (level, experience, etc.)
  - Ability score change detection
  - Combat stat changes (AC, HP)
  - Character-agnostic detection (no hardcoded values)
  - Change priority assignment
  - Description accuracy

#### 3. `test_notification_manager.py`
- **Purpose**: Tests notification delivery and management
- **Coverage**:
  - Startup/shutdown notifications
  - Test notification system
  - Change filtering by priority and groups
  - Message formatting for single/multiple characters
  - Rate limiting logic
  - Error handling in notifications
  - Configuration validation

#### 4. `test_spell_detection_fixes.py` ⭐
- **Purpose**: **Addresses the main bug fix** - cantrip slot detection
- **Coverage**:
  - **Cantrip slot bug fix**: Ensures cantrips don't report "spell slots changed"
  - Proper distinction between cantrips known vs spell slots
  - D&D 5e rule compliance for different classes (Wizard, Sorcerer, Warlock)
  - Prevention of impossible spell changes
  - Character-agnostic spell detection
  - Accurate spell slot descriptions

#### 5. `test_change_detectors.py`
- **Purpose**: Tests individual detector classes
- **Coverage**:
  - BasicInfoDetector (level, name, experience changes)
  - AbilityScoreDetector (ability score increases/decreases)
  - SkillDetector (proficiency, expertise, bonus changes)
  - CombatDetector (weapons, resources, AC, HP)
  - SpellDetector (spell slots, spells learned/forgotten)

### Integration Tests (`tests/integration/`)

#### 1. `test_discord_integration.py`
- **Purpose**: End-to-end Discord workflow testing
- **Coverage**:
  - Discord monitor initialization and configuration
  - Webhook validation integration
  - Character scraping integration
  - Change detection integration
  - Party mode support
  - Error handling integration
  - Configuration security

### Quick Tests (`tests/quick/`)

#### 1. `test_discord.py`
- **Purpose**: Fast-running tests for development feedback
- **Coverage**:
  - Core Discord service functionality
  - Spell detection bug fix verification
  - Basic change detection
  - Error handling basics

## Test Runners

### 1. `tests/run_discord_tests.py`
- **Comprehensive Discord test runner**
- **Features**:
  - Multiple test categories (unit, integration, quick, spell)
  - Detailed reporting and summaries
  - Timeout handling and error recovery
  - Dependency checking
  - Verbose and quiet modes

### 2. Integration with main `test.py`
- **Added `--discord` flag** to main test runner
- **Easy access**: `python test.py --discord`
- **Fallback support** if dedicated runner fails

## Key Bug Fixes Tested

### 1. Cantrip Slot Detection Bug ⭐
**Problem**: System incorrectly reported "Level 0 spell slots changed from X to Y"
**Solution**: 
- Cantrips don't have spell slots in D&D 5e - they're cast at will
- Tests ensure cantrip changes are reported as "spells learned" not "slots changed"
- Proper distinction between cantrips known vs spell slots available

### 2. D&D Rule Compliance
- Tests verify spell detection follows actual D&D 5e rules
- Different spellcasting classes handled correctly (Wizard, Sorcerer, Warlock)
- Impossible changes are prevented or handled gracefully

### 3. Character-Agnostic Detection
- No hardcoded character IDs, names, or specific values
- Works for any character build or level
- Maintains accuracy across different character types

## Running the Tests

### Quick Discord Tests
```bash
python test.py --discord
```

### Specific Test Categories
```bash
# Run dedicated Discord test runner
python tests/run_discord_tests.py all

# Quick tests only
python tests/run_discord_tests.py quick

# Unit tests only  
python tests/run_discord_tests.py unit

# Integration tests only
python tests/run_discord_tests.py integration

# Spell detection tests only
python tests/run_discord_tests.py spell
```

### Individual Test Files
```bash
# Test the main bug fix
python -m pytest tests/unit/services/test_spell_detection_fixes.py -v

# Test Discord service
python -m pytest tests/unit/services/test_discord_service.py -v

# Test change detection
python -m pytest tests/unit/services/test_change_detection_service.py -v
```

## Test Coverage

The test suite provides comprehensive coverage of:

- ✅ **Webhook validation and connectivity**
- ✅ **Message sending and formatting**
- ✅ **Rate limiting and error handling**
- ✅ **Change detection accuracy**
- ✅ **Spell slot detection bug fix** (main issue)
- ✅ **D&D rule compliance**
- ✅ **Configuration security**
- ✅ **Integration workflows**
- ✅ **Error recovery scenarios**

## Benefits

1. **Addresses Spec Requirements**: All tasks from the Discord module fixes specification
2. **Prevents Regressions**: Comprehensive test coverage prevents future bugs
3. **Development Confidence**: Fast feedback during development
4. **Documentation**: Tests serve as living documentation of expected behavior
5. **Easy Debugging**: Detailed test failures help identify issues quickly

## Next Steps

1. **Run the tests** to verify current Discord module functionality
2. **Fix any failing tests** to address existing issues
3. **Use TDD approach** for future Discord module enhancements
4. **Integrate with CI/CD** for automated testing

The test suite is ready to use and will help ensure the Discord module works reliably and follows D&D 5e rules correctly!