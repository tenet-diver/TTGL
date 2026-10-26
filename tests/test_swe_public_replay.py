"""Integrity and leakage checks for the public standard-benchmark replay."""
import importlib.util
from pathlib import Path

import numpy as np
import pytest

SPEC = importlib.util.spec_from_file_location('swe_public_replay', Path(__file__).parents[1] / 'scripts/swe_public_replay.py')
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


def records():
    return {model: {f'repo__name-{i}': {'resolved': bool(i % 2), 'cost': .1, 'api_calls': 3}
                    for i in range(500)} for model in ['small', 'large']}


def test_complete_pair_validation_and_unknown_cost_not_zero():
    rows = records()
    assert len(MODULE.validate_records(rows)) == 500
    rows['small']['repo__name-0']['cost'] = None
    with pytest.raises(ValueError, match='cost'):
        MODULE.validate_records(rows)


def test_incomplete_task_coverage_refused():
    rows = records()
    del rows['large']['repo__name-0']
    with pytest.raises(ValueError, match='coverage'):
        MODULE.validate_records(rows)


def test_fold_quotas_do_not_depend_on_other_folds_scores():
    scores = np.asarray([1., 2., 3., 4., 8., 7., 6., 5.])
    ids = [f'task-{i}' for i in range(8)]
    folds = np.asarray([0, 0, 0, 0, 1, 1, 1, 1])
    original = MODULE.rank_allocate(scores, .5, ids, folds)
    scores[4:] = [1000, 2000, -3000, -4000]
    changed = MODULE.rank_allocate(scores, .5, ids, folds)
    assert np.array_equal(original[:4], changed[:4])
    assert original[:4].sum() == changed[:4].sum() == 2
    assert original[4:].sum() == changed[4:].sum() == 2


def test_training_interface_requires_no_test_labels_or_costs():
    texts = ['bug conversion parser common case '+('alpha' if i % 2 else 'beta') for i in range(20)]
    repos = ['repo'] * 20
    train = np.arange(16)
    test = np.arange(16,20)
    # Only 16 training response rows are passed for the 20 total feature rows.
    quality = np.asarray([[i % 2, (i + 1) % 2] for i in train], dtype=float)
    costs = np.asarray([[.1+i/100, .5+i/100] for i in train])
    p,c = MODULE.fit_fold(texts, repos, train, test, quality, costs)
    assert p.shape == c.shape == (4,2)
    assert np.all((p >= 0) & (p <= 1))
    assert np.all(c > 0)


def test_paired_cost_interval_and_noninferiority_are_separate():
    q=np.asarray([1.,0.,0.,0.]);baseq=np.asarray([1.,1.,1.,1.])
    c=np.asarray([.1,.1,.1,.1]);basec=np.ones(4)
    summary=MODULE.interval_summary(q,c,baseq,basec,[np.arange(4)] * 10)
    assert summary['at_least_25pct_inference_saving_supported']
    assert not summary['quality_noninferiority_3pp_supported']
    assert not summary['joint_exploratory_target_supported']
