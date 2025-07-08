# Spell Files Directory

This directory is intended for spell markdown files to enable rich spell linking in generated character sheets.

## 📜 Copyright Notice

**Spell files are NOT included in this repository** due to potential copyright restrictions. D&D spell descriptions may be protected content owned by Wizards of the Coast.

## 🔧 Setup Instructions

If you want enhanced spell linking in your character sheets:

1. **Create the spells directory:**
   ```bash
   mkdir -p obsidian/spells
   ```

2. **Add your own spell files:**
   - Create markdown files for spells you want to reference
   - Name them like: `fireball-xphb.md`, `magic-missile-xphb.md`, etc.
   - Follow the naming convention: `spell-name-source.md`

3. **Example spell file format:**
   ```markdown
   # Fireball
   
   *3rd-level evocation*
   
   **Casting Time:** 1 action  
   **Range:** 150 feet  
   **Components:** V, S, M (a tiny ball of bat guano and sulfur)  
   **Duration:** Instantaneous
   
   [Your spell description here - create your own or reference official sources you own]
   ```

## ⚖️ Legal Compliance

- Only include spell content you have rights to use
- Reference official D&D books you own
- Create original spell descriptions when possible
- Consider using SRD (System Reference Document) spells which are open content

## 🔗 Integration

Once spell files are added, the parser will automatically:
- Link spell names in character sheets to your spell files
- Create `[[spell-name]]` style links for Obsidian
- Generate rich spell references in markdown output

The parser will gracefully handle missing spell files by using plain text instead of links.