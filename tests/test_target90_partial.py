import importlib.util,json
from pathlib import Path
import pytest
spec=importlib.util.spec_from_file_location('recovery',Path(__file__).parents[1]/'scripts/continue_target90_partial.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)

def test_unstarted_arm_can_be_distinguished(tmp_path):
    assert m.next_action(tmp_path,'large')==('unstarted',None)

def test_uncertain_started_call_is_never_repeatable(tmp_path):
    (tmp_path/'first-block-optional-invocation.json').write_text('{}')
    with pytest.raises(RuntimeError,match='uncertain'):m.next_action(tmp_path,'optional')

def test_completed_native_is_reused_even_when_it_failed_task(tmp_path):
    (tmp_path/'first-block-optional-invocation.json').write_text('{}');d=tmp_path/'jobs/first-block-optional/trial';d.mkdir(parents=True);r=d/'result.json';r.write_text(json.dumps({'verifier_result':{'rewards':{'reward':0}}}))
    assert m.next_action(tmp_path,'optional')==('reuse_completed_native',r)
    r.write_text(json.dumps({'exception_info':{'error':'timeout'},'verifier_result':{'rewards':{'reward':0}}}))
    with pytest.raises(RuntimeError,match='uncertain'):m.next_action(tmp_path,'optional')

def test_unbound_report_is_not_treated_as_new_assignment(tmp_path):
    d=tmp_path/'jobs/first-block-large/trial';d.mkdir(parents=True);(d/'result.json').write_text('{}')
    with pytest.raises(RuntimeError,match='without invocation'):m.next_action(tmp_path,'large')

def test_changed_recovery_evidence_rejected(tmp_path):
    f=tmp_path/'seal';f.write_text('original');inventory={str(f):m.p.digest(f)};m.verify_inventory(inventory);f.write_text('changed')
    with pytest.raises(RuntimeError,match='changed'):m.verify_inventory(inventory)
