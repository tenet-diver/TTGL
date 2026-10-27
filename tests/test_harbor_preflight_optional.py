import pytest

pytest.importorskip('harbor', reason='Requires the separate Harbor runtime')
from ttgl.harbor_preflight import validate_boundary


def boundary():
    return {'head':'base','git_status':'','outside_head_commits':0,'private_path_visible':False,
            'public_endpoint_reachable':False,'witness_ignored':False}


def test_readiness_accepts_observed_clean_boundary():
    validate_boundary(boundary(), 'base')


@pytest.mark.parametrize('field,value', [('head','wrong'), ('git_status','?? unexpected'),
    ('outside_head_commits',1), ('private_path_visible',True), ('public_endpoint_reachable',True),
    ('witness_ignored',True), ('private_path_visible',None)])
def test_failed_or_missing_boundary_observations_stop_before_inference(field,value):
    observed = boundary()
    observed[field] = value
    with pytest.raises(RuntimeError):
        validate_boundary(observed, 'base')
