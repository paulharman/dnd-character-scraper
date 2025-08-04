function SpellQuerySettings({ children }) {
	return <>
		<div style="display: flex; gap: 1em; flex-wrap: wrap; margin-top: 1em;">
			{children}
		</div>
	</>
}

function SpellQuerySetting({ title, icon, children, onToggle, onClear }) {
	return <>
		<div style="border: 1px solid var(--background-modifier-border); border-radius: 8px; padding: 0.5em 0.5em; min-width: 150px; background-color: var(--background-secondary);">
			<div style="font-weight: 600; font-size: 0.9em; margin-bottom: 0.5em; display: flex; justify-content: center; gap: 0.5em; width: 100%;">
				<dc.Icon icon={icon} />
				<span>{title}</span>
				{(onToggle || onClear) && <>|</>}
				{onToggle && <span onclick={onToggle}><dc.Icon icon={"toggle-left"} /></span>}
				{onClear && <span onclick={onClear}><dc.Icon icon={"list-restart"} /></span>}
			</div>
			<div style="display: flex; flex-direction: column; flex-wrap: wrap; justify-content: space-between; gap: 5px 5px; max-height: 250px;">
				{children}
			</div>
		</div>
	</>
}

const allClasses = [ "Priest", "Wizard" ];
const allRarities = [ "Common", "Uncommon", "Rare", "Very Rare", "Unique" ];
const allComponents = [ "V", "S", "M" ];
const componentNames = {
	"V": "Verbal",
	"S": "Somatic",
	"M": "Material",
};

function SpellQuery({ type = allClasses, rarity = allRarities, level, restricted = true, paging = 20, useFilters = true, expandFilters = false }) {
	const query = dc.useQuery("@page and !path(\"00 Assets\") and #data/spell");

	const allSpheres = dc.useArray(dc.useQuery("@page and !path(\"00 Assets\") and #data/sphere-of-magic"), (a) => a.sort(p => [p.$name], "asc"));
	const allSchools = dc.useArray(dc.useQuery("@page and !path(\"00 Assets\") and #data/school-of-magic"), (a) => a.sort(p => [p.$name], "asc"));

	const [filterClass, setFilterClass] = dc.useState(type);
	const [filterLevel, setFilterLevel] = dc.useState(level);
	const [filterSearch, setFilterSearch] = dc.useState('');
	const [filterSchools, setFilterSchools] = dc.useState(allSchools);
	const [filterSpheres, setFilterSpheres] = dc.useState(allSpheres);
	const [filterComponents, setFilterComponents] = dc.useState(allComponents);
	const [filterRarity, setFilterRarity] = dc.useState(rarity);
	const [filterRestricted, setFilterRestricted] = dc.useState(restricted);

	const allPages = dc.useArray(query, (array) => array.sort(page => [page.$name], 'asc'));
	const filteredPages = dc.useMemo(() => (
		allPages.filter(page => {
			const filterSearchLowered = filterSearch.toLowerCase();

			if (filterSearchLowered != '' && !page.$name.toLowerCase().includes(filterSearchLowered)) return false;
			if (filterClass && !filterClass.includes(page.$frontmatter?.class?.value)) return false;
			if (Array.isArray(filterSchools) && Array.isArray(page.$frontmatter?.schools?.value) && !filterSchools.some(s1 => page.$frontmatter.schools.value.some(s2 => s1.$path == s2.path))) return false;
			if (Array.isArray(filterSpheres) && Array.isArray(page.$frontmatter?.spheres?.value) && !filterSpheres.some(s1 => page.$frontmatter.spheres.value.some(s2 => s1.$path == s2.path))) return false;
			if (Array.isArray(filterComponents) && Array.isArray(page.$frontmatter?.components?.value) && !page.$frontmatter.components.value.every(r => filterComponents.includes(r) )) return false;
			if (Array.isArray(filterRarity) && Array.isArray(page.$frontmatter?.rarity?.value) && !page.$frontmatter.rarity.value.some(r => filterRarity.includes(r) )) return false;
			if (!filterRestricted && page.$frontmatter?.restricted?.value) return false;
			if (Number.isInteger(filterLevel) && parseInt(page.$frontmatter?.level?.value) != filterLevel) return false;

			return true;
		})
	), [allPages, filterSearch, filterClass, filterLevel, filterSchools, filterSpheres, filterComponents, filterRarity, filterRestricted]);

	// A list of columns to show in the table.
	let columns = [
		{ id: "Class", value: p => p.value("class") },
		{ id: "Level", value: p => p.value("level") },
		{ id: "Name", value: p => p.$link },
		{ id: "School", value: p => p.value("schools"), render: v => v ? v : '' },
		{ id: "Spheres", value: p => p.value("spheres"), render: v => v ? v : '' },
		{ id: "Components", value: p => p.value("components"), render: v => v ? v : '' },
		{ id: "Rarity", value: p => p.value("rarity"), render: v => v ? v : '' },
		{ id: "Restricted to", value: p => p.value("restricted"), render: v => v ? v : '' },
	];

	// If we weren't given a class, we'll remove the class column.
	const givenAClass = type.toString() != allClasses.toString();
	if (givenAClass) {
		columns = columns.filter(c => c.id != "Class");
	}
	// If we don't have priest spells, remove the spheres column.
	const includeSpheres = type.includes("Priest");
	if (!includeSpheres) {
		columns = columns.filter(c => c.id != "Spheres");
	}

	const [filtersShown, setFiltersShown] = dc.useState(expandFilters);

	const [randomResults, setRandomResults] = dc.useState([]);

	function clearFilterClass() { setFilterClass(type); }
	function clearFilterLevel() { setFilterLevel(level); }
	function clearFilterSearch() { setFilterSearch(''); }
	function clearFilterSchools() { setFilterSchools(allSchools); }
	function toggleFilterSchools() { setFilterSchools(allSchools.filter(f => !filterSchools.includes(f))); }
	function clearFilterSpheres() { setFilterSpheres(allSpheres); }
	function toggleFilterSpheres() { setFilterSpheres(allSpheres.filter(f => !filterSpheres.includes(f))); }
	function clearFilterComponents() { setFilterComponents(allComponents); }
	function toggleFilterComponents() { setFilterComponents(allComponents.filter(f => !filterComponents.includes(f))); }
	function clearFilterRarity() { setFilterRarity(rarity); }
	function toggleFilterRarity() { setFilterRarity(allRarities.filter(f => !filterRarity.includes(f))); }
	function clearFilterRestricted() { setFilterRestricted(restricted); }
	function toggleFilterRestricted() { setFilterRestricted(!filterRestricted); }
	function clearAllFilters() {
		clearFilterClass();
		clearFilterLevel();
		clearFilterSearch();
		clearFilterSchools();
		clearFilterSpheres();
		clearFilterComponents();
		clearFilterRarity();
		clearFilterRestricted();
	};

	return <>
		{useFilters && <>
			<div style="display: flex; gap: 0.75em;">
				<input type="search" placeholder="Search..." value={filterSearch} onchange={(e) => setFilterSearch(e.target.value)} style="flex-grow: 1;" />
				<button class="primary" onclick={() => setFiltersShown(!filtersShown)}>⚙</button>
				<button onclick={clearAllFilters}>Clear All</button>
			</div>
			{filtersShown && <div>
				<SpellQuerySettings>
					<SpellQuerySetting title="Basic Info" icon="lucide-cog">
						{!givenAClass && <>
							Class:
							{allClasses.map((c) => <label><input type="checkbox" onchange={(e) => setFilterClass(e.target.checked ? filterClass.filter(f => f != c).concat([c]) : filterClass.filter(f => f != c))} checked={filterClass.includes(c)} />{c}</label>)}
						</>}
						<label>Level: <input type="search" onchange={(e) => setFilterLevel(parseInt(e.target.value))} value={Number.isInteger(filterLevel) ? filterLevel : ''} style="max-width: 75px;"></input></label>
					</SpellQuerySetting>
					<SpellQuerySetting title={<dc.Link link={dc.fileLink("Schools of Magic").withDisplay("School")} />} icon="lucide-folder" onToggle={toggleFilterSchools} onClear={clearFilterSchools}>
						{allSchools.map((s) => <label><input type="checkbox" onchange={(e) => setFilterSchools(e.target.checked ? filterSchools.filter(f => f != s).concat([s]) : filterSchools.filter(f => f != s))} checked={filterSchools.includes(s)} />{s.$name}</label>)}
					</SpellQuerySetting>
					{includeSpheres && <SpellQuerySetting title="Sphere" icon="lucide-circle-dot" onToggle={toggleFilterSpheres} onClear={clearFilterSpheres}>
						{allSpheres.map((s) => <label><input type="checkbox" onchange={(e) => setFilterSpheres(e.target.checked ? filterSpheres.filter(f => f != s).concat([s]) : filterSpheres.filter(f => f != s))} checked={filterSpheres.includes(s)} />{s.$name}</label>)}
					</SpellQuerySetting>}
					<SpellQuerySetting title="Components" icon="lucide-puzzle" onToggle={toggleFilterComponents} onClear={clearFilterComponents}>
						{allComponents.map((r) => <label><input type="checkbox" onchange={(e) => setFilterComponents(e.target.checked ? filterComponents.filter(f => f != r).concat([r]) : filterComponents.filter(f => f != r))} checked={filterComponents.includes(r)} />{componentNames[r]}</label>)}
					</SpellQuerySetting>
					<SpellQuerySetting title={<dc.Link link={dc.fileLink("Spell Frequency").withDisplay("Rarity")} />} icon="lucide-star" onToggle={() => {toggleFilterRarity(); toggleFilterRestricted();}} onClear={() => {clearFilterRarity(); clearFilterRestricted()}}>
						{allRarities.map((r) => <label><input type="checkbox" onchange={(e) => setFilterRarity(e.target.checked ? filterRarity.filter(f => f != r).concat([r]) : filterRarity.filter(f => f != r))} checked={filterRarity.includes(r)} />{r}</label>)}
						<label><input type="checkbox" onchange={(e) => setFilterRestricted(e.target.checked)} checked={filterRestricted}></input>Restricted</label>
					</SpellQuerySetting>
				</SpellQuerySettings>
			</div>}
		</>}
		<dc.Table columns={columns} rows={filteredPages} paging={paging} />
		<div>
			<h2>Random Results</h2>
			<div style="display: flex; gap: 0.5em;">
				<button class="primary" onclick={() => setRandomResults([filteredPages[Math.floor(Math.random() * filteredPages.length)]].concat(randomResults))}><dc.Icon icon="lucide-plus" /> Add</button>
				<button class="primary" onclick={() => navigator.clipboard.writeText(randomResults.reduce((a, p) => `${a}\n${p.$link.toString()}`, ''))}><dc.Icon icon="lucide-copy" /> Copy</button>
				<button class="primary" onclick={() => setRandomResults([])}><dc.Icon icon="lucide-trash-2" /> Clear</button>
			</div>
			{randomResults.length > 0 && <dc.VanillaTable columns={columns} rows={randomResults} />}
		</div>
	</>;
}

return { SpellQuery }
