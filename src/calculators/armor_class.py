"""
Armor Class Calculator

Calculates armor class from D&D Beyond data with method detection.
Handles various AC calculation methods including Unarmored Defense.
"""

from typing import Dict, Any, Optional
import logging

from src.interfaces.calculator import ArmorClassCalculatorInterface
from src.models.character import Character
from src.config.manager import get_config_manager

logger = logging.getLogger(__name__)


class ArmorClassCalculator(ArmorClassCalculatorInterface):
    """
    Calculator for armor class with method detection and breakdown.
    
    Handles:
    - Standard armor + Dex modifier calculation
    - Unarmored Defense (Barbarian, Monk, Draconic Sorcerer)
    - Natural armor
    - Magic item bonuses
    - Shield bonuses
    - Deflection and misc bonuses
    - Dexterity modifier limits from armor
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.constants = self.config_manager.get_constants_config()
        
    def calculate(self, character: Character, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate armor class with complete breakdown.
        
        Returns:
            Dictionary containing total AC and detailed breakdown
        """
        logger.info(f"Calculating armor class for character {character.id}")
        
        total_ac = self.calculate_ac(character, raw_data)
        ac_breakdown = self.get_ac_breakdown(character, raw_data)
        calculation_method = self.detect_ac_calculation_method(raw_data)
        
        result = {
            'armor_class': total_ac,
            'ac_breakdown': ac_breakdown,
            'calculation_method': calculation_method
        }
        
        logger.debug(f"Calculated AC: {total_ac} (method: {calculation_method})")
        return result
    
    def validate_inputs(self, character: Character, raw_data: Dict[str, Any]) -> bool:
        """Validate that we have sufficient data for AC calculation."""
        # AC can be calculated with minimal data, but we need stats for Dex
        if 'stats' not in raw_data:
            logger.warning("No stats found for AC calculation")
        
        return True  # AC calculation is quite robust
    
    def calculate_ac(self, character: Character, raw_data: Dict[str, Any]) -> int:
        """
        Calculate total armor class.
        
        Args:
            character: Character data model
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Total armor class
        """
        logger.debug("Calculating total armor class")
        
        # Check if there's an override in the API data
        armor_class_data = raw_data.get('armorClass')
        if isinstance(armor_class_data, int):
            logger.debug(f"Using API armor class: {armor_class_data}")
            return armor_class_data
        
        # Check for Warforged Integrated Protection (special case)
        if self._has_warforged_integrated_protection(raw_data):
            return self._calculate_warforged_ac(raw_data)
        
        # Calculate from components
        # Check if wearing armor - if so, armor sets base AC
        armor_ac = self._get_equipped_armor_ac(raw_data)
        if armor_ac > 0:
            # Wearing armor: armor AC + dex (capped) + shield + misc
            base_ac = armor_ac
            dex_bonus = self._get_dexterity_bonus_armored(raw_data)
            unarmored_defense_bonus = 0  # No unarmored defense when wearing armor
            logger.debug(f"Armored AC calculation: base {base_ac} (from armor)")
        else:
            # Unarmored: 10 + dex + unarmored defense + misc
            base_ac = 10
            unarmored_defense_bonus = self._get_unarmored_defense_bonus(raw_data)
            dex_bonus = self._get_dexterity_bonus(raw_data)
            logger.debug(f"Unarmored AC calculation: base {base_ac} + unarmored defense {unarmored_defense_bonus}")
        
        shield_bonus = self._get_shield_bonus(raw_data)
        natural_armor = self._get_natural_armor_bonus(raw_data)
        deflection_bonus = self._get_deflection_bonus(raw_data)
        misc_bonus = self._get_misc_ac_bonus(raw_data)
        
        total_ac = base_ac + shield_bonus + dex_bonus + unarmored_defense_bonus + natural_armor + deflection_bonus + misc_bonus
        
        logger.debug(f"AC components: base:{base_ac} shield:{shield_bonus} dex:{dex_bonus} natural:{natural_armor} deflection:{deflection_bonus} misc:{misc_bonus}")
        return total_ac
    
    def get_ac_breakdown(self, character: Character, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Get detailed AC calculation breakdown.
        
        Args:
            character: Character data model
            raw_data: Raw D&D Beyond character data
            
        Returns:
            Dictionary with detailed AC breakdown
        """
        logger.debug("Generating AC breakdown")
        
        # Check for API override
        armor_class_data = raw_data.get('armorClass')
        if isinstance(armor_class_data, int):
            return {
                'total': armor_class_data,
                'method': 'api_override',
                'source': 'D&D Beyond API',
                'note': 'AC taken directly from API response'
            }
        
        # Calculate detailed breakdown (same logic as main calculation)
        armor_ac = self._get_equipped_armor_ac(raw_data)
        unarmored_defense_bonus = 0
        armor_bonus = 0
        
        if armor_ac > 0:
            # Wearing armor
            base_ac = armor_ac
            armor_bonus = armor_ac - 10  # Armor bonus above base 10 AC
            dex_bonus = self._get_dexterity_bonus_armored(raw_data)
        else:
            # Unarmored
            base_ac = 10
            unarmored_defense_bonus = self._get_unarmored_defense_bonus(raw_data)
            dex_bonus = self._get_dexterity_bonus(raw_data)
        
        shield_bonus = self._get_shield_bonus(raw_data)
        natural_armor = self._get_natural_armor_bonus(raw_data)
        deflection_bonus = self._get_deflection_bonus(raw_data)
        misc_bonus = self._get_misc_ac_bonus(raw_data)
        
        total_ac = base_ac + shield_bonus + dex_bonus + unarmored_defense_bonus + natural_armor + deflection_bonus + misc_bonus
        
        # Get equipment details
        armor_info = self._get_armor_info(raw_data)
        shield_info = self._get_shield_info(raw_data)
        dex_limit = self._get_dex_limit(raw_data)
        
        breakdown = {
            'total': total_ac,
            'base': base_ac,
            'armor_bonus': armor_bonus,
            'shield_bonus': shield_bonus,
            'dexterity_bonus': dex_bonus,
            'unarmored_defense': unarmored_defense_bonus,
            'natural_armor': natural_armor,
            'deflection_bonus': deflection_bonus,
            'misc_bonus': misc_bonus,
            'calculation_method': self.detect_ac_calculation_method(raw_data),
            'armor_worn': armor_info,
            'shield_used': shield_info,
            'max_dex_bonus': dex_limit
        }
        
        return breakdown
    
    def detect_ac_calculation_method(self, raw_data: Dict[str, Any]) -> str:
        """
        Detect which AC calculation method is being used.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            String describing the AC calculation method
        """
        logger.debug("Detecting AC calculation method")
        
        # Check for specific class features
        if self._has_unarmored_defense(raw_data):
            return "unarmored_defense"
        
        # Check for natural armor
        if self._has_natural_armor(raw_data):
            return "natural_armor"
        
        # Check if wearing armor
        armor_info = self._get_armor_info(raw_data)
        if armor_info:
            return "armored"
        
        # Default unarmored
        return "unarmored"
    
    def _get_base_ac(self, raw_data: Dict[str, Any]) -> int:
        """Get base AC (usually 10)."""
        # Check for unarmored defense or natural armor
        if self._has_unarmored_defense(raw_data):
            return 10  # Unarmored defense still starts at 10
        
        return 10  # Standard base AC
    
    def _get_equipped_armor_ac(self, raw_data: Dict[str, Any]) -> int:
        """Get AC from equipped armor (replaces base AC when wearing armor)."""
        logger.debug("Checking for equipped armor")
        
        inventory = raw_data.get('inventory', [])
        
        for item in inventory:
            if self._is_equipped_armor(item):
                # Get item name from definition or top level
                item_def = item.get('definition', {})
                armor_name = item_def.get('name', item.get('name', 'Unknown Armor'))
                
                # Try name lookup first for standard D&D 5e armor
                armor_class = self._get_armor_ac_by_name(armor_name)
                
                if armor_class == 0:
                    # Fallback: API armorClass field might be a bonus above 10
                    armor_bonus = item_def.get('armorClass', 0)
                    if armor_bonus > 0:
                        armor_class = 10 + armor_bonus
                
                logger.debug(f"Equipped armor {armor_name}: AC {armor_class}")
                return armor_class  # Return first equipped armor's AC
        
        return 0  # No armor equipped
    
    def _get_dexterity_bonus_armored(self, raw_data: Dict[str, Any]) -> int:
        """Get Dexterity bonus for armored AC (may be capped)."""
        logger.debug("Calculating Dexterity AC bonus (armored)")
        
        # Get base dex bonus
        dex_bonus = self._get_dexterity_bonus(raw_data)
        
        # Check for armor dex cap
        inventory = raw_data.get('inventory', [])
        for item in inventory:
            if self._is_equipped_armor(item):
                armor_def = item.get('definition', {})
                armor_name = armor_def.get('name', item.get('name', ''))
                
                # First try to get cap from the item definition
                dex_cap = armor_def.get('maxDexModifier')
                
                if dex_cap is None:
                    # Fallback to armor type-based caps
                    armor_name_lower = armor_name.lower()
                    if any(heavy_armor in armor_name_lower for heavy_armor in ['chain mail', 'splint', 'plate']):
                        dex_cap = 0  # Heavy armor
                    elif any(medium_armor in armor_name_lower for medium_armor in ['scale mail', 'chain shirt', 'breastplate', 'half plate', 'hide']):
                        dex_cap = 2  # Medium armor cap
                    else:
                        dex_cap = None  # Light armor or no cap
                
                if dex_cap is not None:
                    capped_dex = min(dex_bonus, dex_cap)
                    logger.debug(f"Dex bonus capped by {armor_name}: {dex_bonus} -> {capped_dex} (cap: {dex_cap})")
                    return capped_dex
                else:
                    logger.debug(f"No Dex cap for armor {armor_name}")
        
        return dex_bonus  # No cap found
    
    def _get_shield_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get AC bonus from equipped shield."""
        logger.debug("Calculating shield bonus")
        
        shield_bonus = 0
        inventory = raw_data.get('inventory', [])
        
        for item in inventory:
            if self._is_equipped_shield(item):
                # Try to get AC from definition first, then fall back to standard shield AC
                item_def = item.get('definition', {})
                armor_class = item_def.get('armorClass')
                
                # Get shield name from definition or top level
                shield_name = item_def.get('name', item.get('name', 'Unknown Shield'))
                
                logger.debug(f"Shield AC detection: name={shield_name}, definition_ac={armor_class}, has_definition={bool(item_def)}")
                
                if armor_class is None or armor_class == 0:
                    # Standard shield provides +2 AC if not defined in data
                    armor_class = 2
                
                # Always check for magical enhancement regardless of base AC source
                is_attuned = item.get('attuned', False)
                requires_attunement = item.get('requires_attunement', False)
                charges_used = item.get('chargesUsed', 0)
                
                logger.debug(f"Shield magic check: attuned={is_attuned}, requires={requires_attunement}, charges={charges_used}")
                
                # Shield is magical if attuned but doesn't require it, or has charges
                if (is_attuned and not requires_attunement) or (charges_used and charges_used > 0):
                    armor_class += 1  # Magical shield bonus
                    logger.debug(f"Detected magical shield: +1 bonus (attuned: {is_attuned}, requires: {requires_attunement}, charges: {charges_used})")
                
                shield_bonus += armor_class
                logger.debug(f"Shield bonus from {shield_name}: +{armor_class}")
        
        return shield_bonus
    
    def _get_dexterity_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get AC bonus from Dexterity modifier (with armor limits)."""
        logger.debug("Calculating Dexterity AC bonus")
        
        # Get Dexterity modifier
        dex_modifier = self._get_dex_modifier(raw_data)
        
        # Check for Dexterity limit from armor
        max_dex = self._get_dex_limit(raw_data)
        
        if max_dex is not None:
            dex_bonus = min(dex_modifier, max_dex)
            logger.debug(f"Dex bonus: {dex_bonus} (modifier: {dex_modifier}, limit: {max_dex})")
        else:
            dex_bonus = dex_modifier
            logger.debug(f"Dex bonus: {dex_bonus} (no limit)")
        
        return dex_bonus
    
    def _get_natural_armor_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get AC bonus from natural armor."""
        logger.debug("Calculating natural armor bonus")
        
        natural_armor = 0
        
        # Check modifiers for natural armor
        modifiers = raw_data.get('modifiers', {})
        
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_natural_armor_modifier(modifier):
                    bonus = modifier.get('bonus', 0) or modifier.get('value', 0) or 0
                    natural_armor += bonus
                    logger.debug(f"Natural armor bonus: +{bonus} (source: {source_type})")
        
        return natural_armor
    
    def _get_deflection_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get AC bonus from deflection effects."""
        logger.debug("Calculating deflection bonus")
        
        deflection_bonus = 0
        
        # Check modifiers for deflection bonuses
        modifiers = raw_data.get('modifiers', {})
        
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_deflection_modifier(modifier):
                    bonus = modifier.get('bonus', 0) or modifier.get('value', 0) or 0
                    deflection_bonus += bonus
                    logger.debug(f"Deflection bonus: +{bonus} (source: {source_type})")
        
        return deflection_bonus
    
    def _get_misc_ac_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get AC bonus from miscellaneous sources."""
        logger.debug("Calculating miscellaneous AC bonuses")
        
        misc_bonus = 0
        
        # Check modifiers for AC bonuses
        modifiers = raw_data.get('modifiers', {})
        
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_ac_modifier(modifier) and not self._is_natural_armor_modifier(modifier) and not self._is_deflection_modifier(modifier):
                    bonus = modifier.get('bonus', 0) or modifier.get('value', 0) or 0
                    misc_bonus += bonus
                    logger.debug(f"Misc AC bonus: +{bonus} (source: {source_type})")
        
        return misc_bonus
    
    def _get_dex_modifier(self, raw_data: Dict[str, Any]) -> int:
        """Get Dexterity modifier. Uses the ability score calculator for consistency."""
        # Import here to avoid circular imports
        from src.calculators.ability_scores import AbilityScoreCalculator
        
        # Use the ability score calculator to get the correct dexterity score
        ability_calc = AbilityScoreCalculator()
        ability_scores = ability_calc.calculate_final_scores(raw_data)
        
        # Extract the numeric score from the ability score structure
        dexterity_data = ability_scores.get('dexterity', {})
        
        if isinstance(dexterity_data, dict):
            dexterity_score = dexterity_data.get('total', 10)
        else:
            dexterity_score = dexterity_data or 10
            
        dexterity_modifier = (dexterity_score - 10) // 2
        logger.debug(f"Using calculated DEX score: {dexterity_score} (modifier: {dexterity_modifier})")
        return dexterity_modifier
    
    def _get_con_modifier(self, raw_data: Dict[str, Any]) -> int:
        """Get Constitution modifier. Uses the ability score calculator for consistency."""
        # Import here to avoid circular imports
        from src.calculators.ability_scores import AbilityScoreCalculator
        
        # Use the ability score calculator to get the correct constitution score
        ability_calc = AbilityScoreCalculator()
        ability_scores = ability_calc.calculate_final_scores(raw_data)
        
        # Extract the numeric score from the ability score structure
        constitution_data = ability_scores.get('constitution', {})
        if isinstance(constitution_data, dict):
            constitution_score = constitution_data.get('total', 10)
        else:
            constitution_score = constitution_data or 10
            
        constitution_modifier = (constitution_score - 10) // 2
        return constitution_modifier
    
    def _get_wis_modifier(self, raw_data: Dict[str, Any]) -> int:
        """Get Wisdom modifier. Uses the ability score calculator for consistency."""
        # Import here to avoid circular imports
        from src.calculators.ability_scores import AbilityScoreCalculator
        
        # Use the ability score calculator to get the correct wisdom score
        ability_calc = AbilityScoreCalculator()
        ability_scores = ability_calc.calculate_final_scores(raw_data)
        
        # Extract the numeric score from the ability score structure
        wisdom_data = ability_scores.get('wisdom', {})
        if isinstance(wisdom_data, dict):
            wisdom_score = wisdom_data.get('total', 10)
        else:
            wisdom_score = wisdom_data or 10
            
        wisdom_modifier = (wisdom_score - 10) // 2
        return wisdom_modifier
    
    def _get_dex_limit(self, raw_data: Dict[str, Any]) -> Optional[int]:
        """Get maximum Dexterity bonus allowed by worn armor."""
        inventory = raw_data.get('inventory', [])
        
        for item in inventory:
            if self._is_equipped_armor(item):
                armor_def = item.get('definition', {})
                return armor_def.get('maxDexModifier')
        
        return None  # No limit
    
    def _has_unarmored_defense(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character has Unarmored Defense class feature."""
        # This would need to check for specific class features
        # For now, simplified check based on classes
        classes = raw_data.get('classes', [])
        
        unarmored_defense_classes = ['barbarian', 'monk']
        
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            
            if class_name in unarmored_defense_classes:
                return True
        
        # Also check for Draconic Bloodline Sorcerer
        # This would require checking subclass features
        
        return False
    
    def _get_unarmored_defense_bonus(self, raw_data: Dict[str, Any]) -> int:
        """
        Calculate additional ability modifier bonus for Unarmored Defense.
        
        Barbarian Unarmored Defense: AC = 10 + Dex + Con (when not wearing armor)
        Monk Unarmored Defense: AC = 10 + Dex + Wis (when not wearing armor or shield)
        
        Note: The base Dex modifier is already added in _get_dexterity_bonus(),
        so this method only adds the Constitution (Barbarian) or Wisdom (Monk) modifier.
        """
        # Only apply if character has no armor equipped
        if self._is_wearing_armor(raw_data):
            return 0
        
        classes = raw_data.get('classes', [])
        unarmored_defense_bonus = 0
        
        for class_data in classes:
            class_def = class_data.get('definition', {})
            class_name = class_def.get('name', '').lower()
            
            if class_name == 'barbarian':
                # Barbarian Unarmored Defense: add Constitution modifier
                con_modifier = self._get_con_modifier(raw_data)
                unarmored_defense_bonus = max(unarmored_defense_bonus, con_modifier)
                logger.debug(f"Barbarian Unarmored Defense: +{con_modifier} CON modifier")
                
            elif class_name == 'monk':
                # Monk Unarmored Defense: add Wisdom modifier (and no shield)
                if not self._is_wearing_shield(raw_data):
                    wis_modifier = self._get_wis_modifier(raw_data)
                    unarmored_defense_bonus = max(unarmored_defense_bonus, wis_modifier)
                    logger.debug(f"Monk Unarmored Defense: +{wis_modifier} WIS modifier")
        
        # Check for Draconic Bloodline Sorcerer (also gets Unarmored Defense)
        # This would need more specific subclass detection
        
        return unarmored_defense_bonus
    
    def _is_wearing_armor(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character is wearing armor."""
        inventory = raw_data.get('inventory', [])
        
        for item in inventory:
            if self._is_equipped_armor(item):
                return True
        
        return False
    
    def _is_wearing_shield(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character is wearing a shield."""
        inventory = raw_data.get('inventory', [])
        
        for item in inventory:
            if item.get('equipped', False):
                item_def = item.get('definition', {})
                armor_class = item_def.get('armorClass')
                armor_type = item_def.get('armorTypeId')
                
                # Shield typically has armorTypeId of 4
                if armor_type == 4 or (armor_class and item_def.get('name', '').lower().find('shield') >= 0):
                    return True
        
        return False
    
    def _has_natural_armor(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character has natural armor."""
        # Check race features or modifiers for natural armor
        modifiers = raw_data.get('modifiers', {})
        
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_natural_armor_modifier(modifier):
                    return True
        
        return False
    
    def _is_equipped_armor(self, item: Dict[str, Any]) -> bool:
        """Check if an item is equipped armor (not shields)."""
        if not item.get('equipped', False):
            return False
        
        # Check both the definition structure (original API) and direct structure (current)
        item_def = item.get('definition', {})
        item_name = item_def.get('name', item.get('name', ''))
        item_type = item_def.get('type', item.get('type', ''))
        filter_type = item_def.get('filterType', '')
        
        # Safe string operations with None checking
        item_name_safe = (item_name or '').lower()
        item_type_safe = item_type or ''
        
        # Exclude shields explicitly
        if 'shield' in item_name_safe:
            return False
        
        # Check if it's armor by type or by being a known armor piece
        is_armor_by_type = (filter_type == 'Armor' or 
                           item_type_safe in ['Light Armor', 'Medium Armor', 'Heavy Armor'] or
                           self._is_known_armor(item_name))
        
        return is_armor_by_type
    
    def _is_known_armor(self, item_name: str) -> bool:
        """Check if an item name is a known armor piece."""
        if not item_name:
            return False
        
        armor_names = [
            'padded', 'leather', 'leather armor', 'studded leather',
            'hide', 'chain shirt', 'scale mail', 'breastplate', 'half plate', 'half plate armor',
            'ring mail', 'chain mail', 'splint', 'splint armor', 'plate', 'plate armor'
        ]
        
        return item_name.lower() in armor_names
    
    def _get_armor_ac_by_name(self, item_name: str) -> int:
        """Get AC value for armor by name."""
        if not item_name:
            return 0
            
        # Standard D&D 5e armor AC values
        armor_ac_table = {
            # Light Armor
            'padded': 11,
            'leather': 11,
            'leather armor': 11,
            'studded leather': 12,
            # Medium Armor
            'hide': 12,
            'chain shirt': 13,
            'scale mail': 14,
            'breastplate': 14,
            'half plate': 15,
            'half plate armor': 15,
            # Heavy Armor
            'ring mail': 14,
            'chain mail': 16,
            'splint': 17,
            'splint armor': 17,
            'plate': 18,
            'plate armor': 18
        }
        
        return armor_ac_table.get(item_name.lower(), 0)
    
    def _is_equipped_shield(self, item: Dict[str, Any]) -> bool:
        """Check if an item is an equipped shield."""
        if not item.get('equipped', False):
            return False
        
        # Check both definition structure and direct structure
        item_def = item.get('definition', {})
        item_name = item_def.get('name', item.get('name', ''))
        item_type = item_def.get('type', item.get('type', ''))
        
        # Safe string operations with None checking
        item_name_safe = (item_name or '').lower()
        item_type_safe = (item_type or '').lower()
        
        return ('shield' in item_name_safe or 
                item_type_safe == 'shield')
    
    def _is_ac_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects armor class."""
        # AC modifiers often have specific subType or friendly type names
        subtype = modifier.get('subType', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        ac_keywords = ['armor-class', 'ac', 'armour-class']
        
        return any(keyword in subtype or keyword in friendly_type for keyword in ac_keywords)
    
    def _is_natural_armor_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier provides natural armor."""
        subtype = modifier.get('subType', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        return 'natural-armor' in subtype or 'natural armor' in friendly_type
    
    def _has_warforged_integrated_protection(self, raw_data: Dict[str, Any]) -> bool:
        """Check if character has Warforged Integrated Protection."""
        inventory = raw_data.get('inventory', [])
        
        for item in inventory:
            if not item.get('equipped', False):
                continue
                
            # Check both definition structure and direct structure
            item_def = item.get('definition', {})
            item_name_def = item_def.get('name', '')
            item_name_direct = item.get('name', '')
            item_name = (item_name_def or item_name_direct).lower()
            
            # Check for Warforged armor types
            if 'heavy plating' in item_name:
                logger.debug("Detected Warforged Heavy Plating")
                return True
            elif 'composite plating' in item_name:
                logger.debug("Detected Warforged Composite Plating")
                return True
            elif 'darkwood core' in item_name:
                logger.debug("Detected Warforged Darkwood Core")
                return True
        
        return False
    
    def _calculate_warforged_ac(self, raw_data: Dict[str, Any]) -> int:
        """Calculate AC for Warforged Integrated Protection."""
        logger.debug("Calculating Warforged Integrated Protection AC")
        
        # Find the equipped Warforged armor
        inventory = raw_data.get('inventory', [])
        warforged_armor = None
        
        for item in inventory:
            if not item.get('equipped', False):
                continue
                
            # Check both definition structure and direct structure
            item_def = item.get('definition', {})
            item_name_def = item_def.get('name', '')
            item_name_direct = item.get('name', '')
            item_name = (item_name_def or item_name_direct).lower()
            
            if any(armor_type in item_name for armor_type in ['heavy plating', 'composite plating', 'darkwood core']):
                warforged_armor = item
                break
        
        if not warforged_armor:
            logger.warning("Warforged armor detected but not found in inventory")
            return 10
        
        # Get base AC from the armor item - use definition first, then hardcoded values
        armor_def = warforged_armor.get('definition', {})
        base_ac = armor_def.get('armorClass')
        
        # Get armor name from definition or direct
        armor_name_def = armor_def.get('name', '')
        armor_name_direct = warforged_armor.get('name', '')
        armor_name = armor_name_def or armor_name_direct or 'Unknown'
        
        if base_ac is None:
            # Use D&D 5e standard values for Warforged armor
            armor_name_lower = armor_name.lower()
            if 'heavy plating' in armor_name_lower:
                base_ac = 16  # Heavy Plating AC 16
            elif 'composite plating' in armor_name_lower:
                base_ac = 13  # Composite Plating AC 13  
            elif 'darkwood core' in armor_name_lower:
                base_ac = 11  # Darkwood Core AC 11
            else:
                base_ac = 16  # Default to Heavy Plating
                
        logger.debug(f"Warforged armor: {armor_name}, base AC: {base_ac}")
        
        # Get proficiency bonus
        proficiency_bonus = self._get_proficiency_bonus(raw_data)
        
        # Warforged AC = base armor + proficiency bonus
        integrated_ac = base_ac + proficiency_bonus
        
        # Get dex modifier with cap (Heavy Plating caps at 0)
        dex_modifier = self._get_dexterity_modifier(raw_data)
        max_dex = self._get_warforged_max_dex(raw_data, armor_name)
        # For Warforged armor, use the cap value directly (0 for Heavy Plating)
        capped_dex = max_dex
        
        # Get other bonuses that still apply
        try:
            shield_bonus = self._get_shield_bonus(raw_data)
        except Exception as e:
            logger.error(f"Error in shield bonus calculation: {e}")
            shield_bonus = 0
            
        try:
            misc_bonus = self._get_warforged_misc_ac_bonus(raw_data)
        except Exception as e:
            logger.error(f"Error in misc AC bonus calculation: {e}")
            misc_bonus = 0
        
        total_ac = integrated_ac + capped_dex + shield_bonus + misc_bonus
        
        logger.debug(f"Warforged AC: {armor_name} {base_ac} + prof {proficiency_bonus} + dex {capped_dex} (capped at {max_dex}) + shield {shield_bonus} + misc {misc_bonus} = {total_ac}")
        
        return total_ac
    
    def _get_proficiency_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get character's proficiency bonus based on level."""
        classes = raw_data.get('classes', [])
        total_level = sum(cls.get('level', 0) for cls in classes) or 1
        return ((total_level - 1) // 4) + 2
    
    def _get_dexterity_modifier(self, raw_data: Dict[str, Any]) -> int:
        """Get Dexterity modifier from stats."""
        stats = raw_data.get('stats', [])
        for stat in stats:
            if stat.get('id') == 2:  # Dexterity is id 2
                dex_score = stat.get('value', 10)
                return (dex_score - 10) // 2
        return 0
    
    def _get_warforged_max_dex(self, raw_data: Dict[str, Any], armor_name: str) -> int:
        """Get maximum Dex modifier for Warforged armor types."""
        logger.debug(f"_get_warforged_max_dex called with armor_name: {armor_name} (type: {type(armor_name)})")
        
        if armor_name is None:
            logger.warning("armor_name is None, using default Heavy Plating")
            armor_name = "heavy plating"
        
        armor_name = armor_name.lower()
        
        # Check for racial modifiers that set max dex
        modifiers = raw_data.get('modifiers', {})
        racial_modifiers = modifiers.get('race', [])
        
        for modifier in racial_modifiers:
            subtype = modifier.get('subType', '')
            if subtype == 'set/ac-max-dex-modifier':
                max_dex = modifier.get('value', 0)
                logger.debug(f"Found racial max dex modifier: {max_dex}")
                return max_dex
        
        # Fallback based on armor name
        if 'heavy plating' in armor_name:
            return 0  # Heavy Plating caps at 0
        elif 'composite plating' in armor_name:
            return 2  # Composite Plating caps at 2
        elif 'darkwood core' in armor_name:
            return 10  # Darkwood Core has no cap (use large number)
        
        return 0  # Default cap for unknown types
    
    def _get_warforged_misc_ac_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get miscellaneous AC bonuses for Warforged, filtering out problematic racial bonuses."""
        logger.debug("Calculating miscellaneous AC bonuses for Warforged")
        
        misc_bonus = 0
        modifiers = raw_data.get('modifiers', {})
        
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
                
            for modifier in modifier_list:
                if self._is_ac_modifier(modifier):
                    # Skip the +6 racial AC bonus that conflicts with Integrated Protection
                    if source_type == 'race' and modifier.get('value', 0) == 6:
                        logger.debug(f"Skipping conflicting racial AC bonus: +{modifier.get('value', 0)}")
                        continue
                    
                    bonus = modifier.get('value', 0) or 0
                    if bonus != 0:
                        misc_bonus += bonus
                        logger.debug(f"Misc AC bonus: +{bonus} (source: {source_type})")
        
        return misc_bonus
    
    def _is_deflection_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier provides deflection bonus."""
        subtype = modifier.get('subType', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        return 'deflection' in subtype or 'deflection' in friendly_type
    
    def _get_armor_info(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get information about worn armor."""
        inventory = raw_data.get('inventory', [])
        
        for item in inventory:
            if self._is_equipped_armor(item):
                armor_def = item.get('definition', {})
                return {
                    'name': armor_def.get('name', 'Unknown Armor'),
                    'type': armor_def.get('type', 'Unknown'),
                    'ac_bonus': armor_def.get('armorClass', 0),
                    'max_dex': armor_def.get('maxDexModifier')
                }
        
        return None
    
    def _get_shield_info(self, raw_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get information about equipped shield."""
        inventory = raw_data.get('inventory', [])
        
        for item in inventory:
            if self._is_equipped_shield(item):
                item_def = item.get('definition', {})
                armor_class = item_def.get('armorClass')
                
                # Get shield name from definition or top level
                shield_name = item_def.get('name', item.get('name', 'Unknown Shield'))
                
                if armor_class is None or armor_class == 0:
                    # Standard shield provides +2 AC if not defined in data
                    armor_class = 2
                
                # Always check for magical enhancement
                is_attuned = item.get('attuned', False)
                requires_attunement = item.get('requires_attunement', False)
                charges_used = item.get('chargesUsed', 0)
                
                if (is_attuned and not requires_attunement) or (charges_used and charges_used > 0):
                    armor_class += 1
                
                return {
                    'name': shield_name,
                    'ac_bonus': armor_class
                }
        
        return None