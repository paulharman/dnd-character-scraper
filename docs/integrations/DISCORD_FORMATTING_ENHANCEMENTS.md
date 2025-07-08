# Discord Message Formatting Enhancements

## Overview

Enhanced the Discord webhook notification system with optimized formatting specifically designed for D&D gameplay monitoring. The new enhanced format provides concise, context-aware messages perfect for Discord chat while preserving all essential information.

## Key Improvements

### 1. **Optimized Message Conciseness**
- Reduced message length while preserving essential information
- Used Discord formatting features (bold, emojis) strategically
- Grouped related changes to minimize noise
- Removed redundant information

### 2. **Enhanced Old/New Value Display**
- Clearer old → new value changes with context
- Better formatting for numeric changes (HP, XP, AC)
- Contextual emojis for different change types
- Percentage and difference calculations where relevant

### 3. **Intelligent Change Categorization**
- **Critical**: Level changes, major HP loss (>25% max HP), death saves
- **Combat**: AC, initiative, speed, hit points, saving throws
- **Progression**: Experience, ability scores, proficiency, feats, spell slots
- **Equipment**: Inventory, wealth, currency
- **Spells**: Spell lists, spellcasting abilities
- **Other**: Everything else

### 4. **Discord-Specific Optimization**
- Concise header with game die emoji (🎲)
- Context-aware emojis for different change types
- Optimized for mobile Discord viewing
- Stays well under Discord's 2000 character limit
- Summary counts for grouped changes

### 5. **Real-World D&D Usage Focus**
- Prioritizes changes that matter to players/DMs
- Reduces noise for minor metadata changes
- Highlights significant character progression
- Makes messages scannable at a glance

## Formatting Examples

### Level-Up Scenario
```
🎲 **Elara Moonwhisper**
🎆 **Level 4 → 5**
💪 Max HP: 32 → **38**
🌟 **+1500 XP**
✨ Level_3: **2 slots**
🎆 Feat: **Fey Touched**
💪 Charisma: 14 → **16**
```

### Combat Scenario
```
🎲 **Elara Moonwhisper**
🩸 HP: 38 → **22** (-16)
🛡️ Temp HP: **8**
✨ Level_1: 4 → **3**
```

### Equipment Change
```
🎲 **Elara Moonwhisper**
🛡️ AC: 12 → **13**
🔄 Leather Armor → **Studded Leather**
➕ **Ring of Protection**
```

## Implementation Details

### Format Types Available:
1. **Compact**: Ultra-concise for mobile, shows only critical changes
2. **Detailed**: Enhanced categorized view with all changes organized
3. **Enhanced**: New optimized format for real D&D gameplay
4. **JSON**: Raw data format for debugging

### Configuration Support:
- Users can choose message verbosity level
- Filtering system supports different message styles
- Compatible with existing data group filtering
- Backward compatible with all existing presets

### Technical Features:
- Smart HP change classification (critical vs normal)
- Context-aware emoji selection
- Category-based change grouping
- Summary generation for multiple changes
- Character limit optimization

## Usage

### Command Line:
```bash
# Use enhanced format
python discord_notifier.py 145081718 --format enhanced

# Enhanced format with specific filtering
python discord_notifier.py 145081718 --format enhanced --preset level_up
```

### Configuration File:
```yaml
format_type: "enhanced"
filtering:
  preset: "level_up"
```

## Benefits for D&D Gameplay

1. **Immediate Recognition**: Critical changes like level-ups are immediately visible
2. **Combat Awareness**: HP changes clearly show damage vs healing
3. **Progression Tracking**: Experience and ability score improvements are highlighted
4. **Equipment Monitoring**: Gear changes are clearly formatted
5. **Mobile Friendly**: Optimized for Discord mobile apps
6. **Channel Friendly**: Concise enough to not spam chat channels

## Testing

The enhanced formatting has been tested with:
- Level-up scenarios (multiple stat changes)
- Combat scenarios (HP damage/healing)
- Equipment changes (AC modifications, new items)
- Mixed scenarios (all change types together)
- Character limits (all scenarios stay well under 2000 chars)

## Future Enhancements

Potential future improvements:
- Customizable emoji sets
- Localization support
- Integration with D&D Beyond character portraits
- Support for rich embeds in addition to text messages
- Automated severity detection based on character level