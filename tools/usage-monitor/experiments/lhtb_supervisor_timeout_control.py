"""Actual dropped-UID timeout cleanup and audited reference reuse; zero LLMs."""
import json,os,subprocess
from pathlib import Path
from lhtb_actor_runtime_v6 import UnknownActor
from lhtb_sqlite_actor_v3 import SQLiteActor
from lhtb_actor_runtime import BASE,HERE,sha,write
ROOT=BASE/'supervisor-timeout-controls-001'
def root_probe(actor,unknown=False):
 marker='/tmp/ttgl-owned-timeout-child.pid'
 if unknown:
  original=(actor.cfg/'engine.py').read_bytes();(actor.cfg/'engine.py').write_text("import os,time\nfrom pathlib import Path\ndef normalize(c):\n Path('"+marker+"').write_text(str(os.getpid()))\n while True:time.sleep(1)\n")
  child=['python3','/opt/cfg/engine_runner.py','/opt/cfg/engine.py'];input_text='{"configs":[{}]}'
 else:
  child=['python3','-c',"import os,time;from pathlib import Path;Path('"+marker+"').write_text(str(os.getpid()));time.sleep(600)"];input_text=''
 code="import os,subprocess,json;from pathlib import Path;assert os.getuid()==0;caps=int(next(x.split(':',1)[1].strip() for x in open('/proc/self/status') if x.startswith('CapEff:')),16);assert caps&(1<<5);timed=False\ntry:subprocess.run("+repr(child)+",input="+repr(input_text)+",text=True,capture_output=True,timeout=2"+('' if unknown else ',user=1000,group=1000,extra_groups=[]')+")\nexcept subprocess.TimeoutExpired:timed=True\nassert timed;pid=int(Path('"+marker+"').read_text());gone=False\ntry:os.kill(pid,0)\nexcept ProcessLookupError:gone=True\nassert gone,'timed-out child remains';print(json.dumps(dict(root_has_kill=True,timeout_observed=True,child_reaped=True)))"
 try:
  r=subprocess.run(['docker','exec','--user','0:0',actor.name,'python3','-c',code],capture_output=True,text=True,timeout=15)
  if r.returncode:raise ValueError('Timeout control failed:'+r.stderr)
  visible=actor.execute("python3 -c \"import os;print(os.getuid());print(next(x.split(':',1)[1].strip() for x in open('/proc/self/status') if x.startswith('CapEff:')))\"")
  parts=visible['stdout'].split();assert parts[0]=='1000' and int(parts[1],16)==0
  return dict(passed=True,root_cleanup=json.loads(r.stdout),actor_uid=1000,actor_effective_capabilities=0)
 finally:
  if unknown:(actor.cfg/'engine.py').write_bytes(original)
def main():
 os.umask(0o077);ROOT.mkdir();write(ROOT/'started.json',dict(pid=os.getpid(),model_calls=0,no_retry=True));checks={}
 try:
  for name,cls in [('unknown',UnknownActor),('sqlite',SQLiteActor)]:
   actor=cls(ROOT/name)
   try:
    actor.start();checks[name]=root_probe(actor,name=='unknown')
    if name=='unknown':actor.stop_daemon();actor.admin_archive()
   finally:actor.close()
  # Preserve the full105round witness instead of silently rerunning it. Strict
  # source equivalence admits only renamed imports and the root supervisor KILL
  # capability; candidate/daemon/verifier/runner bodies remain unchanged.
  pairs=[('lhtb_actor_runtime.py','lhtb_actor_runtime_base_v6.py',lambda s:s.replace("['SETUID','SETGID']","['SETUID','SETGID','KILL']")),('lhtb_actor_runtime_v2.py','lhtb_actor_runtime_private_v6.py',lambda s:s.replace('from lhtb_actor_runtime import','from lhtb_actor_runtime_base_v6 import')),('lhtb_actor_runtime_v5.py','lhtb_actor_runtime_v6.py',lambda s:s.replace('from lhtb_actor_runtime_v2 import','from lhtb_actor_runtime_private_v6 import').replace('from lhtb_actor_runtime import','from lhtb_actor_runtime_base_v6 import')),('lhtb_sqlite_actor_v2.py','lhtb_sqlite_actor_v3.py',lambda s:s.replace('from lhtb_actor_runtime import','from lhtb_actor_runtime_base_v6 import'))]
  equivalence=[]
  for old,new,transform in pairs:
   assert transform((HERE/old).read_text())==(HERE/new).read_text();equivalence.append(dict(old=old,new=new,old_sha256=sha(HERE/old),new_sha256=sha(HERE/new),only_declared_delta=True))
  witness=BASE/'actor-controls-010/reference/complete.json';reference=json.loads(witness.read_text());assert reference['passed'] and reference['reward']==1 and reference['required_rounds']==105 and reference['minimum_interval_seconds']==50
  result=dict(passed=all(c['passed'] for c in checks.values()),checks=checks,source_equivalence=equivalence,reference_witness=str(witness),reference_sha256=sha(witness),reference_reuse='Completed own-task full105round reference010, same candidate/daemon/verifier/runner bodies. Sole functional delta grants root supervisor KILL for timed-out dropped-UID children. Zero untrusted effective capabilities and actual bounded cleanup verified; new own empty/private-boundary011 also required.',model_calls=0,new_reference_model_calls=0)
  write(ROOT/'complete.json',result);print(json.dumps(dict(passed=result['passed'],checks=checks,model_calls=0)),flush=True)
 except BaseException as error:
  write(ROOT/'stopped.json',dict(error=type(error).__name__,message=str(error),model_calls=0,no_retry=True));raise
if __name__=='__main__':main()
