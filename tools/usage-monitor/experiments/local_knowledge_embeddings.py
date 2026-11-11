#!/usr/bin/env python3
"""Local OpenAI embedding transport over the existing reviewed FastEmbed bridge.

No extraction, retrieval or graph implementation. Keeps the pinned BGE model,
normalization and actual token counting from the maintained inference library.
"""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import struct
import threading
import time
import uuid


class Handler(BaseHTTPRequestHandler):
    def reply(self, code, value):
        data = json.dumps(value).encode()
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == '/health':
            return self.reply(200, dict(ready=True, model='local-embedding', dimensions=384))
        self.reply(404, dict(error='Unsupported route'))

    def do_POST(self):
        if self.path != '/v1/embeddings':
            return self.reply(404, dict(error='Unsupported route'))
        try:
            self.connection.settimeout(10)
            size = int(self.headers.get('Content-Length', 0))
            if not 0 < size <= 1024 * 1024:
                raise ValueError('Invalid request size')
            body = json.loads(self.rfile.read(size))
            if not isinstance(body, dict) or body.get('model') != 'local-embedding':
                raise ValueError('Use the configured local-embedding alias')
            texts = body.get('input')
            texts = [texts] if isinstance(texts, str) else texts
            if not isinstance(texts, list) or not 1 <= len(texts) <= 128 or any(not isinstance(t, str) or not t for t in texts):
                raise ValueError('One to128 nonempty text inputs required')
            encoding = body.get('encoding_format', 'float')
            if encoding not in ('float', 'base64') or body.get('dimensions', 384) != 384:
                raise ValueError('Only384-dimensional float/base64 embeddings supported')
        except (ValueError, TypeError, OSError) as error:
            return self.reply(400, dict(error=dict(type='invalid_request_error', message=str(error))))
        ident = uuid.uuid4().hex
        received = time.perf_counter()
        with (self.server.evidence / (ident + '.started.json')).open('x') as stream:
            json.dump(dict(id=ident, at=datetime.now(timezone.utc).isoformat(), request=body), stream)
        try:
            with self.server.lock:
                began, cpu = time.perf_counter(), time.process_time()
                normalized = [text.replace('\n', ' ') for text in texts]
                count = self.server.embedding.model.token_count(normalized)
                vectors = [self.server.embedding(text) for text in texts]
                if any(len(v) != 384 for v in vectors):
                    raise ValueError('Unexpected model dimension')
                values = [base64.b64encode(struct.pack('<384f', *v)).decode() for v in vectors] if encoding == 'base64' else vectors
                result = dict(object='list', model='local-embedding',
                    data=[dict(object='embedding', index=i, embedding=v) for i, v in enumerate(values)],
                    usage=dict(prompt_tokens=count, total_tokens=count))
                record = dict(id=ident, at=datetime.now(timezone.utc).isoformat(), response=result,
                    queue_seconds=began - received, operation_seconds=time.perf_counter() - began,
                    process_cpu_seconds=time.process_time() - cpu, local_embedding_inferences=len(texts),
                    token_definition='FastEmbed.token_count: sum of nonpadding attention masks after configured truncation',
                    model_input_window=512, normalization='newline to space, existing reviewed bridge')
                with (self.server.evidence / (ident + '.completed.json')).open('x') as stream:
                    json.dump(record, stream)
        except BaseException as error:
            with (self.server.evidence / (ident + '.failed.json')).open('x') as stream:
                json.dump(dict(id=ident, error=repr(error), usage=None, automatic_retries=0), stream)
            return self.reply(422, dict(error=dict(type='local_embedding_error', message=type(error).__name__)))
        self.reply(200, result)

    def log_message(self, *_args):
        pass


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--assets', type=Path, required=True)
    parser.add_argument('--evidence', type=Path, required=True)
    parser.add_argument('--port', type=int, default=8451)
    args = parser.parse_args()
    if os.environ.get('HF_HUB_OFFLINE') != '1':
        raise ValueError('Offline loading required')
    import onnxruntime
    onnxruntime.disable_telemetry_events()
    from smallville_local_embeddings import LocalEmbeddings
    os.umask(0o077)
    args.evidence.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    server = ThreadingHTTPServer(('127.0.0.1', args.port), Handler)
    server.embedding = LocalEmbeddings(args.assets, args.evidence / 'embedding-operations.jsonl')
    server.evidence, server.lock = args.evidence, threading.Lock()
    (args.evidence / 'ready.json').write_text(json.dumps(dict(
        at=datetime.now(timezone.utc).isoformat(), model='BAAI/bge-small-en-v1.5',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        load_seconds=time.perf_counter() - started, hosted_calls=0, model_calls=0), indent=2))
    print('Local embedding provider ready.', flush=True)
    server.serve_forever()
