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
from ..weapon_attacks import EnhancedWeaponAttackCalculator
from ..armor_class import EnhancedArmorClassCalculator
from ..hit_points import EnhancedHitPointsCalculator
from ..speed import EnhancedSpeedCalculator
from ..action_attacks import ActionAttackExtractor
from ..utils.data_transformer import EnhancedCalculatorDataTransformer

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

        # Initialize enhanced calculators and data transformer
        self.weapon_attack_calculator = EnhancedWeaponAttackCalculator()
        self.action_attack_extractor = ActionAttackExtractor()
        self.armor_class_calculator = EnhancedArmorClassCalculator(config_manager)
        self.hit_points_calculator = EnhancedHitPointsCalculator()
        self.speed_calculator = EnhancedSpeedCalculator()
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
            
            # Calculate initiative bonus and breakdown
            try:
                initiative_bonus, initiative_breakdown = self._calculate_initiative(raw_data, ability_modifiers, proficiency_bonus)
                self.logger.debug(f"Initiative bonus calculated: {initiative_bonus} ({initiative_breakdown})")
            except Exception as e:
                self.logger.error(f"Error calculating initiative: {e}")
                raise
            
            # Calculate speed
            try:
                speed = self._calculate_speed(raw_data, context)
                self.logger.debug(f"Speed calculated: {speed}")
            except Exception as e:
                self.logger.error(f"Error calculating speed: {e}")
                raise
            
            # Get scraper-provided attack data
            weapon_attacks = self._get_scraper_attack_actions(raw_data, context)

            # Extract special abilities (activation type 8 actions)
            special_abilities = self._extract_special_abilities(raw_data)

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
                'initiative_breakdown': initiative_breakdown,
                'speed': speed.get('walking_speed', 30) if isinstance(speed, dict) else speed,  # Legacy format for backward compatibility
                'movement': speed if isinstance(speed, dict) else {'walking_speed': speed, 'climbing_speed': 0, 'swimming_speed': 0, 'flying_speed': 0},  # Full movement data
                'armor_class': armor_class,
                'hit_points': hit_points,
                'attack_actions': weapon_attacks,
                'spell_actions': spell_attacks,
                'special_abilities': special_abilities,
                'all_actions': all_actions,
                'saving_throws': saving_throws,
                'proficiency_bonus': proficiency_bonus,
                'metadata': {
                    'total_actions': len(all_actions),
                    'weapon_attacks': len(weapon_attacks),
                    'spell_attacks': len(spell_attacks),
                    'special_abilities': len(special_abilities),
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

        # Try to get from already-calculated abilities data in raw_data
        if 'abilities' in raw_data:
            abilities = raw_data['abilities']
            if 'ability_modifiers' in abilities:
                self.logger.debug(f"Using pre-calculated ability modifiers from raw_data: {abilities['ability_modifiers']}")
                return abilities['ability_modifiers']
            # Try ability_scores structure
            elif 'ability_scores' in abilities:
                ability_modifiers = {}
                for ability_name, ability_data in abilities['ability_scores'].items():
                    if isinstance(ability_data, dict) and 'modifier' in ability_data:
                        ability_modifiers[ability_name] = ability_data['modifier']
                if ability_modifiers:
                    self.logger.debug(f"Using pre-calculated ability modifiers from ability_scores: {ability_modifiers}")
                    return ability_modifiers

        # Fallback: calculate from raw data stats (base scores only - NOT recommended)
        self.logger.warning("Falling back to raw stats calculation - this may not include bonuses from items/feats!")
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
        """Get armor class using the enhanced AC calculator with fixed armor type mapping."""
        try:
            # Transform data for enhanced calculator
            transformed_data = self.data_transformer.transform_for_enhanced_calculators(raw_data)
            
            # Create calculation context for enhanced calculator
            calc_context = CalculationContext(
                character_id=str(raw_data.get('id', '')),
                rule_version=context.rule_version if context else "2024",
                calculation_mode="standard",
                performance_mode=False,
                validation_enabled=True,
                debug_enabled=context.debug_enabled if context else False
            )
            
            self.logger.debug(f"Using enhanced AC calculator with fixed armor type mapping")
            # Calculate AC using enhanced calculator with transformed data
            result = self.armor_class_calculator.calculate(transformed_data, calc_context)
            self.logger.debug(f"Enhanced AC calculator returned status: {result.status}")
            
            if result.status == CalculationStatus.COMPLETED and result.data:
                ac_data = result.data
                self.logger.debug(f"Enhanced AC calculator result: {ac_data}")
                
                # Extract values from enhanced calculator format
                total_ac = ac_data.get('armor_class', 10)
                ac_breakdown_data = ac_data.get('ac_breakdown', {})
                base_ac = ac_breakdown_data.get('base_ac', 10)
                
                # Create breakdown string
                breakdown_parts = []
                if base_ac > 10:
                    breakdown_parts.append(f"{base_ac} (armor)")
                if ac_breakdown_data.get('dex_bonus', 0) > 0:
                    breakdown_parts.append(f"{ac_breakdown_data['dex_bonus']} (dex)")
                if ac_breakdown_data.get('shield_bonus', 0) > 0:
                    breakdown_parts.append(f"{ac_breakdown_data['shield_bonus']} (shield)")
                if ac_breakdown_data.get('misc_bonus', 0) > 0:
                    breakdown_parts.append(f"{ac_breakdown_data['misc_bonus']} (misc)")
                
                breakdown = f"AC: {' + '.join(breakdown_parts)} = {total_ac}" if breakdown_parts else f"AC: {total_ac}"
                
                # Determine armor type - try to get from raw data
                armor_name = "unknown"
                has_armor = ac_data.get('calculation_method', '').startswith('armored')
                if has_armor:
                    # Try to get specific armor name from equipment scan
                    inventory = raw_data.get("inventory", [])
                    for item in inventory:
                        if isinstance(item, dict) and item.get("equipped", False):
                            definition = item.get("definition", {})
                            if definition.get("armorTypeId") is not None:
                                armor_name = definition.get("name", "unknown")
                                break
                
                return {
                    'total': total_ac,
                    'base': base_ac,
                    'breakdown': breakdown,
                    'armor_type': armor_name,
                    'has_armor': has_armor,
                    'has_shield': ac_breakdown_data.get('shield_bonus', 0) > 0
                }
            else:
                self.logger.warning(f"Enhanced AC calculator failed: {result.errors}")
                # Fall back to manual calculation if enhanced calculator fails
                return self._calculate_ac_primary(raw_data, context)

        except Exception as e:
            self.logger.error(f"Error using enhanced AC calculator: {e}")
            # Fall back to manual calculation
            return self._calculate_ac_primary(raw_data, context)
    
    def _calculate_ac_primary(self, raw_data: Dict[str, Any], context: CalculationContext = None) -> Dict[str, Any]:
        """Primary AC calculation with proper armor, shield, and dex cap handling."""
        self.logger.debug("Using primary AC calculation")

        # Get ability modifiers
        ability_modifiers = self._get_ability_modifiers(raw_data, context)
        dex_mod = ability_modifiers.get('dexterity', 0) or 0
        con_mod = ability_modifiers.get('constitution', 0) or 0
        wis_mod = ability_modifiers.get('wisdom', 0) or 0
        
        # Check equipment for armor and shields - try multiple data paths
        inventory = raw_data.get('inventory', [])
        if not inventory:
            # Try alternative equipment structure
            equipment = raw_data.get('equipment', {})
            inventory = equipment.get('basic_equipment', [])
        
        # Try enhanced_equipment structure (v6.0.0)
        if not inventory:
            enhanced_equipment = raw_data.get('enhanced_equipment', [])
            if enhanced_equipment:
                inventory = enhanced_equipment
                self.logger.debug("Using enhanced_equipment data for AC calculation")
        
        # Also check if there's pre-calculated combat equipment data we can use
        combat_data = raw_data.get('combat', {})
        combat_equipment = combat_data.get('equipment', [])
        if combat_equipment and not inventory:
            inventory = combat_equipment
            self.logger.debug("Using combat equipment data for AC calculation")
        
        armor_ac = 0
        armor_type = None
        armor_name = None
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
                
                # Method 4: For enhanced armor, add enhancement bonus to API AC
                if ac_value is not None and ac_value > 0:
                    # Check for enhancement bonus in the item name
                    base_name, enhancement_bonus = self._parse_enhanced_armor_name(item_name)
                    if enhancement_bonus > 0:
                        ac_value += enhancement_bonus
                        self.logger.debug(f"Applied enhancement bonus: {ac_value - enhancement_bonus} + {enhancement_bonus} = {ac_value}")
                
                if ac_value and ac_value > armor_ac:
                    armor_ac = ac_value
                    armor_type = self._get_armor_type(item_name)
                    armor_name = item_name
                    self.logger.debug(f"Found armor: {item_name} AC {ac_value} type {armor_type} (will display as '{armor_name}')")
            
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
        
        self.logger.debug(f"Final equipment scan results: armor_ac={armor_ac}, armor_name={armor_name}, armor_type={armor_type}, shield_ac={shield_ac}")
        
        # Calculate final AC
        if armor_ac > 0:
            # Wearing armor: apply dex cap based on armor type
            max_dex = self._get_armor_dex_cap(armor_type)
            capped_dex = min(dex_mod, max_dex) if max_dex is not None else dex_mod
            
            # Check for fighting style bonuses (like Defense)
            fighting_style_bonus = self._get_fighting_style_ac_bonus(raw_data)
            self.logger.debug(f"Fighting style bonus calculated: {fighting_style_bonus}")
            
            final_ac = armor_ac + capped_dex + shield_ac + fighting_style_bonus
            self.logger.debug(f"Armored AC: {armor_ac} (armor) + {capped_dex} (dex, capped at {max_dex}) + {shield_ac} (shield) + {fighting_style_bonus} (fighting style) = {final_ac}")
            
            # Create structured result for armored AC - format without double signs
            breakdown_parts = [f"{armor_ac} (armor)"]
            if capped_dex > 0:
                breakdown_parts.append(f"{capped_dex} (dex)")
            elif capped_dex < 0:
                breakdown_parts.append(f"{capped_dex} (dex)")  # Already has negative sign
            if shield_ac > 0:
                breakdown_parts.append(f"{shield_ac} (shield)")
            if fighting_style_bonus > 0:
                breakdown_parts.append(f"{fighting_style_bonus} (fighting style)")
            
            return {
                'total': final_ac,
                'base': armor_ac,  # Base armor AC instead of 10
                'breakdown': f"AC: {' + '.join(breakdown_parts)}",
                'armor_type': armor_name or armor_type or 'unknown',
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
            
            # Check for magic item AC bonuses (like Cloak of Protection)
            magic_ac_data = self._get_magic_item_ac_bonus(raw_data)
            magic_ac_bonus = magic_ac_data['total']
            magic_items = magic_ac_data['items']
            self.logger.debug(f"Magic item AC bonus: {magic_ac_bonus} from {magic_items}")

            final_ac = base_ac + unarmored_bonus + shield_ac + magic_ac_bonus
            self.logger.debug(f"Unarmored AC: {base_ac} (base+dex) + {unarmored_bonus} (unarmored) + {shield_ac} (shield) + {magic_ac_bonus} (magic) = {final_ac}")

            # Create breakdown
            breakdown_parts = []

            # Base armor value
            breakdown_parts.append("10")

            # Add dexterity bonus
            if dex_mod != 0:
                sign = "+" if dex_mod > 0 else ""
                breakdown_parts.append(f"{sign}{dex_mod} Dex")

            # Add unarmored defense bonus
            if unarmored_bonus != 0:
                sign = "+" if unarmored_bonus > 0 else ""
                breakdown_parts.append(f"{sign}{unarmored_bonus} Unarmored Defense")

            # Add shield
            if shield_ac > 0:
                breakdown_parts.append(f"+{shield_ac} Shield")

            # Add magic item bonuses with item names
            for item in magic_items:
                breakdown_parts.append(f"+{item['bonus']} {item['name']}")

            return {
                'total': final_ac,
                'base': 10,
                'breakdown': ' | '.join(breakdown_parts),
                'armor_type': 'unarmored',
                'has_armor': False,
                'has_shield': shield_ac > 0
            }
    
    def _get_standard_armor_ac(self, armor_name: str) -> Optional[int]:
        """Get AC for standard D&D armor by name, handling enhanced armor like 'Chain Mail, +1'."""
        if not armor_name:
            return None
        
        # Parse enhanced armor name
        base_name, enhancement_bonus = self._parse_enhanced_armor_name(armor_name)
        
        armor_ac_table = {
            # Light Armor
            'padded': 11, 'leather': 11, 'studded leather': 12,
            # Medium Armor  
            'hide': 12, 'chain shirt': 13, 'scale mail': 14, 'breastplate': 14, 'half plate': 15,
            # Heavy Armor
            'ring mail': 14, 'chain mail': 16, 'splint': 17, 'plate': 18
        }
        
        base_ac = armor_ac_table.get(base_name.lower(), None)
        if base_ac is not None:
            total_ac = base_ac + enhancement_bonus
            if enhancement_bonus > 0:
                self.logger.debug(f"Enhanced armor: {base_name} (base AC {base_ac}) + {enhancement_bonus} = {total_ac}")
            return total_ac
        
        return None
    
    def _parse_enhanced_armor_name(self, armor_name: str) -> tuple[str, int]:
        """
        Parse armor name to extract base armor and enhancement bonus.
        
        Args:
            armor_name: Full armor name (e.g., "Chain Mail, +1", "Plate +2")
            
        Returns:
            Tuple of (base_armor_name, enhancement_bonus)
        """
        if not armor_name:
            return "", 0
        
        import re
        
        # Pattern to match enhancement bonuses like "+1", "+2", etc.
        # Handles formats like "Chain Mail, +1", "Plate +2", "Armor, +3"
        enhancement_pattern = r'[,\s]*\+(\d+)(?:\s|$)'
        
        match = re.search(enhancement_pattern, armor_name)
        if match:
            enhancement_bonus = int(match.group(1))
            # Remove the enhancement part to get base armor name
            base_name = re.sub(enhancement_pattern, '', armor_name).strip()
            # Remove trailing comma if present
            base_name = base_name.rstrip(',').strip()
        else:
            base_name = armor_name.strip()
            enhancement_bonus = 0
        
        return base_name, enhancement_bonus
    
    def _get_armor_type(self, armor_name: str) -> str:
        """Get armor type (light/medium/heavy) by name, handling enhanced armor."""
        if not armor_name:
            return 'unknown'
        
        # Parse enhanced armor name to get base name
        base_name, _ = self._parse_enhanced_armor_name(armor_name)
        base_name_lower = base_name.lower()
        
        light_armor = ['padded', 'leather', 'studded leather']
        medium_armor = ['hide', 'chain shirt', 'scale mail', 'breastplate', 'half plate']
        heavy_armor = ['ring mail', 'chain mail', 'splint', 'plate']
        
        if base_name_lower in light_armor:
            return 'light'
        elif base_name_lower in medium_armor:
            return 'medium'
        elif base_name_lower in heavy_armor:
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
    
    def _get_fighting_style_ac_bonus(self, raw_data: Dict[str, Any]) -> int:
        """
        Get AC bonus from fighting styles like Defense.

        Args:
            raw_data: Character data from D&D Beyond

        Returns:
            AC bonus from fighting styles
        """
        fighting_style_bonus = 0

        # Check feats for fighting style bonuses - feats are at root level
        feats_data = raw_data.get('feats', [])
        self.logger.debug(f"Fighting style detection - found {len(feats_data)} feats")

        for feat in feats_data:
            if isinstance(feat, dict):
                # Get feat name from definition
                definition = feat.get('definition', {})
                feat_name = definition.get('name', '').lower()
                description = definition.get('description', '').lower()
                self.logger.debug(f"Checking feat: {feat_name}")

                # Check for Defense fighting style
                if 'defense' in feat_name and 'fighting style' in description:
                    # Defense gives +1 AC when wearing armor
                    fighting_style_bonus += 1
                    self.logger.debug("Defense fighting style bonus: +1 AC")

                # Check for other AC-affecting fighting styles or feats
                elif '+1' in description and 'armor class' in description:
                    fighting_style_bonus += 1
                    self.logger.debug(f"AC bonus from {feat_name}: +1")

        self.logger.debug(f"Fighting style bonus calculated: {fighting_style_bonus}")
        return fighting_style_bonus

    def _get_magic_item_ac_bonus(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get AC bonus from magic items like Cloak of Protection, Ring of Protection, etc.

        Args:
            raw_data: Character data from D&D Beyond

        Returns:
            Dict with 'total' (int) and 'items' (list of dicts with 'name' and 'bonus')
        """
        magic_ac_bonus = 0
        magic_items = []

        # Check equipment for AC-boosting magic items
        inventory = raw_data.get('inventory', [])
        if not inventory:
            equipment = raw_data.get('equipment', {})
            inventory = equipment.get('basic_equipment', [])

        self.logger.debug(f"Scanning {len(inventory)} items for magic AC bonuses")

        # Common magic items that provide AC bonuses
        # Note: Stone of Good Luck provides +1 to ability checks and saves, NOT AC
        ac_bonus_items = {
            'cloak of protection': 1,
            'ring of protection': 1,
            'ioun stone of protection': 1,
            'defender': 3,  # Can vary
            'bracers of defense': 2,  # AC = 10 + DEX + bracers (2)
        }

        for item in inventory:
            if not isinstance(item, dict):
                continue

            # Only check equipped items
            if not item.get('equipped', False):
                continue

            # Get item name from either direct property or nested definition
            item_name = item.get('name', '')
            item_def = item.get('definition', {})
            if not item_name:
                item_name = item_def.get('name', '')
            item_name_lower = item_name.lower()

            # Check if item requires attunement - check both locations
            requires_attunement = (
                item.get('requires_attunement', False) or
                item.get('requiresAttunement', False) or
                item_def.get('requiresAttunement', False) or
                item_def.get('canAttune', False)
            )
            is_attuned = item.get('attuned', False) or item.get('isAttuned', False)

            # Skip items that require attunement but aren't attuned
            if requires_attunement and not is_attuned:
                self.logger.debug(f"Skipping {item_name} - requires attunement but not attuned")
                continue

            self.logger.debug(f"Checking magic item: {item_name} (attuned: {is_attuned}, requires: {requires_attunement})")

            # Check for known AC bonus items
            found_bonus = False
            for magic_item_name, bonus in ac_bonus_items.items():
                if magic_item_name in item_name_lower:
                    magic_ac_bonus += bonus
                    magic_items.append({'name': item_name, 'bonus': bonus})
                    self.logger.debug(f"Found AC bonus from {item_name}: +{bonus}")
                    found_bonus = True
                    break

            # Also check the description for AC bonuses - check both locations
            if not found_bonus:
                description = item.get('description', '') or item_def.get('description', '')
                description_lower = description.lower()

                # Look for various AC bonus patterns using regex
                if description_lower:
                    import re
                    # Match patterns like "+1 bonus to armor class" or "+2 bonus to AC"
                    bonus_match = re.search(r'\+(\d+)\s+bonus to (?:armor class|ac)', description_lower)
                    if bonus_match:
                        bonus_value = int(bonus_match.group(1))
                        magic_ac_bonus += bonus_value
                        magic_items.append({'name': item_name, 'bonus': bonus_value})
                        self.logger.debug(f"Found AC bonus from {item_name} description: +{bonus_value}")

        self.logger.debug(f"Total magic item AC bonus: {magic_ac_bonus} from {len(magic_items)} items")
        return {'total': magic_ac_bonus, 'items': magic_items}
    
    def _get_hit_points(self, raw_data: Dict[str, Any], context: CalculationContext) -> Dict[str, Any]:
        """Get hit points from context or calculate using enhanced calculator with fallback."""
        # Try enhanced calculator first
        try:
            self.logger.debug("Attempting to use enhanced hit points calculator")
            transformed_data = self.data_transformer.transform_for_enhanced_calculators(raw_data)
            enhanced_result = self.hit_points_calculator.calculate(transformed_data, context)
            
            if enhanced_result.status == CalculationStatus.COMPLETED:
                self.logger.info("Successfully used enhanced hit points calculator")
                enhanced_data = enhanced_result.data
                return {
                    'current': enhanced_data.get('current_hp', 1),
                    'maximum': enhanced_data.get('max_hp', 1),
                    'temporary': enhanced_data.get('temp_hp', 0),
                    'hit_dice_used': enhanced_data.get('hit_dice_used', 0),
                    'hit_dice_total': enhanced_data.get('total_hit_dice', []),
                    'calculation_method': 'enhanced'
                }
            else:
                self.logger.debug(f"Enhanced calculator needs additional data: {enhanced_result.errors}")
                
        except Exception as e:
            self.logger.debug(f"Enhanced calculator unavailable, using alternative calculation: {str(e)}")
        
        # Alternative calculation using available data sources
        self.logger.debug("Using comprehensive hit points calculation")
        
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
            
            # Add Draconic Resilience bonus for Draconic Sorcerers
            draconic_bonus = self._get_draconic_resilience_bonus(raw_data)
            max_hp += draconic_bonus
            
            self.logger.debug(f"HP calculation: {base_hp} (base) + {bonus_hp} (bonus) + {constitution_hp} (con * level) + {draconic_bonus} (draconic) = {max_hp}")
        
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
    
    def _calculate_initiative(self, raw_data: Dict[str, Any], ability_modifiers: Dict[str, int], proficiency_bonus: int = 2) -> tuple:
        """Calculate initiative bonus and breakdown.

        Args:
            raw_data: Raw character data from D&D Beyond
            ability_modifiers: Calculated ability modifiers
            proficiency_bonus: Character's proficiency bonus

        Returns:
            tuple: (initiative_bonus: int, breakdown: str)
        """
        dex_mod = ability_modifiers.get('dexterity', 0)
        initiative_bonus = dex_mod

        # Track breakdown components as "Label +N" pairs
        breakdown_parts = [f"Dex {dex_mod:+d}"]

        # Check for initiative bonuses from modifiers
        modifiers = raw_data.get('modifiers', {})
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue

            for modifier in modifier_list:
                if self._is_initiative_modifier(modifier):
                    bonus = modifier.get('value', 0) or modifier.get('bonus', 0)
                    bonus_types = modifier.get('bonusTypes', [])

                    # bonusTypes [1] means proficiency bonus (e.g. Alert feat)
                    if 1 in bonus_types and not bonus:
                        bonus = proficiency_bonus
                        source_name = self._get_modifier_source_name(raw_data, modifier, source_type)
                        initiative_bonus += bonus
                        breakdown_parts.append(f"{source_name} {bonus:+d}")
                        self.logger.debug(f"Initiative proficiency bonus from {source_type}: +{bonus}")
                    elif bonus != 0:
                        source_name = modifier.get('friendlySubtypeName') or modifier.get('friendlyTypeName') or source_type
                        initiative_bonus += bonus
                        breakdown_parts.append(f"{source_name} {bonus:+d}")
                        self.logger.debug(f"Initiative bonus from {source_type}: +{bonus}")

        breakdown = ", ".join(breakdown_parts)

        return initiative_bonus, breakdown

    def _get_modifier_source_name(self, raw_data: Dict[str, Any], modifier: Dict[str, Any], source_type: str) -> str:
        """Look up the source feat/feature name for a modifier."""
        component_id = modifier.get('componentId')
        if component_id and source_type == 'feat':
            # Look up the feat name from the feats list
            for feat in raw_data.get('feats', []):
                if isinstance(feat, dict):
                    defn = feat.get('definition', {})
                    if isinstance(defn, dict) and defn.get('id') == component_id:
                        return defn.get('name', 'Feat')
        return modifier.get('friendlySubtypeName') or modifier.get('friendlyTypeName') or source_type
    
    def _calculate_speed(self, raw_data: Dict[str, Any], context: CalculationContext) -> Dict[str, Any]:
        """Calculate character speed using enhanced calculator with fallback.

        Args:
            raw_data: Raw character data
            context: Calculation context with rule version info

        Returns:
            Dict with keys: walking_speed, climbing_speed, swimming_speed, flying_speed, etc.
        """
        # Try enhanced calculator first
        try:
            self.logger.debug("Attempting to use enhanced speed calculator")
            transformed_data = self.data_transformer.transform_for_enhanced_calculators(raw_data)
            enhanced_result = self.speed_calculator.calculate(transformed_data, context)

            if enhanced_result.status == CalculationStatus.COMPLETED:
                self.logger.info("Successfully used enhanced speed calculator")
                enhanced_data = enhanced_result.data
                # Return all movement speeds from enhanced calculator
                return {
                    'walking_speed': enhanced_data.get('walking_speed', 30),
                    'climbing_speed': enhanced_data.get('climbing_speed', 0),
                    'swimming_speed': enhanced_data.get('swimming_speed', 0),
                    'flying_speed': enhanced_data.get('flying_speed', 0),
                    'burrowing_speed': enhanced_data.get('burrowing_speed', 0),
                    'hover': enhanced_data.get('hover', False),
                    'speed_breakdown': enhanced_data.get('speed_breakdown', {}),
                    'special_movement': enhanced_data.get('special_movement', [])
                }
            else:
                self.logger.warning(f"Enhanced speed calculator failed: {enhanced_result.errors}")

        except Exception as e:
            self.logger.warning(f"Enhanced speed calculator failed, falling back to legacy: {str(e)}")
        
        # Fallback to legacy calculation
        self.logger.debug("Using legacy speed calculation")

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

        # Parse climbing speed from racial traits
        climbing_speed = 0
        race_data = raw_data.get('race', {})
        if race_data:
            racial_traits = race_data.get('racialTraits', [])
            for trait in racial_traits:
                trait_def = trait.get('definition', {})
                trait_name = trait_def.get('name', '').lower()

                if trait_name == 'speed':
                    snippet = trait_def.get('snippet', '').lower()
                    description = trait_def.get('description', '').lower()
                    text = f'{snippet} {description}'

                    if 'climbing speed' in text:
                        if 'equal to your walking speed' in text or 'equal to walking speed' in text:
                            climbing_speed = total_speed  # Equal to walking speed (with bonuses)
                            self.logger.debug(f"Climbing speed from race: {climbing_speed}")
                        else:
                            # Try to parse explicit value
                            import re
                            match = re.search(r'climbing speed (?:of )?(\d+)', text)
                            if match:
                                climbing_speed = int(match.group(1))
                                self.logger.debug(f"Climbing speed from race: {climbing_speed}")

        # Return dict format for consistency with enhanced calculator
        return {
            'walking_speed': max(0, total_speed),
            'climbing_speed': climbing_speed,
            'swimming_speed': 0,
            'flying_speed': 0,
            'burrowing_speed': 0,
            'hover': False,
            'speed_breakdown': {},
            'special_movement': []
        }
    
    def _get_scraper_attack_actions(self, raw_data: Dict[str, Any], context: Optional[CalculationContext] = None) -> List[Dict[str, Any]]:
        """Get scraper-provided attack actions from combat data, or generate from equipped weapons and actions."""
        weapon_actions = []

        try:
            # Get attack actions from combat section
            combat_data = raw_data.get('combat', {})
            attack_actions = combat_data.get('attack_actions', [])

            if isinstance(attack_actions, list) and attack_actions:
                weapon_actions.extend(attack_actions)
                self.logger.debug(f"Found {len(attack_actions)} scraper-provided attack actions")
            else:
                # Extract action-based attacks (monk unarmed strikes, racial attacks, etc.)
                action_attacks = self._get_action_attacks(raw_data, context)
                if action_attacks:
                    weapon_actions.extend(action_attacks)
                    self.logger.debug(f"Extracted {len(action_attacks)} attacks from actions")

                # Use enhanced weapon attack calculator for equipped weapons
                enhanced_attacks = self._get_enhanced_weapon_attacks(raw_data)
                if enhanced_attacks:
                    weapon_actions.extend(enhanced_attacks)
                    self.logger.debug(f"Generated {len(enhanced_attacks)} enhanced weapon attacks")
                else:
                    # Fallback to legacy weapon attack generation
                    legacy_attacks = self._generate_weapon_attacks(raw_data)
                    weapon_actions.extend(legacy_attacks)
                    self.logger.debug(f"Generated {len(legacy_attacks)} weapon attacks from equipped weapons")

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

    def _get_action_attacks(self, raw_data: Dict[str, Any], context: Optional[CalculationContext] = None) -> List[Dict[str, Any]]:
        """Extract attack actions from D&D Beyond actions (monk unarmed strikes, racial attacks, etc.)."""
        try:
            # Get calculated ability scores from context
            calculated_ability_scores = {}
            if context and hasattr(context, 'metadata') and context.metadata:
                abilities_data = context.metadata.get('abilities', {})
                ability_scores_data = abilities_data.get('ability_scores', {})
                if ability_scores_data:
                    # Extract just the score values
                    for ability_name, ability_info in ability_scores_data.items():
                        if isinstance(ability_info, dict) and 'score' in ability_info:
                            calculated_ability_scores[ability_name] = ability_info['score']

            # If ability scores not in context, log warning and return empty list
            if not calculated_ability_scores:
                self.logger.warning("Calculated ability scores not available in context - cannot extract action attacks")
                return []

            # Use action attack extractor to get attacks from actions
            action_attacks = self.action_attack_extractor.extract_attacks(raw_data, calculated_ability_scores)

            # Convert ActionAttack objects to dictionary format
            attack_dicts = []
            for action_attack in action_attacks:
                # Format range string
                if action_attack.attack_type == 'ranged' and action_attack.range_normal:
                    if action_attack.range_long:
                        range_str = f"{action_attack.range_normal}/{action_attack.range_long} ft"
                    else:
                        range_str = f"{action_attack.range_normal} ft"
                elif action_attack.range_normal:
                    range_str = f"{action_attack.range_normal} ft reach"
                else:
                    range_str = "Melee"

                # Format damage string
                if action_attack.damage_bonus >= 0:
                    damage_str = f"{action_attack.damage_dice} + {action_attack.damage_bonus}"
                else:
                    damage_str = f"{action_attack.damage_dice} - {abs(action_attack.damage_bonus)}"

                attack_dict = {
                    'name': action_attack.name,
                    'description': action_attack.description,
                    'type': 'action_attack',
                    'attack_type': action_attack.attack_type,
                    'activation_type': action_attack.activation_type,
                    'attack_bonus': action_attack.attack_bonus,
                    'damage_dice': action_attack.damage_dice,
                    'damage_type': action_attack.damage_type,
                    'damage_bonus': action_attack.damage_bonus,
                    'range': range_str,
                    'snippet': f'{action_attack.attack_type.capitalize()} Attack ({action_attack.activation_type.replace("_", " ").title()}): +{action_attack.attack_bonus} to hit, {damage_str} {action_attack.damage_type} damage',
                    'source': action_attack.source,
                    'uses_martial_arts': action_attack.uses_martial_arts
                }
                attack_dicts.append(attack_dict)

            return attack_dicts

        except Exception as e:
            self.logger.error(f"Error extracting action attacks: {e}")
            return []

    def _extract_special_abilities(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract special abilities (activation type 8) from character actions.

        These are special abilities like Sneak Attack, Uncanny Metabolism, Feline Agility, etc.
        that appear in D&D Beyond's "Other" actions section.

        Args:
            raw_data: Raw D&D Beyond character data

        Returns:
            List of special ability dictionaries
        """
        try:
            actions_data = raw_data.get('actions', {})
            if not actions_data:
                return []

            special_abilities = []

            # Extract special abilities (activation type 8) from all sources
            for source_type in ['class', 'race', 'feat', 'item']:
                action_list = actions_data.get(source_type, [])
                if not isinstance(action_list, list):
                    continue

                for action in action_list:
                    activation = action.get('activation', {})
                    activation_type = activation.get('activationType')

                    # Filter for activation type 8 (special abilities for PCs)
                    if activation_type == 8:
                        name = action.get('name', 'Unknown')
                        snippet = action.get('snippet', '')
                        description = action.get('description', snippet)

                        # Process snippet to replace D&D Beyond template variables
                        if snippet:
                            snippet = self._process_snippet_templates(snippet, raw_data)

                        # Get activation cost/type
                        activation_name = activation.get('activationTypeName', 'Special')

                        # Get limited use information
                        limited_use = action.get('limitedUse')
                        uses_info = {}
                        if limited_use:
                            max_uses = limited_use.get('maxUses')
                            reset_type = limited_use.get('resetType')

                            reset_map = {
                                1: 'Short Rest',
                                2: 'Long Rest',
                                3: 'Day',
                                4: 'Movement',  # Feline Agility
                            }

                            if max_uses:
                                uses_info = {
                                    'max_uses': max_uses,
                                    'reset_type': reset_map.get(reset_type, 'Unknown'),
                                    'number_used': limited_use.get('numberUsed', 0)
                                }

                        ability_dict = {
                            'name': name,
                            'snippet': snippet,
                            'description': description,
                            'activation': activation_name,
                            'uses': uses_info,
                            'source': source_type
                        }
                        special_abilities.append(ability_dict)
                        self.logger.debug(f"Extracted special ability: {name} from {source_type}")

            return special_abilities

        except Exception as e:
            self.logger.error(f"Error extracting special abilities: {e}")
            return []

    def _process_snippet_templates(self, snippet: str, raw_data: Dict[str, Any]) -> str:
        """
        Process D&D Beyond template variables in snippets.

        Replaces templates like {{{(classlevel/2)@roundup}}d6 with actual values.

        Args:
            snippet: The snippet text with potential templates
            raw_data: Raw character data for context (class level, etc.)

        Returns:
            Processed snippet with templates replaced
        """
        import re
        import math

        try:
            # Get total class level
            classes = raw_data.get('classes', [])
            total_level = sum(cls.get('level', 0) for cls in classes) or 1

            # Find all template patterns like {{(classlevel/2)@roundup}} or {{{...}}}
            # Pattern: {{ or {{{ followed by expression, followed by }} or }}}
            # Match both double and triple braces
            template_pattern = r'\{\{+([^}]+)\}\}+'

            def replace_template(match):
                expression = match.group(1)

                # Replace classlevel with actual level
                expression = expression.replace('classlevel', str(total_level))

                # Handle @roundup modifier
                if '@roundup' in expression:
                    expression = expression.replace('@roundup', '')
                    try:
                        # Evaluate the expression
                        result = eval(expression, {"__builtins__": {}}, {})
                        # Round up
                        result = math.ceil(result)
                        return str(int(result))
                    except:
                        return match.group(0)  # Return original if evaluation fails
                else:
                    try:
                        result = eval(expression, {"__builtins__": {}}, {})
                        return str(int(result))
                    except:
                        return match.group(0)

            # Replace all templates
            processed = re.sub(template_pattern, replace_template, snippet)
            return processed

        except Exception as e:
            self.logger.warning(f"Error processing snippet templates: {e}")
            return snippet

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
    
    def _get_draconic_resilience_bonus(self, raw_data: Dict[str, Any]) -> int:
        """
        Calculate HP bonus from Draconic Resilience feature.
        
        Draconic Resilience (Level 3): +3 HP + 1 HP per additional Sorcerer level beyond 3rd
        
        Args:
            raw_data: Raw character data from D&D Beyond
            
        Returns:
            HP bonus from Draconic Resilience (0 if not applicable)
        """
        bonus = 0
        
        # Check classes for Draconic Sorcerer
        classes = raw_data.get('classes', [])
        for class_data in classes:
            class_name = class_data.get('definition', {}).get('name', '').lower()
            class_level = class_data.get('level', 1)
            
            # Only check Sorcerers level 3+
            if 'sorcerer' in class_name and class_level >= 3:
                subclass = class_data.get('subclassDefinition', {}).get('name', '')
                if 'draconic' in subclass.lower():
                    # Draconic Resilience: +3 HP at level 3, +1 HP per additional level
                    bonus = 3 + (class_level - 3)
                    self.logger.debug(f"Found Draconic Resilience: Level {class_level} Sorcerer gets +{bonus} HP")
                    break
        
        return bonus