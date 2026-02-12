// ══════════════════════════════════════════════════════════════════════════════
// MONSTER HUB - Encounter lookup and quick reference
// ══════════════════════════════════════════════════════════════════════════════
// Displays all monsters from the bestiary with filterable, sortable table.
// Data extracted from frontmatter fields (name, size, type, cr, immunities, etc).

// ── Helper Functions ─────────────────────────────────────────────────────────

function toArray(val) {
    if (!val) return [];
    if (Array.isArray(val)) return val;
    if (typeof val === 'object' && val.values) return Array.from(val.values());
    if (typeof val[Symbol.iterator] === 'function') return Array.from(val);
    return [];
}

function getVal(obj, key) {
    if (!obj) return null;
    const val = obj[key];
    if (val === undefined || val === null) return null;
    if (typeof val === 'object' && val.value !== undefined) return val.value;
    return val;
}

function extractFromTags(tags, prefix) {
    const arr = toArray(tags);
    const tag = arr.find(t => typeof t === 'string' && t.startsWith(prefix));
    return tag ? tag.slice(prefix.length) : null;
}

function parseCR(crStr) {
    if (!crStr) return null;
    if (crStr === '1-8' || crStr === '1/8') return 0.125;
    if (crStr === '1-4' || crStr === '1/4') return 0.25;
    if (crStr === '1-2' || crStr === '1/2') return 0.5;
    return parseFloat(crStr);
}

function formatCR(crNum) {
    if (crNum === null || crNum === undefined) return '—';
    if (crNum === 0.125) return '1/8';
    if (crNum === 0.25) return '1/4';
    if (crNum === 0.5) return '1/2';
    return String(crNum);
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}

function hasDefense(defenseStr, damageType) {
    if (!defenseStr) return false;
    return defenseStr.toLowerCase().includes(damageType.toLowerCase());
}

// Word-based search: matches if ALL search words are found in the target string
// e.g., "giant spider" matches "Giant Wolf Spider" because both "giant" and "spider" are present
function matchesSearch(target, searchQuery) {
    if (!target || !searchQuery) return false;
    const targetLower = target.toLowerCase();
    const searchWords = searchQuery.toLowerCase().trim().split(/\s+/).filter(w => w.length > 0);
    return searchWords.every(word => targetLower.includes(word));
}

// ── Constants ────────────────────────────────────────────────────────────────

const CR_OPTIONS = [
    { value: '', label: 'Any' },
    { value: '0', label: '0' },
    { value: '0.125', label: '1/8' },
    { value: '0.25', label: '1/4' },
    { value: '0.5', label: '1/2' },
    ...Array.from({ length: 30 }, (_, i) => ({ value: String(i + 1), label: String(i + 1) }))
];

const MONSTER_TYPES = [
    'aberration', 'beast', 'celestial', 'construct', 'dragon',
    'elemental', 'fey', 'fiend', 'giant', 'humanoid',
    'monstrosity', 'ooze', 'plant', 'undead'
];

const MONSTER_SIZES = ['tiny', 'small', 'medium', 'large', 'huge', 'gargantuan'];

const DAMAGE_TYPES = [
    'acid', 'bludgeoning', 'cold', 'fire', 'force', 'lightning',
    'necrotic', 'piercing', 'poison', 'psychic', 'radiant',
    'slashing', 'thunder'
];

const CONDITION_TYPES = [
    'blinded', 'charmed', 'deafened', 'exhaustion', 'frightened',
    'paralyzed', 'poisoned', 'prone', 'stunned'
];

// ── Layout Components ────────────────────────────────────────────────────────

function MonsterQuerySettings({ children }) {
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

function MonsterQuerySetting({ title, icon, children, onToggle, onClear }) {
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

function MonsterLink({ monster }) {
    const linkPath = monster.filePath + '#^statblock';
    const encodedPath = encodeURIComponent(monster.filePath);
    return (
        <a
            className="internal-link"
            data-href={linkPath}
            href={`obsidian://open?file=${encodedPath}`}
            style="color: var(--text-accent); text-decoration: none; cursor: pointer;"
        >
            {monster.name}
        </a>
    );
}

function DefenseDisplay({ monster }) {
    const parts = [];

    if (monster.immune) {
        const types = monster.immune.split(/,\s*/).slice(0, 3);
        parts.push(
            <span key="immune" title={`Immune: ${monster.immune}`}>
                <span style="color: #718096; font-weight: 500;">I:</span>{' '}
                {types.map((t, i) => (
                    <span key={i} style="display: inline-block; padding: 1px 4px; border-radius: 3px; background-color: rgba(74, 85, 104, 0.3); color: var(--text-normal); margin-right: 2px; margin-bottom: 2px;">{t.split(' ')[0]}</span>
                ))}
                {monster.immune.split(/,\s*/).length > 3 && <span style="display: inline-block; padding: 1px 4px; border-radius: 3px; background-color: rgba(74, 85, 104, 0.3); color: var(--text-normal); margin-right: 2px;">+{monster.immune.split(/,\s*/).length - 3}</span>}
            </span>
        );
    }

    if (monster.resist) {
        const types = monster.resist.split(/,\s*/).slice(0, 3);
        parts.push(
            <span key="resist" title={`Resist: ${monster.resist}`}>
                <span style="color: #975a16; font-weight: 500;">R:</span>{' '}
                {types.map((t, i) => (
                    <span key={i} style="display: inline-block; padding: 1px 4px; border-radius: 3px; background-color: rgba(116, 66, 16, 0.3); color: var(--text-normal); margin-right: 2px; margin-bottom: 2px;">{t.split(' ')[0]}</span>
                ))}
                {monster.resist.split(/,\s*/).length > 3 && <span style="display: inline-block; padding: 1px 4px; border-radius: 3px; background-color: rgba(116, 66, 16, 0.3); color: var(--text-normal); margin-right: 2px;">+{monster.resist.split(/,\s*/).length - 3}</span>}
            </span>
        );
    }

    if (monster.vulnerable) {
        parts.push(
            <span key="vuln" title={`Vulnerable: ${monster.vulnerable}`}>
                <span style="color: #c53030; font-weight: 500;">V:</span>{' '}
                <span style="display: inline-block; padding: 1px 4px; border-radius: 3px; background-color: rgba(197, 48, 48, 0.3); color: var(--text-normal); margin-right: 2px;">{monster.vulnerable.split(/,\s*/)[0]}</span>
            </span>
        );
    }

    if (parts.length === 0) return <span style="color: var(--text-muted);">—</span>;

    return <div style="font-size: 0.75rem; line-height: 1.3;">{parts}</div>;
}

// ══════════════════════════════════════════════════════════════════════════════
// MAIN COMPONENT
// ══════════════════════════════════════════════════════════════════════════════

function MonsterHub() {
    // ── State ────────────────────────────────────────────────────────────────
    const [searchText, setSearchText] = dc.useState('');
    const [filterCRMin, setFilterCRMin] = dc.useState('');
    const [filterCRMax, setFilterCRMax] = dc.useState('');
    const [filterTypes, setFilterTypes] = dc.useState([]);
    const [filterSizes, setFilterSizes] = dc.useState([]);
    const [filterImmune, setFilterImmune] = dc.useState([]);
    const [filterResist, setFilterResist] = dc.useState([]);
    const [filterConditionImmune, setFilterConditionImmune] = dc.useState([]);
    const [filterVulnerable, setFilterVulnerable] = dc.useState([]);
    const [filtersShown, setFiltersShown] = dc.useState(false);

    // Special filters: 'any' = has at least one, 'none' = has none
    const [filterImmuneMode, setFilterImmuneMode] = dc.useState(''); // '', 'any', 'none'
    const [filterResistMode, setFilterResistMode] = dc.useState('');
    const [filterConditionImmuneMode, setFilterConditionImmuneMode] = dc.useState('');
    const [filterVulnerableMode, setFilterVulnerableMode] = dc.useState('');

    // Sorting
    const [sortBy, setSortBy] = dc.useState('name'); // 'name', 'cr', 'ac', 'hp', 'type'
    const [sortDir, setSortDir] = dc.useState('asc'); // 'asc', 'desc'

    // ── Query all bestiary files ─────────────────────────────────────────────
    const filesArray = dc.useArray(dc.useQuery('path("z_Mechanics/CLI/bestiary")'), arr => arr);

    // ── Extract monster data from files ──────────────────────────────────────
    const monsters = dc.useMemo(() => {
        return filesArray
            .filter(f => {
                const path = f.$path || '';
                return path.includes('/bestiary/') &&
                       path.endsWith('.md') &&
                       !path.endsWith('/bestiary.md') &&
                       !path.includes('/legendary-group/');
            })
            .map(f => {
                const fm = f.$frontmatter || f.frontmatter || {};
                const rawTags = getVal(fm, 'tags') || f.$tags || f.tags || [];
                const tags = toArray(rawTags);
                const rawAliases = getVal(fm, 'aliases') || [];
                const aliases = toArray(rawAliases);

                // Primary: explicit frontmatter fields
                const fmName = getVal(fm, 'name');
                const fmSize = getVal(fm, 'size');
                const fmType = getVal(fm, 'type');
                const fmCR = getVal(fm, 'cr');
                const fmAC = getVal(fm, 'ac');
                const fmHP = getVal(fm, 'hp');
                const fmImmune = getVal(fm, 'immune');
                const fmResist = getVal(fm, 'resist');
                const fmVulnerable = getVal(fm, 'vulnerable');
                const fmConditionImmune = getVal(fm, 'condition_immune');
                const fmEnvironment = getVal(fm, 'environment');

                // Fallback: parse from tags
                const tagCR = extractFromTags(tags, 'ttrpg-cli/monster/cr/');
                const tagSize = extractFromTags(tags, 'ttrpg-cli/monster/size/');
                const tagType = extractFromTags(tags, 'ttrpg-cli/monster/type/');
                const tagSource = extractFromTags(tags, 'ttrpg-cli/compendium/src/5e/');

                // Parse type
                let type = null;
                let subtype = null;
                if (fmType) {
                    const typeMatch = fmType.match(/^(\w+)(?:\s*\(([^)]+)\))?/);
                    if (typeMatch) {
                        type = typeMatch[1].toLowerCase();
                        subtype = typeMatch[2] || null;
                    }
                } else if (tagType) {
                    const parts = tagType.split('/');
                    type = parts[0] || null;
                    subtype = parts[1] || null;
                }

                const crStr = fmCR || tagCR;

                return {
                    name: fmName || aliases[0] || f.$name || 'Unknown',
                    crStr: crStr,
                    crNum: parseCR(crStr),
                    ac: fmAC || null,
                    hp: fmHP || null,
                    size: (fmSize || tagSize || '').toLowerCase(),
                    type: type,
                    subtype: subtype,
                    immune: fmImmune || null,
                    resist: fmResist || null,
                    vulnerable: fmVulnerable || null,
                    conditionImmune: fmConditionImmune || null,
                    environment: fmEnvironment || null,
                    source: tagSource,
                    filePath: f.$path || ''
                };
            })
            .filter(m => m.name && m.name !== 'Unknown' && m.crNum !== null);
    }, [filesArray]);

    // ── Filter monsters ──────────────────────────────────────────────────────
    const filteredMonsters = dc.useMemo(() => {
        let result = [...monsters];

        // Text search (word-based: "giant spider" matches "Giant Wolf Spider")
        if (searchText.trim()) {
            result = result.filter(m => matchesSearch(m.name, searchText));
        }

        // CR range
        if (filterCRMin !== '') {
            const minCR = parseFloat(filterCRMin);
            result = result.filter(m => m.crNum !== null && m.crNum >= minCR);
        }
        if (filterCRMax !== '') {
            const maxCR = parseFloat(filterCRMax);
            result = result.filter(m => m.crNum !== null && m.crNum <= maxCR);
        }

        // Type filter
        if (filterTypes.length > 0) {
            result = result.filter(m => m.type && filterTypes.includes(m.type));
        }

        // Size filter
        if (filterSizes.length > 0) {
            result = result.filter(m => m.size && filterSizes.includes(m.size));
        }

        // Damage immunity filter
        if (filterImmuneMode === 'any') {
            result = result.filter(m => m.immune && m.immune.length > 0);
        } else if (filterImmuneMode === 'none') {
            result = result.filter(m => !m.immune || m.immune.length === 0);
        } else if (filterImmune.length > 0) {
            result = result.filter(m =>
                filterImmune.every(dmgType => hasDefense(m.immune, dmgType))
            );
        }

        // Damage resistance filter
        if (filterResistMode === 'any') {
            result = result.filter(m => m.resist && m.resist.length > 0);
        } else if (filterResistMode === 'none') {
            result = result.filter(m => !m.resist || m.resist.length === 0);
        } else if (filterResist.length > 0) {
            result = result.filter(m =>
                filterResist.every(dmgType => hasDefense(m.resist, dmgType))
            );
        }

        // Condition immunity filter
        if (filterConditionImmuneMode === 'any') {
            result = result.filter(m => m.conditionImmune && m.conditionImmune.length > 0);
        } else if (filterConditionImmuneMode === 'none') {
            result = result.filter(m => !m.conditionImmune || m.conditionImmune.length === 0);
        } else if (filterConditionImmune.length > 0) {
            result = result.filter(m =>
                filterConditionImmune.every(cond => hasDefense(m.conditionImmune, cond))
            );
        }

        // Damage vulnerability filter
        if (filterVulnerableMode === 'any') {
            result = result.filter(m => m.vulnerable && m.vulnerable.length > 0);
        } else if (filterVulnerableMode === 'none') {
            result = result.filter(m => !m.vulnerable || m.vulnerable.length === 0);
        } else if (filterVulnerable.length > 0) {
            result = result.filter(m =>
                filterVulnerable.every(dmgType => hasDefense(m.vulnerable, dmgType))
            );
        }

        // Sorting
        result.sort((a, b) => {
            let cmp = 0;
            switch (sortBy) {
                case 'cr':
                    cmp = (a.crNum ?? -1) - (b.crNum ?? -1);
                    break;
                case 'ac':
                    cmp = (a.ac ?? 0) - (b.ac ?? 0);
                    break;
                case 'hp':
                    // Handle HP that might be a string like "40 + 10 for each spell level above 4"
                    const hpA = typeof a.hp === 'number' ? a.hp : parseInt(a.hp) || 0;
                    const hpB = typeof b.hp === 'number' ? b.hp : parseInt(b.hp) || 0;
                    cmp = hpA - hpB;
                    break;
                case 'type':
                    cmp = (a.type || '').localeCompare(b.type || '');
                    break;
                default: // name
                    cmp = a.name.localeCompare(b.name);
            }
            return sortDir === 'desc' ? -cmp : cmp;
        });
        return result;
    }, [monsters, searchText, filterCRMin, filterCRMax, filterTypes, filterSizes, filterImmune, filterResist, filterConditionImmune, filterVulnerable, filterImmuneMode, filterResistMode, filterConditionImmuneMode, filterVulnerableMode, sortBy, sortDir]);

    // ── Toggle handlers ──────────────────────────────────────────────────────
    const toggleType = (type) => {
        setFilterTypes(prev => prev.includes(type) ? prev.filter(t => t !== type) : [...prev, type]);
    };
    const toggleSize = (size) => {
        setFilterSizes(prev => prev.includes(size) ? prev.filter(s => s !== size) : [...prev, size]);
    };
    const toggleImmune = (dmg) => {
        setFilterImmune(prev => prev.includes(dmg) ? prev.filter(d => d !== dmg) : [...prev, dmg]);
    };
    const toggleResist = (dmg) => {
        setFilterResist(prev => prev.includes(dmg) ? prev.filter(d => d !== dmg) : [...prev, dmg]);
    };
    const toggleConditionImmune = (cond) => {
        setFilterConditionImmune(prev => prev.includes(cond) ? prev.filter(c => c !== cond) : [...prev, cond]);
    };
    const toggleVulnerable = (dmg) => {
        setFilterVulnerable(prev => prev.includes(dmg) ? prev.filter(d => d !== dmg) : [...prev, dmg]);
    };

    // Clear handlers
    const clearFilterTypes = () => setFilterTypes([]);
    const clearFilterSizes = () => setFilterSizes([]);
    const clearFilterImmune = () => setFilterImmune([]);
    const clearFilterResist = () => setFilterResist([]);
    const clearFilterConditionImmune = () => setFilterConditionImmune([]);
    const clearFilterVulnerable = () => setFilterVulnerable([]);

    // Toggle all handlers
    const toggleAllTypes = () => setFilterTypes(MONSTER_TYPES.filter(t => !filterTypes.includes(t)));
    const toggleAllSizes = () => setFilterSizes(MONSTER_SIZES.filter(s => !filterSizes.includes(s)));
    const toggleAllImmune = () => setFilterImmune(DAMAGE_TYPES.filter(d => !filterImmune.includes(d)));
    const toggleAllResist = () => setFilterResist(DAMAGE_TYPES.filter(d => !filterResist.includes(d)));
    const toggleAllConditionImmune = () => setFilterConditionImmune(CONDITION_TYPES.filter(c => !filterConditionImmune.includes(c)));
    const toggleAllVulnerable = () => setFilterVulnerable(DAMAGE_TYPES.filter(d => !filterVulnerable.includes(d)));

    const clearFilters = () => {
        setSearchText('');
        setFilterCRMin('');
        setFilterCRMax('');
        setFilterTypes([]);
        setFilterSizes([]);
        setFilterImmune([]);
        setFilterResist([]);
        setFilterConditionImmune([]);
        setFilterVulnerable([]);
        setFilterImmuneMode('');
        setFilterResistMode('');
        setFilterConditionImmuneMode('');
        setFilterVulnerableMode('');
    };

    const hasActiveFilters = searchText || filterCRMin || filterCRMax ||
        filterTypes.length > 0 || filterSizes.length > 0 ||
        filterImmune.length > 0 || filterResist.length > 0 ||
        filterConditionImmune.length > 0 || filterVulnerable.length > 0 ||
        filterImmuneMode || filterResistMode || filterConditionImmuneMode || filterVulnerableMode;

    // ── Table columns ────────────────────────────────────────────────────────
    const columns = [
        { id: 'Name', value: m => <MonsterLink monster={m} /> },
        { id: 'CR', value: m => formatCR(m.crNum) },
        { id: 'AC', value: m => m.ac ?? '—' },
        { id: 'HP', value: m => m.hp ?? '—' },
        { id: 'Type', value: m => m.type ? capitalize(m.type) : '—' },
        { id: 'I/R/V', value: m => <DefenseDisplay monster={m} /> }
    ];

    // ── Render ───────────────────────────────────────────────────────────────
    return (
        <>
            {/* Search bar row */}
            <div style="display: flex; gap: 0.75em; margin-bottom: 1em;">
                <input
                    type="search"
                    placeholder="Search monsters..."
                    value={searchText}
                    oninput={e => setSearchText(e.target.value)}
                    style="flex-grow: 1;"
                />
                <select
                    value={sortBy}
                    onchange={e => setSortBy(e.target.value)}
                    style="min-width: 100px;"
                >
                    <option value="name">Sort: Name</option>
                    <option value="cr">Sort: CR</option>
                    <option value="ac">Sort: AC</option>
                    <option value="hp">Sort: HP</option>
                    <option value="type">Sort: Type</option>
                </select>
                <button
                    onclick={() => setSortDir(sortDir === 'asc' ? 'desc' : 'asc')}
                    style="min-width: 40px;"
                    title={sortDir === 'asc' ? 'Ascending' : 'Descending'}
                >
                    {sortDir === 'asc' ? '↑' : '↓'}
                </button>
                <button class="primary" onclick={() => setFiltersShown(!filtersShown)}>
                    <dc.Icon icon="lucide-filter" /> Filters
                </button>
                {hasActiveFilters && (
                    <button onclick={clearFilters}>
                        Clear All
                    </button>
                )}
            </div>

            {/* Filters panel */}
            {filtersShown && (
                <MonsterQuerySettings>
                    {/* Type filter */}
                    <MonsterQuerySetting
                        title="Type"
                        icon="lucide-skull"
                        onToggle={toggleAllTypes}
                        onClear={clearFilterTypes}
                    >
                        <div style="display: flex; flex-direction: column; gap: 0.2em; max-height: 300px; overflow-y: auto;">
                            {MONSTER_TYPES.map(t => (
                                <button
                                    key={t}
                                    onclick={() => toggleType(t)}
                                    style={`
                                        padding: 0.3em 0.5em;
                                        border: 1px solid ${filterTypes.includes(t) ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                                        border-radius: 0.25em;
                                        background-color: ${filterTypes.includes(t) ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                                        color: ${filterTypes.includes(t) ? '#4fc3f7' : 'var(--text-normal)'};
                                        cursor: pointer;
                                        font-size: 0.8em;
                                        transition: all 0.2s ease;
                                        text-align: left;
                                    `}
                                >
                                    {capitalize(t)}
                                </button>
                            ))}
                        </div>
                    </MonsterQuerySetting>

                    {/* Size filter */}
                    <MonsterQuerySetting
                        title="Size"
                        icon="lucide-maximize"
                        onToggle={toggleAllSizes}
                        onClear={clearFilterSizes}
                    >
                        <div style="display: flex; flex-direction: column; gap: 0.2em;">
                            {MONSTER_SIZES.map(s => (
                                <button
                                    key={s}
                                    onclick={() => toggleSize(s)}
                                    style={`
                                        padding: 0.3em 0.5em;
                                        border: 1px solid ${filterSizes.includes(s) ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                                        border-radius: 0.25em;
                                        background-color: ${filterSizes.includes(s) ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                                        color: ${filterSizes.includes(s) ? '#4fc3f7' : 'var(--text-normal)'};
                                        cursor: pointer;
                                        font-size: 0.8em;
                                        transition: all 0.2s ease;
                                        text-align: left;
                                    `}
                                >
                                    {capitalize(s)}
                                </button>
                            ))}
                        </div>
                    </MonsterQuerySetting>

                    {/* CR Range filter */}
                    <MonsterQuerySetting
                        title="Challenge Rating"
                        icon="lucide-trophy"
                    >
                        <div style="display: flex; flex-direction: column; gap: 0.5em;">
                            <div style="font-weight: 500; font-size: 0.85em;">CR Range</div>
                            <div style="display: flex; gap: 0.4em; align-items: center;">
                                <select
                                    value={filterCRMin}
                                    onchange={e => setFilterCRMin(e.target.value)}
                                    style="flex: 1; font-size: 0.85em; padding: 0.3em;"
                                >
                                    {CR_OPTIONS.map(opt => (
                                        <option key={`min-${opt.value}`} value={opt.value}>{opt.label}</option>
                                    ))}
                                </select>
                                <span style="color: var(--text-muted); font-size: 0.85em;">to</span>
                                <select
                                    value={filterCRMax}
                                    onchange={e => setFilterCRMax(e.target.value)}
                                    style="flex: 1; font-size: 0.85em; padding: 0.3em;"
                                >
                                    {CR_OPTIONS.map(opt => (
                                        <option key={`max-${opt.value}`} value={opt.value}>{opt.label}</option>
                                    ))}
                                </select>
                            </div>
                        </div>
                    </MonsterQuerySetting>

                    {/* Damage Immunity filter */}
                    <MonsterQuerySetting
                        title="Damage Immunity"
                        icon="lucide-shield"
                        onToggle={toggleAllImmune}
                        onClear={() => { clearFilterImmune(); setFilterImmuneMode(''); }}
                    >
                        <div style="display: flex; gap: 0.3em; margin-bottom: 0.5em;">
                            <button
                                onclick={() => { setFilterImmuneMode(filterImmuneMode === 'any' ? '' : 'any'); setFilterImmune([]); }}
                                style={`
                                    flex: 1; padding: 0.3em;
                                    border: 1px solid ${filterImmuneMode === 'any' ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                                    border-radius: 0.2em;
                                    background-color: ${filterImmuneMode === 'any' ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                                    color: ${filterImmuneMode === 'any' ? '#4fc3f7' : 'var(--text-normal)'};
                                    cursor: pointer; font-size: 0.75em;
                                `}
                            >Any</button>
                            <button
                                onclick={() => { setFilterImmuneMode(filterImmuneMode === 'none' ? '' : 'none'); setFilterImmune([]); }}
                                style={`
                                    flex: 1; padding: 0.3em;
                                    border: 1px solid ${filterImmuneMode === 'none' ? '#f44336' : 'var(--background-modifier-border, #444)'};
                                    border-radius: 0.2em;
                                    background-color: ${filterImmuneMode === 'none' ? 'rgba(244, 67, 54, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                                    color: ${filterImmuneMode === 'none' ? '#f44336' : 'var(--text-normal)'};
                                    cursor: pointer; font-size: 0.75em;
                                `}
                            >None</button>
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.2em; max-height: 200px; overflow-y: auto;">
                            {DAMAGE_TYPES.map(d => (
                                <button
                                    key={d}
                                    onclick={() => { toggleImmune(d); setFilterImmuneMode(''); }}
                                    style={`
                                        padding: 0.25em 0.4em;
                                        border: 1px solid ${filterImmune.includes(d) ? '#718096' : 'var(--background-modifier-border, #444)'};
                                        border-radius: 0.2em;
                                        background-color: ${filterImmune.includes(d) ? 'rgba(74, 85, 104, 0.3)' : 'var(--background-primary, #1e1e1e)'};
                                        color: ${filterImmune.includes(d) ? '#a0aec0' : 'var(--text-normal)'};
                                        cursor: pointer;
                                        font-size: 0.75em;
                                        transition: all 0.2s ease;
                                        opacity: ${filterImmuneMode ? '0.5' : '1'};
                                    `}
                                    disabled={!!filterImmuneMode}
                                >
                                    {capitalize(d)}
                                </button>
                            ))}
                        </div>
                    </MonsterQuerySetting>

                    {/* Damage Resistance filter */}
                    <MonsterQuerySetting
                        title="Damage Resistance"
                        icon="lucide-shield-half"
                        onToggle={toggleAllResist}
                        onClear={() => { clearFilterResist(); setFilterResistMode(''); }}
                    >
                        <div style="display: flex; gap: 0.3em; margin-bottom: 0.5em;">
                            <button
                                onclick={() => { setFilterResistMode(filterResistMode === 'any' ? '' : 'any'); setFilterResist([]); }}
                                style={`
                                    flex: 1; padding: 0.3em;
                                    border: 1px solid ${filterResistMode === 'any' ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                                    border-radius: 0.2em;
                                    background-color: ${filterResistMode === 'any' ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                                    color: ${filterResistMode === 'any' ? '#4fc3f7' : 'var(--text-normal)'};
                                    cursor: pointer; font-size: 0.75em;
                                `}
                            >Any</button>
                            <button
                                onclick={() => { setFilterResistMode(filterResistMode === 'none' ? '' : 'none'); setFilterResist([]); }}
                                style={`
                                    flex: 1; padding: 0.3em;
                                    border: 1px solid ${filterResistMode === 'none' ? '#f44336' : 'var(--background-modifier-border, #444)'};
                                    border-radius: 0.2em;
                                    background-color: ${filterResistMode === 'none' ? 'rgba(244, 67, 54, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                                    color: ${filterResistMode === 'none' ? '#f44336' : 'var(--text-normal)'};
                                    cursor: pointer; font-size: 0.75em;
                                `}
                            >None</button>
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.2em; max-height: 200px; overflow-y: auto;">
                            {DAMAGE_TYPES.map(d => (
                                <button
                                    key={d}
                                    onclick={() => { toggleResist(d); setFilterResistMode(''); }}
                                    style={`
                                        padding: 0.25em 0.4em;
                                        border: 1px solid ${filterResist.includes(d) ? '#975a16' : 'var(--background-modifier-border, #444)'};
                                        border-radius: 0.2em;
                                        background-color: ${filterResist.includes(d) ? 'rgba(116, 66, 16, 0.3)' : 'var(--background-primary, #1e1e1e)'};
                                        color: ${filterResist.includes(d) ? '#d69e2e' : 'var(--text-normal)'};
                                        cursor: pointer;
                                        font-size: 0.75em;
                                        transition: all 0.2s ease;
                                        opacity: ${filterResistMode ? '0.5' : '1'};
                                    `}
                                    disabled={!!filterResistMode}
                                >
                                    {capitalize(d)}
                                </button>
                            ))}
                        </div>
                    </MonsterQuerySetting>

                    {/* Condition Immunity filter */}
                    <MonsterQuerySetting
                        title="Condition Immunity"
                        icon="lucide-heart-off"
                        onToggle={toggleAllConditionImmune}
                        onClear={() => { clearFilterConditionImmune(); setFilterConditionImmuneMode(''); }}
                    >
                        <div style="display: flex; gap: 0.3em; margin-bottom: 0.5em;">
                            <button
                                onclick={() => { setFilterConditionImmuneMode(filterConditionImmuneMode === 'any' ? '' : 'any'); setFilterConditionImmune([]); }}
                                style={`
                                    flex: 1; padding: 0.3em;
                                    border: 1px solid ${filterConditionImmuneMode === 'any' ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                                    border-radius: 0.2em;
                                    background-color: ${filterConditionImmuneMode === 'any' ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                                    color: ${filterConditionImmuneMode === 'any' ? '#4fc3f7' : 'var(--text-normal)'};
                                    cursor: pointer; font-size: 0.75em;
                                `}
                            >Any</button>
                            <button
                                onclick={() => { setFilterConditionImmuneMode(filterConditionImmuneMode === 'none' ? '' : 'none'); setFilterConditionImmune([]); }}
                                style={`
                                    flex: 1; padding: 0.3em;
                                    border: 1px solid ${filterConditionImmuneMode === 'none' ? '#f44336' : 'var(--background-modifier-border, #444)'};
                                    border-radius: 0.2em;
                                    background-color: ${filterConditionImmuneMode === 'none' ? 'rgba(244, 67, 54, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                                    color: ${filterConditionImmuneMode === 'none' ? '#f44336' : 'var(--text-normal)'};
                                    cursor: pointer; font-size: 0.75em;
                                `}
                            >None</button>
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.2em; max-height: 200px; overflow-y: auto;">
                            {CONDITION_TYPES.map(c => (
                                <button
                                    key={c}
                                    onclick={() => { toggleConditionImmune(c); setFilterConditionImmuneMode(''); }}
                                    style={`
                                        padding: 0.25em 0.4em;
                                        border: 1px solid ${filterConditionImmune.includes(c) ? '#9c27b0' : 'var(--background-modifier-border, #444)'};
                                        border-radius: 0.2em;
                                        background-color: ${filterConditionImmune.includes(c) ? 'rgba(156, 39, 176, 0.15)' : 'var(--background-primary, #1e1e1e)'};
                                        color: ${filterConditionImmune.includes(c) ? '#ce93d8' : 'var(--text-normal)'};
                                        cursor: pointer;
                                        font-size: 0.75em;
                                        transition: all 0.2s ease;
                                        opacity: ${filterConditionImmuneMode ? '0.5' : '1'};
                                    `}
                                    disabled={!!filterConditionImmuneMode}
                                >
                                    {capitalize(c)}
                                </button>
                            ))}
                        </div>
                    </MonsterQuerySetting>

                    {/* Damage Vulnerability filter */}
                    <MonsterQuerySetting
                        title="Vulnerability"
                        icon="lucide-zap"
                        onToggle={toggleAllVulnerable}
                        onClear={() => { clearFilterVulnerable(); setFilterVulnerableMode(''); }}
                    >
                        <div style="display: flex; gap: 0.3em; margin-bottom: 0.5em;">
                            <button
                                onclick={() => { setFilterVulnerableMode(filterVulnerableMode === 'any' ? '' : 'any'); setFilterVulnerable([]); }}
                                style={`
                                    flex: 1; padding: 0.3em;
                                    border: 1px solid ${filterVulnerableMode === 'any' ? '#4fc3f7' : 'var(--background-modifier-border, #444)'};
                                    border-radius: 0.2em;
                                    background-color: ${filterVulnerableMode === 'any' ? 'rgba(79, 195, 247, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                                    color: ${filterVulnerableMode === 'any' ? '#4fc3f7' : 'var(--text-normal)'};
                                    cursor: pointer; font-size: 0.75em;
                                `}
                            >Any</button>
                            <button
                                onclick={() => { setFilterVulnerableMode(filterVulnerableMode === 'none' ? '' : 'none'); setFilterVulnerable([]); }}
                                style={`
                                    flex: 1; padding: 0.3em;
                                    border: 1px solid ${filterVulnerableMode === 'none' ? '#f44336' : 'var(--background-modifier-border, #444)'};
                                    border-radius: 0.2em;
                                    background-color: ${filterVulnerableMode === 'none' ? 'rgba(244, 67, 54, 0.1)' : 'var(--background-primary, #1e1e1e)'};
                                    color: ${filterVulnerableMode === 'none' ? '#f44336' : 'var(--text-normal)'};
                                    cursor: pointer; font-size: 0.75em;
                                `}
                            >None</button>
                        </div>
                        <div style="display: flex; flex-wrap: wrap; gap: 0.2em; max-height: 200px; overflow-y: auto;">
                            {DAMAGE_TYPES.map(d => (
                                <button
                                    key={d}
                                    onclick={() => { toggleVulnerable(d); setFilterVulnerableMode(''); }}
                                    style={`
                                        padding: 0.25em 0.4em;
                                        border: 1px solid ${filterVulnerable.includes(d) ? '#c53030' : 'var(--background-modifier-border, #444)'};
                                        border-radius: 0.2em;
                                        background-color: ${filterVulnerable.includes(d) ? 'rgba(197, 48, 48, 0.3)' : 'var(--background-primary, #1e1e1e)'};
                                        color: ${filterVulnerable.includes(d) ? '#fc8181' : 'var(--text-normal)'};
                                        cursor: pointer;
                                        font-size: 0.75em;
                                        transition: all 0.2s ease;
                                        opacity: ${filterVulnerableMode ? '0.5' : '1'};
                                    `}
                                    disabled={!!filterVulnerableMode}
                                >
                                    {capitalize(d)}
                                </button>
                            ))}
                        </div>
                    </MonsterQuerySetting>
                </MonsterQuerySettings>
            )}

            {/* Stats bar */}
            <div style="display: flex; gap: 1rem; margin-bottom: 0.5em; margin-top: 1em; font-size: 0.85rem; color: var(--text-muted);">
                <span>Showing {filteredMonsters.length} of {monsters.length} monsters</span>
            </div>

            {/* Table */}
            <dc.VanillaTable
                columns={columns}
                rows={filteredMonsters}
                paging={50}
            />
        </>
    );
}

return { MonsterHub };
