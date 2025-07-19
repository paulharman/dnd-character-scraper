import unittest
from unittest.mock import Mock, patch
from src.calculators.coordinators.resources import ResourcesCoordinator
from src.calculators.services.interfaces import CalculationContext, CalculationResult, CalculationStatus

class TestResourcesCoordinator(unittest.TestCase):
    def setUp(self):
        self.coordinator = ResourcesCoordinator()
        self.sample_raw_data = {
            'id': 12345,
            'name': 'Test Character',
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 2, 'value': 14},  # Dexterity
                {'id': 3, 'value': 15},  # Constitution
                {'id': 4, 'value': 12},  # Intelligence
                {'id': 5, 'value': 13},  # Wisdom
                {'id': 6, 'value': 18}   # Charisma
            ],
            'classes': [
                {'level': 5, 'definition': {'name': 'Monk'}},
                {'level': 3, 'definition': {'name': 'Bard'}}
            ],
            'resource_usage': {}
        }
    
    def test_coordinator_properties(self):
        """Test basic coordinator properties."""
        self.assertEqual(self.coordinator.coordinator_name, "resources")
        self.assertEqual(self.coordinator.dependencies, ["character_info", "abilities"])
        self.assertEqual(self.coordinator.priority, 35)
        self.assertEqual(self.coordinator.version, "1.0.0")
    
    def test_coordinate_basic_resources(self):
        """Test basic resource calculation."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3},
                    'dexterity': {'score': 14, 'modifier': 2},
                    'constitution': {'score': 15, 'modifier': 2},
                    'intelligence': {'score': 12, 'modifier': 1},
                    'wisdom': {'score': 13, 'modifier': 1},
                    'charisma': {'score': 18, 'modifier': 4}
                }
            },
            'character_info': {
                'level': 8,
                'proficiency_bonus': 3
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        self.assertEqual(result.status, CalculationStatus.COMPLETED)
        self.assertIn('class_resources', result.data)
        self.assertIn('resources_by_class', result.data)
        self.assertIn('resources_by_rest_type', result.data)
        self.assertIn('total_resources', result.data)
        self.assertIn('depleted_resources', result.data)
        
        # Should have resources from both Monk and Bard
        self.assertGreater(result.data['total_resources'], 0)
        self.assertTrue(result.data['has_resources'])
    
    def test_multiclass_resources(self):
        """Test resources for multiclass character."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 16, 'modifier': 3},
                    'charisma': {'score': 18, 'modifier': 4}
                }
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        class_resources = result.data['class_resources']
        resources_by_class = result.data['resources_by_class']
        
        # Should have resources from both classes
        self.assertIn('Monk', resources_by_class)
        self.assertIn('Bard', resources_by_class)
        
        # Find Ki Points and Bardic Inspiration
        resource_names = [r['name'] for r in class_resources]
        self.assertIn('Ki Points', resource_names)
        self.assertIn('Bardic Inspiration', resource_names)
        
        # Check Ki Points (Monk level 5)
        ki_points = next(r for r in class_resources if r['name'] == 'Ki Points')
        self.assertEqual(ki_points['class'], 'Monk')
        self.assertEqual(ki_points['maximum'], 4)  # Level 5 - 2 + 1 = 4
        self.assertEqual(ki_points['recharge_on'], 'short_rest')
        self.assertTrue(ki_points['level_based'])
        
        # Check Bardic Inspiration (Bard level 3, CHA +4)
        bardic_inspiration = next(r for r in class_resources if r['name'] == 'Bardic Inspiration')
        self.assertEqual(bardic_inspiration['class'], 'Bard')
        self.assertEqual(bardic_inspiration['maximum'], 4)  # CHA modifier
        self.assertEqual(bardic_inspiration['recharge_on'], 'short_rest')
        self.assertTrue(bardic_inspiration['ability_based'])
        self.assertEqual(bardic_inspiration['ability_name'], 'charisma')
    
    def test_resources_by_rest_type(self):
        """Test organization of resources by rest type."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 16, 'modifier': 3},
                    'charisma': {'score': 18, 'modifier': 4}
                }
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        resources_by_rest_type = result.data['resources_by_rest_type']
        
        # Should have short rest resources
        self.assertIn('short_rest', resources_by_rest_type)
        short_rest_resources = resources_by_rest_type['short_rest']
        
        # Ki Points and Bardic Inspiration are both short rest resources
        short_rest_names = [r['name'] for r in short_rest_resources]
        self.assertIn('Ki Points', short_rest_names)
        self.assertIn('Bardic Inspiration', short_rest_names)
        
        # Check counts
        self.assertEqual(result.data['short_rest_count'], len(short_rest_resources))
        self.assertGreaterEqual(result.data['short_rest_count'], 2)
    
    def test_resource_usage_tracking(self):
        """Test resource usage tracking."""
        # Add resource usage to raw data
        raw_data_with_usage = self.sample_raw_data.copy()
        raw_data_with_usage['resource_usage'] = {
            'monk': {
                'ki_points': 2  # Used 2 Ki points
            },
            'bard': {
                'bardic_inspiration': 3  # Used 3 Bardic Inspiration
            }
        }
        
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 16, 'modifier': 3},
                    'charisma': {'score': 18, 'modifier': 4}
                }
            }
        }
        
        result = self.coordinator.coordinate(raw_data_with_usage, context)
        
        class_resources = result.data['class_resources']
        
        # Check Ki Points usage
        ki_points = next(r for r in class_resources if r['name'] == 'Ki Points')
        self.assertEqual(ki_points['maximum'], 4)
        self.assertEqual(ki_points['used'], 2)
        self.assertEqual(ki_points['remaining'], 2)
        self.assertEqual(ki_points['usage_fraction'], "2/4")
        self.assertFalse(ki_points['is_depleted'])
        
        # Check Bardic Inspiration usage
        bardic_inspiration = next(r for r in class_resources if r['name'] == 'Bardic Inspiration')
        self.assertEqual(bardic_inspiration['maximum'], 4)
        self.assertEqual(bardic_inspiration['used'], 3)
        self.assertEqual(bardic_inspiration['remaining'], 1)
        self.assertEqual(bardic_inspiration['usage_fraction'], "1/4")
        self.assertFalse(bardic_inspiration['is_depleted'])
    
    def test_depleted_resources(self):
        """Test detection of depleted resources."""
        # Add resource usage that depletes resources
        raw_data_depleted = self.sample_raw_data.copy()
        raw_data_depleted['resource_usage'] = {
            'monk': {
                'ki_points': 4  # Used all 4 Ki points
            }
        }
        
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 16, 'modifier': 3},
                    'charisma': {'score': 18, 'modifier': 4}
                }
            }
        }
        
        result = self.coordinator.coordinate(raw_data_depleted, context)
        
        # Should detect depleted resources
        depleted_resources = result.data['depleted_resources']
        self.assertIn('Ki Points', depleted_resources)
        self.assertTrue(result.data['has_depleted_resources'])
        
        # Check the depleted resource
        class_resources = result.data['class_resources']
        ki_points = next(r for r in class_resources if r['name'] == 'Ki Points')
        self.assertTrue(ki_points['is_depleted'])
        self.assertEqual(ki_points['remaining'], 0)
    
    def test_simulate_rest(self):
        """Test rest simulation functionality."""
        # Set up character with used resources
        raw_data_with_usage = self.sample_raw_data.copy()
        raw_data_with_usage['resource_usage'] = {
            'monk': {'ki_points': 3},
            'bard': {'bardic_inspiration': 2}
        }
        
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 16, 'modifier': 3},
                    'charisma': {'score': 18, 'modifier': 4}
                }
            }
        }
        
        # Test short rest
        short_rest_result = self.coordinator.simulate_rest(raw_data_with_usage, context, 'short_rest')
        
        self.assertEqual(short_rest_result['rest_type'], 'short_rest')
        self.assertIn('restored_resources', short_rest_result)
        self.assertIn('class_resources', short_rest_result)
        
        # Both Ki Points and Bardic Inspiration should be restored (both are short rest resources)
        restored = short_rest_result['restored_resources']
        self.assertIn('Ki Points', restored)
        self.assertIn('Bardic Inspiration', restored)
        
        # Check that resources are restored
        resources = short_rest_result['class_resources']
        ki_points = next(r for r in resources if r['name'] == 'Ki Points')
        bardic_inspiration = next(r for r in resources if r['name'] == 'Bardic Inspiration')
        
        self.assertEqual(ki_points['used'], 0)
        self.assertEqual(ki_points['current'], ki_points['maximum'])
        self.assertEqual(bardic_inspiration['used'], 0)
        self.assertEqual(bardic_inspiration['current'], bardic_inspiration['maximum'])
    
    def test_fallback_ability_calculation(self):
        """Test fallback ability calculation when context is missing."""
        # Test without context (should calculate from raw data)
        result = self.coordinator.coordinate(self.sample_raw_data, None)
        
        self.assertEqual(result.status, CalculationStatus.COMPLETED)
        
        # Should still have resources
        self.assertGreater(result.data['total_resources'], 0)
        
        # Check that abilities were calculated from raw stats
        class_resources = result.data['class_resources']
        bardic_inspiration = next((r for r in class_resources if r['name'] == 'Bardic Inspiration'), None)
        
        if bardic_inspiration:
            self.assertEqual(bardic_inspiration['ability_name'], 'charisma')
            self.assertEqual(bardic_inspiration['ability_modifier'], 4)  # (18-10)//2 = 4
    
    def test_no_resources_character(self):
        """Test character with no class resources."""
        # Test with a class that has no resources at low level
        raw_data_no_resources = {
            'id': 12345,
            'stats': [
                {'id': 1, 'value': 16},  # Strength
                {'id': 6, 'value': 10}   # Charisma
            ],
            'classes': [
                {'level': 1, 'definition': {'name': 'Fighter'}}  # Fighter level 1 has Second Wind
            ],
            'resource_usage': {}
        }
        
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 16, 'modifier': 3},
                    'charisma': {'score': 10, 'modifier': 0}
                }
            }
        }
        
        result = self.coordinator.coordinate(raw_data_no_resources, context)
        
        self.assertEqual(result.status, CalculationStatus.COMPLETED)
        
        # Fighter level 1 should have Second Wind
        self.assertGreater(result.data['total_resources'], 0)
        
        class_resources = result.data['class_resources']
        resource_names = [r['name'] for r in class_resources]
        self.assertIn('Second Wind', resource_names)
    
    def test_error_handling(self):
        """Test error handling with invalid data."""
        # Test with empty data
        result = self.coordinator.coordinate({}, None)
        
        # Should handle gracefully (might fail validation but shouldn't crash)
        self.assertIn(result.status, [CalculationStatus.FAILED, CalculationStatus.COMPLETED])
    
    def test_invalid_rest_simulation(self):
        """Test rest simulation with invalid rest type."""
        context = Mock(spec=CalculationContext)
        context.metadata = {'abilities': {'ability_scores': {}}}
        
        result = self.coordinator.simulate_rest(self.sample_raw_data, context, 'invalid_rest')
        
        self.assertEqual(result['rest_type'], 'invalid_rest')
        self.assertIn('error', result)
        self.assertEqual(result['restored_resources'], [])
    
    def test_health_check(self):
        """Test coordinator health check."""
        health = self.coordinator.health_check()
        
        self.assertEqual(health['status'], 'healthy')
        self.assertEqual(health['name'], 'resources')
        self.assertEqual(health['version'], '1.0.0')
        self.assertTrue(health['calculator_available'])
    
    def test_metadata_generation(self):
        """Test resource metadata generation."""
        context = Mock(spec=CalculationContext)
        context.metadata = {
            'abilities': {
                'ability_scores': {
                    'wisdom': {'score': 16, 'modifier': 3},
                    'charisma': {'score': 18, 'modifier': 4}
                }
            }
        }
        
        result = self.coordinator.coordinate(self.sample_raw_data, context)
        
        metadata = result.data['resources_metadata']
        self.assertIn('calculation_method', metadata)
        self.assertIn('total_resources', metadata)
        self.assertIn('total_classes_with_resources', metadata)
        self.assertIn('short_rest_resources', metadata)
        self.assertIn('long_rest_resources', metadata)
        self.assertIn('coordinator_version', metadata)
        
        self.assertEqual(metadata['calculation_method'], 'class_resource_calculator')
        self.assertEqual(metadata['coordinator_version'], '1.0.0')
        self.assertGreater(metadata['total_resources'], 0)

if __name__ == '__main__':
    unittest.main()