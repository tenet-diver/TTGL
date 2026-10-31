import importlib.util
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location('summary90',Path(__file__).parents[1]/'scripts/summarize_target90_development.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def pair(task,sol_cost,router_cost,router_resolved=1):
    return {'status':'audited_development_pair_not_final_target_evidence','task_id':task,
            'policy_identity':{'v7':'fixed'},'arms':{
                'large':{'resolved':1,'cost_scenario_usd':sol_cost},
                'optional':{'resolved':router_resolved,'cost_scenario_usd':router_cost}},
            'comparison':{'sol_success_lost':not router_resolved,'router_extra_success':False}}


def test_favorable_partial_panel_never_passes_full_development_gate():
    plan={'tasks':[{'task_id':'one'},{'task_id':'two'}]}
    result=m.summarize(plan,[pair('one',1,0.01)])
    assert result['aggregate_scenario_saving']==pytest.approx(0.99)
    assert result['development_point_gate'] is None
    assert result['held_out_target_achieved'] is False


def test_aggregate_uses_total_assigned_cost_not_average_task_ratios():
    plan={'tasks':[{'task_id':'one'},{'task_id':'two'}]}
    result=m.summarize(plan,[pair('one',1,0.15),pair('two',9,0.45)])
    assert result['aggregate_scenario_saving']==pytest.approx(0.94)
    assert result['development_point_gate'] is True
    assert result['held_out_target_achieved'] is False


def test_quality_loss_or_unknown_cost_cannot_pass_target_gate():
    plan={'tasks':[{'task_id':'one'}]}
    result=m.summarize(plan,[pair('one',1,0.01,0)])
    assert result['development_point_gate'] is False
    assert result['cost_per_resolved_usd']['optional'] is None
    result=m.summarize(plan,[pair('one',1,None)])
    assert result['aggregate_scenario_saving'] is None
    assert result['development_point_gate'] is False


def test_duplicate_tasks_are_rejected():
    p=pair('one',1,0.01)
    with pytest.raises(ValueError):m.summarize({'tasks':[{'task_id':'one'}]},[p,p])
