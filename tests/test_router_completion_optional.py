from dataclasses import replace
from pathlib import Path

import pytest

pytest.importorskip('harbor')
from ttgl import personal
from ttgl.harbor_bridge import HarborBackend
from ttgl.router_completion import CompletionEvidenceBackend


def test_v5_actor_gets_behavioral_verification_without_forced_review(tmp_path,monkeypatch):
    sent=[]
    monkeypatch.setattr(HarborBackend,'complete',lambda self,r:sent.append(r) or 'response')
    backend=CompletionEvidenceBackend(None,diagnostic='verification',records=tmp_path)
    task={'prompt':'Fix a public bug.','allowed_paths':['.'],'memory':[]}
    request=personal.Request('v5-test','fixture','controller',
        personal._task_prompt(task,cooperative=True,expert_limit=2),Path('/tmp/v5-test'),{},30)
    assert backend.complete(request)=='response'
    assert 'bounded behavioral check' in sent[0].prompt
    assert 'two or three' in sent[0].prompt
    assert 'Expert handoff checklist' in sent[0].prompt
    assert 'required-handoff diagnostic condition' not in sent[0].prompt
    followup=replace(request,thread_id='existing',prompt='Observed a failing public check.')
    backend.complete(followup)
    assert sent[1].prompt==followup.prompt


def test_v5_changed_policy_refuses_inference(tmp_path,monkeypatch):
    backend=CompletionEvidenceBackend(None,diagnostic='verification',records=tmp_path)
    monkeypatch.setattr(backend,'diagnostic_identity',lambda:{'changed':True})
    with pytest.raises(ValueError,match='changed'):
        backend.complete(None)
