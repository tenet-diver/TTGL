#!/usr/bin/env python3
"""Project local rollout usage records for AI Observer; never modifies source files."""
import json,time,os
from pathlib import Path
base=Path.home()/'Library/Application Support/TTGL AI Observer';target=base/'usage-history';target.mkdir(exist_ok=True);os.chmod(target,0o700)
state={}
while True:
 chosen={}
 # Expanded archives are immutable; active plain sources override copies.
 for root in [base/'expanded-history',Path.home()/'.codex/archived_sessions',Path.home()/'.codex/sessions']:
  for f in root.rglob('*.jsonl'):chosen[f.name]=f
 progress={'total':len(chosen),'done':0,'projected_records':0,'errors':[]}
 for name,f in sorted(chosen.items()):
  stat=f.stat();key=(stat.st_size,stat.st_mtime_ns);dest=target/name
  if state.get(name)==key:progress['done']+=1;continue
  try:
   tmp=dest.with_suffix('.partial');n=0
   with f.open('rb') as src,tmp.open('wb') as out:
    while True:
     line=src.readline(32*1024*1024+1)
     if not line:break
     if len(line)>32*1024*1024:
      while line and not line.endswith(b'\n'):line=src.readline(32*1024*1024+1)
      continue
     if not line.endswith(b'\n'):break
     head=line[:350]
     if not any(x in head for x in [b'"session_meta"',b'"turn_context"',b'"token_count"',b'"token_usage_record"',b'"compacted"']):continue
     try:r=json.loads(line)
     except ValueError:continue
     typ=r.get('type');p=r.get('payload') or {}
     if typ=='session_meta':r['payload']={k:p[k] for k in ['id','timestamp','cwd','originator','cli_version','source','model_provider','forked_from_id','git'] if k in p}
     elif typ=='turn_context':r['payload']={k:p[k] for k in ['model','turn_id','root_turn_id','cwd','effort'] if k in p}
     elif typ=='event_msg':
      if p.get('type')!='token_count':continue
      r['payload']={k:p[k] for k in ['type','info'] if k in p}
     elif typ not in ['token_usage_record','compacted']:continue
     out.write(json.dumps(r,separators=(',',':')).encode()+b'\n');n+=1
   # Append to growing projected logs so the observer's byte cursor remains valid.
   # Unchanged historical files are not touched on subsequent scans.
   if dest.exists() and tmp.stat().st_size>=dest.stat().st_size:
    with dest.open('rb') as old,tmp.open('rb') as new:
     prefix=True
     while True:
      a=old.read(1024*1024)
      if not a:break
      if new.read(len(a))!=a:prefix=False;break
    if prefix:
     offset=dest.stat().st_size
     with tmp.open('rb') as new,dest.open('ab') as old:
      new.seek(offset)
      while b:=new.read(1024*1024):old.write(b)
     tmp.unlink()
    else:raise RuntimeError('Projection prefix changed; retained old copy for audit')
   else:tmp.replace(dest)
   state[name]=key;progress['projected_records']+=n
  except Exception as e:progress['errors'].append({'file':name,'error':str(e)})
  progress['done']+=1
  (base/'projection-status.json').write_text(json.dumps(progress))
 (base/'projection-status.json').write_text(json.dumps(progress));time.sleep(20)
