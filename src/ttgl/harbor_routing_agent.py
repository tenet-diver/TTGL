"""Unrun optional-routing / required-review diagnostics on maintained Harbor."""
import asyncio
from dataclasses import replace
from pathlib import Path
import shlex
import shutil
import time
from typing import Literal
import uuid

from . import benchmark, policy
from .harbor_agent import ConversationalCodex, ConversationOptions
from .harbor_bridge import HarborBackend
from .verification_policy import verification_prompt


class DiagnosticOptions(ConversationOptions):
    policy: Literal['verification', 'required_review'] = 'verification'


class DiagnosticBackend(HarborBackend):
    def __init__(self, bridge, *, diagnostic, records):
        if diagnostic not in ('verification', 'required_review'):
            raise ValueError('Unknown diagnostic policy')
        super().__init__(bridge, mode='fallback', audit_root=records/'effective-prompts')
        self.diagnostic, self.records = diagnostic, Path(records)
        self.frozen_diagnostic = self.diagnostic_identity()

    def diagnostic_identity(self):
        return {'mode': self.diagnostic,
                'source_sha256': benchmark.digest(Path(__file__)),
                'verification_source_sha256': benchmark.digest(Path(__file__).with_name('verification_policy.py')),
                'prompts_sha256': {p.name: benchmark.digest(p)
                                  for p in sorted(policy.PROMPTS.glob('controller-v3-*.txt'))}}

    def describe(self):
        return {**super().describe(), 'routing_diagnostic': self.diagnostic_identity()}

    async def capture_candidate(self, request):
        """Host snapshot before first consultation; no grader feedback involved.

        A temporary Git index captures new files without changing the actor's
        actual index. The snapshot is downloaded outside all mounted logs.
        """
        key = uuid.uuid4().hex
        index, patch = '/tmp/ttgl-index-'+key, '/tmp/ttgl-candidate-'+key+'.patch'
        repository = shlex.quote(self.bridge.repository)
        command = (f'cd {repository}; '
                   f'trap "rm -f {index} {index}.lock" EXIT; '
                   f'export GIT_INDEX_FILE={index}; '
                   'git read-tree HEAD && git add -A && '
                   f'git diff --cached HEAD --binary > {patch}')
        # Stop immediately if the assigned repository is unavailable.
        command = 'set -e; '+command
        try:
            result = await self.bridge.environment.exec(command=command, timeout_sec=30)
            if result.return_code:
                raise RuntimeError('Pre-handoff candidate capture failed; no expert call made')
            target = self.records/'pre-handoff.patch'
            await self.bridge.environment.download_file(source_path=patch, target_path=target)
            benchmark.write_new(self.records/'pre-handoff.json', {
                'request_id': request.request_id, 'patch_sha256': benchmark.digest(target),
                'role': 'Candidate before first expert response; not graded during generation',
                'independent_regrade_required': True})
        finally:
            await self.bridge.environment.exec(command=f'rm -f {patch} {index} {index}.lock', timeout_sec=10)

    def complete(self, request):
        if self.diagnostic_identity() != self.frozen_diagnostic:
            raise ValueError('Diagnostic policy changed during execution')
        capture_seconds = 0
        if request.kind == 'expert' and not (self.records/'pre-handoff.json').exists():
            began = time.monotonic()
            future = self.bridge.execution_context.copy().run(
                asyncio.run_coroutine_threadsafe, self.capture_candidate(request), self.bridge.loop)
            try:
                future.result(timeout=50)
            except BaseException:
                future.cancel()
                raise
            capture_seconds = time.monotonic() - began
            request = replace(request, timeout_seconds=max(0, request.timeout_seconds-capture_seconds))
        if request.kind == 'controller' and request.thread_id is None:
            base = policy.policy_prompt(request, 'fallback')
            extra = verification_prompt(request)[len(base):]
            cooperative = 'You are the small agent. Act yourself where useful.' in request.prompt
            if cooperative and self.diagnostic == 'required_review':
                extra += '\n'+(policy.PROMPTS/'controller-v3-required-review.txt').read_text()
            request = replace(request, prompt=request.prompt+extra)
        response = super().complete(request)
        if capture_seconds:
            response.elapsed_seconds += capture_seconds
        return response


class RoutingDiagnosticCodex(ConversationalCodex):
    options_model = DiagnosticOptions

    def __init__(self, *args, policy='verification', **kwargs):
        if policy not in ('verification', 'required_review'):
            raise ValueError('Unknown diagnostic policy')
        super().__init__(*args, policy=policy, **kwargs)

    @staticmethod
    def name():
        return 'ttgl-routing-diagnostic'

    def make_backend(self, bridge, records):
        return DiagnosticBackend(bridge, diagnostic=self.policy, records=records)

    async def run(self, instruction, environment, context):
        await super().run(instruction, environment, context)
        records = Path(context.metadata['private_records_path'])
        snapshot = records/'pre-handoff.json'
        if snapshot.exists():
            # Model generation has ended. Publish a derivative for the unchanged
            # official replay agent's patch_name option; host copy stays authoritative.
            shutil.copyfile(records/'pre-handoff.patch', self.logs_dir/'pre-handoff.patch')
        context.metadata.update({
            'pre_handoff_snapshot': str(snapshot) if snapshot.exists() else None,
            'required_review_observed': (context.metadata['expert_calls'] > 0
                                         if self.policy == 'required_review' and self.condition == 'personal'
                                         else None),
            'analysis': 'Grade final and pre-handoff patches independently after generation; never send grades to the controller'})
