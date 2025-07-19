#!/usr/bin/env python3
"""
Unit tests for spell detection fixes.

Tests the fix for incorrect cantrip slot detection and ensures
spell slot changes are reported accurately according to D&D rules.
"""

import unittest
from unittest.mock import Mock
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).absolute().parent.parent.parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "discord"))

from discord.services.change_detection.detectors import SpellDetector
from discord.services.change_detection.models import ChangeType, ChangePriority, ChangeCategory


class TestSpellDetectionFix(unittest.TestCase):
    """Test spell detection accuracy and D&D rule compliance."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.detector = SpellDetector()
        self.context = {
            'character_id': 12345,
            'character_name': 'Test Character'
        }
    
    def test_cantrips_do_not_have_spell_slots(self):
        """Test that cantrips (level 0 spells) don't generate spell slot changes."""
        old_data = {
            'spellcasting': {
                'spell_slots': [3, 0, 0, 0, 0, 0, 0, 0, 0, 0]  # 3 cantrips known, 0 slots for levels 1-9
            }
        }
        
        new_data = {
            'spellcasting': {
                'spell_slots': [4, 2, 0, 0, 0, 0, 0, 0, 0, 0]  # 4 cantrips known, 2 level 1 slots
            }
        }
        
        changes = self.detector.detect_changes(old_data, new_data, self.context)
        
        # Should only detect level 1 spell slot change, not level 0
        spell_slot_changes = [c for c in changes if 'spell_slots' in c.field_path]
        
        self.assertEqual(len(spell_slot_changes), 1, "Should only detect one spell slot change")
        
        slot_change = spell_slot_changes[0]
        self.assertIn('spell_slots.1', slot_change.field_path, "Should detect level 1 spell slots")
        self.assertEqual(slot_change.old_value, 0, "Old level 1 slots should be 0")
        self.assertEqual(slot_change.new_value, 2, "New level 1 slots should be 2")
        self.assertIn("Level 1 spell slots", slot_change.description, "Description should mention level 1")
        
        # Ensure no level 0 spell slot changes are reported
        level_0_changes = [c for c in changes if 'spell_slots.0' in c.field_path]
        self.assertEqual(len(level_0_changes), 0, "Should not detect level 0 spell slot changes")
    
    def test_spell_slot_priority_levels(self):
        """Test that spell slot changes have appropriate priority levels."""
        old_data = {
            'spellcasting': {
                'spell_slots': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            }
        }
        
        new_data = {
            'spellcasting': {
                'spell_slots': [0, 2, 1, 1, 0, 0, 0, 0, 0, 0]  # Level 1, 2, 3 slots
            }
        }
        
        changes = self.detector.detect_changes(old_data, new_data, self.context)
        spell_slot_changes = [c for c in changes if 'spell_slots' in c.field_path]
        
        # Should have 3 spell slot changes (levels 1, 2, 3)
        self.assertEqual(len(spell_slot_changes), 3)
        
        # Check priority levels
        for change in spell_slot_changes:
            if 'spell_slots.1' in change.field_path or 'spell_slots.2' in change.field_path:
                self.assertEqual(change.priority, ChangePriority.HIGH, 
                               f"Level 1-2 spell slots should be high priority: {change.field_path}")
            elif 'spell_slots.3' in change.field_path:
                self.assertEqual(change.priority, ChangePriority.MEDIUM,
                               f"Level 3+ spell slots should be medium priority: {change.field_path}")
    
    def test_spell_slot_field_path_format(self):
        """Test that spell slot changes use correct field path format."""
        old_data = {
            'spellcasting': {
                'spell_slots': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]
            }
        }
        
        new_data = {
            'spellcasting': {
                'spell_slots': [0, 3, 0, 0, 0, 0, 0, 0, 0, 0]
            }
        }
        
        changes = self.detector.detect_changes(old_data, new_data, self.context)
        spell_slot_changes = [c for c in changes if 'spell_slots' in c.field_path]
        
        self.assertEqual(len(spell_slot_changes), 1)
        change = spell_slot_changes[0]
        
        # Should use spellcasting.spell_slots.X format, not spells.spell_slots.X
        self.assertEqual(change.field_path, 'spellcasting.spell_slots.1')
        self.assertEqual(change.category, ChangeCategory.SPELLS)
        self.assertEqual(change.change_type, ChangeType.INCREMENTED)
    
    def test_no_spell_slot_changes_when_equal(self):
        """Test that no changes are detected when spell slots remain the same."""
        spell_data = {
            'spellcasting': {
                'spell_slots': [4, 2, 1, 0, 0, 0, 0, 0, 0, 0]
            }
        }
        
        changes = self.detector.detect_changes(spell_data, spell_data, self.context)
        spell_slot_changes = [c for c in changes if 'spell_slots' in c.field_path]
        
        self.assertEqual(len(spell_slot_changes), 0, "Should not detect changes when slots are equal")
    
    def test_spell_slot_decrease_detection(self):
        """Test that spell slot decreases are properly detected."""
        old_data = {
            'spellcasting': {
                'spell_slots': [0, 4, 3, 2, 0, 0, 0, 0, 0, 0]
            }
        }
        
        new_data = {
            'spellcasting': {
                'spell_slots': [0, 2, 1, 0, 0, 0, 0, 0, 0, 0]
            }
        }
        
        changes = self.detector.detect_changes(old_data, new_data, self.context)
        spell_slot_changes = [c for c in changes if 'spell_slots' in c.field_path]
        
        self.assertEqual(len(spell_slot_changes), 3)
        
        for change in spell_slot_changes:
            self.assertEqual(change.change_type, ChangeType.DECREMENTED)
            self.assertLess(change.new_value, change.old_value)
    
    def test_character_agnostic_behavior(self):
        """Test that spell detection works for any character without hardcoded values."""
        # Test with different character contexts
        contexts = [
            {'character_id': 111, 'character_name': 'Wizard'},
            {'character_id': 222, 'character_name': 'Sorcerer'},
            {'character_id': 333, 'character_name': 'Multiclass Fighter/Wizard'}
        ]
        
        old_data = {
            'spellcasting': {
                'spell_slots': [0, 1, 0, 0, 0, 0, 0, 0, 0, 0]
            }
        }
        
        new_data = {
            'spellcasting': {
                'spell_slots': [0, 2, 1, 0, 0, 0, 0, 0, 0, 0]
            }
        }
        
        for context in contexts:
            with self.subTest(character=context['character_name']):
                changes = self.detector.detect_changes(old_data, new_data, context)
                spell_slot_changes = [c for c in changes if 'spell_slots' in c.field_path]
                
                # Should work the same for any character
                self.assertEqual(len(spell_slot_changes), 2)
                
                # Verify no hardcoded character-specific logic
                for change in spell_slot_changes:
                    self.assertNotIn(str(context['character_id']), change.description)
                    self.assertNotIn(context['character_name'], change.field_path)


if __name__ == '__main__':
    unittest.main()