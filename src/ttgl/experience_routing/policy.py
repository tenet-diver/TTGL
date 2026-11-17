"""Transparent executor selection from public integrated reuse, not self-confidence."""
from __future__ import annotations
import math
import random
from .io import digest


class RoutingPolicy:
    def __init__(self, *, small, large, threshold=.9, minimum_independent_tasks=3,
                 prior_successes=1,prior_failures=1,exploration_probability=0,seed=0,mode='outcome_aware'):
        if mode not in ('outcome_aware','all_large','cheap_first','similarity_only'):
            raise ValueError('Unknown routing policy')
        if not 0<=exploration_probability<=1 or not 0<=threshold<=1:
            raise ValueError('Invalid routing probabilities')
        self.small,self.large,self.threshold=small,large,threshold
        self.minimum=minimum_independent_tasks
        self.a,self.b=prior_successes,prior_failures
        self.exploration=exploration_probability
        self.random=random.Random(seed);self.mode=mode

    def select(self,node,checkpoint,packet,observations,context):
        evidence=[]
        selected_experiences=[e['versionId'] for e in packet.get('experiences',[])]
        for row in observations:
            if row.get('predictionTarget')!='public_integrated_completion' or row.get('censoring')!='observed' or row.get('terminalSequence',math.inf)>context['watermark'] or row.get('arm')!=context['arm']:
                continue
            if row.get('executorId')==self.small and set(row.get('experienceVersionIds',[]))&set(selected_experiences):
                evidence.append(row)
        independent={r['taskInstanceId'] for r in evidence}
        # Correlated repeats from a parent contribute at most one outcome.
        by_task={}
        for row in evidence:by_task.setdefault(row['taskInstanceId'],[]).append(row)
        successes=sum(all(r['outcome']=='pass' for r in rows) for rows in by_task.values())
        p=(successes+self.a)/(len(by_task)+self.a+self.b) if by_task else None
        costs=context.get('cost_estimates',{})
        small_cost,large_cost=costs.get(self.small),costs.get(self.large)
        expected=None if p is None or small_cost is None or large_cost is None else small_cost+(1-p)*large_cost+context.get('handoff_cost',0)
        eligible=(node['delegationSuitability']=='bounded' and bool(selected_experiences)
                  and all(e.get('admission')=='publicly_supported' for e in packet.get('experiences',[])))
        reason=['sparse_public_executor_evidence'];choose=self.large;explore=False;probability=1.0
        if self.mode=='cheap_first':choose=self.small;reason=['registered_cheap_first']
        elif self.mode=='similarity_only' and eligible:choose=self.small;reason=['registered_similarity_only']
        elif self.mode=='outcome_aware' and eligible and len(independent)>=self.minimum and p is not None and p>=self.threshold and expected is not None and large_cost is not None and expected<large_cost:
            choose=self.small;reason=['calibrated_public_reuse','lower_expected_total_cost']
        elif self.mode=='all_large':reason=['matched_all_large_control']
        elif self.exploration>0:
            explore=self.random.random()<self.exploration
            choose=self.small if explore else self.large
            probability=self.exploration if explore else 1-self.exploration
            reason=['registered_development_exploration' if explore else 'large_under_uncertainty']
        decision={'decisionId':digest([context['task'],context['arm'],node['nodeId'],checkpoint['checkpointId'],context['policy_version']]),
          'taskInstanceId':context['task'],'planNodeId':node['nodeId'],'checkpointId':checkpoint['checkpointId'],
          'memorySnapshotId':context['snapshot'],'policyVersion':context['policy_version'],
          'predictionTarget':'public_integrated_completion','selectedExecutorId':choose,
          'candidateExecutorIds':[self.small,self.large],'predictedSuccess':{self.small:p,self.large:None},
          'predictedTotalCost':{self.small:expected,self.large:large_cost},'predictedLatencyMs':{self.small:None,self.large:None},
          'experienceVersionIds':selected_experiences,'reasonCodes':reason,'assignmentProbability':probability,
          'exploration':explore,'publicEvidenceIds':[r['reuseId'] for r in evidence]}
        return decision


def calibrate(observations, *, minimum=3, thresholds=(.8,.9,.95), small_cost=1,large_cost=20):
    """Development-only threshold selection; missing/censored outcomes remain counted."""
    rows=[x for x in observations if x.get('split')=='router_development' and x.get('censoring')=='observed'
          and x.get('predictionTarget')=='public_integrated_completion']
    if not rows:raise ValueError('No eligible public development calibration observations')
    parents={r['taskInstanceId'] for r in rows}
    if len(parents)<minimum:raise ValueError('Too few independent development parents')
    report=[]
    for threshold in thresholds:
        selected=[r for r in rows if isinstance(r.get('predictedSuccess'),(int,float)) and r['predictedSuccess']>=threshold]
        losses=sum(r['outcome']!='pass' for r in selected)
        cost=sum(small_cost+(large_cost if r['outcome']!='pass' else 0) for r in selected)+(len(rows)-len(selected))*large_cost
        brier=sum(((r.get('predictedSuccess') if isinstance(r.get('predictedSuccess'),(int,float)) else .5)-(r['outcome']=='pass'))**2 for r in rows)/len(rows)
        report.append({'threshold':threshold,'coverage':len(selected)/len(rows),'public_failures':losses,'scenario_cost':cost,'brier':brier})
    valid=[r for r in report if r['public_failures']==0]
    return {'thresholds':report,'selected':min(valid,key=lambda r:r['scenario_cost']) if valid else None,
            'development_parents':len(parents),'censored_or_ineligible':len(observations)-len(rows),'target':'public_integrated_completion'}
