"""Zero-inference recovery of a completed reply; no model fallback or old rewrite."""
import json
import os
from pathlib import Path
import shutil
import sys

from luna_memory_te_native import ROOT, REVIEW, HERE, write, sha
from native_jsonl import records, validate_native_completion


def main():
    recovery = ROOT / 'recovery-001'
    recovery.mkdir()
    protocol = HERE.parent / 'studies/luna-memory-tokeneconomizer-native-protocol-002.json'
    (recovery / 'protocol.json').write_bytes(protocol.read_bytes())
    ar = ROOT / 'te_memory_luna'
    candidates = [p for p in (ar / 'maintenance').glob('call-*') if not (p / 'complete.json').exists()]
    if len(candidates) != 1:
        raise ValueError('Unexpected uncertain-call inventory')
    cell = candidates[0]
    sid = validate_native_completion(cell, no_tools=True)
    cli = next(r['usage'] for r in records(cell) if r.get('type') == 'turn.completed')
    sys.path.insert(0, str(HERE.parent / 'observability'))
    from workspace import Store
    from capture_objects import read_capture
    store = Store(HERE.parents[2] / 'work/security/workspace', Path.home() / '.codex', 'http://localhost:3000')
    store.scan()
    with store.connection() as db:
        rows = [dict(r) for r in db.execute("SELECT id,usage FROM events WHERE session_id=? AND kind='generation'", (sid,))]
    if len(rows) != 1:
        raise ValueError('Ambiguous response count')
    ident = rows[0]['id'].split(':response:', 1)[1]
    matches = []
    for p in Path('/tmp/ttgl-luna-tokeneconomizer-captures-002').glob('*.json'):
        metadata = json.loads(p.read_text())
        if ident in metadata.get('response_ids', []):
            matches.append(read_capture(p))
    if len(matches) != 1:
        raise ValueError('Missing or duplicate capture')
    end = next(e['response'] for e in matches[0]['response']['sse_events']
               if e.get('type') == 'response.completed' and e['response']['id'] == ident)
    native = json.loads(rows[0]['usage'])
    expected = dict(input_tokens=end['usage']['input_tokens'],
        cached_input_tokens=end['usage'].get('input_tokens_details', {}).get('cached_tokens', 0),
        output_tokens=end['usage']['output_tokens'])
    if end['model'] != 'gpt-6-luna' or any(cli[k] != v or native[k] != v for k, v in expected.items()):
        raise ValueError('Usage/model mismatch')
    state = ar / 'te-state'
    manual = next(state.glob('repos/*/codex/mechanisms/manual_state/*.json'))
    if json.loads(manual.read_text())['now'] != 1:
        raise ValueError('Unexpected pre-recovery memory position')
    shutil.copytree(state, recovery / 'before-te-state')
    evidence = dict(passed=True, session_id=sid, response_id=ident,
        native_cli_capture_reconciled=True, usage=expected,
        prompt_sha256=sha(cell / 'prompt.txt'), answer_sha256=sha(cell / 'answer.txt'),
        process_exit_status=None, process_wall_seconds=None,
        explanation='Completed model response independently reconciles. Original wrapper process exit/lifetime receipt remains missing; no inference repeat authorized.')
    write(cell / 'recovery-verified.json', evidence)
    sys.path.insert(0, str(REVIEW / 'source'))
    from tokeneconomizer.plugin import sidecall, cli as upstream_cli
    original = sidecall.runner_for
    replayed = []

    def runner(host, config):
        if host != 'codex' or config.paid_model != 'gpt-6-luna':
            raise ValueError('Replay model/host mismatch')

        def replay(prompt, model):
            if replayed or prompt != (cell / 'prompt.txt').read_text():
                raise ValueError('Exact prompt replay refused; NO model fallback')
            replayed.append(dict(prompt_sha256=sha(cell / 'prompt.txt'), source=str(cell)))
            # Exact upstream accounting conversion; authoritative usage remains native.
            from tokeneconomizer.plugin import accounting
            eff, _ = accounting.effective(dict(input_tokens=cli['input_tokens'] - cli['cached_input_tokens'],
                cache_read_input_tokens=cli['cached_input_tokens'], cache_creation_input_tokens=0,
                output_tokens=cli['output_tokens'], model='gpt-6-luna'))
            return (cell / 'answer.txt').read_text(), eff
        return replay

    env = dict(TOKENECONOMIZER_HOME=str(state), TE_MICROSKILLS='on', TE_PAID_MODEL='gpt-6-luna',
               TE_FOLD_SYNC='1', TE_HISTORY_IMPORT='off')
    prior = {k: os.environ.get(k) for k in env}
    os.environ.update(env)
    sidecall.runner_for = runner
    try:
        parent_sid = validate_native_completion(ar / 'task-01/solver')
        work = json.loads((ROOT / 'workspaces.json').read_text())['te_memory_luna']
        status = upstream_cli.main(['fold', '--session', parent_sid, '--host', 'codex', '--cwd', work])
        if status not in (None, 0) or len(replayed) != 1 or json.loads(manual.read_text())['now'] != 2:
            raise ValueError('Replay fold did not advance exactly once')
        write(recovery / 'complete.json', dict(passed=True, replayed=replayed, new_model_calls=0,
            old_missing_receipt_preserved=True, parent_session_id=parent_sid, response_id=ident))
    finally:
        sidecall.runner_for = original
        for k, v in prior.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


if __name__ == '__main__':
    main()
