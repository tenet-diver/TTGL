from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.request

import capture_proxy


class CaptureTests(unittest.TestCase):
    def test_http_sse_forwarding_redaction_and_opaque_field_omission(self):
        stream = b'data: {"type":"response.completed","response":{"id":"resp_test","encrypted_content":"OPAQUE","output":[{"text":"CANARY_OK"}]}}\n\ndata: [DONE]\n\n'
        class Upstream(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass
            def do_POST(self):
                self.rfile.read(int(self.headers.get('Content-Length', 0)))
                self.send_response(200)
                self.send_header('Content-Type', 'text/event-stream')
                self.send_header('Content-Length', str(len(stream)))
                self.end_headers()
                self.wfile.write(stream)
        with tempfile.TemporaryDirectory() as directory:
            upstream = ThreadingHTTPServer(('127.0.0.1', 0), Upstream)
            proxy = ThreadingHTTPServer(('127.0.0.1', 0), capture_proxy.Handler)
            proxy.destination = Path(directory)
            proxy.collection_state = None
            proxy.upstream = f'http://127.0.0.1:{upstream.server_port}'
            for server in (upstream, proxy):
                threading.Thread(target=server.serve_forever, daemon=True).start()
                self.addCleanup(server.server_close)
                self.addCleanup(server.shutdown)
            body = json.dumps({'input': 'Reply CANARY_OK', 'api_key': 'PLANTED_SECRET'}).encode()
            req = urllib.request.Request(f'http://127.0.0.1:{proxy.server_port}/responses', data=body,
                headers={'Authorization': 'Bearer HEADER_SECRET', 'Content-Type': 'application/json'})
            with urllib.request.urlopen(req, timeout=5) as response:
                self.assertEqual(response.read(), stream)
            # Request completes before the final journal rename in the handler.
            import time
            for _ in range(50):
                paths = list(Path(directory).glob('*.json'))
                if paths and json.loads(paths[0].read_text())['state'] == 'complete':
                    break
                time.sleep(.01)
            capture = paths[0].read_text()
            self.assertNotIn('HEADER_SECRET', capture)
            self.assertNotIn('PLANTED_SECRET', capture)
            self.assertNotIn('OPAQUE', capture)
            record = json.loads(capture)
            self.assertEqual(record['state'], 'complete')
            self.assertFalse(record['response_truncated'])
            self.assertIsNotNone(record['first_byte_ns'])

    def test_unknown_binary_body_is_not_persisted(self):
        self.assertEqual(capture_proxy.body_evidence(b'PRIVATE_BINARY', 'application/octet-stream'),
                         {'unparsed_body': True, 'bytes': 14})


if __name__ == '__main__':
    unittest.main()
