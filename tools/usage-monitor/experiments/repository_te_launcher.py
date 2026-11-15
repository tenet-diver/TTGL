"""Scoped TokenEconomizer hook/async CLI transport for the MCP task harness.

Stock prompts, detectors, thresholds and lifecycle remain upstream. Background
workers load the same semantic adapter, with original native logs retained.
"""
from datetime import datetime, timezone
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

from repository_tokeneconomizer_hook import REVIEW, install_adapter, bridge_result


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with path.open('x') as handle:
        json.dump(value, handle, indent=2)


def install():
    for entry in json.loads((REVIEW / 'download-manifest.json').read_text())['files']:
        if hashlib.sha256((REVIEW / 'source' / entry['path']).read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Reviewed upstream source changed')
    original = install_adapter()
    from tokeneconomizer.plugin import hosts
    from tokeneconomizer.plugin.context import LiveContext

    class ScopedCodex(original):
        def tool_call(self, payload):
            try:
                return super().tool_call(payload)
            except ValueError:
                # A phase-closed or unreadable MCP reply is not an executed
                # command and supplies no success bit. Retain it as an unknown
                # original MCP tool instead of inventing a shell outcome.
                return hosts.Host.tool_call(self, payload)

        def mechanism_trace(self, transcript_path, workdir):
            raw = hosts.Codex.mechanism_trace(self, transcript_path, workdir)
            if raw is None:
                return None
            destination = Path(workdir) / ('ttgl-command-evidence-' + str(time.time_ns()) + '.jsonl')
            skipped, count = [], 0
            with destination.open('x') as output:
                for index, line in enumerate(Path(raw).read_text().splitlines()):
                    event = json.loads(line)
                    item = event.get('item', {})
                    if event.get('type') != 'item.completed' or item.get('type') != 'mcp_tool_call' or item.get('server') != 'ttgl_task' or item.get('tool') != 'terminal':
                        continue
                    try:
                        frame = bridge_result(item.get('result'))
                    except (ValueError, TypeError):
                        skipped.append(dict(source_item=item.get('id'), reason='Unknown/non-executed command result; no success inferred'))
                        continue
                    args = item.get('arguments') or {}
                    args = json.loads(args) if isinstance(args, str) else args
                    provenance = dict(source=raw, source_line=index, source_item=item['id'],
                                      schema='Claude-compatible semantic interchange; actual source is native MCP, no usage invented')
                    entries = [dict(type='assistant', message=dict(content=[dict(type='tool_use',
                        id=item['id'], name='bash', input=args)]), ttgl_derivation=provenance),
                        dict(type='user', message=dict(content=[dict(type='tool_result', tool_use_id=item['id'],
                            content=frame['stdout'] + frame['stderr'], is_error=frame['exit_code'] != 0)]), ttgl_derivation=provenance)]
                    for entry in entries:
                        output.write(json.dumps(entry) + '\n')
                    count += 1
            write(destination.with_suffix('.receipt.json'), dict(source=raw, known_commands=count, skipped=skipped, original_retained=True))
            return str(destination)

    hosts.HOSTS['codex'] = ScopedCodex

    def spawn(ctx, argv, log_name):
        if ctx.host.name != 'codex':
            raise ValueError('This adapter is scoped to the owned Codex experiment')
        env = dict(ctx.env)
        env['PYTHONPATH'] = str(Path(__file__).parent) + os.pathsep + str(REVIEW / 'source')
        env['PYTHONUTF8'] = '1'
        receipt = Path(ctx.store.ensure('ttgl-jobs')) / uuid.uuid4().hex
        receipt.mkdir(mode=0o700)
        env['TTGL_TE_JOB_RECEIPT'] = str(receipt)
        cmd = [sys.executable, str(Path(__file__).resolve()), 'cli', *argv,
               '--host', ctx.host.name, '--cwd', ctx.repo.root]
        write(receipt / 'intent.json', dict(command=cmd, at=datetime.now(timezone.utc).isoformat(), no_retry=True))
        with open(ctx.store.path(log_name), 'a') as log:
            process = subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=log, stderr=log,
                                       cwd=ctx.repo.root, env=env, start_new_session=True)
        write(receipt / 'started.json', dict(pid=process.pid))
        return True

    LiveContext.spawn = spawn
    return ScopedCodex


def main():
    os.umask(0o077)
    adapter = install()
    mode = sys.argv[1]
    if mode == 'cli':
        from tokeneconomizer.plugin.cli import main as cli
        job = Path(os.environ['TTGL_TE_JOB_RECEIPT']) if os.environ.get('TTGL_TE_JOB_RECEIPT') else None
        try:
            status = cli(sys.argv[2:])
            if job:
                write(job / 'complete.json', dict(exit_code=status, at=datetime.now(timezone.utc).isoformat()))
            return status
        except BaseException as error:
            if job:
                write(job / 'stopped.json', dict(error=str(error), no_retry=True))
            raise
    if mode != 'hook':
        raise ValueError('Unsupported scoped command')
    raw = sys.stdin.read()
    payload = json.loads(raw) if raw.strip() else {}
    root = Path(os.environ['TOKENECONOMIZER_HOME']) / 'ttgl-hook-receipts'
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    ident = str(time.time_ns()) + '-' + str(os.getpid())
    before = dict(payload=payload, source='Actual native CLI hook input', at=datetime.now(timezone.utc).isoformat())
    if payload.get('hook_event_name') in ('PostToolUse', 'PostToolUseFailure'):
        name, args, text, code = adapter().tool_call(payload)
        before['semantic_command'] = dict(name=name, arguments=args, observed_exit=code,
                                          result_text_sha256=hashlib.sha256(text.encode()).hexdigest())
    write(root / (ident + '-input.json'), before)
    from tokeneconomizer.plugin.hook import main as hook
    output = io.StringIO()
    status = hook(['--host', 'codex'], stdin=io.StringIO(raw), stdout=output)
    text = output.getvalue()
    write(root / (ident + '-output.json'), dict(stdout=text, exit_code=status))
    sys.stdout.write(text)
    return status


if __name__ == '__main__':
    main()
