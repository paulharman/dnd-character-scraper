"""
Smoke tests for API integration.

Tests basic API integration without making real API calls.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ..factories.character_archetypes import CharacterArchetypeFactory
from ..factories.api_responses import APIResponseFactory

class TestAPIResponseValidation:
    """Smoke tests for API response validation."""
    
    @pytest.mark.quick
    def test_successful_response_structure(self):
        """Test that successful responses have correct structure."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        response = APIResponseFactory.create_successful_character_response(character_data)
        
        # Check required fields
        assert "success" in response
        assert "data" in response
        assert "message" in response
        assert response["success"] is True
        assert response["data"] is not None

    @pytest.mark.quick
    def test_error_response_structure(self):
        """Test that error responses have correct structure."""
        response = APIResponseFactory.create_character_not_found_response("12345")
        
        # Check required fields
        assert "success" in response
        assert "error" in response
        assert response["success"] is False
        assert response["error"] is not None
        assert "code" in response["error"]

    @pytest.mark.quick
    def test_all_response_types(self):
        """Test all response types can be created."""
        response_types = APIResponseFactory.get_available_response_types()
        
        for response_type in response_types:
            if response_type == 'success':
                character_data = CharacterArchetypeFactory.create_fighter(level=1)
                response = APIResponseFactory.create_mock_response_by_type(
                    response_type, character_data=character_data
                )
            else:
                response = APIResponseFactory.create_mock_response_by_type(response_type)
            
            assert response is not None
            assert "success" in response
            assert isinstance(response["success"], bool)

class TestAPIClientIntegration:
    """Smoke tests for API client integration."""
    
    @pytest.mark.quick
    def test_mock_client_basic_functionality(self):
        """Test mock client basic functionality."""
        try:
            from clients.mock_client import MockClient
            
            client = MockClient()
            
            # Test different character types
            test_cases = ["fighter", "wizard", "rogue"]
            for character_type in test_cases:
                result = client.get_character(character_type)
                assert result is not None
                assert "success" in result
                assert result["success"] is True
                assert "data" in result
                
        except ImportError:
            pytest.skip("MockClient not available")

    @pytest.mark.quick
    @patch('requests.get')
    def test_real_client_error_handling(self, mock_get):
        """Test real client error handling."""
        try:
            from clients.dnd_beyond_client import DNDBeyondClient
            
            # Mock a network error
            mock_get.side_effect = Exception("Network error")
            
            client = DNDBeyondClient()
            result = client.get_character("12345")
            
            assert result is not None
            assert "success" in result
            assert result["success"] is False
            assert "error" in result
            
        except ImportError:
            pytest.skip("DNDBeyondClient not available")

    @pytest.mark.quick
    @patch('requests.get')
    def test_real_client_success_response(self, mock_get):
        """Test real client success response handling."""
        try:
            from clients.dnd_beyond_client import DNDBeyondClient
            
            # Mock a successful response
            character_data = CharacterArchetypeFactory.create_fighter(level=1)
            api_response = APIResponseFactory.create_successful_character_response(character_data)
            
            mock_response = Mock()
            mock_response.json.return_value = api_response
            mock_response.status_code = 200
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response
            
            client = DNDBeyondClient()
            result = client.get_character("12345")
            
            assert result is not None
            assert result["success"] is True
            assert "data" in result
            assert result["data"]["name"] == "Test Fighter"
            
        except ImportError:
            pytest.skip("DNDBeyondClient not available")

class TestAPIDataValidation:
    """Smoke tests for API data validation."""
    
    @pytest.mark.quick
    def test_character_data_completeness(self):
        """Test that character data contains expected fields."""
        character_data = CharacterArchetypeFactory.create_wizard(level=5)
        
        # Required fields
        required_fields = ["name", "level", "classes", "ability_scores", "race", "background"]
        for field in required_fields:
            assert field in character_data, f"Missing required field: {field}"
        
        # Spellcaster-specific fields
        if character_data.get("is_spellcaster"):
            assert "spell_slots" in character_data

    @pytest.mark.quick
    def test_ability_scores_validation(self):
        """Test ability scores validation."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        ability_scores = character_data["ability_scores"]
        
        # Check all abilities are present
        required_abilities = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        for ability in required_abilities:
            assert ability in ability_scores, f"Missing ability: {ability}"
            assert isinstance(ability_scores[ability], int), f"Ability {ability} should be integer"
            assert 1 <= ability_scores[ability] <= 30, f"Ability {ability} out of range"

    @pytest.mark.quick
    def test_class_data_validation(self):
        """Test class data validation."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        classes = character_data["classes"]
        
        assert isinstance(classes, list), "Classes should be a list"
        assert len(classes) > 0, "Should have at least one class"
        
        total_level = 0
        for cls in classes:
            assert "name" in cls, "Class should have name"
            assert "level" in cls, "Class should have level"
            assert "hit_die" in cls, "Class should have hit_die"
            assert isinstance(cls["level"], int), "Class level should be integer"
            assert 1 <= cls["level"] <= 20, "Class level should be 1-20"
            total_level += cls["level"]
        
        assert total_level == character_data["level"], "Total class levels should match character level"

    @pytest.mark.quick
    def test_spell_data_validation(self):
        """Test spell data validation."""
        character_data = CharacterArchetypeFactory.create_wizard(level=5)
        
        if character_data.get("is_spellcaster") and "spell_slots" in character_data:
            spell_slots = character_data["spell_slots"]
            
            for level, slots in spell_slots.items():
                assert isinstance(level, str), "Spell level should be string"
                assert level.isdigit(), "Spell level should be numeric string"
                assert 1 <= int(level) <= 9, "Spell level should be 1-9"
                assert isinstance(slots, int), "Spell slots should be integer"
                assert slots >= 0, "Spell slots should be non-negative"

class TestAPIPerformance:
    """Smoke tests for API performance."""
    
    @pytest.mark.quick
    def test_response_creation_performance(self):
        """Test API response creation performance."""
        import time
        
        character_data = CharacterArchetypeFactory.create_fighter(level=10)
        
        start_time = time.time()
        for i in range(100):
            APIResponseFactory.create_successful_character_response(character_data)
        end_time = time.time()
        
        execution_time = end_time - start_time
        assert execution_time < 1.0, "Response creation should be fast"

    @pytest.mark.quick
    def test_mock_client_performance(self):
        """Test mock client performance."""
        import time
        
        try:
            from clients.mock_client import MockClient
            
            client = MockClient()
            
            start_time = time.time()
            for i in range(100):
                client.get_character("fighter")
            end_time = time.time()
            
            execution_time = end_time - start_time
            assert execution_time < 1.0, "Mock client should be very fast"
            
        except ImportError:
            pytest.skip("MockClient not available")

class TestAPIErrorHandling:
    """Smoke tests for API error handling."""
    
    @pytest.mark.quick
    def test_error_response_types(self):
        """Test different error response types."""
        error_types = [
            'not_found', 'error', 'rate_limit', 'timeout', 'network_error'
        ]
        
        for error_type in error_types:
            response = APIResponseFactory.create_mock_response_by_type(error_type)
            assert response is not None
            assert response["success"] is False
            assert "error" in response
            assert response["error"] is not None

    @pytest.mark.quick
    def test_malformed_data_handling(self):
        """Test handling of malformed data."""
        response = APIResponseFactory.create_malformed_character_response()
        
        assert response is not None
        assert response["success"] is True  # Response claims success
        assert "data" in response
        
        # But data should be malformed
        data = response["data"]
        assert data["name"] == "Malformed Character"
        # Level should be invalid
        assert not isinstance(data["level"], int)

    @pytest.mark.quick
    def test_partial_data_handling(self):
        """Test handling of partial data."""
        response = APIResponseFactory.create_partial_character_response()
        
        assert response is not None
        assert response["success"] is True
        assert "data" in response
        
        # Data should be incomplete
        data = response["data"]
        assert "name" in data
        assert "level" in data
        # But should be missing some required fields
        assert "intelligence" not in data["ability_scores"]

class TestAPIDataConsistency:
    """Smoke tests for API data consistency."""
    
    @pytest.mark.quick
    def test_character_archetype_consistency(self):
        """Test consistency between character archetypes."""
        archetypes = [
            CharacterArchetypeFactory.create_fighter(level=1),
            CharacterArchetypeFactory.create_wizard(level=1),
            CharacterArchetypeFactory.create_rogue(level=1)
        ]
        
        for archetype in archetypes:
            # All should have same basic structure
            assert "name" in archetype
            assert "level" in archetype
            assert "classes" in archetype
            assert "ability_scores" in archetype
            assert "race" in archetype
            assert "background" in archetype
            
            # All should have valid levels
            assert archetype["level"] == 1
            
            # All should have valid proficiency bonus
            assert archetype["proficiency_bonus"] == 2  # Level 1 = +2

    @pytest.mark.quick
    def test_response_wrapper_consistency(self):
        """Test consistency of response wrappers."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        
        # Test multiple response creations
        responses = []
        for i in range(5):
            response = APIResponseFactory.create_successful_character_response(character_data)
            responses.append(response)
        
        # All responses should be identical
        for response in responses[1:]:
            assert response["success"] == responses[0]["success"]
            assert response["data"]["name"] == responses[0]["data"]["name"]
            assert response["data"]["level"] == responses[0]["data"]["level"]

    @pytest.mark.quick
    def test_level_scaling_consistency(self):
        """Test level scaling consistency."""
        levels = [1, 5, 10, 15, 20]
        
        for level in levels:
            character_data = CharacterArchetypeFactory.create_fighter(level=level)
            
            # Level should match
            assert character_data["level"] == level
            
            # Proficiency bonus should scale correctly
            expected_prof_bonus = 2 + ((level - 1) // 4)
            assert character_data["proficiency_bonus"] == expected_prof_bonus
            
            # HP should scale with level
            expected_min_hp = 10 + ((level - 1) * 1)  # Minimum HP growth
            assert character_data["hit_points"] >= expected_min_hp

class TestAPIIntegrationScenarios:
    """Smoke tests for API integration scenarios."""
    
    @pytest.mark.quick
    def test_character_fetch_scenario(self):
        """Test character fetching scenario."""
        # Simulate fetching a character
        character_data = CharacterArchetypeFactory.create_wizard(level=3)
        api_response = APIResponseFactory.create_successful_character_response(character_data)
        
        # Verify the complete flow
        assert api_response["success"] is True
        fetched_character = api_response["data"]
        
        # Verify character was fetched correctly
        assert fetched_character["name"] == "Test Wizard"
        assert fetched_character["level"] == 3
        assert fetched_character["is_spellcaster"] is True
        assert "spell_slots" in fetched_character

    @pytest.mark.quick
    def test_character_not_found_scenario(self):
        """Test character not found scenario."""
        # Simulate character not found
        api_response = APIResponseFactory.create_character_not_found_response("99999")
        
        # Verify error handling
        assert api_response["success"] is False
        assert "error" in api_response
        assert api_response["error"]["code"] == "CHARACTER_NOT_FOUND"
        assert "99999" in api_response["error"]["details"]

    @pytest.mark.quick
    def test_rate_limiting_scenario(self):
        """Test rate limiting scenario."""
        # Simulate rate limiting
        api_response = APIResponseFactory.create_rate_limit_response()
        
        # Verify rate limit handling
        assert api_response["success"] is False
        assert "error" in api_response
        assert api_response["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "retry_after" in api_response["error"]
        assert api_response["error"]["retry_after"] == 60