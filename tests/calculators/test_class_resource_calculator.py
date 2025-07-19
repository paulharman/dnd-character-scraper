import unittest
from src.calculators.class_resource_calculator import ClassResourceCalculator, ClassResource, RestType

class TestClassResourceCalculator(unittest.TestCase):
    def setUp(self):
        self.calculator = ClassResourceCalculator()
    
    def test_monk_ki_points(self):
        """Test Ki points calculation for Monk."""
        character_data = {
            'classes': [
                {'name': 'Monk', 'level': 5}
            ],
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 16, 'modifier': 3}
                }
            },
            'character_info': {
                'level': 5
            },
            'resource_usage': {}
        }
        
        result = self.calculator.calculate(character_data)
        resources = result['class_resources']
        
        # Should have Ki points
        self.assertEqual(len(resources), 1)
        ki_points = resources[0]
        
        self.assertEqual(ki_points.resource_name, 'Ki Points')
        self.assertEqual(ki_points.class_name, 'Monk')
        self.assertEqual(ki_points.maximum, 4)  # Level 5 - 2 + 1 = 4 Ki points
        self.assertEqual(ki_points.current, 4)  # No usage
        self.assertEqual(ki_points.recharge_on, RestType.SHORT_REST)
        self.assertTrue(ki_points.level_based)
        self.assertFalse(ki_points.ability_based)
    
    def test_sorcerer_sorcery_points(self):
        """Test Sorcery points calculation for Sorcerer."""
        character_data = {
            'classes': [
                {'name': 'Sorcerer', 'level': 6}
            ],
            'abilities': {
                'ability_scores': {
                    'charisma': {'score': 18, 'modifier': 4}
                }
            },
            'resource_usage': {}
        }
        
        result = self.calculator.calculate(character_data)
        resources = result['class_resources']
        
        # Should have Sorcery points
        self.assertEqual(len(resources), 1)
        sorcery_points = resources[0]
        
        self.assertEqual(sorcery_points.resource_name, 'Sorcery Points')
        self.assertEqual(sorcery_points.class_name, 'Sorcerer')
        self.assertEqual(sorcery_points.maximum, 5)  # Level 6 - 2 + 1 = 5 Sorcery points
        self.assertEqual(sorcery_points.recharge_on, RestType.LONG_REST)
        self.assertTrue(sorcery_points.level_based)
    
    def test_bard_bardic_inspiration(self):
        """Test Bardic Inspiration calculation for Bard."""
        character_data = {
            'classes': [
                {'name': 'Bard', 'level': 3}
            ],
            'abilities': {
                'ability_scores': {
                    'charisma': {'score': 16, 'modifier': 3}
                }
            },
            'resource_usage': {}
        }
        
        result = self.calculator.calculate(character_data)
        resources = result['class_resources']
        
        # Should have Bardic Inspiration
        self.assertEqual(len(resources), 1)
        bardic_inspiration = resources[0]
        
        self.assertEqual(bardic_inspiration.resource_name, 'Bardic Inspiration')
        self.assertEqual(bardic_inspiration.class_name, 'Bard')
        self.assertEqual(bardic_inspiration.maximum, 3)  # CHA modifier
        self.assertEqual(bardic_inspiration.ability_name, 'charisma')
        self.assertEqual(bardic_inspiration.ability_modifier, 3)
        self.assertEqual(bardic_inspiration.recharge_on, RestType.SHORT_REST)
        self.assertTrue(bardic_inspiration.ability_based)
    
    def test_barbarian_rage(self):
        """Test Rage calculation for Barbarian."""
        character_data = {
            'classes': [
                {'name': 'Barbarian', 'level': 6}
            ],
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 18, 'modifier': 4}
                }
            },
            'resource_usage': {}
        }
        
        result = self.calculator.calculate(character_data)
        resources = result['class_resources']
        
        # Should have Rage
        self.assertEqual(len(resources), 1)
        rage = resources[0]
        
        self.assertEqual(rage.resource_name, 'Rage')
        self.assertEqual(rage.class_name, 'Barbarian')
        self.assertEqual(rage.maximum, 4)  # Level 6 = 4 rages
        self.assertEqual(rage.recharge_on, RestType.LONG_REST)
        self.assertTrue(rage.level_based)
    
    def test_cleric_channel_divinity(self):
        """Test Channel Divinity calculation for Cleric."""
        character_data = {
            'classes': [
                {'name': 'Cleric', 'level': 8}
            ],
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 16, 'modifier': 3}
                }
            },
            'resource_usage': {}
        }
        
        result = self.calculator.calculate(character_data)
        resources = result['class_resources']
        
        # Should have Channel Divinity
        self.assertEqual(len(resources), 1)
        channel_divinity = resources[0]
        
        self.assertEqual(channel_divinity.resource_name, 'Channel Divinity')
        self.assertEqual(channel_divinity.class_name, 'Cleric')
        self.assertEqual(channel_divinity.maximum, 2)  # Level 8 = 2 uses
        self.assertEqual(channel_divinity.recharge_on, RestType.SHORT_REST)
    
    def test_fighter_multiple_resources(self):
        """Test multiple resources for Fighter."""
        character_data = {
            'classes': [
                {'name': 'Fighter', 'level': 5}
            ],
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3}
                }
            },
            'resource_usage': {}
        }
        
        result = self.calculator.calculate(character_data)
        resources = result['class_resources']
        
        # Should have Action Surge and Second Wind
        self.assertEqual(len(resources), 2)
        
        resource_names = [r.resource_name for r in resources]
        self.assertIn('Action Surge', resource_names)
        self.assertIn('Second Wind', resource_names)
        
        # Check Action Surge
        action_surge = next(r for r in resources if r.resource_name == 'Action Surge')
        self.assertEqual(action_surge.maximum, 1)  # Level 5 = 1 use
        self.assertEqual(action_surge.recharge_on, RestType.SHORT_REST)
        
        # Check Second Wind
        second_wind = next(r for r in resources if r.resource_name == 'Second Wind')
        self.assertEqual(second_wind.maximum, 1)  # Always 1 use
        self.assertEqual(second_wind.recharge_on, RestType.SHORT_REST)
    
    def test_multiclass_resources(self):
        """Test resources for multiclass character."""
        character_data = {
            'classes': [
                {'name': 'Monk', 'level': 3},
                {'name': 'Barbarian', 'level': 2}
            ],
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 14, 'modifier': 2},
                    'strength': {'score': 16, 'modifier': 3}
                }
            },
            'resource_usage': {}
        }
        
        result = self.calculator.calculate(character_data)
        resources = result['class_resources']
        
        # Should have Ki points and Rage
        self.assertEqual(len(resources), 2)
        
        resource_names = [r.resource_name for r in resources]
        self.assertIn('Ki Points', resource_names)
        self.assertIn('Rage', resource_names)
        
        # Check Ki points (Monk level 3)
        ki_points = next(r for r in resources if r.resource_name == 'Ki Points')
        self.assertEqual(ki_points.maximum, 2)  # Level 3 - 2 + 1 = 2
        
        # Check Rage (Barbarian level 2)
        rage = next(r for r in resources if r.resource_name == 'Rage')
        self.assertEqual(rage.maximum, 2)  # Level 2 = 2 rages (level 1 gives 2)
    
    def test_calculate_specific_resource(self):
        """Test calculating a specific resource."""
        character_data = {
            'classes': [
                {'name': 'Monk', 'level': 4}
            ],
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 16, 'modifier': 3}
                }
            },
            'resource_usage': {}
        }
        
        ki_points = self.calculator.calculate_specific_resource('monk', 'ki_points', character_data)
        
        self.assertIsNotNone(ki_points)
        self.assertEqual(ki_points.resource_name, 'Ki Points')
        self.assertEqual(ki_points.maximum, 3)  # Level 4 - 2 + 1 = 3
        
        # Test invalid resource
        invalid_resource = self.calculator.calculate_specific_resource('monk', 'invalid_resource', character_data)
        self.assertIsNone(invalid_resource)
        
        # Test invalid class
        invalid_class = self.calculator.calculate_specific_resource('invalid_class', 'ki_points', character_data)
        self.assertIsNone(invalid_class)
    
    def test_resource_usage_tracking(self):
        """Test resource usage tracking."""
        character_data = {
            'classes': [
                {'name': 'Monk', 'level': 5}
            ],
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 16, 'modifier': 3}
                }
            },
            'resource_usage': {
                'monk': {
                    'ki_points': 2  # Used 2 Ki points
                }
            }
        }
        
        result = self.calculator.calculate(character_data)
        resources = result['class_resources']
        
        ki_points = resources[0]
        self.assertEqual(ki_points.maximum, 4)
        self.assertEqual(ki_points.used, 2)
        self.assertEqual(ki_points.current, 2)
        self.assertEqual(ki_points.remaining, 2)
        self.assertFalse(ki_points.is_depleted)
        self.assertEqual(ki_points.usage_fraction, "2/4")
    
    def test_resource_depletion(self):
        """Test resource depletion detection."""
        character_data = {
            'classes': [
                {'name': 'Barbarian', 'level': 3}
            ],
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3}
                }
            },
            'resource_usage': {
                'barbarian': {
                    'rage': 3  # Used all 3 rages
                }
            }
        }
        
        result = self.calculator.calculate(character_data)
        resources = result['class_resources']
        
        rage = resources[0]
        self.assertEqual(rage.maximum, 3)
        self.assertEqual(rage.used, 3)
        self.assertEqual(rage.remaining, 0)
        self.assertTrue(rage.is_depleted)
        self.assertEqual(rage.usage_fraction, "0/3")
    
    def test_minimum_level_requirements(self):
        """Test that resources respect minimum level requirements."""
        character_data = {
            'classes': [
                {'name': 'Monk', 'level': 1}  # Below minimum level for Ki
            ],
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 16, 'modifier': 3}
                }
            },
            'resource_usage': {}
        }
        
        result = self.calculator.calculate(character_data)
        resources = result['class_resources']
        
        # Should have no resources (Ki requires level 2)
        self.assertEqual(len(resources), 0)
    
    def test_ability_based_minimum(self):
        """Test that ability-based resources have minimum 1 use."""
        character_data = {
            'classes': [
                {'name': 'Bard', 'level': 3}
            ],
            'abilities': {
                'ability_scores': {
                    'charisma': {'score': 8, 'modifier': -1}  # Negative modifier
                }
            },
            'resource_usage': {}
        }
        
        result = self.calculator.calculate(character_data)
        resources = result['class_resources']
        
        bardic_inspiration = resources[0]
        self.assertEqual(bardic_inspiration.maximum, 1)  # Minimum 1 even with negative modifier
    
    def test_get_resources_by_class(self):
        """Test getting resources by class name."""
        monk_resources = self.calculator.get_resources_by_class('monk')
        self.assertEqual(monk_resources, ['ki_points'])
        
        fighter_resources = self.calculator.get_resources_by_class('fighter')
        self.assertIn('action_surge', fighter_resources)
        self.assertIn('second_wind', fighter_resources)
        
        invalid_resources = self.calculator.get_resources_by_class('invalid_class')
        self.assertEqual(invalid_resources, [])
    
    def test_get_resources_by_rest_type(self):
        """Test getting resources by rest type."""
        short_rest_resources = self.calculator.get_resources_by_rest_type(RestType.SHORT_REST)
        
        # Should include Ki points, Channel Divinity, Action Surge, etc.
        self.assertIn('monk', short_rest_resources)
        self.assertIn('ki_points', short_rest_resources['monk'])
        
        long_rest_resources = self.calculator.get_resources_by_rest_type(RestType.LONG_REST)
        
        # Should include Sorcery points, Rage, etc.
        self.assertIn('sorcerer', long_rest_resources)
        self.assertIn('sorcery_points', long_rest_resources['sorcerer'])
    
    def test_simulate_rest(self):
        """Test rest simulation and resource restoration."""
        character_data = {
            'classes': [
                {'name': 'Monk', 'level': 5},
                {'name': 'Barbarian', 'level': 3}
            ],
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 16, 'modifier': 3},
                    'strength': {'score': 16, 'modifier': 3}
                }
            },
            'resource_usage': {
                'monk': {'ki_points': 3},  # Used 3 Ki points
                'barbarian': {'rage': 2}   # Used 2 rages
            }
        }
        
        # Test short rest
        short_rest_result = self.calculator.simulate_rest(character_data, RestType.SHORT_REST)
        
        # Ki points should be restored (short rest resource)
        ki_points = next(r for r in short_rest_result['class_resources'] if r.resource_name == 'Ki Points')
        self.assertEqual(ki_points.used, 0)
        self.assertEqual(ki_points.current, ki_points.maximum)
        
        # Rage should NOT be restored (long rest resource)
        rage = next(r for r in short_rest_result['class_resources'] if r.resource_name == 'Rage')
        self.assertEqual(rage.used, 2)  # Still used
        
        self.assertIn('Ki Points', short_rest_result['restored_resources'])
        self.assertNotIn('Rage', short_rest_result['restored_resources'])
        
        # Test long rest (should restore everything)
        long_rest_result = self.calculator.simulate_rest(character_data, RestType.LONG_REST)
        
        # Both should be restored
        restored_names = long_rest_result['restored_resources']
        self.assertIn('Ki Points', restored_names)
        self.assertIn('Rage', restored_names)

if __name__ == '__main__':
    unittest.main()