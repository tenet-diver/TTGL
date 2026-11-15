import {renderList} from '/data-list.js';
import { renderStepTimeline } from '/step-timeline.js';
import { button, badge, emptyState } from '/ui.js';
const esc = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
let searchState={query:'',status:'',activity:'',mode:'keyword',offset:0};
let modalEpoch=0;
async function api(path,body) {
  const response=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:undefined);
  const value=await response.json();if(!response.ok)throw new Error(value.error||'Request failed');return value;
}
export function renderHistory(root,{project,open,onError}) {
  root.innerHTML=`<section class="section"><h2>Search past work</h2><p class="section-note">Find a task, understand its subtasks, then inspect the original steps. Interpretations include evidence and confidence.</p>
  <form id="history-search" class="history-search"><label>Search tasks and subtasks<input class="ui-input" name="query" type="search" value="${esc(searchState.query)}" placeholder="e.g. database migration, flaky test, PR URL"></label>
  <label>Task status<select class="ui-input" name="status"><option value="">All statuses</option>${['completed','active','waiting','cancelled','unresolved'].map(s=>`<option ${searchState.status===s?'selected':''}>${s}</option>`).join('')}</select></label>
  <label>Activity<select class="ui-input" name="activity"><option value="">All activities</option>${['investigate','plan','implement','test','review','document','operate','other'].map(s=>`<option ${searchState.activity===s?'selected':''}>${s}</option>`).join('')}</select></label>
  <label>Search method<select class="ui-input" name="mode"><option value="keyword" ${searchState.mode==='keyword'?'selected':''}>Keyword</option><option value="semantic" ${searchState.mode==='semantic'?'selected':''}>Semantic · local embeddings</option></select></label>${button('Search','type="submit"')}</form>
  <p id="history-status" role="status"></p><div id="history-results"></div><div class="modal-actions" id="history-pages"></div></section>`;
  let epoch=0;
  const load=async()=>{
    const version=++epoch;root.querySelector('#history-status').textContent='Searching…';
    try {
      const q=new URLSearchParams({...searchState,limit:'all',offset:0});if(project)q.set('project',project);
      const result=await (searchState.mode==='semantic'?api('/api/search-task-history',Object.fromEntries(q)):api('/api/task-history?'+q));if(version!==epoch||!root.isConnected)return;
      root.querySelector('#history-status').textContent=`${result.total??0} matching tasks · ${result.mode} search`;
      root.querySelector('#history-results').innerHTML=renderList('history-results',[
        {key:'title',label:'Task',cell:t=>button(t.title,`data-history-task="${esc(t.task_id)}"`)},{key:'status',label:'Status',cell:t=>badge(t.status)},{key:'summary',label:'Summary'},{key:'similarity',label:'Similarity',numeric:true},{key:'manual_subtask_count',label:'Collected subtasks',numeric:true}
      ],result.items,null);
      root.querySelector('#history-results').onclick=e=>{const b=e.target.closest('[data-history-task]');if(b){e.stopPropagation();open(b.dataset.historyTask);}};
      root.querySelector('#history-pages').innerHTML='';
    } catch(error) {if(version===epoch)root.querySelector('#history-status').textContent=error.message;}
  };
  root.querySelector('form').onsubmit=e=>{e.preventDefault();searchState={...Object.fromEntries(new FormData(e.currentTarget)),offset:0};load();};
  load();
}
export async function openTaskHistory(taskId,showModal,onTaskChanged=()=>{}) {
  const epoch=++modalEpoch;
  showModal('Task history',`<span data-history-owner="${epoch}" hidden></span><p role="status">Loading task and subtasks…</p>`);
  try {
    const data=await api('/api/task-history-detail?'+new URLSearchParams({task_id:taskId}));
    if(epoch!==modalEpoch||!document.querySelector(`[data-history-owner="${epoch}"]`)||!document.querySelector('#modal')?.open)return;
    const job=data.jobs[0];if(job?.operation==='title'&&job.status==='completed')onTaskChanged();const active=job&&['queued','running'].includes(job.status);
    const groups=renderList('history-subtasks',[
      {key:'title',label:'Subtask',cell:s=>`<details class="history-subtask" data-subtask="${esc(s.id)}"><summary>${badge(s.activity)} <strong>${esc(s.title)}</strong> <small>${s.step_count} steps</small> ${badge(s.source==='user'?'Collected · unverified':'Model suggestion')}</summary><p>${esc(s.summary)}</p><p>${s.source==='user'?'User-collected · outcome unverified'+(s.stale?' · Source evidence changed':''):s.tags.map(esc).join(' · ')+' · '+Math.round(s.confidence*100)+'% interpretation confidence'}</p><div data-step-list></div></details>`},
      {key:'activity',label:'Activity'},{key:'step_count',label:'Steps',numeric:true},{key:'source',label:'Source',value:s=>s.source==='user'?'Collected':'Model interpretation'}
    ],[...(data.manual_subtasks||[]),...data.subtasks],null,true,{onMount:node=>node.querySelectorAll('[data-subtask]').forEach(el=>el.ontoggle=()=>{if(el.open&&!el.dataset.loaded){el.dataset.loaded='true';loadSteps(el);}})});
    showModal(data.task.title,`<span data-history-owner="${epoch}" hidden></span><div class="history-breadcrumb">Task → Subtasks → Source steps</div><p>${badge(data.task.status)}</p><p>${esc(data.task.goal)}</p><details class="task-prompt"><summary>Original user request · name source: ${esc(data.title_provenance?.source||'user')}</summary><p>${esc(data.user_prompt||data.task.goal)}</p></details><div class="ui-actions task-name-actions">${button('Name from user prompt','data-prompt-name')}${button('Format name with Luna',`data-format-name ${active?'disabled':''}`)}</div><p>${esc(data.task.outcome||'Task outcome has not been verified.')}</p>${(data.related_prs||[]).length?'<p>Referenced PRs: '+data.related_prs.map(url=>`<a href="${esc(url)}" target="_blank" rel="noopener">${esc(url)}</a>`).join(' · ')+'</p>':''}<div class="modal-actions">${button(data.analysis?'Analyze new steps':'Analyze into subtasks',`data-start-analysis ${active?'disabled':''}`)}</div><p class="section-note">On demand · small-model interpretation · ${data.step_count} collected steps. Source measurements stay unchanged.</p>
      ${job?`<p role="status">${job.operation==='title'?'Name formatting':'Subtask analysis'}: ${esc(job.status)} · ${esc(job.model)}${job.error?' — '+esc(job.error):''}</p><p class="section-note">Analysis overhead: ${job.usage?esc(job.usage.total_tokens??'Unknown')+' recorded tokens':'unknown or not yet reported'}. Separate from source task measurements.</p>`:''}
      ${data.jobs.length?`<details><summary>Naming and analysis attempts (${data.jobs.length} most recent)</summary>${renderList('history-attempts',[{key:'operation',label:'Operation'},{key:'status',label:'Status'},{key:'model',label:'Model'},{key:'tokens',label:'Tokens',numeric:true,value:j=>j.usage?.total_tokens},{key:'error',label:'Error'}],data.jobs,null)}</details>`:''}
      ${data.stale?'<div class="notice">New or reassigned evidence exists. This interpretation is stale; analyze the current steps to update it.</div>':''}
      <div data-task-timeline></div><p class="section-note">Collected groups and model suggestions are separate interpretations; a source step may appear in both.</p>${data.analysis?`<p>${esc(data.analysis.summary)}</p><small>Version ${esc(data.analysis.id.slice(0,8))} · ${esc(data.analysis.model)}</small>`:''}${groups||'<div class="table-empty">No subtasks yet. Select steps above or ask Luna to organize the task.</div>'}`);
    renderStepTimeline(document.querySelector('[data-task-timeline]'),{taskId,onGrouped:async()=>{await onTaskChanged();await openTaskHistory(taskId,showModal,onTaskChanged);}});
    document.querySelector('[data-prompt-name]').onclick=async e=>{
      e.currentTarget.disabled=true;
      try{await api('/api/task_name',{id:taskId});await onTaskChanged();await openTaskHistory(taskId,showModal,onTaskChanged);}
      catch(error){showModal('Task name could not update',`<p role="alert">${esc(error.message)}</p>`);}
    };
    document.querySelector('[data-format-name]').onclick=async e=>{
      e.currentTarget.disabled=true;
      try{await api('/api/analyze-task',{task_id:taskId,operation:'title'});await openTaskHistory(taskId,showModal,onTaskChanged);}
      catch(error){showModal('Name formatting could not start',`<p role="alert">${esc(error.message)}</p>`);}
    };
    document.querySelector('[data-start-analysis]').onclick=async e=>{
      e.currentTarget.disabled=true;
      try{await api('/api/analyze-task',{task_id:taskId});await openTaskHistory(taskId,showModal,onTaskChanged);}
      catch(error){showModal('Analysis could not start',`<p role="alert">${esc(error.message)}</p>`);}
    };
    const loadSteps=async(node,offset=0)=>{
      const target=node.querySelector('[data-step-list]');target.textContent='Loading source steps…';
      try{
        const detail=await api('/api/task-history-detail?'+new URLSearchParams({task_id:taskId,subtask_id:node.dataset.subtask,limit:'all',offset:0}));
        target.innerHTML=renderList('history-steps-'+node.dataset.subtask,[{key:'name',label:'Source step',cell:s=>button(s.name,`data-history-evidence="${esc(s.id)}"`)},{key:'ts',label:'Time'},{key:'runtime',label:'Runtime',numeric:true},{key:'failed',label:'Nonzero / failed',numeric:true}],detail.steps,null)+'<div data-source-output></div>';
        target.onclick=async e=>{const b=e.target.closest('[data-history-evidence]');if(!b)return;const output=target.querySelector('[data-source-output]');output.textContent='Loading retained evidence…';try{const r=await api('/api/task-step-evidence?'+new URLSearchParams({id:b.dataset.historyEvidence}));output.innerHTML='<h4>Retained source evidence</h4><pre>'+esc(JSON.stringify(r,null,2))+'</pre>';}catch(error){output.textContent=error.message;}};
      }catch(error){target.textContent=error.message;}
    };
    document.querySelectorAll('[data-subtask]').forEach(node=>node.ontoggle=()=>{if(node.open&&!node.dataset.loaded){node.dataset.loaded='true';loadSteps(node);}});
    if(active) {
      const poll=()=>{if(epoch!==modalEpoch||!document.querySelector(`[data-history-owner="${epoch}"]`)||!document.querySelector('#modal')?.open)return;
        if(document.querySelector('[data-step-select]:checked,[data-task-timeline][data-selected-steps]:not([data-selected-steps="0"])')||document.activeElement?.closest('.timeline-collect-form'))setTimeout(poll,2500);
        else openTaskHistory(taskId,showModal,onTaskChanged);
      };setTimeout(poll,2500);
    }
  }catch(error){if(epoch===modalEpoch&&document.querySelector(`[data-history-owner="${epoch}"]`))showModal('Task history unavailable',`<p role="alert">${esc(error.message)}</p>`);}
}
