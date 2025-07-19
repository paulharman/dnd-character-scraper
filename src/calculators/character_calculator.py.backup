"""
Character Calculator

Main calculator that coordinates all individual calculation modules.
Produces complete character data with all derived values.
"""

from typing import Dict, Any, Optional, List
import logging

from src.models.character import (
    Character, AbilityScores, CharacterClass, Species, Background, HitPoints, ArmorClass, Spellcasting, Skill,
    ClassFeature, EnhancedEquipment, CharacterAppearance, ResourcePool, AdvancedCharacterDetails, WeaponProperty
)
from src.config.manager import get_config_manager
from src.rules.version_manager import RuleVersionManager, RuleVersion, DetectionResult
from src.utils.html_cleaner import clean_character_data

from .base import RuleAwareCalculator
from .ability_scores import AbilityScoreCalculator
from .hit_points import HitPointCalculator
from .armor_class import ArmorClassCalculator
from .spellcasting import SpellcastingCalculator
from .proficiencies import ProficiencyCalculator
from .wealth import WealthCalculator
from .encumbrance import EncumbranceCalculator
from .container_inventory import ContainerInventoryCalculator
from .class_features import ClassFeatureExtractor
from .equipment_details import EquipmentDetailsExtractor
from .character_appearance import CharacterAppearanceExtractor
from .resource_tracking import ResourceTrackingExtractor
from .advanced_character_details import AdvancedCharacterDetailsExtractor

logger = logging.getLogger(__name__)


class CharacterCalculator(RuleAwareCalculator):
    """
    Main character calculator that produces complete character data.
    
    Coordinates all individual calculators to produce a fully calculated
    Character model with all derived values and breakdowns.
    
    Now includes rule version detection and handling for 2014 vs 2024 D&D rules.
    """
    
    def __init__(self, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
        super().__init__(config_manager, rule_manager)
        self.config_manager = config_manager or get_config_manager()
        
        # Initialize individual calculators
        self.ability_calculator = AbilityScoreCalculator(config_manager)
        self.hp_calculator = HitPointCalculator(config_manager)
        self.ac_calculator = ArmorClassCalculator(config_manager)
        self.spell_calculator = SpellcastingCalculator(config_manager)
        self.proficiency_calculator = ProficiencyCalculator(config_manager)
        self.wealth_calculator = WealthCalculator(config_manager)
        self.encumbrance_calculator = EncumbranceCalculator(config_manager)
        self.container_calculator = ContainerInventoryCalculator(config_manager)
        
        # Initialize Priority 2 feature extractors
        self.class_feature_extractor = ClassFeatureExtractor(config_manager)
        self.equipment_details_extractor = EquipmentDetailsExtractor(config_manager)
        self.character_appearance_extractor = CharacterAppearanceExtractor(config_manager)
        self.resource_tracking_extractor = ResourceTrackingExtractor(config_manager)
        self.advanced_details_extractor = AdvancedCharacterDetailsExtractor(config_manager)
    
    def calculate(self, raw_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate complete character data as JSON (required by RuleAwareCalculator).
        
        Args:
            raw_data: Raw character data from D&D Beyond API
            **kwargs: Additional parameters
            
        Returns:
            Complete character data dictionary
        """
        return self.calculate_complete_json(raw_data)
        
    def calculate_character(self, raw_data: Dict[str, Any]) -> Character:
        """
        Calculate complete character from raw D&D Beyond data.
        
        Args:
            raw_data: Raw character data from D&D Beyond API
            
        Returns:
            Complete Character model with all calculated values
        """
        character_id = raw_data.get('id', 0)
        logger.info(f"Calculating complete character data for ID {character_id}")
        
        try:
            # Extract basic character information
            basic_info = self._extract_basic_info(raw_data)
            
            # Extract Priority 2 features
            priority2_features = self._extract_priority2_features(raw_data)
            
            # Create initial character model
            character = Character(
                id=character_id,
                name=basic_info['name'],
                level=basic_info['level'],
                rule_version=basic_info['rule_version'],
                ability_scores=basic_info['ability_scores'],
                classes=basic_info['classes'],
                species=basic_info['species'],
                background=basic_info['background'],
                hit_points=basic_info['hit_points'],
                armor_class=basic_info['armor_class'],
                spellcasting=basic_info['spellcasting'],
                proficiency_bonus=basic_info['proficiency_bonus'],
                skills=basic_info['skills'],
                saving_throw_proficiencies=basic_info['saving_throw_proficiencies'],
                initiative_bonus=basic_info['initiative_bonus'],
                speed=basic_info['speed'],
                alignment=basic_info.get('alignment'),
                experience_points=basic_info.get('experience_points', 0),
                equipment=basic_info.get('equipment', []),
                modifiers=basic_info.get('modifiers', []),
                # Priority 2 Features
                enhanced_equipment=priority2_features['enhanced_equipment'],
                class_features=priority2_features['class_features'],
                appearance=priority2_features['appearance'],
                resource_pools=priority2_features['resource_pools'],
                character_details=priority2_features['character_details'],
                raw_data_summary=self._create_raw_data_summary(raw_data)
            )
            
            logger.info(f"Successfully calculated character: {character.name} (Level {character.level})")
            return character
            
        except Exception as e:
            logger.error(f"Error calculating character {character_id}: {str(e)}")
            raise
    
    def calculate_complete_json(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate complete character data as JSON dictionary.
        
        This produces the complete JSON output that the parser will consume,
        including all calculated values and breakdowns.
        
        Args:
            raw_data: Raw character data from D&D Beyond API
            
        Returns:
            Complete character data dictionary
        """
        character_id = raw_data.get('id', 0)
        logger.info(f"Calculating complete JSON output for character {character_id}")
        
        # Calculate all individual components
        ability_results = self._safe_calculate(self.ability_calculator, raw_data, "ability scores")
        # Calculate hit points with the correct constitution modifier
        hp_results = self._safe_calculate_hp_with_constitution(raw_data, ability_results)
        ac_results = self._safe_calculate(self.ac_calculator, raw_data, "armor class")
        spell_results = self._safe_calculate_spellcasting_with_abilities(raw_data, ability_results)
        # Convert spell slots to object format
        spell_results = self._convert_spell_slots_to_object_format(spell_results)
        proficiency_results = self._safe_calculate(self.proficiency_calculator, raw_data, "proficiencies")
        
        # Calculate wealth and encumbrance
        wealth_results = self._safe_calculate_raw(self.wealth_calculator, raw_data, "wealth")
        encumbrance_results = self._safe_calculate_encumbrance(raw_data, ability_results)
        
        # Calculate container inventory organization
        container_results = self._safe_calculate_containers(raw_data)
        
        # Extract class features
        class_features_results = self._safe_calculate(self.class_feature_extractor, raw_data, "class features")
        
        # Fix save bonuses now that we have proficiency data
        self._fix_ability_save_bonuses(ability_results, proficiency_results)
        
        # Extract basic information
        basic_info = self._extract_basic_info_dict(raw_data)
        
        # Extract comprehensive character data
        spells_data = self._extract_spells_comprehensive(raw_data, ability_results)
        actions_data = self._extract_actions(raw_data)
        inventory_data = self._extract_inventory(raw_data)
        feats_data = self._extract_feats(raw_data)
        saving_throws_data = self._extract_saving_throws(raw_data, ability_results)
        skills_data = self._extract_skills_detailed(raw_data, ability_results)
        # Extract appearance data using Priority 2 extractor 
        appearance_obj = self.character_appearance_extractor.extract_character_appearance(raw_data)
        appearance_data = appearance_obj.model_dump() if appearance_obj else {}
        notes_data = self._extract_notes(raw_data)
        
        # Create structured basic_info
        basic_info_structured = self._create_basic_info_structure(
            basic_info, hp_results, ac_results, ability_results, raw_data
        )
        
        # Combine all results
        complete_data = {
            # Basic character info structure
            'basic_info': basic_info_structured,
            
            # Character appearance
            'appearance': appearance_data,
            
            # Character identity (species/race and background)
            'species': basic_info.get('species'),
            'background': basic_info.get('background'),
            
            # Calculated ability scores
            **ability_results,
            
            # Hit points (also in basic_info but keeping for compatibility)
            **hp_results,
            
            # Armor class (also in basic_info but keeping for compatibility)
            **ac_results,
            
            # Spellcasting
            **spell_results,
            
            # Proficiencies
            **proficiency_results,
            
            # Additional calculated values
            'initiative_bonus': self._calculate_initiative(raw_data, ability_results),
            'speed': self._calculate_speed(raw_data),
            
            # Wealth and encumbrance
            'wealth': wealth_results,
            'encumbrance': encumbrance_results,
            'containers': container_results,
            
            # Class features
            'class_features': class_features_results.get('class_features', []),
            
            # Comprehensive character data
            'spells': spells_data,
            'actions': actions_data,
            'inventory': inventory_data,
            'feats': feats_data,
            'saving_throws': saving_throws_data,
            'skills': skills_data,
            'notes': notes_data,
            
            # Meta information
            'meta': {
                'character_id': character_id,
                'calculator_version': '6.0.0',
                'calculation_timestamp': None,  # Will be set by calling code
                'source': 'enhanced_calculator',
                'rule_version': basic_info['rule_version'],
                'api_version': 'v5',
                'scraper_version': '6.0.0'
            }
        }
        
        # Apply HTML cleaning if configured
        complete_data = clean_character_data(complete_data, self.config_manager)
        
        logger.info(f"Successfully calculated complete JSON for character {character_id}")
        return complete_data
    
    def _extract_basic_info(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract and calculate basic character information."""
        logger.debug("Extracting basic character information")
        
        # Get character name and level
        name = raw_data.get('name', 'Unknown Character')
        classes = raw_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes)
        
        # Determine rule version
        rule_version = self._detect_rule_version(raw_data)
        
        # Calculate all components using individual calculators
        ability_results = self._safe_calculate(self.ability_calculator, raw_data, "ability scores")
        hp_results = self._safe_calculate(self.hp_calculator, raw_data, "hit points")
        ac_results = self._safe_calculate(self.ac_calculator, raw_data, "armor class")
        spell_results = self._safe_calculate_spellcasting_with_abilities(raw_data, ability_results)
        # Convert spell slots to object format
        spell_results = self._convert_spell_slots_to_object_format(spell_results)
        proficiency_results = self._safe_calculate(self.proficiency_calculator, raw_data, "proficiencies")
        
        # Create data model objects
        ability_scores = self._create_ability_scores_model(ability_results)
        classes = self._extract_classes(raw_data)
        species = self._extract_species(raw_data)
        background = self._extract_background(raw_data)
        hit_points = self._create_hit_points_model(hp_results)
        armor_class = self._create_armor_class_model(ac_results)
        spellcasting = self._create_spellcasting_model(spell_results)
        skills = self._create_skills_models(proficiency_results)
        
        return {
            'name': name,
            'level': total_level,
            'rule_version': rule_version,
            'ability_scores': ability_scores,
            'classes': classes,
            'species': species,
            'background': background,
            'hit_points': hit_points,
            'armor_class': armor_class,
            'spellcasting': spellcasting,
            'proficiency_bonus': proficiency_results.get('proficiency_bonus', 2),
            'skills': skills,
            'saving_throw_proficiencies': proficiency_results.get('saving_throw_proficiencies', []),
            'initiative_bonus': self._calculate_initiative(raw_data, ability_results),
            'speed': self._calculate_speed(raw_data),
            'alignment': self._extract_alignment(raw_data),
            'experience_points': raw_data.get('currentXp', 0),
            'equipment': self._extract_equipment(raw_data),
            'modifiers': self._extract_modifiers(raw_data)
        }
    
    def _extract_basic_info_dict(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract basic character information as dictionary."""
        name = raw_data.get('name', 'Unknown Character')
        
        # Calculate total level from classes
        classes = raw_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes)
        
        return {
            'character_id': raw_data.get('id', 0),
            'name': name,
            'level': total_level,
            'rule_version': self._detect_rule_version(raw_data),
            'classes': self._extract_classes_dict(raw_data),
            'species': self._extract_species_dict(raw_data),
            'background': self._extract_background_dict(raw_data),
            'alignment': self._extract_alignment(raw_data),
            'experience_points': raw_data.get('currentXp', 0)
        }
    
    def _safe_calculate(self, calculator, raw_data: Dict[str, Any], calculation_type: str) -> Dict[str, Any]:
        """Safely run a calculator with error handling."""
        try:
            # Create a minimal character for interface compliance
            minimal_character = self._create_minimal_character(raw_data)
            return calculator.calculate(minimal_character, raw_data)
        except Exception as e:
            logger.warning(f"Error calculating {calculation_type}: {str(e)}")
            return {}
    
    def _safe_calculate_hp_with_constitution(self, raw_data: Dict[str, Any], ability_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate hit points using the correct constitution score from ability results."""
        try:
            # Get constitution score from ability results
            constitution_data = ability_results.get('ability_scores', {}).get('constitution', {})
            constitution_score = constitution_data.get('score', 10)
            constitution_modifier = (constitution_score - 10) // 2
            
            logger.debug(f"HP calculation using CON {constitution_score} (modifier: {constitution_modifier})")
            
            # Temporarily patch the HP calculator's constitution method
            original_method = self.hp_calculator._get_constitution_modifier
            self.hp_calculator._get_constitution_modifier = lambda raw_data: constitution_modifier
            
            try:
                minimal_character = self._create_minimal_character(raw_data)
                result = self.hp_calculator.calculate(minimal_character, raw_data)
                return result if isinstance(result, dict) else {}
            finally:
                # Restore original method
                self.hp_calculator._get_constitution_modifier = original_method
                
        except Exception as e:
            logger.warning(f"Error calculating hit points with constitution: {e}")
            return {}
    
    def _safe_calculate_spellcasting_with_abilities(self, raw_data: Dict[str, Any], ability_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate spellcasting using the correct ability scores from ability results."""
        try:
            # Create a mapping of ability names to their calculated modifiers
            ability_modifiers = {}
            for ability_name, ability_data in ability_results.get('ability_scores', {}).items():
                score = ability_data.get('score', 10)
                modifier = (score - 10) // 2
                ability_modifiers[ability_name] = modifier
            
            logger.debug(f"Spellcasting calculation using ability modifiers: {ability_modifiers}")
            
            # Temporarily patch the spell calculator's ability modifier method
            original_method = self.spell_calculator._get_ability_modifier
            def patched_get_ability_modifier(raw_data, ability_name):
                return ability_modifiers.get(ability_name.lower(), 0)
            
            self.spell_calculator._get_ability_modifier = patched_get_ability_modifier
            
            try:
                minimal_character = self._create_minimal_character(raw_data)
                result = self.spell_calculator.calculate(minimal_character, raw_data)
                return result if isinstance(result, dict) else {}
            finally:
                # Restore original method
                self.spell_calculator._get_ability_modifier = original_method
                
        except Exception as e:
            logger.warning(f"Error calculating spellcasting with abilities: {e}")
            return {}
    
    def _safe_calculate_raw(self, calculator, raw_data: Dict[str, Any], calculation_type: str) -> Dict[str, Any]:
        """Safely run a calculator that expects raw data directly."""
        try:
            return calculator.calculate(raw_data)
        except Exception as e:
            logger.warning(f"Error calculating {calculation_type}: {str(e)}")
            return {}
    
    def _safe_calculate_encumbrance(self, raw_data: Dict[str, Any], ability_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate encumbrance using the correct ability scores from ability results."""
        try:
            # Pass ability scores to encumbrance calculator
            return self.encumbrance_calculator.calculate(raw_data, ability_scores=ability_results.get('ability_scores', {}))
        except Exception as e:
            logger.warning(f"Error calculating encumbrance: {str(e)}")
            return {}
    
    def _safe_calculate_containers(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate container inventory organization."""
        try:
            return self.container_calculator.calculate(raw_data)
        except Exception as e:
            logger.warning(f"Error calculating container inventory: {str(e)}")
            return {}
    
    def _create_minimal_character(self, raw_data: Dict[str, Any]) -> Character:
        """Create minimal character for calculator interface compliance."""
        character_id = raw_data.get('id', 0)
        name = raw_data.get('name', 'Unknown')
        classes = raw_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes)
        
        # Ensure minimum level of 1 for validation
        if total_level == 0:
            total_level = 1
        
        # Create minimal objects
        ability_scores = AbilityScores(
            strength=10, dexterity=10, constitution=10,
            intelligence=10, wisdom=10, charisma=10
        )
        
        character_class = CharacterClass(name="Unknown", level=total_level, hit_die=8)
        species = Species(name="Unknown")
        background = Background(name="Unknown")
        hit_points = HitPoints(maximum=1)
        armor_class = ArmorClass(total=10)
        spellcasting = Spellcasting()
        
        return Character(
            id=character_id,
            name=name,
            level=total_level,
            ability_scores=ability_scores,
            classes=[character_class],
            species=species,
            background=background,
            hit_points=hit_points,
            armor_class=armor_class,
            spellcasting=spellcasting,
            proficiency_bonus=2,
            # Priority 2 Features - default empty values
            enhanced_equipment=[],
            class_features=[],
            appearance=None,
            resource_pools=[],
            character_details=None
        )
    
    def _detect_rule_version(self, raw_data: Dict[str, Any]) -> str:
        """Detect rule version from character data using RuleVersionManager."""
        character_id = raw_data.get('id')
        detection_result = self.get_rule_version(raw_data, character_id)
        
        # Log detection for transparency
        self.log_rule_detection(detection_result, character_id)
        
        # Return string value for JSON serialization
        return detection_result.version.value
    
    def _create_ability_scores_model(self, ability_results: Dict[str, Any]) -> AbilityScores:
        """Create AbilityScores model from calculator results."""
        scores = ability_results.get('ability_scores', {})
        breakdown = ability_results.get('ability_score_breakdown', {})
        
        return AbilityScores(
            strength=scores.get('strength', 10),
            dexterity=scores.get('dexterity', 10),
            constitution=scores.get('constitution', 10),
            intelligence=scores.get('intelligence', 10),
            wisdom=scores.get('wisdom', 10),
            charisma=scores.get('charisma', 10)
        )
    
    def _extract_classes(self, raw_data: Dict[str, Any]) -> List[CharacterClass]:
        """Extract character classes."""
        classes = []
        class_data_list = raw_data.get('classes', [])
        
        # Detect rule version once for all classes
        rule_version_result = self.get_rule_version(raw_data)
        is_2024_rules = rule_version_result.version.value == "2024"
        
        for class_data in class_data_list:
            class_def = class_data.get('definition', {})
            subclass_def = class_data.get('subclassDefinition', {})
            
            character_class = CharacterClass(
                id=class_def.get('id'),
                name=class_def.get('name', 'Unknown'),
                level=class_data.get('level', 1),
                hit_die=class_def.get('hitDice', 8),
                subclass=subclass_def.get('name') if subclass_def else None,
                subclass_id=subclass_def.get('id') if subclass_def else None,
                is_2024=is_2024_rules
            )
            
            classes.append(character_class)
        
        return classes
    
    def _extract_classes_dict(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract character classes as dictionaries."""
        classes = []
        class_data_list = raw_data.get('classes', [])
        
        # Detect rule version once for all classes
        rule_version_result = self.get_rule_version(raw_data)
        is_2024_rules = rule_version_result.version.value == "2024"
        
        for class_data in class_data_list:
            class_def = class_data.get('definition', {})
            subclass_def = class_data.get('subclassDefinition', {})
            
            classes.append({
                'name': class_def.get('name', 'Unknown'),
                'level': class_data.get('level', 1),
                'hit_die': class_def.get('hitDice', 8),
                'subclass': subclass_def.get('name') if subclass_def else None,
                'spellcasting_ability': '',  # This would need proper implementation
                'is_2024': is_2024_rules
            })
        
        return classes
    
    def _extract_species(self, raw_data: Dict[str, Any]) -> Species:
        """Extract character species/race."""
        race_data = raw_data.get('race', {})
        
        # Handle both old and new race data structures
        if 'definition' in race_data:
            # Old structure: race.definition.name
            race_def = race_data.get('definition', {})
            race_id = race_def.get('id')
            race_name = race_def.get('name', 'Unknown')
            race_speed = race_def.get('speed', 30)
            subrace = race_data.get('subRace')
            subrace_name = subrace.get('definition', {}).get('name') if subrace else None
        else:
            # New structure: race.baseRaceName or race.fullName
            race_id = race_data.get('baseRaceId') or race_data.get('entityRaceId')
            race_name = race_data.get('baseRaceName') or race_data.get('fullName', 'Unknown')
            race_speed = 30  # Default, would need to parse from racialTraits for actual speed
            subrace_name = race_data.get('subRaceShortName') if race_data.get('subRaceShortName') else None
        
        return Species(
            id=race_id,
            name=race_name,
            subrace=subrace_name,
            speed=race_speed
        )
    
    def _extract_species_dict(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract character species with detailed traits."""
        race_data = raw_data.get('race', {})
        
        # Handle both old and new race data structures
        if 'definition' in race_data:
            # Old structure: race.definition.name
            race_def = race_data.get('definition', {})
            race_name = race_def.get('name', 'Unknown')
            subrace = race_data.get('subRace')
            subrace_name = subrace.get('definition', {}).get('name') if subrace else None
            race_description = race_def.get('description', '')
            source_id = race_def.get('sources', [{}])[0].get('sourceId')
        else:
            # New structure: race.baseRaceName or race.fullName
            race_name = race_data.get('baseRaceName') or race_data.get('fullName', 'Unknown')
            # Check for subrace info in new structure
            subrace_name = race_data.get('subRaceShortName') if race_data.get('subRaceShortName') else None
            race_description = race_data.get('description', '')
            source_id = race_data.get('sources', [{}])[0].get('sourceId') if race_data.get('sources') else None
        
        # Determine if this is 2024 rules based on source ID
        is_2024 = source_id in [145] if source_id else False
        
        # Extract racial traits
        traits = self._extract_racial_traits(race_data)
        
        return {
            'name': race_name,
            'subrace': subrace_name,
            'description': race_description,
            'size': race_data.get('sizeId', 4),  # 4 = Medium
            'source_id': source_id,
            'is_2024': is_2024,
            'traits': traits
        }
    
    def _extract_racial_traits(self, race_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract detailed racial traits from race data."""
        traits = []
        
        # Get racial traits from the appropriate structure
        racial_traits = race_data.get('racialTraits', [])
        if not racial_traits and 'definition' in race_data:
            racial_traits = race_data.get('definition', {}).get('racialTraits', [])
        
        for trait in racial_traits:
            trait_def = trait.get('definition', {})
            trait_name = trait_def.get('name', '')
            trait_description = trait_def.get('description', '')
            trait_snippet = trait_def.get('snippet', '')
            
            # Categorize traits by their content and name
            trait_info = {
                'name': trait_name,
                'description': trait_description or trait_snippet,
            }
            
            # Determine trait type and add specific information
            trait_type = self._determine_trait_type(trait_name, trait_description)
            trait_info['type'] = trait_type
            
            # Add specific trait information based on type
            if trait_type == 'sense':
                trait_info.update(self._extract_sense_info(trait_name, trait_description))
            elif trait_type == 'language':
                trait_info.update(self._extract_language_info(trait_name, trait_description))
            elif trait_type == 'proficiency':
                trait_info.update(self._extract_proficiency_info(trait_name, trait_description))
            elif trait_type == 'immunity':
                trait_info.update(self._extract_immunity_info(trait_name, trait_description))
            elif trait_type == 'advantage':
                trait_info.update(self._extract_advantage_info(trait_name, trait_description))
            elif trait_type == 'spellcasting':
                trait_info.update(self._extract_spellcasting_trait_info(trait_name, trait_description))
            
            traits.append(trait_info)
        
        return traits
    
    def _determine_trait_type(self, name: str, description: str) -> str:
        """Determine the type of racial trait based on name and description."""
        name_lower = name.lower()
        desc_lower = description.lower()
        
        if 'darkvision' in name_lower or 'vision' in name_lower:
            return 'sense'
        elif 'language' in name_lower or 'speak' in desc_lower and ('read' in desc_lower or 'write' in desc_lower):
            return 'language'
        elif 'proficiency' in name_lower or 'proficient' in desc_lower:
            return 'proficiency'
        elif 'immunity' in name_lower or 'immune' in desc_lower:
            return 'immunity'
        elif 'advantage' in name_lower or 'advantage' in desc_lower:
            return 'advantage'
        elif 'spell' in desc_lower or 'cantrip' in desc_lower or 'magic' in desc_lower:
            return 'spellcasting'
        else:
            return 'feature'
    
    def _extract_sense_info(self, name: str, description: str) -> Dict[str, Any]:
        """Extract sense-specific information."""
        info = {}
        if 'darkvision' in name.lower():
            info['sense_type'] = 'darkvision'
            # Extract range (e.g., "60 feet")
            import re
            range_match = re.search(r'(\d+)\s*feet?', description)
            if range_match:
                info['range'] = int(range_match.group(1))
        return info
    
    def _extract_language_info(self, name: str, description: str) -> Dict[str, Any]:
        """Extract language-specific information."""
        info = {}
        # Extract language name from description
        import re
        # Look for patterns like "speak, read, and write Common" or "Common"
        language_match = re.search(r'(?:speak|read|write).*?([A-Z][a-z]+)(?:\s|,|\.)', description)
        if language_match:
            info['language'] = language_match.group(1)
        elif 'common' in description.lower():
            info['language'] = 'Common'
        elif 'elvish' in description.lower():
            info['language'] = 'Elvish'
        elif 'draconic' in description.lower():
            info['language'] = 'Draconic'
        return info
    
    def _extract_proficiency_info(self, name: str, description: str) -> Dict[str, Any]:
        """Extract proficiency-specific information."""
        info = {}
        desc_lower = description.lower()
        if 'perception' in desc_lower:
            info['proficiency_type'] = 'perception'
        elif 'insight' in desc_lower:
            info['proficiency_type'] = 'insight'
        elif 'survival' in desc_lower:
            info['proficiency_type'] = 'survival'
        return info
    
    def _extract_immunity_info(self, name: str, description: str) -> Dict[str, Any]:
        """Extract immunity-specific information."""
        info = {}
        desc_lower = description.lower()
        if 'sleep' in desc_lower:
            info['immunity_type'] = 'magical-sleep'
        elif 'charm' in desc_lower:
            info['immunity_type'] = 'charm'
        return info
    
    def _extract_advantage_info(self, name: str, description: str) -> Dict[str, Any]:
        """Extract advantage-specific information."""
        info = {}
        desc_lower = description.lower()
        if 'saving throw' in desc_lower or 'save' in desc_lower:
            if 'charm' in desc_lower:
                info['advantage_type'] = 'charm-saves'
            else:
                info['advantage_type'] = 'saving-throws'
        return info
    
    def _extract_spellcasting_trait_info(self, name: str, description: str) -> Dict[str, Any]:
        """Extract spellcasting trait information."""
        info = {}
        desc_lower = description.lower()
        
        # Extract spells mentioned in the description
        import re
        spell_matches = re.findall(r'([A-Z][a-z\s]+(?:Bolt|Light|Step|Fire|Magic|Familiar))', description)
        if spell_matches:
            info['spells'] = [spell.strip() for spell in spell_matches]
        
        return info
    
    def _extract_background(self, raw_data: Dict[str, Any]) -> Background:
        """Extract character background."""
        bg_data = raw_data.get('background', {})
        bg_def = bg_data.get('definition', {}) if bg_data else {}
        
        return Background(
            id=bg_def.get('id'),
            name=bg_def.get('name', 'Unknown')
        )
    
    def _extract_background_dict(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract character background with detailed traits and information."""
        bg_data = raw_data.get('background', {})
        bg_def = bg_data.get('definition', {}) if bg_data else {}
        
        # Extract character traits (personality, ideals, bonds, flaws)
        traits_data = raw_data.get('traits', {})
        
        # Determine if this is 2024 rules based on source IDs in background
        source_id = bg_def.get('sources', [{}])[0].get('sourceId') if bg_def.get('sources') else None
        is_2024 = source_id in [145] if source_id else False
        
        # Extract additional character notes
        notes_data = raw_data.get('notes', {})
        
        return {
            'name': bg_def.get('name', 'Unknown'),
            'description': bg_def.get('description', ''),
            'source_id': source_id,
            'is_2024': is_2024,
            'personal_possessions': notes_data.get('personalPossessions', ''),
            'other_holdings': notes_data.get('otherHoldings'),
            'organizations': notes_data.get('organizations', ''),
            'enemies': notes_data.get('enemies', ''),
            'ideals': traits_data.get('ideals', ''),
            'bonds': traits_data.get('bonds', ''),
            'flaws': traits_data.get('flaws', ''),
            'personality_traits': traits_data.get('personalityTraits', '')
        }
    
    def _create_hit_points_model(self, hp_results: Dict[str, Any]) -> HitPoints:
        """Create HitPoints model from calculator results."""
        return HitPoints(
            maximum=hp_results.get('max_hp', 1),
            current=hp_results.get('current_hp'),
            temporary=hp_results.get('temporary_hp', 0),
            calculation_method=hp_results.get('calculation_method')
        )
    
    def _create_armor_class_model(self, ac_results: Dict[str, Any]) -> ArmorClass:
        """Create ArmorClass model from calculator results."""
        breakdown = ac_results.get('ac_breakdown', {})
        
        return ArmorClass(
            total=ac_results.get('armor_class', 10),
            base=breakdown.get('base', 10),
            armor_bonus=breakdown.get('armor_bonus', 0),
            shield_bonus=breakdown.get('shield_bonus', 0),
            dexterity_bonus=breakdown.get('dexterity_bonus', 0),
            calculation_method=breakdown.get('calculation_method', 'standard')
        )
    
    def _create_spellcasting_model(self, spell_results: Dict[str, Any]) -> Spellcasting:
        """Create Spellcasting model from calculator results."""
        slots = spell_results.get('spell_slots', [0] * 9)
        
        return Spellcasting(
            is_spellcaster=spell_results.get('is_spellcaster', False),
            spellcasting_ability=spell_results.get('spellcasting_ability'),
            spell_save_dc=spell_results.get('spell_save_dc'),
            spell_attack_bonus=spell_results.get('spell_attack_bonus'),
            spell_slots_level_1=slots[0] if len(slots) > 0 else 0,
            spell_slots_level_2=slots[1] if len(slots) > 1 else 0,
            spell_slots_level_3=slots[2] if len(slots) > 2 else 0,
            spell_slots_level_4=slots[3] if len(slots) > 3 else 0,
            spell_slots_level_5=slots[4] if len(slots) > 4 else 0,
            spell_slots_level_6=slots[5] if len(slots) > 5 else 0,
            spell_slots_level_7=slots[6] if len(slots) > 6 else 0,
            spell_slots_level_8=slots[7] if len(slots) > 7 else 0,
            spell_slots_level_9=slots[8] if len(slots) > 8 else 0,
            pact_slots=spell_results.get('pact_slots', 0),
            pact_slot_level=spell_results.get('pact_slot_level', 0)
        )
    
    def _create_skills_models(self, proficiency_results: Dict[str, Any]) -> List[Skill]:
        """Create Skill models from proficiency results."""
        skills = []
        skill_profs = proficiency_results.get('skill_proficiencies', [])
        
        for skill_info in skill_profs:
            skill = Skill(
                name=skill_info.get('name', 'Unknown'),
                ability=skill_info.get('ability', 'unknown'),
                proficient=skill_info.get('proficient', False),
                expertise=skill_info.get('expertise', False),
                total_bonus=skill_info.get('total_bonus', 0),
                proficiency_source=skill_info.get('source')
            )
            skills.append(skill)
        
        return skills
    
    def _calculate_initiative(self, raw_data: Dict[str, Any], ability_results: Dict[str, Any]) -> int:
        """Calculate initiative bonus including class features and feats."""
        ability_modifiers = ability_results.get('ability_modifiers', {})
        dex_modifier = ability_modifiers.get('dexterity', 0)
        initiative_bonus = dex_modifier
        
        # Check for class-specific initiative bonuses
        classes = raw_data.get('classes', [])
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            
            # Check for subclass-specific bonuses
            subclass_def = class_data.get('subclassDefinition', {})
            if subclass_def:
                subclass_name = subclass_def.get('name', '').lower()
                
                # Swashbuckler Rogue: Rakish Audacity (add Charisma modifier to initiative)
                if class_name == 'rogue' and 'swashbuckler' in subclass_name:
                    cha_modifier = ability_modifiers.get('charisma', 0)
                    initiative_bonus += cha_modifier
                    logger.debug(f"Rakish Audacity: +{cha_modifier} Charisma to initiative")
        
        # Check for feat-based initiative bonuses
        feat_bonus = self._get_initiative_feat_bonuses(raw_data)
        initiative_bonus += feat_bonus
        
        # Check for magical item bonuses (if any)
        item_bonus = self._get_initiative_item_bonuses(raw_data)
        initiative_bonus += item_bonus
        
        logger.debug(f"Initiative calculation: {dex_modifier} (Dex) + {feat_bonus} (feats) + {item_bonus} (items) = {initiative_bonus}")
        return initiative_bonus
    
    def _calculate_initiative_detailed(self, raw_data: Dict[str, Any], ability_results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate initiative with detailed source breakdown."""
        ability_modifiers = ability_results.get('ability_modifiers', {})
        dex_modifier = ability_modifiers.get('dexterity', 0)
        
        sources = []
        total_bonus = 0
        
        # Base Dexterity modifier
        if dex_modifier != 0:
            sources.append({
                'source': 'Dexterity',
                'value': dex_modifier
            })
            total_bonus += dex_modifier
        
        # Check for class-specific initiative bonuses
        classes = raw_data.get('classes', [])
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            
            # Check for subclass-specific bonuses
            subclass_def = class_data.get('subclassDefinition', {})
            if subclass_def:
                subclass_name = subclass_def.get('name', '').lower()
                
                # Swashbuckler Rogue: Rakish Audacity (add Charisma modifier to initiative)
                if class_name == 'rogue' and 'swashbuckler' in subclass_name:
                    cha_modifier = ability_modifiers.get('charisma', 0)
                    if cha_modifier != 0:
                        sources.append({
                            'source': 'Rakish Audacity (Charisma)',
                            'value': cha_modifier
                        })
                        total_bonus += cha_modifier
                        logger.debug(f"Rakish Audacity: +{cha_modifier} Charisma to initiative")
        
        # Check for feat-based initiative bonuses
        feat_sources = self._get_initiative_feat_sources(raw_data)
        sources.extend(feat_sources)
        total_bonus += sum(source['value'] for source in feat_sources)
        
        # Check for magical item bonuses (if any)
        item_sources = self._get_initiative_item_sources(raw_data)
        sources.extend(item_sources)
        total_bonus += sum(source['value'] for source in item_sources)
        
        return {
            'total': total_bonus,
            'sources': sources
        }
    
    def _get_initiative_feat_bonuses(self, raw_data: Dict[str, Any]) -> int:
        """Get initiative bonuses from feats."""
        bonus = 0
        
        # Check modifiers for initiative bonuses
        modifiers = raw_data.get('modifiers', {})
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                # Alert feat gives +5 to initiative
                if self._is_initiative_modifier(modifier):
                    mod_bonus = modifier.get('value', 0)
                    if mod_bonus is not None:
                        bonus += mod_bonus
                    friendly_name = modifier.get('friendlyTypeName', 'Unknown')
                    logger.debug(f"Initiative feat bonus: +{mod_bonus} from {friendly_name}")
        
        return bonus
    
    def _get_initiative_feat_sources(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get initiative bonus sources from feats."""
        sources = []
        
        # Use enhanced modifier filtering based on ddb-importer patterns
        initiative_modifiers = self._filter_modifiers_by_effect(raw_data, 'initiative')
        
        for modifier in initiative_modifiers:
            source_type = modifier.get('_source_type', 'Unknown')
            mod_bonus = self._extract_modifier_value(modifier)
            friendly_name = modifier.get('friendlyTypeName', f'{source_type.title()} Bonus')
            
            if mod_bonus != 0:
                sources.append({
                    'source': friendly_name,
                    'value': mod_bonus
                })
                logger.debug(f"Initiative {source_type} bonus: +{mod_bonus} from {friendly_name}")
        
        return sources
    
    def _filter_modifiers_by_effect(self, raw_data: Dict[str, Any], effect_type: str) -> List[Dict[str, Any]]:
        """Filter modifiers by effect type using ddb-importer patterns."""
        filtered_modifiers = []
        
        # Get all modifiers from different sources
        modifiers = raw_data.get('modifiers', {})
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                # Add source type for tracking
                modifier_copy = modifier.copy()
                modifier_copy['_source_type'] = source_type
                
                # Check if this modifier affects the specified effect type
                if self._modifier_affects_effect(modifier_copy, effect_type):
                    filtered_modifiers.append(modifier_copy)
        
        return filtered_modifiers
    
    def _modifier_affects_effect(self, modifier: Dict[str, Any], effect_type: str) -> bool:
        """Check if a modifier affects a specific effect type."""
        if effect_type == 'initiative':
            return self._is_initiative_modifier(modifier)
        elif effect_type == 'saving_throw':
            return self._is_saving_throw_modifier(modifier)
        elif effect_type == 'ability_score':
            return self._is_ability_score_modifier(modifier)
        # Add more effect types as needed
        return False
    
    def _extract_modifier_value(self, modifier: Dict[str, Any]) -> int:
        """Extract the numeric value from a modifier, following ddb-importer patterns."""
        # Handle different value formats
        value = modifier.get('value', 0)
        
        # Handle cases where value might be a string or complex object
        if isinstance(value, str):
            try:
                value = int(value)
            except ValueError:
                value = 0
        elif isinstance(value, dict):
            # Some modifiers might have complex value structures
            value = value.get('value', 0)
        
        return value if isinstance(value, int) else 0
    
    def _get_initiative_item_bonuses(self, raw_data: Dict[str, Any]) -> int:
        """Get initiative bonuses from magic items."""
        bonus = 0
        
        # Check inventory for items that grant initiative bonuses
        inventory = raw_data.get('inventory', [])
        for item in inventory:
            if item.get('equipped', False):
                item_def = item.get('definition', {})
                # Look for initiative bonuses in item modifiers
                # This would need more specific implementation based on D&D Beyond's item structure
        
        return bonus
    
    def _get_initiative_item_sources(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get initiative bonus sources from magic items."""
        sources = []
        
        # Check inventory for items that grant initiative bonuses
        inventory = raw_data.get('inventory', [])
        for item in inventory:
            if item.get('equipped', False):
                item_def = item.get('definition', {})
                # Look for initiative bonuses in item modifiers
                # This would need more specific implementation based on D&D Beyond's item structure
                # For now, this is a placeholder for future enhancement
        
        return sources
    
    def _is_initiative_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects initiative."""
        # Following ddb-importer patterns for robust modifier detection
        subtype = modifier.get('subType', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        modifier_type = modifier.get('type', '').lower()
        
        # Look for initiative-related keywords in multiple fields
        initiative_keywords = ['initiative']
        
        # Check if this is a bonus type modifier that affects initiative
        is_bonus_type = modifier_type in ['bonus', 'set']
        has_initiative_keyword = any(
            keyword in field for keyword in initiative_keywords 
            for field in [subtype, friendly_type] if field
        )
        
        # Additional patterns based on ddb-importer analysis
        # Check for specific modifier patterns that affect initiative
        if subtype == 'initiative' or 'initiative' in friendly_type:
            return True
            
        # Alert feat specifically (common initiative bonus)
        if 'alert' in friendly_type and is_bonus_type:
            return True
            
        return has_initiative_keyword and is_bonus_type
    
    def _is_saving_throw_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects saving throws."""
        subtype = modifier.get('subType', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        modifier_type = modifier.get('type', '').lower()
        
        # Look for saving throw related keywords
        saving_throw_keywords = ['saving-throw', 'save', 'saving_throw']
        
        is_bonus_type = modifier_type in ['bonus', 'proficiency', 'set']
        has_save_keyword = any(
            keyword in field for keyword in saving_throw_keywords 
            for field in [subtype, friendly_type] if field
        )
        
        return has_save_keyword and is_bonus_type
    
    def _is_ability_score_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects ability scores."""
        subtype = modifier.get('subType', '').lower()
        modifier_type = modifier.get('type', '').lower()
        
        # Check for ability score keywords in subtype
        ability_keywords = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        score_keywords = ['-score', '_score']
        
        is_relevant_type = modifier_type in ['bonus', 'set']
        
        # Check if subtype indicates ability score modification
        affects_ability = any(ability in subtype for ability in ability_keywords)
        affects_score = any(keyword in subtype for keyword in score_keywords)
        
        return is_relevant_type and (affects_ability or affects_score)
    
    def _calculate_speed(self, raw_data: Dict[str, Any]) -> int:
        """Calculate character speed with class features, items, and racial bonuses."""
        logger.debug("Calculating character speed")
        
        # Get base speed from race
        base_speed = self._get_base_racial_speed(raw_data)
        logger.debug(f"Base racial speed: {base_speed}")
        
        # Add class feature speed bonuses
        class_speed_bonus = self._get_class_speed_bonus(raw_data)
        logger.debug(f"Class speed bonus: {class_speed_bonus}")
        
        # Add racial speed bonuses (e.g., Wood Elf lineage)
        racial_speed_bonus = self._get_racial_speed_bonus(raw_data)
        logger.debug(f"Racial speed bonus: {racial_speed_bonus}")
        
        # Add item and modifier speed bonuses
        item_speed_bonus = self._get_item_speed_bonus(raw_data)
        logger.debug(f"Item speed bonus: {item_speed_bonus}")
        
        # Add modifier-based speed bonuses
        modifier_speed_bonus = self._get_modifier_speed_bonus(raw_data)
        logger.debug(f"Modifier speed bonus: {modifier_speed_bonus}")
        
        total_speed = base_speed + class_speed_bonus + racial_speed_bonus + item_speed_bonus + modifier_speed_bonus
        
        logger.debug(f"Speed calculation: {base_speed} (base) + {class_speed_bonus} (class) + {racial_speed_bonus} (racial) + {item_speed_bonus} (items) + {modifier_speed_bonus} (modifiers) = {total_speed}")
        return total_speed
    
    def _calculate_speed_detailed(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate character speed with detailed source breakdown."""
        logger.debug("Calculating detailed character speed")
        
        # Get all speed components with details
        base_speed = self._get_base_racial_speed(raw_data)
        class_speed_bonus = self._get_class_speed_bonus(raw_data)
        racial_speed_bonus = self._get_racial_speed_bonus(raw_data)
        item_speed_bonus = self._get_item_speed_bonus(raw_data)
        modifier_speed_bonus = self._get_modifier_speed_bonus(raw_data)
        
        total_speed = base_speed + class_speed_bonus + racial_speed_bonus + item_speed_bonus + modifier_speed_bonus
        
        # Build detailed breakdown
        sources = []
        
        # Base racial speed
        if base_speed > 0:
            race_data = raw_data.get('race', {})
            race_name = race_data.get('definition', {}).get('name', 'Unknown')
            if not race_name or race_name == 'Unknown':
                race_name = race_data.get('fullName', 'Unknown Race')
            
            sources.append({
                'source': f'Base ({race_name})',
                'value': base_speed,
                'type': 'racial'
            })
        
        # Class speed bonuses with details
        if class_speed_bonus > 0:
            classes = raw_data.get('classes', [])
            for class_data in classes:
                class_def = class_data.get('definition', {})
                class_name = class_def.get('name', '').lower()
                class_level = class_data.get('level', 1)
                
                if class_name == 'monk':
                    monk_bonus = self._get_monk_unarmored_movement_bonus(class_level, raw_data)
                    if monk_bonus > 0:
                        sources.append({
                            'source': f'Unarmored Movement (Monk {class_level})',
                            'value': monk_bonus,
                            'type': 'class_feature'
                        })
                
                elif class_name == 'barbarian':
                    barbarian_bonus = self._get_barbarian_fast_movement_bonus(class_level, raw_data)
                    if barbarian_bonus > 0:
                        sources.append({
                            'source': f'Fast Movement (Barbarian {class_level})',
                            'value': barbarian_bonus,
                            'type': 'class_feature'
                        })
        
        # Other bonuses (if implemented)
        if racial_speed_bonus > 0:
            sources.append({
                'source': 'Racial Feature',
                'value': racial_speed_bonus,
                'type': 'racial'
            })
        
        if item_speed_bonus > 0:
            sources.append({
                'source': 'Magic Items',
                'value': item_speed_bonus,
                'type': 'equipment'
            })
        
        if modifier_speed_bonus > 0:
            sources.append({
                'source': 'Other Modifiers',
                'value': modifier_speed_bonus,
                'type': 'modifier'
            })
        
        return {
            'total': total_speed,
            'sources': sources,
            'walking': {
                'total': total_speed,
                'sources': sources
            }
        }
    
    def _get_base_racial_speed(self, raw_data: Dict[str, Any]) -> int:
        """Get base speed from race/species."""
        race_data = raw_data.get('race', {})
        
        # Handle both old and new race data structures
        if 'definition' in race_data:
            # Old structure: race.definition.speed
            race_def = race_data.get('definition', {})
            return race_def.get('speed', 30)
        else:
            # New structure: check weightSpeeds first (most reliable)
            weight_speeds = race_data.get('weightSpeeds', {})
            normal_speeds = weight_speeds.get('normal', {})
            walk_speed = normal_speeds.get('walk', 0)
            if walk_speed > 0:
                logger.debug(f"Using weightSpeeds walk speed: {walk_speed}")
                return walk_speed
            
            # Fallback: check racial traits for speed descriptions
            racial_traits = race_data.get('racialTraits', [])
            for trait in racial_traits:
                trait_def = trait.get('definition', {})
                trait_name = trait_def.get('name', '').lower()
                description = trait_def.get('description', '')
                
                # Look for speed trait or elven lineage with speed bonus
                if trait_name == 'speed':
                    if '35 feet' in description or '35 ft' in description:
                        return 35
                    elif '25 feet' in description or '25 ft' in description:
                        return 25
                    elif '30 feet' in description or '30 ft' in description:
                        return 30
                elif 'elven lineage' in trait_name and ('speed increases to 35' in description.lower() or 'your speed increases to 35' in description.lower()):
                    # Wood Elf lineage specifically increases speed to 35
                    logger.debug("Detected Wood Elf lineage speed bonus")
                    return 35
            
            return 30  # Default
    
    def _get_class_speed_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get speed bonuses from class features."""
        total_bonus = 0
        classes = raw_data.get('classes', [])
        
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            class_level = class_data.get('level', 1)
            
            # Monk Unarmored Movement
            if class_name == 'monk':
                monk_bonus = self._get_monk_unarmored_movement_bonus(class_level, raw_data)
                total_bonus += monk_bonus
                if monk_bonus > 0:
                    logger.debug(f"Monk Unarmored Movement: +{monk_bonus} at level {class_level}")
            
            # Barbarian Fast Movement
            elif class_name == 'barbarian':
                barbarian_bonus = self._get_barbarian_fast_movement_bonus(class_level, raw_data)
                total_bonus += barbarian_bonus
                if barbarian_bonus > 0:
                    logger.debug(f"Barbarian Fast Movement: +{barbarian_bonus} at level {class_level}")
            
            # Future: Other class speed bonuses could be added here
            # - Ranger (some subclasses)
            # - Fighter (some subclasses)
            # - etc.
        
        return total_bonus
    
    def _get_monk_unarmored_movement_bonus(self, monk_level: int, raw_data: Dict[str, Any]) -> int:
        """
        Calculate Monk Unarmored Movement bonus.
        
        Unarmored Movement increases by 10 feet at levels 2, 6, 10, 14, 18.
        Only applies when not wearing armor or using a shield.
        """
        # Check if wearing armor or shield (Unarmored Movement doesn't work with these)
        if self._is_wearing_armor_or_shield(raw_data):
            logger.debug("Monk wearing armor/shield - no Unarmored Movement bonus")
            return 0
        
        # Calculate bonus based on level
        if monk_level >= 18:
            return 30  # +30 ft at level 18
        elif monk_level >= 14:
            return 25  # +25 ft at level 14
        elif monk_level >= 10:
            return 20  # +20 ft at level 10
        elif monk_level >= 6:
            return 15  # +15 ft at level 6
        elif monk_level >= 2:
            return 10  # +10 ft at level 2
        else:
            return 0   # No bonus at level 1
    
    def _get_barbarian_fast_movement_bonus(self, barbarian_level: int, raw_data: Dict[str, Any]) -> int:
        """
        Calculate Barbarian Fast Movement bonus.
        
        Fast Movement: +10 feet at level 5+, but only when not wearing heavy armor.
        """
        # Fast Movement starts at level 5
        if barbarian_level < 5:
            return 0
        
        # Check if wearing heavy armor (Fast Movement doesn't work with heavy armor)
        if self._is_wearing_heavy_armor(raw_data):
            logger.debug("Barbarian wearing heavy armor - no Fast Movement bonus")
            return 0
        
        return 10  # +10 ft when not wearing heavy armor
    
    def _get_racial_speed_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get speed bonuses from racial traits (e.g., Wood Elf lineage)."""
        race_data = raw_data.get('race', {})
        
        # Check for 2024 Elf lineages (Wood Elf gets +5 speed)
        racial_traits = race_data.get('racialTraits', [])
        for trait in racial_traits:
            trait_def = trait.get('definition', {})
            trait_name = trait_def.get('name', '').lower()
            
            # Wood Elf lineage gives +5 speed in 2024 rules
            if 'elven lineage' in trait_name:
                description = trait_def.get('description', '').lower()
                if 'speed increases to 35' in description or 'wood elf' in description:
                    # This is actually handled in base speed, but check for additional bonuses
                    pass
        
        # Check for other racial speed bonuses in modifiers
        # This will be handled by modifier parsing
        return 0
    
    def _get_item_speed_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get speed bonuses from equipped magic items."""
        total_bonus = 0
        inventory = raw_data.get('inventory', [])
        
        for item in inventory:
            if not item.get('equipped', False):
                continue
            
            item_def = item.get('definition', {})
            item_name = item_def.get('name', '').lower()
            
            # Common magic items that grant speed bonuses
            if 'boots of speed' in item_name:
                total_bonus += 10  # Boots of Speed double speed when activated
            elif 'winged boots' in item_name:
                total_bonus += 0   # Flight, not walking speed
            elif 'boots of striding and springing' in item_name:
                total_bonus += 10  # Increase walking speed
            
            # Check item modifiers for speed bonuses
            item_modifiers = item_def.get('grantedModifiers', [])
            for modifier in item_modifiers:
                if self._is_speed_modifier(modifier):
                    mod_value = self._extract_modifier_value(modifier)
                    if mod_value is not None:
                        total_bonus += mod_value
                        logger.debug(f"Item speed bonus: +{mod_value} from {item_name}")
        
        return total_bonus
    
    def _get_modifier_speed_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get speed bonuses from character modifiers (feats, spells, etc.)."""
        total_bonus = 0
        
        # Check modifiers for speed bonuses
        modifiers = raw_data.get('modifiers', {})
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
            
            for modifier in modifier_list:
                if self._is_speed_modifier(modifier):
                    mod_value = self._extract_modifier_value(modifier)
                    if mod_value is not None:
                        total_bonus += mod_value
                        source_name = modifier.get('friendlyTypeName', source_type.title())
                        logger.debug(f"Modifier speed bonus: +{mod_value} from {source_name}")
        
        return total_bonus
    
    def _is_speed_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects speed."""
        subtype = modifier.get('subType', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        modifier_type = modifier.get('type', '').lower()
        
        # Look for speed-related keywords
        speed_keywords = ['speed', 'movement']
        
        # Check if this is a bonus type modifier that affects speed
        is_bonus_type = modifier_type in ['bonus', 'set']
        has_speed_keyword = any(
            keyword in field for keyword in speed_keywords 
            for field in [subtype, friendly_type] if field
        )
        
        # Additional specific patterns
        if 'unarmored-movement' in subtype or 'fast-movement' in subtype:
            return True
        
        return has_speed_keyword and is_bonus_type
    
    def _is_wearing_armor_or_shield(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character is wearing armor or using a shield."""
        return self._is_wearing_armor(raw_data) or self._is_wearing_shield(raw_data)
    
    def _is_wearing_armor(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character is wearing armor."""
        inventory = raw_data.get('inventory', [])
        
        for item in inventory:
            if not item.get('equipped', False):
                continue
            
            item_def = item.get('definition', {})
            filter_type = item_def.get('filterType', '')
            
            # Check if this is armor
            if filter_type.lower() == 'armor':
                # Exclude shields
                armor_type = item_def.get('armorTypeId', 0)
                if armor_type != 4:  # 4 is typically shield
                    return True
        
        return False
    
    def _is_wearing_shield(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character is using a shield."""
        inventory = raw_data.get('inventory', [])
        
        for item in inventory:
            if not item.get('equipped', False):
                continue
            
            item_def = item.get('definition', {})
            filter_type = item_def.get('filterType', '')
            
            # Check if this is a shield
            if filter_type.lower() == 'armor':
                armor_type = item_def.get('armorTypeId', 0)
                if armor_type == 4:  # 4 is typically shield
                    return True
        
        return False
    
    def _is_wearing_heavy_armor(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character is wearing heavy armor."""
        inventory = raw_data.get('inventory', [])
        
        for item in inventory:
            if not item.get('equipped', False):
                continue
            
            item_def = item.get('definition', {})
            filter_type = item_def.get('filterType', '')
            
            # Check if this is heavy armor
            if filter_type.lower() == 'armor':
                armor_type = item_def.get('armorTypeId', 0)
                # Heavy armor types: typically 3 (but this may vary by system)
                # We'll also check armor class and name patterns
                armor_class = item_def.get('armorClass', 0)
                item_name = item_def.get('name', '').lower()
                
                # Heavy armor typically has AC 14+ and specific names
                heavy_armor_names = ['plate', 'chain mail', 'splint', 'ring mail']
                is_heavy = armor_class >= 14 or any(name in item_name for name in heavy_armor_names)
                
                if is_heavy:
                    return True
        
        return False
    
    def _extract_alignment(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Extract character alignment."""
        alignment_id = raw_data.get('alignmentId')
        if alignment_id:
            alignment_map = self.config_manager.get_constants_config().alignments
            return alignment_map.get(alignment_id)
        return None
    
    def _extract_equipment(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract character equipment."""
        # Simplified equipment extraction
        inventory = raw_data.get('inventory', [])
        equipment = []
        
        for item in inventory[:10]:  # Limit to first 10 items
            item_def = item.get('definition', {})
            equipment.append({
                'name': item_def.get('name', 'Unknown Item'),
                'equipped': item.get('equipped', False),
                'quantity': item.get('quantity', 1)
            })
        
        return equipment
    
    def _extract_modifiers(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract character modifiers summary."""
        # Return a simplified modifier summary
        modifiers_data = raw_data.get('modifiers', {})
        modifier_count = {}
        
        for source_type, modifier_list in modifiers_data.items():
            if isinstance(modifier_list, list):
                modifier_count[source_type] = len(modifier_list)
        
        return [{'source_summary': modifier_count}]
    
    def _create_raw_data_summary(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create summary of raw data for debugging."""
        return {
            'character_id': raw_data.get('id'),
            'api_version': 'v5',
            'data_keys': list(raw_data.keys()),
            'class_count': len(raw_data.get('classes', [])),
            'spell_count': len(raw_data.get('spells', {})),
            'modifier_sources': list(raw_data.get('modifiers', {}).keys())
        }
    
    def _extract_spells_comprehensive(self, raw_data: Dict[str, Any], ability_results: Dict[str, Any] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Extract comprehensive spell data grouped by source."""
        logger.debug("Extracting comprehensive spell data")
        
        spell_groups = {}
        seen_spells = {}  # For deduplication by name
        
        # Process class spells
        class_spells = raw_data.get('classSpells', [])
        for class_spell_entry in class_spells:
            character_class_id = class_spell_entry.get('characterClassId')
            spells = class_spell_entry.get('spells', [])
            
            # Get class info
            class_info = self._get_class_info_by_id(raw_data, character_class_id)
            class_name = class_info.get('name', 'Unknown Class')
            spellcasting_ability = class_info.get('spellcasting_ability', 'intelligence')
            
            for spell_data in spells:
                spell_info = self._create_spell_info(spell_data, spellcasting_ability, class_name, raw_data, ability_results)
                self._add_spell_to_groups(spell_groups, seen_spells, spell_info, class_name)
        
        # Process non-class spells
        non_class_spells = raw_data.get('spells', {})
        
        # Racial spells
        racial_spells = non_class_spells.get('race', [])
        for spell_data in racial_spells:
            spell_info = self._create_spell_info(spell_data, 'charisma', 'Racial', raw_data, ability_results)  # Default to charisma for racial
            self._add_spell_to_groups(spell_groups, seen_spells, spell_info, 'Racial')
        
        # Feat spells
        feat_spells = non_class_spells.get('feat', [])
        for spell_data in feat_spells:
            spell_info = self._create_spell_info(spell_data, 'charisma', 'Feat', raw_data, ability_results)  # Default to charisma for feats
            self._add_spell_to_groups(spell_groups, seen_spells, spell_info, 'Feat')
        
        # Item spells
        item_spells = non_class_spells.get('item', [])
        for spell_data in item_spells:
            spell_info = self._create_spell_info(spell_data, 'charisma', 'Magic Item', raw_data, ability_results)
            self._add_spell_to_groups(spell_groups, seen_spells, spell_info, 'Magic Item')
        
        return spell_groups
    
    def _get_class_info_by_id(self, raw_data: Dict[str, Any], class_id: int) -> Dict[str, Any]:
        """Get class information by character class ID."""
        classes = raw_data.get('classes', [])
        for class_data in classes:
            if class_data.get('id') == class_id:
                class_def = class_data.get('definition', {})
                class_name = class_def.get('name', 'Unknown')
                
                # Map spellcasting ability based on class
                spellcasting_abilities = {
                    'wizard': 'intelligence',
                    'sorcerer': 'charisma', 
                    'warlock': 'charisma',
                    'bard': 'charisma',
                    'cleric': 'wisdom',
                    'druid': 'wisdom',
                    'ranger': 'wisdom',
                    'paladin': 'charisma',
                    'artificer': 'intelligence',
                    'eldritch knight': 'intelligence',
                    'arcane trickster': 'intelligence'
                }
                
                spellcasting_ability = spellcasting_abilities.get(class_name.lower(), 'intelligence')
                
                return {
                    'name': class_name,
                    'spellcasting_ability': spellcasting_ability
                }
        
        return {'name': 'Unknown Class', 'spellcasting_ability': 'intelligence'}
    
    def _create_spell_info(self, spell_data: Dict[str, Any], spellcasting_ability: str, source: str, raw_data: Dict[str, Any] = None, ability_results: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create comprehensive spell information."""
        definition = spell_data.get('definition', {})
        
        # Handle case where definition might be None
        if definition is None:
            definition = {}
        
        name = definition.get('name', 'Unknown Spell')
        level = definition.get('level', 0)
        
        # Handle school - can be string or dict
        school_data = definition.get('school', {})
        if isinstance(school_data, dict):
            school = school_data.get('name', 'Unknown')
        else:
            school = str(school_data) if school_data else 'Unknown'
            
        description = definition.get('description', '')
        
        # Clean HTML from description
        import re
        description = re.sub(r'<[^>]+>', '', description)
        description = description.strip()
        
        # Calculate spell save DC and attack bonus using actual character data
        spell_stats = self._calculate_spell_stats(spellcasting_ability, raw_data, ability_results)
        
        # Extract spell components
        components = self._extract_spell_components(definition)
        
        # Determine effective preparation status
        always_prepared = spell_data.get('alwaysPrepared', False)
        is_prepared = spell_data.get('prepared', True)
        effective_prepared = always_prepared or is_prepared
        
        # Determine preparation type
        preparation_type = self._determine_preparation_type(spell_data, source)
        
        # Determine usage type
        usage_type = 'slot'  # Most spells use spell slots
        if level == 0:  # Cantrips
            usage_type = 'atwill'
        
        # Create source info
        source_info = {
            'class': source if source in ['Wizard', 'Cleric', 'Druid', 'Sorcerer', 'Warlock', 'Bard', 'Ranger', 'Paladin', 'Artificer'] else None,
            'feature': 'Class Spell' if source in ['Wizard', 'Cleric', 'Druid', 'Sorcerer', 'Warlock', 'Bard', 'Ranger', 'Paladin', 'Artificer'] else source,
            'granted_by': f"{source} spell list" if source in ['Wizard', 'Cleric', 'Druid', 'Sorcerer', 'Warlock', 'Bard', 'Ranger', 'Paladin', 'Artificer'] else source
        }
        
        spell_info = {
            'name': name,
            'level': level,
            'school': school,
            'description': description,
            'save_dc': spell_stats['save_dc'],
            'attack_bonus': spell_stats['attack_bonus'],
            'spellcasting_ability': spellcasting_ability,
            'always_prepared': always_prepared,
            'is_prepared': is_prepared,
            'effective_prepared': effective_prepared,
            'ritual': definition.get('ritual', False),
            'preparation_type': preparation_type,
            'usage_type': usage_type,
            'source_info': source_info,
            'data_source': 'A',  # API source
            'concentration': definition.get('concentration', False),
            'sources': [source],  # Array of sources
            **components
        }
        
        return spell_info
    
    def _determine_preparation_type(self, spell_data: Dict[str, Any], source: str) -> str:
        """Determine how the spell is prepared/known."""
        if spell_data.get('alwaysPrepared', False):
            return 'always_prepared'
        elif source in ['Wizard']:
            return 'prepared_from_book'
        elif source in ['Sorcerer', 'Warlock', 'Bard', 'Ranger']:
            return 'known'
        elif source in ['Cleric', 'Druid', 'Paladin']:
            return 'prepared_from_list'
        else:
            return 'granted'  # For racial, feat, or item spells
    
    def _calculate_spell_stats(self, spellcasting_ability: str, raw_data: Dict[str, Any] = None, ability_results: Dict[str, Any] = None) -> Dict[str, int]:
        """Calculate spell save DC and attack bonus using actual character data."""
        # Get ability modifier from ability results if available
        ability_modifier = 0
        if ability_results and spellcasting_ability:
            ability_scores = ability_results.get('ability_scores', {})
            ability_data = ability_scores.get(spellcasting_ability.lower(), {})
            ability_modifier = ability_data.get('modifier', 0)
        
        # Calculate proficiency bonus from character level
        proficiency_bonus = 2  # Default fallback
        if raw_data:
            classes = raw_data.get('classes', [])
            total_level = sum(cls.get('level', 0) for cls in classes)
            proficiency_bonus = self._calculate_proficiency_bonus(total_level)
        
        # Calculate save DC: 8 + proficiency + ability modifier
        save_dc = 8 + proficiency_bonus + ability_modifier
        attack_bonus = proficiency_bonus + ability_modifier
        
        logger.debug(f"Spell stats for {spellcasting_ability}: DC {save_dc} (8 + {proficiency_bonus} prof + {ability_modifier} mod), Attack +{attack_bonus}")
        
        return {
            'save_dc': save_dc,
            'attack_bonus': attack_bonus
        }
    
    def _extract_spell_components(self, definition: Dict[str, Any]) -> Dict[str, str]:
        """Extract spell casting components."""
        # Extract activation (casting time)
        activation = definition.get('activation', {})
        activation_type = activation.get('activationType', 1)
        activation_count = activation.get('activationTime', 1)
        
        activation_types = {
            1: "Action", 2: "Bonus Action", 3: "Reaction", 
            4: "Minute", 5: "Hour", 6: "No Action", 7: "Special"
        }
        
        casting_time = f"{activation_count} {activation_types.get(activation_type, 'Action')}"
        if activation_count > 1 and activation_type in [4, 5]:
            casting_time += "s"
        
        # Extract range
        range_data = definition.get('range', {})
        range_origin = range_data.get('origin', 1)
        range_value = range_data.get('value', 0)
        
        if range_origin == 1:  # Self
            spell_range = "Self"
        elif range_origin == 2:  # Touch
            spell_range = "Touch"
        else:
            spell_range = f"{range_value} feet"
        
        return {
            'casting_time': casting_time,
            'range': spell_range
        }
    
    def _add_spell_to_groups(self, spell_groups: Dict, seen_spells: Dict, spell_info: Dict, source: str):
        """Add spell to groups with deduplication."""
        spell_name = spell_info['name']
        
        if spell_name in seen_spells:
            # Add source to existing spell
            existing_spell = seen_spells[spell_name]
            if 'sources' not in existing_spell:
                existing_spell['sources'] = [existing_spell['source']]
            if source not in existing_spell['sources']:
                existing_spell['sources'].append(source)
        else:
            # Add new spell
            seen_spells[spell_name] = spell_info
            if source not in spell_groups:
                spell_groups[source] = []
            spell_groups[source].append(spell_info)
    
    def _extract_actions(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract character actions including weapon attacks, spells, and class features."""
        actions = []
        
        try:
            # Extract weapon attacks
            weapon_actions = self._extract_weapon_attacks(raw_data)
            actions.extend(weapon_actions)
            
            # Extract spell actions (cantrips and leveled spells that can be cast as actions)
            spell_actions = self._extract_spell_actions(raw_data)
            actions.extend(spell_actions)
            
            # Extract class feature actions
            class_feature_actions = self._extract_class_feature_actions(raw_data)
            actions.extend(class_feature_actions)
            
            # Extract racial feature actions
            racial_actions = self._extract_racial_feature_actions(raw_data)
            actions.extend(racial_actions)
            
            # Extract feat-based actions
            feat_actions = self._extract_feat_actions(raw_data)
            actions.extend(feat_actions)
            
            logger.debug(f"Extracted {len(actions)} total actions")
            
        except Exception as e:
            logger.error(f"Error extracting actions: {e}")
            # Fallback to basic attack if extraction fails
            actions = [{
                'name': 'Basic Attack',
                'description': 'Make a basic weapon attack',
                'type': 'attack',
                'snippet': 'Roll 1d20 + attack bonus'
            }]
        
        return actions
    
    def _extract_weapon_attacks(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract weapon attack actions from equipped weapons."""
        weapon_actions = []
        
        try:
            inventory = raw_data.get('inventory', [])
            ability_scores = self._get_ability_modifiers(raw_data)
            proficiency_bonus = self._calculate_proficiency_bonus(self._get_character_level(raw_data))
            
            for item in inventory:
                if not item.get('equipped', False):
                    continue
                    
                item_def = item.get('definition', {})
                filter_type = item_def.get('filterType', '').lower()
                
                if filter_type != 'weapon':
                    continue
                
                weapon_name = item_def.get('name', 'Unknown Weapon')
                weapon_type = item_def.get('type', 'Unknown')
                damage = item_def.get('damage', {})
                properties = item_def.get('properties', [])
                attack_type = item_def.get('attackType', 1)  # 1=melee, 2=ranged
                
                # Determine ability modifier for attack
                attack_ability = self._get_weapon_attack_ability(item_def, properties)
                attack_modifier = ability_scores.get(attack_ability, 0)
                
                # Check for weapon proficiency
                is_proficient = self._is_weapon_proficient(raw_data, weapon_name, weapon_type)
                attack_bonus = attack_modifier + (proficiency_bonus if is_proficient else 0)
                
                # Calculate damage
                damage_dice = damage.get('diceString', '1d4')
                damage_type = item_def.get('damageType', 'Bludgeoning')
                damage_modifier = attack_modifier
                
                # Create attack action
                weapon_action = {
                    'name': f'{weapon_name} Attack',
                    'description': self._create_weapon_description(item_def, attack_bonus, damage_dice, damage_modifier, damage_type),
                    'type': 'attack',
                    'snippet': f'Attack: +{attack_bonus} to hit, Damage: {damage_dice}+{damage_modifier} {damage_type.lower()}'
                }
                
                weapon_actions.append(weapon_action)
                
                # Add ranged attack variant if weapon is thrown
                if self._has_thrown_property(properties) and attack_type == 1:  # Melee weapon with thrown
                    ranged_range = item_def.get('range', 20)
                    long_range = item_def.get('longRange', ranged_range * 3)
                    
                    ranged_action = {
                        'name': f'{weapon_name} (Thrown)',
                        'description': self._create_thrown_weapon_description(item_def, attack_bonus, damage_dice, damage_modifier, damage_type, ranged_range, long_range),
                        'type': 'attack',
                        'snippet': f'Ranged Attack: +{attack_bonus} to hit, Range {ranged_range}/{long_range} ft, Damage: {damage_dice}+{damage_modifier} {damage_type.lower()}'
                    }
                    
                    weapon_actions.append(ranged_action)
                    
        except Exception as e:
            logger.error(f"Error extracting weapon attacks: {e}")
            
        return weapon_actions
    
    def _get_weapon_attack_ability(self, item_def: Dict[str, Any], properties: List[Dict[str, Any]]) -> str:
        """Determine which ability modifier to use for weapon attacks."""
        # Check for finesse property
        for prop in properties:
            if prop.get('name', '').lower() == 'finesse':
                # For finesse weapons, use the higher of STR or DEX
                # For simplicity, we'll default to DEX for finesse weapons
                return 'dexterity'
        
        # Check attack type: 1=melee (STR), 2=ranged (DEX)
        attack_type = item_def.get('attackType', 1)
        if attack_type == 2:
            return 'dexterity'
        else:
            return 'strength'
    
    def _is_weapon_proficient(self, raw_data: Dict[str, Any], weapon_name: str, weapon_type: str) -> bool:
        """Check if character is proficient with a weapon."""
        try:
            # Get character proficiencies
            character = self._create_minimal_character(raw_data)
            proficiencies = self.proficiency_calculator.calculate(character, raw_data)
            weapon_profs = proficiencies.get('weapons', [])
            
            # Check specific weapon proficiency
            weapon_name_lower = weapon_name.lower()
            for prof in weapon_profs:
                if prof.lower() == weapon_name_lower:
                    return True
            
            # Check weapon type proficiency (simple/martial)
            weapon_type_lower = weapon_type.lower()
            for prof in weapon_profs:
                if 'simple' in prof.lower() and 'simple' in weapon_type_lower:
                    return True
                elif 'martial' in prof.lower() and 'martial' in weapon_type_lower:
                    return True
                    
            return False
            
        except Exception as e:
            logger.error(f"Error checking weapon proficiency: {e}")
            return False
    
    def _has_thrown_property(self, properties: List[Dict[str, Any]]) -> bool:
        """Check if weapon has the thrown property."""
        for prop in properties:
            if prop.get('name', '').lower() == 'thrown':
                return True
        return False
    
    def _create_weapon_description(self, item_def: Dict[str, Any], attack_bonus: int, damage_dice: str, damage_modifier: int, damage_type: str) -> str:
        """Create a descriptive text for weapon attacks."""
        weapon_name = item_def.get('name', 'Unknown Weapon')
        attack_type = 'Melee' if item_def.get('attackType', 1) == 1 else 'Ranged'
        
        description = f"{attack_type} Weapon Attack: +{attack_bonus} to hit. "
        description += f"Hit: {damage_dice}"
        if damage_modifier > 0:
            description += f" + {damage_modifier}"
        elif damage_modifier < 0:
            description += f" - {abs(damage_modifier)}"
        description += f" ({damage_dice}{'+' + str(damage_modifier) if damage_modifier >= 0 else str(damage_modifier)}) {damage_type.lower()} damage."
        
        return description
    
    def _create_thrown_weapon_description(self, item_def: Dict[str, Any], attack_bonus: int, damage_dice: str, damage_modifier: int, damage_type: str, range_normal: int, range_long: int) -> str:
        """Create a descriptive text for thrown weapon attacks."""
        weapon_name = item_def.get('name', 'Unknown Weapon')
        
        description = f"Ranged Weapon Attack: +{attack_bonus} to hit, range {range_normal}/{range_long} ft. "
        description += f"Hit: {damage_dice}"
        if damage_modifier > 0:
            description += f" + {damage_modifier}"
        elif damage_modifier < 0:
            description += f" - {abs(damage_modifier)}"
        description += f" ({damage_dice}{'+' + str(damage_modifier) if damage_modifier >= 0 else str(damage_modifier)}) {damage_type.lower()} damage."
        
        return description
    
    def _extract_spell_actions(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract spell actions from character spells."""
        spell_actions = []
        
        try:
            # Get spellcasting data using existing comprehensive method
            character = self._create_minimal_character(raw_data)
            ability_results = self.ability_calculator.calculate(character, raw_data)
            spells_data = self._extract_spells_comprehensive(raw_data, ability_results)
            
            # Get spell stats for attack bonuses and save DCs
            spell_stats = {}
            
            # Process each spell source
            for source, spell_list in spells_data.items():
                if not spell_list:
                    continue
                    
                for spell_info in spell_list:
                    spell_name = spell_info.get('name', 'Unknown Spell')
                    spell_level = spell_info.get('level', 0)
                    description = spell_info.get('description', '')
                    casting_time = spell_info.get('casting_time', '1 action')
                    spell_range = spell_info.get('range', 'Self')
                    duration = spell_info.get('duration', 'Instantaneous')
                    
                    # Only include spells that can be cast as actions
                    if not self._is_action_spell(casting_time):
                        continue
                    
                    # Get spellcasting ability and modifiers
                    spellcasting_ability = spell_info.get('spellcasting_ability', 'intelligence')
                    
                    # Calculate spell attack bonus and save DC
                    if source not in spell_stats:
                        spell_stats[source] = self._calculate_spell_stats(spellcasting_ability, raw_data, ability_results)
                    
                    stats = spell_stats[source]
                    attack_bonus = stats.get('spell_attack_bonus', 0)
                    save_dc = stats.get('spell_save_dc', 8)
                    
                    # Create spell action
                    spell_action = {
                        'name': spell_name,
                        'description': self._create_spell_action_description(spell_info, attack_bonus, save_dc),
                        'type': 'spell' if spell_level > 0 else 'cantrip',
                        'snippet': self._create_spell_action_snippet(spell_info, attack_bonus, save_dc, casting_time, spell_range, duration)
                    }
                    
                    spell_actions.append(spell_action)
                    
        except Exception as e:
            logger.error(f"Error extracting spell actions: {e}")
            
        return spell_actions
    
    def _is_action_spell(self, casting_time: str) -> bool:
        """Check if a spell can be cast as an action."""
        casting_time_lower = casting_time.lower()
        
        # Include spells that can be cast as actions
        action_casting_times = [
            '1 action', 'action', 
            '1 bonus action', 'bonus action',
            '1 reaction', 'reaction'
        ]
        
        for action_time in action_casting_times:
            if action_time in casting_time_lower:
                return True
                
        return False
    
    def _create_spell_action_description(self, spell_info: Dict[str, Any], attack_bonus: int, save_dc: int) -> str:
        """Create a descriptive text for spell actions."""
        description = spell_info.get('description', '')
        
        # Add attack bonus or save DC info if relevant
        if 'spell attack' in description.lower():
            description = f"Spell Attack: +{attack_bonus} to hit. " + description
        elif 'saving throw' in description.lower() or 'save' in description.lower():
            description = f"Save DC: {save_dc}. " + description
            
        return description
    
    def _create_spell_action_snippet(self, spell_info: Dict[str, Any], attack_bonus: int, save_dc: int, casting_time: str, spell_range: str, duration: str) -> str:
        """Create a snippet for spell actions."""
        spell_name = spell_info.get('name', 'Unknown Spell')
        spell_level = spell_info.get('level', 0)
        
        snippet = f"{casting_time}, Range: {spell_range}, Duration: {duration}"
        
        # Add attack or save info
        description = spell_info.get('description', '').lower()
        if 'spell attack' in description:
            snippet += f", Attack: +{attack_bonus}"
        elif 'saving throw' in description or 'save' in description:
            snippet += f", Save DC: {save_dc}"
            
        return snippet
    
    def _extract_class_feature_actions(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract class feature actions."""
        class_actions = []
        
        try:
            classes = raw_data.get('classes', [])
            
            for class_data in classes:
                class_level = class_data.get('level', 1)
                class_features = class_data.get('classFeatures', [])
                
                for feature in class_features:
                    feature_def = feature.get('definition', {})
                    feature_name = feature_def.get('name', '')
                    feature_description = feature_def.get('description', '')
                    
                    # Check if this feature provides an action
                    if self._is_action_feature(feature_name, feature_description):
                        action = {
                            'name': feature_name,
                            'description': feature_description,
                            'type': 'class',
                            'snippet': self._create_class_feature_snippet(feature_def, feature_description)
                        }
                        
                        class_actions.append(action)
                        
        except Exception as e:
            logger.error(f"Error extracting class feature actions: {e}")
            
        return class_actions
    
    def _is_action_feature(self, feature_name: str, description: str) -> bool:
        """Check if a class feature provides an action."""
        feature_name_lower = feature_name.lower()
        description_lower = description.lower()
        
        # Common action-providing features
        action_keywords = [
            'action', 'bonus action', 'reaction',
            'channel divinity', 'rage', 'action surge', 'second wind',
            'wild shape', 'bardic inspiration', 'sneak attack',
            'lay on hands', 'divine smite', 'metamagic',
            'eldritch invocation', 'maneuvers', 'fighting style',
            'ki point', 'sorcery point', 'spell slot'
        ]
        
        # Check feature name for action keywords
        for keyword in action_keywords:
            if keyword in feature_name_lower:
                return True
                
        # Check description for action indicators
        action_indicators = [
            'as an action', 'as a bonus action', 'as a reaction',
            'you can use your action', 'on your turn',
            'when you take the attack action', 'you can spend',
            'you can use this feature', 'once per'
        ]
        
        for indicator in action_indicators:
            if indicator in description_lower:
                return True
                
        return False
    
    def _create_class_feature_snippet(self, feature_def: Dict[str, Any], description: str) -> str:
        """Create a snippet for class feature actions."""
        description_lower = description.lower()
        
        # Extract action type
        if 'bonus action' in description_lower:
            action_type = 'Bonus Action'
        elif 'reaction' in description_lower:
            action_type = 'Reaction'
        elif 'action' in description_lower:
            action_type = 'Action'
        else:
            action_type = 'Special'
        
        # Extract usage limitations
        usage = ''
        if 'once per short rest' in description_lower or 'short rest' in description_lower:
            usage = ' (Short Rest)'
        elif 'once per long rest' in description_lower or 'long rest' in description_lower:
            usage = ' (Long Rest)'
        elif 'per day' in description_lower:
            usage = ' (Per Day)'
        elif 'times' in description_lower and 'per' in description_lower:
            # Try to extract specific number of uses
            import re
            match = re.search(r'(\d+)\s*times?\s*per\s*(short|long)?\s*rest', description_lower)
            if match:
                num = match.group(1)
                rest_type = match.group(2) or 'rest'
                usage = f' ({num}/rest)'
        
        return f"{action_type}{usage}"
    
    def _extract_racial_feature_actions(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract racial feature actions."""
        racial_actions = []
        
        try:
            race_data = raw_data.get('race', {})
            racial_traits = race_data.get('racialTraits', [])
            
            for trait in racial_traits:
                trait_def = trait.get('definition', {})
                trait_name = trait_def.get('name', '')
                trait_description = trait_def.get('description', '')
                
                # Check if this trait provides an action
                if self._is_action_feature(trait_name, trait_description):
                    action = {
                        'name': trait_name,
                        'description': trait_description,
                        'type': 'racial',
                        'snippet': self._create_racial_feature_snippet(trait_def, trait_description)
                    }
                    
                    racial_actions.append(action)
                    
        except Exception as e:
            logger.error(f"Error extracting racial feature actions: {e}")
            
        return racial_actions
    
    def _create_racial_feature_snippet(self, trait_def: Dict[str, Any], description: str) -> str:
        """Create a snippet for racial feature actions."""
        # Use similar logic to class features but indicate racial source
        base_snippet = self._create_class_feature_snippet(trait_def, description)
        return f"Racial: {base_snippet}"
    
    def _extract_feat_actions(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract feat-based actions."""
        feat_actions = []
        
        try:
            feats = raw_data.get('feats', [])
            
            for feat in feats:
                feat_def = feat.get('definition', {})
                feat_name = feat_def.get('name', '')
                feat_description = feat_def.get('description', '')
                
                # Check if this feat provides an action
                if self._is_action_feature(feat_name, feat_description):
                    action = {
                        'name': feat_name,
                        'description': feat_description,
                        'type': 'feat',
                        'snippet': self._create_feat_snippet(feat_def, feat_description)
                    }
                    
                    feat_actions.append(action)
                    
        except Exception as e:
            logger.error(f"Error extracting feat actions: {e}")
            
        return feat_actions
    
    def _create_feat_snippet(self, feat_def: Dict[str, Any], description: str) -> str:
        """Create a snippet for feat actions."""
        # Use similar logic to class features but indicate feat source
        base_snippet = self._create_class_feature_snippet(feat_def, description)
        return f"Feat: {base_snippet}"
    
    def _get_ability_modifiers(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Get ability modifiers for all abilities."""
        try:
            # Create minimal character for calculator
            character = self._create_minimal_character(raw_data)
            ability_results = self.ability_calculator.calculate(character, raw_data)
            ability_scores = ability_results.get('ability_scores', {})
            
            modifiers = {}
            for ability, score in ability_scores.items():
                # Handle both integer scores and score objects
                if isinstance(score, dict):
                    final_score = score.get('total', score.get('final', 10))
                else:
                    final_score = score
                modifier = (final_score - 10) // 2
                modifiers[ability] = modifier
                
            return modifiers
        except Exception as e:
            logger.error(f"Error getting ability modifiers: {e}")
            return {'strength': 0, 'dexterity': 0, 'constitution': 0, 'intelligence': 0, 'wisdom': 0, 'charisma': 0}
    
    def _get_character_level(self, raw_data: Dict[str, Any]) -> int:
        """Get total character level."""
        try:
            classes = raw_data.get('classes', [])
            total_level = sum(class_data.get('level', 1) for class_data in classes)
            return max(total_level, 1)
        except Exception as e:
            logger.error(f"Error getting character level: {e}")
            return 1

    def _extract_inventory(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract character inventory/equipment."""
        inventory = []
        
        # Extract from standard inventory array (now includes custom items with includeCustomItems=true)
        inventory_data = raw_data.get('inventory', [])
        for item in inventory_data:
            item_def = item.get('definition', {})
            
            # Check if this is a custom item
            is_custom_item = item_def.get('isCustomItem', False)
            
            inventory_item = {
                'name': item_def.get('name', 'Unknown Item'),
                'quantity': item.get('quantity', 1),
                'equipped': item.get('equipped', False),
                'attuned': item.get('isAttuned', False),
                'requires_attunement': item_def.get('canAttune', False),
                'description': item_def.get('description', ''),
                'type': 'Custom' if is_custom_item else item_def.get('type', 'Item'),
                'rarity': item_def.get('rarity', 'Common'),
                'cost': item_def.get('cost', 0),
                'weight': item_def.get('weight', 0)
            }
            inventory.append(inventory_item)
        
        # Custom items are now included in the main inventory array with includeCustomItems=true
        # No separate processing needed - they have proper container relationships and type detection
        
        return inventory
    
    def _extract_feats(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract character feats from multiple sources."""
        feats = []
        feat_ids_seen = set()  # To avoid duplicates
        
        # Extract from main feats array
        feats_data = raw_data.get('feats', [])
        for feat in feats_data:
            feat_def = feat.get('definition', {})
            feat_id = feat_def.get('id')
            
            if feat_id and feat_id not in feat_ids_seen:
                feat_item = {
                    'name': feat_def.get('name', 'Unknown Feat'),
                    'description': feat_def.get('description', ''),
                    'source': f"feat:{feat_id}",
                    'prerequisite': feat_def.get('prerequisite', ''),
                    'is_half_feat': feat_def.get('isHalfFeat', False)
                }
                feats.append(feat_item)
                feat_ids_seen.add(feat_id)
        
        # Extract from background granted feats
        background_data = raw_data.get('background', {})
        if background_data:
            granted_feats = background_data.get('definition', {}).get('grantedFeats', [])
            for granted_feat in granted_feats:
                feat_ids = granted_feat.get('featIds', [])
                feat_name = granted_feat.get('name', 'Unknown Background Feat')
                
                for feat_id in feat_ids:
                    if feat_id not in feat_ids_seen:
                        # Look up feat details from featMap if available
                        feat_details = self._lookup_feat_details(feat_id, raw_data)
                        
                        feat_item = {
                            'name': feat_details.get('name', feat_name),
                            'description': feat_details.get('description', ''),
                            'source': f"background_feat:{granted_feat.get('id', feat_id)}",
                            'prerequisite': feat_details.get('prerequisite', ''),
                            'is_half_feat': feat_details.get('isHalfFeat', False)
                        }
                        feats.append(feat_item)
                        feat_ids_seen.add(feat_id)
        
        # Extract from race granted feats if any
        race_data = raw_data.get('race', {})
        if race_data:
            race_feat_ids = race_data.get('featIds', [])
            for feat_id in race_feat_ids:
                if feat_id not in feat_ids_seen:
                    feat_details = self._lookup_feat_details(feat_id, raw_data)
                    
                    feat_item = {
                        'name': feat_details.get('name', 'Unknown Racial Feat'),
                        'description': feat_details.get('description', ''),
                        'source': f"race_feat:{feat_id}",
                        'prerequisite': feat_details.get('prerequisite', ''),
                        'is_half_feat': feat_details.get('isHalfFeat', False)
                    }
                    feats.append(feat_item)
                    feat_ids_seen.add(feat_id)
        
        return feats
    
    def _lookup_feat_details(self, feat_id: int, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Look up feat details from various sources in the raw data."""
        # Check if there's a featMap or similar structure
        feat_map = raw_data.get('featMap', {})
        if str(feat_id) in feat_map:
            return feat_map[str(feat_id)]
        
        # If no featMap, try to find feat details in other structures
        # This is where you'd add additional lookup logic based on DDB API structure
        
        # Return basic structure if not found
        return {
            'name': f'Feat {feat_id}',
            'description': 'Description not available',
            'prerequisite': '',
            'isHalfFeat': False
        }
    
    def _extract_saving_throws(self, raw_data: Dict[str, Any], ability_results: Dict[str, Any]) -> Dict[str, int]:
        """Extract saving throw bonuses using proficiency calculator results."""
        ability_modifiers = ability_results.get('ability_modifiers', {})
        
        # Calculate proficiency bonus from level
        classes = raw_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes)
        proficiency_bonus = self._calculate_proficiency_bonus(total_level)
        
        # Get saving throw proficiencies from proficiency calculator
        proficiency_results = self._safe_calculate(self.proficiency_calculator, raw_data, "proficiencies")
        proficient_saves = set(proficiency_results.get('saving_throw_proficiencies', []))
        
        logger.debug(f"Saving throw proficiencies: {proficient_saves}")
        logger.debug(f"Proficiency bonus: +{proficiency_bonus}")
        
        saving_throws = {}
        for ability, modifier in ability_modifiers.items():
            ability_save = f"{ability}_save"
            bonus = modifier
            if ability in proficient_saves:
                bonus += proficiency_bonus
                logger.debug(f"{ability} save: {modifier} (base) + {proficiency_bonus} (prof) = {bonus}")
            else:
                logger.debug(f"{ability} save: {modifier} (base only)")
            saving_throws[ability_save] = bonus
        
        return saving_throws
    
    def _calculate_proficiency_bonus(self, level: int) -> int:
        """Calculate proficiency bonus based on character level."""
        if level >= 17:
            return 6
        elif level >= 13:
            return 5
        elif level >= 9:
            return 4
        elif level >= 5:
            return 3
        else:
            return 2
    
    def _extract_skills_detailed(self, raw_data: Dict[str, Any], ability_results: Dict[str, Any]) -> Dict[str, int]:
        """Extract detailed skill bonuses."""
        skills = {}
        ability_modifiers = ability_results.get('ability_modifiers', {})
        # Calculate proficiency bonus from level
        classes = raw_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes)
        proficiency_bonus = self._calculate_proficiency_bonus(total_level)
        
        # Skill to ability mapping
        skill_abilities = {
            'Acrobatics': 'dexterity',
            'Animal Handling': 'wisdom',
            'Arcana': 'intelligence',
            'Athletics': 'strength',
            'Deception': 'charisma',
            'History': 'intelligence',
            'Insight': 'wisdom',
            'Intimidation': 'charisma',
            'Investigation': 'intelligence',
            'Medicine': 'wisdom',
            'Nature': 'intelligence',
            'Perception': 'wisdom',
            'Performance': 'charisma',
            'Persuasion': 'charisma',
            'Religion': 'intelligence',
            'Sleight of Hand': 'dexterity',
            'Stealth': 'dexterity',
            'Survival': 'wisdom'
        }
        
        # Extract skill proficiencies from modifiers
        skill_modifiers = raw_data.get('modifiers', {})
        proficient_skills = set()
        expertise_skills = set()
        
        for modifier_source in skill_modifiers.values():
            if isinstance(modifier_source, list):
                for modifier in modifier_source:
                    if modifier.get('type') == 'proficiency' and 'skills' in modifier.get('subType', ''):
                        skill_name = modifier.get('friendlyTypeName', '')
                        proficient_skills.add(skill_name)
                    elif modifier.get('type') == 'expertise':
                        skill_name = modifier.get('friendlyTypeName', '')
                        expertise_skills.add(skill_name)
        
        # Calculate skill bonuses
        for skill_name, ability_name in skill_abilities.items():
            base_modifier = ability_modifiers.get(ability_name, 0)
            skill_bonus = base_modifier
            
            if skill_name in expertise_skills:
                skill_bonus += proficiency_bonus * 2
            elif skill_name in proficient_skills:
                skill_bonus += proficiency_bonus
            
            skills[skill_name] = skill_bonus
        
        return skills
    
    def _extract_appearance(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract character appearance information."""
        decorations = raw_data.get('decorations', {})
        
        appearance = {
            # Physical description from character data
            'gender': raw_data.get('gender', ''),
            'age': raw_data.get('age', ''),
            'height': raw_data.get('height', ''),
            'weight': raw_data.get('weight', ''),
            'hair': raw_data.get('hair', ''),
            'eyes': raw_data.get('eyes', ''),
            'skin': raw_data.get('skin', ''),
            
            # Avatar and decoration information
            'avatar_url': decorations.get('avatarUrl', ''),
            'frame_avatar_url': decorations.get('frameAvatarUrl', ''),
            'backdrop_avatar_url': decorations.get('backdropAvatarUrl', ''),
            'small_backdrop_avatar_url': decorations.get('smallBackdropAvatarUrl', ''),
            'large_backdrop_avatar_url': decorations.get('largeBackdropAvatarUrl', ''),
            'thumbnail_backdrop_avatar_url': decorations.get('thumbnailBackdropAvatarUrl', ''),
            'default_backdrop': decorations.get('defaultBackdrop', {}),
            'avatar_id': decorations.get('avatarId'),
            'portrait_decoration_id': decorations.get('portraitDecorationId'),
            'theme_color': decorations.get('themeColor')
        }
        
        return appearance
    
    def _extract_notes(self, raw_data: Dict[str, Any]) -> Dict[str, str]:
        """Extract character notes and background."""
        notes_data = raw_data.get('notes', {})
        
        notes = {
            'allies': notes_data.get('allies', ''),
            'backstory': notes_data.get('backstory', ''),
            'bonds': notes_data.get('bonds', ''),
            'character_notes': notes_data.get('characterAppearance', ''),
            'flaws': notes_data.get('flaws', ''),
            'ideals': notes_data.get('ideals', ''),
            'personal_traits': notes_data.get('personalityTraits', '')
        }
        
        return notes
    
    def _fix_ability_save_bonuses(self, ability_results: Dict[str, Any], proficiency_results: Dict[str, Any]):
        """
        Fix save bonuses after proficiency calculation is complete.
        
        This post-processing step updates save bonuses to include proficiency bonuses
        for saves that the character is proficient in.
        """
        logger.debug("Post-processing save bonuses with proficiency data")
        
        # Get proficiency bonus
        proficiency_bonus = proficiency_results.get('proficiency_bonus', 2)
        
        # Get save proficiencies
        save_proficiencies = proficiency_results.get('saving_throw_proficiencies', [])
        proficient_saves = set()
        
        for save_prof in save_proficiencies:
            if isinstance(save_prof, str):
                # Direct string format: ['constitution', 'charisma']
                proficient_saves.add(save_prof.lower())
            elif isinstance(save_prof, dict):
                # Dictionary format: [{'ability': 'constitution'}, ...]
                ability_name = save_prof.get('ability', '').lower()
                if ability_name:
                    proficient_saves.add(ability_name)
        
        logger.debug(f"Proficient saves: {proficient_saves}")
        
        # Update save bonuses in ability_scores
        ability_scores = ability_results.get('ability_scores', {})
        
        for ability_name, ability_data in ability_scores.items():
            if ability_name in proficient_saves:
                current_save_bonus = ability_data.get('save_bonus', 0)
                modifier = ability_data.get('modifier', 0)
                
                # If save bonus equals modifier, add proficiency
                if current_save_bonus == modifier:
                    new_save_bonus = modifier + proficiency_bonus
                    ability_data['save_bonus'] = new_save_bonus
                    logger.debug(f"Updated {ability_name} save bonus: {current_save_bonus} -> {new_save_bonus} (added proficiency)")
                else:
                    logger.debug(f"Skipping {ability_name} save bonus update (already includes proficiency)")
            else:
                logger.debug(f"{ability_name} not proficient in saves")
    
    def _create_basic_info_structure(
        self, 
        basic_info: Dict[str, Any], 
        hp_results: Dict[str, Any], 
        ac_results: Dict[str, Any], 
        ability_results: Dict[str, Any], 
        raw_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create structured basic_info.
        
        This method formats the basic character info in the expected JSON structure.
        """
        # Format armor class
        ac_breakdown = ac_results.get('ac_breakdown', {})
        armor_class_formatted = {
            'total': ac_results.get('armor_class', 10),
            'base': ac_breakdown.get('base', 10),
            'modifiers': [],
            'calculation': ac_breakdown.get('calculation_method', 'standard')
        }
        
        # Add Dex modifier if present
        dex_bonus = ac_breakdown.get('dexterity_bonus', 0)
        if dex_bonus > 0:
            armor_class_formatted['modifiers'].append({
                'source': 'Dexterity',
                'value': dex_bonus,
                'type': 'ability'
            })
        
        # Format calculation method
        if armor_class_formatted['calculation'] == 'unarmored':
            armor_class_formatted['calculation'] = 'Unarmored (10 + Dex)'
        
        # Format initiative with detailed breakdown
        initiative_detailed = self._calculate_initiative_detailed(raw_data, ability_results)
        initiative_formatted = {
            'total': initiative_detailed['total'],
            'sources': initiative_detailed['sources']
        }
        
        # Format speed with detailed breakdown
        speed_formatted = self._calculate_speed_detailed(raw_data)
        
        # Format hit points
        hp_breakdown = hp_results.get('hp_breakdown', {})
        max_hp = hp_results.get('max_hp', 1)
        
        # Get actual current HP and removed HP from raw data
        current_hp = hp_results.get('current_hp', max_hp)
        removed_hp = raw_data.get('removedHitPoints', 0)
        override_hp = raw_data.get('overrideHitPoints')
        
        hit_points_formatted = {
            'current': current_hp,
            'maximum': max_hp,
            'temporary': hp_results.get('temporary_hp', 0),
            'base': hp_breakdown.get('base_hit_points', 0) or 0,
            'bonus': hp_breakdown.get('feat_bonus', 0) + hp_breakdown.get('item_bonus', 0) + hp_breakdown.get('other_bonus', 0),
            'constitution_bonus': hp_breakdown.get('constitution_bonus', 0) or 0,
            'override': override_hp,
            'removed': removed_hp,
            'hit_point_type': raw_data.get("preferences", {}).get("hitPointType", 0),
            'hit_point_method': self._get_hp_method_name(raw_data)
        }
        
        # Format classes
        classes_formatted = []
        for class_info in basic_info.get('classes', []):
            if hasattr(class_info, 'model_dump'):
                class_data = class_info.model_dump()
            elif hasattr(class_info, 'dict'):
                class_data = class_info.dict()
            else:
                class_data = class_info
                
            classes_formatted.append({
                'name': class_data.get('name', 'Unknown'),
                'level': class_data.get('level', 1),
                'hit_die': class_data.get('hit_die', 8),  # Default to d8 instead of d6
                'subclass': class_data.get('subclass', ''),
                'spellcasting_ability': class_data.get('spellcasting_ability', ''),
                'is_2024': class_data.get('is_2024', False)
            })
        
        return {
            'character_id': basic_info.get('character_id', 0),
            'name': basic_info.get('name', 'Unknown Character'),
            'level': basic_info.get('level', 1),
            'proficiency_bonus': self._calculate_proficiency_bonus(basic_info.get('level', 1)),
            'experience': basic_info.get('experience_points', 0),
            'avatarUrl': raw_data.get('decorations', {}).get('avatarUrl', ''),
            'inspiration': raw_data.get('inspiration', False),
            'lifestyleId': raw_data.get('lifestyleId'),
            'armor_class': armor_class_formatted,
            'initiative': initiative_formatted,
            'speed': speed_formatted,
            'hit_points': hit_points_formatted,
            'classes': classes_formatted
        }
    
    def _get_hp_method_name(self, raw_data: Dict[str, Any]) -> str:
        """Get HP calculation method name based on hitPointType."""
        hit_point_type = raw_data.get("preferences", {}).get("hitPointType", 0)
        return "Fixed" if hit_point_type == 1 else "Manual" if hit_point_type == 2 else "Default"
    
    def _convert_spell_slots_to_object_format(self, spell_results: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert spell slots from array format to expected object format.
        
        Converts: spell_slots: [4, 3, 3, 3, 2, 0, 0, 0, 0]
        To: spell_slots: { regular_slots: { level_1: 4, level_2: 3, ... }, level_1: 4, level_2: 3, ... }
        """
        if 'spell_slots' not in spell_results:
            return spell_results
        
        array_slots = spell_results.get('spell_slots', [0] * 9)
        
        # Create regular_slots object
        regular_slots = {}
        spell_slots_flat = {}
        
        # Convert non-zero slots to object format
        for i, count in enumerate(array_slots):
            level = i + 1
            if count > 0:
                level_key = f"level_{level}"
                regular_slots[level_key] = count
                spell_slots_flat[level_key] = count
        
        # Create expected structure
        spell_slots_v5 = {
            'regular_slots': regular_slots,
            'pact_slots': {},  # Will be filled if pact magic exists
            'caster_level': spell_results.get('caster_level', 0),
            **spell_slots_flat  # Add flat level_1, level_2, etc. for backwards compatibility
        }
        
        # Add pact magic if present
        if spell_results.get('pact_slots', 0) > 0:
            spell_slots_v5['pact_slots'] = {
                'slots': spell_results.get('pact_slots', 0),
                'slot_level': spell_results.get('pact_slot_level', 0)
            }
        
        # Replace the array format with object format
        spell_results_v5 = spell_results.copy()
        spell_results_v5['spell_slots'] = spell_slots_v5
        
        return spell_results_v5
    
    def _extract_priority2_features(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract Priority 2 features using specialized extractors.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Dictionary containing all Priority 2 feature data
        """
        logger.debug("Extracting Priority 2 features")
        
        try:
            # Extract class features with rich details
            class_features = self.class_feature_extractor.extract_class_features(raw_data)
            logger.debug(f"Extracted {len(class_features)} class features")
            
            # Extract enhanced equipment details
            enhanced_equipment = self.equipment_details_extractor.extract_equipment_details(raw_data)
            logger.debug(f"Extracted {len(enhanced_equipment)} enhanced equipment items")
            
            # Extract character appearance
            appearance = self.character_appearance_extractor.extract_character_appearance(raw_data)
            logger.debug(f"Character appearance: {'extracted' if appearance else 'none'}")
            
            # Extract resource pools
            resource_pools = self.resource_tracking_extractor.extract_resource_pools(raw_data)
            logger.debug(f"Extracted {len(resource_pools)} resource pools")
            
            # Extract advanced character details
            character_details = self.advanced_details_extractor.extract_advanced_details(raw_data)
            logger.debug(f"Advanced character details: {'extracted' if character_details else 'none'}")
            
            return {
                'class_features': class_features,
                'enhanced_equipment': enhanced_equipment,
                'appearance': appearance,
                'resource_pools': resource_pools,
                'character_details': character_details
            }
            
        except Exception as e:
            logger.error(f"Error extracting Priority 2 features: {e}")
            return {
                'class_features': [],
                'enhanced_equipment': [],
                'appearance': None,
                'resource_pools': [],
                'character_details': None
            }