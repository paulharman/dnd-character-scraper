# Configuration Cleanup Plan & Task List

## Executive Summary

After thorough code verification (not assumptions), I've identified the actual usage status of every configuration item across all config files. This plan addresses truly unused items, inconsistent naming, and missing documentation.

## Verified Configuration Status

### ✅ FULLY USED Configuration Items
These are actively used in the codebase and should be kept:

#### config/main.yaml
- `project.name`, `project.version`, `project.description` - Used in config manager
- `environment` - Used for environment-specific overrides
- `debug` - Used in config schemas and calculator interfaces
- `paths.*` - All path configurations are used (character_data, spells_folder, etc.)
- `features.caching` / `performance.enable_caching` - Used extensively in calculators
- `performance.memory_optimization` - Defined in schemas (though implementation unclear)

#### config/discord.yaml
- `webhook_url`, `character_id`, `username` - Core Discord functionality
- `avatar_url` - Used (gets character avatar dynamically, config sets bot avatar)
- `timezone` - Used in Discord service initialization
- `min_priority`, `max_changes_per_notification` - Core filtering
- `changelog.*` - All changelog settings are used
- `causation.*` - All causation settings are used
- `detection.field_patterns` - Used for priority overrides

#### config/parser.yaml
- `defaults.enhance_spells` - Used in parser
- `defaults.use_dnd_ui_toolkit` - Used in parser
- `defaults.verbose` - Used in parser
- `templates.jsx_components_dir` - Used consistently in templates
- `templates.inventory_component`, `templates.spell_component` - Used in formatters
- `output.section_order` - Used in generator factory
- `spell_enhancement.enabled` - Used in parser
- `discord.enabled` - Used in parser workflow

#### config/scraper.yaml
- `api.base_url`, `api.timeout`, `api.max_retries` - Used in config manager
- `api.user_agent` - Defined in schemas
- `rate_limit.delay_between_requests` - Used in scraper
- `calculations.spell_save_dc_base` - Used in spellcasting calculator
- `output.include_raw_data` - Used in scraper with --keep-html flag
- `output.clean_html` - Used extensively throughout parser and scraper
- `output.verbose` - Used in parser and scraper

#### config/rules/constants.yaml
- `rule_versions.source_2024_ids` - Used for rule version detection
- `abilities.*` - Used in calculators
- `classes.hit_dice` - Used in HP calculations
- `proficiency_bonus` - Used extensively in change detection and calculators
- `skills.ability_mappings` - Used in skill calculations
- `alignments` - Used in character processing

### ❌ TRULY UNUSED Configuration Items
These have no implementation in the codebase:

#### config/main.yaml
- `performance.cleanup_temp_files` - Defined in schema but no implementation
- `logging.log_to_file` - Not implemented in main config (only in environments)
- `logging.log_file_path` - Not implemented in main config
- `logging.include_timestamps` - Defined in schema but no usage
- `logging.include_traceback` - Defined in schema but no usage
- `features.html_cleaning` - No direct usage found
- `features.rule_detection` - No direct usage found
- `features.enhanced_spells` - No direct usage found

#### config/discord.yaml
- `discord.show_change_summaries` - No implementation found
- `changelog.maintenance.generate_reports` - No implementation found
- `changelog.maintenance.report_retention_days` - No implementation found

### ⚠️ PARTIALLY IMPLEMENTED Configuration Items
These are used but have incomplete implementations:

#### config/discord.yaml
- `discord.color_code_by_priority` - Used in config validation but Discord formatter doesn't implement color coding
- `discord.group_related_changes` - Used in config models but grouping logic not fully implemented
- `changelog.enable_compression` - Used in config models, marked as future feature

### 🔄 DUPLICATE Configuration Items
These represent the same functionality with different names:

#### config/main.yaml
- `features.caching` vs `performance.enable_caching` - Both control the same caching functionality

## Task List

### Phase 1: Remove Truly Unused Items (High Priority)

#### Task 1.1: Clean up config/main.yaml
- [ ] Remove `performance.cleanup_temp_files` (no implementation)
- [ ] Remove `logging.log_to_file` from main config (only used in environments)
- [ ] Remove `logging.log_file_path` from main config
- [ ] Remove `logging.include_timestamps` (defined but unused)
- [ ] Remove `logging.include_traceback` (defined but unused)
- [ ] Remove `features.html_cleaning` (no direct usage)
- [ ] Remove `features.rule_detection` (no direct usage)
- [ ] Remove `features.enhanced_spells` (no direct usage)

#### Task 1.2: Clean up config/discord.yaml
- [ ] Remove `discord.show_change_summaries` (no implementation)
- [ ] Remove `changelog.maintenance.generate_reports` (no implementation)
- [ ] Remove `changelog.maintenance.report_retention_days` (no implementation)

#### Task 1.3: Update configuration schemas
- [ ] Remove unused fields from `src/config/schemas.py`
- [ ] Update validation logic to remove checks for deleted fields
- [ ] Update example configurations to remove unused items

### Phase 2: Resolve Duplicates (High Priority)

#### Task 2.1: Consolidate caching configuration
- [ ] Choose single naming convention: `performance.enable_caching`
- [ ] Remove `features.caching` from main.yaml
- [ ] Update all calculator code to use consistent config path
- [ ] Update config loading logic in managers

#### Task 2.2: Verify no other duplicates exist
- [ ] Search codebase for other duplicate configuration patterns
- [ ] Document any intentional duplicates with clear comments

### Phase 3: Standardize Naming Conventions (Medium Priority)

#### Task 3.1: Establish naming standards
- [ ] Document naming conventions:
  - Use `snake_case` for all configuration keys
  - Use `enable_*` prefix for boolean feature flags
  - Use `*_seconds`, `*_minutes`, `*_hours`, `*_days` suffixes for time values
  - Use `*_directory` suffix for directory paths
  - Use `maximum_*` and `minimum_*` prefixes for limits

#### Task 3.2: Apply naming standards (breaking changes)
- [ ] Rename inconsistent keys across all config files
- [ ] Update all code references to use new names
- [ ] Create migration script for existing configurations
- [ ] Update documentation and examples

### Phase 4: Complete Partial Implementations (Medium Priority)

#### Task 4.1: Implement color coding by priority
- [ ] Add color coding logic to Discord formatter
- [ ] Map priority levels to Discord embed colors
- [ ] Test color coding functionality

#### Task 4.2: Implement change grouping
- [ ] Complete grouping logic in Discord formatter
- [ ] Add configuration options for grouping behavior
- [ ] Test change grouping functionality

#### Task 4.3: Plan compression feature
- [ ] Design compression implementation for change logs
- [ ] Update configuration to reflect implementation status
- [ ] Document future implementation plans

### Phase 5: Add Comprehensive Documentation (Medium Priority)

#### Task 5.1: Document all configuration files
- [ ] Add comprehensive comments to each config file
- [ ] Explain purpose and impact of each setting
- [ ] Provide examples for complex configurations
- [ ] Document valid values and ranges

#### Task 5.2: Create configuration guide
- [ ] Write user-friendly configuration guide
- [ ] Include common configuration scenarios
- [ ] Document environment-specific overrides
- [ ] Provide troubleshooting section

#### Task 5.3: Add inline validation help
- [ ] Add descriptive error messages for invalid configurations
- [ ] Include suggestions for fixing common configuration errors
- [ ] Add warnings for deprecated or unused settings

### Phase 6: Implement Configuration Validation (Low Priority)

#### Task 6.1: Create comprehensive validation
- [ ] Validate all configuration files on startup
- [ ] Check for required fields and valid values
- [ ] Warn about unused or deprecated settings
- [ ] Provide helpful error messages

#### Task 6.2: Add configuration testing
- [ ] Create tests for configuration loading
- [ ] Test environment-specific overrides
- [ ] Test configuration validation logic
- [ ] Test migration scenarios

### Phase 7: Create Migration Tools (Low Priority)

#### Task 7.1: Configuration migration script
- [ ] Create script to migrate old configurations to new format
- [ ] Handle renamed fields and removed settings
- [ ] Backup original configurations
- [ ] Validate migrated configurations

#### Task 7.2: Version configuration files
- [ ] Add version field to configuration files
- [ ] Implement version-aware loading
- [ ] Create upgrade path for future changes

## Implementation Priority

### Immediate (Week 1)
- Phase 1: Remove truly unused items
- Phase 2: Resolve duplicates

### Short-term (Week 2-3)
- Phase 3: Standardize naming conventions
- Phase 5: Add comprehensive documentation

### Medium-term (Month 1-2)
- Phase 4: Complete partial implementations
- Phase 6: Implement configuration validation

### Long-term (Month 2+)
- Phase 7: Create migration tools

## Risk Assessment

### High Risk Changes
- Removing configuration items (could break existing deployments)
- Renaming configuration keys (breaking changes)

### Medium Risk Changes
- Consolidating duplicate configurations
- Implementing partial features

### Low Risk Changes
- Adding documentation
- Adding validation
- Creating migration tools

## Success Criteria

1. **Cleanliness**: No unused configuration items remain
2. **Consistency**: All naming follows established conventions
3. **Completeness**: All documented features are implemented
4. **Clarity**: All configuration options are well-documented
5. **Reliability**: Configuration validation prevents errors
6. **Maintainability**: Clear upgrade path for future changes

## Testing Strategy

1. **Before Changes**: Document current configuration behavior
2. **During Changes**: Test each phase incrementally
3. **After Changes**: Verify all functionality still works
4. **Regression Testing**: Ensure no features are broken
5. **User Testing**: Validate documentation and examples

This plan ensures systematic cleanup while minimizing risk to existing deployments.