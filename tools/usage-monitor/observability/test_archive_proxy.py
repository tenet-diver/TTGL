from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
import hashlib,json
import shlex,subprocess
import os
from pathlib import Path
import tempfile,threading,time,unittest,urllib.request,urllib.error
from capture_proxy import Handler,experimental_archive_transform
from exact_source_archive import ExactSourceArchive

class ArchiveProxyTests(unittest.TestCase):
    def test_relative_archive_scope_is_absolute_and_shell_quoted(self):
        with tempfile.TemporaryDirectory(prefix='ttgl archive ') as d:
            captures=Path(d)/'private captures';text='Verified safe diagnostic record.\n'*120
            doc=dict(input=[dict(type='custom_tool_call',name='exec',status='completed',call_id='c'),dict(type='custom_tool_call_output',call_id='c',output=text)])
            updated,meta=experimental_archive_transform(doc,'reversible-shell-handles',Path(os.path.relpath(captures)))
            self.assertTrue(meta['changes'])
            command=updated['input'][1]['output'].split('shell command: ',1)[1].split('\nThis archive handle',1)[0]
            args=shlex.split(command);self.assertEqual(args[args.index('--capture-root')+1],str(captures.resolve()))
            raw=json.loads(subprocess.run(args,capture_output=True,text=True,timeout=10,check=True).stdout)
            self.assertEqual(raw['content'],text)
    def test_missing_model_recovery_is_passthrough(self):
        doc=dict(input=[dict(type='function_call_output',call_id='c',output='value '*500)])
        with tempfile.TemporaryDirectory() as d:
            transformed,meta=experimental_archive_transform(doc,'reversible-handles',Path(d))
            self.assertEqual(transformed,doc);self.assertFalse(meta['changes']);self.assertFalse(list(Path(d).iterdir()))
    def test_real_http_route_requires_optin_and_forwards_exact_recoverable_handle(self):
        received=[]
        class Upstream(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_POST(self):
                received.append(json.loads(self.rfile.read(int(self.headers['Content-Length']))))
                raw=b'data: {"type":"response.completed","response":{"id":"test"}}\n\n'
                self.send_response(200);self.send_header('Content-Length',str(len(raw)));self.end_headers();self.wfile.write(raw)
        with tempfile.TemporaryDirectory() as d:
            upstream=ThreadingHTTPServer(('127.0.0.1',0),Upstream);proxy=ThreadingHTTPServer(('127.0.0.1',0),Handler)
            proxy.destination=Path(d);proxy.collection_state=None;proxy.upstream=f'http://127.0.0.1:{upstream.server_port}'
            for server in (upstream,proxy):
                threading.Thread(target=server.serve_forever,daemon=True).start();self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
            text='Verified record lambda, no credentials.\n'*100;digest=hashlib.sha256(text.encode()).hexdigest()
            doc=dict(tools=[dict(type='function',name='mcp__ttgl__read_compression_source')],input=[dict(type='function_call_output',call_id='c',output=text,status='completed')])
            def call(policy='reversible-handles'):
                request=urllib.request.Request(f'http://127.0.0.1:{proxy.server_port}/compress/{policy}/responses',data=json.dumps(doc).encode(),headers={'Content-Type':'application/json'})
                return urllib.request.urlopen(request,timeout=5).read()
            with self.assertRaises(urllib.error.HTTPError) as e:call()
            self.assertEqual(e.exception.code,404);e.exception.close();self.assertFalse(received)
            proxy.experimental_archive=True;call()
            self.assertIn(digest,received[0]['input'][0]['output']);self.assertEqual(received[0]['input'][0]['call_id'],'c');self.assertEqual(received[0]['tools'],doc['tools'])
            self.assertEqual(ExactSourceArchive(Path(d)/'compression_sources',lambda x:x).read(digest),text)
            # A marked raw recovery must survive the very same active route.
            doc['input'][0]['output']='TTGL_RAW_EVIDENCE\n'+text;call()
            self.assertEqual(received[1],doc)
            # Alternative route requires an actually completed native shell call,
            # and recovers through the existing CLI with this archive's scope.
            doc=dict(input=[dict(type='custom_tool_call',name='exec',status='completed',call_id='shell',input='cat fixture.txt'),dict(type='custom_tool_call_output',call_id='shell',output=text)])
            call('reversible-shell-handles')
            output=received[2]['input'][1]['output'];self.assertIn(digest,output)
            command=output.split('shell command: ',1)[1].split('\nThis archive handle',1)[0]
            restored=subprocess.run(shlex.split(command),capture_output=True,text=True,timeout=10,check=True)
            raw=json.loads(restored.stdout);self.assertEqual(raw['content'],text);self.assertTrue(raw['TTGL_RAW_EVIDENCE'])
            self.assertNotIn('--data',shlex.split(command))
            self.assertFalse(list(Path(d).rglob('workspace.sqlite')))
            # The SSE consumer can finish before the handler seals its journal.
            # Await both owned receipts before removing the temporary directory.
            for _ in range(100):
                records=[json.loads(p.read_text()) for p in Path(d).glob('*.json')]
                if len(records)==3 and all(r['state']=='complete' for r in records):break
                time.sleep(.01)
            self.assertEqual(len(records),3)
            self.assertTrue(all(r['state']=='complete' for r in records))
if __name__=='__main__':unittest.main()
