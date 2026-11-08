#!/usr/bin/env python3
"""Existing neutral-cwd judge method adapted to current immutable reader outputs."""
from datetime import datetime,timezone
from pathlib import Path
import argparse,hashlib,json,os
from smallville_native_mechanism import GLOBAL,HERE
from smallville_native_runtime import NativeCalls
from longmemeval_codex_trial import judge_prompt
from json_corpus import select_records
ROOT=GLOBAL/'smallville-neutral-validation-audit-002';SOURCE=GLOBAL/'smallville-validation-001';PROTOCOL=HERE.parent/'studies/smallville-neutral-audit-protocol-002.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def prepare():
 os.umask(0o077);grades=len(list(SOURCE.glob('case-*/*/grade.json')))
 ROOT.mkdir();(ROOT/'protocol.json').write_bytes(PROTOCOL.read_bytes());p=json.loads((SOURCE/'protocol.json').read_text());plan=[dict(question_id=q,case=i,condition=a) for i,q in enumerate(p['cases']) for a in p['conditions']];plan.sort(key=lambda x:hashlib.sha256(('smallville-neutral-001'+x['question_id']+x['condition']).encode()).hexdigest())
 for i,item in enumerate(plan):item['assessment']='item-'+str(i).zfill(3)
 write(ROOT/'plan.json',plan);sources=[Path(__file__),PROTOCOL,HERE/'smallville_native_runtime.py',HERE/'longmemeval_codex_trial.py'];write(ROOT/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),primary_grade_files=grades,registration_timing="Post-generation sensitivity audit; primary labels not inspected; not pre-primary registration",sources={str(p):sha(p) for p in sources},plan_sha256=sha(ROOT/'plan.json')));print('Prepared18neutral assessments; primary grade files',grades,flush=True)
def run():
 if not (SOURCE/'results.json').exists():raise ValueError('Complete/reconcile primary validation first')
 m=json.loads((ROOT/'manifest.json').read_text())
 if any(sha(Path(p))!=h for p,h in m['sources'].items()) or sha(ROOT/'plan.json')!=m['plan_sha256']:raise ValueError('Frozen audit changed')
 write(ROOT/'started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),no_retry=True));plan=json.loads((ROOT/'plan.json').read_text());rows=select_records(GLOBAL/'longmemeval_s_cleaned.json',[x['question_id'] for x in plan])
 try:
  for item in plan:
   source=SOURCE/f'case-{item["case"]:02d}'/item['condition']/'call-001/answer.txt';cell=ROOT/item['assessment'];cell.mkdir();write(cell/'source.json',dict(**item,answer_sha256=sha(source)));calls=NativeCalls(cell,cap=1);label=calls(judge_prompt(rows[item['question_id']],source.read_text()),'neutral_judge_overhead').strip().lower()
   if label not in ('yes','no'):raise ValueError('Invalid neutral label')
   write(cell/'grade.json',dict(passed=label=='yes',kind='Unchanged rubric; condition-neutral working directory'));print('neutral assessment',item['assessment'],'complete',flush=True)
  write(ROOT/'complete.json',dict(processes=len(plan),usage_audit_pending=True))
 except BaseException as e:
  write(ROOT/'stopped.json',dict(error=type(e).__name__,message=str(e),no_retry=True));raise
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','run']);globals()[parser.parse_args().action]()
