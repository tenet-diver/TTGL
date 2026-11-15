#!/usr/bin/env python3
"""Security-amended continuation of only verified unstarted assignments.

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
    reviewed=Path(config['text_only_global'])/'memory-runtime'
    if any(p.name=='PIL' or p.name.startswith('pillow') for p in reviewed.iterdir()):
        raise ValueError('Excluded image runtime is present')
    controls=json.loads(Path(config['controls']).read_text())
    if len(controls)!=4 or not all(r['reference_pass'] if r['unit'].endswith('reference') else r['expected_base_failure'] for r in controls):
        raise ValueError('Reference/skeleton controls failed')


def validate_preparation_recovery(config):
    receipt=Path(config['preparation_recovery']);value=json.loads(receipt.read_text());cell=receipt.parent
    if not value['passed'] or value['model_calls']!=0 or not value['verified_before_model_invocation']:
        raise ValueError('Preparation recovery is not independently verified')
    if cell.name!='013-simpy-graphiti_luna-1' or value['assignment']!=cell.name:
        raise ValueError('Recovery scope mismatch')
    for name in ('started.json','turn-intent.json','thread.json','accepted.json','process-intent.json'):
        if (cell/name).exists():raise ValueError('Model invocation may have started; never repeat')
    if list((cell/'home').rglob('*.jsonl')):raise ValueError('Prior owned rollout exists')
    for path,expected in value['input_hashes'].items():
        if sha(path)!=expected:raise ValueError('Prepared source/config/boundary changed')
    state=docker(['inspect',value['existing_container_adopted']],capture_output=True,text=True,timeout=30)
    info=json.loads(state.stdout)[0]
    if state.returncode or not info['State']['Running'] or info['Name']!='/ttgl-team-'+cell.name:
        raise ValueError('Audited owned container is not running')
    for prior in (cell/'memory-preparation-005',cell/'memory'):
        if list(prior.rglob('call-*/intent.json')):raise ValueError('A maintenance call may have started')
    return cell.resolve()


def continuation_rows(config,root):
    from analyze_team_memory_extension import validate_assignment
    count=config['continue_after_checkpoint']
    if count!=12 or not (root/'security-interruption-001.json').exists():
        raise ValueError('Explicit audited security boundary required')
    old=json.loads((root/'queue-started.json').read_text())
    if Path(f"/proc/{old['pid']}").exists():raise ValueError('Original queue still exists')
    if any((root/name).exists() for name in ('continuation-002-started.json','completion.json','stopped.json')):
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
    recovery=validate_preparation_recovery(config)
    if any((root/a['directory']).exists() and (root/a['directory']).resolve()!=recovery for a in protocol['assignments'][count:]):
        raise ValueError('An unaudited future assignment exists; never repeat')
    if not json.loads(Path(config['text_equivalence']).read_text())['passed']:
        raise ValueError('Text-only equivalence failed')
    return rows


def verify_runtime_once(config):
    for path,expected in config["runtime_sources"].items():
        if sha(path)!=expected:raise ValueError("Pinned runtime changed: "+path)


def execute(config_path,root):
    config=json.loads(config_path.read_text());verify_gates(config);verify_runtime_once(config)
    rows=continuation_rows(config,root)
    save(root/'continuation-002-started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),config_sha256=sha(config_path),automatic_retries=0,continued_after=len(rows)))
    protocol=json.loads(Path(config['protocol']).read_text())
    try:
        for assignment in protocol['assignments'][len(rows):]:
            if shutil.disk_usage(root).free<128*1024*1024:raise RuntimeError('Workspace evidence reserve reached before new invocation')
            verify_gates(config)
            cell=root/assignment['directory']
            recovered=cell.resolve()==Path(config['preparation_recovery']).parent
            if recovered:validate_preparation_recovery(config)
            else:
                prepare(cell,Path(config['source_manifest']),Path(config['runtime']),assignment['total_agent_capacity'],assignment['arm'],
                        Path(config['memory_entry']) if assignment['arm']=='mcp_memory' else None,assignment['task'])
            m=json.loads((cell/'manifest.json').read_text());m['private_capture']=config['capture_root']
            (cell/'manifest.json').write_text(json.dumps(m,indent=2)+'\n')
            save(cell/'runtime-variant.json',dict(variant='security-amended-text-only-002',
                security_receipt_sha256=sha(config['runtime_security']),equivalence_sha256=sha(config['text_equivalence']),
                frozen_agent_policy_changed=False,remote_preflight_calls=0))
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
                    service=subprocess.Popen([sys.executable,'-S',str(HERE/'team_memory_text_service.py'),'serve','--config',str(cell/'memory-service.json')],
                        env=env,stdout=log,stderr=log,start_new_session=True)
                    deadline=time.monotonic()+60
                    while not (cell/'memory/ready.json').exists():
                        if service.poll() is not None or time.monotonic()>=deadline:raise RuntimeError('Service initialization failed; no scored retry')
                        time.sleep(.1)
                save(cell/'memory-readiness.json',dict(passed=True,scope='Per-arm completed native/backend gates plus fresh service; gates in queue configuration',model_calls=0))
                if not recovered:preflight(cell)
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
    p.add_argument('--check-only',action='store_true')
    a=p.parse_args();os.umask(0o077)
    if a.check_only:
        config=json.loads(a.config.read_text());verify_gates(config);verify_runtime_once(config);rows=continuation_rows(config,a.root.resolve())
        print(json.dumps(dict(passed=True,prior_sealed_assignments=len(rows),remote_model_calls=0)))
    else:execute(a.config.resolve(),a.root.resolve())
