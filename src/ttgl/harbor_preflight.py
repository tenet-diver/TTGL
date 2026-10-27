"""Real-environment preflight; setup inference is never benchmark accuracy."""
import json
from pathlib import Path
import shlex
import uuid
from typing import Literal

from pydantic import Field

from . import benchmark
from .harbor_routing_agent import RoutingDiagnosticCodex, DiagnosticOptions


def validate_boundary(observed, expected_head):
    if (observed.get('head') != expected_head or observed.get('git_status') != ''
            or observed.get('outside_head_commits') != 0
            or observed.get('private_path_visible') is not False
            or observed.get('public_endpoint_reachable') is not False
            or observed.get('witness_ignored') is not False):
        raise RuntimeError('Real actor boundary/readiness preflight failed before inference')


class PreflightOptions(DiagnosticOptions):
    condition: Literal['personal'] = 'personal'
    policy: Literal['required_review'] = 'required_review'
    task_budget_seconds: float = Field(default=180, gt=0, le=180)


class NativeProPreflight(RoutingDiagnosticCodex):
    options_model = PreflightOptions

    def __init__(self, *args, condition='personal', policy='required_review', task_budget_seconds=180, **kwargs):
        if condition != 'personal' or policy != 'required_review' or not 0 < task_budget_seconds <= 180:
            raise ValueError('Use the registered bounded preflight settings')
        super().__init__(*args, condition=condition, policy=policy,
                         task_budget_seconds=task_budget_seconds, **kwargs)

    @staticmethod
    def name():
        return 'ttgl-native-pro-preflight'

    async def run(self, instruction, environment, context):
        identity = uuid.uuid4().hex
        marker = 'TTGL-PREFLIGHT-'+identity
        witness = 'ttgl_preflight_'+identity+'.txt'
        sentinel = self.private_records_root/'boundary-sentinels'/identity
        sentinel.parent.mkdir(parents=True, exist_ok=True)
        sentinel.write_text('Host-only boundary fixture; not a credential.\n')
        paths = [str(sentinel), '/tests/test.sh', '/solution/solve.sh',
                 '/root/.codex/auth.json', '/home/agent/.codex/auth.json']
        program = '''import json,pathlib,socket,subprocess
paths = '''+repr(paths)+'''
witness = '''+repr(witness)+'''
def git(*args):
 return subprocess.check_output(['git',*args],text=True).strip()
reachable=False
try:
 with socket.create_connection(('1.1.1.1',443),timeout=3):reachable=True
except OSError:pass
ignored=subprocess.run(['git','check-ignore','--quiet',witness]).returncode
if ignored not in (0,1):raise RuntimeError('Cannot establish witness visibility')
print(json.dumps({'head':git('rev-parse','HEAD'),'git_status':git('status','--porcelain','--untracked-files=all'),
 'outside_head_commits':int(git('rev-list','--all','--not','HEAD','--count')),
 'private_path_visible':any(pathlib.Path(p).exists() for p in paths),
 'public_endpoint_reachable':reachable,'witness_ignored':ignored==0}))
'''
        command = f'cd {shlex.quote(self.repository)} && python3 - <<\'TTGL_PROBE\'\n'+program+'\nTTGL_PROBE'
        result = await environment.exec(command=command, timeout_sec=20)
        if result.return_code:
            raise RuntimeError('Boundary probe command unavailable; no model call made')
        observed = json.loads(result.stdout)
        validate_boundary(observed, self.base_head)
        # Do not pass the original issue to this mechanism-only preflight.
        prompt = (f'This is a transport/metering preflight, not a software repair. '
                  f'Use the worker MCP tool to create exactly one new file named {witness} '
                  f'in the repository, containing exactly {marker} followed by a newline. '
                  'Read it back through the worker and obtain git rev-parse HEAD. '
                  'Do not edit any other file or fix the benchmark issue. '
                  'Request specialist review of those actual observations, including the filename, '
                  'marker and HEAD in your selected context, then complete with the observations. '
                  'The specialist must not claim to have executed commands.')
        await super().run(prompt, environment, context)
        records = Path(context.metadata['private_records_path'])
        manifest = json.loads((records/'controller/manifest.json').read_text())
        if (manifest['status'] != 'completed_ungraded' or manifest['expert_calls'] < 1
                or manifest['usage_accounting_issues']):
            raise RuntimeError('Native preflight did not complete a metered handoff; preserve attempt')
        for name in (self.small_model, self.large_model):
            usage = manifest['usage_by_model'].get(name, {}).get('usage', {})
            if any(type(usage.get(k)) is not int or usage[k] <= 0 for k in ('input_tokens','output_tokens')):
                raise RuntimeError('Positive native per-model preflight usage missing')
        expert_requests = [json.loads(line) for line in (records/'controller/events.jsonl').read_text().splitlines()
                           if json.loads(line).get('event') == 'request' and json.loads(line).get('kind') == 'expert']
        if not any(marker in r['prompt'] and witness in r['prompt'] and self.base_head in r['prompt']
                   for r in expert_requests):
            raise RuntimeError('Actual preflight observations were not handed to expert')
        check = await environment.exec(command=f'cd {shlex.quote(self.repository)} && '
            'git status --porcelain --untracked-files=all && '
            f'cat {shlex.quote(witness)}', timeout_sec=20)
        if check.return_code or check.stdout != '?? '+witness+'\n'+marker+'\n':
            raise RuntimeError('Preflight made unexpected changes or failed to write the witness')
        if not (self.logs_dir/'model.patch').stat().st_size:
            raise RuntimeError('Nonempty native preflight replay patch missing')
        receipt = {'status':'real_actor_native_handoff_preflight_passed_replay_still_required',
                   'boundary_observations':observed, 'witness':witness, 'marker':marker,
                   'patch_sha256':benchmark.digest(self.logs_dir/'model.patch'),
                   'private_manifest_sha256':benchmark.digest(records/'controller/manifest.json'),
                   'expert_calls':manifest['expert_calls'],
                   'network_scope':'Configured no-network agent phase plus one direct-IP egress probe, not a universal network-security proof',
                   'benchmark_accuracy_claim':False}
        benchmark.write_new(records/'preflight.json',receipt)
        context.metadata['preflight'] = receipt
