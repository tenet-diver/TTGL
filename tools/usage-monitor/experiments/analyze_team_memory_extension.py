#!/usr/bin/env python3
"""Read-only, allowlisted public report for the separately frozen extension.

No model calls, raw prompt export, runner mutation or historical outcome pooling.
Incomplete matrices are explicitly interim; unknown usage remains unknown.
"""
import argparse
import csv
from datetime import datetime,timezone
import json
import os
import re
from pathlib import Path
import statistics

RATES={'gpt-6.1-sol':(50,2.5,250),'gpt-6-luna':(2.5,.25,12.5)}


def scenario(usage_by_model):
    total=0
    for model,u in usage_by_model.items():
        if any(u[k]<0 for k in ('input_tokens','cached_input_tokens','output_tokens')) or u['cached_input_tokens']>u['input_tokens']:
            raise ValueError('Invalid usage subsets')
        fresh,cached,out=RATES[model]
        total+=((u['input_tokens']-u['cached_input_tokens'])*fresh+u['cached_input_tokens']*cached+u['output_tokens']*out)/1000000
    return total


def validate_assignment(row,expected,audit,grade,owned_responses):
    if any(row[k]!=expected[k] for k in ('task','arm','total_agent_capacity','directory')):
        raise ValueError('Assignment is not the registered ordered prefix')
    if row['grade']!=grade or row['usage']!=audit['usage'] or row['usage_by_model']!=audit['usage_by_model']:
        raise ValueError('Checkpoint disagrees with sealed grade or usage')
    if row['inference_accounting_complete']!=audit['complete'] or row['unknown_requests']!=audit['unknown_requests']:
        raise ValueError('Unknown usage coverage changed')
    if bool(row['unknown_requests'])==bool(audit['complete']):
        raise ValueError('Unknown usage was treated as complete')
    if row['total_inference_usage']!=(row['usage'] if audit['complete'] else None):
        raise ValueError('Unknown total must remain null')
    if not audit['distinct_responses'] or len({r['response_id'] for r in audit['responses']})!=audit['distinct_responses']:
        raise ValueError('Invalid positive response coverage')
    for ident in {r['response_id'] for r in audit['responses']}:
        if ident in owned_responses:raise ValueError('Response counted in multiple assignments')
        owned_responses.add(ident)
    for model,u in row['usage_by_model'].items():
        if model not in RATES or u['total_tokens']!=u['input_tokens']+u['output_tokens']:
            raise ValueError('Unsupported model or invalid total')
    for k,value in row['usage'].items():
        if value!=sum(u[k] for u in row['usage_by_model'].values()):
            raise ValueError('Model components do not sum to recorded usage')


def aggregate(rows,planned):
    return dict(completed=len(rows),planned=planned,successes=sum(r['passed'] for r in rows),
        normal_parents=sum(r['parent_status']=='completed' for r in rows),
        clean_artifacts=sum(r['artifact_policy_clean'] for r in rows),
        mean_seconds=statistics.mean(r['coding_run_seconds'] for r in rows),
        mean_coding_threads=statistics.mean(r['actual_coding_threads'] for r in rows),
        mean_credit_lower_bound=statistics.mean(r['standard_credit_scenario_lower_bound'] for r in rows),
        accounting_complete=all(r['inference_accounting_complete'] for r in rows),
        accounting_complete_cells=sum(r['inference_accounting_complete'] for r in rows),
        unknown_requests=sum(r['unknown_request_count'] for r in rows))


def matched_comparisons(cells):
    controls={(r['task'],r['total_agent_capacity']):r for r in cells if r['arm']=='native'}
    pairs=[]
    for row in cells:
        control=controls.get((row['task'],row['total_agent_capacity']))
        if row['arm']=='native' or control is None:continue
        complete=row['inference_accounting_complete'] and control['inference_accounting_complete']
        ratio=row['standard_credit_scenario_lower_bound']/control['standard_credit_scenario_lower_bound']
        bound='exact scenario ratio' if complete else 'lower bound' if control['inference_accounting_complete'] else 'upper bound' if row['inference_accounting_complete'] else 'unidentified'
        pairs.append(dict(task=row['task'],arm=row['arm'],total_agent_capacity=row['total_agent_capacity'],
            source_pass_difference=int(row['passed'])-int(control['passed']),
            run_end_time_ratio=row['coding_run_seconds']/control['coding_run_seconds'],
            both_parents_normal=row['parent_status']==control['parent_status']=='completed',
            scenario_credit_ratio=ratio if bound!='unidentified' else None,scenario_ratio_kind=bound))
    return pairs


def analyze(root,protocol_path):
    protocol=json.loads(protocol_path.read_text())
    complete=(root/'completion.json').exists()
    checkpoints=sorted(p for p in root.glob('checkpoint-*.json') if re.fullmatch(r'checkpoint-\d{3}\.json',p.name))
    source=root/'completion.json' if complete else checkpoints[-1] if checkpoints else None
    assignments=json.loads(source.read_text())['assignments'] if source else []
    state='complete' if complete else 'stopped' if (root/'stopped.json').exists() else 'incomplete'
    continuations=sorted(p for p in root.glob('continuation-*-started.json') if re.fullmatch(r'continuation-\d{3}-started\.json',p.name))
    owner=continuations[-1] if continuations else root/'queue-started.json'
    if state=='incomplete' and owner.exists():
        pid=json.loads(owner.read_text()).get('pid')
        cmd=Path(f'/proc/{pid}/cmdline')
        if cmd.exists():
            arguments=[x.decode() for x in cmd.read_bytes().split(b'\0') if x]
            if any('codex_team_memory_queue.py' in x or 'continue_team_memory_text_runtime' in x for x in arguments) and '--root' in arguments:
                actual=Path(arguments[arguments.index('--root')+1])
                if not actual.is_absolute():actual=Path(f'/proc/{pid}/cwd').resolve()/actual
                if actual.resolve()==root.resolve():state='running'
    if len(assignments)>len(protocol['assignments']) or complete and len(assignments)!=len(protocol['assignments']):
        raise ValueError('Completion does not cover the registered matrix')
    cells=[];owned_responses=set()
    for index,row in enumerate(assignments):
        audit=json.loads((root/row['directory']/'combined-usage-audit.json').read_text())
        grade=json.loads((root/row['directory']/'independent-grade/result.json').read_text())
        validate_assignment(row,protocol['assignments'][index],audit,grade,owned_responses)
        g=row['grade'];known=scenario(row['usage_by_model'])
        variant_path=root/row['directory']/'runtime-variant.json'
        variant=json.loads(variant_path.read_text()) if variant_path.exists() else {}
        embedding_rows=[]
        for path in (root/row['directory']/'memory').rglob('*.jsonl'):
            if path.name not in ('inferences.jsonl','embedding-inferences.jsonl'):continue
            embedding_rows.extend(json.loads(line) for line in path.read_bytes().split(b'\n') if line)
        observed_embeddings=[r for r in embedding_rows if r.get('local_embedding_inferences')==1]
        cells.append(dict(task=row['task'],arm=row['arm'],total_agent_capacity=row['total_agent_capacity'],
            directory=row['directory'],runtime_variant='original-reviewed-runtime' if index<12 else 'security-amended-text-only-002',
            native_startup_timeout_seconds=variant.get('pre_model_rpc_timeout_seconds',20),
            passed=g['passed'],artifact_policy_clean=g['artifact_policy_clean'],
            junit=g['junit'],observed_pass_fraction=g['observed_pass_fraction'],parent_status=row['parent_status'],
            coding_run_seconds=row['wall_seconds'],actual_coding_threads=sum(s['model']=='gpt-6.1-sol' for s in audit['sessions'].values()),
            maintenance_sessions=sum(s['model']=='gpt-6-luna' for s in audit['sessions'].values()),
            inference_accounting_complete=row['inference_accounting_complete'],
            native_usage_lower_bound=row['usage'],native_usage_by_model=row['usage_by_model'],
            total_inference_usage=row['total_inference_usage'],unknown_request_count=len(row['unknown_requests']),
            observed_local_embedding_inferences=len(observed_embeddings),
            summed_recorded_embedding_seconds=sum(r['seconds'] for r in observed_embeddings),
            local_embedding_cost=None,
            local_embedding_coverage='adapter callback receipts; no-receipt count is not proof of zero service computation',
            standard_credit_scenario_lower_bound=known,
            standard_credit_scenario_total=known if row['inference_accounting_complete'] else None,
            end_category='token_budget' if 'token threshold' in (row.get('generation_error') or '') else
                'deadline' if 'TimeoutError' in (row.get('generation_error') or '') else
                'normal' if row['parent_status']=='completed' else 'other_noncompletion'))
    groups=[]
    for arm in protocol['arms']:
        for capacity in protocol['capacities']:
            rows=[r for r in cells if r['arm']==arm and r['total_agent_capacity']==capacity]
            if not rows:continue
            groups.append(dict(arm=arm,total_agent_capacity=capacity,**aggregate(rows,len(protocol['tasks']))))
    arms=[]
    for arm in protocol['arms']:
        rows=[r for r in cells if r['arm']==arm]
        if rows:arms.append(dict(arm=arm,**aggregate(rows,len(protocol['tasks'])*len(protocol['capacities']))))
    return dict(at=datetime.now(timezone.utc).isoformat(),state=state,completed=len(cells),planned=len(protocol['assignments']),
        kind='separate memory-aware development extension; interim until all registered assignments end',cells=cells,groups=groups,arms=arms,
        matched_native_comparisons=matched_comparisons(cells),
        audit=dict(distinct_completed_responses=len(owned_responses),ordered_protocol_membership_verified=True,
            sealed_grades_and_metering_verified=True,source_passes=sum(r['passed'] for r in cells),
            normal_parents=sum(r['parent_status']=='completed' for r in cells),
            complete_usage_cells=sum(r['inference_accounting_complete'] for r in cells),
            unknown_requests=sum(r['unknown_request_count'] for r in cells)),
        pricing=dict(unit='Published Standard-rate scenario credits, not measured allowance or cash',rates_per_million=RATES,
            sol_source='experiments/codex-team-knowledge-001/pricing-scenario-001.json (11 November)',
            luna_source='docs/research/repository-memory-wave-a-results.md (rates checked 10 November)',
            note='Fixed dated scenarios, not new quotes. Cached input counted once; parent/workers/all maintenance included.'),
        subscription_cash_expense=None,quota_savings=None,
        limitations=['Reused two-library development sample, one attempt per cell; not held-out evidence.',
            'Do not compare incomplete task subsets or pool with earlier differently instructed runs.',
            'Unknown usage is null; overlapping lower cost bounds cannot rank unknown totals.',
            'Coding-run time includes in-agent memory operations; setup/replay/local monetary costs and research overhead are separate.',
            'Publication, exact peer exposure and useful checked action require separate trace evidence.'])


def publish(result,output):
    output.mkdir(parents=True,exist_ok=True)
    (output/'memory-aware-results.json').write_text(json.dumps(result,indent=2)+'\n')
    columns=['directory','task','arm','total_agent_capacity','runtime_variant','native_startup_timeout_seconds','passed','artifact_policy_clean','parent_status','end_category',
             'coding_run_seconds','actual_coding_threads','maintenance_sessions','inference_accounting_complete',
             'unknown_request_count','standard_credit_scenario_lower_bound','standard_credit_scenario_total']
    with (output/'memory-aware-cells.csv').open('w',newline='') as stream:
        writer=csv.DictWriter(stream,fieldnames=columns);writer.writeheader()
        for row in result['cells']:writer.writerow({k:row[k] for k in columns})
    lines=['# Memory-aware team comparison', '',
        f"Status: **{result['state']}**, **{result['completed']}/{result['planned']} assignments recorded**. Separate development extension; historical studies remain unchanged.", '',
        'This table includes all completed cells. Rows with fewer than two libraries are incomplete subsets, not matched comparative estimates.', '',
        f"Measurement snapshot: {result['at']}.", '',
        '| Arm | Capacity | Completed / planned | Verified sources | Normal parents | Mean run-end seconds | Mean actual coding threads | Mean Standard scenario credits |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for g in result['groups']:
        prefix='' if g['accounting_complete'] else '≥'
        lines.append(f"| {g['arm']} | {g['total_agent_capacity']} | {g['completed']}/{g['planned']} | {g['successes']}/{g['completed']} | {g['normal_parents']}/{g['completed']} | {g['mean_seconds']:.1f} | {g['mean_coding_threads']:.1f} | {prefix}{g['mean_credit_lower_bound']:.4f} |")
    lines+=['','All model-rate amounts include recorded coding and Luna maintenance inference. Unknown requests make costs lower bounds. These are dated pricing scenarios, not cash or quota measurements. Preparation, independent replay, local compute and research overhead are additional.', '',
        '[Full allowlisted measurements](memory-aware-results.json), [per-cell CSV](memory-aware-cells.csv), [protocol](../../../experiments/codex-team-knowledge-001/memory-aware-extension-protocol-001.json), [experiment appendix](appendix.md).', '',
        'This two-library development matrix cannot establish a general memory-system advantage, held-out transfer or causal knowledge benefit. A passing artifact and normal parent completion are distinct outcomes.']
    (output/'memory-aware-results.md').write_text('\n'.join(lines)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True);parser.add_argument('--protocol',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();value=analyze(args.root.resolve(),args.protocol);publish(value,args.output)
    print(json.dumps({k:value[k] for k in ('state','completed','planned')}))
