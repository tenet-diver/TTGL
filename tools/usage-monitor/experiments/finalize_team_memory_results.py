#!/usr/bin/env python3
"""Independent read-only final archive/runtime audit and public tables.

Requires all 56 registered cells. No inference, retries, grading, service changes
or raw-data publication. Existing failed/unknown evidence remains untouched.
"""
import argparse
from collections import Counter
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import tarfile

from analyze_team_memory_extension import analyze,publish
from inspect_team_memory_trace import inspect
from inspect_team_official_memory import inspect as inspect_official


def sha(path):
    with path.open('rb') as stream:return hashlib.file_digest(stream,'sha256').hexdigest()


def archive_audit(cell):
    archive=cell/'snapshot.tar.xz';receipt=json.loads((cell/'recompression-001.json').read_text())
    original=json.loads((cell/'archive.json').read_text());digest=sha(archive)
    if not original['verified'] or not receipt['exact_raw_tar_roundtrip'] or digest!=receipt['xz_sha256']:
        raise ValueError('Lossless sealed archive mismatch: '+cell.name)
    observed={};links={};roles=Counter();operations={};operation_results={}
    with tarfile.open(archive,'r:xz') as tar:
        for member in tar:
            if member.isfile():
                stream=tar.extractfile(member)
                receipt_member=(member.name.startswith('memory/backend/') and '/call-' in member.name and member.name.endswith('/intent.json'))
                operation_member=member.name.startswith('memory/requests/') and member.name.endswith(('.intent.json','.result.json'))
                if receipt_member or operation_member:
                    data=stream.read();observed[member.name]=hashlib.sha256(data).hexdigest()
                    value=json.loads(data)
                    if receipt_member and member.name.endswith('/intent.json'):
                        role=value.get('role','unattributed')
                        if value.get('model')!='gpt-6-luna':raise ValueError('Unexpected maintenance model')
                        roles[role]+=1
                    elif operation_member:
                        name=member.name.rsplit('.',2)[0]
                        if member.name.endswith('.intent.json'):operations[name]=value['request']['operation']
                        else:operation_results[name]=value
                else:observed[member.name]=hashlib.file_digest(stream,'sha256').hexdigest()
            elif member.issym():links[member.name]=member.linkname
            else:raise ValueError('Unexpected archive member type')
    if observed!=original['file_hashes'] or links!=original['symlinks']:
        raise ValueError('Archived file/link hashes changed: '+cell.name)
    operation_counts=Counter(operations.values());seconds=Counter();completed=Counter()
    for name,value in operation_results.items():
        if name not in operations:raise ValueError('Operation result without original intent')
        duration=value['seconds']
        if not isinstance(duration,(float,int)) or duration<0:raise ValueError('Invalid operation runtime')
        seconds[operations[name]]+=duration;completed[operations[name]]+=1
    return dict(directory=cell.name,archive_sha256=digest,verified_files=len(observed),verified_links=len(links),
        maintenance_intents_by_role=dict(roles),memory_operation_intents=dict(operation_counts),
        completed_memory_operations=dict(completed),summed_operation_runtime_seconds=dict(seconds),
        operation_runtime_unknown=sum(operation_counts.values())-sum(completed.values()),
        timing_scope='Broker perf_counter execution receipts; queue wait/client blocking and total task time differ. Serial runtime sums are not additional inference tokens.',
        raw_files_publicly_exported=False)


def startup_windows(cell):
    result=dict(memory_service_startup_window_seconds=None,post_manifest_to_run_start_seconds=None,
        scope='Finite recorded startup/preparation windows, not background service lifetime or full deployment cost. Manifest follows initial source preparation; its window omits earlier setup.')
    start=cell/'memory/service-started.json';ready=cell/'memory/ready.json'
    if start.exists() and ready.exists():
        seconds=(json.loads(ready.read_text())['at_ns']-json.loads(start.read_text())['at_ns'])/1e9
        if seconds<0:raise ValueError('Startup clock order invalid')
        result['memory_service_startup_window_seconds']=seconds
    manifest=cell/'manifest.json';started=cell/'started.json'
    if manifest.exists() and started.exists():
        seconds=(datetime.fromisoformat(json.loads(started.read_text())['at'])-datetime.fromisoformat(json.loads(manifest.read_text())['created_at'])).total_seconds()
        if seconds<0:raise ValueError('Preparation clock order invalid')
        result['post_manifest_to_run_start_seconds']=seconds
    return result


def service_termination(cell):
    path=cell/'memory-service-ended.json'
    if path.exists():
        value=json.loads(path.read_text())
        return dict(receipt_sha256=sha(path),exit_code=value['exit_code'],
            post_generation_wait_limit_seconds=value['post_generation_wait_limit_seconds'],shutdown_timeout=False)
    recovery=cell/'post-generation-recovery-started-010.json'
    if recovery.exists():
        value=json.loads(recovery.read_text())
        return dict(receipt_sha256=sha(recovery),exit_code=None,post_generation_wait_limit_seconds=30,
            shutdown_timeout=value['shutdown_timed_out'],
            scope='Completed coding turn independently replayed without model restart; exported graph retained, unfinished publication and service exit remain incomplete evidence.')
    return dict(receipt_sha256=None,exit_code=None,shutdown_timeout=None,
        scope='No explicit service termination receipt in this historical cell; absence is not proof of failure or success.')


def totals(cells):
    models={}
    for row in cells:
        for model,usage in row['native_usage_by_model'].items():
            bucket=models.setdefault(model,{k:0 for k in usage})
            for k,v in usage.items():bucket[k]+=v
    known={k:sum(v[k] for v in models.values()) for k in next(iter(models.values()))}
    complete=all(c['inference_accounting_complete'] for c in cells)
    credits=sum(c['standard_credit_scenario_lower_bound'] for c in cells)
    return dict(recorded_native_usage_lower_bound=known,recorded_usage_by_model=models,
        actual_total_native_usage=known if complete else None,
        standard_scenario_credits_lower_bound=credits,standard_scenario_total=credits if complete else None,
        unknown_requests=sum(c['unknown_request_count'] for c in cells),
        observed_local_embedding_calls=sum(c['observed_local_embedding_inferences'] for c in cells),
        summed_embedding_callback_seconds=sum(c['summed_recorded_embedding_seconds'] for c in cells),
        cash_expense=None,quota_savings=None,local_compute_cost=None,research_overhead='Additional, incompletely measured; no net-saving claim')


def finalize(root,protocol,config_path,output):
    result=analyze(root,protocol)
    if result['state']!='complete' or result['completed']!=56 or result['planned']!=56:
        raise ValueError('The full registered study must end before final publication')
    config=json.loads(config_path.read_text());verified=0
    for category in ('frozen_sources','gate_files','runtime_sources'):
        for path,expected in config[category].items():
            if sha(Path(path))!=expected:raise ValueError('Final pinned source/runtime/gate mismatch: '+path)
            verified+=1
        print(json.dumps(dict(stage='integrity',category=category,checked=len(config[category]))),flush=True)
    archives=[];exposure=[];official=[];capture_only=[]
    new_arms={'mem0_luna','graphiti_luna','smallville_luna','searchable_logs'}
    for row in result['cells']:
        cell=root/row['directory'];archives.append(dict(arm=row['arm'],task=row['task'],capacity=row['total_agent_capacity'],
            startup=startup_windows(cell),service_termination=service_termination(cell),**archive_audit(cell)))
        measured=json.loads((cell/'combined-usage-audit.json').read_text())
        evidence={r['response_id'] for r in measured['responses']}
        for response in measured.get('capture_only_completed_responses',[]):
            if response['response_id'] not in evidence or measured['complete']:
                raise ValueError('Single-witness transport coverage was silently treated as complete')
            capture_only.append(dict(directory=cell.name,**response))
        if row['arm'] in new_arms:
            trace=inspect(cell)
            keys=['completed_memory_calls','published_record_ids','completed_searches','nonempty_searches',
                  'known_peer_search_calls','original_record_reads','known_peer_record_reads','explicit_tool_errors',
                  'partial_line_or_schema_gap','interpretation_version']
            exposure.append(dict(directory=cell.name,arm=row['arm'],task=row['task'],capacity=row['total_agent_capacity'],
                trace_source_sha256=trace['source_sha256'],**{k:trace[k] for k in keys}))
        elif row['arm']=='mcp_memory':
            official.append(dict(directory=cell.name,**inspect_official(cell)))
        print(json.dumps(dict(stage='archive_and_exposure',completed=len(archives),directory=cell.name)),flush=True)
    report=dict(at=datetime.now(timezone.utc).isoformat(),passed=True,registered_cells=56,
        duplicate_response_ownership_rejected=True,positive_response_count=result['audit']['distinct_completed_responses'],
        pinned_source_runtime_gate_checks=verified,archives=archives,exposure=exposure,official_mcp_exposure=official,
        analysis_source_sha256={p.name:sha(p) for p in [Path(__file__),Path(__file__).with_name('analyze_team_memory_extension.py'),
            Path(__file__).with_name('inspect_team_memory_trace.py'),Path(__file__).with_name('inspect_team_official_memory.py')]},
        totals=totals(result['cells']),
        capture_only_completed_responses=capture_only,
        capture_only_recorded_tokens=sum(r['usage']['total_tokens'] for r in capture_only),
        operational_scope='Source quality is conditional on actual task-model invocation. Archived pre-model preparation failures and cell27 post-generation broker timeout remain operational incidents; no started task-model call was repeated.',
        limitations=['Exposure counters cover the four custom-broker arms; native/notebook/official MCP communication is not zero or covered by these counters.',
            'Peer exposure uses identifiable native actors/immutable publication IDs. Unattributed extracted facts are not assumed to come from peers.',
            'Maintenance roles count preserved intents, not necessarily successful extraction/reflection.',
            'Official MCP uses separately defined exact-observation exposure counts; they are not directly equated with graph-fact or log-preview counts.',
            'No new model call, test grading, assignment retry or private transcript publication.'])
    publish(result,output)
    (output/'memory-aware-final-audit.json').write_text(json.dumps(report,indent=2)+'\n')
    lines=['# Final memory-aware study audit','',f"All **56/56** registered cells ended; {result['audit']['source_passes']} source artifacts pass, {result['audit']['normal_parents']} parents complete normally.",'',
        '| Arm | Cells | Verified sources | Normal parents | Complete usage | Mean run-end seconds | Mean Standard credits |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for arm in result['arms']:
        prefix='' if arm['accounting_complete'] else '≥'
        lines.append(f"| {arm['arm']} | {arm['completed']}/{arm['planned']} | {arm['successes']}/{arm['completed']} | {arm['normal_parents']}/{arm['completed']} | {arm['accounting_complete_cells']}/{arm['completed']} | {arm['mean_seconds']:.1f} | {prefix}{arm['mean_credit_lower_bound']:.4f} |")
    lines+=['','Every arm has the same two libraries × four capacities. These arm averages are descriptive across capacities; use the [28 matched panels](memory-aware-results.md) for scaling comparisons. Run-end times include stopped parents and are not success-only speed estimates. Unknown cost totals remain lower bounds, not ranked point estimates.','',
        '| Arm | Publications | Searches | Nonempty searches | Known peer searches | Original reads | Known peer reads | Explicit tool errors |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |']
    for arm in ['mem0_luna','graphiti_luna','smallville_luna','searchable_logs']:
        rows=[r for r in exposure if r['arm']==arm]
        fields=['published_record_ids','completed_searches','nonempty_searches','known_peer_search_calls','original_record_reads','known_peer_record_reads','explicit_tool_errors']
        lines.append('| '+arm+' | '+' | '.join(str(sum(r[k] for r in rows)) for k in fields)+' |')
    lines+=['',f"Official MCP separately records {sum(r['returned_publication_observations'] for r in official)} returned publication observations, {sum(r['completed_read_queries'] for r in official)} read queries, {sum(r['nonempty_read_queries'] for r in official)} nonempty queries and {sum(r['known_peer_read_queries'] for r in official)} queries with exactly attributable peer observation text. These definitions differ from backend search-hit counts."]
    t=report['totals'];lines+=['',
        f"Recorded inference is at least **{t['recorded_native_usage_lower_bound']['total_tokens']:,} tokens**, across Sol and Luna. There are {t['unknown_requests']} incomplete-usage or native-coverage-gap receipts. The dated Standard-rate sum is **≥{t['standard_scenario_credits_lower_bound']:.4f} credits**. Cash, subscription quota and local compute prices are unknown; preparation/research overhead is additional.",'',
        f"Of the recorded tokens, {report['capture_only_recorded_tokens']:,} come from {len(capture_only)} completed provider captures without a matching retained native transcript record. They are deduplicated positive single-witness measurements, included in expenditure, and explicitly marked as native coverage gaps. They do not establish complete total usage. All other counted responses reconcile native records and transport receipts.",'',
        'Cell27 completes its native coding turn but exceeds the original30-second broker shutdown wait. Its saved source is independently replayed without another model call. The graph export is retained; an unfinished publication and unobserved service exit remain explicit evidence gaps. Cells28–56 use a prospectively registered180-second post-generation wait and explicit termination receipts. This is separate from coding time and inference budget.','',
        'Source/usage ownership, all archived file/link hashes, exact XZ archive hashes and the pinned runtime were independently checked without model calls. Source quality is conditional on task-model invocation, not flawless first-launch reliability; pre-model preparation failures stay archived. Publication, returned evidence and useful checked action remain separate. This is reused development evidence with disclosed runtime/transport amendments, not held-out transfer or a causal learning result.','',
        '[Audit JSON and provenance](memory-aware-final-audit.json), [all cells](memory-aware-cells.csv), [appendix](appendix.md).']
    (output/'memory-aware-final-audit.md').write_text('\n'.join(lines)+'\n')
    return report


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('root','protocol','config','output'):p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();value=finalize(a.root.resolve(),a.protocol,a.config,a.output)
    print(json.dumps(dict(passed=value['passed'],registered_cells=value['registered_cells'])))
