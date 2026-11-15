/** Native collection behavior for the stdlib-served workspace; no runtime package. */
export const normalizeSearch = value => String(value ?? '').normalize('NFKD').replace(/\p{M}/gu,'').toLocaleLowerCase().trim();
export function serverCollectionPage(items, {total,offset=0,limit=20}) {
  if(!Number.isInteger(total)||total<0||!Number.isInteger(offset)||offset<0||!Number.isInteger(limit)||limit<1||limit>100)throw Error('Invalid server page');
  return {items,total,offset,pageSize:limit,page:Math.floor(offset/limit)+1,pages:Math.max(1,Math.ceil(total/limit))};
}
export function collectionPage(rows, options) {
  const terms=normalizeSearch(options.search).split(/\s+/).filter(Boolean);
  let items=rows.filter(row=>{if(options.filter&&!options.filter(row))return false;if(!terms.length)return true;const text=normalizeSearch(options.searchText(row));return terms.every(term=>text.includes(term));});
  if(options.compare)items.sort(options.compare);
  const pageSize=Math.max(1,Math.min(500,Math.floor(options.pageSize)||20));
  const total=items.length,pages=Math.max(1,Math.ceil(total/pageSize)),page=Math.max(1,Math.min(pages,Math.floor(options.page)||1));
  return {items:items.slice((page-1)*pageSize,page*pageSize),total,pages,page,pageSize};
}
export function nativeActionMenu(document,label,actions) {
  const wrapper=document.createElement('span'),trigger=document.createElement('button'),menu=document.createElement('div');
  menu.id='menu-'+crypto.randomUUID();menu.popover='auto';menu.setAttribute('role','menu');menu.setAttribute('aria-label',label);
  trigger.type='button';trigger.setAttribute('aria-label',label);trigger.setAttribute('aria-haspopup','menu');trigger.setAttribute('aria-expanded','false');
  trigger.popoverTargetElement=menu;
  for(const action of actions){const item=document.createElement('button');item.type='button';item.textContent=action.label;item.disabled=Boolean(action.disabled);item.setAttribute('role','menuitem');item.dataset.variant=action.destructive?'destructive':'default';item.tabIndex=-1;item.onclick=()=>{menu.hidePopover();trigger.focus();action.onSelect();};menu.append(item);}
  menu.addEventListener('toggle',e=>{trigger.setAttribute('aria-expanded',String(e.newState==='open'));if(e.newState!=='open')return;const r=trigger.getBoundingClientRect();menu.style.maxHeight='min(320px, 70vh)';menu.style.overflowY='auto';menu.style.left=Math.max(8,Math.min(innerWidth-menu.offsetWidth-8,r.right-menu.offsetWidth))+'px';menu.style.top=Math.max(8,Math.min(innerHeight-menu.offsetHeight-8,r.bottom+4))+'px';menu.querySelector('button:not(:disabled)')?.focus();});
  trigger.onkeydown=e=>{if(e.key==='ArrowDown'){e.preventDefault();menu.showPopover();}};
  menu.onkeydown=e=>{const items=[...menu.querySelectorAll('button:not(:disabled)')];let n=items.indexOf(document.activeElement);if(e.key==='Escape'||e.key==='Tab'){menu.hidePopover();if(e.key==='Escape'){e.preventDefault();trigger.focus();}return;}if(!items.length)return;if(e.key==='ArrowDown')n=(n+1)%items.length;else if(e.key==='ArrowUp')n=(n+items.length-1)%items.length;else if(e.key==='Home')n=0;else if(e.key==='End')n=items.length-1;else return;e.preventDefault();items[n].focus();};
  wrapper.append(trigger,menu);return wrapper;
}
