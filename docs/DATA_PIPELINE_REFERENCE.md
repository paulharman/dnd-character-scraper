# Data Pipeline Reference

End-to-end field mapping from the D&D Beyond API through the scraper, parser, discord notifier, YAML frontmatter, and Obsidian JSX components.

> **Version**: v6.5.0
> **Last updated**: 2026-02-17

---

## Pipeline Overview

```
D&D Beyond API (raw JSON)
    │
    ▼
Scraper Coordinators (8 coordinators)
    │
    ▼
CharacterCalculator (assembles + post-processes)
    │
    ├──► Parser Formatters (10 formatters → Markdown + YAML frontmatter)
    │        │
    │        ▼
    │    Obsidian Notes (.md files with YAML frontmatter)
    │        │
    │        ▼
    │    JSX Components (read frontmatter via DataCore)
    │
    └──► Discord Change Detection (50+ tracked fields → webhook notifications)
```

---

## Stage 1: Scraper Coordinators

Each coordinator extracts a domain of data from raw D&D Beyond API JSON. Execution is dependency-ordered via `CalculationPipeline`.

| Coordinator | Priority | Dependencies | Key Output Fields |
|---|---|---|---|
| `character_info` | 10 | none | name, level, classes, species, background, alignment, xp, proficiency_bonus, avatarUrl, senses |
| `abilities` | 20 | character_info | ability_scores, ability_modifiers, ability_score_breakdown, save_proficiencies |
| `proficiencies` | 25 | character_info, abilities | skill/save/tool/gaming_set/instrument/language/weapon proficiencies, skill_bonuses, passives |
| `combat` | 30 | character_info, abilities | initiative, speed, movement, armor_class, hit_points, attack_actions, spell_actions, saving_throws |
| `resources` | 35 | character_info, abilities | class_resources (slots, charges, uses), resources_by_class, resources_by_rest_type |
| `spellcasting` | 40 | character_info, abilities | spell_save_dc, spell_attack_bonus, spell_slots, pact_slots, caster_level, spell_counts |
| `features` | 50 | character_info | class_features, racial_traits, feats, background_features, limited_use_features |
| `equipment` | 60 | character_info, abilities | equipment lists, container_inventory, wealth, encumbrance, party_inventory, infusions |

### Coordinator Output Detail

#### character_info
```yaml
character_id: int
name: str
level: int
rule_version: "2014" | "2024"
classes: [{id, name, level, hit_die, subclass}]
species: {id, name, subrace}
background: {id, name, description}
alignment: str
experience_points: int
proficiency_bonus: int
avatarUrl: str | null
senses: {darkvision: 60, blindsight: 10, ...}
```

#### abilities
```yaml
ability_scores:
  strength: {score, modifier, save_bonus, source_breakdown}
  # ... 6 abilities
ability_modifiers: {strength: int, dexterity: int, ...}
ability_score_breakdown:
  strength: {total, base, racial, feat, asi, item, other, sources: [{value, source, source_type}]}
save_proficiencies: [ability_names]
```

#### proficiencies
```yaml
skill_proficiencies: [{name, ability, bonus, is_proficient, has_expertise}]
saving_throw_proficiencies: [ability_names]
tool_proficiencies: [str]
gaming_set_proficiencies: [str]
musical_instrument_proficiencies: [str]
language_proficiencies: [str]
weapon_proficiencies: [str]
skill_bonuses: {acrobatics: int, ...}  # 18 skills
passive_perception: int
passive_investigation: int
passive_insight: int
```

#### combat
```yaml
initiative_bonus: int
initiative_breakdown: str
speed: int
movement: {walking_speed, climbing_speed, swimming_speed, flying_speed}
armor_class: int | {total, base, breakdown}
hit_points: {maximum, current, temp, breakdown}
attack_actions: [{name, bonus, damage, type, ...}]
spell_actions: [{name, dc, attack_bonus, level, ...}]
special_abilities: [...]
saving_throws: {ability: bonus}
```

#### spellcasting
```yaml
is_spellcaster: bool
spellcasting_ability: str | null
spell_save_dc: int | null
spell_attack_bonus: int | null
spell_slots: [9 ints for levels 1-9]
pact_slots: int
pact_slot_level: int
caster_level: int
spell_counts: {cantrips, level_1..level_9, total}
```

#### features
```yaml
class_features: [{id, name, description, snippet, level_required, is_subclass_feature, source_name, limited_use, activation}]
racial_traits: [{id, name, description, trait_type}]
feats: [{id, name, description, prerequisites}]
background_features: [{id, name, description}]
features_by_level: {level: [features]}
limited_use_features: [...]
```

#### equipment
```yaml
basic_equipment: [{id, name, item_type, quantity, weight, equipped, total_weight}]
enhanced_equipment: [{...weapon/armor properties, is_magic, rarity, requires_attunement, attuned}]
container_inventory: {containers, container_organization, weight_breakdown}
wealth: {copper, silver, electrum, gold, platinum, total_gp}
encumbrance: {total_weight, carrying_capacity, encumbrance_level, speed_reduction}
party_inventory: {campaign_id, items, currency, sharing_state} | null
infusions: {active_infusions, known_infusions, slots_used, slots_total} | null
```

#### resources
```yaml
class_resources: [{name, class, maximum, current, used, remaining, recharge_on, level_based, ability_based}]
resources_by_class: {class_name: [resources]}
resources_by_rest_type: {short_rest | long_rest | none: [resources]}
depleted_resources: [names]
```

### Post-Processing (CharacterCalculator)

After all coordinators run, `CharacterCalculator` adds:
- `spells` - Enhanced spell data via `EnhancedSpellProcessor` (keyed by source class)
- `appearance` - {hair, eyes, skin, height, weight, age, gender, description}
- `traits` - {personalityTraits, ideals, bonds, flaws}
- `notes` - {backstory, allies, enemies, personalPossessions}
- Enhanced JSON breakdowns for combat/skills/resources

---

## Stage 2: Parser Formatters

10 formatters transform scraper output into Obsidian markdown notes.

| Formatter | File | Output |
|---|---|---|
| MetadataFormatter | `metadata.py` | YAML frontmatter block (all structured data) |
| CharacterInfoFormatter | `character_info.py` | Character infobox, quick links, stats table |
| AbilitiesFormatter | `abilities.py` | Ability scores table, saves, skills, passives |
| ProficiencyFormatter | `proficiency.py` | Weapon/armor/tool/gaming set/instrument/language sections |
| CombatFormatter | `combat.py` | Action economy, attacks, special abilities |
| SpellcastingFormatter | `spellcasting.py` | Spell stats, slots, spell lists by level |
| InventoryFormatter | `inventory.py` | Wealth, encumbrance, inventory component |
| FeaturesFormatter | `features.py` | Feats, class features by level, resources |
| RacialTraitsFormatter | `racial_traits.py` | Species traits, racial abilities |
| BackgroundFormatter | `background.py` | Appearance, background, backstory |

---

## Stage 3: YAML Frontmatter (MetadataFormatter)

The MetadataFormatter writes all structured data as YAML frontmatter. This is the **interface** between the Python pipeline and Obsidian JSX components.

### Complete Frontmatter Field List

#### Character Identity
| Frontmatter Field | Source Coordinator | Source Field |
|---|---|---|
| `character_name` | character_info | `name` |
| `character_id` | character_info | `character_id` |
| `level` | character_info | `level` |
| `class` | character_info | `classes[0].name` |
| `subclass` | character_info | `classes[0].subclass` |
| `hit_die` | character_info | `classes[0].hit_die` |
| `multiclass` | character_info | `len(classes) > 1` |
| `race` / `species` | character_info | `species.name` (field name depends on `rule_version`) |
| `background` | character_info | `background.name` |
| `is_2024_rules` | character_info | `rule_version == "2024"` |
| `avatar_url` | character_info | `avatarUrl` |
| `senses` | character_info | `senses` (nested object) |

#### Ability Scores
| Frontmatter Field | Source Coordinator | Source Field |
|---|---|---|
| `ability_scores` | abilities | `ability_scores.{ability}.score` (nested: str/dex/con/int/wis/cha) |
| `ability_modifiers` | abilities | `ability_scores.{ability}.modifier` (formatted +X/-X) |

#### Combat Stats
| Frontmatter Field | Source Coordinator | Source Field |
|---|---|---|
| `armor_class` | combat | `armor_class` |
| `current_hp` | combat | `hit_points.current` |
| `max_hp` | combat | `hit_points.maximum` |
| `temp_hp` | combat | `hit_points.temp` |
| `initiative` | combat | `initiative_bonus` (formatted +X/-X) |
| `speed` | combat | `speed` (formatted "X ft") |
| `movement` | combat | `movement` (nested: walking, climbing, swimming, flying) |
| `proficiency_bonus` | character_info | `proficiency_bonus` |

#### Skills & Proficiencies
| Frontmatter Field | Source Coordinator | Source Field |
|---|---|---|
| `skill_proficiencies` | proficiencies | `skill_proficiencies` (filtered: is_proficient) |
| `skill_expertise` | proficiencies | `skill_proficiencies` (filtered: has_expertise) |
| `skill_bonuses` | proficiencies | `skill_bonuses` (nested: 18 skills) |
| `stealth_disadvantage` | proficiencies / combat | armor stealth disadvantage flag |
| `saving_throw_proficiencies` | proficiencies | `saving_throw_proficiencies` |
| `saving_throw_bonuses` | abilities | `ability_scores.{ability}.save_bonus` (nested: 6 abilities) |
| `tool_proficiencies` | proficiencies | `tool_proficiencies` |
| `gaming_set_proficiencies` | proficiencies | `gaming_set_proficiencies` |
| `musical_instrument_proficiencies` | proficiencies | `musical_instrument_proficiencies` |
| `weapon_proficiencies` | proficiencies | `weapon_proficiencies` |
| `armor_proficiencies` | proficiencies | `armor_proficiencies` |
| `languages` | proficiencies | `language_proficiencies` |

#### Passive Scores
| Frontmatter Field | Source Coordinator | Source Field |
|---|---|---|
| `passive_perception` | proficiencies | `passive_perception` |
| `passive_investigation` | proficiencies | `passive_investigation` |
| `passive_insight` | proficiencies | `passive_insight` |

#### Spellcasting
| Frontmatter Field | Source Coordinator | Source Field |
|---|---|---|
| `spellcasting_ability` | spellcasting | `spellcasting_ability` |
| `spell_save_dc` | spellcasting | `spell_save_dc` |
| `spell_count` | spellcasting | `spell_counts.total` |
| `highest_spell_level` | spellcasting | max level with spells |
| `total_caster_level` | spellcasting | `caster_level` |
| `spells` | post-processing | Obsidian `[[links]]` to spell files |
| `spell_list` | post-processing | spell name strings |
| `spell_data` | post-processing | `[{name, level, school, components, casting_time, range, duration, concentration, ritual, prepared, source}]` |

#### Equipment & Wealth
| Frontmatter Field | Source Coordinator | Source Field |
|---|---|---|
| `inventory` | equipment | enhanced_equipment items (nested list) |
| `inventory_items` | equipment | count of items |
| `copper` | equipment | `wealth.copper` |
| `silver` | equipment | `wealth.silver` |
| `electrum` | equipment | `wealth.electrum` |
| `gold` | equipment | `wealth.gold` |
| `platinum` | equipment | `wealth.platinum` |
| `total_wealth_gp` | equipment | `wealth.total_gp` |
| `carrying_capacity` | equipment | `encumbrance.carrying_capacity` |
| `current_weight` | equipment | `encumbrance.total_weight` |
| `magic_items_count` | equipment | count of magic items |
| `attuned_items` | equipment | count of attuned items |
| `max_attunement` | equipment | max attunement slots |
| `party_inventory` | equipment | `party_inventory` (nested if present) |
| `infusions` | equipment | `infusions` (nested if present) |

#### Experience & Progression
| Frontmatter Field | Source Coordinator | Source Field |
|---|---|---|
| `experience` | character_info | `experience_points` |
| `next_level_xp` | calculated | XP threshold for next level |
| `xp_to_next_level` | calculated | `next_level_xp - experience` |
| `hit_dice_remaining` | combat | remaining hit dice |
| `inspiration` | combat | inspiration flag |
| `exhaustion_level` | combat | exhaustion level |

#### Metadata
| Frontmatter Field | Source | Notes |
|---|---|---|
| `processed_date` | generated | Timestamp of generation |
| `scraper_version` | generated | e.g. "6.0.0" |
| `template_version` | static | "1.0" |
| `auto_generated` | static | true |
| `manual_edits` | static | false |
| `is_active` | character state | active flag |
| `character_status` | character state | "alive", "dead", "retired" |
| `has_backstory` | post-processing | bool |
| `source_books` | character_info | list of source abbreviations |
| `homebrew_content` | character_info | bool |
| `official_content_only` | character_info | bool |
| `tags` | generated | [dnd, character-sheet, class-name, ...] |

---

## Stage 4: Discord Change Detection

The discord notifier compares old vs new character snapshots and fires webhook notifications for significant changes.

### Tracked Field Categories

| Category | Priority | Fields Tracked | Change Types |
|---|---|---|---|
| Ability Scores | HIGH | 6 ability scores | `ABILITY_SCORE_CHANGED` |
| Class/Level | HIGH | class levels, multiclass | `MULTICLASS_PROGRESSION` |
| Subclass | HIGH | subclass selections | `SUBCLASS_CHANGED` |
| Race/Species | HIGH | race/species | `RACE_SPECIES_CHANGED` |
| Background | HIGH | background | `BACKGROUND_CHANGED` |
| Feats | HIGH | feat list | `FEAT_ADDED`, `FEAT_REMOVED`, `FEAT_MODIFIED` |
| Hit Points | MEDIUM | max HP | `MAX_HP_CHANGED` |
| Spells | MEDIUM | known/prepared spells, slots | `SPELL_ADDED`, `SPELL_REMOVED`, `SPELL_MODIFIED` |
| Inventory | MEDIUM | items, equipment | `INVENTORY_ADDED`, `INVENTORY_REMOVED`, `INVENTORY_QUANTITY_CHANGED` |
| Spellcasting Stats | MEDIUM | spell attack, save DC | `SPELLCASTING_STATS_CHANGED` |
| Initiative | MEDIUM | initiative bonus | `INITIATIVE_CHANGED` |
| Alignment | MEDIUM | alignment | `ALIGNMENT_CHANGED` |
| Size | MEDIUM | size category | `SIZE_CHANGED` |
| Proficiencies | MEDIUM/LOW | skills, saves, tools, languages | `PROFICIENCY_ADDED`, `PROFICIENCY_REMOVED` |
| Passive Skills | LOW | perception, investigation, insight | `PASSIVE_SKILLS_CHANGED` |
| Movement | LOW | walk/fly/swim/climb speeds | `MOVEMENT_SPEED_CHANGED` |
| Personality | LOW | traits, ideals, bonds, flaws | `PERSONALITY_CHANGED` |

### Causation Analysis

The discord system detects cascading effects:
- Ability score change → triggers skill/save/spell/initiative re-evaluation
- Level change → triggers feature/spell slot/HP cascades
- Feat addition → triggers proficiency/ability/spell cascades

Confidence threshold: 0.7, max cascade depth: 3.

---

## Stage 5: JSX Components (Frontmatter Consumers)

Obsidian JSX components read frontmatter via DataCore's `getVal()`, `getNum()`, `getStr()` helpers.

### PartyStatsHub.jsx

Comprehensive party dashboard. Reads the most frontmatter fields of any component.

| Frontmatter Field | Access Method | Used For |
|---|---|---|
| `character_name` | getVal | Character identification |
| `avatar_url` | getStr | Character portrait |
| `class` | getStr | Class display |
| `subclass` | getStr | Subclass display |
| `level` | getNum | Level display |
| `species` | getStr | Species display |
| `max_hp` | getNum | HP bar |
| `current_hp` | getNum | HP bar |
| `temp_hp` | getNum | HP bar |
| `armor_class` | getNum | AC display |
| `initiative` | getStr | Initiative column |
| `speed` | getStr | Speed display |
| `movement` | getVal | Extra movement types (fly/swim/climb) |
| `proficiency_bonus` | getNum | Prof bonus display |
| `spell_save_dc` | getNum | Spell DC |
| `spell_count` | getNum | Spell count |
| `passive_perception` | getNum | Passives row |
| `passive_investigation` | getNum | Passives row |
| `passive_insight` | getNum | Passives row |
| `ability_scores` | getVal | Ability score grid (nested: 6 abilities) |
| `ability_modifiers` | getVal | Modifier display |
| `skill_proficiencies` | getVal | Skills tab (array) |
| `skill_expertise` | getVal | Skills tab (array) |
| `skill_bonuses` | getVal | Skills tab (nested: 18 skills) |
| `stealth_disadvantage` | getVal | Stealth indicator |
| `saving_throw_proficiencies` | getVal | Saves tab (array) |
| `saving_throw_bonuses` | getVal | Saves tab (nested: 6 abilities) |
| `tool_proficiencies` | getVal | Proficiencies section (array) |
| `senses` | getVal | Senses tags (nested: sense→distance) |

### SpellGenerator.jsx

Cross-character spell lookup.

| Frontmatter Field | Access Method | Used For |
|---|---|---|
| `spells` | getVal | Obsidian links to spell files |
| `spell_data` | getVal | Spell source attribution (`[{name, source}]`) |

Per-spell file frontmatter (in `z_Mechanics/CLI/spells/`):
- `name`, `classes`, `levelint`, `school`, `components`, `concentration`, `ritual`
- `casting_time`, `range`, `duration`, `verbal`, `somatic`, `material`, `material_desc`

### MonsterHub.jsx

Monster bestiary lookup.

| Frontmatter Field | Source | Used For |
|---|---|---|
| `name` | monster file | Monster name |
| `size` | monster file | Size filter |
| `type` | monster file | Type filter (with subtype) |
| `cr` | monster file | CR filter/sort |
| `ac` | monster file | AC display |
| `hp` | monster file | HP display |
| `immune` | monster file | Damage immunities |
| `resist` | monster file | Damage resistances |
| `vulnerable` | monster file | Damage vulnerabilities |
| `condition_immune` | monster file | Condition immunities |
| `environment` | monster file | Environment filter |
| `tags` | monster file | Tag-based filtering |

### Other Components

| Component | File | Key Frontmatter Fields |
|---|---|---|
| InventoryManager | `InventoryManager.jsx` | `character_name`, `inventory`, `wealth` |
| PartyInventoryManager | `PartyInventoryManager.jsx` | `character_name`, `party_inventory` |
| PartyLanguages | `PartyLanguages.jsx` | `character_name`, `species`/`race`, `background`, `languages` |
| InfusionsManager | `InfusionsManager.jsx` | `infusions` (active/known, slots) |
| SpellQuery | `SpellQuery.jsx` | `spell_data` (per-character spell list with prepared status) |
| SessionNotesSearch | `SessionNotesSearch.jsx` | `session_events`, `sessiondate` |
| SessionTracker | `sessiontracker.jsx` | `session_events` |

---

## Duplication Notes

### Proficiency Bonus (intentional)
- **Appears in output of**: character_info, abilities, proficiencies, combat coordinators
- **Canonical source**: character_info coordinator (computes from level)
- **Other coordinators**: read from context, include in output for calculation transparency
- **Frontmatter**: single `proficiency_bonus` field (from character_info)

### Saving Throw Proficiencies (intentional)
- **abilities coordinator**: needs save proficiency list to calculate `save_bonus` per ability
- **proficiencies coordinator**: tracks all proficiency types including saves
- Both read from the same raw modifier data. Each needs the data for its own calculations.
- **Frontmatter**: `saving_throw_proficiencies` (from proficiencies), `saving_throw_bonuses` (from abilities)

### Passive Scores (resolved)
- Previously had fallback calculation in metadata formatter. Dead code removed - proficiencies coordinator is the single source.
- **Frontmatter**: `passive_perception`, `passive_investigation`, `passive_insight`

---

## Data Flow Diagram (by field)

```
Raw API modifiers
  └─► character_info coordinator
        ├─► name ──────────► frontmatter: character_name ──► PartyStatsHub, PartyLanguages
        ├─► level ─────────► frontmatter: level ───────────► PartyStatsHub
        ├─► classes ───────► frontmatter: class, subclass ─► PartyStatsHub
        ├─► species ───────► frontmatter: species/race ────► PartyStatsHub, PartyLanguages
        ├─► senses ────────► frontmatter: senses ──────────► PartyStatsHub
        └─► avatarUrl ─────► frontmatter: avatar_url ──────► PartyStatsHub

  └─► abilities coordinator
        ├─► ability_scores ► frontmatter: ability_scores ──► PartyStatsHub
        ├─► modifiers ─────► frontmatter: ability_modifiers ► PartyStatsHub
        └─► save_bonus ────► frontmatter: saving_throw_bonuses ► PartyStatsHub

  └─► proficiencies coordinator
        ├─► skills ────────► frontmatter: skill_proficiencies ► PartyStatsHub
        ├─► skill_bonuses ─► frontmatter: skill_bonuses ──► PartyStatsHub
        ├─► tools ─────────► frontmatter: tool_proficiencies ► PartyStatsHub
        ├─► gaming_sets ───► frontmatter: gaming_set_proficiencies
        ├─► instruments ───► frontmatter: musical_instrument_proficiencies
        ├─► languages ─────► frontmatter: languages ───────► PartyLanguages
        └─► passives ──────► frontmatter: passive_* ───────► PartyStatsHub

  └─► combat coordinator
        ├─► armor_class ───► frontmatter: armor_class ─────► PartyStatsHub
        ├─► hit_points ────► frontmatter: max_hp, current_hp, temp_hp ► PartyStatsHub
        ├─► initiative ────► frontmatter: initiative ──────► PartyStatsHub
        ├─► speed ─────────► frontmatter: speed ───────────► PartyStatsHub
        └─► movement ──────► frontmatter: movement ────────► PartyStatsHub (fly/swim/climb)

  └─► spellcasting coordinator
        ├─► spell_save_dc ─► frontmatter: spell_save_dc ──► PartyStatsHub
        └─► spell_counts ──► frontmatter: spell_count ────► PartyStatsHub

  └─► equipment coordinator
        ├─► equipment ─────► frontmatter: inventory ───────► InventoryManager
        ├─► wealth ────────► frontmatter: copper..platinum ► InventoryManager
        ├─► party_inv ─────► frontmatter: party_inventory ─► PartyInventoryManager
        └─► infusions ─────► frontmatter: infusions ───────► InfusionsManager

  └─► post-processing (spells)
        ├─► spell links ───► frontmatter: spells ──────────► SpellGenerator
        └─► spell_data ────► frontmatter: spell_data ──────► SpellGenerator, SpellQuery
```
