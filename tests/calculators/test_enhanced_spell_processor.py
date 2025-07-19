#!/usr/bin/env python3
"""
Test cases for the enhanced spell processor.

These tests verify that the spell detection and deduplication fixes work correctly
for various scenarios including feat spells, racial spells, and cross-source duplicates.
"""

import pytest
import logging
from unittest.mock import Mock, patch
from typing import Dict, Any, List

# Import the enhanced spell processor
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from calculators.services.enhanced_spell_processor import EnhancedSpellProcessor, EnhancedSpellInfo

# Set up logging for tests
logging.basicConfig(level=logging.DEBUG)


class TestEnhancedSpellProcessor:
    """Test cases for the enhanced spell processor."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.processor = EnhancedSpellProcessor()
    
    def test_feat_spell_detection(self):
        """Test that feat spells are properly detected and included."""
        # Mock raw data with feat spells that should be included
        raw_data = {
            'spells': {
                'feat': [
                    {
                        'definition': {
                            'id': 2619039,
                            'name': 'Minor Illusion',
                            'level': 0,
                            'school': 'Illusion',
                            'description': 'You create a sound or an image...'
                        },
                        'countsAsKnownSpell': False,
                        'alwaysPrepared': False,
                        'prepared': False,
                        'usesSpellSlot': False,
                        'limitedUse': None,
                        'componentId': 1789165,
                        'componentTypeId': 1088085227
                    }
                ]
            },
            'classSpells': []
        }
        
        # Process spells
        result = self.processor.process_character_spells(raw_data)
        
        # Verify Minor Illusion is included
        assert 'Feat' in result
        assert len(result['Feat']) == 1
        assert result['Feat'][0].name == 'Minor Illusion'
        assert result['Feat'][0].is_available == True
        assert 'feat spell' in result['Feat'][0].availability_reason.lower()
    
    def test_racial_spell_deduplication(self):
        """Test that duplicate racial spells are removed within the same source."""
        # Mock raw data with duplicate Detect Magic in racial spells
        raw_data = {
            'spells': {
                'race': [
                    {
                        'definition': {
                            'id': 2619097,
                            'name': 'Detect Magic',
                            'level': 1,
                            'school': 'Divination',
                            'description': 'For the duration, you sense...'
                        },
                        'countsAsKnownSpell': False,
                        'alwaysPrepared': False,
                        'prepared': False,
                        'usesSpellSlot': False,
                        'limitedUse': {'maxUses': 1, 'resetType': 2},
                        'componentId': 3727517,
                        'componentTypeId': 306912077
                    },
                    {
                        'definition': {
                            'id': 2619097,
                            'name': 'Detect Magic',
                            'level': 1,
                            'school': 'Divination',
                            'description': 'For the duration, you sense...'
                        },
                        'countsAsKnownSpell': False,
                        'alwaysPrepared': False,
                        'prepared': False,
                        'usesSpellSlot': True,
                        'limitedUse': None,
                        'componentId': 3727517,
                        'componentTypeId': 306912077
                    }
                ]
            },
            'classSpells': []
        }
        
        # Process spells
        result = self.processor.process_character_spells(raw_data)
        
        # Verify only one Detect Magic remains in Racial source
        assert 'Racial' in result
        assert len(result['Racial']) == 1
        assert result['Racial'][0].name == 'Detect Magic'
    
    def test_cross_source_duplicates_preserved(self):
        """Test that cross-source duplicates are preserved."""
        # Mock raw data with Detect Magic in both racial and feat sources
        raw_data = {
            'spells': {
                'race': [
                    {
                        'definition': {
                            'id': 2619097,
                            'name': 'Detect Magic',
                            'level': 1,
                            'school': 'Divination',
                            'description': 'For the duration, you sense...'
                        },
                        'countsAsKnownSpell': False,
                        'alwaysPrepared': False,
                        'prepared': False,
                        'usesSpellSlot': False,
                        'limitedUse': {'maxUses': 1, 'resetType': 2},
                        'componentId': 3727517,
                        'componentTypeId': 306912077
                    }
                ],
                'feat': [
                    {
                        'definition': {
                            'id': 2619097,
                            'name': 'Detect Magic',
                            'level': 1,
                            'school': 'Divination',
                            'description': 'For the duration, you sense...'
                        },
                        'countsAsKnownSpell': False,
                        'alwaysPrepared': False,
                        'prepared': False,
                        'usesSpellSlot': False,
                        'limitedUse': {'maxUses': 1, 'resetType': 2},
                        'componentId': 1789165,
                        'componentTypeId': 1088085227
                    }
                ]
            },
            'classSpells': []
        }
        
        # Process spells
        result = self.processor.process_character_spells(raw_data)
        
        # Verify Detect Magic appears in both sources
        assert 'Racial' in result
        assert 'Feat' in result
        assert len(result['Racial']) == 1
        assert len(result['Feat']) == 1
        assert result['Racial'][0].name == 'Detect Magic'
        assert result['Feat'][0].name == 'Detect Magic'
    
    def test_class_spell_detection(self):
        """Test that class spells are properly detected."""
        # Mock raw data with class spells
        raw_data = {
            'spells': {},
            'classSpells': [
                {
                    'characterClassId': 199271964,
                    'spells': [
                        {
                            'definition': {
                                'id': 2619137,
                                'name': 'Magic Missile',
                                'level': 1,
                                'school': 'Evocation',
                                'description': 'You create three glowing darts...'
                            },
                            'countsAsKnownSpell': True,
                            'alwaysPrepared': False,
                            'prepared': False,
                            'usesSpellSlot': True,
                            'limitedUse': None
                        }
                    ]
                }
            ],
            'classes': [
                {
                    'id': 199271964,
                    'definition': {
                        'name': 'Wizard'
                    }
                }
            ]
        }
        
        # Process spells
        result = self.processor.process_character_spells(raw_data)
        
        # Verify class spell is included
        assert 'Wizard' in result
        assert len(result['Wizard']) == 1
        assert result['Wizard'][0].name == 'Magic Missile'
        assert result['Wizard'][0].counts_as_known == True
    
    def test_spell_availability_logic(self):
        """Test the enhanced spell availability logic."""
        # Test different availability scenarios
        test_cases = [
            # Feat spell - should always be available
            {
                'source_type': 'feat',
                'counts_as_known': False,
                'always_prepared': False,
                'prepared': False,
                'uses_spell_slot': True,
                'limited_use': None,
                'expected': True,
                'reason_contains': 'feat spell'
            },
            # Racial spell with limited use - should be available
            {
                'source_type': 'race',
                'counts_as_known': False,
                'always_prepared': False,
                'prepared': False,
                'uses_spell_slot': False,
                'limited_use': {'maxUses': 1},
                'expected': True,
                'reason_contains': 'doesn\'t use spell slots'  # This is the first condition that matches
            },
            # Class spell that counts as known - should be available
            {
                'source_type': 'class',
                'counts_as_known': True,
                'always_prepared': False,
                'prepared': False,
                'uses_spell_slot': True,
                'limited_use': None,
                'expected': True,
                'reason_contains': 'counts as known'
            },
            # Class spell that doesn't count as known - should not be available
            {
                'source_type': 'class',
                'counts_as_known': False,
                'always_prepared': False,
                'prepared': False,
                'uses_spell_slot': True,
                'limited_use': None,
                'expected': False,
                'reason_contains': 'not known'
            }
        ]
        
        for case in test_cases:
            is_available, reason = self.processor._determine_spell_availability(
                {},  # spell_data not used in this method
                case['source_type'],
                case['counts_as_known'],
                case['always_prepared'],
                case['prepared'],
                case['uses_spell_slot'],
                case['limited_use']
            )
            
            assert is_available == case['expected'], f"Failed for case: {case}"
            assert case['reason_contains'].lower() in reason.lower(), f"Reason '{reason}' doesn't contain '{case['reason_contains']}'"
    
    def test_legacy_format_conversion(self):
        """Test conversion to legacy format for compatibility."""
        # Create enhanced spell info
        enhanced_spells = {
            'Feat': [
                EnhancedSpellInfo(
                    id=2619039,
                    name='Minor Illusion',
                    level=0,
                    school='Illusion',
                    source='Feat',
                    description='You create a sound or an image...',
                    is_legacy=False,
                    counts_as_known=False,
                    is_always_prepared=False,
                    is_prepared=False,
                    uses_spell_slot=False,
                    limited_use=None,
                    component_id=1789165,
                    component_type_id=1088085227,
                    is_available=True,
                    availability_reason='Feat spell - all feat spells are available'
                )
            ]
        }
        
        # Convert to legacy format
        legacy_spells = self.processor.convert_to_legacy_format(enhanced_spells)
        
        # Verify legacy format
        assert 'Feat' in legacy_spells
        assert len(legacy_spells['Feat']) == 1
        
        spell = legacy_spells['Feat'][0]
        assert spell['name'] == 'Minor Illusion'
        assert spell['level'] == 0
        assert spell['school'] == 'Illusion'
        assert spell['source'] == 'Feat'
        assert 'description' in spell
        assert 'isLegacy' in spell
        assert 'is_prepared' in spell
    
    def test_empty_spell_data(self):
        """Test handling of empty or malformed spell data."""
        # Test with empty data
        raw_data = {
            'spells': {},
            'classSpells': []
        }
        
        result = self.processor.process_character_spells(raw_data)
        assert result == {}
        
        # Test with malformed data
        raw_data = {
            'spells': {
                'feat': [
                    {
                        # Missing definition
                        'countsAsKnownSpell': False
                    },
                    {
                        'definition': {
                            # Missing name
                            'level': 0
                        }
                    }
                ]
            },
            'classSpells': []
        }
        
        result = self.processor.process_character_spells(raw_data)
        # Should handle malformed data gracefully
        assert isinstance(result, dict)
    
    def test_comprehensive_integration(self):
        """Test comprehensive integration with realistic character data."""
        # Mock realistic character data with multiple spell sources
        raw_data = {
            'spells': {
                'race': [
                    {
                        'definition': {
                            'id': 2619097,
                            'name': 'Detect Magic',
                            'level': 1,
                            'school': 'Divination',
                            'description': 'For the duration, you sense...'
                        },
                        'countsAsKnownSpell': False,
                        'alwaysPrepared': False,
                        'prepared': False,
                        'usesSpellSlot': False,
                        'limitedUse': {'maxUses': 1, 'resetType': 2}
                    },
                    {
                        'definition': {
                            'id': 2619018,
                            'name': 'Fire Bolt',
                            'level': 0,
                            'school': 'Evocation',
                            'description': 'You hurl a mote of fire...'
                        },
                        'countsAsKnownSpell': False,
                        'alwaysPrepared': False,
                        'prepared': False,
                        'usesSpellSlot': False,
                        'limitedUse': None
                    }
                ],
                'feat': [
                    {
                        'definition': {
                            'id': 2619039,
                            'name': 'Minor Illusion',
                            'level': 0,
                            'school': 'Illusion',
                            'description': 'You create a sound or an image...'
                        },
                        'countsAsKnownSpell': False,
                        'alwaysPrepared': False,
                        'prepared': False,
                        'usesSpellSlot': False,
                        'limitedUse': None
                    },
                    {
                        'definition': {
                            'id': 2619097,
                            'name': 'Detect Magic',
                            'level': 1,
                            'school': 'Divination',
                            'description': 'For the duration, you sense...'
                        },
                        'countsAsKnownSpell': False,
                        'alwaysPrepared': False,
                        'prepared': False,
                        'usesSpellSlot': False,
                        'limitedUse': {'maxUses': 1, 'resetType': 2}
                    }
                ]
            },
            'classSpells': [
                {
                    'characterClassId': 199271964,
                    'spells': [
                        {
                            'definition': {
                                'id': 2619137,
                                'name': 'Magic Missile',
                                'level': 1,
                                'school': 'Evocation',
                                'description': 'You create three glowing darts...'
                            },
                            'countsAsKnownSpell': True,
                            'alwaysPrepared': False,
                            'prepared': False,
                            'usesSpellSlot': True,
                            'limitedUse': None
                        }
                    ]
                }
            ],
            'classes': [
                {
                    'id': 199271964,
                    'definition': {
                        'name': 'Wizard'
                    }
                }
            ]
        }
        
        # Process spells
        result = self.processor.process_character_spells(raw_data)
        
        # Verify comprehensive results
        assert 'Racial' in result
        assert 'Feat' in result
        assert 'Wizard' in result
        
        # Check racial spells
        racial_spell_names = [spell.name for spell in result['Racial']]
        assert 'Detect Magic' in racial_spell_names
        assert 'Fire Bolt' in racial_spell_names
        
        # Check feat spells
        feat_spell_names = [spell.name for spell in result['Feat']]
        assert 'Minor Illusion' in feat_spell_names
        assert 'Detect Magic' in feat_spell_names
        
        # Check class spells
        wizard_spell_names = [spell.name for spell in result['Wizard']]
        assert 'Magic Missile' in wizard_spell_names
        
        # Verify cross-source duplicates are preserved
        detect_magic_sources = []
        for source, spells in result.items():
            for spell in spells:
                if spell.name == 'Detect Magic':
                    detect_magic_sources.append(source)
        
        assert len(detect_magic_sources) == 2  # Should be in both Racial and Feat
        assert 'Racial' in detect_magic_sources
        assert 'Feat' in detect_magic_sources


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])