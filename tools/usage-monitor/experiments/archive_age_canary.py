#!/usr/bin/env python3
"""Prepare a matched raw/aging application gate; no automatic model retries."""
import argparse,hashlib,json,os
from pathlib import Path
from datetime import datetime,timezone
from longmemeval_codex_trial import native_command,run_process
from native_jsonl import validate_native_completion
from cost_context_study import REPO
HERE=Path(__file__).resolve().parent;ROOT=REPO/'work/security/context-memory-20261107/archive-age-canary-001'
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def prepare():
    os.umask(0o077);ROOT.mkdir(mode=0o700);p=HERE.parent/'studies/archive-age-canary-protocol-001.json';(ROOT/'protocol.json').write_bytes(p.read_bytes());value='indigo-nebula-4173';text='\n'.join(f'record-{i:04d}: '+(value if i==73 else 'controlled source record '+str(i)+' '+'reference '*8) for i in range(240))+'\n'
    for arm in ('off','older-shell-mask'):
        work=ROOT/arm/'work';work.mkdir(parents=True);(work/'evidence.txt').write_text(text)
    files=[Path(__file__),HERE/'native_jsonl.py',HERE/'longmemeval_codex_trial.py',HERE/'longitudinal_memory_trial.py',HERE.parent/'observability/capture_proxy.py',HERE.parent/'observability/context_archive_policy.py',HERE.parent/'observability/exact_source_archive.py',HERE.parent/'observability/analyst_cli.py',HERE.parent/'observability/analyst_mcp.py']
    write(ROOT/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),sources={str(f.relative_to(REPO)):hashlib.sha256(f.read_bytes()).hexdigest() for f in files},fixture_sha256=hashlib.sha256(text.encode()).hexdigest(),protocol_sha256=hashlib.sha256(p.read_bytes()).hexdigest(),model_calls=0));print('Prepared raw/older matched mechanism fixture; no model call.')
def run():
    p=json.loads((ROOT/'protocol.json').read_text());m=json.loads((ROOT/'manifest.json').read_text())
    if any(hashlib.sha256((REPO/f).read_bytes()).hexdigest()!=h for f,h in m['sources'].items()):raise ValueError('Frozen source changed')
    with (ROOT/'started.json').open('x') as f:json.dump(dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid()),f)
    prompt='This is an explicit history-aging transport diagnostic. First run cat evidence.txt once, requesting enough output to read the file. Next perform five distinct small shell tool invocations, each printf AGING_1, then AGING_2, through AGING_5; wait for each result before the next invocation, do not combine them into one command. After all five, if an archive handle is present, use exactly one supplied read-only TTGL CLI recovery command to read the original source. Do not reread evidence.txt with another command. Finally output only the exact value for record-0073. No other tools, network or installations.'
    try:
        for arm in p['conditions']:
            cell=ROOT/arm;work=cell/'work';(cell/'prompt.txt').write_text(prompt);base='http://127.0.0.1:8323'+('/compress/older-shell-mask' if arm!='off' else '')
            command=native_command(work,cell,p['model']);config={'model_provider':'ttgl_age_canary','features.enable_request_compression':False,'model_providers.ttgl_age_canary.name':'TTGL matched age mechanism only','model_providers.ttgl_age_canary.base_url':base,'model_providers.ttgl_age_canary.wire_api':'responses','model_providers.ttgl_age_canary.requires_openai_auth':True,'model_providers.ttgl_age_canary.supports_websockets':False,'model_providers.ttgl_age_canary.request_max_retries':0,'model_providers.ttgl_age_canary.stream_max_retries':0}
            for k,v in config.items():command[-1:-1]=['-c',k+'='+json.dumps(v)]
            run_process(command,prompt,cell,p['timeout_seconds']);sid=validate_native_completion(cell);write(cell/'mechanism-completion.json',dict(session_id=sid,answer_correct=(cell/'answer.txt').read_text().strip()=='indigo-nebula-4173'));print(arm,'completed',flush=True)
        write(ROOT/'complete.json',dict(model_processes=2,at=datetime.now(timezone.utc).isoformat()))
    except BaseException as e:write(ROOT/'stopped.json',dict(error=type(e).__name__,message=str(e),no_retry=True));raise
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run']);a=ap.parse_args();globals()[a.action]()
