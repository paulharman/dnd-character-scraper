---
tags:
  - "#Hub"
obsidianUIMode: preview
obsidianEditingMode: source
cssclasses:
  - linewidth1500
searchterm1: ""
searchterm2: ""
searchterm3: ""
searchterm4: ""
searchterm5: ""
searchterm6: ""
searchterm7: ""
item_claimed: yes
search:
  holder: 
  item: 
  session: 
  item_claimed: all
  sortby: holder
  sortby2: total
search_item: 
search_session: 
search_holder: 
search_item_claimed: 
---

### Party Master Inventory

<BR>

> [!section]+ Party Items


~~~meta-bind-button
label: "Reset Filter"
style: primary
id: reset-filter
hidden: false
actions:
  - type: updateMetadata
    bindTarget: search.item
    evaluate: false
    value: null
  - type: updateMetadata
    bindTarget: search.session
    evaluate: false
    value: null
  - type: updateMetadata
    bindTarget: search.holder
    evaluate: false
    value: null
  - type: updateMetadata
    bindTarget: search.item_claimed
    evaluate: false
    value: all
~~~

> Filters `INPUT[text(class(input-w-20), placeholder(Item)):search.item]` `INPUT[text(class(input-w-12), placeholder(Session)):search.session]` `INPUT[text(class(input-w-20), placeholder(Holder)):search.holder]` `INPUT[inlineSelect(option(all, ---), option(no, No), option(yes, Yes)):search.item_claimed]`
> Sort order: `INPUT[inlineSelect(option(none, ---), option(item, Item), option(session, Session), option(holder, Holder), option(qty, Qty), option(value, Value), option(total, Total Value), option(claimed, Claimed)):search.sortby]`  
> Secondary sort order: `INPUT[inlineSelect(option(none, ---), option(item, Item), option(session, Session), option(holder, Holder), option(qty, Qty), option(value, Value), option(total, Total Value), option(claimed, Claimed)):search.sortby2]`

~~~dataviewjs
// ============= CONFIGURATION =============
const CURRENCY_CONVERSION = {
    gp: 1,
    sp: 0.1,
    cp: 0.01
};

// ============= UTILITY FUNCTIONS =============

/**
 * Gets the display name for a file (alias or filename)
 */
function getDisplayNameForFile(file) {
    if (!file?.name) return "";
    
    const metadata = app.metadataCache.getFileCache(file);
    const aliases = metadata?.frontmatter?.aliases;
    
    if (aliases) {
        return Array.isArray(aliases) ? aliases[0] : aliases;
    }
    
    return file.name.replace(/\.md$/, "");
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
 * Formats gold values (whole numbers without decimals)
 */
function formatGold(gpValue) {
    return Number(gpValue) % 1 === 0 
        ? Number(gpValue).toFixed(0) 
        : Number(gpValue).toFixed(2);
}

/**
 * Parses currency values and converts to gold pieces
 */
function parseValue(valueStr) {
    const valRaw = String(valueStr).trim().toLowerCase();
    
    for (const [currency, rate] of Object.entries(CURRENCY_CONVERSION)) {
        if (valRaw.endsWith(currency)) {
            const value = parseFloat(valRaw.replace(currency, ""));
            return isNaN(value) ? 0 : value * rate;
        }
    }
    
    // Default to gold if no currency specified
    const value = parseFloat(valRaw);
    return isNaN(value) ? 0 : value;
}

/**
 * Formats display value with currency suffix
 */
function formatDisplayValue(valueStr) {
    const val = String(valueStr || "0");
    return val.match(/(gp|sp|cp)$/i) ? val : val + "gp";
}

/**
 * Parse DD/MM/YYYY date format for sorting
 */
function parseDate(dateStr) {
    if (!dateStr) return "";
    if (dateStr instanceof Date) return dateStr.toISOString();
    
    const [day, month, year] = dateStr.split("/");
    return `${year}-${month.padStart(2, '0')}-${day.padStart(2, '0')}`;
}

/**
 * Gets holder name for sorting (with alias resolution)
 */
function getHolderSortName(holder) {
    if (!holder) return "";
    
    if (typeof holder === "object" && holder.path) {
        const file = app.vault.getAbstractFileByPath(holder.path);
        const displayName = file ? getDisplayNameForFile(file) : holder.path;
        return displayName.toString();
    }
    
    if (typeof holder === "string" && holder.startsWith("[[")) {
        const match = holder.match(/^\[\[(.+?)(?:\|(.+?))?\]\]$/);
        if (match) {
            const linkTarget = match[1];
            const file = app.metadataCache.getFirstLinkpathDest(linkTarget, "");
            return file ? getDisplayNameForFile(file) : linkTarget;
        }
    }
    
    return String(holder);
}

/**
 * Claims an item by updating its frontmatter status using the item's unique ID
 */
async function handleClaim(row) {
    try {
        const targetFile = app.vault.getAbstractFileByPath(row.filePath);
        if (!targetFile) {
            new Notice(`Could not find file: ${row.filePath}`);
            return;
        }
        
        await app.fileManager.processFrontMatter(targetFile, (frontmatter) => {
            if (!Array.isArray(frontmatter.items)) {
                new Notice("No items array found in frontmatter");
                return;
            }
            
            let itemFound = false;
            
            for (let i = 0; i < frontmatter.items.length; i++) {
                const item = frontmatter.items[i];
                
                // Match by unique ID
                if (item.id === row.itemId && item.claimed !== "yes") {
                    frontmatter.items[i].claimed = "yes";
                    itemFound = true;
                    new Notice(`Claimed: ${item.item}`);
                    break;
                }
            }
            
            if (!itemFound) {
                new Notice(`Could not find item with ID: ${row.itemId}`);
            }
        });
    } catch (error) {
        new Notice(`Error claiming item: ${error.message}`);
    }
}

/**
 * Creates a claim button for unclaimed items
 */
function createClaimButton(item) {
    const button = dv.el('button', 'Claim');
    button.onclick = () => handleClaim(item);
    return button;
}

// ============= DATA COLLECTION =============

const sessionPages = dv.pages(" ")
    .where(p =>
        Array.isArray(p.tags) &&
        (p.tags.includes("SessionNote") || p.tags.includes("#SessionNote")) &&
        Array.isArray(p.items)
    );

const allItems = [];

for (const page of sessionPages) {
    for (let index = 0; index < page.items.length; index++) {
        const entry = page.items[index];
        
        // Skip coins and empty items
        if (!entry.item || entry.item.toLowerCase().includes("coin")) {
            continue;
        }

        // Skip items without IDs (they need to be processed by the session first)
        if (!entry.id) {
            continue;
        }

        const holderInfo = processHolder(entry.holder);
        const qty = Number(entry.qty) || 0;
        const value = parseValue(entry.value);
        const totalValue = qty * value;

        allItems.push({
            filePath: page.file.path,
            itemId: entry.id, // Use the item's existing unique ID
            item: entry.item,
            originalHolder: entry.holder, // Keep original for display
            qty: entry.qty,
            value: entry.value,
            session: page.file.link,
            holderDisplay: holderInfo.display,
            holderText: holderInfo.text,
            qtyNum: qty,
            valRaw: formatDisplayValue(entry.value),
            totalVal: formatGold(totalValue),
            claimed: entry.claimed,
            sessiondate: page.sessiondate
        });
    }
}

// ============= FILTERING =============

const searchParams = dv.current().search || {};
const filters = {
    item: (searchParams.item || "").toLowerCase().trim(),
    session: (searchParams.session || "").toLowerCase().trim(),
    holder: (searchParams.holder || "").toLowerCase().trim(),
    claimed: (searchParams.item_claimed || "all").toLowerCase()
};

const filteredItems = allItems.filter(item => {
    return (
        (!filters.item || (item.item || "").toLowerCase().includes(filters.item)) &&
        (!filters.session || (item.session?.path || item.session?.toString() || "").toLowerCase().includes(filters.session)) &&
        (!filters.holder || (item.holderText || "").toLowerCase().includes(filters.holder)) &&
        (filters.claimed === "all" || String(item.claimed).toLowerCase() === filters.claimed)
    );
});

// ============= SORTING =============

const sortBy = (searchParams.sortby || "none").toLowerCase();
const sortBy2 = (searchParams.sortby2 || "none").toLowerCase();

const sortFunctions = {
    qty: (a, b) => a.qtyNum - b.qtyNum,
    value: (a, b) => parseFloat(a.valRaw) - parseFloat(b.valRaw),
    total: (a, b) => Number(a.totalVal) - Number(b.totalVal),
    claimed: (a, b) => String(a.claimed).localeCompare(String(b.claimed)),
    item: (a, b) => (a.item || "").localeCompare(b.item || ""),
    session: (a, b) => parseDate(a.sessiondate).localeCompare(parseDate(b.sessiondate)),
    holder: (a, b) => {
        const holderA = getHolderSortName(a.originalHolder).toLowerCase();
        const holderB = getHolderSortName(b.originalHolder).toLowerCase();
        return holderA.localeCompare(holderB, undefined, { sensitivity: "base" });
    }
};

if (sortBy !== "none" && sortBy !== "---" || sortBy2 !== "none" && sortBy2 !== "---") {
    filteredItems.sort((a, b) => {
        if (sortBy !== "none" && sortBy !== "---" && sortFunctions[sortBy]) {
            const primary = sortFunctions[sortBy](a, b);
            if (primary !== 0) return primary;
        }
        
        if (sortBy2 !== "none" && sortBy2 !== "---" && sortFunctions[sortBy2]) {
            return sortFunctions[sortBy2](a, b);
        }
        
        return 0;
    });
}

// ============= TABLE GENERATION =============

// Generate table rows
const tableRows = filteredItems.map(item => [
    item.item,
    item.session,
    item.holderDisplay,
    item.qty,
    item.valRaw,
    item.totalVal,
    item.claimed === "yes" ? "✅" : "❌",
    item.claimed !== "yes" ? createClaimButton(item) : ""
]);

// Calculate and add totals
const grandTotal = filteredItems.reduce((sum, item) => sum + Number(item.totalVal || 0), 0);

tableRows.push(
    ["&nbsp;", "&nbsp;", "&nbsp;", "&nbsp;", "&nbsp;", "&nbsp;", "&nbsp;", ""],
    ["", "", "", "", "", "**Total:**", `**${formatGold(grandTotal)}**`, ""]
);

// ============= DISPLAY =============

dv.table(
    ["Item", "Session", "Holder", "Qty", "Value", "Total (gp)", "Claimed", "Action"],
    tableRows
);
~~~



<BR><BR>

> [!section]+ Party Coins
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
    let valStr = coin.value === 1
        ? totalVal.toFixed(0)
        : totalVal.toFixed(2);
    return { ...coin, totalQty, valStr };
});

let coinTableRows = coinTotals.map(c => [c.name, c.totalQty, c.valStr]);

let totalValue = coinTotals.reduce((sum, c) => sum + (c.totalQty * c.value), 0);
let totalStr = totalValue % 1 === 0 ? totalValue.toFixed(0) : totalValue.toFixed(2);

// Add total row
coinTableRows.push(["&nbsp;", "&nbsp;", "&nbsp;"]); // spacer
coinTableRows.push(["", "**Total:**", `**${totalStr}**`]);


dv.table(["Coin", "Total Qty", "Value (gp)"], coinTableRows);

~~~
