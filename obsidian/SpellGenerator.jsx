// === Constants and Helpers ===
const CHARACTER_DIR = "Campaign/Parties/Characters/Party 1";
const CHARACTER_NAME = "Ilarion Veles";
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

function useIlarionSpellbook() {
  const chars = dc.useArray(dc.useQuery(`@page and path("${CHARACTER_DIR}")`), arr => arr);
  const ilarion = chars.find(page => page.$name === CHARACTER_NAME);

  let spells = [];
  if (ilarion) {
    let raw = null;
    if (typeof ilarion.value === "function") raw = ilarion.value(SPELLBOOK_YAML_KEY);
    if (!raw && ilarion.frontmatter) raw = ilarion.frontmatter[SPELLBOOK_YAML_KEY];
    if (!raw && ilarion.$frontmatter) raw = ilarion.$frontmatter[SPELLBOOK_YAML_KEY];

    // DEBUG: See what you actually get from YAML
    console.debug("Ilarion spellbook raw value:", raw);

    if (raw) {
      if (Array.isArray(raw)) {
        spells = raw.map(extractSpellFileName).filter(Boolean);
      } else {
        const single = extractSpellFileName(raw);
        if (single) spells = [single];
      }
    }
  }
  // DEBUG: Output the normalized spell list
  console.debug("Ilarion spellbook (normalized):", spells);
  return spells;
}


function SpellQuerySettings({ children }) {
  return (
    <div
      style="
        display: grid;
        grid-template-columns: repeat(3, 1fr);
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
function SpellQuerySetting({ title, icon, children }) {
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
          gap: 0.5em;
        "
      >
        <dc.Icon icon={icon} />
        <span>{title}</span>
      </div>
      <div style="display: flex; flex-direction: column; gap: 0.4em; overflow-y: auto;">
        {children}
      </div>
    </div>
  );
}

function SpellQuery({ showFilters = true, paging = 30 }) {
  const query = dc.useQuery(`@page and path("${SPELL_LOCATION}")`);
  const allPages = dc.useArray(query, arr => arr.sort(page => [page.value("name")], 'asc'));

  const ilarionSpellbook = useIlarionSpellbook();
  const [showSpellbookOnly, setShowSpellbookOnly] = dc.useState(false);

  const [filterSearch, setFilterSearch] = dc.useState('');
  const [filterClass, setFilterClass] = dc.useState([]);
  const [filterLevel, setFilterLevel] = dc.useState('');
  const [filterSchool, setFilterSchool] = dc.useState([]);
  const [filterComponents, setFilterComponents] = dc.useState([]);
  const [filtersShown, setFiltersShown] = dc.useState(false);
  const [filterClassSearch, setFilterClassSearch] = dc.useState('');
  const [filterConcentration, setFilterConcentration] = dc.useState('');
  const [filterRitual, setFilterRitual] = dc.useState('');

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

  const filteredPages = allPages.filter(page => {
    const fm = page.$frontmatter || {};

    if (page.$path === `${SPELL_LOCATION}/spells.md`) return false;
    if (showSpellbookOnly && !ilarionSpellbook.includes(page.$name)) return false;
    const spellName = (getFMVal(fm, 'name') || page.$name || '').toLowerCase();
    if (filterSearch && !spellName.includes(filterSearch.toLowerCase()))
      return false;
    const spellClasses = getFMVal(fm, 'classes') || [];
    if (
      filterClass.length > 0 &&
      !filterClass.some(cls => Array.isArray(spellClasses) ? spellClasses.includes(cls) : spellClasses === cls)
    )
      return false;
    if (
      filterLevel &&
      Number(getFMVal(fm, 'levelint')) !== Number(filterLevel)
    )
      return false;
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
        const href = `obsidian://open?file=${encodeURIComponent(p.$path)}`;
        const inBook = ilarionSpellbook.includes(fileName);
        return (
          <a
            href={href}
            style={inBook
              // Softer, blue, bold, NO underline or background
              ? "font-weight: bold; color: #4fc3f7; text-decoration: none;"
              : undefined}
            title={inBook ? "Ilarion knows this spell" : ""}
          >
            {displayName}
          </a>
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
              setFilterClass([]);
              setFilterLevel('');
              setFilterSearch('');
              setFilterSchool([]);
              setFilterComponents([]);
              setFilterClassSearch('');
              setFilterConcentration('');
              setFilterRitual('');
              setShowSpellbookOnly(false);
            }}
          >
            Clear All
          </button>
        )}
      </div>

      {filtersShown && (
        <SpellQuerySettings>
          <SpellQuerySetting title="Class" icon="lucide-users">
            <input
              type="search"
              placeholder="Type to filter classes..."
              value={filterClassSearch}
              oninput={e => setFilterClassSearch(e.target.value)}
              style="margin-bottom: 0.5em;"
            />
            <div style="display: flex; flex-direction: column; gap: 0.25em; min-height: 260px; max-height: 260px; overflow-y: auto;">
              {allClasses
                .filter(c => c.toLowerCase().includes(filterClassSearch.toLowerCase()))
                .map(c => (
                  <label style="display: block" key={c}>
                    <input
                      type="checkbox"
                      checked={filterClass.includes(c)}
                      onchange={e =>
                        setFilterClass(
                          e.target.checked
                            ? [...filterClass, c]
                            : filterClass.filter(x => x !== c)
                        )
                      }
                    />{' '}
                    {c}
                  </label>
                ))}
            </div>
          </SpellQuerySetting>
          <SpellQuerySetting title="School & Components" icon="lucide-folder">
            <div style="margin-bottom: 1em;">
              <div style="font-weight: 500; margin-bottom: 0.25em;">School</div>
              {allSchools.map(s => (
                <label style="display: block" key={s}>
                  <input
                    type="checkbox"
                    checked={filterSchool.includes(s)}
                    onchange={e =>
                      setFilterSchool(
                        e.target.checked
                          ? [...filterSchool, s]
                          : filterSchool.filter(x => x !== s)
                      )
                    }
                  />{' '}
                  {s}
                </label>
              ))}
            </div>
            <div>
              <div style="font-weight: 500; margin-bottom: 0.25em;">Components</div>
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
            </div>
          </SpellQuerySetting>
          <SpellQuerySetting title="Level, Concentration & Ritual" icon="lucide-hash">
            <div style="margin-bottom: 1em;">
              <div style="font-weight: 500; margin-bottom: 0.25em;">Level</div>
              <input
                type="number"
                min="0"
                max="9"
                value={filterLevel}
                onchange={e => setFilterLevel(e.target.value)}
                style="max-width: 75px;"
              />
            </div>
            <div style="margin-bottom: 1em;">
              <div style="font-weight: 500; margin-bottom: 0.25em;">Concentration</div>
              <select
                value={filterConcentration}
                onchange={e => setFilterConcentration(e.target.value)}
                style="max-width: 120px;"
              >
                <option value="">---</option>
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            </div>
            <div style="margin-bottom: 1em;">
              <div style="font-weight: 500; margin-bottom: 0.25em;">Ritual</div>
              <select
                value={filterRitual}
                onchange={e => setFilterRitual(e.target.value)}
                style="max-width: 120px;"
              >
                <option value="">---</option>
                <option value="true">Yes</option>
                <option value="false">No</option>
              </select>
            </div>
			

            {/* Spellbook filter, in-box and visually attached */}
            <div style="margin-top: 0.8em; padding-top: 0.6em; border-top: 1px solid var(--background-modifier-border, #444); padding-left: 0.4em;">
  <label style="display: flex; align-items: center; gap: 0.45em; margin-bottom: 0.5em;">
    <input
      type="checkbox"
      checked={showSpellbookOnly}
      onchange={e => setShowSpellbookOnly(e.target.checked)}
      style="transform: scale(1.15);"
    />
    <span style="font-size: 1em;">Show only Ilarion’s spellbook</span>
  </label>
  <label style="display: flex; align-items: center; gap: 0.45em;">
    <input
      type="checkbox"
      checked={sortByLevel}
      onchange={e => setSortByLevel(e.target.checked)}
      style="transform: scale(1.15);"
    />
    <span style="font-size: 1em;">Sort by spell level</span>
  </label>
</div>

          </SpellQuerySetting>
        </SpellQuerySettings>
      )}

      <dc.VanillaTable columns={columns} rows={filteredPages} paging={paging} />
    </>
  );
}

return { SpellQuery };
