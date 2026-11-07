#!/usr/bin/env python3
"""Registered native compaction/counter diagnostic, never an efficiency result."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import time
from mcp_memory_probe import Client

REPO = Path(__file__).resolve().parents[3]
ROOT = REPO/'work/security/context-memory-20261107/native-compaction-canary-001'
PROTOCOL = REPO/'tools/usage-monitor/studies/native-compaction-protocol-001.json'


def write(path, value):
    with path.open('x') as stream:
        json.dump(value, stream, indent=2)
        stream.write('\n')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prepare():
    os.umask(0o077)
    ROOT.mkdir()
    (ROOT/'work').mkdir()
    (ROOT/'protocol.json').write_bytes(PROTOCOL.read_bytes())
    files = [Path(__file__), PROTOCOL, Path(__file__).with_name('mcp_memory_probe.py'),
             REPO/'tools/usage-monitor/observability/capture_proxy_compaction.py',
             Path(shutil.which('codex')).resolve()]
    write(ROOT/'manifest.json', dict(at=datetime.now(timezone.utc).isoformat(),
          sources={str(p):digest(p) for p in files}, model_calls=0))
    records = [dict(id=i, value=hashlib.sha256(('compact-fixture-'+str(i)).encode()).hexdigest()) for i in range(240)]
    seed = ('This is a context-compaction accounting diagnostic. Do not use tools, '
            'read files or call other agents. Retain the durable fact: cobalt has '
            'code R7Q2. The following synthetic records are background. Reply '
            'exactly READY.\n'+json.dumps(records))
    (ROOT/'seed.txt').write_text(seed)
    (ROOT/'followup.txt').write_text('Without tools, return only the durable cobalt code from earlier in this conversation.')
    write(ROOT/'prompt-hashes.json', {n:digest(ROOT/n) for n in ('seed.txt','followup.txt')})
    print('Prepared; zero model calls.')


def wait_turn(client, label, seconds=600):
    deadline = time.monotonic()+seconds
    while time.monotonic()<deadline:
        if b'\n' not in client.buffer:
            if not client.selector.select(min(1, max(.001, deadline-time.monotonic()))):
                continue
            chunk = os.read(client.p.stdout.fileno(), 65536)
            if not chunk:
                raise RuntimeError('App-server exited during '+label)
            client.buffer += chunk
            continue
        line, client.buffer = client.buffer.split(b'\n', 1)
        if not line.strip():
            continue
        row = json.loads(line)
        client.record(dict(direction='notification', phase=label, message=row))
        method = row.get('method')
        if method == 'error':
            raise RuntimeError('Native error during '+label+': '+json.dumps(row.get('params')))
        if method == 'turn/completed':
            status = row.get('params',{}).get('turn',{}).get('status')
            if status != 'completed':
                raise ValueError('Non-completed native turn: '+str(status))
            return row
    raise TimeoutError('Unknown native outcome at '+label+'; no automatic retry')


def run():
    manifest = json.loads((ROOT/'manifest.json').read_text())
    for path, expected in manifest['sources'].items():
        if digest(Path(path)) != expected:
            raise ValueError('Frozen source changed: '+path)
    for path, expected in json.loads((ROOT/'prompt-hashes.json').read_text()).items():
        if digest(ROOT/path) != expected:
            raise ValueError('Prompt changed')
    write(ROOT/'started.json', dict(pid=os.getpid(), at=datetime.now(timezone.utc).isoformat()))
    client = Client.__new__(Client)
    client.err = (ROOT/'stderr.log').open('x')
    runtime = str(Path(shutil.which('codex')).resolve())
    settings = {
        'mcp_servers.ttgl-analyst.enabled':False,
        'project_doc_max_bytes':0,
        'features.skip_host_skill_discovery':True,
        'features.enable_request_compression':False,
        'model_providers.ttgl_compaction.name':'TTGL compaction metering diagnostic',
        'model_providers.ttgl_compaction.base_url':'http://127.0.0.1:8330',
        'model_providers.ttgl_compaction.wire_api':'responses',
        'model_providers.ttgl_compaction.requires_openai_auth':True,
        'model_providers.ttgl_compaction.supports_websockets':False,
        'model_providers.ttgl_compaction.request_max_retries':0,
        'model_providers.ttgl_compaction.stream_max_retries':0,
        'default_permissions':'ttgl_compaction',
        'permissions.ttgl_compaction.filesystem':{':root':'deny', ':minimal':'read', str(ROOT/'work'):'read', runtime:'read'},
        'permissions.ttgl_compaction.network.enabled':False,
        'web_search':'disabled',
    }
    for feature in ('multi_agent','plugins','apps','browser_use','computer_use','image_generation','workspace_dependencies','view_image'):
        settings['features.'+feature]=False
    command = ['codex','app-server','--listen','stdio://']
    for key, value in settings.items():
        encoded = ('{'+','.join(json.dumps(k)+'='+json.dumps(v) for k,v in value.items())+'}') if isinstance(value,dict) else json.dumps(value)
        command += ['-c',key+'='+encoded]
    client.p = subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=client.err,start_new_session=True)
    client.selector = selectors.DefaultSelector()
    client.selector.register(client.p.stdout, selectors.EVENT_READ)
    client.buffer = b''
    client.ident = 0
    client.calls = []
    client.journal = (ROOT/'rpc.jsonl').open('x')
    try:
        client.request('initialize',dict(clientInfo=dict(name='ttgl_compaction_canary',version='1'),capabilities=dict(experimentalApi=True)))
        client.p.stdin.write(b'{"method":"initialized","params":{}}\n')
        client.p.stdin.flush()
        thread = client.request('thread/start',dict(cwd=str(ROOT/'work'),model='gpt-6.1-sol',modelProvider='ttgl_compaction',approvalPolicy='never'))
        sid = thread['thread']['id']
        write(ROOT/'thread.json',dict(session_id=sid))
        for phase in ('seed','compact','followup'):
            write(ROOT/(phase+'-started.json'),dict(at=datetime.now(timezone.utc).isoformat(),no_retry=True))
            if phase == 'compact':
                response = client.request('thread/compact/start',dict(threadId=sid))
            else:
                text = (ROOT/('seed.txt' if phase=='seed' else 'followup.txt')).read_text()
                response = client.request('turn/start',dict(threadId=sid,input=[dict(type='text',text=text,text_elements=[])]))
            write(ROOT/(phase+'-accepted.json'),response)
            complete = wait_turn(client,phase)
            write(ROOT/(phase+'-completed.json'),complete)
        write(ROOT/'complete.json',dict(session_id=sid,phases_completed=3,quality_and_usage_audit_pending=True))
        print('All three native phases completed; audit required.')
    except BaseException as error:
        write(ROOT/'stopped.json',dict(type=type(error).__name__,error=str(error),no_retry=True))
        raise
    finally:
        client.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','run'])
    globals()[parser.parse_args().action]()
