"""
Consolidated Change Detectors

All change detectors in one module using duck typing and simple base classes.
This follows the Pythonic approach of consolidating related functionality
instead of splitting into many small files.
"""

import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass
import fnmatch
import re

from .models import FieldChange, ChangeType, ChangePriority, ChangeCategory

logger = logging.getLogger(__name__)


class DetectorBase:
    """
    Simple base class for all detectors using duck typing.
    
    Uses diagnostic errors instead of abstract methods to provide
    better error messages when methods are not implemented.
    """
    
    def __init__(self, name: str, supported_categories: List[ChangeCategory] = None):
        self.name = name
        self.supported_categories = supported_categories or []
        self.logger = logging.getLogger(f"{self.__class__.__name__}")
    
    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                      context: Dict[str, Any]) -> List[FieldChange]:
        """
        Detect changes between old and new data.
        
        Subclasses should implement this method. Using diagnostic error
        instead of abstract method for better error messages.
        """
        raise NotImplementedError(
            f"Detector '{self.name}' must implement detect_changes() method. "
            f"This detector should handle categories: {self.supported_categories}"
        )
    
    def can_detect(self, field_path: str) -> bool:
        """Check if this detector can handle a specific field path."""
        # Default implementation - can be overridden
        return True
    
    def get_priority(self) -> int:
        """Get detector priority (lower = higher priority)."""
        return 100  # Default priority


class BasicInfoDetector(DetectorBase):
    """Detects changes in basic character information."""
    
    def __init__(self):
        super().__init__("basic_info", [ChangeCategory.BASIC_INFO])
        self.tracked_fields = {
            'name': ChangePriority.HIGH,
            'level': ChangePriority.CRITICAL,
            'class': ChangePriority.HIGH,
            'race': ChangePriority.HIGH,
            'background': ChangePriority.MEDIUM,
            'alignment': ChangePriority.MEDIUM,
            'experience_points': ChangePriority.MEDIUM,
            'hit_points': ChangePriority.HIGH,
            'armor_class': ChangePriority.HIGH
        }
    
    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                      context: Dict[str, Any]) -> List[FieldChange]:
        """Detect basic info changes."""
        changes = []
        
        # Check character info section (v6.0.0 data structure)
        old_basic = old_data.get('character_info', {})
        new_basic = new_data.get('character_info', {})
        
        for field, priority in self.tracked_fields.items():
            old_value = old_basic.get(field)
            new_value = new_basic.get(field)
            
            if old_value != new_value:
                change_type = self._determine_change_type(old_value, new_value)
                changes.append(FieldChange(
                    field_path=f'character_info.{field}',
                    old_value=old_value,
                    new_value=new_value,
                    change_type=change_type,
                    priority=priority,
                    category=ChangeCategory.BASIC_INFO,
                    description=self._get_change_description(field, old_value, new_value)
                ))
        
        return changes
    
    def _determine_change_type(self, old_value: Any, new_value: Any) -> ChangeType:
        """Determine the type of change."""
        if old_value is None and new_value is not None:
            return ChangeType.ADDED
        elif old_value is not None and new_value is None:
            return ChangeType.REMOVED
        elif isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
            return ChangeType.INCREMENTED if new_value > old_value else ChangeType.DECREMENTED
        else:
            return ChangeType.MODIFIED
    
    def _get_change_description(self, field: str, old_value: Any, new_value: Any) -> str:
        """Get human-readable description of the change."""
        if field == 'level':
            return f"Character level changed from {old_value} to {new_value}"
        elif field == 'name':
            return f"Character renamed from '{old_value}' to '{new_value}'"
        elif field == 'hit_points':
            return f"Hit points changed from {old_value} to {new_value}"
        else:
            return f"{field.title()} changed from {old_value} to {new_value}"


class AbilityScoreDetector(DetectorBase):
    """Detects changes in ability scores and modifiers."""
    
    def __init__(self):
        super().__init__("ability_scores", [ChangeCategory.ABILITIES])
        self.abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
    
    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                      context: Dict[str, Any]) -> List[FieldChange]:
        """Detect ability score changes."""
        changes = []
        
        old_abilities = old_data.get('ability_scores', {})
        new_abilities = new_data.get('ability_scores', {})
        
        for ability in self.abilities:
            old_score = old_abilities.get(ability, 10)
            new_score = new_abilities.get(ability, 10)
            
            if old_score != new_score:
                change_type = ChangeType.INCREMENTED if new_score > old_score else ChangeType.DECREMENTED
                priority = ChangePriority.HIGH if abs(new_score - old_score) > 2 else ChangePriority.MEDIUM
                
                changes.append(FieldChange(
                    field_path=f'ability_scores.{ability}',
                    old_value=old_score,
                    new_value=new_score,
                    change_type=change_type,
                    priority=priority,
                    category=ChangeCategory.ABILITIES,
                    description=f"{ability.title()} changed from {old_score} to {new_score}"
                ))
        
        return changes


class SkillDetector(DetectorBase):
    """Detects changes in skill proficiencies and bonuses with enhanced format support."""
    
    def __init__(self):
        super().__init__("skills", [ChangeCategory.SKILLS])
    
    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                      context: Dict[str, Any]) -> List[FieldChange]:
        """Detect skill changes with support for enhanced skill bonus format."""
        changes = []
        
        # Try enhanced format first (from proficiencies.skill_bonuses)
        old_proficiencies = old_data.get('proficiencies', {})
        new_proficiencies = new_data.get('proficiencies', {})
        
        old_skill_bonuses = old_proficiencies.get('skill_bonuses', [])
        new_skill_bonuses = new_proficiencies.get('skill_bonuses', [])
        
        if old_skill_bonuses or new_skill_bonuses:
            # Handle enhanced format
            changes.extend(self._detect_enhanced_skill_changes(old_skill_bonuses, new_skill_bonuses))
        else:
            # Fallback to legacy format
            changes.extend(self._detect_legacy_skill_changes(old_data, new_data))
        
        return changes
    
    def _detect_enhanced_skill_changes(self, old_skill_bonuses: List[Dict[str, Any]], 
                                     new_skill_bonuses: List[Dict[str, Any]]) -> List[FieldChange]:
        """Detect changes in enhanced skill bonus format."""
        changes = []
        
        # Convert lists to dictionaries for easier comparison
        old_skills = {skill.get('skill_name', ''): skill for skill in old_skill_bonuses if isinstance(skill, dict)}
        new_skills = {skill.get('skill_name', ''): skill for skill in new_skill_bonuses if isinstance(skill, dict)}
        
        # Get all skill names from both datasets
        all_skills = set(old_skills.keys()) | set(new_skills.keys())
        
        for skill_name in all_skills:
            if not skill_name:
                continue
                
            old_skill_data = old_skills.get(skill_name, {})
            new_skill_data = new_skills.get(skill_name, {})
            
            # Check proficiency changes
            old_proficient = old_skill_data.get('is_proficient', False)
            new_proficient = new_skill_data.get('is_proficient', False)
            
            if old_proficient != new_proficient:
                change_type = ChangeType.ADDED if new_proficient else ChangeType.REMOVED
                changes.append(FieldChange(
                    field_path=f'proficiencies.skill_bonuses.{skill_name}.is_proficient',
                    old_value=old_proficient,
                    new_value=new_proficient,
                    change_type=change_type,
                    priority=ChangePriority.MEDIUM,
                    category=ChangeCategory.SKILLS,
                    description=f"{'Gained' if new_proficient else 'Lost'} proficiency in {skill_name.replace('_', ' ').title()}"
                ))
            
            # Check expertise changes
            old_expertise = old_skill_data.get('has_expertise', False)
            new_expertise = new_skill_data.get('has_expertise', False)
            
            if old_expertise != new_expertise:
                change_type = ChangeType.ADDED if new_expertise else ChangeType.REMOVED
                changes.append(FieldChange(
                    field_path=f'proficiencies.skill_bonuses.{skill_name}.has_expertise',
                    old_value=old_expertise,
                    new_value=new_expertise,
                    change_type=change_type,
                    priority=ChangePriority.HIGH,
                    category=ChangeCategory.SKILLS,
                    description=f"{'Gained' if new_expertise else 'Lost'} expertise in {skill_name.replace('_', ' ').title()}"
                ))
            
            # Check total bonus changes
            old_bonus = old_skill_data.get('total_bonus', 0)
            new_bonus = new_skill_data.get('total_bonus', 0)
            
            if old_bonus != new_bonus:
                change_type = ChangeType.INCREMENTED if new_bonus > old_bonus else ChangeType.DECREMENTED
                delta = new_bonus - old_bonus
                changes.append(FieldChange(
                    field_path=f'proficiencies.skill_bonuses.{skill_name}.total_bonus',
                    old_value=old_bonus,
                    new_value=new_bonus,
                    change_type=change_type,
                    priority=ChangePriority.LOW,
                    category=ChangeCategory.SKILLS,
                    description=f"{skill_name.replace('_', ' ').title()} bonus changed by {delta:+d} ({old_bonus:+d} → {new_bonus:+d})"
                ))
        
        return changes
    
    def _detect_legacy_skill_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> List[FieldChange]:
        """Detect changes in legacy skill format."""
        changes = []
        
        old_skills = old_data.get('skills', {})
        new_skills = new_data.get('skills', {})
        
        # Get all skill names from both datasets
        all_skills = set(old_skills.keys()) | set(new_skills.keys())
        
        for skill in all_skills:
            old_skill_data = old_skills.get(skill, {})
            new_skill_data = new_skills.get(skill, {})
            
            # Check proficiency changes
            old_proficient = old_skill_data.get('proficient', False)
            new_proficient = new_skill_data.get('proficient', False)
            
            if old_proficient != new_proficient:
                change_type = ChangeType.ADDED if new_proficient else ChangeType.REMOVED
                changes.append(FieldChange(
                    field_path=f'skills.{skill}.proficient',
                    old_value=old_proficient,
                    new_value=new_proficient,
                    change_type=change_type,
                    priority=ChangePriority.MEDIUM,
                    category=ChangeCategory.SKILLS,
                    description=f"{'Gained' if new_proficient else 'Lost'} proficiency in {skill}"
                ))
            
            # Check bonus changes
            old_bonus = old_skill_data.get('bonus', 0)
            new_bonus = new_skill_data.get('bonus', 0)
            
            if old_bonus != new_bonus:
                change_type = ChangeType.INCREMENTED if new_bonus > old_bonus else ChangeType.DECREMENTED
                changes.append(FieldChange(
                    field_path=f'skills.{skill}.bonus',
                    old_value=old_bonus,
                    new_value=new_bonus,
                    change_type=change_type,
                    priority=ChangePriority.LOW,
                    category=ChangeCategory.SKILLS,
                    description=f"{skill.title()} bonus changed from {old_bonus:+d} to {new_bonus:+d}"
                ))
        
        return changes


class CombatDetector(DetectorBase):
    """Detects changes in combat-related data including weapon attacks and class resources."""
    
    def __init__(self):
        super().__init__("combat", [ChangeCategory.COMBAT])
    
    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                      context: Dict[str, Any]) -> List[FieldChange]:
        """Detect combat-related changes."""
        changes = []
        
        # Check weapon attacks
        changes.extend(self._detect_weapon_attack_changes(old_data, new_data))
        
        # Check class resources
        changes.extend(self._detect_class_resource_changes(old_data, new_data))
        
        # Check combat stats
        changes.extend(self._detect_combat_stat_changes(old_data, new_data))
        
        return changes
    
    def _detect_weapon_attack_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> List[FieldChange]:
        """Detect changes in weapon attacks."""
        changes = []
        
        old_combat = old_data.get('combat', {})
        new_combat = new_data.get('combat', {})
        
        old_weapon_attacks = old_combat.get('weapon_attacks', [])
        new_weapon_attacks = new_combat.get('weapon_attacks', [])
        
        # Convert to dictionaries for easier comparison
        old_attacks = {attack.get('name', ''): attack for attack in old_weapon_attacks if isinstance(attack, dict)}
        new_attacks = {attack.get('name', ''): attack for attack in new_weapon_attacks if isinstance(attack, dict)}
        
        all_weapons = set(old_attacks.keys()) | set(new_attacks.keys())
        
        for weapon_name in all_weapons:
            if not weapon_name:
                continue
                
            old_attack = old_attacks.get(weapon_name, {})
            new_attack = new_attacks.get(weapon_name, {})
            
            if not old_attack and new_attack:
                # New weapon attack
                changes.append(FieldChange(
                    field_path=f'combat.weapon_attacks.{weapon_name}',
                    old_value=None,
                    new_value=new_attack,
                    change_type=ChangeType.ADDED,
                    priority=ChangePriority.MEDIUM,
                    category=ChangeCategory.COMBAT,
                    description=f"Added weapon attack: {weapon_name}"
                ))
            elif old_attack and not new_attack:
                # Removed weapon attack
                changes.append(FieldChange(
                    field_path=f'combat.weapon_attacks.{weapon_name}',
                    old_value=old_attack,
                    new_value=None,
                    change_type=ChangeType.REMOVED,
                    priority=ChangePriority.MEDIUM,
                    category=ChangeCategory.COMBAT,
                    description=f"Removed weapon attack: {weapon_name}"
                ))
            elif old_attack and new_attack:
                # Check for changes in attack bonus
                old_bonus = old_attack.get('attack_bonus', 0)
                new_bonus = new_attack.get('attack_bonus', 0)
                
                if old_bonus != new_bonus:
                    change_type = ChangeType.INCREMENTED if new_bonus > old_bonus else ChangeType.DECREMENTED
                    delta = new_bonus - old_bonus
                    changes.append(FieldChange(
                        field_path=f'combat.weapon_attacks.{weapon_name}.attack_bonus',
                        old_value=old_bonus,
                        new_value=new_bonus,
                        change_type=change_type,
                        priority=ChangePriority.MEDIUM,
                        category=ChangeCategory.COMBAT,
                        description=f"{weapon_name} attack bonus changed by {delta:+d} ({old_bonus:+d} → {new_bonus:+d})"
                    ))
                
                # Check for changes in damage
                old_damage_dice = old_attack.get('damage_dice', '')
                new_damage_dice = new_attack.get('damage_dice', '')
                old_damage_modifier = old_attack.get('damage_modifier', 0)
                new_damage_modifier = new_attack.get('damage_modifier', 0)
                
                if old_damage_dice != new_damage_dice or old_damage_modifier != new_damage_modifier:
                    old_damage_str = f"{old_damage_dice}+{old_damage_modifier}" if old_damage_modifier > 0 else old_damage_dice
                    new_damage_str = f"{new_damage_dice}+{new_damage_modifier}" if new_damage_modifier > 0 else new_damage_dice
                    
                    changes.append(FieldChange(
                        field_path=f'combat.weapon_attacks.{weapon_name}.damage',
                        old_value=old_damage_str,
                        new_value=new_damage_str,
                        change_type=ChangeType.MODIFIED,
                        priority=ChangePriority.LOW,
                        category=ChangeCategory.COMBAT,
                        description=f"{weapon_name} damage changed from {old_damage_str} to {new_damage_str}"
                    ))
        
        return changes
    
    def _detect_class_resource_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> List[FieldChange]:
        """Detect changes in class resources."""
        changes = []
        
        old_resources = old_data.get('resources', {})
        new_resources = new_data.get('resources', {})
        
        old_class_resources = old_resources.get('class_resources', [])
        new_class_resources = new_resources.get('class_resources', [])
        
        # Convert to dictionaries for easier comparison
        old_resources_dict = {}
        for resource in old_class_resources:
            if isinstance(resource, dict):
                key = f"{resource.get('class_name', '')}.{resource.get('resource_name', '')}"
                old_resources_dict[key] = resource
        
        new_resources_dict = {}
        for resource in new_class_resources:
            if isinstance(resource, dict):
                key = f"{resource.get('class_name', '')}.{resource.get('resource_name', '')}"
                new_resources_dict[key] = resource
        
        all_resource_keys = set(old_resources_dict.keys()) | set(new_resources_dict.keys())
        
        for resource_key in all_resource_keys:
            if not resource_key or resource_key == '.':
                continue
                
            old_resource = old_resources_dict.get(resource_key, {})
            new_resource = new_resources_dict.get(resource_key, {})
            
            if not old_resource and new_resource:
                # New class resource
                resource_name = new_resource.get('resource_name', 'Unknown Resource')
                class_name = new_resource.get('class_name', 'Unknown Class')
                changes.append(FieldChange(
                    field_path=f'resources.class_resources.{resource_key}',
                    old_value=None,
                    new_value=new_resource,
                    change_type=ChangeType.ADDED,
                    priority=ChangePriority.HIGH,
                    category=ChangeCategory.COMBAT,
                    description=f"Gained {class_name} resource: {resource_name}"
                ))
            elif old_resource and not new_resource:
                # Removed class resource
                resource_name = old_resource.get('resource_name', 'Unknown Resource')
                class_name = old_resource.get('class_name', 'Unknown Class')
                changes.append(FieldChange(
                    field_path=f'resources.class_resources.{resource_key}',
                    old_value=old_resource,
                    new_value=None,
                    change_type=ChangeType.REMOVED,
                    priority=ChangePriority.HIGH,
                    category=ChangeCategory.COMBAT,
                    description=f"Lost {class_name} resource: {resource_name}"
                ))
            elif old_resource and new_resource:
                # Check for changes in resource maximum
                old_maximum = old_resource.get('maximum', 0)
                new_maximum = new_resource.get('maximum', 0)
                
                if old_maximum != new_maximum:
                    change_type = ChangeType.INCREMENTED if new_maximum > old_maximum else ChangeType.DECREMENTED
                    resource_name = new_resource.get('resource_name', 'Unknown Resource')
                    changes.append(FieldChange(
                        field_path=f'resources.class_resources.{resource_key}.maximum',
                        old_value=old_maximum,
                        new_value=new_maximum,
                        change_type=change_type,
                        priority=ChangePriority.MEDIUM,
                        category=ChangeCategory.COMBAT,
                        description=f"{resource_name} maximum changed from {old_maximum} to {new_maximum}"
                    ))
                
                # Check for changes in current/used amounts (less important)
                old_used = old_resource.get('used', 0)
                new_used = new_resource.get('used', 0)
                
                if old_used != new_used:
                    change_type = ChangeType.INCREMENTED if new_used > old_used else ChangeType.DECREMENTED
                    resource_name = new_resource.get('resource_name', 'Unknown Resource')
                    delta = new_used - old_used
                    changes.append(FieldChange(
                        field_path=f'resources.class_resources.{resource_key}.used',
                        old_value=old_used,
                        new_value=new_used,
                        change_type=change_type,
                        priority=ChangePriority.LOW,
                        category=ChangeCategory.COMBAT,
                        description=f"{resource_name} usage changed by {delta:+d} ({old_used} → {new_used} used)"
                    ))
        
        return changes
    
    def _detect_combat_stat_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> List[FieldChange]:
        """Detect changes in basic combat stats."""
        changes = []
        
        old_combat = old_data.get('combat', {})
        new_combat = new_data.get('combat', {})
        
        # Check armor class
        old_ac = old_combat.get('armor_class', 10)
        new_ac = new_combat.get('armor_class', 10)
        
        # Handle both integer and dict formats for AC
        if isinstance(old_ac, dict):
            old_ac = old_ac.get('total', old_ac.get('armor_class', 10))
        if isinstance(new_ac, dict):
            new_ac = new_ac.get('total', new_ac.get('armor_class', 10))
        
        if old_ac != new_ac:
            change_type = ChangeType.INCREMENTED if new_ac > old_ac else ChangeType.DECREMENTED
            delta = new_ac - old_ac
            changes.append(FieldChange(
                field_path='combat.armor_class',
                old_value=old_ac,
                new_value=new_ac,
                change_type=change_type,
                priority=ChangePriority.HIGH,
                category=ChangeCategory.COMBAT,
                description=f"Armor Class changed by {delta:+d} ({old_ac} → {new_ac})"
            ))
        
        # Check hit points
        old_hp = old_combat.get('hit_points', {})
        new_hp = new_combat.get('hit_points', {})
        
        if isinstance(old_hp, dict) and isinstance(new_hp, dict):
            old_max_hp = old_hp.get('maximum', 0)
            new_max_hp = new_hp.get('maximum', 0)
            
            if old_max_hp != new_max_hp:
                change_type = ChangeType.INCREMENTED if new_max_hp > old_max_hp else ChangeType.DECREMENTED
                delta = new_max_hp - old_max_hp
                changes.append(FieldChange(
                    field_path='combat.hit_points.maximum',
                    old_value=old_max_hp,
                    new_value=new_max_hp,
                    change_type=change_type,
                    priority=ChangePriority.HIGH,
                    category=ChangeCategory.COMBAT,
                    description=f"Maximum HP changed by {delta:+d} ({old_max_hp} → {new_max_hp})"
                ))
        
        return changes


class SpellDetector(DetectorBase):
    """Detects changes in spells and spellcasting."""
    
    def __init__(self):
        super().__init__("spells", [ChangeCategory.SPELLS])
    
    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                      context: Dict[str, Any]) -> List[FieldChange]:
        """Detect spell changes."""
        changes = []
        
        old_spells = old_data.get('spells', {})
        new_spells = new_data.get('spells', {})
        
        # Check spell slots (in spellcasting section)
        old_spellcasting = old_data.get('spellcasting', {})
        new_spellcasting = new_data.get('spellcasting', {})
        old_slots = old_spellcasting.get('spell_slots', [])
        new_slots = new_spellcasting.get('spell_slots', [])
        
        for level in range(len(max(old_slots, new_slots, key=len))):
            # Skip level 0 (cantrips) - they don't have spell slots, they're cast at will
            if level == 0:
                continue
                
            old_slot_count = old_slots[level] if level < len(old_slots) else 0
            new_slot_count = new_slots[level] if level < len(new_slots) else 0
            
            if old_slot_count != new_slot_count:
                change_type = ChangeType.INCREMENTED if new_slot_count > old_slot_count else ChangeType.DECREMENTED
                priority = ChangePriority.HIGH if level <= 2 else ChangePriority.MEDIUM  # Low level slots are high priority
                
                changes.append(FieldChange(
                    field_path=f'spellcasting.spell_slots.{level}',
                    old_value=old_slot_count,
                    new_value=new_slot_count,
                    change_type=change_type,
                    priority=priority,
                    category=ChangeCategory.SPELLS,
                    description=f"Level {level} spell slots changed from {old_slot_count} to {new_slot_count}"
                ))
        
        # Check known spells - handle new data structure with spells organized by source
        old_known = self._extract_all_spells(old_spells)
        new_known = self._extract_all_spells(new_spells)
        
        # Added spells
        for spell_name in new_known - old_known:
            # Find which source the spell was added to
            source = self._find_spell_source(spell_name, new_data.get('spells', {}))
            changes.append(FieldChange(
                field_path=f'spells.{source}.{spell_name}',
                old_value=None,
                new_value=spell_name,
                change_type=ChangeType.ADDED,
                priority=ChangePriority.HIGH,
                category=ChangeCategory.SPELLS,
                description=f"Learned spell: {spell_name}" + (f" ({source})" if source else "")
            ))
        
        # Removed spells
        for spell_name in old_known - new_known:
            # Find which source the spell was removed from
            source = self._find_spell_source(spell_name, old_data.get('spells', {}))
            changes.append(FieldChange(
                field_path=f'spells.{source}.{spell_name}',
                old_value=spell_name,
                new_value=None,
                change_type=ChangeType.REMOVED,
                priority=ChangePriority.HIGH,
                category=ChangeCategory.SPELLS,
                description=f"Forgot spell: {spell_name}" + (f" ({source})" if source else "")
            ))
        
        # Check spell counts for more detailed change detection
        old_spell_counts = old_data.get('spellcasting', {}).get('spell_counts', {})
        new_spell_counts = new_data.get('spellcasting', {}).get('spell_counts', {})
        
        # Check for total count changes
        old_total = old_spell_counts.get('total', 0)
        new_total = new_spell_counts.get('total', 0)
        
        if old_total != new_total and len(old_known) > 0 and len(new_known) > 0:
            # Only add count change if we don't already have specific spell changes
            if not (new_known - old_known) and not (old_known - new_known):
                change_type = ChangeType.INCREMENTED if new_total > old_total else ChangeType.DECREMENTED
                changes.append(FieldChange(
                    field_path='spellcasting.spell_counts.total',
                    old_value=old_total,
                    new_value=new_total,
                    change_type=change_type,
                    priority=ChangePriority.MEDIUM,
                    category=ChangeCategory.SPELLS,
                    description=f"Total spells: {old_total} → {new_total}"
                ))
        
        return changes
    
    def _extract_all_spells(self, spells_data: Dict[str, Any]) -> set:
        """Extract all spell names from the spell data structure."""
        all_spells = set()
        
        # Handle new structure where spells are organized by source (Wizard, Cleric, etc.)
        for source, spell_list in spells_data.items():
            if isinstance(spell_list, list):
                for spell in spell_list:
                    if isinstance(spell, dict):
                        spell_name = spell.get('name', '')
                        if spell_name:
                            all_spells.add(spell_name)
        
        return all_spells
    
    def _find_spell_source(self, spell_name: str, spells_data: Dict[str, Any]) -> str:
        """Find which source (Wizard, Cleric, etc.) a spell belongs to."""
        for source, spell_list in spells_data.items():
            if isinstance(spell_list, list):
                for spell in spell_list:
                    if isinstance(spell, dict) and spell.get('name') == spell_name:
                        return source
        return "Unknown"


class EquipmentDetector(DetectorBase):
    """Detects changes in equipment and inventory."""
    
    def __init__(self):
        super().__init__("equipment", [ChangeCategory.EQUIPMENT, ChangeCategory.INVENTORY])
    
    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                      context: Dict[str, Any]) -> List[FieldChange]:
        """Detect equipment changes."""
        changes = []
        
        old_equipment = old_data.get('equipment', [])
        new_equipment = new_data.get('equipment', [])
        
        # Extract equipment items from the data structure
        old_equipment_items = self._extract_equipment_items(old_equipment)
        new_equipment_items = self._extract_equipment_items(new_equipment)
        
        # Create item name -> item mapping for easier comparison
        old_items = {item.get('name', ''): item for item in old_equipment_items}
        new_items = {item.get('name', ''): item for item in new_equipment_items}
        
        all_items = set(old_items.keys()) | set(new_items.keys())
        
        for item_name in all_items:
            old_item = old_items.get(item_name)
            new_item = new_items.get(item_name)
            
            if old_item is None:
                # Item added
                changes.append(FieldChange(
                    field_path=f'equipment.{item_name}',
                    old_value=None,
                    new_value=new_item,
                    change_type=ChangeType.ADDED,
                    priority=ChangePriority.MEDIUM,
                    category=ChangeCategory.EQUIPMENT,
                    description=f"Added item: {item_name}"
                ))
            elif new_item is None:
                # Item removed
                changes.append(FieldChange(
                    field_path=f'equipment.{item_name}',
                    old_value=old_item,
                    new_value=None,
                    change_type=ChangeType.REMOVED,
                    priority=ChangePriority.MEDIUM,
                    category=ChangeCategory.EQUIPMENT,
                    description=f"Removed item: {item_name}"
                ))
            else:
                # Item modified - check quantity, equipped status, etc.
                old_quantity = old_item.get('quantity', 1)
                new_quantity = new_item.get('quantity', 1)
                
                if old_quantity != new_quantity:
                    change_type = ChangeType.INCREMENTED if new_quantity > old_quantity else ChangeType.DECREMENTED
                    changes.append(FieldChange(
                        field_path=f'equipment.{item_name}.quantity',
                        old_value=old_quantity,
                        new_value=new_quantity,
                        change_type=change_type,
                        priority=ChangePriority.LOW,
                        category=ChangeCategory.EQUIPMENT,
                        description=f"{item_name} quantity changed from {old_quantity} to {new_quantity}"
                    ))
                
                # Check equipped status
                old_equipped = old_item.get('equipped', False)
                new_equipped = new_item.get('equipped', False)
                
                if old_equipped != new_equipped:
                    change_type = ChangeType.ADDED if new_equipped else ChangeType.REMOVED
                    changes.append(FieldChange(
                        field_path=f'equipment.{item_name}.equipped',
                        old_value=old_equipped,
                        new_value=new_equipped,
                        change_type=change_type,
                        priority=ChangePriority.MEDIUM,
                        category=ChangeCategory.EQUIPMENT,
                        description=f"{'Equipped' if new_equipped else 'Unequipped'} {item_name}"
                    ))
        
        return changes
    
    def _extract_equipment_items(self, equipment_data: Any) -> List[Dict[str, Any]]:
        """
        Extract equipment items from the data structure.
        
        Handles both old format (list of items) and new format (dict with sub-sections).
        """
        if isinstance(equipment_data, list):
            # Old format: equipment is a list of items
            return equipment_data
        elif isinstance(equipment_data, dict):
            # New format: equipment is a dict with sub-sections
            items = []
            
            # Extract from known sub-sections
            if 'basic_equipment' in equipment_data:
                basic_equipment = equipment_data['basic_equipment']
                if isinstance(basic_equipment, list):
                    items.extend(basic_equipment)
            
            if 'enhanced_equipment' in equipment_data:
                enhanced_equipment = equipment_data['enhanced_equipment']
                if isinstance(enhanced_equipment, list):
                    items.extend(enhanced_equipment)
            
            # If no sub-sections found, maybe it's still the old format stored as dict
            # Check if keys look like item names rather than section names
            if not items and equipment_data:
                # Try to identify if this is equipment items stored as dict
                sample_key = next(iter(equipment_data.keys()))
                sample_value = equipment_data[sample_key]
                if isinstance(sample_value, dict) and 'name' in sample_value:
                    # This looks like old format items stored as dict
                    items = list(equipment_data.values())
            
            return items
        else:
            # Unknown format, return empty list
            return []


class FeatureDetector(DetectorBase):
    """Detects changes in class features, racial traits, and feats."""
    
    def __init__(self):
        super().__init__("features", [ChangeCategory.FEATURES])
    
    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                      context: Dict[str, Any]) -> List[FieldChange]:
        """Detect feature changes."""
        changes = []
        
        # Check class features
        old_features = old_data.get('class_features', [])
        new_features = new_data.get('class_features', [])
        
        changes.extend(self._detect_feature_list_changes(
            old_features, new_features, 'class_features', 'class feature'
        ))
        
        # Check racial traits
        old_traits = old_data.get('racial_traits', [])
        new_traits = new_data.get('racial_traits', [])
        
        changes.extend(self._detect_feature_list_changes(
            old_traits, new_traits, 'racial_traits', 'racial trait'
        ))
        
        # Check feats
        old_feats = old_data.get('feats', [])
        new_feats = new_data.get('feats', [])
        
        changes.extend(self._detect_feature_list_changes(
            old_feats, new_feats, 'feats', 'feat'
        ))
        
        return changes
    
    def _detect_feature_list_changes(self, old_list: List[Dict], new_list: List[Dict], 
                                   field_path: str, feature_type: str) -> List[FieldChange]:
        """Detect changes in a list of features."""
        changes = []
        
        old_names = set(feature.get('name', '') for feature in old_list)
        new_names = set(feature.get('name', '') for feature in new_list)
        
        # Added features
        for feature_name in new_names - old_names:
            changes.append(FieldChange(
                field_path=f'{field_path}.{feature_name}',
                old_value=None,
                new_value=feature_name,
                change_type=ChangeType.ADDED,
                priority=ChangePriority.HIGH,
                category=ChangeCategory.FEATURES,
                description=f"Gained {feature_type}: {feature_name}"
            ))
        
        # Removed features
        for feature_name in old_names - new_names:
            changes.append(FieldChange(
                field_path=f'{field_path}.{feature_name}',
                old_value=feature_name,
                new_value=None,
                change_type=ChangeType.REMOVED,
                priority=ChangePriority.HIGH,
                category=ChangeCategory.FEATURES,
                description=f"Lost {feature_type}: {feature_name}"
            ))
        
        return changes


class CompositeDetector(DetectorBase):
    """
    Composite detector that coordinates multiple detectors.
    
    Uses dependency maps instead of constructor injection bloat.
    """
    
    def __init__(self, detector_map: Dict[str, DetectorBase] = None):
        super().__init__("composite", [])
        self.detector_map = detector_map or self._create_default_detectors()
        self.execution_order = self._calculate_execution_order()
    
    def _create_default_detectors(self) -> Dict[str, DetectorBase]:
        """Create default set of detectors using dependency map."""
        return {
            'basic_info': BasicInfoDetector(),
            'ability_scores': AbilityScoreDetector(),
            'skills': SkillDetector(),
            'combat': CombatDetector(),
            'spells': SpellDetector(),
            'equipment': EquipmentDetector(),
            'features': FeatureDetector()
        }
    
    def _calculate_execution_order(self) -> List[str]:
        """Calculate execution order based on detector priorities."""
        return sorted(self.detector_map.keys(), 
                     key=lambda name: self.detector_map[name].get_priority())
    
    def detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any], 
                      context: Dict[str, Any]) -> List[FieldChange]:
        """Detect changes using all registered detectors."""
        all_changes = []
        
        for detector_name in self.execution_order:
            detector = self.detector_map[detector_name]
            
            try:
                changes = detector.detect_changes(old_data, new_data, context)
                all_changes.extend(changes)
                self.logger.debug(f"Detector '{detector_name}' found {len(changes)} changes")
                
                # Debug: Log individual detector changes
                if changes:
                    for change in changes:
                        self.logger.debug(f"  [{detector_name}] {change.field_path}: {change.old_value} → {change.new_value}")
            except Exception as e:
                self.logger.error(f"Error in detector '{detector_name}': {e}")
                # Continue with other detectors instead of failing completely
        
        self.logger.debug(f"CompositeDetector total: {len(all_changes)} changes")
        return all_changes
    
    def register_detector(self, name: str, detector: DetectorBase):
        """Register a new detector."""
        self.detector_map[name] = detector
        self.execution_order = self._calculate_execution_order()
        self.logger.info(f"Registered detector: {name}")
    
    def unregister_detector(self, name: str):
        """Unregister a detector."""
        if name in self.detector_map:
            del self.detector_map[name]
            self.execution_order = self._calculate_execution_order()
            self.logger.info(f"Unregistered detector: {name}")
    
    def get_detector_status(self) -> Dict[str, Any]:
        """Get status of all detectors."""
        return {
            'total_detectors': len(self.detector_map),
            'execution_order': self.execution_order,
            'detector_types': list(self.detector_map.keys())
        }


# Factory function for creating detectors (simple approach)
def create_detector(detector_type: str, **kwargs) -> DetectorBase:
    """
    Factory function for creating detectors.
    
    Uses simple factory pattern instead of complex interfaces.
    """
    detector_types = {
        'basic_info': BasicInfoDetector,
        'ability_scores': AbilityScoreDetector,
        'skills': SkillDetector,
        'combat': CombatDetector,
        'spells': SpellDetector,
        'equipment': EquipmentDetector,
        'features': FeatureDetector,
        'composite': CompositeDetector
    }
    
    if detector_type not in detector_types:
        available_types = ', '.join(detector_types.keys())
        raise ValueError(
            f"Unknown detector type '{detector_type}'. "
            f"Available types: {available_types}"
        )
    
    detector_class = detector_types[detector_type]
    return detector_class(**kwargs)