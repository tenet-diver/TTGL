"""Deterministic, auditable advisory evidence; no new models/dependencies.

Scores are descriptive weighted observations, never calibrated probabilities.
Availability and source/task eligibility precede ranking. Publication time is
not experience age: re-importing old evidence cannot rejuvenate it.
"""
from __future__ import annotations

from dataclasses import dataclass, asdict
from datetime import datetime, timezone
import math
import re

from ..experience_routing.io import digest
from .grounding import applicable_guidance, build_packet, string_list


def timestamp(value):
    if not isinstance(value, str):
        raise ValueError('An explicit timezone-aware timestamp is required')
    result = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if result.tzinfo is None:
        raise ValueError('Naive evidence timestamps are not allowed')
    return result.astimezone(timezone.utc)


def number(value, name, minimum=0):
    if isinstance(value, bool) or not isinstance(value, (float, int)) or not math.isfinite(value) or value < minimum:
        raise ValueError('Invalid ' + name)
    return value


STOP = frozenset('the and for with from this that into have should would could task please using'.split())


def tokens(value):
    return set(re.findall(r'[a-z][a-z0-9_]{1,}', value.lower())) - STOP


def similarity(query, evidence, profile='subtask_v2'):
    a, b = tokens(query['goal']), tokens(evidence['goal'])
    lexical = len(a & b) / math.sqrt(len(a) * len(b)) if a and b else 0.0
    # Action/category is an input feature, not a claim that the tasks are identical.
    category = float(bool(query.get('category')) and query.get('category') == evidence.get('category'))
    qa, ea = set(query.get('actions', [])), set(evidence.get('actions', []))
    actions = len(qa & ea) / len(qa | ea) if qa | ea else 0.0
    if profile == 'whole_task_proxy':
        return .60 * lexical + .25 * category + .15 * actions
    qc, ec = set(query.get('constraints', [])), set(evidence.get('constraints', []))
    constraints = len(qc & ec) / len(qc | ec) if qc | ec else 0.0
    kind = float(query.get('subtask_type') == evidence.get('subtask_type'))
    return .40 * lexical + .25 * kind + .20 * constraints + .15 * actions


@dataclass(frozen=True)
class Policy:
    mode: str = 'similarity_recency'
    half_life_days: float = 30.0
    minimum_similarity: float = .45
    minimum_parents: int = 2
    minimum_weight: float = 1.0
    minimum_success_estimate: float = .70
    maximum_age_days: float = 365.0
    maximum_records: int = 2000
    maximum_packet_bytes: int = 8000
    evidence_profile: str = 'subtask_v2'

    def __post_init__(self):
        if self.mode not in ('always_cheap', 'similarity', 'similarity_recency'):
            raise ValueError('Unknown routing ablation')
        if self.evidence_profile not in ('subtask_v2', 'whole_task_proxy'):
            raise ValueError('Unknown evidence granularity profile')
        for field in ('half_life_days', 'minimum_similarity', 'minimum_weight', 'minimum_success_estimate', 'maximum_age_days'):
            number(getattr(self, field), field)
        if self.half_life_days <= 0 or self.maximum_age_days <= 0:
            raise ValueError('Positive age bounds required')
        if not 0 <= self.minimum_similarity <= 1 or not 0 <= self.minimum_success_estimate <= 1:
            raise ValueError('Similarity and descriptive success thresholds must be in [0,1]')
        for field in ('minimum_parents', 'maximum_records', 'maximum_packet_bytes'):
            if type(getattr(self, field)) is not int or getattr(self, field) <= 0:
                raise ValueError('Positive integer ' + field + ' required')


def route(query, experiences, models, policy=Policy()):
    """Pure routing function over a host-frozen query/time and evidence snapshot.

    `account_hash`, `study`, `arm`, `watermark` and `now` come from the tool host,
    never from a tool caller trying to see another source's experience.
    """
    for key in ('task_id', 'goal', 'project', 'study', 'arm', 'account_hash', 'parent_model', 'rate_scenario'):
        if not isinstance(query.get(key), str) or not query[key]:
            raise ValueError('Missing routing field ' + key)
    if len(query['goal']) > 32000 or len(experiences) > policy.maximum_records:
        raise ValueError('Routing input exceeds declared bounds')
    for field in ('actions', 'constraints', 'required_capabilities', 'excluded_task_ids', 'excluded_leakage_groups'):
        if not isinstance(query.get(field, []), list) or any(not isinstance(x, str) for x in query.get(field, [])):
            raise ValueError('Invalid feature list ' + field)
    for field in ('category', 'subtask_type', 'language', 'framework'):
        if field in query and not isinstance(query[field], str):
            raise ValueError('Invalid feature ' + field)
    if policy.evidence_profile == 'subtask_v2' and not query.get('subtask_type'):
        raise ValueError('Explicit subtask type required for live routing')
    if policy.evidence_profile == 'whole_task_proxy' and query['account_hash'] != 'simulation-no-native-source-binding':
        raise ValueError('Whole-task proxy evidence is restricted to retrospective simulation')
    if type(query.get('watermark')) is not int or query['watermark'] < 0:
        raise ValueError('Host publication watermark required')
    now = timestamp(query['now'])
    if len({x['id'] for x in experiences}) != len(experiences):
        raise ValueError('Duplicate experience version identity')
    if len({x['model'] for x in models}) != len(models):
        raise ValueError('Duplicate model capability identity')
    parent = next((m for m in models if m['model'] == query['parent_model']), None)
    if not parent or parent.get('rate_scenario') != query['rate_scenario']:
        raise ValueError('Matched parent rate scenario is required')
    parent_cost = number(parent['unit_cost'], 'parent relative cost', 0)
    if parent_cost <= 0 or parent.get('account_hash') != query['account_hash']:
        raise ValueError('Positive same-source parent cost reference required')
    excluded, candidate_rows = [], []
    for model in sorted(models, key=lambda m: m['model']):
        reason = None
        if model['model'] == query['parent_model']:
            continue
        cost = number(model['unit_cost'], 'candidate relative cost')
        if model.get('account_hash') != query['account_hash']:
            reason = 'different_source_account'
        elif model.get('available') is not True or model.get('qualified') is not True:
            reason = 'not_available_and_qualified'
        elif timestamp(model['checked_at']) > now or timestamp(model['expires_at']) <= now:
            reason = 'capability_receipt_expired_or_future'
        elif model.get('rate_scenario') != query['rate_scenario'] or cost >= parent_cost:
            reason = 'not_cheaper_under_frozen_scenario'
        elif not set(query.get('required_capabilities', [])).issubset(model.get('capabilities', [])):
            reason = 'unsupported_capability'
        if reason:
            excluded.append({'model': model['model'], 'reason': reason})
            continue
        rows, rejected, guides, conflicts = [], [], {}, set()
        for e in experiences:
            why = None
            own_history = e.get('model') == model['model']
            if not own_history and (policy.evidence_profile == 'whole_task_proxy' or not e.get('guidance')):
                continue
            if any(e.get(k) != query[k] for k in ('project', 'study', 'arm', 'account_hash')):
                why = 'scope'
            elif e.get('visibility') != 'runtime_public' or e.get('verified') is not True:
                why = 'unverified_or_private'
            elif e.get('source_current') is not True or not e.get('verification_ref'):
                why = 'stale_source_or_missing_check'
            elif e.get('outcome') not in ('pass', 'fail'):
                why = 'unresolved_outcome'
            elif policy.evidence_profile == 'subtask_v2' and (e.get('granularity') != 'subtask' or e.get('subtask_type') != query['subtask_type']):
                why = 'different_subtask_type_or_granularity'
            elif e.get('task_id') in {query['task_id'], *query.get('excluded_task_ids', [])}:
                why = 'same_or_excluded_task'
            elif set(e.get('leakage_groups', [])) & set(query.get('excluded_leakage_groups', [])):
                why = 'excluded_lineage'
            elif e.get('language') and query.get('language') and e['language'] != query['language']:
                why = 'language'
            elif e.get('framework') and e['framework'] != query.get('framework'):
                why = 'framework'
            elif type(e.get('available_sequence')) is not int or not 0 <= e['available_sequence'] <= query['watermark']:
                why = 'publication_watermark'
            if why:
                rejected.append({'id': e['id'], 'reason': why})
                continue
            occurred, verified, published = (timestamp(e[k]) for k in ('occurred_at', 'verified_at', 'available_at'))
            if occurred > verified or verified > published or published > now:
                rejected.append({'id': e['id'], 'reason': 'future_or_invalid_chronology'})
                continue
            # Age is from the actual execution/check, never the latest import time.
            age = (now - verified).total_seconds() / 86400
            if age > policy.maximum_age_days:
                rejected.append({'id': e['id'], 'reason': 'beyond_maximum_age'})
                continue
            score = similarity(query, e, policy.evidence_profile)
            if score < policy.minimum_similarity:
                rejected.append({'id': e['id'], 'reason': 'low_similarity'})
                continue
            decay = 2 ** (-age / policy.half_life_days) if policy.mode == 'similarity_recency' else 1.0
            if policy.evidence_profile == 'subtask_v2':
                guidance = applicable_guidance(e, query, model['model'])
                if guidance:
                    key = guidance['id']
                    intrinsic = lambda g: {k: v for k, v in g.items() if k != 'source_experience_id'}
                    if key in guides and intrinsic(guides[key]) != intrinsic(guidance):
                        conflicts.add(key)
                    elif key not in guides:
                        guides[key] = guidance
                if not own_history:
                    continue  # teacher examples can ground a worker, not prove its competence
                if e.get('outcome_target') != 'public_integrated_completion':
                    rejected.append({'id': e['id'], 'reason': 'not_verified_integrated_subtask_completion'})
                    continue
                if e.get('executor_model') != model['model'] or e.get('assistance') not in ('none', 'retrieved_guidance'):
                    rejected.append({'id': e['id'], 'reason': 'not_attributed_small_model_execution'})
                    continue
                if e.get('assistance') == 'retrieved_guidance' and (not string_list(e.get('guidance_used_ids'), nonempty=True) or not e.get('guidance_context_ref')):
                    rejected.append({'id': e['id'], 'reason': 'guided_outcome_without_versioned_context'})
                    continue
            rows.append({'id': e['id'], 'task_id': e['task_id'], 'similarity': score,
                         'age_days': age, 'recency_weight': decay, 'weight': score * decay,
                         'outcome': e['outcome'], 'verification_ref': e['verification_ref'],
                         'assistance': e.get('assistance', 'whole_task_proxy'),
                         'guidance_context_ref': e.get('guidance_context_ref'),
                         'guidance_used_ids': e.get('guidance_used_ids', [])})
        guides = {k: g for k, g in guides.items() if k not in conflicts}
        supported = []
        for row in rows:
            if policy.evidence_profile == 'subtask_v2' and row['assistance'] == 'retrieved_guidance' and not set(row['guidance_used_ids']).issubset(guides):
                if row['outcome'] == 'pass':
                    rejected.append({'id': row['id'], 'reason': 'matching_grounding_missing_in_current_snapshot'})
                else:
                    # Missing old instructions must not erase a known model failure.
                    row['guidance_context_unavailable'] = True
                    supported.append(row)
            else:
                supported.append(row)
        rows = supported
        parents = {}
        for row in rows:
            parents.setdefault(row['task_id'], []).append(row)
        # A correlated parent contributes once. Any relevant known failure makes
        # that parent's observation a failure; repeated successes cannot swamp it.
        observations = [{'task_id': key, 'weight': max(r['weight'] for r in values),
                         'passed': all(r['outcome'] == 'pass' for r in values)}
                        for key, values in sorted(parents.items())]
        support = sum(x['weight'] for x in observations)
        success = (1 + sum(x['weight'] for x in observations if x['passed'])) / (2 + support)
        qualifies = (len(parents) >= policy.minimum_parents and support >= policy.minimum_weight
                     and success >= policy.minimum_success_estimate)
        if policy.mode == 'always_cheap':
            qualifies = True
        candidate = {'model': model['model'], 'unit_cost': cost, 'qualifies': qualifies,
                               'independent_parents': len(parents), 'weighted_support': support,
                               'descriptive_success_estimate': success, 'evidence': sorted(rows, key=lambda r: (-r['weight'], r['id'])),
                               'required_guidance_ids': sorted({g for row in rows if row['assistance'] == 'retrieved_guidance' and row['outcome'] == 'pass' and policy.mode != 'always_cheap' for g in row['guidance_used_ids']}),
                               'guidance': [guides[k] for k in sorted(guides)],
                               'independent_execution_parents': len({r['task_id'] for r in rows if r['assistance'] == 'none'}),
                               'guided_execution_parents': len({r['task_id'] for r in rows if r['assistance'] == 'retrieved_guidance'}),
                               'independent_successful_parents': len({key for key, values in parents.items() if all(r['outcome'] == 'pass' for r in values) and any(r['assistance'] == 'none' for r in values)}),
                               'guided_successful_parents': len({key for key, values in parents.items() if all(r['outcome'] == 'pass' for r in values) and any(r['assistance'] == 'retrieved_guidance' for r in values)}),
                               'failed_parents': sum(not x['passed'] for x in observations),
                               'guided_trial_available': bool(guides) and not any(r['outcome'] == 'pass' for r in rows),
                               'rejected': rejected}
        grounding_packet = build_packet(candidate, experiences, policy.maximum_packet_bytes)
        candidate['grounding_fits_packet'] = grounding_packet['fits_required']
        if policy.evidence_profile == 'subtask_v2' and not grounding_packet['fits_required']:
            candidate['qualifies'] = False
        candidate_rows.append(candidate)
    eligible = sorted((c for c in candidate_rows if c['qualifies']), key=lambda c: (c['unit_cost'], -c['weighted_support'], c['model']))
    chosen = eligible[0] if eligible else None
    decision = {'schema_version': 1, 'policy': asdict(policy), 'query_hash': digest(query),
                'evidence_snapshot_hash': digest(experiences), 'capability_snapshot_hash': digest(models),
                'as_of': query['now'], 'status': 'delegate' if chosen else 'needs_parent',
                'selected_model': chosen['model'] if chosen else None, 'candidates': candidate_rows,
                'excluded_models': excluded, 'automatic_large_fallback': False,
                'score_interpretation': 'descriptive weighted prior outcomes, not calibrated success probability'}
    decision['decision_id'] = digest(decision)
    return decision


def packet(decision, experiences, maximum_bytes):
    """Bounded evidence for worker autonomy; no invented summaries or model call."""
    by_id = {e['id']: e for e in experiences}
    candidate = next((c for c in decision['candidates'] if c['model'] == decision['selected_model']), None)
    if decision['policy'].get('evidence_profile') == 'subtask_v2':
        return build_packet(candidate or {'evidence': []}, experiences, maximum_bytes)
    items, used = [], 2
    if candidate:
        import json
        # Keep worker packet order fixed across age ablations: v1 measures age's
        # admission effect, not an unregistered simultaneous prompt-order change.
        for row in sorted(candidate['evidence'], key=lambda r: (-r['similarity'], r['id'])):
            e = by_id[row['id']]
            item = {k: e[k] for k in ('id', 'goal', 'outcome', 'verification_ref')}
            item.update(procedure=e.get('procedure', []), age_days=row['age_days'], similarity=row['similarity'])
            size = len(json.dumps(item, ensure_ascii=False).encode()) + 1
            if used + size <= maximum_bytes:
                items.append(item)
                used += size
    return {'experiences': items, 'bytes_upper_bound': used, 'limit_bytes': maximum_bytes}
