"""Empty/reference controls for adapted fuzz IPC grading; zero agent LLMs."""
import argparse,json,os,shutil
from pathlib import Path
from lhtb_fuzz_actor_v3 import FuzzActor,SOURCE,BASE,write
ROOT=BASE/'fuzz-controls-003'
def run(condition):
 os.umask(0o077);actor=FuzzActor(ROOT/condition);write(actor.cell/'started.json',dict(pid=os.getpid(),condition=condition,model_calls=0,no_retry=True))
 try:
  actor.start();uid=actor.execute('id -u');private=actor.execute('cat /tests/test_outputs.py');protected=actor.execute('echo forbidden >> /app/harness/targets/sql_parser.py');editable=actor.execute("python3 -c \"from pathlib import Path;Path('/app/workspace/probe.txt').write_text('write works')\"")
  ok=uid['stdout'].strip()=='1000' and private['exit_code']!=0 and protected['exit_code']!=0 and editable['exit_code']==0
  write(actor.cell/'boundary.json',dict(passed=ok,uid=uid,private=private,protected=protected,editable=editable))
  if not ok:raise ValueError('Actor boundary failed')
  if condition=='reference':
   target=actor.workspace/'fuzzer.py';shutil.copyfile(SOURCE/'solution/files/reference_fuzzer.py',target);target.chmod(0o644)
   # Preserve full upstream visible reference exercise, with immutable launcher.
   for i,command in enumerate(('fuzz run --target sql --time 30','fuzz run --target toml --time 30','fuzz run --time 30','fuzz report','fuzz coverage')):
    r=actor.execute(command,timeout=100);write(actor.cell/('reference-visible-'+str(i)+'.json'),r)
    if r['exit_code']:raise ValueError('Reference public exercise failed')
   (actor.output/'JOURNAL.md').write_text('Reference-control witness: unchanged upstream fuzzer; not a model-generated artifact.\n')
  grade=actor.grade();expected=condition=='reference';passed=grade['passed']==expected and (grade['reward']>=.70 if expected else grade['reward']<.70)
  write(actor.cell/'complete.json',dict(control_passed=passed,expected_pass=expected,**grade,model_calls=0));print(json.dumps(dict(control_passed=passed,**grade)),flush=True)
 except BaseException as e:
  write(actor.cell/'stopped.json',dict(error=type(e).__name__,message=str(e),model_calls=0,no_retry=True));raise
 finally:actor.close()
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('condition',choices=['empty','reference']);run(p.parse_args().condition)
