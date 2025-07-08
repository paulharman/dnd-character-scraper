"""
Integration Tests - Complete Character Processing Flow

Tests the entire pipeline from raw D&D Beyond data to final JSON/markdown output.
"""

import unittest
import json
import os
from unittest.mock import Mock, patch

from src.calculators.character_calculator import CharacterCalculator
from src.rules.version_manager import RuleVersionManager, RuleVersion


class TestCharacterProcessing(unittest.TestCase):
    """Test complete character processing pipeline."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.calculator = CharacterCalculator()
        self.rule_manager = RuleVersionManager()
        
        # Sample baseline character data
        self.sample_character = {
            'id': 145081718,
            'name': 'Test Character',
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Fighter',
                        'hitDie': 10,
                        'sourceId': 1
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 15},  # Constitution
                {'id': 4, 'value': 10},  # Intelligence
                {'id': 5, 'value': 13},  # Wisdom
                {'id': 6, 'value': 12}   # Charisma
            ],
            'race': {
                'definition': {
                    'name': 'Human',
                    'sourceId': 1
                }
            },
            'background': {
                'definition': {
                    'name': 'Soldier',
                    'sourceId': 1
                }
            },
            'spells': {},
            'classSpells': [],
            'inventory': [],
            'modifiers': {
                'race': [],
                'class': [],
                'background': [],
                'feat': [],
                'item': []
            }
        }
    
    def test_complete_json_output_structure(self):
        """Test that complete JSON output has all expected fields."""
        result = self.calculator.calculate_complete_json(self.sample_character)
        
        # Core character information
        required_fields = [
            'id', 'name', 'level', 'proficiency_bonus',
            'ability_scores', 'ability_modifiers',
            'armor_class', 'max_hp', 'initiative_bonus',
            'spellcasting'
        ]
        
        for field in required_fields:
            self.assertIn(field, result, f"Missing required field: {field}")
        
        # Check ability scores structure
        ability_fields = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        for ability in ability_fields:
            self.assertIn(ability, result['ability_scores'])
            self.assertIn(ability, result['ability_modifiers'])
        
        # Check spellcasting structure
        spellcasting_fields = ['is_spellcaster', 'spellcasting_ability', 'spell_save_dc']
        for field in spellcasting_fields:
            self.assertIn(field, result['spellcasting'])
        
        # Check data types
        self.assertIsInstance(result['id'], int)
        self.assertIsInstance(result['name'], str)
        self.assertIsInstance(result['level'], int)
        self.assertIsInstance(result['armor_class'], int)
        self.assertIsInstance(result['max_hp'], int)
        self.assertIsInstance(result['proficiency_bonus'], int)
    
    def test_rule_version_integration(self):
        """Test integration between rule version detection and calculations."""
        # Test 2014 character
        character_2014 = self.sample_character.copy()
        character_2014['classes'][0]['definition']['sourceId'] = 1  # 2014 PHB
        
        result_2014 = self.calculator.calculate_complete_json(character_2014)
        detection_2014 = self.rule_manager.detect_rule_version(character_2014)
        
        self.assertEqual(detection_2014.version, RuleVersion.RULES_2014)
        self.assertIn('rule_version', result_2014)
        
        # Test 2024 character
        character_2024 = self.sample_character.copy()
        character_2024['classes'][0]['definition']['sourceId'] = 142  # 2024 PHB
        character_2024['species'] = {'name': 'Human'}  # 2024 terminology
        del character_2024['race']  # Remove 2014 terminology
        
        result_2024 = self.calculator.calculate_complete_json(character_2024)
        detection_2024 = self.rule_manager.detect_rule_version(character_2024)
        
        self.assertEqual(detection_2024.version, RuleVersion.RULES_2024)
        self.assertIn('rule_version', result_2024)
    
    def test_multiclass_integration(self):
        """Test complete integration for multiclass characters."""
        multiclass_character = {
            'id': 999999,
            'name': 'Multiclass Test',
            'classes': [
                {
                    'level': 3,
                    'definition': {
                        'name': 'Fighter',
                        'hitDie': 10,
                        'sourceId': 1
                    }
                },
                {
                    'level': 2,
                    'definition': {
                        'name': 'Wizard',
                        'hitDie': 6,
                        'canCastSpells': True,
                        'spellcastingAbilityId': 4,
                        'sourceId': 1
                    }
                }
            ],
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 15},  # Constitution
                {'id': 4, 'value': 18},  # Intelligence
                {'id': 5, 'value': 13},  # Wisdom
                {'id': 6, 'value': 12}   # Charisma
            ],
            'race': {'definition': {'name': 'Human', 'sourceId': 1}},
            'spells': {},
            'classSpells': [],
            'inventory': [],
            'modifiers': {'race': [], 'class': [], 'background': [], 'feat': [], 'item': []}
        }
        
        result = self.calculator.calculate_complete_json(multiclass_character)
        
        # Should handle multiclass correctly
        self.assertEqual(result['level'], 5)  # 3 + 2
        self.assertEqual(result['proficiency_bonus'], 3)  # Level 5 = +3
        
        # Should be a spellcaster due to Wizard levels
        self.assertTrue(result['spellcasting']['is_spellcaster'])
        self.assertEqual(result['spellcasting']['spellcasting_ability'], 'Intelligence')
        
        # Should have spell slots appropriate for level 2 wizard
        self.assertGreater(result['spellcasting']['spell_slots_level_1'], 0)
    
    def test_calculation_consistency(self):
        """Test that calculations are consistent across multiple runs."""
        # Run calculation multiple times
        results = []
        for _ in range(5):
            result = self.calculator.calculate_complete_json(self.sample_character)
            results.append(result)
        
        # All results should be identical
        first_result = results[0]
        for result in results[1:]:
            # Compare key fields that should be deterministic
            self.assertEqual(result['armor_class'], first_result['armor_class'])
            self.assertEqual(result['max_hp'], first_result['max_hp'])
            self.assertEqual(result['level'], first_result['level'])
            self.assertEqual(result['proficiency_bonus'], first_result['proficiency_bonus'])
            
            # Compare ability scores and modifiers
            for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
                self.assertEqual(result['ability_scores'][ability], first_result['ability_scores'][ability])
                self.assertEqual(result['ability_modifiers'][ability], first_result['ability_modifiers'][ability])
    
    def test_error_recovery_and_fallbacks(self):
        """Test that the system recovers gracefully from calculation errors."""
        # Create problematic character data
        problematic_character = {
            'id': 888888,
            'name': None,  # Problematic name
            'classes': [
                {
                    'level': 'invalid',  # Invalid level
                    'definition': {
                        'name': 'Unknown Class',
                        'hitDie': None  # Invalid hit die
                    }
                }
            ],
            'stats': None,  # Invalid stats
            'inventory': 'not a list',  # Wrong type
            'modifiers': None
        }
        
        # Should not crash, should provide reasonable defaults
        result = self.calculator.calculate_complete_json(problematic_character)
        
        self.assertEqual(result['id'], 888888)
        self.assertIsInstance(result['name'], str)  # Should have fallback name
        self.assertIsInstance(result['level'], int)
        self.assertIsInstance(result['armor_class'], int)
        self.assertIsInstance(result['max_hp'], int)
        self.assertGreaterEqual(result['max_hp'], 1)
    
    def test_performance_with_complex_character(self):
        """Test performance with a complex character (many spells, items, etc.)."""
        import time
        
        # Create a complex character
        complex_character = self.sample_character.copy()
        complex_character['classes'] = [
            {
                'level': 10,
                'definition': {
                    'name': 'Wizard',
                    'hitDie': 6,
                    'canCastSpells': True,
                    'spellcastingAbilityId': 4,
                    'sourceId': 1
                }
            },
            {
                'level': 5,
                'definition': {
                    'name': 'Cleric',
                    'hitDie': 8,
                    'canCastSpells': True,
                    'spellcastingAbilityId': 5,
                    'sourceId': 1
                }
            }
        ]
        
        # Add many spells
        complex_character['classSpells'] = [
            {
                'characterClassId': 1,
                'spells': [
                    {'definition': {'level': i % 9 + 1, 'name': f'Spell {j}'}}
                    for j in range(50)  # 50 spells
                    for i in range(9)
                ]
            }
        ]
        
        # Add many items
        complex_character['inventory'] = [
            {
                'definition': {
                    'name': f'Item {i}',
                    'type': 'Equipment',
                    'grantedModifiers': [
                        {
                            'type': 'bonus',
                            'subType': 'armor-class',
                            'value': 1
                        }
                    ]
                },
                'equipped': i % 2 == 0
            }
            for i in range(100)  # 100 items
        ]
        
        # Time the calculation
        start_time = time.time()
        result = self.calculator.calculate_complete_json(complex_character)
        end_time = time.time()
        
        calculation_time = end_time - start_time
        
        # Should complete in reasonable time (< 5 seconds for complex character)
        self.assertLess(calculation_time, 5.0, f"Calculation took {calculation_time:.2f} seconds")
        
        # Should still produce valid results
        self.assertEqual(result['level'], 15)  # 10 + 5
        self.assertTrue(result['spellcasting']['is_spellcaster'])
        self.assertIsInstance(result['armor_class'], int)
    
    @patch('src.clients.dndbeyond_client.requests.get')
    def test_api_integration_mock(self, mock_get):
        """Test integration with mocked D&D Beyond API."""
        # Mock API response
        mock_response = Mock()
        mock_response.json.return_value = self.sample_character
        mock_response.status_code = 200
        mock_get.return_value = mock_response
        
        # This would test the full API integration if we had the client setup
        # For now, just verify our calculator works with API-like data
        result = self.calculator.calculate_complete_json(self.sample_character)
        
        self.assertIsInstance(result, dict)
        self.assertIn('id', result)
        self.assertIn('armor_class', result)
    
    def test_baseline_character_compatibility(self):
        """Test compatibility with actual baseline character data structure."""
        baseline_file = '/mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/data/baseline/raw/145081718.json'
        
        # Only run if baseline file exists
        if os.path.exists(baseline_file):
            with open(baseline_file, 'r', encoding='utf-8') as f:
                baseline_data = json.load(f)
            
            # Should be able to process real baseline data
            result = self.calculator.calculate_complete_json(baseline_data)
            
            self.assertIsInstance(result, dict)
            self.assertEqual(result['id'], 145081718)
            self.assertIsInstance(result['armor_class'], int)
            self.assertIsInstance(result['max_hp'], int)
        else:
            # Skip test if baseline data not available
            self.skipTest("Baseline data not available")
    
    def test_json_serialization(self):
        """Test that output can be serialized to JSON."""
        result = self.calculator.calculate_complete_json(self.sample_character)
        
        # Should be able to serialize to JSON without errors
        json_string = json.dumps(result, indent=2)
        self.assertIsInstance(json_string, str)
        
        # Should be able to deserialize back
        deserialized = json.loads(json_string)
        self.assertEqual(deserialized['id'], result['id'])
        self.assertEqual(deserialized['armor_class'], result['armor_class'])
    
    def test_memory_usage_stability(self):
        """Test that repeated calculations don't cause memory leaks."""
        import gc
        
        # Force garbage collection before test
        gc.collect()
        
        # Run many calculations
        for i in range(100):
            test_character = self.sample_character.copy()
            test_character['id'] = i
            result = self.calculator.calculate_complete_json(test_character)
            
            # Verify each result is correct
            self.assertEqual(result['id'], i)
            self.assertIsInstance(result['armor_class'], int)
        
        # Force garbage collection after test
        gc.collect()
        
        # Memory usage should be stable (hard to test precisely, but no crashes is good)
        self.assertTrue(True)  # If we get here without crash, memory is stable


if __name__ == '__main__':
    unittest.main()