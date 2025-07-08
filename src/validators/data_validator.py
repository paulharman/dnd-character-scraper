"""
Comprehensive data validation for character scraper output.

Validates actual content and values rather than just file sizes.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of data validation."""
    passed: bool
    field_name: str
    expected: Any
    actual: Any
    message: str


@dataclass
class ValidationSummary:
    """Summary of all validation results."""
    character_id: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    results: List[ValidationResult]
    overall_passed: bool


class DataValidator:
    """
    Comprehensive validator for character data output.
    
    Validates actual data values against baseline expectations.
    """
    
    def __init__(self):
        """Initialize the data validator."""
        self.tolerance = 0.001  # For floating point comparisons
        
    def validate_character_data(self, 
                               character_id: str,
                               current_data: Dict[str, Any], 
                               baseline_data: Dict[str, Any]) -> ValidationSummary:
        """
        Validate current character data against baseline.
        
        Args:
            character_id: Character ID being tested
            current_data: Current v6.0.0 output data
            baseline_data: v5.2.0 baseline data
            
        Returns:
            Comprehensive validation summary
        """
        logger.info(f"Validating character {character_id} data")
        
        results = []
        
        # Basic character info validation
        results.extend(self._validate_basic_info(current_data, baseline_data))
        
        # Ability scores validation
        results.extend(self._validate_ability_scores(current_data, baseline_data))
        
        # Spells validation
        results.extend(self._validate_spells(current_data, baseline_data))
        
        # Inventory validation
        results.extend(self._validate_inventory(current_data, baseline_data))
        
        # Feats validation
        results.extend(self._validate_feats(current_data, baseline_data))
        
        # Skills validation
        results.extend(self._validate_skills(current_data, baseline_data))
        
        # Calculate summary
        passed_tests = sum(1 for r in results if r.passed)
        failed_tests = len(results) - passed_tests
        overall_passed = failed_tests == 0
        
        summary = ValidationSummary(
            character_id=character_id,
            total_tests=len(results),
            passed_tests=passed_tests,
            failed_tests=failed_tests,
            results=results,
            overall_passed=overall_passed
        )
        
        self._log_summary(summary)
        return summary
        
    def _validate_basic_info(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> List[ValidationResult]:
        """Validate basic character information."""
        results = []
        
        # Character name
        current_name = current.get('name', '')
        baseline_name = baseline.get('basic_info', {}).get('name', '')
        results.append(ValidationResult(
            passed=current_name == baseline_name,
            field_name='character_name',
            expected=baseline_name,
            actual=current_name,
            message=f"Character name: expected '{baseline_name}', got '{current_name}'"
        ))
        
        # Character level
        current_level = current.get('level', 0)
        baseline_level = baseline.get('basic_info', {}).get('level', 0)
        results.append(ValidationResult(
            passed=current_level == baseline_level,
            field_name='character_level',
            expected=baseline_level,
            actual=current_level,
            message=f"Character level: expected {baseline_level}, got {current_level}"
        ))
        
        # Experience points
        current_xp = current.get('experience_points', 0)
        baseline_xp = baseline.get('basic_info', {}).get('experience_points', 0)
        results.append(ValidationResult(
            passed=current_xp == baseline_xp,
            field_name='experience_points',
            expected=baseline_xp,
            actual=current_xp,
            message=f"Experience points: expected {baseline_xp}, got {current_xp}"
        ))
        
        return results
        
    def _validate_ability_scores(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> List[ValidationResult]:
        """Validate ability scores."""
        results = []
        
        current_abilities = current.get('ability_scores', {})
        baseline_abilities = baseline.get('ability_scores', {})
        
        abilities = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']
        
        for ability in abilities:
            current_score = current_abilities.get(ability, 0)
            baseline_score = baseline_abilities.get(ability, 0)
            results.append(ValidationResult(
                passed=current_score == baseline_score,
                field_name=f'ability_{ability}',
                expected=baseline_score,
                actual=current_score,
                message=f"Ability {ability}: expected {baseline_score}, got {current_score}"
            ))
            
        return results
        
    def _validate_spells(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> List[ValidationResult]:
        """Validate spell data."""
        results = []
        
        # Total spell count
        current_spells = current.get('spells', {})
        baseline_spells = baseline.get('spells', {})
        
        current_total = sum(len(spells) for spells in current_spells.values())
        baseline_total = sum(len(spells) for spells in baseline_spells.values())
        
        results.append(ValidationResult(
            passed=current_total == baseline_total,
            field_name='total_spells',
            expected=baseline_total,
            actual=current_total,
            message=f"Total spells: expected {baseline_total}, got {current_total}"
        ))
        
        # Spell sources
        current_sources = set(current_spells.keys())
        baseline_sources = set(baseline_spells.keys())
        
        results.append(ValidationResult(
            passed=current_sources == baseline_sources,
            field_name='spell_sources',
            expected=sorted(baseline_sources),
            actual=sorted(current_sources),
            message=f"Spell sources: expected {sorted(baseline_sources)}, got {sorted(current_sources)}"
        ))
        
        # Individual spell names (sample validation)
        for source in current_sources.intersection(baseline_sources):
            current_spell_names = {spell['name'] for spell in current_spells[source]}
            baseline_spell_names = {spell['name'] for spell in baseline_spells[source]}
            
            results.append(ValidationResult(
                passed=current_spell_names == baseline_spell_names,
                field_name=f'spell_names_{source}',
                expected=sorted(baseline_spell_names),
                actual=sorted(current_spell_names),
                message=f"Spell names in {source}: expected {len(baseline_spell_names)}, got {len(current_spell_names)}"
            ))
            
        return results
        
    def _validate_inventory(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> List[ValidationResult]:
        """Validate inventory data."""
        results = []
        
        current_inventory = current.get('inventory', [])
        baseline_inventory = baseline.get('inventory', [])
        
        # Item count
        results.append(ValidationResult(
            passed=len(current_inventory) == len(baseline_inventory),
            field_name='inventory_count',
            expected=len(baseline_inventory),
            actual=len(current_inventory),
            message=f"Inventory items: expected {len(baseline_inventory)}, got {len(current_inventory)}"
        ))
        
        # Item names (sample validation)
        if current_inventory and baseline_inventory:
            current_names = {item['name'] for item in current_inventory if 'name' in item}
            baseline_names = {item['name'] for item in baseline_inventory if 'name' in item}
            
            results.append(ValidationResult(
                passed=len(current_names.intersection(baseline_names)) >= len(baseline_names) * 0.8,
                field_name='inventory_names',
                expected=f"{len(baseline_names)} unique items",
                actual=f"{len(current_names)} unique items, {len(current_names.intersection(baseline_names))} match",
                message=f"Inventory item names: {len(current_names.intersection(baseline_names))}/{len(baseline_names)} items match"
            ))
            
        return results
        
    def _validate_feats(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> List[ValidationResult]:
        """Validate feat data."""
        results = []
        
        current_feats = current.get('feats', [])
        baseline_feats = baseline.get('feats', [])
        
        # Feat count (allow some tolerance for extraction differences)
        feat_count_close = abs(len(current_feats) - len(baseline_feats)) <= 2
        results.append(ValidationResult(
            passed=feat_count_close,
            field_name='feat_count',
            expected=len(baseline_feats),
            actual=len(current_feats),
            message=f"Feats count: expected {len(baseline_feats)}, got {len(current_feats)} (tolerance: ±2)"
        ))
        
        return results
        
    def _validate_skills(self, current: Dict[str, Any], baseline: Dict[str, Any]) -> List[ValidationResult]:
        """Validate skill data."""
        results = []
        
        current_skills = current.get('skills', {})
        baseline_skills = baseline.get('skills', {})
        
        # Skill count
        results.append(ValidationResult(
            passed=len(current_skills) == len(baseline_skills),
            field_name='skill_count',
            expected=len(baseline_skills),
            actual=len(current_skills),
            message=f"Skills count: expected {len(baseline_skills)}, got {len(current_skills)}"
        ))
        
        # Sample skill values (check a few key skills)
        key_skills = ['Perception', 'Investigation', 'Insight', 'Arcana', 'History']
        for skill in key_skills:
            if skill in baseline_skills and skill in current_skills:
                current_bonus = current_skills[skill]
                baseline_bonus = baseline_skills[skill]
                results.append(ValidationResult(
                    passed=current_bonus == baseline_bonus,
                    field_name=f'skill_{skill.lower()}',
                    expected=baseline_bonus,
                    actual=current_bonus,
                    message=f"Skill {skill}: expected {baseline_bonus}, got {current_bonus}"
                ))
                
        return results
        
    def _log_summary(self, summary: ValidationSummary):
        """Log validation summary."""
        if summary.overall_passed:
            logger.info(f"✅ Character {summary.character_id}: ALL {summary.total_tests} tests passed")
        else:
            logger.warning(f"❌ Character {summary.character_id}: {summary.failed_tests}/{summary.total_tests} tests failed")
            
            # Log failed tests
            for result in summary.results:
                if not result.passed:
                    logger.warning(f"  FAIL: {result.message}")


class TestRunner:
    """Run comprehensive validation tests against all characters."""
    
    def __init__(self):
        """Initialize test runner."""
        self.validator = DataValidator()
        
    def run_all_character_tests(self, 
                              current_data_dir: str,
                              baseline_data_dir: str,
                              character_ids: List[str]) -> Dict[str, ValidationSummary]:
        """
        Run validation tests for all characters.
        
        Args:
            current_data_dir: Directory containing current v6.0.0 output
            baseline_data_dir: Directory containing v5.2.0 baseline data
            character_ids: List of character IDs to test
            
        Returns:
            Dictionary mapping character ID to validation summary
        """
        logger.info(f"Running comprehensive validation for {len(character_ids)} characters")
        
        results = {}
        overall_passed = 0
        overall_failed = 0
        
        for char_id in character_ids:
            try:
                # Load current data
                current_file = Path(current_data_dir) / f"v6_{char_id}.json"
                baseline_file = Path(baseline_data_dir) / f"baseline_{char_id}.json"
                
                if not current_file.exists():
                    logger.error(f"Current data file not found: {current_file}")
                    continue
                    
                if not baseline_file.exists():
                    logger.error(f"Baseline data file not found: {baseline_file}")
                    continue
                
                with open(current_file, 'r') as f:
                    current_data = json.load(f)
                    
                with open(baseline_file, 'r') as f:
                    baseline_data = json.load(f)
                
                # Run validation
                summary = self.validator.validate_character_data(char_id, current_data, baseline_data)
                results[char_id] = summary
                
                if summary.overall_passed:
                    overall_passed += 1
                else:
                    overall_failed += 1
                    
            except Exception as e:
                logger.error(f"Failed to validate character {char_id}: {e}")
                continue
        
        # Log overall results
        total_characters = overall_passed + overall_failed
        logger.info(f"\n=== OVERALL VALIDATION RESULTS ===")
        logger.info(f"Characters tested: {total_characters}")
        logger.info(f"Passed: {overall_passed}")
        logger.info(f"Failed: {overall_failed}")
        logger.info(f"Success rate: {overall_passed/total_characters*100:.1f}%")
        
        return results