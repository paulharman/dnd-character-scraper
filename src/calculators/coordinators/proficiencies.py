"""
Proficiencies Coordinator

Coordinates the calculation of skill, tool, language, and weapon proficiencies
with comprehensive source tracking and 2014/2024 rule support.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass

from ..interfaces.coordination import ICoordinator
from ..utils.performance import monitor_performance
from ..utils.validation import validate_character_data
from ..services.interfaces import CalculationContext, CalculationResult, CalculationStatus
from ..proficiencies import ProficiencyCalculator
from ..skill_bonus_calculator import SkillBonusCalculator

logger = logging.getLogger(__name__)


@dataclass
class ProficienciesData:
    """Data class for proficiencies results."""
    skill_proficiencies: List[Dict[str, Any]]
    saving_throw_proficiencies: List[Dict[str, Any]]
    tool_proficiencies: List[Dict[str, Any]]
    language_proficiencies: List[Dict[str, Any]]
    weapon_proficiencies: List[Dict[str, Any]]
    proficiency_bonus: int
    skills_by_ability: Dict[str, List[Dict[str, Any]]]
    metadata: Dict[str, Any]


class ProficienciesCoordinator(ICoordinator):
    """
    Coordinates proficiency calculations with comprehensive source tracking.
    
    This coordinator handles:
    - Skill proficiencies from class, background, race, feats
    - Tool proficiencies from background, class, race
    - Language proficiencies from background, race, feats
    - Weapon proficiencies from class, race, feats
    - Saving throw proficiencies from class
    - Expertise tracking (double proficiency)
    - Comprehensive source attribution
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the proficiencies coordinator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        self.proficiency_calculator = ProficiencyCalculator(config_manager)
        self.skill_bonus_calculator = SkillBonusCalculator(config_manager)
        
        # Coordinator metadata
        self.name = "proficiencies"
        self._priority = 25  # Between abilities (20) and combat (30)
        self._dependencies = ["character_info", "abilities"]
        self.version = "1.1.0"  # Updated version for skill bonus integration
        
        self.logger.debug(f"Initialized {self.__class__.__name__}")
    
    @property
    def coordinator_name(self) -> str:
        """Get the coordinator name."""
        return self.name
    
    @property
    def dependencies(self) -> List[str]:
        """Get the list of dependencies."""
        return self._dependencies.copy()
    
    @property
    def priority(self) -> int:
        """Get the execution priority (lower = higher priority)."""
        return self._priority
    
    @monitor_performance("proficiencies_coordinate")
    def coordinate(self, raw_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Coordinate the calculation of proficiencies.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            context: Calculation context with character data and metadata
            
        Returns:
            CalculationResult with proficiency data
        """
        try:
            # Extract character id and level from raw data
            character_id = raw_data.get('id', 'unknown')
            
            self.logger.info(f"Calculating proficiencies for character {character_id}")
            
            # Create a simple character object for the calculator
            # The ProficiencyCalculator mainly needs id and level
            classes = raw_data.get('classes', [])
            total_level = sum(cls.get('level', 0) for cls in classes) or 1
            
            # Create a minimal character object
            from types import SimpleNamespace
            character = SimpleNamespace(id=character_id, level=total_level)
            
            # Get calculated abilities from context
            calculated_abilities = None
            if context and hasattr(context, 'metadata') and context.metadata:
                abilities_data = context.metadata.get('abilities', {})
                calculated_abilities = abilities_data.get('ability_scores', {})
            
            # Use the proficiency calculator with calculated abilities
            proficiency_data = self.proficiency_calculator.calculate(character, raw_data, calculated_abilities)
            
            # Calculate enhanced skill bonuses using the new skill bonus calculator
            enhanced_skill_bonuses = self._calculate_enhanced_skill_bonuses(raw_data, context)
            
            # Calculate passive skills using correct skill proficiencies data
            passive_skills = self._calculate_passive_skills(raw_data, context, proficiency_data)
            
            # Structure the data
            proficiencies_data = ProficienciesData(
                skill_proficiencies=proficiency_data.get('skill_proficiencies', []),
                saving_throw_proficiencies=proficiency_data.get('saving_throw_proficiencies', []),
                tool_proficiencies=proficiency_data.get('tool_proficiencies', []),
                language_proficiencies=proficiency_data.get('language_proficiencies', []),
                weapon_proficiencies=proficiency_data.get('weapon_proficiencies', []),
                proficiency_bonus=proficiency_data.get('proficiency_bonus', 2),
                skills_by_ability=proficiency_data.get('skills_by_ability', {}),
                metadata={
                    "calculation_method": "enhanced_skill_bonuses",
                    "total_skills": len(proficiency_data.get('skill_proficiencies', [])),
                    "total_tools": len(proficiency_data.get('tool_proficiencies', [])),
                    "total_languages": len(proficiency_data.get('language_proficiencies', [])),
                    "total_weapons": len(proficiency_data.get('weapon_proficiencies', [])),
                    "coordinator_version": self.version,
                    "passive_skills": passive_skills,
                    "enhanced_skill_bonuses": enhanced_skill_bonuses
                }
            )
            
            # Log summary with breakdown
            total_profs = (len(proficiencies_data.skill_proficiencies) + 
                         len(proficiencies_data.tool_proficiencies) + 
                         len(proficiencies_data.language_proficiencies) + 
                         len(proficiencies_data.weapon_proficiencies))
            
            self.logger.info(f"Successfully calculated proficiencies. Total: {total_profs}")
            self.logger.info(f"  Skills: {len(proficiencies_data.skill_proficiencies)}")
            self.logger.info(f"  Tools: {len(proficiencies_data.tool_proficiencies)}")
            self.logger.info(f"  Languages: {len(proficiencies_data.language_proficiencies)}")
            self.logger.info(f"  Weapons: {len(proficiencies_data.weapon_proficiencies)}")
            
            # Log actual proficiencies found
            if proficiencies_data.skill_proficiencies:
                skills = [p.get('name', 'Unknown') for p in proficiencies_data.skill_proficiencies]
                self.logger.info(f"  Skill names: {skills}")
            if proficiencies_data.language_proficiencies:
                langs = [p.get('name', 'Unknown') for p in proficiencies_data.language_proficiencies]
                self.logger.info(f"  Language names: {langs}")
            
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.COMPLETED,
                data=self._format_output(proficiencies_data),
                metadata=proficiencies_data.metadata
            )
            
        except Exception as e:
            self.logger.error(f"Error calculating proficiencies: {e}")
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.FAILED,
                data={},
                errors=[str(e)],
                metadata={"error": str(e)}
            )
    
    def _format_output(self, data: ProficienciesData) -> Dict[str, Any]:
        """
        Format proficiencies data for output.
        
        Args:
            data: ProficienciesData instance
            
        Returns:
            Formatted proficiency data dictionary
        """
        return {
            "skill_proficiencies": data.skill_proficiencies,
            "saving_throw_proficiencies": data.saving_throw_proficiencies,
            "tool_proficiencies": data.tool_proficiencies,
            "language_proficiencies": data.language_proficiencies,
            "weapon_proficiencies": data.weapon_proficiencies,
            "proficiency_bonus": data.proficiency_bonus,
            "skills_by_ability": data.skills_by_ability,
            "proficiencies_metadata": data.metadata,
            "passive_perception": data.metadata.get("passive_skills", {}).get("perception", 10),
            "passive_investigation": data.metadata.get("passive_skills", {}).get("investigation", 10),
            "passive_insight": data.metadata.get("passive_skills", {}).get("insight", 10),
            "enhanced_skill_bonuses": data.metadata.get("enhanced_skill_bonuses", [])
        }
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate that we have sufficient data for proficiency calculation.
        
        Args:
            raw_data: Raw character data to validate
            
        Returns:
            True if inputs are valid, False otherwise
        """
        try:
            if not raw_data:
                return False
            
            # Check for basic character data
            if not raw_data.get('classes'):
                return False
            
            # Proficiency calculation is robust - modifiers is helpful but not required
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating proficiency inputs: {e}")
            return False
    
    def get_dependencies(self) -> List[str]:
        """Get list of coordinator dependencies."""
        return self.dependencies.copy()
    
    def get_name(self) -> str:
        """Get coordinator name."""
        return self.name
    
    def get_priority(self) -> int:
        """Get coordinator priority."""
        return self.priority
    
    def get_version(self) -> str:
        """Get coordinator version."""
        return self.version
    
    def health_check(self) -> Dict[str, Any]:
        """
        Perform health check of the coordinator.
        
        Returns:
            Health check results
        """
        try:
            # Test calculator initialization
            test_calculator = self.proficiency_calculator is not None
            
            return {
                "status": "healthy" if test_calculator else "degraded",
                "name": self.name,
                "version": self.version,
                "priority": self.priority,
                "dependencies": self.dependencies,
                "calculator_available": test_calculator,
                "config_manager": self.config_manager is not None
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "name": self.name,
                "version": self.version
            }
    
    def _calculate_passive_skills(self, raw_data: Dict[str, Any], context: CalculationContext, proficiency_data: Dict[str, Any]) -> Dict[str, int]:
        """
        Calculate passive skill values (Perception, Investigation, Insight).
        
        Args:
            raw_data: Raw character data
            context: Calculation context (may contain ability data)
            proficiency_data: Proficiency calculation results
            
        Returns:
            Dictionary with passive skill values
        """
        try:
            # Get ability scores from context metadata if available, otherwise from raw_data
            abilities = {}
            if context and hasattr(context, 'metadata') and context.metadata:
                abilities_data = context.metadata.get('abilities', {})
                if abilities_data:
                    abilities = abilities_data.get('ability_scores', {})
            
            # Fallback to raw data if context doesn't have abilities
            if not abilities:
                abilities_raw = raw_data.get('abilities', {}).get('ability_scores', {})
                if abilities_raw:
                    abilities = abilities_raw
            
            # Get ability modifiers
            wisdom_mod = abilities.get('wisdom', {}).get('modifier', 0)
            intelligence_mod = abilities.get('intelligence', {}).get('modifier', 0)
            
            # Get proficiency bonus
            proficiency_bonus = proficiency_data.get('proficiency_bonus', 2)
            
            # Check for skill proficiencies and expertise
            skill_proficiencies = proficiency_data.get('skill_proficiencies', [])
            
            # Calculate passive scores using total_bonus directly (it already includes ability modifier)
            perception_total = 10 + wisdom_mod
            investigation_total = 10 + intelligence_mod
            insight_total = 10 + wisdom_mod
            
            for skill in skill_proficiencies:
                skill_name = skill.get('name')
                if skill_name == 'Perception':
                    perception_total = 10 + skill.get('total_bonus', wisdom_mod)
                elif skill_name == 'Investigation':
                    investigation_total = 10 + skill.get('total_bonus', intelligence_mod)
                elif skill_name == 'Insight':
                    insight_total = 10 + skill.get('total_bonus', wisdom_mod)
            
            # Calculate passive scores: 10 + total skill bonus
            passive_scores = {
                "perception": perception_total,
                "investigation": investigation_total,
                "insight": insight_total
            }
            
            self.logger.debug(f"Calculated passive skills: {passive_scores}")
            return passive_scores
            
        except Exception as e:
            self.logger.error(f"Error calculating passive skills: {e}")
            # Return reasonable defaults
            return {
                "perception": 10,
                "investigation": 10,
                "insight": 10
            }
    
    def _calculate_enhanced_skill_bonuses(self, raw_data: Dict[str, Any], context: CalculationContext) -> List[Dict[str, Any]]:
        """
        Calculate enhanced skill bonuses using the skill bonus calculator.
        
        Args:
            raw_data: Raw character data
            context: Calculation context
            
        Returns:
            List of enhanced skill bonus data
        """
        try:
            # Transform raw data to format expected by skill bonus calculator
            character_data = self._transform_raw_data_for_skill_calculator(raw_data, context)
            
            # Calculate skill bonuses using enhanced calculator
            result = self.skill_bonus_calculator.calculate(character_data)
            skill_bonuses_data = result.get('skill_bonuses', [])
            
            # Transform SkillBonus objects to dictionary format for compatibility
            enhanced_skills = []
            for skill_bonus in skill_bonuses_data:
                skill_dict = {
                    'name': skill_bonus.skill_name.replace('_', ' ').title(),
                    'ability': skill_bonus.ability_name,
                    'ability_modifier': skill_bonus.ability_modifier,
                    'proficiency_bonus': skill_bonus.proficiency_bonus,
                    'expertise_bonus': skill_bonus.expertise_bonus,
                    'magic_bonus': skill_bonus.magic_bonus,
                    'total_bonus': skill_bonus.total_bonus,
                    'is_proficient': skill_bonus.is_proficient,
                    'has_expertise': skill_bonus.has_expertise,
                    'bonus_expression': skill_bonus.bonus_expression,
                    'breakdown': skill_bonus.breakdown
                }
                enhanced_skills.append(skill_dict)
            
            return enhanced_skills
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced skill bonuses: {e}")
            return []
    
    def _transform_raw_data_for_skill_calculator(self, raw_data: Dict[str, Any], context: CalculationContext) -> Dict[str, Any]:
        """Transform raw D&D Beyond data to format expected by skill bonus calculator."""
        # Get ability scores from context
        ability_scores = {}
        if context and hasattr(context, 'metadata') and context.metadata:
            abilities_data = context.metadata.get('abilities', {})
            ability_scores = abilities_data.get('ability_scores', {})
        
        # Fallback to raw data if context doesn't have abilities
        if not ability_scores:
            stats = raw_data.get('stats', [])
            ability_id_map = {
                1: "strength", 2: "dexterity", 3: "constitution",
                4: "intelligence", 5: "wisdom", 6: "charisma"
            }
            
            for stat in stats:
                ability_id = stat.get('id')
                ability_score = stat.get('value', 10)
                
                if ability_id in ability_id_map:
                    ability_name = ability_id_map[ability_id]
                    modifier = (ability_score - 10) // 2
                    ability_scores[ability_name] = {
                        'score': ability_score,
                        'modifier': modifier
                    }
        
        # Get proficiencies from raw data
        proficiencies = self._extract_proficiencies_for_skill_calculator(raw_data)
        
        # Get character level
        classes = raw_data.get('classes', [])
        character_level = sum(cls.get('level', 0) for cls in classes) or 1
        
        # Get equipment (placeholder for magic item bonuses)
        equipment = {'equipped_items': []}
        
        return {
            'abilities': {
                'ability_scores': ability_scores
            },
            'proficiencies': proficiencies,
            'character_info': {
                'level': character_level
            },
            'equipment': equipment
        }
    
    def _extract_proficiencies_for_skill_calculator(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract skill proficiencies and expertise for the skill calculator."""
        skill_proficiencies = []
        skill_expertise = []
        
        # Extract from modifiers (D&D Beyond structure)
        modifiers = raw_data.get('modifiers', {})
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_skill_proficiency_modifier(modifier):
                    skill_name = self._extract_skill_name_from_modifier(modifier)
                    if skill_name:
                        skill_proficiencies.append({'name': skill_name})
                
                if self._is_skill_expertise_modifier(modifier):
                    skill_name = self._extract_skill_name_from_modifier(modifier)
                    if skill_name:
                        skill_expertise.append({'name': skill_name})
        
        return {
            'skill_proficiencies': skill_proficiencies,
            'skill_expertise': skill_expertise
        }
    
    def _is_skill_proficiency_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier grants skill proficiency."""
        if not isinstance(modifier, dict):
            return False
        
        modifier_type = modifier.get('type', '').lower()
        modifier_subtype = modifier.get('subType', '').lower()
        
        return ('proficiency' in modifier_type and 'skill' in modifier_subtype) or \
               ('skill' in modifier_type and 'proficiency' in modifier_type)
    
    def _is_skill_expertise_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier grants skill expertise."""
        if not isinstance(modifier, dict):
            return False
        
        modifier_type = modifier.get('type', '').lower()
        modifier_subtype = modifier.get('subType', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        return 'expertise' in modifier_type or 'expertise' in modifier_subtype or \
               'expertise' in friendly_type or 'double' in friendly_type
    
    def _extract_skill_name_from_modifier(self, modifier: Dict[str, Any]) -> Optional[str]:
        """Extract skill name from a modifier."""
        # Check friendlySubtypeName first (most specific)
        friendly_subtype = modifier.get('friendlySubtypeName', '')
        if friendly_subtype:
            return friendly_subtype.lower().replace(' ', '_')
        
        # Check subType
        subtype = modifier.get('subType', '')
        if subtype and subtype != 'skill':
            return subtype.lower().replace(' ', '_')
        
        # Check entityTypeId or other fields that might contain skill name
        # This would need to be expanded based on D&D Beyond's actual structure
        
        return None
    
    def _calculate_passive_skills_enhanced(self, enhanced_skill_bonuses: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Calculate passive skills using enhanced skill bonuses.
        
        Args:
            enhanced_skill_bonuses: List of enhanced skill bonus data
            
        Returns:
            Dictionary with passive skill values
        """
        try:
            passive_skills = {
                "perception": 10,
                "investigation": 10,
                "insight": 10
            }
            
            # Find the relevant skills and calculate passive scores
            for skill in enhanced_skill_bonuses:
                skill_name = skill.get('name', '').lower()
                total_bonus = skill.get('total_bonus', 0)
                
                if skill_name == 'perception':
                    passive_skills['perception'] = 10 + total_bonus
                elif skill_name == 'investigation':
                    passive_skills['investigation'] = 10 + total_bonus
                elif skill_name == 'insight':
                    passive_skills['insight'] = 10 + total_bonus
            
            self.logger.debug(f"Calculated enhanced passive skills: {passive_skills}")
            return passive_skills
            
        except Exception as e:
            self.logger.error(f"Error calculating enhanced passive skills: {e}")
            return {
                "perception": 10,
                "investigation": 10,
                "insight": 10
            }