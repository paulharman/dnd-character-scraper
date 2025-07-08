"""
Command-line argument parser for quick tests.
"""

import argparse
from .config import QuickTestConfig

class QuickTestArgumentParser:
    """Handles command-line argument parsing for quick tests."""
    
    def __init__(self):
        self.config = QuickTestConfig()
    
    def create_parser(self) -> argparse.ArgumentParser:
        """Create the argument parser for quick tests."""
        parser = argparse.ArgumentParser(
            description='Quick Test Runner for D&D Character Scraper',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=self._get_examples()
        )
        
        self._add_category_arguments(parser)
        self._add_specific_test_arguments(parser)
        self._add_utility_arguments(parser)
        
        return parser
    
    def _add_category_arguments(self, parser: argparse.ArgumentParser):
        """Add test category arguments."""
        parser.add_argument('--smoke', action='store_true',
                           help='Run smoke tests for basic functionality')
        parser.add_argument('--isolated', action='store_true',
                           help='Run isolated component tests')
        parser.add_argument('--scenarios', action='store_true',
                           help='Run scenario tests')
    
    def _add_specific_test_arguments(self, parser: argparse.ArgumentParser):
        """Add specific test arguments."""
        parser.add_argument('--calculator', type=str,
                           choices=self.config.AVAILABLE_CALCULATORS,
                           help='Test specific calculator')
        parser.add_argument('--scenario', type=str,
                           choices=self.config.AVAILABLE_SCENARIOS,
                           help='Test specific scenario')
        parser.add_argument('--test', type=str,
                           help='Run specific test by name')
    
    def _add_utility_arguments(self, parser: argparse.ArgumentParser):
        """Add utility arguments."""
        parser.add_argument('--validate', action='store_true',
                           help='Validate quick test setup')
        parser.add_argument('--list', action='store_true',
                           help='List available test categories and options')
    
    def _get_examples(self) -> str:
        """Get example usage string."""
        return """
Examples:
  python -m tests.quick                    # Run all quick tests
  python -m tests.quick --smoke            # Run smoke tests only
  python -m tests.quick --calculator AC    # Test specific calculator
  python -m tests.quick --scenario wizard  # Test specific scenario
  python -m tests.quick --isolated         # Run isolated component tests
  python -m tests.quick --validate         # Validate test setup
        """