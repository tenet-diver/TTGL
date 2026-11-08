"""Bounded readers with raw-evidence fallback in isolated work directories."""
from datetime import datetime,timezone
import hashlib,json,shutil
from pathlib import Path
from longmemeval_codex_trial import native_command,run_process
from native_jsonl import validate_native_completion
class NativeReaders:
 def __init__(self,root,cap=48,replay=None):
  self.root=Path(root);self.cap=cap;self.registry=[];self.replay=replay
  (self.root/'work').mkdir(parents=True,exist_ok=True)
 def __call__(self,prompt,role):
  if self.replay:
   prior=self.replay;self.replay=None
   if (prior/'prompt.txt').read_text()!=prompt:raise ValueError('Prior prompt differs; no silent resubmission')
   validate_native_completion(prior,no_tools=False)
   (self.root/'reused-call.json').write_text(json.dumps(dict(source=str(prior),role=role,prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest()),indent=2))
   return (prior/'answer.txt').read_text()
  if len(self.registry)>=self.cap:raise ValueError('Registered call cap')
  cell=self.root/f'call-{len(self.registry)+1:03d}';cell.mkdir();(cell/'prompt.txt').write_text(prompt)
  command=native_command(self.root/'work',cell,'gpt-6.1-sol');i=command.index('-s');del command[i:i+2];command[-1:-1]=['--ignore-rules']
  for feature in ('multi_agent','plugins','apps','browser_use','computer_use','image_generation','workspace_dependencies','view_image','apply_patch_freeform'):command[-1:-1]=['--disable',feature]
  runtime=str(Path(shutil.which('codex')).resolve());settings={'project_doc_max_bytes':0,'features.skip_host_skill_discovery':True,'suppress_unstable_features_warning':True,'features.enable_request_compression':False,'model_provider':'openai','openai_base_url':'http://127.0.0.1:8338/backend-api/codex','default_permissions':'ttgl_smallville','permissions.ttgl_smallville.filesystem':{':root':'deny',':minimal':'read',str(self.root/'work'):'read',runtime:'read'},'permissions.ttgl_smallville.network.enabled':False,'web_search':'disabled'}
  for key,value in settings.items():
   encoded='{'+','.join(json.dumps(k)+'='+json.dumps(v) for k,v in value.items())+'}' if isinstance(value,dict) else json.dumps(value)
   command[-1:-1]=['-c',key+'='+encoded]
  (cell/'intent.json').write_text(json.dumps(dict(role=role,at=datetime.now(timezone.utc).isoformat(),prompt_sha256=hashlib.sha256(prompt.encode()).hexdigest())))
  run_process(command,prompt,cell,600);sid=validate_native_completion(cell,no_tools=False)
  row=dict(cell=cell.name,session_id=sid,role=role);self.registry.append(row)
  (cell/'complete.json').write_text(json.dumps(row,indent=2));(self.root/'registry.json').write_text(json.dumps(self.registry,indent=2))
  return (cell/'answer.txt').read_text()
