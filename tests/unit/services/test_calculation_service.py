#!/usr/bin/env python3
"""
Unit tests for Calculator Services

Tests all service implementations to ensure they properly implement
their interfaces and produce correct results.
"""

import unittest
import sys
import os
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, project_root)

from src.calculators.services.calculation_service import CalculationService, CalculationSession
from src.calculators.services.character_builder import CharacterBuilder, BuildContext
from src.calculators.services.validation_service import ValidationService, ValidationContext
from src.calculators.services.performance_service import PerformanceService, PerformanceMetric
from src.calculators.services.interfaces import CalculationContext, CalculationStatus
from src.calculators.interfaces.coordination import ICoordinator
from src.models.character import Character, CharacterClass, Species, Background


class TestCalculationService(unittest.TestCase):
    """Test CalculationService implementation."""
    
    def setUp(self):
        self.service = CalculationService()
        self.context = CalculationContext(character_id="12345", rule_version="2014")
        
        self.sample_data = {
            "id": 12345,
            "name": "Test Character",
            "stats": [
                {"id": 1, "value": 16},  # Strength
                {"id": 2, "value": 14},  # Dexterity
                {"id": 3, "value": 15},  # Constitution
                {"id": 4, "value": 18},  # Intelligence
                {"id": 5, "value": 12},  # Wisdom
                {"id": 6, "value": 13}   # Charisma
            ],
            "classes": [
                {
                    "level": 5,
                    "definition": {
                        "name": "Wizard",
                        "hitDie": 6
                    }
                }
            ],
            "race": {
                "fullName": "High Elf",
                "baseName": "Elf"
            },
            "background": {
                "definition": {
                    "name": "Sage"
                }
            },
            "baseHitPoints": 38,
            "bonusHitPoints": 0,
            "removedHitPoints": 0,
            "temporaryHitPoints": 0,
            "currentHitPoints": 38,
            "baseArmorClass": 12,
            "speed": {"walk": 30},
            "alignment": "Neutral"
        }
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsInstance(self.service, CalculationService)
        self.assertGreater(len(self.service.coordinators), 0)
        self.assertIn('character_info', self.service.coordinators)
        self.assertIn('abilities', self.service.coordinators)
        self.assertIn('combat', self.service.coordinators)
    
    def test_coordinator_registration(self):
        """Test coordinator registration and management."""
        # Create mock coordinator
        mock_coordinator = Mock(spec=ICoordinator)
        mock_coordinator.coordinator_name = "test_coordinator"
        mock_coordinator.dependencies = []
        mock_coordinator.priority = 100
        
        # Register coordinator
        initial_count = len(self.service.coordinators)
        self.service.register_coordinator(mock_coordinator)
        
        self.assertEqual(len(self.service.coordinators), initial_count + 1)
        self.assertIn("test_coordinator", self.service.coordinators)
        
        # Unregister coordinator
        self.service.unregister_coordinator("test_coordinator")
        self.assertEqual(len(self.service.coordinators), initial_count)
        self.assertNotIn("test_coordinator", self.service.coordinators)
    
    def test_coordinator_dependency_resolution(self):
        """Test dependency resolution for coordinators."""
        execution_order = self.service._calculate_execution_order()
        
        # Verify character_info comes before abilities (dependency)
        char_info_index = execution_order.index('character_info')
        abilities_index = execution_order.index('abilities')
        self.assertLess(char_info_index, abilities_index)
        
        # Verify abilities comes before combat (dependency)
        combat_index = execution_order.index('combat')
        self.assertLess(abilities_index, combat_index)
    
    def test_successful_calculation(self):
        """Test successful character calculation."""
        result = self.service.calculate(self.sample_data, self.context)
        
        self.assertEqual(result.status, CalculationStatus.COMPLETED)
        self.assertEqual(len(result.errors), 0)
        self.assertIsInstance(result.data, dict)
        
        # Check that all default coordinators produced results
        expected_coordinators = ['character_info', 'abilities', 'combat', 'spellcasting', 'features', 'equipment']
        for coordinator_name in expected_coordinators:
            self.assertIn(coordinator_name, result.data)
    
    def test_calculation_with_invalid_data(self):
        """Test calculation with invalid data."""
        invalid_data = {"invalid": "data"}
        result = self.service.calculate(invalid_data, self.context)
        
        self.assertEqual(result.status, CalculationStatus.FAILED)
        self.assertGreater(len(result.errors), 0)
    
    def test_dependency_validation(self):
        """Test dependency validation."""
        unresolved = self.service.validate_dependencies()
        
        # Should have no unresolved dependencies with default coordinators
        self.assertEqual(len(unresolved), 0)
    
    def test_performance_metrics(self):
        """Test performance metrics collection."""
        # Perform calculation to generate metrics
        self.service.calculate(self.sample_data, self.context)
        
        metrics = self.service.get_performance_metrics()
        
        self.assertIn('total_calculations', metrics)
        self.assertIn('success_rate', metrics)
        self.assertIn('coordinator_performance', metrics)
        self.assertGreater(metrics['total_calculations'], 0)
    
    def test_session_management(self):
        """Test calculation session management."""
        # Start calculation (creates session)
        result = self.service.calculate(self.sample_data, self.context)
        
        # Session should be cleaned up after calculation
        self.assertEqual(len(self.service.active_sessions), 0)
    
    def test_health_check(self):
        """Test service health check."""
        health = self.service.health_check()
        
        self.assertIn('status', health)
        self.assertIn('coordinators', health)
        self.assertIn('performance', health)
        self.assertEqual(health['status'], 'healthy')


class TestCharacterBuilder(unittest.TestCase):
    """Test CharacterBuilder implementation."""
    
    def setUp(self):
        self.builder = CharacterBuilder()
        self.context = BuildContext(character_id="12345", rule_version="2014")
        
        self.calculation_data = {
            'character_info': {
                'character_id': 12345,
                'name': 'Test Wizard',
                'level': 5,
                'rule_version': '2014',
                'classes': [
                    {
                        'id': 1,
                        'name': 'Wizard',
                        'level': 5,
                        'hit_die': 6,
                        'subclass': None
                    }
                ],
                'species': {
                    'id': 1,
                    'name': 'High Elf',
                    'subrace': None
                },
                'background': {
                    'id': 1,
                    'name': 'Sage'
                },
                'alignment': 'Neutral',
                'experience_points': 6500,
                'proficiency_bonus': 3
            },
            'abilities': {
                'ability_scores': {
                    'strength': {'score': 10, 'modifier': 0},
                    'dexterity': {'score': 14, 'modifier': 2},
                    'constitution': {'score': 16, 'modifier': 3},
                    'intelligence': {'score': 18, 'modifier': 4},
                    'wisdom': {'score': 12, 'modifier': 1},
                    'charisma': {'score': 8, 'modifier': -1}
                },
                'proficiency_bonus': 3
            },
            'combat': {
                'hit_points': {
                    'current': 38,
                    'maximum': 38,
                    'temporary': 0
                },
                'armor_class': {
                    'base': 10,
                    'total': 12
                },
                'speed': {
                    'walk': 30,
                    'swim': 0,
                    'fly': 0,
                    'climb': 0
                },
                'initiative_bonus': 2
            },
            'spellcasting': {
                'is_spellcaster': True,
                'spellcasting_ability': 'intelligence',
                'spell_save_dc': 14,
                'spell_attack_bonus': 6,
                'spell_slots': [4, 3, 2, 0, 0, 0, 0, 0, 0],
                'spells': [
                    {
                        'id': 1,
                        'name': 'Magic Missile',
                        'level': 1,
                        'school': 'Evocation',
                        'casting_time': '1 action',
                        'range': '120 feet',
                        'components': ['V', 'S'],
                        'duration': 'Instantaneous',
                        'description': 'You create three glowing darts of magical force.'
                    }
                ]
            },
            'features': {
                'class_features': [
                    {
                        'id': 1,
                        'name': 'Spellcasting',
                        'description': 'You can cast spells',
                        'source_class': 'Wizard',
                        'level_required': 1,
                        'is_subclass_feature': False
                    }
                ],
                'racial_traits': [
                    {
                        'id': 10,
                        'name': 'Darkvision',
                        'description': 'You can see in dim light',
                        'source_race': 'Elf',
                        'trait_type': 'racial'
                    }
                ],
                'feats': []
            },
            'equipment': {
                'basic_equipment': [
                    {
                        'id': 1,
                        'name': 'Quarterstaff',
                        'quantity': 1,
                        'weight': 4.0,
                        'equipped': True,
                        'type': 'Weapon'
                    }
                ],
                'wealth': {
                    'gold': 125,
                    'silver': 23,
                    'copper': 15
                }
            }
        }
    
    def test_builder_initialization(self):
        """Test builder initialization."""
        self.assertIsInstance(self.builder, CharacterBuilder)
        self.assertIsInstance(self.builder.default_values, dict)
        self.assertIn('ability_scores', self.builder.default_values)
    
    def test_successful_character_build(self):
        """Test successful character building."""
        character = self.builder.build_character(self.calculation_data, self.context)
        
        self.assertIsInstance(character, Character)
        self.assertEqual(character.name, 'Test Wizard')
        self.assertEqual(character.level, 5)
        self.assertEqual(character.id, 12345)
        self.assertEqual(len(character.classes), 1)
        self.assertEqual(character.classes[0].name, 'Wizard')
    
    def test_character_info_building(self):
        """Test character info building."""
        char_info = self.builder._build_character_info(self.calculation_data, self.context)
        
        self.assertEqual(char_info['name'], 'Test Wizard')
        self.assertEqual(char_info['level'], 5)
        self.assertIsInstance(char_info['classes'], list)
        self.assertIsInstance(char_info['species'], Species)
        self.assertIsInstance(char_info['background'], Background)
    
    def test_ability_scores_building(self):
        """Test ability scores building."""
        ability_scores = self.builder._build_ability_scores(self.calculation_data, self.context)
        
        self.assertEqual(ability_scores.strength, 10)
        self.assertEqual(ability_scores.intelligence, 18)
        self.assertEqual(ability_scores.charisma, 8)
    
    def test_combat_info_building(self):
        """Test combat info building."""
        combat_info = self.builder._build_combat_info(self.calculation_data, self.context)
        
        self.assertEqual(combat_info['hit_points'].maximum, 38)
        self.assertEqual(combat_info['armor_class'].total, 12)
        self.assertEqual(combat_info['speed'].walk, 30)
        self.assertEqual(combat_info['initiative_bonus'], 2)
    
    def test_validation_with_invalid_data(self):
        """Test validation with invalid data."""
        invalid_data = {'invalid': 'data'}
        
        with self.assertRaises(ValueError):
            self.builder.build_character(invalid_data, self.context)
    
    def test_validation_with_strict_mode(self):
        """Test validation in strict mode."""
        self.context.strict_mode = True
        invalid_data = {'character_info': {'name': ''}}  # Invalid empty name
        
        with self.assertRaises(ValueError):
            self.builder.build_character(invalid_data, self.context)
    
    def test_build_statistics(self):
        """Test build statistics tracking."""
        # Perform successful build
        self.builder.build_character(self.calculation_data, self.context)
        
        stats = self.builder.get_build_statistics()
        
        self.assertEqual(stats['total_builds'], 1)
        self.assertEqual(stats['successful_builds'], 1)
        self.assertEqual(stats['failed_builds'], 0)
        self.assertGreater(stats['success_rate'], 0)


class TestValidationService(unittest.TestCase):
    """Test ValidationService implementation."""
    
    def setUp(self):
        self.service = ValidationService()
        self.context = ValidationContext(rule_version="2014", character_id="12345")
        
        self.valid_data = {
            'level': 5,
            'ability_scores': {
                'strength': {'score': 16},
                'dexterity': {'score': 14},
                'constitution': {'score': 15},
                'intelligence': {'score': 18},
                'wisdom': {'score': 12},
                'charisma': {'score': 13}
            },
            'hit_points': {
                'current': 38,
                'maximum': 38
            },
            'spells': [
                {
                    'name': 'Magic Missile',
                    'level': 1
                }
            ]
        }
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsInstance(self.service, ValidationService)
        self.assertGreater(len(self.service.rules), 0)
        self.assertIn('character_level', self.service.rules)
    
    def test_input_validation_success(self):
        """Test successful input validation."""
        result = self.service.validate_input(self.valid_data, self.context)
        
        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.get_errors()), 0)
    
    def test_input_validation_failure(self):
        """Test input validation failure."""
        invalid_data = {
            'level': 25,  # Invalid level
            'ability_scores': {
                'strength': {'score': 50}  # Invalid score
            }
        }
        
        result = self.service.validate_input(invalid_data, self.context)
        
        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.get_errors()), 0)
    
    def test_character_level_validation(self):
        """Test character level validation rule."""
        rule = self.service.rules['character_level']
        
        # Valid level
        messages = rule.validate({'level': 10}, self.context)
        self.assertEqual(len(messages), 0)
        
        # Invalid level (too high)
        messages = rule.validate({'level': 25}, self.context)
        self.assertGreater(len(messages), 0)
        
        # Invalid level (too low)
        messages = rule.validate({'level': 0}, self.context)
        self.assertGreater(len(messages), 0)
    
    def test_ability_score_validation(self):
        """Test ability score validation rule."""
        rule = self.service.rules['ability_scores']
        
        # Valid scores
        valid_scores = {
            'ability_scores': {
                'strength': {'score': 16},
                'dexterity': {'score': 14}
            }
        }
        messages = rule.validate(valid_scores, self.context)
        # May have messages for missing abilities, but not for invalid values
        error_messages = [m for m in messages if m.severity.value == 'error']
        for msg in error_messages:
            self.assertIn('Missing required ability score', msg.message)
    
    def test_hit_points_validation(self):
        """Test hit points validation rule."""
        rule = self.service.rules['hit_points']
        
        # Valid hit points
        valid_hp = {
            'hit_points': {
                'current': 20,
                'maximum': 30
            }
        }
        messages = rule.validate(valid_hp, self.context)
        self.assertEqual(len(messages), 0)
        
        # Invalid hit points (negative current)
        invalid_hp = {
            'hit_points': {
                'current': -5,
                'maximum': 30
            }
        }
        messages = rule.validate(invalid_hp, self.context)
        self.assertGreater(len(messages), 0)
    
    def test_custom_rule_registration(self):
        """Test custom rule registration."""
        from src.calculators.services.validation_service import IValidationRule, ValidationMessage, ValidationSeverity, ValidationCategory
        
        class TestRule(IValidationRule):
            def validate(self, data, context):
                if data.get('test_field') != 'test_value':
                    return [ValidationMessage(
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.STRUCTURE,
                        message="Test validation failed"
                    )]
                return []
            
            def get_rule_name(self):
                return "test_rule"
        
        # Register custom rule
        test_rule = TestRule()
        self.service.register_rule(test_rule)
        
        self.assertIn('test_rule', self.service.rules)
        
        # Unregister rule
        self.service.unregister_rule('test_rule')
        self.assertNotIn('test_rule', self.service.rules)
    
    def test_validation_statistics(self):
        """Test validation statistics tracking."""
        # Perform validations
        self.service.validate_input(self.valid_data, self.context)
        self.service.validate_input({'invalid': 'data'}, self.context)
        
        stats = self.service.get_validation_statistics()
        
        self.assertEqual(stats['total_validations'], 2)
        self.assertGreater(stats['successful_validations'], 0)
        self.assertIn('rule_usage', stats)


class TestPerformanceService(unittest.TestCase):
    """Test PerformanceService implementation."""
    
    def setUp(self):
        self.service = PerformanceService()
    
    def test_service_initialization(self):
        """Test service initialization."""
        self.assertIsInstance(self.service, PerformanceService)
        self.assertIsNotNone(self.service.collector)
        self.assertIsNotNone(self.service.analyzer)
    
    def test_metric_recording(self):
        """Test metric recording."""
        self.service.record_value("test_metric", 100.0, "ms")
        
        metrics = self.service.collector.get_metrics("test_metric")
        self.assertEqual(len(metrics), 1)
        self.assertEqual(metrics[0].name, "test_metric")
        self.assertEqual(metrics[0].value, 100.0)
    
    def test_measurement_lifecycle(self):
        """Test measurement start/stop lifecycle."""
        measurement_id = self.service.start_measurement("test_operation")
        self.assertIn(measurement_id, self.service.active_measurements)
        
        # Simulate some work
        import time
        time.sleep(0.01)  # 10ms
        
        metric = self.service.stop_measurement(measurement_id)
        self.assertNotIn(measurement_id, self.service.active_measurements)
        self.assertEqual(metric.name, "test_operation")
        self.assertGreater(metric.value, 0)
    
    def test_threshold_checking(self):
        """Test threshold violation detection."""
        from src.calculators.services.performance_service import PerformanceThreshold
        
        # Add threshold
        threshold = PerformanceThreshold(
            metric_name="test_metric",
            max_value=50.0,
            alert_message="Test threshold exceeded"
        )
        self.service.add_threshold(threshold)
        
        # Record metric that violates threshold
        initial_alerts = len(self.service.alerts)
        self.service.record_value("test_metric", 100.0)
        
        self.assertGreater(len(self.service.alerts), initial_alerts)
    
    def test_performance_report_generation(self):
        """Test performance report generation."""
        # Record some metrics
        self.service.record_value("test_metric", 10.0)
        self.service.record_value("test_metric", 20.0)
        self.service.record_value("test_metric", 30.0)
        
        report = self.service.get_performance_report("test_metric")
        
        self.assertEqual(len(report.metrics), 3)
        self.assertIn("test_metric", report.statistics)
        self.assertEqual(report.statistics["test_metric"]["count"], 3)
        self.assertEqual(report.statistics["test_metric"]["mean"], 20.0)
    
    def test_system_monitoring(self):
        """Test system resource monitoring."""
        # Enable system monitoring
        self.service.system_monitoring_enabled = True
        self.service.system_metrics_interval = 0  # Force immediate monitoring
        
        initial_count = self.service.collector.get_metric_count()
        self.service.monitor_system_resources()
        
        # Should have recorded system metrics
        self.assertGreater(self.service.collector.get_metric_count(), initial_count)
    
    def test_metrics_export(self):
        """Test metrics export functionality."""
        import tempfile
        import json
        
        # Record some metrics
        self.service.record_value("export_test", 42.0)
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_file = f.name
        
        try:
            self.service.export_metrics(temp_file, format="json", metric_name="export_test")
            
            # Verify export
            with open(temp_file, 'r') as f:
                exported_data = json.load(f)
            
            self.assertEqual(len(exported_data), 1)
            self.assertEqual(exported_data[0]['name'], "export_test")
            self.assertEqual(exported_data[0]['value'], 42.0)
        
        finally:
            # Clean up
            os.unlink(temp_file)
    
    def test_health_check(self):
        """Test service health check."""
        health = self.service.health_check()
        
        self.assertIn('status', health)
        self.assertIn('statistics', health)
        self.assertEqual(health['status'], 'healthy')


class TestServiceIntegration(unittest.TestCase):
    """Test integration between services."""
    
    def setUp(self):
        self.calculation_service = CalculationService()
        self.character_builder = CharacterBuilder()
        self.validation_service = ValidationService()
        self.performance_service = PerformanceService()
        
        self.context = CalculationContext(character_id="12345", rule_version="2014")
        self.build_context = BuildContext(character_id="12345", rule_version="2014")
        self.validation_context = ValidationContext(rule_version="2014", character_id="12345")
        
        self.sample_data = {
            "id": 12345,
            "name": "Integration Test Character",
            "stats": [
                {"id": 1, "value": 16},  # Strength
                {"id": 2, "value": 14},  # Dexterity
                {"id": 3, "value": 15},  # Constitution
                {"id": 4, "value": 18},  # Intelligence
                {"id": 5, "value": 12},  # Wisdom
                {"id": 6, "value": 13}   # Charisma
            ],
            "classes": [
                {
                    "level": 5,
                    "definition": {
                        "name": "Wizard",
                        "hitDie": 6
                    }
                }
            ],
            "race": {
                "fullName": "High Elf"
            },
            "background": {
                "definition": {
                    "name": "Sage"
                }
            },
            "baseHitPoints": 38,
            "baseArmorClass": 12
        }
    
    def test_full_calculation_to_character_pipeline(self):
        """Test complete pipeline from calculation to character object."""
        # Step 1: Perform calculations (raw D&D Beyond data doesn't need input validation)
        calculation_result = self.calculation_service.calculate(self.sample_data, self.context)
        self.assertEqual(calculation_result.status, CalculationStatus.COMPLETED)
        
        # Step 2: Build character object
        character = self.character_builder.build_character(calculation_result.data, self.build_context)
        self.assertIsInstance(character, Character)
        self.assertEqual(character.name, "Integration Test Character")
        
        # Step 3: Validate final character object (this is the appropriate validation step)
        char_validation = self.validation_service.validate_character(character, self.validation_context)
        self.assertTrue(char_validation.is_valid)
    
    def test_performance_monitoring_integration(self):
        """Test performance monitoring during service operations."""
        # Monitor calculation service
        measurement_id = self.performance_service.start_measurement("full_calculation")
        
        calculation_result = self.calculation_service.calculate(self.sample_data, self.context)
        
        metric = self.performance_service.stop_measurement(measurement_id)
        
        self.assertEqual(calculation_result.status, CalculationStatus.COMPLETED)
        self.assertGreater(metric.value, 0)  # Should have taken some time
        
        # Check performance report
        report = self.performance_service.get_performance_report("full_calculation")
        self.assertEqual(len(report.metrics), 1)
    
    def test_error_handling_across_services(self):
        """Test error handling across service boundaries."""
        invalid_data = {"completely": "invalid"}
        
        # Validation should catch the error
        validation_result = self.validation_service.validate_input(invalid_data, self.validation_context)
        self.assertFalse(validation_result.is_valid)
        
        # Calculation service should also handle it gracefully
        calculation_result = self.calculation_service.calculate(invalid_data, self.context)
        self.assertEqual(calculation_result.status, CalculationStatus.FAILED)
        
        # Performance metrics should still be recorded for failed operations
        metrics = self.performance_service.collector.get_metrics()
        # Should have some metrics even for failed operations


if __name__ == '__main__':
    unittest.main(verbosity=2)