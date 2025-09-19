"""
Enhanced Attack Calculator with new interface compliance.

This module provides an enhanced implementation of the attack calculator
that implements the new calculator interfaces and provides improved functionality.
"""

import logging
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import time

from .interfaces.core import (
    ICalculator, IRuleAwareCalculator, ICachedCalculator, 
    CalculatorType, CalculationError, ValidationError, CalculatorConfig
)
from .services.interfaces import CalculationContext, CalculationResult, CalculationStatus
from .utils.math import DnDMath, MathUtils, DiceRoll
from .utils.validation import CharacterDataValidator
from .base import RuleAwareCalculator
from ..rules.version_manager import RuleVersionManager


logger = logging.getLogger(__name__)


@dataclass
class AttackData:
    """Data class for individual attack information."""
    name: str
    attack_bonus: int
    damage_roll: str
    damage_bonus: int
    damage_type: str
    attack_type: str  # melee, ranged, spell
    weapon_type: str  # simple, martial, natural
    proficient: bool
    ability_modifier: str
    range_normal: int
    range_long: int
    versatile: bool
    versatile_damage: str
    properties: List[str]
    
    def __post_init__(self):
        if self.attack_type not in ['melee', 'ranged', 'spell']:
            raise ValueError(f"Invalid attack type: {self.attack_type}")
        if self.range_normal < 0:
            raise ValueError(f"Range cannot be negative: {self.range_normal}")


@dataclass
class AttackCalculationData:
    """Data class for comprehensive attack calculation information."""
    attacks: List[AttackData]
    spell_attacks: List[AttackData]
    natural_attacks: List[AttackData]
    extra_attacks: int
    fighting_styles: List[str]
    attack_modifiers: Dict[str, int]
    damage_modifiers: Dict[str, int]
    critical_range: int
    
    def __post_init__(self):
        if self.extra_attacks < 0:
            raise ValueError(f"Extra attacks cannot be negative: {self.extra_attacks}")
        if self.critical_range < 19 or self.critical_range > 20:
            raise ValueError(f"Critical range must be 19 or 20: {self.critical_range}")


class EnhancedAttackCalculator(RuleAwareCalculator, ICachedCalculator):
    """
    Enhanced attack calculator with new interface compliance.
    
    Features:
    - Full interface compliance with ICalculator, IRuleAwareCalculator, ICachedCalculator
    - Comprehensive attack and damage calculation
    - Weapon, spell, and natural attack support
    - Enhanced validation and error handling
    - Performance monitoring and caching
    - Rule version support for attack calculation differences
    """
    
    def __init__(self, config_manager=None, rule_manager: Optional[RuleVersionManager] = None):
        """
        Initialize the enhanced attack calculator.
        
        Args:
            config_manager: Configuration manager instance
            rule_manager: Rule version manager instance
        """
        super().__init__(config_manager, rule_manager)
        # Load configuration from main config system (uses performance.enable_caching)
        self.config = self.create_calculator_config_from_main(config_manager)
        self.validator = CharacterDataValidator()
        self.cache = {}
        self.cache_stats = {'hits': 0, 'misses': 0}
        
        # Initialize attack constants
        self._setup_attack_constants()
        
        # Performance tracking
        self.metrics = {
            'total_calculations': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0
        }
    
    def _setup_attack_constants(self):
        """Setup attack calculation constants."""
        # Weapon properties
        self.weapon_properties = {
            'light': 'Can be used for two-weapon fighting',
            'finesse': 'Can use DEX instead of STR for attack and damage',
            'thrown': 'Can be thrown as ranged weapon',
            'two_handed': 'Requires two hands to use',
            'versatile': 'Can be used one or two-handed',
            'reach': 'Adds 5 feet to reach',
            'heavy': 'Small creatures have disadvantage',
            'loading': 'Can only fire one piece of ammunition per action',
            'ammunition': 'Requires ammunition to make ranged attacks'
        }
        
        # Fighting styles that affect attacks
        self.fighting_styles = {
            'archery': {'type': 'ranged', 'attack_bonus': 2},
            'dueling': {'type': 'melee', 'damage_bonus': 2, 'condition': 'one_handed'},
            'great_weapon_fighting': {'type': 'melee', 'reroll_dice': [1, 2]},
            'two_weapon_fighting': {'type': 'melee', 'offhand_damage_bonus': True},
            'defense': {'type': 'defensive', 'ac_bonus': 1},
            'protection': {'type': 'defensive', 'reaction_shield': True}
        }
        
        # Ability ID mappings
        self.ability_id_map = {
            1: 'strength',
            2: 'dexterity', 
            3: 'constitution',
            4: 'intelligence',
            5: 'wisdom',
            6: 'charisma'
        }
        
        # Weapon categories
        self.simple_weapons = [
            'club', 'dagger', 'dart', 'javelin', 'mace', 'staff', 'crossbow_light',
            'shortbow', 'sling', 'handaxe', 'light_hammer', 'spear'
        ]
        
        self.martial_weapons = [
            'battleaxe', 'flail', 'glaive', 'greataxe', 'greatsword', 'halberd',
            'lance', 'longsword', 'maul', 'morningstar', 'pike', 'rapier',
            'scimitar', 'shortsword', 'trident', 'war_pick', 'warhammer',
            'whip', 'blowgun', 'crossbow_hand', 'crossbow_heavy', 'longbow', 'net'
        ]
    
    # ICalculator interface implementation
    @property
    def calculator_type(self) -> CalculatorType:
        """Get the type of this calculator."""
        return CalculatorType.ATTACK
    
    @property
    def name(self) -> str:
        """Get the human-readable name of this calculator."""
        return "Enhanced Attack Calculator"
    
    @property
    def version(self) -> str:
        """Get the version of this calculator."""
        return "2.0.0"
    
    @property
    def dependencies(self) -> List[CalculatorType]:
        """Get the list of calculator types this calculator depends on."""
        return [CalculatorType.ABILITY_SCORE, CalculatorType.PROFICIENCY]  # Needs ability scores and proficiency
    
    def calculate(self, character_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Perform the calculation using the provided character data.
        
        Args:
            character_data: Raw character data from D&D Beyond
            context: Calculation context and configuration
            
        Returns:
            CalculationResult with computed data and metadata
        """
        start_time = time.time()
        self.metrics['total_calculations'] += 1
        
        try:
            # Validate input data
            is_valid, validation_errors = self.validate_input(character_data)
            if not is_valid:
                self.metrics['validation_failures'] += 1
                return CalculationResult(
                    service_name=self.name,
                    status=CalculationStatus.FAILED,
                    data={},
                    errors=validation_errors,
                    execution_time=time.time() - start_time
                )
            
            # Check cache
            cache_key = self.get_cache_key(character_data, context)
            if self.config.enable_caching:
                cached_result = self.get_from_cache(cache_key)
                if cached_result:
                    self.metrics['cache_hits'] += 1
                    self.cache_stats['hits'] += 1
                    return cached_result
            
            self.metrics['cache_misses'] += 1
            self.cache_stats['misses'] += 1
            
            # Perform calculation
            rule_version = self.get_rule_version(character_data)
            logger.debug(f"Calculating attacks with {rule_version.version.value} rules")
            
            # Calculate attacks
            attack_data = self._calculate_attacks(character_data, rule_version)
            
            # Build result
            result_data = {
                'attacks': [{
                    'name': attack.name,
                    'attack_bonus': attack.attack_bonus,
                    'damage_roll': attack.damage_roll,
                    'damage_bonus': attack.damage_bonus,
                    'damage_type': attack.damage_type,
                    'attack_type': attack.attack_type,
                    'weapon_type': attack.weapon_type,
                    'proficient': attack.proficient,
                    'ability_modifier': attack.ability_modifier,
                    'range_normal': attack.range_normal,
                    'range_long': attack.range_long,
                    'versatile': attack.versatile,
                    'versatile_damage': attack.versatile_damage,
                    'properties': attack.properties
                } for attack in attack_data.attacks],
                'spell_attacks': [{
                    'name': attack.name,
                    'attack_bonus': attack.attack_bonus,
                    'damage_roll': attack.damage_roll,
                    'damage_bonus': attack.damage_bonus,
                    'damage_type': attack.damage_type,
                    'attack_type': attack.attack_type,
                    'range_normal': attack.range_normal,
                    'range_long': attack.range_long
                } for attack in attack_data.spell_attacks],
                'natural_attacks': [{
                    'name': attack.name,
                    'attack_bonus': attack.attack_bonus,
                    'damage_roll': attack.damage_roll,
                    'damage_bonus': attack.damage_bonus,
                    'damage_type': attack.damage_type
                } for attack in attack_data.natural_attacks],
                'extra_attacks': attack_data.extra_attacks,
                'fighting_styles': attack_data.fighting_styles,
                'attack_modifiers': attack_data.attack_modifiers,
                'damage_modifiers': attack_data.damage_modifiers,
                'critical_range': attack_data.critical_range,
                'rule_version': rule_version.version.value
            }
            
            result = CalculationResult(
                service_name=self.name,
                status=CalculationStatus.COMPLETED,
                data=result_data,
                execution_time=time.time() - start_time
            )
            
            # Cache result
            if self.config.enable_caching:
                self.store_in_cache(cache_key, result)
            
            # Update metrics
            self.metrics['total_time'] += result.execution_time
            
            return result
            
        except Exception as e:
            logger.error(f"Error in attack calculation: {str(e)}")
            return CalculationResult(
                service_name=self.name,
                status=CalculationStatus.FAILED,
                data={},
                errors=[str(e)],
                execution_time=time.time() - start_time
            )
    
    def validate_input(self, character_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate that the input data is suitable for this calculator.
        
        Args:
            character_data: Character data to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check basic structure
        if not isinstance(character_data, dict):
            errors.append("Character data must be a dictionary")
            return False, errors
        
        # Check for stats (needed for ability modifiers)
        if 'stats' not in character_data:
            errors.append("Missing required 'stats' field for attack calculation")
        else:
            stats = character_data['stats']
            if not isinstance(stats, list):
                errors.append("'stats' field must be a list")
        
        # Check for classes (needed for proficiency bonus)
        if 'classes' not in character_data:
            errors.append("Missing required 'classes' field for proficiency calculation")
        else:
            classes = character_data['classes']
            if not isinstance(classes, list):
                errors.append("'classes' field must be a list")
        
        # Use validator for additional checks
        validation_result = self.validator.validate(character_data)
        if not validation_result.is_valid:
            errors.extend([msg.message for msg in validation_result.messages])
        
        return len(errors) == 0, errors
    
    def get_output_schema(self) -> Dict[str, Any]:
        """
        Get the schema for data this calculator produces.
        
        Returns:
            JSONSchema describing the output data structure
        """
        attack_schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "attack_bonus": {"type": "integer"},
                "damage_roll": {"type": "string"},
                "damage_bonus": {"type": "integer"},
                "damage_type": {"type": "string"},
                "attack_type": {"type": "string", "enum": ["melee", "ranged", "spell"]},
                "weapon_type": {"type": "string"},
                "proficient": {"type": "boolean"},
                "ability_modifier": {"type": "string"},
                "range_normal": {"type": "integer"},
                "range_long": {"type": "integer"},
                "versatile": {"type": "boolean"},
                "versatile_damage": {"type": "string"},
                "properties": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["name", "attack_bonus", "damage_roll", "damage_bonus", "damage_type", "attack_type"]
        }
        
        return {
            "type": "object",
            "properties": {
                "attacks": {"type": "array", "items": attack_schema},
                "spell_attacks": {"type": "array", "items": attack_schema},
                "natural_attacks": {"type": "array", "items": attack_schema},
                "extra_attacks": {"type": "integer", "minimum": 0},
                "fighting_styles": {"type": "array", "items": {"type": "string"}},
                "attack_modifiers": {"type": "object"},
                "damage_modifiers": {"type": "object"},
                "critical_range": {"type": "integer", "minimum": 19, "maximum": 20},
                "rule_version": {"type": "string", "enum": ["2014", "2024"]}
            },
            "required": ["attacks", "spell_attacks", "natural_attacks", "extra_attacks", "fighting_styles", "attack_modifiers", "damage_modifiers", "critical_range", "rule_version"]
        }
    
    def get_required_fields(self) -> List[str]:
        """
        Get the list of required fields in the input data.
        
        Returns:
            List of required field names
        """
        return ['stats', 'classes']
    
    def get_optional_fields(self) -> List[str]:
        """
        Get the list of optional fields in the input data.
        
        Returns:
            List of optional field names
        """
        return ['inventory', 'spells', 'modifiers', 'feats', 'actions']
    
    def supports_rule_version(self, rule_version: str) -> bool:
        """
        Check if this calculator supports the specified rule version.
        
        Args:
            rule_version: Rule version to check (e.g., "2014", "2024")
            
        Returns:
            True if rule version is supported
        """
        return rule_version in ["2014", "2024"]
    
    def get_cache_key(self, character_data: Dict[str, Any], context: CalculationContext) -> str:
        """
        Generate a cache key for the given inputs.
        
        Args:
            character_data: Character data
            context: Calculation context
            
        Returns:
            Cache key string
        """
        import hashlib
        import json
        
        # Extract relevant fields for caching
        cache_data = {
            'stats': character_data.get('stats', []),
            'classes': character_data.get('classes', []),
            'inventory': character_data.get('inventory', []),
            'spells': character_data.get('spells', []),
            'modifiers': character_data.get('modifiers', {}),
            'feats': character_data.get('feats', []),
            'rule_version': context.rule_version,
            'character_id': context.character_id
        }
        
        # Sort keys for consistent hashing
        cache_json = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_json.encode()).hexdigest()
        
        return f"attack_{cache_hash}"
    
    # ICachedCalculator interface implementation
    def get_from_cache(self, cache_key: str) -> Optional[CalculationResult]:
        """Get calculation result from cache."""
        return self.cache.get(cache_key)
    
    def store_in_cache(self, cache_key: str, result: CalculationResult, ttl: Optional[int] = None) -> None:
        """Store calculation result in cache."""
        self.cache[cache_key] = result
        
        # Simple cache size management
        if len(self.cache) > 1000:
            keys_to_remove = list(self.cache.keys())[:100]
            for key in keys_to_remove:
                del self.cache[key]
    
    def invalidate_cache(self, cache_key: str) -> None:
        """Invalidate cached result."""
        if cache_key in self.cache:
            del self.cache[cache_key]
    
    def clear_cache(self) -> None:
        """Clear all cached results for this calculator."""
        self.cache.clear()
        self.cache_stats = {'hits': 0, 'misses': 0}
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return {
            'hits': self.cache_stats['hits'],
            'misses': self.cache_stats['misses'],
            'hit_rate': self.cache_stats['hits'] / (self.cache_stats['hits'] + self.cache_stats['misses']) if (self.cache_stats['hits'] + self.cache_stats['misses']) > 0 else 0,
            'cache_size': len(self.cache)
        }
    
    def configure(self, config: CalculatorConfig) -> None:
        """Configure calculator behavior."""
        self.config = config
        self.validator = CharacterDataValidator()
    
    def get_configuration(self) -> CalculatorConfig:
        """Get current calculator configuration."""
        return self.config
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this calculator."""
        return {
            'total_calculations': self.metrics['total_calculations'],
            'total_time': self.metrics['total_time'],
            'average_time': self.metrics['total_time'] / self.metrics['total_calculations'] if self.metrics['total_calculations'] > 0 else 0,
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses'],
            'validation_failures': self.metrics['validation_failures']
        }
    
    def reset_metrics(self) -> None:
        """Reset performance metrics."""
        self.metrics = {
            'total_calculations': 0,
            'total_time': 0.0,
            'cache_hits': 0,
            'cache_misses': 0,
            'validation_failures': 0
        }
    
    # Core calculation methods
    def _calculate_attacks(self, character_data: Dict[str, Any], rule_version) -> AttackCalculationData:
        """
        Calculate attacks with comprehensive breakdown.
        
        Args:
            character_data: Character data from D&D Beyond
            rule_version: Detected rule version
            
        Returns:
            AttackCalculationData object with complete breakdown
        """
        # Get basic data
        proficiency_bonus = self._get_proficiency_bonus(character_data)
        ability_modifiers = self._get_ability_modifiers(character_data)
        
        # Get weapon attacks
        weapon_attacks = self._calculate_weapon_attacks(character_data, ability_modifiers, proficiency_bonus)
        
        # Get spell attacks
        spell_attacks = self._calculate_spell_attacks(character_data, ability_modifiers, proficiency_bonus)
        
        # Get natural attacks
        natural_attacks = self._calculate_natural_attacks(character_data, ability_modifiers, proficiency_bonus)
        
        # Calculate extra attacks
        extra_attacks = self._calculate_extra_attacks(character_data)
        
        # Get fighting styles
        fighting_styles = self._get_fighting_styles(character_data)
        
        # Get modifiers
        attack_modifiers = self._get_attack_modifiers(character_data)
        damage_modifiers = self._get_damage_modifiers(character_data)
        
        # Get critical range
        critical_range = self._get_critical_range(character_data)
        
        return AttackCalculationData(
            attacks=weapon_attacks,
            spell_attacks=spell_attacks,
            natural_attacks=natural_attacks,
            extra_attacks=extra_attacks,
            fighting_styles=fighting_styles,
            attack_modifiers=attack_modifiers,
            damage_modifiers=damage_modifiers,
            critical_range=critical_range
        )
    
    def _get_proficiency_bonus(self, character_data: Dict[str, Any]) -> int:
        """Get character's proficiency bonus based on level."""
        classes = character_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes) or 1
        return DnDMath.proficiency_bonus(total_level)
    
    def _get_ability_modifiers(self, character_data: Dict[str, Any]) -> Dict[str, int]:
        """Get all ability modifiers including bonuses from feats, backgrounds, etc."""
        ability_modifiers = {}

        for ability_name in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            effective_score = self._get_effective_ability_score(character_data, ability_name)
            ability_modifiers[ability_name] = DnDMath.ability_modifier(effective_score)

        return ability_modifiers

    def _get_effective_ability_score(self, raw_data: Dict[str, Any], ability_name: str) -> int:
        """Get effective ability score (base + bonuses) for given ability."""
        ability_id_map = {
            'strength': 1,
            'dexterity': 2,
            'constitution': 3,
            'intelligence': 4,
            'wisdom': 5,
            'charisma': 6
        }

        ability_id = ability_id_map.get(ability_name.lower())
        if not ability_id:
            return 10

        # Get base score from stats array
        base_score = 10
        stats = raw_data.get('stats', [])
        for stat in stats:
            if stat.get('id') == ability_id:
                base_score = stat.get('value', 10)
                break

        # Calculate bonuses from choices (feats/backgrounds)
        total_bonus = 0
        choices = raw_data.get('choices', {})
        feat_choices = choices.get('feat', [])

        for choice in feat_choices:
            if not isinstance(choice, dict):
                continue

            # Look for ability score choices (subType 5)
            if choice.get('subType') == 5:
                option_value = choice.get('optionValue')
                bonus = self._get_ability_bonus_from_choice_option(option_value, ability_name)
                if bonus > 0:
                    total_bonus += bonus

        effective_score = base_score + total_bonus
        return effective_score

    def _get_ability_bonus_from_choice_option(self, option_value: int, ability_name: str) -> int:
        """Map choice option values to ability score bonuses."""
        if not option_value:
            return 0

        # Known mappings from D&D Beyond choice options
        ability_choice_mappings = {
            # +2 bonuses (Constitution, Intelligence, Wisdom)
            6260: ('constitution', 2),
            6261: ('intelligence', 2),
            6262: ('wisdom', 2),
            # +1 bonuses (Constitution, Intelligence, Wisdom)
            6263: ('constitution', 1),
            6264: ('intelligence', 1),
            6265: ('wisdom', 1),
        }

        if option_value in ability_choice_mappings:
            mapped_ability, bonus = ability_choice_mappings[option_value]
            if mapped_ability.lower() == ability_name.lower():
                return bonus

        return 0
    
    def _calculate_weapon_attacks(self, character_data: Dict[str, Any], ability_modifiers: Dict[str, int], proficiency_bonus: int) -> List[AttackData]:
        """Extract weapon attacks from scraper-provided data."""
        weapon_attacks = []
        
        # Use scraper-provided attack actions from combat section
        combat_data = character_data.get('combat', {})
        attack_actions = combat_data.get('attack_actions', [])
        
        for attack in attack_actions:
            if isinstance(attack, dict) and attack.get('type') == 'attack':
                # Convert scraper attack data to AttackData format
                attack_data = AttackData(
                    name=attack.get('name', 'Unknown Attack'),
                    attack_bonus=attack.get('attack_bonus', 0),
                    damage_roll=attack.get('damage_dice', '1d4'),
                    damage_bonus=attack.get('damage_modifier', 0),
                    damage_type=attack.get('damage_type', 'piercing'),
                    attack_type=attack.get('attack_type', 'melee'),
                    weapon_type='weapon',  # Generic
                    proficient=attack.get('is_proficient', True),
                    ability_modifier=attack.get('ability_used', 'strength'),
                    range_normal=attack.get('range_normal', 5),
                    range_long=attack.get('range_long', 5),
                    versatile=False,  # Not tracked in scraper data
                    versatile_damage='',
                    properties=[]  # Not tracked in scraper data
                )
                weapon_attacks.append(attack_data)
        
        return weapon_attacks
    
    
    def _is_weapon_proficient(self, weapon_item: Dict[str, Any], character_data: Dict[str, Any]) -> bool:
        """Check if character is proficient with weapon."""
        # This would need comprehensive proficiency checking
        # For now, assume proficiency based on class
        return True
    
    def _calculate_spell_attacks(self, character_data: Dict[str, Any], ability_modifiers: Dict[str, int], proficiency_bonus: int) -> List[AttackData]:
        """Calculate spell attack bonuses."""
        spell_attacks = []
        
        # Get spellcasting ability and modifier
        spellcasting_ability = self._get_primary_spellcasting_ability(character_data)
        if spellcasting_ability != 'none':
            spell_mod = ability_modifiers.get(spellcasting_ability, 0)
            spell_attack_bonus = spell_mod + proficiency_bonus
            
            # Create generic spell attack
            spell_attacks.append(AttackData(
                name="Spell Attack",
                attack_bonus=spell_attack_bonus,
                damage_roll="varies",
                damage_bonus=spell_mod,
                damage_type="varies",
                attack_type="spell",
                weapon_type="spell",
                proficient=True,
                ability_modifier=spellcasting_ability,
                range_normal=120,  # Typical spell range
                range_long=120,
                versatile=False,
                versatile_damage="",
                properties=[]
            ))
        
        return spell_attacks
    
    def _calculate_natural_attacks(self, character_data: Dict[str, Any], ability_modifiers: Dict[str, int], proficiency_bonus: int) -> List[AttackData]:
        """Calculate natural weapon attacks."""
        natural_attacks = []
        
        # Check for racial natural weapons
        race_data = character_data.get('race', {})
        if race_data:
            race_name = race_data.get('definition', {}).get('name', '').lower()
            
            # Examples: Tabaxi claws, Dragonborn breath weapon, etc.
            # This would need comprehensive racial feature parsing
        
        return natural_attacks
    
    def _calculate_extra_attacks(self, character_data: Dict[str, Any]) -> int:
        """Calculate number of extra attacks."""
        extra_attacks = 0
        classes = character_data.get('classes', [])
        
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            class_level = class_data.get('level', 1)
            
            # Fighter, Paladin, Ranger, Barbarian get Extra Attack
            if class_name in ['fighter', 'paladin', 'ranger', 'barbarian']:
                if class_level >= 5:
                    extra_attacks = max(extra_attacks, 1)
                if class_name == 'fighter' and class_level >= 11:
                    extra_attacks = max(extra_attacks, 2)
                if class_name == 'fighter' and class_level >= 20:
                    extra_attacks = max(extra_attacks, 3)
        
        return extra_attacks
    
    def _get_fighting_styles(self, character_data: Dict[str, Any]) -> List[str]:
        """Get character's fighting styles."""
        fighting_styles = []
        
        # Parse from class features
        # This would need comprehensive feature parsing
        
        return fighting_styles
    
    def _get_attack_modifiers(self, character_data: Dict[str, Any]) -> Dict[str, int]:
        """Get attack roll modifiers from various sources."""
        attack_modifiers = {}
        
        # Parse from modifiers, feats, magic items, etc.
        # This would need comprehensive modifier parsing
        
        return attack_modifiers
    
    def _get_damage_modifiers(self, character_data: Dict[str, Any]) -> Dict[str, int]:
        """Get damage roll modifiers from various sources."""
        damage_modifiers = {}
        
        # Parse from modifiers, feats, magic items, etc.
        # This would need comprehensive modifier parsing
        
        return damage_modifiers
    
    def _get_critical_range(self, character_data: Dict[str, Any]) -> int:
        """Get critical hit range (19-20 or 20 only)."""
        # Default is 20, some features expand to 19-20
        critical_range = 20
        
        # Check for features that expand crit range (Champion Fighter, etc.)
        classes = character_data.get('classes', [])
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            class_level = class_data.get('level', 1)
            subclass = class_data.get('subclassDefinition', {}).get('name', '').lower()
            
            # Champion Fighter Improved Critical
            if 'fighter' in class_name and 'champion' in subclass and class_level >= 3:
                critical_range = 19
        
        return critical_range
    
    def _get_primary_spellcasting_ability(self, character_data: Dict[str, Any]) -> str:
        """Get primary spellcasting ability."""
        classes = character_data.get('classes', [])
        
        # Simple mapping - would need more sophisticated logic for multiclass
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            
            if 'cleric' in class_name or 'druid' in class_name or 'ranger' in class_name:
                return 'wisdom'
            elif 'sorcerer' in class_name or 'bard' in class_name or 'paladin' in class_name or 'warlock' in class_name:
                return 'charisma'
            elif 'wizard' in class_name:
                return 'intelligence'
        
        return 'none'