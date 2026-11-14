import {renderSuggestions,activityQuery} from '/activity-insights.js';
import {renderExplorer,explorerParams} from '/work-explorer.js';
import { renderStepTimeline } from '/step-timeline.js';
import { renderHistory, openTaskHistory as showTaskHistory } from '/task-history.js';
import { collectionPage, normalizeSearch } from '/design-system/collection.js';
import { button, badge, icon, emptyState, skeleton, createActionMenu } from '/ui.js';

const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const fmt = value => value == null ? 'Unknown' : Number(value).toLocaleString('en', {maximumFractionDigits: 2});
const compact = value => value == null ? 'Unknown' : Intl.NumberFormat('en', {notation:'compact',maximumFractionDigits:2}).format(value);
const date = value => value ? new Date(value).toLocaleString() : 'Unknown';
const seconds = value => value == null ? 'Unknown' : fmt(value) + 's';
const external = (url, title='Inspect in Langfuse') => `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(title)} ↗</a>`;
const section = (title, body, action='', note='') => `<section class="section"><div class="section-heading"><h2>${esc(title)}</h2>${action}</div>${note?`<p class="section-note">${note}</p>`:''}${body}</section>`;
const clip = value => `<span class="clip" title="${esc(value)}">${esc(value)}</span>`;
const config = {
  suggestions:['Suggestions','Small-model activity analysis, proposed task boundaries, and evidence-backed improvements.'],
  analytics:['Analytics','Compare time, tokens, steps, and cost by task and subtask type.'],
  knowledge:['Knowledge','Reusable lessons and examples, with links to the work that supports them.'],
  settings:['Settings','Collection, task assignment, and cost scenarios.'],
  overview:['Overview','Selected task usage, collection coverage, and Codex findings.'],
  analysis:['Codex analysis','Agent-authored recommendations with evidence and validation plans.'],
  projects:['Projects','Repository scope for defined work.'],
  history:['Experience history','Search completed work and explore task → subtasks → source steps.'],
  tasks:['Tasks','Goals, verification evidence, and usage across assigned turns.'],
  inbox:['Unassigned inbox','Collected turns that have not been assigned to a task.'],
  activity:['Activity','Compact native-event timeline and model HTTP exchanges.'],
  rules:['Categories & rules','Codex interpretations and explicit fallback text-matching rules.'],
  opportunities:['Opportunities','Evidence-backed proposals; decisions do not apply changes.'],
  experiments:['Experiments','Agent-authored proposals with immutable task baselines. No trials run automatically.'],
  setup:['Setup & coverage','Source permission, collector coverage, and configuration.']
};
const query = new URLSearchParams(location.search);
const aliases={overview:'tasks',history:'knowledge',activity:'tasks',setup:'settings'};
let view=aliases[location.hash.slice(1)]|| (config[location.hash.slice(1)]?location.hash.slice(1):'tasks');
const primary=()=>['tasks','analytics','knowledge'].includes(view);
let workData=null,loadEpoch=0;
let project = query.get('project') || '', task = query.get('task') || '', category = query.get('category') || '';
let data = null, busy = false, tableMenus = [], toastTimer;
const tables = Object.create(null), tableDefinitions = new Map();
try {
  const saved=JSON.parse(localStorage.getItem('ttgl-table-settings-v1')||'{}');
  for(const [id,value] of Object.entries(saved||{})) {
    if(!value||typeof value!=='object') continue;
    tables[id]={search:typeof value.search==='string'?value.search:'',page:1,
      sort:typeof value.sort==='string'?value.sort:null,direction:value.direction===-1?-1:1,
      hiddenColumns:Array.isArray(value.hiddenColumns)?value.hiddenColumns.filter(v=>typeof v==='string'):[],
      filters:Object.fromEntries(Object.entries(value.filters||{}).filter(([,v])=>typeof v==='string'))};
  }
} catch {}
if(query.get('review')&&tables['work-tasks']){tables['work-tasks'].search='';tables['work-tasks'].filters={};tables['work-tasks'].page=1;}

function saveTableSettings() {
  try {localStorage.setItem('ttgl-table-settings-v1',JSON.stringify(Object.fromEntries(
    Object.entries(tables).map(([id,{search,sort,direction,filters,hiddenColumns}])=>[id,{search,sort,direction,filters,hiddenColumns}]))));}catch{}
}

function toast(message) {
  $('#toast').textContent = message;
  $('#toast').style.display = 'block';
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => $('#toast').style.display = 'none', 4500);
}
function syncURL() {
  const params = new URLSearchParams();
  if (project) params.set('project', project);
  if (task) params.set('task', task);
  if (category) params.set('category', category);
  const review=new URLSearchParams(location.search).get('review');if(review)params.set('review',review);
  history.replaceState(null, '', location.pathname + (params.size?'?'+params:'') + '#' + view);
}
async function load() {
  if (busy) return;
  try {
    const epoch=++loadEpoch;
    if(view==='suggestions'){
      const response=await fetch('/api/activity-insights?'+activityQuery(project));
      const result=await response.json();if(!response.ok)throw Error(result.error||'Suggestions unavailable');if(epoch!==loadEpoch)return;
      $('.scope-toolbar').hidden=true;$('#scope-summary').hidden=true;$('#title').textContent='Suggestions';$('#subtitle').textContent=config.suggestions[1];$('#breadcrumb').textContent='Suggestions';$('#page-actions').innerHTML='';$('#content').setAttribute('aria-busy','false');
      document.querySelectorAll('nav [data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===view);if(b.dataset.view===view)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
      renderSuggestions($('#content'),result,{project,post,onRefresh:load,onError:toast,onProject:value=>{project=value;syncURL();load();},onTask:id=>{task=id;view='tasks';syncURL();load();}});return;
    }
    if(primary()){
      const response=await fetch('/api/work-explorer?'+explorerParams(project));
      if(!response.ok)throw Error('Work explorer request failed');
      const result=await response.json();if(epoch!==loadEpoch)return;workData=result;renderWork();return;
    }
    const params = new URLSearchParams();
    if(project) params.set('project',project);
    if(task) params.set('task',task);
    if(category) params.set('category',category);
    const response = await fetch('/api/workspace?' + params);
    if(!response.ok) throw Error('Workspace request failed');
    data = await response.json();
    render();
  } catch(error) {
    $('#live').textContent='Disconnected'; $('#connection-dot').dataset.state='error';
    $('#content').setAttribute('aria-busy','false');
    if(!data) $('#content').innerHTML=emptyState('Evidence is unavailable','Check the connection and try loading again.',button('Try again','data-refresh'),'database');
    toast(error.message);
  }
}
async function post(action, values) {
  const response = await fetch('/api/'+action, {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(values)});
  const result = await response.json();
  if(!response.ok) throw Error(result.error || 'Could not save');
  return result;
}
function options(rows, key, label, selected) {
  return rows.map(row => `<option value="${esc(row[key])}" ${row[key]===selected?'selected':''}>${esc(row[label])}</option>`).join('');
}
function titleForTask(id) { return data.tasks.find(t=>t.id===id)?.title || 'Unassigned'; }
function openView(next) {view=next;syncURL();load();window.scrollTo(0,0);}
async function openTask(id) {
  task=id; project=data.tasks.find(t=>t.id===id)?.project_id || ''; category=''; view='activity'; syncURL(); await load();
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
function table(id, columns, rows, actions, searchable=true) {
  tableDefinitions.set(id,{columns,rows,actions,searchable});
  const state=tables[id] ||= {search:'',page:1,sort:null,direction:1,filters:{},hiddenColumns:columns.filter(c=>c.hiddenByDefault).map(c=>c.key)};
  const allColumns=columns;
  state.hiddenColumns=(state.hiddenColumns||[]).filter(key=>allColumns.some(c=>c.key===key));
  columns=allColumns.filter(c=>!state.hiddenColumns.includes(c.key));
  if(!columns.length){columns=allColumns;state.hiddenColumns=[];}
  const picker=`<details class="column-picker"><summary class="ui-button">Columns</summary><div class="column-options"><strong>Displayed columns</strong>${allColumns.map(c=>`<label><input type="checkbox" data-column-toggle="${id}" data-key="${c.key}" aria-label="Show ${esc(id)} column ${esc(c.label)}" ${state.hiddenColumns.includes(c.key)?'':'checked'} ${columns.length===1&&columns[0].key===c.key?'disabled':''}>${esc(c.label)}</label>`).join('')}<small>Keep at least one column visible.</small></div></details>`;
  if(!columns.some(c=>c.key===state.sort)) state.sort=null;
  const filtered=columns.some(c=>state.filters[c.key]?.trim());
  const sortedColumn=columns.find(c=>c.key===state.sort);
  const result=collectionPage(rows, {
    search:state.search, searchText:row=>columns.map(c=>columnText(c,row)).join(' '),
    filter:row=>columns.every(c=>matchesColumn(c,row,state.filters[c.key]||'')),
    page:state.page,pageSize:id==='overview-categories'?10:20,
    compare:sortedColumn?(a,b)=>{
      const left=columnValue(sortedColumn,a),right=columnValue(sortedColumn,b);
      // Unknown values stay last in either direction rather than becoming zero.
      if(left==null||right==null) return left==null?(right==null?0:1):-1;
      return state.direction*(typeof left==='number'&&typeof right==='number'?left-right:
        String(left).localeCompare(String(right),'en',{numeric:true,sensitivity:'base'}));
    }:undefined
  });
  state.page=result.page;
  const toolbar=`<div class="list-toolbar">${searchable?`<div class="list-search ui-search"><input class="ui-input" data-search="${id}" value="${esc(state.search)}" placeholder="Search these rows" aria-label="Search ${esc(id)}"><button data-clear-search="${id}" aria-label="Clear search">${icon('x')}</button></div>`:''}<div class="table-controls">${picker}${state.search||filtered||state.sort||state.hiddenColumns.length?button('Reset table',`data-reset-table="${id}"`):''}<span class="muted" role="status">${fmt(result.total)} of ${fmt(rows.length)} rows</span></div></div>`;
  const head=columns.map(column=>`<th scope="col" aria-sort="${state.sort===column.key?(state.direction===1?'ascending':'descending'):'none'}" class="${column.numeric?'numeric':''}"><button data-sort="${id}" data-key="${column.key}" aria-label="Sort by ${esc(column.label)}">${esc(column.label)}<span aria-hidden="true" class="sort-indicator">${state.sort===column.key?(state.direction===1?'↑':'↓'):'↕'}</span></button></th>`).join('');
  const filters=columns.map(column=>`<td><input type="search" class="ui-input column-filter" data-column-filter="${id}" data-key="${column.key}" value="${esc(state.filters[column.key]||'')}" aria-label="Filter ${esc(id)} by ${esc(column.label)}" placeholder="${column.numeric?'e.g. >= 100':'Filter…'}" ${column.numeric?'title="Filter by value, or use =, !=, <, <=, >, >= with a number"':''}></td>`).join('');
  const body=result.items.map((row,index)=>{
    const cells=columns.map(column=>`<td class="${column.numeric?'numeric':''}">${column.cell?column.cell(row):esc(row[column.key])}</td>`).join('');
    let menu='';
    if(actions) {const key=id+'-'+index; tableMenus.push({key,label:'Actions for '+(row.title||row.name||row.id||'row'),actions:actions(row).map(action=>({...action,onSelect:()=>{try{Promise.resolve(action.onSelect()).catch(error=>toast(error.message));}catch(error){toast(error.message);}}}))}); menu=`<td class="row-menu"><span data-row-menu="${key}"></span></td>`;}
    return `<tr>${cells}${menu}</tr>`;
  }).join('');
  const hasFilters=state.search||filtered;
  const emptyAction=hasFilters?button('Clear search and filters',`data-reset-table="${id}"`):id==='projects'?button('Add project','data-add-project',true):id==='tasks'?button('Add task','data-add-task',true):'';
  const empty=emptyState(hasFilters?'No matching rows':'Nothing here yet',hasFilters?'Try different terms or clear the column filters.':'Rows will appear when evidence is available for this scope.',emptyAction);
  return `<div data-table="${esc(id)}">`+toolbar+`<div class="table-container ui-table-scroll" data-slot="table-container"><table class="ui-table" data-slot="table"><thead><tr>${head}${actions?'<th scope="col"><span class="sr-only">Actions</span></th>':''}</tr><tr class="column-filters">${filters}${actions?'<td></td>':''}</tr></thead><tbody>${body||`<tr><td colspan="${columns.length+(actions?1:0)}" class="table-empty">${empty}</td></tr>`}</tbody></table></div>`+
    (result.pages>1?`<div class="pagination"><span>${(result.page-1)*result.pageSize+1}–${Math.min(result.page*result.pageSize,result.total)} of ${result.total}</span>${button('Previous',`data-page="${id}" data-delta="-1" ${result.page===1?'disabled':''}`)}<span>${result.page} / ${result.pages}</span>${button('Next',`data-page="${id}" data-delta="1" ${result.page===result.pages?'disabled':''}`)}</div>`:'')+'</div>';
}
function mountTableMenus() {
  for(const menu of tableMenus) {
    const target=document.querySelector(`[data-row-menu="${menu.key}"]`);
    if(target&&!target.children.length) target.append(createActionMenu(document,menu.label,menu.actions));
  }
}
function refreshTable(id) {
  const target=document.querySelector(`[data-table="${CSS.escape(id)}"]`), definition=tableDefinitions.get(id);
  if(!target||!definition) return;
  const pickerOpen=target.querySelector('.column-picker')?.open;
  const active=document.activeElement, scroll=target.querySelector('.table-container')?.scrollLeft||0;
  const selector=active?.matches('[data-column-toggle]')?`[data-column-toggle][data-key="${CSS.escape(active.dataset.key)}"]`:active?.matches('[data-column-filter]')?`[data-column-filter][data-key="${CSS.escape(active.dataset.key)}"]`:
    active?.matches('[data-search]')?'[data-search]':active?.matches('[data-sort]')?`[data-sort][data-key="${CSS.escape(active.dataset.key)}"]`:null;
  const position=active?.selectionStart;
  tableMenus=[];
  target.outerHTML=table(id,definition.columns,definition.rows,definition.actions,definition.searchable);
  mountTableMenus();
  const replacement=document.querySelector(`[data-table="${CSS.escape(id)}"]`);
  if(pickerOpen) replacement.querySelector('.column-picker').open=true;
  const field=selector&&replacement.querySelector(selector);
  if(field) {field.focus({preventScroll:true});if(position!=null) field.setSelectionRange(position,position);}
  replacement.querySelector('.table-container').scrollLeft=scroll;
  saveTableSettings();
}

function experimentResults(experiment) {
  const accounting=experiment.accounting?.at(-1)?.payload;
  const cost=accounting?`<section class="section"><h3>Accrued research overhead</h3><p>${fmt(accounting.current_research_tokens)} native tokens through ${esc(accounting.as_of)}; ${fmt(accounting.illustrative_repetitions_to_recover_current_tokens)} similar ${esc(accounting.unit||'diagnostic cases')} to recover that token count at the observed mean saving. This is not cash break-even. First use has no net saving.</p><details><summary>Accounting scope and limitations</summary><p>${esc(accounting.limitations)}</p></details></section>`:'';
  return cost+(experiment.evaluations||[]).map((evaluation,index)=>{
    const m=evaluation.measurements;
    const resultsTable=table('evaluation-'+encodeURIComponent(experiment.id)+'-'+index,[
      {key:'case',label:'Case'},{key:'condition',label:'Presentation'},
      {key:'total_tokens',label:'Total tokens',numeric:true,cell:r=>fmt(r.total_tokens)},
      {key:'wall_seconds',label:'Wall time',numeric:true,cell:r=>seconds(r.wall_seconds)},
      {key:'quality',label:'Quality'}
    ],m.cells.map(c=>({...c,total_tokens:c.usage.total_tokens,quality:c.quality.passed?'Pass':'Fail'})),null);
    return `<section class="section"><h3>${esc(evaluation.protocol.id)}</h3><p>${esc(m.scope)}</p><p>Native total tokens: <strong>${fmt(m.raw_total_tokens)} → ${fmt(m.compact_total_tokens)}</strong>. Registered gate: <strong>${m.acceptance_passed?'Passed':'Failed'}</strong>. Token reduction: ${fmt(m.token_reduction_fraction*100)}%. Trial inference is included per arm; analyst, implementation and evaluation overhead is separate.</p>${resultsTable}${evaluation.reviews.map(review=>`<h4>Analyst verdict: ${esc(review.verdict)}</h4><p>${esc(review.notes)}</p>`).join('')}<details><summary>Protocol and evidence references</summary><pre>${esc(JSON.stringify(evaluation,null,2))}</pre></details></section>`;
  }).join('') || '<p>Proposal only; no measured trial results.</p>';
}
function showModal(title, body) {
  $('#modal-content').innerHTML=`<div class="modal-heading"><h2 id="modal-title">${esc(title)}</h2>${button('Close','data-close')}</div><div class="modal-body">${body}</div>`;
  if(!$('#modal').open) $('#modal').showModal();
}
function field(label, name, value='', {textarea=false,required=false,hint=''}={}) {
  const control=textarea?`<textarea class="ui-input" aria-label="${esc(label)}" name="${name}" ${required?'required':''}>${esc(value)}</textarea>`:`<input class="ui-input" aria-label="${esc(label)}" name="${name}" value="${esc(value)}" ${required?'required':''}>`;
  return `<label>${esc(label)}${control}${hint?`<small>${esc(hint)}</small>`:''}</label>`;
}
function form(action, body, submit='Save') {return `<form data-form="${action}">${body}<div class="modal-actions">${button('Cancel','type="button" data-close')}${button(submit,'type="submit"',true)}</div></form>`;}
function newProject() {showModal('Add project',form('project',field('Project name','name','',{required:true})+field('Repository / working folder','repo','',{required:true})+field('Analysis scope','scope','',{textarea:true}),'Add project'));}
async function newTask(turn=null) {
  if(primary())data=await(await fetch('/api/workspace')).json();
  if(!data.projects.length) return newProject();
  showModal('Add task',form('task',`<label>Project<select class="ui-input" aria-label="Project" name="project_id">${options(data.projects,'id','name',turn?data.projects.find(p=>p.repo===turn.repo)?.id||project:project)}</select></label>${turn?`<input type="hidden" name="session_id" value="${esc(turn.session_id)}"><input type="hidden" name="turn_id" value="${esc(turn.turn_id)}">`:''}`+field('Task name (optional)','title','',{hint:'Defaults to your request. Luna can format it from the task history.'})+field('Intended outcome','goal',turn?.prompt||'',{textarea:true,required:true})+field('Acceptance / verification criteria','acceptance','',{textarea:true}),'Start task'));
}
function assignTurn(turn) {
  if(!data.tasks.length) return toast('Create a task before assigning a turn.');
  showModal('Assign collected turn',`<p>${esc((turn.prompt||'Prompt unavailable').slice(0,300))}</p>`+form('assign',`<input type="hidden" name="session_id" value="${esc(turn.session_id)}"><input type="hidden" name="turn_id" value="${esc(turn.turn_id)}"><label>Task<select class="ui-input" aria-label="Task" name="task_id" required>${options(data.tasks,'id','title',task)}</select></label>`,'Assign turn'));
}
function openTaskHistory(id,modal) {return showTaskHistory(id,modal,load);}
function taskDetails(row) {
  showModal(row.title,`<dl class="detail-grid"><dt>Status</dt><dd>${badge(row.status)}</dd><dt>Goal</dt><dd>${esc(row.goal)}</dd><dt>Acceptance</dt><dd>${esc(row.acceptance||'Not specified')}</dd><dt>Outcome evidence</dt><dd>${esc(row.outcome||'Not verified')}</dd><dt>Measured tokens</dt><dd>${fmt(row.usage?.total_tokens)}</dd></dl><div class="modal-actions">${button('Analyze / inspect subtasks',`data-history-task="${esc(row.id)}"`)}${button('Open task evidence',`data-open-task="${esc(row.id)}"`)}</div>`);
}
function completeTask(row) {showModal('Record verified completion',form('task_status',`<input type="hidden" name="id" value="${esc(row.id)}"><input type="hidden" name="status" value="completed">`+field('Outcome / verification evidence','outcome',row.outcome||'',{textarea:true,required:true})));}
function ruleDialog(rule={}) {
  showModal(rule.id?'Edit fallback category rule':'Add fallback category rule',form('rule',
    (rule.id?`<input type="hidden" name="id" value="${esc(rule.id)}">`:'')+
    field('Category name','category',rule.category||'',{required:true})+
    field('Operation label contains — plain text','pattern',rule.pattern||'',{required:true,hint:'Case-insensitive literal text. No regex, wildcards, or LLM call. This checks the operation label, not the full command.'})+
    `<div class="rule-preview"><strong>Example:</strong> <code>tests</code> matches <code>shell / tests (pytest)</code>. <code>pytest|jest</code> is literal text, not an OR expression. Use separate rules for alternatives.<p class="muted">Codex-reviewed labels take precedence; these rules classify only unreviewed events.</p>${button('Preview matches','type="button" data-preview-rule')}<div id="rule-preview-result" aria-live="polite"></div></div>`+
    `<label>Enabled<select class="ui-input" aria-label="Enabled" name="enabled"><option value="true" ${rule.enabled!==0?'selected':''}>Yes</option><option value="false" ${rule.enabled===0?'selected':''}>No</option></select></label>`));
}
async function previewRule() {
  const input=$('#modal [name="pattern"]');const pattern=input.value;
  const result=await(await fetch('/api/rule-preview?'+new URLSearchParams({pattern}))).json();
  if(!$('#rule-preview-result')||input.value!==pattern) return;
  $('#rule-preview-result').innerHTML=`<p>${result.total} operation-label matches; ${result.unreviewed} unreviewed events eligible for fallback categorization.</p><ul>${result.matches.map(m=>`<li>${esc(m.operation)} · ${esc(m.basis)}</li>`).join('')}</ul>${!result.total?'<p>No labels match this literal text.</p>':''}<small>Preview covers the latest ${result.window} source events.</small>`;
}
function eventDetails(row) {
  showModal(row.name,`<dl class="detail-grid"><dt>When</dt><dd>${date(row.ts)}</dd><dt>Task</dt><dd>${esc(titleForTask(row.task_id))}</dd><dt>Category</dt><dd>${esc(row.category)}</dd><dt>Assigned by</dt><dd>${esc(row.category_basis)}</dd><dt>Runtime role</dt><dd>${esc(row.runtime_role)}</dd><dt>Recorded runtime</dt><dd>${seconds(row.runtime)}</dd><dt>Output size</dt><dd>${fmt(row.bytes)} retained bytes</dd><dt>Operation outcome</dt><dd>${row.failed===1?'Nonzero / failed operation; not proof of task failure':row.failed===0?'Completed operation':'Unknown'}</dd>${row.usage?`<dt>Measured usage</dt><dd>${fmt(row.usage.input_tokens)} input (${fmt(row.usage.cached_input_tokens)} cached) + ${fmt(row.usage.output_tokens)} output = ${fmt(row.usage.total_tokens)} total</dd>`:''}</dl>${row.category_rationale?`<h3>Codex rationale · ${esc(row.category_confidence)} confidence</h3><p>${esc(row.category_rationale)}</p>`:''}<h3>Source evidence</h3><p>${external(row.langfuse_url)}</p><small>${esc(row.id)}</small>`);
}
function findingDetails(finding, report) {
  showModal(finding.title,`<p>${badge('Codex · '+finding.confidence+' confidence')}</p><h3>What the evidence shows</h3><p>${esc(finding.observation)}</p><h3>Recommended action</h3><p>${esc(finding.recommended_action)}</p><h3>How to verify an improvement</h3><p>${esc(finding.verification_plan)}</p><h3>Supporting records</h3><ul>${finding.evidence_ids.map(id=>{const event=data.events.find(e=>e.id===id),capture=data.wire_captures.find(c=>c.id===id);return `<li>${event?external(event.langfuse_url,event.name):capture?external(capture.langfuse_url,'HTTP exchange'):esc(id)}</li>`;}).join('')}</ul><small>Frozen snapshot ${date(report.snapshot_at)}. Findings are proposals; no measured savings.</small>`);
}
async function reconcile() {
  showModal('Compare token totals','<p>Checking the same all-source native-generation scope in Langfuse…</p>');
  const result=await(await fetch('/api/reconciliation')).json();
  if(!$('#modal').open) return;
  showModal('Compare token totals',`<dl class="detail-grid"><dt>Selected workspace</dt><dd>${fmt(data.usage.total_tokens)} tokens</dd><dt>All native sources</dt><dd>${fmt(result.local_all_sources??data.usage_scope.all_sources.total_tokens)} tokens</dd><dt>Langfuse, same scope</dt><dd>${fmt(result.langfuse_native_tokens)} tokens</dd><dt>Difference</dt><dd>${fmt(result.difference)} tokens</dd><dt>Check</dt><dd>${esc(result.status)}</dd><dt>Unassigned activity</dt><dd>${fmt(data.usage_scope.unassigned.total_tokens)} tokens</dd></dl><h3>Why totals can differ</h3><p>A selected task excludes other tasks and unassigned turns. A category filter can also exclude model-response events entirely. Langfuse date/environment filters must match before comparing totals.</p><p>${esc(result.definition||result.reason)}</p><p class="muted">${esc(result.note||'')}</p><small>Checked ${date(result.checked_at)}. No daily/session/transport counters are added together.</small>`);
}
function statLine() {
  const u=data.usage;
  return `<div class="stats"><div class="stat"><small>Selected scope · tokens</small><strong>${compact(u.total_tokens)}</strong><span>${fmt(u.total_tokens)} measured total</span></div><div class="stat"><small>Fresh / cached input</small><strong>${compact(u.input_tokens-u.cached_input_tokens)} / ${compact(u.cached_input_tokens)}</strong><span>Output: ${compact(u.output_tokens)} · cache is a subset</span></div><div class="stat"><small>All-source tokens</small><strong>${compact(data.usage_scope.all_sources.total_tokens)}</strong><span>Includes other tasks and unassigned turns</span></div><div class="stat"><small>Unassigned tokens</small><strong>${compact(data.usage_scope.unassigned.total_tokens)}</strong><span>${data.inbox.length} turns awaiting task assignment</span></div></div>`;
}
function categoryTable(id='categories') {
  return table(id,[{key:'name',label:'Category'},{key:'count',label:'Events',numeric:true,cell:r=>fmt(r.count)},
    {key:'finite_runtime_seconds',label:'Finite runtime',numeric:true,cell:r=>seconds(r.finite_runtime_seconds)},
    {key:'background_runtime_seconds',label:'Service lifetime',numeric:true,cell:r=>seconds(r.background_runtime_seconds)},
    {key:'unreviewed_runtime_seconds',label:'Unreviewed runtime',numeric:true,cell:r=>seconds(r.unreviewed_runtime_seconds)},
    {key:'bytes',label:'Output bytes',numeric:true,cell:r=>compact(r.bytes)}],data.categories,r=>[
      {id:'open',label:'Show matching events',onSelect:async()=>{category=r.name;view='activity';syncURL();await load();}}
    ]);
}
function capturesTable() {
  const coverage=data.capture_coverage;
  let notice=`${coverage.matched_selection} exchanges match this task/project; ${coverage.total_model_exchanges} across all sources. Tool-category filters do not hide model HTTP exchanges.`;
  if(data.wire_captures.some(c=>!c.response_body_available)) notice+=' Historical parser failures retained requests and timings but lost response bodies. Those rows are explicitly marked; bodies cannot be recovered from the capture files.';
  return section('Captured model HTTP exchanges',table('captures',[
    {key:'started_at',label:'When',filterText:r=>date(r.started_at)+' '+(r.started_at||''),cell:r=>date(r.started_at)},
    {key:'task_id',label:'Task',value:r=>titleForTask(r.task_id),cell:r=>clip(titleForTask(r.task_id))},
    {key:'status',label:'HTTP',value:r=>r.status??r.state,cell:r=>badge(r.status??r.state)},
    {key:'response_body_state',label:'Response body',cell:r=>`<span class="${r.response_body_available?'':'danger'}">${esc(r.response_body_state)}</span>`},
    {key:'correlation',label:'Matched by'},
    {key:'compression',label:'Live compression',value:r=>r.compression?.policy||'off',cell:r=>r.compression?.changes?.length?external(r.compression_url,r.compression.policy+' · '+fmt(r.request_bytes)+' → '+fmt(r.forwarded_request_bytes)+' B'):esc(r.compression?.policy||'off')},
    {key:'request_bytes',label:'Request / response bytes',numeric:true,filterText:r=>`${r.request_bytes??'Unknown'} / ${r.response_bytes??'Unknown'} ${compact(r.request_bytes)} / ${compact(r.response_bytes)}`,cell:r=>compact(r.request_bytes)+' / '+compact(r.response_bytes)},
    {key:'elapsed_seconds',label:'HTTP duration',numeric:true,cell:r=>seconds(r.elapsed_seconds)},
    {key:'first_body_byte_seconds',label:'First body byte',numeric:true,cell:r=>seconds(r.first_body_byte_seconds)}
  ],data.wire_captures,r=>[{id:'open',label:'Inspect retained request / response',onSelect:()=>window.open(r.langfuse_url,'_blank','noopener')}]),'',esc(notice)+(data.wire_captures.length?'':' This selection may be transcript-only; clear task/project filters to see other captured exchanges.'));
}
function tasksTable(rows) {
  return table('tasks',[{key:'title',label:'Task',cell:r=>`<button class="inline-link" data-history-task="${esc(r.id)}">${esc(r.title)}</button>`},
    {key:'project_id',label:'Project',value:r=>data.projects.find(p=>p.id===r.project_id)?.name||'Unknown',cell:r=>esc(data.projects.find(p=>p.id===r.project_id)?.name||'Unknown')},
    {key:'status',label:'Status',cell:r=>badge(r.status)},
    {key:'total_tokens',label:'Measured tokens',numeric:true,cell:r=>compact(r.usage?.total_tokens)},
    {key:'updated',label:'Updated',filterText:r=>date(r.updated)+' '+(r.updated||''),cell:r=>date(r.updated)}],rows.map(r=>({...r,total_tokens:r.usage?.total_tokens??null})),r=>[
      {id:'open',label:'Open task evidence',onSelect:()=>openTask(r.id)},
      {id:'history',label:'Analyze / inspect subtasks',onSelect:()=>openTaskHistory(r.id,showModal)},
      {id:'details',label:'Goal and verification',onSelect:()=>taskDetails(r)},
      {id:'status',label:'Mark active',onSelect:async()=>{await post('task_status',{id:r.id,status:'active'});await load();}},
      {id:'complete',label:'Complete with evidence',onSelect:()=>completeTask(r)}
    ]);
}
function reviewOpportunity(row) {
  const select=(label,name,values,current)=>`<label>${label}<select class="ui-input" aria-label="${esc(label)}" name="${name}">${values.map(v=>`<option ${v===current?'selected':''}>${v}</option>`).join('')}</select></label>`;
  showModal('Review opportunity',`<p>${esc(row.observation)}</p><p>${esc(row.action)}</p><p class="muted">${esc(row.guardrail)}</p>`+form('decision',`<input name="id" type="hidden" value="${esc(row.id)}">`+
    select('Decision','decision',['review','declined','deferred'],row.state.decision)+
    select('Implementation','implementation',['not_started','prepared','applied','reverted'],row.state.implementation)+
    select('Evaluation','evaluation',['not_measured','trial_planned','in_progress','improved','regressed','inconclusive'],row.state.evaluation)+
    field('Evidence, comparison plan and result notes','notes',row.state.notes||'',{textarea:true})));
}
function findingsTable() {
  const report=data.agent_analyses[0];
  if(!report) return '<div class="notice">No Codex assessment matches this selection. Clear filters or run an on-demand review for the task.</div>';
  return table('findings',[{key:'title',label:'Finding',cell:r=>`<button class="inline-link" data-finding="${r.index}">${esc(r.title)}</button>`},
    {key:'confidence',label:'Confidence',cell:r=>badge(r.confidence)},
    {key:'recommended_action',label:'Recommended action',cell:r=>clip(r.recommended_action)},
    {key:'count',label:'Evidence records',numeric:true}],report.findings.map((f,index)=>({...f,index,count:f.evidence_ids.length})),r=>[
      {id:'open',label:'Evidence and validation plan',onSelect:()=>findingDetails(r,report)}
    ]);
}
function renderWork(){
  if(!workData)return;
  tableMenus=[];$('.scope-toolbar').hidden=true;$('#scope-summary').hidden=true;
  $('#title').textContent=view==='tasks'?'Work explorer':config[view][0];$('#subtitle').textContent=view==='tasks'?'Understand the work. Follow a task into its subtasks and source steps.':config[view][1];
  $('#breadcrumb').textContent=view==='tasks'?'Work':config[view][0];
  $('#live').textContent=workData.collection_enabled?'Collecting':'Paused';$('#connection-dot').dataset.state=workData.collection_enabled?'collecting':'paused';
  $('#langfuse').href=workData.langfuse_url;
  $('#page-actions').innerHTML=view==='tasks'?button('Add task','data-add-task',true,'plus'):'';
  document.querySelectorAll('nav [data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===view);if(b.dataset.view===view)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  $('#content').setAttribute('aria-busy','false');
  renderExplorer($('#content'),{view,data:workData,taskId:task,project,table,mountTableMenus,post,onError:toast,onRefresh:load,
    onProject:value=>{project=value;task='';syncURL();load();},
    onTask:id=>{task=id;view='tasks';syncURL();load();},
    onInspect:(title,body,id)=>id?openTaskHistory(id,showModal):showModal(title,body),
    onReviewScope:()=>{const state=tables['work-tasks'];if(state){state.search='';state.filters={};state.page=1;saveTableSettings();}}});
}
function render() {
  if(primary())return renderWork();
  $('.scope-toolbar').hidden=false;$('#scope-summary').hidden=false;
  if(!data) return;
  tableMenus=[];
  $('#title').textContent=config[view][0]; $('#subtitle').textContent=config[view][1];
  $('#live').textContent=data.sources.collection_enabled?'Collecting':'Paused';
  $('#live').title='Last updated '+date(data.at);
  $('#connection-dot').dataset.state=data.sources.collection_enabled?'collecting':'paused';
  $('#breadcrumb').textContent=config[view][0];
  $('#inbox-count').textContent=data.inbox.length||'';
  $('#langfuse').href=data.langfuse_url;
  document.querySelectorAll('nav [data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===view);if(b.dataset.view===view)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  $('#project').innerHTML='<option value="">All projects</option>'+options(data.projects,'id','name',project);
  $('#task').innerHTML='<option value="">All tasks</option>'+options(data.tasks.filter(t=>!project||t.project_id===project),'id','title',task);
  const categories=[...new Set(['model inference','other tools',...data.categories.map(c=>c.name),...data.rules.map(r=>r.category)])].sort();
  $('#category').innerHTML='<option value="">All categories</option>'+categories.map(name=>`<option ${category===name?'selected':''}>${esc(name)}</option>`).join('');
  const scope=task?titleForTask(task):project?data.projects.find(p=>p.id===project)?.name:'All collected sources';
  $('#scope-summary').innerHTML=`<span>Scope: <strong>${esc(scope)}</strong>${category?' · '+esc(category):''}</span><span>Selected: <strong>${fmt(data.usage.total_tokens)}</strong> tokens</span><span>All sources: <strong>${fmt(data.usage_scope.all_sources.total_tokens)}</strong></span><button class="inline-link" data-reconcile>Why totals differ / reconcile</button>`;
  $('#page-actions').innerHTML=view==='projects'?button('Add project','data-add-project',true,'plus'):view==='tasks'?button('Add task','data-add-task',true,'plus'):'';
  let html='';
  if(view==='overview') {
    const accounting=data.runtime_accounting;
    html=statLine()+section('Codex recommendations',findingsTable(),button('Open full analysis','data-view="analysis"'),data.agent_analyses[0]?esc(data.agent_analyses[0].summary):'No analysis for the current scope.')+
      section('Activity categories',categoryTable('overview-categories'),'',`${accounting.reviewed_tool_events} / ${accounting.tool_events} tool events reviewed. ${seconds(accounting.finite_runtime_seconds)} finite operations; ${seconds(accounting.background_runtime_seconds)} background service lifetime. These overlapping sums are not task elapsed time.`);
  }
  if(view==='analysis') {
    const report=data.agent_analyses[0];
    html=section('Latest Codex review',findingsTable(),'',report?`${esc(report.model)} · snapshot ${date(report.snapshot_at)} · ${report.tool_events} reviewed tool events`:'');
    if(report) html+=section('Scope and analyst overhead',`<dl class="detail-grid"><dt>Source scope</dt><dd>${esc(report.scope)}</dd><dt>Analyst token overhead</dt><dd>${fmt(report.overhead.total_tokens)} total; ${fmt(report.overhead.cached_input_tokens)} cached input</dd><dt>Snapshot</dt><dd>${esc(report.snapshot_hash)}</dd></dl><details><summary>Limits of this review</summary><ul>${report.limitations.map(x=>`<li>${esc(x)}</li>`).join('')}</ul></details><p class="muted">Subsequent reviews inspect unreviewed events by default. No scheduled model calls or savings claims.</p>`);
  }
  if(view==='projects') html=section('Projects',table('projects',[{key:'name',label:'Project'},{key:'repo',label:'Repository',cell:r=>clip(r.repo)},{key:'scope',label:'Scope',cell:r=>clip(r.scope)},{key:'created',label:'Created',filterText:r=>date(r.created)+' '+(r.created||''),cell:r=>date(r.created)}],data.projects,r=>[{id:'open',label:'Open project',onSelect:async()=>{project=r.id;task='';category='';view='overview';syncURL();await load();}}]));
  if(view==='history') html='<div id="history-root"></div>';
  if(view==='tasks') html=section('Defined tasks',tasksTable(data.tasks.filter(t=>!project||t.project_id===project)),button('Open unassigned inbox','data-view="inbox"'),'Tasks are explicit goals. Their measured usage comes from assigned turns, not automatically inferred boundaries.');
  if(view==='inbox') html=section('Unassigned turns',table('inbox',[{key:'prompt',label:'Prompt / activity',cell:r=>clip((r.prompt||'Prompt unavailable').replace(/\s+/g,' '))},{key:'repo',label:'Working folder',cell:r=>clip(r.repo)},{key:'start',label:'Started',filterText:r=>date(r.start)+' '+(r.start||''),cell:r=>date(r.start)},{key:'tokens',label:'Measured tokens',numeric:true,cell:r=>compact(r.usage?.total_tokens)},{key:'completed',label:'Agent turn',value:r=>r.completed?'Completed':'Open',cell:r=>badge(r.completed?'Completed':'Open')}],data.inbox.map(r=>({...r,id:r.session_id+':'+r.turn_id,tokens:r.usage?.total_tokens??null})),r=>[{id:'create',label:'Create task from prompt',onSelect:()=>newTask(r)},{id:'assign',label:'Assign to a task',onSelect:()=>assignTurn(r)},{id:'open',label:'Open transcript',onSelect:()=>window.open(r.langfuse_url,'_blank','noopener')}]),'', 'Unassigned usage is included in all-source totals, but excluded from project/task totals. Agent turn completion is not verified task success.');
  if(view==='activity') {
    html=statLine()+(task?section('Step timeline','<div id="task-step-timeline"></div>','', 'Select steps on the chart to collect them into a named subtask.'):section('Step timeline','<div class="notice">Choose a task above to chart its steps and collect subtasks.</div>'))+capturesTable()+section('Native event timeline',table('events',[
      {key:'ts',label:'When',filterText:r=>date(r.ts)+' '+(r.ts||''),cell:r=>date(r.ts)},
      {key:'name',label:'Operation',cell:r=>`<button class="inline-link clip" data-event="${esc(r.id)}">${esc(r.name)}</button>`},
      {key:'category',label:'Category',cell:r=>clip(r.category)},
      {key:'category_basis',label:'Assigned by',value:r=>r.category_basis==='Codex agent interpretation'?'Codex · '+r.category_confidence:r.kind==='generation'?'Native usage':'Text rule / unmatched',cell:r=>r.category_basis==='Codex agent interpretation'?badge('Codex · '+r.category_confidence):badge(r.kind==='generation'?'Native usage':'Text rule / unmatched')},
      {key:'runtime_role',label:'Runtime role',value:r=>r.kind==='generation'?'Model latency unknown':r.runtime_role,cell:r=>esc(r.kind==='generation'?'Model latency unknown':r.runtime_role)},
      {key:'runtime',label:'Runtime',numeric:true,cell:r=>seconds(r.runtime)},
      {key:'tokens',label:'Tokens',numeric:true,cell:r=>r.usage?compact(r.usage.total_tokens):'—'},
      {key:'bytes',label:'Output bytes',numeric:true,cell:r=>r.bytes==null?'—':compact(r.bytes)}
    ],data.events.slice().reverse().map(e=>({...e,tokens:e.usage?.total_tokens??null})),r=>[{id:'open',label:'Category rationale and event details',onSelect:()=>eventDetails(r)},{id:'trace',label:'Inspect in Langfuse',onSelect:()=>window.open(r.langfuse_url,'_blank','noopener')}]),'',`${data.event_count} matching events; latest ${data.events.length} available in this table. Search applies to these rows. Model tokens are not attributed to individual tools.`);
  }
  if(view==='rules') {
    html='<div class="notice"><strong>Two separate mechanisms:</strong> Codex reads event evidence and assigns purpose labels with rationale/confidence. Unreviewed events use the plain-text rules below. Rules do not invoke an LLM, do not search full commands, and do not override Codex-reviewed labels.</div>'+
      section('Current categories',categoryTable('reviewed-categories'),'', 'Open an event to inspect who assigned its category and why. Category rows summarize the currently selected scope.')+
      section('Fallback text rules',table('rules',[{key:'priority',label:'Order',numeric:true},{key:'category',label:'Category'},{key:'pattern',label:'Operation label contains (literal)',cell:r=>`<code>${esc(r.pattern)}</code>`},{key:'enabled',label:'Enabled',value:r=>r.enabled?'Yes':'No',cell:r=>badge(r.enabled?'Yes':'No')},{key:'version',label:'Version',numeric:true},{key:'matches',label:'Matching labels',numeric:true},{key:'eligible',label:'Unreviewed matches',numeric:true}],data.rules.map((r,index)=>({...r,priority:index+1,matches:data.events.filter(e=>e.kind==='tool'&&e.name.toLowerCase().includes(r.pattern.toLowerCase())).length,eligible:data.events.filter(e=>e.kind==='tool'&&e.category_basis!=='Codex agent interpretation'&&e.name.toLowerCase().includes(r.pattern.toLowerCase())).length})),r=>[{id:'edit',label:'Edit rule and preview matches',onSelect:()=>ruleDialog(r)}]),button('Add rule','data-add-rule',true,'plus'),'First enabled match wins in listed priority order. Matching is case-insensitive substring matching, not regex. Match counts use the current event window.');
  }
  if(view==='opportunities') html=section('Codex recommendations',findingsTable())+section('Additional detector signals',table('opportunities',[{key:'title',label:'Signal'},{key:'observation',label:'Evidence',cell:r=>clip(r.observation)},{key:'decision',label:'Decision',value:r=>r.state.decision,cell:r=>badge(r.state.decision)},{key:'implementation',label:'Implementation',value:r=>r.state.implementation,cell:r=>badge(r.state.implementation)},{key:'evaluation',label:'Evaluation',value:r=>r.state.evaluation,cell:r=>badge(r.state.evaluation)}],data.opportunities,r=>[{id:'review',label:'Review proposal and record decision',onSelect:()=>reviewOpportunity(r)}]),'','Detectors flag large or repeated results. A signal is not proof of waste; measured savings require a controlled comparison.');
  if(view==='experiments') html=section('Experiment proposals',table('experiments',[
    {key:'title',label:'Experiment'}, {key:'task_id',label:'Baseline task',value:r=>titleForTask(r.task_id),cell:r=>esc(titleForTask(r.task_id))},
    {key:'tokens',label:'Historical task tokens',numeric:true,cell:r=>compact(r.tokens)},
    {key:'reduction',label:'Measured token reduction',numeric:true,cell:r=>r.reduction==null?'Not measured':fmt(r.reduction*100)+'%'},
    {key:'created',label:'Proposed',filterText:r=>date(r.created)+' '+(r.created||''),cell:r=>date(r.created)}, {key:'state',label:'State',cell:r=>badge(r.state)}, {key:'verdict',label:'Latest verdict',value:r=>r.evaluations?.at(-1)?.reviews?.at(-1)?.verdict||'Not reviewed',cell:r=>esc(r.evaluations?.at(-1)?.reviews?.at(-1)?.verdict||'Not reviewed')}
  ],(data.experiments||[]).map(r=>({...r,title:r.proposal.title,tokens:r.baseline.usage.total_tokens,reduction:r.evaluations?.at(-1)?.measurements.token_reduction_fraction})),r=>[
    {id:'inspect',label:'Inspect protocol and baseline',onSelect:()=>showModal(r.title,
      '<dl class="detail-grid">'+Object.entries(r.proposal).map(([key,value])=>'<dt>'+esc(key.replaceAll('_',' '))+'</dt><dd>'+esc(value)+'</dd>').join('')+
      '<dt>Frozen baseline</dt><dd>'+esc(r.baseline_sha256)+'</dd><dt>Evidence window</dt><dd>'+esc(r.baseline.first_at)+' — '+esc(r.baseline.last_at)+'; '+fmt(r.baseline.event_count)+' events</dd></dl><p>Protocol and results below apply only to the recorded evaluation scope. Actual charges and pure model latency remain unknown.</p>'+experimentResults(r))}
  ]),'','Agents create proposals using the MCP plan_experiment tool or analyst_cli.py. The baseline is frozen at proposal creation; live task totals may subsequently change.');
  if(view==='setup'||view==='settings') html=section('Collection',`<dl class="detail-grid"><dt>State</dt><dd>${badge(data.sources.collection_enabled?'Enabled':'Paused')}</dd><dt>Authorized source</dt><dd>${esc(data.sources.root)}</dd><dt>Retained files</dt><dd>${data.sources.files}</dd><dt>Model HTTP exchanges</dt><dd>${data.capture_coverage.total_model_exchanges}</dd><dt>Source errors</dt><dd>${data.sources.errors.length}</dd></dl><div class="modal-actions">${button(data.sources.collection_enabled?'Pause collection':'Resume collection',`data-collection="${!data.sources.collection_enabled}"`)}</div>`, '', 'Pausing stops new exports and rejects new capture-route calls. Existing data is retained.')+section('Coverage limits',`<ul>${data.limitations.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><p>Private setup and credentials: <code>work/security/langfuse-stack/</code>. Shared controls follow the workspace design system.</p>`)+section('Audit log',table('audit',[{key:'at',label:'When',filterText:r=>date(r.at)+' '+(r.at||''),cell:r=>date(r.at)},{key:'action',label:'Action'},{key:'entity',label:'Entity',cell:r=>clip(r.entity)}],data.audit,null));
  if(view==='settings')html=`<div class="settings-links">${button('Projects','data-view="projects"')}${button('Collected prompts / assignments','data-view="inbox"')}${button('Add task','data-add-task')}${button('Codex findings','data-view="analysis"')}</div>`+html+`<section class="section"><h2>Cost-rate scenario</h2><p class="section-note">Exact model names; input / cached / output rates per million tokens. Enter your chosen rates and their date. Scenario estimates are separate from actual cash charges.</p><form data-cost-scenario><textarea class="ui-input rate-editor" disabled aria-label="Cost-rate scenario JSON" spellcheck="false"></textarea><div class="ui-actions">${button('Save rate scenario','type="submit"')}</div><p class="section-note">Example model entry: &quot;exact-model-name&quot;: {&quot;input&quot;: 1, &quot;cached&quot;: 0.1, &quot;output&quot;: 4}. These are illustrative values, not a price quote.</p></form></section>`;
  $('#content').innerHTML=html;
  if(view==='settings'){
    const editor=document.querySelector('.rate-editor');
    fetch('/api/work-cost-rates').then(r=>r.json()).then(scenario=>{if(editor.isConnected)editor.value=JSON.stringify(scenario,null,2);}).catch(e=>toast(e.message)).finally(()=>{if(editor.isConnected)editor.disabled=false;});
    document.querySelector('[data-cost-scenario]').onsubmit=async e=>{e.preventDefault();try{await post('work-cost-rates',JSON.parse(document.querySelector('.rate-editor').value));toast('Rate scenario saved.');}catch(error){toast(error.message);}};
  }

  $('#content').setAttribute('aria-busy','false');
  if(view==='activity'&&task) renderStepTimeline($('#task-step-timeline'),{taskId:task,onError:toast});
  if(view==='history') renderHistory($('#history-root'),{project,open:id=>openTaskHistory(id,showModal),onError:toast});
  mountTableMenus();
}

document.addEventListener('click',async event=>{
  const target=event.target.closest('button'); if(!target) return;
  try {
    if(target.hasAttribute('data-close')) return $('#modal').close();
    if(target.hasAttribute('data-refresh')) return await load();
    if(target.dataset.view) return openView(target.dataset.view);
    if(target.hasAttribute('data-add-project')) return newProject();
    if(target.hasAttribute('data-add-task')) return newTask();
    if(target.hasAttribute('data-add-rule')) return ruleDialog();
    if(target.hasAttribute('data-preview-rule')) return await previewRule();
    if(target.hasAttribute('data-reconcile')) return await reconcile();
    if(target.dataset.historyTask) return openTaskHistory(target.dataset.historyTask,showModal);
    if(target.dataset.taskDetails) return taskDetails(data.tasks.find(t=>t.id===target.dataset.taskDetails));
    if(target.dataset.openTask) {$('#modal').close();return await openTask(target.dataset.openTask);}
    if(target.dataset.event) return eventDetails(data.events.find(e=>e.id===target.dataset.event));
    if(target.hasAttribute('data-finding')) {const report=data.agent_analyses[0];return findingDetails(report.findings[Number(target.dataset.finding)],report);}
    if(target.dataset.page) {tables[target.dataset.page].page+=Number(target.dataset.delta);return refreshTable(target.dataset.page);}
    if(target.dataset.sort) {const state=tables[target.dataset.sort];if(state.sort!==target.dataset.key){state.sort=target.dataset.key;state.direction=1;}else if(state.direction===1){state.direction=-1;}else{state.sort=null;state.direction=1;}state.page=1;return refreshTable(target.dataset.sort);}
    if(target.dataset.clearSearch) {tables[target.dataset.clearSearch].search='';tables[target.dataset.clearSearch].page=1;return refreshTable(target.dataset.clearSearch);}
    if(target.dataset.resetTable) {tables[target.dataset.resetTable]={search:'',page:1,sort:null,direction:1,filters:{},hiddenColumns:[]};return refreshTable(target.dataset.resetTable);}
    if(target.hasAttribute('data-clear-filters')) {project='';task='';category='';syncURL();return await load();}
    if(target.dataset.collection) {await post('collection',{enabled:target.dataset.collection==='true'});return await load();}
  } catch(error) {toast(error.message);}
});
document.addEventListener('change',event=>{
  const id=event.target.dataset.columnToggle;if(!id) return;
  const state=tables[id], key=event.target.dataset.key;
  if(event.target.checked) state.hiddenColumns=state.hiddenColumns.filter(c=>c!==key);
  else {state.hiddenColumns.push(key);delete state.filters[key];if(state.sort===key)state.sort=null;}
  state.page=1;refreshTable(id);
});
document.addEventListener('click',event=>{
  if(!event.target.closest('.column-picker')) document.querySelectorAll('.column-picker[open]').forEach(p=>p.open=false);
});
document.addEventListener('keydown',event=>{
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
document.addEventListener('submit',async event=>{
  const element=event.target.closest('form[data-form]');if(!element)return;event.preventDefault();
  const values=Object.fromEntries(new FormData(element));if('enabled' in values)values.enabled=values.enabled==='true';
  busy=true;
  try {await post(element.dataset.form,values);$('#modal').close();toast('Saved. Original evidence is unchanged.');}
  catch(error) {toast(error.message);}
  finally {busy=false;await load();}
});
for(const name of ['project','task','category']) $('#'+name).addEventListener('change',async event=>{
  if(name==='project'){project=event.target.value;task='';}
  if(name==='task'){task=event.target.value;if(task)project=data.tasks.find(t=>t.id===task)?.project_id||project;}
  if(name==='category')category=event.target.value;
  syncURL();await load();
});
$('#refresh').onclick=load;
function setTheme(value) {
  document.documentElement.dataset.theme=value;
  const label=value==='dark'?'Switch to light theme':'Switch to dark theme';
  $('#theme').innerHTML=icon(value==='dark'?'sun':'moon')+`<span>${value==='dark'?'Light mode':'Dark mode'}</span>`;
  $('#theme').setAttribute('aria-label',label);$('#theme').title=label;
}
$('#theme').onclick=()=>{
  const value=document.documentElement.dataset.theme==='dark'?'light':'dark';
  setTheme(value);try {localStorage.setItem('ttgl-theme',value);}catch{}
};
for(const placeholder of document.querySelectorAll('[data-icon]')) placeholder.outerHTML=icon(placeholder.dataset.icon);
setTheme(document.documentElement.dataset.theme==='dark'?'dark':'light');
window.addEventListener('storage',event=>{if(event.key==='ttgl-theme')setTheme(event.newValue==='dark'?'dark':'light');});
$('#content').innerHTML=skeleton();
load();
setInterval(()=>{if((!primary()||!task||document.querySelector('[data-mining-active="true"]'))&&!document.hidden&&!$('#modal').open&&!document.activeElement?.matches('input,textarea,select')&&!document.querySelector('[data-step-select]:checked')&&!document.querySelector('.insight-card details[open]')&&!document.querySelector('.column-picker[open]')&&!busy)load();},10000);
