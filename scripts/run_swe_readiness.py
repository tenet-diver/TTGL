#!/usr/bin/env python3
"""Serial base/gold controls and public probes, reusing each warm task image."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import uuid

import run_swe_controls as controls
from ttgl import benchmark, isolated, personal


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--private-root',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--probe-output',type=Path,required=True)
    parser.add_argument('--tasks',type=Path,required=True)
    parser.add_argument('--timeout',type=int,default=1200)
    parser.add_argument('--resume',action='store_true')
    args=parser.parse_args()
    if args.timeout<1:
        parser.error('--timeout must be positive')
    output,probes=args.output.resolve(),args.probe_output.resolve()
    tasks=benchmark.read_tasks(args.tasks)
    if not args.resume and (output.exists() or probes.exists()):
        raise ValueError('Choose fresh readiness outputs; resume only explicitly')
    probes.mkdir(parents=True,exist_ok=args.resume)
    description={'driver_sha256':benchmark.digest(Path(__file__)),
                 'public_validator_sha256':benchmark.digest(Path(__file__).with_name('validate_policy_workers.py')),
                 'order':'base control, gold control, public probe, image removal; no overlapping grading',
                 'inference_calls':0}
    protocol={'tasks_sha256':benchmark.digest(args.tasks),
              'private_dataset_sha256':benchmark.digest(args.private_root/'selected.dataset.json'),
              'native_control_timeout_seconds':args.timeout,**description}
    if args.resume:
        if json.loads((probes/'pipeline-protocol.json').read_text())!=protocol:
            raise ValueError('Readiness protocol changed; retain attempts and reconcile')
    else:
        benchmark.write_new(probes/'pipeline-protocol.json',protocol)
    state_path=probes/'accepted.json'
    accepted=json.loads(state_path.read_text()) if state_path.exists() else {}
    closed_before_resume={p.stem for p in output.glob('*.json') if p.name not in ('protocol.json','summary.json')}

    def event(row):
        with (probes/'events.jsonl').open('a') as stream:
            stream.write(json.dumps({'epoch':time.time(),**row})+'\n')

    def after_pair(task,row):
        key=task['instance_id']
        record=output/(key+'.json')
        control_hash=benchmark.digest(record)
        if not row['eligible']:
            raise RuntimeError('Independent controls are not valid for '+key+'; preserve and repair before inference')
        cached=accepted.get(key)
        if cached:
            path=Path(cached['record'])
            if (cached['controls_record_sha256']!=control_hash
                    or benchmark.digest(path)!=cached['record_sha256']):
                raise ValueError('Accepted probe provenance changed')
            return
        attempt=probes/'attempts'/key/uuid.uuid4().hex[:12]
        attempt.mkdir(parents=True)
        view=attempt/'control-view';view.mkdir()
        (view/'protocol.json').write_bytes((output/'protocol.json').read_bytes())
        (view/record.name).write_bytes(record.read_bytes())
        benchmark.write_new(view/'summary.json',{'tasks':[row]})
        public=attempt/'public-task.json'
        benchmark.write_new(public,{**tasks,'tasks':[task],
            'selection':{'method':'single public probe from the reserved manifest',
                         'assigned_tasks':1,'source_tasks_sha256':benchmark.digest(args.tasks),
                         'selection_uses_model_outcomes':False}})
        validation=attempt/'validation'
        command=[sys.executable,str(Path(__file__).with_name('validate_policy_workers.py')),
                 '--controls',str(view),'--output',str(validation),
                 '--workspace-root',str(attempt/'workspace'),'--tasks',str(public)]
        event({'event':'public_probe_started','instance_id':key,'attempt':str(attempt)})
        with (attempt/'stdout.txt').open('x') as stream:
            process=subprocess.Popen(command,stdout=stream,stderr=subprocess.STDOUT,start_new_session=True)
            try:
                result=process.wait(timeout=900)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGKILL)
                process.wait()
                result=-9
        probe_record=validation/(key+'.json')
        ready=(result==0 and probe_record.exists()
               and json.loads(probe_record.read_text()).get('ready') is True)
        # A failed source guard can leave its uncharged probe container alive.
        # Preserve its setup diff and identity before removing only that object.
        if not ready:
            worker_output=validation/'runs'/key
            name='ttgl-worker-'+hashlib.sha256(str(worker_output).encode()).hexdigest()[:24]
            inspected=subprocess.run(['docker','inspect',name],capture_output=True)
            if inspected.returncode==0:
                (attempt/'failed-container-inspect.json').write_bytes(inspected.stdout)
                for label,git_args in [('status',['status','--porcelain']),('diff',['diff','--binary'])]:
                    diagnostic=subprocess.run(['docker','exec',name,'git','-C','/testbed',*git_args],capture_output=True)
                    (attempt/('failed-source-'+label+'.txt')).write_bytes(diagnostic.stdout+diagnostic.stderr)
                isolated.docker('rm','-f',name)
        receipt={'instance_id':key,'ready':ready,'returncode':result,
                 'controls_record_sha256':control_hash,
                 'runtime_adapter_sha256':benchmark.digest(Path(isolated.__file__)),
                 'worker_dependencies_sha256':benchmark.digest(isolated.DEPENDENCIES),
                 'image_id':row['image']['image_id'],'inference_calls':0}
        benchmark.write_new(attempt/'receipt.json',receipt)
        event({'event':'public_probe_finished',**receipt})
        if not ready:
            raise RuntimeError('Public probe failed for '+key+'; retain attempt, repair, then explicitly resume readiness')
        probe=json.loads(probe_record.read_text())
        if probe['controls_record_sha256']!=control_hash or probe['image_id']!=row['image']['image_id']:
            raise ValueError('Public probe does not bind the actual control environment')
        accepted[key]={'record':str(probe_record),'record_sha256':benchmark.digest(probe_record),
                       'controls_record_sha256':control_hash}
        personal._write_json(state_path,accepted)
        if key in closed_before_resume:
            # The earlier failed callback stopped before its image cleanup.
            isolated.docker('image','rm',row['image']['image_id'])

    sys.argv=[str(Path(controls.__file__)),'--private-root',str(args.private_root),
              '--output',str(output),'--tasks',str(args.tasks),'--timeout',str(args.timeout)]
    if args.resume:
        sys.argv.append('--resume')
    controls.main(after_pair=after_pair,callback_description=description)
    rows=[json.loads(Path(accepted[t['instance_id']]['record']).read_text()) for t in tasks['tasks']]
    benchmark.write_new(probes/'summary.json',{'tasks':rows,
        'pipeline_protocol_sha256':benchmark.digest(probes/'pipeline-protocol.json'),
        'accepted_records_sha256':benchmark.digest(state_path),
        'native_controls_and_public_probes_are_separate_checks':True})


if __name__=='__main__':
    main()
