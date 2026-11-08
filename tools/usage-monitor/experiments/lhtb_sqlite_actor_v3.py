"""Pinned SQLite task with separate UID1000 actor and sealed private grading.

No dependency installs or model calls. Original comparison and reward bodies
stay unchanged; only candidate subprocess credentials are adapted.
"""
import base64,json,os,secrets,shutil,subprocess,tempfile
from pathlib import Path
from lhtb_actor_runtime_base_v6 import BASE,IMAGE,PYTHON,args,mount,sha,write
SOURCE=BASE/'development-source/tasks-2.0/sqlite_wal_recovery_audit__02'

class SQLiteActor:
 def __init__(self,cell):
  self.cell=Path(cell);self.cell.mkdir(parents=True);self.work=Path(tempfile.mkdtemp(prefix='ttgl-sqlite-actor-'));self.work.chmod(0o755)
  self.app=self.work/'app';shutil.copytree(SOURCE/'environment/app',self.app)
  for p in [self.app,*self.app.rglob('*')]:p.chmod(0o755 if p.is_dir() or p.name=='feedback' else 0o644)
  (self.app/'task_history').mkdir();(self.app/'task_history').chmod(0o755)
  self.workspace=self.app/'workspace';self.workspace.chmod(0o777)
  self.history=self.work/'history';self.history.mkdir(mode=0o755);self.history.chmod(0o755)
  self.name='ttgl-sqlite-'+secrets.token_hex(10);self.protected={str(p.relative_to(self.app)):sha(p) for p in self.app.rglob('*') if p.is_file() and 'workspace' not in p.relative_to(self.app).parts}
  write(self.cell/'manifest.json',dict(container=self.name,work=str(self.work),image=IMAGE,source_hashes={str(p.relative_to(SOURCE)):sha(p) for p in SOURCE.rglob('*') if p.is_file()},adapter_sha256=sha(Path(__file__)),model_calls=0))
 def start(self):
  cmd=['docker','run','--detach','--pull','never','--name',self.name]+args()+mount(PYTHON,'/opt/ttgl/python',True)+mount(self.app,'/app',True)+mount(self.workspace,'/app/workspace')+mount(self.history,'/app/task_history',True)+[IMAGE,'sleep','infinity']
  subprocess.run(cmd,check=True,capture_output=True,timeout=40)
  inspect=json.loads(subprocess.check_output(['docker','inspect',self.name]))[0];write(self.cell/'actor-inspect.json',inspect)
  if any('/tests' in x['Destination'] or '/private' in x['Destination'] or 'docker.sock' in x['Destination'] for x in inspect['Mounts']):raise ValueError('Private actor mount')
 def execute(self,command,timeout=180):
  r=subprocess.run(['docker','exec','--user','1000:1000',self.name,'timeout','-k','3',str(timeout),'bash','-lc',command],capture_output=True,text=True,timeout=timeout+15)
  return dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr)
 def grade(self):
  subprocess.run(['docker','pause',self.name],check=True,capture_output=True,timeout=20)
  # Trusted copy process rejects symlinks/special files and caps retained bytes.
  code="from pathlib import Path;import base64,json;p=Path('/input');a=list(p.rglob('*'));assert not any(x.is_symlink() or not (x.is_dir() or x.is_file()) for x in a);files=[x for x in a if x.is_file()];assert sum(x.stat().st_size for x in files)<67108864;print(json.dumps({str(x.relative_to(p)):base64.b64encode(x.read_bytes()).decode() for x in files}))"
  raw=subprocess.check_output(['docker','run','--rm','--pull','never']+args('0:0')+mount(self.workspace,'/input',True)+[IMAGE,'python3','-I','-S','-c',code],timeout=40);(self.cell/'sealed-workspace.json').write_bytes(raw)
  sealed=self.work/'sealed';sealed.mkdir();sealed.chmod(0o755)
  for name,value in json.loads(raw).items():
   rel=Path(name)
   if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe sealed path')
   p=sealed/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(value));p.chmod(0o644)
  for p in sealed.rglob('*'):
   if p.is_dir():p.chmod(0o755)
  self.close()
  if any(sha(self.app/p)!=h for p,h in self.protected.items()):raise ValueError('Public harness modified')
  private=self.work/'private';shutil.copytree(SOURCE/'tests',private);private.chmod(0o700)
  judge=private/'private/judge.py';original=judge.read_text();needle='        timeout=45,\n'
  if original.count(needle)!=1:raise ValueError('Unexpected candidate invocation')
  judge.write_text(original.replace(needle,needle+'        user=1000, group=1000, extra_groups=[],\n'))
  # Host-created files may retain inherited ACLs; actual access control is also
  # checked with the exact root-mounted private parent before grading.
  init="from pathlib import Path;import os;p=Path('/init');os.chown(p,0,0);[os.chown(x,0,0) for x in p.rglob('*')];os.chmod(p,0o700)"
  subprocess.run(['docker','run','--rm']+args('0:0',init=True)+mount(private,'/init')+[IMAGE,'python3','-I','-S','-c',init],check=True,capture_output=True,timeout=40)
  base=['docker','run','--rm','--pull','never']+args('0:0')+mount(PYTHON,'/opt/ttgl/python',True)+mount(private,'/tests',True)+mount(sealed,'/app/workspace',True)+mount(self.app/'observations','/app/observations',True)
  probe="import subprocess,sys,json;p=subprocess.run([sys.executable,'-c',\"import os;assert os.getuid()==1000;open('/tests/private/manifest.json').read()\"],user=1000,group=1000,extra_groups=[],capture_output=True,text=True);assert p.returncode!=0 and 'PermissionError' in p.stderr;print('private boundary passed')"
  b=subprocess.run(base+[IMAGE,'python3','-I','-S','-c',probe],capture_output=True,text=True,timeout=30);write(self.cell/'private-child-control.json',dict(passed=b.returncode==0,stdout=b.stdout,stderr=b.stderr))
  if b.returncode:raise ValueError('Private candidate boundary failed')
  r=subprocess.run(base+[IMAGE,'python3','/tests/private/judge.py'],capture_output=True,text=True,timeout=900);(self.cell/'judge.log').write_text(r.stdout);(self.cell/'judge-stderr.log').write_text(r.stderr)
  report=json.loads(r.stdout)
  reward=subprocess.run(base+mount(self.cell,'/receipts',True)+[IMAGE,'python3','/tests/private/dense_reward.py','/receipts/judge.log'],capture_output=True,text=True,timeout=30)
  if reward.returncode:raise ValueError('Dense grader failed')
  result=dict(binary=bool(report['passed']),reward=float(reward.stdout),verifier_exit_code=r.returncode,adapter='Original judge/dense comparison; candidate UID1000; sealed state; not official leaderboard',artifact_policy_requires_separate_review=True)
  write(self.cell/'grade.json',result);return result
 def close(self):
  r=subprocess.run(['docker','inspect','--format','{{.State.Paused}}',self.name],capture_output=True,text=True,timeout=15)
  if r.returncode==0 and r.stdout.strip()=='true':subprocess.run(['docker','unpause',self.name],capture_output=True,check=True,timeout=15)
  subprocess.run(['docker','rm','--force',self.name],capture_output=True,timeout=30)
