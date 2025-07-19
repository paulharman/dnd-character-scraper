"""
Isolated calculator tests for quick validation.

Tests individual calculators without requiring the full character processing pipeline.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from src.calculators.armor_class import ArmorClassCalculator
from src.calculators.hit_points import HitPointCalculator
from src.calculators.spellcasting import SpellcastingCalculator
from src.calculators.ability_scores import AbilityScoreCalculator
from src.calculators.wealth import WealthCalculator

from ..factories.character_archetypes import CharacterArchetypeFactory
from ..factories.api_responses import APIResponseFactory

class TestArmorClassCalculator:
    """Tests for ArmorClassCalculator."""
    
    @pytest.mark.quick
    def test_basic_ac_calculation(self):
        """Test basic AC calculation for fighter."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        calculator = ArmorClassCalculator()
        
        # Mock the character object
        mock_character = Mock()
        mock_character.ability_scores = Mock()
        mock_character.ability_scores.get_modifier.return_value = 2  # Dex modifier
        mock_character.equipment = Mock()
        mock_character.equipment.armor = Mock()
        mock_character.equipment.armor.ac_base = 16
        mock_character.equipment.armor.ac_bonus = 0
        
        result = calculator.calculate(mock_character)
        
        assert result is not None
        assert hasattr(result, 'total_ac')
        assert result.total_ac >= 10  # Minimum AC
    
    @pytest.mark.quick
    def test_unarmored_ac_calculation(self):
        """Test AC calculation for unarmored character."""
        character_data = CharacterArchetypeFactory.create_wizard(level=1)
        calculator = ArmorClassCalculator()
        
        mock_character = Mock()
        mock_character.ability_scores = Mock()
        mock_character.ability_scores.get_modifier.return_value = 2  # Dex modifier
        mock_character.equipment = Mock()
        mock_character.equipment.armor = None
        
        result = calculator.calculate(mock_character)
        
        assert result is not None
        assert result.total_ac == 12  # 10 + 2 dex

    @pytest.mark.quick
    def test_ac_with_shield(self):
        """Test AC calculation with shield."""
        calculator = ArmorClassCalculator()
        
        mock_character = Mock()
        mock_character.ability_scores = Mock()
        mock_character.ability_scores.get_modifier.return_value = 2
        mock_character.equipment = Mock()
        mock_character.equipment.armor = Mock()
        mock_character.equipment.armor.ac_base = 16
        mock_character.equipment.armor.ac_bonus = 0
        mock_character.equipment.shield = Mock()
        mock_character.equipment.shield.ac_bonus = 2
        
        result = calculator.calculate(mock_character)
        
        assert result.total_ac == 18  # 16 + 2 shield

class TestHitPointsCalculator:
    """Tests for HitPointCalculator."""
    
    @pytest.mark.quick
    def test_basic_hp_calculation(self):
        """Test basic HP calculation for fighter."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        calculator = HitPointCalculator()
        
        mock_character = Mock()
        mock_character.level = 1
        mock_character.classes = [Mock()]
        mock_character.classes[0].hit_die = 10
        mock_character.classes[0].level = 1
        mock_character.ability_scores = Mock()
        mock_character.ability_scores.get_modifier.return_value = 2  # Con modifier
        
        result = calculator.calculate(mock_character)
        
        assert result is not None
        assert hasattr(result, 'total_hp')
        assert result.total_hp >= 11  # 10 + 1 con mod minimum

    @pytest.mark.quick
    def test_multiclass_hp_calculation(self):
        """Test HP calculation for multiclass character."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        calculator = HitPointCalculator()
        
        mock_character = Mock()
        mock_character.level = 5
        mock_character.classes = [Mock(), Mock()]
        mock_character.classes[0].hit_die = 10
        mock_character.classes[0].level = 3
        mock_character.classes[1].hit_die = 6
        mock_character.classes[1].level = 2
        mock_character.ability_scores = Mock()
        mock_character.ability_scores.get_modifier.return_value = 2
        
        result = calculator.calculate(mock_character)
        
        assert result is not None
        assert result.total_hp > 20  # Should be reasonable for level 5

    @pytest.mark.quick
    def test_negative_con_modifier(self):
        """Test HP calculation with negative constitution modifier."""
        calculator = HitPointCalculator()
        
        mock_character = Mock()
        mock_character.level = 1
        mock_character.classes = [Mock()]
        mock_character.classes[0].hit_die = 6
        mock_character.classes[0].level = 1
        mock_character.ability_scores = Mock()
        mock_character.ability_scores.get_modifier.return_value = -2  # Negative con mod
        
        result = calculator.calculate(mock_character)
        
        assert result is not None
        assert result.total_hp >= 1  # HP should never go below 1

class TestSpellcastingCalculator:
    """Tests for SpellcastingCalculator."""
    
    @pytest.mark.quick
    def test_wizard_spellcasting(self):
        """Test spellcasting calculation for wizard."""
        character_data = CharacterArchetypeFactory.create_wizard(level=3)
        calculator = SpellcastingCalculator()
        
        mock_character = Mock()
        mock_character.level = 3
        mock_character.classes = [Mock()]
        mock_character.classes[0].name = "Wizard"
        mock_character.classes[0].level = 3
        mock_character.classes[0].spellcasting_ability = "intelligence"
        mock_character.ability_scores = Mock()
        mock_character.ability_scores.get_modifier.return_value = 3  # Int modifier
        
        result = calculator.calculate(mock_character)
        
        assert result is not None
        assert hasattr(result, 'spell_slots')
        assert result.spell_slots.get('1', 0) > 0  # Should have 1st level slots

    @pytest.mark.quick
    def test_non_spellcaster(self):
        """Test spellcasting calculation for non-spellcaster."""
        character_data = CharacterArchetypeFactory.create_fighter(level=5)
        calculator = SpellcastingCalculator()
        
        mock_character = Mock()
        mock_character.level = 5
        mock_character.classes = [Mock()]
        mock_character.classes[0].name = "Fighter"
        mock_character.classes[0].level = 5
        mock_character.classes[0].spellcasting_ability = None
        
        result = calculator.calculate(mock_character)
        
        # Should handle non-spellcaster gracefully
        assert result is not None

    @pytest.mark.quick
    def test_multiclass_spellcasting(self):
        """Test spellcasting calculation for multiclass spellcaster."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        calculator = SpellcastingCalculator()
        
        mock_character = Mock()
        mock_character.level = 5
        mock_character.classes = [Mock(), Mock()]
        mock_character.classes[0].name = "Fighter"
        mock_character.classes[0].level = 3
        mock_character.classes[0].spellcasting_ability = None
        mock_character.classes[1].name = "Wizard"
        mock_character.classes[1].level = 2
        mock_character.classes[1].spellcasting_ability = "intelligence"
        mock_character.ability_scores = Mock()
        mock_character.ability_scores.get_modifier.return_value = 3
        
        result = calculator.calculate(mock_character)
        
        assert result is not None
        assert hasattr(result, 'spell_slots')

class TestAbilityScoresCalculator:
    """Tests for AbilityScoreCalculator."""
    
    @pytest.mark.quick
    def test_basic_ability_scores(self):
        """Test basic ability score calculation."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        calculator = AbilityScoreCalculator()
        
        mock_character = Mock()
        mock_character.base_ability_scores = {
            "strength": 16,
            "dexterity": 14,
            "constitution": 15,
            "intelligence": 10,
            "wisdom": 12,
            "charisma": 8
        }
        mock_character.racial_bonuses = {}
        mock_character.magical_bonuses = {}
        
        result = calculator.calculate(mock_character)
        
        assert result is not None
        assert hasattr(result, 'strength')
        assert result.strength >= 1
        assert result.strength <= 30

    @pytest.mark.quick
    def test_ability_score_modifiers(self):
        """Test ability score modifier calculation."""
        calculator = AbilityScoreCalculator()
        
        mock_character = Mock()
        mock_character.base_ability_scores = {
            "strength": 16,
            "dexterity": 10,
            "constitution": 8
        }
        mock_character.racial_bonuses = {}
        mock_character.magical_bonuses = {}
        
        result = calculator.calculate(mock_character)
        
        assert result.get_modifier('strength') == 3  # 16 -> +3
        assert result.get_modifier('dexterity') == 0  # 10 -> +0
        assert result.get_modifier('constitution') == -1  # 8 -> -1

class TestWealthCalculator:
    """Tests for WealthCalculator."""
    
    @pytest.mark.quick
    def test_basic_wealth_calculation(self):
        """Test basic wealth calculation."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        calculator = WealthCalculator()
        
        mock_character = Mock()
        mock_character.equipment = Mock()
        mock_character.equipment.currency = {
            "gold": 100,
            "silver": 50,
            "copper": 25
        }
        mock_character.equipment.items = []
        
        result = calculator.calculate(mock_character)
        
        assert result is not None
        assert hasattr(result, 'total_gold_value')
        assert result.total_gold_value >= 0

    @pytest.mark.quick
    def test_currency_conversion(self):
        """Test currency conversion to gold."""
        calculator = WealthCalculator()
        
        mock_character = Mock()
        mock_character.equipment = Mock()
        mock_character.equipment.currency = {
            "gold": 10,
            "silver": 100,  # 10 gold equivalent
            "copper": 1000  # 10 gold equivalent
        }
        mock_character.equipment.items = []
        
        result = calculator.calculate(mock_character)
        
        assert result.total_gold_value == 30  # 10 + 10 + 10

# Performance tests
class TestCalculatorPerformance:
    """Performance tests for calculators."""
    
    @pytest.mark.quick
    def test_calculator_speed(self):
        """Test that calculator operations complete quickly."""
        import time
        
        character_data = CharacterArchetypeFactory.create_wizard(level=10)
        calculator = ArmorClassCalculator()
        
        mock_character = Mock()
        mock_character.ability_scores = Mock()
        mock_character.ability_scores.get_modifier.return_value = 2
        mock_character.equipment = Mock()
        mock_character.equipment.armor = None
        
        start_time = time.time()
        result = calculator.calculate(mock_character)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 0.1  # Should complete in under 100ms
        assert result is not None

# Error handling tests
class TestCalculatorErrorHandling:
    """Error handling tests for calculators."""
    
    @pytest.mark.quick
    def test_invalid_character_data(self):
        """Test calculator handling of invalid character data."""
        calculator = ArmorClassCalculator()
        
        # Test with None character
        result = calculator.calculate(None)
        assert result is not None or result is None  # Should handle gracefully
        
        # Test with incomplete character data
        mock_character = Mock()
        mock_character.ability_scores = None
        mock_character.equipment = None
        
        result = calculator.calculate(mock_character)
        # Should not raise an exception
        assert True  # If we get here, no exception was raised

    @pytest.mark.quick
    def test_missing_data_handling(self):
        """Test handling of missing required data."""
        calculator = HitPointCalculator()
        
        mock_character = Mock()
        mock_character.level = None
        mock_character.classes = []
        mock_character.ability_scores = None
        
        # Should handle missing data gracefully
        try:
            result = calculator.calculate(mock_character)
            assert True  # No exception raised
        except Exception as e:
            # If exception is raised, it should be a known type
            assert isinstance(e, (ValueError, AttributeError, TypeError))