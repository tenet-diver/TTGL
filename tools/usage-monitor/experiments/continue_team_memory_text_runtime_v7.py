#!/usr/bin/env python3
"""Continue uninvoked assignments after independent post-generation recovery.

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
import codex_team_memory_extension as generation
from team_memory_startup_transport import StartupClient
generation.Client=StartupClient


def verify_gates(config):
    for path,expected in config['frozen_sources'].items():
        if sha(path)!=expected:raise ValueError('Frozen source changed: '+path)
    for path,expected in config['gate_files'].items():
        if sha(path)!=expected:raise ValueError('Gate receipt changed: '+path)
        value=json.loads(Path(path).read_text())
        if not value.get('passed'):raise ValueError('Failed mechanism gate: '+path)
    security=json.loads(Path(config['runtime_security']).read_text())
    if not security.get('complete') or security['findings']:raise ValueError('Runtime review gate failed')
    reviewed=Path(config['text_only_global'])/'memory-runtime'
    if any(p.name=='PIL' or p.name.startswith('pillow') for p in reviewed.iterdir()):
        raise ValueError('Excluded image runtime is present')
    controls=json.loads(Path(config['controls']).read_text())
    if len(controls)!=4 or not all(r['reference_pass'] if r['unit'].endswith('reference') else r['expected_base_failure'] for r in controls):
        raise ValueError('Reference/skeleton controls failed')


def continuation_rows(config,root):
    from analyze_team_memory_extension import validate_assignment
    count=config['continue_after_checkpoint']
    if count!=27 or not (root/'post-generation-recovery-010.json').exists():
        raise ValueError('Explicit audited security boundary required')
    prep=json.loads(Path(config['preparation_audit']).read_text())
    if not prep['passed'] or prep['model_calls'] or not prep['next_assignment_directory_absent']:
        raise ValueError('Completed-turn postprocessing evidence not established')
    if any(Path(f'/proc/{pid}').exists() for pid in prep['prior_queue_pids']):
        raise ValueError('Prior continuation still exists')
    old=json.loads((root/'queue-started.json').read_text())
    if Path(f"/proc/{old['pid']}").exists():raise ValueError('Original queue still exists')
    if any((root/name).exists() for name in ('continuation-006-started.json','completion.json','stopped.json')):
        raise ValueError('Continuation already started or ambiguous end state')
    protocol=json.loads(Path(config['protocol']).read_text())
    rows=json.loads((root/f'checkpoint-{count:03}.json').read_text())['assignments']
    if len(rows)!=count:raise ValueError('Boundary count mismatch')
    owners=set()
    for i,row in enumerate(rows):
        cell=root/row['directory']
        validate_assignment(row,protocol['assignments'][i],json.loads((cell/'combined-usage-audit.json').read_text()),
            json.loads((cell/'independent-grade/result.json').read_text()),owners)
        if not (cell/'recompression-001.json').exists():raise ValueError('Prior raw evidence not sealed')
    if any((root/a['directory']).exists() for a in protocol['assignments'][count:]):
        raise ValueError('A future assignment was prepared/started; never repeat')
    if not json.loads(Path(config['text_equivalence']).read_text())['passed']:
        raise ValueError('Text-only equivalence failed')
    return rows


def verify_runtime_once(config):
    for path,expected in config["runtime_sources"].items():
        if sha(path)!=expected:raise ValueError("Pinned runtime changed: "+path)


def execute(config_path,root):
    config=json.loads(config_path.read_text());verify_gates(config);verify_runtime_once(config)
    rows=continuation_rows(config,root)
    save(root/'continuation-006-started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),config_sha256=sha(config_path),automatic_retries=0,continued_after=len(rows)))
    protocol=json.loads(Path(config['protocol']).read_text())
    try:
        for assignment in protocol['assignments'][len(rows):]:
            if shutil.disk_usage(root).free<128*1024*1024:raise RuntimeError('Workspace evidence reserve reached before new invocation')
            verify_gates(config)
            cell=root/assignment['directory']
            prepare(cell,Path(config['source_manifest']),Path(config['runtime']),assignment['total_agent_capacity'],assignment['arm'],
                    Path(config['memory_entry']) if assignment['arm']=='mcp_memory' else None,assignment['task'])
            m=json.loads((cell/'manifest.json').read_text());m['private_capture']=config['capture_root']
            (cell/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
            save(cell/'runtime-variant.json',dict(variant='security-amended-text-only-002',
                security_receipt_sha256=sha(config['runtime_security']),equivalence_sha256=sha(config['text_equivalence']),
                frozen_agent_policy_changed=False,remote_preflight_calls=0,pre_model_rpc_timeout_seconds=120,post_generation_service_wait_seconds=180))
            service=log=None;container=None;generation_error=None
            try:
                if assignment['arm'] in ('mem0_luna','graphiti_luna','smallville_luna','searchable_logs'):
                    # Reuse the prewritten service spec/socket so every worker
                    # and the observer refer to exactly the same assignment.
                    from probe_team_memory_backends import GLOBAL,HERE
                    import subprocess,sys
                    spec=json.loads((cell/'memory-service.json').read_text())
                    runtime=Path(config['text_only_global'])/('graphiti-runtime' if assignment['arm']=='graphiti_luna' else 'memory-runtime')
                    env={**os.environ,'TTGL_TEAM_TEXT_RUNTIME':config['text_only_global'],'PYTHONPATH':str(HERE)+':'+str(runtime),'HF_HUB_OFFLINE':'1',
                         'HF_HUB_DISABLE_TELEMETRY':'1','MEM0_TELEMETRY':'false','GRAPHITI_TELEMETRY_ENABLED':'false'}
                    log=(cell/'memory-service.log').open('x')
                    service=subprocess.Popen([sys.executable,'-S',str(HERE/'team_memory_text_service_v2.py'),'serve','--config',str(cell/'memory-service.json')],
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
                    os.killpg(service.pid,signal.SIGTERM);service.wait(timeout=180)
                    if service.returncode:raise RuntimeError('Memory seal/graph snapshot failed; preserve')
                if service is not None:
                    save(cell/'memory-service-ended.json',dict(at=datetime.now(timezone.utc).isoformat(),
                        pid=service.pid,exit_code=service.returncode,post_generation_wait_limit_seconds=180,
                        model_calls=0))
                if log is not None:log.close()
            # An absent turn intent is a conservative stop for audit, never an
            # automatic retry or proof of zero usage. Do not consume later cells.
            if generation_error and not (cell/'turn-intent.json').exists():
                save(cell/'pre-inference-setup-stopped.json',dict(reason=generation_error,
                    model_usage=None,requires_independent_invocation_audit=True,automatic_retries=0))
                raise RuntimeError('Native setup stopped before recorded turn intent; audit required')
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
    p.add_argument('--check-only',action='store_true')
    a=p.parse_args();os.umask(0o077)
    if a.check_only:
        config=json.loads(a.config.read_text());verify_gates(config);verify_runtime_once(config);rows=continuation_rows(config,a.root.resolve())
        print(json.dumps(dict(passed=True,prior_sealed_assignments=len(rows),remote_model_calls=0)))
    else:execute(a.config.resolve(),a.root.resolve())
