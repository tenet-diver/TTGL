"""Registered continuation: recover existing evidence, dispatch only unstarted cells.

Original generator, stopped marker, model outputs and progress remain unchanged.
"""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import shlex
import shutil
import sys
import time

import luna_memory_te_native as original
from luna_memory_te_native import ROOT, REVIEW, HERE, GLOBAL, COMMON, write, sha, command, execute
from memory_native_calls import MemoryNativeCalls
from smallville_compat_v4 import CompatibleMemoryV4
from smallville_local_embeddings import LocalEmbeddings
from native_jsonl import records, validate_native_completion
from longmemeval_codex_trial import run_process

PROTOCOL = HERE.parent / 'studies/luna-memory-tokeneconomizer-native-protocol-002.json'


def archive_and_grade(st, cell, task, index, sid, *, late=False):
    work = st['work']
    candidate = (work / 'task.py').read_text()
    (cell / 'candidate.py').write_text(candidate)
    answer = (cell / 'solver/answer.txt').read_text()
    terminal = [r['item'] for r in records(cell / 'solver') if r.get('type') == 'item.completed'
                and r.get('item', {}).get('type') == 'command_execution']
    archive = dict(task=task['task_id'], instruction=task['prompt'], candidate=candidate,
                   answer=answer, visible_commands=terminal)
    destination = work / 'history' / f'task-{index:02d}.json'
    if destination.exists() or (cell / 'sealed.json').exists():
        raise ValueError('Do not replace sealed/archive evidence')
    destination.write_text(json.dumps(archive, indent=2))
    (cell / 'archive.json').write_bytes(destination.read_bytes())
    write(cell / 'sealed.json', dict(candidate_sha256=sha(cell / 'candidate.py'),
        archive_sha256=sha(destination), session_id=sid, late_seal_recovery=late,
        explanation='Post-controller-stop sealing of already completed actor; no re-inference' if late else None))
    grade = execute(candidate, task)
    write(cell / 'grade.json', grade)
    if st.get('memory'):
        when = datetime(2026, 1, 1) + timedelta(days=index)
        for j, item in enumerate([dict(instruction=task['prompt']), *terminal, dict(answer=answer)]):
            text = json.dumps(item).replace('(', r'\u0028').replace(')', r'\u0029')
            t = when + timedelta(minutes=j + 1)
            st['memory'].observe(text, 'TTGL agent', 'observed', task['task_id'], t)
            st['memory'].reflect_if_due(t)
        write(cell / 'memory-update.json', dict(observations=len(st['memory'].memory.seq_event),
            thoughts=len(st['memory'].memory.seq_thought), natural_remaining=st['memory'].scratch.importance_trigger_curr))
    return dict(task=task['task_id'], index=index, arm=st['arm'], session_id=sid,
        passed=grade['passed'], cell=str(cell), source_sha256=sha(cell / 'candidate.py'),
        late_seal_recovery=late, operational_segment='recovered-original' if late else 'async-continuation')


def wait_fold(st, sid):
    deadline = time.monotonic() + 240
    while time.monotonic() < deadline:
        paths = list((st['root'] / 'te-state').glob('repos/*/codex/sessions/' + sid + '.json'))
        if len(paths) == 1 and json.loads(paths[0].read_text()).get('folded'):
            return
        time.sleep(.2)
    raise RuntimeError('Bounded asynchronous fold wait expired; preserve/no retry')


def main():
    os.umask(0o077)
    if not json.loads((ROOT / 'recovery-001/complete.json').read_text())['passed']:
        raise ValueError('Exact zero-model fold recovery required')
    original_manifest = json.loads((ROOT / 'manifest.json').read_text())['sources']
    sources = {**original_manifest, str(Path(__file__)): sha(Path(__file__)), str(PROTOCOL): sha(PROTOCOL)}
    write(ROOT / 'continuation-manifest.json', dict(sources=sources, original_stopped_sha256=sha(ROOT / 'stopped.json'),
        original_progress_sha256=sha(ROOT / 'progress.json'), no_retry=True))
    tasks = json.loads((REVIEW / 'humaneval-selected-private.json').read_text())
    arms = json.loads((ROOT / 'protocol.json').read_text())['arms']
    states = {arm: dict(arm=arm, root=ROOT / arm, work=Path(work))
              for arm, work in json.loads((ROOT / 'workspaces.json').read_text()).items()}
    progress = json.loads((ROOT / 'progress.json').read_text())
    if len(progress) != 6:
        raise ValueError('Unexpected original prefix')
    recovered = states['te_memory_luna']['root'] / 'task-01'
    sid = validate_native_completion(recovered / 'solver')
    progress.append(archive_and_grade(states['te_memory_luna'], recovered, tasks[1], 1, sid, late=True))
    (ROOT / 'continuation-progress.json').write_text(json.dumps(progress, indent=2))
    planned = [(i, arm) for i in range(8) for arm in arms[i % 4:] + arms[:i % 4]]
    if [(x['index'], x['arm']) for x in progress] != planned[:7]:
        raise ValueError('Continuation would alter original order')
    for i, arm in planned[7:]:
        if (ROOT / arm / f'task-{i:02d}').exists():
            raise ValueError('Started/uncertain future assignment exists; no redispatch')
    st = states['smallville_luna']
    calls = MemoryNativeCalls(st['root'] / 'maintenance', 'gpt-6-luna', cap=512)
    calls.registry = json.loads((st['root'] / 'maintenance/registry.json').read_text())
    for c in calls.registry:
        validate_native_completion(st['root'] / 'maintenance' / c['cell'], no_tools=True)
    embed = LocalEmbeddings(GLOBAL, st['root'] / 'embedding-inferences.jsonl')
    st['memory'] = CompatibleMemoryV4(st['root'] / 'memory', embed, calls,
        dict(name='TTGL agent', currently='Solving sequential Python coding tasks.'), restore_last_access=True)
    definitions = json.loads((REVIEW / 'source/plugin/hooks/codex-hooks.json').read_text())['hooks']
    for event, groups in definitions.items():
        for group in groups:
            for hook in group['hooks']:
                hook['command'] = shlex.join([sys.executable, str(REVIEW / 'source/plugin/scripts/te_bootstrap.py'), 'hook', '--host', 'codex'])
                hook.pop('commandWindows', None)
                if event == 'SessionEnd':
                    hook['timeout'] = 240
    write(ROOT / 'continuation-started.json', dict(pid=os.getpid(), at=datetime.now(timezone.utc).isoformat(),
        recovered_existing_assignments=1, maximum_new_actor_processes=25, no_retry=True))
    try:
        for index, arm in planned[7:]:
            for p, digest in sources.items():
                if sha(Path(p)) != digest:
                    raise ValueError('Frozen continuation/original source changed')
            task, st = tasks[index], states[arm]
            cell = st['root'] / f'task-{index:02d}'
            cell.mkdir()
            work = st['work']
            (work / 'task.py').write_text(task['prompt'] + '    raise NotImplementedError\n')
            prefix = ''
            if arm == 'smallville_luna' and index:
                hits = st['memory'].retrieve(task['prompt'], datetime(2026, 1, 1) + timedelta(days=index), 8)
                prefix = '\nFallible retrieved prior task memories:\n' + json.dumps([
                    dict(id=n.node_id, text=n.embedding_key, evidence=n.filling) for n in hits])
            solver = cell / 'solver'
            solver.mkdir()
            prompt = COMMON + '\n\nCurrent task:\n' + task['prompt'] + '\n' + prefix
            (solver / 'prompt.txt').write_text(prompt)
            cmd, _ = command(work, solver, hooks=definitions if arm.startswith('te_') else None)
            cmd[0] = str(Path(shutil.which('codex')).resolve())
            env = dict(TOKENECONOMIZER_HOME=str(st['root'] / 'te-state'),
                TE_CORE_PATH=str(REVIEW / 'source'), TE_PLUGIN_ROOT=str(REVIEW / 'source/plugin'),
                TE_MICROSKILLS='on' if arm == 'te_memory_luna' else 'off', TE_PAID_MODEL='gpt-6-luna',
                TE_HISTORY_IMPORT='off', TE_FOLD_SYNC='0',
                TTGL_TE_SIDECALL_RECORDS=str(st['root'] / 'maintenance'), TTGL_TE_NATIVE_CODEX=cmd[0],
                PATH=str(ROOT / 'bin') + os.pathsep + os.environ['PATH'],
                PYTHONPATH=str(HERE) + os.pathsep + str(REVIEW / 'source'))
            prior = {k: os.environ.get(k) for k in env}
            os.environ.update(env)
            try:
                run_process(cmd, prompt, solver, 600)
                sid = validate_native_completion(solver)
                if arm.startswith('te_'):
                    wait_fold(st, sid)
            finally:
                for k, v in prior.items():
                    if v is None:
                        os.environ.pop(k, None)
                    else:
                        os.environ[k] = v
            for attempt in (st['root'] / 'maintenance').glob('call-*'):
                if not (attempt / 'complete.json').exists() and not (attempt / 'recovery-verified.json').exists():
                    raise RuntimeError('Uncertain maintenance; no retry')
            row = archive_and_grade(st, cell, task, index, sid)
            progress.append(row)
            (ROOT / 'continuation-progress.json').write_text(json.dumps(progress, indent=2))
            print('continued native', task['task_id'], arm, row['passed'], flush=True)
        write(ROOT / 'continuation-complete.json', dict(assignments=32, new_actor_processes=25,
            original_stopped_preserved=True, recovered_reply_replays=1, repeated_model_calls=0,
            original_operational_segment_assignments=7, async_segment_assignments=25, usage_audit_pending=True))
    except BaseException as error:
        write(ROOT / 'continuation-stopped.json', dict(error=type(error).__name__, message=str(error),
            completed_assignments=len(progress), no_retry=True))
        raise


if __name__ == '__main__':
    main()
