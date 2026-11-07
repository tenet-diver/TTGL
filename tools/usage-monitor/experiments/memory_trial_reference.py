"""Operator-only independent reference implementations for generated diagnostics.

Never copied into model work directories or memory. These are not gold patches
for an external benchmark and must not be used to claim official benchmark scores.
"""
import copy
import heapq


def normalize(events):
    seen={}
    for event in events:
        if event['id'] in seen and seen[event['id']]!=event:
            raise ValueError('conflicting event')
        seen.setdefault(event['id'], copy.deepcopy(event))
    return list(seen.values())


def balances(events):
    return reconcile(events,{})


def balances_at(events,cutoff):
    return reconcile(events,{},cutoff)


def reconcile(events,opening,cutoff=None):
    result=dict(opening)
    for e in normalize(events):
        if cutoff is None or e['timestamp']<=cutoff:
            result[e['account']]=result.get(e['account'],0)+e['delta']
    return result


def transfer(events,transfer_id,source,destination,amount,timestamp):
    if type(amount) is not int or amount<=0 or source==destination:
        raise ValueError('invalid transfer')
    return normalize(list(events)+[
        dict(id=transfer_id+':debit',account=source,delta=-amount,timestamp=timestamp),
        dict(id=transfer_id+':credit',account=destination,delta=amount,timestamp=timestamp)])


def statement(events,account):
    result=[];balance=0
    for e in sorted((e for e in normalize(events) if e['account']==account),key=lambda e:(e['timestamp'],e['id'])):
        balance+=e['delta']
        result.append(dict(id=e['id'],timestamp=e['timestamp'],delta=e['delta'],running_balance=balance))
    return result


def _graph(graph):
    return {n:set(graph.get(n,[])) for n in set(graph)|{d for deps in graph.values() for d in deps}}


def order(graph):
    edges=_graph(graph);result=[]
    while edges:
        available=[n for n,d in edges.items() if not d]
        if not available:raise ValueError('cycle')
        n=min(available);result.append(n);del edges[n]
        for d in edges.values():d.discard(n)
    return result


def affected(graph,changed):
    order(graph);selected=set(changed)
    while True:
        updated=selected|{n for n,deps in graph.items() if selected.intersection(deps)}
        if updated==selected:return sorted(selected)
        selected=updated


def plan(graph,changed):
    changed=set(affected(graph,changed))
    return [n for n in order(graph) if n in changed]


def layers(graph):
    edges=_graph(graph);result=[]
    while edges:
        ready=sorted(n for n,d in edges.items() if not d)
        if not ready:raise ValueError('cycle')
        result.append(ready)
        for n in ready:del edges[n]
        for d in edges.values():d.difference_update(ready)
    return result


def critical_path(graph,durations):
    costs={};edges=_graph(graph)
    for n in order(graph):
        value=durations.get(n,1)
        if type(value) is not int or value<0:raise ValueError('invalid duration')
        costs[n]=value+max((costs[d] for d in edges[n]),default=0)
    return max(costs.values(),default=0)
