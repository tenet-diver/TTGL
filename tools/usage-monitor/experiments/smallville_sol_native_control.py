"""Eight-task maintenance-model control; same frozen common native interface."""
from datetime import datetime, timedelta, timezone
import json
import os
from pathlib import Path
import subprocess
import tempfile

from luna_memory_te_native import GLOBAL, HERE, REVIEW, COMMON, command, controls, write, sha
from continue_te_native import archive_and_grade
from memory_native_calls import MemoryNativeCalls
from smallville_compat_v4 import CompatibleMemoryV4
from smallville_local_embeddings import LocalEmbeddings
from longmemeval_codex_trial import run_process
from native_jsonl import validate_native_completion

ROOT = GLOBAL / 'smallville-sol-native-control-001'
PROTOCOL = HERE.parent / 'studies/luna-memory-smallville-sol-control-protocol-001.json'


def main():
    os.umask(0o077)
    prior = GLOBAL / 'luna-memory-tokeneconomizer-native-001'
    if not (prior / 'continuation-complete.json').exists():
        raise ValueError('Finish preceding native block before control')
    ROOT.mkdir()
    (ROOT / 'protocol.json').write_bytes(PROTOCOL.read_bytes())
    p = json.loads(PROTOCOL.read_text())
    tasks = json.loads((REVIEW / 'humaneval-selected-private.json').read_text())
    if p['tasks'] != [x['task_id'] for x in tasks]:
        raise ValueError('Changed selection')
    ar = ROOT / 'smallville_sol'
    ar.mkdir()
    work = Path(tempfile.mkdtemp(prefix='ttgl-native-memory-smallville-sol-'))
    subprocess.run(['git', 'init', '-q', str(work)], check=True)
    controls(work, ar)
    st = dict(arm='smallville_sol', root=ar, work=work)
    calls = MemoryNativeCalls(ar / 'maintenance', 'gpt-6.1-sol', cap=512)
    st['memory'] = CompatibleMemoryV4(ar / 'memory',
        LocalEmbeddings(GLOBAL, ar / 'embedding-inferences.jsonl'), calls,
        dict(name='TTGL agent', currently='Solving sequential Python coding tasks.'))
    source = json.loads((prior / 'continuation-manifest.json').read_text())['sources']
    source.update({str(Path(__file__)): sha(Path(__file__)), str(PROTOCOL): sha(PROTOCOL)})
    write(ROOT / 'manifest.json', dict(sources=source, work=str(work), model_calls=0,
        task_controls_sha256=sha(GLOBAL / 'luna-memory-tokeneconomizer-development-002/controls.json')))
    write(ROOT / 'started.json', dict(pid=os.getpid(), at=datetime.now(timezone.utc).isoformat(), no_retry=True))
    progress = []
    try:
        for index, task in enumerate(tasks):
            for f, h in source.items():
                if sha(Path(f)) != h:
                    raise ValueError('Frozen maintenance-control source changed')
            cell = ar / f'task-{index:02d}'
            cell.mkdir()
            (work / 'task.py').write_text(task['prompt'] + '    raise NotImplementedError\n')
            prefix = ''
            if index:
                hits = st['memory'].retrieve(task['prompt'], datetime(2026, 1, 1) + timedelta(days=index), 8)
                prefix = '\nFallible retrieved prior task memories:\n' + json.dumps([
                    dict(id=n.node_id, text=n.embedding_key, evidence=n.filling) for n in hits])
            solver = cell / 'solver'
            solver.mkdir()
            prompt = COMMON + '\n\nCurrent task:\n' + task['prompt'] + '\n' + prefix
            (solver / 'prompt.txt').write_text(prompt)
            cmd, _ = command(work, solver)
            run_process(cmd, prompt, solver, 600)
            sid = validate_native_completion(solver)
            row = archive_and_grade(st, cell, task, index, sid)
            row['operational_segment'] = 'later-period-sol-maintenance-control'
            progress.append(row)
            (ROOT / 'progress.json').write_text(json.dumps(progress, indent=2))
            print('Sol maintenance control', task['task_id'], row['passed'], flush=True)
        write(ROOT / 'complete.json', dict(assignments=8, maintenance_calls=len(calls.registry),
            quality_passes=sum(x['passed'] for x in progress), usage_audit_pending=True))
    except BaseException as error:
        write(ROOT / 'stopped.json', dict(error=type(error).__name__, message=str(error), completed=len(progress), no_retry=True))
        raise


if __name__ == '__main__':
    main()
