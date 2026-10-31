#!/usr/bin/env python3
"""Audit one completed router-only episode without executing models or graders."""
import argparse
from datetime import datetime
from decimal import Decimal
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('pro_pipeline_audit', ROOT/'scripts/continue_pro_rescue.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


def scenario_cost(models, rates):
    value = Decimal(0)
    for model, record in models.items():
        usage, rate = record['usage'], rates[model]
        if any(usage[k] is None for k in ('input_tokens','cached_input_tokens','output_tokens')):
            return None
        if not 0 <= usage['cached_input_tokens'] <= usage['input_tokens']:
            raise ValueError('Cached input must be included in total input')
        value += ((usage['input_tokens']-usage['cached_input_tokens'])*Decimal(str(rate['input_per_million']))
                  + usage['cached_input_tokens']*Decimal(str(rate['cached_input_per_million']))
                  + usage['output_tokens']*Decimal(str(rate['output_per_million'])))/Decimal(1000000)
    return float(value)


def seconds(start, end):
    return (datetime.fromisoformat(end.replace('Z','+00:00'))-
            datetime.fromisoformat(start.replace('Z','+00:00'))).total_seconds()


def analyze(study, protocol_path):
    protocol = json.loads(protocol_path.read_text())
    completion = json.loads((study/'completion.json').read_text())
    if completion['development_assignments'] != 1 or not protocol['router_only_development']:
        raise ValueError('Require exactly one completed router-only development assignment')
    row = json.loads((study/'completed-optional.json').read_text())
    native_path = Path(row['native_result'])
    native = json.loads(native_path.read_text())
    fresh_paths = list((study/'jobs/first-block-optional-fresh').glob('*/result.json'))
    if len(fresh_paths) != 1:
        raise ValueError('Require one independent fresh grade')
    fresh_path = fresh_paths[0]
    fresh = json.loads(fresh_path.read_text())
    for value in (native, fresh):
        if value.get('exception_info') or value['task_name'].split('/')[-1] != protocol['task_id']:
            raise ValueError('Task mismatch or evaluator infrastructure failure')
    final_grade = fresh['verifier_result']['rewards']['reward']
    if final_grade not in (0,1) or row['resolved'] != bool(final_grade):
        raise ValueError('Independent grade and assignment outcome disagree')
    meta = native['agent_result']['metadata']
    records = Path(meta['private_records_path'])
    manifest = pipeline.audit_native(records)
    pipeline.audit_thread_deltas(records)
    final = records/'final.patch'
    sealed = records/'sealed-replay-source'/protocol['task_id']
    seal = json.loads((sealed/'seal.json').read_text())
    replay = json.loads((fresh_path.parent/'agent/replay.json').read_text())
    if (pipeline.digest(final) != meta['final_patch_sha256']
            or pipeline.digest(sealed/'agent/model.patch') != pipeline.digest(final)
            or seal['native_result_sha256'] != pipeline.digest(native_path)
            or replay['apply_rc'] != 0
            or Path(replay['patch']).resolve() != (sealed/'agent/model.patch').resolve()):
        raise ValueError('Final patch and independent replay provenance disagree')
    events = [json.loads(s) for s in (records/'controller/events.jsonl').read_text().splitlines()]
    requests = [r for r in events if r.get('event')=='request']
    attempts = sum(r['kind']=='expert' for r in requests)
    if attempts != row['expert_requests_attempted'] or manifest['expert_calls'] != row['expert_calls']:
        raise ValueError('Consultation accounting disagrees')
    controllers = [r for r in events if r.get('event')=='response' and r.get('kind')=='controller']
    final_response = json.loads(controllers[-1]['text'])
    trace = records/'visible-tool-trace.jsonl'
    tools = [json.loads(s) for s in trace.read_text().splitlines()]
    rates = json.loads(Path(protocol['rate_scenario']).read_text())['models']
    cost = scenario_cost(manifest['usage_by_model'], rates)
    if cost is not None and abs(cost-row['cost_scenario_usd']) > 1e-10:
        raise ValueError('Recorded and independently recomputed cost scenario disagree')
    setup = json.loads((study/'real-preflight.json').read_text())
    outcome = ('solved_without_consultation' if final_grade else 'failed_without_consultation')
    if attempts:
        outcome = ('failed_consultation_request' if not manifest['expert_calls'] else
                   ('solved_after_consultation' if final_grade else 'failed_after_completed_consultation'))
    initial_grade = native['verifier_result']['rewards']['reward']
    return {
        'status':'audited_single_development_episode','task_id':protocol['task_id'],
        'assigned':1,'resolved':int(final_grade),'initial_grade':initial_grade,'fresh_grade':final_grade,
        'observed_success_fraction':float(final_grade),
        'illustrative_exact_binomial_95_interval':([0.025,1.0] if final_grade else [0.0,0.975]),
        'uncertainty':'Illustrative iid binomial interval only; one selected public development task is not a population sample or evidence of reliable routing/noninferiority.',
        'outcome_class':outcome,'expert_requests_attempted':attempts,
        'completed_consultations':manifest['expert_calls'],
        'native_requests_by_role':{kind:sum(r['kind']==kind for r in requests)
                                   for kind in sorted({r['kind'] for r in requests})},
        'usage':manifest['usage'],'usage_by_model':manifest['usage_by_model'],
        'published_rate_scenario_cost_per_assigned_usd':cost,
        'published_rate_scenario_cost_per_resolved_usd':cost if final_grade else None,
        'actual_cash_cost_usd':None,'subscription_quota_savings':None,
        'accuracy_retention_vs_sol':None,'saving_vs_matched_sol':None,
        'cost_scope':'All episode controller/router/expert/integration inference; frozen historical token rates, not invoice or full deployment cost.',
        'setup_already_completed_reused':{'new_model_calls':setup['new_setup_model_calls'],
          'usage':setup['setup_usage'],'historical_scenario_cost_usd':scenario_cost(setup['setup_usage_by_model'],rates)},
        'latency_seconds':{'native_model_and_tools':manifest.get('elapsed_seconds'),
          'native_actor_phase':seconds(native['agent_execution']['started_at'],native['agent_execution']['finished_at']),
          'generation_environment_and_initial_grading':seconds(native['started_at'],native['finished_at']),
          'independent_fresh_replay':seconds(fresh['started_at'],fresh['finished_at']),
          'generation_start_to_fresh_grade':seconds(native['started_at'],fresh['finished_at'])},
        'visible_tool_requests':sum(r['event']=='tool_request' for r in tools),
        'final_controller_response':final_response,
        'fresh_actor_boundary':meta['fresh_actor_boundary'],
        'pre_handoff_grade':row['pre_handoff_resolved'],
        'provenance':{str(p):pipeline.digest(p) for p in
           [protocol_path,native_path,fresh_path,records/'controller/manifest.json',
            records/'controller/events.jsonl',trace,final,sealed/'seal.json',
            fresh_path.parent/'agent/replay.json',Path(protocol['rate_scenario'])]},
        'validation_tasks_used':0,
    }


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,required=True)
    parser.add_argument('--protocol',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    result=analyze(args.study.resolve(),args.protocol.resolve())
    args.output.mkdir(parents=True,exist_ok=False)
    pipeline.write(args.output/'summary.json', result)
    print(json.dumps({k:result[k] for k in ['resolved','outcome_class','published_rate_scenario_cost_per_assigned_usd']}))


if __name__=='__main__':main()
