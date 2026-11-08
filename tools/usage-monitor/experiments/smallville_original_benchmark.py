#!/usr/bin/env python3
"""Direct original-style memory comparison; originals/failures remain intact."""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import hashlib,json,os
from smallville_native_mechanism import GLOBAL,HERE
from smallville_local_embeddings import LocalEmbeddings
from smallville_compat_v3 import CompatibleMemoryV3
from smallville_native_runtime import NativeCalls
from smallville_native_readers import NativeReaders
from smallville_benchmark import boundary
from longmemeval_codex_trial import history,judge_prompt
from json_corpus import select_records
ROOT=GLOBAL/'smallville-original-benchmark-001';PROTOCOL=HERE.parent/'studies/smallville-original-benchmark-protocol-001.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def parse_date(s):return datetime.strptime(s,'%Y/%m/%d (%a) %H:%M')
def main():
 os.umask(0o077);ROOT.mkdir();(ROOT/'protocol.json').write_bytes(PROTOCOL.read_bytes());p=json.loads(PROTOCOL.read_text())
 sources=[Path(__file__),PROTOCOL,HERE/'smallville_compat_v3.py',HERE/'smallville_memory.py',HERE/'smallville_native_runtime.py',HERE/'smallville_native_readers.py',HERE/'smallville_benchmark.py']
 write(ROOT/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),sources={str(s):sha(s) for s in sources},model_calls=0));rows=select_records(GLOBAL/'longmemeval_s_cleaned.json',p['cases']);common=json.loads((HERE.parent/'studies/longmemeval-codex-protocol-002.json').read_text())['reader_common'];registry=[]
 write(ROOT/'started.json',dict(pid=os.getpid(),no_retry=True))
 try:
  embed=LocalEmbeddings(GLOBAL,ROOT/'embedding-inferences.jsonl')
  for index,key in enumerate(p['cases']):
   for f,h in json.loads((ROOT/'manifest.json').read_text())['sources'].items():
    if sha(Path(f))!=h:raise ValueError('Frozen source changed')
   row=rows[key];episodes=history(row);case=ROOT/f'case-{index:02d}';case.mkdir();build=case/'build';build.mkdir();calls=NativeCalls(build,cap=p['per_case_call_cap']);m=CompatibleMemoryV3(case/'memory',embed,calls,dict(name='TTGL agent',currently='Maintaining useful evidence from prior conversations.'));reflections=[]
   try:
    for e in sorted(episodes,key=lambda e:(parse_date(json.loads(e['body'])['date']),e['id'])):
     when=parse_date(json.loads(e['body'])['date']);body=e['body'].replace('(',r'\u0028').replace(')',r'\u0029')
     m.observe(body,'TTGL agent','read',e['id'],when);thoughts=m.reflect_if_due(when)
     if thoughts:reflections.append(dict(when=when.isoformat(),thoughts=len(thoughts)))
     (case/'build-progress.json').write_text(json.dumps(dict(observations=len(m.memory.seq_event),thoughts=len(m.memory.seq_thought),completed_calls=len(calls.registry),natural_remaining=m.scratch.importance_trigger_curr)))
     print('memory observation',index,len(m.memory.seq_event),'calls',len(calls.registry),flush=True)
   except (ValueError,KeyError,TypeError,SyntaxError) as e:
    # Callback process/transport uncertainty raises RuntimeError and stops whole block.
    write(case/'memory-contract-failure.json',dict(error=type(e).__name__,message=str(e),completed_calls=len(calls.registry),no_retry=True));registry.append(dict(case=index,question_id=key,condition='original_memory',memory_failed=True));continue
   hits=m.retrieve(row['question'],parse_date(row['question_date']),8)
   write(case/'retrieval.json',[dict(id=n.node_id,text=n.embedding_key,evidence=n.filling,kind=n.type) for n in hits]);write(case/'memory-build.json',dict(observations=len(episodes),thoughts=len(m.memory.seq_thought),natural_reflections=reflections,natural_remaining=m.scratch.importance_trigger_curr,completed_calls=len(calls.registry)))
   cell=case/'reader';cell.mkdir();hist=cell/'work/history';hist.mkdir(parents=True)
   for e in episodes:(hist/(e['id']+'.txt')).write_text(e['body'])
   sealed={str(f):sha(f) for f in hist.iterdir()};outside=case/'outside-sentinel.txt';outside.write_text('original-reader-outside-'+key);boundary(cell/'work',outside,cell)
   prompt=common+'\n\n'+json.dumps(dict(question_date=row['question_date'],question=row['question']),ensure_ascii=False)+'\nAutomatically retrieved fallible memory records; full source files remain available:\n'+json.dumps([dict(text=n.embedding_key,evidence=n.filling) for n in hits],ensure_ascii=False)
   reader=NativeReaders(cell,cap=1);reader(prompt,'reader')
   if any(sha(Path(f))!=h for f,h in sealed.items()):raise ValueError('Raw evidence modified')
   registry.append(dict(case=index,question_id=key,condition='original_memory',memory_failed=False,session_id=reader.registry[0]['session_id']));(ROOT/'progress.json').write_text(json.dumps(registry,indent=2))
  write(ROOT/'readers-complete.json',registry)
  for item in registry:
   case=ROOT/f'case-{item["case"]:02d}'
   if item['memory_failed']:write(case/'grade.json',dict(passed=False,kind='completed memory-contract failure'));continue
   judge=case/'judge';judge.mkdir();calls=NativeCalls(judge,cap=1);label=calls(judge_prompt(rows[item['question_id']],(case/'reader/call-001/answer.txt').read_text()),'judge').strip().lower()
   if label not in ('yes','no'):raise ValueError('Invalid judge label')
   write(case/'grade.json',dict(passed=label=='yes',kind='blinded adapted LongMemEval model judge'))
  write(ROOT/'complete.json',dict(cases=3,usage_audit_pending=True));print('Original-style benchmark block complete; accounting pending.',flush=True)
 except BaseException as e:
  write(ROOT/'stopped.json',dict(error=type(e).__name__,message=str(e),completed_readers=len(registry),no_retry=True));raise
if __name__=='__main__':main()
