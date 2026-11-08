#!/usr/bin/env python3
"""Registered deterministic replay of41 completed outputs; zero new LLM calls."""
from datetime import datetime,timedelta
import hashlib,json
from pathlib import Path
from smallville_native_mechanism import GLOBAL,HERE,EVENTS
from smallville_compat_v3 import CompatibleMemoryV3
from smallville_local_embeddings import LocalEmbeddings
ROOT=GLOBAL/'smallville-native-replay-006'
def main():
 ROOT.mkdir();protocol=HERE.parent/'studies/smallville-replay-protocol-006.json';(ROOT/'protocol.json').write_bytes(protocol.read_bytes())
 inputs=[]
 for version in ('003','004','005'):
  inputs+=sorted((GLOBAL/('smallville-native-mechanism-'+version)).glob('call-*'))
 receipts=[]
 def replay(prompt,role):
  p=inputs[len(receipts)]
  if (p/'prompt.txt').read_text()!=prompt:raise ValueError('Replay prompt mismatch; no model fallback')
  if json.loads((p/'complete.json').read_text())['role']!=role:raise ValueError('Replay role mismatch')
  answer=(p/'answer.txt').read_text();receipts.append(dict(source=str(p),role=role,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest(),answer_sha256=hashlib.sha256(answer.encode()).hexdigest()))
  (ROOT/'replay-receipts.json').write_text(json.dumps(receipts,indent=2));return answer
 try:
  embed=LocalEmbeddings(GLOBAL,ROOT/'embedding-inferences.jsonl');m=CompatibleMemoryV3(ROOT/'memory',embed,replay,dict(name='TTGL agent',currently='Diagnosing an assigned journal import problem.'));when=datetime(2026,1,1,9)
  for i,e in enumerate(EVENTS):m.observe(e,'TTGL agent','observed','journal importer',when+timedelta(minutes=i))
  m.retrieve('What repaired the CRLF parse failure?',when+timedelta(minutes=7),3);natural=m.scratch.importance_trigger_curr;m.scratch.importance_trigger_curr=0
  thoughts=m.reflect_if_due(when+timedelta(minutes=8))
  hits=m.retrieve('What is the exact recorded fix identifier for the CRLF parse failure?',when+timedelta(minutes=9),3)
  answer=replay('Use only these fallible memory records to recall the exact recorded fix identifier. Reply with only that identifier; no tools or prose.\n'+json.dumps([n.embedding_key for n in hits]),'diagnostic_reader').strip()
  if len(receipts)!=41 or any(n.subject!='TTGL agent' or n.predicate.startswith(('(','TTGL')) for n in thoughts):raise ValueError('Replay semantic structure mismatch')
  result=dict(replayed_responses=len(receipts),all_prompts_exact=True,new_model_calls=0,natural_trigger_remaining=natural,thoughts=len(thoughts),all_thought_subject_predicate_shapes_valid=True,reader_exact=answer=='normalize_newlines_before_parse',scope='Replay compatibility correction of existing development responses; no new model-quality or savings evidence; previous failed/corrupt snapshots preserved.')
  (ROOT/'complete.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
 except BaseException as e:
  (ROOT/'stopped.json').write_text(json.dumps(dict(error=type(e).__name__,message=str(e),new_model_calls=0,replayed=len(receipts))));raise
if __name__=='__main__':main()
