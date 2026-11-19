"""Frozen construction prefixes and equal-information transfer campaigns.

This module performs no inference and never promotes a model summary to verified
knowledge. It consumes host-audited public records, including negative outcomes.
"""
from __future__ import annotations

from copy import deepcopy
from .routing import similarity, timestamp
from ..experience_routing.io import digest, canonical, write_new

SYSTEMS = ('luna', 'sol', 'frugalgpt_native', 'routellm_native', 'observatory')


def validate_partitions(partitions):
    """Reject aliases and shared issue/fix/base lineages across all partitions."""
    seen = {}
    for partition, tasks in partitions.items():
        for task in tasks:
            if not task.get('task_id') or not task.get('lineage_ids'):
                raise ValueError('Explicit task identity and audited lineage IDs required')
            keys = [('task', task['task_id'])]
            keys += [('task', a) for a in task.get('aliases', [])]
            keys += [('lineage', a) for a in task['lineage_ids']]
            for key in keys:
                if key in seen:
                    raise ValueError('Repeated task/lineage: ' + str(key))
                seen[key] = partition
    return digest(partitions)


def build_snapshots(partitions, records, *, prefixes=(0, 4, 8, 12), scope, watermark):
    if any(not isinstance(scope.get(k), str) or not scope[k] for k in ('project', 'study', 'account_hash')):
        raise ValueError('Explicit source/project/study snapshot scope required')
    validate_partitions(partitions)
    construction = partitions['construction']
    if (not prefixes or prefixes[0] != 0 or list(prefixes) != sorted(set(prefixes))
            or any(type(n) is not int or not 0 <= n <= len(construction) for n in prefixes)):
        raise ValueError('Ordered unique construction prefixes starting at zero required')
    cutoff = timestamp(watermark)
    task_map = {t['task_id']: t for t in construction}
    admitted, excluded, seen = [], [], set()
    for record in records:
        r = deepcopy(record)
        if not r.get('id') or r['id'] in seen:
            raise ValueError('Unique evidence identity required')
        seen.add(r['id'])
        reason = None
        if r.get('task_id') not in task_map:
            reason = 'not_construction'
        elif any(r.get(k) != v for k, v in scope.items()):
            reason = 'source_scope'
        elif (r.get('visibility') != 'runtime_public' or r.get('verified') is not True
                or r.get('source_current') is not True or not r.get('verification_ref')
                or r.get('outcome') not in ('pass', 'fail') or not r.get('executor_model')):
            reason = 'unsupported_public_outcome'
        elif r.get('support_scope') != 'public_integrated':
            reason = 'unverified_integration'
        else:
            try:
                occurred, verified, available = (timestamp(r[k]) for k in ('occurred_at', 'verified_at', 'available_at'))
                if not occurred <= verified <= available <= cutoff:
                    reason = 'chronology'
            except (KeyError, TypeError, ValueError):
                reason = 'chronology'
        if reason:
            excluded.append({'id': r['id'], 'reason': reason})
        else:
            admitted.append(r)
    snapshots = []
    for n in prefixes:
        ids = [t['task_id'] for t in construction[:n]]
        evidence = sorted((r for r in admitted if r['task_id'] in ids), key=lambda r: r['id'])
        body = {'schema_version': 1, 'scope': deepcopy(scope), 'watermark': watermark,
                'construction_prefix': n, 'construction_task_ids': ids, 'experiences': evidence,
                'supporting_parents': len({r['task_id'] for r in evidence}),
                'failed_records': sum(r['outcome'] == 'fail' for r in evidence),
                'partition_hash': digest(partitions)}
        snapshots.append({**body, 'snapshot_id': digest(body)})
    return {'snapshots': snapshots, 'excluded': excluded, 'model_calls': 0}


def retrieve(snapshot, query, *, maximum_bytes=8000):
    """Common standalone/router retrieval: ranking does not select an executor."""
    if type(maximum_bytes) is not int or maximum_bytes < 128:
        raise ValueError('Positive bounded packet budget required')
    body = {k: v for k, v in snapshot.items() if k != 'snapshot_id'}
    if digest(body) != snapshot.get('snapshot_id'):
        raise ValueError('Snapshot integrity mismatch')
    if query['task_id'] in snapshot['construction_task_ids']:
        raise ValueError('Cannot evaluate a construction task against its own library')
    packet = {'snapshot_id': snapshot['snapshot_id'], 'experiences': []}
    records = sorted(snapshot['experiences'], key=lambda r: (-similarity(query, r), r['id']))
    for record in records:
        if similarity(query, record) <= 0:
            continue
        public = deepcopy(record)
        # Exact benchmark identity remains host-side for exclusion/auditing.
        # Runtime provenance is opaque, never a benchmark routing feature.
        public['source_parent_ref'] = digest(public.pop('task_id'))
        packet['experiences'].append(public)
        if len(canonical(packet).encode()) > maximum_bytes:
            packet['experiences'].pop()
    return packet


def build_campaign(partitions, snapshots, *, systems=SYSTEMS, points=('balanced',), limits,
                   source_pins, baseline_pins, stage='development'):
    """Register every assignment and full upper-bound budget before dispatch."""
    partition_hash = validate_partitions(partitions)
    if stage not in ('development', 'heldout') or not partitions.get(stage):
        raise ValueError('Explicit nonempty evaluation partition required')
    if (not systems or len(set(systems)) != len(systems) or set(systems) - set(SYSTEMS)
            or not points or len(set(points)) != len(points)):
        raise ValueError('Unique known systems and operating points required')
    for name in ('maximum_invocations', 'maximum_tokens', 'maximum_elapsed_seconds'):
        value = limits.get(name)
        if type(value) is not int or value <= 0:
            raise ValueError('Finite positive integer ' + name + ' required')
    for key in ('source_binding', 'actor', 'models', 'rates', 'controls', 'exclusions'):
        if (not isinstance(source_pins.get(key), str) or len(source_pins[key]) != 64
                or any(c not in '0123456789abcdef' for c in source_pins[key])):
            raise ValueError('Missing exact source pin: ' + key)
    for system in set(systems) & {'frugalgpt_native', 'routellm_native'}:
        pin = baseline_pins.get(system, {})
        if (pin.get('qualified') is not True or not pin.get('implementation_sha256')
                or not pin.get('calibration_sha256') or pin.get('training_partition') != 'development'
                or pin.get('sufficiency_passed') is not True):
            raise ValueError('Required released baseline is unqualified: ' + system)
    if not snapshots or len({s['snapshot_id'] for s in snapshots}) != len(snapshots):
        raise ValueError('Unique snapshots required')
    rows = []
    for snapshot in snapshots:
        body = {k: v for k, v in snapshot.items() if k != 'snapshot_id'}
        if digest(body) != snapshot['snapshot_id'] or snapshot['partition_hash'] != partition_hash:
            raise ValueError('Snapshot drift or partition mismatch')
        for task in partitions[stage]:
            for system in systems:
                # Standalone endpoints have no threshold operating point.
                for point in (('endpoint',) if system in ('luna', 'sol') else points):
                    row = {'task_id': task['task_id'], 'system': system, 'point': point,
                           'snapshot_id': snapshot['snapshot_id'], 'limits': deepcopy(limits)}
                    rows.append({**row, 'assignment_id': digest(row)})
    body = {'schema_version': 1, 'stage': stage, 'partition_hash': partition_hash,
            'source_pins': deepcopy(source_pins), 'baseline_pins': deepcopy(baseline_pins),
            'assignments': rows, 'automatic_retries': 0, 'grades_sealed': True,
            'maximum_totals': {k: v * len(rows) for k, v in limits.items()},
            'scheduled_inference': False}
    return {**body, 'campaign_id': digest(body)}


def run_campaign(campaign, output, execute, *, qualification, after_completion=None):
    """Single-owner finite execution; any uncertain/start-only assignment stops.

    The supplied host adapter must enforce invocation/token/time limits internally.
    Started assignments can never be resubmitted by re-entering this function.
    """
    from pathlib import Path
    body = {k: v for k, v in campaign.items() if k != 'campaign_id'}
    if digest(body) != campaign['campaign_id']:
        raise ValueError('Campaign integrity mismatch')
    if (qualification.get('campaign_id') != campaign['campaign_id']
            or qualification.get('execution_ready') is not True
            or qualification.get('source_pins') != campaign['source_pins']):
        raise ValueError('Exact native campaign qualification required')
    output = Path(output)
    # An existing owner is a reconciliation case, never a fresh invocation.
    write_new(output/'owner.json', {'campaign_id': campaign['campaign_id']})
    executed = unrun = shared = deadlines = wall_rejections = 0
    terminal_ids = set()
    for assignment in campaign['assignments']:
        folder = output/assignment['assignment_id']
        write_new(folder/'started.json', assignment)
        try:
            if assignment.get('execution_disposition') == 'infeasible_before_heldout':
                write_new(folder/'completion.json', {'status':'unrun_infeasible',
                    'native_invocations':0,'quality':None,'scenario_cost':None,
                    'reason':'No qualified policy meets the frozen development operating-point budget'})
                unrun += 1
                continue
            if assignment.get('execution_disposition') == 'duplicate_policy':
                reference_id = assignment['shared_assignment_id']
                if reference_id not in terminal_ids:
                    raise ValueError('A duplicate policy needs a closed source assignment')
                write_new(folder / 'completion.json', {
                    'status': 'duplicate_policy',
                    'shared_assignment_id': reference_id,
                    'native_invocations': 0,
                })
                shared += 1
                continue
            result = execute(deepcopy(assignment), folder)
            if any(k in result for k in ('grade', 'resolved', 'hidden_feedback')):
                raise ValueError('Live adapter must not receive hidden grades')
            if (qualification.get('retain_recorded_timeouts') is True
                    and result.get('status') == 'native_timeout'
                    and result.get('verified_parent_deadline') is True and result.get('usage') is None):
                write_new(folder / 'completion.json', result)
                terminal_ids.add(assignment['assignment_id'])
                deadlines += 1
                continue
            if result.get('status') not in ('completed', 'public_failure'):
                raise ValueError('Uncertain native assignment; stop without retry')
            usage = result.get('usage', {})
            wall_rejected = False
            for key, cap in assignment['limits'].items():
                observed = usage.get(key)
                if type(observed) not in (int, float) or not 0 <= observed < float('inf'):
                    raise ValueError('Missing or nonfinite assignment usage: ' + key)
                if observed <= cap:
                    continue
                if key == 'maximum_elapsed_seconds' and qualification.get('retain_metered_wall_overruns') is True:
                    wall_rejected = True
                    continue
                raise ValueError('Exceeded assignment limit: ' + key)
            if wall_rejected:
                result = {**result, 'status': 'budget_rejected', 'budget_failure': 'full_assignment_wall_time'}
                wall_rejections += 1
            write_new(folder/'completion.json', result)
            terminal_ids.add(assignment['assignment_id'])
            executed += 1
            if after_completion is not None:
                after_completion(assignment, folder, result)
        except BaseException as error:
            write_new(folder/'stopped.json', {'error': type(error).__name__, 'automatic_retry': False})
            raise
    write_new(output/'completion.json', {'campaign_id': campaign['campaign_id'],
              'assignments_completed': executed, 'assignments_unrun_infeasible': unrun,
              'assignments_shared_duplicate_policy': shared, 'assignments_native_timeout': deadlines,
              'assignments_budget_rejected': wall_rejections,
              'assignments_registered': len(campaign['assignments']), 'grades_sealed': True})


def build_comparison_campaign(partitions, snapshots, *, limits, source_pins, baseline_pins,
                              points=('cost', 'balanced', 'quality'), stage='heldout'):
    """Core accumulation cells plus all named router points at the final prefix.

    For 32 tasks and 4 prefixes: 384 core + 192 named-baseline + 64 additional
    Observatory operating-point episodes = 640, without duplicated endpoints or
    the already registered balanced Observatory point. Optional simple controls
    and recency ablations need their own explicit additional assignment manifest.
    """
    if 'balanced' not in points:
        raise ValueError('Core accumulation requires the balanced operating point')
    core = build_campaign(partitions, snapshots, systems=('luna', 'sol', 'observatory'),
        points=('balanced',), limits=limits, source_pins=source_pins, baseline_pins=baseline_pins, stage=stage)
    final = max(snapshots, key=lambda s: s['construction_prefix'])
    comparative = build_campaign(partitions, [final], systems=('frugalgpt_native', 'routellm_native', 'observatory'),
        points=points, limits=limits, source_pins=source_pins, baseline_pins=baseline_pins, stage=stage)
    by_id = {a['assignment_id']: a for a in [*core['assignments'], *comparative['assignments']]}
    rows = list(by_id.values())
    shared_policies = {}
    for row in rows:
        pins = baseline_pins.get(row['system'], {})
        point = row['point']
        if pins.get('point_feasibility', {}).get(point) is False:
            row['execution_disposition'] = 'infeasible_before_heldout'
            continue
        policy = pins.get('point_policy_sha256', {}).get(point)
        if policy is None:
            continue
        if not isinstance(policy, str) or len(policy) != 64 or any(c not in '0123456789abcdef' for c in policy):
            raise ValueError('Duplicate-policy identity must be an exact SHA-256 digest')
        key = (row['task_id'], row['snapshot_id'], row['system'], policy)
        reference = shared_policies.setdefault(key, row['assignment_id'])
        if reference != row['assignment_id']:
            row.update(execution_disposition='duplicate_policy', shared_assignment_id=reference)
    runnable = sum('execution_disposition' not in row for row in rows)
    body = {k: v for k, v in core.items() if k not in ('campaign_id', 'assignments', 'maximum_totals')}
    body.update(assignments=rows, maximum_totals={k: v*runnable for k, v in limits.items()},
                assignments_scheduled_for_native_execution=runnable,
                matrix_kind='core_accumulation_plus_final_snapshot_required_baselines',
                simple_controls_included=False, recency_ablation_included=False)
    return {**body, 'campaign_id': digest(body)}
