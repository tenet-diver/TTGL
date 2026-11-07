#!/usr/bin/env python3
"""Use reviewed stdlib Exercism tests; supply only missing native experiment glue."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
from longmemeval_codex_trial import native_command,run_process
from native_jsonl import validate_native_completion
from cost_context_study import REPO
HERE=Path(__file__).resolve().parent;GLOBAL=REPO/'work/security/context-memory-20261107';ROOT=GLOBAL/'coding-context-transfer-001';SOURCE=GLOBAL/'code-transfer-source-review-001'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
def prepare():
    controls=json.loads((SOURCE/'controls.json').read_text());receipt=json.loads((SOURCE/'pre-execution-receipt.json').read_text())
    if not controls['all_controls_pass'] or receipt['known_findings']:raise ValueError('Source/security controls fail')
    os.umask(0o077);ROOT.mkdir();protocol=HERE.parent/'studies/coding-context-transfer-protocol-001.json';(ROOT/'protocol.json').write_bytes(protocol.read_bytes());p=json.loads(protocol.read_text());inputs={}
    for family in p['families']:
        stem=family.replace('-','_');src=SOURCE/'source/exercises/practice'/family
        for arm in p['conditions']:
            work=ROOT/family/arm/'work';work.mkdir(parents=True)
            for name,original in [(stem+'.py',src/(stem+'.py')),(stem+'_test.py',src/(stem+'_test.py')),('instructions.md',src/'.docs/instructions.md'),('LICENSE',SOURCE/'source/LICENSE')]:
                dest=work/name;shutil.copyfile(original,dest);inputs[str(dest.relative_to(ROOT))]=digest(dest)
    files=[Path(__file__),HERE/'native_jsonl.py',HERE/'longmemeval_codex_trial.py',HERE/'longitudinal_memory_trial.py',HERE.parent/'observability/capture_proxy.py',HERE.parent/'observability/context_archive_policy.py',HERE.parent/'observability/exact_source_archive.py',HERE.parent/'observability/analyst_cli.py',HERE.parent/'studies/context-memory-pricing-20261107.json']
    write(ROOT/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),sources={str(f.relative_to(REPO)):digest(f) for f in files},inputs=inputs,protocol_sha256=digest(protocol),source_control_sha256=digest(SOURCE/'controls.json'),model_calls=0));print('Prepared12 fresh coding workspaces; no models invoked.')
def frozen():
    m=json.loads((ROOT/'manifest.json').read_text())
    if digest(ROOT/'protocol.json')!=m['protocol_sha256']:raise ValueError('Protocol changed')
    if any(digest(REPO/f)!=h for f,h in m['sources'].items()):raise ValueError('Generation source changed')
    return m
def run():
    m=frozen();p=json.loads((ROOT/'protocol.json').read_text())
    if any(digest(ROOT/f)!=h for f,h in m['inputs'].items()):raise ValueError('Prepared inputs changed')
    with (ROOT/'started.json').open('x') as out:json.dump(dict(pid=os.getpid(),at=datetime.now(timezone.utc).isoformat()),out)
    cells=[]
    try:
        for index,family in enumerate(p['families']):
            arms=p['conditions'][index:]+p['conditions'][:index]
            for arm in arms:
                frozen();cell=ROOT/family/arm;work=cell/'work';prompt='Implement the Python module to meet instructions.md and the existing tests. Inspect relevant files, make a correct general implementation, and run the full provided unittest suite before finishing. Do not modify the provided tests, instructions or license. Work only in this task directory; no network, downloads, package installation or outside solutions. If a TTGL archived observation appears and omitted detail is needed, recover exact source with its supplied read-only command. Verify your final result and briefly report checks and any uncertainty.';(cell/'prompt.txt').write_text(prompt)
                command=native_command(work,cell,p['model']);command[command.index('read-only')]='workspace-write';base='http://127.0.0.1:8324'+('' if arm=='off' else '/compress/'+arm)
                config={'model_provider':'ttgl_coding_context','features.enable_request_compression':False,'model_providers.ttgl_coding_context.name':'TTGL explicit matched coding context','model_providers.ttgl_coding_context.base_url':base,'model_providers.ttgl_coding_context.wire_api':'responses','model_providers.ttgl_coding_context.requires_openai_auth':True,'model_providers.ttgl_coding_context.supports_websockets':False,'model_providers.ttgl_coding_context.request_max_retries':0,'model_providers.ttgl_coding_context.stream_max_retries':0}
                for k,v in config.items():command[-1:-1]=['-c',k+'='+json.dumps(v)]
                run_process(command,prompt,cell,p['timeout_seconds']);sid=validate_native_completion(cell);cells.append(dict(case=family,condition=arm,session_id=sid));write(ROOT/'progress.json',dict(cells=cells));print(family,arm,'completed',flush=True)
        write(ROOT/'generation-complete.json',dict(cells=cells))
        for c in cells:
            cell=ROOT/c['case']/c['condition'];work=cell/'work';stem=c['case'].replace('-','_');grade=cell/'independent';grade.mkdir();src=SOURCE/'source/exercises/practice'/c['case'];shutil.copyfile(src/(stem+'_test.py'),grade/(stem+'_test.py'));shutil.copyfile(work/(stem+'.py'),grade/(stem+'.py'));start=time.monotonic()
            with (grade/'stdout.log').open('x') as out,(grade/'stderr.log').open('x') as err:r=subprocess.run([sys.executable,'-I','-S','-m','unittest','discover','-s',str(grade),'-p','*_test.py'],cwd=grade,stdout=out,stderr=err,timeout=30)
            modified=[name for name in [stem+'_test.py','instructions.md','LICENSE'] if digest(work/name)!=m['inputs'][str((work/name).relative_to(ROOT))]]
            write(cell/'grade.json',dict(passed=r.returncode==0 and not modified,kind='Independent sealed original unittest execution plus artifact policy',test_exit_code=r.returncode,modified_protected_files=modified,host_test_seconds=time.monotonic()-start))
        write(ROOT/'complete.json',dict(model_processes=len(cells),at=datetime.now(timezone.utc).isoformat()))
    except BaseException as e:write(ROOT/'stopped.json',dict(error=type(e).__name__,message=str(e),no_retry=True));raise
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();globals()[a.action]()
