#!/usr/bin/env python3
"""Recorded continuation: preserve native cancellation gaps, never repeat jobs.

Generation, tool, replay and original accounting sources remain frozen. This
adds an explicit incomplete-cost classification and advances only unstarted
assignments. No cancelled model call is retried, estimated as zero, or hidden.
"""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

from codex_team_probe import save, sha
from codex_team_coding import preflight, run, docker
from codex_team_grade import grade, audit
from codex_team_queue import archive
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'observability'))
from capture_objects import read_capture, CaptureObjects


def classify(cell):
    initial=json.loads((cell/'usage-audit.json').read_text())
    manifest=json.loads((cell/'manifest.json').read_text())
    source=Path(manifest['private_capture']);retained=cell/'captures'
    store=CaptureObjects(retained/'capture-objects.sqlite');db=store.connect()
    unknown=[]
    try:
        for name in initial['unknown_http_receipts']:
            path=source/name;r=read_capture(path);original=json.loads(path.read_text())
            if r.get('request',{}).get('client_metadata',{}).get('thread_id') not in initial['threads']:
                raise ValueError('Unattributed request; do not guess')
            with db:
                for key in ('request','forwarded_request','response'):
                    if key in r and store.pack(r[key],db)!=original[key]:
                        raise ValueError('Capture retention mismatch')
            copied=retained/name
            if copied.exists():
                if copied.read_bytes()!=path.read_bytes():raise ValueError('Capture identity collision')
            else:copied.write_bytes(path.read_bytes())
            if read_capture(copied)!=r:raise ValueError('Capture roundtrip failed')
            usage=[e['response'].get('usage') for e in r.get('response',{}).get('sse_events',[]) if e.get('type')=='response.completed']
            unknown.append(dict(capture=name,response_ids=r.get('response_ids'),state=r.get('state'),http_status=r.get('status'),
                complete_response_usage=usage,total_cost=None,
                scope='Interrupted/failed transport, excluded from completed-response token totals; never zero'))
        pending=[]
        for path in (source/'pending').glob('*.json'):
            if (source/path.name).exists():continue
            r=read_capture(path)
            if r.get('request',{}).get('client_metadata',{}).get('thread_id') in initial['threads']:
                pending.append(dict(capture=path.name,total_cost=None,state='pending_without_final_receipt'))
        result=dict(at=datetime.now(timezone.utc).isoformat(),native_rpc_completed_responses_reconcile=True,
            accounting_complete=initial['complete'] and not pending,completed_response_usage=initial['usage'],
            total_inference_usage=initial['usage'] if initial['complete'] and not pending else None,
            unknown_requests=unknown,pending_requests=pending,interrupted_request_count=len(unknown)+len(pending),
            subscription_cash_expense=None,source_sha256=sha(Path(__file__)),
            limitation='Completed-response tokens are a lower bound when any transport has unknown usage. No total-cost comparison in those cells.')
        save(cell/'usage-classification-001.json',result);return result
    finally:db.close()


def finish(cell, assignment):
    classification=classify(cell)
    g=json.loads((cell/'independent-grade/result.json').read_text())
    a=json.loads((cell/'usage-audit.json').read_text())
    return dict(assignment,grade=g,usage=a['usage'],wall_seconds=a['runtime_seconds'],
        inference_accounting_complete=classification['accounting_complete'],
        unknown_inference_requests=classification['interrupted_request_count'],
        total_inference_usage=classification['total_inference_usage'])


def execute(root, protocol_path):
    protocol=json.loads(protocol_path.read_text())
    for path,value in protocol['frozen_sources'].items():
        if sha(path)!=value:raise ValueError('Frozen source changed: '+path)
    save(root/'continuation-001-started.json',dict(at=datetime.now(timezone.utc).isoformat(),protocol_sha256=sha(protocol_path),automatic_retries=0))
    first=json.loads((root/'checkpoint-001.json').read_text())['assignments'][0]
    first.update(inference_accounting_complete=True,unknown_inference_requests=0,total_inference_usage=first['usage'])
    rows=[first]
    # The second completed unit stopped the original queue. Grade and native
    # reconciliation already exist. Classify it without any model invocation.
    second=protocol['assignments'][1];cell=root/second['directory']
    if not (cell/'completed.json').exists() or not (cell/'usage-audit.json').exists():
        raise ValueError('Expected preserved second completion')
    rows.append(finish(cell,second))
    save(root/'checkpoint-002.json',dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows,amendment=protocol['id']))
    archive(cell)
    try:
        for assignment in protocol['assignments'][2:]:
            cell=root/assignment['directory']
            if (cell/'started.json').exists():raise ValueError('Started assignment must never repeat')
            if shutil.disk_usage(root).free<128*1024*1024:raise RuntimeError('Storage reserve reached before inference')
            preflight(cell)
            try:
                try:run(cell)
                except RuntimeError as error:
                    if str(error)!='Observed team token threshold reached; no retry':raise
            finally:
                name=json.loads((cell/'container.json').read_text())['name']
                stopped=docker(['stop','-t','2',name],capture_output=True,text=True,timeout=20)
                save(cell/'container-stopped.json',dict(exit_code=stopped.returncode,stdout=stopped.stdout,stderr=stopped.stderr))
                if stopped.returncode:raise RuntimeError('Artifact seal failed')
            grade(cell);audit(cell)
            rows.append(finish(cell,assignment))
            save(root/(f'checkpoint-{len(rows):03}.json'),dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows,amendment=protocol['id']))
            archive(cell)
            print(json.dumps(dict(completed=len(rows),last=rows[-1])),flush=True)
        save(root/'completion.json',dict(at=datetime.now(timezone.utc).isoformat(),assignments=rows,amendment=protocol['id']))
    except BaseException as error:
        save(root/'continuation-001-stopped.json',dict(at=datetime.now(timezone.utc).isoformat(),error=repr(error),completed=len(rows),automatic_retries=0))
        raise


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',type=Path,required=True);p.add_argument('--protocol',type=Path,required=True)
    a=p.parse_args();execute(a.root.resolve(),a.protocol.resolve())
