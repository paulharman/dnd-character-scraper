// === Inventory Manager for D&D Character Sheets ===
const CHARACTER_DIR = "Campaign/Parties/Characters/Party 1";

function arr(x) {
  if (!x) return [];
  if (Array.isArray(x)) return x;
  return [x];
}

function getFMVal(obj, key) {
  return obj && obj[key] && obj[key].value !== undefined ? obj[key].value : undefined;
}

function InventoryFilters({ children }) {
  return (
    <div
      style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5em;
        margin: 1em 0;
        align-items: stretch;
      "
    >
      {children}
    </div>
  );
}

function InventoryFilter({ title, icon, children, onToggle, onClear }) {
  return (
    <div
      style="
        border: 1px solid var(--background-modifier-border, #444);
        border-radius: 0.5em;
        padding: 1em;
        background-color: var(--background-secondary-alt, #23272e);
        display: flex;
        flex-direction: column;
      "
    >
      <div
        style="
          font-weight: 600;
          font-size: 1em;
          margin-bottom: 0.5em;
          display: flex;
          align-items: center;
          gap: 0.5em;
        "
      >
        <dc.Icon icon={icon} />
        <span style="flex-grow: 1;">{title}</span>
        {(onToggle || onClear) && <span style="color: var(--text-muted);">|</span>}
        {onToggle && (
          <span 
            onclick={onToggle} 
            style="cursor: pointer; opacity: 0.7; hover: opacity: 1;" 
            title="Toggle selection"
          >
            <dc.Icon icon="toggle-left" />
          </span>
        )}
        {onClear && (
          <span 
            onclick={onClear} 
            style="cursor: pointer; opacity: 0.7; hover: opacity: 1;" 
            title="Clear all"
          >
            <dc.Icon icon="list-restart" />
          </span>
        )}
      </div>
      <div style="display: flex; flex-direction: column; gap: 0.4em;">
        {children}
      </div>
    </div>
  );
}

function InventoryQuery({ characterName, paging = 50 }) {
  // Get character data
  const query = dc.useQuery(`@page and path("${CHARACTER_DIR}")`);
  const allCharsRaw = dc.useArray(query, arr => arr);
  
  // Filter out Archive folder
  const allChars = allCharsRaw.filter(page => !page.$path.includes('/Archive/'));
  
  // Try multiple ways to find the character
  let character = allChars.find(page => page.$name === characterName);
  
  // If not found, try without parenthetical parts
  if (!character && characterName.includes('(')) {
    const baseNameMatch = characterName.split('(')[0].trim();
    character = allChars.find(page => page.$name === baseNameMatch);
  }
  
  // If still not found, try matching the character_name from frontmatter
  if (!character) {
    character = allChars.find(page => {
      const fmName = page.$frontmatter?.character_name?.value || page.$frontmatter?.character_name;
      return fmName === characterName;
    });
  }
  
  // If still not found, try partial matching
  if (!character) {
    character = allChars.find(page => {
      const pageName = page.$name?.toLowerCase() || '';
      const searchName = characterName.toLowerCase();
      return pageName.includes(searchName.split('(')[0].trim().toLowerCase()) || 
             searchName.includes(pageName);
    });
  }
  
  // Debug logging
  console.debug("Looking for character:", characterName);
  console.debug("Available characters:", allChars.map(p => ({ 
    name: p.$name, 
    path: p.$path,
    frontmatter_name: p.$frontmatter?.character_name,
    has_inventory: !!p.$frontmatter?.inventory,
    frontmatter_keys: p.$frontmatter ? Object.keys(p.$frontmatter) : []
  })));
  console.debug("Found character:", character?.$name, "at path:", character?.$path);
  if (character) {
    console.debug("Character frontmatter keys:", character.$frontmatter ? Object.keys(character.$frontmatter) : []);
    console.debug("Has inventory:", !!character.$frontmatter?.inventory);
    console.debug("Inventory type:", typeof character.$frontmatter?.inventory);
    console.debug("Inventory value:", character.$frontmatter?.inventory);
    console.debug("Inventory length:", character.$frontmatter?.inventory?.length || 0);
  }
  
  // State for filters
  const [filterSearch, setFilterSearch] = dc.useState('');
  const [filterCategory, setFilterCategory] = dc.useState([]);
  const [filterContainer, setFilterContainer] = dc.useState([]);
  const [filterEquipped, setFilterEquipped] = dc.useState('');
  const [filterRarity, setFilterRarity] = dc.useState([]);
  const [filtersShown, setFiltersShown] = dc.useState(false);
  const [sortBy, setSortBy] = dc.useState('name'); // name, category, container, weight
  
  // Extract inventory from character frontmatter
  let inventoryItems = [];
  if (character && character.$frontmatter && character.$frontmatter.inventory) {
    // Use DataCore's useArray to properly extract the inventory data
    const inventoryArray = dc.useArray(character.$frontmatter.inventory, arr => arr);
    
    // Handle nested structure where inventory data is wrapped in key/value pairs
    if (inventoryArray && inventoryArray.length > 0 && inventoryArray[0]?.key === 'inventory') {
      // Extract the actual inventory items from the value property
      inventoryItems = inventoryArray[0]?.value || [];
    } else {
      // Direct array structure
      inventoryItems = inventoryArray || [];
    }
    
    console.debug("Raw inventory:", character.$frontmatter.inventory);
    console.debug("Processed inventory items:", inventoryItems.length, "items");
    console.debug("First item structure:", inventoryItems[0]);
    console.debug("First item keys:", inventoryItems[0] ? Object.keys(inventoryItems[0]) : 'none');
  }
  
  // If no character found, show helpful error
  if (!character) {
    return (
      <div style="padding: 1em; border: 1px solid #f44336; border-radius: 0.5em; background-color: rgba(244, 67, 54, 0.1);">
        <h3>Character Not Found</h3>
        <p>Could not find character: <strong>{characterName}</strong></p>
        <p>Available characters in <code>{CHARACTER_DIR}</code>:</p>
        <ul>
          {allChars.map(char => (
            <li key={char.$name}>
              <strong>{char.$name}</strong> <code>{char.$path}</code>
              {char.$frontmatter?.character_name && char.$frontmatter.character_name !== char.$name && 
                ` (frontmatter name: ${char.$frontmatter.character_name?.value || char.$frontmatter.character_name})`
              }
              {char.$frontmatter?.inventory ? 
                ` [✓ has inventory: ${char.$frontmatter.inventory.length} items]` : 
                ` [✗ no inventory]`
              }
            </li>
          ))}
        </ul>
        <p><em>Make sure the character file exists in the correct directory and has inventory data in frontmatter.</em></p>
      </div>
    );
  }
  
  // If character found but no inventory
  if (inventoryItems.length === 0) {
    return (
      <div style="padding: 1em; border: 1px solid #ff9800; border-radius: 0.5em; background-color: rgba(255, 152, 0, 0.1);">
        <h3>No Inventory Data</h3>
        <p>Found character <strong>{character.$name}</strong> at <code>{character.$path}</code></p>
        <p>Available frontmatter keys: <code>{character.$frontmatter ? Object.keys(character.$frontmatter).join(', ') : 'none'}</code></p>
        <p>Has inventory key: <strong>{character.$frontmatter?.inventory ? 'Yes' : 'No'}</strong></p>
        {character.$frontmatter?.inventory && (
          <p>Inventory length: <strong>{character.$frontmatter.inventory.length}</strong></p>
        )}
        <p><em>Make sure the character sheet has been generated with inventory data in frontmatter.</em></p>
        <details>
          <summary>Character frontmatter preview</summary>
          <pre>{JSON.stringify(character.$frontmatter, null, 2)}</pre>
        </details>
      </div>
    );
  }
  
  // Get unique values for filters
  const allCategories = Array.from(new Set(inventoryItems.map(item => item.category).filter(Boolean))).sort();
  const allContainers = Array.from(new Set(inventoryItems.map(item => item.container).filter(Boolean))).sort();
  const allRarities = Array.from(new Set(inventoryItems.map(item => item.rarity).filter(x => x && x !== '—'))).sort();
  
  // Clear and toggle functions for enhanced filter controls
  const clearFilterCategory = () => setFilterCategory([]);
  const toggleFilterCategory = () => setFilterCategory(allCategories.filter(c => !filterCategory.includes(c)));
  
  const clearFilterContainer = () => setFilterContainer([]);
  const toggleFilterContainer = () => setFilterContainer(allContainers.filter(c => !filterContainer.includes(c)));
  
  const clearFilterRarity = () => setFilterRarity([]);
  const toggleFilterRarity = () => setFilterRarity(allRarities.filter(r => !filterRarity.includes(r)));
  
  // Apply filters
  const filteredItems = inventoryItems.filter(item => {
    if (filterSearch && !item?.item?.toLowerCase().includes(filterSearch.toLowerCase())) {
      return false;
    }
    if (filterCategory.length > 0 && !filterCategory.includes(item?.category)) {
      return false;
    }
    if (filterContainer.length > 0 && !filterContainer.includes(item?.container)) {
      return false;
    }
    if (filterEquipped && item?.equipped !== (filterEquipped === 'true')) {
      return false;
    }
    if (filterRarity.length > 0 && !filterRarity.includes(item?.rarity)) {
      return false;
    }
    return true;
  });
  
  console.debug("After filtering:", filteredItems.length, "items");
  console.debug("Filter states:", { filterSearch, filterCategory, filterContainer, filterEquipped, filterRarity });
  
  // Apply sorting
  filteredItems.sort((a, b) => {
    switch (sortBy) {
      case 'category':
        return a.category.localeCompare(b.category) || a.item.localeCompare(b.item);
      case 'container':
        return a.container.localeCompare(b.container) || a.item.localeCompare(b.item);
      case 'weight':
        return (b.weight || 0) - (a.weight || 0) || a.item.localeCompare(b.item);
      default:
        return a.item.localeCompare(b.item);
    }
  });
  
  const columns = [
    {
      id: "Item",
      value: item => {
        console.debug("Rendering item:", item?.item);
        return (
          <span style={item?.equipped ? "font-weight: bold; color: #4fc3f7;" : undefined}>
            {item?.item || 'Unknown Item'}
          </span>
        );
      }
    },
    { 
      id: "Type", 
      value: item => {
        const itemType = item?.type || '—';
        const description = item?.description || '';
        
        // Enhanced custom item display with hover tooltips for descriptions/notes
        // Custom items with descriptions show an info icon and tooltip on hover
        if (itemType === 'Custom' && description) {
          return (
            <span>
              <span 
                title={description}
                style="cursor: help;"
              >
                {itemType}
              </span>
              <span 
                title={description}
                style="font-size: 0.8em; opacity: 0.7; margin-left: 0.25em; cursor: help;"
              >
                ℹ️
              </span>
            </span>
          );
        }
        
        return itemType;
      }
    },
    { 
      id: "Category", 
      value: item => {
        const category = item?.category || 'Other';
        return (
          <span style={`
            padding: 2px 6px; 
            border-radius: 3px; 
            font-size: 0.85em;
            background-color: ${getCategoryColor(category)};
            color: white;
          `}>
            {category}
          </span>
        );
      }
    },
    { id: "Container", value: item => item?.container || '—' },
    { id: "Qty", value: item => item?.quantity || 0 },
    { 
      id: "Equipped", 
      value: item => item?.equipped ? "✓" : "—"
    },
    { id: "Weight", value: item => (item?.weight > 0) ? `${item.weight} lbs` : "—" },
    { 
      id: "Rarity", 
      value: item => (item?.rarity && item.rarity !== '') ? (
        <span style={`color: ${getRarityColor(item.rarity)};`}>
          {item.rarity}
        </span>
      ) : "—"
    },
    { id: "Cost", value: item => (item?.cost > 0) ? formatCost(item.cost) : "—" },
    { 
      id: "Total Value", 
      value: item => {
        const cost = item?.cost || 0;
        const quantity = item?.quantity || 0;
        const totalValue = cost * quantity;
        return totalValue > 0 ? formatCost(totalValue) : "—";
      }
    }
  ];
  
  return (
    <>
      <div style="display: flex; gap: 0.75em; align-items: center; margin-bottom: 1em;">
        <input
          type="search"
          placeholder="Search items..."
          value={filterSearch}
          oninput={e => setFilterSearch(e.target.value)}
          style="flex-grow: 1;"
        />
        <select
          value={sortBy}
          onchange={e => setSortBy(e.target.value)}
          style="min-width: 120px;"
        >
          <option value="name">Sort by Name</option>
          <option value="category">Sort by Category</option>
          <option value="container">Sort by Container</option>
          <option value="weight">Sort by Weight</option>
        </select>
        <button
          class="primary"
          onclick={() => setFiltersShown(!filtersShown)}
          title="Show/hide filters"
        >
          ⚙ Filters
        </button>
        <button
          onclick={() => {
            setFilterSearch('');
            clearFilterCategory();
            clearFilterContainer();
            setFilterEquipped('');
            clearFilterRarity();
          }}
          title="Clear all filters"
        >
          Clear
        </button>
      </div>
      
      {filtersShown && (
        <InventoryFilters>
          <InventoryFilter 
            title="Category" 
            icon="lucide-package"
            onToggle={toggleFilterCategory}
            onClear={clearFilterCategory}
          >
            {allCategories.map(cat => (
              <label style="display: block" key={cat}>
                <input
                  type="checkbox"
                  checked={filterCategory.includes(cat)}
                  onchange={e =>
                    setFilterCategory(
                      e.target.checked
                        ? [...filterCategory, cat]
                        : filterCategory.filter(x => x !== cat)
                    )
                  }
                />{' '}
                {cat}
              </label>
            ))}
          </InventoryFilter>
          
          <InventoryFilter 
            title="Container" 
            icon="lucide-box"
            onToggle={toggleFilterContainer}
            onClear={clearFilterContainer}
          >
            {allContainers.map(cont => (
              <label style="display: block" key={cont}>
                <input
                  type="checkbox"
                  checked={filterContainer.includes(cont)}
                  onchange={e =>
                    setFilterContainer(
                      e.target.checked
                        ? [...filterContainer, cont]
                        : filterContainer.filter(x => x !== cont)
                    )
                  }
                />{' '}
                {cont}
              </label>
            ))}
          </InventoryFilter>
          
          <InventoryFilter title="Properties" icon="lucide-settings">
            <div>
              <div style="font-weight: 500; margin-bottom: 0.25em;">Equipped</div>
              <select
                value={filterEquipped}
                onchange={e => setFilterEquipped(e.target.value)}
                style="width: 100%;"
              >
                <option value="">All Items</option>
                <option value="true">Equipped Only</option>
                <option value="false">Unequipped Only</option>
              </select>
            </div>
          </InventoryFilter>
          
          {allRarities.length > 0 && (
            <InventoryFilter 
              title="Rarity" 
              icon="lucide-star"
              onToggle={toggleFilterRarity}
              onClear={clearFilterRarity}
            >
              {allRarities.map(rarity => (
                <label style="display: block" key={rarity}>
                  <input
                    type="checkbox"
                    checked={filterRarity.includes(rarity)}
                    onchange={e =>
                      setFilterRarity(
                        e.target.checked
                          ? [...filterRarity, rarity]
                          : filterRarity.filter(x => x !== rarity)
                      )
                    }
                  />{' '}
                  <span style={`color: ${getRarityColor(rarity)};`}>
                    {rarity}
                  </span>
                </label>
              ))}
            </InventoryFilter>
          )}
        </InventoryFilters>
      )}
      
      <div style="margin-bottom: 1em; font-size: 0.9em; color: var(--text-muted);">
        Showing {filteredItems.length} of {inventoryItems.length} items
      </div>
      
      {(() => {
        console.debug("Passing to table - filteredItems:", filteredItems);
        console.debug("First filtered item:", filteredItems[0]);
        console.debug("Columns structure:", columns.map(c => c.id));
        return <dc.VanillaTable columns={columns} rows={filteredItems} paging={paging} />;
      })()}
    </>
  );
}

// Helper functions
function getCategoryColor(category) {
  const colors = {
    'Magic': '#9c27b0',
    'Weapon': '#f44336',
    'Armor': '#607d8b',
    'Ammo': '#ff9800',
    'Tool': '#795548',
    'Gear': '#4caf50',
    'Container': '#2196f3',
    'Other': '#757575'
  };
  return colors[category] || '#757575';
}

function getRarityColor(rarity) {
  const colors = {
    'Common': '#ffffff',
    'Uncommon': '#1eff00',
    'Rare': '#0070dd',
    'Very Rare': '#a335ee',
    'Legendary': '#ff8000',
    'Artifact': '#e6cc80'
  };
  return colors[rarity] || '#ffffff';
}

function formatCost(cost) {
  if (cost < 1) {
    return cost >= 0.01 ? `${Math.round(cost * 100)} cp` : `${Math.round(cost * 1000)} sp`;
  }
  return cost % 1 === 0 ? `${cost} gp` : `${cost} gp`;
}

return { InventoryQuery };