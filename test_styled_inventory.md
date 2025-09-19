## Inventory

<span class="right-link">[[#Character Statistics|Top]]</span>
> 
<div style="margin-bottom: 1.5em; padding: 1em; background-color: var(--background-secondary-alt, #23272e); border-radius: 0.5em; border: 1px solid var(--background-modifier-border, #444);">
  <h4 style="margin: 0 0 0.5em 0; display: flex; align-items: center; gap: 0.5em;">
    Personal Wealth
  </h4>
  <div style="display: flex; gap: 1em; flex-wrap: wrap;">
    <span style="font-weight: 500;">150 gp</span> <span style="font-weight: 500;">75 sp</span> <span style="font-weight: 500;">25 cp</span> <span style="font-weight: 500;">2 pp</span>
    <span style="margin-left: auto; font-style: italic; opacity: 0.8;">
      Total: 177 gp
    </span>
  </div>
</div>
> **Encumbrance:** 0.0/225 lbs (0% - Light)
>
>
>### Personal Inventory
>
> ```datacorejsx
> const { InventoryQuery } = await dc.require("z_Templates/InventoryManager.jsx");
> return <InventoryQuery characterName="Test Character" />;
> ```
>
>### Party Inventory (Campaign 6616097)
>
> ```datacorejsx
> const { PartyInventoryQuery } = await dc.require("z_Templates/PartyInventoryManager.jsx");
> return <PartyInventoryQuery characterName="Test Character" campaignId="6616097" />;
> ```
> > ^inventory