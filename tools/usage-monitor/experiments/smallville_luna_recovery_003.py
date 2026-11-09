"""Exact replay of30 completed outputs; new calls only for changed triple prompts.

The refused31st output remains failed evidence and cannot be replayed as success.
"""
from datetime import datetime, timedelta
import hashlib
import json
import os
from pathlib import Path
from memory_native_calls import MemoryNativeCalls
from smallville_native_mechanism import EVENTS, GLOBAL, HERE, sha, write
from smallville_compat_v4 import CompatibleMemoryV4
from smallville_local_embeddings import LocalEmbeddings

ROOT = GLOBAL / 'smallville-luna-mechanism-003'
PROTOCOL = HERE.parent / 'studies/smallville-luna-mechanism-protocol-003.json'


def main():
    os.umask(0o077)
    ROOT.mkdir()
    (ROOT / 'protocol.json').write_bytes(PROTOCOL.read_bytes())
    paths = [Path(__file__), PROTOCOL, HERE / 'smallville_compat_v4.py',
             HERE / 'memory_native_calls.py', HERE / 'smallville_memory.py']
    write(ROOT / 'manifest.json', dict(sources={str(p): sha(p) for p in paths}, model_calls=0))
    write(ROOT / 'started.json', dict(pid=os.getpid(), no_retry=True))
    prior = sorted((GLOBAL / 'smallville-luna-mechanism-002/maintenance').glob('call-*'))[:30]
    calls = MemoryNativeCalls(ROOT / 'maintenance', 'gpt-6-luna', cap=18)
    replayed = []

    def complete(prompt, role):
        if len(replayed) < len(prior):
            old = prior[len(replayed)]
            if (old / 'prompt.txt').read_text() != prompt or json.loads(
                    (old / 'complete.json').read_text())['role'] != role:
                raise ValueError('Replay mismatch; no inference fallback')
            answer = (old / 'answer.txt').read_text()
            replayed.append(dict(source=str(old), role=role,
                prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(), answer_sha256=sha(old / 'answer.txt')))
            (ROOT / 'replay-receipts.json').write_text(json.dumps(replayed, indent=2))
            return answer
        return calls(prompt, role)

    try:
        embed = LocalEmbeddings(GLOBAL, ROOT / 'embedding-inferences.jsonl')
        m = CompatibleMemoryV4(ROOT / 'memory', embed, complete, dict(
            name='TTGL agent', currently='Diagnosing an assigned journal import problem.'))
        when = datetime(2026, 1, 1, 9)
        for i, event in enumerate(EVENTS):
            m.observe(event, 'TTGL agent', 'observed', 'journal importer', when + timedelta(minutes=i))
        m.retrieve('What repaired the CRLF parse failure?', when + timedelta(minutes=7), 3)
        remaining = m.scratch.importance_trigger_curr
        m.audit('diagnostic_forced_reflection', original_remaining=remaining, forced_remaining=0)
        m.scratch.importance_trigger_curr = 0
        thoughts = m.reflect_if_due(when + timedelta(minutes=8))
        hits = m.retrieve('What is the exact recorded fix identifier for the CRLF parse failure?',
                          when + timedelta(minutes=9), 3)
        write(ROOT / 'retrieval.json', [dict(id=n.node_id, text=n.embedding_key, evidence=n.filling) for n in hits])
        reader = MemoryNativeCalls(ROOT / 'reader', 'gpt-6.1-sol', cap=1)
        answer = reader('Use only these fallible memory records to recall the exact recorded fix identifier. '
            'Reply with only that identifier; no tools or prose.\n' + json.dumps([n.embedding_key for n in hits]),
            'diagnostic_reader').strip()
        write(ROOT / 'complete.json', dict(passed=len(thoughts) == 15 and all(n.filling for n in thoughts)
            and answer == 'normalize_newlines_before_parse', replayed=len(replayed),
            new_maintenance_calls=len(calls.registry), new_reader_calls=1, thoughts=len(thoughts),
            natural_remaining=remaining, reflection_trigger_forced=True, prompt_adaptation='v4 triple wrapper',
            scope='Synthetic recovery mechanism; all prior costs/failures retained; not benchmark efficacy'))
    except BaseException as error:
        write(ROOT / 'stopped.json', dict(error=type(error).__name__, message=str(error),
              replayed=len(replayed), completed_new_calls=len(calls.registry), no_retry=True))
        raise


if __name__ == '__main__':
    main()
