"""Metadata-only exposure/reservation inspection. Unknown provenance stays excluded."""
from __future__ import annotations
import json
import os
from pathlib import Path
from .io import file_digest,digest,now

ID_KEYS={'instance_id','task_id','library_id','instance_ids','task_ids','libraries','reserved_ids'}


def identifiers(value,key=''):
    result=set()
    if isinstance(value,dict):
        for k,v in value.items():
            if k in ID_KEYS and isinstance(v,str):result.add(v)
            elif k in ID_KEYS and isinstance(v,list):result.update(x for x in v if isinstance(x,str))
            result.update(identifiers(v,k))
    elif isinstance(value,list):
        for x in value:result.update(identifiers(x,key))
    return result


def inventory(root):
    root=Path(root).resolve();sources=[];excluded=set()
    for directory in ('experiments','results'):
        for p in sorted((root/directory).rglob('*.json')):
            if p.stat().st_size>12_000_000 or p.name not in ('reservation.json','reservation-001.json','manifest.json','task-manifest.json','plan.json','protocol.json','completion.json','stopped.json'):
                continue
            try:data=json.loads(p.read_text())
            except (ValueError,OSError):continue
            ids=identifiers(data);excluded.update(ids)
            sources.append({'path':str(p.relative_to(root)),'sha256':file_digest(p),'task_ids':sorted(ids),
              'owner':str(p.parent.relative_to(root)),'permitted_use':'historical_or_reserved_excluded_pending_specific_audit',
              'contains_reference_material':'unreviewed','annotation_eligibility':'incomplete_provenance'})
    owners=[]
    for p in Path('/proc').iterdir():
        if not p.name.isdigit():continue
        try:cmd=(p/'cmdline').read_bytes().split(b'\0')
        except (OSError,PermissionError):continue
        for token in cmd[:3]:
            name=Path(token.decode(errors='replace')).name
            if name.startswith(('continue_','codex_team_','finish_team_')) and name.endswith('.py'):
                owners.append({'pid':int(p.name),'entrypoint':name,'command_hash':digest(b'\0'.join(cmd))})
    return {'schema_version':1,'at':now(),'sources':sources,'active_owners':owners,'excluded_task_ids':sorted(excluded),
      'source_count':len(sources),'model_calls':0,'new_reservations':0,
      'rule':'All prior/reserved IDs excluded until a source-specific permitted-use and exposure audit; no hidden files opened.'}


def exclusion_registry(report):
    return {'schema_version':1,'task_ids':report['excluded_task_ids'],'metadata_sources':[{'path':x['path'],'sha256':x['sha256'],'owner':x['owner']} for x in report['sources']],
            'alias_keys':['issue_or_pr','normalized_problem_hash','base_commit_family','patch_family','synthetic_parent'],
            'unresolved_aliases':'Exclude rather than assume fresh; gold comparisons belong to evaluator only.'}


def build_splits(tasks,exclusions,seed=17012026):
    import random
    reserved=set(exclusions.get('task_ids',[]));seen=set();groups={};result=[]
    for task in tasks:
        if set(task)-{'task_id','repo','base_commit','problem_hash','issue_or_pr','family','synthetic_parent','split','published_at'}:
            raise ValueError('Split construction accepts metadata only, never solutions or hidden tests')
        key=task['task_id'];group=task.get('synthetic_parent') or task.get('issue_or_pr') or task.get('problem_hash') or key
        if key in seen or key in reserved:raise ValueError('Duplicate, exposed or reserved task: '+key)
        seen.add(key)
        if group in groups and groups[group]!=task['split']:raise ValueError('Related parent tasks cross data partitions')
        groups[group]=task['split'];result.append(dict(task,leakage_group=group))
    # Repository chronology precedes randomized interleaving.
    by_repo={}
    for t in result:by_repo.setdefault(t['repo'],[]).append(t)
    for rows in by_repo.values():rows.sort(key=lambda x:(x.get('published_at',''),x['task_id']))
    rng=random.Random(seed);ordered=[]
    while by_repo:
        repo=rng.choice(sorted(by_repo));ordered.append(by_repo[repo].pop(0))
        if not by_repo[repo]:del by_repo[repo]
    return {'schema_version':1,'seed':seed,'tasks':ordered,'split_by_parent_and_lineage':True,'model_calls':0}
