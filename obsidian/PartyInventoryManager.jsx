// === Party Inventory Manager for D&D Character Sheets ===
const CHARACTER_DIR = "Campaign/Parties/Characters/Party 1";

function arr(x) {
  if (!x) return [];
  if (Array.isArray(x)) return x;
  return [x];
}

function getFMVal(obj, key) {
  return obj && obj[key] && obj[key].value !== undefined ? obj[key].value : undefined;
}

function PartyInventoryFilters({ children }) {
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

function PartyInventoryFilter({ title, icon, children, onToggle, onClear }) {
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

function PartyInventoryQuery({ characterName, campaignId, paging = 25 }) {
  // Get character data to access party inventory from frontmatter
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
  console.debug("PartyInventory - Looking for character:", characterName);
  console.debug("PartyInventory - Campaign ID:", campaignId);
  console.debug("PartyInventory - Found character:", character?.$name, "at path:", character?.$path);

  // State for filters
  const [filterSearch, setFilterSearch] = dc.useState('');
  const [filterCategory, setFilterCategory] = dc.useState([]);
  const [filterContainer, setFilterContainer] = dc.useState([]);
  const [filterRarity, setFilterRarity] = dc.useState([]);
  const [filtersShown, setFiltersShown] = dc.useState(false);
  const [sortBy, setSortBy] = dc.useState('name'); // name, category, type, quantity, cost, container

  // Extract party inventory from character frontmatter
  let partyItems = [];
  let partyCurrency = {};
  let sharingEnabled = false;

  if (character && character.$frontmatter && character.$frontmatter.party_inventory) {
    // Use DataCore's useArray to properly extract the party inventory data (like InventoryManager)
    const partyInventoryArray = dc.useArray(character.$frontmatter.party_inventory, arr => arr);

    // Handle nested structure where party inventory data is wrapped in key/value pairs
    if (partyInventoryArray && partyInventoryArray.length > 0 && partyInventoryArray[0]?.key === 'party_inventory') {
      // Extract the actual party inventory data from the value property
      const partyData = partyInventoryArray[0]?.value || {};
      partyItems = partyData.party_items || [];
      partyCurrency = partyData.party_currency || {};
      sharingEnabled = (partyData.sharing_state || 0) > 0;
    } else if (partyInventoryArray && typeof partyInventoryArray === 'object' && !Array.isArray(partyInventoryArray)) {
      // Direct object structure
      partyItems = partyInventoryArray.party_items || [];
      partyCurrency = partyInventoryArray.party_currency || {};
      sharingEnabled = (partyInventoryArray.sharing_state || 0) > 0;
    } else if (Array.isArray(partyInventoryArray)) {
      // If it's already a plain array, treat it as party items directly
      partyItems = partyInventoryArray;
      partyCurrency = {};
      sharingEnabled = false;
    }

    console.debug("PartyInventory - Raw party inventory:", character.$frontmatter.party_inventory);
    console.debug("PartyInventory - Processed party inventory array:", partyInventoryArray);
    console.debug("PartyInventory - Processed party items:", partyItems.length, "items");
    console.debug("PartyInventory - Party currency:", partyCurrency);
    console.debug("PartyInventory - Sharing enabled:", sharingEnabled);
  }

  // If no character found, show helpful error
  if (!character) {
    return (
      <div style="padding: 1em; border: 1px solid #f44336; border-radius: 0.5em; background-color: rgba(244, 67, 54, 0.1);">
        <h3>Character Not Found for Party Inventory</h3>
        <p>Could not find character: <strong>{characterName}</strong></p>
        <p>Available characters in <code>{CHARACTER_DIR}</code>:</p>
        <ul>
          {allChars.map(char => (
            <li key={char.$name}>
              <strong>{char.$name}</strong> <code>{char.$path}</code>
              {char.$frontmatter?.character_name && char.$frontmatter.character_name !== char.$name &&
                ` (frontmatter name: ${char.$frontmatter.character_name?.value || char.$frontmatter.character_name})`
              }
              {char.$frontmatter?.party_inventory ?
                ` [✓ has party inventory]` :
                ` [✗ no party inventory]`
              }
            </li>
          ))}
        </ul>
        <p><em>Make sure the character file exists and has party inventory data in frontmatter.</em></p>
      </div>
    );
  }

  // If character found but no party inventory
  if (partyItems.length === 0 && Object.keys(partyCurrency).length === 0) {
    return (
      <div style="padding: 1em; border: 1px solid #ff9800; border-radius: 0.5em; background-color: rgba(255, 152, 0, 0.1);">
        <h3>No Party Inventory Data</h3>
        <p>Found character <strong>{character.$name}</strong> but no party inventory data available.</p>
        {campaignId && <p>Campaign ID: <strong>{campaignId}</strong></p>}
        <p>Has party_inventory key: <strong>{character.$frontmatter?.party_inventory ? 'Yes' : 'No'}</strong></p>
        <p><em>Make sure the character sheet has been generated with party inventory data from D&D Beyond.</em></p>
      </div>
    );
  }

  // Get unique values for filters
  const allCategories = Array.from(new Set(partyItems.map(item => item.type).filter(Boolean))).sort();
  const allContainers = Array.from(new Set(partyItems.map(item => item.container).filter(Boolean))).sort();
  const allRarities = Array.from(new Set(partyItems.map(item => item.rarity).filter(x => x && x !== '—'))).sort();

  // Clear and toggle functions for enhanced filter controls
  const clearFilterCategory = () => setFilterCategory([]);
  const toggleFilterCategory = () => setFilterCategory(allCategories.filter(c => !filterCategory.includes(c)));

  const clearFilterContainer = () => setFilterContainer([]);
  const toggleFilterContainer = () => setFilterContainer(allContainers.filter(c => !filterContainer.includes(c)));

  const clearFilterRarity = () => setFilterRarity([]);
  const toggleFilterRarity = () => setFilterRarity(allRarities.filter(r => !filterRarity.includes(r)));

  // Apply filters
  const filteredItems = partyItems.filter(item => {
    if (filterSearch && !item?.name?.toLowerCase().includes(filterSearch.toLowerCase())) {
      return false;
    }
    if (filterCategory.length > 0 && !filterCategory.includes(item?.type)) {
      return false;
    }
    if (filterContainer.length > 0 && !filterContainer.includes(item?.container)) {
      return false;
    }
    if (filterRarity.length > 0 && !filterRarity.includes(item?.rarity)) {
      return false;
    }
    return true;
  });

  console.debug("PartyInventory - After filtering:", filteredItems.length, "items");
  console.debug("PartyInventory - Filter states:", { filterSearch, filterCategory, filterContainer, filterRarity });

  // Apply sorting
  filteredItems.sort((a, b) => {
    switch (sortBy) {
      case 'category':
        return (a.type || '').localeCompare(b.type || '') || (a.name || '').localeCompare(b.name || '');
      case 'type':
        return (a.type || '').localeCompare(b.type || '') || (a.name || '').localeCompare(b.name || '');
      case 'container':
        return (a.container || '').localeCompare(b.container || '') || (a.name || '').localeCompare(b.name || '');
      case 'quantity':
        return (b.quantity || 0) - (a.quantity || 0) || (a.name || '').localeCompare(b.name || '');
      case 'cost':
        return (b.cost || 0) - (a.cost || 0) || (a.name || '').localeCompare(b.name || '');
      default:
        return (a.name || '').localeCompare(b.name || '');
    }
  });

  // Calculate total party currency value in gold pieces
  const totalCurrencyGP = Object.entries(partyCurrency).reduce((total, [coinType, amount]) => {
    const multipliers = { 'cp': 0.01, 'sp': 0.1, 'ep': 0.5, 'gp': 1, 'pp': 10 };
    return total + (amount * (multipliers[coinType] || 1));
  }, 0);

  const columns = [
    {
      id: "Item",
      value: item => {
        console.debug("PartyInventory - Rendering item:", item?.name);
        return (
          <span style="font-weight: 500;">
            {item?.name || 'Unknown Item'}
          </span>
        );
      }
    },
    {
      id: "Type",
      value: item => {
        const itemType = item?.type || '—';
        return (
          <span style={`
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.85em;
            background-color: ${getPartyItemTypeColor(itemType)};
            color: white;
          `}>
            {itemType}
          </span>
        );
      }
    },
    { id: "Container", value: item => item?.container || '—' },
    { id: "Quantity", value: item => item?.quantity || 1 },
    {
      id: "Rarity",
      value: item => (item?.rarity && item.rarity !== '') ? (
        <span style={`color: ${getRarityColor(item.rarity)};`}>
          {item.rarity}
        </span>
      ) : "—"
    },
    {
      id: "Cost",
      value: item => (item?.cost > 0) ? formatCost(item.cost) : "—"
    },
    {
      id: "Description",
      value: item => {
        const description = item?.description || '';
        const shortDesc = description.length > 50 ? description.substring(0, 50) + '...' : description;
        return description ? (
          <span title={description} style="cursor: help;">
            {shortDesc}
          </span>
        ) : "—";
      }
    }
  ];

  return (
    <>
      {/* Party Currency Summary */}
      {Object.keys(partyCurrency).length > 0 && (
        <div style="margin-bottom: 1.5em; padding: 1em; background-color: var(--background-secondary-alt, #23272e); border-radius: 0.5em; border: 1px solid var(--background-modifier-border, #444);">
          <h4 style="margin: 0 0 0.5em 0; display: flex; align-items: center; gap: 0.5em;">
            <dc.Icon icon="lucide-coins" />
            Party Currency
            {campaignId && <span style="font-size: 0.8em; opacity: 0.7;">(Campaign {campaignId})</span>}
          </h4>
          <div style="display: flex; gap: 1em; flex-wrap: wrap;">
            {Object.entries(partyCurrency).map(([coinType, amount]) =>
              amount > 0 && (
                <span key={coinType} style="font-weight: 500;">
                  {amount} {coinType.toUpperCase()}
                </span>
              )
            )}
            <span style="margin-left: auto; font-style: italic; opacity: 0.8;">
              Total: {Math.round(totalCurrencyGP * 100) / 100} gp
            </span>
          </div>
          <div style="margin-top: 0.5em; font-size: 0.9em; opacity: 0.7;">
            Sharing: {sharingEnabled ? 'Enabled' : 'Disabled'}
          </div>
        </div>
      )}

      {/* Party Items */}
      {partyItems.length > 0 && (
        <>
          <div style="display: flex; gap: 0.75em; align-items: center; margin-bottom: 1em;">
            <input
              type="search"
              placeholder="Search party items..."
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
              <option value="type">Sort by Type</option>
              <option value="container">Sort by Container</option>
              <option value="quantity">Sort by Quantity</option>
              <option value="cost">Sort by Cost</option>
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
                clearFilterRarity();
              }}
              title="Clear all filters"
            >
              Clear
            </button>
          </div>

          {filtersShown && (
            <PartyInventoryFilters>
              <PartyInventoryFilter
                title="Type"
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
              </PartyInventoryFilter>

              {allContainers.length > 0 && (
                <PartyInventoryFilter
                  title="Container"
                  icon="lucide-box"
                  onToggle={toggleFilterContainer}
                  onClear={clearFilterContainer}
                >
                  {allContainers.map(container => (
                    <label style="display: block" key={container}>
                      <input
                        type="checkbox"
                        checked={filterContainer.includes(container)}
                        onchange={e =>
                          setFilterContainer(
                            e.target.checked
                              ? [...filterContainer, container]
                              : filterContainer.filter(x => x !== container)
                          )
                        }
                      />{' '}
                      {container}
                    </label>
                  ))}
                </PartyInventoryFilter>
              )}

              {allRarities.length > 0 && (
                <PartyInventoryFilter
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
                </PartyInventoryFilter>
              )}
            </PartyInventoryFilters>
          )}

          <div style="margin-bottom: 1em; font-size: 0.9em; color: var(--text-muted);">
            Showing {filteredItems.length} of {partyItems.length} party items
          </div>

          {(() => {
            console.debug("PartyInventory - Passing to table - filteredItems:", filteredItems);
            console.debug("PartyInventory - First filtered item:", filteredItems[0]);
            console.debug("PartyInventory - Columns structure:", columns.map(c => c.id));
            return <dc.VanillaTable columns={columns} rows={filteredItems} paging={paging} />;
          })()}
        </>
      )}

      {partyItems.length === 0 && Object.keys(partyCurrency).length === 0 && (
        <div style="text-align: center; padding: 2em; opacity: 0.7;">
          <dc.Icon icon="lucide-users" size="2em" />
          <p>No party inventory or currency available</p>
        </div>
      )}
    </>
  );
}

// Helper functions
function getPartyItemTypeColor(type) {
  const colors = {
    'Weapon': '#f44336',
    'Armor': '#607d8b',
    'Shield': '#795548',
    'Equipment': '#4caf50',
    'Tool': '#ff9800',
    'Consumable': '#9c27b0',
    'Magic Item': '#2196f3',
    'Treasure': '#ffc107',
    'Other': '#757575'
  };
  return colors[type] || '#757575';
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

return { PartyInventoryQuery };