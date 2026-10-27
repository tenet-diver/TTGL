from dataclasses import replace
from pathlib import Path

import pytest

from ttgl.personal import Request, _task_prompt
from ttgl.verification_policy import verification_prompt, VerificationPolicyBackend
from ttgl import policy


def request(cooperative=True):
    task = {'prompt': 'Repair an artifact.', 'allowed_paths': ['.'], 'memory': []}
    return Request('verification-1', 'fixture', 'controller',
                   _task_prompt(task, cooperative=cooperative, expert_limit=2),
                   Path('/tmp/verification-fixture'), {}, 30)


def test_matched_controls_get_same_verification_and_no_expert_permission():
    solo = verification_prompt(request(False))
    assisted = verification_prompt(request())
    common = solo.split('Verification treatment v3:\n')[1].strip()
    assert common in assisted
    assert 'Use the specialist for verification' not in solo
    assert 'Use the specialist for verification' in assisted
    assert solo.count('Controller policy v2:') == 1


@pytest.mark.parametrize('kind', ['expert', 'router'])
def test_context_only_roles_keep_the_exact_prompt(kind):
    original = replace(request(), kind=kind, read_only=True)
    assert verification_prompt(original) == original.prompt


def test_followup_does_not_repeat_the_instructions():
    original = replace(request(), thread_id='existing', prompt='Expert: test an alternative input.')
    assert verification_prompt(original) == original.prompt


def test_backend_records_effective_prompt_before_native_call(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(policy.ContainerBackend, 'complete', lambda self, r: calls.append(r) or 'native-result')
    backend = VerificationPolicyBackend(audit_root=tmp_path)
    assert backend.complete(request()) == 'native-result'
    assert calls[0].prompt == verification_prompt(request())
    assert len(list(tmp_path.glob('*.json'))) == 1
    assert backend.describe()['controller_policy']['treatment'] == 'verification-v3'


def test_source_change_refuses_inference(tmp_path, monkeypatch):
    backend = VerificationPolicyBackend(audit_root=tmp_path)
    monkeypatch.setattr(backend, 'policy_identity', lambda: {'changed': True})
    with pytest.raises(ValueError, match='changed'):
        backend.complete(request())
    assert not list(tmp_path.iterdir())
