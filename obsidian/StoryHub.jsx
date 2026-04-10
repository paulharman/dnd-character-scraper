// ══════════════════════════════════════════════════════════════════════════════
// STORY HUB - Campaign chronicle / session summary reader
// ══════════════════════════════════════════════════════════════════════════════
// Shows all sessions in chronological order with their quicknote summaries.
// Searchable across session name, subtitle (alias), and quicknote content.
// Data read from #SessionNote frontmatter: quicknote, sessiondate, whichparty, aliases.

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

function getStr(obj, key) {
    const val = getVal(obj, key);
    return val ? String(val) : '';
}

function stripLinks(val) {
    if (!val) return '';
    const str = String(val);
    return str.replace(/\[\[([^\]|]+?)(?:\|([^\]]+?))?\]\]/g, (_, target, display) => display || target);
}

// Parse DD/MM/YYYY to a Date object for sorting
function parseSessionDate(dateStr) {
    if (!dateStr || typeof dateStr !== 'string') return new Date(0);
    const parts = dateStr.split('/');
    if (parts.length === 3) {
        const [day, month, year] = parts;
        const d = new Date(year, month - 1, day);
        if (!isNaN(d.getTime())) return d;
    }
    return new Date(0);
}

// Convert session name to a sort number, handling both digit and word forms
const WORD_NUMBERS = {
    one: 1, two: 2, three: 3, four: 4, five: 5, six: 6, seven: 7, eight: 8,
    nine: 9, ten: 10, eleven: 11, twelve: 12, thirteen: 13, fourteen: 14,
    fifteen: 15, sixteen: 16, seventeen: 17, eighteen: 18, nineteen: 19,
    twenty: 20, 'twenty-one': 21, 'twenty one': 21, 'twenty-two': 22,
    'twenty two': 22, 'twenty-three': 23, 'twenty three': 23,
    'twenty-four': 24, 'twenty four': 24, 'twenty-five': 25, 'twenty five': 25,
    'twenty-six': 26, 'twenty six': 26, 'twenty-seven': 27, 'twenty seven': 27,
    'twenty-eight': 28, 'twenty eight': 28, 'twenty-nine': 29, 'twenty nine': 29,
    thirty: 30,
};

function extractSessionNumber(name) {
    const lower = name.toLowerCase();
    // Check compound word numbers first (longer strings match before shorter)
    const sorted = Object.keys(WORD_NUMBERS).sort((a, b) => b.length - a.length);
    for (const word of sorted) {
        if (lower.includes(word)) return WORD_NUMBERS[word];
    }
    const match = name.match(/(\d+)/);
    return match ? parseInt(match[0]) : 999;
}

// Minimal markdown renderer - preserves line breaks, handles bold/italic/wikilinks
function renderMarkdown(text) {
    if (!text) return '';
    let out = text;
    const wikiLinks = [];
    out = out.replace(/\[\[([^\]]+)\]\]/g, (_, linkText) => {
        const i = wikiLinks.length;
        wikiLinks.push(linkText);
        return `___W${i}___`;
    });
    out = out.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    out = out.replace(/\*([^*\n]+?)\*/g, '<em>$1</em>');
    out = out.replace(/___W(\d+)___/g, (_, i) => {
        const lt = wikiLinks[parseInt(i)];
        return `<a target="_blank" rel="noopener" data-href="${lt}" href="obsidian://open?file=${encodeURIComponent(lt)}" class="internal-link" style="color: #4fc3f7; text-decoration: none;">${lt}</a>`;
    });
    return out;
}

// ── Filter Panel ─────────────────────────────────────────────────────────────

function FilterPanel({ children }) {
    return (
        <div style="
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 1.5em;
            margin-top: 1em;
            align-items: start;
        ">
            {children}
        </div>
    );
}

function FilterGroup({ title, icon, children, onClear }) {
    return (
        <div style="
            border: 1px solid var(--background-modifier-border, #444);
            border-radius: 0.5em;
            padding: 1em;
            background-color: var(--background-secondary-alt, #23272e);
        ">
            <div style="font-weight: 600; margin-bottom: 0.5em; display: flex; align-items: center; gap: 0.5em;">
                <dc.Icon icon={icon} />
                <span style="flex-grow: 1;">{title}</span>
                {onClear && (
                    <span onclick={onClear} style="cursor: pointer; opacity: 0.7;" title="Clear">
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

// ── Main Component ────────────────────────────────────────────────────────────

function StoryHub({ paging = 20 }) {
    const query = dc.useQuery(`#SessionNote and path("Campaign/Parties/Session Notes")`);
    const allPages = dc.useArray(query, arr => arr);

    const [filterSearch, setFilterSearch] = dc.useState('');
    const [filterParty, setFilterParty] = dc.useState([]);
    const [filtersShown, setFiltersShown] = dc.useState(false);
    const [sortDir, setSortDir] = dc.useState('asc'); // asc = oldest first (story order)

    // Files in the session notes folder that aren't actual sessions
    const EXCLUDED_NAMES = new Set(['Inventory tracker']);

    // Build session list from frontmatter (all sessions, with or without quicknote)
    const allSessions = [];
    allPages.forEach(page => {
        if (EXCLUDED_NAMES.has(page.$name)) return;
        const fm = page.$frontmatter;
        const quicknote = getStr(fm, 'quicknote');
        const dateStr = getStr(fm, 'sessiondate');
        const rawParty = getStr(fm, 'whichparty');
        const aliases = toArray(getVal(fm, 'aliases'));
        const subtitle = aliases.length > 0 ? String(aliases[0]) : '';
        allSessions.push({
            name: page.$name || '',
            path: page.$path || '',
            date: dateStr,
            dateObj: parseSessionDate(dateStr),
            sessionNum: extractSessionNumber(page.$name || ''),
            party: stripLinks(rawParty),
            subtitle,
            quicknote,
        });
    });

    // Sessions missing a quicknote (for the warning section)
    const missingSummary = allSessions
        .filter(s => !s.quicknote)
        .sort((a, b) => a.dateObj - b.dateObj || a.sessionNum - b.sessionNum);

    // All parties for filter panel
    const allParties = Array.from(new Set(allSessions.map(s => s.party).filter(Boolean))).sort();

    // Filter
    const lowerSearch = filterSearch.toLowerCase().trim();
    const filtered = allSessions.filter(s => {
        if (lowerSearch) {
            const searchable = `${s.name} ${s.subtitle} ${s.quicknote || ''}`.toLowerCase();
            if (!lowerSearch.split(/\s+/).every(w => searchable.includes(w))) return false;
        }
        if (filterParty.length > 0 && !filterParty.includes(s.party)) return false;
        return true;
    });

    // Sort chronologically (oldest first = story order, or reversed)
    filtered.sort((a, b) => {
        const diff = a.dateObj - b.dateObj || a.sessionNum - b.sessionNum;
        return sortDir === 'asc' ? diff : -diff;
    });

    const columns = [
        {
            id: 'Session',
            value: s => (
                <a
                    target="_blank" rel="noopener"
                    data-href={s.path}
                    href={`obsidian://open?file=${encodeURIComponent(s.path)}`}
                    class="internal-link"
                    style="color: #4fc3f7; text-decoration: none; font-weight: 500; white-space: nowrap;"
                >
                    {s.name}
                </a>
            ),
        },
        {
            id: 'Date',
            value: s => <span style="white-space: nowrap;">{s.date || '—'}</span>,
        },
        {
            id: 'Subtitle',
            value: s => s.subtitle ? <em>{s.subtitle}</em> : '—',
        },
        {
            id: 'Summary',
            value: s => {
                if (!s.quicknote) {
                    return (
                        <span style="color: var(--text-muted); font-style: italic;">
                            No summary written
                        </span>
                    );
                }
                return (
                    <div
                        style="line-height: 1.55; width: 100%; word-wrap: break-word; white-space: pre-line;"
                        dangerouslySetInnerHTML={{ __html: renderMarkdown(s.quicknote) }}
                    />
                );
            },
        },
    ];

    return (
        <>
            {/* ── Toolbar ── */}
            <div style="display: flex; gap: 0.75em; align-items: center; margin-bottom: 1em;">
                <input
                    type="search"
                    placeholder="Search sessions..."
                    value={filterSearch}
                    oninput={e => setFilterSearch(e.target.value)}
                    style="flex-grow: 1;"
                />
                <button
                    onclick={() => setSortDir(sortDir === 'asc' ? 'desc' : 'asc')}
                    title={sortDir === 'asc' ? 'Oldest first (story order)' : 'Newest first'}
                >
                    {sortDir === 'asc' ? '↑ Oldest' : '↓ Newest'}
                </button>
                <button
                    class={filtersShown ? 'primary' : ''}
                    onclick={() => setFiltersShown(!filtersShown)}
                    title="Show/hide filters"
                >
                    ⚙
                </button>
                <button
                    onclick={() => { setFilterSearch(''); setFilterParty([]); }}
                    title="Clear all filters"
                >
                    Clear All
                </button>
            </div>

            {/* ── Filter Panel ── */}
            {filtersShown && allParties.length > 0 && (
                <FilterPanel>
                    <FilterGroup
                        title="Party"
                        icon="lucide-users"
                        onClear={() => setFilterParty([])}
                    >
                        {allParties.map(p => (
                            <label style="display: block;" key={p}>
                                <input
                                    type="checkbox"
                                    checked={filterParty.includes(p)}
                                    onchange={e => setFilterParty(
                                        e.target.checked
                                            ? [...filterParty, p]
                                            : filterParty.filter(x => x !== p)
                                    )}
                                />{' '}{p}
                            </label>
                        ))}
                    </FilterGroup>
                </FilterPanel>
            )}

            {/* ── Stats bar ── */}
            <div style="display: flex; gap: 1rem; margin-bottom: 0.5em; margin-top: 1em; font-size: 0.85rem; color: var(--text-muted);">
                <span>Showing {filtered.length} of {allSessions.length} sessions</span>
            </div>

            <dc.VanillaTable columns={columns} rows={filtered} paging={paging} />

            {/* ── Missing Summary Warning ── */}
            {missingSummary.length > 0 && (
                <div style="
                    margin-top: 2em;
                    border: 1px solid rgba(255, 152, 0, 0.5);
                    border-radius: 0.5em;
                    padding: 1em 1.25em;
                    background: rgba(255, 152, 0, 0.06);
                ">
                    <div style="font-weight: 600; margin-bottom: 0.5em; color: #ff9800;">
                        ⚠ {missingSummary.length} session{missingSummary.length > 1 ? 's' : ''} missing a quick note
                    </div>
                    <div style="display: flex; flex-direction: column; gap: 0.3em;">
                        {missingSummary.map(s => (
                            <div key={s.path} style="display: flex; gap: 1em; align-items: baseline; font-size: 0.9em;">
                                <a
                                    target="_blank" rel="noopener"
                                    data-href={s.path}
                                    href={`obsidian://open?file=${encodeURIComponent(s.path)}`}
                                    class="internal-link"
                                    style="color: #4fc3f7; text-decoration: none;"
                                >
                                    {s.name}
                                </a>
                                {s.date && <span style="color: var(--text-muted);">{s.date}</span>}
                                {s.subtitle && <span style="color: var(--text-muted); font-style: italic;">{s.subtitle}</span>}
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </>
    );
}

return { StoryHub };