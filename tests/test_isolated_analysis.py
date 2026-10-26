"""Observable token-rate scenario costs and incomplete-accounting behavior."""
import copy
import json
from pathlib import Path

import pytest

from scripts.finalize_isolated_swe import scenario_cost


RATES = json.loads((Path(__file__).resolve().parents[1] /
                   'experiments/codex-isolated-20261026/pricing-scenario.json').read_text())


def manifest(model='gpt-6-luna'):
    usage = {'input_tokens': 1_000_000, 'cached_input_tokens': 400_000,
             'output_tokens': 100_000}
    return {'usage': usage, 'usage_by_model': {model: {'usage': usage.copy()}},
            'usage_accounting_issues': []}


@pytest.mark.parametrize('model,expected', [('gpt-6-luna', 0.114), ('gpt-6.1-sol', 2.24)])
def test_prices_cached_and_uncached_tokens_without_double_counting(model, expected):
    assert scenario_cost(manifest(model), RATES) == pytest.approx(expected)


def test_prices_controller_and_expert_together():
    row = manifest()
    row['usage_by_model']['gpt-6.1-sol'] = copy.deepcopy(row['usage_by_model']['gpt-6-luna'])
    row['usage'] = {k: 2*v for k, v in row['usage'].items()}
    assert scenario_cost(row, RATES) == pytest.approx(2.354)


@pytest.mark.parametrize('change', ['unknown_usage', 'unpriced_model', 'accounting_issue'])
def test_incomplete_cost_never_becomes_zero(change):
    row = manifest()
    if change == 'unknown_usage':
        row['usage']['output_tokens'] = None
    elif change == 'unpriced_model':
        row['usage_by_model'] = {'unpriced': row['usage_by_model']['gpt-6-luna']}
    else:
        row['usage_accounting_issues'] = ['invoked_role_without_reported_thread']
    assert scenario_cost(row, RATES) is None


def test_missing_role_counters_cannot_understate_a_complete_total():
    row = manifest()
    row['usage']['input_tokens'] += 1
    with pytest.raises(ValueError, match='reconcile'):
        scenario_cost(row, RATES)
