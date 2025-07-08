# Test Outputs and Temporary Files

This directory contains generated test files, temporary outputs, and development artifacts.

## 📁 Contents

### Test Character Sheets
- `character_145081718*.md` - Various test versions of Ilarion character sheet
- `ilarion_*.md` - Different formatting tests and iterations
- `validation_output/` - Automated validation outputs

### Test Data Files  
- `character_145081718.json` - Test character JSON data
- `complex_character.json` - Complex character for edge case testing
- `temp_*.json` - Temporary debugging files
- `ilarion_*.json` - Character data at various processing stages

### Development Files
- `temp_*.md` - Temporary markdown outputs during development
- `current_*.md` - Current state snapshots
- `fixed_*.md` - Bug fix iterations
- `v5_*.md` - Version 5.2.0 comparison files

## ⚠️ Important Notes

- **DO NOT DELETE**: These files may be referenced by tests
- **Temporary**: Many files are for development and debugging
- **Validation**: Some files are used by the validation test suite
- **Archive**: Consider moving old files to archive/ when no longer needed

## 🔧 Cleanup

To clean up old test files:
```bash
# Remove files older than 30 days
find test_outputs/ -name "*.md" -mtime +30 -delete
find test_outputs/ -name "temp_*" -mtime +7 -delete
```

Keep validation outputs and baseline comparison files for regression testing.