"""
Damage Calculator

Calculates weapon damage with ability modifiers, magic bonuses, and special properties.
Handles versatile weapons, finesse weapons, and various damage types.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from src.calculators.base import RuleAwareCalculator

@dataclass
class WeaponDamage:
    """Represents calculated weapon damage with all bonuses and breakdowns."""
    weapon_name: str
    base_damage_dice: str
    damage_modifier: int
    damage_type: str
    versatile_damage_dice: Optional[str] = None
    versatile_damage_modifier: Optional[int] = None
    magic_damage_bonus: int = 0
    additional_damage: List[Dict[str, Any]] = field(default_factory=list)
    breakdown: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_damage_expression(self) -> str:
        """Get the complete damage expression."""
        base_expr = f"{self.base_damage_dice}"
        if self.damage_modifier > 0:
            base_expr += f" + {self.damage_modifier}"
        elif self.damage_modifier < 0:
            base_expr += f" - {abs(self.damage_modifier)}"
        
        if self.magic_damage_bonus > 0:
            base_expr += f" + {self.magic_damage_bonus} (magic)"
        
        # Add additional damage types
        for additional in self.additional_damage:
            dice = additional.get('dice', '')
            bonus = additional.get('bonus', 0)
            damage_type = additional.get('type', 'unknown')
            
            if dice:
                base_expr += f" + {dice}"
            if bonus > 0:
                base_expr += f" + {bonus}"
            base_expr += f" {damage_type}"
        
        return f"{base_expr} {self.damage_type}"
    
    @property
    def versatile_damage_expression(self) -> Optional[str]:
        """Get the versatile damage expression if applicable."""
        if not self.versatile_damage_dice:
            return None
        
        versatile_expr = f"{self.versatile_damage_dice}"
        versatile_mod = self.versatile_damage_modifier or self.damage_modifier
        
        if versatile_mod > 0:
            versatile_expr += f" + {versatile_mod}"
        elif versatile_mod < 0:
            versatile_expr += f" - {abs(versatile_mod)}"
        
        if self.magic_damage_bonus > 0:
            versatile_expr += f" + {self.magic_damage_bonus} (magic)"
        
        return f"{versatile_expr} {self.damage_type} (versatile)"

class DamageCalculator(RuleAwareCalculator):
    """Calculator for weapon damage with D&D 5e rules."""
    
    def calculate(self, character_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate damage for all equipped weapons.
        
        Args:
            character_data: Character data dictionary
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with weapon damage calculations
        """
        # Get required data
        abilities = character_data.get('abilities', {})
        ability_scores = abilities.get('ability_scores', {})
        inventory = character_data.get('inventory', {})
        equipped_items = inventory.get('equipped_items', [])
        
        # Filter for weapons only
        weapons = [item for item in equipped_items if self._is_weapon(item)]
        
        # Calculate damage for all weapons
        weapon_damages = self.calculate_multiple_weapons(weapons, ability_scores)
        
        return {
            'weapon_damages': weapon_damages
        }
    
    def _is_weapon(self, item: Dict[str, Any]) -> bool:
        """Determine if an item is a weapon."""
        if not isinstance(item, dict):
            return False
        
        # Check if it's explicitly a weapon
        if item.get('type') == 'weapon':
            return True
        
        # Check weapon properties
        if 'weapon_properties' in item:
            return True
        
        # Check for damage dice
        if 'damage' in item:
            return True
        
        return False
    
    def calculate_weapon_damage(
        self, 
        weapon: Dict[str, Any],
        ability_scores: Dict[str, Any],
        is_two_handed: bool = False,
        magic_bonuses: Optional[Dict[str, Any]] = None
    ) -> WeaponDamage:
        """
        Calculate damage for a specific weapon.
        
        Args:
            weapon: Weapon data dictionary
            ability_scores: Character ability scores
            is_two_handed: Whether weapon is being used two-handed
            magic_bonuses: Additional magic damage bonuses
            
        Returns:
            WeaponDamage object with calculated damage
        """
        weapon_name = weapon.get('name', 'Unknown Weapon')
        
        # Get base damage dice and type
        base_damage_dice = self._get_base_damage_dice(weapon)
        damage_type = self._get_damage_type(weapon)
        
        # Get versatile damage if applicable
        versatile_damage_dice = self._get_versatile_damage_dice(weapon)
        
        # Determine ability modifier for damage
        ability_modifier = self._get_damage_ability_modifier(weapon, ability_scores)
        
        # Get magic damage bonus
        magic_damage_bonus = self._get_magic_damage_bonus(weapon, magic_bonuses)
        
        # Handle versatile weapons
        if is_two_handed and versatile_damage_dice:
            primary_dice = versatile_damage_dice
            versatile_dice = base_damage_dice
            versatile_modifier = ability_modifier
        else:
            primary_dice = base_damage_dice
            versatile_dice = versatile_damage_dice
            versatile_modifier = ability_modifier if versatile_dice else None
        
        # Get additional damage sources
        additional_damage = self._get_additional_damage(weapon, magic_bonuses)
        
        # Create breakdown
        breakdown = {
            'base_dice': primary_dice,
            'ability_modifier': ability_modifier,
            'ability_used': self._get_damage_ability_name(weapon, ability_scores),
            'magic_bonus': magic_damage_bonus,
            'is_two_handed': is_two_handed,
            'has_versatile': versatile_dice is not None,
            'additional_damage_sources': len(additional_damage)
        }
        
        return WeaponDamage(
            weapon_name=weapon_name,
            base_damage_dice=primary_dice,
            damage_modifier=ability_modifier,
            damage_type=damage_type,
            versatile_damage_dice=versatile_dice,
            versatile_damage_modifier=versatile_modifier,
            magic_damage_bonus=magic_damage_bonus,
            additional_damage=additional_damage,
            breakdown=breakdown
        )
    
    def calculate_multiple_weapons(
        self,
        weapons: List[Dict[str, Any]],
        ability_scores: Dict[str, Any],
        magic_bonuses: Optional[Dict[str, Any]] = None
    ) -> List[WeaponDamage]:
        """
        Calculate damage for multiple weapons.
        
        Args:
            weapons: List of weapon data dictionaries
            ability_scores: Character ability scores
            magic_bonuses: Additional magic damage bonuses
            
        Returns:
            List of WeaponDamage objects
        """
        damage_calculations = []
        
        for weapon in weapons:
            # Calculate both one-handed and two-handed if versatile
            damage = self.calculate_weapon_damage(
                weapon=weapon,
                ability_scores=ability_scores,
                is_two_handed=False,
                magic_bonuses=magic_bonuses
            )
            damage_calculations.append(damage)
            
            # Add two-handed version if versatile
            if self._is_versatile(weapon):
                two_handed_damage = self.calculate_weapon_damage(
                    weapon=weapon,
                    ability_scores=ability_scores,
                    is_two_handed=True,
                    magic_bonuses=magic_bonuses
                )
                # Mark as two-handed variant
                two_handed_damage.weapon_name += " (Two-Handed)"
                damage_calculations.append(two_handed_damage)
        
        return damage_calculations
    
    def _get_base_damage_dice(self, weapon: Dict[str, Any]) -> str:
        """Get the base damage dice for the weapon."""
        # Check for explicit damage dice
        if 'damage' in weapon:
            damage = weapon.get('damage', {})
            if isinstance(damage, dict):
                return damage.get('damage_dice', '1d4')
            return str(damage)
        
        # Check definition
        definition = weapon.get('definition', {})
        if isinstance(definition, dict):
            damage = definition.get('damage', {})
            if isinstance(damage, dict):
                dice_string = damage.get('diceString', '1d4')
                return dice_string
        
        # Default based on weapon category
        weapon_category = weapon.get('weapon_category', '').lower()
        if 'martial' in weapon_category:
            return '1d8'  # Default martial weapon damage
        return '1d4'  # Default simple weapon damage
    
    def _get_versatile_damage_dice(self, weapon: Dict[str, Any]) -> Optional[str]:
        """Get versatile damage dice if weapon has versatile property."""
        if not self._is_versatile(weapon):
            return None
        
        # Check for explicit versatile damage
        definition = weapon.get('definition', {})
        if isinstance(definition, dict):
            damage = definition.get('damage', {})
            if isinstance(damage, dict):
                versatile_dice = damage.get('versatileDiceString')
                if versatile_dice:
                    return versatile_dice
        
        # Fallback: increase base damage die by one step
        base_dice = self._get_base_damage_dice(weapon)
        return self._increase_damage_die(base_dice)
    
    def _increase_damage_die(self, dice_string: str) -> str:
        """Increase damage die by one step (d6 -> d8, d8 -> d10, etc.)."""
        # Simple mapping for common dice
        dice_upgrades = {
            '1d4': '1d6',
            '1d6': '1d8',
            '1d8': '1d10',
            '1d10': '1d12',
            '1d12': '2d6',  # d12 to 2d6 is common for versatile
            '2d6': '2d8'
        }
        
        return dice_upgrades.get(dice_string, dice_string)
    
    def _get_damage_type(self, weapon: Dict[str, Any]) -> str:
        """Get the damage type for the weapon."""
        # Check for explicit damage type
        if 'damage' in weapon:
            damage = weapon.get('damage', {})
            if isinstance(damage, dict):
                return damage.get('damage_type', 'slashing')
        
        # Check definition
        definition = weapon.get('definition', {})
        if isinstance(definition, dict):
            damage_type = definition.get('damageType')
            if damage_type:
                return damage_type.lower()
        
        # Default to slashing
        return 'slashing'
    
    def _get_damage_ability_modifier(self, weapon: Dict[str, Any], ability_scores: Dict[str, Any]) -> int:
        """Get the ability modifier used for damage."""
        # Get weapon properties
        properties = self._get_weapon_properties(weapon)
        weapon_type = self._determine_weapon_type(weapon, properties)
        
        # Get ability modifiers
        str_mod = self._get_ability_modifier(ability_scores.get('strength', {}))
        dex_mod = self._get_ability_modifier(ability_scores.get('dexterity', {}))
        
        # Finesse weapons can use DEX instead of STR for damage
        if 'finesse' in properties:
            return max(str_mod, dex_mod)
        
        # Ranged weapons typically use DEX
        if weapon_type == 'ranged':
            return dex_mod
        
        # Melee weapons typically use STR
        return str_mod
    
    def _get_damage_ability_name(self, weapon: Dict[str, Any], ability_scores: Dict[str, Any]) -> str:
        """Get the name of the ability used for damage."""
        # Get weapon properties
        properties = self._get_weapon_properties(weapon)
        weapon_type = self._determine_weapon_type(weapon, properties)
        
        # Get ability modifiers
        str_mod = self._get_ability_modifier(ability_scores.get('strength', {}))
        dex_mod = self._get_ability_modifier(ability_scores.get('dexterity', {}))
        
        # Finesse weapons can use DEX instead of STR for damage
        if 'finesse' in properties:
            return 'DEX' if dex_mod > str_mod else 'STR'
        
        # Ranged weapons typically use DEX
        if weapon_type == 'ranged':
            return 'DEX'
        
        # Melee weapons typically use STR
        return 'STR'
    
    def _get_magic_damage_bonus(self, weapon: Dict[str, Any], magic_bonuses: Optional[Dict[str, Any]] = None) -> int:
        """Get magic damage bonus for the weapon."""
        total_bonus = 0
        
        # Check weapon's inherent magic bonus first
        if 'damage_bonus' in weapon:
            total_bonus += weapon.get('damage_bonus', 0)
        else:
            # Only check name if no explicit damage_bonus field
            name = weapon.get('name', '')
            if '+' in name:
                try:
                    plus_index = name.find('+')
                    bonus_str = ''
                    for char in name[plus_index+1:]:
                        if char.isdigit():
                            bonus_str += char
                        else:
                            break
                    if bonus_str:
                        total_bonus += int(bonus_str)
                except:
                    pass
        
        # Add external magic bonuses
        if magic_bonuses:
            weapon_name = weapon.get('name', '').lower()
            if weapon_name in magic_bonuses:
                total_bonus += magic_bonuses[weapon_name].get('damage_bonus', 0)
        
        return total_bonus
    
    def _get_additional_damage(self, weapon: Dict[str, Any], magic_bonuses: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get additional damage sources (elemental, magic, etc.)."""
        additional_damage = []
        
        # Check weapon definition for additional damage
        definition = weapon.get('definition', {})
        if isinstance(definition, dict):
            # Look for additional damage in weapon properties or modifiers
            modifiers = definition.get('modifiers', [])
            for modifier in modifiers:
                if self._is_damage_modifier(modifier):
                    damage_info = self._parse_damage_modifier(modifier)
                    if damage_info:
                        additional_damage.append(damage_info)
        
        # Check external magic bonuses for additional damage
        if magic_bonuses:
            weapon_name = weapon.get('name', '').lower()
            if weapon_name in magic_bonuses:
                weapon_bonuses = magic_bonuses[weapon_name]
                additional_damages = weapon_bonuses.get('additional_damage', [])
                additional_damage.extend(additional_damages)
        
        return additional_damage
    
    def _is_versatile(self, weapon: Dict[str, Any]) -> bool:
        """Check if weapon has versatile property."""
        properties = self._get_weapon_properties(weapon)
        return 'versatile' in properties
    
    def _get_weapon_properties(self, weapon: Dict[str, Any]) -> List[str]:
        """Extract weapon properties."""
        properties = []
        
        # Check for weapon_properties list
        weapon_properties = weapon.get('weapon_properties', [])
        if isinstance(weapon_properties, list):
            for prop in weapon_properties:
                if isinstance(prop, dict) and 'name' in prop:
                    properties.append(prop['name'].lower())
                elif isinstance(prop, str):
                    properties.append(prop.lower())
        
        # Check for properties in definition
        definition = weapon.get('definition', {})
        if isinstance(definition, dict):
            props = definition.get('weaponProperties', [])
            for prop in props:
                if isinstance(prop, dict) and 'name' in prop:
                    properties.append(prop['name'].lower())
        
        return properties
    
    def _determine_weapon_type(self, weapon: Dict[str, Any], properties: List[str]) -> str:
        """Determine if weapon is melee or ranged."""
        # Check explicit type
        if 'weapon_type' in weapon:
            weapon_type = weapon.get('weapon_type', '').lower()
            if 'melee' in weapon_type:
                return 'melee'
            if 'ranged' in weapon_type:
                return 'ranged'
        
        # Check properties
        if 'thrown' in properties and 'ranged' not in properties:
            return 'melee'  # Thrown weapons are typically melee weapons that can be thrown
        if 'ranged' in properties or 'ammunition' in properties:
            return 'ranged'
        
        # Check range
        if weapon.get('range', {}).get('normal', 0) > 0:
            return 'ranged'
        
        # Default to melee
        return 'melee'
    
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
    
    def _is_damage_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects damage."""
        # This would need to be expanded based on D&D Beyond's modifier structure
        modifier_type = modifier.get('type', '').lower()
        return 'damage' in modifier_type
    
    def _parse_damage_modifier(self, modifier: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Parse a damage modifier into structured damage info."""
        # This would need to be expanded based on D&D Beyond's modifier structure
        # For now, return a placeholder structure
        return {
            'dice': '',
            'bonus': modifier.get('value', 0),
            'type': modifier.get('damageType', 'unknown')
        }