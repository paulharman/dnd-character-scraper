"""
Combat Coordinator

Coordinates the calculation of combat-related stats including weapon attacks,
spell attacks, initiative, armor class, hit points, and action economy.
"""

from typing import Dict, Any, List, Optional, Tuple
import logging
from dataclasses import dataclass

from ..interfaces.coordination import ICoordinator
from ..utils.performance import monitor_performance
from ..services.interfaces import CalculationContext, CalculationResult, CalculationStatus
from ..services.spell_service import SpellProcessingService
from ..enhanced_weapon_attacks import EnhancedWeaponAttackCalculator
from ..armor_class import ArmorClassCalculator

logger = logging.getLogger(__name__)


@dataclass
class CombatData:
    """Data class for combat calculation results."""
    initiative_bonus: int
    speed: int
    armor_class: int
    hit_points: Dict[str, Any]
    attack_actions: List[Dict[str, Any]]
    spell_actions: List[Dict[str, Any]]
    saving_throws: Dict[str, Any]
    proficiency_bonus: int
    metadata: Dict[str, Any]


class CombatCoordinator(ICoordinator):
    """
    Coordinates combat calculations and action extraction.
    
    This coordinator handles:
    - Weapon attack calculations with proficiency and ability modifiers
    - Spell attack bonuses and save DCs
    - Initiative bonus calculation
    - Combat action extraction and formatting
    - Attack and damage roll calculations
    - Weapon proficiency determination
    - Action economy management
    """
    
    def __init__(self, config_manager=None):
        """
        Initialize the combat coordinator.
        
        Args:
            config_manager: Configuration manager instance
        """
        self.config_manager = config_manager
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize enhanced weapon attack calculator
        self.weapon_attack_calculator = EnhancedWeaponAttackCalculator()
        
        # Initialize armor class calculator
        self.armor_class_calculator = ArmorClassCalculator(config_manager)
        
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
    
    @property
    def coordinator_name(self) -> str:
        """Get the coordinator name."""
        return "combat"
    
    @property
    def dependencies(self) -> List[str]:
        """Get the list of dependencies."""
        return ["character_info", "abilities"]  # Depends on basic info and ability scores
    
    @property
    def priority(self) -> int:
        """Get the execution priority (lower = higher priority)."""
        return 30  # Medium priority - depends on abilities and character info
    
    @monitor_performance("combat_coordinate")
    def coordinate(self, raw_data: Dict[str, Any], context: CalculationContext) -> CalculationResult:
        """
        Coordinate the calculation of combat statistics.
        
        Args:
            raw_data: Raw character data from D&D Beyond
            context: Calculation context
            
        Returns:
            CalculationResult with combat data
        """
        self.logger.info(f"Coordinating combat calculation for character {raw_data.get('id', 'unknown')}")
        
        try:
            # Check for required fields
            if not self._validate_combat_data(raw_data):
                return CalculationResult(
                    service_name=self.coordinator_name,
                    status=CalculationStatus.FAILED,
                    data={},
                    errors=["Missing required combat data"]
                )
            
            # Get dependencies from context
            ability_modifiers = self._get_ability_modifiers(raw_data, context)
            proficiency_bonus = self._get_proficiency_bonus(raw_data, context)
            character_level = self._get_character_level(raw_data, context)
            
            # Calculate initiative bonus
            try:
                initiative_bonus = self._calculate_initiative(raw_data, ability_modifiers)
                self.logger.debug(f"Initiative bonus calculated: {initiative_bonus}")
            except Exception as e:
                self.logger.error(f"Error calculating initiative: {e}")
                raise
            
            # Calculate speed
            try:
                speed = self._calculate_speed(raw_data)
                self.logger.debug(f"Speed calculated: {speed}")
            except Exception as e:
                self.logger.error(f"Error calculating speed: {e}")
                raise
            
            # Get scraper-provided attack data
            weapon_attacks = self._get_scraper_attack_actions(raw_data)
            
            # Extract spell attacks
            spell_attacks = self._extract_spell_attacks(raw_data, ability_modifiers, proficiency_bonus)
            
            # Calculate saving throws
            saving_throws = self._calculate_saving_throws(raw_data, ability_modifiers, proficiency_bonus)
            
            # Get AC and HP from context or calculate fallback
            try:
                armor_class = self._get_armor_class(raw_data, context)
                self.logger.debug(f"Armor class calculated: {armor_class}")
            except Exception as e:
                self.logger.error(f"Error calculating armor class: {e}")
                raise
                
            try:
                hit_points = self._get_hit_points(raw_data, context)
                self.logger.debug(f"Hit points calculated: {hit_points}")
            except Exception as e:
                self.logger.error(f"Error calculating hit points: {e}")
                raise
            
            # Combine all actions
            all_actions = weapon_attacks + spell_attacks
            
            # Create result data
            result_data = {
                'initiative_bonus': initiative_bonus,
                'speed': speed,
                'armor_class': armor_class,
                'hit_points': hit_points,
                'attack_actions': weapon_attacks,
                'spell_actions': spell_attacks,
                'all_actions': all_actions,
                'saving_throws': saving_throws,
                'proficiency_bonus': proficiency_bonus,
                'metadata': {
                    'total_actions': len(all_actions),
                    'weapon_attacks': len(weapon_attacks),
                    'spell_attacks': len(spell_attacks),
                    'has_ranged_attacks': any(self._is_ranged_attack(action) for action in all_actions),
                    'has_melee_attacks': any(self._is_melee_attack(action) for action in all_actions),
                    'character_level': character_level,
                    'initiative_modifier': ability_modifiers.get('dexterity', 0)
                }
            }
            
            self.logger.info(f"Successfully calculated combat stats. Actions: {len(all_actions)}, Initiative: {initiative_bonus:+d}")
            
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.COMPLETED,
                data=result_data,
                errors=[],
                warnings=[]
            )
            
        except Exception as e:
            self.logger.error(f"Error coordinating combat calculation: {str(e)}")
            return CalculationResult(
                service_name=self.coordinator_name,
                status=CalculationStatus.FAILED,
                data={},
                errors=[f"Combat calculation failed: {str(e)}"]
            )
    
    def _validate_combat_data(self, raw_data: Dict[str, Any]) -> bool:
        """Validate that we have sufficient data for combat calculations."""
        # Basic validation - we need character data
        if not isinstance(raw_data, dict):
            self.logger.error("Raw data is not a dictionary")
            return False
        
        # We need at least some character data
        if 'id' not in raw_data and 'name' not in raw_data:
            self.logger.error("Missing basic character identifiers")
            return False
        
        return True
    
    def _get_ability_modifiers(self, raw_data: Dict[str, Any], context: CalculationContext) -> Dict[str, int]:
        """Get ability modifiers from context or calculate from raw data."""
        # Try to get from context first (from abilities coordinator)
        if context and hasattr(context, 'metadata') and context.metadata:
            abilities_data = context.metadata.get('abilities', {})
            if 'ability_modifiers' in abilities_data:
                return abilities_data['ability_modifiers']
        
        # Fallback: calculate from raw data
        ability_modifiers = {}
        stats = raw_data.get('stats', [])
        
        for stat in stats:
            ability_id = stat.get('id')
            ability_score = stat.get('value', 10)
            
            if ability_id in self.ability_id_map:
                ability_name = self.ability_id_map[ability_id]
                modifier = (ability_score - 10) // 2
                ability_modifiers[ability_name] = modifier
        
        # Ensure all abilities are present
        for ability in self.ability_names:
            if ability not in ability_modifiers:
                ability_modifiers[ability] = 0
        
        return ability_modifiers
    
    def _get_proficiency_bonus(self, raw_data: Dict[str, Any], context: CalculationContext) -> int:
        """Get proficiency bonus from context or calculate from character level."""
        # Try to get from context first (from character_info coordinator)
        if context and hasattr(context, 'metadata') and context.metadata:
            character_info = context.metadata.get('character_info', {})
            if 'proficiency_bonus' in character_info:
                return character_info['proficiency_bonus']
        
        # Fallback: calculate from character level
        character_level = self._get_character_level(raw_data, context)
        return ((character_level - 1) // 4) + 2
    
    def _get_character_level(self, raw_data: Dict[str, Any], context: CalculationContext) -> int:
        """Get character level from context or calculate from classes."""
        # Try to get from context first
        if context and hasattr(context, 'metadata') and context.metadata:
            character_info = context.metadata.get('character_info', {})
            if 'level' in character_info:
                return character_info['level']
        
        # Fallback: calculate from classes
        classes = raw_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes)
        return max(1, total_level)
    
    def _get_armor_class(self, raw_data: Dict[str, Any], context: CalculationContext) -> Dict[str, Any]:
        """Get armor class from context or calculate using proper AC calculator."""
        # Skip context AC for now since it may contain old buggy values
        # TODO: Re-enable context AC once we ensure it's calculated correctly
        # if context and hasattr(context, 'metadata') and context.metadata:
        #     combat_data = context.metadata.get('combat', {})
        #     if 'armor_class' in combat_data:
        #         return combat_data['armor_class']
        
        # Use the proper ArmorClassCalculator for accurate AC calculation
        try:
            # Create a minimal Character object for the AC calculator
            # The AC calculator needs the character structure but we'll pass raw_data
            from src.models.character import Character
            
            # Create a character object with minimal required data
            character_info = raw_data.get('character_info', {})
            character = Character(
                id=character_info.get('character_id', 0),
                name=character_info.get('name', 'Unknown'),
                level=character_info.get('level', 1),
                classes=character_info.get('classes', []),
                race=character_info.get('species', {}),
                background=character_info.get('background', {}),
                abilities={},  # Not needed for AC calculation
                proficiencies={},  # Not needed for AC calculation
                spells={},  # Not needed for AC calculation
                equipment={},  # Not needed for AC calculation
                combat_stats={},  # Not needed for AC calculation
                features=[]  # Not needed for AC calculation
            )
            
            # Calculate AC using the proper calculator
            ac_result = self.armor_class_calculator.calculate_ac(character, raw_data)
            self.logger.debug(f"AC calculated using ArmorClassCalculator: {ac_result}")
            
            # If the AC calculator returns an integer, wrap it in a structure
            if isinstance(ac_result, int):
                return {
                    'total': ac_result,
                    'base': 10,  # Default base, may not be accurate for armored characters
                    'breakdown': f"AC: {ac_result}",
                    'armor_type': 'calculated',
                    'has_armor': True,  # Assume armor if calculated by AC calculator
                    'has_shield': False  # Unknown from basic calculation
                }
            else:
                return ac_result  # Already structured
            
        except Exception as e:
            self.logger.error(f"Error using ArmorClassCalculator: {e}")
            # Fallback to improved but simpler calculation
            return self._calculate_ac_fallback(raw_data)
    
    def _calculate_ac_fallback(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback AC calculation with proper armor, shield, and dex cap handling."""
        self.logger.debug("Using fallback AC calculation")
        
        # Get ability modifiers
        ability_modifiers = self._get_ability_modifiers(raw_data, None)
        dex_mod = ability_modifiers.get('dexterity', 0) or 0
        con_mod = ability_modifiers.get('constitution', 0) or 0
        wis_mod = ability_modifiers.get('wisdom', 0) or 0
        
        # Check equipment for armor and shields - try multiple data paths
        inventory = raw_data.get('inventory', [])
        if not inventory:
            # Try alternative equipment structure
            equipment = raw_data.get('equipment', {})
            inventory = equipment.get('basic_equipment', [])
        
        # Also check if there's pre-calculated combat equipment data we can use
        combat_data = raw_data.get('combat', {})
        combat_equipment = combat_data.get('equipment', [])
        if combat_equipment and not inventory:
            inventory = combat_equipment
            self.logger.debug("Using combat equipment data for AC calculation")
        
        armor_ac = 0
        armor_type = None
        shield_ac = 0
        
        # Scan equipped items
        self.logger.debug(f"Scanning {len(inventory)} items for armor and shields")
        for item in inventory:
            if not item.get('equipped', False):
                continue
                
            # Get item name from either direct property or nested definition
            item_name = item.get('name', '')
            if not item_name:
                # Try nested definition structure (raw D&D Beyond API format)
                item_def = item.get('definition', {})
                item_name = item_def.get('name', '')
            
            item_name = item_name.lower()
            self.logger.debug(f"Checking equipped item: {item_name}")
            
            # Check for armor (not shields)
            if 'shield' not in item_name:
                # Try to get AC from multiple possible locations
                ac_value = None
                
                # Method 1: Check item definition
                item_def = item.get('definition', {})
                ac_value = item_def.get('armorClass') or item_def.get('armor_class')
                self.logger.debug(f"Method 1 (definition): {ac_value}")
                
                # Method 2: Check direct on item
                if ac_value is None:
                    ac_value = item.get('armorClass') or item.get('armor_class')
                    self.logger.debug(f"Method 2 (direct): {ac_value}")
                
                # Method 3: Standard armor lookup
                if ac_value is None:
                    ac_value = self._get_standard_armor_ac(item_name)
                    self.logger.debug(f"Method 3 (standard lookup for '{item_name}'): {ac_value}")
                
                if ac_value and ac_value > armor_ac:
                    armor_ac = ac_value
                    armor_type = self._get_armor_type(item_name)
                    self.logger.debug(f"Found armor: {item_name} AC {ac_value} type {armor_type}")
            
            # Check for shields
            elif 'shield' in item_name:
                # Try to get shield AC
                shield_value = None
                
                # Method 1: Check item definition  
                item_def = item.get('definition', {})
                shield_value = item_def.get('armorClass') or item_def.get('armor_class')
                
                # Method 2: Check direct on item
                if shield_value is None:
                    shield_value = item.get('armorClass') or item.get('armor_class')
                
                # Method 3: Default shield AC
                if shield_value is None:
                    shield_value = 2  # Standard shield AC
                
                shield_ac += shield_value
                self.logger.debug(f"Found shield: {item_name} AC +{shield_value}")
        
        self.logger.debug(f"Final equipment scan results: armor_ac={armor_ac}, armor_type={armor_type}, shield_ac={shield_ac}")
        
        # Calculate final AC
        if armor_ac > 0:
            # Wearing armor: apply dex cap based on armor type
            max_dex = self._get_armor_dex_cap(armor_type)
            capped_dex = min(dex_mod, max_dex) if max_dex is not None else dex_mod
            final_ac = armor_ac + capped_dex + shield_ac
            self.logger.debug(f"Armored AC: {armor_ac} (armor) + {capped_dex} (dex, capped at {max_dex}) + {shield_ac} (shield) = {final_ac}")
            
            # Create structured result for armored AC - format without double signs
            breakdown_parts = [f"{armor_ac} (armor)"]
            if capped_dex > 0:
                breakdown_parts.append(f"{capped_dex} (dex)")
            elif capped_dex < 0:
                breakdown_parts.append(f"{capped_dex} (dex)")  # Already has negative sign
            if shield_ac > 0:
                breakdown_parts.append(f"{shield_ac} (shield)")
            
            return {
                'total': final_ac,
                'base': armor_ac,  # Base armor AC instead of 10
                'breakdown': f"AC: {' + '.join(breakdown_parts)} = {final_ac}",
                'armor_type': armor_type or 'unknown',
                'has_armor': True,
                'has_shield': shield_ac > 0
            }
        else:
            # Unarmored: check for unarmored defense
            base_ac = 10 + dex_mod
            unarmored_bonus = 0
            unarmored_type = "Unarmored"
            
            classes = raw_data.get('classes', [])
            class_names = [cls.get('definition', {}).get('name', '').lower() for cls in classes]
            
            # Barbarian Unarmored Defense: 10 + Dex + Con
            if 'barbarian' in class_names:
                unarmored_bonus = con_mod
                unarmored_type = "Unarmored Defense (Barbarian)"
                self.logger.debug(f"Barbarian unarmored defense: +{con_mod} CON")
            
            # Monk Unarmored Defense: 10 + Dex + Wis (no shield)
            elif 'monk' in class_names and shield_ac == 0:
                unarmored_bonus = wis_mod
                unarmored_type = "Unarmored Defense (Monk)"
                self.logger.debug(f"Monk unarmored defense: +{wis_mod} WIS")
            
            final_ac = base_ac + unarmored_bonus + shield_ac
            self.logger.debug(f"Unarmored AC: {base_ac} (base+dex) + {unarmored_bonus} (unarmored) + {shield_ac} (shield) = {final_ac}")
            
            # Create structured result for unarmored AC - format without double signs
            breakdown_parts = ["10 (base)"]
            
            # Add dex without double signs
            if dex_mod > 0:
                breakdown_parts.append(f"{dex_mod} (dex)")
            elif dex_mod < 0:
                breakdown_parts.append(f"{dex_mod} (dex)")  # Already has negative sign
            else:
                breakdown_parts.append("0 (dex)")
                
            # Add unarmored bonus without double signs  
            if unarmored_bonus != 0:
                ability_name = "con" if 'barbarian' in class_names else "wis" if 'monk' in class_names else "special"
                if unarmored_bonus > 0:
                    breakdown_parts.append(f"{unarmored_bonus} ({ability_name})")
                else:
                    breakdown_parts.append(f"{unarmored_bonus} ({ability_name})")  # Already has negative sign
                    
            # Add shield without double signs
            if shield_ac > 0:
                breakdown_parts.append(f"{shield_ac} (shield)")
            
            return {
                'total': final_ac,
                'base': 10,
                'breakdown': f"{unarmored_type}: {' + '.join(breakdown_parts)} = {final_ac}",
                'armor_type': 'unarmored',
                'has_armor': False,
                'has_shield': shield_ac > 0
            }
    
    def _get_standard_armor_ac(self, armor_name: str) -> Optional[int]:
        """Get AC for standard D&D armor by name."""
        armor_ac_table = {
            # Light Armor
            'padded': 11, 'leather': 11, 'studded leather': 12,
            # Medium Armor  
            'hide': 12, 'chain shirt': 13, 'scale mail': 14, 'breastplate': 14, 'half plate': 15,
            # Heavy Armor
            'ring mail': 14, 'chain mail': 16, 'splint': 17, 'plate': 18
        }
        return armor_ac_table.get(armor_name, None)
    
    def _get_armor_type(self, armor_name: str) -> str:
        """Get armor type (light/medium/heavy) by name."""
        light_armor = ['padded', 'leather', 'studded leather']
        medium_armor = ['hide', 'chain shirt', 'scale mail', 'breastplate', 'half plate']
        heavy_armor = ['ring mail', 'chain mail', 'splint', 'plate']
        
        if armor_name in light_armor:
            return 'light'
        elif armor_name in medium_armor:
            return 'medium'
        elif armor_name in heavy_armor:
            return 'heavy'
        else:
            return 'unknown'
    
    def _get_armor_dex_cap(self, armor_type: str) -> Optional[int]:
        """Get dexterity modifier cap for armor type."""
        caps = {
            'light': None,    # No cap
            'medium': 2,      # +2 max
            'heavy': 0,       # +0 max
            'unknown': None   # No cap for unknown
        }
        return caps.get(armor_type)
    
    def _get_hit_points(self, raw_data: Dict[str, Any], context: CalculationContext) -> Dict[str, Any]:
        """Get hit points from context or pre-calculated data using backup original logic."""
        # Try to get from context (would be calculated by HP coordinator)
        if context and hasattr(context, 'metadata') and context.metadata:
            combat_data = context.metadata.get('combat', {})
            if 'hit_points' in combat_data:
                return combat_data['hit_points']
        
        # Use backup original logic: Look for pre-calculated hit_points data
        # Check if hit_points data is available in the raw data (like basic_info.hit_points in original)
        hp_data = raw_data.get('hit_points', {})
        if hp_data and isinstance(hp_data, dict):
            max_hp = hp_data.get('maximum', 1)
            current_hp = hp_data.get('current', max_hp)
            temp_hp = hp_data.get('temporary', 0)
            hit_dice_used = hp_data.get('hit_dice_used', 0)
            
            self.logger.debug(f"Using pre-calculated HP data: current={current_hp}, maximum={max_hp}")
            return {
                'current': current_hp,
                'maximum': max_hp,
                'temporary': temp_hp,
                'hit_dice_used': hit_dice_used
            }
        
        # Also check in combat section of raw data
        combat_data = raw_data.get('combat', {})
        if combat_data and isinstance(combat_data, dict):
            hp_data = combat_data.get('hit_points', {})
            if hp_data and isinstance(hp_data, dict):
                max_hp = hp_data.get('maximum', 1)
                current_hp = hp_data.get('current', max_hp)
                temp_hp = hp_data.get('temporary', 0)
                hit_dice_used = hp_data.get('hit_dice_used', 0)
                
                self.logger.debug(f"Using pre-calculated HP data from combat section: current={current_hp}, maximum={max_hp}")
                return {
                    'current': current_hp,
                    'maximum': max_hp,
                    'temporary': temp_hp,
                    'hit_dice_used': hit_dice_used
                }
        
        # Fallback: basic HP calculation (original v6.0.0 logic preserved as last resort)
        base_hp = raw_data.get('baseHitPoints', 0) or 0
        temp_hp = raw_data.get('temporaryHitPoints', 0) or 0
        removed_hp = raw_data.get('removedHitPoints', 0) or 0
        
        # Check for override HP first (D&D Beyond manual override)
        override_hp = raw_data.get('overrideHitPoints')
        if override_hp is not None:
            # Use override as total HP - no additional calculation needed
            max_hp = override_hp
            self.logger.debug(f"Using overrideHitPoints: {max_hp}")
        else:
            # Calculate HP from base + bonuses + constitution
            bonus_hp = raw_data.get('bonusHitPoints', 0) or 0
            
            self.logger.debug(f"HP components: base={base_hp} (type: {type(base_hp)}), bonus={bonus_hp} (type: {type(bonus_hp)})")
            
            # Add constitution modifier per level (D&D rule) - scraper should calculate this
            classes = raw_data.get('classes', [])
            total_level = sum(cls.get('level', 0) for cls in classes)
            
            # Get constitution modifier from context
            con_modifier = 0
            if context and hasattr(context, 'metadata') and context.metadata:
                abilities_data = context.metadata.get('abilities', {})
                ability_modifiers = abilities_data.get('ability_modifiers', {})
                con_modifier = ability_modifiers.get('constitution', 0) or 0
            
            constitution_hp = con_modifier * total_level
            
            # Note: D&D Beyond's baseHitPoints excludes constitution modifier
            # We need to add it back to get the correct total HP
            max_hp = base_hp + bonus_hp + constitution_hp
            self.logger.debug(f"HP calculation: {base_hp} (base) + {bonus_hp} (bonus) + {constitution_hp} (con * level) = {max_hp}")
        
        # For malformed characters, ensure minimum HP
        if max_hp <= 0:
            # Calculate basic HP based on level and constitution
            classes = raw_data.get('classes', [])
            total_level = sum(cls.get('level', 0) for cls in classes)
            
            # Get constitution modifier from context if available
            con_modifier = 0
            if context and hasattr(context, 'metadata') and context.metadata:
                abilities_data = context.metadata.get('abilities', {})
                ability_modifiers = abilities_data.get('ability_modifiers', {})
                con_modifier = ability_modifiers.get('constitution', 0) or 0
            
            # Basic HP = (level * average hit die) + (level * con modifier)
            # Use d8 hit die as default
            if total_level > 0:
                self.logger.debug(f"Calculating HP: total_level={total_level}, con_modifier={con_modifier} (type: {type(con_modifier)})")
                max_hp = total_level * 5 + total_level * (con_modifier or 0)  # 5 is average of d8+1
            else:
                max_hp = 1 + (con_modifier or 0)  # Minimum 1 HP at level 0
            
            # Ensure HP is never negative
            max_hp = max(1, max_hp)
        
        current_hp = max_hp - removed_hp
        current_hp = max(0, current_hp)  # Current HP can be 0
        
        return {
            'current': current_hp,
            'maximum': max_hp,
            'temporary': temp_hp,
            'hit_dice_used': raw_data.get('hitDiceUsed', 0)
        }
    
    def _calculate_initiative(self, raw_data: Dict[str, Any], ability_modifiers: Dict[str, int]) -> int:
        """Calculate initiative bonus."""
        initiative_bonus = ability_modifiers.get('dexterity', 0)
        
        # Check for initiative bonuses from modifiers
        modifiers = raw_data.get('modifiers', {})
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_initiative_modifier(modifier):
                    bonus = modifier.get('value', 0) or modifier.get('bonus', 0)
                    initiative_bonus += bonus
                    self.logger.debug(f"Initiative bonus from {source_type}: +{bonus}")
        
        return initiative_bonus
    
    def _calculate_speed(self, raw_data: Dict[str, Any]) -> int:
        """Calculate character speed."""
        # Get base speed from race
        base_speed = 30  # Default
        
        race_data = raw_data.get('race', {})
        if race_data:
            race_def = race_data.get('definition', {})
            base_speed = race_def.get('speed', 30)
        
        # Check for speed modifiers
        total_speed = base_speed
        modifiers = raw_data.get('modifiers', {})
        
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_speed_modifier(modifier):
                    bonus = modifier.get('value', 0) or modifier.get('bonus', 0)
                    total_speed += bonus
                    self.logger.debug(f"Speed modifier from {source_type}: +{bonus}")
        
        return max(0, total_speed)
    
    def _get_scraper_attack_actions(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get scraper-provided attack actions from combat data, or generate from equipped weapons."""
        weapon_actions = []
        
        try:
            # Get attack actions from combat section
            combat_data = raw_data.get('combat', {})
            attack_actions = combat_data.get('attack_actions', [])
            
            if isinstance(attack_actions, list) and attack_actions:
                weapon_actions.extend(attack_actions)
                self.logger.debug(f"Found {len(attack_actions)} scraper-provided attack actions")
            else:
                # Use enhanced weapon attack calculator
                enhanced_attacks = self._get_enhanced_weapon_attacks(raw_data)
                if enhanced_attacks:
                    weapon_actions.extend(enhanced_attacks)
                    self.logger.debug(f"Generated {len(enhanced_attacks)} enhanced weapon attacks")
                else:
                    # Fallback to legacy weapon attack generation
                    weapon_actions = self._generate_weapon_attacks(raw_data)
                    self.logger.debug(f"Generated {len(weapon_actions)} weapon attacks from equipped weapons")
            
        except Exception as e:
            self.logger.error(f"Error getting scraper attack actions: {e}")
        
        return weapon_actions
    
    def _get_enhanced_weapon_attacks(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Get weapon attacks using the enhanced weapon attack calculator."""
        try:
            # Transform raw data to format expected by enhanced calculator
            character_data = self._transform_raw_data_for_calculator(raw_data)
            
            # Calculate weapon attacks using enhanced calculator
            result = self.weapon_attack_calculator.calculate(character_data)
            weapon_attacks_data = result.get('weapon_attacks', [])
            
            # Transform WeaponAttack objects to dictionary format for compatibility
            enhanced_attacks = []
            for weapon_attack in weapon_attacks_data:
                attack_dict = {
                    'name': weapon_attack.name,
                    'description': f"{weapon_attack.weapon_type.capitalize()} weapon attack with {weapon_attack.name}. Attack bonus: +{weapon_attack.attack_bonus}. Damage: {weapon_attack.damage_dice} + {weapon_attack.damage_modifier} {weapon_attack.damage_type}.",
                    'type': 'weapon_attack',
                    'attack_type': weapon_attack.weapon_type,
                    'attack_bonus': weapon_attack.attack_bonus,
                    'damage_dice': weapon_attack.damage_dice,
                    'damage_type': weapon_attack.damage_type,
                    'damage_bonus': weapon_attack.damage_modifier,
                    'range': f"{weapon_attack.range_normal}/{weapon_attack.range_long}" if weapon_attack.range_normal else 'Melee',
                    'properties': weapon_attack.properties,
                    'snippet': f'{weapon_attack.weapon_type.capitalize()} Weapon Attack: +{weapon_attack.attack_bonus} to hit, {weapon_attack.damage_dice} + {weapon_attack.damage_modifier} {weapon_attack.damage_type} damage',
                    'breakdown': weapon_attack.breakdown
                }
                enhanced_attacks.append(attack_dict)
            
            return enhanced_attacks
            
        except Exception as e:
            self.logger.error(f"Error using enhanced weapon attack calculator: {e}")
            return []
    
    def _transform_raw_data_for_calculator(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform raw D&D Beyond data to format expected by enhanced calculator."""
        # Get ability modifiers
        ability_modifiers = self._get_ability_modifiers(raw_data, None)
        
        # Transform ability scores to expected format
        ability_scores = {}
        for ability_name, modifier in ability_modifiers.items():
            # Calculate score from modifier (reverse calculation)
            score = (modifier * 2) + 10
            ability_scores[ability_name] = {
                'score': score,
                'modifier': modifier
            }
        
        # Get proficiencies
        proficiencies = self._extract_proficiencies_for_calculator(raw_data)
        
        # Get equipped items
        equipped_items = []
        inventory = raw_data.get('inventory', [])
        for item in inventory:
            if item.get('equipped', False):
                item_def = item.get('definition', {})
                if self._is_weapon(item_def):
                    # Transform weapon data to expected format
                    weapon_type = item_def.get('type', 'simple').lower()
                    # Extract just 'martial' or 'simple' from 'martial weapon' or 'simple weapon'
                    if 'martial' in weapon_type:
                        weapon_category = 'martial'
                    elif 'simple' in weapon_type:
                        weapon_category = 'simple'
                    else:
                        weapon_category = 'simple'  # Default
                    
                    weapon_data = {
                        'name': item_def.get('name', 'Unknown Weapon'),
                        'type': 'weapon',
                        'weapon_category': weapon_category,
                        'weapon_properties': self._transform_weapon_properties(item_def),
                        'damage': self._transform_weapon_damage(item_def),
                        'range': self._transform_weapon_range(item_def)
                    }
                    equipped_items.append(weapon_data)
        
        # Get character level
        character_level = self._get_character_level(raw_data, None)
        
        return {
            'abilities': {
                'ability_scores': ability_scores
            },
            'proficiencies': proficiencies,
            'inventory': {
                'equipped_items': equipped_items
            },
            'character_info': {
                'level': character_level
            }
        }
    
    def _extract_proficiencies_for_calculator(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract weapon proficiencies for the calculator."""
        weapon_proficiencies = []
        
        # Get class-based proficiencies
        classes = raw_data.get('classes', [])
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            
            # Add weapon proficiencies based on class
            if class_name in ['fighter', 'barbarian', 'paladin', 'ranger']:
                weapon_proficiencies.extend([
                    {'name': 'simple weapons'},
                    {'name': 'martial weapons'}
                ])
            elif class_name in ['wizard', 'sorcerer']:
                weapon_proficiencies.append({'name': 'simple weapons'})
            elif class_name in ['bard', 'cleric', 'druid', 'rogue', 'monk', 'warlock']:
                weapon_proficiencies.append({'name': 'simple weapons'})
        
        return {
            'weapon_proficiencies': weapon_proficiencies
        }
    
    def _transform_weapon_properties(self, item_def: Dict[str, Any]) -> List[Dict[str, str]]:
        """Transform weapon properties to expected format."""
        properties = []
        weapon_props = item_def.get('weaponProperties', [])
        
        for prop in weapon_props:
            if isinstance(prop, dict):
                prop_name = prop.get('name', '')
                if prop_name:
                    properties.append({'name': prop_name})
        
        return properties
    
    def _transform_weapon_damage(self, item_def: Dict[str, Any]) -> Dict[str, str]:
        """Transform weapon damage to expected format."""
        damage_data = item_def.get('damage', {})
        return {
            'damage_dice': damage_data.get('diceString', '1d4'),
            'damage_type': item_def.get('damageType', 'bludgeoning')
        }
    
    def _transform_weapon_range(self, item_def: Dict[str, Any]) -> Dict[str, int]:
        """Transform weapon range to expected format."""
        # For now, return empty dict as range handling needs more complex logic
        return {}
    
    def _generate_weapon_attacks(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate weapon attacks from equipped weapons."""
        weapon_attacks = []
        
        try:
            # Get ability modifiers and proficiency bonus
            ability_modifiers = self._get_ability_modifiers(raw_data, None)
            proficiency_bonus = self._get_proficiency_bonus(raw_data, None)
            
            # Get equipped weapons from inventory
            inventory = raw_data.get('inventory', [])
            
            for item in inventory:
                if not item.get('equipped', False):
                    continue
                    
                item_def = item.get('definition', {})
                
                # Check if item is a weapon
                if not self._is_weapon(item_def):
                    continue
                    
                weapon_name = item_def.get('name', 'Unknown Weapon')
                
                # Skip if weapon name contains special markers (True Strike variants)
                if '(True Strike)' in weapon_name:
                    continue
                
                # Determine attack type (melee/ranged)
                attack_type = self._get_weapon_attack_type(item_def)
                
                # Calculate attack bonus
                attack_bonus = self._calculate_weapon_attack_bonus(item_def, ability_modifiers, proficiency_bonus, raw_data)
                
                # Calculate damage
                damage_info = self._calculate_weapon_damage(item_def, ability_modifiers)
                
                # Create weapon attack action
                weapon_attack = {
                    'name': weapon_name,
                    'description': self._create_weapon_description(item_def, attack_bonus, damage_info),
                    'type': 'weapon_attack',
                    'attack_type': attack_type,
                    'attack_bonus': attack_bonus,
                    'damage_dice': damage_info['damage_dice'],
                    'damage_type': damage_info['damage_type'],
                    'damage_bonus': damage_info['damage_bonus'],
                    'range': item_def.get('range', 'Melee'),
                    'properties': self._get_weapon_properties(item_def),
                    'snippet': f'{attack_type.capitalize()} Weapon Attack: +{attack_bonus} to hit, {damage_info["damage_dice"]} + {damage_info["damage_bonus"]} {damage_info["damage_type"]} damage'
                }
                
                weapon_attacks.append(weapon_attack)
                
        except Exception as e:
            self.logger.error(f"Error generating weapon attacks: {e}")
            
        return weapon_attacks
    
    def _is_weapon(self, item_def: Dict[str, Any]) -> bool:
        """Check if an item is a weapon."""
        # Check weapon type
        item_type = item_def.get('type', '').lower()
        if 'weapon' in item_type:
            return True
            
        # Check filter type
        filter_type = item_def.get('filterType', '').lower()
        if filter_type == 'weapon':
            return True
            
        # Check weapon properties
        if item_def.get('weaponProperties'):
            return True
            
        return False
    
    def _get_weapon_attack_type(self, item_def: Dict[str, Any]) -> str:
        """Determine if weapon is melee or ranged."""
        # Check weapon properties for ranged indicators
        properties = item_def.get('weaponProperties', [])
        for prop in properties:
            if isinstance(prop, dict):
                prop_name = prop.get('name', '').lower()
                if 'ammunition' in prop_name or 'thrown' in prop_name:
                    return 'ranged'
        
        # Check weapon type
        weapon_type = item_def.get('type', '').lower()
        if 'ranged' in weapon_type or 'crossbow' in weapon_type or 'bow' in weapon_type:
            return 'ranged'
            
        return 'melee'
    
    def _calculate_weapon_attack_bonus(self, item_def: Dict[str, Any], ability_modifiers: Dict[str, int], proficiency_bonus: int, raw_data: Dict[str, Any]) -> int:
        """Calculate weapon attack bonus."""
        # Determine ability modifier
        attack_type = self._get_weapon_attack_type(item_def)
        
        # Use finesse property if available
        properties = item_def.get('weaponProperties', [])
        is_finesse = any(prop.get('name', '').lower() == 'finesse' for prop in properties if isinstance(prop, dict))
        
        if is_finesse:
            # Use higher of Str or Dex for finesse weapons
            str_mod = ability_modifiers.get('strength', 0)
            dex_mod = ability_modifiers.get('dexterity', 0)
            ability_mod = max(str_mod, dex_mod)
        elif attack_type == 'ranged':
            ability_mod = ability_modifiers.get('dexterity', 0)
        else:
            ability_mod = ability_modifiers.get('strength', 0)
        
        # Check weapon proficiency
        is_proficient = self._is_weapon_proficient(item_def, raw_data)
        prof_bonus = proficiency_bonus if is_proficient else 0
        
        return ability_mod + prof_bonus
    
    def _calculate_weapon_damage(self, item_def: Dict[str, Any], ability_modifiers: Dict[str, int]) -> Dict[str, Any]:
        """Calculate weapon damage."""
        # Get base damage
        damage_dice = item_def.get('damage', {}).get('diceString', '1d4')
        damage_type = item_def.get('damageType', 'bludgeoning')
        
        # Determine ability modifier for damage
        attack_type = self._get_weapon_attack_type(item_def)
        
        # Use finesse property if available
        properties = item_def.get('weaponProperties', [])
        is_finesse = any(prop.get('name', '').lower() == 'finesse' for prop in properties if isinstance(prop, dict))
        
        if is_finesse:
            # Use higher of Str or Dex for finesse weapons
            str_mod = ability_modifiers.get('strength', 0)
            dex_mod = ability_modifiers.get('dexterity', 0)
            damage_bonus = max(str_mod, dex_mod)
        elif attack_type == 'ranged':
            damage_bonus = ability_modifiers.get('dexterity', 0)
        else:
            damage_bonus = ability_modifiers.get('strength', 0)
        
        return {
            'damage_dice': damage_dice,
            'damage_type': damage_type,
            'damage_bonus': damage_bonus
        }
    
    def _is_weapon_proficient(self, item_def: Dict[str, Any], raw_data: Dict[str, Any]) -> bool:
        """Check if character is proficient with weapon."""
        weapon_name = item_def.get('name', '').lower()
        weapon_type = item_def.get('type', '').lower()
        
        # Check class weapon proficiencies
        classes = raw_data.get('classes', [])
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            
            # Simple weapon proficiency for most classes
            if 'simple' in weapon_type:
                if class_name in ['wizard', 'sorcerer', 'bard', 'cleric', 'druid', 'ranger', 'paladin', 'barbarian', 'fighter', 'rogue', 'monk', 'warlock']:
                    return True
            
            # Martial weapon proficiency for martial classes
            if 'martial' in weapon_type:
                if class_name in ['fighter', 'barbarian', 'paladin', 'ranger']:
                    return True
        
        # Check specific weapon proficiencies from race, background, feats
        # This is a simplified check - could be enhanced with modifier parsing
        return False
    
    def _get_weapon_properties(self, item_def: Dict[str, Any]) -> List[str]:
        """Get weapon properties."""
        properties = []
        weapon_props = item_def.get('weaponProperties', [])
        
        for prop in weapon_props:
            if isinstance(prop, dict):
                prop_name = prop.get('name', '')
                if prop_name:
                    properties.append(prop_name)
        
        return properties
    
    def _create_weapon_description(self, item_def: Dict[str, Any], attack_bonus: int, damage_info: Dict[str, Any]) -> str:
        """Create weapon attack description."""
        weapon_name = item_def.get('name', 'Unknown Weapon')
        attack_type = self._get_weapon_attack_type(item_def)
        
        description = f"{attack_type.capitalize()} weapon attack with {weapon_name}. "
        description += f"Attack bonus: +{attack_bonus}. "
        description += f"Damage: {damage_info['damage_dice']} + {damage_info['damage_bonus']} {damage_info['damage_type']}."
        
        return description
    
    def _extract_spell_attacks(self, raw_data: Dict[str, Any], ability_modifiers: Dict[str, int], proficiency_bonus: int) -> List[Dict[str, Any]]:
        """Extract spell attack actions from known/prepared spells only."""
        spell_actions = []
        
        try:
            spells_data = raw_data.get('spells', {})
            spellcasting_data = raw_data.get('classSpells', [])
            
            # Determine primary spellcasting ability
            spellcasting_ability = self._get_spellcasting_ability(raw_data)
            if not spellcasting_ability:
                return spell_actions  # No spellcasting
            
            spell_modifier = ability_modifiers.get(spellcasting_ability, 0)
            spell_attack_bonus = spell_modifier + proficiency_bonus
            spell_save_dc = 8 + proficiency_bonus + spell_modifier
            
            # Process spells from different sources (filtered for prepared/always prepared)
            all_spells = []
            
            # Handle classSpells first
            for class_spell_data in spellcasting_data:
                if isinstance(class_spell_data, dict):
                    class_spells = class_spell_data.get('spells', [])
                    if isinstance(class_spells, list):
                        for spell_data in class_spells:
                            if self._is_spell_known_or_prepared(spell_data, is_class_spell=True):
                                all_spells.append(spell_data)
            
            # Handle spells dict format (by source) - non-class spells
            if isinstance(spells_data, dict):
                for source, spells_list in spells_data.items():
                    if isinstance(spells_list, list):
                        for spell_data in spells_list:
                            if self._is_spell_known_or_prepared(spell_data, is_class_spell=False):
                                all_spells.append(spell_data)
            elif isinstance(spells_data, list):
                for spell_data in spells_data:
                    if self._is_spell_known_or_prepared(spell_data, is_class_spell=False):
                        all_spells.append(spell_data)
            
            # Process spells that can be used as attacks
            for spell in all_spells:
                if not isinstance(spell, dict):
                    continue
                    
                spell_def = spell.get('definition', {})
                spell_name = spell_def.get('name', 'Unknown Spell')
                spell_level = spell_def.get('level', 0)
                
                # Check if spell requires an attack roll
                if self._spell_requires_attack_roll(spell_def):
                    spell_action = {
                        'name': f'{spell_name}',
                        'description': self._create_spell_description(spell_def, spell_attack_bonus, spell_save_dc),
                        'type': 'spell_attack',
                        'spell_level': spell_level,
                        'attack_bonus': spell_attack_bonus,
                        'save_dc': spell_save_dc,
                        'spellcasting_ability': spellcasting_ability,
                        'casting_time': spell_def.get('castingTime', '1 action'),
                        'range': spell_def.get('range', 'Touch'),
                        'duration': spell_def.get('duration', 'Instantaneous'),
                        'snippet': f'Spell Attack: +{spell_attack_bonus} to hit'
                    }
                    
                    spell_actions.append(spell_action)
                    
        except Exception as e:
            self.logger.error(f"Error extracting spell attacks: {e}")
        
        return spell_actions
    
    def _is_spell_known_or_prepared(self, spell_data: Dict[str, Any], is_class_spell: bool = False) -> bool:
        """
        Check if a spell is known or prepared and should be included in combat attacks.
        
        For combat attacks, we only want spells that are actually prepared or always prepared,
        not just known (since knowing a spell doesn't mean you can cast it in combat).
        
        Args:
            spell_data: The spell data dictionary
            is_class_spell: Whether this is a class spell (from classSpells)
            
        Returns:
            True if the spell should be included in combat attacks
        """
        if not isinstance(spell_data, dict):
            return False
        
        is_prepared = spell_data.get('prepared', False)
        is_always_prepared = spell_data.get('alwaysPrepared', False)
        
        # For combat attacks, only include spells that are prepared or always prepared
        # regardless of whether they're class spells or not
        return is_prepared or is_always_prepared
    
    def _calculate_saving_throws(self, raw_data: Dict[str, Any], ability_modifiers: Dict[str, int], proficiency_bonus: int) -> Dict[str, Any]:
        """Calculate saving throw bonuses."""
        saving_throws = {}
        
        # Get save proficiencies
        save_proficiencies = self._get_save_proficiencies(raw_data)
        
        for ability in self.ability_names:
            modifier = ability_modifiers.get(ability, 0)
            
            # Add proficiency bonus if proficient
            if ability in save_proficiencies:
                save_bonus = modifier + proficiency_bonus
                is_proficient = True
            else:
                save_bonus = modifier
                is_proficient = False
            
            saving_throws[ability] = {
                'bonus': save_bonus,
                'modifier': modifier,
                'proficient': is_proficient
            }
        
        return saving_throws
    
    
    
    
    def _get_spellcasting_ability(self, raw_data: Dict[str, Any]) -> Optional[str]:
        """Determine the primary spellcasting ability using backup original logic."""
        # First try to get spellcasting ability from spell data itself (backup original logic)
        spells_data = raw_data.get('spells', {})
        
        # Handle different spell data formats
        all_spells = []
        if isinstance(spells_data, dict):
            for source, spells_list in spells_data.items():
                if isinstance(spells_list, list):
                    all_spells.extend(spells_list)
        elif isinstance(spells_data, list):
            all_spells = spells_data
        
        # Check for spellcasting_ability in spell data
        for spell in all_spells:
            if isinstance(spell, dict):
                spellcasting_ability = spell.get('spellcasting_ability')
                if spellcasting_ability:
                    self.logger.debug(f"Found spellcasting ability from spell data: {spellcasting_ability}")
                    return spellcasting_ability
        
        # Check for pre-calculated spellcasting data in the root
        spellcasting_data = raw_data.get('spellcasting', {})
        if isinstance(spellcasting_data, dict):
            ability = spellcasting_data.get('spellcasting_ability')
            if ability:
                self.logger.debug(f"Found spellcasting ability from spellcasting data: {ability}")
                return ability
        
        # Fallback: Use class-based mapping as before
        classes = raw_data.get('classes', [])
        
        # Common spellcasting ability mappings
        spellcasting_abilities = {
            'wizard': 'intelligence',
            'sorcerer': 'charisma',
            'warlock': 'charisma',
            'bard': 'charisma',
            'cleric': 'wisdom',
            'druid': 'wisdom',
            'ranger': 'wisdom',
            'paladin': 'charisma'
        }
        
        for cls in classes:
            class_def = cls.get('definition', {})
            class_name = class_def.get('name', '').lower()
            
            if class_name in spellcasting_abilities:
                self.logger.debug(f"Found spellcasting ability from class mapping: {spellcasting_abilities[class_name]} for class: {class_name}")
                return spellcasting_abilities[class_name]
        
        return None
    
    def _spell_requires_attack_roll(self, spell_def: Dict[str, Any]) -> bool:
        """Check if a spell requires an attack roll."""
        description = spell_def.get('description', '').lower()
        snippet = spell_def.get('snippet', '').lower()
        
        # Look for attack roll indicators
        attack_indicators = ['ranged spell attack', 'melee spell attack', 'spell attack', 'attack roll']
        
        for indicator in attack_indicators:
            if indicator in description or indicator in snippet:
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
    
    def _is_initiative_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects initiative."""
        sub_type = modifier.get('subType', '').lower()
        return 'initiative' in sub_type
    
    def _is_speed_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects speed."""
        sub_type = modifier.get('subType', '').lower()
        return 'speed' in sub_type or 'movement' in sub_type
    
    def _is_ranged_attack(self, action: Dict[str, Any]) -> bool:
        """Check if an action is a ranged attack."""
        return action.get('attack_type') == 'ranged'
    
    def _is_melee_attack(self, action: Dict[str, Any]) -> bool:
        """Check if an action is a melee attack."""
        return action.get('attack_type') == 'melee'
    
    
    
    def _create_spell_description(self, spell_def: Dict[str, Any], attack_bonus: int, save_dc: int) -> str:
        """Create a descriptive text for spell attacks."""
        spell_name = spell_def.get('name', 'Unknown Spell')
        description = spell_def.get('description', f'Casts {spell_name}')
        
        # Add attack bonus or save DC info if relevant
        if self._spell_requires_attack_roll(spell_def):
            description = f"Spell Attack: +{attack_bonus} to hit. " + description
        elif 'saving throw' in description.lower():
            description = f"Save DC {save_dc}. " + description
        
        return description
    
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """
        Validate that the input data is suitable for this coordinator.
        
        Args:
            raw_data: Raw character data to validate
            
        Returns:
            True if data is valid for this coordinator
        """
        return self._validate_combat_data(raw_data)
    
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
                "initiative_bonus": {"type": "integer"},
                "speed": {"type": "integer", "minimum": 0},
                "armor_class": {"type": "integer", "minimum": 1},
                "hit_points": {
                    "type": "object",
                    "properties": {
                        "current": {"type": "integer"},
                        "maximum": {"type": "integer"},
                        "temporary": {"type": "integer"},
                        "hit_dice_used": {"type": "integer"}
                    }
                },
                "attack_actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "type": {"type": "string"},
                            "attack_bonus": {"type": "integer"},
                            "damage_dice": {"type": "string"},
                            "snippet": {"type": "string"}
                        }
                    }
                },
                "spell_actions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "name": {"type": "string"},
                            "description": {"type": "string"},
                            "type": {"type": "string"},
                            "attack_bonus": {"type": "integer"},
                            "save_dc": {"type": "integer"}
                        }
                    }
                },
                "saving_throws": {
                    "type": "object",
                    "properties": {
                        ability: {
                            "type": "object",
                            "properties": {
                                "bonus": {"type": "integer"},
                                "modifier": {"type": "integer"},
                                "proficient": {"type": "boolean"}
                            }
                        } for ability in self.ability_names
                    }
                },
                "proficiency_bonus": {"type": "integer", "minimum": 2, "maximum": 6},
                "metadata": {"type": "object"}
            },
            "required": [
                "initiative_bonus", "speed", "attack_actions", "spell_actions",
                "saving_throws", "proficiency_bonus"
            ]
        }