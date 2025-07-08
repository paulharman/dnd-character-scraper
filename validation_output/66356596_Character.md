---
avatar_url: "https://www.dndbeyond.com/avatars/24206/840/1581111423-66356596.jpeg?width=150&height=150&fit=crop&quality=95&auto=webp"
character_name: "Dor'ren Uroprax"
level: 6
proficiency_bonus: 3
experience: 6500
class: "Warlock"
subclass: "The Hexblade"
hit_die: "d8"
is_2024_rules: False
race: "Dragonborn"
background: "Investigator"
ability_scores:
  strength: 8
  dexterity: 14
  constitution: 14
  intelligence: 10
  wisdom: 12
  charisma: 18
ability_modifiers:
  strength: -1
  dexterity: +2
  constitution: +2
  intelligence: +0
  wisdom: +1
  charisma: +4
armor_class: 16
current_hp: 45
max_hp: 45
initiative: "+2"
spellcasting_ability: "charisma"
spell_save_dc: 15
character_id: "66356596"
processed_date: "2025-07-02 17:21:06"
scraper_version: "6.0.0"
speed: "30 ft"
spell_count: 10
highest_spell_level: 3
spells:
  - "[[eldritch-blast-xphb]]"
  - "[[friends-xphb]]"
  - "[[green-flame-blade-xphb]]"
  - "[[hex-xphb]]"
  - "[[suggestion-xphb]]"
  - "[[blink-xphb]]"
  - "[[counterspell-xphb]]"
  - "[[dispel-magic-xphb]]"
  - "[[major-image-xphb]]"
  - "[[thunder-step-xphb]]"
spell_list: ['Eldritch Blast', 'Friends', 'Green-Flame Blade', 'Hex', 'Suggestion', 'Blink', 'Counterspell', 'Dispel Magic', 'Major Image', 'Thunder Step']
inventory_items: 23
passive_perception: 11
passive_investigation: 10
passive_insight: 11
copper: 0
silver: 205
electrum: 0
gold: 1057
platinum: 0
total_wealth_gp: 1077
carrying_capacity: 120
current_weight: 165
magic_items_count: 23
attuned_items: 0
max_attunement: 3
next_level_xp: 23000
xp_to_next_level: 16500
multiclass: False
total_caster_level: 6
hit_dice_remaining: 6
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
tags: ['dnd', 'character-sheet', 'warlock', 'warlock-the-hexblade', 'investigator', 'dragonborn', 'mid-level', 'spellcaster']
---

```run-python
import os, sys, subprocess
os.chdir(r'C:\Users\alc_u\Documents\DnD\CharacterScraper')
vault_path = @vault_path
note_path = @note_path
full_path = os.path.join(vault_path, note_path)
cmd = ['python', 'dnd_json_to_markdown.py', '66356596', full_path, '--scraper-path', 'enhanced_dnd_scraper.py']
result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', shell=True)
print('\n\n')
print('SUCCESS: Character refreshed!' if result.returncode == 0 else f'ERROR: {result.stderr}')
print('Reload file to see changes.' if result.returncode == 0 else '')
```


---

> [!infobox]+ ^character-info
> # Dor'ren Uroprax
> ![Character Avatar|200](https://www.dndbeyond.com/avatars/24206/840/1581111423-66356596.jpeg?width=150&height=150&fit=crop&quality=95&auto=webp)
> ###### Character Details
> |  |  |
> | --- | --- |
> | **Class** | Warlock |
> | **Subclass** | The Hexblade |
> | **Race** | Dragonborn |
> | **Background** | Investigator |
> | **Level** | 6 |
> | **Hit Points** | 45/45 |
> | **HP Calc** | Manual |
> | **Armor Class** | 16 |
> | **Proficiency** | +3 |
> 
> ###### Ability Scores
> |  |  |  |
> | --- | --- | --- |
> | **Str** 8 (-1) | **Dex** 14 (+2) | **Con** 14 (+2) |
> | **Int** 10 (+0) | **Wis** 12 (+1) | **Cha** 18 (+4) |

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
| [D&D Beyond](https://www.dndbeyond.com/characters/66356596) |

---

## Character Statistics

```stats
items:
  - label: Level
    value: '6'
  - label: Class
    value: 'Warlock'
  - label: Subclass
    value: 'The Hexblade'
  - label: Initiative
    value: '+2'
  - label: Speed
    value: '30 ft'
  - label: Armor Class
    sublabel: Unarmored (10 + Dex)
    value: 16

grid:
  columns: 3
```

<BR>

```healthpoints
state_key: dor'ren_uroprax_health
health: 45
hitdice:
  dice: d8
  value: 6
```

^character-statistics

---

## Abilities & Skills

```ability
abilities:
  strength: {'score': 8, 'modifier': -1, 'save_bonus': -1, 'source_breakdown': {'base': 8}}
  dexterity: {'score': 14, 'modifier': 2, 'save_bonus': 2, 'source_breakdown': {'base': 13, 'asi': 1}}
  constitution: {'score': 14, 'modifier': 2, 'save_bonus': 5, 'source_breakdown': {'base': 14}}
  intelligence: {'score': 10, 'modifier': 0, 'save_bonus': 0, 'source_breakdown': {'base': 10}}
  wisdom: {'score': 12, 'modifier': 1, 'save_bonus': 4, 'source_breakdown': {'base': 12}}
  charisma: {'score': 18, 'modifier': 4, 'save_bonus': 7, 'source_breakdown': {'base': 15, 'feat': 1, 'asi': 2}}

proficiencies:
  - charisma
  - constitution
  - wisdom
```

<BR>

```badges
items:
  - label: Passive Perception
    value: 14
  - label: Passive Investigation
    value: 13
  - label: Passive Insight
    value: 14
```

<BR>

```skills
proficiencies:
  - insight
  - intimidation
  - investigation
  - perception


```

### Proficiency Sources
> **Skill Bonuses:**
> - **Insight** (Background: Investigator)
> - **Intimidation** (Class: Warlock)
> - **Investigation** (Class: Warlock)
> - **Perception** (Background: Investigator)
>
> **Saving Throw Bonuses:**
> - **Charisma** +7 (Class: Warlock)
> - **Constitution** +5 (Class: Warlock)
> - **Wisdom** +4 (Class: Warlock)
>
> ^proficiency-sources

^abilities-skills

---

## Appearance

<span class="right-link">[[#Character Statistics|Top]]</span>
> **Gender:** Male
> **Age:** 29
> **Height:** 6'8
> **Weight:** 295
> **Hair:** None
> **Eyes:** Red
> **Skin:** Blue
> **Size:** Medium
>
> ^appearance

---

## Spellcasting

<span class="right-link">[[#Character Statistics|Top]]</span>
> ```stats
> items:
>   - label: Spell Save DC
>     value: 15
>   - label: Spell Attack Bonus
>     value: '+7'
>   - label: Spellcasting Ability
>     value: 'Charisma'
>   - label: Spellcasting Modifier
>     value: '+4'
>
> grid:
>   columns: 4
> ```
>
> ^spellstats

### Spell Slots
> ```consumable
> items:
>   - label: 'Pact Slots (Level 3)'
>     state_key: dor'ren_uroprax_pact_slots
>     uses: 2
> ```
>
> ^spellslots

### Spell List
> | Level | Spell | School | Components | Casting Time | Concentration | Source |
> |-------|-------|--------|------------|--------------|---------------|--------|
> | Cantrip | [[#Eldritch Blast]] | Evocation | V, S | 1 Action |  | Warlock |
> | Cantrip | [[#Friends]] | Enchantment | S, M (some makeup) | 1 Action | Yes | Warlock |
> | Cantrip | [[#Green-Flame Blade]] | Evocation | V, S | 1 Action |  | Warlock |
> | 1 | [[#Hex]] | Enchantment | V, S, M (the petrified eye of a newt) | 1 Reaction | Yes | Warlock |
> | 2 | [[#Suggestion]] | Enchantment | V, M (a drop of honey) | 1 Action | Yes | Warlock |
> | 3 | [[#Blink]] | Transmutation | V, S | 1 Action |  | Warlock |
> | 3 | [[#Counterspell]] | Abjuration | S | 1 Minute |  | Warlock |
> | 3 | [[#Dispel Magic]] | Abjuration | V, S | 1 Action |  | Warlock |
> | 3 | [[#Major Image]] | Illusion | V, S, M (a bit of fleece) | 1 Action | Yes | Warlock |
> | 3 | [[#Thunder Step]] | Conjuration | V, S | 1 Action |  | Warlock |
>
> ^spelltable

### Spell Details
#### Eldritch Blast
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
> **Classes**: [Warlock](/z_Mechanics/CLI/lists/list-spells-classes-warlock.md) *Source: Player's Handbook (2024) p. 267. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Friends
>
> ```badges
> items:
>   - label: Cantrip
>   - label: Enchantment
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: S, M (some makeup)
> duration: Concentration, up to 1 minute
> ```
>
> For the duration, you have advantage on all Charisma checks directed at one creature of your choice that isn’t hostile toward you. When the spell ends, the creature realizes that you used magic to influence its mood and becomes hostile toward you. A creature prone to violence might attack you. Another creature might seek retribution in other ways (at the DM’s discretion), depending on the nature of your interaction with it.
>

<BR>

#### Green-Flame Blade
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
> You brandish the weapon used in the spell’s casting and make a melee attack with it against one creature within 5 feet of you. On a hit, the target suffers the weapon attack’s normal effects, and you can cause green fire to leap from the target to a different creature of your choice that you can see within 5 feet of it. The second creature takes fire damage equal to your spellcasting ability modifier. This spell’s damage increases when you reach certain levels. At 5th level, the melee attack deals an extra 1d8 fire damage to the target on a hit, and the fire damage to the second creature increases to 1d8 + your spellcasting ability modifier. Both damage rolls increase by 1d8 at 11th level (2d8 and 2d8) and 17th level (3d8 and 3d8).
>

<BR>

#### Hex
>
> ```badges
> items:
>   - label: Level 1
>   - label: Enchantment
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Reaction
> range: 0 feet
> components: V, S, M (the petrified eye of a newt)
> duration: 8 hours
> ```
>
> - **Casting time:** 1 Bonus Action - **Range:** 90 feet - **Components:** V, S, M (the petrified eye of a newt) - **Duration:** Concentration, up to 1 hour You place a curse on a creature that you can see within range. Until the spell ends, you deal an extra `1d6` Necrotic damage to the target whenever you hit it with an attack roll. Also, choose one ability when you cast the spell. The target has [Disadvantage](/z_Mechanics/CLI/variant-rules/disadvantage-xphb.md) on ability checks made with the chosen ability. If the target drops to 0 [Hit Points](/z_Mechanics/CLI/variant-rules/hit-points-xphb.md) before this spell ends, you can take a [Bonus Action](/z_Mechanics/CLI/variant-rules/bonus-action-xphb.md) on a later turn to curse a new creature. **Classes**: [Warlock (Great Old One Patron)](/z_Mechanics/CLI/lists/list-spells-classes-warlock-xphb-great-old-one-patron-xphb.md "subclass=XPHB;class=XPHB"); [Warlock](/z_Mechanics/CLI/lists/list-spells-classes-warlock.md) *Source: Player's Handbook (2024) p. 285. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Suggestion
>
> ```badges
> items:
>   - label: Level 2
>   - label: Enchantment
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, M (a drop of honey)
> duration: Concentration, up to 1 minute
> ```
>
> - **Casting time:** 1 Action - **Range:** 30 feet - **Components:** V, M (a drop of honey) - **Duration:** Concentration, up to 8 hours You suggest a course of activity—described in no more than 25 words—to one creature you can see within range that can hear and understand you. The suggestion must sound achievable and not involve anything that would obviously deal damage to the target or its allies. For example, you could say, "Fetch the key to the cult's treasure vault, and give the key to me." Or you could say, "Stop fighting, leave this library peacefully, and don't return." The target must succeed on a Wisdom saving throw or have the [Charmed](/z_Mechanics/CLI/conditions.md#Charmed) condition for the duration or until you or your allies deal damage to the target. The [Charmed](/z_Mechanics/CLI/conditions.md#Charmed) target pursues the suggestion to the best of its ability. The suggested activity can continue for the entire duration, but if the suggested activity can be completed in a shorter time, the spell ends for the target upon completing it. **Classes**: [Rogue (Arcane Trickster)](/z_Mechanics/CLI/lists/list-spells-classes-rogue-xphb-arcane-trickster-xphb.md "subclass=XPHB;class=XPHB"); [Wizard](/z_Mechanics/CLI/lists/list-spells-classes-wizard.md); [Warlock (Fiend Patron)](/z_Mechanics/CLI/lists/list-spells-classes-warlock-xphb-fiend-patron-xphb.md "subclass=XPHB;class=XPHB"); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md); [Sorcerer](/z_Mechanics/CLI/lists/list-spells-classes-sorcerer.md); [Fighter (Eldritch Knight)](/z_Mechanics/CLI/lists/list-spells-classes-fighter-xphb-eldritch-knight-xphb.md "subclass=XPHB;class=XPHB"); [Warlock](/z_Mechanics/CLI/lists/list-spells-classes-warlock.md) *Source: Player's Handbook (2024) p. 321. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Blink
>
> ```badges
> items:
>   - label: Level 3
>   - label: Transmutation
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S
> duration: Varies
> ```
>
> - **Casting time:** 1 Action - **Range:** Self - **Components:** V, S - **Duration:** 1 minute Roll `1d6` at the end of each of your turns for the duration. On a roll of 4-6, you vanish from your current plane of existence and appear in the Ethereal Plane (the spell ends instantly if you are already on that plane). While on the Ethereal Plane, you can perceive the plane you left, which is cast in shades of gray, but you can't see anything there more than 60 feet away. You can affect and be affected only by other creatures on the Ethereal Plane, and creatures on the other plane can't perceive you unless they have a special ability that lets them perceive things on the Ethereal Plane. You return to the other plane at the start of your next turn and when the spell ends if you are on the Ethereal Plane. You return to an unoccupied space of your choice that you can see within 10 feet of the space you left. If no unoccupied space is available within that range, you appear in the nearest unoccupied space. **Classes**: [Rogue (Arcane Trickster)](/z_Mechanics/CLI/lists/list-spells-classes-rogue-xphb-arcane-trickster-xphb.md "subclass=XPHB;class=XPHB"); [Wizard](/z_Mechanics/CLI/lists/list-spells-classes-wizard.md); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md); [Sorcerer](/z_Mechanics/CLI/lists/list-spells-classes-sorcerer.md); [Fighter (Eldritch Knight)](/z_Mechanics/CLI/lists/list-spells-classes-fighter-xphb-eldritch-knight-xphb.md "subclass=XPHB;class=XPHB"); [Warlock (Archfey Patron)](/z_Mechanics/CLI/lists/list-spells-classes-warlock-xphb-archfey-patron-xphb.md "subclass=XPHB;class=XPHB") *Source: Player's Handbook (2024) p. 248. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Counterspell
>
> ```badges
> items:
>   - label: Level 3
>   - label: Abjuration
> ```
>
> ```spell-components
> casting_time: 1 Minute
> range: 0 feet
> components: S
> duration: Varies
> ```
>
> - **Casting time:** 1 Reaction - **Range:** 60 feet - **Components:** S - **Duration:** Instantaneous You attempt to interrupt a creature in the process of casting a spell. The creature makes a Constitution saving throw. On a failed save, the spell dissipates with no effect, and the action, [Bonus Action](/z_Mechanics/CLI/variant-rules/bonus-action-xphb.md), or [Reaction](/z_Mechanics/CLI/variant-rules/reaction-xphb.md) used to cast it is wasted. If that spell was cast with a spell slot, the slot isn't expended. **Classes**: [Rogue (Arcane Trickster)](/z_Mechanics/CLI/lists/list-spells-classes-rogue-xphb-arcane-trickster-xphb.md "subclass=XPHB;class=XPHB"); [Wizard](/z_Mechanics/CLI/lists/list-spells-classes-wizard.md); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md); [Wizard (Abjurer)](/z_Mechanics/CLI/lists/list-spells-classes-wizard-xphb-abjurer-xphb.md "subclass=XPHB;class=XPHB"); [Sorcerer](/z_Mechanics/CLI/lists/list-spells-classes-sorcerer.md); [Fighter (Eldritch Knight)](/z_Mechanics/CLI/lists/list-spells-classes-fighter-xphb-eldritch-knight-xphb.md "subclass=XPHB;class=XPHB"); [Warlock](/z_Mechanics/CLI/lists/list-spells-classes-warlock.md) *Source: Player's Handbook (2024) p. 258. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
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

#### Major Image
>
> ```badges
> items:
>   - label: Level 3
>   - label: Illusion
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S, M (a bit of fleece)
> duration: Concentration, up to 1 minute
> ```
>
> - **Casting time:** 1 Action - **Range:** 120 feet - **Components:** V, S, M (a bit of fleece) - **Duration:** Concentration, up to 10 minutes You create the image of an object, a creature, or some other visible phenomenon that is no larger than a 20-foot Cube. The image appears at a spot that you can see within range and lasts for the duration. It seems real, including sounds, smells, and temperature appropriate to the thing depicted, but it can't deal damage or cause conditions. If you are within range of the illusion, you can take a [Magic](/z_Mechanics/CLI/actions.md#Magic) action to cause the image to move to any other spot within range. As the image changes location, you can alter its appearance so that its movements appear natural for the image. For example, if you create an image of a creature and move it, you can alter the image so that it appears to be walking. Similarly, you can cause the illusion to make different sounds at different times, even making it carry on a conversation, for example. Physical interaction with the image reveals it to be an illusion, for things can pass through it. A creature that takes a [Study](/z_Mechanics/CLI/actions.md#Study) action to examine the image can determine that it is an illusion with a successful Intelligence ([Investigation](/z_Mechanics/CLI/skills.md#Investigation)) check against your spell save DC. If a creature discerns the illusion for what it is, the creature can see through the image, and its other sensory qualities become faint to the creature. **Classes**: [Rogue (Arcane Trickster)](/z_Mechanics/CLI/lists/list-spells-classes-rogue-xphb-arcane-trickster-xphb.md "subclass=XPHB;class=XPHB"); [Wizard](/z_Mechanics/CLI/lists/list-spells-classes-wizard.md); [Bard (College of Lore)](/z_Mechanics/CLI/lists/list-spells-classes-bard-xphb-college-of-lore-xphb.md "subclass=XPHB;class=XPHB"); [Bard](/z_Mechanics/CLI/lists/list-spells-classes-bard.md); [Sorcerer](/z_Mechanics/CLI/lists/list-spells-classes-sorcerer.md); [Fighter (Eldritch Knight)](/z_Mechanics/CLI/lists/list-spells-classes-fighter-xphb-eldritch-knight-xphb.md "subclass=XPHB;class=XPHB"); [Warlock](/z_Mechanics/CLI/lists/list-spells-classes-warlock.md); [Wizard (Illusionist)](/z_Mechanics/CLI/lists/list-spells-classes-wizard-xphb-illusionist-xphb.md "subclass=XPHB;class=XPHB") *Source: Player's Handbook (2024) p. 295. Available in the <span title='Systems Reference Document (5.2)'>SRD</span>*
>

<BR>

#### Thunder Step
>
> ```badges
> items:
>   - label: Level 3
>   - label: Conjuration
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 0 feet
> components: V, S
> duration: Varies
> ```
>
> You teleport yourself to an unoccupied space you can see within range. Immediately after you disappear, a thunderous boom sounds, and each creature within 10 feet of the space you left must make a Constitution saving throw, taking 3d10 thunder damage on a failed save, or half as much damage on a successful one. The thunder can be heard from up to 300 feet away. You can bring along objects as long as their weight doesn’t exceed what you can carry. You can also teleport one willing creature of your size or smaller who is carrying gear up to its carrying capacity. The creature must be within 5 feet of you when you cast this spell, and there must be an unoccupied space within 5 feet of your destination space for the creature to appear in; otherwise, the creature is left behind. At Higher Levels.&nbsp;When you cast this spell using a spell slot of 4th level or higher, the damage increases by 1d10 for each slot level above 3rd.
>

<BR>

> ^spells

^spellcasting

---

## Features

<span class="right-link">[[#Character Statistics|Top]]</span>
>### Expanded Spell List
>
> Additional spells are added to the warlock spell list for you.
>
>### Hexblade’s Curse
>
> Once per short rest, as a bonus action, choose one creature you can see within 30 ft. to curse it for 1 minute (or until the target dies, you die, or you are incapacitated). Against the cursed target, you gain a {{proficiency#signed}} bonus to damage rolls, score a critical hit on a roll of 19 or 20, and you regain {{(classlevel+modifier:cha)@min:1#unsigned}} HP if it dies.
>
>### Hex Warrior
>
> You gain proficiency with medium armor, shields, and martial weapons. Whenever you finish a long rest, you can touch one weapon that you are proficient with and that lacks the two-handed property. With that weapon, you can use your CHA modifier for the attack and damage rolls until you finish your next long rest. You can also use your CHA modifier for the attack and damage rolls for any of your pact weapons if you have that feature.
>
>### Accursed Specter
>
> *Class Feature (Level 6)*
>
> When you slay a humanoid, you can cause its spirit to rise as a specter that gains {{(classlevel/2)@rounddown#signed}} temp HP. Roll initiative for the specter, which has its own turns. It obeys your verbal commands, gains a {{modifier:cha@min:0#signed}} bonus to its attack rolls, and remains until the end of your next long rest.
>
>### Ability Score Improvement
>
> *Class Feature (Level 4)*
>
> When you reach 4th level, and again at 8th, 12th, 16th, and 19th level, you can increase one ability score of your choice by 2, or you can increase two ability scores of your choice by 1. As normal, you can’t increase an ability score above 20 using this feature. Using the optional feats rule, you can forgo taking this feature to take a feat of your choice instead.
>
>### Otherworldly Patron
>
> You have struck a bargain with an otherworldly being.
>
>### Pact Magic
>
> You can cast known warlock spells using CHA as your spellcasting modifier (Spell DC {{savedc:cha}}, Spell Attack {{spellattack:cha}}). You can use an arcane focus as a spellcasting focus.
>
>### Eldritch Invocations
>
> *Class Feature (Level 2)*
>
> You learn fragments of forbidden knowledge that imbue you with an abiding magical ability.
>
>### Pact Boon
>
> *Class Feature (Level 3)*
>
> Your otherworldly patron bestows a gift upon you for your loyal service.
>
>### Proficiencies
>
> Armor: Light armorWeapons: Simple weaponsTools: NoneSaving Throws: Wisdom, CharismaSkills: Choose two skills from Arcana, Deception, History, Intimidation, Investigation, Nature, and Religion
>
>### Hit Points
>
> Hit Dice: 1d8 per warlock levelHit Points at 1st Level: 8 + your Constitution modifierHit Points at Higher Levels: 1d8 (or 5) + your Constitution modifier per warlock level after 1st
>
>### Equipment
>
> You start with the following equipment, in addition to the equipment granted by your background: (a) a light crossbow and 20 bolts or (b) any simple weapon (a) a component pouch or (b) an arcane focus (a) a scholar’s pack or (b) a dungeoneer’s pack Leather armor, any simple weapon, and two daggers
>

### Action Economy

**Action:**
- Blink (0th level)
- Dispel Magic (0th level)
- Eldritch Blast
- Friends
- Green-Flame Blade
- Hex (0th level)
- Major Image (0th level)
- Suggestion (0th level)
- Thunder Step (0th level)
- **Standard Actions:** Attack, Cast a Spell, Dash, Disengage, Dodge, Help, Hide, Ready, Search, Use Object

**Bonus Action:**
- Hex
- Hexblade’s Curse

**Reaction:**
- Hex
- Opportunity Attack
- Ready Action Trigger

> ^features

---

## Racial Traits

<span class="right-link">[[#Character Statistics|Top]]</span>
>### Dragonborn Traits
>
>#### Age
>
> Young dragonborn grow quickly. They walk hours after hatching, attain the size and development of a 10-year-old human child by the age of 3, and reach adulthood by 15. They live to be around 80.
>
>#### Ability Score Increases
>
> When determining your character’s ability scores, increase one of those scores by 2 and increase a different score by 1, or increase three different scores by 1. Follow this rule regardless of the method you use to determine the scores, such as rolling or point buy. The &ldquo;Quick Build&rdquo; section for your character’s class offers suggestions on which scores to increase. You’re free to follow those suggestions or to ignore them. Whichever scores you decide to increase, none of the scores can be raised above 20.
>
>#### Languages
>
> Your character can speak, read, and write Common and one other language that you and your DM agree is appropriate for the character. The Player’s Handbook offers a list of widespread languages to choose from. The DM is free to add or remove languages from that list for a particular campaign.
>
>#### Metallic Ancestry
>
> You have a metallic dragon ancestor, granting you a special magical affinity. Choose one kind of dragon from the Metallic Ancestry table. This determines the damage type for your other traits, as shown in the table. Metallic Ancestry Dragon Damage Type Brass Fire Bronze Lightning Copper Acid Gold Fire Silver Cold
>
>#### Breath Weapon
>
> When you take the Attack action on your turn, you can replace one of your attacks with an exhalation of magical energy in a 15-foot cone. Each creature in that area must make a Dexterity saving throw (DC = 8 + your Constitution modifier + your proficiency bonus). On a failed save, the creature takes 1d10 damage of the type associated with your Metallic Ancestry. On a successful save, it takes half as much damage. This damage increases by 1d10 when you reach 5th level (2d10), 11th level (3d10), and 17th level (4d10). You can use your Breath Weapon a number of times equal to your proficiency bonus, and you regain all expended uses when you finish a long rest.
>
>#### Draconic Resistance
>
> You have resistance to the damage type associated with your Metallic Ancestry.
>
>#### Metallic Breath Weapon
>
> At 5th level, you gain a second breath weapon. When you take the Attack action on your turn, you can replace one of your attacks with an exhalation in a 15-foot cone. The save DC for this breath is 8 + your Constitution modifier + your proficiency bonus. Whenever you use this trait, choose one: Enervating Breath. Each creature in the cone must succeed on a Constitution saving throw or become incapacitated until the start of your next turn. Repulsion Breath. Each creature in the cone must succeed on a Strength saving throw or be pushed 20 feet away from you and be knocked prone. Once you use your Metallic Breath Weapon, you can’t do so again until you finish a long rest.
>
> ^racial-traits


---

## Attacks

<span class="right-link">[[#Character Statistics|Top]]</span>

>
> ### Dagger
> **Type:** Dagger
> **Attack Bonus:** +5
> **Damage:** 1d4 + 2 piercing
> **Properties:** Finesse, Light, Thrown
> **Weight:** 1.0 lbs
> 
> ### Dagger
> **Type:** Dagger
> **Attack Bonus:** +5
> **Damage:** 1d4 + 2 piercing
> **Properties:** Finesse, Light, Thrown
> **Weight:** 1.0 lbs
> 
> ### Handaxe
> **Type:** Handaxe
> **Attack Bonus:** +2
> **Damage:** 1d4 + -1 piercing
> **Weight:** 2.0 lbs
> 
> ### Crossbow, Light
> **Type:** Crossbow, Light
> **Attack Bonus:** +5
> **Damage:** 1d8 + 2 piercing
> **Range:** 80/320 ft
> **Properties:** Ammunition, Light, Loading
> **Weight:** 5.0 lbs
> 
> ### Warhammer
> **Type:** Warhammer
> **Attack Bonus:** +2
> **Damage:** 1d4 + -1 piercing
> **Weight:** 5.0 lbs
> 
> ^attacks

---

## Proficiencies

<span class="right-link">[[#Character Statistics|Top]]</span>
>### Weapons
>
> - Martial Weapons (Class: Warlock)
> - Simple Weapons (Class: Warlock)
>
>### Tools
>
> - Disguise Kit (Background: Investigator)
> - Thieves' Tools (Background: Investigator)
>
>### Languages
>
> - Common (Species: Metallic Dragonborn)
> - Draconic (Species: Metallic Dragonborn)
>
>### Ability Score Bonuses
>
> - **Dexterity** +1 (ASI/Choices)
> - **Charisma** +1 (Feats)
> - **Charisma** +2 (ASI/Choices)
>
> ^proficiencies

---

## Background

<span class="right-link">[[#Character Statistics|Top]]</span>
>### Investigator
>
> <p>You relentlessly seek the truth. Perhaps you’re motivated by belief in the law and a sense of universal justice, or maybe that very law has failed you and you seek to make things right. You could have witnessed something remarkable or terrible, and now you must know more about this hidden truth. Or maybe you’re a detective for hire, uncovering secrets for well-paying clients. Whether the mysteries you’re embroiled in are local crimes or realm-spanning conspiracies, you’re driven by a personal need to hunt down even the most elusive clues and reveal what others would keep hidden in the shadows.</p>
<p><strong>Skill Proficiencies:</strong> Choose two from among Insight, Investigation, or Perception</p>
<p><strong>Tool Proficiencies:</strong> Disguise kit, thieves’ tools</p>
<p><strong>Equipment:</strong> A magnifying glass, evidence from a past case (choose one or roll for a trinket from the Horror Trinkets table after this background), a set of common clothes, and 10 gp</p>
<h4 id="PathtoMystery" class="compendium-hr">Path to Mystery</h4>
<p>Your first case influenced the types of mysteries you’re interested in. Why was this case so impactful, personal, or traumatic? Whom did it affect besides you? Why and how did you get involved? Was it solved? How did it set you on the path to investigating other mysteries? Roll on or choose details from the First Case table to develop the mystery that started your career as an investigator.</p>
<h5 id="FirstCaseTable" class="quick-menu-exclude compendium-hr">First Case</h5>
<table class="table--generic-dice">
<thead>
<tr>
<th>d8</th>
<th>Case</th>
</tr>
</thead>
<tbody>
<tr>
<td>1</td>
<td>A friend was wrongfully accused of murder. You tracked down the actual killer, proving your friend’s innocence and starting your career as a detective.</td>
</tr>
<tr>
<td>2</td>
<td>You’re told you went missing for weeks. When you were found, you had no memory of being gone. Now you search to discover what happened to you.</td>
</tr>
<tr>
<td>3</td>
<td>You helped a spirit find peace by finding its missing corpse. Ever since, other spectral clients have sought you out to help them find rest.</td>
</tr>
<tr>
<td>4</td>
<td>You revealed that the monsters terrorizing your home were illusions created by a cruel mage. The magic-user escaped, but you’ve continued to uncover magical hoaxes.</td>
</tr>
<tr>
<td>5</td>
<td>You were wrongfully accused and convicted of a crime. You managed to escape and seek to help others avoid the experience you suffered, even while still being pursued by the law.</td>
</tr>
<tr>
<td>6</td>
<td>You survived the destructive use of a magic device that wiped out your home. Members of a secret organization found you. You now work with them, tracking down dangerous supernatural phenomena and preventing them from doing harm.</td>
</tr>
<tr>
<td>7</td>
<td>You found evidence of a conspiracy underpinning society. You tried to expose this mysterious cabal, but no one believed you. You’re still trying to prove what you know is true.</td>
</tr>
<tr>
<td>8</td>
<td>You got a job with an agency that investigates crimes that local law enforcement can’t solve. You often wonder which you value more, the truth or your pay.</td>
</tr>
</tbody>
</table>
>
> ^background

---

## Backstory

<span class="right-link">[[#Character Statistics|Top]]</span>
> *No backstory available.*
> 
> ^backstory

---

## Inventory

<span class="right-link">[[#Character Statistics|Top]]</span>
> **Wealth:** 1057 gp, 205 sp *(Total: 1077 gp)*
> **Encumbrance:** 190.7/120 lbs (158% - Heavy)
>
>
>### Cloak of Displacement
>
> **Type:** Wondrous item
> **Quantity:** 1
> **Equipped:** Yes
>
>### Scale Mail
>
> **Type:** 
> **Quantity:** 1
> **Equipped:** Yes
> **Weight:** 45.0 lbs
>
>### Dagger
>
> **Type:** Dagger
> **Quantity:** 1
> **Equipped:** Yes
> **Weight:** 1.0 lbs
>
>### Dagger
>
> **Type:** Dagger
> **Quantity:** 1
> **Equipped:** Yes
> **Weight:** 1.0 lbs
>
>### Handaxe
>
> **Type:** Handaxe
> **Quantity:** 1
> **Equipped:** Yes
> **Weight:** 2.0 lbs
>
>### Crossbow, Light
>
> **Type:** Crossbow, Light
> **Quantity:** 1
> **Equipped:** Yes
> **Weight:** 5.0 lbs
>
>### Warhammer
>
> **Type:** Warhammer
> **Quantity:** 1
> **Equipped:** Yes
> **Weight:** 5.0 lbs
>
>### Crossbow Bolts
>
> **Type:** Gear
> **Quantity:** 20
> **Equipped:** Yes
> **Weight:** 1.5 lbs
>
>### Backpack
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 5.0 lbs
>
>### Healer's Kit
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 3.0 lbs
>
>### Playing Card Set
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
>
>### Arcane Focus
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
>
>### Alchemy Jug
>
> **Type:** Wondrous item
> **Quantity:** 1
> **Equipped:** Yes
> **Weight:** 12.0 lbs
>
>### Amulet of the Drunkard
>
> **Type:** Wondrous item
> **Quantity:** 1
> **Equipped:** Yes
>
>### Crowbar
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 5.0 lbs
>
>### Hammer
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 3.0 lbs
>
>### Piton
>
> **Type:** Gear
> **Quantity:** 10
> **Equipped:** No
> **Weight:** 0.25 lbs
>
>### Rations (1 day)
>
> **Type:** Gear
> **Quantity:** 10
> **Equipped:** No
> **Weight:** 2.0 lbs
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
>### Waterskin
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
> **Weight:** 5.0 lbs
>
>### Antitoxin
>
> **Type:** Gear
> **Quantity:** 1
> **Equipped:** No
>
> ^inventory