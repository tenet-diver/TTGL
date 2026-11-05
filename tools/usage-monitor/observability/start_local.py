#!/usr/bin/env python3
"""Run and supervise the local workspace, capture adapter and Langfuse exporter.

Requires the prepared/pulled Langfuse stack. Never installs packages or pulls images.
"""
import argparse
import fcntl
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.request

HERE = Path(__file__).resolve().parent
DEFAULTS = json.loads((HERE.parent / 'config/defaults.json').read_text())


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--state', type=Path, required=True)
    parser.add_argument('--workspace-data', type=Path, required=True)
    parser.add_argument('--codex-root', type=Path, default=Path.home() / '.codex')
    parser.add_argument('--langfuse-url', default='http://localhost:3000')
    args = parser.parse_args()
    args.state = args.state.resolve()
    args.workspace_data = args.workspace_data.resolve()
    args.state.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.umask(0o077)
    lock = (args.state / 'supervisor.lock').open('w')
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    subprocess.run(['docker', 'compose', '-f', str(args.state / 'compose.json'), 'up', '-d', '--wait', '--wait-timeout', '180'], check=True)
    # Compose health is insufficient when an image has no healthcheck.
    for attempt in range(36):
        try:
            with urllib.request.urlopen('http://127.0.0.1:3000/api/public/health', timeout=5) as response:
                if response.status == 200:
                    break
        except OSError:
            pass
        time.sleep(5)
    else:
        raise RuntimeError('Langfuse HTTP health did not become ready')
    commands = {
        'workspace': [sys.executable, str(HERE / 'workspace.py'), '--data', str(args.workspace_data), '--codex-root', str(args.codex_root), '--langfuse-url', args.langfuse_url, '--capture-root', str(args.state / 'captures')],
        'capture': [sys.executable, str(HERE / 'capture_proxy.py'), '--destination', str(args.state / 'captures'), '--collection-state', str(args.workspace_data / 'workspace.sqlite')],
        'collector': [sys.executable, str(HERE.parent / 'langfuse/live_export.py'), '--credentials', str(args.state / 'local-access.json'), '--state', str(args.state / 'native-export'), '--collection-state', str(args.workspace_data / 'workspace.sqlite'), '--capture-root', str(args.state / 'captures'), '--codex-root', str(args.codex_root), '--watch'],
    }
    processes, handles = {}, {}
    stopping = False
    def stop(signum, frame):
        nonlocal stopping
        stopping = True
    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        while not stopping:
            for name, command in commands.items():
                if name in processes and processes[name].poll() is None:
                    continue
                if name in handles:
                    handles[name].close()
                log = args.state / (name + '.log')
                if log.exists() and log.stat().st_size > 10 * 1024 * 1024:
                    log.replace(log.with_suffix('.previous.log'))
                handles[name] = log.open('a')
                processes[name] = subprocess.Popen(command, stdout=handles[name], stderr=subprocess.STDOUT)
                print(f'Started {name}: {processes[name].pid}', flush=True)
            runtime = dict(pid=os.getpid(), children={name: p.pid for name, p in processes.items()},
                           langfuse_url=args.langfuse_url, workspace_port=8766, capture_port=8317)
            (args.state / 'runtime.json').write_text(json.dumps(runtime, indent=2))
            time.sleep(DEFAULTS['collection']['supervisor_poll_seconds'])
    finally:
        for process in processes.values():
            if process.poll() is None:
                process.terminate()
        for process in processes.values():
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
        for handle in handles.values():
            handle.close()
        print('Stopped local capture/analysis processes. Docker data and services are preserved.', flush=True)


if __name__ == '__main__':
    main()
