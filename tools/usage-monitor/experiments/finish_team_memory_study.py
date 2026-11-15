#!/usr/bin/env python3
"""One publication phase attached to the existing registered queue process.

No scheduler, model calls, worker creation, retries or queue restart. Imports of
analysis/plotting happen in fresh subprocesses after the generation process ends.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import select
import subprocess
import sys


def save(path,value):
    with path.open('x') as stream:json.dump(value,stream,indent=2);stream.write('\n')


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def finish(root,protocol,config,output,plot_runtime,plot_manifest,owner_receipt,queue_script,phase):
    if Path(owner_receipt).name!=owner_receipt or Path(queue_script).name!=queue_script or not phase.isdigit():
        raise ValueError('Invalid owned process/phase names')
    here=Path(__file__).resolve().parent;owner=json.loads((root/owner_receipt).read_text());pid=owner['pid']
    if sha(config)!=owner['config_sha256']:raise ValueError('Owned configuration mismatch')
    command=Path(f'/proc/{pid}/cmdline')
    if command.exists():
        args=[x.decode() for x in command.read_bytes().split(b'\0') if x]
        if not any(Path(x).name==queue_script for x in args) or '--root' not in args:
            raise ValueError('This is not the owned generation process')
        actual=Path(args[args.index('--root')+1])
        if not actual.is_absolute():actual=Path(f'/proc/{pid}/cwd').resolve()/actual
        if actual.resolve()!=root.resolve():raise ValueError('Owned root mismatch')
    save(root/f'publication-phase-started-{phase}.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),queue_pid=pid,
        model_calls=0,recurring=False,queue_restart_supported=False))
    try:
        if command.exists():
            try:fd=os.pidfd_open(pid)
            except ProcessLookupError:fd=None
            if fd is not None:
                try:select.select([fd],[],[])
                finally:os.close(fd)
        def run(name,arguments,env=None):
            subprocess.run([sys.executable,'-S',str(here/name),*arguments],env=env,check=True)
        if not (root/'completion.json').exists():
            run('analyze_team_memory_extension.py',['--root',str(root),'--protocol',str(protocol),'--output',str(output)])
            save(root/f'publication-phase-stopped-{phase}.json',dict(at=datetime.now(timezone.utc).isoformat(),reason='Generation incomplete; only actual progress exported',model_calls=0))
            return
        run('finalize_team_memory_results.py',['--root',str(root),'--protocol',str(protocol),'--config',str(config),'--output',str(output)])
        manifest=json.loads(plot_manifest.read_text())
        if Path(manifest['target']).resolve()!=plot_runtime.resolve():raise ValueError('Plot runtime receipt mismatch')
        for name,expected in manifest['files'].items():
            path=plot_runtime/name
            if sha(path)!=expected:raise ValueError('Plot runtime changed')
        env={**os.environ,'PYTHONPATH':str(plot_runtime),'NO_LXML':'1','PYTHONDONTWRITEBYTECODE':'1'}
        run('plot_team_memory_extension.py',['--results',str(output/'memory-aware-results.json'),'--output',str(output/'figures')],env)
        run('update_team_memory_paper.py',['--output',str(output)])
        save(root/f'publication-phase-completed-{phase}.json',dict(at=datetime.now(timezone.utc).isoformat(),model_calls=0,
            queue_restarted=False,output=str(output),requires_editorial_review=True,
            output_sha256={name:sha(output/name) for name in ['paper.md','README.md','memory-aware-results.json','memory-aware-final-audit.json','memory-aware-cells.csv']}))
        print('All56 ended; final archive/runtime audit, figures and paper draft written. Editorial review required.',flush=True)
    except BaseException as error:
        path=root/f'publication-phase-failed-{phase}.json'
        if not path.exists():save(path,dict(at=datetime.now(timezone.utc).isoformat(),error=repr(error),model_calls=0,automatic_retries=0))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('root','protocol','config','output','plot-runtime','plot-manifest'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--owner-receipt',default='continuation-005-started.json')
    p.add_argument('--queue-script',default='continue_team_memory_text_runtime_v6.py')
    p.add_argument('--phase',default='004')
    a=p.parse_args();finish(a.root.resolve(),a.protocol.resolve(),a.config.resolve(),a.output.resolve(),a.plot_runtime.resolve(),a.plot_manifest.resolve(),a.owner_receipt,a.queue_script,a.phase)
