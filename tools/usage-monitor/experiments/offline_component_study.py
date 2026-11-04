#!/usr/bin/env python3
"""Synthetic component comparisons with oracle-guided recovery; NOT agent trials."""
import argparse,hashlib,json,pathlib,tempfile,time
from datetime import datetime,timezone
import context_pilot as pilot

ARMS=('baseline','deterministic_projection','older_masking','reversible_handles','projection_with_handles')
def encode(x):return json.dumps(x,ensure_ascii=False,separators=(',',':'))
def size(x):return len(encode(x).encode())

def study():
    results=[]
    with tempfile.TemporaryDirectory(prefix='ttgl-components-') as t:
        data=pilot.fixtures(pathlib.Path(t))
        for case,observations in data.items():
            originals={x['observation_ref']:encode(x).encode() for x in observations}
            hashes={k:hashlib.sha256(v).hexdigest() for k,v in originals.items()}
            def retrieve(ref):
                raw=originals[ref]
                if hashlib.sha256(raw).hexdigest()!=hashes[ref]:raise ValueError('archive integrity failure')
                return json.loads(raw)
            for arm in ARMS:
                start=time.perf_counter_ns();view=[];checks=[];exposure=0;retrieval_bytes=0;retrievals=0
                for observation in observations:
                    ref=observation['observation_ref']
                    if arm in ('deterministic_projection','projection_with_handles'):
                        item={'observation_ref':ref,'representation':'failed rows only; not semantically equivalent',
                              'rows':[r for r in observation['rows'] if r['status']=='failed'],
                              'original_sha256':hashes[ref],'original_ref':ref}
                        if arm=='deterministic_projection':
                            item.pop('original_ref');item.pop('original_sha256')
                    elif arm=='reversible_handles':
                        item={'observation_ref':ref,'original_sha256':hashes[ref],'original_ref':ref}
                    else:item=observation
                    view.append(item)
                    if arm=='older_masking':
                        view=[{'observation_ref':x['observation_ref'],'original_ref':x['observation_ref'],
                               'original_sha256':hashes[x['observation_ref']]} for x in view[:-1]]+[view[-1]]
                    exposure+=size(view)
                    # An explicit oracle knows which source to recover. This is not agent behavior.
                    available=view[-1]
                    if 'rows' not in available:
                        available=retrieve(ref);retrievals+=1;retrieval_bytes+=len(originals[ref]);exposure+=len(originals[ref])
                    failed=[r for r in available['rows'] if r['status']=='failed']
                    checks.append(len(failed)==1 and failed[0]['id']=='item-117' and failed[0]['message']==observation['rows'][117]['message'])
                for phase,index in [(0,83),(1,41)]:
                    ref=observations[phase]['observation_ref'];exposure+=size(view)
                    found=next((r for x in view if x['observation_ref']==ref for r in x.get('rows',[]) if r['id']==f'item-{index:03}'),None)
                    if found is None and arm!='deterministic_projection':
                        original=retrieve(ref);retrievals+=1;retrieval_bytes+=len(originals[ref]);exposure+=len(originals[ref]);found=original['rows'][index]
                    checks.append(found is not None and found['checksum']==observations[phase]['rows'][index]['checksum'])
                results.append({'case':case,'arm':arm,'checks_passed':sum(checks),'checks_total':len(checks),
                    'oracle_recovery_calls':retrievals,'oracle_recovery_bytes':retrieval_bytes,
                    'constructed_context_exposure_bytes':exposure,'final_view_bytes':size(view),
                    'transform_and_oracle_runtime_ns':time.perf_counter_ns()-start,
                    'provider_tokens':None,'model_task_quality':None,'cost_saving':None})
    for row in results:
        baseline=next(x for x in results if x['case']==row['case'] and x['arm']=='baseline')
        row['constructed_exposure_ratio_vs_baseline']=row['constructed_context_exposure_bytes']/baseline['constructed_context_exposure_bytes']
    return {'schema_version':1,'checked_at':datetime.now(timezone.utc).isoformat(),
        'kind':'synthetic offline component diagnostics with oracle-guided recovery',
        'model_calls':0,'headroom_executed':False,'results':results,
        'limitations':['Constructed context exposure bytes are not provider tokens or charges.',
            'Recovery source selection is supplied by an oracle; no model decision or task-quality claim.',
            'Recovery payload is charged once in this exposure proxy, not assumed to remain in subsequent requests.',
            'Only two frozen synthetic formats; no coding benchmark or generalization claim.',
            'No Headroom, Mem0, local model, hierarchy, principle, stage, graph or cache efficacy tested.']}

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=pathlib.Path,required=True);a=p.parse_args()
    r=study();a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(r,indent=2)+'\n')
    print(json.dumps({'comparisons':len(r['results']),'checks_passed':sum(x['checks_passed'] for x in r['results']),
                      'checks_total':sum(x['checks_total'] for x in r['results']),'model_calls':0}))
