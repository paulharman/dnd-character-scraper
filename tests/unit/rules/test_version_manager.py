"""
Unit tests for RuleVersionManager

Tests the 2014/2024 rule version detection system.
"""

import unittest
from unittest.mock import Mock, patch

from src.rules.version_manager import RuleVersionManager, RuleVersion, DetectionResult


class TestRuleVersionManager(unittest.TestCase):
    """Test cases for rule version detection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.manager = RuleVersionManager()
    
    def test_force_version_override(self):
        """Test that forced version overrides all detection."""
        # Force 2014 rules
        self.manager.set_force_version(RuleVersion.RULES_2014)
        
        # Even with 2024 content, should return 2014
        character_data = {
            'classes': [{
                'definition': {'sourceId': 142}  # 2024 source
            }]
        }
        
        result = self.manager.detect_rule_version(character_data)
        self.assertEqual(result.version, RuleVersion.RULES_2014)
        self.assertEqual(result.detection_method, "user_override")
        self.assertEqual(result.confidence, 1.0)
    
    def test_primary_class_detection_2024(self):
        """Test detection of 2024 rules by primary class."""
        character_data = {
            'classes': [
                {
                    'level': 5,
                    'definition': {
                        'name': 'Fighter',
                        'sourceId': 142  # 2024 PHB
                    }
                },
                {
                    'level': 3,
                    'definition': {
                        'name': 'Wizard',
                        'sourceId': 1  # 2014 PHB
                    }
                }
            ]
        }
        
        result = self.manager.detect_rule_version(character_data)
        self.assertEqual(result.version, RuleVersion.RULES_2024)
        self.assertIn("primary_class", result.detection_method)
    
    def test_primary_class_detection_mixed_content(self):
        """Test that mixed content defaults to 2014 rules."""
        character_data = {
            'classes': [{
                'level': 10,
                'definition': {
                    'name': 'Barbarian',
                    'sourceId': 1  # 2014 PHB
                },
                'subclassDefinition': {
                    'name': 'Path of the Berserker',
                    'sourceId': 142  # 2024 subclass
                }
            }]
        }
        
        result = self.manager.detect_rule_version(character_data)
        self.assertEqual(result.version, RuleVersion.RULES_2014)
        # Check evidence contains mixed content warning
        evidence_str = " ".join(result.evidence).lower()
        self.assertIn("mixed content", evidence_str)
        self.assertIn("2014 rules", evidence_str)
    
    def test_terminology_detection(self):
        """Test detection based on species vs race terminology."""
        # 2024 uses 'species'
        character_data_2024 = {
            'species': {'name': 'Human'}
        }
        
        result = self.manager.detect_rule_version(character_data_2024)
        self.assertIn("species", str(result.evidence))
        
        # 2014 uses 'race'
        character_data_2014 = {
            'race': {'name': 'Human'}
        }
        
        result = self.manager.detect_rule_version(character_data_2014)
        self.assertIn("race", str(result.evidence))
    
    def test_source_id_detection(self):
        """Test detection based on source book IDs."""
        character_data = {
            'race': {
                'definition': {'sourceId': 143}  # 2024 DMG
            },
            'background': {
                'definition': {'sourceId': 144}  # 2024 MM
            },
            'feats': [
                {'definition': {'sourceId': 142}}  # 2024 PHB
            ]
        }
        
        result = self.manager.detect_rule_version(character_data)
        self.assertEqual(result.version, RuleVersion.RULES_2024)
        self.assertIn("source_ids", result.detection_method)
    
    def test_mixed_source_conservative_approach(self):
        """Test that mixed sources default to 2014."""
        character_data = {
            'race': {
                'definition': {'sourceId': 1}  # 2014
            },
            'feats': [
                {'definition': {'sourceId': 142}}  # 2024
            ]
        }
        
        result = self.manager.detect_rule_version(character_data)
        self.assertEqual(result.version, RuleVersion.RULES_2014)
        self.assertIn("Mixed source IDs", str(result.evidence))
    
    def test_default_to_2024_with_warning(self):
        """Test default to 2024 when no clear indicators."""
        character_data = {
            'name': 'Test Character',
            'level': 5
            # No clear version indicators
        }
        
        result = self.manager.detect_rule_version(character_data)
        self.assertEqual(result.version, RuleVersion.RULES_2024)
        self.assertEqual(result.detection_method, "default")
        self.assertIn("--force-2014", str(result.warnings))
        self.assertLess(result.confidence, 0.6)
    
    def test_caching(self):
        """Test that results are cached by character ID."""
        character_data = {
            'classes': [{
                'definition': {'sourceId': 142}
            }]
        }
        
        # First call
        result1 = self.manager.detect_rule_version(character_data, character_id=12345)
        
        # Modify data (shouldn't affect cached result)
        character_data['classes'][0]['definition']['sourceId'] = 1
        
        # Second call should return cached result
        result2 = self.manager.detect_rule_version(character_data, character_id=12345)
        
        self.assertEqual(result1.version, result2.version)
        self.assertEqual(result1.detection_method, result2.detection_method)
    
    def test_detection_summary(self):
        """Test human-readable detection summary."""
        character_data = {
            'classes': [{
                'level': 10,
                'definition': {
                    'name': 'Fighter',
                    'sourceId': 142
                }
            }]
        }
        
        result = self.manager.detect_rule_version(character_data)
        summary = self.manager.get_detection_summary(result)
        
        self.assertIn("Rule Version Detected: 2024", summary)
        self.assertIn("Confidence:", summary)
        self.assertIn("Evidence:", summary)
        self.assertIn("Primary class source ID 142", summary)
    
    def test_homebrew_ignored(self):
        """Test that homebrew content is ignored for detection."""
        character_data = {
            'classes': [{
                'level': 10,
                'definition': {
                    'name': 'Fighter',
                    'sourceId': 1,  # Official 2014
                    'isHomebrew': False
                },
                'subclassDefinition': {
                    'name': 'Custom Archetype',
                    'sourceId': 99999,  # Homebrew ID
                    'isHomebrew': True
                }
            }]
        }
        
        result = self.manager.detect_rule_version(character_data)
        # Should detect as 2014 based on official class, ignoring homebrew subclass
        self.assertEqual(result.version, RuleVersion.RULES_2014)
    
    def test_multiple_detection_methods_voting(self):
        """Test that multiple detection methods contribute to final result."""
        character_data = {
            'species': {'name': 'Human'},  # 2024 terminology
            'classes': [{
                'level': 10,
                'definition': {
                    'sourceId': 142  # 2024 source
                }
            }],
            'background': {
                'definition': {
                    'sourceId': 142  # 2024 source
                }
            }
        }
        
        result = self.manager.detect_rule_version(character_data)
        self.assertEqual(result.version, RuleVersion.RULES_2024)
        self.assertGreater(result.confidence, 0.8)  # High confidence from multiple indicators
        self.assertGreater(len(result.evidence), 2)  # Multiple pieces of evidence


if __name__ == '__main__':
    unittest.main()