#!/usr/bin/env python3
"""Temporal, conservative exact-observation exposure in official MCP memory.

No model calls. Successful tool replies supply the observations actually added
or returned; an entity name alone does not establish peer-text exposure.
"""
from collections import Counter
import hashlib
import json
from pathlib import Path
import tarfile

from inspect_team_memory_trace import decoded


def inspect_body(body,final_observations=None):
    authors={};announced=set();seen=set();tools=Counter();reads=[];published=0;errors=0
    for line in body.splitlines():
        message=json.loads(line).get('message',{});params=message.get('params',{});item=params.get('item',{})
        if message.get('method')!='item/completed' or item.get('type')!='mcpToolCall' or item.get('server')!='team_memory':continue
        identity=(params.get('threadId'),item.get('id'))
        if identity in seen:continue
        seen.add(identity);thread=identity[0];tool=item.get('tool');tools[tool]+=1
        value=decoded(item)
        if item.get('error') or (item.get('result') or {}).get('isError'):
            errors+=1;continue
        if tool=='create_entities' and isinstance(value,dict):
            for entity in value.get('entities',[]):
                for text in entity.get('observations',[]):
                    key=(entity['name'],text);authors.setdefault(key,set()).add(thread);announced.add(key);published+=1
        elif tool=='add_observations' and isinstance(value,dict):
            for row in value.get('results',[]):
                for text in row.get('addedObservations',[]):
                    key=(row['entityName'],text);authors.setdefault(key,set()).add(thread);announced.add(key);published+=1
        elif tool in ('search_nodes','open_nodes','read_graph') and isinstance(value,dict):
            peer=0;observations=0;entities=value.get('entities',[])
            for entity in entities:
                for text in entity.get('observations',[]):
                    observations+=1;owners=authors.get((entity['name'],text),set())
                    if owners and thread not in owners:peer+=1
            reads.append(dict(tool=tool,entities=len(entities),observations=observations,known_peer_observations=peer))
        elif tool in ('delete_entities','delete_observations'):
            # Deleted authorship is conservatively unavailable for later linkage.
            authors={}
    return dict(interpretation_version=1,completed_memory_calls=len(seen),tool_counts=dict(tools),
        returned_publication_observations=published,completed_read_queries=len(reads),
        unique_announced_observations=len(announced),
        sealed_observation_count=len(final_observations) if final_observations is not None else None,
        accepted_observations_absent_from_sealed_file=len(announced-final_observations) if final_observations is not None and not any(tools[k] for k in ('delete_entities','delete_observations')) else None,
        nonempty_read_queries=sum(r['entities']>0 for r in reads),
        queries_with_observations=sum(r['observations']>0 for r in reads),
        known_peer_read_queries=sum(r['known_peer_observations']>0 for r in reads),
        returned_known_peer_observation_occurrences=sum(r['known_peer_observations'] for r in reads),
        explicit_tool_errors=errors,
        limitation='Conservative exact returned-text linkage in chronological completed calls. No causal/useful-action claim; native/code/notebook channels remain separate.')


def inspect(cell):
    if (cell/'rpc.jsonl').exists():body=(cell/'rpc.jsonl').read_bytes()
    else:
        with tarfile.open(cell/'snapshot.tar.xz') as tar:body=tar.extractfile('rpc.jsonl').read()
        expected=json.loads((cell/'archive.json').read_text())['file_hashes']['rpc.jsonl']
        if hashlib.sha256(body).hexdigest()!=expected:raise ValueError('Archived RPC changed')
    member='memory/knowledge.jsonl';original=json.loads((cell/'archive.json').read_text())['file_hashes'] if (cell/'archive.json').exists() else {}
    path=cell/member;stored=None;store_hash=None
    if path.exists():store=path.read_bytes()
    elif member in original:
        with tarfile.open(cell/'snapshot.tar.xz') as tar:store=tar.extractfile(member).read()
    else:store=None
    if store is not None:
        store_hash=hashlib.sha256(store).hexdigest()
        if member in original and store_hash!=original[member]:raise ValueError('Sealed official memory changed')
        stored=set()
        for line in store.splitlines():
            entity=json.loads(line)
            if entity.get('type')=='entity':stored.update((entity['name'],text) for text in entity.get('observations',[]))
    return dict(source_sha256=hashlib.sha256(body).hexdigest(),sealed_store_sha256=store_hash,**inspect_body(body,stored))
