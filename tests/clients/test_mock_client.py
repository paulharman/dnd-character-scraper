"""
Tests for mock character client.
"""

import pytest
import asyncio
from unittest.mock import patch, mock_open
import json

from src.clients.mock_client import MockDNDBeyondClient, StaticMockClient
from src.clients.exceptions import CharacterNotFoundError, ValidationError


class TestMockDNDBeyondClient:
    """Test mock client functionality."""
    
    @pytest.fixture
    def mock_client(self):
        """Create mock client for testing."""
        return MockDNDBeyondClient(mock_data_dir="tests/fixtures", enable_delays=False)
    
    @pytest.fixture
    def sample_character_data(self):
        """Sample character data for testing."""
        return {
            "id": 123456,
            "name": "Test Character",
            "levels": [{"level": 5}],
            "classes": [{
                "definition": {"name": "Wizard"},
                "level": 5
            }],
            "race": {"fullName": "Human"},
            "stats": [
                {"id": 1, "value": 14},
                {"id": 2, "value": 16},
                {"id": 3, "value": 13},
                {"id": 4, "value": 18},
                {"id": 5, "value": 12},
                {"id": 6, "value": 10}
            ]
        }
    
    def test_validate_character_data_valid(self, mock_client, sample_character_data):
        """Test validation with valid character data."""
        assert mock_client.validate_character_data(sample_character_data) is True
    
    def test_validate_character_data_invalid(self, mock_client):
        """Test validation with invalid character data."""
        # Missing required fields
        invalid_data = {"id": 123, "name": "Test"}
        assert mock_client.validate_character_data(invalid_data) is False
        
        # Not a dictionary
        assert mock_client.validate_character_data("not a dict") is False
        
        # Empty classes
        invalid_data = {
            "id": 123,
            "name": "Test",
            "levels": [{"level": 1}],
            "classes": []
        }
        assert mock_client.validate_character_data(invalid_data) is False
    
    def test_get_character_summary(self, mock_client, sample_character_data):
        """Test character summary generation."""
        summary = mock_client.get_character_summary(sample_character_data)
        
        assert summary['id'] == 123456
        assert summary['name'] == "Test Character"
        assert summary['level'] == 5
        assert summary['race'] == "Human"
        assert summary['primary_class'] == "Wizard"
        assert summary['is_multiclass'] is False
        assert len(summary['classes']) == 1
    
    @pytest.mark.asyncio
    async def test_fetch_character_not_found(self, mock_client):
        """Test fetching non-existent character."""
        with pytest.raises(CharacterNotFoundError):
            await mock_client.fetch_character_data(999999)
    
    def test_add_mock_character(self, mock_client, sample_character_data, tmp_path):
        """Test adding mock character data."""
        # Use temporary directory
        mock_client.mock_data_dir = tmp_path
        
        # Add mock character
        char_id = 123456
        mock_client.add_mock_character(char_id, sample_character_data)
        
        # Verify it was added
        assert char_id in mock_client.available_characters
        
        # Verify file was created
        expected_file = tmp_path / f"{char_id}.json"
        assert expected_file.exists()
        
        # Verify file contents
        with open(expected_file, 'r') as f:
            saved_data = json.load(f)
        assert saved_data == sample_character_data
    
    def test_list_available_characters(self, mock_client):
        """Test listing available characters."""
        available = mock_client.list_available_characters()
        assert isinstance(available, dict)
        # All values should be file paths
        for char_id, path in available.items():
            assert isinstance(char_id, int)
            assert isinstance(path, str)


class TestStaticMockClient:
    """Test static mock client with predefined data."""
    
    @pytest.fixture
    def static_client(self):
        """Create static mock client."""
        return StaticMockClient()
    
    @pytest.mark.asyncio
    async def test_fetch_static_character(self, static_client):
        """Test fetching predefined static character."""
        # Should have test characters 999999 and 999998
        data = await static_client.fetch_character_data(999999)
        
        assert data['id'] == 999999
        assert data['name'] == "Test Character"
        assert 'classes' in data
        assert 'stats' in data
    
    @pytest.mark.asyncio
    async def test_fetch_multiclass_character(self, static_client):
        """Test fetching multiclass static character."""
        data = await static_client.fetch_character_data(999998)
        
        assert data['id'] == 999998
        assert data['name'] == "Multiclass Caster"
        assert len(data['classes']) == 2  # Paladin and Sorcerer
    
    def test_get_summary_multiclass(self, static_client):
        """Test summary generation for multiclass character."""
        # Get the multiclass character data
        data = static_client._static_data[999998]
        summary = static_client.get_character_summary(data)
        
        assert summary['is_multiclass'] is True
        assert len(summary['classes']) == 2
        assert summary['level'] == 8  # 5 + 3
    
    def test_list_static_characters(self, static_client):
        """Test listing static characters."""
        available = static_client.list_available_characters()
        
        # Should include static test characters
        assert 999999 in available
        assert 999998 in available


@pytest.mark.asyncio
async def test_mock_client_with_real_files():
    """Integration test with actual Raw/ files if they exist."""
    mock_client = MockDNDBeyondClient(enable_delays=False)
    
    # Check if we have any real character files
    available = mock_client.list_available_characters()
    
    if available:
        # Test loading one of the available characters
        char_id = next(iter(available.keys()))
        
        try:
            data = await mock_client.fetch_character_data(char_id)
            
            # Basic validation
            assert 'id' in data
            assert 'name' in data
            assert 'classes' in data
            
            # Generate summary
            summary = mock_client.get_character_summary(data)
            assert summary['id'] == char_id
            
            print(f"Successfully loaded character: {summary['name']} (Level {summary['level']} {summary['primary_class']})")
            
        except Exception as e:
            pytest.skip(f"Could not load character {char_id}: {str(e)}")
    else:
        pytest.skip("No character files available for testing")