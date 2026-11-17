"""Native accounting reuses validated cumulative deltas; role views are separate."""
from __future__ import annotations
from dataclasses import dataclass
import math
import time
from pathlib import Path
from ..personal import USAGE_FIELDS, _account_usage
from .io import append, read, digest, now

ROLES = {'annotation','extraction','embedding','applicability','planning','small_execution',
         'large_execution','public_verification','integration','recovery','research_audit'}
PURPOSES = {'operational','seed_construction','research_measurement'}


class UsageLedger:
    def __init__(self, root, rates=None):
        self.root = Path(root)
        self.path = self.root/'usage-ledger.jsonl'
        self.rates = rates or {}
        self.state = {'usage':{k:0 for k in USAGE_FIELDS},'usage_complete':{k:True for k in USAGE_FIELDS},
                      'usage_threads':{},'usage_by_model':{},'usage_accounting_issues':[]}
        self.records = {}
        if self.path.exists():
            import json
            for line in self.path.read_text().splitlines():
                row=json.loads(line)
                if row['kind']=='native':
                    self.records[row['invocation_id']]=row
                    self.state=row['accounting_state']

    def record(self, request, response, role, purpose, artifact_hash, *, origin='native', response_ids=()):
        if role not in ROLES or purpose not in PURPOSES:
            raise ValueError('Unknown inference role or cost centre')
        signature = digest({'model':request.model,'thread':response.thread_id,'usage':response.usage,
                            'scope':response.usage_scope,'evidence':response.usage_evidence,'artifact':artifact_hash})
        old=self.records.get(request.request_id)
        if old:
            if old['signature']!=signature:
                raise ValueError('Immutable invocation accounting conflict')
            return old
        # All-zero upstream defaults cannot establish free inference.
        if response.usage and all(response.usage.get(k)==0 for k in ('input_tokens','output_tokens','total_tokens')):
            response.usage={k:None for k in USAGE_FIELDS}
            response.usage_evidence='all_zero_upstream_defaults'
        ids=set(response_ids)
        seen={identity for row in self.records.values() for identity in row.get('response_ids',[])}
        if ids and ids <= seen:
            accounted={'delta':{k:0 for k in USAGE_FIELDS},'issues':['duplicate_native_response_identity']}
        elif ids & seen:
            accounted={'delta':{k:None for k in USAGE_FIELDS},'issues':['partial_native_response_overlap_requires_reconciliation']}
        else:accounted=_account_usage(self.state,request,response)
        delta=accounted['delta']
        delta['total_tokens']=delta['input_tokens']+delta['output_tokens'] if delta['input_tokens'] is not None and delta['output_tokens'] is not None else None
        rate=self.rates.get(request.model)
        cost=None
        if rate and all(delta.get(k) is not None for k in ('input_tokens','cached_input_tokens','output_tokens')):
            i,c,o=(delta[k] for k in ('input_tokens','cached_input_tokens','output_tokens'))
            if c<=i:
                cost=((i-c)*rate['input']+c*rate['cached']+o*rate['output'])/1e6
                # Cache-write rates are an explicit premium over ordinary input.
                if rate.get('cache_write_premium') is not None:
                    writes=delta.get('cache_write_input_tokens')
                    cost=None if writes is None else cost+writes*rate['cache_write_premium']/1e6
        import copy
        row={'kind':'native','invocation_id':request.request_id,'signature':signature,'role':role,'purpose':purpose,
             'model':request.model,'thread_id':response.thread_id,'response_ids':sorted(set(response_ids)),
             'measurement_origin':origin,'usage_scope':response.usage_scope,'usage_evidence':response.usage_evidence,
             'delta':delta,'scenario_cost':cost,'actual_cash':None,'provider_estimate':None,'elapsed_seconds':response.elapsed_seconds,
             'accounting_issues':accounted['issues'],'raw_artifact_hash':artifact_hash,
             'accounting_state':copy.deepcopy(self.state),'recorded_at':now()}
        append(self.path,row);self.records[request.request_id]=row
        return row

    def logical_shared_charge(self, invocation_id, arm, reason='shared_initial_plan'):
        if invocation_id not in self.records:
            raise ValueError('Logical charge must cite one measured actual invocation')
        row={'kind':'logical_policy_charge','invocation_id':invocation_id,'arm':arm,'reason':reason,
             'scenario_cost':self.records[invocation_id]['scenario_cost'],'additional_actual_spending':False}
        path=self.root/'logical-policy-ledger.jsonl'
        import json
        prior=[json.loads(x) for x in path.read_text().splitlines()] if path.exists() else []
        if not any(x['invocation_id']==invocation_id and x['arm']==arm for x in prior):append(path,row)
        return row

    def totals(self):
        rows=list(self.records.values());costs=[r['scenario_cost'] for r in rows]
        return {'actual_invocations':len(rows),'observed_partial_tokens':sum(r['delta']['total_tokens'] or 0 for r in rows),
                'native_tokens':sum(r['delta']['total_tokens'] for r in rows) if all(r['delta']['total_tokens'] is not None for r in rows) else None,
                'scenario_cost':sum(costs) if all(c is not None for c in costs) else None,
                'known_scenario_cost':sum(c for c in costs if c is not None),'unpriced_invocations':sum(c is None for c in costs),
                'cash_expense':None,'logical_shared_charges_included':False}


class BudgetExhausted(RuntimeError):pass


@dataclass
class Budget:
    maximum_invocations:int
    maximum_tokens:int
    maximum_elapsed_seconds:float
    used_invocations:int=0
    used_tokens:int=0
    unknown_usage:bool=False

    def __post_init__(self):
        if type(self.maximum_invocations) is not int or self.maximum_invocations<=0 or type(self.maximum_tokens) is not int or self.maximum_tokens<=0 or not math.isfinite(self.maximum_elapsed_seconds) or self.maximum_elapsed_seconds<=0:
            raise ValueError('Every stage needs finite positive invocation, token and elapsed budgets')
        self.started=time.monotonic()

    def reserve(self):
        if self.unknown_usage or self.used_invocations>=self.maximum_invocations or self.used_tokens>=self.maximum_tokens or self.remaining_seconds<=0:
            raise BudgetExhausted('Parent budget exhausted or inference usage uncertain')
        self.used_invocations+=1

    def charge(self, row):
        tokens=row['delta']['total_tokens']
        if tokens is None:self.unknown_usage=True
        else:self.used_tokens+=tokens

    @property
    def remaining_seconds(self):
        return max(0,self.maximum_elapsed_seconds-(time.monotonic()-self.started))

    def receipt(self):
        return {'maximum_invocations':self.maximum_invocations,'used_invocations':self.used_invocations,
                'maximum_tokens':self.maximum_tokens,'observed_tokens':self.used_tokens,'unknown_usage':self.unknown_usage,
                'maximum_elapsed_seconds':self.maximum_elapsed_seconds,'elapsed_seconds':time.monotonic()-self.started,
                'token_overshoot':max(0,self.used_tokens-self.maximum_tokens),'enforcement':'before-call checks plus per-call timeout; in-flight token overshoot retained'}
