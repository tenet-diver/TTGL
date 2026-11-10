"""One registered turn initializes a native session, then observe its pipeline.

The preceding thread/start-only probe made zero model requests. Reuse the actual
aged public seed without editing timestamps or native jobs. No caller retries.
"""
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
import time

from native_memory_feature_probe import ROOT, client, start_thread, write
from native_compaction_canary_003 import wait_turn


def run():
    directory = ROOT / 'generation-probe-003'
    c = client(directory)
    write(directory / 'protocol.json', dict(at=datetime.now(timezone.utc).isoformat(),
          parent_turns=1, model='gpt-6-luna', purpose='Initialize native session, observe generation; not coding score',
          prior_probe='thread/start-only made zero model requests; preserved timeout and capture audit',
          seed_repeated=False, timestamps_edited=False, jobs_edited=False,
          native_internal_retry_policy='Unchanged native policy; every attempted request retained, unknown cost remains unknown',
          no_caller_retry=True, followup_injection='Separate next unit only if actual generated summary observed'))
    try:
        sid = start_thread(c, directory)
        write(directory / 'turn-intent.json', dict(no_retry=True, at=datetime.now(timezone.utc).isoformat()))
        result = c.request('turn/start', dict(threadId=sid, input=[dict(type='text',
              text='This is an isolated native-memory initialization diagnostic. Do not use tools, files, network or other agents. Reply in one short sentence acknowledging the diagnostic; do not claim memory generation or test success.', text_elements=[])]))
        write(directory / 'turn-accepted.json', result)
        turn = wait_turn(c, 'native_memory_generation_initialization')
        write(directory / 'parent-complete.json', dict(session_id=sid, turn=turn))
        deadline = time.monotonic() + 600
        summary = ROOT / 'home/memories/memory_summary.md'
        while time.monotonic() < deadline:
            with sqlite3.connect('file:' + str(ROOT / 'home/memories_1.sqlite') + '?mode=ro', uri=True) as db:
                jobs = db.execute('SELECT kind,status,started_at,finished_at,last_error FROM jobs').fetchall()
                sources = db.execute('SELECT thread_id,length(raw_memory),length(rollout_summary),generated_at FROM stage1_outputs').fetchall()
            if summary.exists() and summary.stat().st_size and not any(j[1] == 'running' for j in jobs):
                write(directory / 'complete.json', dict(session_id=sid, native_summary_generated=True,
                      native_jobs=jobs, native_sources=sources, injection_and_accounting_pending=True))
                print('Observed actual native summary and settled job lifecycle.', flush=True)
                return
            if c.p.poll() is not None:
                raise RuntimeError('Native server exited; no retry')
            if c.selector.select(1):
                c.buffer += os.read(c.p.stdout.fileno(), 65536)
                while b'\n' in c.buffer:
                    line, c.buffer = c.buffer.split(b'\n', 1)
                    if line.strip():
                        c.record(dict(direction='notification', message=json.loads(line)))
        write(directory / 'observed-native-state.json', dict(jobs=jobs, sources=sources,
              summary_exists=summary.exists(), at=datetime.now(timezone.utc).isoformat()))
        raise TimeoutError('No settled native summary within600s; preserve all attempts')
    except BaseException as error:
        write(directory / 'stopped.json', dict(error=str(error), no_retry=True, usage_unknown_until_audit=True))
        raise
    finally:
        c.close()


if __name__ == '__main__':
    run()
