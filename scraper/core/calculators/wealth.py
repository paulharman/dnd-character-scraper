"""
Wealth Calculator

Calculates character wealth from D&D Beyond API data.
Handles currency extraction and total wealth calculation.
"""

from typing import Dict, Any, Optional
import logging

from .base import RuleAwareCalculator

logger = logging.getLogger(__name__)


class WealthCalculator(RuleAwareCalculator):
    """
    Calculator for character wealth and currency.
    
    Extracts currency values from D&D Beyond API data and calculates
    total wealth in gold pieces for easy comparison.
    """
    
    # Currency conversion rates to gold pieces
    CURRENCY_TO_GP = {
        'pp': 10.0,   # 1 platinum = 10 gold
        'gp': 1.0,    # 1 gold = 1 gold
        'ep': 0.5,    # 1 electrum = 0.5 gold
        'sp': 0.1,    # 1 silver = 0.1 gold
        'cp': 0.01    # 1 copper = 0.01 gold
    }
    
    def calculate(self, raw_data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        Calculate character wealth from raw D&D Beyond data.
        
        Args:
            raw_data: Raw character data from D&D Beyond API
            **kwargs: Additional parameters (unused)
            
        Returns:
            Dictionary containing:
                - copper: Number of copper pieces
                - silver: Number of silver pieces
                - electrum: Number of electrum pieces
                - gold: Number of gold pieces
                - platinum: Number of platinum pieces
                - total_gp: Total wealth converted to gold pieces
        """
        character_id = raw_data.get('id', 'unknown')
        logger.debug(f"Calculating wealth for character {character_id}")
        
        # Extract currencies from raw data
        currencies = raw_data.get('currencies', {})
        
        # Build wealth dictionary with defaults
        wealth = {
            'copper': currencies.get('cp', 0),
            'silver': currencies.get('sp', 0),
            'electrum': currencies.get('ep', 0),
            'gold': currencies.get('gp', 0),
            'platinum': currencies.get('pp', 0)
        }
        
        # Calculate total wealth in gold pieces
        total_gp = 0.0
        for currency_code, conversion_rate in self.CURRENCY_TO_GP.items():
            amount = currencies.get(currency_code, 0)
            total_gp += amount * conversion_rate
        
        wealth['total_gp'] = round(total_gp, 2)
        
        logger.debug(f"Character {character_id} wealth: {wealth}")
        
        return wealth
    
    def _extract_starting_equipment_value(self, raw_data: Dict[str, Any]) -> float:
        """
        Extract value of starting equipment from background/class.
        
        This is a placeholder for potential future enhancement to calculate
        the monetary value of starting equipment.
        
        Args:
            raw_data: Raw character data
            
        Returns:
            Estimated value in gold pieces
        """
        # TODO: Could analyze starting equipment from background/class
        # and estimate their market value
        return 0.0