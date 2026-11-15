import {button, badge, escapeHTML as esc, emptyState} from '/ui.js';

const n = value => value == null ? 'Unknown' : Number(value).toLocaleString('en', {maximumFractionDigits:2});
const stamp = value => value ? new Date(value).toLocaleString() : 'Unknown';
const field = (title, value) => `<div><small>${esc(title)}</small><strong>${esc(value)}</strong></div>`;
const control = (label, name, value='', type='text') => `<label>${esc(label)}<input class="ui-input" type="${type}" name="${name}" value="${esc(value)}"></label>`;
const select = (label, name, values, value) => `<label>${esc(label)}<select class="ui-input" name="${name}">${values.map(([key,text])=>`<option value="${esc(key)}" ${value===key?'selected':''}>${esc(text)}</option>`).join('')}</select></label>`;
const modes = [['turns','Turns'],['tools','Tools'],['patterns','Repeated operations'],['steps','Source steps']];
const sorts = [['recent','Most recent'],['tokens','Most tokens'],['runtime','Most recorded runtime'],['output','Largest output'],['failures','Most tool failures'],['count','Most operations / copies']];

export function renderTraceExplorer(root, {state, data, overview, onChange, showModal, onError}) {
  const metrics = data.metrics;
  const set = values => onChange({...state, offset:0, ...values});
  const facets = overview?.facets || {};
  const scope = ['project','task','session','turn'].filter(key=>state[key]);
  const summary = [field('Native turns', n(metrics.turns)), field('Measured tokens', n(metrics.total_tokens)),
    field('Tool calls',n(metrics.tool_calls)), field('Unsuccessful tools',n(metrics.tool_failures)),
    field('Unknown tool outcomes',n(metrics.unknown_tool_outcomes)), field('Metered responses',`${n(metrics.metered_responses)} / ${n(metrics.responses)}`)].join('');
  root.innerHTML = `<div class="trace-explorer">
    <form class="trace-filters" data-trace-filters>
      ${control('Search prompts, tasks or operation labels','query',state.query)}
      ${control('Exact tool name','tool',state.tool)}${control('Exact model name','model',state.model)}
      ${control('Recorded task status','status',state.status)}
      ${select('Investigation signal','signal',[['','All turns'],['tool_failure','Recorded tool failure'],['unknown_tool_outcome','Unknown tool outcome'],['repeated_input','Repeated exact input'],['unassigned','Unassigned turns']],state.signal||'')}
      ${select('Order','sort',sorts,state.sort||'recent')}
      ${control('Since (ISO, with timezone)','since',state.since)}${control('Until (ISO, exclusive)','until',state.until)}
      <div class="ui-actions">${button('Apply','type="submit"',true)}${button('Reset','type="button" data-trace-reset')}</div>
    </form>
    <div class="trace-facets">${(facets.tools?.records||[]).slice(0,6).map((r,i)=>button(`${r.value} (${n(r.count)})`,`data-trace-tool="${i}"`)).join('')}
      ${(facets.models?.records||[]).filter(r=>r.value).slice(0,4).map((r,i)=>button(`${r.value} (${n(r.count)})`,`data-trace-model="${i}"`)).join('')}</div>
    ${scope.length?`<p class="section-note">Scope: ${scope.map(key=>`${esc(key)} <code>${esc(state[key])}</code>`).join(' · ')} ${button('Clear scope','data-trace-unscope')}</p>`:''}
    <div class="work-metrics ops-kpis">${summary}</div>
    <p class="section-note">${esc(data.scope)} ${data.view==='steps'?'Step filters apply to the results below; counters above cover the whole selected turns.':''}</p>
    <div class="trace-modes" role="group" aria-label="Evidence views">${modes.map(([key,label])=>button(label,`data-trace-mode="${key}" aria-pressed="${data.view===key}"`,data.view===key)).join('')}
      ${data.view==='patterns'?select('Fingerprint','pattern',[['input','Exact inputs'],['output','Nonempty outputs']],state.pattern||'input'):''}
      ${data.view==='steps'?select('Event type','kind',[['','All events'],['tool','Tool calls'],['generation','Model responses']],state.kind||''):''}
    </div>
    <div class="trace-results">${data.records.length?data.records.map((record,index)=>card(data.view,record,index)).join(''):emptyState('No matching evidence','Change the scope or filters. Missing records do not establish zero agent activity.')}</div>
    <div class="pagination trace-pagination"><span>${data.records.length?n(data.pagination.offset+1):'0'}–${n(data.pagination.offset+data.records.length)} of ${n(data.pagination.total)} results</span>
      ${button('Previous',`data-trace-page="${Math.max(0,data.pagination.offset-data.pagination.limit)}" ${data.pagination.offset===0?'disabled':''}`)}
      ${button('Next',`data-trace-page="${data.pagination.next_offset}" ${data.pagination.next_offset==null?'disabled':''}`)}</div>
    <details class="section trace-contract"><summary>Evidence contract and analyst tools</summary>
      <p>Use <code>query_trace_index</code> from the analyst MCP or CLI with the same filters. Follow evidence IDs with <code>read_evidence</code>; assigned tasks expose interpreted subtasks through <code>get_task_history</code>.</p>
      <pre>${esc(JSON.stringify({view:data.view,...state},null,2))}</pre>
      <ul>${data.limitations.map(text=>`<li>${esc(text)}</li>`).join('')}</ul>
    </details>
  </div>`;
  root.querySelector('[data-trace-filters]').onsubmit = event => {
    event.preventDefault(); set(Object.fromEntries(new FormData(event.currentTarget)));
  };
  root.querySelector('[data-trace-reset]').onclick = () => onChange({view:'turns',sort:'recent'});
  root.querySelector('[data-trace-unscope]')?.addEventListener('click',()=>set({project:'',task:'',session:'',turn:'',fingerprint:''}));
  root.querySelectorAll('[data-trace-tool]').forEach(node=>node.onclick=()=>set({tool:facets.tools.records[Number(node.dataset.traceTool)].value}));
  root.querySelectorAll('[data-trace-model]').forEach(node=>node.onclick=()=>set({model:facets.models.records.filter(r=>r.value)[Number(node.dataset.traceModel)].value}));
  root.querySelectorAll('[data-trace-mode]').forEach(node=>node.onclick=()=>set({view:node.dataset.traceMode,kind:'',fingerprint:''}));
  root.querySelectorAll('[data-trace-page]').forEach(node=>node.onclick=()=>onChange({...state,offset:Number(node.dataset.tracePage)}));
  root.querySelector('[name="pattern"]')?.addEventListener('change',event=>set({pattern:event.target.value}));
  root.querySelector('[name="kind"]')?.addEventListener('change',event=>set({kind:event.target.value}));
  root.querySelectorAll('[data-trace-open]').forEach(node=>node.onclick=()=>{
    const row=data.records[Number(node.dataset.traceOpen)];
    if(data.view==='tools')set({view:'turns',tool:row.name,kind:'',fingerprint:''});
    else set({view:'steps',session:row.session_id,turn:row.turn_id,kind:data.view==='patterns'?'tool':'',fingerprint:row.fingerprint||''});
  });
  root.querySelectorAll('[data-trace-raw]').forEach(node=>node.onclick=()=>readRaw(data.records[Number(node.dataset.traceRaw)].id,0,showModal,onError));
}

function card(view, row, index) {
  const open=button(view==='tools'?'Find turns':'Inspect steps',`data-trace-open="${index}"`);
  const task=row.task_id?`<a href="/tasks/${encodeURIComponent(row.task_id)}">${esc(row.task_title||row.task_id)}</a>`:'Unassigned native turn';
  const ref=`<p class="section-note trace-ref">${esc(row.session_id||'')} ${row.turn_id?' / '+esc(row.turn_id):''}</p>`;
  if(view==='turns') return `<article class="trace-result"><div class="section-heading"><h2>${task}</h2>${open}</div>${ref}
    <p>${esc(stamp(row.start))} · ${esc(row.models||'Model unknown')} · ${badge(row.task_status||'No recorded task status')} ${badge(row.native_completion_marker?'Native completion marker':'No completion marker')}</p>
    <div class="trace-measures">${field('Tokens',n(row.total_tokens))}${field('Tool calls',n(row.tool_calls))}${field('Tool failures',n(row.tool_failures))}${field('Unknown outcomes',n(row.unknown_tool_outcomes))}${field('Recorded tool runtime',n(row.recorded_tool_runtime_seconds)+' s')}${field('Output',n(row.recorded_output_bytes)+' bytes')}</div></article>`;
  if(view==='tools') return `<article class="trace-result"><div class="section-heading"><h2>${esc(row.name)}</h2>${open}</div><div class="trace-measures">${field('Calls',n(row.calls))}${field('Turns',n(row.turns))}${field('Tool failures',n(row.tool_failures))}${field('Unknown outcomes',n(row.unknown_tool_outcomes))}${field('Timed calls',n(row.timed_calls))}${field('Recorded runtime',n(row.recorded_tool_runtime_seconds)+' s')}</div></article>`;
  if(view==='patterns') return `<article class="trace-result"><div class="section-heading"><h2>${esc(row.name)} · ${n(row.copies)} exact copies</h2>${open}</div>${ref}<code class="trace-ref">${esc(row.fingerprint)}</code><div class="trace-measures">${field('Tool failures',n(row.tool_failures))}${field('Recorded runtime',n(row.recorded_tool_runtime_seconds)+' s')}${field('Output',n(row.recorded_output_bytes)+' bytes')}</div></article>`;
  const outcome=row.kind==='generation'?'Measured model response':row.failed===1?'Recorded unsuccessful tool':row.failed===0?'Recorded successful tool':'Tool outcome unknown';
  return `<article class="trace-result"><div class="section-heading"><h2>${esc(row.name)}</h2>${button('Read original evidence',`data-trace-raw="${index}"`)}</div><p>${esc(stamp(row.ts))} · ${badge(outcome)}</p><p class="trace-ref"><code>${esc(row.id)}</code></p><div class="trace-measures">${field('Model',row.model||'Unknown')}${field('Tokens',n(row.usage?.total_tokens))}${field('Recorded runtime',n(row.runtime)+' s')}${field('Output',n(row.bytes)+' bytes')}${field('Source line',n(row.source_line))}</div></article>`;
}

async function readRaw(id, offset, showModal, onError) {
  showModal('Original retained evidence','<p role="status">Loading source record…</p>');
  try {
    const response=await fetch('/api/task-step-evidence?'+new URLSearchParams({id,offset,limit:8000}));
    const result=await response.json();if(!response.ok||result.isError)throw Error(result.content?.[0]?.text||result.error||'Evidence unavailable');
    const data=JSON.parse(result.content[0].text);
    showModal('Original retained evidence',`<p class="trace-ref"><code>${esc(id)}</code></p><p>Characters ${n(offset)}–${n(offset+data.evidence.length)} of ${n(data.total_characters)}. Redaction and source retention limits apply.</p><pre class="trace-raw">${esc(data.evidence)}</pre><div class="ui-actions">${button('Previous',`data-raw-prev ${offset===0?'disabled':''}`)}${button('Next',`data-raw-next ${data.next_offset==null?'disabled':''}`)}</div>`);
    document.querySelector('[data-raw-prev]').onclick=()=>readRaw(id,Math.max(0,offset-8000),showModal,onError);
    document.querySelector('[data-raw-next]').onclick=()=>readRaw(id,data.next_offset,showModal,onError);
  } catch(error) {showModal('Original retained evidence',`<p>${esc(error.message)}</p>`);onError(error.message);}
}
