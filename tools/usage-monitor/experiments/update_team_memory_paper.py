#!/usr/bin/env python3
"""Update factual paper sections only after the complete independent audit.

No model calls. Historical pilot results and their failed evidence stay intact.
The writer is an auditable draft generator; human/agent review remains required.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import re
import statistics


LABELS={'native':'Native','notebook':'Notebook','mcp_memory':'Official MCP memory',
        'mem0_luna':'Mem0 / Luna','graphiti_luna':'Graphiti / Luna',
        'smallville_luna':'Smallville / Luna','searchable_logs':'Searchable logs'}


def replace_section(text,start,end,body):
    if text.count(start)!=1 or text.count(end)!=1:raise ValueError('Ambiguous paper section')
    prefix,rest=text.split(start,1);old,suffix=rest.split(end,1)
    return prefix+start+'\n\n'+body.strip()+'\n\n'+end+suffix


def validate(result,audit):
    if result['state']!='complete' or result['completed']!=56 or result['planned']!=56 or len(result['cells'])!=56:
        raise ValueError('Paper cannot describe an incomplete comparison as finished')
    if not audit['passed'] or audit['registered_cells']!=56:raise ValueError('Independent final audit required')
    if {r['directory'] for r in result['cells']}!={r['directory'] for r in audit['archives']}:
        raise ValueError('Final audit does not cover these cells')
    if sum(r['native_usage_lower_bound']['total_tokens'] for r in result['cells'])!=audit['totals']['recorded_native_usage_lower_bound']['total_tokens']:
        raise ValueError('Final audit is stale')
    if len(result['arms'])!=7 or any(r['completed']!=8 for r in result['arms']):raise ValueError('Arm panel incomplete')
    expected=dict(source_passes=sum(c['passed'] for c in result['cells']),
        normal_parents=sum(c['parent_status']=='completed' for c in result['cells']),
        complete_usage_cells=sum(c['inference_accounting_complete'] for c in result['cells']))
    if any(result['audit'][k]!=v for k,v in expected.items()):raise ValueError('Headline disagrees with cells')
    for arm in result['arms']:
        cells=[c for c in result['cells'] if c['arm']==arm['arm']]
        if len(cells)!=8 or sum(c['passed'] for c in cells)!=arm['successes'] or sum(c['parent_status']=='completed' for c in cells)!=arm['normal_parents']:
            raise ValueError('Arm summary disagrees with cells')


def render(text,result,audit):
    validate(result,audit)
    p=result['audit']['source_passes'];normal=result['audit']['normal_parents'];known=result['audit']['complete_usage_cells']
    usage=audit['totals']['recorded_native_usage_lower_bound']['total_tokens'];credits=audit['totals']['standard_scenario_credits_lower_bound']
    unknown=audit['totals']['unknown_requests'];official=audit['official_mcp_exposure']
    peer=sum(r['known_peer_read_queries'] for r in official)
    quality=('All 56 sealed source artifacts pass the prescribed tests, leaving no observed quality gain to identify.' if p==56 else
             f'{p}/56 sealed source artifacts pass the prescribed tests; the failures remain in every comparison.')
    abstract=(
        'We investigate whether shared knowledge changes the scalability of native Codex coding teams. '
        'A completed24-cell pilot crosses two development libraries, three knowledge conditions and four offered capacities. '
        'All pilot artifacts pass; native capacity8 reduces mean run time by31.3% with at least2.45 times the fully measured single-agent model-rate expenditure. '
        'A separate56-cell memory-aware extension adds Mem0, Graphiti, adapted Smallville and shared searchable logs to matched native/notebook/MCP controls. '
        'Sol low codes, Luna maintains model-based memory, and every parent/child receives explicit tool and knowledge-use guidance. '
        +quality+f' Normal parent completion is {normal}/56, reported separately. '
        f'Observed inference is at least{usage:,} tokens and {credits:.4f} dated Standard-rate credits; {56-known} cells contain unknown final usage. '
        f'Official MCP has {peer} queries returning exactly attributable peer observations; other backends have separately measured exposure. '
        'These records demonstrate observable memory use, not causal benefit. '
        'Disclosed amendments exclude unused image dependencies after cell12, extend only the pre-model startup wait after cell19, and remove independently verified dead socket paths before startup from cell21. '
        'Failed preparations remain preserved; source quality is conditional on task-model invocation rather than flawless first-launch reliability. '
        'The small reused development sample, outcome ceiling where present, unknown costs and dependency strata limit inference. '
        'Held-out transfer, general learning and net economic benefit remain unestablished.')
    # Keep ordinary typography readable, including computed numbers.
    abstract=re.sub(r'(?<=[A-Za-z])(?=\d)', ' ', abstract)
    text=replace_section(text,'## Abstract','## 1. Introduction',abstract)
    status=('**Status:** the original24-cell development pilot and the separately registered56-cell memory-aware comparison are complete. '
        f'The extension has {p}/56 passing source artifacts and {normal}/56 normally completed parents. '
        'Their results remain separate. The historical interrupted80-cell reserved-library extension remains separately documented; uncertain started calls are preserved. '
        'See the [final audit](memory-aware-final-audit.md), [full extension panels](memory-aware-results.md), '
        '[pilot report](pilot-results.md), [appendix](appendix.md) and [reproduction guide](REPRODUCING.md).')
    status=re.sub(r'(?<=[A-Za-z])(?=\d)', ' ', status)
    first=text.index('**Status:**');last=text.index('## Abstract')
    text=text[:first]+status+'\n\n'+text[last:]
    date=datetime.now(timezone.utc).strftime('%d %B %Y')
    text=re.sub(r'(?m)^Working study,.*$',f'Working study, {date} · Draft 0.4 — completed pilot and memory-aware comparison',text)
    table=['| Arm | Cells | Verified sources | Normal parents | Complete usage | Mean run-end seconds | Mean Standard credits |',
           '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for arm in result['arms']:
        sign='' if arm['accounting_complete'] else '≥'
        table.append(f"| {LABELS[arm['arm']]} | 8 | {arm['successes']}/8 | {arm['normal_parents']}/8 | {arm['accounting_complete_cells']}/8 | {arm['mean_seconds']:.1f} | {sign}{arm['mean_credit_lower_bound']:.4f} |")
    mechanism=['| Backend | Nonempty searches | Known peer search calls | Original-record reads | Known peer reads | Explicit tool errors |',
               '| --- | ---: | ---: | ---: | ---: | ---: |']
    for arm in ('mem0_luna','graphiti_luna','smallville_luna','searchable_logs'):
        rows=[r for r in audit['exposure'] if r['arm']==arm]
        fields=('nonempty_searches','known_peer_search_calls','original_record_reads','known_peer_record_reads','explicit_tool_errors')
        mechanism.append('| '+LABELS[arm]+' | '+' | '.join(str(sum(r[k] for r in rows)) for k in fields)+' |')
    extension=(f'### 6.6 Completed memory-aware extension\n\nAll56 registered assignments end with independent source-only replay and positive deduplicated native-response evidence. '
        +quality+f' {normal}/56 parents complete normally; budget/transport endings and passing artifacts remain distinct. '
        'All arms have the same two libraries × capacities1/2/4/8, one attempt per cell. '
        'The next table averages across those capacities; the [28 complete matched panels](memory-aware-results.md) retain the scaling analysis.\n\n'
        +'\n'.join(table)+'\n\n'
        f'Only {known}/56 cells have complete observed usage. The other cells contain {unknown} unknown requests; at least{usage:,} native tokens and '
        f'{credits:.4f} dated Standard-rate credits are recorded across Sol and Luna. All recorded parent, worker and maintenance inference is included. '
        f"Of those tokens, {audit.get('capture_only_recorded_tokens',0):,} belong to {len(audit.get('capture_only_completed_responses',[]))} completed provider responses missing their retained native transcript record. They are counted once as positive single-witness measurements, with explicit coverage gaps; the other counted responses reconcile native and transport records. "
        'These are model-rate scenarios, not cash/quota measurements. Local embeddings, deployment compute, preparation and incompletely measured research overhead are additional. '
        'Overlapping unknown lower bounds cannot rank total cost.\n\n'
        'End-time means include every cell, including stopped parents; they do not estimate success-only solution time. '
        'Offered coding capacity includes the parent, while actual Sol threads and Luna maintenance sessions are counted separately. '
        'Cells1–12 retain the original dependency variant; cells13–56 use the prospectively disclosed text-only variant with identical text-inference witnesses. Cells20–56 also use the disclosed longer pre-model setup wait; cells21–56 check and remove only independently verified dead socket paths before starting their broker. '
        'These preparation amendments were registered before the affected task-model calls. Failed container, transport and service preparations are archived separately after independent evidence established that no task turn had started. No started or uncertain task-model call was repeated. '
        'The source pass rate is conditional on actual task-model invocation. It is not a first-launch deployment reliability rate; failed preparations and their additional local/research overhead remain part of the operational record. '
        'Cell27 also exceeds the original broker shutdown wait after its native parent finishes. Its saved source is graded without repeating generation; an exported graph is retained, while an unfinished publication and service exit remain incomplete evidence. A prospective post-generation wait amendment applies only to cells28–56. '
        'All frozen source/runtime/gate and archive member/link hashes pass the independent final audit.\n\n'
        '![Memory-aware coding-run end times](figures/memory-aware-time.svg)\n\n'
        '[All standalone SVG charts and self-contained HTML](figures/memory-aware-figures.html), [per-cell CSV](memory-aware-cells.csv), '
        '[audited JSON](memory-aware-final-audit.json). Cost-chart points are recorded minima with no invented upper bounds.\n\n'
        '### 6.7 Observed memory exposure\n\n'
        f"Official MCP returns {sum(r['returned_publication_observations'] for r in official)} publication observations and completes {sum(r['completed_read_queries'] for r in official)} read queries. "
        f"{sum(r['nonempty_read_queries'] for r in official)} queries are nonempty; {peer} return exact observation text attributable to another native coding actor. "
        f"The sealed stores contain {sum(r.get('sealed_observation_count') or 0 for r in official)} observations; the audit separately compares unique accepted observations with final retention where no deletion occurred. "
        'That is observable peer exposure under explicit guidance. The earlier pilot’s empty reads remain historical evidence; the two policies are not pooled into a causal instruction-effect estimate.\n\n'
        +'\n'.join(mechanism)+'\n\n'
        'The four broker-arm counters use identifiable native authors and immutable publication/backend IDs. Unattributed extracted facts are not assumed to come from peers. '
        'Search hits, original-record reads and useful checked actions remain separate; neither a hit nor a final passing artifact proves the hit caused success. '
        'Native messages, shared code and notebook communication are additional channels. '
        'The [appendix](appendix.md) preserves real baseline failures, interface commitments, empty queries, original memories and verification caveats with hashes. '
        'Luna maintenance roles are counted from actual preserved intents; an available reflection feature does not imply a reflection occurred.\n\n')
    extension=re.sub(r'(?<=[A-Za-z])(?=\d)', ' ', extension)
    if '### 6.6 Completed memory-aware extension' in text:
        a=text.index('### 6.6 Completed memory-aware extension');b=text.index('## 7. Discussion',a);text=text[:a]+extension+text[b:]
    else:text=text.replace('## 7. Discussion',extension+'## 7. Discussion',1)
    discussion=('The original pilot shows a native parallelism trade-off: lower observed coding time at higher minimum model expenditure. '
        'Its publication activity does not establish memory reuse because the observed MCP reads are empty. '
        'The separately registered extension supplies explicit knowledge-use guidance and demonstrates actual peer exposure. '
        'It compares the resulting end-to-end deployment policies, including their processing overhead and reliability.\n\n'
        +quality+' Observed timing and model-rate differences are descriptive for these reused libraries. '
        'A memory system may add extraction and retrieval latency while agents already communicate through messages and source code. '
        'Publication count is therefore not a measure of avoided work. Stronger claims require repeated, larger tasks and interventions that isolate useful memory-to-action effects.\n\n'
        'The native control receives the same common guidance, preventing a simple instructions-versus-no-instructions interpretation within the extension. '
        'Comparisons with the earlier pilot still combine different executions and policies. '
        'The security-driven dependency amendment is separately labeled and supported by deterministic text witnesses; it does not prove identity for every possible input.\n\n'
        'Inference accounting identifies exact totals only where reconciled. A lower bound above a fully measured control can prove a scenario cost increase; '
        'overlapping unknown bounds do not identify a ranking. Model rates do not measure subscription cash or quota. '
        'Preparation and research overhead are additional, so no first-use net saving is claimed.')
    text=replace_section(text,'## 7. Discussion','## 8. Limitations',discussion)
    conclusion=(f'The historical24-cell pilot and separate56-cell memory-aware comparison are complete. '
        +quality+f' Normal parent completion in the extension is {normal}/56. '
        'Explicit tool guidance and shared stores support observable peer exposure, with backend-specific adoption, processing and failure records. '
        'The data do not establish that memory causes more accurate or generally faster coding. '
        'Unknown usage limits total-cost comparisons, and local/research overhead remains additional. '
        'Held-out generalization, accumulation across tasks and net economic benefit remain research questions.')
    conclusion=re.sub(r'(?<=[A-Za-z])(?=\d)', ' ', conclusion)
    text=replace_section(text,'## 9. Conclusion','## References',conclusion)
    return text


def appendix_summary(result,audit):
    lines=['## G. Completed memory-aware comparison','',
        f"All 56 registered cells end: {result['audit']['source_passes']}/56 source artifacts pass and {result['audit']['normal_parents']}/56 parents complete normally. The [complete panels](memory-aware-results.md) and [final audit](memory-aware-final-audit.md) retain every result. This section supersedes the status of earlier chronological preparation entries, without changing their evidence.",'',
        'Cell27 finishes its native coding turn and seals the source, but the broker exceeds its30-second shutdown wait. Independent replay uses the same saved implementation without a model restart. A graph export survives; one unfinished publication and the unobserved service exit remain gaps. Cells28–56 have a prospectively registered180-second post-generation wait and explicit exit receipts. None of these shutdown waits are coding/inference budget extensions.','',
        'Cell32 reaches its observed token threshold and its original source replay records199 passes, one failure and one skip. The failure is retained without repair or replacement. An already-started Luna process briefly outlives the broker; auditing resumes only after it ends, without restarting it or rerunning the grade. From cell33 onward a bounded passive drain precedes audit. Completed provider responses absent from native transcripts are retained as explicitly labeled single-witness measurements; no complete total is inferred.','',
        'The following runtime values come from finite broker execution receipts. They are recorded processing sums, not native agent-blocking time, pure inference time or full deployment latency. Missing runtimes remain unknown. Service startup ends at the ready marker; background service lifetime is not added to task time. The post-manifest preparation window omits earlier source preparation.','',
        '| Backend | Service startup mean (n) | Post-manifest preparation mean (n) | Recorded publish seconds | Recorded search seconds | Recorded read seconds | Recorded log-ingest seconds | Missing operation runtimes |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for arm in ('mem0_luna','graphiti_luna','smallville_luna','searchable_logs'):
        rows=[r for r in audit['archives'] if r['arm']==arm];windows=[]
        for field in ('memory_service_startup_window_seconds','post_manifest_to_run_start_seconds'):
            values=[r['startup'][field] for r in rows if r['startup'][field] is not None]
            windows.append(f'{statistics.mean(values):.3f} ({len(values)})' if values else 'unknown (0)')
        seconds=[sum(r['summed_operation_runtime_seconds'].get(op,0) for r in rows) for op in ('publish_finding','search_memory','read_record','ingest_visible')]
        lines.append('| '+LABELS[arm]+' | '+' | '.join(windows)+' | '+' | '.join(f'{x:.3f}' for x in seconds)+' | '+str(sum(r['operation_runtime_unknown'] for r in rows))+' |')
    lines+=['','Recorded operation sums are already within the relevant coding run where they occur. Do not add them again to parent-run time. Zero recorded seconds is not proof of zero unobserved computation. Local embedding callback counts/time and unknown local monetary cost are in the audit JSON.','',
        '| Memory backend | Preserved Luna maintenance intents by actual role |',
        '| --- | --- |']
    for arm in ('mem0_luna','graphiti_luna','smallville_luna'):
        counts=Counter()
        for row in audit['archives']:
            if row['arm']==arm:counts.update(row['maintenance_intents_by_role'])
        roles='; '.join(f'`{role}`: {count}' for role,count in sorted(counts.items())) or 'No preserved intent'
        lines.append('| '+LABELS[arm]+' | '+roles+' |')
    lines+=['','An intent records an attempted role, not necessarily a successful extraction or completed reflection. All recorded native maintenance responses are charged in the model-rate scenario; missing responses are unknown. Smallville reflects only when its natural threshold is reached. The presence of reflection code is not a measured reflection count.','',
        'Official MCP retention is reconciled separately. Accepted publication occurrences may repeat identical text; unique accepted observations and final-store contents are therefore counted separately. A missing accepted observation is reported only when no deletion call occurred, without assigning an unobserved cause.','',
        '| Official MCP cell | Accepted publication occurrences | Unique accepted observations | Final-store observations | Accepted observations absent at seal |',
        '| --- | ---: | ---: | ---: | ---: |']
    for row in audit['official_mcp_exposure']:
        values=[row['returned_publication_observations'],row.get('unique_announced_observations'),row.get('sealed_observation_count'),row.get('accepted_observations_absent_from_sealed_file')]
        lines.append('| '+row['directory']+' | '+' | '.join(str(v) if v is not None else 'unknown' for v in values)+' |')
    lines+=['',
        'Exact peer exposure is defined separately for official MCP observations and the four broker arms. Original-record read counts are completed pages, which need not cover every character of a record. Explicit tool errors count failed calls, including propagated failures, rather than independent root causes. Useful checked integration and causal effects require additional trace evidence.','',
        '[Reproduction and code/setup details](REPRODUCING.md), [migration-agent prompt](PORTING_PROMPT.md). All failed preparations, budget stops, skips, lower bounds and historical pilot records remain preserved.']
    return '\n'.join(lines)+'\n'


def update(output):
    result=json.loads((output/'memory-aware-results.json').read_text());audit=json.loads((output/'memory-aware-final-audit.json').read_text())
    path=output/'paper.md';before=path.read_bytes();after=render(before.decode(),result,audit)
    if path.read_bytes()!=before:raise ValueError('Concurrent paper edit; draft write stopped')
    path.write_text(after)
    appendix_path=output/'appendix.md';appendix=appendix_path.read_text()
    appendix=appendix.split('## G. Completed memory-aware comparison',1)[0].rstrip()+'\n\n'+appendix_summary(result,audit)
    note='The preparation and early-cell entries below preserve their original checkpoints. The completed 56-cell comparison is summarized in [section G](#g-completed-memory-aware-comparison).\n\n'
    marker='## D. Separate registered extensions\n\n'
    if note not in appendix:appendix=appendix.replace(marker,marker+note,1)
    appendix_path.write_text(appendix)
    p=result['audit']['source_passes'];normal=result['audit']['normal_parents']
    (output/'README.md').write_text(f'''# Native Codex teams and shared knowledge

The [paper](paper.md) includes the completed 24-cell pilot and a separate completed
**56-cell memory-aware comparison**. Extension source artifacts pass in **{p}/56**
cells; **{normal}/56** parents complete normally. Unknown usage remains null or a
lower bound. These are reused two-library development results, with a disclosed
dependency amendment. They do not establish held-out learning or a causal benefit.
Source pass rates are conditional on task-model invocation; archived pre-model
preparation failures remain separate operational evidence.

The seven arms are native, notebook, official MCP memory, Mem0/Luna,
Graphiti/Luna, adapted Smallville/Luna and shared searchable visible logs.
Sol low codes; Luna handles model-based memory. Every parent/child receives
explicit tools and common publication/retrieval/revalidation guidance.

- [Final audit and arm comparison](memory-aware-final-audit.md)
- [All 28 scaling panels](memory-aware-results.md), [cells CSV](memory-aware-cells.csv), [full measurements](memory-aware-results.json)
- [Standalone SVG figures and self-contained HTML](figures/memory-aware-figures.html)
- [Experiment details and actual memory/communication excerpts](appendix.md)
- [Reproduction commands](REPRODUCING.md), [migration-agent prompt](PORTING_PROMPT.md)

The [completed pilot](pilot-results.md) retains its own [CSV](pilot-cells.csv),
[JSON](pilot-results.json) and [PDF figures](figures/pilot-scaling.pdf).
The historical [reserved-library extension](reserved-extension.md) is interrupted
and remains separate. All failed submissions, preparation/security blockers and
unknown counters are preserved. No research schedule is enabled; raw private
captures and credentials are outside tracked files.
''')
    return dict(paper_before_sha256=hashlib.sha256(before).hexdigest(),paper_after_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                source_passes=p,normal_parents=normal,model_calls=0,requires_editorial_review=True)


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();print(json.dumps(update(a.output)))
