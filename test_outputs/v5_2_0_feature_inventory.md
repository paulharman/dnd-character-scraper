# v5.2.0 Feature Preservation Checklist

## Core API & Data Extraction Features

### ✅ API Integration
- **User Agent**: `'DnDBeyond-Enhanced-Scraper/5.2.0'`
- **Retry Logic**: Exponential backoff with randomization (MAX_RETRIES = 3)
- **Session Cookie Support**: `--session` flag for private characters
- **Rate Limiting**: Respect D&D Beyond API limits
- **Request Headers**: Proper User-Agent and session handling

### ✅ Command Line Interface
- **Character ID**: Required positional argument
- **Output File**: `--output` flag with JSON export
- **Session Cookie**: `--session` flag for authentication  
- **Verbose Mode**: `--verbose` flag for detailed logging
- **Configuration Variables**: VERBOSE_OUTPUT, INCLUDE_RAW_DATA, etc.

### ✅ Core Data Extraction
- **Complete Character Data**: All API fields preserved
- **Ability Scores**: With source breakdown and modifiers
- **Classes & Subclasses**: Including hit die mapping
- **Species/Race**: With 2024 vs 2014 terminology
- **Background**: Including granted features and spells
- **Feats**: Complete feat resolution system
- **Inventory**: Enhanced magic item properties and charges
- **Actions**: Basic action parsing from API data

## Spellcasting System Features

### ✅ Spell Parsing & Organization
- **Multiple Sources**: `classSpells`, top-level `spells` dict (race/feat/item)
- **Spell Deduplication**: Advanced grouping by source with provenance tracking
- **Background Spells**: Detection via `spellListIds` with separate API calls
- **Spell Metadata**: Components, casting time, range, duration, concentration
- **Source Attribution**: Detailed `source_info` structure with `granted_by` information

### ✅ Multiclass Spellcasting
- **Total Caster Level**: `_calculate_total_caster_level()` with multiclass progression
- **Full Casters**: Wizard, Sorcerer, Cleric, Druid, Bard, Warlock (full progression)
- **Half Casters**: Paladin, Ranger (half progression), Artificer (rounds up)
- **Third Casters**: Eldritch Knight, Arcane Trickster (1/3 progression starting at level 3)
- **Spell Slot Separation**: `regular_slots` vs `pact_slots` structure

### ✅ Warlock Pact Magic
- **Separate Pact Slots**: Independent from regular spell slots
- **Pact Progression**: Proper slot count and level by Warlock level
- **Level-based Scaling**: 
  - Level 1: 1 slot (1st level)
  - Level 2: 2 slots (1st level)  
  - Level 3-4: 2 slots (2nd level)
  - Level 5-6: 2 slots (3rd level)
  - Level 7-8: 2 slots (4th level)
  - Level 9-10: 2 slots (5th level)
  - Level 11-16: 3 slots (5th level)
  - Level 17-20: 4 slots (5th level)

### ✅ Spell Preparation System
- **Preparation Types**: 
  - `"known"` - Bard, Sorcerer, Warlock (fixed spells)
  - `"prepared_from_list"` - Cleric, Druid, Paladin (full class list)
  - `"prepared_from_book"` - Wizard (spellbook limited)
- **Always Prepared**: Racial, feat, and domain spells
- **Effective Prepared**: Includes ritual logic for Wizards
- **Ritual Casting**: Special handling for unprepared ritual spells

## Class-Specific Features

### ✅ Wizard Features
- **Spellbook System**: `prepared_from_book` preparation type
- **Ritual Casting**: Can cast ritual spells without preparing them
- **Spell Preparation**: Notes about cantrips/prepared/ritual/always-prepared
- **Arcane Recovery**: Class feature detection and description
- **Spell Mastery**: High-level wizard feature tracking

### ✅ Sorcerer Features  
- **Sorcery Points**: `_get_sorcery_points()` = sorcerer level
- **Font of Magic**: Special processing with conversion table formatting
- **Metamagic**: Detection and bonus action classification
- **Spell Slot Conversion**: Table for sorcery points ↔ spell slots
- **Special Formatting**: Enhanced Font of Magic feature blocks

### ✅ Warlock Features
- **Pact Magic**: Separate from regular spellcasting
- **Eldritch Invocations**: Feature detection and parsing
- **Patron Features**: Hexblade and other patron abilities
- **Short Rest Recovery**: Pact magic slot recovery mechanics

### ✅ Cleric Features  
- **Domain Spells**: Always prepared domain spell detection
- **Channel Divinity**: Class feature parsing
- **Divine Domain**: Subclass-specific abilities
- **Turn Undead**: Standard cleric feature tracking

### ✅ Other Class Features
- **Barbarian**: Rage, Unarmored Defense class features
- **Fighter**: Action Surge, Second Wind, Fighting Style
- **Rogue**: Cunning Action, Sneak Attack detection
- **Paladin**: Divine Smite, Lay on Hands tracking

## Enhanced Output Features (Parser)

### ✅ Checkbox Generation System
- **Rest Mechanics Detection**: Regex patterns for usage tracking
  ```python
  usage_patterns = [
      r"once.*long rest", r"once.*short rest", r"\d+.*per day", 
      r"regain.*on.*rest", r"spend.*spell slot", r"expend.*use",
      r"you can cast.*once", r"ability to cast.*way.*long rest"
  ]
  ```
- **Safe State Keys**: `get_safe_state_key()` for DnD UI Toolkit compatibility
- **Consumable Blocks**: Automatic checkbox generation for limited-use features
- **Usage Count Detection**: Parse numeric uses from descriptions

### ✅ Advanced Spell Tables
- **Preparation Status**: Always/Yes/No/Ritual/Known indicators
- **Class-Specific Display**: Different columns for prepared vs known casters
- **Wizard Ritual Handling**: Show unprepared rituals as "Ritual"
- **Source Attribution**: Clear spell source tracking in tables
- **Internal Links**: `[[#SpellName]]` format for Obsidian integration

### ✅ Action Economy Analysis
- **Action Categorization**: Actions, Bonus Actions, Reactions
- **Spell Action Types**: Parse casting time for action economy
- **Ongoing Effects**: Detect spells that provide different action types
- **Availability Filtering**: Only show prepared/known/always-available spells

### ✅ Special Resource Tracking
- **Sorcery Points**: Above spell slots as requested
- **Hit Points**: With hit dice type detection
- **Free Spell Casts**: Racial and feat-granted spell uses
- **Class Resources**: Rage, Action Surge, etc. with state tracking

## Rule Version Management

### ✅ 2024 vs 2014 Detection
- **Source ID Checking**: `SOURCE_2024_IDS = {145, 146, 147, 148, 149, 150}`
- **Terminology Handling**: Species vs Race based on rule version
- **Ability Score Improvements**: Different feat handling between versions
- **Rule-Specific Progressions**: Spell slot and class feature differences

### ✅ Backward Compatibility
- **2014 Fallback**: Graceful degradation for 2014 characters
- **Mixed Sources**: Handle characters with both 2014 and 2024 content
- **Legacy Support**: Maintain compatibility with existing output formats

## Diagnostic & Error Handling

### ✅ Comprehensive Diagnostics
- **Data Structure Exploration**: `_explore_data_structure()` for debugging
- **Spell Source Analysis**: `_explore_spell_sources()` validation
- **Missing Data Detection**: Identify gaps in character data
- **Diagnostic Reporting**: Detailed error context and recovery

### ✅ Validation Systems
- **Expected vs Actual**: Spell count validation
- **Build Validation**: Detect incomplete character builds
- **Error Recovery**: Graceful failure with partial data export
- **Verbose Logging**: Detailed debugging information when enabled

## Integration Features

### ✅ Parser Integration
- **JSON to Markdown**: Complete conversion pipeline
- **DnD UI Toolkit**: Full compatibility with Obsidian plugin
- **Enhanced Spell Data**: Optional local spell file enhancement
- **Cross-Platform**: Python replacement for PowerShell scripts

### ✅ External Data Sources
- **Local Spell Files**: Optional enhancement with `spells/*.md` files
- **Spell Suffix Pattern**: `"-xphb.md"` file matching
- **Fallback Handling**: API data when local files unavailable
- **Configuration Options**: `USE_ENHANCED_SPELL_DATA` toggle

## Critical Regex Patterns

### ✅ Feature Usage Detection
```python
usage_patterns = [
    r"once.*long rest", r"once.*short rest", r"\d+.*per day", 
    r"regain.*on.*rest", r"spend.*spell slot", r"expend.*use",
    r"you can cast.*once", r"ability to cast.*way.*long rest"
]
```

### ✅ Bonus Action Detection
```python
bonus_action_names = [
    "innate sorcery", "metamagic", "font of magic.*create"
]

bonus_action_patterns = [
    r'as a bonus action',
    # Additional patterns in code
]
```

### ✅ State Key Generation
```python
def get_safe_state_key(self, name: str, suffix: str = "") -> str:
    safe_name = name.lower().replace(' ', '_').replace("'", '').replace('-', '_')
    safe_name = re.sub(r'[^a-z0-9_]', '', safe_name)
    if safe_name and (safe_name[0].isdigit() or safe_name[0] == '_'):
        safe_name = f"item_{safe_name}"
```

## Output Format Compatibility

### ✅ JSON Structure Preservation
- **Nested Data**: Maintain all API structure
- **Calculated Fields**: Preserve all computed values
- **Metadata**: Include diagnostic and processing information
- **Backward Compatibility**: Support existing consumers

### ✅ Markdown Format Features
- **DnD UI Toolkit**: Full plugin compatibility
- **Obsidian Integration**: Internal links and formatting
- **Table Generation**: Spell tables, equipment, actions
- **Block Formatting**: Consumables, health points, spell slots

This checklist ensures 100% feature parity during the v6.0.0 refactor. Every feature, pattern, and integration point from v5.2.0 must be preserved or explicitly enhanced.