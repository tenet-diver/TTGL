#!/usr/bin/env python3
"""Pace append-only usage history into AI Observer's watcher for responsive startup."""
from pathlib import Path
import time,json,os
base=Path.home()/'Library/Application Support/TTGL AI Observer';source=base/'usage-history';dest=base/'observer-stream';dest.mkdir(exist_ok=True);os.chmod(dest,0o700)
while True:
 fs=sorted(source.glob('*.jsonl'),key=lambda p:p.name,reverse=True);copied=0;total=0;complete=0;errors=[]
 for f in fs:
  out=dest/f.name;offset=out.stat().st_size if out.exists() else 0;size=f.stat().st_size;total+=size
  if offset>size:errors.append(f.name+': source shrank; old stream retained');continue
  if offset<size:
   with f.open('rb') as src:
    src.seek(offset);chunk=src.read(512*1024)
    if chunk and not chunk.endswith(b'\n'):chunk+=src.readline()
   if chunk:
    with out.open('ab') as target:target.write(chunk)
    offset+=len(chunk)
    # Avoid queuing all historical files at once; reads can run between batches.
    time.sleep(.35)
  copied+=offset
  if offset>=size:complete+=1
  (base/'feed-status.json').write_text(json.dumps({'files':len(fs),'complete':complete,'copied_bytes':copied,'source_bytes_seen':total,'errors':errors}))
 time.sleep(3)
