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

    def test_live_route_forwards_compressed_body_and_journals_both_versions(self):
        received=[]
        class Upstream(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_POST(self):
                received.append((self.path,json.loads(self.rfile.read(int(self.headers['Content-Length'])))))
                raw=b'data: {"response":{"id":"resp_compressed"}}\n\n'
                self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        with tempfile.TemporaryDirectory() as directory:
            upstream=ThreadingHTTPServer(('127.0.0.1',0),Upstream)
            proxy=ThreadingHTTPServer(('127.0.0.1',0),capture_proxy.Handler)
            proxy.destination=Path(directory);proxy.collection_state=None;proxy.upstream=f'http://127.0.0.1:{upstream.server_port}'
            for server in (upstream,proxy):
                threading.Thread(target=server.serve_forever,daemon=True).start()
                self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
            text=' abcdef012345 Downloading 12B\n'*200+'Error: disk quota\n'
            body=dict(input=[dict(type='message',role='user',content=text),dict(type='custom_tool_call_output',call_id='c',output=text)])
            request=urllib.request.Request(f'http://127.0.0.1:{proxy.server_port}/compress/progress/responses',data=json.dumps(body).encode(),headers={'Content-Type':'application/json'})
            urllib.request.urlopen(request,timeout=5).read()
            self.assertEqual(received[0][0],'/responses')
            self.assertEqual(received[0][1]['input'][0],body['input'][0])
            self.assertNotIn('Downloading 12B',received[0][1]['input'][1]['output'])
            self.assertIn('Error: disk quota',received[0][1]['input'][1]['output'])
            import time
            for _ in range(50):
                captures=list(Path(directory).glob('*.json'))
                if captures and json.loads(captures[0].read_text())['state']=='complete': break
                time.sleep(.01)
            record=json.loads(captures[0].read_text())
            self.assertEqual(record['request'],body)
            self.assertEqual(record['forwarded_request'],received[0][1])
            self.assertTrue(record['compression']['changes'])
            self.assertEqual(len(list(Path(directory).joinpath('compression_sources').glob('*.json'))),1)

    def test_unknown_binary_body_is_not_persisted(self):
        self.assertEqual(capture_proxy.body_evidence(b'PRIVATE_BINARY', 'application/octet-stream'),
                         {'unparsed_body': True, 'bytes': 14})
        self.assertEqual(capture_proxy.body_evidence(b'["error"]', 'application/json'), {'json_body': ['error']})

    def test_octet_stream_sse_is_parsed_and_response_ids_survive_chunks(self):
        raw = b'event: response.created\ndata: {"type":"response.created","response":{"id":"resp_real","encrypted_content":"OPAQUE"}}\n\ndata: {"type":"response.output_text.delta","delta":"hello"}\n\n'
        self.assertIn('sse_events', capture_proxy.body_evidence(raw, 'application/octet-stream'))
        recorder = capture_proxy.StreamEvidence()
        for offset in range(0, len(raw), 7):
            recorder.feed(raw[offset:offset+7])
        self.assertEqual(recorder.response_ids, ['resp_real'])
        self.assertEqual(len(recorder.events), 2)
        self.assertNotIn('OPAQUE', json.dumps(recorder.events))

    def test_oversize_frame_is_flagged_without_losing_following_frames(self):
        recorder = capture_proxy.StreamEvidence()
        recorder.feed(b'data: ' + b'x' * (capture_proxy.MAX_CAPTURE + 10) + b'\n')
        recorder.feed(b'data: {"response":{"id":"resp_after"}}\n\n')
        self.assertTrue(recorder.truncated)
        self.assertEqual(recorder.response_ids, ['resp_after'])


if __name__ == '__main__':
    unittest.main()
