"""
Services package for high-level character processing operations.

This package contains services that coordinate between different components:
- Character scraping service
- Character processing coordination
- High-level business logic

Note: Discord services are now in the discord/ package
"""

from .scraper_service import ScraperService

__all__ = [
    'ScraperService'
]