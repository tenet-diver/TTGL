#!/usr/bin/env python3
"""Publish real code-task metering, checks and live transform evidence."""
import collections
import hashlib
import json
from pathlib import Path

from workspace import Store
from analyst_experiments import plan_experiment,record_evaluation

REPO=Path(__file__).resolve().parents[3]


def main():
    directory=REPO/'work/security/live-harness/study-001'
    if (directory/'publication.json').exists():raise ValueError('Already published')
    if not (directory/'complete.json').exists():raise ValueError('Trial incomplete')
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000',REPO/'work/security/langfuse-stack/captures')
    store.scan();report=store.report(event_limit=None)
    project=store.mutate('project',dict(name='Live Codex compression',repo=str(REPO),scope='Actual normal shell/edit tools, request transforms, native usage and independently checked task outcomes.'))['id']
    def register(cell,title,acceptance):
        session=next(json.loads(line)['thread_id'] for line in (cell/'agent.jsonl').read_text().splitlines() if line.startswith('{') and json.loads(line).get('type')=='thread.started')
        task=store.mutate('task',dict(project_id=project,title=title,goal='Exercise actual Codex execution and preserve raw/forwarded evidence.',acceptance=acceptance))['id']
        for turn in report['turns']:
            if turn['session_id']==session:store.mutate('assign',dict(session_id=session,turn_id=turn['turn_id'],task_id=task))
        return session,task
    canary_session,baseline=register(directory.parent/'installed-canary','Verify installed normal Codex command compression','Ordinary codex exec uses the configured live route; warnings, digest and exit status survive.')
    store.mutate('task_status',dict(id=baseline,status='completed',outcome='Normal codex exec with no provider override used live progress route; exact warning and digest reported. Original and forwarded requests retained.'))
    experiment=plan_experiment(store,dict(task_id=baseline,title='Compress live Codex shell results with Headroom lossless folds',
        change='Normal tool output is transformed before upstream inference: verified Docker progress filter plus pinned Headroom search/run folds with exact inverse checks; no source or prompt modification.',
        metrics='Registered live-harness-001: compare whole-task native usage on two code-edit-and-test tasks; >=5% pooled token reduction, actual transforms in both compact cells.',
        quality_gate='All four runs preserve tests/fixtures and pass visible plus independent post-run checks.',
        overhead='Record transform time and include all model/tool calls per arm. Analyst and development/research costs are additional; no net first-use or cash saving claim.',
        rollback='Use unmodified /responses route or installer --policy off. Keep progress-only default if the full-lossless gate fails.'))['id']
    protocol=json.loads((directory/'protocol.json').read_text());manifest=json.loads((directory/'manifest.json').read_text());cells=[]
    for case in protocol['cases']:
        for condition in case['order']:
            cell=directory/(case['id']+'--'+condition);session,task=register(cell,protocol['id']+' '+cell.name,protocol['quality_gate'])
            events=[e for e in report['events'] if e['session_id']==session];usage=collections.Counter();responses=[]
            for event in events:
                if event['usage']:
                    usage.update({key:event['usage'].get(key,0) for key in ('input_tokens','cached_input_tokens','output_tokens','total_tokens')});responses.append(event['id'])
            if not responses or not usage['total_tokens']:raise ValueError('Missing native metering')
            selected=store.report(task=task);captures=selected['wire_captures'];grades=json.loads((cell/'grade.json').read_text())
            changes=[dict(capture_id=c['id'],**change) for c in captures for change in c.get('compression',{}).get('changes',[])]
            completion=json.loads((cell/'completion.json').read_text())
            store.mutate('task_status',dict(id=task,status='completed' if grades['passed'] else 'unresolved',outcome='Independent operator checks '+json.dumps(grades)+'; actual app.py repair and ordinary shell execution.'))
            cells.append(dict(case=case['id'],condition=condition,policy=completion['policy'],task_id=task,session_id=session,
                usage=dict(usage),native_response_ids=responses,tool_evidence_ids=[e['id'] for e in events if e['kind']=='tool'],
                capture_ids=[c['id'] for c in captures],captures_complete=len(captures)==len(responses) and all(c['response_body_state']=='available' and c['correlation']=='response ID' for c in captures),
                wall_seconds=completion['elapsed_seconds'],compaction_seconds=sum(c.get('compression',{}).get('elapsed_seconds',0) for c in captures),
                presented_bytes=sum(c['forwarded_request_bytes'] for c in captures),original_bytes=sum(c['request_bytes'] for c in captures),
                transform_changes=changes,quality=grades,answer=(cell/'answer.md').read_text()))
    raw=[c for c in cells if c['condition']=='raw'];compact=[c for c in cells if c['condition']=='compact']
    before=sum(c['usage']['total_tokens'] for c in raw);after=sum(c['usage']['total_tokens'] for c in compact)
    quality=all(c['quality']['passed'] for c in cells);transforms=all(c['transform_changes'] for c in compact)
    measurements=dict(scope=protocol['scope'],cells=cells,raw_total_tokens=before,compact_total_tokens=after,
        token_reduction_fraction=1-after/before,raw_wall_seconds=sum(c['wall_seconds'] for c in raw),compact_wall_seconds=sum(c['wall_seconds'] for c in compact),
        quality_passed=quality,actual_transforms_in_both_cells=transforms,acceptance_passed=quality and transforms and after<=before*.95,
        cash_cost=None,inference_latency=None,overhead_note='Both arms include every model response. Additional analysis/development is research overhead; no first-use net saving inferred.')
    sealed=dict(protocol=protocol,manifest=manifest,measurements=measurements)
    digest=hashlib.sha256(json.dumps(sealed,sort_keys=True).encode()).hexdigest()
    (directory/'measurements.json').write_text(json.dumps(sealed,indent=2))
    evaluation=record_evaluation(store,experiment,protocol,measurements,digest)
    publication=dict(project_id=project,experiment_id=experiment,evaluation_id=evaluation,baseline_task_id=baseline,artifact_sha256=digest)
    (directory/'publication.json').write_text(json.dumps(publication,indent=2));print(json.dumps({**publication,**{key:measurements[key] for key in ('raw_total_tokens','compact_total_tokens','token_reduction_fraction','acceptance_passed')}}))


if __name__=='__main__':main()
