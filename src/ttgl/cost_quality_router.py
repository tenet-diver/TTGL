"""Consolidated general policy, matched common guidance for Sol and Luna router."""
import asyncio
from dataclasses import replace
from pathlib import Path
import time

from . import benchmark, personal, policy
from .actor_boundary import check_actor
from .harbor_routing_agent import DiagnosticBackend, RoutingDiagnosticCodex

COMMON = policy.PROMPTS/'controller-v7-common.txt'
ROUTING = policy.PROMPTS/'controller-v7-routing.txt'


class CostQualityBackend(DiagnosticBackend):
    def diagnostic_identity(self):
        return {'mode': 'consolidated-v7', 'source_sha256': benchmark.digest(Path(__file__)),
                'common_sha256': benchmark.digest(COMMON),
                'routing_sha256': benchmark.digest(ROUTING),
                'transport_sha256': benchmark.digest(Path(__file__).with_name('harbor_bridge.py')),
                'snapshot_source_sha256': benchmark.digest(Path(__file__).with_name('harbor_routing_agent.py'))}

    def describe(self):
        return {**super().describe(), 'controller_policy': self.diagnostic_identity()}

    def complete(self, request):
        if self.diagnostic_identity() != self.frozen_diagnostic:
            raise ValueError('Consolidated policy or transport changed during execution')
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
            capture_seconds = time.monotonic()-began
            request = replace(request, timeout_seconds=max(0, request.timeout_seconds-capture_seconds))
        prompt = request.prompt
        if request.kind == 'controller' and request.thread_id is None:
            prompt += '\n\nGeneral solving and verification policy v7:\n'+COMMON.read_text()
            if 'You are the small agent. Act yourself where useful.' in request.prompt:
                prompt += '\n\nVoluntary consultation policy v7:\n'+ROUTING.read_text()
        if not request.read_only:
            prompt += ('\nUse only the worker shell MCP tool for repository work. Its repository is '
                       + self.bridge.repository+' inside the assigned environment; the host workspace is empty.')
        benchmark.write_new(self.audit_root/(personal._digest(request.request_id)+'.json'), {
            'request_id':request.request_id,'kind':request.kind,'prompt':prompt,
            'policy':self.frozen_diagnostic})
        if not request.read_only:
            self.bridge.active_request = {'request_id':request.request_id,'model':request.model,'kind':request.kind}
        try:
            # Keep the supported Codex/MCP command path, without stacking archived
            # v2/v3/v4/v6 policy text onto this separately registered treatment.
            response = personal.CodexBackend.complete(self, replace(request,prompt=prompt))
            if capture_seconds:
                response.elapsed_seconds += capture_seconds
            return response
        finally:
            if not request.read_only:
                self.bridge.active_request = {}


class CostQualityCodex(RoutingDiagnosticCodex):
    @staticmethod
    def name():
        return 'ttgl-cost-quality-v7'

    def make_backend(self, bridge, records):
        if self.policy != 'verification' or self.condition not in ('personal','large'):
            raise ValueError('Matched v7 requires voluntary router or Sol-only condition')
        return CostQualityBackend(bridge, diagnostic='verification', records=records)

    async def run(self, instruction, environment, context):
        boundary = await check_actor(environment,self.repository,self.base_head,self.private_records_root)
        benchmark.write_new(self.logs_dir/'actor-boundary.json',boundary)
        await super().run(instruction,environment,context)
        context.metadata['fresh_actor_boundary'] = boundary
