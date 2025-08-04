function SessionTracker() {
  const file = app.workspace.getActiveFile();
  if (!file) return <div>No active file</div>;

  const frontmatter = app.metadataCache.getFileCache(file)?.frontmatter ?? {};
  const [events, setEvents] = dc.useState(frontmatter.session_events || []);
  const [newEvent, setNewEvent] = dc.useState("");
  const [newCategory, setNewCategory] = dc.useState("general");
  const [editingIndex, setEditingIndex] = dc.useState(-1);
  const [editText, setEditText] = dc.useState("");
  const [editCategory, setEditCategory] = dc.useState("general");

  // Categories sorted alphabetically with "general" first
  const categories = ["general", "combat", "discovery", "plot", "social", "travel"];

  // Auto-resize textarea function
  const autoResize = (textarea) => {
    textarea.style.height = 'auto';
    textarea.style.height = textarea.scrollHeight + 'px';
  };

  // Reset textarea size to default
  const resetTextareaSize = (textarea) => {
    textarea.style.height = 'auto';
  };

  // Simple markdown-like rendering with basic bullet support
  const renderMarkdown = (text) => {
    let processed = text;
    
    // First, preserve double newlines as paragraph breaks
    processed = processed.replace(/\n\s*\n/g, '|||PARAGRAPH_BREAK|||');
    
    // Convert bullet points to HTML - handle different indentation levels
    processed = processed.replace(/^(\s*)[-*+]\s+(.*)$/gm, (match, spaces, content) => {
      const level = Math.floor(spaces.length / 2);
      const marginLeft = level * 20; // 20px per level
      return `<div class="bullet-point" style="margin-left: ${marginLeft}px; margin-bottom: 4px;">• ${content}</div>`;
    });
    
    // Remove single newlines around bullet points
    processed = processed.replace(/\n(?=<div class="bullet-point")/g, '');
    processed = processed.replace(/(?<=<\/div>)\n/g, '');
    
    // Restore paragraph breaks
    processed = processed.replace(/\|\|\|PARAGRAPH_BREAK\|\|\|/g, '<div style="margin-bottom: 12px;"></div>');
    
    return processed
      // Bold: **text** or __text__
      .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
      .replace(/__(.*?)__/g, '<strong>$1</strong>')
      // Italic: *text* or _text_
      .replace(/\*([^*\n]+?)\*/g, '<em>$1</em>')
      .replace(/_([^_\n]+?)_/g, '<em>$1</em>')
      // Strikethrough: ~~text~~
      .replace(/~~(.*?)~~/g, '<del>$1</del>')
      // Inline code: `text`
      .replace(/`([^`]+)`/g, '<code>$1</code>')
      // Wiki links: [[link|display]] and [[link]]
      .replace(/\[\[([^\]|]+)\|([^\]]+)\]\]/g, (match, link, display) => {
        const encodedLink = encodeURIComponent(link);
        return `<a target="_blank" rel="noopener" data-href="${link}" href="obsidian://open?file=${encodedLink}" class="internal-link" aria-label="${link}">${display}</a>`;
      })
      .replace(/\[\[([^\]]+)\]\]/g, (match, link) => {
        const encodedLink = encodeURIComponent(link);
        return `<a target="_blank" rel="noopener" data-href="${link}" href="obsidian://open?file=${encodedLink}" class="internal-link" aria-label="${link}">${link}</a>`;
      })
      // Tags: #tag
      .replace(/#([a-zA-Z0-9_-]+)/g, '<a href="#" class="tag" onclick="return false;">#$1</a>')
      // Line breaks for remaining single newlines
      .replace(/\n/g, '<br>');
  };

  // Persist to frontmatter
  const updateFrontmatter = async (newEvents) => {
    await app.fileManager.processFrontMatter(file, (fm) => {
      fm.session_events = newEvents;
    });
  };

  // Add event
  const addEvent = async () => {
    if (!newEvent.trim()) return;
    const eventObj = {
      text: newEvent,
      category: newCategory,
      timestamp: new Date().toLocaleTimeString()
    };
    const updated = [...events, eventObj];
    setEvents(updated);
    setNewEvent("");
    
    // Reset the textarea size after clearing text
    setTimeout(() => {
      const textarea = document.querySelector('textarea[data-main-input]');
      if (textarea) resetTextareaSize(textarea);
    }, 10);
    
    await updateFrontmatter(updated);
  };

  // Delete event
  const deleteEvent = async (index) => {
    const updated = events.filter((_, i) => i !== index);
    setEvents(updated);
    await updateFrontmatter(updated);
  };

  // Start editing
  const startEdit = (index) => {
    setEditingIndex(index);
    setEditText(events[index].text);
    setEditCategory(events[index].category);
    // Auto-resize after state update
    setTimeout(() => {
      const textarea = document.querySelector(`textarea[data-edit-index="${index}"]`);
      if (textarea) autoResize(textarea);
    }, 10);
  };

  // Save edit
  const saveEdit = async () => {
    const updated = [...events];
    updated[editingIndex] = {
      ...updated[editingIndex],
      text: editText,
      category: editCategory
    };
    setEvents(updated);
    setEditingIndex(-1);
    await updateFrontmatter(updated);
  };

  const getCategoryColor = (category) => {
    const colors = {
      combat: "#ff6b6b",
      travel: "#4ecdc4", 
      social: "#45b7d1",
      discovery: "#96ceb4",
      plot: "#feca57",
      general: "#95a5a6"
    };
    return colors[category] || colors.general;
  };

  return (
    <div>
      <h3>📜 What happened?</h3>
      
      {/* Add new event */}
      <div style="margin-bottom: 1em;">
        <select 
          value={newCategory} 
          onchange={e => setNewCategory(e.target.value)}
          style="margin-right: 0.5em;"
        >
          {categories.map(cat => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        <textarea
          data-main-input
          value={newEvent}
          oninput={e => {
            setNewEvent(e.target.value);
            autoResize(e.target);
          }}
          placeholder="Add a session event (supports **bold**, *italic*, [[links]], #tags, - bullets, etc.)"
          rows={3}
          style="width: calc(100% - 80px); margin-right: 0.5em; padding: 6px; font-family: inherit;"
        />
        <button onclick={addEvent}>➕ Add</button>
      </div>

      {/* Events list */}
      <div>
        {events.map((event, i) => (
          <div key={i} style={`
            margin-bottom: 0.75em; 
            padding: 0.5em; 
            border: 1px solid #ddd;
            border-radius: 4px;
            border-left: 4px solid ${getCategoryColor(event.category)};
          `}>
            {editingIndex === i ? (
              // Edit mode
              <div>
                <select 
                  value={editCategory} 
                  onchange={e => setEditCategory(e.target.value)}
                  style="margin-right: 0.5em; margin-bottom: 0.5em;"
                >
                  {categories.map(cat => (
                    <option key={cat} value={cat}>{cat}</option>
                  ))}
                </select>
                <textarea
                  data-edit-index={i}
                  value={editText}
                  oninput={e => {
                    setEditText(e.target.value);
                    autoResize(e.target);
                  }}
                  style="width: 100%; margin-bottom: 0.5em; padding: 6px; font-family: inherit; min-height: 60px; resize: vertical; overflow: hidden;"
                />
                <button onclick={saveEdit} style="margin-right: 0.5em;">💾 Save</button>
                <button onclick={() => setEditingIndex(-1)}>❌ Cancel</button>
              </div>
            ) : (
              // Display mode with rendered markdown
              <div>
                <div style="
                  display: flex; 
                  justify-content: space-between; 
                  align-items: flex-start;
                  margin-bottom: 0.25em;
                ">
                  <span style={`
                    font-size: 0.8em; 
                    color: ${getCategoryColor(event.category)};
                    font-weight: bold;
                    text-transform: uppercase;
                  `}>
                    {event.category} {event.timestamp && `• ${event.timestamp}`}
                  </span>
                  <div>
                    <button 
                      onclick={() => startEdit(i)}
                      style="margin-right: 0.25em; font-size: 0.8em;"
                    >
                      ✏️ Edit
                    </button>
                    <button 
                      onclick={() => deleteEvent(i)}
                      style="font-size: 0.8em;"
                    >
                      🗑️ Delete
                    </button>
                  </div>
                </div>
                <div 
                  style="line-height: 1.5;"
                  dangerouslySetInnerHTML={{__html: renderMarkdown(event.text)}}
                />
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}

return { SessionTracker };