# Project Instructions for Claude

## Overview

Personal D&D Beyond character scraper project with three modules:

- **Scraper** (`scraper/`) - Scrapes D&D Beyond, retrieves character values and performs calculations. Outputs standard JSON that could be imported into any application.
- **Parser** (`parser/`) - Takes the scraped JSON and outputs a `.md` file compatible with Obsidian. Uses the [DnD UI Toolkit](https://github.com/hay-kot/obsidian-dnd-ui-toolkit) and adds YAML frontmatter for [Datacore](https://github.com/blacksmithgu/datacore).
- **Discord Notifier** (`discord/`) - Monitors for character changes and sends notifications to Discord.

The usual entry point is through the **parser** - it calls the scraper, parses the output into `.md`, then calls the discord module for change monitoring.

This project will be shared openly on GitHub.

## Important Rules

- **Never commit personal information**: No API keys, character IDs, webhook URLs, cobalt tokens, or any user-specific data. Check for `.env` files, credentials, and hardcoded IDs before committing.
- **Character-independent code only**: No hardcoded values for specific character IDs. All logic must work generically for any D&D Beyond character.
- **Don't make assumptions**: If you're unsure about how something works, read the code first. Don't guess at data structures - trace them through the pipeline. Ask if unclear.
- **Personal project, not enterprise**: Keep solutions practical and straightforward. Avoid over-engineering.

## Key Documentation

Read these before making structural changes:

- **`docs/DATA_PIPELINE_REFERENCE.md`** - End-to-end field mapping: Raw API -> Scraper Coordinators -> Parser Formatters -> YAML Frontmatter -> JSX Components. Shows where every field comes from and goes to.
- **`docs/CLEAN_ARCHITECTURE_GUIDE.md`** - Architecture overview, file structure, and usage patterns.

## Documentation Rules

- **When adding new data fields**: Trace the field through the full pipeline (coordinator -> metadata formatter -> frontmatter -> JSX component) and update `DATA_PIPELINE_REFERENCE.md` with the new mapping.
- **When modifying coordinators or formatters**: Check `DATA_PIPELINE_REFERENCE.md` to understand what downstream consumers depend on the data you're changing.
- **When modifying JSX components**: Check what frontmatter fields they read and ensure those fields are being written by the metadata formatter.
- **When deleting or renaming files**: Update `CLEAN_ARCHITECTURE_GUIDE.md` file structure and check for stale imports across the codebase.
- **At the end of any session with structural changes**: Confirm docs are up to date. Update version numbers in docs if a release is tagged.

## Architecture Quick Reference

### Data Pipeline
```
D&D Beyond API -> Scraper Coordinators (8) -> CharacterCalculator -> Parser Formatters (10) -> Obsidian Markdown
                                                                  -> Discord Change Detection
```

### Coordinator execution order (by dependency)
1. character_info (no deps)
2. abilities (needs character_info)
3. proficiencies (needs character_info, abilities)
4. combat (needs character_info, abilities)
5. resources (needs character_info, abilities)
6. spellcasting (needs character_info, abilities)
7. features (needs character_info)
8. equipment (needs character_info, abilities)

### Key directories
- `scraper/core/calculators/coordinators/` - Entry points, always import via coordinators
- `parser/formatters/metadata.py` - YAML frontmatter generation (interface between Python and JSX)
- `obsidian/*.jsx` - Obsidian DataCore components reading frontmatter
- `discord/core/services/` - Change detection and notifications
- `config/constants.yaml` - D&D constants (class hit dice, proficiency categorization sets)

### Adding a new data field checklist
1. Extract from raw API in the appropriate coordinator
2. Include in coordinator's `result_data` dict
3. If coordinator passes through another coordinator, update that coordinator too
4. Add to `parser/formatters/metadata.py` frontmatter output
5. Read in the relevant JSX component via `getVal()`/`getNum()`/`getStr()`
6. If discord should track it, add to change detection models
7. Update `docs/DATA_PIPELINE_REFERENCE.md`

## Style Notes

- Coordinators use the `ICoordinator` interface with `coordinate()`, `can_coordinate()`, `validate_input()`
- Proficiency categorization uses constant sets in calculators (e.g. `MUSICAL_INSTRUMENTS`, `GAMING_SETS`)
- Frontmatter is the **interface** between Python and JSX - changes must be coordinated across both
- JSX components use DataCore helpers: `getVal()`, `getNum()`, `getStr()`, `dc.useArray()`, `dc.useQuery()`
