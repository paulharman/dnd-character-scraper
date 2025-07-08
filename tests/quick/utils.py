"""
Utility functions for quick tests.
"""

import time
from pathlib import Path
from typing import Dict, Any, Optional, List
from colorama import init, Fore, Style

init(autoreset=True)

class TestResultFormatter:
    """Formats and displays test results."""
    
    @staticmethod
    def format_execution_time(seconds: float) -> str:
        """Format execution time with appropriate units."""
        if seconds < 1.0:
            return f"{seconds*1000:.0f}ms"
        return f"{seconds:.2f}s"
    
    @staticmethod
    def get_status_color(status: str) -> str:
        """Get color for test status."""
        colors = {
            'success': Fore.GREEN,
            'failure': Fore.RED,
            'error': Fore.YELLOW,
            'warning': Fore.YELLOW
        }
        return colors.get(status, Fore.WHITE)
    
    @staticmethod
    def print_header(title: str):
        """Print formatted header."""
        print(f"\n{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{title.center(60)}{Style.RESET_ALL}")
        print(f"{Fore.CYAN}{'='*60}{Style.RESET_ALL}")
    
    @staticmethod
    def print_results(results: Dict[str, Any]):
        """Print formatted test results."""
        status_color = TestResultFormatter.get_status_color(results['status'])
        
        print(f"\n{status_color}{'='*50}{Style.RESET_ALL}")
        print(f"{status_color}Test Results: {results['status'].upper()}{Style.RESET_ALL}")
        print(f"Category: {results.get('category', 'unknown')}")
        
        if results.get('specific_test'):
            print(f"Specific Test: {results['specific_test']}")
        
        execution_time = TestResultFormatter.format_execution_time(
            results.get('execution_time', 0)
        )
        print(f"Execution Time: {execution_time}")
        print(f"Exit Code: {results.get('exit_code', 'unknown')}")
        
        if results.get('message'):
            print(f"Message: {results['message']}")
        
        print(f"{status_color}{'='*50}{Style.RESET_ALL}")

class DirectoryValidator:
    """Validates test directory structure."""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
    
    def validate_structure(self, required_dirs: List[str]) -> Dict[str, Any]:
        """Validate that required directories exist."""
        missing_dirs = []
        existing_dirs = []
        
        for dir_name in required_dirs:
            dir_path = self.base_dir / dir_name
            if dir_path.exists():
                existing_dirs.append(dir_name)
            else:
                missing_dirs.append(dir_name)
        
        return {
            'valid': len(missing_dirs) == 0,
            'missing_dirs': missing_dirs,
            'existing_dirs': existing_dirs
        }
    
    def print_validation_results(self, validation_results: Dict[str, Any]):
        """Print validation results."""
        if validation_results['valid']:
            print(f"{Fore.GREEN}✓ Quick test setup validated successfully!{Style.RESET_ALL}")
        else:
            print(f"{Fore.YELLOW}⚠ Warning: Missing directories: {validation_results['missing_dirs']}{Style.RESET_ALL}")
            print(f"{Fore.YELLOW}Some quick test features may not be available.{Style.RESET_ALL}")

class TimingDecorator:
    """Decorator for timing test execution."""
    
    def __init__(self, func):
        self.func = func
        self.execution_time = 0
    
    def __call__(self, *args, **kwargs):
        start_time = time.time()
        result = self.func(*args, **kwargs)
        self.execution_time = time.time() - start_time
        
        # Add timing to result if it's a dict
        if isinstance(result, dict):
            result['execution_time'] = self.execution_time
        
        return result