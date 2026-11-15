import io
import json
import selectors
import subprocess
import sys
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch

from mcp_memory_probe import Client
from team_memory_startup_transport import StartupClient


class StartupTransportTests(unittest.TestCase):
    def client(self,delay,timeout):
        tmp=tempfile.TemporaryDirectory();self.addCleanup(tmp.cleanup);root=Path(tmp.name)
        c=StartupClient.__new__(StartupClient);c.startup_timeout_seconds=timeout
        c.err=(root/'err').open('w');c.journal=(root/'rpc').open('w')
        code='import sys,json,time\nr=json.loads(sys.stdin.readline());time.sleep('+str(delay)+');print(json.dumps({"id":r["id"],"result":{"ready":True}}),flush=True);time.sleep(10)'
        c.p=subprocess.Popen([sys.executable,'-u','-c',code],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=c.err,start_new_session=True)
        c.selector=selectors.DefaultSelector();c.selector.register(c.p.stdout,selectors.EVENT_READ)
        c.buffer=b'';c.ident=0;c.calls=[];self.addCleanup(c.close)
        return c,root

    def test_single_slow_setup_reply_is_accepted_without_resending(self):
        c,root=self.client(.05,2);self.assertEqual(c.request('thread/start',{}),dict(ready=True))
        rows=[json.loads(x) for x in (root/'rpc').read_text().splitlines()]
        self.assertEqual(sum(r['direction']=='request' for r in rows),1)

    def test_setup_timeout_does_not_retry(self):
        c,root=self.client(.5,.02)
        with self.assertRaises(TimeoutError):c.request('initialize',{})
        rows=[json.loads(x) for x in (root/'rpc').read_text().splitlines()]
        self.assertEqual(len(rows),1);self.assertEqual(c.ident,1)

    def test_inference_start_uses_original_transport(self):
        c=StartupClient.__new__(StartupClient)
        with patch.object(Client,'request',return_value='original') as method:
            self.assertEqual(c.request('turn/start',dict(threadId='t')),'original')
            method.assert_called_once_with('turn/start',dict(threadId='t'))


if __name__=='__main__':unittest.main()
