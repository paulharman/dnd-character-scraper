// === Party Languages Display ===

const CHARACTER_DIR = "Campaign/Parties/Characters";

function arr(x) {
  if (!x) return [];
  if (Array.isArray(x)) return x;
  return [x];
}

function getFMVal(obj, key) {
  return obj && obj[key] && obj[key].value !== undefined ? obj[key].value : undefined;
}

function PartyLanguages() {
  // Use the same pattern as SpellGenerator for finding character files
  const chars = dc.useArray(dc.useQuery(`#character-sheet and path("${CHARACTER_DIR}")`), arr => arr);
  
  console.log("Found characters:", chars.length);
  console.log("Sample character:", chars[0]);
  
  // Extract languages from each character
  const partyLanguages = new Map();
  const characterLanguages = new Map();
  
  chars.forEach(character => {
    const characterName = character.character_name || character.$name;
    
    console.log("Processing character:", characterName);
    
    if (!characterName) return;
    
    // Get languages using the same pattern as SpellGenerator
    let rawLanguages = null;
    if (typeof character.value === "function") rawLanguages = character.value("languages");
    if (!rawLanguages && character.frontmatter) rawLanguages = character.frontmatter["languages"];
    if (!rawLanguages && character.$frontmatter) rawLanguages = character.$frontmatter["languages"];
    
    console.log("Raw languages for", characterName, ":", rawLanguages);
    console.log("Available frontmatter keys:", Object.keys(character.frontmatter || {}));
    console.log("Available $frontmatter keys:", Object.keys(character.$frontmatter || {}));
    
    if (rawLanguages) {
      const languages = arr(rawLanguages);
      const species = character.species || character.race || 'Unknown';
      const background = character.background || 'Unknown';
      
      console.log("Languages for", characterName, ":", languages);
      
      const characterLanguageData = [];
      
      languages.forEach(language => {
        if (language && typeof language === 'string') {
          // Basic source mapping for display purposes
          let source = 'Standard';
          if (language === 'Common') {
            source = 'Standard';
          } else if (species.toLowerCase().includes('elf') && language === 'Elvish') {
            source = `Species: ${species}`;
          } else if (species.toLowerCase().includes('dwarf') && language === 'Dwarvish') {
            source = `Species: ${species}`;
          } else if (species.toLowerCase().includes('dragonborn') && language === 'Draconic') {
            source = `Species: ${species}`;
          } else if (species.toLowerCase().includes('tiefling') && language === 'Infernal') {
            source = `Species: ${species}`;
          } else if (species.toLowerCase().includes('halfling') && language === 'Halfling') {
            source = `Species: ${species}`;
          } else if (species.toLowerCase().includes('gnome') && language === 'Gnomish') {
            source = `Species: ${species}`;
          } else if (species.toLowerCase().includes('orc') && language === 'Orc') {
            source = `Species: ${species}`;
          } else {
            source = `Background: ${background}`;
          }
          
          characterLanguageData.push({ language, source });
          
          // Add to party-wide language map
          if (!partyLanguages.has(language)) {
            partyLanguages.set(language, new Set());
          }
          partyLanguages.get(language).add(characterName);
        }
      });
      
      if (characterLanguageData.length > 0) {
        characterLanguages.set(characterName, characterLanguageData);
      }
    }
  });
  
  console.log("Final character languages:", characterLanguages);
  console.log("Final party languages:", partyLanguages);
  
  // Sort languages alphabetically
  const sortedLanguages = Array.from(partyLanguages.entries())
    .sort(([a], [b]) => a.localeCompare(b));
    
  const sortedCharacters = Array.from(characterLanguages.entries())
    .sort(([a], [b]) => a.localeCompare(b));
  
  // Debug display if no data found
  if (chars.length === 0) {
    return (
      <div>
        <h2>🗣️ Party Languages Debug</h2>
        <p>No character files found with 'character-sheet' tag in {CHARACTER_DIR}</p>
      </div>
    );
  }
  
  if (sortedCharacters.length === 0) {
    return (
      <div>
        <h2>🗣️ Party Languages</h2>
        <p>Found {chars.length} character files but no languages extracted.</p>
        <p>Check the console for debug info.</p>
      </div>
    );
  }
  
  return (
    <div style="font-family: var(--default-font), -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1000px; margin: 0 auto; padding: 20px;">
      <style>{`
        .language-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
          gap: 20px;
          margin-bottom: 30px;
        }
        .language-card {
          background: var(--background-secondary);
          border: 1px solid var(--background-modifier-border);
          border-radius: 8px;
          padding: 15px;
        }
        .language-name {
          font-size: 1.1em;
          font-weight: bold;
          color: var(--text-accent);
          margin-bottom: 8px;
        }
        .character-list {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
        }
        .character-tag {
          background: var(--interactive-accent);
          color: var(--text-on-accent);
          padding: 4px 8px;
          border-radius: 4px;
          font-size: 0.85em;
          white-space: nowrap;
        }
        .stats-bar {
          background: var(--background-secondary);
          padding: 15px;
          border-radius: 8px;
          margin-bottom: 20px;
          display: flex;
          justify-content: space-around;
          text-align: center;
        }
        .stat-item {
          display: flex;
          flex-direction: column;
        }
        .stat-number {
          font-size: 1.5em;
          font-weight: bold;
          color: var(--text-accent);
        }
        .stat-label {
          font-size: 0.9em;
          color: var(--text-muted);
        }
        .character-section {
          margin-top: 30px;
        }
        .character-card {
          background: var(--background-secondary);
          border-left: 4px solid var(--interactive-accent);
          padding: 15px;
          margin-bottom: 15px;
          border-radius: 0 8px 8px 0;
        }
        .character-card h4 {
          margin: 0 0 10px 0;
          color: var(--text-accent);
        }
        .language-item {
          display: inline-block;
          background: var(--background-primary);
          border: 1px solid var(--background-modifier-border);
          padding: 4px 8px;
          margin: 2px;
          border-radius: 4px;
          font-size: 0.85em;
        }
        .language-source {
          color: var(--text-muted);
          font-style: italic;
        }
        .section-header {
          display: flex;
          align-items: center;
          gap: 10px;
          margin-bottom: 15px;
          padding-bottom: 8px;
          border-bottom: 2px solid var(--background-modifier-border);
        }
        .section-icon {
          font-size: 1.2em;
        }
      `}</style>

      <div className="section-header">
        <span className="section-icon">🗣️</span>
        <h2>Party Languages Overview</h2>
      </div>

      <div className="stats-bar">
        <div className="stat-item">
          <div className="stat-number">{sortedLanguages.length}</div>
          <div className="stat-label">Total Languages</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">{sortedCharacters.length}</div>
          <div className="stat-label">Party Members</div>
        </div>
        <div className="stat-item">
          <div className="stat-number">
            {sortedLanguages.filter(([_, speakers]) => speakers.size > 1).length}
          </div>
          <div className="stat-label">Shared Languages</div>
        </div>
      </div>

      <div className="section-header">
        <span className="section-icon">📚</span>
        <h3>Languages by Coverage</h3>
      </div>

      <div className="language-grid">
        {sortedLanguages.map(([language, speakers]) => (
          <div key={language} className="language-card">
            <div className="language-name">
              {language}
              <span style={{ 
                fontSize: '0.8em', 
                marginLeft: '8px', 
                color: 'var(--text-muted)' 
              }}>
                ({speakers.size} speaker{speakers.size !== 1 ? 's' : ''})
              </span>
            </div>
            <div className="character-list">
              {Array.from(speakers).sort().map(speaker => (
                <span key={speaker} className="character-tag">
                  {speaker}
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div className="character-section">
        <div className="section-header">
          <span className="section-icon">👥</span>
          <h3>Languages by Character</h3>
        </div>

        {sortedCharacters.map(([character, languages]) => (
          <div key={character} className="character-card">
            <h4>{character}</h4>
            <div>
              {languages
                .sort((a, b) => a.language.localeCompare(b.language))
                .map(({ language, source }, index) => (
                <span key={index} className="language-item">
                  <strong>{language}</strong>
                  <span className="language-source"> ({source})</span>
                </span>
              ))}
            </div>
          </div>
        ))}
      </div>

      <div style={{ 
        marginTop: '30px', 
        padding: '15px', 
        background: 'var(--background-secondary)', 
        borderRadius: '8px',
        fontSize: '0.9em',
        color: 'var(--text-muted)'
      }}>
        <strong>📊 Data Source:</strong> Character sheets in {CHARACTER_DIR} (filtered by 'character-sheet' tag)
        <br />
        <strong>🔄 Last Updated:</strong> {new Date().toLocaleString()}
      </div>
    </div>
  );
}

return { PartyLanguages };