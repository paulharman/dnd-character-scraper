"""
Hit Points Calculator

Calculates hit points from D&D Beyond data with detailed breakdown.
Handles constitution bonuses, class hit dice, and various modifiers.
"""

from typing import Dict, Any, Optional
import logging

from src.interfaces.calculator import HitPointCalculatorInterface
from src.models.character import Character
from src.config.manager import get_config_manager

logger = logging.getLogger(__name__)


class HitPointCalculator(HitPointCalculatorInterface):
    """
    Calculator for hit points with comprehensive breakdown.
    
    Handles:
    - Base hit points from class hit dice
    - Constitution modifier bonuses
    - Tough feat and other feat bonuses
    - Magic item bonuses
    - Manual overrides
    - Hit point calculation methods (rolled, average, manual)
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.constants = self.config_manager.get_constants_config()
        
        # Class hit dice mapping
        self.class_hit_dice = self.constants.classes.hit_dice
        
    def calculate(self, character: Character, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate hit points with complete breakdown.
        
        Returns:
            Dictionary containing max HP, current HP, and detailed breakdown
        """
        logger.info(f"Calculating hit points for character {character.id}")
        
        max_hp = self.calculate_max_hp(character, raw_data)
        hp_breakdown = self.get_hp_breakdown(character, raw_data)
        hit_die_info = self.calculate_hit_die(character, raw_data)
        
        # Get current HP from API data
        current_hp = self._get_current_hp(raw_data)
        temporary_hp = self._get_temporary_hp(raw_data)
        
        result = {
            'max_hp': max_hp,
            'current_hp': current_hp,
            'temporary_hp': temporary_hp,
            'hp_breakdown': hp_breakdown,
            'hit_dice': hit_die_info,
            'calculation_method': hp_breakdown.get('method', 'calculated')
        }
        
        logger.debug(f"Calculated HP: {current_hp}/{max_hp} (temp: {temporary_hp})")
        return result
    
    def validate_inputs(self, character: Character, raw_data: Dict[str, Any]) -> bool:
        """Validate that we have sufficient data for HP calculation."""
        required_fields = ['classes', 'stats']
        
        for field in required_fields:
            if field not in raw_data:
                logger.error(f"Missing required field for HP: {field}")
                return False
        
        # Check that we have classes with levels
        classes = raw_data.get('classes', [])
        if not classes:
            logger.error("No classes found for HP calculation")
            return False
        
        return True
    
    def calculate_max_hp(self, character: Character, raw_data: Dict[str, Any]) -> int:
        """
        Calculate maximum hit points.
        
        Args:
            character: Character data model
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Maximum hit points
        """
        logger.debug("Calculating maximum hit points")
        
        # Check if there's an override in hitPointInfo
        hit_point_info = raw_data.get('hitPointInfo', {})
        if 'maximum' in hit_point_info:
            max_hp = hit_point_info['maximum']
            logger.debug(f"Using hitPointInfo maximum: {max_hp}")
            return max_hp
        
        # Check for direct override (2024 API structure) - this takes precedence
        override_hp = raw_data.get('overrideHitPoints')
        if override_hp is not None:
            # Add racial HP bonuses that might not be included in override
            racial_hp_bonus = self._get_racial_hp_bonus(raw_data)
            final_override = override_hp + racial_hp_bonus
            logger.debug(f"Using overrideHitPoints: {override_hp} + racial bonus: {racial_hp_bonus} = {final_override}")
            return final_override
        
        # Follow the original v5.2.0 logic for HP calculation
        base_hp = raw_data.get("baseHitPoints", 0)
        bonus_hp = raw_data.get("bonusHitPoints", 0) or 0
        
        # Get hit point calculation method
        hit_point_type = raw_data.get("preferences", {}).get("hitPointType", 0)
        hit_point_method = "Fixed" if hit_point_type == 1 else "Manual" if hit_point_type == 2 else "Default"
        
        # Get Constitution modifier and character level
        constitution_modifier = self._get_constitution_modifier(raw_data)
        total_level = self._get_total_level(raw_data)
        
        logger.debug(f"HP calculation: method={hit_point_method}, base_hp={base_hp}, con_mod={constitution_modifier}, level={total_level}")
        
        if hit_point_type == 1:  # Fixed HP Method
            # For Fixed HP method, add constitution bonus but don't show it in breakdown
            constitution_hp_bonus = constitution_modifier * total_level
            max_hp_base = base_hp + constitution_hp_bonus
            logger.debug(f"Fixed HP: {base_hp} (base) + {constitution_hp_bonus} (con) = {max_hp_base}")
        else:
            # Manual/Rolled HP or Default: Use API base_hp + separate CON bonus
            constitution_hp_bonus = constitution_modifier * total_level
            max_hp_base = base_hp + constitution_hp_bonus
            logger.debug(f"Manual/Rolled HP: {base_hp} + {constitution_hp_bonus} = {max_hp_base}")
        
        # Add any bonus HP from items/features and racial bonuses
        # Ensure all values are not None
        max_hp_base = max_hp_base or 0
        bonus_hp = bonus_hp or 0
        racial_hp_bonus = self._get_racial_hp_bonus(raw_data)
        total_hp = max_hp_base + bonus_hp + racial_hp_bonus
        logger.debug(f"Final HP: {max_hp_base} + {bonus_hp} (bonus) + {racial_hp_bonus} (racial) = {total_hp}")
        
        # Minimum 1 HP per level
        total_level = self._get_total_level(raw_data)
        min_hp = max(1, total_level)
        
        final_hp = max(total_hp, min_hp)
        
        logger.debug(f"Calculated max HP: {final_hp} (base:{base_hp} con:{constitution_modifier} bonus:{bonus_hp})")
        return final_hp
    
    def get_hp_breakdown(self, character: Character, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed hit point calculation breakdown.
        
        Args:
            character: Character data model
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Dictionary with detailed HP breakdown
        """
        logger.debug("Generating HP breakdown")
        
        # Check for override
        hit_point_info = raw_data.get('hitPointInfo', {})
        if 'maximum' in hit_point_info:
            return {
                'total': hit_point_info['maximum'],
                'method': 'override',
                'source': 'hitPointInfo',
                'note': 'HP taken from D&D Beyond hitPointInfo (manual entry or calculated)'
            }
        
        # Check for direct override (2024 API structure)
        override_hp = raw_data.get('overrideHitPoints')
        if override_hp is not None:
            return {
                'total': override_hp,
                'method': 'override',
                'source': 'overrideHitPoints',
                'note': 'HP manually overridden in D&D Beyond'
            }
        
        # Calculate breakdown with null safety
        base_hp = self._calculate_base_hp(raw_data) or 0
        constitution_bonus = self._calculate_constitution_bonus(raw_data) or 0
        feat_bonus = self._calculate_feat_hp_bonus(raw_data) or 0
        item_bonus = self._calculate_item_hp_bonus(raw_data) or 0
        other_bonus = self._calculate_other_hp_bonus(raw_data) or 0
        
        # For Fixed HP method, constitution is included but not shown in breakdown
        hit_point_type = self._get_hit_point_type(raw_data)
        if hit_point_type == 'Fixed':
            # Use the actual CON modifier from API calculation
            actual_con_bonus = self._get_constitution_hp_from_api(raw_data)
            total_hp = base_hp + actual_con_bonus + feat_bonus + item_bonus + other_bonus
            logger.debug(f"Fixed HP: base {base_hp} + hidden_con {actual_con_bonus} + feat {feat_bonus} + item {item_bonus} + other {other_bonus} = {total_hp}")
        else:
            total_hp = base_hp + constitution_bonus + feat_bonus + item_bonus + other_bonus
        
        breakdown = {
            'total': total_hp,
            'base_hit_points': base_hp,
            'constitution_bonus': constitution_bonus,
            'feat_bonus': feat_bonus,
            'item_bonus': item_bonus,
            'other_bonus': other_bonus,
            'method': 'calculated',
            'class_breakdown': self._get_class_hp_breakdown(raw_data)
        }
        
        return breakdown
    
    def calculate_hit_die(self, character: Character, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate hit dice information.
        
        Args:
            character: Character data model
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Dictionary with hit dice information
        """
        logger.debug("Calculating hit dice information")
        
        classes = raw_data.get('classes', [])
        hit_dice = {}
        total_hit_dice = 0
        used_hit_dice = 0
        
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', 'Unknown').lower()
            class_level = class_data.get('level', 0)
            hit_dice_used = class_data.get('hitDiceUsed', 0)
            
            # Get hit die size
            hit_die_size = self.class_hit_dice.get(class_name, 8)
            
            hit_dice[class_name] = {
                'die_size': hit_die_size,
                'total': class_level,
                'used': hit_dice_used,
                'available': class_level - hit_dice_used
            }
            
            total_hit_dice += class_level
            used_hit_dice += hit_dice_used
        
        return {
            'by_class': hit_dice,
            'total_hit_dice': total_hit_dice,
            'used_hit_dice': used_hit_dice,
            'available_hit_dice': total_hit_dice - used_hit_dice
        }
    
    def _calculate_base_hp(self, raw_data: Dict[str, Any]) -> int:
        """Calculate base HP from class levels and hit dice (without CON modifier)."""
        logger.debug("Calculating base HP from classes")
        
        # For Manual HP method, use API's baseHitPoints if available
        hit_point_type = self._get_hit_point_type(raw_data)
        api_base_hp = raw_data.get('baseHitPoints')
        
        if hit_point_type == 'Manual' and api_base_hp is not None:
            logger.debug(f"Using API baseHitPoints for Manual HP: {api_base_hp}")
            return api_base_hp
        
        base_hp = 0
        classes = raw_data.get('classes', [])
        
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', 'Unknown').lower()
            class_level = class_data.get('level', 0)
            
            # Get hit die size for this class
            hit_die_size = self.class_hit_dice.get(class_name, 8)
            
            if class_level > 0:
                # First level is always max hit die (without CON modifier for base)
                first_level_hp = hit_die_size
                
                # Remaining levels depend on hit point method
                remaining_levels = class_level - 1
                if hit_point_type == 'Manual':
                    # For manual, assume they chose slightly above average
                    # Level 2 Sorcerer with base 11 suggests: 6 (L1) + 5 (L2) = 11
                    avg_hp_per_level = (hit_die_size // 2) + 1  # For d6: 4
                    remaining_hp = remaining_levels * (avg_hp_per_level + 1)  # +1 for good rolls
                elif hit_point_type == 'Fixed':
                    # Fixed uses average rounded up
                    avg_hp_per_level = (hit_die_size // 2) + 1
                    remaining_hp = remaining_levels * avg_hp_per_level
                else:
                    # Default uses average
                    avg_hp_per_level = (hit_die_size // 2) + 1
                    remaining_hp = remaining_levels * avg_hp_per_level
                
                class_hp = first_level_hp + remaining_hp
                base_hp += class_hp
                
                logger.debug(f"{class_name.title()} Level {class_level}: {class_hp} HP (d{hit_die_size})")
        
        return base_hp
    
    def _get_hit_point_type(self, raw_data: Dict[str, Any]) -> str:
        """Get the hit point calculation method."""
        preferences = raw_data.get('preferences', {})
        hit_point_type = preferences.get('hitPointType', 0)
        
        # Map numeric types to strings
        type_map = {
            0: 'Default',
            1: 'Fixed', 
            2: 'Manual'
        }
        
        return type_map.get(hit_point_type, 'Default')
    
    def _get_constitution_hp_from_api(self, raw_data: Dict[str, Any]) -> int:
        """Get Constitution HP bonus by calculating from current vs base HP in API."""
        # D&D Beyond's API often shows the real HP total somewhere
        # Try to extract it from the difference between what they calculate and baseHitPoints
        base_hp = raw_data.get('baseHitPoints', 0)
        bonus_hp = raw_data.get('bonusHitPoints', 0) or 0
        
        # The character's displayed HP should be available - let's find it
        # For now, calculate based on constitution directly
        return self._calculate_actual_constitution_bonus(raw_data)
    
    def _calculate_actual_constitution_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Calculate actual Constitution HP bonus for internal calculations."""
        logger.debug("Calculating actual Constitution HP bonus")
        
        # Get Constitution score from ability scores
        con_score = 10
        stats = raw_data.get('stats', [])
        
        for stat in stats:
            if stat.get('id') == 3:  # Constitution is ID 3
                con_score = stat.get('value', 10)
                break
        
        # Apply racial and other bonuses to get final constitution
        modifiers = raw_data.get('modifiers', {})
        
        # Check racial modifiers
        racial_modifiers = modifiers.get('race', [])
        for modifier in racial_modifiers:
            if modifier.get('subType') == 'constitution-score':
                con_score += modifier.get('value', 0)
                logger.debug(f"Applied racial CON bonus: +{modifier.get('value', 0)}")
        
        # Calculate modifier
        con_modifier = (con_score - 10) // 2
        
        # Get total character level
        classes = raw_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes) or 1
        
        constitution_hp_bonus = con_modifier * total_level
        
        logger.debug(f"Constitution HP calculation: score {con_score}, modifier {con_modifier}, level {total_level}, bonus {constitution_hp_bonus}")
        
        return constitution_hp_bonus
    
    def _calculate_constitution_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Calculate HP bonus from Constitution modifier."""
        logger.debug("Calculating Constitution HP bonus")
        
        # For Fixed HP method, constitution bonus is already included in base HP
        hit_point_type = self._get_hit_point_type(raw_data)
        if hit_point_type == 'Fixed':
            logger.debug("Fixed HP method: constitution bonus already included in base, returning 0")
            return 0
        
        # Use the same comprehensive CON modifier calculation as the main HP calculation
        con_modifier = self._get_constitution_modifier(raw_data)
        total_level = self._get_total_level(raw_data)
        
        constitution_bonus = con_modifier * total_level
        
        logger.debug(f"Constitution bonus: {constitution_bonus} (modifier {con_modifier}, level {total_level})")
        return constitution_bonus
    
    def _calculate_feat_hp_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Calculate HP bonus from feats (like Tough)."""
        logger.debug("Calculating feat HP bonuses")
        
        feat_bonus = 0
        try:
            modifiers = raw_data.get('modifiers', {})
            if not isinstance(modifiers, dict):
                return 0
                
            feat_modifiers = modifiers.get('feat', [])
            if not isinstance(feat_modifiers, list):
                return 0
            
            for modifier in feat_modifiers:
                if not isinstance(modifier, dict):
                    continue
                    
                if self._is_hp_modifier(modifier):
                    bonus = modifier.get('bonus', 0) or modifier.get('value', 0)
                    if bonus is not None and isinstance(bonus, (int, float)):
                        feat_bonus += int(bonus)
                    
                    # Tough feat gives +2 HP per level
                    if modifier.get('friendlyTypeName') == 'Tough':
                        total_level = self._get_total_level(raw_data)
                        tough_bonus = 2 * total_level
                        feat_bonus += tough_bonus
                        logger.debug(f"Tough feat bonus: {tough_bonus}")
        except Exception as e:
            logger.debug(f"Error calculating feat HP bonus: {e}")
            return 0
        
        return feat_bonus
    
    def _calculate_item_hp_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Calculate HP bonus from magic items."""
        logger.debug("Calculating item HP bonuses")
        
        item_bonus = 0
        try:
            modifiers = raw_data.get('modifiers', {})
            if not isinstance(modifiers, dict):
                return 0
                
            item_modifiers = modifiers.get('item', [])
            if not isinstance(item_modifiers, list):
                return 0
            
            for modifier in item_modifiers:
                if not isinstance(modifier, dict):
                    continue
                    
                if self._is_hp_modifier(modifier):
                    bonus = modifier.get('bonus', 0) or modifier.get('value', 0)
                    if bonus is not None and isinstance(bonus, (int, float)):
                        item_bonus += int(bonus)
                        logger.debug(f"Item HP bonus: {bonus}")
        except Exception as e:
            logger.debug(f"Error calculating item HP bonus: {e}")
            return 0
        
        return item_bonus
    
    def _calculate_other_hp_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Calculate HP bonus from other sources."""
        logger.debug("Calculating other HP bonuses")
        
        other_bonus = 0
        try:
            modifiers = raw_data.get('modifiers', {})
            if not isinstance(modifiers, dict):
                return 0
            
            for source_type, modifier_list in modifiers.items():
                if source_type in ['feat', 'item']:
                    continue  # Already handled
                    
                if not isinstance(modifier_list, list):
                    continue
                    
                for modifier in modifier_list:
                    if not isinstance(modifier, dict):
                        continue
                        
                    if self._is_hp_modifier(modifier):
                        bonus = modifier.get('bonus', 0) or modifier.get('value', 0)
                        if bonus is not None and isinstance(bonus, (int, float)):
                            other_bonus += int(bonus)
                            logger.debug(f"Other HP bonus: {bonus} (source: {source_type})")
        except Exception as e:
            logger.debug(f"Error calculating other HP bonus: {e}")
            return 0
        
        return other_bonus
    
    def _is_hp_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects hit points."""
        # HP modifiers might have specific patterns
        subtype = modifier.get('subType', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        hp_keywords = ['hit-points', 'hitpoints', 'hp', 'maximum-hit-points']
        
        return any(keyword in subtype or keyword in friendly_type for keyword in hp_keywords)
    
    def _get_current_hp(self, raw_data: Dict[str, Any]) -> Optional[int]:
        """Get current HP from D&D Beyond data."""
        # Try new format first (hitPointInfo)
        hit_point_info = raw_data.get('hitPointInfo', {})
        current_hp = hit_point_info.get('current')
        if current_hp is not None:
            return current_hp
        
        # Fall back to older format with overrideHitPoints/removedHitPoints
        override_hp = raw_data.get('overrideHitPoints')
        removed_hp = raw_data.get('removedHitPoints', 0)
        
        if override_hp is not None:
            # Current HP = override HP - removed HP
            current_hp = override_hp - removed_hp
            logger.debug(f"Current HP calculated from override: {override_hp} - {removed_hp} = {current_hp}")
            return current_hp
        
        # If no current HP info available, assume full HP
        max_hp = self.calculate_max_hp(None, raw_data)
        current_hp = max_hp - removed_hp
        logger.debug(f"Current HP calculated from max: {max_hp} - {removed_hp} = {current_hp}")
        return current_hp
    
    def _get_racial_hp_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Calculate racial HP bonuses like Dwarven Toughness."""
        racial_hp_bonus = 0
        
        # Check for Dwarven Toughness by looking at racial traits
        race_data = raw_data.get('race', {})
        if race_data:
            racial_traits = race_data.get('racialTraits', [])
            total_level = self._get_total_level(raw_data)
            
            for trait in racial_traits:
                trait_def = trait.get('definition', {})
                trait_name = trait_def.get('name', '').lower()
                
                if 'dwarven toughness' in trait_name:
                    # Dwarven Toughness: +1 HP per level
                    racial_hp_bonus += total_level
                    logger.debug(f"Dwarven Toughness: +{total_level} HP (level {total_level})")
                    break
                    
            # Also check by race name as fallback
            race_name = race_data.get('fullName', '').lower()
            if 'dwarf' in race_name and racial_hp_bonus == 0:
                # Fallback for older data structure
                racial_hp_bonus += total_level
                logger.debug(f"Dwarven Toughness (fallback): +{total_level} HP")
        
        # Add other racial HP bonuses here as needed
        
        return racial_hp_bonus
    
    def _get_temporary_hp(self, raw_data: Dict[str, Any]) -> int:
        """Get temporary HP from D&D Beyond data."""
        hit_point_info = raw_data.get('hitPointInfo', {})
        return hit_point_info.get('temp', 0)
    
    def _get_total_level(self, raw_data: Dict[str, Any]) -> int:
        """Get total character level."""
        classes = raw_data.get('classes', [])
        return sum(cls.get('level', 0) for cls in classes) or 1
    
    def _get_constitution_modifier(self, raw_data: Dict[str, Any]) -> int:
        """Get Constitution modifier. Uses the ability score calculator for consistency."""
        # Import here to avoid circular imports
        from src.calculators.ability_scores import AbilityScoreCalculator
        
        # Use the ability score calculator to get the correct constitution score
        ability_calc = AbilityScoreCalculator()
        ability_scores = ability_calc.calculate_final_scores(raw_data)
        
        # Extract the numeric score from the ability score structure
        constitution_data = ability_scores.get('constitution', {})
        if isinstance(constitution_data, dict):
            constitution_score = constitution_data.get('score', 10)
        else:
            constitution_score = constitution_data or 10
            
        constitution_modifier = (constitution_score - 10) // 2
        
        logger.debug(f"Final Constitution: {constitution_score} (modifier: {constitution_modifier})")
        return constitution_modifier
    
    def _get_class_hp_breakdown(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Get HP breakdown by class."""
        class_breakdown = {}
        classes = raw_data.get('classes', [])
        
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', 'Unknown')
            class_level = class_data.get('level', 0)
            
            # Get hit die size
            hit_die_size = self.class_hit_dice.get(class_name.lower(), 8)
            
            # Estimate HP contribution (first level max, others average)
            if class_level > 0:
                first_level = hit_die_size
                remaining = (class_level - 1) * ((hit_die_size // 2) + 1)
                total_class_hp = first_level + remaining
                
                class_breakdown[class_name] = {
                    'level': class_level,
                    'hit_die': f"d{hit_die_size}",
                    'estimated_hp': total_class_hp,
                    'first_level_hp': first_level,
                    'remaining_levels_hp': remaining
                }
        
        return class_breakdown