"""
D&D Beyond API client implementation.
"""

import asyncio
import random
import time
from typing import Dict, Any, Optional
import logging

import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from scraper.core.interfaces.character_client import CharacterClientInterface
from shared.config.settings import Settings
from .exceptions import (
    CharacterNotFoundError, PrivateCharacterError, APIError, 
    ValidationError, RateLimitError, TimeoutError
)

logger = logging.getLogger(__name__)


class DNDBeyondClient(CharacterClientInterface):
    """
    D&D Beyond API client with robust error handling and rate limiting.
    """
    
    def __init__(self, user_agent: Optional[str] = None):
        self.settings = Settings()
        if user_agent:
            self.settings.user_agent = user_agent
        
        # Create session with retry strategy
        self.session = requests.Session()
        self._setup_session()
        
        # Rate limiting
        self.last_request_time = 0
        self.min_delay = self.settings.min_request_delay
        
        logger.info(f"DNDBeyond client initialized with base URL: {self.settings.api_base_url}")
    
    def _setup_session(self):
        """Configure session with retry strategy and headers."""
        # Configure retry strategy
        retry_strategy = Retry(
            total=self.settings.api_retries,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"],  # newer urllib3 uses allowed_methods
            backoff_factor=1.0
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # Set default headers
        self.session.headers.update({
            'User-Agent': self.settings.user_agent,
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9'
        })
    
    def _apply_rate_limiting(self):
        """Apply rate limiting between requests."""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_delay:
            sleep_time = self.min_delay - time_since_last
            # Add small random jitter
            jitter = random.uniform(
                self.settings.jitter_min, 
                self.settings.jitter_max
            )
            sleep_time += jitter
            
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    async def fetch_character_data(self, character_id: int) -> Dict[str, Any]:
        """
        Fetch character data from D&D Beyond API.
        
        Args:
            character_id: The character ID to fetch
            
        Returns:
            Raw character data dictionary
            
        Raises:
            CharacterNotFoundError: Character doesn't exist
            PrivateCharacterError: Character is private
            APIError: API returned an error
            ValidationError: Character data is invalid
            TimeoutError: Request timed out
        """
        logger.info(f"Fetching character data for ID: {character_id}")
        
        # Apply rate limiting
        self._apply_rate_limiting()
        
        # Prepare request
        url = f"{self.settings.api_base_url.rstrip('/')}/{character_id}?includeCustomItems=true"
        headers = {}
        
        try:
            # Make request
            logger.debug(f"Making request to: {url}")
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.settings.api_timeout
            )
            
            # Handle response
            if response.status_code == 200:
                wrapper_data = response.json()
                
                # Extract character data from wrapper
                if isinstance(wrapper_data, dict) and 'data' in wrapper_data:
                    data = wrapper_data['data']
                    logger.debug("Extracted character data from API wrapper")
                else:
                    data = wrapper_data
                    logger.debug("Using response data directly (no wrapper detected)")
                
                # Validate data
                if not self.validate_character_data(data):
                    raise ValidationError(f"Character {character_id} data failed validation")
                
                logger.info(f"Successfully fetched character {character_id}")
                return data
                
            elif response.status_code == 404:
                raise CharacterNotFoundError(character_id)
                
            elif response.status_code == 403:
                raise PrivateCharacterError(character_id)
                
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(retry_after)
                
            else:
                raise APIError(response.status_code, response.text)
                
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.settings.api_timeout} seconds")
            
        except requests.exceptions.RequestException as e:
            raise APIError(0, f"Request failed: {str(e)}")
    
    def get_character(self, character_id: int) -> Dict[str, Any]:
        """
        Fetch character data from D&D Beyond API (synchronous).
        
        Args:
            character_id: The character ID to fetch
            
        Returns:
            Raw character data dictionary
            
        Raises:
            CharacterNotFoundError: Character doesn't exist
            PrivateCharacterError: Character is private
            APIError: API returned an error
            ValidationError: Character data is invalid
            TimeoutError: Request timed out
        """
        logger.info(f"Fetching character data for ID: {character_id}")
        
        # Apply rate limiting
        self._apply_rate_limiting()
        
        # Prepare request
        url = f"{self.settings.api_base_url.rstrip('/')}/{character_id}?includeCustomItems=true"
        headers = {}
        
        try:
            # Make request
            logger.debug(f"Making request to: {url}")
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.settings.api_timeout
            )
            
            # Handle response
            if response.status_code == 200:
                wrapper_data = response.json()
                
                # Extract character data from wrapper
                if isinstance(wrapper_data, dict) and 'data' in wrapper_data:
                    data = wrapper_data['data']
                    logger.debug("Extracted character data from API wrapper")
                else:
                    data = wrapper_data
                    logger.debug("Using response data directly (no wrapper detected)")
                
                # Validate data
                if not self.validate_character_data(data):
                    raise ValidationError(f"Character {character_id} data failed validation")
                
                logger.info(f"Successfully fetched character {character_id}")
                return data
                
            elif response.status_code == 404:
                raise CharacterNotFoundError(character_id)
                
            elif response.status_code == 403:
                raise PrivateCharacterError(character_id)
                
            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(retry_after)
                
            else:
                raise APIError(response.status_code, response.text)
                
        except requests.exceptions.Timeout:
            raise TimeoutError(f"Request timed out after {self.settings.api_timeout} seconds")
            
        except requests.exceptions.RequestException as e:
            raise APIError(0, f"Request failed: {str(e)}")

    def get_party_inventory(self, campaign_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch party inventory data from D&D Beyond API.

        Args:
            campaign_id: The campaign ID to fetch party inventory for

        Returns:
            Party inventory data dictionary or None if not available

        Raises:
            APIError: API returned an error
            TimeoutError: Request timed out
        """
        if not campaign_id:
            logger.debug("No campaign ID provided, skipping party inventory")
            return None

        logger.info(f"Fetching party inventory for campaign ID: {campaign_id}")

        # Apply rate limiting
        self._apply_rate_limiting()

        # Prepare request
        url = f"https://character-service.dndbeyond.com/character/v5/party/inventory/{campaign_id}"
        headers = {}

        try:
            # Make request
            logger.debug(f"Making request to: {url}")
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.settings.api_timeout
            )

            # Handle response
            if response.status_code == 200:
                wrapper_data = response.json()

                # Extract party inventory data from wrapper
                if isinstance(wrapper_data, dict) and 'data' in wrapper_data:
                    data = wrapper_data['data']
                    logger.debug("Extracted party inventory data from API wrapper")
                    logger.info(f"Successfully fetched party inventory for campaign {campaign_id}")
                    return data
                else:
                    logger.warning("Party inventory response missing data wrapper")
                    return None

            elif response.status_code == 404:
                logger.info(f"No party inventory found for campaign {campaign_id}")
                return None

            elif response.status_code == 403:
                logger.warning(f"Access denied to party inventory for campaign {campaign_id}")
                return None

            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(retry_after)

            else:
                logger.warning(f"Party inventory API returned {response.status_code}: {response.text[:200]}")
                return None

        except requests.exceptions.Timeout:
            raise TimeoutError(f"Party inventory request timed out after {self.settings.api_timeout} seconds")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Party inventory request failed: {str(e)}")
            return None

    def get_character_infusions(self, character_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch character infusion data from D&D Beyond API.

        Args:
            character_id: The character ID to fetch infusions for

        Returns:
            Infusion data dictionary or None if not available

        Raises:
            APIError: API returned an error
            TimeoutError: Request timed out
        """
        logger.info(f"Fetching infusions for character ID: {character_id}")

        # Apply rate limiting
        self._apply_rate_limiting()

        # Prepare request
        url = f"https://character-service.dndbeyond.com/character/v5/infusion/items/{character_id}"
        headers = {}

        try:
            # Make request
            logger.debug(f"Making request to: {url}")
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.settings.api_timeout
            )

            # Handle response
            if response.status_code == 200:
                wrapper_data = response.json()

                # Extract infusion data from wrapper
                if isinstance(wrapper_data, dict) and 'data' in wrapper_data:
                    data = wrapper_data['data']
                    logger.debug("Extracted infusion data from API wrapper")
                    logger.info(f"Successfully fetched infusions for character {character_id}")
                    return data
                else:
                    logger.warning("Infusion response missing data wrapper")
                    return None

            elif response.status_code == 404:
                logger.info(f"No infusions found for character {character_id}")
                return None

            elif response.status_code == 403:
                logger.warning(f"Access denied to infusions for character {character_id}")
                return None

            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(retry_after)

            else:
                logger.warning(f"Infusion API returned {response.status_code}: {response.text[:200]}")
                return None

        except requests.exceptions.Timeout:
            raise TimeoutError(f"Infusion request timed out after {self.settings.api_timeout} seconds")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Infusion request failed: {str(e)}")
            return None

    def get_known_infusions(self, character_id: int) -> Optional[Dict[str, Any]]:
        """
        Fetch known infusions for character from D&D Beyond API.

        Args:
            character_id: The character ID to fetch known infusions for

        Returns:
            Known infusions data dictionary or None if not available

        Raises:
            APIError: API returned an error
            TimeoutError: Request timed out
        """
        logger.info(f"Fetching known infusions for character ID: {character_id}")

        # Apply rate limiting
        self._apply_rate_limiting()

        # Prepare request
        url = f"https://character-service.dndbeyond.com/character/v5/known-infusions/{character_id}"
        headers = {}

        try:
            # Make request
            logger.debug(f"Making request to: {url}")
            response = self.session.get(
                url,
                headers=headers,
                timeout=self.settings.api_timeout
            )

            # Handle response
            if response.status_code == 200:
                wrapper_data = response.json()

                # Extract known infusions data from wrapper
                if isinstance(wrapper_data, dict) and 'data' in wrapper_data:
                    data = wrapper_data['data']
                    logger.debug("Extracted known infusions data from API wrapper")
                    logger.info(f"Successfully fetched known infusions for character {character_id}")
                    return data
                else:
                    logger.warning("Known infusions response missing data wrapper")
                    return None

            elif response.status_code == 404:
                logger.info(f"No known infusions found for character {character_id}")
                return None

            elif response.status_code == 403:
                logger.warning(f"Access denied to known infusions for character {character_id}")
                return None

            elif response.status_code == 429:
                retry_after = int(response.headers.get('Retry-After', 60))
                raise RateLimitError(retry_after)

            else:
                logger.warning(f"Known infusions API returned {response.status_code}: {response.text[:200]}")
                return None

        except requests.exceptions.Timeout:
            raise TimeoutError(f"Known infusions request timed out after {self.settings.api_timeout} seconds")

        except requests.exceptions.RequestException as e:
            logger.warning(f"Known infusions request failed: {str(e)}")
            return None

    def validate_character_data(self, data: Dict[str, Any]) -> bool:
        """
        Validate that character data contains required fields.
        
        Args:
            data: Raw character data dictionary
            
        Returns:
            True if data is valid, False otherwise
        """
        if not isinstance(data, dict):
            logger.error("Character data is not a dictionary")
            return False
        
        # Required top-level fields
        required_fields = ['id', 'name', 'classes']
        
        for field in required_fields:
            if field not in data:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate character has at least one class
        if not data.get('classes') or len(data['classes']) == 0:
            logger.error("Character has no classes")
            return False
        
        # Validate character ID is correct
        if not isinstance(data.get('id'), int) or data['id'] <= 0:
            logger.error(f"Invalid character ID: {data.get('id')}")
            return False
        
        logger.debug("Character data validation passed")
        return True
    
    def get_character_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract basic character summary from raw data.
        
        Args:
            data: Raw character data dictionary
            
        Returns:
            Dictionary with basic character info
        """
        try:
            # Calculate total level from classes directly
            classes = data.get('classes', [])
            total_level = sum(cls.get('level', 0) for cls in classes)
            
            # Get primary class
            primary_class = None
            if classes:
                # Find highest level class
                primary_class = max(classes, key=lambda c: c.get('level', 0))
            
            # Get species/race
            race = data.get('race', {})
            species = data.get('species', {})
            race_name = (race.get('fullName') or race.get('baseName') or 
                        species.get('fullName') or species.get('baseName') or 'Unknown')
            
            summary = {
                'id': data.get('id'),
                'name': data.get('name', 'Unknown'),
                'level': total_level,
                'race': race_name,
                'classes': [
                    {
                        'name': cls.get('definition', {}).get('name', 'Unknown'),
                        'level': cls.get('level', 0),
                        'subclass': cls.get('subclassDefinition', {}).get('name')
                    }
                    for cls in classes
                ],
                'primary_class': primary_class.get('definition', {}).get('name') if primary_class else None,
                'is_multiclass': len(classes) > 1
            }
            
            logger.debug(f"Generated summary for character: {summary['name']} (Level {summary['level']} {summary['primary_class']})")
            return summary
            
        except Exception as e:
            logger.error(f"Error generating character summary: {str(e)}")
            return {
                'id': data.get('id'),
                'name': data.get('name', 'Unknown'),
                'error': f"Failed to generate summary: {str(e)}"
            }
    
    def close(self):
        """Close the session."""
        if self.session:
            self.session.close()
            logger.debug("Client session closed")
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()