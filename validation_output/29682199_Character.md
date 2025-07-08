---
avatar_url: "https://www.dndbeyond.com/avatars/10846/680/1581111423-29682199.jpeg?width=150&height=150&fit=crop&quality=95&auto=webp"
character_name: "Redgrave"
level: 10
proficiency_bonus: 4
experience: 34000
class: "Cleric"
subclass: "Forge Domain"
hit_die: "d8"
is_2024_rules: False
race: "Warforged (UA)"
background: "Guild Artisan / Guild Merchant"
ability_scores:
  strength: 16
  dexterity: 8
  constitution: 14
  intelligence: 10
  wisdom: 20
  charisma: 10
ability_modifiers:
  strength: +3
  dexterity: -1
  constitution: +2
  intelligence: +0
  wisdom: +5
  charisma: +0
armor_class: 24
current_hp: 73
max_hp: 73
initiative: "-1"
spellcasting_ability: "wisdom"
spell_save_dc: 17
character_id: "29682199"
processed_date: "2025-07-02 17:20:22"
scraper_version: "6.0.0"
speed: "30 ft"
spell_count: 18
highest_spell_level: 5
spells:
  - "[[mending-xphb]]"
  - "[[sacred-flame-xphb]]"
  - "[[thaumaturgy-xphb]]"
  - "[[word-of-radiance-xphb]]"
  - "[[command-xphb]]"
  - "[[cure-wounds-xphb]]"
  - "[[healing-word-xphb]]"
  - "[[locate-object-xphb]]"
  - "[[silence-xphb]]"
  - "[[spiritual-weapon-xphb]]"
  - "[[dispel-magic-xphb]]"
  - "[[mass-healing-word-xphb]]"
  - "[[remove-curse-xphb]]"
  - "[[revivify-xphb]]"
  - "[[spirit-guardians-xphb]]"
  - "[[control-water-xphb]]"
  - "[[guardian-of-faith-xphb]]"
  - "[[mass-cure-wounds-xphb]]"
spell_list: ['Mending', 'Sacred Flame', 'Thaumaturgy', 'Word of Radiance', 'Command', 'Cure Wounds', 'Healing Word', 'Locate Object', 'Silence', 'Spiritual Weapon', 'Dispel Magic', 'Mass Healing Word', 'Remove Curse', 'Revivify', 'Spirit Guardians', 'Control Water', 'Guardian of Faith', 'Mass Cure Wounds']
inventory_items: 22
passive_perception: 15
passive_investigation: 10
passive_insight: 15
copper: 0
silver: 33
electrum: 0
gold: 21
platinum: 0
total_wealth_gp: 24
carrying_capacity: 240
current_weight: 152
magic_items_count: 22
attuned_items: 0
max_attunement: 3
next_level_xp: 85000
xp_to_next_level: 51000
multiclass: False
total_caster_level: 10
hit_dice_remaining: 10
inspiration: false
exhaustion_level: 0
has_backstory: true
is_active: true
character_status: "alive"
source_books: ['PHB']
homebrew_content: false
official_content_only: true
template_version: "1.0"
auto_generated: true
manual_edits: false
tags: ['dnd', 'character-sheet', 'cleric', 'cleric-forge-domain', 'guild-artisan---guild-merchant', 'warforged-(ua)', 'mid-level', 'spellcaster']
---

```run-python
import os, sys, subprocess
os.chdir(r'C:\Users\alc_u\Documents\DnD\CharacterScraper')
vault_path = @vault_path
note_path = @note_path
full_path = os.path.join(vault_path, note_path)
cmd = ['python', 'dnd_json_to_markdown.py', '29682199', full_path, '--scraper-path', 'enhanced_dnd_scraper.py']
result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', shell=True)
print('\n\n')
print('SUCCESS: Character refreshed!' if result.returncode == 0 else f'ERROR: {result.stderr}')
print('Reload file to see changes.' if result.returncode == 0 else '')
```


---

> [!infobox]+ ^character-info
> # Redgrave
> ![Character Avatar|200](https://www.dndbeyond.com/avatars/10846/680/1581111423-29682199.jpeg?width=150&height=150&fit=crop&quality=95&auto=webp)
> ###### Character Details
> |  |  |
> | --- | --- |
> | **Class** | Cleric |
> | **Subclass** | Forge Domain |
> | **Race** | Warforged (UA) |
> | **Background** | Guild Artisan / Guild Merchant |
> | **Level** | 10 |
> | **Hit Points** | 73/73 |
> | **HP Calc** | Manual |
> | **Armor Class** | 24 |
> | **Proficiency** | +4 |
> 
> ###### Ability Scores
> |  |  |  |
> | --- | --- | --- |
> | **Str** 16 (+3) | **Dex** 8 (-1) | **Con** 14 (+2) |
> | **Int** 10 (+0) | **Wis** 20 (+5) | **Cha** 10 (+0) |

## Quick Links

| Section |
| --- |
| [[#Character Statistics]] |
| [[#Abilities & Skills]] |
| [[#Appearance]] |
| [[#Spellcasting]] |
| [[#Features]] |
| [[#Racial Traits]] |
| [[#Attacks]] |
| [[#Proficiencies]] |
| [[#Background]] |
| [[#Backstory]] |
| [[#Inventory]] |
| &nbsp; |
| [D&D Beyond](https://www.dndbeyond.com/characters/29682199) |

---

## Character Statistics

```stats
items:
  - label: Level
    value: '10'
  - label: Class
    value: 'Cleric'
  - label: Subclass
    value: 'Forge Domain'
  - label: Initiative
    value: '-1'
  - label: Speed
    value: '30 ft'
  - label: Armor Class
    sublabel: Unarmored (10 + Dex)
    value: 24

grid:
  columns: 3
```

<BR>

```healthpoints
state_key: redgrave_health
health: 73
hitdice:
  dice: d8
  value: 10
```

^character-statistics

---

## Abilities & Skills

```ability
abilities:
  strength: {'score': 16, 'modifier': 3, 'save_bonus': 3, 'source_breakdown': {'base': 15, 'asi': 1}}
  dexterity: {'score': 8, 'modifier': -1, 'save_bonus': -1, 'source_breakdown': {'base': 8}}
  constitution: {'score': 14, 'modifier': 2, 'save_bonus': 2, 'source_breakdown': {'base': 13, 'race': 1}}
  intelligence: {'score': 10, 'modifier': 0, 'save_bonus': 0, 'source_breakdown': {'base': 10}}
  wisdom: {'score': 20, 'modifier': 5, 'save_bonus': 9, 'source_breakdown': {'base': 15, 'race': 2, 'asi': 3}}
  charisma: {'score': 10, 'modifier': 0, 'save_bonus': 4, 'source_breakdown': {'base': 10}}

proficiencies:
  - charisma
  - wisdom
```

<BR>

```badges
items:
  - label: Passive Perception
    value: 19
  - label: Passive Investigation
    value: 10
  - label: Passive Insight
    value: 19
```

<BR>

```skills
proficiencies:
  - athletics
  - insight
  - perception
  - persuasion
  - religion


```

### Proficiency Sources
> **Skill Bonuses:**
> - **Athletics** (Background: Guild Artisan / Guild Merchant)
> - **Insight** (Class: Cleric)
> - **Perception** (Species: Warforged Envoy)
> - **Persuasion** (Background: Guild Artisan / Guild Merchant)
> - **Religion** (Class: Cleric)
>
> **Saving Throw Bonuses:**
> - **Charisma** +4 (Class: Cleric)
> - **Wisdom** +9 (Class: Cleric)
>
> ^proficiency-sources

^abilities-skills

---

## Appearance

<span class="right-link">[[#Character Statistics|Top]]</span>
> **Gender:** 
> **Age:** 
> **Height:** 6'5"
> **Weight:** 300
> **Hair:** 
> **Eyes:** Emeralds
> **Skin:** Metallic with gold engraving
> **Size:** Medium
>
> ^appearance

---

## Spellcasting

<span class="right-link">[[#Character Statistics|Top]]</span>
> ```stats
> items:
>   - label: Spell Save DC
>     value: 17
>   - label: Spell Attack Bonus
>     value: '+9'
>   - label: Spellcasting Ability
>     value: 'Wisdom'
>   - label: Spellcasting Modifier
>     value: '+5'
>
> grid:
>   columns: 4
> ```
>
> ^spellstats

### Spell Slots
> ```consumable
> items:
>   - label: 'Level 1'
>     state_key: redgrave_spells_1
>     uses: 4
>   - label: 'Level 2'
>     state_key: redgrave_spells_2
>     uses: 3
>   - label: 'Level 3'
>     state_key: redgrave_spells_3
>     uses: 3
>   - label: 'Level 4'
>     state_key: redgrave_spells_4
>     uses: 3
>   - label: 'Level 5'
>     state_key: redgrave_spells_5
>     uses: 2
> ```
>
> ^spellslots

### Spell List
> | Level | Spell | School | Components | Casting Time | Concentration | Source |
> |-------|-------|--------|------------|--------------|---------------|--------|
> | Cantrip | [[#Mending]] | Transmutation | V, S, M (two lodestones) | 1 Minute |  | Cleric |
> | Cantrip | [[#Sacred Flame]] | Evocation | V, S | 1 Action |  | Cleric |
> | Cantrip | [[#Thaumaturgy]] | Transmutation | V | 1 Action |  | Cleric |
> | Cantrip | [[#Word of Radiance]] | Evocation | V, M (a sunburst token) | 1 Action |  | Cleric |
> | 1 | [[#Command]] | Enchantment | V | 1 Action |  | Cleric |
> | 1 | [[#Cure Wounds]] | Abjuration | V, S | 1 Action |  | Cleric |
> | 1 | [[#Healing Word]] | Abjuration | V | 1 Reaction |  | Cleric |
> | 2 | [[#Locate Object]] | Divination | V, S, M (a forked twig) | 1 Action | Yes | Cleric |
> | 2 | [[#Silence]] | Illusion | V, S | 1 Action | Yes | Cleric |
> | 2 | [[#Spiritual Weapon]] | Evocation | V, S | 1 Reaction | Yes | Cleric |
> | 3 | [[#Dispel Magic]] | Abjuration | V, S | 1 Action |  | Cleric |
> | 3 | [[#Mass Healing Word]] | Abjuration | V | 1 Reaction |  | Cleric |
> | 3 | [[#Remove Curse]] | Abjuration | V, S | 1 Action |  | Cleric |
> | 3 | [[#Revivify]] | Necromancy | V, S, M (a diamond worth 300+ GP, which the spell consumes) | 1 Action |  | Cleric |
> | 3 | [[#Spirit Guardians]] | Conjuration | V, S, M (a prayer scroll) | 1 Action | Yes | Cleric |
> | 4 | [[#Control Water]] | Transmutation | V, S, M (a mixture of water and dust) | 1 Action | Yes | Cleric |
> | 4 | [[#Guardian of Faith]] | Conjuration | V | 1 Action |  | Cleric |
> | 5 | [[#Mass Cure Wounds]] | Abjuration | V, S | 1 Action |  | Cleric |
>
> ^spelltable

### Spell Details
#### Mending
>
> ```badges
> items:
>   - label: Cantrip
>   - label: Transmutation
> ```
>
> ```spell-components
> casting_time: 1 No Action
> range: 0 feet
> components: V, S, M (two lodestones)
> duration: Varies
> ```
>
> This spell repairs a single break or tear in an object you touch, such as a broken chain link, two halves of a broken key, a torn cloak, or a leaking wineskin. As long as the break or tear is no larger than 1 foot in any dimension, you mend it, leaving no trace of the former damage. This spell can physically repair a magic item, but it can’t restore magic to such an object.
>

<BR>

#### Sacred Flame
>
> ```badges
> items:
>   - label: Cantrip
>   - label: Evocation
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S
> duration: Varies
> ```
>
> **Classes**: [Warlock (Celestial Patron)](/z_Mechanics/CLI/lists/list-spells-classes-warlock-xphb-celestial-patron-xphb.md "subclass=XPHB;class=XPHB"); [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB") *Source: Player's Handbook (2024) p. 313. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Thaumaturgy
>
> ```badges
> items:
>   - label: Cantrip
>   - label: Transmutation
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V
> duration: 1 minute
> ```
>
> You manifest a minor wonder within range. You create one of the effects below within range. If you cast this spell multiple times, you can have up to three of its 1-minute effects active at a time. Altered Eyes. You alter the appearance of your eyes for 1 minute. Booming Voice. Your voice booms up to three times as loud as normal for 1 minute. For the duration, you have Advantage on Charisma (Intimidation) checks. Fire Play. You cause flames to flicker, brighten, dim, or change color for 1 minute. Invisible Hand. You instantaneously cause an unlocked door or window to fly open or slam shut. Phantom Sound. You create an instantaneous sound that originates from a point of your choice within range, such as a rumble of thunder, the cry of a raven, or ominous whispers. Tremors. You cause harmless tremors in the ground for 1 minute.
>

<BR>

#### Word of Radiance
>
> ```badges
> items:
>   - label: Cantrip
>   - label: Evocation
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, M (a sunburst token)
> duration: Varies
> ```
>
> **Classes**: [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB") *Source: Player's Handbook (2024) p. 343*
>

<BR>

#### Command
>
> ```badges
> items:
>   - label: Level 1
>   - label: Enchantment
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V
> duration: Varies
> ```
>
> - **Casting time:** 1 Action - **Range:** 60 feet - **Components:** V - **Duration:** Instantaneous You speak a one-word command to a creature you can see within range. The target must succeed on a Wisdom saving throw or follow the command on its next turn. Choose the command from these options: - **Approach.** The target moves toward you by the shortest and most direct route, ending its turn if it moves within 5 feet of you.   - **Drop.** The target drops whatever it is holding and then ends its turn.   - **Flee.** The target spends its turn moving away from you by the fastest available means.   - **Grovel.** The target has the [Prone](/z_Mechanics/CLI/conditions.md#Prone) condition and then ends its turn.   - **Halt.** On its turn, the target doesn't move and takes no action or [Bonus Action](/z_Mechanics/CLI/variant-rules/bonus-action-xphb.md).   **Classes**: [Sorcerer (Draconic Sorcery)](/z_Mechanics/CLI/lists/list-spells-classes-sorcerer-xphb-draconic-sorcery-xphb.md "subclass=XPHB;class=XPHB"); [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Warlock (Fiend Patron)](/z_Mechanics/CLI/lists/list-spells-classes-warlock-xphb-fiend-patron-xphb.md "subclass=XPHB;class=XPHB"); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md); [Paladin](/z_Mechanics/CLI/lists/list-spells-classes-paladin.md); [Bard (College of Glamour)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-glamour-xphb.md "subclass=XPHB;class=XPHB") *Source: Player's Handbook (2024) p. 251. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Cure Wounds
>
> ```badges
> items:
>   - label: Level 1
>   - label: Abjuration
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S
> duration: Varies
> ```
>
> - **Casting time:** 1 Action - **Range:** Touch - **Components:** V, S - **Duration:** Instantaneous A creature you touch regains a number of [Hit Points](/z_Mechanics/CLI/variant-rules/hit-points-xphb.md) equal to `2d8` plus your spellcasting ability modifier. **Classes**: [Warlock (Celestial Patron)](/z_Mechanics/CLI/lists/list-spells-classes-warlock-xphb-celestial-patron-xphb.md "subclass=XPHB;class=XPHB"); [Cleric (Life Domain)](/z_Mechanics/CLI/lists/list-spells-classes-cleric-xphb-life-domain-xphb.md "subclass=XPHB;class=XPHB"); [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Druid](/z_Mechanics/CLI/lists/list-spells-classes-druid.md); [Ranger](/z_Mechanics/CLI/lists/list-spells-classes-ranger.md); [Druid (Circle of the Moon)](/z_Mechanics/CLI/lists/list-spells-classes-druid-xphb-circle-of-the-moon-xphb.md "subclass=XPHB;class=XPHB"); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md); [Paladin](/z_Mechanics/CLI/lists/list-spells-classes-paladin.md) *Source: Player's Handbook (2024) p. 259. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Healing Word
>
> ```badges
> items:
>   - label: Level 1
>   - label: Abjuration
> ```
>
> ```spell-components
> casting_time: 1 Reaction
> range: 0 feet
> components: V
> duration: Varies
> ```
>
> - **Casting time:** 1 Bonus Action - **Range:** 60 feet - **Components:** V - **Duration:** Instantaneous A creature of your choice that you can see within range regains [Hit Points](/z_Mechanics/CLI/variant-rules/hit-points-xphb.md) equal to `2d4` plus your spellcasting ability modifier. **Classes**: [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Druid](/z_Mechanics/CLI/lists/list-spells-classes-druid.md); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md) *Source: Player's Handbook (2024) p. 284. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Locate Object
>
> ```badges
> items:
>   - label: Level 2
>   - label: Divination
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S, M (a forked twig)
> duration: Concentration, up to 1 minute
> ```
>
> - **Casting time:** 1 Action - **Range:** Self - **Components:** V, S, M (a forked twig) - **Duration:** Concentration, up to 10 minutes Describe or name an object that is familiar to you. You sense the direction to the object's location if that object is within 1,000 feet of you. If the object is in motion, you know the direction of its movement. The spell can locate a specific object known to you if you have seen it up close—within 30 feet—at least once. Alternatively, the spell can locate the nearest object of a particular kind, such as a certain kind of apparel, jewelry, furniture, tool, or weapon. This spell can't locate an object if any thickness of lead blocks a direct path between you and the object. **Classes**: [Rogue (Arcane Trickster)](/z_Mechanics/CLI/lists/list-spells-classes-rogue-xphb-arcane-trickster-xphb.md "subclass=XPHB;class=XPHB"); [Wizard](/z_Mechanics/CLI/lists/list-spells-classes-wizard.md); [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Druid](/z_Mechanics/CLI/lists/list-spells-classes-druid.md); [Ranger](/z_Mechanics/CLI/lists/list-spells-classes-ranger.md); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md); [Paladin](/z_Mechanics/CLI/lists/list-spells-classes-paladin.md); [Wizard (Diviner)](/z_Mechanics/CLI/lists/list-spells-classes-wizard-xphb-diviner-xphb.md "subclass=XPHB;class=XPHB"); [Fighter (Eldritch Knight)](/z_Mechanics/CLI/lists/list-spells-classes-fighter-xphb-eldritch-knight-xphb.md "subclass=XPHB;class=XPHB") *Source: Player's Handbook (2024) p. 293. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Silence
>
> ```badges
> items:
>   - label: Level 2
>   - label: Illusion
>   - label: R
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S
> duration: Concentration, up to 1 minute
> ```
>
> - **Casting time:** 1 Action unless cast as a ritual - **Range:** 120 feet - **Components:** V, S - **Duration:** Concentration, up to 10 minutes For the duration, no sound can be created within or pass through a 20-foot-radius Sphere centered on a point you choose within range. Any creature or object entirely inside the Sphere has [Immunity](/z_Mechanics/CLI/variant-rules/immunity-xphb.md) to Thunder damage, and creatures have the [Deafened](/z_Mechanics/CLI/conditions.md#Deafened) condition while entirely inside it. Casting a spell that includes a Verbal component is impossible there. **Classes**: [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Ranger](/z_Mechanics/CLI/lists/list-spells-classes-ranger.md); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md) *Source: Player's Handbook (2024) p. 316. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Spiritual Weapon
>
> ```badges
> items:
>   - label: Level 2
>   - label: Evocation
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Reaction
> range: 0 feet
> components: V, S
> duration: Concentration, up to 20 feet
> ```
>
> ![](/z_Mechanics/CLI/spells/img/spiritual-weapon.webp#right) - **Casting time:** 1 Bonus Action - **Range:** 60 feet - **Components:** V, S - **Duration:** Concentration, up to 1 minute You create a floating, spectral force that resembles a weapon of your choice and lasts for the duration. The force appears within range in a space of your choice, and you can immediately make one melee spell attack against one creature within 5 feet of the force. On a hit, the target takes Force damage equal to `1d8` plus your spellcasting ability modifier. As a [Bonus Action](/z_Mechanics/CLI/variant-rules/bonus-action-xphb.md) on your later turns, you can move the force up to 20 feet and repeat the attack against a creature within 5 feet of it. **Classes**: [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Cleric (War Domain)](/z_Mechanics/CLI/lists/list-spells-classes-cleric-xphb-war-domain-xphb.md "subclass=XPHB;class=XPHB"); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md) *Source: Player's Handbook (2024) p. 319. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Dispel Magic
>
> ```badges
> items:
>   - label: Level 3
>   - label: Abjuration
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S
> duration: Varies
> ```
>
> - **Casting time:** 1 Action - **Range:** 120 feet - **Components:** V, S - **Duration:** Instantaneous Choose one creature, object, or magical effect within range. Any ongoing spell of level 3 or lower on the target ends. For each ongoing spell of level 4 or higher on the target, make an ability check using your spellcasting ability (DC 10 plus that spell's level). On a successful check, the spell ends. **Classes**: [Wizard](/z_Mechanics/CLI/lists/list-spells-classes-wizard.md); [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Druid](/z_Mechanics/CLI/lists/list-spells-classes-druid.md); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md); [Sorcerer](/z_Mechanics/CLI/lists/list-spells-classes-sorcerer.md); [Fighter (Eldritch Knight)](/z_Mechanics/CLI/lists/list-spells-classes-fighter-xphb-eldritch-knight-xphb.md "subclass=XPHB;class=XPHB"); [Rogue (Arcane Trickster)](/z_Mechanics/CLI/lists/list-spells-classes-rogue-xphb-arcane-trickster-xphb.md "subclass=XPHB;class=XPHB"); [Paladin (Oath of Devotion)](/z_Mechanics/CLI/lists/list-spells-classes-paladin-xphb-oath-of-devotion-xphb.md "subclass=XPHB;class=XPHB"); [Ranger](/z_Mechanics/CLI/lists/list-spells-classes-ranger.md); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Wizard (Abjurer)](/z_Mechanics/CLI/lists/list-spells-classes-wizard-xphb-abjurer-xphb.md "subclass=XPHB;class=XPHB"); [Paladin](/z_Mechanics/CLI/lists/list-spells-classes-paladin.md); [Sorcerer (Clockwork Sorcery)](/z_Mechanics/CLI/lists/list-spells-classes-sorcerer-xphb-clockwork-sorcery-xphb.md "subclass=XPHB;class=XPHB"); [Warlock](/z_Mechanics/CLI/lists/list-spells-classes-warlock.md) *Source: Player's Handbook (2024) p. 264. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Mass Healing Word
>
> ```badges
> items:
>   - label: Level 3
>   - label: Abjuration
> ```
>
> ```spell-components
> casting_time: 1 Reaction
> range: 0 feet
> components: V
> duration: Varies
> ```
>
> - **Casting time:** 1 Bonus Action - **Range:** 60 feet - **Components:** V - **Duration:** Instantaneous Up to six creatures of your choice that you can see within range regain [Hit Points](/z_Mechanics/CLI/variant-rules/hit-points-xphb.md) equal to `2d4` plus your spellcasting ability modifier. **Classes**: [Cleric (Life Domain)](/z_Mechanics/CLI/lists/list-spells-classes-cleric-xphb-life-domain-xphb.md "subclass=XPHB;class=XPHB"); [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md) *Source: Player's Handbook (2024) p. 296. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Remove Curse
>
> ```badges
> items:
>   - label: Level 3
>   - label: Abjuration
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S
> duration: Varies
> ```
>
> - **Casting time:** 1 Action - **Range:** Touch - **Components:** V, S - **Duration:** Instantaneous At your touch, all curses affecting one creature or object end. If the object is a cursed magic item, its curse remains, but the spell breaks its owner's [Attunement](/z_Mechanics/CLI/variant-rules/attunement-xphb.md) to the object so it can be removed or discarded. **Classes**: [Rogue (Arcane Trickster)](/z_Mechanics/CLI/lists/list-spells-classes-rogue-xphb-arcane-trickster-xphb.md "subclass=XPHB;class=XPHB"); [Wizard](/z_Mechanics/CLI/lists/list-spells-classes-wizard.md); [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md); [Wizard (Abjurer)](/z_Mechanics/CLI/lists/list-spells-classes-wizard-xphb-abjurer-xphb.md "subclass=XPHB;class=XPHB"); [Paladin](/z_Mechanics/CLI/lists/list-spells-classes-paladin.md); [Fighter (Eldritch Knight)](/z_Mechanics/CLI/lists/list-spells-classes-fighter-xphb-eldritch-knight-xphb.md "subclass=XPHB;class=XPHB"); [Warlock](/z_Mechanics/CLI/lists/list-spells-classes-warlock.md) *Source: Player's Handbook (2024) p. 312. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Revivify
>
> ```badges
> items:
>   - label: Level 3
>   - label: Necromancy
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S, M (a diamond worth 300+ GP, which the spell consumes)
> duration: Varies
> ```
>
> - **Casting time:** 1 Action - **Range:** Touch - **Components:** V, S, M (a diamond worth 300+ GP, which the spell consumes) - **Duration:** Instantaneous You touch a creature that has died within the last minute. That creature revives with 1 [Hit Point](/z_Mechanics/CLI/variant-rules/hit-points-xphb.md). This spell can't revive a creature that has died of old age, nor does it restore any missing body parts. **Classes**: [Warlock (Celestial Patron)](/z_Mechanics/CLI/lists/list-spells-classes-warlock-xphb-celestial-patron-xphb.md "subclass=XPHB;class=XPHB"); [Cleric (Life Domain)](/z_Mechanics/CLI/lists/list-spells-classes-cleric-xphb-life-domain-xphb.md "subclass=XPHB;class=XPHB"); [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Druid](/z_Mechanics/CLI/lists/list-spells-classes-druid.md); [Ranger](/z_Mechanics/CLI/lists/list-spells-classes-ranger.md); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md); [Paladin](/z_Mechanics/CLI/lists/list-spells-classes-paladin.md) *Source: Player's Handbook (2024) p. 312. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Spirit Guardians
>
> ```badges
> items:
>   - label: Level 3
>   - label: Conjuration
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S, M (a prayer scroll)
> duration: Concentration, up to 1 minute
> ```
>
> - **Casting time:** 1 Action - **Range:** Self (15-foot Emanation) - **Components:** V, S, M (a prayer scroll) - **Duration:** Concentration, up to 10 minutes Protective spirits flit around you in a 15-foot Emanation for the duration. If you are good or neutral, their spectral form appears angelic or fey (your choice). If you are evil, they appear fiendish. When you cast this spell, you can designate creatures to be unaffected by it. Any other creature's [Speed](/z_Mechanics/CLI/variant-rules/speed-xphb.md) is halved in the Emanation, and whenever the Emanation enters a creature's space and whenever a creature enters the Emanation or ends its turn there, the creature must make a Wisdom saving throw. On a failed save, the creature takes `3d8` Radiant damage (if you are good or neutral) or `3d8` Necrotic damage (if you are evil). On a successful save, the creature takes half as much damage. A creature makes this save only once per turn. **Classes**: [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Cleric (War Domain)](/z_Mechanics/CLI/lists/list-spells-classes-cleric-xphb-war-domain-xphb.md "subclass=XPHB;class=XPHB"); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md) *Source: Player's Handbook (2024) p. 319. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Control Water
>
> ```badges
> items:
>   - label: Level 4
>   - label: Transmutation
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S, M (a mixture of water and dust)
> duration: Concentration, up to 100 feet
> ```
>
> - **Casting time:** 1 Action - **Range:** 300 feet - **Components:** V, S, M (a mixture of water and dust) - **Duration:** Concentration, up to 10 minutes Until the spell ends, you control any water inside an area you choose that is a Cube up to 100 feet on a side, using one of the following effects. As a [Magic](/z_Mechanics/CLI/actions.md#Magic) action on your later turns, you can repeat the same effect or choose a different one. ## Flood You cause the water level of all standing water in the area to rise by as much as 20 feet. If you choose an area in a large body of water, you instead create a 20-foot tall wave that travels from one side of the area to the other and then crashes. Any Huge or smaller vehicles in the wave's path are carried with it to the other side. Any Huge or smaller vehicles struck by the wave have a  chance of capsizing. The water level remains elevated until the spell ends or you choose a different effect. If this effect produced a wave, the wave repeats on the start of your next turn while the flood effect lasts. ## Part Water You part water in the area and create a trench. The trench extends across the spell's area, and the separated water forms a wall to either side. The trench remains until the spell ends or you choose a different effect. The water then slowly fills in the trench over the course of the next round until the normal water level is restored. ## Redirect Flow You cause flowing water in the area to move in a direction you choose, even if the water has to flow over obstacles, up walls, or in other unlikely directions. The water in the area moves as you direct it, but once it moves beyond the spell's area, it resumes its flow based on the terrain. The water continues to move in the direction you chose until the spell ends or you choose a different effect. ## Whirlpool You cause a whirlpool to form in the center of the area, which must be at least 50 feet square and 25 feet deep. The whirlpool lasts until you choose a different effect or the spell ends. The whirlpool is 5 feet wide at the base, up to 50 feet wide at the top, and 25 feet tall. Any creature in the water and within 25 feet of the whirlpool is pulled 10 feet toward it. When a creature enters the whirlpool for the first time on a turn or ends its turn there, it makes a Strength saving throw. On a failed save, the creature takes `2d8` Bludgeoning damage. On a successful save, the creature takes half as much damage. A creature can swim away from the whirlpool only if it first takes an action to pull away and succeeds on a Strength ([Athletics](/z_Mechanics/CLI/skills.md#Athletics)) check against your spell save DC. ## Summary **Classes**: [Rogue (Arcane Trickster)](/z_Mechanics/CLI/lists/list-spells-classes-rogue-xphb-arcane-trickster-xphb.md "subclass=XPHB;class=XPHB"); [Wizard](/z_Mechanics/CLI/lists/list-spells-classes-wizard.md); [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Druid](/z_Mechanics/CLI/lists/list-spells-classes-druid.md); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md); [Fighter (Eldritch Knight)](/z_Mechanics/CLI/lists/list-spells-classes-fighter-xphb-eldritch-knight-xphb.md "subclass=XPHB;class=XPHB") *Source: Player's Handbook (2024) p. 256. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Guardian of Faith
>
> ```badges
> items:
>   - label: Level 4
>   - label: Conjuration
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V
> duration: Varies
> ```
>
> ![](/z_Mechanics/CLI/spells/img/guardian-of-faith.webp#right) - **Casting time:** 1 Action - **Range:** 30 feet - **Components:** V - **Duration:** 8 hours A Large spectral guardian appears and hovers for the duration in an unoccupied space that you can see within range. The guardian occupies that space and is invulnerable, and it appears in a form appropriate for your deity or pantheon. Any enemy that moves to a space within 10 feet of the guardian for the first time on a turn or starts its turn there makes a Dexterity saving throw, taking 20 Radiant damage on a failed save or half as much damage on a successful one. The guardian vanishes when it has dealt a total of 60 damage. **Classes**: [Warlock (Celestial Patron)](/z_Mechanics/CLI/lists/list-spells-classes-warlock-xphb-celestial-patron-xphb.md "subclass=XPHB;class=XPHB"); [Paladin (Oath of Devotion)](/z_Mechanics/CLI/lists/list-spells-classes-paladin-xphb-oath-of-devotion-xphb.md "subclass=XPHB;class=XPHB"); [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md) *Source: Player's Handbook (2024) p. 281. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Mass Cure Wounds
>
> ```badges
> items:
>   - label: Level 5
>   - label: Abjuration
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S
> duration: Varies
> ```
>
> - **Casting time:** 1 Action - **Range:** 60 feet - **Components:** V, S - **Duration:** Instantaneous A wave of healing energy washes out from a point you can see within range. Choose up to six creatures in a 30-foot-radius Sphere centered on that point. Each target regains [Hit Points](/z_Mechanics/CLI/variant-rules/hit-points-xphb.md) equal to `5d8` plus your spellcasting ability modifier. **Classes**: [Cleric (Life Domain)](/z_Mechanics/CLI/lists/list-spells-classes-cleric-xphb-life-domain-xphb.md "subclass=XPHB;class=XPHB"); [Cleric](/z_Mechanics/CLI/lists/list-spells-classes-cleric.md); [Druid](/z_Mechanics/CLI/lists/list-spells-classes-druid.md); [Druid (Circle of the Moon)](/z_Mechanics/CLI/lists/list-spells-classes-druid-xphb-circle-of-the-moon-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md) *Source: Player's Handbook (2024) p. 296. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

> ^spells

^spellcasting

---

## Features

<span class="right-link">[[#Character Statistics|Top]]</span>
>### Domain Spells
>
> You gain domain spells based on your cleric level.
>
>### Bonus Proficiencies
>
> You gain proficiency with heavy armor and smith’s tools.
>
>### Blessing of the Forge
>
> At the end of a long rest, you can imbue magic into a weapon or armor by touching a nonmagical version. Until your next long rest or you die, the object grants a +1 bonus to either AC or attack and damage rolls. You can't use this feature again until you finish a long rest.
>
>### Channel Divinity: Artisan's Blessing
>
> *Class Feature (Level 2)*
>
> You can use your Channel Divinity to conduct an hour-long ritual that crafts a nonmagical item that must include some metal: a simple or martial weapon, a suit of armor, ten pieces of ammunition, a set of tools, or another metal object. The thing you create can be something that is worth no more than 100 gp.
>
>### Soul of the Forge
>
> *Class Feature (Level 6)*
>
> You gain resistance to fire damage and while wearing heavy armor, you gain a +1 bonus to AC.
>
>### Divine Strike
>
> *Class Feature (Level 8)*
>
> Once on each of your turns when you hit a creature with a weapon attack, you can cause the attack to deal an extra 1d8 fire damage. [14th] 2d8 Fire Damage
>
>### Spellcasting
>
> You can cast prepared cleric spells using WIS as your spellcasting modifier (Spell DC {{savedc:wis}}, Spell Attack {{spellattack:wis}}) and prepared cleric spells as rituals if they have the ritual tag. You can use a holy symbol as a spellcasting focus.
>
>### Divine Domain
>
> You choose a divine domain that grants you additional spells and other features related to your deity.
>
>### Channel Divinity
>
> *Class Feature (Level 2)*
>
> You can channel divine energy to fuel magical effects a number of times per short rest
>
>### Ability Score Improvement
>
> *Class Feature (Level 4)*
>
> When you reach 4th level, and again at 8th, 12th, 16th, and 19th level, you can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1. As normal, you can’t increase an ability score above 20 using this feature. Using the optional feats rule, you can forgo taking this feature to take a feat of your choice instead.
>
>### Destroy Undead
>
> *Class Feature (Level 5)*
>
> When an undead fails its saving throw against your Turn Undead feature, it is instantly destroyed if its CR is lower than the threshold for your level.
>
>### Ability Score Improvement
>
> *Class Feature (Level 8)*
>
> When you reach 8th level, and again at 12th, 16th, and 19th level, you can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1. As normal, you can’t increase an ability score above 20 using this feature. Using the optional feats rule, you can forgo taking this feature to take a feat of your choice instead.
>
>### Divine Intervention
>
> *Class Feature (Level 10)*
>
> As an action, you can request your deity's aid and roll percentile dice. If your roll is equal to or less than {{classlevel}}, your deity intervenes (your DM chooses the nature of the intervention). If successful, you can't use this feature again for 7 days, otherwise, you can use it again after a long rest. At 20th level, your request succeeds automatically, no roll required.
>
>### Proficiencies
>
> Armor: Light armor, medium armor, shieldsWeapons: Simple weaponsTools: NoneSaving Throws: Wisdom, CharismaSkills: Choose two from History, Insight, Medicine, Persuasion, and Religion
>
>### Hit Points
>
> Hit Dice: 1d8 per cleric levelHit Points at 1st Level: 8 + your Constitution modifierHit Points at Higher Levels: 1d8 (or 5) + your Constitution modifier per cleric level after 1st
>
>### Equipment
>
> You start with the following equipment, in addition to the equipment granted by your background: (a) a mace or (b) a warhammer (if proficient) (a) scale mail, (b) leather armor, or (c) chain mail (if proficient) (a) a light crossbow and 20 bolts or (b) any simple weapon (a) a priest’s pack or (b) an explorer’s pack A shield and a holy symbol
>

### Action Economy

**Action:**
- Command (0th level)
- Control Water (0th level)
- Cure Wounds (0th level)
- Dispel Magic (0th level)
- Guardian of Faith (0th level)
- Healing Word (0th level)
- Locate Object (0th level)
- Mass Cure Wounds (0th level)
- Mass Healing Word (0th level)
- Mending
- Remove Curse (0th level)
- Revivify (0th level)
- Sacred Flame
- Silence (0th level)
- Spirit Guardians (0th level)
- Spiritual Weapon (0th level)
- Thaumaturgy
- Word of Radiance
- **Standard Actions:** Attack, Cast a Spell, Dash, Disengage, Dodge, Help, Hide, Ready, Search, Use Object

**Bonus Action:**
- Command
- Spiritual Weapon
- If cast: Cure Wounds
- If cast: Healing Word
- If cast: Spiritual Weapon

**Reaction:**
- Channel Divinity
- Healing Word
- Mass Healing Word
- Opportunity Attack
- Ready Action Trigger
- Spiritual Weapon

> ^features

---

## Racial Traits

<span class="right-link">[[#Character Statistics|Top]]</span>
>### Warforged (UA) Traits
>
>#### Ability Score Increase
>
> Your Constitution score increases by 1.
>
>#### Age
>
> A typical warforged is between two and thirty years old. The maximum lifespan of the warforged remains a mystery; so far, warforged have shown no signs of deterioration due to age.
>
>#### Alignment
>
> Most warforged take comfort in order and discipline, tending toward law and neutrality. But some have absorbed the morality &mdash; or lack thereof &mdash; of the beings with which they served.
>
>#### Warforged Resilience
>
> You were created to have remarkable fortitude, represented by the following benefits. You have advantage on saving throws against being poisoned, and you have resistance to poison damage. You are immune to disease. You don’t need to eat, drink, or breathe. You don’t need to sleep and don’t suffer the effects of exhaustion due to lack of rest, and magic can’t put you to sleep.
>
>#### Integrated Protection
>
> Your body has built-in defensive layers, which determine your armor class. You gain no benefit from wearing armor, but if you are using a shield, you apply its bonus as normal. You can alter your body to enter different defensive modes; each time you finish a long rest, choose one mode to adopt from the Integrated Protection table, provided you meet the mode’s prerequisite. Mode Prerequisite Effect Darkwood Core (unarmored) None 11 + your Dexterity modifier (add proficiency bonus if proficient with light armor) Composite Plating (armor) Medium armor proficiency 13 + your Dexterity modifier (maximum of 2) + your proficiency bonus. Heavy Plating (armor) Heavy armor proficiency 16 + your proficiency bonus; disadvantage on Dexterity (Stealth) checks.
>
>#### Sentry's Rest
>
> When you take a long rest, you must spend at least six hours in an inactive, motionless state, rather than sleeping. In this state, you appear inert, but it doesn’t render you unconscious, and you can see and hear as normal.
>
>#### Languages
>
> You can speak, read, and write Common.
>
>#### Ability Score Increase
>
> Two different ability scores of your choice increase by 1.
>
>#### Specialized Design
>
> You gain one skill proficiency of your choice, one tool proficiency of your choice, and fluency in one language of your choice.
>
>#### Integrated Tool
>
> Choose one tool you’re proficient with. This tool is integrated into your body, and you double your proficiency bonus for any ability checks you make with it. You must have your hands free to use this integrated tool.
>
> ^racial-traits


---

## Attacks

<span class="right-link">[[#Character Statistics|Top]]</span>

>
> ### Sun Blade
> **Type:** Longsword
> **Attack Bonus:** +3
> **Damage:** 1d8 + -1 slashing
> **Properties:** Versatile (1d10), Finesse
> **Weight:** 3.0 lbs
> 
> ### Heavy Plating
> **Type:** None
> **Attack Bonus:** +7
> **Damage:** 1d4 + 3 piercing
> **Weight:** 55.0 lbs
> 
> ### Javelin
> **Type:** Javelin
> **Attack Bonus:** +7
> **Damage:** 1d4 + 3 piercing
> **Weight:** 2.0 lbs
> 
> ### Quarterstaff
> **Type:** Quarterstaff
> **Attack Bonus:** +7
> **Damage:** 1d6 + 3 bludgeoning
> **Properties:** Versatile (1d8)
> **Weight:** 4.0 lbs
> 
> ^attacks

---

## Proficiencies

<span class="right-link">[[#Character Statistics|Top]]</span>
>### Weapons
>
> - Simple Weapons (Class: Cleric)
>
>### Tools
>
> - Mason's Tools (Species: Warforged Envoy)
> - Smith's Tools (Class: Cleric)
> - Tinker's Tools (Background: Guild Artisan / Guild Merchant)
>
>### Languages
>
> - Common (Species: Warforged Envoy)
> - Draconic (Species: Warforged Envoy)
> - Elvish (Background: Guild Artisan / Guild Merchant)
>
>### Ability Score Bonuses
>
> - **Strength** +1 (ASI/Choices)
> - **Constitution** +1 (Species/Race)
> - **Wisdom** +2 (Species/Race)
> - **Wisdom** +3 (ASI/Choices)
>
> ^proficiencies

---

## Background

<span class="right-link">[[#Character Statistics|Top]]</span>
>### Guild Artisan / Guild Merchant
>
> <p>You are a member of an artisan’s guild, skilled in a particular field and closely associated with other artisans. You are a well-established part of the mercantile world, freed by talent and wealth from the constraints of a feudal social order. You learned your skills as an apprentice to a master artisan, under the sponsorship of your guild, until you became a master in your own right.</p>
<hr />
<p><strong>Skill Proficiencies:</strong> Insight, Persuasion</p>
<p><strong>Tool Proficiencies:</strong> One type of artisan’s tools</p>
<p><strong>Languages:</strong> One of your choice</p>
<p><strong>Equipment:</strong> A set of artisan’s tools (one of your choice), a letter of introduction from your guild, a set of traveler’s clothes, and a pouch containing 15 gp</p>
<hr />
<h5 class="compendium-hr">Guild Business</h5>
<p>Guilds are generally found in cities large enough to support several artisans practicing the same trade. However, your guild might instead be a loose network of artisans who each work in a different village within a larger realm. Work with your DM to determine the nature of your guild. You can select your guild business from the Guild Business table or roll randomly.</p>
<table class="compendium-left-aligned-table">
<thead>
<tr>
<th>d20</th>
<th style="text-align: left;">Guild Business</th>
</tr>
</thead>
<tbody>
<tr>
<td>1</td>
<td>Alchemists and apothecaries</td>
</tr>
<tr>
<td>2</td>
<td>Armorers, locksmiths, and finesmiths</td>
</tr>
<tr>
<td>3</td>
<td>Brewers, distillers, and vintners</td>
</tr>
<tr>
<td>4</td>
<td>Calligraphers, scribes, and scriveners</td>
</tr>
<tr>
<td>5</td>
<td>Carpenters, roofers, and plasterers</td>
</tr>
<tr>
<td>6</td>
<td>Cartographers, surveyors, and chart-makers</td>
</tr>
<tr>
<td>7</td>
<td>Cobblers and shoemakers</td>
</tr>
<tr>
<td>8</td>
<td>Cooks and bakers</td>
</tr>
<tr>
<td>9</td>
<td>Glassblowers and glaziers</td>
</tr>
<tr>
<td>10</td>
<td>Jewelers and gemcutters</td>
</tr>
<tr>
<td>11</td>
<td>Leatherworkers, skinners, and tanners</td>
</tr>
<tr>
<td>12</td>
<td>Masons and stonecutters</td>
</tr>
<tr>
<td>13</td>
<td>Painters, limners, and sign-makers</td>
</tr>
<tr>
<td>14</td>
<td>Potters and tile-makers</td>
</tr>
<tr>
<td>15</td>
<td>Shipwrights and sailmakers</td>
</tr>
<tr>
<td>16</td>
<td>Smiths and metal-forgers</td>
</tr>
<tr>
<td>17</td>
<td>Tinkers, pewterers, and casters</td>
</tr>
<tr>
<td>18</td>
<td>Wagon-makers and wheelwrights</td>
</tr>
<tr>
<td>19</td>
<td>Weavers and dyers</td>
</tr>
<tr>
<td>20</td>
<td>Woodcarvers, coopers, and bowyers</td>
</tr>
</tbody>
</table>
<p>As a member of your guild, you know the skills needed to create finished items from raw materials (reflected in your proficiency with a certain kind of artisan’s tools), as well as the principles of trade and good business practices. The question now is whether you abandon your trade for adventure, or take on the extra effort to weave adventuring and trade together.</p>
<hr />
<h5 class="compendium-hr">Feature: Guild Membership</h5>
<p>As an established and respected member of a guild, you can rely on certain benefits that membership provides. Your fellow guild members will provide you with lodging and food if necessary, and pay for your funeral if needed. In some cities and towns, a guildhall offers a central place to meet other members of your profession, which can be a good place to meet potential patrons, allies, or hirelings.</p>
<p>Guilds often wield tremendous political power. If you are accused of a crime, your guild will support you if a good case can be made for your innocence or the crime is justifiable. You can also gain access to powerful political figures through the guild, if you are a member in good standing. Such connections might require the donation of money or magic items to the guild’s coffers.</p>
<p>You must pay dues of 5 gp per month to the guild. If you miss payments, you must make up back dues to remain in the guild’s good graces.</p>
<hr />
<h5 class="compendium-hr">Variant Guild Artisan: Guild Merchant</h5>
<p>Instead of an artisans’ guild, you might belong to a guild of traders, caravan masters, or shopkeepers. You don’t craft items yourself but earn a living by buying and selling the works of others (or the raw materials artisans need to practice their craft). Your guild might be a large merchant consortium (or family) with interests across the region. Perhaps you transported goods from one place to another, by ship, wagon, or caravan, or bought them from traveling traders and sold them in your own little shop. In some ways, the traveling merchant’s life lends itself to adventure far more than the life of an artisan.</p>
>
> ^background

---

## Backstory

<span class="right-link">[[#Character Statistics|Top]]</span>
> Forged in lightning and blood by the dark wizard Eludrax, "Eight" was born. The wizard's thirst for eternal life led him not to the cultivation of a new fleshy body, but a perfect one of his own design.
Using ancient techniques from lands quite distant, Eludrax forged machines for his allies war efforts. Nothing, however, could keep him from his true life's work.
>
> ---
>
> It was the eighth of Eludrax's shield guardians, and thus aptly named.
>
> Most of of the Lich's constructs bore no soul of their own, merely mindless automatons for his own bidding. He would often pluck lost souls from Limbo and twist and torture them to suit his machinations.
>
> But the eight were different. They were his personal bodyguards, improved physically in every way, and candidates for his transference of life. Most importantly, they were devoid of soul.
>
> At the aging dark wizard's command the constructs committed unspeakable atrocities. They were the harbingers of his dirty work, and Eludrax was not above committing horrors in the name of his research.
>
> Eight was his magnum opus, and thus his intended vessel. His plan to transfer his own soul into the guardian was made haste, however, as Eludrax awoke one night to an adventurer's group tearing through his laboratory. He commanded Eight to follow, sending the other seven to combat the coming threat.
>
> He clamored as fast as he could to the dark crystal machine intended to bind his soul into his vessel,  and spilled his blood on the dais with a quick slice to the palm. He grasped Eight's cool metal hand, and forced it onto the crystal. Thus, the dark ritual began. Eludrax's eyes went white as his spirit was ripped from his body and absorbed into the orb.
>
> What he miscalculated, however, was that a soul already existed inside his creation. It was faint, beaten down by years of cruelty and transgression, but there nonetheless.
>
> The Lich's powerful spirit growled menacingly as it reached out to pluck the soul from Eight. Before he could, however, a burst of radiance appeared to encapsulate the soul. Eludrax's fury burned hot, but was not strong enough to pierce the veil of light.
>
> Time was not on the dark wizard's side. The party that'd breached his laboratory had finally made it into this sanctum. The group exchanged quick words, deliberating on their plan of action. Before their sorcerer could cry out, however, the paladin raised her mace and brought it crashing down on the large swirling crystal. As it shattered, the wizard's soul was cast into limbo, spiraling out of the material plane with a guttural scream.
>
> "Am I...?" Eight spoke aloud with a sound of relief, before collapsing to the cold stone floor with a hearty thud.
>
> ---
>
> Eight awoke to the stench of burning and the feel of a warm hand against its cold metal chest. In the distance the tower it'd known as its home, the place of its creation, was fervently ablaze.
>
> "Can it understand us?" One of the adventurers pondered out loud. 
Eight nodded in response
>
> The woman whose hand was pulsating over it with life magic leaned in a bit closer to its face.
"So, do you have a name?" She asked in a soft voice, curiously, as if she were talking to a child.
>
> Eight looked down at the ground, then back at the burning spire behind him.
>
> "Redgrave," it muttered quietly, then returned its gaze to hers.
>
> "My name is Redgrave."
>
> "Like that tower?" One of the men in the group asked questioningly.
>
> "Yes," the forged known formerly as Eight responded.
"So that I may never forget what happened here."
>
> 
> ^backstory

---

## Inventory

<span class="right-link">[[#Character Statistics|Top]]</span>
> **Wealth:** 21 gp, 33 sp *(Total: 24 gp)*
> **Encumbrance:** 153.1/240 lbs (63% - Medium)
>
>
>### Cloak of Protection
>
> **Type:** Wondrous item
> **Quantity:** 1
> **Equipped:** Yes
>
>### Sun Blade
>
> **Type:** Longsword
> **Quantity:** 1
> **Equipped:** Yes
> **Weight:** 3.0 lbs
>
>### Heavy Plating
>
> **Type:** None
> **Quantity:** 1
> **Equipped:** Yes
> **Weight:** 55.0 lbs
>
>### Holy Symbol of Ravenkind
>
> **Type:** Wondrous item
> **Quantity:** 1
> **Equipped:** Yes
>
>### Shield
>
> **Type:** Shield
> **Quantity:** 1
> **Equipped:** Yes
> **Weight:** 6.0 lbs
>
>### Javelin
>
> **Type:** Javelin
> **Quantity:** 6
> **Equipped:** Yes
> **Weight:** 2.0 lbs
>
>### Mace
>
> **Type:** Mace
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 4.0 lbs
>
>### Quarterstaff
>
> **Type:** Quarterstaff
> **Quantity:** 1
> **Equipped:** Yes
> **Weight:** 4.0 lbs
>
>### Spear
>
> **Type:** Spear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 3.0 lbs
>
>### Backpack
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 5.0 lbs
>
>### Potion of Healing
>
> **Type:** Gear
> **Quantity:** 0
> **Equipped:** No
> **Weight:** 0.5 lbs
>
>### Waterskin
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 5.0 lbs
>
>### Smith's Tools
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 8.0 lbs
>
>### Holy Symbol
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
>
>### Wand of Secrets
>
> **Type:** Wand
> **Quantity:** 1
> **Equipped:** No
>
>### Bedroll
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 7.0 lbs
>
>### Mess Kit
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 1.0 lbs
>
>### Rope, Hempen (50 feet)
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 10.0 lbs
>
>### Tinderbox
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 1.0 lbs
>
>### Torch
>
> **Type:** Gear
> **Quantity:** 10
> **Equipped:** No
> **Weight:** 1.0 lbs
>
>### Mason's Tools
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 8.0 lbs
>
>### Tinker's Tools
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 10.0 lbs
>
> ^inventory