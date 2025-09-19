// === Session Notes Search for D&D Campaign ===

function arr(x) {
  if (!x) return [];
  if (Array.isArray(x)) return x;
  return [x];
}

function getFMVal(obj, key) {
  return obj && obj[key] && obj[key].value !== undefined ? obj[key].value : undefined;
}

function SessionFilters({ children }) {
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

function SessionFilter({ title, icon, children, onToggle, onClear }) {
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

// Markdown renderer with placeholder approach
function renderSimpleMarkdown(text) {
  let processed = text;
  
  // Step 1: Replace wiki links with temporary placeholders
  const wikiLinks = [];
  processed = processed.replace(/\[\[([^\]]+)\]\]/g, (match, linkText) => {
    const index = wikiLinks.length;
    wikiLinks.push(linkText);
    return `___WIKI_${index}___`;
  });
  
  // Step 2: Process bold formatting
  processed = processed.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  
  // Step 3: Process italic formatting
  processed = processed.replace(/\*([^*\n]+?)\*/g, '<em>$1</em>');
  
  // Step 4: Process tags
  processed = processed.replace(/#([a-zA-Z0-9_-]+)/g, '<span style="color: #feca57;">#$1</span>');
  
  // Step 5: Replace placeholders with actual wiki links
  processed = processed.replace(/___WIKI_(\d+)___/g, (match, index) => {
    const linkText = wikiLinks[parseInt(index)];
    const encodedLink = encodeURIComponent(linkText);
    return `<a target="_blank" rel="noopener" data-href="${linkText}" href="obsidian://open?file=${encodedLink}" class="internal-link" aria-label="${linkText}" style="color: #4fc3f7; text-decoration: none;">${linkText}</a>`;
  });
  
  return processed;
}

function SessionNotesSearch({ paging = 50 }) {
  // Try to detect JS Engine plugin for enhanced markdown rendering
  let jsEngine, engine;
  try {
    jsEngine = app.plugins.plugins['js-engine'];
    engine = jsEngine?.api;
    console.debug("JS Engine available:", !!jsEngine, "API:", !!engine, "markdown.create:", !!engine?.markdown?.create);
  } catch (e) {
    console.debug("JS Engine detection failed:", e);
  }

  // Enhanced markdown rendering with JS Engine fallback
  const renderMarkdown = (text) => {
    // Try JS Engine's markdown.create first
    if (engine?.markdown?.create) {
      try {
        console.debug("Using JS Engine markdown");
        return engine.markdown.create(text);
      } catch (e) {
        console.warn("JS Engine markdown failed, using fallback:", e);
      }
    }
    
    // Fallback to our custom renderer
    return renderSimpleMarkdown(text);
  };

  // Get all session note pages
  const query = dc.useQuery(`#SessionNote`);
  const allSessionPages = dc.useArray(query, arr => arr);
  
  // State for filters
  const [filterSearch, setFilterSearch] = dc.useState('');
  const [filterCategory, setFilterCategory] = dc.useState([]);
  const [filterSession, setFilterSession] = dc.useState([]);
  const [filterDateRange, setFilterDateRange] = dc.useState('');
  const [filterDateTo, setFilterDateTo] = dc.useState('');
  const [filtersShown, setFiltersShown] = dc.useState(false);
  const [sortBy, setSortBy] = dc.useState('date'); // date, session, category, text
  
  // Extract and flatten all session events
  let allEvents = [];
  
  console.debug("Found session pages:", allSessionPages.length);
  
  allSessionPages.forEach(page => {
    console.debug("Processing page:", page.$name, "at path:", page.$path);
    
    if (page.$frontmatter && page.$frontmatter.session_events) {
      // Use DataCore's useArray to properly extract the session events
      const eventsArray = dc.useArray(page.$frontmatter.session_events, arr => arr);
      
      // Handle nested structure where session data is wrapped in key/value pairs
      let events = [];
      if (eventsArray && eventsArray.length > 0 && eventsArray[0]?.key === 'session_events') {
        events = eventsArray[0]?.value || [];
      } else {
        events = eventsArray || [];
      }
      
      console.debug("Found events for", page.$name, ":", events.length);
      
      // Add metadata to each event
      events.forEach(event => {
        const sessionDate = getFMVal(page.$frontmatter, 'sessiondate') || 'Unknown Date';
        console.debug("Session date for", page.$name, ":", sessionDate, "type:", typeof sessionDate);
        
        allEvents.push({
          ...event,
          sessionName: page.$name,
          sessionPath: page.$path,
          sessionDate: sessionDate,
          sessionNumber: extractSessionNumber(page.$name)
        });
      });
    }
  });
  
  console.debug("Total events found:", allEvents.length);
  console.debug("First event:", allEvents[0]);
  
  // If no events found, show helpful message
  if (allEvents.length === 0) {
    return (
      <div style="padding: 1em; border: 1px solid #ff9800; border-radius: 0.5em; background-color: rgba(255, 152, 0, 0.1);">
        <h3>No Session Events Found</h3>
        <p>No session events found across {allSessionPages.length} session pages.</p>
        <p>Pages found with #SessionNote tag:</p>
        <ul>
          {allSessionPages.map(page => (
            <li key={page.$name}>
              <strong>{page.$name}</strong> <code>{page.$path}</code>
              {page.$frontmatter?.session_events ? 
                ` [✓ has events: ${page.$frontmatter.session_events.length} events]` : 
                ` [✗ no session_events in frontmatter]`
              }
            </li>
          ))}
        </ul>
        <p><em>Make sure your session notes have session_events in frontmatter and are tagged with #SessionNote.</em></p>
      </div>
    );
  }
  
  // Get unique values for filters
  const allCategories = Array.from(new Set(allEvents.map(event => event.category).filter(Boolean))).sort();
  const allSessions = Array.from(new Set(allEvents.map(event => event.sessionName).filter(Boolean))).sort();
  
  // Clear and toggle functions for enhanced filter controls
  const clearFilterCategory = () => setFilterCategory([]);
  const toggleFilterCategory = () => setFilterCategory(allCategories.filter(c => !filterCategory.includes(c)));
  
  const clearFilterSession = () => setFilterSession([]);
  const toggleFilterSession = () => setFilterSession(allSessions.filter(s => !filterSession.includes(s)));
  
  // Apply filters
  const filteredEvents = allEvents.filter(event => {
    if (filterSearch && !event?.text?.toLowerCase().includes(filterSearch.toLowerCase())) {
      return false;
    }
    if (filterCategory.length > 0 && !filterCategory.includes(event?.category)) {
      return false;
    }
    // Individual session name filtering
    if (filterSession.length > 0 && !filterSession.includes(event?.sessionName)) {
      return false;
    }
    if (filterDateRange || filterDateTo) {
      // Parse event date from DD/MM/YYYY format
      let eventDate;
      const dateStr = event?.sessionDate;
      if (dateStr && dateStr !== 'Unknown Date' && typeof dateStr === 'string') {
        const parts = dateStr.split('/');
        if (parts.length === 3) {
          const [day, month, year] = parts;
          eventDate = new Date(year, month - 1, day);
        }
      }
      
      if (!eventDate || isNaN(eventDate.getTime())) {
        return false;
      }
      
      // Check from date
      if (filterDateRange) {
        const filterFromDate = new Date(filterDateRange);
        if (eventDate < filterFromDate) {
          return false;
        }
      }
      
      // Check to date
      if (filterDateTo) {
        const filterToDate = new Date(filterDateTo);
        if (eventDate > filterToDate) {
          return false;
        }
      }
    }
    return true;
  });
  
  console.debug("After filtering:", filteredEvents.length, "events");
  console.debug("Filter states:", { filterSearch, filterCategory, filterSession, filterDateRange, filterDateTo });
  
  // Apply sorting
  filteredEvents.sort((a, b) => {
    switch (sortBy) {
      case 'session':
        return (a.sessionNumber || 0) - (b.sessionNumber || 0) || a.sessionName.localeCompare(b.sessionName);
      case 'category':
        return a.category.localeCompare(b.category) || a.sessionName.localeCompare(b.sessionName);
      case 'text':
        return a.text.localeCompare(b.text);
      default: // date
        // Parse dates from DD/MM/YYYY format for proper sorting
        const parseSessionDate = (dateStr) => {
          if (!dateStr || dateStr === 'Unknown Date' || typeof dateStr !== 'string') return new Date(0);
          const parts = dateStr.split('/');
          if (parts.length === 3) {
            const [day, month, year] = parts;
            return new Date(year, month - 1, day);
          }
          return new Date(0);
        };
        
        const dateA = parseSessionDate(a.sessionDate);
        const dateB = parseSessionDate(b.sessionDate);
        return dateB - dateA || (b.sessionNumber || 0) - (a.sessionNumber || 0);
    }
  });
  
  const columns = [
    {
      id: "Session",
      value: event => {
        const href = `obsidian://open?file=${encodeURIComponent(event.sessionPath)}`;
        return (
          <a
            target="_blank"
            rel="noopener"
            data-href={event.sessionPath}
            href={href}
            class="internal-link"
            aria-label={event.sessionPath}
            style="color: #4fc3f7; text-decoration: none; font-weight: 500;"
            title={`Open ${event.sessionName}`}
          >
            {event.sessionName}
          </a>
        );
      }
    },
    { 
      id: "Date", 
      value: event => {
        const dateStr = event.sessionDate;
        if (!dateStr || dateStr === 'Unknown Date' || typeof dateStr !== 'string') return dateStr || 'Unknown Date';
        
        // Try to parse DD/MM/YYYY format
        const parts = dateStr.split('/');
        if (parts.length === 3) {
          const [day, month, year] = parts;
          const date = new Date(year, month - 1, day); // month is 0-indexed
          if (!isNaN(date.getTime())) {
            return date.toLocaleDateString('en-GB'); // UK format: DD/MM/YYYY
          }
        }
        
        // Fallback to original string if parsing fails
        return dateStr;
      }
    },
    { 
      id: "Category", 
      value: event => {
        const category = event?.category || 'General';
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
    {
      id: "Event",
      value: event => {
        const text = event?.text || 'No text';
        
        // If searching, show full text; otherwise truncate
        const shouldTruncate = !filterSearch || filterSearch.trim() === '';
        const displayText = shouldTruncate && text.length > 200 
          ? text.substring(0, 200) + '...' 
          : text;
        
        return (
          <div 
            style="line-height: 1.4; width: 100%; word-wrap: break-word;"
            title={shouldTruncate && text.length > 200 ? text : undefined}
            dangerouslySetInnerHTML={{__html: renderMarkdown(displayText)}}
          />
        );
      }
    }
  ];
  
  return (
    <>
      <div style="display: flex; gap: 0.75em; align-items: center; margin-bottom: 1em;">
        <input
          type="search"
          placeholder="Search events..."
          value={filterSearch}
          oninput={e => setFilterSearch(e.target.value)}
          style="flex-grow: 1;"
        />
        <select
          value={sortBy}
          onchange={e => setSortBy(e.target.value)}
          style="min-width: 120px;"
        >
          <option value="date">Sort by Date</option>
          <option value="session">Sort by Session</option>
          <option value="category">Sort by Category</option>
          <option value="text">Sort by Text</option>
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
            clearFilterSession();
            setFilterDateRange('');
            setFilterDateTo('');
          }}
          title="Clear all filters"
        >
          Clear
        </button>
      </div>
      
      {filtersShown && (
        <SessionFilters>
          <SessionFilter 
            title="Category" 
            icon="lucide-tag"
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
          </SessionFilter>
          
          <SessionFilter 
            title="Sessions" 
            icon="lucide-book-open"
            onToggle={toggleFilterSession}
            onClear={clearFilterSession}
          >
            <div style="max-height: 200px; overflow-y: auto;">
                {allSessions
                  .map(session => {
                    // Find the session date for this session
                    const sessionEvent = allEvents.find(event => event.sessionName === session);
                    const sessionDate = sessionEvent?.sessionDate || 'Unknown Date';
                    return { session, sessionDate };
                  })
                  .sort((a, b) => {
                    // Sort by date, with most recent first
                    const parseDate = (dateStr) => {
                      if (!dateStr || dateStr === 'Unknown Date') return new Date(0);
                      const parts = dateStr.split('/');
                      if (parts.length === 3) {
                        const [day, month, year] = parts;
                        return new Date(year, month - 1, day);
                      }
                      return new Date(0);
                    };
                    return parseDate(b.sessionDate) - parseDate(a.sessionDate);
                  })
                  .map(({ session, sessionDate }) => (
                    <label style="display: block" key={session}>
                      <input
                        type="checkbox"
                        checked={filterSession.includes(session)}
                        onchange={e =>
                          setFilterSession(
                            e.target.checked
                              ? [...filterSession, session]
                              : filterSession.filter(x => x !== session)
                          )
                        }
                      />{' '}
                      <span title={`Session date: ${sessionDate}`}>
                        {session} {sessionDate !== 'Unknown Date' ? `(${sessionDate})` : ''}
                      </span>
                    </label>
                  ))}
            </div>
          </SessionFilter>
          
          <SessionFilter title="Date Range" icon="lucide-calendar">
            <div style="margin-bottom: 1em;">
              <div style="font-weight: 500; margin-bottom: 0.25em;">From Date</div>
              <input
                type="date"
                value={filterDateRange}
                onchange={e => setFilterDateRange(e.target.value)}
                style="width: 100%;"
              />
            </div>
            <div>
              <div style="font-weight: 500; margin-bottom: 0.25em;">To Date</div>
              <input
                type="date"
                value={filterDateTo}
                onchange={e => setFilterDateTo(e.target.value)}
                style="width: 100%;"
              />
            </div>
          </SessionFilter>
        </SessionFilters>
      )}
      
      <div style="margin-bottom: 1em; font-size: 0.9em; color: var(--text-muted);">
        Showing {filteredEvents.length} of {allEvents.length} events from {allSessionPages.length} sessions
      </div>
      
      {(() => {
        console.debug("Passing to table - filteredEvents:", filteredEvents);
        console.debug("First filtered event:", filteredEvents[0]);
        console.debug("Columns structure:", columns.map(c => c.id));
        return <dc.VanillaTable columns={columns} rows={filteredEvents} paging={paging} />;
      })()}
    </>
  );
}

// Helper functions
function getCategoryColor(category) {
  const colors = {
    'combat': '#ff6b6b',
    'travel': '#4ecdc4', 
    'social': '#45b7d1',
    'discovery': '#96ceb4',
    'plot': '#feca57',
    'general': '#95a5a6',
    'General': '#95a5a6'
  };
  return colors[category] || '#95a5a6';
}

function extractSessionNumber(sessionName) {
  const match = sessionName.match(/(\d+)/);
  return match ? parseInt(match[0]) : 0;
}

return { SessionNotesSearch };