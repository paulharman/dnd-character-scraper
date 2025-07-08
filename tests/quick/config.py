"""
Configuration for quick tests.
"""

from typing import Dict, List
from pathlib import Path

class QuickTestConfig:
    """Configuration settings for quick tests."""
    
    # Test execution limits
    MAX_EXECUTION_TIME = 5.0  # seconds
    DEFAULT_TIMEOUT = 30.0    # seconds
    
    # Test categories and their directories
    TEST_CATEGORIES = {
        'smoke': 'smoke/',
        'isolated': 'isolated/',
        'scenarios': 'scenarios/',
        'all': '.'
    }
    
    # Required directory structure
    REQUIRED_DIRS = ['factories', 'isolated', 'smoke', 'scenarios']
    
    # Pytest configuration
    PYTEST_ARGS = [
        '-v',                    # verbose
        '--tb=short',           # short traceback
        '-x',                   # stop on first failure for quick tests
        '--disable-warnings',   # reduce noise
    ]
    
    # Test markers
    QUICK_MARKERS = ['quick', 'not slow']
    
    # Available calculators for testing
    AVAILABLE_CALCULATORS = [
        'AC', 'HP', 'spells', 'abilities', 'attacks', 'saves', 
        'skills', 'proficiency', 'containers', 'wealth'
    ]
    
    # Available scenarios for testing
    AVAILABLE_SCENARIOS = [
        'wizard', 'fighter', 'rogue', 'barbarian', 'cleric', 
        'multiclass', 'level1', 'level20', 'extreme'
    ]