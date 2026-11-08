#!/usr/bin/env python3
"""One registered native full-capture/automatic-compaction mechanism canary."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
from longmemeval_codex_trial import native_command,run_process
from native_jsonl import validate_native_completion
from cost_context_study import REPO

HERE=Path(__file__).resolve().parent
ROOT=REPO/'work/security/context-memory-20261107/native-long-capture-canary-001'
WORK=ROOT/'work'
PROTOCOL=HERE.parent/'studies/native-long-capture-protocol-001.json'


def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def prepare():
    os.umask(0o077)
    WORK.mkdir(parents=True)
    marker='LAST_MARKER_'+secrets.token_hex(16)
    text=''.join('row-'+str(i).zfill(5)+':'+hashlib.sha256(('long-capture-'+str(i)).encode()).hexdigest()+'\n' for i in range(4200))
    text+='unicode-boundary\u2028fixture\n'+marker+'\n'
    (WORK/'fixture.txt').write_text(text)
    write(ROOT/'expected.json',dict(marker=marker,fixture_bytes=len(text.encode()),fixture_sha256=digest(WORK/'fixture.txt')))
    (ROOT/'protocol.json').write_bytes(PROTOCOL.read_bytes())
    sources=[Path(__file__),HERE/'native_jsonl.py',HERE/'longmemeval_codex_trial.py',HERE/'longitudinal_memory_trial.py',
        HERE.parent/'observability/capture_proxy_longhorizon.py',HERE.parent/'observability/capture_objects.py',
        HERE.parent/'observability/capture_proxy_compaction.py',HERE.parent/'langfuse/live_export.py',PROTOCOL,
        Path(shutil.which('codex')).resolve()]
    write(ROOT/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),sources={str(p):digest(p) for p in sources},
          runtime_path=str(Path(shutil.which('codex')).resolve()),fixture_sha256=digest(WORK/'fixture.txt'),expected_sha256=digest(ROOT/'expected.json'),model_calls=0))
    print('Prepared315k-character synthetic fixture; no model calls.')


def frozen():
    m=json.loads((ROOT/'manifest.json').read_text())
    if str(Path(shutil.which('codex')).resolve())!=m['runtime_path']:raise ValueError('Pinned runtime path changed')
    if any(digest(Path(p))!=h for p,h in m['sources'].items()) or digest(WORK/'fixture.txt')!=m['fixture_sha256'] or digest(ROOT/'expected.json')!=m['expected_sha256']:
        raise ValueError('Frozen source/input changed')


def run():
    frozen()
    cell=ROOT/'reader';cell.mkdir()
    prompt=('This is an authorized native capture and automatic-compaction mechanism diagnostic with synthetic data. '
            'Read the entire fixture.txt with exactly one cat command, requesting at least200000 output tokens '
            'so the complete file is returned. Do not tail, filter or reread it. Then run a separate shell printf '
            'command producing CANARY_STEP_DONE. Finally reply with only the exact LAST_MARKER line from the file. '
            'No other files, edits, network, downloads, other agents or models. There is no scored benchmark task here.')
    (cell/'prompt.txt').write_text(prompt)
    command=native_command(WORK,cell,'gpt-6.1-sol')
    i=command.index('-s');del command[i:i+2]
    command[-1:-1]=['--ignore-rules']
    for feature in ('multi_agent','plugins','apps','browser_use','computer_use','image_generation','workspace_dependencies','view_image'):
        command[-1:-1]=['--disable',feature]
    settings={
        'project_doc_max_bytes':0,'features.skip_host_skill_discovery':True,'features.enable_request_compression':False,
        'tool_output_token_limit':200000,'model_auto_compact_token_limit':50000,
        'default_permissions':'ttgl_long_capture',
        'permissions.ttgl_long_capture.filesystem':{':root':'deny',':minimal':'read',str(WORK):'read',str(Path(shutil.which('codex')).resolve()):'read'},
        'permissions.ttgl_long_capture.network.enabled':False,'web_search':'disabled',
        'model_provider':'ttgl_long_capture','model_providers.ttgl_long_capture.name':'TTGL long capture canary',
        'model_providers.ttgl_long_capture.base_url':'http://127.0.0.1:8336',
        'model_providers.ttgl_long_capture.wire_api':'responses','model_providers.ttgl_long_capture.requires_openai_auth':True,
        'model_providers.ttgl_long_capture.supports_websockets':False,'model_providers.ttgl_long_capture.request_max_retries':0,
        'model_providers.ttgl_long_capture.stream_max_retries':0,
    }
    for key,value in settings.items():
        encoded='{'+','.join(json.dumps(k)+'='+json.dumps(v) for k,v in value.items())+'}' if isinstance(value,dict) else json.dumps(value)
        command[-1:-1]=['-c',key+'='+encoded]
    write(ROOT/'started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),maximum_cli_processes=1))
    try:
        run_process(command,prompt,cell,900)
        sid=validate_native_completion(cell)
        marker=json.loads((ROOT/'expected.json').read_text())['marker']
        write(ROOT/'complete.json',dict(session_id=sid,answer_exact=(cell/'answer.txt').read_text().strip()==marker,
                                      storage_compaction_and_usage_audit_pending=True,model_processes=1))
        print('Native canary completed; full-string/compaction/counter audit required.')
    except BaseException as error:
        write(ROOT/'stopped.json',dict(type=type(error).__name__,error=str(error),no_retry=True))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','run'])
    globals()[parser.parse_args().action]()
