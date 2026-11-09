"""Registered Luna maintenance diagnostic, preserving original prompts/ranking."""
from datetime import datetime, timedelta
import json
import os
from pathlib import Path

from memory_native_calls import MemoryNativeCalls
from smallville_native_mechanism import EVENTS, GLOBAL, HERE, sha, write
from smallville_compat_v3 import CompatibleMemoryV3
from smallville_local_embeddings import LocalEmbeddings

ROOT = GLOBAL / 'smallville-luna-mechanism-001'
PROTOCOL = HERE.parent / 'studies/smallville-luna-mechanism-protocol-001.json'


def main():
    os.umask(0o077)
    ROOT.mkdir()
    (ROOT / 'protocol.json').write_bytes(PROTOCOL.read_bytes())
    paths = [Path(__file__), HERE / 'memory_native_calls.py', PROTOCOL,
             HERE / 'smallville_memory.py', HERE / 'smallville_compat.py',
             HERE / 'smallville_compat_v3.py', HERE / 'smallville_local_embeddings.py']
    write(ROOT / 'manifest.json', dict(sources={str(p): sha(p) for p in paths},
                                     events=EVENTS, model_calls=0))
    write(ROOT / 'started.json', dict(pid=os.getpid(), no_retry=True))
    calls = MemoryNativeCalls(ROOT / 'maintenance', 'gpt-6-luna', cap=47)
    try:
        embed = LocalEmbeddings(GLOBAL, ROOT / 'embedding-inferences.jsonl')
        memory = CompatibleMemoryV3(ROOT / 'memory', embed, calls, dict(
            name='TTGL agent', currently='Diagnosing an assigned journal import problem.'))
        when = datetime(2026, 1, 1, 9)
        for index, event in enumerate(EVENTS):
            memory.observe(event, 'TTGL agent', 'observed', 'journal importer',
                           when + timedelta(minutes=index))
            print('observed', index + 1, 'calls', len(calls.registry), flush=True)
        memory.retrieve('What repaired the CRLF parse failure?', when + timedelta(minutes=7), 3)
        remaining = memory.scratch.importance_trigger_curr
        forced = remaining > 0
        if forced:
            memory.audit('diagnostic_forced_reflection', original_remaining=remaining, forced_remaining=0)
            memory.scratch.importance_trigger_curr = 0
        thoughts = memory.reflect_if_due(when + timedelta(minutes=8))
        if len(thoughts) != 15 or any(not n.filling for n in thoughts):
            raise ValueError('Reflection mechanics incomplete')
        hits = memory.retrieve('What is the exact recorded fix identifier for the CRLF parse failure?',
                               when + timedelta(minutes=9), 3)
        write(ROOT / 'retrieval.json', [dict(id=n.node_id, kind=n.type,
              text=n.embedding_key, evidence=n.filling) for n in hits])
        reader = MemoryNativeCalls(ROOT / 'reader', 'gpt-6.1-sol', cap=1)
        answer = reader('Use only these fallible memory records to recall the exact recorded fix identifier. '
                        'Reply with only that identifier; no tools or prose.\n' +
                        json.dumps([n.embedding_key for n in hits]), 'diagnostic_reader').strip()
        reloaded = CompatibleMemoryV3(ROOT / 'memory', embed, calls, dict(name='TTGL agent'))
        passed = len(reloaded.memory.id_to_node) == 21 and answer == 'normalize_newlines_before_parse'
        write(ROOT / 'complete.json', dict(passed=passed, observations=6, thoughts=15,
            natural_remaining=remaining, reflection_trigger_forced=forced,
            maintenance_calls=len(calls.registry), reader_calls=1, usage_audit_pending=True,
            scope='Synthetic mechanism only; no benchmark or economic benefit established'))
    except BaseException as error:
        write(ROOT / 'stopped.json', dict(error=type(error).__name__, message=str(error),
              completed_maintenance_calls=len(calls.registry), no_retry=True))
        raise


if __name__ == '__main__':
    main()
