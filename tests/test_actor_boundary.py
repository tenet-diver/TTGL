import pytest

pytest.importorskip('harbor')


@pytest.mark.parametrize('violation', [None, 'private_path_visible', 'public_endpoint_reachable', 'git_status'])
def test_fresh_actor_boundary_accepts_clean_actor_and_rejects_exposure(tmp_path, violation):
    import asyncio
    import json
    from types import SimpleNamespace
    from ttgl.actor_boundary import check_actor
    observed = {'head':'assigned-base','git_status':'','outside_head_commits':0,
                'private_path_visible':False,'public_endpoint_reachable':False,'witness_ignored':False}
    if violation:
        observed[violation] = ' M source.py' if violation=='git_status' else True
    class Environment:
        async def exec(self, **kwargs):
            return SimpleNamespace(return_code=0, stdout=json.dumps(observed))
    call = check_actor(Environment(), '/app', 'assigned-base', tmp_path/'host-records')
    if violation:
        with pytest.raises(RuntimeError, match='boundary'):
            asyncio.run(call)
    else:
        receipt = asyncio.run(call)
        assert receipt['status']=='fresh_actor_boundary_passed_before_router_inference'
        assert receipt['observations']['private_path_visible'] is False
