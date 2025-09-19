"""
Enhanced Change Detection Models

Extended configuration and field mappings for comprehensive D&D Beyond character change tracking.
Supports new change types including feats, subclass, spells, inventory, background, max HP, 
proficiencies, ability scores, race, multiclass, personality traits, spellcasting stats, 
initiative, passive skills, alignment, size, and movement speed.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, List, Optional, Set
from pathlib import Path

from shared.models.change_detection import ChangeCategory, ChangePriority


class EnhancedChangeType(Enum):
    """Enhanced change types for comprehensive character tracking."""
    FEAT_ADDED = "feat_added"
    FEAT_REMOVED = "feat_removed"
    FEAT_MODIFIED = "feat_modified"
    SUBCLASS_CHANGED = "subclass_changed"
    SPELL_ADDED = "spell_added"
    SPELL_REMOVED = "spell_removed"
    SPELL_MODIFIED = "spell_modified"
    INVENTORY_ADDED = "inventory_added"
    INVENTORY_REMOVED = "inventory_removed"
    INVENTORY_QUANTITY_CHANGED = "inventory_quantity_changed"
    BACKGROUND_CHANGED = "background_changed"
    MAX_HP_CHANGED = "max_hp_changed"
    PROFICIENCY_ADDED = "proficiency_added"
    PROFICIENCY_REMOVED = "proficiency_removed"
    ABILITY_SCORE_CHANGED = "ability_score_changed"
    RACE_SPECIES_CHANGED = "race_species_changed"
    MULTICLASS_PROGRESSION = "multiclass_progression"
    PERSONALITY_CHANGED = "personality_changed"
    SPELLCASTING_STATS_CHANGED = "spellcasting_stats_changed"
    INITIATIVE_CHANGED = "initiative_changed"
    PASSIVE_SKILLS_CHANGED = "passive_skills_changed"
    ALIGNMENT_CHANGED = "alignment_changed"
    SIZE_CHANGED = "size_changed"
    MOVEMENT_SPEED_CHANGED = "movement_speed_changed"


@dataclass
class EnhancedFieldMapping:
    """Enhanced field mapping configuration for D&D Beyond API structure."""
    api_path: str  # Path in D&D Beyond API response
    display_name: str  # Human-readable name for the field
    priority: ChangePriority  # Default priority for changes to this field
    category: ChangeCategory  # Category this field belongs to
    change_types: List[EnhancedChangeType] = field(default_factory=list)  # Supported change types
    validation_rules: Dict[str, Any] = field(default_factory=dict)  # Validation rules
    causation_patterns: List[str] = field(default_factory=list)  # Patterns for causation detection
    
    def matches_path(self, field_path: str) -> bool:
        """Check if a field path matches this mapping."""
        import fnmatch
        return fnmatch.fnmatch(field_path, self.api_path)


@dataclass
class ChangeDetectionConfig:
    """Enhanced configuration for change detection service."""
    # Change type enablement
    enabled_change_types: Set[str] = field(default_factory=lambda: {
        'level', 'feats', 'subclass', 'spells', 'inventory', 'background', 
        'max_hp', 'proficiencies', 'ability_scores', 'race_species',
        'multiclass', 'personality', 'spellcasting_stats', 'initiative',
        'passive_skills', 'alignment', 'size', 'movement_speed'
    })
    
    # Change log settings
    enable_change_logging: bool = True
    change_log_storage_dir: str = "character_data/change_logs"
    change_log_retention_days: int = 365
    change_log_rotation_size_mb: int = 10
    
    # Discord notification settings
    discord_only_high_priority: bool = False
    discord_include_low_priority: bool = False
    
    # Priority overrides
    priority_overrides: Dict[str, ChangePriority] = field(default_factory=dict)
    
    # Field mapping customizations
    custom_field_mappings: Dict[str, Dict[str, str]] = field(default_factory=dict)
    
    # Causation analysis settings
    enable_causation_analysis: bool = True
    causation_confidence_threshold: float = 0.7
    max_cascade_depth: int = 3
    
    # Detection sensitivity settings
    detect_minor_changes: bool = False
    detect_metadata_changes: bool = False
    detect_cosmetic_changes: bool = False
    
    def __post_init__(self):
        """Ensure storage_dir is a Path object."""
        if not isinstance(self.change_log_storage_dir, Path):
            self.change_log_storage_dir = Path(self.change_log_storage_dir)


# Enhanced field mappings for D&D Beyond API structure
ENHANCED_FIELD_MAPPINGS = {
    # Feats
    'feats': EnhancedFieldMapping(
        api_path='character.feats',
        display_name='Feats',
        priority=ChangePriority.HIGH,
        category=ChangeCategory.FEATURES,
        change_types=[EnhancedChangeType.FEAT_ADDED, EnhancedChangeType.FEAT_REMOVED, EnhancedChangeType.FEAT_MODIFIED],
        causation_patterns=['*proficienc*', '*skill*', '*ability_score*', '*spell*', '*combat*']
    ),
    
    'feat_individual': EnhancedFieldMapping(
        api_path='character.feats.*',
        display_name='Individual Feat',
        priority=ChangePriority.HIGH,
        category=ChangeCategory.FEATURES,
        change_types=[EnhancedChangeType.FEAT_ADDED, EnhancedChangeType.FEAT_REMOVED, EnhancedChangeType.FEAT_MODIFIED],
        causation_patterns=['*proficienc*', '*skill*', '*ability_score*', '*spell*', '*combat*']
    ),
    
    # Subclass
    'subclass': EnhancedFieldMapping(
        api_path='character.classes.*.subclass',
        display_name='Subclass',
        priority=ChangePriority.HIGH,
        category=ChangeCategory.PROGRESSION,
        change_types=[EnhancedChangeType.SUBCLASS_CHANGED],
        causation_patterns=['*feature*', '*spell*', '*proficienc*']
    ),
    
    # Spells
    'spells_known': EnhancedFieldMapping(
        api_path='character.spells.known',
        display_name='Known Spells',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.SPELLS,
        change_types=[EnhancedChangeType.SPELL_ADDED, EnhancedChangeType.SPELL_REMOVED],
        causation_patterns=['*level*', '*feat*', '*class_feature*']
    ),
    
    'spells_prepared': EnhancedFieldMapping(
        api_path='character.spells.prepared',
        display_name='Prepared Spells',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.SPELLS,
        change_types=[EnhancedChangeType.SPELL_ADDED, EnhancedChangeType.SPELL_REMOVED],
        causation_patterns=['*wisdom*', '*intelligence*', '*charisma*', '*level*']
    ),
    
    'spell_slots': EnhancedFieldMapping(
        api_path='character.spellcasting.spell_slots.*',
        display_name='Spell Slots',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.SPELLS,
        change_types=[EnhancedChangeType.SPELL_MODIFIED],
        causation_patterns=['*level*', '*multiclass*']
    ),
    
    # Inventory and Equipment
    'inventory': EnhancedFieldMapping(
        api_path='character.inventory.*',
        display_name='Inventory',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.INVENTORY,
        change_types=[EnhancedChangeType.INVENTORY_ADDED, EnhancedChangeType.INVENTORY_REMOVED, EnhancedChangeType.INVENTORY_QUANTITY_CHANGED],
        causation_patterns=['*armor_class*', '*attack*', '*damage*']
    ),
    
    'equipment': EnhancedFieldMapping(
        api_path='character.equipment.*',
        display_name='Equipment',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.EQUIPMENT,
        change_types=[EnhancedChangeType.INVENTORY_ADDED, EnhancedChangeType.INVENTORY_REMOVED],
        causation_patterns=['*armor_class*', '*attack*', '*damage*', '*ability_score*']
    ),
    
    # Background
    'background': EnhancedFieldMapping(
        api_path='character.background',
        display_name='Background',
        priority=ChangePriority.HIGH,
        category=ChangeCategory.BASIC_INFO,
        change_types=[EnhancedChangeType.BACKGROUND_CHANGED],
        causation_patterns=['*proficienc*', '*skill*', '*language*', '*tool*']
    ),
    
    # Maximum Hit Points
    'max_hp': EnhancedFieldMapping(
        api_path='character.baseHitPoints',
        display_name='Maximum Hit Points',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.COMBAT,
        change_types=[EnhancedChangeType.MAX_HP_CHANGED],
        causation_patterns=['*level*', '*constitution*', '*feat*', '*class_feature*']
    ),
    
    'hit_points_maximum': EnhancedFieldMapping(
        api_path='character.hitPoints.maximum',
        display_name='Maximum Hit Points',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.COMBAT,
        change_types=[EnhancedChangeType.MAX_HP_CHANGED],
        causation_patterns=['*level*', '*constitution*', '*feat*', '*class_feature*']
    ),
    
    # Proficiencies
    'skill_proficiencies': EnhancedFieldMapping(
        api_path='character.proficiencies.skills.*',
        display_name='Skill Proficiencies',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.SKILLS,
        change_types=[EnhancedChangeType.PROFICIENCY_ADDED, EnhancedChangeType.PROFICIENCY_REMOVED],
        causation_patterns=['*background*', '*class*', '*feat*', '*race*']
    ),
    
    'saving_throw_proficiencies': EnhancedFieldMapping(
        api_path='character.proficiencies.saving_throws.*',
        display_name='Saving Throw Proficiencies',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.ABILITIES,
        change_types=[EnhancedChangeType.PROFICIENCY_ADDED, EnhancedChangeType.PROFICIENCY_REMOVED],
        causation_patterns=['*class*', '*multiclass*']
    ),
    
    'tool_proficiencies': EnhancedFieldMapping(
        api_path='character.proficiencies.tools.*',
        display_name='Tool Proficiencies',
        priority=ChangePriority.LOW,
        category=ChangeCategory.SKILLS,
        change_types=[EnhancedChangeType.PROFICIENCY_ADDED, EnhancedChangeType.PROFICIENCY_REMOVED],
        causation_patterns=['*background*', '*feat*', '*race*']
    ),
    
    'language_proficiencies': EnhancedFieldMapping(
        api_path='character.proficiencies.languages.*',
        display_name='Language Proficiencies',
        priority=ChangePriority.LOW,
        category=ChangeCategory.SKILLS,
        change_types=[EnhancedChangeType.PROFICIENCY_ADDED, EnhancedChangeType.PROFICIENCY_REMOVED],
        causation_patterns=['*background*', '*feat*', '*race*']
    ),
    
    # Ability Scores
    'ability_scores': EnhancedFieldMapping(
        api_path='character.abilityScores.*',
        display_name='Ability Scores',
        priority=ChangePriority.HIGH,
        category=ChangeCategory.ABILITIES,
        change_types=[EnhancedChangeType.ABILITY_SCORE_CHANGED],
        causation_patterns=['*skill*', '*saving_throw*', '*spell_attack*', '*spell_save_dc*', '*initiative*', '*feat*', '*level*']
    ),
    
    # Race/Species
    'race': EnhancedFieldMapping(
        api_path='character.race',
        display_name='Race/Species',
        priority=ChangePriority.HIGH,
        category=ChangeCategory.BASIC_INFO,
        change_types=[EnhancedChangeType.RACE_SPECIES_CHANGED],
        causation_patterns=['*ability_score*', '*proficienc*', '*trait*', '*speed*', '*size*']
    ),
    
    'species': EnhancedFieldMapping(
        api_path='character.species',
        display_name='Species',
        priority=ChangePriority.HIGH,
        category=ChangeCategory.BASIC_INFO,
        change_types=[EnhancedChangeType.RACE_SPECIES_CHANGED],
        causation_patterns=['*ability_score*', '*proficienc*', '*trait*', '*speed*', '*size*']
    ),
    
    # Multiclass
    'class_levels': EnhancedFieldMapping(
        api_path='character.classes.*.level',
        display_name='Class Levels',
        priority=ChangePriority.HIGH,
        category=ChangeCategory.PROGRESSION,
        change_types=[EnhancedChangeType.MULTICLASS_PROGRESSION],
        causation_patterns=['*feature*', '*spell*', '*hit_point*', '*proficienc*']
    ),
    
    'multiclass': EnhancedFieldMapping(
        api_path='character.classes',
        display_name='Multiclass Progression',
        priority=ChangePriority.HIGH,
        category=ChangeCategory.PROGRESSION,
        change_types=[EnhancedChangeType.MULTICLASS_PROGRESSION],
        causation_patterns=['*feature*', '*spell*', '*hit_point*', '*proficienc*', '*spell_slot*']
    ),
    
    # Personality Traits
    'personality_traits': EnhancedFieldMapping(
        api_path='character.traits',
        display_name='Personality Traits',
        priority=ChangePriority.LOW,
        category=ChangeCategory.SOCIAL,
        change_types=[EnhancedChangeType.PERSONALITY_CHANGED],
        causation_patterns=[]
    ),
    
    'ideals': EnhancedFieldMapping(
        api_path='character.ideals',
        display_name='Ideals',
        priority=ChangePriority.LOW,
        category=ChangeCategory.SOCIAL,
        change_types=[EnhancedChangeType.PERSONALITY_CHANGED],
        causation_patterns=[]
    ),
    
    'bonds': EnhancedFieldMapping(
        api_path='character.bonds',
        display_name='Bonds',
        priority=ChangePriority.LOW,
        category=ChangeCategory.SOCIAL,
        change_types=[EnhancedChangeType.PERSONALITY_CHANGED],
        causation_patterns=[]
    ),
    
    'flaws': EnhancedFieldMapping(
        api_path='character.flaws',
        display_name='Flaws',
        priority=ChangePriority.LOW,
        category=ChangeCategory.SOCIAL,
        change_types=[EnhancedChangeType.PERSONALITY_CHANGED],
        causation_patterns=[]
    ),
    
    # Spellcasting Stats
    'spell_attack_bonus': EnhancedFieldMapping(
        api_path='character.spellcastingInfo.spellAttackBonus',
        display_name='Spell Attack Bonus',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.SPELLS,
        change_types=[EnhancedChangeType.SPELLCASTING_STATS_CHANGED],
        causation_patterns=['*ability_score*', '*proficiency_bonus*', '*feat*', '*equipment*']
    ),
    
    'spell_save_dc': EnhancedFieldMapping(
        api_path='character.spellcastingInfo.spellSaveDc',
        display_name='Spell Save DC',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.SPELLS,
        change_types=[EnhancedChangeType.SPELLCASTING_STATS_CHANGED],
        causation_patterns=['*ability_score*', '*proficiency_bonus*', '*feat*', '*equipment*']
    ),
    
    # Initiative
    'initiative_bonus': EnhancedFieldMapping(
        api_path='character.initiative.bonus',
        display_name='Initiative Bonus',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.COMBAT,
        change_types=[EnhancedChangeType.INITIATIVE_CHANGED],
        causation_patterns=['*dexterity*', '*feat*', '*equipment*', '*class_feature*']
    ),
    
    'combat_initiative_bonus': EnhancedFieldMapping(
        api_path='character.combat.initiative_bonus',
        display_name='Initiative Bonus',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.COMBAT,
        change_types=[EnhancedChangeType.INITIATIVE_CHANGED],
        causation_patterns=['*dexterity*', '*feat*', '*equipment*', '*class_feature*']
    ),
    
    'combat_initiative_modifier': EnhancedFieldMapping(
        api_path='character.combat.initiative_modifier',
        display_name='Initiative Modifier',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.COMBAT,
        change_types=[EnhancedChangeType.INITIATIVE_CHANGED],
        causation_patterns=['*dexterity*', '*feat*', '*equipment*', '*class_feature*']
    ),
    
    # Passive Skills
    'passive_perception': EnhancedFieldMapping(
        api_path='character.passivePerception',
        display_name='Passive Perception',
        priority=ChangePriority.LOW,
        category=ChangeCategory.SKILLS,
        change_types=[EnhancedChangeType.PASSIVE_SKILLS_CHANGED],
        causation_patterns=['*wisdom*', '*proficiency*', '*feat*', '*equipment*']
    ),
    
    'passive_investigation': EnhancedFieldMapping(
        api_path='character.passiveInvestigation',
        display_name='Passive Investigation',
        priority=ChangePriority.LOW,
        category=ChangeCategory.SKILLS,
        change_types=[EnhancedChangeType.PASSIVE_SKILLS_CHANGED],
        causation_patterns=['*intelligence*', '*proficiency*', '*feat*', '*equipment*']
    ),
    
    'passive_insight': EnhancedFieldMapping(
        api_path='character.passiveInsight',
        display_name='Passive Insight',
        priority=ChangePriority.LOW,
        category=ChangeCategory.SKILLS,
        change_types=[EnhancedChangeType.PASSIVE_SKILLS_CHANGED],
        causation_patterns=['*wisdom*', '*proficiency*', '*feat*', '*equipment*']
    ),
    
    # Alignment
    'alignment': EnhancedFieldMapping(
        api_path='character.alignment',
        display_name='Alignment',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.BASIC_INFO,
        change_types=[EnhancedChangeType.ALIGNMENT_CHANGED],
        causation_patterns=[]
    ),
    
    # Size
    'size': EnhancedFieldMapping(
        api_path='character.size',
        display_name='Size Category',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.BASIC_INFO,
        change_types=[EnhancedChangeType.SIZE_CHANGED],
        causation_patterns=['*race*', '*feat*', '*spell*', '*equipment*']
    ),
    
    # Movement Speed
    'walking_speed': EnhancedFieldMapping(
        api_path='character.speed.walking',
        display_name='Walking Speed',
        priority=ChangePriority.LOW,
        category=ChangeCategory.BASIC_INFO,
        change_types=[EnhancedChangeType.MOVEMENT_SPEED_CHANGED],
        causation_patterns=['*race*', '*feat*', '*equipment*', '*spell*']
    ),
    
    'flying_speed': EnhancedFieldMapping(
        api_path='character.speed.flying',
        display_name='Flying Speed',
        priority=ChangePriority.MEDIUM,
        category=ChangeCategory.BASIC_INFO,
        change_types=[EnhancedChangeType.MOVEMENT_SPEED_CHANGED],
        causation_patterns=['*race*', '*feat*', '*equipment*', '*spell*']
    ),
    
    'swimming_speed': EnhancedFieldMapping(
        api_path='character.speed.swimming',
        display_name='Swimming Speed',
        priority=ChangePriority.LOW,
        category=ChangeCategory.BASIC_INFO,
        change_types=[EnhancedChangeType.MOVEMENT_SPEED_CHANGED],
        causation_patterns=['*race*', '*feat*', '*equipment*', '*spell*']
    ),
    
    'climbing_speed': EnhancedFieldMapping(
        api_path='character.speed.climbing',
        display_name='Climbing Speed',
        priority=ChangePriority.LOW,
        category=ChangeCategory.BASIC_INFO,
        change_types=[EnhancedChangeType.MOVEMENT_SPEED_CHANGED],
        causation_patterns=['*race*', '*feat*', '*equipment*', '*spell*']
    )
}


def get_field_mapping(field_path: str) -> Optional[EnhancedFieldMapping]:
    """Get the field mapping for a given field path."""
    for mapping_key, mapping in ENHANCED_FIELD_MAPPINGS.items():
        if mapping.matches_path(field_path):
            return mapping
    return None


def get_mappings_by_category(category: ChangeCategory) -> List[EnhancedFieldMapping]:
    """Get all field mappings for a specific category."""
    return [mapping for mapping in ENHANCED_FIELD_MAPPINGS.values() if mapping.category == category]


def get_mappings_by_priority(priority: ChangePriority) -> List[EnhancedFieldMapping]:
    """Get all field mappings for a specific priority level."""
    return [mapping for mapping in ENHANCED_FIELD_MAPPINGS.values() if mapping.priority == priority]


def get_causation_patterns_for_field(field_path: str) -> List[str]:
    """Get causation patterns for a specific field path."""
    mapping = get_field_mapping(field_path)
    return mapping.causation_patterns if mapping else []


def is_change_type_enabled(change_type: str, config: ChangeDetectionConfig) -> bool:
    """Check if a specific change type is enabled in the configuration."""
    return change_type in config.enabled_change_types


def get_priority_for_field(field_path: str, config: ChangeDetectionConfig) -> ChangePriority:
    """Get the priority for a field, considering configuration overrides."""
    # Check for explicit override
    if field_path in config.priority_overrides:
        return config.priority_overrides[field_path]
    
    # Use field mapping default
    mapping = get_field_mapping(field_path)
    return mapping.priority if mapping else ChangePriority.MEDIUM


def validate_enhanced_config(config: ChangeDetectionConfig) -> List[str]:
    """Validate enhanced change detection configuration."""
    errors = []
    
    # Validate enabled change types
    valid_change_types = {
        'level', 'feats', 'subclass', 'spells', 'inventory', 'background', 
        'max_hp', 'proficiencies', 'ability_scores', 'race_species',
        'multiclass', 'personality', 'spellcasting_stats', 'initiative',
        'passive_skills', 'alignment', 'size', 'movement_speed'
    }
    
    invalid_types = config.enabled_change_types - valid_change_types
    if invalid_types:
        errors.append(f"Invalid change types: {invalid_types}")
    
    # Validate storage directory
    try:
        config.change_log_storage_dir.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        errors.append(f"Cannot create storage directory: {e}")
    
    # Validate numeric settings
    if config.change_log_rotation_size_mb <= 0:
        errors.append("change_log_rotation_size_mb must be positive")
    
    if config.change_log_retention_days <= 0:
        errors.append("change_log_retention_days must be positive")
    
    if not 0.0 <= config.causation_confidence_threshold <= 1.0:
        errors.append("causation_confidence_threshold must be between 0.0 and 1.0")
    
    if config.max_cascade_depth < 0:
        errors.append("max_cascade_depth must be non-negative")
    
    return errors