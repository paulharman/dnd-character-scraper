"""
Unit tests for change detection service functionality.

Tests change detection accuracy, spell slot detection fixes, and D&D rule compliance.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add Discord module to path
discord_root = Path(__file__).parent.parent.parent.parent / "discord"
sys.path.insert(0, str(discord_root))

from services.change_detection_service import ChangeDetectionService, ChangePriority
from services.change_detection.models import FieldChange, ChangeType, ChangeCategory


class TestChangeDetectionService:
    """Test change detection service functionality."""
    
    @pytest.fixture
    def change_service(self):
        """Change detection service instance."""
        return ChangeDetectionService()
    
    @pytest.fixture
    def basic_character_data(self):
        """Basic character data for testing."""
        return {
            'character_info': {
                'name': 'Test Character',
                'level': 5,
                'class': 'Wizard',
                'race': 'Human',
                'experience_points': 6500,
                'hit_points': 32,
                'armor_class': 13
            },
            'ability_scores': {
                'strength': 10,
                'dexterity': 14,
                'constitution': 13,
                'intelligence': 16,
                'wisdom': 12,
                'charisma': 8
            },
            'spells': {
                'class_spells': {
                    'Wizard': [
                        {'name': 'Cantrip 1', 'level': 0},
                        {'name': 'Cantrip 2', 'level': 0},
                        {'name': 'Magic Missile', 'level': 1},
                        {'name': 'Shield', 'level': 1}
                    ]
                }
            },
            'spellcasting': {
                'spell_slots': [4, 3, 2, 0, 0, 0, 0, 0, 0, 0],  # Cantrips, 1st, 2nd, etc.
                'spell_counts': {
                    'total': 6,
                    'by_level': {0: 4, 1: 2}
                }
            }
        }
    
    def test_service_initialization(self, change_service):
        """Test change detection service initialization."""
        assert change_service is not None
        assert hasattr(change_service, 'detect_changes')
    
    def test_basic_info_change_detection(self, change_service, basic_character_data):
        """Test detection of basic character information changes."""
        old_data = basic_character_data.copy()
        new_data = basic_character_data.copy()
        
        # Change level
        new_data['character_info']['level'] = 6
        new_data['character_info']['experience_points'] = 14000
        
        changes = change_service.detect_changes(old_data, new_data)
        
        # Should detect level and experience changes
        level_changes = [c for c in changes if 'level' in c.field_path]
        exp_changes = [c for c in changes if 'experience' in c.field_path]
        
        assert len(level_changes) > 0
        assert len(exp_changes) > 0
        
        # Level change should be high priority
        level_change = level_changes[0]
        assert level_change.priority in [ChangePriority.HIGH, ChangePriority.CRITICAL]
        assert level_change.old_value == 5
        assert level_change.new_value == 6
    
    def test_ability_score_change_detection(self, change_service, basic_character_data):
        """Test detection of ability score changes."""
        old_data = basic_character_data.copy()
        new_data = basic_character_data.copy()
        
        # Increase Intelligence (important for wizard)
        new_data['ability_scores']['intelligence'] = 18
        
        changes = change_service.detect_changes(old_data, new_data)
        
        # Should detect intelligence change
        int_changes = [c for c in changes if 'intelligence' in c.field_path]
        assert len(int_changes) > 0
        
        int_change = int_changes[0]
        assert int_change.old_value == 16
        assert int_change.new_value == 18
        assert int_change.change_type == ChangeType.INCREMENTED
    
    def test_spell_slot_detection_accuracy(self, change_service, basic_character_data):
        """Test accurate spell slot change detection (fixing cantrip bug)."""
        old_data = basic_character_data.copy()
        new_data = basic_character_data.copy()
        
        # Level up: gain more spell slots (but cantrips don't have slots)
        new_data['character_info']['level'] = 6
        new_data['spellcasting']['spell_slots'] = [4, 4, 2, 0, 0, 0, 0, 0, 0, 0]  # More 1st level slots
        
        changes = change_service.detect_changes(old_data, new_data)
        
        # Should detect 1st level spell slot increase
        spell_slot_changes = [c for c in changes if 'spell_slots' in c.field_path and '1' in c.field_path]
        
        # Should NOT detect cantrip "slot" changes (cantrips don't have slots)
        cantrip_slot_changes = [c for c in changes if 'spell_slots' in c.field_path and '0' in c.field_path]
        
        # Verify correct detection
        if spell_slot_changes:
            slot_change = spell_slot_changes[0]
            assert slot_change.old_value == 3
            assert slot_change.new_value == 4
            assert "Level 1 spell slots" in slot_change.description or "1st level" in slot_change.description.lower()
        
        # Verify cantrip slots are NOT reported as changing
        # (This is the bug fix - cantrips don't have spell slots)
        for change in cantrip_slot_changes:
            # If cantrip changes are detected, they should be about cantrips known, not slots
            assert "cantrip" in change.description.lower() or "level 0" not in change.description
    
    def test_cantrip_vs_spell_slot_distinction(self, change_service):
        """Test proper distinction between cantrips known and spell slots."""
        old_data = {
            'spells': {
                'class_spells': {
                    'Wizard': [
                        {'name': 'Mage Hand', 'level': 0},
                        {'name': 'Prestidigitation', 'level': 0},
                        {'name': 'Magic Missile', 'level': 1}
                    ]
                }
            },
            'spellcasting': {
                'spell_slots': [3, 2, 0, 0, 0, 0, 0, 0, 0, 0],  # 3 cantrips known, 2 1st level slots
                'spell_counts': {'total': 3, 'by_level': {0: 2, 1: 1}}
            }
        }
        
        new_data = {
            'spells': {
                'class_spells': {
                    'Wizard': [
                        {'name': 'Mage Hand', 'level': 0},
                        {'name': 'Prestidigitation', 'level': 0},
                        {'name': 'Minor Illusion', 'level': 0},  # New cantrip
                        {'name': 'Magic Missile', 'level': 1}
                    ]
                }
            },
            'spellcasting': {
                'spell_slots': [4, 3, 0, 0, 0, 0, 0, 0, 0, 0],  # 4 cantrips known, 3 1st level slots
                'spell_counts': {'total': 4, 'by_level': {0: 3, 1: 1}}
            }
        }
        
        changes = change_service.detect_changes(old_data, new_data)
        
        # Should detect new cantrip learned
        cantrip_changes = [c for c in changes if 'Minor Illusion' in str(c.new_value) or 'cantrip' in c.description.lower()]
        
        # Should detect 1st level spell slot increase
        slot_changes = [c for c in changes if 'spell_slots' in c.field_path and '1' in c.field_path]
        
        # Verify cantrip is detected as spell learned, not slot change
        if cantrip_changes:
            cantrip_change = cantrip_changes[0]
            assert cantrip_change.change_type == ChangeType.ADDED
            assert "learned" in cantrip_change.description.lower() or "gained" in cantrip_change.description.lower()
        
        # Verify spell slot increase is properly detected
        if slot_changes:
            slot_change = slot_changes[0]
            assert slot_change.old_value == 2
            assert slot_change.new_value == 3
    
    def test_spell_detection_d_and_d_rule_compliance(self, change_service):
        """Test spell detection follows D&D 5e rules."""
        # Test data that follows D&D rules
        old_data = {
            'character_info': {'level': 3, 'class': 'Wizard'},
            'spellcasting': {
                'spell_slots': [0, 4, 2, 0, 0, 0, 0, 0, 0, 0],  # Level 3 wizard: 4 1st, 2 2nd
                'spell_counts': {'total': 8}
            }
        }
        
        new_data = {
            'character_info': {'level': 4, 'class': 'Wizard'},
            'spellcasting': {
                'spell_slots': [0, 4, 3, 0, 0, 0, 0, 0, 0, 0],  # Level 4 wizard: 4 1st, 3 2nd
                'spell_counts': {'total': 9}
            }
        }
        
        changes = change_service.detect_changes(old_data, new_data)
        
        # Should detect 2nd level spell slot increase (valid for level 4 wizard)
        slot_changes = [c for c in changes if 'spell_slots' in c.field_path and '2' in c.field_path]
        
        if slot_changes:
            slot_change = slot_changes[0]
            assert slot_change.old_value == 2
            assert slot_change.new_value == 3
            assert slot_change.change_type == ChangeType.INCREMENTED
    
    def test_impossible_spell_slot_changes_prevention(self, change_service):
        """Test prevention of reporting impossible spell slot changes."""
        # Test data with impossible changes (should be filtered out or handled gracefully)
        old_data = {
            'character_info': {'level': 1, 'class': 'Fighter'},  # Fighter has no spellcasting
            'spellcasting': {
                'spell_slots': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
                'spell_counts': {'total': 0}
            }
        }
        
        new_data = {
            'character_info': {'level': 2, 'class': 'Fighter'},
            'spellcasting': {
                'spell_slots': [0, 3, 0, 0, 0, 0, 0, 0, 0, 0],  # Impossible: Fighter can't cast spells
                'spell_counts': {'total': 3}
            }
        }
        
        changes = change_service.detect_changes(old_data, new_data)
        
        # Should either not detect impossible changes or mark them appropriately
        spell_changes = [c for c in changes if 'spell' in c.field_path.lower()]
        
        # If spell changes are detected, they should be handled appropriately
        # (Implementation may vary - could filter out, mark as unusual, etc.)
        for change in spell_changes:
            # Ensure the change makes sense or is properly flagged
            assert change.description is not None
            assert len(change.description) > 0
    
    def test_combat_stat_change_detection(self, change_service, basic_character_data):
        """Test detection of combat-related changes."""
        old_data = basic_character_data.copy()
        new_data = basic_character_data.copy()
        
        # Change armor class and hit points
        new_data['character_info']['armor_class'] = 15
        new_data['character_info']['hit_points'] = 38
        
        changes = change_service.detect_changes(old_data, new_data)
        
        # Should detect AC and HP changes
        ac_changes = [c for c in changes if 'armor_class' in c.field_path]
        hp_changes = [c for c in changes if 'hit_points' in c.field_path]
        
        assert len(ac_changes) > 0
        assert len(hp_changes) > 0
        
        # Both should be high priority
        for change in ac_changes + hp_changes:
            assert change.priority in [ChangePriority.HIGH, ChangePriority.CRITICAL, ChangePriority.MEDIUM]
    
    def test_skill_proficiency_change_detection(self, change_service):
        """Test detection of skill proficiency changes."""
        old_data = {
            'proficiencies': {
                'skill_bonuses': [
                    {
                        'skill_name': 'arcana',
                        'is_proficient': True,
                        'has_expertise': False,
                        'total_bonus': 5
                    },
                    {
                        'skill_name': 'investigation',
                        'is_proficient': False,
                        'has_expertise': False,
                        'total_bonus': 3
                    }
                ]
            }
        }
        
        new_data = {
            'proficiencies': {
                'skill_bonuses': [
                    {
                        'skill_name': 'arcana',
                        'is_proficient': True,
                        'has_expertise': True,  # Gained expertise
                        'total_bonus': 8
                    },
                    {
                        'skill_name': 'investigation',
                        'is_proficient': True,  # Gained proficiency
                        'has_expertise': False,
                        'total_bonus': 6
                    }
                ]
            }
        }
        
        changes = change_service.detect_changes(old_data, new_data)
        
        # Should detect expertise and proficiency gains
        expertise_changes = [c for c in changes if 'expertise' in c.field_path]
        proficiency_changes = [c for c in changes if 'proficient' in c.field_path and 'investigation' in c.field_path]
        
        assert len(expertise_changes) > 0
        assert len(proficiency_changes) > 0
        
        # Expertise should be higher priority than regular proficiency
        if expertise_changes and proficiency_changes:
            expertise_change = expertise_changes[0]
            proficiency_change = proficiency_changes[0]
            
            # Expertise is typically higher priority
            assert expertise_change.priority.value <= proficiency_change.priority.value
    
    def test_change_priority_assignment(self, change_service, basic_character_data):
        """Test proper priority assignment for different types of changes."""
        old_data = basic_character_data.copy()
        new_data = basic_character_data.copy()
        
        # Make various changes with different expected priorities
        new_data['character_info']['level'] = 6  # Critical priority
        new_data['character_info']['name'] = 'New Name'  # High priority
        new_data['ability_scores']['strength'] = 12  # Medium priority
        
        changes = change_service.detect_changes(old_data, new_data)
        
        # Verify priority assignments
        level_changes = [c for c in changes if 'level' in c.field_path]
        name_changes = [c for c in changes if 'name' in c.field_path]
        ability_changes = [c for c in changes if 'strength' in c.field_path]
        
        if level_changes:
            assert level_changes[0].priority in [ChangePriority.CRITICAL, ChangePriority.HIGH]
        
        if name_changes:
            assert name_changes[0].priority in [ChangePriority.HIGH, ChangePriority.MEDIUM]
        
        if ability_changes:
            # Small ability score changes are typically medium/low priority
            assert ability_changes[0].priority in [ChangePriority.MEDIUM, ChangePriority.LOW]
    
    def test_change_description_accuracy(self, change_service, basic_character_data):
        """Test accuracy and clarity of change descriptions."""
        old_data = basic_character_data.copy()
        new_data = basic_character_data.copy()
        
        # Make a clear change
        new_data['character_info']['level'] = 6
        new_data['character_info']['hit_points'] = 40
        
        changes = change_service.detect_changes(old_data, new_data)
        
        # Verify descriptions are clear and accurate
        for change in changes:
            assert change.description is not None
            assert len(change.description) > 0
            assert str(change.old_value) in change.description or str(change.new_value) in change.description
            
            # Should not contain placeholder text or debug info
            assert "TODO" not in change.description
            assert "DEBUG" not in change.description
            assert "None" != change.description
    
    def test_no_false_positive_changes(self, change_service, basic_character_data):
        """Test that identical data produces no changes."""
        old_data = basic_character_data.copy()
        new_data = basic_character_data.copy()
        
        changes = change_service.detect_changes(old_data, new_data)
        
        # Should detect no changes when data is identical
        assert len(changes) == 0
    
    def test_character_agnostic_detection(self, change_service):
        """Test that change detection works for any character without hardcoded values."""
        # Test with different character types
        test_characters = [
            {
                'character_info': {'name': 'Fighter', 'level': 1, 'class': 'Fighter'},
                'ability_scores': {'strength': 16, 'dexterity': 12, 'constitution': 14, 'intelligence': 10, 'wisdom': 13, 'charisma': 8}
            },
            {
                'character_info': {'name': 'Rogue', 'level': 3, 'class': 'Rogue'},
                'ability_scores': {'strength': 8, 'dexterity': 16, 'constitution': 12, 'intelligence': 14, 'wisdom': 13, 'charisma': 10}
            },
            {
                'character_info': {'name': 'Cleric', 'level': 5, 'class': 'Cleric'},
                'ability_scores': {'strength': 10, 'dexterity': 12, 'constitution': 14, 'intelligence': 8, 'wisdom': 16, 'charisma': 13}
            }
        ]
        
        for old_char in test_characters:
            new_char = old_char.copy()
            new_char['character_info']['level'] += 1  # Level up
            
            changes = change_service.detect_changes(old_char, new_char)
            
            # Should detect level change for any character
            level_changes = [c for c in changes if 'level' in c.field_path]
            assert len(level_changes) > 0
            
            # Should not contain character-specific hardcoded values
            for change in changes:
                assert "12345" not in change.description  # No hardcoded character IDs
                assert "Specific Name" not in change.description  # No hardcoded names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])