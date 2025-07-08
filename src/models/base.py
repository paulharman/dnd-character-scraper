"""
Base data models with extensibility support.
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field, ConfigDict


class ExtensibleModel(BaseModel):
    """
    Base model that allows unknown fields for extensibility.
    
    This enables the scraper to handle new D&D Beyond fields without breaking,
    and preserves unknown content for future analysis.
    """
    
    # Allow unknown fields to be preserved
    model_config = ConfigDict(
        extra="allow",  # This preserves unknown fields
        validate_assignment=True,
        use_enum_values=True
    )
    
    # Storage for any additional fields not explicitly defined
    additional_data: Dict[str, Any] = Field(default_factory=dict, exclude=True)
    
    def __init__(self, **data):
        # Extract known fields for validation
        known_fields = set(self.model_fields.keys())
        known_data = {k: v for k, v in data.items() if k in known_fields}
        unknown_data = {k: v for k, v in data.items() if k not in known_fields}
        
        # Initialize with known fields
        super().__init__(**known_data)
        
        # Store unknown fields separately
        if unknown_data:
            self.additional_data = unknown_data
    
    def get_unknown_fields(self) -> Dict[str, Any]:
        """Get any fields that weren't part of the original model definition."""
        return self.additional_data.copy()
    
    def has_unknown_fields(self) -> bool:
        """Check if this instance has any unknown fields."""
        return bool(self.additional_data)
    
    def to_dict_with_unknown(self) -> Dict[str, Any]:
        """Convert to dictionary including unknown fields."""
        result = self.model_dump()
        result.update(self.additional_data)
        return result


class SourcedValue(BaseModel):
    """
    A value with information about its source.
    
    Useful for tracking where modifiers, bonuses, and other values come from.
    """
    value: Any
    source: str
    source_type: Optional[str] = None  # e.g., "race", "class", "feat", "item"
    source_id: Optional[int] = None
    description: Optional[str] = None
    
    model_config = ConfigDict(extra="allow")


class Modifier(ExtensibleModel):
    """
    Represents a character modifier with source information.
    """
    id: Optional[str] = None
    entity_id: Optional[int] = None
    entity_type_id: Optional[int] = None
    type: Optional[str] = None
    subtype: Optional[str] = None
    dice: Optional[Dict[str, Any]] = None
    bonus: Optional[int] = None
    value: Optional[Any] = None
    available_to_multiclass: Optional[bool] = None
    modifies_id: Optional[int] = None
    modifies_type_id: Optional[int] = None
    component_id: Optional[int] = None
    component_type_id: Optional[int] = None
    
    # Source information
    source: Optional[str] = None
    source_definition: Optional[Dict[str, Any]] = None
    
    # Conditional logic
    condition: Optional[str] = None
    requires_attunement: Optional[bool] = None
    
    def get_effective_value(self) -> Any:
        """Get the effective value of this modifier."""
        if self.value is not None:
            return self.value
        elif self.bonus is not None:
            return self.bonus
        elif self.dice:
            # For dice modifiers, return a representation
            return self.dice
        else:
            return None
    
    def applies_to(self, target_id: int, target_type_id: Optional[int] = None) -> bool:
        """Check if this modifier applies to a specific target."""
        if self.modifies_id and self.modifies_id != target_id:
            return False
        if target_type_id and self.modifies_type_id and self.modifies_type_id != target_type_id:
            return False
        return True