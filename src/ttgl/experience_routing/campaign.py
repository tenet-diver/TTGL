"""Finite, source-frozen parent assignments using existing Codex and public checks."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import time
import subprocess
from .io import read,write_new,digest,file_digest,now,inside
from .config import verify_freeze
from .contracts import validate,SCHEMAS
from .backend import RecordedCodexBackend
from .client import ExperienceClient
from .execution import DockerWorkspace
from .checkpoints import CheckpointStore
from .verification import PublicVerifier
from .ledger import Budget,UsageLedger
from .policy import RoutingPolicy
from .runtime import ParentRunner,Invocations,UncertainInvocation
from .benchmarks import public_task,assert_exposure


def pinned(config,key,root):
    pin=config['pins'][key];p=Path(pin['path'])
    if not p.is_absolute():p=Path(root)/p
    if file_digest(p)!=pin['sha256']:raise ValueError('Changed pin: '+key)
    return read(p)


def query_for(config,scope,task,arm,snapshot,phase,node=None,error=None):
    return {**scope,'taskInstanceId':task['task_id'],'workItemId':node['nodeId'] if node else None,
      'planRevisionId':node['planRevisionId'] if node else None,'phase':phase,'goal':node['goal'] if node else task['prompt'],
      'publicContextSummary':task.get('context_summary',''),'languages':task.get('languages',[]),'frameworkConstraints':task.get('frameworks',[]),
      'relevantPaths':node.get('relevantPaths',[]) if node else [],'relevantSymbols':node.get('relevantSymbols',[]) if node else [],
      'requiredTools':['Bash'],'acceptanceCriteria':[c['description'] for c in node['acceptanceCriteria']] if node else [],
      'errorSignature':error,'repositoryStateHash':config['repository_state_hash'],'memorySnapshotId':snapshot,
      'availableBeforeSequence':config['watermark'],'retrievalPolicyVersion':config['policy_version'],'arm':arm,
      'sourceRepository':task['repo'],'sourceBaseCommit':task['base_commit'],'excludedLeakageGroups':[task.get('leakage_group',task['task_id'])],
      'excludedTaskIds':[task['task_id']],'mode':config['mode'],'retrievalMode':'lexical'}


def standalone_plan(task,arm):
    catalog=task['public_check_catalog'];node='whole-task:'+arm+':'+task['task_id'];revision=digest([node,'standalone'])
    return {'planRevisionId':revision,'taskInstanceId':task['task_id'],'previousRevisionId':None,
      'nodes':[{'nodeId':node,'planRevisionId':revision,'parentWorkItemId':task['task_id'],'goal':task['prompt'],'dependsOn':[],
        'preconditions':[],'acceptanceCriteria':[{'id':k,'description':v.get('description',k),'publicCheck':None} for k,v in catalog.items()],
        'relevantPaths':[],'relevantSymbols':[],'allowedWritePaths':['**'],'expectedArtifacts':[],
        'publicVerificationCommands':[],'estimatedDifficulty':'unknown','delegationSuitability':'unknown','supersedesNodeIds':[]}],
      'continuedNodeIds':[],'cancelledNodeIds':[],'contextHash':digest(task),'plannerInvocationId':'none:standalone'}


def run_campaign(freeze_path,output):
    frozen=read(freeze_path);config=verify_freeze(frozen);root=frozen['root'];output=Path(output)
    if (output/'campaign-started.json').exists():raise ValueError('Campaign already started; retain assignments and reconcile, never rerun')
    tasks=pinned(config,'task_manifest',root)['tasks'];exclusions=pinned(config,'exclusion_registry',root)
    catalogue=pinned(config,'model_catalog',root);rates=pinned(config,'rate_scenario',root)
    qualified=pinned(config,'runtime_isolation_manifest',root)
    if qualified.get('host_qualified') is not True:raise ValueError('Host/actor environment is not qualified')
    # Raw records and source auth remain in private, durable local paths.
    if not output.resolve().is_relative_to(Path(config['private_output_root']).resolve()):raise ValueError('Native run output must be inside the registered private spool root')
    if config.get('active_workers',1)!=1:raise ValueError('The registered reference runner is serial; freeze a separate concurrency registration after serial qualification')
    fairness=pinned(config,'execution_fairness_manifest',root)
    by_id={t['task_id']:t for t in tasks}
    order=fairness.get('assignment_order')
    if not order:raise ValueError('Freeze a balanced explicit arm/task order before model execution')
    expected={(t['task_id'],a) for t in tasks for a in config['arms']}
    if len(order)!=len(expected) or {(a['task_id'],a['arm']) for a in order}!=expected:raise ValueError('Fairness assignment order differs from the finite task/arm matrix')
    assignments=[(by_id[a['task_id']],a['arm']) for a in order]
    if len(assignments)>config['budgets']['maximum_parent_assignments']:raise ValueError('Assignment cap exceeded before launch')
    write_new(output/'campaign-started.json',{'study_id':config['study_id'],'configuration_hash':digest(config),'assignments':len(assignments),'started_at':now(),'automatic_retries':0})
    client=ExperienceClient(config['project_id'],config['study_id'],config.get('service_endpoint','http://127.0.0.1:3333/api/experience'))
    results=[];shared_plans={};started=time.monotonic();total_tokens=0;total_invocations=0
    for task_record,arm in assignments:
        verify_freeze(frozen)
        remaining=config['budgets']['maximum_elapsed_seconds']-(time.monotonic()-started)
        if remaining<=0 or total_tokens>=config['budgets']['maximum_model_tokens'] or total_invocations>=config['budgets']['maximum_invocations']:break
        task=public_task(task_record);assert_exposure(task,exclusions)
        assignment=digest([task['task_id'],arm]);unit=output/'assignments'/assignment
        source=Path(qualified['workspaces'][task['task_id']]).resolve()
        from .checkpoints import manifest
        if manifest(source)['state_hash']!=qualified['source_hashes'][task['task_id']]:raise ValueError('Prepared source differs from the qualified checkpoint')
        workspace=unit/'source';shutil.copytree(source,workspace,ignore=shutil.ignore_patterns('.git'))
        # Host-only Git identity permits ordinary binary patch export, while the
        # actor and planner only see the audited source projection.
        for args in (['init','-q'],['config','user.name','Observatory replay'],['config','user.email','replay@localhost'],['add','--all'],['commit','-qm','Public base checkpoint']):
            subprocess.run(['git','-C',str(workspace),*args],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
        worker=DockerWorkspace(image=qualified['image_id'],review=qualified['image_review'],root=unit/'worker',identity=[config['study_id'],assignment],
            base_commit=task['base_commit'],memory_bytes=qualified['memory_bytes'],cpus=qualified['cpus'])
        ledger=None
        try:
            container=worker.start(workspace)
            backend=RecordedCodexBackend(executable=catalogue['codex_executable'],executable_sha256=catalogue['codex_sha256'],
                source_home=config['source_home'],source_account_hash=config['source_account_hash'],output=unit/'native',client=client,
                container=container,node_executable=catalogue['node_executable'])
            budget=Budget(min(config['per_parent']['maximum_invocations'],config['budgets']['maximum_invocations']-total_invocations),
                min(config['per_parent']['maximum_model_tokens'],config['budgets']['maximum_model_tokens']-total_tokens),
                min(config['per_parent']['maximum_elapsed_seconds'],remaining))
            ledger=UsageLedger(unit/'accounting',rates['models']);calls=Invocations(unit/'invocations',backend,ledger,budget,client=client)
            snapshot=config['snapshots'][arm];local={**config,'watermark':config.get('watermark',0),'repository_state_hash':manifest(workspace)['state_hash'],
                'memory_snapshot_id':snapshot,'models':catalogue['models']}
            memory_enabled=arm in ('LPM','SFM','HRM')
            def memory(node,phase,history):
                if not memory_enabled:return {'experiences':[]}
                error=json.dumps(history[-1]['publicVerification'])[:2000] if history else None
                q=query_for(local,client.scope,task,arm,snapshot,phase,node,error)
                return client.search(q)['packet']
            shared_measurement=None
            if arm in ('L0','S0'):plan=standalone_plan(task,arm)
            elif arm in ('LPM','SFM','HRM') and task['task_id'] in shared_plans:
                plan,shared_measurement=shared_plans[task['task_id']]
            else:
                initial=client.search(query_for(local,client.scope,task,arm,snapshot,'user_task'))['packet'] if memory_enabled else {'experiences':[]}
                context={}
                for relative in qualified.get('context_files',{}).get(task['task_id'],[]):
                    p=inside(workspace,relative)
                    if '.git' in Path(relative).parts:raise ValueError('Planner context may not include Git history')
                    context[relative]=p.read_text()[:8000]
                if len(json.dumps(context).encode())>64000:raise ValueError('Prepared planner context exceeds frozen bound')
                identity=digest([assignment,'initial-plan'])
                instruction={'task':task,'publicContext':context,'experiences':initial,
                  'instruction':'Create at most eight independently checkable deliverables. Use only the supplied host acceptance criterion IDs, relative allowed write paths and source context. Return the registered plan schema. Do not use tools.',
                  'requiredIds':{'taskInstanceId':task['task_id'],'planRevisionId':digest([task['task_id'],'common-plan' if memory_enabled else arm]),'plannerInvocationId':identity}}
                req=__import__('ttgl.personal',fromlist=['Request']).Request(identity,config['models']['large'],'planning',json.dumps(instruction),unit,
                  read(SCHEMAS)['plan'],max(.01,budget.remaining_seconds),read_only=True,reasoning_effort=catalogue['models'][config['models']['large']]['reasoning_effort'])
                plan,usage=calls.call(req,'planning');validate('plan',plan)
                if any(plan[k]!=v for k,v in instruction['requiredIds'].items()):raise ValueError('Planner changed a registered identity')
                criteria={c['id'] for n in plan['nodes'] for c in n['acceptanceCriteria']}
                if criteria!=set(task['public_check_catalog']):raise ValueError('Planner must preserve all and only the frozen public acceptance criteria')
                if memory_enabled:shared_plans[task['task_id']]=(plan,usage)
            mode='all_large' if arm in ('L0','LP0','LPM') else 'cheap_first' if arm in ('S0','SFM') else 'outcome_aware'
            policy=RoutingPolicy(small=config['models']['small'],large=config['models']['large'],mode=mode,
                threshold=config['routing']['threshold'],minimum_independent_tasks=config['routing']['minimum_independent_tasks'],
                exploration_probability=config['routing'].get('exploration_probability',0),seed=config['order_seed'])
            verifier=PublicVerifier(task['public_check_catalog'],task.get('protected_paths',[]),unit/'verification',executor=worker.public_check)
            store=CheckpointStore(unit/'checkpoints',workspace,base_commit=task['base_commit'],environment_digest=qualified['image_id'])
            runner=ParentRunner(task=task,arm=arm,workspace=workspace,checkpoints=store,verifier=verifier,invocations=calls,policy=policy,
                memory=memory,output=unit/'parent',config=local,client=client,execution_context=worker)
            result=runner.run(plan)
            # Exact final source plus a portable binary Git patch are both sealed.
            subprocess.run(['git','-C',str(workspace),'add','--intent-to-add','--all'],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
            patch=subprocess.run(['git','-C',str(workspace),'diff','--binary','HEAD'],check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).stdout
            patch_path=unit/'candidate.patch';patch_path.write_bytes(patch);patch_path.chmod(0o600)
            patch_archive=client.retain_file(patch_path,kind='candidate-patch',identity=assignment+':patch')
            write_new(unit/'patch-manifest.json',{'task_id':task['task_id'],'arm':arm,'base_commit':task['base_commit'],
                'artifact_path':str(patch_path.resolve()),'artifact_sha256':file_digest(patch_path),'artifact_archive_id':patch_archive['artifactId'],
                'evaluator_revision':qualified['evaluator_revision'],'score_label':qualified['score_label']})
            trace_jobs=[]
            for retained in backend.rollout_artifacts:
                trace_jobs.append(client.call('ingest-native',{'artifactId':retained['artifactId'],'taskInstanceId':task['task_id']+'@'+arm,
                    'title':task['task_id']+' '+arm,'goal':task['prompt'][:8000],'acceptance':'; '.join(task['public_check_catalog'])[:8000],
                    'accountHash':config['source_account_hash'],'isolationReceiptHash':file_digest(unit/'worker'/'runtime-isolation.json')}))
            write_new(unit/'annotation-preparation.json',{'source_jobs':trace_jobs,'model_calls':0,'instruction':'Execute only registered exact job IDs under the separate annotation budget; then queue envelope extraction.'})
            if shared_measurement and shared_measurement['invocation_id'] not in ledger.records:
                write_new(unit/'shared-plan-charge.json',{'kind':'logical_policy_charge','source_invocation_id':shared_measurement['invocation_id'],
                    'source_receipt_hash':digest(shared_measurement),'scenario_cost':shared_measurement['scenario_cost'],'additional_actual_spending':False})
                cost=result['usage']['scenario_cost'];plan_cost=shared_measurement['scenario_cost']
                result['deployment_scenario_cost']=cost+plan_cost if cost is not None and plan_cost is not None else None
            else:result['deployment_scenario_cost']=result['usage']['scenario_cost']
            result['shared_planner_reused']=shared_measurement is not None and shared_measurement['invocation_id'] not in ledger.records
            write_new(unit/'deployment-accounting.json',result)
            results.append(result);total_invocations+=budget.used_invocations;total_tokens+=budget.used_tokens
            if result['public_state']=='uncertain' or budget.unknown_usage:break
        except BaseException as error:
            observed=ledger.totals() if ledger is not None else None
            stopped={'study_id':config['study_id'],'complete':False,'completed':len(results),'assigned':len(assignments),
                'stopped_assignment':assignment,'reason':str(error)[:1000],'error':type(error).__name__,
                'current_usage':observed,'automatic_retry':False,'reconciliation_required':True,'target90_result':None}
            write_new(output/'stopped.json',stopped)
            raise
        finally:worker.close()
    complete=len(results)==len(assignments)
    receipt={'study_id':config['study_id'],'complete':complete,'assigned':len(assignments),'completed':len(results),'results':results,
             'observed_actual_invocations':total_invocations,'observed_actual_tokens':total_tokens,
             'end_to_end_seconds':time.monotonic()-started,'independent_grades':'pending separate evaluator','target90_result':None}
    write_new(output/('completion.json' if complete else 'stopped.json'),receipt);return receipt
