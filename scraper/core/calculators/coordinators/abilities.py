"""
Abilities Coordinator

Coordinates the calculation of ability scores, modifiers, and saving throws
with comprehensive source breakdown and 2014/2024 rule support.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass

from ..interfaces.coordination import ICoordinator
from ..ability_scores import EnhancedAbilityScoreCalculator
from ..utils.data_transformer import EnhancedCalculatorDataTransformer
from ..utils.performance import monitor_performance
from ..utils.validation import validate_character_data
from ..services.interfaces import CalculationContext, CalculationResult, CalculationStatus

logger = logging.getLogger(__name__)


@dataclass
class AbilityScoresData:
    """Data class for ability scores results."""
    ability_scores: Dict[str, Dict[str, Any]]
    ability_modifiers: Dict[str, int]
    ability_score_breakdown: Dict[str, Any]
    save_proficiencies: List[str]
    proficiency_bonus: int
    calculation_method: str
    metadata: Dict[str, Any]


class AbilitiesCoordinator(ICoordinator):
    """
    Coordinates ability score calculations with comprehensive source tracking.
    
    This coordinator handles:
    - Base ability scores from character creation
    - Species/racial bonuses (2014 vs 2024 differences)
    - ASI choices from leveling up
    - Feat bonuses
    - Item bonuses and "set" type modifiers
    - Saving throw proficiencies and bonuses
    - Comprehensive source breakdown
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the abilities coordinator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize enhanced calculator and data transformer
        self.enhanced_calculator = EnhancedAbilityScoreCalculator()
        self.data_transformer = EnhancedCalculatorDataTransformer()
        
        
        # Ability mappings for D&D Beyond
        self.ability_names = ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        self.ability_id_map = {
            1: "strength",
            2: "dexterity", 
            3: "constitution",
            4: "intelligence",
            5: "wisdom",
            6: "charisma"
        }
        
        # Common ASI choice mappings
        self.choice_mappings = {
            # These would be loaded from config in a real implementation
            # For now, using common patterns
        }
    
    @property
    def coordinator_name(self) -> str:
        """Get the coordinator name."""
        return "abilities"
    
    @property
    def dependencies(self) -> List[str]:
        """Get the list of dependencies."""
        return ["character_info"]  # Depends on character info for level and proficiency
    
    @property
    def priority(self) -> int:
        """Get the execution priority (lower = higher priority)."""
        return 20  # High priority - needed by many other coordinators
    
    @monitor_performance("abilities_coordinate")
    def coordinate(self, raw_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Coordinate the calculation of ability scores.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            context: Calculation context
            
        Returns:
            CalculationResult with ability scores and breakdown
        """
        self.logger.info(f"Coordinating abilities calculation for character {raw_data.get('id', 'unknown')}")
        
        try:
            # Check for required fields specific to this coordinator
            if not self._validate_ability_data(raw_data):
                return CalculationResult(
                    service_name=self.coordinator_name,
                    status=CalculationStatus.FAILED,
                    data={},
                    errors=["Missing required ability score data"]
                )
            
            # Try enhanced calculator first
            try:
                self.logger.debug("Using enhanced ability score calculator")
                transformed_data = self.data_transformer.transform_for_enhanced_calculators(raw_data)
                enhanced_result = self.enhanced_calculator.calculate(transformed_data, context)
                
                if enhanced_result.status == CalculationStatus.COMPLETED:
                    self.logger.info("Successfully used enhanced ability score calculator")
                    return self._transform_enhanced_result(enhanced_result, raw_data, context)
                else:
                    self.logger.debug(f"Enhanced calculator needs additional data: {enhanced_result.errors}")
                    
            except Exception as e:
                self.logger.debug(f"Enhanced calculator unavailable, using comprehensive calculation: {str(e)}")
            
            # Comprehensive ability score calculation
            self.logger.debug("Using comprehensive ability score calculation")
            
            # Get proficiency bonus from context or calculate
            proficiency_bonus = self._get_proficiency_bonus(raw_data, context)
            
            # Calculate ability scores with comprehensive breakdown
            ability_breakdown = self._calculate_final_scores(raw_data)
            
            # Extract final scores and modifiers
            final_scores = {}
            final_modifiers = {}
            
            for ability in self.ability_names:
                final_scores[ability] = ability_breakdown[ability]['total']
                final_modifiers[ability] = (final_scores[ability] - 10) // 2
            
            # Calculate saving throw proficiencies
            save_proficiencies = self._get_save_proficiencies(raw_data)
            
            # Format ability scores with save bonuses
            ability_scores = {}
            for ability in self.ability_names:
                save_bonus = self._calculate_save_bonus(ability, final_modifiers[ability], raw_data, proficiency_bonus)
                
                # Create simplified breakdown for compatibility
                breakdown = ability_breakdown[ability]
                simple_breakdown = self._create_simple_breakdown(breakdown)
                
                ability_scores[ability] = {
                    'score': final_scores[ability],
                    'modifier': final_modifiers[ability],
                    'save_bonus': save_bonus,
                    'source_breakdown': simple_breakdown
                }
            
            # Create result data
            result_data = {
                'ability_scores': ability_scores,
                'ability_modifiers': final_modifiers,
                'ability_score_breakdown': ability_breakdown,
                'save_proficiencies': save_proficiencies,
                'proficiency_bonus': proficiency_bonus,
                'calculation_method': 'comprehensive',
                'metadata': {
                    'total_asi_used': sum(breakdown.get('asi', 0) for breakdown in ability_breakdown.values()),
                    'has_racial_bonuses': any(breakdown.get('racial', 0) > 0 for breakdown in ability_breakdown.values()),
                    'has_feat_bonuses': any(breakdown.get('feat', 0) > 0 for breakdown in ability_breakdown.values()),
                    'has_item_bonuses': any(breakdown.get('item', 0) > 0 for breakdown in ability_breakdown.values()),
                    'highest_ability': max(final_scores.keys(), key=lambda k: final_scores[k]),
                    'lowest_ability': min(final_scores.keys(), key=lambda k: final_scores[k])
                }
            }
            
            self.logger.info(f"Successfully calculated ability scores. Highest: {result_data['metadata']['highest_ability']} "
                           f"({final_scores[result_data['metadata']['highest_ability']]})")
            
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.COMPLETED,
                data=result_data,
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error coordinating abilities calculation: {str(e)}")
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.FAILED,
                data={},
                errors=[f"Abilities calculation failed: {str(e)}"]
            )
    
    def _transform_enhanced_result(self, enhanced_result: CalculationResult, raw_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """Transform enhanced calculator result to coordinator format."""
        try:
            enhanced_data = enhanced_result.data
            ability_scores_data = enhanced_data.get('ability_scores', {})
            
            # Get proficiency bonus from context or calculate
            proficiency_bonus = self._get_proficiency_bonus(raw_data, context)
            
            # Transform to coordinator format
            ability_scores = {}
            final_modifiers = {}
            save_proficiencies = self._get_save_proficiencies(raw_data)
            
            for ability in self.ability_names:
                ability_data = ability_scores_data.get(ability, {})
                score = ability_data.get('score', 10)
                modifier = ability_data.get('modifier', (score - 10) // 2)
                save_bonus = self._calculate_save_bonus(ability, modifier, raw_data, proficiency_bonus)
                source_breakdown = ability_data.get('source_breakdown', {'base': score})
                
                final_modifiers[ability] = modifier
                ability_scores[ability] = {
                    'score': score,
                    'modifier': modifier, 
                    'save_bonus': save_bonus,
                    'source_breakdown': source_breakdown
                }
            
            # Create result data in coordinator format
            result_data = {
                'ability_scores': ability_scores,
                'ability_modifiers': final_modifiers,
                'ability_score_breakdown': enhanced_data.get('ability_score_breakdown', {}),
                'save_proficiencies': save_proficiencies,
                'proficiency_bonus': proficiency_bonus,
                'calculation_method': 'enhanced',
                'metadata': enhanced_data.get('metadata', {})
            }
            
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.COMPLETED,
                data=result_data,
                errors=enhanced_result.errors,
                warnings=enhanced_result.warnings,
                execution_time=enhanced_result.execution_time
            )
            
        except Exception as e:
            self.logger.error(f"Error transforming enhanced result: {str(e)}")
            raise
    
    def _validate_ability_data(self, raw_data: Dict[str, Any]) -> bool:
        """Validate that we have sufficient data for ability score calculation."""
        if not isinstance(raw_data, dict):
            return False
            
        # For empty character data, we can still provide defaults
        # This allows processing of malformed/empty characters
        if 'stats' not in raw_data:
            self.logger.warning("Missing 'stats' field in character data, will use defaults")
            return True  # We can handle this with defaults
        
        stats = raw_data.get('stats', [])
        if not stats:
            self.logger.warning("Empty stats array, will use defaults")
            return True  # We can handle this with defaults
        
        # Allow partial stats data - we'll fill in missing abilities with defaults
        return True
    
    def _get_proficiency_bonus(self, raw_data: Dict[str, Any], context: CalculationContext) -> int:
        """Get proficiency bonus from context or calculate from character level."""
        # First try to get from context (from character_info coordinator)
        if context and hasattr(context, 'metadata') and context.metadata:
            character_info = context.metadata.get('character_info', {})
            if 'proficiency_bonus' in character_info:
                return character_info['proficiency_bonus']
        
        # Fallback: calculate from character level
        classes = raw_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes) or 1
        return ((total_level - 1) // 4) + 2
    
    def _calculate_final_scores(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate final ability scores with complete source breakdown."""
        self.logger.debug("Calculating final ability scores with breakdown")
        
        # Get scores from different sources
        base_scores = self._calculate_base_scores(raw_data)
        racial_bonuses = self._calculate_racial_bonuses(raw_data)
        feat_bonuses = self._calculate_feat_bonuses(raw_data)
        asi_bonuses = self._calculate_asi_bonuses(raw_data)
        item_bonuses = self._calculate_item_bonuses(raw_data)
        other_bonuses = self._calculate_other_bonuses(raw_data)
        
        # Build comprehensive breakdown
        breakdown = {}
        
        for ability in self.ability_names:
            base = base_scores.get(ability, 10)
            racial = racial_bonuses.get(ability, 0)
            feat = feat_bonuses.get(ability, 0)
            asi = asi_bonuses.get(ability, 0)
            item = item_bonuses.get(ability, 0)
            other = other_bonuses.get(ability, 0)
            
            total = base + racial + feat + asi + item + other
            
            # Build source list for detailed tracking
            sources = []
            sources.append({'value': base, 'source': 'Base Score', 'source_type': 'base'})
            
            if racial != 0:
                sources.append({'value': racial, 'source': 'Species/Race', 'source_type': 'racial'})
            if feat != 0:
                sources.append({'value': feat, 'source': 'Feats', 'source_type': 'feat'})
            if asi != 0:
                sources.append({'value': asi, 'source': 'ASI/Choices', 'source_type': 'asi'})
            if item != 0:
                sources.append({'value': item, 'source': 'Items', 'source_type': 'item'})
            if other != 0:
                sources.append({'value': other, 'source': 'Other', 'source_type': 'other'})
            
            breakdown[ability] = {
                'total': total,
                'base': base,
                'racial': racial,
                'feat': feat,
                'asi': asi,
                'item': item,
                'other': other,
                'sources': sources
            }
            
            self.logger.debug(f"{ability.title()}: {total} (base:{base} racial:{racial} feat:{feat} asi:{asi} item:{item} other:{other})")
        
        return breakdown
    
    def _calculate_base_scores(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate base ability scores from character creation."""
        self.logger.debug("Calculating base ability scores")
        
        base_scores = {}
        stats = raw_data.get('stats', [])
        
        # Handle stats data if present
        for stat in stats:
            if not isinstance(stat, dict):
                continue
                
            ability_id = stat.get('id')
            base_value = stat.get('value', 10)
            
            # Handle malformed stat values
            if not isinstance(base_value, int):
                try:
                    base_value = int(base_value)
                except (ValueError, TypeError):
                    base_value = 10
                    self.logger.warning(f"Invalid stat value {stat.get('value')} for ability {ability_id}, using default 10")
            
            # Clamp to reasonable range
            base_value = max(3, min(30, base_value))
            
            if ability_id in self.ability_id_map:
                ability_name = self.ability_id_map[ability_id]
                base_scores[ability_name] = base_value
                self.logger.debug(f"Base {ability_name}: {base_value}")
        
        # Ensure all abilities are present with reasonable defaults
        for ability in self.ability_names:
            if ability not in base_scores:
                base_scores[ability] = 10
                self.logger.debug(f"Missing base score for {ability}, defaulting to 10")
        
        return base_scores
    
    def _calculate_racial_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score bonuses from species/race."""
        self.logger.debug("Calculating racial ability score bonuses")
        
        racial_bonuses = {ability: 0 for ability in self.ability_names}
        
        # Check race data
        race_data = raw_data.get('race', {})
        if not race_data:
            self.logger.debug("No race data found")
            return racial_bonuses
        
        # Method 1: Get racial ASI from race definition
        race_definition = race_data.get('definition', {})
        ability_score_increases = race_definition.get('abilityScoreIncreases', [])
        
        for asi in ability_score_increases:
            ability_id = asi.get('entityId')
            value = asi.get('value', 0)
            
            if ability_id in self.ability_id_map:
                ability_name = self.ability_id_map[ability_id]
                racial_bonuses[ability_name] += value
                self.logger.debug(f"Racial bonus {ability_name}: +{value} (from definition)")
        
        # Check for subrace bonuses
        subrace_data = raw_data.get('subrace')
        if subrace_data:
            subrace_definition = subrace_data.get('definition', {})
            subrace_asi = subrace_definition.get('abilityScoreIncreases', [])
            
            for asi in subrace_asi:
                ability_id = asi.get('entityId')
                value = asi.get('value', 0)
                
                if ability_id in self.ability_id_map:
                    ability_name = self.ability_id_map[ability_id]
                    racial_bonuses[ability_name] += value
                    self.logger.debug(f"Subrace bonus {ability_name}: +{value} (from definition)")
        
        # Method 2: Check for racial ability score modifiers (for some races)
        # Only use this if no 2024 racial ASI choices are detected
        if not self._has_2024_racial_asi_choices(raw_data):
            modifiers = raw_data.get('modifiers', {})
            race_modifiers = modifiers.get('race', [])
            
            for modifier in race_modifiers:
                if self._is_ability_score_modifier(modifier):
                    ability_name, bonus = self._extract_ability_modifier(modifier)
                    if ability_name:
                        racial_bonuses[ability_name] += bonus
                        self.logger.debug(f"Racial bonus {ability_name}: +{bonus} (from modifiers)")
        
        return racial_bonuses
    
    def _calculate_feat_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score bonuses from feats."""
        self.logger.debug("Calculating feat ability score bonuses")
        
        feat_bonuses = {ability: 0 for ability in self.ability_names}
        
        # Check modifiers for feat-based ability score increases
        modifiers = raw_data.get('modifiers', {})
        feat_modifiers = modifiers.get('feat', [])
        
        for modifier in feat_modifiers:
            if self._is_ability_score_modifier(modifier):
                ability_name, bonus = self._extract_ability_modifier(modifier)
                if ability_name:
                    feat_bonuses[ability_name] += bonus
                    self.logger.debug(f"Feat bonus {ability_name}: +{bonus}")
        
        return feat_bonuses
    
    def _calculate_asi_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score improvements from ASI choices and class leveling."""
        asi_bonuses = {ability: 0 for ability in self.ability_names}
        
        # Method 1: Check choices for ASI selections
        choices = raw_data.get('choices', {})
        
        for source_type, choice_list in choices.items():
            if not isinstance(choice_list, list):
                continue
                
            for choice in choice_list:
                if self._is_asi_choice(choice):
                    ability_name, bonus = self._extract_asi_choice(choice)
                    if ability_name:
                        asi_bonuses[ability_name] += bonus
                        self.logger.debug(f"ASI choice {ability_name}: +{bonus}")
                elif self._is_2024_racial_asi_choice(choice):
                    ability_name, bonus = self._extract_2024_racial_asi_choice(choice, raw_data)
                    if ability_name:
                        asi_bonuses[ability_name] += bonus
                        self.logger.debug(f"2024 Racial ASI {ability_name}: +{bonus}")
        
        # Method 2: Check class modifiers for ASI improvements
        modifiers = raw_data.get('modifiers', {})
        class_modifiers = modifiers.get('class', [])
        
        for modifier in class_modifiers:
            if self._is_ability_score_modifier(modifier):
                ability_name, bonus = self._extract_ability_modifier(modifier)
                if ability_name:
                    asi_bonuses[ability_name] += bonus
                    self.logger.debug(f"Class ASI {ability_name}: +{bonus} (from modifiers)")
        
        return asi_bonuses
    
    def _calculate_item_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score bonuses from magic items."""
        item_bonuses = {ability: 0 for ability in self.ability_names}
        item_set_values = {}  # Track "set" type modifiers separately
        
        # Check modifiers for item-based ability score increases
        modifiers = raw_data.get('modifiers', {})
        item_modifiers = modifiers.get('item', [])
        
        for modifier in item_modifiers:
            if self._is_ability_score_modifier(modifier):
                ability_name, value = self._extract_ability_modifier(modifier)
                if ability_name:
                    if value < -999000:  # Special encoding for "set" type
                        set_value = value + 999999
                        item_set_values[ability_name] = set_value
                        self.logger.debug(f"Item sets {ability_name} to: {set_value}")
                    else:
                        item_bonuses[ability_name] += value
                        self.logger.debug(f"Item bonus {ability_name}: +{value}")
        
        # Apply set values by calculating the difference from base
        if item_set_values:
            base_scores = self._calculate_base_scores(raw_data)
            for ability_name, set_value in item_set_values.items():
                base_score = base_scores.get(ability_name, 10)
                needed_bonus = set_value - base_score
                item_bonuses[ability_name] = needed_bonus
                self.logger.debug(f"Item sets {ability_name} from {base_score} to {set_value} (bonus: {needed_bonus})")
        
        return item_bonuses
    
    def _calculate_other_bonuses(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Calculate ability score bonuses from other sources."""
        other_bonuses = {ability: 0 for ability in self.ability_names}
        
        # Check for other modifier sources
        modifiers = raw_data.get('modifiers', {})
        
        for source_type, modifier_list in modifiers.items():
            if source_type in ['race', 'feat', 'item', 'class']:
                continue  # Already handled in dedicated methods
                
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_ability_score_modifier(modifier):
                    ability_name, bonus = self._extract_ability_modifier(modifier)
                    if ability_name:
                        other_bonuses[ability_name] += bonus
                        self.logger.debug(f"Other bonus {ability_name}: +{bonus} (source: {source_type})")
        
        return other_bonuses
    
    def _is_ability_score_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects ability scores."""
        modifies_id = modifier.get('modifiesId')
        modifies_type_id = modifier.get('modifiesTypeId')
        sub_type = modifier.get('subType', '')
        
        # Method 1: Traditional ability score modifiers
        if modifies_type_id == 1 and modifies_id in self.ability_id_map:
            return True
            
        # Method 2: New format with subType ending in "-score"
        if sub_type.endswith('-score'):
            ability_name = sub_type.replace('-score', '').replace('-', '_')
            return ability_name in self.ability_names
            
        return False
    
    def _extract_ability_modifier(self, modifier: Dict[str, Any]) -> Tuple[Optional[str], int]:
        """Extract ability name and bonus from a modifier."""
        modifies_id = modifier.get('modifiesId')
        sub_type = modifier.get('subType', '')
        bonus = modifier.get('bonus', 0) or modifier.get('value', 0) or modifier.get('fixedValue', 0)
        modifier_type = modifier.get('type', '')
        
        # Method 1: Traditional format with modifiesId
        if modifies_id in self.ability_id_map:
            ability_name = self.ability_id_map[modifies_id]
            
            # Handle "set" type modifiers
            if modifier_type == 'set':
                return ability_name, -999999 + bonus  # Special encoding
            else:
                return ability_name, bonus
            
        # Method 2: New format with subType ending in "-score"
        if sub_type.endswith('-score'):
            ability_name = sub_type.replace('-score', '').replace('-', '_')
            if ability_name in self.ability_names:
                if modifier_type == 'set':
                    return ability_name, -999999 + bonus  # Special encoding
                else:
                    return ability_name, bonus
        
        return None, 0
    
    def _is_asi_choice(self, choice: Dict[str, Any]) -> bool:
        """Check if a choice is an ASI selection."""
        choice_id = choice.get('choiceId')
        return choice_id in self.choice_mappings
    
    def _extract_asi_choice(self, choice: Dict[str, Any]) -> Tuple[Optional[str], int]:
        """Extract ability name and bonus from an ASI choice."""
        choice_id = choice.get('choiceId')
        
        if choice_id in self.choice_mappings:
            ability_name = self.choice_mappings[choice_id]
            bonus = 1  # ASI choices are typically +1
            return ability_name, bonus
        
        return None, 0
    
    def _is_2024_racial_asi_choice(self, choice: Dict[str, Any]) -> bool:
        """Check if a choice is a 2024 racial ASI selection."""
        label = choice.get('label') or ''
        return 'Ability Score' in label and ('increase by' in label or 'Increase by' in label)
    
    def _extract_2024_racial_asi_choice(self, choice: Dict[str, Any], raw_data: Dict[str, Any]) -> Tuple[Optional[str], int]:
        """Extract ability name and bonus from a 2024 racial ASI choice."""
        option_value = choice.get('optionValue')
        label = choice.get('label') or ''
        
        # Determine bonus amount from the choice label
        if 'increase by 2' in label.lower():
            bonus = 2
        elif 'increase by 1' in label.lower():
            bonus = 1
        else:
            bonus = 1  # Default
        
        # Look up the option value in choice definitions
        choice_definitions = raw_data.get('choices', {}).get('choiceDefinitions', [])
        
        for choice_def in choice_definitions:
            if not isinstance(choice_def, dict):
                continue
                
            options = choice_def.get('options', [])
            for option in options:
                if not isinstance(option, dict):
                    continue
                    
                if option.get('id') == option_value:
                    option_label = option.get('label', '')
                    
                    # Extract ability name from label
                    ability_name = None
                    for ability in self.ability_names:
                        if ability.lower() in option_label.lower():
                            ability_name = ability
                            break
                    
                    if ability_name:
                        self.logger.debug(f"Resolved 2024 ASI choice: {ability_name} +{bonus}")
                        return ability_name, bonus
        
        self.logger.warning(f"Could not resolve 2024 ASI choice: {label}")
        return None, 0
    
    def _has_2024_racial_asi_choices(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character has 2024-style racial ASI choices."""
        choices = raw_data.get('choices', {})
        
        for source_type, choice_list in choices.items():
            if not isinstance(choice_list, list):
                continue
                
            for choice in choice_list:
                if self._is_2024_racial_asi_choice(choice):
                    return True
        
        return False
    
    def _get_save_proficiencies(self, raw_data: Dict[str, Any]) -> List[str]:
        """Get list of saving throw proficiencies."""
        save_proficiencies = []
        
        # Check class proficiencies
        classes = raw_data.get('classes', [])
        for class_data in classes:
            class_def = class_data.get('definition', {})
            saving_throws = class_def.get('savingThrows', [])
            
            for save_throw in saving_throws:
                save_id = save_throw.get('id')
                if save_id in self.ability_id_map:
                    ability_name = self.ability_id_map[save_id]
                    if ability_name not in save_proficiencies:
                        save_proficiencies.append(ability_name)
        
        return save_proficiencies
    
    def _calculate_save_bonus(self, ability: str, modifier: int, raw_data: Dict[str, Any], proficiency_bonus: int) -> int:
        """Calculate saving throw bonus including proficiency if applicable."""
        save_proficiencies = self._get_save_proficiencies(raw_data)
        
        if ability in save_proficiencies:
            return modifier + proficiency_bonus
        else:
            return modifier
    
    def _create_simple_breakdown(self, breakdown: Dict[str, Any]) -> Dict[str, Any]:
        """Create simplified breakdown format for compatibility."""
        simple_breakdown = {}
        
        if breakdown.get('base', 0) != 0:
            simple_breakdown['base'] = breakdown['base']
        if breakdown.get('racial', 0) != 0:
            simple_breakdown['race'] = breakdown['racial']
        if breakdown.get('feat', 0) != 0:
            simple_breakdown['feat'] = breakdown['feat']
        if breakdown.get('asi', 0) != 0:
            simple_breakdown['asi'] = breakdown['asi']
        if breakdown.get('item', 0) != 0:
            simple_breakdown['item'] = breakdown['item']
        if breakdown.get('other', 0) != 0:
            simple_breakdown['other'] = breakdown['other']
        
        # If we still don't have a breakdown, provide fallback
        if not simple_breakdown:
            simple_breakdown['base'] = breakdown.get('total', 10)
        
        return simple_breakdown
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate that the input data is suitable for this coordinator.
        
        Args:
            raw_data: Raw character data to validate
            
        Returns:
            True if data is valid for this coordinator
        """
        return self._validate_ability_data(raw_data)
    
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
                "ability_scores": {
                    "type": "object",
                    "properties": {
                        ability: {
                            "type": "object",
                            "properties": {
                                "score": {"type": "integer", "minimum": 1, "maximum": 30},
                                "modifier": {"type": "integer", "minimum": -5, "maximum": 10},
                                "save_bonus": {"type": "integer"},
                                "source_breakdown": {"type": "object"}
                            },
                            "required": ["score", "modifier", "save_bonus", "source_breakdown"]
                        } for ability in self.ability_names
                    }
                },
                "ability_modifiers": {
                    "type": "object",
                    "properties": {
                        ability: {"type": "integer", "minimum": -5, "maximum": 10}
                        for ability in self.ability_names
                    }
                },
                "ability_score_breakdown": {"type": "object"},
                "save_proficiencies": {
                    "type": "array",
                    "items": {"type": "string"}
                },
                "proficiency_bonus": {"type": "integer", "minimum": 2, "maximum": 6},
                "calculation_method": {"type": "string"},
                "metadata": {"type": "object"}
            },
            "required": [
                "ability_scores", "ability_modifiers", "ability_score_breakdown",
                "save_proficiencies", "proficiency_bonus", "calculation_method"
            ]
        }