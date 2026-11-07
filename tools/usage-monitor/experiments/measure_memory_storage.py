#!/usr/bin/env python3
"""Allocate continued CLI snapshots to unique native turns, never sum snapshots."""
import argparse,collections,json
from pathlib import Path
from native_jsonl import records,validate_native_completion,meter_cell
from cost_context_study import PRICING,REPO,price
from longmemeval_codex_trial import Store
KEYS=('input_tokens','cached_input_tokens','output_tokens','total_tokens')

def meter_calls(store,entries,rates):
    groups=collections.defaultdict(list);result=[];seen=set()
    for item in entries:groups[item['session_id']].append(item)
    with store.connection() as db:
        for sid,items in groups.items():
            items=sorted(items,key=lambda i:i['query'])
            if len({(i['case'],i['condition']) for i in items})!=1:raise ValueError('Thread shared across conditions/corpora')
            continued=items[0]['condition']=='continued_full'
            if len(items)>1 and not continued:raise ValueError('Fresh condition reuses a thread')
            turns=[r['turn_id'] for r in db.execute('SELECT turn_id FROM turns WHERE session_id=? ORDER BY start,turn_id',(sid,))]
            rows=[dict(r) for r in db.execute("SELECT id,turn_id,usage FROM events WHERE session_id=? AND kind='generation'",(sid,))]
            if len(turns)!=len(items) or not rows:raise ValueError('Ambiguous native turn mapping')
            for r in rows:r['usage']=json.loads(r['usage'])
            prefix={k:0 for k in KEYS}
            for item,turn in zip(items,turns):
                cell=Path(item['cell']);actual=validate_native_completion(cell)
                if actual!=sid:raise ValueError('CLI/native thread differs')
                native=[r for r in rows if r['turn_id']==turn];usage={k:sum(r['usage'].get(k,0) for r in native) for k in KEYS}
                if not native:raise ValueError('Missing turn usage')
                for k in KEYS:prefix[k]+=usage[k]
                cli=next(r['usage'] for r in records(cell) if r.get('type')=='turn.completed');expected=prefix if continued else usage
                if any(cli[k]!=expected[k] for k in KEYS[:3]):raise ValueError('CLI counter semantic mismatch')
                ids=[r['id'] for r in native]
                if any(i in seen for i in ids):raise ValueError('Response counted twice')
                seen.update(ids);grade=json.loads((cell/'grade.json').read_text()) if (cell/'grade.json').exists() else None
                result.append(dict(case=item['case'],condition=item['condition'],query=item['query'],role='reader',session_id=sid,turn_id=turn,usage=usage,native_reconciled=True,native_response_ids=ids,cost=sum(price(r['usage'],rates) for r in native),grade=grade,cli_counter_semantics='cumulative-thread' if continued else 'fresh-thread',reader_artifact=str(cell)))
    return result

def measure():
    from memory_storage_ablation import ROOT,frozen,GLOBAL
    frozen()
    if not (ROOT/'complete.json').exists():raise ValueError('Incomplete reuse block')
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan();rates=json.loads(PRICING.read_text())['primary_scenario'];entries=json.loads((ROOT/'readers-complete.json').read_text())['cells']
    for item in entries:item['cell']=str(ROOT/item['cell'])
    cells=meter_calls(store,entries,rates)
    for path in ROOT.glob('corpus-*/mem0-build/extractions/extract-*'):
        sid=validate_native_completion(path,no_tools=True);cells.append(meter_cell(store,path,sid,dict(case=path.parents[2].name,condition='mem0_dense',role='memory_extraction',query=0),rates))
    ids=[i for c in cells for i in c['native_response_ids']]
    if len(ids)!=len(set(ids)):raise ValueError('Cross-role native response duplication')
    totals={};curves=[]
    for arm in sorted({c['condition'] for c in cells}):
        selected=[c for c in cells if c['condition']==arm];readers=[c for c in selected if c['role']=='reader'];usage={k:sum(c['usage'][k] for c in selected) for k in KEYS}
        totals[arm]=dict(task_credit_rate_scenario=sum(c['cost'] for c in selected),task_native_tokens=usage['total_tokens'],usage=usage,reader_successes=sum(c['grade']['passed'] for c in readers),reader_count=len(readers))
        for case in sorted({c['case'] for c in selected}):
            for count in range(1,5):
                prefix=[c for c in selected if c['case']==case and (c['role']=='memory_extraction' or c['query']<count)];r=[c for c in prefix if c['role']=='reader'];cost=sum(c['cost'] for c in prefix)
                curves.append(dict(case=case,condition=arm,actual_questions=count,credit_rate_scenario=cost,average_per_actual_question=cost/count,correct=sum(c['grade']['passed'] for c in r),native_tokens=sum(c['usage']['total_tokens'] for c in prefix)))
    result=dict(protocol=json.loads((ROOT/'protocol.json').read_text()),cells=cells,totals=totals,actual_reuse_curves=curves,cash_cost=None,quota_saving=None,local_compute_monetary_cost=None,limitation='Generated static recall with3 corpus sizes/4 actual questions; not coding or population validation. No extrapolated reuse savings. Local compute and research expense separate.')
    (ROOT/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(totals,indent=2))
if __name__=='__main__':measure()
