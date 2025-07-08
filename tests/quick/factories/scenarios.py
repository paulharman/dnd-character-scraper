"""
Test scenario factories for quick tests.

Provides complete test scenarios combining character data with expected outcomes.
"""

from typing import Dict, Any, List, Tuple
from .character_archetypes import CharacterArchetypeFactory
from .api_responses import APIResponseFactory

class ScenarioFactory:
    """Factory for creating complete test scenarios."""
    
    @staticmethod
    def create_new_character_scenario() -> Dict[str, Any]:
        """Create a scenario for testing new character creation."""
        character_data = CharacterArchetypeFactory.create_fighter(level=1)
        api_response = APIResponseFactory.create_successful_character_response(character_data)
        
        return {
            "name": "New Character Creation",
            "character_data": character_data,
            "api_response": api_response,
            "expected_outcomes": {
                "ac_calculation": 16,
                "hp_calculation": 12,
                "proficiency_bonus": 2,
                "spell_slots": {},
                "has_spells": False,
                "attack_bonus": 5,  # str mod + prof bonus
                "save_bonuses": {
                    "strength": 5,
                    "constitution": 4
                }
            },
            "test_duration_limit": 2.0  # seconds
        }
    
    @staticmethod
    def create_spellcaster_scenario() -> Dict[str, Any]:
        """Create a scenario for testing spellcaster functionality."""
        character_data = CharacterArchetypeFactory.create_wizard(level=3)
        api_response = APIResponseFactory.create_successful_character_response(character_data)
        
        return {
            "name": "Spellcaster Functionality",
            "character_data": character_data,
            "api_response": api_response,
            "expected_outcomes": {
                "ac_calculation": 12,
                "hp_calculation": 14,  # 6 + 4 + 4
                "proficiency_bonus": 2,
                "spell_slots": {"1": 4, "2": 2},
                "has_spells": True,
                "spell_attack_bonus": 5,  # int mod + prof bonus
                "spell_save_dc": 13,      # 8 + int mod + prof bonus
                "cantrips_known": 4
            },
            "test_duration_limit": 3.0
        }
    
    @staticmethod
    def create_multiclass_scenario() -> Dict[str, Any]:
        """Create a scenario for testing multiclass functionality."""
        character_data = CharacterArchetypeFactory.create_multiclass_fighter_wizard(
            fighter_level=3, wizard_level=2
        )
        api_response = APIResponseFactory.create_successful_character_response(character_data)
        
        return {
            "name": "Multiclass Character",
            "character_data": character_data,
            "api_response": api_response,
            "expected_outcomes": {
                "total_level": 5,
                "ac_calculation": 16,
                "hp_calculation": 28,  # 10 + 6 + 3*5
                "proficiency_bonus": 3,
                "spell_slots": {"1": 3, "2": 0},  # Wizard level 2 spell slots
                "has_spells": True,
                "spell_attack_bonus": 5,
                "spell_save_dc": 13,
                "action_surge": True,
                "second_wind": True
            },
            "test_duration_limit": 4.0
        }
    
    @staticmethod
    def create_high_level_scenario() -> Dict[str, Any]:
        """Create a scenario for testing high-level character functionality."""
        character_data = CharacterArchetypeFactory.create_level_20_barbarian()
        api_response = APIResponseFactory.create_successful_character_response(character_data)
        
        return {
            "name": "High Level Character",
            "character_data": character_data,
            "api_response": api_response,
            "expected_outcomes": {
                "ac_calculation": 17,
                "hp_calculation": 285,
                "proficiency_bonus": 6,
                "spell_slots": {},
                "has_spells": False,
                "attack_bonus": 13,  # str mod + prof bonus
                "damage_bonus": 7,   # str mod
                "rage_damage": 4,    # level 20 barbarian rage damage
                "brutal_critical_dice": 3
            },
            "test_duration_limit": 5.0
        }
    
    @staticmethod
    def create_error_handling_scenario() -> Dict[str, Any]:
        """Create a scenario for testing error handling."""
        api_response = APIResponseFactory.create_character_not_found_response("99999")
        
        return {
            "name": "Error Handling",
            "character_data": None,
            "api_response": api_response,
            "expected_outcomes": {
                "should_fail": True,
                "error_type": "CHARACTER_NOT_FOUND",
                "graceful_degradation": True
            },
            "test_duration_limit": 1.0
        }
    
    @staticmethod
    def create_malformed_data_scenario() -> Dict[str, Any]:
        """Create a scenario for testing malformed data handling."""
        api_response = APIResponseFactory.create_malformed_character_response()
        
        return {
            "name": "Malformed Data Handling",
            "character_data": None,
            "api_response": api_response,
            "expected_outcomes": {
                "should_fail": True,
                "error_type": "VALIDATION_ERROR",
                "graceful_degradation": True,
                "error_details": ["Invalid level", "Invalid ability scores"]
            },
            "test_duration_limit": 2.0
        }
    
    @staticmethod
    def create_performance_scenario() -> Dict[str, Any]:
        """Create a scenario for testing performance."""
        character_data = CharacterArchetypeFactory.create_wizard(level=10)
        api_response = APIResponseFactory.create_successful_character_response(character_data)
        
        return {
            "name": "Performance Testing",
            "character_data": character_data,
            "api_response": api_response,
            "expected_outcomes": {
                "execution_time_limit": 1.0,  # Must complete in under 1 second
                "memory_usage_limit": 50,     # MB
                "calculation_accuracy": 0.99  # 99% accuracy required
            },
            "test_duration_limit": 1.5,
            "performance_critical": True
        }
    
    @staticmethod
    def create_integration_scenario() -> Dict[str, Any]:
        """Create a scenario for integration testing."""
        character_data = CharacterArchetypeFactory.create_rogue(level=5)
        api_response = APIResponseFactory.create_successful_character_response(character_data)
        
        return {
            "name": "Integration Testing",
            "character_data": character_data,
            "api_response": api_response,
            "expected_outcomes": {
                "pipeline_completion": True,
                "all_calculators_run": True,
                "output_format_valid": True,
                "markdown_generated": True,
                "validation_passed": True
            },
            "test_duration_limit": 4.0,
            "integration_test": True
        }
    
    @staticmethod
    def create_scenario_batch() -> List[Dict[str, Any]]:
        """Create a batch of scenarios for comprehensive testing."""
        return [
            ScenarioFactory.create_new_character_scenario(),
            ScenarioFactory.create_spellcaster_scenario(),
            ScenarioFactory.create_multiclass_scenario(),
            ScenarioFactory.create_error_handling_scenario(),
            ScenarioFactory.create_performance_scenario()
        ]
    
    @staticmethod
    def get_scenario_by_name(name: str) -> Dict[str, Any]:
        """Get scenario by name."""
        scenarios = {
            'new_character': ScenarioFactory.create_new_character_scenario,
            'spellcaster': ScenarioFactory.create_spellcaster_scenario,
            'multiclass': ScenarioFactory.create_multiclass_scenario,
            'high_level': ScenarioFactory.create_high_level_scenario,
            'error_handling': ScenarioFactory.create_error_handling_scenario,
            'malformed_data': ScenarioFactory.create_malformed_data_scenario,
            'performance': ScenarioFactory.create_performance_scenario,
            'integration': ScenarioFactory.create_integration_scenario
        }
        
        if name not in scenarios:
            raise ValueError(f"Unknown scenario: {name}. Available: {list(scenarios.keys())}")
        
        return scenarios[name]()
    
    @staticmethod
    def get_all_scenarios() -> List[str]:
        """Get list of all available scenarios."""
        return [
            'new_character', 'spellcaster', 'multiclass', 'high_level',
            'error_handling', 'malformed_data', 'performance', 'integration'
        ]