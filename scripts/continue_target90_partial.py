#!/usr/bin/env python3
"""Evidence-registered recovery of stopped matched pairs; never repeat an invocation."""
import argparse, fcntl, hashlib, importlib.util, json, os
from pathlib import Path
import shutil, subprocess, sys, tomllib
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pipeline',ROOT/'scripts/continue_pro_rescue.py')
p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

def next_action(out, arm):
    """An invocation with no completed report is ambiguous, never retryable."""
    name='first-block-'+arm
    invoke=out/(name+'-invocation.json')
    reports=list((out/'jobs'/name).glob('*/result.json'))
    if invoke.exists():
        if len(reports)!=1:raise RuntimeError('Started/uncertain model invocation: '+arm)
        native=json.loads(reports[0].read_text())
        if native.get('exception_info') or (native.get('verifier_result') or {}).get('rewards',{}).get('reward') not in (0,1):
            raise RuntimeError('Unsuccessful/uncertain model invocation: '+arm)
        return 'reuse_completed_native',reports[0]
    if reports:raise RuntimeError('Native report without invocation')
    return 'unstarted',None

def verify_inventory(inventory):
    for name,sha in inventory.items():
        if p.digest(name)!=sha:raise RuntimeError('Recovery evidence changed: '+name)

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--registration',type=Path,required=True);args=parser.parse_args()
    reg=json.loads(args.registration.read_text());verify_inventory(reg['artifacts_sha256'])
    protocol_path=Path(reg['protocol']);protocol=json.loads(protocol_path.read_text());p.validate_matched_pair(protocol)
    out=Path(reg['output']);task=protocol['task_id'];lock=ROOT/'artifacts'/('pro-pipeline-'+hashlib.sha256(task.encode()).hexdigest()[:16]+'.lock')
    handle=lock.open('a+');fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
    for name,sha in protocol['source_sha256'].items():
        if p.digest(name)!=sha:raise RuntimeError('Frozen generation source changed: '+name)
    if p.digest(protocol_path)!=json.loads((out/'queue.json').read_text())['protocol_sha256']:raise RuntimeError('Original registration mismatch')
    if json.loads((out/'stopped.json').read_text())['message']!='Reserved disk unavailable before job: first-block-optional-fresh':raise RuntimeError('Recovery scope differs')
    if (out/'completion.json').exists():raise RuntimeError('Pair already complete')
    # Recovery registrations are exclusive and bind all pre-existing evidence.
    p.write(out/'recovery-invocation.json',{'registration':str(args.registration.resolve()),'sha256':p.digest(args.registration),'no_automatic_retries':True})
    private=Path(protocol['private_task_root']);image=tomllib.loads((private/'v2/tasks'/task/'task.toml').read_text())['environment']['docker_image']
    frozen=json.loads((out/'image-binding.json').read_text())['image_id']
    env={**os.environ,'PYTHONPATH':str(ROOT/'src')+os.pathsep+str(private/'v2/tooling')}
    if protocol.get('docker_config'):env['DOCKER_CONFIG']=protocol['docker_config']
    def verify():
        verify_inventory(reg['artifacts_sha256'])
        for name,sha in protocol['source_sha256'].items():
            if p.digest(name)!=sha:raise RuntimeError('Frozen source changed')
        if subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],text=True).strip()!=frozen:raise RuntimeError('Image changed')
        if shutil.disk_usage(ROOT).free<protocol['disk_guard_bytes']:raise RuntimeError('Disk reserve unavailable; no invocation')
    def job(name,agent,options):
        verify()
        if (out/(name+'-invocation.json')).exists() or (out/'jobs'/name).exists():raise RuntimeError('Never repeat started job: '+name)
        command=[str(ROOT/'artifacts/harbor-runtime-001/bin/harbor'),'run','-p',str(private/'v2/tasks'),'--environment-import-path',protocol['environment_import_path'],'-a',agent,'-n','1','--n-attempts','1','--max-retries','0','--jobs-dir',str(out/'jobs'),'--job-name',name]
        for key,value in options:command+=['--ak',key+'='+str(value)]
        p.write(out/(name+'-invocation.json'),{'command':command,'state':'registered_before_invocation','recovery':str(args.registration.resolve())})
        with (out/(name+'.stdout.txt')).open('x') as stream:r=subprocess.run(command,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=9000)
        paths=list((out/'jobs'/name).glob('*/result.json'))
        if r.returncode or len(paths)!=1:raise RuntimeError('Job failed/uncertain; do not retry')
        if subprocess.check_output(['docker','image','inspect',image,'--format','{{.Id}}'],text=True).strip()!=frozen:raise RuntimeError('Image changed during job')
        for source,sha in protocol['source_sha256'].items():
            if p.digest(source)!=sha:raise RuntimeError('Frozen source changed during job')
        native=json.loads(paths[0].read_text());grade=(native.get('verifier_result') or {}).get('rewards',{}).get('reward')
        if native.get('exception_info') or grade not in (0,1):raise RuntimeError('Invalid job outcome')
        return paths[0],native,int(grade)
    rows=[];rates=json.loads(Path(protocol['rate_scenario']).read_text())['models']
    for arm in protocol['first_block_order']:
        action,path=next_action(out,arm)
        if action=='unstarted':
            claim=Path(protocol['assignment_claims'][arm]);p.write(claim,{'protocol_sha256':p.digest(protocol_path),'task_id':task,'arm':arm,'status':'claimed_before_scored_invocation','recovery':str(args.registration.resolve())})
            path,native,initial=job('first-block-'+arm,protocol['agent_import_path'],[('private_records_root',protocol['private_records_root']),('condition',arm if arm=='large' else 'personal'),('policy','verification')])
        else:
            claim=json.loads(Path(protocol['assignment_claims'][arm]).read_text())
            if claim['protocol_sha256']!=p.digest(protocol_path) or claim['arm']!=arm:raise RuntimeError('Original claim disagrees')
            native=json.loads(path.read_text());initial=int(native['verifier_result']['rewards']['reward'])
        meta=native['agent_result']['metadata'];records=Path(meta['private_records_path']).resolve()
        if not records.is_relative_to(Path(protocol['private_records_root']).resolve()) or native['task_name'].split('/')[-1]!=task:raise RuntimeError('Wrong records/task')
        manifest=p.audit_native(records);p.audit_thread_deltas(records)
        if manifest['status']!='completed_ungraded' or p.digest(records/'controller/manifest.json')!=meta['manifest_sha256'] or p.digest(records/'final.patch')!=meta['final_patch_sha256']:raise RuntimeError('Incomplete/tampered native')
        sealed=records/'sealed-replay-source';folder=sealed/task
        if action=='unstarted':
            p.write(folder/'result.json',{'task_name':native['task_name']});(folder/'agent').mkdir();shutil.copyfile(records/'final.patch',folder/'agent/model.patch')
            if (records/'pre-handoff.json').exists():
                snapshot=json.loads((records/'pre-handoff.json').read_text())
                if p.digest(records/'pre-handoff.patch')!=snapshot['patch_sha256']:raise RuntimeError('Pre-handoff changed')
                shutil.copyfile(records/'pre-handoff.patch',folder/'agent/pre-handoff.patch')
            p.write(folder/'seal.json',{'native_result_sha256':p.digest(path),'patches_sha256':{f.name:p.digest(f) for f in (folder/'agent').iterdir()}})
        seal=json.loads((folder/'seal.json').read_text())
        if seal['native_result_sha256']!=p.digest(path) or p.digest(folder/'agent/model.patch')!=p.digest(records/'final.patch'):raise RuntimeError('Seal/native mismatch')
        for name,sha in seal['patches_sha256'].items():
            if Path(name).name!=name or p.digest(folder/'agent'/name)!=sha:raise RuntimeError('Sealed patch changed')
        def replay(suffix,patch):
            rp,rn,grade=job('first-block-'+arm+'-'+suffix,'patch_replay:PatchReplayAgent',[('source_job',sealed),('patch_name',patch)])
            rr=json.loads((rp.parent/'agent/replay.json').read_text())
            if rr['apply_rc']!=0 or Path(rr['patch']).resolve()!=(folder/'agent'/patch).resolve():raise RuntimeError('Replay seal join failed')
            return grade
        final=replay('fresh','model.patch');prior=None
        if (folder/'agent/pre-handoff.patch').exists():prior=bool(replay('pre-handoff','pre-handoff.patch'))
        cost=0.0
        for model,record in manifest['usage_by_model'].items():
            usage=record['usage'];rate=rates[model]
            if any(usage[k] is None for k in ('input_tokens','cached_input_tokens','output_tokens')):cost=None;break
            cost+=((usage['input_tokens']-usage['cached_input_tokens'])*rate['input_per_million']+usage['cached_input_tokens']*rate['cached_input_per_million']+usage['output_tokens']*rate['output_per_million'])/1e6
        attempted=sum(json.loads(line).get('event')=='request' and json.loads(line).get('kind')=='expert' for line in (records/'controller/events.jsonl').read_text().splitlines())
        row={'task_id':task,'arm':arm,'resolved':bool(final),'initial_grade':initial,'expert_calls':manifest['expert_calls'],'expert_requests_attempted':attempted,'pre_handoff_resolved':prior,'cost_scenario_usd':cost,'native_result':str(path),'private_manifest_sha256':p.digest(records/'controller/manifest.json')};rows.append(row);p.write(out/('completed-'+arm+'.json'),row)
    p.write(out/'records.json',rows);p.write(out/'matched-pair.json',p.matched_pair_observation(rows));p.write(out/'completion.json',{'status':'registered_partial_continuation_completed','development_assignments':2,'full_twelve_task_run_started':False,'validation_started':False,'recovery_registration':str(args.registration.resolve())})

if __name__=='__main__':main()
