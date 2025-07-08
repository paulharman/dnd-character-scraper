"""
Unit tests for Armor Class Calculator

Tests the AC calculation including the fixed Barbarian/Monk Unarmored Defense.
"""

import unittest
from unittest.mock import Mock

from src.calculators.armor_class import ArmorClassCalculator
from src.models.character import Character, AbilityScores
from tests.factories import CharacterFactory, TestDataFactory


class TestArmorClassCalculator(unittest.TestCase):
    """Test cases for armor class calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = ArmorClassCalculator()
        
        # Create a basic character for testing with specific ability scores
        ability_scores = CharacterFactory.create_ability_scores(
            strength=16,
            dexterity=14,
            constitution=16,
            intelligence=10,
            wisdom=13,
            charisma=12
        )
        self.character = CharacterFactory.create_basic_character(
            id=1,
            name="Test Character",
            level=10,
            ability_scores=ability_scores,
            proficiency_bonus=4
        )
    
    def test_basic_ac_calculation(self):
        """Test basic AC calculation (10 + Dex modifier)."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 14}  # Dexterity 14 = +2 modifier
            ],
            'inventory': []  # No armor
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        self.assertEqual(result['armor_class'], 12)  # 10 + 2 Dex
        self.assertEqual(result['ac_breakdown']['base'], 10)
        self.assertEqual(result['ac_breakdown']['dexterity_bonus'], 2)
    
    def test_barbarian_unarmored_defense(self):
        """Test Barbarian Unarmored Defense (10 + Dex + Con)."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 14},  # Dexterity 14 = +2
                {'id': 3, 'value': 16}   # Constitution 16 = +3
            ],
            'classes': [{
                'definition': {'name': 'Barbarian'}
            }],
            'inventory': []  # No armor
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should be 10 + 2 (Dex) + 3 (Con) = 15
        self.assertEqual(result['armor_class'], 15)
        self.assertIn("unarmored_defense", result['ac_breakdown'])
        self.assertEqual(result['ac_breakdown']['base'], 10)
        self.assertEqual(result['ac_breakdown']['dexterity_bonus'], 2)
        # The unarmored defense bonus should be the Con modifier
        unarmored_bonus = result['ac_breakdown'].get('unarmored_defense', 0)
        self.assertEqual(unarmored_bonus, 3)  # Con modifier
    
    def test_monk_unarmored_defense(self):
        """Test Monk Unarmored Defense (10 + Dex + Wis, no shield)."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 16},  # Dexterity 16 = +3
                {'id': 5, 'value': 16}   # Wisdom 16 = +3
            ],
            'classes': [{
                'definition': {'name': 'Monk'}
            }],
            'inventory': []  # No armor or shield
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should be 10 + 3 (Dex) + 3 (Wis) = 16
        self.assertEqual(result['armor_class'], 16)
        self.assertEqual(result['ac_breakdown']['base'], 10)
        self.assertEqual(result['ac_breakdown']['dexterity_bonus'], 3)
        unarmored_bonus = result['ac_breakdown'].get('unarmored_defense', 0)
        self.assertEqual(unarmored_bonus, 3)  # Wis modifier
    
    def test_monk_with_shield_no_bonus(self):
        """Test that Monk doesn't get Wisdom bonus when using a shield."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 16},  # Dexterity 16 = +3
                {'id': 5, 'value': 16}   # Wisdom 16 = +3
            ],
            'classes': [{
                'definition': {'name': 'Monk'}
            }],
            'inventory': [{
                'equipped': True,
                'definition': {
                    'name': 'Shield',
                    'armorTypeId': 4,  # Shield type
                    'armorClass': 2
                }
            }]
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should be 10 + 3 (Dex) + 2 (shield) = 15 (no Wis bonus)
        self.assertEqual(result['armor_class'], 15)
        self.assertEqual(result['ac_breakdown']['shield_bonus'], 2)
        # Should not have unarmored defense bonus
        unarmored_bonus = result['ac_breakdown'].get('unarmored_defense', 0)
        self.assertEqual(unarmored_bonus, 0)
    
    def test_barbarian_with_armor_no_bonus(self):
        """Test that Barbarian doesn't get Con bonus when wearing armor."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 14},  # Dexterity 14 = +2
                {'id': 3, 'value': 16}   # Constitution 16 = +3
            ],
            'classes': [{
                'definition': {'name': 'Barbarian'}
            }],
            'inventory': [{
                'equipped': True,
                'definition': {
                    'name': 'Leather Armor',
                    'armorTypeId': 1,  # Light armor
                    'baseArmorName': 'Leather',
                    'armorClass': 1  # 11 + Dex
                }
            }]
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should use armor calculation, not Unarmored Defense
        # Leather is 11 + Dex(2) = 13
        self.assertEqual(result['armor_class'], 13)
        self.assertEqual(result['ac_breakdown']['armor_bonus'], 1)
        # Should not have unarmored defense bonus
        unarmored_bonus = result['ac_breakdown'].get('unarmored_defense', 0)
        self.assertEqual(unarmored_bonus, 0)
    
    def test_armor_with_dex_limit(self):
        """Test armor that limits Dexterity bonus."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 18}  # Dexterity 18 = +4
            ],
            'inventory': [{
                'equipped': True,
                'definition': {
                    'name': 'Half Plate',
                    'armorTypeId': 2,  # Medium armor
                    'baseArmorName': 'Half Plate',
                    'armorClass': 5,  # 15 + Dex (max 2)
                    'maxDexModifier': 2
                }
            }]
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Half Plate is 15 + Dex (max 2), so 15 + 2 = 17 (not 19)
        self.assertEqual(result['armor_class'], 17)
        self.assertEqual(result['ac_breakdown']['dexterity_bonus'], 2)  # Limited to 2
    
    def test_heavy_armor_no_dex(self):
        """Test heavy armor ignores Dexterity."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 18}  # Dexterity 18 = +4
            ],
            'inventory': [{
                'equipped': True,
                'definition': {
                    'name': 'Plate Armor',
                    'armorTypeId': 3,  # Heavy armor
                    'baseArmorName': 'Plate',
                    'armorClass': 8,  # AC 18, no Dex
                    'maxDexModifier': 0
                }
            }]
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Plate is AC 18, no Dex bonus
        self.assertEqual(result['armor_class'], 18)
        self.assertEqual(result['ac_breakdown']['dexterity_bonus'], 0)
    
    def test_shield_bonus(self):
        """Test shield adds +2 AC."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 14}  # Dexterity 14 = +2
            ],
            'inventory': [{
                'equipped': True,
                'definition': {
                    'name': 'Shield',
                    'armorTypeId': 4,
                    'armorClass': 2
                }
            }]
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # 10 + 2 (Dex) + 2 (shield) = 14
        self.assertEqual(result['armor_class'], 14)
        self.assertEqual(result['ac_breakdown']['shield_bonus'], 2)
    
    def test_api_override(self):
        """Test that API override value is used when present."""
        raw_data = {
            'stats': [
                {'id': 2, 'value': 14}  # Dexterity 14 = +2
            ],
            'armorClass': 20  # API override
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should use the API value
        self.assertEqual(result['armor_class'], 20)


if __name__ == '__main__':
    unittest.main()