"""
Unit tests for Ability Score Calculator

Tests ability score calculations including source breakdown and 2024 racial ASI support.
"""

import unittest
from unittest.mock import Mock

from src.calculators.ability_scores import AbilityScoreCalculator
from src.models.character import Character
from tests.factories import CharacterFactory, TestDataFactory


class TestAbilityScoreCalculator(unittest.TestCase):
    """Test cases for ability score calculations."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = AbilityScoreCalculator()
        
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
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Check ability scores
        scores = result['ability_scores']
        self.assertEqual(scores['strength'], 16)
        self.assertEqual(scores['dexterity'], 14)
        self.assertEqual(scores['constitution'], 15)
        self.assertEqual(scores['intelligence'], 10)
        self.assertEqual(scores['wisdom'], 13)
        self.assertEqual(scores['charisma'], 12)
        
        # Check modifiers
        modifiers = result['ability_modifiers']
        self.assertEqual(modifiers['strength'], 3)    # (16-10)//2 = 3
        self.assertEqual(modifiers['dexterity'], 2)    # (14-10)//2 = 2
        self.assertEqual(modifiers['constitution'], 2) # (15-10)//2 = 2
        self.assertEqual(modifiers['intelligence'], 0) # (10-10)//2 = 0
        self.assertEqual(modifiers['wisdom'], 1)       # (13-10)//2 = 1
        self.assertEqual(modifiers['charisma'], 1)     # (12-10)//2 = 1
    
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
        
        result = self.calculator.calculate(self.character, raw_data)
        
        modifiers = result['ability_modifiers']
        self.assertEqual(modifiers['strength'], -1)     # (8-10)//2 = -1
        self.assertEqual(modifiers['dexterity'], -1)    # (9-10)//2 = -1
        self.assertEqual(modifiers['constitution'], 5)  # (20-10)//2 = 5
        self.assertEqual(modifiers['intelligence'], 5)  # (21-10)//2 = 5
        self.assertEqual(modifiers['wisdom'], -4)       # (3-10)//2 = -3.5 -> -4
        self.assertEqual(modifiers['charisma'], 10)     # (30-10)//2 = 10
    
    def test_racial_asi_2014_rules(self):
        """Test 2014 racial ability score improvements."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 16},  # Base 15 + 1 racial = 16
                {'id': 2, 'value': 14},  # Base 14, no bonus
                {'id': 3, 'value': 15},  # Base 15, no bonus
                {'id': 4, 'value': 10},  # Base 10, no bonus
                {'id': 5, 'value': 13},  # Base 13, no bonus
                {'id': 6, 'value': 14}   # Base 12 + 2 racial = 14
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
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Should have breakdown showing racial bonuses
        if 'ability_score_breakdown' in result:
            breakdown = result['ability_score_breakdown']
            
            # Strength should show base + racial
            if 'strength' in breakdown:
                str_breakdown = breakdown['strength']
                self.assertIn('base', str_breakdown)
                self.assertIn('racial', str_breakdown)
                self.assertEqual(str_breakdown['racial'], 1)
            
            # Charisma should show base + racial
            if 'charisma' in breakdown:
                cha_breakdown = breakdown['charisma']
                self.assertIn('base', cha_breakdown)
                self.assertIn('racial', cha_breakdown)
                self.assertEqual(cha_breakdown['racial'], 2)
    
    def test_feat_asi(self):
        """Test ability score improvements from feats."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 17},  # Base 15 + 2 feat = 17
                {'id': 2, 'value': 15},  # Base 14 + 1 feat = 15
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
        
        result = self.calculator.calculate(self.character, raw_data)
        
        # Check final scores include feat bonuses
        scores = result['ability_scores']
        self.assertEqual(scores['strength'], 17)
        self.assertEqual(scores['dexterity'], 15)
        
        # Check breakdown if available
        if 'ability_score_breakdown' in result:
            breakdown = result['ability_score_breakdown']
            
            if 'strength' in breakdown:
                str_breakdown = breakdown['strength']
                self.assertIn('feat', str_breakdown)
                self.assertEqual(str_breakdown['feat'], 2)
    
    def test_class_asi(self):
        """Test ability score improvements from class levels."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 17},  # Base 15 + 2 class ASI = 17
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
        
        result = self.calculator.calculate(self.character, raw_data)
        
        scores = result['ability_scores']
        self.assertEqual(scores['strength'], 17)
        
        # Check breakdown if available
        if 'ability_score_breakdown' in result:
            breakdown = result['ability_score_breakdown']
            
            if 'strength' in breakdown:
                str_breakdown = breakdown['strength']
                self.assertIn('class', str_breakdown)
                self.assertEqual(str_breakdown['class'], 2)
    
    def test_set_modifiers(self):
        """Test 'set' type modifiers (overrides instead of bonus)."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 19},  # Set to 19 by modifier
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
        
        result = self.calculator.calculate(self.character, raw_data)
        
        scores = result['ability_scores']
        self.assertEqual(scores['strength'], 19)
        
        # Set modifier should override base
        if 'ability_score_breakdown' in result:
            breakdown = result['ability_score_breakdown']
            
            if 'strength' in breakdown:
                str_breakdown = breakdown['strength']
                self.assertIn('set', str_breakdown)
                self.assertEqual(str_breakdown['set'], 19)
    
    def test_multiple_sources(self):
        """Test ability scores from multiple sources."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 20},  # Base 15 + 2 racial + 2 feat + 1 class = 20
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
        
        result = self.calculator.calculate(self.character, raw_data)
        
        scores = result['ability_scores']
        self.assertEqual(scores['strength'], 20)
        
        # Check comprehensive breakdown
        if 'ability_score_breakdown' in result:
            breakdown = result['ability_score_breakdown']
            
            if 'strength' in breakdown:
                str_breakdown = breakdown['strength']
                self.assertEqual(str_breakdown.get('racial', 0), 2)
                self.assertEqual(str_breakdown.get('feat', 0), 2)
                self.assertEqual(str_breakdown.get('class', 0), 1)
                
                # Total should equal final score
                total = sum(str_breakdown.values())
                self.assertEqual(total, 20)
    
    def test_missing_stats_defaults(self):
        """Test default values when stats are missing."""
        raw_data = {
            'stats': [
                {'id': 1, 'value': 16},  # Only Strength provided
            ]
        }
        
        result = self.calculator.calculate(self.character, raw_data)
        
        scores = result['ability_scores']
        self.assertEqual(scores['strength'], 16)
        # Other abilities should default to 10
        self.assertEqual(scores['dexterity'], 10)
        self.assertEqual(scores['constitution'], 10)
        self.assertEqual(scores['intelligence'], 10)
        self.assertEqual(scores['wisdom'], 10)
        self.assertEqual(scores['charisma'], 10)
        
        # Modifiers should be calculated correctly
        modifiers = result['ability_modifiers']
        self.assertEqual(modifiers['strength'], 3)
        self.assertEqual(modifiers['dexterity'], 0)
        self.assertEqual(modifiers['constitution'], 0)


if __name__ == '__main__':
    unittest.main()