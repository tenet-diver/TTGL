"""Exercise reuse against raw evidence; corrupted evidence must never call setup."""
import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('reuse_pipeline', Path(__file__).parents[1]/'scripts/continue_pro_rescue.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value))


@pytest.fixture
def registered(tmp_path):
    task = 'instance_fixture'
    old, records = tmp_path/'old', tmp_path/'private'/'run'
    source_file = tmp_path/'source.py'
    source_file.write_text('unchanged fixture source')
    controls = str(tmp_path/'controls.json')
    source = tmp_path/'source-protocol.json'
    save(source, {'task_id': task, 'controls_summary': controls,
                  'private_records_root': str(tmp_path/'private'),
                  'source_sha256': {str(source_file): pipeline.digest(source_file)}})
    save(old/'queue.json', {'protocol_sha256': pipeline.digest(source)})
    save(old/'image-binding.json', {'image_id': 'image-fixture'})
    events, by_model = [], {}
    for number, model in enumerate(('gpt-6-luna', 'gpt-6.1-sol')):
        usage = {k:100 if k=='input_tokens' else 5 if k=='output_tokens' else 0
                 for k in pipeline.personal.USAGE_FIELDS}
        identity = str(number)
        events += [{'event':'request', 'request_id':identity},
                   {'event':'response','request_id':identity,'model':model,
                    'kind':'controller' if number==0 else 'expert','tool_events':[],
                    'thread_id':'thread-'+identity,'status':'completed',
                    'usage':usage,'usage_delta':usage.copy(),'usage_scope':'thread_cumulative',
                    'usage_accounting_issues':[]}]
        by_model[model] = {'usage':usage}
    total = {k:sum(r['usage'][k] for r in by_model.values()) for k in pipeline.personal.USAGE_FIELDS}
    manifest = {'status':'completed_ungraded','expert_calls':1,'usage':total,
                'usage_by_model':by_model,'usage_accounting_issues':[]}
    save(records/'controller/manifest.json', manifest)
    (records/'controller/events.jsonl').write_text('\n'.join(map(json.dumps,events)))
    (records/'final.patch').write_text('nonempty witness patch')
    (records/'pre-handoff.patch').write_text('initial candidate')
    save(records/'pre-handoff.json', {'patch_sha256': pipeline.digest(records/'pre-handoff.patch')})
    preflight = {'status':'real_actor_native_handoff_preflight_passed_replay_still_required',
                 'boundary_observations':{'head':'head','git_status':'','outside_head_commits':0,
                     'private_path_visible':False,'public_endpoint_reachable':False,'witness_ignored':False},
                 'witness':'witness.txt'}
    save(records/'preflight.json', preflight)
    original = old/'jobs/native-preflight-001/trial/result.json'
    meta = {'private_records_path':str(records),'manifest_sha256':pipeline.digest(records/'controller/manifest.json'),
            'final_patch_sha256':pipeline.digest(records/'final.patch'),'preflight':preflight}
    native = {'task_name':'swebench-pro/'+task,'exception_info':None,
              'verifier_result':{'rewards':{'reward':0}},
              'agent_result':{'metadata':meta,'model_usage':{
                  m:{'n_input_tokens':r['usage']['input_tokens'],'n_cache_tokens':0,
                     'n_output_tokens':r['usage']['output_tokens']} for m,r in by_model.items()}}}
    save(original, native)
    replay_path = old/'jobs/native-preflight-replay-001/trial/result.json'
    save(replay_path, {**native, 'agent_result':None})
    sealed = records/'sealed-replay-source'/task
    save(sealed/'result.json', {'task_name': native['task_name']})
    (sealed/'agent').mkdir()
    (sealed/'agent/model.patch').write_bytes((records/'final.patch').read_bytes())
    (sealed/'agent/pre-handoff.patch').write_bytes((records/'pre-handoff.patch').read_bytes())
    save(sealed/'seal.json', {'native_result_sha256':pipeline.digest(original),
                            'patches_sha256':{p.name:pipeline.digest(p) for p in (sealed/'agent').iterdir()}})
    save(replay_path.parent/'agent/replay.json', {'patch':str(sealed/'agent/model.patch'),
          'apply_rc':0,'apply_out':'Applied patch witness.txt cleanly.\n'})
    paths = [source, *[p for p in old.rglob('*') if p.is_file()],
             *[p for p in records.rglob('*') if p.is_file()]]
    protocol = {'task_id':task,'controls_summary':controls,'source_sha256':{},
                'reuse_setup':{'source_protocol':str(source),'source_output':str(old),
                   'artifacts_sha256':{str(p.resolve()):pipeline.digest(p) for p in paths}}}
    return protocol, records, old


def test_valid_reuse_returns_measured_setup_without_calling_fresh_setup(registered):
    protocol, records, old = registered
    receipt = pipeline.setup_stage(protocol, 'image-fixture', lambda:pytest.fail('Repeated setup inference'))
    assert receipt['new_setup_model_calls'] == 0
    assert receipt['setup_usage']['input_tokens'] == 200
    assert receipt['expert_calls'] == 1
    assert receipt['benchmark_accuracy_claim'] is False
    assert not list(old.glob('first-block-*'))


@pytest.mark.parametrize('corruption', ['patch','missing-inventory','wrong-task','wrong-image',
                                       'scored-started','wrong-delta','source-changed','wrong-native-usage'])
def test_invalid_reuse_never_falls_back_to_setup(registered, corruption):
    protocol, records, old = registered
    image = 'image-fixture'
    if corruption=='patch':
        (records/'final.patch').write_text('changed')
    elif corruption=='missing-inventory':
        del protocol['reuse_setup']['artifacts_sha256'][str((records/'controller/events.jsonl').resolve())]
    elif corruption=='wrong-task':
        protocol['task_id'] = 'other-task'
    elif corruption=='wrong-image':
        image = 'other-image'
    elif corruption=='scored-started':
        save(old/'first-block-optional-invocation.json', {'uncertain':True})
    elif corruption=='wrong-delta':
        path = records/'controller/events.jsonl'
        events = [json.loads(s) for s in path.read_text().splitlines()]
        # Preserve aggregate usage/deltas but corrupt the underlying cumulative counter.
        events[-1]['usage']['input_tokens'] += 1
        path.write_text('\n'.join(map(json.dumps,events)))
        protocol['reuse_setup']['artifacts_sha256'][str(path.resolve())] = pipeline.digest(path)
    elif corruption=='wrong-native-usage':
        path = next((old/'jobs/native-preflight-001').glob('*/result.json'))
        native = json.loads(path.read_text())
        native['agent_result']['model_usage']['gpt-6-luna']['n_input_tokens'] = 101
        save(path, native)
        protocol['reuse_setup']['artifacts_sha256'][str(path.resolve())] = pipeline.digest(path)
    else:
        source = json.loads(Path(protocol['reuse_setup']['source_protocol']).read_text())
        Path(next(iter(source['source_sha256']))).write_text('changed generation source')
    with pytest.raises(RuntimeError):
        pipeline.setup_stage(protocol, image, lambda:pytest.fail('Must never retry setup'))


def test_fresh_setup_requires_explicit_authorization():
    with pytest.raises(RuntimeError, match='explicit'):
        pipeline.setup_stage({}, 'image', lambda:pytest.fail('Implicit setup inference'))
    assert pipeline.setup_stage({'setup_mode':'fresh_authorized'}, 'image', lambda:'fresh') == 'fresh'


def transport_target(protocol, old):
    protocol['reuse_setup']['scope'] = 'transport_metering_only'
    protocol['task_id'] = 'instance_next-task'
    summary = old.parent/'target-controls.json'
    rows = []
    for agent, grade in [('nop',0),('oracle',1)]:
        path = old.parent/(agent+'-target.json')
        save(path, {'task_name':'swebench-pro/instance_next-task','exception_info':None,
                    'verifier_result':{'rewards':{'reward':grade}}})
        rows.append({'agent':agent,'native_result':str(path),'native_result_sha256':pipeline.digest(path)})
    save(summary, {'status':'one_task_empty_reference_controls_passed','controls':rows})
    protocol['controls_summary'] = str(summary)
    protocol['source_sha256'][str(summary)] = pipeline.digest(summary)
    return summary


def test_transport_reuse_does_not_reuse_prior_task_readiness_or_quality(registered):
    protocol, records, old = registered
    transport_target(protocol, old)
    receipt = pipeline.setup_stage(protocol, 'new-target-image', lambda:pytest.fail('Repeated native setup'))
    assert receipt['original_task_id'] == 'instance_fixture'
    assert receipt['target_task_id'] == 'instance_next-task'
    assert receipt['target_image_id'] == 'new-target-image'
    assert receipt['target_task_quality_claim'] is False
    assert receipt['target_controls_audited'] is True
    assert receipt['new_setup_model_calls'] == 0


@pytest.mark.parametrize('fault', ['wrong-task','bad-reference','unbound-summary'])
def test_transport_reuse_rejects_unready_target_before_any_inference(registered,fault):
    protocol, records, old = registered
    summary = transport_target(protocol, old)
    if fault=='unbound-summary':
        del protocol['source_sha256'][str(summary)]
    else:
        rows = json.loads(summary.read_text())
        path = Path(rows['controls'][1]['native_result'])
        native = json.loads(path.read_text())
        if fault=='wrong-task':native['task_name']='other-task'
        else:native['verifier_result']['rewards']['reward']=0
        save(path,native)
        rows['controls'][1]['native_result_sha256']=pipeline.digest(path)
        save(summary,rows)
        protocol['source_sha256'][str(summary)]=pipeline.digest(summary)
    with pytest.raises(RuntimeError):
        pipeline.setup_stage(protocol,'new-target-image',lambda:pytest.fail('Must not call a model'))
