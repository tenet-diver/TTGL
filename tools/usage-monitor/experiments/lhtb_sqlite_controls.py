"""Fresh empty/reference controls for SQLite private actor boundary, zero LLMs."""
import argparse,json,os,shutil
from pathlib import Path
from lhtb_sqlite_actor import SQLiteActor,SOURCE,BASE,write,sha
ROOT=BASE/'sqlite-controls-001'
def run(condition):
 os.umask(0o077);actor=SQLiteActor(ROOT/condition);write(actor.cell/'started.json',dict(pid=os.getpid(),condition=condition,model_calls=0,no_retry=True))
 try:
  actor.start();uid=actor.execute('id -u');private=actor.execute('cat /tests/private/manifest.json');protected=actor.execute('echo forbidden >> /app/observations/manifest.json');editable=actor.execute("python3 -c \"from pathlib import Path;Path('/app/workspace/probe.txt').write_text('write works')\"")
  passed=uid['stdout'].strip()=='1000' and private['exit_code']!=0 and protected['exit_code']!=0 and editable['exit_code']==0
  write(actor.cell/'boundary.json',dict(passed=passed,uid=uid,private=private,protected=protected,editable=editable))
  if not passed:raise ValueError('Actor boundary failed')
  if condition=='reference':
   # This oracle is a control-only known-correct witness, never mounted in model
   # actors. All functions are copied unchanged; stdin dispatch is only wrapper.
   oracle=SOURCE/'tests/private/new10_oracle.py';target=actor.workspace/'reference_oracle.py';shutil.copyfile(oracle,target);target.chmod(0o644)
   code="import json,sys\nfrom reference_oracle import sqlite_analytics\nprint(json.dumps(sqlite_analytics(json.load(sys.stdin)['parameters'])))\n"
   (actor.workspace/'reconstruct.py').write_text(code);(actor.workspace/'reconstruct.py').chmod(0o644)
   write(actor.cell/'control-only-reference.json',dict(original_oracle_sha256=sha(oracle),copied_sha256=sha(target),model_exposure=False))
   result=actor.execute('python3 /app/tools/feedback');write(actor.cell/'public-feedback.json',result)
   if result['exit_code'] or not json.loads(result['stdout']).get('public_passed'):raise ValueError('Reference public feedback failed')
  grade=actor.grade();expected=condition=='reference';ok=grade['binary']==expected and (grade['reward']==1.0 if expected else grade['reward']<1)
  write(actor.cell/'complete.json',dict(passed=ok,expected_binary=expected,**grade,model_calls=0));print(json.dumps(dict(passed=ok,**grade)),flush=True)
 except BaseException as e:
  write(actor.cell/'stopped.json',dict(error=type(e).__name__,message=str(e),model_calls=0,no_retry=True));raise
 finally:actor.close()
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('condition',choices=['empty','reference']);run(p.parse_args().condition)
