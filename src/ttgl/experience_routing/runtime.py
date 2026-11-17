"""Serial reference runtime: immutable attempts, public fallback and integration."""
from __future__ import annotations
import json
import time
from pathlib import Path
from ..personal import Request
from .contracts import validate
from .io import digest,write_new,read,append,now
from .plans import PlanState
from .ledger import BudgetExhausted

WORKER_SCHEMA={'type':'object','additionalProperties':False,'required':['summary','changedArtifacts','publicChecks','unresolved','usedExperienceIds','escalate'],
 'properties':{'summary':{'type':'string'},'changedArtifacts':{'type':'array','items':{'type':'string'}},
 'publicChecks':{'type':'array','items':{'type':'string'}},'unresolved':{'type':'array','items':{'type':'string'}},
 'usedExperienceIds':{'type':'array','items':{'type':'string'}},'escalate':{'type':'boolean'}}}


class RetainedInvocation(RuntimeError):pass
class UncertainInvocation(RuntimeError):pass


class Invocations:
    def __init__(self,root,backend,ledger,budget,*,client=None,origin='native'):
        self.root=Path(root);self.backend=backend;self.ledger=ledger;self.budget=budget;self.client=client;self.origin=origin

    def call(self,request,role,purpose='operational'):
        folder=self.root/request.request_id
        if folder.exists():raise RetainedInvocation('Started/retained invocation cannot be replayed: '+request.request_id)
        self.budget.reserve();folder.mkdir(parents=True,exist_ok=False)
        write_new(folder/'started.json',{'invocation_id':request.request_id,'model':request.model,'role':role,'purpose':purpose,
                  'request_hash':digest(request.prompt),'schema_hash':digest(request.schema),'started_at':now(),'automatic_retries':0})
        try:
            response=self.backend.complete(request)
            # Response is a derived view. Exact native streams stay in local S3
            # through RecordedCodexBackend; fixtures explicitly mark synthetic data.
            derived={'text':response.text,'thread_id':response.thread_id,'status':response.status,'usage':response.usage,
                     'usage_scope':response.usage_scope,'usage_evidence':response.usage_evidence,'error_type':response.error_type}
            artifact=getattr(self.backend,'last_native_artifact_hash',None) or digest(derived);write_new(folder/'response.json',derived)
            usage=self.ledger.record(request,response,role,purpose,artifact,origin=self.origin,
                                     response_ids=getattr(self.backend,'last_response_ids',()))
            self.budget.charge(usage)
            if response.status!='completed':raise UncertainInvocation('Invocation did not complete; preserve and reconcile')
            result=json.loads(response.text)
            from jsonschema import Draft202012Validator
            Draft202012Validator(request.schema).validate(result)
            write_new(folder/'completion.json',{'invocation_id':request.request_id,'response_hash':artifact,
                                               'usage_receipt':request.request_id,'completed_at':now()})
            return result,usage
        except BaseException as error:
            write_new(folder/'uncertain.json',{'invocation_id':request.request_id,'error':type(error).__name__,
                                              'reason':str(error)[:1000],'automatic_retry':False,'recorded_at':now()})
            raise UncertainInvocation(str(error)) from error


class ParentRunner:
    def __init__(self, *, task,arm,workspace,checkpoints,verifier,invocations,policy,memory,output,config,client=None,integrate=None,replan=None,execution_context=None,verifier_client=None):
        self.task,self.arm=task,arm;self.workspace=Path(workspace);self.checkpoints=checkpoints;self.verifier=verifier
        self.calls=invocations;self.policy=policy;self.memory=memory;self.output=Path(output);self.config=config
        self.client=client;self.integrate=integrate;self.replan=replan;self.execution_context=execution_context;self.verifier_client=verifier_client
        self.output.mkdir(parents=True,exist_ok=True)

    def emit(self,kind,value):
        append(self.output/'public-events.jsonl',{'kind':kind,'payload':value,'at':now()})
        if self.client:
            if kind=='verification':
                target=self.verifier_client or self.client
                for criterion in value['criterionResults']:
                    retained=[]
                    for reference in criterion['evidenceArtifactRefs']:
                        path=self.verifier.root/(reference+'.json')
                        if not path.is_file():raise ValueError('Public verification source artifact is unavailable')
                        stored=target.retain_file(path,kind='public-verification',identity=value['attemptId']+':'+value['scope']+':'+criterion['criterionId'])
                        retained.append(stored['artifactId'])
                    criterion['evidenceArtifactRefs']=retained
            target=self.verifier_client if kind in ('verification','reuse','barrier') and self.verifier_client else self.client
            target.record(kind,value)

    def request(self,identity,model,kind,prompt,schema,read_only=False):
        return Request(identity,model,kind,prompt,self.output,schema,max(.01,self.calls.budget.remaining_seconds),
                       thread_id=None,read_only=read_only,reasoning_effort=self.config['models'][model]['reasoning_effort'])

    def run(self,plan,*,plan_usage_id=None):
        if (self.output/'assignment-started.json').exists():raise RetainedInvocation('Assignment already started; no automatic resume')
        start=time.monotonic();write_new(self.output/'assignment-started.json',{'task':self.task['task_id'],'arm':self.arm,'started_at':now(),
            'plan_hash':digest(plan),'configuration_hash':digest(self.config),'fixture_only':getattr(self.calls.backend,'fixture_only',False)})
        state=PlanState(plan,self.calls.budget);replans=0;accepted_artifacts=[]
        if plan_usage_id:self.calls.ledger.logical_shared_charge(plan_usage_id,self.arm)
        self.emit('plan',plan)
        uncertain=None
        try:
            while ready:=state.ready():
                node=ready[0];checkpoint=self.checkpoints.capture(self.task['task_id'],node['nodeId'],node,accepted_artifacts)
                public_checkpoint={k:v for k,v in checkpoint.items() if k not in ('source_manifest','archive_path')}
                if self.client:
                    stored=self.client.retain_file(checkpoint['archive_path'],kind='checkpoint',identity=checkpoint['checkpointId'])
                    public_checkpoint['artifactArchiveId']=stored['artifactId']
                self.emit('checkpoint',public_checkpoint)
                packet=self.memory(node,'plan_node',None)
                context={'task':self.task['task_id'],'arm':self.arm,'watermark':self.config['watermark'],
                         'snapshot':self.config['memory_snapshot_id'],'policy_version':self.config['policy_version'],
                         'cost_estimates':self.config.get('executor_cost_estimates',{}),'handoff_cost':self.config.get('handoff_cost',0)}
                decision=self.policy.select(node,checkpoint,packet,self.config.get('public_reuse_observations',[]),context)
                self.emit('routing',validate('routing',decision))
                sequence=[decision['selectedExecutorId']]
                if sequence[0]==self.policy.small and self.arm!='S0' and self.config.get('maximum_large_fallbacks_per_node',1):sequence.append(self.policy.large)
                history=[];accepted=False
                for ordinal,executor in enumerate(sequence):
                    # Even a fallback after integration failure starts from the
                    # complete pre-node state, including accepted dependencies.
                    self.checkpoints.restore(checkpoint)
                    if self.execution_context:self.execution_context.before_attempt(self.workspace)
                    attempt=digest([self.task['task_id'],self.arm,plan['planRevisionId'],node['nodeId'],ordinal])
                    prompt=json.dumps({'parent':{k:self.task[k] for k in ('task_id','prompt')},'node':node,
                      'checkpoint':public_checkpoint,'completedDependencies':accepted_artifacts,'experiences':packet,
                      'priorAttempts':history,'remainingBudget':self.calls.budget.receipt(),
                      'instructions':'Build on the supplied public evidence; do not repeat failed approaches without new evidence. Respect allowed write paths. Normally make two or three meaningfully different checked repair attempts before requesting help; request help earlier only when no credible useful independent attempt remains, and state the concrete reason. Preserve integration budget. Verify your work and explicitly report unresolved criteria or escalation.'})
                    self.emit('attempt',{'attemptId':attempt,'taskInstanceId':self.task['task_id'],'planNodeId':node['nodeId'],
                                        'planRevisionId':plan['planRevisionId'],'checkpointId':checkpoint['checkpointId'],'executorId':executor,'arm':self.arm,'ordinal':ordinal})
                    request=self.request(attempt,executor,'coding',prompt,WORKER_SCHEMA)
                    result,usage=self.calls.call(request,'small_execution' if executor==self.policy.small else 'large_execution')
                    if self.execution_context:self.execution_context.after_attempt(self.workspace)
                    candidate=self.checkpoints.capture(self.task['task_id'],node['nodeId']+':candidate:'+attempt,node,accepted_artifacts)
                    write_new(self.output/'patches'/(attempt+'.json'),candidate)
                    candidate_archive=self.client.retain_file(candidate['archive_path'],kind='candidate-source',identity=attempt) if self.client else None
                    artifact_id=candidate_archive['artifactId'] if candidate_archive else candidate['checkpointId']
                    artifact_check=self.checkpoints.admissible(checkpoint,node['allowedWritePaths'],self.verifier.protected)
                    verification,timing=self.verifier.verify(node,attempt,self.workspace,timeout=min(60,self.calls.budget.remaining_seconds))
                    self.emit('verification',verification);append(self.output/'timing-ledger.jsonl',{'kind':'public_verification','attempt':attempt,**timing})
                    integration=None
                    if artifact_check['passed'] and verification['verdict']=='pass' and not result['unresolved'] and not result['escalate']:
                        if self.integrate:integration=self.integrate(node,attempt,self.workspace)
                        else:integration,_=self.verifier.verify(node,attempt,self.workspace,scope='integration',timeout=min(60,self.calls.budget.remaining_seconds))
                        self.emit('verification',integration)
                        accepted=integration['verdict']=='pass'
                    trigger='accepted' if accepted else 'out_of_scope_artifact' if not artifact_check['passed'] else 'integration_failure' if integration else 'model_requested' if result['escalate'] else 'unresolved_requirement' if result['unresolved'] else 'public_contract_failure'
                    outcome={'attemptId':attempt,'taskInstanceId':self.task['task_id'],'arm':self.arm,'status':'accepted' if accepted else 'public_failure',
                             'artifactId':artifact_id,'verificationId':verification['verificationId'],
                             'integrationId':integration['verificationId'] if integration else None,'trigger':trigger,
                             'artifactCheck':artifact_check,'completionReport':result,'usageInvocationId':usage['invocation_id']}
                    self.emit('attempt-event',outcome)
                    if self.client and integration:
                        self.emit('reuse',{'reuseId':digest([attempt,'reuse']),'attemptId':attempt,'experienceVersionIds':decision['experienceVersionIds'],
                          'publicVerificationIds':[verification['verificationId']],'integrationVerificationId':integration['verificationId'],
                          'outcome':'pass' if accepted else 'fail','predictionTarget':'public_integrated_completion','executorId':executor,
                          'taskInstanceId':self.task['task_id'],'family':self.task.get('family','unknown'),'arm':self.arm,
                          'terminalSequence':self.config['watermark']+1,'censoring':'observed','assignmentProbability':decision['assignmentProbability']})
                    history.append({'executor':executor,'completion':result,'artifactCheck':artifact_check,'publicVerification':verification,
                                    'integration':integration,'trigger':trigger,'candidateArtifactId':candidate['checkpointId']})
                    if accepted:
                        accepted_artifacts.append(artifact_id);state.finish(node['nodeId'],attempt,True);break
                    self.checkpoints.restore(checkpoint)
                    if ordinal==0 and len(sequence)>1:packet=self.memory(node,'recovery',history)
                if not accepted:
                    state.finish(node['nodeId'],history[-1]['candidateArtifactId'],False)
                    if self.replan and replans<self.config.get('maximum_parent_replans',1):
                        revised=self.replan(state,history,self.calls.budget)
                        state=PlanState(revised,self.calls.budget,previous=state);plan=revised;replans+=1;self.emit('plan',revised)
                    else:break
        except (UncertainInvocation,RetainedInvocation,RuntimeError) as error:
            uncertain={'type':type(error).__name__,'reason':str(error),'reconciliation_required':isinstance(error,(UncertainInvocation,RetainedInvocation))}
        whole=None
        if not uncertain and state.completed:
            criteria={c['id']:c for n in plan['nodes'] for c in n['acceptanceCriteria']}
            whole_node={'nodeId':self.task['task_id'],'acceptanceCriteria':list(criteria.values())}
            whole,_=self.verifier.verify(whole_node,attempt,self.workspace,scope='whole_task',timeout=min(60,max(.01,self.calls.budget.remaining_seconds)),contract_hash=digest(plan))
            self.emit('verification',whole)
        final=self.checkpoints.capture(self.task['task_id'],'final',{'plan':plan},accepted_artifacts)
        retained_final=self.client.retain_file(final['archive_path'],kind='final-source',identity=self.task['task_id']+':'+self.arm+':final') if self.client else None
        receipt={'retained_final_artifact':retained_final,'task_id':self.task['task_id'],'arm':self.arm,'public_state':('uncertain' if uncertain['reconciliation_required'] else 'budget_exhausted' if uncertain['type']=='BudgetExhausted' else 'infrastructure_error') if uncertain else 'completed' if state.completed and whole and whole['verdict']=='pass' else 'unsuccessful',
                 'independent_grade':None,'whole_task_public_verification':whole,'node_states':state.states,'artifact':final,'budget':self.calls.budget.receipt(),
                 'end_to_end_seconds':time.monotonic()-start,'usage':self.calls.ledger.totals(),'uncertainty':uncertain,
                 'replans':replans,'study_mode':self.config['mode'],'fixture_only':getattr(self.calls.backend,'fixture_only',False)}
        write_new(self.output/'completion.json',receipt)
        # Public trace preparation is queued by the driver only after exact raw
        # retention and assignment ownership reconcile. Hidden grades are absent.
        return receipt
