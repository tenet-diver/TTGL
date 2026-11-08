#!/usr/bin/env python3
"""Versioned boundary/empty/reference controls, no benchmark model calls."""
import argparse,json,os,time
from pathlib import Path
from lhtb_actor_runtime import BASE,HERE,sha,write
from lhtb_actor_runtime_v6 import UnknownActor
ROOT=BASE/'actor-controls-011'
def run(condition):
 os.umask(0o077);cell=ROOT/condition;actor=UnknownActor(cell,reference=condition=='reference');write(cell/'started.json',dict(pid=os.getpid(),condition=condition,model_calls=0,no_retry=True));start=time.monotonic()
 try:
  actor.start()
  tests={}
  for label,command,expected in [
   ('actor_uid','id -u',0),
   ('private_data_denied','cat /opt/cfg/cfgd_data.json',1),
   ('private_key_denied','cat /opt/cfg/runs/.key',1),
   ('protected_source_denied',"printf blocked >> /opt/cfg/cfg_daemon.py",1),
   ('host_home_absent','test -e /home/codespace/.codex/auth.json',1),
   ('verifier_absent','test -e /private/tests/test_outputs.py',1),
   ('solution_scope','test -e /solution/solve.sh',0 if condition=='reference' else 1)]:
   r=actor.execute(command,timeout=10);passed=(r['exit_code']==expected) if label not in ('private_data_denied','private_key_denied','protected_source_denied') else r['exit_code']!=0
   if label=='actor_uid':passed=passed and r['stdout'].strip()=='1000'
   tests[label]=dict(passed=passed,result=r)
  inplace=actor.execute("python3 -c \"from pathlib import Path;p=Path('/opt/cfg/engine.py');v=p.read_text();p.write_text(v);print('inplaceOK')\"",timeout=10)
  tests['actual_actor_inplace_write']=dict(passed=inplace['exit_code']==0 and inplace['stdout'].strip()=='inplaceOK',result=inplace)
  # Candidate code executes through the exact trusted runner with UID1000 and
  # cannot read private oracle/key even when invoked by the root daemon.
  original=(actor.cfg/'engine.py').read_bytes()
  payload="import os,json\ndef normalize(c):\n out={'uid':os.getuid()}\n for key,p in [('key','/opt/cfg/runs/.key'),('data','/opt/cfg/cfgd_data.json'),('gold','/private/tests/cases_hidden.json')]:\n  try:open(p).read();out[key]='LEAK'\n  except (PermissionError,FileNotFoundError):out[key]='DENIED'\n return out\n"
  (actor.cfg/'engine.py').write_text(payload)
  r=actor.execute("printf '%s' '{\"configs\":[{}]}' | python3 /opt/cfg/engine_runner.py /opt/cfg/engine.py",timeout=15,user='0:0');v=json.loads(r['stdout']);out=v['outputs'][0];tests['root_invoked_engine_drops_privilege']=dict(passed=out==dict(uid=1000,key='DENIED',data='DENIED',gold='DENIED'),result=out)
  (actor.cfg/'engine.py').write_bytes(original)
  write(cell/'boundary-controls.json',dict(checks=tests,passed=all(x['passed'] for x in tests.values()),model_calls=0))
  if not all(x['passed'] for x in tests.values()):raise ValueError('Actor boundary failed; no model assignment')
  if condition=='boundary':
   actor.stop_daemon();actor.admin_archive();actor.close();result=dict(passed=True,model_calls=0,scope='Actual container/source/key/runner boundary only; no benchmark efficacy')
  else:
   if condition=='reference':
    with (cell/'solver-stdout.log').open('xb') as out,(cell/'solver-stderr.log').open('xb') as err:
     import subprocess
     install=actor.execute("python3 -c \"from pathlib import Path;Path('/opt/cfg/engine.py').write_bytes(Path('/solution/reference_engine.py').read_bytes())\"",timeout=20)
     if install['exit_code']:raise ValueError('In-place reference installation failed')
     r=subprocess.run(['docker','exec','--user','1000:1000',actor.name,'python3','/solution/solve_client.py'],stdout=out,stderr=err,timeout=9000)
     if r.returncode:raise ValueError('Reference control execution failed')
   grade=actor.grade();expected=1.0 if condition=='reference' else 0.0;result=dict(**grade,expected=expected,passed=grade['reward']==expected,required_rounds=105,minimum_interval_seconds=50)
  result['wall_seconds']=time.monotonic()-start;write(cell/'complete.json',result);print(json.dumps(result),flush=True)
 except BaseException as e:
  write(cell/'stopped.json',dict(error=type(e).__name__,message=str(e),model_calls=0,no_retry=True));raise
 finally:actor.close()
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('condition',choices=['boundary','empty','reference']);run(parser.parse_args().condition)
