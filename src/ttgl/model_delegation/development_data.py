"""Build scorer tables from sealed development outcomes and public candidates.

Only offline development fitting sees labels. Feature generation is shared with
the live native cascade, avoiding training/serving context or formatting drift.
"""
import json
from pathlib import Path
from .native_swe import public_contract
from .accumulation import retrieve
from .campaign import coding_candidate_text,scenario_cost
from ..experience_routing.io import read,digest


def collect(config, completion, snapshot):
    if completion['stage']!='development':raise ValueError('Development table only')
    records=[];seen=set()
    for row in completion['results']:
        identity=(row['task_id'],row['model'])
        if identity in seen:raise ValueError('Duplicate native development endpoint')
        seen.add(identity)
        episode=Path(row['episode']);result=read(episode/'completion.json')
        if result['worker_invocations'] or result['status'] not in ('completed','public_failure'):
            raise ValueError('Known matched standalone candidates required')
        folder=Path(config['eligibility_root'])/row['task_id']
        task=public_contract(folder/'private-task',folder/'base')
        packet=retrieve(snapshot,{**task['features'],'task_id':task['task_id'],'goal':task['prompt']},maximum_bytes=config['maximum_packet_bytes'])
        if digest(packet)!=result['packet_hash']:raise ValueError('Development knowledge context differs from candidate')
        public=json.dumps({'goal':task['prompt'],'knowledge':packet},sort_keys=True)
        records.append({'task_id':row['task_id'],'model':row['model'],'public_input':public,
            'candidate_text':coding_candidate_text(task,result,row['source'],read(episode/'public-check.json')),
            'resolved':bool(row['resolved'] and not row['invalid_paths'] and result['public_check_passed']),
            'official_resolved':row['resolved'],'scope_flags':row['invalid_paths'],
            'scenario_cost':scenario_cost(result['native_usage'],config['rates'][row['model']]),
            'native_usage':result['native_usage'],'source_receipt':str(episode/'completion.json'),
            'quality_scope':'Official completion with valid scope and prescribed public check; raw official outcome retained separately'})
    return records
