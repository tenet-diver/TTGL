"""Isolated native-memory mechanism probe; never a coding benchmark score.

Uses the documented child Codex-home location for its intended purpose, without
changing the normal home, config, auth, or memory. No fabricated idle timestamps.
The seed is public repository documentation, not grading feedback. Background
native calls use the capture route and are part of probe overhead.
"""
from datetime import datetime, timezone, timedelta
import argparse
import json
import os
from pathlib import Path
import selectors
import shutil
import sqlite3
import subprocess
import time

from mcp_memory_probe import Client
from native_compaction_canary_003 import wait_turn

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO / 'work/security/repository-memory-20261110/native-memory-feature-002'


def write(path, value):
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)
        handle.write('\n')


def prepare():
    os.umask(0o077)
    ROOT.mkdir()
    (ROOT / 'home').mkdir(mode=0o700)
    (ROOT / 'work').mkdir()
    # Credentials are reused only by the authenticated native client, not actors
    # or memory. Never print them, put them in prompts, or modify the original.
    auth_source = Path(os.environ.get('CODEX_HOME', str(Path.home() / '.codex'))) / 'auth.json'
    shutil.copyfile(auth_source, ROOT / 'home/auth.json')
    (ROOT / 'home/auth.json').chmod(0o600)
    source = Path('/tmp/ttgl-repository-memory-20261110/source/aws-cloudformation-cfn-lint-1c42cb6')
    evidence = {name: (source / name).read_text()[:8000]
                for name in ('setup.py', 'tox.ini', 'CONTRIBUTING.md')}
    prompt = ('This is a repository-environment memory mechanism diagnostic, not a task-solving score. '
              'Summarize reusable procedures and constraints supported by the supplied public source '
              'documents. Do not claim any test passed: these documents are not execution receipts. '
              'Separate observations from hypotheses, include file provenance, and keep uncertainties. '
              'Do not use tools, install anything, access credentials or network, or delegate. '
              'Return a concise useful record of how this repository is packaged and tested.\n'
              + json.dumps(evidence))
    (ROOT / 'seed.txt').write_text(prompt)
    write(ROOT / 'protocol.json', dict(id='native-memory-feature-002',
          model='gpt-6-luna', coding_trials=0, purpose='Actual native generation/injection in isolated store',
          seed_agent_turns=1, followup_agent_turns=1,
          native_background_inference='Additional, fully captured and counted; not free. Inspect before continuing.',
          minimum_idle_hours=1, timestamp_manipulation=False, native_version='v1',
          cadence_adaptation='Documented minimum1h, default6h not claimed; no forced database edits',
          no_invocation_retries=True, normal_user_memory_untouched=True,
          transport_attempts='Built-in provider retry settings cannot be overridden. All native HTTP attempts captured, failures/unknown usage retained; no repeated model assignment.',
          preparation_failure='001 reserved-provider config rejected before thread/turn or upstream submission; preserved separately',
          source_material='Public setup.py/tox.ini/CONTRIBUTING.md only; no issue, patch, test patch or grades'))


def client(directory):
    directory.mkdir()
    runtime = str(Path(shutil.which('codex')).resolve())
    settings = {
        'model_provider': 'openai',
        'openai_base_url': 'http://127.0.0.1:8381/backend-api/codex',
        'features.enable_request_compression': False,
        'features.skip_host_skill_discovery': True,
        'features.memories': True,
        'project_doc_max_bytes': 0,
        'memories.version': 'v1',
        'memories.dual_write': False,
        'memories.generate_memories': True,
        'memories.use_memories': True,
        'memories.extract_model': 'gpt-6-luna',
        'memories.consolidation_model': 'gpt-6-luna',
        'memories.min_rollout_idle_hours': 1,
        'memories.max_rollouts_per_startup': 1,
        'memories.disable_on_external_context': False,
        'model_reasoning_effort': 'low',
        'web_search': 'disabled',
        'default_permissions': 'ttgl_native_memory_probe',
        'permissions.ttgl_native_memory_probe.filesystem': {
            ':root': 'deny', ':minimal': 'read', str(ROOT / 'work'): 'read',
            str(ROOT / 'home/memories'): 'read', runtime: 'read'},
        'permissions.ttgl_native_memory_probe.network.enabled': False,
    }
    # Native consolidation needs its own normal file tools. The parent has no
    # write scope, credentials, network, host Docker socket or grader access.
    for feature in ('multi_agent', 'plugins', 'apps', 'browser_use', 'computer_use',
                    'image_generation', 'workspace_dependencies', 'view_image', 'hooks'):
        settings['features.' + feature] = False
    cmd = ['codex', 'app-server', '--listen', 'stdio://']
    for key, value in settings.items():
        encoded = ('{' + ','.join(json.dumps(k) + '=' + json.dumps(v)
                                   for k, v in value.items()) + '}'
                   if isinstance(value, dict) else json.dumps(value))
        cmd += ['-c', key + '=' + encoded]
    write(directory / 'intent.json', dict(command=cmd, at=datetime.now(timezone.utc).isoformat(),
                                         no_retry=True, child_home_isolated=True))
    env = os.environ.copy()
    env['CODEX_HOME'] = str(ROOT / 'home')
    c = Client.__new__(Client)
    c.err = (directory / 'stderr.log').open('x')
    c.p = subprocess.Popen(cmd, env=env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                           stderr=c.err, start_new_session=True)
    c.selector = selectors.DefaultSelector()
    c.selector.register(c.p.stdout, selectors.EVENT_READ)
    c.buffer, c.ident, c.calls = b'', 0, []
    c.journal = (directory / 'rpc.jsonl').open('x')
    try:
        c.request('initialize', dict(clientInfo=dict(name='ttgl_memory_probe', version='1'),
                                    capabilities=dict(experimentalApi=True)))
        c.p.stdin.write(b'{"method":"initialized","params":{}}\n')
        c.p.stdin.flush()
        return c
    except BaseException:
        c.close()
        raise


def start_thread(c, directory):
    result = c.request('thread/start', dict(cwd=str(ROOT / 'work'), model='gpt-6-luna',
                       modelProvider='openai', approvalPolicy='never', ephemeral=False))
    thread = result['thread']
    write(directory / 'thread.json', thread)
    return thread['id']


def seed():
    directory = ROOT / 'seed'
    c = client(directory)
    try:
        sid = start_thread(c, directory)
        write(directory / 'turn-intent.json', dict(at=datetime.now(timezone.utc).isoformat(), no_retry=True))
        response = c.request('turn/start', dict(threadId=sid,
                    input=[dict(type='text', text=(ROOT / 'seed.txt').read_text(), text_elements=[])]))
        write(directory / 'turn-accepted.json', response)
        complete = wait_turn(c, 'native_memory_seed')
        write(directory / 'complete.json', dict(at=datetime.now(timezone.utc).isoformat(),
              session_id=sid, turn=complete, earliest_probe_utc=(datetime.now(timezone.utc)
              + timedelta(hours=1, minutes=1)).isoformat(), coding_quality_result=False))
        print('Native memory seed completed; idle eligibility must elapse naturally.', flush=True)
    except BaseException as error:
        write(directory / 'stopped.json', dict(error=str(error), no_retry=True,
                                              upstream_state='inspect receipts; never assume zero'))
        raise
    finally:
        c.close()


def probe():
    seed_result = json.loads((ROOT / 'seed/complete.json').read_text())
    if datetime.now(timezone.utc) < datetime.fromisoformat(seed_result['earliest_probe_utc']):
        raise ValueError('Real idle gate not reached; do not edit timestamps or launch early')
    directory = ROOT / 'generation-probe'
    c = client(directory)
    try:
        sid = start_thread(c, directory)
        # Thread creation triggers the native pipeline. Do not send an ordinary
        # user turn until generation is independently inspected and costed.
        deadline = time.monotonic() + 600
        target = ROOT / 'home/memories/memory_summary.md'
        while time.monotonic() < deadline:
            if target.exists() and target.stat().st_size:
                # Do not kill consolidation merely because its file appeared.
                # Inspect native job lifecycle read-only; never alter eligibility,
                # leases, timestamps or native retry policy.
                db_path = ROOT / 'home/memories_1.sqlite'
                with sqlite3.connect('file:' + str(db_path) + '?mode=ro', uri=True) as db:
                    jobs = db.execute('SELECT kind,status,started_at,finished_at,last_error FROM jobs').fetchall()
                    sources = db.execute('SELECT thread_id,source_updated_at,generated_at FROM stage1_outputs').fetchall()
                if not any(j[1] == 'running' for j in jobs):
                    write(directory / 'complete.json', dict(session_id=sid,
                          native_summary_generated=True, at=datetime.now(timezone.utc).isoformat(),
                          native_jobs=jobs, native_sources=sources,
                          injection_and_background_accounting_still_pending=True))
                    print('Native summary and completed jobs observed; inspect provenance and metering before followup.')
                    return
            if c.p.poll() is not None:
                raise RuntimeError('Native server exited; no retry')
            if c.selector.select(1):
                raw = os.read(c.p.stdout.fileno(), 65536)
                c.buffer += raw
                while b'\n' in c.buffer:
                    line, c.buffer = c.buffer.split(b'\n', 1)
                    if line.strip():
                        c.record(dict(direction='notification', message=json.loads(line)))
        raise TimeoutError('Native summary not observed within bounded probe; preserve all calls')
    except BaseException as error:
        write(directory / 'stopped.json', dict(error=str(error), no_retry=True))
        raise
    finally:
        c.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'seed', 'probe'])
    globals()[parser.parse_args().action]()
