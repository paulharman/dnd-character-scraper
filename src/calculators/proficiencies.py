"""
Proficiency Calculator

Calculates proficiency bonus, skill proficiencies, and saving throw proficiencies.
Tracks sources of proficiencies for debugging and display.
"""

from typing import Dict, Any, List
import logging

from src.interfaces.calculator import ProficiencyCalculatorInterface
from src.models.character import Character
from src.config.manager import get_config_manager

logger = logging.getLogger(__name__)


class ProficiencyCalculator(ProficiencyCalculatorInterface):
    """
    Calculator for proficiencies with source tracking.
    
    Handles:
    - Proficiency bonus based on character level
    - Skill proficiencies from class, background, race, feats
    - Saving throw proficiencies from class features
    - Expertise (double proficiency) tracking
    - Source attribution for all proficiencies
    """
    
    def __init__(self, config_manager=None):
        self.config_manager = config_manager or get_config_manager()
        self.constants = self.config_manager.get_constants_config()
        
        # Proficiency bonus by level
        self.proficiency_bonus_table = self.constants.proficiency_bonus
        
        # Skill to ability mappings
        self.skill_abilities = self.constants.skills.ability_mappings
        
    def calculate(self, character: Character, raw_data: Dict[str, Any], calculated_abilities: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Calculate all proficiency information.
        
        Returns:
            Dictionary containing proficiency bonus, skills, saving throws, tools, languages, and weapons
        """
        logger.info(f"Calculating proficiencies for character {character.id}")
        
        proficiency_bonus = self.calculate_proficiency_bonus(character)
        skill_proficiencies = self.get_skill_proficiencies(raw_data, calculated_abilities)
        saving_throw_proficiencies = self.get_saving_throw_proficiencies(raw_data)
        tool_proficiencies = self.get_tool_proficiencies(raw_data)
        language_proficiencies = self.get_language_proficiencies(raw_data)
        weapon_proficiencies = self.get_weapon_proficiencies(raw_data)
        
        result = {
            'proficiency_bonus': proficiency_bonus,
            'skill_proficiencies': skill_proficiencies,
            'saving_throw_proficiencies': saving_throw_proficiencies,
            'tool_proficiencies': tool_proficiencies,
            'language_proficiencies': language_proficiencies,
            'weapon_proficiencies': weapon_proficiencies,
            'skills_by_ability': self._group_skills_by_ability(skill_proficiencies)
        }
        
        logger.debug(f"Proficiency bonus: +{proficiency_bonus}")
        logger.debug(f"Skill proficiencies: {len(skill_proficiencies)} skills")
        logger.debug(f"Tool proficiencies: {len(tool_proficiencies)} tools")
        logger.debug(f"Language proficiencies: {len(language_proficiencies)} languages")
        logger.debug(f"Weapon proficiencies: {len(weapon_proficiencies)} weapons")
        logger.debug(f"Saving throw proficiencies: {saving_throw_proficiencies}")
        
        return result
    
    def validate_inputs(self, character: Character, raw_data: Dict[str, Any]) -> bool:
        """Validate that we have sufficient data for proficiency calculation."""
        # Proficiency calculation is quite robust and works with minimal data
        return True
    
    def calculate_proficiency_bonus(self, character: Character) -> int:
        """
        Calculate proficiency bonus based on character level.
        
        Args:
            character: Character data model
            
        Returns:
            Proficiency bonus
        """
        logger.debug(f"Calculating proficiency bonus for level {character.level}")
        
        return self.proficiency_bonus_table.get(character.level, 2)
    
    def get_skill_proficiencies(self, raw_data: Dict[str, Any], calculated_abilities: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """
        Get skill proficiencies with sources.
        
        Args:
            raw_data: Raw D&D Beyond character data
            calculated_abilities: Calculated ability scores from abilities coordinator (optional)
            
        Returns:
            List of skill proficiency dictionaries with sources
        """
        logger.debug("Calculating skill proficiencies")
        
        skills = []
        
        # Get modifiers for skill proficiencies
        modifiers = raw_data.get('modifiers', {})
        
        # Track skills we've seen to merge expertise
        skills_map = {}
        
        # Process modifiers from different sources
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
            
            for modifier in modifier_list:
                if self._is_skill_proficiency_modifier(modifier):
                    skill_info = self._extract_skill_proficiency(modifier, source_type, raw_data)
                    if skill_info:
                        skill_name = skill_info['name']
                        if skill_name in skills_map:
                            # Merge expertise information
                            if skill_info.get('expertise', False):
                                skills_map[skill_name]['expertise'] = True
                        else:
                            skills_map[skill_name] = skill_info
                        logger.debug(f"Skill proficiency: {skill_name} (source: {skill_info['source']}, expertise: {skill_info.get('expertise', False)})")
        
        # Convert map to list
        skills = list(skills_map.values())
        
        # Also check proficiencies array if available
        proficiencies = raw_data.get('proficiencies', [])
        for prof in proficiencies:
            if self._is_skill_proficiency(prof):
                skill_info = self._extract_skill_from_proficiency(prof)
                if skill_info and skill_info['name'] not in skills_map:
                    skills_map[skill_info['name']] = skill_info
        
        # Calculate ability modifiers and total bonuses
        for skill in skills:
            skill['ability_modifier'] = self._get_ability_modifier_for_skill(raw_data, skill['name'], calculated_abilities)
            skill['proficiency_bonus'] = self._get_proficiency_bonus(raw_data)
            
            # For expertise, double the proficiency bonus
            if skill.get('expertise', False):
                skill['expertise_bonus'] = skill['proficiency_bonus']  # Keep for compatibility
                skill['total_bonus'] = skill['ability_modifier'] + (2 * skill['proficiency_bonus'])
            else:
                skill['expertise_bonus'] = 0
                skill['total_bonus'] = skill['ability_modifier'] + skill['proficiency_bonus']
        
        return sorted(skills, key=lambda x: x['name'])
    
    def get_saving_throw_proficiencies(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get saving throw proficiencies.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            List of saving throw proficiency dictionaries with sources
        """
        logger.debug("Calculating saving throw proficiencies")
        
        saving_throws = []
        seen_saves = set()
        
        # Get modifiers for saving throw proficiencies
        modifiers = raw_data.get('modifiers', {})
        
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
            
            for modifier in modifier_list:
                if self._is_saving_throw_modifier(modifier):
                    ability = self._extract_saving_throw_ability(modifier)
                    if ability and ability not in seen_saves:
                        save_info = {
                            'name': ability.title(),
                            'source': self._get_source_name(source_type, raw_data),
                            'source_type': source_type,
                            'description': f'{ability.title()} saving throw proficiency'
                        }
                        saving_throws.append(save_info)
                        seen_saves.add(ability)
                        logger.debug(f"Saving throw proficiency: {ability} (source: {source_type})")
        
        # Also check proficiencies array
        proficiencies = raw_data.get('proficiencies', [])
        for prof in proficiencies:
            if self._is_saving_throw_proficiency(prof):
                ability = self._extract_saving_throw_from_proficiency(prof)
                if ability and ability not in seen_saves:
                    save_info = {
                        'name': ability.title(),
                        'source': 'Proficiency List',
                        'source_type': 'proficiency',
                        'description': f'{ability.title()} saving throw proficiency'
                    }
                    saving_throws.append(save_info)
                    seen_saves.add(ability)
        
        return sorted(saving_throws, key=lambda x: x['name'])
    
    def _is_skill_proficiency_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier grants skill proficiency or expertise."""
        subtype = modifier.get('subType', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        skill_keywords = ['skill', 'proficiency', 'expertise']
        
        return any(keyword in subtype or keyword in friendly_type for keyword in skill_keywords)
    
    def _extract_skill_proficiency(self, modifier: Dict[str, Any], source_type: str, raw_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract skill proficiency information from modifier."""
        # This is simplified - the real implementation would need to map
        # modifier IDs to skill names based on D&D Beyond's schema
        
        friendly_subtype = modifier.get('friendlySubtypeName', '')
        
        # Try to extract skill name
        skill_name = None
        for skill in self.skill_abilities.keys():
            if skill.lower() in friendly_subtype.lower():
                skill_name = skill
                break
        
        if not skill_name:
            return None
        
        # Check for expertise
        is_expertise = 'expertise' in modifier.get('friendlyTypeName', '').lower()
        
        return {
            'name': skill_name,
            'source': self._get_source_name(source_type, raw_data),
            'source_type': source_type,
            'proficient': True,
            'expertise': is_expertise,
            'ability': self.skill_abilities.get(skill_name, 'unknown')
        }
    
    def _is_skill_proficiency(self, proficiency: Dict[str, Any]) -> bool:
        """Check if proficiency entry is for a skill."""
        # Check proficiency type or name patterns
        name = proficiency.get('name', '').lower()
        return any(skill.lower() in name for skill in self.skill_abilities.keys())
    
    def _extract_skill_from_proficiency(self, proficiency: Dict[str, Any]) -> Dict[str, Any]:
        """Extract skill information from proficiency entry."""
        name = proficiency.get('name', '')
        
        # Find matching skill
        skill_name = None
        for skill in self.skill_abilities.keys():
            if skill.lower() in name.lower():
                skill_name = skill
                break
        
        if not skill_name:
            return None
        
        return {
            'name': skill_name,
            'source': 'Proficiency List',
            'source_type': 'proficiency',
            'proficient': True,
            'expertise': False,
            'ability': self.skill_abilities.get(skill_name, 'unknown')
        }
    
    def _is_saving_throw_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier grants saving throw proficiency."""
        subtype = modifier.get('subType', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        save_keywords = ['saving-throw', 'saving-throws', 'save']
        
        return any(keyword in subtype or keyword in friendly_type for keyword in save_keywords)
    
    def _extract_saving_throw_ability(self, modifier: Dict[str, Any]) -> str:
        """Extract ability name from saving throw modifier."""
        friendly_subtype = modifier.get('friendlySubtypeName', '').lower()
        
        abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        
        for ability in abilities:
            if ability in friendly_subtype:
                return ability
        
        return None
    
    def _is_saving_throw_proficiency(self, proficiency: Dict[str, Any]) -> bool:
        """Check if proficiency entry is for a saving throw."""
        name = proficiency.get('name', '').lower()
        abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        
        return any(f"{ability} saving throw" in name for ability in abilities)
    
    def _extract_saving_throw_from_proficiency(self, proficiency: Dict[str, Any]) -> str:
        """Extract ability from saving throw proficiency."""
        name = proficiency.get('name', '').lower()
        abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        
        for ability in abilities:
            if ability in name:
                return ability
        
        return None
    
    def _get_ability_modifier_for_skill(self, raw_data: Dict[str, Any], skill_name: str, calculated_abilities: Dict[str, Any] = None) -> int:
        """Get ability modifier for a specific skill."""
        ability = self.skill_abilities.get(skill_name)
        if not ability:
            return 0
        
        return self._get_ability_modifier(raw_data, ability, calculated_abilities)
    
    def _get_ability_modifier(self, raw_data: Dict[str, Any], ability_name: str, calculated_abilities: Dict[str, Any] = None) -> int:
        """Get ability modifier for given ability."""
        # If we have calculated abilities, use those (they include all bonuses)
        if calculated_abilities and ability_name.lower() in calculated_abilities:
            ability_data = calculated_abilities[ability_name.lower()]
            if isinstance(ability_data, dict) and 'modifier' in ability_data:
                return ability_data['modifier']
            elif isinstance(ability_data, dict) and 'score' in ability_data:
                # Calculate modifier from score if modifier not available
                score = ability_data['score']
                return (score - 10) // 2
        
        # Fallback to raw data if calculated abilities not available
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
            return 0
        
        stats = raw_data.get('stats', [])
        for stat in stats:
            if stat.get('id') == ability_id:
                score = stat.get('value', 10)
                return (score - 10) // 2
        
        return 0
    
    def _get_proficiency_bonus(self, raw_data: Dict[str, Any]) -> int:
        """Get proficiency bonus from character level."""
        total_level = 0
        levels = raw_data.get('levels', [])
        
        for level_data in levels:
            total_level += level_data.get('level', 0)
        
        return self.proficiency_bonus_table.get(total_level, 2)
    
    def _get_source_name(self, source_type: str, raw_data: Dict[str, Any] = None) -> str:
        """Convert source type to friendly name with specific class/race/background names."""
        if source_type == 'class' and raw_data:
            # Get the specific class name
            classes = raw_data.get('classes', [])
            if classes:
                class_name = classes[0].get('definition', {}).get('name', 'Unknown')
                return f'Class: {class_name}'
            return 'Class'
        elif source_type == 'race' and raw_data:
            # Get the specific race/species name
            race_data = raw_data.get('race', {})
            race_name = race_data.get('fullName', race_data.get('baseName', 'Unknown'))
            return f'Species: {race_name}'
        elif source_type == 'background' and raw_data:
            # Get the specific background name
            background_data = raw_data.get('background', {})
            bg_name = background_data.get('definition', {}).get('name', background_data.get('name', 'Unknown'))
            return f'Background: {bg_name}'
        
        source_map = {
            'race': 'Species',
            'class': 'Class',
            'background': 'Background',
            'feat': 'Feat',
            'item': 'Magic Item'
        }
        
        return source_map.get(source_type, source_type.title())
    
    def _group_skills_by_ability(self, skills: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Group skills by their governing ability."""
        grouped = {}
        
        for skill in skills:
            ability = skill.get('ability', 'unknown')
            if ability not in grouped:
                grouped[ability] = []
            grouped[ability].append(skill)
        
        return grouped
    
    def get_tool_proficiencies(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get tool proficiencies with sources.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            List of tool proficiency dictionaries with sources
        """
        logger.debug("Calculating tool proficiencies")
        
        tools = []
        
        # Get modifiers for tool proficiencies
        modifiers = raw_data.get('modifiers', {})
        
        # Track tools we've seen to avoid duplicates
        seen_tools = set()
        
        # Process modifiers from different sources
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
            
            for modifier in modifier_list:
                if self._is_tool_proficiency_modifier(modifier):
                    tool_info = self._extract_tool_proficiency(modifier, source_type, raw_data)
                    if tool_info and tool_info['name'] not in seen_tools:
                        tools.append(tool_info)
                        seen_tools.add(tool_info['name'])
                        logger.debug(f"Tool proficiency: {tool_info['name']} (source: {tool_info['source']})")
        
        return sorted(tools, key=lambda x: x['name'])
    
    def get_language_proficiencies(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get language proficiencies with sources.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            List of language proficiency dictionaries with sources
        """
        logger.debug("Calculating language proficiencies")
        
        languages = []
        
        # Check for languages in modifiers
        modifiers = raw_data.get('modifiers', {})
        seen_languages = set()
        
        # Process modifiers from different sources
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
            
            for modifier in modifier_list:
                if self._is_language_modifier(modifier):
                    lang_info = self._extract_language_proficiency(modifier, source_type, raw_data)
                    if lang_info and lang_info['name'] not in seen_languages:
                        languages.append(lang_info)
                        seen_languages.add(lang_info['name'])
                        logger.debug(f"Language proficiency: {lang_info['name']} (source: {lang_info['source']})")
        
        # Check race features for languages
        race_data = raw_data.get('race', {})
        race_features = race_data.get('features', []) + race_data.get('traits', [])
        
        for feature in race_features:
            if self._is_language_feature(feature):
                lang_info = self._extract_language_from_feature(feature, 'race', raw_data)
                if lang_info and lang_info['name'] not in seen_languages:
                    languages.append(lang_info)
                    seen_languages.add(lang_info['name'])
                    logger.debug(f"Language proficiency from race: {lang_info['name']}")
        
        # Add Common by default (every character knows Common)
        if 'Common' not in seen_languages:
            languages.append({
                'name': 'Common',
                'source': 'Standard',
                'source_type': 'standard',
                'description': 'Universal language known by all player characters'
            })
            
        return sorted(languages, key=lambda x: x['name'])
    
    def get_weapon_proficiencies(self, raw_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Get weapon proficiencies with sources.
        
        Args:
            raw_data: Raw D&D Beyond character data
            
        Returns:
            List of weapon proficiency dictionaries with sources
        """
        logger.debug("Calculating weapon proficiencies")
        
        weapons = []
        
        # Get modifiers for weapon proficiencies
        modifiers = raw_data.get('modifiers', {})
        
        # Track weapons we've seen to avoid duplicates
        seen_weapons = set()
        
        # Process modifiers from different sources
        for source_type, modifier_list in modifiers.items():
            if not isinstance(modifier_list, list):
                continue
            
            for modifier in modifier_list:
                if self._is_weapon_proficiency_modifier(modifier):
                    weapon_info = self._extract_weapon_proficiency(modifier, source_type, raw_data)
                    if weapon_info and weapon_info['name'] not in seen_weapons:
                        weapons.append(weapon_info)
                        seen_weapons.add(weapon_info['name'])
                        logger.debug(f"Weapon proficiency: {weapon_info['name']} (source: {weapon_info['source']})")
        
        return sorted(weapons, key=lambda x: x['name'])
    
    def _is_tool_proficiency_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier grants tool proficiency."""
        subtype = modifier.get('subType', '').lower()
        friendly_subtype = modifier.get('friendlySubtypeName', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        # Tool keywords to look for
        tool_keywords = ['supplies', 'kit', 'tools', 'set', 'instrument']
        
        # Check if it's a tool type or contains tool keywords
        return ('tool' in friendly_type or 
                any(keyword in friendly_subtype for keyword in tool_keywords))
    
    def _extract_tool_proficiency(self, modifier: Dict[str, Any], source_type: str, raw_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract tool proficiency information from modifier."""
        tool_name = modifier.get('friendlySubtypeName', 'Unknown Tool')
        
        return {
            'name': tool_name,
            'source': self._get_source_name(source_type, raw_data),
            'source_type': source_type,
            'description': f'Proficiency with {tool_name}'
        }
    
    def _is_language_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier grants language proficiency."""
        subtype = modifier.get('subType', '').lower()
        friendly_subtype = modifier.get('friendlySubtypeName', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        # Common language names  
        languages = ['common', 'elvish', 'draconic', 'dwarvish', 'halfling', 'gnomish', 'giant', 'goblin', 'orc', 'thieves']
        
        # Check if it's a language-related modifier
        return ('language' in subtype or 'language' in friendly_subtype or 'language' in friendly_type or 
                any(lang in friendly_subtype for lang in languages))
    
    def _extract_language_proficiency(self, modifier: Dict[str, Any], source_type: str, raw_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract language proficiency information from modifier."""
        language_name = modifier.get('friendlySubtypeName', 'Unknown Language')
        
        return {
            'name': language_name,
            'source': self._get_source_name(source_type, raw_data),
            'source_type': source_type,
            'description': f'Can speak, read, and write {language_name}'
        }
    
    def _is_language_feature(self, feature: Dict[str, Any]) -> bool:
        """Check if a race feature grants language proficiency."""
        name = feature.get('name', '').lower()
        description = feature.get('description', '').lower()
        
        return 'language' in name or 'language' in description
    
    def _extract_language_from_feature(self, feature: Dict[str, Any], source_type: str, raw_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract language information from race feature."""
        # This is a simplified extraction - in a real implementation, you'd parse the feature description
        name = feature.get('name', '')
        description = feature.get('description', '')
        
        # Try to extract language name from feature
        languages = ['Common', 'Elvish', 'Draconic', 'Dwarvish', 'Halfling', 'Gnomish', 'Giant', 'Goblin', 'Orc']
        
        for lang in languages:
            if lang.lower() in description.lower():
                return {
                    'name': lang,
                    'source': self._get_source_name(source_type, raw_data),
                    'source_type': source_type,
                    'description': f'Language proficiency from {name}'
                }
        
        return None
    
    def _is_weapon_proficiency_modifier(self, modifier: Dict[str, Any]) -> bool:
        """Check if a modifier grants weapon proficiency."""
        subtype = modifier.get('subType', '').lower()
        friendly_subtype = modifier.get('friendlySubtypeName', '').lower()
        friendly_type = modifier.get('friendlyTypeName', '').lower()
        
        # Weapon keywords to look for
        weapon_keywords = ['weapon', 'simple', 'martial', 'sword', 'bow', 'crossbow', 'dagger', 'staff']
        
        # Check if it's a weapon type or contains weapon keywords
        return ('weapon' in friendly_type or 
                any(keyword in friendly_subtype for keyword in weapon_keywords))
    
    def _extract_weapon_proficiency(self, modifier: Dict[str, Any], source_type: str, raw_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extract weapon proficiency information from modifier."""
        weapon_name = modifier.get('friendlySubtypeName', 'Unknown Weapon')
        
        return {
            'name': weapon_name,
            'source': self._get_source_name(source_type, raw_data),
            'source_type': source_type,
            'description': f'Proficiency with {weapon_name}'
        }