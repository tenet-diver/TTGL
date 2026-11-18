"""Bounded, evidence-linked procedures; teacher knowledge is not student success."""
from __future__ import annotations
import json


def string_list(value, *, nonempty=False):
    return isinstance(value, list) and (bool(value) or not nonempty) and all(isinstance(x, str) and bool(x.strip()) for x in value)


def applicable_guidance(experience, query, model):
    g = experience.get('guidance')
    if not isinstance(g, dict) or g.get('supported') is not True or experience.get('outcome') != 'pass':
        return None
    if not isinstance(g.get('id'), str) or not g['id']:
        return None
    for key in ('procedure', 'acceptance_criteria', 'evidence_refs'):
        if not string_list(g.get(key), nonempty=True) or len(g[key]) > 16:
            return None
    if not string_list(g.get('preconditions')) or not string_list(g.get('target_models', [])):
        return None
    if g.get('target_models') and model not in g['target_models']:
        return None
    if not set(x.strip().casefold() for x in g['preconditions']).issubset(x.strip().casefold() for x in query.get('constraints', [])):
        return None
    # The procedure is attached to a supported source outcome, not just advice
    # labelled useful by an annotator. Its source executor stays visible.
    if not experience.get('executor_model') or g.get('source_model') != experience['executor_model']:
        return None
    if experience['verification_ref'] not in g['evidence_refs']:
        return None
    result = {key: g[key] for key in ('id', 'procedure', 'preconditions', 'acceptance_criteria', 'evidence_refs', 'source_model')}
    result['source_experience_id'] = experience['id']
    result['source_assistance'] = experience.get('assistance', 'unknown')
    return result


def build_packet(candidate, experiences, maximum_bytes):
    by_id = {e['id']: e for e in experiences}
    guides = {g['id']: g for g in candidate.get('guidance', [])}
    required = candidate.get('required_guidance_ids', [])
    content = {'guidance': [], 'experiences': []}
    size = lambda: len(json.dumps(content, ensure_ascii=False, sort_keys=True).encode())
    if size() > maximum_bytes:
        return {**content, 'bytes_upper_bound': size(), 'limit_bytes': maximum_bytes, 'fits_required': False}
    for key in required:
        if key not in guides:
            return {**content, 'bytes_upper_bound': size(), 'limit_bytes': maximum_bytes, 'fits_required': False}
        content['guidance'].append(guides[key])
        if size() > maximum_bytes:
            content['guidance'].pop()
            return {**content, 'bytes_upper_bound': size(), 'limit_bytes': maximum_bytes, 'fits_required': False}
    # Same order across age ablations: isolate admission from prompt reordering.
    for row in sorted(candidate['evidence'], key=lambda r: (-r['similarity'], r['id'])):
        e = by_id[row['id']]
        item = {k: e[k] for k in ('id', 'goal', 'outcome', 'verification_ref')}
        item.update(subtask_type=e.get('subtask_type'), executor_model=e.get('executor_model'),
                    assistance=e.get('assistance', 'unknown'), age_days=row['age_days'], similarity=row['similarity'])
        if row.get('guidance_context_unavailable'):
            item['guidance_context_unavailable'] = True
        if row.get('guidance_context_ref'):
            item['guidance_context_ref'] = row['guidance_context_ref']
        # An outcome is valid history even without a verified reusable procedure.
        # Do not promote arbitrary top-level procedure text into grounded advice.
        content['experiences'].append(item)
        if size() > maximum_bytes:
            content['experiences'].pop()
    for key in sorted(guides):
        if key in required:
            continue
        content['guidance'].append(guides[key])
        if size() > maximum_bytes:
            content['guidance'].pop()
    return {**content, 'bytes_upper_bound': size(), 'limit_bytes': maximum_bytes, 'fits_required': True}
