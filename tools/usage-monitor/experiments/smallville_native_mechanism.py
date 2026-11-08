#!/usr/bin/env python3
"""Registered synthetic original-style memory mechanism; not benchmark efficacy."""
import argparse
from datetime import datetime,timedelta,timezone
import hashlib,json,os,shutil
from pathlib import Path
from cost_context_study import REPO,PRICING
from longmemeval_codex_trial import native_command,run_process
from native_jsonl import validate_native_completion
from smallville_memory import SmallvilleMemory,VENDOR
from smallville_local_embeddings import LocalEmbeddings
HERE=Path(__file__).resolve().parent;GLOBAL=REPO/'work/security/context-memory-20261107';ROOT=GLOBAL/'smallville-native-mechanism-001';PROTOCOL=HERE.parent/'studies/smallville-native-mechanism-protocol-001.json'
EVENTS=[
 'TTGL agent observed that journal import passes LF input but fails CRLF input with a record-shape error.',
 'TTGL agent changed the input filename; the same CRLF parse failure remained, ruling out the filename as its cause.',
 'TTGL agent compared decoded records and found a trailing carriage return left on each CRLF input line.',
 'TTGL agent normalized newlines before parsing; the LF and CRLF checks both passed. The exact recorded fix identifier is normalize_newlines_before_parse.',
 'TTGL agent learned that deleting blank records does not repair the trailing-carriage-return failure.',
 'TTGL agent verified that the newline normalization fix preserves empty-field handling; all three public regression checks passed.'
]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def write(p,v):
 with p.open('x') as f:json.dump(v,f,indent=2);f.write('\n')
def prepare():
 os.umask(0o077);ROOT.mkdir();(ROOT/'work').mkdir();(ROOT/'protocol.json').write_bytes(PROTOCOL.read_bytes());write(ROOT/'events.json',EVENTS)
 paths=[Path(__file__),HERE/'smallville_memory.py',HERE/'smallville_local_embeddings.py',HERE/'native_jsonl.py',HERE/'longmemeval_codex_trial.py',HERE/'longitudinal_memory_trial.py',PRICING,PROTOCOL,ROOT/'events.json',GLOBAL/'embedding-model-receipt.json',GLOBAL/'mem0-fastembed-resolved.json',Path(shutil.which('codex')).resolve()]
 paths += [p for p in VENDOR.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
 write(ROOT/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),sources={str(p):sha(p) for p in paths},runtime_path=str(Path(shutil.which('codex')).resolve()),model_calls=0,software_controls=10))
 print('Prepared6synthetic observations; max48native calls;0models invoked.')
def run():
 manifest=json.loads((ROOT/'manifest.json').read_text())
 if any(sha(Path(p))!=h for p,h in manifest['sources'].items()):raise ValueError('Frozen source changed')
 write(ROOT/'started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),no_retry=True))
 registry=[]
 def complete(prompt,role):
  if len(registry)>=48:raise ValueError('Registered model cap')
  cell=ROOT/f'call-{len(registry)+1:03d}';cell.mkdir();(cell/'prompt.txt').write_text(prompt)
  command=native_command(ROOT/'work',cell,'gpt-6.1-sol');index=command.index('-s');del command[index:index+2];command[-1:-1]=['--ignore-rules']
  for feature in ('multi_agent','plugins','apps','browser_use','computer_use','image_generation','workspace_dependencies','view_image','shell_tool','unified_exec','apply_patch_freeform'):
   command[-1:-1]=['--disable',feature]
  settings={'project_doc_max_bytes':0,'features.skip_host_skill_discovery':True,'suppress_unstable_features_warning':True,'features.enable_request_compression':False,'model_provider':'openai','openai_base_url':'http://127.0.0.1:8338/backend-api/codex','default_permissions':'ttgl_smallville','permissions.ttgl_smallville.filesystem':{':root':'deny',':minimal':'read',str(ROOT/'work'):'read',manifest['runtime_path']:'read'},'permissions.ttgl_smallville.network.enabled':False,'web_search':'disabled'}
  for key,value in settings.items():
   encoded='{'+','.join(json.dumps(k)+'='+json.dumps(v) for k,v in value.items())+'}' if isinstance(value,dict) else json.dumps(value)
   command[-1:-1]=['-c',key+'='+encoded]
  write(cell/'started.json',dict(role=role,at=datetime.now(timezone.utc).isoformat(),prompt_sha256=sha(cell/'prompt.txt'),no_process_retry=True))
  run_process(command,prompt,cell,600);sid=validate_native_completion(cell,no_tools=True)
  row=dict(cell=cell.name,session_id=sid,role=role);registry.append(row);write(cell/'complete.json',row)
  (ROOT/'registry.json').write_text(json.dumps(registry,indent=2)+'\n')
  return (cell/'answer.txt').read_text()
 try:
  embed=LocalEmbeddings(GLOBAL,ROOT/'embedding-inferences.jsonl');memory=SmallvilleMemory(ROOT/'memory',embed,complete,dict(name='TTGL agent',currently='Diagnosing an assigned journal import problem.'))
  when=datetime(2026,1,1,9)
  for index,event in enumerate(json.loads((ROOT/'events.json').read_text())):memory.observe(event,'TTGL agent','observed','journal importer',when+timedelta(minutes=index))
  memory.retrieve('What repaired the CRLF parse failure?',when+timedelta(minutes=7),3)
  natural_remaining=memory.scratch.importance_trigger_curr
  # Explicit diagnostic only. Do not pretend six rated events naturally consumed150.
  forced=natural_remaining>0
  if forced:
   memory.audit('diagnostic_forced_reflection',original_remaining=natural_remaining,forced_remaining=0)
   memory.scratch.importance_trigger_curr=0
  thoughts=memory.reflect_if_due(when+timedelta(minutes=8))
  if len(thoughts)!=15 or any(not n.filling for n in thoughts):raise ValueError('Reflection mechanics incomplete')
  hits=memory.retrieve('What is the exact recorded fix identifier for the CRLF parse failure?',when+timedelta(minutes=9),3)
  (ROOT/'retrieved-example.json').write_text(json.dumps([dict(id=n.node_id,kind=n.type,text=n.embedding_key,evidence=n.filling,poignancy=n.poignancy) for n in hits],indent=2)+'\n')
  answer=complete('Use only these fallible memory records to recall the exact recorded fix identifier. Reply with only that identifier; no tools or prose.\n'+json.dumps([n.embedding_key for n in hits]),'diagnostic_reader').strip()
  exact=answer=='normalize_newlines_before_parse'
  reloaded=SmallvilleMemory(ROOT/'memory',embed,complete,dict(name='TTGL agent'))
  if len(reloaded.memory.id_to_node)!=21:raise ValueError('Persisted memory node count mismatch')
  write(ROOT/'complete.json',dict(model_processes=len(registry),observations=6,thoughts=15,persisted_nodes=21,natural_remaining=natural_remaining,reflection_trigger_forced=forced,reader_exact=exact,usage_audit_pending=True,scope='Synthetic mechanism, not benchmark/savings evidence. Original source semantics, modern Codex/local BGE and explicit safety/transport adaptations.'))
  print('Smallville mechanism complete; inspect memories, reconcile all inference, no savings claim.',flush=True)
 except BaseException as error:
  write(ROOT/'stopped.json',dict(error=type(error).__name__,message=str(error),no_retry=True,completed_model_processes=len(registry)));raise
if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('action',choices=['prepare','run']);globals()[parser.parse_args().action]()
