import { button, badge, emptyState, escapeHTML as esc } from '/ui.js';
const activities=['investigate','plan','implement','test','review','document','operate','other'];
async function api(path,body) {
  const response=await fetch(path,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:undefined);
  const value=await response.json();if(!response.ok)throw new Error(value.error||'Request failed');return value;
}

/** Recorded tool timing with explicit, user-owned step selection. No model calls. */
export function renderStepTimeline(root,{taskId,subtaskId=null,onGrouped=()=>{},onError=()=>{}}) {
  let offset=0, epoch=0, snapshot=null, selected=new Map();
  root.innerHTML='<p role="status">Loading source step timeline…</p>';
  const load=async()=>{
    const version=++epoch;
    try {
      const data=await api('/api/task-timeline?'+new URLSearchParams({task_id:taskId,...(subtaskId?{subtask_id:subtaskId}:{}),limit:100,offset}));
      if(version!==epoch||!root.isConnected)return;
      const selectionChanged=snapshot&&snapshot!==data.snapshot_hash&&selected.size;
      if(selectionChanged)selected.clear();
      snapshot=data.snapshot_hash;
      const groupNames=new Map(data.groups.map(g=>[g.id,g.title]));
      const span=Math.max(1,(data.range_end??0)-(data.range_start??0));
      const rows=data.steps.map((step,index)=>{
        const end=Date.parse(step.ts), runtime=typeof step.runtime==='number'&&step.runtime>=0?step.runtime:null;
        const left=Number.isFinite(end)?Math.max(0,Math.min(99.8,((end-(runtime??0)*1000-data.range_start)/span)*100)):0;
        const width=runtime==null?0:Math.max(0,Math.min(100-left,runtime*1000/span*100));
        const timing=runtime==null?'Runtime unknown':runtime.toLocaleString('en',{maximumFractionDigits:3})+'s recorded runtime';
        const eventTime=Number.isFinite(end)?new Date(end).toLocaleString():'Event time unknown';
        return `<div class="timeline-step"><label class="timeline-step-select"><input type="checkbox" data-step-select="${esc(step.id)}" aria-label="Select step ${offset+index+1}: ${esc(step.name)}" ${selected.has(step.id)?'checked':''} ${step.group_id?'disabled':''}><span class="timeline-step-name"><strong>${esc(step.name)}</strong><small>${esc(eventTime)}${step.group_id?' · '+esc(groupNames.get(step.group_id)||'Collected subtask'):''}${step.failed===1?' · Nonzero operation':''}</small></span><span class="timeline-track" aria-hidden="true">${Number.isFinite(end)?`<span class="timeline-bar ${runtime==null?'timeline-point':''} ${step.failed===1?'timeline-nonzero':''} ${step.group_id?'timeline-collected':''}" style="left:${left}%;width:max(2px,${width}%)"></span>`:'Timing unavailable'}</span><small class="timeline-runtime">${esc(timing)}</small></label>${button('Inspect',`data-inspect-step="${esc(step.id)}"`)}</div>`;
      }).join('');
      root.innerHTML=`<div class="timeline-chart" role="group" aria-label="Source step timeline"><div class="section-heading"><h3>Source steps</h3><span class="muted">${data.total} steps · ${data.groups.length} collected subtasks</span></div><p class="section-note">${esc(data.timing_basis)} Select steps to collect a subtask; grouping records your interpretation and does not verify success.</p>
        ${data.total?`<div class="timeline-axis"><span>${data.range_start==null?'Time unknown':esc(new Date(data.range_start).toLocaleString())}</span><span>${data.range_end==null?'Time unknown':esc(new Date(data.range_end).toLocaleString())}</span></div><div class="timeline-rows">${rows}</div>`:emptyState('No source steps yet','Assign a collected turn to this task to chart its operations.')}
        <div class="pagination">${offset?button('Earlier steps','data-timeline-prev'):''}<span>${data.total?offset+1:0}–${Math.min(offset+data.steps.length,data.total)} of ${data.total}</span>${data.next_offset!=null?button('Later steps','data-timeline-next'):''}</div>
        <details class="timeline-curation" data-timeline-curation><summary>Collect selected steps into a subtask</summary><form class="timeline-collect-form"><p data-selection-count role="status"></p><div class="timeline-group-fields"><label>Subtask name<input class="ui-input" name="title" maxlength="200" required placeholder="What these steps did"></label><label>Subtask type<select class="ui-input" name="activity" aria-label="Subtask type">${activities.map(a=>`<option>${a}</option>`).join('')}</select></label></div><label>Description (optional)<input class="ui-input" name="summary" maxlength="4000" placeholder="Your interpretation of the selected evidence"></label><div class="ui-actions">${button('Clear selection','type="button" data-clear-steps')}${button('Collect selected into subtask','type="submit" data-collect-steps',true)}</div><p class="section-note" data-timeline-message role="status"></p></form></details><div data-timeline-evidence></div></div>`;
      const sync=()=>{
        root.querySelector('[data-timeline-curation]').open=selected.size>0;
        root.querySelector('[data-selection-count]').textContent=selected.size+' steps selected (up to 200, across pages)';
        root.querySelector('[data-collect-steps]').disabled=!selected.size;
        root.querySelector('[data-clear-steps]').disabled=!selected.size;
      };
      root.querySelectorAll('[data-step-select]').forEach(input=>input.onchange=()=>{
        if(input.checked&&selected.size>=200){input.checked=false;root.querySelector('[data-timeline-message]').textContent='Collect at most 200 steps at a time.';return;}
        if(input.checked)selected.set(input.dataset.stepSelect,data.steps.find(s=>s.id===input.dataset.stepSelect));else selected.delete(input.dataset.stepSelect);
        sync();
      });
      root.querySelector('[data-clear-steps]').onclick=()=>{selected.clear();root.querySelectorAll('[data-step-select]').forEach(i=>i.checked=false);sync();};
      const previous=root.querySelector('[data-timeline-prev]'),next=root.querySelector('[data-timeline-next]');
      if(previous)previous.onclick=()=>{offset=Math.max(0,offset-100);load();};
      if(next)next.onclick=()=>{offset=data.next_offset;load();};
      root.querySelector('form').onsubmit=async event=>{
        event.preventDefault();const fields=Object.fromEntries(new FormData(event.currentTarget));
        root.querySelector('[data-collect-steps]').disabled=true;
        try {
          await api('/api/collect-task-steps',{task_id:taskId,step_ids:[...selected.keys()],snapshot_hash:snapshot,...fields});
          selected.clear();await load();await onGrouped();
        }catch(error){if(root.isConnected){root.querySelector('[data-timeline-message]').textContent=error.message;sync();}onError(error.message);}
      };
      root.querySelectorAll('[data-inspect-step]').forEach(b=>b.onclick=async()=>{
        const output=root.querySelector('[data-timeline-evidence]');output.textContent='Loading retained source…';
        try{const value=await api('/api/task-step-evidence?'+new URLSearchParams({id:b.dataset.inspectStep}));if(output.isConnected)output.innerHTML='<h4>Retained source evidence</h4><pre>'+esc(JSON.stringify(value,null,2))+'</pre>';}
        catch(error){if(output.isConnected)output.textContent=error.message;}
      });
      if(selectionChanged)root.querySelector('[data-timeline-message]').textContent='Source evidence changed; selection cleared. Review the current steps.';
      sync();
    }catch(error){if(root.isConnected)root.innerHTML=emptyState('Timeline unavailable',error.message);onError(error.message);}
  };
  load();
}
