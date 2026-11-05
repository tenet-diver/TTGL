#!/usr/bin/env python3
"""Import actual native metering and quality checks into immutable trial results."""
import argparse
import collections
import hashlib
import json
from pathlib import Path
import sys

from workspace import Store
from analyst_experiments import record_evaluation

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]


def publish(directory):
    if (directory/'publication.json').exists():
        raise ValueError('Already published; refusing to duplicate results or tasks')
    if not (directory/'complete.json').exists():
        raise ValueError('Trial is incomplete; retain evidence and do not infer results')
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000',REPO/'work/security/langfuse-stack/captures')
    store.scan()
    protocol=json.loads((directory/'protocol.json').read_text())
    manifest=json.loads((directory/'manifest.json').read_text())
    report=store.report(event_limit=None)
    project=next(t['project_id'] for t in report['tasks'] if t['id']=='a2a4af35000a4bf4a522fb0fecd70401')
    cells=[]
    for case in protocol['cases']:
        for condition in case['order']:
            cell=directory/(case['id']+'--'+condition)
            completion=json.loads((cell/'completion.json').read_text())
            records=[json.loads(l) for l in (cell/'agent.jsonl').read_text().splitlines() if l.startswith('{')]
            session=next(r['thread_id'] for r in records if r.get('type')=='thread.started')
            events=[e for e in report['events'] if e['session_id']==session]
            usage=collections.Counter()
            generations=[]
            for event in events:
                if event['usage']:
                    usage.update({k:event['usage'].get(k,0) for k in ('input_tokens','cached_input_tokens','output_tokens','total_tokens')})
                    generations.append(event['id'])
            if not generations or not usage['total_tokens']:
                raise ValueError('Native usage unavailable; cannot publish an economic result')
            task=store.mutate('task',dict(project_id=project,title=protocol['id']+' '+cell.name,
                goal='Interpret retained pull evidence with '+condition+' presentation.',acceptance=protocol['quality_gate']))['id']
            for turn in report['turns']:
                if turn['session_id']==session:
                    store.mutate('assign',dict(session_id=session,turn_id=turn['turn_id'],task_id=task))
            grade=json.loads((cell/'grade.json').read_text())
            store.mutate('task_status',dict(id=task,status='completed' if grade['passed'] else 'unresolved',
                outcome='Frozen replay quality '+json.dumps(grade)+'; no actual images pulled or services changed.'))
            calls=[json.loads(l) for l in (cell/'calls.jsonl').read_text().splitlines()]
            calls=[r for r in calls if r['method']=='tools/call']
            captures=store.report(task=task)['wire_captures']
            cells.append(dict(case=case['id'],condition=condition,synthetic=case['synthetic'],task_id=task,
                session_id=session,usage=dict(usage),native_response_ids=generations,
                tool_evidence_ids=[e['id'] for e in events if e['kind']=='tool'],
                capture_ids=[c['id'] for c in captures],captures_complete=all(c['response_body_state']=='available' and c['correlation']=='response ID' for c in captures) and len(captures)==len(generations),
                wall_seconds=completion['elapsed_seconds'],compaction_seconds=completion['compaction_seconds'],
                presented_bytes=completion['presented_bytes'],original_bytes=completion['original_bytes'],
                tool_calls=len(calls),tool_response_bytes=sum(c['response_bytes'] for c in calls),
                quality=grade,answer=json.loads((cell/'answer.json').read_text())))
    raw=[c for c in cells if c['condition']=='raw'];compact=[c for c in cells if c['condition']=='compact']
    before=sum(c['usage']['total_tokens'] for c in raw);after=sum(c['usage']['total_tokens'] for c in compact)
    quality_passed=all(c['quality']['passed'] for c in cells)
    measurements=dict(scope=protocol['scope'],cells=cells,
        raw_total_tokens=before,compact_total_tokens=after,token_reduction_fraction=1-after/before,
        raw_wall_seconds=sum(c['wall_seconds'] for c in raw),compact_wall_seconds=sum(c['wall_seconds'] for c in compact),
        quality_passed=quality_passed,acceptance_passed=quality_passed and after<=before*.9,
        cash_cost=None,inference_latency=None,
        overhead_note='Trial inference included per arm; analyst, implementation and verification overhead remain separate. Native cached input is already included. No full coding-task savings inferred.')
    sealed=dict(protocol=protocol,manifest=manifest,measurements=measurements)
    digest=hashlib.sha256(json.dumps(sealed,sort_keys=True).encode()).hexdigest()
    (directory/'measurements.json').write_text(json.dumps(sealed,indent=2))
    evaluation=record_evaluation(store,protocol['proposal_id'],protocol,measurements,digest)
    (directory/'publication.json').write_text(json.dumps(dict(evaluation_id=evaluation,artifact_sha256=digest),indent=2))
    print(json.dumps(dict(evaluation_id=evaluation,raw_tokens=before,compact_tokens=after,
                         reduction=1-after/before,quality_passed=quality_passed,acceptance_passed=measurements['acceptance_passed'])))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    publish(parser.parse_args().directory.resolve())
