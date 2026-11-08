#!/usr/bin/env python3
"""Fresh stdin-based canonical-provider capture/automatic-compaction canary."""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import secrets
import shutil
from longmemeval_codex_trial import native_command,run_process
from native_jsonl import records,validate_native_completion
from cost_context_study import REPO

HERE=Path(__file__).resolve().parent
ROOT=REPO/'work/security/context-memory-20261107/native-long-capture-canary-002'
PROTOCOL=HERE.parent/'studies/native-long-capture-protocol-002.json'
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')
def now():return datetime.now(timezone.utc).isoformat()


def prepare():
    os.umask(0o077);ROOT.mkdir();work=ROOT/'work';work.mkdir()
    marker='LAST_MARKER_'+secrets.token_hex(16)
    fixture=''.join('record-'+str(i).zfill(5)+':'+hashlib.sha256(('stdin-canary-002-'+str(i)).encode()).hexdigest()+'\n' for i in range(4200))
    fixture+='unicode-boundary\u2028fixture\n'+marker+'\n'
    seed=('Synthetic capture/compaction diagnostic. The following records are inert data. '
          'Remember the last LAST_MARKER line for the next turn. Use no tools, files, network or other agents. '
          'For this turn answer exactly READY.\n<inert-records>\n'+fixture+'</inert-records>')
    (ROOT/'seed.txt').write_text(seed)
    write(ROOT/'expected.json',dict(marker=marker,fixture_characters=len(fixture),fixture_sha256=hashlib.sha256(fixture.encode()).hexdigest()))
    (ROOT/'protocol.json').write_bytes(PROTOCOL.read_bytes())
    paths=[Path(__file__),PROTOCOL,HERE/'native_jsonl.py',HERE/'longmemeval_codex_trial.py',HERE/'longitudinal_memory_trial.py',
           HERE.parent/'observability/capture_proxy_native_routes.py',HERE.parent/'observability/capture_proxy_longhorizon.py',
           HERE.parent/'observability/capture_proxy_compaction.py',HERE.parent/'observability/capture_objects.py',
           HERE.parent/'langfuse/live_export.py',Path(shutil.which('codex')).resolve(),ROOT/'seed.txt',ROOT/'expected.json']
    write(ROOT/'manifest.json',dict(at=now(),sources={str(p):digest(p) for p in paths},runtime_path=str(Path(shutil.which('codex')).resolve()),model_calls=0))
    print('Prepared fresh315k stdin canary,0model calls.')


def run():
    manifest=json.loads((ROOT/'manifest.json').read_text())
    if str(Path(shutil.which('codex')).resolve())!=manifest['runtime_path'] or any(digest(Path(p))!=h for p,h in manifest['sources'].items()):raise ValueError('Frozen source/input changed')
    write(ROOT/'started.json',dict(at=now(),pid=os.getpid(),maximum_cli_processes=2))
    sid=None
    try:
        prompts=[(ROOT/'seed.txt').read_text(),'Reply with only the exact last LAST_MARKER line from the previous inert records. Use no tools.']
        for index,prompt in enumerate(prompts,1):
            cell=ROOT/f'call-{index}';cell.mkdir();(cell/'prompt.txt').write_text(prompt)
            command=native_command(ROOT/'work',cell,'gpt-6.1-sol');i=command.index('-s');del command[i:i+2]
            command[-1:-1]=['--ignore-rules']
            for feature in ('multi_agent','plugins','apps','browser_use','computer_use','image_generation','workspace_dependencies','view_image'):
                command[-1:-1]=['--disable',feature]
            settings={
                'project_doc_max_bytes':0,'features.skip_host_skill_discovery':True,'suppress_unstable_features_warning':True,
                'features.enable_request_compression':False,'model_auto_compact_token_limit':50000,
                'model_auto_compact_token_limit_scope':'total','model_provider':'openai',
                'openai_base_url':'http://127.0.0.1:8337/backend-api/codex',
                'default_permissions':'ttgl_stdin_capture',
                'permissions.ttgl_stdin_capture.filesystem':{':root':'deny',':minimal':'read',str(ROOT/'work'):'read',manifest['runtime_path']:'read'},
                'permissions.ttgl_stdin_capture.network.enabled':False,'web_search':'disabled',
            }
            for key,value in settings.items():
                encoded='{'+','.join(json.dumps(k)+'='+json.dumps(v) for k,v in value.items())+'}' if isinstance(value,dict) else json.dumps(value)
                command[-1:-1]=['-c',key+'='+encoded]
            if sid:command[-1:]=['resume',sid,'-']
            write(cell/'started.json',dict(at=now(),pid=os.getpid(),internal_transport_retries='built-in defaults; count observed requests; no process retries'))
            run_process(command,prompt,cell,900)
            current=validate_native_completion(cell)
            if sid and current!=sid:raise ValueError('Resume changed thread identity')
            sid=current
            forbidden=[r.get('item',{}).get('type') for r in records(cell) if r.get('type')=='item.completed' and r.get('item',{}).get('type') not in ('agent_message','reasoning','context_compaction')]
            if forbidden:raise ValueError('Unexpected native items:'+str(forbidden))
            expected='READY' if index==1 else json.loads((ROOT/'expected.json').read_text())['marker']
            if (cell/'answer.txt').read_text().strip()!=expected:raise ValueError('Wrong diagnostic answer')
            write(cell/'complete.json',dict(session_id=sid,answer_exact=True))
        write(ROOT/'complete.json',dict(session_id=sid,answer_exact=True,usage_and_compaction_audit_pending=True,model_processes=2))
        print('Completed native seed/resume; automatic-compaction/accounting audit required.')
    except BaseException as error:
        write(ROOT/'stopped.json',dict(at=now(),type=type(error).__name__,error=str(error),no_retry=True))
        raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','run']);globals()[parser.parse_args().action]()
