"""
Mock D&D Beyond client for testing.
"""

import json
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path
import logging

from scraper.core.interfaces.character_client import CharacterClientInterface
from .exceptions import CharacterNotFoundError, ValidationError

logger = logging.getLogger(__name__)


class MockDNDBeyondClient(CharacterClientInterface):
    """
    Mock client that serves character data from local files.
    
    Useful for testing and development without hitting the real API.
    """
    
    def __init__(self, mock_data_dir: str = "tests/fixtures", enable_delays: bool = True):
        self.mock_data_dir = Path(mock_data_dir)
        self.enable_delays = enable_delays
        
        # Load available mock characters
        self.available_characters = self._discover_mock_characters()
        
        logger.info(f"Mock client initialized with {len(self.available_characters)} characters")
        if self.available_characters:
            logger.debug(f"Available characters: {list(self.available_characters.keys())}")
    
    def _discover_mock_characters(self) -> Dict[int, Path]:
        """Discover available mock character files."""
        characters = {}
        
        # Check for JSON files in mock data directory
        if self.mock_data_dir.exists():
            for json_file in self.mock_data_dir.glob("*.json"):
                try:
                    # Try to extract character ID from filename
                    if json_file.stem.isdigit():
                        char_id = int(json_file.stem)
                        characters[char_id] = json_file
                    elif "_" in json_file.stem:
                        # Handle files like "144986992_character.json"
                        char_id_str = json_file.stem.split("_")[0]
                        if char_id_str.isdigit():
                            char_id = int(char_id_str)
                            characters[char_id] = json_file
                except ValueError:
                    continue
        
        # Also check Raw/ directory for existing character files
        raw_dir = Path("Raw")
        if raw_dir.exists():
            for json_file in raw_dir.glob("*.json"):
                try:
                    if json_file.stem.isdigit():
                        char_id = int(json_file.stem)
                        characters[char_id] = json_file
                except ValueError:
                    continue
        
        return characters
    
    async def fetch_character_data(self, character_id: int, session_cookie: Optional[str] = None) -> Dict[str, Any]:
        """
        Fetch character data from mock files.
        
        Args:
            character_id: The character ID to fetch
            session_cookie: Ignored in mock client
            
        Returns:
            Character data from mock file
            
        Raises:
            CharacterNotFoundError: No mock data available
            ValidationError: Mock data is invalid
        """
        logger.info(f"Mock client fetching character {character_id}")
        
        # Simulate network delay
        if self.enable_delays:
            await asyncio.sleep(0.1)
        
        if character_id not in self.available_characters:
            raise CharacterNotFoundError(character_id, f"No mock data available for character {character_id}")
        
        mock_file = self.available_characters[character_id]
        
        try:
            with open(mock_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate the mock data
            if not self.validate_character_data(data):
                raise ValidationError(f"Mock data for character {character_id} failed validation")
            
            logger.info(f"Successfully loaded mock data for character {character_id}")
            return data
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in mock file {mock_file}: {str(e)}")
        except Exception as e:
            raise ValidationError(f"Error loading mock data: {str(e)}")
    
    def validate_character_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate mock character data.
        
        Args:
            data: Character data dictionary
            
        Returns:
            True if data is valid
        """
        if not isinstance(data, dict):
            logger.error("Mock character data is not a dictionary")
            return False
        
        # Basic validation - same as real client
        required_fields = ['id', 'name', 'levels', 'classes']
        
        for field in required_fields:
            if field not in data:
                logger.error(f"Mock data missing required field: {field}")
                return False
        
        return True
    
    def get_character_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract character summary from mock data.
        
        Args:
            data: Character data dictionary
            
        Returns:
            Character summary
        """
        try:
            # Calculate total level
            total_level = sum(level.get('level', 0) for level in data.get('levels', []))
            
            # Get classes
            classes = data.get('classes', [])
            primary_class = None
            if classes:
                primary_class = max(classes, key=lambda c: c.get('level', 0))
            
            # Get species/race
            race = data.get('race', {})
            race_name = race.get('fullName') or race.get('baseName', 'Unknown')
            
            summary = {
                'id': data.get('id'),
                'name': data.get('name', 'Unknown'),
                'level': total_level,
                'race': race_name,
                'classes': [
                    {
                        'name': cls.get('definition', {}).get('name', 'Unknown'),
                        'level': cls.get('level', 0),
                        'subclass': cls.get('subclassDefinition', {}).get('name')
                    }
                    for cls in classes
                ],
                'primary_class': primary_class.get('definition', {}).get('name') if primary_class else None,
                'is_multiclass': len(classes) > 1,
                'mock_source': str(self.available_characters.get(data.get('id')))
            }
            
            logger.debug(f"Generated mock summary for: {summary['name']}")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating mock character summary: {str(e)}")
            return {
                'id': data.get('id'),
                'name': data.get('name', 'Unknown'),
                'error': f"Failed to generate summary: {str(e)}",
                'mock_source': 'error'
            }
    
    def add_mock_character(self, character_id: int, data: Dict[str, Any]):
        """
        Add a mock character to the available characters.
        
        Args:
            character_id: Character ID
            data: Character data dictionary
        """
        # Store in memory for this session
        mock_file = self.mock_data_dir / f"{character_id}.json"
        self.available_characters[character_id] = mock_file
        
        # Optionally save to file
        try:
            self.mock_data_dir.mkdir(parents=True, exist_ok=True)
            with open(mock_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Saved mock character {character_id} to {mock_file}")
        except Exception as e:
            logger.warning(f"Could not save mock character to file: {str(e)}")
    
    def list_available_characters(self) -> Dict[int, str]:
        """
        List available mock characters.
        
        Returns:
            Dictionary mapping character ID to file path
        """
        return {char_id: str(path) for char_id, path in self.available_characters.items()}


class StaticMockClient(MockDNDBeyondClient):
    """
    Mock client with predefined static data.
    
    Useful for unit tests that need consistent, predictable data.
    """
    
    def __init__(self):
        super().__init__(enable_delays=False)
        
        # Add some static test characters
        self._add_static_characters()
    
    def _add_static_characters(self):
        """Add predefined static characters for testing."""
        
        # Simple test character
        test_char_1 = {
            "id": 999999,
            "name": "Test Character",
            "levels": [{"level": 5}],
            "classes": [{
                "definition": {"name": "Fighter"},
                "level": 5,
                "hitDiceUsed": 0
            }],
            "race": {"fullName": "Human"},
            "stats": [
                {"id": 1, "value": 16},  # Strength
                {"id": 2, "value": 14},  # Dexterity
                {"id": 3, "value": 15},  # Constitution
                {"id": 4, "value": 12},  # Intelligence
                {"id": 5, "value": 13},  # Wisdom
                {"id": 6, "value": 10}   # Charisma
            ],
            "hitPointInfo": {"maximum": 42, "current": 42},
            "armorClass": 18
        }
        
        # Multiclass spellcaster
        test_char_2 = {
            "id": 999998,
            "name": "Multiclass Caster",
            "levels": [{"level": 8}],
            "classes": [
                {
                    "definition": {"name": "Paladin"},
                    "level": 5,
                    "hitDiceUsed": 0
                },
                {
                    "definition": {"name": "Sorcerer"},
                    "level": 3,
                    "hitDiceUsed": 0
                }
            ],
            "race": {"fullName": "Dragonborn"},
            "stats": [
                {"id": 1, "value": 16},  # Strength
                {"id": 2, "value": 12},  # Dexterity
                {"id": 3, "value": 14},  # Constitution
                {"id": 4, "value": 10},  # Intelligence
                {"id": 5, "value": 13},  # Wisdom
                {"id": 6, "value": 16}   # Charisma
            ],
            "hitPointInfo": {"maximum": 62, "current": 62},
            "armorClass": 16,
            "spellSlots": [
                {"level": 1, "used": 0, "available": 4},
                {"level": 2, "used": 0, "available": 2}
            ]
        }
        
        # Store static characters
        self.available_characters[999999] = Path("static_test_1.json")
        self.available_characters[999998] = Path("static_test_2.json")
        
        # Keep data in memory
        self._static_data = {
            999999: test_char_1,
            999998: test_char_2
        }
    
    async def fetch_character_data(self, character_id: int, session_cookie: Optional[str] = None) -> Dict[str, Any]:
        """Fetch static character data."""
        if character_id in self._static_data:
            data = self._static_data[character_id].copy()
            logger.info(f"Loaded static character {character_id}: {data['name']}")
            return data
        else:
            # Fall back to file-based mock data
            return await super().fetch_character_data(character_id, session_cookie)