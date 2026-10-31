"""Model-free boundary check in each fresh router actor, before inference."""
import json
from pathlib import Path
import shlex
import uuid

from .harbor_preflight import validate_boundary


async def check_actor(environment, repository, expected_head, records_root):
    sentinel = Path(records_root)/'boundary-sentinels'/uuid.uuid4().hex
    sentinel.parent.mkdir(parents=True, exist_ok=True)
    sentinel.write_text('Model-free host-only isolation sentinel.\n')
    paths = [str(sentinel), '/tests/test.sh', '/solution/solve.sh',
             '/root/.codex/auth.json', '/home/agent/.codex/auth.json']
    program = '''import json,pathlib,socket,subprocess
paths = '''+repr(paths)+'''
def git(*args):
 return subprocess.check_output(['git',*args],text=True).strip()
reachable=False
try:
 with socket.create_connection(('1.1.1.1',443),timeout=3):reachable=True
except OSError:pass
print(json.dumps({'head':git('rev-parse','HEAD'),
 'git_status':git('status','--porcelain','--untracked-files=all'),
 'outside_head_commits':int(git('rev-list','--all','--not','HEAD','--count')),
 'private_path_visible':any(pathlib.Path(p).exists() for p in paths),
 'public_endpoint_reachable':reachable,'witness_ignored':False}))
'''
    result = await environment.exec(command=f'cd {shlex.quote(repository)} && '
                                    "python3 - <<'TTGL_BOUNDARY'\n"+program+'\nTTGL_BOUNDARY',
                                    timeout_sec=20)
    if result.return_code:
        raise RuntimeError('Fresh actor boundary probe failed; no router call started')
    observed = json.loads(result.stdout)
    validate_boundary(observed, expected_head)
    return {'status': 'fresh_actor_boundary_passed_before_router_inference',
            'observations': observed,
            'scope': 'Hidden paths plus host sentinel, clean HEAD/history, direct-IP egress probe; not universal isolation proof'}
