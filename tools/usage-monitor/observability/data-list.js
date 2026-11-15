/** Shared record collection: renderer, controls, persisted state and row actions. */
import {collectionPage,normalizeSearch} from '/collection.js';
import {button as uiButton,icon,emptyState,createActionMenu,escapeHTML as esc} from '/ui.js';
const button=(title,attributes='',primary=false,iconName='')=>uiButton(title,'type="button" '+attributes,primary,iconName);
const fmt=value=>value==null?'Unknown':Number(value).toLocaleString('en',{maximumFractionDigits:2});
const compact=value=>value==null?'Unknown':Intl.NumberFormat('en',{notation:'compact',maximumFractionDigits:2}).format(value);
let reportError=message=>{const node=document.querySelector('[data-list-error]');if(node)node.textContent=message;};
export function setListErrorHandler(handler){reportError=handler;}
const tables = Object.create(null), tableDefinitions = new Map(),mounted=new WeakSet(),refreshing=new Set();
try {
  const saved=JSON.parse(localStorage.getItem('ttgl-table-settings-v1')||'{}');
  for(const [id,value] of Object.entries(saved||{})) {
    if(!value||typeof value!=='object') continue;
    tables[id]={search:typeof value.search==='string'?value.search:'',page:1,
      sort:typeof value.sort==='string'?value.sort:null,direction:value.direction===-1?-1:1,
      hiddenColumns:Array.isArray(value.hiddenColumns)?value.hiddenColumns.filter(v=>typeof v==='string'):[],
      pageSize:[10,20,50,100].includes(value.pageSize)?value.pageSize:20,filters:Object.fromEntries(Object.entries(value.filters||{}).filter(([,v])=>typeof v==='string'))};
  }
} catch {}
export function clearListFilters(id){const state=tables[id];if(state){state.search='';state.filters={};state.page=1;saveTableSettings();}}

function saveTableSettings() {
  try {localStorage.setItem('ttgl-table-settings-v1',JSON.stringify(Object.fromEntries(
    Object.entries(tables).map(([id,{search,sort,direction,filters,hiddenColumns,pageSize}])=>[id,{search,sort,direction,filters,hiddenColumns,pageSize}]))));}catch{}
}
function columnValue(column,row) { return column.value?column.value(row):row[column.key]; }
function columnText(column,row) {
  const value=columnValue(column,row);
  if(column.filterText) return column.filterText(row);
  return value==null?'Unknown':typeof value==='number'?`${value} ${fmt(value)} ${compact(value)}`:String(value);
}
function matchesColumn(column,row,query) {
  if(!query.trim()) return true;
  const comparison=column.numeric&&query.trim().match(/^(<=|>=|!=|=|<|>)\s*(-?\d[\d,]*(?:\.\d+)?)$/);
  if(comparison) {
    const value=columnValue(column,row), limit=Number(comparison[2].replaceAll(',',''));
    if(typeof value!=='number'||!Number.isFinite(value)) return false;
    return {'<':value<limit,'>':value>limit,'<=':value<=limit,'>=':value>=limit,'=':value===limit,'!=':value!==limit}[comparison[1]];
  }
  return normalizeSearch(String(columnText(column,row))).includes(normalizeSearch(query));
}
export function renderList(id, columns, rows, actions, searchable=true, options={}) {
  const menus=[];tableDefinitions.set(id,{columns,rows,actions,searchable,menus,options});queueMicrotask(mountTableMenus);
  const state=tables[id] ||= {search:'',page:1,pageSize:20,sort:null,direction:1,filters:{},hiddenColumns:columns.filter(c=>c.hiddenByDefault).map(c=>c.key)};
  const allColumns=columns;
  const selection=columns.find(c=>c.selectionKey);if(selection){const allowed=new Set(rows.map(r=>String(r[selection.selectionKey])));for(const key of selected.get(id)||[])if(!allowed.has(key))selected.get(id).delete(key);}
  state.hiddenColumns=(state.hiddenColumns||[]).filter(key=>allColumns.some(c=>c.key===key));
  columns=allColumns.filter(c=>!state.hiddenColumns.includes(c.key));
  if(!columns.length){columns=allColumns;state.hiddenColumns=[];}
  const picker=`<details class="column-picker"><summary class="ui-button">Columns</summary><div class="column-options" popover="manual"><strong>Displayed columns</strong>${allColumns.map(c=>`<label><input type="checkbox" data-column-toggle="${id}" data-key="${c.key}" aria-label="Show ${esc(id)} column ${esc(c.label)}" ${state.hiddenColumns.includes(c.key)?'':'checked'} ${columns.length===1&&columns[0].key===c.key?'disabled':''}>${esc(c.label)}</label>`).join('')}<small>Keep at least one column visible.</small></div></details>`;
  if(!columns.some(c=>c.key===state.sort)) state.sort=null;
  const filtered=columns.some(c=>state.filters[c.key]?.trim());
  const sortedColumn=columns.find(c=>c.key===state.sort);
  const result=collectionPage(rows, {
    search:state.search, searchText:row=>allColumns.map(c=>columnText(c,row)).join(' '),
    filter:row=>columns.every(c=>matchesColumn(c,row,state.filters[c.key]||'')),
    page:state.page,pageSize:state.pageSize||20,
    compare:sortedColumn?(a,b)=>{
      const left=columnValue(sortedColumn,a),right=columnValue(sortedColumn,b);
      // Unknown values stay last in either direction rather than becoming zero.
      if(left==null||right==null) return left==null?(right==null?0:1):-1;
      return state.direction*(typeof left==='number'&&typeof right==='number'?left-right:
        String(left).localeCompare(String(right),'en',{numeric:true,sensitivity:'base'}));
    }:undefined
  });
  state.page=result.page;
  const toolbar=`<div class="list-toolbar">${searchable?`<div class="list-search ui-search"><input class="ui-input" data-search="${id}" value="${esc(state.search)}" placeholder="Search these rows" aria-label="Search ${esc(id)}"><button type="button" data-clear-search="${id}" aria-label="Clear search">${icon('x')}</button></div>`:''}<div class="table-controls">${picker}${state.search||filtered||state.sort||state.hiddenColumns.length?button('Reset table',`data-reset-table="${id}"`):''}<span class="muted" role="status">${fmt(result.total)} of ${fmt(rows.length)} rows</span>${selection?`<span data-list-selection-count>${selectedIds(id).length} selected</span>`:''}</div></div>`;
  const head=columns.map(column=>`<th scope="col" aria-sort="${state.sort===column.key?(state.direction===1?'ascending':'descending'):'none'}" class="${column.numeric?'numeric':''}"><button type="button" data-sort="${id}" data-key="${column.key}" aria-label="Sort by ${esc(column.label)}">${esc(column.label)}<span aria-hidden="true" class="sort-indicator">${state.sort===column.key?(state.direction===1?'↑':'↓'):'↕'}</span></button></th>`).join('');
  const filters=columns.map(column=>`<td><input type="search" class="ui-input column-filter" data-column-filter="${id}" data-key="${column.key}" value="${esc(state.filters[column.key]||'')}" aria-label="Filter ${esc(id)} by ${esc(column.label)}" placeholder="${column.numeric?'e.g. >= 100':'Filter…'}" ${column.numeric?'title="Filter by value, or use =, !=, <, <=, >, >= with a number"':''}></td>`).join('');
  const body=result.items.map((row,index)=>{
    const cells=columns.map(column=>`<td class="${column.numeric?'numeric':''}">${column.cell?column.cell(row):esc(columnValue(column,row))}</td>`).join('');
    let menu='';
    if(actions) {const key=id+'-'+index; menus.push({key,label:'Actions for '+(row.title||row.name||row.id||'row'),actions:actions(row).map(action=>({...action,onSelect:()=>{try{Promise.resolve(action.onSelect()).catch(error=>reportError(error.message));}catch(error){reportError(error.message);}}}))}); menu=`<td class="row-menu"><span data-row-menu="${key}"></span></td>`;}
    return `<tr${options.rowClass?` class="${esc(options.rowClass)}"`: ''}>${cells}${menu}</tr>`;
  }).join('');
  const hasFilters=state.search||filtered;
  const emptyAction=hasFilters?button('Clear search and filters',`data-reset-table="${id}"`):id==='projects'?button('Add project','data-add-project',true):id==='tasks'?button('Add task','data-add-task',true):'';
  const empty=emptyState(hasFilters?'No matching rows':'Nothing here yet',hasFilters?'Try different terms or clear the column filters.':'Rows will appear when evidence is available for this scope.',emptyAction);
  return `<div data-table="${esc(id)}">`+toolbar+`<div class="table-container ui-table-scroll" data-slot="table-container"><table class="ui-table" data-slot="table"><thead><tr>${head}${actions?'<th scope="col"><span class="sr-only">Actions</span></th>':''}</tr><tr class="column-filters">${filters}${actions?'<td></td>':''}</tr></thead><tbody>${body||`<tr><td colspan="${columns.length+(actions?1:0)}" class="table-empty">${empty}</td></tr>`}</tbody></table></div>`+
    `<div class="pagination list-pagination"><span>${result.total?(result.page-1)*result.pageSize+1:0}–${Math.min(result.page*result.pageSize,result.total)} of ${result.total}</span><label>Rows per page<select class="ui-input" data-list-size="${esc(id)}" aria-label="Rows per page ${esc(id)}">${[10,20,50,100].map(size=>`<option value="${size}" ${size===result.pageSize?'selected':''}>${size}</option>`).join('')}</select></label>${button('Previous',`data-page="${id}" data-delta="-1" ${result.page===1?'disabled':''}`)}<label class="list-page-jump">Page<input class="ui-input" type="number" min="1" max="${result.pages}" value="${result.page}" data-list-jump="${esc(id)}" aria-label="Page ${esc(id)}"></label><span>of ${result.pages}</span>${button('Next',`data-page="${id}" data-delta="1" ${result.page===result.pages?'disabled':''}`)}</div><p data-list-error role="status"></p></div>`;
}
export function mountTableMenus() {
  for(const [id,definition] of tableDefinitions){const root=document.querySelector(`[data-table="${CSS.escape(id)}"]`);if(root&&!mounted.has(root)){mounted.add(root);definition.options?.onMount?.(root);}}
  for(const menu of [...tableDefinitions.values()].flatMap(d=>d.menus)) {
    const target=document.querySelector(`[data-row-menu="${menu.key}"]`);
    if(target&&!target.children.length) target.append(createActionMenu(document,menu.label,menu.actions));
  }
}
function refreshTable(id) {
  const target=document.querySelector(`[data-table="${CSS.escape(id)}"]`), definition=tableDefinitions.get(id);
  if(!target||!definition||refreshing.has(id)) return;
  refreshing.add(id);try{
  const pickerOpen=target.querySelector('.column-picker')?.open;
  const active=document.activeElement, scroll=target.querySelector('.table-container')?.scrollLeft||0;
  const selector=active?.matches('[data-column-toggle]')?`[data-column-toggle][data-key="${CSS.escape(active.dataset.key)}"]`:active?.matches('[data-column-filter]')?`[data-column-filter][data-key="${CSS.escape(active.dataset.key)}"]`:
    active?.matches('[data-list-size]')?'[data-list-size]':active?.matches('[data-list-jump]')?'[data-list-jump]':active?.matches('[data-search]')?'[data-search]':active?.matches('[data-sort]')?`[data-sort][data-key="${CSS.escape(active.dataset.key)}"]`:null;
  const position=active?.selectionStart;
  target.outerHTML=renderList(id,definition.columns,definition.rows,definition.actions,definition.searchable,definition.options);
  mountTableMenus();
  const replacement=document.querySelector(`[data-table="${CSS.escape(id)}"]`);
  if(pickerOpen){const picker=replacement.querySelector('.column-picker');picker.open=true;positionColumns(picker);}
  const field=selector&&replacement.querySelector(selector);
  if(field) {field.focus({preventScroll:true});if(position!=null) field.setSelectionRange(position,position);}
  replacement.querySelector('.table-container').scrollLeft=scroll;
  saveTableSettings();
  }finally{refreshing.delete(id);}
}

document.addEventListener('click',event=>{
 const target=event.target.closest('button');if(!target)return;
 if(target.dataset.page&&tables[target.dataset.page]){tables[target.dataset.page].page+=Number(target.dataset.delta);refreshTable(target.dataset.page);}
 if(target.dataset.sort&&tables[target.dataset.sort]){const state=tables[target.dataset.sort];if(state.sort!==target.dataset.key){state.sort=target.dataset.key;state.direction=1;}else if(state.direction===1)state.direction=-1;else{state.sort=null;state.direction=1;}state.page=1;refreshTable(target.dataset.sort);}
 if(target.dataset.clearSearch&&tables[target.dataset.clearSearch]){tables[target.dataset.clearSearch].search='';tables[target.dataset.clearSearch].page=1;refreshTable(target.dataset.clearSearch);}
 if(target.dataset.resetTable&&tables[target.dataset.resetTable]){tables[target.dataset.resetTable]={search:'',page:1,pageSize:20,sort:null,direction:1,filters:{},hiddenColumns:[]};refreshTable(target.dataset.resetTable);}
});
document.addEventListener('change',event=>{
  const id=event.target.dataset.columnToggle||event.target.dataset.listSize||event.target.dataset.listJump;if(!id||!tables[id])return;
  if(event.target.dataset.listSize){tables[id].pageSize=Number(event.target.value);tables[id].page=1;refreshTable(id);return;}
  if(event.target.dataset.listJump){tables[id].page=Number(event.target.value);refreshTable(id);return;}
  const state=tables[id], key=event.target.dataset.key;
  if(event.target.checked) state.hiddenColumns=state.hiddenColumns.filter(c=>c!==key);
  else {state.hiddenColumns.push(key);delete state.filters[key];if(state.sort===key)state.sort=null;}
  state.page=1;refreshTable(id);
});
document.addEventListener('click',event=>{
  if(!event.target.closest('.column-picker')) document.querySelectorAll('.column-picker[open]').forEach(p=>p.open=false);
});
document.addEventListener('keydown',event=>{
  if(event.key==='Enter'&&event.target.matches('[data-search],[data-column-filter],[data-list-jump]')){event.preventDefault();if(event.target.dataset.listJump){const id=event.target.dataset.listJump;tables[id].page=Number(event.target.value);refreshTable(id);}return;}
  const picker=event.target.closest('.column-picker');
  if(event.key==='Escape'&&picker?.open){event.preventDefault();event.stopPropagation();picker.open=false;picker.querySelector('summary').focus();}
});
document.addEventListener('input',event=>{
  const id=event.target.dataset.columnFilter||event.target.dataset.search;if(!id) return;
  const state=tables[id];
  if(event.target.dataset.columnFilter) state.filters[event.target.dataset.key]=event.target.value;
  else state.search=event.target.value;
  state.page=1;refreshTable(id);
});

/** Source buttons are ordinary searchable/paged records, including in dialogs. */
export function sourceList(id,ids,attribute='data-source',prefix='Source'){
 return renderList(id,[{key:'position',label:'#',numeric:true},{key:'id',label:'Source ID'},{key:'open',label:'Evidence',value:r=>prefix+' '+r.position,cell:r=>button(prefix+' '+r.position,`${attribute}="${esc(r.id)}"`)}],ids.map((ident,i)=>({id:ident,position:i+1})),null);
}
const selected=new Map();
export function selectedIds(id){return [...(selected.get(id)||[])];}
export function selectionColumn(id,{key='id',name='choice',label='Select',limit=200}={}){
 const choices=selected.get(id)||new Set();selected.set(id,choices);
 return {key:'__selection',selectionKey:key,label,value:r=>choices.has(String(r[key])),cell:r=>`<input type="checkbox" name="${esc(name)}" value="${esc(r[key])}" aria-label="${esc(r.title||r.name||r[key])}" data-list-select="${esc(id)}" data-choice="${esc(r[key])}" data-choice-limit="${limit}" ${choices.has(String(r[key]))?'checked':''}>`};
}
export function clearSelection(id){selected.delete(id);}
document.addEventListener('change',event=>{
 const input=event.target;if(!input.dataset.listSelect)return;const id=input.dataset.listSelect,choices=selected.get(id)||new Set();selected.set(id,choices);
 if(input.checked&&choices.size>=Number(input.dataset.choiceLimit)){input.checked=false;reportError('Select at most '+input.dataset.choiceLimit+' records.');return;}
 if(input.checked)choices.add(input.dataset.choice);else choices.delete(input.dataset.choice);
 const count=input.closest('[data-table]').querySelector('[data-list-selection-count]');if(count)count.textContent=choices.size+' selected';
 input.dispatchEvent(new CustomEvent('list-selection',{bubbles:true,detail:{id,selected:[...choices]}}));
});

function positionColumns(picker){
 const panel=picker.querySelector('.column-options');if(!panel?.isConnected)return;
 if(!picker.open){if(panel.matches(':popover-open'))panel.hidePopover();return;}
 if(!panel.matches(':popover-open'))panel.showPopover();
 const rect=picker.querySelector('summary').getBoundingClientRect();
 panel.style.left=Math.max(8,Math.min(innerWidth-panel.offsetWidth-8,rect.right-panel.offsetWidth))+'px';
 panel.style.top=Math.max(8,Math.min(innerHeight-panel.offsetHeight-8,rect.bottom+6))+'px';
}
document.addEventListener('toggle',event=>{if(event.target.matches('.column-picker'))positionColumns(event.target);},true);
window.addEventListener('resize',()=>document.querySelectorAll('.column-picker[open]').forEach(positionColumns));
