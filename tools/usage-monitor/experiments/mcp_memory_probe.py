#!/usr/bin/env python3
"""Bounded no-inference contract check of the reviewed maintained memory server."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import time


def tool_result(value):
    if value.get('isError'):raise RuntimeError('Memory tool rejected call')
    if 'structuredContent' in value:return value['structuredContent']
    documents=[]
    for block in value.get('content',[]):
        if block.get('type')!='text':continue
        try:documents.append(json.loads(block['text']))
        except ValueError:pass  # Notice remains verbatim in the private RPC receipt.
    if len(documents)!=1:raise ValueError('Expected exactly one structured JSON payload')
    return documents[0]


class Client:
    def __init__(self,entry,memory,log):
        env=os.environ.copy();env['MEMORY_FILE_PATH']=str(memory.resolve())
        self.err=log.open('x');self.p=subprocess.Popen(['node',str(entry.resolve())],env=env,
            stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=self.err,start_new_session=True)
        self.selector=selectors.DefaultSelector();self.selector.register(self.p.stdout,selectors.EVENT_READ)
        self.buffer=b'';self.ident=0;self.calls=[]
        self.journal=log.with_name(log.stem+'-rpc.jsonl').open('x')

    def record(self,value):
        self.journal.write(json.dumps(value)+'\n');self.journal.flush();os.fsync(self.journal.fileno())

    def request(self,method,params):
        self.ident+=1;started=time.monotonic()
        self.record(dict(direction='request',id=self.ident,method=method,params=params))
        self.p.stdin.write((json.dumps(dict(jsonrpc='2.0',id=self.ident,method=method,params=params))+'\n').encode());self.p.stdin.flush()
        deadline=started+20
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
            value=json.loads(line)
            self.record(dict(direction='response',message=value))
            if value.get('id')!=self.ident:continue
            if value.get('error'):raise RuntimeError('MCP error: '+json.dumps(value['error']))
            self.calls.append(dict(method=method,params=params,result=value['result'],seconds=time.monotonic()-started))
            return value['result']
        raise TimeoutError('Bounded MCP request timed out')

    def tool(self,name,args):
        value=self.request('tools/call',dict(name=name,arguments=args))
        return tool_result(value)

    def close(self):
        try:os.killpg(self.p.pid,signal.SIGTERM)
        except ProcessLookupError:pass
        try:self.p.wait(timeout=5)
        except subprocess.TimeoutExpired:os.killpg(self.p.pid,signal.SIGKILL);self.p.wait()
        self.selector.close();self.p.stdin.close();self.p.stdout.close();self.err.close();self.journal.close()


def probe(review,out):
    os.umask(0o077);out.mkdir(parents=True,exist_ok=False,mode=0o700)
    receipt=json.loads((review/'pre-install-receipt.json').read_text())
    if receipt['known_findings']:raise ValueError('Known findings block execution')
    entry=review/'node_modules/@modelcontextprotocol/server-memory/dist/index.js';memory=out/'knowledge.jsonl'
    manifest=dict(at=datetime.now(timezone.utc).isoformat(),entry_sha256=hashlib.sha256(entry.read_bytes()).hexdigest(),
        lock_sha256=hashlib.sha256((review/'package-lock.json').read_bytes()).hexdigest(),
        security_receipt_sha256=hashlib.sha256((review/'pre-install-receipt.json').read_bytes()).hexdigest(),model_calls=0,
        scope='Synthetic local server protocol/persistence check only; not an agent efficacy or isolation/security benchmark.')
    (out/'manifest.json').write_text(json.dumps(manifest,indent=2))
    checks={};all_calls=[]
    for phase in ('write','reopen'):
        client=Client(entry,memory,out/(phase+'-stderr.log'))
        try:
            client.request('initialize',dict(protocolVersion='2025-06-18',capabilities={},clientInfo=dict(name='ttgl-memory-probe',version='1')))
            client.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');client.p.stdin.flush()
            tools=client.request('tools/list',{})['tools'];names={t['name'] for t in tools}
            checks[phase+'_tools_available']={'create_entities','create_relations','search_nodes','read_graph','add_observations'}<=names
            if phase=='write':
                entities=[dict(name='ledger',entityType='project',observations=['Conflicting duplicate identifiers raise ValueError.']),dict(name='graph',entityType='project',observations=['Validate all cycles before planning affected nodes.'])]
                client.tool('create_entities',dict(entities=entities));client.tool('create_entities',dict(entities=entities))
                client.tool('create_relations',{'relations':[{'from':'ledger','to':'graph','relationType':'shares_verification'}]})
                client.tool('add_observations',dict(observations=[dict(entityName='ledger',contents=['Validate future records before time filtering.'])]))
                hit=client.tool('search_nodes',dict(query='ledger'))
                checks['search_finds_correct_entity']=any(e['name']=='ledger' for e in hit['entities'])
                graph=client.tool('read_graph',{})
                checks['idempotent_entity_creation']=len(graph['entities'])==2
                checks['relation_stored']=len(graph['relations'])==1
                checks['observations_preserved']=len(next(e for e in graph['entities'] if e['name']=='ledger')['observations'])==2
                (out/'expected-graph.json').write_text(json.dumps(graph,sort_keys=True))
            else:
                graph=client.tool('read_graph',{})
                checks['persisted_across_process_restart']=graph==json.loads((out/'expected-graph.json').read_text())
            all_calls+=client.calls
        finally:client.close()
    result=dict(manifest=manifest,checks=checks,passed=all(checks.values()),model_calls=0,requests=all_calls,
        memory_sha256=hashlib.sha256(memory.read_bytes()).hexdigest(),cash_cost=None,
        note='Actual maintained server, explicit private file, two owned stdio processes. No Codex/plugin/global config change. No model, embedding or efficacy trial.')
    (out/'results.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(dict(passed=result['passed'],checks=checks,model_calls=0)))
    if not result['passed']:raise RuntimeError('Memory server contract check failed')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--review',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();probe(a.review,a.output)
