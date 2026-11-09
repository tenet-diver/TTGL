"""Model-selectable maintenance calls using the already audited native boundary.

No retries, implicit model fallback, plugins or model-visible filesystem tools.
Existing frozen Smallville runtimes are deliberately unchanged.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil

from longmemeval_codex_trial import native_command, run_process
from native_jsonl import validate_native_completion


class MemoryNativeCalls:
    def __init__(self, root, model, *, cap=48, port=8381):
        if model not in ('gpt-6-luna', 'gpt-6.1-sol'):
            raise ValueError('Unregistered model')
        self.root = Path(root).resolve()
        self.model, self.cap, self.port = model, cap, port
        self.registry = []
        (self.root / 'work').mkdir(parents=True, exist_ok=True)

    def command(self, cell):
        cmd = native_command(self.root / 'work', cell, self.model)
        index = cmd.index('-s')
        del cmd[index:index + 2]
        cmd[-1:-1] = ['--ignore-rules']
        for feature in ('multi_agent', 'plugins', 'apps', 'browser_use', 'computer_use',
                        'image_generation', 'workspace_dependencies', 'view_image',
                        'shell_tool', 'unified_exec', 'apply_patch_freeform', 'goals', 'hooks'):
            cmd[-1:-1] = ['--disable', feature]
        runtime = str(Path(shutil.which('codex')).resolve())
        settings = {
            'project_doc_max_bytes': 0,
            'features.skip_host_skill_discovery': True,
            'suppress_unstable_features_warning': True,
            'features.enable_request_compression': False,
            'model_provider': 'openai',
            'openai_base_url': f'http://127.0.0.1:{self.port}/backend-api/codex',
            'default_permissions': 'ttgl_memory_maintenance',
            'permissions.ttgl_memory_maintenance.filesystem': {
                ':root': 'deny', ':minimal': 'read', str(self.root / 'work'): 'read', runtime: 'read'},
            'permissions.ttgl_memory_maintenance.network.enabled': False,
            'web_search': 'disabled',
        }
        for key, value in settings.items():
            encoded = ('{' + ','.join(json.dumps(k) + '=' + json.dumps(v)
                                      for k, v in value.items()) + '}'
                       if isinstance(value, dict) else json.dumps(value))
            cmd[-1:-1] = ['-c', key + '=' + encoded]
        return cmd

    def __call__(self, prompt, role):
        if len(self.registry) >= self.cap:
            raise ValueError('Registered call cap')
        cell = self.root / f'call-{len(self.registry) + 1:03d}'
        cell.mkdir()  # Existing/uncertain calls can never be silently repeated.
        (cell / 'prompt.txt').write_text(prompt)
        intent = dict(model=self.model, role=role, at=datetime.now(timezone.utc).isoformat(),
                      prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), no_retry=True)
        (cell / 'intent.json').write_text(json.dumps(intent, indent=2))
        run_process(self.command(cell), prompt, cell, 600)
        sid = validate_native_completion(cell, no_tools=True)
        row = dict(cell=cell.name, session_id=sid, model=self.model, role=role)
        self.registry.append(row)
        (cell / 'complete.json').write_text(json.dumps(row, indent=2))
        (self.root / 'registry.json').write_text(json.dumps(self.registry, indent=2))
        return (cell / 'answer.txt').read_text()
