# Migration Guide: v5.2.0 → v6.0.0

This guide helps users migrate from the original v5.2.0 scripts to the new v6.0.0 modular architecture.

## 🔄 No Migration Required for Basic Usage

**Good news**: v6.0.0 is fully backward compatible! Your existing commands work unchanged.

```bash
# This v5.2.0 command...
python3 enhanced_dnd_scraper.py 144986992 --output char.json --verbose

# ...works exactly the same in v6.0.0 ✅
python3 enhanced_dnd_scraper.py 144986992 --output char.json --verbose
```

## 🆕 New Features You Can Use

### 1. Rule Version Control

```bash
# Force specific D&D rules (new in v6.0.0)
python3 enhanced_dnd_scraper.py 144986992 --force-2024
python3 enhanced_dnd_scraper.py 144986992 --force-2014

# Automatic detection with detailed reporting
python3 enhanced_dnd_scraper.py 144986992 --verbose
```

### 2. Enhanced Output Information

Your JSON output now includes additional fields:

```json
{
  "id": 144986992,
  "name": "Character Name",
  // ... all your existing v5.2.0 fields ...
  
  // 🆕 New v6.0.0 fields
  "rule_version": "2024",
  "rule_detection": {
    "version": "2024",
    "confidence": 0.95,
    "method": "primary_class",
    "evidence": [
      "Primary class source ID 142 (2024 PHB)",
      "Uses 'species' terminology (2024 rules)"
    ],
    "warnings": []
  },
  "scraper_version": "6.0.0"
}
```

## 🔧 Fixed Issues from v5.2.0

### Critical Bug Fixes

If you've been experiencing AC calculation issues, v6.0.0 fixes them:

- **Barbarian Unarmored Defense**: Now correctly `AC = 10 + DEX + CON` (was missing DEX)
- **Monk Unarmored Defense**: Now correctly `AC = 10 + DEX + WIS` (was missing DEX)

### Before (v5.2.0 Bug)
```json
{
  "armor_class": 13,  // Wrong! Missing DEX modifier
  "calculation_method": "unarmored_defense_barbarian"
}
```

### After (v6.0.0 Fixed)
```json
{
  "armor_class": 16,  // Correct! 10 + 3 DEX + 3 CON
  "calculation_method": "unarmored_defense_barbarian"
}
```

## 📁 File Organization Changes

### v5.2.0 Structure
```
CharacterScraper/
├── enhanced_dnd_scraper.py
└── dnd_json_to_markdown.py
```

### v6.0.0 Structure
```
CharacterScraper/
├── enhanced_dnd_scraper.py          # 🆕 New v6.0.0 version
├── dnd_json_to_markdown.py          # 🆕 New v6.0.0 version
├── archive/v5.2.0/                  # 📦 Your original scripts
│   ├── enhanced_dnd_scraper_v5.2.0_original.py
│   └── dnd_json_to_markdown_v5.2.0_original.py
└── src/                             # 🏗️ Modular architecture
```

## 🔄 Migration Strategies

### Option 1: Use v6.0.0 (Recommended)

Simply use the new scripts - they're backward compatible:

```bash
# Replace your old commands with these:
python3 enhanced_dnd_scraper.py 144986992
python3 dnd_json_to_markdown.py 144986992 output.md
```

**Benefits:**
- ✅ Bug fixes (Barbarian/Monk AC)
- ✅ Rule version detection
- ✅ Better error handling
- ✅ Enhanced validation
- ✅ All your existing options work

### Option 2: Keep Using v5.2.0

If you prefer the original scripts, they're preserved:

```bash
# Use the archived v5.2.0 scripts:
python3 archive/v5.2.0/enhanced_dnd_scraper_v5.2.0_original.py 144986992
python3 archive/v5.2.0/dnd_json_to_markdown_v5.2.0_original.py 144986992 output.md
```

**Use cases:**
- 🔒 Need exact v5.2.0 behavior
- 📊 Comparing v5.2.0 vs v6.0.0 output
- 🐛 Reporting bugs by comparing versions

### Option 3: Gradual Migration

Test v6.0.0 alongside v5.2.0:

```bash
# Test v6.0.0 output
python3 enhanced_dnd_scraper.py 144986992 --output v6_output.json

# Compare with v5.2.0 output
python3 archive/v5.2.0/enhanced_dnd_scraper_v5.2.0_original.py 144986992 --output v5_output.json

# Compare the files
diff v5_output.json v6_output.json
```

## 🧪 Validation and Testing

### Test Your Characters

Validate that v6.0.0 works correctly with your characters:

```bash
# Run comprehensive validation
python3 test_validation_framework.py 144986992

# Test specific character with verbose output
python3 enhanced_dnd_scraper.py 144986992 --verbose

# Run the test suite
python3 tests/run_all_tests.py
```

### Compare Outputs

Use the baseline comparison tool:

```bash
# Compare v6.0.0 vs v5.2.0 for your character
python3 tools/baseline/baseline_comparison.py 144986992
```

## ⚙️ Configuration Migration

### Environment Variables

v6.0.0 adds new environment variables you can use:

```bash
# New in v6.0.0 - customize behavior
export DNDBEYOND_DEFAULT_RULES=auto    # auto, 2014, 2024
export DNDBEYOND_MIN_DELAY=30.0        # Respect 30-second minimum
export DNDBEYOND_USER_AGENT="Your-App/1.0"

# Run with your settings
python3 enhanced_dnd_scraper.py 144986992
```

### Custom Configurations

Create `config/local.yaml` for advanced settings:

```yaml
api:
  timeout: 30
  min_delay: 20.0
  user_agent: "My-Custom-Scraper/1.0"

rules:
  default_version: "auto"  # "2014", "2024", or "auto"
  conservative_detection: true

logging:
  level: "INFO"
  debug: false
```

## 🔍 Troubleshooting Migration Issues

### Common Migration Problems

#### 1. Import Errors
```bash
# Error: No module named 'src'
# Solution: Run from project root directory
cd /path/to/CharacterScraper
python3 enhanced_dnd_scraper.py 144986992
```

#### 2. Different AC Values
```bash
# If you see different AC values, v6.0.0 is likely correct
# The old version had bugs with Unarmored Defense

# Test with verbose mode to see calculation details
python3 enhanced_dnd_scraper.py 144986992 --verbose
```

#### 3. Rule Version Detection
```bash
# If rule detection seems wrong, force the version
python3 enhanced_dnd_scraper.py 144986992 --force-2014
python3 enhanced_dnd_scraper.py 144986992 --force-2024
```

#### 4. Session Cookie Issues
```bash
# Session cookies work the same way
python3 enhanced_dnd_scraper.py 144986992 --session "your_cookie"
```

### Getting Help

1. **Check verbose output**: Add `--verbose` to see detailed processing
2. **Compare with v5.2.0**: Use archived scripts to compare
3. **Run validation**: Use `test_validation_framework.py`
4. **Check baseline data**: Look in `data/baseline/` for reference

## 📊 Feature Comparison

| Feature | v5.2.0 | v6.0.0 |
|---------|--------|--------|
| **Basic Scraping** | ✅ | ✅ |
| **Markdown Generation** | ✅ | ✅ |
| **Session Cookies** | ✅ | ✅ |
| **Verbose Logging** | ✅ | ✅ |
| **Rule Version Detection** | ❌ | ✅ |
| **Force Rule Version** | ❌ | ✅ |
| **Fixed AC Calculations** | ❌ | ✅ |
| **Enhanced Validation** | ❌ | ✅ |
| **Modular Architecture** | ❌ | ✅ |
| **Comprehensive Testing** | ❌ | ✅ |
| **Professional Error Handling** | ❌ | ✅ |

## 🎯 Migration Checklist

- [ ] Backup your existing scripts (they're in `archive/v5.2.0/`)
- [ ] Test v6.0.0 with your characters: `python3 enhanced_dnd_scraper.py YOUR_CHAR_ID --verbose`
- [ ] Compare AC values - v6.0.0 fixes Barbarian/Monk AC bugs
- [ ] Check rule version detection with `--verbose`
- [ ] Update any automation scripts to use new features
- [ ] Consider using `--force-2014` or `--force-2024` if needed
- [ ] Run validation: `python3 test_validation_framework.py YOUR_CHAR_ID`

## 🚀 Taking Advantage of v6.0.0

### Enhanced Debugging
```bash
# More detailed error reporting
python3 enhanced_dnd_scraper.py 144986992 --verbose --raw-output debug.json
```

### Rule Version Control
```bash
# Ensure consistent rule interpretation
python3 enhanced_dnd_scraper.py 144986992 --force-2024
```

### Professional Validation
```bash
# Validate your character data
python3 test_validation_framework.py 144986992
```

### Comprehensive Testing
```bash
# Test the entire system
python3 tests/run_all_tests.py
```

## 📞 Support During Migration

If you encounter issues during migration:

1. **Check the troubleshooting section** in README.md
2. **Use the archived v5.2.0 scripts** as a fallback
3. **Run validation tools** to identify specific issues
4. **Enable verbose logging** to understand what's happening
5. **Compare outputs** between v5.2.0 and v6.0.0

Remember: **v6.0.0 is designed to be a drop-in replacement** that just works better!

---

**Migration Support**: The v5.2.0 scripts will remain available indefinitely in the `archive/` directory for compatibility and comparison purposes.