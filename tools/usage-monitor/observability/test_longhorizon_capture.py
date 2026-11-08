from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import json
from pathlib import Path
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from unittest.mock import patch
import capture_proxy_longhorizon as proxy
from capture_objects import read_capture


class LongCaptureTests(unittest.TestCase):
    def test_large_body_compaction_passthrough_and_rejected_ingress(self):
        seen=[]
        response=json.dumps(dict(id='cmp_fixture',usage=dict(input_tokens=41,output_tokens=9,total_tokens=50),encrypted_content='opaque-value')).encode()
        class Upstream(BaseHTTPRequestHandler):
            def do_POST(self):
                seen.append(self.rfile.read(int(self.headers['Content-Length'])))
                self.send_response(200)
                self.send_header('Content-Type','application/json')
                self.send_header('Content-Length',str(len(response)))
                self.end_headers()
                self.wfile.write(response)
            def log_message(self,*args):pass
        upstream=ThreadingHTTPServer(('127.0.0.1',0),Upstream)
        with tempfile.TemporaryDirectory() as directory:
            server=ThreadingHTTPServer(('127.0.0.1',0),proxy.Handler)
            server.destination=Path(directory)
            server.upstream='http://127.0.0.1:'+str(upstream.server_port)
            server.collection_state=None
            server.experimental_archive=False
            threads=[threading.Thread(target=s.serve_forever,daemon=True) for s in (server,upstream)]
            for thread in threads:thread.start()
            try:
                long_text='x'*262140+' Authorization: Bearer sensitive-fixture-value end-marker'
                raw=json.dumps(dict(input=[dict(text=long_text)],password='credential-fixture')).encode()
                url='http://127.0.0.1:'+str(server.server_port)+'/responses/compact'
                with urllib.request.urlopen(urllib.request.Request(url,data=raw),timeout=5) as reply:
                    self.assertEqual(reply.read(),response)
                deadline=time.monotonic()+3
                while not list(Path(directory).glob('*.json')) and time.monotonic()<deadline:time.sleep(.01)
                paths=list(Path(directory).glob('*.json'))
                self.assertEqual(len(paths),1)
                record=read_capture(paths[0])
                self.assertEqual(seen,[raw])
                retained=record['request']['input'][0]['text']
                self.assertGreater(len(retained),262144)
                self.assertTrue(retained.endswith('end-marker'))
                self.assertNotIn('sensitive-fixture-value',retained)
                self.assertEqual(record['request']['password'],'[OMITTED]')
                self.assertEqual(record['response']['encrypted_content'],'[OMITTED]')
                self.assertEqual(record['response_ids'],['cmp_fixture'])
                self.assertEqual(record['response']['usage']['total_tokens'],50)
                self.assertEqual(len(list((Path(directory)/'pending').glob('*.json'))),1)
                with patch.object(proxy.shutil,'disk_usage',return_value=type('Usage',(),dict(free=0))()):
                    with self.assertRaises(urllib.error.HTTPError) as error:
                        urllib.request.urlopen(urllib.request.Request(url,data=b'{}'),timeout=5)
                    self.assertEqual(error.exception.code,507)
                    error.exception.close()
                rejected=[read_capture(p) for p in (Path(directory)/'rejections').glob('*.json')]
                self.assertEqual(len(rejected),1)
                self.assertEqual(rejected[0]['upstream_submission'],'not_attempted')
                self.assertEqual(seen,[raw])
            finally:
                for service in (server,upstream):service.shutdown();service.server_close()
                for thread in threads:thread.join(timeout=3)

    def test_old_redaction_limit_is_not_mutated(self):
        from live_export import safe_content
        self.assertEqual(len(safe_content('x'*300000)[0]),262144)
        self.assertEqual(len(proxy.base.safe_content('x'*300000)[0]),300000)


if __name__=='__main__':unittest.main()
