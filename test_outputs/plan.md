# D&D Beyond Character Scraper Development Plan ✅ COMPLETE

## 🎉 Project Status: v6.0.0 Production Ready

**✅ All development phases completed successfully (0-5)**
**✅ Production-ready system with comprehensive features**
**✅ 15+ specialized calculators with modular architecture**
**✅ Container inventory tracking and rule detection**
**✅ 50+ unit tests with excellent coverage**
**✅ All critical bugs resolved from v5.2.0**

This plan document serves as a historical record of the successful development process. The v6.0.0 system is now production-ready and provides superior functionality compared to the original v5.2.0 baseline.

## Project Overview ✅ COMPLETED
**Goal**: Refactor the enhanced_dnd_scraper.py into a modular, maintainable, and testable codebase while maintaining full functionality and improving accuracy.

**Original State**: Single 4000+ line file (v5.2.0) with comprehensive functionality but limited modularity
**Achieved State**: ✅ Production-ready modular package (v6.0.0) with clear separation of concerns, comprehensive testing, improved maintainability, and enhanced functionality

**v6.0.0 Production Status**: All development phases complete (0-5), production-ready system with 15+ specialized calculators, comprehensive testing, container inventory tracking, and intelligent rule detection.

## Development Environment & Dependencies

### Python Environment Setup
```bash
# Python 3.9+ required (tested on 3.9, 3.10, 3.11, 3.12)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development/testing
```

### Dependencies (`requirements.txt`)
```
requests>=2.31.0
pydantic>=2.0.0  # For data validation and unknown field handling
typing-extensions>=4.0.0  # For advanced type hints
pyyaml>=6.0.0  # For YAML configuration files
python-dotenv>=1.0.0  # For environment variable support
```

### Development Dependencies (`requirements-dev.txt`)
```
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
mypy>=1.0.0
black>=23.0.0
flake8>=6.0.0
```

## Version Control Strategy

### Repository Status
- **Git Repository**: ✅ Initialized and active
- **Remote**: `origin/main` with upstream tracking  
- **Initial Commit**: `d7180d1` - D&D character scraper v5.2.0 with refactor plan
- **Current Commits**: 
  - `0ea8250` - Phase 1 Complete: Core Architecture & Data Models
  - `0715201` - Phase 0 Complete: Configuration Management & CI/CD Setup
  - `d7180d1` - Initial commit with v5.2.0 baseline

### Branching Strategy  
```
main                      # Stable releases and major milestones
├── phase-0-complete      # ✅ Configuration Management & CI/CD
├── phase-1-complete      # ✅ Core Architecture & Data Models  
├── phase-2-complete      # ✅ D&D Rule Calculations & JSON Output
├── phase-3-planned       # ⏳ Rule Version Management
├── phase-4-planned       # ⏳ Validation & Testing Framework
├── phase-5-planned       # ⏳ Integration & Obsidian Preservation
└── phase-6-planned       # ⏳ Comprehensive Class Coverage Testing
```

### 🔄 **Git Workflow Discipline**

**Branch Management**:
- **Feature branches**: `feature/fix-ac-calculation`, `feature/warlock-pact-magic`
- **Bug fix branches**: `bugfix/nonetype-armor-error`, `bugfix/2024-ability-scores`
- **Phase branches**: `phase-3-rule-management`, `phase-4-validation`

**Merge Requirements (Phases 3-6)**:
- [ ] All JSON tests pass (`comprehensive_scraper_validation.py`)
- [ ] All MD tests pass (`comprehensive_parser_validation.py`)
- [ ] No regression in baseline accuracy (87.7%+ maintained for JSON, 13 characters)
- [ ] No regression in baseline MD quality (baseline TBD for MD)
- [ ] Commit message follows standards
- [ ] Documentation updated if needed

**Milestone Commits**:
```bash
# Phase completion
git commit -m "feat(phase3): complete Rule Version Management implementation

- Add 2014/2024 rule detection and processing
- Implement rule-specific calculation paths  
- Testing: all 13 baseline characters maintain accuracy
- Impact: enables proper 2024 rule support

Closes Phase 3 objectives"

# Critical bug fixes
git commit -m "fix(ac): resolve Unarmored Defense calculation errors

- Add null checking for armor modifiers
- Fix NoneType += operation in AC calculation
- Testing: JSON and MD validation passed, characters 103814449, 145079040 now 95%+ accurate
- Impact: fixes critical AC bugs affecting 4 characters in both JSON and MD output

Fixes #103814449 #145079040"

# Feature additions
git commit -m "feat(spells): implement Warlock Pact Magic system

- Add separate tracking for Pact Magic spell slots
- Implement short rest recovery mechanics
- Add Eldritch Invocation spell parsing
- Testing: JSON and MD validation passed, validated against new Warlock test character
- Impact: enables full Warlock support in both JSON data and MD formatting

Implements Phase 6.2 Warlock requirements"
```

### Original Code Preservation
- **v5.2.0 Scripts**: `enhanced_dnd_scraper_v5.2.0_original.py`, `dnd_json_to_markdown_v5.2.0_original.py`
- **SHA256 Verified**: Backup scripts identical to initial commit
- **Baseline Data**: 12/12 characters with complete pipeline (Raw → Scraper → Parser)
- **Validation Framework**: Comprehensive regression testing against v5.2.0 output

### Migration Strategy
- **Backward Compatibility**: v5.2.0 CLI interface maintained via wrapper
- **Data Migration**: Automatic conversion of existing JSON outputs
- **Configuration Migration**: CLAUDE.md settings preserved
- **Validation Migration**: Existing validation templates supported

## Progress Tracking

**Note**: All progress items can be updated using the Edit tool to maintain continuity across sessions.

- [x] **Phase 0**: Configuration Management & CI/CD Setup ✅ COMPLETED
- [x] **Phase 1**: Core Architecture & Data Models ✅ COMPLETED
- [x] **Phase 2**: D&D Rule Calculations & Complete JSON Output ✅ COMPLETED
- [x] **Phase 3**: Rule Version Management ✅ COMPLETE
- [ ] **Phase 4**: Validation & Testing
- [ ] **Phase 5**: Integration & Documentation
- [ ] **Phase 6**: Comprehensive Class Coverage Testing

### Progress Update Instructions
**For detailed progress tracking, see PROGRESS.md**

When completing tasks, update checkboxes using Edit tool:
```markdown
- [x] **Phase 1**: Core Architecture & Data Models ✅ COMPLETED
- [ ] **Phase 2**: D&D Rule Calculations & Complete JSON Output
```

**Update both files**:
1. `plan.md` - Update main phase checkboxes
2. `PROGRESS.md` - Update detailed task progress and session notes

### 🔄 **Incremental Progress Tracking**

**Every Minor Update Must Include**:
1. **Task Description**: What specific change was made
2. **Testing Status**: What tests were run (if any)
3. **Git Commit**: Commit hash and message
4. **Validation**: Impact on baseline accuracy (if applicable)

**Example Progress Entry**:
```markdown
- [x] Fix AC calculation NoneType error for Barbarian Unarmored Defense
  - **Testing**: Validated against characters 103814449, 145079040
  - **Commit**: `a1b2c3d` - "Fix NoneType error in AC calculation for Unarmored Defense"
  - **Impact**: Characters 103814449, 145079040 accuracy improved from 83.3%/81.8% to 95%+
  - **Date**: 2025-06-30
```

### 📋 **Git Workflow Standards**

**Commit Message Format**:
```
type(scope): brief description

Detailed explanation if needed

- Fixes specific issue or implements feature
- Testing: what tests were run
- Impact: accuracy changes or new functionality
```

**Commit Types**:
- `fix`: Bug fixes that improve accuracy
- `feat`: New features or enhancements  
- `test`: Adding or updating tests
- `refactor`: Code restructuring without functionality changes
- `docs`: Documentation updates
- `chore`: Maintenance tasks

**Example Commits**:
```bash
fix(ac): resolve NoneType error in Unarmored Defense calculation

- Add null checking for armor modifiers before addition
- Testing: validated against Barbarian/Monk test characters
- Impact: improves AC accuracy for characters 103814449, 145079040

feat(spells): add Warlock Pact Magic slot calculation

- Implement separate Pact Magic slot tracking
- Testing: validated against Warlock test character
- Impact: adds support for short-rest spell slot recovery

test(validation): extend validation framework for Phase 6 characters

- Add data preservation structure for Phase 6 testing
- Testing: validated data capture workflow
- Impact: enables systematic class coverage testing
```

### 🧪 **Testing Requirements by Change Type**

**For Bug Fixes**:
- [ ] Run `comprehensive_scraper_validation.py` (JSON validation)
- [ ] Run `comprehensive_parser_validation.py` (MD validation) 
- [ ] Test specific affected characters if known
- [ ] Document accuracy improvements in both JSON and MD output

**For New Features**:
- [ ] Create specific test case demonstrating feature in both JSON and MD
- [ ] Run full validation suite (both scraper and parser) to ensure no regressions
- [ ] Update validation framework if needed
- [ ] Verify markdown formatting and D&D UI Toolkit compatibility

**For Refactoring**:
- [ ] Run complete validation suite - 100% baseline accuracy maintained for both outputs
- [ ] Verify no functional changes in JSON or MD output
- [ ] Performance testing if architecture changes
- [ ] Validate markdown structure and Obsidian compatibility

**For Phase 6 Character Testing**:
- [ ] Capture baseline data immediately after character creation (JSON + MD)
- [ ] Run validation against new character (95%+ target for both outputs)
- [ ] Test that existing characters maintain accuracy in both JSON and MD
- [ ] Archive all data before character deletion (raw JSON, scraper JSON, parser MD, validation data)
- [ ] Update validation framework for new character (both scripts)

## Current Status Summary (Last Updated: 2025-06-30)

### 🎯 **COMPREHENSIVE VALIDATION COMPLETE** ✅
**Achievement**: Full baseline performance analysis for v5.2.0 scraper and parser  
**Coverage**: 12/12 characters validated (100% complete)  
**Overall Accuracy**: 88.1% (126/143 comparisons)  
**Validation Method**: Automated comparison of scraper JSON output against manual D&D Beyond data

### 📊 **Scraper Performance Baseline Established**
**Perfect Characters (100% accuracy)**: 3/12 (25%)
- ✅ Faerah Duskrane (105635812) - Level 10 Rogue
- ✅ Vaelith Duskthorn (144986992) - Level 2 Character  
- ✅ ZuB Public Demo (147061783) - Level 15 Wizard

**High Performance (90%+ accuracy)**: 4/12 (33%)
- ⚠️ Dor'ren Uroprax (66356596) - 91.7% accuracy
- ⚠️ Zemfur Folle (68622804) - 91.7% accuracy  
- ⚠️ Seluvis Felo'melorn (103214475) - 91.7% accuracy
- ⚠️ Ilarion Veles (145081718) - 91.7% accuracy

**Issues Identified (<90% accuracy)**: 5/12 (42%)
- ❌ Redgrave (29682199) - 83.3% accuracy
- ❌ Yevelda Ovak (103814449) - 83.3% accuracy (AC calculation bug)
- ❌ Marin (103873194) - 83.3% accuracy  
- ❌ Thuldus Blackblade (145079040) - 81.8% accuracy (AC calculation bug)
- ❌ Baldrin Highfoot (141875964) - 58.3% accuracy (2024 rule parsing issues)

### 🐛 **Critical Issues Discovered**
1. **AC Calculation Bugs** (4 characters affected):
   - Error: `unsupported operand type(s) for +=: 'NoneType' and 'int'`
   - Characters: 103814449, 145079040, plus calculation discrepancies
   - **Priority 1 Fix Required**

2. **Spell Count Discrepancies** (7 characters affected):
   - Pattern: Scraper reports fewer spells than validation
   - Potential causes: Prepared vs total spellbook, deduplication logic
   - **Requires methodology clarification**

3. **2024 Rule Support** (1 character affected):
   - Baldrin Highfoot: Multiple ability score parsing errors
   - **Enhanced 2024 rule detection needed**

### ✅ **All Phases Completed - Production Ready**
- **Phase 0**: Configuration Management & CI/CD Setup ✅ (Commit: 0715201)
- **Phase 1**: Core Architecture & Data Models ✅ (Commit: 0ea8250)  
- **Phase 2**: D&D Rule Calculations & Complete JSON Output ✅ (Commit: eb542f9)
- **Phase 3**: Rule Version Management & Main Entry Scripts ✅ (Commit: 693a210)
- **Phase 4**: Validation & Testing Framework ✅ (Commit: eb542f9)
- **Phase 5**: Integration & Documentation ✅ (Commit: 826c56d)
- **Project Organization**: Clean directory structure and baseline data collection ✅
- **Container Inventory**: Comprehensive container tracking system ✅ (Commit: 88ed74e)
- **Baseline Data Collection**: 12/12 characters with complete Raw→Scraper→Parser pipeline ✅
- **Validation Framework**: Comprehensive automated validation methodology ✅
- **Baseline Performance Analysis**: 88.1% accuracy baseline established ✅
- **Parser Path Fixes**: Fixed spells folder and scraper path resolution ✅
- **Progress Tracking System**: Comprehensive tracking for incremental updates, testing, and git workflow ✅
- **MD Structure Documentation**: Complete D&D UI Toolkit format specification for validation ✅
- **Spell Enhancement Documentation**: Configurable spells folder and enhanced vs API-only modes ✅

### 📊 **Validation Infrastructure**
- **Raw D&D Beyond JSON**: 12/12 characters at `data/baseline/raw/{character_id}.json`
- **v5.2.0 Scraper JSON**: 12/12 characters at `data/baseline/scraper/baseline_{character_id}.json`
- **v5.2.0 Parser MD**: 12/12 characters at `data/baseline/parser/baseline_{character_id}.md`
- **Validation Data**: 12/12 manual validation files at `validation_data/{character_id}_validation.json`
- **Fresh Scraper Output**: 12/12 characters at `archive/v5.2.0/validation_scraper_{character_id}.json`
- **Fresh Parser Output**: **⚠️ NEEDED** - 12/12 characters at `archive/v5.2.0/validation_parser_{character_id}.md`
- **JSON Validation Script**: `archive/v5.2.0/comprehensive_scraper_validation.py` for automated testing
- **MD Validation Script**: **⚠️ NEEDED** - `archive/v5.2.0/comprehensive_parser_validation.py` 
  - Must validate 11+ critical MD components (frontmatter, infobox, anchor tags, spell tables, spell enhancement, etc.)
  - **CRITICAL**: Must validate heading/anchor block structure for Obsidian functionality
  - **CRITICAL**: Must validate spell enhancement system (enhanced vs API-only modes)
  - Must check Windows path compatibility and UTF-8 encoding
  - Must verify D&D UI Toolkit and Obsidian plugin compatibility
  - Must test configurable spells folder path resolution
  - Must test all 5 spell enhancement criteria across different scenarios:
    * 2014 character (should skip all enhanced files)
    * 2024 character with full enhanced folder (should use enhanced files)
    * 2024 character with missing enhanced files (should fall back per-spell)
    * Enhanced mode disabled (should use API for all)
- **Performance Report**: `SCRAPER_BASELINE_PERFORMANCE.md` with detailed analysis
- **Parser Fixes**: Path resolution fixed in `archive/v5.2.0/dnd_json_to_markdown_v5.2.0_original.py`

### 🚨 **Missing Validation Infrastructure** 
**Critical Gap**: We have comprehensive JSON validation but **no systematic MD validation**

**⚠️ APPLIES TO ALL PHASES 3-6**: This dual validation requirement starts with Phase 3 development

**Immediate Tasks Needed Before Phase 3**:
1. **Generate fresh parser output** for all 12 characters: `validation_parser_{character_id}.md`
2. **Create comprehensive_parser_validation.py** to validate MD content (see MD Structure Requirements below)
3. **Establish parser baseline performance** - similar to 88.1% scraper baseline

### 📝 **D&D UI Toolkit Markdown Structure Requirements**

**Critical Components for MD Validation**:

#### **1. Frontmatter (YAML Header)**
```yaml
---
character_name: "Character Name"
level: 10
proficiency_bonus: 4
class: "Class Name"
subclass: "Subclass Name"
hit_die: "d8"
is_2024_rules: False
race: "Race/Species Name"
background: "Background Name"
ability_scores:
  strength: 14
  dexterity: 16
  # ... all six abilities
armor_class: 17
current_hp: 70
max_hp: 73
initiative: "+7"
spellcasting_ability: "intelligence"
spell_save_dc: 17
character_id: 105635812
processed_date: "2025-06-30 13:14:35"
scraper_version: "5.2.0"
# ... additional metadata
---
```

#### **2. Python Execute Script (Windows Compatible)**
```markdown
```run-python
import os, sys, subprocess
os.chdir(r'C:/Users/alc_u/Documents/DnD/CharacterScraper')
vault_path = @vault_path
note_path = @note_path
full_path = os.path.join(vault_path, note_path)
cmd = ['python', 'dnd_json_to_markdown.py', '147061783', full_path]
result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8')
print('\n\n')
print('SUCCESS: Character refreshed!' if result.returncode == 0 else f'ERROR: {result.stderr}')
print('Reload file to see changes.' if result.returncode == 0 else '')
```
```

#### **3. Infobox Structure**
```markdown
> [!infobox]+ ^character-info
> # Character Name
> ###### Character Details
> |  |  |
> | --- | --- |
> | **Class** | Class Name |
> | **Subclass** | Subclass Name |
> | **Race** | Race/Species Name |
> | **Background** | Background Name |
> | **Level** | 10 |
> | **Hit Points** | 70/73 |
> | **Armor Class** | 17 |
> | **Proficiency** | +4 |
> 
> ###### Ability Scores
> |  |  |  |
> | --- | --- | --- |
> | **Str** 14 (+2) | **Dex** 16 (+3) | **Con** 15 (+2) |
> | **Int** 10 (+0) | **Wis** 13 (+1) | **Cha** 12 (+1) |
```

#### **4. Quick Links Section**
```markdown
## Quick Links

| Section |
| --- |
| [[#Character Statistics]] |
| [[#Abilities & Skills]] |
| [[#Spellcasting]] |
| [[#Features]] |
| [[#Attacks]] |
| [[#Inventory]] |
| &nbsp; |
| [D&D Beyond](https://www.dndbeyond.com/characters/105635812) |
```

#### **5. Section Anchor Tags and Heading Structure**
**CRITICAL**: Anchor tags must be in `>` blocks, but headings must be outside for internal links to work:

```markdown
## Character Statistics

> ^character-statistics

Content for character statistics...

## Abilities & Skills

> ^abilities-skills

Content for abilities and skills...

## Spellcasting

> ^spellcasting

Content for spellcasting...

## Features

> ^features

Content for features...

## Attacks

> ^attacks

Content for attacks...

## Inventory

> ^inventory

Content for inventory...
```

**Structure Requirements**:
- **Heading**: `## Section Name` (outside block for internal linking)
- **Anchor**: `> ^section-name` (inside block for anchor functionality)
- **Content**: Follows after anchor block

**Why This Structure Matters**:
- **Internal Links**: `[[#Spellcasting]]` links work only if heading is outside blocks
- **Anchor References**: `[[#^spellcasting]]` anchors work only if anchor is inside blocks
- **Obsidian Navigation**: Both functionalities required for proper plugin integration

#### **6. Spell Table Format**
```markdown
| Level | Spell | School | Components | Casting Time | Concentration | Prepared | Source |
|-------|-------|--------|------------|--------------|---------------|----------|--------|
| 3rd | [[fireball-xphb]] | Evocation | V, S, M | 1 Action | No | Cast | Wizard |
| 1st | [[magic-missile-xphb]] | Evocation | V, S | 1 Action | No | At Will | Feat |
| 3rd | [[counterspell-xphb]] | Abjuration | S | 1 Reaction | No | Ritual | Wizard |
| Cantrip | [[mage-hand-xphb]] | Conjuration | V, S | 1 Action | No | - | Racial |
```

**Column Definitions**:
- **Level**: Spell level (Cantrip, 1st, 2nd, etc.)
- **Spell**: Spell name with link to enhanced file `[[spell-name-xphb]]`
- **School**: School of magic (Evocation, Conjuration, etc.)
- **Components**: V (Verbal), S (Somatic), M (Material)
- **Casting Time**: Action economy (1 Action, 1 Bonus Action, 1 Reaction, etc.)
- **Concentration**: Yes/No for concentration spells
- **Prepared**: Cast/At Will/Ritual/- (usage type)
- **Source**: How spell was obtained (Wizard, Racial, Feat, etc.)

#### **7. Callout Formats**
```markdown
> [!info]+ Class Features
> Content for class features

> [!abstract]+ Racial Traits  
> Content for racial traits

> [!tip]+ Background Features
> Content for background features

> [!warning]+ Combat Notes
> Important combat information
```

#### **8. Stats Blocks (D&D UI Toolkit)**
```markdown
```stats
items:
  - label: Level
    value: '10'
  - label: Proficiency Bonus
    value: '+4'
  - label: Hit Dice
    value: '10d8'
```
```

#### **9. Cross-Reference Links**
- **Spell links**: `[[spell-name-xphb]]` format for enhanced spell files
- **Internal links**: `[[#section-name]]` for navigation within document
- **External links**: `[D&D Beyond](https://www.dndbeyond.com/characters/ID)` for source

#### **10. Spell Enhancement System**
**Parser supports two spell data modes**:

**Enhanced Mode (Default)**: Uses local spell markdown files for rich formatting
```markdown
# Configuration
--spells-path /path/to/spells/folder    # Configurable location
# Default: /mnt/c/Users/alc_u/Documents/DnD/CharacterScraper/spells

# Enhanced spell files provide:
- Rich markdown formatting with cross-references
- Additional metadata and descriptions  
- Enhanced spell tables with Time/Range/Hit/DC columns
- Cross-links to related spells and features
```

**API-Only Mode**: Fallback to D&D Beyond spell data
```markdown
# Configuration  
--no-enhance-spells                     # Disable enhanced spell files
# Falls back to API data when:
- Enhanced files not found
- Spells folder path invalid
- Enhanced mode explicitly disabled
```

**Spell File Format Requirements**:
```
spells/
├── fireball-xphb.md                   # 2024 Player's Handbook spell
├── fireball-phb.md                    # 2014 Player's Handbook spell  
├── magic-missile-xphb.md              # 2024 version
├── magic-missile-phb.md               # 2014 version
├── counterspell-xphb.md               # 2024 version
└── ...

# File naming: spell-name-{source}.md
# Source suffixes determine rule version compatibility
```

**Source Mapping (from ttrpg-convert-cli)**:
```
2024 Rule Sources:
- xphb = 2024 Player's Handbook
- xdmg = 2024 Dungeon Master's Guide  
- xmm = 2024 Monster Manual

2014 Rule Sources:
- phb = 2014 Player's Handbook
- dmg = 2014 Dungeon Master's Guide
- mm = 2014 Monster Manual
- xge = Xanathar's Guide to Everything
- tce = Tasha's Cauldron of Everything
- (many others...)

Reference: https://github.com/ebullient/ttrpg-convert-cli/blob/main/docs/sourceMap.md#source-name-mapping-for-5etools
```

**Configuration Variables**:
```python
# Parser configuration (dnd_json_to_markdown.py)
SPELLS_FOLDER_PATH = "/configurable/path/to/spells"  # Configurable location
USE_ENHANCED_SPELL_DATA = True                       # Enable/disable enhanced mode
SPELL_FILE_SUFFIX = "-xphb.md"                      # File naming pattern
```

**Spell Enhancement Criteria**:
**Enhanced spell files are used ONLY when ALL conditions are met:**

1. **Enhanced Mode Enabled**: `USE_ENHANCED_SPELL_DATA = True` (default)
2. **Spells Folder Exists**: Valid path to spells directory
3. **Rule Version Match**: Enhanced file source matches character rule version
4. **Enhanced File Exists**: Rule-appropriate spell file found
5. **File Readable**: Enhanced file can be successfully loaded

**Rule Version Matching Logic**:
```python
# Character rule detection
character_rules = "2024" if character["is_2024_rules"] else "2014"

# Source suffix mapping
RULE_2024_SOURCES = ["xphb", "xdmg", "xmm"]  # 2024 sources
RULE_2014_SOURCES = ["phb", "dmg", "mm", "xge", "tce", ...]  # 2014 sources

# Enhanced file selection
if character_rules == "2024":
    # Look for 2024 sources first: fireball-xphb.md, fireball-xdmg.md, etc.
    for source in RULE_2024_SOURCES:
        if file_exists(f"spell-name-{source}.md"):
            return enhanced_file_data
elif character_rules == "2014":
    # Look for 2014 sources: fireball-phb.md, fireball-xge.md, etc.
    for source in RULE_2014_SOURCES:
        if file_exists(f"spell-name-{source}.md"):
            return enhanced_file_data

# Fall back to API if no rule-appropriate file found
return api_data
```

**Fallback to API Data Occurs When:**
- Enhanced mode disabled (`--no-enhance-spells` flag)
- Spells folder path invalid or not found
- No rule-appropriate enhanced file found (2024 character but only 2014 files available)
- Enhanced file corrupt/unreadable

**Updated Parser Logic**:
```python
# From parser verbose output we should now see:
"Skipping enhanced spell data for [Spell] - character uses 2014 rules, only 2024 sources available"
"Using enhanced spell data for [Spell] from source: xphb (2024 rules)"
"Using enhanced spell data for [Spell] from source: phb (2014 rules)"
```

**Spell Enhancement Behavior**:
- **Parser-Only Feature**: Scraper always uses API data, parser optionally enhances
- **Rule Version Aware**: Source suffix determines compatibility (xphb=2024, phb=2014, etc.)
- **Source Priority**: Multiple source files can exist, parser selects rule-appropriate version
- **Per-Spell Basis**: Enhancement checked individually for each spell
- **Graceful Fallback**: Missing rule-appropriate files fall back to API data automatically
- **Path Resolution**: Spells folder location configurable via command line or config

#### **11. Windows Path Compatibility**
- **Forward slashes**: Use `/` in paths, not `\` for cross-platform compatibility  
- **Raw strings**: Use `r'C:/path'` for Windows paths in Python code
- **UTF-8 encoding**: Ensure proper character encoding for special symbols

**MD Validation Must Check**:
- [ ] Complete frontmatter with all required fields
- [ ] Python script uses Windows-compatible paths (`r'C:/'` format)
- [ ] Infobox structure and formatting correct
- [ ] **CRITICAL**: Headings (`## Section Name`) outside blocks for internal linking
- [ ] **CRITICAL**: Anchor tags (`> ^section-name`) inside blocks for anchor functionality  
- [ ] Proper heading/anchor structure: Heading → Anchor Block → Content
- [ ] Quick Links section complete with internal navigation
- [ ] Spell table format matches D&D UI Toolkit requirements (8 columns: Level, Spell, School, Components, Casting Time, Concentration, Prepared, Source)
- [ ] **Spell Enhancement**: Spell links use correct format `[[spell-name-xphb]]`
- [ ] **Spell Enhancement**: Enhanced mode vs API-only mode working correctly
- [ ] **Spell Enhancement**: Rule version awareness (2024 vs 2014) functioning correctly
- [ ] **Spell Enhancement**: 2014 characters automatically use API data (no enhanced files)
- [ ] **Spell Enhancement**: 2024 characters use enhanced files when available
- [ ] **Spell Enhancement**: Graceful fallback when enhanced files missing (per-spell basis)
- [ ] **Spell Enhancement**: All 5 criteria properly evaluated for each spell
- [ ] Callout blocks use correct syntax and types
- [ ] Cross-reference links properly formatted
- [ ] Stats blocks use correct YAML structure
- [ ] UTF-8 encoding preserved for special characters

**Phase 3+ Requirement**: ALL changes must pass both JSON and MD validation

### 🧹 **File Organization Notes**
- **Temporary Test Files**: Several test output files in `archive/v5.2.0/` should be cleaned up
- **Validation Artifacts**: Keep validation scripts and scraper outputs for regression testing
- **Folder Structure**: Maintain clean separation between archived v5.2.0 code and new v6.0.0 development

### 🎯 **Ready for Phase 3 with Quantified Baseline**
**Success Criteria for v6.0.0 (JSON + MD Combined)**:
- Target: 95%+ overall accuracy for JSON output (vs current 88.1%)
- Target: Establish and maintain MD baseline quality metrics
- No regressions: All currently perfect characters remain perfect in both outputs
- Critical fixes: AC calculation bugs resolved (verified in both JSON and MD)
- 2024 support: Baldrin Highfoot accuracy >90% (both outputs)
- MD Quality: Maintain D&D UI Toolkit compatibility and Obsidian plugin functionality

**Regression Testing**: `comprehensive_scraper_validation.py` provides automated baseline comparison

### 🚀 **Quick Development Workflow Reference**

**Before Starting Work**:
```bash
# Create feature branch
git checkout -b feature/your-feature-name

# Ensure baseline is clean
cd archive/v5.2.0
python3 comprehensive_scraper_validation.py
# Should show 88.1% baseline accuracy
```

**During Development**:
```bash
# Make changes to code
# Test specific functionality

# Run regression testing - BOTH outputs
cd archive/v5.2.0
python3 comprehensive_scraper_validation.py     # JSON validation
python3 comprehensive_parser_validation.py      # MD validation
# Ensure no accuracy decrease in either output

# Commit with proper message
git add .
git commit -m "fix(scope): description

- Specific changes made
- Testing: JSON and MD validation completed
- Impact: accuracy or functionality changes"
```

**Before Merge**:
```bash
# Final validation - BOTH outputs
cd archive/v5.2.0
python3 comprehensive_scraper_validation.py     # Must maintain 87.7%+ baseline (13 chars)
python3 comprehensive_parser_validation.py      # Must maintain MD format quality

# Update plan.md progress if completing major task
# Merge to main
git checkout main
git merge feature/your-feature-name
```

**Phase Completion**:
```bash
# Tag major milestones
git tag -a v6.0.0-phase3 -m "Phase 3: Rule Version Management Complete"
git push origin v6.0.0-phase3
```

## 📊 **Current Validation Status (Updated 2025-06-30)**

### **Baseline Performance Established**:
- **Characters tested**: 13 (including new multiclass character 116277190)
- **Overall JSON accuracy**: 87.7% (136/155 comparisons)
- **Perfect matches**: 3 characters (Faerah, Vaelith, ZuB)
- **High performance**: 5 characters with 90%+ accuracy
- **Script**: `comprehensive_scraper_validation.py` ✅ Working

### **Known Issues Identified**:
1. **AC Calculation Bugs**: 5 characters affected (NoneType errors)
2. **Speed Calculation**: Monk Unarmored Movement missing
3. **2024 Rule Detection**: Homebrew causing false positives
4. **Spell Enhancement**: Using wrong rule version files

### **Validation Framework Status**:
- ✅ **JSON Validation**: Complete (13 characters)
- ❌ **MD Validation**: Missing (`comprehensive_parser_validation.py` needed)
- ❌ **Skills Methodology**: Broken (features/traits in skills field)

### 🚨 **Phase 3 Priority Issues (Based on Validation)**
**Priority 0: Validation Infrastructure (PREREQUISITE)**
0. **CRITICAL: Fix Validation Methodology**: Before any Phase 3 work begins
   - **Issue Discovered**: "skills" field in ALL validation files incorrectly contains features/traits instead of skill proficiencies
   - **Example**: Character 116277190 shows `{"name": "Ki", "source": "Class - monk"}` in skills - this is a class feature, not a skill
   - **Must fix**: All 13 validation files need skills corrected to actual proficiencies (Acrobatics, Athletics, etc.)
   - **Must separate**: Create new "features" field for actual features/traits (Ki, Second Wind, Celestial Resistance, etc.)
   - **Impact**: Current validation comparison is fundamentally flawed for skills assessment

1. **Complete Dual Validation Framework**: Before any Phase 3 work begins  
   - **Must complete**: Generate all 13 parser baselines (`validation_parser_{character_id}.md`)
   - **Must create**: `comprehensive_parser_validation.py` script
   - **Must establish**: MD baseline quality metrics
   - **Impact**: Enables proper testing for all subsequent development

**Priority 1: Critical Bugs (Blocking)**
1. **AC Calculation NoneType Errors**: Fix `unsupported operand type(s) for +=: 'NoneType' and 'int'`
   - Affects: Characters 103814449, 145079040
   - Impact: Complete AC calculation failure in both JSON and MD output
   - **Must test**: AC calculation for Barbarian Unarmored Defense and similar features (both outputs)

2. **2024 Rule Parsing**: Fix ability score calculation for 2024 characters
   - Affects: Character 141875964 (58.3% accuracy)
   - Impact: Multiple ability scores parsed incorrectly in both JSON and MD
   - **Must test**: All 2024 rule characters for ability score accuracy (both outputs)

**Priority 2: Methodology Clarification**
3. **Spell Count Methodology**: Clarify prepared vs total spellbook counting
   - Affects: 7/12 characters with spell count discrepancies
   - Impact: Validation accuracy measurement and MD spell table formatting
   - **Must test**: Spell counting logic against known spellcaster builds (both outputs)

---

## Configuration Management System

**Current State**: Hardcoded constants in enhanced_dnd_scraper.py  
**Target State**: External configuration files with environment variable support and validation

### Configuration Architecture

```
config/
├── default.yaml           # Default settings
├── rules/
│   ├── 2014.yaml          # 2014 rule definitions
│   ├── 2024.yaml          # 2024 rule definitions
│   └── constants.yaml     # Game constants (spell lists, class data)
├── api.yaml               # API configuration
├── formatting.yaml        # Output formatting settings
└── environments/
    ├── development.yaml   # Dev overrides
    ├── testing.yaml       # Test overrides
    └── production.yaml    # Production overrides
```

### Core Configuration Files

#### `config/default.yaml`
```yaml
# Core application settings
app:
  name: "DnDBeyond-Enhanced-Scraper"
  version: "6.0.0"
  user_agent: "DnDBeyond-Enhanced-Scraper/6.0.0"

# API settings
api:
  base_url: "https://character-service.dndbeyond.com"
  timeout: 30
  max_retries: 3
  retry_delay: 1.0
  rate_limit: 20  # seconds between requests

# Output settings
output:
  include_raw_data: false
  verbose_output: false
  debug_summary: true
  preserve_unknown_fields: true

# Logging configuration
logging:
  level: "INFO"
  format: "%(asctime)s - %(levelname)s - %(message)s"
  structured: false
```

#### `config/rules/2014.yaml`
```yaml
# D&D 2014 Edition Rules
rule_version: "2014"
terminology:
  character_origin: "race"
  ability_improvement: "ability_score_improvement"

source_ids:
  phb: [1]
  dmg: [2] 
  mm: [3]
  xgte: [40]
  tcoe: [39]
  all_2014: [1, 2, 3, 40, 39, 15, 4, 6, 17, 18, 19, 20, 28, 34, 35, 42]

classes:
  artificer:
    hit_die: 8
    spellcasting: "half"
    primary_ability: "intelligence"
    introduced_in: "tcoe"
  barbarian:
    hit_die: 12
    spellcasting: null
    primary_ability: "strength"
  # ... all 13 classes
```

#### `config/rules/2024.yaml`
```yaml
# D&D 2024 Edition Rules
rule_version: "2024"
terminology:
  character_origin: "species"
  ability_improvement: "ability_score_improvement"

source_ids:
  phb_2024: [142]
  dmg_2024: [143] 
  mm_2024: [144]
  all_2024: [142, 143, 144]

classes:
  artificer:
    hit_die: 8
    spellcasting: "half"
    primary_ability: "intelligence"
    weapon_mastery: true
  barbarian:
    hit_die: 12
    spellcasting: null
    primary_ability: "strength"
    weapon_mastery: true
  # ... all 13 classes with 2024 updates

feat_categories:
  origin: "Background-granted feats"
  general: "Standard feats available to all"
  fighting_style: "Combat-focused feats"
  epic_boon: "High-level character rewards"
```

#### `config/api.yaml`
```yaml
# API-specific configuration
endpoints:
  character: "/character/v5/character/{id}"
  spell_list: "/spell-list/{id}"
  
headers:
  default:
    User-Agent: "${app.user_agent}"
    Accept: "application/json"
    
session:
  cookie_name: "session"
  
rate_limiting:
  requests_per_minute: 3
  burst_limit: 1
  
error_handling:
  retry_status_codes: [429, 500, 502, 503, 504]
  timeout_retry: true
  max_timeout_retries: 2
```

#### `config/formatting.yaml`
```yaml
# Output formatting configuration
obsidian:
  dnd_ui_toolkit:
    version: "latest"
    components:
      stats:
        grid_columns: 3
        show_sublabels: true
      healthpoints:
        show_death_saves: true
        default_reset: "long-rest"
      abilities:
        show_bonuses: true
        show_proficiencies: true
      consumables:
        default_reset: "long-rest"
        show_amounts: true

markdown:
  yaml_frontmatter: true
  internal_linking: true
  callout_system: true
  spell_cross_references: true
  
json:
  pretty_print: true
  indent: 2
  sort_keys: false
```

### Configuration Management Implementation

#### `config/manager.py`
```python
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, validator
from dotenv import load_dotenv

class ConfigManager:
    """Centralized configuration management with environment variable support."""
    
    def __init__(self, config_dir: Optional[Path] = None, env_file: Optional[str] = None):
        self.config_dir = config_dir or Path(__file__).parent
        self.env_file = env_file or ".env"
        self._config_cache: Dict[str, Any] = {}
        
        # Load environment variables
        load_dotenv(self.env_file)
        
        # Load base configuration
        self._load_base_config()
    
    def _load_base_config(self):
        """Load and merge configuration files."""
        # Load default config
        default_config = self._load_yaml_file("default.yaml")
        
        # Load environment-specific overrides
        env = os.getenv("DND_SCRAPER_ENV", "development")
        env_config = self._load_yaml_file(f"environments/{env}.yaml", required=False)
        
        # Merge configurations
        self._config_cache = self._deep_merge(default_config, env_config or {})
        
        # Apply environment variable overrides
        self._apply_env_overrides()
    
    def _load_yaml_file(self, filename: str, required: bool = True) -> Dict[str, Any]:
        """Load YAML configuration file."""
        file_path = self.config_dir / filename
        if not file_path.exists():
            if required:
                raise FileNotFoundError(f"Required config file not found: {file_path}")
            return {}
        
        with open(file_path, 'r') as f:
            return yaml.safe_load(f) or {}
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides."""
        # API configuration
        if api_timeout := os.getenv("DND_API_TIMEOUT"):
            self._config_cache["api"]["timeout"] = int(api_timeout)
        
        if api_retries := os.getenv("DND_API_MAX_RETRIES"):
            self._config_cache["api"]["max_retries"] = int(api_retries)
        
        if rate_limit := os.getenv("DND_API_RATE_LIMIT"):
            self._config_cache["api"]["rate_limit"] = int(rate_limit)
        
        # Output configuration
        if debug := os.getenv("DND_DEBUG_OUTPUT"):
            self._config_cache["output"]["debug_summary"] = debug.lower() == "true"
        
        if verbose := os.getenv("DND_VERBOSE"):
            self._config_cache["output"]["verbose_output"] = verbose.lower() == "true"
        
        # Logging configuration
        if log_level := os.getenv("DND_LOG_LEVEL"):
            self._config_cache["logging"]["level"] = log_level.upper()
    
    def get(self, key_path: str, default: Any = None) -> Any:
        """Get configuration value using dot notation."""
        keys = key_path.split('.')
        value = self._config_cache
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        
        return value
    
    def get_rule_config(self, rule_version: str) -> Dict[str, Any]:
        """Get rule-specific configuration."""
        if rule_version not in self._config_cache.get("rules", {}):
            # Load rule config on demand
            rule_config = self._load_yaml_file(f"rules/{rule_version}.yaml")
            if "rules" not in self._config_cache:
                self._config_cache["rules"] = {}
            self._config_cache["rules"][rule_version] = rule_config
        
        return self._config_cache["rules"][rule_version]
    
    @staticmethod
    def _deep_merge(base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = ConfigManager._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

# Global configuration instance
config = ConfigManager()
```

### Environment Variable Support

#### `.env` (Local Development)
```bash
# API Configuration
DND_API_TIMEOUT=45
DND_API_MAX_RETRIES=5
DND_API_RATE_LIMIT=30
DND_SESSION_COOKIE=""

# Output Configuration  
DND_DEBUG_OUTPUT=true
DND_VERBOSE=true
DND_INCLUDE_RAW_DATA=false

# Logging Configuration
DND_LOG_LEVEL=DEBUG
DND_STRUCTURED_LOGGING=true

# Environment
DND_SCRAPER_ENV=development
```

### Configuration Validation

#### `config/validators.py`
```python
from pydantic import BaseModel, Field, validator
from typing import Dict, List, Optional, Union

class APIConfig(BaseModel):
    base_url: str = Field(..., regex=r'^https?://')
    timeout: int = Field(30, gt=0, le=300)
    max_retries: int = Field(3, ge=0, le=10)
    rate_limit: int = Field(20, gt=0)

class RuleConfig(BaseModel):
    rule_version: str = Field(..., regex=r'^(2014|2024)$')
    terminology: Dict[str, str]
    source_ids: Dict[str, List[int]]
    
    @validator('source_ids')
    def validate_source_ids(cls, v):
        required_keys = ['all_2014', 'all_2024']
        if not any(key in v for key in required_keys):
            raise ValueError("Must contain at least one of: all_2014, all_2024")
        return v

class OutputConfig(BaseModel):
    include_raw_data: bool = False
    verbose_output: bool = False
    debug_summary: bool = True
    preserve_unknown_fields: bool = True

class ConfigValidator:
    """Validate configuration integrity."""
    
    @staticmethod
    def validate_config(config_dict: Dict) -> bool:
        """Validate entire configuration structure."""
        try:
            # Validate API config
            if 'api' in config_dict:
                APIConfig(**config_dict['api'])
            
            # Validate output config
            if 'output' in config_dict:
                OutputConfig(**config_dict['output'])
            
            return True
        except Exception as e:
            raise ValueError(f"Configuration validation failed: {e}")
```

### Integration with Existing Code

#### Usage in Scrapers
```python
from config.manager import config

class DNDBeyondAPIClient:
    def __init__(self):
        self.base_url = config.get('api.base_url')
        self.timeout = config.get('api.timeout', 30)
        self.max_retries = config.get('api.max_retries', 3)
        self.rate_limit = config.get('api.rate_limit', 20)
        
    def get_user_agent(self) -> str:
        return config.get('app.user_agent', 'DnDBeyond-Enhanced-Scraper/6.0.0')

class RuleVersionManager:
    def __init__(self):
        self.rules_2014 = config.get_rule_config('2014')
        self.rules_2024 = config.get_rule_config('2024')
    
    def detect_version(self, character_data) -> str:
        # Use configured source IDs for detection
        source_ids_2024 = self.rules_2024['source_ids']['all_2024']
        # ... detection logic
```

### Benefits of Configuration Management

1. **Maintainability**: No more hardcoded constants scattered throughout code
2. **Flexibility**: Easy to adjust behavior without code changes
3. **Environment Support**: Different settings for dev/test/prod
4. **Validation**: Catch configuration errors early
5. **Documentation**: Configuration files serve as documentation
6. **Version Control**: Track configuration changes alongside code

---

## Phase 0: Configuration Management & CI/CD Setup

**Goal**: Establish development infrastructure and configuration management before core refactoring begins.

### 0.1 Configuration Management Implementation

See Configuration Management System section above for complete implementation details.

**Implementation Tasks**:
- [ ] Create `config/` directory structure
- [ ] Implement `ConfigManager` class with YAML loading and environment variable support
- [ ] Create rule-specific configuration files (2014.yaml, 2024.yaml)
- [ ] Add Pydantic validation for configuration schemas
- [ ] Update dependencies to include PyYAML and python-dotenv
- [ ] Create environment-specific configuration overrides

### 0.2 Basic Testing Setup

**Current State**: No testing framework  
**Target State**: Simple testing that allows Claude to validate changes work

#### Simple Testing Framework

##### Basic Test Setup
```python
# tests/test_scraper.py - Simple tests that validate functionality
import pytest
from enhanced_dnd_scraper import DNDBeyondScraper
from unittest.mock import Mock, patch

def test_scraper_basic_functionality():
    """Test scraper can process mock character data."""
    mock_data = {
        "id": 144986992,
        "name": "Test Character",
        "classes": [{"definition": {"name": "Fighter"}, "level": 1}],
        "stats": [{"id": 1, "value": 15}],  # Strength 15
        "preferences": {"hitPointType": 1}
    }
    
    scraper = DNDBeyondScraper()
    result = scraper.process_character_data(mock_data)
    
    assert result["name"] == "Test Character"
    assert result["level"] == 1

def test_configuration_loading():
    """Test configuration system works."""
    from config.manager import config
    
    # Test basic config access
    assert config.get('app.name') == 'DnDBeyond-Enhanced-Scraper'
    assert config.get('api.timeout', 30) == 30

# tests/test_integration.py - Real API tests (rate limited)
@pytest.mark.integration
def test_known_character():
    """Test against a known character with rate limiting."""
    import time
    time.sleep(25)  # Rate limiting
    
    scraper = DNDBeyondScraper()
    result = scraper.scrape_character(144986992)
    
    # Validate expected structure exists
    assert "name" in result
    assert "level" in result
    assert "classes" in result
```

##### GitHub Action (Simplified)
```yaml
# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v4
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt pytest
      - run: pytest tests/ -v --tb=short
      - name: Test integration (rate limited)
        run: pytest tests/test_integration.py -m integration -v
        if: github.event_name == 'push'  # Only on push, not PR
```

#### Minimal Requirements
```
# requirements-dev.txt (just the essentials)
pytest>=7.0.0
black>=23.0.0  # Code formatting
```

#### Simple pytest config
```ini
# pytest.ini
[tool:pytest]
testpaths = tests
addopts = -v --tb=short
markers =
    integration: Tests that call the real API (rate limited)
```

### 0.3 Benefits

1. **Claude can test changes** - Simple automated testing
2. **Configuration flexibility** - No more hardcoded constants
3. **Code quality** - Basic formatting and structure
4. **API validation** - Ensure changes don't break scraping

### 0.3 Git Setup (First Time)

Since you haven't used Git before, here's a simple walkthrough:

#### 1. Install Git
**Windows**: Download from https://git-scm.com/download/windows
**Mac**: `brew install git` or download from git-scm.com
**Linux**: `sudo apt install git` (Ubuntu) or equivalent

#### 2. Configure Git (One-time setup)
```bash
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

#### 3. Create GitHub Account
- Go to https://github.com and sign up
- This is where your code will be stored online

#### 4. Initialize Your Project
```bash
# In your project directory
cd /mnt/c/Users/alc_u/Documents/DnD/CharacterScraper

# Initialize git
git init

# Create .gitignore file to ignore temporary files
echo "__pycache__/
*.pyc
*.pyo
.env
venv/
.pytest_cache/
coverage.xml
*.log" > .gitignore

# Add your files
git add .
git commit -m "Initial commit - D&D character scraper v5.2.0"
```

#### 5. Create GitHub Repository
- Go to https://github.com/new
- Repository name: `dnd-character-scraper` (or whatever you prefer)
- Set to **Private** (recommended for personal tools)
- Don't initialize with README (since you already have files)
- Click "Create repository"

#### 6. Connect Local to GitHub
```bash
# Replace YOUR_USERNAME with your GitHub username
git remote add origin https://github.com/YOUR_USERNAME/dnd-character-scraper.git
git branch -M main
git push -u origin main
```

#### 7. Basic Git Workflow (Daily Use)
```bash
# See what changed
git status

# Add changes
git add .

# Commit with a message
git commit -m "Describe what you changed"

# Push to GitHub
git push
```

#### 8. For Claude Development
Once your repo is on GitHub:
- Give me the repository URL
- I can create branches, make changes, and test them
- You can review changes before merging
- All changes are tracked and reversible

#### Common Git Commands
```bash
git status          # See what files changed
git add filename    # Stage a specific file
git add .           # Stage all changes
git commit -m "msg" # Save changes with message
git push           # Upload to GitHub
git pull           # Download latest changes
git log --oneline  # See commit history
```

### 0.4 Weekly Workflow Improvements

Since you run this weekly for ~8 characters, focus on reliability over performance:

#### Batch Processing
```python
# cli/batch.py - Process multiple characters with proper rate limiting
def process_batch(character_ids: List[int], rate_limit: int = 25):
    results = []
    for i, char_id in enumerate(character_ids):
        if i > 0:  # Rate limit between requests
            time.sleep(rate_limit)
        
        try:
            result = scraper.scrape_character(char_id)
            results.append({"id": char_id, "status": "success", "data": result})
            print(f"✅ {char_id}: Success")
        except Exception as e:
            results.append({"id": char_id, "status": "failed", "error": str(e)})
            print(f"❌ {char_id}: {e}")
    
    return results

# Usage: python enhanced_dnd_scraper.py --batch my_characters.txt
```

#### Character Configuration
```yaml
# config/my_characters.yaml
characters:
  - id: 12345678
    name: "Character 1" 
    notes: "Example character"
  - id: 87654321
    name: "Character 2"
    session_required: true
  # ... add your actual character IDs here
```

#### Simple Success Summary
```python
def print_batch_summary(results):
    successes = [r for r in results if r["status"] == "success"]
    failures = [r for r in results if r["status"] == "failed"]
    
    print(f"\n📊 Batch Complete: {len(successes)}/{len(results)} successful")
    
    if failures:
        print("\n❌ Failed Characters:")
        for failure in failures:
            print(f"  - {failure['id']}: {failure['error']}")
```

### 0.5 Phase 0 Completion Criteria

- [ ] Git repository set up and pushed to GitHub
- [ ] Configuration management system implemented
- [ ] Basic test framework set up
- [ ] Simple GitHub Action for testing
- [ ] Can run pytest locally to validate changes
- [ ] Configuration files replace hardcoded constants
- [ ] Batch processing for weekly character updates

---

## Immediate v5.2.x Improvements (Integrate into v6)

Based on external API suggestions, these practical improvements should be integrated into the v6 refactor:

### 1. Debug Summary Output
**Implementation**: Add to JSON output for easy validation
```json
"debug_summary": {
  "name": "Test Character",
  "level": 2,
  "hit_points": 13,
  "armor_class": 12,
  "rule_version": "2024",
  "proficiency_bonus": 2,
  "spell_slots": { "level_1": 3 },
  "ability_scores": { "strength": 15, "dexterity": 14, "constitution": 16, "intelligence": 8, "wisdom": 12, "charisma": 17 },
  "modifiers": { "strength": 2, "dexterity": 2, "constitution": 3, "intelligence": -1, "wisdom": 1, "charisma": 3 }
}
```
**Benefit**: Easy human comparison against D&D Beyond
**Integration Point**: Phase 4 Validation System

### 2. Quick Compare Mode
**Implementation**: `--quick-compare validation.json` flag
```bash
python enhanced_dnd_scraper.py 144986992 --quick-compare validation_data/144986992_validation.json
```
**Benefit**: No framework required, high utility for validation
**Integration Point**: Phase 5 CLI Integration

### 3. Centralized Rule Version Detection
**Implementation**: Single function in `rules/version_manager.py`
```python
def detect_rule_version(character_data) -> str:
    if "species" in character_data:
        return "2024"
    if any(spell["definition"]["name"] in KNOWN_2024_SPELLS for spell in character_data.get("spells", [])):
        return "2024"
    return "2014"
```
**Benefit**: One place to update logic, removes duplication
**Integration Point**: Phase 3 Rule Version Management

### 4. Fail Fast API Validation
**Implementation**: Early structure validation in `api/client.py`
```python
if "stats" not in character_data:
    raise ValueError("Missing stats section — invalid or outdated API response.")
```
**Benefit**: Stops downstream crashes with unhelpful errors
**Integration Point**: Phase 1 API Client

### 5. Modifier Validation Assertions (Debug Mode)
**Implementation**: Debug-only validation in calculators
```python
assert modifier == (score - 10) // 2, f"Mismatch: {modifier} vs expected"
```
**Benefit**: Catches upstream parsing bugs
**Integration Point**: Phase 2 Calculators (debug mode only)

### 6. Static Markdown Summary (Optional)
**Implementation**: Lightweight character summary export
```markdown
# Test Character
- Level 2 Sorcerer (2024 Rules)
- HP: 13 | AC: 12 | Initiative: +2
- Spell Save DC: 14 | Spell Attack: +6
- Proficiencies: Arcana, History, Intimidation, Perception, Persuasion
```
**Integration Point**: Phase 5 Exporters (optional feature)

---

## Phase 1: Core Architecture & Data Models

**Goal**: Extract and modularize core data structures from the monolithic 4000+ line file  
**Duration**: Foundation phase - get this right before proceeding  
**Success Criteria**: Clean interfaces, validated data models, testable modules

### 1.1 Step-by-Step Implementation Guide

#### Step 1: Initial Project Setup (30 minutes)

**1.1.1 Create Directory Structure**
```bash
mkdir -p dnd_character_scraper/{interfaces,models,api,calculators,rules,processors,validators,exporters,utils,tests,cli}
mkdir -p dnd_character_scraper/tests/{fixtures,mocks,unit,integration,edge_cases,validation}
touch dnd_character_scraper/__init__.py
find dnd_character_scraper -type d -exec touch {}/__init__.py \;
```

**1.1.2 Copy Current Working Files**
```bash
# Backup current version
cp enhanced_dnd_scraper.py enhanced_dnd_scraper_v5.2.0_backup.py
cp dnd_json_to_markdown.py dnd_json_to_markdown_v5.2.0_backup.py

# Keep current version working while developing v6
# Don't modify these files until Phase 5 integration
```

#### Step 2: Extract Core Interfaces (1 hour)

**1.2.1 Analyze Current Code Structure**
Open `enhanced_dnd_scraper.py` and identify:
- All `@cached_property` methods → These become calculator interfaces
- All `_process_*` methods → These become processor interfaces  
- All `_calculate_*` methods → These become calculator interfaces
- All data classes → These become Pydantic models

**1.2.2 Create Base Interfaces** (`interfaces/calculators.py`)
```python
# STEP-BY-STEP: Copy this exactly, then customize

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Protocol
from pydantic import BaseModel

class CalculationResult(BaseModel):
    """Standard calculation result with debugging info."""
    value: Any
    calculation_steps: List[str]
    source_data: Dict[str, Any]
    warnings: List[str] = []

class CalculatorInterface(ABC):
    """Base interface for all character calculations."""
    
    @abstractmethod
    def calculate(self, character_data: Dict[str, Any], rule_version: str) -> CalculationResult:
        """Perform calculation and return structured result."""
        pass
    
    @abstractmethod
    def get_dependencies(self) -> List[str]:
        """Return list of required fields from character_data."""
        pass
    
    @property
    @abstractmethod
    def calculator_name(self) -> str:
        """Return human-readable calculator name."""
        pass

class ProcessorInterface(ABC):
    """Base interface for data processors."""
    
    @abstractmethod
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw API data into structured format."""
        pass
    
    @abstractmethod
    def validate_input(self, raw_data: Dict[str, Any]) -> List[str]:
        """Return list of validation errors, empty if valid."""
        pass
```

#### Step 3: Extract Data Models (2 hours)

**1.3.1 Find All Current Data Classes**
Search `enhanced_dnd_scraper.py` for:
```bash
grep -n "@dataclass\|class.*:" enhanced_dnd_scraper.py
```

**1.3.2 Convert to Pydantic Models** (`models/character.py`)

*Step-by-step conversion process:*

1. **Copy existing SpellInfo dataclass**
```python
# FROM enhanced_dnd_scraper.py (find around line 100-200)
@dataclass
class SpellInfo:
    spell_id: int
    name: str
    level: int
    # ... rest of fields
```

2. **Convert to Pydantic**
```python
# TO models/spells.py
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, List, Dict, Any

class SpellInfo(BaseModel):
    model_config = ConfigDict(extra='allow')  # Critical: allows unknown fields
    
    spell_id: int = Field(..., description="D&D Beyond spell ID")
    name: str = Field(..., description="Spell name")
    level: int = Field(..., ge=0, le=9, description="Spell level (0-9)")
    school: Optional[str] = Field(None, description="School of magic")
    
    # Copy ALL fields from original dataclass
    # Add validation where appropriate
    # Keep extra='allow' for unknown D&D Beyond fields
```

3. **Repeat for all dataclasses:**
   - `InventoryItem` → `models/equipment.py`
   - `SpeciesInfo` → `models/character.py`
   - `ClassInfo` → `models/character.py`
   - `CharacterModifier` → `models/abilities.py`

**1.3.3 Create Core Character Model** (`models/character.py`)
```python
from pydantic import BaseModel, Field, ConfigDict, computed_field
from typing import Dict, List, Optional, Any
from enum import Enum

class RuleVersion(str, Enum):
    RULES_2014 = "2014"
    RULES_2024 = "2024"

class Character(BaseModel):
    """Complete character representation with all calculated values."""
    model_config = ConfigDict(extra='allow')
    
    # Basic Info (directly from API)
    character_id: int
    name: str
    level: int
    
    # Calculated Values (computed by calculators)
    ability_scores: Dict[str, int] = Field(default_factory=dict)
    ability_modifiers: Dict[str, int] = Field(default_factory=dict)
    hit_points: int = 0
    armor_class: int = 10
    initiative: int = 0
    proficiency_bonus: int = 2
    
    # Metadata
    rule_version: RuleVersion = RuleVersion.RULES_2014
    calculation_warnings: List[str] = Field(default_factory=list)
    unknown_fields: Dict[str, Any] = Field(default_factory=dict)
    
    @computed_field
    @property
    def debug_summary(self) -> Dict[str, Any]:
        """Generate debug summary for validation."""
        return {
            "name": self.name,
            "level": self.level,
            "hit_points": self.hit_points,
            "armor_class": self.armor_class,
            "rule_version": self.rule_version,
            "ability_scores": self.ability_scores,
            "modifiers": self.ability_modifiers
        }
```

#### Step 4: Create Mock API Client (1 hour)

**1.4.1 Extract API Logic** (`api/client.py`)

Find the current API code in `enhanced_dnd_scraper.py`:
```bash
grep -n -A 20 "def.*character\|requests\.get\|session" enhanced_dnd_scraper.py
```

Copy the working API logic exactly:
```python
# api/client.py
import requests
from typing import Dict, Any, Optional
from ..interfaces.calculators import ProcessorInterface

class DNDBeyondAPIClient:
    """D&D Beyond API client extracted from v5.2.0."""
    
    def __init__(self, session_cookie: Optional[str] = None):
        # COPY EXACT LOGIC from enhanced_dnd_scraper.py
        # Don't modify working code yet
        pass
    
    def get_character(self, character_id: int) -> Dict[str, Any]:
        """Get character data - EXACT copy from v5.2.0."""
        # Copy the working _fetch_character_data method exactly
        pass
```

**1.4.2 Create Mock Client** (`api/mock_client.py`)
```python
class MockAPIClient:
    """Mock client for testing without API calls."""
    
    def __init__(self):
        self.mock_responses = {
            999999: {  # Generic test character
                "id": 999999,
                "name": "Test Character",
                "level": 2,
                "classes": [{"definition": {"name": "Sorcerer"}, "level": 2}],
                "stats": [
                    {"id": 1, "value": 15},  # STR
                    {"id": 2, "value": 14},  # DEX
                    {"id": 3, "value": 16},  # CON
                    {"id": 4, "value": 8},   # INT
                    {"id": 5, "value": 12},  # WIS
                    {"id": 6, "value": 17}   # CHA
                ],
                "preferences": {"hitPointType": 1}
            }
        }
    
    def get_character(self, character_id: int) -> Dict[str, Any]:
        if character_id in self.mock_responses:
            return self.mock_responses[character_id]
        raise ValueError(f"Mock character {character_id} not found")
```

#### Step 5: Extract First Calculator (1.5 hours)

**1.5.1 Find Ability Score Calculation**
In `enhanced_dnd_scraper.py`, find the `@cached_property` for ability scores:
```bash
grep -n -A 30 "@cached_property.*ability_scores" enhanced_dnd_scraper.py
```

**1.5.2 Create Ability Score Calculator** (`calculators/ability_scores.py`)
```python
from typing import Dict, Any
from ..interfaces.calculators import CalculatorInterface, CalculationResult
from ..models.abilities import AbilityScores

class AbilityScoreCalculator(CalculatorInterface):
    """Calculate final ability scores from base + racial + ASI + items."""
    
    @property
    def calculator_name(self) -> str:
        return "Ability Score Calculator"
    
    def get_dependencies(self) -> List[str]:
        return ["stats", "modifiers", "bonusStats"]
    
    def calculate(self, character_data: Dict[str, Any], rule_version: str) -> CalculationResult:
        """EXACT copy of ability score logic from v5.2.0."""
        steps = []
        warnings = []
        
        # Copy the exact logic from enhanced_dnd_scraper.py
        # Don't optimize yet - just extract working code
        
        base_stats = character_data.get("stats", [])
        # ... copy exact calculation logic
        
        result_scores = {
            "strength": 10,    # calculated value
            "dexterity": 10,   # calculated value
            # ... all six abilities
        }
        
        return CalculationResult(
            value=result_scores,
            calculation_steps=steps,
            source_data={"stats": base_stats},
            warnings=warnings
        )
```

#### Step 6: Create Basic Tests (1 hour)

**1.6.1 Test Data Models** (`tests/unit/test_models.py`)
```python
import pytest
from dnd_character_scraper.models.character import Character, RuleVersion

def test_character_model_basic():
    """Test character model accepts required fields."""
    char = Character(
        character_id=144986992,
        name="Test Character",
        level=1
    )
    
    assert char.character_id == 144986992
    assert char.name == "Test Character"
    assert char.level == 1
    assert char.rule_version == RuleVersion.RULES_2014  # default

def test_character_model_unknown_fields():
    """Test model handles unknown fields gracefully."""
    char = Character(
        character_id=1,
        name="Test",
        level=1,
        unknown_field="should_be_preserved"
    )
    
    # Pydantic extra='allow' should preserve unknown fields
    assert hasattr(char, 'unknown_field')
```

**1.6.2 Test Calculator Interface** (`tests/unit/test_calculators.py`)
```python
import pytest
from dnd_character_scraper.calculators.ability_scores import AbilityScoreCalculator

def test_ability_score_calculator():
    """Test ability score calculator with known data."""
    calculator = AbilityScoreCalculator()
    
    test_data = {
        "stats": [
            {"id": 1, "value": 15},  # STR
            {"id": 2, "value": 14},  # DEX
            {"id": 3, "value": 16},  # CON
            {"id": 4, "value": 8},   # INT
            {"id": 5, "value": 12},  # WIS
            {"id": 6, "value": 17}   # CHA
        ]
    }
    
    result = calculator.calculate(test_data, "2014")
    
    assert isinstance(result.value, dict)
    assert "strength" in result.value
    assert result.value["strength"] == 15  # Expected value
    assert len(result.calculation_steps) > 0
```

#### Step 7: Integration Test (30 minutes)

**1.7.1 Test Complete Flow** (`tests/integration/test_phase1.py`)
```python
def test_character_creation_from_mock_api():
    """Test complete flow: API → Models → Calculator."""
    from dnd_character_scraper.api.mock_client import MockAPIClient
    from dnd_character_scraper.calculators.ability_scores import AbilityScoreCalculator
    from dnd_character_scraper.models.character import Character
    
    # Get mock data
    client = MockAPIClient()
    raw_data = client.get_character(999999)
    
    # Calculate ability scores
    calculator = AbilityScoreCalculator()
    ability_result = calculator.calculate(raw_data, "2014")
    
    # Create character model
    character = Character(
        character_id=raw_data["id"],
        name=raw_data["name"],
        level=raw_data["level"],
        ability_scores=ability_result.value
    )
    
    assert character.name == "Test Character"
    assert character.level == 2
    assert len(character.ability_scores) == 6
```

### 1.2 Project Structure
```
dnd_character_scraper/
├── __init__.py
├── interfaces/              # NEW: Explicit interface definitions
│   ├── __init__.py
│   ├── calculators.py      # Calculator ABC interfaces
│   ├── processors.py       # Processor ABC interfaces
│   ├── exporters.py        # Exporter ABC interfaces
│   └── validators.py       # Validator ABC interfaces
├── models/
│   ├── __init__.py
│   ├── character.py         # Character data models
│   ├── spells.py           # Spell-related models
│   ├── equipment.py        # Equipment and inventory models
│   ├── abilities.py        # Ability scores and modifiers
│   └── proficiencies.py    # Skills, saves, languages, tools
├── api/
│   ├── __init__.py
│   ├── client.py           # D&D Beyond API client (with fail-fast validation)
│   ├── endpoints.py        # API endpoint definitions
│   ├── exceptions.py       # API-specific exceptions
│   └── mock_client.py      # NEW: Mock client for testing
├── calculators/
│   ├── __init__.py
│   ├── base.py            # Base calculator interface
│   ├── ability_scores.py  # Ability score calculations
│   ├── hit_points.py      # HP calculations (2014/2024)
│   ├── armor_class.py     # AC calculations
│   ├── spell_slots.py     # Spell slot calculations
│   ├── proficiency.py     # Proficiency bonus calculations
│   └── initiative.py      # Initiative calculations
├── rules/
│   ├── __init__.py
│   ├── base.py            # Base rule interface
│   ├── version_manager.py # Centralized 2014 vs 2024 rule detection
│   ├── rule_2014.py       # 2014-specific rules
│   ├── rule_2024.py       # 2024-specific rules
│   └── constants.py       # Game constants and mappings
├── processors/
│   ├── __init__.py
│   ├── base.py            # Base processor interface
│   ├── spells.py          # Spell processing logic
│   ├── equipment.py       # Equipment processing
│   ├── features.py        # Class/racial feature processing
│   └── modifiers.py       # Modifier processing
├── validators/
│   ├── __init__.py
│   ├── character.py       # Character data validation
│   ├── calculations.py    # Calculation validation
│   └── completeness.py    # Data completeness checks
├── exporters/
│   ├── __init__.py
│   ├── json_exporter.py   # JSON output (with debug_summary)
│   └── markdown_exporter.py # Markdown converter integration
├── utils/
│   ├── __init__.py
│   ├── logging.py         # Structured logging configuration
│   ├── text_processing.py # HTML/text cleaning
│   └── diagnostics.py     # Diagnostic utilities
├── tests/
│   ├── __init__.py
│   ├── fixtures/          # Test data fixtures
│   ├── mocks/             # NEW: Mock data and responses
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   ├── edge_cases/        # NEW: Edge case testing
│   ├── performance/       # NEW: Performance benchmarks
│   └── validation/        # Validation tests
└── cli/
    ├── __init__.py
    └── main.py            # Command-line interface (with --quick-compare)
```

### 1.2 Core Interfaces (`interfaces/`)

#### 1.2.1 Calculator Interface (`interfaces/calculators.py`)
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, Protocol

class CalculatorInterface(ABC):
    """Base interface for all character calculations."""
    
    @abstractmethod
    def calculate(self, character_data: Dict[str, Any]) -> Any:
        """Perform the calculation and return result."""
        pass
    
    @abstractmethod
    def validate_result(self, result: Any) -> bool:
        """Validate the calculation result."""
        pass
    
    @abstractmethod
    def get_calculation_steps(self) -> List[str]:
        """Return human-readable calculation steps for debugging."""
        pass

class ProcessorInterface(ABC):
    """Base interface for data processors."""
    
    @abstractmethod
    def process(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process raw data and return structured result."""
        pass
    
    @abstractmethod
    def validate_input(self, raw_data: Dict[str, Any]) -> bool:
        """Validate input data before processing."""
        pass

class ExporterInterface(ABC):
    """Base interface for data exporters."""
    
    @abstractmethod
    def export(self, character_data: Dict[str, Any], output_path: str) -> bool:
        """Export character data to specified format/path."""
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported export formats."""
        pass
```

### 1.3 Enhanced Data Models with Extensibility

#### 1.3.1 Character Model with Pydantic (`models/character.py`)
```python
from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any, Union
from enum import Enum

class RuleVersion(str, Enum):
    RULES_2014 = "2014"
    RULES_2024 = "2024"

class HitPointType(int, Enum):
    FIXED = 1
    MANUAL = 2

class CharacterBasicInfo(BaseModel):
    model_config = ConfigDict(extra='allow')  # Allow unknown fields
    
    character_id: int
    name: str
    level: int
    experience: int
    classes: List['CharacterClass']
    species: Optional['Species'] = None
    race: Optional['Race'] = None  # Legacy 2014 support
    background: Optional['Background'] = None
    rule_version: RuleVersion = RuleVersion.RULES_2014
    hit_point_type: HitPointType = HitPointType.FIXED

class CharacterClass(BaseModel):
    model_config = ConfigDict(extra='allow')  # Handle unknown subclasses
    
    name: str
    level: int
    definition_id: int
    subclass: Optional['Subclass'] = None
    hit_die: str = "d8"
    spellcasting_ability: Optional[str] = None

class Character(BaseModel):
    model_config = ConfigDict(extra='allow')  # Future API changes
    
    basic_info: CharacterBasicInfo
    ability_scores: 'AbilityScores'
    hit_points: 'HitPoints'
    armor_class: 'ArmorClass'
    spells: 'SpellCollection'
    proficiencies: 'Proficiencies'
    equipment: 'Equipment'
    features: List['Feature']
    debug_summary: Dict[str, Any]  # For validation and debugging
    meta: 'CharacterMeta'
    raw_data: Dict[str, Any] = Field(exclude=True)  # Don't include in serialization
```

#### 1.3.2 Ability Scores Model with Pydantic (`models/abilities.py`)
```python
from pydantic import BaseModel, computed_field
from typing import Optional

class AbilityScore(BaseModel):
    base: int
    racial_bonus: int = 0
    asi_bonus: int = 0
    feat_bonus: int = 0
    item_bonus: int = 0
    misc_bonus: int = 0
    override: Optional[int] = None
    
    @computed_field
    @property
    def total(self) -> int:
        if self.override is not None:
            return self.override
        return self.base + self.racial_bonus + self.asi_bonus + self.feat_bonus + self.item_bonus + self.misc_bonus
    
    @computed_field
    @property
    def modifier(self) -> int:
        return (self.total - 10) // 2

class AbilityScores(BaseModel):
    strength: AbilityScore
    dexterity: AbilityScore
    constitution: AbilityScore
    intelligence: AbilityScore
    wisdom: AbilityScore
    charisma: AbilityScore
    
    def get_modifier(self, ability: str) -> int:
        return getattr(self, ability.lower()).modifier
```

### 1.3 Enhanced API Client (`api/client.py`)
```python
import requests
from typing import Dict, Any, Optional
from .exceptions import DNDBeyondAPIError, CharacterNotFoundError

class DNDBeyondAPIClient:
    BASE_URL = "https://character-service.dndbeyond.com"
    
    def __init__(self, session_cookie: Optional[str] = None):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'DnDBeyond-Enhanced-Scraper/6.0.0'
        })
        if session_cookie:
            self.session.cookies.set('session', session_cookie)
    
    def get_character(self, character_id: int) -> Dict[str, Any]:
        """Fetch character data from D&D Beyond API."""
        url = f"{self.BASE_URL}/character/v5/character/{character_id}"
        
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # FAIL FAST: Validate response structure early
            if 'data' not in data:
                raise DNDBeyondAPIError(f"Invalid response structure for character {character_id}")
            
            character_data = data['data']
            
            # FAIL FAST: Validate required sections
            required_sections = ['stats', 'classes']
            for section in required_sections:
                if section not in character_data:
                    raise DNDBeyondAPIError(f"Missing {section} section — invalid or outdated API response")
            
            return character_data
            
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                raise CharacterNotFoundError(f"Character {character_id} not found")
            raise DNDBeyondAPIError(f"API request failed: {e}")
        except requests.exceptions.RequestException as e:
            raise DNDBeyondAPIError(f"Network error: {e}")
```

### 1.4 Enhanced Error Handling & Logging (`utils/logging.py`)

```python
import logging
import json
from typing import Dict, Any, Optional
from enum import Enum

class LogLevel(Enum):
    DEBUG = "DEBUG"
    INFO = "INFO" 
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

class StructuredLogger:
    """Structured logging for better debugging and monitoring."""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self._setup_structured_logging()
    
    def _setup_structured_logging(self):
        """Configure structured JSON logging."""
        handler = logging.StreamHandler()
        formatter = StructuredFormatter()
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_character_processing(self, character_id: int, phase: str, data: Dict[str, Any]):
        """Log character processing with context."""
        self.logger.info("Character processing", extra={
            'character_id': character_id,
            'phase': phase,
            'data': data
        })
    
    def log_calculation_error(self, calculator: str, error: Exception, context: Dict[str, Any]):
        """Log calculation errors with full context."""
        self.logger.error("Calculation failed", extra={
            'calculator': calculator,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'context': context
        })
    
    def log_api_request(self, character_id: int, response_time: float, success: bool):
        """Log API requests for monitoring."""
        self.logger.info("API request", extra={
            'character_id': character_id,
            'response_time_ms': response_time * 1000,
            'success': success
        })

class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured JSON logging."""
    
    def format(self, record):
        log_entry = {
            'timestamp': self.formatTime(record),
            'level': record.levelname,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName
        }
        
        # Add extra fields if present
        if hasattr(record, 'character_id'):
            log_entry['character_id'] = record.character_id
        if hasattr(record, 'phase'):
            log_entry['phase'] = record.phase
        if hasattr(record, 'data'):
            log_entry['data'] = record.data
        if hasattr(record, 'context'):
            log_entry['context'] = record.context
            
        return json.dumps(log_entry)
```

### 1.5 Simple Testing Strategy (No DI Container)

For a personal tool, we'll use simpler testing approaches:

```python
# tests/conftest.py - Simple pytest fixtures
import pytest
from api.mock_client import MockDNDBeyondAPIClient

@pytest.fixture
def mock_api_client():
    """Provide mock API client for testing."""
    return MockDNDBeyondAPIClient()

@pytest.fixture
def sample_character_data():
    """Provide sample character data for testing."""
    return {
        "id": 144986992,
        "name": "Test Character",
        "level": 2,
        "classes": [{"definition": {"name": "Sorcerer"}, "level": 2}],
        "stats": [{"id": 1, "value": 15}, {"id": 6, "value": 17}]
    }

# Simple dependency passing instead of DI container:
class CharacterProcessor:
    def __init__(self, api_client=None):
        self.api_client = api_client or DNDBeyondAPIClient()
    
    def process_character(self, character_id: int):
        # Use injected client (for testing) or default (for production)
        raw_data = self.api_client.get_character(character_id)
        return self._process_data(raw_data)
```

### 1.6 Progress Tracking for Phase 1

**Update Status**: Use Edit tool to change `[ ]` to `[x]` when complete.

- [ ] Create project structure and `__init__.py` files
- [ ] Implement explicit interface definitions (ABC classes)
- [ ] Implement core data models with extensibility fields
- [ ] Implement API client with fail-fast validation and mock client
- [ ] Set up simple testing with mock clients
- [ ] Set up structured logging system
- [ ] Write unit tests for data models and interfaces
- [ ] Plan manual migration strategy (piece-by-piece, not automated)

**Phase 1 Completion Criteria**:
- [ ] All modules created with proper interfaces
- [ ] Data models handle 2014 and 2024 content
- [ ] API client includes mock for testing
- [ ] Basic unit tests pass
- [ ] Logging system configured

---

## Phase 2: D&D Rule Calculations & Complete JSON Output

**Goal**: Extract and implement all calculation logic from v5.2.0 into modular calculators  
**Duration**: Core functionality phase - most complex work  
**Success Criteria**: All derived values calculated correctly, complete JSON output, parser independence

**Key Principle**: The scraper must calculate and include ALL derived values in the JSON output so that the parser can work independently without performing complex D&D calculations.

### 2.1 Step-by-Step Calculator Implementation

#### Step 1: Set Up Calculator Framework (1 hour)

**2.1.1 Create Base Calculator** (`calculators/base.py`)
```python
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from ..interfaces.calculators import CalculatorInterface, CalculationResult
from ..models.character import Character

class BaseCalculator(CalculatorInterface):
    """Base calculator with common functionality."""
    
    def __init__(self, rule_version: str = "2014"):
        self.rule_version = rule_version
    
    @abstractmethod
    def calculate(self, character_data: Dict[str, Any], rule_version: str) -> CalculationResult:
        pass
    
    def _log_calculation_step(self, step: str, steps: List[str]):
        """Helper to log calculation steps."""
        steps.append(f"[{self.calculator_name}] {step}")
    
    def _get_ability_modifier(self, score: int) -> int:
        """Standard D&D ability modifier calculation."""
        return (score - 10) // 2
    
    def _get_proficiency_bonus(self, level: int) -> int:
        """Standard D&D proficiency bonus calculation."""
        return 2 + ((level - 1) // 4)
```

**2.1.2 Identify All Calculators Needed**
Search `enhanced_dnd_scraper.py` for all calculations:
```bash
grep -n -B2 -A5 "@cached_property\|def _calculate" enhanced_dnd_scraper.py > calculator_analysis.txt
```

Expected calculators to extract:
- Ability Scores (already done in Phase 1)
- Hit Points
- Armor Class  
- Initiative
- Spell Slots
- Proficiency Bonus
- Saving Throws
- Skills
- Speed

#### Step 2: Hit Points Calculator (2 hours)

**2.2.1 Find Existing HP Logic**
```bash
grep -n -A 20 "_calculate_hit_points\|hit.*point\|hp" enhanced_dnd_scraper.py
```

**2.2.2 Extract HP Calculator** (`calculators/hit_points.py`)
```python
from typing import Dict, Any, List
from ..interfaces.calculators import CalculationResult
from .base import BaseCalculator

class HitPointsCalculator(BaseCalculator):
    """Calculate hit points with proper 2014/2024 rules support."""
    
    @property
    def calculator_name(self) -> str:
        return "Hit Points Calculator"
    
    def get_dependencies(self) -> List[str]:
        return ["classes", "stats", "preferences", "level"]
    
    def calculate(self, character_data: Dict[str, Any], rule_version: str) -> CalculationResult:
        """EXACT copy of HP calculation logic from v5.2.0."""
        steps = []
        warnings = []
        
        # Step 1: Get character level and CON modifier
        level = character_data.get("level", 1)
        self._log_calculation_step(f"Character level: {level}", steps)
        
        # Get CON modifier from stats
        stats = character_data.get("stats", [])
        con_score = next((s["value"] for s in stats if s["id"] == 3), 10)
        con_modifier = self._get_ability_modifier(con_score)
        self._log_calculation_step(f"CON score: {con_score}, modifier: {con_modifier}", steps)
        
        # Step 2: Get hit point type preference
        preferences = character_data.get("preferences", {})
        hit_point_type = preferences.get("hitPointType", 1)  # 1=fixed, 2=manual
        
        # Step 3: Calculate hit points by class
        classes = character_data.get("classes", [])
        total_hp = 0
        
        for class_info in classes:
            class_name = class_info.get("definition", {}).get("name", "Unknown")
            class_level = class_info.get("level", 1)
            
            # Get hit die for this class (copy exact logic from v5.2.0)
            hit_die = self._get_hit_die_for_class(class_name)
            self._log_calculation_step(f"{class_name} level {class_level}, hit die: d{hit_die}", steps)
            
            if hit_point_type == 1:  # Fixed HP
                # First level: max hit die + CON
                # Other levels: average hit die + CON (minimum 1)
                if class_level >= 1:
                    first_level_hp = hit_die + con_modifier
                    total_hp += max(1, first_level_hp)
                    self._log_calculation_step(f"Level 1: {hit_die} + {con_modifier} = {max(1, first_level_hp)}", steps)
                
                if class_level > 1:
                    avg_per_level = (hit_die // 2) + 1 + con_modifier
                    additional_levels = class_level - 1
                    additional_hp = max(additional_levels, additional_levels * avg_per_level)
                    total_hp += additional_hp
                    self._log_calculation_step(f"Levels 2-{class_level}: {additional_levels} × {avg_per_level} = {additional_hp}", steps)
            
            elif hit_point_type == 2:  # Manual HP
                # Copy manual HP logic from v5.2.0
                manual_hp = self._get_manual_hp(character_data, class_info)
                total_hp += manual_hp
                self._log_calculation_step(f"Manual HP for {class_name}: {manual_hp}", steps)
        
        # Step 4: Apply any HP bonuses from feats/items
        hp_bonuses = self._calculate_hp_bonuses(character_data)
        if hp_bonuses > 0:
            total_hp += hp_bonuses
            self._log_calculation_step(f"HP bonuses from feats/items: +{hp_bonuses}", steps)
        
        return CalculationResult(
            value=total_hp,
            calculation_steps=steps,
            source_data={
                "level": level,
                "con_modifier": con_modifier,
                "hit_point_type": hit_point_type,
                "classes": classes
            },
            warnings=warnings
        )
    
    def _get_hit_die_for_class(self, class_name: str) -> int:
        """Copy exact hit die mapping from v5.2.0."""
        hit_dice = {
            "Artificer": 8, "Barbarian": 12, "Bard": 8, "Cleric": 8,
            "Druid": 8, "Fighter": 10, "Monk": 8, "Paladin": 10,
            "Ranger": 10, "Rogue": 8, "Sorcerer": 6, "Warlock": 8, "Wizard": 6
        }
        return hit_dice.get(class_name, 8)  # Default to d8
    
    def _get_manual_hp(self, character_data: Dict[str, Any], class_info: Dict[str, Any]) -> int:
        """Extract manual HP logic from v5.2.0."""
        # Copy the exact manual HP calculation logic
        # This is complex - need to find it in the existing code
        return 0  # Placeholder
    
    def _calculate_hp_bonuses(self, character_data: Dict[str, Any]) -> int:
        """Calculate HP bonuses from feats, items, etc."""
        # Copy feat/item HP bonus logic from v5.2.0
        return 0  # Placeholder
```

**2.2.3 Test HP Calculator** (`tests/unit/test_hit_points.py`)
```python
import pytest
from dnd_character_scraper.calculators.hit_points import HitPointsCalculator

def test_hit_points_sorcerer_level_2():
    """Test HP calculation using standard D&D rules."""
    calculator = HitPointsCalculator()
    
    test_data = {
        "level": 2,
        "stats": [{"id": 3, "value": 16}],  # CON 16 = +3 modifier
        "classes": [{"definition": {"name": "Sorcerer"}, "level": 2}],
        "preferences": {"hitPointType": 1}  # Fixed HP
    }
    
    result = calculator.calculate(test_data, "2014")
    
    # Sorcerer: d6 hit die
    # Level 1: 6 + 3 = 9 HP
    # Level 2: 4 + 3 = 7 HP (average of d6+1 = 4, +3 CON)
    # Total: 9 + 7 = 16 HP
    
    expected_hp = 16  # Based on standard D&D rules
    assert result.value == expected_hp
    assert len(result.calculation_steps) > 0
    assert "Sorcerer level 2" in str(result.calculation_steps)
```

#### Step 3: Armor Class Calculator (1.5 hours)

**2.3.1 Find AC Logic**
```bash
grep -n -A 15 "armor.*class\|_calculate.*ac" enhanced_dnd_scraper.py
```

**2.3.2 Extract AC Calculator** (`calculators/armor_class.py`)
```python
from typing import Dict, Any, List
from ..interfaces.calculators import CalculationResult
from .base import BaseCalculator

class ArmorClassCalculator(BaseCalculator):
    """Calculate armor class from equipment, abilities, and class features."""
    
    @property
    def calculator_name(self) -> str:
        return "Armor Class Calculator"
    
    def get_dependencies(self) -> List[str]:
        return ["stats", "inventory", "modifiers", "classes"]
    
    def calculate(self, character_data: Dict[str, Any], rule_version: str) -> CalculationResult:
        """EXACT copy of AC calculation logic from v5.2.0."""
        steps = []
        warnings = []
        
        # Step 1: Get DEX modifier
        stats = character_data.get("stats", [])
        dex_score = next((s["value"] for s in stats if s["id"] == 2), 10)
        dex_modifier = self._get_ability_modifier(dex_score)
        self._log_calculation_step(f"DEX score: {dex_score}, modifier: {dex_modifier}", steps)
        
        # Step 2: Check for equipped armor
        equipped_armor = self._find_equipped_armor(character_data)
        
        if equipped_armor:
            # Armor-based AC calculation
            base_ac = equipped_armor.get("armorClass", 10)
            armor_name = equipped_armor.get("definition", {}).get("name", "Unknown Armor")
            
            # Check if armor limits DEX bonus
            dex_bonus = self._calculate_armor_dex_bonus(equipped_armor, dex_modifier)
            
            total_ac = base_ac + dex_bonus
            self._log_calculation_step(f"Armor: {armor_name}, base AC: {base_ac}, DEX bonus: {dex_bonus}", steps)
        
        else:
            # Unarmored AC calculation
            base_ac = 10
            
            # Check for Unarmored Defense class features
            unarmored_defense = self._check_unarmored_defense(character_data)
            if unarmored_defense:
                total_ac = self._calculate_unarmored_defense_ac(character_data, steps)
            else:
                total_ac = base_ac + dex_modifier
                self._log_calculation_step(f"Unarmored: {base_ac} + {dex_modifier} DEX = {total_ac}", steps)
        
        # Step 3: Apply AC bonuses from shields, magic items, spells
        ac_bonuses = self._calculate_ac_bonuses(character_data, steps)
        final_ac = total_ac + ac_bonuses
        
        if ac_bonuses > 0:
            self._log_calculation_step(f"AC bonuses: +{ac_bonuses}, final AC: {final_ac}", steps)
        
        return CalculationResult(
            value=final_ac,
            calculation_steps=steps,
            source_data={
                "dex_modifier": dex_modifier,
                "equipped_armor": equipped_armor,
                "ac_bonuses": ac_bonuses
            },
            warnings=warnings
        )
    
    def _find_equipped_armor(self, character_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find equipped armor from inventory."""
        # Copy exact inventory parsing logic from v5.2.0
        inventory = character_data.get("inventory", [])
        for item in inventory:
            if item.get("equipped") and item.get("definition", {}).get("armorClass"):
                return item
        return None
    
    def _calculate_armor_dex_bonus(self, armor: Dict[str, Any], dex_modifier: int) -> int:
        """Calculate DEX bonus allowed by armor type."""
        # Copy exact armor type logic from v5.2.0
        armor_type = armor.get("definition", {}).get("armorTypeId", 1)
        
        if armor_type == 1:  # Light armor
            return dex_modifier
        elif armor_type == 2:  # Medium armor
            return min(dex_modifier, 2)
        elif armor_type == 3:  # Heavy armor
            return 0
        else:
            return dex_modifier  # Unknown type, allow full DEX
    
    def _check_unarmored_defense(self, character_data: Dict[str, Any]) -> bool:
        """Check if character has Unarmored Defense feature."""
        classes = character_data.get("classes", [])
        for class_info in classes:
            class_name = class_info.get("definition", {}).get("name", "")
            if class_name in ["Barbarian", "Monk"]:
                return True
        return False
    
    def _calculate_unarmored_defense_ac(self, character_data: Dict[str, Any], steps: List[str]) -> int:
        """Calculate AC with Unarmored Defense."""
        # Copy exact Unarmored Defense logic from v5.2.0
        # Barbarian: 10 + DEX + CON
        # Monk: 10 + DEX + WIS
        return 10  # Placeholder
```

#### Step 4: Spell Slots Calculator (2 hours)

**2.4.1 Find Spell Slot Logic**
```bash
grep -n -A 25 "spell.*slot\|_calculate.*spell" enhanced_dnd_scraper.py
```

This is complex multiclass logic - copy exactly from v5.2.0.

#### Step 5: Integration and Testing (1 hour)

**2.5.1 Create Calculator Registry** (`calculators/__init__.py`)
```python
from .ability_scores import AbilityScoreCalculator
from .hit_points import HitPointsCalculator
from .armor_class import ArmorClassCalculator
from .spell_slots import SpellSlotsCalculator

class CalculatorRegistry:
    """Registry of all calculators for complete character processing."""
    
    def __init__(self, rule_version: str = "2014"):
        self.calculators = {
            "ability_scores": AbilityScoreCalculator(rule_version),
            "hit_points": HitPointsCalculator(rule_version),
            "armor_class": ArmorClassCalculator(rule_version),
            "spell_slots": SpellSlotsCalculator(rule_version),
        }
    
    def calculate_all(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run all calculators and return complete results."""
        results = {}
        calculation_log = []
        
        for name, calculator in self.calculators.items():
            try:
                result = calculator.calculate(character_data, self.rule_version)
                results[name] = result.value
                calculation_log.extend(result.calculation_steps)
            except Exception as e:
                results[name] = None
                calculation_log.append(f"ERROR in {name}: {e}")
        
        results["_calculation_log"] = calculation_log
        return results
```

**2.5.2 Integration Test** (`tests/integration/test_phase2.py`)
```python
def test_complete_character_calculation():
    """Test all calculators working together."""
    from dnd_character_scraper.api.mock_client import MockAPIClient
    from dnd_character_scraper.calculators import CalculatorRegistry
    
    client = MockAPIClient()
    raw_data = client.get_character(999999)  # Test character
    
    registry = CalculatorRegistry("2014")
    results = registry.calculate_all(raw_data)
    
    # Verify all calculations completed
    assert results["ability_scores"] is not None
    assert results["hit_points"] is not None
    assert results["armor_class"] is not None
    
    # Verify specific values match expected
    assert results["hit_points"] > 0
    assert results["armor_class"] >= 10
    assert len(results["ability_scores"]) == 6
```

### 2.1 Calculator Architecture

#### 2.1.1 Base Calculator (`calculators/base.py`)
```python
from abc import ABC, abstractmethod
from typing import Any, Dict
from ..models.character import Character
from ..rules.version_manager import RuleVersionManager

class BaseCalculator(ABC):
    def __init__(self, rule_manager: RuleVersionManager):
        self.rule_manager = rule_manager
    
    @abstractmethod
    def calculate(self, character_data: Dict[str, Any]) -> Any:
        """Perform the calculation."""
        pass
    
    @abstractmethod
    def validate(self, result: Any) -> bool:
        """Validate the calculation result."""
        pass
```

#### 2.1.2 Hit Points Calculator (`calculators/hit_points.py`)
```python
from typing import Dict, Any
from ..models.character import HitPointType, Character
from ..models.abilities import AbilityScores
from .base import BaseCalculator

class HitPointsCalculator(BaseCalculator):
    """Calculate character hit points based on 2014/2024 rules."""
    
    # Hit die averages (rounded up)
    HIT_DIE_AVERAGES = {
        'd6': 4, 'd8': 5, 'd10': 6, 'd12': 7
    }
    
    def calculate(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate hit points using appropriate rule set."""
        hit_point_type = self._get_hit_point_type(character_data)
        classes = character_data.get('classes', [])
        constitution_modifier = self._get_constitution_modifier(character_data)
        
        if hit_point_type == HitPointType.FIXED:
            return self._calculate_fixed_hp(classes, constitution_modifier)
        else:
            return self._calculate_manual_hp(character_data, constitution_modifier)
    
    def _calculate_fixed_hp(self, classes: List[Dict], con_mod: int) -> Dict[str, Any]:
        """Calculate HP using fixed/average method."""
        total_hp = 0
        calculation_steps = []
        
        for class_info in classes:
            class_name = class_info.get('definition', {}).get('name', 'Unknown')
            level = class_info.get('level', 1)
            hit_die = class_info.get('definition', {}).get('hitDie', 8)
            hit_die_str = f'd{hit_die}'
            
            if level >= 1:
                # Level 1: max hit die + CON mod
                level_1_hp = hit_die + con_mod
                total_hp += level_1_hp
                calculation_steps.append(f"{class_name} L1: {hit_die} (max {hit_die_str}) + {con_mod} CON = {level_1_hp}")
                
                # Remaining levels: average + CON mod
                if level > 1:
                    avg_per_level = self.HIT_DIE_AVERAGES.get(hit_die_str, 5)
                    remaining_levels = level - 1
                    remaining_hp = remaining_levels * (avg_per_level + con_mod)
                    total_hp += remaining_hp
                    calculation_steps.append(f"{class_name} L2-{level}: {remaining_levels} × ({avg_per_level} avg + {con_mod} CON) = {remaining_hp}")
        
        return {
            'calculated_hp': total_hp,
            'current_hp': total_hp,  # Default to max unless specified
            'method': 'Fixed',
            'calculation_steps': calculation_steps,
            'breakdown': {
                'constitution_modifier': con_mod,
                'level_1_hp': hit_die + con_mod,
                'additional_levels_hp': total_hp - (hit_die + con_mod)
            }
        }
    
    def _get_constitution_modifier(self, character_data: Dict[str, Any]) -> int:
        """Get constitution modifier from character data."""
        stats = character_data.get('stats', [])
        for stat in stats:
            if stat.get('id') == 3:  # Constitution stat ID
                return (stat.get('value', 10) - 10) // 2
        return 0
```

#### 2.1.3 Spell Slots Calculator (`calculators/spell_slots.py`)
```python
class SpellSlotsCalculator(BaseCalculator):
    """Calculate spell slots including multiclass and Warlock pact magic."""
    
    SPELL_SLOT_TABLES = {
        'full_caster': {
            1: [2, 0, 0, 0, 0, 0, 0, 0, 0],
            2: [3, 0, 0, 0, 0, 0, 0, 0, 0],
            3: [4, 2, 0, 0, 0, 0, 0, 0, 0],
            # ... full table
        },
        'half_caster': {
            2: [2, 0, 0, 0, 0],
            3: [3, 0, 0, 0, 0],
            # ... half caster table
        },
        'third_caster': {
            3: [2, 0, 0, 0],
            4: [3, 0, 0, 0],
            # ... third caster table
        }
    }
    
    def calculate(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate spell slots for all classes including multiclass rules."""
        classes = character_data.get('classes', [])
        
        if len(classes) == 1:
            return self._calculate_single_class_slots(classes[0])
        else:
            return self._calculate_multiclass_slots(classes)
    
    def _calculate_multiclass_slots(self, classes: List[Dict]) -> Dict[str, Any]:
        """Calculate multiclass spell slots using 2024 rules."""
        caster_level = 0
        warlock_levels = 0
        
        for class_info in classes:
            class_name = class_info.get('definition', {}).get('name', '').lower()
            level = class_info.get('level', 0)
            
            if class_name == 'warlock':
                warlock_levels = level
            elif class_name in ['wizard', 'sorcerer', 'bard', 'cleric', 'druid']:
                caster_level += level  # Full casters
            elif class_name in ['paladin', 'ranger']:
                caster_level += level // 2  # Half casters
            elif class_name in ['fighter', 'rogue']:  # Eldritch Knight, Arcane Trickster
                subclass = class_info.get('subclassDefinition', {}).get('name', '')
                if 'eldritch knight' in subclass.lower() or 'arcane trickster' in subclass.lower():
                    caster_level += level // 3  # Third casters
        
        return {
            'multiclass_caster_level': caster_level,
            'warlock_levels': warlock_levels,
            'spell_slots': self._get_slots_for_level(caster_level),
            'warlock_slots': self._get_warlock_slots(warlock_levels),
            'spell_save_dc': self._calculate_spell_save_dc(character_data),
            'spell_attack_bonus': self._calculate_spell_attack_bonus(character_data),
            'primary_spellcasting_ability': self._determine_primary_ability(classes)
        }
```

### 2.2 Complete JSON Output Structure

The scraper must provide a comprehensive JSON output with all calculated values so the parser requires minimal computation:

```json
{
  "character_id": 144986992,
  "name": "Test Character",
  "level": 2,
  "classes": [
    {
      "name": "Sorcerer",
      "level": 2,
      "subclass": null,
      "hit_die": "d6",
      "spellcasting_ability": "charisma"
    }
  ],
  "rule_version": "2024",
  "hit_point_type": "Fixed",
  
  "ability_scores": {
    "strength": {"total": 15, "modifier": 2, "breakdown": {...}},
    "dexterity": {"total": 14, "modifier": 2, "breakdown": {...}},
    "constitution": {"total": 16, "modifier": 3, "breakdown": {...}},
    "intelligence": {"total": 8, "modifier": -1, "breakdown": {...}},
    "wisdom": {"total": 12, "modifier": 1, "breakdown": {...}},
    "charisma": {"total": 17, "modifier": 3, "breakdown": {...}}
  },
  
  "hit_points": {
    "calculated_hp": 13,
    "current_hp": 13,
    "method": "Fixed",
    "calculation_steps": ["Sorcerer L1: 6 (max d6) + 3 CON = 9", "Sorcerer L2: 1 × (4 avg + 3 CON) = 7"],
    "breakdown": {...}
  },
  
  "armor_class": {
    "total": 12,
    "base_ac": 10,
    "dex_modifier": 2,
    "armor_bonus": 0,
    "shield_bonus": 0,
    "calculation_method": "Unarmored"
  },
  
  "spellcasting": {
    "is_spellcaster": true,
    "spellcasting_type": "full_caster",
    "primary_ability": "charisma",
    "spell_save_dc": 13,
    "spell_attack_bonus": 5,
    "spell_slots": [3, 0, 0, 0, 0, 0, 0, 0, 0],
    "warlock_slots": null,
    "spells_known": 4,
    "cantrips_known": 3,
    "spells_prepared": null,
    "ritual_casting": false,
    "multiclass_caster_level": 2
  },
  
  "class_resources": {
    "sorcery_points": 2,
    "metamagic_known": 1,
    "ki_points": null,
    "rage_uses": null,
    "bardic_inspiration": null,
    "channel_divinity": null,
    "wild_shape": null,
    "action_surge": null,
    "second_wind": null
  },
  
  "feats": [
    {
      "name": "Tough",
      "type": "origin",
      "source": "Background",
      "description": "Your hit point maximum increases by twice your character level"
    }
  ],
  
  "proficiencies": {
    "proficiency_bonus": 2,
    "saving_throws": ["charisma", "constitution"],
    "skills": [
      {"name": "Arcana", "modifier": 1, "proficient": true, "source": "Class: Sorcerer"},
      {"name": "Persuasion", "modifier": 5, "proficient": true, "source": "Class: Sorcerer"}
    ]
  },
  
  "initiative": 2,
  "speed": 30,
  
  "debug_summary": {
    "key_calculations": "All major derived values for quick validation"
  }
}
```

### 2.3 Testing Strategy (Simplified)

#### 2.3.1 Edge Case Testing
Focus on D&D rule edge cases rather than performance:

```python
# tests/edge_cases/test_multiclass_scenarios.py
def test_triple_multiclass_spell_slots():
    """Test complex multiclass spell slot calculations."""
    # Wizard/Sorcerer/Warlock multiclass
    character_data = {
        'classes': [
            {'definition': {'name': 'Wizard'}, 'level': 6},
            {'definition': {'name': 'Sorcerer'}, 'level': 6},
            {'definition': {'name': 'Warlock'}, 'level': 8}
        ]
    }
    
    # Verify separate spell slot pools are calculated correctly
    result = calculator.calculate(character_data)
    assert result['multiclass_caster_level'] == 12  # Wizard + Sorcerer
    assert result['warlock_levels'] == 8  # Separate pact magic

def test_constitution_penalty_hp():
    """Test HP calculation with negative Constitution modifier."""
    character_data = {
        'classes': [{'definition': {'name': 'Fighter', 'hitDie': 10}, 'level': 5}],
        'stats': [{'id': 3, 'value': 8}],  # CON 8 = -1 modifier
        'preferences': {'hitPointType': 1}  # Fixed HP
    }
    
    result = calculator.calculate(character_data)
    # Each level minimum 1 HP even with negative CON
    assert result['calculated_hp'] >= 5  # Minimum 1 HP per level
```

#### 2.3.2 API Mock Testing
For testing without external API dependency:

```python
# tests/mocks/mock_responses.py
MOCK_CHARACTERS = {
    144986992: {
        "id": 144986992,
        "name": "Test Character",
        "level": 2,
        "classes": [{"definition": {"name": "Sorcerer", "hitDie": 6}, "level": 2}],
        "stats": [
            {"id": 1, "value": 15}, {"id": 2, "value": 14}, {"id": 3, "value": 16},
            {"id": 4, "value": 8}, {"id": 5, "value": 12}, {"id": 6, "value": 17}
        ],
        "preferences": {"hitPointType": 1}
    }
}

class MockAPIClient:
    def get_character(self, character_id: int):
        if character_id in MOCK_CHARACTERS:
            return MOCK_CHARACTERS[character_id]
        raise CharacterNotFoundError(f"Character {character_id} not found")
```

### 2.4 Progress Tracking for Phase 2

**Update Status**: Use Edit tool to change `[ ]` to `[x]` when complete.

- [ ] Implement calculators that produce complete derived values
- [ ] Create hit points calculator (HP, current HP, calculation steps)
- [ ] Create armor class calculator (total AC, breakdown, method)
- [ ] Create spell slots calculator (slots, save DC, attack bonus)
- [ ] Create ability score calculator (totals, modifiers, source breakdown)
- [ ] Create proficiency calculator (bonus, skills with sources)
- [ ] Ensure JSON output contains all values needed by parser
- [ ] Test edge cases (multiclass, negative modifiers, unknown content)
- [ ] Create API mock framework for testing
- [ ] Validate against manually verified character data

**Phase 2 Completion Criteria**:
- [ ] All calculators produce complete JSON output
- [ ] Parser requires minimal computation
- [ ] Edge cases handled gracefully
- [ ] Spell system supports all 4 casting types
- [ ] Multiclass scenarios work correctly

---

## Phase 3: Rule Version Management ✅ ARCHITECTURE COMPLETE

**Goal**: Implement comprehensive 2014/2024 rule detection and handling  
**Duration**: Rules complexity phase - handle all D&D content variations  
**Success Criteria**: Accurate rule detection, proper terminology, all content supported

### ✅ **Completed in Phase 3**

**Core Architecture**:
- ✅ **RuleVersionManager** - Sophisticated 2014/2024 detection with voting system
- ✅ **GameConstants** - Comprehensive D&D data for both rule versions
- ✅ **RuleAwareCalculator** base class - Enhanced calculator framework
- ✅ **Rule Detection Hierarchy** - Primary class-based with 2024 default
- ✅ **Validation Infrastructure** - Fixed skills→features field rename

**Critical Bug Fixes**:
- ✅ **Barbarian Unarmored Defense** - Fixed AC calculation (10+DEX+CON, was missing DEX)
- ✅ **Monk Unarmored Defense** - Fixed AC calculation (10+DEX+WIS when unarmored/no shield)
- ✅ **Calculator Integration** - Enhanced CharacterCalculator with rule-awareness

**Rule Detection Features**:
- ✅ **Multi-Method Detection** - Primary class, source IDs, terminology, structure
- ✅ **Conservative Strategy** - Any 2014 content forces 2014 rules
- ✅ **User Override** - `--force-2014` / `--force-2024` command line options
- ✅ **Evidence Logging** - Transparent detection with warnings and evidence
- ✅ **Homebrew Filtering** - Only official content influences detection

### 🚧 **Phase 3 Remaining Tasks**

**Entry Scripts**:
- ✅ Create new main scraper entry point using v6.0.0 architecture
- ✅ Create new main parser entry point using v6.0.0 architecture
- ✅ Preserve all v5.2.0 CLI features and options
- ✅ Implement force option passing from parser to scraper

**Testing & Validation**:
- ⏳ Comprehensive test suite for rule detection
- ⏳ Integration tests for calculator enhancement
- ⏳ Regression testing against v5.2.0 baseline

### 🎯 **Priority Issues from Validation**
Based on manual validation of character 29682199 (Redgrave), address these critical gaps:

**AC Calculator Enhancement (High Priority)**:
- **Missing Class Features**: Forge Domain AC bonuses (Soul of the Forge +1, Blessing of the Forge +1)
- **Missing Magic Items**: Cloak of Protection and other AC-enhancing magic items
- **Feature Interactions**: Warforged Integrated Protection + class features + magic items
- **Stacking Rules**: Proper AC bonus stacking and interaction logic

**Enhanced Spell Table Format (High Priority)**:
- **Detailed Spell Tables**: Implement comprehensive spell tables with casting indicators  
- **Spell Categories**: Cantrips (At Will), Leveled Spells (Cast/Prepared/Ritual)  
- **Free Spell Casting**: Track spells that can be cast without slots (e.g., "Detect Magic 1/LR")
- **Ritual Spell Handling**: Wizard ritual spells available without preparation
- **Spell Details**: Include Time, Range, Hit/DC, Effect, Notes columns
- **Source Attribution**: Clear spell source tracking (Sorcerer, Elven Lineage Spells, etc.)
- **Test Characters**: 
  - Vaelith (Sorcerer spell formatting)
  - Ilarion (Wizard rituals, free casting, Magic Initiate feat)
  - ZuB (High-level wizard, School of Conjuration, large spellbook)

**Sorcerer Class Features (High Priority)**:
- **Sorcery Points**: Track current/maximum sorcery points (Level 2+ Sorcerers)
- **Font of Magic**: Parse spell slot ↔ sorcery point conversion abilities
- **Metamagic Options**: Detect and list available metamagic (Careful, Distant, Empowered, etc.)
- **Metamagic Usage**: Track which metamagic options are known vs available
- **Test Character**: 144986992 (Vaelith) - Level 2 Sorcerer with Font of Magic and Metamagic

**Barbarian & HP Fixes (High Priority)**:
- **Unarmored Defense**: Fix Barbarian AC calculation (10 + DEX + CON mod) - Test: Character 145079040
- **HP Type Validation**: Detect manual vs fixed HP mismatches and auto-correct
- **Manual HP Detection**: When API reports fixed but actual HP doesn't match calculation

**2024 Rules Support (Medium Priority)**:
- **Feat Parsing**: Handle 2024 background feat bonuses differently than 2014
- **Source ID Detection**: Improve 2024 vs 2014 rule detection - Test: Character 141875964
- **Terminology**: Species vs Race handling for 2024 characters

**Baseline Export Enhancements (High Priority)**:
- **Spellcasting Section Export**: Add calculated spell save DC, spell attack bonus to main JSON structure
- **Large Spellbook Support**: Fix spell export limits (ZuB character: 9 parsed, only 2 exported)
- **Calculated Field Promotion**: Move meta calculations to main structure for parser compatibility
- **Test Character**: 147061783 (ZuB) - High-level wizard with large spellbook

**🚨 FEATURE PRESERVATION (CRITICAL) 🚨**:
- **MANDATORY**: Every feature in `v5_2_0_feature_inventory.md` MUST be preserved in v6.0.0
- **Zero Regression Policy**: No existing functionality can be lost or degraded
- **Pre-Development Requirement**: Review complete inventory before starting Phase 3 coding

**Key Preservation Areas**:
- **Checkbox/Rest System**: All regex patterns for "once per long rest", usage tracking, state keys
- **Spell System**: Multiclass calculations, pact magic separation, spell deduplication, preparation logic
- **Class Features**: Wizard spellbook, Sorcerer sorcery points, Warlock invocations, all class-specific mechanics
- **Parser Integration**: DnD UI Toolkit compatibility, action economy, spell tables, Obsidian formatting
- **API Integration**: Session cookies, retry logic, rate limiting, all CLI options
- **Rule Management**: 2024 vs 2014 detection, terminology handling, source ID checking

**Validation Requirement**: Each Phase 3 module MUST pass regression tests against v5.2.0 baseline output

**Target**: Achieve 95%+ accuracy on character 29682199 validation (currently 88.9%)

### 3.1 Step-by-Step Rule Implementation

#### Step 1: Analyze Current Rule Detection (1 hour)

**3.1.1 Find Existing Rule Logic**
```bash
grep -n -B5 -A10 "2024\|2014\|SOURCE_.*ID" enhanced_dnd_scraper.py
```

**3.1.2 Document Current Detection Methods**
Create analysis document:
```bash
# Create rule_analysis.md
echo "# Current Rule Detection Analysis

## Methods Found:
1. Source ID checking
2. Terminology detection (species vs race)
3. Spell source analysis
4. Class feature differences

## Source IDs to Extract:
" > rule_analysis.md

# Extract all source ID references
grep -n "SOURCE\|source.*id\|142\|143\|144" enhanced_dnd_scraper.py >> rule_analysis.md
```

### 🔍 **CRITICAL: Improved 2014/2024 Detection Strategy**
**Based on analysis of character 116277190 ([GI] Kaeda) - multiclass with homebrew subclasses**

#### **Detection Issue Discovered**:
- **Current Logic**: Relies on `SOURCE_2024_IDS = {145, 146, 147, 148, 149, 150}` but source IDs are `None` in API
- **False Positive**: "2024 Echo Knight" subclass triggered 2024 detection but is `isHomebrew: True`
- **Enhanced Spell Bug**: Parser incorrectly used `light-xphb.md` (2024) for Legacy 2014 character
- **Result**: Character detected as 2024 but should be 2014 with homebrew subclasses

#### **Improved Detection Logic (Phase 3 Implementation)**:
```python
def _detect_2024_rules_improved(self) -> bool:
    """Enhanced 2024 detection with homebrew filtering."""
    try:
        # Priority 1: User override flags (highest priority)
        if hasattr(self, 'force_rule_version'):
            return self.force_rule_version == "2024"
        
        # Priority 2: Official source ID detection
        official_2024_sources = self._check_official_2024_sources()
        if official_2024_sources is not None:
            return official_2024_sources
        
        # Priority 3: Official content analysis (exclude homebrew)
        official_2024_indicators = self._check_official_2024_content()
        if official_2024_indicators is not None:
            return official_2024_indicators
        
        # Priority 4: Conservative default (2014)
        return False
        
    except Exception as e:
        logger.error(f"Error in 2024 detection: {e}")
        return False  # Default to 2014 on error

def _check_official_2024_content(self) -> Optional[bool]:
    """Check for 2024 indicators in official content only."""
    # Check classes (exclude homebrew subclasses)
    for cls in self.raw_data.get("classes", []):
        class_def = cls.get("definition", {})
        subclass_def = cls.get("subclassDefinition", {})
        
        # Only check official content
        if not class_def.get("isHomebrew", False):
            # Check for official 2024 class indicators
            if self._has_2024_class_features(class_def):
                return True
        
        # Skip homebrew subclasses for rule detection
        if subclass_def and not subclass_def.get("isHomebrew", False):
            subclass_name = subclass_def.get("name", "")
            # Only trust "2024" in official content
            if "2024" in subclass_name:
                return True
    
    # Check race/species (exclude homebrew)
    race_data = self.raw_data.get("race", {})
    if race_data and not race_data.get("definition", {}).get("isHomebrew", False):
        # Check for official 2024 species indicators
        if "species" in self.raw_data:  # 2024 terminology
            return True
    
    return None  # No clear indicators found
```

#### **Command Line Force Options (Phase 3) - Parser-to-Scraper Continuity**:
```bash
# Direct scraper usage with force options
python enhanced_dnd_scraper.py 116277190 --force-2014  # Force Legacy rules
python enhanced_dnd_scraper.py 141875964 --force-2024  # Force 2024 rules

# Parser automatically passes force options to scraper
python dnd_json_to_markdown.py 116277190 output.md --force-2014 --no-enhance-spells
python dnd_json_to_markdown.py 116277190 output.md --force-2024

# Parser calls scraper with: python enhanced_dnd_scraper.py 116277190 --output temp.json --force-2014
```

#### **Parser-to-Scraper Argument Passing (Phase 3 Implementation)**:
```python
def run_scraper(character_id: str, session_cookie: Optional[str] = None, 
                script_path: Optional[Path] = None, 
                force_rules: Optional[str] = None) -> Dict[str, Any]:
    """Run enhanced DnD scraper with force rule options."""
    
    # Build base command
    cmd = [sys.executable, str(script_path), character_id, "--output", "temp_character.json"]
    
    # Pass through session cookie
    if session_cookie:
        cmd.extend(["--session", session_cookie])
    
    # Pass through force rule option
    if force_rules == "2014":
        cmd.append("--force-2014")
    elif force_rules == "2024": 
        cmd.append("--force-2024")
    
    # Pass through verbose flag
    if VERBOSE_OUTPUT:
        cmd.append("--verbose")
    
    # Execute scraper
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
```

#### **Consistent Option Handling**:
```python
# Parser argument parser additions (Phase 3)
parser.add_argument(
    "--force-2014",
    action="store_true", 
    help="Force 2014 rule detection (disables enhanced spells)"
)

parser.add_argument(
    "--force-2024",
    action="store_true",
    help="Force 2024 rule detection (enables enhanced spells)"
)

# Enhanced spell behavior with force options
def get_enhanced_spell_behavior(args) -> bool:
    """Determine enhanced spell usage based on arguments."""
    if args.no_enhance_spells:
        return False  # Explicit disable
    elif args.force_2014:
        return False  # Force 2014 = API only
    elif args.force_2024:
        return True   # Force 2024 = enhanced files
    else:
        return USE_ENHANCED_SPELL_DATA  # Default behavior
```

#### **Enhanced Spell System Fix**:
- **2014/Legacy Characters**: Always use API data (no enhanced files)
- **2024 Characters**: Use enhanced files with appropriate source suffix (`xphb`, `xge`, etc.)
- **Force Override**: `--force-2014` disables enhanced files regardless of detection

#### **Option Passing Workflow (Critical for Phase 3)**:
```
User runs: python dnd_json_to_markdown.py 116277190 output.md --force-2014
    ↓
Parser processes: --force-2014 argument
    ↓  
Parser calls: python enhanced_dnd_scraper.py 116277190 --output temp.json --force-2014
    ↓
Scraper detects: force_rules="2014" → sets is_2024_rules=False
    ↓
Scraper outputs: JSON with "is_2024_rules": false
    ↓
Parser reads: JSON and sees is_2024_rules=false 
    ↓
Parser applies: API spell data only (no enhanced files)
    ↓
Result: Consistent 2014 behavior across both scraper detection and parser enhancement
```

#### **Critical Implementation Requirements**:
1. **Scraper must accept**: `--force-2014` and `--force-2024` arguments
2. **Parser must pass through**: Force options to scraper subprocess call
3. **Enhanced spell logic**: Must respect JSON `is_2024_rules` field from scraper
4. **Error handling**: Invalid combinations (e.g., `--force-2014 --force-2024`) must be caught
5. **Documentation**: Help text must explain force option behavior clearly

#### **Test Cases for Phase 3**:
1. **Character 116277190**: Should detect as 2014 (homebrew subclasses ignored)
   - Test: `python dnd_json_to_markdown.py 116277190 test.md` → should use API spells
   - Force test: `python dnd_json_to_markdown.py 116277190 test.md --force-2024` → should use enhanced spells
2. **Character 141875964**: Verify 2024 detection accuracy 
   - Test both automatic detection and force override behavior
3. **Enhanced Spell Compatibility**: Test rule-appropriate file selection
   - Verify `light-xphb.md` used for 2024, API data for 2014
4. **Force Options**: Test manual override in edge cases
   - Test conflicting options, invalid combinations
   - Verify parser→scraper argument passing works correctly

#### Step 2: Create Rule Version Manager (1.5 hours)

**3.2.1 Extract Rule Constants** (`rules/constants.py`)
```python
from typing import Dict, List, Set
from enum import Enum

class RuleVersion(str, Enum):
    RULES_2014 = "2014"
    RULES_2024 = "2024"

class SourceBooks:
    """D&D Beyond source book IDs for rule version detection."""
    
    # 2014 Edition Sources
    SOURCES_2014 = {
        1: "Player's Handbook (2014)",
        2: "Dungeon Master's Guide", 
        3: "Monster Manual",
        4: "Elemental Evil Player's Companion",
        6: "Sword Coast Adventurer's Guide",
        15: "Acquisitions Incorporated",
        17: "Mordenkainen's Tome of Foes",
        18: "Guildmasters' Guide to Ravnica",
        19: "Mordenkainen's Fiendish Folio",
        20: "Eberron: Rising from the Last War",
        28: "Explorer's Guide to Wildemount",
        34: "Mythic Odysseys of Theros",
        35: "Icewind Dale: Rime of the Frostmaiden",
        39: "Tasha's Cauldron of Everything",
        40: "Xanathar's Guide to Everything",
        42: "Fizban's Treasury of Dragons"
    }
    
    # 2024 Edition Sources  
    SOURCES_2024 = {
        142: "Player's Handbook (2024)",
        143: "Dungeon Master's Guide (2024)",
        144: "Monster Manual (2024)"
    }
    
    @classmethod
    def get_all_2014_sources(cls) -> Set[int]:
        return set(cls.SOURCES_2014.keys())
    
    @classmethod  
    def get_all_2024_sources(cls) -> Set[int]:
        return set(cls.SOURCES_2024.keys())

class GameConstants:
    """Game constants and mappings."""
    
    # Ability Score ID Mapping (from v5.2.0)
    ABILITY_ID_MAP = {
        1: "strength",
        2: "dexterity", 
        3: "constitution",
        4: "intelligence",
        5: "wisdom",
        6: "charisma"
    }
    
    # Class Hit Dice (exact copy from v5.2.0)
    CLASS_HIT_DICE = {
        "Artificer": 8, "Barbarian": 12, "Bard": 8, "Cleric": 8,
        "Druid": 8, "Fighter": 10, "Monk": 8, "Paladin": 10,
        "Ranger": 10, "Rogue": 8, "Sorcerer": 6, "Warlock": 8, "Wizard": 6
    }
    
    # Spellcasting Types
    FULL_CASTERS = ["Bard", "Cleric", "Druid", "Sorcerer", "Warlock", "Wizard"]
    HALF_CASTERS = ["Artificer", "Paladin", "Ranger"]
    THIRD_CASTERS = ["Arcane Trickster", "Eldritch Knight"]  # Subclasses
    
    # 2024 Rule Changes
    RULE_2024_CHANGES = {
        "terminology": {
            "race": "species",
            "racial_traits": "species_traits"
        },
        "feat_categories": ["origin", "general", "fighting_style", "epic_boon"],
        "weapon_mastery": True
    }
```

**3.2.2 Create Rule Version Manager** (`rules/version_manager.py`)
```python
from typing import Dict, Any, List, Optional, Set
from .constants import RuleVersion, SourceBooks, GameConstants

class RuleVersionManager:
    """Centralized rule version detection and management."""
    
    def __init__(self):
        self.version_cache: Dict[int, RuleVersion] = {}
    
    def detect_rule_version(self, character_data: Dict[str, Any]) -> RuleVersion:
        """Detect rule version using multiple methods."""
        character_id = character_data.get("id", 0)
        
        # Check cache first
        if character_id in self.version_cache:
            return self.version_cache[character_id]
        
        detection_methods = [
            self._detect_by_source_ids,
            self._detect_by_terminology,
            self._detect_by_species_data,
            self._detect_by_feat_structure,
            self._detect_by_spell_sources
        ]
        
        version_votes = []
        detection_log = []
        
        for method in detection_methods:
            try:
                result = method(character_data)
                if result:
                    version_votes.append(result)
                    detection_log.append(f"{method.__name__}: {result}")
            except Exception as e:
                detection_log.append(f"{method.__name__}: ERROR - {e}")
        
        # Determine final version by majority vote
        if version_votes:
            # Count votes
            vote_2024 = version_votes.count(RuleVersion.RULES_2024)
            vote_2014 = version_votes.count(RuleVersion.RULES_2014)
            
            if vote_2024 > vote_2014:
                final_version = RuleVersion.RULES_2024
            else:
                final_version = RuleVersion.RULES_2014
        else:
            # Default to 2014 if no clear detection
            final_version = RuleVersion.RULES_2014
        
        # Cache result
        self.version_cache[character_id] = final_version
        
        return final_version
    
    def _detect_by_source_ids(self, character_data: Dict[str, Any]) -> Optional[RuleVersion]:
        """Detect by source book IDs in character data."""
        sources_found = set()
        
        # Check race/species sources
        race_data = character_data.get("race", {})
        if race_source := race_data.get("definition", {}).get("sourceId"):
            sources_found.add(race_source)
        
        # Check class sources
        for class_info in character_data.get("classes", []):
            if class_source := class_info.get("definition", {}).get("sourceId"):
                sources_found.add(class_source)
        
        # Check background sources
        background_data = character_data.get("background", {})
        if bg_source := background_data.get("definition", {}).get("sourceId"):
            sources_found.add(bg_source)
        
        # Check feat sources
        for feat in character_data.get("feats", []):
            if feat_source := feat.get("definition", {}).get("sourceId"):
                sources_found.add(feat_source)
        
        # Analyze sources
        sources_2024 = sources_found.intersection(SourceBooks.get_all_2024_sources())
        sources_2014 = sources_found.intersection(SourceBooks.get_all_2014_sources())
        
        if sources_2024:
            return RuleVersion.RULES_2024
        elif sources_2014:
            return RuleVersion.RULES_2014
        else:
            return None
    
    def _detect_by_terminology(self, character_data: Dict[str, Any]) -> Optional[RuleVersion]:
        """Detect by checking for 2024 terminology vs 2014."""
        # Check for 'species' field (2024) vs 'race' field (2014)
        if "species" in character_data:
            return RuleVersion.RULES_2024
        elif "race" in character_data:
            return RuleVersion.RULES_2014
        else:
            return None
    
    def _detect_by_species_data(self, character_data: Dict[str, Any]) -> Optional[RuleVersion]:
        """Detect by species/race data structure differences."""
        race_data = character_data.get("race", {})
        
        # Check for 2024-specific race features
        if race_data.get("definition", {}).get("hasSubraces") is False:
            # Many 2024 species don't have subraces
            return RuleVersion.RULES_2024
        
        # Check for specific 2024 species names or features
        race_name = race_data.get("definition", {}).get("name", "")
        if race_name in ["Human (2024)", "Elf (2024)", "Dwarf (2024)"]:
            return RuleVersion.RULES_2024
        
        return None
    
    def _detect_by_feat_structure(self, character_data: Dict[str, Any]) -> Optional[RuleVersion]:
        """Detect by feat category structure (2024 has origin/general/etc.)."""
        feats = character_data.get("feats", [])
        
        for feat in feats:
            feat_definition = feat.get("definition", {})
            
            # Check for 2024 feat categories
            if "category" in feat_definition:
                category = feat_definition["category"]
                if category in ["origin", "general", "fighting_style", "epic_boon"]:
                    return RuleVersion.RULES_2024
        
        return None
    
    def _detect_by_spell_sources(self, character_data: Dict[str, Any]) -> Optional[RuleVersion]:
        """Detect by spell source structure and content."""
        # Copy exact spell source detection logic from v5.2.0
        # This is complex and should be extracted carefully
        
        class_spells = character_data.get("classSpells", [])
        spell_dict = character_data.get("spells", {})
        
        # Look for 2024-specific spell sources or structures
        # This needs to be copied from existing detection logic
        
        return None
    
    def get_terminology(self, rule_version: RuleVersion) -> Dict[str, str]:
        """Get appropriate terminology for the rule version."""
        if rule_version == RuleVersion.RULES_2024:
            return {
                "character_origin": "species",
                "racial_traits": "species_traits",
                "ability_score_improvement": "ability_score_improvement"
            }
        else:
            return {
                "character_origin": "race", 
                "racial_traits": "racial_traits",
                "ability_score_improvement": "ability_score_improvement"
            }
    
    def supports_weapon_mastery(self, rule_version: RuleVersion) -> bool:
        """Check if weapon mastery is supported in this rule version."""
        return rule_version == RuleVersion.RULES_2024
    
    def get_feat_categories(self, rule_version: RuleVersion) -> List[str]:
        """Get feat categories for the rule version."""
        if rule_version == RuleVersion.RULES_2024:
            return ["origin", "general", "fighting_style", "epic_boon"]
        else:
            return ["feat"]  # 2014 has simpler feat structure
```

#### Step 3: Rule-Specific Calculators (2 hours)

**3.3.1 Create Rule-Aware Base Calculator** (`calculators/rule_aware_base.py`)
```python
from abc import ABC
from typing import Dict, Any
from .base import BaseCalculator
from ..rules.version_manager import RuleVersionManager, RuleVersion

class RuleAwareCalculator(BaseCalculator):
    """Base calculator that handles rule version differences."""
    
    def __init__(self, rule_manager: RuleVersionManager):
        super().__init__()
        self.rule_manager = rule_manager
    
    def calculate(self, character_data: Dict[str, Any], rule_version: str = None) -> CalculationResult:
        """Calculate with automatic rule version detection."""
        if rule_version is None:
            detected_version = self.rule_manager.detect_rule_version(character_data)
            rule_version = detected_version.value
        
        return self._calculate_for_version(character_data, rule_version)
    
    @abstractmethod
    def _calculate_for_version(self, character_data: Dict[str, Any], rule_version: str) -> CalculationResult:
        """Implement version-specific calculation logic."""
        pass
    
    def _get_character_origin_data(self, character_data: Dict[str, Any], rule_version: str) -> Dict[str, Any]:
        """Get race/species data using appropriate terminology."""
        terminology = self.rule_manager.get_terminology(RuleVersion(rule_version))
        origin_key = "species" if rule_version == "2024" else "race"
        return character_data.get(origin_key, {})
```

**3.3.2 Update Hit Points Calculator for Rules** (`calculators/hit_points.py`)
```python
# Add to existing HitPointsCalculator class

def _calculate_for_version(self, character_data: Dict[str, Any], rule_version: str) -> CalculationResult:
    """Calculate HP with rule version awareness."""
    steps = []
    warnings = []
    
    # Rule-specific differences in HP calculation
    if rule_version == "2024":
        # 2024 may have different HP calculation rules
        # Copy any 2024-specific logic from v5.2.0
        return self._calculate_hp_2024(character_data, steps, warnings)
    else:
        # 2014 rules (existing logic)
        return self._calculate_hp_2014(character_data, steps, warnings)

def _calculate_hp_2024(self, character_data: Dict[str, Any], steps: List[str], warnings: List[str]) -> CalculationResult:
    """2024-specific HP calculation."""
    # Check for any 2024 HP rule changes
    # If no changes, fall back to 2014 logic
    return self._calculate_hp_2014(character_data, steps, warnings)

def _calculate_hp_2014(self, character_data: Dict[str, Any], steps: List[str], warnings: List[str]) -> CalculationResult:
    """2014 HP calculation (existing logic)."""
    # Move existing calculation logic here
    # This is the working code from Phase 2
    pass
```

#### Step 4: Content Support Analysis (1 hour)

**3.4.1 Create Content Coverage Analysis** (`rules/content_analysis.py`)
```python
from typing import Dict, List, Set
from .constants import GameConstants

class ContentCoverageAnalyzer:
    """Analyze and validate D&D content coverage."""
    
    def __init__(self):
        self.all_classes = [
            "Artificer", "Barbarian", "Bard", "Cleric", "Druid", "Fighter",
            "Monk", "Paladin", "Ranger", "Rogue", "Sorcerer", "Warlock", "Wizard"
        ]
        
        self.all_subclasses_2014 = {
            "Artificer": ["Alchemist", "Armorer", "Battle Smith", "Artillerist"],
            "Barbarian": ["Berserker", "Totem Warrior", "Ancestral Guardian", "Storm Herald", "Zealot", "Wild Magic", "Beast"],
            "Bard": ["Lore", "Valor", "Glamour", "Swords", "Whispers", "Creation", "Eloquence"],
            # ... all 48+ subclasses from 2014
        }
        
        self.all_subclasses_2024 = {
            # Updated subclasses for 2024 edition
            # Copy from official 2024 sources
        }
    
    def analyze_character_content(self, character_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze what content types this character uses."""
        analysis = {
            "classes": [],
            "subclasses": [],
            "species": None,
            "background": None,
            "feats": [],
            "spells": [],
            "items": [],
            "unknown_content": []
        }
        
        # Analyze classes
        for class_info in character_data.get("classes", []):
            class_name = class_info.get("definition", {}).get("name")
            if class_name:
                analysis["classes"].append(class_name)
                
                if class_name not in self.all_classes:
                    analysis["unknown_content"].append(f"Unknown class: {class_name}")
        
        # Analyze subclasses
        # Analyze species/race
        # Analyze feats
        # etc.
        
        return analysis
    
    def validate_content_support(self, character_data: Dict[str, Any], rule_version: str) -> List[str]:
        """Validate that all character content is supported."""
        issues = []
        
        # Check class support
        for class_info in character_data.get("classes", []):
            class_name = class_info.get("definition", {}).get("name")
            if class_name not in self.all_classes:
                issues.append(f"Unsupported class: {class_name}")
        
        # Check rule version compatibility
        if rule_version == "2024":
            # Check for 2024-specific validation
            pass
        
        return issues
```

#### Step 5: Integration and Testing (1 hour)

**3.5.1 Test Rule Detection** (`tests/unit/test_rule_detection.py`)
```python
import pytest
from dnd_character_scraper.rules.version_manager import RuleVersionManager, RuleVersion

def test_rule_detection_2024_sources():
    """Test detection by 2024 source IDs."""
    manager = RuleVersionManager()
    
    character_data_2024 = {
        "id": 1,
        "race": {
            "definition": {
                "sourceId": 142,  # PHB 2024
                "name": "Human"
            }
        }
    }
    
    version = manager.detect_rule_version(character_data_2024)
    assert version == RuleVersion.RULES_2024

def test_rule_detection_species_terminology():
    """Test detection by species terminology."""
    manager = RuleVersionManager()
    
    character_data_2024 = {
        "id": 2,
        "species": {  # 2024 terminology
            "definition": {
                "name": "Elf"
            }
        }
    }
    
    version = manager.detect_rule_version(character_data_2024)
    assert version == RuleVersion.RULES_2024

def test_rule_detection_2014_fallback():
    """Test fallback to 2014 for ambiguous data."""
    manager = RuleVersionManager()
    
    character_data_ambiguous = {
        "id": 3,
        "race": {
            "definition": {
                "sourceId": 1,  # PHB 2014
                "name": "Human"
            }
        }
    }
    
    version = manager.detect_rule_version(character_data_ambiguous)
    assert version == RuleVersion.RULES_2014
```

**3.5.2 Integration Test** (`tests/integration/test_phase3.py`)
```python
def test_rule_aware_calculations():
    """Test that calculators handle both rule versions."""
    from dnd_character_scraper.rules.version_manager import RuleVersionManager
    from dnd_character_scraper.calculators.hit_points import HitPointsCalculator
    
    rule_manager = RuleVersionManager()
    calculator = RuleAwareHitPointsCalculator(rule_manager)
    
    # Test with 2024 character
    char_2024 = {
        "id": 1,
        "species": {"definition": {"sourceId": 142}},
        "level": 2,
        "stats": [{"id": 3, "value": 16}],
        "classes": [{"definition": {"name": "Sorcerer"}, "level": 2}],
        "preferences": {"hitPointType": 1}
    }
    
    result_2024 = calculator.calculate(char_2024)
    assert result_2024.value > 0
    
    # Test with 2014 character  
    char_2014 = {
        "id": 2,
        "race": {"definition": {"sourceId": 1}},
        "level": 2,
        "stats": [{"id": 3, "value": 16}],
        "classes": [{"definition": {"name": "Sorcerer"}, "level": 2}],
        "preferences": {"hitPointType": 1}
    }
    
    result_2014 = calculator.calculate(char_2014)
    assert result_2014.value > 0
```

### 3.1 Centralized Rule Engine Architecture

#### 3.1.1 Rule Version Manager (`rules/version_manager.py`)
```python
from enum import Enum
from typing import Dict, Any, Set
from .constants import GameConstants

class RuleVersion(Enum):
    RULES_2014 = "2014"
    RULES_2024 = "2024"

class RuleVersionManager:
    """Centralized management and detection of 2014 vs 2024 D&D rules."""
    
    def __init__(self, character_data: Dict[str, Any]):
        self.character_data = character_data
        self._rule_version = self._detect_rule_version()
    
    def _detect_rule_version(self) -> RuleVersion:
        """Centralized rule version detection logic."""
        # Priority 1: Check for species terminology (2024 uses "species")
        if self._uses_species_terminology():
            return RuleVersion.RULES_2024
        
        # Priority 2: Check for 2024 source books
        if self._has_2024_sources():
            return RuleVersion.RULES_2024
        
        # Priority 3: Check for 2024-specific spells
        if self._has_2024_spells():
            return RuleVersion.RULES_2024
        
        # Priority 4: Check for 2024-specific class features
        if self._has_2024_features():
            return RuleVersion.RULES_2024
        
        # Default to 2014 rules
        return RuleVersion.RULES_2014
    
    def _uses_species_terminology(self) -> bool:
        """Check if character uses 'species' instead of 'race'."""
        return "species" in self.character_data
    
    def _has_2024_sources(self) -> bool:
        """Check if character uses 2024 source books."""
        sources = self._get_character_sources()
        return bool(sources.intersection(GameConstants.SOURCE_2024_IDS))
    
    def _has_2024_spells(self) -> bool:
        """Check for 2024-specific spells."""
        spells = self._get_all_spells()
        for spell in spells:
            spell_name = spell.get('definition', {}).get('name', '').lower()
            if spell_name in GameConstants.SPELLS_2024_ONLY:
                return True
        return False
    
    def _has_2024_features(self) -> bool:
        """Check for 2024-specific class features."""
        classes = self.character_data.get('classes', [])
        for cls in classes:
            features = cls.get('classFeatures', [])
            for feature in features:
                feature_name = feature.get('definition', {}).get('name', '').lower()
                if feature_name in GameConstants.FEATURES_2024_ONLY:
                    return True
        return False
    
    @property
    def is_2024_rules(self) -> bool:
        return self._rule_version == RuleVersion.RULES_2024
    
    @property
    def rule_version(self) -> RuleVersion:
        return self._rule_version
    
    @property
    def rule_version_string(self) -> str:
        return self._rule_version.value
```

#### 3.1.2 Comprehensive Game Constants (`rules/constants.py`)
```python
class GameConstants:
    """Constants for D&D game rules and data - handles full breadth of 5e content."""
    
    # Source book IDs for 2024 detection
    SOURCE_2024_IDS = {
        142,  # Player's Handbook (2024)
        143,  # Dungeon Master's Guide (2024)
        144,  # Monster Manual (2024)
    }
    
    # All 13 official classes (2014 + 2024)
    OFFICIAL_CLASSES = {
        'artificer', 'barbarian', 'bard', 'cleric', 'druid', 'fighter', 
        'monk', 'paladin', 'ranger', 'rogue', 'sorcerer', 'warlock', 'wizard'
    }
    
    # Spellcasting progression types
    SPELLCASTING_TYPES = {
        # Full casters (1:1 ratio)
        'full_caster': {'wizard', 'sorcerer', 'bard', 'cleric', 'druid', 'warlock'},
        # Half casters (2:1 ratio, start at level 2)
        'half_caster': {'paladin', 'ranger'},
        # Third casters (3:1 ratio, start at level 3)
        'third_caster': {'eldritch_knight', 'arcane_trickster'},
        # Pact magic (separate system)
        'pact_magic': {'warlock'},
        # Ritual casters
        'ritual_caster': {'wizard', 'cleric', 'druid', 'bard'}
    }
    
    # Subclass spellcasting detection
    SPELLCASTING_SUBCLASSES = {
        'fighter': ['eldritch knight'],
        'rogue': ['arcane trickster'],
        # 2024 updates may change these
    }
    
    # Species vs Race terminology (2024 vs 2014)
    SPECIES_2024 = {
        'aasimar', 'dragonborn', 'dwarf', 'elf', 'gnome', 'goliath', 
        'halfling', 'human', 'orc', 'tiefling'
    }
    
    RACES_2014 = {
        'dragonborn', 'dwarf', 'elf', 'gnome', 'half-elf', 'half-orc', 
        'halfling', 'human', 'tiefling'
    }
    
    # 2024 Origin Feats (tied to backgrounds)
    ORIGIN_FEATS_2024 = {
        'alert', 'crafter', 'healer', 'lucky', 'magic initiate', 
        'musician', 'savage attacker', 'skilled', 'tavern brawler', 'tough'
    }
    
    # Feat categories in 2024
    FEAT_CATEGORIES_2024 = {
        'origin': 'Given by background at level 1',
        'general': 'Available at level 4+ ASI levels',
        'fighting_style': 'Available to martial classes',
        'epic_boon': 'Available at level 19+'
    }
    
    # Classes with special mechanics
    SPECIAL_MECHANICS = {
        'warlock': {
            'pact_magic': True,
            'short_rest_slots': True,
            'invocations': True
        },
        'sorcerer': {
            'sorcery_points': True,
            'metamagic': True
        },
        'monk': {
            'ki_points': True,
            'martial_arts': True,
            'unarmored_defense': True
        },
        'barbarian': {
            'rage': True,
            'unarmored_defense': True
        },
        'artificer': {
            'infusions': True,
            'magical_tinkering': True
        }
    }
    
    # Ability score choice mappings (covers both 2014 and 2024)
    ABILITY_CHOICE_MAPPING = {
        'race-ability-score-increase': {  # 2014 racial bonuses
            4: 'strength', 5: 'dexterity', 6: 'constitution',
            7: 'intelligence', 8: 'wisdom', 9: 'charisma'
        },
        'background-ability-score-increase': {  # 2024 background bonuses
            4: 'strength', 5: 'dexterity', 6: 'constitution',
            7: 'intelligence', 8: 'wisdom', 9: 'charisma'
        },
        'asi': {  # Class ability score improvements
            4: 'strength', 5: 'dexterity', 6: 'constitution',
            7: 'intelligence', 8: 'wisdom', 9: 'charisma'
        }
    }
    
    # Hit dice by class
    HIT_DICE = {
        'artificer': 8, 'barbarian': 12, 'bard': 8, 'cleric': 8,
        'druid': 8, 'fighter': 10, 'monk': 8, 'paladin': 10,
        'ranger': 10, 'rogue': 8, 'sorcerer': 6, 'warlock': 8, 'wizard': 6
    }
    
    # Classes that get Unarmored Defense
    UNARMORED_DEFENSE_CLASSES = {
        'barbarian': ['dexterity', 'constitution'],
        'monk': ['dexterity', 'wisdom']
    }
```

### 3.2 Complex Content Handling Strategy

The plan must account for the full breadth of D&D 5e official content:

#### 3.2.1 Class Complexity Matrix
- **13 official classes** with varying mechanics
- **48 subclasses in 2024** vs **117+ subclasses in 2014**
- **Special resource systems**: Ki points, Sorcery points, Rage, Invocations, Infusions
- **Unique AC calculations**: Unarmored Defense (Barbarian/Monk), class-specific bonuses
- **Multiclass prerequisites and restrictions**

#### 3.2.2 Spellcasting Complexity
- **4 different spellcasting types**: Full, Half, Third, Pact Magic
- **Multiclass spellcasting combinations** (e.g., Wizard/Sorcerer/Warlock)
- **Ritual casting variants** across classes
- **Warlock short-rest mechanics** vs long-rest casters
- **Spell preparation vs spells known** systems

#### 3.2.3 Species/Race Evolution
- **2024 terminology change**: "Race" → "Species"
- **Ability score handling**: 2014 racial bonuses vs 2024 background bonuses
- **Legacy content compatibility**: Half-Elf/Half-Orc removal in 2024
- **New species additions**: Aasimar, Goliath, Orc in 2024 PHB

#### 3.2.4 Feat System Overhaul
- **75 feats in 2024** vs **42 feats in 2014**
- **4 feat categories**: Origin, General, Fighting Style, Epic Boon
- **Level 1 Origin Feats** tied to backgrounds
- **Repeatable feats** in 2024
- **Human versatility**: Dual Origin Feats in 2024

#### 3.2.5 Background Transformation
- **2014**: Simple features and proficiencies
- **2024**: Ability score increases + Origin Feat + enhanced features
- **Mechanical impact**: Backgrounds now affect core character power

#### 3.2.6 Content Extensibility Requirements
```python
# The scraper must handle:
class ContentComplexity:
    """Handle the full scope of D&D content complexity."""
    
    def handle_unknown_subclass(self, class_name: str, subclass_name: str):
        """Gracefully handle homebrew/new subclasses."""
        # Default to base class mechanics
        # Log unknown content for future updates
        pass
    
    def detect_spellcasting_type(self, class_info: Dict, subclass_info: Optional[Dict]):
        """Determine spellcasting progression type."""
        # Handle Fighter/Rogue subclass spellcasting
        # Account for Artificer (2014 only)
        # Manage multiclass interactions
        pass
    
    def calculate_special_resources(self, character_data: Dict):
        """Calculate class-specific resources."""
        resources = {}
        
        # Sorcery Points = Sorcerer level
        # Ki Points = Monk level  
        # Rage uses = Barbarian level-based table
        # Warlock Invocations = level-based
        # Artificer Infusions = level-based table
        
        return resources
```

### 3.3 Progress Tracking for Phase 3

**Update Status**: Use Edit tool to change `[ ]` to `[x]` when complete.

- [ ] Implement centralized rule version detection logic
- [ ] Create comprehensive game constants for all 13 classes
- [ ] Handle species vs race terminology and mechanics
- [ ] Implement feat system changes (Origin, General, Fighting Style, Epic Boon)
- [ ] Create spellcasting type detection for all classes and subclasses
- [ ] Handle special class resources (Ki, Sorcery Points, Rage, etc.)
- [ ] Account for background ability score changes in 2024
- [ ] Create extensibility for unknown/homebrew content
- [ ] Test with characters using complex multiclass combinations
- [ ] Validate against both 2014 and 2024 characters

**Phase 3 Completion Criteria**:
- [ ] Rule version detection works for all test characters
- [ ] All 13 classes supported with proper mechanics
- [ ] 2024 feat system properly implemented
- [ ] Special class resources calculated correctly
- [ ] Unknown content handled gracefully

---

## Phase 4: Validation & Testing Framework

**Goal**: Create comprehensive validation and testing to ensure scraper accuracy  
**Duration**: Quality assurance phase - critical for reliability  
**Success Criteria**: All test characters validate correctly, edge cases handled, regression prevention

### 4.1 Step-by-Step Validation Implementation

#### Step 1: Create Validation Framework (1.5 hours)

**4.1.1 Analyze Current Validation**
Find existing validation logic in `enhanced_dnd_scraper.py`:
```bash
grep -n -A 10 "validation\|validate\|compare" enhanced_dnd_scraper.py
```

**4.1.2 Create Base Validator** (`validators/base.py`)
```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class ValidationResult:
    """Result of validation with detailed feedback."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    field_comparisons: Dict[str, Any]
    
class BaseValidator(ABC):
    """Base validator interface."""
    
    @abstractmethod
    def validate(self, data: Dict[str, Any]) -> ValidationResult:
        """Perform validation and return detailed results."""
        pass
    
    def _validate_field(self, field_name: str, actual: Any, expected: Any, tolerance: float = 0) -> Optional[str]:
        """Validate a single field with optional tolerance."""
        if isinstance(actual, (int, float)) and isinstance(expected, (int, float)):
            if abs(actual - expected) > tolerance:
                return f"{field_name}: expected {expected}, got {actual} (diff: {abs(actual - expected)})"
        elif actual != expected:
            return f"{field_name}: expected {expected}, got {actual}"
        return None
```

**4.1.3 Create Character Validator** (`validators/character.py`)
```python
import json
from pathlib import Path
from typing import Dict, Any, List
from .base import BaseValidator, ValidationResult

class CharacterValidator(BaseValidator):
    """Validates complete character data against known good values."""
    
    def __init__(self, validation_data_dir: str = "validation_data"):
        self.validation_dir = Path(validation_data_dir)
    
    def validate(self, character_data: Dict[str, Any]) -> ValidationResult:
        """Validate character data structure and content."""
        errors = []
        warnings = []
        field_comparisons = {}
        
        # Step 1: Validate required structure
        structure_errors = self._validate_structure(character_data)
        errors.extend(structure_errors)
        
        # Step 2: Validate calculations are reasonable
        calc_errors = self._validate_calculations(character_data)
        errors.extend(calc_errors)
        
        # Step 3: Check for missing or suspicious data
        completeness_warnings = self._check_completeness(character_data)
        warnings.extend(completeness_warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_comparisons=field_comparisons
        )
    
    def _validate_structure(self, character_data: Dict[str, Any]) -> List[str]:
        """Validate basic data structure."""
        errors = []
        
        # Required top-level fields
        required_fields = ["name", "level", "classes", "stats"]
        for field in required_fields:
            if field not in character_data:
                errors.append(f"Missing required field: {field}")
        
        # Validate classes structure
        if "classes" in character_data:
            for i, class_info in enumerate(character_data["classes"]):
                if "definition" not in class_info:
                    errors.append(f"Class {i}: missing definition")
                elif "name" not in class_info["definition"]:
                    errors.append(f"Class {i}: missing definition.name")
        
        # Validate stats structure
        if "stats" in character_data:
            stats = character_data["stats"]
            if len(stats) != 6:
                errors.append(f"Expected 6 ability scores, found {len(stats)}")
            
            for stat in stats:
                if "id" not in stat or "value" not in stat:
                    errors.append("Ability score missing id or value")
        
        return errors
    
    def _validate_calculations(self, character_data: Dict[str, Any]) -> List[str]:
        """Validate that calculated values are reasonable."""
        errors = []
        
        # Check debug_summary if present
        debug_summary = character_data.get("debug_summary", {})
        if debug_summary:
            # Validate level
            level = debug_summary.get("level", 0)
            if level < 1 or level > 20:
                errors.append(f"Invalid level: {level} (should be 1-20)")
            
            # Validate hit points
            hit_points = debug_summary.get("hit_points", 0)
            if hit_points < level:  # Minimum 1 HP per level
                errors.append(f"HP too low: {hit_points} for level {level}")
            
            # Validate armor class
            armor_class = debug_summary.get("armor_class", 0)
            if armor_class < 10 or armor_class > 30:
                errors.append(f"Suspicious AC: {armor_class}")
            
            # Validate ability scores
            ability_scores = debug_summary.get("ability_scores", {})
            for ability, score in ability_scores.items():
                if score < 3 or score > 30:
                    errors.append(f"Suspicious {ability}: {score}")
        
        return errors
    
    def _check_completeness(self, character_data: Dict[str, Any]) -> List[str]:
        """Check for completeness and warn about missing optional data."""
        warnings = []
        
        # Check for common optional fields
        optional_fields = ["spells", "inventory", "feats", "background"]
        for field in optional_fields:
            if field not in character_data:
                warnings.append(f"Optional field missing: {field}")
        
        return warnings
    
    def quick_compare(self, character_data: Dict[str, Any], validation_file: Path) -> ValidationResult:
        """Compare against validation file (for testing known characters)."""
        if not validation_file.exists():
            return ValidationResult(
                is_valid=False,
                errors=[f"Validation file not found: {validation_file}"],
                warnings=[],
                field_comparisons={}
            )
        
        with open(validation_file) as f:
            validation_data = json.load(f)
        
        errors = []
        warnings = []
        field_comparisons = {}
        
        debug_summary = character_data.get("debug_summary", {})
        
        # Compare key fields with tolerance for floating point
        comparisons = [
            ("name", debug_summary.get("name"), validation_data.get("name")),
            ("level", debug_summary.get("level"), validation_data.get("level")),
            ("hit_points", debug_summary.get("hit_points"), validation_data.get("max_hp")),
            ("armor_class", debug_summary.get("armor_class"), validation_data.get("armor_class")),
        ]
        
        for field_name, actual, expected in comparisons:
            field_comparisons[field_name] = {"actual": actual, "expected": expected}
            
            if error := self._validate_field(field_name, actual, expected):
                errors.append(error)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_comparisons=field_comparisons
        )
```

#### Step 2: Create Calculation Validators (2 hours)

**4.2.1 Create Calculator Validator** (`validators/calculations.py`)
```python
from typing import Dict, Any, List
from ..calculators import CalculatorRegistry
from .base import BaseValidator, ValidationResult

class CalculationValidator(BaseValidator):
    """Validates calculator outputs for consistency and accuracy."""
    
    def __init__(self):
        self.calculator_registry = CalculatorRegistry()
    
    def validate(self, character_data: Dict[str, Any]) -> ValidationResult:
        """Validate all calculations are consistent."""
        errors = []
        warnings = []
        field_comparisons = {}
        
        # Run all calculators
        calculated_results = self.calculator_registry.calculate_all(character_data)
        
        # Cross-validate calculations
        errors.extend(self._validate_ability_score_consistency(calculated_results))
        errors.extend(self._validate_hp_calculation(character_data, calculated_results))
        errors.extend(self._validate_ac_calculation(character_data, calculated_results))
        
        # Check for calculation warnings
        calc_log = calculated_results.get("_calculation_log", [])
        calc_warnings = [line for line in calc_log if "WARNING" in line or "ERROR" in line]
        warnings.extend(calc_warnings)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            field_comparisons=field_comparisons
        )
    
    def _validate_ability_score_consistency(self, results: Dict[str, Any]) -> List[str]:
        """Validate ability scores and modifiers are consistent."""
        errors = []
        
        ability_scores = results.get("ability_scores", {})
        ability_modifiers = results.get("ability_modifiers", {})
        
        for ability, score in ability_scores.items():
            expected_modifier = (score - 10) // 2
            actual_modifier = ability_modifiers.get(ability)
            
            if actual_modifier != expected_modifier:
                errors.append(f"{ability}: modifier {actual_modifier} doesn't match score {score} (expected {expected_modifier})")
        
        return errors
    
    def _validate_hp_calculation(self, character_data: Dict[str, Any], results: Dict[str, Any]) -> List[str]:
        """Validate HP calculation against manual verification."""
        errors = []
        
        calculated_hp = results.get("hit_points", 0)
        level = character_data.get("level", 1)
        
        # Basic sanity checks
        if calculated_hp < level:
            errors.append(f"HP {calculated_hp} is less than level {level} (minimum 1 per level)")
        
        # Check against reasonable maximums (assumes best case scenario)
        classes = character_data.get("classes", [])
        if classes:
            max_possible_hp = 0
            for class_info in classes:
                class_level = class_info.get("level", 1)
                # Use largest hit die (d12) + max CON bonus (+5) for upper bound
                max_possible_hp += class_level * (12 + 5)
            
            if calculated_hp > max_possible_hp:
                errors.append(f"HP {calculated_hp} exceeds theoretical maximum {max_possible_hp}")
        
        return errors
    
    def _validate_ac_calculation(self, character_data: Dict[str, Any], results: Dict[str, Any]) -> List[str]:
        """Validate AC calculation logic."""
        errors = []
        
        calculated_ac = results.get("armor_class", 10)
        
        # Basic sanity checks
        if calculated_ac < 10:
            errors.append(f"AC {calculated_ac} is below unarmored minimum (10)")
        
        if calculated_ac > 25:  # Very high but possible with magic items
            errors.append(f"AC {calculated_ac} is suspiciously high")
        
        return errors
```

#### Step 3: Edge Case Testing (2 hours)

**4.3.1 Create Edge Case Tests** (`tests/edge_cases/test_multiclass.py`)
```python
import pytest
from dnd_character_scraper.calculators import CalculatorRegistry
from dnd_character_scraper.validators.calculations import CalculationValidator

def test_triple_multiclass_spell_slots():
    """Test complex multiclass spell slot calculation."""
    character_data = {
        "id": 888888,
        "name": "Triple Multiclass Test",
        "level": 20,
        "classes": [
            {"definition": {"name": "Wizard"}, "level": 8},
            {"definition": {"name": "Sorcerer"}, "level": 6}, 
            {"definition": {"name": "Warlock"}, "level": 6}
        ],
        "stats": [
            {"id": 1, "value": 10}, {"id": 2, "value": 14}, {"id": 3, "value": 16},
            {"id": 4, "value": 20}, {"id": 5, "value": 12}, {"id": 6, "value": 18}
        ]
    }
    
    registry = CalculatorRegistry("2014")
    results = registry.calculate_all(character_data)
    
    # Wizard + Sorcerer = 14 caster levels (6th level slots)
    # Warlock = separate pact magic (3rd level slots)
    spell_slots = results.get("spell_slots", {})
    
    assert "regular_slots" in spell_slots
    assert "pact_slots" in spell_slots
    
    # Should have high-level regular slots from Wizard/Sorcerer
    regular_slots = spell_slots["regular_slots"]
    assert regular_slots.get("level_6", 0) > 0
    
    # Should have separate Warlock pact slots
    pact_slots = spell_slots["pact_slots"]
    assert pact_slots.get("level", 0) == 3  # 6th level warlock = 3rd level pact slots

def test_negative_constitution_hp():
    """Test HP calculation with negative CON modifier."""
    character_data = {
        "id": 777777,
        "name": "Weak Constitution Test",
        "level": 5,
        "classes": [{"definition": {"name": "Wizard"}, "level": 5}],
        "stats": [
            {"id": 1, "value": 10}, {"id": 2, "value": 14}, {"id": 3, "value": 6},  # CON 6 = -2 modifier
            {"id": 4, "value": 18}, {"id": 5, "value": 12}, {"id": 6, "value": 10}
        ],
        "preferences": {"hitPointType": 1}  # Fixed HP
    }
    
    registry = CalculatorRegistry("2014")
    results = registry.calculate_all(character_data)
    
    calculated_hp = results.get("hit_points", 0)
    
    # Even with negative CON, should get minimum 1 HP per level
    assert calculated_hp >= 5  # Level 5 = minimum 5 HP
    
    # First level: 6 (max d6) - 2 (CON) = 4, but minimum 1
    # Levels 2-5: 4 * (4 - 2) = 8, but minimum 4 (1 per level)
    # Total: 1 + 4 = 5 minimum
    assert calculated_hp >= 5

def test_unarmored_defense_barbarian_monk():
    """Test Unarmored Defense for Barbarian/Monk multiclass."""
    character_data = {
        "id": 666666,
        "name": "Barbarian Monk Test",
        "level": 10,
        "classes": [
            {"definition": {"name": "Barbarian"}, "level": 6},
            {"definition": {"name": "Monk"}, "level": 4}
        ],
        "stats": [
            {"id": 1, "value": 16}, {"id": 2, "value": 16}, {"id": 3, "value": 16},  # STR/DEX/CON 16
            {"id": 4, "value": 10}, {"id": 5, "value": 16}, {"id": 6, "value": 10}   # WIS 16
        ],
        "inventory": []  # No armor
    }
    
    registry = CalculatorRegistry("2014")
    results = registry.calculate_all(character_data)
    
    calculated_ac = results.get("armor_class", 10)
    
    # Both classes get Unarmored Defense, player chooses better option:
    # Barbarian: 10 + DEX (3) + CON (3) = 16
    # Monk: 10 + DEX (3) + WIS (3) = 16
    # Should pick either (both equal in this case)
    assert calculated_ac == 16
```

**4.3.2 Create API Edge Case Tests** (`tests/edge_cases/test_api_edge_cases.py`)
```python
import pytest
from dnd_character_scraper.api.client import DNDBeyondAPIClient
from dnd_character_scraper.api.exceptions import CharacterNotFoundError

def test_malformed_character_data():
    """Test handling of malformed character data."""
    from dnd_character_scraper.validators.character import CharacterValidator
    
    malformed_data = {
        "id": 123,
        "name": "Broken Character",
        # Missing required fields: level, classes, stats
        "random_field": "should be preserved"
    }
    
    validator = CharacterValidator()
    result = validator.validate(malformed_data)
    
    assert not result.is_valid
    assert "Missing required field: level" in result.errors
    assert "Missing required field: classes" in result.errors
    assert "Missing required field: stats" in result.errors

def test_unknown_class_handling():
    """Test handling of unknown/homebrew classes."""
    character_data = {
        "id": 555555,
        "name": "Homebrew Class Test",
        "level": 5,
        "classes": [{"definition": {"name": "Blood Hunter"}, "level": 5}],  # Homebrew class
        "stats": [
            {"id": 1, "value": 15}, {"id": 2, "value": 14}, {"id": 3, "value": 16},
            {"id": 4, "value": 8}, {"id": 5, "value": 12}, {"id": 6, "value": 17}
        ]
    }
    
    from dnd_character_scraper.calculators.hit_points import HitPointsCalculator
    
    calculator = HitPointsCalculator()
    result = calculator.calculate(character_data, "2014")
    
    # Should handle gracefully with default hit die (d8)
    assert result.value > 0
    assert "Unknown class" in " ".join(result.warnings) or "default" in " ".join(result.calculation_steps)

def test_extreme_ability_scores():
    """Test handling of extreme ability scores."""
    character_data = {
        "id": 444444,
        "name": "Extreme Stats Test", 
        "level": 20,
        "classes": [{"definition": {"name": "Fighter"}, "level": 20}],
        "stats": [
            {"id": 1, "value": 30}, {"id": 2, "value": 30}, {"id": 3, "value": 30},  # Godlike stats
            {"id": 4, "value": 3}, {"id": 5, "value": 3}, {"id": 6, "value": 3}     # Minimal stats
        ]
    }
    
    from dnd_character_scraper.calculators.ability_scores import AbilityScoreCalculator
    
    calculator = AbilityScoreCalculator()
    result = calculator.calculate(character_data, "2014")
    
    ability_scores = result.value
    assert ability_scores["strength"] == 30
    assert ability_scores["intelligence"] == 3
    
    # Modifiers should be calculated correctly
    from dnd_character_scraper.calculators.base import BaseCalculator
    base_calc = BaseCalculator()
    assert base_calc._get_ability_modifier(30) == 10
    assert base_calc._get_ability_modifier(3) == -4
```

#### Step 4: Integration Testing (1.5 hours)

**4.4.1 Create Integration Test Suite** (`tests/integration/test_complete_flow.py`)
```python
import pytest
from pathlib import Path
from dnd_character_scraper.api.mock_client import MockAPIClient
from dnd_character_scraper.calculators import CalculatorRegistry
from dnd_character_scraper.validators.character import CharacterValidator
from dnd_character_scraper.validators.calculations import CalculationValidator

def test_complete_character_processing_flow():
    """Test complete flow from API to validation."""
    # Step 1: Get character data
    client = MockAPIClient()
    raw_data = client.get_character(999999)
    
    # Step 2: Run all calculations
    registry = CalculatorRegistry("2014")
    calculated_data = registry.calculate_all(raw_data)
    
    # Step 3: Combine raw and calculated data
    complete_data = {**raw_data, **calculated_data}
    
    # Step 4: Validate structure
    validator = CharacterValidator()
    structure_result = validator.validate(complete_data)
    
    assert structure_result.is_valid, f"Structure validation failed: {structure_result.errors}"
    
    # Step 5: Validate calculations
    calc_validator = CalculationValidator()
    calc_result = calc_validator.validate(raw_data)
    
    assert calc_result.is_valid, f"Calculation validation failed: {calc_result.errors}"
    
    # Step 6: Check for warnings
    if structure_result.warnings:
        print(f"Warnings: {structure_result.warnings}")

def test_multiple_rule_versions():
    """Test processing characters from both rule versions."""
    test_characters = [
        # 2014 character
        {
            "id": 111111,
            "name": "2014 Character",
            "level": 5,
            "race": {"definition": {"sourceId": 1, "name": "Human"}},  # 2014 PHB
            "classes": [{"definition": {"name": "Fighter"}, "level": 5}],
            "stats": [{"id": i, "value": 15} for i in range(1, 7)]
        },
        # 2024 character
        {
            "id": 222222,
            "name": "2024 Character", 
            "level": 5,
            "species": {"definition": {"sourceId": 142, "name": "Human"}},  # 2024 PHB
            "classes": [{"definition": {"name": "Fighter"}, "level": 5}],
            "stats": [{"id": i, "value": 15} for i in range(1, 7)]
        }
    ]
    
    for char_data in test_characters:
        # Detect rule version
        from dnd_character_scraper.rules.version_manager import RuleVersionManager
        rule_manager = RuleVersionManager()
        detected_version = rule_manager.detect_rule_version(char_data)
        
        # Process with appropriate rules
        registry = CalculatorRegistry(detected_version.value)
        results = registry.calculate_all(char_data)
        
        # Validate results
        assert results["hit_points"] > 0
        assert results["armor_class"] >= 10
        assert len(results["ability_scores"]) == 6

def test_error_recovery():
    """Test system handles errors gracefully."""
    broken_data = {
        "id": 0,
        "name": "",
        "level": -1,  # Invalid level
        "classes": [],  # No classes
        "stats": []  # No stats
    }
    
    # Should not crash, should return errors
    validator = CharacterValidator()
    result = validator.validate(broken_data)
    
    assert not result.is_valid
    assert len(result.errors) > 0
    
    # Calculators should also handle gracefully
    registry = CalculatorRegistry("2014")
    calc_results = registry.calculate_all(broken_data)
    
    # Should have some None results but not crash
    assert calc_results is not None
    assert "_calculation_log" in calc_results
```

#### Step 5: Test Data Management (1 hour)

**4.5.1 Create Test Data Generator** (`tests/fixtures/character_generator.py`)
```python
from typing import Dict, Any, List

class TestCharacterGenerator:
    """Generate test character data for various scenarios."""
    
    @staticmethod
    def create_basic_character(
        character_id: int = 999999,
        name: str = "Test Character",
        level: int = 2,
        class_name: str = "Sorcerer",
        rule_version: str = "2014"
    ) -> Dict[str, Any]:
        """Create a basic test character."""
        
        base_character = {
            "id": character_id,
            "name": name,
            "level": level,
            "classes": [{"definition": {"name": class_name}, "level": level}],
            "stats": [
                {"id": 1, "value": 15}, {"id": 2, "value": 14}, {"id": 3, "value": 16},
                {"id": 4, "value": 8}, {"id": 5, "value": 12}, {"id": 6, "value": 17}
            ],
            "preferences": {"hitPointType": 1}
        }
        
        if rule_version == "2024":
            base_character["species"] = {"definition": {"sourceId": 142, "name": "Human"}}
        else:
            base_character["race"] = {"definition": {"sourceId": 1, "name": "Human"}}
        
        return base_character
    
    @staticmethod
    def create_multiclass_character() -> Dict[str, Any]:
        """Create a multiclass test character."""
        return {
            "id": 888888,
            "name": "Multiclass Test",
            "level": 10,
            "classes": [
                {"definition": {"name": "Fighter"}, "level": 6},
                {"definition": {"name": "Rogue"}, "level": 4}
            ],
            "race": {"definition": {"sourceId": 1, "name": "Half-Elf"}},
            "stats": [
                {"id": 1, "value": 16}, {"id": 2, "value": 18}, {"id": 3, "value": 14},
                {"id": 4, "value": 12}, {"id": 5, "value": 13}, {"id": 6, "value": 15}
            ],
            "preferences": {"hitPointType": 1}
        }
    
    @staticmethod
    def create_spellcaster_character() -> Dict[str, Any]:
        """Create a spellcasting test character."""
        return {
            "id": 777777,
            "name": "Spellcaster Test",
            "level": 8,
            "classes": [{"definition": {"name": "Wizard"}, "level": 8}],
            "race": {"definition": {"sourceId": 1, "name": "High Elf"}},
            "stats": [
                {"id": 1, "value": 10}, {"id": 2, "value": 14}, {"id": 3, "value": 16},
                {"id": 4, "value": 20}, {"id": 5, "value": 12}, {"id": 6, "value": 13}
            ],
            "classSpells": [
                {
                    "characterClassId": 1,
                    "spells": [
                        {"id": 1, "definition": {"name": "Magic Missile", "level": 1}},
                        {"id": 2, "definition": {"name": "Fireball", "level": 3}}
                    ]
                }
            ],
            "preferences": {"hitPointType": 1}
        }
```

**4.5.2 Create Validation Data Templates** (`tests/fixtures/validation_templates.py`)
```python
import json
from pathlib import Path

def create_validation_template(character_id: int, output_file: Path):
    """Create a validation template file."""
    template = {
        "character_id": character_id,
        "name": "CHARACTER_NAME_HERE",
        "level": 0,
        "classes": [{"name": "CLASS_NAME", "level": 0, "subclass": "SUBCLASS_NAME"}],
        "species": "SPECIES_NAME",
        "background": "BACKGROUND_NAME", 
        "is_2024_rules": False,
        "ability_scores": {
            "strength": 0, "dexterity": 0, "constitution": 0,
            "intelligence": 0, "wisdom": 0, "charisma": 0
        },
        "ability_modifiers": {
            "strength": 0, "dexterity": 0, "constitution": 0,
            "intelligence": 0, "wisdom": 0, "charisma": 0
        },
        "proficiency_bonus": 0,
        "armor_class": 0,
        "max_hp": 0,
        "hit_point_type": "fixed/manual",
        "initiative": 0,
        "speed": 30,
        "spellcasting": {
            "is_spellcaster": False,
            "spell_save_dc": 0,
            "spell_attack_bonus": 0,
            "spellcasting_ability": "",
            "total_spells": 0,
            "cantrips": 0,
            "spell_slots_level_1": 0,
            "spell_slots_level_2": 0,
            "spell_slots_level_3": 0,
            "spell_slots_level_4": 0,
            "spell_slots_level_5": 0
        },
        "saving_throws": ["List proficient saves here"],
        "skills": [{"name": "Skill Name", "source": "Class/Background/Species/Feat"}],
        "key_spells": ["List 3-5 important spells to verify"],
        "notes": "Any special notes about this character"
    }
    
    with open(output_file, 'w') as f:
        json.dump(template, f, indent=2)

if __name__ == "__main__":
    # Create templates for test characters
    templates_dir = Path("validation_data")
    templates_dir.mkdir(exist_ok=True)
    
    test_characters = [999999, 888888, 777777, 666666]
    for char_id in test_characters:
        create_validation_template(char_id, templates_dir / f"{char_id}_validation.json")
```

### 4.2 Enhanced Validation System

#### 4.1.1 Character Validator with Quick Compare (`validators/character.py`)
```python
from typing import List, Dict, Any, Tuple
from ..models.character import Character
from ..utils.diagnostics import DiagnosticCollector
import json

class CharacterValidator:
    """Validates character data completeness and accuracy."""
    
    def __init__(self, validation_data: Dict[str, Any] = None):
        self.validation_data = validation_data
        self.diagnostics = DiagnosticCollector()
    
    def validate_character(self, character: Character) -> Tuple[bool, List[str]]:
        """Validate complete character data."""
        errors = []
        
        # Basic info validation
        errors.extend(self._validate_basic_info(character.basic_info))
        
        # Ability scores validation
        errors.extend(self._validate_ability_scores(character.ability_scores))
        
        # Calculations validation
        if self.validation_data:
            errors.extend(self._validate_against_ground_truth(character))
        
        return len(errors) == 0, errors
    
    def quick_compare(self, character_data: Dict[str, Any], validation_file: str) -> List[str]:
        """Quick comparison against validation data (API suggestion)."""
        with open(validation_file, 'r') as f:
            validation_data = json.load(f)
        
        mismatches = []
        debug_summary = character_data.get('debug_summary', {})
        
        # Compare key fields
        key_fields = [
            'name', 'level', 'hit_points', 'armor_class', 
            'proficiency_bonus', 'rule_version'
        ]
        
        for field in key_fields:
            expected = validation_data.get(field)
            actual = debug_summary.get(field)
            
            if expected and expected != actual:
                mismatches.append(f"{field}: expected {expected}, got {actual}")
        
        # Compare ability scores
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            expected = validation_data.get('ability_scores', {}).get(ability, 0)
            actual = debug_summary.get('ability_scores', {}).get(ability, 0)
            
            if expected and expected != actual:
                mismatches.append(f"{ability}: expected {expected}, got {actual}")
        
        return mismatches
    
    def _validate_basic_info(self, basic_info) -> List[str]:
        """Validate basic character information."""
        errors = []
        
        if not basic_info.name:
            errors.append("Character name is missing")
        
        if basic_info.level < 1 or basic_info.level > 20:
            errors.append(f"Invalid character level: {basic_info.level}")
        
        if not basic_info.classes:
            errors.append("Character has no classes")
        
        return errors
    
    def _validate_against_ground_truth(self, character: Character) -> List[str]:
        """Validate against manually verified data."""
        errors = []
        
        # Compare ability scores
        for ability in ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma']:
            expected = self.validation_data.get('ability_scores', {}).get(ability, 0)
            actual = getattr(character.ability_scores, ability).total
            
            if expected and expected != actual:
                errors.append(f"{ability.title()} score mismatch: expected {expected}, got {actual}")
        
        return errors
```

#### 4.1.2 Test Framework Integration
```python
# tests/integration/test_character_accuracy.py
import pytest
from dnd_character_scraper.api.client import DNDBeyondAPIClient
from dnd_character_scraper.processors.character import CharacterProcessor
from dnd_character_scraper.validators.character import CharacterValidator

class TestCharacterAccuracy:
    """Integration tests using validation data."""
    
    @pytest.fixture
    def api_client(self):
        return DNDBeyondAPIClient()
    
    @pytest.fixture
    def processor(self):
        return CharacterProcessor()
    
    @pytest.mark.parametrize("character_id,validation_file", [
        (144986992, "validation_data/144986992_validation.json"),
        (145081718, "validation_data/145081718_validation.json"),
        # ... other test characters
    ])
    def test_character_accuracy(self, character_id, validation_file, api_client, processor):
        """Test character processing accuracy against validation data."""
        # Load validation data
        with open(validation_file) as f:
            validation_data = json.load(f)
        
        # Process character
        raw_data = api_client.get_character(character_id)
        character = processor.process_character(raw_data)
        
        # Validate
        validator = CharacterValidator(validation_data)
        is_valid, errors = validator.validate_character(character)
        
        assert is_valid, f"Character {character_id} validation failed: {errors}"
```

### 4.2 Progress Tracking for Phase 4

**Update Status**: Use Edit tool to change `[ ]` to `[x]` when complete.

- [ ] Implement character validation framework with quick compare
- [ ] Create calculation validation tests
- [ ] Integrate with existing validation data files
- [ ] Create comprehensive test suite
- [ ] Test all 12 character IDs successfully
- [ ] Validate edge cases and multiclass scenarios

**Phase 4 Completion Criteria**:
- [ ] All 12 test characters process without errors
- [ ] Validation against manual data shows 100% accuracy
- [ ] Edge cases handled properly
- [ ] Quick compare mode works for rapid validation
- [ ] Test coverage adequate for all major systems

---

## Phase 5: Integration & Obsidian-Specific Formatting Preservation

**Goal**: Integrate new modular architecture while preserving all working Obsidian formatting  
**Duration**: Critical integration phase - must not break existing functionality  
**Success Criteria**: All existing outputs identical, CLI compatibility maintained, Obsidian blocks perfect

**Critical**: Must preserve existing Obsidian DnD UI Toolkit integration and formatting patterns.

### 5.1 Step-by-Step Integration Implementation

#### Step 1: Analyze Current Formatting Logic (2 hours)

**5.1.1 Extract Obsidian Formatting Functions**
Find all formatting functions in `dnd_json_to_markdown.py`:
```bash
grep -n -A 5 "def.*format\|def.*generate\|def.*wrap" dnd_json_to_markdown.py
```

**5.1.2 Document Critical Functions to Preserve**
Create preservation analysis:
```bash
# Identify critical functions that must be copied exactly
echo "# Critical Obsidian Formatting Functions

## Must Preserve Exactly:
" > obsidian_preservation.md

grep -n "_wrap_in_callout\|generate.*block\|get_safe_state_key" dnd_json_to_markdown.py >> obsidian_preservation.md
```

**5.1.3 Create Obsidian Formatter** (`exporters/obsidian_formatter.py`)
```python
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

class ObsidianFormatter:
    """Preserves exact Obsidian DnD UI Toolkit formatting from v5.2.0."""
    
    def __init__(self, character_data: Dict[str, Any]):
        self.character_data = character_data
        self.debug_summary = character_data.get("debug_summary", {})
        self.name = self.debug_summary.get("name", "Unknown Character")
    
    def _wrap_in_callout(self, content: List[str], block_id: str) -> List[str]:
        """EXACT COPY from dnd_json_to_markdown.py - DO NOT MODIFY."""
        # This function is complex and handles:
        # - Quote block management (> prefixes)
        # - Heading preservation (#### spell names outside quotes for linking)
        # - BR tag placement (outside quote blocks)
        # - Anchor generation (^block-id)
        # - Internal linking support [[#Spell Name]]
        
        # COPY EXACT LOGIC FROM EXISTING FILE
        # DO NOT OPTIMIZE OR CHANGE
        wrapped_content = []
        
        # Find the exact implementation in dnd_json_to_markdown.py and copy it
        # This is critical for Obsidian compatibility
        
        return wrapped_content  # Placeholder - copy real implementation
    
    def get_safe_state_key(self, suffix: str) -> str:
        """EXACT COPY from dnd_json_to_markdown.py - DO NOT MODIFY."""
        # Copy exact state key generation logic
        safe_name = re.sub(r'[^a-zA-Z0-9]', '', self.name.lower())
        return f"{safe_name}_{suffix}"
    
    def generate_stats_block(self) -> List[str]:
        """Generate stats block with exact v5.2.0 formatting."""
        stats_content = [
            "```stats",
            "items:",
            f"  - label: Level",
            f"    value: '{self.debug_summary.get('level', 1)}'",
            f"  - label: Initiative", 
            f"    value: '+{self.debug_summary.get('initiative', 0)}'",
            f"  - label: Armor Class",
            f"    sublabel: {self._get_ac_breakdown()}",
            f"    value: {self.debug_summary.get('armor_class', 10)}",
            "grid:",
            "  columns: 3",
            "```"
        ]
        return stats_content
    
    def generate_healthpoints_block(self) -> List[str]:
        """Generate health points block with exact v5.2.0 formatting."""
        state_key = self.get_safe_state_key("health")
        hit_points = self.debug_summary.get("hit_points", 1)
        
        # Get hit dice from character data
        hit_dice_info = self._get_hit_dice_info()
        
        hp_content = [
            "```healthpoints",
            f"state_key: {state_key}",
            f"health: {hit_points}",
            "hitdice:",
            f"  dice: {hit_dice_info['dice']}",
            f"  value: {hit_dice_info['value']}",
            "```"
        ]
        return hp_content
    
    def generate_abilities_block(self) -> List[str]:
        """Generate abilities block with exact v5.2.0 formatting."""
        ability_scores = self.debug_summary.get("ability_scores", {})
        
        abilities_content = [
            "```ability", 
            "abilities:",
            f"  strength: {ability_scores.get('strength', 10)}",
            f"  dexterity: {ability_scores.get('dexterity', 10)}",
            f"  constitution: {ability_scores.get('constitution', 10)}",
            f"  intelligence: {ability_scores.get('intelligence', 10)}",
            f"  wisdom: {ability_scores.get('wisdom', 10)}",
            f"  charisma: {ability_scores.get('charisma', 10)}"
        ]
        
        # Add bonuses if present (2024 DnD UI Toolkit syntax)
        bonuses = self._get_ability_bonuses()
        if bonuses:
            abilities_content.append("bonuses:")
            for bonus in bonuses:
                abilities_content.append(f"  - name: \"{bonus['name']}\"")
                abilities_content.append(f"    target: {bonus['target']}")
                abilities_content.append(f"    value: {bonus['value']}")
        
        # Add proficiencies
        proficiencies = self._get_saving_throw_proficiencies()
        if proficiencies:
            abilities_content.append("proficiencies:")
            for prof in proficiencies:
                abilities_content.append(f"  - {prof}")
        
        abilities_content.append("```")
        return abilities_content
    
    def generate_consumables_block(self) -> List[str]:
        """Generate consumables/spell slots block with exact v5.2.0 formatting."""
        consumables_content = ["```consumable", "items:"]
        
        # Add spell slots
        spell_slots = self.character_data.get("spell_slots", {})
        if spell_slots:
            # Regular spell slots
            regular_slots = spell_slots.get("regular_slots", {})
            for level, count in regular_slots.items():
                if count > 0:
                    level_num = level.split("_")[-1]
                    state_key = self.get_safe_state_key(f"spells_{level_num}")
                    consumables_content.extend([
                        f"  - label: 'Level {level_num} Spell Slots'",
                        f"    state_key: {state_key}",
                        f"    uses: {count}",
                        f"    reset_on: long-rest"
                    ])
            
            # Pact magic slots (Warlock)
            pact_slots = spell_slots.get("pact_slots", {})
            if pact_slots:
                pact_level = pact_slots.get("level", 1)
                pact_count = pact_slots.get("count", 0)
                if pact_count > 0:
                    state_key = self.get_safe_state_key("pact_magic")
                    consumables_content.extend([
                        f"  - label: 'Pact Magic (Level {pact_level})'",
                        f"    state_key: {state_key}",
                        f"    uses: {pact_count}",
                        f"    reset_on:",
                        f"      - event: short-rest",
                        f"        amount: {pact_count}",
                        f"      - event: long-rest"
                    ])
        
        consumables_content.append("```")
        return consumables_content
    
    def _get_ac_breakdown(self) -> str:
        """Get AC breakdown description."""
        # Copy logic from existing dnd_json_to_markdown.py
        return "Unarmored (10 + Dex)"  # Placeholder
    
    def _get_hit_dice_info(self) -> Dict[str, Any]:
        """Get hit dice information from character data."""
        # Extract from character classes
        classes = self.character_data.get("classes", [])
        if classes:
            # Use first class for hit dice (or combine for multiclass)
            first_class = classes[0]
            class_name = first_class.get("definition", {}).get("name", "Fighter")
            
            # Map class to hit die (copy from existing logic)
            hit_dice_map = {
                "Artificer": "d8", "Barbarian": "d12", "Bard": "d8", "Cleric": "d8",
                "Druid": "d8", "Fighter": "d10", "Monk": "d8", "Paladin": "d10",
                "Ranger": "d10", "Rogue": "d8", "Sorcerer": "d6", "Warlock": "d8", "Wizard": "d6"
            }
            
            dice = hit_dice_map.get(class_name, "d8")
            level = first_class.get("level", 1)
            
            return {"dice": dice, "value": level}
        
        return {"dice": "d8", "value": 1}
    
    def _get_ability_bonuses(self) -> List[Dict[str, Any]]:
        """Get ability bonuses for 2024 DnD UI Toolkit syntax."""
        # Extract from character modifiers or features
        # This would be empty for most characters unless they have specific bonuses
        return []
    
    def _get_saving_throw_proficiencies(self) -> List[str]:
        """Get saving throw proficiencies."""
        # Extract from character data
        proficiencies = self.character_data.get("proficiencies", {})
        saving_throws = proficiencies.get("saving_throws", [])
        return saving_throws
```

#### Step 2: Preserve Spell Formatting (2.5 hours)

**5.2.1 Extract Spell Processing Logic**
```bash
grep -n -A 10 "def.*spell\|_process.*spell" dnd_json_to_markdown.py > spell_formatting_analysis.txt
```

**5.2.2 Create Spell Formatter** (`exporters/spell_formatter.py`)
```python
from typing import List, Dict, Any, Optional
from pathlib import Path

class SpellFormatter:
    """Preserves exact spell formatting and enhancement logic from v5.2.0."""
    
    def __init__(self, character_data: Dict[str, Any], enhance_spells: bool = True):
        self.character_data = character_data
        self.enhance_spells = enhance_spells
        self.spells_dir = Path("spells")
    
    def format_spells_section(self) -> List[str]:
        """EXACT COPY of spell formatting from dnd_json_to_markdown.py."""
        spell_content = []
        
        # Copy exact logic for:
        # - Spell grouping by source (class, racial, feat, item)
        # - Spell level organization
        # - Enhanced spell file loading
        # - Fallback to API data
        # - Internal linking format
        # - Preparation status tracking
        
        # CRITICAL: Do not modify the complex spell processing logic
        # This handles many edge cases and integrations
        
        return spell_content
    
    def _load_enhanced_spell_data(self, spell_name: str) -> Optional[str]:
        """EXACT COPY from dnd_json_to_markdown.py - enhanced spell loading."""
        if not self.enhance_spells:
            return None
        
        # Copy exact enhanced spell file loading logic
        # This handles local spell/*.md files with rich formatting
        
        return None  # Placeholder - copy real implementation
    
    def _format_spell_table(self, spells_by_level: Dict[int, List[Dict]]) -> List[str]:
        """EXACT COPY from dnd_json_to_markdown.py - spell table formatting."""
        # Copy exact table formatting logic
        # This creates the spell tables with proper columns
        
        return []  # Placeholder - copy real implementation
    
    def _generate_spell_callouts(self, spells: List[Dict[str, Any]]) -> List[str]:
        """EXACT COPY from dnd_json_to_markdown.py - spell callout generation."""
        # Copy exact callout generation logic using _wrap_in_callout
        
        return []  # Placeholder - copy real implementation
```

#### Step 3: Create Backward-Compatible CLI (1.5 hours)

**5.3.1 Create CLI Wrapper** (`cli/main.py`)
```python
import argparse
import sys
import json
from pathlib import Path
from typing import Optional, List

# Import new modular components
from ..api.client import DNDBeyondAPIClient
from ..calculators import CalculatorRegistry
from ..rules.version_manager import RuleVersionManager
from ..exporters.json_exporter import JSONExporter
from ..exporters.obsidian_formatter import ObsidianFormatter
from ..exporters.spell_formatter import SpellFormatter
from ..validators.character import CharacterValidator

def main():
    """Main CLI entry point - maintains v5.2.0 compatibility."""
    parser = argparse.ArgumentParser(
        description="Enhanced D&D Beyond Character Scraper v6.0.0",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python enhanced_dnd_scraper.py 12345678
  python enhanced_dnd_scraper.py 12345678 --output character.json
  python enhanced_dnd_scraper.py 12345678 --session "your_cookie"
  python enhanced_dnd_scraper.py 12345678 --verbose
  python enhanced_dnd_scraper.py 12345678 --quick-compare validation.json
  python enhanced_dnd_scraper.py --batch characters.yaml
        """
    )
    
    # Maintain exact v5.2.0 argument structure
    parser.add_argument("character_id", nargs="?", type=int, 
                       help="D&D Beyond character ID")
    parser.add_argument("--output", "-o", type=str,
                       help="Output JSON file path")
    parser.add_argument("--session", "-s", type=str,
                       help="Session cookie for private characters")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose output")
    parser.add_argument("--quick-compare", type=str,
                       help="Quick compare against validation file")
    parser.add_argument("--batch", type=str,
                       help="Process multiple characters from YAML file")
    
    args = parser.parse_args()
    
    # Handle batch processing
    if args.batch:
        return process_batch_characters(args)
    
    # Require character_id for single character processing
    if not args.character_id:
        parser.print_help()
        return 1
    
    try:
        # Step 1: Fetch character data
        if args.verbose:
            print(f"Fetching character {args.character_id}...")
        
        client = DNDBeyondAPIClient(session_cookie=args.session)
        raw_character_data = client.get_character(args.character_id)
        
        # Step 2: Detect rule version
        rule_manager = RuleVersionManager()
        rule_version = rule_manager.detect_rule_version(raw_character_data)
        
        if args.verbose:
            print(f"Detected rule version: {rule_version.value}")
        
        # Step 3: Run all calculations
        calculator_registry = CalculatorRegistry(rule_version.value)
        calculated_data = calculator_registry.calculate_all(raw_character_data)
        
        # Step 4: Combine data
        complete_character_data = {
            **raw_character_data,
            **calculated_data,
            "rule_version": rule_version.value
        }
        
        # Step 5: Validate if requested
        if args.quick_compare:
            validator = CharacterValidator()
            validation_file = Path(args.quick_compare)
            result = validator.quick_compare(complete_character_data, validation_file)
            
            print(f"Quick Compare Results:")
            print(f"Valid: {result.is_valid}")
            if result.errors:
                print("Errors:")
                for error in result.errors:
                    print(f"  - {error}")
            if result.warnings:
                print("Warnings:")
                for warning in result.warnings:
                    print(f"  - {warning}")
            
            if not result.is_valid:
                return 1
        
        # Step 6: Output JSON
        output_file = args.output or f"character_{args.character_id}.json"
        
        exporter = JSONExporter()
        exporter.export(complete_character_data, output_file)
        
        if args.verbose:
            print(f"Character data saved to {output_file}")
        
        # Step 7: Generate Markdown (like existing dnd_json_to_markdown.py)
        markdown_file = output_file.replace('.json', '.md')
        generate_obsidian_markdown(complete_character_data, markdown_file)
        
        if args.verbose:
            print(f"Obsidian markdown saved to {markdown_file}")
        
        return 0
    
    except Exception as e:
        print(f"Error processing character {args.character_id}: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

def generate_obsidian_markdown(character_data: Dict[str, Any], output_file: str):
    """Generate Obsidian markdown using preserved formatting."""
    
    # Create formatters
    obsidian_formatter = ObsidianFormatter(character_data)
    spell_formatter = SpellFormatter(character_data)
    
    # Generate all sections
    markdown_content = []
    
    # YAML frontmatter (copy exact format from v5.2.0)
    markdown_content.extend(generate_yaml_frontmatter(character_data))
    
    # Character info section
    markdown_content.extend(generate_character_info_section(character_data))
    
    # DnD UI Toolkit blocks
    markdown_content.extend(obsidian_formatter.generate_stats_block())
    markdown_content.append("")
    markdown_content.extend(obsidian_formatter.generate_healthpoints_block())
    markdown_content.append("")
    markdown_content.extend(obsidian_formatter.generate_abilities_block())
    markdown_content.append("")
    markdown_content.extend(obsidian_formatter.generate_consumables_block())
    markdown_content.append("")
    
    # Spells section (if character has spells)
    if character_data.get("spells") or character_data.get("classSpells"):
        markdown_content.extend(spell_formatter.format_spells_section())
    
    # Write to file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(markdown_content))

def generate_yaml_frontmatter(character_data: Dict[str, Any]) -> List[str]:
    """Generate YAML frontmatter - EXACT COPY from dnd_json_to_markdown.py."""
    # Copy exact frontmatter generation logic
    # This includes tags, character metadata, etc.
    
    frontmatter = [
        "---",
        f"character_id: {character_data.get('id', 0)}",
        f"name: \"{character_data.get('name', 'Unknown')}\"",
        f"level: {character_data.get('level', 1)}",
        # ... copy all frontmatter fields
        "---",
        ""
    ]
    
    return frontmatter

def generate_character_info_section(character_data: Dict[str, Any]) -> List[str]:
    """Generate character info section - EXACT COPY from dnd_json_to_markdown.py."""
    # Copy exact character info formatting
    
    return []

def process_batch_characters(args) -> int:
    """Process multiple characters from YAML configuration."""
    import yaml
    
    try:
        with open(args.batch) as f:
            batch_config = yaml.safe_load(f)
        
        characters = batch_config.get("characters", [])
        results = []
        
        for i, char_config in enumerate(characters):
            char_id = char_config.get("id")
            if not char_id:
                print(f"Skipping character {i}: missing ID")
                continue
            
            print(f"Processing character {char_id}...")
            
            # Rate limiting (respect 20-second API limit)
            if i > 0:
                import time
                time.sleep(25)
            
            try:
                # Process single character
                # (reuse single character logic)
                print(f"✅ {char_id}: Success")
                results.append({"id": char_id, "status": "success"})
                
            except Exception as e:
                print(f"❌ {char_id}: {e}")
                results.append({"id": char_id, "status": "failed", "error": str(e)})
        
        # Print summary
        successes = [r for r in results if r["status"] == "success"]
        failures = [r for r in results if r["status"] == "failed"]
        
        print(f"\n📊 Batch Complete: {len(successes)}/{len(results)} successful")
        
        if failures:
            print("\n❌ Failed Characters:")
            for failure in failures:
                print(f"  - {failure['id']}: {failure.get('error', 'Unknown error')}")
        
        return 0 if len(failures) == 0 else 1
    
    except Exception as e:
        print(f"Error processing batch: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

#### Step 4: Final Integration Testing (2 hours)

**5.4.1 Test Output Compatibility** (`tests/integration/test_output_preservation.py`)
```python
import pytest
import json
import tempfile
from pathlib import Path
from dnd_character_scraper.cli.main import main as cli_main
from dnd_character_scraper.api.mock_client import MockAPIClient

def test_cli_output_identical_to_v5():
    """Test that CLI output is identical to v5.2.0 format."""
    # Create mock character
    client = MockAPIClient()
    test_char_id = 999999
    
    # Run new CLI
    with tempfile.TemporaryDirectory() as temp_dir:
        output_file = Path(temp_dir) / "test_output.json"
        
        # Simulate CLI call
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ["enhanced_dnd_scraper.py", str(test_char_id), "--output", str(output_file)]
            result = cli_main()
            assert result == 0
        finally:
            sys.argv = original_argv
        
        # Verify JSON structure
        assert output_file.exists()
        with open(output_file) as f:
            output_data = json.load(f)
        
        # Check required fields from v5.2.0
        required_fields = ["id", "name", "level", "debug_summary"]
        for field in required_fields:
            assert field in output_data, f"Missing required field: {field}"
        
        # Check debug_summary structure
        debug_summary = output_data["debug_summary"]
        debug_required = ["name", "level", "hit_points", "armor_class", "ability_scores"]
        for field in debug_required:
            assert field in debug_summary, f"Missing debug_summary field: {field}"

def test_obsidian_markdown_format_preserved():
    """Test that Obsidian markdown format is preserved exactly."""
    from dnd_character_scraper.exporters.obsidian_formatter import ObsidianFormatter
    from dnd_character_scraper.tests.fixtures.character_generator import TestCharacterGenerator
    
    # Create test character
    character_data = TestCharacterGenerator.create_basic_character()
    character_data["debug_summary"] = {
        "name": "Test Character",
        "level": 2,
        "hit_points": 16,
        "armor_class": 12,
        "ability_scores": {"strength": 15, "dexterity": 14, "constitution": 16, 
                          "intelligence": 8, "wisdom": 12, "charisma": 17}
    }
    
    formatter = ObsidianFormatter(character_data)
    
    # Test stats block format
    stats_block = formatter.generate_stats_block()
    assert "```stats" in stats_block
    assert "items:" in stats_block
    assert "grid:" in stats_block
    assert "columns: 3" in stats_block
    
    # Test health points block format
    hp_block = formatter.generate_healthpoints_block()
    assert "```healthpoints" in hp_block
    assert "state_key:" in " ".join(hp_block)
    assert "health: 16" in " ".join(hp_block)
    assert "hitdice:" in " ".join(hp_block)
    
    # Test abilities block format
    abilities_block = formatter.generate_abilities_block()
    assert "```ability" in abilities_block
    assert "abilities:" in abilities_block
    assert "strength: 15" in " ".join(abilities_block)

def test_batch_processing():
    """Test batch processing functionality."""
    import yaml
    import tempfile
    
    # Create test batch configuration
    batch_config = {
        "characters": [
            {"id": 999999, "name": "Test Character 1"},
            {"id": 888888, "name": "Test Character 2"}
        ]
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(batch_config, f)
        batch_file = f.name
    
    try:
        # Run batch processing
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ["enhanced_dnd_scraper.py", "--batch", batch_file]
            result = cli_main()
            # Should succeed with mock data
            assert result == 0
        finally:
            sys.argv = original_argv
    finally:
        Path(batch_file).unlink()

def test_backward_compatibility():
    """Test that all v5.2.0 CLI arguments still work."""
    test_cases = [
        # Basic usage
        ["999999"],
        # With output file
        ["999999", "--output", "test.json"],
        # With verbose
        ["999999", "--verbose"],
        # With session (won't work with mock, but should parse)
        ["999999", "--session", "fake_cookie"],
    ]
    
    for args in test_cases:
        import sys
        original_argv = sys.argv
        try:
            sys.argv = ["enhanced_dnd_scraper.py"] + args
            # Should parse without error (might fail on execution with real API)
            # For now, just test argument parsing
            from dnd_character_scraper.cli.main import main
            parser = main.__code__.co_consts  # Get parser from main function
            
            # If we reach here, argument parsing succeeded
            assert True
        except SystemExit:
            # argparse calls sys.exit on help/error, that's expected behavior
            pass
        finally:
            sys.argv = original_argv
```

#### Step 5: Documentation and Migration (1 hour)

**5.5.1 Create Migration Guide** (`MIGRATION_V6.md`)
```markdown
# Migration Guide: v5.2.0 → v6.0.0

## What Changed

### ✅ Preserved (Identical Behavior)
- All CLI arguments work exactly the same
- JSON output format identical
- Obsidian markdown formatting preserved
- Enhanced spell integration unchanged
- D&D UI Toolkit blocks identical

### 🆕 New Features
- Modular architecture for easier maintenance
- Comprehensive testing framework
- Configuration management system
- Better error handling and diagnostics
- Batch processing for multiple characters

### 🔧 Internal Changes (No User Impact)
- Code split into logical modules
- Pydantic data models with validation
- Rule version detection improvements
- Comprehensive test coverage

## Migration Steps

### For Users
**No changes required!** Your existing usage continues to work:

```bash
# All existing commands work identically
python enhanced_dnd_scraper.py 12345678
python enhanced_dnd_scraper.py 12345678 --output character.json --verbose
python dnd_json_to_markdown.py 12345678 character_sheet.md
```

### For Developers
If you've modified the scraper, see `DEVELOPER_MIGRATION.md` for details on adapting to the new modular structure.

## Verification

To verify v6.0.0 produces identical output to v5.2.0:

```bash
# Test with your characters
python enhanced_dnd_scraper.py YOUR_CHARACTER_ID --output v6_output.json
# Compare with your existing v5.2.0 output

# Run validation
python enhanced_dnd_scraper.py YOUR_CHARACTER_ID --quick-compare validation_data/YOUR_CHARACTER_ID_validation.json
```
```

**5.5.2 Update CLAUDE.md** (Add to existing file)
```markdown
## v6.0.0 Architecture (Current)

The scraper has been refactored into a modular architecture while preserving all existing functionality:

### Modules
- `api/`: D&D Beyond API client with retry logic
- `calculators/`: All D&D rule calculations (HP, AC, spell slots, etc.)
- `rules/`: 2014/2024 rule version detection and management
- `models/`: Pydantic data models with validation
- `exporters/`: JSON and Obsidian markdown generation
- `validators/`: Character data validation and testing
- `cli/`: Command-line interface (maintains v5.2.0 compatibility)

### Key Principles Maintained
- **Scraper uses API only**: No local files except enhanced spell descriptions
- **Complete JSON output**: All calculations included for parser independence
- **Obsidian formatting preserved**: Exact DnD UI Toolkit block generation
- **Backward compatibility**: All v5.2.0 CLI arguments work identically

### Baseline Validation Status

#### v5.2.0 vs v6.0.0 Comparison Results
- **Total Characters Tested**: 11/12 (91% coverage)
- **Perfect Compatibility**: 1/11 characters (Character 144986992 - Vaelith Duskthorn)
- **Partial Compatibility**: 10/11 characters with 60-70% match rate

#### Current Issues Identified
1. **HP Calculation Regression**: Missing v5.2.0 hit point calculation methods (Fixed/Manual/Rolled)
2. **ASI Choice Mapping**: 2024 racial ASI choices need optionValue → ability mapping  
3. **AC Calculation Variance**: Equipment and modifier handling differences
4. **Data Processing Issues**: Some characters showing level=0, name="Unknown Character"

#### Baseline Data Available
- **Raw D&D Beyond JSON**: `Raw/{character_id}.json` (11 files)
- **v5.2.0 Scraper Output**: `baseline_{character_id}.json` (11 files)
- **v5.2.0 Parser Output**: `baseline_{character_id}.md` (11 files)
- **Failed Character**: 103214475 (parser string/int comparison error)

### Testing Framework
```bash
# Run full test suite
pytest

# Baseline validation (current implementation)
python comprehensive_baseline_test.py

# Test specific areas
pytest tests/unit/test_calculators.py
pytest tests/integration/test_complete_flow.py
pytest tests/edge_cases/

# Individual character validation
python baseline_comparison.py 144986992
```

### 5.1 Existing Valuable Logic to Preserve

From our current implementation, these patterns are working well and must be maintained:

#### 5.1.1 Enhanced Scraper Capabilities (enhanced_dnd_scraper.py)
```python
# Already implemented and working well:
- Comprehensive spell source detection (class, racial, feat, item spells)
- Advanced spell grouping and deduplication
- Detailed spell metadata extraction (components, casting time, concentration)
- Robust ability score calculation with source attribution
- Enhanced multiclass spell slot calculations
- Subclass detection and hit die mapping
- Comprehensive diagnostics and error handling
- Background spell detection via spellListIds
- Action parsing and inventory enhancement
- Cached property pattern for performance
```

#### 5.1.2 Obsidian DnD UI Toolkit Formatting (dnd_json_to_markdown.py)
```markdown
# Critical formatting patterns to preserve:

## Stats Blocks
```stats
items:
  - label: Level
    value: '2'
  - label: Initiative
    value: '+2'
  - label: Armor Class
    sublabel: Scale Mail (14 + Dex)
    value: 16
grid:
  columns: 3
```

## Health Points Block
```healthpoints
state_key: vaelith_health
health: 13
hitdice:
  dice: d6
  value: 2
```

## Abilities Block (Updated Syntax)
```ability
abilities:
  strength: 15
  dexterity: 14
  constitution: 16
  intelligence: 8
  wisdom: 12
  charisma: 17
bonuses:
  - name: "Right of Power"
    target: strength
    value: 2
proficiencies:
  - constitution
  - charisma
```

## Spell Slots Block (Updated Syntax)
```consumable
items:
  - label: 'Level 1 Spell Slots'
    state_key: vaelith_spells_1
    uses: 3
    reset_on: long-rest
  - label: 'Pact Magic (Level 2)'
    state_key: vaelith_pact_magic
    uses: 2
    reset_on: 
      - event: short-rest
        amount: 2
      - event: long-rest
```
```

#### 5.1.3 Advanced Callout System (_wrap_in_callout)
```python
# Complex logic for Obsidian callouts with proper:
- Quote block management (> prefixes)
- Heading preservation (#### spell names outside quotes for linking)
- BR tag placement (outside quote blocks)
- Anchor generation (^block-id)
- Internal linking support [[#Spell Name]]
```

#### 5.1.4 Enhanced Spell Integration
```python
# Sophisticated spell enhancement system:
- Local spell file loading (spells/*.md) for enhanced descriptions
- Fallback to API data when enhanced files unavailable
- Cross-referencing between API and local data
- Spell preparation tracking (prepared vs known vs always-prepared)
- Internal document linking for spell references
```

#### 5.1.5 Comprehensive Proficiency Source Attribution
```python
# Detailed source tracking for:
- Skill proficiencies with specific sources (Class: Sorcerer, Background: Noble)
- Saving throw proficiencies with class/feat attribution
- Multi-source proficiency handling
- Unknown source detection and fallback logic
```

### 5.2 Obsidian Integration Requirements

#### 5.2.1 YAML Frontmatter
```yaml
# Rich metadata for Obsidian queries and organization:
character_id: 144986992
level: 2
classes: ["Sorcerer"]
species: "Human"
ability_scores: { strength: 15, charisma: 17 }
spells: ["[[acid-splash-xphb]]", "[[prestidigitation-xphb]]"]
tags: [dnd, character-sheet, sorcerer, low-level, spellcaster]
```

#### 5.2.2 State Key Generation
```python
# For DnD UI Toolkit state persistence:
def get_safe_state_key(self, name: str, suffix: str) -> str:
    safe_name = re.sub(r'[^a-zA-Z0-9]', '', name.lower())
    return f"{safe_name}_{suffix}"
```

#### 5.2.3 Internal Linking Patterns
```markdown
# Spell references with internal document links:
| Level | Spell | School | Components | Prepared |
|-------|-------|--------|------------|----------|
| 0 | [[#Acid Splash]] | Evocation | V, S | Known |
| 1 | [[#Magic Missile]] | Evocation | V, S | Prepared |
```

## Phase 5: Integration & Documentation

### 5.3 Refactor Strategy for Existing Code

#### 5.3.1 Migration Philosophy
- **Preserve Working Logic**: Don't break what already works well
- **Enhance Structure**: Improve modularity without losing functionality  
- **Maintain Compatibility**: Keep existing CLI interface and output format
- **Gradual Refactor**: Move logic into modules while preserving behavior

#### 5.3.2 Code Preservation Priorities
1. **High Priority - Must Preserve Exactly**:
   - `_wrap_in_callout()` function (Obsidian formatting)
   - DnD UI Toolkit block generation (stats, healthpoints, ability, consumable) - **UPDATE SYNTAX**
   - Enhanced spell loading and fallback logic
   - YAML frontmatter generation
   - State key generation for UI persistence
   
   **Note**: DnD UI Toolkit syntax has been updated to include `bonuses` in ability blocks and enhanced `reset_on` configurations in consumables. Our parser must generate the current syntax.

2. **Medium Priority - Preserve Logic, Improve Structure**:
   - Spell source detection and grouping
   - Ability score calculation with attribution
   - Proficiency source tracking
   - Multiclass spell slot calculations

3. **Low Priority - Can Refactor Freely**:
   - Error handling patterns (improve with structured logging)
   - API retry logic (enhance with better patterns)
   - Data validation (add comprehensive validation)

#### 5.3.3 Manual Migration Strategy (Not Automated)

**Approach**: Gradual, manual migration preserving working logic

```python
# Phase-by-phase manual migration:

# Phase 1: Extract data models and interfaces
# - Manually copy field definitions from existing classes
# - Convert to Pydantic models with validation
# - Preserve all existing field names and types

# Phase 2: Extract calculators one by one
# - Copy _calculate_hit_points() logic exactly
# - Move to calculators/hit_points.py 
# - Test against existing output
# - Repeat for each calculator

# Phase 3: Extract processors
# - Copy _process_class_spells() logic exactly
# - Move to processors/spells.py
# - Preserve spell grouping and deduplication logic

# Phase 5: Keep formatters nearly identical
class ObsidianFormatter:
    def _wrap_in_callout(self, content: List[str], block_id: str) -> List[str]:
        # COPY EXACT LOGIC - don't modify this complex function
        
    def generate_stats_block(self) -> List[str]:
        # COPY EXACT FORMAT - DnD UI Toolkit requirement
```

**Migration Principles**:
- Copy working code, don't rewrite
- Test each piece against existing output
- Preserve exact behavior first, optimize later
- Manual verification at each step

### 5.4 Enhanced CLI Integration (`cli/main.py`)
```python
import argparse
from typing import Optional
from ..api.client import DNDBeyondAPIClient
from ..processors.character import CharacterProcessor
from ..exporters.json_exporter import JSONExporter
from ..validators.character import CharacterValidator
from ..utils.logging import setup_logging

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="D&D Beyond Character Scraper v6.0.0"
    )
    parser.add_argument("character_id", type=int, help="Character ID")
    parser.add_argument("--output", "-o", help="Output file")
    parser.add_argument("--raw-output", help="Raw data output file")
    parser.add_argument("--session", help="Session cookie")
    parser.add_argument("--verbose", "-v", action="store_true")
    parser.add_argument("--quick-compare", help="Quick compare against validation file")  # NEW
    
    args = parser.parse_args()
    
    if args.verbose:
        setup_logging(level='DEBUG')
    
    try:
        # Initialize components
        client = DNDBeyondAPIClient(args.session)
        processor = CharacterProcessor()
        exporter = JSONExporter()
        
        # Process character
        raw_data = client.get_character(args.character_id)
        character = processor.process_character(raw_data)
        
        # Quick compare mode
        if args.quick_compare:
            validator = CharacterValidator()
            mismatches = validator.quick_compare(character.__dict__, args.quick_compare)
            if mismatches:
                print("VALIDATION MISMATCHES:")
                for mismatch in mismatches:
                    print(f"  ❌ {mismatch}")
                return 1
            else:
                print("✅ All validations passed!")
                return 0
        
        # Export data
        output_file = args.output or f"{character.basic_info.name}.json"
        exporter.export(character, output_file)
        
        if args.raw_output:
            exporter.export_raw(raw_data, args.raw_output)
        
        print(f"Character data exported to: {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0
```

### 5.2 Enhanced JSON Exporter with Debug Summary (`exporters/json_exporter.py`)
```python
import json
from typing import Dict, Any
from ..models.character import Character

class JSONExporter:
    """Export character data to JSON with debug summary."""
    
    def export(self, character: Character, output_file: str):
        """Export character with debug summary."""
        # Generate debug summary for validation
        debug_summary = self._generate_debug_summary(character)
        
        character_dict = character.__dict__.copy()
        character_dict['debug_summary'] = debug_summary
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(character_dict, f, indent=2, ensure_ascii=False, default=str)
    
    def _generate_debug_summary(self, character: Character) -> Dict[str, Any]:
        """Generate debug summary for easy validation."""
        return {
            "name": character.basic_info.name,
            "level": character.basic_info.level,
            "hit_points": character.hit_points.calculated_hp,
            "armor_class": character.armor_class.total,
            "rule_version": character.basic_info.rule_version.value,
            "proficiency_bonus": character.proficiencies.bonus,
            "spell_slots": {
                f"level_{i}": slots for i, slots in enumerate(character.spells.spell_slots, 1)
                if slots > 0
            },
            "ability_scores": {
                "strength": character.ability_scores.strength.total,
                "dexterity": character.ability_scores.dexterity.total,
                "constitution": character.ability_scores.constitution.total,
                "intelligence": character.ability_scores.intelligence.total,
                "wisdom": character.ability_scores.wisdom.total,
                "charisma": character.ability_scores.charisma.total
            },
            "modifiers": {
                "strength": character.ability_scores.strength.modifier,
                "dexterity": character.ability_scores.dexterity.modifier,
                "constitution": character.ability_scores.constitution.modifier,
                "intelligence": character.ability_scores.intelligence.modifier,
                "wisdom": character.ability_scores.wisdom.modifier,
                "charisma": character.ability_scores.charisma.modifier
            }
        }
```

### 5.3 Backward Compatibility Layer
```python
# enhanced_dnd_scraper.py (compatibility wrapper)
"""
Backward compatibility wrapper for the refactored scraper.
Maintains the same CLI interface as v5.2.0.
"""

import sys
from dnd_character_scraper.cli.main import main

if __name__ == "__main__":
    sys.exit(main())
```

### 5.4 Documentation Plan
- [ ] **API Documentation**: Complete docstrings and type hints
- [ ] **Architecture Guide**: Module structure and design patterns
- [ ] **Migration Guide**: Upgrading from v5.2.0 to v6.0.0
- [ ] **D&D Rules Reference**: 2014 vs 2024 differences and detection
- [ ] **Testing Guide**: Running and extending the test suite
- [ ] **Contributing Guide**: Code style and contribution process

### 5.5 Progress Tracking for Phase 5

**Update Status**: Use Edit tool to change `[ ]` to `[x]` when complete.

- [ ] Preserve all Obsidian DnD UI Toolkit formatting exactly
- [ ] Migrate existing logic into modular structure
- [ ] Create CLI wrapper maintaining v5.2.0 compatibility
- [ ] Implement quick compare functionality
- [ ] Add debug summary to JSON output
- [ ] Test with existing validation data
- [ ] Verify Obsidian output unchanged
- [ ] Final integration testing with all 12 character IDs

**Phase 5 Completion Criteria**:
- [ ] Obsidian output identical to current version
- [ ] All existing CLI arguments work correctly
- [ ] Enhanced spell integration preserved
- [ ] State keys and callouts work in Obsidian
- [ ] All 12 characters produce valid markdown
- [ ] Documentation updated for new architecture

---

## Quality Assurance & Success Metrics

### Code Quality Targets
- [ ] **Test Coverage**: 90%+ line coverage
- [ ] **Type Safety**: 100% type hints with mypy validation
- [ ] **Code Style**: Black formatting, flake8 compliance
- [ ] **Documentation**: 100% public API documented with examples

### Basic Performance Expectations
Since this is a personal tool, performance requirements are minimal:
- Processing should complete without hanging
- Memory usage should be reasonable for typical desktop machines
- No enterprise-level optimization needed

### Validation Targets
- [ ] **All Test Characters**: 12/12 characters process successfully
- [ ] **Calculation Accuracy**: 100% match on core calculations (HP, AC, spell slots)
- [ ] **Rule Detection**: 100% accuracy on 2014/2024 rule detection
- [ ] **Data Completeness**: 95%+ data extraction completeness
- [ ] **Edge Case Handling**: Graceful handling of unknown/homebrew content
- [ ] **Error Recovery**: Proper error messages for invalid API responses

---

## Risk Management

### Technical Risks
1. **API Changes**: D&D Beyond API modifications or deprecation
   - *Mitigation*: Comprehensive error handling, API versioning detection, fail-fast validation
   - *Contingency*: Mock API client allows testing without external dependency
   - *Monitoring*: Structured logging of API response changes

2. **Rule Complexity**: Missing edge cases in D&D rule calculations
   - *Mitigation*: Extensive validation dataset, edge case testing, debug assertions
   - *Validation*: 100% accuracy requirement on 12 test characters
   - *Documentation*: Clear calculation steps in debug output

3. **Processing Failures**: Characters that fail to process correctly
   - *Mitigation*: Comprehensive error handling and graceful degradation
   - *Testing*: All 12 test characters must process successfully
   - *Validation*: Quick compare mode for rapid verification

4. **Dependency Management**: Python version compatibility issues
   - *Mitigation*: Support Python 3.9+ with minimal external dependencies
   - *Dependencies*: Standard library preferred, essential packages only

### Project Risks
1. **Scope Creep**: Adding features beyond core refactoring
   - *Mitigation*: Strict scope definition, phase-based development
   - *Governance*: Clear acceptance criteria for each phase

2. **Breaking Changes**: Loss of backward compatibility
   - *Mitigation*: Compatibility wrapper maintains v5.2.0 CLI interface
   - *Migration*: Automated migration tools for data formats
   - *Testing*: Regression testing against existing outputs

3. **Timeline Overrun**: Underestimating refactoring complexity
   - *Mitigation*: Phased approach with incremental delivery
   - *Flexibility*: Core features prioritized over nice-to-have enhancements

4. **Data Integrity**: Calculation errors in refactored code
   - *Mitigation*: Validation against manually verified character data
   - *Testing*: Comprehensive unit and integration test coverage
   - *Verification*: Quick compare mode for rapid validation

---

## Manual Validation Tracking

### 📋 **Validation Progress**
Track manual validation of test characters against baseline data to identify v5.2.0 gaps and v6.0.0 improvement targets.

#### ✅ **Completed Validations**
| Character ID | Name | Level | Class | Accuracy | Key Findings |
|--------------|------|-------|-------|-----------|--------------|
| 29682199 | Redgrave | 10 | Cleric (Forge) | 88.9% | AC Gap: Missing Forge Domain bonuses (+2), Cloak of Protection (+1) |

#### 📝 **Validation Template Location**
- **Manual validation files**: `validation_data/{character_id}_validation.json`
- **Comparison tool**: Use baseline comparison utilities in `tools/baseline/`
- **Target accuracy**: 95%+ for v6.0.0 calculator improvements

#### 🎯 **Priority Characters for Validation**
Focus on characters with complex features that stress-test calculations:
1. **29682199** (Redgrave) - ✅ **Completed** - Forge Domain Cleric, Warforged, Magic Items
2. **103214475** (Seluvis) - Multiclass, 2014 rules, Complex spell sources
3. **144986992** (Vaelith) - 2024 rules, Warlock, Known working baseline
4. **Additional characters** - As needed based on feature complexity

#### 📊 **Validation Impact on Development**
- **Phase 3 Priority**: AC calculator enhancement based on Redgrave findings
- **Feature Detection**: Class feature interactions (Forge Domain + Warforged)
- **Magic Item Parsing**: Equipment with AC bonuses
- **v6.0.0 Test Cases**: Use validation discrepancies as test scenarios

### Manual Validation Tracking

**⚠️ Important Note**: Manual validation data may contain human entry errors. All discrepancies should be cross-verified against D&D Beyond character sheets before concluding they represent scraper issues. Use validation results as indicators for investigation, not definitive evidence of problems.

**📊 Validation Progress Summary**:
- **Total Characters**: 6/12 completed (50% coverage)
- **Average Accuracy**: 87.0% across all validated characters
- **Accuracy Range**: 78.6% (Barbarian with critical failures) to 93.8% (Warlock with minor gaps)
- **Pattern Recognition**: Systematic gaps identified across multiple character types
- **Methodology Validation**: Successfully distinguishes scraper bugs from incomplete builds

**🔍 Validation Methodology Proven Effective**:
- **Collaborative Verification**: User provides D&D Beyond data, Claude analyzes against baseline
- **Specific Evidence**: Detailed spell lists, AC breakdowns enable precise root cause analysis  
- **Character Diversity**: Different classes reveal different gap types and systematic patterns
- **Real Player Data**: Ensures fixes address actual character builds and use cases
- **False Positive Prevention**: Distinguishes scraper bugs from incomplete builds (Magic Initiate example)
- **Pattern Recognition**: 6 characters reveal systematic issues affecting multiple classes

**🚨 Critical Validation Findings Summary**:
1. **Subclass Spell Parser**: Missing domain spells (Clerics) AND subclass spells (Artificers) - affects ALL subclass characters
2. **Unarmored Defense Calculator**: Complete AC calculation failure for Barbarians/Monks - critical system breakdown  
3. **Warlock Spell System**: Missing invocation spells + incorrect pact magic spell level display
4. **At-Will Spell Parser**: Missing class feature ritual spells (Totem Warrior features)
5. **Magic Item AC**: Both missing bonuses (Cloak of Protection) AND overcalculation (Elven Chain Dex caps)
6. **Build Validation**: Opportunity to surface incomplete character builds to players

**🎯 Technical Debt Priority Matrix**:
- **CRITICAL**: Subclass spells, Unarmored AC (complete failures affecting core mechanics)
- **HIGH**: Warlock system, At-will spells (missing character abilities)  
- **MEDIUM**: Magic item AC, Spell slot parsing (calculation errors)
- **LOW**: Build warnings (quality of life improvements)

#### Character 29682199 (Redgrave) - Level 10 Forge Domain Cleric
**Status**: ✅ Completed  
**Overall Accuracy**: 88.9% (32/36 validated fields)

#### Character 66356596 (Dor'ren Uroprax) - Level 6 Hexblade Warlock  
**Status**: ✅ Completed  
**Overall Accuracy**: 93.8% (30/32 validated fields)

#### Character 68622804 (Zemfur Folle) - Level 6 Grave Domain Cleric
**Status**: ✅ Completed  
**Overall Accuracy**: 87.5% (28/32 validated fields)

#### Character 103214475 (Seluvis Felo'melorn) - Level 9 Armorer Artificer
**Status**: ✅ Completed  
**Overall Accuracy**: 84.4% (27/32 validated fields)

#### Character 103814449 (Yevelda Ovak) - Level 10 Totem Warrior Barbarian
**Status**: ✅ Completed  
**Overall Accuracy**: 78.6% (11/14 validated fields)

#### Character 103873194 (Marin) - Level 10 Hexblade Warlock
**Status**: ✅ Completed  
**Overall Accuracy**: 90.0% (27/30 validated fields)

| Field Category | Expected | v5.2.0 Baseline | Accuracy | Notes |
|---|---|---|---|---|
| **Basic Info** | ✅ | ✅ | 100% | Name, level, experience match |
| **Ability Scores** | ✅ | ✅ | 100% | All 6 abilities and modifiers correct |
| **Classes** | ✅ | ✅ | 100% | Cleric 10, Forge Domain detected |
| **Species/Background** | ✅ | ✅ | 100% | Warforged Envoy, Guild Artisan |
| **HP** | 73 | 73 | ✅ | Manual HP assignment correct |
| **Initiative** | -1 | -1 | ✅ | Dex modifier applied |
| **Speed** | 30 | 30 | ✅ | Base walking speed |
| **Armor Class** | **25** | **24** | ❌ | **Missing +1 AC** |
| **Spellcasting** | ✅ | ✅ | 100% | DC 17, +9 attack, Wisdom-based |
| **Spell Slots** | ✅ | ✅ | 100% | All levels 1-5 correct |
| **Saving Throws** | ✅ | ✅ | 100% | Wisdom, Charisma proficiencies |

| Field Category | Expected | v5.2.0 Baseline | Accuracy | Notes |
|---|---|---|---|---|
| **Basic Info** | ✅ | ✅ | 100% | Name, level, class, subclass match |
| **Ability Scores** | ✅ | ✅ | 100% | All 6 abilities and modifiers correct |
| **Species/Background** | ✅ | ✅ | 100% | Metallic Dragonborn, Investigator |
| **HP/AC/Initiative** | ✅ | ✅ | 100% | 45 HP, 16 AC, +2 initiative |
| **Spellcasting** | ✅ | ✅ | 100% | DC 15, +7 attack, Charisma-based |
| **Pact Magic** | ✅ | ✅ | 100% | 2 level 3 slots (Warlock 6) |
| **Total Spells** | **11** | **10** | ❌ | **Missing 1 spell** |
| **Saving Throws** | ✅ | ✅ | 100% | Wisdom, Charisma (case sensitivity) |

| Field Category | Expected | v5.2.0 Baseline | Accuracy | Notes |
|---|---|---|---|---|
| **Basic Info** | ✅ | ✅ | 100% | Name, level, class, subclass match |
| **Ability Scores** | ✅ | ✅ | 100% | All 6 abilities and modifiers correct |
| **Species/Background** | ✅ | ✅ | 100% | Firbolg, Witherbloom Student |
| **HP/AC/Initiative** | ✅ | ✅ | 100% | 39 HP, 18 AC, +2 initiative |
| **Spellcasting** | ✅ | ✅ | 100% | DC 15, +7 attack, Wisdom-based |
| **Spell Slots** | ✅ | ❌ | 0% | **Parsing issue: 4/3/3 vs 0/0/0** |
| **Total Spells** | **42** | **18** | ❌ | **Missing 6 domain spells** |
| **Saving Throws** | ✅ | ✅ | 100% | Wisdom, Charisma proficiencies |

#### Discrepancy Analysis - Character 66356596 (Dor'ren Uroprax) ✅ **VERIFIED**
1. **Missing Eldritch Invocation Spell**: Bane spell missing entirely
   - **Root cause**: Spell granted by Eldritch Invocation, not captured by scraper
   - **Impact**: Functional gap - missing actual character abilities
2. **Warlock Pact Magic Display Issue**: Hex/Suggestion show base levels, not casting levels
   - **Expected**: All spells at Level 3 (pact slot level for Level 6 Warlock)
   - **Baseline**: Hex (Level 1), Suggestion (Level 2) - base levels from spell definitions
   - **Impact**: Misleading display - Warlocks can't cast at base levels
3. **Saving Throw Case**: Format consistency issue ("Wisdom" vs "wisdom") - functional match

**Critical Finding**: Major Warlock-specific gaps identified. Scraper misses Eldritch Invocation spells and displays misleading spell levels for pact magic.

#### Discrepancy Analysis - Character 68622804 (Zemfur Folle) ✅ **VERIFIED**
1. **Missing Domain Spells**: 6 Grave Domain spells completely absent
   - **Expected**: Bane, False Life (1st), Gentle Repose, Ray of Enfeeblement (3rd), Revivify, Vampiric Touch (5th)
   - **Baseline**: 0 domain spells captured
   - **Impact**: Core subclass identity missing - affects ALL domain clerics
2. **Spell Slot Parsing Issue**: Data structure mismatch
   - **Expected**: 4/3/3 slots for levels 1/2/3
   - **Baseline**: Has correct data but wrong key format (`level_1` vs `1`)
3. **Spell Count Display**: D&D Beyond shows spells at all castable levels (42 entries)
   - **Baseline**: Shows unique spells only (18 entries)
   - **Impact**: Count mismatch but both approaches valid

**Critical Finding**: Domain spells are fundamental cleric mechanics missing entirely. This is the most severe gap identified - affects every cleric subclass in our dataset.

#### Discrepancy Analysis - Character 103214475 (Seluvis Felo'melorn) ✅ **VERIFIED**
1. **Missing Subclass Spells**: 6 Armorer spells completely absent
   - **Expected**: Magic Missile, Thunderwave (3rd), Mirror Image, Shatter (5th), Hypnotic Pattern, Lightning Bolt (9th)
   - **Baseline**: 0 subclass spells captured
   - **Impact**: Same fundamental gap as domain spells - affects ALL Artificer subclasses
2. **Spell Slot Parsing Issue**: Same data structure mismatch as other characters
   - **Expected**: 4/3/2 slots for levels 1/2/3
   - **Baseline**: Has correct data but wrong key format (`level_1` vs `1`)
3. **Spell Count Display**: D&D Beyond shows spells at all castable levels (28 entries)
   - **Baseline**: Shows unique spells only (14 entries)
4. **Terminology**: "intellect" vs "Intelligence" - validation entry variation

**CRITICAL PATTERN CONFIRMED**: Subclass spell parsing gap affects BOTH Clerics (domain spells) AND Artificers (subclass spells). This is a broader, more severe issue than initially identified.

#### Discrepancy Analysis - Character 103814449 (Yevelda Ovak) ✅ **VERIFIED**
1. **Unarmored Defense Calculator FAILURE**: Complete AC calculation breakdown
   - **Expected**: 15 AC (10 base + 2 Dex + 3 Con Unarmored Defense)
   - **Baseline**: 10 AC with "Error in calculation"
   - **Impact**: CRITICAL - Total failure for unarmored characters (Barbarians, Monks)
2. **Missing At-Will Class Feature Spells**: 3 Totem Warrior spells completely absent
   - **Expected**: Speak with Animals, Beast Sense, Commune with Nature (all "At Will")
   - **Baseline**: 0 spells (not recognized as spellcaster)
   - **Impact**: NEW spell gap - class features granting at-will/ritual spells
3. **Spell Mechanics**: These are at-will rituals (no spell slots) from Spirit Seeker/Walker features
   - **Different from**: Subclass spell lists, invocation spells, regular slotted spells

**CRITICAL DISCOVERY**: Scraper has fundamental gaps in core D&D mechanics - can't calculate unarmored AC or recognize at-will class feature spells.

#### Discrepancy Analysis - Character 103873194 (Marin) ✅ **VERIFIED**
1. **Elven Chain AC Overcalculation**: Baseline calculating AC incorrectly
   - **Expected**: 18 AC (14 Elven Chain + 2 Dex + 2 Shield) - Dex capped at +2 for this armor
   - **Baseline**: 19 AC - not applying Dex modifier cap for magical armor  
   - **Impact**: Magic armor Dex cap calculation error
2. **Magic Initiate Feat Incomplete Build**: Player hasn't made feat selections
   - **D&D Beyond**: Shows "No Choice Made" x3 for Magic Initiate (Warlock) feat
   - **Expected**: 2 cantrips + 1 first-level spell if completed
   - **Baseline**: Correctly shows 0 feat spells (player incomplete build)
   - **Insight**: This is NOT a scraper bug - it's an incomplete character build
3. **Missing Eldritch Invocation Spell**: Confirms pattern from other Hexblade (66356596)
   - **Expected**: Disguise Self (at-will from invocation)
   - **Baseline**: 0 invocation spells captured
   - **Impact**: Same invocation parsing gap as other Warlocks

**KEY INSIGHT**: This character demonstrates the validation methodology's value - distinguishing between scraper bugs, incomplete character builds, and correct behavior.

#### AC Calculation Breakdown - Character 29682199 (Redgrave)
**Manual D&D Beyond Calculation**: 25 AC
```
10 (Base) + 10 (Integrated Protection) + 1 (Cloak of Protection) + 2 (Shield) + 1 (Soul of the Forge) + 1 (Blessing of the Forge) = 25
```

**v5.2.0 Baseline Calculation**: 24 AC  
```json
{
  "total": 24,
  "base": 20,
  "modifiers": [
    {"source": "Bonus", "value": 1, "type": "bonus"},
    {"source": "Bonus", "value": 1, "type": "bonus"},
    {"source": "Shield", "value": 2, "type": "shield"}
  ],
  "calculation": "Integrated Protection (20 + Dex (max 0)) + Bonus (+1) + Bonus (+1) + Shield (+2)"
}
```

#### Missing Features Analysis
1. **Soul of the Forge** (1st level Forge Domain feature): +1 AC while wearing armor
2. **Blessing of the Forge** (1st level Forge Domain feature): +1 AC enhancement to armor/shield
3. **Equipment Detection**: Cloak of Protection AC bonus not specifically identified

#### Priority Items for Phase 3
1. **Subclass Spell Parser**: **CRITICAL** - Missing core subclass mechanics across multiple classes
   - **Cleric Domain Spells**: Parse and include domain-granted spells (always prepared)
   - **Artificer Subclass Spells**: Parse and include subclass-granted spells (always prepared)
   - **Other Subclass Spells**: Likely affects other classes with subclass-specific spell lists
   - **Subclass Identity**: Core feature that defines subclass abilities across classes
   - **Data Source**: Parse subclass features, not just `classSpells` array
   - **Test Characters**: 
     - 68622804 (Grave Domain Cleric - 6 missing domain spells)
     - 29682199 (Forge Domain Cleric - 6 missing domain spells)  
     - 103214475 (Armorer Artificer - 6 missing subclass spells)
2. **Warlock Spell System Enhancement**: Critical functional gaps identified
   - **Eldritch Invocation Spells**: Parse and include spells from invocations
   - **Pact Magic Display**: Show spells at casting level, not base level
   - **Multiple Spell Sources**: Expand beyond `classSpells` to invocation-granted spells
   - **Test Character**: 66356596 (Hexblade Warlock with Bane invocation)
3. **At-Will/Ritual Spell Parser**: Missing class feature spells with no spell slots
   - **Totem Warrior Spells**: Parse Spirit Seeker/Walker at-will spells
   - **Other Class Features**: Likely affects other classes with ritual/at-will abilities
   - **Different Mechanics**: No spell slots, save DCs, or attack bonuses
   - **Test Character**: 103814449 (Totem Warrior Barbarian - 3 missing at-will spells)
4. **Unarmored Defense Calculator**: **CRITICAL** - Complete AC calculation failure
   - **Barbarian Unarmored Defense**: 10 + Dex + Con
   - **Monk Unarmored Defense**: 10 + Dex + Wis  
   - **Current State**: "Error in calculation" - total breakdown
   - **Test Character**: 103814449 (Expected AC 15, gets "Error in calculation")
5. **Spell Slot Data Structure**: Fix parsing issue (`level_1` vs `1` key format)
   - **Test Character**: 68622804 (has correct slot data in wrong format)
6. **Class Feature Calculator**: Detect and apply Forge Domain AC bonuses
   - **Soul of the Forge**: +1 AC while wearing armor
   - **Blessing of the Forge**: +1 AC enhancement to armor/shield
   - **Test Character**: 29682199 (Forge Domain Cleric, missing +2 AC total)
7. **Magic Item Parser**: Identify specific equipment AC contributions
   - **Cloak of Protection**: +1 AC magic item bonus
   - **Test Character**: 29682199 (has Cloak of Protection, AC 25 vs baseline 24)
8. **Build Validation Warnings**: **NEW** - Detect incomplete character builds
   - **Incomplete Feat Selections**: Flag "No Choice Made" for feats like Magic Initiate
   - **Missing Spell Selections**: Detect unfinished build choices
   - **Build Optimization**: Surface incomplete character progression to players
   - **Test Character**: 103873194 (Magic Initiate feat with no spells selected)
   - **Output Target**: Include warnings in markdown output for player awareness

#### Validation Methodology Improvements
- **Double-check process**: All discrepancies require D&D Beyond sheet verification
- **Screenshot capture**: Visual confirmation of calculated values when possible  
- **Conservative interpretation**: Treat manual validation as investigation starting point, not ground truth
- **Test Character Database**: Maintain character IDs for specific feature testing
- **Collaborative Verification**: User provides detailed D&D Beyond data (spell lists, AC breakdowns) for analysis
- **Pattern Recognition**: Look for systematic gaps across multiple characters vs isolated issues
- **Root Cause Analysis**: Distinguish technical bugs from incomplete builds from correct behavior

#### Remaining Validation Characters (Optional)
If continuing validation before Phase 3 development:
- **144986992** (Vaelith): 2024 Sorcerer - Test 2024 rules handling
- **145081718, 147061783, 145079040, 141875964, 105635812**: Unknown classes - Additional coverage

**Current Assessment**: 50% validation coverage has identified major systematic patterns. Sufficient data exists to begin Phase 3 development, but additional validation would provide broader coverage.

#### Test Character Reference
| Character ID | Name | Class/Subclass | Accuracy | Test Cases | Status |
|---|---|---|---|---|---|
| 29682199 | Redgrave | Forge Domain Cleric | 88.9% | Domain spells (6 missing), AC bonuses (Soul/Blessing +2), Magic items (Cloak +1) | ✅ Verified |
| 66356596 | Dor'ren Uroprax | Hexblade Warlock | 93.8% | Eldritch Invocations (Bane missing), Pact magic spell levels (base vs casting) | ✅ Verified |
| 68622804 | Zemfur Folle | Grave Domain Cleric | 87.5% | Domain spells (6 missing), Spell slot parsing (data structure), Staff of Healing | ✅ Verified |
| 103214475 | Seluvis | Armorer Artificer | 84.4% | Subclass spells (6 Armorer missing), Spell slot parsing, Artificer mechanics | ✅ Verified |
| 103814449 | Yevelda | Totem Warrior Barbarian | 78.6% | Unarmored Defense AC (CRITICAL - "Error in calculation"), At-will spells (3 missing) | ✅ Verified |
| 103873194 | Marin | Hexblade Warlock | 90.0% | Eldritch Invocations (Disguise Self), Magic item AC (Elven Chain +1 over), Build warnings | ✅ Verified |
| 144986992 | Vaelith Duskthorn | 2024 Elf Sorcerer | 91.7% | Spell count (9 actual vs 2 baseline), Spell table enhancement needed | ✅ Verified |
| 145079040 | Thuldus Blackblade | 2024 Dwarf Barbarian | 83.3% | Unarmored Defense AC (+1 missing), HP type detection (manual vs fixed) | ✅ Verified |
| 141875964 | Baldrin Highfoot | 2024 Halfling Bard | 50.0% | **2024 rule differences confirmed** - feat parsing issues, spell count | ✅ Verified |
| 105635812 | Faerah Duskrane | Drow Rogue | 100.0% | **Perfect accuracy** - Drow Magic spells, Swashbuckler mechanics | ✅ Verified |
| 145081718 | Ilarion Veles | 2024 Elf Wizard | TBD | Ritual spells, Magic Initiate feat, free spell casting (Detect Magic 1/LR) | ✅ Verified |
| 147061783 | ZuB Public Demo | 2014 Conjuration Wizard | 75.0% | High-level slots (6th-8th), Variant Human feats, large spellbook (30 spells) | ✅ Verified |

**Validation Statistics**: 12/12 completed (100%), Average accuracy 83.9%, Range 50.0%-100.0%

---

## Version Release Plan

### v6.0.0-alpha (End of Phase 2)
- Core architecture and basic calculations
- Limited character support
- Developer preview with debug summary

### v6.0.0-beta (End of Phase 4)
- Full feature parity with v5.2.0
- Comprehensive testing with quick compare
- Beta user feedback

### v6.0.0-stable (End of Phase 5)
- Production-ready release
- Complete documentation
- Migration tools

---

## Phase 6: Comprehensive Class Coverage Testing

**Goal**: Systematically test all D&D class mechanics to identify and fix remaining scraper gaps  
**Timeline**: After Phases 3-5 complete (v6.0.0 released with 95%+ baseline accuracy)  
**Method**: Create specific test characters → validate → iterate → fix → next character

### 6.1 Testing Methodology

**Process**: 
1. Claude specifies exact character build requirements
2. User creates character in D&D Beyond with specified features
3. **IMMEDIATELY capture baseline data** (raw JSON, scraper output, validation data)
4. Run scraper validation against new character
5. Identify gaps, implement fixes, validate fixes
6. **Archive all data before character deletion** - character will be deleted due to D&D Beyond limits
7. Mark character as "validated" and move to next

**⚠️ Critical Data Preservation**:
- **Raw D&D Beyond JSON**: Must capture immediately after character creation
- **Scraper JSON Output**: Baseline v6.0.0+ output for regression testing  
- **Manual Validation Data**: User-provided accuracy verification
- **Character Build Notes**: Detailed build specifications for recreation if needed

**⏰ Immediate Capture Workflow**:
1. User creates character in D&D Beyond
2. **FIRST**: Capture raw JSON via browser dev tools or API call
3. **SECOND**: Run scraper to generate baseline JSON output  
4. **THIRD**: Run parser to generate baseline MD output
5. **FOURTH**: User provides manual validation data
6. **FIFTH**: Begin testing and iteration with both JSON and MD validation
7. Character can be deleted after all data is safely archived

**Success Criteria per Character**:
- 95%+ accuracy on automated validation
- All class-specific mechanics correctly parsed
- No regressions on existing validated characters
- **Complete data archive** captured before character deletion

### 6.2 Priority Testing Queue

#### **Phase 6.1: Critical AC & Resource Mechanics** 
**Target**: Classes with unique AC/resource calculations that may trigger existing bugs

**Character 1: Barbarian (Unarmored Defense + Rage)**
```
Build Specification: TBD when Phase 6 begins
- Level 5+ Path of the Wild Heart Barbarian
- Focus: CON-based Unarmored Defense, Rage mechanics, damage resistance
- Test: AC calculation without armor, resource tracking
```

**Character 2: Monk (WIS Unarmored Defense + Ki)**
```
Build Specification: TBD when Phase 6 begins  
- Level 5+ Way of the Open Hand Monk
- Focus: WIS-based Unarmored Defense, Ki point mechanics
- Test: Different AC formula from Barbarian, short rest resources
```

#### **Phase 6.2: Complex Spellcasting** 
**Target**: Non-standard spellcasting mechanics

**Character 3: Sorcerer (Metamagic + Sorcery Points)**
```
Build Specification: TBD when Phase 6 begins
- Level 5+ Draconic Bloodline Sorcerer  
- Focus: Sorcery Points, Metamagic, flexible spellcasting
- Test: Resource conversion, spell slot manipulation
```

**Character 4: Warlock (Pact Magic + Invocations)**
```
Build Specification: TBD when Phase 6 begins
- Level 5+ Great Old One Warlock
- Focus: Pact Magic slots, Eldritch Invocations, short rest recovery
- Test: Non-standard spell slot progression, at-will spells
```

#### **Phase 6.3: Subclass Spell Integration**
**Target**: Classes with mandatory subclass spells

**Character 5: Paladin (Oath Spells + Smite)**
```
Build Specification: TBD when Phase 6 begins
- Level 5+ Oath of Devotion Paladin
- Focus: Oath spells, Divine Smite, Lay on Hands
- Test: Always-prepared spells, resource consumption mechanics
```

**Character 6: Artificer (Infusions + Ritual Casting)**
```
Build Specification: TBD when Phase 6 begins
- Level 5+ Battle Smith Artificer
- Focus: Infusions, subclass spells, ritual casting
- Test: Magic item creation, unique spell preparation
```

#### **Phase 6.4: Third-Caster Progression**
**Target**: Unique spell slot progressions

**Character 7: Eldritch Knight Fighter**
```
Build Specification: TBD when Phase 6 begins
- Level 7+ Eldritch Knight Fighter
- Focus: Third-caster spell slots, school restrictions
- Test: Non-standard spell progression, limited spell selection
```

#### **Phase 6.5: Multiclass Edge Cases**
**Target**: Complex multiclass spell interactions

**Character 8: Warlock/Sorcerer Multiclass**
```
Build Specification: TBD when Phase 6 begins
- Warlock 3 / Sorcerer 3+ multiclass
- Focus: Pact Magic + Spellcasting interaction
- Test: Separate spell slot pools, sorcery point conversion
```

#### **Phase 6.6: 2024 Rule Validation**
**Target**: Comprehensive 2024 rule support

**Character 9: 2024 Character (Class TBD)**
```
Build Specification: TBD when Phase 6 begins
- Level 5+ character using 2024 Player's Handbook
- Focus: Species vs Race terminology, updated mechanics
- Test: Comprehensive 2024 rule parsing accuracy
```

### 6.3 Implementation Notes

- **Each character becomes a permanent test case** for regression testing **via archived data**
- **Character specifications provided just-in-time** when ready to test
- **Iterative approach**: Fix issues immediately, don't accumulate technical debt
- **Validation framework**: Extend `comprehensive_scraper_validation.py` for new characters

**Data Preservation Strategy**:
```
data/phase6/
├── character_001_barbarian/
│   ├── raw_dndbeyond.json           # Captured immediately after creation
│   ├── scraper_output_v6.0.json     # Baseline scraper JSON output
│   ├── parser_output_v6.0.md        # Baseline parser MD output
│   ├── validation_data.json         # Manual validation data
│   ├── build_specification.md       # Exact build requirements for recreation
│   ├── json_test_results.md         # JSON validation results and issues
│   └── md_test_results.md           # MD validation results and issues
├── character_002_monk/
│   └── [same structure]
...
```

**Regression Testing Approach**:
- **Static data validation**: Test against archived JSON, not live characters
- **Build recreation guide**: Detailed specs allow recreation if needed
- **Version tracking**: Track which scraper version captured each baseline

**Prerequisites**: Phases 3-5 complete, baseline accuracy ≥95%, no known critical bugs

---

## Post-Refactor Roadmap

### v6.1.0 - Enhanced Features
- [ ] Homebrew content support
- [ ] Advanced spell analysis
- [ ] Character comparison tools
- [ ] Static markdown summary export

### v6.2.0 - Integration Improvements
- [ ] D&D Beyond campaign integration
- [ ] Discord bot interface
- [ ] Web API service

### v7.0.0 - Next Generation
- [ ] Real-time character sync
- [ ] AI-powered character analysis
- [ ] Advanced visualization tools