#!/usr/bin/env python3
"""One registered Pro preflight/replay and four-arm block; never retry inference."""
import argparse
import hashlib
import fcntl
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


def witness_replay_passed(pre_reward, reward, replay, witness):
    # git diff --stat omits newly created untracked files. git apply --verbose
    # reports the exact successfully applied path even for that legitimate case.
    applied_line = f"Applied patch {witness} cleanly."
    return (pre_reward == 0 and reward == 0 and replay.get('apply_rc') == 0
            and applied_line in replay.get('apply_out', '').splitlines())


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


def audit_thread_deltas(records):
    previous = {}
    for line in (records/'controller/events.jsonl').read_text().splitlines():
        event = json.loads(line)
        if event.get('event') != 'response':
            continue
        if (event.get('status') != 'completed' or event.get('usage_accounting_issues')
                or event.get('usage_scope') != 'thread_cumulative' or not event.get('thread_id')):
            raise RuntimeError('Reusable setup needs completed, metered cumulative-thread responses')
        key = (event['model'], event['thread_id'])
        prior = previous.get(key, {})
        for field in personal.USAGE_FIELDS:
            current, delta = event['usage'][field], event['usage_delta'][field]
            before = prior.get(field, 0)
            if current is None or before is None:
                if delta is not None:
                    raise RuntimeError('Unknown cumulative usage cannot produce a known delta')
            elif (type(current) is not int or type(before) is not int
                  or current < before or delta != current-before):
                raise RuntimeError('Cumulative-thread token delta does not reconcile')
        previous[key] = event['usage']


def audit_reused_setup(protocol, current_image):
    """Read-only audit; never executes a job, reseals an artifact, or calls a model."""
    reuse = protocol['reuse_setup']
    inventory = reuse['artifacts_sha256']
    for name, expected in inventory.items():
        if digest(name) != expected:
            raise RuntimeError('Reusable setup inventory changed: '+name)
    def bound(path):
        path = Path(path).resolve()
        if inventory.get(str(path)) != digest(path):
            raise RuntimeError('Unbound or changed reusable setup artifact: '+str(path))
        return path
    source_protocol_path = bound(reuse['source_protocol'])
    source = json.loads(source_protocol_path.read_text())
    old = Path(reuse['source_output']).resolve()
    if source['task_id'] != protocol['task_id']:
        raise RuntimeError('Reusable setup belongs to a different task')
    if source['controls_summary'] != protocol['controls_summary']:
        raise RuntimeError('Reusable setup controls changed')
    if list(old.glob('first-block-*')) or list((old/'jobs').glob('first-block-*')):
        raise RuntimeError('Prior scored assignment exists or is uncertain; do not repeat it')
    queue = json.loads(bound(old/'queue.json').read_text())
    if queue['protocol_sha256'] != digest(source_protocol_path):
        raise RuntimeError('Original setup protocol binding does not match')
    for name, expected in source['source_sha256'].items():
        if digest(name) == expected:
            continue
        change = reuse.get('allowed_source_changes', {}).get(name)
        if (name not in (str(ROOT/'scripts/continue_pro_rescue.py'),
                         str(ROOT/'src/ttgl/router_development.py')) or not change
                or change['from_sha256'] != expected
                or change['to_sha256'] != digest(name)
                or protocol['source_sha256'].get(name) != digest(name)
                or digest(bound(change['archived_source'])) != expected):
            raise RuntimeError('Original setup source changed without an audited amendment: '+name)
    image = json.loads(bound(old/'image-binding.json').read_text())
    if image['image_id'] != current_image:
        raise RuntimeError('Reusable setup image differs from current task image')
    def native(job):
        paths = list((old/'jobs'/job).glob('*/result.json'))
        if len(paths) != 1:
            raise RuntimeError('Ambiguous reusable native job: '+job)
        path = bound(paths[0])
        value = json.loads(path.read_text())
        if (value.get('exception_info') or value.get('task_name', '').split('/')[-1] != protocol['task_id']
                or value.get('verifier_result', {}).get('rewards', {}).get('reward') != 0):
            raise RuntimeError('Reusable setup has an invalid task or negative control grade')
        return path, value
    native_path, original = native('native-preflight-001')
    replay_path, replay_native = native('native-preflight-replay-001')
    meta = original['agent_result']['metadata']
    records = Path(meta['private_records_path']).resolve()
    if not records.is_relative_to(Path(source['private_records_root']).resolve()):
        raise RuntimeError('Reusable private records are outside their registered root')
    for path in records.rglob('*'):
        if path.is_file() and path.name != '.lock':
            bound(path)
    if digest(records/'controller/manifest.json') != meta['manifest_sha256']:
        raise RuntimeError('Reusable native manifest changed')
    manifest = audit_native(records)
    audit_thread_deltas(records)
    models = {'gpt-6-luna', 'gpt-6.1-sol'}
    if (set(manifest['usage_by_model']) != models or manifest['status'] != 'completed_ungraded'
            or manifest.get('usage_accounting_issues') or manifest['expert_calls'] < 1):
        raise RuntimeError('Reusable setup model identity, completion, or consultation is invalid')
    for model in models:
        usage = manifest['usage_by_model'][model]['usage']
        if any(type(usage[k]) is not int or usage[k] <= 0 for k in ('input_tokens', 'output_tokens')):
            raise RuntimeError('Reusable setup needs positive per-model metering')
        native_usage = original['agent_result']['model_usage'][model]
        if any(native_usage[k] != usage[field] for k, field in
               [('n_input_tokens', 'input_tokens'), ('n_cache_tokens', 'cached_input_tokens'),
                ('n_output_tokens', 'output_tokens')]):
            raise RuntimeError('Native and private per-model usage disagree')
    final = records/'final.patch'
    sealed = records/'sealed-replay-source'/protocol['task_id']
    seal = json.loads(bound(sealed/'seal.json').read_text())
    if (not final.stat().st_size or digest(final) != meta['final_patch_sha256']
            or seal['native_result_sha256'] != digest(native_path)
            or digest(sealed/'agent/model.patch') != digest(final)):
        raise RuntimeError('Reusable sealed final patch provenance failed')
    for name, expected in seal['patches_sha256'].items():
        if Path(name).name != name or digest(bound(sealed/'agent'/name)) != expected:
            raise RuntimeError('Reusable sealed patch changed')
    snapshot = json.loads((records/'pre-handoff.json').read_text())
    if digest(records/'pre-handoff.patch') != snapshot['patch_sha256']:
        raise RuntimeError('Reusable pre-handoff patch changed')
    preflight = meta['preflight']
    if json.loads((records/'preflight.json').read_text()) != preflight:
        raise RuntimeError('Private preflight does not match native metadata')
    observed = preflight['boundary_observations']
    if (preflight['status'] != 'real_actor_native_handoff_preflight_passed_replay_still_required'
            or observed['git_status'] != '' or observed['outside_head_commits'] != 0
            or any(observed[k] is not False for k in
                   ('private_path_visible', 'public_endpoint_reachable', 'witness_ignored'))):
        raise RuntimeError('Original actor boundary did not pass')
    replay = json.loads(bound(replay_path.parent/'agent/replay.json').read_text())
    if (Path(replay['patch']).resolve() != (sealed/'agent/model.patch').resolve()
            or not witness_replay_passed(0, 0, replay, preflight['witness'])):
        raise RuntimeError('Reusable witness replay did not pass')
    return {'status': 'completed_setup_reused_after_evidence_audit',
            'source_output': str(old), 'native_result': str(native_path),
            'native_grade': 0, 'fresh_grade': 0, 'expert_calls': manifest['expert_calls'],
            'setup_usage': manifest['usage'], 'setup_usage_by_model': manifest['usage_by_model'],
            'new_setup_model_calls': 0, 'benchmark_accuracy_claim': False,
            'artifact_count': len(inventory), 'fresh_actor_boundary_required': True}


def setup_stage(protocol, current_image, fresh_setup):
    # Selecting reuse is fail-closed: invalid evidence never falls back to inference.
    if 'reuse_setup' in protocol:
        if protocol['reuse_setup'].get('scope') == 'transport_metering_only':
            audit_controls(protocol)
            reuse = protocol['reuse_setup']
            source = json.loads(Path(reuse['source_protocol']).read_text())
            image = json.loads((Path(reuse['source_output'])/'image-binding.json').read_text())
            original_context = {**protocol, 'task_id': source['task_id'],
                                'controls_summary': source['controls_summary']}
            receipt = audit_reused_setup(original_context, image['image_id'])
            receipt.update(reuse_scope='native_transport_and_metering_only',
                           original_task_id=source['task_id'], target_task_id=protocol['task_id'],
                           target_image_id=current_image, target_controls_audited=True,
                           target_task_quality_claim=False)
            return receipt
        return audit_reused_setup(protocol, current_image)
    if protocol.get('setup_mode') != 'fresh_authorized':
        raise RuntimeError('Register explicit setup reuse or fresh setup authorization')
    return fresh_setup()


def audit_controls(protocol):
    summary_path = Path(protocol['controls_summary'])
    if protocol['source_sha256'].get(str(summary_path)) != digest(summary_path):
        raise RuntimeError('Target control summary must be frozen before inference')
    summary = json.loads(summary_path.read_text())
    if (summary['status'] != 'one_task_empty_reference_controls_passed'
            or len(summary['controls']) != 2
            or {r['agent'] for r in summary['controls']} != {'nop', 'oracle'}):
        raise RuntimeError('Require both independent target-task controls')
    for row in summary['controls']:
        path = Path(row['native_result'])
        if digest(path) != row['native_result_sha256']:
            raise RuntimeError('Target control native evidence changed')
        native = json.loads(path.read_text())
        if (native.get('exception_info') or native['task_name'].split('/')[-1] != protocol['task_id']
                or native['verifier_result']['rewards']['reward'] != (0 if row['agent']=='nop' else 1)):
            raise RuntimeError('Target task identity or control grade is invalid')
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--protocol', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    protocol = json.loads(args.protocol.read_text())
    lock_path = ROOT/'artifacts'/('pro-pipeline-'+hashlib.sha256(
        protocol.get('task_id', 'unregistered').encode()).hexdigest()[:16]+'.lock')
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    run_lock = lock_path.open('a+')
    fcntl.flock(run_lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
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
        if protocol.get('require_target_controls'):
            audit_controls(protocol)
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
        def fresh_setup():
            pre_path,pre_native,pre_reward = job('native-preflight-001','ttgl.harbor_preflight:NativeProPreflight',
                                                [('private_records_root',records_root)])
            pre_meta = pre_native['agent_result']['metadata']
            if pre_meta.get('preflight',{}).get('status') != 'real_actor_native_handoff_preflight_passed_replay_still_required':
                raise RuntimeError('Real actor preflight metadata missing')
            sealed,manifest,_ = sealed_source(pre_path,pre_native)
            reward,replay_json = replay('native-preflight-replay-001',sealed,'model.patch')
            witness = pre_meta['preflight']['witness']
            if not witness_replay_passed(pre_reward, reward, replay_json, witness):
                raise RuntimeError('Witness replay did not preserve the expected negative task control')
            return {'status':'real_actor_native_handoff_and_pristine_witness_replay_passed',
                'native_result':str(pre_path),'native_grade':pre_reward,'fresh_grade':reward,
                'expert_calls':manifest['expert_calls'],'setup_usage':manifest['usage'],
                'benchmark_accuracy_claim':False}
        write(out/'real-preflight.json', setup_stage(protocol, frozen_image, fresh_setup))

        rates = json.loads(Path(protocol['rate_scenario']).read_text())['models']
        rows = []
        for arm in protocol['first_block_order']:
            if protocol.get('assignment_claim'):
                write(Path(protocol['assignment_claim']), {'protocol_sha256': digest(args.protocol),
                      'task_id': task_id, 'arm': arm, 'status': 'claimed_before_scored_invocation'})
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
