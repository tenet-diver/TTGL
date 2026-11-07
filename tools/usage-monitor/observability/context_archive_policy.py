"""Experimental tool-history policies, requiring a durable raw-source archive.

SQLite/native Codex already provide search/execution; Headroom provides the
existing lossless transforms. This module supplies only missing history-age and
exact-handle selection glue. It is NOT connected to the normal provider route.
Whole-history efficacy requires a separate actual request/recovery canary.
"""
import hashlib
import json
import time

POLICIES=('off','older-mask','reversible-handles')
RAW_MARKER='TTGL_RAW_EVIDENCE'
TEXT_KEYS={'output','aggregated_output','text','content','result','content_blocks'}


def rewrite(document,policy,retain_source=None,keep_last=4,minimum_characters=1000):
    """Only completed tool-output TEXT is eligible; never remove tool-call items.

    The callback must durably retain the exact source before returning. A
    callback error fails open for the entire request. Fixture tests prove the
    callback contract; live storage/retrieval must be independently verified.
    """
    if policy not in POLICIES:raise ValueError('Unknown experimental policy')
    if type(keep_last) is not int or keep_last<0:raise ValueError('Invalid retained output count')
    if type(minimum_characters) is not int or minimum_characters<256:raise ValueError('Invalid minimum size')
    started=time.perf_counter();changes=[]
    meta=dict(policy=policy,changes=changes,keep_last=keep_last,source_fidelity='exact source required by callback contract',
              not_a_live_efficacy_result=True)
    def finish(value,**extra):return value,dict(meta,elapsed_seconds=time.perf_counter()-started,**extra)
    if policy=='off':return finish(document,completed_outputs_present=None,passthrough_reason='policy disabled; no scan')
    if not isinstance(document,dict) or not isinstance(document.get('input'),list):
        return finish(document,completed_outputs_present=None,passthrough_reason='unsupported request envelope')
    if retain_source is None:return finish(document,passthrough_reason='durable archive callback unavailable')
    indices=[i for i,item in enumerate(document['input']) if isinstance(item,dict)
             and item.get('type') in ('custom_tool_call_output','function_call_output') and 'output' in item]
    selected=set(indices if policy=='reversible-handles' else indices[:-keep_last] if keep_last else indices)

    def text(value,path,call_id):
        if isinstance(value,str):
            if RAW_MARKER in value:return value
            # Only fully serialized JSON is descended into, retaining every
            # status, identifier, numeric field and unknown structural key.
            try:parsed=json.loads(value)
            except ValueError:parsed=None
            if isinstance(parsed,(dict,list)):
                before=len(changes);updated=text(parsed,path+['json'],call_id)
                return json.dumps(updated,ensure_ascii=False) if len(changes)>before else value
            if len(value)<minimum_characters:return value
            digest=hashlib.sha256(value.encode()).hexdigest()
            replacement=(f'[TTGL archived tool observation; mode={policy}; exact raw SHA256={digest}; '
                f'original UTF-8 bytes={len(value.encode())}. Retrieve the original with read_compression_source '
                'when any omitted detail is needed. This archive handle is not evidence that the tool succeeded.]')
            if len(replacement.encode())>=len(value.encode())*.8:return value
            retain_source(digest,value)
            changes.append(dict(call_id=call_id,path=path,source_sha256=digest,
                original_bytes=len(value.encode()),forwarded_bytes=len(replacement.encode()),
                representation='exact archive handle; original content removed from presentation'))
            return replacement
        if isinstance(value,list):return [text(v,path+[i],call_id) for i,v in enumerate(value)]
        if isinstance(value,dict):return {k:text(v,path+[k],call_id) if k in TEXT_KEYS else v for k,v in value.items()}
        return value

    try:
        items=[]
        for index,item in enumerate(document['input']):
            if index not in selected or RAW_MARKER in json.dumps(item.get('output'),ensure_ascii=False):
                items.append(item);continue
            items.append(dict(item,output=text(item['output'],['input',index,'output'],item.get('call_id'))))
    except Exception as exc:
        # Earlier successful archival writes may remain as unused evidence;
        # no partial transformed context or fabricated recovery is sent.
        meta['changes']=[]
        return finish(document,passthrough_reason=type(exc).__name__,completed_outputs_present=len(indices),
                      archived_fields_before_failure=len(changes))
    return finish(dict(document,input=items),completed_outputs_present=len(indices),selected_outputs=len(selected))
