"""Invocation-local native app-server client for matched memory controls.

Reuses the audited stdio client and supported API. Original RPC is the primary
record; no fabricated CLI stream, usage, timestamps or transport completions.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import sys
import time

from mcp_memory_probe import Client
from native_compaction_canary_003 import wait_turn
from tokeneconomizer_native_hooks import toml

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def save(path, value):
    with Path(path).open('x') as handle:
        json.dump(value, handle, indent=2)


def child_home(home):
    home = Path(home)
    home.mkdir(parents=True, exist_ok=False, mode=0o700)
    source = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    shutil.copyfile(source, home / 'auth.json')
    (home / 'auth.json').chmod(0o600)


def open_client(directory, home, work, task_config=None, *, memories=False, hooks=None, env_extra=None):
    directory, home, work = Path(directory), Path(home), Path(work)
    directory.mkdir(parents=True, exist_ok=False)
    runtime = str(Path(shutil.which('codex')).resolve())
    permissions = {':root': 'deny', ':minimal': 'read', str(work.resolve()): 'read', runtime: 'read'}
    if memories:
        permissions[str(home.resolve() / 'memories')] = 'read'
    settings = {
        'model_provider': 'openai', 'openai_base_url': 'http://127.0.0.1:8381/backend-api/codex',
        'project_doc_max_bytes': 0, 'features.skip_host_skill_discovery': True,
        'features.enable_request_compression': False, 'features.incremental_tools': False,
        'suppress_unstable_features_warning': True, 'web_search': 'disabled',
        'model_reasoning_effort': 'low', 'features.memories': memories,
        'memories.version': 'v1', 'memories.dual_write': False,
        'memories.generate_memories': memories, 'memories.use_memories': memories,
        'memories.extract_model': 'gpt-6-luna', 'memories.consolidation_model': 'gpt-6-luna',
        'memories.min_rollout_idle_hours': 1, 'memories.max_rollouts_per_startup': 1,
        'memories.disable_on_external_context': False,
        'default_permissions': 'ttgl_repository_app',
        'permissions.ttgl_repository_app.filesystem': permissions,
        'permissions.ttgl_repository_app.network.enabled': False,
        'features.hooks': bool(hooks),
    }
    for feature in ('multi_agent', 'plugins', 'apps', 'browser_use', 'computer_use',
                    'image_generation', 'workspace_dependencies', 'view_image', 'goals',
                    'shell_tool', 'unified_exec', 'apply_patch_freeform'):
        settings['features.' + feature] = False
    if task_config:
        settings.update({
            'mcp_servers.ttgl_task.command': sys.executable,
            'mcp_servers.ttgl_task.args': [str(HERE / 'repository_task_bridge.py'), '--config', str(Path(task_config).resolve())],
            'mcp_servers.ttgl_task.env': dict(PYTHONPATH=str(HERE) + ':' + str(REPO / 'work/security/context-memory-20261107/memory-runtime'),
                 HF_HUB_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1'),
            'mcp_servers.ttgl_task.required': True,
            'mcp_servers.ttgl_task.startup_timeout_sec': 60,
            'mcp_servers.ttgl_task.tool_timeout_sec': 240,
            'mcp_servers.ttgl_task.enabled_tools': ['terminal', 'remember', 'search_records', 'read_record'],
        })
        for tool in ('terminal', 'remember', 'search_records', 'read_record'):
            settings['mcp_servers.ttgl_task.tools.' + tool + '.approval_mode'] = 'approve'
    if hooks:
        settings['hooks'] = hooks
    cmd = ['codex']
    if hooks:
        # Supported invocation-only flag for automation that vets exact sources.
        # No persisted trust or normal plugin/config state is changed.
        cmd += ['--dangerously-bypass-hook-trust']
    cmd += ['app-server', '--listen', 'stdio://']
    for key, value in settings.items():
        cmd += ['-c', key + '=' + toml(value)]
    save(directory / 'process-intent.json', dict(command=cmd, at=datetime.now(timezone.utc).isoformat(),
         no_invocation_retry=True, child_home=str(home.resolve()), original_rpc_preserved=True))
    env = os.environ.copy()
    env['CODEX_HOME'] = str(home.resolve())
    env.update(env_extra or {})
    c = Client.__new__(Client)
    c.err = (directory / 'stderr.log').open('x')
    c.p = subprocess.Popen(cmd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=c.err, start_new_session=True)
    c.selector = selectors.DefaultSelector()
    c.selector.register(c.p.stdout, selectors.EVENT_READ)
    c.buffer, c.ident, c.calls = b'', 0, []
    c.journal = (directory / 'rpc.jsonl').open('x')
    try:
        c.request('initialize', dict(clientInfo=dict(name='ttgl_repository_control', version='1'),
                                    capabilities=dict(experimentalApi=True)))
        c.p.stdin.write(b'{"method":"initialized","params":{}}\n')
        c.p.stdin.flush()
        return c
    except BaseException:
        c.close()
        raise


def turn(client, directory, work, prompt, model='gpt-6.1-sol', timeout=1500):
    directory = Path(directory)
    (directory / 'prompt.txt').write_text(prompt)
    response = client.request('thread/start', dict(cwd=str(Path(work).resolve()), model=model,
                         modelProvider='openai', approvalPolicy='never', ephemeral=False))
    thread = response['thread']
    save(directory / 'thread.json', thread)
    sid = thread['id']
    save(directory / 'turn-intent.json', dict(session_id=sid, model=model, at=datetime.now(timezone.utc).isoformat(), no_retry=True))
    started = time.perf_counter()
    accepted = client.request('turn/start', dict(threadId=sid, input=[dict(type='text', text=prompt, text_elements=[])]))
    save(directory / 'turn-accepted.json', accepted)
    try:
        result = wait_turn(client, 'repository_solver', seconds=timeout)
        # Original RPC, not a CLI-compatible synthetic stream, is authoritative.
        client.journal.flush()
        messages = [json.loads(line).get('message', {}) for line in (directory / 'rpc.jsonl').read_text().splitlines()]
        items = [m['params']['item'] for m in messages if m.get('method') == 'item/completed']
        replies = [i['text'] for i in items if i.get('type') == 'agentMessage']
        # Match output-last-message semantics; progress stays in original RPC.
        (directory / 'answer.txt').write_text(replies[-1] if replies else '')
        save(directory / 'items.json', items)
        save(directory / 'complete.json', dict(session_id=sid, turn=result,
             process_wall_seconds=time.perf_counter() - started, source='Original native app-server RPC, no CLI counter invented',
             native_capture_usage_audit_pending=True))
        return sid, items
    except BaseException as error:
        save(directory / 'stopped.json', dict(error=str(error), no_retry=True, unknown_until_capture_audit=True))
        raise
