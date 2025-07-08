"""
Command-line interface for quick tests.
"""

import sys
from .cli_parser import QuickTestArgumentParser
from .cli_commands import QuickTestCommands

def main():
    """Main entry point for quick tests."""
    parser_handler = QuickTestArgumentParser()
    command_handler = QuickTestCommands()
    
    parser = parser_handler.create_parser()
    args = parser.parse_args()
    
    # Handle utility commands first
    if args.list:
        return command_handler.list_available_options()
    
    if args.validate:
        return command_handler.validate_setup()
    
    # Handle test execution commands
    if args.smoke:
        return command_handler.run_smoke_tests()
    elif args.isolated:
        return command_handler.run_isolated_tests()
    elif args.scenarios:
        return command_handler.run_scenario_tests()
    elif args.calculator:
        return command_handler.run_calculator_test(args.calculator)
    elif args.scenario:
        return command_handler.run_scenario_test(args.scenario)
    elif args.test:
        return command_handler.run_specific_test(args.test)
    else:
        # Default: run all quick tests
        return command_handler.run_all_quick_tests()

if __name__ == '__main__':
    sys.exit(main())