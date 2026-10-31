"""Router-only development candidate; never modifies archived v3 treatments."""
from dataclasses import replace
from pathlib import Path

from . import benchmark, policy
from .harbor_routing_agent import DiagnosticBackend, RoutingDiagnosticCodex
from .actor_boundary import check_actor

PROMPT = policy.PROMPTS / 'controller-v4-router-decisions.txt'


class RouterDevelopmentBackend(DiagnosticBackend):
    def diagnostic_identity(self):
        return {**super().diagnostic_identity(),
                'router_development_source_sha256': benchmark.digest(Path(__file__)),
                'router_decisions_prompt_sha256': benchmark.digest(PROMPT)}

    def complete(self, request):
        if self.diagnostic_identity() != self.frozen_diagnostic:
            raise ValueError('Router development policy changed during execution')
        if request.kind == 'controller' and request.thread_id is None:
            request = replace(request, prompt=request.prompt + '\n\n' + PROMPT.read_text())
        return super().complete(request)


class RouterDevelopmentCodex(RoutingDiagnosticCodex):
    @staticmethod
    def name():
        return 'ttgl-router-development'

    def make_backend(self, bridge, records):
        if self.condition != 'personal' or self.policy != 'verification':
            raise ValueError('Router development requires voluntary personal condition')
        return RouterDevelopmentBackend(bridge, diagnostic='verification', records=records)

    async def run(self, instruction, environment, context):
        boundary = await check_actor(environment, self.repository, self.base_head,
                                     self.private_records_root)
        benchmark.write_new(self.logs_dir/'actor-boundary.json', boundary)
        await super().run(instruction, environment, context)
        context.metadata['fresh_actor_boundary'] = boundary
