// ══════════════════════════════════════════════════════════════════════════════
// NPC HUB - NPC lookup and quick reference
// ══════════════════════════════════════════════════════════════════════════════
// Displays all NPCs from the campaign with filterable, sortable table.
// Data extracted from frontmatter fields (location, organization, occupation, etc).

// ── Helper Functions ─────────────────────────────────────────────────────────

function toArray(val) {
    if (!val) return [];
    if (Array.isArray(val)) return val;
    if (typeof val === 'object' && val.values) return Array.from(val.values());
    if (typeof val[Symbol.iterator] === 'function') return Array.from(val);
    return [val];
}

function getVal(obj, key) {
    if (!obj) return null;
    const val = obj[key];
    if (val === undefined || val === null) return null;
    if (typeof val === 'object' && val.value !== undefined) return val.value;
    return val;
}

// Strip wiki-link syntax: "[[Saltmarsh]]" -> "Saltmarsh", "[[Place|Display]]" -> "Display"
function stripLinks(val) {
    if (!val) return '';
    const str = String(val);
    return str.replace(/\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]/g, (_, target, display) => display || target);
}

function matchesSearch(target, searchQuery) {
    if (!target || !searchQuery) return false;
    const targetLower = target.toLowerCase();
    const searchWords = searchQuery.toLowerCase().trim().split(/\s+/).filter(w => w.length > 0);
    return searchWords.every(word => targetLower.includes(word));
}

// ── Layout Components ────────────────────────────────────────────────────────

function NPCQuerySettings({ children }) {
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

function NPCQuerySetting({ title, icon, children, onToggle, onClear }) {
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
                        style="cursor: pointer; opacity: 0.7;"
                        title="Toggle selection"
                    >
                        <dc.Icon icon="toggle-left" />
                    </span>
                )}
                {onClear && (
                    <span
                        onclick={onClear}
                        style="cursor: pointer; opacity: 0.7;"
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

// ── Display Components ───────────────────────────────────────────────────────

function NPCLink({ npc }) {
    const encodedPath = encodeURIComponent(npc.filePath);
    return (
        <a
            className="internal-link"
            data-href={npc.filePath}
            href={`obsidian://open?file=${encodedPath}`}
            style="color: var(--text-accent); text-decoration: none; cursor: pointer;"
        >
            {npc.name}
        </a>
    );
}

function ConditionBadge({ condition }) {
    if (!condition) return <span style="color: var(--text-muted);">{'\u2014'}</span>;
    const colors = {
        'healthy': { bg: 'rgba(76, 175, 80, 0.15)', color: '#4caf50' },
        'dead': { bg: 'rgba(244, 67, 54, 0.15)', color: '#f44336' },
        'injured': { bg: 'rgba(255, 152, 0, 0.15)', color: '#ff9800' },
        'missing': { bg: 'rgba(156, 39, 176, 0.15)', color: '#ce93d8' },
    };
    const c = colors[condition.toLowerCase()] || { bg: 'rgba(79, 195, 247, 0.1)', color: '#4fc3f7' };
    return (
        <span style={`display: inline-block; padding: 2px 8px; border-radius: 4px; background: ${c.bg}; color: ${c.color}; font-weight: 500;`}>
            {condition}
        </span>
    );
}

function TagList({ items, emptyText }) {
    if (!items || items.length === 0) return <span style="color: var(--text-muted);">{emptyText || '\u2014'}</span>;
    return (
        <span>
            {items.map((item, i) => (
                <span key={i}>
                    {i > 0 && ', '}
                    {item}
                </span>
            ))}
        </span>
    );
}

// ══════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ══════════════════════════════════════════════════════════════════════════════

const NPC_DIR = "Campaign/NPCs";

function NPCHub() {
    // ── State ────────────────────────────────────────────────────────────────
    const [searchText, setSearchText] = dc.useState('');
    const [filterLocations, setFilterLocations] = dc.useState([]);
    const [filterOrganizations, setFilterOrganizations] = dc.useState([]);
    const [filterOccupations, setFilterOccupations] = dc.useState([]);
    const [filterRaces, setFilterRaces] = dc.useState([]);
    const [filterConditions, setFilterConditions] = dc.useState([]);
    const [filtersShown, setFiltersShown] = dc.useState(false);
    const [sortBy, setSortBy] = dc.useState('name');

    // ── Query all NPC files ─────────────────────────────────────────────────
    const filesArray = dc.useArray(dc.useQuery(`#NPC and path("${NPC_DIR}")`), arr => arr);

    // ── Extract NPC data ────────────────────────────────────────────────────
    const npcs = dc.useMemo(() => {
        return filesArray
            .filter(f => {
                const tags = toArray(f.$tags || (f.$frontmatter && f.$frontmatter.tags) || []);
                return tags.some(t => typeof t === 'string' && t.includes('NPC'));
            })
            .map(f => {
                const fm = f.$frontmatter || f.frontmatter || {};
                const rawAliases = toArray(getVal(fm, 'aliases') || []);
                const rawLocations = toArray(getVal(fm, 'location') || []);
                const rawOrganizations = toArray(getVal(fm, 'organization') || []);
                const rawOccupations = toArray(getVal(fm, 'occupation') || []);

                const locations = rawLocations.map(stripLinks).filter(Boolean);
                const organizations = rawOrganizations.map(stripLinks).filter(Boolean);
                const occupations = rawOccupations.map(stripLinks).filter(Boolean);
                const aliases = rawAliases.map(stripLinks).filter(Boolean);
                const race = stripLinks(getVal(fm, 'ancestry') || getVal(fm, 'race') || '');
                const gender = stripLinks(getVal(fm, 'gender') || '');
                const condition = stripLinks(getVal(fm, 'condition') || '');
                const name = getVal(fm, 'name') || aliases[0] || f.$name || 'Unknown';

                return {
                    name,
                    aliases,
                    race,
                    gender,
                    condition,
                    locations,
                    organizations,
                    occupations,
                    filePath: f.$path || '',
                    folder: (f.$path || '').split('/').slice(0, -1).pop() || ''
                };
            })
            .filter(n => n.name && n.name !== 'Unknown');
    }, [filesArray]);

    // ── Build filter options from data ───────────────────────────────────────
    const allLocations = [...new Set(npcs.flatMap(n => n.locations))].sort();
    const allOrganizations = [...new Set(npcs.flatMap(n => n.organizations))].sort();
    const allOccupations = [...new Set(npcs.flatMap(n => n.occupations))].sort();
    const allRaces = [...new Set(npcs.map(n => n.race).filter(Boolean))].sort();
    const allConditions = [...new Set(npcs.map(n => n.condition).filter(Boolean))].sort();

    // ── Filter NPCs ─────────────────────────────────────────────────────────
    const filteredNPCs = dc.useMemo(() => {
        let result = [...npcs];

        if (searchText.trim()) {
            result = result.filter(n =>
                matchesSearch(n.name, searchText) ||
                n.aliases.some(a => matchesSearch(a, searchText))
            );
        }

        if (filterLocations.length > 0) {
            result = result.filter(n =>
                filterLocations.some(loc => n.locations.includes(loc))
            );
        }

        if (filterOrganizations.length > 0) {
            result = result.filter(n =>
                filterOrganizations.some(org => n.organizations.includes(org))
            );
        }

        if (filterOccupations.length > 0) {
            result = result.filter(n =>
                filterOccupations.some(occ => n.occupations.includes(occ))
            );
        }

        if (filterRaces.length > 0) {
            result = result.filter(n => n.race && filterRaces.includes(n.race));
        }

        if (filterConditions.length > 0) {
            result = result.filter(n => n.condition && filterConditions.includes(n.condition));
        }

        // Sorting
        result.sort((a, b) => {
            let cmp = 0;
            switch (sortBy) {
                case 'race':
                    cmp = (a.race || '').localeCompare(b.race || '');
                    break;
                case 'location':
                    cmp = (a.locations[0] || '').localeCompare(b.locations[0] || '');
                    break;
                case 'occupation':
                    cmp = (a.occupations[0] || '').localeCompare(b.occupations[0] || '');
                    break;
                case 'condition':
                    cmp = (a.condition || '').localeCompare(b.condition || '');
                    break;
                default:
                    cmp = a.name.localeCompare(b.name);
            }
            return cmp;
        });

        return result;
    }, [npcs, searchText, filterLocations, filterOrganizations, filterOccupations, filterRaces, filterConditions, sortBy]);

    // ── Toggle/Clear handlers ────────────────────────────────────────────────
    const toggleFilter = (arr, setArr, allItems) => () =>
        setArr(allItems.filter(x => !arr.includes(x)));

    const hasActiveFilters = searchText || filterLocations.length > 0 ||
        filterOrganizations.length > 0 || filterOccupations.length > 0 ||
        filterRaces.length > 0 || filterConditions.length > 0;

    const clearFilters = () => {
        setSearchText('');
        setFilterLocations([]);
        setFilterOrganizations([]);
        setFilterOccupations([]);
        setFilterRaces([]);
        setFilterConditions([]);
    };

    // ── Helper: filter button style ──────────────────────────────────────────
    const btnStyle = (isActive) => `
        padding: 0.3em 0.5em;
        border: 1px solid ${isActive ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
        border-radius: 0.25em;
        background-color: ${isActive ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
        color: ${isActive ? '#4fc3f7' : 'var(--text-normal)'};
        cursor: pointer;
        font-size: 0.8em;
        transition: all 0.2s ease;
        text-align: left;
    `;

    const toggleItem = (item, arr, setArr) => {
        setArr(arr.includes(item) ? arr.filter(x => x !== item) : [...arr, item]);
    };

    // ── Table columns ────────────────────────────────────────────────────────
    const columns = [
        { id: 'Name', value: n => <NPCLink npc={n} /> },
        { id: 'Aliases', value: n => <TagList items={n.aliases} /> },
        { id: 'Race', value: n => n.race || '\u2014' },
        { id: 'Occupation', value: n => <TagList items={n.occupations} /> },
        { id: 'Location', value: n => <TagList items={n.locations} /> },
        { id: 'Organization', value: n => <TagList items={n.organizations} /> },
        { id: 'Status', value: n => <ConditionBadge condition={n.condition} /> }
    ];

    // ── Render ───────────────────────────────────────────────────────────────
    return (
        <>
            {/* Search bar row */}
            <div style="display: flex; gap: 0.75em; align-items: center;">
                <input
                    type="search"
                    placeholder="Search NPCs..."
                    value={searchText}
                    oninput={e => setSearchText(e.target.value)}
                    style="flex-grow: 1;"
                />
                <div style="display: flex; gap: 0.2em; align-items: center;">
                    {[['name', 'A-Z'], ['race', 'Race'], ['location', 'Loc'], ['condition', 'Status']].map(([key, label]) => (
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
                <button
                    class="primary"
                    onclick={() => dc.app.commands.executeCommandById('quickadd:choice:3ad71beb-875e-49a5-890a-c7d60338a327')}
                    title="Create a new NPC from template"
                >
                    <dc.Icon icon="lucide-user-plus" /> New NPC
                </button>
                <button class="primary" onclick={() => setFiltersShown(!filtersShown)}>
                    ⚙
                </button>
                {hasActiveFilters && (
                    <button onclick={clearFilters}>
                        Clear All
                    </button>
                )}
            </div>

            {/* Filters panel */}
            {filtersShown && (
                <NPCQuerySettings>
                    {/* Location filter */}
                    {allLocations.length > 0 && (
                        <NPCQuerySetting
                            title="Location"
                            icon="lucide-map-pin"
                            onToggle={toggleFilter(filterLocations, setFilterLocations, allLocations)}
                            onClear={() => setFilterLocations([])}
                        >
                            <div style="display: flex; flex-direction: column; gap: 0.2em; max-height: 300px; overflow-y: auto;">
                                {allLocations.map(loc => (
                                    <button
                                        key={loc}
                                        onclick={() => toggleItem(loc, filterLocations, setFilterLocations)}
                                        style={btnStyle(filterLocations.includes(loc))}
                                    >
                                        {loc}
                                    </button>
                                ))}
                            </div>
                        </NPCQuerySetting>
                    )}

                    {/* Organization filter */}
                    {allOrganizations.length > 0 && (
                        <NPCQuerySetting
                            title="Organization"
                            icon="lucide-users"
                            onToggle={toggleFilter(filterOrganizations, setFilterOrganizations, allOrganizations)}
                            onClear={() => setFilterOrganizations([])}
                        >
                            <div style="display: flex; flex-direction: column; gap: 0.2em; max-height: 300px; overflow-y: auto;">
                                {allOrganizations.map(org => (
                                    <button
                                        key={org}
                                        onclick={() => toggleItem(org, filterOrganizations, setFilterOrganizations)}
                                        style={btnStyle(filterOrganizations.includes(org))}
                                    >
                                        {org}
                                    </button>
                                ))}
                            </div>
                        </NPCQuerySetting>
                    )}

                    {/* Occupation filter */}
                    {allOccupations.length > 0 && (
                        <NPCQuerySetting
                            title="Occupation"
                            icon="lucide-briefcase"
                            onToggle={toggleFilter(filterOccupations, setFilterOccupations, allOccupations)}
                            onClear={() => setFilterOccupations([])}
                        >
                            <div style="display: flex; flex-direction: column; gap: 0.2em; max-height: 300px; overflow-y: auto;">
                                {allOccupations.map(occ => (
                                    <button
                                        key={occ}
                                        onclick={() => toggleItem(occ, filterOccupations, setFilterOccupations)}
                                        style={btnStyle(filterOccupations.includes(occ))}
                                    >
                                        {occ}
                                    </button>
                                ))}
                            </div>
                        </NPCQuerySetting>
                    )}

                    {/* Race filter */}
                    {allRaces.length > 0 && (
                        <NPCQuerySetting
                            title="Race"
                            icon="lucide-dna"
                            onToggle={toggleFilter(filterRaces, setFilterRaces, allRaces)}
                            onClear={() => setFilterRaces([])}
                        >
                            <div style="display: flex; flex-direction: column; gap: 0.2em; max-height: 300px; overflow-y: auto;">
                                {allRaces.map(race => (
                                    <button
                                        key={race}
                                        onclick={() => toggleItem(race, filterRaces, setFilterRaces)}
                                        style={btnStyle(filterRaces.includes(race))}
                                    >
                                        {race}
                                    </button>
                                ))}
                            </div>
                        </NPCQuerySetting>
                    )}

                    {/* Condition/Status filter */}
                    {allConditions.length > 0 && (
                        <NPCQuerySetting
                            title="Status"
                            icon="lucide-heart-pulse"
                            onToggle={toggleFilter(filterConditions, setFilterConditions, allConditions)}
                            onClear={() => setFilterConditions([])}
                        >
                            <div style="display: flex; flex-direction: column; gap: 0.2em;">
                                {allConditions.map(cond => (
                                    <button
                                        key={cond}
                                        onclick={() => toggleItem(cond, filterConditions, setFilterConditions)}
                                        style={btnStyle(filterConditions.includes(cond))}
                                    >
                                        {cond}
                                    </button>
                                ))}
                            </div>
                        </NPCQuerySetting>
                    )}
                </NPCQuerySettings>
            )}

            {/* Stats bar */}
            <div style="display: flex; gap: 1rem; margin-bottom: 0.5em; margin-top: 1em; font-size: 0.85rem; color: var(--text-muted);">
                <span>Showing {filteredNPCs.length} of {npcs.length} NPCs</span>
            </div>

            {/* Table */}
            <dc.VanillaTable
                columns={columns}
                rows={filteredNPCs}
                paging={50}
            />
        </>
    );
}

return { NPCHub };
