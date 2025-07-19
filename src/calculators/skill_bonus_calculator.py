"""
Skill Bonus Calculator

Calculates skill bonuses with ability modifiers, proficiency, expertise, and magic item bonuses.
Handles D&D 5e skill mechanics including expertise doubling and magic item bonuses.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Set
from src.calculators.base import RuleAwareCalculator
from src.calculators.utils.magic_item_parser import MagicItemParser

@dataclass
class SkillBonus:
    """Represents a calculated skill bonus with all bonuses and breakdowns."""
    skill_name: str
    ability_name: str
    ability_modifier: int
    proficiency_bonus: int
    expertise_bonus: int
    magic_bonus: int
    total_bonus: int
    is_proficient: bool
    has_expertise: bool
    breakdown: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def bonus_expression(self) -> str:
        """Get a human-readable bonus expression."""
        parts = []
        
        # Ability modifier
        if self.ability_modifier != 0:
            sign = "+" if self.ability_modifier > 0 else ""
            ability_abbrev = self.ability_name[:3].upper()  # STR, DEX, CON, etc.
            parts.append(f"{sign}{self.ability_modifier} ({ability_abbrev})")
        
        # Proficiency bonus
        if self.proficiency_bonus > 0:
            parts.append(f"+{self.proficiency_bonus} (Prof)")
        
        # Expertise bonus
        if self.expertise_bonus > 0:
            parts.append(f"+{self.expertise_bonus} (Expertise)")
        
        # Magic bonus
        if self.magic_bonus > 0:
            parts.append(f"+{self.magic_bonus} (Magic)")
        
        if not parts:
            return "0"
        
        expression = " ".join(parts)
        # Don't remove leading + for positive ability modifiers
        
        return f"{expression} = {self.total_bonus:+d}"

class SkillBonusCalculator(RuleAwareCalculator):
    """Calculator for skill bonuses with D&D 5e rules."""
    
    # D&D 5e skill to ability mapping
    SKILL_ABILITIES = {
        'acrobatics': 'dexterity',
        'animal_handling': 'wisdom',
        'arcana': 'intelligence',
        'athletics': 'strength',
        'deception': 'charisma',
        'history': 'intelligence',
        'insight': 'wisdom',
        'intimidation': 'charisma',
        'investigation': 'intelligence',
        'medicine': 'wisdom',
        'nature': 'intelligence',
        'perception': 'wisdom',
        'performance': 'charisma',
        'persuasion': 'charisma',
        'religion': 'intelligence',
        'sleight_of_hand': 'dexterity',
        'stealth': 'dexterity',
        'survival': 'wisdom'
    }
    
    def __init__(self, config_manager=None, rule_manager=None):
        """Initialize the skill bonus calculator."""
        super().__init__(config_manager, rule_manager)
        self.magic_item_parser = MagicItemParser()
    
    def calculate(self, character_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate skill bonuses for all skills.
        
        Args:
            character_data: Character data dictionary
            **kwargs: Additional parameters
            
        Returns:
            Dictionary with skill bonus calculations
        """
        if not character_data:
            return {'skill_bonuses': [], 'errors': ['No character data provided']}
        
        errors = []
        warnings = []
        
        try:
            # Detect rule version
            rule_version = self._detect_rule_version(character_data)
            
            # Get required data with fallbacks
            abilities = character_data.get('abilities', {})
            ability_scores = abilities.get('ability_scores', {})
            proficiencies = character_data.get('proficiencies', {})
            character_info = character_data.get('character_info', {})
            equipment = character_data.get('equipment', {})
            
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
            
            # Get skill proficiencies and expertise
            skill_proficiencies = self._extract_skill_proficiencies(proficiencies)
            skill_expertise = self._extract_skill_expertise(proficiencies)
            
            # Get magic item bonuses
            magic_bonuses = self._extract_magic_skill_bonuses(equipment)
            
            # Calculate bonuses for all skills
            skill_bonuses = []
            for skill_name, ability_name in self.SKILL_ABILITIES.items():
                try:
                    skill_bonus = self._calculate_skill_bonus(
                        skill_name=skill_name,
                        ability_name=ability_name,
                        ability_scores=ability_scores,
                        proficiency_bonus=proficiency_bonus,
                        skill_proficiencies=skill_proficiencies,
                        skill_expertise=skill_expertise,
                        magic_bonuses=magic_bonuses,
                        rule_version=rule_version
                    )
                    
                    # Validate calculated skill bonus is reasonable
                    if skill_bonus.total_bonus < -10 or skill_bonus.total_bonus > 30:
                        warnings.append(f"Unusual skill bonus for {skill_name}: {skill_bonus.total_bonus:+d}")
                    
                    skill_bonuses.append(skill_bonus)
                except Exception as e:
                    errors.append(f"Failed to calculate skill bonus for {skill_name}: {str(e)}")
            
            result = {
                'skill_bonuses': skill_bonuses,
                'rule_version': rule_version
            }
            
            if errors:
                result['errors'] = errors
            if warnings:
                result['warnings'] = warnings
                
            return result
            
        except Exception as e:
            return {
                'skill_bonuses': [],
                'rule_version': '2014',
                'errors': [f"Critical error in skill bonus calculation: {str(e)}"]
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
    
    def calculate_specific_skill(
        self,
        skill_name: str,
        character_data: Dict[str, Any],
        **kwargs
    ) -> Optional[SkillBonus]:
        """
        Calculate bonus for a specific skill.
        
        Args:
            skill_name: Name of the skill to calculate
            character_data: Character data dictionary
            **kwargs: Additional parameters
            
        Returns:
            SkillBonus object or None if skill not found
        """
        if skill_name not in self.SKILL_ABILITIES:
            return None
        
        result = self.calculate(character_data, **kwargs)
        skill_bonuses = result.get('skill_bonuses', [])
        
        for skill_bonus in skill_bonuses:
            if skill_bonus.skill_name == skill_name:
                return skill_bonus
        
        return None
    
    def _calculate_proficiency_bonus(self, level: int) -> int:
        """Calculate proficiency bonus based on character level."""
        return 2 + ((level - 1) // 4)
    
    def _calculate_skill_bonus(
        self,
        skill_name: str,
        ability_name: str,
        ability_scores: Dict[str, Any],
        proficiency_bonus: int,
        skill_proficiencies: Set[str],
        skill_expertise: Set[str],
        magic_bonuses: Dict[str, int],
        rule_version: str = "2014"
    ) -> SkillBonus:
        """Calculate bonus for a specific skill."""
        # Get ability modifier
        ability_modifier = self._get_ability_modifier(ability_scores.get(ability_name, {}))
        
        # Check proficiency
        is_proficient = skill_name in skill_proficiencies
        prof_bonus = proficiency_bonus if is_proficient else 0
        
        # Check expertise (doubles proficiency bonus)
        has_expertise = skill_name in skill_expertise
        expertise_bonus = proficiency_bonus if has_expertise else 0
        
        # Get magic bonus
        magic_bonus = magic_bonuses.get(skill_name, 0)
        
        # Calculate total bonus
        total_bonus = ability_modifier + prof_bonus + expertise_bonus + magic_bonus
        
        # Create breakdown
        breakdown = {
            'ability_modifier': ability_modifier,
            'proficiency_bonus': prof_bonus,
            'expertise_bonus': expertise_bonus,
            'magic_bonus': magic_bonus,
            'calculation': f"{ability_modifier} (ability) + {prof_bonus} (prof) + {expertise_bonus} (expertise) + {magic_bonus} (magic)"
        }
        
        return SkillBonus(
            skill_name=skill_name,
            ability_name=ability_name,
            ability_modifier=ability_modifier,
            proficiency_bonus=prof_bonus,
            expertise_bonus=expertise_bonus,
            magic_bonus=magic_bonus,
            total_bonus=total_bonus,
            is_proficient=is_proficient,
            has_expertise=has_expertise,
            breakdown=breakdown
        )
    
    def _extract_skill_proficiencies(self, proficiencies: Dict[str, Any]) -> Set[str]:
        """Extract skill proficiencies from character data."""
        skill_profs = set()
        
        # Extract from skill_proficiencies
        skill_proficiencies = proficiencies.get('skill_proficiencies', [])
        if isinstance(skill_proficiencies, list):
            for prof in skill_proficiencies:
                if isinstance(prof, dict):
                    skill_name = prof.get('name', '').lower().replace(' ', '_')
                    if skill_name in self.SKILL_ABILITIES:
                        skill_profs.add(skill_name)
                elif isinstance(prof, str):
                    skill_name = prof.lower().replace(' ', '_')
                    if skill_name in self.SKILL_ABILITIES:
                        skill_profs.add(skill_name)
        
        return skill_profs
    
    def _extract_skill_expertise(self, proficiencies: Dict[str, Any]) -> Set[str]:
        """Extract skill expertise from character data."""
        skill_expertise = set()
        
        # Extract from skill_expertise
        expertise_list = proficiencies.get('skill_expertise', [])
        if isinstance(expertise_list, list):
            for expertise in expertise_list:
                if isinstance(expertise, dict):
                    skill_name = expertise.get('name', '').lower().replace(' ', '_')
                    if skill_name in self.SKILL_ABILITIES:
                        skill_expertise.add(skill_name)
                elif isinstance(expertise, str):
                    skill_name = expertise.lower().replace(' ', '_')
                    if skill_name in self.SKILL_ABILITIES:
                        skill_expertise.add(skill_name)
        
        # Also check for expertise in class features
        class_features = proficiencies.get('class_features', [])
        if isinstance(class_features, list):
            for feature in class_features:
                if self._is_expertise_feature(feature):
                    expertise_skills = self._extract_expertise_from_feature(feature)
                    skill_expertise.update(expertise_skills)
        
        return skill_expertise
    
    def _extract_magic_skill_bonuses(self, equipment: Dict[str, Any]) -> Dict[str, int]:
        """Extract magic item skill bonuses."""
        magic_bonuses = {}
        
        # Check equipped items for skill bonuses
        equipped_items = equipment.get('equipped_items', [])
        if isinstance(equipped_items, list):
            for item in equipped_items:
                item_bonuses = self._get_item_skill_bonuses(item)
                for skill_name, bonus in item_bonuses.items():
                    magic_bonuses[skill_name] = magic_bonuses.get(skill_name, 0) + bonus
        
        return magic_bonuses
    
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
    
    def _is_expertise_feature(self, feature: Dict[str, Any]) -> bool:
        """Check if a class feature grants expertise."""
        if not isinstance(feature, dict):
            return False
        
        feature_name = feature.get('name', '').lower()
        feature_description = feature.get('description', '').lower()
        
        # Common expertise feature names
        expertise_indicators = [
            'expertise',
            'double proficiency',
            'reliable talent'
        ]
        
        return any(indicator in feature_name or indicator in feature_description 
                  for indicator in expertise_indicators)
    
    def _extract_expertise_from_feature(self, feature: Dict[str, Any]) -> Set[str]:
        """Extract expertise skills from a class feature."""
        expertise_skills = set()
        
        # This would need to be expanded based on how D&D Beyond structures expertise features
        # For now, return empty set as a placeholder
        return expertise_skills
    
    def _get_item_skill_bonuses(self, item: Dict[str, Any]) -> Dict[str, int]:
        """Get skill bonuses from a magic item using enhanced magic item parser."""
        skill_bonuses = {}
        
        if not isinstance(item, dict):
            return skill_bonuses
        
        # Use magic item parser for comprehensive bonus detection
        bonuses = self.magic_item_parser.parse_item_bonuses(item)
        magic_skill_bonuses = self.magic_item_parser.get_skill_bonuses(bonuses)
        
        # Add parsed bonuses
        skill_bonuses.update(magic_skill_bonuses)
        
        # Fallback to legacy detection if parser didn't find anything
        if not skill_bonuses:
            # Check item modifiers for skill bonuses
            modifiers = item.get('modifiers', [])
            if isinstance(modifiers, list):
                for modifier in modifiers:
                    if self._is_skill_modifier(modifier):
                        skill_name, bonus = self._parse_skill_modifier(modifier)
                        if skill_name and skill_name in self.SKILL_ABILITIES:
                            skill_bonuses[skill_name] = bonus
            
            # Check item properties for skill bonuses
            properties = item.get('properties', [])
            if isinstance(properties, list):
                for prop in properties:
                    if self._is_skill_property(prop):
                        skill_name, bonus = self._parse_skill_property(prop)
                        if skill_name and skill_name in self.SKILL_ABILITIES:
                            skill_bonuses[skill_name] = skill_bonuses.get(skill_name, 0) + bonus
        
        return skill_bonuses
    
    def _is_skill_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier affects skills."""
        if not isinstance(modifier, dict):
            return False
        
        modifier_type = modifier.get('type', '').lower()
        modifier_subtype = modifier.get('subType', '').lower()
        
        return 'skill' in modifier_type or 'skill' in modifier_subtype
    
    def _parse_skill_modifier(self, modifier: Dict[str, Any]) -> tuple[Optional[str], int]:
        """Parse a skill modifier to extract skill name and bonus."""
        # This would need to be expanded based on D&D Beyond's modifier structure
        # For now, return placeholder values
        return None, 0
    
    def _is_skill_property(self, prop: Dict[str, Any]) -> bool:
        """Check if a property affects skills."""
        if not isinstance(prop, dict):
            return False
        
        prop_name = prop.get('name', '').lower()
        prop_description = prop.get('description', '').lower()
        
        # Look for skill-related keywords
        skill_keywords = ['skill', 'proficiency', 'expertise', 'advantage']
        return any(keyword in prop_name or keyword in prop_description 
                  for keyword in skill_keywords)
    
    def _parse_skill_property(self, prop: Dict[str, Any]) -> tuple[Optional[str], int]:
        """Parse a skill property to extract skill name and bonus."""
        # This would need to be expanded based on D&D Beyond's property structure
        # For now, return placeholder values
        return None, 0
    
    def get_skills_by_ability(self, ability_name: str) -> List[str]:
        """Get all skills that use a specific ability."""
        return [skill for skill, ability in self.SKILL_ABILITIES.items() 
                if ability == ability_name]
    
    def get_proficient_skills(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of skills the character is proficient in."""
        proficiencies = character_data.get('proficiencies', {})
        return list(self._extract_skill_proficiencies(proficiencies))
    
    def get_expertise_skills(self, character_data: Dict[str, Any]) -> List[str]:
        """Get list of skills the character has expertise in."""
        proficiencies = character_data.get('proficiencies', {})
        return list(self._extract_skill_expertise(proficiencies))
    
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