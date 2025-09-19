"""
Character Client Interface

Defines the contract for fetching character data from D&D Beyond API.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class CharacterClientInterface(ABC):
    """Abstract interface for character data clients."""
    
    @abstractmethod
    async def fetch_character_data(self, character_id: int, session_cookie: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch raw character data from D&D Beyond API.
        
        Args:
            character_id: The D&D Beyond character ID
            session_cookie: Optional session cookie for private characters
            
        Returns:
            Raw character data dictionary from API
            
        Raises:
            ClientError: When character cannot be fetched
            ValidationError: When character data is invalid
        """
        pass
    
    @abstractmethod
    def validate_character_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate that character data contains required fields.
        
        Args:
            data: Raw character data dictionary
            
        Returns:
            True if data is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_character_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract basic character summary from raw data.
        
        Args:
            data: Raw character data dictionary
            
        Returns:
            Dictionary with basic character info (name, level, class, etc.)
        """
        pass