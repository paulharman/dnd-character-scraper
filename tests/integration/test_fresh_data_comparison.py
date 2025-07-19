#!/usr/bin/env python3
"""
Fresh Data Comparison Test - Fair Parser Comparison

This test compares the original and refactored parsers using fresh data
from D&D Beyond, which is how both are intended to be used in production.

The original parser always fetches fresh data, while the refactored parser
can work with both fresh data and existing JSON files.
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

class FreshDataParserComparisonTest:
    """Test class for comparing parsers using fresh data from D&D Beyond."""
    
    def __init__(self):
        self.project_root = project_root
        self.parser_dir = self.project_root / "parser"
        self.original_parser = self.parser_dir / "dnd_json_to_markdown_original.py"
        self.refactored_parser = self.parser_dir / "dnd_json_to_markdown.py"
        
    def compare_fresh_data_parsers(self, character_id: str) -> Dict:
        """Compare both parsers using fresh data for the given character ID."""
        print(f"\n🔍 Testing character ID {character_id} with fresh data...")
        
        test_result = {
            "character_id": character_id,
            "original_success": False,
            "refactored_success": False,
            "outputs_match": False,
            "errors": [],
            "differences": []
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Output file paths
            original_output = temp_path / f"character_{character_id}_original.md"
            refactored_output = temp_path / f"character_{character_id}_refactored.md"
            
            # Run original parser (fetches fresh data)
            print("  Running original parser with fresh data...")
            orig_success, orig_error = self.run_original_parser(character_id, original_output)
            test_result["original_success"] = orig_success
            
            if not orig_success:
                test_result["errors"].append(f"Original: {orig_error}")
                print(f"  ❌ Original parser failed: {orig_error}")
            else:
                print("  ✅ Original parser succeeded")
            
            # Run refactored parser (also fetch fresh data via character ID)
            print("  Running refactored parser with fresh data...")
            refact_success, refact_error = self.run_refactored_parser(character_id, refactored_output)
            test_result["refactored_success"] = refact_success
            
            if not refact_success:
                test_result["errors"].append(f"Refactored: {refact_error}")
                print(f"  ❌ Refactored parser failed: {refact_error}")
            else:
                print("  ✅ Refactored parser succeeded")
            
            # Compare outputs if both succeeded
            if orig_success and refact_success:
                print("  Comparing outputs...")
                
                if original_output.exists() and refactored_output.exists():
                    outputs_match, differences = self.compare_outputs(original_output, refactored_output)
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
                        shutil.copy2(original_output, debug_dir / f"character_{character_id}_original_fresh.md")
                        shutil.copy2(refactored_output, debug_dir / f"character_{character_id}_refactored_fresh.md")
                        print(f"  📁 Debug outputs saved to {debug_dir}")
                else:
                    print("  ❌ One or both output files missing")
                    test_result["errors"].append("Output files missing")
        
        return test_result
    
    def run_original_parser(self, character_id: str, output_file: Path) -> Tuple[bool, str]:
        """Run the original parser with character ID (fetches fresh data)."""
        try:
            cmd = [
                sys.executable, str(self.original_parser),
                character_id, str(output_file)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # Longer timeout for API calls
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
    
    def run_refactored_parser(self, character_id: str, output_file: Path) -> Tuple[bool, str]:
        """Run the refactored parser with character ID (fetches fresh data)."""
        try:
            cmd = [
                sys.executable, "-m", "parser.dnd_json_to_markdown",
                character_id, str(output_file)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,  # Longer timeout for API calls
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
    
    def run_comparison_test(self, character_ids: List[str]) -> Dict:
        """Run comparison tests for multiple character IDs."""
        print("=" * 80)
        print("🔬 FRESH DATA PARSER COMPARISON TEST")
        print("=" * 80)
        print("This test compares both parsers using fresh data from D&D Beyond")
        print("(Original parser always fetches fresh data, refactored parser can do both)")
        print()
        
        test_results = []
        
        for character_id in character_ids:
            test_result = self.compare_fresh_data_parsers(character_id)
            test_results.append(test_result)
        
        # Generate summary
        print("\n" + "=" * 80)
        print("📊 FRESH DATA COMPARISON RESULTS")
        print("=" * 80)
        
        total_tests = len(test_results)
        original_successes = sum(1 for r in test_results if r["original_success"])
        refactored_successes = sum(1 for r in test_results if r["refactored_success"])
        both_successes = sum(1 for r in test_results if r["original_success"] and r["refactored_success"])
        matching_outputs = sum(1 for r in test_results if r["outputs_match"])
        
        print(f"Total Character IDs Tested: {total_tests}")
        print(f"Original Parser Success Rate: {original_successes}/{total_tests} ({100*original_successes/total_tests if total_tests > 0 else 0:.1f}%)")
        print(f"Refactored Parser Success Rate: {refactored_successes}/{total_tests} ({100*refactored_successes/total_tests if total_tests > 0 else 0:.1f}%)")
        print(f"Both Parsers Succeeded: {both_successes}/{total_tests}")
        print(f"Identical Outputs: {matching_outputs}/{total_tests}")
        
        # Overall assessment
        all_tests_pass = (
            matching_outputs == both_successes and
            both_successes == total_tests
        )
        
        print("\n" + "=" * 80)
        if all_tests_pass:
            print("🎉 ALL TESTS PASSED - BOTH PARSERS PRODUCE IDENTICAL RESULTS!")
            print("✅ Original and refactored parsers produce identical outputs with fresh data")
            print("✅ Refactor maintains perfect compatibility")
        else:
            print("❌ DIFFERENCES DETECTED")
            if matching_outputs < both_successes:
                print("⚠️  Parsers produce different outputs")
            if both_successes < total_tests:
                print("⚠️  Some parsers failed - check API access or connectivity")
        
        print("=" * 80)
        
        return {
            "total_tests": total_tests,
            "original_successes": original_successes,
            "refactored_successes": refactored_successes,
            "both_successes": both_successes,
            "matching_outputs": matching_outputs,
            "all_tests_pass": all_tests_pass,
            "detailed_results": test_results
        }


def main():
    """Main entry point for the fresh data comparison test."""
    # Test with specific character IDs that we know exist
    test_character_ids = [
        "145081718",  # Ilarion Veles
        # Add more character IDs as needed
    ]
    
    test_runner = FreshDataParserComparisonTest()
    results = test_runner.run_comparison_test(test_character_ids)
    
    # Exit with appropriate code
    sys.exit(0 if results["all_tests_pass"] else 1)


if __name__ == "__main__":
    main()