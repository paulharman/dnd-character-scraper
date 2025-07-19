#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simple test command script for D&D Beyond Character Scraper.

This script provides easy-to-use commands for running tests without
needing to remember complex pytest or test runner commands.
"""

import sys
import os
import subprocess
import argparse
from pathlib import Path

# Set UTF-8 encoding for Windows compatibility
if sys.platform.startswith('win'):
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.detach())
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.detach())

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def run_command(cmd, description="Running command"):
    """Run a command and return the exit code."""
    try:
        print(f"\n🔧 {description}")
    except UnicodeEncodeError:
        print(f"\n[*] {description}")
    
    print(f"Command: {' '.join(cmd)}")
    try:
        print("─" * 60)
    except UnicodeEncodeError:
        print("-" * 60)
    
    try:
        result = subprocess.run(cmd, cwd=project_root)
        return result.returncode
    except KeyboardInterrupt:
        print("\n❌ Test execution interrupted by user")
        return 1
    except Exception as e:
        print(f"\n❌ Error running command: {e}")
        return 1


def main():
    """Main entry point for test commands."""
    parser = argparse.ArgumentParser(
        description="Easy test commands for D&D Beyond Character Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test.py                    # Run all tests
  python test.py --quick            # Run quick smoke tests
  python test.py --unit             # Run only unit tests
  python test.py --coverage         # Run tests with coverage
  python test.py --spell            # Run spell-related tests
  python test.py --file tests/unit/calculators/test_spell_processor.py
        """
    )
    
    # Test suite options
    parser.add_argument('--all', action='store_true', 
                       help='Run complete test suite (default)')
    parser.add_argument('--quick', action='store_true',
                       help='Run quick smoke tests for fast feedback')
    parser.add_argument('--unit', action='store_true',
                       help='Run only unit tests')
    parser.add_argument('--integration', action='store_true',
                       help='Run only integration tests')
    parser.add_argument('--edge', action='store_true',
                       help='Run only edge case tests')
    
    # Coverage options
    parser.add_argument('--coverage', action='store_true',
                       help='Run tests with coverage report')
    parser.add_argument('--coverage-html', action='store_true',
                       help='Generate HTML coverage report')
    
    # Specific test options
    parser.add_argument('--file', type=str,
                       help='Run specific test file')
    parser.add_argument('--pattern', '-k', type=str,
                       help='Run tests matching pattern')
    parser.add_argument('--spell', action='store_true',
                       help='Run spell-related tests')
    parser.add_argument('--calculator', action='store_true',
                       help='Run calculator tests')
    parser.add_argument('--discord', action='store_true',
                       help='Run Discord integration tests')
    
    # Output options
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Verbose output')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Quiet output')
    parser.add_argument('--debug', action='store_true',
                       help='Drop into debugger on failures')
    
    # Utility options
    parser.add_argument('--list', action='store_true',
                       help='List available test commands')
    parser.add_argument('--setup-check', action='store_true',
                       help='Check if test environment is set up correctly')
    
    args = parser.parse_args()
    
    # Handle utility commands
    if args.list:
        print_available_commands()
        return 0
    
    if args.setup_check:
        return check_test_setup()
    
    # Determine which tests to run
    if args.quick:
        return run_quick_tests(args)
    elif args.unit:
        return run_unit_tests(args)
    elif args.integration:
        return run_integration_tests(args)
    elif args.edge:
        return run_edge_tests(args)
    elif args.file:
        return run_specific_file(args.file, args)
    elif args.pattern:
        return run_pattern_tests(args.pattern, args)
    elif args.spell:
        return run_spell_tests(args)
    elif args.calculator:
        return run_calculator_tests(args)
    elif args.discord:
        return run_discord_tests(args)
    elif args.coverage or args.coverage_html:
        return run_coverage_tests(args)
    else:
        # Default: run all tests
        return run_all_tests(args)


def print_available_commands():
    """Print available test commands."""
    print("""
🧪 Available Test Commands

Basic Commands:
  python test.py                    # Run complete test suite
  python test.py --quick            # Quick smoke tests (~30 seconds)
  python test.py --unit             # Unit tests only
  python test.py --integration      # Integration tests only
  python test.py --edge             # Edge case tests only

Coverage Commands:
  python test.py --coverage         # Run with coverage report
  python test.py --coverage-html    # Generate HTML coverage report

Specific Test Commands:
  python test.py --spell            # All spell-related tests
  python test.py --calculator       # All calculator tests
  python test.py --discord          # Discord integration tests
  python test.py --file <path>      # Run specific test file
  python test.py -k <pattern>       # Run tests matching pattern

Output Options:
  python test.py --verbose          # Detailed output
  python test.py --quiet            # Minimal output
  python test.py --debug            # Drop into debugger on failures

Utility Commands:
  python test.py --list             # Show this help
  python test.py --setup-check      # Verify test environment

Examples:
  python test.py -k "spell and not integration"  # Spell unit tests
  python test.py --file tests/unit/calculators/test_spell_processor.py
  python test.py --spell --verbose --coverage
    """)


def check_test_setup():
    """Check if the test environment is properly set up."""
    print("🔍 Checking test environment setup...")
    
    issues = []
    
    # Check if required directories exist
    required_dirs = ['tests', 'src', 'tests/fixtures', 'tests/unit']
    for dir_path in required_dirs:
        if not (project_root / dir_path).exists():
            issues.append(f"Missing directory: {dir_path}")
    
    # Check if key test files exist
    key_files = ['tests/run_all_tests.py', 'tests/factories.py']
    for file_path in key_files:
        if not (project_root / file_path).exists():
            issues.append(f"Missing file: {file_path}")
    
    # Check if pytest is available
    try:
        import pytest
        print("✅ pytest is available")
    except ImportError:
        issues.append("pytest not installed - run: pip install -r requirements-dev.txt")
    
    # Check if src modules can be imported
    try:
        sys.path.insert(0, str(project_root / 'src'))
        from models.character import Character
        print("✅ Source modules can be imported")
    except ImportError as e:
        issues.append(f"Cannot import source modules: {e}")
    
    if issues:
        print("\n❌ Test environment issues found:")
        for issue in issues:
            print(f"  • {issue}")
        return 1
    else:
        print("\n✅ Test environment is properly set up!")
        return 0


def run_quick_tests(args):
    """Run quick smoke tests."""
    cmd = [sys.executable, '-m', 'tests.quick', '--smoke']
    return run_command(cmd, "Running quick smoke tests")


def run_all_tests(args):
    """Run the complete test suite."""
    cmd = [sys.executable, 'tests/run_all_tests.py']
    
    if args.verbose:
        cmd.extend(['-v', '2'])
    elif args.quiet:
        cmd.extend(['-v', '0'])
    
    return run_command(cmd, "Running complete test suite")


def run_unit_tests(args):
    """Run unit tests only."""
    cmd = [sys.executable, 'tests/run_all_tests.py', '--suite', 'unit']
    
    if args.verbose:
        cmd.extend(['-v', '2'])
    elif args.quiet:
        cmd.extend(['-v', '0'])
    
    return run_command(cmd, "Running unit tests")


def run_integration_tests(args):
    """Run integration tests only."""
    cmd = [sys.executable, 'tests/run_all_tests.py', '--suite', 'integration']
    
    if args.verbose:
        cmd.extend(['-v', '2'])
    elif args.quiet:
        cmd.extend(['-v', '0'])
    
    return run_command(cmd, "Running integration tests")


def run_edge_tests(args):
    """Run edge case tests only."""
    cmd = [sys.executable, 'tests/run_all_tests.py', '--suite', 'edge']
    
    if args.verbose:
        cmd.extend(['-v', '2'])
    elif args.quiet:
        cmd.extend(['-v', '0'])
    
    return run_command(cmd, "Running edge case tests")


def run_coverage_tests(args):
    """Run tests with coverage."""
    cmd = [sys.executable, '-m', 'pytest', '--cov=src']
    
    if args.coverage_html:
        cmd.append('--cov-report=html')
        description = "Running tests with HTML coverage report"
    else:
        cmd.append('--cov-report=term-missing')
        description = "Running tests with coverage report"
    
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')
    
    exit_code = run_command(cmd, description)
    
    if args.coverage_html and exit_code == 0:
        print(f"\n📊 HTML coverage report generated in: {project_root}/htmlcov/index.html")
    
    return exit_code


def run_specific_file(file_path, args):
    """Run a specific test file."""
    cmd = [sys.executable, '-m', 'pytest', file_path]
    
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')
    
    if args.debug:
        cmd.append('--pdb')
    
    return run_command(cmd, f"Running tests in {file_path}")


def run_pattern_tests(pattern, args):
    """Run tests matching a pattern."""
    cmd = [sys.executable, '-m', 'pytest', '-k', pattern]
    
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')
    
    if args.debug:
        cmd.append('--pdb')
    
    return run_command(cmd, f"Running tests matching pattern: {pattern}")


def run_spell_tests(args):
    """Run all spell-related tests."""
    cmd = [sys.executable, '-m', 'pytest', '-k', 'spell']
    
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')
    
    if args.coverage:
        cmd.extend(['--cov=src', '--cov-report=term-missing'])
    
    return run_command(cmd, "Running spell-related tests")


def run_calculator_tests(args):
    """Run all calculator tests."""
    cmd = [sys.executable, '-m', 'pytest', 'tests/calculators/', 'tests/unit/calculators/']
    
    if args.verbose:
        cmd.append('-v')
    elif args.quiet:
        cmd.append('-q')
    
    if args.coverage:
        cmd.extend(['--cov=src.calculators', '--cov-report=term-missing'])
    
    return run_command(cmd, "Running calculator tests")


def run_discord_tests(args):
    """Run Discord integration tests."""
    try:
        # Try to use the dedicated Discord test runner
        cmd = [sys.executable, 'tests/run_discord_tests.py', 'all']
        
        if args.verbose:
            cmd.append('--verbose')
        
        return run_command(cmd, "Running Discord integration tests")
    except Exception:
        # Fallback to pytest with Discord test files
        cmd = [sys.executable, '-m', 'pytest', 
               'tests/unit/services/test_discord_service.py',
               'tests/unit/services/test_change_detection_service.py',
               'tests/unit/services/test_notification_manager.py',
               'tests/unit/services/test_spell_detection_fixes.py',
               'tests/integration/test_discord_integration.py']
        
        if args.verbose:
            cmd.append('-v')
        elif args.quiet:
            cmd.append('-q')
        
        if args.coverage:
            cmd.extend(['--cov=discord', '--cov-report=term-missing'])
        
        return run_command(cmd, "Running Discord tests (fallback mode)")


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n❌ Interrupted by user")
        sys.exit(1)