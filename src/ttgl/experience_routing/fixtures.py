"""Actual edit/check/replay control-flow tests with a clearly synthetic backend."""
from __future__ import annotations
import json
import shutil
import sys
import tempfile
from pathlib import Path
from ..personal import Response
from .io import digest,write_new,read
from .checkpoints import CheckpointStore,replay_snapshot,manifest
from .ledger import Budget,UsageLedger
from .policy import RoutingPolicy
from .runtime import Invocations,ParentRunner
from .verification import PublicVerifier


class FixtureBackend:
    fixture_only=True
    def __init__(self,workspace,behavior='success'):
        self.workspace=Path(workspace);self.behavior=behavior;self.calls=[]

    def complete(self,request):
        payload=json.loads(request.prompt);node=payload['node']['nodeId'];small=request.model=='fixture-small'
        self.calls.append({'model':request.model,'node':node,'handoff':payload.get('priorAttempts',[])})
        if self.behavior=='uncertain' and small:
            return Response(status='timeout',error_type='fixture_uncertainty',usage={'input_tokens':10,'cached_input_tokens':0,'output_tokens':2,'total_tokens':12})
        value='x*x' if node=='square' else '-x'
        if self.behavior=='public_failure' and small:value='x+1'
        (self.workspace/(node+'.py')).write_text(f'def run(x):\n    return {value}\n')
        if self.behavior=='protected_write' and small:(self.workspace/'protected.txt').write_text('tampered')
        report={'summary':'Synthetic backend edited fixture source','changedArtifacts':[node+'.py'],'publicChecks':[],
                'unresolved':[],'usedExperienceIds':[x['versionId'] for x in payload['experiences'].get('experiences',[])],'escalate':False}
        return Response(text=json.dumps(report),thread_id=request.request_id,usage={'input_tokens':10,'cached_input_tokens':0,'output_tokens':2,'total_tokens':12},elapsed_seconds=.001)


def fixture_plan():
    plan_id='fixture-plan'
    nodes=[]
    for name in ('square','negate'):
        nodes.append({'nodeId':name,'planRevisionId':plan_id,'parentWorkItemId':'fixture-task','goal':'Implement '+name,
          'dependsOn':[],'preconditions':[],'acceptanceCriteria':[{'id':name,'description':'Public arithmetic behavior','publicCheck':None}],
          'relevantPaths':[name+'.py'],'relevantSymbols':['run'],'allowedWritePaths':[name+'.py'],'expectedArtifacts':[name+'.py'],
          'publicVerificationCommands':[],'estimatedDifficulty':'routine','delegationSuitability':'bounded','supersedesNodeIds':[]})
    return {'planRevisionId':plan_id,'taskInstanceId':'fixture-task','previousRevisionId':None,'nodes':nodes,
            'continuedNodeIds':[],'cancelledNodeIds':[],'contextHash':digest({}),'plannerInvocationId':'fixture-plan-generation'}


def run_fixture(output):
    output=Path(output)
    if output.exists():raise ValueError('Fixture output already exists; preserve the previous result')
    output.mkdir(parents=True)
    cases=[]
    for behavior in ('success','public_failure','integration_failure','protected_write','uncertain','budget'):
        root=output/behavior;root.mkdir()
        with tempfile.TemporaryDirectory(prefix='observatory-experience-fixture-') as temporary:
            workspace=Path(temporary)/'actor';workspace.mkdir();(workspace/'protected.txt').write_text('original')
            plan=fixture_plan();backend=FixtureBackend(workspace,behavior)
            budget=Budget(1 if behavior=='budget' else 6,1000,60)
            ledger=UsageLedger(root/'accounting',{'fixture-small':{'input':1,'cached':.1,'output':1},'fixture-large':{'input':20,'cached':2,'output':20}})
            calls=Invocations(root/'invocations',backend,ledger,budget,origin='fixture')
            store=CheckpointStore(root/'checkpoints',workspace,base_commit='fixture-base',environment_digest='fixture-stdlib')
            checks={name:{'argv':[sys.executable,'-c',f'from {name} import run; assert run(3)=={9 if name=="square" else -3}; assert run(0)==0']} for name in ('square','negate')}
            verifier=PublicVerifier(checks,['protected.txt'],root/'public-checks')
            packet={'experiences':[{'versionId':'prior-square','experienceId':'prior-square','version':1,'admission':'publicly_supported',
                                   'granularity':'subtask','kind':'procedure','procedure':['Multiply the input by itself'],'preconditions':['Numeric input'],
                                   'postconditions':['Square returned'],'requiredTools':[],'failureConditions':[]}]}
            def memory(node,phase,history):return packet if node['nodeId']=='square' else {'experiences':[]}
            observations=[{'reuseId':str(n),'predictionTarget':'public_integrated_completion','censoring':'observed','terminalSequence':0,
                'arm':'HRM','executorId':'fixture-small','experienceVersionIds':['prior-square'],'taskInstanceId':'earlier-'+str(n),'outcome':'pass'} for n in range(20)]
            config={'mode':'frozen_memory','watermark':0,'memory_snapshot_id':'fixture-snapshot','policy_version':'fixture-policy',
              'executor_cost_estimates':{'fixture-small':1,'fixture-large':20},'public_reuse_observations':observations,
              'models':{'fixture-small':{'reasoning_effort':'low'},'fixture-large':{'reasoning_effort':'low'}}}
            policy=RoutingPolicy(small='fixture-small',large='fixture-large')
            def integrate(node,attempt,source):
                receipt,_=verifier.verify(node,attempt,source,scope='integration')
                if behavior=='integration_failure' and len(backend.calls)==1:
                    receipt['verdict']='fail';receipt['criterionResults'][0]['verdict']='fail'
                return receipt
            runner=ParentRunner(task={'task_id':'fixture-task','prompt':'Implement independently checkable square and negate functions'},arm='HRM',workspace=workspace,
                checkpoints=store,verifier=verifier,invocations=calls,policy=policy,memory=memory,output=root/'parent',config=config,integrate=integrate)
            result=runner.run(plan)
            expected='uncertain' if behavior=='uncertain' else 'budget_exhausted' if behavior=='budget' else 'completed'
            assert result['public_state']==expected,(behavior,result)
            grade=None
            if expected=='completed':
                restored=Path(temporary)/'independent';replay_snapshot(result['artifact'],restored)
                import subprocess
                grades=[subprocess.run(c['argv'],cwd=restored,capture_output=True).returncode==0 for c in checks.values()]
                assert all(grades);assert (restored/'protected.txt').read_text()=='original'
                grade={'passed':True,'tests_collected':len(grades),'source_only_independent_replay':True,'score_label':'fixture control-flow verification, not benchmark/model quality'}
            if behavior in ('public_failure','integration_failure','protected_write'):
                assert [c['model'] for c in backend.calls[:2]]==['fixture-small','fixture-large']
                assert backend.calls[1]['handoff'], 'Fallback must receive prior attempt evidence'
                assert len(list((root/'invocations').glob('*/completion.json')))==3
            if behavior=='uncertain':assert len(backend.calls)==1
            if behavior=='budget':assert len(backend.calls)==1 and budget.used_invocations==1
            cases.append({'case':behavior,'passed':True,'public_state':result['public_state'],'simulated_backend_calls':len(backend.calls),'independent_replay':grade,'fixture_only':True})
    report={'schema_version':1,'scope':'Deterministic software mechanism checks with a synthetic backend. No Luna/Sol inference or economic result.',
        'cases':cases,'passed':all(x['passed'] for x in cases),'actual_model_calls':0,'target90_result':None}
    write_new(output/'report.json',report);return report
