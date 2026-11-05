#!/usr/bin/env python3
"""Continuously export native Codex turns, tools and measured responses to Langfuse.

Transcript evidence, not wire capture. Uses the existing durable OTLP receipts.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import re
import sqlite3
import time

import bridge

LIMIT = 256 * 1024


def safe_content(value):
    text = value if isinstance(value, str) else json.dumps(value, ensure_ascii=False)
    text = re.sub(r'(?i)(authorization\s*[:=]\s*[\"\x27]?)(?:bearer|basic)\s+[^\s\"\x27]+', r'\1[REDACTED]', text)
    text = re.sub(r'\b(?:sk-lf-|pk-lf-|sk-proj-|sk-)[A-Za-z0-9_-]{16,}', '[REDACTED]', text)
    text = re.sub(r'(?i)([\"\x27]?(?:password|secret_key|access_token|refresh_token|api_key)[\"\x27]?\s*[:=]\s*)[\"\x27][^\"\x27\n]+[\"\x27]', r'\1"[REDACTED]"', text)
    return text[:LIMIT], len(text) > LIMIT


def content(span, kind, value):
    text, truncated = safe_content(value)
    span['attributes'].append(bridge.attr('langfuse.observation.' + kind, text))
    if truncated:
        span['attributes'].append(bridge.attr('langfuse.observation.metadata.' + kind + '_truncated', True))


def native_spans(path):
    meta, tools, bad = bridge.tool_records(path)
    if bad:
        raise ValueError(f'{bad} malformed or oversized transcript lines')
    tools_by_id = {tool['id']: tool for tool in tools}
    sid = meta['id']
    turns = {}
    model = None
    seen = set()
    for line, record in bridge.monitor.lines(path):
        if not record:
            continue
        p = record.get('payload') or {}
        if p.get('thread_id') and p['thread_id'] != sid:
            continue
        timestamp = record.get('timestamp') or meta.get('timestamp')
        if timestamp < meta.get('timestamp', ''):
            continue
        if record.get('type') == 'turn_context':
            model = p.get('model')
        turn = p.get('turn_id')
        if not turn:
            continue
        state = turns.setdefault(turn, dict(prompt=[], messages=[], start=timestamp, model=model))
        trace = 'native-turn-v1:' + sid + ':' + turn
        root = trace + ':root'
        md = dict(record_kind='native_transcript', trace_name='Codex task turn',
                  source='native Codex transcript', turn_id=turn, project=Path(meta.get('cwd', '')).name,
                  wire_capture=False, content_redaction='best effort; not a secret-free guarantee')
        if record.get('type') == 'event_msg':
            kind = p.get('type')
            if kind == 'task_started':
                state['start'] = timestamp
            elif kind == 'item_completed':
                item = p.get('item') or {}
                if item.get('type') == 'UserMessage':
                    state['prompt'].append(item.get('content'))
                elif item.get('type') == 'AgentMessage':
                    state['messages'].append(item.get('content'))
                elif item.get('type') in bridge.NATIVE:
                    ident = item.get('id')
                    if not ident or ident in seen:
                        continue
                    seen.add(ident)
                    native = tools_by_id.get(ident)
                    end = bridge.nanos(timestamp)
                    duration = bridge.runtime.native_ns(item.get('duration'))
                    start = end - duration if duration is not None else end
                    tool = bridge.span(trace, sid + ':native-content:' + ident,
                        native['operation'] if native else item.get('kind', item['type']), 'tool', start, end,
                        'codex-native', dict(md, source_line=line, native_runtime_known=duration is not None,
                        failed=native['failed'] if native else None, timing_basis='native item.duration' if duration is not None else 'unknown; zero width'), sid, root)
                    # Explicit allowlist avoids exporting opaque reasoning or credential stores.
                    content(tool, 'input', {k: item[k] for k in ('command', 'arguments', 'query', 'action', 'changes') if k in item})
                    content(tool, 'output', {k: item[k] for k in ('aggregated_output', 'result', 'results', 'stdout', 'stderr', 'status', 'exit_code') if k in item})
                    yield tool
            elif kind == 'task_complete':
                span = bridge.span(trace, root, 'Codex task turn', 'agent', bridge.nanos(state['start']),
                    bridge.nanos(timestamp), 'codex-native', dict(md, outcome='agent turn completed; task success unverified'), sid)
                content(span, 'input', state['prompt'])
                content(span, 'output', state['messages'])
                yield span
        if record.get('type') == 'token_usage_record':
            ident = p.get('response_id')
            u = p.get('usage') or {}
            if not ident or ident in seen:
                continue
            seen.add(ident)
            required = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens')
            if any(not isinstance(u.get(k), int) or u[k] < 0 for k in required):
                raise ValueError('Unsupported response usage; export stopped for reconciliation')
            if u['cached_input_tokens'] > u['input_tokens'] or u['input_tokens'] + u['output_tokens'] != u['total_tokens']:
                raise ValueError('Non-reconciling response usage')
            usage = dict(input=u['input_tokens'] - u['cached_input_tokens'],
                         input_cached_tokens=u['cached_input_tokens'], output=u['output_tokens'], total=u['total_tokens'])
            when = bridge.nanos(timestamp)
            yield bridge.span(trace, sid + ':response:' + ident, 'Measured model response', 'generation', when, when,
                'codex-native', dict(md, response_id=ident, measured_usage=True, model_latency_known=False,
                wire_input_available=False, wire_output_available=False, reported_reasoning_subset=u.get('reasoning_output_tokens'),
                pricing='Langfuse price scenario; actual subscription charge unknown'), sid, root,
                usage=usage, model=state.get('model') or model)


def capture_spans(root):
    for path in sorted(root.glob('*.json')):
        record = json.loads(path.read_text())
        if record.get('state') == 'pending':
            continue
        ident = 'transport-v1:' + record['id']
        response_ids = []
        for event in record.get('response', {}).get('sse_events', []):
            response_id = (event.get('response') or {}).get('id') if isinstance(event, dict) else None
            if response_id and response_id not in response_ids:
                response_ids.append(response_id)
        md = dict(record_kind='http_transport', trace_name='Codex HTTP capture', source='proxy_downstream_http',
                  capture_id=record['id'], path=record['path'], status=record.get('status'),
                  failed=record.get('state') in ('error', 'cancelled') or (record.get('status') or 0) >= 400,
                  capture_state=record['state'], response_ids=response_ids,
                  response_truncated=record.get('response_truncated', False),
                  first_body_byte_seconds=(record['first_byte_ns'] - record['started_ns']) / 1e9 if record.get('first_byte_ns') else None,
                  timing_scope='HTTP transport; not pure inference latency', token_accounting='Native generation records only; never add proxy usage',
                  headers_persisted=False, opaque_reasoning_omitted=True, redaction='best effort')
        span = bridge.span(ident, ident, 'Codex model request / response' if record['path'].endswith('/responses') else 'Codex model catalog fetch',
            'span', record['started_ns'], record['ended_ns'], 'codex-transport', md)
        content(span, 'input', record.get('request'))
        content(span, 'output', record.get('response'))
        yield span


def run(args):
    args.state.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.umask(0o077)
    lock = (args.state / 'run.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    while True:
        if args.collection_state and args.collection_state.exists():
            with sqlite3.connect(args.collection_state) as db:
                row = db.execute("SELECT value FROM settings WHERE key='collection_enabled'").fetchone()
            if row and row[0] != 'true':
                if not args.watch:
                    raise RuntimeError('Source collection is paused')
                time.sleep(5)
                continue
        exporter = bridge.Exporter(args.credentials, args.state)
        files = sorted(args.codex_root.joinpath('sessions').rglob('*.jsonl'))
        files += sorted(args.codex_root.joinpath('archived_sessions').rglob('*.jsonl'))
        errors = []
        for path in files:
            try:
                for span in native_spans(path):
                    exporter.add(span)
                exporter.flush()
            except Exception as exc:
                errors.append(dict(file=path.name, error=type(exc).__name__, detail=str(exc)[:200]))
                # Stop instead of replaying ambiguous immutable records.
                break
        if args.capture_root and not errors:
            for span in capture_spans(args.capture_root):
                exporter.add(span)
            exporter.flush()
        status = dict(at=bridge.monitor.now(), files=len(files), exported=exporter.exported,
                      skipped=exporter.skipped, errors=errors, source='native_transcript',
                      transport_capture_directory_configured=bool(args.capture_root),
                      all_sessions_proxied=False)
        (args.state / 'status.json').write_text(json.dumps(status, indent=2))
        print(json.dumps(status), flush=True)
        exporter.db.close()
        if errors:
            raise RuntimeError('Export stopped; see private status and reconcile delivery before retrying')
        if not args.watch:
            break
        time.sleep(15)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--credentials', type=Path, required=True)
    p.add_argument('--state', type=Path, required=True)
    p.add_argument('--codex-root', type=Path, default=Path.home() / '.codex')
    p.add_argument('--watch', action='store_true')
    p.add_argument('--collection-state', type=Path, help='Workspace SQLite permission state; pauses new exports when disabled')
    p.add_argument('--capture-root', type=Path, help='Private HTTP/SSE capture directory; separate observations without token accounting')
    run(p.parse_args())
