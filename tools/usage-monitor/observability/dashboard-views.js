import {chartTones} from '/chart-theme.js';
import {sourceList,selectionColumn,selectedIds,clearSelection} from '/data-list.js';
import {button,badge,escapeHTML as esc,emptyState} from '/ui.js';
import {filters} from '/optimization.js';
import {usageChart} from '/usage-views.js';
const n=v=>v==null?'Unknown':Number(v).toLocaleString('en',{maximumFractionDigits:3});
const money=(v,u)=>v==null?'Unknown':Number(v).toLocaleString('en',{maximumFractionDigits:Math.abs(v)<.01?6:3})+' '+u;
const pct=v=>v==null?'Unknown':n(v*100)+'%';
const duration=v=>v==null?'Unknown':v>=3600?n(v/3600)+' h':v>=60?n(v/60)+' min':n(v)+' s';
const label=v=>String(v||'unknown').replaceAll('_',' ');
const colors=chartTones;
const section=(title,body,action='')=>`<section class="section ops-card"><div class="section-heading"><h2>${esc(title)}</h2>${action}</div>${body}</section>`;
const link=(title,view)=>button(title,`data-dash-view="${view}"`);
function kpis(items){return `<div class="work-metrics ops-kpis usage-kpis">${items.map(([title,value,note,view])=>`<div>${view?`<button class="dashboard-kpi-link" data-dash-view="${view}">`:''}<small>${esc(title)}</small><strong>${esc(value)}</strong>${view?'</button>':''}<span class="muted">${esc(note||'')}</span></div>`).join('')}</div>`;}
function turnTable(table,rows,data,id='activity-turns',options={}){
 return table(id,[
  {key:'title',label:'Task / native turn',cell:r=>button(r.title,`data-dash-turn="${r.id}"`)},
  {key:'started',label:'Started',numeric:true,cell:r=>r.started==null?'Unknown':esc(new Date(r.started*1000).toLocaleString())},
  {key:'cost',label:'API estimate',numeric:true,value:r=>r.metrics.cost,cell:r=>money(r.metrics.cost,data.unit)},
  {key:'tokens',label:'Tokens',numeric:true,value:r=>r.metrics.tokens,cell:r=>n(r.metrics.tokens)},
  {key:'span',label:'Observed span',numeric:true,cell:r=>duration(r.span)+(r.clipped?' · clipped':'')},
  {key:'responses',label:'API responses',numeric:true,value:r=>r.metrics.responses},
  {key:'tools',label:'Tools',numeric:true,value:r=>r.metrics.tool_calls},
  {key:'errors',label:'Nonzero / errors',numeric:true,value:r=>r.metrics.errors},
  {key:'outcome',label:'Assigned task outcome',cell:r=>r.outcome==='needed_fix'?badge('Needed a fix'):r.outcome==='warning'?badge('Warning signs'):'Unknown'},
  {key:'loops',label:'Loops',numeric:true},{key:'models',label:'Models',value:r=>r.models.join(', ')},
  {key:'interpretation',label:'Interpretation',cell:r=>badge(label(r.interpretation))},
  {key:'subtasks',label:'Subtasks',numeric:true,hiddenByDefault:true},
  {key:'categories',label:'Categories',value:r=>r.categories.join(', '),hiddenByDefault:true},
  {key:'workspace',label:'Workspace',hiddenByDefault:true},{key:'session_id',label:'Session',hiddenByDefault:true},
  {key:'agents',label:'Agents',value:r=>r.agents.join(', '),hiddenByDefault:true},
  {key:'output',label:'Output tokens',numeric:true,value:r=>r.metrics.output,hiddenByDefault:true},
  {key:'source_state',label:'Source availability',hiddenByDefault:true}
 ],rows,null,true,options);
}
function markedTable(table,data,options={}){return table('marked-tasks',[
 {key:'title',label:'Defined task',cell:r=>button(r.title,`data-dash-task="${esc(r.id)}"`)},
 {key:'categories',label:'Categories',value:r=>r.categories.join(', ')},
 {key:'status',label:'Status',cell:r=>badge(r.status)},
 {key:'started',label:'Started',numeric:true,cell:r=>r.started==null?'Unknown':esc(new Date(r.started*1000).toLocaleString())},
 {key:'span_sum',label:'Sum of turn spans',numeric:true,cell:r=>duration(r.span_sum)},
 {key:'turns',label:'Turns',numeric:true},
 {key:'responses',label:'API responses',numeric:true,value:r=>r.metrics.responses},
 {key:'tools',label:'Tool calls',numeric:true,value:r=>r.metrics.tool_calls},
 {key:'tokens',label:'Tokens',numeric:true,value:r=>r.metrics.tokens,cell:r=>n(r.metrics.tokens)},
 {key:'cost',label:'API estimate',numeric:true,value:r=>r.metrics.cost,cell:r=>money(r.metrics.cost,data.unit)}
 ],data.marked_tasks,null,true,options);}
function toolTable(table,rows,data,id='dashboard-tools'){return table(id,[
 {key:'name',label:'Tool',cell:r=>button(r.name,`data-dash-tool="${esc(r.name)}"`)},
 {key:'calls',label:'Calls',numeric:true},{key:'runtime',label:'Recorded time',numeric:true,cell:r=>r.runtime==null?(r.known_runtime?'≥ '+duration(r.known_runtime)+' known':'Unknown'):duration(r.runtime)},
 {key:'failed',label:'Failed',numeric:true}
 ],rows,null);}
let modalController;
export function renderDashboard(root,{view,data,state,table,post,showModal,inspect,onFilters,onNavigate,onError}){
 let html=filters(data,state).replace('</form>',`<label>Display timezone<select class="ui-input" name="zone" aria-label="Display timezone">${[...new Set([data.timezone,'UTC','Europe/Amsterdam'])].map(z=>`<option value="${esc(z)}" ${z===data.timezone?'selected':''}>${esc(z)}</option>`).join('')}</select></label></form>`);
 const stats=data.statistics;let modalTurns=[];
 const remote=(page,key)=>page?{serverPage:{...page,onPage:(offset,limit)=>onFilters({[key]:offset,limit})}}:{};
 if(view==='taskactivity'){
  html+=kpis([['Native turns',n(data.counts.turns),n(data.counts.prompts)+' retained prompts'],['Average API estimate',money(stats.cost.mean,data.unit),'Median '+money(stats.cost.median,data.unit)+' · '+stats.cost.known+'/'+stats.cost.total+' priced turns'],['90th percentile cost',money(stats.cost.p90,data.unit),'Known turn estimates only'],['Average observed span',duration(stats.duration.mean),'Median '+duration(stats.duration.median)+' · '+stats.duration.known+'/'+stats.duration.total+' known spans'],['90th percentile span',duration(stats.duration.p90),'Elapsed spans include idle gaps'],['Average tool calls',n(stats.tool_calls.mean),'Recorded per selected turn']]);
  html+=section('Interpreted turns',`<strong class="coverage-total">${data.interpreted_turns} / ${data.counts.turns}</strong><p>${data.complete_turns} turns have complete source-event coverage · ${pct(data.interpreted_spend_share)} of scenario spend belongs to interpreted turns.</p><div class="coverage-strip">${Object.entries(data.coverage).map(([key,count],i)=>`<span style="flex:${count};background:${({interpreted:colors[0],pending:colors[1],unclassified:colors[4],stale:colors[2],no_activity:colors[5]})[key]||colors[i%colors.length]}" title="${esc(label(key))}: ${count}"></span>`).join('')}</div><p>${Object.entries(data.coverage).map(([key,count])=>esc(label(key))+' '+count).join(' · ')}</p><p class="section-note">Turn source availability: ${Object.entries(data.source_coverage).map(([key,count])=>esc(label(key))+' '+count).join(' · ')||'No retained turns'}. Absence does not establish deletion. Pending refreshes can retain current interpreted groups. No analysis starts automatically.</p>`,button('Review remaining tasks',`data-dash-review ${data.eligible.length?'':'disabled'}`));
  html+=section('All marked tasks',`<p class="section-note">Explicit defined tasks only. Provisional discovery and model-proposed boundaries are separate. Turn spans may overlap; they are not active time.</p>`+markedTable(table,data,remote(data.task_pagination,'task_offset')));
  html+=section('Tasks',`<p class="section-note">One row per native session/turn, including unassigned turns and separately recorded subagent turns. Defined task assignments are preserved. Outcome labels belong to the assigned task, not independently to this turn.</p>`+turnTable(table,data.turns,data,'activity-turns',remote(data.turn_pagination,'turn_offset')));
 }else{
  const m=data.metrics,knownTime=data.time_by_role.reduce((sum,r)=>sum+(r.known_runtime||0),0);
  html+=kpis([['API token estimate',money(m.cost,data.unit),'Known priced portion '+money(m.known_cost,data.unit),'costs'],['Native turns',n(data.counts.turns),`${data.counts.prompts} prompts · ${data.counts.sessions} sessions · ${data.counts.defined_tasks} assigned defined tasks`,'taskactivity'],['Known recorded time',duration(knownTime),'Sum of recorded runtimes; overlaps and missing timing remain','timeline'],['Tool calls',n(m.tool_calls),n(m.errors)+' nonzero/error outcomes · '+m.responses+' model responses','tools'],['Cache hit rate',pct(data.cache_hit_rate),'Cache-read tokens / native input tokens','costs'],['Needed a fix',pct(data.outcomes.fix_rate),data.outcomes.needed_fix+' confirmed / '+data.outcomes.tasks+' assigned tasks','outcomes']]);
  const maxRole=Math.max(0,...data.time_by_role.map(r=>r.known_runtime));
  html+=`<div class="analysis-pair">${section('Cost per day',usageChart(data.days,[['API estimate','cost']],'Daily API estimates'),link('Cost & tokens →','costs'))}${section('Time by activity',`<p class="section-note">Recorded model and tool runtime by reviewed runtime role. Tool durations can overlap. Background service lifetime is excluded. Unknown timing is not zero.</p><div class="category-bars">${data.time_by_role.map((r,i)=>`<button data-dash-role="${i}"><span>${esc(label(r.name))}</span><span class="category-track"><span style="width:${maxRole?r.known_runtime/maxRole*100:0}%;background:${colors[i%colors.length]}"></span></span><strong>${r.runtime==null?(r.known_runtime?'≥ '+duration(r.known_runtime):'Unknown'):duration(r.runtime)}</strong></button>`).join('')}</div>`,link('Tool usage →','tools'))}</div>`;
  html+=`<div class="analysis-pair">${section('Top tools',`<p class="section-note">${data.top_tools.length} of ${data.tool_count}, ranked by known operation time. Select a tool to inspect its actions and targets.</p>`+toolTable(table,data.top_tools,data),link('Tool usage →','tools'))}${section('Top categories',`<p class="section-note">${data.top_categories.length} of ${data.category_count}. Categories use existing agent annotations or fallback name rules.</p>`+table('dashboard-categories',[{key:'name',label:'Category',cell:r=>button(r.name,`data-dash-category="${esc(r.name)}"`)},{key:'calls',label:'Calls',numeric:true},{key:'runtime',label:'Recorded time',numeric:true,cell:r=>r.runtime==null?(r.known_runtime?'≥ '+duration(r.known_runtime):'Unknown'):duration(r.runtime)},{key:'context_cost',label:'Context cost',numeric:true,cell:()=> 'Unknown'}],data.top_categories,null))}</div>`;
  html+=`<div class="analysis-pair">${section('Outcomes',`<dl class="report-story"><dt>Needed a fix</dt><dd>${data.outcomes.needed_fix} confirmed task interventions · ${data.outcomes.warnings} assigned tasks with warning signs</dd><dt>Got stuck</dt><dd>${data.outcomes.stuck} assigned tasks with retained loop patterns</dd><dt>Commits / PRs</dt><dd>${data.outcomes.commits} retained references; remote state unverified</dd></dl>`,link('Outcomes →','outcomes'))}${section('Top suggestions',table('dashboard-findings',[{key:'title',label:'Finding'},{key:'action',label:'Recommended action',cell:f=>`<span class="table-prose">${esc(f.action)}</span>`},{key:'count',label:'Matching records',numeric:true},{key:'affected_cost',label:'Affected API estimate',numeric:true,cell:f=>money(f.affected_cost,data.unit)},{key:'evidence',label:'Evidence',cell:f=>button('Inspect finding',`data-dash-finding="${f.id}"`)}],data.findings,null),link('Suggestions →','suggestions'))}</div>`;
 }
 html+=section('Counting and coverage',`<ul>${data.limits.map(s=>`<li>${esc(s)}</li>`).join('')}</ul>`);
 root.innerHTML=html;
 root.querySelector('[data-ops-filters]').onsubmit=e=>{e.preventDefault();onFilters(Object.fromEntries(new FormData(e.currentTarget)));};
 const sources=(item,title,note='')=>showModal(title,`<p>${esc(note)}</p><p>${item.event_ids.length} of ${item.event_count??item.evidence_total} source records listed.</p><div class="ui-actions">${sourceList('dashboard-source-records',item.event_ids,'data-dash-source')}</div><div data-dash-output></div>`);
 const handler=async e=>{const b=e.target.closest('[data-dash-view],[data-dash-turn],[data-dash-task],[data-dash-tool],[data-dash-category],[data-dash-role],[data-dash-finding],[data-usage-day],[data-dash-source],[data-dash-review]');if(!b)return;try{
  if(b.dataset.dashView)return onNavigate(b.dataset.dashView);
  if(b.dataset.dashTask){document.querySelector('#modal').close();return onFilters({task:b.dataset.dashTask});}
  if(b.dataset.dashSource)return inspect(b.dataset.dashSource,document.querySelector('[data-dash-output]'));
  if(b.dataset.dashTurn){const t=data.turns.find(t=>t.id===b.dataset.dashTurn)||modalTurns.find(t=>t.id===b.dataset.dashTurn);if(!t)return;showModal(t.title,'<p>Loading retained request…</p>');const response=await fetch('/api/activity-turn?'+new URLSearchParams({session:t.session_id,turn:t.turn_id}));const detail=await response.json();if(!response.ok)throw Error(detail.error||'Turn unavailable');showModal(t.title,`<p>${esc(detail.prompt||'No prompt retained')}</p><p>${n(t.metrics.responses)} model responses · ${n(t.metrics.tool_calls)} tools · ${money(t.metrics.cost,data.unit)} · ${duration(t.span)} observed span.</p><p>${esc(t.outcome_basis)}</p>${t.task_id?button('Open defined task',`data-dash-task="${esc(t.task_id)}"`):'<p>Unassigned turn. Assign it through the existing inbox or work tools.</p>'}<p>${t.event_ids.length} of ${t.event_count} source records listed.</p><div class="ui-actions">${sourceList('dashboard-turn-sources',t.event_ids,'data-dash-source')}</div><div data-dash-output></div>`);return;}
  if(b.dataset.dashTool){const tool=data.tools.find(t=>t.name===b.dataset.dashTool);return onNavigate('tools',{family:tool.family,action:tool.action});}
  if(b.dataset.dashCategory){const tools=data.top_categories.find(c=>c.name===b.dataset.dashCategory).tools;return showModal(b.dataset.dashCategory,toolTable(table,tools,data,'dashboard-category-tools'));}
  if(b.dataset.dashRole!=null)return sources(data.time_by_role[Number(b.dataset.dashRole)],'Recorded runtime evidence');
  if(b.dataset.dashFinding){const f=data.findings.find(f=>f.id===b.dataset.dashFinding);return sources({...f,event_ids:f.evidence_ids},f.title,f.action);}
  if(b.dataset.usageDay!=null){const day=data.days[Number(b.dataset.usageDay)];const showDay=async(offset=0,limit=20)=>{showModal(day.date+' turns','<p>Loading turns…</p>');const response=await fetch('/api/activity-dashboard?'+new URLSearchParams({...state,view:'taskactivity',day:day.date,turn_offset:offset,limit}));const result=await response.json();if(!response.ok)throw Error(result.error||'Turns unavailable');modalTurns=result.turns;showModal(day.date+' turns',turnTable(table,result.turns,result,'dashboard-day-turns',{serverPage:{...result.turn_pagination,onPage:showDay}}));};return showDay();}
  if(b.hasAttribute('data-dash-review')){const choices=data.eligible;clearSelection('dashboard-analysis-selection');showModal('Analyze selected tasks',`<p>Choose one or two defined tasks. This explicitly starts the existing small-model analysis and accounts for its overhead separately.</p><p>${choices.length} of ${data.eligible_count??data.eligible.length} eligible tasks shown. Narrow the scope if necessary.</p><form data-dash-analyze>${table('dashboard-analysis-selection',[selectionColumn('dashboard-analysis-selection',{name:'task_id',limit:2}),{key:'title',label:'Task'},{key:'source_state',label:'Source availability'}],choices,null)}${button('Analyze selected tasks','type="submit"')}<p data-dash-analysis-result role="status"></p></form>`);document.querySelector('[data-dash-analyze]').onsubmit=async ev=>{ev.preventDefault();const form=ev.currentTarget,ids=selectedIds('dashboard-analysis-selection'),output=form.querySelector('[data-dash-analysis-result]');if(ids.length<1||ids.length>2){output.textContent='Select one or two tasks.';return;}form.querySelector('button[type="submit"]').disabled=true;try{const result=await post('analyze-process-tasks',{task_ids:ids});output.textContent=result.jobs.map(j=>(choices.find(t=>t.id===j.task_id)?.title||'Task')+': '+j.status+(j.error?' · '+j.error:'')).join('\n');}catch(error){output.textContent=error.message;form.querySelector('button[type="submit"]').disabled=false;}};}
 }catch(error){onError(error.message);}};
 root.onclick=handler;modalController?.abort();modalController=new AbortController();document.querySelector('#modal').addEventListener('click',handler,{signal:modalController.signal});
 root.onkeydown=e=>{if(e.target.matches('g[role="button"]')&&['Enter',' '].includes(e.key)){e.preventDefault();e.target.dispatchEvent(new MouseEvent('click',{bubbles:true}));}};
}
