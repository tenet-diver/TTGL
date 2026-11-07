#!/usr/bin/env python3
"""Accrued unique-native-response research expense; never a net saving claim."""
from datetime import datetime,timezone
import collections
import json
import os
from pathlib import Path
import sys

REPO=Path(__file__).resolve().parents[3]
ROOT=REPO/'work/security/context-memory-20261107'
sys.path.insert(0,str(REPO/'tools/usage-monitor/observability'))
from workspace import Store
from analyst_experiments import record_accounting


def long_history_sessions(root):
    """Discover started calls, including failed/unfinished calls, without retrying."""
    sessions={}
    for block in root.glob('longmemeval-*'):
        if not block.is_dir():continue
        paths=list(block.glob('case-*/*/agent.jsonl'))+list(block.glob('case-*/*/judge/agent.jsonl'))+list(block.glob('case-*/mem0-build/extractions/extract-*/agent.jsonl'))
        for path in paths:
            for line in path.read_text().splitlines():
                try:row=json.loads(line)
                except json.JSONDecodeError:continue
                if row.get('type')!='thread.started':continue
                role='evaluation_judges' if path.parent.name=='judge' else 'memory_extraction' if path.parent.name.startswith('extract-') else 'long_history_readers'
                sid=row['thread_id']
                if sid in sessions:raise ValueError('Duplicate thread across long-history artifacts')
                sessions[sid]=role
    return sessions


def main():
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan()
    parent=os.environ.get('CODEX_THREAD_ID')
    if not parent:raise ValueError('Explicit active parent session required')
    with store.connection() as db:
        turns=[dict(r) for r in db.execute('SELECT * FROM turns WHERE session_id=?',(parent,))]
        selected=[t for t in turns if 'run all of the experiments we planned' in (t.get('prompt') or '')]
        if not selected:raise ValueError('Cannot identify authorized research turn; do not guess overhead')
        cutoff=min(t['start'] for t in selected)
        parent_turns={t['turn_id'] for t in turns if t['start']>=cutoff}
        rows=[dict(r) for r in db.execute("SELECT * FROM events WHERE kind='generation'")]
    sessions=long_history_sessions(ROOT)
    for name in ('batching-001','chronological-002'):
        result=json.loads((ROOT/name/'results.json').read_text())
        for cell in result['cells']:sessions[cell['session_id']]='registered_trials'
    for path in (ROOT/'mem0-preflight-001').glob('extract-*/agent.jsonl'):
        sid=next(json.loads(l)['thread_id'] for l in path.read_text().splitlines() if l.startswith('{') and json.loads(l).get('type')=='thread.started')
        sessions[sid]='memory_mechanism_preflight'
    report=store.report(event_limit=None)
    for turn in report['turns']:
        if Path(turn['repo']).resolve()==(ROOT/'analyst-001').resolve():sessions[turn['session_id']]='analyst_review'
    groups=collections.defaultdict(lambda:dict(usage=collections.Counter(),response_ids=[]))
    seen=set()
    for row in rows:
        group='implementation_and_supervision' if row['session_id']==parent and row['turn_id'] in parent_turns else sessions.get(row['session_id'])
        if not group or row['id'] in seen or not row['usage']:continue
        seen.add(row['id']);usage=json.loads(row['usage'])
        groups[group]['usage'].update({k:usage.get(k,0) for k in ('input_tokens','cached_input_tokens','output_tokens','total_tokens')})
        groups[group]['response_ids'].append(row['id'])
    metered_sessions={r['session_id'] for r in rows if r['id'] in seen and json.loads(r['usage']).get('total_tokens',0)>0}
    unknown_sessions=[dict(session_id=sid,role=role,usage=None,cost=None) for sid,role in sessions.items() if sid not in metered_sessions]
    rates=json.loads((REPO/'tools/usage-monitor/studies/context-memory-pricing-20261107.json').read_text())['primary_scenario']
    known_cost=sum(((g['usage']['input_tokens']-g['usage']['cached_input_tokens'])*rates['fresh_input_per_million']+g['usage']['cached_input_tokens']*rates['cached_input_per_million']+g['usage']['output_tokens']*rates['output_per_million'])/1e6 for g in groups.values())
    payload=dict(as_of=datetime.now(timezone.utc).isoformat(),scope='Cumulative snapshot of this active research turn, original30 completed trial cells, all discovered long-history readers/extractors/judges including failed or active calls, one analyst and Mem0 preflight. Initial service-start turn excluded.',
        components=dict(groups),native_tokens=sum(g['usage']['total_tokens'] for g in groups.values()),unique_responses=len(seen),
        local_embedding_inferences=len((ROOT/'embedding-inferences.jsonl').read_text().splitlines()),
        unknown_sessions=unknown_sessions,total_program_cost=None,known_native_credit_rate_scenario=known_cost,
        cash_cost=None,subscription_quota_impact=None,operational_cost=None,net_saving=None,
        snapshot_semantics='Cumulative lower bound while parent is active. Alternative snapshots must not be added together. Local embedding model inferences have separately measured runtime, not native Codex tokens. Installation/security/human costs not monetized.')
    publication=json.loads((ROOT/'chronological-002/publication.json').read_text())
    ident=record_accounting(store,publication['experiment_id'],payload);payload['accounting_id']=ident
    out=ROOT/('accounting-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json');out.write_text(json.dumps(payload,indent=2)+'\n')
    print(json.dumps({k:v for k,v in payload.items() if k!='components'}))
    print(json.dumps({k:dict(v['usage']) for k,v in groups.items()}))


if __name__=='__main__':main()
