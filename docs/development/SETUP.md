# D&D Character Scraper - Complete Setup Guide

This guide will help you set up the D&D Character Scraper to generate beautiful character sheets in Obsidian with full functionality.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Python Dependencies](#python-dependencies)
3. [Obsidian Plugins](#obsidian-plugins)
4. [CSS Styling](#css-styling)
5. [Manual Usage](#manual-usage)
6. [Obsidian Integration](#obsidian-integration)
7. [Embedding Sections](#embedding-sections)
8. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Required Software

1. **Python 3.8+** - Download from [python.org](https://www.python.org/downloads/)
   - During installation, make sure to check "Add Python to PATH"
2. **Obsidian** - Download from [obsidian.md](https://obsidian.md/)
3. **Git** (optional) - For cloning the repository

### Verify Installation

Open Command Prompt or PowerShell and verify:

```bash
python --version
# or
python3 --version
```

Should return Python 3.8 or higher.

---

## Python Dependencies

### Install Required Packages

Navigate to the scraper directory and install dependencies:

```bash
cd "C:/Users/[USERNAME]/Documents/DnD/CharacterScraper"
pip install -r requirements.txt
```

Or install manually:

```bash
pip install requests beautifulsoup4
```

### Verify Installation

Test the scraper works:

```bash
python enhanced_dnd_scraper.py --help
```

---

## Obsidian Plugins

### Required Plugins

#### 1. BRAT (Beta Reviewers Auto-update Tester)
- **Installation**:
  1. Open Obsidian Settings → Community Plugins
  2. Turn off Safe Mode (if enabled)
  3. Click "Browse" and search for "BRAT"
  4. Install and enable the plugin

#### 2. D&D UI Toolkit
- **Repository**: https://github.com/hay-kot/obsidian-dnd-ui-toolkit
- **Installation** (requires BRAT):
  1. Open BRAT plugin settings
  2. Click "Add Beta Plugin"
  3. Enter: `hay-kot/obsidian-dnd-ui-toolkit`
  4. Click "Add Plugin"
  5. Enable the plugin in Community Plugins

#### 3. Execute Code
- **Repository**: https://github.com/twibiral/obsidian-execute-code
- **Installation**:
  1. In Community Plugins, search for "Execute Code"
  2. Install and enable the plugin
  3. In plugin settings, ensure Python execution is enabled

### Plugin Configuration

#### Execute Code Settings
1. Go to Settings → Execute Code
2. Ensure these languages are enabled:
   - Python
3. Set Python command to `python` or `python3` (whichever works on your system)

---

## CSS Styling (Optional)

The CSS styling is **optional** and only improves the appearance of the refresh button. Character sheets work perfectly without it.

### Install Custom CSS

1. **Copy the CSS file**: Copy `character-scraper-styles.css` to your vault
2. **Enable CSS Snippets**:
   - Go to Settings → Appearance → CSS Snippets
   - Click the folder icon to open snippets folder
   - Copy `character-scraper-styles.css` to this folder
   - Refresh the snippets list and enable "character-scraper-styles"

### What the CSS Does

- Creates clean "🔄 Refresh Character Data" button with proper alignment
- Hides Python code while keeping functionality
- Styles Run and Clear buttons consistently
- Without CSS: You'll see a plain Execute Code run button (still functional)

---

## Manual Usage

### Command Line Usage

#### Basic Scraping
```bash
# Generate character sheet for specific ID
python run_scraper.py [CHARACTER_ID] "[OUTPUT_FILE].md"

# Examples:
python run_scraper.py 66356596 "My Character.md"
python run_scraper.py 105635812 "Faerah Duskrane.md"
```

#### Advanced Options
```bash
# With session cookie for private characters
python run_scraper.py 66356596 "Character.md" --session "your_session_cookie"

# Verbose output for debugging
python run_scraper.py 66356596 "Character.md" --verbose

# Custom scraper path
python run_scraper.py 66356596 "Character.md" --scraper-path "./custom_scraper.py"
```

#### Direct Scraper Usage
```bash
# Just get JSON data
python enhanced_dnd_scraper.py 66356596

# Specify output file
python enhanced_dnd_scraper.py 66356596 --output "character.json"

# Private character with session
python enhanced_dnd_scraper.py 66356596 --session "your_session_cookie"

# Debug mode
python enhanced_dnd_scraper.py 66356596 --verbose
```

### Batch Processing
```bash
# Process multiple characters (add delays to avoid rate limiting)
python run_scraper.py 105635812 "105635812.md"
sleep 30
python run_scraper.py 103873194 "103873194.md"
sleep 30
python run_scraper.py 29682199 "29682199.md"
```

---

## Obsidian Integration

### In-Vault Refresh

Each generated character sheet includes a refresh button that works within Obsidian:

1. **Locate the refresh section** at the top of any character sheet
2. **Click the Run button** (▶️) to update character data
3. **Wait for success message**, then reload the file to see changes

### Automatic Path Detection

The refresh functionality automatically detects:
- Current vault path
- Current file location
- Script directory location

No manual configuration needed!

---

## Embedding Sections

### Available Block References

Each character sheet includes these embeddable sections:

```markdown
# Character Info
![[Character Name#^character-info]]

# Character Statistics  
![[Character Name#^character-statistics]]

# Abilities & Skills
![[Character Name#^abilities-skills]]

# Appearance
![[Character Name#^appearance]]

# Spellcasting (Complete Section)
![[Character Name#^spellcasting]]

# Spellcasting Stats
![[Character Name#^spellstats]]

# Spell Slots
![[Character Name#^spellslots]]

# Spell Table
![[Character Name#^spelltable]]

# Spell Descriptions
![[Character Name#^spells]]

# Features
![[Character Name#^features]]

# Racial Traits
![[Character Name#^racial-traits]]

# Attacks
![[Character Name#^attacks]]

# Proficiencies
![[Character Name#^proficiencies]]

# Background
![[Character Name#^background]]

# Backstory & Notes
![[Character Name#^backstory]]

# Inventory
![[Character Name#^inventory]]
```

### Embedding Examples

#### Campaign Overview
```markdown
# Party Members

## Faerah Duskrane
![[Faerah Duskrane#^character-info]]

## Marin  
![[Marin#^character-info]]

## Redgrave
![[Redgrave#^character-info]]
```

#### Combat Reference
```markdown
# Combat Stats

## Initiative Order
![[Faerah Duskrane#^character-statistics]]
![[Marin#^character-statistics]]

## Attacks
![[Faerah Duskrane#^attacks]]
![[Marin#^attacks]]
```

#### Spell Reference
```markdown
# Party Spellcasters

## Marin's Spells
![[Marin#^spellstats]]
![[Marin#^spelltable]]

## Redgrave's Spells  
![[Redgrave#^spellstats]]
![[Redgrave#^spelltable]]
```

---

## Troubleshooting

### Python Issues

#### "Module not found: requests"
```bash
pip install requests beautifulsoup4
# or
python -m pip install requests beautifulsoup4
```

#### "Python not found"
- Verify Python is in system PATH
- Try `python3` instead of `python`
- Reinstall Python with "Add to PATH" checked

#### Permission errors
```bash
# Use --user flag
pip install --user requests beautifulsoup4
```

### Obsidian Issues

#### Execute Code plugin not working
1. Check plugin is enabled in Settings → Community Plugins
2. Verify Python path in Execute Code settings
3. Test with simple code: `print("Hello World")`
4. Check developer console (Ctrl+Shift+I) for errors

#### CSS not applying
1. Ensure CSS snippets are enabled in Settings → Appearance
2. Refresh snippets list after copying CSS file
3. Check CSS file has `.css` extension
4. Try disabling/re-enabling the snippet

#### Refresh button not working
1. Verify Execute Code plugin is installed and enabled
2. Check Python is accessible: run `python --version` in terminal
3. Ensure character file is in an Obsidian vault
4. Try manually running: `python run_scraper.py [ID] "[file]"`

### Character Data Issues

#### "Character not found"
- Verify character ID is correct (number from D&D Beyond URL)
- Check character is public or provide session cookie
- Test character loads in browser first

#### "Network error"
- Check internet connection
- Verify D&D Beyond is accessible
- Try again later (may be temporary server issue)

#### Private character access
```bash
# Get session cookie from browser Developer Tools → Application → Cookies
python run_scraper.py 66356596 "character.md" --session "your_session_cookie"
```

#### Unicode/encoding errors
- Ensure your terminal supports UTF-8
- Use Command Prompt or PowerShell on Windows
- Files are saved with UTF-8 encoding automatically

### File Path Issues

#### "File not found" errors
- Use absolute paths: `"C:/Users/Username/Documents/Character.md"`
- Escape spaces: `"My Character Sheet.md"`
- Check file permissions in target directory

#### Script path configuration
Update script directory in generated files if you move the scraper:
```python
script_dir = r'C:/Path/To/Your/CharacterScraper'
```

---

## Configuration

### Default Paths

The scraper assumes these default locations:
- **Script**: `C:/Users/[USERNAME]/Documents/DnD/CharacterScraper/`
- **Output**: Current working directory or specified path
- **Vault**: Auto-detected by Obsidian Execute Code plugin

### Customization

#### Change script location
Edit the generated markdown files:
```python
script_dir = r'C:/Your/Custom/Path/CharacterScraper'
```

#### Modify CSS styling
Edit `character-scraper-styles.css` and refresh in Obsidian

#### Adjust output format
Modify `run_scraper.py` to customize markdown output

---

## Getting Help

### Check Logs
- Run with `--verbose` flag for detailed output
- Check Obsidian Developer Console (Ctrl+Shift+I)
- Look for error messages in terminal output

### Common Solutions
1. **Restart Obsidian** after installing plugins
2. **Reload files** after running refresh (Ctrl+R)
3. **Check file paths** are correct and accessible
4. **Verify Python installation** with `python --version`
5. **Test network connectivity** to D&D Beyond

### Support Resources
- **Enhanced Scraper Issues**: Check scraper output with `--verbose`
- **D&D UI Toolkit**: https://github.com/hay-kot/obsidian-dnd-ui-toolkit
- **Execute Code Plugin**: https://github.com/twibiral/obsidian-execute-code
- **Obsidian Help**: https://help.obsidian.md/

---

## Version Information

- **Scraper Version**: 5.2.0
- **Enhanced Features**: 2024 Player's Handbook support
- **Template Version**: 1.0
- **Last Updated**: 2025-06-23

Generated character sheets include version information in frontmatter for tracking compatibility.