import {button,escapeHTML as esc,badge} from '/ui.js';
import {renderList} from '/data-list.js';
const n=v=>v==null?'Unknown':Number(v).toLocaleString('en');
let epoch=0;

export async function openBulkAnalysis({showModal,post,onError},offset=0,limit=20) {
  const current=++epoch;
  showModal('Bulk activity analysis','<p role="status">Loading analysis queue…</p>');
  const render=async()=>{
    try {
      const response=await fetch('/api/bulk-analysis?'+new URLSearchParams({offset,limit}));const data=await response.json();
      if(!response.ok)throw Error(data.error||'Queue unavailable');
      if(current!==epoch||!document.querySelector('#modal').open)return;
      const batch=data.batch,active=batch&&['queued','running','stopping'].includes(batch.status);
      const header=batch?`<p>${badge(batch.status)} · ${esc(batch.model)} · version ${esc(JSON.parse(batch.protocol).id)}</p><p><strong>${n(data.finished)} / ${n(data.total)}</strong> tasks finished processing. ${Object.entries(data.counts).map(([key,value])=>esc(key.replaceAll('_',' '))+': '+n(value)).join(' · ')}</p><p>Source-event coverage: ${n(data.coverage.interpreted_events)} / ${n(data.coverage.frozen_events)} interpreted. Analysis overhead: ${n(data.coverage.known_analysis_tokens)} known native tokens; ${n(data.coverage.jobs_missing_usage)} attempts have unknown usage.</p>${batch.error?`<p role="alert">${esc(batch.error)}</p>`:''}`:'<p>No bulk analysis has been started.</p>';
      showModal('Bulk activity analysis',`${header}<p>Analyze all indexed tasks across projects using the configured small model. Two analyses at a time. Existing source measurements and explicit task acceptance stay unchanged. Outcomes and user-intervention labels cite their evidence and remain interpretations.</p><div class="ui-actions">${button(active?'Analysis running':'Analyze all activity',`data-bulk-start ${active?'disabled':''}`,true)}${active?button('Stop after current analyses','data-bulk-stop'):''}</div><p class="section-note">A finite frozen corpus, with bounded excerpts for long tasks. Failed or uncertain calls are preserved without automatic retries. New activity arriving later is separate.</p>${batch?renderList('bulk-analysis-items',[{key:'title',label:'Task'},{key:'status',label:'Analysis status',cell:r=>badge(r.status.replaceAll('_',' '))},{key:'tokens',label:'Analysis tokens',numeric:true,value:r=>r.usage?.total_tokens},{key:'error',label:'Details'}],data.records,null,false,{serverPage:{...data.pagination,onPage:(next,size)=>openBulkAnalysis({showModal,post,onError},next,size)}}):''}<p data-bulk-message role="status"></p>`);
      document.querySelector('[data-bulk-start]').onclick=async event=>{
        event.currentTarget.disabled=true;document.querySelector('[data-bulk-message]').textContent='Freezing the corpus and starting analysis…';
        try{await post('bulk-analysis',{action:'start'});openBulkAnalysis({showModal,post,onError});}
        catch(error){document.querySelector('[data-bulk-message]').textContent=error.message;event.target.disabled=false;onError(error.message);}
      };
      document.querySelector('[data-bulk-stop]')?.addEventListener('click',async()=>{try{await post('bulk-analysis',{action:'stop',batch_id:batch.id});openBulkAnalysis({showModal,post,onError});}catch(error){onError(error.message);}});
      if(active)setTimeout(()=>{if(current===epoch&&document.querySelector('#modal').open&&!document.activeElement?.closest('[data-table]'))render();},4000);
    }catch(error){if(current===epoch){showModal('Bulk activity analysis',`<p role="alert">${esc(error.message)}</p>`);onError(error.message);}}
  };
  return render();
}
