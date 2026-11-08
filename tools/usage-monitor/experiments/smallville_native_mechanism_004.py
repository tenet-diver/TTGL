#!/usr/bin/env python3
"""Registered compatible reflection continuation; no reissue of completed calls."""
from datetime import datetime,timedelta,timezone
from pathlib import Path
import json,shutil,hashlib
from smallville_native_mechanism import GLOBAL,HERE
from smallville_native_runtime import NativeCalls
from smallville_local_embeddings import LocalEmbeddings
from smallville_compat import CompatibleMemory
ROOT=GLOBAL/'smallville-native-mechanism-004';PRIOR=GLOBAL/'smallville-native-mechanism-003'
def main():
 ROOT.mkdir();protocol=HERE.parent/'studies/smallville-native-mechanism-protocol-004.json';(ROOT/'protocol.json').write_bytes(protocol.read_bytes())
 sources=[Path(__file__),HERE/'smallville_compat.py',HERE/'smallville_native_runtime.py',protocol]
 (ROOT/'manifest.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),sources={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}),indent=2))
 (ROOT/'started.json').write_text(json.dumps(dict(no_retry=True)))
 shutil.copytree(PRIOR/'memory',ROOT/'memory')
 complete=NativeCalls(ROOT,cap=34,replay=PRIOR/'call-007')
 try:
  embed=LocalEmbeddings(GLOBAL,ROOT/'embedding-inferences.jsonl');memory=CompatibleMemory(ROOT/'memory',embed,complete,dict(name='TTGL agent',currently='Diagnosing an assigned journal import problem.'),restore_last_access=True)
  when=datetime(2026,1,1,9);remaining=memory.scratch.importance_trigger_curr
  memory.scratch.importance_trigger_curr=0;memory.audit('diagnostic_forced_reflection',original_remaining=remaining,forced_remaining=0)
  thoughts=memory.reflect_if_due(when+timedelta(minutes=8))
  if len(thoughts)!=15 or any(not n.filling for n in thoughts):raise ValueError('Reflection mechanics incomplete')
  hits=memory.retrieve('What is the exact recorded fix identifier for the CRLF parse failure?',when+timedelta(minutes=9),3)
  (ROOT/'retrieved-example.json').write_text(json.dumps([dict(id=n.node_id,kind=n.type,text=n.embedding_key,evidence=n.filling,poignancy=n.poignancy) for n in hits],indent=2))
  answer=complete('Use only these fallible memory records to recall the exact recorded fix identifier. Reply with only that identifier; no tools or prose.\n'+json.dumps([n.embedding_key for n in hits]),'diagnostic_reader').strip()
  result=dict(observations=6,thoughts=15,persisted_nodes=len(memory.memory.id_to_node),new_model_calls=len(complete.registry),prior_model_calls=7,reader_exact=answer=='normalize_newlines_before_parse',reflection_trigger_forced=True,natural_remaining=remaining,compatibility='Accept JSON list as well as original list-string; exact prior focal output reused. Explicit access-time restoration continues prior in-memory state.',usage_audit_pending=True,scope='Synthetic mechanism only; not benchmark savings.')
  (ROOT/'complete.json').write_text(json.dumps(result,indent=2));print(json.dumps(result),flush=True)
 except BaseException as e:
  (ROOT/'stopped.json').write_text(json.dumps(dict(error=type(e).__name__,message=str(e),completed_calls=len(complete.registry),no_retry=True),indent=2));raise
if __name__=='__main__':main()
