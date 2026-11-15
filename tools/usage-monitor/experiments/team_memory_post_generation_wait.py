"""Passive bounded wait for already-started maintenance processes; no signals."""
import json
from pathlib import Path
import time


def active_maintenance(root,proc=Path('/proc')):
    active=[]
    for intent in sorted(root.rglob('call-*/intent.json')):
        started=intent.parent/'started.json'
        if not started.exists():continue
        pid=json.loads(started.read_text())['pid'];command=proc/str(pid)/'cmdline'
        try:body=command.read_bytes()
        except FileNotFoundError:continue
        if str(intent.parent).encode() in body:active.append(pid)
    return active


def wait_for_maintenance(root,limit=180):
    from codex_team_probe import save
    started=time.monotonic();observed=set()
    while True:
        active=active_maintenance(root);observed.update(active)
        if not active:break
        if time.monotonic()-started>=limit:
            raise TimeoutError('Already-started maintenance remains active; preserve and audit, never retry')
        time.sleep(.2)
    result=dict(model_calls=0,seconds=time.monotonic()-started,already_started_processes_observed=len(observed),
        limit_seconds=limit,signals_sent=0,processes_restarted=0,
        scope='After coding/source seal and broker close; finite passive drain, not extra coding budget. All in-flight inference remains charged.')
    save(root/'post-generation-maintenance-wait.json',result)
    return result
