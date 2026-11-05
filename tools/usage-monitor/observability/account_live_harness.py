#!/usr/bin/env python3
"""Append accrued native cost for the installed live-harness development cycle."""
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
        repo=turn.get('repo','');prompt=(turn.get('prompt') or '').lower()
        if 'well keep going, until it is implemented' in prompt:
            selected[(turn['session_id'],turn['turn_id'])]='implementation_and_supervision'
        elif '/work/security/live-harness/study-001/' in repo:
            selected[(turn['session_id'],turn['turn_id'])]='matched_coding_trials'
        elif '/work/security/live-harness/analyst-' in repo:
            selected[(turn['session_id'],turn['turn_id'])]='analyst_evaluation'
        elif '/work/security/live-harness/' in repo:
            selected[(turn['session_id'],turn['turn_id'])]='installation_verification'
    groups=collections.defaultdict(lambda:dict(usage=collections.Counter(),native_response_ids=[]))
    for event in report['events']:
        label=selected.get((event['session_id'],event['turn_id']))
        if label and event['usage']:
            groups[label]['usage'].update({key:event['usage'].get(key,0) for key in ('input_tokens','cached_input_tokens','output_tokens','total_tokens')})
            groups[label]['native_response_ids'].append(event['id'])
    directory=REPO/'work/security/live-harness/study-001'
    measurements=json.loads((directory/'measurements.json').read_text())['measurements']
    publication=json.loads((directory/'publication.json').read_text())
    prior=json.loads((REPO/'work/security/experiments/progress-replay-002/accounting.json').read_text())['including_prior_usability_tokens']
    mean_saved=(measurements['raw_total_tokens']-measurements['compact_total_tokens'])/2
    total=sum(value['usage']['total_tokens'] for value in groups.values())
    payload=dict(as_of=datetime.now(timezone.utc).isoformat(),unit='coding tasks resembling the two development cases',components=dict(groups),
        current_research_tokens=total,including_prior_usability_tokens=total+prior,prior_research_tokens=prior,
        mean_saved_tokens_per_task=mean_saved,illustrative_repetitions_to_recover_current_tokens=total/mean_saved,
        illustrative_repetitions_including_prior_usability=(total+prior)/mean_saved,cash_cost=None,net_first_use_saving=False,
        limitations='Accrued native token snapshot while implementation is active. Cached input is counted once, not billed at assumed rates. Both trial arms, installation checks, analysts and this implementation turn are development expense. Prior cost is the earlier frozen replay/usability ledger, not all historical project cost. Illustrative token amortization on two generated tasks is not dollar break-even, quota saving or a forecast. Human and operational costs are unmeasured.')
    record_accounting(store,publication['experiment_id'],payload)
    (directory/'accounting.json').write_text(json.dumps(payload,indent=2))
    print(json.dumps({key:value for key,value in payload.items() if key!='components'}))


if __name__=='__main__':main()
