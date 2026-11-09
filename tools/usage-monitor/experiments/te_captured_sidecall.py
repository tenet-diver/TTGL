"""Capture upstream TokenEconomizer Codex sidecalls without changing its prompts.

Invocation-local PATH shim only. Retain native sessions for metering; disable
model tools on maintenance calls. No retries or normal Codex configuration edits.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import uuid


def main():
    if os.environ.get('TE_SIDECALL') != '1':
        raise ValueError('This shim is exclusively for upstream maintenance calls')
    root = Path(os.environ['TTGL_TE_SIDECALL_RECORDS'])
    root.mkdir(parents=True, exist_ok=True)
    if len(list(root.glob('call-*'))) >= 512:
        raise ValueError('Registered maintenance-call ceiling reached')
    cell = root / ('call-' + uuid.uuid4().hex)
    cell.mkdir()
    incoming = sys.argv[1:]
    if not incoming or incoming[0] != 'exec':
        raise ValueError('Unsupported sidecall command')
    prompt = incoming[-1]
    (cell / 'prompt.txt').write_text(prompt)
    incoming = [x for x in incoming[:-1] if x != '--ephemeral']
    cmd = [os.environ['TTGL_TE_NATIVE_CODEX'], *incoming, '--ignore-user-config', '--ignore-rules',
           '-c', 'openai_base_url="http://127.0.0.1:8381/backend-api/codex"',
           '-c', 'model_provider="openai"', '-c', 'model_reasoning_effort="low"',
           '-c', 'features.enable_request_compression=false',
           '-c', 'suppress_unstable_features_warning=true',
           '-c', 'features.skip_host_skill_discovery=true', '-c', 'project_doc_max_bytes=0',
           '--output-last-message', str(cell / 'answer.txt')]
    for feature in ('shell_tool', 'unified_exec', 'apply_patch_freeform', 'plugins', 'apps',
                    'browser_use', 'computer_use', 'image_generation', 'view_image', 'multi_agent', 'goals'):
        cmd += ['--disable', feature]
    cmd += ['-']
    from longmemeval_codex_trial import run_process
    from native_jsonl import validate_native_completion
    run_process(cmd, prompt, cell, 180)
    sid = validate_native_completion(cell, no_tools=True)
    (cell / 'complete.json').write_text(json.dumps(dict(session_id=sid, no_retry=True)))
    sys.stdout.write((cell / 'agent.jsonl').read_text())


if __name__ == '__main__':
    main()
