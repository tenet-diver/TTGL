#!/usr/bin/env python3
"""Sequential memory-aware coding comparison; never resumes a started queue.

No dependency installation, provider retries or implicit service provisioning.
All required gates are checked before the first scored model invocation. Each
cell is independently sealed/replayed, audited and losslessly archived.
"""
import argparse
from datetime import datetime,timezone
import json
import os
from pathlib import Path
import signal
import shutil
import time

from codex_team_probe import save,sha
from codex_team_memory_extension import prepare,preflight,run,docker
from codex_team_grade_v3 import grade
from codex_team_queue import archive
from resume_codex_team_scaling import compact_archived_databases
from recompress_codex_team_archives import recompress
from probe_team_memory_backends import start_service
from audit_team_memory_usage import audit


def verify_gates(config):
    for path,expected in config['frozen_sources'].items():
        if sha(path)!=expected:raise ValueError('Frozen source changed: '+path)
    for path,expected in config['gate_files'].items():
        if sha(path)!=expected:raise ValueError('Gate receipt changed: '+path)
        value=json.loads(Path(path).read_text())
        if not value.get('passed'):raise ValueError('Failed mechanism gate: '+path)
    security=json.loads(Path(config['runtime_security']).read_text())
    if not security.get('complete') or security['findings']:raise ValueError('Runtime review gate failed')
    controls=json.loads(Path(config['controls']).read_text())
    if len(controls)!=4 or not all(r['reference_pass'] if r['unit'].endswith('reference') else r['expected_base_failure'] for r in controls):
        raise ValueError('Reference/skeleton controls failed')


def execute(config_path,root):
    config=json.loads(config_path.read_text());verify_gates(config)
    root.mkdir(parents=True,exist_ok=False,mode=0o700)
    save(root/'queue-started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),config_sha256=sha(config_path),automatic_retries=0))
    protocol=json.loads(Path(config['protocol']).read_text())
    rows=[]
    try:
        for assignment in protocol['assignments']:
            if shutil.disk_usage(root).free<128*1024*1024:raise RuntimeError('Workspace evidence reserve reached before new invocation')
            verify_gates(config)
            cell=root/assignment['directory']
            prepare(cell,Path(config['source_manifest']),Path(config['runtime']),assignment['total_agent_capacity'],assignment['arm'],
                    Path(config['memory_entry']) if assignment['arm']=='mcp_memory' else None,assignment['task'])
            m=json.loads((cell/'manifest.json').read_text());m['private_capture']=config['capture_root']
            (cell/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
            service=log=None;container=None;generation_error=None
            try:
                if assignment['arm'] in ('mem0_luna','graphiti_luna','smallville_luna','searchable_logs'):
                    # Reuse the prewritten service spec/socket so every worker
                    # and the observer refer to exactly the same assignment.
                    from probe_team_memory_backends import GLOBAL,HERE
                    import subprocess,sys
                    spec=json.loads((cell/'memory-service.json').read_text())
                    runtime=GLOBAL/('graphiti-runtime' if assignment['arm']=='graphiti_luna' else 'memory-runtime')
                    env={**os.environ,'PYTHONPATH':str(HERE)+':'+str(runtime),'HF_HUB_OFFLINE':'1',
                         'HF_HUB_DISABLE_TELEMETRY':'1','MEM0_TELEMETRY':'false','GRAPHITI_TELEMETRY_ENABLED':'false'}
                    log=(cell/'memory-service.log').open('x')
                    service=subprocess.Popen([sys.executable,'-S',str(HERE/'team_memory_service.py'),'serve','--config',str(cell/'memory-service.json')],
                        env=env,stdout=log,stderr=log,start_new_session=True)
                    deadline=time.monotonic()+60
                    while not (cell/'memory/ready.json').exists():
                        if service.poll() is not None or time.monotonic()>=deadline:raise RuntimeError('Service initialization failed; no scored retry')
                        time.sleep(.1)
                save(cell/'memory-readiness.json',dict(passed=True,scope='Per-arm completed native/backend gates plus fresh service; gates in queue configuration',model_calls=0))
                preflight(cell)
                container=json.loads((cell/'container.json').read_text())['name']
                try:run(cell)
                except Exception as error:
                    if not (cell/'stopped.json').exists():raise
                    generation_error=repr(error)
            finally:
                # Seal own source and memory before independent grade. Do not
                # silently kill an unrelated service or repeat an uncertain call.
                if container is None and (cell/'container.json').exists():container=json.loads((cell/'container.json').read_text())['name']
                if container:
                    result=docker(['stop','-t','2',container],capture_output=True,text=True,timeout=20)
                    save(cell/'container-stopped.json',dict(exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr))
                    if result.returncode:raise RuntimeError('Source seal failed; audit required')
                if service is not None and service.poll() is None:
                    os.killpg(service.pid,signal.SIGTERM);service.wait(timeout=30)
                    if service.returncode:raise RuntimeError('Memory seal/graph snapshot failed; preserve')
                if log is not None:log.close()
            # Never run a model after any evaluation for this cell. Independent
            # grades are written outside all actor and memory namespaces.
            grade(cell)
            metering=audit(cell,Path(config['capture_root']))
            result=json.loads((cell/'independent-grade/result.json').read_text())
            ended=next(json.loads((cell/name).read_text()) for name in ('completed.json','stopped.json') if (cell/name).exists())
            row=dict(assignment,grade=result,wall_seconds=ended.get('wall_seconds'),
                parent_status=ended.get('turn',{}).get('status','stopped'),generation_error=generation_error,
                inference_accounting_complete=metering['complete'],usage=metering['usage'],
                usage_by_model=metering['usage_by_model'],total_inference_usage=metering['total_inference_usage'],
                unknown_requests=metering['unknown_requests'])
            rows.append(row)
            save(root/f'checkpoint-{len(rows):03}.json',dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows))
            archive(cell);compact_archived_databases(cell);recompress(cell)
            print(json.dumps(dict(completed=len(rows),assignment=assignment,passed=result['passed'],usage=metering['usage'],complete=metering['complete'])),flush=True)
        save(root/'completion.json',dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows))
    except BaseException as error:
        save(root/'stopped.json',dict(at=datetime.now(timezone.utc).isoformat(),error=repr(error),completed=len(rows),automatic_retries=0))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--config',type=Path,required=True);p.add_argument('--root',type=Path,required=True)
    a=p.parse_args();os.umask(0o077);execute(a.config.resolve(),a.root.resolve())
