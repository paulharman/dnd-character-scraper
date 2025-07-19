"""
Parser core module for interfaces and base classes.

This module provides the core interfaces and abstractions used throughout
the character parser system.
"""

from .interfaces import (
    IFormatter,
    ITemplateManager, 
    ITextProcessor,
    IValidationService,
    IPerformanceMonitor
)

__all__ = [
    'IFormatter',
    'ITemplateManager',
    'ITextProcessor', 
    'IValidationService',
    'IPerformanceMonitor'
]