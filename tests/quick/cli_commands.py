"""
Command handlers for quick test CLI.
"""

from .runner import QuickTestRunner
from .config import QuickTestConfig

class QuickTestCommands:
    """Handles command execution for quick tests."""
    
    def __init__(self):
        self.runner = QuickTestRunner()
        self.config = QuickTestConfig()
    
    def list_available_options(self) -> int:
        """List available test categories and options."""
        print("Available Quick Test Options:")
        print("\nCategories:")
        print("  --smoke      : Basic functionality tests")
        print("  --isolated   : Component isolation tests")  
        print("  --scenarios  : Common character scenarios")
        
        print("\nSpecific Tests:")
        print(f"  --calculator : {', '.join(self.config.AVAILABLE_CALCULATORS)}")
        print(f"  --scenario   : {', '.join(self.config.AVAILABLE_SCENARIOS)}")
        print("  --test       : Specific test function name")
        
        print("\nUtilities:")
        print("  --validate   : Check test setup")
        print("  --list       : Show this help")
        
        return 0
    
    def validate_setup(self) -> int:
        """Validate quick test setup."""
        if self.runner.validate_setup():
            print("Quick test setup is valid!")
            return 0
        else:
            print("Quick test setup has issues.")
            return 1
    
    def run_smoke_tests(self) -> int:
        """Run smoke tests."""
        results = self.runner.run_smoke_tests()
        self.runner.print_results(results)
        return results['exit_code']
    
    def run_isolated_tests(self) -> int:
        """Run isolated component tests."""
        results = self.runner.run_category('isolated')
        self.runner.print_results(results)
        return results['exit_code']
    
    def run_scenario_tests(self) -> int:
        """Run scenario tests."""
        results = self.runner.run_category('scenarios')
        self.runner.print_results(results)
        return results['exit_code']
    
    def run_calculator_test(self, calculator_name: str) -> int:
        """Run tests for a specific calculator."""
        results = self.runner.run_calculator_test(calculator_name)
        self.runner.print_results(results)
        return results['exit_code']
    
    def run_scenario_test(self, scenario_name: str) -> int:
        """Run tests for a specific scenario."""
        results = self.runner.run_scenario_test(scenario_name)
        self.runner.print_results(results)
        return results['exit_code']
    
    def run_specific_test(self, test_name: str) -> int:
        """Run a specific test by name."""
        results = self.runner.run_category('all', test_name)
        self.runner.print_results(results)
        return results['exit_code']
    
    def run_all_quick_tests(self) -> int:
        """Run all quick tests."""
        results = self.runner.run_all_quick_tests()
        self.runner.print_results(results)
        return results['exit_code']