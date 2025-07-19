#!/usr/bin/env python3
"""
Unit tests for SpellcastingFormatter to ensure proper handling of different spell_slots formats.
"""

import unittest
from unittest.mock import MagicMock
from pathlib import Path
import sys

# Add src and parser to path
src_path = Path(__file__).parent.parent.parent.parent / 'src'
parser_path = Path(__file__).parent.parent.parent.parent / 'parser'
sys.path.insert(0, str(src_path))
sys.path.insert(0, str(parser_path))

from parser.formatters.spellcasting import SpellcastingFormatter
from parser.utils.text import TextProcessor


class TestSpellcastingFormatter(unittest.TestCase):
    """Test cases for the SpellcastingFormatter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.text_processor = TextProcessor()
        self.formatter = SpellcastingFormatter(self.text_processor)
    
    def test_normalize_spell_slots_list_format(self):
        """Test _normalize_spell_slots handles v6.0.0 list format correctly."""
        # Test v6.0.0 list format: [level1_slots, level2_slots, ...]
        spell_slots_list = [3, 1, 0, 0, 0, 0, 0, 0, 0]
        result = self.formatter._normalize_spell_slots(spell_slots_list)
        
        expected = {
            'level_1': 3,
            'level_2': 1
        }
        self.assertEqual(result, expected)
    
    def test_normalize_spell_slots_dict_format(self):
        """Test _normalize_spell_slots handles legacy dictionary format correctly."""
        # Test legacy nested dictionary format
        spell_slots_dict = {
            'regular_slots': {
                'level_1': 3,
                'level_2': 1
            }
        }
        result = self.formatter._normalize_spell_slots(spell_slots_dict)
        
        expected = {
            'level_1': 3,
            'level_2': 1
        }
        self.assertEqual(result, expected)
    
    def test_normalize_spell_slots_flat_dict_format(self):
        """Test _normalize_spell_slots handles flat dictionary format correctly."""
        # Test flat dictionary format (already normalized)
        spell_slots_dict = {
            'level_1': 3,
            'level_2': 1
        }
        result = self.formatter._normalize_spell_slots(spell_slots_dict)
        
        expected = {
            'level_1': 3,
            'level_2': 1
        }
        self.assertEqual(result, expected)
    
    def test_normalize_spell_slots_empty_list(self):
        """Test _normalize_spell_slots handles empty list correctly."""
        spell_slots_list = []
        result = self.formatter._normalize_spell_slots(spell_slots_list)
        
        expected = {}
        self.assertEqual(result, expected)
    
    def test_normalize_spell_slots_all_zeros(self):
        """Test _normalize_spell_slots handles list with all zeros correctly."""
        spell_slots_list = [0, 0, 0, 0, 0, 0, 0, 0, 0]
        result = self.formatter._normalize_spell_slots(spell_slots_list)
        
        expected = {}
        self.assertEqual(result, expected)
    
    def test_normalize_spell_slots_high_level_slots(self):
        """Test _normalize_spell_slots handles high-level spell slots correctly."""
        spell_slots_list = [2, 1, 1, 1, 1, 1, 1, 1, 1]  # All levels 1-9
        result = self.formatter._normalize_spell_slots(spell_slots_list)
        
        expected = {
            'level_1': 2,
            'level_2': 1,
            'level_3': 1,
            'level_4': 1,
            'level_5': 1,
            'level_6': 1,
            'level_7': 1,
            'level_8': 1,
            'level_9': 1
        }
        self.assertEqual(result, expected)
    
    def test_normalize_spell_slots_invalid_format(self):
        """Test _normalize_spell_slots handles invalid format gracefully."""
        # Test with string (invalid format)
        result = self.formatter._normalize_spell_slots("invalid")
        self.assertEqual(result, {})
        
        # Test with None
        result = self.formatter._normalize_spell_slots(None)
        self.assertEqual(result, {})
        
        # Test with number
        result = self.formatter._normalize_spell_slots(123)
        self.assertEqual(result, {})
    
    def test_generate_spell_slots_integration(self):
        """Test that _generate_spell_slots works with the normalized data."""
        # Create mock character data with v6.0.0 list format
        character_data = {
            'basic_info': {
                'name': 'Test Character',
                'level': 3,
                'classes': [{'name': 'Sorcerer'}]
            },
            'spell_slots': [4, 2, 0, 0, 0, 0, 0, 0, 0]  # v6.0.0 list format
        }
        
        result = self.formatter._generate_spell_slots(character_data)
        
        # Check that the result contains the expected spell slots
        self.assertIn("'Level 1'", result)
        self.assertIn("uses: 4", result)
        self.assertIn("'Level 2'", result)
        self.assertIn("uses: 2", result)
        self.assertIn("'Sorcery Points'", result)
        self.assertIn("uses: 3", result)  # Level 3 sorcerer gets 3 sorcery points


if __name__ == '__main__':
    unittest.main()