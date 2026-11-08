#!/usr/bin/env python3
"""Registered matched memory-QA development block, no hidden validation access."""
from datetime import datetime,timezone
import hashlib,json,os,shutil,subprocess,sys,time
from pathlib import Path
from smallville_native_mechanism import GLOBAL,HERE
from smallville_local_embeddings import LocalEmbeddings
from smallville_evidence_memory import EvidenceMemory
from smallville_native_readers import NativeReaders
from smallville_native_runtime import NativeCalls
from longmemeval_codex_trial import history,judge_prompt
from json_corpus import select_records
ROOT=GLOBAL/'smallville-validation-001';PROTOCOL=HERE.parent/'studies/smallville-validation-protocol-001.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def boundary(work,outside,cell):
 runtime=str(Path(shutil.which('codex')).resolve())
 settings={'default_permissions':'ttgl_smallville','permissions.ttgl_smallville.filesystem':{':root':'deny',':minimal':'read',str(work):'read',runtime:'read'},'permissions.ttgl_smallville.network.enabled':False}
 cmd=['codex','sandbox','-P','ttgl_smallville','-C',str(work)]
 for k,v in settings.items():
  encoded='{'+','.join(json.dumps(a)+'='+json.dumps(b) for a,b in v.items())+'}' if isinstance(v,dict) else json.dumps(v)
  cmd+=['-c',k+'='+encoded]
 results=[]
 for target in (work/'history/session-0000.txt',outside):
  r=subprocess.run(cmd+['--','/bin/cat',str(target)],capture_output=True,timeout=30)
  results.append(dict(exit_code=r.returncode,bytes=len(r.stdout),exact=r.stdout==target.read_bytes(),stderr=r.stderr.decode(errors='replace')))
 passed=results[0]['exit_code']==0 and results[0]['exact'] and results[1]['exit_code']!=0 and not results[1]['exact']
 write(cell/'boundary.json',dict(passed=passed,results=results,model_calls=0))
 if not passed:raise ValueError('Own reader boundary failed; no model call')
def main():
 os.umask(0o077);ROOT.mkdir();p=json.loads(PROTOCOL.read_text());(ROOT/'protocol.json').write_bytes(PROTOCOL.read_bytes())
 sources=[Path(__file__),HERE/'smallville_evidence_memory.py',HERE/'smallville_native_readers.py',HERE/'smallville_native_runtime.py',HERE/'memory_retrieval.py',PROTOCOL]
 write(ROOT/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),sources={str(s):sha(s) for s in sources},dataset_sha256=sha(GLOBAL/'longmemeval_s_cleaned.json')))
 rows=select_records(GLOBAL/'longmemeval_s_cleaned.json',p['cases']);common=json.loads((HERE.parent/'studies/longmemeval-codex-protocol-002.json').read_text())['reader_common'];registry=[]
 write(ROOT/'started.json',dict(pid=os.getpid(),no_retry=True))
 try:
  embed=LocalEmbeddings(GLOBAL,ROOT/'embedding-inferences.jsonl')
  for i,key in enumerate(p['cases']):
   case=ROOT/f'case-{i:02d}';case.mkdir();row=rows[key];episodes=history(row)
   memory=EvidenceMemory(case/'memory.sqlite',embed);write(case/'memory-build.json',memory.build(episodes))
   # Only after construction does the memory receive a current query.
   retrieval=memory.query(row['question']);write(case/'retrieval.json',retrieval)
   order=p['conditions'][i%3:]+p['conditions'][:i%3]
   for arm in order:
    for s,h in json.loads((ROOT/'manifest.json').read_text())['sources'].items():
     if sha(Path(s))!=h:raise ValueError('Frozen source changed')
    cell=case/arm;cell.mkdir();work=cell/'work';hist=work/'history';hist.mkdir(parents=True)
    for e in episodes:(hist/(e['id']+'.txt')).write_text(e['body'])
    sealed={str(f):sha(f) for f in hist.iterdir()};outside=case/'outside-sentinel.txt'
    if not outside.exists():outside.write_text('reader-outside-boundary-sentinel-'+key)
    boundary(work,outside,cell)
    prompt=common+'\n\n'+json.dumps(dict(question_date=row['question_date'],question=row['question']),ensure_ascii=False)+'\n'
    if arm=='full_history':prompt+='\nComplete supplied history follows:\n'+'\n\n'.join(e['body'] for e in episodes)
    elif arm=='evidence_memory':prompt+='\nAutomatically retrieved exact prior-history excerpts (fallible, full files remain available):\n'+json.dumps(retrieval['hits'],ensure_ascii=False)
    calls=NativeReaders(cell,cap=1);calls(prompt,'reader')
    if any(sha(Path(f))!=h for f,h in sealed.items()):raise ValueError('History changed')
    record=dict(case=i,question_id=key,condition=arm,cell=str(cell.relative_to(ROOT)),session_id=calls.registry[0]['session_id']);registry.append(record);write(cell/'reader.json',record)
    (ROOT/'progress.json').write_text(json.dumps(registry,indent=2));print('reader complete',i,arm,flush=True)
  write(ROOT/'readers-complete.json',registry)
  for item in registry:
   cell=ROOT/item['cell'];answer=(cell/'call-001/answer.txt').read_text();judge=cell/'judge';judge.mkdir();calls=NativeCalls(judge,cap=1);label=calls(judge_prompt(rows[item['question_id']],answer),'judge').strip().lower()
   if label not in ('yes','no'):raise ValueError('Invalid blinded judge output')
   write(cell/'grade.json',dict(passed=label=='yes',kind='blinded adapted LongMemEval model judge; not independently programmatic'))
   print('judge complete',item['case'],item['condition'],label,flush=True)
  write(ROOT/'complete.json',dict(readers=len(registry),judges=len(registry),model_calls=2*len(registry),usage_audit_pending=True))
 except BaseException as e:
  write(ROOT/'stopped.json',dict(error=type(e).__name__,message=str(e),completed_readers=len(registry),no_retry=True));raise
if __name__=='__main__':main()
