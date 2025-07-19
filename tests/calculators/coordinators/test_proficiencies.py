import unittest
from unittest.mock import Mock, patch
from src.calculators.coordinators.proficiencies import ProficienciesCoordinator
from src.calculators.services.interfaces import CalculationContext, CalculationResult, CalculationStatus

class TestProficienciesCoordinator(unittest.TestCase):
    def setUp(self):
        self.coordinator = ProficienciesCoordinator()
        self.sample_raw_data = {
            'id': 12345,
            'name': 'Test Character',
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 15},  # Constitution
                {'id': 4, 'value': 12},  # Intelligence
                {'id': 5, 'value': 13},  # Wisdom
                {'id': 6, 'value': 10}   # Charisma
            ],
            'classes': [
                {'level': 5, 'definition': {'name': 'Rogue'}}
            ],
            'modifiers': {
                'class': [
                    {
                        'type': 'proficiency',
                        'subType': 'skill',
                        'friendlySubtypeName': 'Stealth'
                    },
                    {
                        'type': 'proficiency',
                        'subType': 'skill',
                        'friendlySubtypeName': 'Sleight of Hand'
                    },
                    {
                        'type': 'expertise',
                        'subType': 'skill',
                        'friendlySubtypeName': 'Stealth'
                    }
                ]
            }
        }
    
    def test_coordinator_properties(self):
        """Test basic coordinator properties."""
        self.assertEqual(self.coordinator.coordinator_name, "proficiencies")
        self.assertEqual(self.coordinator.dependencies, ["character_info", "abilities"])
        self.assertEqual(self.coordinator.priority, 25)
        self.assertEqual(self.coordinator.version, "1.1.0")
    
    def test_coordinate_basic_proficiencies(self):
        """Test basic proficiencies calculation."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3},
                    'dexterity': {'score': 14, 'modifier': 2},
                    'constitution': {'score': 15, 'modifier': 2},
                    'intelligence': {'score': 12, 'modifier': 1},
                    'wisdom': {'score': 13, 'modifier': 1},
                    'charisma': {'score': 10, 'modifier': 0}
                }
            },
            'character_info': {
                'level': 5,
                'proficiency_bonus': 3
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        self.assertEqual(result.status, CalculationStatus.COMPLETED)
        self.assertIn('skill_proficiencies', result.data)
        self.assertIn('tool_proficiencies', result.data)
        self.assertIn('language_proficiencies', result.data)
        self.assertIn('weapon_proficiencies', result.data)
        self.assertIn('proficiency_bonus', result.data)
        self.assertIn('enhanced_skill_bonuses', result.data)
        
        # Check proficiency bonus
        self.assertEqual(result.data['proficiency_bonus'], 3)
    
    def test_enhanced_skill_bonuses_integration(self):
        """Test that enhanced skill bonuses are calculated and integrated."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3},
                    'dexterity': {'score': 14, 'modifier': 2},
                    'constitution': {'score': 15, 'modifier': 2},
                    'intelligence': {'score': 12, 'modifier': 1},
                    'wisdom': {'score': 13, 'modifier': 1},
                    'charisma': {'score': 10, 'modifier': 0}
                }
            },
            'character_info': {
                'level': 5,
                'proficiency_bonus': 3
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        # Should have enhanced skill bonuses
        enhanced_skills = result.data['enhanced_skill_bonuses']
        self.assertIsInstance(enhanced_skills, list)
        self.assertEqual(len(enhanced_skills), 18)  # All 18 D&D skills
        
        # Check specific skill structure
        stealth_skill = next((skill for skill in enhanced_skills if skill['name'] == 'Stealth'), None)
        self.assertIsNotNone(stealth_skill)
        
        # Verify skill structure
        self.assertIn('name', stealth_skill)
        self.assertIn('ability', stealth_skill)
        self.assertIn('ability_modifier', stealth_skill)
        self.assertIn('proficiency_bonus', stealth_skill)
        self.assertIn('expertise_bonus', stealth_skill)
        self.assertIn('total_bonus', stealth_skill)
        self.assertIn('is_proficient', stealth_skill)
        self.assertIn('has_expertise', stealth_skill)
        self.assertIn('bonus_expression', stealth_skill)
        
        # Check stealth skill values (should be proficient and have expertise)
        self.assertEqual(stealth_skill['ability'], 'dexterity')
        self.assertEqual(stealth_skill['ability_modifier'], 2)
        self.assertTrue(stealth_skill['is_proficient'])
        self.assertTrue(stealth_skill['has_expertise'])
        self.assertEqual(stealth_skill['total_bonus'], 8)  # 2 (DEX) + 3 (Prof) + 3 (Expertise)
    
    def test_passive_skills_calculation(self):
        """Test passive skills calculation using enhanced skill bonuses."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3},
                    'dexterity': {'score': 14, 'modifier': 2},
                    'constitution': {'score': 15, 'modifier': 2},
                    'intelligence': {'score': 12, 'modifier': 1},
                    'wisdom': {'score': 13, 'modifier': 1},
                    'charisma': {'score': 10, 'modifier': 0}
                }
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        # Check passive skills
        self.assertIn('passive_perception', result.data)
        self.assertIn('passive_investigation', result.data)
        self.assertIn('passive_insight', result.data)
        
        # Passive perception should be 10 + WIS modifier (no proficiency)
        self.assertEqual(result.data['passive_perception'], 11)  # 10 + 1
        
        # Passive investigation should be 10 + INT modifier (no proficiency)
        self.assertEqual(result.data['passive_investigation'], 11)  # 10 + 1
        
        # Passive insight should be 10 + WIS modifier (no proficiency)
        self.assertEqual(result.data['passive_insight'], 11)  # 10 + 1
    
    def test_skill_proficiency_detection(self):
        """Test skill proficiency detection from modifiers."""
        # Test data with skill proficiencies
        raw_data_with_skills = self.sample_raw_data.copy()
        raw_data_with_skills['modifiers'] = {
            'class': [
                {
                    'type': 'proficiency',
                    'subType': 'skill',
                    'friendlySubtypeName': 'Perception'
                },
                {
                    'type': 'proficiency',
                    'subType': 'skill',
                    'friendlySubtypeName': 'Investigation'
                }
            ]
        }
        
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 15, 'modifier': 2},
                    'intelligence': {'score': 14, 'modifier': 2}
                }
            }
        }
        
        result = self.coordinator.coordinate(raw_data_with_skills, context)
        
        enhanced_skills = result.data['enhanced_skill_bonuses']
        
        # Find perception and investigation skills
        perception = next((skill for skill in enhanced_skills if skill['name'] == 'Perception'), None)
        investigation = next((skill for skill in enhanced_skills if skill['name'] == 'Investigation'), None)
        
        self.assertIsNotNone(perception)
        self.assertIsNotNone(investigation)
        
        # Both should be proficient
        self.assertTrue(perception['is_proficient'])
        self.assertTrue(investigation['is_proficient'])
        
        # Check passive skills with proficiency
        self.assertEqual(result.data['passive_perception'], 15)  # 10 + 2 (WIS) + 3 (Prof)
        self.assertEqual(result.data['passive_investigation'], 15)  # 10 + 2 (INT) + 3 (Prof)
    
    def test_expertise_detection(self):
        """Test expertise detection from modifiers."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'dexterity': {'score': 16, 'modifier': 3}
                }
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        enhanced_skills = result.data['enhanced_skill_bonuses']
        
        # Find stealth skill (should have expertise from sample data)
        stealth = next((skill for skill in enhanced_skills if skill['name'] == 'Stealth'), None)
        self.assertIsNotNone(stealth)
        
        # Should have expertise
        self.assertTrue(stealth['has_expertise'])
        self.assertEqual(stealth['expertise_bonus'], 3)  # Same as proficiency bonus
        
        # Total should include expertise
        expected_total = 3 + 3 + 3  # DEX + Prof + Expertise
        self.assertEqual(stealth['total_bonus'], expected_total)
    
    def test_fallback_ability_calculation(self):
        """Test fallback ability calculation when context is missing."""
        # Test without context (should calculate from raw data)
        result = self.coordinator.coordinate(self.sample_raw_data, None)
        
        self.assertEqual(result.status, CalculationStatus.COMPLETED)
        
        # Should still have enhanced skill bonuses
        enhanced_skills = result.data['enhanced_skill_bonuses']
        self.assertIsInstance(enhanced_skills, list)
        self.assertEqual(len(enhanced_skills), 18)
        
        # Check that abilities were calculated from raw stats
        athletics = next((skill for skill in enhanced_skills if skill['name'] == 'Athletics'), None)
        self.assertIsNotNone(athletics)
        self.assertEqual(athletics['ability'], 'strength')
        self.assertEqual(athletics['ability_modifier'], 3)  # (16-10)//2 = 3
    
    def test_error_handling(self):
        """Test error handling with invalid data."""
        # Test with empty data
        result = self.coordinator.coordinate({}, None)
        
        # Should handle gracefully (might fail validation but shouldn't crash)
        self.assertIn(result.status, [CalculationStatus.FAILED, CalculationStatus.COMPLETED])
    
    def test_skill_name_normalization(self):
        """Test that skill names are properly normalized and formatted."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'dexterity': {'score': 14, 'modifier': 2}
                }
            }
        }
        
        # Test data with "Sleight of Hand" skill
        raw_data = self.sample_raw_data.copy()
        raw_data['modifiers'] = {
            'class': [
                {
                    'type': 'proficiency',
                    'subType': 'skill',
                    'friendlySubtypeName': 'Sleight of Hand'
                }
            ]
        }
        
        result = self.coordinator.coordinate(raw_data, context)
        
        enhanced_skills = result.data['enhanced_skill_bonuses']
        
        # Should find "Sleight Of Hand" skill (properly formatted)
        sleight_skill = next((skill for skill in enhanced_skills if skill['name'] == 'Sleight Of Hand'), None)
        self.assertIsNotNone(sleight_skill)
        self.assertTrue(sleight_skill['is_proficient'])
    
    def test_health_check(self):
        """Test coordinator health check."""
        health = self.coordinator.health_check()
        
        self.assertEqual(health['status'], 'healthy')
        self.assertEqual(health['name'], 'proficiencies')
        self.assertEqual(health['version'], '1.1.0')
        self.assertTrue(health['calculator_available'])

if __name__ == '__main__':
    unittest.main()