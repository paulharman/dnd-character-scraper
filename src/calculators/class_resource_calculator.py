"""
Class Resource Calculator

Calculates class-specific resources like Ki points, Sorcery points, Bardic Inspiration,
Rage uses, Channel Divinity, and other class features with usage tracking.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from src.calculators.base import RuleAwareCalculator

class RestType(Enum):
    """Types of rests that restore resources."""
    SHORT_REST = "short_rest"
    LONG_REST = "long_rest"
    NONE = "none"  # Resources that don't restore on rest

@dataclass
class ClassResource:
    """Represents a calculated class resource with usage tracking."""
    resource_name: str
    class_name: str
    maximum: int
    current: int
    used: int
    recharge_on: RestType
    level_based: bool
    ability_based: bool
    ability_name: Optional[str] = None
    ability_modifier: int = 0
    per_level_amount: int = 0
    base_amount: int = 0
    bonus_amount: int = 0
    description: str = ""
    breakdown: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def remaining(self) -> int:
        """Get remaining uses of this resource."""
        return max(0, self.maximum - self.used)
    
    @property
    def is_depleted(self) -> bool:
        """Check if resource is completely used up."""
        return self.remaining <= 0
    
    @property
    def usage_fraction(self) -> str:
        """Get usage as a fraction string."""
        return f"{self.remaining}/{self.maximum}"

class ClassResourceCalculator(RuleAwareCalculator):
    """Calculator for class-specific resources with D&D 5e rules."""
    
    # Class resource definitions
    CLASS_RESOURCES = {
        'monk': {
            'ki_points': {
                'level_based': True,
                'per_level': 1,
                'min_level': 2,
                'recharge_on': RestType.SHORT_REST,
                'description': 'Ki points for martial arts abilities'
            }
        },
        'sorcerer': {
            'sorcery_points': {
                'level_based': True,
                'per_level': 1,
                'min_level': 2,
                'recharge_on': RestType.LONG_REST,
                'description': 'Sorcery points for metamagic and spell slots'
            }
        },
        'bard': {
            'bardic_inspiration': {
                'ability_based': True,
                'ability': 'charisma',
                'min_level': 1,
                'recharge_on': RestType.SHORT_REST,
                'description': 'Bardic Inspiration dice to inspire allies'
            }
        },
        'barbarian': {
            'rage': {
                'level_based': True,
                'uses_per_level': {
                    1: 2, 3: 3, 6: 4, 12: 5, 17: 6, 20: 999  # Unlimited at 20
                },
                'recharge_on': RestType.LONG_REST,
                'description': 'Rage uses for enhanced combat'
            }
        },
        'cleric': {
            'channel_divinity': {
                'level_based': True,
                'uses_per_level': {
                    2: 1, 6: 2, 18: 3
                },
                'recharge_on': RestType.SHORT_REST,
                'description': 'Channel Divinity for divine abilities'
            }
        },
        'paladin': {
            'channel_divinity': {
                'level_based': True,
                'uses_per_level': {
                    3: 1, 7: 2, 15: 3
                },
                'recharge_on': RestType.SHORT_REST,
                'description': 'Channel Divinity for divine abilities'
            }
        },
        'druid': {
            'wild_shape': {
                'level_based': True,
                'uses_per_level': {
                    2: 2, 20: 999  # Unlimited at 20
                },
                'recharge_on': RestType.SHORT_REST,
                'description': 'Wild Shape uses to transform into beasts'
            }
        },
        'fighter': {
            'action_surge': {
                'level_based': True,
                'uses_per_level': {
                    2: 1, 17: 2
                },
                'recharge_on': RestType.SHORT_REST,
                'description': 'Action Surge for extra actions'
            },
            'second_wind': {
                'level_based': True,
                'uses_per_level': {
                    1: 1
                },
                'recharge_on': RestType.SHORT_REST,
                'description': 'Second Wind for healing'
            }
        },
        'warlock': {
            'spell_slots': {
                'level_based': True,
                'uses_per_level': {
                    1: 1, 2: 2, 11: 3, 17: 4
                },
                'recharge_on': RestType.SHORT_REST,
                'description': 'Warlock spell slots (Pact Magic)'
            }
        }
    }
    
    def __init__(self, config_manager=None, rule_manager=None):
        """Initialize the class resource calculator."""
        super().__init__(config_manager, rule_manager)
    
    def calculate(self, character_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate class resources for all character classes.
        
        Args:
            character_data: Character data dictionary
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with class resource calculations
        """
        if not character_data:
            return {'class_resources': [], 'errors': ['No character data provided']}
        
        errors = []
        warnings = []
        
        try:
            # Detect rule version
            rule_version = self._detect_rule_version(character_data)
            
            # Get required data with fallbacks
            classes = character_data.get('classes', [])
            abilities = character_data.get('abilities', {})
            ability_scores = abilities.get('ability_scores', {})
            character_info = character_data.get('character_info', {})
            
            # Validate basic data
            if not classes:
                warnings.append("No classes found for character")
                return {
                    'class_resources': [],
                    'rule_version': rule_version,
                    'warnings': warnings
                }
            
            if not ability_scores:
                warnings.append("No ability scores found, using defaults for ability-based resources")
                ability_scores = self._get_default_ability_scores()
            
            # Calculate resources for each class
            class_resources = []
            for class_data in classes:
                try:
                    class_name = class_data.get('name', '').lower()
                    class_level = class_data.get('level', 1)
                    
                    # Validate class level
                    if class_level < 1 or class_level > 20:
                        warnings.append(f"Unusual class level for {class_name}: {class_level}, clamping to valid range")
                        class_level = max(1, min(20, class_level))
                    
                    if class_name in self.CLASS_RESOURCES:
                        resources = self._calculate_class_resources(
                            class_name=class_name,
                            class_level=class_level,
                            ability_scores=ability_scores,
                            character_data=character_data,
                            rule_version=rule_version
                        )
                        class_resources.extend(resources)
                    else:
                        # Not an error - just means this class doesn't have tracked resources
                        pass
                except Exception as e:
                    class_name = class_data.get('name', 'Unknown Class')
                    errors.append(f"Failed to calculate resources for {class_name}: {str(e)}")
            
            result = {
                'class_resources': class_resources,
                'rule_version': rule_version
            }
            
            if errors:
                result['errors'] = errors
            if warnings:
                result['warnings'] = warnings
                
            return result
            
        except Exception as e:
            return {
                'class_resources': [],
                'rule_version': '2014',
                'errors': [f"Critical error in class resource calculation: {str(e)}"]
            }
    
    def _get_default_ability_scores(self) -> Dict[str, Any]:
        """Get default ability scores when none are provided."""
        return {
            'strength': {'score': 10, 'modifier': 0},
            'dexterity': {'score': 10, 'modifier': 0},
            'constitution': {'score': 10, 'modifier': 0},
            'intelligence': {'score': 10, 'modifier': 0},
            'wisdom': {'score': 10, 'modifier': 0},
            'charisma': {'score': 10, 'modifier': 0}
        }
    
    def calculate_specific_resource(
        self,
        class_name: str,
        resource_name: str,
        character_data: Dict[str, Any],
        **kwargs
    ) -> Optional[ClassResource]:
        """
        Calculate a specific class resource.
        
        Args:
            class_name: Name of the class
            resource_name: Name of the resource
            character_data: Character data dictionary
            **kwargs: Additional parameters
            
        Returns:
            ClassResource object or None if not found
        """
        class_name = class_name.lower()
        if class_name not in self.CLASS_RESOURCES:
            return None
        
        if resource_name not in self.CLASS_RESOURCES[class_name]:
            return None
        
        # Find the class level
        classes = character_data.get('classes', [])
        class_level = 1
        for class_data in classes:
            if class_data.get('name', '').lower() == class_name:
                class_level = class_data.get('level', 1)
                break
        
        abilities = character_data.get('abilities', {})
        ability_scores = abilities.get('ability_scores', {})
        
        return self._calculate_single_resource(
            class_name=class_name,
            resource_name=resource_name,
            class_level=class_level,
            ability_scores=ability_scores,
            character_data=character_data
        )
    
    def _calculate_class_resources(
        self,
        class_name: str,
        class_level: int,
        ability_scores: Dict[str, Any],
        character_data: Dict[str, Any],
        rule_version: str = "2014"
    ) -> List[ClassResource]:
        """Calculate all resources for a specific class."""
        resources = []
        
        class_resource_defs = self.CLASS_RESOURCES.get(class_name, {})
        for resource_name, resource_def in class_resource_defs.items():
            resource = self._calculate_single_resource(
                class_name=class_name,
                resource_name=resource_name,
                class_level=class_level,
                ability_scores=ability_scores,
                character_data=character_data
            )
            if resource:
                resources.append(resource)
        
        return resources
    
    def _calculate_single_resource(
        self,
        class_name: str,
        resource_name: str,
        class_level: int,
        ability_scores: Dict[str, Any],
        character_data: Dict[str, Any]
    ) -> Optional[ClassResource]:
        """Calculate a single class resource."""
        resource_def = self.CLASS_RESOURCES[class_name][resource_name]
        
        # Check minimum level requirement
        min_level = resource_def.get('min_level', 1)
        if class_level < min_level:
            return None
        
        # Calculate maximum uses
        maximum = self._calculate_resource_maximum(
            resource_def=resource_def,
            class_level=class_level,
            ability_scores=ability_scores
        )
        
        if maximum <= 0:
            return None
        
        # Get current usage (would come from character state)
        used = self._get_resource_usage(character_data, class_name, resource_name)
        current = maximum - used
        
        # Get ability information if ability-based
        ability_name = None
        ability_modifier = 0
        if resource_def.get('ability_based', False):
            ability_name = resource_def.get('ability', 'charisma')
            ability_modifier = self._get_ability_modifier(ability_scores.get(ability_name, {}))
        
        # Create breakdown
        breakdown = self._create_resource_breakdown(
            resource_def=resource_def,
            class_level=class_level,
            ability_modifier=ability_modifier,
            maximum=maximum
        )
        
        return ClassResource(
            resource_name=resource_name.replace('_', ' ').title(),
            class_name=class_name.title(),
            maximum=maximum,
            current=current,
            used=used,
            recharge_on=resource_def.get('recharge_on', RestType.LONG_REST),
            level_based=resource_def.get('level_based', False),
            ability_based=resource_def.get('ability_based', False),
            ability_name=ability_name,
            ability_modifier=ability_modifier,
            per_level_amount=resource_def.get('per_level', 0),
            base_amount=resource_def.get('base_amount', 0),
            bonus_amount=0,  # Could be enhanced for magic items
            description=resource_def.get('description', ''),
            breakdown=breakdown
        )
    
    def _calculate_resource_maximum(
        self,
        resource_def: Dict[str, Any],
        class_level: int,
        ability_scores: Dict[str, Any]
    ) -> int:
        """Calculate the maximum uses of a resource."""
        maximum = 0
        
        # Level-based resources
        if resource_def.get('level_based', False):
            if 'uses_per_level' in resource_def:
                # Lookup table based on level
                uses_per_level = resource_def['uses_per_level']
                for level_threshold in sorted(uses_per_level.keys(), reverse=True):
                    if class_level >= level_threshold:
                        maximum = uses_per_level[level_threshold]
                        break
            elif 'per_level' in resource_def:
                # Simple per-level calculation
                per_level = resource_def['per_level']
                min_level = resource_def.get('min_level', 1)
                if class_level >= min_level:
                    maximum = (class_level - min_level + 1) * per_level
        
        # Ability-based resources
        if resource_def.get('ability_based', False):
            ability_name = resource_def.get('ability', 'charisma')
            ability_modifier = self._get_ability_modifier(ability_scores.get(ability_name, {}))
            
            # Minimum 1 use even with negative modifier
            maximum = max(1, ability_modifier)
            
            # Some resources get bonus uses at higher levels
            if 'bonus_per_level' in resource_def:
                bonus_levels = resource_def['bonus_per_level']
                for level_threshold, bonus in bonus_levels.items():
                    if class_level >= level_threshold:
                        maximum += bonus
        
        # Base amount (fixed number)
        if 'base_amount' in resource_def:
            maximum += resource_def['base_amount']
        
        return maximum
    
    def _get_resource_usage(self, character_data: Dict[str, Any], class_name: str, resource_name: str) -> int:
        """Get current usage of a resource from character data."""
        # This would typically come from character state/save data
        # For now, return 0 (unused)
        resource_usage = character_data.get('resource_usage', {})
        class_usage = resource_usage.get(class_name, {})
        return class_usage.get(resource_name, 0)
    
    def _get_ability_modifier(self, ability: Dict[str, Any]) -> int:
        """Get ability modifier from ability score."""
        if not ability:
            return 0
        
        # Check if modifier is directly provided
        if 'modifier' in ability:
            return ability.get('modifier', 0)
        
        # Calculate from score
        score = ability.get('score', 10)
        return (score - 10) // 2
    
    def _create_resource_breakdown(
        self,
        resource_def: Dict[str, Any],
        class_level: int,
        ability_modifier: int,
        maximum: int
    ) -> Dict[str, Any]:
        """Create a breakdown of how the resource maximum was calculated."""
        breakdown = {
            'class_level': class_level,
            'maximum': maximum,
            'calculation_method': []
        }
        
        if resource_def.get('level_based', False):
            if 'uses_per_level' in resource_def:
                breakdown['calculation_method'].append('level_lookup_table')
            elif 'per_level' in resource_def:
                per_level = resource_def['per_level']
                min_level = resource_def.get('min_level', 1)
                breakdown['calculation_method'].append(f'{per_level}_per_level_from_{min_level}')
        
        if resource_def.get('ability_based', False):
            ability_name = resource_def.get('ability', 'charisma')
            breakdown['ability_name'] = ability_name
            breakdown['ability_modifier'] = ability_modifier
            breakdown['calculation_method'].append(f'{ability_name}_modifier')
        
        if 'base_amount' in resource_def:
            breakdown['base_amount'] = resource_def['base_amount']
            breakdown['calculation_method'].append('base_amount')
        
        return breakdown
    
    def get_resources_by_class(self, class_name: str) -> List[str]:
        """Get all resource names for a specific class."""
        class_name = class_name.lower()
        if class_name in self.CLASS_RESOURCES:
            return list(self.CLASS_RESOURCES[class_name].keys())
        return []
    
    def get_resources_by_rest_type(self, rest_type: RestType) -> Dict[str, List[str]]:
        """Get all resources that recharge on a specific rest type."""
        resources_by_class = {}
        
        for class_name, class_resources in self.CLASS_RESOURCES.items():
            matching_resources = []
            for resource_name, resource_def in class_resources.items():
                if resource_def.get('recharge_on') == rest_type:
                    matching_resources.append(resource_name)
            
            if matching_resources:
                resources_by_class[class_name] = matching_resources
        
        return resources_by_class
    
    def simulate_rest(
        self,
        character_data: Dict[str, Any],
        rest_type: RestType
    ) -> Dict[str, Any]:
        """
        Simulate taking a rest and restore appropriate resources.
        
        Args:
            character_data: Character data dictionary
            rest_type: Type of rest taken
            
        Returns:
            Updated character data with restored resources
        """
        # Calculate current resources
        result = self.calculate(character_data)
        class_resources = result.get('class_resources', [])
        
        # Restore resources that recharge on this rest type
        restored_resources = []
        for resource in class_resources:
            if resource.recharge_on == rest_type or (rest_type == RestType.LONG_REST and resource.recharge_on == RestType.SHORT_REST):
                # Restore to maximum
                resource.used = 0
                resource.current = resource.maximum
                restored_resources.append(resource.resource_name)
        
        return {
            'class_resources': class_resources,
            'restored_resources': restored_resources,
            'rest_type': rest_type.value
        }
    
    def _detect_rule_version(self, character_data: Dict[str, Any]) -> str:
        """
        Detect rule version from character data.
        
        Args:
            character_data: Character data dictionary
            
        Returns:
            Rule version string ("2014" or "2024")
        """
        # Use rule manager if available
        if self.rule_manager:
            try:
                character_id = character_data.get('character_info', {}).get('character_id', 0)
                detection_result = self.rule_manager.detect_rule_version(character_data, character_id)
                return detection_result.version.value
            except Exception:
                pass
        
        # Fallback detection logic
        character_info = character_data.get('character_info', {})
        
        # Check for explicit rule version
        if 'rule_version' in character_info:
            version = character_info['rule_version']
            if version in ['2024', 'onedd']:
                return '2024'
        
        # Check for 2024 indicators in sources
        sources = character_data.get('sources', [])
        for source in sources:
            if isinstance(source, dict):
                source_name = source.get('name', '').lower()
                if '2024' in source_name or 'one d&d' in source_name:
                    return '2024'
        
        # Default to 2014
        return '2014'