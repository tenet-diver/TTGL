#!/usr/bin/env python3
"""Actual backend fidelity/peer-client check, separate from coding efficacy.

One service and two independent stdio MCP clients. No automatic invocation retry.
Native parent/child access is a separate gate; passing this probe does not imply it.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import time

from mcp_memory_probe import Client
from team_memory_service import KINDS, persist

HERE=Path(__file__).resolve().parent
GLOBAL=HERE.parents[2]/'work/security/context-memory-20261107'


def stdio_client(config, root, name):
    client=Client.__new__(Client)
    client.err=(root/(name+'-stderr.log')).open('x')
    client.p=subprocess.Popen([sys.executable,str(HERE/'team_memory_service.py'),'mcp','--config',str(config)],
        stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=client.err,start_new_session=True)
    client.selector=selectors.DefaultSelector();client.selector.register(client.p.stdout,selectors.EVENT_READ)
    client.buffer,client.ident,client.calls=b'',0,[];client.journal=(root/(name+'-rpc.jsonl')).open('x')
    # Existing tiny MCP client bounds requests to 20 seconds. Memory engines need
    # their real operation window, so this version uses the same framing below.
    return client


def request(client, method, params, timeout=900):
    client.ident+=1
    client.record(dict(direction='request',method=method,params=params,id=client.ident))
    client.p.stdin.write((json.dumps(dict(jsonrpc='2.0',id=client.ident,method=method,params=params))+'\n').encode());client.p.stdin.flush()
    deadline=time.monotonic()+timeout
    while time.monotonic()<deadline:
        if b'\n' not in client.buffer:
            if not client.selector.select(1):continue
            chunk=os.read(client.p.stdout.fileno(),65536)
            if not chunk:raise RuntimeError('MCP client closed; preserve attempt')
            client.buffer+=chunk;continue
        line,client.buffer=client.buffer.split(b'\n',1)
        row=json.loads(line);client.record(dict(direction='response',message=row))
        if row.get('id')!=client.ident:continue
        if row.get('error'):raise RuntimeError(str(row['error']))
        value=row['result']
        if value.get('isError'):raise RuntimeError(str(value))
        return value
    raise TimeoutError('One bounded MCP request timed out; never repeated')


def tool(client,name,args):
    result=request(client,'tools/call',dict(name=name,arguments=args))
    return json.loads(next(c['text'] for c in result['content'] if c['type']=='text'))


def start_service(root, kind):
    socket='/tmp/ttgl-memory-probe-'+hashlib.sha256(str(root).encode()).hexdigest()[:24]+'.sock'
    config=root/'service.json'
    persist(config,dict(kind=kind,root=str(root/'memory'),socket=socket,capture_port=8452,maintenance_call_cap=24))
    runtime=GLOBAL/('graphiti-runtime' if kind=='graphiti_luna' else 'memory-runtime')
    env={**os.environ,'PYTHONPATH':str(HERE)+':'+str(runtime), 'HF_HUB_OFFLINE':'1',
         'HF_HUB_DISABLE_TELEMETRY':'1','MEM0_TELEMETRY':'false','GRAPHITI_TELEMETRY_ENABLED':'false'}
    log=(root/'service-stderr.log').open('x')
    service=subprocess.Popen([sys.executable,'-S',str(HERE/'team_memory_service.py'),'serve','--config',str(config)],
        env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    deadline=time.monotonic()+60
    while time.monotonic()<deadline:
        if service.poll() is not None:
            log.close();raise RuntimeError('Backend initialization failed before readiness; inspect service log')
        if (root/'memory/ready.json').exists():return service,log,config
        time.sleep(.1)
    os.killpg(service.pid,signal.SIGTERM);service.wait(timeout=10);log.close()
    raise TimeoutError('Service readiness timeout; inspect before any continuation')


def probe(root, kind):
    root.mkdir(parents=True,exist_ok=False,mode=0o700)
    files=[Path(__file__),HERE/'team_memory_service.py',HERE/'team_memory_store.py',HERE/'team_memory_backends.py']
    persist(root/'protocol.json',dict(kind='synthetic backend+peer-client mechanism, not coding quality',backend=kind,
        sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},automatic_retries=0,
        expected='Exact project/command, reciprocal client visibility and assignment isolation'))
    frozen=root/'frozen-source';frozen.mkdir()
    for path in files:
        (frozen/path.name).write_bytes(path.read_bytes())
    service=log=None;clients=[]
    try:
        service,log,config=start_service(root,kind)
        for name in ('parent','peer'):
            client=stdio_client(config,root,name);clients.append(client)
            request(client,'initialize',dict(protocolVersion='2025-06-18',capabilities={},clientInfo=dict(name='ttgl-memory-probe-'+name,version='1')))
            names={t['name'] for t in request(client,'tools/list',{})['tools']}
            if names!={'publish_finding','search_memory','read_record','coverage'}:
                raise ValueError('Tool-awareness contract failed')
        first=tool(clients[0],'publish_finding',dict(author='parent',text='The cedar repository documents the exact check command python -m unittest. This is a documentation observation; the command was not executed.',source='synthetic:cedar/docs/checks.md:4'))
        second=tool(clients[1],'publish_finding',dict(author='peer',text='The cedar parser lives in cedar/config.py. Its behavior is unverified; do not treat this as a passed test.',source='synthetic:cedar/docs/layout.md:2'))
        hits=tool(clients[1],'search_memory',dict(query='cedar public check command',limit=8))
        peer=tool(clients[0],'search_memory',dict(query='cedar parser configuration location',limit=8))
        original=tool(clients[1],'read_record',dict(id=first['record_id']))
        raw=json.dumps(hits,ensure_ascii=False).lower()
        passed='python -m unittest' in raw and 'cedar' in raw and 'cedar/config.py' in json.dumps(peer) and original['source'].startswith('synthetic:')
        persist(root/'result.json',dict(passed=passed,hits=hits,peer_hits=peer,original=original,
            published_ids=[first['record_id'],second['record_id']],scope='Two real stdio clients over one actual engine; native agent inheritance and cross-assignment isolation tested separately',coding_trials=0))
        print(json.dumps(dict(backend=kind,passed=passed)),flush=True)
        if not passed:raise ValueError('Registered exact fidelity gate failed; preserve, do not retry')
    except BaseException as error:
        persist(root/'stopped.json',dict(error=repr(error),automatic_retries=0))
        raise
    finally:
        for client in clients:client.close()
        if service is not None and service.poll() is None:
            os.killpg(service.pid,signal.SIGTERM);service.wait(timeout=15)
        if log is not None:log.close()


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root',type=Path,required=True)
    parser.add_argument('--kind',choices=KINDS,required=True)
    args=parser.parse_args();os.umask(0o077);probe(args.root.resolve(),args.kind)
