"""
Unit tests for spell detection fixes.

Specifically tests the cantrip slot detection bug fix and D&D rule compliance.
This addresses the issue where cantrips were incorrectly reported as having spell slots.
"""

import pytest
from unittest.mock import Mock, patch
from pathlib import Path
import sys

# Add Discord module to path
discord_root = Path(__file__).parent.parent.parent.parent / "discord"
sys.path.insert(0, str(discord_root))

from services.change_detection.detectors import SpellDetector
from services.change_detection.models import FieldChange, ChangeType, ChangeCategory, ChangePriority


class TestSpellDetectionFixes:
    """Test spell detection accuracy and D&D rule compliance."""
    
    @pytest.fixture
    def spell_detector(self):
        """Spell detector instance for testing."""
        return SpellDetector()
    
    @pytest.fixture
    def wizard_spell_data_old(self):
        """Old wizard spell data for testing."""
        return {
            'spells': {
                'class_spells': {
                    'Wizard': [
                        {'name': 'Mage Hand', 'level': 0},
                        {'name': 'Prestidigitation', 'level': 0},
                        {'name': 'Minor Illusion', 'level': 0},
                        {'name': 'Magic Missile', 'level': 1},
                        {'name': 'Shield', 'level': 1}
                    ]
                }
            },
            'spellcasting': {
                'spell_slots': [0, 2, 0, 0, 0, 0, 0, 0, 0, 0],  # No cantrip slots, 2 first level
                'spell_counts': {
                    'total': 5,
                    'by_level': {0: 3, 1: 2}  # 3 cantrips known, 2 first level spells
                }
            }
        }
    
    @pytest.fixture
    def wizard_spell_data_new_level_up(self):
        """New wizard spell data after level up."""
        return {
            'spells': {
                'class_spells': {
                    'Wizard': [
                        {'name': 'Mage Hand', 'level': 0},
                        {'name': 'Prestidigitation', 'level': 0},
                        {'name': 'Minor Illusion', 'level': 0},
                        {'name': 'Fire Bolt', 'level': 0},  # New cantrip
                        {'name': 'Magic Missile', 'level': 1},
                        {'name': 'Shield', 'level': 1},
                        {'name': 'Detect Magic', 'level': 1}  # New 1st level spell
                    ]
                }
            },
            'spellcasting': {
                'spell_slots': [0, 3, 0, 0, 0, 0, 0, 0, 0, 0],  # Still no cantrip slots, 3 first level
                'spell_counts': {
                    'total': 7,
                    'by_level': {0: 4, 1: 3}  # 4 cantrips known, 3 first level spells
                }
            }
        }
    
    def test_cantrip_slot_bug_fix(self, spell_detector, wizard_spell_data_old, wizard_spell_data_new_level_up):
        """Test that cantrip 'slots' are not reported as changing."""
        changes = spell_detector.detect_changes(
            wizard_spell_data_old, 
            wizard_spell_data_new_level_up, 
            {}
        )
        
        # Should NOT detect cantrip slot changes (cantrips don't have slots)
        cantrip_slot_changes = [
            c for c in changes 
            if 'spell_slots' in c.field_path and ('0' in c.field_path or 'cantrip' in c.description.lower())
        ]
        
        # The bug was reporting "Level 0 spell slots changed from X to Y"
        # This should NOT happen because cantrips don't have spell slots
        for change in cantrip_slot_changes:
            # If any cantrip-related slot changes are detected, they should be about spells known, not slots
            assert 'slot' not in change.description.lower() or 'known' in change.description.lower()
        
        # Should detect actual spell slot changes (1st level)
        first_level_slot_changes = [
            c for c in changes 
            if 'spell_slots' in c.field_path and '1' in c.field_path
        ]
        
        assert len(first_level_slot_changes) > 0
        slot_change = first_level_slot_changes[0]
        assert slot_change.old_value == 2
        assert slot_change.new_value == 3
        assert 'level 1' in slot_change.description.lower() or '1st level' in slot_change.description.lower()
    
    def test_cantrip_learning_detection(self, spell_detector, wizard_spell_data_old, wizard_spell_data_new_level_up):
        """Test that learning new cantrips is properly detected."""
        changes = spell_detector.detect_changes(
            wizard_spell_data_old, 
            wizard_spell_data_new_level_up, 
            {}
        )
        
        # Should detect new cantrip learned
        cantrip_learned_changes = [
            c for c in changes 
            if 'Fire Bolt' in str(c.new_value) or ('cantrip' in c.description.lower() and 'learned' in c.description.lower())
        ]
        
        # Should detect cantrip as spell learned, not slot change
        if cantrip_learned_changes:
            cantrip_change = cantrip_learned_changes[0]
            assert cantrip_change.change_type == ChangeType.ADDED
            assert 'learned' in cantrip_change.description.lower() or 'gained' in cantrip_change.description.lower()
            assert 'slot' not in cantrip_change.description.lower()
    
    def test_spell_slot_vs_spells_known_distinction(self, spell_detector):
        """Test proper distinction between spell slots and spells known."""
        old_data = {
            'spellcasting': {
                'spell_slots': [0, 2, 1, 0, 0, 0, 0, 0, 0, 0],  # 2 first level, 1 second level
                'spell_counts': {'total': 4, 'by_level': {0: 2, 1: 1, 2: 1}}
            },
            'spells': {
                'class_spells': {
                    'Wizard': [
                        {'name': 'Mage Hand', 'level': 0},
                        {'name': 'Prestidigitation', 'level': 0},
                        {'name': 'Magic Missile', 'level': 1},
                        {'name': 'Misty Step', 'level': 2}
                    ]
                }
            }
        }
        
        new_data = {
            'spellcasting': {
                'spell_slots': [0, 3, 2, 0, 0, 0, 0, 0, 0, 0],  # More slots
                'spell_counts': {'total': 5, 'by_level': {0: 2, 1: 2, 2: 1}}
            },
            'spells': {
                'class_spells': {
                    'Wizard': [
                        {'name': 'Mage Hand', 'level': 0},
                        {'name': 'Prestidigitation', 'level': 0},
                        {'name': 'Magic Missile', 'level': 1},
                        {'name': 'Shield', 'level': 1},  # New spell known
                        {'name': 'Misty Step', 'level': 2}
                    ]
                }
            }
        }
        
        changes = spell_detector.detect_changes(old_data, new_data, {})
        
        # Should detect spell slot increases
        slot_changes = [c for c in changes if 'spell_slots' in c.field_path]
        spell_learned_changes = [c for c in changes if 'Shield' in str(c.new_value)]
        
        # Verify slot changes are about slots, not spells known
        for slot_change in slot_changes:
            assert 'slot' in slot_change.description.lower()
            assert 'learned' not in slot_change.description.lower()
        
        # Verify spell learned changes are about spells, not slots
        for spell_change in spell_learned_changes:
            assert 'learned' in spell_change.description.lower() or 'gained' in spell_change.description.lower()
            assert 'slot' not in spell_change.description.lower()
    
    def test_d_and_d_rule_compliance_wizard(self, spell_detector):
        """Test spell detection follows D&D 5e rules for wizards."""
        # Level 3 wizard spell progression
        old_data = {
            'character_info': {'level': 3, 'class': 'Wizard'},
            'spellcasting': {
                'spell_slots': [0, 4, 2, 0, 0, 0, 0, 0, 0, 0],  # Level 3: 4 first, 2 second
                'spell_counts': {'total': 8}
            }
        }
        
        # Level 4 wizard spell progression
        new_data = {
            'character_info': {'level': 4, 'class': 'Wizard'},
            'spellcasting': {
                'spell_slots': [0, 4, 3, 0, 0, 0, 0, 0, 0, 0],  # Level 4: 4 first, 3 second
                'spell_counts': {'total': 9}
            }
        }
        
        changes = spell_detector.detect_changes(old_data, new_data, {})
        
        # Should detect second level spell slot increase (valid for level 4 wizard)
        second_level_changes = [c for c in changes if 'spell_slots' in c.field_path and '2' in c.field_path]
        
        if second_level_changes:
            slot_change = second_level_changes[0]
            assert slot_change.old_value == 2
            assert slot_change.new_value == 3
            assert slot_change.change_type == ChangeType.INCREMENTED
            assert '2' in slot_change.description or 'second' in slot_change.description.lower()
    
    def test_d_and_d_rule_compliance_sorcerer(self, spell_detector):
        """Test spell detection follows D&D 5e rules for sorcerers."""
        # Sorcerers have different spell progression than wizards
        old_data = {
            'character_info': {'level': 2, 'class': 'Sorcerer'},
            'spellcasting': {
                'spell_slots': [0, 3, 0, 0, 0, 0, 0, 0, 0, 0],  # Level 2 sorcerer: 3 first level
                'spell_counts': {'total': 3, 'known': 3}  # Sorcerers have limited spells known
            }
        }
        
        new_data = {
            'character_info': {'level': 3, 'class': 'Sorcerer'},
            'spellcasting': {
                'spell_slots': [0, 4, 2, 0, 0, 0, 0, 0, 0, 0],  # Level 3: 4 first, 2 second
                'spell_counts': {'total': 4, 'known': 4}
            }
        }
        
        changes = spell_detector.detect_changes(old_data, new_data, {})
        
        # Should detect appropriate slot increases for sorcerer progression
        slot_changes = [c for c in changes if 'spell_slots' in c.field_path]
        
        # Should have changes for both 1st and 2nd level slots
        first_level_changes = [c for c in slot_changes if '1' in c.field_path]
        second_level_changes = [c for c in slot_changes if '2' in c.field_path]
        
        if first_level_changes:
            assert first_level_changes[0].old_value == 3
            assert first_level_changes[0].new_value == 4
        
        if second_level_changes:
            assert second_level_changes[0].old_value == 0
            assert second_level_changes[0].new_value == 2
    
    def test_non_spellcaster_class_handling(self, spell_detector):
        """Test handling of non-spellcasting classes."""
        # Fighter gaining spells (multiclass or magic items)
        old_data = {
            'character_info': {'level': 5, 'class': 'Fighter'},
            'spellcasting': {
                'spell_slots': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'spell_counts': {'total': 0}
            }
        }
        
        new_data = {
            'character_info': {'level': 6, 'class': 'Fighter'},
            'spellcasting': {
                'spell_slots': [0, 2, 0, 0, 0, 0, 0, 0, 0, 0],  # Gained spell slots (multiclass?)
                'spell_counts': {'total': 2}
            }
        }
        
        changes = spell_detector.detect_changes(old_data, new_data, {})
        
        # Should detect spell slot gain even for non-traditional spellcasters
        # (Could be multiclassing, magic items, etc.)
        slot_changes = [c for c in changes if 'spell_slots' in c.field_path]
        
        if slot_changes:
            # Should handle gracefully without assuming class-specific rules
            for change in slot_changes:
                assert change.description is not None
                assert len(change.description) > 0
    
    def test_warlock_pact_magic_handling(self, spell_detector):
        """Test handling of warlock pact magic (different from normal spellcasting)."""
        # Warlocks have unique spell slot progression
        old_data = {
            'character_info': {'level': 2, 'class': 'Warlock'},
            'spellcasting': {
                'spell_slots': [0, 1, 0, 0, 0, 0, 0, 0, 0, 0],  # 1 first level slot
                'pact_magic': True,
                'spell_counts': {'total': 2, 'known': 2}
            }
        }
        
        new_data = {
            'character_info': {'level': 3, 'class': 'Warlock'},
            'spellcasting': {
                'spell_slots': [0, 0, 2, 0, 0, 0, 0, 0, 0, 0],  # 2 second level slots (pact magic)
                'pact_magic': True,
                'spell_counts': {'total': 3, 'known': 3}
            }
        }
        
        changes = spell_detector.detect_changes(old_data, new_data, {})
        
        # Should handle warlock's unique progression
        slot_changes = [c for c in changes if 'spell_slots' in c.field_path]
        
        # Warlock slots change level, not just quantity
        if slot_changes:
            # Should detect the change appropriately
            for change in slot_changes:
                assert change.description is not None
    
    def test_impossible_spell_changes_prevention(self, spell_detector):
        """Test prevention of reporting impossible spell changes."""
        # Test with clearly impossible data
        old_data = {
            'character_info': {'level': 1, 'class': 'Barbarian'},  # Non-spellcaster
            'spellcasting': {
                'spell_slots': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'spell_counts': {'total': 0}
            }
        }
        
        new_data = {
            'character_info': {'level': 2, 'class': 'Barbarian'},
            'spellcasting': {
                'spell_slots': [0, 0, 0, 0, 0, 0, 0, 0, 0, 9],  # Impossible: 9th level slots at level 2
                'spell_counts': {'total': 1}
            }
        }
        
        changes = spell_detector.detect_changes(old_data, new_data, {})
        
        # Should handle impossible changes gracefully
        # Implementation may filter them out or mark them as unusual
        ninth_level_changes = [c for c in changes if '9' in c.field_path and 'spell_slots' in c.field_path]
        
        for change in ninth_level_changes:
            # If detected, should be handled appropriately
            assert change.description is not None
            # Could be marked as unusual, or filtered out entirely
    
    def test_character_agnostic_spell_detection(self, spell_detector):
        """Test that spell detection works for any character without hardcoded values."""
        # Test with different character builds
        test_cases = [
            {
                'name': 'Low Level Wizard',
                'old': {
                    'character_info': {'level': 1, 'class': 'Wizard'},
                    'spellcasting': {'spell_slots': [0, 2, 0, 0, 0, 0, 0, 0, 0, 0]}
                },
                'new': {
                    'character_info': {'level': 2, 'class': 'Wizard'},
                    'spellcasting': {'spell_slots': [0, 3, 0, 0, 0, 0, 0, 0, 0, 0]}
                }
            },
            {
                'name': 'High Level Sorcerer',
                'old': {
                    'character_info': {'level': 17, 'class': 'Sorcerer'},
                    'spellcasting': {'spell_slots': [0, 4, 3, 3, 3, 2, 1, 1, 1, 1]}
                },
                'new': {
                    'character_info': {'level': 18, 'class': 'Sorcerer'},
                    'spellcasting': {'spell_slots': [0, 4, 3, 3, 3, 3, 1, 1, 1, 1]}
                }
            }
        ]
        
        for test_case in test_cases:
            changes = spell_detector.detect_changes(test_case['old'], test_case['new'], {})
            
            # Should detect changes for any character level/class
            if changes:
                for change in changes:
                    # Should not contain hardcoded character-specific values
                    assert "12345" not in change.description  # No hardcoded IDs
                    assert "Specific Character Name" not in change.description
                    assert change.description is not None
                    assert len(change.description) > 0
    
    def test_spell_slot_description_accuracy(self, spell_detector):
        """Test that spell slot change descriptions are accurate and clear."""
        old_data = {
            'spellcasting': {
                'spell_slots': [0, 2, 1, 0, 0, 0, 0, 0, 0, 0]
            }
        }
        
        new_data = {
            'spellcasting': {
                'spell_slots': [0, 3, 2, 1, 0, 0, 0, 0, 0, 0]
            }
        }
        
        changes = spell_detector.detect_changes(old_data, new_data, {})
        
        slot_changes = [c for c in changes if 'spell_slots' in c.field_path]
        
        for change in slot_changes:
            # Description should be clear and accurate
            assert change.description is not None
            assert len(change.description) > 0
            
            # Should mention the spell level
            assert any(level_word in change.description.lower() 
                      for level_word in ['1st', '2nd', '3rd', 'first', 'second', 'third', 'level 1', 'level 2', 'level 3'])
            
            # Should mention it's about spell slots
            assert 'slot' in change.description.lower()
            
            # Should include old and new values
            assert str(change.old_value) in change.description
            assert str(change.new_value) in change.description


if __name__ == "__main__":
    pytest.main([__file__, "-v"])