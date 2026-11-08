"""Version2adds an actual private-mounted verifier child privilege control."""
import json,shutil,subprocess
from pathlib import Path
from lhtb_actor_runtime_base_v6 import UnknownActor as BaseActor,SOURCE,IMAGE,PYTHON,RUNNER,args,mount,write,sha,HERE
PROBE='''import os
def normalize(c):
 result={'uid':os.getuid()}
 for k,p in [('key','/opt/cfg/runs/.key'),('data','/opt/cfg/cfgd_data.json'),('gold','/private/tests/cases_hidden.json')]:
  try:open(p).read();result[k]='LEAK'
  except PermissionError:result[k]='DENIED'
  except FileNotFoundError:result[k]='MISSING'
 return result
'''
class UnknownActor(BaseActor):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw)
  if sha(SOURCE/'environment/harness/engine_runner.py')!=sha(SOURCE/'tests/engine_runner.py'):raise ValueError('Source runners differ; cannot substitute silently')
  write(self.cell/'boundary-version.json',dict(version=2,sources={str(p):sha(p) for p in (Path(__file__),HERE/'lhtb_actor_runtime.py',HERE/'lhtb_actor_controls.py')},model_calls=0))
 def grade(self):
  self.stop_daemon();self.admin_archive();self.close()
  private=self.work/'private-tests';shutil.copytree(SOURCE/'tests',private);(private/'engine_runner.py').write_text(RUNNER)
  probe=self.work/'privilege-probe.py';probe.write_text(PROBE);probe.chmod(0o644)
  a=['docker','run','--rm']+args('0:0',private=True)+mount(PYTHON,'/opt/ttgl/python',True)+mount(self.cfg,'/opt/cfg',True)+mount(self.app,'/app')+mount(self.grade_logs,'/logs/verifier')+mount(private,'/private/tests',True)
  control="import json,pathlib,subprocess,sys;assert pathlib.Path('/private/tests/cases_hidden.json').exists();r=subprocess.run([sys.executable,'/opt/cfg/engine_runner.py','/opt/privilege-probe.py'],input='{"+'"configs":[{}]'+"}',capture_output=True,text=True);print(r.stdout);assert json.loads(r.stdout)['outputs']==[dict(uid=1000,key='DENIED',data='DENIED',gold='DENIED')]"
  result=subprocess.run(a+mount(probe,'/opt/privilege-probe.py',True)+[IMAGE,'python3','-c',control],capture_output=True,text=True,timeout=45)
  write(self.cell/'verifier-child-boundary.json',dict(passed=result.returncode==0,stdout=result.stdout,stderr=result.stderr,model_calls=0))
  if result.returncode:raise ValueError('Actual mounted verifier boundary failed')
  with (self.cell/'verifier-stdout.log').open('xb') as out,(self.cell/'verifier-stderr.log').open('xb') as err:r=subprocess.run(a+[IMAGE,'python3','-m','pytest','-p','no:cacheprovider','-rA','/private/tests/test_outputs.py'],stdout=out,stderr=err,timeout=900)
  reward=float((self.grade_logs/'reward.txt').read_text())
  for p in self.grade_logs.glob('*'):
   if p.is_file():shutil.copyfile(p,self.cell/('verifier-'+p.name))
  value=dict(reward=reward,verifier_exit_code=r.returncode,model_calls=0,grading='Original verifier body, matched original runner via trusted UID-drop wrapper; private-mounted child probe passes; actor stopped first.')
  write(self.cell/'grade.json',value);return value
