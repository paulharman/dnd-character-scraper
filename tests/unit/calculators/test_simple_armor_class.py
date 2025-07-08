"""
Unit tests for Armor Class Calculator (Simplified)

Tests the AC calculation directly with raw data instead of complex Character models.
"""

import unittest
from unittest.mock import Mock

from src.calculators.armor_class import ArmorClassCalculator


class TestArmorClassCalculatorSimple(unittest.TestCase):
    """Test cases for armor class calculations with raw data."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = ArmorClassCalculator()
    
    def test_basic_ac_no_armor(self):
        """Test basic AC calculation with no armor."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 14}  # Dexterity 14 = +2 modifier
            ],
            'inventory': [],
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Fighter'
                    }
                }
            ]
        }
        
        # Mock character
        character = Mock()
        character.level = 5
        
        result = self.calculator.calculate(character, raw_data)
        
        # Base AC = 10 + Dex modifier = 10 + 2 = 12
        self.assertEqual(result['armor_class'], 12)
    
    def test_barbarian_unarmored_defense(self):
        """Test Barbarian Unarmored Defense: AC = 10 + Dex + Con."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 16},  # Dexterity 16 = +3
                {'id': 3, 'value': 18}   # Constitution 18 = +4
            ],
            'inventory': [],  # No armor
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Barbarian'
                    }
                }
            ]
        }
        
        character = Mock()
        character.level = 5
        
        result = self.calculator.calculate(character, raw_data)
        
        # Barbarian Unarmored Defense = 10 + Dex + Con = 10 + 3 + 4 = 17
        self.assertEqual(result['armor_class'], 17)
    
    def test_monk_unarmored_defense(self):
        """Test Monk Unarmored Defense: AC = 10 + Dex + Wis."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 16},  # Dexterity 16 = +3
                {'id': 5, 'value': 18}   # Wisdom 18 = +4
            ],
            'inventory': [],  # No armor, no shield
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Monk'
                    }
                }
            ]
        }
        
        character = Mock()
        character.level = 5
        
        result = self.calculator.calculate(character, raw_data)
        
        # Monk Unarmored Defense = 10 + Dex + Wis = 10 + 3 + 4 = 17
        self.assertEqual(result['armor_class'], 17)
    
    def test_ac_with_armor(self):
        """Test AC calculation with armor."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 14}  # Dexterity 14 = +2
            ],
            'inventory': [
                {
                    'definition': {
                        'name': 'Chain Mail',
                        'armorClass': 16,
                        'armorTypeId': 3  # Heavy armor
                    },
                    'equipped': True
                }
            ],
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Fighter'
                    }
                }
            ]
        }
        
        character = Mock()
        character.level = 5
        
        result = self.calculator.calculate(character, raw_data)
        
        # Chain Mail AC = 16 (no Dex bonus for heavy armor)
        self.assertEqual(result['armor_class'], 16)
    
    def test_ac_with_shield(self):
        """Test AC calculation with shield."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 14}  # Dexterity 14 = +2
            ],
            'inventory': [
                {
                    'definition': {
                        'name': 'Leather Armor',
                        'armorClass': 11,
                        'armorTypeId': 1  # Light armor
                    },
                    'equipped': True
                },
                {
                    'definition': {
                        'name': 'Shield',
                        'armorClass': 2,
                        'armorTypeId': 4  # Shield
                    },
                    'equipped': True
                }
            ],
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Fighter'
                    }
                }
            ]
        }
        
        character = Mock()
        character.level = 5
        
        result = self.calculator.calculate(character, raw_data)
        
        # Leather Armor (11) + Dex (+2) + Shield (+2) = 15
        self.assertEqual(result['armor_class'], 15)


if __name__ == '__main__':
    unittest.main()