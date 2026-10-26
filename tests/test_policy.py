from pathlib import Path
from dataclasses import replace

import pytest

from ttgl.personal import Request, _task_prompt
from ttgl.policy import policy_prompt


def request(cooperative=True):
    task = {'prompt': 'Check a calculation.', 'allowed_paths': ['.'], 'memory': []}
    return Request('1', 'fixture', 'controller',
                   _task_prompt(task, cooperative=cooperative, expert_limit=2),
                   Path('/tmp/fixture'), {}, 30)


def test_standalone_gets_same_solving_guidance_without_expert_permission():
    solo = policy_prompt(request(False), 'adaptive')
    assisted = policy_prompt(request(), 'adaptive')
    common = solo.split('Controller policy v2:\n')[1].strip()
    assert common in assisted
    assert 'stronger specialist is available' not in solo
    assert 'self-contained handoff' in assisted
    assert 'checks' in common and 'uncertainty' in common


@pytest.mark.parametrize('kind', ['expert', 'router'])
def test_context_only_roles_do_not_receive_controller_instructions(kind):
    original = replace(request(), kind=kind, read_only=True)
    assert policy_prompt(original, 'adaptive') == original.prompt


def test_followup_keeps_expert_reply_without_reinserting_policy():
    original = replace(request(), thread_id='existing', prompt='Expert says: inspect the boundary.')
    assert policy_prompt(original, 'adaptive') == original.prompt


def test_fallback_requires_attempt_and_check_but_adaptive_allows_early_help():
    assert 'First make a bounded independent attempt' in policy_prompt(request(), 'fallback')
    assert 'You may ask early' in policy_prompt(request(), 'adaptive')
    with pytest.raises(ValueError):
        policy_prompt(request(), 'unknown')
