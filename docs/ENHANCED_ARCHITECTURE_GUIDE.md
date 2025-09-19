# Clean Architecture Guide

## Overview

The D&D Character Scraper uses a clean, modern architecture with intuitive file names. Legacy files are preserved with `_legacy` suffixes where needed for backward compatibility.

**Generated:** 2025-09-08  
**Status:** Active Implementation Guide

---

## 🏗️ Architecture Principles

### **1. Clean, Modern Architecture**
- **Always use current versions** for new development
- Modern calculators provide comprehensive functionality
- Built with coordinator pattern and modern design principles

### **2. Legacy Compatibility**  
- Legacy versions with `_legacy` suffix serve as **internal dependencies**
- Maintain backward compatibility for complex systems
- Preserve proven functionality while enabling innovation

### **3. Clear Separation of Concerns**
- **Coordinators** orchestrate multiple calculators
- **Modern calculators** provide specialized functionality  
- **Legacy calculators** handle fundamental operations as building blocks

---

## 📁 File Structure Guide

### **SCRAPER MODULE - Enhanced Calculator Architecture**

```
scraper/core/calculators/
├── coordinators/           # 🎯 USE THESE - Main entry points
│   ├── abilities.py       # → imports enhanced_ability_scores  
│   ├── combat.py          # → imports enhanced_weapon_attacks, enhanced_armor_class, etc.
│   ├── spellcasting.py    # → imports enhanced_spellcasting
│   └── equipment.py       # → imports enhanced_encumbrance
├── enhanced_*.py          # 🎯 USE THESE - Primary calculators
│   ├── enhanced_ability_scores.py      ✅ Active
│   ├── enhanced_armor_class.py         ✅ Active  
│   ├── enhanced_weapon_attacks.py      ✅ Active
│   ├── enhanced_hit_points.py          ✅ Active
│   ├── enhanced_spellcasting.py        ✅ Active
│   ├── enhanced_encumbrance.py         ✅ Active
│   └── enhanced_*.py                   ✅ All Active
└── *.py                   # ⚠️ LEGACY - Internal dependencies only
    ├── ability_scores.py  # Used by enhanced_armor_class.py internally
    ├── armor_class.py     # Legacy features, larger implementation
    └── spellcasting.py    # Different purpose - this is parser formatter!
```

### **DISCORD MODULE - Mixed Architecture**

```
discord/
├── services/
│   └── notification_manager.py        # 🎯 USE THIS - Fully functional (1198 lines)
└── core/services/
    ├── enhanced_change_detection_service.py  # 🎯 USE THIS - Active
    ├── enhanced_change_detectors.py          # 🎯 USE THIS - Active
    └── enhanced_config_service.py            # 🎯 USE THIS - Active
```

---

## 🎯 Usage Guidelines

### **FOR DEVELOPERS**

#### **✅ DO - Use Enhanced Versions**
```python
# ✅ Correct - Use coordinators (which use enhanced calculators)
from scraper.core.calculators.coordinators.abilities import AbilitiesCoordinator
from scraper.core.calculators.coordinators.combat import CombatCoordinator

# ✅ Correct - Use enhanced services  
from discord.core.services.enhanced_change_detection_service import EnhancedChangeDetectionService

# ✅ Correct - Use current notification manager
from discord.services.notification_manager import NotificationManager
```

#### **❌ DON'T - Use Non-Enhanced Versions Directly**
```python
# ❌ Wrong - Don't import non-enhanced calculators directly
from scraper.core.calculators.ability_scores import AbilityScoreCalculator
from scraper.core.calculators.armor_class import ArmorClassCalculator

# ❌ Wrong - Don't use broken enhanced versions  
from discord.core.services.enhanced_notification_manager import EnhancedNotificationManager  # REMOVED
```

#### **⚠️ EXCEPTION - Parser Components**
```python
# ✅ Correct - This is the parser formatter, not the calculator
from parser.formatters.spellcasting import SpellcastingFormatter
```

---

## 🔧 Integration Patterns

### **Coordinator Pattern (Recommended)**
```python
# Use coordinators that orchestrate enhanced calculators
coordinator = AbilitiesCoordinator(rule_version="2024")
result = coordinator.calculate(character, raw_data)
```

### **Direct Enhanced Calculator (Advanced)**
```python
# Direct use of enhanced calculators for specialized needs
calculator = EnhancedAbilityScoreCalculator(rule_version="2024")
abilities = calculator.calculate(character_data)
```

### **Service Integration**
```python
# Enhanced services for change detection and notifications
change_detector = EnhancedChangeDetectionService(config)
notification_manager = NotificationManager(storage, config)
```

---

## 🧪 Testing Approach

### **Test Enhanced Versions**
- All tests should target **enhanced coordinators and calculators**
- Test backward compatibility through enhanced→legacy chains
- Verify import chains work correctly

### **Legacy Testing**
- Test non-enhanced versions only as **internal dependencies**
- Ensure they continue to work as building blocks for enhanced versions

---

## 📊 Current Status Summary

| Component | Enhanced Status | Recommendation |
|-----------|----------------|----------------|
| **Scraper Calculators** | ✅ **Fully Enhanced** | Use coordinators & enhanced calculators |
| **Discord Change Detection** | ✅ **Fully Enhanced** | Use enhanced services |
| **Discord Notifications** | ⚠️ **Mixed Success** | Use current notification_manager.py (not enhanced) |
| **Parser Components** | ⚠️ **Not Enhanced** | Use existing formatters (different purpose) |

---

## 🚀 Future Development

### **Guidelines for New Features**

1. **Create Enhanced Versions First**
   - Build on enhanced architecture patterns
   - Use coordinator pattern for complex operations
   - Leverage existing enhanced calculators

2. **Maintain Compatibility**
   - Don't break existing import chains
   - Preserve internal dependencies where needed
   - Test integration with legacy components

3. **Documentation**
   - Document enhanced vs non-enhanced decisions
   - Provide clear usage examples
   - Update architecture guides

---

## ⚠️ Common Pitfalls

### **Don't Remove Legacy Dependencies**
- `ability_scores.py` is used by `enhanced_armor_class.py`
- Removing it will break enhanced functionality
- Always check import chains before cleanup

### **Don't Confuse Parser vs Calculator**
- `parser/formatters/spellcasting.py` ≠ `scraper/core/calculators/enhanced_spellcasting.py`
- Different purposes, both needed

### **Don't Use Broken Enhanced Versions**
- `enhanced_notification_manager.py` was removed (broken imports)
- Current `notification_manager.py` is superior

---

## 📚 Related Documentation

- See `ENHANCED_VS_NONENHANCED_ANALYSIS.md` for complete file inventory
- See `CODE_REVIEW_FINDINGS.md` for security and quality analysis
- See individual module README files for specific guidance

---

**This guide ensures consistent use of the enhanced architecture while maintaining system stability and backward compatibility.**