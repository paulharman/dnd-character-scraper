#!/usr/bin/env python3
"""
Character change detection service.

Provides comprehensive change detection between character snapshots
with field-level granularity and priority assessment.
"""

import logging
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum
import fnmatch

@dataclass
class CharacterSnapshot:
    """Simple snapshot for Discord service."""
    character_id: int
    version: int
    timestamp: datetime
    character_data: Any

@dataclass  
class CharacterDiff:
    """Simple diff for Discord service."""
    old_snapshot: CharacterSnapshot
    new_snapshot: CharacterSnapshot
    changes: Any

logger = logging.getLogger(__name__)


class ChangePriority(Enum):
    """Priority levels for character changes."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class ChangeType(Enum):
    """Types of changes that can occur."""
    ADDED = "added"
    REMOVED = "removed"
    MODIFIED = "modified"
    INCREMENTED = "incremented"
    DECREMENTED = "decremented"


@dataclass
class FieldChange:
    """Represents a single field change with metadata."""
    field_path: str
    old_value: Any
    new_value: Any
    change_type: ChangeType
    priority: ChangePriority = ChangePriority.MEDIUM
    description: Optional[str] = None
    
    def __post_init__(self):
        """Validate field_path is always a string and priority is an enum."""
        self.field_path = str(self.field_path)
        # Ensure priority is always a ChangePriority enum
        if not isinstance(self.priority, ChangePriority):
            logger.warning(f"Invalid priority type {type(self.priority)} for field {self.field_path}, defaulting to MEDIUM")
            self.priority = ChangePriority.MEDIUM
    
    def get_change_delta(self) -> Optional[int]:
        """Get numeric delta for incremental changes."""
        if self.change_type in [ChangeType.INCREMENTED, ChangeType.DECREMENTED]:
            try:
                old_val = int(self.old_value) if self.old_value is not None else 0
                new_val = int(self.new_value) if self.new_value is not None else 0
                return new_val - old_val
            except (ValueError, TypeError):
                return None
        return None


@dataclass
class CharacterChangeSet:
    """Collection of changes for a character with metadata."""
    character_id: int
    character_name: str
    from_version: int
    to_version: int
    timestamp: datetime
    changes: List[FieldChange]
    summary: Optional[str] = None
    
    def get_changes_by_priority(self, min_priority: ChangePriority = ChangePriority.LOW) -> List[FieldChange]:
        """Get changes filtered by minimum priority."""
        return [change for change in self.changes if change.priority.value >= min_priority.value]
    
    def get_changes_by_type(self, change_type: ChangeType) -> List[FieldChange]:
        """Get changes filtered by type."""
        return [change for change in self.changes if change.change_type == change_type]
    
    def has_high_priority_changes(self) -> bool:
        """Check if any high priority changes exist."""
        return any(change.priority.value >= ChangePriority.HIGH.value for change in self.changes)


class ChangeDetectionService:
    """
    Service for detecting and analyzing character changes.
    
    Features:
    - Deep field comparison between character snapshots
    - Priority assessment based on field importance
    - Change type classification (added/removed/modified/incremented)
    - Support for nested object comparison
    - Configurable field filtering and grouping
    """
    
    def __init__(self):
        # Fields to exclude from change detection (timestamps, etc.)
        self.excluded_fields = {
            'updated_at',
            'created_at', 
            'date_modified',
            'timestamp',
            'last_modified',
            'last_accessed',
            'version',
            'basic_info.avatarUrl',  # Can change frequently
            'basic_info.avatar_url',  # Alternative field name
            'meta.*',  # Metadata fields
            'debug.*',  # Debug information
            'generated_timestamp',  # Always changes
            'containers',  # Complex container structure that varies
            'containers.*',  # All container-related fields
            
            # Array indices cause false positives when items are added/removed
            'inventory*',  # Match anything starting with inventory
            'inventory_items*',  # Alternative naming
            'encumbrance',  # Weight calculations change when items are added/removed
            'encumbrance.*',  # All encumbrance sub-fields
            'actions*',  # Action array shuffling when spells/abilities are added
            'spells*',  # Spell array changes
            'spell_counts*',  # Spell count recalculations
            
            # Class feature metadata that can vary between runs
            '*.level_required',
            '*.levelRequired', 
            '*.level_scales',
            '*.levelScales',
            '*.creature_rules',
            '*.creatureRules',
            '*.display_order',
            '*.displayOrder',
            '*.hide_in_builder',
            '*.hideInBuilder',
            '*.hide_in_sheet',
            '*.hideInSheet',
            '*.source_id',
            '*.sourceId',
            '*.source_page_number',
            '*.sourcePageNumber',
            '*.definition_key',
            '*.definitionKey',
            
            # Feature processing metadata
            'class_features*level_required',
            'class_features*level_scales', 
            'class_features*creature_rules',
            'class_features*display_order',
            'class_features*source_id'
        }
        
        self.high_priority_fields = {
            'basic_info.level',
            'basic_info.experience', 
            'basic_info.hit_points.current',
            'basic_info.hit_points.maximum',
            'basic_info.armor_class.total',
            'basic_info.classes.*',
            'spell_slots.*',
            'inventory.*',
            'feats.*'
        }
        
        self.medium_priority_fields = {
            'ability_scores.*',
            'proficiencies.*',
            'skills.*',
            'saving_throws.*',
            'equipment.*'
        }
        
        # Fields that are typically numeric and should show deltas
        self.numeric_fields = {
            'basic_info.level',
            'basic_info.experience',
            'basic_info.hit_points.*',
            'basic_info.armor_class.*',
            'ability_scores.*',
            'spell_slots.*',
            'currency.*'
        }
        
        logger.info("Change detection service initialized")
    
    def detect_changes(
        self,
        old_snapshot: CharacterSnapshot,
        new_snapshot: CharacterSnapshot
    ) -> CharacterChangeSet:
        """
        Detect semantic changes between two character snapshots.
        
        Args:
            old_snapshot: Previous character state
            new_snapshot: Current character state
            
        Returns:
            CharacterChangeSet with semantic changes detected
        """
        if old_snapshot.character_id != new_snapshot.character_id:
            raise ValueError("Cannot compare snapshots of different characters")
        
        logger.info(f"Detecting changes for character {old_snapshot.character_id} "
                   f"(v{old_snapshot.version} -> v{new_snapshot.version})")
        
        changes = []
        
        # Use semantic comparison for complex data structures with error handling
        detection_methods = [
            ("spell_changes", self._detect_spell_changes),
            ("inventory_changes", self._detect_inventory_changes),
            ("basic_stat_changes", self._detect_basic_stat_changes),
            ("feature_changes", self._detect_feature_changes),
            ("ability_score_changes", self._detect_ability_score_changes),
            ("skill_changes", self._detect_skill_changes),
            ("proficiency_changes", self._detect_proficiency_changes),
            ("feat_changes", self._detect_feat_changes),
            ("equipment_changes", self._detect_equipment_changes),
            ("currency_changes", self._detect_currency_changes),
            ("spell_slot_changes", self._detect_spell_slot_changes),
        ]
        
        for method_name, method_func in detection_methods:
            try:
                logger.debug(f"Running {method_name} detection...")
                method_changes = method_func(old_snapshot.character_data, new_snapshot.character_data)
                logger.debug(f"{method_name} detection completed: {len(method_changes)} changes found")
                changes.extend(method_changes)
            except Exception as e:
                logger.error(f"Error in {method_name} detection: {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")
                logger.error(f"Error traceback:", exc_info=True)
                # Continue with other detection methods
        
        # Fall back to field-by-field comparison for other fields
        try:
            logger.debug("Running field-by-field comparison...")
            other_changes = self._detect_other_field_changes(old_snapshot.character_data, new_snapshot.character_data)
            logger.debug(f"Field-by-field comparison completed: {len(other_changes)} changes found")
            changes.extend(other_changes)
        except Exception as e:
            logger.error(f"Error in field-by-field comparison: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error traceback:", exc_info=True)
        
        # Extract character name safely
        character_name = 'Unknown'
        try:
            if hasattr(new_snapshot.character_data, 'basic_info') and hasattr(new_snapshot.character_data.basic_info, 'get'):
                character_name = new_snapshot.character_data.basic_info.get('name', 'Unknown')
            elif isinstance(new_snapshot.character_data, dict) and 'basic_info' in new_snapshot.character_data:
                basic_info = new_snapshot.character_data['basic_info']
                if isinstance(basic_info, dict):
                    character_name = basic_info.get('name', 'Unknown')
            
            # Ensure character_name is always a string
            character_name = str(character_name) if character_name is not None else 'Unknown'
        except Exception as e:
            logger.warning(f"Error extracting character name: {e}, using 'Unknown'")
            character_name = 'Unknown'
        
        # Deduplicate changes to remove any remaining duplicates
        changes = self._deduplicate_changes(changes)
        
        change_set = CharacterChangeSet(
            character_id=old_snapshot.character_id,
            character_name=character_name,
            from_version=old_snapshot.version,
            to_version=new_snapshot.version,
            timestamp=new_snapshot.timestamp,
            changes=changes,
            summary=self._generate_change_summary(changes)
        )
        
        logger.info(f"Detected {len(changes)} semantic changes for character {old_snapshot.character_id}")
        
        # Log details of each change for debugging
        if changes:
            logger.info("Change details:")
            for i, change in enumerate(changes[:5]):  # Show first 5 changes
                logger.info(f"  {i+1}. {change.change_type.value.title()}: {change.field_path}")
                if change.description:
                    logger.info(f"     -> {change.description}")
                else:
                    logger.info(f"     -> {change.old_value} → {change.new_value}")
            if len(changes) > 5:
                logger.info(f"  ... and {len(changes) - 5} more changes")
        
        return change_set
    
    def _detect_spell_changes(self, old_data, new_data) -> List[FieldChange]:
        """Detect spell additions, removals, and changes."""
        changes = []
        
        try:
            logger.debug("Extracting spell lists for comparison...")
            # Get spell lists from both snapshots
            old_spells = self._extract_spell_list(old_data)
            new_spells = self._extract_spell_list(new_data)
            
            logger.debug(f"Old spells count: {len(old_spells)}, New spells count: {len(new_spells)}")
            
            # Convert to sets for comparison
            old_spell_names = {spell['name'] for spell in old_spells if isinstance(spell, dict) and 'name' in spell}
            new_spell_names = {spell['name'] for spell in new_spells if isinstance(spell, dict) and 'name' in spell}
            
            logger.debug(f"Old spell names: {len(old_spell_names)}, New spell names: {len(new_spell_names)}")
        except Exception as e:
            logger.error(f"Error extracting spell data: {str(e)}")
            logger.error(f"Old data type: {type(old_data)}, New data type: {type(new_data)}")
            return changes
        
        # Detect added spells
        added_spells = new_spell_names - old_spell_names
        for spell_name in added_spells:
            spell_info = next(s for s in new_spells if s['name'] == spell_name)
            spell_type = "cantrip" if spell_info.get('level', 0) == 0 else f"level {spell_info.get('level')} spell"
            
            changes.append(FieldChange(
                field_path=f"spells.{spell_name}",
                old_value=None,
                new_value=spell_name,
                change_type=ChangeType.ADDED,
                priority=ChangePriority.HIGH,
                description=f"Learned {spell_type}: {spell_name}"
            ))
        
        # Detect removed spells
        removed_spells = old_spell_names - new_spell_names
        for spell_name in removed_spells:
            spell_info = next(s for s in old_spells if s['name'] == spell_name)
            spell_type = "cantrip" if spell_info.get('level', 0) == 0 else f"level {spell_info.get('level')} spell"
            
            changes.append(FieldChange(
                field_path=f"spells.{spell_name}",
                old_value=spell_name,
                new_value=None,
                change_type=ChangeType.REMOVED,
                priority=ChangePriority.HIGH,
                description=f"Forgot {spell_type}: {spell_name}"
            ))
        
        return changes
    
    def _extract_spell_list(self, character_data) -> List[Dict[str, Any]]:
        """Extract a normalized list of spells from character data."""
        spells = []
        
        try:
            # Handle both object and dict access
            spell_data = None
            if hasattr(character_data, 'spells'):
                spell_data = character_data.spells
            elif isinstance(character_data, dict) and 'spells' in character_data:
                spell_data = character_data['spells']
            
            if spell_data:
                if isinstance(spell_data, dict):
                    # Handle structured spell data (e.g., {'Wizard': [...], 'Racial': [...]})
                    for category, spell_list in spell_data.items():
                        if isinstance(spell_list, list):
                            for spell in spell_list:
                                if isinstance(spell, dict) and 'name' in spell:
                                    spells.append(spell)
                elif isinstance(spell_data, list):
                    for spell in spell_data:
                        if isinstance(spell, dict) and 'name' in spell:
                            spells.append(spell)
            
            # Also check actions for cantrips
            actions_data = None
            if hasattr(character_data, 'actions'):
                actions_data = character_data.actions
            elif isinstance(character_data, dict) and 'actions' in character_data:
                actions_data = character_data['actions']
                
            if actions_data and isinstance(actions_data, list):
                for action in actions_data:
                    if isinstance(action, dict) and action.get('type') in ['cantrip', 'spell'] and action.get('name'):
                        spells.append({
                            'name': action.get('name'),
                            'level': 0 if action.get('type') == 'cantrip' else action.get('level', 1),
                            'school': action.get('school', 'Unknown')
                        })
        except Exception as e:
            logger.error(f"Error extracting spell list: {str(e)}")
            logger.error(f"Character data type: {type(character_data)}")
        
        return spells
    
    def _detect_inventory_changes(self, old_data, new_data) -> List[FieldChange]:
        """Detect inventory item additions, removals, and quantity changes."""
        changes = []
        
        try:
            logger.debug("Extracting inventory items for comparison...")
            old_items = self._extract_inventory_items(old_data)
            new_items = self._extract_inventory_items(new_data)
            
            logger.debug(f"Old items count: {len(old_items)}, New items count: {len(new_items)}")
            
            # Group by item name for comparison
            old_item_map = {item['name']: item for item in old_items if isinstance(item, dict) and 'name' in item}
            new_item_map = {item['name']: item for item in new_items if isinstance(item, dict) and 'name' in item}
            
            logger.debug(f"Old item map keys: {len(old_item_map)}, New item map keys: {len(new_item_map)}")
        except Exception as e:
            logger.error(f"Error extracting inventory data: {str(e)}")
            logger.error(f"Old data type: {type(old_data)}, New data type: {type(new_data)}")
            return changes
        
        # Detect added items
        for item_name, item in new_item_map.items():
            if item_name not in old_item_map:
                changes.append(FieldChange(
                    field_path=f"inventory.{item_name}",
                    old_value=None,
                    new_value=f"{item['quantity']}x {item_name}",
                    change_type=ChangeType.ADDED,
                    priority=ChangePriority.MEDIUM,
                    description=f"Added {item['quantity']}x {item_name}"
                ))
        
        # Detect removed items
        for item_name, item in old_item_map.items():
            if item_name not in new_item_map:
                changes.append(FieldChange(
                    field_path=f"inventory.{item_name}",
                    old_value=f"{item['quantity']}x {item_name}",
                    new_value=None,
                    change_type=ChangeType.REMOVED,
                    priority=ChangePriority.MEDIUM,
                    description=f"Removed {item['quantity']}x {item_name}"
                ))
        
        # Detect quantity changes
        for item_name in old_item_map.keys() & new_item_map.keys():
            old_qty = old_item_map[item_name]['quantity']
            new_qty = new_item_map[item_name]['quantity']
            
            if old_qty != new_qty:
                change_type = ChangeType.INCREMENTED if new_qty > old_qty else ChangeType.DECREMENTED
                changes.append(FieldChange(
                    field_path=f"inventory.{item_name}.quantity",
                    old_value=old_qty,
                    new_value=new_qty,
                    change_type=change_type,
                    priority=ChangePriority.LOW,
                    description=f"{item_name} quantity: {old_qty} → {new_qty}"
                ))
        
        return changes
    
    def _extract_inventory_items(self, character_data) -> List[Dict[str, Any]]:
        """Extract normalized inventory items from character data."""
        items = []
        
        try:
            # Handle both object and dict access
            inventory_data = None
            if hasattr(character_data, 'inventory'):
                inventory_data = character_data.inventory
            elif isinstance(character_data, dict) and 'inventory' in character_data:
                inventory_data = character_data['inventory']
            
            if inventory_data and isinstance(inventory_data, list):
                for item in inventory_data:
                    if isinstance(item, dict) and 'name' in item:
                        items.append({
                            'name': item.get('name', 'Unknown Item'),
                            'quantity': item.get('quantity', 1),
                            'weight': item.get('weight', 0),
                            'type': item.get('type', 'Unknown')
                        })
        except Exception as e:
            logger.error(f"Error extracting inventory items: {str(e)}")
            logger.error(f"Character data type: {type(character_data)}")
        
        return items
    
    def _detect_basic_stat_changes(self, old_data, new_data) -> List[FieldChange]:
        """Detect changes to basic character stats."""
        changes = []
        
        # Important stats to monitor
        stats_to_check = [
            ('basic_info.level', 'Level', ChangePriority.CRITICAL),
            ('basic_info.experience', 'Experience', ChangePriority.HIGH),
            ('basic_info.hit_points.current', 'Current HP', ChangePriority.HIGH),
            ('basic_info.hit_points.maximum', 'Maximum HP', ChangePriority.HIGH),
            ('basic_info.armor_class.total', 'Armor Class', ChangePriority.MEDIUM),
        ]
        
        # Check for HP relationship logic first
        old_max_hp = self._get_nested_value(old_data, 'basic_info.hit_points.maximum')
        new_max_hp = self._get_nested_value(new_data, 'basic_info.hit_points.maximum')
        old_current_hp = self._get_nested_value(old_data, 'basic_info.hit_points.current')
        new_current_hp = self._get_nested_value(new_data, 'basic_info.hit_points.current')
        
        # Determine if current HP change is just due to max HP increase
        skip_current_hp = False
        if (old_max_hp is not None and new_max_hp is not None and 
            old_current_hp is not None and new_current_hp is not None and
            isinstance(old_max_hp, (int, float)) and isinstance(new_max_hp, (int, float)) and
            isinstance(old_current_hp, (int, float)) and isinstance(new_current_hp, (int, float))):
            
            max_hp_increase = new_max_hp - old_max_hp
            current_hp_increase = new_current_hp - old_current_hp
            
            # If current HP increased by the same amount as max HP and character was at full health
            if (max_hp_increase > 0 and current_hp_increase == max_hp_increase and 
                old_current_hp == old_max_hp):
                skip_current_hp = True
                logger.debug(f"Skipping current HP change - automatic increase due to max HP increase")
        
        for field_path, display_name, priority in stats_to_check:
            try:
                # Skip current HP if it's just due to max HP increase
                if field_path == 'basic_info.hit_points.current' and skip_current_hp:
                    continue
                    
                logger.debug(f"Checking basic stat: {field_path}")
                old_value = self._get_nested_value(old_data, field_path)
                new_value = self._get_nested_value(new_data, field_path)
                
                logger.debug(f"  Old value: {old_value} (type: {type(old_value)})")
                logger.debug(f"  New value: {new_value} (type: {type(new_value)})")
                
                if old_value != new_value and old_value is not None and new_value is not None:
                    if isinstance(old_value, (int, float)) and isinstance(new_value, (int, float)):
                        change_type = ChangeType.INCREMENTED if new_value > old_value else ChangeType.DECREMENTED
                    else:
                        change_type = ChangeType.MODIFIED
                    
                    changes.append(FieldChange(
                        field_path=field_path,
                        old_value=old_value,
                        new_value=new_value,
                        change_type=change_type,
                        priority=priority,
                        description=f"{display_name}: {old_value} → {new_value}"
                    ))
            except Exception as e:
                logger.error(f"Error checking basic stat {field_path}: {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")
                continue
        
        return changes
    
    def _detect_feature_changes(self, old_data, new_data) -> List[FieldChange]:
        """Detect changes to class features and abilities."""
        changes = []
        
        try:
            logger.debug("Extracting features for comparison...")
            # Extract features from both snapshots
            old_features = self._extract_features(old_data)
            new_features = self._extract_features(new_data)
            
            logger.debug(f"Old features count: {len(old_features)}, New features count: {len(new_features)}")
            
            old_feature_names = {f['name'] for f in old_features if isinstance(f, dict) and 'name' in f}
            new_feature_names = {f['name'] for f in new_features if isinstance(f, dict) and 'name' in f}
            
            logger.debug(f"Old feature names: {len(old_feature_names)}, New feature names: {len(new_feature_names)}")
        except Exception as e:
            logger.error(f"Error extracting feature data: {str(e)}")
            logger.error(f"Old data type: {type(old_data)}, New data type: {type(new_data)}")
            return changes
        
        # Detect new features
        for feature_name in new_feature_names - old_feature_names:
            changes.append(FieldChange(
                field_path=f"features.{feature_name}",
                old_value=None,
                new_value=feature_name,
                change_type=ChangeType.ADDED,
                priority=ChangePriority.HIGH,
                description=f"Gained feature: {feature_name}"
            ))
        
        return changes
    
    def _extract_features(self, character_data) -> List[Dict[str, Any]]:
        """Extract class features from character data."""
        features = []
        
        try:
            # Handle both object and dict access
            features_data = None
            if hasattr(character_data, 'class_features'):
                features_data = character_data.class_features
            elif isinstance(character_data, dict) and 'class_features' in character_data:
                features_data = character_data['class_features']
            
            if features_data and isinstance(features_data, list):
                for feature in features_data:
                    if isinstance(feature, dict) and 'name' in feature:
                        features.append(feature)
        except Exception as e:
            logger.error(f"Error extracting features: {str(e)}")
            logger.error(f"Character data type: {type(character_data)}")
        
        return features
    
    def _detect_ability_score_changes(self, old_data, new_data) -> List[FieldChange]:
        """Detect changes to ability scores."""
        changes = []
        
        abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        
        for ability in abilities:
            try:
                logger.debug(f"Checking ability score: {ability}")
                old_ability_data = self._get_nested_value(old_data, f'ability_scores.{ability}')
                new_ability_data = self._get_nested_value(new_data, f'ability_scores.{ability}')
                
                logger.debug(f"  Old {ability}: {old_ability_data} (type: {type(old_ability_data)})")
                logger.debug(f"  New {ability}: {new_ability_data} (type: {type(new_ability_data)})")
                
                # Handle both simple numeric scores and complex ability data
                old_score = None
                new_score = None
                
                if isinstance(old_ability_data, (int, float)):
                    old_score = old_ability_data
                elif isinstance(old_ability_data, dict) and 'score' in old_ability_data:
                    old_score = old_ability_data['score']
                elif isinstance(old_ability_data, dict) and 'total' in old_ability_data:
                    old_score = old_ability_data['total']
                
                if isinstance(new_ability_data, (int, float)):
                    new_score = new_ability_data
                elif isinstance(new_ability_data, dict) and 'score' in new_ability_data:
                    new_score = new_ability_data['score']
                elif isinstance(new_ability_data, dict) and 'total' in new_ability_data:
                    new_score = new_ability_data['total']
                
                # Only proceed if we have valid numeric scores
                if old_score is not None and new_score is not None and old_score != new_score:
                    if isinstance(old_score, (int, float)) and isinstance(new_score, (int, float)):
                        change_type = ChangeType.INCREMENTED if new_score > old_score else ChangeType.DECREMENTED
                        changes.append(FieldChange(
                            field_path=f"ability_scores.{ability}",
                            old_value=old_score,
                            new_value=new_score,
                            change_type=change_type,
                            priority=ChangePriority.HIGH,
                            description=f"{ability.title()} score: {old_score} → {new_score}"
                        ))
                    else:
                        logger.warning(f"Non-numeric ability score for {ability}: old={old_score}, new={new_score}")
                        
            except Exception as e:
                logger.error(f"Error checking ability score {ability}: {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")
                continue
        
        return changes
    
    def _detect_skill_changes(self, old_data, new_data) -> List[FieldChange]:
        """Detect changes to skill proficiencies and bonuses."""
        changes = []
        
        try:
            logger.debug("Extracting skills for comparison...")
            old_skills = self._extract_skills(old_data)
            new_skills = self._extract_skills(new_data)
            
            logger.debug(f"Old skills count: {len(old_skills)}, New skills count: {len(new_skills)}")
            
            # Compare skill proficiencies
            old_proficient = {skill['name'] for skill in old_skills if isinstance(skill, dict) and 'name' in skill and skill.get('proficient', False)}
            new_proficient = {skill['name'] for skill in new_skills if isinstance(skill, dict) and 'name' in skill and skill.get('proficient', False)}
            
            logger.debug(f"Old proficient skills: {len(old_proficient)}, New proficient skills: {len(new_proficient)}")
        except Exception as e:
            logger.error(f"Error extracting skill data: {str(e)}")
            logger.error(f"Old data type: {type(old_data)}, New data type: {type(new_data)}")
            return changes
        
        # New proficiencies
        for skill in new_proficient - old_proficient:
            changes.append(FieldChange(
                field_path=f"skills.{skill}.proficient",
                old_value=False,
                new_value=True,
                change_type=ChangeType.ADDED,
                priority=ChangePriority.MEDIUM,
                description=f"Gained proficiency: {skill}"
            ))
        
        # Lost proficiencies
        for skill in old_proficient - new_proficient:
            changes.append(FieldChange(
                field_path=f"skills.{skill}.proficient",
                old_value=True,
                new_value=False,
                change_type=ChangeType.REMOVED,
                priority=ChangePriority.MEDIUM,
                description=f"Lost proficiency: {skill}"
            ))
        
        return changes
    
    def _extract_skills(self, character_data) -> List[Dict[str, Any]]:
        """Extract skill information from character data."""
        skills = []
        
        try:
            # Handle both object and dict access
            skills_data = None
            if hasattr(character_data, 'skills'):
                skills_data = character_data.skills
            elif isinstance(character_data, dict) and 'skills' in character_data:
                skills_data = character_data['skills']
            
            if skills_data:
                if isinstance(skills_data, dict):
                    for skill_name, skill_data in skills_data.items():
                        if isinstance(skill_data, dict):
                            skills.append({
                                'name': skill_name,
                                'proficient': skill_data.get('proficient', False),
                                'expertise': skill_data.get('expertise', False),
                                'bonus': skill_data.get('bonus', 0)
                            })
                elif isinstance(skills_data, list):
                    for skill in skills_data:
                        if isinstance(skill, dict) and 'name' in skill:
                            skills.append(skill)
        except Exception as e:
            logger.error(f"Error extracting skills: {str(e)}")
            logger.error(f"Character data type: {type(character_data)}")
        
        return skills
    
    def _detect_proficiency_changes(self, old_data, new_data) -> List[FieldChange]:
        """Detect changes to weapon, armor, and tool proficiencies."""
        changes = []
        
        proficiency_types = ['weapons', 'armor', 'tools', 'languages']
        
        for prof_type in proficiency_types:
            try:
                logger.debug(f"Checking proficiency type: {prof_type}")
                old_profs = set(self._extract_proficiencies(old_data, prof_type))
                new_profs = set(self._extract_proficiencies(new_data, prof_type))
                
                logger.debug(f"  Old {prof_type}: {len(old_profs)}, New {prof_type}: {len(new_profs)}")
            except Exception as e:
                logger.error(f"Error extracting {prof_type} proficiencies: {str(e)}")
                continue
            
            # New proficiencies
            for prof in new_profs - old_profs:
                changes.append(FieldChange(
                    field_path=f"proficiencies.{prof_type}.{prof}",
                    old_value=None,
                    new_value=prof,
                    change_type=ChangeType.ADDED,
                    priority=ChangePriority.MEDIUM,
                    description=f"Gained {prof_type[:-1]} proficiency: {prof}"
                ))
            
            # Lost proficiencies
            for prof in old_profs - new_profs:
                changes.append(FieldChange(
                    field_path=f"proficiencies.{prof_type}.{prof}",
                    old_value=prof,
                    new_value=None,
                    change_type=ChangeType.REMOVED,
                    priority=ChangePriority.LOW,
                    description=f"Lost {prof_type[:-1]} proficiency: {prof}"
                ))
        
        return changes
    
    def _extract_proficiencies(self, character_data, prof_type: str) -> List[str]:
        """Extract proficiencies of a specific type."""
        proficiencies = []
        
        try:
            # Handle both object and dict access
            prof_container = None
            if hasattr(character_data, 'proficiencies'):
                prof_container = character_data.proficiencies
            elif isinstance(character_data, dict) and 'proficiencies' in character_data:
                prof_container = character_data['proficiencies']
            
            if prof_container and isinstance(prof_container, dict):
                prof_data = prof_container.get(prof_type, [])
                if isinstance(prof_data, list):
                    for p in prof_data:
                        if isinstance(p, dict) and 'name' in p:
                            proficiencies.append(p['name'])
                        elif isinstance(p, str):
                            proficiencies.append(p)
        except Exception as e:
            logger.error(f"Error extracting {prof_type} proficiencies: {str(e)}")
            logger.error(f"Character data type: {type(character_data)}")
        
        return proficiencies
    
    def _detect_feat_changes(self, old_data, new_data) -> List[FieldChange]:
        """Detect changes to feats."""
        changes = []
        
        try:
            logger.debug("Extracting feats for comparison...")
            old_feats = set(self._extract_feats(old_data))
            new_feats = set(self._extract_feats(new_data))
            
            logger.debug(f"Old feats count: {len(old_feats)}, New feats count: {len(new_feats)}")
        except Exception as e:
            logger.error(f"Error extracting feat data: {str(e)}")
            logger.error(f"Old data type: {type(old_data)}, New data type: {type(new_data)}")
            return changes
        
        # New feats
        for feat in new_feats - old_feats:
            changes.append(FieldChange(
                field_path=f"feats.{feat}",
                old_value=None,
                new_value=feat,
                change_type=ChangeType.ADDED,
                priority=ChangePriority.HIGH,
                description=f"Gained feat: {feat}"
            ))
        
        # Lost feats (rare but possible with respec)
        for feat in old_feats - new_feats:
            changes.append(FieldChange(
                field_path=f"feats.{feat}",
                old_value=feat,
                new_value=None,
                change_type=ChangeType.REMOVED,
                priority=ChangePriority.MEDIUM,
                description=f"Lost feat: {feat}"
            ))
        
        return changes
    
    def _extract_feats(self, character_data) -> List[str]:
        """Extract feat names from character data."""
        feats = []
        
        try:
            # Handle both object and dict access
            feats_data = None
            if hasattr(character_data, 'feats'):
                feats_data = character_data.feats
            elif isinstance(character_data, dict) and 'feats' in character_data:
                feats_data = character_data['feats']
            
            if feats_data and isinstance(feats_data, list):
                for feat in feats_data:
                    if isinstance(feat, dict) and 'name' in feat:
                        feats.append(feat['name'])
                    elif isinstance(feat, str):
                        feats.append(feat)
        except Exception as e:
            logger.error(f"Error extracting feats: {str(e)}")
            logger.error(f"Character data type: {type(character_data)}")
        
        return feats
    
    def _detect_equipment_changes(self, old_data, new_data) -> List[FieldChange]:
        """Detect changes to equipped items."""
        changes = []
        
        try:
            logger.debug("Extracting equipped items for comparison...")
            old_equipped = set(self._extract_equipped_items(old_data))
            new_equipped = set(self._extract_equipped_items(new_data))
            
            logger.debug(f"Old equipped items: {len(old_equipped)}, New equipped items: {len(new_equipped)}")
        except Exception as e:
            logger.error(f"Error extracting equipment data: {str(e)}")
            logger.error(f"Old data type: {type(old_data)}, New data type: {type(new_data)}")
            return changes
        
        # Newly equipped items
        for item in new_equipped - old_equipped:
            changes.append(FieldChange(
                field_path=f"equipment.{item}",
                old_value=None,
                new_value=item,
                change_type=ChangeType.ADDED,
                priority=ChangePriority.MEDIUM,
                description=f"Equipped: {item}"
            ))
        
        # Unequipped items
        for item in old_equipped - new_equipped:
            changes.append(FieldChange(
                field_path=f"equipment.{item}",
                old_value=item,
                new_value=None,
                change_type=ChangeType.REMOVED,
                priority=ChangePriority.LOW,
                description=f"Unequipped: {item}"
            ))
        
        return changes
    
    def _extract_equipped_items(self, character_data) -> List[str]:
        """Extract names of equipped items."""
        equipped = []
        
        try:
            # Check equipment slots
            equipment_data = None
            if hasattr(character_data, 'equipment'):
                equipment_data = character_data.equipment
            elif isinstance(character_data, dict) and 'equipment' in character_data:
                equipment_data = character_data['equipment']
            
            if equipment_data and isinstance(equipment_data, dict):
                for slot, item in equipment_data.items():
                    if item and isinstance(item, dict) and 'name' in item:
                        equipped.append(item['name'])
            
            # Also check inventory for equipped items
            inventory_data = None
            if hasattr(character_data, 'inventory'):
                inventory_data = character_data.inventory
            elif isinstance(character_data, dict) and 'inventory' in character_data:
                inventory_data = character_data['inventory']
            
            if inventory_data and isinstance(inventory_data, list):
                for item in inventory_data:
                    if isinstance(item, dict) and item.get('equipped', False) and 'name' in item:
                        equipped.append(item['name'])
        except Exception as e:
            logger.error(f"Error extracting equipped items: {str(e)}")
            logger.error(f"Character data type: {type(character_data)}")
        
        return equipped
    
    def _detect_currency_changes(self, old_data, new_data) -> List[FieldChange]:
        """Detect changes to currency amounts."""
        changes = []
        
        currency_types = ['cp', 'sp', 'gp', 'ep', 'pp']  # copper, silver, gold, electrum, platinum
        
        for currency in currency_types:
            try:
                logger.debug(f"Checking currency: {currency}")
                old_amount = self._get_nested_value(old_data, f'currency.{currency}')
                new_amount = self._get_nested_value(new_data, f'currency.{currency}')
                
                logger.debug(f"  Old {currency}: {old_amount} (type: {type(old_amount)})")
                logger.debug(f"  New {currency}: {new_amount} (type: {type(new_amount)})")
                
                if old_amount != new_amount and old_amount is not None and new_amount is not None:
                    # Add defensive type checking for numeric operations
                    if isinstance(old_amount, (int, float)) and isinstance(new_amount, (int, float)):
                        if abs(new_amount - old_amount) >= 1:  # Only report significant changes
                            change_type = ChangeType.INCREMENTED if new_amount > old_amount else ChangeType.DECREMENTED
                            delta = new_amount - old_amount
                            sign = "+" if delta > 0 else ""
                            
                            changes.append(FieldChange(
                                field_path=f"currency.{currency}",
                                old_value=old_amount,
                                new_value=new_amount,
                                change_type=change_type,
                                priority=ChangePriority.LOW,
                                description=f"{currency.upper()}: {old_amount} → {new_amount} ({sign}{delta})"
                            ))
                    else:
                        logger.warning(f"Non-numeric currency value for {currency}: old={old_amount}, new={new_amount}")
            except Exception as e:
                logger.error(f"Error checking currency {currency}: {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")
                continue
        
        return changes
    
    def _detect_spell_slot_changes(self, old_data, new_data) -> List[FieldChange]:
        """Detect changes to spell slot counts."""
        changes = []
        
        # Check spell slots for levels 1-9
        for level in range(1, 10):
            try:
                logger.debug(f"Checking spell slots for level {level}")
                old_slots = self._get_nested_value(old_data, f'spell_slots.level_{level}.total')
                new_slots = self._get_nested_value(new_data, f'spell_slots.level_{level}.total')
                
                logger.debug(f"  Old level {level} slots: {old_slots} (type: {type(old_slots)})")
                logger.debug(f"  New level {level} slots: {new_slots} (type: {type(new_slots)})")
                
                if old_slots != new_slots and old_slots is not None and new_slots is not None:
                    # Add defensive type checking for numeric operations
                    if isinstance(old_slots, (int, float)) and isinstance(new_slots, (int, float)):
                        if new_slots > 0 or old_slots > 0:  # Only report if there are actual slots
                            change_type = ChangeType.INCREMENTED if new_slots > old_slots else ChangeType.DECREMENTED
                            changes.append(FieldChange(
                                field_path=f"spell_slots.level_{level}",
                                old_value=old_slots,
                                new_value=new_slots,
                                change_type=change_type,
                                priority=ChangePriority.MEDIUM,
                                description=f"Level {level} spell slots: {old_slots} → {new_slots}"
                            ))
                    else:
                        logger.warning(f"Non-numeric spell slot value for level {level}: old={old_slots}, new={new_slots}")
            except Exception as e:
                logger.error(f"Error checking spell slots for level {level}: {str(e)}")
                logger.error(f"Error type: {type(e).__name__}")
                continue
        
        return changes
    
    def _detect_other_field_changes(self, old_data, new_data) -> List[FieldChange]:
        """Detect other field changes using traditional flat comparison, but with exclusions."""
        changes = []
        
        try:
            logger.debug("Flattening character data for field comparison...")
            # Convert to flat data but exclude problematic fields
            old_flat = self._flatten_character_data(old_data)
            new_flat = self._flatten_character_data(new_data)
            
            logger.debug(f"Old flat data fields: {len(old_flat)}, New flat data fields: {len(new_flat)}")
            
            # Remove semantic fields we already handled - comprehensive list to prevent duplicates
            semantic_prefixes = [
                'spells', 'inventory', 'actions', 'class_features', 
                'basic_info.level', 'basic_info.experience', 'basic_info.hit_points', 'basic_info.armor_class',
                'spell_slots', 'ability_scores', 'feats', 'skills', 'proficiencies', 'equipment', 'currency'
            ]
            
            for field_path in list(old_flat.keys()) + list(new_flat.keys()):
                if any(field_path.startswith(prefix) for prefix in semantic_prefixes):
                    old_flat.pop(field_path, None)
                    new_flat.pop(field_path, None)
            
            # Compare remaining fields
            all_fields = set(old_flat.keys()) | set(new_flat.keys())
            logger.debug(f"Fields to compare after filtering: {len(all_fields)}")
            
            # Safely sort field paths, ensuring they are all strings
            try:
                sorted_fields = sorted(str(field) for field in all_fields)
            except (TypeError, ValueError) as e:
                logger.warning(f"Error sorting field paths, using unsorted: {e}")
                sorted_fields = list(all_fields)
            
            for field_path in sorted_fields:
                try:
                    if self._is_field_excluded(field_path):
                        continue
                    
                    old_value = old_flat.get(field_path)
                    new_value = new_flat.get(field_path)
                    
                    logger.debug(f"Comparing field {field_path}: old={type(old_value)}, new={type(new_value)}")
                    
                    # Add defensive comparison to avoid dict comparison errors
                    if self._safe_compare_values(old_value, new_value):
                        change = self._create_field_change(field_path, old_value, new_value)
                        if change:
                            changes.append(change)
                except Exception as e:
                    logger.error(f"Error comparing field {field_path}: {str(e)}")
                    logger.error(f"  Old value: {old_value} (type: {type(old_value)})")
                    logger.error(f"  New value: {new_value} (type: {type(new_value)})")
                    continue
        
        except Exception as e:
            logger.error(f"Error in field-by-field comparison: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            return changes
        
        return changes
    
    def _get_nested_value(self, data, field_path: str):
        """Get a value from nested data using dot notation."""
        try:
            current = data
            logger.debug(f"Getting nested value for path: {field_path}")
            for part in field_path.split('.'):
                logger.debug(f"  Accessing part: {part} from {type(current)}")
                if hasattr(current, part):
                    current = getattr(current, part)
                elif isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    logger.debug(f"  Part {part} not found in {type(current)}")
                    return None
            logger.debug(f"  Final value: {current} (type: {type(current)})")
            return current
        except (AttributeError, KeyError, TypeError) as e:
            logger.debug(f"Error getting nested value for {field_path}: {str(e)}")
            return None
    
    def _is_field_excluded(self, field_path: str) -> bool:
        """Check if a field should be excluded from change detection."""
        for excluded_pattern in self.excluded_fields:
            if fnmatch.fnmatch(field_path, excluded_pattern):
                return True
        return False
    
    def _flatten_character_data(self, character: Any, prefix: str = '') -> Dict[str, Any]:
        """
        Flatten nested character data into dot-notation paths.
        
        Args:
            character: Character data to flatten
            prefix: Current path prefix
            
        Returns:
            Dictionary with flattened field paths
        """
        flat_data = {}
        
        if hasattr(character, '__dict__'):
            data = character.__dict__
        elif isinstance(character, dict):
            data = character
        else:
            return {prefix: character}
        
        for key, value in data.items():
            current_path = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict) or (hasattr(value, '__dict__') and not isinstance(value, (str, int, float, bool, type(None), list))):
                # Recursively flatten nested objects
                nested_data = self._flatten_character_data(value, current_path)
                flat_data.update(nested_data)
            elif isinstance(value, list):
                # Handle lists by indexing or treating as a whole
                if len(value) > 0 and (isinstance(value[0], dict) or (hasattr(value[0], '__dict__') and not isinstance(value[0], (str, int, float, bool, type(None))))):
                    # List of objects - flatten each with index
                    for i, item in enumerate(value):
                        item_data = self._flatten_character_data(item, f"{current_path}[{i}]")
                        flat_data.update(item_data)
                else:
                    # Simple list - store as whole value
                    flat_data[current_path] = value
            else:
                # Primitive value
                flat_data[current_path] = value
        
        return flat_data
    
    def _create_field_change(
        self,
        field_path: str,
        old_value: Any,
        new_value: Any
    ) -> Optional[FieldChange]:
        """
        Create a FieldChange object with appropriate metadata.
        
        Args:
            field_path: Dot-notation path to the field
            old_value: Previous value
            new_value: Current value
            
        Returns:
            FieldChange object or None if change should be ignored
        """
        try:
            logger.debug(f"Creating field change for {field_path}")
            logger.debug(f"  Old: {old_value} (type: {type(old_value)})")
            logger.debug(f"  New: {new_value} (type: {type(new_value)})")
            
            # Determine change type
            if old_value is None:
                change_type = ChangeType.ADDED
            elif new_value is None:
                change_type = ChangeType.REMOVED
            elif self._is_numeric_field(field_path) and self._is_numeric(old_value) and self._is_numeric(new_value):
                # Numeric field - determine if increment or decrement
                try:
                    old_num = float(old_value)
                    new_num = float(new_value)
                    if new_num > old_num:
                        change_type = ChangeType.INCREMENTED
                    else:
                        change_type = ChangeType.DECREMENTED
                except (ValueError, TypeError) as e:
                    logger.warning(f"Error converting numeric values for {field_path}: {str(e)}")
                    change_type = ChangeType.MODIFIED
            else:
                change_type = ChangeType.MODIFIED
            
            # Determine priority
            priority = self._get_field_priority(field_path)
            
            # Generate description
            description = self._generate_change_description(field_path, old_value, new_value, change_type)
            
            return FieldChange(
                field_path=field_path,
                old_value=old_value,
                new_value=new_value,
                change_type=change_type,
                priority=priority,
                description=description
            )
        except Exception as e:
            logger.error(f"Error creating field change for {field_path}: {str(e)}")
            logger.error(f"  Old value: {old_value} (type: {type(old_value)})")
            logger.error(f"  New value: {new_value} (type: {type(new_value)})")
            return None
    
    def _is_numeric_field(self, field_path: str) -> bool:
        """Check if a field path represents a numeric field."""
        return any(fnmatch.fnmatch(field_path, pattern) for pattern in self.numeric_fields)
    
    def _is_numeric(self, value: Any) -> bool:
        """Check if a value is numeric."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    def _get_field_priority(self, field_path: str) -> ChangePriority:
        """Determine the priority of a field change."""
        if any(fnmatch.fnmatch(field_path, pattern) for pattern in self.high_priority_fields):
            return ChangePriority.HIGH
        elif any(fnmatch.fnmatch(field_path, pattern) for pattern in self.medium_priority_fields):
            return ChangePriority.MEDIUM
        else:
            return ChangePriority.LOW
    
    def _generate_change_description(
        self,
        field_path: str,
        old_value: Any,
        new_value: Any,
        change_type: ChangeType
    ) -> str:
        """Generate a human-readable description of the change."""
        field_name = self._humanize_field_name(field_path)
        
        # Special handling for certain types of changes
        if change_type == ChangeType.ADDED:
            # Special cases for added items
            if field_path.startswith('spells.'):
                return f"Learned spell: {new_value}"
            elif field_path.startswith('feats.'):
                return f"Gained feat: {new_value}"
            elif field_path.startswith('inventory.'):
                return f"Added to inventory: {new_value}"
            elif field_path.startswith('equipment.'):
                return f"Equipped: {new_value}"
            elif field_path.startswith('proficiencies.'):
                return f"Gained proficiency: {new_value}"
            elif field_path.startswith('skills.') and field_path.endswith('.proficient'):
                skill_name = field_path.split('.')[1].replace('_', ' ').title()
                return f"Gained skill proficiency: {skill_name}"
            else:
                return f"{field_name} added: {new_value}"
        
        elif change_type == ChangeType.REMOVED:
            # Special cases for removed items
            if field_path.startswith('spells.'):
                return f"Forgot spell: {old_value}"
            elif field_path.startswith('feats.'):
                return f"Lost feat: {old_value}"
            elif field_path.startswith('inventory.'):
                return f"Removed from inventory: {old_value}"
            elif field_path.startswith('equipment.'):
                return f"Unequipped: {old_value}"
            elif field_path.startswith('proficiencies.'):
                return f"Lost proficiency: {old_value}"
            elif field_path.startswith('skills.') and field_path.endswith('.proficient'):
                skill_name = field_path.split('.')[1].replace('_', ' ').title()
                return f"Lost skill proficiency: {skill_name}"
            else:
                return f"{field_name} removed: {old_value}"
        
        elif change_type == ChangeType.INCREMENTED:
            try:
                delta = float(new_value) - float(old_value)
                # Special formatting for different types of increments
                if field_path.startswith('spell_slots.'):
                    if delta == 1:
                        return f"{field_name}: {old_value} → {new_value} (+1 slot)"
                    else:
                        return f"{field_name}: {old_value} → {new_value} (+{delta:g} slots)"
                elif field_path.startswith('currency.'):
                    currency_type = field_path.split('.')[-1].upper()
                    return f"{field_name}: {old_value} → {new_value} (+{delta:g} {currency_type})"
                elif field_path.startswith('ability_scores.'):
                    return f"{field_name}: {old_value} → {new_value} (+{delta:g})"
                elif field_path.startswith('basic_info.level'):
                    return f"Level increased: {old_value} → {new_value}"
                elif field_path.startswith('basic_info.experience'):
                    return f"Experience gained: {old_value} → {new_value} (+{delta:g} XP)"
                elif field_path.startswith('basic_info.hit_points'):
                    return f"{field_name}: {old_value} → {new_value} (+{delta:g} HP)"
                else:
                    return f"{field_name}: {old_value} → {new_value} (+{delta:g})"
            except (ValueError, TypeError):
                return f"{field_name}: {old_value} → {new_value}"
        
        elif change_type == ChangeType.DECREMENTED:
            try:
                delta = float(new_value) - float(old_value)
                # Special formatting for different types of decrements
                if field_path.startswith('spell_slots.'):
                    if abs(delta) == 1:
                        return f"{field_name}: {old_value} → {new_value} (-1 slot)"
                    else:
                        return f"{field_name}: {old_value} → {new_value} ({delta:g} slots)"
                elif field_path.startswith('currency.'):
                    currency_type = field_path.split('.')[-1].upper()
                    return f"{field_name}: {old_value} → {new_value} ({delta:g} {currency_type})"
                elif field_path.startswith('ability_scores.'):
                    return f"{field_name}: {old_value} → {new_value} ({delta:g})"
                elif field_path.startswith('basic_info.level'):
                    return f"Level decreased: {old_value} → {new_value}"
                elif field_path.startswith('basic_info.experience'):
                    return f"Experience lost: {old_value} → {new_value} ({delta:g} XP)"
                elif field_path.startswith('basic_info.hit_points'):
                    return f"{field_name}: {old_value} → {new_value} ({delta:g} HP)"
                else:
                    return f"{field_name}: {old_value} → {new_value} ({delta:g})"
            except (ValueError, TypeError):
                return f"{field_name}: {old_value} → {new_value}"
        
        else:
            # Modified change type
            return f"{field_name} changed: {old_value} → {new_value}"
    
    def _humanize_field_name(self, field_path: str) -> str:
        """Convert a field path to a human-readable name with better context preservation."""
        # Special handling for common field patterns to preserve context
        if field_path.startswith('spell_slots.level_'):
            level = field_path.split('.')[-1].replace('level_', '')
            return f"Level {level} spell slots"
        
        if field_path.startswith('spell_slots.') and field_path.endswith('.total'):
            # Handle spell_slots.level_4.total patterns
            parts = field_path.split('.')
            if len(parts) >= 2 and parts[1].startswith('level_'):
                level = parts[1].replace('level_', '')
                return f"Level {level} spell slots"
        
        if field_path.startswith('ability_scores.'):
            ability = field_path.split('.')[-1].replace('_', ' ')
            return f"{ability.title()} score"
        
        if field_path.startswith('feats.') and len(field_path.split('.')) >= 2:
            feat_name = field_path.split('.')[1].replace('_', ' ')
            return f"Feat: {feat_name}"
        
        if field_path.startswith('spells.') and len(field_path.split('.')) >= 2:
            spell_name = field_path.split('.')[1].replace('_', ' ')
            return f"Spell: {spell_name}"
        
        if field_path.startswith('inventory.') and len(field_path.split('.')) >= 2:
            item_name = field_path.split('.')[1].replace('_', ' ')
            if field_path.endswith('.quantity'):
                return f"{item_name} quantity"
            return f"Item: {item_name}"
        
        if field_path.startswith('equipment.') and len(field_path.split('.')) >= 2:
            item_name = field_path.split('.')[1].replace('_', ' ')
            return f"Equipment: {item_name}"
        
        if field_path.startswith('skills.') and len(field_path.split('.')) >= 2:
            skill_name = field_path.split('.')[1].replace('_', ' ')
            return f"{skill_name.title()} skill"
        
        if field_path.startswith('proficiencies.') and len(field_path.split('.')) >= 3:
            prof_type = field_path.split('.')[1].replace('_', ' ')
            prof_name = field_path.split('.')[2].replace('_', ' ')
            return f"{prof_type.title()} proficiency: {prof_name}"
        
        if field_path.startswith('currency.'):
            currency_type = field_path.split('.')[-1].upper()
            return f"{currency_type} currency"
        
        # Handle class-specific caster levels
        if 'caster_level' in field_path.lower():
            parts = field_path.split('.')
            # Look for class context in the path
            for i, part in enumerate(parts):
                if part.lower() in ['wizard', 'sorcerer', 'cleric', 'druid', 'bard', 'warlock', 'paladin', 'ranger', 'artificer', 'fighter', 'rogue']:
                    return f"{part.title()} caster level"
            # If no class found, use generic
            return "Caster level"
        
        # Handle multi-classing patterns
        if 'classes.' in field_path:
            parts = field_path.split('.')
            if len(parts) >= 3:
                class_name = parts[1].replace('_', ' ')
                field_name = parts[2].replace('_', ' ')
                return f"{class_name.title()} {field_name}"
        
        # Generic handling - preserve more context from the path
        parts = field_path.replace('_', ' ').split('.')
        
        # If we have multiple parts, try to preserve meaningful context
        if len(parts) >= 2:
            # For paths like 'basic_info.level', use 'Basic Info Level'
            # For paths like 'hit_points.maximum', use 'Hit Points Maximum'  
            if len(parts) == 2:
                return f"{parts[0].title()} {parts[1].title()}"
            # For longer paths, use the last 2 parts to preserve context
            elif len(parts) >= 3:
                return f"{parts[-2].title()} {parts[-1].title()}"
        
        # Fallback to just the last part
        return ' '.join(word.title() for word in parts[-1].split())
    
    def _generate_change_summary(self, changes: List[FieldChange]) -> str:
        """Generate a summary of all changes."""
        if not changes:
            return "No changes detected"
        
        high_priority = len([c for c in changes if c.priority == ChangePriority.HIGH])
        medium_priority = len([c for c in changes if c.priority == ChangePriority.MEDIUM])
        low_priority = len([c for c in changes if c.priority == ChangePriority.LOW])
        
        summary_parts = []
        if high_priority:
            summary_parts.append(f"{high_priority} high priority")
        if medium_priority:
            summary_parts.append(f"{medium_priority} medium priority")
        if low_priority:
            summary_parts.append(f"{low_priority} low priority")
        
        return f"{len(changes)} total changes: {', '.join(summary_parts)}"
    
    def filter_changes_by_groups(
        self,
        changes: List[FieldChange],
        include_groups: Optional[Set[str]] = None,
        exclude_groups: Optional[Set[str]] = None,
        group_definitions: Optional[Dict[str, List[str]]] = None
    ) -> List[FieldChange]:
        """
        Filter changes based on data group membership.
        
        Args:
            changes: List of changes to filter
            include_groups: Groups to include (None = include all)
            exclude_groups: Groups to exclude
            group_definitions: Mapping of group names to field patterns
            
        Returns:
            Filtered list of changes
        """
        if not group_definitions:
            group_definitions = self._get_default_group_definitions()
        
        filtered_changes = []
        
        for change in changes:
            field_path = change.field_path
            
            # Check if field belongs to any excluded groups
            if exclude_groups:
                excluded = False
                for group_name in exclude_groups:
                    if group_name in group_definitions:
                        patterns = group_definitions[group_name]
                        if any(fnmatch.fnmatch(field_path, pattern) for pattern in patterns):
                            excluded = True
                            break
                if excluded:
                    continue
            
            # Check if field belongs to any included groups (if specified)
            if include_groups:
                included = False
                for group_name in include_groups:
                    if group_name in group_definitions:
                        patterns = group_definitions[group_name]
                        if any(fnmatch.fnmatch(field_path, pattern) for pattern in patterns):
                            included = True
                            break
                if not included:
                    continue
            
            filtered_changes.append(change)
        
        if len(changes) == len(filtered_changes):
            logger.info(f"All {len(changes)} changes passed filtering")
        else:
            logger.info(f"Filtered {len(changes)} changes to {len(filtered_changes)} changes")
            
        # Log filtering details
        if include_groups or exclude_groups:
            logger.info("Filtering settings:")
            if include_groups:
                logger.info(f"  Include groups: {sorted(include_groups)}")
            if exclude_groups:
                logger.info(f"  Exclude groups: {sorted(exclude_groups)}")
        else:
            logger.info("No filtering applied (debug preset = include all)")
        return filtered_changes
    
    def _safe_compare_values(self, old_value: Any, new_value: Any) -> bool:
        """
        Safely compare two values, handling dict/complex types that may cause comparison errors.
        
        Args:
            old_value: Previous value
            new_value: Current value
            
        Returns:
            True if values are different, False if same or comparison fails
        """
        try:
            # Handle None values
            if old_value is None and new_value is None:
                return False
            if old_value is None or new_value is None:
                return True
            
            # Handle dict comparison - these can cause "'>' not supported" errors
            if isinstance(old_value, dict) and isinstance(new_value, dict):
                logger.debug(f"Comparing dictionaries: old keys={list(old_value.keys())}, new keys={list(new_value.keys())}")
                # For dictionaries, check if they have the same keys and values
                if set(old_value.keys()) != set(new_value.keys()):
                    return True
                for key in old_value.keys():
                    if not self._safe_compare_values(old_value[key], new_value[key]):
                        return True
                return False
            
            # Handle list comparison
            if isinstance(old_value, list) and isinstance(new_value, list):
                logger.debug(f"Comparing lists: old len={len(old_value)}, new len={len(new_value)}")
                if len(old_value) != len(new_value):
                    return True
                for i, (old_item, new_item) in enumerate(zip(old_value, new_value)):
                    if self._safe_compare_values(old_item, new_item):
                        return True
                return False
            
            # Handle mixed types
            if type(old_value) != type(new_value):
                logger.debug(f"Different types: {type(old_value)} vs {type(new_value)}")
                return True
            
            # For simple types, use direct comparison
            return old_value != new_value
            
        except Exception as e:
            logger.error(f"Error in safe comparison: {str(e)}")
            logger.error(f"  Old value: {old_value} (type: {type(old_value)})")
            logger.error(f"  New value: {new_value} (type: {type(new_value)})")
            # If comparison fails, assume they're different to be safe
            return True
    
    def _get_default_group_definitions(self) -> Dict[str, List[str]]:
        """Get default data group definitions."""
        return {
            'basic': [
                'basic_info.name',
                'basic_info.level',
                'basic_info.experience',
                'basic_info.classes.*',
                'features.*',
                'class_features.*'
            ],
            'combat': [
                'basic_info.hit_points.*',
                'hit_points.*',
                'basic_info.armor_class.*',
                'armor_class.*',
                'basic_info.initiative.*',
                'saving_throws.*'
            ],
            'abilities': [
                'ability_scores.*',
                'ability_modifiers.*'
            ],
            'spells': [
                'spells.*',
                'spell_slots.*',
                'spellcasting.*'
            ],
            'inventory': [
                'inventory.*',
                'equipment.*',
                'currency.*'
            ],
            'skills': [
                'skills.*',
                'proficiencies.*',
                'feats.*'
            ],
            'appearance': [
                'appearance.*',
                'basic_info.avatar*',
                'decorations.*'
            ],
            'backstory': [
                'background.*',
                'backstory.*',
                'basic_info.background*'
            ],
            'meta': [
                'meta.*',
                'processed_date',
                'scraper_version'
            ]
        }
    
    def _deduplicate_changes(self, changes: List[FieldChange]) -> List[FieldChange]:
        """Remove duplicate changes based on field path and description similarity."""
        if not changes:
            return changes
        
        # Group changes by field path
        field_groups = {}
        for change in changes:
            field_path = change.field_path
            if field_path not in field_groups:
                field_groups[field_path] = []
            field_groups[field_path].append(change)
        
        deduplicated = []
        duplicates_removed = 0
        
        for field_path, field_changes in field_groups.items():
            if len(field_changes) == 1:
                # No duplicates for this field
                deduplicated.extend(field_changes)
            else:
                # Multiple changes for same field - pick the best one
                # Prioritize semantic method descriptions over generic ones
                best_change = field_changes[0]
                for change in field_changes[1:]:
                    # Prefer changes with more descriptive descriptions
                    if len(change.description or '') > len(best_change.description or ''):
                        best_change = change
                    # Prefer changes that don't use generic field names
                    elif (change.description and 
                          not any(generic in change.description.lower() 
                                 for generic in ['field', 'value', 'changed', 'modified'])):
                        best_change = change
                
                deduplicated.append(best_change)
                duplicates_removed += len(field_changes) - 1
        
        if duplicates_removed > 0:
            logger.info(f"Removed {duplicates_removed} duplicate changes during deduplication")
        
        return deduplicated