#!/usr/bin/env python3
"""
End-to-end comparison test for parser refactor validation.

This test compares the original parser with the refactored parser to ensure
identical outputs. This is critical for validating that the refactor maintains
backward compatibility and produces exactly the same results.
"""

import json
import sys
import os
import subprocess
import tempfile
import difflib
from pathlib import Path
from typing import Dict, List, Tuple

# Add the project root to the Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class ParserComparisonTest:
    """Test class for comparing original and refactored parser outputs."""
    
    def __init__(self):
        self.project_root = project_root
        self.character_data_dir = self.project_root / "character_data"
        self.parser_dir = self.project_root / "parser"
        self.original_parser = self.parser_dir / "dnd_json_to_markdown_original.py"
        self.refactored_parser = self.parser_dir / "dnd_json_to_markdown.py"
        self.test_results = []
        
    def get_test_character_files(self) -> List[Path]:
        """Get a selection of character files for testing."""
        # Get character files for multiple different characters
        character_files = []
        
        # Use fresh test files with current v6.0.0 format
        specific_test_files = [
            "character_145081718_test.json",  # Fresh test data
        ]
        
        for filename in specific_test_files:
            file_path = self.character_data_dir / filename
            if file_path.exists():
                character_files.append(file_path)
                print(f"Found test file: {filename}")
            else:
                print(f"Missing test file: {filename}")
        
        return character_files
    
    def run_original_parser(self, character_file: Path, output_file: Path) -> Tuple[bool, str]:
        """Run the original parser and return success status and any error."""
        try:
            # Extract character ID from filename to use the original interface
            char_id = character_file.name.split('_')[1]
            
            # The original parser fetches fresh data from D&D Beyond
            # This is fundamentally different from processing existing files
            # For a fair test, we'll let it fetch fresh data
            cmd = [
                sys.executable, str(self.original_parser),
                char_id, str(output_file), "--verbose"
            ]
            
            result = subprocess.run(
                cmd, 
                capture_output=True, 
                text=True, 
                timeout=60,
                cwd=str(self.project_root)
            )
            
            if result.returncode == 0:
                return True, ""
            else:
                return False, f"Original parser failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Original parser timed out"
        except Exception as e:
            return False, f"Original parser exception: {e}"
    
    def run_refactored_parser(self, character_file: Path, output_file: Path) -> Tuple[bool, str]:
        """Run the refactored parser and return success status and any error."""
        try:
            # Use the specific file path to avoid character ID lookup issues
            cmd = [
                sys.executable, "-m", "parser.dnd_json_to_markdown",
                str(character_file), str(output_file.parent)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True, 
                text=True, 
                timeout=60,
                cwd=str(self.project_root)
            )
            
            if result.returncode == 0:
                return True, ""
            else:
                return False, f"Refactored parser failed: {result.stderr}"
                
        except subprocess.TimeoutExpired:
            return False, "Refactored parser timed out"
        except Exception as e:
            return False, f"Refactored parser exception: {e}"
    
    def compare_outputs(self, original_file: Path, refactored_file: Path) -> Tuple[bool, List[str]]:
        """Compare two output files and return if they match and any differences."""
        try:
            with open(original_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            with open(refactored_file, 'r', encoding='utf-8') as f:
                refactored_content = f.read()
            
            if original_content == refactored_content:
                return True, []
            
            # Generate diff for debugging
            diff = list(difflib.unified_diff(
                original_content.splitlines(keepends=True),
                refactored_content.splitlines(keepends=True),
                fromfile='original',
                tofile='refactored',
                n=3
            ))
            
            return False, diff
            
        except Exception as e:
            return False, [f"Error comparing files: {e}"]
    
    def test_character_file(self, character_file: Path) -> Dict:
        """Test a single character file with both parsers."""
        print(f"\n🧪 Testing character file: {character_file.name}")
        
        test_result = {
            "character_file": character_file.name,
            "original_success": False,
            "refactored_success": False,
            "outputs_match": False,
            "errors": [],
            "differences": []
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Create output file paths
            char_name = character_file.name.replace('.json', '')
            original_output = temp_path / f"{char_name}_original.md"
            refactored_output = temp_path / f"{char_name}_refactored.md"
            
            # Run original parser
            print("  Running original parser...")
            orig_success, orig_error = self.run_original_parser(character_file, original_output)
            test_result["original_success"] = orig_success
            
            if not orig_success:
                test_result["errors"].append(f"Original: {orig_error}")
                print(f"  ❌ Original parser failed: {orig_error}")
            else:
                print("  ✅ Original parser succeeded")
            
            # Run refactored parser
            print("  Running refactored parser...")
            refact_success, refact_error = self.run_refactored_parser(character_file, refactored_output)
            test_result["refactored_success"] = refact_success
            
            if not refact_success:
                test_result["errors"].append(f"Refactored: {refact_error}")
                print(f"  ❌ Refactored parser failed: {refact_error}")
            else:
                print("  ✅ Refactored parser succeeded")
            
            # Compare outputs if both succeeded
            if orig_success and refact_success:
                print("  Comparing outputs...")
                
                # Find the actual refactored output file
                # The refactored parser may create a file with a different name
                refactored_files = list(temp_path.glob("*refactored*.md"))
                if not refactored_files:
                    # Look for any .md files in the temp directory
                    all_md_files = list(temp_path.glob("*.md"))
                    # Filter out the original file
                    refactored_files = [f for f in all_md_files if "original" not in f.name]
                
                if refactored_files:
                    actual_refactored_output = refactored_files[0]
                    outputs_match, differences = self.compare_outputs(original_output, actual_refactored_output)
                    test_result["outputs_match"] = outputs_match
                    test_result["differences"] = differences[:50]  # Limit diff size
                    
                    if outputs_match:
                        print("  ✅ Outputs match perfectly!")
                    else:
                        print(f"  ❌ Outputs differ ({len(differences)} lines of diff)")
                        if len(differences) <= 10:
                            for line in differences[:10]:
                                print(f"    {line.rstrip()}")
                        else:
                            print(f"    ... showing first 10 of {len(differences)} diff lines ...")
                            for line in differences[:10]:
                                print(f"    {line.rstrip()}")
                    
                    # Save outputs for debugging if they differ
                    if not outputs_match:
                        debug_dir = self.project_root / "test_debug_outputs"
                        debug_dir.mkdir(exist_ok=True)
                        
                        import shutil
                        shutil.copy2(original_output, debug_dir / f"{char_name}_original_debug.md")
                        shutil.copy2(actual_refactored_output, debug_dir / f"{char_name}_refactored_debug.md")
                        print(f"  📁 Debug outputs saved to {debug_dir}")
                else:
                    print("  ❌ Could not find refactored output file")
                    test_result["errors"].append("Refactored output file not found")
                    # List all files in temp directory for debugging
                    print(f"  Available files in {temp_path}:")
                    for f in temp_path.iterdir():
                        print(f"    {f.name}")
            
        
        return test_result
    
    def run_command_line_interface_tests(self) -> Dict:
        """Test that the command line interfaces work as expected."""
        print(f"\n🖥️ Testing command line interfaces...")
        
        cli_test_result = {
            "character_id_interface": False,
            "json_file_interface": False,
            "errors": []
        }
        
        # Test character ID interface (user's original command)
        char_files = self.get_test_character_files()
        if char_files:
            test_file = char_files[0]
            char_id = test_file.name.split('_')[1]
            
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                output_file = temp_path / "test_output.md"
                
                try:
                    cmd = [
                        sys.executable, "-m", "parser.dnd_json_to_markdown",
                        char_id, str(output_file)
                    ]
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True, 
                        text=True, 
                        timeout=30,
                        cwd=str(self.project_root)
                    )
                    
                    if result.returncode == 0 and output_file.exists():
                        cli_test_result["character_id_interface"] = True
                        print("  ✅ Character ID interface works")
                    else:
                        cli_test_result["errors"].append(f"Character ID interface failed: {result.stderr}")
                        print("  ❌ Character ID interface failed")
                        
                except Exception as e:
                    cli_test_result["errors"].append(f"Character ID interface exception: {e}")
                    print(f"  ❌ Character ID interface exception: {e}")
                
                # Test JSON file interface
                try:
                    cmd = [
                        sys.executable, "-m", "parser.dnd_json_to_markdown",
                        str(test_file), str(temp_path)
                    ]
                    
                    result = subprocess.run(
                        cmd,
                        capture_output=True, 
                        text=True, 
                        timeout=30,
                        cwd=str(self.project_root)
                    )
                    
                    if result.returncode == 0:
                        cli_test_result["json_file_interface"] = True
                        print("  ✅ JSON file interface works")
                    else:
                        cli_test_result["errors"].append(f"JSON file interface failed: {result.stderr}")
                        print("  ❌ JSON file interface failed")
                        
                except Exception as e:
                    cli_test_result["errors"].append(f"JSON file interface exception: {e}")
                    print(f"  ❌ JSON file interface exception: {e}")
        
        return cli_test_result
    
    def generate_report(self) -> str:
        """Generate a comprehensive test report."""
        total_tests = len(self.test_results)
        successful_original = sum(1 for r in self.test_results if r["original_success"])
        successful_refactored = sum(1 for r in self.test_results if r["refactored_success"])
        matching_outputs = sum(1 for r in self.test_results if r["outputs_match"])
        
        report = f"""
# Parser Refactor Validation Report

## Summary
- **Total Character Files Tested**: {total_tests}
- **Original Parser Success Rate**: {successful_original}/{total_tests} ({100*successful_original/total_tests if total_tests > 0 else 0:.1f}%)
- **Refactored Parser Success Rate**: {successful_refactored}/{total_tests} ({100*successful_refactored/total_tests if total_tests > 0 else 0:.1f}%)
- **Output Match Rate**: {matching_outputs}/{total_tests} ({100*matching_outputs/total_tests if total_tests > 0 else 0:.1f}%)

## Detailed Results

"""
        
        for result in self.test_results:
            report += f"### {result['character_file']}\n"
            report += f"- Original Parser: {'✅' if result['original_success'] else '❌'}\n"
            report += f"- Refactored Parser: {'✅' if result['refactored_success'] else '❌'}\n"
            report += f"- Outputs Match: {'✅' if result['outputs_match'] else '❌'}\n"
            
            if result['errors']:
                report += "- Errors:\n"
                for error in result['errors']:
                    report += f"  - {error}\n"
            
            if result['differences']:
                report += f"- Differences: {len(result['differences'])} lines\n"
            
            report += "\n"
        
        return report
    
    def run_full_test_suite(self):
        """Run the complete test suite."""
        print("=" * 80)
        print("🔬 PARSER REFACTOR END-TO-END VALIDATION")
        print("=" * 80)
        
        # Get test files
        character_files = self.get_test_character_files()
        
        if not character_files:
            print("❌ No character files found for testing!")
            return False
        
        print(f"Found {len(character_files)} character files for testing")
        
        # Test each character file
        for character_file in character_files:
            test_result = self.test_character_file(character_file)
            self.test_results.append(test_result)
        
        # Test command line interfaces
        cli_result = self.run_command_line_interface_tests()
        
        # Generate and display report
        print("\n" + "=" * 80)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        successful_both = sum(1 for r in self.test_results if r["original_success"] and r["refactored_success"])
        matching_outputs = sum(1 for r in self.test_results if r["outputs_match"])
        
        print(f"Character File Tests: {total_tests}")
        print(f"Both Parsers Succeeded: {successful_both}/{total_tests}")
        print(f"Identical Outputs: {matching_outputs}/{total_tests}")
        print(f"CLI Character ID Interface: {'✅' if cli_result['character_id_interface'] else '❌'}")
        print(f"CLI JSON File Interface: {'✅' if cli_result['json_file_interface'] else '❌'}")
        
        # Overall success criteria
        all_tests_pass = (
            matching_outputs == successful_both and
            successful_both == total_tests and
            cli_result['character_id_interface'] and
            cli_result['json_file_interface']
        )
        
        print("\n" + "=" * 80)
        if all_tests_pass:
            print("🎉 ALL TESTS PASSED - REFACTOR IS SUCCESSFUL!")
            print("✅ Original and refactored parsers produce identical outputs")
            print("✅ Command line interfaces work correctly")
            print("✅ Backward compatibility maintained")
        else:
            print("❌ TESTS FAILED - REFACTOR NEEDS ATTENTION")
            if matching_outputs < successful_both:
                print("⚠️  Parsers produce different outputs - refactor broke functionality")
            if successful_both < total_tests:
                print("⚠️  Some parsers failed to run - check error handling")
            if not cli_result['character_id_interface']:
                print("⚠️  Character ID interface not working")
            if not cli_result['json_file_interface']:
                print("⚠️  JSON file interface not working")
        
        print("=" * 80)
        
        # Save detailed report
        report = self.generate_report()
        report_file = self.project_root / "parser_refactor_validation_report.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"📄 Detailed report saved to: {report_file}")
        
        return all_tests_pass


def main():
    """Main entry point for the test."""
    test_runner = ParserComparisonTest()
    success = test_runner.run_full_test_suite()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()