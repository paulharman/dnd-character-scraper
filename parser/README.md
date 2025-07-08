# D&D Character Markdown Parser

Converts character JSON data from the scraper into beautifully formatted markdown character sheets.

## 🚀 Features

- **Rich Markdown Output**: Professional character sheets with proper formatting
- **YAML Frontmatter**: Metadata for integration with tools like Obsidian
- **Spell Integration**: Links to enhanced spell markdown files
- **Inventory Tables**: Organized equipment and container tracking
- **Action Economy**: Properly categorized actions, bonus actions, reactions
- **Rule Version Support**: Handles both 2014 and 2024 D&D rules
- **DnD UI Toolkit**: Optional integration with specialized markdown components

## 📋 Usage

### Basic Conversion
```bash
# Convert JSON to markdown
python parser/dnd_json_to_markdown.py character_12345.json

# With custom output file
python parser/dnd_json_to_markdown.py character_12345.json --output "My Character.md"

# Enable YAML frontmatter
python parser/dnd_json_to_markdown.py character_12345.json --yaml-frontmatter

# Use DnD UI Toolkit formatting
python parser/dnd_json_to_markdown.py character_12345.json --dnd-ui-toolkit
```

### Programmatic Usage
```python
from parser.dnd_json_to_markdown import CharacterMarkdownGenerator

# Initialize parser
generator = CharacterMarkdownGenerator(
    character_data,
    use_yaml_frontmatter=True,
    use_enhanced_spells=True,
    use_dnd_ui_toolkit=False
)

# Generate markdown
markdown_content = generator.generate_markdown()
```

## ⚙️ Output Formats

### Standard Markdown
Clean, readable character sheets compatible with any markdown viewer:
```markdown
# Elara Moonwhisper (Level 3)

## Basic Information
- **Race:** Elf (High Elf)
- **Class:** Wizard (3)
- **Background:** Sage
- **Alignment:** Chaotic Good

## Ability Scores
| Ability | Score | Modifier |
|---------|-------|----------|
| Strength | 10 | +0 |
| Dexterity | 14 | +2 |
...
```

### YAML Frontmatter
Rich metadata for tool integration:
```yaml
---
character_name: "Elara Moonwhisper"
level: 3
class: "Wizard"
race: "Elf"
ability_scores:
  strength: 10
  dexterity: 14
spells:
  - "[[fire-bolt]]"
  - "[[magic-missile]]"
inventory:
  - item: "Spellbook"
    type: "Equipment"
    equipped: true
---
```

### DnD UI Toolkit
Enhanced formatting with special components:
```markdown
> [!statblock|columns]
> # Elara Moonwhisper
> *Medium humanoid (elf), chaotic good*
> 
> **Armor Class** 12 (15 with *Mage Armor*)
> **Hit Points** 22 (3d6 + 9)
> **Speed** 30 ft.
```

## 🎨 Formatting Features

### ✅ **Character Information**
- Basic stats with proper formatting
- Ability scores in tables
- Class features and racial traits
- Background information and bonds

### ✅ **Combat Statistics**  
- Armor Class calculations
- Hit Points and Hit Dice
- Attack bonuses and damage
- Saving throws and skills

### ✅ **Spellcasting**
- Spell lists with proper organization
- Spell slot tracking
- Spell save DC and attack bonuses
- Ritual and concentration indicators

### ✅ **Inventory Management**
- Equipment organized by type
- Container-based organization
- Weight and encumbrance tracking
- Currency and wealth totals

### ✅ **Action Economy**
- Actions categorized properly
- Bonus actions and reactions
- Conditional abilities
- Resource usage tracking

## 🔧 Integration

### With Obsidian
```yaml
# Enables rich linking and graph features
use_yaml_frontmatter: true
use_enhanced_spells: true
spell_folder: "obsidian/spells/"
```

### With Character Sheets
```bash
# Generate multiple formats
python parser/dnd_json_to_markdown.py character.json --yaml-frontmatter --output "vault/characters/"
```

### With Discord Monitoring
The parser integrates with the Discord notification system to generate updated character sheets when changes are detected.

## 📊 Input Format

Expects JSON from the enhanced scraper:
```json
{
  "basic_info": {...},
  "ability_scores": {...},
  "spells": {...},
  "inventory": [...],
  "features": [...],
  "meta": {...}
}
```

## 🚨 Troubleshooting

**"File not found"**
- Verify JSON file path is correct
- Ensure scraper has run successfully
- Check file permissions

**"Malformed JSON"**  
- Validate JSON syntax
- Check for incomplete scraper output
- Verify character data integrity

**"Missing spell files"**
- Create `obsidian/spells/` directory manually
- Add your own spell markdown files (not included due to copyright)
- Update spell folder path in configuration if needed
- Spell files should be named like `fireball-xphb.md` for proper linking

For more help, see the main project documentation.