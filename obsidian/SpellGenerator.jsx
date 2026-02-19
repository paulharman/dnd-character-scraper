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

// Word-based search: matches if ALL search words are found in the target string
// e.g., "fire ball" matches "Fireball" and "Wall of Fire"
function matchesSearch(target, searchQuery) {
  if (!target || !searchQuery) return false;
  const targetLower = target.toLowerCase();
  const searchWords = searchQuery.toLowerCase().trim().split(/\s+/).filter(w => w.length > 0);
  return searchWords.every(word => targetLower.includes(word));
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

// Convert a spell display name to its expected filename (mirrors Python's link generation)
function spellNameToFileName(name) {
  if (!name) return "";
  return name.toLowerCase().replace(/ /g, '-').replace(/'/g, '').replace(/\./g, '') + '-xphb';
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
  // Track spell sources per character: Map<spellFileName, Map<characterDisplayName, source>>
  let spellToCharacterSources = new Map();

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

      // Read spell_data for source information
      let spellData = null;
      if (typeof character.value === "function") spellData = character.value("spell_data");
      if (!spellData && character.frontmatter) spellData = character.frontmatter["spell_data"];
      if (!spellData && character.$frontmatter) spellData = character.$frontmatter["spell_data"];

      // Build a source map from spell_data: fileName -> source
      const sourceMap = new Map();
      if (spellData && Array.isArray(spellData)) {
        spellData.forEach(sd => {
          const name = sd.name || (sd.value && sd.value.name);
          const source = sd.source || (sd.value && sd.value.source);
          if (name) {
            const fileName = spellNameToFileName(typeof name === "object" && name.value !== undefined ? name.value : name);
            if (source) {
              const sourceStr = typeof source === "object" && source.value !== undefined ? source.value : source;
              sourceMap.set(fileName, sourceStr);
            }
          }
        });
      }

      // DEBUG: See what you actually get from YAML
      console.debug("Character spellbook raw value:", raw);
      console.debug("Character spell_data source map:", Object.fromEntries(sourceMap));

      const displayName = characterName.replace(/_/g, ' ');

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
          spellToCharacters.get(spell).push(displayName);

          // Track source for this character+spell
          const source = sourceMap.get(spell);
          if (source) {
            if (!spellToCharacterSources.has(spell)) {
              spellToCharacterSources.set(spell, new Map());
            }
            spellToCharacterSources.get(spell).set(displayName, source);
          }
        });
      }
    }
  });

  const spellsArray = Array.from(combinedSpells);
  // DEBUG: Output the normalized spell list
  console.debug("Combined character spellbooks (normalized):", spellsArray);
  return { spells: spellsArray, spellToCharacters, spellToCharacterSources };
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
  // Always load all characters' spellbooks for the Characters column, plus any specifically selected ones
  const allCharactersForSpellbook = selectedCharacters.length > 0 ? selectedCharacters : availableCharacters;
  const spellbookData = useSelectedCharactersSpellbooks(allCharactersForSpellbook);
  const characterSpellbook = spellbookData.spells;
  const spellToCharacters = spellbookData.spellToCharacters;
  const spellToCharacterSources = spellbookData.spellToCharacterSources;
  const showSpellbookOnly = selectedCharacters.length > 0;

  const [itemExcludeCharacters, setItemExcludeCharacters] = dc.useState([]); // Characters whose item spells are excluded
  const [filterSearch, setFilterSearch] = dc.useState('');
  const [filterClass, setFilterClass] = dc.useState([]);
  const [filterLevel, setFilterLevel] = dc.useState('');
  const [filterLevelMin, setFilterLevelMin] = dc.useState('');
  const [filterLevelMax, setFilterLevelMax] = dc.useState('');
  const [filterSchool, setFilterSchool] = dc.useState([]);
  const [filterComponents, setFilterComponents] = dc.useState({}); // { V: 'include'|'exclude', S: ..., M: ... }
  const [filtersShown, setFiltersShown] = dc.useState(false);
  const [filterConcentration, setFilterConcentration] = dc.useState('');
  const [filterRitual, setFilterRitual] = dc.useState('');
  const [filterRange, setFilterRange] = dc.useState('');
  const [materialCostThreshold, setMaterialCostThreshold] = dc.useState('100');
  const [materialCostMode, setMaterialCostMode] = dc.useState('gt'); // 'gt' or 'lt'

  const allComponents = ["V", "S", "M"];
  const componentNames = { V: "Verbal", S: "Somatic", M: "Material" };
  const componentPropMap = { V: 'verbal', S: 'somatic', M: 'material' };

  // Helper function to extract GP cost from material_desc
  function extractGoldCost(materialDesc) {
    if (!materialDesc) return null;
    // Match patterns like "300 GP", "1,000+ GP", "300 gp", "worth 1,000 gp", etc.
    // Remove commas from numbers first
    const match = String(materialDesc).match(/([\d,]+)\+?\s*(?:GP|gp)/i);
    if (!match) return null;
    // Remove commas and parse
    const numStr = match[1].replace(/,/g, '');
    return parseInt(numStr, 10);
  }
  
  const [sortBy, setSortBy] = dc.useState('name'); // 'name', 'level', or 'school'

  const allClassesRaw = Array.from(
    new Set(
      allPages
        .flatMap(p => arr(p.value("classes")))
        .filter(Boolean)
    )
  ).sort();
  // Extract main classes (without subclass in parentheses)
  const mainClasses = Array.from(new Set(allClassesRaw.map(c => c.replace(/\s*\(.*\)$/, '')))).sort();
  // Get subclasses for a given main class
  const getSubclasses = (main) => allClassesRaw.filter(c => c !== main && c.startsWith(main + ' ('));
  const allSchools = Array.from(
    new Set(
      allPages
        .map(p => p.value("school"))
        .filter(Boolean)
    )
  ).sort();

  // Clear and toggle functions for enhanced filter controls
  const clearFilterClass = () => setFilterClass([]);
  const toggleFilterClass = () => setFilterClass(mainClasses.filter(c => !filterClass.includes(c)));
  
  const clearFilterSchool = () => setFilterSchool([]);
  const toggleFilterSchool = () => setFilterSchool(allSchools.filter(s => !filterSchool.includes(s)));
  
  const clearFilterComponents = () => setFilterComponents({});
  const toggleFilterComponents = () => {
    const hasAny = Object.keys(filterComponents).length > 0;
    if (hasAny) { setFilterComponents({}); }
    else { setFilterComponents(Object.fromEntries(allComponents.map(c => [c, 'include']))); }
  };
  
  const clearSelectedCharacters = () => setSelectedCharacters([]);
  const toggleSelectedCharacters = () => setSelectedCharacters(availableCharacters.filter(c => !selectedCharacters.includes(c)));

  const filteredPages = allPages.filter(page => {
    const fm = page.$frontmatter || {};

    if (page.$path === `${SPELL_LOCATION}/spells.md`) return false;
    if (showSpellbookOnly && !characterSpellbook.includes(page.$name)) return false;
    // Per-character item spell filter: hide spells where all remaining characters are item-excluded
    if (itemExcludeCharacters.length > 0 && showSpellbookOnly) {
      const sources = spellToCharacterSources.get(page.$name);
      const characters = spellToCharacters.get(page.$name) || [];
      // Remove item-sourced entries for excluded characters
      const remaining = characters.filter(ch => {
        if (!itemExcludeCharacters.includes(ch)) return true;
        return !(sources && sources.get(ch) === 'Item');
      });
      if (remaining.length === 0) return false;
    }
    const spellName = getFMVal(fm, 'name') || page.$name || '';
    if (filterSearch && !matchesSearch(spellName, filterSearch))
      return false;
    const spellClasses = getFMVal(fm, 'classes') || [];
    if (filterClass.length > 0) {
      const classArr = Array.isArray(spellClasses) ? spellClasses : [spellClasses];
      // Check if any selected filter matches a spell class (main class matches subclass variants too)
      const matchesClass = filterClass.some(cls =>
        classArr.some(sc => sc === cls || sc.startsWith(cls + ' ('))
      );
      if (!matchesClass) return false;
    }
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
    const compEntries = Object.entries(filterComponents);
    if (compEntries.length > 0) {
      for (const [short, mode] of compEntries) {
        const has = getFMVal(fm, componentPropMap[short]) === true;
        if (mode === 'include' && !has) return false;
        if (mode === 'exclude' && has) return false;
      }
    }
    return true;
  });

// Apply sorting after filtering
filteredPages.sort((a, b) => {
  switch (sortBy) {
    case 'level':
      // By level (numeric, then fallback to name)
      let lA = Number(a.value("levelint") ?? a.value("level") ?? 0);
      let lB = Number(b.value("levelint") ?? b.value("level") ?? 0);
      if (lA !== lB) return lA - lB;
      // By name/alias as fallback
      let nA = (a.value("name") ?? a.$name ?? "").toLowerCase();
      let nB = (b.value("name") ?? b.$name ?? "").toLowerCase();
      return nA.localeCompare(nB);
    case 'school':
      // By school, then by name
      let sA = (a.value("school") ?? "").toLowerCase();
      let sB = (b.value("school") ?? "").toLowerCase();
      if (sA !== sB) return sA.localeCompare(sB);
      // By name/alias as fallback
      let nASchool = (a.value("name") ?? a.$name ?? "").toLowerCase();
      let nBSchool = (b.value("name") ?? b.$name ?? "").toLowerCase();
      return nASchool.localeCompare(nBSchool);
    default:
      // Default: sort by name/alias
      let nADefault = (a.value("name") ?? a.$name ?? "").toLowerCase();
      let nBDefault = (b.value("name") ?? b.$name ?? "").toLowerCase();
      return nADefault.localeCompare(nBDefault);
  }
});

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
    // Always show Characters column to display which party members know each spell
    {
      id: "Characters",
      value: p => {
        const fileName = p.$name;
        const allCharacters = spellToCharacters.get(fileName) || [];
        const sources = spellToCharacterSources.get(fileName);
        // Filter out item-sourced entries for characters with item exclusion enabled
        const characters = allCharacters.filter(ch => {
          if (!itemExcludeCharacters.includes(ch)) return true;
          return !(sources && sources.get(ch) === 'Item');
        });
        if (characters.length === 0) return "";
        return (
          <span>
            {characters.sort().map((charName, i) => {
              const source = sources && sources.get(charName);
              const isItem = source === "Item";
              return (
                <span key={charName}>
                  {i > 0 ? ", " : ""}
                  <span style={isItem ? "color: #ff9800; font-style: italic;" : undefined}>
                    {charName}
                    {isItem && <span style="font-size: 0.75em; opacity: 0.85;" title={`Granted by item`}> (Item)</span>}
                  </span>
                </span>
              );
            })}
          </span>
        );
      }
    },
    {
  id: "Level",
  value: p => (
    <span style="display:inline-block; min-width:90px; text-align:left;">
      {p.value("level")}
    </span>
  )
},

    {
      id: "School",
      value: p => {
        const school = p.value("school") || 'Unknown';
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
    {
      id: "Components",
      value: p => {
        const fm = p.$frontmatter || {};
        const materialDesc = getFMVal(fm, 'material_desc');
        const goldCost = extractGoldCost(materialDesc);

        const componentsText = typeof p.value("components") === "string"
          ? p.value("components")
          : arr(p.value("components")).join(', ');

        // Determine if we should highlight based on material cost
        let shouldHighlight = false;
        if (materialCostThreshold && materialCostMode && goldCost !== null) {
          const threshold = Number(materialCostThreshold);
          if (materialCostMode === 'gt' && goldCost > threshold) {
            shouldHighlight = true;
          } else if (materialCostMode === 'lt' && goldCost < threshold) {
            shouldHighlight = true;
          }
        }

        return shouldHighlight
          ? <span style="color: #ff9800; font-weight: 600;">{componentsText}</span>
          : componentsText;
      }
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
      <div style="display: flex; gap: 0.75em; align-items: center;">
        <input
          type="search"
          placeholder="Search..."
          value={filterSearch}
          oninput={e => setFilterSearch(e.target.value)}
          style="flex-grow: 1;"
        />
        {showFilters && (
          <div style="display: flex; gap: 0.2em; align-items: center;">
            {[['name', 'A-Z'], ['level', 'Lvl'], ['school', 'Sch']].map(([key, label]) => (
              <button
                key={key}
                onclick={() => setSortBy(key)}
                style={`
                  padding: 0.4em 0.8em;
                  border: 1px solid ${sortBy === key ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                  border-radius: 0.25em;
                  background-color: ${sortBy === key ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                  color: ${sortBy === key ? '#4fc3f7' : 'var(--text-muted)'};
                  cursor: pointer;
                  font-size: 0.9em;
                  transition: all 0.2s ease;
                `}
                title={`Sort by ${key}`}
              >
                {label}
              </button>
            ))}
          </div>
        )}
        {showFilters && (
          <button
            style="font-weight: 600; padding: 0 0.8em;"
            title="Quick: Only show Wizard spells"
            onclick={() => {
              setFilterClass(['Wizard']);
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
              setFilterConcentration('');
              setFilterRitual('');
              setFilterRange('');
              setMaterialCostThreshold('');
              setMaterialCostMode('');
              clearSelectedCharacters();
              setItemExcludeCharacters([]);
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
              {availableCharacters.map(c => {
                const isSelected = selectedCharacters.includes(c);
                const isItemExcluded = itemExcludeCharacters.includes(c);
                return (
                  <div key={c} style="display: flex; gap: 0.3em; align-items: stretch;">
                    <button
                      onclick={() => setSelectedCharacters(
                        isSelected
                          ? selectedCharacters.filter(x => x !== c)
                          : [...selectedCharacters, c]
                      )}
                      style={`
                        flex: 1;
                        padding: 0.3em 0.5em;
                        border: 1px solid ${isSelected ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                        border-radius: 0.25em;
                        background-color: ${isSelected ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                        color: ${isSelected ? '#4fc3f7' : 'var(--text-normal)'};
                        cursor: pointer;
                        font-size: 0.8em;
                        transition: all 0.2s ease;
                        text-align: left;
                      `}
                    >
                      {c.replace(/_/g, ' ')}
                    </button>
                    {isSelected && (
                      <button
                        onclick={(e) => {
                          e.stopPropagation();
                          setItemExcludeCharacters(
                            isItemExcluded
                              ? itemExcludeCharacters.filter(x => x !== c)
                              : [...itemExcludeCharacters, c]
                          );
                        }}
                        title={isItemExcluded ? "Item spells hidden - click to show" : "Item spells shown - click to hide"}
                        style={`
                          padding: 0.2em 0.4em;
                          border: 1px solid ${isItemExcluded ? '#ff9800' : 'var(--background-modifier-border, #444)'};
                          border-radius: 0.25em;
                          background-color: ${isItemExcluded ? 'rgba(255, 152, 0, 0.15)' : 'var(--background-primary, #1e1e1e)'};
                          color: ${isItemExcluded ? '#ff9800' : 'var(--text-muted)'};
                          cursor: pointer;
                          font-size: 0.7em;
                          transition: all 0.2s ease;
                          display: flex;
                          align-items: center;
                          min-width: 28px;
                          justify-content: center;
                        `}
                      >
                        <dc.Icon icon={isItemExcluded ? "package-x" : "package"} size={14} />
                      </button>
                    )}
                  </div>
                );
              })}
            </div>
          </SpellQuerySetting>
          <SpellQuerySetting
            title="Class"
            icon="lucide-users"
            onToggle={toggleFilterClass}
            onClear={clearFilterClass}
          >
            <div style="display: flex; flex-direction: column; gap: 0.2em;">
              {mainClasses.map(main => {
                const isSelected = filterClass.includes(main);
                const subs = getSubclasses(main);
                const selectedSubs = filterClass.filter(c => subs.includes(c));
                return (
                  <div key={main}>
                    <button
                      onclick={() => {
                        if (isSelected) {
                          // Deselect main class and all its subclasses
                          setFilterClass(filterClass.filter(x => x !== main && !subs.includes(x)));
                        } else {
                          setFilterClass([...filterClass, main]);
                        }
                      }}
                      style={`
                        width: 100%;
                        padding: 0.3em 0.5em;
                        border: 1px solid ${isSelected ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                        border-radius: 0.25em;
                        background-color: ${isSelected ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                        color: ${isSelected ? '#4fc3f7' : 'var(--text-normal)'};
                        cursor: pointer;
                        font-size: 0.8em;
                        transition: all 0.2s ease;
                        text-align: left;
                      `}
                    >
                      {main}{subs.length > 0 ? ` (${subs.length})` : ''}
                    </button>
                    {isSelected && subs.length > 0 && (
                      <div style="margin-left: 1em; margin-top: 0.2em; margin-bottom: 0.3em; display: flex; flex-direction: column; gap: 0.15em;">
                        {subs.map(sub => {
                          const subName = sub.replace(main + ' ', '');
                          const isSubSelected = selectedSubs.includes(sub);
                          return (
                            <button
                              key={sub}
                              onclick={() => setFilterClass(
                                isSubSelected
                                  ? filterClass.filter(x => x !== sub)
                                  : [...filterClass, sub]
                              )}
                              style={`
                                padding: 0.2em 0.4em;
                                border: 1px solid ${isSubSelected ? '#ff9800' : 'var(--background-modifier-border, #444)'};
                                border-radius: 0.2em;
                                background-color: ${isSubSelected ? 'rgba(255, 152, 0, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                                color: ${isSubSelected ? '#ff9800' : 'var(--text-muted)'};
                                cursor: pointer;
                                font-size: 0.75em;
                                transition: all 0.2s ease;
                                text-align: left;
                              `}
                            >
                              {subName}
                            </button>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
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
            title="Level & Components"
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
            
            <div style="font-weight: 500; margin-bottom: 0.4em;">Components Filter <span style="color: var(--text-muted); font-size: 0.75em; font-weight: 400;">click to cycle: off / require / exclude</span></div>
            <div style="display: flex; flex-wrap: wrap; gap: 0.2em; margin-bottom: 1em;">
              {allComponents.map(comp => {
                const mode = filterComponents[comp]; // undefined, 'include', or 'exclude'
                const isInclude = mode === 'include';
                const isExclude = mode === 'exclude';
                return (
                  <button
                    key={comp}
                    onclick={() => {
                      const next = { ...filterComponents };
                      if (!mode) next[comp] = 'include';
                      else if (mode === 'include') next[comp] = 'exclude';
                      else delete next[comp];
                      setFilterComponents(next);
                    }}
                    style={`
                      padding: 0.25em 0.4em;
                      border: 1px solid ${isInclude ? '#4fc3f7' : isExclude ? '#ff9800' : 'var(--background-modifier-border, #444)'};
                      border-radius: 0.2em;
                      background-color: ${isInclude ? 'rgba(79, 195, 247, 0.1)' : isExclude ? 'rgba(255, 152, 0, 0.15)' : 'var(--background-primary, #1e1e1e)'};
                      color: ${isInclude ? '#4fc3f7' : isExclude ? '#ff9800' : 'var(--text-normal)'};
                      cursor: pointer;
                      font-size: 0.75em;
                      transition: all 0.2s ease;
                      min-width: 60px;
                      text-align: center;
                    `}
                    title={isInclude ? 'Required - click to exclude' : isExclude ? 'Excluded - click to clear' : 'Click to require'}
                  >
                    {isExclude ? '✗ ' : isInclude ? '✓ ' : ''}{componentNames[comp]}
                  </button>
                );
              })}
            </div>

            <div style="font-weight: 500; margin-bottom: 0.4em;">Material Cost Highlighting</div>
            <div style="display: flex; gap: 0.4em; align-items: center; margin-bottom: 0.5em;">
              <input
                type="number"
                min="0"
                step="10"
                value={materialCostThreshold}
                onchange={e => setMaterialCostThreshold(e.target.value)}
                placeholder="GP threshold"
                style="max-width: 100px;"
              />
              <span style="color: var(--text-muted); font-size: 0.8em;">GP</span>
            </div>
            <div style="display: flex; flex-direction: column; gap: 0.2em; margin-bottom: 1em;">
              <button
                onclick={() => setMaterialCostMode('')}
                style={`
                  padding: 0.25em 0.4em;
                  border: 1px solid ${materialCostMode === '' ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                  border-radius: 0.2em;
                  background-color: ${materialCostMode === '' ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                  color: ${materialCostMode === '' ? '#4fc3f7' : 'var(--text-normal)'};
                  cursor: pointer;
                  font-size: 0.75em;
                  transition: all 0.2s ease;
                `}
              >
                No Highlighting
              </button>
              <button
                onclick={() => setMaterialCostMode('gt')}
                style={`
                  padding: 0.25em 0.4em;
                  border: 1px solid ${materialCostMode === 'gt' ? '#ff9800' : 'var(--background-modifier-border, #444)'};
                  border-radius: 0.2em;
                  background-color: ${materialCostMode === 'gt' ? 'rgba(255, 152, 0, 0.15)' : 'var(--background-primary, #1e1e1e)'};
                  color: ${materialCostMode === 'gt' ? '#ff9800' : 'var(--text-normal)'};
                  cursor: pointer;
                  font-size: 0.75em;
                  transition: all 0.2s ease;
                `}
              >
                {'>'} Greater Than
              </button>
              <button
                onclick={() => setMaterialCostMode('lt')}
                style={`
                  padding: 0.25em 0.4em;
                  border: 1px solid ${materialCostMode === 'lt' ? '#ff9800' : 'var(--background-modifier-border, #444)'};
                  border-radius: 0.2em;
                  background-color: ${materialCostMode === 'lt' ? 'rgba(255, 152, 0, 0.15)' : 'var(--background-primary, #1e1e1e)'};
                  color: ${materialCostMode === 'lt' ? '#ff9800' : 'var(--text-normal)'};
                  cursor: pointer;
                  font-size: 0.75em;
                  transition: all 0.2s ease;
                `}
              >
                {'<'} Less Than
              </button>
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

      <div style="display: flex; gap: 1rem; margin-bottom: 0.5em; margin-top: 1em; font-size: 0.85rem; color: var(--text-muted);">
        <span>Showing {filteredPages.length} of {allPages.length} spells</span>
      </div>

      <dc.VanillaTable columns={columns} rows={filteredPages} paging={paging} />
    </>
  );
}

// Helper function for school colors
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
