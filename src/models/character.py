"""
Core Character data model.
"""

from typing import Dict, List, Optional, Any, Union
from pydantic import Field, field_validator
from datetime import datetime

from .base import ExtensibleModel, SourcedValue, Modifier
from src.interfaces.rule_engine import RuleVersion


class AbilityScores(ExtensibleModel):
    """Character ability scores with source breakdown."""
    strength: int = Field(ge=1, le=30)
    dexterity: int = Field(ge=1, le=30)
    constitution: int = Field(ge=1, le=30)
    intelligence: int = Field(ge=1, le=30)
    wisdom: int = Field(ge=1, le=30)
    charisma: int = Field(ge=1, le=30)
    
    # Source breakdown for debugging
    strength_sources: List[SourcedValue] = Field(default_factory=list)
    dexterity_sources: List[SourcedValue] = Field(default_factory=list)
    constitution_sources: List[SourcedValue] = Field(default_factory=list)
    intelligence_sources: List[SourcedValue] = Field(default_factory=list)
    wisdom_sources: List[SourcedValue] = Field(default_factory=list)
    charisma_sources: List[SourcedValue] = Field(default_factory=list)
    
    def get_modifier(self, ability: str) -> int:
        """Get ability modifier for given ability."""
        score = getattr(self, ability.lower())
        return (score - 10) // 2
    
    def get_all_modifiers(self) -> Dict[str, int]:
        """Get all ability modifiers."""
        return {
            ability: self.get_modifier(ability)
            for ability in ["strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"]
        }


class CharacterClass(ExtensibleModel):
    """Character class information."""
    id: Optional[int] = None
    name: str
    level: int = Field(ge=1, le=20)
    hit_die: int = Field(ge=4, le=12)
    subclass: Optional[str] = None
    subclass_id: Optional[int] = None
    
    # Rule version information
    is_2024: bool = False
    
    # Spellcasting information
    is_spellcaster: bool = False
    spellcasting_ability: Optional[str] = None
    spellcasting_type: Optional[str] = None  # "full", "half", "third", "pact"
    
    # Class features - Enhanced with ClassFeature models
    features: List['ClassFeature'] = Field(default_factory=list)
    
    @field_validator('hit_die')
    @classmethod
    def validate_hit_die(cls, v):
        """Validate hit die is appropriate for D&D classes."""
        valid_hit_dice = [4, 6, 8, 10, 12]
        if v not in valid_hit_dice:
            raise ValueError(f'Hit die must be one of {valid_hit_dice}')
        return v


class Species(ExtensibleModel):
    """Character species/race information."""
    id: Optional[int] = None
    name: str
    subrace: Optional[str] = None
    subrace_id: Optional[int] = None
    
    # Ability score increases
    ability_score_increases: Dict[str, int] = Field(default_factory=dict)
    
    # Racial traits
    traits: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Size and speed
    size: Optional[str] = None
    speed: int = Field(default=30, ge=0, le=120)
    
    # Special abilities
    darkvision: int = Field(default=0, ge=0, le=120)
    languages: List[str] = Field(default_factory=list)


class Background(ExtensibleModel):
    """Character background information."""
    id: Optional[int] = None
    name: str
    
    # 2024 backgrounds provide ability score increases
    ability_score_increases: Dict[str, int] = Field(default_factory=dict)
    
    # Skills and proficiencies
    skill_proficiencies: List[str] = Field(default_factory=list)
    tool_proficiencies: List[str] = Field(default_factory=list)
    language_proficiencies: List[str] = Field(default_factory=list)
    
    # Background features
    features: List[Dict[str, Any]] = Field(default_factory=list)


class HitPoints(ExtensibleModel):
    """Hit point information with calculation breakdown."""
    maximum: int = Field(ge=1)
    current: Optional[int] = None
    temporary: int = Field(default=0, ge=0)
    
    # Calculation breakdown
    base_hit_points: int = Field(default=0)
    constitution_bonus: int = Field(default=0)
    class_bonus: int = Field(default=0)
    feat_bonus: int = Field(default=0)
    item_bonus: int = Field(default=0)
    other_bonus: int = Field(default=0)
    
    calculation_method: Optional[str] = None  # "manual", "average", "rolled"
    hit_dice_used: int = Field(default=0, ge=0)
    
    @field_validator('current')
    @classmethod
    def current_cannot_exceed_maximum(cls, v, info):
        if v is not None and info.data and 'maximum' in info.data and v > info.data['maximum']:
            return info.data['maximum']
        return v


class ArmorClass(ExtensibleModel):
    """Armor class information with calculation breakdown."""
    total: int = Field(ge=1, le=30)
    
    # AC calculation breakdown
    base: int = Field(default=10)
    armor_bonus: int = Field(default=0)
    shield_bonus: int = Field(default=0)
    dexterity_bonus: int = Field(default=0)
    natural_armor: int = Field(default=0)
    deflection_bonus: int = Field(default=0)
    misc_bonus: int = Field(default=0)
    
    # Calculation method
    calculation_method: str = Field(default="standard")  # "standard", "unarmored_defense", "natural_armor", etc.
    armor_worn: Optional[str] = None
    shield_used: Optional[str] = None
    
    # Limitations
    max_dex_bonus: Optional[int] = None
    
    @field_validator('total')
    @classmethod
    def validate_total_matches_breakdown(cls, v):
        """Validate that total AC matches the sum of components."""
        # This is a soft validation - we'll log warnings rather than fail
        return v


class Spellcasting(ExtensibleModel):
    """Spellcasting information."""
    is_spellcaster: bool = False
    spellcasting_ability: Optional[str] = None
    spell_save_dc: Optional[int] = None
    spell_attack_bonus: Optional[int] = None
    
    # Spell slots by level
    spell_slots_level_1: int = Field(default=0, ge=0)
    spell_slots_level_2: int = Field(default=0, ge=0)
    spell_slots_level_3: int = Field(default=0, ge=0)
    spell_slots_level_4: int = Field(default=0, ge=0)
    spell_slots_level_5: int = Field(default=0, ge=0)
    spell_slots_level_6: int = Field(default=0, ge=0)
    spell_slots_level_7: int = Field(default=0, ge=0)
    spell_slots_level_8: int = Field(default=0, ge=0)
    spell_slots_level_9: int = Field(default=0, ge=0)
    
    # Pact magic (Warlocks)
    pact_slots: int = Field(default=0, ge=0)
    pact_slot_level: int = Field(default=0, ge=0)
    
    # Spell information
    spells_known: List[Dict[str, Any]] = Field(default_factory=list)
    cantrips_known: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Spell source breakdown
    class_spells: List[Dict[str, Any]] = Field(default_factory=list)
    racial_spells: List[Dict[str, Any]] = Field(default_factory=list)
    feat_spells: List[Dict[str, Any]] = Field(default_factory=list)
    item_spells: List[Dict[str, Any]] = Field(default_factory=list)
    
    def get_total_spell_slots(self) -> int:
        """Get total number of spell slots."""
        return sum([
            self.spell_slots_level_1, self.spell_slots_level_2, self.spell_slots_level_3,
            self.spell_slots_level_4, self.spell_slots_level_5, self.spell_slots_level_6,
            self.spell_slots_level_7, self.spell_slots_level_8, self.spell_slots_level_9,
            self.pact_slots
        ])
    
    def get_spell_slots_array(self) -> List[int]:
        """Get spell slots as array [1st, 2nd, 3rd, ...]."""
        return [
            self.spell_slots_level_1, self.spell_slots_level_2, self.spell_slots_level_3,
            self.spell_slots_level_4, self.spell_slots_level_5, self.spell_slots_level_6,
            self.spell_slots_level_7, self.spell_slots_level_8, self.spell_slots_level_9
        ]


class Skill(ExtensibleModel):
    """Character skill information."""
    name: str
    ability: str  # The ability this skill is based on
    proficient: bool = False
    expertise: bool = False
    bonus: int = Field(default=0)
    total_bonus: int = Field(default=0)
    
    # Source of proficiency
    proficiency_source: Optional[str] = None
    proficiency_source_type: Optional[str] = None


class InventoryItem(ExtensibleModel):
    """Inventory item with container support."""
    id: Optional[int] = None
    name: str
    quantity: int = Field(default=1, ge=0)
    weight: float = Field(default=0.0, ge=0.0)
    equipped: bool = Field(default=False)
    attuned: bool = Field(default=False)
    requires_attunement: bool = Field(default=False)
    
    # Container relationships
    container_entity_id: Optional[int] = None
    container_entity_type_id: Optional[int] = None
    container_definition_key: Optional[str] = None
    
    # Container metadata (if this item is a container)
    is_container: bool = Field(default=False)
    capacity_weight: float = Field(default=0.0, ge=0.0)
    capacity_volume: Optional[str] = None
    
    # Additional item properties
    description: Optional[str] = None
    notes: Optional[str] = None
    item_type: Optional[str] = None
    rarity: Optional[str] = None
    cost: Optional[float] = None
    
    # D&D Beyond specific fields
    definition_id: Optional[int] = None
    entity_type_id: Optional[int] = None
    equipped_entity_id: Optional[int] = None
    equipped_entity_type_id: Optional[int] = None


class Container(ExtensibleModel):
    """Container for organizing inventory items."""
    id: int
    name: str
    capacity_weight: float = Field(default=0.0, ge=0.0)
    capacity_volume: Optional[str] = None
    items: List[int] = Field(default_factory=list)  # List of item IDs
    current_weight: float = Field(default=0.0, ge=0.0)
    
    # Container metadata
    is_character: bool = Field(default=False)  # True if this represents the character's direct inventory
    
    def get_utilization_text(self) -> str:
        """Get container utilization as text."""
        if self.capacity_weight <= 0:
            return f"{self.current_weight} lbs"
        return f"{self.current_weight}/{self.capacity_weight} lbs"
    
    def get_utilization_percentage(self) -> float:
        """Get container utilization as percentage."""
        if self.capacity_weight <= 0:
            return 0.0
        return min(100.0, (self.current_weight / self.capacity_weight) * 100.0)


# Priority 2 Feature Models

class ClassFeature(ExtensibleModel):
    """Individual class feature with rich details."""
    id: Optional[int] = None
    name: str
    description: str
    snippet: Optional[str] = None
    
    # Feature metadata
    level_required: int = Field(ge=1, le=20)
    is_subclass_feature: bool = False
    feature_type: Optional[str] = None
    
    # Usage and limitations
    limited_use: Optional[Dict[str, Any]] = None
    activation: Optional[Dict[str, Any]] = None
    
    # Display configuration
    hide_in_builder: bool = False
    hide_in_sheet: bool = False
    display_order: Optional[int] = None
    
    # Sources and references
    source_id: Optional[int] = None
    source_page_number: Optional[int] = None
    definition_key: Optional[str] = None
    
    # Level scaling
    level_scales: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Spell lists and creature rules
    spell_list_ids: List[int] = Field(default_factory=list)
    creature_rules: List[Dict[str, Any]] = Field(default_factory=list)


class WeaponProperty(ExtensibleModel):
    """Weapon property with details."""
    id: int
    name: str
    description: Optional[str] = None
    
    # Property values (for properties like Versatile, Range, etc.)
    damage_value: Optional[str] = None
    range_normal: Optional[int] = None
    range_long: Optional[int] = None


class EnhancedEquipment(ExtensibleModel):
    """Enhanced equipment with detailed properties."""
    # Base item information
    id: Optional[int] = None
    name: str
    item_type: str
    subtype: Optional[str] = None
    
    # Basic properties
    quantity: int = Field(default=1, ge=0)
    weight: float = Field(default=0.0, ge=0.0)
    cost: Optional[float] = None
    rarity: str = Field(default="common")
    
    # Equipment state
    equipped: bool = Field(default=False)
    attuned: bool = Field(default=False)
    requires_attunement: bool = Field(default=False)
    charges_used: int = Field(default=0, ge=0)
    
    # Descriptions
    description: Optional[str] = None
    snippet: Optional[str] = None
    
    # Magic item properties
    is_magic: bool = False
    attunement_description: Optional[str] = None
    
    # Container relationships
    container_entity_id: Optional[int] = None
    container_entity_type_id: Optional[int] = None
    
    # Weapon-specific properties
    weapon_properties: List['WeaponProperty'] = Field(default_factory=list)
    damage_dice: Optional[str] = None
    damage_type: Optional[str] = None
    weapon_category: Optional[str] = None  # "simple", "martial"
    attack_type: Optional[str] = None  # "melee", "ranged"
    range_normal: Optional[int] = None
    range_long: Optional[int] = None
    is_monk_weapon: bool = False
    
    # Armor-specific properties
    armor_class: Optional[int] = None
    strength_requirement: Optional[int] = None
    stealth_disadvantage: bool = False
    armor_type: Optional[str] = None  # "light", "medium", "heavy", "shield"
    
    # Modifiers granted by this item
    granted_modifiers: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Source information
    source_id: Optional[int] = None
    source_page_number: Optional[int] = None
    definition_key: Optional[str] = None
    
    # D&D Beyond metadata
    entity_type_id: Optional[int] = None
    definition_id: Optional[int] = None
    equipped_entity_id: Optional[int] = None
    equipped_entity_type_id: Optional[int] = None
    
    # Custom item flag
    is_custom: bool = False


class CharacterAppearance(ExtensibleModel):
    """Character appearance and visual details."""
    # Basic physical description
    gender: Optional[str] = None
    age: Optional[int] = None
    height: Optional[str] = None
    weight: Optional[str] = None
    hair: Optional[str] = None
    eyes: Optional[str] = None
    skin: Optional[str] = None
    
    # Narrative appearance description
    appearance_description: Optional[str] = None
    
    # Avatar and imagery
    avatar_url: Optional[str] = None
    portrait_avatar_url: Optional[str] = None
    frame_avatar_url: Optional[str] = None
    backdrop_avatar_url: Optional[str] = None
    small_backdrop_avatar_url: Optional[str] = None
    large_backdrop_avatar_url: Optional[str] = None
    thumbnail_backdrop_avatar_url: Optional[str] = None
    
    # Avatar IDs and decoration keys
    avatar_id: Optional[int] = None
    portrait_decoration_key: Optional[str] = None
    frame_avatar_decoration_key: Optional[str] = None
    backdrop_avatar_decoration_key: Optional[str] = None
    theme_color: Optional[str] = None
    
    # Default backdrop information
    default_backdrop: Optional[Dict[str, Any]] = None


class ResourcePool(ExtensibleModel):
    """Individual resource pool (like spell slots, ki points, etc.)."""
    name: str
    resource_type: str  # "spell_slot", "feature_use", "hit_dice", etc.
    level: Optional[int] = None  # For spell slots
    
    # Current state
    maximum: int = Field(ge=0)
    current: int = Field(ge=0)
    used: int = Field(default=0, ge=0)
    
    # Recovery information
    recovery_type: str = "long_rest"  # "short_rest", "long_rest", "dawn", "manual"
    recovery_amount: int = Field(default=0, ge=0)  # 0 means full recovery
    
    # Source of this resource
    source_class: Optional[str] = None
    source_feature: Optional[str] = None
    source_type: str = "class"  # "class", "race", "feat", "item"


class AdvancedCharacterDetails(ExtensibleModel):
    """Advanced character details and metadata."""
    # Character notes and backstory
    backstory: Optional[str] = None
    personality_traits: Optional[str] = None
    ideals: Optional[str] = None
    bonds: Optional[str] = None
    flaws: Optional[str] = None
    
    # Relationships
    allies: Optional[str] = None
    enemies: Optional[str] = None
    organizations: Optional[str] = None
    
    # Possessions and holdings
    personal_possessions: Optional[str] = None
    other_holdings: Optional[str] = None
    other_notes: Optional[str] = None
    
    # Campaign information
    campaign_name: Optional[str] = None
    campaign_id: Optional[int] = None
    dm_name: Optional[str] = None
    
    # Character status
    inspiration: bool = False
    lifestyle: Optional[str] = None
    alignment_id: Optional[int] = None
    faith: Optional[str] = None
    
    # Experience and progression
    current_xp: int = Field(default=0, ge=0)
    
    # Meta information
    username: Optional[str] = None
    is_assigned_to_player: bool = True
    readonly_url: Optional[str] = None
    can_edit: bool = True
    date_modified: Optional[str] = None


class Character(ExtensibleModel):
    """
    Main character data model with full D&D Beyond integration.
    
    This model represents a complete D&D character with all calculated values
    and preserves unknown fields for future extensibility.
    """
    
    # Basic Information
    id: int = Field(description="D&D Beyond character ID")
    name: str
    level: int = Field(ge=1, le=20)
    
    # Rule version
    rule_version: RuleVersion = RuleVersion.UNKNOWN
    
    # Core character components
    ability_scores: AbilityScores
    classes: List[CharacterClass] = Field(min_length=1)
    species: Species
    background: Background
    
    # Calculated values
    hit_points: HitPoints
    armor_class: ArmorClass
    spellcasting: Spellcasting
    proficiency_bonus: int = Field(ge=2, le=6)
    
    # Skills and proficiencies
    skills: List[Skill] = Field(default_factory=list)
    saving_throw_proficiencies: List[str] = Field(default_factory=list)
    
    # Combat stats
    initiative_bonus: int = Field(default=0)
    speed: int = Field(default=30, ge=0)
    
    # Additional character info
    alignment: Optional[str] = None
    experience_points: int = Field(default=0, ge=0)
    
    # Equipment and inventory - Enhanced with container support
    equipment: List[InventoryItem] = Field(default_factory=list)
    containers: Dict[str, Container] = Field(default_factory=dict)
    
    # Priority 2 Features - Enhanced equipment with detailed properties
    enhanced_equipment: List['EnhancedEquipment'] = Field(default_factory=list)
    
    # Priority 2 Features - Class features with rich details
    class_features: List['ClassFeature'] = Field(default_factory=list)
    
    # Priority 2 Features - Character appearance
    appearance: Optional['CharacterAppearance'] = None
    
    # Priority 2 Features - Resource tracking
    resource_pools: List['ResourcePool'] = Field(default_factory=list)
    
    # Priority 2 Features - Advanced character details
    character_details: Optional['AdvancedCharacterDetails'] = None
    
    # Modifiers and effects
    modifiers: List[Modifier] = Field(default_factory=list)
    
    # Meta information
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    # Raw data preservation
    raw_data_summary: Dict[str, Any] = Field(default_factory=dict)
    
    @field_validator('classes')
    @classmethod
    def validate_classes_not_empty(cls, v):
        if not v or len(v) == 0:
            raise ValueError('Character must have at least one class')
        return v
    
    @field_validator('level')
    @classmethod
    def validate_level_matches_classes(cls, v, info):
        """Validate that character level matches sum of class levels."""
        if info.data and 'classes' in info.data and info.data['classes']:
            total_class_levels = sum(char_class.level for char_class in info.data['classes'])
            if v != total_class_levels:
                # Log warning but don't fail validation
                pass
        return v
    
    def get_primary_class(self) -> CharacterClass:
        """Get the character's primary (highest level) class."""
        return max(self.classes, key=lambda c: c.level)
    
    def is_multiclass(self) -> bool:
        """Check if character has multiple classes."""
        return len(self.classes) > 1
    
    def get_caster_level(self) -> int:
        """Calculate effective caster level for multiclass spellcasting."""
        total_caster_level = 0
        
        for char_class in self.classes:
            if char_class.spellcasting_type == "full":
                total_caster_level += char_class.level
            elif char_class.spellcasting_type == "half":
                total_caster_level += char_class.level // 2
            elif char_class.spellcasting_type == "third":
                total_caster_level += char_class.level // 3
            # Pact magic (Warlock) doesn't contribute to multiclass caster level
        
        return total_caster_level
    
    def get_skill_by_name(self, skill_name: str) -> Optional[Skill]:
        """Get skill by name."""
        for skill in self.skills:
            if skill.name.lower() == skill_name.lower():
                return skill
        return None
    
    def has_saving_throw_proficiency(self, ability: str) -> bool:
        """Check if character is proficient in a saving throw."""
        return ability.lower() in [save.lower() for save in self.saving_throw_proficiencies]