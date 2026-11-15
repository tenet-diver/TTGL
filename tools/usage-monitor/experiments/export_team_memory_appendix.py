#!/usr/bin/env python3
"""Export a fixed, reviewed set of pilot memory examples; no inference.

No reasoning, encrypted communications, arbitrary prompt dumps or credentials
are selected. Examples describe memory contents, not proven causal effects.
Original private archives remain unchanged; excerpts carry original source hashes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile


def digest(data):
    return hashlib.sha256(data).hexdigest()


def member(root, name):
    archive=root/'snapshot.tar.xz'
    recompression=json.loads((root/'recompression-001.json').read_text())
    # Verify against the exact output artifact, regardless of historical key name.
    if digest(archive.read_bytes()) not in json.dumps(recompression):
        raise ValueError('XZ artifact does not match its recompression receipt')
    with tarfile.open(archive) as tar:
        body=tar.extractfile(name).read()
    expected=json.loads((root/'archive.json').read_text())['file_hashes'][name]
    if digest(body)!=expected:
        raise ValueError('Original archived member changed')
    return body,dict(assignment=root.name,archive_sha256=digest(archive.read_bytes()),
                    member=name,member_sha256=digest(body))


def export(root, output):
    examples=[]
    body,source=member(root/'007-simpy-mcp_memory-4','memory/knowledge.jsonl')
    entities={e['name']:e for e in (json.loads(line) for line in body.split(b'\n') if line)}
    choices=[('ownership','simpy-implementation-ownership',0),
             ('interface_contract','simpy-utilities',1),
             ('claimed_check','simpy-utilities',3),
             ('failed_check_or_environment_caveat','simpy-utilities',6)]
    for label,name,index in choices:
        text=entities[name]['observations'][index]
        examples.append(dict(category=label,text=text,entity=name,observation_index=index,
            provenance=source,interpretation='Actual agent-authored publication. Check claims are self-reported here; this excerpt alone does not establish peer exposure, independent verification or causality.'))
    body,source=member(root/'006-tinydb-mcp_memory-2','rpc.jsonl')
    for line in body.split(b'\n'):
        if not line:continue
        message=json.loads(line).get('message',{})
        item=message.get('params',{}).get('item',{})
        if message.get('method')=='item/completed' and item.get('type')=='mcpToolCall' and item.get('server')=='team_memory' and item.get('tool')=='search_nodes':
            result=item['result']['structuredContent']
            if result!=dict(entities=[],relations=[]):raise ValueError('Expected preserved empty query')
            examples.append(dict(category='empty_retrieval',tool=item['tool'],arguments=item['arguments'],result=result,
                provenance=dict(source,item_id=item['id']),interpretation='A completed search returned no stored entities; this call supplies no peer-observation exposure.'))
            break
    else:raise ValueError('Expected query absent; do not replace with a favorable example')
    value=dict(kind='fixed qualitative pilot examples; not representative sampling or a mechanism effect estimate',
        selection='Predeclared source cells/entities/observation indices in exporter; includes failure and empty retrieval',
        privacy='Reviewed benchmark-only publications and one empty tool response. No raw private chat, reasoning or decoded communication.',
        examples=examples)
    with output.open('x') as stream:json.dump(value,stream,ensure_ascii=False,indent=2);stream.write('\n')
    return value


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--pilot-root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();result=export(a.pilot_root,a.output);print(json.dumps(dict(examples=len(result['examples']),model_calls=0)))
