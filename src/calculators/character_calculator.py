"""
Character Calculator

Main character calculator facade with full dependency injection wiring.
Coordinates all calculation services and coordinators to produce complete character data.
"""

from typing import Dict, Any, Optional
import logging

from src.models.character import Character
from src.config.manager import get_config_manager
from src.rules.version_manager import RuleVersionManager

from .base import RuleAwareCalculator
from .services.calculation_service import CalculationService
from .services.character_builder import CharacterBuilder
from .services.calculation_pipeline import CalculationPipeline
from .services.spell_service import SpellProcessingService
from .services.enhanced_spell_processor import EnhancedSpellProcessor
from .factories.calculator_factory import CalculatorFactory
from .services.interfaces import CalculationContext, CalculationStatus
from .utils.performance import monitor_performance

logger = logging.getLogger(__name__)


class CharacterCalculator(RuleAwareCalculator):
    """
    Main character calculator facade with full DI wiring.
    
    This calculator uses dependency injection to coordinate all calculation
    services and coordinators. It provides a high-level interface for
    character calculation while delegating the actual work to specialized
    services organized through a calculation pipeline.
    """
    
    def __init__(self, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
        """
        Initialize the character calculator with dependency injection.
        
        Args:
            config_manager: Configuration manager instance
            rule_manager: Rule version manager instance
        """
        super().__init__(config_manager, rule_manager)
        self.config_manager = config_manager or get_config_manager()
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Create factory for dependency injection
        self.factory = CalculatorFactory(self.config_manager)
        
        # Create calculation service using factory with full DI
        self.calculation_service = self._create_calculation_service()
        
        # Create character builder using factory
        self.character_builder = self._create_character_builder()
        
        # Create calculation pipeline with dependency management
        self.calculation_pipeline = self._create_calculation_pipeline()
        
        self.logger.info("CharacterCalculator initialized with dependency injection")
    
    def _create_calculation_service(self) -> CalculationService:
        """Create calculation service with full DI wiring."""
        service = self.factory.create_calculation_service(self.config_manager)
        self.logger.debug("Created CalculationService with DI")
        return service
    
    def _create_character_builder(self) -> CharacterBuilder:
        """Create character builder with dependencies."""
        builder = self.factory.create_character_builder(self.config_manager)
        self.logger.debug("Created CharacterBuilder with DI")
        return builder
    
    def _create_calculation_pipeline(self) -> CalculationPipeline:
        """Create calculation pipeline with dependency management."""
        pipeline = CalculationPipeline()
        
        # Register coordinator execution stages with dependencies
        coordinators = self.calculation_service.list_coordinators()
        
        # Register stages in dependency order
        if 'character_info' in coordinators:
            pipeline.register_stage(
                'character_info', 
                self.calculation_service.get_coordinator('character_info'), 
                dependencies=[]
            )
        
        if 'abilities' in coordinators:
            pipeline.register_stage(
                'abilities', 
                self.calculation_service.get_coordinator('abilities'), 
                dependencies=['character_info']
            )
        
        if 'proficiencies' in coordinators:
            pipeline.register_stage(
                'proficiencies', 
                self.calculation_service.get_coordinator('proficiencies'), 
                dependencies=['character_info', 'abilities']
            )
        
        if 'combat' in coordinators:
            pipeline.register_stage(
                'combat', 
                self.calculation_service.get_coordinator('combat'), 
                dependencies=['character_info', 'abilities']
            )
        
        if 'spellcasting' in coordinators:
            pipeline.register_stage(
                'spellcasting', 
                self.calculation_service.get_coordinator('spellcasting'), 
                dependencies=['character_info', 'abilities']
            )
        
        if 'features' in coordinators:
            pipeline.register_stage(
                'features', 
                self.calculation_service.get_coordinator('features'), 
                dependencies=['character_info', 'abilities']
            )
        
        if 'equipment' in coordinators:
            pipeline.register_stage(
                'equipment', 
                self.calculation_service.get_coordinator('equipment'), 
                dependencies=['character_info']
            )
        
        if 'resources' in coordinators:
            pipeline.register_stage(
                'resources', 
                self.calculation_service.get_coordinator('resources'), 
                dependencies=['character_info', 'abilities']
            )
        
        self.logger.debug(f"Created CalculationPipeline with {len(pipeline.list_stages())} stages")
        return pipeline
    
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
    
    @monitor_performance("character_calculator_calculate_character")
    def calculate_character(self, raw_data: Dict[str, Any]) -> Character:
        """
        Calculate complete character using orchestrated pipeline.
        
        Args:
            raw_data: Raw character data from D&D Beyond API
            
        Returns:
            Complete Character model with all calculated values
        """
        character_id = raw_data.get('id', 0)
        self.logger.info(f"Calculating complete character data for ID {character_id}")
        
        try:
            # Create calculation context
            context = CalculationContext(
                character_id=str(character_id),
                rule_version=self._detect_rule_version(raw_data)
            )
            
            # Execute calculation pipeline with dependency resolution
            calculated_data = self.calculation_pipeline.execute(raw_data, context)
            
            # Build Character model from pipeline results
            character = self._build_character_model(calculated_data, raw_data, context)
            
            self.logger.info(f"Successfully calculated character: {character.name} (Level {character.level})")
            return character
            
        except Exception as e:
            self.logger.error(f"Error calculating character {character_id}: {str(e)}")
            raise
    
    @monitor_performance("character_calculator_calculate_complete_json")
    def calculate_complete_json(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate complete character data as JSON using pipeline.
        
        Args:
            raw_data: Raw character data from D&D Beyond API
            
        Returns:
            Complete character data dictionary
        """
        character_id = raw_data.get('id', 0)
        self.logger.info(f"Calculating complete character JSON for ID {character_id}")
        
        try:
            # Create calculation context
            context = CalculationContext(
                character_id=str(character_id),
                rule_version=self._detect_rule_version(raw_data)
            )
            
            # Execute calculation pipeline
            calculated_data = self.calculation_pipeline.execute(raw_data, context)
            
            # Extract spell data from raw API response (missing in v6.0.0)
            self._extract_spell_data(raw_data, calculated_data)
            
            # Extract appearance and traits data from raw API response
            self._extract_appearance_data(raw_data, calculated_data)
            
            # Enhance JSON output structure with detailed breakdowns
            self._enhance_json_output_structure(calculated_data, context)
            
            # Remove pipeline metadata from output
            if '_pipeline_metadata' in calculated_data:
                del calculated_data['_pipeline_metadata']
            
            self.logger.info(f"Successfully calculated character JSON for ID {character_id}")
            return calculated_data
            
        except Exception as e:
            self.logger.error(f"Error calculating character JSON {character_id}: {str(e)}")
            raise
    
    def _build_character_model(self, calculated_data: Dict[str, Any], 
                              raw_data: Dict[str, Any], context: CalculationContext) -> Character:
        """
        Build Character model from pipeline results.
        
        Args:
            calculated_data: Results from calculation pipeline
            raw_data: Original raw character data
            context: Calculation context
            
        Returns:
            Complete Character model
        """
        from .services.character_builder import BuildContext
        
        # Create build context
        build_context = BuildContext(
            character_id=context.character_id,
            rule_version=context.rule_version
        )
        
        # Use character builder to create model
        character = self.character_builder.build_character(calculated_data, build_context)
        
        return character
    
    def _detect_rule_version(self, raw_data: Dict[str, Any]) -> str:
        """
        Detect rule version from character data.
        
        Args:
            raw_data: Raw character data
            
        Returns:
            Rule version string ("2014" or "2024")
        """
        # Use rule manager if available
        if self.rule_manager:
            character_id = raw_data.get('id', 0)
            detection_result = self.rule_manager.detect_rule_version(raw_data, character_id)
            return detection_result.version.value
        
        # Fallback detection logic
        if 'ruleVersion' in raw_data:
            version = raw_data['ruleVersion']
            if version == '2024' or version == 'onedd':
                return '2024'
        
        # Check for 2024 indicators
        sources = raw_data.get('sources', [])
        for source in sources:
            if isinstance(source, dict):
                source_name = source.get('name', '').lower()
                if '2024' in source_name or 'one d&d' in source_name:
                    return '2024'
        
        # Default to 2014
        return '2014'
    
    def get_calculation_service(self) -> CalculationService:
        """
        Get the calculation service instance.
        
        Returns:
            CalculationService instance
        """
        return self.calculation_service
    
    def get_character_builder(self) -> CharacterBuilder:
        """
        Get the character builder instance.
        
        Returns:
            CharacterBuilder instance
        """
        return self.character_builder
    
    def get_calculation_pipeline(self) -> CalculationPipeline:
        """
        Get the calculation pipeline instance.
        
        Returns:
            CalculationPipeline instance
        """
        return self.calculation_pipeline
    
    def get_factory(self) -> CalculatorFactory:
        """
        Get the calculator factory instance.
        
        Returns:
            CalculatorFactory instance
        """
        return self.factory
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the calculator and all dependencies.
        
        Returns:
            Health check results
        """
        health = {
            'status': 'healthy',
            'calculator': 'CharacterCalculator',
            'components': {}
        }
        
        # Check calculation service
        try:
            service_health = self.calculation_service.health_check()
            health['components']['calculation_service'] = service_health
            if service_health['status'] != 'healthy':
                health['status'] = 'degraded'
        except Exception as e:
            health['status'] = 'degraded'
            health['components']['calculation_service'] = {'status': 'error', 'error': str(e)}
        
        # Check calculation pipeline
        try:
            pipeline_health = self.calculation_pipeline.health_check()
            health['components']['calculation_pipeline'] = pipeline_health
            if pipeline_health['status'] != 'healthy':
                health['status'] = 'degraded'
        except Exception as e:
            health['status'] = 'degraded'
            health['components']['calculation_pipeline'] = {'status': 'error', 'error': str(e)}
        
        # Check factory
        try:
            factory_health = self.factory.health_check()
            health['components']['factory'] = factory_health
            if factory_health['status'] != 'healthy':
                health['status'] = 'degraded'
        except Exception as e:
            health['status'] = 'degraded'
            health['components']['factory'] = {'status': 'error', 'error': str(e)}
        
        return health
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics from all components.
        
        Returns:
            Performance metrics dictionary
        """
        metrics = {
            'calculation_service': {},
            'calculation_pipeline': {},
            'character_builder': {}
        }
        
        # Get calculation service metrics
        try:
            metrics['calculation_service'] = self.calculation_service.get_performance_metrics()
        except Exception as e:
            self.logger.error(f"Error getting calculation service metrics: {e}")
        
        # Get pipeline metrics
        try:
            pipeline_summary = self.calculation_pipeline.get_execution_summary()
            metrics['calculation_pipeline'] = pipeline_summary.get('performance', {})
        except Exception as e:
            self.logger.error(f"Error getting pipeline metrics: {e}")
        
        # Get character builder metrics
        try:
            metrics['character_builder'] = self.character_builder.get_build_statistics()
        except Exception as e:
            self.logger.error(f"Error getting character builder metrics: {e}")
        
        return metrics
    
    def _extract_spell_data(self, raw_data: Dict[str, Any], calculated_data: Dict[str, Any]) -> None:
        """
        Extract spell data from raw API response using enhanced spell processor.
        
        This method uses the enhanced spell processor to fix spell detection
        and deduplication issues.
        
        Args:
            raw_data: Raw character data from D&D Beyond API
            calculated_data: Calculated character data to enhance with spells
        """
        self.logger.debug("Extracting spell data using enhanced spell processor")
        
        try:
            # Use the enhanced spell processor
            enhanced_processor = EnhancedSpellProcessor()
            enhanced_spells = enhanced_processor.process_character_spells(raw_data)
            
            # Convert to legacy format for compatibility
            legacy_spells = enhanced_processor.convert_to_legacy_format(enhanced_spells)
            
            # Add to calculated data
            if legacy_spells:
                calculated_data['spells'] = legacy_spells
                
                # Update spell counts
                total_spells = sum(len(spell_list) for spell_list in legacy_spells.values())
                self.logger.info(f"Enhanced processor extracted {total_spells} spells from {len(legacy_spells)} sources")
                
                # Log spell breakdown
                for source, spell_list in legacy_spells.items():
                    self.logger.debug(f"  {source}: {len(spell_list)} spells")
            else:
                self.logger.debug("No spells extracted by enhanced processor")
                
        except Exception as e:
            self.logger.error(f"Error in enhanced spell extraction: {e}")
            # Fallback to original logic if enhanced processor fails
            self.logger.warning("Falling back to original spell extraction logic")
            self._extract_spell_data_fallback(raw_data, calculated_data)
    
    def _extract_spell_data_fallback(self, raw_data: Dict[str, Any], calculated_data: Dict[str, Any]) -> None:
        """
        Fallback spell extraction logic using the original method.
        
        This is used if the enhanced spell processor fails for any reason.
        """
        self.logger.debug("Using fallback spell extraction logic")
        
        try:
            # Extract spell data from raw API (same structure as v5.2.0)
            spells_data = raw_data.get('spells', {})
            class_spells_data = raw_data.get('classSpells', [])
            
            if not spells_data and not class_spells_data:
                self.logger.debug("No spell data found in raw API response")
                return
                
            # Create spells section for parser compatibility
            extracted_spells = {}
            
            # Process class spells (Wizard spells, etc.)
            for class_spell_entry in class_spells_data:
                character_class_id = class_spell_entry.get('characterClassId')
                spells = class_spell_entry.get('spells', [])
                
                if spells:
                    # Get class name from character classes
                    class_name = self._get_class_name_by_id(raw_data, character_class_id)
                    if class_name not in extracted_spells:
                        extracted_spells[class_name] = []
                    
                    # Process each spell - only include known spells
                    for spell_data in spells:
                        # Only include spells that are known (for class spells, use countsAsKnownSpell)
                        counts_as_known = spell_data.get('countsAsKnownSpell', False)
                        is_always_prepared = spell_data.get('alwaysPrepared', False)
                        
                        if counts_as_known or is_always_prepared:
                            spell_info = self._create_spell_info(spell_data, class_name)
                            if spell_info:
                                extracted_spells[class_name].append(spell_info)
            
            # Process non-class spells (racial, feat, item, background)
            for source_type, spell_list in spells_data.items():
                if isinstance(spell_list, list) and spell_list:
                    # Map source types to friendly names
                    source_name = self._get_spell_source_name(source_type)
                    if source_name not in extracted_spells:
                        extracted_spells[source_name] = []
                    
                    # Process each spell - include known spells and free cast spells
                    for spell_data in spell_list:
                        # For non-class spells, include if known, always prepared, prepared, or free cast
                        counts_as_known = spell_data.get('countsAsKnownSpell', False)
                        is_always_prepared = spell_data.get('alwaysPrepared', False)
                        is_prepared = spell_data.get('prepared', False)
                        uses_spell_slot = spell_data.get('usesSpellSlot', True)
                        limited_use = spell_data.get('limitedUse')
                        
                        # Include free cast spells (don't use spell slots and have limited use)
                        is_free_cast = not uses_spell_slot and limited_use is not None
                        
                        # Racial spells should always be available regardless of flags
                        is_racial_spell = source_type == 'race'
                        
                        if counts_as_known or is_always_prepared or is_prepared or is_free_cast or is_racial_spell:
                            # For feat spells, try to get the specific feat name
                            if source_type == 'feat':
                                specific_source = self._get_feat_name_for_spell(spell_data, calculated_data)
                                if specific_source not in extracted_spells:
                                    extracted_spells[specific_source] = []
                                spell_info = self._create_spell_info(spell_data, specific_source)
                                if spell_info:
                                    extracted_spells[specific_source].append(spell_info)
                            else:
                                spell_info = self._create_spell_info(spell_data, source_name)
                                if spell_info:
                                    extracted_spells[source_name].append(spell_info)
            
            # Add extracted spells to calculated data
            if extracted_spells:
                calculated_data['spells'] = extracted_spells
                
                # Update spell counts
                total_spells = sum(len(spell_list) for spell_list in extracted_spells.values())
                self.logger.info(f"Fallback extracted {total_spells} spells from {len(extracted_spells)} sources")
                
                # Log spell breakdown
                for source, spell_list in extracted_spells.items():
                    self.logger.debug(f"  {source}: {len(spell_list)} spells")
            else:
                self.logger.debug("No spells extracted from raw data using fallback")
                
        except Exception as e:
            self.logger.error(f"Error in fallback spell extraction: {e}")
            # Don't raise - spell extraction failure shouldn't break character processing
    
    def _get_class_name_by_id(self, raw_data: Dict[str, Any], character_class_id: int) -> str:
        """Get class name by character class ID."""
        for cls in raw_data.get('classes', []):
            if cls.get('id') == character_class_id:
                class_def = cls.get('definition', {})
                return class_def.get('name', 'Unknown Class')
        return 'Unknown Class'
    
    def _get_spell_source_name(self, source_type: str) -> str:
        """Map API source type to friendly source name."""
        source_mapping = {
            'race': 'Racial',
            'feat': 'Feat', 
            'item': 'Item',
            'background': 'Background',
            'class': 'Class'
        }
        return source_mapping.get(source_type, source_type.capitalize())
    
    def _create_spell_info(self, spell_data: Dict[str, Any], source_name: str) -> Optional[Dict[str, Any]]:
        """Create spell info dictionary from raw spell data."""
        try:
            spell_def = spell_data.get('definition', {})
            if not spell_def:
                return None
                
            spell_name = spell_def.get('name', 'Unknown Spell')
            spell_level = spell_def.get('level', 0)
            
            # Handle school field (can be string or dict)
            school_data = spell_def.get('school', 'Unknown')
            if isinstance(school_data, dict):
                spell_school = school_data.get('name', 'Unknown')
            else:
                spell_school = school_data
            
            # Extract basic spell information
            spell_info = {
                'name': spell_name,
                'level': spell_level,
                'school': spell_school,
                'source': source_name,
                'description': spell_def.get('description', ''),
                'isLegacy': False  # Default to false, can be enhanced later
            }
            
            # Add preparation info if available
            if 'prepared' in spell_data:
                spell_info['is_prepared'] = spell_data['prepared']
            if 'alwaysPrepared' in spell_data:
                spell_info['always_prepared'] = spell_data['alwaysPrepared']
            
            # Add ritual info
            if 'ritual' in spell_def:
                spell_info['ritual'] = spell_def['ritual']
            
            # Add concentration info
            if 'concentration' in spell_def:
                spell_info['concentration'] = spell_def['concentration']
                
            return spell_info
            
        except Exception as e:
            self.logger.warning(f"Error creating spell info for {spell_data}: {e}")
            return None
    
    def _extract_appearance_data(self, raw_data: Dict[str, Any], calculated_data: Dict[str, Any]) -> None:
        """
        Extract appearance and traits data from raw API response and add to calculated data.
        
        Args:
            raw_data: Raw character data from D&D Beyond API
            calculated_data: Calculated character data to enhance with appearance
        """
        self.logger.debug("Extracting appearance and traits data from raw API response")
        
        try:
            # Extract basic appearance fields
            appearance_data = {}
            appearance_fields = ['hair', 'eyes', 'skin', 'height', 'weight', 'age', 'gender']
            
            for field in appearance_fields:
                if field in raw_data and raw_data[field]:
                    appearance_data[field] = raw_data[field]
            
            # Extract traits data
            traits_data = raw_data.get('traits', {})
            appearance_description = traits_data.get('appearance', '')
            
            if appearance_description:
                appearance_data['description'] = appearance_description
            
            # Extract personality traits
            traits_info = {}
            if traits_data:
                trait_fields = ['personalityTraits', 'ideals', 'bonds', 'flaws']
                for field in trait_fields:
                    if field in traits_data and traits_data[field]:
                        traits_info[field] = traits_data[field]
            
            # Extract notes (backstory, allies, enemies, etc.)
            notes_data = raw_data.get('notes', {})
            notes_info = {}
            if notes_data:
                note_fields = ['allies', 'personalPossessions', 'otherHoldings', 'organizations', 'enemies', 'backstory', 'otherNotes']
                for field in note_fields:
                    if field in notes_data and notes_data[field]:
                        notes_info[field] = notes_data[field]
            
            # Add to calculated data
            if appearance_data:
                calculated_data['appearance'] = appearance_data
                self.logger.debug(f"Extracted appearance data: {list(appearance_data.keys())}")
            
            if traits_info:
                calculated_data['traits'] = traits_info
                self.logger.debug(f"Extracted traits data: {list(traits_info.keys())}")
            
            if notes_info:
                calculated_data['notes'] = notes_info
                self.logger.debug(f"Extracted notes data: {list(notes_info.keys())}")
                
        except Exception as e:
            self.logger.error(f"Error extracting appearance data: {e}")
            # Don't raise - appearance extraction failure shouldn't break character processing
    
    def _get_feat_name_for_spell(self, spell_data: Dict[str, Any], calculated_data: Dict[str, Any]) -> str:
        """
        Get the specific feat name for a feat spell instead of generic 'Feat'.
        
        Args:
            spell_data: Spell data from raw API
            calculated_data: Current calculated character data
            
        Returns:
            Specific feat name or fallback to 'Feat'
        """
        try:
            # Get the componentId from the spell
            component_id = spell_data.get('componentId')
            if not component_id:
                return 'Feat'
            
            # Look for the feat in the calculated features
            features = calculated_data.get('features', {})
            feats = features.get('feats', [])
            
            for feat in feats:
                if feat.get('id') == component_id:
                    feat_name = feat.get('name', 'Unknown Feat')
                    self.logger.debug(f"Mapped spell componentId {component_id} to feat: {feat_name}")
                    return feat_name
            
            # Fallback to generic name
            self.logger.debug(f"Could not find feat name for componentId {component_id}, using 'Feat'")
            return 'Feat'
            
        except Exception as e:
            self.logger.warning(f"Error getting feat name for spell: {e}")
            return 'Feat'
    
    def _enhance_json_output_structure(self, calculated_data: Dict[str, Any], context: CalculationContext) -> None:
        """
        Enhance JSON output structure with detailed breakdowns and standardized format.
        
        This method ensures all calculations include detailed breakdowns and follow
        the standardized JSON structure from steering rules.
        
        Args:
            calculated_data: Calculated character data to enhance
            context: Calculation context
        """
        self.logger.debug("Enhancing JSON output structure with detailed breakdowns")
        
        try:
            # Enhance combat section with weapon attacks
            self._enhance_combat_section(calculated_data)
            
            # Enhance skills section with detailed bonuses
            self._enhance_skills_section(calculated_data)
            
            # Enhance class resources section
            self._enhance_class_resources_section(calculated_data)
            
            # Add rule version information
            calculated_data['rule_version'] = context.rule_version
            
            # Add calculation metadata
            calculated_data['calculation_metadata'] = {
                'version': '6.0.0',
                'calculated_at': self._get_current_timestamp(),
                'rule_version': context.rule_version,
                'character_id': context.character_id
            }
            
            self.logger.debug("Successfully enhanced JSON output structure")
            
        except Exception as e:
            self.logger.error(f"Error enhancing JSON output structure: {e}")
            # Don't raise - enhancement failure shouldn't break character processing
    
    def _enhance_combat_section(self, calculated_data: Dict[str, Any]) -> None:
        """Enhance combat section with weapon attacks and detailed breakdowns."""
        combat_data = calculated_data.get('combat', {})
        if not combat_data:
            return
        
        # Ensure weapon attacks have proper structure
        attack_actions = combat_data.get('attack_actions', [])
        if attack_actions:
            enhanced_attacks = []
            for attack in attack_actions:
                if isinstance(attack, dict):
                    # Ensure attack has breakdown information
                    if 'breakdown' not in attack and 'attack_bonus' in attack:
                        attack['breakdown'] = {
                            'total': attack['attack_bonus'],
                            'description': f"Attack bonus: +{attack['attack_bonus']}"
                        }
                    enhanced_attacks.append(attack)
            
            combat_data['weapon_attacks'] = enhanced_attacks
            self.logger.debug(f"Enhanced {len(enhanced_attacks)} weapon attacks with breakdowns")
        
        # Ensure armor class has breakdown
        if 'armor_class' in combat_data and isinstance(combat_data['armor_class'], int):
            ac_value = combat_data['armor_class']
            combat_data['armor_class'] = {
                'total': ac_value,
                'base': 10,
                'breakdown': f"AC: {ac_value}"
            }
        
        # Ensure hit points have proper structure
        if 'hit_points' in combat_data and isinstance(combat_data['hit_points'], dict):
            hp_data = combat_data['hit_points']
            if 'breakdown' not in hp_data:
                max_hp = hp_data.get('maximum', 0)
                hp_data['breakdown'] = f"Max HP: {max_hp}"
    
    def _enhance_skills_section(self, calculated_data: Dict[str, Any]) -> None:
        """Enhance skills section with detailed bonus breakdowns."""
        proficiencies_data = calculated_data.get('proficiencies', {})
        if not proficiencies_data:
            return
        
        skills_data = proficiencies_data.get('skills', {})
        if not skills_data:
            return
        
        # Handle both dict and list formats for skills
        if isinstance(skills_data, dict):
            # Ensure each skill has detailed breakdown
            for skill_name, skill_info in skills_data.items():
                if isinstance(skill_info, dict) and 'breakdown' not in skill_info:
                    total_bonus = skill_info.get('total_bonus', 0)
                    ability_mod = skill_info.get('ability_modifier', 0)
                    prof_bonus = skill_info.get('proficiency_bonus', 0)
                    
                    # Create human-readable breakdown
                    breakdown_parts = []
                    if ability_mod != 0:
                        breakdown_parts.append(f"{ability_mod:+d} (ability)")
                    if prof_bonus != 0:
                        breakdown_parts.append(f"{prof_bonus:+d} (proficiency)")
                    
                    breakdown_text = " + ".join(breakdown_parts) if breakdown_parts else "0"
                    skill_info['breakdown'] = f"{breakdown_text} = {total_bonus:+d}"
            
            self.logger.debug(f"Enhanced {len(skills_data)} skills with detailed breakdowns")
        elif isinstance(skills_data, list):
            # Handle list format - enhance each skill object
            for skill_info in skills_data:
                if isinstance(skill_info, dict) and 'breakdown' not in skill_info:
                    total_bonus = skill_info.get('total_bonus', 0)
                    ability_mod = skill_info.get('ability_modifier', 0)
                    prof_bonus = skill_info.get('proficiency_bonus', 0)
                    
                    # Create human-readable breakdown
                    breakdown_parts = []
                    if ability_mod != 0:
                        breakdown_parts.append(f"{ability_mod:+d} (ability)")
                    if prof_bonus != 0:
                        breakdown_parts.append(f"{prof_bonus:+d} (proficiency)")
                    
                    breakdown_text = " + ".join(breakdown_parts) if breakdown_parts else "0"
                    skill_info['breakdown'] = f"{breakdown_text} = {total_bonus:+d}"
            
            self.logger.debug(f"Enhanced {len(skills_data)} skills with detailed breakdowns")
    
    def _enhance_class_resources_section(self, calculated_data: Dict[str, Any]) -> None:
        """Enhance class resources section with usage tracking."""
        # Check if resources coordinator added class resources
        if 'resources' in calculated_data:
            resources_data = calculated_data['resources']
            
            # Ensure class resources have proper structure
            class_resources = resources_data.get('class_resources', {})
            if class_resources:
                for resource_name, resource_info in class_resources.items():
                    if isinstance(resource_info, dict) and 'breakdown' not in resource_info:
                        total = resource_info.get('total', 0)
                        source_class = resource_info.get('source_class', 'Unknown')
                        resource_info['breakdown'] = f"{resource_name}: {total} from {source_class}"
                
                self.logger.debug(f"Enhanced {len(class_resources)} class resources")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + 'Z'