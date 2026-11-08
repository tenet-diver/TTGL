"""Freeze actor processes and grade a separate sealed copy, not live writable state."""
import base64,hashlib,json,subprocess
from pathlib import Path
from lhtb_actor_runtime_v2 import UnknownActor as Previous
from lhtb_actor_runtime import args,mount,IMAGE,SOURCE,write,sha
class UnknownActor(Previous):
 def __init__(self,*a,**kw):
  super().__init__(*a,**kw)
  self.app.chmod(0o777);self.history.chmod(0o755);self.grade_logs.chmod(0o777)
 def admin_archive(self):
  subprocess.run(['docker','pause',self.name],check=True,capture_output=True,timeout=20)
  code="from pathlib import Path;import base64,json;p=Path('/opt/cfg');files=[x for x in p.rglob('*') if x.is_file()];assert all(x.stat().st_size<=33554432 for x in files);print(json.dumps({str(x.relative_to(p)):base64.b64encode(x.read_bytes()).decode() for x in files}))"
  raw=subprocess.check_output(['docker','run','--rm']+args('0:0')+mount(self.cfg,'/opt/cfg',True)+[IMAGE,'python3','-I','-S','-c',code],timeout=40)
  archive=self.cell/'sealed-cfg.json';archive.write_bytes(raw);archive.chmod(0o600);values=json.loads(raw);hashes={name:hashlib.sha256(base64.b64decode(v)).hexdigest() for name,v in values.items()}
  if hashes['cfgd_data.json']!=sha(SOURCE/'environment/harness/cfgd_data.json'):raise ValueError('Private oracle input changed')
  modified=[p for p,h in self.original.items() if hashes.get(p)!=h and p!='engine.py']
  if modified:raise ValueError('Protected harness changed:'+str(modified))
  target=self.work/'sealed-cfg';target.mkdir(mode=0o755);target.chmod(0o755)
  for name,value in values.items():
   rel=Path(name)
   if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe sealed path')
   p=target/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(value));p.chmod(0o600 if p.name in ('.key','cfgd_data.json') else 0o644)
  for p in target.rglob('*'):
   if p.is_dir():p.chmod(0o755)
  init="from pathlib import Path;import os;p=Path('/init');os.chown(p,0,0);[os.chown(x,0,0) for x in p.rglob('*')]"
  subprocess.run(['docker','run','--rm']+args('0:0',init=True)+mount(target,'/init')+[IMAGE,'python3','-I','-S','-c',init],check=True,capture_output=True,timeout=40)
  write(self.cell/'sealed-state.json',dict(files=hashes,archive_sha256=sha(archive),actor_paused_during_archive=True,grading_uses_separate_sealed_copy=True,private_values_printed=False))
  self.live_cfg=self.cfg;self.cfg=target
  return hashes
 def close(self):
  r=subprocess.run(['docker','inspect','--format','{{.State.Paused}}',self.name],capture_output=True,text=True,timeout=15)
  if r.returncode==0 and r.stdout.strip()=='true':subprocess.run(['docker','unpause',self.name],capture_output=True,check=True,timeout=15)
  super().close()
