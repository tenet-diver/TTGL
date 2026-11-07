#!/usr/bin/env python3
"""Run Codex as an on-demand evidence analyst, then publish validated interpretations.

No scheduled inference. The frozen source snapshot and analyst overhead stay private.
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
import uuid

from workspace import Store, bridge
from capture_proxy import sanitized
from setup_local import CONFIG, REPO, DEFAULTS, public_url


def snapshot(store, directory, task=None, project=None, include_reviewed=False):
    os.umask(0o077)
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    store.scan()
    report = store.report(task=task, project=project)
    selected = {event['id'] for event in report['events'] if event['kind'] == 'tool'
                and (include_reviewed or event.get('category_basis') != 'Codex agent interpretation')}
    if report['event_count'] > 1000:
        raise ValueError('Scope exceeds the 1,000-event report window; select a narrower task')
    if not selected:
        raise ValueError('No unreviewed tool evidence in this scope; use --full for an intentional complete re-review')
    secrets = {}
    if store.capture_root and (store.capture_root.parent / 'local-access.json').exists():
        secrets = json.loads((store.capture_root.parent / 'local-access.json').read_text())
    def clean(value):
        text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
        for key in ('postgres_password', 'redis_password', 'clickhouse_password', 's3_secret', 'salt',
                    'nextauth_secret', 'password', 'encryption_key', 'public_key', 'secret_key'):
            if secrets.get(key):
                text = text.replace(secrets[key], '[REDACTED]')
        return text
    raw = {}
    with store.connection() as c:
        paths = [Path(row['path']) for row in c.execute('SELECT path FROM files')]
    for path in paths:
        meta = None
        for _, record in bridge.monitor.lines(path):
            if not record:
                continue
            p = record.get('payload') or {}
            if record.get('type') == 'session_meta':
                meta = p
            if not meta or record.get('type') != 'event_msg' or p.get('type') != 'item_completed':
                continue
            item = p.get('item') or {}
            ident = meta['id'] + ':tool:' + str(item.get('id'))
            if ident not in selected:
                continue
            command = json.dumps(item['command'], ensure_ascii=False) if item.get('command') is not None else None
            truncated = bool(command and len(command) > 3200)
            if truncated:
                command = command[:2200] + ' ... [TRUNCATED] ... ' + command[-800:]
            raw[ident] = dict(command=clean(sanitized(command)) if command else None, command_truncated=truncated,
                item_type=item.get('type'), failure_excerpt=clean(sanitized(str(item.get('aggregated_output'))[:700])) if item.get('exit_code') not in (None, 0) else None)
    tools = [dict({key: event[key] for key in ('id', 'name', 'category', 'runtime', 'bytes', 'failed', 'ts', 'turn_id', 'task_id')}, **raw.get(event['id'], {})) for event in report['events'] if event['id'] in selected]
    usage = [e['usage'] for e in report['events'] if e['kind'] == 'generation']
    data = dict(snapshot_at=datetime.now(timezone.utc).isoformat(),
        scope=f'Frozen native evidence; task={task or "all"}, project={project or "all"}. Review covers {"all" if include_reviewed else "unreviewed"} tool events; aggregate usage covers the selected scope. This analyst run is excluded.',
        task_definitions=[{k: t[k] for k in ('id', 'title', 'goal', 'acceptance', 'status')} for t in report['tasks'] if not task or t['id'] == task],
        usage=report['usage'], model_response_count=len(usage),
        response_input_range=[min(u['input_tokens'] for u in usage), max(u['input_tokens'] for u in usage)] if usage else None,
        existing_category_breakdown=report['categories'], tools=tools, capture_summary=report['wire_captures'], limits=report['limitations'])
    evidence = json.dumps(data, indent=2)
    (directory / 'evidence.json').write_text(evidence)
    (directory / 'manifest.json').write_text(json.dumps(dict(sha256=hashlib.sha256(evidence.encode()).hexdigest(), tool_events=len(tools), model_responses=len(usage), at=data['snapshot_at']), indent=2))
    (directory / 'schema.json').write_bytes((CONFIG / 'analyst-output.schema.json').read_bytes())
    (directory / 'prompt.txt').write_bytes((CONFIG / 'analyst-prompt.txt').read_bytes())
    return data


def publish(store, directory, model):
    raw = (directory / 'evidence.json').read_bytes()
    manifest = json.loads((directory / 'manifest.json').read_text())
    if hashlib.sha256(raw).hexdigest() != manifest['sha256']:
        raise ValueError('Frozen snapshot hash changed')
    evidence = json.loads(raw)
    analysis = json.loads((directory / 'analysis.json').read_text())
    store.scan()
    report = store.report()
    turns = [turn for turn in report['turns'] if Path(turn['repo']).resolve() == directory.resolve()]
    identities = {(turn['session_id'], turn['turn_id']) for turn in turns}
    overhead = collections.Counter()
    for event in report['events']:
        if (event['session_id'], event['turn_id']) in identities and event['usage']:
            overhead.update({k: event['usage'].get(k, 0) for k in ('input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens')})
    ident = store.publish_analysis(analysis, evidence, dict(id=directory.name, model=model, snapshot_hash=manifest['sha256'], overhead=dict(overhead)))
    if report['projects'] and turns:
        project_ids = {task['project_id'] for task in report['tasks'] if any(t['id'] == task['id'] for t in evidence.get('task_definitions', []))}
        project = next(iter(project_ids)) if len(project_ids) == 1 else report['projects'][0]['id']
        task = store.mutate('task', dict(project_id=project, title='Analyze Codex evidence: ' + ident,
            goal='Explain the frozen evidence and propose verified efficiency improvements.',
            acceptance='A Codex-authored analysis cites valid source events, covers every frozen tool event and separates background lifetime.'))['id']
        for turn in turns:
            store.mutate('assign', dict(session_id=turn['session_id'], turn_id=turn['turn_id'], task_id=task))
        store.mutate('task_status', dict(id=task, status='completed', outcome='Published ' + ident + '; evidence IDs, coverage and immutable snapshot hash validated. Findings are proposals; savings unmeasured.'))
    (directory / 'published.json').write_text(json.dumps(dict(id=ident, overhead=dict(overhead)), indent=2))
    return ident


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['prepare', 'run', 'publish'])
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--task')
    parser.add_argument('--project')
    parser.add_argument('--full', action='store_true', help='Intentionally re-review already annotated events; default is incremental')
    parser.add_argument('--data', type=Path, default=REPO / DEFAULTS['workspace_directory'])
    parser.add_argument('--codex-root', type=Path, default=Path.home() / '.codex')
    parser.add_argument('--captures', type=Path, default=REPO / DEFAULTS['state_directory'] / 'captures')
    parser.add_argument('--langfuse-url', default=public_url())
    parser.add_argument('--model', default='gpt-6.1-sol')
    args = parser.parse_args()
    os.umask(0o077)
    directory = args.directory or REPO / 'work/security/analyses' / ('codex-review-' + uuid.uuid4().hex[:12])
    directory = directory.resolve()
    store = Store(args.data, args.codex_root, args.langfuse_url, args.captures)
    if args.action == 'publish':
        print('Published', publish(store, directory, args.model))
        return
    snapshot(store, directory, args.task, args.project, args.full)
    print('Prepared frozen evidence:', directory, flush=True)
    if args.action == 'prepare':
        return
    command = ['codex', 'exec', '-p', 'ttgl-observability', '-c', 'model_provider="openai"', '--skip-git-repo-check',
               '-C', str(directory), '-m', args.model, '-s', 'read-only',
               '--output-schema', str(directory / 'schema.json'), '--output-last-message', str(directory / 'analysis.json'), '-']
    # One bounded process attempt; native transport retry defaults apply.
    # Never automatically repeat a started or ambiguous analyst process.
    with (directory / 'prompt.txt').open() as prompt, (directory / 'agent.log').open('w') as log:
        result = subprocess.run(command, stdin=prompt, stdout=log, stderr=subprocess.STDOUT, timeout=900)
    if result.returncode:
        raise RuntimeError('Analyst failed; preserve logs and inspect before deciding whether to retry')
    print('Published', publish(store, directory, args.model))


if __name__ == '__main__':
    main()
