#!/usr/bin/env python3
"""Audit one complete matched development pair; never execute models or graders."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('episode_analysis',ROOT/'scripts/analyze_router_episode.py')
episode=importlib.util.module_from_spec(spec)
spec.loader.exec_module(episode)
pipeline=episode.pipeline


def analyze(study, protocol_path):
    protocol=json.loads(protocol_path.read_text())
    pipeline.validate_matched_pair(protocol)
    if not protocol.get('matched_pair_development'):
        raise ValueError('Require registered matched pair')
    completion=json.loads((study/'completion.json').read_text())
    rows=json.loads((study/'records.json').read_text())
    if completion['development_assignments']!=2:
        raise ValueError('Incomplete matched assignment count')
    diagnostic=pipeline.matched_pair_observation(rows)
    rates=json.loads(Path(protocol['rate_scenario']).read_text())['models']
    arms={}
    exports={}
    for row in rows:
        arm=row['arm'];native_path=Path(row['native_result'])
        native=json.loads(native_path.read_text())
        fresh_paths=list((study/'jobs'/('first-block-'+arm+'-fresh')).glob('*/result.json'))
        if len(fresh_paths)!=1:raise ValueError('Missing or ambiguous independent grade')
        fresh_path=fresh_paths[0];fresh=json.loads(fresh_path.read_text())
        for report in [native,fresh]:
            if report.get('exception_info') or report['task_name'].split('/')[-1]!=protocol['task_id']:
                raise ValueError('Infrastructure error or wrong task')
        grade=fresh['verifier_result']['rewards']['reward']
        if grade not in (0,1) or row['resolved']!=bool(grade):raise ValueError('Grade disagrees')
        meta=native['agent_result']['metadata'];records=Path(meta['private_records_path'])
        manifest=pipeline.audit_native(records);pipeline.audit_thread_deltas(records)
        if (pipeline.digest(records/'controller/manifest.json')!=meta['manifest_sha256']
                or pipeline.digest(records/'controller/manifest.json')!=row['private_manifest_sha256']):
            raise ValueError('Manifest provenance disagrees')
        final=records/'final.patch';sealed=records/'sealed-replay-source'/protocol['task_id']
        seal=json.loads((sealed/'seal.json').read_text())
        replay_path=fresh_path.parent/'agent/replay.json';replay=json.loads(replay_path.read_text())
        if (pipeline.digest(final)!=meta['final_patch_sha256']
                or pipeline.digest(sealed/'agent/model.patch')!=pipeline.digest(final)
                or seal['native_result_sha256']!=pipeline.digest(native_path)
                or replay['apply_rc']!=0
                or Path(replay['patch']).resolve()!=(sealed/'agent/model.patch').resolve()):
            raise ValueError('Sealed patch/replay provenance disagrees')
        events=[json.loads(x) for x in (records/'controller/events.jsonl').read_text().splitlines()]
        requests=[e for e in events if e.get('event')=='request']
        if not requests or manifest['status']!='completed_ungraded' or manifest['usage']['input_tokens']<=0:
            raise ValueError('No completed positive-metered model work')
        if any(e['kind'] not in ('controller','expert') for e in requests):
            raise ValueError('Unexpected native role')
        attempted=sum(e['kind']=='expert' for e in requests)
        if attempted!=row['expert_requests_attempted'] or manifest['expert_calls']!=row['expert_calls']:
            raise ValueError('Consultation counts disagree')
        if arm=='large' and (attempted or any(e['model']!='gpt-6.1-sol' for e in requests)):
            raise ValueError('Standalone Sol contains another role/model')
        if arm=='optional' and any(e['model']!=('gpt-6.1-sol' if e['kind']=='expert' else 'gpt-6-luna') for e in requests):
            raise ValueError('Router model identity disagrees')
        policy=manifest['backend']['controller_policy']
        expected_common=protocol['source_sha256'][str(ROOT/'prompts/controller-v7-common.txt')]
        if policy.get('mode')!='consolidated-v7' or policy.get('common_sha256')!=expected_common:
            raise ValueError('Matched common guidance not bound')
        boundary=meta['fresh_actor_boundary']
        if boundary['status']!='fresh_actor_boundary_passed_before_router_inference':
            raise ValueError('Fresh actor boundary not confirmed')
        cost=episode.scenario_cost(manifest['usage_by_model'],rates)
        if cost is None or row['cost_scenario_usd'] is None or abs(cost-row['cost_scenario_usd'])>1e-10:
            raise ValueError('Unknown or disagreeing cost scenario')
        final_responses=[e for e in events if e.get('event')=='response' and e.get('kind')=='controller']
        arms[arm]={'assigned':1,'resolved':int(grade),'initial_grade':native['verifier_result']['rewards']['reward'],
            'cost_scenario_usd':cost,'cost_per_resolved_usd':cost if grade else None,
            'usage':manifest['usage'],'usage_by_model':manifest['usage_by_model'],
            'expert_requests':attempted,'completed_consultations':manifest['expert_calls'],
            'pre_handoff_grade':row['pre_handoff_resolved'],
            'native_requests_by_role':{k:sum(e['kind']==k for e in requests) for k in {e['kind'] for e in requests}},
            'latency_seconds':{'native_model_and_tools':manifest['elapsed_seconds'],
                'actor':episode.seconds(native['agent_execution']['started_at'],native['agent_execution']['finished_at']),
                'generation_start_to_fresh_grade':episode.seconds(native['started_at'],fresh['finished_at'])},
            'final_response':json.loads(final_responses[-1]['text']),
            'provenance':{str(p):pipeline.digest(p) for p in [protocol_path,native_path,fresh_path,
                replay_path,records/'controller/manifest.json',records/'controller/events.jsonl',
                records/'visible-tool-trace.jsonl',final,sealed/'seal.json']}}
        exports[arm]={'native-result.json':native_path,'fresh-result.json':fresh_path,
                     'replay.json':replay_path,'manifest.json':records/'controller/manifest.json',
                     'final.patch':final,'visible-tool-trace.jsonl':records/'visible-tool-trace.jsonl'}
        if (records/'pre-handoff.patch').exists():
            pre_paths=list((study/'jobs'/('first-block-'+arm+'-pre-handoff')).glob('*/result.json'))
            if len(pre_paths)!=1:raise ValueError('Missing pre-handoff grade')
            pre_path=pre_paths[0];pre=json.loads(pre_path.read_text());pre_replay_path=pre_path.parent/'agent/replay.json';pre_replay=json.loads(pre_replay_path.read_text())
            if (pre.get('exception_info') or pre['task_name']!=native['task_name']
                    or pre['verifier_result']['rewards']['reward'] not in (0,1)
                    or pre_replay['apply_rc']!=0 or pipeline.digest(pre_replay['patch'])!=pipeline.digest(records/'pre-handoff.patch')
                    or bool(pre['verifier_result']['rewards']['reward'])!=row['pre_handoff_resolved']):
                raise ValueError('Pre-handoff provenance disagrees')
            exports[arm].update({'pre-handoff.patch':records/'pre-handoff.patch',
                                'pre-handoff-result.json':pre_path,'pre-handoff-replay.json':pre_replay_path})
    return {'status':'audited_development_pair_not_final_target_evidence','task_id':protocol['task_id'],
            'policy':'v7','arms':arms,'comparison':diagnostic,'actual_cash_saving':None,
            'subscription_quota_saving':None,'validation_tasks_used':0,
            'uncertainty':'One selected public development task, not population equivalence, transfer or confirmatory90% target proof'},exports


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--study',type=Path,required=True)
    parser.add_argument('--protocol',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();summary,exports=analyze(args.study.resolve(),args.protocol.resolve())
    args.output.mkdir(parents=True,exist_ok=False)
    pipeline.write(args.output/'summary.json',summary)
    for arm,files in exports.items():
        target=args.output/arm;target.mkdir()
        for name,source in files.items():shutil.copyfile(source,target/name)
    pipeline.write(args.output/'artifact-manifest.json',{'files':{str(p.relative_to(args.output)):pipeline.digest(p) for p in args.output.rglob('*') if p.is_file()}})
    print(json.dumps(summary['comparison']))


if __name__=='__main__':main()
