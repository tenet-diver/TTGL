#!/usr/bin/env python3
"""One explicitly registered model-facing archive/recovery mechanism diagnostic."""
from datetime import datetime,timezone
import argparse,hashlib,json,os
from pathlib import Path
import sys
HERE=Path(__file__).resolve().parent;REPO=HERE.parents[2]
sys.path.insert(0,str(HERE.parent/'observability'))
from longitudinal_memory_trial import run_process
from longmemeval_codex_trial import validate_native_completion

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--protocol',type=Path,required=True);args=ap.parse_args()
    protocol=args.protocol;p=json.loads(protocol.read_text())
    if p['id']!='archive-native-canary-005':raise ValueError('Fresh registered005 only; original001 through004 preserved')
    os.umask(0o077);root=REPO/'work/security/context-memory-20261107'/p['id'];root.mkdir(mode=0o700,exist_ok=True)
    if (root/'manifest.json').exists():raise ValueError('Never repeat a registered or started canary')
    (root/'protocol.json').write_bytes(protocol.read_bytes())
    files=[Path(__file__),HERE/'longitudinal_memory_trial.py',HERE/'longmemeval_codex_trial.py',HERE.parent/'observability/capture_proxy.py',HERE.parent/'observability/context_archive_policy.py',HERE.parent/'observability/exact_source_archive.py',HERE.parent/'observability/analyst_mcp.py',HERE.parent/'observability/analyst_cli.py']
    (root/'manifest.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),sources={str(f.relative_to(REPO)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files}),indent=2))
    work=root/'work';work.mkdir();cell=root/'reader';cell.mkdir();expected='copper-pulsar-5816'
    text='\n'.join(f'record-{i:04d}: '+(expected if i==73 else 'ordinary preserved diagnostic evidence '+str(i)+' '+'reference '*6) for i in range(160))+'\n';(work/'evidence.txt').write_text(text)
    prompt='This is an explicit archive transport diagnostic, not a general task. Use the shell to run exactly cat evidence.txt once. Then, if the observation is replaced with an archive handle, run the read-only TTGL CLI recovery command provided in that handle to recover the source (limit16000; paginate only if needed). Do not reread the file with another tool or command. Recover the exact value for record-0073 and output only that value. If no handle is observed, output UNAPPLIED. Use no other tools, network or installations.'
    command=['codex','exec','--ignore-user-config','--skip-git-repo-check','-C',str(work),'-m',p['model'],'-s','read-only','--json','--output-last-message',str(cell/'answer.txt'),'-']
    config={'features.incremental_tools':False,'mcp_servers.ttgl-analyst.enabled':False,'model_provider':'ttgl_archive_canary','model_reasoning_effort':'low','features.enable_request_compression':False,
        'model_providers.ttgl_archive_canary.name':'TTGL archive mechanism only','model_providers.ttgl_archive_canary.base_url':'http://127.0.0.1:8322/compress/reversible-shell-handles','model_providers.ttgl_archive_canary.wire_api':'responses','model_providers.ttgl_archive_canary.requires_openai_auth':True,'model_providers.ttgl_archive_canary.supports_websockets':False,
        'mcp_servers.ttgl_archive.required':True,'mcp_servers.ttgl_archive.startup_timeout_sec':30,'mcp_servers.ttgl_archive.enabled_tools':['read_compression_source'],'mcp_servers.ttgl_archive.command':sys.executable,'mcp_servers.ttgl_archive.args':[str(HERE.parent/'observability/analyst_mcp.py'),'--data',str(root/'data'),'--codex-root',str(root/'empty-native-root'),'--langfuse-url','http://localhost:3000','--capture-root',str(root/'captures')]}
    config={key:value for key,value in config.items() if not key.startswith('mcp_servers.') and key!='features.incremental_tools'}
    config.update({'model_providers.ttgl_archive_canary.request_max_retries':0,'model_providers.ttgl_archive_canary.stream_max_retries':0})
    for key,value in config.items():command[-1:-1]=['-c',key+'='+json.dumps(value)]
    (root/'prompt.txt').write_text(prompt)
    try:
        run_process(command,prompt,cell,p['timeout_seconds']);sid=validate_native_completion(cell)
        (root/'complete.json').write_text(json.dumps(dict(session_id=sid,answer_correct=(cell/'answer.txt').read_text().strip()==expected,note='Full transport/source/usage audit still required.'),indent=2))
    except BaseException as exc:
        (root/'stopped.json').write_text(json.dumps(dict(error=type(exc).__name__,message=str(exc),no_retries=True),indent=2));raise
if __name__=='__main__':main()
