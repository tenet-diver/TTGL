import { renderHistory, openTaskHistory } from '/task-history.js';
import { collectionPage } from '/design-system/collection.js';
import { createActionMenu } from '/design-system/dom.js';

const $ = selector => document.querySelector(selector);
const esc = value => String(value ?? '').replace(/[&<>"']/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[char]));
const fmt = value => value == null ? 'Unknown' : Number(value).toLocaleString('en', {maximumFractionDigits: 2});
const compact = value => value == null ? 'Unknown' : Intl.NumberFormat('en', {notation:'compact',maximumFractionDigits:2}).format(value);
const date = value => value ? new Date(value).toLocaleString() : 'Unknown';
const seconds = value => value == null ? 'Unknown' : fmt(value) + 's';
const external = (url, title='Inspect in Langfuse') => `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(title)} ↗</a>`;
const badge = value => `<span class="badge">${esc(value)}</span>`;
const button = (title, attributes='', primary=false) => `<button class="evlv-button ${primary?'evlv-primary':'evlv-secondary'} evlv-compact" ${attributes}>${esc(title)}</button>`;
const section = (title, body, action='', note='') => `<section class="section"><div class="section-heading"><h2>${esc(title)}</h2>${action}</div>${note?`<p class="section-note">${note}</p>`:''}${body}</section>`;
const clip = value => `<span class="clip" title="${esc(value)}">${esc(value)}</span>`;
const config = {
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
let view = config[location.hash.slice(1)] ? location.hash.slice(1) : 'overview';
let project = query.get('project') || '', task = query.get('task') || '', category = query.get('category') || '';
let data = null, busy = false, tableMenus = [], toastTimer;
const tables = {};

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
  history.replaceState(null, '', location.pathname + (params.size?'?'+params:'') + '#' + view);
}
async function load() {
  if (busy) return;
  try {
    const params = new URLSearchParams();
    if(project) params.set('project',project);
    if(task) params.set('task',task);
    if(category) params.set('category',category);
    const response = await fetch('/api/workspace?' + params);
    if(!response.ok) throw Error('Workspace request failed');
    data = await response.json();
    render();
  } catch(error) { $('#live').textContent = 'Connection interrupted'; toast(error.message); }
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
function openView(next) { view=next; syncURL(); render(); window.scrollTo(0,0); }
async function openTask(id) {
  task=id; project=data.tasks.find(t=>t.id===id)?.project_id || ''; category=''; view='activity'; syncURL(); await load();
}
function table(id, columns, rows, actions, searchable=true) {
  const state=tables[id] ||= {search:'',page:1,sort:null,direction:1};
  const result=collectionPage(rows, {
    search:state.search, searchText:row=>Object.entries(row).filter(([k,v])=>typeof v==='string'||typeof v==='number').map(([,v])=>v).join(' '),
    page:state.page,pageSize:id==='overview-categories'?10:20,
    compare:state.sort?(a,b)=>{
      const left=a[state.sort],right=b[state.sort];
      return state.direction*(typeof left==='number'&&typeof right==='number'?left-right:String(left??'').localeCompare(String(right??'')));
    }:undefined
  });
  state.page=result.page;
  const toolbar=searchable?`<div class="list-toolbar"><div class="list-search evlv-search"><input class="evlv-input" data-search="${id}" value="${esc(state.search)}" placeholder="Search these rows" aria-label="Search ${esc(id)}"><button data-clear-search="${id}" aria-label="Clear search">×</button></div><span class="muted">${fmt(result.total)} rows</span></div>`:'';
  const head=columns.map(column=>`<th scope="col" class="${column.numeric?'numeric':''}"><button data-sort="${id}" data-key="${column.key}">${esc(column.label)}${state.sort===column.key?(state.direction===1?' ↑':' ↓'):''}</button></th>`).join('');
  const body=result.items.map((row,index)=>{
    const cells=columns.map(column=>`<td class="${column.numeric?'numeric':''}">${column.cell?column.cell(row):esc(row[column.key])}</td>`).join('');
    let menu='';
    if(actions) {const key=id+'-'+index; tableMenus.push({key,label:'Actions for '+(row.title||row.name||row.id||'row'),actions:actions(row).map(action=>({...action,onSelect:()=>{try{Promise.resolve(action.onSelect()).catch(error=>toast(error.message));}catch(error){toast(error.message);}}}))}); menu=`<td class="row-menu"><span data-row-menu="${key}"></span></td>`;}
    return `<tr>${cells}${menu}</tr>`;
  }).join('');
  return toolbar+`<div class="table-container evlv-table-scroll"><table class="evlv-table"><thead><tr>${head}${actions?'<th scope="col"><span class="evlv-sr-only">Actions</span></th>':''}</tr></thead><tbody>${body||`<tr><td colspan="${columns.length+(actions?1:0)}" class="table-empty">No matching rows.</td></tr>`}</tbody></table></div>`+
    (result.pages>1?`<div class="pagination"><span>${(result.page-1)*result.pageSize+1}–${Math.min(result.page*result.pageSize,result.total)} of ${result.total}</span>${button('Previous',`data-page="${id}" data-delta="-1" ${result.page===1?'disabled':''}`)}<span>${result.page} / ${result.pages}</span>${button('Next',`data-page="${id}" data-delta="1" ${result.page===result.pages?'disabled':''}`)}</div>`:'');
}
function experimentResults(experiment) {
  const accounting=experiment.accounting?.at(-1)?.payload;
  const cost=accounting?`<section class="section"><h3>Accrued research overhead</h3><p>${fmt(accounting.current_research_tokens)} native tokens through ${esc(accounting.as_of)}; ${fmt(accounting.illustrative_repetitions_to_recover_current_tokens)} similar ${esc(accounting.unit||'diagnostic cases')} to recover that token count at the observed mean saving. This is not cash break-even. First use has no net saving.</p><details><summary>Accounting scope and limitations</summary><p>${esc(accounting.limitations)}</p></details></section>`:'';
  return cost+(experiment.evaluations||[]).map(evaluation=>{
    const m=evaluation.measurements;
    const rows=m.cells.map(c=>`<tr><td>${esc(c.case)}</td><td>${esc(c.condition)}</td><td>${fmt(c.usage.total_tokens)}</td><td>${seconds(c.wall_seconds)}</td><td>${c.quality.passed?'Pass':'Fail'}</td></tr>`).join('');
    return `<section class="section"><h3>${esc(evaluation.protocol.id)}</h3><p>${esc(m.scope)}</p><p>Native total tokens: <strong>${fmt(m.raw_total_tokens)} → ${fmt(m.compact_total_tokens)}</strong>. Registered gate: <strong>${m.acceptance_passed?'Passed':'Failed'}</strong>. Token reduction: ${fmt(m.token_reduction_fraction*100)}%. Trial inference is included per arm; analyst, implementation and evaluation overhead is separate.</p><div class="table-container evlv-table-scroll"><table class="evlv-table"><thead><tr><th>Case</th><th>Presentation</th><th>Total tokens</th><th>Wall time</th><th>Quality</th></tr></thead><tbody>${rows}</tbody></table></div>${evaluation.reviews.map(review=>`<h4>Analyst verdict: ${esc(review.verdict)}</h4><p>${esc(review.notes)}</p>`).join('')}<details><summary>Protocol and evidence references</summary><pre>${esc(JSON.stringify(evaluation,null,2))}</pre></details></section>`;
  }).join('') || '<p>Proposal only; no measured trial results.</p>';
}
function showModal(title, body) {
  $('#modal-content').innerHTML=`<div class="modal-heading"><h2 id="modal-title">${esc(title)}</h2>${button('Close','data-close')}</div><div class="modal-body">${body}</div>`;
  if(!$('#modal').open) $('#modal').showModal();
}
function field(label, name, value='', {textarea=false,required=false,hint=''}={}) {
  const control=textarea?`<textarea class="evlv-input" aria-label="${esc(label)}" name="${name}" ${required?'required':''}>${esc(value)}</textarea>`:`<input class="evlv-input" aria-label="${esc(label)}" name="${name}" value="${esc(value)}" ${required?'required':''}>`;
  return `<label>${esc(label)}${control}${hint?`<small>${esc(hint)}</small>`:''}</label>`;
}
function form(action, body, submit='Save') {return `<form data-form="${action}">${body}<div class="modal-actions">${button('Cancel','type="button" data-close')}${button(submit,'type="submit"',true)}</div></form>`;}
function newProject() {showModal('Add project',form('project',field('Project name','name','',{required:true})+field('Repository / working folder','repo','',{required:true})+field('Analysis scope','scope','',{textarea:true}),'Add project'));}
function newTask() {
  if(!data.projects.length) return newProject();
  showModal('Add task',form('task',`<label>Project<select class="evlv-input evlv-select" aria-label="Project" name="project_id">${options(data.projects,'id','name',project)}</select></label>`+field('Task title','title','',{required:true})+field('Intended outcome','goal','',{textarea:true,required:true})+field('Acceptance / verification criteria','acceptance','',{textarea:true}),'Start task'));
}
function assignTurn(turn) {
  if(!data.tasks.length) return toast('Create a task before assigning a turn.');
  showModal('Assign collected turn',`<p>${esc((turn.prompt||'Prompt unavailable').slice(0,300))}</p>`+form('assign',`<input type="hidden" name="session_id" value="${esc(turn.session_id)}"><input type="hidden" name="turn_id" value="${esc(turn.turn_id)}"><label>Task<select class="evlv-input evlv-select" aria-label="Task" name="task_id" required>${options(data.tasks,'id','title',task)}</select></label>`,'Assign turn'));
}
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
    `<label>Enabled<select class="evlv-input evlv-select" aria-label="Enabled" name="enabled"><option value="true" ${rule.enabled!==0?'selected':''}>Yes</option><option value="false" ${rule.enabled===0?'selected':''}>No</option></select></label>`));
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
    {key:'started_at',label:'When',cell:r=>date(r.started_at)},
    {key:'task_id',label:'Task',cell:r=>clip(titleForTask(r.task_id))},
    {key:'status',label:'HTTP',cell:r=>badge(r.status??r.state)},
    {key:'response_body_state',label:'Response body',cell:r=>`<span class="${r.response_body_available?'':'danger'}">${esc(r.response_body_state)}</span>`},
    {key:'correlation',label:'Matched by'},
    {key:'compression',label:'Live compression',cell:r=>r.compression?.changes?.length?external(r.compression_url,r.compression.policy+' · '+fmt(r.request_bytes)+' → '+fmt(r.forwarded_request_bytes)+' B'):esc(r.compression?.policy||'off')},
    {key:'request_bytes',label:'Request / response bytes',numeric:true,cell:r=>compact(r.request_bytes)+' / '+compact(r.response_bytes)},
    {key:'elapsed_seconds',label:'HTTP duration',numeric:true,cell:r=>seconds(r.elapsed_seconds)},
    {key:'first_body_byte_seconds',label:'First body byte',numeric:true,cell:r=>seconds(r.first_body_byte_seconds)}
  ],data.wire_captures,r=>[{id:'open',label:'Inspect retained request / response',onSelect:()=>window.open(r.langfuse_url,'_blank','noopener')}]),'',esc(notice)+(data.wire_captures.length?'':' This selection may be transcript-only; clear task/project filters to see other captured exchanges.'));
}
function tasksTable(rows) {
  return table('tasks',[{key:'title',label:'Task',cell:r=>`<button class="inline-link" data-task-details="${esc(r.id)}">${esc(r.title)}</button>`},
    {key:'project_id',label:'Project',cell:r=>esc(data.projects.find(p=>p.id===r.project_id)?.name||'Unknown')},
    {key:'status',label:'Status',cell:r=>badge(r.status)},
    {key:'total_tokens',label:'Measured tokens',numeric:true,cell:r=>compact(r.usage?.total_tokens)},
    {key:'updated',label:'Updated',cell:r=>date(r.updated)}],rows.map(r=>({...r,total_tokens:r.usage?.total_tokens||0})),r=>[
      {id:'open',label:'Open task evidence',onSelect:()=>openTask(r.id)},
      {id:'history',label:'Analyze / inspect subtasks',onSelect:()=>openTaskHistory(r.id,showModal)},
      {id:'details',label:'Goal and verification',onSelect:()=>taskDetails(r)},
      {id:'status',label:'Mark active',onSelect:async()=>{await post('task_status',{id:r.id,status:'active'});await load();}},
      {id:'complete',label:'Complete with evidence',onSelect:()=>completeTask(r)}
    ]);
}
function reviewOpportunity(row) {
  const select=(label,name,values,current)=>`<label>${label}<select class="evlv-input evlv-select" aria-label="${esc(label)}" name="${name}">${values.map(v=>`<option ${v===current?'selected':''}>${v}</option>`).join('')}</select></label>`;
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
function render() {
  if(!data) return;
  tableMenus=[];
  $('#title').textContent=config[view][0]; $('#subtitle').textContent=config[view][1];
  $('#live').textContent=(data.sources.collection_enabled?'Collecting · ':'Paused · ')+date(data.at);
  $('#inbox-count').textContent=data.inbox.length||'';
  $('#langfuse').href=data.langfuse_url;
  document.querySelectorAll('nav [data-view]').forEach(b=>{b.classList.toggle('active',b.dataset.view===view);if(b.dataset.view===view)b.setAttribute('aria-current','page');else b.removeAttribute('aria-current');});
  $('#project').innerHTML='<option value="">All projects</option>'+options(data.projects,'id','name',project);
  $('#task').innerHTML='<option value="">All tasks</option>'+options(data.tasks.filter(t=>!project||t.project_id===project),'id','title',task);
  const categories=[...new Set(['model inference','other tools',...data.categories.map(c=>c.name),...data.rules.map(r=>r.category)])].sort();
  $('#category').innerHTML='<option value="">All categories</option>'+categories.map(name=>`<option ${category===name?'selected':''}>${esc(name)}</option>`).join('');
  const scope=task?titleForTask(task):project?data.projects.find(p=>p.id===project)?.name:'All collected sources';
  $('#scope-summary').innerHTML=`<span>Scope: <strong>${esc(scope)}</strong>${category?' · '+esc(category):''}</span><span>Selected: <strong>${fmt(data.usage.total_tokens)}</strong> tokens</span><span>All sources: <strong>${fmt(data.usage_scope.all_sources.total_tokens)}</strong></span><button class="inline-link" data-reconcile>Why totals differ / reconcile</button>`;
  $('#page-actions').innerHTML=view==='projects'?button('Add project','data-add-project',true):view==='tasks'?button('Add task','data-add-task',true):'';
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
  if(view==='projects') html=section('Projects',table('projects',[{key:'name',label:'Project'},{key:'repo',label:'Repository',cell:r=>clip(r.repo)},{key:'scope',label:'Scope',cell:r=>clip(r.scope)},{key:'created',label:'Created',cell:r=>date(r.created)}],data.projects,r=>[{id:'open',label:'Open project',onSelect:async()=>{project=r.id;task='';category='';view='overview';syncURL();await load();}}]));
  if(view==='history') html='<div id="history-root"></div>';
  if(view==='tasks') html=section('Defined tasks',tasksTable(data.tasks.filter(t=>!project||t.project_id===project)),button('Open unassigned inbox','data-view="inbox"'),'Tasks are explicit goals. Their measured usage comes from assigned turns, not automatically inferred boundaries.');
  if(view==='inbox') html=section('Unassigned turns',table('inbox',[{key:'prompt',label:'Prompt / activity',cell:r=>clip((r.prompt||'Prompt unavailable').replace(/\s+/g,' '))},{key:'repo',label:'Working folder',cell:r=>clip(r.repo)},{key:'start',label:'Started',cell:r=>date(r.start)},{key:'tokens',label:'Measured tokens',numeric:true,cell:r=>compact(r.usage?.total_tokens)},{key:'completed',label:'Agent turn',cell:r=>badge(r.completed?'Completed':'Open')}],data.inbox.map(r=>({...r,id:r.session_id+':'+r.turn_id,tokens:r.usage?.total_tokens||0})),r=>[{id:'assign',label:'Assign to a task',onSelect:()=>assignTurn(r)},{id:'open',label:'Open transcript',onSelect:()=>window.open(r.langfuse_url,'_blank','noopener')}]),'', 'Unassigned usage is included in all-source totals, but excluded from project/task totals. Agent turn completion is not verified task success.');
  if(view==='activity') {
    html=statLine()+capturesTable()+section('Native event timeline',table('events',[
      {key:'ts',label:'When',cell:r=>date(r.ts)},
      {key:'name',label:'Operation',cell:r=>`<button class="inline-link clip" data-event="${esc(r.id)}">${esc(r.name)}</button>`},
      {key:'category',label:'Category',cell:r=>clip(r.category)},
      {key:'category_basis',label:'Assigned by',cell:r=>r.category_basis==='Codex agent interpretation'?badge('Codex · '+r.category_confidence):badge(r.kind==='generation'?'Native usage':'Text rule / unmatched')},
      {key:'runtime_role',label:'Runtime role',cell:r=>esc(r.kind==='generation'?'Model latency unknown':r.runtime_role)},
      {key:'runtime',label:'Runtime',numeric:true,cell:r=>seconds(r.runtime)},
      {key:'tokens',label:'Tokens',numeric:true,cell:r=>r.usage?compact(r.usage.total_tokens):'—'},
      {key:'bytes',label:'Output bytes',numeric:true,cell:r=>r.bytes==null?'—':compact(r.bytes)}
    ],data.events.slice().reverse().map(e=>({...e,tokens:e.usage?.total_tokens||0})),r=>[{id:'open',label:'Category rationale and event details',onSelect:()=>eventDetails(r)},{id:'trace',label:'Inspect in Langfuse',onSelect:()=>window.open(r.langfuse_url,'_blank','noopener')}]),'',`${data.event_count} matching events; latest ${data.events.length} available in this table. Search applies to these rows. Model tokens are not attributed to individual tools.`);
  }
  if(view==='rules') {
    html='<div class="notice"><strong>Two separate mechanisms:</strong> Codex reads event evidence and assigns purpose labels with rationale/confidence. Unreviewed events use the plain-text rules below. Rules do not invoke an LLM, do not search full commands, and do not override Codex-reviewed labels.</div>'+
      section('Current categories',categoryTable('reviewed-categories'),'', 'Open an event to inspect who assigned its category and why. Category rows summarize the currently selected scope.')+
      section('Fallback text rules',table('rules',[{key:'priority',label:'Order',numeric:true},{key:'category',label:'Category'},{key:'pattern',label:'Operation label contains (literal)',cell:r=>`<code>${esc(r.pattern)}</code>`},{key:'enabled',label:'Enabled',cell:r=>badge(r.enabled?'Yes':'No')},{key:'version',label:'Version',numeric:true},{key:'matches',label:'Matching labels',numeric:true},{key:'eligible',label:'Unreviewed matches',numeric:true}],data.rules.map((r,index)=>({...r,priority:index+1,matches:data.events.filter(e=>e.kind==='tool'&&e.name.toLowerCase().includes(r.pattern.toLowerCase())).length,eligible:data.events.filter(e=>e.kind==='tool'&&e.category_basis!=='Codex agent interpretation'&&e.name.toLowerCase().includes(r.pattern.toLowerCase())).length})),r=>[{id:'edit',label:'Edit rule and preview matches',onSelect:()=>ruleDialog(r)}]),button('Add rule','data-add-rule',true),'First enabled match wins in listed priority order. Matching is case-insensitive substring matching, not regex. Match counts use the current event window.');
  }
  if(view==='opportunities') html=section('Codex recommendations',findingsTable())+section('Additional detector signals',table('opportunities',[{key:'title',label:'Signal'},{key:'observation',label:'Evidence',cell:r=>clip(r.observation)},{key:'decision',label:'Decision',cell:r=>badge(r.state.decision)},{key:'implementation',label:'Implementation',cell:r=>badge(r.state.implementation)},{key:'evaluation',label:'Evaluation',cell:r=>badge(r.state.evaluation)}],data.opportunities,r=>[{id:'review',label:'Review proposal and record decision',onSelect:()=>reviewOpportunity(r)}]),'','Detectors flag large or repeated results. A signal is not proof of waste; measured savings require a controlled comparison.');
  if(view==='experiments') html=section('Experiment proposals',table('experiments',[
    {key:'title',label:'Experiment'}, {key:'task_id',label:'Baseline task',cell:r=>esc(titleForTask(r.task_id))},
    {key:'tokens',label:'Historical task tokens',numeric:true,cell:r=>compact(r.tokens)},
    {key:'reduction',label:'Measured token reduction',numeric:true,cell:r=>r.reduction==null?'Not measured':fmt(r.reduction*100)+'%'},
    {key:'created',label:'Proposed',cell:r=>date(r.created)}, {key:'state',label:'State',cell:r=>badge(r.state)}, {key:'verdict',label:'Latest verdict',cell:r=>esc(r.evaluations?.at(-1)?.reviews?.at(-1)?.verdict||'Not reviewed')}
  ],(data.experiments||[]).map(r=>({...r,title:r.proposal.title,tokens:r.baseline.usage.total_tokens,reduction:r.evaluations?.at(-1)?.measurements.token_reduction_fraction})),r=>[
    {id:'inspect',label:'Inspect protocol and baseline',onSelect:()=>showModal(r.title,
      '<dl class="detail-grid">'+Object.entries(r.proposal).map(([key,value])=>'<dt>'+esc(key.replaceAll('_',' '))+'</dt><dd>'+esc(value)+'</dd>').join('')+
      '<dt>Frozen baseline</dt><dd>'+esc(r.baseline_sha256)+'</dd><dt>Evidence window</dt><dd>'+esc(r.baseline.first_at)+' — '+esc(r.baseline.last_at)+'; '+fmt(r.baseline.event_count)+' events</dd></dl><p>Protocol and results below apply only to the recorded evaluation scope. Actual charges and pure model latency remain unknown.</p>'+experimentResults(r))}
  ]),'','Agents create proposals using the MCP plan_experiment tool or analyst_cli.py. The baseline is frozen at proposal creation; live task totals may subsequently change.');
  if(view==='setup') html=section('Collection',`<dl class="detail-grid"><dt>State</dt><dd>${badge(data.sources.collection_enabled?'Enabled':'Paused')}</dd><dt>Authorized source</dt><dd>${esc(data.sources.root)}</dd><dt>Retained files</dt><dd>${data.sources.files}</dd><dt>Model HTTP exchanges</dt><dd>${data.capture_coverage.total_model_exchanges}</dd><dt>Source errors</dt><dd>${data.sources.errors.length}</dd></dl><div class="modal-actions">${button(data.sources.collection_enabled?'Pause collection':'Resume collection',`data-collection="${!data.sources.collection_enabled}"`)}</div>`, '', 'Pausing stops new exports and rejects new capture-route calls. Existing data is retained.')+section('Coverage limits',`<ul>${data.limitations.map(x=>`<li>${esc(x)}</li>`).join('')}</ul><p>Private setup and credentials: <code>work/security/langfuse-stack/</code>. The app uses the pinned private EVLV DOM design-system distribution.</p>`)+section('Audit log',table('audit',[{key:'at',label:'When',cell:r=>date(r.at)},{key:'action',label:'Action'},{key:'entity',label:'Entity',cell:r=>clip(r.entity)}],data.audit,null));
  $('#content').innerHTML=html;
  if(view==='history') renderHistory($('#history-root'),{project,open:id=>openTaskHistory(id,showModal),onError:toast});
  for(const menu of tableMenus) {
    const target=document.querySelector(`[data-row-menu="${menu.key}"]`);
    if(target) target.append(createActionMenu(document,menu.label,menu.actions));
  }
}

document.addEventListener('click',async event=>{
  const target=event.target.closest('button'); if(!target) return;
  try {
    if(target.hasAttribute('data-close')) return $('#modal').close();
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
    if(target.dataset.page) {tables[target.dataset.page].page+=Number(target.dataset.delta);return render();}
    if(target.dataset.sort) {const state=tables[target.dataset.sort];state.direction=state.sort===target.dataset.key?-state.direction:1;state.sort=target.dataset.key;return render();}
    if(target.dataset.clearSearch) {tables[target.dataset.clearSearch].search='';tables[target.dataset.clearSearch].page=1;return render();}
    if(target.hasAttribute('data-clear-filters')) {project='';task='';category='';syncURL();return await load();}
    if(target.dataset.collection) {await post('collection',{enabled:target.dataset.collection==='true'});return await load();}
  } catch(error) {toast(error.message);}
});
document.addEventListener('input',event=>{
  const id=event.target.dataset.search;if(!id) return;
  const position=event.target.selectionStart;tables[id].search=event.target.value;tables[id].page=1;render();
  const field=document.querySelector(`[data-search="${id}"]`);field?.focus();field?.setSelectionRange(position,position);
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
$('#theme').onclick=()=>{const value=document.documentElement.dataset.theme==='dark'?'light':'dark';document.documentElement.dataset.theme=value;localStorage.setItem('ttgl-theme',value);};
try {const theme=localStorage.getItem('ttgl-theme');if(theme==='dark'||theme==='light')document.documentElement.dataset.theme=theme;}catch{}
load();
setInterval(()=>{if(!document.hidden&&!$('#modal').open&&!document.activeElement?.matches('input,textarea,select')&&!busy)load();},10000);
