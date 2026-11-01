"""Matched common guidance and voluntary-only routing without model inference."""
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip('harbor')
from ttgl import personal
from ttgl.completion_review_router import COMMON, ROUTING, CompletionReviewBackend, CompletionReviewCodex


def request(cooperative, identity):
    task = {'prompt':'Solve this task.','allowed_paths':['.'],'memory':[]}
    return personal.Request(identity, 'gpt-6-luna' if cooperative else 'gpt-6.1-sol',
        'controller',personal._task_prompt(task,cooperative=cooperative,expert_limit=2),
        Path('/tmp/v8-fixture'),{},30)


def test_router_and_sol_share_one_common_policy_but_only_router_can_delegate(tmp_path,monkeypatch):
    sent=[]
    monkeypatch.setattr(personal.CodexBackend,'complete',lambda self,r:sent.append(r) or SimpleNamespace(elapsed_seconds=0))
    for cooperative, name in [(False,'sol'),(True,'router')]:
        bridge=SimpleNamespace(repository='/app',active_request={})
        backend=CompletionReviewBackend(bridge,diagnostic='verification',records=tmp_path/name)
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
    monkeypatch.setattr(personal.CodexBackend,'complete',lambda self,r:sent.append(r) or SimpleNamespace(elapsed_seconds=0))
    bridge=SimpleNamespace(repository='/app',active_request={})
    backend=CompletionReviewBackend(bridge,diagnostic='verification',records=tmp_path)
    resumed=replace(request(True,'resume'),thread_id='existing',prompt='Observed a failing check.')
    backend.complete(resumed)
    assert COMMON.read_text() not in sent[0].prompt
    (tmp_path/'pre-handoff.json').write_text('{}')
    expert=replace(resumed,request_id='expert',kind='expert',read_only=True,prompt='Exact source and focused question.')
    backend.complete(expert)
    assert sent[1].prompt==expert.prompt
    assert bridge.active_request=={}


def test_changed_policy_refuses_before_inference(tmp_path,monkeypatch):
    backend=CompletionReviewBackend(None,diagnostic='verification',records=tmp_path)
    monkeypatch.setattr(backend,'diagnostic_identity',lambda:{'changed':True})
    with pytest.raises(ValueError,match='changed'):
        backend.complete(None)


def test_matched_agent_refuses_unregistered_conditions():
    agent=object.__new__(CompletionReviewCodex)
    for condition, policy in [('small','verification'),('personal','required_review')]:
        agent.condition,agent.policy=condition,policy
        with pytest.raises(ValueError,match='Matched v8'):
            agent.make_backend(None,Path('/tmp/unused-v8'))


def test_v8_expert_remains_context_only(tmp_path):
    bridge=SimpleNamespace(repository='/app',active_request={},port=12345,token='a'*64)
    backend=CompletionReviewBackend(bridge,diagnostic='verification',records=tmp_path)
    expert=replace(request(True,'expert-command'),kind='expert',read_only=True)
    command=backend.command(expert,tmp_path/'schema.json')
    assert not any('mcp_servers.worker' in part for part in command)
    for feature in ('shell_tool','unified_exec','apps','browser_use'):
        assert command[command.index(feature)-1]=='--disable'
