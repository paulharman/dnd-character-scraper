"""
Smoke tests for core functionality.

These tests verify that basic functionality works without extensive testing.
"""

import pytest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ..factories.character_archetypes import CharacterArchetypeFactory
from ..factories.api_responses import APIResponseFactory
from ..factories.scenarios import ScenarioFactory

class TestBasicCharacterProcessing:
    """Smoke tests for basic character processing."""
    
    @pytest.mark.quick
    def test_character_creation_smoke(self):
        """Smoke test for character creation."""
        # Test that we can create basic character data
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        
        assert character_data is not None
        assert character_data["name"] == "Test Fighter"
        assert character_data["level"] == 1
        assert character_data["classes"][0]["name"] == "Fighter"
        assert character_data["is_spellcaster"] is False

    @pytest.mark.quick
    def test_spellcaster_creation_smoke(self):
        """Smoke test for spellcaster creation."""
        character_data = CharacterArchetypeFactory.create_wizard(level=3)
        
        assert character_data is not None
        assert character_data["name"] == "Test Wizard"
        assert character_data["level"] == 3
        assert character_data["classes"][0]["name"] == "Wizard"
        assert character_data["is_spellcaster"] is True
        assert "spell_slots" in character_data

    @pytest.mark.quick
    def test_multiclass_creation_smoke(self):
        """Smoke test for multiclass character creation."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(3, 2)
        
        assert character_data is not None
        assert character_data["level"] == 5
        assert len(character_data["classes"]) == 2
        assert any(cls["name"] == "Fighter" for cls in character_data["classes"])
        assert any(cls["name"] == "Wizard" for cls in character_data["classes"])

    @pytest.mark.quick
    def test_high_level_character_smoke(self):
        """Smoke test for high-level character creation."""
        character_data = CharacterArchetypeFactory.create_level_20_barbarian()
        
        assert character_data is not None
        assert character_data["level"] == 20
        assert character_data["classes"][0]["name"] == "Barbarian"
        assert character_data["hit_points"] > 200  # High level should have high HP

class TestAPIResponseHandling:
    """Smoke tests for API response handling."""
    
    @pytest.mark.quick
    def test_successful_response_smoke(self):
        """Smoke test for successful API response."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        response = APIResponseFactory.create_successful_character_response(character_data)
        
        assert response is not None
        assert response["success"] is True
        assert "data" in response
        assert response["data"]["name"] == "Test Fighter"

    @pytest.mark.quick
    def test_error_response_smoke(self):
        """Smoke test for error API response."""
        response = APIResponseFactory.create_character_not_found_response("12345")
        
        assert response is not None
        assert response["success"] is False
        assert "error" in response
        assert response["error"]["code"] == "CHARACTER_NOT_FOUND"

    @pytest.mark.quick
    def test_malformed_response_smoke(self):
        """Smoke test for malformed API response."""
        response = APIResponseFactory.create_malformed_character_response()
        
        assert response is not None
        assert response["success"] is True  # Response says success but data is malformed
        assert "data" in response
        assert response["data"]["name"] == "Malformed Character"

    @pytest.mark.quick
    def test_rate_limit_response_smoke(self):
        """Smoke test for rate limit response."""
        response = APIResponseFactory.create_rate_limit_response()
        
        assert response is not None
        assert response["success"] is False
        assert "error" in response
        assert response["error"]["code"] == "RATE_LIMIT_EXCEEDED"

class TestScenarioExecution:
    """Smoke tests for scenario execution."""
    
    @pytest.mark.quick
    def test_new_character_scenario_smoke(self):
        """Smoke test for new character scenario."""
        scenario = ScenarioFactory.create_new_character_scenario()
        
        assert scenario is not None
        assert scenario["name"] == "New Character Creation"
        assert "character_data" in scenario
        assert "api_response" in scenario
        assert "expected_outcomes" in scenario
        assert scenario["expected_outcomes"]["ac_calculation"] == 16

    @pytest.mark.quick
    def test_spellcaster_scenario_smoke(self):
        """Smoke test for spellcaster scenario."""
        scenario = ScenarioFactory.create_spellcaster_scenario()
        
        assert scenario is not None
        assert scenario["name"] == "Spellcaster Functionality"
        assert scenario["expected_outcomes"]["has_spells"] is True
        assert "spell_slots" in scenario["expected_outcomes"]
        assert scenario["expected_outcomes"]["spell_slots"]["1"] == 4

    @pytest.mark.quick
    def test_multiclass_scenario_smoke(self):
        """Smoke test for multiclass scenario."""
        scenario = ScenarioFactory.create_multiclass_scenario()
        
        assert scenario is not None
        assert scenario["name"] == "Multiclass Character"
        assert scenario["expected_outcomes"]["total_level"] == 5
        assert scenario["expected_outcomes"]["has_spells"] is True

    @pytest.mark.quick
    def test_error_handling_scenario_smoke(self):
        """Smoke test for error handling scenario."""
        scenario = ScenarioFactory.create_error_handling_scenario()
        
        assert scenario is not None
        assert scenario["name"] == "Error Handling"
        assert scenario["expected_outcomes"]["should_fail"] is True
        assert scenario["expected_outcomes"]["error_type"] == "CHARACTER_NOT_FOUND"

class TestCalculatorSmoke:
    """Smoke tests for calculator functionality."""
    
    @pytest.mark.quick
    def test_ac_calculation_smoke(self):
        """Smoke test for AC calculation."""
        # Import here to avoid import errors if module doesn't exist
        try:
            from calculators.armor_class import ArmorClassCalculator
            
            calculator = ArmorClassCalculator()
            assert calculator is not None
            assert hasattr(calculator, 'calculate')
            assert callable(calculator.calculate)
        except ImportError:
            # If calculator doesn't exist, skip this test
            pytest.skip("ArmorClassCalculator not available")

    @pytest.mark.quick
    def test_hp_calculation_smoke(self):
        """Smoke test for HP calculation."""
        try:
            from calculators.hit_points import HitPointsCalculator
            
            calculator = HitPointsCalculator()
            assert calculator is not None
            assert hasattr(calculator, 'calculate')
            assert callable(calculator.calculate)
        except ImportError:
            pytest.skip("HitPointsCalculator not available")

    @pytest.mark.quick
    def test_spell_calculation_smoke(self):
        """Smoke test for spell calculation."""
        try:
            from calculators.spellcasting import SpellcastingCalculator
            
            calculator = SpellcastingCalculator()
            assert calculator is not None
            assert hasattr(calculator, 'calculate')
            assert callable(calculator.calculate)
        except ImportError:
            pytest.skip("SpellcastingCalculator not available")

    @pytest.mark.quick
    def test_ability_score_calculation_smoke(self):
        """Smoke test for ability score calculation."""
        try:
            from calculators.ability_scores import AbilityScoresCalculator
            
            calculator = AbilityScoresCalculator()
            assert calculator is not None
            assert hasattr(calculator, 'calculate')
            assert callable(calculator.calculate)
        except ImportError:
            pytest.skip("AbilityScoresCalculator not available")

class TestClientSmoke:
    """Smoke tests for client functionality."""
    
    @pytest.mark.quick
    def test_mock_client_smoke(self):
        """Smoke test for mock client."""
        try:
            from clients.mock_client import MockClient
            
            client = MockClient()
            assert client is not None
            assert hasattr(client, 'get_character')
            assert callable(client.get_character)
            
            # Test basic functionality
            result = client.get_character("fighter")
            assert result is not None
            assert "success" in result
        except ImportError:
            pytest.skip("MockClient not available")

    @pytest.mark.quick
    def test_dnd_beyond_client_smoke(self):
        """Smoke test for D&D Beyond client."""
        try:
            from clients.dnd_beyond_client import DNDBeyondClient
            
            client = DNDBeyondClient()
            assert client is not None
            assert hasattr(client, 'get_character')
            assert callable(client.get_character)
        except ImportError:
            pytest.skip("DNDBeyondClient not available")

class TestFormatterSmoke:
    """Smoke tests for formatter functionality."""
    
    @pytest.mark.quick
    def test_json_formatter_smoke(self):
        """Smoke test for JSON formatter."""
        try:
            from formatters.json_formatter import JSONFormatter
            
            formatter = JSONFormatter()
            assert formatter is not None
            assert hasattr(formatter, 'format')
            assert callable(formatter.format)
            
            # Test basic formatting
            test_data = {"name": "Test", "level": 1}
            result = formatter.format(test_data)
            assert result is not None
            assert isinstance(result, str)
            assert "Test" in result
        except ImportError:
            pytest.skip("JSONFormatter not available")

    @pytest.mark.quick
    def test_yaml_formatter_smoke(self):
        """Smoke test for YAML formatter."""
        try:
            from formatters.yaml_formatter import YAMLFormatter
            
            # YAMLFormatter requires character_data parameter
            test_data = {"name": "Test", "level": 1}
            formatter = YAMLFormatter(test_data)
            assert formatter is not None
            assert hasattr(formatter, 'format')
            assert callable(formatter.format)
            
            # Test basic formatting - format() method doesn't take additional parameters
            result = formatter.format()
            assert result is not None
            assert isinstance(result, str)
            assert "Test" in result
        except ImportError:
            pytest.skip("YAMLFormatter not available")

class TestValidatorSmoke:
    """Smoke tests for validator functionality."""
    
    @pytest.mark.quick
    def test_character_validator_smoke(self):
        """Smoke test for character validator."""
        try:
            from validators.character_validator import CharacterValidator
            
            validator = CharacterValidator()
            assert validator is not None
            assert hasattr(validator, 'validate')
            assert callable(validator.validate)
            
            # Test basic validation
            character_data = CharacterArchetypeFactory.create_fighter(level=1)
            result = validator.validate(character_data)
            assert result is not None
            assert hasattr(result, 'is_valid')
        except ImportError:
            pytest.skip("CharacterValidator not available")

    @pytest.mark.quick
    def test_ability_score_validator_smoke(self):
        """Smoke test for ability score validator."""
        try:
            from validators.ability_score_validator import AbilityScoreValidator
            
            validator = AbilityScoreValidator()
            assert validator is not None
            assert hasattr(validator, 'validate')
            assert callable(validator.validate)
            
            # Test basic validation
            ability_scores = {
                "strength": 16, "dexterity": 14, "constitution": 15,
                "intelligence": 10, "wisdom": 12, "charisma": 8
            }
            result = validator.validate(ability_scores)
            assert result is not None
            assert hasattr(result, 'is_valid')
        except ImportError:
            pytest.skip("AbilityScoreValidator not available")

class TestPerformanceSmoke:
    """Smoke tests for performance requirements."""
    
    @pytest.mark.quick
    def test_factory_performance_smoke(self):
        """Smoke test for factory performance."""
        import time
        
        start_time = time.time()
        
        # Create multiple characters quickly
        for i in range(10):
            CharacterArchetypeFactory.create_fighter(level=i+1)
            CharacterArchetypeFactory.create_wizard(level=i+1)
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly
        assert execution_time < 1.0  # Under 1 second for 20 characters

    @pytest.mark.quick  
    def test_response_factory_performance_smoke(self):
        """Smoke test for response factory performance."""
        import time
        
        start_time = time.time()
        
        # Create multiple responses quickly
        for i in range(10):
            character_data = CharacterArchetypeFactory.create_fighter(level=i+1)
            APIResponseFactory.create_successful_character_response(character_data)
            APIResponseFactory.create_character_not_found_response(str(i))
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly
        assert execution_time < 1.0  # Under 1 second for 20 responses

    @pytest.mark.quick
    def test_scenario_factory_performance_smoke(self):
        """Smoke test for scenario factory performance."""
        import time
        
        start_time = time.time()
        
        # Create multiple scenarios quickly
        ScenarioFactory.create_new_character_scenario()
        ScenarioFactory.create_spellcaster_scenario()
        ScenarioFactory.create_multiclass_scenario()
        ScenarioFactory.create_error_handling_scenario()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should complete quickly
        assert execution_time < 1.0  # Under 1 second for 4 scenarios

class TestIntegrationSmoke:
    """Smoke tests for basic integration."""
    
    @pytest.mark.quick
    def test_end_to_end_scenario_smoke(self):
        """Smoke test for end-to-end scenario."""
        # Create a complete scenario
        scenario = ScenarioFactory.create_new_character_scenario()
        
        # Verify all components are present
        assert scenario["character_data"] is not None
        assert scenario["api_response"] is not None
        assert scenario["expected_outcomes"] is not None
        
        # Verify data consistency
        character_data = scenario["character_data"]
        api_response = scenario["api_response"]
        
        assert api_response["success"] is True
        assert api_response["data"]["name"] == character_data["name"]
        assert api_response["data"]["level"] == character_data["level"]

    @pytest.mark.quick
    def test_factory_integration_smoke(self):
        """Smoke test for factory integration."""
        # Test that different factories work together
        character_data = CharacterArchetypeFactory.create_wizard(level=5)
        api_response = APIResponseFactory.create_successful_character_response(character_data)
        
        # Verify integration
        assert api_response["success"] is True
        assert api_response["data"]["name"] == character_data["name"]
        assert api_response["data"]["level"] == character_data["level"]
        assert api_response["data"]["is_spellcaster"] is True

    @pytest.mark.quick
    def test_quick_test_runner_smoke(self):
        """Smoke test for quick test runner itself."""
        from ..runner import QuickTestRunner
        
        runner = QuickTestRunner()
        assert runner is not None
        assert hasattr(runner, 'run_category')
        assert hasattr(runner, 'validate_setup')
        
        # Test validation
        is_valid = runner.validate_setup()
        assert isinstance(is_valid, bool)  # Should return a boolean