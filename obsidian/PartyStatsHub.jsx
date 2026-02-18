// === Party Stats Hub ===
// Displays party character statistics for comparison

const CHARACTER_DIR = "Campaign/Parties/Characters";
const ABILITIES = ['strength', 'dexterity', 'constitution', 'intelligence', 'wisdom', 'charisma'];
const ABILITY_SHORT = { strength: 'STR', dexterity: 'DEX', constitution: 'CON', intelligence: 'INT', wisdom: 'WIS', charisma: 'CHA' };

const ALL_SKILLS = [
  { name: 'Acrobatics', key: 'Acrobatics', bonusKey: 'acrobatics', ability: 'DEX' },
  { name: 'Animal Handling', key: 'Animal_Handling', bonusKey: 'animal_handling', ability: 'WIS' },
  { name: 'Arcana', key: 'Arcana', bonusKey: 'arcana', ability: 'INT' },
  { name: 'Athletics', key: 'Athletics', bonusKey: 'athletics', ability: 'STR' },
  { name: 'Deception', key: 'Deception', bonusKey: 'deception', ability: 'CHA' },
  { name: 'History', key: 'History', bonusKey: 'history', ability: 'INT' },
  { name: 'Insight', key: 'Insight', bonusKey: 'insight', ability: 'WIS' },
  { name: 'Intimidation', key: 'Intimidation', bonusKey: 'intimidation', ability: 'CHA' },
  { name: 'Investigation', key: 'Investigation', bonusKey: 'investigation', ability: 'INT' },
  { name: 'Medicine', key: 'Medicine', bonusKey: 'medicine', ability: 'WIS' },
  { name: 'Nature', key: 'Nature', bonusKey: 'nature', ability: 'INT' },
  { name: 'Perception', key: 'Perception', bonusKey: 'perception', ability: 'WIS' },
  { name: 'Performance', key: 'Performance', bonusKey: 'performance', ability: 'CHA' },
  { name: 'Persuasion', key: 'Persuasion', bonusKey: 'persuasion', ability: 'CHA' },
  { name: 'Religion', key: 'Religion', bonusKey: 'religion', ability: 'INT' },
  { name: 'Sleight of Hand', key: 'Sleight_Of_Hand', bonusKey: 'sleight_of_hand', ability: 'DEX' },
  { name: 'Stealth', key: 'Stealth', bonusKey: 'stealth', ability: 'DEX' },
  { name: 'Survival', key: 'Survival', bonusKey: 'survival', ability: 'WIS' }
];

const SAVING_THROWS = ['Strength', 'Dexterity', 'Constitution', 'Intelligence', 'Wisdom', 'Charisma'];

function arr(x) {
  if (!x) return [];
  if (Array.isArray(x)) return x;
  return [x];
}

function getVal(character, key) {
  let val = null;
  if (typeof character.value === "function") val = character.value(key);
  if (val == null && character.frontmatter) val = character.frontmatter[key];
  if (val == null && character.$frontmatter) val = character.$frontmatter[key];
  return val;
}

function getAbilityScores(character) {
  const raw = getVal(character, 'ability_scores');
  if (!raw) return null;
  const scores = {};
  ABILITIES.forEach(a => {
    const v = raw[a];
    scores[a] = (v && v.value !== undefined) ? v.value : (typeof v === 'number' ? v : null);
  });
  return scores;
}

function getAbilityModifiers(character) {
  const raw = getVal(character, 'ability_modifiers');
  if (!raw) return null;
  const mods = {};
  ABILITIES.forEach(a => {
    const v = raw[a];
    mods[a] = (v && v.value !== undefined) ? v.value : v;
  });
  return mods;
}

function getNum(character, key) {
  const v = getVal(character, key);
  if (v == null || v === 'None') return null;
  const n = Number(v);
  return isNaN(n) ? null : n;
}

function getStr(character, key) {
  const v = getVal(character, key);
  if (v == null || v === 'None') return null;
  return String(v);
}

function getPartyFromPath(character) {
  const path = character.$path || character.path || '';
  if (path.includes('Party 2')) return 'Party 2';
  if (path.includes('Party 1')) return 'Party 1';
  return 'Unknown';
}

function getNestedVal(character, key, subkey) {
  const obj = getVal(character, key);
  if (!obj) return null;
  const v = obj[subkey];
  if (v && v.value !== undefined) return v.value;
  return typeof v === 'number' ? v : null;
}

function formatBonus(n) {
  if (n == null) return '\u2014';
  return n >= 0 ? `+${n}` : `${n}`;
}

function CharLink({ character, children, style }) {
  if (!character.filePath) return <span style={style}>{children || character.name}</span>;
  return (
    <a target="_blank" rel="noopener"
      data-href={character.filePath}
      href={`obsidian://open?file=${encodeURIComponent(character.filePath)}`}
      class="internal-link"
      aria-label={character.filePath}
      style={style || ''}
    >{children || character.name}</a>
  );
}

function hpColor(pct) {
  if (pct > 0.5) return '#4caf50';
  if (pct > 0.25) return '#ff9800';
  return '#f44336';
}

function getClassColor(cls) {
  const colors = {
    'Barbarian': '#e76f51', 'Bard': '#ab47bc', 'Cleric': '#78909c',
    'Druid': '#66bb6a', 'Fighter': '#8d6e63', 'Monk': '#26c6da',
    'Paladin': '#ffd54f', 'Ranger': '#43a047', 'Rogue': '#455a64',
    'Sorcerer': '#ef5350', 'Warlock': '#7e57c2', 'Wizard': '#42a5f5',
    'Artificer': '#ff8a65', 'Blood Hunter': '#c62828'
  };
  return colors[cls] || '#607d8b';
}

function PartyStatsHub() {
  const chars = dc.useArray(dc.useQuery(`#character-sheet and path("${CHARACTER_DIR}")`), arr => arr);

  // Read initial party filter from this hub page's frontmatter
  const hubFile = dc.app.vault.getAbstractFileByPath("Party Stats Hub.md");
  const hubCache = hubFile ? dc.app.metadataCache.getFileCache(hubFile) : null;
  const initialParty = hubCache?.frontmatter?.party_filter || 'Party 1';
  const [selectedParty, setSelectedParty] = dc.useState(initialParty);

  // Extract character data
  const characters = chars
    .filter(c => getVal(c, 'character_name'))
    .map(c => ({
      name: getVal(c, 'character_name'),
      avatar: getStr(c, 'avatar_url'),
      class: getStr(c, 'class') || '?',
      subclass: getStr(c, 'subclass') || '',
      level: getNum(c, 'level') || 0,
      species: getStr(c, 'species') || '?',
      maxHp: getNum(c, 'max_hp') || 0,
      currentHp: getNum(c, 'current_hp') || 0,
      tempHp: getNum(c, 'temp_hp') || 0,
      ac: getNum(c, 'armor_class') || 0,
      initiative: getStr(c, 'initiative') || '+0',
      speed: getStr(c, 'speed') || '30 ft',
      movement: getVal(c, 'movement') || {},
      profBonus: getNum(c, 'proficiency_bonus') || 2,
      spellSaveDc: getNum(c, 'spell_save_dc'),
      spellCount: getNum(c, 'spell_count') || 0,
      passivePerception: getNum(c, 'passive_perception'),
      passiveInvestigation: getNum(c, 'passive_investigation'),
      passiveInsight: getNum(c, 'passive_insight'),
      scores: getAbilityScores(c) || {},
      modifiers: getAbilityModifiers(c) || {},
      skills: arr(getVal(c, 'skill_proficiencies')),
      expertise: arr(getVal(c, 'skill_expertise')),
      skillBonuses: getVal(c, 'skill_bonuses') || {},
      stealthDisadvantage: getVal(c, 'stealth_disadvantage') === true || getVal(c, 'stealth_disadvantage') === 'True',
      saves: arr(getVal(c, 'saving_throw_proficiencies')),
      saveBonuses: getVal(c, 'saving_throw_bonuses') || {},
      toolProficiencies: arr(getVal(c, 'tool_proficiencies')),
      senses: getVal(c, 'senses') || {},
      party: getPartyFromPath(c),
      filePath: c.$path || ''
    }))
    .filter(c => selectedParty === 'All' || c.party === selectedParty)
    .sort((a, b) => a.name.localeCompare(b.name));

  // Discover available parties
  const allParties = [...new Set(chars.filter(c => getVal(c, 'character_name')).map(c => getPartyFromPath(c)))].sort();

  // Compute column highs/lows for ability modifiers (what matters in gameplay)
  const modMax = {};
  const modMin = {};
  ABILITIES.forEach(a => {
    const vals = characters.map(c => c.modifiers[a]).filter(v => v != null);
    modMax[a] = vals.length ? Math.max(...vals) : null;
    modMin[a] = vals.length ? Math.min(...vals) : null;
  });

  // Summary stats
  const partySize = characters.length;
  const avgLevel = partySize ? (characters.reduce((s, c) => s + c.level, 0) / partySize).toFixed(1) : 0;
  const totalHp = characters.reduce((s, c) => s + c.maxHp, 0);
  const avgAc = partySize ? (characters.reduce((s, c) => s + c.ac, 0) / partySize).toFixed(1) : 0;

  // Determine which skills nobody in the party is proficient in
  const uncoveredSkills = ALL_SKILLS.filter(skill =>
    !characters.some(c => c.skills.includes(skill.key))
  );

  if (chars.length === 0) {
    return (
      <div style="padding: 1em; border: 1px solid #f44336; background-color: rgba(244, 67, 54, 0.1); border-radius: 8px;">
        <h3>No Characters Found</h3>
        <p>No character files found with 'character-sheet' tag in {CHARACTER_DIR}</p>
      </div>
    );
  }

  return (
    <div style="font-family: var(--default-font), -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 1200px; margin: 0 auto; padding: 20px;">
      <style>{`
        .psh-stats-bar {
          background: var(--background-secondary);
          padding: 15px;
          border-radius: 8px;
          margin-bottom: 20px;
          display: flex;
          justify-content: space-around;
          text-align: center;
        }
        .psh-stat-item { display: flex; flex-direction: column; }
        .psh-stat-number { font-size: 1.5em; font-weight: bold; color: var(--text-accent); }
        .psh-stat-label { font-size: 0.9em; color: var(--text-muted); }
        .psh-section-header {
          display: flex; align-items: center; gap: 10px;
          margin-bottom: 15px; padding-bottom: 8px;
          border-bottom: 2px solid var(--background-modifier-border);
        }
        .psh-card-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 16px;
          margin-bottom: 30px;
        }
        .psh-char-card {
          background: var(--background-secondary);
          border: 1px solid var(--background-modifier-border);
          border-radius: 8px;
          padding: 16px;
          display: flex;
          flex-direction: column;
          gap: 10px;
          text-decoration: none;
          color: inherit;
          cursor: pointer;
          transition: border-color 0.15s ease, box-shadow 0.15s ease;
        }
        .psh-char-card:hover {
          border-color: var(--text-accent);
          box-shadow: 0 0 0 1px var(--text-accent);
        }
        .psh-char-header {
          display: flex;
          align-items: center;
          gap: 12px;
        }
        .psh-avatar {
          width: 48px;
          height: 48px;
          border-radius: 50%;
          object-fit: cover;
          border: 2px solid var(--background-modifier-border);
          flex-shrink: 0;
        }
        .psh-char-info { flex: 1; min-width: 0; }
        .psh-char-name {
          font-weight: bold;
          font-size: 1.05em;
          color: var(--text-normal);
          white-space: nowrap;
          overflow: hidden;
          text-overflow: ellipsis;
        }
        .psh-char-name a.internal-link {
          color: var(--text-normal);
          text-decoration: none;
        }
        .psh-char-name a.internal-link:hover {
          color: var(--text-accent);
          text-decoration: underline;
        }
        .psh-char-detail {
          font-size: 0.85em;
          color: var(--text-muted);
        }
        .psh-hp-bar-bg {
          width: 100%;
          height: 8px;
          background: var(--background-modifier-border);
          border-radius: 4px;
          overflow: hidden;
        }
        .psh-hp-bar-fill {
          height: 100%;
          border-radius: 4px;
          transition: width 0.3s;
        }
        .psh-combat-row {
          display: flex;
          justify-content: space-between;
          font-size: 0.9em;
        }
        .psh-combat-stat {
          display: flex;
          flex-direction: column;
          align-items: center;
        }
        .psh-combat-val { font-weight: bold; color: var(--text-normal); }
        .psh-combat-lbl { font-size: 0.75em; color: var(--text-muted); }
        .psh-table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 30px;
          font-size: 0.9em;
        }
        .psh-table th {
          padding: 8px 12px;
          text-align: center;
          font-size: 0.85em;
          color: var(--text-muted);
          border-bottom: 2px solid var(--background-modifier-border);
        }
        .psh-table th:first-child { text-align: left; }
        .psh-table td {
          padding: 8px 12px;
          text-align: center;
          border-bottom: 1px solid var(--background-modifier-border);
        }
        .psh-table td:first-child {
          text-align: left;
          font-weight: 500;
          color: var(--text-normal);
        }
        .psh-ability-high,
        .psh-skill-table td.psh-ability-high {
          color: #4caf50 !important;
          font-weight: bold;
          background: rgba(76, 175, 80, 0.15) !important;
        }
        .psh-ability-low,
        .psh-skill-table td.psh-ability-low {
          color: #ef5350 !important;
          font-weight: bold;
          background: rgba(239, 83, 80, 0.15) !important;
        }
        .psh-skill-table {
          width: 100%;
          border-collapse: collapse;
          margin-bottom: 30px;
          font-size: 0.85em;
        }
        .psh-skill-table th {
          padding: 6px 10px;
          text-align: center;
          font-size: 0.8em;
          color: var(--text-muted);
          border-bottom: 2px solid var(--background-modifier-border);
          white-space: nowrap;
        }
        .psh-skill-table th:first-child,
        .psh-skill-table th:nth-child(2) { text-align: left; }
        .psh-skill-table td {
          padding: 6px 10px;
          text-align: center;
          border-bottom: 1px solid var(--background-modifier-border);
        }
        .psh-skill-table td:first-child {
          text-align: left;
          font-weight: 500;
          color: var(--text-normal);
          white-space: nowrap;
        }
        .psh-skill-table td:nth-child(2) {
          text-align: left;
          color: var(--text-muted);
          font-size: 0.85em;
        }
        .psh-prof {
          color: #4caf50;
          font-weight: bold;
        }
        .psh-expert {
          color: var(--text-accent);
          font-weight: bold;
        }
        .psh-no-prof {
          color: var(--text-faint, var(--text-muted));
          opacity: 0.4;
        }
        .psh-uncovered-skills {
          display: flex;
          flex-wrap: wrap;
          gap: 6px;
          margin-bottom: 30px;
        }
        .psh-uncovered-tag {
          background: rgba(244, 67, 54, 0.15);
          color: #f44336;
          padding: 4px 10px;
          border-radius: 4px;
          font-size: 0.85em;
        }
        .psh-party-select {
          background: var(--background-secondary);
          color: var(--text-normal);
          border: 1px solid var(--background-modifier-border);
          border-radius: 4px;
          padding: 4px 8px;
          font-size: 0.9em;
          cursor: pointer;
        }
        .psh-filter-bar {
          display: flex;
          align-items: center;
          gap: 12px;
          margin-bottom: 20px;
        }
        .psh-table-scroll {
          overflow-x: auto;
          margin-bottom: 30px;
        }
        .psh-sense-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 4px;
        }
        .psh-sense-tag {
          font-size: 0.72em;
          padding: 2px 6px;
          border-radius: 3px;
          background: rgba(66, 165, 245, 0.15);
          color: #42a5f5;
          white-space: nowrap;
        }
      `}</style>

      <div className="psh-section-header">
        <dc.Icon icon="users" size={20} />
        <h2 style="margin: 0;">Party Stats Hub</h2>
      </div>

      {/* Party Selector */}
      <div className="psh-filter-bar">
        <label style="font-size: 0.9em; color: var(--text-muted);">Party:</label>
        <select
          className="psh-party-select"
          value={selectedParty}
          onChange={e => {
            const val = e.target.value;
            setSelectedParty(val);
            // Persist to frontmatter so the refresh script uses the same party
            try {
              const f = dc.app.vault.getAbstractFileByPath("Party Stats Hub.md");
              if (f) dc.app.fileManager.processFrontMatter(f, fm => { fm.party_filter = val; });
            } catch(err) {}
          }}
        >
          {allParties.map(p => (
            <option key={p} value={p}>{p}</option>
          ))}
          <option value="All">All Parties</option>
        </select>
        <span style="font-size: 0.85em; color: var(--text-muted);">
          {partySize} character{partySize !== 1 ? 's' : ''}
        </span>
      </div>

      {/* Summary Stats */}
      <div className="psh-stats-bar">
        <div className="psh-stat-item">
          <div className="psh-stat-number">{partySize}</div>
          <div className="psh-stat-label">Party Size</div>
        </div>
        <div className="psh-stat-item">
          <div className="psh-stat-number">{avgLevel}</div>
          <div className="psh-stat-label">Avg Level</div>
        </div>
        <div className="psh-stat-item">
          <div className="psh-stat-number">{totalHp}</div>
          <div className="psh-stat-label">Total HP Pool</div>
        </div>
        <div className="psh-stat-item">
          <div className="psh-stat-number">{avgAc}</div>
          <div className="psh-stat-label">Avg AC</div>
        </div>
      </div>

      {/* Character Cards */}
      <div className="psh-section-header">
        <dc.Icon icon="id-card" size={18} />
        <h3 style="margin: 0;">Character Overview</h3>
      </div>

      <div className="psh-card-grid">
        {characters.map(c => {
          const hpPct = c.maxHp > 0 ? c.currentHp / c.maxHp : 0;
          return (
            <a key={c.name} className="psh-char-card internal-link"
              data-href={c.filePath}
              href={c.filePath ? `obsidian://open?file=${encodeURIComponent(c.filePath)}` : '#'}
              aria-label={c.filePath}
              style={`border-top: 3px solid ${getClassColor(c.class)};`}>
              <div className="psh-char-header">
                {c.avatar ? (
                  <img className="psh-avatar" src={c.avatar} alt={c.name} />
                ) : (
                  <div className="psh-avatar" style="background: var(--background-modifier-border); display: flex; align-items: center; justify-content: center; font-size: 1.2em;">?</div>
                )}
                <div className="psh-char-info">
                  <div className="psh-char-name">{c.name}</div>
                  <div className="psh-char-detail">
                    Lv {c.level} {c.species} {c.class}
                  </div>
                  {c.subclass && (
                    <div className="psh-char-detail" style="font-style: italic;">{c.subclass}</div>
                  )}
                </div>
              </div>

              {/* HP Bar */}
              <div>
                <div style="display: flex; justify-content: space-between; font-size: 0.85em; margin-bottom: 3px;">
                  <span style="color: var(--text-muted);">HP</span>
                  <span style="color: var(--text-normal); font-weight: 500;">
                    {c.currentHp}/{c.maxHp}
                    {c.tempHp > 0 && <span style="color: #42a5f5;"> +{c.tempHp}</span>}
                  </span>
                </div>
                <div className="psh-hp-bar-bg">
                  <div className="psh-hp-bar-fill" style={`width: ${Math.min(hpPct * 100, 100)}%; background-color: ${hpColor(hpPct)};`} />
                </div>
              </div>

              {/* Combat Stats */}
              <div className="psh-combat-row">
                <div className="psh-combat-stat">
                  <div className="psh-combat-val">{c.ac}</div>
                  <div className="psh-combat-lbl">AC</div>
                </div>
                <div className="psh-combat-stat">
                  <div className="psh-combat-val">{c.initiative}</div>
                  <div className="psh-combat-lbl">Init</div>
                </div>
                <div className="psh-combat-stat">
                  <div className="psh-combat-val">{c.speed}</div>
                  <div className="psh-combat-lbl">Speed</div>
                  {(() => {
                    const mv = c.movement;
                    const extra = [];
                    const getSpd = (k) => { const v = mv[k]; return (v && v.value !== undefined) ? v.value : v; };
                    if (Number(getSpd('flying')) > 0) extra.push(`Fly ${getSpd('flying')}`);
                    if (Number(getSpd('swimming')) > 0) extra.push(`Swim ${getSpd('swimming')}`);
                    if (Number(getSpd('climbing')) > 0) extra.push(`Climb ${getSpd('climbing')}`);
                    if (extra.length === 0) return null;
                    return <div style="font-size: 0.65em; color: var(--text-muted); margin-top: 1px;">{extra.join(', ')}</div>;
                  })()}
                </div>
                <div className="psh-combat-stat">
                  <div className="psh-combat-val">+{c.profBonus}</div>
                  <div className="psh-combat-lbl">Prof</div>
                </div>
              </div>

              {/* Mini Ability Scores */}
              <div style="display: flex; justify-content: space-between; gap: 2px;">
                {ABILITIES.map(a => (
                  <div key={a} style="text-align: center; flex: 1;">
                    <div style="font-size: 0.7em; color: var(--text-muted);">{ABILITY_SHORT[a]}</div>
                    <div style={`font-size: 0.9em; font-weight: 500; color: ${c.modifiers[a] != null && c.modifiers[a] === modMax[a] && characters.length > 1 ? 'var(--text-accent)' : 'var(--text-normal)'};`}>
                      {c.scores[a] != null ? c.scores[a] : '?'}
                    </div>
                  </div>
                ))}
              </div>

              {/* Senses & Speed Tags */}
              {(() => {
                const raw = c.senses;
                const senseEntries = Object.entries(raw).filter(([, v]) => {
                  const n = (v && v.value !== undefined) ? v.value : v;
                  return n != null && Number(n) > 0;
                });
                const mv = c.movement;
                const getSpd = (k) => { const v = mv[k]; return (v && v.value !== undefined) ? v.value : v; };
                const walkSpeed = Number(getSpd('walking')) || parseInt(c.speed) || 30;
                const extraSpeeds = [];
                if (Number(getSpd('flying')) > 0) extraSpeeds.push({ name: 'Fly', ft: getSpd('flying') });
                if (Number(getSpd('swimming')) > 0) extraSpeeds.push({ name: 'Swim', ft: getSpd('swimming') });
                if (Number(getSpd('climbing')) > 0) extraSpeeds.push({ name: 'Climb', ft: getSpd('climbing') });
                return (
                  <div className="psh-sense-tags">
                    <span className="psh-sense-tag">Speed {walkSpeed} ft</span>
                    {extraSpeeds.map(s => <span key={s.name} className="psh-sense-tag">{s.name} {s.ft} ft</span>)}
                    {senseEntries.map(([name, v]) => {
                      const ft = (v && v.value !== undefined) ? v.value : v;
                      const label = name.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase());
                      return <span key={name} className="psh-sense-tag">{label} {ft} ft</span>;
                    })}
                  </div>
                );
              })()}
            </a>
          );
        })}
      </div>

      {/* Ability Scores Comparison Table */}
      <div className="psh-section-header">
        <dc.Icon icon="bar-chart-3" size={18} />
        <h3 style="margin: 0;">Ability Score Comparison</h3>
      </div>

      <div className="psh-table-scroll">
        <table className="psh-table">
          <thead>
            <tr>
              <th>Character</th>
              {ABILITIES.map(a => <th key={a}>{ABILITY_SHORT[a]}</th>)}
            </tr>
          </thead>
          <tbody>
            {characters.map(c => (
              <tr key={c.name}>
                <td><CharLink character={c} /></td>
                {ABILITIES.map(a => {
                  const score = c.scores[a];
                  const mod = c.modifiers[a];
                  const isMax = mod != null && mod === modMax[a] && characters.length > 1;
                  const isMin = mod != null && mod === modMin[a] && characters.length > 1 && modMin[a] !== modMax[a];
                  return (
                    <td key={a} className={isMax ? 'psh-ability-high' : isMin ? 'psh-ability-low' : ''}>
                      {score != null ? `${score} (${mod != null ? formatBonus(mod) : '?'})` : '\u2014'}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Saving Throws */}
      <div className="psh-section-header">
        <dc.Icon icon="shield" size={18} />
        <h3 style="margin: 0;">Saving Throws</h3>
      </div>

      <div className="psh-table-scroll">
        <table className="psh-skill-table">
          <thead>
            <tr>
              <th>Save</th>
              {characters.map(c => <th key={c.name}>{c.name.split(' ')[0]}</th>)}
            </tr>
          </thead>
          <tbody>
            {SAVING_THROWS.map(save => {
              const saveKey = save.toLowerCase();
              const bonuses = characters.map(c => {
                const raw = c.saveBonuses[saveKey];
                return (raw && raw.value !== undefined) ? raw.value : (typeof raw === 'number' ? raw : null);
              });
              const validBonuses = bonuses.filter(b => b != null);
              const maxBonus = validBonuses.length ? Math.max(...validBonuses) : null;
              const minBonus = validBonuses.length ? Math.min(...validBonuses) : null;
              return (
                <tr key={save}>
                  <td>{save}</td>
                  {characters.map((c, i) => {
                    const hasSave = c.saves.includes(save);
                    const bonus = bonuses[i];
                    const isHighest = bonus != null && bonus === maxBonus && validBonuses.length > 1;
                    const isLowest = bonus != null && bonus === minBonus && validBonuses.length > 1 && minBonus !== maxBonus;
                    return (
                      <td key={c.name} className={isHighest ? 'psh-ability-high' : isLowest ? 'psh-ability-low' : ''}>
                        {bonus != null ? formatBonus(bonus) : '\u2014'}
                        {hasSave && ' \u2713'}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Skills Proficiency Matrix */}
      <div className="psh-section-header">
        <dc.Icon icon="list-checks" size={18} />
        <h3 style="margin: 0;">Skills</h3>
      </div>

      {uncoveredSkills.length > 0 && (
        <div style="margin-bottom: 15px;">
          <span style="font-size: 0.85em; color: var(--text-muted); margin-right: 8px;">No one proficient in:</span>
          <div className="psh-uncovered-skills" style="display: inline-flex;">
            {uncoveredSkills.map(s => (
              <span key={s.key} className="psh-uncovered-tag">{s.name}</span>
            ))}
          </div>
        </div>
      )}

      <div className="psh-table-scroll">
        <table className="psh-skill-table">
          <thead>
            <tr>
              <th>Skill</th>
              <th>Ability</th>
              {characters.map(c => <th key={c.name}>{c.name.split(' ')[0]}</th>)}
            </tr>
          </thead>
          <tbody>
            {ALL_SKILLS.map(skill => {
              const anyoneHas = characters.some(c => c.skills.includes(skill.key));
              // Find highest and lowest bonus for this skill across the party
              const bonuses = characters.map(c => {
                const raw = c.skillBonuses[skill.bonusKey];
                return (raw && raw.value !== undefined) ? raw.value : (typeof raw === 'number' ? raw : null);
              });
              const validBonuses = bonuses.filter(b => b != null);
              const maxBonus = validBonuses.length ? Math.max(...validBonuses) : null;
              const minBonus = validBonuses.length ? Math.min(...validBonuses) : null;
              return (
                <tr key={skill.key} style={!anyoneHas ? 'background: rgba(244, 67, 54, 0.05);' : ''}>
                  <td>{skill.name}</td>
                  <td>{skill.ability}</td>
                  {characters.map((c, i) => {
                    const hasExpertise = c.expertise.includes(skill.key);
                    const hasProf = c.skills.includes(skill.key);
                    const bonus = bonuses[i];
                    const isHighest = bonus != null && bonus === maxBonus && validBonuses.length > 1;
                    const isLowest = bonus != null && bonus === minBonus && validBonuses.length > 1 && minBonus !== maxBonus;
                    const hasDis = skill.bonusKey === 'stealth' && c.stealthDisadvantage;
                    // Show bonus value with proficiency indicator suffix
                    let display;
                    if (bonus != null) {
                      const suffix = hasExpertise ? ' \u2605' : hasProf ? ' \u2713' : '';
                      display = `${formatBonus(bonus)}${suffix}`;
                    } else {
                      display = '\u2014';
                    }
                    return (
                      <td key={c.name}
                        className={isHighest ? 'psh-ability-high' : isLowest ? 'psh-ability-low' : ''}
                        title={hasDis ? 'Disadvantage (armor)' : ''}>
                        {display}{hasDis ? ' \u25BC' : ''}
                      </td>
                    );
                  })}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div style="display: flex; gap: 16px; font-size: 0.8em; color: var(--text-muted); margin-bottom: 30px; flex-wrap: wrap;">
        <span><span className="psh-ability-high">Highest</span></span>
        <span><span className="psh-ability-low">Lowest</span></span>
        <span>{'\u2605'} Expertise</span>
        <span>{'\u2713'} Proficient</span>
        <span>{'\u25BC'} Disadvantage</span>
      </div>

      {/* Tool Proficiencies */}
      {(() => {
        const allTools = [...new Set(characters.flatMap(c => c.toolProficiencies))].sort();
        if (allTools.length === 0) return null;
        return (
          <>
            <div className="psh-section-header">
              <dc.Icon icon="wrench" size={18} />
              <h3 style="margin: 0;">Tool Proficiencies</h3>
            </div>
            <div className="psh-table-scroll">
              <table className="psh-skill-table">
                <thead>
                  <tr>
                    <th>Tool</th>
                    {characters.map(c => <th key={c.name}>{c.name.split(' ')[0]}</th>)}
                  </tr>
                </thead>
                <tbody>
                  {allTools.map(tool => (
                    <tr key={tool}>
                      <td>{tool}</td>
                      {characters.map(c => {
                        const has = c.toolProficiencies.includes(tool);
                        return (
                          <td key={c.name} className={has ? 'psh-prof' : 'psh-no-prof'}>
                            {has ? '\u2713' : '\u2014'}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </>
        );
      })()}

      {/* Passives */}
      <div className="psh-section-header">
        <dc.Icon icon="eye" size={18} />
        <h3 style="margin: 0;">Passive Scores</h3>
      </div>

      <div className="psh-table-scroll">
        <table className="psh-table">
          <thead>
            <tr>
              <th>Character</th>
              <th>Perception</th>
              <th>Investigation</th>
              <th>Insight</th>
            </tr>
          </thead>
          <tbody>
            {characters.map(c => (
              <tr key={c.name}>
                <td>{c.name}</td>
                <td>{c.passivePerception != null ? c.passivePerception : '\u2014'}</td>
                <td>{c.passiveInvestigation != null ? c.passiveInvestigation : '\u2014'}</td>
                <td>{c.passiveInsight != null ? c.passiveInsight : '\u2014'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div style={{
        marginTop: '20px',
        padding: '15px',
        background: 'var(--background-secondary)',
        borderRadius: '8px',
        fontSize: '0.9em',
        color: 'var(--text-muted)'
      }}>
        <strong>Data Source:</strong> Character sheets in {CHARACTER_DIR} (filtered by 'character-sheet' tag)
        <br />
        <strong>Last Updated:</strong> {new Date().toLocaleString()}
      </div>
    </div>
  );
}

return { PartyStatsHub };
