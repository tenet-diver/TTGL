import importlib.util
from pathlib import Path

import pytest

spec=importlib.util.spec_from_file_location('router_episode_analysis',Path(__file__).parents[1]/'scripts/analyze_router_episode.py')
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_cost_counts_cached_input_once_and_keeps_unknown_cost_unknown():
    rates={'fixture':{'input_per_million':2,'cached_input_per_million':0.1,'output_per_million':10}}
    models={'fixture':{'usage':{'input_tokens':1000000,'cached_input_tokens':400000,'output_tokens':1000}}}
    assert module.scenario_cost(models,rates)==1.25
    models['fixture']['usage']['output_tokens']=None
    assert module.scenario_cost(models,rates) is None
    models['fixture']['usage'].update(output_tokens=0,cached_input_tokens=1000001)
    with pytest.raises(ValueError):module.scenario_cost(models,rates)


def test_latencies_use_actual_elapsed_time_across_timezone_offsets():
    assert module.seconds('2026-10-31T18:00:00Z','2026-10-31T19:00:12+01:00')==12
