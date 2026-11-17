#!/usr/bin/env python3
"""Read-only Observatory HTTP benchmark; never an agent-quality benchmark.

Uses only the standard library. No model calls, dependency installation, source
imports, mutations or scheduling. Reports failures and empty data explicitly.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import math
import os
from pathlib import Path
import time
import urllib.error
import urllib.parse
import urllib.request


def percentile(values, fraction):
    if not values:
        return None
    values = sorted(values)
    return values[max(0, math.ceil(len(values) * fraction) - 1)]


def inspect_response(path, status, body):
    if status != 200:
        return {"ok": False, "reason": "http_error", "status": status}
    if path.startswith('/api/records/'):
        value = json.loads(body)
        total, rows = value.get('total'), value.get('rows')
        if not isinstance(total, int) or isinstance(total, bool) or total < 0 or not isinstance(rows, list):
            return {"ok": False, "reason": "invalid_record_shape"}
        ids = [row.get('id') for row in rows]
        if len(rows) > 20 or any(not isinstance(i, str) for i in ids) or len(ids) != len(set(ids)):
            return {"ok": False, "reason": "invalid_page_identity"}
        signature = hashlib.sha256(json.dumps([total, ids], separators=(',', ':')).encode()).hexdigest()
        return {"ok": True, "total": total, "returned": len(rows), "identity_sha256": signature}
    if path.startswith('/api/health'):
        value = json.loads(body)
        ready = value.get('postgres') is True and value.get('clickhouse') is True and value.get('raw_storage', value.get('garage')) is True
        return {"ok": ready, "reason": None if ready else 'service_unhealthy', "services": value}
    text = body.decode('utf-8')
    ok = 'Observatory' in text and 'data services are unavailable' not in text
    return {"ok": ok, "reason": None if ok else 'page_error'}


def request(base, path, timeout):
    start = time.perf_counter_ns()
    try:
        req = urllib.request.Request(base + path, headers={'Accept-Encoding': 'identity'})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                status, body = response.status, response.read()
        except urllib.error.HTTPError as error:
            status, body = error.code, error.read()
        elapsed = (time.perf_counter_ns() - start) / 1_000_000
        return {"latency_ms": elapsed, "status": status, "response_bytes": len(body), "check": inspect_response(path, status, body)}
    except Exception as error:
        return {"latency_ms": (time.perf_counter_ns() - start) / 1_000_000, "status": None, "response_bytes": None,
                "check": {"ok": False, "reason": type(error).__name__}}


def benchmark(base, samples=10, timeout=20, minimum_turns=1, project=''):
    url = urllib.parse.urlsplit(base)
    if url.scheme != 'http' or url.hostname not in ('127.0.0.1', '::1') or url.username or url.password or url.path not in ('', '/') or url.query or url.fragment:
        raise ValueError('Benchmark requires a literal loopback HTTP application endpoint')
    query = urllib.parse.urlencode({'range': 'all', 'limit': 20, 'project': project})
    paths = ['/api/health', '/tasks?' + query, '/api/records/tasks?' + query, '/api/records/tools?' + query, '/api/records/models?' + query]
    cases = []
    for path in paths:
        first = request(base.rstrip('/'), path, timeout)
        measured = [request(base.rstrip('/'), path, timeout) for _ in range(samples)]
        values = [r['latency_ms'] for r in measured if r['check']['ok']]
        signatures = {r['check'].get('identity_sha256') for r in [first, *measured] if r['check'].get('identity_sha256')}
        cases.append({'path': path, 'first_observed': first, 'samples': measured, 'p50_ms': percentile(values, .5),
                      'p95_ms': percentile(values, .95), 'failures': sum(not r['check']['ok'] for r in measured),
                      'record_page_stable': len(signatures) <= 1})
    task_case = next(c for c in cases if c['path'].startswith('/api/records/tasks?'))
    task_totals = [r['check'].get('total') for r in [task_case['first_observed'], *task_case['samples']]]
    data_ready = all(isinstance(n, int) and n >= minimum_turns for n in task_totals)
    passed = data_ready and all(c['first_observed']['check']['ok'] and not c['failures'] and c['record_page_stable'] for c in cases)
    return {'schema_version': 1, 'kind': 'observatory_http_performance', 'at': datetime.now(timezone.utc).isoformat(),
            'base_url': base, 'project': project or None, 'samples_per_endpoint': samples, 'concurrency': 1,
            'minimum_native_turns': minimum_turns, 'data_ready': data_ready, 'checks_passed': passed, 'cases': cases,
            'model_calls': 0, 'limitations': ['HTTP response latency, not browser paint, agent task latency or model latency.',
                'First observed request is not a cold-start measurement.', 'Sequential observational samples; no causal speedup claim.',
                'Task activity lists native turns, distinct from explicit tasks.', 'No raw prompts, tool arguments or results are written to this report.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url', default='http://127.0.0.1:3333')
    parser.add_argument('--samples', type=int, default=10)
    parser.add_argument('--minimum-turns', type=int, default=1)
    parser.add_argument('--project', default='')
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    if not 1 <= args.samples <= 100 or args.minimum_turns < 1:
        parser.error('Use 1..100 samples and at least one expected native turn')
    if args.output.exists():
        parser.error('Output already exists; preserve previous measurements')
    result = benchmark(args.base_url, args.samples, minimum_turns=args.minimum_turns, project=args.project)
    args.output.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with args.output.open('x') as file:
        os.chmod(args.output, 0o600)
        json.dump(result, file, indent=2)
        file.write('\n')
    print(json.dumps({'report': str(args.output), 'data_ready': result['data_ready'], 'checks_passed': result['checks_passed'], 'model_calls': 0}))
    raise SystemExit(0 if result['checks_passed'] else 2)


if __name__ == '__main__':
    main()
