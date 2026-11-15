#!/usr/bin/env python3
"""Publication phase attached to one existing study process; no new inference.

Wait for the owned queue process to exit, then publish its actual final/stop
state. This is not a scheduler, worker, retry loop or general monitoring service.
It cannot restart a queue or launch a model.
"""
import argparse
import json
import os
from pathlib import Path
import select

from analyze_team_memory_extension import analyze,publish
from codex_team_probe import save


def finish(root,protocol,output):
    started=json.loads((root/'queue-started.json').read_text());pid=started['pid']
    command=Path(f'/proc/{pid}/cmdline')
    if command.exists():
        args=[v.decode() for v in command.read_bytes().split(b'\0') if v]
        if not any('codex_team_memory_queue.py' in v for v in args) or '--root' not in args:
            raise ValueError('PID does not identify the owned study queue')
        target=Path(args[args.index('--root')+1])
        if not target.is_absolute():target=Path(f'/proc/{pid}/cwd').resolve()/target
        if target.resolve()!=root.resolve():raise ValueError('Queue ownership mismatch')
        try:fd=os.pidfd_open(pid)
        except ProcessLookupError:fd=None
        if fd is not None:
            try:select.select([fd],[],[])
            finally:os.close(fd)
    value=analyze(root,protocol);publish(value,output)
    save(root/'publication-completed.json',dict(state=value['state'],completed=value['completed'],planned=value['planned'],
        output=str(output),model_calls=0,queue_restarted=False))
    print(json.dumps({k:value[k] for k in ('state','completed','planned')}),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();finish(a.root.resolve(),a.protocol.resolve(),a.output.resolve())
