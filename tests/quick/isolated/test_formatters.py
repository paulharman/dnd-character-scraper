"""
Isolated formatter tests for quick validation.

Tests output formatters without requiring full character processing.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path
import tempfile
import os

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from formatters.yaml_formatter import YAMLFormatter
from formatters.json_formatter import JSONFormatter

from ..factories.character_archetypes import CharacterArchetypeFactory

class TestYAMLFormatter:
    """Tests for YAML formatter."""
    
    @pytest.mark.quick
    def test_basic_yaml_formatting(self):
        """Test basic YAML formatting."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        formatter = YAMLFormatter()
        
        result = formatter.format(character_data)
        
        assert result is not None
        assert isinstance(result, str)
        assert 'name: Test Fighter' in result
        assert 'level: 1' in result

    @pytest.mark.quick
    def test_yaml_with_complex_data(self):
        """Test YAML formatting with complex character data."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        formatter = YAMLFormatter()
        
        result = formatter.format(character_data)
        
        assert result is not None
        assert isinstance(result, str)
        assert 'classes:' in result
        assert 'Fighter' in result
        assert 'Wizard' in result

    @pytest.mark.quick
    def test_yaml_with_special_characters(self):
        """Test YAML formatting with special characters."""
        character_data = {
            "name": "Test's Character with \"quotes\"",
            "description": "A character with special chars: & < > []",
            "level": 5
        }
        formatter = YAMLFormatter()
        
        result = formatter.format(character_data)
        
        assert result is not None
        assert isinstance(result, str)
        # Should handle special characters properly
        assert 'Test\'s Character' in result or 'Test&apos;s Character' in result

    @pytest.mark.quick
    def test_yaml_empty_data(self):
        """Test YAML formatting with empty data."""
        formatter = YAMLFormatter()
        
        result = formatter.format({})
        
        assert result is not None
        assert isinstance(result, str)
        assert result.strip() == '{}' or result.strip() == ''

    @pytest.mark.quick
    def test_yaml_none_data(self):
        """Test YAML formatting with None data."""
        formatter = YAMLFormatter()
        
        result = formatter.format(None)
        
        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.quick
    def test_yaml_performance(self):
        """Test YAML formatting performance."""
        import time
        
        character_data = CharacterArchetypeFactory.create_wizard(level=10)
        formatter = YAMLFormatter()
        
        start_time = time.time()
        result = formatter.format(character_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 0.1  # Should complete in under 100ms
        assert result is not None

class TestJSONFormatter:
    """Tests for JSON formatter."""
    
    @pytest.mark.quick
    def test_basic_json_formatting(self):
        """Test basic JSON formatting."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        formatter = JSONFormatter()
        
        result = formatter.format(character_data)
        
        assert result is not None
        assert isinstance(result, str)
        assert '"name": "Test Fighter"' in result
        assert '"level": 1' in result

    @pytest.mark.quick
    def test_json_with_complex_data(self):
        """Test JSON formatting with complex character data."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        formatter = JSONFormatter()
        
        result = formatter.format(character_data)
        
        assert result is not None
        assert isinstance(result, str)
        assert '"classes":' in result
        assert '"Fighter"' in result
        assert '"Wizard"' in result

    @pytest.mark.quick
    def test_json_pretty_formatting(self):
        """Test JSON pretty formatting."""
        character_data = CharacterArchetypeFactory.create_rogue(level=3)
        formatter = JSONFormatter(pretty=True)
        
        result = formatter.format(character_data)
        
        assert result is not None
        assert isinstance(result, str)
        # Pretty formatted JSON should have newlines and indentation
        assert '\n' in result
        assert '  ' in result  # Indentation

    @pytest.mark.quick
    def test_json_compact_formatting(self):
        """Test JSON compact formatting."""
        character_data = CharacterArchetypeFactory.create_rogue(level=3)
        formatter = JSONFormatter(pretty=False)
        
        result = formatter.format(character_data)
        
        assert result is not None
        assert isinstance(result, str)
        # Compact JSON should not have unnecessary whitespace
        assert result.count('\n') <= 1  # At most one newline at end

    @pytest.mark.quick
    def test_json_with_special_characters(self):
        """Test JSON formatting with special characters."""
        character_data = {
            "name": "Test's Character with \"quotes\"",
            "description": "A character with special chars: & < > []",
            "level": 5
        }
        formatter = JSONFormatter()
        
        result = formatter.format(character_data)
        
        assert result is not None
        assert isinstance(result, str)
        # Should properly escape special characters
        assert '\\"' in result  # Escaped quotes
        assert '\\\\"' not in result  # No double escaping

    @pytest.mark.quick
    def test_json_empty_data(self):
        """Test JSON formatting with empty data."""
        formatter = JSONFormatter()
        
        result = formatter.format({})
        
        assert result is not None
        assert isinstance(result, str)
        assert result.strip() == '{}'

    @pytest.mark.quick
    def test_json_none_data(self):
        """Test JSON formatting with None data."""
        formatter = JSONFormatter()
        
        result = formatter.format(None)
        
        assert result is not None
        assert isinstance(result, str)
        assert result.strip() == 'null'

    @pytest.mark.quick
    def test_json_performance(self):
        """Test JSON formatting performance."""
        import time
        
        character_data = CharacterArchetypeFactory.create_wizard(level=15)
        formatter = JSONFormatter()
        
        start_time = time.time()
        result = formatter.format(character_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 0.1  # Should complete in under 100ms
        assert result is not None

class TestFormatterInterface:
    """Tests for formatter interface compliance."""
    
    @pytest.mark.quick
    def test_formatter_interface_compliance(self):
        """Test that formatters implement required interface."""
        formatters = [YAMLFormatter(), JSONFormatter()]
        
        for formatter in formatters:
            assert hasattr(formatter, 'format')
            assert callable(getattr(formatter, 'format'))

    @pytest.mark.quick
    def test_formatter_output_types(self):
        """Test that formatters return string output."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        formatters = [YAMLFormatter(), JSONFormatter()]
        
        for formatter in formatters:
            result = formatter.format(character_data)
            assert isinstance(result, str)
            assert len(result) > 0

    @pytest.mark.quick
    def test_formatter_consistency(self):
        """Test formatter consistency across multiple calls."""
        character_data = CharacterArchetypeFactory.create_wizard(level=5)
        formatter = JSONFormatter()
        
        result1 = formatter.format(character_data)
        result2 = formatter.format(character_data)
        
        assert result1 == result2  # Should be deterministic

class TestFormatterErrorHandling:
    """Tests for formatter error handling."""
    
    @pytest.mark.quick
    def test_formatter_with_circular_references(self):
        """Test formatter handling of circular references."""
        # Create circular reference
        data = {"name": "Test"}
        data["self"] = data  # Circular reference
        
        formatter = JSONFormatter()
        
        # Should handle circular references gracefully
        try:
            result = formatter.format(data)
            assert result is not None
        except (ValueError, TypeError) as e:
            # Expected error for circular references
            assert "circular" in str(e).lower() or "recursion" in str(e).lower()

    @pytest.mark.quick
    def test_formatter_with_unserializable_data(self):
        """Test formatter handling of unserializable data."""
        import datetime
        
        data = {
            "name": "Test",
            "timestamp": datetime.datetime.now(),  # Not JSON serializable by default
            "function": lambda x: x  # Not serializable
        }
        
        formatter = JSONFormatter()
        
        # Should handle unserializable data gracefully
        try:
            result = formatter.format(data)
            assert result is not None
        except (ValueError, TypeError) as e:
            # Expected error for unserializable data
            assert "serializable" in str(e).lower() or "json" in str(e).lower()

    @pytest.mark.quick
    def test_formatter_with_very_large_data(self):
        """Test formatter handling of large data sets."""
        # Create large data set
        large_data = {
            "name": "Large Character",
            "items": [f"item_{i}" for i in range(1000)],
            "description": "A" * 10000  # Large string
        }
        
        formatter = JSONFormatter()
        
        start_time = time.time()
        result = formatter.format(large_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 1.0  # Should complete in reasonable time
        assert result is not None
        assert len(result) > 10000  # Should contain the large data

# File output tests
class TestFormatterFileOutput:
    """Tests for formatter file output capabilities."""
    
    @pytest.mark.quick
    def test_formatter_file_output(self):
        """Test formatter file output if supported."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        formatter = JSONFormatter()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.json') as f:
            temp_file = f.name
        
        try:
            # Test if formatter supports file output
            if hasattr(formatter, 'format_to_file'):
                result = formatter.format_to_file(character_data, temp_file)
                assert result is True
                assert os.path.exists(temp_file)
                
                # Verify file contents
                with open(temp_file, 'r') as f:
                    content = f.read()
                    assert '"name": "Test Fighter"' in content
            else:
                # Manual file output test
                result = formatter.format(character_data)
                with open(temp_file, 'w') as f:
                    f.write(result)
                
                assert os.path.exists(temp_file)
                
                # Verify file contents
                with open(temp_file, 'r') as f:
                    content = f.read()
                    assert '"name": "Test Fighter"' in content
        finally:
            # Clean up
            if os.path.exists(temp_file):
                os.unlink(temp_file)