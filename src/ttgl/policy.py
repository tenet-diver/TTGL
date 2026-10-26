"""Prompt-only development treatments; the frozen pilot runner is unchanged."""
from dataclasses import replace
from pathlib import Path

from . import benchmark, personal
from .isolated import ContainerBackend

PROMPTS = Path(__file__).resolve().parents[2] / 'prompts'
MODES = ('adaptive', 'fallback')


def policy_prompt(request, mode: str) -> str:
    """Apply shared solving guidance to both standalone and assisted controllers.

    Expert/router prompts and resumed controller messages retain their existing
    semantics. The first controller message persists in its Codex thread.
    """
    if mode not in MODES:
        raise ValueError('Unknown delegation policy')
    if request.kind != 'controller' or request.thread_id is not None:
        return request.prompt
    common = (PROMPTS / 'controller-v2-common.txt').read_text()
    # Existing run_task establishes whether consultation is actually permitted.
    # Never grant expert actions to the matched standalone control.
    cooperative = 'You are the small agent. Act yourself where useful.' in request.prompt
    specific = ''
    if cooperative:
        name = 'delegation' if mode == 'adaptive' else 'fallback'
        specific = (PROMPTS / f'controller-v2-{name}.txt').read_text()
    return request.prompt + '\n\nController policy v2:\n' + common + '\n' + specific


class PolicyBackend(ContainerBackend):
    def __init__(self, mode='adaptive', executable='codex', audit_root=None):
        if mode not in MODES:
            raise ValueError('Unknown delegation policy')
        super().__init__(executable)
        self.mode = mode
        self.audit_root = Path(audit_root) if audit_root is not None else None
        self.frozen_policy = self.policy_identity()

    def policy_identity(self):
        return {'mode': self.mode, 'source_sha256': benchmark.digest(Path(__file__)),
                'prompts_sha256': {path.name: benchmark.digest(path)
                    for path in sorted(PROMPTS.glob('controller-v2-*.txt'))}}

    def describe(self):
        return {**super().describe(), 'controller_policy': self.policy_identity()}

    def complete(self, request):
        if self.policy_identity() != self.frozen_policy:
            raise ValueError('Controller policy changed during execution')
        effective = replace(request, prompt=policy_prompt(request, self.mode))
        if self.audit_root is not None:
            # The ordinary run journal contains the original harness prompt.
            # Preserve the effective policy-injected prompt separately before
            # invocation, with the same unique request identity, including roles
            # which intentionally do not receive an injected policy.
            key = personal._digest(request.request_id)
            benchmark.write_new(self.audit_root / (key + '.json'), {
                'request_id': request.request_id, 'kind': request.kind,
                'model': request.model, 'thread_id': request.thread_id,
                'prompt': effective.prompt, 'policy': self.frozen_policy})
        return super().complete(effective)
