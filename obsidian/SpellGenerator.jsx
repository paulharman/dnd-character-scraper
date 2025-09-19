// === Constants and Helpers ===
const CHARACTER_DIR = "Campaign/Parties/Characters/Party 1";
const CHARACTER_NAME = "Ilarion_Veles_Paul";
const SPELLBOOK_YAML_KEY = "spells";
const SPELL_LOCATION = "z_Mechanics/CLI/spells";



function arr(x) {
  if (!x) return [];
  if (Array.isArray(x)) return x;
  return [x];
}

function getFMVal(obj, key) {
  return obj && obj[key] && obj[key].value !== undefined ? obj[key].value : undefined;
}

function extractSpellName(entry) {
  if (!entry) return null;
  if (typeof entry === "string") {
    return entry.replace(/^\[\[(.+?)\]\]$/, "$1");
  }
  if (typeof entry === "object") {
    if (entry.link) return entry.link;
    if (entry.path) return entry.path;
    if (entry.display) return entry.display;
    return String(entry);
  }
  return null;
}

function extractSpellFileName(entry) {
  // For a link object: { path: "z_Mechanics/CLI/spells/wall-of-fire-xphb", ... }
  if (entry && typeof entry === "object") {
    // Most robust: use path, but just grab filename at the end (no folders)
    const path = entry.path || entry.file?.name || entry.display || "";
    const match = path.match(/([^\/]+)$/); // grabs last bit after slash
    return match ? match[1].replace(/\.md$/, "").trim() : "";
  }
  // For a string: "[[wall-of-fire-xphb]]"
  if (typeof entry === "string") {
    const match = entry.match(/^\[\[(.+?)(\|.+?)?\]\]$/);
    return match ? match[1].replace(/\.md$/, "").trim() : entry.replace(/\.md$/, "").trim();
  }
  return "";
}

function useSelectedCharactersSpellbooks(selectedCharacters) {
  const chars = dc.useArray(dc.useQuery(`@page and path("${CHARACTER_DIR}")`), arr => arr);
  console.debug("All characters found:", chars);
  console.debug("Selected character names:", selectedCharacters);
  
  let combinedSpells = new Set();
  let spellToCharacters = new Map(); // Track which characters know each spell
  
  selectedCharacters.forEach(characterName => {
    const character = chars.find(page => page.$name === characterName);
    console.debug("Found character:", character?.name || characterName);
    
    if (character) {
      console.debug("Found character object:", character);
      let raw = null;
      console.debug("Checking for spells with key:", SPELLBOOK_YAML_KEY);
      if (typeof character.value === "function") raw = character.value(SPELLBOOK_YAML_KEY);
      if (!raw && character.frontmatter) raw = character.frontmatter[SPELLBOOK_YAML_KEY];
      if (!raw && character.$frontmatter) raw = character.$frontmatter[SPELLBOOK_YAML_KEY];

      // DEBUG: See what you actually get from YAML
      console.debug("Character spellbook raw value:", raw);
      console.debug("Available frontmatter keys:", Object.keys(character.frontmatter || {}));
      console.debug("Available $frontmatter keys:", Object.keys(character.$frontmatter || {}));

      if (raw) {
        let spells = [];
        if (Array.isArray(raw)) {
          spells = raw.map(extractSpellFileName).filter(Boolean);
        } else {
          const single = extractSpellFileName(raw);
          if (single) spells = [single];
        }
        spells.forEach(spell => {
          combinedSpells.add(spell);
          if (!spellToCharacters.has(spell)) {
            spellToCharacters.set(spell, []);
          }
          spellToCharacters.get(spell).push(characterName.replace(/_/g, ' '));
        });
      }
    }
  });
  
  const spellsArray = Array.from(combinedSpells);
  // DEBUG: Output the normalized spell list
  console.debug("Combined character spellbooks (normalized):", spellsArray);
  return { spells: spellsArray, spellToCharacters };
}

function useAvailableCharacters() {
  const chars = dc.useArray(dc.useQuery(`@page and path("${CHARACTER_DIR}")`), arr => arr);
  return chars
    .filter(page => {
      // Only include pages that have spells in frontmatter
      let hasSpells = false;
      if (typeof page.value === "function") hasSpells = !!page.value(SPELLBOOK_YAML_KEY);
      if (!hasSpells && page.frontmatter) hasSpells = !!page.frontmatter[SPELLBOOK_YAML_KEY];
      if (!hasSpells && page.$frontmatter) hasSpells = !!page.$frontmatter[SPELLBOOK_YAML_KEY];
      return hasSpells;
    })
    .map(page => page.$name)
    .sort();
}


function SpellQuerySettings({ children }) {
  return (
    <div
      style="
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5em;
        margin-top: 1em;
        align-items: stretch;
        height: 100%;
      "
    >
      {children}
    </div>
  );
}

function SpellQuerySetting({ title, icon, children, onToggle, onClear }) {
  return (
    <div
      style="
        border: 1px solid var(--background-modifier-border, #444);
        border-radius: 1em;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        padding: 1em 1em;
        min-width: 160px;
        background-color: var(--background-secondary-alt, #23272e);
        margin-bottom: 1.1em;
        display: flex;
        flex-direction: column;
        height: 100%;
        justify-content: flex-start;
      "
    >
      <div
        style="
          font-weight: 600;
          font-size: 1em;
          margin-bottom: 0.5em;
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 0.5em;
        "
      >
        <dc.Icon icon={icon} />
        <span style="flex-grow: 1; text-align: center;">{title}</span>
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
      <div style="display: flex; flex-direction: column; gap: 0.4em; overflow-y: auto;">
        {children}
      </div>
    </div>
  );
}

function SpellQuery({ showFilters = true, paging = 100 }) {
  const query = dc.useQuery(`@page and path("${SPELL_LOCATION}")`);
  const allPages = dc.useArray(query, arr => arr.sort(page => [page.value("name")], 'asc'));

  const availableCharacters = useAvailableCharacters();
  const [selectedCharacters, setSelectedCharacters] = dc.useState([]);
  const spellbookData = useSelectedCharactersSpellbooks(selectedCharacters);
  const characterSpellbook = spellbookData.spells;
  const spellToCharacters = spellbookData.spellToCharacters;
  const showSpellbookOnly = selectedCharacters.length > 0;

  const [filterSearch, setFilterSearch] = dc.useState('');
  const [filterClass, setFilterClass] = dc.useState([]);
  const [filterLevel, setFilterLevel] = dc.useState('');
  const [filterLevelMin, setFilterLevelMin] = dc.useState('');
  const [filterLevelMax, setFilterLevelMax] = dc.useState('');
  const [filterSchool, setFilterSchool] = dc.useState([]);
  const [filterComponents, setFilterComponents] = dc.useState([]);
  const [filtersShown, setFiltersShown] = dc.useState(false);
  const [filterClassSearch, setFilterClassSearch] = dc.useState('');
  const [filterConcentration, setFilterConcentration] = dc.useState('');
  const [filterRitual, setFilterRitual] = dc.useState('');
  const [filterRange, setFilterRange] = dc.useState('');

  const allComponents = ["V", "S", "M"];
  const componentNames = { V: "Verbal", S: "Somatic", M: "Material" };
  const componentPropMap = { V: 'verbal', S: 'somatic', M: 'material' };
  
  const [sortByLevel, setSortByLevel] = dc.useState(false);

  const allClasses = Array.from(
    new Set(
      allPages
        .flatMap(p => arr(p.value("classes")))
        .filter(Boolean)
    )
  ).sort();
  const allSchools = Array.from(
    new Set(
      allPages
        .map(p => p.value("school"))
        .filter(Boolean)
    )
  ).sort();

  // Clear and toggle functions for enhanced filter controls
  const clearFilterClass = () => setFilterClass([]);
  const toggleFilterClass = () => setFilterClass(allClasses.filter(c => !filterClass.includes(c)));
  
  const clearFilterSchool = () => setFilterSchool([]);
  const toggleFilterSchool = () => setFilterSchool(allSchools.filter(s => !filterSchool.includes(s)));
  
  const clearFilterComponents = () => setFilterComponents([]);
  const toggleFilterComponents = () => setFilterComponents(allComponents.filter(c => !filterComponents.includes(c)));
  
  const clearSelectedCharacters = () => setSelectedCharacters([]);
  const toggleSelectedCharacters = () => setSelectedCharacters(availableCharacters.filter(c => !selectedCharacters.includes(c)));

  const filteredPages = allPages.filter(page => {
    const fm = page.$frontmatter || {};

    if (page.$path === `${SPELL_LOCATION}/spells.md`) return false;
    if (showSpellbookOnly && !characterSpellbook.includes(page.$name)) return false;
    const spellName = (getFMVal(fm, 'name') || page.$name || '').toLowerCase();
    if (filterSearch && !spellName.includes(filterSearch.toLowerCase()))
      return false;
    const spellClasses = getFMVal(fm, 'classes') || [];
    if (
      filterClass.length > 0 &&
      !filterClass.some(cls => Array.isArray(spellClasses) ? spellClasses.includes(cls) : spellClasses === cls)
    )
      return false;
    // Handle level filtering - either exact level or range
    const spellLevel = Number(getFMVal(fm, 'levelint'));
    // If exact level is specified, use that
    if (filterLevel && spellLevel !== Number(filterLevel)) {
      return false;
    }
    // If range is specified (and exact is not), use range
    if (!filterLevel && (filterLevelMin || filterLevelMax)) {
      const minLevel = filterLevelMin !== '' ? Number(filterLevelMin) : 0;
      const maxLevel = filterLevelMax !== '' ? Number(filterLevelMax) : 9;
      if (spellLevel < minLevel || spellLevel > maxLevel) {
        return false;
      }
    }
    if (
      filterConcentration &&
      String(getFMVal(fm, 'concentration')) !== filterConcentration
    )
      return false;
    if (
      filterRitual &&
      String(getFMVal(fm, 'ritual')) !== filterRitual
    )
      return false;
    // Range filtering
    if (filterRange) {
      const spellRange = (getFMVal(fm, 'range') || '').toLowerCase();
      if (filterRange === 'touch' && !spellRange.includes('touch')) {
        return false;
      }
    }
    if (
      filterSchool.length > 0 &&
      !filterSchool.includes(getFMVal(fm, 'school'))
    )
      return false;
    if (
      filterComponents.length > 0 &&
      !filterComponents.every(short =>
        getFMVal(fm, componentPropMap[short]) === true
      )
    )
      return false;
    return true;
  });

// Apply sorting after filtering
if (sortByLevel) {
  filteredPages.sort((a, b) => {
    // By level (numeric, then fallback to name)
    let lA = Number(a.value("levelint") ?? a.value("level") ?? 0);
    let lB = Number(b.value("levelint") ?? b.value("level") ?? 0);
    if (lA !== lB) return lA - lB;
    // By name/alias as fallback
    let nA = (a.value("name") ?? a.$name ?? "").toLowerCase();
    let nB = (b.value("name") ?? b.$name ?? "").toLowerCase();
    return nA.localeCompare(nB);
  });
} else {
  // Default: sort by name/alias
  filteredPages.sort((a, b) => {
    let nA = (a.value("name") ?? a.$name ?? "").toLowerCase();
    let nB = (b.value("name") ?? b.$name ?? "").toLowerCase();
    return nA.localeCompare(nB);
  });
}

  const columns = [
    {
      id: "Name",
      value: p => {
        const fileName = p.$name;
        const displayName = p.value("name") || fileName;
        const filePath = p.$path;
        const href = `obsidian://open?file=${encodeURIComponent(filePath)}`;
        const inBook = characterSpellbook.includes(fileName);
        return (
          <a
            target="_blank"
            rel="noopener"
            data-href={filePath}
            href={href}
            class="internal-link"
            aria-label={filePath}
            style={inBook
              // Softer, blue, bold, NO underline or background
              ? "font-weight: bold; color: #4fc3f7; text-decoration: none;"
              : undefined}
            title={inBook ? "Character knows this spell" : ""}
          >
            {displayName}
          </a>
        );
      }
    },
    // Add character column only when multiple characters are selected
    ...(selectedCharacters.length > 1 ? [{
      id: "Characters",
      value: p => {
        const fileName = p.$name;
        const characters = spellToCharacters.get(fileName) || [];
        return characters.length > 0 ? characters.sort().join(", ") : "";
      }
    }] : []),
    {
  id: "Level",
  value: p => (
    <span style="display:inline-block; min-width:90px; text-align:left;">
      {p.value("level")}
    </span>
  )
},

    { id: "School", value: p => p.value("school") },
    {
      id: "Components",
      value: p => typeof p.value("components") === "string"
        ? p.value("components")
        : arr(p.value("components")).join(', ')
    },
    {
      id: "Concentration",
      value: p => getFMVal(p.$frontmatter, 'concentration') === true ? "Yes" :
                  getFMVal(p.$frontmatter, 'concentration') === false ? "No" : ""
    },
    {
      id: "Ritual",
      value: p => getFMVal(p.$frontmatter, 'ritual') === true ? "Yes" :
                  getFMVal(p.$frontmatter, 'ritual') === false ? "No" : ""
    },
    {
      id: "Casting Time",
      value: p => getFMVal(p.$frontmatter, 'casting_time') || ""
    },
    {
      id: "Range",
      value: p => getFMVal(p.$frontmatter, 'range') || ""
    },
    {
      id: "Duration",
      value: p => getFMVal(p.$frontmatter, 'duration') || ""
    }
  ];

  return (
    <>
      <div style="display: flex; gap: 0.75em;">
        <input
          type="search"
          placeholder="Search..."
          value={filterSearch}
          oninput={e => setFilterSearch(e.target.value)}
          style="flex-grow: 1;"
        />
        {showFilters && (
          <button
            style="font-weight: 600; padding: 0 0.8em;"
            title="Quick: Only show Wizard spells"
            onclick={() => {
              setFilterClass(['Wizard']);
              setFilterClassSearch('Wizard');
            }}
          >
            🧙‍♂️ Wizard
          </button>
        )}
        {showFilters && (
          <button class="primary" onclick={() => setFiltersShown(!filtersShown)}>
            ⚙
          </button>
        )}
        {showFilters && (
          <button
            onclick={() => {
              clearFilterClass();
              setFilterLevel('');
              setFilterLevelMin('');
              setFilterLevelMax('');
              setFilterSearch('');
              clearFilterSchool();
              clearFilterComponents();
              setFilterClassSearch('');
              setFilterConcentration('');
              setFilterRitual('');
              setFilterRange('');
              clearSelectedCharacters();
            }}
          >
            Clear All
          </button>
        )}
      </div>

      {filtersShown && (
        <SpellQuerySettings>
          <SpellQuerySetting 
            title="Characters" 
            icon="lucide-user"
            onToggle={toggleSelectedCharacters}
            onClear={clearSelectedCharacters}
          >
            <div style="display: flex; flex-direction: column; gap: 0.2em; min-height: 400px; max-height: 400px; overflow-y: auto;">
              {availableCharacters.map(c => (
                <button
                  key={c}
                  onclick={() => setSelectedCharacters(
                    selectedCharacters.includes(c)
                      ? selectedCharacters.filter(x => x !== c)
                      : [...selectedCharacters, c]
                  )}
                  style={`
                    padding: 0.3em 0.5em;
                    border: 1px solid ${selectedCharacters.includes(c) ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.25em;
                    background-color: ${selectedCharacters.includes(c) ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${selectedCharacters.includes(c) ? '#4fc3f7' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.8em;
                    transition: all 0.2s ease;
                    text-align: left;
                  `}
                >
                  {c.replace(/_/g, ' ')}
                </button>
              ))}
            </div>
          </SpellQuerySetting>
          <SpellQuerySetting 
            title="Class" 
            icon="lucide-users"
            onToggle={toggleFilterClass}
            onClear={clearFilterClass}
          >
            <input
              type="search"
              placeholder="Type to filter classes..."
              value={filterClassSearch}
              oninput={e => setFilterClassSearch(e.target.value)}
              style="margin-bottom: 0.5em; font-size: 0.8em; padding: 0.3em;"
            />
            <div style="display: flex; flex-direction: column; gap: 0.2em; min-height: 400px; max-height: 400px; overflow-y: auto;">
              {allClasses
                .filter(c => c.toLowerCase().includes(filterClassSearch.toLowerCase()))
                .map(c => (
                  <button
                    key={c}
                    onclick={() => setFilterClass(
                      filterClass.includes(c)
                        ? filterClass.filter(x => x !== c)
                        : [...filterClass, c]
                    )}
                    style={`
                      padding: 0.3em 0.5em;
                      border: 1px solid ${filterClass.includes(c) ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                      border-radius: 0.25em;
                      background-color: ${filterClass.includes(c) ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                      color: ${filterClass.includes(c) ? '#4fc3f7' : 'var(--text-normal)'};
                      cursor: pointer;
                      font-size: 0.8em;
                      transition: all 0.2s ease;
                      text-align: left;
                    `}
                  >
                    {c}
                  </button>
                ))}
            </div>
          </SpellQuerySetting>
          <SpellQuerySetting 
            title="School" 
            icon="lucide-folder"
            onToggle={toggleFilterSchool}
            onClear={clearFilterSchool}
          >
            <div style="display: flex; flex-direction: column; gap: 0.2em;">
              {allSchools.map(s => (
                <button
                  key={s}
                  onclick={() => setFilterSchool(
                    filterSchool.includes(s)
                      ? filterSchool.filter(x => x !== s)
                      : [...filterSchool, s]
                  )}
                  style={`
                    padding: 0.3em 0.5em;
                    border: 1px solid ${filterSchool.includes(s) ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.25em;
                    background-color: ${filterSchool.includes(s) ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterSchool.includes(s) ? '#4fc3f7' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.8em;
                    transition: all 0.2s ease;
                    text-align: left;
                  `}
                >
                  {s}
                </button>
              ))}
            </div>
          </SpellQuerySetting>
          <SpellQuerySetting 
            title="Level, Components & Sorting" 
            icon="lucide-hash"
            onToggle={toggleFilterComponents}
            onClear={clearFilterComponents}
          >
            <div style="font-weight: 500; margin-bottom: 0.5em;">Level Filter</div>
            <div style="display: flex; gap: 0.4em; align-items: center; margin-bottom: 1em; flex-wrap: wrap;">
              <input
                type="number"
                min="0"
                max="9"
                value={filterLevel || filterLevelMin}
                onchange={e => {
                  const value = e.target.value;
                  setFilterLevel(value);
                  setFilterLevelMin(value);
                  if (!value) setFilterLevelMax('');
                }}
                placeholder="Min/Exact"
                style="max-width: 70px;"
              />
              <span style="color: var(--text-muted); font-size: 0.85em;">to</span>
              <input
                type="number"
                min="0"
                max="9"
                value={filterLevelMax}
                onchange={e => {
                  setFilterLevelMax(e.target.value);
                  if (e.target.value) setFilterLevel('');
                }}
                placeholder="Max"
                style="max-width: 50px;"
              />
            </div>
            
            <div style="font-weight: 500; margin-bottom: 0.4em;">Components</div>
            <div style="display: flex; flex-wrap: wrap; gap: 0.2em; margin-bottom: 1em;">
              {allComponents.map(comp => (
                <button
                  key={comp}
                  onclick={() => setFilterComponents(
                    filterComponents.includes(comp)
                      ? filterComponents.filter(x => x !== comp)
                      : [...filterComponents, comp]
                  )}
                  style={`
                    padding: 0.25em 0.4em;
                    border: 1px solid ${filterComponents.includes(comp) ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.2em;
                    background-color: ${filterComponents.includes(comp) ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterComponents.includes(comp) ? '#4fc3f7' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.75em;
                    transition: all 0.2s ease;
                    min-width: 60px;
                    text-align: center;
                  `}
                >
                  {componentNames[comp]}
                </button>
              ))}
            </div>
            
            <div style="padding-top: 0.4em; border-top: 1px solid var(--background-modifier-border, #444);">
              <div style="font-weight: 500; margin-bottom: 0.4em;">Sort Order</div>
              <div style="display: flex; flex-direction: column; gap: 0.2em;">
                <button
                  onclick={() => setSortByLevel(false)}
                  style={`
                    padding: 0.3em 0.5em;
                    border: 1px solid ${!sortByLevel ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.25em;
                    background-color: ${!sortByLevel ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${!sortByLevel ? '#4fc3f7' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.8em;
                    transition: all 0.2s ease;
                  `}
                >
                  🔤 Sort by Name
                </button>
                <button
                  onclick={() => setSortByLevel(true)}
                  style={`
                    padding: 0.3em 0.5em;
                    border: 1px solid ${sortByLevel ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.25em;
                    background-color: ${sortByLevel ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${sortByLevel ? '#4fc3f7' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.8em;
                    transition: all 0.2s ease;
                  `}
                >
                  📈 Sort by Level
                </button>
              </div>
            </div>
          </SpellQuerySetting>
          
          <SpellQuerySetting title="Properties & Range" icon="lucide-focus">
            <div style="margin-bottom: 1em;">
              <div style="font-weight: 500; margin-bottom: 0.4em;">Concentration</div>
              <div style="display: flex; flex-direction: column; gap: 0.2em;">
                <button
                  onclick={() => setFilterConcentration('')}
                  style={`
                    padding: 0.3em 0.5em;
                    border: 1px solid ${filterConcentration === '' ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.25em;
                    background-color: ${filterConcentration === '' ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterConcentration === '' ? '#4fc3f7' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.8em;
                    transition: all 0.2s ease;
                  `}
                >
                  All
                </button>
                <button
                  onclick={() => setFilterConcentration('true')}
                  style={`
                    padding: 0.3em 0.5em;
                    border: 1px solid ${filterConcentration === 'true' ? '#4caf50' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.25em;
                    background-color: ${filterConcentration === 'true' ? 'rgba(76, 175, 80, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterConcentration === 'true' ? '#4caf50' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.8em;
                    transition: all 0.2s ease;
                  `}
                >
                  🔮 Yes
                </button>
                <button
                  onclick={() => setFilterConcentration('false')}
                  style={`
                    padding: 0.3em 0.5em;
                    border: 1px solid ${filterConcentration === 'false' ? '#ff9800' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.25em;
                    background-color: ${filterConcentration === 'false' ? 'rgba(255, 152, 0, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterConcentration === 'false' ? '#ff9800' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.8em;
                    transition: all 0.2s ease;
                  `}
                >
                  ⚡ No
                </button>
              </div>
            </div>
            
            <div style="margin-bottom: 1em;">
              <div style="font-weight: 500; margin-bottom: 0.4em;">Ritual</div>
              <div style="display: flex; flex-direction: column; gap: 0.2em;">
                <button
                  onclick={() => setFilterRitual('')}
                  style={`
                    padding: 0.3em 0.5em;
                    border: 1px solid ${filterRitual === '' ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.25em;
                    background-color: ${filterRitual === '' ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterRitual === '' ? '#4fc3f7' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.8em;
                    transition: all 0.2s ease;
                  `}
                >
                  All
                </button>
                <button
                  onclick={() => setFilterRitual('true')}
                  style={`
                    padding: 0.3em 0.5em;
                    border: 1px solid ${filterRitual === 'true' ? '#9c27b0' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.25em;
                    background-color: ${filterRitual === 'true' ? 'rgba(156, 39, 176, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterRitual === 'true' ? '#9c27b0' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.8em;
                    transition: all 0.2s ease;
                  `}
                >
                  🕯️ Yes
                </button>
                <button
                  onclick={() => setFilterRitual('false')}
                  style={`
                    padding: 0.3em 0.5em;
                    border: 1px solid ${filterRitual === 'false' ? '#607d8b' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.25em;
                    background-color: ${filterRitual === 'false' ? 'rgba(96, 125, 139, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterRitual === 'false' ? '#607d8b' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.8em;
                    transition: all 0.2s ease;
                  `}
                >
                  ⚔️ No
                </button>
              </div>
            </div>
            
            <div>
              <div style="font-weight: 500; margin-bottom: 0.4em;">Range</div>
              <div style="display: flex; flex-direction: column; gap: 0.2em;">
                <button
                  onclick={() => setFilterRange('')}
                  style={`
                    padding: 0.3em 0.5em;
                    border: 1px solid ${filterRange === '' ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.25em;
                    background-color: ${filterRange === '' ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterRange === '' ? '#4fc3f7' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.8em;
                    transition: all 0.2s ease;
                  `}
                >
                  All Ranges
                </button>
                <button
                  onclick={() => setFilterRange('touch')}
                  style={`
                    padding: 0.3em 0.5em;
                    border: 1px solid ${filterRange === 'touch' ? '#e91e63' : 'var(--background-modifier-border, #444)'};
                    border-radius: 0.25em;
                    background-color: ${filterRange === 'touch' ? 'rgba(233, 30, 99, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                    color: ${filterRange === 'touch' ? '#e91e63' : 'var(--text-normal)'};
                    cursor: pointer;
                    font-size: 0.8em;
                    transition: all 0.2s ease;
                  `}
                >
                  👋 Touch Only
                </button>
              </div>
            </div>
          </SpellQuerySetting>
        </SpellQuerySettings>
      )}

      <dc.VanillaTable columns={columns} rows={filteredPages} paging={paging} />
    </>
  );
}

return { SpellQuery };
