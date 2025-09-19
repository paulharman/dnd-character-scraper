"""
High-level scraper service that coordinates character data processing.

This service provides a clean interface for scraping character data
using the modular v6.0.0 architecture.
"""

import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional

from ..clients.factory import ClientFactory
from ..calculators.character_calculator import CharacterCalculator
from ..rules.version_manager import RuleVersionManager, RuleVersion
from ..config.manager import ConfigManager

logger = logging.getLogger(__name__)


class ScraperService:
    """
    High-level service for character data scraping and processing.
    
    Coordinates between client, calculator, and rule management components.
    """
    
    def __init__(self, 
                 config_manager: Optional[ConfigManager] = None,
                 rule_manager: Optional[RuleVersionManager] = None):
        """
        Initialize the scraper service.
        
        Args:
            config_manager: Configuration manager instance
            rule_manager: Rule version manager instance
        """
        self.config_manager = config_manager
        self.rule_manager = rule_manager or RuleVersionManager()
        
        # Initialize calculator with dependencies
        self.calculator = CharacterCalculator(
            config_manager=self.config_manager,
            rule_manager=self.rule_manager
        )
        
        # Client will be created per-request
        self.client = None
        
    def set_rule_override(self, rule_version: RuleVersion):
        """Set a rule version override."""
        self.rule_manager.set_force_version(rule_version)
        
    def scrape_character(self, 
                        character_id: str, 
                        session_cookie: Optional[str] = None) -> Dict[str, Any]:
        """
        Scrape and process character data.
        
        Args:
            character_id: D&D Beyond character ID
            session_cookie: Optional session cookie for private characters
            
        Returns:
            Complete processed character data
            
        Raises:
            Exception: If scraping or processing fails
        """
        logger.info(f"Starting character scrape for ID: {character_id}")
        
        # Create client for this request
        self.client = ClientFactory.create_client(
            client_type='real',
            config_manager=self.config_manager,
            session_cookie=session_cookie
        )
        
        try:
            # Fetch raw data
            logger.info(f"Fetching character data for ID: {character_id}")
            raw_data = self.client.get_character(int(character_id))
            logger.info("Character data fetched successfully")
            
            # Process with calculator
            logger.info("Processing character data with v6.0.0 architecture")
            complete_data = self.calculator.calculate_complete_json(raw_data)
            
            # Add metadata
            complete_data.update({
                'scraper_version': '6.0.0',
                'api_version': 'v5',
                'character_url': f"https://ddb.ac/characters/{character_id}",
                'generated_timestamp': time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime()),
            })
            
            # Log rule detection summary
            rule_detection = self.rule_manager.detect_rule_version(raw_data, int(character_id))
            detection_summary = self.rule_manager.get_detection_summary(rule_detection)
            
            logger.info("Rule Version Detection:")
            for line in detection_summary.split('\n'):
                if line.strip():
                    logger.info(f"  {line}")
            
            logger.info(f"Successfully processed character {character_id}")
            return complete_data
            
        except Exception as e:
            logger.error(f"Failed to scrape character {character_id}: {e}")
            raise
            
    def save_to_file(self, character_data: Dict[str, Any], output_path: Optional[str] = None) -> str:
        """
        Save character data to JSON file.
        
        Args:
            character_data: Complete character data
            output_path: Optional output filename
            
        Returns:
            Path to saved file
        """
        # Determine output filename
        if not output_path:
            character_name = character_data.get('name', 'Unknown_Character')
            character_id = character_data.get('character_id', 'unknown')
            # Sanitize filename
            safe_name = "".join(c for c in character_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            safe_name = safe_name.replace(' ', '_')
            output_path = f"{safe_name}_{character_id}.json"
        
        # Save to file
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(character_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Character data saved to: {output_file.absolute()}")
        return str(output_file.absolute())
        
    def save_raw_data(self, raw_data: Dict[str, Any], output_path: str) -> str:
        """
        Save raw API response to file for debugging.
        
        Args:
            raw_data: Raw API response data
            output_path: Output filename
            
        Returns:
            Path to saved file
        """
        output_file = Path(output_path)
        with open(output_file, 'w', encoding='utf-8') as f:
            import json
            json.dump(raw_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Raw API data saved to: {output_file.absolute()}")
        return str(output_file.absolute())