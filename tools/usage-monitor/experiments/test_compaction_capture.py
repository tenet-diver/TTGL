import json
from pathlib import Path
import sys
import tempfile
import threading
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'observability'))
import capture_proxy_compaction as proxy


class CaptureTests(unittest.TestCase):
    def test_compaction_is_exact_passthrough_with_separate_operation(self):
        seen = []
        reply = dict(id='cmp_test', output=[dict(type='compaction', encrypted_content='opaque-secret')],
                     usage=dict(input_tokens=123, output_tokens=45, total_tokens=168))
        body = json.dumps(reply).encode()
        class Upstream(BaseHTTPRequestHandler):
            def do_POST(self):
                seen.append((self.path, self.rfile.read(int(self.headers['Content-Length']))))
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            def log_message(self, *args):
                pass
        upstream = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
        with tempfile.TemporaryDirectory() as directory:
            server = ThreadingHTTPServer(('127.0.0.1', 0), proxy.Handler)
            server.destination = Path(directory)
            server.upstream = 'http://127.0.0.1:'+str(upstream.server_port)
            server.collection_state = None
            server.experimental_archive = False
            threads = [threading.Thread(target=s.serve_forever, daemon=True) for s in (server, upstream)]
            for thread in threads:
                thread.start()
            try:
                request = b'{"model":"fixture","input":[],"encrypted_content":"private-request"}'
                url = 'http://127.0.0.1:'+str(server.server_port)+'/responses/compact'
                with urllib.request.urlopen(urllib.request.Request(url, data=request), timeout=5) as response:
                    self.assertEqual(response.read(), body)
                self.assertEqual(seen, [('/responses/compact', request)])
                # Handler persists after completing the downstream stream.
                import time
                deadline = time.monotonic()+2
                while time.monotonic()<deadline:
                    paths = list(Path(directory).glob('*.json'))
                    if paths and json.loads(paths[0].read_text()).get('ended_ns'):
                        break
                    time.sleep(.01)
                records = [json.loads(p.read_text()) for p in Path(directory).glob('*.json')]
                self.assertEqual(len(records), 1)
                record = records[0]
                self.assertEqual(record['operation'], 'compaction')
                self.assertEqual(record['response_ids'], ['cmp_test'])
                self.assertEqual(record['response']['usage'], reply['usage'])
                self.assertNotIn('opaque-secret', json.dumps(record))
                self.assertNotIn('private-request', json.dumps(record))
            finally:
                for service in (server, upstream):
                    service.shutdown()
                    service.server_close()
                for thread in threads:
                    thread.join(timeout=3)


if __name__ == '__main__':
    unittest.main()
