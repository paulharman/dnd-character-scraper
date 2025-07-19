from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from src.calculators.base import RuleAwareCalculator
from src.calculators.damage_calculator import DamageCalculator, WeaponDamage
from src.calculators.utils.magic_item_parser import MagicItemParser
from src.rules.version_manager import RuleVersion

@dataclass
class WeaponAttack:
    """Represents a calculated weapon attack with all bonuses and breakdowns."""
    name: str
    attack_bonus: int
    damage_dice: str
    damage_modifier: int
    damage_type: str
    weapon_type: str  # melee/ranged
    properties: List[str] = field(default_factory=list)
    range_normal: Optional[int] = None
    range_long: Optional[int] = None
    breakdown: Dict[str, Any] = field(default_factory=dict)
    damage_calculation: Optional[WeaponDamage] = None
    
    @property
    def full_damage_expression(self) -> str:
        """Get the full damage expression including versatile options."""
        if self.damage_calculation:
            return self.damage_calculation.total_damage_expression
        else:
            # Fallback to basic expression
            expr = f"{self.damage_dice}"
            if self.damage_modifier > 0:
                expr += f" + {self.damage_modifier}"
            elif self.damage_modifier < 0:
                expr += f" - {abs(self.damage_modifier)}"
            return f"{expr} {self.damage_type}"

class EnhancedWeaponAttackCalculator(RuleAwareCalculator):
    """Calculator for weapon attack bonuses and damage."""
    
    def __init__(self, config_manager=None, rule_manager=None):
        """Initialize the enhanced weapon attack calculator."""
        super().__init__(config_manager, rule_manager)
        self.damage_calculator = DamageCalculator(config_manager, rule_manager)
        self.magic_item_parser = MagicItemParser()
    
    def calculate(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate weapon attack bonuses and damage for all equipped weapons."""
        if not character_data:
            return {'weapon_attacks': [], 'errors': ['No character data provided']}
        
        errors = []
        warnings = []
        
        try:
            # Detect rule version
            rule_version = self._detect_rule_version(character_data)
            
            # Get required data with fallbacks
            abilities = character_data.get('abilities', {})
            ability_scores = abilities.get('ability_scores', {})
            proficiencies = character_data.get('proficiencies', {})
            inventory = character_data.get('inventory', {})
            equipped_items = inventory.get('equipped_items', [])
            character_info = character_data.get('character_info', {})
            
            # Validate basic data
            if not ability_scores:
                warnings.append("No ability scores found, using defaults")
                ability_scores = self._get_default_ability_scores()
            
            # Calculate proficiency bonus
            level = character_info.get('level', 1)
            if level < 1 or level > 20:
                warnings.append(f"Unusual character level: {level}, clamping to valid range")
                level = max(1, min(20, level))
            
            proficiency_bonus = self._calculate_proficiency_bonus(level)
            
            # Get weapon proficiencies
            weapon_proficiencies = self._extract_weapon_proficiencies(proficiencies)
            
            # Calculate attacks for each equipped weapon
            weapon_attacks = []
            for item in equipped_items:
                if self._is_weapon(item):
                    try:
                        attack = self._calculate_weapon_attack(
                            weapon=item,
                            ability_scores=ability_scores,
                            proficiency_bonus=proficiency_bonus,
                            weapon_proficiencies=weapon_proficiencies,
                            rule_version=rule_version
                        )
                        if attack:
                            # Validate calculated attack bonus is reasonable
                            if attack.attack_bonus < -5 or attack.attack_bonus > 25:
                                warnings.append(f"Unusual attack bonus for {attack.name}: +{attack.attack_bonus}")
                            weapon_attacks.append(attack)
                    except Exception as e:
                        weapon_name = item.get('definition', {}).get('name', 'Unknown Weapon')
                        errors.append(f"Failed to calculate attack for {weapon_name}: {str(e)}")
            
            result = {
                'weapon_attacks': weapon_attacks,
                'rule_version': rule_version
            }
            
            if errors:
                result['errors'] = errors
            if warnings:
                result['warnings'] = warnings
                
            return result
            
        except Exception as e:
            return {
                'weapon_attacks': [],
                'rule_version': '2014',
                'errors': [f"Critical error in weapon attack calculation: {str(e)}"]
            }
    
    def _calculate_proficiency_bonus(self, level: int) -> int:
        """Calculate proficiency bonus based on character level."""
        return 2 + ((level - 1) // 4)
    
    def _extract_weapon_proficiencies(self, proficiencies: Dict[str, Any]) -> List[str]:
        """Extract weapon proficiencies from character data."""
        weapon_profs = []
        
        # Extract from weapon_proficiencies
        weapon_proficiencies = proficiencies.get('weapon_proficiencies', [])
        if isinstance(weapon_proficiencies, list):
            for prof in weapon_proficiencies:
                if isinstance(prof, dict):
                    weapon_profs.append(prof.get('name', '').lower())
                elif isinstance(prof, str):
                    weapon_profs.append(prof.lower())
        
        # Extract from class features that grant weapon proficiencies
        # This would need to be expanded based on class features
        
        return weapon_profs
    
    def _is_weapon(self, item: Dict[str, Any]) -> bool:
        """Determine if an item is a weapon."""
        if not isinstance(item, dict):
            return False
        
        # Check definition for weapon indicators
        definition = item.get('definition', {})
        
        # Check if it has damage (weapons have damage)
        if definition.get('damage'):
            return True
        
        # Check if it has attackType (weapons have attack types)
        if definition.get('attackType') is not None:
            return True
        
        # Check if it has weapon properties
        if definition.get('properties'):
            return True
        
        # Check if it has weapon category
        if definition.get('categoryId') is not None:
            return True
        
        # Check for explicit weapon type in name or type
        item_type = definition.get('type', '').lower()
        if any(weapon_type in item_type for weapon_type in ['sword', 'bow', 'crossbow', 'dagger', 'axe', 'mace', 'spear']):
            return True
        
        # Legacy checks for transformed data
        if item.get('type') == 'weapon':
            return True
        
        if 'weapon_properties' in item:
            return True
        
        if 'attack_bonus' in item or 'damage' in item:
            return True
        
        return False   
 
    def _calculate_weapon_attack(
        self, 
        weapon: Dict[str, Any],
        ability_scores: Dict[str, Any],
        proficiency_bonus: int,
        weapon_proficiencies: List[str],
        rule_version: str = "2014"
    ) -> Optional[WeaponAttack]:
        """Calculate attack bonus and damage for a weapon."""
        if not weapon:
            return None
        
        # Get weapon name from definition or fallback to item name
        definition = weapon.get('definition', {})
        weapon_name = definition.get('name', weapon.get('name', 'Unknown Weapon'))
        
        # Determine weapon properties
        properties = self._get_weapon_properties(weapon)
        
        # Determine if it's a melee or ranged weapon
        weapon_type = self._determine_weapon_type(weapon, properties)
        
        # Determine ability modifier to use
        ability_mod, ability_used = self._determine_ability_modifier(
            weapon_type, 
            properties, 
            ability_scores
        )
        
        # Determine if proficient
        is_proficient = self._is_proficient_with_weapon(weapon, weapon_proficiencies)
        prof_bonus = proficiency_bonus if is_proficient else 0
        
        # Get magic bonus
        magic_bonus = self._get_magic_bonus(weapon)
        
        # Calculate attack bonus
        attack_bonus = ability_mod + prof_bonus + magic_bonus
        
        # Get damage dice
        damage_dice = self._get_damage_dice(weapon)
        
        # Get damage type
        damage_type = self._get_damage_type(weapon)
        
        # Get magic damage bonus (may be different from attack bonus)
        magic_damage_bonus = self._get_magic_damage_bonus(weapon)
        
        # Calculate damage modifier (ability mod + magic damage bonus)
        damage_modifier = ability_mod + magic_damage_bonus
        
        # Get range if applicable
        range_normal, range_long = self._get_weapon_range(weapon)
        
        # Calculate comprehensive damage using damage calculator
        damage_calculation = None
        try:
            damage_calculation = self.damage_calculator.calculate_weapon_damage(
                weapon=weapon,
                ability_scores=ability_scores
            )
        except Exception as e:
            # Log error but continue with basic damage calculation
            pass
        
        # Create breakdown
        breakdown = {
            'ability_modifier': ability_mod,
            'ability_used': ability_used,
            'proficiency_bonus': prof_bonus,
            'magic_bonus': magic_bonus,
            'description': f"{ability_mod} ({ability_used}) + {prof_bonus} (Prof) + {magic_bonus} (Magic)"
        }
        
        attack = WeaponAttack(
            name=weapon_name,
            attack_bonus=attack_bonus,
            damage_dice=damage_dice,
            damage_modifier=damage_modifier,
            damage_type=damage_type,
            weapon_type=weapon_type,
            properties=properties,
            range_normal=range_normal,
            range_long=range_long,
            breakdown=breakdown,
            damage_calculation=damage_calculation
        )
        
        # Apply rule version specific differences
        attack = self._apply_rule_version_differences(attack, rule_version)
        
        return attack
    
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
    
    def _get_weapon_properties(self, weapon: Dict[str, Any]) -> List[str]:
        """Extract weapon properties."""
        properties = []
        
        # Check for weapon_properties list (legacy format)
        weapon_properties = weapon.get('weapon_properties', [])
        if isinstance(weapon_properties, list):
            for prop in weapon_properties:
                if isinstance(prop, dict) and 'name' in prop:
                    properties.append(prop['name'].lower())
                elif isinstance(prop, str):
                    properties.append(prop.lower())
        
        # Check for properties in definition (D&D Beyond format)
        definition = weapon.get('definition', {})
        if isinstance(definition, dict):
            props = definition.get('properties', [])
            if isinstance(props, list):
                for prop in props:
                    if isinstance(prop, dict) and 'name' in prop:
                        properties.append(prop['name'].lower())
        
        return properties
    
    def _determine_weapon_type(self, weapon: Dict[str, Any], properties: List[str]) -> str:
        """Determine if weapon is melee or ranged."""
        # Check explicit type (legacy format)
        if 'weapon_type' in weapon:
            weapon_type = weapon.get('weapon_type', '').lower()
            if 'melee' in weapon_type:
                return 'melee'
            if 'ranged' in weapon_type:
                return 'ranged'
        
        # Check D&D Beyond attackType (1 = melee, 2 = ranged)
        definition = weapon.get('definition', {})
        attack_type = definition.get('attackType')
        if attack_type == 1:
            return 'melee'
        elif attack_type == 2:
            return 'ranged'
        
        # Check properties
        if 'thrown' in properties and 'range' not in properties:
            return 'melee'  # Thrown weapons are typically melee weapons that can be thrown
        if 'range' in properties or 'ammunition' in properties:
            return 'ranged'
        
        # Check if weapon has range (D&D Beyond format)
        normal_range = definition.get('range')
        if normal_range and normal_range > 0:
            return 'ranged'
        
        # Check legacy range format
        if weapon.get('range', {}).get('normal', 0) > 0:
            return 'ranged'
        
        # Check weapon name for common ranged weapon types
        weapon_name = definition.get('name', weapon.get('name', '')).lower()
        ranged_weapon_types = ['bow', 'crossbow', 'sling', 'dart', 'javelin']
        if any(weapon_type in weapon_name for weapon_type in ranged_weapon_types):
            return 'ranged'
        
        # Default to melee
        return 'melee'
    
    def _determine_ability_modifier(
        self, 
        weapon_type: str, 
        properties: List[str],
        ability_scores: Dict[str, Any]
    ) -> Tuple[int, str]:
        """Determine which ability modifier to use for attack and damage."""
        # Get ability modifiers
        str_mod = self._get_ability_modifier(ability_scores.get('strength', {}))
        dex_mod = self._get_ability_modifier(ability_scores.get('dexterity', {}))
        
        # Finesse weapons can use DEX instead of STR for melee
        if 'finesse' in properties:
            if dex_mod > str_mod:
                return dex_mod, 'DEX'
            return str_mod, 'STR'
        
        # Ranged weapons typically use DEX
        if weapon_type == 'ranged':
            return dex_mod, 'DEX'
        
        # Melee weapons typically use STR
        return str_mod, 'STR'
    
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
    
    def _is_proficient_with_weapon(self, weapon: Dict[str, Any], weapon_proficiencies: List[str]) -> bool:
        """Determine if character is proficient with this weapon."""
        # Get weapon category and name
        weapon_name = weapon.get('name', '').lower()
        weapon_category = weapon.get('weapon_category', '').lower()
        
        # Check direct name match
        if weapon_name in weapon_proficiencies:
            return True
        
        # Check category match (simple weapons, martial weapons, etc.)
        if weapon_category in weapon_proficiencies:
            return True
        
        # Check for "all weapons" proficiency
        if 'all weapons' in weapon_proficiencies:
            return True
        
        # Check for weapon groups
        weapon_group = weapon.get('weapon_group', '').lower()
        if weapon_group and weapon_group in weapon_proficiencies:
            return True
        
        # Check for broader category matches
        if weapon_category == 'martial' and 'martial weapons' in weapon_proficiencies:
            return True
        if weapon_category == 'simple' and 'simple weapons' in weapon_proficiencies:
            return True
        
        return False
    
    def _get_magic_bonus(self, weapon: Dict[str, Any]) -> int:
        """Extract magic bonus from weapon using enhanced magic item parser."""
        # Use magic item parser for comprehensive bonus detection
        bonuses = self.magic_item_parser.parse_item_bonuses(weapon)
        weapon_bonuses = self.magic_item_parser.get_weapon_bonuses(bonuses)
        
        # Return attack bonus (damage bonus is handled separately)
        magic_attack_bonus = weapon_bonuses.get('attack_bonus', 0)
        
        # Fallback to legacy detection if parser didn't find anything
        if magic_attack_bonus == 0:
            # Check for explicit attack bonus
            if 'attack_bonus' in weapon:
                magic_attack_bonus = weapon.get('attack_bonus', 0)
            
            # Check for +X in name
            if magic_attack_bonus == 0:
                name = weapon.get('name', '')
                if '+' in name:
                    try:
                        # Extract +X from name like "Longsword +1"
                        plus_index = name.find('+')
                        bonus_str = ''
                        for char in name[plus_index+1:]:
                            if char.isdigit():
                                bonus_str += char
                            else:
                                break
                        if bonus_str:
                            magic_attack_bonus = int(bonus_str)
                    except:
                        pass
        
        return magic_attack_bonus
    
    def _get_magic_damage_bonus(self, weapon: Dict[str, Any]) -> int:
        """Extract magic damage bonus from weapon using enhanced magic item parser."""
        # Use magic item parser for comprehensive bonus detection
        bonuses = self.magic_item_parser.parse_item_bonuses(weapon)
        weapon_bonuses = self.magic_item_parser.get_weapon_bonuses(bonuses)
        
        # Return damage bonus
        magic_damage_bonus = weapon_bonuses.get('damage_bonus', 0)
        
        # Fallback to legacy detection if parser didn't find anything
        if magic_damage_bonus == 0:
            # Check for explicit damage bonus
            if 'damage_bonus' in weapon:
                magic_damage_bonus = weapon.get('damage_bonus', 0)
            
            # Check for +X in name (same as attack bonus for most magic weapons)
            if magic_damage_bonus == 0:
                name = weapon.get('name', '')
                if '+' in name:
                    try:
                        # Extract +X from name like "Longsword +1"
                        plus_index = name.find('+')
                        bonus_str = ''
                        for char in name[plus_index+1:]:
                            if char.isdigit():
                                bonus_str += char
                            else:
                                break
                        if bonus_str:
                            magic_damage_bonus = int(bonus_str)
                    except:
                        pass
        
        return magic_damage_bonus
    
    def _get_damage_dice(self, weapon: Dict[str, Any]) -> str:
        """Get the damage dice for the weapon."""
        # Check for explicit damage dice (legacy format)
        if 'damage' in weapon:
            damage = weapon.get('damage', {})
            if isinstance(damage, dict):
                return damage.get('damage_dice', '1d4')
            return str(damage)
        
        # Check definition (D&D Beyond format)
        definition = weapon.get('definition', {})
        if isinstance(definition, dict):
            damage = definition.get('damage', {})
            if isinstance(damage, dict):
                # D&D Beyond uses 'diceString' for damage dice
                dice_string = damage.get('diceString', damage.get('damage_dice', '1d4'))
                return dice_string
        
        # Default damage dice based on weapon type
        weapon_type = weapon.get('weapon_category', '').lower()
        if 'martial' in weapon_type:
            return '1d8'  # Default martial weapon damage
        return '1d4'  # Default simple weapon damage
    
    def _get_damage_type(self, weapon: Dict[str, Any]) -> str:
        """Get the damage type for the weapon."""
        # Check for explicit damage type (legacy format)
        if 'damage' in weapon:
            damage = weapon.get('damage', {})
            if isinstance(damage, dict):
                return damage.get('damage_type', 'slashing')
        
        # Check definition (D&D Beyond format)
        definition = weapon.get('definition', {})
        if isinstance(definition, dict):
            # D&D Beyond uses 'damageType' directly in definition
            damage_type = definition.get('damageType')
            if damage_type:
                return damage_type.lower()
            
            # Also check damage object
            damage = definition.get('damage', {})
            if isinstance(damage, dict):
                return damage.get('damageType', damage.get('damage_type', 'slashing')).lower()
        
        # Default to slashing
        return 'slashing'
    
    def _get_weapon_range(self, weapon: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
        """Get the normal and long range of the weapon if applicable."""
        # Check for explicit range (legacy format)
        if 'range' in weapon:
            range_data = weapon.get('range', {})
            if isinstance(range_data, dict):
                normal = range_data.get('normal')
                long = range_data.get('long')
                return normal, long
        
        # Check definition (D&D Beyond format)
        definition = weapon.get('definition', {})
        if isinstance(definition, dict):
            # D&D Beyond uses 'range' and 'longRange' directly in definition
            normal_range = definition.get('range')
            long_range = definition.get('longRange')
            
            if normal_range is not None or long_range is not None:
                return normal_range, long_range
            
            # Also check nested range object
            if 'range' in definition:
                range_data = definition.get('range', {})
                if isinstance(range_data, dict):
                    normal = range_data.get('normal')
                    long = range_data.get('long')
                    return normal, long
        
        # Default to None for melee weapons
        return None, None
    
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
    
    def _apply_rule_version_differences(self, attack: WeaponAttack, rule_version: str) -> WeaponAttack:
        """
        Apply rule version specific differences to weapon attacks.
        
        Args:
            attack: Base weapon attack calculation
            rule_version: Rule version to apply ("2014" or "2024")
            
        Returns:
            Modified weapon attack with rule-specific adjustments
        """
        if rule_version == "2024":
            # 2024 rule differences for weapon attacks:
            
            # 1. Weapon Mastery properties (new in 2024)
            # Note: This would require additional data about weapon mastery choices
            # For now, we'll document that this is where weapon mastery would be applied
            
            # 2. Two-Weapon Fighting changes
            # In 2024, two-weapon fighting works differently with light weapons
            if 'light' in attack.properties:
                # In 2024, light weapons can be used for two-weapon fighting more easily
                # This would affect bonus action attacks, but that's handled elsewhere
                pass
            
            # 3. Nick property (new in 2024)
            if 'nick' in attack.properties:
                # Nick property allows making an extra attack as part of the Attack action
                # This would be reflected in action economy, not individual attack calculations
                pass
            
            # Add rule version to breakdown
            attack.breakdown['rule_version'] = '2024'
            attack.breakdown['description'] += ' (2024 rules)'
        else:
            # 2014 rules (default)
            attack.breakdown['rule_version'] = '2014'
            attack.breakdown['description'] += ' (2014 rules)'
        
        return attack