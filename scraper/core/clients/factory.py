"""
Client factory for creating appropriate character clients.
"""

from typing import Optional
import logging

from scraper.core.interfaces.character_client import CharacterClientInterface
from shared.config.manager import get_config_manager
from .dndbeyond_client import DNDBeyondClient
from .mock_client import MockDNDBeyondClient, StaticMockClient

logger = logging.getLogger(__name__)


class ClientFactory:
    """Factory for creating character clients based on configuration."""
    
    @staticmethod
    def create_client(
        client_type: Optional[str] = None,
        config_manager=None,
        **kwargs
    ) -> CharacterClientInterface:
        """
        Create a character client based on configuration or explicit type.
        
        Args:
            client_type: Override client type ("real", "mock", "static")
            config_manager: Optional config manager instance
            **kwargs: Additional arguments passed to client constructor
            
        Returns:
            Configured character client
        """
        if config_manager is None:
            config_manager = get_config_manager()
        
        config = config_manager.get_app_config()
        
        # Determine client type
        if client_type is None:
            # Use configuration to determine client type
            if hasattr(config, 'testing') and config.testing.use_mock_clients:
                client_type = "mock"
            else:
                client_type = "real"
        
        # Create appropriate client
        if client_type == "real":
            logger.info("Creating real D&D Beyond API client")
            return DNDBeyondClient(**kwargs)
            
        elif client_type == "mock":
            logger.info("Creating mock D&D Beyond client")
            return MockDNDBeyondClient(**kwargs)
            
        elif client_type == "static":
            logger.info("Creating static mock client")
            return StaticMockClient(**kwargs)
            
        else:
            raise ValueError(f"Unknown client type: {client_type}")
    
    @staticmethod
    def create_for_environment(environment: str = None, **kwargs) -> CharacterClientInterface:
        """
        Create client appropriate for the given environment.
        
        Args:
            environment: Environment name ("development", "testing", "production")
            **kwargs: Additional arguments passed to client constructor
            
        Returns:
            Configured character client
        """
        config_manager = get_config_manager(environment=environment)
        config = config_manager.get_app_config()
        
        # Environment-specific logic
        if environment == "testing":
            # Use mock client for testing
            return ClientFactory.create_client("mock", config_manager, **kwargs)
        elif environment == "development":
            # Allow override for development
            return ClientFactory.create_client(None, config_manager, **kwargs)
        else:
            # Production uses real client
            return ClientFactory.create_client("real", config_manager, **kwargs)