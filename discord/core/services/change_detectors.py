"""
Enhanced Change Detectors

Specialized detectors for comprehensive D&D Beyond character change tracking.
Each detector focuses on a specific type of change with detailed field mappings
and priority classification.
"""

import logging
from typing import Dict, Any, List, Optional, Set
from abc import ABC, abstractmethod
from dataclasses import dataclass

from shared.models.change_detection import (
    FieldChange, ChangeType, ChangePriority, ChangeCategory, DetectionContext
)
from discord.core.models.change_detection_models import (
    EnhancedChangeType, EnhancedFieldMapping, get_field_mapping, get_priority_for_field
)
from discord.core.models.change_log import ChangeAttribution

logger = logging.getLogger(__name__)


def extract_classes_data(character_data: Dict) -> Dict[str, Dict]:
    """
    Universal class data extraction utility.
    
    Returns a dictionary mapping class names to their full class data dictionaries.
    Handles all known data structure variations and provides consistent class name extraction.
    """
    try:
        classes = {}
        class_data = None
        
        # Try different possible paths for class data (prioritized by most common)
        if 'character_info' in character_data and 'classes' in character_data['character_info']:
            class_data = character_data['character_info']['classes']
        elif 'character' in character_data and 'classes' in character_data['character']:
            class_data = character_data['character']['classes']  
        elif 'classes' in character_data:
            class_data = character_data['classes']
        else:
            return {}
        
        # Handle different class data structures
        if isinstance(class_data, list):
            for cls in class_data:
                if isinstance(cls, dict):
                    # Extract class name using multiple fallback strategies
                    class_name = (
                        cls.get('definition', {}).get('name') or  # D&D Beyond API format
                        cls.get('name') or                        # Direct name field
                        cls.get('class_name') or                  # Alternative name field
                        'Unknown Class'                           # Final fallback
                    )
                    classes[class_name] = cls
        elif isinstance(class_data, dict):
            # Already in dict format
            for class_name, cls in class_data.items():
                classes[class_name] = cls if isinstance(cls, dict) else {'name': class_name, 'data': cls}
        
        return classes
        
    except Exception as e:
        logger.warning(f"Error extracting classes: {e}")
        return {}


def extract_classes_list(character_data: Dict) -> List[Dict[str, Any]]:
    """
    Universal class data extraction utility that returns a list.
    
    Returns a list of class data dictionaries.
    """
    class_dict = extract_classes_data(character_data)
    return list(class_dict.values())


def extract_skill_proficiencies_list(character_data: Dict) -> List[str]:
    """
    Universal skill proficiency extraction that returns just the skill names as a list.
    
    Returns list of skill names that character is proficient in.
    """
    skill_dict = extract_skill_proficiencies_data(character_data)
    return [skill for skill, data in skill_dict.items() if data.get('proficient', False)]


def extract_skill_proficiencies_data(character_data: Dict) -> Dict[str, Dict[str, bool]]:
    """
    Universal skill proficiency extraction with expertise tracking.
    
    Returns dict mapping skill names to {'proficient': bool, 'expertise': bool}
    """
    try:
        skills = {}
        
        # Try different possible paths for skill data
        skill_data = None
        if 'character' in character_data:
            if 'proficiencies' in character_data['character'] and 'skills' in character_data['character']['proficiencies']:
                skill_data = character_data['character']['proficiencies']['skills']
            elif 'proficiencies' in character_data['character'] and 'skill_proficiencies' in character_data['character']['proficiencies']:
                skill_data = character_data['character']['proficiencies']['skill_proficiencies']
            elif 'skills' in character_data['character']:
                skill_data = character_data['character']['skills']
        elif 'skills' in character_data:
            skill_data = character_data['skills']
        elif 'proficiencies' in character_data:
            if 'skills' in character_data['proficiencies']:
                skill_data = character_data['proficiencies']['skills']
            elif 'skill_proficiencies' in character_data['proficiencies']:
                skill_data = character_data['proficiencies']['skill_proficiencies']
        
        if skill_data:
            if isinstance(skill_data, dict):
                for skill_name, skill_info in skill_data.items():
                    if isinstance(skill_info, dict):
                        skills[skill_name] = {
                            'proficient': skill_info.get('proficient', False),
                            'expertise': skill_info.get('expertise', False)
                        }
                    elif isinstance(skill_info, bool):
                        skills[skill_name] = {
                            'proficient': skill_info,
                            'expertise': False
                        }
                    else:
                        # Handle other types (maybe strings, numbers)
                        skills[skill_name] = {
                            'proficient': bool(skill_info),
                            'expertise': False
                        }
            elif isinstance(skill_data, list):
                # Handle list of skill objects or skill names
                for skill_item in skill_data:
                    if isinstance(skill_item, dict):
                        # Skill object with detailed info (legacy format)
                        skill_name = skill_item.get('name', 'Unknown')
                        # Normalize skill name to lowercase with underscores for consistency
                        skill_name_normalized = skill_name.lower().replace(' ', '_').replace("'", "")
                        skills[skill_name_normalized] = {
                            'proficient': skill_item.get('proficient', False),
                            'expertise': skill_item.get('expertise', False)
                        }
                    elif isinstance(skill_item, str):
                        # Simple skill name - all proficient, no expertise
                        skills[skill_item] = {
                            'proficient': True,
                            'expertise': False
                        }
        
        return skills
        
    except Exception as e:
        logger.warning(f"Error extracting skill proficiencies: {e}")
        return {}


def extract_skill_proficiencies_list(character_data: Dict) -> List[str]:
    """
    Universal skill proficiency extraction returning simple list.
    
    Returns list of skill names that the character is proficient in.
    """
    skills_dict = extract_skill_proficiencies_data(character_data)
    return [skill for skill, info in skills_dict.items() if info.get('proficient', False)]


def extract_ability_scores_data(character_data: Dict) -> Dict[str, int]:
    """
    Universal ability score extraction handling all data formats.
    
    Returns dict mapping ability names to scores.
    """
    try:
        # Try primary path: abilities.ability_scores (most common in processed files)
        if 'abilities' in character_data and 'ability_scores' in character_data['abilities']:
            ability_scores = character_data['abilities']['ability_scores']
            # Handle nested structure {ability: {score: X, modifier: Y}}
            if ability_scores and isinstance(list(ability_scores.values())[0], dict):
                return {ability: data.get('score', data) if isinstance(data, dict) else data 
                       for ability, data in ability_scores.items()}
            else:
                return ability_scores
                
        # Try alternative paths
        paths_to_try = [
            'character.abilityScores',
            'character.ability_scores', 
            'abilityScores',
            'ability_scores'
        ]
        
        for path in paths_to_try:
            value = character_data
            for key in path.split('.'):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    value = None
                    break
            
            if value and isinstance(value, dict):
                # Handle nested format if needed
                if isinstance(list(value.values())[0], dict):
                    return {ability: data.get('score', data) if isinstance(data, dict) else data 
                           for ability, data in value.items()}
                else:
                    return value
        
        return {}
        
    except Exception as e:
        logger.warning(f"Error extracting ability scores: {e}")
        return {}


def extract_feats_data(character_data: Dict) -> Dict[str, Dict]:
    """
    Universal feats extraction with proper name and ID handling.
    
    Returns dict mapping feat names to feat data dictionaries.
    """
    try:
        feats = {}
        
        # Try different possible paths for feats
        feat_paths = [
            'features.feats',                      # Current system format
            'character.feats',
            'character.featList', 
            'feats',
            'featList'
        ]
        
        feat_data = None
        for path in feat_paths:
            value = character_data
            for key in path.split('.'):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    value = None
                    break
            
            if value:
                feat_data = value
                break
        
        if feat_data:
            if isinstance(feat_data, list):
                for feat in feat_data:
                    if isinstance(feat, dict):
                        # Extract feat name using multiple strategies
                        feat_name = (
                            feat.get('definition', {}).get('name') or
                            feat.get('name') or
                            feat.get('feat_name') or 
                            feat.get('displayName') or
                            'Unknown Feat'
                        )
                        feats[feat_name] = feat
            elif isinstance(feat_data, dict):
                # Already in dict format
                for feat_name, feat_info in feat_data.items():
                    feats[feat_name] = feat_info if isinstance(feat_info, dict) else {'name': feat_name, 'data': feat_info}
        
        return feats
        
    except Exception as e:
        logger.warning(f"Error extracting feats: {e}")
        return {}


def extract_character_level_data(character_data: Dict) -> int:
    """
    Universal character level extraction with multiclass support.
    
    Returns total character level, calculating from classes if needed.
    """
    try:
        # Primary path: character_info.level (most reliable)
        if 'character_info' in character_data and 'level' in character_data['character_info']:
            level = int(character_data['character_info']['level'])
            return level
            
        # Secondary path: nested character.character_info.level
        if 'character' in character_data:
            character = character_data['character']
            if 'character_info' in character and 'level' in character['character_info']:
                level = int(character['character_info']['level'])
                return level
            elif 'level' in character:
                level = int(character['level'])
                return level
                
        # Tertiary path: top-level level field
        if 'level' in character_data:
            level = int(character_data['level'])
            return level
            
        # Calculate from classes if no direct level found
        class_levels = extract_class_levels_data(character_data)
        if class_levels:
            return sum(class_levels.values())
            
        # Check metadata for total_class_levels
        if 'metadata' in character_data and 'total_class_levels' in character_data['metadata']:
            level = int(character_data['metadata']['total_class_levels'])
            return level
            
        return 1  # Default fallback
        
    except (ValueError, TypeError) as e:
        logger.warning(f"Error extracting character level: {e}")
        return 1


def extract_class_levels_data(character_data: Dict) -> Dict[str, int]:
    """
    Universal class level extraction for multiclass characters.
    
    Returns dict mapping class names to their levels.
    """
    try:
        class_levels = {}
        classes = extract_classes_data(character_data)
        
        for class_name, class_info in classes.items():
            if isinstance(class_info, dict) and 'level' in class_info:
                class_levels[class_name] = int(class_info['level'])
                
        return class_levels
        
    except Exception as e:
        logger.warning(f"Error extracting class levels: {e}")
        return {}


def extract_equipment_data(character_data: Dict) -> List[Dict[str, Any]]:
    """
    Universal equipment extraction handling all data structures.
    
    Returns list of equipment/item dictionaries.
    """
    try:
        equipment = []
        
        # Try different possible paths for equipment
        equipment_paths = [
            'character.equipment',
            'character.inventory',
            'equipment',
            'inventory'
        ]
        
        for path in equipment_paths:
            value = character_data
            for key in path.split('.'):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    value = None
                    break
            
            if value:
                if isinstance(value, list):
                    equipment.extend(value)
                elif isinstance(value, dict):
                    # Convert dict to list of items
                    equipment.extend(list(value.values()))
                break
                
        # Also check enhanced_equipment if available
        if 'equipment' in character_data and 'enhanced_equipment' in character_data['equipment']:
            enhanced = character_data['equipment']['enhanced_equipment']
            if isinstance(enhanced, dict):
                equipment.extend(list(enhanced.values()))
            elif isinstance(enhanced, list):
                equipment.extend(enhanced)
        
        return [item for item in equipment if isinstance(item, dict)]
        
    except Exception as e:
        logger.warning(f"Error extracting equipment: {e}")
        return []


def extract_class_features_data(character_data: Dict) -> Dict[str, Any]:
    """
    Universal class features extraction with proper categorization.
    
    Returns dict of class features organized by source.
    """
    try:
        features = {}
        
        # Try different possible paths for features
        feature_paths = [
            'character.features',
            'character.class_features',
            'features',
            'class_features'
        ]
        
        for path in feature_paths:
            value = character_data
            for key in path.split('.'):
                if isinstance(value, dict) and key in value:
                    value = value[key]
                else:
                    value = None
                    break
            
            if value:
                if isinstance(value, dict):
                    features.update(value)
                elif isinstance(value, list):
                    # Convert list to dict using feature names as keys
                    for feature in value:
                        if isinstance(feature, dict):
                            feature_name = (
                                feature.get('definition', {}).get('name') or
                                feature.get('name') or
                                feature.get('displayName') or
                                'Unknown Feature'
                            )
                            features[feature_name] = feature
                break
        
        return features
        
    except Exception as e:
        logger.warning(f"Error extracting class features: {e}")
        return {}


def extract_feat_name_data(feat_data: Any) -> str:
    """
    Universal feat name extraction from various feat data formats.
    
    Returns feat name as string, handling dict, string, and other formats.
    """
    try:
        if isinstance(feat_data, dict):
            return feat_data.get('name', feat_data.get('feat_name', 'Unknown Feat'))
        elif isinstance(feat_data, str):
            return feat_data
        else:
            return 'Unknown Feat'
    except Exception:
        return 'Unknown Feat'


def extract_feature_name_data(feature_data: Any) -> str:
    """
    Universal feature name extraction from various feature data formats.
    
    Returns feature name as string, handling dict, string, and other formats.
    """
    try:
        if isinstance(feature_data, dict):
            # Try multiple possible name paths
            return (feature_data.get('definition', {}).get('name') or
                   feature_data.get('name') or
                   feature_data.get('featureName') or
                   feature_data.get('feature_name') or
                   'Unknown Feature')
        elif isinstance(feature_data, str):
            return feature_data
        else:
            return 'Unknown Feature'
    except Exception:
        return 'Unknown Feature'


def extract_tool_proficiencies_data(character_data: Dict) -> List[str]:
    """
    Universal tool proficiencies extraction with comprehensive path checking.
    
    Returns list of tool names the character is proficient with.
    """
    try:
        tools = []
        
        # Try different possible paths for tool data
        tool_paths = [
            'character.proficiencies.tools',
            'character.proficiencies.tool_proficiencies',
            'character.tools',
            'proficiencies.tools',
            'proficiencies.tool_proficiencies',
            'tools',
            'tool_proficiencies'
        ]
        
        for path in tool_paths:
            tool_data = character_data
            for key in path.split('.'):
                if isinstance(tool_data, dict) and key in tool_data:
                    tool_data = tool_data[key]
                else:
                    tool_data = None
                    break
            
            if tool_data:
                if isinstance(tool_data, list):
                    # Handle list of tool objects or tool names
                    for tool_item in tool_data:
                        if isinstance(tool_item, dict):
                            tool_name = tool_item.get('name', 'Unknown Tool')
                            # If object is in tool_proficiencies array, assume it's proficient
                            # or check if proficient field explicitly set
                            if 'name' in tool_item or tool_item.get('proficient', True):
                                tools.append(tool_name)
                        elif isinstance(tool_item, str):
                            tools.append(tool_item)
                elif isinstance(tool_data, dict):
                    # Handle dict of tools
                    for tool_name, tool_info in tool_data.items():
                        if isinstance(tool_info, bool) and tool_info:
                            tools.append(tool_name)
                        elif isinstance(tool_info, dict) and tool_info.get('proficient', False):
                            tools.append(tool_name)
                
                if tools:  # If we found tools, return them
                    break
        
        return list(set(tools))  # Remove duplicates
        
    except Exception as e:
        logger.warning(f"Error extracting tool proficiencies: {e}")
        return []


def extract_passive_skills_data(character_data: Dict) -> Dict[str, int]:
    """
    Universal passive skills extraction with calculation support.
    
    Returns dict mapping passive skill names to their values.
    """
    try:
        passive_skills = {}
        
        # Try direct passive skill paths first
        passive_paths = [
            'character.passive_skills',
            'character.passiveSkills',
            'passive_skills',
            'passiveSkills',
            'proficiencies.passive_skills',
            'proficiencies.passiveSkills'
        ]
        
        for path in passive_paths:
            passive_data = character_data
            for key in path.split('.'):
                if isinstance(passive_data, dict) and key in passive_data:
                    passive_data = passive_data[key]
                else:
                    passive_data = None
                    break
            
            if passive_data and isinstance(passive_data, dict):
                passive_skills.update(passive_data)
                break
        
        # If no direct passive skills found, try to extract from proficiencies
        if not passive_skills and 'proficiencies' in character_data:
            prof_data = character_data['proficiencies']
            for skill_name in ['passive_perception', 'passive_investigation', 'passive_insight']:
                if skill_name in prof_data:
                    passive_skills[skill_name] = prof_data[skill_name]
        
        return passive_skills
        
    except Exception as e:
        logger.warning(f"Error extracting passive skills: {e}")
        return {}


def extract_weapon_proficiencies_data(character_data: Dict) -> List[str]:
    """
    Universal weapon proficiencies extraction with comprehensive path checking.
    
    Returns list of weapon names the character is proficient with.
    """
    try:
        weapons = []
        
        # Try different possible paths for weapon data
        weapon_paths = [
            'character.proficiencies.weapons',
            'character.proficiencies.weapon_proficiencies', 
            'character.weapons',
            'proficiencies.weapons',
            'proficiencies.weapon_proficiencies',
            'weapons',
            'weapon_proficiencies'
        ]
        
        for path in weapon_paths:
            weapon_data = character_data
            for key in path.split('.'):
                if isinstance(weapon_data, dict) and key in weapon_data:
                    weapon_data = weapon_data[key]
                else:
                    weapon_data = None
                    break
            
            if weapon_data:
                if isinstance(weapon_data, list):
                    # Handle list of weapon objects or weapon names
                    for weapon_item in weapon_data:
                        if isinstance(weapon_item, dict):
                            weapon_name = weapon_item.get('name', 'Unknown Weapon')
                            if weapon_item.get('proficient', True):  # Default to proficient if in list
                                weapons.append(weapon_name)
                        elif isinstance(weapon_item, str):
                            weapons.append(weapon_item)
                elif isinstance(weapon_data, dict):
                    # Handle dict of weapons
                    for weapon_name, weapon_info in weapon_data.items():
                        if isinstance(weapon_info, bool) and weapon_info:
                            weapons.append(weapon_name)
                        elif isinstance(weapon_info, dict) and weapon_info.get('proficient', False):
                            weapons.append(weapon_name)
                
                if weapons:  # If we found weapons, return them
                    break
        
        return list(set(weapons))  # Remove duplicates
        
    except Exception as e:
        logger.warning(f"Error extracting weapon proficiencies: {e}")
        return []


def extract_armor_proficiencies_data(character_data: Dict) -> List[str]:
    """
    Universal armor proficiencies extraction with comprehensive path checking.
    
    Returns list of armor types the character is proficient with.
    """
    try:
        armor = []
        
        # Try different possible paths for armor data
        armor_paths = [
            'character.proficiencies.armor',
            'character.proficiencies.armor_proficiencies',
            'character.armor',
            'proficiencies.armor', 
            'proficiencies.armor_proficiencies',
            'armor',
            'armor_proficiencies'
        ]
        
        for path in armor_paths:
            armor_data = character_data
            for key in path.split('.'):
                if isinstance(armor_data, dict) and key in armor_data:
                    armor_data = armor_data[key]
                else:
                    armor_data = None
                    break
            
            if armor_data:
                if isinstance(armor_data, list):
                    # Handle list of armor objects or armor names
                    for armor_item in armor_data:
                        if isinstance(armor_item, dict):
                            armor_name = armor_item.get('name', 'Unknown Armor')
                            if armor_item.get('proficient', True):  # Default to proficient if in list
                                armor.append(armor_name)
                        elif isinstance(armor_item, str):
                            armor.append(armor_item)
                elif isinstance(armor_data, dict):
                    # Handle dict of armor
                    for armor_name, armor_info in armor_data.items():
                        if isinstance(armor_info, bool) and armor_info:
                            armor.append(armor_name)
                        elif isinstance(armor_info, dict) and armor_info.get('proficient', False):
                            armor.append(armor_name)
                
                if armor:  # If we found armor, return them
                    break
        
        return list(set(armor))  # Remove duplicates
        
    except Exception as e:
        logger.warning(f"Error extracting armor proficiencies: {e}")
        return []


def extract_item_name_data(item_data: Any) -> str:
    """
    Universal item name extraction from various item data formats.
    
    Returns item name as string, handling dict, string, and other formats.
    """
    try:
        if isinstance(item_data, dict):
            # Try multiple possible name paths
            return (item_data.get('definition', {}).get('name') or
                   item_data.get('name') or
                   item_data.get('itemName') or
                   item_data.get('item_name') or
                   'Unknown Item')
        elif isinstance(item_data, str):
            return item_data
        else:
            return 'Unknown Item'
    except Exception:
        return 'Unknown Item'


def extract_character_classes_data(character_data: Dict) -> Dict[str, Dict]:
    """
    Universal classes extraction with level and subclass information.
    
    Returns dict mapping class names to class information.
    """
    try:
        classes = {}
        
        # Try different possible paths for class data
        class_paths = [
            'character_info.classes',
            'character.classes',
            'classes'
        ]
        
        for path in class_paths:
            class_data = character_data
            for key in path.split('.'):
                if isinstance(class_data, dict) and key in class_data:
                    class_data = class_data[key]
                else:
                    class_data = None
                    break
            
            if class_data:
                if isinstance(class_data, list):
                    # Handle list of class objects
                    for class_item in class_data:
                        if isinstance(class_item, dict):
                            class_name = class_item.get('name', 'Unknown Class')
                            classes[class_name] = class_item
                elif isinstance(class_data, dict):
                    # Handle dict of classes
                    classes.update(class_data)
                
                if classes:  # If we found classes, return them
                    break
        
        return classes
        
    except Exception as e:
        logger.warning(f"Error extracting classes: {e}")
        return {}


def extract_race_name_data(race_data: Any) -> str:
    """Universal race name extraction from various race data formats."""
    try:
        if isinstance(race_data, dict):
            # Try different possible name fields for race/species
            return (race_data.get('fullName') or 
                   race_data.get('name') or 
                   race_data.get('raceName') or 
                   race_data.get('race_name') or 
                   'Unknown Race')
        elif isinstance(race_data, str):
            return race_data
        else:
            return 'Unknown Race'
    except Exception:
        return 'Unknown Race'


def extract_background_name_data(background_data: Any) -> str:
    """Universal background name extraction from various background data formats."""
    try:
        if isinstance(background_data, dict):
            return (background_data.get('definition', {}).get('name') or
                   background_data.get('name') or
                   background_data.get('backgroundName') or
                   background_data.get('background_name') or
                   'Unknown Background')
        elif isinstance(background_data, str):
            return background_data
        else:
            return 'Unknown Background'
    except Exception:
        return 'Unknown Background'


def extract_proficiency_bonus_data(character_data: Dict) -> int:
    """Universal proficiency bonus extraction with level-based calculation fallback."""
    try:
        # Try direct proficiency bonus paths
        if 'character_info' in character_data and 'proficiency_bonus' in character_data['character_info']:
            return character_data['character_info']['proficiency_bonus']
        
        if 'character' in character_data and 'proficiency_bonus' in character_data['character']:
            return character_data['character']['proficiency_bonus']
            
        if 'proficiency_bonus' in character_data:
            return character_data['proficiency_bonus']
        
        # Calculate from character level as fallback
        level = extract_character_level_data(character_data)
        return 2 + ((level - 1) // 4)  # Standard D&D proficiency bonus progression
        
    except Exception:
        return 2  # Default proficiency bonus


def extract_classes_list_data(character_data: Dict) -> List[Dict[str, Any]]:
    """
    Universal class data extraction that returns a list of class dictionaries.
    
    Returns a list of class data dictionaries for change detection.
    """
    classes_dict = extract_character_classes_data(character_data)
    return list(classes_dict.values())


def extract_passive_skill_bonus_from_item_data(item_data: Any, skill_name: str) -> int:
    """
    Universal passive skill bonus extraction from item data.
    
    Returns the passive skill bonus provided by an item for a specific skill.
    """
    try:
        bonus = 0
        
        if isinstance(item_data, dict):
            # Check modifiers for passive skill bonuses
            modifiers = item_data.get('modifiers', [])
            if isinstance(modifiers, list):
                for modifier in modifiers:
                    if isinstance(modifier, dict):
                        mod_type = modifier.get('type', '').lower()
                        mod_subtype = modifier.get('subType', '').lower()
                        mod_skill = modifier.get('friendlySubtypeName', '').lower()
                        
                        # Check for passive skill modifiers
                        if (mod_type == 'bonus' and 
                            ('passive' in mod_subtype or 'passive' in mod_skill) and
                            skill_name.lower() in mod_skill):
                            bonus += modifier.get('value', 0)
            
            # Check for other passive bonuses
            if 'passiveBonus' in item_data:
                passive_data = item_data['passiveBonus']
                if isinstance(passive_data, dict):
                    skill_key = skill_name.lower().replace(' ', '_')
                    bonus += passive_data.get(skill_key, 0)
        
        return bonus
        
    except Exception as e:
        logger.warning(f"Error extracting passive skill bonus from item: {e}")
        return 0


def extract_spellcasting_info_data(character_data: Dict) -> Dict[str, Any]:
    """
    Universal spellcasting info extraction utility.
    
    Returns comprehensive spellcasting information including spell save DC, attack bonus, etc.
    """
    try:
        spellcasting_info = {}
        
        # Try different possible paths for spellcasting data
        spellcasting_paths = [
            'character.spellcasting',
            'character.spellcastingInfo',
            'spellcasting',
            'spellcastingInfo'
        ]
        
        for path in spellcasting_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data and isinstance(data, dict):
                spellcasting_info.update(data)
        
        # Ensure we have the key spellcasting stats
        if 'spell_save_dc' not in spellcasting_info:
            # Try to find spell save DC in other locations
            if 'character' in character_data and 'spellSaveDc' in character_data['character']:
                spellcasting_info['spell_save_dc'] = character_data['character']['spellSaveDc']
        
        if 'spell_attack_bonus' not in spellcasting_info:
            # Try to find spell attack bonus in other locations
            if 'character' in character_data and 'spellAttackBonus' in character_data['character']:
                spellcasting_info['spell_attack_bonus'] = character_data['character']['spellAttackBonus']
        
        return spellcasting_info
        
    except Exception as e:
        logger.warning(f"Error extracting spellcasting info: {e}")
        return {}


def extract_spells_data(character_data: Dict) -> Dict[str, List]:
    """
    Universal spell data extraction utility.
    
    Returns dictionary mapping spell levels to lists of spells.
    """
    try:
        spells = {}
        
        # Try different possible paths for spell data
        spell_paths = [
            'character.spells',
            'spells',
            'character.spellbook',
            'spellbook'
        ]
        
        for path in spell_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data:
                if isinstance(data, dict):
                    # Spell data organized by level
                    spells.update(data)
                elif isinstance(data, list):
                    # Flat list of spells - organize by level
                    for spell in data:
                        if isinstance(spell, dict):
                            level = spell.get('level', 0)
                            level_key = f'level_{level}'
                            if level_key not in spells:
                                spells[level_key] = []
                            spells[level_key].append(spell)
                break
        
        return spells
        
    except Exception as e:
        logger.warning(f"Error extracting spells: {e}")
        return {}


def extract_feature_id_data(feature_data: Any) -> str:
    """
    Universal feature ID extraction utility.
    
    Returns the unique identifier for a feature.
    """
    try:
        if isinstance(feature_data, dict):
            # Try different possible ID fields
            return (
                feature_data.get('id') or
                feature_data.get('feature_id') or
                feature_data.get('definitionId') or
                feature_data.get('definition', {}).get('id') or
                str(feature_data.get('name', 'unknown_feature'))
            )
        elif hasattr(feature_data, 'id'):
            return feature_data.id
        elif hasattr(feature_data, 'feature_id'):
            return feature_data.feature_id
        else:
            return str(feature_data) if feature_data else 'unknown_feature'
    except Exception as e:
        logger.warning(f"Error extracting feature ID: {e}")
        return 'unknown_feature'


def extract_spell_slots_data(character_data: Dict) -> Dict[str, int]:
    """
    Universal spell slots extraction utility.
    
    Returns dictionary mapping spell levels to available spell slots.
    """
    try:
        spell_slots = {}
        
        # Try different possible paths for spell slot data
        slot_paths = [
            'character.spellcasting.spell_slots',
            'character.spellSlots',
            'spellcasting.spell_slots',
            'spellSlots'
        ]
        
        for path in slot_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data and isinstance(data, dict):
                spell_slots.update(data)
                break
        
        # Ensure spell slot keys are standardized
        standardized_slots = {}
        for key, value in spell_slots.items():
            if isinstance(key, str) and key.startswith('level_'):
                standardized_slots[key] = value
            elif isinstance(key, str) and key.isdigit():
                standardized_slots[f'level_{key}'] = value
            elif isinstance(key, int):
                standardized_slots[f'level_{key}'] = value
            else:
                standardized_slots[str(key)] = value
        
        return standardized_slots
        
    except Exception as e:
        logger.warning(f"Error extracting spell slots: {e}")
        return {}


def extract_character_levels_data(character_data: Dict) -> Dict[str, int]:
    """
    Universal character levels extraction utility (for multiclass characters).
    
    Returns dictionary mapping class names to their levels.
    """
    try:
        class_levels = {}
        
        # Get class data
        classes_data = extract_character_classes_data(character_data)
        
        for class_name, class_info in classes_data.items():
            if isinstance(class_info, dict):
                level = (
                    class_info.get('level') or
                    class_info.get('class_level') or
                    class_info.get('levels') or
                    1  # Default to level 1
                )
                class_levels[class_name] = level
        
        return class_levels
        
    except Exception as e:
        logger.warning(f"Error extracting character levels: {e}")
        return {}


def extract_constitution_score_data(character_data: Dict) -> int:
    """Universal Constitution score extraction utility."""
    try:
        ability_scores = extract_ability_scores_data(character_data)
        return ability_scores.get('CON', ability_scores.get('Constitution', 10))
    except Exception as e:
        logger.warning(f"Error extracting Constitution score: {e}")
        return 10  # Default Constitution


def extract_total_character_level_data(character_data: Dict) -> int:
    """Universal total character level extraction utility (sum of all class levels)."""
    try:
        # For multiclass characters, sum all class levels
        class_levels = extract_character_levels_data(character_data)
        return sum(class_levels.values()) if class_levels else extract_character_level_data(character_data)
    except Exception as e:
        logger.warning(f"Error extracting total character level: {e}")
        return 1  # Default level


def extract_race_data(character_data: Dict) -> Dict[str, Any]:
    """Universal race data extraction utility."""
    try:
        race_data = {}
        
        # Try different possible paths for race data
        race_paths = [
            'character.race',
            'character.species',  # 2024 rules
            'race',
            'species'
        ]
        
        for path in race_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data and isinstance(data, dict):
                race_data.update(data)
                break
        
        return race_data
        
    except Exception as e:
        logger.warning(f"Error extracting race data: {e}")
        return {}


def extract_skill_bonuses_data(character_data: Dict) -> Dict[str, int]:
    """Universal skill bonuses extraction utility."""
    try:
        skill_bonuses = {}
        
        # Try different paths for skill bonus data
        bonus_paths = [
            'character.skills',
            'character.skill_bonuses',
            'skills',
            'skill_bonuses'
        ]
        
        for path in bonus_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data and isinstance(data, dict):
                for skill_name, bonus_info in data.items():
                    if isinstance(bonus_info, dict):
                        skill_bonuses[skill_name] = bonus_info.get('bonus', bonus_info.get('total', 0))
                    elif isinstance(bonus_info, (int, float)):
                        skill_bonuses[skill_name] = int(bonus_info)
                break
        
        return skill_bonuses
        
    except Exception as e:
        logger.warning(f"Error extracting skill bonuses: {e}")
        return {}


def extract_saving_throws_data(character_data: Dict) -> Dict[str, int]:
    """Universal saving throw bonuses extraction utility."""
    try:
        saving_throws = {}
        
        # Try different paths for saving throw data
        save_paths = [
            'character.saving_throws',
            'character.savingThrows',
            'saving_throws',
            'savingThrows'
        ]
        
        for path in save_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data and isinstance(data, dict):
                for save_name, save_info in data.items():
                    if isinstance(save_info, dict):
                        saving_throws[save_name] = save_info.get('bonus', save_info.get('total', 0))
                    elif isinstance(save_info, (int, float)):
                        saving_throws[save_name] = int(save_info)
                break
        
        return saving_throws
        
    except Exception as e:
        logger.warning(f"Error extracting saving throws: {e}")
        return {}


def extract_language_proficiencies_data(character_data: Dict) -> List[str]:
    """Universal language proficiencies extraction."""
    try:
        languages = []
        
        # Try different possible paths for language data
        language_paths = [
            'character.proficiencies.languages',
            'character.proficiencies.language_proficiencies',
            'character.languages',
            'proficiencies.languages',
            'proficiencies.language_proficiencies',
            'languages',
            'language_proficiencies'
        ]
        
        for path in language_paths:
            lang_data = character_data
            for key in path.split('.'):
                if isinstance(lang_data, dict) and key in lang_data:
                    lang_data = lang_data[key]
                else:
                    lang_data = None
                    break
            
            if lang_data:
                if isinstance(lang_data, list):
                    # Handle list of language objects or language names
                    for lang_item in lang_data:
                        if isinstance(lang_item, dict):
                            lang_name = lang_item.get('name', 'Unknown Language')
                            if lang_item.get('proficient', True):
                                languages.append(lang_name)
                        elif isinstance(lang_item, str):
                            languages.append(lang_item)
                elif isinstance(lang_data, dict):
                    # Handle dict of languages
                    for lang_name, lang_info in lang_data.items():
                        if isinstance(lang_info, bool) and lang_info:
                            languages.append(lang_name)
                        elif isinstance(lang_info, dict) and lang_info.get('proficient', False):
                            languages.append(lang_name)
                
                if languages:  # If we found languages, return them
                    break
        
        return list(set(languages))  # Remove duplicates
        
    except Exception as e:
        logger.warning(f"Error extracting language proficiencies: {e}")
        return []


def extract_spellcasting_stats_data(character_data: Dict) -> Dict[str, Any]:
    """Universal spellcasting stats extraction utility."""
    try:
        stats = {}
        
        # Extract spellcasting info and expand with calculated stats
        spellcasting_info = extract_spellcasting_info_data(character_data)
        stats.update(spellcasting_info)
        
        # Add specific spellcasting ability info
        if 'character' in character_data:
            char_data = character_data['character']
            if 'spellcastingAbility' in char_data:
                stats['spellcasting_ability'] = char_data['spellcastingAbility']
        
        return stats
        
    except Exception as e:
        logger.warning(f"Error extracting spellcasting stats: {e}")
        return {}


def extract_initiative_bonus_data(character_data: Dict) -> int:
    """Universal initiative bonus extraction utility."""
    try:
        # Get DEX modifier as base
        ability_scores = extract_ability_scores_data(character_data)
        dex_score = ability_scores.get('DEX', ability_scores.get('Dexterity', 10))
        init_bonus = (dex_score - 10) // 2
        
        # Check for additional initiative bonuses
        if 'character' in character_data:
            char_data = character_data['character']
            if 'initiative' in char_data:
                init_data = char_data['initiative']
                if isinstance(init_data, dict):
                    init_bonus += init_data.get('bonus', 0)
                elif isinstance(init_data, (int, float)):
                    init_bonus = int(init_data)
        
        return init_bonus
        
    except Exception as e:
        logger.warning(f"Error extracting initiative bonus: {e}")
        return 0


def extract_subclasses_from_features_data(character_data: Dict) -> Dict[str, str]:
    """Universal subclass extraction from features utility."""
    try:
        subclasses = {}
        
        # Get class features and look for subclass indicators
        features = extract_class_features_data(character_data)
        
        for feature_name, feature_data in features.items():
            if isinstance(feature_data, dict):
                # Look for subclass information in feature source or description
                source = feature_data.get('source', '')
                description = feature_data.get('description', '')
                
                # Common subclass feature patterns
                subclass_patterns = [
                    'Domain', 'Circle', 'Path', 'College', 'Archetype', 
                    'Patron', 'Origin', 'Tradition', 'Way', 'Oath'
                ]
                
                for pattern in subclass_patterns:
                    if pattern.lower() in feature_name.lower():
                        # Extract the subclass name
                        subclass_name = feature_name.replace(pattern, '').strip()
                        if subclass_name:
                            subclasses[source or 'Unknown'] = subclass_name
        
        return subclasses
        
    except Exception as e:
        logger.warning(f"Error extracting subclasses from features: {e}")
        return {}


def extract_subclass_name_data(subclass_data: Any) -> str:
    """Universal subclass name extraction utility."""
    try:
        if isinstance(subclass_data, dict):
            return (
                subclass_data.get('name') or
                subclass_data.get('subclass_name') or
                subclass_data.get('definition', {}).get('name') or
                'Unknown Subclass'
            )
        elif isinstance(subclass_data, str):
            return subclass_data
        else:
            return str(subclass_data) if subclass_data else 'Unknown Subclass'
            
    except Exception as e:
        logger.warning(f"Error extracting subclass name: {e}")
        return 'Unknown Subclass'


def extract_spell_list_data(character_data: Dict, spell_type: str = None) -> Dict[str, Dict]:
    """Universal spell list extraction utility.

    Args:
        character_data: Character data dictionary
        spell_type: Optional filter ('known', 'prepared') - currently unused

    Returns:
        Dictionary mapping spell name to spell data
    """
    try:
        spell_dict = {}

        # Get spells data
        spells_data = extract_spells_data(character_data)

        # Flatten spell levels into a dict keyed by spell name
        for level_name, spells in spells_data.items():
            if isinstance(spells, list):
                for spell in spells:
                    if isinstance(spell, dict):
                        name = spell.get('name', spell.get('definition', {}).get('name', ''))
                        if name:
                            spell_dict[name] = spell

        return spell_dict

    except Exception as e:
        logger.warning(f"Error extracting spell list: {e}")
        return {}


def extract_spell_slot_usage_data(character_data: Dict) -> Dict[str, Dict[str, int]]:
    """Universal spell slot usage extraction utility."""
    try:
        usage_data = {}
        
        # Get spell slots and usage information
        spell_slots = extract_spell_slots_data(character_data)
        
        for level, max_slots in spell_slots.items():
            usage_data[level] = {
                'max': max_slots,
                'used': 0,  # Would need to get from character state
                'remaining': max_slots
            }
        
        return usage_data
        
    except Exception as e:
        logger.warning(f"Error extracting spell slot usage: {e}")
        return {}


def extract_equipment_slots_data(character_data: Dict) -> Dict[str, Any]:
    """Universal equipment slots extraction utility."""
    try:
        slots = {}
        
        # Get equipment and organize by slots
        equipment = extract_equipment_data(character_data)
        
        slot_categories = {
            'armor': [], 'shield': [], 'weapon': [], 'ring': [],
            'necklace': [], 'boots': [], 'gloves': [], 'helmet': [],
            'belt': [], 'cloak': [], 'bracers': []
        }
        
        for item in equipment:
            if isinstance(item, dict):
                item_type = item.get('type', '').lower()
                location = item.get('location', '').lower()
                
                for slot_name in slot_categories:
                    if slot_name in item_type or slot_name in location:
                        slot_categories[slot_name].append(item)
                        break
        
        return slot_categories
        
    except Exception as e:
        logger.warning(f"Error extracting equipment slots: {e}")
        return {}


def extract_currencies_data(character_data: Dict) -> Dict[str, int]:
    """Universal currencies extraction utility."""
    try:
        currencies = {}
        
        # Try different paths for currency data
        currency_paths = [
            'character.currencies',
            'character.money',
            'currencies',
            'money'
        ]
        
        for path in currency_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data and isinstance(data, dict):
                currencies.update(data)
                break
        
        # Ensure standard currency types
        standard_currencies = ['cp', 'sp', 'ep', 'gp', 'pp']
        for currency in standard_currencies:
            if currency not in currencies:
                currencies[currency] = 0
        
        return currencies
        
    except Exception as e:
        logger.warning(f"Error extracting currencies: {e}")
        return {'cp': 0, 'sp': 0, 'ep': 0, 'gp': 0, 'pp': 0}


def extract_class_levels_data(character_data: Dict) -> Dict[str, int]:
    """Universal class levels extraction utility (alias for character_levels)."""
    return extract_character_levels_data(character_data)


def extract_background_data(character_data: Dict) -> Dict[str, Any]:
    """Universal background data extraction utility."""
    try:
        background_data = {}
        
        # Try different paths for background data
        bg_paths = [
            'character.background',
            'character.characterBackground',
            'background',
            'characterBackground'
        ]
        
        for path in bg_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data and isinstance(data, dict):
                background_data.update(data)
                break
        
        return background_data
        
    except Exception as e:
        logger.warning(f"Error extracting background data: {e}")
        return {}


def extract_max_hp_data(character_data: Dict) -> int:
    """Universal maximum hit points extraction utility."""
    try:
        # Try different paths for max HP
        hp_paths = [
            'combat.hit_points.maximum',           # Current system format
            'character.hit_points.maximum',
            'character.hitPoints.max',
            'character.maxHitPoints',
            'hit_points.maximum',
            'hitPoints.max',
            'maxHitPoints'
        ]
        
        for path in hp_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data is not None and isinstance(data, (int, float)):
                return int(data)
        
        return 0
        
    except Exception as e:
        logger.warning(f"Error extracting max HP: {e}")
        return 0


def extract_experience_points_data(character_data: Dict) -> int:
    """Universal experience points extraction utility."""
    try:
        # Try different paths for XP
        xp_paths = [
            'character_info.experience_points',    # Current system format
            'character.experience_points',
            'character.experiencePoints',
            'character.xp',
            'experience_points',
            'experiencePoints',
            'xp'
        ]
        
        for path in xp_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data is not None and isinstance(data, (int, float)):
                return int(data)
        
        return 0
        
    except Exception as e:
        logger.warning(f"Error extracting experience points: {e}")
        return 0


def extract_current_hp_data(character_data: Dict) -> int:
    """Universal current hit points extraction utility."""
    try:
        # Try different paths for current HP
        hp_paths = [
            'character.hit_points.current',
            'character.hitPoints.current',
            'character.currentHitPoints',
            'hit_points.current',
            'hitPoints.current',
            'currentHitPoints'
        ]
        
        for path in hp_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data is not None and isinstance(data, (int, float)):
                return int(data)
        
        # Default to max HP if current not found
        return extract_max_hp_data(character_data)
        
    except Exception as e:
        logger.warning(f"Error extracting current HP: {e}")
        return 0


def extract_temporary_hp_data(character_data: Dict) -> int:
    """Universal temporary hit points extraction utility."""
    try:
        # Try different paths for temp HP
        hp_paths = [
            'character.hit_points.temporary',
            'character.hitPoints.temp',
            'character.temporaryHitPoints',
            'hit_points.temporary',
            'hitPoints.temp',
            'temporaryHitPoints'
        ]
        
        for path in hp_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data is not None and isinstance(data, (int, float)):
                return int(data)
        
        return 0
        
    except Exception as e:
        logger.warning(f"Error extracting temporary HP: {e}")
        return 0


def extract_equipped_items_data(character_data: Dict) -> List[Dict]:
    """Universal equipped items extraction utility."""
    try:
        equipped_items = []
        
        # Get all equipment and filter for equipped items
        all_equipment = extract_equipment_data(character_data)
        
        for item in all_equipment:
            if isinstance(item, dict):
                equipped = item.get('equipped', False)
                location = item.get('location', '').lower()
                
                if equipped or any(slot in location for slot in ['equipped', 'worn', 'wielded']):
                    equipped_items.append(item)
        
        return equipped_items
        
    except Exception as e:
        logger.warning(f"Error extracting equipped items: {e}")
        return []


def extract_personality_data_data(character_data: Dict) -> Dict[str, Any]:
    """Universal personality data extraction utility."""
    try:
        personality = {}
        
        # Try different paths for personality data
        personality_paths = [
            'character.personality',
            'character.traits',
            'character.personalityTraits',
            'personality',
            'traits',
            'personalityTraits'
        ]
        
        for path in personality_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data and isinstance(data, dict):
                personality.update(data)
        
        # Ensure standard personality fields
        standard_fields = ['traits', 'ideals', 'bonds', 'flaws']
        for field in standard_fields:
            if field not in personality:
                personality[field] = ''
        
        return personality
        
    except Exception as e:
        logger.warning(f"Error extracting personality data: {e}")
        return {'traits': '', 'ideals': '', 'bonds': '', 'flaws': ''}


def extract_background_traits_data(character_data: Dict) -> List[str]:
    """Universal background traits extraction utility."""
    try:
        background_data = extract_background_data(character_data)
        traits = background_data.get('traits', [])
        
        if isinstance(traits, list):
            return traits
        elif isinstance(traits, str):
            return [traits] if traits else []
        else:
            return []
            
    except Exception as e:
        logger.warning(f"Error extracting background traits: {e}")
        return []


def extract_background_features_data(character_data: Dict) -> List[Dict]:
    """Universal background features extraction utility."""
    try:
        background_data = extract_background_data(character_data)
        features = background_data.get('features', [])
        
        if isinstance(features, list):
            return features
        elif isinstance(features, dict):
            return [features]
        else:
            return []
            
    except Exception as e:
        logger.warning(f"Error extracting background features: {e}")
        return []


def extract_saving_throw_proficiencies_data(character_data: Dict) -> List[str]:
    """Universal saving throw proficiencies extraction utility."""
    try:
        proficiencies = []
        
        # Try different paths for saving throw proficiencies
        save_prof_paths = [
            'proficiencies.saving_throw_proficiencies',  # New format (current)
            'character.proficiencies.savingThrows',      # Legacy format
            'character.savingThrowProficiencies',        # Alternative legacy
            'proficiencies.savingThrows',                # Alternative format
            'savingThrowProficiencies'                   # Simple format
        ]
        
        for path in save_prof_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data:
                if isinstance(data, list):
                    # Handle new format: list of objects with 'name' field
                    for item in data:
                        if isinstance(item, dict) and 'name' in item:
                            proficiencies.append(item['name'])
                        elif isinstance(item, str):
                            proficiencies.append(item)
                elif isinstance(data, dict):
                    # Handle new enhanced calculator format: dict with detailed proficiency data
                    for save, proficiency_data in data.items():
                        if isinstance(proficiency_data, dict):
                            # New format: {'constitution': {'proficient': True, ...}}
                            if proficiency_data.get('proficient', False):
                                proficiencies.append(save)
                        elif proficiency_data:
                            # Legacy format: {'constitution': True}
                            proficiencies.append(save)
                break
        
        return list(set(proficiencies))  # Remove duplicates
        
    except Exception as e:
        logger.warning(f"Error extracting saving throw proficiencies: {e}")
        return []


def extract_racial_traits_data(character_data: Dict) -> List[Dict]:
    """Universal racial traits extraction utility."""
    try:
        race_data = extract_race_data(character_data)
        traits = race_data.get('traits', [])
        
        if isinstance(traits, list):
            return traits
        elif isinstance(traits, dict):
            return [traits]
        else:
            return []
            
    except Exception as e:
        logger.warning(f"Error extracting racial traits: {e}")
        return []


def extract_racial_bonuses_data(character_data: Dict) -> Dict[str, int]:
    """Universal racial bonuses extraction utility."""
    try:
        race_data = extract_race_data(character_data)
        bonuses = race_data.get('bonuses', {})
        
        if isinstance(bonuses, dict):
            return bonuses
        else:
            return {}
            
    except Exception as e:
        logger.warning(f"Error extracting racial bonuses: {e}")
        return {}


def extract_proficiencies_data(character_data: Dict) -> Dict[str, List[str]]:
    """Universal proficiencies extraction utility."""
    try:
        all_proficiencies = {
            'skills': extract_skill_proficiencies_list(character_data),
            'tools': extract_tool_proficiencies_data(character_data),
            'languages': extract_language_proficiencies_data(character_data),
            'weapons': extract_weapon_proficiencies_data(character_data),
            'armor': extract_armor_proficiencies_data(character_data),
            'saving_throws': extract_saving_throw_proficiencies_data(character_data)
        }
        
        return all_proficiencies
        
    except Exception as e:
        logger.warning(f"Error extracting proficiencies: {e}")
        return {'skills': [], 'tools': [], 'languages': [], 'weapons': [], 'armor': [], 'saving_throws': []}


def extract_background_personality_traits_data(character_data: Dict) -> List[str]:
    """Universal background personality traits extraction utility."""
    try:
        background_data = extract_background_data(character_data)
        personality_traits = background_data.get('personalityTraits', [])
        
        if isinstance(personality_traits, list):
            return personality_traits
        elif isinstance(personality_traits, str):
            return [personality_traits] if personality_traits else []
        else:
            return []
            
    except Exception as e:
        logger.warning(f"Error extracting background personality traits: {e}")
        return []


def extract_initiative_info_data(character_data: Dict) -> Dict[str, Any]:
    """Universal initiative info extraction utility."""
    try:
        initiative_info = {
            'bonus': extract_initiative_bonus_data(character_data),
            'dex_modifier': (extract_ability_scores_data(character_data).get('DEX', 10) - 10) // 2,
            'additional_bonuses': []
        }
        
        return initiative_info
        
    except Exception as e:
        logger.warning(f"Error extracting initiative info: {e}")
        return {'bonus': 0, 'dex_modifier': 0, 'additional_bonuses': []}


def extract_initiative_bonus_from_item_data(item_data: Any) -> int:
    """Universal initiative bonus from item extraction utility."""
    try:
        bonus = 0
        
        if isinstance(item_data, dict):
            modifiers = item_data.get('modifiers', [])
            for mod in modifiers:
                if isinstance(mod, dict):
                    mod_type = mod.get('type', '').lower()
                    if 'initiative' in mod_type:
                        bonus += mod.get('value', 0)
        
        return bonus
        
    except Exception as e:
        logger.warning(f"Error extracting initiative bonus from item: {e}")
        return 0


def extract_alignment_info_data(character_data: Dict) -> Dict[str, Any]:
    """Universal alignment info extraction utility."""
    try:
        alignment_info = {}
        
        # Try different paths for alignment data
        alignment_paths = [
            'character.alignment',
            'character.alignmentId',
            'alignment',
            'alignmentId'
        ]
        
        for path in alignment_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data is not None:
                if 'Id' in path:
                    alignment_info['alignment_id'] = data
                else:
                    alignment_info['alignment'] = data
        
        return alignment_info
        
    except Exception as e:
        logger.warning(f"Error extracting alignment info: {e}")
        return {}


def extract_size_info_data(character_data: Dict) -> Dict[str, Any]:
    """Universal size info extraction utility."""
    try:
        size_info = {}
        
        # Try different paths for size data
        size_paths = [
            'character.size',
            'character.sizeId',
            'size',
            'sizeId'
        ]
        
        for path in size_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data is not None:
                if 'Id' in path:
                    size_info['size_id'] = data
                else:
                    size_info['size'] = data
        
        return size_info
        
    except Exception as e:
        logger.warning(f"Error extracting size info: {e}")
        return {}


def extract_movement_speeds_data(character_data: Dict) -> Dict[str, int]:
    """Universal movement speeds extraction utility."""
    try:
        speeds = {}
        
        # Try different paths for speed data
        speed_paths = [
            'character.speed',
            'character.speeds',
            'character.movement',
            'speed',
            'speeds',
            'movement'
        ]
        
        for path in speed_paths:
            data = character_data
            for key in path.split('.'):
                if isinstance(data, dict) and key in data:
                    data = data[key]
                else:
                    data = None
                    break
            
            if data and isinstance(data, dict):
                speeds.update(data)
                break
            elif data and isinstance(data, (int, float)):
                speeds['walk'] = int(data)
                break
        
        # Ensure standard movement types
        if 'walk' not in speeds:
            speeds['walk'] = 30
        
        return speeds
        
    except Exception as e:
        logger.warning(f"Error extracting movement speeds: {e}")
        return {'walk': 30, 'fly': 0, 'swim': 0, 'climb': 0, 'burrow': 0}


class BaseEnhancedDetector(ABC):
    """Base class for enhanced change detectors."""
    
    def __init__(self, field_mappings: Dict[str, EnhancedFieldMapping], 
                 priority_rules: Dict[str, ChangePriority]):
        self.field_mappings = field_mappings
        self.priority_rules = priority_rules
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect changes specific to this detector's domain."""
        pass
    
    def _extract_relevant_data(self, character_data: Dict, field_patterns: List[str]) -> Dict:
        """Extract only the data relevant to this detector."""
        relevant_data = {}
        
        for pattern in field_patterns:
            # Simple pattern matching - in practice, you'd want more sophisticated extraction
            if '.' in pattern:
                parts = pattern.split('.')
                current = character_data
                
                try:
                    for part in parts:
                        if part == '*':
                            # Handle wildcard - for now, just take the whole current level
                            relevant_data[pattern] = current
                            break
                        elif isinstance(current, dict) and part in current:
                            current = current[part]
                        else:
                            current = None
                            break
                    
                    if current is not None and pattern not in relevant_data:
                        relevant_data[pattern] = current
                        
                except (KeyError, TypeError, AttributeError):
                    continue
        
        return relevant_data
    
    def _determine_priority(self, field_path: str, change_type: ChangeType) -> ChangePriority:
        """Determine priority based on field and change type."""
        # Check explicit priority rules first
        if field_path in self.priority_rules:
            return self.priority_rules[field_path]
        
        # Use field mapping priority
        mapping = get_field_mapping(field_path)
        if mapping:
            return mapping.priority
        
        # Default priority based on change type
        if change_type in [ChangeType.ADDED, ChangeType.REMOVED]:
            return ChangePriority.HIGH
        elif change_type in [ChangeType.INCREMENTED, ChangeType.DECREMENTED]:
            return ChangePriority.MEDIUM
        else:
            return ChangePriority.LOW
    
    def _create_field_change(self, field_path: str, old_value: Any, new_value: Any,
                           change_type: ChangeType, category: ChangeCategory,
                           description: str = None) -> FieldChange:
        """Create a FieldChange with appropriate metadata."""
        priority = self._determine_priority(field_path, change_type)
        
        return FieldChange(
            field_path=field_path,
            old_value=old_value,
            new_value=new_value,
            change_type=change_type,
            priority=priority,
            category=category,
            description=description or f"{field_path} changed",
            metadata={
                'detector': self.__class__.__name__,
                'enhanced_change_type': change_type.value if hasattr(change_type, 'value') else str(change_type)
            }
        )


class FeatsChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for feat additions, removals, and modifications with detailed attribution."""
    
    def __init__(self):
        field_mappings = {
            'feats': EnhancedFieldMapping(
                api_path='character.feats',
                display_name='Feats',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.FEATURES
            )
        }
        priority_rules = {
            'character.feats': ChangePriority.HIGH,
            'character.feats.*': ChangePriority.HIGH
        }
        super().__init__(field_mappings, priority_rules)
        
        # Load feat mechanical effects database
        self.feat_effects = self._load_feat_effects_database()
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect feat changes with detailed attribution and secondary effects."""
        changes = []
        
        try:
            old_feats = extract_feats_data(old_data)
            new_feats = extract_feats_data(new_data)
            
            # Detect added feats
            for feat_id, feat_data in new_feats.items():
                if feat_id not in old_feats:
                    feat_name = extract_feat_name_data(feat_data)
                    feat_change = self._create_enhanced_feat_change(
                        field_path=f'character.feats.{feat_id}',
                        old_value=None,
                        new_value=feat_data,
                        change_type=ChangeType.ADDED,
                        feat_name=feat_name,
                        context=context
                    )
                    changes.append(feat_change)
                    
                    # Detect secondary changes caused by this feat
                    secondary_changes = self._detect_feat_secondary_changes(
                        feat_name, feat_data, old_data, new_data, context
                    )
                    changes.extend(secondary_changes)
            
            # Detect removed feats
            for feat_id, feat_data in old_feats.items():
                if feat_id not in new_feats:
                    feat_name = extract_feat_name_data(feat_data)
                    
                    # Check if this "removed" feat exists as a class feature (deduplication scenario)
                    if self._feat_exists_as_class_feature(feat_name, new_data):
                        self.logger.debug(f"Skipping feat removal for '{feat_name}' - exists as class feature (deduplication)")
                        continue
                    
                    feat_change = self._create_enhanced_feat_change(
                        field_path=f'character.feats.{feat_id}',
                        old_value=feat_data,
                        new_value=None,
                        change_type=ChangeType.REMOVED,
                        feat_name=feat_name,
                        context=context
                    )
                    changes.append(feat_change)
            
            # Detect modified feats
            for feat_id in old_feats.keys() & new_feats.keys():
                if old_feats[feat_id] != new_feats[feat_id]:
                    # Check if the difference is only cosmetic (name cleaning)
                    if self._is_cosmetic_feat_change(old_feats[feat_id], new_feats[feat_id]):
                        # Skip cosmetic changes like "4: Weapon Mastery" -> "Weapon Mastery"
                        continue
                    
                    feat_name = extract_feat_name_data(new_feats[feat_id])
                    feat_change = self._create_enhanced_feat_change(
                        field_path=f'character.feats.{feat_id}',
                        old_value=old_feats[feat_id],
                        new_value=new_feats[feat_id],
                        change_type=ChangeType.MODIFIED,
                        feat_name=feat_name,
                        context=context
                    )
                    changes.append(feat_change)
            
            self.logger.debug(f"Detected {len(changes)} feat changes (including secondary effects)")
            
        except Exception as e:
            self.logger.error(f"Error detecting feat changes: {e}", exc_info=True)
        
        return changes
    
    def _create_enhanced_feat_change(self, field_path: str, old_value: Any, new_value: Any,
                                   change_type: ChangeType, feat_name: str, 
                                   context: DetectionContext) -> FieldChange:
        """Create an enhanced feat change with detailed attribution."""
        # Get feat mechanical effects
        feat_effects = self.feat_effects.get(feat_name.lower(), {})
        
        # Create detailed description
        if change_type == ChangeType.ADDED:
            description = f"Added feat: {feat_name}"
            detailed_description = self._create_feat_added_description(feat_name, feat_effects)
        elif change_type == ChangeType.REMOVED:
            description = f"Removed feat: {feat_name}"
            detailed_description = f"Removed feat: {feat_name}. Lost all associated benefits and abilities."
        else:
            description = f"Modified feat: {feat_name}"
            detailed_description = f"Modified feat: {feat_name}. Usage or configuration changed."
        
        # Create the field change with enhanced metadata
        change = self._create_field_change(
            field_path=field_path,
            old_value=old_value,
            new_value=new_value,
            change_type=change_type,
            category=ChangeCategory.FEATURES,
            description=description
        )
        
        # Add enhanced metadata
        change.metadata.update({
            'feat_name': feat_name,
            'feat_effects': feat_effects,
            'detailed_description': detailed_description,
            'causation_trigger': 'feat_selection',
            'secondary_effects_expected': len(feat_effects.get('affects', [])) > 0
        })
        
        return change
    
    def _feat_exists_as_class_feature(self, feat_name: str, character_data: Dict) -> bool:
        """
        Check if a feat exists as a class feature in the character data.
        
        This helps identify when a feat removal is actually just deduplication
        where the feat has been moved to the class features section.
        
        Args:
            feat_name: Name of the feat to check
            character_data: Complete character data dictionary
            
        Returns:
            True if the feat exists as a class feature, False otherwise
        """
        try:
            # Check multiple possible paths for class features
            class_features_paths = [
                'features.class_features',
                'class_features',
                'character.class_features'
            ]
            
            cleaned_feat_name = feat_name.lower().strip()
            
            for path in class_features_paths:
                value = character_data
                for key in path.split('.'):
                    if isinstance(value, dict) and key in value:
                        value = value[key]
                    else:
                        value = None
                        break
                
                if value and isinstance(value, list):
                    # Check each class feature in the list
                    for feature in value:
                        if isinstance(feature, dict):
                            feature_name = (
                                feature.get('name') or
                                feature.get('displayName') or
                                feature.get('definition', {}).get('name', '')
                            )
                            if feature_name:
                                cleaned_feature_name = feature_name.lower().strip()
                                if cleaned_feat_name == cleaned_feature_name:
                                    self.logger.debug(f"Found feat '{feat_name}' as class feature '{feature_name}'")
                                    return True
                    
            return False
            
        except Exception as e:
            self.logger.warning(f"Error checking if feat exists as class feature: {e}")
            return False

    def _is_cosmetic_feat_change(self, old_feat: Dict, new_feat: Dict) -> bool:
        """
        Check if the change between two feat dictionaries is only cosmetic.
        
        Cosmetic changes include:
        - Name cleaning (removing level prefixes like "4:")
        - Description formatting changes
        - Other non-functional differences
        
        Args:
            old_feat: Old feat dictionary
            new_feat: New feat dictionary
            
        Returns:
            True if the change is only cosmetic, False if it's a functional change
        """
        # Extract names and clean them for comparison
        old_name = old_feat.get('name', '')
        new_name = new_feat.get('name', '')
        
        # Clean both names by removing level prefixes
        import re
        clean_old_name = re.sub(r'^\d+:\s*', '', old_name).strip()
        clean_new_name = re.sub(r'^\d+:\s*', '', new_name).strip()
        
        # If cleaned names are the same, check if other fields are substantially the same
        if clean_old_name.lower() == clean_new_name.lower():
            # Compare other important fields (description, effects, etc.)
            old_desc = old_feat.get('description', '').strip()
            new_desc = new_feat.get('description', '').strip()
            
            # If descriptions are the same or only differ in formatting, it's cosmetic
            if old_desc == new_desc:
                return True
            
            # Could add more sophisticated description comparison here if needed
            # For now, if names match but descriptions differ, consider it functional
        
        return False
    
    def _detect_feat_secondary_changes(self, feat_name: str, feat_data: Dict, 
                                     old_data: Dict, new_data: Dict, 
                                     context: DetectionContext) -> List[FieldChange]:
        """Detect secondary changes caused by feat selection."""
        secondary_changes = []
        feat_effects = self.feat_effects.get(feat_name.lower(), {})
        
        try:
            # Check for ability score increases
            if 'ability_score_increase' in feat_effects:
                ability_changes = self._detect_feat_ability_score_changes(
                    feat_name, feat_effects['ability_score_increase'], old_data, new_data
                )
                secondary_changes.extend(ability_changes)
            
            # Check for proficiency grants
            if 'proficiencies' in feat_effects:
                proficiency_changes = self._detect_feat_proficiency_changes(
                    feat_name, feat_effects['proficiencies'], old_data, new_data
                )
                secondary_changes.extend(proficiency_changes)
            
            # Check for spell grants
            if 'spells' in feat_effects:
                spell_changes = self._detect_feat_spell_changes(
                    feat_name, feat_effects['spells'], old_data, new_data
                )
                secondary_changes.extend(spell_changes)
            
            # Check for combat option grants
            if 'combat_options' in feat_effects:
                combat_changes = self._detect_feat_combat_changes(
                    feat_name, feat_effects['combat_options'], old_data, new_data
                )
                secondary_changes.extend(combat_changes)
            
            # Mark all secondary changes as caused by this feat
            for change in secondary_changes:
                change.metadata.update({
                    'caused_by_feat': feat_name,
                    'causation_trigger': 'feat_selection',
                    'causation_source': f'character.feats.{feat_name.lower().replace(" ", "_")}'
                })
            
        except Exception as e:
            self.logger.error(f"Error detecting secondary changes for feat {feat_name}: {e}", exc_info=True)
        
        return secondary_changes
    
    def _detect_feat_ability_score_changes(self, feat_name: str, ability_increases: Dict,
                                         old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect ability score changes caused by feat."""
        changes = []
        
        try:
            old_abilities = extract_ability_scores_data(old_data)
            new_abilities = extract_ability_scores_data(new_data)
            
            for ability, increase in ability_increases.items():
                old_score = old_abilities.get(ability, 10)
                new_score = new_abilities.get(ability, 10)
                
                if new_score > old_score:
                    change = self._create_field_change(
                        field_path=f'character.ability_scores.{ability}',
                        old_value=old_score,
                        new_value=new_score,
                        change_type=ChangeType.INCREMENTED,
                        category=ChangeCategory.ABILITIES,
                        description=f"{ability.title()} increased by {new_score - old_score} (from {feat_name} feat)"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting ability score changes for feat {feat_name}: {e}")
        
        return changes
    
    def _detect_feat_proficiency_changes(self, feat_name: str, proficiencies: Dict,
                                       old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect proficiency changes caused by feat."""
        changes = []
        
        try:
            # Check skill proficiencies
            if 'skills' in proficiencies:
                skill_changes = self._detect_skill_proficiency_changes(
                    feat_name, proficiencies['skills'], old_data, new_data
                )
                changes.extend(skill_changes)
            
            # Check tool proficiencies
            if 'tools' in proficiencies:
                tool_changes = self._detect_tool_proficiency_changes(
                    feat_name, proficiencies['tools'], old_data, new_data
                )
                changes.extend(tool_changes)
            
            # Check weapon proficiencies
            if 'weapons' in proficiencies:
                weapon_changes = self._detect_weapon_proficiency_changes(
                    feat_name, proficiencies['weapons'], old_data, new_data
                )
                changes.extend(weapon_changes)
            
            # Check armor proficiencies
            if 'armor' in proficiencies:
                armor_changes = self._detect_armor_proficiency_changes(
                    feat_name, proficiencies['armor'], old_data, new_data
                )
                changes.extend(armor_changes)
        
        except Exception as e:
            self.logger.error(f"Error detecting proficiency changes for feat {feat_name}: {e}")
        
        return changes
    
    def _detect_feat_spell_changes(self, feat_name: str, spells: Dict,
                                 old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect spell changes caused by feat."""
        changes = []
        
        try:
            old_spells = extract_spells_data(old_data)
            new_spells = extract_spells_data(new_data)
            
            # Check for new spells known
            for spell_name in spells.get('known', []):
                if spell_name not in old_spells.get('known', []) and spell_name in new_spells.get('known', []):
                    change = self._create_field_change(
                        field_path=f'character.spells.known.{spell_name.lower().replace(" ", "_")}',
                        old_value=None,
                        new_value={'name': spell_name, 'source': feat_name},
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.SPELLS,
                        description=f"Learned spell: {spell_name} (from {feat_name} feat)"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting spell changes for feat {feat_name}: {e}")
        
        return changes
    
    def _detect_feat_combat_changes(self, feat_name: str, combat_options: Dict,
                                  old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect combat option changes caused by feat."""
        changes = []
        
        try:
            # Check for new attack options
            if 'attack_options' in combat_options:
                for option_name in combat_options['attack_options']:
                    change = self._create_field_change(
                        field_path=f'character.combat.attack_options.{option_name.lower().replace(" ", "_")}',
                        old_value=None,
                        new_value={'name': option_name, 'source': feat_name},
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.COMBAT,
                        description=f"Gained attack option: {option_name} (from {feat_name} feat)"
                    )
                    changes.append(change)
            
            # Check for new bonus actions
            if 'bonus_actions' in combat_options:
                for action_name in combat_options['bonus_actions']:
                    change = self._create_field_change(
                        field_path=f'character.combat.bonus_actions.{action_name.lower().replace(" ", "_")}',
                        old_value=None,
                        new_value={'name': action_name, 'source': feat_name},
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.COMBAT,
                        description=f"Gained bonus action: {action_name} (from {feat_name} feat)"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting combat changes for feat {feat_name}: {e}")
        
        return changes
    
    def _create_feat_added_description(self, feat_name: str, feat_effects: Dict) -> str:
        """Create detailed description for feat addition."""
        description = f"Gained {feat_name} feat"
        
        if feat_effects:
            effects = []
            
            if 'ability_score_increase' in feat_effects:
                abilities = list(feat_effects['ability_score_increase'].keys())
                effects.append(f"increases {', '.join(abilities)}")
            
            if 'proficiencies' in feat_effects:
                prof_types = list(feat_effects['proficiencies'].keys())
                effects.append(f"grants {', '.join(prof_types)} proficiencies")
            
            if 'spells' in feat_effects:
                spell_count = len(feat_effects['spells'].get('known', []))
                if spell_count > 0:
                    effects.append(f"grants {spell_count} spell(s)")
            
            if 'combat_options' in feat_effects:
                combat_count = len(feat_effects['combat_options'].get('attack_options', [])) + \
                              len(feat_effects['combat_options'].get('bonus_actions', []))
                if combat_count > 0:
                    effects.append(f"adds {combat_count} combat option(s)")
            
            if effects:
                description += f". This feat {', '.join(effects)}."
        
        return description
    
    def _load_feat_effects_database(self) -> Dict[str, Dict]:
        """Load database of feat mechanical effects."""
        # This would ideally load from a configuration file or database
        # For now, we'll include some common feats as examples
        return {
            'great weapon master': {
                'ability_score_increase': {},
                'proficiencies': {},
                'spells': {},
                'combat_options': {
                    'attack_options': ['Power Attack (-5 attack, +10 damage)'],
                    'bonus_actions': ['Bonus Attack (on crit or kill)']
                },
                'affects': ['combat.attack_options', 'combat.bonus_actions']
            },
            'sharpshooter': {
                'ability_score_increase': {},
                'proficiencies': {},
                'spells': {},
                'combat_options': {
                    'attack_options': ['Precision Shot (-5 attack, +10 damage)', 'Long Range Shot', 'Cover Ignore']
                },
                'affects': ['combat.attack_options']
            },
            'fey touched': {
                'ability_score_increase': {'intelligence': 1, 'wisdom': 1, 'charisma': 1},  # Player choice
                'proficiencies': {},
                'spells': {
                    'known': ['Misty Step', 'Enchantment or Divination 1st level']
                },
                'combat_options': {},
                'affects': ['ability_scores', 'spells.known']
            },
            'magic initiate': {
                'ability_score_increase': {},
                'proficiencies': {},
                'spells': {
                    'known': ['2 cantrips', '1 1st-level spell']
                },
                'combat_options': {},
                'affects': ['spells.known']
            },
            'skilled': {
                'ability_score_increase': {},
                'proficiencies': {
                    'skills': ['Any 3 skills']
                },
                'spells': {},
                'combat_options': {},
                'affects': ['proficiencies.skills']
            },
            'resilient': {
                'ability_score_increase': {'any': 1},  # Player choice
                'proficiencies': {
                    'saving_throws': ['Chosen ability']
                },
                'spells': {},
                'combat_options': {},
                'affects': ['ability_scores', 'proficiencies.saving_throws']
            },
            'war caster': {
                'ability_score_increase': {},
                'proficiencies': {},
                'spells': {},
                'combat_options': {
                    'attack_options': ['Spell Opportunity Attack'],
                    'reactions': ['Concentration Save Advantage']
                },
                'affects': ['combat.reactions', 'spellcasting.concentration']
            }
        }
    
    
    
    
    def _extract_spells(self, character_data: Dict) -> Dict[str, List]:
        """Extract spells from character data."""
        try:
            spells_data = None
            
            # Try different possible paths for spell data
            if 'character' in character_data and 'spells' in character_data['character']:
                spells_data = character_data['character']['spells']
            elif 'spells' in character_data:
                spells_data = character_data['spells']
            
            if spells_data:
                # Handle D&D Beyond format with categories (Racial, Class, Feat, Wizard, etc.)
                if isinstance(spells_data, dict):
                    all_spells = []
                    for source, spell_list in spells_data.items():
                        if isinstance(spell_list, list):
                            for spell in spell_list:
                                if isinstance(spell, dict) and 'name' in spell:
                                    # Add source information to spell
                                    spell_with_source = spell.copy()
                                    spell_with_source['source'] = source
                                    all_spells.append(spell_with_source)
                    
                    # Group spells by level for easier comparison
                    spells_by_level = {}
                    for spell in all_spells:
                        level = spell.get('level', 0)
                        if level not in spells_by_level:
                            spells_by_level[level] = []
                        spells_by_level[level].append(spell)
                    
                    return spells_by_level
                
                # Handle legacy format
                elif isinstance(spells_data, list):
                    return {'known': spells_data, 'prepared': []}
            
            return {}
        except Exception as e:
            self.logger.warning(f"Error extracting spells: {e}")
            return {}
    
    def _detect_skill_proficiency_changes(self, feat_name: str, skills: List[str],
                                        old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect skill proficiency changes from feat."""
        changes = []
        try:
            old_skills = extract_skill_proficiencies_list(old_data)
            new_skills = extract_skill_proficiencies_list(new_data)
            
            for skill in skills:
                if skill not in old_skills and skill in new_skills:
                    change = self._create_field_change(
                        field_path=f'character.proficiencies.skills.{skill.lower().replace(" ", "_")}',
                        old_value=False,
                        new_value=True,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.SKILLS,
                        description=f"Gained {skill} proficiency (from {feat_name} feat)"
                    )
                    changes.append(change)
        except Exception as e:
            self.logger.error(f"Error detecting skill proficiency changes: {e}")
        return changes
    
    def _detect_tool_proficiency_changes(self, feat_name: str, tools: List[str],
                                       old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect tool proficiency changes from feat."""
        changes = []
        try:
            old_tools = extract_tool_proficiencies_data(old_data)
            new_tools = extract_tool_proficiencies_data(new_data)
            
            for tool in tools:
                if tool not in old_tools and tool in new_tools:
                    change = self._create_field_change(
                        field_path=f'character.proficiencies.tools.{tool.lower().replace(" ", "_")}',
                        old_value=False,
                        new_value=True,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.SKILLS,
                        description=f"Gained {tool} proficiency (from {feat_name} feat)"
                    )
                    changes.append(change)
        except Exception as e:
            self.logger.error(f"Error detecting tool proficiency changes: {e}")
        return changes
    
    def _detect_weapon_proficiency_changes(self, feat_name: str, weapons: List[str],
                                         old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect weapon proficiency changes from feat."""
        changes = []
        try:
            old_weapons = extract_weapon_proficiencies_data(old_data)
            new_weapons = extract_weapon_proficiencies_data(new_data)
            
            for weapon in weapons:
                if weapon not in old_weapons and weapon in new_weapons:
                    change = self._create_field_change(
                        field_path=f'character.proficiencies.weapons.{weapon.lower().replace(" ", "_")}',
                        old_value=False,
                        new_value=True,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.COMBAT,
                        description=f"Gained {weapon} proficiency (from {feat_name} feat)"
                    )
                    changes.append(change)
        except Exception as e:
            self.logger.error(f"Error detecting weapon proficiency changes: {e}")
        return changes
    
    def _detect_armor_proficiency_changes(self, feat_name: str, armor: List[str],
                                        old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect armor proficiency changes from feat."""
        changes = []
        try:
            old_armor = extract_armor_proficiencies_data(old_data)
            new_armor = extract_armor_proficiencies_data(new_data)
            
            for armor_type in armor:
                if armor_type not in old_armor and armor_type in new_armor:
                    change = self._create_field_change(
                        field_path=f'character.proficiencies.armor.{armor_type.lower().replace(" ", "_")}',
                        old_value=False,
                        new_value=True,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.COMBAT,
                        description=f"Gained {armor_type} proficiency (from {feat_name} feat)"
                    )
                    changes.append(change)
        except Exception as e:
            self.logger.error(f"Error detecting armor proficiency changes: {e}")
        return changes
    
    
    
    


class EnhancedAbilityScoreDetector(BaseEnhancedDetector):
    """Enhanced detector for ability score changes with comprehensive causation tracking."""
    
    def __init__(self):
        field_mappings = {
            'ability_scores': EnhancedFieldMapping(
                api_path='character.abilityScores.*',
                display_name='Ability Scores',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.ABILITIES
            )
        }
        priority_rules = {
            'character.abilityScores.*': ChangePriority.HIGH,
            'character.ability_scores.*': ChangePriority.HIGH
        }
        super().__init__(field_mappings, priority_rules)
        
        # Ability score names
        self.abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        
        # Load ability score causation database
        self.ability_effects = self._load_ability_effects_database()
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect ability score changes with detailed attribution and cascading effects."""
        changes = []
        
        try:
            old_abilities = extract_ability_scores_data(old_data)
            new_abilities = extract_ability_scores_data(new_data)
            
            for ability in self.abilities:
                old_score = old_abilities.get(ability, 10)
                new_score = new_abilities.get(ability, 10)
                
                if old_score != new_score:
                    # Create the primary ability score change
                    ability_change = self._create_enhanced_ability_change(
                        ability=ability,
                        old_score=old_score,
                        new_score=new_score,
                        old_data=old_data,
                        new_data=new_data,
                        context=context
                    )
                    changes.append(ability_change)
                    
                    # Detect cascading effects of this ability score change
                    cascading_changes = self._detect_ability_cascading_effects(
                        ability, old_score, new_score, old_data, new_data, context
                    )
                    changes.extend(cascading_changes)
            
            self.logger.debug(f"Detected {len(changes)} ability score changes (including cascading effects)")
            
        except Exception as e:
            self.logger.error(f"Error detecting ability score changes: {e}", exc_info=True)
        
        return changes
    
    def _create_enhanced_ability_change(self, ability: str, old_score: int, new_score: int,
                                      old_data: Dict, new_data: Dict, 
                                      context: DetectionContext) -> FieldChange:
        """Create an enhanced ability score change with detailed attribution."""
        # Determine change type and priority
        change_type = ChangeType.INCREMENTED if new_score > old_score else ChangeType.DECREMENTED
        score_diff = abs(new_score - old_score)
        priority = ChangePriority.HIGH if score_diff > 2 else ChangePriority.MEDIUM
        
        # Calculate modifier changes
        old_modifier = (old_score - 10) // 2
        new_modifier = (new_score - 10) // 2
        modifier_change = new_modifier - old_modifier
        
        # Determine the source of the ability score change
        attribution = self._determine_ability_score_source(
            ability, old_score, new_score, old_data, new_data
        )
        
        # Create detailed descriptions
        direction = "increased" if new_score > old_score else "decreased"
        description = f"{ability.title()} {direction} from {old_score} to {new_score}"
        
        if attribution:
            description += f" (from {attribution.source_name})"
        
        detailed_description = self._create_ability_detailed_description(
            ability, old_score, new_score, old_modifier, new_modifier, attribution
        )
        
        # Create the field change
        change = self._create_field_change(
            field_path=f'character.abilityScores.{ability}',
            old_value=old_score,
            new_value=new_score,
            change_type=change_type,
            category=ChangeCategory.ABILITIES,
            description=description
        )
        
        # Add enhanced metadata
        change.metadata.update({
            'ability_name': ability,
            'score_change': new_score - old_score,
            'old_modifier': old_modifier,
            'new_modifier': new_modifier,
            'modifier_change': modifier_change,
            'detailed_description': detailed_description,
            'attribution': attribution.__dict__ if attribution else None,
            'cascading_effects_expected': len(self.ability_effects.get(ability, {}).get('affects', [])) > 0
        })
        
        return change
    
    def _detect_ability_cascading_effects(self, ability: str, old_score: int, new_score: int,
                                        old_data: Dict, new_data: Dict, 
                                        context: DetectionContext) -> List[FieldChange]:
        """Detect cascading effects of ability score changes."""
        cascading_changes = []
        
        try:
            old_modifier = (old_score - 10) // 2
            new_modifier = (new_score - 10) // 2
            
            # Only detect cascading effects if the modifier actually changed
            if old_modifier != new_modifier:
                modifier_change = new_modifier - old_modifier
                
                # Detect skill changes
                skill_changes = self._detect_ability_skill_effects(
                    ability, modifier_change, old_data, new_data
                )
                cascading_changes.extend(skill_changes)
                
                # Detect saving throw changes
                save_changes = self._detect_ability_save_effects(
                    ability, modifier_change, old_data, new_data
                )
                cascading_changes.extend(save_changes)
                
                # Detect spellcasting stat changes
                spell_changes = self._detect_ability_spell_effects(
                    ability, modifier_change, old_data, new_data
                )
                cascading_changes.extend(spell_changes)
                
                # Detect initiative changes (for Dexterity)
                if ability == 'dexterity':
                    initiative_changes = self._detect_ability_initiative_effects(
                        modifier_change, old_data, new_data
                    )
                    cascading_changes.extend(initiative_changes)
                
                # Detect passive skill changes
                passive_changes = self._detect_ability_passive_effects(
                    ability, modifier_change, old_data, new_data
                )
                cascading_changes.extend(passive_changes)
                
                # Mark all cascading changes as caused by this ability score change
                for change in cascading_changes:
                    change.metadata.update({
                        'caused_by_ability': ability,
                        'ability_modifier_change': modifier_change,
                        'causation_trigger': 'ability_score_change',
                        'causation_source': f'character.abilityScores.{ability}'
                    })
            
        except Exception as e:
            self.logger.error(f"Error detecting cascading effects for {ability}: {e}", exc_info=True)
        
        return cascading_changes
    
    def _determine_ability_score_source(self, ability: str, old_score: int, new_score: int,
                                      old_data: Dict, new_data: Dict) -> Optional[ChangeAttribution]:
        """Determine what caused the ability score change."""
        try:
            # Check for feat-based increases
            feat_attribution = self._check_feat_ability_increase(ability, old_data, new_data)
            if feat_attribution:
                return feat_attribution
            
            # Check for ASI (Ability Score Improvement) at level 4, 8, 12, 16, 19
            asi_attribution = self._check_asi_increase(ability, old_data, new_data)
            if asi_attribution:
                return asi_attribution
            
            # Check for equipment-based changes
            equipment_attribution = self._check_equipment_ability_change(ability, old_data, new_data)
            if equipment_attribution:
                return equipment_attribution
            
            # Check for racial bonuses (usually at character creation or race change)
            racial_attribution = self._check_racial_ability_bonus(ability, old_data, new_data)
            if racial_attribution:
                return racial_attribution
            
            # Check for class feature bonuses
            class_attribution = self._check_class_ability_bonus(ability, old_data, new_data)
            if class_attribution:
                return class_attribution
            
            # Default attribution for unknown sources
            return ChangeAttribution(
                source="unknown",
                source_name="Unknown Source",
                source_type="unknown",
                impact_summary=f"Ability score change of {new_score - old_score}"
            )
            
        except Exception as e:
            self.logger.error(f"Error determining ability score source for {ability}: {e}")
            return None
    
    def _check_feat_ability_increase(self, ability: str, old_data: Dict, new_data: Dict) -> Optional[ChangeAttribution]:
        """Check if ability increase is from a feat."""
        try:
            old_feats = extract_feats_data(old_data)
            new_feats = extract_feats_data(new_data)
            
            # Look for newly added feats
            for feat_id, feat_data in new_feats.items():
                if feat_id not in old_feats:
                    feat_name = extract_feat_name_data(feat_data)
                    
                    # Check if this feat provides ability score increases
                    if self._feat_affects_ability(feat_name, ability):
                        return ChangeAttribution(
                            source="feat_selection",
                            source_name=feat_name,
                            source_type="feat",
                            impact_summary=f"Grants +1 {ability.title()}"
                        )
            
        except Exception as e:
            self.logger.error(f"Error checking feat ability increase: {e}")
        
        return None
    
    def _check_asi_increase(self, ability: str, old_data: Dict, new_data: Dict) -> Optional[ChangeAttribution]:
        """Check if ability increase is from Ability Score Improvement (ASI)."""
        try:
            old_level = extract_character_level_data(old_data)
            new_level = extract_character_level_data(new_data)
            
            # Check if character passed through any ASI levels during level progression
            asi_levels = [4, 8, 12, 16, 19]
            
            # Find the highest ASI level that was passed through
            for asi_level in reversed(asi_levels):  # Check from highest to lowest
                if old_level < asi_level <= new_level:
                    return ChangeAttribution(
                        source="ability_score_improvement",
                        source_name=f"Level {asi_level} ASI",
                        source_type="class_feature",
                        impact_summary=f"Ability Score Improvement gained at level {asi_level}"
                    )
            
        except Exception as e:
            self.logger.error(f"Error checking ASI increase: {e}")
        
        return None
    
    def _check_equipment_ability_change(self, ability: str, old_data: Dict, new_data: Dict) -> Optional[ChangeAttribution]:
        """Check if ability change is from equipment."""
        try:
            old_equipment = extract_equipment_data(old_data)
            new_equipment = extract_equipment_data(new_data)
            
            # Look for equipment changes that affect ability scores
            for item_id, item_data in new_equipment.items():
                if item_id not in old_equipment or old_equipment[item_id] != item_data:
                    item_name = extract_item_name_data(item_data)
                    
                    # Check if this item affects the ability score
                    if self._item_affects_ability(item_name, item_data, ability):
                        return ChangeAttribution(
                            source="equipment_change",
                            source_name=item_name,
                            source_type="magic_item",
                            impact_summary=f"Magic item affecting {ability.title()}"
                        )
            
        except Exception as e:
            self.logger.error(f"Error checking equipment ability change: {e}")
        
        return None
    
    def _check_racial_ability_bonus(self, ability: str, old_data: Dict, new_data: Dict) -> Optional[ChangeAttribution]:
        """Check if ability change is from racial bonuses."""
        try:
            old_race = extract_race_data(old_data)
            new_race = extract_race_data(new_data)
            
            # Check if race changed
            if old_race != new_race and new_race:
                race_name = extract_race_name_data(new_race)
                
                # Check if this race provides bonuses to this ability
                if self._race_affects_ability(race_name, ability):
                    return ChangeAttribution(
                        source="racial_bonus",
                        source_name=race_name,
                        source_type="race",
                        impact_summary=f"Racial bonus to {ability.title()}"
                    )
            
        except Exception as e:
            self.logger.error(f"Error checking racial ability bonus: {e}")
        
        return None
    
    def _check_class_ability_bonus(self, ability: str, old_data: Dict, new_data: Dict) -> Optional[ChangeAttribution]:
        """Check if ability change is from class features."""
        try:
            old_features = extract_class_features_data(old_data)
            new_features = extract_class_features_data(new_data)
            
            # Look for new class features that affect ability scores
            for feature_id, feature_data in new_features.items():
                if feature_id not in old_features:
                    feature_name = extract_feature_name_data(feature_data)
                    
                    # Check if this feature affects the ability score
                    if self._feature_affects_ability(feature_name, ability):
                        return ChangeAttribution(
                            source="class_feature",
                            source_name=feature_name,
                            source_type="class_feature",
                            impact_summary=f"Class feature affecting {ability.title()}"
                        )
            
        except Exception as e:
            self.logger.error(f"Error checking class ability bonus: {e}")
        
        return None
    
    def _detect_ability_skill_effects(self, ability: str, modifier_change: int,
                                    old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect skill changes caused by ability modifier changes."""
        changes = []
        
        try:
            # Get skills that use this ability
            affected_skills = self.ability_effects.get(ability, {}).get('skills', [])
            
            old_skills = extract_skill_bonuses_data(old_data)
            new_skills = extract_skill_bonuses_data(new_data)
            
            for skill in affected_skills:
                # Make skill lookup case-insensitive
                skill_key = skill.lower().replace(" ", "_")
                old_bonus = old_skills.get(skill_key, old_skills.get(skill, 0))
                new_bonus = new_skills.get(skill_key, new_skills.get(skill, 0))
                
                # Check if the skill bonus changed by the expected amount
                if new_bonus - old_bonus == modifier_change:
                    change = self._create_field_change(
                        field_path=f'character.skills.{skill.lower().replace(" ", "_")}',
                        old_value=old_bonus,
                        new_value=new_bonus,
                        change_type=ChangeType.INCREMENTED if modifier_change > 0 else ChangeType.DECREMENTED,
                        category=ChangeCategory.SKILLS,
                        description=f"{skill} bonus changed from +{old_bonus} to +{new_bonus} (due to {ability.title()} modifier change)"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting skill effects for {ability}: {e}")
        
        return changes
    
    def _detect_ability_save_effects(self, ability: str, modifier_change: int,
                                   old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect saving throw changes caused by ability modifier changes."""
        changes = []
        
        try:
            old_saves = extract_saving_throws_data(old_data)
            new_saves = extract_saving_throws_data(new_data)
            
            # Check the saving throw for this ability
            old_save = old_saves.get(ability, 0)
            new_save = new_saves.get(ability, 0)
            
            # Check if the save bonus changed by the expected amount
            if new_save - old_save == modifier_change:
                change = self._create_field_change(
                    field_path=f'character.saving_throws.{ability}',
                    old_value=old_save,
                    new_value=new_save,
                    change_type=ChangeType.INCREMENTED if modifier_change > 0 else ChangeType.DECREMENTED,
                    category=ChangeCategory.ABILITIES,
                    description=f"{ability.title()} save changed from +{old_save} to +{new_save} (due to ability modifier change)"
                )
                changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting save effects for {ability}: {e}")
        
        return changes
    
    def _detect_ability_spell_effects(self, ability: str, modifier_change: int,
                                    old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect spellcasting stat changes caused by ability modifier changes."""
        changes = []
        
        try:
            # Check if this ability is a spellcasting ability
            spellcasting_abilities = ['intelligence', 'wisdom', 'charisma']
            
            if ability in spellcasting_abilities:
                old_spell_stats = extract_spellcasting_stats_data(old_data)
                new_spell_stats = extract_spellcasting_stats_data(new_data)
                
                # Check spell attack bonus
                old_attack = old_spell_stats.get('spell_attack_bonus', 0)
                new_attack = new_spell_stats.get('spell_attack_bonus', 0)
                
                if new_attack - old_attack == modifier_change:
                    change = self._create_field_change(
                        field_path='character.spellcasting.spell_attack_bonus',
                        old_value=old_attack,
                        new_value=new_attack,
                        change_type=ChangeType.INCREMENTED if modifier_change > 0 else ChangeType.DECREMENTED,
                        category=ChangeCategory.SPELLS,
                        description=f"Spell attack bonus changed from +{old_attack} to +{new_attack} (due to {ability.title()} increase)"
                    )
                    changes.append(change)
                
                # Check spell save DC
                old_dc = old_spell_stats.get('spell_save_dc', 8)
                new_dc = new_spell_stats.get('spell_save_dc', 8)
                
                if new_dc - old_dc == modifier_change:
                    change = self._create_field_change(
                        field_path='character.spellcasting.spell_save_dc',
                        old_value=old_dc,
                        new_value=new_dc,
                        change_type=ChangeType.INCREMENTED if modifier_change > 0 else ChangeType.DECREMENTED,
                        category=ChangeCategory.SPELLS,
                        description=f"Spell save DC changed from {old_dc} to {new_dc} (due to {ability.title()} increase)"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting spell effects for {ability}: {e}")
        
        return changes
    
    def _detect_ability_initiative_effects(self, modifier_change: int,
                                         old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect initiative changes caused by Dexterity modifier changes."""
        changes = []
        
        try:
            old_initiative = extract_initiative_bonus_data(old_data)
            new_initiative = extract_initiative_bonus_data(new_data)
            
            # Check if initiative changed by the expected amount
            if new_initiative - old_initiative == modifier_change:
                change = self._create_field_change(
                    field_path='character.initiative.bonus',
                    old_value=old_initiative,
                    new_value=new_initiative,
                    change_type=ChangeType.INCREMENTED if modifier_change > 0 else ChangeType.DECREMENTED,
                    category=ChangeCategory.COMBAT,
                    description=f"Initiative bonus changed from +{old_initiative} to +{new_initiative} (due to Dexterity increase)"
                )
                changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting initiative effects: {e}")
        
        return changes
    
    def _detect_ability_passive_effects(self, ability: str, modifier_change: int,
                                      old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect passive skill changes caused by ability modifier changes."""
        changes = []
        
        try:
            # Get passive skills that use this ability
            passive_skills = self.ability_effects.get(ability, {}).get('passive_skills', [])
            
            old_passives = extract_passive_skills_data(old_data)
            new_passives = extract_passive_skills_data(new_data)
            
            for passive_skill in passive_skills:
                # Make passive skill lookup case-insensitive
                skill_key = passive_skill.lower().replace(" ", "_")
                old_passive = old_passives.get(skill_key, old_passives.get(passive_skill, 10))
                new_passive = new_passives.get(skill_key, new_passives.get(passive_skill, 10))
                
                # Check if the passive skill changed by the expected amount
                if new_passive - old_passive == modifier_change:
                    change = self._create_field_change(
                        field_path=f'character.passive_skills.{passive_skill.lower().replace(" ", "_")}',
                        old_value=old_passive,
                        new_value=new_passive,
                        change_type=ChangeType.INCREMENTED if modifier_change > 0 else ChangeType.DECREMENTED,
                        category=ChangeCategory.SKILLS,
                        description=f"Passive {passive_skill} changed from {old_passive} to {new_passive} (due to {ability.title()} increase)"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting passive effects for {ability}: {e}")
        
        return changes
    
    def _create_ability_detailed_description(self, ability: str, old_score: int, new_score: int,
                                           old_modifier: int, new_modifier: int,
                                           attribution: Optional[ChangeAttribution]) -> str:
        """Create detailed description for ability score change."""
        direction = "increased" if new_score > old_score else "decreased"
        score_change = abs(new_score - old_score)
        modifier_change = abs(new_modifier - old_modifier)
        
        description = f"{ability.title()} {direction} by {score_change} points (from {old_score} to {new_score})"
        
        if old_modifier != new_modifier:
            modifier_direction = "increased" if new_modifier > old_modifier else "decreased"
            description += f", {modifier_direction} modifier from {old_modifier:+d} to {new_modifier:+d}"
        
        if attribution:
            description += f". Source: {attribution.source_name}"
            if attribution.impact_summary:
                description += f" - {attribution.impact_summary}"
        
        # Add information about cascading effects
        affected_areas = []
        ability_effects = self.ability_effects.get(ability, {})
        
        if ability_effects.get('skills'):
            affected_areas.append(f"{len(ability_effects['skills'])} skills")
        if ability == 'dexterity':
            affected_areas.append("initiative")
        if ability in ['intelligence', 'wisdom', 'charisma']:
            affected_areas.append("spellcasting stats")
        if ability_effects.get('passive_skills'):
            affected_areas.append("passive skills")
        
        if affected_areas and old_modifier != new_modifier:
            description += f". This change affects: {', '.join(affected_areas)}."
        
        return description
    
    def _load_ability_effects_database(self) -> Dict[str, Dict]:
        """Load database of ability score effects on other stats."""
        return {
            'strength': {
                'skills': ['Athletics'],
                'passive_skills': [],
                'affects': ['skills.athletics', 'attack_bonus.melee', 'damage.melee']
            },
            'dexterity': {
                'skills': ['Acrobatics', 'Sleight of Hand', 'Stealth'],
                'passive_skills': [],
                'affects': ['skills.acrobatics', 'skills.sleight_of_hand', 'skills.stealth', 
                           'initiative', 'armor_class', 'attack_bonus.ranged', 'damage.finesse']
            },
            'constitution': {
                'skills': [],
                'passive_skills': [],
                'affects': ['hit_points', 'concentration_saves']
            },
            'intelligence': {
                'skills': ['Arcana', 'History', 'Investigation', 'Nature', 'Religion'],
                'passive_skills': ['Investigation'],
                'affects': ['skills.arcana', 'skills.history', 'skills.investigation', 
                           'skills.nature', 'skills.religion', 'passive_investigation',
                           'spell_attack_bonus', 'spell_save_dc']
            },
            'wisdom': {
                'skills': ['Animal Handling', 'Insight', 'Medicine', 'Perception', 'Survival'],
                'passive_skills': ['Perception', 'Insight'],
                'affects': ['skills.animal_handling', 'skills.insight', 'skills.medicine',
                           'skills.perception', 'skills.survival', 'passive_perception',
                           'passive_insight', 'spell_attack_bonus', 'spell_save_dc']
            },
            'charisma': {
                'skills': ['Deception', 'Intimidation', 'Performance', 'Persuasion'],
                'passive_skills': [],
                'affects': ['skills.deception', 'skills.intimidation', 'skills.performance',
                           'skills.persuasion', 'spell_attack_bonus', 'spell_save_dc']
            }
        }
    
    # Helper methods for data extraction
    
    
    
    def _extract_character_level(self, character_data: Dict) -> int:
        """Extract the overall character level from character data."""
        return extract_character_level_data(character_data)
    
    def _extract_equipment(self, character_data: Dict) -> Dict[str, Any]:
        """Extract equipment from character data."""
        return extract_equipment_data(character_data)
    
    
    def _extract_race(self, character_data: Dict) -> Any:
        """Extract race from character data."""
        try:
            if 'character' in character_data:
                if 'race' in character_data['character']:
                    return character_data['character']['race']
                elif 'species' in character_data['character']:
                    return character_data['character']['species']
            
            if 'race' in character_data:
                return character_data['race']
            elif 'species' in character_data:
                return character_data['species']
            
            return None
        except Exception:
            return None
    
    def _extract_race_name(self, race_data: Any) -> str:
        return extract_race_name_data(race_data)
    
    
    
    def _extract_skill_bonuses(self, character_data: Dict) -> Dict[str, int]:
        """Extract skill bonuses from character data."""
        try:
            if 'character' in character_data and 'skills' in character_data['character']:
                return character_data['character']['skills']
            elif 'skills' in character_data:
                return character_data['skills']
            else:
                return {}
        except Exception:
            return {}
    
    def _extract_saving_throws(self, character_data: Dict) -> Dict[str, int]:
        """Extract saving throws from character data."""
        try:
            if 'character' in character_data and 'saving_throws' in character_data['character']:
                return character_data['character']['saving_throws']
            elif 'saving_throws' in character_data:
                return character_data['saving_throws']
            else:
                return {}
        except Exception:
            return {}
    
    def _extract_spellcasting_stats(self, character_data: Dict) -> Dict[str, int]:
        """Extract spellcasting stats from character data."""
        try:
            if 'character' in character_data and 'spellcasting' in character_data['character']:
                return character_data['character']['spellcasting']
            elif 'spellcasting' in character_data:
                return character_data['spellcasting']
            else:
                return {}
        except Exception:
            return {}
    
    def _extract_initiative_bonus(self, character_data: Dict) -> int:
        """Extract initiative bonus from character data."""
        try:
            if 'character' in character_data and 'initiative' in character_data['character']:
                initiative = character_data['character']['initiative']
                if isinstance(initiative, dict):
                    return initiative.get('bonus', 0)
                else:
                    return initiative
            elif 'initiative' in character_data:
                initiative = character_data['initiative']
                if isinstance(initiative, dict):
                    return initiative.get('bonus', 0)
                else:
                    return initiative
            
            return 0
        except Exception:
            return 0
    
    
    # Helper methods for checking causation sources
    def _feat_affects_ability(self, feat_name: str, ability: str) -> bool:
        """Check if a feat affects a specific ability score."""
        # This would ideally check against a comprehensive feat database
        # For now, we'll check some common feats
        feat_ability_map = {
            'fey touched': ['intelligence', 'wisdom', 'charisma'],
            'telekinetic': ['intelligence', 'wisdom', 'charisma'],
            'telepathic': ['intelligence', 'wisdom', 'charisma'],
            'resilient': ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'],
            'observant': ['intelligence', 'wisdom'],
            'keen mind': ['intelligence'],
            'actor': ['charisma'],
            'athlete': ['strength', 'dexterity'],
            'durable': ['constitution'],
            'linguist': ['intelligence'],
            'skilled': [],  # No ability score increase
            'tavern brawler': ['strength', 'constitution']
        }
        
        feat_key = feat_name.lower()
        return ability in feat_ability_map.get(feat_key, [])
    
    def _item_affects_ability(self, item_name: str, item_data: Dict, ability: str) -> bool:
        """Check if an item affects a specific ability score."""
        # Check item description or properties for ability score bonuses
        try:
            item_lower = item_name.lower()
            
            # Common magic items that affect ability scores
            ability_items = {
                'strength': ['gauntlets of ogre power', 'belt of giant strength', 'hammer of thunderbolts'],
                'dexterity': ['gloves of dexterity', 'boots of speed'],
                'constitution': ['amulet of health', 'belt of dwarvenkind'],
                'intelligence': ['headband of intellect', 'tome of understanding'],
                'wisdom': ['periapt of wisdom', 'stone of good luck'],
                'charisma': ['cloak of charisma', 'instrument of the bards']
            }
            
            return any(item in item_lower for item in ability_items.get(ability, []))
        except Exception:
            return False
    
    def _race_affects_ability(self, race_name: str, ability: str) -> bool:
        """Check if a race affects a specific ability score."""
        # Common racial ability score bonuses
        race_bonuses = {
            'human': ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'],
            'variant human': ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'],
            'elf': ['dexterity'],
            'high elf': ['dexterity', 'intelligence'],
            'wood elf': ['dexterity', 'wisdom'],
            'dark elf': ['dexterity', 'charisma'],
            'dwarf': ['constitution'],
            'mountain dwarf': ['strength', 'constitution'],
            'hill dwarf': ['wisdom', 'constitution'],
            'halfling': ['dexterity'],
            'lightfoot halfling': ['dexterity', 'charisma'],
            'stout halfling': ['dexterity', 'constitution'],
            'dragonborn': ['strength', 'charisma'],
            'gnome': ['intelligence'],
            'forest gnome': ['intelligence', 'dexterity'],
            'rock gnome': ['intelligence', 'constitution'],
            'half-elf': ['charisma'],
            'half-orc': ['strength', 'constitution'],
            'tiefling': ['intelligence', 'charisma']
        }
        
        race_key = race_name.lower()
        return ability in race_bonuses.get(race_key, [])
    
    def _feature_affects_ability(self, feature_name: str, ability: str) -> bool:
        """Check if a class feature affects a specific ability score."""
        # Some class features that can affect ability scores
        feature_lower = feature_name.lower()
        
        # Barbarian features
        if 'primal champion' in feature_lower and ability in ['strength', 'constitution']:
            return True
        
        # Monk features
        if 'timeless body' in feature_lower and ability == 'constitution':
            return True
        
        # Paladin features
        if 'aura' in feature_lower and ability == 'charisma':
            return True
        
        return False
    
    
    
    def _extract_weapon_proficiencies(self, character_data: Dict) -> List[str]:
        """Extract weapon proficiencies from character data."""
        try:
            if 'character' in character_data and 'proficiencies' in character_data['character']:
                return character_data['character']['proficiencies'].get('weapons', [])
            elif 'proficiencies' in character_data:
                return character_data['proficiencies'].get('weapons', [])
            else:
                return []
        except Exception:
            return []
    
    def _extract_armor_proficiencies(self, character_data: Dict) -> List[str]:
        """Extract armor proficiencies from character data."""
        try:
            if 'character' in character_data and 'proficiencies' in character_data['character']:
                return character_data['character']['proficiencies'].get('armor', [])
            elif 'proficiencies' in character_data:
                return character_data['proficiencies'].get('armor', [])
            else:
                return []
        except Exception:
            return []


class SubclassChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for subclass selections and changes with multiclass support."""
    
    def __init__(self):
        field_mappings = {
            'subclass': EnhancedFieldMapping(
                api_path='character.classes.*.subclass',
                display_name='Subclass',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.PROGRESSION
            ),
            'subclass_selection': EnhancedFieldMapping(
                api_path='character.classes.*.subclass.name',
                display_name='Subclass Selection',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.PROGRESSION
            ),
            'subclass_features': EnhancedFieldMapping(
                api_path='character.classes.*.subclass.features',
                display_name='Subclass Features',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.FEATURES
            )
        }
        priority_rules = {
            'character.classes.*.subclass': ChangePriority.HIGH,
            'character.classes.*.subclass.name': ChangePriority.HIGH,
            'character.classes.*.subclass.features': ChangePriority.MEDIUM
        }
        super().__init__(field_mappings, priority_rules)
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect subclass changes with enhanced multiclass support."""
        changes = []

        try:
            old_classes = extract_character_classes_data(old_data)
            new_classes = extract_character_classes_data(new_data)
            
            # Also extract subclass information from features (D&D Beyond sometimes stores it there)
            old_subclasses_from_features = extract_subclasses_from_features_data(old_data)
            new_subclasses_from_features = extract_subclasses_from_features_data(new_data)
            
            # Compare subclasses for each class (including multiclass scenarios)
            all_class_names = set(old_classes.keys()) | set(new_classes.keys())
            
            for class_name in all_class_names:
                old_class_data = old_classes.get(class_name, {})
                new_class_data = new_classes.get(class_name, {})
                
                # Try direct subclass field first
                old_subclass = old_class_data.get('subclass')
                new_subclass = new_class_data.get('subclass')
                
                # If direct subclass is null, check features (case-insensitive)
                if not old_subclass:
                    old_subclass = old_subclasses_from_features.get(class_name.lower())
                if not new_subclass:
                    new_subclass = new_subclasses_from_features.get(class_name.lower())
                
                # Detect subclass changes
                if old_subclass != new_subclass:
                    change = self._create_subclass_change(
                        class_name, old_subclass, new_subclass, old_class_data, new_class_data
                    )
                    changes.append(change)
                    self.logger.info(f"Detected subclass change for {class_name}: {old_subclass} -> {new_subclass}")
                
                # Detect subclass feature changes (if subclass exists)
                if new_subclass and old_subclass:
                    feature_changes = self._detect_subclass_feature_changes(
                        class_name, old_subclass, new_subclass
                    )
                    changes.extend(feature_changes)
            
            self.logger.debug(f"Detected {len(changes)} subclass changes across {len(all_class_names)} classes")
            
        except Exception as e:
            self.logger.error(f"Error detecting subclass changes: {e}", exc_info=True)
        
        return changes
    
    
    def _extract_subclass_name(self, subclass_data: Any) -> str:
        """Extract subclass name from subclass data."""
        try:
            if isinstance(subclass_data, dict):
                return subclass_data.get('name', subclass_data.get('subclass_name', 'Unknown Subclass'))
            elif isinstance(subclass_data, str):
                return subclass_data
            else:
                return 'Unknown Subclass'
        except Exception:
            return 'Unknown Subclass'
    
    def _create_subclass_change(self, class_name: str, old_subclass: Any, new_subclass: Any,
                              old_class_data: Dict, new_class_data: Dict) -> FieldChange:
        """Create an enhanced subclass change with detailed metadata."""
        old_name = extract_subclass_name_data(old_subclass) if old_subclass else None
        new_name = extract_subclass_name_data(new_subclass) if new_subclass else None
        
        # Determine change type and description
        if old_name and new_name:
            description = f"{class_name} subclass changed from {old_name} to {new_name}"
            change_type = ChangeType.MODIFIED
        elif new_name:
            description = f"{class_name} subclass set to {new_name}"
            change_type = ChangeType.ADDED
        elif old_name:
            description = f"{class_name} subclass {old_name} removed"
            change_type = ChangeType.REMOVED
        else:
            description = f"{class_name} subclass changed"
            change_type = ChangeType.MODIFIED
        
        # Create the field change with enhanced metadata
        change = self._create_field_change(
            field_path=f'character.classes.{class_name}.subclass',
            old_value=old_subclass,
            new_value=new_subclass,
            change_type=change_type,
            category=ChangeCategory.PROGRESSION,
            description=description
        )
        
        # Add enhanced metadata
        change.metadata.update({
            'class_name': class_name,
            'old_subclass_name': old_name,
            'new_subclass_name': new_name,
            'class_level': new_class_data.get('level', old_class_data.get('level')),
            'multiclass_character': self._is_multiclass_character(old_class_data, new_class_data),
            'subclass_selection_level': self._get_subclass_selection_level(class_name),
            'causation_trigger': 'subclass_selection' if change_type == ChangeType.ADDED else 'subclass_change'
        })
        
        return change
    
    def _detect_subclass_feature_changes(self, class_name: str, old_subclass: Dict, 
                                       new_subclass: Dict) -> List[FieldChange]:
        """Detect changes in subclass features."""
        changes = []
        
        try:
            old_features = old_subclass.get('features', []) if isinstance(old_subclass, dict) else []
            new_features = new_subclass.get('features', []) if isinstance(new_subclass, dict) else []
            
            # Convert to sets for comparison (assuming features have unique identifiers)
            old_feature_ids = set(extract_feature_id_data(f) for f in old_features)
            new_feature_ids = set(extract_feature_id_data(f) for f in new_features)
            
            # Detect added features
            for feature_id in new_feature_ids - old_feature_ids:
                feature_data = next(f for f in new_features if extract_feature_id_data(f) == feature_id)
                feature_name = extract_feature_name_data(feature_data)
                
                change = self._create_field_change(
                    field_path=f'character.classes.{class_name}.subclass.features.{feature_id}',
                    old_value=None,
                    new_value=feature_data,
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.FEATURES,
                    description=f"{class_name} gained subclass feature: {feature_name}"
                )
                
                change.metadata.update({
                    'class_name': class_name,
                    'feature_name': feature_name,
                    'feature_source': 'subclass',
                    'causation_trigger': 'level_progression'
                })
                
                changes.append(change)
            
            # Detect removed features (rare but possible with subclass changes)
            for feature_id in old_feature_ids - new_feature_ids:
                feature_data = next(f for f in old_features if extract_feature_id_data(f) == feature_id)
                feature_name = extract_feature_name_data(feature_data)
                
                change = self._create_field_change(
                    field_path=f'character.classes.{class_name}.subclass.features.{feature_id}',
                    old_value=feature_data,
                    new_value=None,
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.FEATURES,
                    description=f"{class_name} lost subclass feature: {feature_name}"
                )
                
                change.metadata.update({
                    'class_name': class_name,
                    'feature_name': feature_name,
                    'feature_source': 'subclass',
                    'causation_trigger': 'subclass_change'
                })
                
                changes.append(change)
        
        except Exception as e:
            self.logger.warning(f"Error detecting subclass feature changes for {class_name}: {e}")
        
        return changes
    
    def _is_multiclass_character(self, old_class_data: Dict, new_class_data: Dict) -> bool:
        """Determine if this is a multiclass character based on available class data."""
        # This is a simplified check - in a real implementation, you'd check all classes
        # For now, we'll assume multiclass if we have class level data and it's not the only class
        class_level = new_class_data.get('level', old_class_data.get('level', 1))
        return class_level < 20  # Simplified heuristic
    
    def _get_subclass_selection_level(self, class_name: str) -> int:
        """Get the level at which a class typically selects their subclass."""
        # Standard D&D 5e subclass selection levels
        subclass_levels = {
            'Artificer': 1,
            'Barbarian': 3,
            'Bard': 3,
            'Cleric': 1,
            'Druid': 2,
            'Fighter': 3,
            'Monk': 3,
            'Paladin': 3,
            'Ranger': 3,
            'Rogue': 3,
            'Sorcerer': 1,
            'Warlock': 1,
            'Wizard': 2
        }
        return subclass_levels.get(class_name, 3)  # Default to level 3
    
    def _extract_feature_id(self, feature_data: Any) -> str:
        """Extract feature ID from feature data."""
        try:
            if isinstance(feature_data, dict):
                return feature_data.get('id', feature_data.get('name', str(hash(str(feature_data)))))
            elif isinstance(feature_data, str):
                return feature_data
            else:
                return str(hash(str(feature_data)))
        except Exception:
            return 'unknown_feature'
    
    
    def _extract_subclasses_from_features(self, character_data: Dict) -> Dict[str, Any]:
        """Extract subclass information from character features (fallback method)."""
        subclasses = {}
        
        try:
            # Look for subclass information in features
            features = character_data.get('features', {})
            if isinstance(features, dict):
                for feature_category, feature_list in features.items():
                    if isinstance(feature_list, list):
                        for feature in feature_list:
                            if isinstance(feature, dict):
                                # Look for subclass indicators in feature names or descriptions
                                feature_name = feature.get('name', '').lower()
                                feature_desc = feature.get('description', '').lower()
                                
                                # Look for subclass features by source_name
                                source_name = feature.get('source_name', '').lower()
                                is_subclass_feature = feature.get('is_subclass_feature', False)
                                
                                # If it's marked as a subclass feature, use the source_name as the subclass
                                if is_subclass_feature and source_name and source_name != 'unknown':
                                    # Map source_name to class name (source_name is often the subclass name)
                                    if source_name not in subclasses:
                                        subclasses[source_name] = {
                                            'name': source_name.title(),
                                            'id': feature.get('id'),
                                            'source': 'features'
                                        }
                                
                                # Also check for common subclass indicators in feature names
                                subclass_indicators = {
                                    'illusion savant': ('wizard', 'Illusionist'),
                                    'school of': ('wizard', None),
                                    'college of': ('bard', None), 
                                    'path of': ('barbarian', None),
                                    'circle of': ('druid', None),
                                    'domain': ('cleric', None),
                                    'oath of': ('paladin', None),
                                    'archetype': ('fighter', None),
                                    'way of': ('monk', None),
                                    'patron': ('warlock', None),
                                    'origin': ('sorcerer', None)
                                }
                                
                                for indicator, (class_name, subclass_name) in subclass_indicators.items():
                                    if indicator in feature_name or indicator in feature_desc:
                                        if subclass_name:
                                            subclasses[class_name] = {
                                                'name': subclass_name,
                                                'id': feature.get('id'),
                                                'source': 'features'
                                            }
                                        break
            
            # Also check class features directly
            classes = character_data.get('character_info', {}).get('classes', [])
            if isinstance(classes, list):
                for class_data in classes:
                    if isinstance(class_data, dict):
                        class_name = class_data.get('name', '').lower()
                        subclass_data = class_data.get('subclass')
                        if subclass_data and class_name not in subclasses:
                            subclasses[class_name] = subclass_data
            
        except Exception as e:
            self.logger.warning(f"Error extracting subclasses from features: {e}")
        
        return subclasses


class EnhancedSpellsChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for comprehensive spell tracking."""
    
    def __init__(self):
        field_mappings = {
            'spells_known': EnhancedFieldMapping(
                api_path='character.spells.known',
                display_name='Known Spells',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SPELLS
            ),
            'spells_prepared': EnhancedFieldMapping(
                api_path='character.spells.prepared',
                display_name='Prepared Spells',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SPELLS
            ),
            'spell_slots': EnhancedFieldMapping(
                api_path='character.spellcasting.spell_slots.*',
                display_name='Spell Slots',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SPELLS
            ),
            'spell_attack_bonus': EnhancedFieldMapping(
                api_path='character.spellcasting.spell_attack_bonus',
                display_name='Spell Attack Bonus',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SPELLS
            ),
            'spell_save_dc': EnhancedFieldMapping(
                api_path='character.spellcasting.spell_save_dc',
                display_name='Spell Save DC',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SPELLS
            ),
            'spellcasting_ability': EnhancedFieldMapping(
                api_path='character.spellcasting.spellcasting_ability',
                display_name='Spellcasting Ability',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.SPELLS
            )
        }
        priority_rules = {
            'character.spells.*': ChangePriority.MEDIUM,
            'character.spellcasting.spell_slots.*': ChangePriority.MEDIUM,
            'character.spellcasting.spell_attack_bonus': ChangePriority.MEDIUM,
            'character.spellcasting.spell_save_dc': ChangePriority.MEDIUM,
            'character.spellcasting.spellcasting_ability': ChangePriority.HIGH
        }
        super().__init__(field_mappings, priority_rules)
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect comprehensive spell changes."""
        changes = []
        
        try:
            # Detect spell changes (all spells from all sources)
            changes.extend(self._detect_spell_list_changes(
                old_data, new_data, 'all', 'All spells'
            ))
            
            # Detect spell modifications (changes to existing spells)
            changes.extend(self._detect_spell_modifications(old_data, new_data))
            
            # Detect spell slot changes (maximum slots)
            changes.extend(self._detect_spell_slot_changes(old_data, new_data))
            
            # Detect spell slot usage changes
            changes.extend(self._detect_spell_slot_usage_changes(old_data, new_data))
            
            # Detect spellcasting progression changes
            changes.extend(self._detect_spellcasting_progression_changes(old_data, new_data))
            
            self.logger.debug(f"Detected {len(changes)} spell changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting spell changes: {e}", exc_info=True)
        
        return changes
    
    def _extract_spells(self, character_data: Dict) -> Dict[str, List]:
        """Extract spells from character data."""
        try:
            spells_data = None
            
            # Try different possible paths for spell data
            if 'character' in character_data and 'spells' in character_data['character']:
                spells_data = character_data['character']['spells']
            elif 'spells' in character_data:
                spells_data = character_data['spells']
            
            if spells_data:
                # Handle D&D Beyond format with categories (Racial, Class, Feat, Wizard, etc.)
                if isinstance(spells_data, dict):
                    all_spells = []
                    for source, spell_list in spells_data.items():
                        if isinstance(spell_list, list):
                            for spell in spell_list:
                                if isinstance(spell, dict) and 'name' in spell:
                                    # Add source information to spell
                                    spell_with_source = spell.copy()
                                    spell_with_source['source'] = source
                                    all_spells.append(spell_with_source)
                    
                    # Group spells by level for easier comparison
                    spells_by_level = {}
                    for spell in all_spells:
                        level = spell.get('level', 0)
                        if level not in spells_by_level:
                            spells_by_level[level] = []
                        spells_by_level[level].append(spell)
                    
                    return spells_by_level
                
                # Handle legacy format
                elif isinstance(spells_data, list):
                    return {'known': spells_data, 'prepared': []}
            
            return {}
        except Exception as e:
            self.logger.warning(f"Error extracting spells: {e}")
            return {}
    
    def _detect_spell_list_changes(self, old_data: Dict, new_data: Dict, 
                                 spell_type: str, display_name: str) -> List[FieldChange]:
        """Detect changes in spell lists using D&D Beyond format."""
        changes = []
        
        try:
            # Use the updated _extract_spells method that handles D&D Beyond format
            old_spells_by_level = extract_spells_data(old_data)
            new_spells_by_level = extract_spells_data(new_data)
            
            # Compare spells by level
            all_levels = set(old_spells_by_level.keys()) | set(new_spells_by_level.keys())
            
            for level in all_levels:
                old_spells_at_level = old_spells_by_level.get(level, [])
                new_spells_at_level = new_spells_by_level.get(level, [])
                
                # Create sets of spell names for comparison
                old_spell_names = {spell.get('name', '') for spell in old_spells_at_level}
                new_spell_names = {spell.get('name', '') for spell in new_spells_at_level}
                
                # Detect added spells
                added_spells = new_spell_names - old_spell_names
                for spell_name in added_spells:
                    # Find the full spell data
                    spell_data = next((s for s in new_spells_at_level if s.get('name') == spell_name), {})
                    source = spell_data.get('source', 'Unknown')
                    
                    level_text = "cantrip" if level == 0 else f"level {level}"
                    changes.append(self._create_field_change(
                        field_path=f'spells.{source}.{spell_name.lower().replace(" ", "_")}',
                        old_value=None,
                        new_value=spell_data,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.SPELLS,
                        description=f"Learned {level_text} spell: {spell_name} (from {source})"
                    ))
                
                # Detect removed spells
                removed_spells = old_spell_names - new_spell_names
                for spell_name in removed_spells:
                    # Find the full spell data
                    spell_data = next((s for s in old_spells_at_level if s.get('name') == spell_name), {})
                    source = spell_data.get('source', 'Unknown')
                    
                    level_text = "cantrip" if level == 0 else f"level {level}"
                    changes.append(self._create_field_change(
                        field_path=f'spells.{source}.{spell_name.lower().replace(" ", "_")}',
                        old_value=spell_data,
                        new_value=None,
                        change_type=ChangeType.REMOVED,
                        category=ChangeCategory.SPELLS,
                        description=f"Forgot {level_text} spell: {spell_name} (from {source})"
                    ))
            
        except Exception as e:
            self.logger.warning(f"Error detecting spell changes: {e}")
        
        return changes
    
    def _detect_spell_slot_changes(self, old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect spell slot changes."""
        changes = []
        
        try:
            old_slots = extract_spell_slots_data(old_data)
            new_slots = extract_spell_slots_data(new_data)
            
            # Compare spell slots by level
            for level in set(old_slots.keys()) | set(new_slots.keys()):
                old_count = old_slots.get(level, 0)
                new_count = new_slots.get(level, 0)
                
                if old_count != new_count:
                    change_type = ChangeType.INCREMENTED if new_count > old_count else ChangeType.DECREMENTED
                    changes.append(self._create_field_change(
                        field_path=f'character.spellcasting.spell_slots.level_{level}',
                        old_value=old_count,
                        new_value=new_count,
                        change_type=change_type,
                        category=ChangeCategory.SPELLS,
                        description=f"Level {level} spell slots: {old_count} → {new_count}"
                    ))
            
        except Exception as e:
            self.logger.warning(f"Error detecting spell slot changes: {e}")
        
        return changes
    
    def _extract_spell_list(self, character_data: Dict, spell_type: str) -> Dict[str, Any]:
        """Extract a specific spell list from character data."""
        try:
            # Try different possible paths
            spells = None
            if 'character' in character_data and 'spells' in character_data['character']:
                spells = character_data['character']['spells'].get(spell_type, [])
            elif 'spells' in character_data:
                spells = character_data['spells'].get(spell_type, [])
            
            if not spells:
                return {}
            
            # Convert to dict format
            if isinstance(spells, list):
                spell_dict = {}
                for i, spell in enumerate(spells):
                    if isinstance(spell, dict):
                        spell_key = spell.get('id', spell.get('name', f'spell_{i}'))
                        spell_dict[str(spell_key)] = spell
                    else:
                        spell_dict[f'spell_{i}'] = spell
                return spell_dict
            elif isinstance(spells, dict):
                return spells
            else:
                return {}
                
        except Exception as e:
            self.logger.warning(f"Error extracting {spell_type} spells: {e}")
            return {}
    
    def _extract_spell_slots(self, character_data: Dict) -> Dict[int, int]:
        """Extract spell slot information from character data."""
        try:
            slots = {}
            
            # Try different possible paths
            spell_slots = None
            if 'character' in character_data and 'spellcasting' in character_data['character']:
                spell_slots = character_data['character']['spellcasting'].get('spell_slots')
            elif 'spellcasting' in character_data:
                spell_slots = character_data['spellcasting'].get('spell_slots')
            
            if not spell_slots:
                return slots
            
            # Handle array format: [4, 2, 0, 0, 0, ...] where index 0 = level 1 slots
            if isinstance(spell_slots, list):
                for i, slot_count in enumerate(spell_slots):
                    level = i + 1  # Array index 0 = spell level 1
                    if slot_count > 0:  # Only include levels with slots
                        slots[level] = slot_count
            
            # Handle dictionary format: {"level_1": 4, "level_2": 2, ...}
            elif isinstance(spell_slots, dict):
                for level_key, slot_data in spell_slots.items():
                    try:
                        level = int(level_key.replace('level_', '').replace('level', ''))
                        if isinstance(slot_data, dict):
                            count = slot_data.get('max', slot_data.get('total', 0))
                        else:
                            count = int(slot_data)
                        if count > 0:  # Only include levels with slots
                            slots[level] = count
                    except (ValueError, TypeError):
                        continue
            
            return slots
            
        except Exception as e:
            self.logger.warning(f"Error extracting spell slots: {e}")
            return {}
    
    def _extract_spell_name(self, spell_data: Any) -> str:
        """Extract spell name from spell data."""
        try:
            if isinstance(spell_data, dict):
                return spell_data.get('name', spell_data.get('spell_name', 'Unknown Spell'))
            elif isinstance(spell_data, str):
                return spell_data
            else:
                return 'Unknown Spell'
        except Exception:
            return 'Unknown Spell'
    
    def _detect_spell_modifications(self, old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect modifications to existing spells (changes in spell properties)."""
        changes = []

        try:
            old_spells = extract_spell_list_data(old_data)
            new_spells = extract_spell_list_data(new_data)

            # Find spells that exist in both old and new data
            common_spell_names = set(old_spells.keys()) & set(new_spells.keys())

            for spell_name in common_spell_names:
                old_spell = old_spells[spell_name]
                new_spell = new_spells[spell_name]

                spell_changes = self._compare_spell_properties(
                    old_spell, new_spell, spell_name, 'spell'
                )
                changes.extend(spell_changes)

        except Exception as e:
            self.logger.warning(f"Error detecting spell modifications: {e}")

        return changes
    
    def _compare_spell_properties(self, old_spell: Dict, new_spell: Dict,
                                spell_id: str, spell_type: str) -> List[FieldChange]:
        """Compare properties of a spell to detect modifications."""
        changes = []

        try:
            spell_name = self._extract_spell_name(new_spell)

            # Properties to check for changes
            properties_to_check = [
                ('level', 'spell level'),
                ('school', 'school of magic'),
                ('casting_time', 'casting time'),
                ('range', 'range'),
                ('duration', 'duration'),
                ('components', 'components'),
                ('ritual', 'ritual casting'),
                ('concentration', 'concentration requirement'),
                ('prepared', 'preparation status'),
                ('always_prepared', 'always prepared status')
            ]

            for prop_key, prop_display in properties_to_check:
                old_value = old_spell.get(prop_key) if isinstance(old_spell, dict) else None
                new_value = new_spell.get(prop_key) if isinstance(new_spell, dict) else None

                # Skip changes where a field was simply added by a scraper update
                # (None -> value transitions for complex data types)
                if old_value is None and new_value is not None and isinstance(new_value, (dict, list)):
                    continue

                if old_value != new_value and (old_value is not None or new_value is not None):
                    old_display = self._format_spell_property(prop_key, old_value)
                    new_display = self._format_spell_property(prop_key, new_value)
                    changes.append(self._create_field_change(
                        field_path=f'character.spells.{spell_type}.{spell_id}.{prop_key}',
                        old_value=old_value,
                        new_value=new_value,
                        change_type=ChangeType.MODIFIED,
                        category=ChangeCategory.SPELLS,
                        description=f"Modified {spell_name} {prop_display}: {old_display} → {new_display}"
                    ))

        except Exception as e:
            self.logger.warning(f"Error comparing spell properties for {spell_id}: {e}")

        return changes

    @staticmethod
    def _format_spell_property(prop_key: str, value: Any) -> str:
        """Format a spell property value for human-readable display."""
        if value is None:
            return 'None'

        # Component IDs to names
        if prop_key == 'components' and isinstance(value, list):
            component_map = {1: 'V', 2: 'S', 3: 'M'}
            parts = [component_map.get(c, str(c)) for c in value]
            return ', '.join(parts) if parts else 'None'

        # Range dict
        if prop_key == 'range' and isinstance(value, dict):
            origin = value.get('origin', '')
            range_val = value.get('rangeValue', 0)
            if range_val and range_val > 0:
                return f"{origin} ({range_val} ft)"
            return origin or 'None'

        # Duration dict
        if prop_key == 'duration' and isinstance(value, dict):
            interval = value.get('durationInterval', '')
            unit = value.get('durationUnit', '')
            dur_type = value.get('durationType', '')
            parts = []
            if interval and unit:
                parts.append(f"{interval} {unit}")
            if dur_type and dur_type != 'Time':
                parts.append(dur_type)
            return ', '.join(parts) if parts else 'None'

        # Casting time (action count)
        if prop_key == 'casting_time' and isinstance(value, (int, float)):
            if value == 1:
                return '1 Action'
            return f"{value} Actions"

        # Boolean properties
        if isinstance(value, bool):
            return 'Yes' if value else 'No'

        return str(value)
    
    def _detect_spell_slot_usage_changes(self, old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect changes in spell slot usage (used vs available)."""
        changes = []
        
        try:
            old_usage = extract_spell_slot_usage_data(old_data)
            new_usage = extract_spell_slot_usage_data(new_data)
            
            # Compare usage for each spell level
            for level in set(old_usage.keys()) | set(new_usage.keys()):
                old_used = old_usage.get(level, {}).get('used', 0)
                new_used = new_usage.get(level, {}).get('used', 0)
                old_max = old_usage.get(level, {}).get('max', 0)
                new_max = new_usage.get(level, {}).get('max', 0)
                
                # Only track usage changes if max slots exist
                if new_max > 0 and old_used != new_used:
                    change_type = ChangeType.INCREMENTED if new_used > old_used else ChangeType.DECREMENTED
                    remaining_old = old_max - old_used
                    remaining_new = new_max - new_used
                    
                    changes.append(self._create_field_change(
                        field_path=f'character.spellcasting.spell_slots.level_{level}.used',
                        old_value=old_used,
                        new_value=new_used,
                        change_type=change_type,
                        category=ChangeCategory.SPELLS,
                        description=f"Level {level} spell slots used: {old_used}/{old_max} → {new_used}/{new_max} ({remaining_new} remaining)"
                    ))
                    
        except Exception as e:
            self.logger.warning(f"Error detecting spell slot usage changes: {e}")
        
        return changes
    
    def _detect_spellcasting_progression_changes(self, old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect changes in spellcasting progression (attack bonus, save DC, ability)."""
        changes = []
        
        try:
            old_casting = extract_spellcasting_info_data(old_data)
            new_casting = extract_spellcasting_info_data(new_data)
            
            # Check spell attack bonus
            old_attack = old_casting.get('spell_attack_bonus')
            new_attack = new_casting.get('spell_attack_bonus')
            if old_attack != new_attack and (old_attack is not None or new_attack is not None):
                change_type = ChangeType.INCREMENTED if (new_attack or 0) > (old_attack or 0) else ChangeType.DECREMENTED
                changes.append(self._create_field_change(
                    field_path='character.spellcasting.spell_attack_bonus',
                    old_value=old_attack,
                    new_value=new_attack,
                    change_type=change_type,
                    category=ChangeCategory.SPELLS,
                    description=f"Spell attack bonus: {old_attack or 0:+d} → {new_attack or 0:+d}"
                ))
            
            # Check spell save DC
            old_dc = old_casting.get('spell_save_dc')
            new_dc = new_casting.get('spell_save_dc')
            if old_dc != new_dc and (old_dc is not None or new_dc is not None):
                change_type = ChangeType.INCREMENTED if (new_dc or 0) > (old_dc or 0) else ChangeType.DECREMENTED
                changes.append(self._create_field_change(
                    field_path='character.spellcasting.spell_save_dc',
                    old_value=old_dc,
                    new_value=new_dc,
                    change_type=change_type,
                    category=ChangeCategory.SPELLS,
                    description=f"Spell save DC: {old_dc or 0} → {new_dc or 0}"
                ))
            
            # Check spellcasting ability
            old_ability = old_casting.get('spellcasting_ability')
            new_ability = new_casting.get('spellcasting_ability')
            if old_ability != new_ability and (old_ability is not None or new_ability is not None):
                changes.append(self._create_field_change(
                    field_path='character.spellcasting.spellcasting_ability',
                    old_value=old_ability,
                    new_value=new_ability,
                    change_type=ChangeType.MODIFIED,
                    category=ChangeCategory.SPELLS,
                    description=f"Spellcasting ability: {old_ability or 'None'} → {new_ability or 'None'}"
                ))
                
        except Exception as e:
            self.logger.warning(f"Error detecting spellcasting progression changes: {e}")
        
        return changes
    
    def _extract_spell_slot_usage(self, character_data: Dict) -> Dict[int, Dict[str, int]]:
        """Extract spell slot usage information (used and max) from character data."""
        try:
            usage = {}
            
            # Try different possible paths
            spell_slots = None
            if 'character' in character_data and 'spellcasting' in character_data['character']:
                spell_slots = character_data['character']['spellcasting'].get('spell_slots')
            elif 'spellcasting' in character_data:
                spell_slots = character_data['spellcasting'].get('spell_slots')
            
            if not spell_slots:
                return usage
            
            # Handle array format: [4, 2, 0, 0, 0, ...] where index 0 = level 1 slots
            if isinstance(spell_slots, list):
                for i, slot_count in enumerate(spell_slots):
                    level = i + 1  # Array index 0 = spell level 1
                    if slot_count > 0:  # Only include levels with slots
                        # For array format, assume max slots with 0 used (no usage tracking in array format)
                        usage[level] = {'max': slot_count, 'used': 0}
            
            # Handle dictionary format: {"level_1": {...}, "level_2": {...}, ...}
            elif isinstance(spell_slots, dict):
                for level_key, slot_data in spell_slots.items():
                    try:
                        level = int(level_key.replace('level_', '').replace('level', ''))
                        if isinstance(slot_data, dict):
                            max_slots = slot_data.get('max', slot_data.get('total', 0))
                            used_slots = slot_data.get('used', slot_data.get('expended', 0))
                            usage[level] = {'max': max_slots, 'used': used_slots}
                        else:
                            # If it's just a number, assume it's max slots with 0 used
                            usage[level] = {'max': int(slot_data), 'used': 0}
                    except (ValueError, TypeError):
                        continue
            
            return usage
            
        except Exception as e:
            self.logger.warning(f"Error extracting spell slot usage: {e}")
            return {}
    
    def _extract_spellcasting_info(self, character_data: Dict) -> Dict[str, Any]:
        """Extract spellcasting information from character data."""
        try:
            casting_info = {}
            
            # Try different possible paths
            if 'character' in character_data and 'spellcasting' in character_data['character']:
                spellcasting = character_data['character']['spellcasting']
            elif 'spellcasting' in character_data:
                spellcasting = character_data['spellcasting']
            else:
                # Try alternative paths
                spellcasting = {}
                if 'character' in character_data:
                    char_data = character_data['character']
                    casting_info['spell_attack_bonus'] = char_data.get('spell_attack_bonus')
                    casting_info['spell_save_dc'] = char_data.get('spell_save_dc')
                    casting_info['spellcasting_ability'] = char_data.get('spellcasting_ability')
                return casting_info
            
            # Extract spellcasting information
            casting_info['spell_attack_bonus'] = spellcasting.get('spell_attack_bonus')
            casting_info['spell_save_dc'] = spellcasting.get('spell_save_dc')
            casting_info['spellcasting_ability'] = spellcasting.get('spellcasting_ability')
            
            return casting_info
            
        except Exception as e:
            self.logger.warning(f"Error extracting spellcasting info: {e}")
            return {}


class EnhancedInventoryChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for inventory and equipment changes with proper item name extraction."""
    
    def __init__(self):
        field_mappings = {
            'inventory': EnhancedFieldMapping(
                api_path='character.inventory.*',
                display_name='Inventory',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.INVENTORY
            ),
            'equipment': EnhancedFieldMapping(
                api_path='character.equipment.*',
                display_name='Equipment',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.EQUIPMENT
            )
        }
        priority_rules = {
            'character.inventory.*': ChangePriority.MEDIUM,
            'character.equipment.*': ChangePriority.MEDIUM
        }
        super().__init__(field_mappings, priority_rules)
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect inventory and equipment changes with proper item name extraction."""
        changes = []
        
        try:
            # Detect changes in equipment sections (basic_equipment, enhanced_equipment, container_inventory)
            changes.extend(self._detect_equipment_section_changes(old_data, new_data, context))
            
            # Detect equipment slot changes
            changes.extend(self._detect_equipment_slot_changes(old_data, new_data, context))
            
            # Detect currency changes
            changes.extend(self._detect_currency_changes(old_data, new_data, context))
            
            self.logger.debug(f"Detected {len(changes)} inventory/equipment changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting inventory changes: {e}", exc_info=True)
        
        return changes
    
    def _detect_equipment_section_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect changes in equipment sections with improved item tracking to avoid false positives."""
        changes = []
        
        try:
            old_equipment = old_data.get('equipment', {})
            new_equipment = new_data.get('equipment', {})
            
            # First, get all items from all sections to track global item presence
            old_all_items = self._get_all_items_from_equipment(old_equipment)
            new_all_items = self._get_all_items_from_equipment(new_equipment)
            
            # Detect truly new items (not just moved between sections)
            changes.extend(self._detect_true_item_additions_removals(old_all_items, new_all_items, old_data, new_data, context))
            
            # Detect item moves between sections/containers
            changes.extend(self._detect_item_moves_and_reorganization(old_equipment, new_equipment, old_data, new_data, context))
            
            # Detect quantity and equipped status changes
            changes.extend(self._detect_item_property_changes(old_all_items, new_all_items, context))
            
        except Exception as e:
            self.logger.error(f"Error detecting equipment section changes: {e}", exc_info=True)
        
        return changes
    
    def _get_all_items_from_equipment(self, equipment: Dict) -> Dict[str, Dict]:
        """Get all items from all equipment sections, indexed by item ID."""
        all_items = {}
        
        try:
            # Handle basic_equipment and enhanced_equipment (lists)
            for section in ['basic_equipment', 'enhanced_equipment']:
                items = equipment.get(section, [])
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and 'id' in item:
                            item_id = str(item['id'])
                            # Use the actual container_entity_id from the item data
                            container_id = item.get('container_entity_id', 'character')
                            all_items[item_id] = {
                                **item,
                                '_section': section,
                                '_container': str(container_id)
                            }
            
            # Handle container_inventory (dict structure) - the actual structure has containers with item ID lists
            # The item data is in basic_equipment, but we need to map container relationships
            container_inventory = equipment.get('container_inventory', {})
            if isinstance(container_inventory, dict):
                containers = container_inventory.get('containers', {})
                if isinstance(containers, dict):
                    # Create a mapping of item ID to container for items already processed from basic_equipment
                    for container_id, container_data in containers.items():
                        if isinstance(container_data, dict) and 'items' in container_data:
                            item_ids = container_data['items']
                            if isinstance(item_ids, list):
                                for item_id in item_ids:
                                    item_id_str = str(item_id)
                                    # Update container info for items already in all_items from basic_equipment
                                    if item_id_str in all_items:
                                        all_items[item_id_str]['_container'] = str(container_id)
        
        except Exception as e:
            self.logger.error(f"Error getting all items from equipment: {e}")
        
        return all_items
    
    def _detect_true_item_additions_removals(self, old_all_items: Dict, new_all_items: Dict, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect items that are truly added or removed (not just moved).

        Uses name+quantity reconciliation to handle D&D Beyond item ID
        reassignment (observed during backend migrations where all item IDs
        change). Only reports the net difference after cancelling out items
        that appear in both old and new data with the same name and quantity.
        """
        changes = []

        try:
            from collections import Counter

            # Collect candidate additions (new IDs not in old)
            candidate_additions = []
            for item_id, item_data in new_all_items.items():
                if item_id not in old_all_items:
                    candidate_additions.append((item_id, item_data))

            # Collect candidate removals (old IDs not in new)
            candidate_removals = []
            for item_id, item_data in old_all_items.items():
                if item_id not in new_all_items:
                    candidate_removals.append((item_id, item_data))

            # Reconcile by name+quantity to filter out ID reassignments
            added_names = Counter()
            removed_names = Counter()
            added_by_name = {}
            removed_by_name = {}

            for item_id, item_data in candidate_additions:
                name = extract_item_name_data(item_data)
                qty = item_data.get('quantity', 1)
                key = (name, qty)
                added_names[key] += 1
                added_by_name.setdefault(key, []).append((item_id, item_data))

            for item_id, item_data in candidate_removals:
                name = extract_item_name_data(item_data)
                qty = item_data.get('quantity', 1)
                key = (name, qty)
                removed_names[key] += 1
                removed_by_name.setdefault(key, []).append((item_id, item_data))

            # Cancel out matching name+quantity pairs (same item, different ID)
            all_keys = set(added_names.keys()) | set(removed_names.keys())
            net_additions = []
            net_removals = []

            for key in all_keys:
                add_count = added_names.get(key, 0)
                remove_count = removed_names.get(key, 0)
                net = add_count - remove_count

                if net > 0:
                    items = added_by_name.get(key, [])
                    net_additions.extend(items[:net])
                elif net < 0:
                    items = removed_by_name.get(key, [])
                    net_removals.extend(items[:abs(net)])

            # Create change entries for net additions
            for item_id, item_data in net_additions:
                item_name = extract_item_name_data(item_data)
                section = item_data.get('_section', 'unknown')
                container = item_data.get('_container', 'character')
                quantity = item_data.get('quantity', 1)
                container_name = self._get_container_name(container, new_data)

                description = self._create_inventory_change_description(
                    ChangeType.ADDED, item_name, container_name, quantity
                )

                change = self._create_field_change(
                    field_path=f'equipment.{section}.{item_id}',
                    old_value=None,
                    new_value={k: v for k, v in item_data.items() if not k.startswith('_')},
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.INVENTORY,
                    description=description
                )
                change.metadata.update({
                    'item_name': item_name,
                    'equipment_section': section,
                    'container': container,
                    'causation_trigger': 'new_item_acquisition'
                })
                changes.append(change)

            # Create change entries for net removals
            for item_id, item_data in net_removals:
                item_name = extract_item_name_data(item_data)
                section = item_data.get('_section', 'unknown')
                container = item_data.get('_container', 'character')
                quantity = item_data.get('quantity', 1)
                container_name = self._get_container_name(container, old_data)

                description = self._create_inventory_change_description(
                    ChangeType.REMOVED, item_name, container_name, quantity
                )

                change = self._create_field_change(
                    field_path=f'equipment.{section}.{item_id}',
                    old_value={k: v for k, v in item_data.items() if not k.startswith('_')},
                    new_value=None,
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.INVENTORY,
                    description=description
                )
                change.metadata.update({
                    'item_name': item_name,
                    'equipment_section': section,
                    'container': container,
                    'causation_trigger': 'item_removal'
                })
                changes.append(change)

        except Exception as e:
            self.logger.error(f"Error detecting true item additions/removals: {e}")

        return changes
    
    def _detect_item_moves_and_reorganization(self, old_equipment: Dict, new_equipment: Dict, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect items moved between containers or sections."""
        changes = []
        
        try:
            old_all_items = self._get_all_items_from_equipment(old_equipment)
            new_all_items = self._get_all_items_from_equipment(new_equipment)
            
            # Find items that moved between containers/sections
            for item_id in old_all_items.keys() & new_all_items.keys():
                old_item = old_all_items[item_id]
                new_item = new_all_items[item_id]
                
                old_container = old_item.get('_container', 'character')
                new_container = new_item.get('_container', 'character')
                old_section = old_item.get('_section', 'unknown')
                new_section = new_item.get('_section', 'unknown')
                
                # Check if item moved between containers or sections
                if old_container != new_container or old_section != new_section:
                    item_name = extract_item_name_data(new_item)
                    
                    if old_container != new_container:
                        # Get human-readable container names
                        old_container_name = self._get_container_name(old_container, old_data)
                        new_container_name = self._get_container_name(new_container, new_data)
                        description = f"Moved {item_name} from {old_container_name} to {new_container_name}"
                        change_type = ChangeType.MOVED
                    elif old_section != new_section:
                        # More specific description when moving between sections within same container
                        section_names = {
                            'basic_equipment': 'basic equipment',
                            'enhanced_equipment': 'enhanced equipment', 
                            'container_inventory': 'container storage'
                        }
                        old_section_name = section_names.get(old_section, old_section)
                        new_section_name = section_names.get(new_section, new_section)
                        description = f"Moved {item_name} from {old_section_name} to {new_section_name}"
                        change_type = ChangeType.MOVED
                    else:
                        # Item position changed within same section/container
                        description = f"Reordered {item_name} within {old_section.replace('_', ' ')}"
                        change_type = ChangeType.REORDERED
                    
                    change = self._create_field_change(
                        field_path=f'equipment.{item_id}.location',
                        old_value={'section': old_section, 'container': old_container},
                        new_value={'section': new_section, 'container': new_container},
                        change_type=change_type,
                        category=ChangeCategory.INVENTORY,
                        description=description
                    )
                    change.metadata.update({
                        'item_name': item_name,
                        'old_container': old_container,
                        'new_container': new_container,
                        'old_section': old_section,
                        'new_section': new_section,
                        'causation_trigger': 'inventory_reorganization'
                    })
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting item moves: {e}")
        
        return changes
    
    def _detect_item_property_changes(self, old_all_items: Dict, new_all_items: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect changes in item properties like quantity, equipped status, etc."""
        changes = []
        
        try:
            # Find items with property changes
            for item_id in old_all_items.keys() & new_all_items.keys():
                old_item = old_all_items[item_id]
                new_item = new_all_items[item_id]
                
                item_name = extract_item_name_data(new_item)
                
                # Check equipped status change
                old_equipped = old_item.get('equipped', False)
                new_equipped = new_item.get('equipped', False)
                if old_equipped != new_equipped:
                    status = "Equipped" if new_equipped else "Unequipped"
                    change = self._create_field_change(
                        field_path=f'equipment.{item_id}.equipped',
                        old_value=old_equipped,
                        new_value=new_equipped,
                        change_type=ChangeType.ADDED if new_equipped else ChangeType.REMOVED,
                        category=ChangeCategory.EQUIPMENT,
                        description=f"{status} {item_name}"
                    )
                    change.metadata.update({
                        'item_name': item_name,
                        'causation_trigger': 'equipment_change'
                    })
                    changes.append(change)
                
                # Check quantity change
                old_quantity = old_item.get('quantity', 1)
                new_quantity = new_item.get('quantity', 1)
                if old_quantity != new_quantity:
                    change_type = ChangeType.INCREMENTED if new_quantity > old_quantity else ChangeType.DECREMENTED
                    change = self._create_field_change(
                        field_path=f'equipment.{item_id}.quantity',
                        old_value=old_quantity,
                        new_value=new_quantity,
                        change_type=change_type,
                        category=ChangeCategory.INVENTORY,
                        description=f"{item_name} quantity: {old_quantity} → {new_quantity}"
                    )
                    change.metadata.update({
                        'item_name': item_name,
                        'quantity_change': new_quantity - old_quantity,
                        'causation_trigger': 'inventory_management'
                    })
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting item property changes: {e}")
        
        return changes
    

    

    
    def _detect_equipment_slot_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect equipment slot changes (equipped items) - excluding summary fields."""
        changes = []
        
        try:
            old_equipment = extract_equipment_slots_data(old_data)
            new_equipment = extract_equipment_slots_data(new_data)
            
            # Define summary fields that should be excluded from item change detection
            summary_fields = {
                'item_counts', 'weight_distribution', 'container_summary', 
                'notable_items', 'wealth_summary', 'total_weight', 'equipped_weight',
                'unequipped_weight', 'encumbrance_level', 'total_items', 'weapons',
                'armor', 'magic_items', 'equipped_items', 'attuned_items'
            }
            
            # Compare equipment slots, excluding summary fields
            for slot in set(old_equipment.keys()) | set(new_equipment.keys()):
                # Skip summary fields - these aren't actual equipment items
                if slot in summary_fields:
                    continue
                    
                old_item = old_equipment.get(slot)
                new_item = new_equipment.get(slot)
                
                if old_item != new_item:
                    old_name = extract_item_name_data(old_item) if old_item else None
                    new_name = extract_item_name_data(new_item) if new_item else None
                    
                    # Determine change type and description
                    if not old_item and new_item:
                        change_type = ChangeType.ADDED
                        if slot == 'armor':
                            description = f"Equipped armor: {new_name}"
                        elif slot in ['mainHand', 'offHand']:
                            description = f"Equipped weapon: {new_name}"
                        else:
                            description = f"Equipped {new_name} in {slot} slot"
                    elif old_item and not new_item:
                        change_type = ChangeType.REMOVED
                        if slot == 'armor':
                            description = f"Unequipped armor: {old_name}"
                        elif slot in ['mainHand', 'offHand']:
                            description = f"Unequipped weapon: {old_name}"
                        else:
                            description = f"Unequipped {old_name} from {slot} slot"
                    else:
                        change_type = ChangeType.MODIFIED
                        if slot == 'armor':
                            description = f"Changed armor: {old_name} → {new_name}"
                        elif slot in ['mainHand', 'offHand']:
                            description = f"Changed weapon: {old_name} → {new_name}"
                        else:
                            description = f"Changed equipment in {slot}: {old_name} → {new_name}"
                    
                    change = self._create_field_change(
                        field_path=f'character.equipment.{slot}',
                        old_value=old_item,
                        new_value=new_item,
                        change_type=change_type,
                        category=ChangeCategory.EQUIPMENT,
                        description=description
                    )
                    
                    # Add enhanced metadata
                    change.metadata.update({
                        'equipment_slot': slot,
                        'old_item_name': old_name,
                        'new_item_name': new_name,
                        'causation_trigger': 'equipment_change'
                    })
                    
                    changes.append(change)
            
        except Exception as e:
            self.logger.warning(f"Error detecting equipment slot changes: {e}")
        
        return changes
    
    def _extract_inventory(self, character_data: Dict) -> Dict[str, Any]:
        """Extract inventory from character data, supporting v6.0.0 format."""
        try:
            # Try v6.0.0 format first (equipment.basic_equipment)
            equipment = character_data.get('equipment', {})
            if equipment and 'basic_equipment' in equipment:
                basic_equipment = equipment['basic_equipment']
                if isinstance(basic_equipment, list):
                    inventory_dict = {}
                    for item in basic_equipment:
                        if isinstance(item, dict) and 'id' in item:
                            item_id = str(item['id'])
                            inventory_dict[item_id] = item
                    return inventory_dict
            
            # Try legacy character.inventory format
            if 'character' in character_data and 'inventory' in character_data['character']:
                inventory = character_data['character']['inventory']
            elif 'inventory' in character_data:
                inventory = character_data['inventory']
            else:
                return {}
            
            # Handle different inventory structures
            if isinstance(inventory, list):
                inventory_dict = {}
                for i, item in enumerate(inventory):
                    if isinstance(item, dict):
                        item_key = item.get('id', item.get('name', f'item_{i}'))
                        inventory_dict[str(item_key)] = item
                    else:
                        inventory_dict[f'item_{i}'] = item
                return inventory_dict
            elif isinstance(inventory, dict):
                return inventory
            else:
                return {}
                
        except Exception as e:
            self.logger.warning(f"Error extracting inventory: {e}")
            return {}
    
    def _extract_equipment_slots(self, character_data: Dict) -> Dict[str, Any]:
        """Extract equipment slots from character data."""
        try:
            if 'character' in character_data and 'equipment' in character_data['character']:
                equipment = character_data['character']['equipment']
            elif 'equipment' in character_data:
                equipment = character_data['equipment']
            else:
                return {}
            
            # Look for equipment_summary which contains equipped items
            if isinstance(equipment, dict) and 'equipment_summary' in equipment:
                return equipment['equipment_summary']
            
            return equipment if isinstance(equipment, dict) else {}
            
        except Exception as e:
            self.logger.warning(f"Error extracting equipment slots: {e}")
            return {}
    
    def _extract_item_name(self, item_data: Any) -> str:
        """Extract item name from item data with improved fallbacks."""
        try:
            if not item_data:
                return 'Unknown Item'
            
            if isinstance(item_data, dict):
                # Try different name fields
                name = (item_data.get('name') or 
                        item_data.get('item_name') or 
                        item_data.get('display_name') or
                        item_data.get('title'))
                
                if name and isinstance(name, str) and name.strip():
                    return name.strip()
                
                # Try to construct name from other fields
                item_type = item_data.get('item_type', '')
                if item_type:
                    return f"Unknown {item_type}"
                
                return 'Unknown Item'
            elif isinstance(item_data, str):
                return item_data.strip() if item_data.strip() else 'Unknown Item'
            else:
                return 'Unknown Item'
        except Exception:
            return 'Unknown Item'
    
    def _extract_item_quantity(self, item_data: Any) -> int:
        """Extract item quantity from item data."""
        try:
            if isinstance(item_data, dict):
                return item_data.get('quantity', item_data.get('count', 1))
            else:
                return 1
        except Exception:
            return 1
    
    def _get_item_quantity(self, item_data: Any) -> int:
        """Get item quantity from item data (alias for consistency with tests)."""
        return self._extract_item_quantity(item_data)
    
    def _get_container_name(self, container_id: Any, character_data: Dict) -> str:
        """Get the name of a container by its ID using the container_inventory structure."""
        try:
            if not container_id:
                return "Unknown Container"
            
            # First, try to get container name from the container_inventory structure
            equipment = character_data.get('equipment', {})
            container_inventory = equipment.get('container_inventory', {})
            containers = container_inventory.get('containers', {})
            
            # Check if we have the container in the containers mapping
            container_id_str = str(container_id)
            if container_id_str in containers:
                container_info = containers[container_id_str]
                container_name = container_info.get('name', 'Unknown Container')
                
                # If it's the character container, make it more descriptive
                if container_info.get('is_character', False):
                    character_name = character_data.get('character_info', {}).get('name') or character_data.get('name', 'Character')
                    return f"{character_name}'s inventory"
                else:
                    return container_name
            
            # Fallback: If container_id matches character ID, it's the character's main inventory
            character_id = character_data.get('id') or character_data.get('character_info', {}).get('id')
            if str(container_id) == str(character_id):
                character_name = character_data.get('character_info', {}).get('name') or character_data.get('name', 'Character')
                return f"{character_name}'s inventory"
            
            # Fallback: Look for the container in the inventory items
            inventory = self._extract_inventory(character_data)
            for item_id, item_data in inventory.items():
                if str(item_id) == str(container_id):
                    container_name = extract_item_name_data(item_data)
                    return container_name
            
            # Fallback: Also look for the container in equipment data
            all_items = self._get_all_items_from_equipment(equipment)
            for item_id, item_data in all_items.items():
                if str(item_id) == str(container_id):
                    container_name = extract_item_name_data(item_data)
                    return container_name
            
            # Special case for 'character' container ID
            if str(container_id).lower() == 'character':
                return "Character"
            
            # Final fallback: Use generic container name
            return f"Container ({container_id})"
                
        except Exception as e:
            self.logger.warning(f"Error getting container name for ID {container_id}: {e}")
            return f"Container ({container_id})"
    
    def _create_inventory_change_description(self, change_type: ChangeType, item_name: str, 
                                           container_name: str, quantity: int = 1) -> str:
        """Create a descriptive message for inventory changes with smart quantity handling."""
        try:
            # For quantities > 1, show the quantity but don't attempt pluralization
            # Complex item names like "Map - nautical, found on Sea Ghosts" don't pluralize well
            if quantity > 1:
                item_display = f"{quantity} {item_name}"
            else:
                item_display = item_name
            
            # Create description based on change type
            if change_type == ChangeType.ADDED:
                return f"Added {item_display} to {container_name}"
            elif change_type == ChangeType.REMOVED:
                return f"Removed {item_display} from {container_name}"
            else:
                return f"Modified {item_display} in {container_name}"
                
        except Exception as e:
            self.logger.warning(f"Error creating inventory change description: {e}")
            # Fallback to simple description
            if change_type == ChangeType.ADDED:
                return f"Added {item_name} to {container_name}"
            elif change_type == ChangeType.REMOVED:
                return f"Removed {item_name} from {container_name}"
            else:
                return f"Modified {item_name} in {container_name}"
    
    def _detect_currency_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect currency changes."""
        changes = []
        
        try:
            old_currencies = extract_currencies_data(old_data)
            new_currencies = extract_currencies_data(new_data)
            
            # Compare each currency type
            all_currency_types = set(old_currencies.keys()) | set(new_currencies.keys())
            
            for currency_type in all_currency_types:
                old_amount = old_currencies.get(currency_type, 0)
                new_amount = new_currencies.get(currency_type, 0)
                
                if old_amount != new_amount:
                    currency_name = self._get_currency_display_name(currency_type)
                    change_type = ChangeType.INCREMENTED if new_amount > old_amount else ChangeType.DECREMENTED
                    amount_change = new_amount - old_amount
                    
                    change = self._create_field_change(
                        field_path=f'character.currencies.{currency_type}',
                        old_value=old_amount,
                        new_value=new_amount,
                        change_type=change_type,
                        category=ChangeCategory.INVENTORY,
                        description=f"{currency_name} {'increased' if amount_change > 0 else 'decreased'} from {old_amount} to {new_amount}"
                    )
                    
                    # Add enhanced metadata
                    change.metadata.update({
                        'currency_type': currency_type,
                        'currency_name': currency_name,
                        'amount_change': amount_change,
                        'causation_trigger': 'currency_transaction'
                    })
                    
                    changes.append(change)
        
        except Exception as e:
            self.logger.warning(f"Error detecting currency changes: {e}")
        
        return changes
    
    def _extract_currencies(self, character_data: Dict) -> Dict[str, int]:
        """Extract currencies from character data."""
        try:
            if 'character' in character_data and 'currencies' in character_data['character']:
                currencies = character_data['character']['currencies']
            elif 'currencies' in character_data:
                currencies = character_data['currencies']
            else:
                return {}
            
            return currencies if isinstance(currencies, dict) else {}
            
        except Exception as e:
            self.logger.warning(f"Error extracting currencies: {e}")
            return {}
    
    def _get_currency_display_name(self, currency_type: str) -> str:
        """Get display name for currency type."""
        currency_names = {
            'gp': 'Gold',
            'sp': 'Silver',
            'ep': 'Electrum',
            'cp': 'Copper',
            'pp': 'Platinum'
        }
        return currency_names.get(currency_type, currency_type)
    
    def _create_enhanced_inventory_change(self, field_path: str, old_value: Any, new_value: Any,
                                        change_type: ChangeType, item_name: str, 
                                        context: DetectionContext) -> FieldChange:
        """Create an enhanced inventory change with detailed attribution."""
        quantity = self._get_item_quantity(new_value) if new_value else self._get_item_quantity(old_value)
        
        # Create detailed description
        if change_type == ChangeType.ADDED:
            description = f"Added item: {item_name}"
            if quantity > 1:
                description += f" (x{quantity})"
        elif change_type == ChangeType.REMOVED:
            description = f"Removed item: {item_name}"
            if quantity > 1:
                description += f" (x{quantity})"
        else:
            description = f"Modified item: {item_name}"
        
        # Create the field change with enhanced metadata
        change = self._create_field_change(
            field_path=field_path,
            old_value=old_value,
            new_value=new_value,
            change_type=change_type,
            category=ChangeCategory.INVENTORY,
            description=description
        )
        
        # Add enhanced metadata
        change.metadata.update({
            'item_name': item_name,
            'item_quantity': quantity,
            'causation_trigger': 'inventory_management'
        })
        
        return change


class LevelProgressionDetector(BaseEnhancedDetector):
    """Detector for overall character level progression and advancement."""
    
    def __init__(self):
        field_mappings = {
            'character_level': EnhancedFieldMapping(
                api_path='character_info.level',
                display_name='Character Level',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.BASIC_INFO
            ),
            'total_level': EnhancedFieldMapping(
                api_path='metadata.total_class_levels',
                display_name='Total Level',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.BASIC_INFO
            )
        }
        
        priority_rules = {
            'character_info.level': ChangePriority.HIGH,
            'metadata.total_class_levels': ChangePriority.HIGH,
        }
        
        super().__init__(field_mappings, priority_rules)
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect overall character level progression changes."""
        changes = []
        
        try:
            # Extract overall character level from both snapshots
            old_level = extract_character_level_data(old_data)
            new_level = extract_character_level_data(new_data)

            # Get character name for descriptions
            character_name = new_data.get('character_info', {}).get('name', 'Character')

            if new_level > old_level:
                # Character leveled up
                levels_gained = new_level - old_level
                
                # Analyze which classes changed
                old_class_levels = extract_class_levels_data(old_data)
                new_class_levels = extract_class_levels_data(new_data)
                
                # Find which classes leveled up
                class_changes = []
                new_classes = []
                for class_name, new_class_level in new_class_levels.items():
                    old_class_level = old_class_levels.get(class_name, 0)
                    if new_class_level > old_class_level:
                        if old_class_level == 0:
                            new_classes.append(f"{class_name} {new_class_level}")
                        else:
                            class_changes.append(f"{class_name} {old_class_level}→{new_class_level}")
                
                # First, create a separate "Character level increased" change (similar to non-multiclass characters)
                level_increase_description = f"Character level increased: {old_level} -> {new_level}"
                if levels_gained > 1:
                    level_increase_description += f" (+{levels_gained} levels)"
                else:
                    level_increase_description += f" (+{levels_gained} level)"
                
                level_increase_change = self._create_field_change(
                    field_path='character_info.total_level',
                    old_value=old_level,
                    new_value=new_level,
                    change_type=ChangeType.INCREMENTED,
                    category=ChangeCategory.BASIC_INFO,
                    description=level_increase_description
                )
                
                level_increase_change.metadata.update({
                    'old_level': old_level,
                    'new_level': new_level,
                    'levels_gained': levels_gained,
                    'character_name': character_name,
                    'causation_trigger': 'level_progression',
                    'change_subtype': 'character_level_increase'
                })
                
                changes.append(level_increase_change)
                
                # Then create the detailed summary description
                description = f"Advanced from level {old_level} to level {new_level}"
                if levels_gained > 1:
                    description += f" (gained {levels_gained} levels)"
                
                # Add class-specific details
                if new_classes and class_changes:
                    description += f" - Multiclassed into {', '.join(new_classes)} and advanced {', '.join(class_changes)}"
                elif new_classes:
                    description += f" - Multiclassed into {', '.join(new_classes)}"
                elif class_changes:
                    description += f" - Advanced {', '.join(class_changes)}"
                
                change = self._create_field_change(
                    field_path='character_info.level',
                    old_value=old_level,
                    new_value=new_level,
                    change_type=ChangeType.INCREMENTED,
                    category=ChangeCategory.BASIC_INFO,
                    description=description
                )
                
                # Add enhanced metadata for level progression summary
                change.metadata.update({
                    'old_level': old_level,
                    'new_level': new_level,
                    'levels_gained': levels_gained,
                    'character_name': character_name,
                    'causation_trigger': 'level_progression',
                    'advancement_type': 'multiclass' if new_classes else 'level_up',
                    'class_changes': class_changes,
                    'new_classes': new_classes,
                    'old_class_levels': old_class_levels,
                    'new_class_levels': new_class_levels,
                    'proficiency_bonus_old': self._calculate_proficiency_bonus(old_level),
                    'proficiency_bonus_new': self._calculate_proficiency_bonus(new_level),
                    'proficiency_bonus_increased': self._calculate_proficiency_bonus(new_level) > self._calculate_proficiency_bonus(old_level),
                    'change_subtype': 'character_level_summary'
                })
                
                changes.append(change)
                self.logger.info(f"Detected level progression: {old_level} -> {new_level}")
            
            elif new_level < old_level:
                # Character level decreased (rare but possible)
                levels_lost = old_level - new_level
                
                description = f"Level decreased from {old_level} to {new_level}"
                if levels_lost > 1:
                    description += f" (lost {levels_lost} levels)"
                
                change = self._create_field_change(
                    field_path='character_info.level',
                    old_value=old_level,
                    new_value=new_level,
                    change_type=ChangeType.DECREMENTED,
                    category=ChangeCategory.BASIC_INFO,
                    description=description
                )
                
                change.metadata.update({
                    'old_level': old_level,
                    'new_level': new_level,
                    'levels_lost': levels_lost,
                    'character_name': character_name,
                    'causation_trigger': 'level_decrease',
                    'advancement_type': 'level_down'
                })
                
                changes.append(change)
                self.logger.info(f"Detected level decrease: {old_level} -> {new_level}")
        
            # Check for experience points changes
            old_xp = extract_experience_points_data(old_data)
            new_xp = extract_experience_points_data(new_data)
            
            if new_xp != old_xp and old_xp != 0 and new_xp != 0:
                # XP changed
                xp_change = new_xp - old_xp
                character_name = new_data.get('character_info', {}).get('name', 'Character')
                
                if xp_change > 0:
                    description = f"Gained {xp_change:,} experience points ({old_xp:,} -> {new_xp:,})"
                    change_type = ChangeType.INCREMENTED
                else:
                    description = f"Lost {abs(xp_change):,} experience points ({old_xp:,} -> {new_xp:,})"
                    change_type = ChangeType.DECREMENTED
                
                xp_change_obj = self._create_field_change(
                    field_path='character_info.experience_points',
                    old_value=old_xp,
                    new_value=new_xp,
                    change_type=change_type,
                    category=ChangeCategory.BASIC_INFO,
                    description=description
                )
                
                # Add enhanced metadata for XP change
                xp_change_obj.metadata.update({
                    'old_xp': old_xp,
                    'new_xp': new_xp,
                    'xp_change': xp_change,
                    'character_name': character_name,
                    'causation_trigger': 'experience_gain' if xp_change > 0 else 'experience_loss'
                })
                
                changes.append(xp_change_obj)
                self.logger.info(f"Detected XP change: {old_xp} -> {new_xp} ({xp_change:+})")
        
        except Exception as e:
            self.logger.error(f"Error detecting level progression changes: {e}", exc_info=True)
        
        return changes
    
    def _extract_character_level(self, character_data: Dict) -> int:
        """Extract the overall character level from character data."""
        return extract_character_level_data(character_data)
    
    def _calculate_total_level_from_classes(self, classes_data: Any) -> int:
        """Calculate total character level from class data."""
        total_level = 0
        
        try:
            if isinstance(classes_data, list):
                for cls in classes_data:
                    if isinstance(cls, dict) and 'level' in cls:
                        total_level += int(cls['level'])
            elif isinstance(classes_data, dict):
                for class_name, class_info in classes_data.items():
                    if isinstance(class_info, dict) and 'level' in class_info:
                        total_level += int(class_info['level'])
                    elif isinstance(class_info, int):
                        total_level += class_info
        except (ValueError, TypeError) as e:
            self.logger.debug(f"Error calculating total level from classes: {e}")
        
        return max(total_level, 1)  # Ensure at least level 1
    
    def _calculate_proficiency_bonus(self, level: int) -> int:
        """Calculate proficiency bonus for a given level."""
        return (level - 1) // 4 + 2
    
    def _extract_class_levels(self, character_data: Dict) -> Dict[str, int]:
        """Extract individual class levels from character data."""
        class_levels = {}
        try:
            # Try character_info.classes first
            if 'character_info' in character_data and 'classes' in character_data['character_info']:
                classes = character_data['character_info']['classes']
                if isinstance(classes, list):
                    for cls in classes:
                        if isinstance(cls, dict):
                            class_name = cls.get('definition', {}).get('name') or cls.get('name', 'Unknown')
                            level = cls.get('level', 0)
                            if level > 0:
                                class_levels[class_name] = level
            
            # Fallback to other paths
            elif 'character' in character_data and 'classes' in character_data['character']:
                classes = character_data['character']['classes']
                if isinstance(classes, list):
                    for cls in classes:
                        if isinstance(cls, dict):
                            class_name = cls.get('definition', {}).get('name') or cls.get('name', 'Unknown')
                            level = cls.get('level', 0)
                            if level > 0:
                                class_levels[class_name] = level
            
        except Exception as e:
            self.logger.debug(f"Error extracting class levels: {e}")
        
        return class_levels


# Factory function to create enhanced detectors
def create_enhanced_detector(detector_type: str) -> BaseEnhancedDetector:
    """Create an enhanced detector of the specified type."""
    detectors = {
        'level': LevelProgressionDetector,
        'feats': FeatsChangeDetector,
        'subclass': SubclassChangeDetector,
        'spells': EnhancedSpellsChangeDetector,
        'inventory': EnhancedInventoryChangeDetector,
        'background': BackgroundChangeDetector,
        'max_hp': MaxHPChangeDetector,
        'proficiencies': ProficienciesChangeDetector,
        'ability_scores': EnhancedAbilityScoreDetector,
        'race_species': RaceSpeciesChangeDetector,
        'multiclass': MulticlassChangeDetector,
        'personality': PersonalityChangeDetector,
        'spellcasting_stats': SpellcastingStatsDetector,
        'initiative': InitiativeChangeDetector,
        'passive_skills': PassiveSkillsDetector,
        'alignment': AlignmentChangeDetector,
        'size': SizeChangeDetector,
        'movement_speed': MovementSpeedDetector,
    }
    
    if detector_type not in detectors:
        raise ValueError(f"Unknown detector type: {detector_type}")
    
    return detectors[detector_type]()


def get_available_enhanced_detectors() -> List[str]:
    """Get list of available enhanced detector types."""
    return ['level', 'feats', 'subclass', 'spells', 'inventory', 'background', 'max_hp', 'proficiencies', 'ability_scores', 'race_species', 'multiclass', 'personality', 'spellcasting_stats', 'initiative', 'passive_skills', 'alignment', 'size', 'movement_speed']

class BackgroundChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for background changes and related proficiencies/traits."""
    
    def __init__(self):
        field_mappings = {
            'background': EnhancedFieldMapping(
                api_path='character.background',
                display_name='Background',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.FEATURES
            ),
            'background.skill_proficiencies': EnhancedFieldMapping(
                api_path='character.background.skill_proficiencies',
                display_name='Background Skill Proficiencies',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SKILLS
            ),
            'background.tool_proficiencies': EnhancedFieldMapping(
                api_path='character.background.tool_proficiencies',
                display_name='Background Tool Proficiencies',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SKILLS
            ),
            'background.languages': EnhancedFieldMapping(
                api_path='character.background.languages',
                display_name='Background Languages',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SKILLS
            ),
            'background.traits': EnhancedFieldMapping(
                api_path='character.background.traits',
                display_name='Background Traits',
                priority=ChangePriority.LOW,
                category=ChangeCategory.FEATURES
            ),
            'background.features': EnhancedFieldMapping(
                api_path='character.background.features',
                display_name='Background Features',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.FEATURES
            )
        }
        
        priority_rules = {
            'character.background': ChangePriority.MEDIUM,
            'character.background.*': ChangePriority.MEDIUM,
            'character.proficiencies.skills.*': ChangePriority.MEDIUM,
            'character.proficiencies.tools.*': ChangePriority.MEDIUM,
            'character.proficiencies.languages.*': ChangePriority.MEDIUM,
            'character.background.traits.*': ChangePriority.LOW
        }
        
        super().__init__(field_mappings, priority_rules)
        
        # Load background effects database
        self.background_effects = self._load_background_effects_database()
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect background changes with detailed attribution and secondary effects."""
        changes = []
        
        try:
            old_background = extract_background_data(old_data)
            new_background = extract_background_data(new_data)
            
            # Detect background change
            if old_background != new_background:
                background_change = self._create_background_change(
                    old_background, new_background, context
                )
                if background_change:
                    changes.append(background_change)
                    
                    # Detect secondary changes caused by background change
                    secondary_changes = self._detect_background_secondary_changes(
                        old_background, new_background, old_data, new_data, context
                    )
                    changes.extend(secondary_changes)
            
            # Detect specific background component changes
            component_changes = self._detect_background_component_changes(
                old_background, new_background, old_data, new_data, context
            )
            changes.extend(component_changes)
            
            self.logger.debug(f"Detected {len(changes)} background-related changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting background changes: {e}", exc_info=True)
        
        return changes
    
    def _create_background_change(self, old_background: Dict, new_background: Dict, 
                                context: DetectionContext) -> Optional[FieldChange]:
        """Create a background change with detailed attribution."""
        try:
            old_name = extract_background_name_data(old_background)
            new_name = extract_background_name_data(new_background)
            
            if old_name == new_name:
                return None
            
            # Determine change type
            if not old_background or not old_name:
                change_type = ChangeType.ADDED
                description = f"Selected background: {new_name}"
            elif not new_background or not new_name:
                change_type = ChangeType.REMOVED
                description = f"Removed background: {old_name}"
            else:
                change_type = ChangeType.MODIFIED
                description = f"Changed background from {old_name} to {new_name}"
            
            # Get background effects
            background_effects = self.background_effects.get(new_name.lower() if new_name else '', {})
            
            # Create the field change
            change = self._create_field_change(
                field_path='character.background',
                old_value=old_background,
                new_value=new_background,
                change_type=change_type,
                category=ChangeCategory.FEATURES,
                description=description
            )
            
            # Add enhanced metadata
            change.metadata.update({
                'old_background_name': old_name,
                'new_background_name': new_name,
                'background_effects': background_effects,
                'causation_trigger': 'background_selection',
                'secondary_effects_expected': len(background_effects.get('affects', [])) > 0
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error creating background change: {e}")
            return None
    
    def _detect_background_secondary_changes(self, old_background: Dict, new_background: Dict,
                                           old_data: Dict, new_data: Dict, 
                                           context: DetectionContext) -> List[FieldChange]:
        """Detect secondary changes caused by background change."""
        secondary_changes = []
        new_background_name = extract_background_name_data(new_background)
        
        if not new_background_name:
            return secondary_changes
        
        try:
            background_effects = self.background_effects.get(new_background_name.lower(), {})
            
            # Check for skill proficiency changes
            if 'skill_proficiencies' in background_effects:
                skill_changes = self._detect_background_skill_changes(
                    new_background_name, background_effects['skill_proficiencies'], 
                    old_data, new_data
                )
                secondary_changes.extend(skill_changes)
            
            # Check for tool proficiency changes
            if 'tool_proficiencies' in background_effects:
                tool_changes = self._detect_background_tool_changes(
                    new_background_name, background_effects['tool_proficiencies'],
                    old_data, new_data
                )
                secondary_changes.extend(tool_changes)
            
            # Check for language changes
            if 'languages' in background_effects:
                language_changes = self._detect_background_language_changes(
                    new_background_name, background_effects['languages'],
                    old_data, new_data
                )
                secondary_changes.extend(language_changes)
            
            # Mark all secondary changes as caused by background
            for change in secondary_changes:
                change.metadata.update({
                    'caused_by_background': new_background_name,
                    'causation_trigger': 'background_change',
                    'causation_source': 'character.background'
                })
            
        except Exception as e:
            self.logger.error(f"Error detecting background secondary changes: {e}")
        
        return secondary_changes
    
    def _detect_background_component_changes(self, old_background: Dict, new_background: Dict,
                                           old_data: Dict, new_data: Dict,
                                           context: DetectionContext) -> List[FieldChange]:
        """Detect changes in specific background components."""
        changes = []
        
        try:
            # Detect trait changes
            trait_changes = self._detect_background_trait_changes(
                old_background, new_background, context
            )
            changes.extend(trait_changes)
            
            # Detect feature changes
            feature_changes = self._detect_background_feature_changes(
                old_background, new_background, context
            )
            changes.extend(feature_changes)
            
        except Exception as e:
            self.logger.error(f"Error detecting background component changes: {e}")
        
        return changes
    
    def _detect_background_skill_changes(self, background_name: str, expected_skills: List[str],
                                       old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect skill proficiency changes from background."""
        changes = []
        
        try:
            old_skills = extract_skill_proficiencies_list(old_data)
            new_skills = extract_skill_proficiencies_list(new_data)
            
            for skill in expected_skills:
                if skill not in old_skills and skill in new_skills:
                    change = self._create_field_change(
                        field_path=f'character.proficiencies.skills.{skill.lower().replace(" ", "_")}',
                        old_value=False,
                        new_value=True,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.SKILLS,
                        description=f"Gained {skill} proficiency (from {background_name} background)"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting background skill changes: {e}")
        
        return changes
    
    def _detect_background_tool_changes(self, background_name: str, expected_tools: List[str],
                                      old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect tool proficiency changes from background."""
        changes = []
        
        try:
            old_tools = extract_tool_proficiencies_data(old_data)
            new_tools = extract_tool_proficiencies_data(new_data)
            
            for tool in expected_tools:
                if tool not in old_tools and tool in new_tools:
                    change = self._create_field_change(
                        field_path=f'character.proficiencies.tools.{tool.lower().replace(" ", "_")}',
                        old_value=False,
                        new_value=True,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.SKILLS,
                        description=f"Gained {tool} proficiency (from {background_name} background)"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting background tool changes: {e}")
        
        return changes
    
    def _detect_background_language_changes(self, background_name: str, expected_languages: List[str],
                                          old_data: Dict, new_data: Dict) -> List[FieldChange]:
        """Detect language proficiency changes from background."""
        changes = []
        
        try:
            old_languages = extract_language_proficiencies_data(old_data)
            new_languages = extract_language_proficiencies_data(new_data)
            
            for language in expected_languages:
                if language not in old_languages and language in new_languages:
                    change = self._create_field_change(
                        field_path=f'character.proficiencies.languages.{language.lower().replace(" ", "_")}',
                        old_value=False,
                        new_value=True,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.SKILLS,
                        description=f"Learned {language} language (from {background_name} background)"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting background language changes: {e}")
        
        return changes
    
    def _detect_background_trait_changes(self, old_background: Dict, new_background: Dict,
                                       context: DetectionContext) -> List[FieldChange]:
        """Detect changes in background traits (personality, ideals, bonds, flaws)."""
        changes = []

        try:
            # extract_background_traits_data returns a list, not a dict
            old_traits = extract_background_traits_data(old_background)
            new_traits = extract_background_traits_data(new_background)

            # Compare the trait lists directly
            if old_traits != new_traits:
                change_type = ChangeType.MODIFIED
                if not old_traits and new_traits:
                    change_type = ChangeType.ADDED
                elif old_traits and not new_traits:
                    change_type = ChangeType.REMOVED

                change = self._create_field_change(
                    field_path='character.background.traits',
                    old_value=old_traits,
                    new_value=new_traits,
                    change_type=change_type,
                    category=ChangeCategory.FEATURES,
                    description="Changed background traits"
                )
                changes.append(change)

        except Exception as e:
            self.logger.error(f"Error detecting background trait changes: {e}")

        return changes
    
    def _detect_background_feature_changes(self, old_background: Dict, new_background: Dict,
                                         context: DetectionContext) -> List[FieldChange]:
        """Detect changes in background features."""
        changes = []
        
        try:
            old_features = extract_background_features_data(old_background)
            new_features = extract_background_features_data(new_background)
            
            # Convert to comparable format
            old_feature_names = {f.get('name', '') for f in old_features if isinstance(f, dict)}
            new_feature_names = {f.get('name', '') for f in new_features if isinstance(f, dict)}
            
            # Detect added features
            for feature_name in new_feature_names - old_feature_names:
                if feature_name:
                    feature_data = next((f for f in new_features if f.get('name') == feature_name), {})
                    change = self._create_field_change(
                        field_path=f'character.background.features.{feature_name.lower().replace(" ", "_")}',
                        old_value=None,
                        new_value=feature_data,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.FEATURES,
                        description=f"Gained background feature: {feature_name}"
                    )
                    changes.append(change)
            
            # Detect removed features
            for feature_name in old_feature_names - new_feature_names:
                if feature_name:
                    feature_data = next((f for f in old_features if f.get('name') == feature_name), {})
                    change = self._create_field_change(
                        field_path=f'character.background.features.{feature_name.lower().replace(" ", "_")}',
                        old_value=feature_data,
                        new_value=None,
                        change_type=ChangeType.REMOVED,
                        category=ChangeCategory.FEATURES,
                        description=f"Lost background feature: {feature_name}"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting background feature changes: {e}")
        
        return changes
    
    def _load_background_effects_database(self) -> Dict[str, Dict]:
        """Load database of background mechanical effects."""
        # This would ideally load from a configuration file or database
        return {
            'acolyte': {
                'skill_proficiencies': ['Insight', 'Religion'],
                'tool_proficiencies': [],
                'languages': ['Any two languages'],
                'affects': ['proficiencies.skills', 'proficiencies.languages']
            },
            'criminal': {
                'skill_proficiencies': ['Deception', 'Stealth'],
                'tool_proficiencies': ['Thieves\' Tools', 'Gaming Set'],
                'languages': [],
                'affects': ['proficiencies.skills', 'proficiencies.tools']
            },
            'folk hero': {
                'skill_proficiencies': ['Animal Handling', 'Survival'],
                'tool_proficiencies': ['Artisan\'s Tools', 'Vehicles (Land)'],
                'languages': [],
                'affects': ['proficiencies.skills', 'proficiencies.tools']
            },
            'noble': {
                'skill_proficiencies': ['History', 'Persuasion'],
                'tool_proficiencies': ['Gaming Set'],
                'languages': ['Any one language'],
                'affects': ['proficiencies.skills', 'proficiencies.tools', 'proficiencies.languages']
            },
            'sage': {
                'skill_proficiencies': ['Arcana', 'History'],
                'tool_proficiencies': [],
                'languages': ['Draconic', 'Elvish'],
                'affects': ['proficiencies.skills', 'proficiencies.languages']
            },
            'soldier': {
                'skill_proficiencies': ['Athletics', 'Intimidation'],
                'tool_proficiencies': ['Gaming Set', 'Vehicles (Land)'],
                'languages': [],
                'affects': ['proficiencies.skills', 'proficiencies.tools']
            },
            'hermit': {
                'skill_proficiencies': ['Medicine', 'Religion'],
                'tool_proficiencies': ['Herbalism Kit'],
                'languages': ['Any one language'],
                'affects': ['proficiencies.skills', 'proficiencies.tools', 'proficiencies.languages']
            },
            'guild artisan': {
                'skill_proficiencies': ['Insight', 'Persuasion'],
                'tool_proficiencies': ['Artisan\'s Tools'],
                'languages': ['Any one language'],
                'affects': ['proficiencies.skills', 'proficiencies.tools', 'proficiencies.languages']
            }
        }
    
    def _extract_background(self, character_data: Dict) -> Dict:
        """Extract background data from character data."""
        try:
            if not character_data:
                return {}
            
            if 'character' in character_data and 'background' in character_data['character']:
                return character_data['character']['background']
            elif 'background' in character_data:
                return character_data['background']
            else:
                return {}
        except Exception as e:
            self.logger.warning(f"Error extracting background: {e}")
            return {}
    
    def _extract_background_name(self, background_data: Dict) -> str:
        return extract_background_name_data(background_data)
    
    def _extract_background_traits(self, background_data: Dict) -> Dict:
        """Extract traits from background data."""
        try:
            if isinstance(background_data, dict) and 'traits' in background_data:
                return background_data['traits']
            else:
                return {}
        except Exception:
            return {}
    
    def _extract_background_features(self, background_data: Dict) -> List[Dict]:
        """Extract features from background data."""
        try:
            if isinstance(background_data, dict) and 'features' in background_data:
                features = background_data['features']
                if isinstance(features, list):
                    return features
                elif isinstance(features, dict):
                    return [features]
            return []
        except Exception:
            return []
    
    
    
    def _extract_language_proficiencies(self, character_data: Dict) -> List[str]:
        return extract_language_proficiencies_data(character_data)


class MaxHPChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for maximum hit point changes with detailed causation attribution."""
    
    def __init__(self):
        field_mappings = {
            'max_hp': EnhancedFieldMapping(
                api_path='character.hit_points.maximum',
                display_name='Maximum Hit Points',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.COMBAT
            ),
            'hit_points': EnhancedFieldMapping(
                api_path='character.hit_points',
                display_name='Hit Points',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.COMBAT
            )
        }
        priority_rules = {
            'character.hit_points.maximum': ChangePriority.HIGH,
            'character.hit_points.*': ChangePriority.HIGH,
            'character.combat.hit_points.*': ChangePriority.HIGH
        }
        super().__init__(field_mappings, priority_rules)
        
        # Load HP calculation rules database
        self.hp_calculation_rules = self._load_hp_calculation_rules()
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect maximum HP changes with detailed causation attribution."""
        changes = []
        
        try:
            old_max_hp = extract_max_hp_data(old_data)
            new_max_hp = extract_max_hp_data(new_data)
            
            if old_max_hp != new_max_hp and old_max_hp is not None and new_max_hp is not None:
                # Calculate HP change details
                hp_change = new_max_hp - old_max_hp
                
                # Analyze causation for HP change
                causation_analysis = self._analyze_hp_change_causation(
                    old_data, new_data, old_max_hp, new_max_hp, context
                )
                
                # Create the main HP change
                hp_change_field = self._create_enhanced_hp_change(
                    field_path='character.hit_points.maximum',
                    old_value=old_max_hp,
                    new_value=new_max_hp,
                    hp_change=hp_change,
                    causation_analysis=causation_analysis,
                    context=context
                )
                changes.append(hp_change_field)
                
                self.logger.debug(f"Detected max HP change: {old_max_hp} -> {new_max_hp} ({hp_change:+d})")
                
                # Detect related HP changes (current HP adjustments, etc.)
                related_changes = self._detect_related_hp_changes(
                    old_data, new_data, hp_change, causation_analysis, context
                )
                changes.extend(related_changes)
            
        except Exception as e:
            self.logger.error(f"Error detecting max HP changes: {e}", exc_info=True)
        
        return changes
    
    def _analyze_hp_change_causation(self, old_data: Dict, new_data: Dict, 
                                   old_max_hp: int, new_max_hp: int, 
                                   context: DetectionContext) -> Dict[str, Any]:
        """Analyze what caused the maximum HP change."""
        causation = {
            'primary_causes': [],
            'contributing_factors': [],
            'detailed_breakdown': {},
            'confidence': 0.0
        }
        
        try:
            hp_change = new_max_hp - old_max_hp
            
            # Check for level progression
            level_causation = self._analyze_level_progression_hp_impact(
                old_data, new_data, hp_change
            )
            if level_causation:
                causation['primary_causes'].append(level_causation)
                causation['confidence'] += 0.4
            
            # Check for constitution changes
            constitution_causation = self._analyze_constitution_hp_impact(
                old_data, new_data, hp_change
            )
            if constitution_causation:
                causation['primary_causes'].append(constitution_causation)
                causation['confidence'] += 0.3
            
            # Check for feat effects
            feat_causation = self._analyze_feat_hp_impact(
                old_data, new_data, hp_change
            )
            if feat_causation:
                causation['contributing_factors'].extend(feat_causation)
                causation['confidence'] += 0.2
            
            # Check for magic item effects
            item_causation = self._analyze_item_hp_impact(
                old_data, new_data, hp_change
            )
            if item_causation:
                causation['contributing_factors'].extend(item_causation)
                causation['confidence'] += 0.1
            
            # Check for class feature effects
            class_feature_causation = self._analyze_class_feature_hp_impact(
                old_data, new_data, hp_change
            )
            if class_feature_causation:
                causation['contributing_factors'].extend(class_feature_causation)
                causation['confidence'] += 0.1
            
            # Create detailed breakdown
            causation['detailed_breakdown'] = self._create_hp_breakdown(
                old_data, new_data, causation
            )
            
            # Cap confidence at 1.0
            causation['confidence'] = min(causation['confidence'], 1.0)
            
        except Exception as e:
            self.logger.error(f"Error analyzing HP change causation: {e}", exc_info=True)
        
        return causation
    
    def _analyze_level_progression_hp_impact(self, old_data: Dict, new_data: Dict, 
                                           hp_change: int) -> Optional[Dict[str, Any]]:
        """Analyze HP changes from level progression."""
        try:
            old_levels = extract_character_levels_data(old_data)
            new_levels = extract_character_levels_data(new_data)
            
            level_changes = []
            total_expected_hp_gain = 0
            
            for class_name in new_levels:
                old_level = old_levels.get(class_name, 0)
                new_level = new_levels.get(class_name, 0)
                
                if new_level > old_level:
                    levels_gained = new_level - old_level
                    hit_die = self._get_class_hit_die(class_name)
                    
                    # Calculate expected HP gain (average roll + con modifier)
                    con_modifier = self._calculate_constitution_modifier(new_data)
                    expected_hp_per_level = (hit_die // 2 + 1) + con_modifier
                    expected_hp_gain = levels_gained * expected_hp_per_level
                    
                    level_changes.append({
                        'class': class_name,
                        'old_level': old_level,
                        'new_level': new_level,
                        'levels_gained': levels_gained,
                        'hit_die': hit_die,
                        'expected_hp_gain': expected_hp_gain,
                        'con_modifier': con_modifier
                    })
                    
                    total_expected_hp_gain += expected_hp_gain
            
            if level_changes and abs(total_expected_hp_gain - hp_change) <= len(level_changes) * 6:
                # HP change is consistent with level progression (allowing for roll variance)
                return {
                    'type': 'level_progression',
                    'level_changes': level_changes,
                    'expected_hp_gain': total_expected_hp_gain,
                    'actual_hp_gain': hp_change,
                    'variance': hp_change - total_expected_hp_gain,
                    'confidence': 0.9 if abs(hp_change - total_expected_hp_gain) <= 2 else 0.7
                }
            
        except Exception as e:
            self.logger.error(f"Error analyzing level progression HP impact: {e}")
        
        return None
    
    def _analyze_constitution_hp_impact(self, old_data: Dict, new_data: Dict, 
                                      hp_change: int) -> Optional[Dict[str, Any]]:
        """Analyze HP changes from constitution score changes."""
        try:
            old_con = extract_constitution_score_data(old_data)
            new_con = extract_constitution_score_data(new_data)
            
            if old_con != new_con and old_con is not None and new_con is not None:
                old_modifier = (old_con - 10) // 2
                new_modifier = (new_con - 10) // 2
                modifier_change = new_modifier - old_modifier
                
                if modifier_change != 0:
                    # Calculate expected HP change based on constitution modifier change
                    character_level = extract_total_character_level_data(new_data)
                    expected_hp_change = modifier_change * character_level
                    
                    if abs(expected_hp_change - hp_change) <= 2:
                        # HP change is consistent with constitution change
                        return {
                            'type': 'constitution_change',
                            'old_constitution': old_con,
                            'new_constitution': new_con,
                            'old_modifier': old_modifier,
                            'new_modifier': new_modifier,
                            'modifier_change': modifier_change,
                            'character_level': character_level,
                            'expected_hp_change': expected_hp_change,
                            'actual_hp_change': hp_change,
                            'confidence': 0.95 if expected_hp_change == hp_change else 0.8
                        }
            
        except Exception as e:
            self.logger.error(f"Error analyzing constitution HP impact: {e}")
        
        return None
    
    def _analyze_feat_hp_impact(self, old_data: Dict, new_data: Dict, 
                              hp_change: int) -> List[Dict[str, Any]]:
        """Analyze HP changes from feat effects."""
        feat_impacts = []
        
        try:
            old_feats = extract_feats_data(old_data)
            new_feats = extract_feats_data(new_data)
            
            # Check for new feats that affect HP
            for feat_id, feat_data in new_feats.items():
                if feat_id not in old_feats:
                    feat_name = extract_feat_name_data(feat_data)
                    hp_effect = self._get_feat_hp_effect(feat_name, new_data)
                    
                    if hp_effect:
                        feat_impacts.append({
                            'type': 'feat_effect',
                            'feat_name': feat_name,
                            'feat_id': feat_id,
                            'hp_effect': hp_effect,
                            'confidence': 0.8
                        })
            
        except Exception as e:
            self.logger.error(f"Error analyzing feat HP impact: {e}")
        
        return feat_impacts
    
    def _analyze_item_hp_impact(self, old_data: Dict, new_data: Dict, 
                              hp_change: int) -> List[Dict[str, Any]]:
        """Analyze HP changes from magic item effects."""
        item_impacts = []
        
        try:
            old_items = extract_equipped_items_data(old_data)
            new_items = extract_equipped_items_data(new_data)
            
            # Check for new items that affect HP
            for item_id, item_data in new_items.items():
                if item_id not in old_items or old_items[item_id] != item_data:
                    item_name = extract_item_name_data(item_data)
                    hp_effect = self._get_item_hp_effect(item_name, item_data)
                    
                    if hp_effect:
                        item_impacts.append({
                            'type': 'magic_item_effect',
                            'item_name': item_name,
                            'item_id': item_id,
                            'hp_effect': hp_effect,
                            'confidence': 0.7
                        })
            
        except Exception as e:
            self.logger.error(f"Error analyzing item HP impact: {e}")
        
        return item_impacts
    
    def _analyze_class_feature_hp_impact(self, old_data: Dict, new_data: Dict, 
                                       hp_change: int) -> List[Dict[str, Any]]:
        """Analyze HP changes from class feature effects."""
        feature_impacts = []
        
        try:
            # Check for class features that might affect HP
            old_features = extract_class_features_data(old_data)
            new_features = extract_class_features_data(new_data)
            
            for feature_id, feature_data in new_features.items():
                if feature_id not in old_features:
                    feature_name = extract_feature_name_data(feature_data)
                    hp_effect = self._get_class_feature_hp_effect(feature_name, feature_data, new_data)
                    
                    if hp_effect:
                        feature_impacts.append({
                            'type': 'class_feature_effect',
                            'feature_name': feature_name,
                            'feature_id': feature_id,
                            'hp_effect': hp_effect,
                            'confidence': 0.6
                        })
            
        except Exception as e:
            self.logger.error(f"Error analyzing class feature HP impact: {e}")
        
        return feature_impacts
    
    def _create_enhanced_hp_change(self, field_path: str, old_value: int, new_value: int,
                                 hp_change: int, causation_analysis: Dict[str, Any],
                                 context: DetectionContext) -> FieldChange:
        """Create an enhanced HP change with detailed attribution."""
        
        # Create detailed description
        description = f"Maximum HP changed from {old_value} to {new_value} ({hp_change:+d})"
        
        # Add causation details to description
        if causation_analysis['primary_causes']:
            primary_cause = causation_analysis['primary_causes'][0]
            if primary_cause['type'] == 'level_progression':
                level_details = primary_cause['level_changes'][0]  # Take first class for simplicity
                description += f" due to {level_details['class']} level {level_details['new_level']}"
            elif primary_cause['type'] == 'constitution_change':
                con_change = primary_cause['new_constitution'] - primary_cause['old_constitution']
                description += f" due to Constitution {primary_cause['old_constitution']} -> {primary_cause['new_constitution']} ({con_change:+d})"
        
        # Create the field change with enhanced metadata
        change = self._create_field_change(
            field_path=field_path,
            old_value=old_value,
            new_value=new_value,
            change_type=ChangeType.INCREMENTED if hp_change > 0 else ChangeType.DECREMENTED,
            category=ChangeCategory.COMBAT,
            description=description
        )
        
        # Add enhanced metadata
        change.metadata.update({
            'hp_change': hp_change,
            'causation_analysis': causation_analysis,
            'causation_confidence': causation_analysis['confidence'],
            'primary_causes': [cause['type'] for cause in causation_analysis['primary_causes']],
            'contributing_factors': [factor['type'] for factor in causation_analysis['contributing_factors']],
            'detailed_breakdown': causation_analysis['detailed_breakdown']
        })
        
        return change
    
    def _detect_related_hp_changes(self, old_data: Dict, new_data: Dict, 
                                 max_hp_change: int, causation_analysis: Dict[str, Any],
                                 context: DetectionContext) -> List[FieldChange]:
        """Detect related HP changes (current HP adjustments, temporary HP, etc.)."""
        related_changes = []
        
        try:
            # Check for current HP changes
            old_current_hp = extract_current_hp_data(old_data)
            new_current_hp = extract_current_hp_data(new_data)
            
            if (old_current_hp is not None and new_current_hp is not None and 
                old_current_hp != new_current_hp):
                
                current_hp_change = new_current_hp - old_current_hp
                
                # Check if current HP change is related to max HP change
                if abs(current_hp_change - max_hp_change) <= 1:
                    # Current HP likely adjusted to match new max HP
                    change = self._create_field_change(
                        field_path='character.hit_points.current',
                        old_value=old_current_hp,
                        new_value=new_current_hp,
                        change_type=ChangeType.INCREMENTED if current_hp_change > 0 else ChangeType.DECREMENTED,
                        category=ChangeCategory.COMBAT,
                        description=f"Current HP adjusted from {old_current_hp} to {new_current_hp} ({current_hp_change:+d}) to match new maximum"
                    )
                    
                    change.metadata.update({
                        'related_to_max_hp_change': True,
                        'hp_change': current_hp_change,
                        'causation_trigger': 'max_hp_adjustment'
                    })
                    
                    related_changes.append(change)
            
            # Check for temporary HP changes
            old_temp_hp = extract_temporary_hp_data(old_data)
            new_temp_hp = extract_temporary_hp_data(new_data)
            
            if (old_temp_hp is not None and new_temp_hp is not None and 
                old_temp_hp != new_temp_hp):
                
                temp_hp_change = new_temp_hp - old_temp_hp
                
                change = self._create_field_change(
                    field_path='character.hit_points.temporary',
                    old_value=old_temp_hp,
                    new_value=new_temp_hp,
                    change_type=ChangeType.INCREMENTED if temp_hp_change > 0 else ChangeType.DECREMENTED,
                    category=ChangeCategory.COMBAT,
                    description=f"Temporary HP changed from {old_temp_hp} to {new_temp_hp} ({temp_hp_change:+d})"
                )
                
                change.metadata.update({
                    'hp_change': temp_hp_change,
                    'hp_type': 'temporary'
                })
                
                related_changes.append(change)
            
        except Exception as e:
            self.logger.error(f"Error detecting related HP changes: {e}")
        
        return related_changes
    
    def _create_hp_breakdown(self, old_data: Dict, new_data: Dict, 
                           causation: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed breakdown of HP calculation."""
        breakdown = {
            'base_hp_calculation': {},
            'modifiers': [],
            'total_breakdown': ''
        }
        
        try:
            # Calculate base HP from class levels and hit dice
            character_levels = extract_character_levels_data(new_data)
            con_modifier = self._calculate_constitution_modifier(new_data)
            
            base_hp = 0
            level_breakdown = []
            
            for class_name, level in character_levels.items():
                if level > 0:
                    hit_die = self._get_class_hit_die(class_name)
                    # First level gets max hit die, others get average
                    first_level_hp = hit_die + con_modifier
                    remaining_levels_hp = (level - 1) * ((hit_die // 2 + 1) + con_modifier)
                    class_total_hp = first_level_hp + remaining_levels_hp
                    
                    base_hp += class_total_hp
                    level_breakdown.append({
                        'class': class_name,
                        'level': level,
                        'hit_die': hit_die,
                        'first_level_hp': first_level_hp,
                        'remaining_levels_hp': remaining_levels_hp,
                        'class_total_hp': class_total_hp
                    })
            
            breakdown['base_hp_calculation'] = {
                'base_hp': base_hp,
                'constitution_modifier': con_modifier,
                'level_breakdown': level_breakdown
            }
            
            # Add modifiers from various sources
            for cause in causation['primary_causes'] + causation['contributing_factors']:
                if 'hp_effect' in cause:
                    breakdown['modifiers'].append({
                        'source': cause['type'],
                        'effect': cause['hp_effect'],
                        'description': self._format_hp_modifier_description(cause)
                    })
            
            # Create total breakdown string
            breakdown_parts = [f"Base HP: {base_hp}"]
            for modifier in breakdown['modifiers']:
                breakdown_parts.append(f"{modifier['description']}: {modifier['effect']:+d}")
            
            breakdown['total_breakdown'] = ' + '.join(breakdown_parts)
            
        except Exception as e:
            self.logger.error(f"Error creating HP breakdown: {e}")
        
        return breakdown
    
    def _load_hp_calculation_rules(self) -> Dict[str, Dict]:
        """Load HP calculation rules and class hit dice."""
        return {
            'class_hit_dice': {
                'barbarian': 12,
                'fighter': 10,
                'paladin': 10,
                'ranger': 10,
                'bard': 8,
                'cleric': 8,
                'druid': 8,
                'monk': 8,
                'rogue': 8,
                'warlock': 8,
                'artificer': 8,
                'sorcerer': 6,
                'wizard': 6
            },
            'feat_hp_effects': {
                'tough': {'type': 'multiplier', 'value': 2, 'per_level': True},
                'durable': {'type': 'constitution_bonus', 'value': 1},
                'resilient': {'type': 'ability_score_increase', 'ability': 'constitution', 'value': 1}
            },
            'magic_item_hp_effects': {
                'amulet of health': {'type': 'constitution_set', 'value': 19},
                'belt of hill giant strength': {'type': 'constitution_bonus', 'value': 2},
                'manual of bodily health': {'type': 'constitution_increase', 'value': 2}
            }
        }
    
    # Helper methods for data extraction
    def _extract_max_hp(self, character_data: Dict) -> Optional[int]:
        """Extract maximum HP from character data."""
        try:
            paths = [
                'character.hit_points.maximum',
                'character.combat.hit_points.maximum',
                'hit_points.maximum',
                'combat.hit_points.maximum'
            ]
            
            for path in paths:
                value = self._get_nested_value(character_data, path)
                if isinstance(value, int):
                    return value
            
            return None
        except Exception:
            return None
    
    def _extract_current_hp(self, character_data: Dict) -> Optional[int]:
        """Extract current HP from character data."""
        try:
            paths = [
                'character.hit_points.current',
                'character.combat.hit_points.current',
                'hit_points.current',
                'combat.hit_points.current'
            ]
            
            for path in paths:
                value = self._get_nested_value(character_data, path)
                if isinstance(value, int):
                    return value
            
            return None
        except Exception:
            return None
    
    def _extract_temporary_hp(self, character_data: Dict) -> Optional[int]:
        """Extract temporary HP from character data."""
        try:
            paths = [
                'character.hit_points.temporary',
                'character.combat.hit_points.temporary',
                'hit_points.temporary',
                'combat.hit_points.temporary'
            ]
            
            for path in paths:
                value = self._get_nested_value(character_data, path)
                if isinstance(value, int):
                    return value
            
            return 0  # Default to 0 if not found
        except Exception:
            return 0
    
    def _extract_constitution_score(self, character_data: Dict) -> Optional[int]:
        """Extract constitution score from character data."""
        try:
            paths = [
                'character.ability_scores.constitution',
                'character.abilities.constitution',
                'ability_scores.constitution',
                'abilities.constitution'
            ]
            
            for path in paths:
                value = self._get_nested_value(character_data, path)
                if isinstance(value, int):
                    return value
            
            return None
        except Exception:
            return None
    
    def _calculate_constitution_modifier(self, character_data: Dict) -> int:
        """Calculate constitution modifier from character data."""
        con_score = extract_constitution_score_data(character_data)
        if con_score is not None:
            return (con_score - 10) // 2
        return 0
    
    def _extract_character_levels(self, character_data: Dict) -> Dict[str, int]:
        """Extract character levels by class from character data."""
        levels = {}
        try:
            paths = [
                'character.classes',
                'character.levels',
                'classes',
                'levels'
            ]
            
            for path in paths:
                classes_data = self._get_nested_value(character_data, path)
                if isinstance(classes_data, dict):
                    for class_name, class_data in classes_data.items():
                        if isinstance(class_data, dict) and 'level' in class_data:
                            levels[class_name.lower()] = class_data['level']
                        elif isinstance(class_data, int):
                            levels[class_name.lower()] = class_data
                    break
                elif isinstance(classes_data, list):
                    for class_data in classes_data:
                        if isinstance(class_data, dict):
                            class_name = class_data.get('name', '').lower()
                            level = class_data.get('level', 0)
                            if class_name and level:
                                levels[class_name] = level
                    break
            
        except Exception as e:
            self.logger.error(f"Error extracting character levels: {e}")
        
        return levels
    
    def _extract_total_character_level(self, character_data: Dict) -> int:
        """Extract total character level from character data."""
        levels = extract_character_levels_data(character_data)
        return sum(levels.values())
    
    def _get_class_hit_die(self, class_name: str) -> int:
        """Get hit die for a class."""
        return self.hp_calculation_rules['class_hit_dice'].get(class_name.lower(), 8)
    
    def _get_feat_hp_effect(self, feat_name: str, character_data: Dict) -> Optional[int]:
        """Get HP effect of a feat."""
        feat_effects = self.hp_calculation_rules['feat_hp_effects']
        feat_key = feat_name.lower()
        
        if feat_key in feat_effects:
            effect = feat_effects[feat_key]
            if effect['type'] == 'multiplier' and effect.get('per_level'):
                character_level = extract_total_character_level_data(character_data)
                return effect['value'] * character_level
            elif effect['type'] == 'constitution_bonus':
                character_level = extract_total_character_level_data(character_data)
                return effect['value'] * character_level
        
        return None
    
    def _get_item_hp_effect(self, item_name: str, item_data: Dict) -> Optional[int]:
        """Get HP effect of a magic item."""
        item_effects = self.hp_calculation_rules['magic_item_hp_effects']
        item_key = item_name.lower()
        
        if item_key in item_effects:
            effect = item_effects[item_key]
            # This would need more complex logic based on item type
            return effect.get('value', 0)
        
        return None
    
    def _get_class_feature_hp_effect(self, feature_name: str, feature_data: Dict, 
                                   character_data: Dict) -> Optional[int]:
        """Get HP effect of a class feature."""
        # This would analyze class features that affect HP
        # For now, return None as this requires detailed class feature analysis
        return None
    
    
    
    def _extract_equipped_items(self, character_data: Dict) -> Dict[str, Any]:
        """Extract equipped items from character data."""
        try:
            paths = [
                'character.equipment.equipped',
                'character.inventory.equipped',
                'equipment.equipped',
                'inventory.equipped'
            ]
            
            for path in paths:
                items_data = self._get_nested_value(character_data, path)
                if isinstance(items_data, dict):
                    return items_data
                elif isinstance(items_data, list):
                    item_dict = {}
                    for i, item in enumerate(items_data):
                        if isinstance(item, dict):
                            item_key = item.get('id', item.get('name', f'item_{i}'))
                            item_dict[str(item_key)] = item
                    return item_dict
            
            return {}
        except Exception:
            return {}
    
    
    
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        try:
            keys = path.split('.')
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            return current
        except Exception:
            return None
    
    def _format_hp_modifier_description(self, cause: Dict[str, Any]) -> str:
        """Format HP modifier description for breakdown."""
        try:
            if cause['type'] == 'feat_effect':
                return f"{cause['feat_name']} feat"
            elif cause['type'] == 'magic_item_effect':
                return f"{cause['item_name']} item"
            elif cause['type'] == 'class_feature_effect':
                return f"{cause['feature_name']} feature"
            else:
                return cause['type'].replace('_', ' ').title()
        except Exception:
            return 'Unknown modifier'


class ProficienciesChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for skill, tool, language, and saving throw proficiency changes with expertise tracking."""
    
    def __init__(self):
        field_mappings = {
            'skill_proficiencies': EnhancedFieldMapping(
                api_path='character.proficiencies.skills',
                display_name='Skill Proficiencies',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SKILLS
            ),
            'tool_proficiencies': EnhancedFieldMapping(
                api_path='character.proficiencies.tools',
                display_name='Tool Proficiencies',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SKILLS
            ),
            'language_proficiencies': EnhancedFieldMapping(
                api_path='character.proficiencies.languages',
                display_name='Language Proficiencies',
                priority=ChangePriority.LOW,
                category=ChangeCategory.SKILLS
            ),
            'saving_throw_proficiencies': EnhancedFieldMapping(
                api_path='character.proficiencies.saving_throws',
                display_name='Saving Throw Proficiencies',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.ABILITIES
            ),
            'weapon_proficiencies': EnhancedFieldMapping(
                api_path='character.proficiencies.weapons',
                display_name='Weapon Proficiencies',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.COMBAT
            ),
            'armor_proficiencies': EnhancedFieldMapping(
                api_path='character.proficiencies.armor',
                display_name='Armor Proficiencies',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.COMBAT
            )
        }
        priority_rules = {
            'character.proficiencies.saving_throws.*': ChangePriority.HIGH,
            'character.proficiencies.skills.*': ChangePriority.MEDIUM,
            'character.proficiencies.tools.*': ChangePriority.MEDIUM,
            'character.proficiencies.weapons.*': ChangePriority.MEDIUM,
            'character.proficiencies.armor.*': ChangePriority.MEDIUM,
            'character.proficiencies.languages.*': ChangePriority.LOW
        }
        super().__init__(field_mappings, priority_rules)
        
        # Proficiency bonus tracking for context
        self.proficiency_bonus_levels = {
            1: 2, 2: 2, 3: 2, 4: 2,
            5: 3, 6: 3, 7: 3, 8: 3,
            9: 4, 10: 4, 11: 4, 12: 4,
            13: 5, 14: 5, 15: 5, 16: 5,
            17: 6, 18: 6, 19: 6, 20: 6
        }
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect proficiency changes including expertise and proficiency bonus changes."""
        changes = []
        
        try:
            # Detect skill proficiency changes
            skill_changes = self._detect_skill_proficiency_changes(old_data, new_data, context)
            changes.extend(skill_changes)
            
            # Detect tool proficiency changes
            tool_changes = self._detect_tool_proficiency_changes(old_data, new_data, context)
            changes.extend(tool_changes)
            
            # Detect language proficiency changes
            language_changes = self._detect_language_proficiency_changes(old_data, new_data, context)
            changes.extend(language_changes)
            
            # Detect saving throw proficiency changes
            saving_throw_changes = self._detect_saving_throw_proficiency_changes(old_data, new_data, context)
            changes.extend(saving_throw_changes)
            
            # Detect weapon proficiency changes
            weapon_changes = self._detect_weapon_proficiency_changes(old_data, new_data, context)
            changes.extend(weapon_changes)
            
            # Detect armor proficiency changes
            armor_changes = self._detect_armor_proficiency_changes(old_data, new_data, context)
            changes.extend(armor_changes)
            
            # Detect proficiency bonus changes
            proficiency_bonus_changes = self._detect_proficiency_bonus_changes(old_data, new_data, context)
            changes.extend(proficiency_bonus_changes)
            
            # Detect expertise changes
            expertise_changes = self._detect_expertise_changes(old_data, new_data, context)
            changes.extend(expertise_changes)
            
            self.logger.debug(f"Detected {len(changes)} proficiency changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting proficiency changes: {e}", exc_info=True)
        
        return changes
    
    def _detect_skill_proficiency_changes(self, old_data: Dict, new_data: Dict, 
                                        context: DetectionContext) -> List[FieldChange]:
        """Detect skill proficiency and expertise changes."""
        changes = []
        
        try:
            old_skills = extract_skill_proficiencies_data(old_data)
            new_skills = extract_skill_proficiencies_data(new_data)
            
            # Get all skill names from both datasets
            all_skills = set(old_skills.keys()) | set(new_skills.keys())
            
            for skill in all_skills:
                old_prof = old_skills.get(skill, {'proficient': False, 'expertise': False})
                new_prof = new_skills.get(skill, {'proficient': False, 'expertise': False})
                
                # Check for proficiency changes
                if old_prof['proficient'] != new_prof['proficient']:
                    if new_prof['proficient']:
                        change = self._create_field_change(
                            field_path=f'character.proficiencies.skills.{skill.lower().replace(" ", "_")}',
                            old_value=False,
                            new_value=True,
                            change_type=ChangeType.ADDED,
                            category=ChangeCategory.SKILLS,
                            description=f"Gained {skill} proficiency"
                        )
                    else:
                        change = self._create_field_change(
                            field_path=f'character.proficiencies.skills.{skill.lower().replace(" ", "_")}',
                            old_value=True,
                            new_value=False,
                            change_type=ChangeType.REMOVED,
                            category=ChangeCategory.SKILLS,
                            description=f"Lost {skill} proficiency"
                        )
                    
                    # Add skill-specific metadata
                    change.metadata.update({
                        'skill_name': skill,
                        'proficiency_type': 'skill',
                        'expertise': new_prof.get('expertise', False)
                    })
                    changes.append(change)
                
                # Check for expertise changes (separate from proficiency)
                if old_prof.get('expertise', False) != new_prof.get('expertise', False):
                    if new_prof.get('expertise', False):
                        change = self._create_field_change(
                            field_path=f'character.proficiencies.skills.{skill.lower().replace(" ", "_")}.expertise',
                            old_value=False,
                            new_value=True,
                            change_type=ChangeType.ADDED,
                            category=ChangeCategory.SKILLS,
                            description=f"Gained {skill} expertise (double proficiency bonus)"
                        )
                    else:
                        change = self._create_field_change(
                            field_path=f'character.proficiencies.skills.{skill.lower().replace(" ", "_")}.expertise',
                            old_value=True,
                            new_value=False,
                            change_type=ChangeType.REMOVED,
                            category=ChangeCategory.SKILLS,
                            description=f"Lost {skill} expertise"
                        )
                    
                    change.metadata.update({
                        'skill_name': skill,
                        'proficiency_type': 'expertise',
                        'proficient': new_prof.get('proficient', False)
                    })
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting skill proficiency changes: {e}")
        
        return changes
    
    def _detect_tool_proficiency_changes(self, old_data: Dict, new_data: Dict, 
                                       context: DetectionContext) -> List[FieldChange]:
        """Detect tool proficiency changes."""
        changes = []
        
        try:
            old_tools = extract_tool_proficiencies_data(old_data)
            new_tools = extract_tool_proficiencies_data(new_data)
            
            # Convert lists to sets for comparison
            old_tools_set = set(old_tools)
            new_tools_set = set(new_tools)
            
            # Detect added tools
            for tool in new_tools_set - old_tools_set:
                change = self._create_field_change(
                    field_path=f'character.proficiencies.tools.{tool.lower().replace(" ", "_")}',
                    old_value=False,
                    new_value=True,
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.SKILLS,
                    description=f"Gained {tool} proficiency"
                )
                change.metadata.update({
                    'tool_name': tool,
                    'proficiency_type': 'tool'
                })
                changes.append(change)
            
            # Detect removed tools
            for tool in old_tools_set - new_tools_set:
                change = self._create_field_change(
                    field_path=f'character.proficiencies.tools.{tool.lower().replace(" ", "_")}',
                    old_value=True,
                    new_value=False,
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.SKILLS,
                    description=f"Lost {tool} proficiency"
                )
                change.metadata.update({
                    'tool_name': tool,
                    'proficiency_type': 'tool'
                })
                changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting tool proficiency changes: {e}")
        
        return changes
    
    def _detect_language_proficiency_changes(self, old_data: Dict, new_data: Dict, 
                                           context: DetectionContext) -> List[FieldChange]:
        """Detect language proficiency changes."""
        changes = []
        
        try:
            old_languages = extract_language_proficiencies_data(old_data)
            new_languages = extract_language_proficiencies_data(new_data)
            
            # Convert lists to sets for comparison
            old_languages_set = set(old_languages)
            new_languages_set = set(new_languages)
            
            # Detect added languages
            for language in new_languages_set - old_languages_set:
                change = self._create_field_change(
                    field_path=f'character.proficiencies.languages.{language.lower().replace(" ", "_")}',
                    old_value=False,
                    new_value=True,
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.SKILLS,
                    description=f"Learned {language} language"
                )
                change.metadata.update({
                    'language_name': language,
                    'proficiency_type': 'language'
                })
                changes.append(change)
            
            # Detect removed languages
            for language in old_languages_set - new_languages_set:
                change = self._create_field_change(
                    field_path=f'character.proficiencies.languages.{language.lower().replace(" ", "_")}',
                    old_value=True,
                    new_value=False,
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.SKILLS,
                    description=f"Lost {language} language"
                )
                change.metadata.update({
                    'language_name': language,
                    'proficiency_type': 'language'
                })
                changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting language proficiency changes: {e}")
        
        return changes
    
    def _detect_saving_throw_proficiency_changes(self, old_data: Dict, new_data: Dict, 
                                               context: DetectionContext) -> List[FieldChange]:
        """Detect saving throw proficiency changes."""
        changes = []
        
        try:
            old_saves = extract_saving_throw_proficiencies_data(old_data)
            new_saves = extract_saving_throw_proficiencies_data(new_data)
            
            # Convert lists to sets for comparison (normalize case)
            old_saves_set = set(save.lower() for save in old_saves)
            new_saves_set = set(save.lower() for save in new_saves)
            
            # Check each ability score for saving throw proficiency changes
            abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
            
            for ability in abilities:
                old_prof = ability.lower() in old_saves_set
                new_prof = ability.lower() in new_saves_set
                
                if old_prof != new_prof:
                    if new_prof:
                        change = self._create_field_change(
                            field_path=f'character.proficiencies.saving_throws.{ability}',
                            old_value=False,
                            new_value=True,
                            change_type=ChangeType.ADDED,
                            category=ChangeCategory.ABILITIES,
                            description=f"Gained {ability.title()} saving throw proficiency"
                        )
                    else:
                        change = self._create_field_change(
                            field_path=f'character.proficiencies.saving_throws.{ability}',
                            old_value=True,
                            new_value=False,
                            change_type=ChangeType.REMOVED,
                            category=ChangeCategory.ABILITIES,
                            description=f"Lost {ability.title()} saving throw proficiency"
                        )
                    
                    change.metadata.update({
                        'ability_name': ability,
                        'proficiency_type': 'saving_throw'
                    })
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting saving throw proficiency changes: {e}")
        
        return changes
    
    def _detect_weapon_proficiency_changes(self, old_data: Dict, new_data: Dict, 
                                         context: DetectionContext) -> List[FieldChange]:
        """Detect weapon proficiency changes."""
        changes = []
        
        try:
            old_weapons = extract_weapon_proficiencies_data(old_data)
            new_weapons = extract_weapon_proficiencies_data(new_data)
            
            # Convert lists to sets for comparison
            old_weapons_set = set(old_weapons)
            new_weapons_set = set(new_weapons)
            
            # Detect added weapons
            for weapon in new_weapons_set - old_weapons_set:
                change = self._create_field_change(
                    field_path=f'character.proficiencies.weapons.{weapon.lower().replace(" ", "_")}',
                    old_value=False,
                    new_value=True,
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.COMBAT,
                    description=f"Gained {weapon} proficiency"
                )
                change.metadata.update({
                    'weapon_name': weapon,
                    'proficiency_type': 'weapon'
                })
                changes.append(change)
            
            # Detect removed weapons
            for weapon in old_weapons_set - new_weapons_set:
                change = self._create_field_change(
                    field_path=f'character.proficiencies.weapons.{weapon.lower().replace(" ", "_")}',
                    old_value=True,
                    new_value=False,
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.COMBAT,
                    description=f"Lost {weapon} proficiency"
                )
                change.metadata.update({
                    'weapon_name': weapon,
                    'proficiency_type': 'weapon'
                })
                changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting weapon proficiency changes: {e}")
        
        return changes
    
    def _detect_armor_proficiency_changes(self, old_data: Dict, new_data: Dict, 
                                        context: DetectionContext) -> List[FieldChange]:
        """Detect armor proficiency changes."""
        changes = []
        
        try:
            old_armor = extract_armor_proficiencies_data(old_data)
            new_armor = extract_armor_proficiencies_data(new_data)
            
            # Convert lists to sets for comparison
            old_armor_set = set(old_armor)
            new_armor_set = set(new_armor)
            
            # Detect added armor
            for armor in new_armor_set - old_armor_set:
                change = self._create_field_change(
                    field_path=f'character.proficiencies.armor.{armor.lower().replace(" ", "_")}',
                    old_value=False,
                    new_value=True,
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.COMBAT,
                    description=f"Gained {armor} proficiency"
                )
                change.metadata.update({
                    'armor_name': armor,
                    'proficiency_type': 'armor'
                })
                changes.append(change)
            
            # Detect removed armor
            for armor in old_armor_set - new_armor_set:
                change = self._create_field_change(
                    field_path=f'character.proficiencies.armor.{armor.lower().replace(" ", "_")}',
                    old_value=True,
                    new_value=False,
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.COMBAT,
                    description=f"Lost {armor} proficiency"
                )
                change.metadata.update({
                    'armor_name': armor,
                    'proficiency_type': 'armor'
                })
                changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting armor proficiency changes: {e}")
        
        return changes
    
    def _detect_proficiency_bonus_changes(self, old_data: Dict, new_data: Dict, 
                                        context: DetectionContext) -> List[FieldChange]:
        """Detect proficiency bonus changes (usually due to level progression)."""
        changes = []
        
        try:
            old_bonus = extract_proficiency_bonus_data(old_data)
            new_bonus = extract_proficiency_bonus_data(new_data)
            
            if old_bonus != new_bonus:
                change = self._create_field_change(
                    field_path='character.proficiency_bonus',
                    old_value=old_bonus,
                    new_value=new_bonus,
                    change_type=ChangeType.INCREMENTED if new_bonus > old_bonus else ChangeType.DECREMENTED,
                    category=ChangeCategory.ABILITIES,
                    description=f"Proficiency bonus changed from +{old_bonus} to +{new_bonus}"
                )
                
                # Determine likely cause based on character level
                old_level = extract_character_level_data(old_data)
                new_level = extract_character_level_data(new_data)
                
                change.metadata.update({
                    'proficiency_type': 'proficiency_bonus',
                    'old_level': old_level,
                    'new_level': new_level,
                    'level_progression': new_level > old_level
                })
                
                if new_level > old_level:
                    change.description += f" (level {old_level} → {new_level})"
                    change.metadata['causation_trigger'] = 'level_progression'
                
                changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting proficiency bonus changes: {e}")
        
        return changes
    
    def _detect_expertise_changes(self, old_data: Dict, new_data: Dict, 
                                context: DetectionContext) -> List[FieldChange]:
        """Detect expertise changes (handled in skill proficiency detection but tracked separately)."""
        # This is primarily handled in _detect_skill_proficiency_changes
        # but we could add additional expertise tracking here if needed
        return []
    
    
    def _extract_tool_proficiencies(self, character_data: Dict) -> Set[str]:
        """Extract tool proficiencies from character data."""
        return set(extract_tool_proficiencies_data(character_data))
    
    def _extract_language_proficiencies(self, character_data: Dict) -> Set[str]:
        return set(extract_language_proficiencies_data(character_data))
    
    def _extract_saving_throw_proficiencies(self, character_data: Dict) -> Dict[str, bool]:
        """Extract saving throw proficiencies from character data."""
        try:
            saves = {}
            abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
            
            # Try different possible paths for saving throw data
            save_data = None
            if 'character' in character_data:
                if 'proficiencies' in character_data['character'] and 'saving_throws' in character_data['character']['proficiencies']:
                    save_data = character_data['character']['proficiencies']['saving_throws']
                elif 'saving_throws' in character_data['character']:
                    save_data = character_data['character']['saving_throws']
            elif 'saving_throws' in character_data:
                save_data = character_data['saving_throws']
            elif 'proficiencies' in character_data and 'saving_throws' in character_data['proficiencies']:
                save_data = character_data['proficiencies']['saving_throws']
            
            if save_data:
                if isinstance(save_data, dict):
                    for ability in abilities:
                        saves[ability] = save_data.get(ability, False)
                elif isinstance(save_data, list):
                    # Handle list format
                    for save in save_data:
                        if isinstance(save, dict):
                            ability = save.get('ability', save.get('name', '')).lower()
                            if ability in abilities:
                                saves[ability] = save.get('proficient', True)
                        elif isinstance(save, str) and save.lower() in abilities:
                            saves[save.lower()] = True
            
            # Ensure all abilities are represented
            for ability in abilities:
                if ability not in saves:
                    saves[ability] = False
            
            return saves
            
        except Exception as e:
            self.logger.warning(f"Error extracting saving throw proficiencies: {e}")
            return {ability: False for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']}
    
    def _extract_weapon_proficiencies(self, character_data: Dict) -> Set[str]:
        """Extract weapon proficiencies from character data."""
        return set(extract_weapon_proficiencies_data(character_data))
    
    def _extract_armor_proficiencies(self, character_data: Dict) -> Set[str]:
        """Extract armor proficiencies from character data."""
        return set(extract_armor_proficiencies_data(character_data))
    
    def _extract_proficiency_bonus(self, character_data: Dict) -> int:
        return extract_proficiency_bonus_data(character_data)
    


class RaceSpeciesChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for race and species changes with racial trait tracking."""
    
    def __init__(self):
        field_mappings = {
            'race': EnhancedFieldMapping(
                api_path='character.race',
                display_name='Race',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.BASIC_INFO
            ),
            'species': EnhancedFieldMapping(
                api_path='character.species',
                display_name='Species',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.BASIC_INFO
            ),
            'racial_traits': EnhancedFieldMapping(
                api_path='character.race.traits',
                display_name='Racial Traits',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.FEATURES
            ),
            'racial_bonuses': EnhancedFieldMapping(
                api_path='character.race.bonuses',
                display_name='Racial Bonuses',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.ABILITIES
            )
        }
        priority_rules = {
            'character.race': ChangePriority.HIGH,
            'character.species': ChangePriority.HIGH,
        }
        super().__init__(field_mappings, priority_rules)
        
        # Load racial traits and bonuses database
        self.racial_effects = self._load_racial_effects_database()
    
    def _determine_priority(self, field_path: str, change_type: ChangeType) -> ChangePriority:
        """Determine priority based on field and change type, with race-specific rules."""
        # Race/species changes are always HIGH priority
        if field_path in ['character.race', 'character.species']:
            return ChangePriority.HIGH
        
        # Racial traits and bonuses are MEDIUM priority
        if 'traits' in field_path or 'bonuses' in field_path:
            return ChangePriority.MEDIUM
        
        # Fall back to base class logic
        return super()._determine_priority(field_path, change_type)
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect race/species changes and related trait/bonus changes."""
        changes = []
        
        try:
            old_race_data = extract_race_data(old_data)
            new_race_data = extract_race_data(new_data)
            
            # Detect race/species changes
            race_changes = self._detect_race_changes(old_race_data, new_race_data, context)
            changes.extend(race_changes)
            
            # Detect racial trait changes
            trait_changes = self._detect_racial_trait_changes(old_race_data, new_race_data, context)
            changes.extend(trait_changes)
            
            # Detect racial bonus changes
            bonus_changes = self._detect_racial_bonus_changes(old_race_data, new_race_data, context)
            changes.extend(bonus_changes)
            
            self.logger.debug(f"Detected {len(changes)} race/species changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting race/species changes: {e}", exc_info=True)
        
        return changes
    
    def _detect_race_changes(self, old_race_data: Dict, new_race_data: Dict, 
                           context: DetectionContext) -> List[FieldChange]:
        """Detect changes to race/species selection."""
        changes = []
        
        try:
            old_race_name = extract_race_name_data(old_race_data)
            new_race_name = extract_race_name_data(new_race_data)
            
            if old_race_name != new_race_name:
                # Determine the field path based on available data
                field_path = 'character.race'
                if 'species' in new_race_data:
                    field_path = 'character.species'
                
                description = self._create_race_change_description(old_race_name, new_race_name)
                
                change = self._create_field_change(
                    field_path=field_path,
                    old_value=old_race_data,
                    new_value=new_race_data,
                    change_type=ChangeType.MODIFIED if old_race_name else ChangeType.ADDED,
                    category=ChangeCategory.BASIC_INFO,
                    description=description
                )
                
                # Add enhanced metadata
                change.metadata.update({
                    'old_race_name': old_race_name,
                    'new_race_name': new_race_name,
                    'race_effects': self.racial_effects.get(new_race_name.lower(), {}),
                    'causation_trigger': 'race_change',
                    'secondary_effects_expected': True
                })
                
                changes.append(change)
                
                self.logger.debug(f"Detected race change: {old_race_name} -> {new_race_name}")
        
        except Exception as e:
            self.logger.error(f"Error detecting race changes: {e}", exc_info=True)
        
        return changes
    
    def _detect_racial_trait_changes(self, old_race_data: Dict, new_race_data: Dict,
                                   context: DetectionContext) -> List[FieldChange]:
        """Detect changes to racial traits."""
        changes = []

        try:
            # extract_racial_traits_data returns List[Dict], convert to dict keyed by name
            old_traits_list = extract_racial_traits_data(old_race_data)
            new_traits_list = extract_racial_traits_data(new_race_data)

            # Convert lists to dicts keyed by trait name
            old_traits = {trait.get('name', f'trait_{i}'): trait for i, trait in enumerate(old_traits_list)}
            new_traits = {trait.get('name', f'trait_{i}'): trait for i, trait in enumerate(new_traits_list)}

            # Detect added traits
            for trait_name, trait_data in new_traits.items():
                if trait_name not in old_traits:
                    change = self._create_field_change(
                        field_path=f'character.race.traits.{trait_name.lower().replace(" ", "_")}',
                        old_value=None,
                        new_value=trait_data,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.FEATURES,
                        description=f"Gained racial trait: {trait_name}"
                    )

                    change.metadata.update({
                        'trait_name': trait_name,
                        'trait_data': trait_data,
                        'causation_trigger': 'race_change'
                    })

                    changes.append(change)

            # Detect removed traits
            for trait_name, trait_data in old_traits.items():
                if trait_name not in new_traits:
                    change = self._create_field_change(
                        field_path=f'character.race.traits.{trait_name.lower().replace(" ", "_")}',
                        old_value=trait_data,
                        new_value=None,
                        change_type=ChangeType.REMOVED,
                        category=ChangeCategory.FEATURES,
                        description=f"Lost racial trait: {trait_name}"
                    )

                    change.metadata.update({
                        'trait_name': trait_name,
                        'trait_data': trait_data,
                        'causation_trigger': 'race_change'
                    })

                    changes.append(change)

            # Detect modified traits
            for trait_name in old_traits.keys() & new_traits.keys():
                if old_traits[trait_name] != new_traits[trait_name]:
                    change = self._create_field_change(
                        field_path=f'character.race.traits.{trait_name.lower().replace(" ", "_")}',
                        old_value=old_traits[trait_name],
                        new_value=new_traits[trait_name],
                        change_type=ChangeType.MODIFIED,
                        category=ChangeCategory.FEATURES,
                        description=f"Modified racial trait: {trait_name}"
                    )

                    change.metadata.update({
                        'trait_name': trait_name,
                        'old_trait_data': old_traits[trait_name],
                        'new_trait_data': new_traits[trait_name],
                        'causation_trigger': 'race_change'
                    })

                    changes.append(change)

        except Exception as e:
            self.logger.error(f"Error detecting racial trait changes: {e}", exc_info=True)

        return changes
    
    def _detect_racial_bonus_changes(self, old_race_data: Dict, new_race_data: Dict,
                                   context: DetectionContext) -> List[FieldChange]:
        """Detect changes to racial bonuses (ability scores, proficiencies, etc.)."""
        changes = []
        
        try:
            old_bonuses = extract_racial_bonuses_data(old_race_data)
            new_bonuses = extract_racial_bonuses_data(new_race_data)
            
            # Detect ability score bonus changes
            old_ability_bonuses = old_bonuses.get('ability_scores', {})
            new_ability_bonuses = new_bonuses.get('ability_scores', {})
            
            for ability, bonus in new_ability_bonuses.items():
                old_bonus = old_ability_bonuses.get(ability, 0)
                if bonus != old_bonus:
                    change = self._create_field_change(
                        field_path=f'character.race.bonuses.ability_scores.{ability}',
                        old_value=old_bonus,
                        new_value=bonus,
                        change_type=ChangeType.INCREMENTED if bonus > old_bonus else ChangeType.DECREMENTED,
                        category=ChangeCategory.ABILITIES,
                        description=f"Racial {ability.title()} bonus changed: {old_bonus:+d} -> {bonus:+d}"
                    )
                    
                    change.metadata.update({
                        'ability_name': ability,
                        'old_bonus': old_bonus,
                        'new_bonus': bonus,
                        'bonus_difference': bonus - old_bonus,
                        'causation_trigger': 'race_change'
                    })
                    
                    changes.append(change)
            
            # Detect proficiency bonus changes
            old_proficiency_bonuses = old_bonuses.get('proficiencies', {})
            new_proficiency_bonuses = new_bonuses.get('proficiencies', {})
            
            # Check skill proficiencies
            old_skills = set(old_proficiency_bonuses.get('skills', []))
            new_skills = set(new_proficiency_bonuses.get('skills', []))
            
            for skill in new_skills - old_skills:
                change = self._create_field_change(
                    field_path=f'character.race.bonuses.proficiencies.skills.{skill.lower().replace(" ", "_")}',
                    old_value=False,
                    new_value=True,
                    change_type=ChangeType.ADDED,
                    category=ChangeCategory.SKILLS,
                    description=f"Gained racial skill proficiency: {skill}"
                )
                
                change.metadata.update({
                    'skill_name': skill,
                    'causation_trigger': 'race_change'
                })
                
                changes.append(change)
            
            for skill in old_skills - new_skills:
                change = self._create_field_change(
                    field_path=f'character.race.bonuses.proficiencies.skills.{skill.lower().replace(" ", "_")}',
                    old_value=True,
                    new_value=False,
                    change_type=ChangeType.REMOVED,
                    category=ChangeCategory.SKILLS,
                    description=f"Lost racial skill proficiency: {skill}"
                )
                
                change.metadata.update({
                    'skill_name': skill,
                    'causation_trigger': 'race_change'
                })
                
                changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting racial bonus changes: {e}", exc_info=True)
        
        return changes
    
    def _extract_race_data(self, character_data: Dict) -> Dict:
        """Extract race/species data from character data."""
        try:
            race_data = {}
            
            # Try different possible paths for race data
            if 'character' in character_data:
                char_data = character_data['character']
                
                # Check for race field
                if 'race' in char_data:
                    race_data['race'] = char_data['race']
                
                # Check for species field (2024 rules)
                if 'species' in char_data:
                    race_data['species'] = char_data['species']
                
                # Check for racial traits
                if 'racialTraits' in char_data:
                    race_data['traits'] = char_data['racialTraits']
                elif 'race' in char_data and isinstance(char_data['race'], dict) and 'traits' in char_data['race']:
                    race_data['traits'] = char_data['race']['traits']
                
                # Check for racial bonuses
                if 'race' in char_data and isinstance(char_data['race'], dict):
                    if 'bonuses' in char_data['race']:
                        race_data['bonuses'] = char_data['race']['bonuses']
                    if 'abilityScoreIncrease' in char_data['race']:
                        race_data['ability_bonuses'] = char_data['race']['abilityScoreIncrease']
            
            # Direct access patterns
            elif 'race' in character_data:
                race_data['race'] = character_data['race']
            elif 'species' in character_data:
                race_data['species'] = character_data['species']
            
            return race_data
            
        except Exception as e:
            self.logger.warning(f"Error extracting race data: {e}")
            return {}
    
    def _extract_race_name(self, race_data: Dict) -> str:
        """Extract race/species name from race data."""
        try:
            # Try different possible name fields
            if 'race' in race_data:
                race_info = race_data['race']
                if isinstance(race_info, dict):
                    return (race_info.get('fullName') or 
                           race_info.get('name') or 
                           race_info.get('raceName') or 
                           'Unknown Race')
                elif isinstance(race_info, str):
                    return race_info
            
            if 'species' in race_data:
                species_info = race_data['species']
                if isinstance(species_info, dict):
                    return (species_info.get('fullName') or 
                           species_info.get('name') or 
                           species_info.get('speciesName') or 
                           'Unknown Species')
                elif isinstance(species_info, str):
                    return species_info
            
            return 'Unknown'
            
        except Exception as e:
            self.logger.warning(f"Error extracting race name: {e}")
            return 'Unknown'
    
    def _extract_racial_traits(self, race_data: Dict) -> Dict[str, Any]:
        """Extract racial traits from race data."""
        try:
            traits = {}
            
            if 'traits' in race_data:
                trait_data = race_data['traits']
                if isinstance(trait_data, list):
                    for trait in trait_data:
                        if isinstance(trait, dict):
                            trait_name = trait.get('name', trait.get('traitName', f'trait_{len(traits)}'))
                            traits[trait_name] = trait
                        else:
                            traits[f'trait_{len(traits)}'] = trait
                elif isinstance(trait_data, dict):
                    traits.update(trait_data)
            
            # Also check for traits in race object
            if 'race' in race_data and isinstance(race_data['race'], dict):
                race_obj = race_data['race']
                if 'traits' in race_obj:
                    trait_data = race_obj['traits']
                    if isinstance(trait_data, list):
                        for trait in trait_data:
                            if isinstance(trait, dict):
                                trait_name = trait.get('name', trait.get('traitName', f'trait_{len(traits)}'))
                                traits[trait_name] = trait
                    elif isinstance(trait_data, dict):
                        traits.update(trait_data)
            
            return traits
            
        except Exception as e:
            self.logger.warning(f"Error extracting racial traits: {e}")
            return {}
    
    def _extract_racial_bonuses(self, race_data: Dict) -> Dict[str, Any]:
        """Extract racial bonuses from race data."""
        try:
            bonuses = {
                'ability_scores': {},
                'proficiencies': {
                    'skills': [],
                    'tools': [],
                    'languages': [],
                    'weapons': [],
                    'armor': []
                }
            }
            
            # Extract ability score bonuses
            if 'ability_bonuses' in race_data:
                bonuses['ability_scores'] = race_data['ability_bonuses']
            elif 'bonuses' in race_data and 'ability_scores' in race_data['bonuses']:
                bonuses['ability_scores'] = race_data['bonuses']['ability_scores']
            elif 'race' in race_data and isinstance(race_data['race'], dict):
                race_obj = race_data['race']
                if 'abilityScoreIncrease' in race_obj:
                    bonuses['ability_scores'] = race_obj['abilityScoreIncrease']
                elif 'bonuses' in race_obj and 'ability_scores' in race_obj['bonuses']:
                    bonuses['ability_scores'] = race_obj['bonuses']['ability_scores']
            
            # Extract proficiency bonuses
            if 'bonuses' in race_data and 'proficiencies' in race_data['bonuses']:
                prof_bonuses = race_data['bonuses']['proficiencies']
                for prof_type in bonuses['proficiencies'].keys():
                    if prof_type in prof_bonuses:
                        bonuses['proficiencies'][prof_type] = prof_bonuses[prof_type]
            elif 'race' in race_data and isinstance(race_data['race'], dict):
                race_obj = race_data['race']
                if 'proficiencies' in race_obj:
                    prof_data = race_obj['proficiencies']
                    for prof_type in bonuses['proficiencies'].keys():
                        if prof_type in prof_data:
                            bonuses['proficiencies'][prof_type] = prof_data[prof_type]
            
            return bonuses
            
        except Exception as e:
            self.logger.warning(f"Error extracting racial bonuses: {e}")
            return {
                'ability_scores': {},
                'proficiencies': {
                    'skills': [],
                    'tools': [],
                    'languages': [],
                    'weapons': [],
                    'armor': []
                }
            }
    
    def _create_race_change_description(self, old_race_name: str, new_race_name: str) -> str:
        """Create description for race/species change."""
        if not old_race_name or old_race_name == 'Unknown':
            return f"Selected race/species: {new_race_name}"
        else:
            return f"Changed race/species: {old_race_name} -> {new_race_name}"
    
    def _load_racial_effects_database(self) -> Dict[str, Dict]:
        """Load database of racial effects and traits."""
        # This would ideally load from a configuration file or database
        # For now, we'll include some common races as examples
        return {
            'human': {
                'ability_bonuses': {'all': 1},  # Variant human gets +1 to two different abilities
                'proficiencies': {
                    'skills': ['Any one skill']
                },
                'traits': ['Extra Language', 'Extra Skill'],
                'size': 'Medium',
                'speed': 30
            },
            'elf': {
                'ability_bonuses': {'dexterity': 2},
                'proficiencies': {
                    'skills': ['Perception'],
                    'weapons': ['Longsword', 'Shortbow', 'Longbow', 'Rapier']
                },
                'traits': ['Darkvision', 'Keen Senses', 'Fey Ancestry', 'Trance'],
                'size': 'Medium',
                'speed': 30
            },
            'high elf': {
                'ability_bonuses': {'dexterity': 2, 'intelligence': 1},
                'proficiencies': {
                    'skills': ['Perception'],
                    'weapons': ['Longsword', 'Shortbow', 'Longbow', 'Rapier']
                },
                'traits': ['Darkvision', 'Keen Senses', 'Fey Ancestry', 'Trance', 'Cantrip', 'Extra Language'],
                'size': 'Medium',
                'speed': 30
            },
            'dwarf': {
                'ability_bonuses': {'constitution': 2},
                'proficiencies': {
                    'tools': ['Smith\'s Tools', 'Brewer\'s Supplies', 'Mason\'s Tools'],
                    'weapons': ['Battleaxe', 'Handaxe', 'Light Hammer', 'Warhammer']
                },
                'traits': ['Darkvision', 'Dwarven Resilience', 'Stonecunning'],
                'size': 'Medium',
                'speed': 25
            },
            'halfling': {
                'ability_bonuses': {'dexterity': 2},
                'proficiencies': {},
                'traits': ['Lucky', 'Brave', 'Halfling Nimbleness'],
                'size': 'Small',
                'speed': 25
            },
            'dragonborn': {
                'ability_bonuses': {'strength': 2, 'charisma': 1},
                'proficiencies': {},
                'traits': ['Draconic Ancestry', 'Breath Weapon', 'Damage Resistance'],
                'size': 'Medium',
                'speed': 30
            },
            'gnome': {
                'ability_bonuses': {'intelligence': 2},
                'proficiencies': {},
                'traits': ['Darkvision', 'Gnome Cunning'],
                'size': 'Small',
                'speed': 25
            },
            'half-elf': {
                'ability_bonuses': {'charisma': 2, 'any_two': 1},
                'proficiencies': {
                    'skills': ['Any two skills']
                },
                'traits': ['Darkvision', 'Fey Ancestry', 'Extra Language'],
                'size': 'Medium',
                'speed': 30
            },
            'half-orc': {
                'ability_bonuses': {'strength': 2, 'constitution': 1},
                'proficiencies': {
                    'skills': ['Intimidation']
                },
                'traits': ['Darkvision', 'Relentless Endurance', 'Savage Attacks'],
                'size': 'Medium',
                'speed': 30
            },
            'tiefling': {
                'ability_bonuses': {'intelligence': 1, 'charisma': 2},
                'proficiencies': {},
                'traits': ['Darkvision', 'Hellish Resistance', 'Infernal Legacy'],
                'size': 'Medium',
                'speed': 30
            }
        }


class MulticlassChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for multiclass progression with detailed class attribution and causation linking."""
    
    def __init__(self):
        field_mappings = {
            'classes': EnhancedFieldMapping(
                api_path='character.classes',
                display_name='Classes',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.BASIC_INFO
            ),
            'class_levels': EnhancedFieldMapping(
                api_path='character.classes.*.level',
                display_name='Class Levels',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.BASIC_INFO
            ),
            'class_features': EnhancedFieldMapping(
                api_path='character.features.class_features',
                display_name='Class Features',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.FEATURES
            ),
            'spell_slots': EnhancedFieldMapping(
                api_path='character.spellcasting.spell_slots',
                display_name='Spell Slots',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SPELLS
            ),
            'proficiency_bonus': EnhancedFieldMapping(
                api_path='character.proficiency_bonus',
                display_name='Proficiency Bonus',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.ABILITIES
            )
        }
        priority_rules = {
            'character.classes': ChangePriority.HIGH,
            'character.classes.*.level': ChangePriority.HIGH,
            'character.features.class_features': ChangePriority.HIGH,
        }
        super().__init__(field_mappings, priority_rules)
        
        # Load class progression database
        self.class_progression = self._load_class_progression_database()
        self.multiclass_rules = self._load_multiclass_rules()
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect multiclass progression with detailed class attribution and causation linking."""
        changes = []
        
        try:
            old_classes = extract_classes_data(old_data)
            new_classes = extract_classes_data(new_data)
            
            # Detect new class additions (multiclassing)
            new_class_changes = self._detect_new_class_additions(old_classes, new_classes, context)
            changes.extend(new_class_changes)
            
            # Detect class level progressions
            level_changes = self._detect_class_level_progressions(old_classes, new_classes, context)
            changes.extend(level_changes)
            
            # Detect class feature acquisitions from multiclassing
            feature_changes = self._detect_multiclass_feature_acquisitions(
                old_classes, new_classes, old_data, new_data, context
            )
            changes.extend(feature_changes)
            
            # Detect multiclass-related spell slot changes
            spell_slot_changes = self._detect_multiclass_spell_slot_changes(
                old_classes, new_classes, old_data, new_data, context
            )
            changes.extend(spell_slot_changes)
            
            # Detect multiclass-related proficiency changes
            proficiency_changes = self._detect_multiclass_proficiency_changes(
                old_classes, new_classes, old_data, new_data, context
            )
            changes.extend(proficiency_changes)
            
            self.logger.debug(f"Detected {len(changes)} multiclass-related changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting multiclass changes: {e}", exc_info=True)
        
        return changes
    
    def _detect_new_class_additions(self, old_classes: Dict, new_classes: Dict, 
                                  context: DetectionContext) -> List[FieldChange]:
        """Detect when a character adds a new class (multiclassing)."""
        changes = []
        
        try:
            # Find classes that are new or went from level 0 to level 1+
            for class_name, new_class_data in new_classes.items():
                old_class_data = old_classes.get(class_name, {})
                old_level = old_class_data.get('level', 0)
                new_level = new_class_data.get('level', 0)
                
                # Check if this is a new class (multiclass)
                is_new_class = (class_name not in old_classes or 
                               old_level == 0 and new_level > 0)
                
                if is_new_class and new_level > 0:
                    # Determine if this is the first class or multiclassing
                    total_old_level = sum(cls.get('level', 0) for cls in old_classes.values())
                    is_multiclass = total_old_level > 0
                    
                    description = self._create_new_class_description(
                        class_name, new_level, is_multiclass
                    )
                    
                    change = self._create_field_change(
                        field_path=f'character.classes.{class_name.lower().replace(" ", "_")}',
                        old_value=old_class_data if old_class_data else None,
                        new_value=new_class_data,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.BASIC_INFO,
                        description=description
                    )
                    
                    # Add enhanced metadata
                    change.metadata.update({
                        'class_name': class_name,
                        'class_level': new_level,
                        'is_multiclass': is_multiclass,
                        'total_character_level': sum(cls.get('level', 0) for cls in new_classes.values()),
                        'causation_trigger': 'multiclass_progression' if is_multiclass else 'class_selection',
                        'class_features_gained': self._get_class_features_for_level(class_name, new_level),
                        'multiclass_prerequisites': self._check_multiclass_prerequisites(class_name, old_classes)
                    })
                    
                    changes.append(change)
                    
                    self.logger.debug(f"Detected new class addition: {class_name} level {new_level} (multiclass: {is_multiclass})")
        
        except Exception as e:
            self.logger.error(f"Error detecting new class additions: {e}", exc_info=True)
        
        return changes
    
    def _detect_class_level_progressions(self, old_classes: Dict, new_classes: Dict,
                                       context: DetectionContext) -> List[FieldChange]:
        """Detect when existing classes gain levels."""
        changes = []
        
        try:
            for class_name in old_classes.keys() & new_classes.keys():
                old_level = old_classes[class_name].get('level', 0)
                new_level = new_classes[class_name].get('level', 0)
                
                if new_level > old_level:
                    levels_gained = new_level - old_level
                    
                    # Determine if this is part of multiclass progression
                    total_classes = len([cls for cls in new_classes.values() if cls.get('level', 0) > 0])
                    is_multiclass_progression = total_classes > 1
                    
                    # Skip individual class level messages for single-class characters
                    # since the overall progression message covers it
                    if not is_multiclass_progression:
                        continue
                    
                    description = self._create_level_progression_description(
                        class_name, old_level, new_level, is_multiclass_progression
                    )
                    
                    change = self._create_field_change(
                        field_path=f'character.classes.{class_name.lower().replace(" ", "_")}.level',
                        old_value=old_level,
                        new_value=new_level,
                        change_type=ChangeType.INCREMENTED,
                        category=ChangeCategory.BASIC_INFO,
                        description=description
                    )
                    
                    # Add enhanced metadata
                    change.metadata.update({
                        'class_name': class_name,
                        'old_level': old_level,
                        'new_level': new_level,
                        'levels_gained': levels_gained,
                        'is_multiclass_progression': is_multiclass_progression,
                        'total_character_level': sum(cls.get('level', 0) for cls in new_classes.values()),
                        'causation_trigger': 'level_progression',
                        'class_features_gained': self._get_class_features_for_levels(class_name, old_level + 1, new_level)
                    })
                    
                    changes.append(change)
                    
                    self.logger.debug(f"Detected level progression: {class_name} {old_level} -> {new_level}")
        
        except Exception as e:
            self.logger.error(f"Error detecting class level progressions: {e}", exc_info=True)
        
        return changes
    
    def _detect_multiclass_feature_acquisitions(self, old_classes: Dict, new_classes: Dict,
                                              old_data: Dict, new_data: Dict,
                                              context: DetectionContext) -> List[FieldChange]:
        """Detect class features gained from multiclassing."""
        changes = []
        
        try:
            old_features = extract_class_features_data(old_data)
            new_features = extract_class_features_data(new_data)
            
            # Find new features
            for feature_id, feature_data in new_features.items():
                if feature_id not in old_features:
                    feature_name = extract_feature_name_data(feature_data)
                    source_class = self._determine_feature_source_class(feature_data, new_classes)
                    
                    if source_class:
                        class_level = new_classes.get(source_class, {}).get('level', 0)
                        
                        description = f"Gained class feature: {feature_name} ({source_class} level {class_level})"
                        
                        change = self._create_field_change(
                            field_path=f'character.features.class_features.{feature_id}',
                            old_value=None,
                            new_value=feature_data,
                            change_type=ChangeType.ADDED,
                            category=ChangeCategory.FEATURES,
                            description=description
                        )
                        
                        # Add enhanced metadata
                        change.metadata.update({
                            'feature_name': feature_name,
                            'source_class': source_class,
                            'class_level': class_level,
                            'feature_level': self._get_feature_level(feature_data),
                            'causation_trigger': 'multiclass_progression',
                            'is_multiclass_feature': len(new_classes) > 1
                        })
                        
                        changes.append(change)
                        
                        self.logger.debug(f"Detected multiclass feature: {feature_name} from {source_class}")
        
        except Exception as e:
            self.logger.error(f"Error detecting multiclass feature acquisitions: {e}", exc_info=True)
        
        return changes
    
    def _detect_multiclass_spell_slot_changes(self, old_classes: Dict, new_classes: Dict,
                                            old_data: Dict, new_data: Dict,
                                            context: DetectionContext) -> List[FieldChange]:
        """Detect spell slot changes from multiclass spellcaster progression."""
        changes = []
        
        try:
            # Check if character has spellcasting classes
            spellcasting_classes = self._get_spellcasting_classes(new_classes)
            
            if len(spellcasting_classes) > 1:  # Multiclass spellcaster
                old_spell_slots = extract_spell_slots_data(old_data)
                new_spell_slots = extract_spell_slots_data(new_data)
                
                for slot_level in range(1, 10):  # Spell levels 1-9
                    old_slots = old_spell_slots.get(str(slot_level), {}).get('max', 0)
                    new_slots = new_spell_slots.get(str(slot_level), {}).get('max', 0)
                    
                    if new_slots != old_slots:
                        # Calculate multiclass caster level
                        caster_level = self._calculate_multiclass_caster_level(spellcasting_classes)
                        
                        description = f"Spell slots (level {slot_level}) changed: {old_slots} -> {new_slots} (multiclass caster level {caster_level})"
                        
                        change = self._create_field_change(
                            field_path=f'character.spellcasting.spell_slots.{slot_level}.max',
                            old_value=old_slots,
                            new_value=new_slots,
                            change_type=ChangeType.INCREMENTED if new_slots > old_slots else ChangeType.DECREMENTED,
                            category=ChangeCategory.SPELLS,
                            description=description
                        )
                        
                        # Add enhanced metadata
                        change.metadata.update({
                            'spell_level': slot_level,
                            'old_slots': old_slots,
                            'new_slots': new_slots,
                            'multiclass_caster_level': caster_level,
                            'spellcasting_classes': list(spellcasting_classes.keys()),
                            'causation_trigger': 'multiclass_progression'
                        })
                        
                        changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting multiclass spell slot changes: {e}", exc_info=True)
        
        return changes
    
    def _detect_multiclass_proficiency_changes(self, old_classes: Dict, new_classes: Dict,
                                             old_data: Dict, new_data: Dict,
                                             context: DetectionContext) -> List[FieldChange]:
        """Detect proficiency changes from multiclassing."""
        changes = []
        
        try:
            # Find newly added classes
            new_class_names = set(new_classes.keys()) - set(old_classes.keys())
            
            for class_name in new_class_names:
                if new_classes[class_name].get('level', 0) > 0:
                    # Get multiclass proficiencies for this class
                    multiclass_profs = self._get_multiclass_proficiencies(class_name)
                    
                    old_proficiencies = extract_proficiencies_data(old_data)
                    new_proficiencies = extract_proficiencies_data(new_data)
                    
                    # Check for new proficiencies that match multiclass grants
                    for prof_type, prof_list in multiclass_profs.items():
                        old_profs = set(old_proficiencies.get(prof_type, []))
                        new_profs = set(new_proficiencies.get(prof_type, []))
                        
                        gained_profs = new_profs - old_profs
                        
                        for prof in gained_profs:
                            if prof in prof_list or 'any' in prof_list:
                                description = f"Gained {prof_type.rstrip('s')} proficiency: {prof} (multiclass {class_name})"
                                
                                change = self._create_field_change(
                                    field_path=f'character.proficiencies.{prof_type}.{prof.lower().replace(" ", "_")}',
                                    old_value=False,
                                    new_value=True,
                                    change_type=ChangeType.ADDED,
                                    category=ChangeCategory.SKILLS,
                                    description=description
                                )
                                
                                # Add enhanced metadata
                                change.metadata.update({
                                    'proficiency_name': prof,
                                    'proficiency_type': prof_type,
                                    'source_class': class_name,
                                    'causation_trigger': 'multiclass_progression',
                                    'is_multiclass_proficiency': True
                                })
                                
                                changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting multiclass proficiency changes: {e}", exc_info=True)
        
        return changes
    
    
    
    def _extract_spell_slots(self, character_data: Dict) -> Dict[str, Dict]:
        """Extract spell slots from character data."""
        try:
            if 'character' in character_data and 'spellcasting' in character_data['character']:
                spellcasting = character_data['character']['spellcasting']
                return spellcasting.get('spell_slots', {})
            elif 'spellcasting' in character_data:
                return character_data['spellcasting'].get('spell_slots', {})
            else:
                return {}
        except Exception:
            return {}
    
    def _extract_proficiencies(self, character_data: Dict) -> Dict[str, List]:
        """Extract proficiencies from character data."""
        try:
            if 'character' in character_data and 'proficiencies' in character_data['character']:
                return character_data['character']['proficiencies']
            elif 'proficiencies' in character_data:
                return character_data['proficiencies']
            else:
                return {}
        except Exception:
            return {}
    
    
    def _determine_feature_source_class(self, feature_data: Dict, classes: Dict) -> Optional[str]:
        """Determine which class a feature comes from."""
        try:
            # Check if feature has class information
            if 'class' in feature_data:
                class_info = feature_data['class']
                if isinstance(class_info, dict):
                    return class_info.get('name')
                elif isinstance(class_info, str):
                    return class_info
            
            if 'className' in feature_data:
                return feature_data['className']
            
            if 'definition' in feature_data and 'className' in feature_data['definition']:
                return feature_data['definition']['className']
            
            # Try to match by feature name patterns
            feature_name = extract_feature_name_data(feature_data).lower()
            
            for class_name in classes.keys():
                if class_name.lower() in feature_name:
                    return class_name
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error determining feature source class: {e}")
            return None
    
    def _get_feature_level(self, feature_data: Dict) -> int:
        """Get the level at which a feature is gained."""
        try:
            if 'requiredLevel' in feature_data:
                return feature_data['requiredLevel']
            elif 'level' in feature_data:
                return feature_data['level']
            elif 'definition' in feature_data and 'requiredLevel' in feature_data['definition']:
                return feature_data['definition']['requiredLevel']
            else:
                return 1
        except Exception:
            return 1
    
    def _get_spellcasting_classes(self, classes: Dict) -> Dict[str, Dict]:
        """Get classes that have spellcasting."""
        spellcasting_classes = {}
        
        for class_name, class_data in classes.items():
            if self._is_spellcasting_class(class_name):
                spellcasting_classes[class_name] = class_data
        
        return spellcasting_classes
    
    def _is_spellcasting_class(self, class_name: str) -> bool:
        """Check if a class has spellcasting."""
        spellcasting_classes = {
            'wizard', 'sorcerer', 'warlock', 'bard', 'cleric', 'druid',
            'paladin', 'ranger', 'artificer', 'eldritch knight', 'arcane trickster'
        }
        return class_name.lower() in spellcasting_classes
    
    def _calculate_multiclass_caster_level(self, spellcasting_classes: Dict) -> int:
        """Calculate multiclass spellcaster level."""
        caster_level = 0
        
        for class_name, class_data in spellcasting_classes.items():
            class_level = class_data.get('level', 0)
            
            # Full casters
            if class_name.lower() in ['wizard', 'sorcerer', 'bard', 'cleric', 'druid']:
                caster_level += class_level
            # Half casters
            elif class_name.lower() in ['paladin', 'ranger']:
                caster_level += class_level // 2
            # Third casters
            elif class_name.lower() in ['eldritch knight', 'arcane trickster']:
                caster_level += class_level // 3
            # Warlock uses different rules (pact magic)
            elif class_name.lower() == 'warlock':
                # Warlock doesn't contribute to multiclass caster level
                pass
        
        return caster_level
    
    def _get_multiclass_proficiencies(self, class_name: str) -> Dict[str, List[str]]:
        """Get proficiencies granted when multiclassing into a class."""
        multiclass_proficiencies = {
            'barbarian': {
                'armor': ['shields', 'medium armor'],
                'weapons': ['simple weapons', 'martial weapons']
            },
            'bard': {
                'armor': ['light armor'],
                'skills': ['any one skill'],
                'tools': ['any one musical instrument']
            },
            'cleric': {
                'armor': ['light armor', 'medium armor', 'shields']
            },
            'druid': {
                'armor': ['light armor', 'medium armor', 'shields (non-metal)']
            },
            'fighter': {
                'armor': ['light armor', 'medium armor', 'shields'],
                'weapons': ['simple weapons', 'martial weapons']
            },
            'monk': {
                'weapons': ['simple weapons', 'shortswords']
            },
            'paladin': {
                'armor': ['light armor', 'medium armor', 'shields'],
                'weapons': ['simple weapons', 'martial weapons']
            },
            'ranger': {
                'armor': ['light armor', 'medium armor', 'shields'],
                'weapons': ['simple weapons', 'martial weapons'],
                'skills': ['any one skill from the ranger skill list']
            },
            'rogue': {
                'armor': ['light armor'],
                'weapons': ['simple weapons', 'hand crossbows', 'longswords', 'rapiers', 'shortswords'],
                'tools': ['thieves\' tools'],
                'skills': ['any one skill from the rogue skill list']
            },
            'sorcerer': {},  # No proficiencies
            'warlock': {
                'armor': ['light armor'],
                'weapons': ['simple weapons']
            },
            'wizard': {}  # No proficiencies
        }
        
        return multiclass_proficiencies.get(class_name.lower(), {})
    
    def _check_multiclass_prerequisites(self, class_name: str, existing_classes: Dict) -> Dict[str, Any]:
        """Check multiclass prerequisites for a class."""
        prerequisites = {
            'barbarian': {'strength': 13},
            'bard': {'charisma': 13},
            'cleric': {'wisdom': 13},
            'druid': {'wisdom': 13},
            'fighter': {'strength': 13, 'dexterity': 13},  # Either one
            'monk': {'dexterity': 13, 'wisdom': 13},
            'paladin': {'strength': 13, 'charisma': 13},
            'ranger': {'dexterity': 13, 'wisdom': 13},
            'rogue': {'dexterity': 13},
            'sorcerer': {'charisma': 13},
            'warlock': {'charisma': 13},
            'wizard': {'intelligence': 13}
        }
        
        return {
            'required_abilities': prerequisites.get(class_name.lower(), {}),
            'is_first_class': len(existing_classes) == 0
        }
    
    def _get_class_features_for_level(self, class_name: str, level: int) -> List[str]:
        """Get class features gained at a specific level."""
        # This would ideally load from a comprehensive database
        # For now, return basic information
        return [f"{class_name} level {level} features"]
    
    def _get_class_features_for_levels(self, class_name: str, start_level: int, end_level: int) -> List[str]:
        """Get class features gained across a range of levels."""
        features = []
        for level in range(start_level, end_level + 1):
            features.extend(self._get_class_features_for_level(class_name, level))
        return features
    
    def _create_new_class_description(self, class_name: str, level: int, is_multiclass: bool) -> str:
        """Create description for new class addition."""
        if is_multiclass:
            return f"Multiclassed into {class_name} (level {level})"
        else:
            return f"Selected {class_name} class (level {level})"
    
    def _create_level_progression_description(self, class_name: str, old_level: int, 
                                            new_level: int, is_multiclass: bool) -> str:
        """Create description for level progression."""
        levels_gained = new_level - old_level
        
        if is_multiclass:
            return f"{class_name} level increased: {old_level} -> {new_level} (+{levels_gained} levels, multiclass progression)"
        else:
            return f"{class_name} level increased: {old_level} -> {new_level} (+{levels_gained} levels)"
    
    def _load_class_progression_database(self) -> Dict[str, Dict]:
        """Load database of class progression information."""
        # This would ideally load from a configuration file or database
        # For now, return basic structure
        return {
            'fighter': {
                'hit_die': 10,
                'primary_ability': ['strength', 'dexterity'],
                'saving_throw_proficiencies': ['strength', 'constitution'],
                'features_by_level': {
                    1: ['Fighting Style', 'Second Wind'],
                    2: ['Action Surge'],
                    3: ['Martial Archetype'],
                    4: ['Ability Score Improvement'],
                    5: ['Extra Attack']
                }
            },
            'wizard': {
                'hit_die': 6,
                'primary_ability': ['intelligence'],
                'saving_throw_proficiencies': ['intelligence', 'wisdom'],
                'features_by_level': {
                    1: ['Spellcasting', 'Arcane Recovery'],
                    2: ['Arcane Tradition'],
                    3: ['Cantrip Formulas'],
                    4: ['Ability Score Improvement']
                }
            }
            # Add more classes as needed
        }
    
    def _load_multiclass_rules(self) -> Dict[str, Any]:
        """Load multiclass rules and restrictions."""
        return {
            'spell_slot_progression': {
                'full_casters': ['wizard', 'sorcerer', 'bard', 'cleric', 'druid'],
                'half_casters': ['paladin', 'ranger'],
                'third_casters': ['eldritch knight', 'arcane trickster'],
                'pact_magic': ['warlock']
            },
            'proficiency_bonus_stacking': False,  # Proficiency bonus doesn't stack
            'hit_points_calculation': 'class_specific'  # Each class uses its own hit die
        }


class PersonalityChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for personality changes including traits, ideals, bonds, and flaws."""
    
    def __init__(self):
        field_mappings = {
            'personality_traits': EnhancedFieldMapping(
                api_path='character.personality.traits',
                display_name='Personality Traits',
                priority=ChangePriority.LOW,
                category=ChangeCategory.FEATURES
            ),
            'ideals': EnhancedFieldMapping(
                api_path='character.personality.ideals',
                display_name='Ideals',
                priority=ChangePriority.LOW,
                category=ChangeCategory.FEATURES
            ),
            'bonds': EnhancedFieldMapping(
                api_path='character.personality.bonds',
                display_name='Bonds',
                priority=ChangePriority.LOW,
                category=ChangeCategory.FEATURES
            ),
            'flaws': EnhancedFieldMapping(
                api_path='character.personality.flaws',
                display_name='Flaws',
                priority=ChangePriority.LOW,
                category=ChangeCategory.FEATURES
            ),
            'background_traits': EnhancedFieldMapping(
                api_path='character.background.traits',
                display_name='Background Personality Traits',
                priority=ChangePriority.LOW,
                category=ChangeCategory.FEATURES
            )
        }
        
        priority_rules = {
            'character.personality.*': ChangePriority.LOW,
            'character.background.traits.*': ChangePriority.LOW,
            'character.traits.*': ChangePriority.LOW,
            'character.ideals.*': ChangePriority.LOW,
            'character.bonds.*': ChangePriority.LOW,
            'character.flaws.*': ChangePriority.LOW
        }
        
        super().__init__(field_mappings, priority_rules)
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect personality-related character development changes."""
        changes = []
        
        try:
            # Extract personality data from both old and new character data
            old_personality = extract_personality_data_data(old_data)
            new_personality = extract_personality_data_data(new_data)
            
            # Detect changes in personality traits
            trait_changes = self._detect_personality_trait_changes(
                old_personality.get('traits', []), 
                new_personality.get('traits', []), 
                context
            )
            changes.extend(trait_changes)
            
            # Detect changes in ideals
            ideal_changes = self._detect_ideal_changes(
                old_personality.get('ideals', []), 
                new_personality.get('ideals', []), 
                context
            )
            changes.extend(ideal_changes)
            
            # Detect changes in bonds
            bond_changes = self._detect_bond_changes(
                old_personality.get('bonds', []), 
                new_personality.get('bonds', []), 
                context
            )
            changes.extend(bond_changes)
            
            # Detect changes in flaws
            flaw_changes = self._detect_flaw_changes(
                old_personality.get('flaws', []), 
                new_personality.get('flaws', []), 
                context
            )
            changes.extend(flaw_changes)
            
            # Detect background-related personality changes
            background_personality_changes = self._detect_background_personality_changes(
                old_data, new_data, context
            )
            changes.extend(background_personality_changes)
            
            self.logger.debug(f"Detected {len(changes)} personality-related changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting personality changes: {e}", exc_info=True)
        
        return changes
    
    def _extract_personality_data(self, character_data: Dict) -> Dict[str, List[str]]:
        """Extract personality data from character data."""
        personality_data = {
            'traits': [],
            'ideals': [],
            'bonds': [],
            'flaws': []
        }
        
        try:
            # Try different possible paths for personality data
            personality_paths = [
                'character.personality',
                'personality',
                'character.background.traits',
                'background.traits',
                'character.traits'
            ]
            
            for path in personality_paths:
                data = self._get_nested_value(character_data, path)
                if data:
                    # Handle different data structures
                    if isinstance(data, dict):
                        # Extract from dict structure
                        for key in ['traits', 'personality_traits']:
                            if key in data:
                                personality_data['traits'].extend(self._normalize_personality_list(data[key]))
                        
                        for key in ['ideals']:
                            if key in data:
                                personality_data['ideals'].extend(self._normalize_personality_list(data[key]))
                        
                        for key in ['bonds']:
                            if key in data:
                                personality_data['bonds'].extend(self._normalize_personality_list(data[key]))
                        
                        for key in ['flaws']:
                            if key in data:
                                personality_data['flaws'].extend(self._normalize_personality_list(data[key]))
                    
                    elif isinstance(data, list):
                        # If it's a list, assume it's traits
                        personality_data['traits'].extend(self._normalize_personality_list(data))
            
            # Remove duplicates while preserving order
            for key in personality_data:
                personality_data[key] = list(dict.fromkeys(personality_data[key]))
            
        except Exception as e:
            self.logger.warning(f"Error extracting personality data: {e}")
        
        return personality_data
    
    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get nested value from dictionary using dot notation."""
        try:
            keys = path.split('.')
            current = data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return None
            
            return current
        except Exception:
            return None
    
    def _normalize_personality_list(self, data: Any) -> List[str]:
        """Normalize personality data to a list of strings."""
        if not data:
            return []
        
        if isinstance(data, str):
            return [data]
        elif isinstance(data, list):
            result = []
            for item in data:
                if isinstance(item, str):
                    result.append(item)
                elif isinstance(item, dict):
                    # Extract text from dict (might have 'text', 'description', 'name', etc.)
                    text = item.get('text', item.get('description', item.get('name', str(item))))
                    if text:
                        result.append(str(text))
                else:
                    result.append(str(item))
            return result
        elif isinstance(data, dict):
            # If it's a dict, try to extract meaningful text
            text = data.get('text', data.get('description', data.get('name', '')))
            return [str(text)] if text else []
        else:
            return [str(data)]
    
    def _detect_personality_trait_changes(self, old_traits: List[str], new_traits: List[str], 
                                        context: DetectionContext) -> List[FieldChange]:
        """Detect changes in personality traits."""
        changes = []
        
        try:
            # Detect added traits
            for trait in new_traits:
                if trait not in old_traits:
                    change = self._create_field_change(
                        field_path=f'character.personality.traits.{self._sanitize_field_name(trait)}',
                        old_value=None,
                        new_value=trait,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.FEATURES,
                        description=f"Added personality trait: {trait}"
                    )
                    changes.append(change)
            
            # Detect removed traits
            for trait in old_traits:
                if trait not in new_traits:
                    change = self._create_field_change(
                        field_path=f'character.personality.traits.{self._sanitize_field_name(trait)}',
                        old_value=trait,
                        new_value=None,
                        change_type=ChangeType.REMOVED,
                        category=ChangeCategory.FEATURES,
                        description=f"Removed personality trait: {trait}"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting personality trait changes: {e}")
        
        return changes
    
    def _detect_ideal_changes(self, old_ideals: List[str], new_ideals: List[str], 
                            context: DetectionContext) -> List[FieldChange]:
        """Detect changes in ideals."""
        changes = []
        
        try:
            # Detect added ideals
            for ideal in new_ideals:
                if ideal not in old_ideals:
                    change = self._create_field_change(
                        field_path=f'character.personality.ideals.{self._sanitize_field_name(ideal)}',
                        old_value=None,
                        new_value=ideal,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.FEATURES,
                        description=f"Added ideal: {ideal}"
                    )
                    changes.append(change)
            
            # Detect removed ideals
            for ideal in old_ideals:
                if ideal not in new_ideals:
                    change = self._create_field_change(
                        field_path=f'character.personality.ideals.{self._sanitize_field_name(ideal)}',
                        old_value=ideal,
                        new_value=None,
                        change_type=ChangeType.REMOVED,
                        category=ChangeCategory.FEATURES,
                        description=f"Removed ideal: {ideal}"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting ideal changes: {e}")
        
        return changes
    
    def _detect_bond_changes(self, old_bonds: List[str], new_bonds: List[str], 
                           context: DetectionContext) -> List[FieldChange]:
        """Detect changes in bonds."""
        changes = []
        
        try:
            # Detect added bonds
            for bond in new_bonds:
                if bond not in old_bonds:
                    change = self._create_field_change(
                        field_path=f'character.personality.bonds.{self._sanitize_field_name(bond)}',
                        old_value=None,
                        new_value=bond,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.FEATURES,
                        description=f"Added bond: {bond}"
                    )
                    changes.append(change)
            
            # Detect removed bonds
            for bond in old_bonds:
                if bond not in new_bonds:
                    change = self._create_field_change(
                        field_path=f'character.personality.bonds.{self._sanitize_field_name(bond)}',
                        old_value=bond,
                        new_value=None,
                        change_type=ChangeType.REMOVED,
                        category=ChangeCategory.FEATURES,
                        description=f"Removed bond: {bond}"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting bond changes: {e}")
        
        return changes
    
    def _detect_flaw_changes(self, old_flaws: List[str], new_flaws: List[str], 
                           context: DetectionContext) -> List[FieldChange]:
        """Detect changes in flaws."""
        changes = []
        
        try:
            # Detect added flaws
            for flaw in new_flaws:
                if flaw not in old_flaws:
                    change = self._create_field_change(
                        field_path=f'character.personality.flaws.{self._sanitize_field_name(flaw)}',
                        old_value=None,
                        new_value=flaw,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.FEATURES,
                        description=f"Added flaw: {flaw}"
                    )
                    changes.append(change)
            
            # Detect removed flaws
            for flaw in old_flaws:
                if flaw not in new_flaws:
                    change = self._create_field_change(
                        field_path=f'character.personality.flaws.{self._sanitize_field_name(flaw)}',
                        old_value=flaw,
                        new_value=None,
                        change_type=ChangeType.REMOVED,
                        category=ChangeCategory.FEATURES,
                        description=f"Removed flaw: {flaw}"
                    )
                    changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error detecting flaw changes: {e}")
        
        return changes
    
    def _detect_background_personality_changes(self, old_data: Dict, new_data: Dict, 
                                             context: DetectionContext) -> List[FieldChange]:
        """Detect personality changes that come from background changes."""
        changes = []
        
        try:
            old_background = extract_background_data(old_data)
            new_background = extract_background_data(new_data)
            
            # Check if background changed
            old_bg_name = extract_background_name_data(old_background)
            new_bg_name = extract_background_name_data(new_background)
            
            if old_bg_name != new_bg_name and new_bg_name:
                # Background changed, check for personality trait changes
                old_bg_traits = extract_background_personality_traits_data(old_background)
                new_bg_traits = extract_background_personality_traits_data(new_background)
                
                # Detect changes in background-provided personality elements
                bg_changes = self._compare_background_personality_traits(
                    old_bg_traits, new_bg_traits, new_bg_name, context
                )
                changes.extend(bg_changes)
        
        except Exception as e:
            self.logger.error(f"Error detecting background personality changes: {e}")
        
        return changes
    
    def _extract_background_data(self, character_data: Dict) -> Dict:
        """Extract background data from character data."""
        try:
            if 'character' in character_data and 'background' in character_data['character']:
                return character_data['character']['background']
            elif 'background' in character_data:
                return character_data['background']
            else:
                return {}
        except Exception:
            return {}
    
    def _extract_background_name(self, background_data: Dict) -> str:
        return extract_background_name_data(background_data)
    
    def _extract_background_personality_traits(self, background_data: Dict) -> Dict[str, List[str]]:
        """Extract personality traits from background data."""
        traits = {
            'traits': [],
            'ideals': [],
            'bonds': [],
            'flaws': []
        }
        
        try:
            if isinstance(background_data, dict) and 'traits' in background_data:
                bg_traits = background_data['traits']
                
                if isinstance(bg_traits, dict):
                    for key in ['personality_traits', 'traits']:
                        if key in bg_traits:
                            traits['traits'].extend(self._normalize_personality_list(bg_traits[key]))
                    
                    for key in ['ideals']:
                        if key in bg_traits:
                            traits['ideals'].extend(self._normalize_personality_list(bg_traits[key]))
                    
                    for key in ['bonds']:
                        if key in bg_traits:
                            traits['bonds'].extend(self._normalize_personality_list(bg_traits[key]))
                    
                    for key in ['flaws']:
                        if key in bg_traits:
                            traits['flaws'].extend(self._normalize_personality_list(bg_traits[key]))
        
        except Exception as e:
            self.logger.warning(f"Error extracting background personality traits: {e}")
        
        return traits
    
    def _compare_background_personality_traits(self, old_traits: Dict[str, List[str]], 
                                             new_traits: Dict[str, List[str]], 
                                             background_name: str,
                                             context: DetectionContext) -> List[FieldChange]:
        """Compare background personality traits and create changes."""
        changes = []
        
        try:
            for trait_type in ['traits', 'ideals', 'bonds', 'flaws']:
                old_list = old_traits.get(trait_type, [])
                new_list = new_traits.get(trait_type, [])
                
                # Detect added traits
                for trait in new_list:
                    if trait not in old_list:
                        change = self._create_field_change(
                            field_path=f'character.background.traits.{trait_type}.{self._sanitize_field_name(trait)}',
                            old_value=None,
                            new_value=trait,
                            change_type=ChangeType.ADDED,
                            category=ChangeCategory.FEATURES,
                            description=f"Added {trait_type.rstrip('s')} from {background_name} background: {trait}"
                        )
                        change.metadata.update({
                            'caused_by_background': background_name,
                            'causation_trigger': 'background_change',
                            'personality_type': trait_type
                        })
                        changes.append(change)
                
                # Detect removed traits
                for trait in old_list:
                    if trait not in new_list:
                        change = self._create_field_change(
                            field_path=f'character.background.traits.{trait_type}.{self._sanitize_field_name(trait)}',
                            old_value=trait,
                            new_value=None,
                            change_type=ChangeType.REMOVED,
                            category=ChangeCategory.FEATURES,
                            description=f"Removed {trait_type.rstrip('s')} from background change: {trait}"
                        )
                        change.metadata.update({
                            'caused_by_background_change': True,
                            'causation_trigger': 'background_change',
                            'personality_type': trait_type
                        })
                        changes.append(change)
        
        except Exception as e:
            self.logger.error(f"Error comparing background personality traits: {e}")
        
        return changes
    
    def _determine_priority(self, field_path: str, change_type: ChangeType) -> ChangePriority:
        """Determine priority for personality changes - always LOW priority."""
        # Personality changes are always LOW priority regardless of change type
        return ChangePriority.LOW
    
    def _sanitize_field_name(self, name: str) -> str:
        """Sanitize a name for use in field paths."""
        try:
            # Convert to lowercase, replace spaces and special characters with underscores
            sanitized = name.lower()
            sanitized = ''.join(c if c.isalnum() else '_' for c in sanitized)
            # Remove multiple consecutive underscores
            while '__' in sanitized:
                sanitized = sanitized.replace('__', '_')
            # Remove leading/trailing underscores
            sanitized = sanitized.strip('_')
            # Limit length
            if len(sanitized) > 50:
                sanitized = sanitized[:50]
            return sanitized or 'unknown'
        except Exception:
            return 'unknown'


class SpellcastingStatsDetector(BaseEnhancedDetector):
    """Enhanced detector for spellcasting stat changes with causation attribution."""
    
    def __init__(self):
        field_mappings = {
            'spell_attack_bonus': EnhancedFieldMapping(
                api_path='character.spellcastingInfo.spellAttackBonus',
                display_name='Spell Attack Bonus',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SPELLS
            ),
            'spell_save_dc': EnhancedFieldMapping(
                api_path='character.spellcastingInfo.spellSaveDc',
                display_name='Spell Save DC',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SPELLS
            ),
            'spellcasting_ability': EnhancedFieldMapping(
                api_path='character.spellcastingInfo.spellcastingAbility',
                display_name='Spellcasting Ability',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SPELLS
            )
        }
        priority_rules = {
            'character.spellcastingInfo.spellAttackBonus': ChangePriority.MEDIUM,
            'character.spellcastingInfo.spellSaveDc': ChangePriority.MEDIUM,
            'character.spellcastingInfo.spellcastingAbility': ChangePriority.MEDIUM
        }
        super().__init__(field_mappings, priority_rules)
        
        # Load spellcasting ability mappings for different classes
        self.spellcasting_abilities = self._load_spellcasting_abilities()
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect spellcasting stat changes with detailed attribution and causation."""
        changes = []
        
        try:
            old_spellcasting = extract_spellcasting_info_data(old_data)
            new_spellcasting = extract_spellcasting_info_data(new_data)
            
            # Detect spell attack bonus changes
            if old_spellcasting.get('spell_attack_bonus') != new_spellcasting.get('spell_attack_bonus'):
                attack_change = self._create_spell_attack_change(
                    old_spellcasting.get('spell_attack_bonus'),
                    new_spellcasting.get('spell_attack_bonus'),
                    old_data, new_data, context
                )
                if attack_change:
                    changes.append(attack_change)
            
            # Detect spell save DC changes
            if old_spellcasting.get('spell_save_dc') != new_spellcasting.get('spell_save_dc'):
                save_dc_change = self._create_spell_save_dc_change(
                    old_spellcasting.get('spell_save_dc'),
                    new_spellcasting.get('spell_save_dc'),
                    old_data, new_data, context
                )
                if save_dc_change:
                    changes.append(save_dc_change)
            
            # Detect spellcasting ability changes
            if old_spellcasting.get('spellcasting_ability') != new_spellcasting.get('spellcasting_ability'):
                ability_change = self._create_spellcasting_ability_change(
                    old_spellcasting.get('spellcasting_ability'),
                    new_spellcasting.get('spellcasting_ability'),
                    old_data, new_data, context
                )
                if ability_change:
                    changes.append(ability_change)
            
            self.logger.debug(f"Detected {len(changes)} spellcasting stat changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting spellcasting stat changes: {e}", exc_info=True)
        
        return changes
    
    def _create_spell_attack_change(self, old_value: Any, new_value: Any,
                                  old_data: Dict, new_data: Dict, 
                                  context: DetectionContext) -> Optional[FieldChange]:
        """Create spell attack bonus change with detailed causation attribution."""
        try:
            # Analyze what caused the spell attack bonus change
            causation_info = self._analyze_spell_attack_causation(old_value, new_value, old_data, new_data)
            
            # Create description with causation
            if new_value is not None and old_value is not None:
                difference = new_value - old_value
                if difference > 0:
                    description = f"Spell attack bonus increased by +{difference} (now +{new_value})"
                else:
                    description = f"Spell attack bonus decreased by {difference} (now +{new_value})"
            elif new_value is not None:
                description = f"Spell attack bonus set to +{new_value}"
            else:
                description = "Spell attack bonus removed"
            
            # Add causation to description
            if causation_info['primary_cause']:
                description += f" due to {causation_info['primary_cause']}"
            
            change = self._create_field_change(
                field_path='character.spellcastingInfo.spellAttackBonus',
                old_value=old_value,
                new_value=new_value,
                change_type=ChangeType.INCREMENTED if (new_value or 0) > (old_value or 0) else ChangeType.DECREMENTED,
                category=ChangeCategory.SPELLS,
                description=description
            )
            
            # Add enhanced metadata with causation details
            change.metadata.update({
                'spellcasting_stat_type': 'spell_attack_bonus',
                'causation_analysis': causation_info,
                'detailed_description': self._create_detailed_spell_attack_description(
                    old_value, new_value, causation_info
                ),
                'calculation_breakdown': self._create_spell_attack_breakdown(new_data, causation_info)
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error creating spell attack change: {e}", exc_info=True)
            return None
    
    def _create_spell_save_dc_change(self, old_value: Any, new_value: Any,
                                   old_data: Dict, new_data: Dict,
                                   context: DetectionContext) -> Optional[FieldChange]:
        """Create spell save DC change with detailed causation attribution."""
        try:
            # Analyze what caused the spell save DC change
            causation_info = self._analyze_spell_save_dc_causation(old_value, new_value, old_data, new_data)
            
            # Create description with causation
            if new_value is not None and old_value is not None:
                difference = new_value - old_value
                if difference > 0:
                    description = f"Spell save DC increased by +{difference} (now DC {new_value})"
                else:
                    description = f"Spell save DC decreased by {difference} (now DC {new_value})"
            elif new_value is not None:
                description = f"Spell save DC set to DC {new_value}"
            else:
                description = "Spell save DC removed"
            
            # Add causation to description
            if causation_info['primary_cause']:
                description += f" due to {causation_info['primary_cause']}"
            
            change = self._create_field_change(
                field_path='character.spellcastingInfo.spellSaveDc',
                old_value=old_value,
                new_value=new_value,
                change_type=ChangeType.INCREMENTED if (new_value or 0) > (old_value or 0) else ChangeType.DECREMENTED,
                category=ChangeCategory.SPELLS,
                description=description
            )
            
            # Add enhanced metadata with causation details
            change.metadata.update({
                'spellcasting_stat_type': 'spell_save_dc',
                'causation_analysis': causation_info,
                'detailed_description': self._create_detailed_spell_save_dc_description(
                    old_value, new_value, causation_info
                ),
                'calculation_breakdown': self._create_spell_save_dc_breakdown(new_data, causation_info)
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error creating spell save DC change: {e}", exc_info=True)
            return None
    
    def _create_spellcasting_ability_change(self, old_value: Any, new_value: Any,
                                          old_data: Dict, new_data: Dict,
                                          context: DetectionContext) -> Optional[FieldChange]:
        """Create spellcasting ability change with detailed causation attribution."""
        try:
            # Analyze what caused the spellcasting ability change
            causation_info = self._analyze_spellcasting_ability_causation(old_value, new_value, old_data, new_data)
            
            # Create description with causation
            old_ability_name = self._get_ability_name(old_value)
            new_ability_name = self._get_ability_name(new_value)
            
            if old_ability_name and new_ability_name:
                description = f"Spellcasting ability changed from {old_ability_name} to {new_ability_name}"
            elif new_ability_name:
                description = f"Spellcasting ability set to {new_ability_name}"
            else:
                description = "Spellcasting ability removed"
            
            # Add causation to description
            if causation_info['primary_cause']:
                description += f" due to {causation_info['primary_cause']}"
            
            change = self._create_field_change(
                field_path='character.spellcastingInfo.spellcastingAbility',
                old_value=old_value,
                new_value=new_value,
                change_type=ChangeType.MODIFIED,
                category=ChangeCategory.SPELLS,
                description=description
            )
            
            # Add enhanced metadata with causation details
            change.metadata.update({
                'spellcasting_stat_type': 'spellcasting_ability',
                'causation_analysis': causation_info,
                'detailed_description': self._create_detailed_spellcasting_ability_description(
                    old_value, new_value, causation_info
                ),
                'old_ability_name': old_ability_name,
                'new_ability_name': new_ability_name
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error creating spellcasting ability change: {e}", exc_info=True)
            return None
    
    def _analyze_spell_attack_causation(self, old_value: Any, new_value: Any,
                                      old_data: Dict, new_data: Dict) -> Dict[str, Any]:
        """Analyze what caused the spell attack bonus change."""
        causation_info = {
            'primary_cause': None,
            'contributing_factors': [],
            'ability_score_change': None,
            'proficiency_bonus_change': None,
            'equipment_bonus_change': None,
            'feat_bonus_change': None,
            'confidence': 0.0
        }
        
        try:
            # Check for ability score changes
            old_abilities = extract_ability_scores_data(old_data)
            new_abilities = extract_ability_scores_data(new_data)
            spellcasting_ability = self._get_primary_spellcasting_ability(new_data)
            
            if spellcasting_ability and spellcasting_ability in old_abilities and spellcasting_ability in new_abilities:
                old_score = old_abilities[spellcasting_ability]
                new_score = new_abilities[spellcasting_ability]
                old_modifier = (old_score - 10) // 2
                new_modifier = (new_score - 10) // 2
                
                if old_modifier != new_modifier:
                    causation_info['ability_score_change'] = {
                        'ability': spellcasting_ability,
                        'old_score': old_score,
                        'new_score': new_score,
                        'old_modifier': old_modifier,
                        'new_modifier': new_modifier,
                        'modifier_change': new_modifier - old_modifier
                    }
                    causation_info['primary_cause'] = f"{spellcasting_ability.title()} modifier change"
                    causation_info['contributing_factors'].append('ability_score_increase')
                    causation_info['confidence'] = 0.9
            
            # Check for proficiency bonus changes (level progression)
            old_prof_bonus = self._calculate_proficiency_bonus(old_data)
            new_prof_bonus = self._calculate_proficiency_bonus(new_data)
            
            if old_prof_bonus != new_prof_bonus:
                causation_info['proficiency_bonus_change'] = {
                    'old_bonus': old_prof_bonus,
                    'new_bonus': new_prof_bonus,
                    'change': new_prof_bonus - old_prof_bonus
                }
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = "level progression"
                    causation_info['confidence'] = 0.8
                causation_info['contributing_factors'].append('level_progression')
            
            # Check for equipment changes
            equipment_bonus_change = self._detect_equipment_spell_bonus_change(old_data, new_data)
            if equipment_bonus_change:
                causation_info['equipment_bonus_change'] = equipment_bonus_change
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = f"equipment change ({equipment_bonus_change['item_name']})"
                    causation_info['confidence'] = 0.7
                causation_info['contributing_factors'].append('equipment_change')
            
            # Check for feat changes
            feat_bonus_change = self._detect_feat_spell_bonus_change(old_data, new_data)
            if feat_bonus_change:
                causation_info['feat_bonus_change'] = feat_bonus_change
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = f"feat selection ({feat_bonus_change['feat_name']})"
                    causation_info['confidence'] = 0.8
                causation_info['contributing_factors'].append('feat_selection')
            
        except Exception as e:
            self.logger.error(f"Error analyzing spell attack causation: {e}", exc_info=True)
        
        return causation_info
    
    def _analyze_spell_save_dc_causation(self, old_value: Any, new_value: Any,
                                       old_data: Dict, new_data: Dict) -> Dict[str, Any]:
        """Analyze what caused the spell save DC change."""
        # Spell save DC uses the same factors as spell attack bonus
        # DC = 8 + proficiency bonus + ability modifier
        return self._analyze_spell_attack_causation(old_value, new_value, old_data, new_data)
    
    def _analyze_spellcasting_ability_causation(self, old_value: Any, new_value: Any,
                                              old_data: Dict, new_data: Dict) -> Dict[str, Any]:
        """Analyze what caused the spellcasting ability change."""
        causation_info = {
            'primary_cause': None,
            'contributing_factors': [],
            'class_change': None,
            'subclass_change': None,
            'multiclass_change': None,
            'feat_change': None,
            'confidence': 0.0
        }
        
        try:
            # Check for class changes
            old_classes = extract_classes_list_data(old_data)
            new_classes = extract_classes_list_data(new_data)
            
            if old_classes != new_classes:
                causation_info['class_change'] = {
                    'old_classes': old_classes,
                    'new_classes': new_classes
                }
                causation_info['primary_cause'] = "class progression or multiclassing"
                causation_info['contributing_factors'].append('class_change')
                causation_info['confidence'] = 0.9
            
            # Check for subclass changes
            subclass_change = self._detect_subclass_change(old_data, new_data)
            if subclass_change:
                causation_info['subclass_change'] = subclass_change
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = f"subclass selection ({subclass_change['subclass_name']})"
                    causation_info['confidence'] = 0.8
                causation_info['contributing_factors'].append('subclass_selection')
            
            # Check for feat changes that might affect spellcasting ability
            feat_change = self._detect_spellcasting_feat_change(old_data, new_data)
            if feat_change:
                causation_info['feat_change'] = feat_change
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = f"feat selection ({feat_change['feat_name']})"
                    causation_info['confidence'] = 0.7
                causation_info['contributing_factors'].append('feat_selection')
            
        except Exception as e:
            self.logger.error(f"Error analyzing spellcasting ability causation: {e}", exc_info=True)
        
        return causation_info
    
    def _create_detailed_spell_attack_description(self, old_value: Any, new_value: Any,
                                                causation_info: Dict[str, Any]) -> str:
        """Create detailed description for spell attack bonus change."""
        description = f"Spell attack bonus changed from +{old_value or 0} to +{new_value or 0}."
        
        if causation_info['ability_score_change']:
            ability_info = causation_info['ability_score_change']
            description += f" This change is due to a {ability_info['ability'].title()} score increase from {ability_info['old_score']} to {ability_info['new_score']}, changing the modifier from +{ability_info['old_modifier']} to +{ability_info['new_modifier']}."
        
        if causation_info['proficiency_bonus_change']:
            prof_info = causation_info['proficiency_bonus_change']
            description += f" The proficiency bonus also changed from +{prof_info['old_bonus']} to +{prof_info['new_bonus']} due to level progression."
        
        if causation_info['equipment_bonus_change']:
            equip_info = causation_info['equipment_bonus_change']
            description += f" Equipment changes ({equip_info['item_name']}) contributed a bonus of +{equip_info['bonus']}."
        
        if causation_info['feat_bonus_change']:
            feat_info = causation_info['feat_bonus_change']
            description += f" The {feat_info['feat_name']} feat provides a +{feat_info['bonus']} bonus to spell attacks."
        
        return description
    
    def _create_detailed_spell_save_dc_description(self, old_value: Any, new_value: Any,
                                                 causation_info: Dict[str, Any]) -> str:
        """Create detailed description for spell save DC change."""
        description = f"Spell save DC changed from DC {old_value or 8} to DC {new_value or 8}."
        
        if causation_info['ability_score_change']:
            ability_info = causation_info['ability_score_change']
            description += f" This change is due to a {ability_info['ability'].title()} score increase from {ability_info['old_score']} to {ability_info['new_score']}, changing the modifier from +{ability_info['old_modifier']} to +{ability_info['new_modifier']}."
        
        if causation_info['proficiency_bonus_change']:
            prof_info = causation_info['proficiency_bonus_change']
            description += f" The proficiency bonus also changed from +{prof_info['old_bonus']} to +{prof_info['new_bonus']} due to level progression."
        
        if causation_info['equipment_bonus_change']:
            equip_info = causation_info['equipment_bonus_change']
            description += f" Equipment changes ({equip_info['item_name']}) contributed a bonus of +{equip_info['bonus']}."
        
        if causation_info['feat_bonus_change']:
            feat_info = causation_info['feat_bonus_change']
            description += f" The {feat_info['feat_name']} feat provides a +{feat_info['bonus']} bonus to spell save DC."
        
        return description
    
    def _create_detailed_spellcasting_ability_description(self, old_value: Any, new_value: Any,
                                                        causation_info: Dict[str, Any]) -> str:
        """Create detailed description for spellcasting ability change."""
        old_name = self._get_ability_name(old_value)
        new_name = self._get_ability_name(new_value)
        
        description = f"Spellcasting ability changed from {old_name or 'None'} to {new_name or 'None'}."
        
        if causation_info['class_change']:
            description += " This change is due to class progression or multiclassing, which determines the primary spellcasting ability."
        
        if causation_info['subclass_change']:
            subclass_info = causation_info['subclass_change']
            description += f" The {subclass_info['subclass_name']} subclass uses {new_name} as its spellcasting ability."
        
        if causation_info['feat_change']:
            feat_info = causation_info['feat_change']
            description += f" The {feat_info['feat_name']} feat allows using {new_name} for spellcasting."
        
        return description
    
    def _create_spell_attack_breakdown(self, character_data: Dict, causation_info: Dict[str, Any]) -> str:
        """Create calculation breakdown for spell attack bonus."""
        spellcasting_ability = self._get_primary_spellcasting_ability(character_data)
        ability_modifier = self._get_ability_modifier(character_data, spellcasting_ability)
        proficiency_bonus = self._calculate_proficiency_bonus(character_data)
        
        breakdown = f"{proficiency_bonus} (proficiency) + {ability_modifier} ({spellcasting_ability.title()} modifier)"
        
        if causation_info.get('equipment_bonus_change'):
            equip_bonus = causation_info['equipment_bonus_change']['bonus']
            breakdown += f" + {equip_bonus} (equipment)"
        
        if causation_info.get('feat_bonus_change'):
            feat_bonus = causation_info['feat_bonus_change']['bonus']
            breakdown += f" + {feat_bonus} (feat)"
        
        return breakdown
    
    def _create_spell_save_dc_breakdown(self, character_data: Dict, causation_info: Dict[str, Any]) -> str:
        """Create calculation breakdown for spell save DC."""
        spellcasting_ability = self._get_primary_spellcasting_ability(character_data)
        ability_modifier = self._get_ability_modifier(character_data, spellcasting_ability)
        proficiency_bonus = self._calculate_proficiency_bonus(character_data)
        
        breakdown = f"8 + {proficiency_bonus} (proficiency) + {ability_modifier} ({spellcasting_ability.title()} modifier)"
        
        if causation_info.get('equipment_bonus_change'):
            equip_bonus = causation_info['equipment_bonus_change']['bonus']
            breakdown += f" + {equip_bonus} (equipment)"
        
        if causation_info.get('feat_bonus_change'):
            feat_bonus = causation_info['feat_bonus_change']['bonus']
            breakdown += f" + {feat_bonus} (feat)"
        
        return breakdown
    
    def _extract_spellcasting_info(self, character_data: Dict) -> Dict[str, Any]:
        """Extract spellcasting information from character data."""
        try:
            if 'character' in character_data and 'spellcastingInfo' in character_data['character']:
                spellcasting_info = character_data['character']['spellcastingInfo']
            elif 'spellcastingInfo' in character_data:
                spellcasting_info = character_data['spellcastingInfo']
            elif 'character' in character_data and 'spellcasting' in character_data['character']:
                spellcasting_info = character_data['character']['spellcasting']
            elif 'spellcasting' in character_data:
                spellcasting_info = character_data['spellcasting']
            else:
                return {}
            
            return {
                'spell_attack_bonus': spellcasting_info.get('spellAttackBonus'),
                'spell_save_dc': spellcasting_info.get('spellSaveDc'),
                'spellcasting_ability': spellcasting_info.get('spellcastingAbility')
            }
            
        except Exception as e:
            self.logger.warning(f"Error extracting spellcasting info: {e}")
            return {}
    
    def _get_primary_spellcasting_ability(self, character_data: Dict) -> Optional[str]:
        """Get the primary spellcasting ability for the character."""
        try:
            spellcasting_info = extract_spellcasting_info_data(character_data)
            if spellcasting_info.get('spellcasting_ability'):
                return spellcasting_info['spellcasting_ability'].lower()
            
            # Fallback: determine from classes
            classes = extract_classes_list_data(character_data)
            for class_info in classes:
                class_name = class_info.get('name', '').lower()
                if class_name in self.spellcasting_abilities:
                    return self.spellcasting_abilities[class_name]
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error getting primary spellcasting ability: {e}")
            return None
    
    def _get_ability_modifier(self, character_data: Dict, ability_name: str) -> int:
        """Get the modifier for a specific ability score."""
        try:
            abilities = extract_ability_scores_data(character_data)
            score = abilities.get(ability_name, 10)
            return (score - 10) // 2
        except Exception:
            return 0
    
    def _calculate_proficiency_bonus(self, character_data: Dict) -> int:
        """Calculate proficiency bonus based on character level."""
        try:
            # Try character_info.proficiency_bonus first (actual data structure)
            if 'character_info' in character_data and 'proficiency_bonus' in character_data['character_info']:
                return character_data['character_info']['proficiency_bonus']
            
            # Try to get proficiency bonus directly
            if 'character' in character_data and 'proficiencyBonus' in character_data['character']:
                return character_data['character']['proficiencyBonus']
            
            # Calculate from total level
            total_level = self._get_total_character_level(character_data)
            return (total_level - 1) // 4 + 2
            
        except Exception:
            return 2  # Default for level 1
    
    def _get_total_character_level(self, character_data: Dict) -> int:
        """Get total character level across all classes."""
        try:
            classes = extract_classes_list_data(character_data)
            return sum(class_info.get('level', 0) for class_info in classes)
        except Exception:
            return 1
    
    def _get_ability_name(self, ability_value: Any) -> Optional[str]:
        """Convert ability value to readable name."""
        if isinstance(ability_value, str):
            return ability_value.title()
        elif isinstance(ability_value, int):
            ability_names = ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma']
            if 1 <= ability_value <= 6:
                return ability_names[ability_value - 1]
        return None
    
    def _detect_equipment_spell_bonus_change(self, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect equipment changes that affect spell bonuses."""
        try:
            # This is a simplified implementation
            # In practice, you'd need to analyze specific magic items
            old_equipment = extract_equipment_data(old_data)
            new_equipment = extract_equipment_data(new_data)
            
            # Look for magic items that provide spell bonuses
            spell_bonus_items = ['rod of the pact keeper', 'wand of the war mage', 'arcane focus']
            
            for item_name in spell_bonus_items:
                old_has_item = any(item_name in str(item).lower() for item in old_equipment)
                new_has_item = any(item_name in str(item).lower() for item in new_equipment)
                
                if old_has_item != new_has_item:
                    return {
                        'item_name': item_name,
                        'bonus': 1 if new_has_item else -1,
                        'added': new_has_item
                    }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error detecting equipment spell bonus change: {e}")
            return None
    
    def _detect_feat_spell_bonus_change(self, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect feat changes that affect spell bonuses."""
        try:
            old_feats = extract_feats_data(old_data)
            new_feats = extract_feats_data(new_data)
            
            # Look for feats that provide spell bonuses
            spell_bonus_feats = ['elemental adept', 'spell sniper', 'war caster']
            
            for feat_name in spell_bonus_feats:
                old_has_feat = any(feat_name in str(feat).lower() for feat in old_feats.values())
                new_has_feat = any(feat_name in str(feat).lower() for feat in new_feats.values())
                
                if old_has_feat != new_has_feat:
                    return {
                        'feat_name': feat_name,
                        'bonus': 1 if new_has_feat else -1,
                        'added': new_has_feat
                    }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error detecting feat spell bonus change: {e}")
            return None
    
    def _detect_subclass_change(self, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect subclass changes that might affect spellcasting ability."""
        try:
            old_classes = extract_classes_list_data(old_data)
            new_classes = extract_classes_list_data(new_data)
            
            for old_class, new_class in zip(old_classes, new_classes):
                old_subclass = old_class.get('subclass', {}).get('name', '')
                new_subclass = new_class.get('subclass', {}).get('name', '')
                
                if old_subclass != new_subclass and new_subclass:
                    return {
                        'class_name': new_class.get('name', ''),
                        'subclass_name': new_subclass,
                        'old_subclass': old_subclass
                    }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error detecting subclass change: {e}")
            return None
    
    def _detect_spellcasting_feat_change(self, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect feat changes that affect spellcasting ability."""
        try:
            old_feats = extract_feats_data(old_data)
            new_feats = extract_feats_data(new_data)
            
            # Look for feats that might change spellcasting ability
            spellcasting_feats = ['fey touched', 'shadow touched', 'magic initiate', 'ritual caster']
            
            for feat_name in spellcasting_feats:
                old_has_feat = any(feat_name in str(feat).lower() for feat in old_feats.values())
                new_has_feat = any(feat_name in str(feat).lower() for feat in new_feats.values())
                
                if old_has_feat != new_has_feat and new_has_feat:
                    return {
                        'feat_name': feat_name,
                        'added': True
                    }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error detecting spellcasting feat change: {e}")
            return None
    
    def _load_spellcasting_abilities(self) -> Dict[str, str]:
        """Load spellcasting abilities for different classes."""
        return {
            'wizard': 'intelligence',
            'sorcerer': 'charisma',
            'warlock': 'charisma',
            'bard': 'charisma',
            'cleric': 'wisdom',
            'druid': 'wisdom',
            'ranger': 'wisdom',
            'paladin': 'charisma',
            'artificer': 'intelligence',
            'eldritch knight': 'intelligence',
            'arcane trickster': 'intelligence'
        }
    
    
    
    


class InitiativeChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for initiative bonus changes with causation attribution."""
    
    def __init__(self):
        field_mappings = {
            'initiative_bonus': EnhancedFieldMapping(
                api_path='character.combat.initiative_bonus',
                display_name='Initiative Bonus',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.COMBAT
            ),
            'initiative_modifier': EnhancedFieldMapping(
                api_path='character.combat.initiative_modifier',
                display_name='Initiative Modifier',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.COMBAT
            )
        }
        priority_rules = {
            'character.combat.initiative_bonus': ChangePriority.MEDIUM,
            'character.combat.initiative_modifier': ChangePriority.MEDIUM
        }
        super().__init__(field_mappings, priority_rules)
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect initiative bonus changes with detailed attribution and causation."""
        changes = []
        
        try:
            old_initiative = extract_initiative_info_data(old_data)
            new_initiative = extract_initiative_info_data(new_data)
            
            # Detect initiative bonus changes
            if old_initiative.get('bonus') != new_initiative.get('bonus'):
                bonus_change = self._create_initiative_bonus_change(
                    old_initiative.get('bonus'),
                    new_initiative.get('bonus'),
                    old_data, new_data, context
                )
                if bonus_change:
                    changes.append(bonus_change)
            
            # Detect initiative modifier changes (if tracked separately)
            if old_initiative.get('modifier') != new_initiative.get('modifier'):
                modifier_change = self._create_initiative_modifier_change(
                    old_initiative.get('modifier'),
                    new_initiative.get('modifier'),
                    old_data, new_data, context
                )
                if modifier_change:
                    changes.append(modifier_change)
            
            self.logger.debug(f"Detected {len(changes)} initiative changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting initiative changes: {e}", exc_info=True)
        
        return changes
    
    def _create_initiative_bonus_change(self, old_value: Any, new_value: Any,
                                      old_data: Dict, new_data: Dict, 
                                      context: DetectionContext) -> Optional[FieldChange]:
        """Create initiative bonus change with detailed causation attribution."""
        try:
            # Analyze what caused the initiative bonus change
            causation_info = self._analyze_initiative_causation(old_value, new_value, old_data, new_data)
            
            # Create description with causation
            if new_value is not None and old_value is not None:
                difference = new_value - old_value
                if difference > 0:
                    description = f"Initiative bonus increased by +{difference} (now +{new_value})"
                else:
                    description = f"Initiative bonus decreased by {difference} (now +{new_value})"
            elif new_value is not None:
                description = f"Initiative bonus set to +{new_value}"
            else:
                description = "Initiative bonus removed"
            
            # Add causation to description
            if causation_info['primary_cause']:
                description += f" due to {causation_info['primary_cause']}"
            
            change = self._create_field_change(
                field_path='character.combat.initiative_bonus',
                old_value=old_value,
                new_value=new_value,
                change_type=ChangeType.INCREMENTED if (new_value or 0) > (old_value or 0) else ChangeType.DECREMENTED,
                category=ChangeCategory.COMBAT,
                description=description
            )
            
            # Add enhanced metadata with causation details
            change.metadata.update({
                'initiative_stat_type': 'initiative_bonus',
                'causation_analysis': causation_info,
                'detailed_description': self._create_detailed_initiative_description(
                    old_value, new_value, causation_info
                ),
                'calculation_breakdown': self._create_initiative_breakdown(new_data, causation_info)
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error creating initiative bonus change: {e}", exc_info=True)
            return None
    
    def _create_initiative_modifier_change(self, old_value: Any, new_value: Any,
                                         old_data: Dict, new_data: Dict,
                                         context: DetectionContext) -> Optional[FieldChange]:
        """Create initiative modifier change with detailed causation attribution."""
        try:
            # Analyze what caused the initiative modifier change
            causation_info = self._analyze_initiative_causation(old_value, new_value, old_data, new_data)
            
            # Create description with causation
            if new_value is not None and old_value is not None:
                difference = new_value - old_value
                if difference > 0:
                    description = f"Initiative modifier increased by +{difference} (now +{new_value})"
                else:
                    description = f"Initiative modifier decreased by {difference} (now +{new_value})"
            elif new_value is not None:
                description = f"Initiative modifier set to +{new_value}"
            else:
                description = "Initiative modifier removed"
            
            # Add causation to description
            if causation_info['primary_cause']:
                description += f" due to {causation_info['primary_cause']}"
            
            change = self._create_field_change(
                field_path='character.combat.initiative_modifier',
                old_value=old_value,
                new_value=new_value,
                change_type=ChangeType.INCREMENTED if (new_value or 0) > (old_value or 0) else ChangeType.DECREMENTED,
                category=ChangeCategory.COMBAT,
                description=description
            )
            
            # Add enhanced metadata with causation details
            change.metadata.update({
                'initiative_stat_type': 'initiative_modifier',
                'causation_analysis': causation_info,
                'detailed_description': self._create_detailed_initiative_description(
                    old_value, new_value, causation_info
                )
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error creating initiative modifier change: {e}", exc_info=True)
            return None
    
    def _analyze_initiative_causation(self, old_value: Any, new_value: Any,
                                    old_data: Dict, new_data: Dict) -> Dict[str, Any]:
        """Analyze what caused the initiative bonus/modifier change."""
        causation_info = {
            'primary_cause': None,
            'contributing_factors': [],
            'dexterity_change': None,
            'equipment_bonus_change': None,
            'feat_bonus_change': None,
            'class_feature_change': None,
            'magic_item_change': None,
            'confidence': 0.0
        }
        
        try:
            # Check for Dexterity score changes (primary factor for initiative)
            old_abilities = extract_ability_scores_data(old_data)
            new_abilities = extract_ability_scores_data(new_data)
            
            old_dex = old_abilities.get('dexterity', 10)
            new_dex = new_abilities.get('dexterity', 10)
            old_dex_mod = (old_dex - 10) // 2
            new_dex_mod = (new_dex - 10) // 2
            
            if old_dex_mod != new_dex_mod:
                causation_info['dexterity_change'] = {
                    'old_score': old_dex,
                    'new_score': new_dex,
                    'old_modifier': old_dex_mod,
                    'new_modifier': new_dex_mod,
                    'modifier_change': new_dex_mod - old_dex_mod
                }
                causation_info['primary_cause'] = "Dexterity modifier change"
                causation_info['contributing_factors'].append('ability_score_increase')
                causation_info['confidence'] = 0.9
            
            # Check for equipment changes that affect initiative
            equipment_bonus_change = self._detect_equipment_initiative_bonus_change(old_data, new_data)
            if equipment_bonus_change:
                causation_info['equipment_bonus_change'] = equipment_bonus_change
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = f"equipment change ({equipment_bonus_change['item_name']})"
                    causation_info['confidence'] = 0.8
                causation_info['contributing_factors'].append('equipment_change')
            
            # Check for feat changes that affect initiative
            feat_bonus_change = self._detect_feat_initiative_bonus_change(old_data, new_data)
            if feat_bonus_change:
                causation_info['feat_bonus_change'] = feat_bonus_change
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = f"feat selection ({feat_bonus_change['feat_name']})"
                    causation_info['confidence'] = 0.8
                causation_info['contributing_factors'].append('feat_selection')
            
            # Check for class feature changes that affect initiative
            class_feature_change = self._detect_class_feature_initiative_change(old_data, new_data)
            if class_feature_change:
                causation_info['class_feature_change'] = class_feature_change
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = f"class feature ({class_feature_change['feature_name']})"
                    causation_info['confidence'] = 0.7
                causation_info['contributing_factors'].append('class_feature')
            
            # Check for magic item changes
            magic_item_change = self._detect_magic_item_initiative_change(old_data, new_data)
            if magic_item_change:
                causation_info['magic_item_change'] = magic_item_change
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = f"magic item ({magic_item_change['item_name']})"
                    causation_info['confidence'] = 0.7
                causation_info['contributing_factors'].append('magic_item')
            
        except Exception as e:
            self.logger.error(f"Error analyzing initiative causation: {e}", exc_info=True)
        
        return causation_info
    
    def _create_detailed_initiative_description(self, old_value: Any, new_value: Any, 
                                              causation_info: Dict[str, Any]) -> str:
        """Create detailed description for initiative change."""
        description = f"Initiative bonus changed from {old_value or 0:+d} to {new_value or 0:+d}"
        
        if causation_info['primary_cause']:
            description += f" due to {causation_info['primary_cause']}"
        
        # Add detailed breakdown of contributing factors
        factors = []
        if causation_info.get('dexterity_change'):
            dex_change = causation_info['dexterity_change']
            factors.append(f"Dexterity modifier changed from {dex_change['old_modifier']:+d} to {dex_change['new_modifier']:+d}")
        
        if causation_info.get('equipment_bonus_change'):
            eq_change = causation_info['equipment_bonus_change']
            factors.append(f"Equipment bonus from {eq_change['item_name']}: {eq_change['bonus_change']:+d}")
        
        if causation_info.get('feat_bonus_change'):
            feat_change = causation_info['feat_bonus_change']
            factors.append(f"Feat bonus from {feat_change['feat_name']}: {feat_change['bonus_change']:+d}")
        
        if causation_info.get('class_feature_change'):
            class_change = causation_info['class_feature_change']
            factors.append(f"Class feature bonus from {class_change['feature_name']}: {class_change['bonus_change']:+d}")
        
        if factors:
            description += f". Contributing factors: {'; '.join(factors)}"
        
        return description
    
    def _create_initiative_breakdown(self, character_data: Dict, causation_info: Dict[str, Any]) -> str:
        """Create calculation breakdown for initiative bonus."""
        breakdown_parts = []
        
        # Base Dexterity modifier
        abilities = extract_ability_scores_data(character_data)
        dex_score = abilities.get('dexterity', 10)
        dex_mod = (dex_score - 10) // 2
        breakdown_parts.append(f"{dex_mod:+d} (Dex)")
        
        # Equipment bonuses
        if causation_info.get('equipment_bonus_change'):
            eq_change = causation_info['equipment_bonus_change']
            breakdown_parts.append(f"{eq_change['new_bonus']:+d} ({eq_change['item_name']})")
        
        # Feat bonuses
        if causation_info.get('feat_bonus_change'):
            feat_change = causation_info['feat_bonus_change']
            breakdown_parts.append(f"{feat_change['new_bonus']:+d} ({feat_change['feat_name']})")
        
        # Class feature bonuses
        if causation_info.get('class_feature_change'):
            class_change = causation_info['class_feature_change']
            breakdown_parts.append(f"{class_change['new_bonus']:+d} ({class_change['feature_name']})")
        
        return " ".join(breakdown_parts) if breakdown_parts else f"{dex_mod:+d} (Dex only)"
    
    def _extract_initiative_info(self, character_data: Dict) -> Dict[str, Any]:
        """Extract initiative information from character data."""
        try:
            initiative_info = {}
            
            # Try different possible paths for initiative data
            if 'character' in character_data and 'combat' in character_data['character']:
                combat_data = character_data['character']['combat']
                initiative_info['bonus'] = combat_data.get('initiative_bonus')
                initiative_info['modifier'] = combat_data.get('initiative_modifier')
            elif 'combat' in character_data:
                combat_data = character_data['combat']
                initiative_info['bonus'] = combat_data.get('initiative_bonus')
                initiative_info['modifier'] = combat_data.get('initiative_modifier')
            
            # If not found in combat section, try to calculate from Dexterity
            if initiative_info.get('bonus') is None and initiative_info.get('modifier') is None:
                abilities = extract_ability_scores_data(character_data)
                dex_score = abilities.get('dexterity', 10)
                dex_mod = (dex_score - 10) // 2
                initiative_info['modifier'] = dex_mod
                initiative_info['bonus'] = dex_mod  # Base initiative is usually just Dex modifier
            
            return initiative_info
            
        except Exception as e:
            self.logger.warning(f"Error extracting initiative info: {e}")
            return {'bonus': None, 'modifier': None}
    
    def _detect_equipment_initiative_bonus_change(self, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect equipment changes that affect initiative."""
        try:
            old_equipment = extract_equipment_data(old_data)
            new_equipment = extract_equipment_data(new_data)
            
            # Look for items that provide initiative bonuses
            initiative_items = [
                'ioun stone', 'alert feat', 'dexterity bonus', 'initiative bonus',
                'boots of speed', 'cloak of elvenkind'
            ]
            
            for item in new_equipment:
                if isinstance(item, dict):
                    item_name = item.get('name', '').lower()
                    item_desc = item.get('description', '').lower()
                    
                    # Check if this item affects initiative
                    if any(init_keyword in item_name or init_keyword in item_desc for init_keyword in initiative_items):
                        # Check if this item is new or changed
                        old_item = next((old for old in old_equipment 
                                       if isinstance(old, dict) and old.get('name') == item.get('name')), None)
                        
                        if not old_item or old_item != item:
                            return {
                                'item_name': item.get('name', 'Unknown Item'),
                                'old_bonus': 0,
                                'new_bonus': extract_initiative_bonus_from_item_data(item),
                                'bonus_change': extract_initiative_bonus_from_item_data(item)
                            }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error detecting equipment initiative bonus change: {e}")
            return None
    
    def _detect_feat_initiative_bonus_change(self, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect feat changes that affect initiative."""
        try:
            old_feats = extract_feats_data(old_data)
            new_feats = extract_feats_data(new_data)
            
            # Feats that affect initiative
            initiative_feats = {
                'alert': 5,  # +5 to initiative
                'fey touched': 0,  # Might affect through ability score increase
                'elven accuracy': 0,  # Might affect through ability score increase
            }
            
            for feat_id, feat_data in new_feats.items():
                if feat_id not in old_feats:
                    feat_name = extract_feat_name_data(feat_data).lower()
                    
                    for init_feat, bonus in initiative_feats.items():
                        if init_feat in feat_name:
                            return {
                                'feat_name': extract_feat_name_data(feat_data),
                                'old_bonus': 0,
                                'new_bonus': bonus,
                                'bonus_change': bonus
                            }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error detecting feat initiative bonus change: {e}")
            return None
    
    def _detect_class_feature_initiative_change(self, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect class feature changes that affect initiative."""
        try:
            # Some class features that affect initiative
            # Examples: Barbarian's Feral Instinct, Gloom Stalker's Dread Ambusher, etc.
            
            old_features = extract_class_features_data(old_data)
            new_features = extract_class_features_data(new_data)
            
            initiative_features = {
                'feral instinct': 0,  # Advantage on initiative, not a bonus
                'dread ambusher': 0,  # Wisdom modifier to initiative
                'jack of all trades': 0,  # Half proficiency to initiative (Bard)
            }
            
            for feature_name, feature_data in new_features.items():
                if feature_name not in old_features:
                    feature_name_lower = feature_name.lower()
                    
                    for init_feature, bonus in initiative_features.items():
                        if init_feature in feature_name_lower:
                            return {
                                'feature_name': feature_name,
                                'old_bonus': 0,
                                'new_bonus': bonus,
                                'bonus_change': bonus
                            }
            
            return None
            
        except Exception as e:
            self.logger.warning(f"Error detecting class feature initiative change: {e}")
            return None
    
    def _detect_magic_item_initiative_change(self, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect magic item changes that affect initiative."""
        try:
            # This is similar to equipment detection but specifically for magic items
            # that have initiative bonuses
            return self._detect_equipment_initiative_bonus_change(old_data, new_data)
            
        except Exception as e:
            self.logger.warning(f"Error detecting magic item initiative change: {e}")
            return None
    
    def _extract_initiative_bonus_from_item(self, item: Dict[str, Any]) -> int:
        """Extract initiative bonus from an item description."""
        try:
            description = item.get('description', '').lower()
            
            # Look for patterns like "+2 to initiative", "initiative +1", etc.
            import re
            patterns = [
                r'\+(\d+)\s+(?:bonus\s+)?to\s+initiative(?:\s+rolls?)?',
                r'initiative\s+\+(\d+)',
                r'initiative\s+bonus\s+\+(\d+)',
                r'grants?\s+a?\s*\+(\d+)\s+(?:bonus\s+)?to\s+initiative(?:\s+rolls?)?',
                r'provides?\s+initiative\s+bonus\s+\+(\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, description)
                if match:
                    return int(match.group(1))
            
            # Special cases for known items
            item_name = item.get('name', '').lower()
            if 'alert' in item_name:
                return 5
            
            return 0
            
        except Exception:
            return 0
    
    
    
    
    


class PassiveSkillsDetector(BaseEnhancedDetector):
    """Enhanced detector for passive skill changes with detailed causation attribution."""
    
    def __init__(self):
        field_mappings = {
            'passive_perception': EnhancedFieldMapping(
                api_path='character.passive_perception',
                display_name='Passive Perception',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SKILLS
            ),
            'passive_investigation': EnhancedFieldMapping(
                api_path='character.passive_investigation',
                display_name='Passive Investigation',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SKILLS
            ),
            'passive_insight': EnhancedFieldMapping(
                api_path='character.passive_insight',
                display_name='Passive Insight',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SKILLS
            )
        }
        priority_rules = {
            'character.passive_perception': ChangePriority.MEDIUM,
            'character.passive_investigation': ChangePriority.MEDIUM,
            'character.passive_insight': ChangePriority.MEDIUM
        }
        super().__init__(field_mappings, priority_rules)
        
        # Passive skill calculation constants
        self.PASSIVE_BASE = 10
        self.PASSIVE_SKILLS = {
            'perception': 'wisdom',
            'investigation': 'intelligence',
            'insight': 'wisdom'
        }
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect passive skill changes with detailed causation attribution."""
        changes = []
        
        try:
            old_passive_skills = extract_passive_skills_data(old_data)
            new_passive_skills = extract_passive_skills_data(new_data)
            
            for skill_name in self.PASSIVE_SKILLS.keys():
                old_value = old_passive_skills.get(skill_name, 0)
                new_value = new_passive_skills.get(skill_name, 0)
                
                if old_value != new_value:
                    change = self._create_enhanced_passive_skill_change(
                        skill_name=skill_name,
                        old_value=old_value,
                        new_value=new_value,
                        old_data=old_data,
                        new_data=new_data,
                        context=context
                    )
                    changes.append(change)
            
            self.logger.debug(f"Detected {len(changes)} passive skill changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting passive skill changes: {e}", exc_info=True)
        
        return changes
    
    def _create_enhanced_passive_skill_change(self, skill_name: str, old_value: int, new_value: int,
                                            old_data: Dict, new_data: Dict, 
                                            context: DetectionContext) -> FieldChange:
        """Create an enhanced passive skill change with detailed causation attribution."""
        field_path = f'character.passive_{skill_name}'
        
        # Determine change type
        if new_value > old_value:
            change_type = ChangeType.INCREMENTED
            description = f"Passive {skill_name.title()} increased by +{new_value - old_value} (from {old_value} to {new_value})"
        else:
            change_type = ChangeType.DECREMENTED
            description = f"Passive {skill_name.title()} decreased by {new_value - old_value} (from {old_value} to {new_value})"
        
        # Analyze causation
        causation_info = self._analyze_passive_skill_causation(
            skill_name, old_value, new_value, old_data, new_data
        )
        
        # Create detailed description
        detailed_description = self._create_passive_skill_detailed_description(
            skill_name, old_value, new_value, causation_info
        )
        
        # Create the field change
        change = self._create_field_change(
            field_path=field_path,
            old_value=old_value,
            new_value=new_value,
            change_type=change_type,
            category=ChangeCategory.SKILLS,
            description=description
        )
        
        # Add enhanced metadata
        change.metadata.update({
            'skill_name': skill_name,
            'causation_analysis': causation_info,
            'detailed_description': detailed_description,
            'passive_skill_breakdown': self._create_passive_skill_breakdown(skill_name, new_data, causation_info)
        })
        
        return change
    
    def _analyze_passive_skill_causation(self, skill_name: str, old_value: int, new_value: int,
                                       old_data: Dict, new_data: Dict) -> Dict[str, Any]:
        """Analyze what caused the passive skill change."""
        causation_info = {
            'primary_cause': 'Unknown',
            'contributing_factors': [],
            'confidence': 0.5
        }
        
        try:
            ability_name = self.PASSIVE_SKILLS[skill_name]
            
            # Check for ability score changes
            ability_change = self._detect_ability_score_change(ability_name, old_data, new_data)
            if ability_change:
                causation_info['ability_score_change'] = ability_change
                causation_info['contributing_factors'].append('ability_score_change')
                causation_info['primary_cause'] = f'{ability_name.title()} modifier change'
                causation_info['confidence'] = 0.9
            
            # Check for proficiency changes
            proficiency_change = self._detect_skill_proficiency_change(skill_name, old_data, new_data)
            if proficiency_change:
                causation_info['proficiency_change'] = proficiency_change
                causation_info['contributing_factors'].append('proficiency_change')
                if causation_info['primary_cause'] == 'Unknown':
                    causation_info['primary_cause'] = f'{skill_name.title()} proficiency gained'
                    causation_info['confidence'] = 0.8
            
            # Check for expertise changes
            expertise_change = self._detect_skill_expertise_change(skill_name, old_data, new_data)
            if expertise_change:
                causation_info['expertise_change'] = expertise_change
                causation_info['contributing_factors'].append('expertise_change')
                if causation_info['primary_cause'] == 'Unknown':
                    causation_info['primary_cause'] = f'{skill_name.title()} expertise gained'
                    causation_info['confidence'] = 0.8
            
            # Check for feat-based bonuses
            feat_change = self._detect_feat_passive_skill_bonus_change(skill_name, old_data, new_data)
            if feat_change:
                causation_info['feat_bonus_change'] = feat_change
                causation_info['contributing_factors'].append('feat_bonus_change')
                if causation_info['primary_cause'] == 'Unknown':
                    causation_info['primary_cause'] = f'{feat_change["feat_name"]} feat bonus'
                    causation_info['confidence'] = 0.7
            
            # Check for equipment bonuses
            equipment_change = self._detect_equipment_passive_skill_bonus_change(skill_name, old_data, new_data)
            if equipment_change:
                causation_info['equipment_bonus_change'] = equipment_change
                causation_info['contributing_factors'].append('equipment_bonus_change')
                if causation_info['primary_cause'] == 'Unknown':
                    causation_info['primary_cause'] = f'{equipment_change["item_name"]} equipment bonus'
                    causation_info['confidence'] = 0.6
            
            # Check for level progression effects
            level_change = self._detect_level_progression_passive_skill_effect(skill_name, old_data, new_data)
            if level_change:
                causation_info['level_progression_change'] = level_change
                causation_info['contributing_factors'].append('level_progression_change')
                if causation_info['primary_cause'] == 'Unknown':
                    causation_info['primary_cause'] = 'Level progression'
                    causation_info['confidence'] = 0.7
            
        except Exception as e:
            self.logger.error(f"Error analyzing passive skill causation for {skill_name}: {e}")
        
        return causation_info
    
    def _detect_ability_score_change(self, ability_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect ability score changes that affect passive skills."""
        try:
            old_abilities = extract_ability_scores_data(old_data)
            new_abilities = extract_ability_scores_data(new_data)
            
            old_score = old_abilities.get(ability_name, 10)
            new_score = new_abilities.get(ability_name, 10)
            
            if old_score != new_score:
                old_modifier = (old_score - 10) // 2
                new_modifier = (new_score - 10) // 2
                
                return {
                    'ability_name': ability_name,
                    'old_score': old_score,
                    'new_score': new_score,
                    'old_modifier': old_modifier,
                    'new_modifier': new_modifier,
                    'modifier_change': new_modifier - old_modifier
                }
        except Exception as e:
            self.logger.error(f"Error detecting ability score change for {ability_name}: {e}")
        
        return None
    
    def _detect_skill_proficiency_change(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect skill proficiency changes that affect passive skills."""
        try:
            old_proficiencies = extract_skill_proficiencies_list(old_data)
            new_proficiencies = extract_skill_proficiencies_list(new_data)
            
            old_proficient = skill_name in old_proficiencies
            new_proficient = skill_name in new_proficiencies
            
            if old_proficient != new_proficient:
                proficiency_bonus = self._calculate_proficiency_bonus(new_data)
                
                return {
                    'skill_name': skill_name,
                    'gained_proficiency': new_proficient,
                    'proficiency_bonus': proficiency_bonus,
                    'bonus_change': proficiency_bonus if new_proficient else -proficiency_bonus
                }
        except Exception as e:
            self.logger.error(f"Error detecting skill proficiency change for {skill_name}: {e}")
        
        return None
    
    def _detect_skill_expertise_change(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect skill expertise changes that affect passive skills."""
        try:
            old_expertise = extract_skill_proficiencies_data(old_data)
            new_expertise = extract_skill_proficiencies_data(new_data)
            
            old_has_expertise = skill_name in old_expertise
            new_has_expertise = skill_name in new_expertise
            
            if old_has_expertise != new_has_expertise:
                proficiency_bonus = self._calculate_proficiency_bonus(new_data)
                
                return {
                    'skill_name': skill_name,
                    'gained_expertise': new_has_expertise,
                    'proficiency_bonus': proficiency_bonus,
                    'bonus_change': proficiency_bonus if new_has_expertise else -proficiency_bonus
                }
        except Exception as e:
            self.logger.error(f"Error detecting skill expertise change for {skill_name}: {e}")
        
        return None
    
    def _detect_feat_passive_skill_bonus_change(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect feat-based passive skill bonus changes."""
        try:
            old_feats = extract_feats_data(old_data)
            new_feats = extract_feats_data(new_data)
            
            # Check for feats that provide passive skill bonuses
            passive_skill_feats = {
                'observant': {'perception': 5, 'investigation': 5},
                'keen mind': {'investigation': 5},
                'alert': {'perception': 5}
            }
            
            for feat_name, skill_bonuses in passive_skill_feats.items():
                if skill_name in skill_bonuses:
                    old_has_feat = any(feat.get('name', '').lower() == feat_name for feat in old_feats.values())
                    new_has_feat = any(feat.get('name', '').lower() == feat_name for feat in new_feats.values())
                    
                    if old_has_feat != new_has_feat:
                        bonus = skill_bonuses[skill_name]
                        return {
                            'feat_name': feat_name.title(),
                            'skill_name': skill_name,
                            'gained_feat': new_has_feat,
                            'bonus_change': bonus if new_has_feat else -bonus
                        }
        except Exception as e:
            self.logger.error(f"Error detecting feat passive skill bonus change for {skill_name}: {e}")
        
        return None
    
    def _detect_equipment_passive_skill_bonus_change(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect equipment-based passive skill bonus changes."""
        try:
            old_equipment = extract_equipment_data(old_data)
            new_equipment = extract_equipment_data(new_data)
            
            old_bonus = self._calculate_equipment_passive_skill_bonus(skill_name, old_equipment)
            new_bonus = self._calculate_equipment_passive_skill_bonus(skill_name, new_equipment)
            
            if old_bonus != new_bonus:
                # Find the specific item that changed
                changed_item = self._find_changed_passive_skill_item(skill_name, old_equipment, new_equipment)
                
                return {
                    'skill_name': skill_name,
                    'item_name': changed_item.get('name', 'Unknown Item') if changed_item else 'Unknown Item',
                    'old_bonus': old_bonus,
                    'new_bonus': new_bonus,
                    'bonus_change': new_bonus - old_bonus
                }
        except Exception as e:
            self.logger.error(f"Error detecting equipment passive skill bonus change for {skill_name}: {e}")
        
        return None
    
    def _detect_level_progression_passive_skill_effect(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect level progression effects on passive skills."""
        try:
            old_level = extract_character_level_data(old_data)
            new_level = extract_character_level_data(new_data)
            
            if new_level > old_level:
                old_proficiency_bonus = self._calculate_proficiency_bonus_for_level(old_level)
                new_proficiency_bonus = self._calculate_proficiency_bonus_for_level(new_level)
                
                if old_proficiency_bonus != new_proficiency_bonus:
                    # Check if character is proficient in this skill
                    proficiencies = extract_skill_proficiencies_list(new_data)
                    expertise = extract_skill_proficiencies_data(new_data)
                    
                    if skill_name in proficiencies:
                        multiplier = 2 if skill_name in expertise else 1
                        bonus_change = (new_proficiency_bonus - old_proficiency_bonus) * multiplier
                        
                        return {
                            'old_level': old_level,
                            'new_level': new_level,
                            'old_proficiency_bonus': old_proficiency_bonus,
                            'new_proficiency_bonus': new_proficiency_bonus,
                            'has_proficiency': True,
                            'has_expertise': skill_name in expertise,
                            'bonus_change': bonus_change
                        }
        except Exception as e:
            self.logger.error(f"Error detecting level progression passive skill effect for {skill_name}: {e}")
        
        return None
    
    def _create_passive_skill_detailed_description(self, skill_name: str, old_value: int, new_value: int,
                                                 causation_info: Dict[str, Any]) -> str:
        """Create detailed description for passive skill change."""
        description = f"Passive {skill_name.title()} changed from {old_value} to {new_value}"
        
        if causation_info['primary_cause'] != 'Unknown':
            description += f" due to {causation_info['primary_cause']}"
        
        # Add specific details based on causation
        details = []
        
        if 'ability_score_change' in causation_info:
            ability_change = causation_info['ability_score_change']
            details.append(f"{ability_change['ability_name'].title()} modifier changed from "
                         f"+{ability_change['old_modifier']} to +{ability_change['new_modifier']}")
        
        if 'proficiency_change' in causation_info:
            prof_change = causation_info['proficiency_change']
            if prof_change['gained_proficiency']:
                details.append(f"Gained proficiency in {skill_name.title()} (+{prof_change['proficiency_bonus']})")
            else:
                details.append(f"Lost proficiency in {skill_name.title()} (-{prof_change['proficiency_bonus']})")
        
        if 'expertise_change' in causation_info:
            exp_change = causation_info['expertise_change']
            if exp_change['gained_expertise']:
                details.append(f"Gained expertise in {skill_name.title()} (additional +{exp_change['proficiency_bonus']})")
            else:
                details.append(f"Lost expertise in {skill_name.title()} (-{exp_change['proficiency_bonus']})")
        
        if 'feat_bonus_change' in causation_info:
            feat_change = causation_info['feat_bonus_change']
            if feat_change['gained_feat']:
                details.append(f"{feat_change['feat_name']} feat provides +{feat_change['bonus_change']} bonus")
            else:
                details.append(f"Lost {feat_change['feat_name']} feat bonus ({feat_change['bonus_change']})")
        
        if 'equipment_bonus_change' in causation_info:
            eq_change = causation_info['equipment_bonus_change']
            details.append(f"{eq_change['item_name']} provides {eq_change['bonus_change']:+d} bonus")
        
        if 'level_progression_change' in causation_info:
            level_change = causation_info['level_progression_change']
            details.append(f"Proficiency bonus increased from +{level_change['old_proficiency_bonus']} "
                         f"to +{level_change['new_proficiency_bonus']} (level {level_change['new_level']})")
        
        if details:
            description += ". " + "; ".join(details) + "."
        
        return description
    
    def _create_passive_skill_breakdown(self, skill_name: str, character_data: Dict, 
                                      causation_info: Dict[str, Any]) -> str:
        """Create a breakdown of passive skill calculation."""
        ability_name = self.PASSIVE_SKILLS[skill_name]
        ability_scores = extract_ability_scores_data(character_data)
        ability_modifier = (ability_scores.get(ability_name, 10) - 10) // 2
        
        breakdown_parts = [f"{self.PASSIVE_BASE} (base)"]
        breakdown_parts.append(f"{ability_modifier:+d} ({ability_name.title()[:3]})")
        
        # Add proficiency bonus if applicable
        proficiencies = extract_skill_proficiencies_list(character_data)
        expertise = extract_skill_proficiencies_data(character_data)
        
        if skill_name in proficiencies:
            proficiency_bonus = self._calculate_proficiency_bonus(character_data)
            if skill_name in expertise:
                breakdown_parts.append(f"{proficiency_bonus * 2:+d} (expertise)")
            else:
                breakdown_parts.append(f"{proficiency_bonus:+d} (proficiency)")
        
        # Add feat bonuses
        if 'feat_bonus_change' in causation_info:
            feat_change = causation_info['feat_bonus_change']
            if feat_change['gained_feat']:
                breakdown_parts.append(f"{feat_change['bonus_change']:+d} ({feat_change['feat_name']})")
        
        # Add equipment bonuses
        if 'equipment_bonus_change' in causation_info:
            eq_change = causation_info['equipment_bonus_change']
            if eq_change['bonus_change'] != 0:
                breakdown_parts.append(f"{eq_change['bonus_change']:+d} ({eq_change['item_name']})")
        
        return " ".join(breakdown_parts)
    
    def _extract_passive_skills(self, character_data: Dict) -> Dict[str, int]:
        """Extract passive skill values from character data."""
        passive_skills = {}
        
        try:
            # Try to extract directly from character data
            character = character_data.get('character', {})
            
            for skill_name in self.PASSIVE_SKILLS.keys():
                # Try direct extraction first
                passive_value = character.get(f'passive_{skill_name}')
                
                if passive_value is not None:
                    passive_skills[skill_name] = int(passive_value)
                else:
                    # Calculate passive skill if not directly available
                    passive_skills[skill_name] = self._calculate_passive_skill(skill_name, character_data)
        
        except Exception as e:
            self.logger.error(f"Error extracting passive skills: {e}")
            # Return calculated values as fallback
            for skill_name in self.PASSIVE_SKILLS.keys():
                passive_skills[skill_name] = self._calculate_passive_skill(skill_name, character_data)
        
        return passive_skills
    
    def _calculate_passive_skill(self, skill_name: str, character_data: Dict) -> int:
        """Calculate passive skill value from character data."""
        try:
            ability_name = self.PASSIVE_SKILLS[skill_name]
            
            # Get ability modifier
            ability_scores = extract_ability_scores_data(character_data)
            ability_score = ability_scores.get(ability_name, 10)
            ability_modifier = (ability_score - 10) // 2
            
            # Start with base + ability modifier
            passive_value = self.PASSIVE_BASE + ability_modifier
            
            # Add proficiency bonus if proficient
            proficiencies = extract_skill_proficiencies_list(character_data)
            if skill_name in proficiencies:
                proficiency_bonus = self._calculate_proficiency_bonus(character_data)
                passive_value += proficiency_bonus
                
                # Double proficiency bonus if expertise
                expertise = extract_skill_proficiencies_data(character_data)
                if skill_name in expertise:
                    passive_value += proficiency_bonus
            
            # Add feat bonuses
            passive_value += self._calculate_feat_passive_skill_bonus(skill_name, character_data)
            
            # Add equipment bonuses
            equipment = extract_equipment_data(character_data)
            passive_value += self._calculate_equipment_passive_skill_bonus(skill_name, equipment)
            
            return passive_value
            
        except Exception as e:
            self.logger.error(f"Error calculating passive {skill_name}: {e}")
            return 10  # Default passive value
    
    def _calculate_feat_passive_skill_bonus(self, skill_name: str, character_data: Dict) -> int:
        """Calculate feat-based passive skill bonuses."""
        try:
            feats = extract_feats_data(character_data)
            
            # Feat bonuses for passive skills
            passive_skill_feats = {
                'observant': {'perception': 5, 'investigation': 5},
                'keen mind': {'investigation': 5},
                'alert': {'perception': 5}
            }
            
            total_bonus = 0
            for feat_name, skill_bonuses in passive_skill_feats.items():
                if skill_name in skill_bonuses:
                    has_feat = any(feat.get('name', '').lower() == feat_name for feat in feats.values())
                    if has_feat:
                        total_bonus += skill_bonuses[skill_name]
            
            return total_bonus
            
        except Exception as e:
            self.logger.error(f"Error calculating feat passive skill bonus for {skill_name}: {e}")
            return 0
    
    def _calculate_equipment_passive_skill_bonus(self, skill_name: str, equipment: List[Dict]) -> int:
        """Calculate equipment-based passive skill bonuses."""
        try:
            total_bonus = 0
            
            for item in equipment:
                item_bonus = extract_passive_skill_bonus_from_item_data(skill_name, item)
                total_bonus += item_bonus
            
            return total_bonus
            
        except Exception as e:
            self.logger.error(f"Error calculating equipment passive skill bonus for {skill_name}: {e}")
            return 0
    
    def _extract_passive_skill_bonus_from_item(self, skill_name: str, item: Dict) -> int:
        """Extract passive skill bonus from item description."""
        try:
            description = item.get('description', '').lower()
            name = item.get('name', '').lower()
            
            # Look for passive skill bonuses in description
            import re
            
            # Pattern for "passive perception +X" or "passive perception bonus +X"
            pattern = rf'passive\s+{skill_name}\s+(?:bonus\s+)?([+-]?\d+)'
            match = re.search(pattern, description)
            if match:
                return int(match.group(1))
            
            # Pattern for "+X to passive perception"
            pattern = rf'([+-]?\d+)\s+to\s+passive\s+{skill_name}'
            match = re.search(pattern, description)
            if match:
                return int(match.group(1))
            
            # Special items
            if 'eyes of the eagle' in name and skill_name == 'perception':
                return 5
            elif 'sentinel shield' in name and skill_name == 'perception':
                return 5
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error extracting passive skill bonus from item: {e}")
            return 0
    
    def _find_changed_passive_skill_item(self, skill_name: str, old_equipment: List[Dict], 
                                       new_equipment: List[Dict]) -> Optional[Dict]:
        """Find the specific item that changed passive skill bonus."""
        try:
            old_items = {item.get('name', ''): item for item in old_equipment}
            new_items = {item.get('name', ''): item for item in new_equipment}
            
            # Check for new items
            for name, item in new_items.items():
                if name not in old_items:
                    bonus = extract_passive_skill_bonus_from_item_data(skill_name, item)
                    if bonus != 0:
                        return item
            
            # Check for removed items
            for name, item in old_items.items():
                if name not in new_items:
                    bonus = extract_passive_skill_bonus_from_item_data(skill_name, item)
                    if bonus != 0:
                        return item
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding changed passive skill item: {e}")
            return None
    
    
    def _extract_skill_expertise(self, character_data: Dict) -> List[str]:
        """Extract skill expertise from character data."""
        try:
            character = character_data.get('character', {})
            
            # Try different possible paths for expertise
            if 'expertise' in character:
                expertise = character['expertise']
                if isinstance(expertise, list):
                    return expertise
                elif isinstance(expertise, dict):
                    return [skill for skill, has_expertise in expertise.items() if has_expertise]
            
            # Check in proficiencies section
            proficiencies = character.get('proficiencies', {})
            if 'expertise' in proficiencies:
                expertise = proficiencies['expertise']
                if isinstance(expertise, list):
                    return expertise
                elif isinstance(expertise, dict):
                    return [skill for skill, has_expertise in expertise.items() if has_expertise]
            
            return []
        except Exception:
            return []
    
    def _calculate_proficiency_bonus(self, character_data: Dict) -> int:
        """Calculate proficiency bonus from character data."""
        try:
            # Try character_info.proficiency_bonus first (actual data structure)
            if 'character_info' in character_data and 'proficiency_bonus' in character_data['character_info']:
                return character_data['character_info']['proficiency_bonus']
            
            character = character_data.get('character', {})
            
            # Try direct extraction first
            if 'proficiency_bonus' in character:
                return int(character['proficiency_bonus'])
            
            # Calculate from level
            level = extract_character_level_data(character_data)
            return self._calculate_proficiency_bonus_for_level(level)
            
        except Exception:
            return 2  # Default proficiency bonus
    
    def _calculate_proficiency_bonus_for_level(self, level: int) -> int:
        """Calculate proficiency bonus for a given level."""
        if level >= 17:
            return 6
        elif level >= 13:
            return 5
        elif level >= 9:
            return 4
        elif level >= 5:
            return 3
        else:
            return 2
    


class PassiveSkillsDetector(BaseEnhancedDetector):
    """Enhanced detector for passive skill changes with detailed causation attribution."""
    
    def __init__(self):
        field_mappings = {
            'passive_perception': EnhancedFieldMapping(
                api_path='character.passive_perception',
                display_name='Passive Perception',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SKILLS
            ),
            'passive_investigation': EnhancedFieldMapping(
                api_path='character.passive_investigation',
                display_name='Passive Investigation',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SKILLS
            ),
            'passive_insight': EnhancedFieldMapping(
                api_path='character.passive_insight',
                display_name='Passive Insight',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SKILLS
            )
        }
        priority_rules = {
            'character.passive_perception': ChangePriority.MEDIUM,
            'character.passive_investigation': ChangePriority.MEDIUM,
            'character.passive_insight': ChangePriority.MEDIUM
        }
        super().__init__(field_mappings, priority_rules)
        
        # Passive skill calculation constants
        self.PASSIVE_BASE = 10
        self.PASSIVE_SKILLS = {
            'perception': 'wisdom',
            'investigation': 'intelligence',
            'insight': 'wisdom'
        }
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect passive skill changes with detailed causation attribution."""
        changes = []
        
        try:
            old_passive_skills = extract_passive_skills_data(old_data)
            new_passive_skills = extract_passive_skills_data(new_data)
            
            for skill_name in self.PASSIVE_SKILLS.keys():
                old_value = old_passive_skills.get(skill_name, 0)
                new_value = new_passive_skills.get(skill_name, 0)
                
                if old_value != new_value:
                    change = self._create_enhanced_passive_skill_change(
                        skill_name=skill_name,
                        old_value=old_value,
                        new_value=new_value,
                        old_data=old_data,
                        new_data=new_data,
                        context=context
                    )
                    changes.append(change)
            
            self.logger.debug(f"Detected {len(changes)} passive skill changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting passive skill changes: {e}", exc_info=True)
        
        return changes
    
    def _create_enhanced_passive_skill_change(self, skill_name: str, old_value: int, new_value: int,
                                            old_data: Dict, new_data: Dict, 
                                            context: DetectionContext) -> FieldChange:
        """Create an enhanced passive skill change with detailed causation attribution."""
        field_path = f'character.passive_{skill_name}'
        
        # Determine change type
        if new_value > old_value:
            change_type = ChangeType.INCREMENTED
            description = f"Passive {skill_name.title()} increased by +{new_value - old_value} (from {old_value} to {new_value})"
        else:
            change_type = ChangeType.DECREMENTED
            description = f"Passive {skill_name.title()} decreased by {new_value - old_value} (from {old_value} to {new_value})"
        
        # Analyze causation
        causation_info = self._analyze_passive_skill_causation(
            skill_name, old_value, new_value, old_data, new_data
        )
        
        # Add primary cause to description if identified
        if causation_info.get('primary_cause') and causation_info['primary_cause'] != 'Unknown':
            description += f" - {causation_info['primary_cause']}"
        
        # Create detailed description
        detailed_description = self._create_passive_skill_detailed_description(
            skill_name, old_value, new_value, causation_info
        )
        
        # Create the field change
        change = self._create_field_change(
            field_path=field_path,
            old_value=old_value,
            new_value=new_value,
            change_type=change_type,
            category=ChangeCategory.SKILLS,
            description=description
        )
        
        # Add enhanced metadata
        change.metadata.update({
            'skill_name': skill_name,
            'causation_analysis': causation_info,
            'detailed_description': detailed_description,
            'passive_skill_breakdown': self._create_passive_skill_breakdown(skill_name, new_data, causation_info)
        })
        
        return change
    
    def _analyze_passive_skill_causation(self, skill_name: str, old_value: int, new_value: int,
                                       old_data: Dict, new_data: Dict) -> Dict[str, Any]:
        """Analyze what caused the passive skill change."""
        causation_info = {
            'primary_cause': 'Unknown',
            'contributing_factors': [],
            'confidence': 0.5
        }
        
        try:
            ability_name = self.PASSIVE_SKILLS[skill_name]
            
            # Check for ability score changes
            ability_change = self._detect_ability_score_change(ability_name, old_data, new_data)
            if ability_change:
                causation_info['ability_score_change'] = ability_change
                causation_info['contributing_factors'].append('ability_score_change')
                causation_info['primary_cause'] = f'{ability_name.title()} modifier change'
                causation_info['confidence'] = 0.9
            
            # Check for proficiency changes
            proficiency_change = self._detect_skill_proficiency_change(skill_name, old_data, new_data)
            if proficiency_change:
                causation_info['proficiency_change'] = proficiency_change
                causation_info['contributing_factors'].append('proficiency_change')
                if causation_info['primary_cause'] == 'Unknown':
                    causation_info['primary_cause'] = f'{skill_name.title()} proficiency gained'
                    causation_info['confidence'] = 0.8
            
            # Check for expertise changes
            expertise_change = self._detect_skill_expertise_change(skill_name, old_data, new_data)
            if expertise_change:
                causation_info['expertise_change'] = expertise_change
                causation_info['contributing_factors'].append('expertise_change')
                if causation_info['primary_cause'] == 'Unknown':
                    causation_info['primary_cause'] = f'{skill_name.title()} expertise gained'
                    causation_info['confidence'] = 0.8
            
            # Check for feat-based bonuses
            feat_change = self._detect_feat_passive_skill_bonus_change(skill_name, old_data, new_data)
            if feat_change:
                causation_info['feat_bonus_change'] = feat_change
                causation_info['contributing_factors'].append('feat_bonus_change')
                if causation_info['primary_cause'] == 'Unknown':
                    causation_info['primary_cause'] = f'{feat_change["feat_name"]} feat bonus'
                    causation_info['confidence'] = 0.7
            
            # Check for equipment bonuses
            equipment_change = self._detect_equipment_passive_skill_bonus_change(skill_name, old_data, new_data)
            if equipment_change:
                causation_info['equipment_bonus_change'] = equipment_change
                causation_info['contributing_factors'].append('equipment_bonus_change')
                if causation_info['primary_cause'] == 'Unknown':
                    causation_info['primary_cause'] = f'{equipment_change["item_name"]} equipment bonus'
                    causation_info['confidence'] = 0.6
            
            # Check for level progression effects
            level_change = self._detect_level_progression_passive_skill_effect(skill_name, old_data, new_data)
            if level_change:
                causation_info['level_progression_change'] = level_change
                causation_info['contributing_factors'].append('level_progression_change')
                if causation_info['primary_cause'] == 'Unknown':
                    causation_info['primary_cause'] = 'Level progression'
                    causation_info['confidence'] = 0.7
            
        except Exception as e:
            self.logger.error(f"Error analyzing passive skill causation for {skill_name}: {e}")
        
        return causation_info
    
    def _detect_ability_score_change(self, ability_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect ability score changes that affect passive skills."""
        try:
            old_abilities = extract_ability_scores_data(old_data)
            new_abilities = extract_ability_scores_data(new_data)
            
            old_score = old_abilities.get(ability_name, 10)
            new_score = new_abilities.get(ability_name, 10)
            
            if old_score != new_score:
                old_modifier = (old_score - 10) // 2
                new_modifier = (new_score - 10) // 2
                
                return {
                    'ability_name': ability_name,
                    'old_score': old_score,
                    'new_score': new_score,
                    'old_modifier': old_modifier,
                    'new_modifier': new_modifier,
                    'modifier_change': new_modifier - old_modifier
                }
        except Exception as e:
            self.logger.error(f"Error detecting ability score change for {ability_name}: {e}")
        
        return None
    
    def _detect_skill_proficiency_change(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect skill proficiency changes that affect passive skills."""
        try:
            old_proficiencies = extract_skill_proficiencies_list(old_data)
            new_proficiencies = extract_skill_proficiencies_list(new_data)
            
            old_proficient = skill_name in old_proficiencies
            new_proficient = skill_name in new_proficiencies
            
            if old_proficient != new_proficient:
                proficiency_bonus = self._calculate_proficiency_bonus(new_data)
                
                return {
                    'skill_name': skill_name,
                    'gained_proficiency': new_proficient,
                    'proficiency_bonus': proficiency_bonus,
                    'bonus_change': proficiency_bonus if new_proficient else -proficiency_bonus
                }
        except Exception as e:
            self.logger.error(f"Error detecting skill proficiency change for {skill_name}: {e}")
        
        return None
    
    def _detect_skill_expertise_change(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect skill expertise changes that affect passive skills."""
        try:
            old_expertise = extract_skill_proficiencies_data(old_data)
            new_expertise = extract_skill_proficiencies_data(new_data)
            
            old_has_expertise = skill_name in old_expertise
            new_has_expertise = skill_name in new_expertise
            
            if old_has_expertise != new_has_expertise:
                proficiency_bonus = self._calculate_proficiency_bonus(new_data)
                
                return {
                    'skill_name': skill_name,
                    'gained_expertise': new_has_expertise,
                    'proficiency_bonus': proficiency_bonus,
                    'bonus_change': proficiency_bonus if new_has_expertise else -proficiency_bonus
                }
        except Exception as e:
            self.logger.error(f"Error detecting skill expertise change for {skill_name}: {e}")
        
        return None
    
    def _detect_feat_passive_skill_bonus_change(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect feat-based passive skill bonus changes."""
        try:
            old_feats = extract_feats_data(old_data)
            new_feats = extract_feats_data(new_data)
            
            # Check for feats that provide passive skill bonuses
            passive_skill_feats = {
                'observant': {'perception': 5, 'investigation': 5},
                'keen mind': {'investigation': 5},
                'alert': {'perception': 5}
            }
            
            for feat_name, skill_bonuses in passive_skill_feats.items():
                if skill_name in skill_bonuses:
                    old_has_feat = any(feat.get('name', '').lower() == feat_name for feat in old_feats.values())
                    new_has_feat = any(feat.get('name', '').lower() == feat_name for feat in new_feats.values())
                    
                    if old_has_feat != new_has_feat:
                        bonus = skill_bonuses[skill_name]
                        return {
                            'feat_name': feat_name.title(),
                            'skill_name': skill_name,
                            'gained_feat': new_has_feat,
                            'bonus_change': bonus if new_has_feat else -bonus
                        }
        except Exception as e:
            self.logger.error(f"Error detecting feat passive skill bonus change for {skill_name}: {e}")
        
        return None
    
    def _detect_equipment_passive_skill_bonus_change(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect equipment-based passive skill bonus changes."""
        try:
            old_equipment = extract_equipment_data(old_data)
            new_equipment = extract_equipment_data(new_data)
            
            old_bonus = self._calculate_equipment_passive_skill_bonus(skill_name, old_equipment)
            new_bonus = self._calculate_equipment_passive_skill_bonus(skill_name, new_equipment)
            
            if old_bonus != new_bonus:
                # Find the specific item that changed
                changed_item = self._find_changed_passive_skill_item(skill_name, old_equipment, new_equipment)
                
                return {
                    'skill_name': skill_name,
                    'item_name': changed_item.get('name', 'Unknown Item') if changed_item else 'Unknown Item',
                    'old_bonus': old_bonus,
                    'new_bonus': new_bonus,
                    'bonus_change': new_bonus - old_bonus
                }
        except Exception as e:
            self.logger.error(f"Error detecting equipment passive skill bonus change for {skill_name}: {e}")
        
        return None
    
    def _detect_level_progression_passive_skill_effect(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict[str, Any]]:
        """Detect level progression effects on passive skills."""
        try:
            old_level = extract_character_level_data(old_data)
            new_level = extract_character_level_data(new_data)
            
            if new_level > old_level:
                old_proficiency_bonus = self._calculate_proficiency_bonus_for_level(old_level)
                new_proficiency_bonus = self._calculate_proficiency_bonus_for_level(new_level)
                
                if old_proficiency_bonus != new_proficiency_bonus:
                    # Check if character is proficient in this skill
                    proficiencies = extract_skill_proficiencies_list(new_data)
                    expertise = extract_skill_proficiencies_data(new_data)
                    
                    if skill_name in proficiencies:
                        multiplier = 2 if skill_name in expertise else 1
                        bonus_change = (new_proficiency_bonus - old_proficiency_bonus) * multiplier
                        
                        return {
                            'old_level': old_level,
                            'new_level': new_level,
                            'old_proficiency_bonus': old_proficiency_bonus,
                            'new_proficiency_bonus': new_proficiency_bonus,
                            'has_proficiency': True,
                            'has_expertise': skill_name in expertise,
                            'bonus_change': bonus_change
                        }
        except Exception as e:
            self.logger.error(f"Error detecting level progression passive skill effect for {skill_name}: {e}")
        
        return None
    
    def _create_passive_skill_detailed_description(self, skill_name: str, old_value: int, new_value: int,
                                                 causation_info: Dict[str, Any]) -> str:
        """Create detailed description for passive skill change."""
        description = f"Passive {skill_name.title()} changed from {old_value} to {new_value}"
        
        if causation_info['primary_cause'] != 'Unknown':
            description += f" due to {causation_info['primary_cause']}"
        
        # Add specific details based on causation
        details = []
        
        if 'ability_score_change' in causation_info:
            ability_change = causation_info['ability_score_change']
            details.append(f"{ability_change['ability_name'].title()} modifier changed from "
                         f"{ability_change['old_modifier']:+d} to {ability_change['new_modifier']:+d}")
        
        if 'proficiency_change' in causation_info:
            prof_change = causation_info['proficiency_change']
            if prof_change['gained_proficiency']:
                details.append(f"Gained proficiency in {skill_name.title()} (+{prof_change['proficiency_bonus']})")
            else:
                details.append(f"Lost proficiency in {skill_name.title()} (-{prof_change['proficiency_bonus']})")
        
        if 'expertise_change' in causation_info:
            exp_change = causation_info['expertise_change']
            if exp_change['gained_expertise']:
                details.append(f"Gained expertise in {skill_name.title()} (additional +{exp_change['proficiency_bonus']})")
            else:
                details.append(f"Lost expertise in {skill_name.title()} (-{exp_change['proficiency_bonus']})")
        
        if 'feat_bonus_change' in causation_info:
            feat_change = causation_info['feat_bonus_change']
            if feat_change['gained_feat']:
                details.append(f"{feat_change['feat_name']} feat provides +{feat_change['bonus_change']} bonus")
            else:
                details.append(f"Lost {feat_change['feat_name']} feat bonus ({feat_change['bonus_change']})")
        
        if 'equipment_bonus_change' in causation_info:
            eq_change = causation_info['equipment_bonus_change']
            details.append(f"{eq_change['item_name']} provides {eq_change['bonus_change']:+d} bonus")
        
        if 'level_progression_change' in causation_info:
            level_change = causation_info['level_progression_change']
            details.append(f"Proficiency bonus increased from +{level_change['old_proficiency_bonus']} "
                         f"to +{level_change['new_proficiency_bonus']} (level {level_change['new_level']})")
        
        if details:
            description += ". " + "; ".join(details) + "."
        
        return description
    
    def _create_passive_skill_breakdown(self, skill_name: str, character_data: Dict, 
                                      causation_info: Dict[str, Any]) -> str:
        """Create a breakdown of passive skill calculation."""
        ability_name = self.PASSIVE_SKILLS[skill_name]
        ability_scores = extract_ability_scores_data(character_data)
        ability_modifier = (ability_scores.get(ability_name, 10) - 10) // 2
        
        breakdown_parts = [f"{self.PASSIVE_BASE} (base)"]
        breakdown_parts.append(f"{ability_modifier:+d} ({ability_name.title()[:3]})")
        
        # Add proficiency bonus if applicable
        proficiencies = extract_skill_proficiencies_list(character_data)
        expertise = extract_skill_proficiencies_data(character_data)
        
        if skill_name in proficiencies:
            proficiency_bonus = self._calculate_proficiency_bonus(character_data)
            if skill_name in expertise:
                breakdown_parts.append(f"{proficiency_bonus * 2:+d} (expertise)")
            else:
                breakdown_parts.append(f"{proficiency_bonus:+d} (proficiency)")
        
        # Add feat bonuses
        if 'feat_bonus_change' in causation_info:
            feat_change = causation_info['feat_bonus_change']
            if feat_change['gained_feat']:
                breakdown_parts.append(f"{feat_change['bonus_change']:+d} ({feat_change['feat_name']})")
        
        # Add equipment bonuses
        if 'equipment_bonus_change' in causation_info:
            eq_change = causation_info['equipment_bonus_change']
            if eq_change['bonus_change'] != 0:
                breakdown_parts.append(f"{eq_change['bonus_change']:+d} ({eq_change['item_name']})")
        
        return " ".join(breakdown_parts)
    
    def _extract_passive_skills(self, character_data: Dict) -> Dict[str, int]:
        """Extract passive skill values from character data."""
        passive_skills = {}
        
        try:
            # Try to extract directly from character data
            character = character_data.get('character', {})
            
            for skill_name in self.PASSIVE_SKILLS.keys():
                # Try direct extraction first
                passive_value = character.get(f'passive_{skill_name}')
                
                if passive_value is not None:
                    passive_skills[skill_name] = int(passive_value)
                else:
                    # Calculate passive skill if not directly available
                    passive_skills[skill_name] = self._calculate_passive_skill(skill_name, character_data)
        
        except Exception as e:
            self.logger.error(f"Error extracting passive skills: {e}")
            # Return calculated values as fallback
            for skill_name in self.PASSIVE_SKILLS.keys():
                passive_skills[skill_name] = self._calculate_passive_skill(skill_name, character_data)
        
        return passive_skills
    
    def _calculate_passive_skill(self, skill_name: str, character_data: Dict) -> int:
        """Calculate passive skill value from character data."""
        try:
            ability_name = self.PASSIVE_SKILLS[skill_name]
            
            # Get ability modifier
            ability_scores = extract_ability_scores_data(character_data)
            ability_score = ability_scores.get(ability_name, 10)
            ability_modifier = (ability_score - 10) // 2
            
            # Start with base + ability modifier
            passive_value = self.PASSIVE_BASE + ability_modifier
            
            # Add proficiency bonus if proficient
            proficiencies = extract_skill_proficiencies_list(character_data)
            if skill_name in proficiencies:
                proficiency_bonus = self._calculate_proficiency_bonus(character_data)
                passive_value += proficiency_bonus
                
                # Double proficiency bonus if expertise
                expertise = extract_skill_proficiencies_data(character_data)
                if skill_name in expertise:
                    passive_value += proficiency_bonus
            
            # Add feat bonuses
            passive_value += self._calculate_feat_passive_skill_bonus(skill_name, character_data)
            
            # Add equipment bonuses
            equipment = extract_equipment_data(character_data)
            passive_value += self._calculate_equipment_passive_skill_bonus(skill_name, equipment)
            
            return passive_value
            
        except Exception as e:
            self.logger.error(f"Error calculating passive {skill_name}: {e}")
            return 10  # Default passive value
    
    def _calculate_feat_passive_skill_bonus(self, skill_name: str, character_data: Dict) -> int:
        """Calculate feat-based passive skill bonuses."""
        try:
            feats = extract_feats_data(character_data)
            
            # Feat bonuses for passive skills
            passive_skill_feats = {
                'observant': {'perception': 5, 'investigation': 5},
                'keen mind': {'investigation': 5},
                'alert': {'perception': 5}
            }
            
            total_bonus = 0
            for feat_name, skill_bonuses in passive_skill_feats.items():
                if skill_name in skill_bonuses:
                    has_feat = any(feat.get('name', '').lower() == feat_name for feat in feats.values())
                    if has_feat:
                        total_bonus += skill_bonuses[skill_name]
            
            return total_bonus
            
        except Exception as e:
            self.logger.error(f"Error calculating feat passive skill bonus for {skill_name}: {e}")
            return 0
    
    def _calculate_equipment_passive_skill_bonus(self, skill_name: str, equipment: List[Dict]) -> int:
        """Calculate equipment-based passive skill bonuses."""
        try:
            total_bonus = 0
            
            for item in equipment:
                item_bonus = extract_passive_skill_bonus_from_item_data(skill_name, item)
                total_bonus += item_bonus
            
            return total_bonus
            
        except Exception as e:
            self.logger.error(f"Error calculating equipment passive skill bonus for {skill_name}: {e}")
            return 0
    
    def _extract_passive_skill_bonus_from_item(self, skill_name: str, item: Dict) -> int:
        """Extract passive skill bonus from item description."""
        try:
            description = item.get('description', '').lower()
            name = item.get('name', '').lower()
            
            # Look for passive skill bonuses in description
            import re
            patterns = [
                rf'passive\s+{skill_name}.*?[+](\d+)',
                rf'[+](\d+).*?(?:to\s+)?passive\s+{skill_name}',
                rf'{skill_name}.*?[+](\d+)',
                rf'[+](\d+).*?{skill_name}',
                rf'[+](\d+)\s+bonus.*?passive\s+{skill_name}',
                rf'[+](\d+)\s+bonus.*?{skill_name}'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, description)
                if match:
                    return int(match.group(1))
            
            return 0
            
        except Exception as e:
            self.logger.error(f"Error extracting passive skill bonus from item: {e}")
            return 0
    
    def _find_changed_passive_skill_item(self, skill_name: str, old_equipment: List[Dict], 
                                       new_equipment: List[Dict]) -> Optional[Dict]:
        """Find the specific item that changed passive skill bonuses."""
        try:
            # Find items that were added
            old_item_names = {item.get('name', '') for item in old_equipment}
            
            for item in new_equipment:
                if item.get('name', '') not in old_item_names:
                    # Check if this item affects the passive skill
                    if extract_passive_skill_bonus_from_item_data(skill_name, item) > 0:
                        return item
            
            # Find items that were removed
            new_item_names = {item.get('name', '') for item in new_equipment}
            
            for item in old_equipment:
                if item.get('name', '') not in new_item_names:
                    # Check if this item affected the passive skill
                    if extract_passive_skill_bonus_from_item_data(skill_name, item) > 0:
                        return item
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error finding changed passive skill item: {e}")
            return None
    
    
    def _calculate_proficiency_bonus_for_level(self, level: int) -> int:
        """Calculate proficiency bonus for a specific level."""
        return 2 + ((level - 1) // 4)
    
    
    def _extract_skill_expertise(self, character_data: Dict) -> List[str]:
        """Extract skill expertise from character data."""
        try:
            character = character_data.get('character', {})
            
            # Try different possible paths
            if 'proficiencies' in character and 'expertise' in character['proficiencies']:
                return list(character['proficiencies']['expertise'].keys())
            elif 'skills' in character:
                # Filter for expertise skills
                expertise_skills = []
                for skill, skill_data in character['skills'].items():
                    if isinstance(skill_data, dict) and skill_data.get('expertise', False):
                        expertise_skills.append(skill)
                return expertise_skills
            
        except Exception as e:
            self.logger.error(f"Error extracting skill expertise: {e}")
        
        return []
    
    def _calculate_proficiency_bonus(self, character_data: Dict) -> int:
        """Calculate proficiency bonus from character level."""
        try:
            # Try character_info.proficiency_bonus first (actual data structure)
            if 'character_info' in character_data and 'proficiency_bonus' in character_data['character_info']:
                return character_data['character_info']['proficiency_bonus']
            
            character = character_data.get('character', {})
            
            # Try to get proficiency bonus directly
            if 'proficiency_bonus' in character:
                return character['proficiency_bonus']
            
            # Calculate from total level
            level = extract_character_level_data(character_data)
            return self._calculate_proficiency_bonus_for_level(level)
            
        except Exception as e:
            self.logger.error(f"Error calculating proficiency bonus: {e}")
            return 2  # Default proficiency bonus
    
    
    
    def _extract_equipment(self, character_data: Dict) -> List[Dict]:
        """Extract equipment from character data."""
        return extract_equipment_data(character_data)


class PassiveSkillsDetector(BaseEnhancedDetector):
    """Enhanced detector for passive skill changes (passive perception, investigation, etc.)."""
    
    def __init__(self):
        field_mappings = {
            'passive_perception': EnhancedFieldMapping(
                api_path='character.skills.passive_perception',
                display_name='Passive Perception',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.SKILLS
            ),
            'passive_investigation': EnhancedFieldMapping(
                api_path='character.skills.passive_investigation',
                display_name='Passive Investigation',
                priority=ChangePriority.LOW,
                category=ChangeCategory.SKILLS
            ),
            'passive_insight': EnhancedFieldMapping(
                api_path='character.skills.passive_insight',
                display_name='Passive Insight',
                priority=ChangePriority.LOW,
                category=ChangeCategory.SKILLS
            )
        }
        priority_rules = {
            'character.skills.passive_perception': ChangePriority.MEDIUM,
            'character.skills.passive_investigation': ChangePriority.LOW,
            'character.skills.passive_insight': ChangePriority.LOW,
            'character.skills.passive_*': ChangePriority.LOW
        }
        super().__init__(field_mappings, priority_rules)
        
        # Define which passive skills to track
        self.tracked_passive_skills = {
            'passive_perception': {
                'ability': 'wisdom',
                'skill': 'perception',
                'display_name': 'Passive Perception',
                'priority': ChangePriority.MEDIUM
            },
            'passive_investigation': {
                'ability': 'intelligence',
                'skill': 'investigation',
                'display_name': 'Passive Investigation',
                'priority': ChangePriority.LOW
            },
            'passive_insight': {
                'ability': 'wisdom',
                'skill': 'insight',
                'display_name': 'Passive Insight',
                'priority': ChangePriority.LOW
            },
            'passive_medicine': {
                'ability': 'wisdom',
                'skill': 'medicine',
                'display_name': 'Passive Medicine',
                'priority': ChangePriority.LOW
            },
            'passive_survival': {
                'ability': 'wisdom',
                'skill': 'survival',
                'display_name': 'Passive Survival',
                'priority': ChangePriority.LOW
            }
        }
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect passive skill changes with detailed attribution and causation."""
        changes = []
        
        try:
            old_passive_skills = extract_passive_skills_data(old_data)
            new_passive_skills = extract_passive_skills_data(new_data)
            
            # Check each tracked passive skill for changes
            for passive_skill_key, skill_config in self.tracked_passive_skills.items():
                old_value = old_passive_skills.get(passive_skill_key)
                new_value = new_passive_skills.get(passive_skill_key)
                
                if old_value != new_value and (old_value is not None or new_value is not None):
                    passive_change = self._create_passive_skill_change(
                        passive_skill_key, skill_config, old_value, new_value,
                        old_data, new_data, context
                    )
                    if passive_change:
                        changes.append(passive_change)
            
            self.logger.debug(f"Detected {len(changes)} passive skill changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting passive skill changes: {e}", exc_info=True)
        
        return changes
    
    def _create_passive_skill_change(self, passive_skill_key: str, skill_config: Dict,
                                   old_value: Any, new_value: Any,
                                   old_data: Dict, new_data: Dict,
                                   context: DetectionContext) -> Optional[FieldChange]:
        """Create passive skill change with detailed causation attribution."""
        try:
            # Analyze what caused the passive skill change
            causation_info = self._analyze_passive_skill_causation(
                passive_skill_key, skill_config, old_value, new_value, old_data, new_data
            )
            
            # Create description with causation
            skill_name = skill_config['display_name']
            if new_value is not None and old_value is not None:
                difference = new_value - old_value
                if difference > 0:
                    description = f"{skill_name} increased by +{difference} (now {new_value})"
                else:
                    description = f"{skill_name} decreased by {difference} (now {new_value})"
            elif new_value is not None:
                description = f"{skill_name} set to {new_value}"
            else:
                description = f"{skill_name} removed"
            
            # Add causation to description
            if causation_info['primary_cause']:
                description += f" due to {causation_info['primary_cause']}"
            
            change = self._create_field_change(
                field_path=f'character.skills.{passive_skill_key}',
                old_value=old_value,
                new_value=new_value,
                change_type=ChangeType.INCREMENTED if (new_value or 0) > (old_value or 0) else ChangeType.DECREMENTED,
                category=ChangeCategory.SKILLS,
                description=description
            )
            
            # Override priority from skill config
            change.priority = skill_config['priority']
            
            # Add enhanced metadata with causation details
            change.metadata.update({
                'passive_skill_type': passive_skill_key,
                'base_ability': skill_config['ability'],
                'base_skill': skill_config['skill'],
                'causation_analysis': causation_info,
                'detailed_description': self._create_detailed_passive_skill_description(
                    skill_name, old_value, new_value, causation_info
                ),
                'calculation_breakdown': self._create_passive_skill_breakdown(
                    skill_config, new_data, causation_info
                )
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error creating passive skill change for {passive_skill_key}: {e}", exc_info=True)
            return None
    
    def _analyze_passive_skill_causation(self, passive_skill_key: str, skill_config: Dict,
                                       old_value: Any, new_value: Any,
                                       old_data: Dict, new_data: Dict) -> Dict[str, Any]:
        """Analyze what caused the passive skill change."""
        causation_info = {
            'primary_cause': None,
            'contributing_factors': [],
            'ability_modifier_change': None,
            'proficiency_change': None,
            'expertise_change': None,
            'equipment_bonus_change': None,
            'feat_bonus_change': None,
            'magic_item_change': None,
            'confidence': 0.0
        }
        
        try:
            ability_name = skill_config['ability']
            skill_name = skill_config['skill']
            
            # Check for ability score changes (primary factor for passive skills)
            old_abilities = extract_ability_scores_data(old_data)
            new_abilities = extract_ability_scores_data(new_data)
            
            old_ability_score = old_abilities.get(ability_name, 10)
            new_ability_score = new_abilities.get(ability_name, 10)
            old_ability_mod = (old_ability_score - 10) // 2
            new_ability_mod = (new_ability_score - 10) // 2
            
            if old_ability_mod != new_ability_mod:
                causation_info['ability_modifier_change'] = {
                    'ability': ability_name,
                    'old_score': old_ability_score,
                    'new_score': new_ability_score,
                    'old_modifier': old_ability_mod,
                    'new_modifier': new_ability_mod,
                    'modifier_change': new_ability_mod - old_ability_mod
                }
                causation_info['primary_cause'] = f"{ability_name.title()} modifier change"
                causation_info['contributing_factors'].append('ability_score_change')
                causation_info['confidence'] = 0.9
            
            # Check for proficiency changes
            proficiency_change = self._detect_skill_proficiency_change(
                skill_name, old_data, new_data
            )
            if proficiency_change:
                causation_info['proficiency_change'] = proficiency_change
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = f"{skill_name.title()} proficiency gained"
                    causation_info['confidence'] = 0.8
                causation_info['contributing_factors'].append('proficiency_gain')
            
            # Check for expertise changes
            expertise_change = self._detect_skill_expertise_change(
                skill_name, old_data, new_data
            )
            if expertise_change:
                causation_info['expertise_change'] = expertise_change
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = f"{skill_name.title()} expertise gained"
                    causation_info['confidence'] = 0.8
                causation_info['contributing_factors'].append('expertise_gain')
            
            # Check for proficiency bonus changes (affects all proficient skills)
            proficiency_bonus_change = self._detect_proficiency_bonus_change(old_data, new_data)
            if proficiency_bonus_change and (proficiency_change or expertise_change):
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = "Proficiency bonus increase"
                    causation_info['confidence'] = 0.7
                causation_info['contributing_factors'].append('proficiency_bonus_increase')
            
            # Check for equipment bonuses (magic items, etc.)
            equipment_bonus_change = self._detect_equipment_skill_bonus_change(
                skill_name, old_data, new_data
            )
            if equipment_bonus_change:
                causation_info['equipment_bonus_change'] = equipment_bonus_change
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = f"Equipment bonus to {skill_name.title()}"
                    causation_info['confidence'] = 0.6
                causation_info['contributing_factors'].append('equipment_bonus')
            
            # Check for feat bonuses
            feat_bonus_change = self._detect_feat_skill_bonus_change(
                skill_name, old_data, new_data
            )
            if feat_bonus_change:
                causation_info['feat_bonus_change'] = feat_bonus_change
                if not causation_info['primary_cause']:
                    causation_info['primary_cause'] = f"Feat bonus to {skill_name.title()}"
                    causation_info['confidence'] = 0.7
                causation_info['contributing_factors'].append('feat_bonus')
            
            # If no specific cause found but there's a change, it might be a calculation update
            if not causation_info['primary_cause'] and old_value != new_value:
                causation_info['primary_cause'] = "Passive skill recalculation"
                causation_info['confidence'] = 0.3
                causation_info['contributing_factors'].append('calculation_update')
            
        except Exception as e:
            self.logger.error(f"Error analyzing passive skill causation for {passive_skill_key}: {e}")
        
        return causation_info
    
    def _create_detailed_passive_skill_description(self, skill_name: str, old_value: Any, 
                                                 new_value: Any, causation_info: Dict) -> str:
        """Create detailed description for passive skill change."""
        description = f"{skill_name} changed from {old_value or 'unknown'} to {new_value or 'unknown'}"
        
        if causation_info.get('ability_modifier_change'):
            ability_info = causation_info['ability_modifier_change']
            description += f". This change is primarily due to a {ability_info['ability'].title()} modifier change "
            description += f"from {ability_info['old_modifier']:+d} to {ability_info['new_modifier']:+d} "
            description += f"(ability score: {ability_info['old_score']} → {ability_info['new_score']})"
        
        if causation_info.get('proficiency_change'):
            description += f". The character gained proficiency in {skill_name.title()}"
        
        if causation_info.get('expertise_change'):
            description += f". The character gained expertise in {skill_name.title()}, doubling the proficiency bonus"
        
        if causation_info.get('equipment_bonus_change'):
            equipment_info = causation_info['equipment_bonus_change']
            description += f". Equipment provides a {equipment_info.get('bonus', 0):+d} bonus to {skill_name.title()}"
        
        if causation_info.get('feat_bonus_change'):
            feat_info = causation_info['feat_bonus_change']
            description += f". A feat provides a {feat_info.get('bonus', 0):+d} bonus to {skill_name.title()}"
        
        # Add passive skill calculation explanation
        description += f". Passive {skill_name.title()} is calculated as 10 + ability modifier + proficiency bonus + other bonuses"
        
        return description
    
    def _create_passive_skill_breakdown(self, skill_config: Dict, character_data: Dict,
                                      causation_info: Dict) -> str:
        """Create calculation breakdown for passive skill."""
        try:
            ability_name = skill_config['ability']
            skill_name = skill_config['skill']
            
            # Get current values
            abilities = extract_ability_scores_data(character_data)
            ability_score = abilities.get(ability_name, 10)
            ability_mod = (ability_score - 10) // 2
            
            # Get proficiency info
            proficiency_bonus = extract_proficiency_bonus_data(character_data)
            is_proficient = self._is_skill_proficient(skill_name, character_data)
            has_expertise = self._has_skill_expertise(skill_name, character_data)
            
            # Calculate components
            base = 10
            prof_bonus = 0
            if is_proficient:
                prof_bonus = proficiency_bonus
                if has_expertise:
                    prof_bonus *= 2
            
            # Get other bonuses
            equipment_bonus = causation_info.get('equipment_bonus_change', {}).get('bonus', 0)
            feat_bonus = causation_info.get('feat_bonus_change', {}).get('bonus', 0)
            other_bonuses = equipment_bonus + feat_bonus
            
            # Create breakdown
            breakdown = f"10 (base) + {ability_mod:+d} ({ability_name.title()}) + {prof_bonus:+d} (proficiency)"
            if other_bonuses != 0:
                breakdown += f" + {other_bonuses:+d} (other bonuses)"
            
            total = base + ability_mod + prof_bonus + other_bonuses
            breakdown += f" = {total}"
            
            return breakdown
            
        except Exception as e:
            self.logger.error(f"Error creating passive skill breakdown: {e}")
            return "Calculation breakdown unavailable"
    
    def _extract_passive_skills(self, character_data: Dict) -> Dict[str, int]:
        """Extract passive skill values from character data."""
        passive_skills = {}
        
        try:
            # Try different possible paths for passive skills
            skills_data = None
            if 'character' in character_data and 'skills' in character_data['character']:
                skills_data = character_data['character']['skills']
            elif 'skills' in character_data:
                skills_data = character_data['skills']
            
            if not skills_data:
                # Calculate passive skills from ability scores and proficiencies
                return self._calculate_passive_skills(character_data)
            
            # Extract passive skills from skills data
            for passive_skill_key in self.tracked_passive_skills.keys():
                if passive_skill_key in skills_data:
                    passive_skills[passive_skill_key] = skills_data[passive_skill_key]
                elif f'passive_{passive_skill_key}' in skills_data:
                    passive_skills[passive_skill_key] = skills_data[f'passive_{passive_skill_key}']
            
            # If no passive skills found in data, calculate them
            if not passive_skills:
                passive_skills = self._calculate_passive_skills(character_data)
            
        except Exception as e:
            self.logger.warning(f"Error extracting passive skills: {e}")
            # Fallback to calculation
            passive_skills = self._calculate_passive_skills(character_data)
        
        return passive_skills
    
    def _calculate_passive_skills(self, character_data: Dict) -> Dict[str, int]:
        """Calculate passive skills from character data."""
        passive_skills = {}
        
        try:
            abilities = extract_ability_scores_data(character_data)
            proficiency_bonus = extract_proficiency_bonus_data(character_data)
            
            for passive_skill_key, skill_config in self.tracked_passive_skills.items():
                ability_name = skill_config['ability']
                skill_name = skill_config['skill']
                
                # Get ability modifier
                ability_score = abilities.get(ability_name, 10)
                ability_mod = (ability_score - 10) // 2
                
                # Check proficiency
                prof_bonus = 0
                if self._is_skill_proficient(skill_name, character_data):
                    prof_bonus = proficiency_bonus
                    if self._has_skill_expertise(skill_name, character_data):
                        prof_bonus *= 2
                
                # Calculate passive skill (10 + ability mod + proficiency bonus)
                passive_value = 10 + ability_mod + prof_bonus
                
                # Add any additional bonuses (equipment, feats, etc.)
                additional_bonus = self._get_skill_additional_bonuses(skill_name, character_data)
                passive_value += additional_bonus
                
                passive_skills[passive_skill_key] = passive_value
                
        except Exception as e:
            self.logger.warning(f"Error calculating passive skills: {e}")
        
        return passive_skills
    
    
    def _extract_proficiency_bonus(self, character_data: Dict) -> int:
        """Extract proficiency bonus from character data."""
        try:
            # Try character_info.proficiency_bonus first (actual data structure)
            if 'character_info' in character_data and 'proficiency_bonus' in character_data['character_info']:
                return character_data['character_info']['proficiency_bonus']
            
            # Try direct proficiency bonus field
            if 'character' in character_data:
                char_data = character_data['character']
                if 'proficiency_bonus' in char_data:
                    return char_data['proficiency_bonus']
                
                # Calculate from level if available
                if 'level' in char_data:
                    level = char_data['level']
                    return 2 + ((level - 1) // 4)  # Standard D&D proficiency bonus progression
            
            # Try alternative paths
            if 'proficiency_bonus' in character_data:
                return character_data['proficiency_bonus']
            
            # Default proficiency bonus for level 1
            return 2
            
        except Exception:
            return 2
    
    def _is_skill_proficient(self, skill_name: str, character_data: Dict) -> bool:
        """Check if character is proficient in a skill."""
        try:
            # Try different possible paths for skill proficiencies
            proficiencies = None
            if 'character' in character_data and 'proficiencies' in character_data['character']:
                proficiencies = character_data['character']['proficiencies']
            elif 'proficiencies' in character_data:
                proficiencies = character_data['proficiencies']
            
            if not proficiencies:
                return False
            
            # Check skills proficiencies
            skills_prof = proficiencies.get('skills', [])
            if isinstance(skills_prof, list):
                return skill_name in skills_prof or skill_name.title() in skills_prof
            elif isinstance(skills_prof, dict):
                return skills_prof.get(skill_name, False) or skills_prof.get(skill_name.title(), False)
            
            return False
            
        except Exception:
            return False
    
    def _has_skill_expertise(self, skill_name: str, character_data: Dict) -> bool:
        """Check if character has expertise in a skill."""
        try:
            # Try different possible paths for expertise
            expertise = None
            if 'character' in character_data and 'expertise' in character_data['character']:
                expertise = character_data['character']['expertise']
            elif 'expertise' in character_data:
                expertise = character_data['expertise']
            elif 'character' in character_data and 'proficiencies' in character_data['character']:
                proficiencies = character_data['character']['proficiencies']
                expertise = proficiencies.get('expertise', [])
            
            if not expertise:
                return False
            
            if isinstance(expertise, list):
                return skill_name in expertise or skill_name.title() in expertise
            elif isinstance(expertise, dict):
                return expertise.get(skill_name, False) or expertise.get(skill_name.title(), False)
            
            return False
            
        except Exception:
            return False
    
    def _get_skill_additional_bonuses(self, skill_name: str, character_data: Dict) -> int:
        """Get additional bonuses to a skill from equipment, feats, etc."""
        total_bonus = 0
        
        try:
            # Check for equipment bonuses
            equipment_bonus = self._get_equipment_skill_bonus(skill_name, character_data)
            total_bonus += equipment_bonus
            
            # Check for feat bonuses
            feat_bonus = self._get_feat_skill_bonus(skill_name, character_data)
            total_bonus += feat_bonus
            
            # Check for magic item bonuses
            magic_item_bonus = self._get_magic_item_skill_bonus(skill_name, character_data)
            total_bonus += magic_item_bonus
            
        except Exception as e:
            self.logger.warning(f"Error getting additional bonuses for {skill_name}: {e}")
        
        return total_bonus
    
    def _get_equipment_skill_bonus(self, skill_name: str, character_data: Dict) -> int:
        """Get equipment bonus to a skill."""
        # This would need to be implemented based on the specific equipment data structure
        # For now, return 0 as a placeholder
        return 0
    
    def _get_feat_skill_bonus(self, skill_name: str, character_data: Dict) -> int:
        """Get feat bonus to a skill."""
        # This would need to be implemented based on the specific feat data structure
        # For now, return 0 as a placeholder
        return 0
    
    def _get_magic_item_skill_bonus(self, skill_name: str, character_data: Dict) -> int:
        """Get magic item bonus to a skill."""
        # This would need to be implemented based on the specific magic item data structure
        # For now, return 0 as a placeholder
        return 0
    
    def _detect_skill_proficiency_change(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict]:
        """Detect if skill proficiency changed."""
        try:
            old_proficient = self._is_skill_proficient(skill_name, old_data)
            new_proficient = self._is_skill_proficient(skill_name, new_data)
            
            if old_proficient != new_proficient:
                return {
                    'skill': skill_name,
                    'old_proficient': old_proficient,
                    'new_proficient': new_proficient,
                    'gained': new_proficient and not old_proficient,
                    'lost': old_proficient and not new_proficient
                }
            
            return None
            
        except Exception:
            return None
    
    def _detect_skill_expertise_change(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict]:
        """Detect if skill expertise changed."""
        try:
            old_expertise = self._has_skill_expertise(skill_name, old_data)
            new_expertise = self._has_skill_expertise(skill_name, new_data)
            
            if old_expertise != new_expertise:
                return {
                    'skill': skill_name,
                    'old_expertise': old_expertise,
                    'new_expertise': new_expertise,
                    'gained': new_expertise and not old_expertise,
                    'lost': old_expertise and not new_expertise
                }
            
            return None
            
        except Exception:
            return None
    
    def _detect_proficiency_bonus_change(self, old_data: Dict, new_data: Dict) -> Optional[Dict]:
        """Detect if proficiency bonus changed."""
        try:
            old_bonus = extract_proficiency_bonus_data(old_data)
            new_bonus = extract_proficiency_bonus_data(new_data)
            
            if old_bonus != new_bonus:
                return {
                    'old_bonus': old_bonus,
                    'new_bonus': new_bonus,
                    'change': new_bonus - old_bonus
                }
            
            return None
            
        except Exception:
            return None
    
    def _detect_equipment_skill_bonus_change(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict]:
        """Detect if equipment skill bonus changed."""
        try:
            old_bonus = self._get_equipment_skill_bonus(skill_name, old_data)
            new_bonus = self._get_equipment_skill_bonus(skill_name, new_data)
            
            if old_bonus != new_bonus:
                return {
                    'skill': skill_name,
                    'old_bonus': old_bonus,
                    'new_bonus': new_bonus,
                    'bonus': new_bonus - old_bonus
                }
            
            return None
            
        except Exception:
            return None
    
    def _detect_feat_skill_bonus_change(self, skill_name: str, old_data: Dict, new_data: Dict) -> Optional[Dict]:
        """Detect if feat skill bonus changed."""
        try:
            old_bonus = self._get_feat_skill_bonus(skill_name, old_data)
            new_bonus = self._get_feat_skill_bonus(skill_name, new_data)
            
            if old_bonus != new_bonus:
                return {
                    'skill': skill_name,
                    'old_bonus': old_bonus,
                    'new_bonus': new_bonus,
                    'bonus': new_bonus - old_bonus
                }
            
            return None
            
        except Exception:
            return None


class AlignmentChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for character alignment changes and modifications."""
    
    def __init__(self):
        field_mappings = {
            'alignment': EnhancedFieldMapping(
                api_path='character.alignment',
                display_name='Alignment',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.FEATURES
            ),
            'alignment_id': EnhancedFieldMapping(
                api_path='character.alignmentId',
                display_name='Alignment ID',
                priority=ChangePriority.LOW,
                category=ChangeCategory.METADATA
            )
        }
        priority_rules = {
            'character.alignment': ChangePriority.MEDIUM,
            'character.alignmentId': ChangePriority.LOW
        }
        super().__init__(field_mappings, priority_rules)
        
        # Alignment mapping for better descriptions
        self.alignment_names = {
            1: "Lawful Good",
            2: "Neutral Good", 
            3: "Chaotic Good",
            4: "Lawful Neutral",
            5: "True Neutral",
            6: "Chaotic Neutral",
            7: "Lawful Evil",
            8: "Neutral Evil",
            9: "Chaotic Evil"
        }
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect alignment changes with detailed attribution."""
        changes = []
        
        try:
            old_alignment = extract_alignment_info_data(old_data)
            new_alignment = extract_alignment_info_data(new_data)
            
            # Detect alignment name/text changes
            if old_alignment.get('name') != new_alignment.get('name'):
                alignment_change = self._create_alignment_change(
                    old_alignment.get('name'),
                    new_alignment.get('name'),
                    old_alignment.get('id'),
                    new_alignment.get('id'),
                    context
                )
                if alignment_change:
                    changes.append(alignment_change)
            
            # Detect alignment ID changes (if name didn't change but ID did)
            elif old_alignment.get('id') != new_alignment.get('id'):
                alignment_id_change = self._create_alignment_id_change(
                    old_alignment.get('id'),
                    new_alignment.get('id'),
                    old_alignment.get('name'),
                    new_alignment.get('name'),
                    context
                )
                if alignment_id_change:
                    changes.append(alignment_id_change)
            
            self.logger.debug(f"Detected {len(changes)} alignment changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting alignment changes: {e}", exc_info=True)
        
        return changes
    
    def _create_alignment_change(self, old_name: str, new_name: str, 
                               old_id: int, new_id: int,
                               context: DetectionContext) -> Optional[FieldChange]:
        """Create alignment change with detailed description."""
        try:
            # Determine change type
            if old_name is None and new_name is not None:
                change_type = ChangeType.ADDED
                description = f"Alignment set to {new_name}"
            elif old_name is not None and new_name is None:
                change_type = ChangeType.REMOVED
                description = f"Alignment removed (was {old_name})"
            else:
                change_type = ChangeType.MODIFIED
                description = f"Alignment changed from {old_name} to {new_name}"
            
            # Analyze the nature of the alignment shift
            shift_analysis = self._analyze_alignment_shift(old_name, new_name, old_id, new_id)
            
            # Create detailed description
            detailed_description = self._create_detailed_alignment_description(
                old_name, new_name, shift_analysis
            )
            
            change = self._create_field_change(
                field_path='character.alignment',
                old_value=old_name,
                new_value=new_name,
                change_type=change_type,
                category=ChangeCategory.FEATURES,
                description=description
            )
            
            # Add enhanced metadata
            change.metadata.update({
                'alignment_change_type': 'alignment_shift',
                'old_alignment_id': old_id,
                'new_alignment_id': new_id,
                'shift_analysis': shift_analysis,
                'detailed_description': detailed_description,
                'moral_axis_change': shift_analysis.get('moral_axis_change'),
                'ethical_axis_change': shift_analysis.get('ethical_axis_change'),
                'alignment_distance': shift_analysis.get('alignment_distance', 0)
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error creating alignment change: {e}", exc_info=True)
            return None
    
    def _create_alignment_id_change(self, old_id: int, new_id: int,
                                  old_name: str, new_name: str,
                                  context: DetectionContext) -> Optional[FieldChange]:
        """Create alignment ID change (usually metadata)."""
        try:
            # This is typically a metadata change when the name stays the same
            # but the underlying ID changes (rare, but possible with API updates)
            description = f"Alignment ID changed from {old_id} to {new_id}"
            if old_name and new_name and old_name != new_name:
                description += f" ({old_name} → {new_name})"
            
            change = self._create_field_change(
                field_path='character.alignmentId',
                old_value=old_id,
                new_value=new_id,
                change_type=ChangeType.MODIFIED,
                category=ChangeCategory.METADATA,
                description=description
            )
            
            # Add metadata
            change.metadata.update({
                'alignment_change_type': 'alignment_id_change',
                'old_alignment_name': old_name,
                'new_alignment_name': new_name
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error creating alignment ID change: {e}", exc_info=True)
            return None
    
    def _analyze_alignment_shift(self, old_name: str, new_name: str, 
                               old_id: int, new_id: int) -> Dict[str, Any]:
        """Analyze the nature of the alignment shift."""
        analysis = {
            'moral_axis_change': None,  # Good/Neutral/Evil axis
            'ethical_axis_change': None,  # Lawful/Neutral/Chaotic axis
            'alignment_distance': 0,
            'shift_type': 'unknown',
            'shift_description': ''
        }
        
        try:
            if old_id is None or new_id is None:
                analysis['shift_type'] = 'initial_set' if old_id is None else 'removed'
                return analysis
            
            # Map IDs to coordinates (Law/Chaos, Good/Evil)
            # Using a 3x3 grid: (0,0) = Lawful Good, (2,2) = Chaotic Evil
            alignment_coords = {
                1: (0, 0),  # Lawful Good
                2: (1, 0),  # Neutral Good
                3: (2, 0),  # Chaotic Good
                4: (0, 1),  # Lawful Neutral
                5: (1, 1),  # True Neutral
                6: (2, 1),  # Chaotic Neutral
                7: (0, 2),  # Lawful Evil
                8: (1, 2),  # Neutral Evil
                9: (2, 2)   # Chaotic Evil
            }
            
            old_coords = alignment_coords.get(old_id, (1, 1))
            new_coords = alignment_coords.get(new_id, (1, 1))
            
            # Calculate axis changes
            ethical_change = new_coords[0] - old_coords[0]  # Law/Chaos axis
            moral_change = new_coords[1] - old_coords[1]    # Good/Evil axis
            
            # Determine axis change descriptions
            if ethical_change > 0:
                analysis['ethical_axis_change'] = 'toward_chaos'
            elif ethical_change < 0:
                analysis['ethical_axis_change'] = 'toward_law'
            else:
                analysis['ethical_axis_change'] = 'no_change'
            
            if moral_change > 0:
                analysis['moral_axis_change'] = 'toward_evil'
            elif moral_change < 0:
                analysis['moral_axis_change'] = 'toward_good'
            else:
                analysis['moral_axis_change'] = 'no_change'
            
            # Calculate Manhattan distance
            analysis['alignment_distance'] = abs(ethical_change) + abs(moral_change)
            
            # Determine shift type
            if analysis['alignment_distance'] == 0:
                analysis['shift_type'] = 'no_change'
            elif analysis['alignment_distance'] == 1:
                analysis['shift_type'] = 'adjacent_shift'
            elif analysis['alignment_distance'] == 2:
                if abs(ethical_change) == 2 or abs(moral_change) == 2:
                    analysis['shift_type'] = 'axis_extreme_shift'
                else:
                    analysis['shift_type'] = 'diagonal_shift'
            elif analysis['alignment_distance'] >= 3:
                analysis['shift_type'] = 'major_shift'
            
            # Create shift description
            analysis['shift_description'] = self._create_shift_description(
                analysis['ethical_axis_change'], 
                analysis['moral_axis_change'],
                analysis['shift_type']
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing alignment shift: {e}")
            analysis['shift_type'] = 'analysis_error'
        
        return analysis
    
    def _create_shift_description(self, ethical_change: str, moral_change: str, shift_type: str) -> str:
        """Create a description of the alignment shift."""
        descriptions = []
        
        if ethical_change == 'toward_law':
            descriptions.append("became more lawful")
        elif ethical_change == 'toward_chaos':
            descriptions.append("became more chaotic")
        
        if moral_change == 'toward_good':
            descriptions.append("became more good")
        elif moral_change == 'toward_evil':
            descriptions.append("became more evil")
        
        if not descriptions:
            return "alignment changed"
        
        if len(descriptions) == 1:
            return descriptions[0]
        else:
            return f"{descriptions[0]} and {descriptions[1]}"
    
    def _create_detailed_alignment_description(self, old_name: str, new_name: str, 
                                             shift_analysis: Dict[str, Any]) -> str:
        """Create detailed description for alignment change."""
        if old_name is None:
            return f"Character alignment set to {new_name}. This establishes the character's moral and ethical worldview."
        
        if new_name is None:
            return f"Character alignment removed (was {old_name}). Character no longer has a defined moral/ethical stance."
        
        base_desc = f"Character alignment changed from {old_name} to {new_name}."
        
        shift_type = shift_analysis.get('shift_type', 'unknown')
        shift_desc = shift_analysis.get('shift_description', '')
        distance = shift_analysis.get('alignment_distance', 0)
        
        if shift_type == 'adjacent_shift':
            base_desc += f" This is a minor alignment shift where the character {shift_desc}."
        elif shift_type == 'diagonal_shift':
            base_desc += f" This is a moderate alignment shift affecting both moral and ethical axes - the character {shift_desc}."
        elif shift_type == 'axis_extreme_shift':
            base_desc += f" This is a significant alignment shift across an entire axis - the character {shift_desc}."
        elif shift_type == 'major_shift':
            base_desc += f" This is a major alignment shift (distance: {distance}) - the character {shift_desc}."
        
        # Add context about what this means
        if 'good' in new_name.lower() and 'evil' in old_name.lower():
            base_desc += " This represents a fundamental change in moral outlook from evil to good."
        elif 'evil' in new_name.lower() and 'good' in old_name.lower():
            base_desc += " This represents a fundamental change in moral outlook from good to evil."
        elif 'lawful' in new_name.lower() and 'chaotic' in old_name.lower():
            base_desc += " This represents a shift from chaotic to lawful behavior and worldview."
        elif 'chaotic' in new_name.lower() and 'lawful' in old_name.lower():
            base_desc += " This represents a shift from lawful to chaotic behavior and worldview."
        
        return base_desc
    
    def _extract_alignment_info(self, character_data: Dict) -> Dict[str, Any]:
        """Extract alignment information from character data."""
        alignment_info = {
            'name': None,
            'id': None
        }
        
        try:
            # Try different possible paths for alignment data
            if 'character' in character_data:
                char_data = character_data['character']
                
                # Check for alignment name/text
                if 'alignment' in char_data:
                    alignment_info['name'] = char_data['alignment']
                
                # Check for alignment ID
                if 'alignmentId' in char_data:
                    alignment_info['id'] = char_data['alignmentId']
                elif 'alignment_id' in char_data:
                    alignment_info['id'] = char_data['alignment_id']
            
            # Direct access fallback
            if alignment_info['name'] is None and 'alignment' in character_data:
                alignment_info['name'] = character_data['alignment']
            
            if alignment_info['id'] is None and 'alignmentId' in character_data:
                alignment_info['id'] = character_data['alignmentId']
            
            # If we have an ID but no name, try to map it
            if alignment_info['id'] is not None and alignment_info['name'] is None:
                alignment_info['name'] = self.alignment_names.get(alignment_info['id'])
            
            # If we have a name but no ID, try to reverse map it
            if alignment_info['name'] is not None and alignment_info['id'] is None:
                for aid, aname in self.alignment_names.items():
                    if aname.lower() == alignment_info['name'].lower():
                        alignment_info['id'] = aid
                        break
            
        except Exception as e:
            self.logger.warning(f"Error extracting alignment info: {e}")
        
        return alignment_info


class SizeChangeDetector(BaseEnhancedDetector):
    """Enhanced detector for character size category changes and size-related effects."""
    
    def __init__(self):
        field_mappings = {
            'size': EnhancedFieldMapping(
                api_path='character.size',
                display_name='Size Category',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.FEATURES
            ),
            'size_id': EnhancedFieldMapping(
                api_path='character.sizeId',
                display_name='Size ID',
                priority=ChangePriority.LOW,
                category=ChangeCategory.METADATA
            )
        }
        priority_rules = {
            'character.size': ChangePriority.MEDIUM,
            'character.sizeId': ChangePriority.LOW
        }
        super().__init__(field_mappings, priority_rules)
        
        # Size category mapping for better descriptions
        self.size_categories = {
            1: "Tiny",
            2: "Small", 
            3: "Medium",
            4: "Large",
            5: "Huge",
            6: "Gargantuan"
        }
        
        # Size effects for detailed descriptions
        self.size_effects = {
            "Tiny": {
                "space": "2.5 x 2.5 feet",
                "reach": "0 feet",
                "ac_modifier": "+2 (size)",
                "attack_modifier": "+2 (size)",
                "stealth_modifier": "+4 (size)",
                "carrying_capacity_multiplier": 0.5,
                "special_rules": ["Can move through spaces of Small or larger creatures", "Disadvantage on Strength checks and saves"]
            },
            "Small": {
                "space": "5 x 5 feet",
                "reach": "5 feet",
                "ac_modifier": "+1 (size)",
                "attack_modifier": "+1 (size)",
                "stealth_modifier": "+2 (size)",
                "carrying_capacity_multiplier": 0.75,
                "special_rules": ["Can move through spaces of Medium or larger creatures"]
            },
            "Medium": {
                "space": "5 x 5 feet",
                "reach": "5 feet",
                "ac_modifier": "0",
                "attack_modifier": "0",
                "stealth_modifier": "0",
                "carrying_capacity_multiplier": 1.0,
                "special_rules": ["Standard size category for most humanoids"]
            },
            "Large": {
                "space": "10 x 10 feet",
                "reach": "5 feet (10 feet with reach weapons)",
                "ac_modifier": "-1 (size)",
                "attack_modifier": "-1 (size)",
                "stealth_modifier": "-2 (size)",
                "carrying_capacity_multiplier": 2.0,
                "special_rules": ["Can grapple creatures up to one size larger", "Advantage on Strength checks and saves"]
            },
            "Huge": {
                "space": "15 x 15 feet",
                "reach": "10 feet (15 feet with reach weapons)",
                "ac_modifier": "-2 (size)",
                "attack_modifier": "-2 (size)",
                "stealth_modifier": "-4 (size)",
                "carrying_capacity_multiplier": 4.0,
                "special_rules": ["Can grapple creatures up to two sizes larger", "Advantage on Strength checks and saves"]
            },
            "Gargantuan": {
                "space": "20 x 20 feet or larger",
                "reach": "15 feet (20 feet with reach weapons)",
                "ac_modifier": "-4 (size)",
                "attack_modifier": "-4 (size)",
                "stealth_modifier": "-8 (size)",
                "carrying_capacity_multiplier": 8.0,
                "special_rules": ["Can grapple creatures up to three sizes larger", "Advantage on Strength checks and saves"]
            }
        }
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect size changes with detailed attribution and effects analysis."""
        changes = []
        
        try:
            old_size = extract_size_info_data(old_data)
            new_size = extract_size_info_data(new_data)
            
            # Detect size name/category changes
            if old_size.get('name') != new_size.get('name'):
                size_change = self._create_size_change(
                    old_size.get('name'),
                    new_size.get('name'),
                    old_size.get('id'),
                    new_size.get('id'),
                    context
                )
                if size_change:
                    changes.append(size_change)
            
            # Detect size ID changes (if name didn't change but ID did)
            elif old_size.get('id') != new_size.get('id'):
                size_id_change = self._create_size_id_change(
                    old_size.get('id'),
                    new_size.get('id'),
                    old_size.get('name'),
                    new_size.get('name'),
                    context
                )
                if size_id_change:
                    changes.append(size_id_change)
            
            self.logger.debug(f"Detected {len(changes)} size changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting size changes: {e}", exc_info=True)
        
        return changes
    
    def _create_size_change(self, old_name: str, new_name: str, 
                           old_id: int, new_id: int,
                           context: DetectionContext) -> Optional[FieldChange]:
        """Create size change with detailed description and effects analysis."""
        try:
            # Determine change type
            if old_name is None and new_name is not None:
                change_type = ChangeType.ADDED
                description = f"Size set to {new_name}"
            elif old_name is not None and new_name is None:
                change_type = ChangeType.REMOVED
                description = f"Size removed (was {old_name})"
            else:
                change_type = ChangeType.MODIFIED
                description = f"Size changed from {old_name} to {new_name}"
            
            # Analyze the size change effects
            size_analysis = self._analyze_size_change_effects(old_name, new_name, old_id, new_id)
            
            # Create detailed description
            detailed_description = self._create_detailed_size_description(
                old_name, new_name, size_analysis
            )
            
            change = self._create_field_change(
                field_path='character.size',
                old_value=old_name,
                new_value=new_name,
                change_type=change_type,
                category=ChangeCategory.FEATURES,
                description=description
            )
            
            # Add enhanced metadata
            change.metadata.update({
                'size_change_type': 'size_category_change',
                'old_size_id': old_id,
                'new_size_id': new_id,
                'size_analysis': size_analysis,
                'detailed_description': detailed_description,
                'size_direction': size_analysis.get('size_direction'),
                'size_steps': size_analysis.get('size_steps', 0),
                'mechanical_effects': size_analysis.get('mechanical_effects', []),
                'combat_implications': size_analysis.get('combat_implications', [])
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error creating size change: {e}", exc_info=True)
            return None
    
    def _create_size_id_change(self, old_id: int, new_id: int,
                              old_name: str, new_name: str,
                              context: DetectionContext) -> Optional[FieldChange]:
        """Create size ID change (usually metadata)."""
        try:
            # This is typically a metadata change when the name stays the same
            # but the underlying ID changes (rare, but possible with API updates)
            description = f"Size ID changed from {old_id} to {new_id}"
            if old_name and new_name and old_name != new_name:
                description += f" ({old_name} → {new_name})"
            
            change = self._create_field_change(
                field_path='character.sizeId',
                old_value=old_id,
                new_value=new_id,
                change_type=ChangeType.MODIFIED,
                category=ChangeCategory.METADATA,
                description=description
            )
            
            # Add metadata
            change.metadata.update({
                'size_change_type': 'size_id_change',
                'old_size_name': old_name,
                'new_size_name': new_name
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error creating size ID change: {e}", exc_info=True)
            return None
    
    def _analyze_size_change_effects(self, old_name: str, new_name: str, 
                                   old_id: int, new_id: int) -> Dict[str, Any]:
        """Analyze the mechanical effects of the size change."""
        analysis = {
            'size_direction': None,
            'size_steps': 0,
            'mechanical_effects': [],
            'combat_implications': [],
            'space_reach_changes': {},
            'modifier_changes': {},
            'carrying_capacity_change': None
        }
        
        try:
            # Determine direction and magnitude of size change
            if old_id is not None and new_id is not None:
                analysis['size_steps'] = new_id - old_id
                if analysis['size_steps'] > 0:
                    analysis['size_direction'] = 'increase'
                elif analysis['size_steps'] < 0:
                    analysis['size_direction'] = 'decrease'
                    analysis['size_steps'] = abs(analysis['size_steps'])
                else:
                    analysis['size_direction'] = 'no_change'
            
            # Get size effects for old and new sizes
            old_effects = self.size_effects.get(old_name, {}) if old_name else {}
            new_effects = self.size_effects.get(new_name, {}) if new_name else {}
            
            # Analyze space and reach changes
            if old_effects.get('space') != new_effects.get('space'):
                analysis['space_reach_changes']['space'] = {
                    'old': old_effects.get('space'),
                    'new': new_effects.get('space')
                }
            
            if old_effects.get('reach') != new_effects.get('reach'):
                analysis['space_reach_changes']['reach'] = {
                    'old': old_effects.get('reach'),
                    'new': new_effects.get('reach')
                }
            
            # Analyze modifier changes
            modifiers_to_check = ['ac_modifier', 'attack_modifier', 'stealth_modifier']
            for modifier in modifiers_to_check:
                old_mod = old_effects.get(modifier)
                new_mod = new_effects.get(modifier)
                if old_mod != new_mod:
                    analysis['modifier_changes'][modifier] = {
                        'old': old_mod,
                        'new': new_mod
                    }
            
            # Analyze carrying capacity changes
            old_capacity = old_effects.get('carrying_capacity_multiplier', 1.0)
            new_capacity = new_effects.get('carrying_capacity_multiplier', 1.0)
            if old_capacity != new_capacity:
                analysis['carrying_capacity_change'] = {
                    'old_multiplier': old_capacity,
                    'new_multiplier': new_capacity,
                    'change_factor': new_capacity / old_capacity if old_capacity > 0 else 1.0
                }
            
            # Generate mechanical effects list
            if analysis['space_reach_changes']:
                analysis['mechanical_effects'].append('Space and reach modifications')
            
            if analysis['modifier_changes']:
                analysis['mechanical_effects'].append('Combat modifier changes')
            
            if analysis['carrying_capacity_change']:
                analysis['mechanical_effects'].append('Carrying capacity adjustment')
            
            # Generate combat implications
            if 'ac_modifier' in analysis['modifier_changes']:
                analysis['combat_implications'].append('Armor Class modifier changed')
            
            if 'attack_modifier' in analysis['modifier_changes']:
                analysis['combat_implications'].append('Attack roll modifier changed')
            
            if 'stealth_modifier' in analysis['modifier_changes']:
                analysis['combat_implications'].append('Stealth modifier changed')
            
            if analysis['space_reach_changes'].get('space'):
                analysis['combat_implications'].append('Combat positioning and movement affected')
            
            if analysis['space_reach_changes'].get('reach'):
                analysis['combat_implications'].append('Melee attack reach changed')
            
            # Add special rules implications
            old_rules = old_effects.get('special_rules', [])
            new_rules = new_effects.get('special_rules', [])
            if old_rules != new_rules:
                analysis['mechanical_effects'].append('Special size rules changed')
                analysis['combat_implications'].append('Special combat rules modified')
            
        except Exception as e:
            self.logger.error(f"Error analyzing size change effects: {e}", exc_info=True)
        
        return analysis
    
    def _create_detailed_size_description(self, old_name: str, new_name: str, 
                                        size_analysis: Dict[str, Any]) -> str:
        """Create detailed description of size change and its effects."""
        try:
            if old_name is None and new_name is not None:
                description = f"Character size set to {new_name}."
            elif old_name is not None and new_name is None:
                description = f"Character size removed (was {old_name})."
            else:
                direction = size_analysis.get('size_direction', 'changed')
                steps = size_analysis.get('size_steps', 0)
                
                if direction == 'increase':
                    description = f"Character size increased from {old_name} to {new_name}"
                    if steps > 1:
                        description += f" ({steps} size categories larger)"
                elif direction == 'decrease':
                    description = f"Character size decreased from {old_name} to {new_name}"
                    if steps > 1:
                        description += f" ({steps} size categories smaller)"
                else:
                    description = f"Character size changed from {old_name} to {new_name}"
                
                description += "."
            
            # Add mechanical effects
            effects = size_analysis.get('mechanical_effects', [])
            if effects:
                description += f" This change affects: {', '.join(effects).lower()}."
            
            # Add specific effect details
            space_reach = size_analysis.get('space_reach_changes', {})
            if space_reach:
                if 'space' in space_reach:
                    old_space = space_reach['space']['old']
                    new_space = space_reach['space']['new']
                    description += f" Space changed from {old_space} to {new_space}."
                
                if 'reach' in space_reach:
                    old_reach = space_reach['reach']['old']
                    new_reach = space_reach['reach']['new']
                    description += f" Reach changed from {old_reach} to {new_reach}."
            
            # Add modifier changes
            modifier_changes = size_analysis.get('modifier_changes', {})
            if modifier_changes:
                mod_descriptions = []
                for mod_type, change in modifier_changes.items():
                    mod_name = mod_type.replace('_modifier', '').replace('_', ' ').title()
                    old_val = change['old']
                    new_val = change['new']
                    mod_descriptions.append(f"{mod_name}: {old_val} → {new_val}")
                
                if mod_descriptions:
                    description += f" Modifier changes: {', '.join(mod_descriptions)}."
            
            # Add carrying capacity changes
            capacity_change = size_analysis.get('carrying_capacity_change')
            if capacity_change:
                factor = capacity_change['change_factor']
                if factor > 1:
                    description += f" Carrying capacity increased by {factor:.1f}x."
                elif factor < 1:
                    description += f" Carrying capacity decreased by {1/factor:.1f}x."
            
            # Add combat implications
            combat_implications = size_analysis.get('combat_implications', [])
            if combat_implications:
                description += f" Combat implications: {', '.join(combat_implications).lower()}."
            
            # Add size effects information
            if new_name and new_name in self.size_effects:
                new_effects = self.size_effects[new_name]
                special_rules = new_effects.get('special_rules', [])
                if special_rules:
                    description += f" Special rules for {new_name} size: {'; '.join(special_rules)}."
            
            return description
            
        except Exception as e:
            self.logger.error(f"Error creating detailed size description: {e}", exc_info=True)
            return f"Size changed from {old_name or 'Unknown'} to {new_name or 'Unknown'}."
    
    def _extract_size_info(self, character_data: Dict) -> Dict[str, Any]:
        """Extract size information from character data."""
        size_info = {'name': None, 'id': None}
        
        try:
            # Try character.size path first
            if 'character' in character_data:
                char_data = character_data['character']
                
                # Check for size name
                if 'size' in char_data:
                    size_info['name'] = char_data['size']
                
                # Check for size ID
                if 'sizeId' in char_data:
                    size_info['id'] = char_data['sizeId']
                elif 'size_id' in char_data:
                    size_info['id'] = char_data['size_id']
            
            # Direct access fallback
            if size_info['name'] is None and 'size' in character_data:
                size_info['name'] = character_data['size']
            
            if size_info['id'] is None and 'sizeId' in character_data:
                size_info['id'] = character_data['sizeId']
            
            # If we have an ID but no name, try to map it
            if size_info['id'] is not None and size_info['name'] is None:
                size_info['name'] = self.size_categories.get(size_info['id'])
            
            # If we have a name but no ID, try to reverse map it
            if size_info['name'] is not None and size_info['id'] is None:
                for sid, sname in self.size_categories.items():
                    if sname.lower() == size_info['name'].lower():
                        size_info['id'] = sid
                        break
            
        except Exception as e:
            self.logger.warning(f"Error extracting size info: {e}")
        
        return size_info


class MovementSpeedDetector(BaseEnhancedDetector):
    """Enhanced detector for movement speed modifications and various movement types."""
    
    def __init__(self):
        field_mappings = {
            'speed': EnhancedFieldMapping(
                api_path='character.speed',
                display_name='Movement Speed',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.FEATURES
            ),
            'walking_speed': EnhancedFieldMapping(
                api_path='character.speed.walking',
                display_name='Walking Speed',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.FEATURES
            ),
            'flying_speed': EnhancedFieldMapping(
                api_path='character.speed.flying',
                display_name='Flying Speed',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.FEATURES
            ),
            'swimming_speed': EnhancedFieldMapping(
                api_path='character.speed.swimming',
                display_name='Swimming Speed',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.FEATURES
            ),
            'climbing_speed': EnhancedFieldMapping(
                api_path='character.speed.climbing',
                display_name='Climbing Speed',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.FEATURES
            ),
            'burrowing_speed': EnhancedFieldMapping(
                api_path='character.speed.burrowing',
                display_name='Burrowing Speed',
                priority=ChangePriority.MEDIUM,
                category=ChangeCategory.FEATURES
            )
        }
        priority_rules = {
            'character.speed': ChangePriority.MEDIUM,
            'character.speed.walking': ChangePriority.MEDIUM,
            'character.speed.flying': ChangePriority.HIGH,
            'character.speed.swimming': ChangePriority.MEDIUM,
            'character.speed.climbing': ChangePriority.MEDIUM,
            'character.speed.burrowing': ChangePriority.MEDIUM
        }
        super().__init__(field_mappings, priority_rules)
        
        # Movement types and their tactical significance
        self.movement_types = {
            'walking': {
                'display_name': 'Walking Speed',
                'tactical_significance': 'Primary movement mode for positioning and combat',
                'default_speed': 30,
                'units': 'feet'
            },
            'flying': {
                'display_name': 'Flying Speed',
                'tactical_significance': 'Provides 3D movement, immunity to ground hazards, and tactical advantage',
                'default_speed': 0,
                'units': 'feet',
                'special_notes': 'Requires concentration or specific conditions unless innate'
            },
            'swimming': {
                'display_name': 'Swimming Speed',
                'tactical_significance': 'Enables efficient underwater movement and aquatic combat',
                'default_speed': 0,
                'units': 'feet',
                'special_notes': 'Without swimming speed, movement underwater is at half walking speed'
            },
            'climbing': {
                'display_name': 'Climbing Speed',
                'tactical_significance': 'Allows vertical movement without Athletics checks',
                'default_speed': 0,
                'units': 'feet',
                'special_notes': 'Without climbing speed, requires Athletics checks and costs extra movement'
            },
            'burrowing': {
                'display_name': 'Burrowing Speed',
                'tactical_significance': 'Enables underground movement and unique tactical positioning',
                'default_speed': 0,
                'units': 'feet',
                'special_notes': 'Rare ability that provides immunity to many surface effects'
            },
            'hover': {
                'display_name': 'Hover',
                'tactical_significance': 'Maintains flight without movement, immune to being knocked prone while flying',
                'default_speed': None,
                'units': 'boolean',
                'special_notes': 'Modifies flying speed behavior rather than providing speed itself'
            }
        }
        
        # Speed change sources for causation analysis
        self.speed_change_sources = {
            'racial_trait': 'Racial or species trait',
            'class_feature': 'Class feature or ability',
            'feat': 'Feat selection',
            'spell': 'Spell effect',
            'magic_item': 'Magic item',
            'equipment': 'Equipment or armor',
            'condition': 'Condition or status effect',
            'level_progression': 'Level advancement',
            'ability_score': 'Ability score change',
            'size_change': 'Size category change'
        }
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect movement speed changes with detailed attribution and tactical analysis."""
        changes = []
        
        try:
            old_speeds = extract_movement_speeds_data(old_data)
            new_speeds = extract_movement_speeds_data(new_data)
            
            # Detect changes for each movement type
            for movement_type in self.movement_types.keys():
                old_speed = old_speeds.get(movement_type)
                new_speed = new_speeds.get(movement_type)
                
                # Skip if both are None or both are the same
                if old_speed == new_speed:
                    continue
                
                speed_change = self._create_movement_speed_change(
                    movement_type,
                    old_speed,
                    new_speed,
                    context
                )
                if speed_change:
                    changes.append(speed_change)
            
            # Detect overall speed profile changes
            if changes:
                profile_change = self._analyze_speed_profile_change(old_speeds, new_speeds, changes)
                if profile_change:
                    changes.append(profile_change)
            
            self.logger.debug(f"Detected {len(changes)} movement speed changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting movement speed changes: {e}", exc_info=True)
        
        return changes
    
    def _create_movement_speed_change(self, movement_type: str, old_speed: Any, 
                                    new_speed: Any, context: DetectionContext) -> Optional[FieldChange]:
        """Create movement speed change with detailed description and tactical analysis."""
        try:
            movement_info = self.movement_types.get(movement_type, {})
            display_name = movement_info.get('display_name', movement_type.title())
            
            # Determine change type and description
            if old_speed is None and new_speed is not None:
                change_type = ChangeType.ADDED
                if movement_type == 'hover':
                    description = f"Gained {display_name} ability"
                else:
                    description = f"Gained {display_name}: {new_speed} feet"
            elif old_speed is not None and new_speed is None:
                change_type = ChangeType.REMOVED
                if movement_type == 'hover':
                    description = f"Lost {display_name} ability"
                else:
                    description = f"Lost {display_name} (was {old_speed} feet)"
            else:
                change_type = ChangeType.MODIFIED
                if movement_type == 'hover':
                    description = f"{display_name} ability changed"
                else:
                    old_val = old_speed if old_speed is not None else 0
                    new_val = new_speed if new_speed is not None else 0
                    if new_val > old_val:
                        change_type = ChangeType.INCREMENTED
                        description = f"{display_name} increased: {old_val} → {new_val} feet"
                    elif new_val < old_val:
                        change_type = ChangeType.DECREMENTED
                        description = f"{display_name} decreased: {old_val} → {new_val} feet"
                    else:
                        description = f"{display_name} modified: {old_speed} → {new_speed}"
            
            # Analyze tactical implications
            tactical_analysis = self._analyze_speed_change_implications(
                movement_type, old_speed, new_speed
            )
            
            # Create detailed description
            detailed_description = self._create_detailed_speed_description(
                movement_type, old_speed, new_speed, tactical_analysis
            )
            
            change = self._create_field_change(
                field_path=f'character.speed.{movement_type}',
                old_value=old_speed,
                new_value=new_speed,
                change_type=change_type,
                category=ChangeCategory.FEATURES,
                description=description
            )
            
            # Add enhanced metadata
            change.metadata.update({
                'movement_type': movement_type,
                'movement_display_name': display_name,
                'tactical_analysis': tactical_analysis,
                'detailed_description': detailed_description,
                'speed_change_magnitude': tactical_analysis.get('speed_change_magnitude', 0),
                'tactical_significance': movement_info.get('tactical_significance'),
                'special_notes': movement_info.get('special_notes'),
                'combat_implications': tactical_analysis.get('combat_implications', []),
                'exploration_implications': tactical_analysis.get('exploration_implications', [])
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error creating movement speed change for {movement_type}: {e}", exc_info=True)
            return None
    
    def _analyze_speed_change_implications(self, movement_type: str, 
                                         old_speed: Any, new_speed: Any) -> Dict[str, Any]:
        """Analyze the tactical and mechanical implications of speed changes."""
        analysis = {
            'speed_change_magnitude': 0,
            'change_direction': 'no_change',
            'tactical_impact': 'minimal',
            'combat_implications': [],
            'exploration_implications': [],
            'mechanical_effects': [],
            'strategic_advantages': [],
            'strategic_disadvantages': []
        }
        
        try:
            # Calculate magnitude for numeric speeds
            if movement_type != 'hover':
                old_val = old_speed if old_speed is not None else 0
                new_val = new_speed if new_speed is not None else 0
                analysis['speed_change_magnitude'] = new_val - old_val
                
                if analysis['speed_change_magnitude'] > 0:
                    analysis['change_direction'] = 'increase'
                elif analysis['speed_change_magnitude'] < 0:
                    analysis['change_direction'] = 'decrease'
            
            # Analyze based on movement type
            if movement_type == 'walking':
                analysis.update(self._analyze_walking_speed_change(old_speed, new_speed))
            elif movement_type == 'flying':
                analysis.update(self._analyze_flying_speed_change(old_speed, new_speed))
            elif movement_type == 'swimming':
                analysis.update(self._analyze_swimming_speed_change(old_speed, new_speed))
            elif movement_type == 'climbing':
                analysis.update(self._analyze_climbing_speed_change(old_speed, new_speed))
            elif movement_type == 'burrowing':
                analysis.update(self._analyze_burrowing_speed_change(old_speed, new_speed))
            elif movement_type == 'hover':
                analysis.update(self._analyze_hover_change(old_speed, new_speed))
            
            # Determine overall tactical impact
            if movement_type in ['flying', 'burrowing'] and new_speed and not old_speed:
                analysis['tactical_impact'] = 'major'
            elif movement_type == 'walking' and abs(analysis['speed_change_magnitude']) >= 10:
                analysis['tactical_impact'] = 'significant'
            elif analysis['speed_change_magnitude'] != 0:
                analysis['tactical_impact'] = 'moderate'
            
        except Exception as e:
            self.logger.error(f"Error analyzing speed change implications: {e}", exc_info=True)
        
        return analysis
    
    def _analyze_walking_speed_change(self, old_speed: Any, new_speed: Any) -> Dict[str, Any]:
        """Analyze walking speed change implications."""
        analysis = {}
        old_val = old_speed if old_speed is not None else 30
        new_val = new_speed if new_speed is not None else 30
        
        if new_val > old_val:
            analysis['combat_implications'] = [
                'Improved battlefield positioning',
                'Better ability to close distance to enemies',
                'Enhanced kiting potential for ranged characters',
                'Improved opportunity attack avoidance'
            ]
            analysis['exploration_implications'] = [
                'Faster overland travel',
                'Better chase and pursuit capabilities',
                'Improved exploration efficiency'
            ]
            analysis['strategic_advantages'] = [
                'Enhanced tactical mobility',
                'Better positioning options in combat'
            ]
        elif new_val < old_val:
            analysis['combat_implications'] = [
                'Reduced battlefield mobility',
                'Difficulty closing distance to enemies',
                'Increased vulnerability to kiting',
                'Harder to avoid opportunity attacks'
            ]
            analysis['exploration_implications'] = [
                'Slower overland travel',
                'Reduced chase capabilities',
                'Potential party movement bottleneck'
            ]
            analysis['strategic_disadvantages'] = [
                'Reduced tactical options',
                'Positioning limitations in combat'
            ]
        
        return analysis
    
    def _analyze_flying_speed_change(self, old_speed: Any, new_speed: Any) -> Dict[str, Any]:
        """Analyze flying speed change implications."""
        analysis = {}
        
        if old_speed is None and new_speed is not None:
            # Gained flight
            analysis['combat_implications'] = [
                'Immunity to ground-based hazards and effects',
                'Superior battlefield positioning and line of sight',
                'Ability to bypass ground-based enemies',
                'Enhanced ranged combat effectiveness',
                'Immunity to difficult terrain'
            ]
            analysis['exploration_implications'] = [
                'Ability to bypass ground obstacles',
                'Enhanced scouting and reconnaissance',
                'Access to previously unreachable areas',
                'Immunity to ground-based environmental hazards'
            ]
            analysis['strategic_advantages'] = [
                'Three-dimensional tactical movement',
                'Significant combat advantage',
                'Major exploration enhancement'
            ]
        elif old_speed is not None and new_speed is None:
            # Lost flight
            analysis['combat_implications'] = [
                'Loss of aerial tactical advantage',
                'Vulnerability to ground hazards',
                'Reduced positioning options',
                'Loss of immunity to ground effects'
            ]
            analysis['exploration_implications'] = [
                'Loss of aerial scouting capability',
                'Inability to bypass ground obstacles',
                'Reduced access to elevated areas'
            ]
            analysis['strategic_disadvantages'] = [
                'Major tactical capability loss',
                'Significant exploration limitation'
            ]
        elif old_speed is not None and new_speed is not None:
            # Flight speed changed
            old_val = old_speed if old_speed is not None else 0
            new_val = new_speed if new_speed is not None else 0
            
            if new_val > old_val:
                analysis['combat_implications'] = [
                    'Improved aerial maneuverability',
                    'Better ability to maintain distance',
                    'Enhanced hit-and-run tactics'
                ]
                analysis['strategic_advantages'] = [
                    'Enhanced aerial mobility'
                ]
            else:
                analysis['combat_implications'] = [
                    'Reduced aerial maneuverability',
                    'Difficulty maintaining optimal distance'
                ]
                analysis['strategic_disadvantages'] = [
                    'Reduced aerial effectiveness'
                ]
        
        return analysis
    
    def _analyze_swimming_speed_change(self, old_speed: Any, new_speed: Any) -> Dict[str, Any]:
        """Analyze swimming speed change implications."""
        analysis = {}
        
        if old_speed is None and new_speed is not None:
            # Gained swimming speed
            analysis['combat_implications'] = [
                'Full movement speed in water',
                'No Athletics checks required for swimming',
                'Enhanced aquatic combat effectiveness'
            ]
            analysis['exploration_implications'] = [
                'Efficient underwater exploration',
                'Ability to traverse water obstacles',
                'Enhanced aquatic survival'
            ]
            analysis['strategic_advantages'] = [
                'Aquatic mobility advantage',
                'Access to underwater areas'
            ]
        elif old_speed is not None and new_speed is None:
            # Lost swimming speed
            analysis['combat_implications'] = [
                'Reduced to half speed in water',
                'Athletics checks required for swimming',
                'Vulnerability in aquatic combat'
            ]
            analysis['exploration_implications'] = [
                'Inefficient underwater movement',
                'Difficulty with water obstacles'
            ]
            analysis['strategic_disadvantages'] = [
                'Loss of aquatic advantage'
            ]
        
        return analysis
    
    def _analyze_climbing_speed_change(self, old_speed: Any, new_speed: Any) -> Dict[str, Any]:
        """Analyze climbing speed change implications."""
        analysis = {}
        
        if old_speed is None and new_speed is not None:
            # Gained climbing speed
            analysis['combat_implications'] = [
                'No Athletics checks for climbing',
                'Full movement speed on vertical surfaces',
                'Enhanced vertical positioning options'
            ]
            analysis['exploration_implications'] = [
                'Efficient vertical exploration',
                'Ability to bypass ground obstacles',
                'Access to elevated areas'
            ]
            analysis['strategic_advantages'] = [
                'Vertical mobility advantage',
                'Enhanced positioning options'
            ]
        elif old_speed is not None and new_speed is None:
            # Lost climbing speed
            analysis['combat_implications'] = [
                'Athletics checks required for climbing',
                'Reduced climbing efficiency',
                'Limited vertical positioning'
            ]
            analysis['exploration_implications'] = [
                'Difficulty with vertical obstacles',
                'Reduced access to elevated areas'
            ]
            analysis['strategic_disadvantages'] = [
                'Loss of vertical mobility'
            ]
        
        return analysis
    
    def _analyze_burrowing_speed_change(self, old_speed: Any, new_speed: Any) -> Dict[str, Any]:
        """Analyze burrowing speed change implications."""
        analysis = {}
        
        if old_speed is None and new_speed is not None:
            # Gained burrowing speed
            analysis['combat_implications'] = [
                'Ability to move underground',
                'Immunity to surface area effects',
                'Unique tactical positioning options',
                'Potential for surprise attacks'
            ]
            analysis['exploration_implications'] = [
                'Underground exploration capability',
                'Ability to bypass surface obstacles',
                'Access to underground areas'
            ]
            analysis['strategic_advantages'] = [
                'Unique mobility option',
                'Major tactical advantage',
                'Rare and powerful ability'
            ]
        elif old_speed is not None and new_speed is None:
            # Lost burrowing speed
            analysis['combat_implications'] = [
                'Loss of underground positioning',
                'Vulnerability to surface effects',
                'Loss of unique tactical options'
            ]
            analysis['exploration_implications'] = [
                'Loss of underground access',
                'Inability to bypass surface obstacles'
            ]
            analysis['strategic_disadvantages'] = [
                'Loss of rare mobility option',
                'Significant tactical limitation'
            ]
        
        return analysis
    
    def _analyze_hover_change(self, old_hover: Any, new_hover: Any) -> Dict[str, Any]:
        """Analyze hover ability change implications."""
        analysis = {}
        
        if not old_hover and new_hover:
            # Gained hover
            analysis['combat_implications'] = [
                'Can remain stationary while flying',
                'Immune to being knocked prone while flying',
                'No need to move to maintain flight'
            ]
            analysis['strategic_advantages'] = [
                'Enhanced flight stability',
                'Improved aerial positioning control'
            ]
        elif old_hover and not new_hover:
            # Lost hover
            analysis['combat_implications'] = [
                'Must move to maintain flight',
                'Vulnerable to being knocked prone while flying',
                'Reduced flight control'
            ]
            analysis['strategic_disadvantages'] = [
                'Reduced flight stability',
                'Loss of stationary flight'
            ]
        
        return analysis
    
    def _create_detailed_speed_description(self, movement_type: str, old_speed: Any, 
                                         new_speed: Any, tactical_analysis: Dict[str, Any]) -> str:
        """Create detailed description of movement speed change and its implications."""
        try:
            movement_info = self.movement_types.get(movement_type, {})
            display_name = movement_info.get('display_name', movement_type.title())
            
            # Base description
            if old_speed is None and new_speed is not None:
                if movement_type == 'hover':
                    description = f"Gained {display_name} ability."
                else:
                    description = f"Gained {display_name} of {new_speed} feet."
            elif old_speed is not None and new_speed is None:
                if movement_type == 'hover':
                    description = f"Lost {display_name} ability."
                else:
                    description = f"Lost {display_name} (was {old_speed} feet)."
            else:
                if movement_type == 'hover':
                    description = f"{display_name} ability changed."
                else:
                    old_val = old_speed if old_speed is not None else 0
                    new_val = new_speed if new_speed is not None else 0
                    change_mag = abs(new_val - old_val)
                    
                    if new_val > old_val:
                        description = f"{display_name} increased by {change_mag} feet ({old_val} → {new_val} feet)."
                    elif new_val < old_val:
                        description = f"{display_name} decreased by {change_mag} feet ({old_val} → {new_val} feet)."
                    else:
                        description = f"{display_name} modified from {old_speed} to {new_speed}."
            
            # Add tactical significance
            tactical_significance = movement_info.get('tactical_significance')
            if tactical_significance:
                description += f" {tactical_significance}."
            
            # Add tactical impact
            tactical_impact = tactical_analysis.get('tactical_impact', 'minimal')
            if tactical_impact == 'major':
                description += " This represents a major tactical capability change."
            elif tactical_impact == 'significant':
                description += " This significantly affects tactical options."
            elif tactical_impact == 'moderate':
                description += " This moderately impacts tactical capabilities."
            
            # Add combat implications
            combat_implications = tactical_analysis.get('combat_implications', [])
            if combat_implications:
                description += f" Combat implications: {'; '.join(combat_implications[:3])}."
                if len(combat_implications) > 3:
                    description += f" Plus {len(combat_implications) - 3} additional combat effects."
            
            # Add exploration implications
            exploration_implications = tactical_analysis.get('exploration_implications', [])
            if exploration_implications:
                description += f" Exploration implications: {'; '.join(exploration_implications[:2])}."
                if len(exploration_implications) > 2:
                    description += f" Plus {len(exploration_implications) - 2} additional exploration effects."
            
            # Add special notes
            special_notes = movement_info.get('special_notes')
            if special_notes:
                description += f" Note: {special_notes}."
            
            return description
            
        except Exception as e:
            self.logger.error(f"Error creating detailed speed description: {e}", exc_info=True)
            return f"{movement_type.title()} speed changed from {old_speed} to {new_speed}."
    
    def _analyze_speed_profile_change(self, old_speeds: Dict[str, Any], 
                                    new_speeds: Dict[str, Any], 
                                    individual_changes: List[FieldChange]) -> Optional[FieldChange]:
        """Analyze overall movement profile changes for comprehensive summary."""
        try:
            # Only create profile change if there are multiple movement changes
            if len(individual_changes) < 2:
                return None
            
            # Analyze the overall mobility change
            mobility_analysis = self._analyze_overall_mobility_change(old_speeds, new_speeds)
            
            if not mobility_analysis.get('significant_change', False):
                return None
            
            description = f"Movement profile changed: {mobility_analysis['summary']}"
            detailed_description = self._create_mobility_profile_description(
                old_speeds, new_speeds, mobility_analysis
            )
            
            change = self._create_field_change(
                field_path='character.speed',
                old_value=old_speeds,
                new_value=new_speeds,
                change_type=ChangeType.MODIFIED,
                category=ChangeCategory.FEATURES,
                description=description
            )
            
            # Add enhanced metadata
            change.metadata.update({
                'change_type': 'movement_profile_change',
                'mobility_analysis': mobility_analysis,
                'detailed_description': detailed_description,
                'individual_changes_count': len(individual_changes),
                'mobility_tier_change': mobility_analysis.get('mobility_tier_change'),
                'tactical_impact_level': mobility_analysis.get('tactical_impact_level')
            })
            
            return change
            
        except Exception as e:
            self.logger.error(f"Error analyzing speed profile change: {e}", exc_info=True)
            return None
    
    def _analyze_overall_mobility_change(self, old_speeds: Dict[str, Any], 
                                       new_speeds: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the overall change in character mobility."""
        analysis = {
            'significant_change': False,
            'summary': '',
            'mobility_tier_change': 'no_change',
            'tactical_impact_level': 'minimal',
            'gained_movement_types': [],
            'lost_movement_types': [],
            'improved_movement_types': [],
            'reduced_movement_types': []
        }
        
        try:
            # Check for gained/lost movement types
            for movement_type in self.movement_types.keys():
                old_speed = old_speeds.get(movement_type)
                new_speed = new_speeds.get(movement_type)
                
                if old_speed is None and new_speed is not None:
                    analysis['gained_movement_types'].append(movement_type)
                elif old_speed is not None and new_speed is None:
                    analysis['lost_movement_types'].append(movement_type)
                elif old_speed is not None and new_speed is not None:
                    if movement_type != 'hover':
                        old_val = old_speed if old_speed is not None else 0
                        new_val = new_speed if new_speed is not None else 0
                        if new_val > old_val:
                            analysis['improved_movement_types'].append(movement_type)
                        elif new_val < old_val:
                            analysis['reduced_movement_types'].append(movement_type)
            
            # Determine if this is a significant change
            major_gains = [t for t in analysis['gained_movement_types'] if t in ['flying', 'burrowing']]
            major_losses = [t for t in analysis['lost_movement_types'] if t in ['flying', 'burrowing']]
            
            if major_gains or major_losses or len(analysis['gained_movement_types']) >= 2:
                analysis['significant_change'] = True
                analysis['tactical_impact_level'] = 'major'
            elif analysis['gained_movement_types'] or analysis['lost_movement_types']:
                analysis['significant_change'] = True
                analysis['tactical_impact_level'] = 'moderate'
            elif len(analysis['improved_movement_types']) + len(analysis['reduced_movement_types']) >= 2:
                analysis['significant_change'] = True
                analysis['tactical_impact_level'] = 'moderate'
            
            # Create summary
            summary_parts = []
            if analysis['gained_movement_types']:
                gained_display = [self.movement_types[t]['display_name'] for t in analysis['gained_movement_types']]
                summary_parts.append(f"gained {', '.join(gained_display)}")
            
            if analysis['lost_movement_types']:
                lost_display = [self.movement_types[t]['display_name'] for t in analysis['lost_movement_types']]
                summary_parts.append(f"lost {', '.join(lost_display)}")
            
            if analysis['improved_movement_types']:
                improved_display = [self.movement_types[t]['display_name'] for t in analysis['improved_movement_types']]
                summary_parts.append(f"improved {', '.join(improved_display)}")
            
            if analysis['reduced_movement_types']:
                reduced_display = [self.movement_types[t]['display_name'] for t in analysis['reduced_movement_types']]
                summary_parts.append(f"reduced {', '.join(reduced_display)}")
            
            analysis['summary'] = ', '.join(summary_parts)
            
        except Exception as e:
            self.logger.error(f"Error analyzing overall mobility change: {e}", exc_info=True)
        
        return analysis
    
    def _create_mobility_profile_description(self, old_speeds: Dict[str, Any], 
                                           new_speeds: Dict[str, Any], 
                                           mobility_analysis: Dict[str, Any]) -> str:
        """Create detailed description of overall mobility profile change."""
        try:
            description = "Character movement profile underwent significant changes. "
            
            # Add gained movement types
            gained = mobility_analysis.get('gained_movement_types', [])
            if gained:
                gained_display = [self.movement_types[t]['display_name'] for t in gained]
                description += f"Gained new movement capabilities: {', '.join(gained_display)}. "
            
            # Add lost movement types
            lost = mobility_analysis.get('lost_movement_types', [])
            if lost:
                lost_display = [self.movement_types[t]['display_name'] for t in lost]
                description += f"Lost movement capabilities: {', '.join(lost_display)}. "
            
            # Add improved movement types
            improved = mobility_analysis.get('improved_movement_types', [])
            if improved:
                improved_display = [self.movement_types[t]['display_name'] for t in improved]
                description += f"Improved movement speeds: {', '.join(improved_display)}. "
            
            # Add reduced movement types
            reduced = mobility_analysis.get('reduced_movement_types', [])
            if reduced:
                reduced_display = [self.movement_types[t]['display_name'] for t in reduced]
                description += f"Reduced movement speeds: {', '.join(reduced_display)}. "
            
            # Add tactical impact assessment
            tactical_impact = mobility_analysis.get('tactical_impact_level', 'minimal')
            if tactical_impact == 'major':
                description += "This represents a major shift in tactical capabilities and battlefield positioning options."
            elif tactical_impact == 'moderate':
                description += "This moderately affects tactical options and movement strategies."
            
            # Add specific implications for major movement types
            if 'flying' in gained:
                description += " Gaining flight provides significant tactical advantages including 3D positioning, immunity to ground hazards, and enhanced battlefield control."
            
            if 'flying' in lost:
                description += " Losing flight removes major tactical advantages and limits positioning options significantly."
            
            if 'burrowing' in gained:
                description += " Gaining burrowing speed provides unique underground positioning and immunity to surface effects."
            
            return description
            
        except Exception as e:
            self.logger.error(f"Error creating mobility profile description: {e}", exc_info=True)
            return "Character movement profile changed significantly."
    
    def _extract_movement_speeds(self, character_data: Dict) -> Dict[str, Any]:
        """Extract movement speed information from character data."""
        speeds = {}
        
        try:
            # Try character.speed path first
            speed_data = None
            if 'character' in character_data and 'speed' in character_data['character']:
                speed_data = character_data['character']['speed']
            elif 'speed' in character_data:
                speed_data = character_data['speed']
            
            if not speed_data:
                return speeds
            
            # Handle different speed data structures
            if isinstance(speed_data, dict):
                # Extract each movement type
                for movement_type in self.movement_types.keys():
                    # Try different possible field names
                    possible_fields = [
                        movement_type,
                        f'{movement_type}_speed',
                        movement_type.replace('_', ''),
                        movement_type.title(),
                        movement_type.replace('_', ' ').title().replace(' ', '')
                    ]
                    
                    for field in possible_fields:
                        if field in speed_data:
                            value = speed_data[field]
                            # Handle different value formats
                            if isinstance(value, (int, float)) and value > 0:
                                speeds[movement_type] = value
                            elif isinstance(value, bool) and movement_type == 'hover':
                                speeds[movement_type] = value
                            elif isinstance(value, str) and value.isdigit():
                                speeds[movement_type] = int(value)
                            break
            
            elif isinstance(speed_data, (int, float)):
                # If speed is just a number, assume it's walking speed
                speeds['walking'] = speed_data
            
            # Handle legacy or alternative field names
            if 'character' in character_data:
                char_data = character_data['character']
                
                # Check for direct speed fields
                if 'walking_speed' in char_data:
                    speeds['walking'] = char_data['walking_speed']
                elif 'base_speed' in char_data:
                    speeds['walking'] = char_data['base_speed']
                
                if 'fly_speed' in char_data:
                    speeds['flying'] = char_data['fly_speed']
                elif 'flight_speed' in char_data:
                    speeds['flying'] = char_data['flight_speed']
                
                if 'swim_speed' in char_data:
                    speeds['swimming'] = char_data['swim_speed']
                
                if 'climb_speed' in char_data:
                    speeds['climbing'] = char_data['climb_speed']
                
                if 'burrow_speed' in char_data:
                    speeds['burrowing'] = char_data['burrow_speed']
                
                if 'hover' in char_data:
                    speeds['hover'] = char_data['hover']
            
            # Clean up speeds - remove None values and ensure proper types
            cleaned_speeds = {}
            for movement_type, speed in speeds.items():
                if speed is not None:
                    if movement_type == 'hover':
                        cleaned_speeds[movement_type] = bool(speed)
                    elif isinstance(speed, (int, float)) and speed > 0:
                        cleaned_speeds[movement_type] = int(speed)
            
            return cleaned_speeds
            
        except Exception as e:
            self.logger.warning(f"Error extracting movement speeds: {e}")
            return {}


class ClassFeaturesChangeDetector(BaseEnhancedDetector):
    """Detector for class feature changes including both single-class and multiclass characters."""
    
    def __init__(self):
        field_mappings = {
            'class_features': EnhancedFieldMapping(
                api_path='features.class_features',
                display_name='Class Features',
                priority=ChangePriority.HIGH,
                category=ChangeCategory.FEATURES
            )
        }
        priority_rules = {
            'features.class_features': ChangePriority.HIGH,
            'features.class_features.*': ChangePriority.HIGH
        }
        super().__init__(field_mappings, priority_rules)
    
    def detect_changes(self, old_data: Dict, new_data: Dict, context: DetectionContext) -> List[FieldChange]:
        """Detect class feature changes for any character (single-class or multiclass)."""
        changes = []
        
        try:
            old_features = extract_class_features_data(old_data)
            new_features = extract_class_features_data(new_data)
            
            # Get the actual class features lists
            old_class_features = old_features.get('class_features', [])
            new_class_features = new_features.get('class_features', [])
            
            # Convert lists to dictionaries for easier comparison
            old_features_dict = {}
            new_features_dict = {}
            
            if isinstance(old_class_features, list):
                for feature in old_class_features:
                    if isinstance(feature, dict) and 'name' in feature:
                        # Use feature name as key for comparison
                        feature_key = feature['name'].lower().replace(' ', '_').replace("'", '')
                        old_features_dict[feature_key] = feature
            
            if isinstance(new_class_features, list):
                for feature in new_class_features:
                    if isinstance(feature, dict) and 'name' in feature:
                        feature_key = feature['name'].lower().replace(' ', '_').replace("'", '')
                        new_features_dict[feature_key] = feature
            
            # Detect new class features
            for feature_key, feature_data in new_features_dict.items():
                if feature_key not in old_features_dict:
                    feature_name = feature_data.get('name', 'Unknown Feature')
                    source = feature_data.get('source_name', 'Unknown Class')
                    
                    description = f"Gained class feature: {feature_name} ({source})"
                    
                    change = self._create_field_change(
                        field_path=f'features.class_features.{feature_key}',
                        old_value=None,
                        new_value=feature_data,
                        change_type=ChangeType.ADDED,
                        category=ChangeCategory.FEATURES,
                        description=description
                    )
                    
                    # Add enhanced metadata
                    change.metadata.update({
                        'feature_name': feature_name,
                        'source_class': source,
                        'feature_type': 'class_feature',
                        'causation_trigger': 'level_progression'
                    })
                    
                    changes.append(change)
                    self.logger.debug(f"Detected new class feature: {feature_name}")
            
            # Detect removed class features (rare but possible)
            for feature_key, feature_data in old_features_dict.items():
                if feature_key not in new_features_dict:
                    feature_name = feature_data.get('name', 'Unknown Feature')
                    source = feature_data.get('source_name', 'Unknown Class')
                    
                    description = f"Lost class feature: {feature_name} ({source})"
                    
                    change = self._create_field_change(
                        field_path=f'features.class_features.{feature_key}',
                        old_value=feature_data,
                        new_value=None,
                        change_type=ChangeType.REMOVED,
                        category=ChangeCategory.FEATURES,
                        description=description
                    )
                    
                    changes.append(change)
                    self.logger.debug(f"Detected lost class feature: {feature_name}")
            
            self.logger.debug(f"Detected {len(changes)} class feature changes")
            
        except Exception as e:
            self.logger.error(f"Error detecting class feature changes: {e}", exc_info=True)
        
        return changes