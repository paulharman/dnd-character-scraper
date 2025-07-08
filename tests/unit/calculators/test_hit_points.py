"""
Unit tests for Hit Points Calculator

Tests HP calculations with Constitution bonuses and class hit dice.
"""

import unittest
from unittest.mock import Mock

from src.calculators.hit_points import HitPointCalculator
from src.models.character import Character, AbilityScores
from tests.factories import CharacterFactory, TestDataFactory


class TestHitPointCalculator(unittest.TestCase):
    """Test cases for hit point calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = HitPointCalculator()
        
        # Create a basic character for testing with specific ability scores
        ability_scores = CharacterFactory.create_ability_scores(
            strength=16,
            dexterity=14,
            constitution=16,  # +3 modifier
            intelligence=10,
            wisdom=13,
            charisma=12
        )
        self.character = CharacterFactory.create_basic_character(
            id=1,
            name="Test Character",
            level=5,
            ability_scores=ability_scores,
            proficiency_bonus=3
        )
    
    def test_basic_hp_calculation(self):
        """Test basic HP calculation with Constitution bonus."""
        raw_data = {
            'stats': [
                {'id': 3, 'value': 16}  # Constitution 16 = +3 modifier
            ],
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Fighter',
                        'hitDie': 10
                    }
                }
            ],
            'baseHitPoints': 34,  # Average: 10 + 4*5.5 = 32, but let's say 34
            'bonusHitPoints': 15   # 3 Con * 5 levels = 15
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should combine base + con bonus
        expected_hp = 34 + 15  # 49
        self.assertEqual(result['max_hp'], expected_hp)
        
        # Check breakdown if available
        if 'hit_point_breakdown' in result:
            breakdown = result['hit_point_breakdown']
            self.assertEqual(breakdown['base_hp'], 34)
            self.assertEqual(breakdown['con_bonus'], 15)
    
    def test_fighter_hit_die(self):
        """Test Fighter hit die (d10) calculations."""
        raw_data = {
            'stats': [
                {'id': 3, 'value': 14}  # Constitution 14 = +2 modifier
            ],
            'classes': [
                {
                    'level': 3,
                    'definition': {
                        'name': 'Fighter',
                        'hitDie': 10
                    }
                }
            ],
            'baseHitPoints': 26,  # 10 + 2*8 = 26 (10 first level, then 8+8)
            'bonusHitPoints': 6   # 2 Con * 3 levels = 6
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        expected_hp = 26 + 6  # 32
        self.assertEqual(result['max_hp'], expected_hp)
        
        # Verify minimum HP (should be at least level * (1 + con mod))
        min_hp = 3 * (1 + 2)  # 3 levels * 3 min = 9
        self.assertGreaterEqual(result['max_hp'], min_hp)
    
    def test_wizard_hit_die(self):
        """Test Wizard hit die (d6) calculations."""
        raw_data = {
            'stats': [
                {'id': 3, 'value': 14}  # Constitution 14 = +2 modifier
            ],
            'classes': [
                {
                    'level': 4,
                    'definition': {
                        'name': 'Wizard',
                        'hitDie': 6
                    }
                }
            ],
            'baseHitPoints': 16,  # 6 + 3*3.5 = 16.5 -> 16
            'bonusHitPoints': 8   # 2 Con * 4 levels = 8
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        expected_hp = 16 + 8  # 24
        self.assertEqual(result['max_hp'], expected_hp)
        
        # Verify reasonable HP for Wizard
        self.assertGreaterEqual(result['max_hp'], 12)  # Minimum reasonable
        self.assertLessEqual(result['max_hp'], 40)     # Maximum reasonable for level 4
    
    def test_barbarian_hit_die(self):
        """Test Barbarian hit die (d12) calculations."""
        raw_data = {
            'stats': [
                {'id': 3, 'value': 18}  # Constitution 18 = +4 modifier
            ],
            'classes': [
                {
                    'level': 6,
                    'definition': {
                        'name': 'Barbarian',
                        'hitDie': 12
                    }
                }
            ],
            'baseHitPoints': 54,  # 12 + 5*6.5 = 44.5, but high rolls = 54
            'bonusHitPoints': 24  # 4 Con * 6 levels = 24
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        expected_hp = 54 + 24  # 78
        self.assertEqual(result['max_hp'], expected_hp)
        
        # Barbarians should have high HP
        self.assertGreaterEqual(result['max_hp'], 30)  # Minimum for level 6 Barbarian
    
    def test_multiclass_hp(self):
        """Test multiclass hit point calculations."""
        raw_data = {
            'stats': [
                {'id': 3, 'value': 16}  # Constitution 16 = +3 modifier
            ],
            'classes': [
                {
                    'level': 3,
                    'definition': {
                        'name': 'Fighter',
                        'hitDie': 10
                    }
                },
                {
                    'level': 2,
                    'definition': {
                        'name': 'Rogue',
                        'hitDie': 8
                    }
                }
            ],
            'baseHitPoints': 30,  # Fighter: 10 + 2*5.5, Rogue: 8 + 1*4.5 = 30.5
            'bonusHitPoints': 15  # 3 Con * 5 total levels = 15
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        expected_hp = 30 + 15  # 45
        self.assertEqual(result['max_hp'], expected_hp)
        
        # Should track total level correctly
        total_level = sum(cls['level'] for cls in raw_data['classes'])
        self.assertEqual(total_level, 5)
    
    def test_negative_con_modifier(self):
        """Test HP with negative Constitution modifier."""
        raw_data = {
            'stats': [
                {'id': 3, 'value': 8}  # Constitution 8 = -1 modifier
            ],
            'classes': [
                {
                    'level': 3,
                    'definition': {
                        'name': 'Wizard',
                        'hitDie': 6
                    }
                }
            ],
            'baseHitPoints': 13,   # 6 + 2*3.5 = 13
            'bonusHitPoints': -3   # -1 Con * 3 levels = -3
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        expected_hp = 13 + (-3)  # 10
        self.assertEqual(result['max_hp'], expected_hp)
        
        # Should have minimum 1 HP per level
        min_hp = 3  # 3 levels * 1 HP minimum
        self.assertGreaterEqual(result['max_hp'], min_hp)
    
    def test_hp_override(self):
        """Test HP override from D&D Beyond."""
        raw_data = {
            'stats': [
                {'id': 3, 'value': 14}  # Constitution 14 = +2 modifier
            ],
            'classes': [
                {
                    'level': 2,
                    'definition': {
                        'name': 'Fighter',
                        'hitDie': 10
                    }
                }
            ],
            'overrideHitPoints': 25,  # Manual override
            'baseHitPoints': 15,
            'bonusHitPoints': 4
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should use override value
        self.assertEqual(result['max_hp'], 25)
        
        # Should note that it's an override
        if 'calculation_method' in result:
            self.assertIn('override', result['calculation_method'].lower())
    
    def test_fixed_hp_type(self):
        """Test fixed HP type (manual HP instead of rolled)."""
        raw_data = {
            'stats': [
                {'id': 3, 'value': 16}  # Constitution 16 = +3 modifier
            ],
            'classes': [
                {
                    'level': 4,
                    'definition': {
                        'name': 'Paladin',
                        'hitDie': 10
                    }
                }
            ],
            'baseHitPoints': 34,    # 10 + 3*8 = 34 (taking average)
            'bonusHitPoints': 12,   # 3 Con * 4 levels = 12
            'removedHitPoints': 0,
            'hitPointMaxModifier': 0
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        expected_hp = 34 + 12  # 46
        self.assertEqual(result['max_hp'], expected_hp)
        
        # Should be reasonable for a Paladin
        self.assertGreaterEqual(result['max_hp'], 16)  # Minimum (4 * 4)
        self.assertLessEqual(result['max_hp'], 52)     # Maximum (10+3*10+3*4)
    
    def test_hit_point_type_detection(self):
        """Test detection of HP calculation type."""
        raw_data = {
            'stats': [
                {'id': 3, 'value': 14}
            ],
            'classes': [
                {
                    'level': 2,
                    'definition': {
                        'name': 'Fighter',
                        'hitDie': 10
                    }
                }
            ],
            'baseHitPoints': 15,
            'bonusHitPoints': 4,
            'hitPointType': 2  # Fixed HP type
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        if 'hit_point_type' in result:
            self.assertEqual(result['hit_point_type'], 2)
    
    def test_temporary_hit_points(self):
        """Test that temporary HP doesn't affect max HP."""
        raw_data = {
            'stats': [
                {'id': 3, 'value': 14}
            ],
            'classes': [
                {
                    'level': 2,
                    'definition': {
                        'name': 'Fighter',
                        'hitDie': 10
                    }
                }
            ],
            'baseHitPoints': 15,
            'bonusHitPoints': 4,
            'temporaryHitPoints': 5  # Temporary HP shouldn't affect max
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Max HP should ignore temporary HP
        expected_hp = 15 + 4  # 19
        self.assertEqual(result['max_hp'], expected_hp)
        
        # But temporary HP might be tracked separately
        if 'temporary_hp' in result:
            self.assertEqual(result['temporary_hp'], 5)


if __name__ == '__main__':
    unittest.main()