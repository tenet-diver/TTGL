#!/usr/bin/env python3
"""Actual native parent/child memory awareness and reciprocal read diagnostic.

Separate fresh fixture from coding assignments. No automatic retries. The model
does the delegation; the operator verifies tool calls and witness files afterward.
"""
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import selectors
import signal
import shutil
import subprocess
import time

from codex_team_probe import prepare, sandbox_check, save, sha
from codex_team_memory_extension import guidance, observe
from mcp_memory_probe import Client
from probe_team_memory_backends import start_service
from team_memory_service import KINDS, TOOLS
from tokeneconomizer_native_hooks import toml

HERE=Path(__file__).resolve().parent


def probe(root,kind):
    prepare(root,2)
    config=json.loads((root/'config.json').read_text())
    # Each mechanism uses its own service and namespace; never reuse the earlier
    # backend probe's memories or maintenance call IDs.
    service_root=root/'broker';service_root.mkdir()
    service=log=None
    try:
        service,log,service_config=start_service(service_root,kind)
        config.update({'model_provider':'ttgl-study',
            'model_providers.ttgl-study.name':'Native team memory diagnostic',
            'model_providers.ttgl-study.base_url':'http://127.0.0.1:8452/backend-api/codex',
            'model_providers.ttgl-study.wire_api':'responses',
            'model_providers.ttgl-study.requires_openai_auth':True,
            'model_providers.ttgl-study.request_max_retries':0,
            'model_providers.ttgl-study.stream_max_retries':0,
            'model_providers.ttgl-study.supports_websockets':False,
            'mcp_servers.team_memory.command':shutil.which('python3'),
            'mcp_servers.team_memory.args':[str(HERE/'team_memory_service.py'),'mcp','--config',str(service_config)],
            'mcp_servers.team_memory.required':True,'mcp_servers.team_memory.tool_timeout_sec':900,
            'developer_instructions':guidance(kind)})
        for tool in TOOLS:config['mcp_servers.team_memory.tools.'+tool['name']+'.approval_mode']='approve'
        (root/'config.json').write_text(json.dumps(config,indent=2))
        prompt=('This is a synthetic shared-memory mechanism check, not a coding benchmark. '
            'Read public.txt. Publish one finding to team_memory with author parent, its exact contents and source public.txt. '
            'Spawn exactly one default native child. Tell the child the available memory tool names and shared scope, but do not send it the file contents or your record ID. '
            'The child must search_memory for the parent public.txt finding, read_record using its returned ID, then write only the exact original file contents plus newline into child.txt. '
            'The child must publish its own finding with author child, saying it retrieved the parent record and reporting the exact token. '
            'Wait for the child. Search shared memory for its child finding and read its original record. Independently compare child.txt and public.txt. '
            'Use actual tools; do not substitute delegation text for memory retrieval. Report tool names, outcomes and gaps. '
            +guidance(kind))
        (root/'prompt.txt').write_text(prompt)
        manifest=json.loads((root/'manifest.json').read_text());manifest.update(kind='native_reciprocal_memory_mechanism_not_benchmark',memory_backend=kind)
        for p in [root/'config.json',root/'prompt.txt',Path(__file__),HERE/'team_memory_service.py',HERE/'team_memory_backends.py',HERE/'team_memory_store.py']:
            manifest['sources'][str(p.resolve())]=sha(p)
        (root/'manifest.json').write_text(json.dumps(manifest,indent=2))
        frozen=root/'frozen-source';frozen.mkdir()
        for path in [Path(__file__),HERE/'team_memory_service.py',HERE/'team_memory_backends.py',HERE/'team_memory_store.py']:
            (frozen/path.name).write_bytes(path.read_bytes())
        sandbox_check(root)
        for p,h in manifest['sources'].items():
            if sha(p)!=h:raise ValueError('Frozen probe source changed')
        save(root/'started.json',dict(at=datetime.now(timezone.utc).isoformat(),automatic_retries=0))
        auth=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))/'auth.json'
        shutil.copyfile(auth,root/'home/auth.json');(root/'home/auth.json').chmod(0o600)
        command=['codex','app-server','--listen','stdio://']
        for key,value in config.items():command+=['-c',key+'='+toml(value)]
        c=Client.__new__(Client);c.err=(root/'stderr.log').open('x')
        c.p=subprocess.Popen(command,env={**os.environ,'CODEX_HOME':str(root/'home')},stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=c.err,start_new_session=True)
        c.selector=selectors.DefaultSelector();c.selector.register(c.p.stdout,selectors.EVENT_READ)
        c.buffer,c.ident,c.calls=b'',0,[];c.journal=(root/'rpc.jsonl').open('x')
        start=time.perf_counter()
        try:
            c.request('initialize',dict(clientInfo=dict(name='ttgl_reciprocal_memory_probe',version='1'),capabilities=dict(experimentalApi=True)))
            c.p.stdin.write(b'{"method":"initialized","params":{}}\n');c.p.stdin.flush()
            thread=c.request('thread/start',dict(cwd=str(root/'actor'),model='gpt-6.1-sol',modelProvider='ttgl-study',approvalPolicy='never',ephemeral=False))
            sid=thread['thread']['id'];save(root/'thread.json',thread)
            accepted=c.request('turn/start',dict(threadId=sid,input=[dict(type='text',text=prompt,text_elements=[])]));save(root/'accepted.json',accepted)
            deadline=time.monotonic()+900
            while time.monotonic()<deadline:
                if b'\n' not in c.buffer:
                    if not c.selector.select(1):continue
                    chunk=os.read(c.p.stdout.fileno(),65536)
                    if not chunk:raise RuntimeError('Native app-server exited; no retry')
                    c.buffer+=chunk;continue
                line,c.buffer=c.buffer.split(b'\n',1)
                if not line.strip():continue
                row=json.loads(line);c.record(dict(direction='notification',message=row));p=row.get('params',{})
                if row.get('method')=='turn/completed' and p.get('threadId')==sid:
                    save(root/'completed.json',dict(parent_thread_id=sid,turn=p['turn'],wall_seconds=time.perf_counter()-start));break
            else:raise TimeoutError('Native awareness probe timed out; preserve')
        finally:c.close()
        events=[json.loads(line).get('message',{}) for line in (root/'rpc.jsonl').read_text().splitlines()]
        tools={};retrievals={}
        for event in events:
            if event.get('method')!='item/completed':continue
            p=event.get('params',{});item=p.get('item',{})
            if item.get('type')=='mcpToolCall' and item.get('server')=='team_memory':
                tools.setdefault(p['threadId'],[]).append(item.get('tool'))
                if item.get('tool') in ('read_record','search_memory'):
                    retrievals.setdefault(p['threadId'],[]).append(item.get('result'))
        nonce=(root/'actor/public.txt').read_text().strip()
        peers={k:v for k,v in tools.items() if k!=sid}
        exact=(root/'actor/child.txt').exists() and (root/'actor/child.txt').read_text()==nonce+'\n'
        reciprocal=len(peers)==1 and all({'publish_finding','search_memory','read_record'}<=set(v) for v in tools.values())
        exposed=len(retrievals)==2 and all(nonce in json.dumps(v) for v in retrievals.values())
        value=dict(passed=exact and reciprocal and exposed,parent_thread=sid,tools_by_thread=tools,
                   exact_witness=exact,reciprocal_tools=reciprocal,exact_exposure=exposed,
                   scope='Actual native parent+child on synthetic fixture; not coding efficacy or causal knowledge benefit',automatic_retries=0)
        save(root/'result.json',value);print(json.dumps(value),flush=True)
        if not value['passed']:raise ValueError('Native awareness/retrieval gate failed; do not repeat')
    except BaseException as error:
        save(root/'probe-stopped.json',dict(error=repr(error),automatic_retries=0));raise
    finally:
        if service is not None and service.poll() is None:
            os.killpg(service.pid,signal.SIGTERM);service.wait(timeout=15)
        if log is not None:log.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--kind',choices=KINDS,required=True)
    a=p.parse_args();os.umask(0o077);probe(a.root.resolve(),a.kind)
