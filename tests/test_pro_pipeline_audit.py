import importlib.util
import json
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('pro_pipeline',Path(__file__).parents[1]/'scripts/continue_pro_rescue.py')
pipeline = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pipeline)


def fixture(tmp_path):
    directory = tmp_path/'controller'
    directory.mkdir()
    events = []
    for identity, count in [('one',100),('two',40)]:
        events.append({'event':'request','request_id':identity})
        usage = {k:count if k=='input_tokens' else 0 for k in pipeline.personal.USAGE_FIELDS}
        events.append({'event':'response','request_id':identity,'model':'fixture-model','kind':'controller',
                       'usage_delta':usage,'tool_events':[]})
    total = {k:140 if k=='input_tokens' else 0 for k in pipeline.personal.USAGE_FIELDS}
    manifest = {'usage':total,'usage_by_model':{'fixture-model':{'usage':total.copy()}}}
    (directory/'manifest.json').write_text(json.dumps(manifest))
    return events


def test_independent_audit_reconciles_all_native_roles(tmp_path):
    events = fixture(tmp_path)
    (tmp_path/'controller/events.jsonl').write_text('\n'.join(map(json.dumps,events)))
    assert pipeline.audit_native(tmp_path)['usage']['input_tokens'] == 140


@pytest.mark.parametrize('corruption', ['duplicate','missing','wrong-total','expert-tool','missing-model'])
def test_audit_rejects_ambiguous_or_mismatched_inference(tmp_path,corruption):
    events = fixture(tmp_path)
    if corruption=='duplicate':
        events.append(events[0])
    elif corruption=='missing':
        events.pop()
    elif corruption=='wrong-total':
        events[-1]['usage_delta']['input_tokens'] = 41
    elif corruption=='expert-tool':
        events[-1]['kind'] = 'expert'
        events[-1]['tool_events'] = [{'type':'mcp_tool_call'}]
    else:
        path = tmp_path/'controller/manifest.json'
        manifest = json.loads(path.read_text())
        manifest['usage_by_model'] = {}
        path.write_text(json.dumps(manifest))
    (tmp_path/'controller/events.jsonl').write_text('\n'.join(map(json.dumps,events)))
    with pytest.raises(RuntimeError):
        pipeline.audit_native(tmp_path)


def test_missing_control_queue_stops_without_launching_any_job(tmp_path,monkeypatch):
    protocol = tmp_path/'protocol.json'
    protocol.write_text(json.dumps({'source_sha256':{},'controls_summary':str(tmp_path/'not-ready.json'),
                                    'controls_queue_pid':1234}))
    output = tmp_path/'new-output'
    monkeypatch.setattr(pipeline.sys, 'argv', ['continue_pro_rescue','--protocol',str(protocol),'--output',str(output)])
    def dead_queue(pid, signal):
        raise ProcessLookupError('fixture controls queue is gone')
    monkeypatch.setattr(pipeline.os, 'kill', dead_queue)
    monkeypatch.setattr(pipeline.subprocess, 'run', lambda *args,**kwargs: pytest.fail('No job may launch before controls'))
    with pytest.raises(ProcessLookupError):
        pipeline.main()
    assert json.loads((output/'stopped.json').read_text())['error_type']=='ProcessLookupError'
    assert not list(output.glob('*-invocation.json'))


def test_new_untracked_witness_is_verified_from_successful_patch_application():
    replay = {'apply_rc': 0, 'apply_out': 'Checking patch witness.txt...\nApplied patch witness.txt cleanly.\n',
              'post_apply_diffstat': '---\n1\n'}
    assert pipeline.witness_replay_passed(0, 0, replay, 'witness.txt')
    assert not pipeline.witness_replay_passed(0, 0, replay, 'other.txt')
    assert not pipeline.witness_replay_passed(0, 1, replay, 'witness.txt')
    assert not pipeline.witness_replay_passed(1, 0, replay, 'witness.txt')
    assert not pipeline.witness_replay_passed(0, 0, {**replay, 'apply_rc': 1}, 'witness.txt')
    assert not pipeline.witness_replay_passed(0, 0, {**replay, 'apply_out': 'Checking patch witness.txt...'}, 'witness.txt')
