"""
Data Transformation Utilities for Enhanced Calculators

This module provides utilities to transform raw D&D Beyond API data 
into the structured format expected by enhanced calculators.
"""

import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)


class EnhancedCalculatorDataTransformer:
    """
    Transforms raw D&D Beyond API data into the structured format
    expected by enhanced calculators.
    """
    
    def __init__(self):
        """Initialize the data transformer."""
        self.logger = logger
        
    def transform_for_enhanced_calculators(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw D&D Beyond API data into enhanced calculator format.
        
        Args:
            raw_data: Raw character data from D&D Beyond API
            
        Returns:
            Structured data compatible with enhanced calculators
        """
        try:
            transformed = {}
            
            # Transform basic info
            transformed["basic_info"] = self._transform_basic_info(raw_data)
            
            # Transform ability scores
            transformed["ability_scores"] = self._transform_ability_scores(raw_data)
            
            # Transform hit points
            transformed["hit_points"] = self._transform_hit_points(raw_data)
            
            # Transform armor class (calculate basic value)
            transformed["armor_class"] = self._estimate_armor_class(raw_data)
            
            # Transform speed
            transformed["speed"] = self._transform_speed(raw_data)
            
            # Pass through other relevant data
            transformed["inventory"] = raw_data.get("inventory", [])
            transformed["equipment"] = raw_data.get("inventory", [])  # Enhanced calculators may expect this key
            transformed["modifiers"] = raw_data.get("modifiers", [])
            transformed["classes"] = raw_data.get("classes", [])
            transformed["feats"] = raw_data.get("feats", [])
            transformed["race"] = raw_data.get("race", {})
            
            # Preserve original stats format for enhanced calculators that still expect it
            transformed["stats"] = raw_data.get("stats", [])
            
            # Add raw data reference for fallback
            transformed["_raw_data"] = raw_data
            
            self.logger.debug(f"Transformed data keys: {list(transformed.keys())}")
            return transformed
            
        except Exception as e:
            self.logger.error(f"Error transforming data for enhanced calculators: {e}")
            # Return raw data with minimal structure as fallback
            return {
                "basic_info": {"name": raw_data.get("name", "Unknown"), "level": 1},
                "ability_scores": {"strength": 10, "dexterity": 10, "constitution": 10, 
                                 "intelligence": 10, "wisdom": 10, "charisma": 10},
                "hit_points": {"current": 1, "maximum": 1},
                "armor_class": 10,
                "speed": 30,
                "_raw_data": raw_data,
                "_transformation_error": str(e)
            }
    
    def _transform_basic_info(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Transform basic character information."""
        # Calculate total level from classes
        classes = raw_data.get("classes", [])
        total_level = sum(cls.get("level", 0) for cls in classes if isinstance(cls, dict))
        total_level = max(1, total_level)  # Minimum level 1
        
        return {
            "name": raw_data.get("name", "Unknown Character"),
            "level": total_level
        }
    
    def _transform_ability_scores(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Transform ability scores from D&D Beyond format."""
        ability_scores = {
            "strength": 10,
            "dexterity": 10, 
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10
        }
        
        # D&D Beyond API uses stats array with id mapping
        stats = raw_data.get("stats", [])
        if isinstance(stats, list):
            # Map ability IDs to names
            ability_map = {
                1: "strength",
                2: "dexterity", 
                3: "constitution",
                4: "intelligence",
                5: "wisdom",
                6: "charisma"
            }
            
            for stat in stats:
                if isinstance(stat, dict) and "id" in stat and "value" in stat:
                    ability_id = stat["id"]
                    if ability_id in ability_map:
                        ability_name = ability_map[ability_id]
                        ability_scores[ability_name] = stat["value"]
        
        self.logger.debug(f"Transformed ability scores: {ability_scores}")
        return ability_scores
    
    def _transform_hit_points(self, raw_data: Dict[str, Any]) -> Dict[str, int]:
        """Transform hit points information."""
        # D&D Beyond uses overrideHitPoints or baseHitPoints + bonusHitPoints
        max_hp = raw_data.get("overrideHitPoints")
        if max_hp is None:
            base_hp = raw_data.get("baseHitPoints", 0) or 0
            bonus_hp = raw_data.get("bonusHitPoints", 0) or 0
            max_hp = base_hp + bonus_hp
        
        # Handle case where max_hp could still be None
        if max_hp is None:
            max_hp = 0
        
        # Current HP calculation
        current_hp = max_hp - (raw_data.get("removedHitPoints", 0) or 0)
        temp_hp = raw_data.get("temporaryHitPoints", 0) or 0
        
        return {
            "current": max(0, current_hp + temp_hp),
            "maximum": max(1, max_hp)
        }
    
    def _estimate_armor_class(self, raw_data: Dict[str, Any]) -> int:
        """Estimate armor class for validation purposes."""
        # This is a rough estimate - the enhanced calculator will do the real calculation
        # We just need a reasonable value for validation
        
        # Start with base AC 10
        estimated_ac = 10
        
        # Add dex modifier (estimated)
        stats = raw_data.get("stats", [])
        dex_value = 10
        for stat in stats:
            if isinstance(stat, dict) and stat.get("id") == 2:
                dex_value = stat.get("value", 10)
                break
        
        dex_mod = (dex_value - 10) // 2
        
        # Check if wearing armor
        inventory = raw_data.get("inventory", [])
        has_armor = False
        for item in inventory:
            if isinstance(item, dict) and item.get("equipped", False):
                definition = item.get("definition", {})
                if definition.get("armorTypeId") is not None:
                    has_armor = True
                    # Rough AC estimate for validation
                    estimated_ac = max(estimated_ac, 12)  # Assume at least leather armor
                    break
        
        if not has_armor:
            estimated_ac += dex_mod  # Unarmored gets full dex
        else:
            estimated_ac += min(dex_mod, 2)  # Assume medium armor dex cap
        
        return max(1, estimated_ac)
    
    def _transform_speed(self, raw_data: Dict[str, Any]) -> int:
        """Transform speed information."""
        # Check race speed
        race = raw_data.get("race", {})
        if isinstance(race, dict):
            race_speed = race.get("weightSpeeds", {}).get("normal", {}).get("walk")
            if race_speed is not None:
                return race_speed
        
        # Default to 30 feet
        return 30