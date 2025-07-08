---
tags:
  - "#SessionNote"
whichparty: "[[Party 1]]"
sessiondate: 20/05/2025
locations:
  - "[[Campaign/Points of Interest/Haunted Mansion.md|Haunted Mansion]]"
characters:
  - "[[Tirm Harad]]"
  - "[[Sanbalet]]"
  - "[[Ned]]"
quests:
  - "[[Clear Tirm's haunted house]]"
organizations:
  - "[[Smuggling ring]]"
items:
  - item: Gold coins
    holder: Party
    qty: 47
    id: item_1750196086140_2ya9g59z5
  - item: Silver coins
    holder: Party
    qty: 0
    id: item_1750196086140_1bh6blbf8
  - item: Copper coins
    holder: Party
    qty: 0
    id: item_1750196086140_5uwvqlkmm
  - item: Spell book with charm person, colour spray, magic missile, silent image, magic mouth, scorching ray
    holder: "[[Ilarion Veles|Ilarion Veles]]"
    qty: 1
    value: 0gp
    claimed: no
    id: item_1750196086140_zzxpa4ab4
  - item: Spell book with dancing lights, comprehend languages, tensors floating disc, shatter
    holder: "[[Ilarion Veles|Ilarion Veles]]"
    qty: 1
    value: 0gp
    claimed: no
    id: item_1750196086140_fxb8r9yfa
  - item: Book that alchemist was reading has a title of "Ye secret of ye philosophers stone", gold lettering, written in common, most of it is incomprehensible, if studied for hours might be able to get more out of it. It does describe about how to turn base metal in to gold.
    holder: "[[Ilarion Veles|Ilarion Veles]]"
    qty: 1
    value: 50gp
    claimed: no
    id: item_1750196086140_dciqybrfy
  - item: Golden human skull
    holder: "[[Ilarion Veles|Ilarion Veles]]"
    qty: 1
    value: 20gp
    claimed: no
    id: item_1750196086140_u9xlkwls4
  - item: Golden apple
    holder: "[[Ilarion Veles|Ilarion Veles]]"
    qty: 1
    value: 5gp
    claimed: no
    id: item_1750196086140_1qjcpu2hb
  - item: Golden small balance weight discs
    holder: "[[Ilarion Veles|Ilarion Veles]]"
    qty: 5
    value: 5gp
    claimed: no
    id: item_1750196086140_qiszjomer
  - item: Chemical apparatus
    holder: "[[Campaign/Parties/Characters/Party 1/Dirk.md|Dirk]]"
    qty: 1
    value: 20gp
    claimed: no
    id: item_1750196086140_wc1gdl7ly
  - item: Book about potions and alchemic preparations
    holder: "[[Ilarion Veles|Ilarion Veles]]"
    qty: 1
    value: 0gp
    claimed: no
    id: item_1750196086140_znabqth19
  - item: Recipe book 1
    holder: "[[Campaign/Parties/Characters/Party 1/Beron Voss.md|Beron Voss]]"
    qty: 1
    value: 0gp
    claimed: yes
    id: item_1750196086140_w1e2qnxm3
  - item: Recipe book 2
    holder: "[[Campaign/Parties/Characters/Party 1/Dirk.md|Dirk]]"
    qty: 1
    value: 0gp
    claimed: no
    id: item_1750196086140_q7upl2z3k
gold_delta: 0
silver_delta: 0
copper_delta: 0
item_name: 
item_holder: 
item_qty: 1
item_value: 
item_value_currency: gp
quicknote: |-
  The party stood back from the trapdoor... and conferred, what was their next move? They struggled to get a resolution with Sanablat that they could agree on—some wanted to deal, some didn’t... the scout was left tied and gagged, to team up or take them out?

  A decision and idea was eventually reached... the plan started with Charm Person being successfully cast on Sanablat, then they descended back into the hidden cellar. They pretended that they wanted a deal on killing the undead. They negotiated to enter the cellar again, this time without a potential fight... but everything unravelled when someone decided to open the door to the undead... and push Sanablat inside... he died... horribly!

  The compatriots of Sanablat fled, with the exception of the spokesman "Ned," who was tied and gagged... and oddly "covered in oil" by Vaelith.

  ...........................

  With the room clear, they then set about a plan to destroy the undead. Positioned, they opened the door and the fight began... The skeletons moved slowly at first but with evil purpose, closing rapidly and striking out with swords and claws... The fight seemed to be turning for the party when, through the now open doorway, the skeletal figure of the long dead Alchemist, a whispy beard and robes around him... he started throwing balls of acid, injuring Mercy.

  ...........................

  The party set to work, eventually overcoming them. Piles of bones lay shattered on the floor, and through the door in the room beyond were the remains of the now dead Sanablat, thrown against the wall by magic from the party... Vaelith and Thuldus remained in the cellar, watching the secret door and Ned; the rest went in to examine the alchemist’s tomb.

  They found books on magic and golden items... also a lost recipe book...

  Meanwhile, Thuldus and Vaelith heard first noises... then doors burst open and smugglers rushed into the room from the secret door they knew... and another by the cooker, and down from above... Hobgoblins laughed and demanded their surrender... they chose to fight!!
item_claimed: no
aliases:
  - Into the fire
---
> [!metadata|metadata]- Metadata 
>> [!metadata|metadataoption]- System
>> #### System
>> |  |  |
>> | --- | --- |
>> | **Tags** | `INPUT[Tags][inlineListSuggester:tags]` |
>
>> [!metadata|metadataoption]- Info
>> #### Info
>> |  |  |
>> | --- | --- |
>> | **Aliases** | `INPUT[list:aliases]` |
>> | **Which Party** | `INPUT[Null][suggester(optionQuery(#Party AND !"z_Templates"), useLinks(partial)):whichparty]` |
>> | **Session Date** | `INPUT[datePicker:sessiondate]` |
>> | **Quick Notes** |  `INPUT[textArea:quicknote]` |
>
>> [!metadata|metadataoption]- Quick References
>> #### Quick References
>> |  |  |
>> | --- | --- |
>> | **Character** | `INPUT[inlineListSuggester(optionQuery(#Character AND !"z_Templates"), useLinks(partial)):characters]` |
>> | **Locations** | `INPUT[inlineListSuggester(optionQuery(#Location AND !"z_Templates")):locations]` |
>> | **Quests** | `INPUT[inlineListSuggester(optionQuery(#Quest AND !"z_Templates"), useLinks(partial)):quests]` |
>> | **Rumours** | `INPUT[inlineListSuggester(optionQuery(#Rumour AND !"z_Templates"), useLinks(partial)):rumours]` |
>> | **Organizations** | `INPUT[inlineListSuggester(optionQuery(#Organization AND !"z_Templates"), useLinks(partial)):organizations]` |
>> | **Miscellaneous** | `INPUT[inlineListSuggester(optionQuery("" AND !"z_Templates")):misc]` |

# `INPUT[toggle(class(star)):starred]` **  `=link(this.whichparty)`** - `=this.sessiondate`** - `=this.file.name`** - `=this.file.aliases`

### Quick References

> [!column|3 no-title]
>> [!metadata|characters] People
>> `VIEW[{characters}][link]`
>
>> [!metadata|location] Locations
>> `VIEW[{locations}][link]`
>
>> [!metadata|misc] Misc
>> `VIEW[{misc}][link]`

> [!column|3 no-title]
>> [!metadata|quests] Quests
>> `VIEW[{quests}][link]`
>
>> [!metadata|rumours] Rumours
>> `VIEW[{rumours}][link]`
>
>> [!metadata|organizations] Organizations
>> `VIEW[{organizations}][link]`

<BR><BR>
### Session overview

> [!kirk|info] What happened?
- [[Ned]] has a deal of some sorts with [[Sanbalet]].
- [[Vaelith Duskthorn orig||Vaelith]] has an oil fetish

Initiative for latest combat:

Baldrin - 19
Vaelith - 18
Thuldus - 18
Friedrich - 17
Other enemies
Beron - 17
Ilarion - 7
Dirk - 5
Hobgoblins
Mercy - 4
Bandits


![[Pasted image 20250521120336.png]]






<BR>

### Items gathered

> [!metadata|misc] Item scratch pad
> - [[Ilarion Veles|Ilarion]] - Spell book with charm person, colour spray, magic missile, silent image, magic mouth, scorching ray
> - [[Ilarion Veles|Ilarion]] - Spell book with dancing lights, comprehend languages, tensors floating disc, shatter
> - [[Ilarion Veles|Ilarion]] - Book that alchemist was reading has a title of "Ye secret of ye philosophers stone", gold lettering - 50gp, written in common, most in it is incomprehensible, if studied for hours might be able to get more out of it.  It does describe about how to turn base metal in to gold.  
> - Objects made of pure gold 
> 	- Golden human skull 20gp
> 	- Golden apple 5 gp
> 	- Golden rose 5
> 	- Golden set of 5 small balance weight discs, 5gp each
> 	- Golden stack of gold coins 47gp
> - [[Dirk]] - Chemical apparatus worth 20gp
> - [[Ilarion Veles|Ilarion]] - Book about potions and alchemic preparations, 
> - 2 x recipe book (one taken by [[Beron Voss|Beron]], one taken by [[Dirk]]) 

<BR>


```meta-bind-button
label: "Add Item"
style: primary
id: add-item
hidden: true
actions:
  - type: updateMetadata
    bindTarget: items
    evaluate: true
    value: >
      x.concat([{
        item: getMetadata("item_name"),
        holder: getMetadata("item_holder"),
        qty: getMetadata("item_qty"),
        value: getMetadata("item_value") + getMetadata("item_value_currency"),
        claimed: getMetadata("item_claimed")
      }])
  - type: updateMetadata
    bindTarget: item_name
    evaluate: false
    value: null
  - type: updateMetadata
    bindTarget: item_holder
    evaluate: false
    value: null
  - type: updateMetadata
    bindTarget: item_qty
    evaluate: false
    value: 1
  - type: updateMetadata
    bindTarget: item_value
    evaluate: false
    value: null
  - type: updateMetadata
    bindTarget: item_value_currency
    evaluate: false
    value: "gp"
  - type: updateMetadata
    bindTarget: item_claimed
    evaluate: false
    value: "no"

```

### Item Tracker
> [!section]+ Add items
> | Field         | Input |
> |---------------|-------|
> | Item Name     | `INPUT[text(class(input-w-100), placeholder(Item name)):item_name]` |
> | Item Holder   | `INPUT[suggester(optionQuery("Campaign/Parties/Characters/Party 1")):item_holder]` |
> | Item quantity | `INPUT[number(class(input-w-10), placeholder(1)):item_qty]` |
> | Item value    | `INPUT[number(class(input-w-10), placeholder(Amount)):item_value]` `INPUT[inlineSelect(option(gp, gold), option(sp, silver), option(cp, copper)):item_value_currency]` |
>| Claimed | `INPUT[inlineSelect(option(no, No), option(yes, Yes)):item_claimed]` |
> |               | `BUTTON[add-item]` |


> [!section]+ Session items

~~~dataviewjs
const page = dv.current();
const currentFile = app.vault.getAbstractFileByPath(page.file.path);

// ============= UTILITY FUNCTIONS =============

/**
 * Generates a unique ID for an item
 */
function generateItemId() {
    return `item_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Ensures all items have unique IDs, adding them if missing
 */
async function ensureItemIds() {
    await app.fileManager.processFrontMatter(currentFile, (fm) => {
        if (!Array.isArray(fm.items)) return;
        
        let needsUpdate = false;
        for (let i = 0; i < fm.items.length; i++) {
            if (!fm.items[i].id) {
                fm.items[i].id = generateItemId();
                needsUpdate = true;
            }
        }
        
        if (needsUpdate) {
            new Notice("Added IDs to items without them");
        }
    });
}

/**
 * Claims an item by updating its frontmatter status
 */
async function handleClaim(row) {
    await app.fileManager.processFrontMatter(currentFile, (fm) => {
        if (!Array.isArray(fm.items)) return;
        
        for (let i = 0; i < fm.items.length; i++) {
            const item = fm.items[i];
            if (item.id === row.itemId && item.claimed !== "yes") {
                fm.items[i].claimed = "yes";
                new Notice(`Claimed: ${item.item}`);
                break;
            }
        }
    });
}

/**
 * Gets the display name for a file (alias or filename)
 */
function getDisplayNameForFile(file) {
    if (!file) return "";
    
    const metadata = app.metadataCache.getFileCache(file);
    const frontmatter = metadata?.frontmatter;
    
    if (frontmatter?.aliases) {
        return Array.isArray(frontmatter.aliases) 
            ? frontmatter.aliases[0] 
            : frontmatter.aliases;
    }
    
    return file.name.replace(/\.md$/, "");
}

/**
 * Formats gold values (whole numbers without decimals)
 */
function formatGold(gpValue) {
    return Number(gpValue) % 1 === 0 
        ? Number(gpValue).toFixed(0) 
        : Number(gpValue).toFixed(2);
}

/**
 * Processes holder information and returns display format
 */
function processHolder(holder) {
    if (!holder) return { display: "", text: "" };
    
    // Handle Dataview link objects
    if (typeof holder === "object" && holder.path) {
        const file = app.metadataCache.getFirstLinkpathDest(holder.path, "");
        const displayName = file ? getDisplayNameForFile(file) : holder.path.replace(/\.md$/, "");
        return {
            display: `[[${holder.path}|${displayName}]]`,
            text: holder.path.replace(/\.md$/, "")
        };
    }
    
    // Handle string holders
    if (typeof holder === "string") {
        // Already a wikilink
        if (holder.startsWith("[[")) {
            return {
                display: holder,
                text: holder.replace(/^\[\[(.+?)(\|.+?)?\]\]$/, "$1")
            };
        }
        
        // Try to resolve as file path
        const file = app.metadataCache.getFirstLinkpathDest(holder, "");
        if (file) {
            const displayName = getDisplayNameForFile(file);
            return {
                display: `[[${file.path}|${displayName}]]`,
                text: file.path.replace(/\.md$/, "")
            };
        }
        
        // Plain string
        return {
            display: holder.replace(/\.md$/, ""),
            text: holder.replace(/\.md$/, "")
        };
    }
    
    return { display: "", text: "" };
}

/**
 * Parses currency values and converts to gold pieces
 */
function parseValue(valueStr) {
    const valRaw = String(valueStr).trim().toLowerCase();
    let val = 0;
    
    if (valRaw.endsWith("gp")) {
        val = parseFloat(valRaw.replace("gp", ""));
    } else if (valRaw.endsWith("sp")) {
        val = parseFloat(valRaw.replace("sp", "")) / 10;
    } else if (valRaw.endsWith("cp")) {
        val = parseFloat(valRaw.replace("cp", "")) / 100;
    } else {
        val = parseFloat(valRaw);
    }
    
    return isNaN(val) ? 0 : val;
}

/**
 * Creates a claim button for unclaimed items
 */
function createClaimButton(item) {
    const button = dv.el('button', 'Claim');
    button.onclick = () => handleClaim(item);
    return button;
}

// ============= MAIN PROCESSING =============

// Ensure all items have IDs
await ensureItemIds();

const allItems = [];

// Process each item from the page
for (const entry of (page.items ?? [])) {
    // Skip coins and empty items
    if (!entry.item || entry.item.toLowerCase().includes("coin")) {
        continue;
    }
    
    const holder = processHolder(entry.holder);
    const qty = Number(entry.qty) || 0;
    const value = parseValue(entry.value);
    const totalValue = qty * value;
    
    // Format display value
    let displayValue = String(entry.value || "0");
    if (!displayValue.match(/(gp|sp|cp)$/i)) {
        displayValue += "gp";
    }
    
    allItems.push({
        itemId: entry.id, // Use the item's unique ID
        item: entry.item,
        holder: entry.holder, // Keep original holder for matching
        qty: entry.qty,
        value: entry.value,
        holderDisplay: holder.display,
        holderText: holder.text,
        qtyNum: qty,
        valRaw: displayValue,
        totalVal: formatGold(totalValue),
        claimed: entry.claimed
    });
}

// Sort by holder, then by item name
allItems.sort((a, b) => {
    const holderA = (a.holderText || "").toLowerCase();
    const holderB = (b.holderText || "").toLowerCase();
    
    if (holderA === holderB) {
        return (a.item || "").localeCompare(b.item || "");
    }
    
    return holderA.localeCompare(holderB);
});

// ============= TABLE GENERATION =============

const tableRows = allItems.map(item => [
    item.item,
    item.holderDisplay,
    item.qty,
    item.valRaw,
    item.totalVal,
    item.claimed === "yes" ? "✅" : "❌",
    item.claimed !== "yes" ? createClaimButton(item) : ""
]);

// ============= DISPLAY =============

if (tableRows.length === 0) {
    dv.paragraph("📦 No loot found for this session.");
} else {
    dv.table(
        ["Item", "Holder", "Qty", "Value", "Total (gp)", "Claimed", "Action"], 
        tableRows
    );
}
~~~

<BR>

```meta-bind-button
label: "➕"
style: destructive
class: coin-button-plus
hidden: true
id: "add-gold"
actions:
  - type: updateMetadata
    bindTarget: items[0].qty
    evaluate: true
    value: "x + getMetadata('gold_delta')"
  - type: updateMetadata
    bindTarget: gold_delta
    evaluate: false
    value: 0
```

```meta-bind-button
label: "➖"
style: destructive
class: coin-button
hidden: true
id: "subtract-gold"
actions:
  - type: updateMetadata
    bindTarget: items[0].qty
    evaluate: true
    value: "x - getMetadata('gold_delta')"
  - type: updateMetadata
    bindTarget: gold_delta
    evaluate: false
    value: 0
```

```meta-bind-button
label: "➕"
style: destructive
class: coin-button-plus
hidden: true
id: "add-silver"
actions:
  - type: updateMetadata
    bindTarget: items[1].qty
    evaluate: true
    value: "x + getMetadata('silver_delta')"
  - type: updateMetadata
    bindTarget: silver_delta
    evaluate: false
    value: 0
```

```meta-bind-button
label: "➖"
style: destructive
class: coin-button
hidden: true
id: "subtract-silver"
actions:
  - type: updateMetadata
    bindTarget: items[1].qty
    evaluate: true
    value: "x - getMetadata('silver_delta')"
  - type: updateMetadata
    bindTarget: silver_delta
    evaluate: false
    value: 0
```

```meta-bind-button
label: "➕"
style: destructive
class: coin-button-plus
hidden: true
id: "add-copper"
actions:
  - type: updateMetadata
    bindTarget: items[2].qty
    evaluate: true
    value: "x + getMetadata('copper_delta')"
  - type: updateMetadata
    bindTarget: copper_delta
    evaluate: false
    value: 0
```

```meta-bind-button
label: "➖"
style: destructive
class: coin-button
hidden: true
id: "subtract-copper"
actions:
  - type: updateMetadata
    bindTarget: items[2].qty
    evaluate: true
    value: "x - getMetadata('copper_delta')"
  - type: updateMetadata
    bindTarget: copper_delta
    evaluate: false
    value: 0
```

<BR>

### 💰 Coin Tracker
> [!section]+ Session Totals
> 
> | 🪙 Gold - `VIEW[{items[0].qty}][text]` | 🥈 Silver - `VIEW[{items[1].qty}][text]` | 🥉 Copper - `VIEW[{items[2].qty}][text]` |
> |--------|-----------|-----------|
> | `INPUT[number(class(input-w-15)):gold_delta]` `BUTTON[add-gold]` `BUTTON[subtract-gold]`| `INPUT[number(class(input-w-15)):silver_delta]` `BUTTON[add-silver]` `BUTTON[subtract-silver]`| `INPUT[number(class(input-w-15)):copper_delta]` `BUTTON[add-copper]` `BUTTON[subtract-copper]`|

> [!section]+ Overall
> 
> ```dataviewjs
> let pages = dv.pages('"Campaign"')
>     .where(p => p.tags && (p.tags.includes("SessionNote") || p.tags.includes("#SessionNote")) && p.items);
> 
> let allItems = [];
> for (let page of pages) {
>   if (Array.isArray(page.items)) allItems.push(...page.items);
> }
> 
> let coins = [
>     { name: "Gold coins", value: 1 },
>     { name: "Silver coins", value: 0.1 },
>     { name: "Copper coins", value: 0.01 }
> ];
> 
> let coinTotals = coins.map(coin => {
>     let entries = allItems.filter(i => (i.item || "").toLowerCase().trim() === coin.name.toLowerCase());
>     let totalQty = entries.reduce((sum, i) => sum + (Number(i.qty) || 0), 0);
>     let totalVal = totalQty * coin.value;
>     // Gold: no decimals, Silver/Copper: two decimals
>     let valStr = coin.value === 1
>         ? totalVal.toFixed(0)
>         : totalVal.toFixed(2);
>     return { ...coin, totalQty, valStr };
> });
> 
> dv.table(
>     ["Coin", "Total Qty", "Value (gp)"],
>     coinTotals.map(c => [c.name, c.totalQty, c.valStr])
> );
> 
> let totalValue = coinTotals.reduce((sum, c) => sum + (c.totalQty * c.value), 0);
> dv.paragraph(`**Total Value (gp): ${totalValue.toFixed(2)}**`);
> ```


<BR><BR>
### Resume
 `=this.quicknote`
 
<BR><BR>
### End of Session Notes
