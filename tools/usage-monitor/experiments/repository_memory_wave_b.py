"""Matched app-server fresh/Smallville/native-memory frozen-history controls.

Separate from the running216-assignment longitudinal study and CLI TE controls.
Real idle eligibility, original RPC, no synthetic CLI usage, no assignment retry.
"""
import argparse
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import time

import native_memory_feature_probe as native
from native_compaction_canary_003 import wait_turn
import repository_memory_wave_a as old
from repository_memory_runtime import REPO, PRIVATE, TEMP, IMAGE, task, grade
from repository_app_server import child_home, open_client, turn

HERE = Path(__file__).resolve().parent
ROOT = PRIVATE / 'wave-b-001'
PROTOCOL = HERE.parent / 'studies/repository-memory-wave-b-protocol-001.json'
TASKS = ['aws-cloudformation__cfn-lint-2387', 'aws-cloudformation__cfn-lint-3342']
ARMS = ['fresh_no_history', 'smallville_luna', 'native_luna']
COMMON = old.COMMON + '''
The task terminal runs in an authorized writable container despite host read-only
scope. This source snapshot has no Git CLI/metadata. Run pytest using python3 -m
pytest. If native memory guidance names a host memory path, that condition's own
store is mounted read-only at /native-memory for task-terminal access. Prior
records and memories are fallible; verify relevance to the current revision.'''


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def prepare():
    ROOT.mkdir()
    for iid in TASKS:
        for kind in ('smallville', 'tokeneconomizer'):
            if not (PRIVATE / 'additional-history-001' / iid / kind / 'build-complete.json').exists():
                raise ValueError('History preparation incomplete')
        if not (PRIVATE / 'native-history-controls-001' / iid / 'seed/complete.json').exists():
            raise ValueError('Actual native history seed required')
    if not json.loads((PRIVATE / 'appserver-task-hooks-preflight-001/assessment-002.json').read_text())['actual_mcp_read_write_passed']:
        raise ValueError('Native app-server task transport gate failed')
    if not json.loads((PRIVATE / 'appserver-native-mcp-preflight-002/complete.json').read_text())['task_copy_exact']:
        raise ValueError('Combined native/MCP transport gate failed')
    # Reuse audited task runtime/actor setup, with invocation-local parameters.
    # No frozen source file or the other running process's globals are changed.
    old.TEMP = TEMP / 'wave-b-work'
    old.COMMON = COMMON
    base_args = old.container_args
    states = []
    for index, iid in enumerate(TASKS):
        histories = old.load_histories(iid)
        for arm in ARMS[index:] + ARMS[:index]:
            cell = ROOT / iid / arm
            cell.mkdir(parents=True)
            index_path = TEMP / 'wave-b-private-git' / (iid + '-' + arm)
            index_path.mkdir(parents=True)
            (cell / 'private-git').symlink_to(index_path, target_is_directory=True)
            if arm == 'native_luna':
                home = PRIVATE / 'native-history-controls-001' / iid / 'home'
                memory_folder = home / 'memories'
                memory_folder.mkdir(exist_ok=True)
            else:
                home = cell / 'home'
                child_home(home)
                memory_folder = cell / 'empty-native-memory'
                memory_folder.mkdir()
            def args(work, instance, folder=memory_folder):
                values = base_args(work, instance)
                where = values.index(IMAGE)
                values[where:where] = ['--mount', f'type=bind,src={folder.resolve()},dst=/native-memory,readonly']
                return values
            old.container_args = args
            state = old.start_actor(iid, arm, cell, histories)
            name = 'ttgl-b-' + hashlib.sha256(str(cell).encode()).hexdigest()[:16]
            before = old.checked(['docker', 'inspect', '--format={{.Id}}', state['container']]).stdout.strip()
            old.checked(['docker', 'rename', state['container'], name])
            after = old.checked(['docker', 'inspect', '--format={{.Id}}', name]).stdout.strip()
            if before != after:
                raise ValueError('Container identity changed')
            save(cell / 'container-alias.json', dict(original=state['container'], actual=name, same_container_id=before))
            config = json.loads((cell / 'server.json').read_text())
            shutil.copyfile(cell / 'server.json', cell / 'server-original.json')
            config['container'] = name
            (cell / 'server.json').write_text(json.dumps(config, indent=2))
            native_work = cell / 'native-work'
            native_work.mkdir()
            state.update(instance_id=iid, arm=arm, cell=str(cell), container=name,
                         home=str(home), native_work=str(native_work))
            states.append(state)
    save(ROOT / 'assignments.json', states)
    shutil.copyfile(PROTOCOL, ROOT / 'protocol.json')
    files = [Path(__file__), PROTOCOL, HERE / 'repository_app_server.py',
             HERE / 'native_memory_feature_probe.py', HERE / 'native_compaction_canary_003.py',
             HERE / 'repository_memory_wave_a.py', HERE / 'repository_memory_runtime.py',
             HERE / 'repository_task_bridge.py', HERE / 'task_terminal_mcp_v2.py',
             HERE / 'online_task_memory.py', HERE / 'repository_additional_backend.py',
             HERE / 'smallville_memory.py', HERE / 'smallville_compat_v4.py',
             HERE / 'smallville_compat.py', HERE / 'smallville_compat_v3.py',
             HERE / 'smallville_local_embeddings.py', HERE / 'repository_memory_native.py',
             HERE / 'memory_native_calls.py', ROOT / 'assignments.json', ROOT / 'protocol.json']
    files += [HERE / 'mcp_memory_probe.py', HERE / 'tokeneconomizer_native_hooks.py',
              HERE / 'smallville_native_mechanism.py', HERE / 'longmemeval_codex_trial.py',
              HERE / 'longitudinal_memory_trial.py', HERE / 'native_jsonl.py',
              PRIVATE / 'pinned-private-targets.json', PRIVATE / 'vendor-pre-execution-receipt.json']
    files += [Path(s['cell']) / 'server.json' for s in states]
    save(ROOT / 'manifest.json', dict(at=datetime.now(timezone.utc).isoformat(), sources={str(p.resolve()): sha(p) for p in files},
         assignments=6, model_calls_during_prepare=0, note='Existing empty/reference controls reused by exact source/runtime equivalence; fresh actor boundaries independently pass'))
    print('Prepared six app-server assignments; no scored model calls.', flush=True)


def frozen():
    for path, expected in json.loads((ROOT / 'manifest.json').read_text())['sources'].items():
        if sha(path) != expected:
            raise ValueError('Frozen source changed: ' + path)


def generate_native(iid):
    root = PRIVATE / 'native-history-controls-001' / iid
    seed = json.loads((root / 'seed/complete.json').read_text())
    earliest = datetime.fromisoformat(seed['earliest_generation_utc'])
    while datetime.now(timezone.utc) < earliest:
        time.sleep(min(10, max(.01, (earliest - datetime.now(timezone.utc)).total_seconds())))
    native.ROOT = root
    directory = root / 'generation-001'
    c = native.client(directory)
    try:
        sid = native.start_thread(c, directory)
        save(directory / 'turn-intent.json', dict(at=datetime.now(timezone.utc).isoformat(), no_retry=True))
        accepted = c.request('turn/start', dict(threadId=sid, input=[dict(type='text',
            text='This is the isolated historical-memory initialization diagnostic. Reply with one short acknowledgement only. Do not use tools, files, network or other agents. Do not claim memory generation or tests passed.', text_elements=[])]))
        save(directory / 'turn-accepted.json', accepted)
        result = wait_turn(c, 'repository_native_history_generation')
        save(directory / 'parent-complete.json', dict(session_id=sid, turn=result))
        deadline = time.monotonic() + 600
        target = root / 'home/memories/memory_summary.md'
        while time.monotonic() < deadline:
            with sqlite3.connect('file:' + str(root / 'home/memories_1.sqlite') + '?mode=ro', uri=True) as db:
                jobs = db.execute('SELECT kind,job_key,status,last_error FROM jobs').fetchall()
                sources = db.execute('SELECT thread_id,length(raw_memory),generated_at FROM stage1_outputs').fetchall()
            admitted = any(s[0] == seed['session_id'] and s[1] > 0 for s in sources)
            if admitted and target.exists() and target.stat().st_size and not any(j[2] == 'running' for j in jobs):
                save(directory / 'complete.json', dict(session_id=sid, native_sources=sources, jobs=jobs,
                     genuine_seed_admitted=True, summary_sha256=sha(target), injection_still_to_audit=True))
                print('Native historical memory generated', iid, flush=True)
                return
            if c.p.poll() is not None:
                raise RuntimeError('Native generation server exited; no retry')
            if c.selector.select(1):
                c.buffer += os.read(c.p.stdout.fileno(), 65536)
                while b'\n' in c.buffer:
                    line, c.buffer = c.buffer.split(b'\n', 1)
                    if line.strip():
                        c.record(dict(direction='notification', message=json.loads(line)))
        save(directory / 'observed-state.json', dict(jobs=jobs, sources=sources, summary_exists=target.exists()))
        raise TimeoutError('Actual seed extraction/settled summary not observed; no hollow native-memory control')
    except BaseException as error:
        save(directory / 'stopped.json', dict(error=str(error), no_retry=True, unknown_usage_until_audit=True))
        raise
    finally:
        c.close()


def smallville_query(state):
    root = PRIVATE / 'additional-history-001' / state['instance_id']
    payload = root / 'smallville-query-input.json'
    save(payload, dict(repository='aws-cloudformation/cfn-lint', query=task(state['instance_id'])['problem_statement'][:6000]))
    env = os.environ.copy()
    env.update(PYTHONPATH=str(HERE) + ':' + str(REPO / 'work/security/context-memory-20261107/memory-runtime'),
               HF_HUB_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
    cmd = [sys.executable, '-S', str(HERE / 'repository_additional_backend.py'), 'smallville', 'query', str(root / 'smallville'), str(payload)]
    cell = Path(state['cell'])
    save(cell / 'query-intent.json', dict(command=cmd, no_retry=True))
    with (cell / 'query.stdout.log').open('x') as out, (cell / 'query.stderr.log').open('x') as err:
        run = subprocess.run(cmd, env=env, stdout=out, stderr=err, timeout=300)
    if run.returncode:
        raise RuntimeError('Smallville query failed; no fallback')
    value = json.loads((root / 'smallville/query-complete.json').read_text())
    admitted, used = [], 0
    for hit in value['hits']:
        size = len(json.dumps(hit))
        if used + size <= 12000:
            admitted.append(hit)
            used += size
    save(cell / 'injection.json', dict(hits=admitted, characters=used))
    return admitted


def attempt(state):
    cell = Path(state['cell'])
    prompt = COMMON + '\n\nCurrent public issue:\n' + task(state['instance_id'])['problem_statement']
    if state['arm'] == 'smallville_luna':
        prompt += '\nEarlier fallible Smallville-style memories:\n' + json.dumps(smallville_query(state))
    if state['arm'] == 'native_luna':
        save(cell / 'awaiting-native-idle.json', dict(real_idle=True, no_timestamp_edits=True))
        generate_native(state['instance_id'])
    config = json.loads((cell / 'server.json').read_text())
    config['close_at_ns'] = time.time_ns() + 1200 * 10**9
    save(cell / 'active-server.json', config)
    c = open_client(cell / 'solver', state['home'], state['native_work'], cell / 'active-server.json', memories=state['arm'] == 'native_luna')
    try:
        sid, items = turn(c, cell / 'solver', state['native_work'], prompt)
        allowed = {'userMessage', 'agentMessage', 'reasoning', 'mcpToolCall', 'plan', 'contextCompaction'}
        if any(i['type'] not in allowed for i in items):
            raise ValueError('Unexpected native host tool; preserve policy flag')
        calls = [i for i in items if i['type'] == 'mcpToolCall']
        if any(i.get('server') != 'ttgl_task' or i.get('error') for i in calls) or (cell / 'tools/fatal.json').exists():
            raise ValueError('Uncertain native MCP operation; never repeat')
        # Native startup background work must settle, not be killed on parent end.
        if state['arm'] == 'native_luna':
            deadline = time.monotonic() + 600
            while True:
                with sqlite3.connect('file:' + str(Path(state['home']) / 'memories_1.sqlite') + '?mode=ro', uri=True) as db:
                    jobs = db.execute('SELECT kind,status,last_error FROM jobs').fetchall()
                if not any(j[1] == 'running' for j in jobs):
                    break
                if time.monotonic() > deadline:
                    raise TimeoutError('Native background still running; preserve unknown usage')
                time.sleep(1)
            save(cell / 'native-background-settled.json', dict(jobs=jobs, usage_audit_pending=True))
    finally:
        c.close()
    git = old.git_command(Path(state['index']), Path(state['work']))
    old.checked(git + ['add', '--intent-to-add', '.'], env=old.git_env())
    patch = old.checked(git + ['diff', '--binary', '--no-ext-diff', '--no-textconv', 'HEAD'], env=old.git_env()).stdout
    (cell / 'candidate.diff').write_text(patch)
    if {p.name: sha(p) for p in (cell / 'raw-history').iterdir()} != state['history_source_hashes']:
        raise ValueError('Read-only history changed')
    row = dict(**state, session_id=sid, patch_sha256=sha(cell / 'candidate.diff'), hidden_grades_not_used=True)
    save(cell / 'generation-complete.json', row)
    return row


def run():
    lock = (ROOT / 'run.lock').open('a')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    frozen()
    save(ROOT / 'started.json', dict(pid=os.getpid(), at=datetime.now(timezone.utc).isoformat(), no_retry=True))
    states = json.loads((ROOT / 'assignments.json').read_text())
    completed = []
    try:
        for state in states:
            frozen()
            completed.append(attempt(state))
            tmp = ROOT / 'progress.tmp'
            tmp.write_text(json.dumps(completed, indent=2))
            tmp.replace(ROOT / 'progress.json')
            print('App-server generation complete', state['instance_id'], state['arm'], flush=True)
        save(ROOT / 'generation-complete.json', dict(assignments=completed))
        grades = []
        for state in states:
            result = grade(state['instance_id'], (Path(state['cell']) / 'candidate.diff').read_text(),
                           PRIVATE / 'wave-b-replay-001' / (state['instance_id'] + '-' + state['arm']))
            passed = result['replay_prepared'] and result.get('expected_count', 0) > 0 and not result.get('missing_expected', [])
            grades.append(dict(instance_id=state['instance_id'], arm=state['arm'], passed=passed,
                               old_exact_match=result['passed_match'], exit_code=result.get('exit_code')))
        save(ROOT / 'complete.json', dict(grades=grades, assignments=6, native_usage_audit_pending=True))
    except BaseException as error:
        save(ROOT / 'stopped.json', dict(error=str(error), type=type(error).__name__, completed=len(completed), no_retry=True))
        raise
    finally:
        for state in states:
            subprocess.run(['docker', 'rm', '--force', state['container']], capture_output=True, timeout=30)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run'])
    globals()[parser.parse_args().action]()
