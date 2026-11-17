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
            if plan['previousRevisionId'] != previous.plan['planRevisionId']:
                raise ValueError('Replan must reference the prior revision')
            prior = {n['nodeId']: n for n in previous.plan['nodes']}
            for node in plan['nodes']:
                old = prior.get(node['nodeId'])
                if old and digest({k:v for k,v in node.items() if k!='planRevisionId'}) != digest({k:v for k,v in old.items() if k!='planRevisionId'}):
                    raise ValueError('A materially changed contract needs a new node ID')
                if old and previous.states[node['nodeId']] == 'accepted':
                    self.states[node['nodeId']] = 'accepted'
            self.attempts = dict(previous.attempts)
        self.revisions.append(plan)

    def ready(self):
        return ready_nodes(self.plan, self.states)

    def finish(self, node, attempt, accepted):
        self.attempts.setdefault(node, []).append(attempt)
        self.states[node] = 'accepted' if accepted else 'failed'
        if not accepted:
            changed = True
            while changed:
                changed = False
                for n in self.plan['nodes']:
                    if self.states[n['nodeId']] == 'pending' and any(self.states[d] in ('failed','blocked') for d in n['dependsOn']):
                        self.states[n['nodeId']] = 'blocked'; changed = True

    @property
    def completed(self):
        return all(v == 'accepted' for v in self.states.values())
