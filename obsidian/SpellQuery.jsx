// === Spell Query for D&D Character Sheets ===
const CHARACTER_DIR = "Campaign/Parties/Characters/Party 1";

function arr(x) {
  if (!x) return [];
  if (Array.isArray(x)) return x;
  return [x];
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

function SpellFilter({ title, icon, children }) {
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
        <span>{title}</span>
      </div>
      <div style="display: flex; flex-direction: column; gap: 0.4em;">
        {children}
      </div>
    </div>
  );
}

function SpellQuery({ characterName, fileName, paging = 50 }) {
  let character;
  let allChars = [];

  // Always load character pages (needed for both fileName and characterName modes)
  const allCharsQuery = dc.useQuery(`@page and path("${CHARACTER_DIR}")`);
  const allCharsRaw = dc.useArray(allCharsQuery) || [];
  
  if (fileName) {
    // Find the specific file by name
    const fileNameBase = fileName.replace('.md', '');
    character = allCharsRaw.find(page => 
      page && (page.$name === fileNameBase || page.$name === fileName)
    );
    allChars = [];
  } else if (characterName) {
    // Filter and search for character by name
    const allCharsFiltered = allCharsRaw.filter(page => {
      return page && page.$path && typeof page.$path === 'string' && !page.$path.includes('/Archive/');
    });

    allChars = allCharsFiltered;

    character = allChars.find(page => page && page.$name === characterName)
      || allChars.find(page => characterName.includes('(') && page?.$name === characterName.split('(')[0].trim())
      || allChars.find(page => {
        const fmName = page?.$frontmatter?.character_name?.value || page?.$frontmatter?.character_name;
        return fmName === characterName;
      })
      || allChars.find(page => {
        const pageName = page?.$name?.toLowerCase() || '';
        const searchName = characterName.toLowerCase();
        return pageName.includes(searchName.split('(')[0].trim()) || searchName.includes(pageName);
      });
  }

  if (fileName) {
    console.debug("Using fileName:", fileName);
  } else {
    console.debug("Searching for characterName:", characterName);
  }
  console.debug("Found character:", character?.$name, "at path:", character?.$path);

  const [filterSearch, setFilterSearch] = dc.useState('');
  const [filterLevel, setFilterLevel] = dc.useState('');
  const [filterSchool, setFilterSchool] = dc.useState([]);
  const [filterComponents, setFilterComponents] = dc.useState([]);
  const [filterConcentration, setFilterConcentration] = dc.useState('');
  const [filterRitual, setFilterRitual] = dc.useState('');
  const [filterPrepared, setFilterPrepared] = dc.useState('');
  const [filtersShown, setFiltersShown] = dc.useState(false);
  const [sortBy, setSortBy] = dc.useState('name');

  let spellData = [];
  if (character?.$frontmatter?.spell_data) {
    const raw = dc.useArray(character.$frontmatter.spell_data, arr => arr);
    spellData = Array.isArray(raw) && raw.length && raw[0]?.key === 'spell_data' ? raw[0]?.value : raw;
  }

  if (!character) {
    return (
      <div style="padding: 1em; border: 1px solid #f44336; border-radius: 0.5em; background-color: rgba(244, 67, 54, 0.1);">
        <h3>Character Not Found</h3>
        <p>{fileName ? `Could not find file: ${fileName}` : `Could not find character: ${characterName}`}</p>
      </div>
    );
  }

  if (!spellData?.length) {
    return (
      <div style="padding: 1em; border: 1px solid #ff9800; border-radius: 0.5em; background-color: rgba(255, 152, 0, 0.1);">
        <h3>No Spell Data</h3>
        <p>Character <strong>{character.$name}</strong> found at <code>{character.$path}</code></p>
        <p><em>Make sure the frontmatter contains valid <code>spell_data</code>.</em></p>
        <details><summary>Frontmatter</summary><pre>{JSON.stringify(character.$frontmatter, null, 2)}</pre></details>
      </div>
    );
  }

  const allSchools = Array.from(new Set(spellData.map(spell => spell.school).filter(Boolean))).sort();
  const allComponents = ['V', 'S', 'M'];
  const componentNames = { V: 'Verbal', S: 'Somatic', M: 'Material' };

  const filteredSpells = spellData.filter(spell => {
    if (filterSearch && !spell?.name?.toLowerCase().includes(filterSearch.toLowerCase())) return false;
    if (filterLevel && spell?.level !== parseInt(filterLevel)) return false;
    if (filterSchool.length && !filterSchool.includes(spell?.school)) return false;
    if (filterComponents.length && !filterComponents.every(c => spell?.components?.includes(c))) return false;
    if (filterConcentration && spell?.concentration !== (filterConcentration === 'true')) return false;
    if (filterRitual && spell?.ritual !== (filterRitual === 'true')) return false;
    if (filterPrepared && spell?.prepared !== (filterPrepared === 'true')) return false;
    return true;
  });

  filteredSpells.sort((a, b) => {
    if (sortBy === 'level') return a.level - b.level || a.name.localeCompare(b.name);
    if (sortBy === 'school') return a.school.localeCompare(b.school) || a.name.localeCompare(b.name);
    return a.name.localeCompare(b.name);
  });

  const isWizard = character?.$frontmatter?.class?.value === 'Wizard' || character?.$frontmatter?.class === 'Wizard';

  const columns = [
    {
      id: "Name",
      value: spell => (
        <span style={spell?.prepared ? "font-weight: bold; color: #4fc3f7;" : undefined}>
          {spell?.name || 'Unknown Spell'}
        </span>
      )
    },
    {
      id: "Level",
      value: spell => spell.level === 0 ? "Cantrip" : `${spell.level}${getOrdinalSuffix(spell.level)}`
    },
    {
      id: "School",
      value: spell => (
        <span style={`
          padding: 2px 6px;
          border-radius: 3px;
          font-size: 0.85em;
          background-color: ${getSchoolColor(spell.school)};
          color: white;
        `}>
          {spell.school}
        </span>
      )
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
    }
  ];

  if (isWizard) {
    columns.push({
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
        <button class="primary" onclick={() => setFiltersShown(!filtersShown)}>
          ⚙ Filters
        </button>
        <button onclick={() => {
          setFilterSearch('');
          setFilterLevel('');
          setFilterSchool([]);
          setFilterComponents([]);
          setFilterConcentration('');
          setFilterRitual('');
          setFilterPrepared('');
        }}>
          Clear
        </button>
      </div>

      {filtersShown && (
        <SpellFilters>
          <SpellFilter title="Level & School" icon="lucide-book">
            <div style="margin-bottom: 1em;">
              <div style="font-weight: 500;">Spell Level</div>
              <select value={filterLevel} onchange={e => setFilterLevel(e.target.value)}>
                <option value="">All Levels</option>
                {[...Array(10).keys()].map(i => (
                  <option value={i}>{i === 0 ? "Cantrip" : `${i} Level`}</option>
                ))}
              </select>
            </div>
            <div>
              <div style="font-weight: 500;">School</div>
              {allSchools.map(school => (
                <label style="display: block">
                  <input type="checkbox" checked={filterSchool.includes(school)} onchange={e =>
                    setFilterSchool(e.target.checked
                      ? [...filterSchool, school]
                      : filterSchool.filter(s => s !== school))
                  } /> {school}
                </label>
              ))}
            </div>
          </SpellFilter>
          <SpellFilter title="Components & Properties" icon="lucide-zap">
            <div>
              <div style="font-weight: 500;">Components</div>
              {allComponents.map(c => (
                <label style="display: block">
                  <input type="checkbox" checked={filterComponents.includes(c)} onchange={e =>
                    setFilterComponents(e.target.checked
                      ? [...filterComponents, c]
                      : filterComponents.filter(x => x !== c))
                  } /> {componentNames[c]}
                </label>
              ))}
            </div>
            <div>
              <div style="font-weight: 500;">Concentration</div>
              <select value={filterConcentration} onchange={e => setFilterConcentration(e.target.value)}>
                <option value="">All</option>
                <option value="true">Only Concentration</option>
                <option value="false">Exclude Concentration</option>
              </select>
            </div>
            <div>
              <div style="font-weight: 500;">Ritual</div>
              <select value={filterRitual} onchange={e => setFilterRitual(e.target.value)}>
                <option value="">All</option>
                <option value="true">Only Ritual</option>
                <option value="false">Exclude Ritual</option>
              </select>
            </div>
          </SpellFilter>
          {isWizard && (
            <SpellFilter title="Preparation" icon="lucide-check">
              <div>
                <div style="font-weight: 500;">Prepared</div>
                <select value={filterPrepared} onchange={e => setFilterPrepared(e.target.value)}>
                  <option value="">All</option>
                  <option value="true">Prepared Only</option>
                  <option value="false">Unprepared Only</option>
                </select>
              </div>
            </SpellFilter>
          )}
        </SpellFilters>
      )}

      <div style="margin-bottom: 1em; font-size: 0.9em; color: var(--text-muted);">
        Showing {filteredSpells.length} of {spellData.length} spells
      </div>

      <dc.VanillaTable columns={columns} rows={filteredSpells} paging={paging} />
    </>
  );
}

// Helpers
function getOrdinalSuffix(n) {
  const j = n % 10, k = n % 100;
  if (j === 1 && k !== 11) return "st";
  if (j === 2 && k !== 12) return "nd";
  if (j === 3 && k !== 13) return "rd";
  return "th";
}

function getSchoolColor(school) {
  const map = {
    Abjuration: '#2196f3',
    Conjuration: '#4caf50',
    Divination: '#ff9800',
    Enchantment: '#e91e63',
    Evocation: '#f44336',
    Illusion: '#9c27b0',
    Necromancy: '#424242',
    Transmutation: '#795548',
  };
  return map[school] || '#757575';
}

return { SpellQuery };
