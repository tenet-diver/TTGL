#!/usr/bin/env python3
"""Exercise the existing official memory MCP across processes; no model calls."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from mcp_memory_probe import Client


def open_client(entry, memory, log):
    client = Client(entry, memory, log)
    try:
        client.request('initialize', dict(protocolVersion='2025-06-18', capabilities={},
            clientInfo=dict(name='ttgl_shared_memory_probe', version='1')))
        client.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n')
        client.p.stdin.flush()
        return client
    except BaseException:
        client.close()
        raise


def run(entry, output, scan):
    review = json.loads(scan.read_text())
    if review['known_findings']:
        raise ValueError('Known advisory findings block execution')
    output.mkdir(parents=True, exist_ok=False)
    memory = output / 'shared.jsonl'
    (output / 'manifest.json').write_text(json.dumps(dict(
        at=datetime.now(timezone.utc).isoformat(), model_calls=0,
        entry=str(entry.resolve()), entry_sha256=hashlib.sha256(entry.read_bytes()).hexdigest(),
        scan_sha256=hashlib.sha256(scan.read_bytes()).hexdigest(), workers=8,
        scope='Actual official MCP persistence/visibility/concurrent updates only; not agent efficacy'), indent=2))
    clients, checks = [], {}
    try:
        for i in range(8):
            clients.append(open_client(entry, memory, output / f'worker-{i}.log'))
        name = 'procedure:widget_store'
        command = 'python -m pytest tests/unit'
        clients[0].tool('create_entities', dict(entities=[dict(name=name,
            entityType='SyntheticProcedure', observations=['synthetic fixture: ' + command])]))
        found = clients[1].tool('search_nodes', dict(query=name))
        checks['peer_reads_another_process_write'] = any(
            n['name'] == name and 'synthetic fixture: ' + command in n['observations'] for n in found['entities'])

        def write(i):
            return clients[i].tool('create_entities', dict(entities=[dict(name=f'worker:{i}',
                entityType='SyntheticFinding', observations=[f'fixture source:{i}'])]))

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(write, range(8)))
        graph = clients[0].tool('read_graph', {})
        expected = {name, *(f'worker:{i}' for i in range(8))}
        checks['eight_process_updates_all_retained'] = {n['name'] for n in graph['entities']} == expected
        clients[1].tool('add_observations', dict(observations=[dict(entityName=name,
            contents=['synthetic revision2: command remains ' + command])]))
        revised = clients[0].tool('search_nodes', dict(query=name))
        checks['peer_revision_visible'] = any(
            'synthetic revision2: command remains ' + command in n['observations'] for n in revised['entities'])
        isolated = open_client(entry, output / 'isolated.jsonl', output / 'isolated.log')
        try:
            result = isolated.tool('read_graph', {})
            checks['separate_store_starts_empty'] = not result['entities'] and not result['relations']
        finally:
            isolated.close()
    finally:
        for client in clients:
            client.close()
    reopened = open_client(entry, memory, output / 'reopened.log')
    try:
        final = reopened.tool('read_graph', {})
        checks['reopen_preserves_all_updates'] = {n['name'] for n in final['entities']} == expected
        (output / 'final-graph.json').write_text(json.dumps(final, indent=2))
    finally:
        reopened.close()
    result = dict(at=datetime.now(timezone.utc).isoformat(), checks=checks,
        passed=all(checks.values()), model_calls=0,
        limits='Synthetic direct MCP clients. Codex all-member tool inheritance and task efficacy remain untested.')
    (output / 'result.json').write_text(json.dumps(result, indent=2))
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--entry', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--scan', type=Path, required=True)
    args = parser.parse_args()
    run(args.entry, args.output, args.scan)
