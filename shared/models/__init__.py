"""
Shared Data Models

Core data models and structures used across multiple modules.
"""

from .base import ExtensibleModel
from .change_detection import (
    ChangeType,
    ChangePriority, 
    ChangeCategory,
    FieldChange,
    DetectionContext,
    ChangeDetectionResult
)
from .character import (
    AbilityScores,
    CharacterClass,
    Species,
    Background,
    HitPoints,
    ArmorClass,
    Spellcasting,
    Skill,
    InventoryItem,
    Container
)

__all__ = [
    'ExtensibleModel',
    'ChangeType',
    'ChangePriority',
    'ChangeCategory', 
    'FieldChange',
    'DetectionContext',
    'ChangeDetectionResult',
    'AbilityScores',
    'CharacterClass',
    'Species',
    'Background', 
    'HitPoints',
    'ArmorClass',
    'Spellcasting',
    'Skill',
    'InventoryItem',
    'Container'
]