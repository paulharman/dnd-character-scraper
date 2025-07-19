"""
Discord Test Runner

Comprehensive test runner for all Discord-related functionality.
Provides different test modes and detailed reporting.
"""

import sys
import subprocess
import argparse
from pathlib import Path
import time
from typing import List, Dict, Any


class DiscordTestRunner:
    """Test runner for Discord functionality."""
    
    def __init__(self):
        self.test_root = Path(__file__).parent
        self.project_root = self.test_root.parent
        self.discord_root = self.project_root / "discord"
        
        # Test categories and their files
        self.test_categories = {
            'unit': [
                'tests/unit/services/test_discord_service.py',
                'tests/unit/services/test_change_detection_service.py',
                'tests/unit/services/test_notification_manager.py',
                'tests/unit/services/test_spell_detection_fixes.py',
                'tests/unit/services/test_change_detectors.py'
            ],
            'integration': [
                'tests/integration/test_discord_integration.py'
            ],
            'quick': [
                'tests/quick/test_discord.py'
            ]
        }
    
    def run_category(self, category: str, verbose: bool = False, stop_on_fail: bool = False) -> Dict[str, Any]:
        """Run tests for a specific category."""
        if category not in self.test_categories:
            return {'success': False, 'error': f'Unknown category: {category}'}
        
        test_files = self.test_categories[category]
        results = {
            'category': category,
            'files': [],
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'success': True,
            'duration': 0
        }
        
        start_time = time.time()
        
        for test_file in test_files:
            file_path = self.project_root / test_file
            if not file_path.exists():
                print(f"⚠️  Test file not found: {test_file}")
                continue
            
            print(f"Running {test_file}...")
            
            # Build pytest command
            cmd = [
                sys.executable, '-m', 'pytest',
                str(file_path),
                '-v' if verbose else '-q',
                '--tb=short'
            ]
            
            if stop_on_fail:
                cmd.append('-x')
            
            # Run the test
            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minute timeout
                )
                
                file_result = {
                    'file': test_file,
                    'exit_code': result.returncode,
                    'stdout': result.stdout,
                    'stderr': result.stderr,
                    'success': result.returncode == 0
                }
                
                # Parse test counts from output
                if 'passed' in result.stdout:
                    # Extract test counts from pytest output
                    lines = result.stdout.split('\n')
                    for line in lines:
                        if 'passed' in line and ('failed' in line or 'error' in line):
                            # Parse line like "5 failed, 10 passed in 2.3s"
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == 'passed':
                                    try:
                                        results['passed_tests'] += int(parts[i-1])
                                    except (ValueError, IndexError):
                                        pass
                                elif part == 'failed':
                                    try:
                                        results['failed_tests'] += int(parts[i-1])
                                    except (ValueError, IndexError):
                                        pass
                        elif 'passed in' in line:
                            # Parse line like "10 passed in 2.3s"
                            parts = line.split()
                            for i, part in enumerate(parts):
                                if part == 'passed':
                                    try:
                                        results['passed_tests'] += int(parts[i-1])
                                    except (ValueError, IndexError):
                                        pass
                
                results['files'].append(file_result)
                
                if result.returncode != 0:
                    results['success'] = False
                    print(f"❌ {test_file} failed")
                    if verbose:
                        print(f"STDOUT:\n{result.stdout}")
                        print(f"STDERR:\n{result.stderr}")
                else:
                    print(f"✅ {test_file} passed")
                
            except subprocess.TimeoutExpired:
                print(f"⏰ {test_file} timed out")
                results['success'] = False
                results['files'].append({
                    'file': test_file,
                    'exit_code': -1,
                    'stdout': '',
                    'stderr': 'Test timed out',
                    'success': False
                })
            except Exception as e:
                print(f"💥 Error running {test_file}: {e}")
                results['success'] = False
                results['files'].append({
                    'file': test_file,
                    'exit_code': -1,
                    'stdout': '',
                    'stderr': str(e),
                    'success': False
                })
        
        results['duration'] = time.time() - start_time
        results['total_tests'] = results['passed_tests'] + results['failed_tests']
        
        return results
    
    def run_all(self, verbose: bool = False, stop_on_fail: bool = False) -> Dict[str, Any]:
        """Run all Discord tests."""
        print("🎲 Running all Discord tests...\n")
        
        overall_results = {
            'categories': {},
            'total_duration': 0,
            'total_tests': 0,
            'total_passed': 0,
            'total_failed': 0,
            'success': True
        }
        
        start_time = time.time()
        
        for category in ['quick', 'unit', 'integration']:
            print(f"\n📂 Running {category} tests...")
            category_result = self.run_category(category, verbose, stop_on_fail)
            overall_results['categories'][category] = category_result
            
            overall_results['total_tests'] += category_result['total_tests']
            overall_results['total_passed'] += category_result['passed_tests']
            overall_results['total_failed'] += category_result['failed_tests']
            
            if not category_result['success']:
                overall_results['success'] = False
                if stop_on_fail:
                    print(f"🛑 Stopping due to failure in {category} tests")
                    break
        
        overall_results['total_duration'] = time.time() - start_time
        
        return overall_results
    
    def run_spell_detection_tests(self, verbose: bool = False) -> Dict[str, Any]:
        """Run only spell detection related tests."""
        print("🪄 Running spell detection tests...\n")
        
        spell_test_files = [
            'tests/unit/services/test_spell_detection_fixes.py',
            'tests/unit/services/test_change_detectors.py'
        ]
        
        results = {
            'files': [],
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'success': True,
            'duration': 0
        }
        
        start_time = time.time()
        
        for test_file in spell_test_files:
            file_path = self.project_root / test_file
            if not file_path.exists():
                print(f"⚠️  Test file not found: {test_file}")
                continue
            
            print(f"Running {test_file}...")
            
            cmd = [
                sys.executable, '-m', 'pytest',
                str(file_path),
                '-v' if verbose else '-q',
                '--tb=short',
                '-k', 'spell'  # Only run spell-related tests
            ]
            
            try:
                result = subprocess.run(
                    cmd,
                    cwd=str(self.project_root),
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                file_result = {
                    'file': test_file,
                    'exit_code': result.returncode,
                    'success': result.returncode == 0
                }
                
                results['files'].append(file_result)
                
                if result.returncode != 0:
                    results['success'] = False
                    print(f"❌ {test_file} spell tests failed")
                    if verbose:
                        print(f"STDOUT:\n{result.stdout}")
                else:
                    print(f"✅ {test_file} spell tests passed")
                
            except Exception as e:
                print(f"💥 Error running {test_file}: {e}")
                results['success'] = False
        
        results['duration'] = time.time() - start_time
        return results
    
    def print_summary(self, results: Dict[str, Any]):
        """Print test results summary."""
        print("\n" + "="*60)
        print("🎲 DISCORD TEST SUMMARY")
        print("="*60)
        
        if 'categories' in results:
            # Full test run summary
            for category, category_result in results['categories'].items():
                status = "✅ PASSED" if category_result['success'] else "❌ FAILED"
                duration = f"{category_result['duration']:.1f}s"
                test_count = f"{category_result['passed_tests']}/{category_result['total_tests']}"
                
                print(f"{category.upper():12} {status:10} {test_count:>8} tests in {duration}")
            
            print("-" * 60)
            total_status = "✅ PASSED" if results['success'] else "❌ FAILED"
            total_duration = f"{results['total_duration']:.1f}s"
            total_count = f"{results['total_passed']}/{results['total_tests']}"
            
            print(f"{'TOTAL':12} {total_status:10} {total_count:>8} tests in {total_duration}")
            
        else:
            # Single category or spell test summary
            status = "✅ PASSED" if results['success'] else "❌ FAILED"
            duration = f"{results['duration']:.1f}s"
            
            print(f"RESULT: {status} in {duration}")
        
        print("="*60)
        
        if not results['success']:
            print("\n💡 To see detailed failure information, run with --verbose")
            print("💡 To run only failing tests, check individual test files")
    
    def check_dependencies(self) -> bool:
        """Check if required dependencies are available."""
        print("🔍 Checking Discord test dependencies...")
        
        # Check if Discord module exists
        if not self.discord_root.exists():
            print(f"❌ Discord module not found at {self.discord_root}")
            return False
        
        # Check if pytest is available
        try:
            subprocess.run([sys.executable, '-m', 'pytest', '--version'], 
                         capture_output=True, check=True)
            print("✅ pytest is available")
        except subprocess.CalledProcessError:
            print("❌ pytest is not available")
            return False
        
        # Check if test files exist
        missing_files = []
        for category, files in self.test_categories.items():
            for file_path in files:
                full_path = self.project_root / file_path
                if not full_path.exists():
                    missing_files.append(file_path)
        
        if missing_files:
            print(f"⚠️  Missing test files: {missing_files}")
            return False
        
        print("✅ All dependencies and test files found")
        return True


def main():
    """Main entry point for Discord test runner."""
    parser = argparse.ArgumentParser(description='Run Discord functionality tests')
    parser.add_argument(
        'category',
        nargs='?',
        choices=['all', 'quick', 'unit', 'integration', 'spell'],
        default='all',
        help='Test category to run (default: all)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Verbose output'
    )
    parser.add_argument(
        '--stop-on-fail', '-x',
        action='store_true',
        help='Stop on first failure'
    )
    parser.add_argument(
        '--check-deps',
        action='store_true',
        help='Check dependencies and exit'
    )
    
    args = parser.parse_args()
    
    runner = DiscordTestRunner()
    
    # Check dependencies if requested
    if args.check_deps:
        success = runner.check_dependencies()
        sys.exit(0 if success else 1)
    
    # Run tests
    if args.category == 'all':
        results = runner.run_all(args.verbose, args.stop_on_fail)
    elif args.category == 'spell':
        results = runner.run_spell_detection_tests(args.verbose)
    else:
        results = runner.run_category(args.category, args.verbose, args.stop_on_fail)
    
    # Print summary
    runner.print_summary(results)
    
    # Exit with appropriate code
    sys.exit(0 if results['success'] else 1)


if __name__ == "__main__":
    main()