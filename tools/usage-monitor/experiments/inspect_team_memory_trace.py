#!/usr/bin/env python3
"""Deterministic visible-tool exposure counts; no model interpretation or grading.

Publication, nonempty search, original-record reads and known peer exposure are
separate. No claim of useful integration follows from these counts alone.
"""
import argparse
import hashlib
import json
from pathlib import Path
import tarfile


def decoded(item):
    value=item.get('result') or {}
    if isinstance(value.get('structuredContent'),dict):return value['structuredContent']
    for block in value.get('content',[]):
        if block.get('type')=='text':
            try:return json.loads(block['text'])
            except (ValueError,TypeError):continue
    return None


def hit_count(value):
    if isinstance(value,list):return len(value)
    if isinstance(value,dict):
        return sum(len(value[k]) for k in ('results','facts','episodes','entities') if isinstance(value.get(k),list))
    return 0


def inspect(root):
    if (root/'rpc.jsonl').exists():body=(root/'rpc.jsonl').read_bytes();origin='rpc.jsonl'
    else:
        archive=next(p for p in (root/'snapshot.tar.xz',root/'snapshot.tar.gz') if p.exists())
        with tarfile.open(archive) as t:body=t.extractfile('rpc.jsonl').read()
        origin=archive.name+':rpc.jsonl'
        expected=json.loads((root/'archive.json').read_text())['file_hashes']['rpc.jsonl']
        if hashlib.sha256(body).hexdigest()!=expected:raise ValueError('Archived trace bytes changed')
    items={};partial=False
    for line in body.split(b'\n'):
        if not line:continue
        try:message=json.loads(line).get('message',{})
        except ValueError:partial=True;continue
        p=message.get('params',{});item=p.get('item',{})
        if message.get('method')=='item/completed' and item.get('type')=='mcpToolCall' and item.get('server')=='team_memory':
            items[(p.get('threadId'),item.get('id'))]=item
    audit_path=root/'combined-usage-audit.json'
    native_threads={sid for sid,s in json.loads(audit_path.read_text())['sessions'].items() if s['model']=='gpt-6.1-sol'} if audit_path.exists() else set()
    publishers={};backend_publishers={};bythread={};reads=[];searches=[];errors=0
    for (thread,ident),item in items.items():
        result=decoded(item);tool=item.get('tool');bythread.setdefault(thread,[]).append(tool)
        if item.get('error') or (item.get('result') or {}).get('isError'):errors+=1
        if tool=='publish_finding' and isinstance(result,dict) and result.get('record_id'):
            publishers.setdefault(result['record_id'],set()).add(thread)
            created=result.get('backend_result') or {}
            if isinstance(created,dict):
                if created.get('node_id'):backend_publishers.setdefault(created['node_id'],set()).add(thread)
                for hit in created.get('results',[]):
                    if isinstance(hit,dict) and hit.get('id'):backend_publishers.setdefault(hit['id'],set()).add(thread)
    for (thread,ident),item in items.items():
        tool=item.get('tool');result=decoded(item)
        args=item.get('arguments') or {}
        if isinstance(args,str):
            try:args=json.loads(args)
            except ValueError:args={}
        if tool=='read_record' and isinstance(result,dict) and isinstance(result.get('body'),str):
            record=result.get('id') or args.get('id');authors=publishers.get(record,set())
            known_peer=bool(authors) and thread not in authors
            if not authors and result.get('author') in (native_threads or bythread.keys()) and result['author']!=thread:
                known_peer=True # Native auto-log author ID, not a self-reported publication label.
            reads.append(dict(thread=thread,item_id=ident,record_id=record,known_peer=known_peer,
                origin='publication' if authors else 'native-log' if result.get('author') in (native_threads or bythread.keys()) else 'unattributed',
                characters_exposed=len(result['body']),record_characters=result.get('characters')))
        if tool=='search_memory':
            hits=result.get('hits') if isinstance(result,dict) else None
            candidates=hits if isinstance(hits,list) else [r for key in ('results','episodes','facts') for r in hits.get(key,[]) ] if isinstance(hits,dict) else []
            peer=0
            for hit in candidates:
                if not isinstance(hit,dict):continue
                ident=hit.get('record_id') or hit.get('id')
                authors=publishers.get(ident,set()) or backend_publishers.get(ident,set()) or backend_publishers.get(hit.get('node_id'),set())
                if bool(authors) and thread not in authors:peer+=1
                elif not authors and hit.get('author') in (native_threads or bythread.keys()) and hit['author']!=thread:peer+=1
            searches.append(dict(thread=thread,item_id=item.get('id'),hits=hit_count(hits),known_peer_hits=peer,decoded=result is not None))
    return dict(interpretation_version=2,source=origin,source_sha256=hashlib.sha256(body).hexdigest(),partial_line_or_schema_gap=partial,
        completed_memory_calls=len(items),tools_by_thread=bythread,published_record_ids=len(publishers),
        completed_searches=len(searches),nonempty_searches=sum(s['hits']>0 for s in searches),searches=searches,
        known_peer_search_calls=sum(s['known_peer_hits']>0 for s in searches),
        original_record_reads=len(reads),known_peer_record_reads=sum(r['known_peer'] for r in reads),reads=reads,explicit_tool_errors=errors,
        limitation='Observable exposure only. Self-reported publication authors are mapped through native call threads; unlinked records remain unattributed. No causal or useful-action claim.')


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();value=inspect(a.root);a.output.write_text(json.dumps(value,indent=2)+'\n')
    print(json.dumps({k:value[k] for k in ('completed_memory_calls','published_record_ids','nonempty_searches','original_record_reads','known_peer_record_reads')}))
