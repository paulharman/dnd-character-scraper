---
avatar_url: "https://www.dndbeyond.com/avatars/48761/398/1581111423-145081718.jpeg?width=150&height=150&fit=crop&quality=95&auto=webp"
character_name: "Ilarion Veles (Paul)"
level: 2
proficiency_bonus: 2
experience: 753
class: "Wizard"

hit_die: "d6"
is_2024_rules: False
race: "Elf"
background: "Sage"
ability_scores:
  strength: 9
  dexterity: 13
  constitution: 16
  intelligence: 16
  wisdom: 12
  charisma: 10
ability_modifiers:
  strength: -1
  dexterity: +1
  constitution: +3
  intelligence: +3
  wisdom: +1
  charisma: +0
armor_class: 11
current_hp: 16
max_hp: 16
initiative: "+1"
spellcasting_ability: "intelligence"
spell_save_dc: 13
character_id: "145081718"
processed_date: "2025-07-03 00:26:17"
scraper_version: "6.0.0"
speed: "30 ft"
spell_count: 15
highest_spell_level: 1
spells:
  - "[[acid-splash-xphb]]"
  - "[[fire-bolt-xphb]]"
  - "[[mind-sliver-xphb]]"
  - "[[minor-illusion-xphb]]"
  - "[[prestidigitation-xphb]]"
  - "[[true-strike-xphb]]"
  - "[[comprehend-languages-xphb]]"
  - "[[detect-magic-xphb]]"
  - "[[disguise-self-xphb]]"
  - "[[find-familiar-xphb]]"
  - "[[identify-xphb]]"
  - "[[magic-missile-xphb]]"
  - "[[shield-xphb]]"
  - "[[sleep-xphb]]"
  - "[[unseen-servant-xphb]]"
spell_list: ['Acid Splash', 'Fire Bolt', 'Mind Sliver', 'Minor Illusion', 'Prestidigitation', 'True Strike', 'Comprehend Languages', 'Detect Magic', 'Disguise Self', 'Find Familiar', 'Identify', 'Magic Missile', 'Shield', 'Sleep', 'Unseen Servant']
inventory_items: 21
passive_perception: 11
passive_investigation: 13
passive_insight: 11
copper: 0
silver: 12
electrum: 0
gold: 32
platinum: 0
total_wealth_gp: 33
carrying_capacity: 135
current_weight: 72
magic_items_count: 21
attuned_items: 0
max_attunement: 3
next_level_xp: 900
xp_to_next_level: 147
multiclass: False
total_caster_level: 2
hit_dice_remaining: 2
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
tags: ['dnd', 'character-sheet', 'wizard', 'sage', 'elf', 'low-level', 'spellcaster']
---

```run-python
import os, sys, subprocess
os.chdir(r'C:\Users\alc_u\Documents\DnD\CharacterScraper')
vault_path = @vault_path
note_path = @note_path
full_path = os.path.join(vault_path, note_path)
cmd = ['python', 'dnd_json_to_markdown.py', '145081718', full_path, '--scraper-path', 'enhanced_dnd_scraper.py']
result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', shell=True)
print('\n\n')
print('SUCCESS: Character refreshed!' if result.returncode == 0 else f'ERROR: {result.stderr}')
print('Reload file to see changes.' if result.returncode == 0 else '')
```


---

> [!infobox]+ ^character-info
> # Ilarion Veles (Paul)
> ![Character Avatar|200](https://www.dndbeyond.com/avatars/48761/398/1581111423-145081718.jpeg?width=150&height=150&fit=crop&quality=95&auto=webp)
> ###### Character Details
> |  |  |
> | --- | --- |
> | **Class** | Wizard |
> | **Race** | Elf |
> | **Background** | Sage |
> | **Level** | 2 |
> | **Hit Points** | 16/16 |
> | **HP Calc** | Manual |
> | **Armor Class** | 11 |
> | **Proficiency** | +2 |
> 
> ###### Ability Scores
> |  |  |  |
> | --- | --- | --- |
> | **Str** 9 (-1) | **Dex** 13 (+1) | **Con** 16 (+3) |
> | **Int** 16 (+3) | **Wis** 12 (+1) | **Cha** 10 (+0) |

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
| [D&D Beyond](https://www.dndbeyond.com/characters/145081718) |

---

## Character Statistics

```stats
items:
  - label: Level
    value: '2'
  - label: Class
    value: 'Wizard'
  - label: Subclass
    value: 'None'
  - label: Initiative
    value: '+1'
  - label: Speed
    value: '30 ft'
  - label: Armor Class
    sublabel: Unarmored (10 + Dex)
    value: 11

grid:
  columns: 3
```

<BR>

```healthpoints
state_key: ilarion_veles_paul_health
health: 16
hitdice:
  dice: d6
  value: 2
```

^character-statistics

---

## Abilities & Skills

```ability
abilities:
  strength: 9
  dexterity: 13
  constitution: 16
  intelligence: 16
  wisdom: 12
  charisma: 10

proficiencies:
  - intelligence
  - wisdom
```

<BR>

```badges
items:
  - label: Passive Perception
    value: 13
  - label: Passive Investigation
    value: 17
  - label: Passive Insight
    value: 13
```

<BR>

```skills
proficiencies:
  - arcana
  - history
  - insight
  - perception

expertise:
  - investigation
```

### Proficiency Sources
> **Skill Bonuses:**
> - **Arcana** (Class: Wizard)
> - **History** (Background: Sage)
> - **Insight** (Background: Sage)
> - **Investigation** (Class: Wizard)
> - **Perception** (Species: Elf)
>
> **Saving Throw Bonuses:**
> - **Intelligence** +5 (Class: Wizard)
> - **Wisdom** +3 (Class: Wizard)
>
> ^proficiency-sources

^abilities-skills

---

## Appearance

<span class="right-link">[[#Character Statistics|Top]]</span>
> **Gender:** Male
> **Age:** 52
> **Height:** 6'
> **Weight:** 155
> **Hair:** Silver
> **Eyes:** Violet
> **Skin:** Light
> **Size:** Medium
>
> ^appearance

### Physical Description

Handsome, angular jawline, high cheekbones, and a narrow, refined nose. His carriage is graceful but proud, suggesting both intellect and superiority. Loki, his raven, is often perched on his shoulder or circling overhead, lending an aura of enigmatic companionship.

---

## Spellcasting

<span class="right-link">[[#Character Statistics|Top]]</span>
> ```stats
> items:
>   - label: Spell Save DC
>     value: 13
>   - label: Spell Attack Bonus
>     value: '+5'
>   - label: Spellcasting Ability
>     value: 'Intelligence'
>   - label: Spellcasting Modifier
>     value: '+3'
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
>     state_key: ilarion_veles_paul_spells_1
>     uses: 3
> ```
>
> ^spellslots

### Free Cast Spells
> ```consumable
> items:
>   - label: 'Detect Magic (Magic Initiate)'
>     state_key: ilarion_veles_paul_detect_magic_free
>     uses: 1
> ```
>
> ^freecasts

### Spell List
> | Level | Spell | School | Components | Casting Time | Concentration | Prepared | Source |
> |-------|-------|--------|------------|--------------|---------------|----------|--------|
> | Cantrip | [[#Acid Splash]] | Evocation | V, S | 1 Action |  | — | Wizard |
> | Cantrip | [[#Fire Bolt]] | Evocation | V, S | 1 Action |  | — | Elf Heritage |
> | Cantrip | [[#Mind Sliver]] | Enchantment | V | 1 Action |  | — | Magic Initiate (Wizard) |
> | Cantrip | [[#Minor Illusion]] | Illusion | S, M (a bit of fleece) | 1 Action |  | — | Magic Initiate (Wizard) |
> | Cantrip | [[#Prestidigitation]] | Transmutation | V, S | 1 Action |  | — | Wizard |
> | Cantrip | [[#True Strike]] | Divination | S, M (a weapon with which you have proficiency and that is worth 1+ CP) | 1 Action |  | — | Wizard |
> | 1 | [[#Comprehend Languages]] | Divination | V, S, M (a pinch of soot and salt) | 1 Action |  | Ritual | Wizard |
> | 1 | [[#Detect Magic]] | Divination | V, S | 1 Action | Yes | Ritual | Magic Initiate (Wizard) |
> | 1 | [[#Disguise Self]] | Illusion | V, S | 1 Action |  | Yes | Wizard |
> | 1 | [[#Find Familiar]] | Conjuration | V, S, M (burning incense worth 10+ GP, which the spell consumes) | 1 Hour |  | Ritual | Wizard |
> | 1 | [[#Identify]] | Divination | V, S, M (a pearl worth 100+ GP) | 1 Minute |  | Ritual | Wizard |
> | 1 | [[#Magic Missile]] | Evocation | V, S | 1 Action |  | Yes | Wizard |
> | 1 | [[#Shield]] | Abjuration | V, S | 1 Reaction |  | Yes | Wizard |
> | 1 | [[#Sleep]] | Enchantment | V, S, M (a pinch of sand or rose petals) | 1 Action | Yes | Yes | Wizard |
> | 1 | [[#Unseen Servant]] | Conjuration | V, S, M (a bit of string and of wood) | 1 Action |  | Ritual | Wizard |
>
> ^spelltable

### Spell Details
#### Acid Splash
>
> ```badges
> items:
>   - label: Cantrip
>   - label: Evocation
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 60 feet
> components: V, S
> duration: Instantaneous
> ```
>
> You create an acidic bubble at a point within range, where it explodes in a 5-foot-radius Sphere. Each creature in that Sphere must succeed on a Dexterity saving throw or take `1d6` Acid damage.
>
> **Cantrip Upgrade.** The damage increases by `1d6` when you reach levels 5 (`2d6`), 11 (`3d6`), and 17 (`4d6`).
>

<BR>

#### Fire Bolt
>
> ```badges
> items:
>   - label: Cantrip
>   - label: Evocation
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 120 feet
> components: V, S
> duration: Instantaneous
> ```
>
> You hurl a mote of fire at a creature or an object within range. Make a ranged spell attack against the target. On a hit, the target takes `1d10` Fire damage. A flammable object hit by this spell starts [burning](/z_Mechanics/CLI/traps-hazards/burning-xphb.md) if it isn't being worn or carried.
>
> **Cantrip Upgrade.** The damage increases by `1d10` when you reach levels 5 (`2d10`), 11 (`3d10`), and 17 (`4d10`).
>

<BR>

#### Mind Sliver
>
> ```badges
> items:
>   - label: Cantrip
>   - label: Enchantment
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 60 feet
> components: V
> duration: Instantaneous
> ```
>
> You try to temporarily sliver the mind of one creature you can see within range. The target must succeed on an Intelligence saving throw or take `1d6` Psychic damage and subtract `1d4` from the next saving throw it makes before the end of your next turn.
>
> **Cantrip Upgrade.** The damage increases by `1d6` when you reach levels 5 (`2d6`), 11 (`3d6`), and 17 (`4d6`).
>

<BR>

#### Minor Illusion
>
> ```badges
> items:
>   - label: Cantrip
>   - label: Illusion
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 30 feet
> components: S, M (a bit of fleece)
> duration: 1 minute
> ```
>
> You create a sound or an image of an object within range that lasts for the duration. See the descriptions below for the effects of each. The illusion ends if you cast this spell again.
>
> If a creature takes a [Study](/z_Mechanics/CLI/actions.md#Study) action to examine the sound or image, the creature can determine that it is an illusion with a successful Intelligence ([Investigation](/z_Mechanics/CLI/skills.md#Investigation)) check against your spell save DC. If a creature discerns the illusion for what it is, the illusion becomes faint to the creature.
>
> ##### Sound
>
> If you create a sound, its volume can range from a whisper to a scream. It can be your voice, someone else's voice, a lion's roar, a beating of drums, or any other sound you choose. The sound continues unabated throughout the duration, or you can make discrete sounds at different times before the spell ends.
>
> ##### Image
>
> If you create an image of an object—such as a chair, muddy footprints, or a small chest—it must be no larger than a 5-foot Cube. The image can't create sound, light, smell, or any other sensory effect. Physical interaction with the image reveals it to be an illusion, since things can pass through it.
>

<BR>

#### Prestidigitation
>
> ```badges
> items:
>   - label: Cantrip
>   - label: Transmutation
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 10 feet
> components: V, S
> duration: 1 hour
> ```
>
> You create a magical effect within range. Choose the effect from the options below. If you cast this spell multiple times, you can have up to three of its non-instantaneous effects active at a time.
>
> ##### Sensory Effect
>
> You create an instantaneous, harmless sensory effect, such as a shower of sparks, a puff of wind, faint musical notes, or an odd odor.
>
> ##### Fire Play
>
> You instantaneously light or snuff out a candle, a torch, or a small campfire.
>
> ##### Clean or Soil
>
> You instantaneously clean or soil an object no larger than 1 cubic foot.
>
> ##### Minor Sensation
>
> You chill, warm, or flavor up to 1 cubic foot of nonliving material for 1 hour.
>
> ##### Magic Mark
>
> You make a color, a small mark, or a symbol appear on an object or a surface for 1 hour.
>
> ##### Minor Creation
>
> You create a nonmagical trinket or an illusory image that can fit in your hand. It lasts until the end of your next turn. A trinket can deal no damage and has no monetary worth.
>

<BR>

#### True Strike
>
> ```badges
> items:
>   - label: Cantrip
>   - label: Divination
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: Self
> components: S, M (a weapon with which you have proficiency and that is worth 1+ CP)
> duration: Instantaneous
> ```
>
> Guided by a flash of magical insight, you make one attack with the weapon used in the spell's casting. The attack uses your spellcasting ability for the attack and damage rolls instead of using Strength or Dexterity. If the attack deals damage, it can be Radiant damage or the weapon's normal damage type (your choice).
>
> **Cantrip Upgrade.** Whether you deal Radiant damage or the weapon's normal damage type, the attack deals extra Radiant damage when you reach levels 5 (`1d6`), 11 (`2d6`), and 17 (`3d6`).
>

<BR>

#### Comprehend Languages
>
> ```badges
> items:
>   - label: Level 1
>   - label: Divination
>   - label: Ritual
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: Self
> components: V, S, M (a pinch of soot and salt)
> duration: 1 hour
> ```
>
> For the duration, you understand the literal meaning of any language that you hear or see signed. You also understand any written language that you see, but you must be touching the surface on which the words are written. It takes about 1 minute to read one page of text. This spell doesn't decode symbols or secret messages.
>

<BR>

#### Detect Magic
>
> ```badges
> items:
>   - label: Level 1
>   - label: Divination
>   - label: Ritual
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: Self
> components: V, S
> duration: Concentration, up to 10 minutes
> ```
>
> For the duration, you sense the presence of magical effects within 30 feet of yourself. If you sense such effects, you can take the [Magic](/z_Mechanics/CLI/actions.md#Magic) action to see a faint aura around any visible creature or object in the area that bears the magic, and if an effect was created by a spell, you learn the spell's "school of magic".
>
> The spell is blocked by 1 foot of stone, dirt, or wood; 1 inch of metal; or a thin sheet of lead.
>

<BR>

#### Disguise Self
>
> ```badges
> items:
>   - label: Level 1
>   - label: Illusion
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: Self
> components: V, S
> duration: 1 hour
> ```
>
> You make yourself—including your clothing, armor, weapons, and other belongings on your person—look different until the spell ends. You can seem 1 foot shorter or taller and can appear heavier or lighter. You must adopt a form that has the same basic arrangement of limbs as you have. Otherwise, the extent of the illusion is up to you.
>
> The changes wrought by this spell fail to hold up to physical inspection. For example, if you use this spell to add a hat to your outfit, objects pass through the hat, and anyone who touches it would feel nothing.
>
> To discern that you are disguised, a creature must take the [Study](/z_Mechanics/CLI/actions.md#Study) action to inspect your appearance and succeed on an Intelligence ([Investigation](/z_Mechanics/CLI/skills.md#Investigation)) check against your spell save DC.
>

<BR>

#### Find Familiar
>
> ```badges
> items:
>   - label: Level 1
>   - label: Conjuration
>   - label: Ritual
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Hour
> range: 10 feet
> components: V, S, M (burning incense worth 10+ GP, which the spell consumes)
> duration: Instantaneous
> ```
>
> You gain the service of a familiar, a spirit that takes an animal form you choose: [Bat](/z_Mechanics/CLI/bestiary/beast/bat-xmm.md), [Cat](/z_Mechanics/CLI/bestiary/beast/cat-xmm.md), [Frog](/z_Mechanics/CLI/bestiary/beast/frog-xmm.md), [Hawk](/z_Mechanics/CLI/bestiary/beast/hawk-xmm.md), [Lizard](/z_Mechanics/CLI/bestiary/beast/lizard-xmm.md), [Octopus](/z_Mechanics/CLI/bestiary/beast/octopus-xmm.md), [Owl](/z_Mechanics/CLI/bestiary/beast/owl-xmm.md), [Rat](/z_Mechanics/CLI/bestiary/beast/rat-xmm.md), [Raven](/z_Mechanics/CLI/bestiary/beast/raven-xmm.md), [Spider](/z_Mechanics/CLI/bestiary/beast/spider-xmm.md), [Weasel](/z_Mechanics/CLI/bestiary/beast/weasel-xmm.md), or another Beast that has a Challenge Rating of 0. Appearing in an unoccupied space within range, the familiar has the statistics of the chosen form, though it is a Celestial, Fey, or Fiend (your choice) instead of a Beast. Your familiar acts independently of you, but it obeys your commands.
>
> ##### Telepathic Connection
>
> While your familiar is within 100 feet of you, you can communicate with it telepathically. Additionally, as a [Bonus Action](/z_Mechanics/CLI/variant-rules/bonus-action-xphb.md), you can see through the familiar's eyes and hear what it hears until the start of your next turn, gaining the benefits of any special senses it has.
>
> Finally, when you cast a spell with a range of touch, your familiar can deliver the touch. Your familiar must be within 100 feet of you, and it must take a [Reaction](/z_Mechanics/CLI/variant-rules/reaction-xphb.md) to deliver the touch when you cast the spell.
>
> ##### Combat
>
> The familiar is an ally to you and your allies. It rolls its own [Initiative](/z_Mechanics/CLI/variant-rules/initiative-xphb.md) and acts on its own turn. A familiar can't attack, but it can take other actions as normal.
>
> ##### Disappearance of the Familiar
>
> When the familiar drops to 0 [Hit Points](/z_Mechanics/CLI/variant-rules/hit-points-xphb.md), it disappears. It reappears after you cast this spell again. As a [Magic](/z_Mechanics/CLI/actions.md#Magic) action, you can temporarily dismiss the familiar to a pocket dimension. Alternatively, you can dismiss it forever. As a [Magic](/z_Mechanics/CLI/actions.md#Magic) action while it is temporarily dismissed, you can cause it to reappear in an unoccupied space within 30 feet of you. Whenever the familiar drops to 0 [Hit Points](/z_Mechanics/CLI/variant-rules/hit-points-xphb.md) or disappears into the pocket dimension, it leaves behind in its space anything it was wearing or carrying.
>
> ##### One Familiar Only
>
> You can't have more than one familiar at a time. If you cast this spell while you have a familiar, you instead cause it to adopt a new eligible form.
>

<BR>

#### Identify
>
> ```badges
> items:
>   - label: Level 1
>   - label: Divination
>   - label: Ritual
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Minute
> range: Touch
> components: V, S, M (a pearl worth 100+ GP)
> duration: Instantaneous
> ```
>
> You touch an object throughout the spell's casting. If the object is a magic item or some other magical object, you learn its properties and how to use them, whether it requires [Attunement](/z_Mechanics/CLI/variant-rules/attunement-xphb.md), and how many charges it has, if any. You learn whether any ongoing spells are affecting the item and what they are. If the item was created by a spell, you learn that spell's name.
>
> If you instead touch a creature throughout the casting, you learn which ongoing spells, if any, are currently affecting it.
>

<BR>

#### Magic Missile
>
> ```badges
> items:
>   - label: Level 1
>   - label: Evocation
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 120 feet
> components: V, S
> duration: Instantaneous
> ```
>
> You create three glowing darts of magical force. Each dart strikes a creature of your choice that you can see within range. A dart deals `1d4 + 1` Force damage to its target. The darts all strike simultaneously, and you can direct them to hit one creature or several.
>
> **Using a Higher-Level Spell Slot.** The spell creates one more dart for each spell slot level above 1.
>

<BR>

#### Shield
>
> ```badges
> items:
>   - label: Level 1
>   - label: Abjuration
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Reaction
> range: Self
> components: V, S
> duration: 1 round
> ```
>
> An imperceptible barrier of magical force protects you. Until the start of your next turn, you have a +5 bonus to AC, including against the triggering attack, and you take no damage from [Magic Missile](/z_Mechanics/CLI/spells/magic-missile-xphb.md).
>

<BR>

#### Sleep
>
> ```badges
> items:
>   - label: Level 1
>   - label: Enchantment
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 90 feet
> components: V, S, M (a pinch of sand or rose petals)
> duration: Concentration, up to 1 minute
> ```
>
> Each creature of your choice in a 5-foot-radius Sphere centered on a point within range must succeed on a Wisdom saving throw or have the [Incapacitated](/z_Mechanics/CLI/conditions.md#Incapacitated) condition until the end of its next turn, at which point it must repeat the save. If the target fails the second save, the target has the [Unconscious](/z_Mechanics/CLI/conditions.md#Unconscious) condition for the duration. The spell ends on a target if it takes damage or someone within 5 feet of it takes an action to shake it out of the spell's effect.
>
> Creatures that don't sleep, such as elves, or that have [Immunity](/z_Mechanics/CLI/variant-rules/immunity-xphb.md) to the [Exhaustion](/z_Mechanics/CLI/conditions.md#Exhaustion) condition automatically succeed on saves against this spell.
>

<BR>

#### Unseen Servant
>
> ```badges
> items:
>   - label: Level 1
>   - label: Conjuration
>   - label: Ritual
>   - label:
>   - label: F
> ```
>
> ```spell-components
> casting_time: 1 Action
> range: 60 feet
> components: V, S, M (a bit of string and of wood)
> duration: 1 hour
> ```
>
> This spell creates an [Invisible](/z_Mechanics/CLI/conditions.md#Invisible), mindless, shapeless, Medium force that performs simple tasks at your command until the spell ends. The servant springs into existence in an unoccupied space on the ground within range. It has AC 10, 1 [Hit Point](/z_Mechanics/CLI/variant-rules/hit-points-xphb.md), and a Strength of 2, and it can't attack. If it drops to 0 [Hit Points](/z_Mechanics/CLI/variant-rules/hit-points-xphb.md), the spell ends.
>
> Once on each of your turns as a [Bonus Action](/z_Mechanics/CLI/variant-rules/bonus-action-xphb.md), you can mentally command the servant to move up to 15 feet and interact with an object. The servant can perform simple tasks that a human could do, such as fetching things, cleaning, mending, folding clothes, lighting fires, serving food, and pouring drinks. Once you give the command, the servant performs the task to the best of its ability until it completes the task, then waits for your next command.
>
> If you command the servant to perform a task that would move it more than 60 feet away from you, the spell ends.
>

<BR>

> ^spells

^spellcasting

---

## Features

<span class="right-link">[[#Character Statistics|Top]]</span>
>### Magic Initiate (Wizard) (Feat)
>
> Origin Feat You gain the following benefits. Two Cantrips. You learn two cantrips of your choice from the Wizard spell list. Intelligence, Wisdom, or Charisma is your spellcasting ability for this feat’s spells (choose when you select this feat). Level 1 Spell. Choose a level 1 spell from the same list you selected for this feat’s cantrips. You always have that spell prepared. You can cast it once without a spell slot, and you regain the ability to cast it in that way when you finish a Long Rest. You can also cast the spell using any spell slots you have. Spell Change. Whenever you gain a new level, you can replace one of the spells you chose for this feat with a different spell of the same level from the chosen spell list. Repeatable. You can take this feat more than once, but you must choose a different spell list each time.
>
>### Sage Ability Score Improvements (Feat)
>
> The Sage Background allows you to choose between Constitution, Intelligence, and Wisdom. Increase one of these scores by 2 and another one by 1, or increase all three by 1. None of these increases can raise a score above 20.
>
>### Core Wizard Traits
>
> As a Level 1 Character: Gain all the traits in the Core Wizard Traits table. Gain the Wizard’s level 1 features. Core Wizard Traits Primary Ability Intelligence Hit Point Die D6 per Wizard level Saving Throw Proficiencies Intelligence and Wisdom Skill Proficiencies Choose 2: Arcana, History, Insight, Investigation, Medicine, Nature, or Religion Weapon Proficiencies Simple weapons Armor Training None Starting Equipment Choose A or B: (A) 2 Daggers, Arcane Focus (Quarterstaff), Robe, Spellbook, Scholar’s Pack, and 5 GP; or (B) 55 GP
>
>### Spellcasting
>
> As a student of arcane magic, you have learned to cast spells. Cantrips. You know three Wizard cantrips of your choice. Whenever you finish a Long Rest, you can replace one of your cantrips from this feature with another Wizard cantrip of your choice. When you reach Wizard levels 4 and 10, you learn another Wizard cantrip of your choice, as shown in the Cantrips column of the Wizard Features table. Spellbook. Your wizardly apprenticeship culminated in the creation of a unique book: your spellbook. It is a Tiny object that weighs 3 pounds, contains 100 pages, and can be read only by you or someone casting Identify. You determine the book’s appearance and materials, such as a gilt-edged tome or a collection of vellum bound with twine. The book contains the level 1+ spells you know. It starts with six level 1 Wizard spells of your choice. Whenever you gain a Wizard level after 1, add two Wizard spells of your choice to your spellbook. Each of these spells must be of a level for which you have spell slots, as shown in the Wizard Features table. The spells are the culmination of arcane research you do regularly. Spell Slots. The Wizard Features table shows how many spell slots you have to cast your level 1+ spells. You regain all expended slots when you finish a Long Rest. Prepared Spells of Level 1+. You prepare the list of level 1+ spells that are available for you to cast with this feature. To do so, choose four spells from your spellbook. The chosen spells must be of a level for which you have spell slots. The number of spells on your list increases as you gain Wizard levels, as shown in the Prepared Spells column of the Wizard Features table. Whenever that number increases, choose additional Wizard spells until the number of spells on your list matches the number in the table. The chosen spells must be of a level for which you have spell slots. For example, if you’re a level 3 Wizard, your list of prepared spells can include six spells of levels 1 and 2 in any combination, chosen from your spellbook. If another Wizard feature gives you spells that you always have prepared, those spells don’t count against the number of spells you can prepare with this feature, but those spells otherwise count as Wizard spells for you. Changing Your Prepared Spells. Whenever you finish a Long Rest, you can change your list of prepared spells, replacing any of the spells there with spells from your spellbook. Spellcasting Ability. Intelligence is your spellcasting ability for your Wizard spells. Spellcasting Focus. You can use an Arcane Focus or your spellbook as a Spellcasting Focus for your Wizard spells. Expanding and Replacing a Spellbook The spells you add to your spellbook as you gain levels reflect your ongoing magical research, but you might find other spells during your adventures that you can add to the book. You could discover a Wizard spell on a Spell Scroll, for example, and then copy it into your spellbook. Copying a Spell into the Book. When you find a level 1+ Wizard spell, you can copy it into your spellbook if it’s of a level you can prepare and if you have time to copy it. For each level of the spell, the transcription takes 2 hours and costs 50 GP. Afterward you can prepare the spell like the other spells in your spellbook. Copying the Book. You can copy a spell from your spellbook into another book. This is like copying a new spell into your spellbook but faster, since you already know how to cast the spell. You need spend only 1 hour and 10 GP for each level of the copied spell. If you lose your spellbook, you can use the same procedure to transcribe the Wizard spells that you have prepared into a new spellbook. Filling out the remainder of the new book requires you to find new spells to do so. For this reason, many wizards keep a backup spellbook.
>
>### Ritual Adept
>
> You can cast any spell as a Ritual if that spell has the Ritual tag and the spell is in your spellbook. You needn’t have the spell prepared, but you must read from the book to cast a spell in this way.
>
>### Arcane Recovery
>
> ```consumable
> label: ""
> state_key: ilarion_veles_paul_arcane_recovery
> uses: 1
> ```
>
> You can regain some of your magical energy by studying your spellbook. When you finish a Short Rest, you can choose expended spell slots to recover. The spell slots can have a combined level equal to no more than half your Wizard level (round up), and none of the slots can be level 6 or higher. For example, if you’re a level 4 Wizard, you can recover up to two levels’ worth of spell slots, regaining either one level 2 spell slot or two level 1 spell slots. Once you use this feature, you can’t do so again until you finish a Long Rest.
>
>### Scholar
>
> *Class Feature (Level 2)*
>
> While studying magic, you also specialized in another field of study. Choose one of the following skills in which you have proficiency: Arcana, History, Investigation, Medicine, Nature, or Religion. You have Expertise in the chosen skill.
>

### Action Economy

*Note: Shows cantrips (always available), prepared spells, ritual spells (can be cast unprepared), and always-prepared spells.*

**Action:**
- Acid Splash
- Fire Bolt
- Mind Sliver
- Minor Illusion
- Prestidigitation
- True Strike
- Comprehend Languages (1st level)
- Detect Magic (1st level)
- Disguise Self (1st level)
- Identify (1st level)
- Magic Missile (1st level)
- Sleep (1st level)
- Unseen Servant (1st level)
- **Standard Actions:** Attack, Cast a Spell, Dash, Disengage, Dodge, Help, Hide, Ready, Search, Use Object

**Bonus Action:**
If cast:
- Find Familiar - Command
- Unseen Servant - Command

**Reaction:**
- Opportunity Attack
- Ready Action Trigger

> ^features

---

## Racial Traits

<span class="right-link">[[#Character Statistics|Top]]</span>
>### Elf Traits
>
>#### Darkvision
>
> You have Darkvision with a range of 60 feet.
>
> *Range: 60 feet*
>
>#### Elven Lineage
>
> You are part of a lineage that grants you supernatural abilities. Choose a lineage from the Elven Lineages table. You gain the level 1 benefit of that lineage. When you reach character levels 3 and 5, you learn a higher-level spell, as shown on the table. You always have that spell prepared. You can cast it once without a spell slot, and you regain the ability to cast it in that way when you finish a Long Rest. You can also cast the spell using any spell slots you have of the appropriate level. Intelligence, Wisdom, or Charisma is your spellcasting ability for the spells you cast with this trait (choose the ability when you select the lineage). Elven Lineages Lineage Level 1 Level 3 Level 5 Drow The range of your Darkvision increases to 120 feet. You also know the Dancing Lights cantrip. Faerie Fire Darkness High Elf You know the Prestidigitation cantrip. Whenever you finish a Long Rest, you can replace that cantrip with a different cantrip from the Wizard spell list. Detect Magic Misty Step Wood Elf Your Speed increases to 35 feet. You also know the Druidcraft cantrip. Longstrider Pass without Trace
>
> *Chosen Spells: Detect Magic, Fire Bolt*
>
>#### Fey Ancestry
>
> You have Advantage on saving throws you make to avoid or end the Charmed condition.
>
>#### Keen Senses
>
> You have proficiency in the Insight, Perception, or Survival skill.
>
>#### Trance
>
> You don’t need to sleep, and magic can’t put you to sleep. You can finish a Long Rest in 4 hours if you spend those hours in a trancelike meditation, during which you retain consciousness.
>
>#### Elven Lineage Spells
>
> When you choose your Elven Lineage, and at character levels 3 and 5, you learn a spell as shown on the table. You always have that spell prepared. You can cast it once without a spell slot, and you regain the ability to cast it in that way when you finish a Long Rest. You can also cast the spell using any spell slots you have of the appropriate level. Intelligence, Wisdom, or Charisma is your spellcasting ability for the spells you cast with this trait (choose the ability when you select the lineage).
>
> *Chosen Spells: Fire Bolt*
>
>#### Ability Score Increases
>
> When determining your character’s ability scores, increase one score by 2 and a different one by 1, or increase three scores by 1. None of these increases can raise a score above 20.
>
>#### Languages
>
> Your character knows at least three languages: Common plus two languages you roll or choose from the Standard Languages table. Knowledge of a language means your character can communicate in it, read it, and write it. Your class and other features might also give you languages. The Standard Languages table lists languages that are widespread on D&amp;D worlds. Every player character knows Common, which originated in the planar metropolis of Sigil, the hub of the multiverse. The other standard languages originated with the first members of the most prominent species in the worlds of D&amp;D and have since spread widely. Standard Languages 1d12 Language Origin &mdash; Common Sigil 1 Common Sign Language Sigil 2 Draconic Dragons 3-4 Dwarvish Dwarves 5-6 Elvish Elves 7 Giant Giants 8 Gnomish Gnomish 9 Goblin Goblinoids 10-11 Halfling Halflings 12 Orc Orcs
>
> ^racial-traits


---

## Attacks

<span class="right-link">[[#Character Statistics|Top]]</span>

>
> ### Crossbow, Light (True Strike)
> **Type:** Crossbow, Light
> **Attack Bonus:** +3
> **Damage:** 1d8 + 1 piercing
> **Range:** 80/320 ft
> **Properties:** Ammunition, Light, Loading
> **Weight:** 5.0 lbs
> 
> ### Crossbow, Light
> **Type:** Crossbow, Light
> **Attack Bonus:** +3
> **Damage:** 1d8 + 1 piercing
> **Range:** 80/320 ft
> **Properties:** Ammunition, Light, Loading
> **Weight:** 5.0 lbs
> 
> ^attacks

---

## Proficiencies

<span class="right-link">[[#Character Statistics|Top]]</span>
>### Weapons
>
> - Simple Weapons (Class: Wizard)
>
>### Tools
>
> - Calligrapher's Supplies (Background: Sage)
>
>### Languages
>
> - Common (Species: Elf)
> - Draconic (Species: Elf)
> - Elvish (Species: Elf)
>
>### Ability Score Bonuses
>
> - **Constitution** 16 (Base 14 + Feat +2 (Sage Ability Score Improvements))
> - **Intelligence** 16 (Base 15 + Feat +1 (Sage Ability Score Improvements))
>
> ^proficiencies

---

## Background

<span class="right-link">[[#Character Statistics|Top]]</span>
>### Sage
>
> **Ability Scores:** Constitution, Intelligence, Wisdom
>
> **Feat:** Magic Initiate (Wizard)
>
> **Skill Proficiencies:** Arcana and History
>
> **Tool Proficiency:** Calligrapher's Supplies
>
> **Equipment:** Choose A or B: (A) Quarterstaff, Calligrapher's Supplies, Book (history), Parchment (8 sheets), Robe, 8 GP; or (B) 50 GP
>
> You spent your formative years traveling between manors and monasteries, performing various odd jobs and services in exchange for access to their libraries. You whiled away many a long evening studying books and scrolls, learning the lore of the multiverse—even the rudiments of magic—and your mind yearns for more.
>
>### Personal Possessions
>
> The Clockwork Cipher A finely crafted, palm-sized brass puzzle box — filled with shifting, interlocking gears
>
>### Organizations
>
> The Arcanum Lyceum – A prestigious magical academy that once nurtured his early brilliance but ultimately failed to match his ambition. He left disillusioned with its rigid structure, seeing it as more concerned with control than discovery. While no longer affiliated, he still acknowledges a few minds there as worthy of respect.
>
>### Allies & Contacts
>
> Professor Virel Thand – One of the few instructors Ilarion admired. Virel encouraged independent thinking and left him with the Clockwork Cipher, a parting gift and challenge. Their relationship was based on mutual respect rather than sentiment.
>
>### Enemies
>
> None (yet)
>
>### Ideals
>
> Ambition – Knowledge defines my worth. The more I gain, the further I rise.
>
>### Bonds
>
> "A professor gave me a puzzle I still haven’t solved. I’ll unlock it one day - because I must."
>
> Item: The Clockwork Cipher A finely crafted, palm-sized brass puzzle box — filled with shifting, interlocking gears. It was a parting gift from Professor Virel Thand, one of the few instructors he respected. The professor offered no explanation, only the cryptic suggestion that he would “know its value when he deserved it.”
>
> He often idly works at it while thinking, or during conversations, much to the irritation of others.
>
>### Flaws
>
> His arrogance often blinds him to the wisdom of others.
>
> He has a hard time holding his tongue when he sees a better way to do something - even when it’s not his place.
>
>### Personality Traits
>
> “If a rule stands between me and understanding, the rule breaks.”
>
> “I have respect for those who strive to better themselves, and I’ll gladly share some of what I know if they’re willing to learn.”
>
>### Lifestyle
>
> **Lifestyle:** Aristocratic
>
> ^background

---

## Backstory

<span class="right-link">[[#Character Statistics|Top]]</span>
> From a young age, Ilarion was always a step ahead. Born into a lesser noble house in the city of Elarith, he grew up in a world where knowledge meant status. But where others saw learning as tradition, he saw it as conquest. From the start, he wasn't satisfied with understanding what was known - he was driven to uncover what was not.
>
> At the Arcanum Lyceum, Ilarion quickly made a name for himself, not just for his exceptional intellect, but for his relentless pursuit of knowledge at any cost. His brilliance was undeniable, though it often came paired with an arrogance that grated on his peers and instructors alike. He wasn’t content to simply learn what was presented to him - he questioned everything, disregarded traditional methods, and constantly pushed the boundaries of what was considered acceptable study.
>
> Ilarion often ignored the advice of his professors, seeking answers to questions that had yet to be posed in the curriculum. He’d sneak into the restricted archives, eager to dig through forbidden texts, and propose his own untested theories during lectures, frustrating those around him. He wasn’t interested in what others thought was practical or safe; he wanted to uncover the unknown, even if it meant stepping on established norms or ignoring the risks involved. As a result, his talent was both admired and feared, but the institution was quickly growing tired of his disruptive behavior.
>
> One night, he was caught sneaking into the restricted archives - again. No damage done, but it was a breach of protocol that couldn’t be ignored. Officially, he was reprimanded and placed under strict oversight. Unofficially, it was made clear: one more misstep, and he’d be out.
>
> He left before they had the chance.
>
> In his eyes, the Lyceum had become a cage - too slow, too cautious, too narrow in its thinking. He didn’t need their approval to rise. If they wouldn’t give him access to the knowledge he sought, he’d find it himself.
>
> Since then, he’s been traveling, following scattered references, cryptic symbols, forgotten journals. He’s not after truth. He’s after knowledge, insight, mastery. The kind that no one else has, because no one else is willing to reach for it the way he is.
>
> Saltmarsh is just the next step. A place on the edge of civilization, where rumors and relics go unnoticed. He doesn’t care about the town. He cares about what secrets might be buried there.
>
> 
> ^backstory

---

## Inventory

<span class="right-link">[[#Character Statistics|Top]]</span>
> **Wealth:** 32 gp, 12 sp *(Total: 33 gp)*
> **Encumbrance:** 72.9/135 lbs (53% - Medium)
>
>
>### Currently Equipped
>
> - **Bag of Holding** (Uncommon) - Wondrous item
> - **Crossbow, Light (True Strike)** - Crossbow, Light
> - **Crossbow, Light** - Crossbow, Light
> - **Backpack** - Gear
> - **Bolts** - Gear
>
>### Magic Items & Containers
>
> **Bag of Holding** [Uncommon] (equipped) - 5.0 lbs
> *Wondrous item*
>
> **Potion of Water Breathing** [Uncommon]
> *Potion*
>
> **Potion of Water Breathing** [Uncommon]
> *Potion*
>
>### Weapons & Armor
>
> - Crossbow, Light (equipped)
> - Crossbow, Light (True Strike) (equipped)
> - Dagger × 2
> - Quarterstaff
>
>### Other Equipment
>
> - Backpack
> - Bolts × 10
> - Book × 2
> - Calligrapher's Supplies
> - Ink
> - Ink Pen
> - Lamp
> - Oil × 10
> - Parchment × 18
> - Robe
> - Tinderbox
>
> ^inventory