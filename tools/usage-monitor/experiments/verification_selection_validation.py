#!/usr/bin/env python3
"""Use reviewed stdlib Exercism tests; supply only missing native experiment glue."""
import argparse,hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
from longmemeval_codex_trial import native_command,run_process
from native_jsonl import validate_native_completion
from cost_context_study import REPO
from verification_actor_controls import permission_settings,check
HERE=Path(__file__).resolve().parent;GLOBAL=REPO/'work/security/context-memory-20261107';ROOT=GLOBAL/'verification-selection-validation-001';SOURCE=GLOBAL/'verification-selection-validation-source-001'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,value):p.write_text(json.dumps(value,indent=2)+'\n')
def prepare():
    controls=json.loads((SOURCE/'controls.json').read_text());receipt=json.loads((SOURCE/'pre-execution-receipt.json').read_text())
    if not controls['all_controls_pass'] or receipt['known_findings'] or not json.loads((SOURCE/'bug-controls.json').read_text())['all_controls_pass'] or not json.loads((SOURCE/'permission-control-002/results.json').read_text())['passed']:raise ValueError('Source/security/permission controls fail')
    os.umask(0o077);ROOT.mkdir();protocol=HERE.parent/'studies/verification-selection-validation-protocol-001.json';(ROOT/'protocol.json').write_bytes(protocol.read_bytes());p=json.loads(protocol.read_text());inputs={}
    for family in p['families']:
        stem=family.replace('-','_');src=SOURCE/'source/exercises/practice'/family
        for arm in p['conditions']:
            work=ROOT/family/arm/'work';work.mkdir(parents=True)
            for name,original in [(stem+'.py',SOURCE/'bug-controls'/family/(stem+'.py')),(stem+'_test.py',src/(stem+'_test.py')),('instructions.md',src/'.docs/instructions.md'),('LICENSE',SOURCE/'source/LICENSE')]:
                dest=work/name;shutil.copyfile(original,dest);inputs[str(dest.relative_to(ROOT))]=digest(dest)
    boundary=[]
    for family in p['families']:
        for arm in p['conditions']:
            cell=ROOT/family/arm;result=check(cell/'work',SOURCE/'outside-control.txt',cell/'permission-control');boundary.append(result)
    write(ROOT/'actor-permission-controls.json',dict(passed=all(x['passed'] for x in boundary),cells=boundary,model_calls=0))
    if not all(x['passed'] for x in boundary):raise ValueError('Actor permission controls fail before inference')
    files=[Path(__file__),HERE/'verification_actor_controls.py',HERE/'native_jsonl.py',HERE/'longmemeval_codex_trial.py',HERE/'longitudinal_memory_trial.py',HERE.parent/'observability/capture_proxy_compaction.py',HERE.parent/'observability/context_archive_policy.py',HERE.parent/'observability/exact_source_archive.py',HERE.parent/'observability/analyst_cli.py',HERE.parent/'studies/context-memory-pricing-20261107.json']
    write(ROOT/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),sources={str(f.relative_to(REPO)):digest(f) for f in files},inputs=inputs,protocol_sha256=digest(protocol),source_control_sha256=digest(SOURCE/'controls.json'),actor_control_sha256=digest(ROOT/'actor-permission-controls.json'),reviewed_source_files={row['path']:row['sha256'] for row in json.loads((SOURCE/'download-receipt.json').read_text())['files']},permission_control_sha256=digest(SOURCE/'permission-control-002/results.json'),bug_controls_sha256=digest(SOURCE/'bug-controls.json'),runtime_sha256=digest(Path(shutil.which('codex')).resolve()),model_calls=0));print('Prepared24 fresh repair workspaces; no models invoked.')
def frozen():
    m=json.loads((ROOT/'manifest.json').read_text())
    if digest(ROOT/'protocol.json')!=m['protocol_sha256']:raise ValueError('Protocol changed')
    if digest(ROOT/'actor-permission-controls.json')!=m['actor_control_sha256'] or any(digest(SOURCE/'source'/name)!=expected for name,expected in m['reviewed_source_files'].items()):raise ValueError('Actor controls or reviewed source changed')
    if digest(SOURCE/'permission-control-002/results.json')!=m['permission_control_sha256'] or digest(SOURCE/'bug-controls.json')!=m['bug_controls_sha256'] or digest(Path(shutil.which('codex')).resolve())!=m['runtime_sha256']:raise ValueError('Controls/runtime changed')
    if any(digest(REPO/f)!=h for f,h in m['sources'].items()):raise ValueError('Generation source changed')
    return m
def run():
    m=frozen();p=json.loads((ROOT/'protocol.json').read_text())
    if any(digest(ROOT/f)!=h for f,h in m['inputs'].items()):raise ValueError('Prepared inputs changed')
    with (ROOT/'started.json').open('x') as out:json.dump(dict(pid=os.getpid(),at=datetime.now(timezone.utc).isoformat()),out)
    cells=[]
    try:
        for index,family in enumerate(p['families']):
            shift=index%len(p['conditions']);arms=p['conditions'][shift:]+p['conditions'][:shift]
            for arm in arms:
                frozen();cell=ROOT/family/arm;work=cell/'work';prompt=('Repair the existing Python implementation to satisfy instructions.md and the provided tests. Inspect relevant task files. '+('Before editing, run the entire provided unittest suite once to diagnose the problem. ' if arm=='full_initial' else 'Before editing, select and run a focused relevant subset of the provided unittest tests to diagnose the problem. ')+"After repair, run the entire provided unittest suite before finishing; final full verification is mandatory in both conditions. Use the Python executable "+str(Path(sys.executable).resolve())+" with -I -S; package installs and external dependencies are not needed. Do not modify tests, instructions or license. Work only in this task directory; no network, downloads, outside solutions or other agents. Make a correct general repair, verify the final result and briefly report checks and uncertainty.");(cell/'prompt.txt').write_text(prompt)
                command=native_command(work,cell,p['model']);i=command.index('-s');del command[i:i+2];command[-1:-1]=['--ignore-rules']
                for feature in ('multi_agent','plugins','apps','browser_use','computer_use','image_generation','workspace_dependencies','view_image'):command[-1:-1]=['--disable',feature]
                config={'model_provider':'ttgl_verify','project_doc_max_bytes':0,'features.skip_host_skill_discovery':True,'features.enable_request_compression':False,'default_permissions':'ttgl_verify','permissions.ttgl_verify.filesystem':{':root':'deny',':minimal':'read',str(work.resolve()):'write',str(Path(sys.prefix).resolve()):'read',str(Path(shutil.which('codex')).resolve()):'read'},'permissions.ttgl_verify.network.enabled':False,'web_search':'disabled','model_providers.ttgl_verify.name':'TTGL initial verification comparison','model_providers.ttgl_verify.base_url':'http://127.0.0.1:8334','model_providers.ttgl_verify.wire_api':'responses','model_providers.ttgl_verify.requires_openai_auth':True,'model_providers.ttgl_verify.supports_websockets':False,'model_providers.ttgl_verify.request_max_retries':0,'model_providers.ttgl_verify.stream_max_retries':0}
                config.update(permission_settings(work))
                for k,v in config.items():
                    encoded='{'+','.join(json.dumps(a)+'='+json.dumps(b) for a,b in v.items())+'}' if isinstance(v,dict) else json.dumps(v);command[-1:-1]=['-c',k+'='+encoded]
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
