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


def pair_protocol(tmp_path):
    return {'matched_pair_development':True,'first_block_order':['large','optional'],
            'scored_assignment_cap':2,'assignment_claims':{
                'large':str(tmp_path/'sol.json'),'optional':str(tmp_path/'router.json')}}


def test_matched_pair_requires_distinct_registered_assignment_claims(tmp_path):
    protocol=pair_protocol(tmp_path)
    pipeline.validate_matched_pair(protocol)
    protocol['assignment_claims']['optional']=protocol['assignment_claims']['large']
    with pytest.raises(RuntimeError):pipeline.validate_matched_pair(protocol)


@pytest.mark.parametrize('fault',['extra-arm','wrong-cap','missing-claim','router-only'])
def test_invalid_matched_scope_refused_before_inference(tmp_path,fault):
    protocol=pair_protocol(tmp_path)
    if fault=='extra-arm':protocol['first_block_order'].append('small')
    elif fault=='wrong-cap':protocol['scored_assignment_cap']=0
    elif fault=='missing-claim':protocol['assignment_claims'].pop('large')
    else:protocol['router_only_development']=True
    with pytest.raises(RuntimeError):pipeline.validate_matched_pair(protocol)


def test_matched_summary_keeps_quality_loss_and_unknown_cost_visible():
    rows=[{'task_id':'same','arm':'large','resolved':True,'cost_scenario_usd':1.0},
          {'task_id':'same','arm':'optional','resolved':False,'cost_scenario_usd':0.05}]
    result=pipeline.matched_pair_observation(rows)
    assert result['sol_success_lost'] is True
    assert result['resolved_delta']==-1
    assert result['scenario_saving']==pytest.approx(0.95)
    assert result['population_noninferiority_claim'] is False
    rows[1]['cost_scenario_usd']=None
    assert pipeline.matched_pair_observation(rows)['scenario_saving'] is None
    rows[1]['task_id']='other'
    with pytest.raises(RuntimeError):pipeline.matched_pair_observation(rows)


@pytest.mark.parametrize('cost',[-1,float('nan'),float('inf')])
def test_matched_summary_rejects_invalid_cost(cost):
    rows=[{'task_id':'same','arm':'large','resolved':True,'cost_scenario_usd':1.0},
          {'task_id':'same','arm':'optional','resolved':True,'cost_scenario_usd':cost}]
    with pytest.raises(RuntimeError):pipeline.matched_pair_observation(rows)
