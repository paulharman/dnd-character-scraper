#!/usr/bin/env python3
"""
Comprehensive Baseline Test Script

Run baseline comparison for all available test characters to validate 
that the new v6.0.0 calculator produces results consistent with v5.2.0.
"""

import sys
import json
import asyncio
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.calculators.character_calculator import CharacterCalculator


class ComprehensiveBaselineTest:
    """Comprehensive baseline test for all available characters."""
    
    def __init__(self):
        self.calculator = CharacterCalculator()
        self.test_results = []
        self.available_characters = []
        
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run baseline tests for all available characters."""
        print("🔍 Comprehensive Baseline Test - v5.2.0 vs v6.0.0")
        print("=" * 70)
        
        # Find available character files
        raw_dir = Path("Raw")
        if not raw_dir.exists():
            print("❌ Raw directory not found!")
            return {"success": False, "error": "Raw directory missing"}
        
        character_files = list(raw_dir.glob("*.json"))
        if not character_files:
            print("❌ No character data files found!")
            return {"success": False, "error": "No character files"}
        
        print(f"📋 Found {len(character_files)} character files to test")
        print()
        
        # Test each character
        total_tests = 0
        passed_tests = 0
        
        for char_file in sorted(character_files):
            character_id = char_file.stem
            print(f"🧪 Testing Character {character_id}")
            print("-" * 50)
            
            try:
                result = await self.test_character(character_id)
                self.test_results.append(result)
                
                if result['success']:
                    passed_tests += 1
                    print(f"✅ {result['name']}: {result['matches']}/{result['total_checks']} checks passed")
                else:
                    print(f"❌ {result['name']}: {result['matches']}/{result['total_checks']} checks passed")
                
                total_tests += 1
                
                # Print key discrepancies
                if result['discrepancies']:
                    print("   Key discrepancies:")
                    for disc in result['discrepancies'][:3]:  # Show first 3
                        print(f"     - {disc}")
                
                print()
                
            except Exception as e:
                print(f"❌ Error testing character {character_id}: {str(e)}")
                self.test_results.append({
                    'character_id': character_id,
                    'success': False,
                    'error': str(e)
                })
                total_tests += 1
                print()
        
        # Summary
        print("📊 Test Summary")
        print("=" * 40)
        print(f"Total characters tested: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {total_tests - passed_tests}")
        print(f"Success rate: {passed_tests/total_tests*100:.1f}%" if total_tests > 0 else "N/A")
        
        return {
            "success": passed_tests == total_tests,
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": total_tests - passed_tests,
            "success_rate": passed_tests/total_tests*100 if total_tests > 0 else 0,
            "results": self.test_results
        }
    
    async def test_character(self, character_id: str) -> Dict[str, Any]:
        """Test a single character against baseline."""
        # Check if we have baseline data (we'll need to generate it first)
        baseline_file = Path(f"baseline_{character_id}.json")
        
        if not baseline_file.exists():
            # Generate baseline using current v5.2.0 scraper
            print(f"   📋 Generating baseline for {character_id}...")
            await self.generate_baseline(character_id)
        
        if not baseline_file.exists():
            return {
                'character_id': character_id,
                'success': False,
                'error': 'Could not generate baseline data'
            }
        
        # Load baseline data
        with open(baseline_file, 'r') as f:
            v5_data = json.load(f)
        
        # Load raw data
        raw_file = Path(f"Raw/{character_id}.json")
        with open(raw_file, 'r') as f:
            api_response = json.load(f)
        raw_data = api_response.get('data', {})
        
        # Calculate with new system
        v6_data = self.calculator.calculate_complete_json(raw_data)
        
        # Compare results
        comparison = self.compare_character_data(v5_data, v6_data)
        
        return {
            'character_id': character_id,
            'name': v6_data.get('name', 'Unknown'),
            'success': comparison['success'],
            'matches': comparison['matches'],
            'total_checks': comparison['total_checks'],
            'discrepancies': comparison['discrepancies'],
            'v5_data': v5_data,
            'v6_data': v6_data
        }
    
    async def generate_baseline(self, character_id: str):
        """Generate baseline data using current v5.2.0 scraper."""
        import subprocess
        import time
        
        baseline_file = f"baseline_{character_id}.json"
        
        try:
            # Run the current v5.2.0 scraper
            cmd = ["python3", "enhanced_dnd_scraper.py", character_id, "--output", baseline_file]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode != 0:
                print(f"   ⚠️  Scraper failed for {character_id}: {result.stderr}")
                return False
            
            # Add a small delay for rate limiting
            time.sleep(2)
            return True
            
        except subprocess.TimeoutExpired:
            print(f"   ⚠️  Scraper timeout for {character_id}")
            return False
        except Exception as e:
            print(f"   ⚠️  Scraper error for {character_id}: {str(e)}")
            return False
    
    def compare_character_data(self, v5_data: Dict[str, Any], v6_data: Dict[str, Any]) -> Dict[str, Any]:
        """Compare v5.2.0 and v6.0.0 character data."""
        discrepancies = []
        matches = 0
        total_checks = 0
        
        # Core comparison fields (v5 path, v6 path)
        comparisons = [
            ('basic_info.name', 'name'),
            ('basic_info.level', 'level'),
            ('basic_info.hit_points.maximum', 'max_hp'),
            ('basic_info.armor_class.total', 'armor_class'),
        ]
        
        # Add ability score comparisons
        abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        for ability in abilities:
            comparisons.append((f'ability_scores.{ability}.score', f'ability_scores.{ability}'))
        
        # Perform comparisons
        for v5_path, v6_path in comparisons:
            total_checks += 1
            v5_val = self.get_nested_value(v5_data, v5_path)
            v6_val = self.get_nested_value(v6_data, v6_path)
            
            if v5_val == v6_val:
                matches += 1
            else:
                discrepancies.append(f"{v5_path}: v5={v5_val} vs v6={v6_val}")
        
        # Success threshold: at least 80% of checks should pass
        success = (matches / total_checks) >= 0.8 if total_checks > 0 else False
        
        return {
            'success': success,
            'matches': matches,
            'total_checks': total_checks,
            'discrepancies': discrepancies
        }
    
    def get_nested_value(self, data: Dict[str, Any], path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split('.')
        current = data
        
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        
        return current


async def main():
    """Run comprehensive baseline test."""
    tester = ComprehensiveBaselineTest()
    
    print("Starting comprehensive baseline validation...")
    print("This will test the new v6.0.0 calculator against v5.2.0 for all available characters.")
    print()
    
    results = await tester.run_all_tests()
    
    if results['success']:
        print("🎉 All baseline tests passed!")
        print("✅ New v6.0.0 calculator is validated and ready for production.")
    else:
        print("⚠️  Some baseline tests failed.")
        print("🔧 Review discrepancies before proceeding with development.")
    
    # Save detailed results (exclude complex objects for JSON serialization)
    results_file = "comprehensive_baseline_results.json"
    
    # Create a simplified version for JSON serialization
    simplified_results = {
        "success": results['success'],
        "total_tests": results['total_tests'],
        "passed_tests": results['passed_tests'],
        "failed_tests": results['failed_tests'],
        "success_rate": results['success_rate'],
        "summary": [
            {
                "character_id": r.get('character_id'),
                "name": r.get('name'),
                "success": r.get('success'),
                "matches": r.get('matches'),
                "total_checks": r.get('total_checks'),
                "discrepancies": r.get('discrepancies', [])[:5]  # Limit discrepancies
            }
            for r in results.get('results', [])
        ]
    }
    
    with open(results_file, 'w') as f:
        json.dump(simplified_results, f, indent=2)
    
    print(f"\n📋 Detailed results saved to: {results_file}")
    
    return 0 if results['success'] else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)