"""
Magic Item Parser

Utility for parsing magic item bonuses from D&D Beyond equipment data.
Extracts attack bonuses, damage bonuses, skill bonuses, AC bonuses, and other magical effects.
"""

from typing import Dict, List, Optional, Any, Set
import re
import logging

logger = logging.getLogger(__name__)


class MagicItemBonus:
    """Represents a magic item bonus."""
    
    def __init__(self, bonus_type: str, bonus_value: int, target: str, condition: Optional[str] = None):
        self.bonus_type = bonus_type  # 'attack', 'damage', 'skill', 'ac', 'ability', etc.
        self.bonus_value = bonus_value
        self.target = target  # specific target like 'stealth', 'longsword', 'all_weapons', etc.
        self.condition = condition  # conditional requirements like 'while attuned'
    
    def __repr__(self):
        condition_str = f" ({self.condition})" if self.condition else ""
        return f"{self.bonus_type}:{self.target}:+{self.bonus_value}{condition_str}"


class MagicItemParser:
    """Parser for extracting magic item bonuses from D&D Beyond equipment data."""
    
    # Common magic item bonus patterns
    BONUS_PATTERNS = {
        'weapon_attack_damage': [
            r'\+(\d+)\s+(?:magic\s+)?(?:weapon|sword|axe|bow|crossbow)',
            r'(?:attack|damage)\s+(?:and\s+damage\s+)?rolls?\s+(?:made\s+with\s+this\s+weapon\s+)?(?:gain\s+a\s+)?\+(\d+)\s+bonus',
            r'you\s+(?:have\s+a\s+)?\+(\d+)\s+bonus\s+to\s+attack\s+(?:and\s+damage\s+)?rolls?'
        ],
        'skill_bonus': [
            r'\+(\d+)\s+bonus\s+to\s+(\w+(?:\s+\w+)*)\s+checks?',
            r'(\w+(?:\s+\w+)*)\s+checks?\s+(?:made\s+)?(?:with\s+this\s+item\s+)?(?:gain\s+a\s+)?\+(\d+)\s+bonus',
            r'advantage\s+on\s+(?:\w+\s+)?\((\w+(?:\s+\w+)*)\)\s+checks?',  # "advantage on Dexterity (Stealth) checks"
            r'advantage\s+on\s+(\w+(?:\s+\w+)*)\s+checks?'  # "advantage on Stealth checks"
        ],
        'armor_class': [
            r'\+(\d+)\s+(?:bonus\s+to\s+)?(?:armor\s+class|AC)',
            r'(?:armor\s+class|AC)(?:\s+bonus)?\s+(?:increases?\s+by\s+|is\s+)?\+?(\d+)',
            r'your\s+AC\s+(?:increases?\s+by\s+|is\s+increased\s+by\s+)?\+?(\d+)'
        ],
        'ability_score': [
            r'your\s+(\w+)\s+score\s+is\s+(\d+)',  # "Your Strength score is 19"
            r'your\s+(\w+)\s+(?:score\s+)?(?:increases?\s+by\s+|is\s+)?\+?(\d+)',
            r'\+(\d+)\s+(?:bonus\s+to\s+)?(\w+)\s+(?:ability\s+)?(?:score|modifier)'
        ],
        'saving_throw': [
            r'\+(\d+)\s+bonus\s+to\s+(\w+)\s+saving\s+throws?',
            r'(\w+)\s+saving\s+throws?\s+(?:gain\s+a\s+)?\+(\d+)\s+bonus'
        ]
    }
    
    # Skill name mappings for normalization
    SKILL_MAPPINGS = {
        'sleight of hand': 'sleight_of_hand',
        'animal handling': 'animal_handling',
        # Add more as needed
    }
    
    def __init__(self):
        """Initialize the magic item parser."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def parse_item_bonuses(self, item: Dict[str, Any]) -> List[MagicItemBonus]:
        """
        Parse all bonuses from a magic item.
        
        Args:
            item: Item data from D&D Beyond
            
        Returns:
            List of MagicItemBonus objects
        """
        bonuses = []
        
        if not isinstance(item, dict):
            return bonuses
        
        item_name = item.get('name', 'Unknown Item')
        self.logger.debug(f"Parsing bonuses for item: {item_name}")
        
        # Parse bonuses from item name (e.g., "Longsword +2")
        name_bonuses = self._parse_name_bonuses(item)
        bonuses.extend(name_bonuses)
        
        # Parse bonuses from item description
        description_bonuses = self._parse_description_bonuses(item)
        bonuses.extend(description_bonuses)
        
        # Parse bonuses from item modifiers
        modifier_bonuses = self._parse_modifier_bonuses(item)
        bonuses.extend(modifier_bonuses)
        
        # Parse bonuses from item properties
        property_bonuses = self._parse_property_bonuses(item)
        bonuses.extend(property_bonuses)
        
        self.logger.debug(f"Found {len(bonuses)} bonuses for {item_name}: {bonuses}")
        return bonuses
    
    def _parse_name_bonuses(self, item: Dict[str, Any]) -> List[MagicItemBonus]:
        """Parse bonuses from item name (e.g., 'Longsword +2')."""
        bonuses = []
        item_name = item.get('name', '')
        
        # Look for +X pattern in name
        plus_match = re.search(r'\+(\d+)', item_name)
        if plus_match:
            bonus_value = int(plus_match.group(1))
            
            # Determine if it's a weapon, armor, or other item
            if self._is_weapon(item):
                bonuses.append(MagicItemBonus('attack', bonus_value, 'weapon'))
                bonuses.append(MagicItemBonus('damage', bonus_value, 'weapon'))
            elif self._is_armor(item):
                bonuses.append(MagicItemBonus('ac', bonus_value, 'armor'))
            elif self._is_shield(item):
                bonuses.append(MagicItemBonus('ac', bonus_value, 'shield'))
        
        return bonuses
    
    def _parse_description_bonuses(self, item: Dict[str, Any]) -> List[MagicItemBonus]:
        """Parse bonuses from item description text."""
        bonuses = []
        
        # Get description text
        description = self._get_item_description(item)
        if not description:
            return bonuses
        
        description = description.lower()
        
        # Parse weapon attack/damage bonuses
        for pattern in self.BONUS_PATTERNS['weapon_attack_damage']:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                bonus_value = int(match.group(1))
                if self._is_weapon(item):
                    bonuses.append(MagicItemBonus('attack', bonus_value, 'weapon'))
                    bonuses.append(MagicItemBonus('damage', bonus_value, 'weapon'))
        
        # Parse skill bonuses
        for pattern in self.BONUS_PATTERNS['skill_bonus']:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                if 'advantage' in pattern:
                    bonus_value = 5  # Advantage roughly equivalent to +5
                    skill_name = match.group(1).lower().strip()
                else:
                    # Handle different group orders based on pattern
                    if match.lastindex >= 2:
                        # Pattern like "+2 bonus to Perception checks" or "Perception checks gain a +2 bonus"
                        try:
                            bonus_value = int(match.group(1))
                            skill_name = match.group(2).lower().strip()
                        except ValueError:
                            # Pattern like "Perception checks gain a +2 bonus"
                            skill_name = match.group(1).lower().strip()
                            bonus_value = int(match.group(2))
                    else:
                        continue
                
                # Normalize skill name
                skill_name = self._normalize_skill_name(skill_name)
                if skill_name:
                    bonuses.append(MagicItemBonus('skill', bonus_value, skill_name))
        
        # Parse AC bonuses
        for pattern in self.BONUS_PATTERNS['armor_class']:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                bonus_value = int(match.group(1))
                bonuses.append(MagicItemBonus('ac', bonus_value, 'armor_class'))
        
        # Parse ability score bonuses
        for i, pattern in enumerate(self.BONUS_PATTERNS['ability_score']):
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                if match.lastindex >= 2:
                    ability_name = match.group(1).lower().strip()
                    bonus_value = int(match.group(2))
                    
                    ability_name = self._normalize_ability_name(ability_name)
                    if ability_name:
                        # Check if this is the first pattern (set to X)
                        if i == 0:  # First pattern is "score is X"
                            bonuses.append(MagicItemBonus('ability_set', bonus_value, ability_name))
                        else:
                            bonuses.append(MagicItemBonus('ability', bonus_value, ability_name))
        
        # Parse saving throw bonuses
        for pattern in self.BONUS_PATTERNS['saving_throw']:
            matches = re.finditer(pattern, description, re.IGNORECASE)
            for match in matches:
                if match.lastindex >= 2:
                    bonus_value = int(match.group(1))
                    save_name = match.group(2).lower().strip()
                else:
                    bonus_value = int(match.group(2))
                    save_name = match.group(1).lower().strip()
                
                save_name = self._normalize_ability_name(save_name)
                if save_name:
                    bonuses.append(MagicItemBonus('saving_throw', bonus_value, save_name))
        
        return bonuses
    
    def _parse_modifier_bonuses(self, item: Dict[str, Any]) -> List[MagicItemBonus]:
        """Parse bonuses from D&D Beyond item modifiers."""
        bonuses = []
        
        # Check item definition modifiers
        definition = item.get('definition', {})
        modifiers = definition.get('modifiers', [])
        
        for modifier in modifiers:
            if not isinstance(modifier, dict):
                continue
            
            modifier_type = modifier.get('type', '').lower()
            modifier_subtype = modifier.get('subType', '').lower()
            modifier_value = modifier.get('value', 0)
            
            if modifier_value == 0:
                continue
            
            # Parse different modifier types
            if 'bonus' in modifier_type:
                if 'attack' in modifier_subtype:
                    bonuses.append(MagicItemBonus('attack', modifier_value, 'weapon'))
                elif 'damage' in modifier_subtype:
                    bonuses.append(MagicItemBonus('damage', modifier_value, 'weapon'))
                elif 'armor-class' in modifier_subtype or 'ac' in modifier_subtype:
                    bonuses.append(MagicItemBonus('ac', modifier_value, 'armor_class'))
                elif 'skill' in modifier_subtype:
                    skill_name = modifier.get('friendlySubtypeName', '').lower()
                    skill_name = self._normalize_skill_name(skill_name)
                    if skill_name:
                        bonuses.append(MagicItemBonus('skill', modifier_value, skill_name))
            
            elif 'set' in modifier_type and 'ability-score' in modifier_subtype:
                ability_name = modifier.get('friendlySubtypeName', '').lower()
                ability_name = self._normalize_ability_name(ability_name)
                if ability_name:
                    # Calculate bonus from set score (assuming base 10)
                    set_score = modifier_value
                    current_bonus = (set_score - 10) // 2
                    # This would need character's current score to calculate actual bonus
                    bonuses.append(MagicItemBonus('ability_set', set_score, ability_name))
        
        return bonuses
    
    def _parse_property_bonuses(self, item: Dict[str, Any]) -> List[MagicItemBonus]:
        """Parse bonuses from item properties."""
        bonuses = []
        
        # Check item properties
        definition = item.get('definition', {})
        properties = definition.get('properties', [])
        
        if not properties:
            return bonuses
        
        for prop in properties:
            if not isinstance(prop, dict):
                continue
            
            prop_name = prop.get('name', '').lower()
            prop_description = prop.get('description', '').lower()
            
            # Look for bonus patterns in property descriptions
            if prop_description:
                # This could be expanded to parse specific property bonuses
                pass
        
        return bonuses
    
    def _get_item_description(self, item: Dict[str, Any]) -> Optional[str]:
        """Get item description text."""
        definition = item.get('definition', {})
        
        # Try different description fields
        description = definition.get('description')
        if not description:
            description = definition.get('snippet')
        if not description:
            description = definition.get('notes')
        
        return description
    
    def _is_weapon(self, item: Dict[str, Any]) -> bool:
        """Check if item is a weapon."""
        definition = item.get('definition', {})
        
        # Check filter type
        filter_type = definition.get('filterType', '').lower()
        if filter_type == 'weapon':
            return True
        
        # Check item type
        item_type = definition.get('type', '').lower()
        if 'weapon' in item_type:
            return True
        
        # Check for weapon properties
        if definition.get('weaponProperties'):
            return True
        
        return False
    
    def _is_armor(self, item: Dict[str, Any]) -> bool:
        """Check if item is armor."""
        definition = item.get('definition', {})
        
        # Check filter type
        filter_type = definition.get('filterType', '').lower()
        if filter_type == 'armor':
            return True
        
        # Check item type
        item_type = definition.get('type', '').lower()
        if 'armor' in item_type and 'shield' not in item_type:
            return True
        
        return False
    
    def _is_shield(self, item: Dict[str, Any]) -> bool:
        """Check if item is a shield."""
        definition = item.get('definition', {})
        
        # Check item type
        item_type = definition.get('type', '').lower()
        if 'shield' in item_type:
            return True
        
        # Check item name
        item_name = definition.get('name', '').lower()
        if 'shield' in item_name:
            return True
        
        return False
    
    def _normalize_skill_name(self, skill_name: str) -> Optional[str]:
        """Normalize skill name to match calculator expectations."""
        if not skill_name:
            return None
        
        skill_name = skill_name.lower().strip()
        
        # Use mapping if available
        if skill_name in self.SKILL_MAPPINGS:
            return self.SKILL_MAPPINGS[skill_name]
        
        # Convert spaces to underscores
        skill_name = skill_name.replace(' ', '_')
        
        # Check if it's a valid D&D skill
        valid_skills = {
            'acrobatics', 'animal_handling', 'arcana', 'athletics', 'deception',
            'history', 'insight', 'intimidation', 'investigation', 'medicine',
            'nature', 'perception', 'performance', 'persuasion', 'religion',
            'sleight_of_hand', 'stealth', 'survival'
        }
        
        if skill_name in valid_skills:
            return skill_name
        
        return None
    
    def _normalize_ability_name(self, ability_name: str) -> Optional[str]:
        """Normalize ability name to match calculator expectations."""
        if not ability_name:
            return None
        
        ability_name = ability_name.lower().strip()
        
        # Map common variations
        ability_mappings = {
            'str': 'strength',
            'dex': 'dexterity', 
            'con': 'constitution',
            'int': 'intelligence',
            'wis': 'wisdom',
            'cha': 'charisma'
        }
        
        if ability_name in ability_mappings:
            return ability_mappings[ability_name]
        
        # Check if it's already a valid ability name
        valid_abilities = {'strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'}
        if ability_name in valid_abilities:
            return ability_name
        
        return None
    
    def organize_bonuses_by_type(self, bonuses: List[MagicItemBonus]) -> Dict[str, List[MagicItemBonus]]:
        """Organize bonuses by type for easy lookup."""
        organized = {}
        
        for bonus in bonuses:
            if bonus.bonus_type not in organized:
                organized[bonus.bonus_type] = []
            organized[bonus.bonus_type].append(bonus)
        
        return organized
    
    def get_weapon_bonuses(self, bonuses: List[MagicItemBonus]) -> Dict[str, int]:
        """Extract weapon attack and damage bonuses."""
        weapon_bonuses = {
            'attack_bonus': 0,
            'damage_bonus': 0
        }
        
        for bonus in bonuses:
            if bonus.bonus_type == 'attack' and bonus.target in ['weapon', 'all_weapons']:
                weapon_bonuses['attack_bonus'] += bonus.bonus_value
            elif bonus.bonus_type == 'damage' and bonus.target in ['weapon', 'all_weapons']:
                weapon_bonuses['damage_bonus'] += bonus.bonus_value
        
        return weapon_bonuses
    
    def get_skill_bonuses(self, bonuses: List[MagicItemBonus]) -> Dict[str, int]:
        """Extract skill bonuses."""
        skill_bonuses = {}
        
        for bonus in bonuses:
            if bonus.bonus_type == 'skill':
                skill_name = bonus.target
                if skill_name not in skill_bonuses:
                    skill_bonuses[skill_name] = 0
                skill_bonuses[skill_name] += bonus.bonus_value
        
        return skill_bonuses
    
    def get_ac_bonus(self, bonuses: List[MagicItemBonus]) -> int:
        """Extract armor class bonus."""
        ac_bonus = 0
        
        for bonus in bonuses:
            if bonus.bonus_type == 'ac':
                ac_bonus += bonus.bonus_value
        
        return ac_bonus