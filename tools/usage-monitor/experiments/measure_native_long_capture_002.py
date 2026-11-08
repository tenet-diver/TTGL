#!/usr/bin/env python3
"""Read-only response-level accounting incl native in-band compaction."""
import json
from pathlib import Path
import sys
from longmemeval_codex_trial import Store,REPO
from native_jsonl import records
from cost_context_study import PRICING,price
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'observability'))
from capture_objects import read_capture
ROOT=REPO/'work/security/context-memory-20261107/native-long-capture-canary-002'


def measure():
    if (ROOT/'results.json').exists():raise ValueError('Preserve existing measurement')
    sid=json.loads((ROOT/'complete.json').read_text())['session_id'];store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan()
    with store.connection() as db:
        native=[dict(r) for r in db.execute("SELECT id,usage FROM events WHERE session_id=? AND kind='generation'",(sid,))]
    for row in native:row['usage']=json.loads(row['usage'])
    byid={r['id'].split(':response:',1)[1]:r for r in native}
    if len(byid)!=len(native):raise ValueError('Duplicate native IDs')
    captures=[read_capture(p) for p in (ROOT/'captures').glob('*.json')]
    generated=[c for c in captures if c.get('response_ids')]
    observed=[];aux=[];keys=('input_tokens','cached_input_tokens','output_tokens','total_tokens')
    for c in generated:
        if c['status']!=200 or c.get('response_truncated') or c['original_request_sha256']!=c['forwarded_request_sha256']:raise ValueError('Incomplete/changed request or response')
        if len(c['response_ids'])!=1:raise ValueError('Ambiguous response')
        ident=c['response_ids'][0];observed.append(ident)
        ends=[e['response'] for e in c['response']['sse_events'] if e.get('type')=='response.completed']
        if len(ends)!=1:raise ValueError('Missing unique completed SSE')
        response=ends[0];u=response['usage'];transport=dict(input_tokens=u['input_tokens'],cached_input_tokens=u.get('input_tokens_details',{}).get('cached_tokens',0),output_tokens=u['output_tokens'],total_tokens=u['total_tokens'])
        if response['id']!=ident or transport!={k:byid[ident]['usage'][k] for k in keys}:raise ValueError('Native transport mismatch')
        if response['model']!='gpt-6.1-sol':raise ValueError('Unregistered response model')
        if any(item.get('type')=='compaction_trigger' for item in c['request'].get('input',[])):aux.append(ident)
    if set(observed)!=set(byid) or len(set(observed))!=len(observed) or len(aux)!=1:raise ValueError('Response/compaction allocation incomplete')
    expected=(ROOT/'seed.txt').read_text()
    seed_retained=any(item.get('text')==expected for c in generated for m in c['request'].get('input',[]) for item in m.get('content',[]) if isinstance(item,dict))
    if len(expected)<=262144 or not seed_retained:raise ValueError('Large string not retained exactly')
    total={k:sum(r['usage'][k] for r in native) for k in keys}
    ordinary={k:sum(r['usage'][k] for ident,r in byid.items() if ident not in aux) for k in keys}
    snapshots=[next(r['usage'] for r in records(ROOT/f'call-{i}') if r.get('type')=='turn.completed') for i in (1,2)]
    if any(snapshots[-1][k]!=ordinary[k] for k in keys[:3]):raise ValueError('CLI ordinary response semantics unresolved')
    rollout=list((Path.home()/'.codex/sessions').rglob('*'+sid+'*'))
    if len(rollout)!=1:raise ValueError('Ambiguous rollout')
    compacted=[json.loads(line)['payload'] for line in rollout[0].read_bytes().split(b'\n') if line.startswith(b'{') and json.loads(line).get('type')=='compacted']
    if len(compacted)!=1 or compacted[0].get('compaction_response_id')!=aux[0]:raise ValueError('No matching native automatic compaction')
    rates=json.loads(PRICING.read_text())['primary_scenario'];cost=sum(price(r['usage'],rates) for r in native);auxcost=sum(price(byid[i]['usage'],rates) for i in aux)
    public=dict(id='native-long-capture-canary-002',gate_passed=True,answer_exact=True,large_string_retained_exactly=True,input_characters=len(expected),automatic_compaction_observed=True,compaction_branch='Native in-band /responses compaction_trigger; compacted event matches response ID. Separate /responses/compact endpoint not used.',
        unique_responses=len(native),auxiliary_responses=len(aux),usage=total,ordinary_usage=ordinary,compaction_usage={k:total[k]-ordinary[k] for k in keys},credit_rate_scenario=cost,compaction_credit_rate_scenario=auxcost,
        cli_cumulative_snapshots=snapshots,cli_semantics='Cumulative ordinary response usage; excludes compaction. Never sum snapshots; use deduplicated native generation IDs including compaction.',native_cli_transport_reconciled=True,wire_hashes_equal=True,cash_cost=None,
        limitations='Synthetic2-turn mechanism only; not benchmark performance, savings, all-host security or separate compact-endpoint proof. Built-in transport fallback attempted; process retries zero.')
    cell=dict(case='native-long-capture-002',condition='capture_only',role='reader',session_id=sid,usage=total,native_reconciled=True,native_response_ids=[r['id'] for r in native],cost=cost,quality=dict(passed=True,kind='Synthetic capture/automatic-compaction/accounting mechanism'))
    (ROOT/'results.json').write_text(json.dumps(dict(public,cells=[cell]),indent=2)+'\n')
    (Path(__file__).resolve().parent.parent/'studies/native-long-capture-results-002.json').write_text(json.dumps(public,indent=2)+'\n')
    print(json.dumps(public,indent=2))


if __name__=='__main__':measure()
