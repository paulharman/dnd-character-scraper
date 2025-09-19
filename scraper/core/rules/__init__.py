"""
D&D Beyond Character Scraper - Rules Module

This module handles D&D 5e rule version detection and management,
supporting both 2014 and 2024 rule sets.

Key Components:
- RuleVersionManager: Centralized rule version detection
- GameConstants: Comprehensive D&D game data for both rule versions
- Rule-specific implementations for 2014 and 2024 differences
"""

from .version_manager import RuleVersionManager, RuleVersion
from .constants import GameConstants

__all__ = [
    'RuleVersionManager',
    'RuleVersion', 
    'GameConstants'
]