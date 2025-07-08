"""
Encumbrance Calculator

Calculates character encumbrance based on inventory weight and carrying capacity.
Follows D&D 5e encumbrance rules.
"""

from typing import Dict, Any, Optional, List
import logging

from .base import RuleAwareCalculator

logger = logging.getLogger(__name__)


class EncumbranceCalculator(RuleAwareCalculator):
    """
    Calculator for character encumbrance and carrying capacity.
    
    Calculates total weight carried and encumbrance level based on
    Strength score and D&D 5e encumbrance rules.
    """
    
    def calculate(self, raw_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate character encumbrance from raw D&D Beyond data.
        
        Args:
            raw_data: Raw character data from D&D Beyond API
            **kwargs: Additional parameters:
                - ability_scores: Pre-calculated ability scores (optional)
                
        Returns:
            Dictionary containing:
                - total_weight: Total weight carried in pounds
                - carrying_capacity: Maximum carrying capacity (STR × 15)
                - encumbered_threshold: Weight at which character is encumbered (STR × 5)
                - heavily_encumbered_threshold: Weight at which character is heavily encumbered (STR × 10)
                - encumbrance_level: Current encumbrance level (0=unencumbered, 1=encumbered, 2=heavily encumbered)
                - speed_reduction: Speed reduction due to encumbrance
        """
        character_id = raw_data.get('id', 'unknown')
        logger.debug(f"Calculating encumbrance for character {character_id}")
        
        # Get ability scores - either from kwargs or calculate
        ability_scores = kwargs.get('ability_scores', {})
        if ability_scores:
            # Use pre-calculated ability scores
            strength_data = ability_scores.get('strength', {})
            if isinstance(strength_data, dict):
                strength_score = strength_data.get('score', 10)
            else:
                strength_score = strength_data if isinstance(strength_data, int) else 10
        else:
            # Extract Strength score directly from raw data
            stats = raw_data.get('stats', [])
            strength_score = 10  # Default
            for stat in stats:
                if stat.get('id') == 1:  # Strength ID is 1
                    strength_score = stat.get('value', 10)
                    break
            
            # Apply any overrides
            override_stats = raw_data.get('overrideStats', [])
            for stat in override_stats:
                if stat.get('id') == 1 and stat.get('value') is not None:
                    strength_score = stat['value']
                    break
        
        # Calculate carrying capacity thresholds
        carrying_capacity = strength_score * 15
        encumbered_threshold = strength_score * 5
        heavily_encumbered_threshold = strength_score * 10
        
        # Calculate total weight carried
        total_weight = self._calculate_total_weight(raw_data)
        
        # Determine encumbrance level
        if total_weight <= encumbered_threshold:
            encumbrance_level = 0  # Unencumbered
            speed_reduction = 0
        elif total_weight <= heavily_encumbered_threshold:
            encumbrance_level = 1  # Encumbered
            speed_reduction = 10  # -10 ft to speed
        elif total_weight <= carrying_capacity:
            encumbrance_level = 2  # Heavily encumbered
            speed_reduction = 20  # -20 ft to speed
        else:
            # Over capacity - cannot move (house rule territory)
            encumbrance_level = 3  # Over capacity
            speed_reduction = 999  # Effectively immobile
        
        result = {
            'total_weight': round(total_weight, 2),
            'carrying_capacity': carrying_capacity,
            'encumbered_threshold': encumbered_threshold,
            'heavily_encumbered_threshold': heavily_encumbered_threshold,
            'encumbrance_level': encumbrance_level,
            'speed_reduction': speed_reduction,
            'strength_score': strength_score
        }
        
        logger.debug(f"Character {character_id} encumbrance: {result}")
        
        return result
    
    def _calculate_total_weight(self, raw_data: Dict[str, Any]) -> float:
        """
        Calculate total weight of all inventory items with container organization.
        
        Args:
            raw_data: Raw character data
            
        Returns:
            Total weight in pounds
        """
        inventory = raw_data.get('inventory', [])
        total_weight = 0.0
        weight_by_container = {}
        
        # Organize items by container for detailed weight tracking
        for item in inventory:
            # Get item definition
            definition = item.get('definition', {})
            
            # Get base weight
            base_weight = definition.get('weight', 0.0) or 0.0
            
            # Apply weight multiplier if any
            weight_multiplier = definition.get('weightMultiplier', 1) or 1
            
            # Get quantity
            quantity = item.get('quantity', 1)
            
            # Calculate total weight for this item stack
            item_weight = base_weight * weight_multiplier * quantity
            total_weight += item_weight
            
            # Track weight by container for detailed breakdown
            container_id = item.get('containerEntityId', 'character')
            if container_id not in weight_by_container:
                weight_by_container[container_id] = {
                    'items': [],
                    'total_weight': 0.0,
                    'container_name': 'Character' if container_id == 'character' else definition.get('name', f'Container {container_id}')
                }
            
            item_info = {
                'name': definition.get('name', 'Unknown'),
                'weight': base_weight,
                'quantity': quantity,
                'total_weight': item_weight,
                'is_container': definition.get('isContainer', False),
                'capacity_weight': definition.get('capacityWeight', 0.0) or 0.0
            }
            weight_by_container[container_id]['items'].append(item_info)
            weight_by_container[container_id]['total_weight'] += item_weight
            
            logger.debug(f"Item: {definition.get('name', 'Unknown')} - "
                        f"Weight: {base_weight} × {weight_multiplier} × {quantity} = {item_weight} "
                        f"(Container: {container_id})")
        
        # Log container breakdown
        for container_id, container_data in weight_by_container.items():
            logger.debug(f"Container '{container_data['container_name']}': "
                        f"{container_data['total_weight']} lbs from {len(container_data['items'])} items")
        
        # Also check for carried currency weight (optional rule)
        # Standard rule: 50 coins = 1 pound
        if raw_data.get('currencies'):
            currencies = raw_data['currencies']
            total_coins = (
                currencies.get('cp', 0) +
                currencies.get('sp', 0) +
                currencies.get('ep', 0) +
                currencies.get('gp', 0) +
                currencies.get('pp', 0)
            )
            coin_weight = total_coins / 50.0
            total_weight += coin_weight
            
            if coin_weight > 0:
                logger.debug(f"Coins: {total_coins} coins = {coin_weight} lbs")
        
        return total_weight
    
    def get_encumbrance_description(self, encumbrance_level: int) -> str:
        """
        Get human-readable description of encumbrance level.
        
        Args:
            encumbrance_level: Numeric encumbrance level (0-3)
            
        Returns:
            Description string
        """
        descriptions = {
            0: "Unencumbered",
            1: "Encumbered (-10 ft speed)",
            2: "Heavily Encumbered (-20 ft speed, disadvantage on ability checks, attack rolls, and saving throws that use Strength, Dexterity, or Constitution)",
            3: "Over Capacity (cannot move)"
        }
        return descriptions.get(encumbrance_level, "Unknown")