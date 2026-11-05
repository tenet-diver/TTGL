#!/usr/bin/env python3
"""Loopback-only bounded HTTP/SSE capture adapter for an explicit Codex provider.

No TLS interception, OAuth implementation, redirects, WebSocket translation or
third-party packages. Credentials are forwarded to the fixed upstream, never
persisted. Bodies are redacted and opaque reasoning protocol fields omitted.
"""
import argparse
import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'langfuse'))
from live_export import safe_content

DEFAULTS = json.loads((Path(__file__).resolve().parents[1] / 'config/defaults.json').read_text())
MAX_BODY = DEFAULTS['capture']['request_limit_bytes']
MAX_CAPTURE = DEFAULTS['capture']['response_capture_limit_bytes']


def sanitized(value):
    if isinstance(value, dict):
        kind = value.get('type', '')
        if isinstance(kind, str) and 'reasoning' in kind and 'summary' not in kind:
            if kind == 'reasoning':
                return {key: sanitized(item) for key, item in value.items() if key in ('type', 'id', 'summary')}
            return {'type': kind, 'content': '[OMITTED reasoning protocol data]'}
        return {k: '[OMITTED]' if k.lower() in ('authorization', 'cookie', 'api_key', 'access_token', 'refresh_token', 'encrypted_content', 'raw_content') else sanitized(v) for k, v in value.items()}
    if isinstance(value, list):
        return [sanitized(v) for v in value]
    if isinstance(value, str):
        return safe_content(value)[0]
    return value


def body_evidence(raw, content_type):
    try:
        # Some compatible gateways label SSE application/octet-stream or omit
        # Content-Type. Detect protocol framing as well as the advertised type.
        probe = raw.lstrip()
        if 'text/event-stream' in content_type or probe.startswith((b'data:', b'event:', b':')):
            events = []
            for line in raw.decode('utf-8', errors='strict').splitlines():
                if line.startswith('data:'):
                    payload = line[5:].strip()
                    if payload == '[DONE]':
                        continue
                    try:
                        events.append(sanitized(json.loads(payload)))
                    except ValueError:
                        events.append({'unparsed_frame': True})
            return {'sse_events': events}
        parsed = sanitized(json.loads(raw))
        return parsed if isinstance(parsed, dict) else {'json_body': parsed}
    except (ValueError, UnicodeError):
        return {'unparsed_body': True, 'bytes': len(raw)}


class StreamEvidence:
    """Bounded SSE framing independent of transport Content-Type.

    Forwarding never depends on parsing. Keep small sanitized frames, extract
    response IDs throughout the stream, and explicitly flag dropped big frames.
    """
    def __init__(self):
        self.line = bytearray()
        self.discard_line = False
        self.events = []
        self.response_ids = []
        self.retained = 0
        self.is_sse = False
        self.truncated = False

    def feed(self, chunk):
        for part in chunk.splitlines(keepends=True):
            ended = part.endswith((b'\n', b'\r'))
            if not self.discard_line:
                if len(self.line) + len(part) > MAX_CAPTURE:
                    self.discard_line = True
                    self.line.clear()
                    self.truncated = True
                else:
                    self.line.extend(part)
            if ended:
                if not self.discard_line:
                    self.consume(bytes(self.line).strip())
                self.line.clear()
                self.discard_line = False

    def consume(self, line):
        if line.startswith((b'event:', b':')):
            self.is_sse = True
        if not line.startswith(b'data:'):
            return
        self.is_sse = True
        payload = line[5:].strip()
        if payload == b'[DONE]':
            return
        try:
            event = json.loads(payload)
        except (ValueError, UnicodeError):
            self.truncated = True
            return
        if isinstance(event, dict):
            response = event.get('response') or {}
            ident = response.get('id') if isinstance(response, dict) else None
            if isinstance(ident, str) and ident.startswith('resp_') and ident not in self.response_ids:
                self.response_ids.append(ident)
        event = sanitized(event)
        size = len(json.dumps(event).encode())
        if self.retained + size <= MAX_CAPTURE:
            self.events.append(event)
            self.retained += size
        else:
            self.truncated = True


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *args):
        return None


class Handler(BaseHTTPRequestHandler):
    protocol_version = 'HTTP/1.1'

    def setup(self):
        super().setup()
        self.connection.settimeout(120)

    def log_message(self, *args):
        pass

    def error(self, code, message):
        raw = json.dumps({'error': message}).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(raw)))
        self.send_header('Connection', 'close')
        self.end_headers()
        self.wfile.write(raw)
        self.close_connection = True

    def do_GET(self):
        self.proxy()

    def do_POST(self):
        self.proxy()

    def proxy(self):
        if self.headers.get('Host') not in (f'localhost:{self.server.server_port}', f'127.0.0.1:{self.server.server_port}'):
            return self.error(403, 'Invalid host')
        if self.server.collection_state and self.server.collection_state.exists():
            with sqlite3.connect(self.server.collection_state) as database:
                row = database.execute("SELECT value FROM settings WHERE key='collection_enabled'").fetchone()
            if row and row[0] != 'true':
                return self.error(503, 'Collection is paused; resume it in the workspace before using the capture route')
        parsed = urllib.parse.urlsplit(self.path)
        if parsed.scheme or parsed.netloc or parsed.path not in ('/responses', '/models', '/v1/responses', '/v1/models'):
            return self.error(404, 'Unsupported capture route')
        if self.headers.get('Upgrade'):
            return self.error(426, 'Use HTTP/SSE; WebSockets are not supported by this adapter')
        if self.headers.get('Transfer-Encoding') or self.headers.get('Content-Encoding') not in (None, 'identity'):
            return self.error(415, 'Use uncompressed requests with Content-Length')
        try:
            length = int(self.headers.get('Content-Length', '0'))
        except ValueError:
            return self.error(400, 'Invalid request length')
        if not 0 <= length <= MAX_BODY:
            return self.error(413, 'Request too large')
        # Preserve existing private captures rather than silently rotating evidence.
        if sum(p.stat().st_size for p in self.server.destination.glob('*.json')) > DEFAULTS['capture']['retained_capture_quota_bytes']:
            return self.error(507, 'Private capture quota reached; archive evidence before continuing')
        raw = self.rfile.read(length)
        ident = uuid.uuid4().hex
        start = time.time_ns()
        record = dict(id=ident, started_ns=start, source='proxy_downstream_http', state='pending',
                      method=self.command, path=parsed.path, request=body_evidence(raw, self.headers.get('Content-Type', '')),
                      headers_persisted=False, opaque_reasoning_omitted=True, redaction='best effort',
                      request_bytes=len(raw), websocket_supported=False)
        self.persist(record)
        # Credentials remain only in memory and only go to the configured upstream.
        headers = {k: v for k, v in self.headers.items() if k.lower() not in
                   ('host', 'connection', 'content-length', 'accept-encoding', 'transfer-encoding', 'proxy-authorization', 'cookie')}
        headers['Accept-Encoding'] = 'identity'
        suffix = parsed.path.removeprefix('/v1')
        if parsed.query:
            suffix += '?' + parsed.query
        request = urllib.request.Request(self.server.upstream + suffix, data=raw if self.command == 'POST' else None,
                                         method=self.command, headers=headers)
        upstream = None
        response_started = False
        captured = bytearray()
        stream_evidence = StreamEvidence()
        first_byte = None
        try:
            opener = urllib.request.build_opener(NoRedirect())
            try:
                upstream = opener.open(request, timeout=120)
            except urllib.error.HTTPError as exc:
                upstream = exc
            record['status'] = upstream.status
            record['headers_received_ns'] = time.time_ns()
            content_type = upstream.headers.get('Content-Type', 'application/octet-stream')
            record['content_type'] = content_type
            self.send_response(upstream.status)
            self.send_header('Content-Type', content_type)
            self.send_header('Transfer-Encoding', 'chunked')
            self.send_header('Cache-Control', 'no-store')
            self.send_header('Connection', 'close')
            self.end_headers()
            response_started = True
            count = 0
            while True:
                chunk = upstream.read1(16384)
                if not chunk:
                    break
                if first_byte is None:
                    first_byte = time.time_ns()
                count += len(chunk)
                captured.extend(chunk[:max(0, MAX_CAPTURE - len(captured))])
                stream_evidence.feed(chunk)
                self.wfile.write(f'{len(chunk):x}\r\n'.encode() + chunk + b'\r\n')
                self.wfile.flush()
            self.wfile.write(b'0\r\n\r\n')
            record.update(state='complete', response_bytes=count, response_truncated=count > MAX_CAPTURE)
        except (BrokenPipeError, ConnectionResetError):
            record.update(state='cancelled', response_truncated=True)
        except Exception as exc:
            record.update(state='error', error=type(exc).__name__, response_truncated=True)
            if not response_started:
                self.error(502, 'Upstream request failed; inspect private capture metadata')
        finally:
            if upstream:
                upstream.close()
            if stream_evidence.line and not stream_evidence.discard_line:
                stream_evidence.consume(bytes(stream_evidence.line).strip())
            response = {'sse_events': stream_evidence.events} if stream_evidence.is_sse else body_evidence(bytes(captured), record.get('content_type', ''))
            record.update(ended_ns=time.time_ns(), first_byte_ns=first_byte, response=response,
                          response_ids=stream_evidence.response_ids, capture_schema=2,
                          response_body_available=bool(stream_evidence.events) if stream_evidence.is_sse else not (isinstance(response, dict) and response.get('unparsed_body', False)),
                          response_truncated=bool(record.get('response_truncated')) or stream_evidence.truncated)
            self.persist(record)
            self.close_connection = True

    def persist(self, record):
        path = self.server.destination / (record['id'] + '.json')
        temporary = path.with_suffix('.tmp')
        fd = os.open(temporary, os.O_WRONLY | os.O_TRUNC | os.O_CREAT, 0o600)
        with os.fdopen(fd, 'w') as stream:
            json.dump(record, stream)
        temporary.replace(path)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--destination', type=Path, required=True)
    p.add_argument('--upstream', default=DEFAULTS['capture']['upstream'])
    p.add_argument('--port', type=int, default=DEFAULTS['ports']['capture'])
    p.add_argument('--collection-state', type=Path)
    args = p.parse_args()
    upstream = urllib.parse.urlsplit(args.upstream)
    if upstream.scheme != 'https' and upstream.hostname not in ('localhost', '127.0.0.1'):
        raise ValueError('Upstream must use HTTPS or a loopback test server')
    if upstream.username or upstream.password or upstream.query or upstream.fragment:
        raise ValueError('Upstream must not contain credentials, query or fragment')
    os.umask(0o077)
    args.destination.mkdir(parents=True, exist_ok=True, mode=0o700)
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.destination, server.upstream = args.destination, args.upstream.rstrip('/')
    server.collection_state = args.collection_state
    print(f'HTTP/SSE capture adapter: http://127.0.0.1:{args.port}; credentials are not persisted', flush=True)
    server.serve_forever()


if __name__ == '__main__':
    main()
