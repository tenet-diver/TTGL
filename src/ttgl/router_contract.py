"""Separately versioned v6 changed-contract verification candidate for development."""
from dataclasses import replace
from pathlib import Path

from . import benchmark, policy
from .router_development import RouterDevelopmentBackend, RouterDevelopmentCodex

PROMPT = policy.PROMPTS/'controller-v6-contract-evidence.txt'


class ContractEvidenceBackend(RouterDevelopmentBackend):
    def diagnostic_identity(self):
        return {**super().diagnostic_identity(),
                'completion_source_sha256': benchmark.digest(Path(__file__)),
                'completion_prompt_sha256': benchmark.digest(PROMPT)}

    def complete(self, request):
        if self.diagnostic_identity() != self.frozen_diagnostic:
            raise ValueError('Completion-evidence policy changed during execution')
        if request.kind == 'controller' and request.thread_id is None:
            request = replace(request, prompt=request.prompt+'\n\n'+PROMPT.read_text())
        return super().complete(request)


class RouterContractCodex(RouterDevelopmentCodex):
    @staticmethod
    def name():
        return 'ttgl-router-contract-v6'

    def make_backend(self, bridge, records):
        if self.condition != 'personal' or self.policy != 'verification':
            raise ValueError('Completion development requires voluntary personal condition')
        return ContractEvidenceBackend(bridge, diagnostic='verification', records=records)
