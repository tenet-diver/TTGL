import numpy as np
import pytest
from scipy import sparse
from ttgl.routing import (exact_budget_mask, fit_soft_logistic, policy_outcomes,
                          cluster_bootstrap_indices, outcome)


def test_exact_budget_and_stable_ties():
    result = exact_budget_mask([0.8, 0.8, 0.9, 0.1], 0.5, ["b", "a", "c", "d"])
    np.testing.assert_array_equal(result, [0, 1, 1, 0])


def test_pre_call_routing_includes_remote_regressions():
    local = np.array([1.0, 0.1, 0.5, 0.0])
    remote = np.array([0.0, 0.9, 0.5, 0.2])
    chosen = exact_budget_mask(remote-local, 0.5, list("abcd"))
    np.testing.assert_allclose(policy_outcomes(local, remote, chosen), [1, 0.9, 0.5, 0.2])


def test_random_expected_is_linear_mixture():
    np.testing.assert_allclose(policy_outcomes(np.array([0, 1]), np.array([1, 0]), 0.5), [0.5, 0.5])


def test_cluster_bootstrap_never_splits_contest():
    for indices in cluster_bootstrap_indices(["a", "a", "b", "c", "c"], 30):
        counts = np.bincount(indices, minlength=5)
        assert counts[0] == counts[1]
        assert counts[3] == counts[4]


def test_soft_logistic_learns_fractional_outcomes():
    x = sparse.csr_matrix(np.arange(20).reshape(-1, 1)/5)
    y = np.linspace(0.1, 0.9, 20)
    model = fit_soft_logistic(x, y)
    predicted = model.predict_proba(x)[:, 1]
    assert predicted[-1] > predicted[0]
    assert 0 < predicted.min() < predicted.max() < 1


def test_labels_require_real_booleans_and_ten_samples():
    with pytest.raises(ValueError):
        outcome([{"grades": [1]*10}], "grades")
    assert outcome([{"grades": [True]*3 + [False]*7}], "grades")[0] == pytest.approx(0.3)


def test_invalid_budget_rejected():
    with pytest.raises(ValueError):
        exact_budget_mask([1], 1.1, ["a"])
