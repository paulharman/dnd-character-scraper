#!/usr/bin/env python3
"""
Comprehensive Test Runner

Runs all tests in the test suite with detailed reporting and coverage analysis.
"""

import sys
import os
import unittest
import time
import json
from io import StringIO
from contextlib import redirect_stdout, redirect_stderr

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)


class ColoredTextTestResult(unittest.TextTestResult):
    """Enhanced test result with colored output and detailed reporting."""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.test_results = []
        self.start_time = None
        self.verbosity = verbosity
        
        # ANSI color codes
        self.colors = {
            'green': '\033[92m',
            'red': '\033[91m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'reset': '\033[0m',
            'bold': '\033[1m'
        }
    
    def startTest(self, test):
        super().startTest(test)
        self.start_time = time.time()
        if self.verbosity > 1:
            self.stream.write(f"{self.colors['blue']}Running: {test._testMethodName}{self.colors['reset']} ... ")
            self.stream.flush()
    
    def addSuccess(self, test):
        super().addSuccess(test)
        duration = time.time() - self.start_time
        self.test_results.append({
            'test': str(test),
            'status': 'PASS',
            'duration': duration,
            'error': None
        })
        if self.verbosity > 1:
            self.stream.write(f"{self.colors['green']}PASS{self.colors['reset']} ({duration:.3f}s)\n")
    
    def addError(self, test, err):
        super().addError(test, err)
        duration = time.time() - self.start_time
        self.test_results.append({
            'test': str(test),
            'status': 'ERROR',
            'duration': duration,
            'error': self._exc_info_to_string(err, test)
        })
        if self.verbosity > 1:
            self.stream.write(f"{self.colors['red']}ERROR{self.colors['reset']} ({duration:.3f}s)\n")
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        duration = time.time() - self.start_time
        self.test_results.append({
            'test': str(test),
            'status': 'FAIL',
            'duration': duration,
            'error': self._exc_info_to_string(err, test)
        })
        if self.verbosity > 1:
            self.stream.write(f"{self.colors['red']}FAIL{self.colors['reset']} ({duration:.3f}s)\n")
    
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        duration = time.time() - self.start_time
        self.test_results.append({
            'test': str(test),
            'status': 'SKIP',
            'duration': duration,
            'error': reason
        })
        if self.verbosity > 1:
            self.stream.write(f"{self.colors['yellow']}SKIP{self.colors['reset']} ({duration:.3f}s) - {reason}\n")


class ComprehensiveTestRunner:
    """Comprehensive test runner with detailed reporting."""
    
    def __init__(self, verbosity=2):
        self.verbosity = verbosity
        self.test_suites = {
            'Unit Tests': [
                'tests.unit.rules.test_version_manager',
                'tests.unit.calculators.test_armor_class',
                'tests.unit.calculators.test_ability_scores',
                'tests.unit.calculators.test_hit_points',
                'tests.unit.calculators.test_spellcasting',
                'tests.unit.calculators.test_proficiency',
                'tests.unit.calculators.test_coordinators'
            ],
            'Calculator Tests': [
                'tests.calculators.test_enhanced_spell_processor',
                'tests.calculators.test_enhanced_weapon_attacks',
                'tests.calculators.test_equipment_integration',
                'tests.calculators.test_magic_item_integration',
                'tests.calculators.test_skill_bonus_calculator',
                'tests.calculators.test_class_resource_calculator',
                'tests.calculators.test_damage_calculator'
            ],
            'Integration Tests': [
                'tests.integration.test_character_processing',
                'tests.integration.test_character_validation',
                'tests.integration.test_fresh_data_comparison',
                'tests.integration.test_parser_refactor_comparison'
            ],
            'Edge Case Tests': [
                'tests.edge_cases.test_multiclass_scenarios',
                'tests.edge_cases.test_extreme_stats',
                'tests.edge_cases.test_unknown_content'
            ]
        }
        
        self.colors = {
            'green': '\033[92m',
            'red': '\033[91m',
            'yellow': '\033[93m',
            'blue': '\033[94m',
            'purple': '\033[95m',
            'cyan': '\033[96m',
            'reset': '\033[0m',
            'bold': '\033[1m'
        }
    
    def print_header(self):
        """Print test runner header."""
        print(f"\n{self.colors['bold']}{self.colors['cyan']}{'='*80}")
        print("D&D Beyond Character Scraper - Comprehensive Test Suite")
        print(f"{'='*80}{self.colors['reset']}\n")
    
    def print_section_header(self, section_name):
        """Print section header."""
        print(f"\n{self.colors['bold']}{self.colors['purple']}")
        print(f"{'─'*80}")
        print(f" {section_name}")
        print(f"{'─'*80}")
        print(f"{self.colors['reset']}")
    
    def run_test_suite(self, suite_name, test_modules):
        """Run a specific test suite."""
        self.print_section_header(suite_name)
        
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Load tests from modules
        loaded_modules = 0
        for module_name in test_modules:
            try:
                module_suite = loader.loadTestsFromName(module_name)
                suite.addTest(module_suite)
                loaded_modules += 1
                print(f"{self.colors['green']}✓{self.colors['reset']} Loaded {module_name}")
            except Exception as e:
                print(f"{self.colors['red']}✗{self.colors['reset']} Failed to load {module_name}: {e}")
        
        if loaded_modules == 0:
            print(f"{self.colors['yellow']}⚠{self.colors['reset']} No tests loaded for {suite_name}")
            return unittest.TestResult(), 0
        
        print(f"\n{self.colors['blue']}Running {suite.countTestCases()} tests...{self.colors['reset']}\n")
        
        # Run tests with custom result class
        runner = unittest.TextTestRunner(
            stream=sys.stdout,
            verbosity=self.verbosity,
            resultclass=ColoredTextTestResult
        )
        
        result = runner.run(suite)
        return result, suite.countTestCases()
    
    def print_summary(self, all_results, total_tests):
        """Print comprehensive test summary."""
        total_passed = sum(r.testsRun - len(r.failures) - len(r.errors) - len(r.skipped) for r in all_results)
        total_failed = sum(len(r.failures) for r in all_results)
        total_errors = sum(len(r.errors) for r in all_results)
        total_skipped = sum(len(r.skipped) for r in all_results)
        
        print(f"\n{self.colors['bold']}{self.colors['cyan']}")
        print(f"{'='*80}")
        print(" TEST SUMMARY")
        print(f"{'='*80}")
        print(f"{self.colors['reset']}")
        
        print(f"Total Tests: {total_tests}")
        print(f"{self.colors['green']}✓ Passed: {total_passed}{self.colors['reset']}")
        if total_failed > 0:
            print(f"{self.colors['red']}✗ Failed: {total_failed}{self.colors['reset']}")
        if total_errors > 0:
            print(f"{self.colors['red']}💥 Errors: {total_errors}{self.colors['reset']}")
        if total_skipped > 0:
            print(f"{self.colors['yellow']}⚠ Skipped: {total_skipped}{self.colors['reset']}")
        
        # Calculate success rate
        if total_tests > 0:
            success_rate = (total_passed / total_tests) * 100
            print(f"\nSuccess Rate: {success_rate:.1f}%")
            
            if success_rate >= 95:
                print(f"{self.colors['green']}🎉 Excellent! Test suite is in great shape.{self.colors['reset']}")
            elif success_rate >= 80:
                print(f"{self.colors['yellow']}⚠ Good, but some issues need attention.{self.colors['reset']}")
            else:
                print(f"{self.colors['red']}❌ Test suite needs significant work.{self.colors['reset']}")
        
        # Print failure details
        if total_failed > 0 or total_errors > 0:
            print(f"\n{self.colors['red']}{self.colors['bold']}FAILURE DETAILS:{self.colors['reset']}")
            for result in all_results:
                for test, traceback in result.failures + result.errors:
                    print(f"\n{self.colors['red']}✗ {test}{self.colors['reset']}")
                    print(f"  {traceback.split(chr(10))[0]}")  # First line of error
    
    def save_results_json(self, all_results, output_file='test_results.json'):
        """Save test results to JSON file."""
        results_data = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'summary': {
                'total_tests': sum(r.testsRun for r in all_results),
                'passed': sum(r.testsRun - len(r.failures) - len(r.errors) - len(r.skipped) for r in all_results),
                'failed': sum(len(r.failures) for r in all_results),
                'errors': sum(len(r.errors) for r in all_results),
                'skipped': sum(len(r.skipped) for r in all_results)
            },
            'suites': {}
        }
        
        for i, (suite_name, result) in enumerate(zip(self.test_suites.keys(), all_results)):
            results_data['suites'][suite_name] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped),
                'details': getattr(result, 'test_results', [])
            }
        
        try:
            with open(output_file, 'w') as f:
                json.dump(results_data, f, indent=2)
            print(f"\n{self.colors['blue']}📊 Detailed results saved to {output_file}{self.colors['reset']}")
        except Exception as e:
            print(f"\n{self.colors['yellow']}⚠ Could not save results: {e}{self.colors['reset']}")
    
    def run_all_tests(self):
        """Run all test suites."""
        start_time = time.time()
        self.print_header()
        
        all_results = []
        total_tests = 0
        
        # Run each test suite
        for suite_name, modules in self.test_suites.items():
            result, test_count = self.run_test_suite(suite_name, modules)
            all_results.append(result)
            total_tests += test_count
        
        end_time = time.time()
        
        # Print comprehensive summary
        self.print_summary(all_results, total_tests)
        
        print(f"\n{self.colors['blue']}⏱ Total execution time: {end_time - start_time:.2f} seconds{self.colors['reset']}")
        
        # Save results to JSON
        self.save_results_json(all_results)
        
        # Return exit code
        total_failures = sum(len(r.failures) + len(r.errors) for r in all_results)
        return 0 if total_failures == 0 else 1


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run comprehensive test suite')
    parser.add_argument('-v', '--verbosity', type=int, choices=[0, 1, 2], default=2,
                       help='Test output verbosity (0=quiet, 1=normal, 2=verbose)')
    parser.add_argument('--suite', choices=['unit', 'calculator', 'integration', 'edge', 'all'], default='all',
                       help='Run specific test suite')
    parser.add_argument('--output', default='test_results.json',
                       help='Output file for test results')
    
    args = parser.parse_args()
    
    runner = ComprehensiveTestRunner(verbosity=args.verbosity)
    
    if args.suite == 'all':
        exit_code = runner.run_all_tests()
    else:
        # Run specific suite
        suite_map = {
            'unit': 'Unit Tests',
            'calculator': 'Calculator Tests',
            'integration': 'Integration Tests',
            'edge': 'Edge Case Tests'
        }
        
        suite_name = suite_map[args.suite]
        modules = runner.test_suites[suite_name]
        
        runner.print_header()
        result, test_count = runner.run_test_suite(suite_name, modules)
        runner.print_summary([result], test_count)
        
        exit_code = 0 if len(result.failures) + len(result.errors) == 0 else 1
    
    return exit_code


if __name__ == '__main__':
    sys.exit(main())