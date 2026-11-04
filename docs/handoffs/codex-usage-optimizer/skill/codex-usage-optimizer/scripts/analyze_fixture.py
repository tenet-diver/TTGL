#!/usr/bin/env python3
"""Reference oversized passing-test-output detector. Normalized fixtures only.
No private-log discovery, model calls, cloud writes, command execution or changes.
"""
import argparse,json,hashlib,math
from collections import defaultdict
from pathlib import Path

def analyze(data,min_calls=3,min_total_tokens=10000,reduction=None):
 if type(min_calls) is not int or min_calls<1:raise ValueError('min_calls must be positive')
 if type(min_total_tokens) is not int or min_total_tokens<0:raise ValueError('threshold must be nonnegative')
 if reduction is not None and (type(reduction) not in (int,float) or not math.isfinite(reduction) or not 0<=reduction<=1):raise ValueError('scenario fraction must be 0..1')
 groups=defaultdict(list);seen=set();unknown=0
 for row in data['tool_calls']:
  identity=(row['source_id'],row['id'])
  if identity in seen:continue
  seen.add(identity)
  tokens=row.get('model_facing_output_tokens_estimate')
  if tokens is not None and (type(tokens) is not int or tokens<0):raise ValueError('invalid token estimate')
  if row['tool_family']!='test_runner' or row['success'] is not True:continue
  if tokens is None:unknown+=1;continue
  groups[(row['repository_id'],row['command_family'])].append(row)
 proposals=[]
 for (repo,command),rows in sorted(groups.items()):
  total=sum(r['model_facing_output_tokens_estimate'] for r in rows)
  if len(rows)<min_calls or total<min_total_tokens:continue
  identity=hashlib.sha256(json.dumps([repo,command,sorted(r['id'] for r in rows)],sort_keys=True).encode()).hexdigest()[:16]
  scenario=None if reduction is None else total*reduction
  proposals.append({'schema_version':1,'id':'proposal-'+identity,'version':1,'title':'Prepare a concise successful-test reporter','recipe_ids':['OPT-001'],'status':'needs_preparation','scope':{'repository_id':repo,'command_family':command,'kind':'task_local'},'evidence_refs':[r['id'] for r in rows],'window':data['window'],'observed':{'eligible_calls':len(rows),'payload_tokens_estimate':total,'metric_provenance':'tokenizer_estimated_model_facing_payload'},'expected':{'basis':'unknown' if reduction is None else 'scenario','payload_tokens_saved':scenario,'lower_payload_tokens_saved':None if scenario is None else 0,'upper_payload_tokens_saved':scenario,'assumed_reduction_fraction':reduction,'model_tokens_saved':None,'cost_saved_usd':None,'elapsed_seconds_saved':None,'assumptions':[] if reduction is None else ['Same eligible calls/window; assumed fractional payload reduction.','No measured reduction in billed tokens, total time or cost.']},'concrete_change':None,'quality_checks':['Verify installed reporter options and config precedence.','Preserve failure diagnostics and exit status.','Run required final task verification.'],'rollback':'Capture and restore exact task-local preimage; avoid overwriting later user edits.','overlap_group':'passing-test-output:'+repo+':'+command,'coverage_notes':['Across dataset, eligible calls with unknown output size: '+str(unknown),'Reference detector only; tool version and a concrete patch still required.']})
 return {'synthetic':data.get('synthetic',False),'detector':'oversized_passing_test_output_v1','suggestions':proposals,'unknown_eligible_sizes':unknown}

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('input');p.add_argument('--min-calls',type=int,default=3);p.add_argument('--min-total-tokens',type=int,default=10000);p.add_argument('--scenario-reduction',type=float);a=p.parse_args()
 try:result=analyze(json.loads(Path(a.input).read_text()),a.min_calls,a.min_total_tokens,a.scenario_reduction)
 except (ValueError,KeyError,TypeError,json.JSONDecodeError) as ex:p.error(str(ex))
 print(json.dumps(result,indent=2))
