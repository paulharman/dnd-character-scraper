"""
API response factories for quick tests.

Provides mock API responses for testing without making real API calls.
"""

from typing import Dict, Any, List, Optional
import json

class APIResponseFactory:
    """Factory for creating mock API responses."""
    
    @staticmethod
    def create_successful_character_response(character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a successful character API response."""
        return {
            "success": True,
            "data": character_data,
            "message": None,
            "meta": {
                "sources": ["Player's Handbook", "Xanathar's Guide to Everything"],
                "version": "2024",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
    
    @staticmethod
    def create_character_not_found_response(character_id: str) -> Dict[str, Any]:
        """Create a character not found error response."""
        return {
            "success": False,
            "data": None,
            "message": f"Character with ID {character_id} not found",
            "error": {
                "code": "CHARACTER_NOT_FOUND",
                "details": f"No character exists with ID: {character_id}"
            }
        }
    
    @staticmethod
    def create_api_error_response(error_message: str = "Internal Server Error") -> Dict[str, Any]:
        """Create a generic API error response."""
        return {
            "success": False,
            "data": None,
            "message": error_message,
            "error": {
                "code": "API_ERROR",
                "details": error_message
            }
        }
    
    @staticmethod
    def create_rate_limit_response() -> Dict[str, Any]:
        """Create a rate limit error response."""
        return {
            "success": False,
            "data": None,
            "message": "Rate limit exceeded",
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "details": "Too many requests. Please try again later.",
                "retry_after": 60
            }
        }
    
    @staticmethod
    def create_malformed_character_response() -> Dict[str, Any]:
        """Create a response with malformed character data."""
        return {
            "success": True,
            "data": {
                "name": "Malformed Character",
                "level": "not_a_number",  # Invalid data type
                "classes": "should_be_array",  # Invalid data type
                "ability_scores": {
                    "strength": 50,  # Invalid value (too high)
                    "dexterity": -5,  # Invalid value (too low)
                    "constitution": None,  # Missing required value
                    # Missing other required abilities
                }
            },
            "message": None
        }
    
    @staticmethod
    def create_partial_character_response() -> Dict[str, Any]:
        """Create a response with partial character data."""
        return {
            "success": True,
            "data": {
                "name": "Partial Character",
                "level": 5,
                "classes": [{
                    "name": "Fighter",
                    "level": 5
                    # Missing hit_die and other required fields
                }],
                "ability_scores": {
                    "strength": 16,
                    "dexterity": 14,
                    "constitution": 15
                    # Missing intelligence, wisdom, charisma
                },
                "race": "Human"
                # Missing background, armor_class, hit_points, etc.
            },
            "message": None
        }
    
    @staticmethod
    def create_timeout_response() -> Dict[str, Any]:
        """Create a timeout error response."""
        return {
            "success": False,
            "data": None,
            "message": "Request timeout",
            "error": {
                "code": "TIMEOUT",
                "details": "Request timed out after 30 seconds"
            }
        }
    
    @staticmethod
    def create_network_error_response() -> Dict[str, Any]:
        """Create a network error response."""
        return {
            "success": False,
            "data": None,
            "message": "Network error",
            "error": {
                "code": "NETWORK_ERROR",
                "details": "Unable to connect to D&D Beyond API"
            }
        }
    
    @staticmethod
    def create_mock_response_by_type(response_type: str, **kwargs) -> Dict[str, Any]:
        """Create a mock response by type."""
        response_types = {
            'success': lambda: APIResponseFactory.create_successful_character_response(kwargs.get('character_data', {})),
            'not_found': lambda: APIResponseFactory.create_character_not_found_response(kwargs.get('character_id', '12345')),
            'error': lambda: APIResponseFactory.create_api_error_response(kwargs.get('error_message', 'API Error')),
            'rate_limit': APIResponseFactory.create_rate_limit_response,
            'malformed': APIResponseFactory.create_malformed_character_response,
            'partial': APIResponseFactory.create_partial_character_response,
            'timeout': APIResponseFactory.create_timeout_response,
            'network_error': APIResponseFactory.create_network_error_response
        }
        
        if response_type not in response_types:
            raise ValueError(f"Unknown response type: {response_type}. Available: {list(response_types.keys())}")
        
        return response_types[response_type]()
    
    @staticmethod
    def get_available_response_types() -> List[str]:
        """Get list of available response types."""
        return ['success', 'not_found', 'error', 'rate_limit', 'malformed', 'partial', 'timeout', 'network_error']