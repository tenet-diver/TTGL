import importlib.util
from pathlib import Path

import pytest

spec = importlib.util.spec_from_file_location('feedback_subset', Path(__file__).parents[1]/'scripts/prepare_feedback_subset.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def inventory():
    # Same exercise families in all tracks exercise cross-language leakage.
    return {'sha': module.REVISION, 'truncated': False, 'tree': [
        {'path': f'{language}/exercises/practice/family-{i}/.docs/instructions.md'}
        for language, count in zip(module.LANGUAGES, (26,39,47,49,34,30))
        for i in range(count)]}


def test_panels_are_balanced_stable_and_family_disjoint():
    tree = inventory()
    dev, held = module.reserve(tree)
    assert len(dev) == 12 and len(held) == 24
    assert not {r['exercise_family'] for r in dev} & {r['exercise_family'] for r in held}
    assert all(sum(r['language'] == language for r in dev) == 2 for language in module.LANGUAGES)
    assert all(sum(r['language'] == language for r in held) == 4 for language in module.LANGUAGES)
    tree['tree'].reverse()
    assert module.reserve(tree) == (dev, held)


@pytest.mark.parametrize('change', ['truncated', 'sha', 'duplicate'])
def test_invalid_inventory_is_rejected(change):
    tree = inventory()
    if change == 'duplicate':
        tree['tree'][-1] = tree['tree'][0]
    else:
        tree[change] = True if change == 'truncated' else 'wrong-revision'
    with pytest.raises(ValueError):
        module.reserve(tree)
