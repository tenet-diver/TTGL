const esc = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const button = (label, attrs='') => `<button class="evlv-button evlv-secondary evlv-compact" ${attrs}>${esc(label)}</button>`;
let searchState={query:'',status:'',activity:'',mode:'keyword',offset:0};
let modalEpoch=0;
async function api(path,body) {
  const response=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:undefined);
  const value=await response.json();if(!response.ok)throw new Error(value.error||'Request failed');return value;
}
export function renderHistory(root,{project,open,onError}) {
  root.innerHTML=`<section class="section"><h2>Search past work</h2><p class="section-note">Find a task, understand its subtasks, then inspect the original steps. Interpretations include evidence and confidence.</p>
  <form id="history-search" class="history-search"><label>Search tasks and subtasks<input class="evlv-input" name="query" type="search" value="${esc(searchState.query)}" placeholder="e.g. database migration, flaky test, PR URL"></label>
  <label>Task status<select class="evlv-input evlv-select" name="status"><option value="">All statuses</option>${['completed','active','waiting','cancelled','unresolved'].map(s=>`<option ${searchState.status===s?'selected':''}>${s}</option>`).join('')}</select></label>
  <label>Activity<select class="evlv-input evlv-select" name="activity"><option value="">All activities</option>${['investigate','plan','implement','test','review','document','operate','other'].map(s=>`<option ${searchState.activity===s?'selected':''}>${s}</option>`).join('')}</select></label>
  <label>Search method<select class="evlv-input evlv-select" name="mode"><option value="keyword" ${searchState.mode==='keyword'?'selected':''}>Keyword</option><option value="semantic" ${searchState.mode==='semantic'?'selected':''}>Semantic · local embeddings</option></select></label>${button('Search','type="submit"')}</form>
  <p id="history-status" role="status"></p><div id="history-results"></div><div class="modal-actions" id="history-pages"></div></section>`;
  let epoch=0;
  const load=async()=>{
    const version=++epoch;root.querySelector('#history-status').textContent='Searching…';
    try {
      const q=new URLSearchParams({...searchState,limit:20});if(project)q.set('project',project);
      const result=await (searchState.mode==='semantic'?api('/api/search-task-history',Object.fromEntries(q)):api('/api/task-history?'+q));if(version!==epoch||!root.isConnected)return;
      root.querySelector('#history-status').textContent=`${result.total??0} matching tasks · ${result.mode} search`;
      root.querySelector('#history-results').innerHTML=result.items.length?`<div class="history-list">${result.items.map(t=>`<article class="history-card"><div><span class="badge">${esc(t.status)}</span>${t.similarity!=null?` <small>Similarity ${Number(t.similarity).toFixed(3)}</small>`:''}</div><h3><button class="inline-link" data-history-task="${esc(t.task_id)}">${esc(t.title)}</button></h3><p>${esc(t.summary||'Not analyzed yet. Open this task to collect its steps into subtasks.')}</p><small>${result.mode==='semantic'?'Semantic task match':t.matched_subtasks.length+' matching subtasks'} · ${t.analysis_id?'Analyzed':'Unanalyzed'}${t.stale?' · Updated steps: analysis is stale':''}</small></article>`).join('')}</div>`:'<div class="table-empty">No matching tasks. Try fewer terms or assign collected turns to a task.</div>';
      root.querySelectorAll('[data-history-task]').forEach(b=>b.onclick=e=>{e.stopPropagation();open(b.dataset.historyTask);});
      root.querySelector('#history-pages').innerHTML=(searchState.offset?button('Previous','data-history-prev'):'')+(result.next_offset!=null?button('Next','data-history-next'):'');
      const prev=root.querySelector('[data-history-prev]'),next=root.querySelector('[data-history-next]');
      if(prev)prev.onclick=()=>{searchState.offset=Math.max(0,searchState.offset-20);load();};
      if(next)next.onclick=()=>{searchState.offset=result.next_offset;load();};
    } catch(error) {if(version===epoch)root.querySelector('#history-status').textContent=error.message;}
  };
  root.querySelector('form').onsubmit=e=>{e.preventDefault();searchState={...Object.fromEntries(new FormData(e.currentTarget)),offset:0};load();};
  load();
}
export async function openTaskHistory(taskId,showModal) {
  const epoch=++modalEpoch;
  showModal('Task history',`<span data-history-owner="${epoch}" hidden></span><p role="status">Loading task and subtasks…</p>`);
  try {
    const data=await api('/api/task-history-detail?'+new URLSearchParams({task_id:taskId}));
    if(epoch!==modalEpoch||!document.querySelector(`[data-history-owner="${epoch}"]`)||!document.querySelector('#modal')?.open)return;
    const job=data.jobs[0];const active=job&&['queued','running'].includes(job.status);
    const groups=data.subtasks.map(s=>`<details class="history-subtask" data-subtask="${esc(s.id)}"><summary><span class="badge">${esc(s.activity)}</span> <strong>${esc(s.title)}</strong> <small>${s.step_count} steps</small></summary><p>${esc(s.summary)}</p><p>${s.tags.map(esc).join(' · ')} · ${Math.round(s.confidence*100)}% interpretation confidence</p><div data-step-list></div></details>`).join('');
    showModal(data.task.title,`<span data-history-owner="${epoch}" hidden></span><div class="history-breadcrumb">Task → Subtasks → Source steps</div><p>${esc(data.task.goal)}</p><p>${esc(data.task.outcome||'Task outcome has not been verified.')}</p>${(data.related_prs||[]).length?'<p>Referenced PRs: '+data.related_prs.map(url=>`<a href="${esc(url)}" target="_blank" rel="noopener">${esc(url)}</a>`).join(' · ')+'</p>':''}<div class="modal-actions">${button(data.analysis?'Analyze new steps':'Analyze into subtasks',`data-start-analysis ${active?'disabled':''}`)}</div><p class="section-note">On demand · small-model interpretation · ${data.step_count} collected steps. Source measurements stay unchanged.</p>
      ${job?`<p role="status">Analysis: ${esc(job.status)} · ${esc(job.model)}${job.error?' — '+esc(job.error):''}</p><p class="section-note">Analysis overhead: ${job.usage?esc(job.usage.total_tokens??'Unknown')+' recorded tokens':'unknown or not yet reported'}. Separate from source task measurements.</p>`:''}
      ${data.stale?'<div class="notice">New or reassigned evidence exists. This interpretation is stale; analyze the current steps to update it.</div>':''}
      ${data.analysis?`<p>${esc(data.analysis.summary)}</p><small>Version ${esc(data.analysis.id.slice(0,8))} · ${esc(data.analysis.model)}</small>${groups}`:'<div class="table-empty">No subtask analysis yet. Analyze the task to organize its collected steps.</div>'}`);
    document.querySelector('[data-start-analysis]').onclick=async e=>{
      e.currentTarget.disabled=true;
      try{await api('/api/analyze-task',{task_id:taskId});await openTaskHistory(taskId,showModal);}
      catch(error){showModal('Analysis could not start',`<p role="alert">${esc(error.message)}</p>`);}
    };
    const loadSteps=async(node,offset=0)=>{
      const target=node.querySelector('[data-step-list]');target.textContent='Loading source steps…';
      try{
        const detail=await api('/api/task-history-detail?'+new URLSearchParams({task_id:taskId,subtask_id:node.dataset.subtask,limit:20,offset}));
        target.innerHTML=`<ol class="history-steps" start="${offset+1}">${detail.steps.map(s=>`<li><button class="inline-link" data-history-evidence="${esc(s.id)}">${esc(s.name)}</button><small>${esc(s.ts)} · ${s.runtime==null?'Runtime unknown':esc(s.runtime)+'s'} · ${s.failed===1?'Nonzero/failed operation':s.failed===0?'Operation completed':'Outcome unknown'}</small></li>`).join('')}</ol><div class="modal-actions">${offset?button('Previous steps','data-steps-prev'):''}${detail.next_offset!=null?button('More steps','data-steps-next'):''}</div><div data-source-output></div>`;
        const prev=target.querySelector('[data-steps-prev]'),next=target.querySelector('[data-steps-next]');if(prev)prev.onclick=()=>loadSteps(node,Math.max(0,offset-20));if(next)next.onclick=()=>loadSteps(node,detail.next_offset);
        target.querySelectorAll('[data-history-evidence]').forEach(b=>b.onclick=async()=>{
          const output=target.querySelector('[data-source-output]');output.textContent='Loading retained evidence…';
          try{const r=await api('/api/task-step-evidence?'+new URLSearchParams({id:b.dataset.historyEvidence}));output.innerHTML='<h4>Retained source evidence</h4><pre>'+esc(JSON.stringify(r,null,2))+'</pre>';}
          catch(error){output.textContent=error.message;}
        });
      }catch(error){target.textContent=error.message;}
    };
    document.querySelectorAll('[data-subtask]').forEach(node=>node.ontoggle=()=>{if(node.open&&!node.dataset.loaded){node.dataset.loaded='true';loadSteps(node);}});
    if(active)setTimeout(()=>{if(epoch===modalEpoch&&document.querySelector(`[data-history-owner="${epoch}"]`)&&document.querySelector('#modal')?.open)openTaskHistory(taskId,showModal);},2500);
  }catch(error){if(epoch===modalEpoch&&document.querySelector(`[data-history-owner="${epoch}"]`))showModal('Task history unavailable',`<p role="alert">${esc(error.message)}</p>`);}
}
