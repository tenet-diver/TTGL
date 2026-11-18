from .contracts import validate, ready_nodes
from .io import digest


class PlanState:
    def __init__(self, plan, budget, previous=None):
        self.plan = validate('plan', plan)
        self.states = {n['nodeId']: 'pending' for n in plan['nodes']}
        self.attempts = {}
        self.budget = budget  # One shared parent budget; never reset on replan.
        self.revisions = list(previous.revisions) if previous else []
        if previous:
            if budget is not previous.budget:raise ValueError('A replan cannot replace its consumed parent budget')
            if plan['previousRevisionId'] != previous.plan['planRevisionId']:
                raise ValueError('Replan must reference the prior revision')
            if plan['taskInstanceId'] != previous.plan['taskInstanceId'] or plan['planRevisionId'] in {p['planRevisionId'] for p in previous.revisions}:
                raise ValueError('Replan must preserve parent identity and use a new revision')
            prior = {n['nodeId']: n for n in previous.plan['nodes']}
            current = {n['nodeId']: n for n in plan['nodes']}
            if any(previous.states[k] == 'accepted' and k not in current for k in prior):
                raise ValueError('Accepted dependencies cannot disappear during replan')
            original_criteria = {c['id'] for n in previous.plan['nodes'] for c in n['acceptanceCriteria']}
            if {c['id'] for n in plan['nodes'] for c in n['acceptanceCriteria']} != original_criteria:
                raise ValueError('Replan must preserve the complete public acceptance contract')
            if any(k not in prior for k in plan['cancelledNodeIds']) or any(k not in current or k not in prior for k in plan['continuedNodeIds']):
                raise ValueError('Replan lineage references an unknown node')
            for node in plan['nodes']:
                old = prior.get(node['nodeId'])
                if old and digest({k:v for k,v in node.items() if k!='planRevisionId'}) != digest({k:v for k,v in old.items() if k!='planRevisionId'}):
                    raise ValueError('A materially changed contract needs a new node ID')
                if any(k not in prior or previous.states[k] == 'accepted' for k in node['supersedesNodeIds']):
                    raise ValueError('Replacement must reference an unsuccessful prior node')
                if old:
                    self.states[node['nodeId']] = previous.states[node['nodeId']]
            self.attempts = dict(previous.attempts)
            if set(plan['cancelledNodeIds']) & set(plan['continuedNodeIds']):raise ValueError('A node cannot be continued and cancelled')
            for key in plan['cancelledNodeIds']:
                if previous.states[key]=='accepted':raise ValueError('Accepted work cannot be cancelled')
                if key in self.states:self.states[key]='cancelled'
        self._block_dependents()
        self.revisions.append(plan)

    def _block_dependents(self):
        changed=True
        while changed:
            changed=False
            for node in self.plan['nodes']:
                if self.states[node['nodeId']]=='pending' and any(self.states[d] in ('failed','blocked','cancelled','uncertain') for d in node['dependsOn']):
                    self.states[node['nodeId']]='blocked';changed=True

    def ready(self):
        return ready_nodes(self.plan, self.states)

    def finish(self, node, attempt, accepted):
        if node not in self.states or self.states[node] != 'pending':
            raise ValueError('Only a pending node may finish once')
        self.attempts.setdefault(node, []).append(attempt)
        self.states[node] = 'accepted' if accepted else 'failed'
        if not accepted:
            self._block_dependents()

    @property
    def completed(self):
        return all(v == 'accepted' for v in self.states.values())
