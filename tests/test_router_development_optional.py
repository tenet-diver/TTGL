from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip('harbor')
from ttgl import personal
from ttgl.harbor_bridge import HarborBackend
from ttgl.router_development import RouterDevelopmentBackend, RouterDevelopmentCodex


def request():
    task = {'prompt': 'Repair this artifact.', 'allowed_paths': ['.'], 'memory': []}
    return personal.Request('router-dev-test', 'fixture', 'controller',
        personal._task_prompt(task, cooperative=True, expert_limit=2),
        Path('/tmp/router-dev-test'), {}, 30)


def test_router_receives_decision_guidance_and_retains_voluntary_help(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(HarborBackend, 'complete', lambda self, r: calls.append(r) or 'reply')
    backend = RouterDevelopmentBackend(None, diagnostic='verification', records=tmp_path)
    assert backend.complete(request()) == 'reply'
    assert 'next action (continue, ask_expert, or complete)' in calls[0].prompt
    assert 'at most 2 times' in calls[0].prompt
    assert 'required-handoff diagnostic condition' not in calls[0].prompt
    assert 'Verification treatment v3:' in calls[0].prompt
    followup = replace(request(), thread_id='existing', prompt='Continue with observed test output.')
    backend.complete(followup)
    assert calls[1].prompt == followup.prompt


def test_changed_router_prompt_stops_before_inference(tmp_path, monkeypatch):
    backend = RouterDevelopmentBackend(None, diagnostic='verification', records=tmp_path)
    monkeypatch.setattr(backend, 'diagnostic_identity', lambda: {'changed': True})
    with pytest.raises(ValueError, match='changed'):
        backend.complete(request())


def test_router_only_agent_refuses_standalone_or_required_review():
    agent = object.__new__(RouterDevelopmentCodex)
    agent.condition, agent.policy = 'small', 'verification'
    with pytest.raises(ValueError, match='voluntary personal'):
        agent.make_backend(None, Path('/tmp/unused'))
