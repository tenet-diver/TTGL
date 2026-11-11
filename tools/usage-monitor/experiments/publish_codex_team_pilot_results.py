#!/usr/bin/env python3
"""Export completed pilot summaries and figures, never raw private transcripts."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import statistics


def publish(analysis,figures,output):
    d=json.loads(analysis.read_text())
    if not d['complete'] or d['completed']!=24:raise ValueError('All24registered cells required')
    target=output/'pilot-results.json'
    if target.exists():raise ValueError('Never overwrite published result snapshot')
    names={'native':'Native Codex','notebook':'Shared notebook','mcp_memory':'MCP memory'}
    cells=[]
    for x in d['cells']:
        cells.append({k:x[k] for k in ('task','condition','total_agent_capacity','grade','wall_seconds','actual_threads','observed_active_threads_peak',
            'parent_native_status','rpc_delivery_complete','server_capacity_guidance','observed_native_multi_agent_versions','peak_overlapping_http_requests','terminal_calls',
            'usage','inference_accounting_complete','standard_credit_lower_bound','full_standard_credit_scenario','api_equivalent_lower_bound_usd','full_standard_api_equivalent_usd')})
        cells[-1]['memory_mechanism']=dict(published_observations=x['memory_exposure']['published_observations'],
            read_calls=len(x['memory_exposure']['successful_reads']),nonempty_read_calls=sum(r['returned_entities']>0 for r in x['memory_exposure']['successful_reads']),
            peer_observation_read_calls=x['memory_exposure']['cross_agent_read_calls'])
    public=dict(at=datetime.now(timezone.utc).isoformat(),kind='completed_development_pilot',tasks=2,assignments=24,cells=cells,grouped=d['grouped'],paired=d['paired'],
        pricing_sources=d['pricing_sources'],pricing_checked=d['pricing_checked'],limitations=d['limitations'],subscription_cash_expense=None,
        raw_evidence='Local ignored study archives; credentials and private transcripts excluded from publication')
    target.write_text(json.dumps(public,indent=2)+'\n');shutil.copyfile(analysis.parent/'cells.csv',output/'pilot-cells.csv')
    dest=output/'figures';dest.mkdir(exist_ok=True)
    for ext in ('svg','pdf','png'):shutil.copyfile(figures/('scaling.'+ext),dest/('pilot-scaling.'+ext))
    shutil.copyfile(figures/'caption.txt',dest/'pilot-scaling-caption.txt')
    native1=[x for x in cells if x['condition']=='native' and x['total_agent_capacity']==1]
    native8=[x for x in cells if x['condition']=='native' and x['total_agent_capacity']==8]
    speed=100*(1-sum(x['wall_seconds'] for x in native8)/sum(x['wall_seconds'] for x in native1))
    ratio=sum(x['standard_credit_lower_bound'] for x in native8)/sum(x['standard_credit_lower_bound'] for x in native1)
    memory=[x for x in cells if x['condition']=='mcp_memory'];published=sum(x['memory_mechanism']['published_observations'] for x in memory)
    reads=sum(x['memory_mechanism']['read_calls'] for x in memory);nonempty=sum(x['memory_mechanism']['nonempty_read_calls'] for x in memory)
    lines=['# Completed native Codex knowledge pilot','',
        '11 November 2026. **24 fixed assignments on two development libraries; one attempt per cell.** This is not the reserved evaluation or an official Commit0 leaderboard score.','',
        '**All 24 submitted artifacts pass independent source-only replay:** SimPy passes 140 prescribed tests per run; TinyDB passes 200 with one environment-prescribed skip. There are 23 normally completed parent turns and one stream-failed parent with a passing sealed artifact.','',
        '| Knowledge condition | Allowed total agents | Verified / tasks | Mean parent-run seconds | Mean distinct threads | Mean Standard-credit scenario |',
        '| --- | ---: | ---: | ---: | ---: | ---: |']
    for x in d['grouped']:
        bound='' if x['cost_accounting_complete'] else '≥'
        lines.append(f'| {names[x["condition"]]} | {x["total_agent_capacity"]} | {x["verified_resolutions"]}/{x["assignments"]} | {x["mean_attempt_seconds"]:.1f} | {x["mean_actual_threads"]:.1f} | {bound}{x["total_standard_credit_lower_bound"]/x["assignments"]:.3f} |')
    lines += ['',f'Native capacity eight averages {statistics.mean(x["wall_seconds"] for x in native8):.1f} seconds versus {statistics.mean(x["wall_seconds"] for x in native1):.1f} for the single agent: **{speed:.1f}% less time**, using four or five distinct threads. Its known model-rate expenditure is already **at least {ratio:.2f}×** the fully measured single-agent control. This is an observed two-task trade-off, not a general speedup estimate.','',
        'Added knowledge does not improve observed completion, which is at a ceiling. Timing changes are mixed across libraries and capacities; one attempt per cell cannot establish a reliable knowledge-system advantage. Capacity eight is not an eight-worker observation.','',
        f'MCP agents publish **{published} observations** across eight runs. There are **{reads} read queries, {nonempty} returning entities**, and no exact peer-observation retrieval. The integration works as a publication log here; these trials do not demonstrate social reuse through retrieved observation text. Native messages, inherited context and shared code remain communication channels in every condition.','',
        '**Accounting:** seven cells have complete observed inference accounting. Seventeen have interrupted or incomplete transports, so their completed-response totals are lower bounds. Across the pilot, at least 33,076,632 native tokens and 260.226880 Standard-rate credits are observed, with 98 unknown-usage requests. Full cost is unknown. One child has an extra native/captured completion absent from final RPC notification delivery; its exact counter prefix and additional 34,872 tokens are retained. No notification is fabricated and no call is repeated.','',
        'A bound above a fully measured control proves a cost increase under the stated scenario; overlapping unknown bounds do not establish a ranking. Subscription cash expense and quota savings are unknown. [Standard credit rates](https://learn.chatgpt.com/docs/pricing) and [separate API token prices](https://developers.openai.com/api/docs/models/gpt-6.1-sol) were checked on 11 November.','',
        '**Timing:** the registered timer measures app-server coding execution through the parent turn end, including planning, tools, native worker activity, knowledge operations and in-agent checks. Initial task preparation and later independent replay are separate. The red cross marks time to a failed parent stream, not normal final completion. This is not a complete deployment-latency or local-CPU-cost measurement.','',
        '![Pilot quality, coding time and cost bounds](figures/pilot-scaling.png)','',
        'Download the [SVG](figures/pilot-scaling.svg), [PDF](figures/pilot-scaling.pdf), [cell CSV](pilot-cells.csv) or [sanitized results](pilot-results.json).','',
        '**Controls and boundaries:** Codex CLI 0.167.0, hosted native backend reported v2, GPT-6.1 Sol low for all agents, shared constrained terminal, isolated task stores, no web or prior candidate history. Total capacity limits are 1/2/4/8; each team gets 30 minutes, 80 terminal calls and a four-million-observed-token stop threshold. In-flight and auxiliary usage can exceed the threshold. The runtime is a declared Python 3.11.18 variant of the dataset environment. Public tests are restored from sealed assets; hidden-test robustness was not measured.','',
        '**Exclusions:** Graphiti local-provider diagnostics did not establish ingestion readiness. Cognee’s current compatible full graph includes a confirmed advisory-matched Transformers release. Neither receives a coding score or an invented zero cost. Detailed failed preparations, provider adaptations and unknown usage are in the [preparation record](preparation-results.md). Twelve reserved libraries have no model outcomes; current preparation is not held-out validation.','',
        '**Interpretation:** the pilot supports faster native execution with higher minimum model expenditure on these two tasks. It does not establish that added external knowledge accelerates verified innovation, that larger fixed teams degrade, or that graph memory is superior to text. A larger workload and a separately frozen knowledge-use policy are needed to study effective retrieval and generalization.','',
        'The prospective paper preceded inference. Local protocol amendments preserve the cancellation accounting stop, verified archive cleanup and late-notification reconciliation without changing generation prompts, order or replay behavior. All raw evidence remains local in verified lossless archives; no model assignment was retried.']
    (output/'pilot-results.md').write_text('\n'.join(lines)+'\n');print('Published sanitized completed-pilot report, tables, CSV and figures locally.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--analysis',required=True,type=Path);p.add_argument('--figures',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
    a=p.parse_args();publish(a.analysis,a.figures,a.output)
