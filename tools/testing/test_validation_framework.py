#!/usr/bin/env python3
"""
Test the v6.0.0 Validation Framework

Demonstrates the comprehensive validation system including:
- Character data validation
- Calculation validation
- Regression testing against v5.2.0
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from src.validators import CharacterValidator, CalculationValidator, RegressionValidator
from src.validators.base import ValidationResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_test_data(character_id: int) -> Dict[str, Any]:
    """Load test character data."""
    # Create test data in v6.0.0 format
    # (v5.2.0 baseline has different structure)
    return {
        "character_id": character_id,
        "name": "Test Character",
        "level": 10,
        "classes": [{"name": "Fighter", "level": 10}],
        "ability_scores": {
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 13,
            "charisma": 12
        },
        "ability_modifiers": {
            "strength": 3,
            "dexterity": 2,
            "constitution": 2,
            "intelligence": 0,
            "wisdom": 1,
            "charisma": 1
        },
        "max_hp": 84,
        "armor_class": 16,
        "proficiency_bonus": 4,
        "initiative_bonus": 2
    }


def test_character_validation():
    """Test character data validation."""
    logger.info("=" * 60)
    logger.info("Testing Character Validation")
    logger.info("=" * 60)
    
    validator = CharacterValidator()
    
    # Test with minimal data
    test_data = load_test_data(145081718)
    
    # Validate structure and integrity
    result = validator.validate(test_data)
    print("\nCharacter Validation Result:")
    print(result.get_summary())
    
    # Test with validation file
    validation_file = Path("validation_data/145081718_validation.json")
    if validation_file.exists():
        logger.info("\nValidating against validation file...")
        result_with_file = validator.validate(test_data, validation_file)
        print("\nValidation with Comparison:")
        print(result_with_file.get_summary())
        
        # Show some field comparisons
        if result_with_file.field_comparisons:
            print("\nField Comparisons:")
            for field, comparison in list(result_with_file.field_comparisons.items())[:10]:
                match_symbol = "✓" if comparison['match'] else "✗"
                print(f"  {match_symbol} {field}: {comparison['actual']} vs {comparison['expected']}")


def test_calculation_validation():
    """Test calculation validation."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Calculation Validation")
    logger.info("=" * 60)
    
    validator = CalculationValidator()
    
    # Test with character data
    test_data = load_test_data(145081718)
    
    # Add some calculations to validate
    test_data.update({
        "ac_breakdown": {
            "base": 10,
            "dexterity_bonus": 2,
            "armor_bonus": 4,
            "calculation_method": "armor"
        },
        "hit_point_breakdown": {
            "base_hp": 64,  # 10d10 average
            "con_bonus": 20,  # 2 * 10 levels
            "other_bonuses": 0
        },
        "spellcasting": {
            "is_spellcaster": False
        }
    })
    
    result = validator.validate(test_data)
    print("\nCalculation Validation Result:")
    print(result.get_summary())


def test_regression_validation():
    """Test regression validation against v5.2.0."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Regression Validation")
    logger.info("=" * 60)
    
    validator = RegressionValidator()
    
    # Test with a character that has baseline data
    character_id = 145081718
    baseline_file = Path(f"data/baseline/scraper/baseline_{character_id}.json")
    
    if not baseline_file.exists():
        logger.warning(f"No baseline file found for character {character_id}")
        return
    
    # Load v5.2.0 baseline
    with open(baseline_file, 'r', encoding='utf-8') as f:
        v5_data = json.load(f)
    
    # Simulate v6.0.0 data (would normally come from new scraper)
    v6_data = v5_data.copy()
    v6_data["scraper_version"] = "6.0.0"
    v6_data["rule_version"] = "2014"
    
    # Add some v6.0.0 enhancements
    v6_data["ac_breakdown"] = {
        "base": 10,
        "dexterity_bonus": v6_data.get("ability_modifiers", {}).get("dexterity", 0),
        "armor_bonus": v6_data.get("armor_class", 10) - 10 - v6_data.get("ability_modifiers", {}).get("dexterity", 0),
        "calculation_method": "standard"
    }
    
    result = validator.validate(v6_data, character_id)
    print("\nRegression Validation Result:")
    print(result.get_summary())
    
    # Show accuracy score
    if result.accuracy_score is not None:
        print(f"\nRegression Test Accuracy: {result.accuracy_score:.1%}")
        if result.accuracy_score >= 0.95:
            print("✅ No regression detected (≥95% accuracy)")
        else:
            print("❌ Regression detected (<95% accuracy)")


def test_combined_validation():
    """Test all validators together."""
    logger.info("\n" + "=" * 60)
    logger.info("Testing Combined Validation")
    logger.info("=" * 60)
    
    # Load test character
    character_id = 145081718
    test_data = load_test_data(character_id)
    
    # Run all validators
    char_validator = CharacterValidator()
    calc_validator = CalculationValidator()
    regr_validator = RegressionValidator()
    
    # Aggregate results
    all_errors = []
    all_warnings = []
    
    # Character validation
    char_result = char_validator.validate(test_data)
    all_errors.extend(char_result.errors)
    all_warnings.extend(char_result.warnings)
    
    # Calculation validation
    calc_result = calc_validator.validate(test_data)
    all_errors.extend(calc_result.errors)
    all_warnings.extend(calc_result.warnings)
    
    # Regression validation (if baseline exists)
    baseline_file = Path(f"data/baseline/scraper/baseline_{character_id}.json")
    if baseline_file.exists():
        regr_result = regr_validator.validate(test_data, character_id)
        all_errors.extend(regr_result.errors)
        all_warnings.extend(regr_result.warnings)
    
    # Summary
    print("\nCombined Validation Summary:")
    print(f"Total Errors: {len(all_errors)}")
    print(f"Total Warnings: {len(all_warnings)}")
    
    if all_errors:
        print("\nTop Errors:")
        for error in all_errors[:5]:
            print(f"  ❌ {error}")
    
    if all_warnings:
        print("\nTop Warnings:")
        for warning in all_warnings[:5]:
            print(f"  ⚠️  {warning}")
    
    # Overall result
    if len(all_errors) == 0:
        print("\n✅ All validations PASSED!")
    else:
        print("\n❌ Validation FAILED")


def main():
    """Run all validation tests."""
    print("D&D Beyond Character Scraper - Validation Framework Test")
    print("=" * 60)
    
    try:
        # Test individual validators
        test_character_validation()
        test_calculation_validation()
        test_regression_validation()
        
        # Test combined validation
        test_combined_validation()
        
        print("\n✅ Validation framework test completed successfully!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()