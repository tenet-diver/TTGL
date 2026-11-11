#!/usr/bin/env python3
"""Registered isolated Commit0 units with native Codex orchestration.

No work allocation or custom agents. Preparation, live inference and independent
source-only replay are distinct commands. Started units never run twice.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import selectors
import shutil
import subprocess
import time

from codex_team_probe import save, sha
from commit0_team_controls import IMAGE
from mcp_memory_probe import Client
from tokeneconomizer_native_hooks import toml

HERE = Path(__file__).resolve().parent
DOCKER = ['docker', '--host=unix:///var/run/docker.sock']


def docker(args, **kwargs):
    env = {k: v for k, v in os.environ.items() if k not in ('DOCKER_HOST','DOCKER_CONTEXT','DOCKER_TLS','DOCKER_TLS_VERIFY','DOCKER_CERT_PATH')}
    return subprocess.run(DOCKER + args, env=env, **kwargs)


def prepare(root, source_manifest, runtime, total, condition, minutes, budget, memory_entry, task, kind, token_limit):
    if total not in (1,2,4,8) or condition not in ('native','notebook','mcp_memory'):
        raise ValueError('Unregistered capacity/condition')
    root.mkdir(parents=True, exist_ok=False)
    entries = json.loads(source_manifest.read_text())
    if task not in ('tinydb', 'simpy'):
        raise ValueError('Task requires separately passing controls and registration')
    entry = next(e for e in entries if e['name'] == task and e['phase'] == 'base')
    relative = 'tinydb' if task == 'tinydb' else 'src/simpy'
    source = Path(entry['source'])
    if any(sha(source / rel) != value for rel,value in entry['hashes'].items()):
        raise ValueError('Base source changed')
    actor, home = root / 'actor', root / 'home'
    shutil.copytree(source, actor)
    if (actor / '.git').exists():
        raise ValueError('Repository history not allowed')
    home.mkdir(mode=0o700)
    cli = Path(shutil.which('codex')).resolve()
    config = {
        'model_provider':'ttgl-study', 'model':'gpt-6.1-sol','model_reasoning_effort':'low',
        'model_providers.ttgl-study.name':'OpenAI study capture',
        'model_providers.ttgl-study.base_url':'http://127.0.0.1:8452/backend-api/codex',
        'model_providers.ttgl-study.wire_api':'responses',
        'model_providers.ttgl-study.requires_openai_auth':True,
        'model_providers.ttgl-study.request_max_retries':0,
        'model_providers.ttgl-study.stream_max_retries':0,
        'model_providers.ttgl-study.supports_websockets':False,
        'project_doc_max_bytes':0,'allow_login_shell':False,'web_search':'disabled',
        'features.skip_host_skill_discovery':True,'features.enable_request_compression':False,
        'features.multi_agent':total>1,'features.multi_agent_v2':False,'agents.enabled':total>1,
        'agents.max_depth':1,'agents.default_subagent_model':'gpt-6.1-sol',
        'agents.default_subagent_reasoning_effort':'low',
        'default_permissions':'team_coding',
        'permissions.team_coding.filesystem':{':root':'deny',':minimal':'read',str(actor):'read',str(cli):'read'},
        'permissions.team_coding.network.enabled':False,
        'shell_environment_policy.inherit':'none',
        'shell_environment_policy.set':{'PATH':'/usr/bin:/bin','HOME':str(actor)},
        'mcp_servers.repository.command':shutil.which('python'),
        'mcp_servers.repository.args':[str(HERE/'codex_team_terminal.py'),'--config',str(root/'terminal.json')],
        'mcp_servers.repository.required':True,'mcp_servers.repository.startup_timeout_sec':30,
        'mcp_servers.repository.tool_timeout_sec':210,
        'mcp_servers.repository.tools.terminal.approval_mode':'approve',
    }
    if total>1:
        config['agents.max_concurrent_threads_per_session']=total-1
    for feature in ('memories','plugins','apps','browser_use','computer_use','image_generation',
                    'workspace_dependencies','goals','hooks','shell_tool','unified_exec','apply_patch_freeform'):
        config['features.'+feature]=False
    knowledge=''
    if condition=='notebook':
        (actor/'KNOWLEDGE.md').write_text('# Shared project knowledge\n\nRecord source paths, observed checks, revisions and uncertainty here.\n')
        knowledge='Use /task/KNOWLEDGE.md as a shared notebook for reusable findings, interface agreements and checked procedures. Keep the evidence and uncertainty attached; recheck facts after relevant source changes. '
    if condition=='mcp_memory':
        if not memory_entry or not memory_entry.is_file():
            raise ValueError('Reviewed official memory entry required')
        (root/'memory').mkdir()
        config.update({'mcp_servers.team_memory.command':str(Path(shutil.which('node')).resolve()),
            'mcp_servers.team_memory.args':[str(memory_entry.resolve())],
            'mcp_servers.team_memory.env':{'MEMORY_FILE_PATH':str(root/'memory/knowledge.jsonl')},
            'mcp_servers.team_memory.required':True,'mcp_servers.team_memory.tool_timeout_sec':60})
        for name in ('create_entities','create_relations','add_observations','delete_entities','delete_observations','delete_relations','read_graph','search_nodes','open_nodes'):
            config['mcp_servers.team_memory.tools.'+name+'.approval_mode']='approve'
        knowledge='Use the team_memory MCP tools as shared project knowledge for reusable findings, interface agreements and checked procedures. Keep source references and uncertainty attached; recheck facts after relevant source changes. '
    instruction=(
        f'Implement the missing {task} library behavior in the provided repository skeleton. '
        'Use the public source docstrings, documentation and tests as the specification. '
        'The repository is /task inside the repository terminal tool. All reading, editing and testing must use that tool. '
        'Python and reviewed test dependencies are already installed: run python3 -m pytest -p no:cacheprovider -q tests/. '
        'Do not install packages, access the network, fetch an existing implementation or inspect external repositories. '
        f'Only changes under /task/{relative}/ are submitted; tests, harness and dependency changes are not submitted. '
        'Use general implementations rather than hardcoding test answers. Verify your integrated implementation before finishing. '
        f'The total concurrent agent capacity is {total}, including you. '
        + ('Do not delegate. ' if total==1 else 'Use native default subagents when useful, up to the capacity. Do not change worker models or nest delegation. Assign clear ownership, communicate interface dependencies and integrate and verify the final result. All workers share this repository. ')
        +knowledge+f'The whole team has {minutes} minutes and {budget} total terminal calls, including checks. '
        'Report what is implemented, the exact checks run, their outcomes and remaining gaps. Do not claim unobserved success.')
    (root/'prompt.txt').write_text(instruction)
    save(root/'config.json',config)
    files=[Path(__file__),HERE/'codex_team_terminal.py',HERE/'codex_team_probe.py',HERE/'mcp_memory_probe.py',HERE/'tokeneconomizer_native_hooks.py',cli,root/'config.json',root/'prompt.txt']
    if memory_entry:
        files.append(memory_entry)
    save(root/'manifest.json',dict(created_at=datetime.now(timezone.utc).isoformat(),
        kind=kind,task='commit-0/'+task,src_dir=relative,condition=condition,
        total_agent_capacity=total,model='gpt-6.1-sol',effort='low',minutes=minutes,tool_budget=budget,
        observed_token_stop_threshold=token_limit,token_threshold_overshoot='In-flight native requests and auxiliary compaction can exceed threshold; full usage retained',
        sources={str(p.resolve()):sha(p) for p in files},base=entry,
        source_manifest=str(source_manifest.resolve()),runtime=str(runtime.resolve()),image=IMAGE,
        private_capture='/tmp/ttgl-team-knowledge-20261110/native-capture-001',
        automatic_assignment_retries=0,provider_request_retries=0,provider_stream_retries=0,
        notes='Codex native orchestration; constrained common terminal profile. No claim of unmodified product defaults.'))


def preflight(root):
    m=json.loads((root/'manifest.json').read_text())
    name='ttgl-team-'+root.name
    cmd=['run','--rm','-d','--name',name,'--network=none','--read-only','--cap-drop=ALL',
        '--security-opt=no-new-privileges','--user','1000:1000','--pids-limit','128','--memory','768m','--cpus','2',
        '--tmpfs','/tmp:rw,noexec,nosuid,size=128m','--mount',f'type=bind,src={root/"actor"},dst=/task',
        '--mount',f'type=bind,src={m["runtime"]},dst=/runtime,readonly',
        '--env','PYTHONPATH=/runtime:/task','--env','PYTHONDONTWRITEBYTECODE=1',
        '--env','COVERAGE_FILE=/tmp/.coverage','--env','HTTP_PROXY=','--env','HTTPS_PROXY=','--env','ALL_PROXY=',
        '--workdir','/task',m['image'],'sleep','7200']
    save(root/'container-intent.json',dict(command=DOCKER+cmd,model_calls=0))
    process=docker(cmd,capture_output=True,text=True,timeout=30)
    if process.returncode:
        raise RuntimeError(process.stderr)
    save(root/'container.json',dict(name=name,id=process.stdout.strip()))
    check=docker(['exec',name,'python3','-c',
        "import pathlib,socket,pytest; assert not pathlib.Path('/var/run/docker.sock').exists(); assert not pathlib.Path('/workspaces/TTGL').exists(); p=pathlib.Path('/task/.boundary-witness');p.write_text('write-ok');assert p.read_text()=='write-ok';p.unlink();s=socket.socket();s.settimeout(1);assert s.connect_ex(('1.1.1.1',443))!=0;print('fixed container boundary and writable source passed')"],capture_output=True,text=True,timeout=15)
    save(root/'container-boundary.json',dict(exit_code=check.returncode,stdout=check.stdout,stderr=check.stderr,passed=check.returncode==0,model_calls=0))
    if check.returncode:
        raise RuntimeError('Container boundary check failed')
    config=json.loads((root/'config.json').read_text())
    native=['codex','sandbox','-P','team_coding','-C',str(root/'actor')]
    for key,value in config.items():
        native+=['-c',key+'='+toml(value)]
    import shlex
    native+=['--','/bin/sh','-c',
        'test -r '+shlex.quote(m.get('src_dir','tinydb')+'/__init__.py')+' || exit 41\n'
        'if cat '+shlex.quote(str(root/'manifest.json'))+' >/dev/null 2>&1; then exit 42; fi\n'
        'if touch .host-write-witness 2>/dev/null; then exit 43; fi']
    check=subprocess.run(native,env={**os.environ,'CODEX_HOME':str(root/'home')},capture_output=True,text=True,timeout=30)
    save(root/'native-boundary.json',dict(command=native,exit_code=check.returncode,stdout=check.stdout,stderr=check.stderr,passed=check.returncode==0,model_calls=0))
    if check.returncode:
        raise RuntimeError('Native boundary/configuration check failed')


def run(root):
    m=json.loads((root/'manifest.json').read_text())
    if not json.loads((root/'container-boundary.json').read_text())['passed']:
        raise ValueError('Passing boundary required')
    if not json.loads((root/'native-boundary.json').read_text())['passed']:
        raise ValueError('Passing native boundary required')
    for file,value in m['sources'].items():
        if sha(file)!=value:
            raise ValueError('Frozen source changed: '+file)
    save(root/'started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),retries=0))
    save(root/'terminal.json',dict(records=str(root/'tool-records'),container=json.loads((root/'container.json').read_text())['name'],
        tool_budget=m['tool_budget'],close_at_ns=time.time_ns()+int(m['minutes']*60*1e9)))
    auth=Path(os.environ.get('CODEX_HOME',str(Path.home()/'.codex')))/'auth.json'
    shutil.copyfile(auth,root/'home/auth.json');(root/'home/auth.json').chmod(0o600)
    cmd=['codex','app-server','--listen','stdio://']
    for key,value in json.loads((root/'config.json').read_text()).items():
        cmd+=['-c',key+'='+toml(value)]
    save(root/'process-intent.json',dict(command=cmd))
    c=Client.__new__(Client)
    c.err=(root/'stderr.log').open('x')
    c.p=subprocess.Popen(cmd,env={**os.environ,'CODEX_HOME':str(root/'home')},stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=c.err,start_new_session=True)
    c.selector=selectors.DefaultSelector();c.selector.register(c.p.stdout,selectors.EVENT_READ)
    c.buffer,c.ident,c.calls=b'',0,[];c.journal=(root/'rpc.jsonl').open('x')
    start=time.perf_counter();counts={}
    try:
        c.request('initialize',dict(clientInfo=dict(name='ttgl_native_team_coding',version='1'),capabilities=dict(experimentalApi=True)))
        c.p.stdin.write(b'{"method":"initialized","params":{}}\n');c.p.stdin.flush()
        thread=c.request('thread/start',dict(cwd=str(root/'actor'),model=m['model'],modelProvider='ttgl-study',approvalPolicy='never',ephemeral=False))
        save(root/'thread.json',thread);sid=thread['thread']['id']
        save(root/'turn-intent.json',dict(thread_id=sid,at=datetime.now(timezone.utc).isoformat()))
        accepted=c.request('turn/start',dict(threadId=sid,input=[dict(type='text',text=(root/'prompt.txt').read_text(),text_elements=[])]))
        save(root/'accepted.json',accepted)
        deadline=time.monotonic()+m['minutes']*60
        while time.monotonic()<deadline:
            if b'\n' not in c.buffer:
                if not c.selector.select(1):continue
                chunk=os.read(c.p.stdout.fileno(),65536)
                if not chunk:raise RuntimeError('App-server exited; do not retry')
                c.buffer+=chunk;continue
            line,c.buffer=c.buffer.split(b'\n',1)
            if not line.strip():continue
            row=json.loads(line);c.record(dict(direction='notification',message=row));p=row.get('params',{})
            if row.get('method')=='thread/tokenUsage/updated':
                counts[p['threadId']]=p['tokenUsage']['total']['totalTokens']
                if sum(counts.values())>=m['observed_token_stop_threshold']:
                    raise RuntimeError('Observed team token threshold reached; no retry')
            if row.get('method')=='turn/completed' and p.get('threadId')==sid:
                save(root/'completed.json',dict(turn=p['turn'],parent_thread_id=sid,wall_seconds=time.perf_counter()-start,independent_grade_pending=True));return
        raise TimeoutError('Team deadline reached; preserve and grade current artifact')
    except BaseException as error:
        save(root/'stopped.json',dict(error=repr(error),wall_seconds=time.perf_counter()-start,outcome='requires_audit',no_retry=True));raise
    finally:
        c.close()


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','preflight','run']);p.add_argument('--root',type=Path,required=True)
    p.add_argument('--source-manifest',type=Path);p.add_argument('--runtime',type=Path);p.add_argument('--total',type=int,default=1)
    p.add_argument('--condition',default='native');p.add_argument('--minutes',type=int,default=30);p.add_argument('--tool-budget',type=int,default=80);p.add_argument('--memory-entry',type=Path)
    p.add_argument('--task',default='tinydb',choices=['tinydb','simpy'])
    p.add_argument('--kind',default='development_feasibility_not_main_comparison')
    p.add_argument('--token-limit',type=int,default=2000000)
    a=p.parse_args();os.umask(0o077);root=a.root.resolve()
    if a.action=='prepare':prepare(root,a.source_manifest,a.runtime,a.total,a.condition,a.minutes,a.tool_budget,a.memory_entry,a.task,a.kind,a.token_limit)
    elif a.action=='preflight':preflight(root)
    else:run(root)
