// === Spell Query for D&D Character Sheets ===
const CHARACTER_DIR = "Campaign/Parties/Characters/Party 1";

function arr(x) {
  if (!x) return [];
  if (Array.isArray(x)) return x;
  return [x];
}

function getFMVal(obj, key) {
  return obj && obj[key] && obj[key].value !== undefined ? obj[key].value : undefined;
}

function SpellFilters({ children }) {
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

function SpellFilter({ title, icon, children, onToggle, onClear }) {
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

function SpellQuery({ characterName, paging = 50 }) {
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
  console.debug("Found character:", character?.$name, "at path:", character?.$path);
  if (character) {
    console.debug("Character frontmatter keys:", character.$frontmatter ? Object.keys(character.$frontmatter) : []);
    console.debug("Has spell_data:", !!character.$frontmatter?.spell_data);
    console.debug("Spell_data type:", typeof character.$frontmatter?.spell_data);
    console.debug("Spell_data length:", character.$frontmatter?.spell_data?.length || 0);
  }
  
  // State for filters
  const [filterSearch, setFilterSearch] = dc.useState('');
  const [filterLevel, setFilterLevel] = dc.useState('');
  const [filterLevelMin, setFilterLevelMin] = dc.useState('');
  const [filterLevelMax, setFilterLevelMax] = dc.useState('');
  const [useLevelRange, setUseLevelRange] = dc.useState(false);
  const [filterSchool, setFilterSchool] = dc.useState([]);
  const [filterComponents, setFilterComponents] = dc.useState([]);
  const [filterConcentration, setFilterConcentration] = dc.useState('');
  const [filterRitual, setFilterRitual] = dc.useState('');
  const [filterPrepared, setFilterPrepared] = dc.useState('');
  const [filtersShown, setFiltersShown] = dc.useState(false);
  const [sortBy, setSortBy] = dc.useState('name'); // name, level, school
  
  // Extract spell data from character frontmatter
  let spellData = [];
  if (character && character.$frontmatter && character.$frontmatter.spell_data) {
    // Use DataCore's useArray to properly extract the spell data
    const spellArray = dc.useArray(character.$frontmatter.spell_data, arr => arr);
    
    // Handle nested structure where spell data is wrapped in key/value pairs
    if (spellArray && spellArray.length > 0 && spellArray[0]?.key === 'spell_data') {
      // Extract the actual spell items from the value property
      spellData = spellArray[0]?.value || [];
    } else {
      // Direct array structure
      spellData = spellArray || [];
    }
    
    console.debug("Raw spell_data:", character.$frontmatter.spell_data);
    console.debug("Processed spell data:", spellData.length, "spells");
    console.debug("First spell structure:", spellData[0]);
    console.debug("First spell keys:", spellData[0] ? Object.keys(spellData[0]) : 'none');
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
              {char.$frontmatter?.spell_data ? 
                ` [✓ has spells: ${char.$frontmatter.spell_data.length} spells]` : 
                ` [✗ no spell data]`
              }
            </li>
          ))}
        </ul>
        <p><em>Make sure the character file exists in the correct directory and has spell_data in frontmatter.</em></p>
      </div>
    );
  }
  
  // If character found but no spell data
  if (spellData.length === 0) {
    return (
      <div style="padding: 1em; border: 1px solid #ff9800; border-radius: 0.5em; background-color: rgba(255, 152, 0, 0.1);">
        <h3>No Spell Data</h3>
        <p>Found character <strong>{character.$name}</strong> at <code>{character.$path}</code></p>
        <p>Available frontmatter keys: <code>{character.$frontmatter ? Object.keys(character.$frontmatter).join(', ') : 'none'}</code></p>
        <p>Has spell_data key: <strong>{character.$frontmatter?.spell_data ? 'Yes' : 'No'}</strong></p>
        {character.$frontmatter?.spell_data && (
          <p>Spell_data length: <strong>{character.$frontmatter.spell_data.length}</strong></p>
        )}
        <p><em>Make sure the character sheet has been generated with spell_data in frontmatter.</em></p>
        <details>
          <summary>Character frontmatter preview</summary>
          <pre>{JSON.stringify(character.$frontmatter, null, 2)}</pre>
        </details>
      </div>
    );
  }
  
  // Get unique values for filters
  const allSchools = Array.from(new Set(spellData.map(spell => spell.school).filter(Boolean))).sort();
  const allComponents = ['V', 'S', 'M'];
  const componentNames = { V: 'Verbal', S: 'Somatic', M: 'Material' };
  
  // Clear and toggle functions for enhanced filter controls
  const clearFilterSchool = () => setFilterSchool([]);
  const toggleFilterSchool = () => setFilterSchool(allSchools.filter(s => !filterSchool.includes(s)));
  
  const clearFilterComponents = () => setFilterComponents([]);
  const toggleFilterComponents = () => setFilterComponents(allComponents.filter(c => !filterComponents.includes(c)));
  
  // Apply filters
  const filteredSpells = spellData.filter(spell => {
    if (filterSearch && !spell?.name?.toLowerCase().includes(filterSearch.toLowerCase())) {
      return false;
    }
    // Handle level filtering - either exact level or range
    const spellLevel = spell?.level || 0;
    if (useLevelRange) {
      // Range filtering
      const minLevel = filterLevelMin !== '' ? Number(filterLevelMin) : 0;
      const maxLevel = filterLevelMax !== '' ? Number(filterLevelMax) : 9;
      if (spellLevel < minLevel || spellLevel > maxLevel) {
        return false;
      }
    } else {
      // Exact level filtering
      if (filterLevel && spellLevel !== parseInt(filterLevel)) {
        return false;
      }
    }
    if (filterSchool.length > 0 && !filterSchool.includes(spell?.school)) {
      return false;
    }
    if (filterComponents.length > 0) {
      const spellComponents = spell?.components || '';
      if (!filterComponents.every(comp => spellComponents.includes(comp))) {
        return false;
      }
    }
    if (filterConcentration && spell?.concentration !== (filterConcentration === 'true')) {
      return false;
    }
    if (filterRitual && spell?.ritual !== (filterRitual === 'true')) {
      return false;
    }
    if (filterPrepared && spell?.prepared !== (filterPrepared === 'true')) {
      return false;
    }
    return true;
  });
  
  console.debug("After filtering:", filteredSpells.length, "spells");
  console.debug("Filter states:", { filterSearch, filterLevel, filterSchool, filterComponents, filterConcentration, filterRitual, filterPrepared });
  
  // Apply sorting
  filteredSpells.sort((a, b) => {
    switch (sortBy) {
      case 'level':
        return a.level - b.level || a.name.localeCompare(b.name);
      case 'school':
        return a.school.localeCompare(b.school) || a.name.localeCompare(b.name);
      default:
        return a.name.localeCompare(b.name);
    }
  });
  
  // Check if character is a Wizard (needs Prepared column)
  const isWizard = character && character.$frontmatter && 
    (character.$frontmatter.class?.value === 'Wizard' || character.$frontmatter.class === 'Wizard');
  
  const columns = [
    {
      id: "Name",
      value: spell => {
        console.debug("Rendering spell:", spell?.name);
        return (
          <span style={spell?.prepared ? "font-weight: bold; color: #4fc3f7;" : undefined}>
            {spell?.name || 'Unknown Spell'}
          </span>
        );
      }
    },
    { 
      id: "Level", 
      value: spell => {
        const level = spell?.level;
        return level === 0 ? "Cantrip" : `${level}${getOrdinalSuffix(level)}`;
      }
    },
    { 
      id: "School", 
      value: spell => {
        const school = spell?.school || 'Unknown';
        return (
          <span style={`
            padding: 2px 6px; 
            border-radius: 3px; 
            font-size: 0.85em;
            background-color: ${getSchoolColor(school)};
            color: white;
          `}>
            {school}
          </span>
        );
      }
    },
    { id: "Components", value: spell => spell?.components || '' },
    { id: "Casting Time", value: spell => spell?.casting_time || '' },
    { id: "Range", value: spell => spell?.range || '' },
    { id: "Duration", value: spell => spell?.duration || '' },
    { 
      id: "Concentration", 
      value: spell => spell?.concentration ? (
        <span style="color: #4caf50; font-weight: bold;">Yes</span>
      ) : ""
    },
    { 
      id: "Ritual", 
      value: spell => spell?.ritual ? (
        <span style="color: #4caf50; font-weight: bold;">Yes</span>
      ) : ""
    },
    { id: "Source", value: spell => spell?.source || '' }
  ];
  
  // Add Prepared column only for Wizards
  if (isWizard) {
    columns.splice(-1, 0, {
      id: "Prepared", 
      value: spell => spell?.prepared ? (
        <span style="color: #4caf50; font-weight: bold;">Yes</span>
      ) : ""
    });
  }
  
  return (
    <>
      <div style="display: flex; gap: 0.75em; align-items: center; margin-bottom: 1em;">
        <input
          type="search"
          placeholder="Search spells..."
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
          <option value="level">Sort by Level</option>
          <option value="school">Sort by School</option>
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
            setFilterLevel('');
            setFilterLevelMin('');
            setFilterLevelMax('');
            setUseLevelRange(false);
            clearFilterSchool();
            clearFilterComponents();
            setFilterConcentration('');
            setFilterRitual('');
            setFilterPrepared('');
          }}
          title="Clear all filters"
        >
          Clear
        </button>
      </div>
      
      {filtersShown && (
        <SpellFilters>
          <SpellFilter 
            title="School" 
            icon="lucide-book"
            onToggle={toggleFilterSchool}
            onClear={clearFilterSchool}
          >
            {allSchools.map(school => (
              <label style="display: block" key={school}>
                <input
                  type="checkbox"
                  checked={filterSchool.includes(school)}
                  onchange={e =>
                    setFilterSchool(
                      e.target.checked
                        ? [...filterSchool, school]
                        : filterSchool.filter(x => x !== school)
                    )
                  }
                />{' '}
                {school}
              </label>
            ))}
          </SpellFilter>
          
          <SpellFilter title="Level" icon="lucide-hash">
            <div style="margin-bottom: 1em;">
              <div style="font-weight: 500; margin-bottom: 0.25em; display: flex; align-items: center; gap: 0.5em;">
                Spell Level
                <label style="font-weight: normal; font-size: 0.9em; display: flex; align-items: center; gap: 0.25em;">
                  <input
                    type="checkbox"
                    checked={useLevelRange}
                    onchange={e => {
                      setUseLevelRange(e.target.checked);
                      if (e.target.checked) {
                        setFilterLevel(''); // Clear exact level when switching to range
                      } else {
                        setFilterLevelMin(''); // Clear range when switching to exact
                        setFilterLevelMax('');
                      }
                    }}
                    style="transform: scale(0.9);"
                  />
                  Range
                </label>
              </div>
              {useLevelRange ? (
                <div style="display: flex; gap: 0.5em; align-items: center;">
                  <input
                    type="number"
                    min="0"
                    max="9"
                    value={filterLevelMin}
                    onchange={e => setFilterLevelMin(e.target.value)}
                    placeholder="Min"
                    style="max-width: 60px;"
                  />
                  <span style="font-size: 0.9em; color: var(--text-muted);">to</span>
                  <input
                    type="number"
                    min="0"
                    max="9"
                    value={filterLevelMax}
                    onchange={e => setFilterLevelMax(e.target.value)}
                    placeholder="Max"
                    style="max-width: 60px;"
                  />
                </div>
              ) : (
                <select
                  value={filterLevel}
                  onchange={e => setFilterLevel(e.target.value)}
                  style="width: 100%;"
                >
                  <option value="">All Levels</option>
                  <option value="0">Cantrips</option>
                  <option value="1">1st Level</option>
                  <option value="2">2nd Level</option>
                  <option value="3">3rd Level</option>
                  <option value="4">4th Level</option>
                  <option value="5">5th Level</option>
                  <option value="6">6th Level</option>
                  <option value="7">7th Level</option>
                  <option value="8">8th Level</option>
                  <option value="9">9th Level</option>
                </select>
              )}
            </div>
          </SpellFilter>
          
          <SpellFilter 
            title="Components" 
            icon="lucide-zap"
            onToggle={toggleFilterComponents}
            onClear={clearFilterComponents}
          >
            {allComponents.map(comp => (
              <label style="display: block" key={comp}>
                <input
                  type="checkbox"
                  checked={filterComponents.includes(comp)}
                  onchange={e =>
                    setFilterComponents(
                      e.target.checked
                        ? [...filterComponents, comp]
                        : filterComponents.filter(x => x !== comp)
                    )
                  }
                />{' '}
                {componentNames[comp]}
              </label>
            ))}
          </SpellFilter>
          
          <SpellFilter title="Properties" icon="lucide-settings">
            <div style="margin-bottom: 1em;">
              <div style="font-weight: 500; margin-bottom: 0.5em;">Concentration</div>
              <div style="display: flex; flex-direction: column; gap: 0.25em;">
                <button
                  onclick={() => setFilterConcentration('')}
                  style={`
                    padding: 0.4em 0.6em;
                    border: 1px solid ${filterConcentration === '' ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.3em;
                    background-color: ${filterConcentration === '' ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterConcentration === '' ? '#4fc3f7' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.9em;
                    transition: all 0.2s ease;
                  `}
                >
                  All Spells
                </button>
                <button
                  onclick={() => setFilterConcentration('true')}
                  style={`
                    padding: 0.4em 0.6em;
                    border: 1px solid ${filterConcentration === 'true' ? '#4caf50' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.3em;
                    background-color: ${filterConcentration === 'true' ? 'rgba(76, 175, 80, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterConcentration === 'true' ? '#4caf50' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.9em;
                    transition: all 0.2s ease;
                  `}
                >
                  🔮 Concentration Only
                </button>
                <button
                  onclick={() => setFilterConcentration('false')}
                  style={`
                    padding: 0.4em 0.6em;
                    border: 1px solid ${filterConcentration === 'false' ? '#ff9800' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.3em;
                    background-color: ${filterConcentration === 'false' ? 'rgba(255, 152, 0, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterConcentration === 'false' ? '#ff9800' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.9em;
                    transition: all 0.2s ease;
                  `}
                >
                  ⚡ No Concentration
                </button>
              </div>
            </div>
            
            <div>
              <div style="font-weight: 500; margin-bottom: 0.5em;">Ritual</div>
              <div style="display: flex; flex-direction: column; gap: 0.25em;">
                <button
                  onclick={() => setFilterRitual('')}
                  style={`
                    padding: 0.4em 0.6em;
                    border: 1px solid ${filterRitual === '' ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.3em;
                    background-color: ${filterRitual === '' ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterRitual === '' ? '#4fc3f7' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.9em;
                    transition: all 0.2s ease;
                  `}
                >
                  All Spells
                </button>
                <button
                  onclick={() => setFilterRitual('true')}
                  style={`
                    padding: 0.4em 0.6em;
                    border: 1px solid ${filterRitual === 'true' ? '#9c27b0' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.3em;
                    background-color: ${filterRitual === 'true' ? 'rgba(156, 39, 176, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterRitual === 'true' ? '#9c27b0' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.9em;
                    transition: all 0.2s ease;
                  `}
                >
                  🕯️ Ritual Only
                </button>
                <button
                  onclick={() => setFilterRitual('false')}
                  style={`
                    padding: 0.4em 0.6em;
                    border: 1px solid ${filterRitual === 'false' ? '#607d8b' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.3em;
                    background-color: ${filterRitual === 'false' ? 'rgba(96, 125, 139, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterRitual === 'false' ? '#607d8b' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.9em;
                    transition: all 0.2s ease;
                  `}
                >
                  ⚔️ No Ritual
                </button>
              </div>
            </div>
          </SpellFilter>
          
          {isWizard && (
            <SpellFilter title="Preparation" icon="lucide-check">
              <div>
                <div style="font-weight: 500; margin-bottom: 0.5em;">Prepared Status</div>
                <div style="display: flex; flex-direction: column; gap: 0.25em;">
                  <button
                    onclick={() => setFilterPrepared('')}
                    style={`
                      padding: 0.4em 0.6em;
                      border: 1px solid ${filterPrepared === '' ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                      border-radius: 0.3em;
                      background-color: ${filterPrepared === '' ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                      color: ${filterPrepared === '' ? '#4fc3f7' : 'var(--text-normal)'};
                      cursor: pointer;
                      font-size: 0.9em;
                      transition: all 0.2s ease;
                    `}
                  >
                    All Spells
                  </button>
                  <button
                    onclick={() => setFilterPrepared('true')}
                    style={`
                      padding: 0.4em 0.6em;
                      border: 1px solid ${filterPrepared === 'true' ? '#4caf50' : 'var(--background-modifier-border, #444)'};
                      border-radius: 0.3em;
                      background-color: ${filterPrepared === 'true' ? 'rgba(76, 175, 80, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                      color: ${filterPrepared === 'true' ? '#4caf50' : 'var(--text-normal)'};
                      cursor: pointer;
                      font-size: 0.9em;
                      transition: all 0.2s ease;
                    `}
                  >
                    📝 Prepared Only
                  </button>
                  <button
                    onclick={() => setFilterPrepared('false')}
                    style={`
                      padding: 0.4em 0.6em;
                      border: 1px solid ${filterPrepared === 'false' ? '#ff9800' : 'var(--background-modifier-border, #444)'};
                      border-radius: 0.3em;
                      background-color: ${filterPrepared === 'false' ? 'rgba(255, 152, 0, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                      color: ${filterPrepared === 'false' ? '#ff9800' : 'var(--text-normal)'};
                      cursor: pointer;
                      font-size: 0.9em;
                      transition: all 0.2s ease;
                    `}
                  >
                    📖 Not Prepared
                  </button>
                </div>
              </div>
            </SpellFilter>
          )}
        </SpellFilters>
      )}
      
      <div style="margin-bottom: 1em; font-size: 0.9em; color: var(--text-muted);">
        Showing {filteredSpells.length} of {spellData.length} spells
      </div>
      
      {(() => {
        console.debug("Passing to table - filteredSpells:", filteredSpells);
        console.debug("First filtered spell:", filteredSpells[0]);
        console.debug("Columns structure:", columns.map(c => c.id));
        return <dc.VanillaTable columns={columns} rows={filteredSpells} paging={paging} />;
      })()}
    </>
  );
}

// Helper functions
function getOrdinalSuffix(num) {
  const j = num % 10;
  const k = num % 100;
  if (j === 1 && k !== 11) return "st";
  if (j === 2 && k !== 12) return "nd";
  if (j === 3 && k !== 13) return "rd";
  return "th";
}

function getSchoolColor(school) {
  const colors = {
    'Abjuration': '#2196f3',
    'Conjuration': '#4caf50',
    'Divination': '#ff9800',
    'Enchantment': '#e91e63',
    'Evocation': '#f44336',
    'Illusion': '#9c27b0',
    'Necromancy': '#424242',
    'Transmutation': '#795548',
    'Unknown': '#757575'
  };
  return colors[school] || '#757575';
}

return { SpellQuery };