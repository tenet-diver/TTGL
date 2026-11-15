"""Longer bounded pre-model RPC setup; no inference-call retry or prompt change.

The original20-second transport remains in force for turn/start and every other
method. Only initialize/thread/start can wait120seconds on their single request.
"""
import json
import os
import time
from mcp_memory_probe import Client


class StartupClient(Client):
    startup_timeout_seconds=120

    def request(self,method,params):
        if method not in ('initialize','thread/start'):
            return super().request(method,params)
        self.ident+=1;started=time.monotonic()
        self.record(dict(direction='request',id=self.ident,method=method,params=params))
        self.p.stdin.write((json.dumps(dict(jsonrpc='2.0',id=self.ident,method=method,params=params))+'\n').encode());self.p.stdin.flush()
        deadline=started+self.startup_timeout_seconds
        while time.monotonic()<deadline:
            if b'\n' not in self.buffer:
                if not self.selector.select(max(.001,deadline-time.monotonic())):break
                chunk=os.read(self.p.stdout.fileno(),65536)
                if not chunk:raise RuntimeError('Server exited')
                self.buffer+=chunk
                if len(self.buffer)>8*1024*1024:raise ValueError('Oversized MCP output')
                continue
            line,self.buffer=self.buffer.split(b'\n',1)
            if not line.strip():continue
            value=json.loads(line);self.record(dict(direction='response',message=value))
            if value.get('id')!=self.ident:continue
            if value.get('error'):raise RuntimeError('MCP error: '+json.dumps(value['error']))
            self.calls.append(dict(method=method,params=params,result=value['result'],seconds=time.monotonic()-started))
            return value['result']
        raise TimeoutError('Bounded pre-model startup request timed out; no retry')
