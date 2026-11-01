"""Matched common guidance and voluntary-only routing without model inference."""
from dataclasses import replace
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip('harbor')
from ttgl import personal
from ttgl.evidence_decision_router import COMMON, ROUTING, EvidenceDecisionBackend, EvidenceDecisionCodex


def request(cooperative, identity):
    task = {'prompt':'Solve this task.','allowed_paths':['.'],'memory':[]}
    return personal.Request(identity, 'gpt-6-luna' if cooperative else 'gpt-6.1-sol',
        'controller',personal._task_prompt(task,cooperative=cooperative,expert_limit=2),
        Path('/tmp/v9-fixture'),personal.ACTION_SCHEMA,30)


def evidence_response(r):
    value={'action':'complete','question':'','context':'','summary':'candidate summary',
           'verification_status':'incomplete','acceptance_evidence':'existing regression only',
           'attempt_evidence':'candidate; relevant check missing','material_gaps':'new behavior untested',
           'escalation_reason':'chosen completion despite gap; no backend override'}
    if r.kind=='expert':value={'action':'answer','message':'focused advice'}
    return personal.Response(text=json.dumps(value),thread_id='thread',usage={'input_tokens':100},elapsed_seconds=2)


def test_router_and_sol_share_one_common_policy_but_only_router_can_delegate(tmp_path,monkeypatch):
    sent=[]
    monkeypatch.setattr(personal.CodexBackend,'complete',lambda self,r:sent.append(r) or evidence_response(r))
    for cooperative, name in [(False,'sol'),(True,'router')]:
        bridge=SimpleNamespace(repository='/app',active_request={})
        backend=EvidenceDecisionBackend(bridge,diagnostic='verification',records=tmp_path/name)
        backend.complete(request(cooperative,name))
        assert bridge.active_request=={}
    for r in sent:
        assert r.prompt.count(COMMON.read_text())==1
        assert 'Controller policy v2:' not in r.prompt
        assert 'Verification treatment v3:' not in r.prompt
        assert 'Router development v4' not in r.prompt
        assert 'Router v6' not in r.prompt
    assert ROUTING.read_text() not in sent[0].prompt
    assert ROUTING.read_text() in sent[1].prompt
    assert 'concrete\nblocker' in sent[1].prompt
    assert 'Expert handoff checklist' not in sent[1].prompt


def test_resumed_controller_and_expert_do_not_get_repeated_policy(tmp_path,monkeypatch):
    sent=[]
    monkeypatch.setattr(personal.CodexBackend,'complete',lambda self,r:sent.append(r) or evidence_response(r))
    bridge=SimpleNamespace(repository='/app',active_request={})
    backend=EvidenceDecisionBackend(bridge,diagnostic='verification',records=tmp_path)
    resumed=replace(request(True,'resume'),thread_id='existing',prompt='Observed a failing check.')
    backend.complete(resumed)
    assert COMMON.read_text() not in sent[0].prompt
    (tmp_path/'pre-handoff.json').write_text('{}')
    expert=replace(resumed,request_id='expert',kind='expert',schema=personal.EXPERT_SCHEMA,read_only=True,prompt='Exact source and focused question.')
    backend.complete(expert)
    assert sent[1].prompt==expert.prompt
    assert bridge.active_request=={}


def test_changed_policy_refuses_before_inference(tmp_path,monkeypatch):
    backend=EvidenceDecisionBackend(None,diagnostic='verification',records=tmp_path)
    monkeypatch.setattr(backend,'diagnostic_identity',lambda:{'changed':True})
    with pytest.raises(ValueError,match='changed'):
        backend.complete(None)


def test_matched_agent_refuses_unregistered_conditions():
    agent=object.__new__(EvidenceDecisionCodex)
    for condition, policy in [('small','verification'),('personal','required_review')]:
        agent.condition,agent.policy=condition,policy
        with pytest.raises(ValueError,match='Matched v9'):
            agent.make_backend(None,Path('/tmp/unused-v9'))


def test_v9_expert_remains_context_only(tmp_path):
    bridge=SimpleNamespace(repository='/app',active_request={},port=12345,token='a'*64)
    backend=EvidenceDecisionBackend(bridge,diagnostic='verification',records=tmp_path)
    expert=replace(request(True,'expert-command'),kind='expert',read_only=True)
    command=backend.command(expert,tmp_path/'schema.json')
    assert not any('mcp_servers.worker' in part for part in command)
    for feature in ('shell_tool','unified_exec','apps','browser_use'):
        assert command[command.index(feature)-1]=='--disable'


def test_structured_evidence_preserves_agent_action_and_all_metering(tmp_path,monkeypatch):
    sent=[];raw=evidence_response(request(True,'meter'))
    monkeypatch.setattr(personal.CodexBackend,'complete',lambda self,r:sent.append(r) or raw)
    backend=EvidenceDecisionBackend(SimpleNamespace(repository='/app',active_request={}),diagnostic='verification',records=tmp_path)
    response=backend.complete(request(True,'meter'))
    assert set(sent[0].schema['properties'])==set(personal.ACTION_SCHEMA['properties'])|{'verification_status','acceptance_evidence','attempt_evidence','material_gaps','escalation_reason'}
    assert json.loads(response.text)['action']=='complete' # no automatic conversion to Sol
    assert response.usage==raw.usage and response.elapsed_seconds==raw.elapsed_seconds
    evidence=json.loads(next((tmp_path/'decision-evidence').glob('*.json')).read_text())
    assert evidence['decision']['verification_status']=='incomplete'
    assert evidence['decision']['material_gaps']=='new behavior untested'
    assert evidence['decision']['action']=='complete'


def test_malformed_evidence_does_not_erase_consumed_usage(tmp_path,monkeypatch):
    raw=personal.Response(text='{}',thread_id='thread',usage={'input_tokens':123},elapsed_seconds=3)
    monkeypatch.setattr(personal.CodexBackend,'complete',lambda self,r:raw)
    backend=EvidenceDecisionBackend(SimpleNamespace(repository='/app',active_request={}),diagnostic='verification',records=tmp_path)
    response=backend.complete(request(True,'invalid'))
    assert response.status=='failed' and response.error_type=='decision_evidence_schema'
    assert response.usage==raw.usage and response.elapsed_seconds==raw.elapsed_seconds


def test_audit_write_failure_preserves_consumed_usage(tmp_path,monkeypatch):
    from ttgl import evidence_decision_router as module
    raw=evidence_response(request(True,'write'))
    monkeypatch.setattr(personal.CodexBackend,'complete',lambda self,r:raw)
    original=module.benchmark.write_new
    def write(path,value):
        if path.parent.name=='decision-evidence':raise OSError('disk unavailable')
        return original(path,value)
    monkeypatch.setattr(module.benchmark,'write_new',write)
    backend=EvidenceDecisionBackend(SimpleNamespace(repository='/app',active_request={}),diagnostic='verification',records=tmp_path)
    response=backend.complete(request(True,'write'))
    assert response.status=='failed' and response.error_type=='decision_evidence_write'
    assert response.usage==raw.usage and response.elapsed_seconds==raw.elapsed_seconds
