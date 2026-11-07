#!/usr/bin/env python3
"""Read existing thread estimates without starting/resuming a model turn.

Keep raw replies private. Empty groups/all-zero defaults are unavailable evidence,
not evidence of zero inference expense. This does not read a cash invoice.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import selectors
import subprocess
from mcp_memory_probe import Client


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--thread', action='append', required=True)
    args = parser.parse_args()
    os.umask(0o077)
    args.output.mkdir(parents=True, exist_ok=False)
    client = Client.__new__(Client)
    client.err = (args.output/'stderr.log').open('x')
    client.p = subprocess.Popen(
        ['codex', 'app-server', '--listen', 'stdio://', '-c',
         'mcp_servers.ttgl-analyst.enabled=false'],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=client.err,
        start_new_session=True)
    client.selector = selectors.DefaultSelector()
    client.selector.register(client.p.stdout, selectors.EVENT_READ)
    client.buffer = b''
    client.ident = 0
    client.calls = []
    client.journal = (args.output/'rpc.jsonl').open('x')
    rows = []
    try:
        client.request('initialize', dict(
            clientInfo=dict(name='ttgl_read_only_billing', version='1'),
            capabilities=dict(experimentalApi=True)))
        client.p.stdin.write(b'{"method":"initialized","params":{}}\n')
        client.p.stdin.flush()
        for thread in args.thread:
            try:
                reply = client.request('account/usage/read', dict(threadId=thread))
                rows.append(dict(thread_id=thread, reply=reply))
            except (RuntimeError, TimeoutError) as error:
                rows.append(dict(thread_id=thread, error=str(error), billing=None))
    finally:
        client.close()
    result = dict(at=datetime.now(timezone.utc).isoformat(), model_calls=0,
                  thread_mutations=0, rows=rows, cash_cost=None,
                  interpretation='Raw backend estimates require reconciliation; '
                  'missing, empty or all-zero defaults do not imply zero expense.')
    (args.output/'results.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(dict(model_calls=0, checked_threads=len(rows),
                         rpc_errors=sum('error' in r for r in rows),
                         cash_cost=None)))


if __name__ == '__main__':
    main()
