"""Invocation-local vetted upstream hooks; one native compatibility canary.

No plugin installation, persisted hook trust or normal routing/config changes.
"""
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import sys

from smallville_native_mechanism import GLOBAL, HERE, write, sha
from longmemeval_codex_trial import native_command, run_process
from native_jsonl import validate_native_completion

REVIEW = HERE.parents[2] / 'work/security/tokeneconomizer-review-20261109'
ROOT = GLOBAL / 'tokeneconomizer-native-hooks-001'
PROTOCOL = HERE.parent / 'studies/tokeneconomizer-native-hooks-protocol-001.json'


def toml(value):
    if isinstance(value, dict):
        return '{' + ','.join(json.dumps(k) + '=' + toml(v) for k, v in value.items()) + '}'
    if isinstance(value, list):
        return '[' + ','.join(toml(v) for v in value) + ']'
    return json.dumps(value)


def main():
    os.umask(0o077)
    ROOT.mkdir()
    work = ROOT / 'work'
    work.mkdir()
    (work / 'marker.txt').write_text('native-hook-compatibility-marker-20261109')
    (ROOT / 'outside.txt').write_text('private-owned-marker-not-for-model')
    (ROOT / 'protocol.json').write_bytes(PROTOCOL.read_bytes())
    receipt = json.loads((REVIEW / 'pre-execution-receipt.json').read_text())
    if receipt['confirmed_findings']:
        raise ValueError('Confirmed vulnerabilities block')
    definitions = json.loads((REVIEW / 'source/plugin/hooks/codex-hooks.json').read_text())['hooks']
    launcher = REVIEW / 'source/plugin/scripts/te_bootstrap.py'
    for groups in definitions.values():
        for group in groups:
            for hook in group['hooks']:
                hook['command'] = shlex.join([sys.executable, str(launcher), 'hook', '--host', 'codex'])
                hook.pop('commandWindows', None)
    runtime = str(Path(shutil.which('codex')).resolve())
    settings = {
        'project_doc_max_bytes': 0, 'features.skip_host_skill_discovery': True,
        'features.enable_request_compression': False, 'model_provider': 'openai',
        'openai_base_url': 'http://127.0.0.1:8381/backend-api/codex',
        'default_permissions': 'ttgl_te_hook_canary',
        'permissions.ttgl_te_hook_canary.filesystem': {
            ':root': 'deny', ':minimal': 'read', str(work): 'read', runtime: 'read'},
        'permissions.ttgl_te_hook_canary.network.enabled': False,
        'web_search': 'disabled', 'suppress_unstable_features_warning': True,
        'hooks': definitions,
    }
    control = ['codex', 'sandbox', '-P', 'ttgl_te_hook_canary', '-C', str(work)]
    for k, v in settings.items():
        if k.startswith(('default_permissions', 'permissions.')):
            control += ['-c', k + '=' + toml(v)]
    results = []
    for target in (work / 'marker.txt', ROOT / 'outside.txt'):
        r = subprocess.run(control + ['--', '/bin/cat', str(target)], capture_output=True, timeout=30)
        results.append(dict(exit_code=r.returncode, exact=r.stdout == target.read_bytes()))
    passed = results[0]['exit_code'] == 0 and results[0]['exact'] and results[1]['exit_code'] != 0 and not results[1]['exact']
    write(ROOT / 'boundary.json', dict(passed=passed, cells=results, model_calls=0))
    if not passed:
        raise ValueError('Own boundary failed')
    paths = [Path(__file__), PROTOCOL, REVIEW / 'pre-execution-receipt.json']
    paths += [p for p in (REVIEW / 'source/tokeneconomizer').rglob('*.py')]
    write(ROOT / 'manifest.json', dict(sources={str(p): sha(p) for p in paths}, runtime=runtime, model_calls=0))
    env = dict(TOKENECONOMIZER_HOME=str(ROOT / 'state'), TE_CORE_PATH=str(REVIEW / 'source'),
               TE_PLUGIN_ROOT=str(REVIEW / 'source/plugin'), TE_MICROSKILLS='envfacts',
               TE_FOLD_SYNC='1', TE_HISTORY_IMPORT='off')
    previous = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    cell = ROOT / 'solver'
    cell.mkdir()
    prompt = 'Read marker.txt with a shell command in the current directory. Return its exact contents only. Do not read any other paths, install anything or use the network.'
    (cell / 'prompt.txt').write_text(prompt)
    cmd = native_command(work, cell, 'gpt-6.1-sol')
    index = cmd.index('-s')
    del cmd[index:index + 2]
    cmd[-1:-1] = ['--ignore-rules', '--dangerously-bypass-hook-trust', '--enable', 'hooks']
    for feature in ('multi_agent', 'plugins', 'apps', 'browser_use', 'computer_use',
                    'image_generation', 'workspace_dependencies', 'view_image', 'goals'):
        cmd[-1:-1] = ['--disable', feature]
    for k, v in settings.items():
        cmd[-1:-1] = ['-c', k + '=' + toml(v)]
    write(ROOT / 'started.json', dict(pid=os.getpid(), no_retry=True))
    try:
        run_process(cmd, prompt, cell, 600)
        sid = validate_native_completion(cell)
        event_files = list((ROOT / 'state').rglob('events.jsonl'))
        events = [json.loads(line) for p in event_files for line in p.read_text().splitlines()]
        kinds = sorted({x.get('kind', '') for x in events})
        sessions = list((ROOT / 'state').rglob('sessions/*.json'))
        session_records = [json.loads(p.read_text()) for p in sessions]
        write(ROOT / 'complete.json', dict(session_id=sid,
            passed=(cell / 'answer.txt').read_text().strip() == (work / 'marker.txt').read_text() and
                   bool(events) and any(x.get('session_id') == sid for x in session_records),
            event_kinds=kinds, session_records=len(session_records), model_processes=1,
            scope='Native reviewed hook transport only; forced source read, not benchmark performance'))
    except BaseException as error:
        write(ROOT / 'stopped.json', dict(error=type(error).__name__, message=str(error), no_retry=True))
        raise
    finally:
        for k, v in previous.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


if __name__ == '__main__':
    main()
