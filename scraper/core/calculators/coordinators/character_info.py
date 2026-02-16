"""
Character Info Coordinator

Coordinates the extraction and calculation of basic character information
including name, level, classes, species, background, alignment, and XP.
"""

from typing import Dict, Any, List, Optional, Union
import logging
from dataclasses import dataclass

from ..interfaces.coordination import ICoordinator
from ..utils.performance import monitor_performance
from ..utils.validation import validate_character_data
from ..services.interfaces import CalculationContext, CalculationResult, CalculationStatus
from shared.models.character import CharacterClass, Species, Background

logger = logging.getLogger(__name__)


@dataclass
class CharacterInfoData:
    """Data class for character information results."""
    character_id: int
    name: str
    level: int
    rule_version: str
    classes: List[CharacterClass]
    species: Optional[Species]
    background: Optional[Background]
    alignment: Optional[str]
    experience_points: int
    proficiency_bonus: int
    metadata: Dict[str, Any]


class CharacterInfoCoordinator(ICoordinator):
    """
    Coordinates the extraction and calculation of basic character information.
    
    This coordinator handles:
    - Character name and ID
    - Character level calculation from classes
    - Rule version detection
    - Class information extraction
    - Species/race information
    - Background information
    - Alignment
    - Experience points
    - Proficiency bonus calculation
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the character info coordinator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration (rule version detection now handled by centralized RuleVersionManager)
        
        # Ability ID mappings for D&D Beyond
        self.ability_id_map = {
            1: "strength",
            2: "dexterity", 
            3: "constitution",
            4: "intelligence",
            5: "wisdom",
            6: "charisma"
        }
    
    @property
    def coordinator_name(self) -> str:
        """Get the coordinator name."""
        return "character_info"
    
    @property
    def dependencies(self) -> List[str]:
        """Get the list of dependencies."""
        return []  # No dependencies - this is a foundational coordinator
    
    @property
    def priority(self) -> int:
        """Get the execution priority (lower = higher priority)."""
        return 10  # High priority - needed by many other coordinators
    
    @monitor_performance("character_info_coordinate")
    def coordinate(self, raw_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Coordinate the extraction of character information.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            context: Calculation context
            
        Returns:
            CalculationResult with character information
        """
        self.logger.info(f"Coordinating character info extraction for character {raw_data.get('id', 'unknown')}")
        
        try:
            # Basic input validation - check we can process this data
            if not self.can_coordinate(raw_data):
                return CalculationResult(
                    service_name=self.coordinator_name,
                    status=CalculationStatus.FAILED,
                    data={},
                    errors=["Cannot process character info data - missing required fields"]
                )
            
            # Extract basic information
            character_id = raw_data.get('id', 0)
            name = self._extract_name(raw_data)
            level = self._calculate_total_level(raw_data)
            # Use rule version from context (determined by centralized RuleVersionManager)
            if not context:
                raise ValueError("CalculationContext is required for rule version detection")
            rule_version = context.rule_version
            
            # Extract complex information
            classes = self._extract_classes(raw_data)
            species = self._extract_species(raw_data)
            background = self._extract_background(raw_data)
            alignment = self._extract_alignment(raw_data)
            experience_points = self._extract_experience_points(raw_data)
            proficiency_bonus = self._calculate_proficiency_bonus(level)
            avatar_url = self._extract_avatar_url(raw_data)
            senses = self._extract_senses(raw_data)

            # Create result data
            result_data = {
                'character_id': character_id,
                'name': name,
                'level': level,
                'rule_version': rule_version,
                'classes': [cls.model_dump() if hasattr(cls, 'model_dump') else cls for cls in classes],
                'species': species.model_dump() if species and hasattr(species, 'model_dump') else species,
                'background': background.model_dump() if background and hasattr(background, 'model_dump') else background,
                'alignment': alignment,
                'experience_points': experience_points,
                'proficiency_bonus': proficiency_bonus,
                'avatarUrl': avatar_url,
                'senses': senses,
                'metadata': {
                    'total_class_levels': level,
                    'multiclass': len(classes) > 1,
                    'rule_version_detected': rule_version,
                    'character_id': character_id
                }
            }
            
            self.logger.info(f"Successfully extracted character info for {name} (Level {level})")
            
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.COMPLETED,
                data=result_data,
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error coordinating character info: {str(e)}")
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.FAILED,
                data={},
                errors=[f"Character info coordination failed: {str(e)}"]
            )
    
    def _extract_name(self, raw_data: Dict[str, Any]) -> str:
        """Extract character name from raw data."""
        name = raw_data.get('name', 'Unknown Character')
        
        # Clean up name if needed
        if not name or name.strip() == "":
            name = "Unknown Character"
        
        return name.strip()
    
    def _calculate_total_level(self, raw_data: Dict[str, Any]) -> int:
        """Calculate total character level from all classes."""
        classes = raw_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes)
        
        # If no classes or all classes have level 0, return 0 (test expects this)
        # This allows handling of empty/malformed characters
        if not classes or total_level == 0:
            return 0
        
        # Otherwise ensure level is at least 1
        return max(1, total_level)
    
    
    def _extract_classes(self, raw_data: Dict[str, Any]) -> List[CharacterClass]:
        """Extract character classes from raw data."""
        classes = []
        raw_classes = raw_data.get('classes', [])
        
        for cls_data in raw_classes:
            try:
                # Extract class information
                class_id = cls_data.get('id', 0)
                level = cls_data.get('level', 1)
                
                # Get class definition
                class_def = cls_data.get('definition', {})
                name = class_def.get('name', 'Unknown Class')
                hit_die = self._get_class_hit_die(name)
                
                # Get subclass information
                subclass_info = cls_data.get('subclass')
                subclass_name = None
                if subclass_info:
                    subclass_def = subclass_info.get('definition', {})
                    subclass_name = subclass_def.get('name')
                
                # Create CharacterClass object
                character_class = CharacterClass(
                    id=class_id,
                    name=name,
                    level=level,
                    hit_die=hit_die,
                    subclass=subclass_name
                )
                
                classes.append(character_class)
                
            except Exception as e:
                self.logger.warning(f"Error extracting class data: {str(e)}")
                continue
        
        return classes
    
    def _extract_species(self, raw_data: Dict[str, Any]) -> Optional[Species]:
        """Extract species/race information from raw data."""
        race_data = raw_data.get('race')
        if not race_data:
            return None
        
        try:
            # Get race definition - handle both formats
            race_def = race_data.get('definition', {})
            race_name = race_def.get('name') or race_data.get('fullName') or race_data.get('baseName') or 'Unknown Race'
            
            # Get subrace information
            subrace_data = raw_data.get('subrace')
            subrace_name = None
            if subrace_data:
                subrace_def = subrace_data.get('definition', {})
                subrace_name = subrace_def.get('name')
            
            # Create Species object
            species = Species(
                id=race_data.get('id', 0),
                name=race_name,
                subrace=subrace_name
            )
            
            return species
            
        except Exception as e:
            self.logger.warning(f"Error extracting species data: {str(e)}")
            return None

    def _extract_senses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Extract senses (darkvision, blindsight, etc.) from modifier data.

        Returns a dict like {'darkvision': 60, 'blindsight': 10}.
        When multiple sources grant the same sense, the highest value wins.
        """
        senses = {}
        modifiers = raw_data.get('modifiers', {})

        for modifier_list in modifiers.values():
            if not isinstance(modifier_list, list):
                continue
            for modifier in modifier_list:
                friendly_type = (modifier.get('friendlyTypeName') or '').lower()
                if friendly_type != 'sense':
                    continue
                sense_name = modifier.get('friendlySubtypeName', '')
                value = modifier.get('value')
                if sense_name and value and isinstance(value, (int, float)):
                    key = sense_name.lower().replace(' ', '_')
                    senses[key] = max(senses.get(key, 0), int(value))
                    self.logger.debug(f"Sense: {sense_name} {value}ft")

        return senses

    def _extract_background(self, raw_data: Dict[str, Any]) -> Optional[Background]:
        """Extract background information from raw data."""
        background_data = raw_data.get('background')
        if not background_data:
            return None

        try:
            # Check if this is a custom background
            has_custom = background_data.get('hasCustomBackground', False)
            background_def = background_data.get('definition')

            if background_def:
                # Standard background
                background_name = background_def.get('name', 'Unknown Background')
                description = background_def.get('description', '')
            else:
                # Custom background
                custom_bg = background_data.get('customBackground', {})
                background_name = custom_bg.get('name', 'Unknown Background')
                if has_custom and background_name != 'Unknown Background':
                    background_name = f"{background_name} (Custom)"
                description = custom_bg.get('description', '')

            # Create Background object
            background = Background(
                id=background_data.get('id', 0),
                name=background_name,
                description=description
            )

            return background

        except Exception as e:
            self.logger.warning(f"Error extracting background data: {str(e)}")
            return None
    
    def _extract_alignment(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract alignment from raw data."""
        alignment_id = raw_data.get('alignmentId')
        if not alignment_id:
            return None
        
        # D&D Beyond alignment ID mappings
        alignment_map = {
            1: "Lawful Good",
            2: "Neutral Good", 
            3: "Chaotic Good",
            4: "Lawful Neutral",
            5: "True Neutral",
            6: "Chaotic Neutral",
            7: "Lawful Evil",
            8: "Neutral Evil",
            9: "Chaotic Evil"
        }
        
        return alignment_map.get(alignment_id, "Unknown")
    
    def _extract_experience_points(self, raw_data: Dict[str, Any]) -> int:
        """Extract experience points from raw data."""
        return raw_data.get('currentXp', 0)
    
    def _extract_avatar_url(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract avatar URL from decorations (matching v5.2.0 logic)."""
        decorations = raw_data.get('decorations', {})
        if decorations and decorations.get('avatarUrl'):
            return decorations['avatarUrl']
        return None
    
    def _calculate_proficiency_bonus(self, level: int) -> int:
        """Calculate proficiency bonus based on character level."""
        if level <= 0:
            return 2  # Minimum proficiency bonus
        elif level <= 4:
            return 2
        elif level <= 8:
            return 3
        elif level <= 12:
            return 4
        elif level <= 16:
            return 5
        else:
            return 6
    
    def _get_class_hit_die(self, class_name: str) -> int:
        """Get the correct hit die for a class from configuration."""
        if not self.config_manager:
            raise ValueError(f"No config manager available to get hit die for class '{class_name}'")
        
        try:
            # Get hit dice mapping from config (same pattern as hit_points.py)
            constants_config = self.config_manager.get_constants_config()
            if not constants_config or not hasattr(constants_config, 'classes'):
                raise ValueError(f"Constants config missing or has no classes section for hit die lookup")
            
            class_hit_dice = constants_config.classes.hit_dice
            hit_die = class_hit_dice.get(class_name.lower())
            if hit_die is None:
                raise ValueError(f"No hit die configured for class '{class_name}' - check constants.yaml")
            
            return hit_die
            
        except Exception as e:
            self.logger.error(f"Failed to get hit die for class '{class_name}': {e}")
            raise
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate that the input data is suitable for this coordinator.
        
        Args:
            raw_data: Raw character data to validate
            
        Returns:
            True if data is valid for this coordinator
        """
        if not isinstance(raw_data, dict):
            return False
        
        # For basic character info, we only really need id and name
        # We can handle missing classes gracefully
        required_fields = ['id', 'name']
        for field in required_fields:
            if field not in raw_data:
                return False
        
        # Classes is optional - if missing, we'll assume empty array
        # This allows handling of malformed/empty characters
        if 'classes' in raw_data and not isinstance(raw_data['classes'], list):
            return False
        
        return True
    
    def can_coordinate(self, raw_data: Dict[str, Any]) -> bool:
        """
        Check if this coordinator can handle the given data.
        
        Args:
            raw_data: Raw character data
            
        Returns:
            True if coordinator can handle this data
        """
        return self.validate_input(raw_data)
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the schema for data this coordinator produces.
        
        Returns:
            Schema describing the output data structure
        """
        return {
            "type": "object",
            "properties": {
                "character_id": {"type": "integer"},
                "name": {"type": "string"},
                "level": {"type": "integer", "minimum": 1, "maximum": 20},
                "rule_version": {"type": "string", "enum": ["2014", "2024"]},
                "classes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "name": {"type": "string"},
                            "level": {"type": "integer"},
                            "hit_die": {"type": "integer"},
                            "subclass": {"type": ["string", "null"]}
                        }
                    }
                },
                "species": {
                    "type": ["object", "null"],
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"},
                        "subrace": {"type": ["string", "null"]}
                    }
                },
                "background": {
                    "type": ["object", "null"],
                    "properties": {
                        "id": {"type": "integer"},
                        "name": {"type": "string"}
                    }
                },
                "alignment": {"type": ["string", "null"]},
                "experience_points": {"type": "integer"},
                "proficiency_bonus": {"type": "integer"},
                "metadata": {"type": "object"}
            },
            "required": [
                "character_id", "name", "level", "rule_version", 
                "classes", "experience_points", "proficiency_bonus"
            ]
        }