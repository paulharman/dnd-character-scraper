/**
 * Infusions Manager Component
 *
 * Interactive component for viewing character infusions including active infusions
 * and known infusion recipes for Artificer characters.
 */

const InfusionsQuery = () => {
    const { characterName } = input;

    // Get character files
    const files = dc.pages(
        { from: '"character_data/parser"' },
        { limit: 100 }
    ).filter(file =>
        file.file.name.includes(characterName) &&
        file.file.name.endsWith('.md')
    );

    if (files.length === 0) {
        return <div style={{
            color: 'var(--text-muted)',
            fontStyle: 'italic',
            padding: '1em',
            textAlign: 'center'
        }}>
            No character sheet found for "{characterName}"
        </div>;
    }

    const characterFile = files[0];
    const infusions = characterFile.infusions;

    if (!infusions) {
        return <div style={{
            color: 'var(--text-muted)',
            fontStyle: 'italic',
            padding: '1em',
            textAlign: 'center'
        }}>
            No infusions data available for {characterName}
        </div>;
    }

    const activeInfusions = dc.useArray(infusions.active_infusions || []);
    const knownInfusions = dc.useArray(infusions.known_infusions || []);
    const slotsUsed = infusions.infusion_slots_used || 0;
    const slotsTotal = infusions.infusion_slots_total || 0;
    const artificerLevels = infusions.metadata?.artificer_levels || 0;

    // State for filtering and sorting
    const [activeFilter, setActiveFilter] = React.useState('');
    const [knownFilter, setKnownFilter] = React.useState('');
    const [activeSortBy, setActiveSortBy] = React.useState('name');
    const [knownSortBy, setKnownSortBy] = React.useState('name');

    // Filter functions
    const filteredActiveInfusions = activeInfusions.filter(infusion =>
        infusion.name?.toLowerCase().includes(activeFilter.toLowerCase()) ||
        infusion.infused_item_name?.toLowerCase().includes(activeFilter.toLowerCase()) ||
        infusion.type?.toLowerCase().includes(activeFilter.toLowerCase())
    );

    const filteredKnownInfusions = knownInfusions.filter(infusion =>
        infusion.name?.toLowerCase().includes(knownFilter.toLowerCase())
    );

    // Sort functions
    const sortedActiveInfusions = [...filteredActiveInfusions].sort((a, b) => {
        switch (activeSortBy) {
            case 'name':
                return (a.name || '').localeCompare(b.name || '');
            case 'item':
                return (a.infused_item_name || '').localeCompare(b.infused_item_name || '');
            case 'type':
                return (a.type || '').localeCompare(b.type || '');
            default:
                return 0;
        }
    });

    const sortedKnownInfusions = [...filteredKnownInfusions].sort((a, b) => {
        switch (knownSortBy) {
            case 'name':
                return (a.name || '').localeCompare(b.name || '');
            case 'level':
                return (a.level_requirement || 0) - (b.level_requirement || 0);
            default:
                return 0;
        }
    });

    const containerStyle = {
        fontFamily: 'var(--font-text)',
        fontSize: '14px',
        lineHeight: '1.5',
        color: 'var(--text-normal)'
    };

    const headerStyle = {
        display: 'flex',
        alignItems: 'center',
        gap: '0.5em',
        marginBottom: '1em',
        padding: '0.75em',
        backgroundColor: 'var(--background-secondary-alt)',
        borderRadius: '0.5em',
        border: '1px solid var(--background-modifier-border)'
    };

    const slotsStyle = {
        marginLeft: 'auto',
        fontSize: '0.9em',
        color: slotsUsed >= slotsTotal ? 'var(--text-error)' : 'var(--text-muted)'
    };

    const controlsStyle = {
        display: 'flex',
        gap: '1em',
        marginBottom: '1em',
        flexWrap: 'wrap'
    };

    const inputStyle = {
        padding: '0.5em',
        borderRadius: '0.25em',
        border: '1px solid var(--background-modifier-border)',
        backgroundColor: 'var(--background-secondary)',
        color: 'var(--text-normal)',
        fontSize: '0.9em'
    };

    const selectStyle = {
        ...inputStyle,
        cursor: 'pointer'
    };

    const tableStyle = {
        width: '100%',
        borderCollapse: 'collapse',
        marginBottom: '1.5em'
    };

    const thStyle = {
        padding: '0.75em',
        textAlign: 'left',
        borderBottom: '2px solid var(--background-modifier-border)',
        backgroundColor: 'var(--background-secondary)',
        fontWeight: '600',
        fontSize: '0.9em'
    };

    const tdStyle = {
        padding: '0.75em',
        borderBottom: '1px solid var(--background-modifier-border)',
        verticalAlign: 'top'
    };

    const rarityColors = {
        common: 'var(--text-normal)',
        uncommon: '#1eff00',
        rare: '#0070dd',
        'very rare': '#a335ee',
        legendary: '#ff8000',
        artifact: '#e6cc80'
    };

    const getRarityColor = (rarity) => {
        return rarityColors[rarity?.toLowerCase()] || rarityColors.common;
    };

    return (
        <div style={containerStyle}>
            {/* Header with infusion slots */}
            <div style={headerStyle}>
                <h4 style={{ margin: 0 }}>
                    Artificer Infusions
                    {artificerLevels > 0 && ` (Level ${artificerLevels})`}
                </h4>
                {slotsTotal > 0 && (
                    <span style={slotsStyle}>
                        {slotsUsed}/{slotsTotal} slots used
                        {slotsTotal > slotsUsed && ` (${slotsTotal - slotsUsed} available)`}
                    </span>
                )}
            </div>

            {/* Active Infusions */}
            {activeInfusions.length > 0 && (
                <>
                    <h5 style={{ marginBottom: '0.5em' }}>
                        Active Infusions ({activeInfusions.length})
                    </h5>

                    <div style={controlsStyle}>
                        <input
                            type="text"
                            placeholder="Filter active infusions..."
                            value={activeFilter}
                            onChange={(e) => setActiveFilter(e.target.value)}
                            style={inputStyle}
                        />
                        <select
                            value={activeSortBy}
                            onChange={(e) => setActiveSortBy(e.target.value)}
                            style={selectStyle}
                        >
                            <option value="name">Sort by Name</option>
                            <option value="item">Sort by Infused Item</option>
                            <option value="type">Sort by Type</option>
                        </select>
                    </div>

                    <table style={tableStyle}>
                        <thead>
                            <tr>
                                <th style={thStyle}>Infusion</th>
                                <th style={thStyle}>Infused Item</th>
                                <th style={thStyle}>Type</th>
                                <th style={thStyle}>Rarity</th>
                                <th style={thStyle}>Attunement</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sortedActiveInfusions.map((infusion, index) => (
                                <tr key={index}>
                                    <td style={tdStyle}>
                                        <strong>{infusion.name || 'Unknown'}</strong>
                                        {infusion.description && (
                                            <div style={{
                                                fontSize: '0.85em',
                                                color: 'var(--text-muted)',
                                                marginTop: '0.25em',
                                                maxWidth: '300px'
                                            }}>
                                                {infusion.description.length > 100
                                                    ? infusion.description.substring(0, 100) + '...'
                                                    : infusion.description
                                                }
                                            </div>
                                        )}
                                    </td>
                                    <td style={tdStyle}>
                                        {infusion.infused_item_name || 'Unknown Item'}
                                    </td>
                                    <td style={tdStyle}>
                                        {infusion.type || 'Unknown'}
                                    </td>
                                    <td style={{
                                        ...tdStyle,
                                        color: getRarityColor(infusion.rarity),
                                        fontWeight: '500'
                                    }}>
                                        {infusion.rarity ?
                                            infusion.rarity.charAt(0).toUpperCase() + infusion.rarity.slice(1)
                                            : 'Common'
                                        }
                                    </td>
                                    <td style={tdStyle}>
                                        {infusion.requires_attunement ? 'Yes' : 'No'}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </>
            )}

            {/* Known Infusions */}
            {knownInfusions.length > 0 && (
                <>
                    <h5 style={{ marginBottom: '0.5em' }}>
                        Known Infusions ({knownInfusions.length})
                    </h5>

                    <div style={controlsStyle}>
                        <input
                            type="text"
                            placeholder="Filter known infusions..."
                            value={knownFilter}
                            onChange={(e) => setKnownFilter(e.target.value)}
                            style={inputStyle}
                        />
                        <select
                            value={knownSortBy}
                            onChange={(e) => setKnownSortBy(e.target.value)}
                            style={selectStyle}
                        >
                            <option value="name">Sort by Name</option>
                            <option value="level">Sort by Level Requirement</option>
                        </select>
                    </div>

                    <table style={tableStyle}>
                        <thead>
                            <tr>
                                <th style={thStyle}>Infusion</th>
                                <th style={thStyle}>Level Req.</th>
                                <th style={thStyle}>Description</th>
                            </tr>
                        </thead>
                        <tbody>
                            {sortedKnownInfusions.map((infusion, index) => (
                                <tr key={index}>
                                    <td style={tdStyle}>
                                        <strong>{infusion.name || 'Unknown'}</strong>
                                    </td>
                                    <td style={tdStyle}>
                                        {infusion.level_requirement || 1}
                                    </td>
                                    <td style={tdStyle}>
                                        <div style={{
                                            fontSize: '0.9em',
                                            maxWidth: '400px'
                                        }}>
                                            {infusion.description || 'No description available'}
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </>
            )}

            {/* No infusions message */}
            {activeInfusions.length === 0 && knownInfusions.length === 0 && (
                <div style={{
                    color: 'var(--text-muted)',
                    fontStyle: 'italic',
                    padding: '1em',
                    textAlign: 'center'
                }}>
                    No infusions found for this character.
                </div>
            )}
        </div>
    );
};

return { InfusionsQuery };