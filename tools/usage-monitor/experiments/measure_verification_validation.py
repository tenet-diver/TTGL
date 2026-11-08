#!/usr/bin/env python3
"""Price all24 frozen held-out repair attempts and retain actual verification commands."""
import json
from pathlib import Path
from verification_selection_validation import ROOT, SOURCE, digest, frozen
from native_jsonl import records, meter_cell
from longmemeval_codex_trial import Store
from cost_context_study import REPO, PRICING


def measure():
    frozen()
    if not (ROOT/'complete.json').exists() or (ROOT/'results.json').exists():
        raise ValueError('Incomplete or already measured experiment')
    receipt=json.loads((SOURCE/'download-receipt.json').read_text())
    if any(digest(SOURCE/'source'/r['path'])!=r['sha256'] for r in receipt['files']):
        raise ValueError('Reviewed source changed')
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000')
    store.scan()
    rates=json.loads(PRICING.read_text())['primary_scenario']
    captures=[json.loads(p.read_text()) for p in (ROOT/'captures').glob('*.json')]
    cells=[]
    for item in json.loads((ROOT/'generation-complete.json').read_text())['cells']:
        cell=ROOT/item['case']/item['condition']
        metered=meter_cell(store,cell,item['session_id'],dict(case=item['case'],condition=item['condition'],role='reader'),rates)
        with store.connection() as db:
            models={r['model'] for r in db.execute("SELECT model FROM events WHERE session_id=? AND kind='generation'",(item['session_id'],))}
        if models!={'gpt-6.1-sol'}:
            raise ValueError('Unregistered pricing model')
        ids={i.rsplit(':response:',1)[-1] for i in metered['native_response_ids']}
        matched=[c for c in captures if ids.intersection(c.get('response_ids',[]))]
        if len(matched)!=len(ids) or any(c.get('state')!='complete' or c.get('status')!=200 for c in matched):
            raise ValueError('Incomplete transport/native coverage')
        metered['grade']=json.loads((cell/'grade.json').read_text())
        metered['process_wall_seconds']=json.loads((cell/'completion.json').read_text())['elapsed_seconds']
        commands=[r['item'] for r in records(cell) if r.get('type')=='item.completed' and r.get('item',{}).get('type')=='command_execution']
        metered['test_commands']=[dict(command=c['command'],exit_code=c.get('exit_code')) for c in commands if 'unittest' in c.get('command','')]
        metered['verification_adherence']='Exact command sequence retained; semantic initial/final adherence requires separate read-only audit.'
        cells.append(metered)
    ids=[i for c in cells for i in c['native_response_ids']]
    if len(cells)!=24 or len(ids)!=len(set(ids)):
        raise ValueError('Allocation incomplete or duplicate responses')
    totals={}
    for arm in ('full_initial','focused_initial'):
        selected=[c for c in cells if c['condition']==arm]
        totals[arm]=dict(cells=len(selected),passed=sum(c['grade']['passed'] for c in selected),
                         native_tokens=sum(c['usage']['total_tokens'] for c in selected),
                         credit_rate_scenario=sum(c['cost'] for c in selected),
                         process_wall_seconds=sum(c['process_wall_seconds'] for c in selected))
    baseline=totals['full_initial'];candidate=totals['focused_initial']
    by_case={}
    for cell in cells:by_case.setdefault(cell['case'],{})[cell['condition']]=cell
    pairs=[]
    for case,arms in by_case.items():
        if set(arms)!={'full_initial','focused_initial'}:raise ValueError('Unpaired validation case')
        b=arms['full_initial'];f=arms['focused_initial'];pairs.append(dict(case=case,baseline_passed=b['grade']['passed'],focused_passed=f['grade']['passed'],baseline_cost=b['cost'],focused_cost=f['cost'],focused_cost_win=f['cost']<b['cost']))
    losses=[p['case'] for p in pairs if p['baseline_passed'] and not p['focused_passed']]
    wins=sum(p['focused_cost_win'] for p in pairs)
    baseline_successes=baseline['passed']
    gate=dict(allocation_complete=len(pairs)==12,matched_baseline_successes=baseline_successes,baseline_successes_lost=losses,paired_cost_wins=wins,matched_success_retention=(baseline_successes-len(losses))/baseline_successes if baseline_successes else None,pooled_cost_saving=1-candidate['credit_rate_scenario']/baseline['credit_rate_scenario'],zero_observed_loss_one_sided95_upper_loss_rate=(1-.05**(1/baseline_successes)) if baseline_successes and not losses else None)
    gate['passed']=bool(gate['allocation_complete'] and baseline_successes>0 and not losses and gate['pooled_cost_saving']>=.10 and wins>6)
    gate['interpretation']='Frozen observed-quality/cost selection gate only; small visible-test repair panel does not establish population noninferiority or long-horizon efficacy.'
    summary=dict(id='verification-selection-validation-001',totals=totals,joint_gate=gate,pairs=pairs,
                 cost_change_percent=(candidate['credit_rate_scenario']/baseline['credit_rate_scenario']-1)*100,
                 token_change_percent=(candidate['native_tokens']/baseline['native_tokens']-1)*100,
                 unique_responses=len(ids),all_native_cli_transport_reconciled=True,
                 cash_cost=None,local_operational_cost=None,
                 note='Twelve previously uninspected public exercise families with seeded bugs; frozen-policy held-out repair validation. Full final tests shared. No long-horizon, official benchmark, cash or population noninferiority claim.')
    result=dict(**summary,cells=cells,protocol=json.loads((ROOT/'protocol.json').read_text()))
    (ROOT/'results.json').write_text(json.dumps(result,indent=2)+'\n')
    public=Path(__file__).resolve().parents[1]/'studies/verification-selection-validation-results-001.json'
    with public.open('x') as stream:
        json.dump(summary,stream,indent=2)
        stream.write('\n')
    print(json.dumps(summary))


if __name__=='__main__':
    measure()
