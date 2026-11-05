#!/usr/bin/env python3
"""Append an explicit native-token research-cost snapshot without editing trial results."""
import collections
from datetime import datetime,timezone
import json
from pathlib import Path

from workspace import Store
from analyst_experiments import record_accounting

REPO=Path(__file__).resolve().parents[3]


def main():
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000')
    store.scan();report=store.report(event_limit=None)
    selected={}
    for turn in report['turns']:
        prompt=(turn.get('prompt') or '').lower()
        if 'keep going until the analyst is able to use the product' in prompt:
            selected[(turn['session_id'],turn['turn_id'])]='implementation_and_supervision'
        path=turn.get('repo','')
        if '/work/security/experiments/progress-replay-00' in path:
            selected[(turn['session_id'],turn['turn_id'])]='both_development_trials'
        elif '/work/security/usability/trial-review-00' in path:
            selected[(turn['session_id'],turn['turn_id'])]='analyst_evaluation'
        elif '/work/security/usability/pilot-00' in path:
            selected[(turn['session_id'],turn['turn_id'])]='prior_usability_research'
    groups=collections.defaultdict(lambda:dict(usage=collections.Counter(),native_response_ids=[]))
    for event in report['events']:
        label=selected.get((event['session_id'],event['turn_id']))
        if label and event['usage']:
            groups[label]['usage'].update({k:event['usage'].get(k,0) for k in ('input_tokens','cached_input_tokens','output_tokens','total_tokens')})
            groups[label]['native_response_ids'].append(event['id'])
    latest=json.loads((REPO/'work/security/experiments/progress-replay-002/measurements.json').read_text())['measurements']
    mean_saved=(latest['raw_total_tokens']-latest['compact_total_tokens'])/3
    current=sum(g['usage']['total_tokens'] for k,g in groups.items() if k!='prior_usability_research')
    all_research=sum(g['usage']['total_tokens'] for g in groups.values())
    payload=dict(as_of=datetime.now(timezone.utc).isoformat(),components=dict(groups),
        current_research_tokens=current,including_prior_usability_tokens=all_research,
        mean_saved_tokens_per_replayed_case=mean_saved,
        illustrative_repetitions_to_recover_current_tokens=current/mean_saved,
        illustrative_repetitions_including_prior_usability=all_research/mean_saved,
        cash_cost=None,net_first_use_saving=False,
        limitations='Accrued native token counts through this snapshot, including cached input once. Active implementation/review may add responses. These are token-count amortization illustrations for repeated similar diagnostic cases, not dollar break-even or forecasts. Both trial arms are R&D expense; setup history predating usability is excluded. No net savings on the first use.')
    ident=record_accounting(store,'1d394c92734f457f91d4fb201b2f5e69',payload)
    (REPO/'work/security/experiments/progress-replay-002/accounting.json').write_text(json.dumps(payload,indent=2))
    print(json.dumps({k:v for k,v in payload.items() if k!='components'}))


if __name__=='__main__':
    main()
