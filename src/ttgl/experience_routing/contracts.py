"""Use the maintained JSON Schema validator over the web contract export."""
from __future__ import annotations
from pathlib import Path
import json

ROOT = Path(__file__).resolve().parents[3]
SCHEMAS = ROOT / 'experiments/experience-routing-001/contracts.schema.json'


def validate(kind, value):
    from jsonschema import Draft202012Validator
    schema = json.loads(SCHEMAS.read_text())[kind]
    errors = sorted(Draft202012Validator(schema).iter_errors(value), key=lambda e: str(e.path))
    if errors:
        raise ValueError('Invalid ' + kind + ': ' + '; '.join(e.message for e in errors[:5]))
    if kind == 'plan':
        validate_plan(value)
    if kind == 'verification' and len({c['criterionId'] for c in value['criterionResults']}) != len(value['criterionResults']):raise ValueError('Duplicate verification criterion')
    if kind == 'verification' and value['verdict'] == 'pass':
        if not value['criterionResults'] or any(c['verdict'] != 'pass' for c in value['criterionResults']):
            raise ValueError('A passing verification requires nonempty passing criteria')
    return value


def validate_plan(plan):
    nodes = {n['nodeId']: n for n in plan['nodes']}
    if len(nodes) != len(plan['nodes']):
        raise ValueError('Duplicate node identity')
    visited, visiting = set(), set()

    def visit(key):
        if key in visiting:
            raise ValueError('Plan dependency cycle')
        if key in visited:
            return
        if key not in nodes or nodes[key]['planRevisionId'] != plan['planRevisionId']:
            raise ValueError('Unknown dependency or plan revision')
        node = nodes[key]
        if len({c['id'] for c in node['acceptanceCriteria']}) != len(node['acceptanceCriteria']):
            raise ValueError('Duplicate acceptance criterion')
        for value in node['allowedWritePaths']:
            p = Path(value)
            if p.is_absolute() or '..' in p.parts or '.git' in p.parts:
                raise ValueError('Invalid write scope')
        visiting.add(key)
        for dep in node['dependsOn']:
            visit(dep)
        visiting.remove(key)
        visited.add(key)

    for key in nodes:
        visit(key)
    return plan


def ready_nodes(plan, states):
    return [n for n in plan['nodes'] if states.get(n['nodeId'], 'pending') == 'pending'
            and all(states.get(d) == 'accepted' for d in n['dependsOn'])]


def outcome(public_criteria, complete, cancelled=False):
    """A transport completion or an isolated command failure is not task success."""
    if cancelled or not complete or not public_criteria:
        return 'abstain'
    states = [c.get('verdict') for c in public_criteria]
    return 'successful' if all(s == 'pass' for s in states) else 'unsuccessful' if 'fail' in states else 'abstain'
