"""Existing reviewed runtime, public fuzz harness, isolated adapted verifier."""
import base64,json,secrets,shutil,subprocess,tempfile
from pathlib import Path
from lhtb_actor_runtime import BASE,HERE,IMAGE,PYTHON,args,mount,sha,write
SOURCE=BASE/'development-source/tasks/grammar-fuzz-coverage-hunt'
class FuzzActor:
 def __init__(self,cell):
  self.cell=Path(cell);self.cell.mkdir(parents=True);self.work=Path(tempfile.mkdtemp(prefix='ttgl-fuzz-actor-'));self.work.chmod(0o755)
  self.app=self.work/'app';shutil.copytree(SOURCE/'environment',self.app);(self.app/'Dockerfile').unlink()
  for name in ('workspace','output','task_history'):(self.app/name).mkdir(exist_ok=True)
  (self.app/'output/covdata').mkdir(exist_ok=True)
  for p in [self.app,*self.app.rglob('*')]:p.chmod(0o755 if p.is_dir() else 0o644)
  for name in ('workspace','output','output/covdata'):(self.app/name).chmod(0o777)
  self.history=self.app/'task_history';self.workspace=self.app/'workspace';self.output=self.app/'output';self.name='ttgl-fuzz-'+secrets.token_hex(10)
  self.launcher=self.work/'fuzz';self.launcher.write_text('#!/bin/sh\nexec python3 /app/harness/fuzz_cli.py "$@"\n');self.launcher.chmod(0o755)
  self.original={str(p.relative_to(self.app)):sha(p) for p in (self.app/'harness').rglob('*') if p.is_file()}
  write(self.cell/'manifest.json',dict(work=str(self.work),container=self.name,image=IMAGE,adapter_sha256=sha(Path(__file__)),source_hashes={str(p.relative_to(SOURCE)):sha(p) for p in SOURCE.rglob('*') if p.is_file()},model_calls=0))
 def start(self):
  cmd=['docker','run','--detach','--pull','never','--name',self.name]+args()+mount(PYTHON,'/opt/ttgl/python',True)+mount(self.app,'/app',True)+mount(self.workspace,'/app/workspace')+mount(self.output,'/app/output')+mount(self.launcher,'/usr/local/bin/fuzz',True)+[IMAGE,'sleep','infinity']
  subprocess.run(cmd,check=True,capture_output=True,timeout=40);inspect=json.loads(subprocess.check_output(['docker','inspect',self.name]))[0];write(self.cell/'actor-inspect.json',inspect)
  if any('/tests' in x['Destination'] or '/private' in x['Destination'] or 'docker.sock' in x['Destination'] for x in inspect['Mounts']):raise ValueError('Private actor mount')
 def execute(self,command,timeout=180):
  r=subprocess.run(['docker','exec','--user','1000:1000',self.name,'timeout','-k','3',str(timeout),'bash','-lc',command],capture_output=True,text=True,timeout=timeout+15)
  return dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr)
 def grade(self):
  subprocess.run(['docker','pause',self.name],check=True,capture_output=True,timeout=20)
  code="from pathlib import Path;import base64,json;p=Path('/input');a=list(p.rglob('*'));assert not any(x.is_symlink() or not(x.is_dir() or x.is_file()) for x in a);files=[x for x in a if x.is_file()];assert sum(x.stat().st_size for x in files)<134217728;print(json.dumps({str(x.relative_to(p)):base64.b64encode(x.read_bytes()).decode() for x in files}))"
  sealed=self.work/'sealed';sealed.mkdir();sealed.chmod(0o755)
  for component in ('workspace','output'):
   raw=subprocess.check_output(['docker','run','--rm','--pull','never']+args('0:0')+mount(self.app/component,'/input',True)+[IMAGE,'python3','-I','-S','-c',code],timeout=60);(self.cell/('sealed-'+component+'.json')).write_bytes(raw);root=sealed/component;root.mkdir();root.chmod(0o755)
   for name,value in json.loads(raw).items():
    rel=Path(name)
    if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe sealed path')
    p=root/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(value));p.chmod(0o644)
   for p in root.rglob('*'):
    if p.is_dir():p.chmod(0o755)
  self.close()
  if any(sha(self.app/p)!=h for p,h in self.original.items()):raise ValueError('Public harness changed')
  private=self.work/'private';private.mkdir();private.chmod(0o700)
  original=(SOURCE/'tests/test_outputs.py').read_text();needle='fuzzer_mod = load_module("fuzzer", fuzzer_path)'
  if original.count(needle)!=1:raise ValueError('Unexpected upstream fuzzer loader')
  (private/'test_outputs.py').write_text(original.replace(needle,'fuzzer_mod = __import__("fuzz_verifier_bridge").RemoteFuzzer()'))
  shutil.copyfile(HERE/'fuzz_verifier_bridge.py',private/'fuzz_verifier_bridge.py')
  init="from pathlib import Path;import os;p=Path('/init');os.chown(p,0,0);[os.chown(x,0,0) for x in p.rglob('*')];os.chmod(p,0o700)"
  subprocess.run(['docker','run','--rm']+args('0:0',init=True)+mount(private,'/init')+[IMAGE,'python3','-I','-S','-c',init],check=True,capture_output=True,timeout=40)
  logs=self.work/'grade-logs';logs.mkdir();logs.chmod(0o755)
  init_outputs="from pathlib import Path;import os;roots=[Path('/grade-output'),Path('/grade-logs')];[(os.chown(p,0,0),os.chmod(p,0o755)) for p in roots];[(os.chown(x,0,0),os.chmod(x,0o755 if x.is_dir() else 0o644)) for p in roots for x in p.rglob('*')]"
  subprocess.run(['docker','run','--rm']+args('0:0',init=True)+mount(sealed/'output','/grade-output')+mount(logs,'/grade-logs')+[IMAGE,'python3','-I','-S','-c',init_outputs],check=True,capture_output=True,timeout=40)
  base=['docker','run','--rm','--pull','never']+args('0:0')+['--cap-add','KILL','-e','COVERAGE_FILE=/grade-state/.coverage']+mount(logs,'/grade-state')+mount(PYTHON,'/opt/ttgl/python',True)+mount(private,'/tests',True)+mount(HERE/'fuzz_worker.py','/opt/ttgl/fuzz_worker.py',True)+mount(self.app/'harness','/app/harness',True)+mount(sealed/'workspace','/app/workspace',True)+mount(sealed/'output','/app/output')+mount(logs,'/logs/verifier')
  probe="import subprocess,sys;p=subprocess.run([sys.executable,'-c',\"import os;assert os.getuid()==1000;open('/tests/test_outputs.py').read()\"],user=1000,group=1000,extra_groups=[],capture_output=True,text=True);assert p.returncode!=0 and 'PermissionError' in p.stderr;print('private boundary passed')"
  b=subprocess.run(base+[IMAGE,'python3','-I','-S','-c',probe],capture_output=True,text=True,timeout=30);write(self.cell/'private-child-control.json',dict(passed=b.returncode==0,stdout=b.stdout,stderr=b.stderr))
  if b.returncode:raise ValueError('Private candidate boundary failed')
  r=subprocess.run(base+[IMAGE,'python3','/tests/test_outputs.py'],capture_output=True,text=True,timeout=180);(self.cell/'verifier-stdout.log').write_text(r.stdout);(self.cell/'verifier-stderr.log').write_text(r.stderr)
  result=json.loads((sealed/'output/verification_result.json').read_text());result.update(verifier_exit_code=r.returncode,adapter='Unmodified target/parser/coverage/threshold; separate UID1000 fuzzer JSON IPC changes throughput; not official score',artifact_policy_requires_separate_review=True);write(self.cell/'grade.json',result);return result
 def close(self):
  r=subprocess.run(['docker','inspect','--format','{{.State.Paused}}',self.name],capture_output=True,text=True,timeout=15)
  if r.returncode==0 and r.stdout.strip()=='true':subprocess.run(['docker','unpause',self.name],capture_output=True,check=True,timeout=15)
  subprocess.run(['docker','rm','--force',self.name],capture_output=True,timeout=30)
