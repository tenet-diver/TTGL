"""Reviewed-runtime LHTB actor boundary; private oracle/key never actor-readable.

Reuses pinned task sources and existing Docker/Python artifacts. Original source
is copied unchanged except a trusted privilege-dropping runner/launcher boundary.
No model call, package installation, image pull or grading feedback to actors.
"""
from datetime import datetime,timezone
import base64,hashlib,json,os,secrets,shutil,subprocess,tempfile,time
from pathlib import Path
from lhtb_unknown_controls_002 import BASE,SOURCE,IMAGE,PYTHON,ENV,mount
HERE=Path(__file__).resolve().parent
RUNNER='''import os,runpy
if os.geteuid()==0:
 os.setgroups([]);os.setgid(1000);os.setuid(1000)
runpy.run_path('/opt/cfg/engine_runner.original.py',run_name='__main__')
'''
LAUNCH='''import os,runpy
os.umask(0o022)
runpy.run_path('/opt/cfg/cfg_daemon.py',run_name='__main__')
'''
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def write(p,v):
 with Path(p).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def args(user='1000:1000',*,private=False,init=False):
 a=['--user',user,'--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','4096m','--cpus','2','--pids-limit','256','--tmpfs','/tmp:rw,nosuid,nodev,size=256m','--workdir','/app']
 for cap in (['CHOWN'] if init else ['SETUID','SETGID','KILL']):a+=['--cap-add',cap]
 if private:a+=['--tmpfs','/private:rw,nosuid,nodev,size=64m,mode=0700']
 for k,v in ENV.items():a+=['-e',k+'='+v]
 return a
class UnknownActor:
 def __init__(self,cell,*,reference=False):
  self.cell=Path(cell);self.cell.mkdir(parents=True);self.work=Path(tempfile.mkdtemp(prefix='ttgl-lhtb-actor-'));self.work.chmod(0o755);self.reference=reference;self.name='ttgl-memory-'+secrets.token_hex(10);self.daemon=None;self.logs=[]
  self.cfg=self.work/'cfg';shutil.copytree(SOURCE/'environment/harness',self.cfg);shutil.copyfile(self.cfg/'engine.py',self.cfg/'engine.orig.py');shutil.copyfile(self.cfg/'engine_runner.py',self.cfg/'engine_runner.original.py');(self.cfg/'engine_runner.py').write_text(RUNNER);(self.cfg/'daemon_launcher.py').write_text(LAUNCH);(self.cfg/'runs/submissions').mkdir(parents=True)
  self.app=self.work/'app';self.app.mkdir(mode=0o777);self.history=self.work/'history';self.history.mkdir(mode=0o755);self.grade_logs=self.work/'grade-logs';self.grade_logs.mkdir(mode=0o777)
  self.launcher=self.work/'cfg-cli';self.launcher.write_text('#!/bin/sh\nexec python3 /opt/cfg/cfg_cli.py "$@"\n');self.launcher.chmod(0o755)
  for p in self.cfg.rglob('*'):p.chmod(0o755 if p.is_dir() else 0o644)
  self.cfg.chmod(0o755);(self.cfg/'engine.py').chmod(0o666)
  init="from pathlib import Path;import os;p=Path('/init');os.chown(p,0,0);[(os.chown(x,0,0)) for x in p.rglob('*')];os.chmod(p/'cfgd_data.json',0o600)"
  subprocess.run(['docker','run','--rm']+args('0:0',init=True)+mount(self.cfg,'/init')+[IMAGE,'python3','-I','-S','-c',init],check=True,capture_output=True,timeout=40)
  self.original={str(p.relative_to(self.cfg)):sha(p) for p in self.cfg.rglob('*') if p.is_file() and p.name!='cfgd_data.json'}
  write(self.cell/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),work=str(self.work),container=self.name,image=IMAGE,reference_control=reference,original_public_files=self.original,runner_wrapper_sha256=sha(self.cfg/'engine_runner.py'),source_runner_sha256=sha(SOURCE/'environment/harness/engine_runner.py'),adapter_sha256=sha(Path(__file__)),model_calls=0,scope='Private root daemon; UID1000 actor and untrusted engine; no verifier mounted during generation. No official leaderboard claim.'))
 def start(self):
  a=['docker','run','--detach','--name',self.name]+args()+mount(PYTHON,'/opt/ttgl/python',True)+mount(self.cfg,'/opt/cfg',True)+mount(self.cfg/'engine.py','/opt/cfg/engine.py')+mount(self.cfg/'runs','/opt/cfg/runs')+mount(self.app,'/app')+mount(self.history,'/app/task_history',True)+mount(self.launcher,'/usr/local/bin/cfg',True)
  if self.reference:a+=mount(SOURCE/'solution','/solution',True)
  subprocess.run(a+[IMAGE,'sleep','infinity'],check=True,capture_output=True,timeout=40)
  inspect=json.loads(subprocess.check_output(['docker','inspect',self.name]))[0];write(self.cell/'actor-inspect.json',inspect)
  if any('/tests' in x['Destination'] or 'docker.sock' in x['Destination'] for x in inspect['Mounts']):raise ValueError('Forbidden actor mount')
  for filename in ('daemon-stdout.log','daemon-stderr.log'):self.logs.append((self.cell/filename).open('xb'))
  self.daemon=subprocess.Popen(['docker','exec','--user','0:0',self.name,'python3','/opt/cfg/daemon_launcher.py'],stdout=self.logs[0],stderr=self.logs[1])
  for i in range(100):
   r=self.execute('cfg status',timeout=10)
   if r['exit_code']==0:
    write(self.cell/'ready.json',dict(at=datetime.now(timezone.utc).isoformat(),status=r));return
   if self.daemon.poll() is not None:raise ValueError('Trusted daemon exited during preparation')
   time.sleep(.1)
  raise ValueError('No task daemon readiness; no model assignment')
 def execute(self,command,timeout=180,user='1000:1000'):
  start=time.monotonic();r=subprocess.run(['docker','exec','--user',user,self.name,'timeout','-s','TERM','-k','3',str(timeout),'bash','-lc',command],capture_output=True,text=True,timeout=timeout+15)
  return dict(exit_code=r.returncode,stdout=r.stdout,stderr=r.stderr,seconds=time.monotonic()-start)
 def admin_archive(self):
  code="from pathlib import Path;import base64,json;print(json.dumps({str(p.relative_to('/opt/cfg')):base64.b64encode(p.read_bytes()).decode() for p in Path('/opt/cfg').rglob('*') if p.is_file()}))"
  raw=subprocess.check_output(['docker','exec','--user','0:0',self.name,'python3','-I','-S','-c',code],timeout=30);archive=self.cell/'sealed-cfg.json';archive.write_bytes(raw);archive.chmod(0o600)
  values=json.loads(raw);hashes={p:hashlib.sha256(base64.b64decode(v)).hexdigest() for p,v in values.items()};write(self.cell/'sealed-state.json',dict(files=hashes,archive_sha256=sha(archive),private_values_printed=False))
  modified=[p for p,h in self.original.items() if hashes.get(p)!=h and p!='engine.py']
  if modified:raise ValueError('Protected harness changed:'+str(modified))
  return hashes
 def stop_daemon(self):
  r=self.execute('cfg shutdown',timeout=20)
  if r['exit_code']!=0:raise ValueError('Daemon shutdown did not complete')
  self.daemon.wait(timeout=20)
 def grade(self):
  self.stop_daemon();self.admin_archive();self.close()
  private=self.work/'private-tests';shutil.copytree(SOURCE/'tests',private);(private/'engine_runner.py').write_text(RUNNER)
  # The engine runner opens as root, drops to1000, then imports the public trusted
  # original runner. /private stays0700root, so child cannot read test golds.
  a=['docker','run','--rm']+args('0:0',private=True)+mount(PYTHON,'/opt/ttgl/python',True)+mount(self.cfg,'/opt/cfg',True)+mount(self.app,'/app')+mount(self.grade_logs,'/logs/verifier')+mount(private,'/private/tests',True)
  with (self.cell/'verifier-stdout.log').open('xb') as out,(self.cell/'verifier-stderr.log').open('xb') as err:r=subprocess.run(a+[IMAGE,'python3','-m','pytest','-p','no:cacheprovider','-rA','/private/tests/test_outputs.py'],stdout=out,stderr=err,timeout=900)
  reward=float((self.grade_logs/'reward.txt').read_text())
  for p in self.grade_logs.glob('*'):
   if p.is_file():shutil.copyfile(p,self.cell/('verifier-'+p.name))
  result=dict(reward=reward,verifier_exit_code=r.returncode,model_calls=0,grading='Unmodified task verifier body, trusted privilege-dropping runner; actor stopped before tests mount.')
  write(self.cell/'grade.json',result);return result
 def close(self):
  subprocess.run(['docker','rm','--force',self.name],capture_output=True,timeout=30)
  if self.daemon:
   try:self.daemon.wait(timeout=10)
   except subprocess.TimeoutExpired:self.daemon.terminate();self.daemon.wait(timeout=10)
  for f in self.logs:
   if not f.closed:f.close()
