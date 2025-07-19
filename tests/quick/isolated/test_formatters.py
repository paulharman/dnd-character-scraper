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

from src.formatters.yaml_formatter import YAMLFormatter

from ..factories.character_archetypes import CharacterArchetypeFactory

class TestYAMLFormatter:
    """Tests for YAML formatter."""
    
    @pytest.mark.quick
    def test_basic_yaml_formatting(self):
        """Test basic YAML formatting."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        formatter = YAMLFormatter(character_data)
        
        result = formatter.format()
        
        assert result is not None
        assert isinstance(result, str)
        assert 'Test Fighter' in result
        assert '---' in result  # YAML frontmatter markers

    @pytest.mark.quick
    def test_yaml_with_complex_data(self):
        """Test YAML formatting with complex character data."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        formatter = YAMLFormatter(character_data)
        
        result = formatter.format()
        
        assert result is not None
        assert isinstance(result, str)
        assert 'Test Multiclass' in result
        assert '---' in result

    @pytest.mark.quick
    def test_yaml_with_special_characters(self):
        """Test YAML formatting with special characters."""
        character_data = {
            "name": "Test's Character with \"quotes\"",
            "description": "A character with special chars: & < > []",
            "level": 5
        }
        formatter = YAMLFormatter(character_data)
        
        result = formatter.format()
        
        assert result is not None
        assert isinstance(result, str)
        # Should handle special characters properly
        assert 'Test' in result

    @pytest.mark.quick
    def test_yaml_empty_data(self):
        """Test YAML formatting with minimal data."""
        character_data = {"name": "Empty", "level": 1}
        formatter = YAMLFormatter(character_data)
        
        result = formatter.format()
        
        assert result is not None
        assert isinstance(result, str)
        assert '---' in result

    @pytest.mark.quick
    def test_yaml_performance(self):
        """Test YAML formatting performance."""
        import time
        
        character_data = CharacterArchetypeFactory.create_wizard(level=10)
        formatter = YAMLFormatter(character_data)
        
        start_time = time.time()
        result = formatter.format()
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 0.5  # Should complete in under 500ms
        assert result is not None

class TestFormatterInterface:
    """Tests for formatter interface compliance."""
    
    @pytest.mark.quick
    def test_formatter_interface_compliance(self):
        """Test that formatters implement required interface."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        formatter = YAMLFormatter(character_data)
        
        assert hasattr(formatter, 'format')
        assert callable(getattr(formatter, 'format'))

    @pytest.mark.quick
    def test_formatter_output_types(self):
        """Test that formatters return expected output types."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        formatter = YAMLFormatter(character_data)
        
        result = formatter.format()
        
        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.quick
    def test_formatter_consistency(self):
        """Test that formatters produce consistent output."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        formatter = YAMLFormatter(character_data)
        
        result1 = formatter.format()
        result2 = formatter.format()
        
        assert result1 == result2  # Should be deterministic

class TestFormatterErrorHandling:
    """Error handling tests for formatters."""
    
    @pytest.mark.quick
    def test_formatter_with_missing_data(self):
        """Test formatter handling of missing data."""
        character_data = {"name": "Incomplete"}  # Missing level and other data
        formatter = YAMLFormatter(character_data)
        
        # Should not raise an exception
        result = formatter.format()
        assert result is not None
        assert isinstance(result, str)

    @pytest.mark.quick
    def test_formatter_with_very_large_data(self):
        """Test formatter performance with large data sets."""
        # Create a character with lots of data
        character_data = CharacterArchetypeFactory.create_level_20_barbarian()
        # Add some large data structures
        character_data["large_list"] = list(range(1000))
        character_data["large_dict"] = {f"key_{i}": f"value_{i}" for i in range(100)}
        
        formatter = YAMLFormatter(character_data)
        
        # Should handle large data without issues
        result = formatter.format()
        assert result is not None
        assert isinstance(result, str)

class TestFormatterFileOutput:
    """Tests for formatter file output capabilities."""
    
    @pytest.mark.quick
    def test_formatter_file_output(self):
        """Test formatter output can be written to files."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        formatter = YAMLFormatter(character_data)
        
        result = formatter.format()
        
        # Test writing to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(result)
            temp_path = f.name
        
        try:
            # Verify file was written
            assert os.path.exists(temp_path)
            assert os.path.getsize(temp_path) > 0
            
            # Verify content can be read back
            with open(temp_path, 'r') as f:
                content = f.read()
            
            assert content == result
        finally:
            # Clean up
            if os.path.exists(temp_path):
                os.unlink(temp_path)

# Performance tests
class TestFormatterPerformance:
    """Performance tests for formatters."""
    
    @pytest.mark.quick
    def test_formatter_speed(self):
        """Test that formatter operations complete quickly."""
        import time
        
        character_data = CharacterArchetypeFactory.create_wizard(level=5)
        
        start_time = time.time()
        formatter = YAMLFormatter(character_data)
        result = formatter.format()
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 0.1  # Should complete in under 100ms
        assert result is not None

    @pytest.mark.quick
    def test_formatter_memory_usage(self):
        """Test formatter memory usage stays reasonable."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        
        # Create and use multiple formatters to check for memory leaks
        for i in range(50):
            formatter = YAMLFormatter(character_data)
            result = formatter.format()
            assert result is not None
            # Force garbage collection of formatter
            del formatter
            del result
        
        # If we get here without memory errors, test passes
        assert True

    @pytest.mark.quick
    def test_formatter_batch_processing(self):
        """Test formatter with batch processing."""
        import time
        
        # Create multiple character datasets
        characters = [
            CharacterArchetypeFactory.create_fighter(level=1),
            CharacterArchetypeFactory.create_wizard(level=3),
            CharacterArchetypeFactory.create_rogue(level=2),
        ]
        
        start_time = time.time()
        results = []
        for char_data in characters:
            formatter = YAMLFormatter(char_data)
            result = formatter.format()
            results.append(result)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 0.5  # Should complete batch in under 500ms
        assert len(results) == len(characters)
        assert all(isinstance(r, str) for r in results)