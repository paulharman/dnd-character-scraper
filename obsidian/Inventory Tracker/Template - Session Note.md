---
tags:
  - "#SessionNote"
items:
  - item: Gold coins
    holder: Party
    qty: 0
    id: item_1750197304214_xvo61o1io
  - item: Silver coins
    holder: Party
    qty: 0
    id: item_1750197304214_g3554bet1
  - item: Copper coins
    holder: Party
    qty: 0
    id: item_1750197304214_pr4bn117n
gold_delta: 0
silver_delta: 0
copper_delta: 0
item_name: 
item_holder: 
item_qty: 1
item_value: 
item_value_currency: gp
task_list: []
item_claimed: no
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

---

### Session overview

> [!section]+ What happened?
> `INPUT[list(placeholder(Add a session event)):session_events]`

<BR>

> [!section]+ Quick notes
> `INPUT[textArea(placeholder(Add quick notes)):session_quicknote]`


<BR>

> [!section]+ Rule queries
> `INPUT[list(placeholder(Add a rule query)):session_rule_queries]`

---

### Items gathered
> [!section]+ Item scratch pad
> `INPUT[list(placeholder(Add an item)):session_item_scratch]`


<BR>


~~~meta-bind-button
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

~~~

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

### Item Tracker
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

~~~meta-bind-button
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
~~~

~~~meta-bind-button
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
~~~

~~~meta-bind-button
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
~~~

~~~meta-bind-button
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
~~~

~~~meta-bind-button
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
~~~

~~~meta-bind-button
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
~~~

---

### 💰 Coin Tracker
> [!section]+ Session Totals
> 
> | 🪙 Gold - `VIEW[{items[0].qty}][text]` | 🥈 Silver - `VIEW[{items[1].qty}][text]` | 🥉 Copper - `VIEW[{items[2].qty}][text]` |
> |--------|-----------|-----------|
> | `INPUT[number(class(input-w-15)):gold_delta]` `BUTTON[add-gold]` `BUTTON[subtract-gold]`| `INPUT[number(class(input-w-15)):silver_delta]` `BUTTON[add-silver]` `BUTTON[subtract-silver]`| `INPUT[number(class(input-w-15)):copper_delta]` `BUTTON[add-copper]` `BUTTON[subtract-copper]`|

> [!section]+ Overall
> 
~~~dataviewjs
let pages = dv.pages('"Campaign"')
    .where(p => p.tags && (p.tags.includes("SessionNote") || p.tags.includes("#SessionNote")) && p.items);

let allItems = [];
for (let page of pages) {
  if (Array.isArray(page.items)) allItems.push(...page.items);
}

let coins = [
    { name: "Gold coins", value: 1 },
    { name: "Silver coins", value: 0.1 },
    { name: "Copper coins", value: 0.01 }
];

let coinTotals = coins.map(coin => {
    let entries = allItems.filter(i => (i.item || "").toLowerCase().trim() === coin.name.toLowerCase());
    let totalQty = entries.reduce((sum, i) => sum + (Number(i.qty) || 0), 0);
    let totalVal = totalQty * coin.value;
    // Gold: no decimals, Silver/Copper: two decimals
    let valStr = coin.value === 1
        ? totalVal.toFixed(0)
        : totalVal.toFixed(2);
    return { ...coin, totalQty, valStr };
});

dv.table(
    ["Coin", "Total Qty", "Value (gp)"],
    coinTotals.map(c => [c.name, c.totalQty, c.valStr])
);

let totalValue = coinTotals.reduce((sum, c) => sum + (c.totalQty * c.value), 0);
dv.paragraph(`**Total Value (gp): ${totalValue.toFixed(2)}**`);
~~~

---

### Resume
 `=this.quicknote`
 