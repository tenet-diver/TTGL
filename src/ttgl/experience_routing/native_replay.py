"""Exact-node replay adapter. Native execution remains behind the ordinary freeze gates."""
from pathlib import Path
import json
import time
from .io import read,write_new,digest,file_digest
from .config import verify_freeze
from .contracts import validate
from .campaign import pinned
from .replay import execute_checkpoint
from .execution import DockerWorkspace
from .backend import RecordedCodexBackend
from .checkpoints import CheckpointStore
from .verification import PublicVerifier
from .runtime import Invocations,WORKER_SCHEMA
from .ledger import Budget,UsageLedger
from .client import ExperienceClient
from .benchmarks import public_task,assert_exposure
from ..personal import Request


def replay_pin(config,key,root):
    pin=config['replay'][key];path=Path(pin['path'])
    if not path.is_absolute():path=Path(root)/path
    if file_digest(path)!=pin['sha256']:raise ValueError('Changed replay pin: '+key)
    return read(path)


def run_native_replay(freeze_path,assignment,output):
    frozen=read(freeze_path);config=verify_freeze(frozen);root=frozen['root'];spec=config['replay'];output=Path(output)
    if not output.resolve().is_relative_to(Path(config['private_output_root']).resolve()):raise ValueError('Replay needs its private registered spool')
    if spec['condition']!=assignment['condition'] or spec['checkpoint_id']!=assignment['checkpoint_id'] or spec['contract_hash']!=assignment['contract_hash']:
        raise ValueError('Replay freeze differs from the registered assignment')
    if spec.get('shadow_memory_publication') is not False:raise ValueError('Controlled replay must disable shadow memory publication')
    tasks=pinned(config,'task_manifest',root)['tasks'];task=next((public_task(t) for t in tasks if t['task_id']==assignment['parent_id']),None)
    if not task:raise ValueError('Unknown replay parent')
    assert_exposure(task,pinned(config,'exclusion_registry',root))
    cp=replay_pin(config,'checkpoint_manifest',root);node=replay_pin(config,'node_contract',root);plan=validate('plan',replay_pin(config,'original_plan',root))
    if plan['taskInstanceId']!=task['task_id'] or next((n for n in plan['nodes'] if n['nodeId']==node['nodeId']),None)!=node:
        raise ValueError('Replay contract differs from its original parent plan')
    qualified=pinned(config,'runtime_isolation_manifest',root)
    if cp['environmentDigest']!=qualified['image_id']:raise ValueError('Replay environment differs from its source checkpoint')
    if qualified.get('host_qualified') is not True or qualified.get('replay_checkpoint_hashes',{}).get(cp['checkpointId'])!=cp['repositoryStateHash']:
        raise ValueError('Exact replay checkpoint has not passed actor/source qualification')
    packet={'experiences':[]} if assignment['condition']=='small_empty' else replay_pin(config,'experience_packet',root)
    if len(json.dumps(packet).encode())>64000:raise ValueError('Replay packet exceeds the frozen input bound')
    arm=spec['arm']
    if arm not in config['arms']:raise ValueError('Replay arm is not registered')
    write_new(output/'started.json',{'assignment':assignment,'fixture_only':False,'shadow_memory_publication':False})
    client=ExperienceClient(config['project_id'],config['study_id'],config.get('service_endpoint','http://127.0.0.1:3333/api/experience'))
    if assignment['condition']!='small_empty':
        query=replay_pin(config,'retrieval_query',root)
        if query['taskInstanceId']!=task['task_id'] or query['workItemId']!=node['nodeId'] or query['repositoryStateHash']!=cp['repositoryStateHash'] or query['arm']!=arm or query['memorySnapshotId']!=config['snapshots'][arm]:
            raise ValueError('Replay retrieval query differs from its frozen node, source or arm')
        versions=packet.get('sourceExperienceVersionIds',[]) if assignment['condition']=='small_raw' else [e['versionId'] for e in packet.get('experiences',[])]
        if not versions:raise ValueError('Nonempty replay condition requires authorized source versions')
        authorized=client.read(query,versions)
        if set(versions)!={e['versionId'] for e in authorized['experiences']}:raise ValueError('Replay source was excluded, stale or outside the bounded packet')
        if assignment['condition']=='small_raw':
            provenance=replay_pin(config,'raw_packet_provenance',root)
            if provenance.get('visibility')!='runtime_public' or provenance.get('reviewed') is not True or provenance.get('rawEvidenceHash')!=digest(packet['rawEvidence']) or set(provenance.get('sourceVersionIds',[]))!=set(versions):
                raise ValueError('Raw replay evidence requires its audited public source provenance')
        elif digest(authorized['experiences'])!=digest(packet['experiences']):raise ValueError('Structured replay packet changed from the authorized snapshot')
    catalogue=pinned(config,'model_catalog',root);rates=pinned(config,'rate_scenario',root)
    limits=config['budgets'];parent=config['per_parent']
    budget=Budget(min(limits['maximum_invocations'],parent['maximum_invocations']),min(limits['maximum_model_tokens'],parent['maximum_model_tokens']),min(limits['maximum_elapsed_seconds'],parent['maximum_elapsed_seconds']),maximum_scenario_cost=parent.get('maximum_scenario_cost'))
    ledger=UsageLedger(output/'accounting',rates['models']);actor=None;attempt_id=assignment['assignment_id'];active=False
    terminal=None
    try:
        def execute(contract,workspace,memory,role):
            nonlocal actor,active,terminal
            actor=DockerWorkspace(image=qualified['image_id'],review=qualified['image_review'],root=output/'actor',identity=[config['study_id'],attempt_id],base_commit=cp['baseCommit'],memory_bytes=qualified['memory_bytes'],cpus=qualified['cpus'])
            container=actor.start(workspace)
            backend=RecordedCodexBackend(executable=catalogue['codex_executable'],executable_sha256=catalogue['codex_sha256'],source_home=config['source_home'],source_account_hash=config['source_account_hash'],output=output/'native',client=client,container=container,node_executable=catalogue['node_executable'])
            calls=Invocations(output/'invocations',backend,ledger,budget,client=client,origin='fixture' if getattr(backend,'fixture_only',False) else 'native')
            client.record('plan',plan)
            retained=client.retain_file(cp['archive_path'],kind='checkpoint',identity=cp['checkpointId'])
            public_cp={k:v for k,v in cp.items() if k not in ('source_manifest','archive_path')};public_cp['artifactArchiveId']=retained['artifactId'];client.record('checkpoint',public_cp)
            client.record('attempt',{'attemptId':attempt_id,'taskInstanceId':task['task_id'],'planNodeId':contract['nodeId'],'planRevisionId':plan['planRevisionId'],'checkpointId':cp['checkpointId'],'executorId':config['models'][role],'arm':arm,'ordinal':0});active=True
            model=config['models'][role]
            prompt=json.dumps({'parent':{'task_id':task['task_id'],'prompt':task['prompt']},'node':contract,'checkpoint':public_cp,'experiences':memory,'completedDependencies':cp['dependencyArtifactIds'],'priorAttempts':[],
                'instructions':'Execute only this frozen subtask contract from its exact pre-node checkpoint. No replanning, fallback or publication to memory is allowed. Report public checks and unresolved criteria.'})
            req=Request(attempt_id,model,'coding',prompt,output,WORKER_SCHEMA,budget.remaining_seconds,reasoning_effort=catalogue['models'][model]['reasoning_effort'])
            result,usage=calls.call(req,'small_execution' if role=='small' else 'large_execution');actor.after_attempt(workspace)
            store=CheckpointStore(output/'candidate-checkpoint',workspace,base_commit=cp['baseCommit'],environment_digest=qualified['image_id'])
            artifact_check=store.admissible(cp,contract['allowedWritePaths'],task.get('protected_paths',[]))
            candidate=store.capture(task['task_id'],contract['nodeId']+':candidate',contract,cp['dependencyArtifactIds'])
            retained_candidate=client.retain_file(candidate['archive_path'],kind='candidate-source',identity=attempt_id)
            verifier=PublicVerifier(task['public_check_catalog'],task.get('protected_paths',[]),output/'verification',executor=actor.public_check)
            def verify(scope):
                receipt,_=verifier.verify(contract,attempt_id,workspace,scope=scope,timeout=min(60,budget.remaining_seconds))
                for criterion in receipt['criterionResults']:
                    criterion['evidenceArtifactRefs']=[client.retain_file(verifier.root/(ref+'.json'),kind='public-verification',identity=attempt_id+':'+scope+':'+criterion['criterionId'])['artifactId'] for ref in criterion['evidenceArtifactRefs']]
                client.record('verification',receipt);return receipt
            local=verify('subtask');integrated=verify('integration') if artifact_check['passed'] and local['verdict']=='pass' and not result['unresolved'] and not result['escalate'] else None
            accepted=bool(integrated and integrated['verdict']=='pass')
            infrastructure=local['verdict']=='infrastructure_error' or bool(integrated and integrated['verdict']=='infrastructure_error')
            terminal={'attemptId':attempt_id,'taskInstanceId':task['task_id'],'arm':arm,'status':'uncertain' if infrastructure else 'accepted' if accepted else 'public_failure','artifactId':retained_candidate['artifactId'],'verificationId':local['verificationId'],'integrationId':integrated['verificationId'] if integrated else None,'trigger':'accepted' if accepted else 'controlled_replay_public_failure','artifactCheck':artifact_check,'completionReport':result,'usageInvocationId':usage['invocation_id']}
            client.record('attempt-event',terminal);active=False;write_new(output/'attempt-terminal.json',terminal)
            return {'uncertain':budget.unknown_usage or infrastructure,'public_state':'infrastructure_error' if infrastructure else 'completed' if accepted else 'unsuccessful','usage':ledger.totals(),'budget':budget.receipt(),'fixture_only':getattr(backend,'fixture_only',False)}
        value=execute_checkpoint(assignment,cp,node,output/'source',execute,packet=packet)
        value.update(complete=not value['uncertain'],scope='subtask_replay',automatic_retries=0,shadow_memory_publication=False)
        write_new(output/('completion.json' if value['complete'] else 'stopped.json'),value);return value
    except BaseException as error:
        if active:
            terminal={'attemptId':attempt_id,'taskInstanceId':task['task_id'],'arm':arm,'status':'uncertain','artifactId':cp['artifactArchiveId'],'verificationId':None,'integrationId':None,'trigger':type(error).__name__,'artifactCheck':{'passed':False,'changed_paths':[],'invalid_paths':[],'repository_state_hash':cp['repositoryStateHash'],'includes_adds_deletes_modes_and_links':True},'completionReport':None,'usageInvocationId':attempt_id}
            write_new(output/'attempt-terminal.json',terminal)
            try:client.record('attempt-event',terminal)
            except Exception:pass # Local receipt and immutable invocation remain authoritative.
        write_new(output/'stopped.json',{'complete':False,'uncertain':True,'reason':str(error)[:1000],'usage':ledger.totals(),'automatic_retry':False})
        raise
    finally:
        if actor is not None:actor.close()
