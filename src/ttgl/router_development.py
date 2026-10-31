"""Router-only development candidate; never modifies archived v3 treatments."""
from dataclasses import replace
from pathlib import Path

from . import benchmark, policy
from .harbor_routing_agent import DiagnosticBackend, RoutingDiagnosticCodex

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
