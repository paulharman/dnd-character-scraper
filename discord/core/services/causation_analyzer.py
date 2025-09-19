"""
Change Causation Analysis System

Analyzes and tracks the root causes of character changes and their cascading effects.
"""

import logging
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field

from shared.models.change_detection import FieldChange, ChangeType
from discord.core.models.change_log import ChangeCausation, ChangeAttribution

logger = logging.getLogger(__name__)


@dataclass
class CausationRule:
    """Rule for detecting causation patterns."""
    trigger_pattern: str  # Pattern to match the trigger
    affected_fields: List[str]  # Field patterns that are affected
    causation_type: str  # Type of causation
    confidence: float = 1.0  # Confidence in this rule
    
    def matches_trigger(self, field_path: str, old_value: Any, new_value: Any) -> bool:
        """Check if this rule matches a trigger change."""
        import fnmatch
        return fnmatch.fnmatch(field_path, self.trigger_pattern)
    
    def matches_affected_field(self, field_path: str) -> bool:
        """Check if a field is affected by this rule."""
        import fnmatch
        return any(fnmatch.fnmatch(field_path, pattern) for pattern in self.affected_fields)


class ChangeCausationAnalyzer:
    """Analyzes what caused character changes and links related changes."""
    
    def __init__(self):
        self.causation_rules = self._load_causation_rules()
        self.cascade_detectors = self._create_cascade_detectors()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    async def analyze_causation(self, changes: List[FieldChange], 
                              old_data: Dict, new_data: Dict) -> List[ChangeCausation]:
        """Analyze what caused the detected changes."""
        causations = []
        
        try:
            # Detect feat-based causation
            feat_causations = self.detect_feat_causation(changes, new_data)
            causations.extend(feat_causations)
            
            # Detect level progression causation
            level_causations = self.detect_level_progression_causation(changes, old_data, new_data)
            causations.extend(level_causations)
            
            # Detect equipment causation
            equipment_causations = self.detect_equipment_causation(changes, old_data, new_data)
            causations.extend(equipment_causations)
            
            # Detect ability score causation
            ability_causations = self.detect_ability_score_causation(changes, old_data, new_data)
            causations.extend(ability_causations)
            
            # Detect subclass causation
            subclass_causations = self.detect_subclass_causation(changes, old_data, new_data)
            causations.extend(subclass_causations)
            
            # Detect background causation
            background_causations = self.detect_background_causation(changes, old_data, new_data)
            causations.extend(background_causations)
            
            # Detect race/species causation
            race_causations = self.detect_race_species_causation(changes, old_data, new_data)
            causations.extend(race_causations)
            
            # Detect multiclass causation
            multiclass_causations = self.detect_multiclass_causation(changes, old_data, new_data)
            causations.extend(multiclass_causations)
            
            # Link cascading changes
            self._link_cascading_changes(causations, changes)
            
            self.logger.debug(f"Analyzed causation for {len(changes)} changes, found {len(causations)} causation patterns")
            
        except Exception as e:
            self.logger.error(f"Error in causation analysis: {e}", exc_info=True)
        
        return causations
    
    def detect_feat_causation(self, changes: List[FieldChange], character_data: Dict) -> List[ChangeCausation]:
        """Detect changes caused by feat selection."""
        causations = []
        
        try:
            # Look for feat additions
            feat_changes = [c for c in changes if 'feat' in c.field_path.lower()]
            
            for feat_change in feat_changes:
                if feat_change.change_type == ChangeType.ADDED and feat_change.new_value:
                    feat_name = self._extract_feat_name(feat_change.new_value)
                    if feat_name:
                        # Find related changes that could be caused by this feat
                        related_changes = self._find_feat_related_changes(feat_name, changes)
                        
                        if related_changes:
                            causation = ChangeCausation(
                                trigger="feat_selection",
                                trigger_details={
                                    "feat_name": feat_name,
                                    "feat_field": feat_change.field_path,
                                    "feat_data": feat_change.new_value
                                },
                                related_changes=[c.field_path for c in related_changes],
                                cascade_depth=0
                            )
                            causations.append(causation)
                            
                            self.logger.debug(f"Detected feat causation: {feat_name} affects {len(related_changes)} changes")
        
        except Exception as e:
            self.logger.error(f"Error detecting feat causation: {e}", exc_info=True)
        
        return causations
    
    def detect_level_progression_causation(self, changes: List[FieldChange], 
                                         old_data: Dict, new_data: Dict) -> List[ChangeCausation]:
        """Detect changes caused by level progression."""
        causations = []
        
        try:
            # Look for level changes
            level_changes = [c for c in changes if 'level' in c.field_path.lower()]
            
            for level_change in level_changes:
                if (level_change.change_type in [ChangeType.INCREMENTED, ChangeType.MODIFIED] and
                    isinstance(level_change.old_value, int) and isinstance(level_change.new_value, int) and
                    level_change.new_value > level_change.old_value):
                    
                    level_gained = level_change.new_value
                    class_name = self._extract_class_from_level_change(level_change.field_path)
                    
                    # Find changes that could be caused by level progression
                    related_changes = self._find_level_related_changes(level_gained, class_name, changes)
                    
                    if related_changes:
                        causation = ChangeCausation(
                            trigger="level_progression",
                            trigger_details={
                                "level_gained": level_gained,
                                "class": class_name,
                                "old_level": level_change.old_value,
                                "new_level": level_change.new_value
                            },
                            related_changes=[c.field_path for c in related_changes],
                            cascade_depth=0
                        )
                        causations.append(causation)
                        
                        self.logger.debug(f"Detected level progression causation: {class_name} level {level_gained} affects {len(related_changes)} changes")
        
        except Exception as e:
            self.logger.error(f"Error detecting level progression causation: {e}", exc_info=True)
        
        return causations
    
    def detect_equipment_causation(self, changes: List[FieldChange], 
                                 old_data: Dict, new_data: Dict) -> List[ChangeCausation]:
        """Detect changes caused by equipment modifications."""
        causations = []
        
        try:
            # Look for equipment changes
            equipment_changes = [c for c in changes if 'equipment' in c.field_path.lower() or 'item' in c.field_path.lower()]
            
            for equipment_change in equipment_changes:
                if equipment_change.change_type in [ChangeType.ADDED, ChangeType.MODIFIED]:
                    item_name = self._extract_item_name(equipment_change.new_value)
                    if item_name:
                        # Find stat changes that could be caused by this equipment
                        related_changes = self._find_equipment_related_changes(item_name, changes)
                        
                        if related_changes:
                            causation = ChangeCausation(
                                trigger="equipment_change",
                                trigger_details={
                                    "item_name": item_name,
                                    "item_field": equipment_change.field_path,
                                    "change_type": equipment_change.change_type.value,
                                    "item_data": equipment_change.new_value
                                },
                                related_changes=[c.field_path for c in related_changes],
                                cascade_depth=0
                            )
                            causations.append(causation)
                            
                            self.logger.debug(f"Detected equipment causation: {item_name} affects {len(related_changes)} changes")
        
        except Exception as e:
            self.logger.error(f"Error detecting equipment causation: {e}", exc_info=True)
        
        return causations
    
    def detect_ability_score_causation(self, changes: List[FieldChange], 
                                     old_data: Dict, new_data: Dict) -> List[ChangeCausation]:
        """Detect changes caused by ability score modifications."""
        causations = []
        
        try:
            # Look for ability score changes
            ability_changes = [c for c in changes if 'ability_score' in c.field_path.lower() or 
                             any(ability in c.field_path.lower() for ability in 
                                 ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'])]
            
            for ability_change in ability_changes:
                if (ability_change.change_type in [ChangeType.INCREMENTED, ChangeType.DECREMENTED, ChangeType.MODIFIED] and
                    isinstance(ability_change.old_value, int) and isinstance(ability_change.new_value, int)):
                    
                    ability_name = self._extract_ability_name(ability_change.field_path)
                    old_modifier = (ability_change.old_value - 10) // 2
                    new_modifier = (ability_change.new_value - 10) // 2
                    
                    # Only create causation if the modifier changed
                    if old_modifier != new_modifier:
                        # Find changes that could be caused by this ability score change
                        related_changes = self._find_ability_related_changes(ability_name, changes)
                        
                        if related_changes:
                            causation = ChangeCausation(
                                trigger="ability_score_change",
                                trigger_details={
                                    "ability": ability_name,
                                    "old_score": ability_change.old_value,
                                    "new_score": ability_change.new_value,
                                    "old_modifier": old_modifier,
                                    "new_modifier": new_modifier,
                                    "modifier_change": new_modifier - old_modifier
                                },
                                related_changes=[c.field_path for c in related_changes],
                                cascade_depth=1  # Ability changes are often secondary effects
                            )
                            causations.append(causation)
                            
                            self.logger.debug(f"Detected ability score causation: {ability_name} modifier change affects {len(related_changes)} changes")
        
        except Exception as e:
            self.logger.error(f"Error detecting ability score causation: {e}", exc_info=True)
        
        return causations
    
    def detect_subclass_causation(self, changes: List[FieldChange], 
                                old_data: Dict, new_data: Dict) -> List[ChangeCausation]:
        """Detect changes caused by subclass selection."""
        causations = []
        
        try:
            # Look for subclass changes
            subclass_changes = [c for c in changes if 'subclass' in c.field_path.lower()]
            
            for subclass_change in subclass_changes:
                if subclass_change.change_type in [ChangeType.ADDED, ChangeType.MODIFIED]:
                    subclass_name = self._extract_subclass_name(subclass_change.new_value)
                    class_name = self._extract_class_from_subclass_path(subclass_change.field_path)
                    
                    if subclass_name:
                        # Find related changes that could be caused by this subclass
                        related_changes = self._find_subclass_related_changes(subclass_name, class_name, changes)
                        
                        if related_changes:
                            causation = ChangeCausation(
                                trigger="subclass_selection",
                                trigger_details={
                                    "subclass_name": subclass_name,
                                    "class_name": class_name,
                                    "subclass_field": subclass_change.field_path,
                                    "subclass_data": subclass_change.new_value
                                },
                                related_changes=[c.field_path for c in related_changes],
                                cascade_depth=0
                            )
                            causations.append(causation)
                            
                            self.logger.debug(f"Detected subclass causation: {class_name} {subclass_name} affects {len(related_changes)} changes")
        
        except Exception as e:
            self.logger.error(f"Error detecting subclass causation: {e}", exc_info=True)
        
        return causations
    
    def detect_background_causation(self, changes: List[FieldChange], 
                                  old_data: Dict, new_data: Dict) -> List[ChangeCausation]:
        """Detect changes caused by background changes."""
        causations = []
        
        try:
            # Look for background changes
            background_changes = [c for c in changes if 'background' in c.field_path.lower()]
            
            for background_change in background_changes:
                if background_change.change_type in [ChangeType.ADDED, ChangeType.MODIFIED]:
                    background_name = self._extract_background_name(background_change.new_value)
                    
                    if background_name:
                        # Find related changes that could be caused by this background
                        related_changes = self._find_background_related_changes(background_name, changes)
                        
                        if related_changes:
                            causation = ChangeCausation(
                                trigger="background_change",
                                trigger_details={
                                    "background_name": background_name,
                                    "background_field": background_change.field_path,
                                    "background_data": background_change.new_value
                                },
                                related_changes=[c.field_path for c in related_changes],
                                cascade_depth=0
                            )
                            causations.append(causation)
                            
                            self.logger.debug(f"Detected background causation: {background_name} affects {len(related_changes)} changes")
        
        except Exception as e:
            self.logger.error(f"Error detecting background causation: {e}", exc_info=True)
        
        return causations
    
    def detect_race_species_causation(self, changes: List[FieldChange], 
                                    old_data: Dict, new_data: Dict) -> List[ChangeCausation]:
        """Detect changes caused by race/species changes."""
        causations = []
        
        try:
            # Look for race/species changes
            race_changes = [c for c in changes if 'race' in c.field_path.lower() or 'species' in c.field_path.lower()]
            
            for race_change in race_changes:
                if race_change.change_type in [ChangeType.ADDED, ChangeType.MODIFIED]:
                    race_name = self._extract_race_name(race_change.new_value)
                    
                    if race_name:
                        # Find related changes that could be caused by this race/species
                        related_changes = self._find_race_related_changes(race_name, changes)
                        
                        # Only create causation if there are related changes
                        if related_changes:
                            causation = ChangeCausation(
                                trigger="race_change",
                                trigger_details={
                                    "race_name": race_name,
                                    "race_field": race_change.field_path,
                                    "race_data": race_change.new_value
                                },
                                related_changes=[c.field_path for c in related_changes],
                                cascade_depth=0
                            )
                            causations.append(causation)
                            
                            self.logger.debug(f"Detected race causation: {race_name} affects {len(related_changes)} changes")
        
        except Exception as e:
            self.logger.error(f"Error detecting race causation: {e}", exc_info=True)
        
        return causations
    
    def detect_multiclass_causation(self, changes: List[FieldChange], 
                                  old_data: Dict, new_data: Dict) -> List[ChangeCausation]:
        """Detect changes caused by multiclass progression."""
        causations = []
        
        try:
            # Look for class level changes that indicate multiclassing
            class_level_changes = [c for c in changes if 'classes' in c.field_path.lower() and 'level' in c.field_path.lower()]
            
            for level_change in class_level_changes:
                if (level_change.change_type in [ChangeType.INCREMENTED, ChangeType.ADDED] and
                    isinstance(level_change.new_value, int)):
                    
                    class_name = self._extract_class_from_level_change(level_change.field_path)
                    level_gained = level_change.new_value
                    
                    # Check if this is a new class (multiclass) or existing class progression
                    is_new_class = (level_change.change_type == ChangeType.ADDED or 
                                  (isinstance(level_change.old_value, int) and level_change.old_value == 0) or
                                  level_change.old_value is None)
                    
                    if class_name and is_new_class:
                        # Only detect multiclass for truly new classes
                        # Find related changes that could be caused by this multiclass progression
                        related_changes = self._find_multiclass_related_changes(class_name, level_gained, is_new_class, changes)
                        
                        if related_changes:
                            causation = ChangeCausation(
                                trigger="multiclass_progression",
                                trigger_details={
                                    "class_name": class_name,
                                    "level_gained": level_gained,
                                    "old_level": level_change.old_value if isinstance(level_change.old_value, int) else 0,
                                    "is_new_class": is_new_class,
                                    "level_field": level_change.field_path
                                },
                                related_changes=[c.field_path for c in related_changes],
                                cascade_depth=0
                            )
                            causations.append(causation)
                            
                            self.logger.debug(f"Detected multiclass causation: {class_name} level {level_gained} affects {len(related_changes)} changes")
        
        except Exception as e:
            self.logger.error(f"Error detecting multiclass causation: {e}", exc_info=True)
        
        return causations
    
    def _link_cascading_changes(self, causations: List[ChangeCausation], all_changes: List[FieldChange]):
        """Link changes that cascade from primary changes."""
        try:
            # Create a map of field paths to changes for quick lookup
            change_map = {change.field_path: change for change in all_changes}
            
            for causation in causations:
                # For each related change, check if it might cause other changes
                for related_field in causation.related_changes:
                    if related_field in change_map:
                        related_change = change_map[related_field]
                        
                        # Check if this change might cause other changes
                        secondary_effects = self._find_secondary_effects(related_change, all_changes)
                        
                        if secondary_effects:
                            # Add these as deeper cascade effects
                            for effect in secondary_effects:
                                if effect.field_path not in causation.related_changes:
                                    causation.related_changes.append(effect.field_path)
                                    
                            self.logger.debug(f"Linked {len(secondary_effects)} secondary effects to {causation.trigger}")
        
        except Exception as e:
            self.logger.error(f"Error linking cascading changes: {e}", exc_info=True)
    
    def _load_causation_rules(self) -> List[CausationRule]:
        """Load enhanced causation detection rules."""
        return [
            # Feat-based rules
            CausationRule(
                trigger_pattern="*feat*",
                affected_fields=[
                    "*proficienc*", "*skill*", "*ability_score*", "*spell*", "*combat*",
                    "*attack*", "*damage*", "*bonus_action*", "*reaction*", "*passive*"
                ],
                causation_type="feat_selection",
                confidence=0.9
            ),
            
            # Level progression rules
            CausationRule(
                trigger_pattern="*level*",
                affected_fields=[
                    "*hit_point*", "*spell_slot*", "*proficiency_bonus*", "*feature*",
                    "*class_feature*", "*subclass*", "*ability_score*", "*spell*"
                ],
                causation_type="level_progression",
                confidence=0.95
            ),
            
            # Equipment rules
            CausationRule(
                trigger_pattern="*equipment*",
                affected_fields=[
                    "*armor_class*", "*attack_bonus*", "*damage*", "*ability_score*",
                    "*skill*", "*saving_throw*", "*speed*", "*initiative*"
                ],
                causation_type="equipment_change",
                confidence=0.85
            ),
            
            # Ability score rules
            CausationRule(
                trigger_pattern="*ability_score*",
                affected_fields=[
                    "*skill*", "*saving_throw*", "*spell_attack*", "*spell_save_dc*", 
                    "*initiative*", "*passive*", "*modifier*", "*bonus*"
                ],
                causation_type="ability_score_change",
                confidence=0.9
            ),
            
            # Subclass rules
            CausationRule(
                trigger_pattern="*subclass*",
                affected_fields=[
                    "*feature*", "*spell*", "*proficienc*", "*skill*", "*combat*"
                ],
                causation_type="subclass_selection",
                confidence=0.85
            ),
            
            # Background rules
            CausationRule(
                trigger_pattern="*background*",
                affected_fields=[
                    "*proficienc*", "*skill*", "*language*", "*tool*", "*equipment*"
                ],
                causation_type="background_change",
                confidence=0.8
            ),
            
            # Race/Species rules
            CausationRule(
                trigger_pattern="*race*",
                affected_fields=[
                    "*ability_score*", "*proficienc*", "*trait*", "*speed*", "*size*",
                    "*language*", "*skill*", "*resistance*", "*immunity*"
                ],
                causation_type="race_change",
                confidence=0.9
            ),
            
            CausationRule(
                trigger_pattern="*species*",
                affected_fields=[
                    "*ability_score*", "*proficienc*", "*trait*", "*speed*", "*size*",
                    "*language*", "*skill*", "*resistance*", "*immunity*"
                ],
                causation_type="race_change",
                confidence=0.9
            ),
            
            # Multiclass rules
            CausationRule(
                trigger_pattern="*classes*",
                affected_fields=[
                    "*spell_slot*", "*proficienc*", "*feature*", "*hit_point*",
                    "*spell*", "*skill*", "*saving_throw*"
                ],
                causation_type="multiclass_progression",
                confidence=0.85
            )
        ]
    
    def _create_cascade_detectors(self) -> Dict[str, List[str]]:
        """Create enhanced cascade detection rules."""
        return {
            'ability_score_increase': [
                'ability_modifiers.*',
                'saving_throws.*',
                'skills.*',
                'spell_attack_bonus',
                'spell_save_dc',
                'initiative_bonus',
                'passive_perception',
                'passive_investigation',
                'passive_insight'
            ],
            'feat_selection': [
                'proficiencies.*',
                'combat.attack_options.*',
                'combat.bonus_actions.*',
                'spells.known.*',
                'spells.prepared.*',
                'ability_scores.*',
                'skills.*',
                'saving_throws.*',
                'combat.armor_class.*',
                'combat.hit_points.*'
            ],
            'level_progression': [
                'character_info.proficiency_bonus',
                'combat.hit_points.maximum',
                'spellcasting.spell_slots.*',
                'features.class_features.*',
                'features.subclass_features.*',
                'spells.known.*',
                'spells.prepared.*',
                'ability_scores.*'
            ],
            'subclass_selection': [
                'features.subclass_features.*',
                'spells.known.*',
                'spells.prepared.*',
                'proficiencies.*',
                'skills.*',
                'combat.*'
            ],
            'background_change': [
                'proficiencies.skills.*',
                'proficiencies.tools.*',
                'proficiencies.languages.*',
                'equipment.*',
                'inventory.*'
            ],
            'race_change': [
                'ability_scores.*',
                'proficiencies.*',
                'traits.*',
                'speed.*',
                'size',
                'languages.*',
                'resistances.*',
                'immunities.*'
            ],
            'equipment_change': [
                'combat.armor_class.*',
                'combat.attack_bonus.*',
                'combat.damage.*',
                'ability_scores.*',
                'skills.*',
                'saving_throws.*',
                'speed.*',
                'initiative.*'
            ],
            'multiclass_progression': [
                'spellcasting.spell_slots.*',
                'proficiencies.saving_throws.*',
                'features.class_features.*',
                'combat.hit_points.*',
                'spells.*',
                'skills.*'
            ]
        }
    
    def _extract_feat_name(self, feat_data: Any) -> Optional[str]:
        """Extract feat name from feat data."""
        try:
            if isinstance(feat_data, dict):
                return feat_data.get('name', feat_data.get('feat_name'))
            elif isinstance(feat_data, str):
                return feat_data
            return None
        except Exception:
            return None
    
    def _extract_class_from_level_change(self, field_path: str) -> Optional[str]:
        """Extract class name from level change field path."""
        try:
            # Look for class name in field path like "classes.fighter.level"
            parts = field_path.split('.')
            for i, part in enumerate(parts):
                if part == 'classes' and i + 1 < len(parts):
                    return parts[i + 1].title()
            return None
        except Exception:
            return None
    
    def _extract_item_name(self, item_data: Any) -> Optional[str]:
        """Extract item name from equipment data."""
        try:
            if isinstance(item_data, dict):
                return item_data.get('name', item_data.get('item_name'))
            elif isinstance(item_data, str):
                return item_data
            return None
        except Exception:
            return None
    
    def _extract_ability_name(self, field_path: str) -> Optional[str]:
        """Extract ability name from field path."""
        try:
            abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
            field_lower = field_path.lower()
            
            for ability in abilities:
                if ability in field_lower:
                    return ability.title()
            return None
        except Exception:
            return None
    
    def _find_feat_related_changes(self, feat_name: str, changes: List[FieldChange]) -> List[FieldChange]:
        """Find changes that could be related to a feat with enhanced pattern matching."""
        related = []
        
        try:
            # Enhanced feat-specific patterns
            feat_specific_patterns = {
                'great weapon master': [
                    '*combat*attack*', '*combat*bonus*', '*damage*', '*power*attack*'
                ],
                'sharpshooter': [
                    '*combat*attack*', '*damage*', '*precision*', '*range*', '*cover*'
                ],
                'fey touched': [
                    '*spell*', '*ability_score*', '*intelligence*', '*wisdom*', '*charisma*',
                    '*misty*step*', '*enchantment*', '*divination*'
                ],
                'magic initiate': [
                    '*spell*', '*cantrip*', '*spell_attack*', '*spell_save*'
                ],
                'skilled': [
                    '*skill*', '*proficienc*'
                ],
                'resilient': [
                    '*ability_score*', '*saving_throw*', '*proficienc*'
                ],
                'war caster': [
                    '*spell*', '*concentration*', '*opportunity*', '*reaction*'
                ],
                'alert': [
                    '*initiative*', '*surprise*', '*passive*perception*'
                ],
                'mobile': [
                    '*speed*', '*movement*', '*opportunity*'
                ],
                'sentinel': [
                    '*opportunity*', '*reaction*', '*movement*'
                ],
                'polearm master': [
                    '*opportunity*', '*bonus*action*', '*reach*'
                ],
                'crossbow expert': [
                    '*bonus*action*', '*ranged*', '*loading*'
                ],
                'dual wielder': [
                    '*two*weapon*', '*armor_class*', '*weapon*'
                ],
                'heavy armor master': [
                    '*damage*', '*armor_class*', '*strength*'
                ],
                'observant': [
                    '*passive*perception*', '*passive*investigation*'
                ],
                'spell sniper': [
                    '*spell*attack*', '*spell*range*', '*cover*', '*cantrip*'
                ],
                'telekinetic': [
                    '*spell*', '*bonus*action*', '*mage*hand*', '*shove*'
                ],
                'telepathic': [
                    '*spell*', '*detect*thoughts*', '*telepathy*'
                ]
            }
            
            # Get specific patterns for this feat
            specific_patterns = feat_specific_patterns.get(feat_name.lower(), [])
            
            # Common feat effect patterns (fallback)
            common_patterns = [
                '*proficienc*', '*skill*', '*ability_score*', '*spell*', 
                '*attack*', '*damage*', '*combat*', '*bonus_action*',
                '*reaction*', '*passive*', '*initiative*', '*speed*',
                '*armor_class*', '*hit_point*', '*spell_attack*', '*spell_save*'
            ]
            
            # Combine specific and common patterns
            all_patterns = specific_patterns + common_patterns
            
            import fnmatch
            for change in changes:
                # Skip the feat change itself
                if ('feat' in change.field_path.lower() and 
                    feat_name.lower().replace(' ', '_') in change.field_path.lower()):
                    continue
                
                field_lower = change.field_path.lower()
                
                for pattern in all_patterns:
                    if fnmatch.fnmatch(field_lower, pattern):
                        related.append(change)
                        self.logger.debug(f"Matched pattern '{pattern}' for feat {feat_name} in field {change.field_path}")
                        break
        
        except Exception as e:
            self.logger.error(f"Error finding feat-related changes for {feat_name}: {e}")
        
        return related
    
    def _find_level_related_changes(self, level: int, class_name: Optional[str], 
                                  changes: List[FieldChange]) -> List[FieldChange]:
        """Find changes that could be related to level progression."""
        related = []
        
        # Common level progression effects
        level_effect_patterns = [
            '*hit_point*', '*hitpoint*', '*spell_slot*', '*proficiency_bonus*', 
            '*feature*', '*class_feature*', '*spell*', '*maximum*'
        ]
        
        for change in changes:
            # Skip the level change itself
            if 'level' in change.field_path.lower():
                continue
                
            for pattern in level_effect_patterns:
                import fnmatch
                if fnmatch.fnmatch(change.field_path.lower(), pattern):
                    related.append(change)
                    break
        
        return related
    
    def _find_equipment_related_changes(self, item_name: str, changes: List[FieldChange]) -> List[FieldChange]:
        """Find changes that could be related to equipment."""
        related = []
        
        # Common equipment effects
        equipment_effect_patterns = [
            '*armor_class*', '*attack_bonus*', '*damage*', '*ability_score*',
            '*skill*', '*saving_throw*', '*speed*'
        ]
        
        for change in changes:
            for pattern in equipment_effect_patterns:
                import fnmatch
                if fnmatch.fnmatch(change.field_path.lower(), pattern):
                    related.append(change)
                    break
        
        return related
    
    def _find_ability_related_changes(self, ability_name: str, changes: List[FieldChange]) -> List[FieldChange]:
        """Find changes that could be related to ability score changes."""
        related = []
        
        ability_lower = ability_name.lower() if ability_name else ''
        
        for change in changes:
            field_lower = change.field_path.lower()
            
            # Skip the original ability score change itself
            if ability_lower and ability_lower in field_lower and 'abilityscore' in field_lower:
                continue
            
            # Check for direct ability-related changes
            if (ability_lower and ability_lower in field_lower) or \
               'skill' in field_lower or \
               'saving_throw' in field_lower or \
               'spell_attack' in field_lower or \
               'spell_save_dc' in field_lower or \
               'initiative' in field_lower:
                related.append(change)
        
        return related
    
    def _find_secondary_effects(self, primary_change: FieldChange, all_changes: List[FieldChange]) -> List[FieldChange]:
        """Find changes that might be secondary effects of a primary change."""
        secondary = []
        
        # This is a simplified implementation - in practice, you'd want more sophisticated rules
        primary_field = primary_change.field_path.lower()
        
        for change in all_changes:
            if change == primary_change:
                continue
                
            change_field = change.field_path.lower()
            
            # Simple heuristic: if fields share common terms, they might be related
            primary_terms = set(primary_field.split('.'))
            change_terms = set(change_field.split('.'))
            
            if len(primary_terms.intersection(change_terms)) > 0:
                secondary.append(change)
        
        return secondary
    
    def _extract_subclass_name(self, subclass_data: Any) -> Optional[str]:
        """Extract subclass name from subclass data."""
        try:
            if isinstance(subclass_data, dict):
                return subclass_data.get('name', subclass_data.get('subclass_name'))
            elif isinstance(subclass_data, str):
                return subclass_data
            return None
        except Exception:
            return None
    
    def _extract_class_from_subclass_path(self, field_path: str) -> Optional[str]:
        """Extract class name from subclass field path."""
        try:
            # Look for class name in field path like "classes.fighter.subclass"
            parts = field_path.split('.')
            for i, part in enumerate(parts):
                if part == 'classes' and i + 1 < len(parts):
                    return parts[i + 1].title()
            return None
        except Exception:
            return None
    
    def _extract_background_name(self, background_data: Any) -> Optional[str]:
        """Extract background name from background data."""
        try:
            if isinstance(background_data, dict):
                return background_data.get('name', background_data.get('background_name'))
            elif isinstance(background_data, str):
                return background_data
            return None
        except Exception:
            return None
    
    def _extract_race_name(self, race_data: Any) -> Optional[str]:
        """Extract race name from race data."""
        try:
            if isinstance(race_data, dict):
                return race_data.get('name', race_data.get('race_name', race_data.get('species_name')))
            elif isinstance(race_data, str):
                return race_data
            return None
        except Exception:
            return None
    
    def _find_subclass_related_changes(self, subclass_name: str, class_name: Optional[str], 
                                     changes: List[FieldChange]) -> List[FieldChange]:
        """Find changes that could be related to a subclass."""
        related = []
        
        # Common subclass effects
        subclass_effect_patterns = [
            '*feature*', '*spell*', '*proficienc*', '*skill*', 
            '*combat*', '*bonus_action*', '*reaction*'
        ]
        
        for change in changes:
            for pattern in subclass_effect_patterns:
                import fnmatch
                if fnmatch.fnmatch(change.field_path.lower(), pattern):
                    related.append(change)
                    break
        
        return related
    
    def _find_background_related_changes(self, background_name: str, changes: List[FieldChange]) -> List[FieldChange]:
        """Find changes that could be related to a background."""
        related = []
        
        # Common background effects
        background_effect_patterns = [
            '*proficienc*', '*skill*', '*language*', '*tool*', 
            '*equipment*', '*inventory*'
        ]
        
        for change in changes:
            for pattern in background_effect_patterns:
                import fnmatch
                if fnmatch.fnmatch(change.field_path.lower(), pattern):
                    related.append(change)
                    break
        
        return related
    
    def _find_race_related_changes(self, race_name: str, changes: List[FieldChange]) -> List[FieldChange]:
        """Find changes that could be related to a race/species."""
        related = []
        
        # Common race effects
        race_effect_patterns = [
            '*ability_score*', '*abilityscore*', '*proficienc*', '*trait*', '*speed*', '*size*',
            '*language*', '*skill*', '*resistance*', '*immunity*', '*darkvision*', '*dexterity*',
            '*strength*', '*constitution*', '*intelligence*', '*wisdom*', '*charisma*'
        ]
        
        for change in changes:
            # Skip the race change itself
            if 'race' in change.field_path.lower() or 'species' in change.field_path.lower():
                continue
                
            for pattern in race_effect_patterns:
                import fnmatch
                if fnmatch.fnmatch(change.field_path.lower(), pattern):
                    related.append(change)
                    break
        
        return related
    
    def _find_multiclass_related_changes(self, class_name: str, level: int, is_new_class: bool,
                                       changes: List[FieldChange]) -> List[FieldChange]:
        """Find changes that could be related to multiclass progression."""
        related = []
        
        # Common multiclass effects
        multiclass_effect_patterns = [
            '*spell_slot*', '*proficienc*', '*feature*', '*hit_point*',
            '*spell*', '*skill*', '*saving_throw*'
        ]
        
        for change in changes:
            for pattern in multiclass_effect_patterns:
                import fnmatch
                if fnmatch.fnmatch(change.field_path.lower(), pattern):
                    related.append(change)
                    break
        
        return related


class CascadeChangeDetector:
    """Detects cascading effects of primary changes."""
    
    CASCADE_RULES = {
        'ability_score_increase': [
            'ability_modifiers.*',
            'saving_throws.*',
            'skills.*',
            'spell_attack_bonus',
            'spell_save_dc',
            'initiative_bonus'
        ],
        'feat_selection': [
            'proficiencies.*',
            'combat.attack_options.*',
            'combat.bonus_actions.*',
            'spells.known.*'
        ],
        'level_progression': [
            'character_info.proficiency_bonus',
            'combat.hit_points.maximum',
            'spellcasting.spell_slots.*',
            'features.class_features.*'
        ]
    }
    
    def detect_cascades(self, primary_change: FieldChange, 
                       all_changes: List[FieldChange]) -> List[FieldChange]:
        """Detect which changes cascade from a primary change."""
        cascades = []
        
        # Determine the type of primary change
        primary_type = self._classify_change_type(primary_change)
        
        if primary_type in self.CASCADE_RULES:
            patterns = self.CASCADE_RULES[primary_type]
            
            for change in all_changes:
                if change == primary_change:
                    continue
                    
                for pattern in patterns:
                    import fnmatch
                    if fnmatch.fnmatch(change.field_path, pattern):
                        cascades.append(change)
                        break
        
        return cascades
    
    def _classify_change_type(self, change: FieldChange) -> str:
        """Classify a change to determine its cascade type."""
        field_lower = change.field_path.lower()
        
        if 'abilityscore' in field_lower or 'ability_score' in field_lower or any(ability in field_lower for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']):
            return 'ability_score_increase'
        elif 'feat' in field_lower:
            return 'feat_selection'
        elif 'level' in field_lower:
            return 'level_progression'
        else:
            return 'unknown'