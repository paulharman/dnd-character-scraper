"""
Quick Testing Framework for D&D Character Scraper

This module provides fast, developer-friendly testing capabilities that complement
the comprehensive test suite. Quick tests are designed to execute in <5 seconds
and provide immediate feedback during development.

Usage:
    python -m tests.quick                    # Run all quick tests
    python -m tests.quick --smoke            # Run smoke tests only
    python -m tests.quick --calculator AC    # Test specific calculator
    python -m tests.quick --scenario wizard  # Test specific scenario
    python -m tests.quick --isolated         # Run isolated component tests
"""

from .runner import QuickTestRunner
from .cli import main

__version__ = "1.0.0"
__all__ = ["QuickTestRunner", "main"]