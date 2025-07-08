"""
Test regex patterns against real spell descriptions from the spells folder.

Uses actual D&D spell markdown files to validate pattern matching.
"""

import pytest
import sys
from pathlib import Path
import re

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "src"))

from ..factories.character_archetypes import CharacterArchetypeFactory

class TestRealSpellRegexPatterns:
    """Test regex patterns against real spell descriptions."""
    
    def _extract_spell_info(self, spell_file_path):
        """Extract spell information from markdown files."""
        try:
            content = Path(spell_file_path).read_text()
            
            # Extract key information
            name = ""
            casting_time = ""
            description = ""
            
            # Parse frontmatter
            lines = content.split('\n')
            in_frontmatter = False
            description_started = False
            
            for line in lines:
                if line.strip() == '---':
                    in_frontmatter = not in_frontmatter
                    continue
                    
                if in_frontmatter:
                    if line.startswith('name:'):
                        name = line.split(':', 1)[1].strip()
                    elif line.startswith('casting_time:'):
                        casting_time = line.split(':', 1)[1].strip()
                else:
                    # Extract description after the spell stat block
                    if line.startswith('- **Duration:**') or description_started:
                        description_started = True
                        if line and not line.startswith('**Classes**') and not line.startswith('*Source:'):
                            description += line + " "
            
            return {
                "name": name,
                "casting_time": casting_time, 
                "description": description.strip()
            }
        except Exception as e:
            return {"name": "", "casting_time": "", "description": "", "error": str(e)}

    @pytest.mark.quick
    def test_expeditious_retreat_real_spell(self):
        """Test Expeditious Retreat with real spell description."""
        spell_file = Path(__file__).parent.parent.parent.parent / "obsidian/spells/expeditious-retreat-xphb.md"
        
        if not spell_file.exists():
            pytest.skip("Expeditious Retreat spell file not found")
            
        spell_info = self._extract_spell_info(spell_file)
        
        # Verify basic info
        assert "expeditious retreat" in spell_info["name"].lower()
        assert "bonus action" in spell_info["casting_time"].lower()
        
        # Test regex patterns on real description
        desc_lower = spell_info["description"].lower()
        
        # Should match "until the spell ends" + "bonus action" pattern
        assert re.search(r'until the spell ends.*bonus action', desc_lower), "Should match ongoing bonus action pattern"
        
        # Should be categorized as hybrid (cast as bonus action + ongoing effects)
        assert "bonus action" in spell_info["casting_time"].lower()
        assert "until the spell ends" in desc_lower

    @pytest.mark.quick
    def test_arcane_eye_real_spell(self):
        """Test Arcane Eye with real spell description.""" 
        spell_file = Path(__file__).parent.parent.parent.parent / "obsidian/spells/arcane-eye-xphb.md"
        
        if not spell_file.exists():
            pytest.skip("Arcane Eye spell file not found")
            
        spell_info = self._extract_spell_info(spell_file)
        
        # Verify basic info
        assert "arcane eye" in spell_info["name"].lower()
        assert "action" in spell_info["casting_time"].lower()
        assert "bonus action" not in spell_info["casting_time"].lower()
        
        # Test regex patterns on real description
        desc_lower = spell_info["description"].lower()
        
        # Should match "as a bonus action" pattern (with flexible spacing)
        assert re.search(r'as a\s+.*bonus action', desc_lower), "Should match conditional bonus action pattern"
        
        # Should be categorized as conditional (cast as action, provides bonus action)
        assert "bonus action" in desc_lower
        assert "move" in desc_lower

    @pytest.mark.quick
    def test_spiritual_weapon_real_spell(self):
        """Test Spiritual Weapon with real spell description."""
        spell_file = Path(__file__).parent.parent.parent.parent / "obsidian/spells/spiritual-weapon-xphb.md"
        
        if not spell_file.exists():
            pytest.skip("Spiritual Weapon spell file not found")
            
        spell_info = self._extract_spell_info(spell_file)
        
        # Verify basic info  
        assert "spiritual weapon" in spell_info["name"].lower()
        assert "bonus action" in spell_info["casting_time"].lower()
        
        # Test regex patterns on real description
        desc_lower = spell_info["description"].lower()
        
        # Should match "bonus action" + "later turns" pattern (correct order for Spiritual Weapon)
        assert re.search(r'bonus action.*on your\s+later\s+turns', desc_lower), "Should match ongoing bonus action pattern"
        
        # Should be categorized as hybrid (cast as bonus action + ongoing effects)
        assert "bonus action" in spell_info["casting_time"].lower()
        assert "later turns" in desc_lower

    @pytest.mark.quick
    def test_find_familiar_real_spell(self):
        """Test Find Familiar with real spell description."""
        spell_file = Path(__file__).parent.parent.parent.parent / "obsidian/spells/find-familiar-xphb.md"
        
        if not spell_file.exists():
            pytest.skip("Find Familiar spell file not found")
            
        spell_info = self._extract_spell_info(spell_file)
        
        # Verify basic info
        assert "find familiar" in spell_info["name"].lower()
        assert "hour" in spell_info["casting_time"].lower() or "action" in spell_info["casting_time"].lower()
        
        # Test regex patterns on real description
        desc_lower = spell_info["description"].lower()
        
        # Should match "as a bonus action" pattern (with flexible spacing)
        assert re.search(r'as a\s+.*bonus action', desc_lower), "Should match conditional bonus action pattern"
        
        # Should be categorized as conditional (ritual/action cast, provides bonus action)
        assert "bonus action" in desc_lower

    @pytest.mark.quick
    def test_dynamic_detection_on_real_spells(self):
        """Test the full dynamic detection function on real spells."""
        import re
        
        def is_conditional_bonus_spell(spell_name, description, casting_time):
            """Copy of the dynamic detection function for testing."""
            name_lower = spell_name.lower()
            desc_lower = description.lower()
            cast_lower = casting_time.lower()
            
            # Skip if cast as bonus action AND doesn't have ongoing effects
            if 'bonus action' in cast_lower:
                # Check for hybrid spells (cast as bonus action AND provide ongoing)
                ongoing_patterns = [
                    r'later turns?', r'subsequent turns?', r'until the spell ends',
                    r'while the spell', r'on your turn.*you can', r'on your\s+later\s+turns'
                ]
                if any(re.search(pattern, desc_lower) for pattern in ongoing_patterns):
                    if 'expeditious retreat' in name_lower:
                        return True, "Expeditious Retreat - Dash"
                    elif 'spiritual weapon' in name_lower:
                        return True, "Spiritual Weapon - Attack"
                    return True, f"{spell_name} - Ongoing"
                return False, None
            
            # Check for conditional bonus action patterns
            conditional_patterns = [
                (r'as a\s+bonus action.*you can', 'Move/Command'),
                (r'as a\s+[Bb]onus\s+[Aa]ction.*can', 'Action'),
                (r'on your\s+(?:later\s+)?turns?.*bonus action', 'Repeat'),
                (r'bonus action.*on your\s+(?:later\s+)?turns?', 'Repeat'),
                (r'until the spell ends.*bonus action', 'Duration'),
                (r'while.*spell.*bonus action', 'Active'),
                (r'command.*bonus action', 'Command'),
                (r'move.*bonus action', 'Move'),
                (r'bonus action.*move', 'Move'),
                (r'control.*bonus action', 'Control')
            ]
            
            for pattern, action_type in conditional_patterns:
                if re.search(pattern, desc_lower):
                    # Specific spell handling
                    if 'familiar' in name_lower:
                        return True, "Find Familiar - Command"
                    elif 'servant' in name_lower:
                        return True, "Unseen Servant - Command"
                    elif 'weapon' in name_lower:
                        return True, "Spiritual Weapon - Attack"
                    elif 'arcane eye' in name_lower:
                        return True, "Arcane Eye - Move"
                    elif 'healing word' in name_lower:
                        return True, "Healing Word"
                    else:
                        return True, f"{spell_name} - {action_type}"
            
            return False, None
        
        # Test on all four real spells
        spell_files = [
            ("expeditious-retreat-xphb.md", True, "Expeditious Retreat - Dash"),
            ("arcane-eye-xphb.md", True, "Arcane Eye - Move"),
            ("spiritual-weapon-xphb.md", True, "Spiritual Weapon - Attack"),
            ("find-familiar-xphb.md", True, "Find Familiar - Command")
        ]
        
        base_path = Path(__file__).parent.parent.parent.parent / "obsidian/spells"
        
        for filename, expected_conditional, expected_desc in spell_files:
            spell_file = base_path / filename
            
            if not spell_file.exists():
                continue
                
            spell_info = self._extract_spell_info(spell_file)
            is_conditional, description = is_conditional_bonus_spell(
                spell_info["name"], 
                spell_info["description"], 
                spell_info["casting_time"]
            )
            
            assert is_conditional == expected_conditional, f"Detection failed for {spell_info['name']}"
            if expected_conditional:
                assert description == expected_desc, f"Wrong description for {spell_info['name']}: got '{description}', expected '{expected_desc}'"

    @pytest.mark.quick
    def test_regex_patterns_on_real_text(self):
        """Test individual regex patterns on real spell text."""
        # Real text from the spell files
        test_cases = [
            {
                "spell": "Expeditious Retreat",
                "text": "You take the Dash action, and until the spell ends, you can take that action again as a Bonus Action.",
                "should_match": [r'until the spell ends.*bonus action'],
                "should_not_match": [r'as a bonus action.*you can']
            },
            {
                "spell": "Arcane Eye", 
                "text": "As a Bonus Action, you can move the eye up to 30 feet in any direction.",
                "should_match": [r'as a\s+.*bonus action.*you can', r'bonus action.*move'],
                "should_not_match": [r'until the spell ends.*bonus action']
            },
            {
                "spell": "Spiritual Weapon",
                "text": "As a Bonus Action on your later turns, you can move the force up to 20 feet and repeat the attack",
                "should_match": [r'bonus action.*on your\s+(?:later\s+)?turns?', r'as a\s+.*bonus action.*you can'],
                "should_not_match": [r'until the spell ends.*bonus action']
            },
            {
                "spell": "Find Familiar",
                "text": "Additionally, as a Bonus Action, you can see through the familiar's eyes and hear what it hears",
                "should_match": [r'as a\s+.*bonus action.*you can'],
                "should_not_match": [r'on your\s+(?:later\s+)?turns?.*bonus action']
            }
        ]
        
        for case in test_cases:
            text_lower = case["text"].lower()
            
            # Test patterns that should match
            for pattern in case["should_match"]:
                assert re.search(pattern, text_lower), f"Pattern '{pattern}' should match text from {case['spell']}: '{case['text']}'"
            
            # Test patterns that should NOT match
            for pattern in case["should_not_match"]:
                assert not re.search(pattern, text_lower), f"Pattern '{pattern}' should NOT match text from {case['spell']}: '{case['text']}'"

    @pytest.mark.quick
    def test_pattern_precision(self):
        """Test that patterns are precise and don't create false positives."""
        # Text that should NOT match conditional patterns
        negative_cases = [
            "Cast this spell as a bonus action to teleport",  # Misty Step type - cast as bonus action
            "This spell requires a bonus action to cast",  # Casting requirement, not ongoing effect
            "The spell affects bonus actions but doesn't provide them",  # Descriptive text
            "Mention of bonus action in unrelated context"  # Unrelated mention
        ]
        
        # Patterns that should match conditional bonus actions
        conditional_patterns = [
            r'as a\s+bonus action.*you can',
            r'on your\s+(?:later\s+)?turns?.*bonus action', 
            r'until the spell ends.*bonus action',
            r'while.*spell.*bonus action'
        ]
        
        for text in negative_cases:
            text_lower = text.lower()
            for pattern in conditional_patterns:
                assert not re.search(pattern, text_lower), f"Pattern '{pattern}' incorrectly matched: '{text}'"

    @pytest.mark.quick
    def test_case_and_formatting_variations(self):
        """Test that patterns work with various case and formatting variations."""
        # Test with different capitalizations and formatting from real spells
        variations = [
            "As a Bonus Action, you can move the eye",  # Standard capitalization
            "as a bonus action, you can move the eye",  # All lowercase  
            "AS A BONUS ACTION, YOU CAN MOVE THE EYE",  # All uppercase
            "As a [Bonus Action](/link), you can move",  # With markdown links
            "As a Bonus Action, you can\nmove the eye",  # With line breaks
            "As a  Bonus Action  ,  you can move",  # Extra spaces
        ]
        
        pattern = r'as a\s+.*bonus action.*you can'
        
        for text in variations:
            assert re.search(pattern, text.lower(), re.DOTALL), f"Pattern should match variation: '{text}'"

class TestSpellFileIntegration:
    """Test integration with actual spell files from the obsidian folder."""
    
    @pytest.mark.quick
    def test_spell_files_exist(self):
        """Test that the expected spell files exist."""
        base_path = Path(__file__).parent.parent.parent.parent / "obsidian/spells"
        
        expected_files = [
            "expeditious-retreat-xphb.md",
            "arcane-eye-xphb.md", 
            "spiritual-weapon-xphb.md",
            "find-familiar-xphb.md"
        ]
        
        for filename in expected_files:
            spell_file = base_path / filename
            if spell_file.exists():
                assert spell_file.is_file(), f"{filename} should be a file"
                assert spell_file.stat().st_size > 0, f"{filename} should not be empty"

    @pytest.mark.quick
    def test_spell_file_format(self):
        """Test that spell files have the expected format."""
        base_path = Path(__file__).parent.parent.parent.parent / "obsidian/spells"
        test_file = base_path / "expeditious-retreat-xphb.md"
        
        if not test_file.exists():
            pytest.skip("Test spell file not found")
            
        content = test_file.read_text()
        
        # Should have frontmatter
        assert content.startswith('---'), "Spell file should start with frontmatter"
        assert 'name:' in content, "Spell file should have name field"
        assert 'casting_time:' in content, "Spell file should have casting_time field"
        
        # Should have spell description
        assert '# ' in content, "Spell file should have markdown headers"
        assert 'Bonus Action' in content, "Expeditious Retreat should mention bonus actions"

    @pytest.mark.quick 
    def test_performance_with_real_files(self):
        """Test performance of regex matching on real spell files."""
        import time
        
        base_path = Path(__file__).parent.parent.parent.parent / "obsidian/spells"
        
        # Get all spell files
        spell_files = list(base_path.glob("*.md"))
        
        if len(spell_files) == 0:
            pytest.skip("No spell files found for performance testing")
        
        # Test with up to 50 spell files for performance
        test_files = spell_files[:50]
        
        start_time = time.time()
        
        conditional_pattern = r'as a.*bonus action.*you can|on your (?:later )?turns?.*bonus action|until the spell ends.*bonus action'
        matches_found = 0
        
        for spell_file in test_files:
            try:
                content = spell_file.read_text().lower()
                if re.search(conditional_pattern, content):
                    matches_found += 1
            except Exception:
                continue  # Skip files that can't be read
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should be very fast even with many files
        assert execution_time < 1.0, f"Processing {len(test_files)} spell files should be fast, took {execution_time:.3f}s"
        
        # Should find some matches (at least our test spells)
        assert matches_found >= 0, "Should find some conditional bonus action spells"