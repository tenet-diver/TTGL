#!/usr/bin/env python3
"""Opt-in Claude Code steering adapter and generic local hook client. Stdlib only.

Install edits only the selected settings file after writing a backup; it never
installs packages or changes model routing. Failures/timeouts are advisory fail-open.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shlex
import sys
import time
import urllib.error
import urllib.request
import uuid
from urllib.parse import urlparse

NAMES={'SessionStart':'start','UserPromptSubmit':'prompt','PreToolUse':'pre_tool','PostToolUse':'post_tool','PostToolUseFailure':'post_tool','Stop':'stop'}
MARK='TTGL_STEERING_HOOK=1'


def send(data,url,payload):
    parsed=urlparse(url)
    if parsed.scheme!='http' or parsed.hostname not in ('localhost','127.0.0.1') or parsed.username or parsed.password:raise ValueError('Hook URL must be loopback HTTP')
    token=(data/'steering-token').read_text().strip()
    request=urllib.request.Request(url.rstrip('/')+'/api/steering-hook',json.dumps(payload).encode(),{'Authorization':'Bearer '+token,'Content-Type':'application/json'})
    # Never forward this local token through a configured HTTP proxy.
    with urllib.request.build_opener(urllib.request.ProxyHandler({})).open(request,timeout=1.8) as response:return json.load(response)


def normalize(raw):
    if not isinstance(raw,dict):raise ValueError('Expected a hook object')
    if raw.get('event') in ('start','prompt','pre_tool','post_tool','stop'):return raw
    name=raw.get('hook_event_name');event=NAMES.get(name)
    if event is None:raise ValueError('Unsupported Claude hook')
    inputs=raw.get('tool_input') or {};tool=raw.get('tool_name','');command=inputs.get('command','') if isinstance(inputs,dict) else ''
    import re
    operation='edit' if tool in ('Edit','Write','MultiEdit','NotebookEdit') else 'check' if re.search(r'\b(pytest|unittest|jest|vitest|playwright|tsc|eslint|test|lint|check|build)\b',command) else 'other'
    # A pre/post pair shares the provider call ID, but represents two receipts.
    stable_id=hashlib.sha256(json.dumps([raw['session_id'],name,raw['tool_use_id']],separators=(',',':')).encode()).hexdigest() if raw.get('tool_use_id') else None
    payload={'event':event,'session_id':raw['session_id'],'event_id':raw.get('event_id') or stable_id or uuid.uuid4().hex,'workspace':raw.get('cwd',''),'tool':tool,'command':command[:8000],'input_hash':hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest(),'operation':operation}
    if event=='post_tool':payload['failed']=name=='PostToolUseFailure'
    if raw.get('task_id'):payload['task_id']=raw['task_id']
    if 'main_folder' not in raw:
        folder=Path(raw.get('cwd','.')).resolve()
        for parent in [folder,*folder.parents]:
            if (parent/'.git').exists():payload['main_folder']=(parent/'.git').is_dir();break
    for key in ('cost_usd','context_tokens','main_folder'):
        if key in raw:payload[key]=raw[key]
    return payload


def claude_result(raw,result):
    name=raw.get('hook_event_name');decision=result['decision'];message='\n'.join(result['messages'])
    if name=='PreToolUse':
        output={'hookEventName':name}
        if decision in ('ask','block'):output.update(permissionDecision='ask' if decision=='ask' else 'deny',permissionDecisionReason=message)
        elif message:output['additionalContext']=message
        return {'hookSpecificOutput':output}
    if name=='UserPromptSubmit' and decision in ('ask','block'):return {'decision':'block','reason':('Approval requested: ' if decision=='ask' else '')+message}
    if name in ('UserPromptSubmit','SessionStart','PostToolUse','PostToolUseFailure'):
        return {'hookSpecificOutput':{'hookEventName':name,'additionalContext':message}} if message else {}
    if name=='Stop':
        # Stop hook has no ask primitive. A note/block requests continued work;
        # stop_hook_active prevents endless retries if the agent cannot resolve it.
        if (decision in ('ask','block') or any(r.get('name')=='Session note' for r in result.get('rules',[]))) and not raw.get('stop_hook_active'):return {'decision':'block','reason':message}
        return {'systemMessage':message} if message else {}
    return result


def configure(settings,data,url,remove=False):
    old=json.loads(settings.read_text()) if settings.exists() else {}
    hooks=old.setdefault('hooks',{})
    if not isinstance(hooks,dict):raise ValueError('Invalid hook configuration')
    command=MARK+' '+shlex.join([sys.executable,str(Path(__file__).resolve()),'send','--data',str(data.resolve()),'--url',url])
    for name in NAMES:
        entries=hooks.get(name,[])
        if not isinstance(entries,list):raise ValueError('Invalid hook entries')
        clean=[]
        for entry in entries:
            if not isinstance(entry,dict):raise ValueError('Invalid hook entry')
            remaining=[h for h in entry.get('hooks',[]) if MARK not in str(h.get('command',''))]
            if remaining:clean.append({**entry,'hooks':remaining})
        if not remove:clean.append({'matcher':'*','hooks':[{'type':'command','command':command,'timeout':3}]})
        if clean:hooks[name]=clean
        else:hooks.pop(name,None)
    settings.parent.mkdir(parents=True,exist_ok=True)
    if settings.exists():
        backup=settings.with_name(settings.name+'.ttgl-backup-'+str(time.time_ns()));backup.write_bytes(settings.read_bytes());os.chmod(backup,0o600)
    temp=settings.with_name(settings.name+'.ttgl-tmp-'+uuid.uuid4().hex)
    fd=os.open(temp,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:f.write(json.dumps(old,indent=2)+'\n')
    os.replace(temp,settings)
    return {'installed':not remove,'settings':str(settings),'events':list(NAMES)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['send','install','uninstall','status'])
    parser.add_argument('--data',type=Path,required=True)
    parser.add_argument('--url',default='http://127.0.0.1:8766')
    parser.add_argument('--settings',type=Path,default=Path.home()/'.claude/settings.json')
    args=parser.parse_args()
    if args.action in ('install','uninstall'):
        if args.action=='install' and not (args.data/'steering-token').exists():parser.error('Start the workspace first to create its private token')
        print(json.dumps(configure(args.settings,args.data,args.url,args.action=='uninstall')));return
    if args.action=='status':
        settings=json.loads(args.settings.read_text()) if args.settings.exists() else {}
        print(json.dumps({'token_present':(args.data/'steering-token').exists(),'installed':MARK in json.dumps(settings),'url':args.url,'client':'Claude Code adapter; generic JSON send also supported. Codex hooks do not provide equivalent pre-tool enforcement.'}));return
    raw={}
    try:
        if os.environ.get('TTGL_HOOK_OFF')=='1':return
        content=sys.stdin.buffer.read(32769)
        if len(content)>32768:raise ValueError('Hook input too large')
        raw=json.loads(content);result=send(args.data,args.url,normalize(raw))
        print(json.dumps(claude_result(raw,result)))
    except (OSError,ValueError,KeyError,TypeError,urllib.error.URLError) as exc:
        # Never print credentials or hook input. Failure cannot trap the user's agent.
        print('Observatory advisory hook unavailable: '+type(exc).__name__,file=sys.stderr)


if __name__=='__main__':main()
