#!/usr/bin/env python3
"""One registered Pro preflight/replay and four-arm block; never retry inference."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import tomllib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from ttgl import handoff_metrics, personal


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def audit_native(records):
    manifest = json.loads((records/'controller/manifest.json').read_text())
    events = [json.loads(s) for s in (records/'controller/events.jsonl').read_text().splitlines()]
    requests = [r for r in events if r['event']=='request']
    responses = [r for r in events if r['event']=='response']
    if (len({r['request_id'] for r in requests}) != len(requests)
            or len({r['request_id'] for r in responses}) != len(responses)
            or {r['request_id'] for r in requests} != {r['request_id'] for r in responses}):
        raise RuntimeError('Unreconciled or repeated native invocation identity')
    if {r['model'] for r in responses} != set(manifest['usage_by_model']):
        raise RuntimeError('An invoked model is missing from native accounting')
    def total(rows, field):
        values = [r['usage_delta'][field] for r in rows]
        return None if any(v is None for v in values) else sum(values)
    for field in personal.USAGE_FIELDS:
        if total(responses, field) != manifest['usage'][field]:
            raise RuntimeError('Native total usage does not reconcile')
    for model, row in manifest['usage_by_model'].items():
        for field in personal.USAGE_FIELDS:
            if total([r for r in responses if r['model']==model],field) != row['usage'][field]:
                raise RuntimeError('Native per-model usage does not reconcile')
    if any(r.get('tool_events') for r in responses if r['kind']=='expert'):
        raise RuntimeError('Context-only expert used a tool')
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    def verify():
        for path, expected in protocol['source_sha256'].items():
            if digest(path) != expected:
                raise RuntimeError('Registered pipeline source changed: '+path)
    verify()
    write(out/'queue.json', {'status':'waiting_for_existing_one_task_controls',
                            'protocol_sha256':digest(args.protocol), 'no_automatic_retries':True})
    controls = Path(protocol['controls_summary'])
    try:
        while not controls.exists():
            os.kill(protocol['controls_queue_pid'], 0)
            time.sleep(10)
        summary = json.loads(controls.read_text())
        if summary['status'] != 'one_task_empty_reference_controls_passed':
            raise RuntimeError('Prior Pro controls did not pass')
        if {r['agent'] for r in summary['controls']} != {'nop','oracle'} or len(summary['controls']) != 2:
            raise RuntimeError('Require both independent controls')
        for row in summary['controls']:
            if digest(row['native_result']) != row['native_result_sha256']:
                raise RuntimeError('Prior native control evidence changed')
            native_control = json.loads(Path(row['native_result']).read_text())
            expected = 0 if row['agent']=='nop' else 1
            if native_control.get('exception_info') or native_control['verifier_result']['rewards']['reward'] != expected:
                raise RuntimeError('Prior control grade is invalid')
        if shutil.disk_usage(ROOT).free < protocol['disk_guard_bytes']:
            raise RuntimeError('Insufficient reserved disk before Pro pipeline; no model call started')
        harbor = str(ROOT/'artifacts/harbor-runtime-001/bin/harbor')
        private = Path(protocol['private_task_root'])
        task_id = protocol['task_id']
        task_config = tomllib.loads((private/'v2/tasks'/task_id/'task.toml').read_text())
        image = task_config['environment']['docker_image']
        def image_id():
            return subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],text=True).strip()
        frozen_image = image_id()
        write(out/'image-binding.json',{'image':image,'image_id':frozen_image,
                                       'scope':'Require the same locally resolved task image through this first block'})
        env = {**os.environ, 'PYTHONPATH':str(ROOT/'src')+os.pathsep+str(private/'v2/tooling')}
        if protocol.get('docker_config'):
            env['DOCKER_CONFIG'] = protocol['docker_config']
        def job(name, agent, options=()):
            verify()
            if image_id() != frozen_image:
                raise RuntimeError('Resolved Pro task image changed; no automatic retry')
            if shutil.disk_usage(ROOT).free < protocol['disk_guard_bytes']:
                raise RuntimeError('Reserved disk unavailable before job: '+name)
            environment = (['--environment-import-path', protocol['environment_import_path']]
                           if protocol.get('environment_import_path') else ['-e', 'docker'])
            command = [harbor,'run','-p',str(private/'v2/tasks'),*environment,'-a',agent,
                       '-n','1','--n-attempts','1','--max-retries','0',
                       '--jobs-dir',str(out/'jobs'),'--job-name',name]
            for key, value in options:
                command += ['--ak',key+'='+str(value)]
            write(out/(name+'-invocation.json'), {'command':command,'state':'registered_before_invocation'})
            with (out/(name+'.stdout.txt')).open('x') as log:
                result = subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,env=env,timeout=9000)
            paths = list((out/'jobs'/name).glob('*/result.json'))
            if result.returncode or len(paths)!=1:
                raise RuntimeError('Native job failed or ambiguous; never replay started inference: '+name)
            if image_id() != frozen_image:
                raise RuntimeError('Resolved Pro task image changed during job')
            native = json.loads(paths[0].read_text())
            reward = (native.get('verifier_result') or {}).get('rewards',{}).get('reward')
            if native.get('exception_info') or reward not in (0,1):
                raise RuntimeError('Native exception or unknown grade: '+name)
            return paths[0],native,int(reward)

        def sealed_source(native_path, native):
            meta = native['agent_result']['metadata']
            records = Path(meta['private_records_path']).resolve()
            if (not records.is_relative_to(records_root.resolve())
                    or native['task_name'].split('/')[-1] != task_id
                    or digest(records/'controller/manifest.json') != meta['manifest_sha256']):
                raise RuntimeError('Native task/manifest provenance does not match private records')
            manifest = audit_native(records)
            final = records/'final.patch'
            if digest(final) != meta['final_patch_sha256']:
                raise RuntimeError('Authoritative final patch changed')
            sealed = records/'sealed-replay-source'
            folder = sealed/task_id
            write(folder/'result.json', {'task_name':native['task_name']})
            (folder/'agent').mkdir()
            shutil.copyfile(final,folder/'agent/model.patch')
            if (records/'pre-handoff.json').exists():
                snapshot = json.loads((records/'pre-handoff.json').read_text())
                if digest(records/'pre-handoff.patch') != snapshot['patch_sha256']:
                    raise RuntimeError('Authoritative pre-handoff patch changed')
                shutil.copyfile(records/'pre-handoff.patch',folder/'agent/pre-handoff.patch')
            write(folder/'seal.json', {'native_result_sha256':digest(native_path),
                 'patches_sha256':{p.name:digest(p) for p in (folder/'agent').iterdir()}})
            attempted = sum(json.loads(s).get('event')=='request' and json.loads(s).get('kind')=='expert'
                            for s in (records/'controller/events.jsonl').read_text().splitlines())
            return sealed,manifest,attempted

        def replay(name, sealed, patch_name):
            path,native,reward = job(name,'patch_replay:PatchReplayAgent',
                                     [('source_job',sealed),('patch_name',patch_name)])
            replay_json = json.loads((path.parent/'agent/replay.json').read_text())
            patch = next(sealed.glob('*/agent/'+patch_name))
            if patch.stat().st_size and replay_json.get('apply_rc') != 0:
                raise RuntimeError('Nonempty patch did not apply on pristine image')
            return reward,replay_json

        records_root = Path(protocol['private_records_root'])
        pre_path,pre_native,pre_reward = job('native-preflight-001','ttgl.harbor_preflight:NativeProPreflight',
                                            [('private_records_root',records_root)])
        pre_meta = pre_native['agent_result']['metadata']
        if pre_meta.get('preflight',{}).get('status') != 'real_actor_native_handoff_preflight_passed_replay_still_required':
            raise RuntimeError('Real actor preflight metadata missing')
        sealed,manifest,_ = sealed_source(pre_path,pre_native)
        reward,replay_json = replay('native-preflight-replay-001',sealed,'model.patch')
        witness = pre_meta['preflight']['witness']
        if pre_reward != 0 or reward != 0 or witness not in replay_json['post_apply_diffstat']:
            raise RuntimeError('Witness replay did not preserve the expected negative task control')
        write(out/'real-preflight.json', {'status':'real_actor_native_handoff_and_pristine_witness_replay_passed',
            'native_result':str(pre_path),'native_grade':pre_reward,'fresh_grade':reward,
            'expert_calls':manifest['expert_calls'],'setup_usage':manifest['usage'],
            'benchmark_accuracy_claim':False})

        rates = json.loads(Path(protocol['rate_scenario']).read_text())['models']
        rows = []
        for arm in protocol['first_block_order']:
            condition = arm if arm in ('small','large') else 'personal'
            mode = 'required_review' if arm=='required_review' else 'verification'
            path,native,initial = job('first-block-'+arm,protocol.get('agent_import_path', 'ttgl.harbor_routing_agent:RoutingDiagnosticCodex'),
                [('private_records_root',records_root),('condition',condition),('policy',mode)])
            sealed,manifest,attempted = sealed_source(path,native)
            final,_ = replay('first-block-'+arm+'-fresh',sealed,'model.patch')
            prior = None
            if (sealed/task_id/'agent/pre-handoff.patch').exists():
                prior,_ = replay('first-block-'+arm+'-pre-handoff',sealed,'pre-handoff.patch')
                prior = bool(prior)
            cost = 0.0
            for model, record in manifest['usage_by_model'].items():
                usage,rate = record['usage'],rates[model]
                if any(usage[k] is None for k in ('input_tokens','cached_input_tokens','output_tokens')):
                    cost = None
                    break
                cost += ((usage['input_tokens']-usage['cached_input_tokens'])*rate['input_per_million']
                         +usage['cached_input_tokens']*rate['cached_input_per_million']
                         +usage['output_tokens']*rate['output_per_million'])/1e6
            rows.append({'task_id':task_id,'arm':arm,'resolved':bool(final),'initial_grade':initial,
                'expert_calls':manifest['expert_calls'],'expert_requests_attempted':attempted,'pre_handoff_resolved':prior,
                'cost_scenario_usd':cost,'native_result':str(path),
                'private_manifest_sha256':digest(Path(native['agent_result']['metadata']['private_records_path'])/'controller/manifest.json')})
            write(out/('completed-'+arm+'.json'),rows[-1])
        write(out/'records.json',rows)
        if protocol.get('router_only_development'):
            if len(rows) != 1 or rows[0]['arm'] != 'optional':
                raise RuntimeError('Router-only unit requires one voluntary router assignment')
            write(out/'router-observation.json', {'status': 'development_observation_not_matched_comparison',
                  'assignment': rows[0], 'next_step': 'Inspect visible checks, decision records and consultation before next task or prompt'})
        else:
            write(out/'paired-rescue.json',handoff_metrics.summarize(rows, arms=tuple(protocol.get('analysis_arms', handoff_metrics.ARMS))))
        write(out/'completion.json', {'status':'registered_first_block_completed_review_cost_runtime_before_expanding',
              'development_assignments':len(rows),'full_twelve_task_run_started':False,'validation_started':False})
    except BaseException as exc:
        write(out/'stopped.json', {'status':'stopped_preserve_all_attempts_do_not_retry_blindly',
                                 'error_type':type(exc).__name__,'message':str(exc)})
        raise


if __name__ == '__main__':
    main()
