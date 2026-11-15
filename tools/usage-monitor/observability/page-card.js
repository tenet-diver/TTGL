/** Collapsible analysis surfaces shared by the screenshot-backed pages. */
import {escapeHTML as esc} from '/ui.js';
export function card(title,body,action=''){
 return `<details class="section ops-card analysis-card" open><summary class="section-heading"><h2>${esc(title)}</h2>${action?`<span class="card-actions">${action}</span>`:''}</summary><div class="analysis-card-body">${body}</div></details>`;
}

export function rangeControl(value){
 const ranges=[['1d','1d'],['7d','7d'],['30d','30d'],['90d','90d'],['all','All']];
 return `<div class="scope-range"><label>Range<select class="ui-input range-native" name="range" aria-label="Range">${ranges.map(([id,title])=>`<option value="${id}" ${value===id?'selected':''}>${title}</option>`).join('')}</select></label><div class="range-segments" role="group" aria-label="Date range">${ranges.map(([id,title])=>`<button type="button" data-range="${id}" aria-pressed="${value===id}">${title}</button>`).join('')}</div></div>`;
}
document.addEventListener('click',event=>{
 const button=event.target.closest('[data-range]');if(!button)return;
 const form=button.closest('[data-ops-filters]');if(!form)return;
 form.elements.range.value=button.dataset.range;form.requestSubmit();
});
