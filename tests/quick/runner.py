"""
Quick Test Runner for D&D Character Scraper

Provides fast, focused testing capabilities for development workflows.
"""

from pathlib import Path
from typing import Dict, Any, Optional
import pytest
from colorama import Fore, Style

from .config import QuickTestConfig
from .utils import TestResultFormatter, DirectoryValidator, TimingDecorator

class QuickTestRunner:
    """Fast test runner for development workflows."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        self.base_dir = base_dir or Path(__file__).parent
        self.config = QuickTestConfig()
        self.formatter = TestResultFormatter()
        self.validator = DirectoryValidator(self.base_dir)
    
    @TimingDecorator
    def run_category(self, category: str, specific_test: Optional[str] = None) -> Dict[str, Any]:
        """Run tests in a specific category."""
        if category not in self.config.TEST_CATEGORIES:
            raise ValueError(f"Unknown category: {category}. Available: {list(self.config.TEST_CATEGORIES.keys())}")
        
        test_dir = self.base_dir / self.config.TEST_CATEGORIES[category]
        if not test_dir.exists():
            return {'status': 'error', 'message': f"Test directory {test_dir} does not exist"}
        
        # Build pytest arguments
        pytest_args = self._build_pytest_args(test_dir, specific_test)
        
        print(f"{Fore.CYAN}Running {category} tests{Style.RESET_ALL}")
        
        # Run pytest
        result = pytest.main(pytest_args)
        
        return {
            'status': 'success' if result == 0 else 'failure',
            'exit_code': result,
            'category': category,
            'specific_test': specific_test
        }
    
    def _build_pytest_args(self, test_dir: Path, specific_test: Optional[str] = None) -> list:
        """Build pytest arguments for test execution."""
        args = [str(test_dir)]
        args.extend(self.config.PYTEST_ARGS)
        
        if specific_test:
            args.extend(['-k', specific_test])
        
        # Add quick test markers
        marker_expr = ' or '.join(self.config.QUICK_MARKERS)
        args.extend(['-m', marker_expr])
        
        return args
    
    def run_calculator_test(self, calculator_name: str) -> Dict[str, Any]:
        """Run tests for a specific calculator."""
        if calculator_name not in self.config.AVAILABLE_CALCULATORS:
            return {
                'status': 'error',
                'message': f"Unknown calculator: {calculator_name}. Available: {self.config.AVAILABLE_CALCULATORS}"
            }
        return self.run_category('isolated', f'test_calculators and {calculator_name}')
    
    def run_smoke_tests(self) -> Dict[str, Any]:
        """Run smoke tests for basic functionality validation."""
        return self.run_category('smoke', None)
    
    def run_scenario_test(self, scenario_name: str) -> Dict[str, Any]:
        """Run tests for a specific scenario."""
        if scenario_name not in self.config.AVAILABLE_SCENARIOS:
            return {
                'status': 'error',
                'message': f"Unknown scenario: {scenario_name}. Available: {self.config.AVAILABLE_SCENARIOS}"
            }
        return self.run_category('scenarios', scenario_name)
    
    def run_all_quick_tests(self) -> Dict[str, Any]:
        """Run all quick tests."""
        return self.run_category('all', None)
    
    def print_results(self, results: Dict[str, Any]):
        """Print formatted test results."""
        self.formatter.print_results(results)
    
    def validate_setup(self) -> bool:
        """Validate that the quick test setup is correct."""
        validation_results = self.validator.validate_structure(self.config.REQUIRED_DIRS)
        self.validator.print_validation_results(validation_results)
        return validation_results['valid']