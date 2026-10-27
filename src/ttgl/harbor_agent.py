"""Optional Harbor custom agent for the registered proprietary subset study.

Requires the separately installed Harbor runtime. The official Pro verifier and
PatchReplayAgent remain responsible for grading; this adapter never reads them.
"""
import asyncio
import json
from pathlib import Path
import shlex
import uuid
from typing import Literal

from harbor.agents.base import BaseAgent
from harbor.agents.options import AgentOptions
from harbor.models.agent.context import ModelUsage
from pydantic import Field

from . import benchmark, personal
from .harbor_bridge import EnvironmentBridge, HarborBackend


class ConversationOptions(AgentOptions):
    private_records_root: str
    condition: Literal['small', 'large', 'personal'] = 'personal'
    policy: Literal['adaptive', 'fallback'] = 'fallback'
    small_model: str = 'gpt-6-luna'
    large_model: str = 'gpt-6.1-sol'
    task_budget_seconds: float = Field(default=2940, gt=0, le=2940)


class ConversationalCodex(BaseAgent):
    options_model = ConversationOptions
    skip_model_parsing = True

    def __init__(self, *args, private_records_root: str, condition='personal', policy='fallback',
                 small_model='gpt-6-luna', large_model='gpt-6.1-sol',
                 task_budget_seconds=2940, **kwargs):
        kwargs['skip_model_parsing'] = True  # Native Codex aliases are not Harbor API-provider routes.
        kwargs.update(private_records_root=private_records_root, condition=condition, policy=policy,
                      small_model=small_model, large_model=large_model, task_budget_seconds=task_budget_seconds)
        super().__init__(*args, **kwargs)
        if condition not in ('small', 'large', 'personal'):
            raise ValueError('Use the registered standalone or cooperative arms')
        if not 1 <= float(task_budget_seconds) <= 2940:
            raise ValueError('Reserve capture time within the native 3000-second budget')
        self.condition, self.policy = condition, policy
        self.small_model, self.large_model = small_model, large_model
        self.budget = float(task_budget_seconds)
        self.private_records_root = Path(private_records_root).resolve()
        if self.private_records_root.is_relative_to(self.logs_dir.resolve()):
            raise ValueError('Authoritative host records must be outside the mounted agent logs')

    @staticmethod
    def name():
        return 'ttgl-conversational-codex'

    def version(self):
        return '0.1.0-experimental'

    async def setup(self, environment):
        result = await environment.exec(
            command='git -C /app rev-parse --show-toplevel 2>/dev/null || git -C /testbed rev-parse --show-toplevel',
            timeout_sec=30)
        repository = (result.stdout or '').strip()
        if result.return_code != 0 or not repository.startswith('/') or '\n' in repository:
            raise RuntimeError('Cannot establish assigned repository')
        self.repository = repository
        head = await environment.exec(command=f'git -C {shlex.quote(repository)} rev-parse HEAD', timeout_sec=30)
        if head.return_code:
            raise RuntimeError('Cannot establish source revision')
        self.base_head = (head.stdout or '').strip()

    async def run(self, instruction, environment, context):
        self.logs_dir.mkdir(parents=True, exist_ok=True)
        config = json.loads((self.logs_dir.parent/'config.json').read_text())
        task_id = Path(config['task']['path']).name
        if not task_id.startswith('instance_'):
            raise ValueError('Expected a registered Pro task identity')
        # Harbor may expose /logs/agent to the worker. Keep cost, prompts and
        # trace evidence elsewhere so the acting model cannot rewrite them.
        records = self.private_records_root/task_id/self.condition/uuid.uuid4().hex
        records.mkdir(parents=True, exist_ok=False)
        workspace = records/'empty-host-context'
        workspace.mkdir(exist_ok=False)
        bridge = EnvironmentBridge(environment, self.repository, records/'visible-tool-trace.jsonl').start()
        backend = HarborBackend(bridge, mode=self.policy, audit_root=records/'effective-prompts')
        task = {'task_id': task_id, 'prompt': instruction+'\nRepair the assigned repository. Do not commit, change HEAD, retrieve upstream fixes, or inspect evaluator artifacts. Report checks honestly.',
                'workspace': str(workspace.resolve()), 'allowed_paths': ['.'], 'memory': []}
        try:
            manifest = await asyncio.to_thread(personal.run_task, task, records/'controller',
                condition=self.condition, small_model=self.small_model, large_model=self.large_model,
                backend=backend, timeout_seconds=self.budget, max_turns=6, max_expert_calls=2,
                max_context_characters=24000, reasoning_effort='medium')
            usage = manifest['usage']
            context.n_input_tokens = usage['input_tokens']
            context.n_cache_tokens = usage['cached_input_tokens']
            context.n_output_tokens = usage['output_tokens']
            context.cost_usd = None  # Token-rate scenario is not a native bill.
            models = manifest['usage_by_model']
            if all(all(type(r['usage'][k]) is int for k in ('input_tokens','cached_input_tokens','output_tokens'))
                   for r in models.values()):
                context.model_usage = {name: ModelUsage(n_input_tokens=r['usage']['input_tokens'],
                    n_cache_tokens=r['usage']['cached_input_tokens'], n_output_tokens=r['usage']['output_tokens'],
                    cost_usd=None) for name, r in models.items()}
            context.metadata = {'ttgl_task_id': task_id, 'condition': self.condition,
                                'policy': self.policy, 'status': manifest['status'],
                                'private_records_path': str(records),
                                'manifest_sha256': benchmark.digest(records/'controller/manifest.json'),
                                'expert_calls': manifest['expert_calls'], 'grading': 'Official fresh-sandbox regrade required'}
        finally:
            try:
                head = await environment.exec(command=f'git -C {shlex.quote(self.repository)} rev-parse HEAD', timeout_sec=30)
                if head.return_code or (head.stdout or '').strip() != self.base_head:
                    raise RuntimeError('Agent changed repository HEAD; preserve failed attempt')
                capture = await environment.exec(command=f'cd {shlex.quote(self.repository)} && mkdir -p /logs/agent && git add -A && git diff --cached --binary > /logs/agent/model.patch && git reset -q', timeout_sec=30)
                if capture.return_code:
                    raise RuntimeError('Patch capture failed; do not silently grade an empty patch')
                if not (self.logs_dir/'model.patch').exists():
                    await environment.download_file(source_path='/logs/agent/model.patch', target_path=self.logs_dir/'model.patch')
            finally:
                await bridge.close()
