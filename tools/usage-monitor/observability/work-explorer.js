import {button,badge,emptyState,escapeHTML as esc} from '/ui.js';
import {renderStepTimeline} from '/step-timeline.js';
const n=v=>v==null?'Unknown':Number(v).toLocaleString('en',{maximumFractionDigits:2});
const price=v=>v==null?'Unknown':Number(v).toLocaleString('en',{maximumFractionDigits:Math.abs(v)<.01?6:2});
const compact=v=>v==null?'Unknown':Intl.NumberFormat('en',{notation:'compact',maximumFractionDigits:2}).format(v);
const duration=v=>v==null?'Unknown':v<60?n(v)+'s':v<3600?n(v/60)+'m':n(v/3600)+'h';
const types=['feature','bugfix','investigation','refactor','testing','documentation','operations','other','unclassified'];
const selectedSubtasks=new Map();
let prefs={query:'',status:'',task_type:'',attribution:'measured',metric:'steps',offset:0};
try{prefs={...prefs,...JSON.parse(localStorage.getItem('ttgl-work-preferences')||'{}')};}catch{}
function save(){try{localStorage.setItem('ttgl-work-preferences',JSON.stringify(prefs));}catch{}}
export function explorerParams(project){return new URLSearchParams({...(project?{project}:{}),query:prefs.query,status:prefs.status,task_type:prefs.task_type,attribution:prefs.attribution,limit:100,offset:prefs.offset||0});}
const select=(name,label,values,value)=>`<label>${esc(label)}<select class="ui-input" data-work-filter="${name}" aria-label="${esc(label)}">${values.map(([id,text])=>`<option value="${esc(id)}" ${id===value?'selected':''}>${esc(text)}</option>`).join('')}</select></label>`;
const metricValue=(metric,v,unit='USD')=>metric==='runtime_seconds'?duration(v):metric==='cost'?v==null?'Unknown':price(v)+' '+unit:compact(v);
function stats(m,estimate=false,unit='USD') {return `<div class="work-metrics">${[['Steps',n(m.steps)],['Recorded runtime',duration(m.runtime_seconds)],[(estimate?'Estimated ':'')+'Tokens',compact(m.tokens)],[estimate?'Allocated API estimate':'API token estimate',m.cost==null?'Unknown':price(m.cost)+' '+unit]].map(([label,value])=>`<div><small>${label}</small><strong>${value}</strong></div>`).join('')}</div>`;}
function bars(rows,metric,unit){
  const value=r=>r[metric]??(metric==='cost'?r.known_cost:metric==='runtime_seconds'?r.known_runtime_seconds:null);
  const max=Math.max(0,...rows.map(r=>value(r)??0));
  return `<div class="bar-chart" role="img" aria-label="${esc(metric.replaceAll('_',' '))} by type">${rows.map(r=>`<div class="bar-row"><span>${esc(r.type)}</span><div class="bar-track"><div class="bar-fill" style="width:${value(r)==null?0:max?Math.max(1,value(r)/max*100):0}%"></div></div><strong>${r[metric]==null&&value(r)>0?'≥ ':''}${metricValue(metric,value(r),unit)}</strong><small>${n(r.count)} items${r[metric]==null&&value(r)>0?' · known portion only':''}</small></div>`).join('')||'<p class="muted">No classified work in this scope yet.</p>'}</div>`;
}
function knowledgeTable(table,id,items){
  return table(id,[
    {key:'title',label:'Knowledge',cell:r=>`<strong>${esc(r.title)}</strong>`},
    {key:'statement',label:'Lesson',cell:r=>`<span class="table-prose">${esc(r.statement)}</span>`},
    {key:'task_title',label:'Source task',cell:r=>button(r.task_title,`data-work-task="${esc(r.task_id)}"`)},
    {key:'status',label:'Status',value:r=>r.stale?'Source changed':'Candidate',cell:r=>badge(r.stale?'Source changed':'Candidate')},
    {key:'confidence',label:'Model confidence',numeric:true,cell:r=>n(r.confidence)+' (uncalibrated)'},
    {key:'evidence',label:'Evidence',value:r=>r.step_ids.length,cell:r=>`<details><summary>${r.step_ids.length} source steps</summary>${r.step_ids.map(id=>button('Inspect step',`data-knowledge-step="${esc(id)}"`)).join('')}</details>`}
  ],items,null);
}
function usageColumns(unit){return [
  {key:'steps',label:'Tool steps',numeric:true,value:r=>r.metrics.steps,cell:r=>n(r.metrics.steps)},
  {key:'responses',label:'Responses',numeric:true,value:r=>r.metrics.responses,cell:r=>r.usage_basis&&r.usage_basis!=='native_turn'?'Unattributed':n(r.metrics.responses)},
  {key:'runtime',label:'Tool runtime',numeric:true,value:r=>r.metrics.runtime_seconds,cell:r=>duration(r.metrics.runtime_seconds)},
  {key:'tokens',label:'Tokens',numeric:true,value:r=>r.metrics.tokens,cell:r=>r.metrics.tokens==null&&r.usage_basis==='unattributed'?'Unattributed':n(r.metrics.tokens)},
  {key:'cost',label:'API token estimate',numeric:true,value:r=>r.metrics.cost,cell:r=>r.metrics.cost==null?(r.usage_basis==='unattributed'?'Unattributed':'No matched rate'):price(r.metrics.cost)+' '+unit}
];}
const providers=[
  ['mem0','Mem0','Agent memory extraction and retrieval. The Mem0 SDK is Apache-2.0; a dashboard depends on the deployment. The older OpenMemory UI is archived.','https://github.com/mem0ai/mem0'],
  ['cognee','Cognee','A document-to-memory pipeline combining graph and vector retrieval. Inspect the current visualization and deployment options in the project.','https://github.com/topoteretes/cognee'],
  ['graphiti','Graphiti','Temporal knowledge graph with hybrid retrieval. Explore a compatible deployed graph through its database UI, such as Neo4j Browser.','https://github.com/getzep/graphiti'],
  ['letta','Letta','Stateful agent memory with an agent development UI. ADE documentation currently sits under the legacy V1 SDK; check deployment compatibility.','https://docs.letta.com/v1-sdk/ade']
];
function safeURL(value){try{const u=new URL(value);return ['http:','https:'].includes(u.protocol)&&!u.username&&!u.password?u.href:null;}catch{return null;}}
function links(){try{return JSON.parse(localStorage.getItem('ttgl-knowledge-explorers')||'{}');}catch{return {};}}
export async function renderExplorer(root,{view,data,taskId,project,onProject,onTask,onRefresh,onInspect,table,mountTableMenus,post,onError}) {
  const token=Symbol();root._workToken=token;
  const total=data.totals,unit=data.cost_scenario.unit;
  const filters=`<form class="work-filters" data-work-search><label class="work-search">Search work<input class="ui-input" name="query" aria-label="Search work" placeholder="Task, subtask, or knowledge…" value="${esc(prefs.query)}"></label>${select('project','Project',[['','All projects'],...data.projects.map(p=>[p.id,p.name])],project)}${select('status','Status',[['','All statuses'],['active','Active'],['waiting','Waiting'],['completed','Completed']],prefs.status)}${select('task_type','Task type',[['','All types'],...types.map(t=>[t,t])],prefs.task_type)}${button('Search','type="submit"')}${button('Reset','type="button" data-work-reset')}</form>`;
  let html=filters;
  if(view==='tasks'){
    html+=`<div class="work-overview"><div><span class="eyebrow">Work at a glance</span><h2>${n(total.tasks)} tasks <span class="muted">/ ${n(total.subtasks)} subtasks / ${n(total.steps)} tool steps</span></h2></div>${button(data.discovery_enabled?'Log discovery enabled':'Discover tasks from logs','data-discover-tasks')}</div>`;
    if(taskId)html+=`<div data-work-detail><p role="status">Loading task hierarchy…</p></div>`;
    else html+=table('work-tasks',[
      {key:'title',label:'Task',cell:r=>`<button class="inline-link table-prose" data-work-task="${esc(r.id)}">${esc(r.title)}</button>`},
      {key:'project_name',hiddenByDefault:true,label:'Project'},{key:'status',label:'Status',cell:r=>badge(r.status)},{key:'type',label:'Type'},
      ...usageColumns(unit),
      {key:'updated',label:'Last activity',cell:r=>esc(r.updated?.slice(0,19).replace('T',' '))},
      {key:'summary',hiddenByDefault:true,label:'Summary',cell:r=>`<span class="table-prose">${esc(r.summary||'Recorded activity; semantic mining pending.')}</span>`}
    ],data.tasks,r=>[{id:'open',label:'Explore task',onSelect:()=>onTask(r.id)}]);
    if(!taskId&&(data.next_offset!=null||data.offset))html+=`<div class="pagination"><span>Tasks ${data.offset+1}–${Math.min(data.offset+data.tasks.length,data.total)} of ${data.total}. Table sorting and column filters apply to this batch.</span>${button('Previous tasks',`data-work-page="${Math.max(0,data.offset-100)}" ${!data.offset?'disabled':''}`)}${button('Next tasks',`data-work-page="${data.next_offset??0}" ${data.next_offset==null?'disabled':''}`)}</div>`;
    if(data.undiscovered)html+=`<div class="work-callout"><div><strong>${n(data.undiscovered)} collected prompts await task assignment</strong><p>Prompt-based task boundaries are provisional. Group related turns before mining a long-running task.</p></div>${button('Review prompts','data-view="inbox"')}</div>`;
  }
  if(view==='analytics'){
    html+=`<div class="stats"><div class="stat"><small>Tasks / subtasks</small><strong>${n(total.tasks)} / ${n(total.subtasks)}</strong></div><div class="stat"><small>Source steps</small><strong>${n(total.steps)}</strong></div><div class="stat"><small>Known native tokens</small><strong>${compact(total.known_tokens)}</strong><span>${n(total.tasks_missing_tokens)} tasks with incomplete counters</span></div><div class="stat"><small>Recorded runtime sum</small><strong>${duration(total.runtime_seconds)}</strong></div></div><div class="chart-controls">${select('metric','Measure',[['steps','Steps'],['runtime_seconds','Recorded runtime'],['tokens','Tokens'],['cost','Rate-scenario cost']],prefs.metric)}${select('attribution','Subtask attribution',[['measured','Measured only'],['step_share','Estimate by tool-step share']],prefs.attribution)}</div><div class="chart-grid"><section class="chart-card"><h2>By task type</h2>${bars(data.task_types,prefs.metric,unit)}</section><section class="chart-card"><h2>By subtask type ${prefs.attribution==='step_share'?badge('Estimated tokens / cost'):''}</h2>${bars(data.subtask_types,prefs.metric,unit)}</section></div><div class="work-callout"><div><strong>Measurement scope</strong><p>Known API token estimate: ${price(total.known_cost)} ${unit}; ${n(total.tasks_missing_cost)} tasks with missing counters or unmatched rates. This is a partial total when coverage is incomplete.</p>${safeURL(data.cost_scenario.source)?`<p><a href="${esc(safeURL(data.cost_scenario.source))}" target="_blank" rel="noopener">Rate source ↗</a></p>`:''}<p>${esc(data.cost_scenario.name||'Custom rate scenario')} · ${esc(data.cost_scenario.as_of)}. ${esc(data.cost_scenario.basis||'User-configured token rates; actual charges remain unknown.')}</p><p>${esc(data.measurement_note)}</p><p>Step-share distributes each turn’s tokens and scenario cost by its number of tool steps; it does not measure inference used by a subtask. Turns without tool steps remain unattributed.</p><p>Mining / naming overhead: ${n(total.mining_overhead_tokens)} known tokens, separate from source work. Unknown call usage may remain.</p></div>${button('Configure cost rates','data-view="settings"')}</div>`;
  }
  if(view==='knowledge'){
    html+=`<section class="section"><div class="section-heading"><h2>Knowledge from completed activity</h2>${button('Explore work','data-view="tasks"')}</div><p class="section-note">Luna proposes reusable lessons with source evidence. Candidates remain unverified; they are not automatically added to model memory.</p>${knowledgeTable(table,'work-knowledge',data.knowledge)}${data.knowledge.length===100?'<p>First 100 candidates; narrow your search for more.</p>':''}</section><section class="section"><h2>Explore other knowledge systems</h2><p class="section-note">Save a link to an existing explorer. These links do not connect an API, export activity, install a service, or establish benchmark superiority.</p>${table('knowledge-systems',[
      {key:'title',label:'System'},
      {key:'text',label:'Purpose',cell:r=>`<span class="table-prose">${esc(r.text)}</span>`},
      {key:'status',label:'Status'},
      {key:'url',label:'Documentation',cell:r=>`<a target="_blank" rel="noopener" href="${r.url}">Project / UI docs ↗</a>`},
      {key:'explorer',label:'Explorer',cell:r=>`<form data-explorer-link="${r.id}"><input type="url" class="ui-input" name="url" aria-label="${r.title} explorer URL" placeholder="https://your-deployment/" value="${esc(r.saved||'')}"><div class="ui-actions">${button('Save link','type="submit"')}${r.saved?`<a class="ui-button" href="${esc(r.saved)}" target="_blank" rel="noopener">Open explorer ↗</a>`:''}</div></form>`}
    ],providers.map(([id,title,text,url])=>{const saved=safeURL(links()[id]);return {id,title,text,url,saved,status:saved?'Explorer link saved':'Not configured'};}),null)}<p class="section-note">Catalog reviewed 12 November 2026. Deployment, security review, and any managed plan selection are separate setup work.</p></section>`;
  }
  root.innerHTML=html;mountTableMenus();
  root.querySelector('[data-work-search]').onsubmit=e=>{e.preventDefault();prefs.query=new FormData(e.currentTarget).get('query').trim();prefs.offset=0;save();onRefresh();};
  root.querySelector('[data-work-reset]').onclick=()=>{prefs.query='';prefs.status='';prefs.task_type='';prefs.offset=0;save();onProject('');};
  root.querySelectorAll('[data-work-filter]').forEach(el=>el.onchange=()=>{if(el.dataset.workFilter==='project'){prefs.offset=0;save();return onProject(el.value);}prefs.offset=0;prefs[el.dataset.workFilter]=el.value;save();onRefresh();});
  root.querySelectorAll('[data-work-page]').forEach(b=>b.onclick=()=>{prefs.offset=Number(b.dataset.workPage);save();onRefresh();});
  root.onclick=async event=>{
    const target=event.target.closest('[data-work-task],[data-knowledge-step],[data-discover-tasks]');if(!target)return;
    try{
      if(target.hasAttribute('data-work-task'))return onTask(target.dataset.workTask);
      if(target.hasAttribute('data-discover-tasks')){target.disabled=true;await post('task-discovery',{enabled:true});return onRefresh();}
      const response=await fetch('/api/task-step-evidence?'+new URLSearchParams({id:target.dataset.knowledgeStep}));
      const value=await response.json();if(!response.ok)throw Error(value.error||'Evidence unavailable');
      onInspect('Retained source evidence',`<pre>${esc(JSON.stringify(value,null,2))}</pre>`);
    }catch(error){onError(error.message);}
  };
  root.onsubmit=event=>{
    const form=event.target.closest('[data-explorer-link]');if(!form)return;event.preventDefault();
    const value=new FormData(form).get('url').trim(),url=safeURL(value);
    if(value&&!url)return onError('Use an HTTP(S) explorer URL without credentials.');
    try{const saved=links();if(url)saved[form.dataset.explorerLink]=url;else delete saved[form.dataset.explorerLink];localStorage.setItem('ttgl-knowledge-explorers',JSON.stringify(saved));onRefresh();}catch(error){onError(error.message);}
  };
  if(view!=='tasks'||!taskId)return;
  const detail=root.querySelector('[data-work-detail]');
  try{
    const response=await fetch('/api/work-task?'+new URLSearchParams({task_id:taskId,attribution:prefs.attribution}));const t=await response.json();if(!response.ok)throw Error(t.error);if(root._workToken!==token)return;
    let selected=selectedSubtasks.get(t.id)||'';
    if(!t.subtasks.some(s=>s.id===selected)){selected='';selectedSubtasks.delete(t.id);}
    const show=()=>{
      const sub=t.subtasks.find(s=>s.id===selected),active=t.jobs.find(j=>['queued','running'].includes(j.status));
      detail.innerHTML=`<div class="work-breadcrumb">${button('All tasks','data-all-tasks')}<span>/</span><strong>${esc(t.title)}</strong>${sub?`<span>/</span><span>${esc(sub.title)}</span>`:''}</div><article class="task-detail"><div class="card-eyebrow">${badge(t.status)}${badge(t.type)}${t.analysis_stale?badge('Interpretation needs refresh'):''}</div><div class="detail-heading"><h2>${esc(t.title)}</h2><div class="ui-actions">${button(active?'Luna is mining…':'Mine with Luna',`data-mine-task data-mining-active="${Boolean(active)}" ${active||!t.metrics.steps?'disabled':''}`,true)}${button('Task details','data-task-information')}</div></div><p class="work-summary">${esc(t.summary||t.goal||'No interpretation yet.')}</p>${stats(t.metrics,false,unit)}<p class="section-note">${n(t.metrics.timed_steps)} / ${n(t.metrics.steps)} steps have recorded operation runtimes. Identified service lifetime: ${duration(t.metrics.background_seconds)} (separate). ${n(t.metrics.unreviewed_steps)} runtime roles are unreviewed. Model totals belong to the task; tool runtimes may overlap.</p>${t.analysis_derivation?`<p class="section-note">Evidence-backed groups were derived from the retained model output. Proposals with no source steps were omitted; the original attempt and validation result remain recorded.</p>`:''}${t.jobs[0]?`<p class="section-note" role="status">Latest ${esc(t.jobs[0].operation)}: ${esc(t.jobs[0].status)}${t.jobs[0].error?' · '+esc(t.jobs[0].error):''}. Mining is separate overhead: ${n(t.mining_overhead_tokens)} known tokens.</p>`:''}</article><div class="work-hierarchy"><section class="subtask-panel"><div class="section-heading"><h2>Subtasks <span class="muted">${n(t.subtasks.length)}</span></h2>${selected?button('All steps','data-all-steps'):''}</div><p class="section-note">Native turn counters are measured. Semantic subtask allocation is optional and estimated; each tool step is counted once.</p><div class="chart-controls">${select('attribution','Subtask token attribution',[['measured','Measured turn counters only'],['step_share','Estimate semantic subtask shares']],prefs.attribution)}</div>${table('work-subtasks',[
        {key:'title',label:'Subtask / recorded turn',cell:r=>`<button class="inline-link table-prose" data-subtask="${esc(r.id)}" aria-pressed="${r.id===selected}">${esc(r.title)}</button>`},
        {key:'type',label:'Type'},
        {key:'source',label:'Interpretation',cell:r=>badge(r.source==='model'?'Luna':r.source==='user'?'Human':'Native log')},
        ...usageColumns(unit),
        {key:'usage_basis',label:'Token attribution',cell:r=>esc(r.usage_basis==='native_turn'?'Measured turn':r.usage_basis==='step_share'?'Estimated step share':'Unattributed')},
        {key:'summary',hiddenByDefault:true,label:'Summary',cell:r=>`<span class="table-prose">${esc(r.summary)}</span>`}
      ],t.subtasks,null)}</section><details class="step-panel" ${selected?'open':''}><summary>${sub?esc(sub.title):'Explore all source steps and model responses'}</summary>${sub?`<p>${esc(sub.summary)}</p>${stats(sub.metrics,prefs.attribution==='step_share',unit)}`:''}<div data-work-timeline></div><section class="section"><h3>Steps and model responses</h3><p class="section-note">Response tokens are measured on model rows. Tool rows have no native token attribution.</p><div data-work-steps></div></section></details></div>${t.knowledge.length?`<section class="section"><h2>Knowledge candidates</h2>${knowledgeTable(table,'task-knowledge',t.knowledge)}</section>`:''}`;
      detail.querySelector('[data-work-filter="attribution"]').onchange=e=>{prefs.attribution=e.target.value;save();onRefresh();};
      detail.querySelector('[data-all-tasks]').onclick=()=>onTask('');
      detail.querySelector('[data-task-information]').onclick=()=>onInspect(null,null,t.id);
      detail.querySelector('[data-mine-task]').onclick=async e=>{e.currentTarget.disabled=true;try{await post('analyze-task',{task_id:t.id,operation:'overview'});onRefresh();}catch(error){onError(error.message);e.target.disabled=false;}};
      detail.onclick=event=>{const b=event.target.closest('[data-subtask]');if(!b)return;selected=selected===b.dataset.subtask?'':b.dataset.subtask;selectedSubtasks.set(t.id,selected);show();};
      const all=detail.querySelector('[data-all-steps]');if(all)all.onclick=()=>{selected='';selectedSubtasks.delete(t.id);show();};
      renderStepTimeline(detail.querySelector('[data-work-timeline]'),{taskId:t.id,subtaskId:selected||null,onGrouped:onRefresh,onError});mountTableMenus();
      renderSteps(detail.querySelector('[data-work-steps]'),selected);
    };
    const renderSteps=async(target,subtaskId,offset=0)=>{
      try{
        const r=await fetch('/api/work-steps?'+new URLSearchParams({task_id:t.id,...(subtaskId?{subtask_id:subtaskId}:{}),limit:100,offset}));
        const result=await r.json();if(!r.ok)throw Error(result.error);if(!target.isConnected)return;
        target.innerHTML=table('work-steps',[
          {key:'sequence',label:'Sequence',numeric:true},
          {key:'name',label:'Step',cell:r=>button(r.name,`data-knowledge-step="${esc(r.id)}"`)},
          {key:'kind',label:'Kind'},
          {key:'timestamp',label:'Recorded time',cell:r=>esc(r.timestamp?.slice(0,23).replace('T',' '))},
          {key:'runtime',label:'Duration',numeric:true,cell:r=>duration(r.runtime)},
          {key:'model',hiddenByDefault:true,label:'Model'},
          {key:'tokens',label:'Response tokens',numeric:true,cell:r=>r.kind==='tool'?'Not attributed':n(r.tokens)},
          {key:'cost',label:'API token estimate',numeric:true,cell:r=>r.kind==='tool'?'Not attributed':r.cost==null?'No matched rate':price(r.cost)+' '+unit}
        ],result.items,null)+`<div class="pagination"><span>Records ${result.total?offset+1:0}–${Math.min(offset+result.items.length,result.total)} of ${result.total}</span>${offset?button('Previous records','data-records-prev'):''}${result.next_offset!=null?button('Next records','data-records-next'):''}</div>`;
        const prev=target.querySelector('[data-records-prev]'),next=target.querySelector('[data-records-next]');
        if(prev)prev.onclick=()=>renderSteps(target,subtaskId,Math.max(0,offset-100));if(next)next.onclick=()=>renderSteps(target,subtaskId,result.next_offset);
        mountTableMenus();
      }catch(error){if(target.isConnected)target.innerHTML=emptyState('Steps unavailable',error.message);onError(error.message);}
    };show();
  }catch(error){if(root._workToken===token)detail.innerHTML=emptyState('Task unavailable',error.message,button('All tasks','data-work-task=""'));onError(error.message);}
}
