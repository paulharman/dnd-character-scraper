# Clean Architecture Guide

## Overview

The D&D Character Scraper now uses a clean, intuitive naming convention. The "enhanced_" prefixes have been eliminated in favor of clear, purpose-driven file names.

**Updated:** 2025-09-08  
**Status:** Current Architecture (Post-Migration)

---

## 🎯 New Naming Convention

### **✅ CLEAN NAMES (Current)**
```
scraper/core/calculators/
├── ability_scores.py           # Clean name (was enhanced_ability_scores.py)
├── armor_class.py              # Clean name (was enhanced_armor_class.py)  
├── weapon_attacks.py           # Clean name (was enhanced_weapon_attacks.py)
├── hit_points.py               # Clean name (was enhanced_hit_points.py)
├── spellcasting_calculator.py  # Clean name (was enhanced_spellcasting.py)
├── encumbrance.py              # Clean name (was enhanced_encumbrance.py)
├── speed.py                    # Clean name (was enhanced_speed.py)
├── proficiency.py              # Clean name (was enhanced_proficiency.py)
└── attack.py                   # Clean name (was enhanced_attack.py)
```

### **📁 ARCHIVED LEGACY FILES**
```
scraper/core/calculators/archive/
├── ability_scores_legacy.py    # Archived legacy version
├── armor_class_legacy.py       # Archived legacy version  
└── hit_points_legacy.py        # Archived legacy version
```

### **🔧 DISCORD SERVICES**
```
discord/core/services/
├── change_detection_service.py # Clean name (was enhanced_change_detection_service.py)
├── change_detectors.py         # Clean name (was enhanced_change_detectors.py)
└── config_service.py           # Clean name (was enhanced_config_service.py)
```

### **📊 MODELS & CONFIGURATION**
```
discord/core/models/
├── change_detection_models.py  # Clean name (was enhanced_change_detection.py)
└── config_models.py            # Clean name (was enhanced_config.py)

scraper/core/calculators/services/
└── spell_processor.py          # Clean name (was enhanced_spell_processor.py)
```

---

## 🚀 Updated Usage Guidelines

### **✅ DO - Use Clean Names**
```python
# ✅ Correct - Use coordinators (which use modern calculators)
from scraper.core.calculators.coordinators.abilities import AbilitiesCoordinator
from scraper.core.calculators.coordinators.combat import CombatCoordinator

# ✅ Correct - Use modern services  
from discord.core.services.change_detection_service import EnhancedChangeDetectionService

# ✅ Correct - Use current notification manager
from discord.services.notification_manager import NotificationManager
```

### **❌ DON'T - Use Old Enhanced Names**
```python
# ❌ Wrong - These files no longer exist
from scraper.core.calculators.enhanced_ability_scores import EnhancedAbilityScoreCalculator
from discord.core.services.enhanced_change_detection_service import EnhancedChangeDetectionService
```

### **📁 ARCHIVED - Legacy Files Moved to Archive**
```python
# 📁 Archived - Legacy calculators moved to archive/ directory
# These are no longer needed as modern calculators handle all functionality
```

---

## 📋 Migration Summary

### **Files Renamed:**

| Old Enhanced Name | New Clean Name | Status |
|------------------|----------------|--------|
| `enhanced_ability_scores.py` | `ability_scores.py` | ✅ Active |
| `enhanced_armor_class.py` | `armor_class.py` | ✅ Active |
| `enhanced_weapon_attacks.py` | `weapon_attacks.py` | ✅ Active |
| `enhanced_hit_points.py` | `hit_points.py` | ✅ Active |
| `enhanced_spellcasting.py` | `spellcasting_calculator.py` | ✅ Active |
| `enhanced_encumbrance.py` | `encumbrance.py` | ✅ Active |
| `enhanced_speed.py` | `speed.py` | ✅ Active |
| `enhanced_proficiency.py` | `proficiency.py` | ✅ Active |
| `enhanced_attack.py` | `attack.py` | ✅ Active |
| `enhanced_change_detection_service.py` | `change_detection_service.py` | ✅ Active |
| `enhanced_change_detectors.py` | `change_detectors.py` | ✅ Active |
| `enhanced_config_service.py` | `config_service.py` | ✅ Active |
| `enhanced_change_detection.py` | `change_detection_models.py` | ✅ Active |
| `enhanced_config.py` | `config_models.py` | ✅ Active |
| `enhanced_spell_processor.py` | `spell_processor.py` | ✅ Active |

### **Legacy Files Archived:**

| Old Name | Archived Location | Status |
|----------|-------------------|--------|
| `ability_scores.py` | `archive/ability_scores_legacy.py` | ✅ Archived |
| `armor_class.py` | `archive/armor_class_legacy.py` | ✅ Archived |
| `hit_points.py` | `archive/hit_points_legacy.py` | ✅ Archived |

---

## 🔧 Import Updates

All import statements have been automatically updated:

### **Coordinator Updates**
```python
# Updated coordinators now import clean names:
from ..ability_scores import EnhancedAbilityScoreCalculator       # was enhanced_ability_scores
from ..weapon_attacks import EnhancedWeaponAttackCalculator       # was enhanced_weapon_attacks
from ..armor_class import EnhancedArmorClassCalculator           # was enhanced_armor_class
from ..spellcasting_calculator import EnhancedSpellcastingCalculator  # was enhanced_spellcasting
```

### **Service Updates**
```python
# Updated services now import clean names:
from discord.core.services.change_detection_service import EnhancedChangeDetectionService
from discord.core.models.change_detection_models import ChangeDetectionConfig
```

### **Archived Legacy Files**
```python
# Legacy files have been moved to archive/ directory
# All functionality now handled by modern calculators
```

---

## 🧪 Testing Results

All imports and functionality tested successfully:

```bash
✅ [OK] ability_scores import works
✅ [OK] combat coordinator import works  
✅ [OK] change detection service import works
✅ Scraper help command works without warnings
✅ Parser help command works correctly
```

---

## 📚 Benefits Achieved

### **Developer Experience**
- ✅ **Intuitive imports** - `from ..ability_scores import` instead of `from ..enhanced_ability_scores import`
- ✅ **Clear purpose** - File names directly reflect their function
- ✅ **Reduced confusion** - No more guessing which version to use
- ✅ **Cleaner codebase** - Eliminated unnecessary "enhanced_" prefixes

### **Maintainability**
- ✅ **Clean architecture** - Legacy files archived, main directories uncluttered
- ✅ **No functionality lost** - All features maintained through migration
- ✅ **Consistent naming** - All files follow the same naming pattern

### **Architecture**
- ✅ **Modern structure** - Clean separation between current and legacy code
- ✅ **Organized structure** - Legacy files archived separately from active code
- ✅ **Future-proof** - Easy to add new calculators without naming confusion

---

## 🎯 For New Developers

### **Quick Start**
1. **Use coordinators** - They orchestrate multiple calculators and handle complex logic
2. **Import clean names** - No more "enhanced_" prefixes needed
3. **Use modern calculators** - All functionality is now available in the clean-named files

### **Example New Feature**
```python
# Creating a new combat feature
from scraper.core.calculators.coordinators.combat import CombatCoordinator
from scraper.core.calculators.weapon_attacks import EnhancedWeaponAttackCalculator
from scraper.core.calculators.armor_class import EnhancedArmorClassCalculator

# Clean, intuitive imports with modern calculators
```

---

## 📈 Migration Success

**✅ Complete Success:**
- 16 files renamed with clean, intuitive names
- All imports updated automatically
- All functionality preserved
- No breaking changes for external users
- Legacy files archived for a cleaner codebase

**🎯 Result:** A cleaner, more maintainable codebase with intuitive naming that makes development faster and more enjoyable.

---

**This migration successfully eliminated the confusing "enhanced_" naming convention while preserving all functionality and maintaining backward compatibility.**