#!/usr/bin/env python3
"""Register, run and reconcile a bounded native source-retrieval comparison.

Uses existing Codex, ripgrep and the TTGL native reader. No package installation,
proxy configuration, custom compressor, automatic retry or scheduled inference.
"""
import argparse
import collections
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

from workspace import Store

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
DEFAULT_PROTOCOL = HERE.parent / 'studies/retrieval-guidance-protocol-001.json'
KEYS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    path.write_text(json.dumps(value, indent=2) + '\n')


def fingerprints(root):
    return {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*')) if p.is_file()}


def prepare(directory, protocol_path):
    os.umask(0o077)
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    protocol = json.loads(protocol_path.read_text())
    write(directory / 'protocol.json', protocol)
    source = directory / 'source'
    source.mkdir()
    paths = subprocess.check_output(['git', 'ls-files', '-z', 'tools/usage-monitor'], cwd=REPO).decode().split('\0')
    for name in paths:
        path = Path(name)
        # Public source only; exclude registered questions/answers and experiment runners.
        if not name or 'studies' in path.parts or path.suffix not in ('.py', '.js', '.json', '.md', '.toml', '.html', '.css'):
            continue
        if path.name in ('retrieval_trial.py', 'live_harness_trial.py', 'progress_trial.py'):
            continue
        target = source / path.relative_to('tools/usage-monitor')
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes((REPO / path).read_bytes())
    write(directory / 'manifest.json', dict(created=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=digest(directory / 'protocol.json'), runner_sha256=digest(Path(__file__)),
        source=fingerprints(source), codex_version=subprocess.check_output(['codex', '--version'], text=True).strip(),
        rg_version=subprocess.check_output(['rg', '--version'], text=True).splitlines()[0]))
    print('Registered', directory, flush=True)


def run(directory):
    if any(directory.glob('*--*')):
        raise ValueError('An attempt already exists; inspect it, never automatically repeat')
    manifest = json.loads((directory / 'manifest.json').read_text())
    if digest(directory / 'protocol.json') != manifest['protocol_sha256'] or digest(Path(__file__)) != manifest['runner_sha256']:
        raise ValueError('Registered protocol or runner changed')
    protocol = json.loads((directory / 'protocol.json').read_text())
    for case in protocol['cases']:
        for condition in case['order']:
            if fingerprints(directory / 'source') != manifest['source']:
                raise ValueError('Frozen source changed')
            cell = directory / (case['id'] + '--' + condition)
            cell.mkdir(mode=0o700)
            prompt = '\n\n'.join((protocol['common'], protocol['conditions'][condition], case['question']))
            (cell / 'prompt.txt').write_text(prompt)
            # Answer/protocol directories are outside the source workspace. Read-only
            # sandbox is an agent constraint, not a claim of hidden-file isolation.
            command = ['codex', 'exec', '-p', 'ttgl-observability', '-c', 'model_provider="openai"',
                '--skip-git-repo-check', '--json', '-C', str(directory / 'source'), '-m', protocol['model'],
                '-s', 'read-only', '--output-last-message', str(cell / 'answer.txt'), '-']
            write(cell / 'command.json', command)
            started = time.monotonic()
            with (cell / 'agent.jsonl').open('w') as output:
                try:
                    result = subprocess.run(command, input=prompt, text=True, stdout=output, stderr=subprocess.STDOUT,
                                            timeout=protocol['timeout_seconds_per_run'])
                    completion = dict(exit_code=result.returncode)
                except subprocess.TimeoutExpired:
                    completion = dict(timeout=True)
            completion['elapsed_seconds'] = time.monotonic() - started
            write(cell / 'completion.json', completion)
            print(cell.name, json.dumps(completion), flush=True)
            if completion.get('exit_code') != 0 or completion.get('timeout'):
                raise RuntimeError('Failed/uncertain process; preserve evidence and stop without retry')
            records = records_at(cell)
            if len([r for r in records if r.get('type') == 'turn.completed']) != 1:
                raise RuntimeError('Missing or ambiguous completion; preserve and stop')
            answer = (cell / 'answer.txt').read_text().strip()
            if answer.startswith('```'):
                answer = '\n'.join(answer.splitlines()[1:-1])
            try:
                answer = json.loads(answer)
            except ValueError:
                answer = None
            quality = dict(answer=answer, exact_fields=answer == case['expected'],
                           source_unchanged=fingerprints(directory / 'source') == manifest['source'])
            quality['passed'] = quality['exact_fields'] and quality['source_unchanged']
            write(cell / 'grade.json', quality)
            if not quality['source_unchanged']:
                raise RuntimeError('Source changed; stop')
    write(directory / 'complete.json', dict(cells=6, completed=datetime.now(timezone.utc).isoformat()))


def records_at(cell):
    return [json.loads(line) for line in (cell / 'agent.jsonl').read_text().splitlines() if line.startswith('{')]


def measure(directory):
    if not (directory / 'complete.json').exists():
        raise ValueError('Incomplete trial; no economic result')
    protocol = json.loads((directory / 'protocol.json').read_text())
    manifest = json.loads((directory / 'manifest.json').read_text())
    if digest(directory / 'protocol.json') != manifest['protocol_sha256'] or fingerprints(directory / 'source') != manifest['source']:
        raise ValueError('Frozen inputs changed')
    store = Store(REPO / 'work/security/workspace', Path.home() / '.codex', 'http://localhost:3000')
    store.scan()
    cells = []
    for case in protocol['cases']:
        for condition in case['order']:
            cell = directory / (case['id'] + '--' + condition)
            records = records_at(cell)
            sessions = [r['thread_id'] for r in records if r.get('type') == 'thread.started']
            if len(sessions) != 1:
                raise ValueError('Ambiguous session identity')
            session = sessions[0]
            report = store.report(session=session, event_limit=None)
            generations = [e for e in report['events'] if e['kind'] == 'generation' and e['usage']]
            usage = {k: sum(e['usage'].get(k, 0) for e in generations) for k in KEYS}
            cli = next(r['usage'] for r in records if r.get('type') == 'turn.completed')
            if not generations or not usage['total_tokens'] or any(usage[k] != cli[k] for k in KEYS[:3]):
                raise ValueError('Native counters missing or do not reconcile with CLI')
            tools = [e for e in report['events'] if e['kind'] == 'tool']
            cells.append(dict(case=case['id'], condition=condition, session_id=session, usage=usage,
                cli_usage=cli, native_reconciled=True, native_response_ids=[e['id'] for e in generations],
                tool_evidence_ids=[e['id'] for e in tools], tool_calls=len(tools),
                retained_tool_bytes=sum(e['bytes'] or 0 for e in tools),
                elapsed_seconds=json.loads((cell / 'completion.json').read_text())['elapsed_seconds'],
                quality=json.loads((cell / 'grade.json').read_text())))
    totals = {condition: sum(c['usage']['total_tokens'] for c in cells if c['condition'] == condition) for condition in protocol['conditions']}
    pair_wins = sum(next(c['usage']['total_tokens'] for c in cells if c['case'] == case['id'] and c['condition'] == 'scoped') <
                    next(c['usage']['total_tokens'] for c in cells if c['case'] == case['id'] and c['condition'] == 'baseline') for case in protocol['cases'])
    reduction = 1 - totals['scoped'] / totals['baseline']
    quality = all(c['quality']['passed'] for c in cells)
    result = dict(protocol=protocol['id'], scope=protocol['scope'], cells=cells, totals=totals,
        token_reduction_fraction=reduction, pair_wins=pair_wins, quality_passed=quality,
        acceptance_passed=quality and reduction >= .05 and pair_wins >= 2,
        cash_cost=None, model_latency=None, net_saving=None, implementation_overhead=None,
        limitations=protocol['overhead'], artifacts=fingerprints(directory / 'source'))
    write(directory / 'results.json', result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('cells', 'artifacts')}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run', 'measure'])
    parser.add_argument('directory', type=Path)
    parser.add_argument('--protocol', type=Path, default=DEFAULT_PROTOCOL)
    args = parser.parse_args()
    directory = args.directory.resolve()
    if args.action == 'prepare':
        prepare(directory, args.protocol)
    elif args.action == 'run':
        run(directory)
    else:
        measure(directory)
