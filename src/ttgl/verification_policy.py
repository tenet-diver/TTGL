"""Unrun verification treatment, separate from the active frozen v2 study."""
from dataclasses import replace
from pathlib import Path

from . import benchmark, personal, policy


def verification_prompt(request):
    prompt = policy.policy_prompt(request, 'fallback')
    if request.kind != 'controller' or request.thread_id is not None:
        return prompt
    common = (policy.PROMPTS / 'controller-v3-verification-common.txt').read_text()
    cooperative = 'You are the small agent. Act yourself where useful.' in request.prompt
    delegation = ((policy.PROMPTS / 'controller-v3-verification-delegation.txt').read_text()
                  if cooperative else '')
    return prompt + '\n\nVerification treatment v3:\n' + common + '\n' + delegation


class VerificationPolicyBackend(policy.PolicyBackend):
    """Same native backend, with new prompts and a separately frozen identity.

    This is not wired into the active v2 runner. A new study must explicitly
    select this backend and freeze its identity before any model invocation.
    """

    def __init__(self, executable='codex', audit_root=None):
        super().__init__('fallback', executable, audit_root)

    def policy_identity(self):
        return {**super().policy_identity(), 'treatment': 'verification-v3',
                'verification_source_sha256': benchmark.digest(Path(__file__)),
                'verification_prompts_sha256': {
                    p.name: benchmark.digest(p)
                    for p in sorted(policy.PROMPTS.glob('controller-v3-verification-*.txt'))}}

    def complete(self, request):
        if self.policy_identity() != self.frozen_policy:
            raise ValueError('Verification policy changed during execution')
        effective = replace(request, prompt=verification_prompt(request))
        if self.audit_root is not None:
            benchmark.write_new(self.audit_root / (personal._digest(request.request_id) + '.json'), {
                'request_id': request.request_id, 'kind': request.kind,
                'model': request.model, 'thread_id': request.thread_id,
                'prompt': effective.prompt, 'policy': self.frozen_policy})
        # Avoid the parent policy layer injecting v2 a second time.
        return policy.ContainerBackend.complete(self, effective)
