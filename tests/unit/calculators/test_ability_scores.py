"""
Unit tests for Ability Score Calculator

Tests ability score calculations including source breakdown and 2024 racial ASI support.
"""

import unittest
from unittest.mock import Mock

from src.calculators.enhanced_ability_scores import EnhancedAbilityScoreCalculator
from src.models.character import Character
from tests.factories import CharacterFactory, TestDataFactory


class TestAbilityScoreCalculator(unittest.TestCase):
    """Test cases for ability score calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = EnhancedAbilityScoreCalculator()
        
        # Create a basic character for testing
        self.character = CharacterFactory.create_basic_character(
            id=1,
            name="Test Character",
            level=5,
            proficiency_bonus=3
        )
    
    def test_basic_ability_scores(self):
        """Test basic ability score extraction from stats."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 15},  # Constitution
                {'id': 4, 'value': 10},  # Intelligence
                {'id': 5, 'value': 13},  # Wisdom
                {'id': 6, 'value': 12}   # Charisma
            ]
        }
        
        # Create mock calculation context
        from src.calculators.services.interfaces import CalculationContext
        context = CalculationContext(character_id=1, rule_version="2014")
        
        result = self.calculator.calculate(raw_data, context)
        
        # Check calculation was successful
        self.assertEqual(result.status.value, 'completed')
        
        # Check ability scores - now returns rich objects
        scores = result.data['ability_scores']
        self.assertEqual(scores['strength'].score, 16)
        self.assertEqual(scores['dexterity'].score, 14)
        self.assertEqual(scores['constitution'].score, 15)
        self.assertEqual(scores['intelligence'].score, 10)
        self.assertEqual(scores['wisdom'].score, 13)
        self.assertEqual(scores['charisma'].score, 12)
        
        # Check modifiers - available in both places
        modifiers = result.data['ability_modifiers']
        self.assertEqual(modifiers['strength'], 3)    # (16-10)//2 = 3
        self.assertEqual(modifiers['dexterity'], 2)    # (14-10)//2 = 2
        self.assertEqual(modifiers['constitution'], 2) # (15-10)//2 = 2
        self.assertEqual(modifiers['intelligence'], 0) # (10-10)//2 = 0
        self.assertEqual(modifiers['wisdom'], 1)       # (13-10)//2 = 1
        self.assertEqual(modifiers['charisma'], 1)     # (12-10)//2 = 1
        
        # Verify modifiers match object modifiers
        self.assertEqual(scores['strength'].modifier, 3)
        self.assertEqual(scores['dexterity'].modifier, 2)
        self.assertEqual(scores['constitution'].modifier, 2)
        self.assertEqual(scores['intelligence'].modifier, 0)
        self.assertEqual(scores['wisdom'].modifier, 1)
        self.assertEqual(scores['charisma'].modifier, 1)
        
        # Check source breakdown (new feature)
        self.assertEqual(scores['strength'].source_breakdown['base'], 16)
        self.assertEqual(scores['dexterity'].source_breakdown['base'], 14)
        self.assertEqual(scores['constitution'].source_breakdown['base'], 15)
        
        # Check save bonuses
        save_bonuses = result.data['save_bonuses']
        self.assertEqual(save_bonuses['strength'], 3)  # modifier + 0 (not proficient)
        self.assertEqual(save_bonuses['dexterity'], 2)  # modifier + 0 (not proficient)
        self.assertEqual(save_bonuses['constitution'], 2)  # modifier + 0 (not proficient)
    
    def test_modifier_calculation_edge_cases(self):
        """Test modifier calculation for edge cases."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 8},   # -1 modifier
                {'id': 2, 'value': 9},   # -1 modifier
                {'id': 3, 'value': 20},  # +5 modifier
                {'id': 4, 'value': 21},  # +5 modifier
                {'id': 5, 'value': 3},   # -4 modifier (minimum)
                {'id': 6, 'value': 30}   # +10 modifier (maximum)
            ]
        }
        
        # Create mock calculation context
        from src.calculators.services.interfaces import CalculationContext
        context = CalculationContext(character_id=1, rule_version="2014")
        
        result = self.calculator.calculate(raw_data, context)
        
        # Check calculation was successful
        self.assertEqual(result.status.value, 'completed')
        
        # Check ability scores
        scores = result.data['ability_scores']
        self.assertEqual(scores['strength'].score, 8)
        self.assertEqual(scores['dexterity'].score, 9)
        self.assertEqual(scores['constitution'].score, 20)
        self.assertEqual(scores['intelligence'].score, 21)
        self.assertEqual(scores['wisdom'].score, 3)
        self.assertEqual(scores['charisma'].score, 30)
        
        # Check modifiers
        modifiers = result.data['ability_modifiers']
        self.assertEqual(modifiers['strength'], -1)     # (8-10)//2 = -1
        self.assertEqual(modifiers['dexterity'], -1)    # (9-10)//2 = -1
        self.assertEqual(modifiers['constitution'], 5)  # (20-10)//2 = 5
        self.assertEqual(modifiers['intelligence'], 5)  # (21-10)//2 = 5
        self.assertEqual(modifiers['wisdom'], -4)       # (3-10)//2 = -3.5 -> -4
        self.assertEqual(modifiers['charisma'], 10)     # (30-10)//2 = 10
        
        # Verify modifiers match object modifiers
        self.assertEqual(scores['strength'].modifier, -1)
        self.assertEqual(scores['dexterity'].modifier, -1)
        self.assertEqual(scores['constitution'].modifier, 5)
        self.assertEqual(scores['intelligence'].modifier, 5)
        self.assertEqual(scores['wisdom'].modifier, -4)
        self.assertEqual(scores['charisma'].modifier, 10)
    
    def test_racial_asi_2014_rules(self):
        """Test 2014 racial ability score improvements."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 15},  # Base 15, will get +1 racial = 16
                {'id': 2, 'value': 14},  # Base 14, no bonus
                {'id': 3, 'value': 15},  # Base 15, no bonus
                {'id': 4, 'value': 10},  # Base 10, no bonus
                {'id': 5, 'value': 13},  # Base 13, no bonus
                {'id': 6, 'value': 12}   # Base 12, will get +2 racial = 14
            ],
            'modifiers': {
                'race': [
                    {
                        'subType': 'ability-score',
                        'type': 'bonus',
                        'value': 1,
                        'statId': 1  # Strength +1
                    },
                    {
                        'subType': 'ability-score',
                        'type': 'bonus',
                        'value': 2,
                        'statId': 6  # Charisma +2
                    }
                ]
            }
        }
        
        # Create mock calculation context
        from src.calculators.services.interfaces import CalculationContext
        context = CalculationContext(character_id=1, rule_version="2014")
        
        result = self.calculator.calculate(raw_data, context)
        
        # Check calculation was successful
        self.assertEqual(result.status.value, 'completed')
        
        # Check final scores include racial bonuses
        scores = result.data['ability_scores']
        self.assertEqual(scores['strength'].score, 16)  # Base 15 + 1 racial = 16
        self.assertEqual(scores['charisma'].score, 14)  # Base 12 + 2 racial = 14
        
        # Check source breakdown showing racial bonuses
        str_breakdown = scores['strength'].source_breakdown
        self.assertIn('base', str_breakdown)
        self.assertIn('racial', str_breakdown)
        self.assertEqual(str_breakdown['racial'], 1)
        
        cha_breakdown = scores['charisma'].source_breakdown
        self.assertIn('base', cha_breakdown)
        self.assertIn('racial', cha_breakdown)
        self.assertEqual(cha_breakdown['racial'], 2)
        
        # Verify total calculation is correct
        self.assertEqual(str_breakdown['base'] + str_breakdown['racial'], 16)
        self.assertEqual(cha_breakdown['base'] + cha_breakdown['racial'], 14)
    
    def test_feat_asi(self):
        """Test ability score improvements from feats."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 15},  # Base 15, will get +2 feat = 17
                {'id': 2, 'value': 14},  # Base 14, will get +1 feat = 15
                {'id': 3, 'value': 15},  # Base 15, no bonus
                {'id': 4, 'value': 10},  # Base 10, no bonus
                {'id': 5, 'value': 13},  # Base 13, no bonus
                {'id': 6, 'value': 12}   # Base 12, no bonus
            ],
            'modifiers': {
                'feat': [
                    {
                        'subType': 'ability-score',
                        'type': 'bonus',
                        'value': 2,
                        'statId': 1  # Strength +2
                    },
                    {
                        'subType': 'ability-score',
                        'type': 'bonus',
                        'value': 1,
                        'statId': 2  # Dexterity +1
                    }
                ]
            }
        }
        
        # Create mock calculation context
        from src.calculators.services.interfaces import CalculationContext
        context = CalculationContext(character_id=1, rule_version="2014")
        
        result = self.calculator.calculate(raw_data, context)
        
        # Check calculation was successful
        self.assertEqual(result.status.value, 'completed')
        
        # Check final scores include feat bonuses
        scores = result.data['ability_scores']
        self.assertEqual(scores['strength'].score, 17)
        self.assertEqual(scores['dexterity'].score, 15)
        
        # Check breakdown
        str_breakdown = scores['strength'].source_breakdown
        self.assertIn('feat', str_breakdown)
        self.assertEqual(str_breakdown['feat'], 2)
        
        dex_breakdown = scores['dexterity'].source_breakdown
        self.assertIn('feat', dex_breakdown)
        self.assertEqual(dex_breakdown['feat'], 1)
        
        # Verify total calculation is correct
        self.assertEqual(str_breakdown['base'] + str_breakdown['feat'], 17)
        self.assertEqual(dex_breakdown['base'] + dex_breakdown['feat'], 15)
    
    def test_class_asi(self):
        """Test ability score improvements from class levels."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 15},  # Base 15, will get +2 class ASI = 17
                {'id': 2, 'value': 14},  # Base 14, no bonus
                {'id': 3, 'value': 15},  # Base 15, no bonus
                {'id': 4, 'value': 10},  # Base 10, no bonus
                {'id': 5, 'value': 13},  # Base 13, no bonus
                {'id': 6, 'value': 12}   # Base 12, no bonus
            ],
            'modifiers': {
                'class': [
                    {
                        'subType': 'ability-score',
                        'type': 'bonus',
                        'value': 2,
                        'statId': 1  # Strength +2 from ASI
                    }
                ]
            }
        }
        
        # Create mock calculation context
        from src.calculators.services.interfaces import CalculationContext
        context = CalculationContext(character_id=1, rule_version="2014")
        
        result = self.calculator.calculate(raw_data, context)
        
        # Check calculation was successful
        self.assertEqual(result.status.value, 'completed')
        
        # Check final scores include class ASI bonuses
        scores = result.data['ability_scores']
        self.assertEqual(scores['strength'].score, 17)
        
        # Check breakdown - class ASI bonuses should be in 'asi' category
        str_breakdown = scores['strength'].source_breakdown
        self.assertIn('asi', str_breakdown)
        self.assertEqual(str_breakdown['asi'], 2)
        
        # Verify total calculation is correct
        self.assertEqual(str_breakdown['base'] + str_breakdown['asi'], 17)
    
    def test_set_modifiers(self):
        """Test 'set' type modifiers (overrides instead of bonus)."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 8},   # Base 8, will be set to 19 by modifier
                {'id': 2, 'value': 14},  # Base 14
                {'id': 3, 'value': 15},  # Base 15
                {'id': 4, 'value': 10},  # Base 10
                {'id': 5, 'value': 13},  # Base 13
                {'id': 6, 'value': 12}   # Base 12
            ],
            'modifiers': {
                'item': [
                    {
                        'subType': 'ability-score',
                        'type': 'set',
                        'value': 19,
                        'statId': 1  # Strength set to 19
                    }
                ]
            }
        }
        
        # Create mock calculation context
        from src.calculators.services.interfaces import CalculationContext
        context = CalculationContext(character_id=1, rule_version="2014")
        
        result = self.calculator.calculate(raw_data, context)
        
        # Check calculation was successful
        self.assertEqual(result.status.value, 'completed')
        
        # Check final score is set to 19
        scores = result.data['ability_scores']
        self.assertEqual(scores['strength'].score, 19)
        
        # Set modifier should be tracked in the breakdown
        str_breakdown = scores['strength'].source_breakdown
        self.assertIn('set', str_breakdown)
        self.assertEqual(str_breakdown['set'], 19)
        
        # Verify the modifier calculation is correct for the set score
        self.assertEqual(scores['strength'].modifier, 4)  # (19-10)//2 = 4
    
    def test_multiple_sources(self):
        """Test ability scores from multiple sources."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 15},  # Base 15, will get +2 racial + 2 feat + 1 class = 20
                {'id': 2, 'value': 14},  # Base 14
                {'id': 3, 'value': 15},  # Base 15
                {'id': 4, 'value': 10},  # Base 10
                {'id': 5, 'value': 13},  # Base 13
                {'id': 6, 'value': 12}   # Base 12
            ],
            'modifiers': {
                'race': [
                    {
                        'subType': 'ability-score',
                        'type': 'bonus',
                        'value': 2,
                        'statId': 1  # Strength +2 racial
                    }
                ],
                'feat': [
                    {
                        'subType': 'ability-score',
                        'type': 'bonus',
                        'value': 2,
                        'statId': 1  # Strength +2 feat
                    }
                ],
                'class': [
                    {
                        'subType': 'ability-score',
                        'type': 'bonus',
                        'value': 1,
                        'statId': 1  # Strength +1 class ASI
                    }
                ]
            }
        }
        
        # Create mock calculation context
        from src.calculators.services.interfaces import CalculationContext
        context = CalculationContext(character_id=1, rule_version="2014")
        
        result = self.calculator.calculate(raw_data, context)
        
        # Check calculation was successful
        self.assertEqual(result.status.value, 'completed')
        
        # Check final score includes all bonuses
        scores = result.data['ability_scores']
        self.assertEqual(scores['strength'].score, 20)
        
        # Check comprehensive breakdown
        str_breakdown = scores['strength'].source_breakdown
        self.assertEqual(str_breakdown.get('racial', 0), 2)
        self.assertEqual(str_breakdown.get('feat', 0), 2)
        self.assertEqual(str_breakdown.get('asi', 0), 1)  # Class ASI bonus
        
        # Total should equal final score
        total = sum(str_breakdown.values())
        self.assertEqual(total, 20)
        
        # Verify modifier calculation for high score
        self.assertEqual(scores['strength'].modifier, 5)  # (20-10)//2 = 5
    
    def test_missing_stats_defaults(self):
        """Test default values when stats are missing."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 16},  # Only Strength provided
            ]
        }
        
        # Create mock calculation context
        from src.calculators.services.interfaces import CalculationContext
        context = CalculationContext(character_id=1, rule_version="2014")
        
        result = self.calculator.calculate(raw_data, context)
        
        # Check calculation was successful
        self.assertEqual(result.status.value, 'completed')
        
        # Check ability scores
        scores = result.data['ability_scores']
        self.assertEqual(scores['strength'].score, 16)
        # Other abilities should default to 10
        self.assertEqual(scores['dexterity'].score, 10)
        self.assertEqual(scores['constitution'].score, 10)
        self.assertEqual(scores['intelligence'].score, 10)
        self.assertEqual(scores['wisdom'].score, 10)
        self.assertEqual(scores['charisma'].score, 10)
        
        # Modifiers should be calculated correctly
        modifiers = result.data['ability_modifiers']
        self.assertEqual(modifiers['strength'], 3)
        self.assertEqual(modifiers['dexterity'], 0)
        self.assertEqual(modifiers['constitution'], 0)
        self.assertEqual(modifiers['intelligence'], 0)
        self.assertEqual(modifiers['wisdom'], 0)
        self.assertEqual(modifiers['charisma'], 0)
        
        # Verify source breakdown for defaults
        self.assertEqual(scores['strength'].source_breakdown['base'], 16)
        self.assertEqual(scores['dexterity'].source_breakdown['base'], 10)
        self.assertEqual(scores['constitution'].source_breakdown['base'], 10)


if __name__ == '__main__':
    unittest.main()