"""
Character Builder Service

Service for constructing complete Character model instances from calculation results.
This service takes aggregated calculation data and builds properly validated
Character objects with all computed fields and relationships.
"""

from typing import Dict, Any, List, Optional, Union
import logging
from datetime import datetime
from dataclasses import dataclass, field

from shared.models.character import (
    Character, CharacterClass, Species, Background, AbilityScores, 
    HitPoints, ArmorClass, Spellcasting, ClassFeature, InventoryItem
)


@dataclass
class Speed:
    """Simple speed class for internal use."""
    walk: int = 30
    swim: int = 0
    fly: int = 0
    climb: int = 0
from ..utils.validation import validate_character_data, ValidationResult
from ..utils.performance import monitor_performance

logger = logging.getLogger(__name__)


@dataclass
class BuildContext:
    """Context for character building operations."""
    character_id: str
    rule_version: str
    build_timestamp: datetime = field(default_factory=datetime.now)
    validation_enabled: bool = True
    strict_mode: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)


class CharacterBuilder:
    """
    Service for building complete Character objects from calculation results.
    
    This service handles:
    - Model construction from calculation data
    - Data validation and consistency checking
    - Relationship building between model components
    - Default value assignment and fallback handling
    - Performance monitoring and error reporting
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the character builder.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Build statistics
        self.build_stats = {
            'total_builds': 0,
            'successful_builds': 0,
            'failed_builds': 0,
            'validation_failures': 0,
            'build_times': []
        }
        
        # Default values for missing data
        self.default_values = {
            'hit_points': {'current': 1, 'maximum': 1, 'temporary': 0},
            'armor_class': {'base': 10, 'total': 10},
            'speed': {'walk': 30, 'swim': 0, 'fly': 0, 'climb': 0},
            'ability_scores': {
                'strength': 10, 'dexterity': 10, 'constitution': 10,
                'intelligence': 10, 'wisdom': 10, 'charisma': 10
            }
        }
    
    @monitor_performance("character_builder_build")
    def build_character(self, calculation_data: Dict[str, Any], context: BuildContext) -> Character:
        """
        Build a complete Character object from calculation data.
        
        Args:
            calculation_data: Aggregated calculation results
            context: Build context
            
        Returns:
            Complete Character object
            
        Raises:
            ValueError: If required data is missing or invalid
        """
        self.build_stats['total_builds'] += 1
        build_start_time = datetime.now()
        
        try:
            self.logger.info(f"Building character {context.character_id} with rule version {context.rule_version}")
            
            # Validate input data if enabled
            if context.validation_enabled:
                validation_result = self._validate_calculation_data(calculation_data)
                if not validation_result.is_valid:
                    self.build_stats['validation_failures'] += 1
                    if context.strict_mode:
                        raise ValueError(f"Validation failed: {validation_result.get_errors()}")
                    else:
                        self.logger.warning(f"Validation warnings: {validation_result.get_warnings()}")
            
            # Build character components
            character_info = self._build_character_info(calculation_data, context)
            ability_scores = self._build_ability_scores(calculation_data, context)
            combat_info = self._build_combat_info(calculation_data, context)
            spellcasting_info = self._build_spellcasting_info(calculation_data, context)
            features = self._build_features(calculation_data, context)
            equipment = self._build_equipment(calculation_data, context)
            
            # Create complete character
            character = Character(
                id=character_info['character_id'],
                name=character_info['name'],
                level=character_info['level'],
                classes=character_info['classes'],
                species=character_info['species'],
                background=character_info['background'],
                alignment=character_info['alignment'],
                experience_points=character_info['experience_points'],
                ability_scores=ability_scores,
                hit_points=combat_info['hit_points'],
                armor_class=combat_info['armor_class'],
                speed=combat_info['speed'].walk,  # Use walk speed as main speed
                initiative_bonus=combat_info['initiative_bonus'],
                proficiency_bonus=character_info['proficiency_bonus'],
                spellcasting=Spellcasting(
                    is_spellcaster=spellcasting_info.get('is_spellcaster', False),
                    spellcasting_ability=spellcasting_info.get('spellcasting_ability', 'intelligence'),
                    spell_save_dc=spellcasting_info.get('spell_save_dc', 8),
                    spell_attack_bonus=spellcasting_info.get('spell_attack_bonus', 0)
                ),
                equipment=equipment,
                class_features=features
            )
            
            # Final validation
            if context.validation_enabled:
                self._validate_character_object(character)
            
            # Update statistics
            build_time = (datetime.now() - build_start_time).total_seconds()
            self.build_stats['build_times'].append(build_time)
            self.build_stats['successful_builds'] += 1
            
            self.logger.info(f"Successfully built character {character.name} (ID: {character.id})")
            return character
            
        except Exception as e:
            self.build_stats['failed_builds'] += 1
            self.logger.error(f"Failed to build character {context.character_id}: {str(e)}")
            raise ValueError(f"Character build failed: {str(e)}")
    
    def _validate_calculation_data(self, calculation_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate calculation data before building.
        
        Args:
            calculation_data: Calculation results to validate
            
        Returns:
            Validation result
        """
        # Check for required coordinators
        required_coordinators = ['character_info', 'abilities', 'combat']
        validation_result = ValidationResult(is_valid=True)
        
        for coordinator in required_coordinators:
            if coordinator not in calculation_data:
                validation_result.add_message(
                    severity="error",
                    category="structure",
                    message=f"Missing required coordinator data: {coordinator}"
                )
        
        # Validate each coordinator's data
        for coordinator_name, coordinator_data in calculation_data.items():
            if not isinstance(coordinator_data, dict):
                validation_result.add_message(
                    severity="error",
                    category="type",
                    message=f"Coordinator {coordinator_name} data must be a dictionary"
                )
        
        return validation_result
    
    def _build_character_info(self, calculation_data: Dict[str, Any], context: BuildContext) -> Dict[str, Any]:
        """
        Build basic character information.
        
        Args:
            calculation_data: Calculation results
            context: Build context
            
        Returns:
            Character info dictionary
        """
        info_data = calculation_data.get('character_info', {})
        
        # Build classes
        classes = []
        for class_data in info_data.get('classes', []):
            if isinstance(class_data, dict):
                character_class = CharacterClass(
                    id=class_data.get('id', 0),
                    name=class_data.get('name', 'Unknown'),
                    level=class_data.get('level', 1),
                    hit_die=class_data['hit_die'],  # Should be provided by character_info coordinator
                    subclass=class_data.get('subclass')
                )
                classes.append(character_class)
        
        # Build species
        species = None
        species_data = info_data.get('species')
        if species_data and isinstance(species_data, dict):
            species = Species(
                id=species_data.get('id', 0),
                name=species_data.get('name', 'Unknown'),
                subrace=species_data.get('subrace')
            )
        
        # Build background
        background = None
        background_data = info_data.get('background')
        if background_data and isinstance(background_data, dict):
            background = Background(
                id=background_data.get('id', 0),
                name=background_data.get('name', 'Unknown')
            )
        
        return {
            'character_id': info_data.get('character_id', context.character_id),
            'name': info_data.get('name', 'Unknown Character'),
            'level': info_data.get('level', 1),
            'rule_version': info_data.get('rule_version', context.rule_version),
            'classes': classes,
            'species': species,
            'background': background,
            'alignment': info_data.get('alignment'),
            'experience_points': info_data.get('experience_points', 0),
            'proficiency_bonus': info_data.get('proficiency_bonus', 2)
        }
    
    def _build_ability_scores(self, calculation_data: Dict[str, Any], context: BuildContext) -> AbilityScores:
        """
        Build ability scores from calculation data.
        
        Args:
            calculation_data: Calculation results
            context: Build context
            
        Returns:
            AbilityScores object
        """
        abilities_data = calculation_data.get('abilities', {})
        scores_data = abilities_data.get('ability_scores', {})
        
        # Extract scores with defaults
        scores = {}
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            ability_data = scores_data.get(ability, {})
            if isinstance(ability_data, dict):
                scores[ability] = ability_data.get('score', self.default_values['ability_scores'][ability])
            else:
                scores[ability] = self.default_values['ability_scores'][ability]
        
        return AbilityScores(
            strength=scores['strength'],
            dexterity=scores['dexterity'],
            constitution=scores['constitution'],
            intelligence=scores['intelligence'],
            wisdom=scores['wisdom'],
            charisma=scores['charisma']
        )
    
    def _build_combat_info(self, calculation_data: Dict[str, Any], context: BuildContext) -> Dict[str, Any]:
        """
        Build combat information.
        
        Args:
            calculation_data: Calculation results
            context: Build context
            
        Returns:
            Combat info dictionary
        """
        combat_data = calculation_data.get('combat', {})
        
        # Build hit points
        hp_data = combat_data.get('hit_points', {})
        hit_points = HitPoints(
            current=hp_data.get('current', self.default_values['hit_points']['current']),
            maximum=hp_data.get('maximum', self.default_values['hit_points']['maximum']),
            temporary=hp_data.get('temporary', self.default_values['hit_points']['temporary'])
        )
        
        # Build armor class
        ac_data = combat_data.get('armor_class', {})
        if isinstance(ac_data, (int, float)):
            # Simple AC value
            armor_class = ArmorClass(
                total=int(ac_data)
            )
        else:
            # Detailed AC breakdown
            armor_class = ArmorClass(
                total=ac_data.get('total', self.default_values['armor_class']['total'])
            )
        
        # Build speed - use Speed object for tests
        speed_data = combat_data.get('speed', {})
        if isinstance(speed_data, (int, float)):
            # Simple speed value
            speed = Speed(walk=int(speed_data))
        else:
            # Detailed speed breakdown
            speed = Speed(
                walk=speed_data.get('walk', self.default_values['speed']['walk']),
                swim=speed_data.get('swim', self.default_values['speed']['swim']),
                fly=speed_data.get('fly', self.default_values['speed']['fly']),
                climb=speed_data.get('climb', self.default_values['speed']['climb'])
            )
        
        return {
            'hit_points': hit_points,
            'armor_class': armor_class,
            'speed': speed,
            'initiative_bonus': combat_data.get('initiative_bonus', 0)
        }
    
    def _build_spellcasting_info(self, calculation_data: Dict[str, Any], context: BuildContext) -> Dict[str, Any]:
        """
        Build spellcasting information.
        
        Args:
            calculation_data: Calculation results
            context: Build context
            
        Returns:
            Spellcasting info dictionary
        """
        spellcasting_data = calculation_data.get('spellcasting', {})
        
        # Build spell slots - use dict directly
        spell_slots = []
        slots_data = spellcasting_data.get('spell_slots', [])
        for level, slots in enumerate(slots_data):
            if slots > 0:
                spell_slot = {
                    'level': level + 1,
                    'total': slots,
                    'used': 0
                }
                spell_slots.append(spell_slot)
        
        # Build spells - use dict directly  
        spells = []
        spells_data = spellcasting_data.get('spells', [])
        for spell_data in spells_data:
            if isinstance(spell_data, dict):
                spell = {
                    'id': spell_data.get('id', 0),
                    'name': spell_data.get('name', 'Unknown Spell'),
                    'level': spell_data.get('level', 0),
                    'school': spell_data.get('school', 'Universal'),
                    'casting_time': spell_data.get('casting_time', '1 action'),
                    'range': spell_data.get('range', 'Self'),
                    'components': spell_data.get('components', []),
                    'duration': spell_data.get('duration', 'Instantaneous'),
                    'description': spell_data.get('description', '')
                }
                spells.append(spell)
        
        return {
            'spells': spells,
            'spell_slots': spell_slots
        }
    
    def _build_features(self, calculation_data: Dict[str, Any], context: BuildContext) -> List[ClassFeature]:
        """
        Build character class features only.
        
        Args:
            calculation_data: Calculation results
            context: Build context
            
        Returns:
            List of ClassFeature objects
        """
        features_data = calculation_data.get('features', {})
        class_features = []
        
        # Build class features only - Character model expects List[ClassFeature]
        class_features_data = features_data.get('class_features', [])
        for feature_data in class_features_data:
            if isinstance(feature_data, dict):
                # Create ClassFeature only if we have required fields
                feature_dict = {
                    'id': feature_data.get('id', 0),
                    'name': feature_data.get('name', 'Unknown Feature'),
                    'description': feature_data.get('description', ''),
                    'level_required': feature_data.get('level_required', 1),
                    'is_subclass_feature': feature_data.get('is_subclass_feature', False)
                }
                
                # Only add optional fields if they exist
                if 'source_class' in feature_data:
                    feature_dict['source_class'] = feature_data['source_class']
                
                try:
                    feature = ClassFeature(**feature_dict)
                    class_features.append(feature)
                except Exception as e:
                    # If ClassFeature creation fails, log but continue
                    self.logger.warning(f"Failed to create ClassFeature for {feature_data.get('name', 'Unknown')}: {e}")
        
        # Note: Racial traits and feats are handled separately in the Character model
        # as they have their own fields: species.traits and other structures
        
        return class_features
    
    def _build_equipment(self, calculation_data: Dict[str, Any], context: BuildContext) -> List[Dict[str, Any]]:
        """
        Build character equipment.
        
        Args:
            calculation_data: Calculation results
            context: Build context
            
        Returns:
            List of equipment dictionaries
        """
        equipment_data = calculation_data.get('equipment', {})
        equipment = []
        
        # Build basic equipment
        basic_equipment = equipment_data.get('basic_equipment', [])
        for item_data in basic_equipment:
            if isinstance(item_data, dict):
                equipment_item = {
                    'id': item_data.get('id', 0),
                    'name': item_data.get('name', 'Unknown Item'),
                    'quantity': item_data.get('quantity', 1),
                    'weight': item_data.get('weight', 0.0),
                    'equipped': item_data.get('equipped', False),
                    'item_type': item_data.get('type', 'Unknown')
                }
                equipment.append(equipment_item)
        
        return equipment
    
    def _validate_character_object(self, character: Character):
        """
        Validate the final character object.
        
        Args:
            character: Character object to validate
            
        Raises:
            ValueError: If character is invalid
        """
        # Basic validation
        if not character.name or character.name.strip() == '':
            raise ValueError("Character name cannot be empty")
        
        if character.level < 1 or character.level > 20:
            raise ValueError(f"Character level must be between 1 and 20, got {character.level}")
        
        if not character.classes:
            raise ValueError("Character must have at least one class")
        
        # Validate ability scores
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            score = getattr(character.ability_scores, ability)
            if score < 1 or score > 30:
                raise ValueError(f"{ability.title()} score must be between 1 and 30, got {score}")
        
        # Validate hit points
        if character.hit_points.maximum < 1:
            raise ValueError("Maximum hit points must be at least 1")
        
        if character.hit_points.current < 0:
            raise ValueError("Current hit points cannot be negative")
        
        # Validate armor class
        if character.armor_class.total < 1:
            raise ValueError("Armor class must be at least 1")
        
        self.logger.debug(f"Character {character.name} passed validation")
    
    def get_build_statistics(self) -> Dict[str, Any]:
        """
        Get build statistics.
        
        Returns:
            Dictionary of build statistics
        """
        stats = {
            'total_builds': self.build_stats['total_builds'],
            'successful_builds': self.build_stats['successful_builds'],
            'failed_builds': self.build_stats['failed_builds'],
            'validation_failures': self.build_stats['validation_failures'],
            'success_rate': 0.0,
            'average_build_time': 0.0
        }
        
        if self.build_stats['total_builds'] > 0:
            stats['success_rate'] = (self.build_stats['successful_builds'] / self.build_stats['total_builds']) * 100
        
        if self.build_stats['build_times']:
            stats['average_build_time'] = sum(self.build_stats['build_times']) / len(self.build_stats['build_times'])
        
        return stats
    
    def clear_statistics(self):
        """Clear build statistics."""
        self.build_stats = {
            'total_builds': 0,
            'successful_builds': 0,
            'failed_builds': 0,
            'validation_failures': 0,
            'build_times': []
        }
        self.logger.info("Build statistics cleared")