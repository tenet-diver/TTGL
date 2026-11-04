from pathlib import Path
import subprocess,json,time,shutil
base=Path.home()/'Library/Application Support/TTGL AI Observer';dest=base/'expanded-history'
roots=[Path.home()/'.codex/archived_sessions',Path.home()/'.codex/sessions'];chosen={}
for root in roots:
 for f in root.rglob('*.jsonl*'):
  if not (f.name.endswith('.jsonl') or f.name.endswith('.jsonl.zst')):continue
  key=f.name.removesuffix('.zst');old=chosen.get(key)
  if old is None or f.name.endswith('.jsonl') or (root.name=='sessions' and not old.name.endswith('.jsonl')):chosen[key]=f
fs=sorted([f for f in chosen.values() if f.name.endswith('.zst')],key=lambda x:x.stat().st_mtime,reverse=True)
state={'total':len(fs),'done':0,'bytes':0,'errors':[]}
for f in fs:
 out=dest/f.name.removesuffix('.zst');tmp=out.with_suffix('.partial')
 try:
  if shutil.disk_usage(base).free<6*1024**3:raise RuntimeError('Less than 6 GiB free; stopped expansion')
  if not out.exists():
   with tmp.open('wb') as stream:subprocess.run(['zstd','-dc','--',str(f)],stdout=stream,check=True)
   tmp.replace(out)
  state['bytes']+=out.stat().st_size
 except Exception as e:state['errors'].append({'file':f.name,'error':str(e)});break
 state['done']+=1
 (base/'expansion-status.json').write_text(json.dumps(state))
print(json.dumps(state),flush=True)
