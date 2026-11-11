#!/usr/bin/env python3
"""Reserved native-team extension: reuse frozen native run/boundary/transport code.

Only preparation generalizes admitted tasks and adds a registered knowledge-use
instruction factor. Native Codex still owns decomposition, delegation and integration.
"""
import argparse
from codex_team_coding import *

def prepare(root, source_manifest, runtime, total, condition, minutes, budget, memory_entry, task, kind, token_limit, guidance):
    if total not in (1,2,4,8) or condition not in ('native','mcp_memory'):
        raise ValueError('Unregistered capacity/condition')
    root.mkdir(parents=True, exist_ok=False)
    entries = json.loads(source_manifest.read_text())
    entry = next(e for e in entries if e['name'] == task and e['phase'] == 'base')
    control = json.loads(Path(entry['control_result']).read_text())
    if not control['reference_pass'] or control.get('original_source_changed'):
        raise ValueError('Independent reference gate must pass')
    relative = entry['src_dir'].rstrip('/')
    test_dir = entry['test_dir']
    for path in (relative, test_dir):
        if Path(path).is_absolute() or '..' in Path(path).parts:
            raise ValueError('Task path outside repository')
    test_command = 'python3 -m pytest -p no:cacheprovider -q ' + test_dir
    if guidance not in ('standard', 'explicit'):
        raise ValueError('Unregistered guidance')
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
        if guidance == 'explicit':
            knowledge += ('Use the common entity name "repository" (entity type "project") for cross-worker observations. '
                'Read it with open_nodes(names=["repository"]) before using shared findings; use create_entities if absent and add_observations to publish. '
                'Search is literal substring matching, so prefer opening this known entity to sentence-length searches. ')
    protocol = ''
    if guidance == 'explicit':
        protocol = ('Before dependent implementation, publish checked discoveries and interface commitments through the available team channels. '
            'Include source path, check result, relevant current-code identity and uncertainty; distinguish proposals from observations. '
            'Before changing a shared interface or integrating work, retrieve the latest peer findings relevant to it. '
            'Recheck a finding after a relevant source change, correct stale claims, and proceed independently when nothing relevant exists. '
            'The parent reviews worker findings and verifies the integrated source before finishing. ')

    instruction=(
        f'Implement the missing {task} library behavior in the provided repository skeleton. '
        'Use the public source docstrings, documentation and tests as the specification. '
        'The repository is /task inside the repository terminal tool. All reading, editing and testing must use that tool. '
        f'Python and reviewed test dependencies are already installed: run {test_command}. '
        'Do not install packages, access the network, fetch an existing implementation or inspect external repositories. '
        f'Only implementation changes under /task/{relative}/ are submitted; prescribed tests, fixed data, harness and dependencies are restored independently. '
        'Use general implementations rather than hardcoding test answers. Verify your integrated implementation before finishing. '
        f'The total concurrent agent capacity is {total}, including you. '
        + ('Do not delegate. ' if total==1 else 'Use native default subagents when useful, up to the capacity. Do not change worker models or nest delegation. Assign clear ownership, communicate interface dependencies and integrate and verify the final result. All workers share this repository. ')
        +protocol+knowledge+f'The whole team has {minutes} minutes and {budget} total terminal calls, including checks. '
        'Report what is implemented, the exact checks run, their outcomes and remaining gaps. Do not claim unobserved success.')
    (root/'prompt.txt').write_text(instruction)
    save(root/'config.json',config)
    files=[Path(__file__),HERE/'codex_team_coding.py',HERE/'codex_team_grade_v3.py',HERE/'codex_team_grade_v2.py',HERE/'codex_team_evidence.py',HERE/'commit0_compatibility_controls.py',HERE/'codex_team_terminal.py',HERE/'codex_team_probe.py',HERE/'mcp_memory_probe.py',HERE/'tokeneconomizer_native_hooks.py',source_manifest,cli,root/'config.json',root/'prompt.txt']
    if memory_entry:
        files.append(memory_entry)
    save(root/'manifest.json',dict(created_at=datetime.now(timezone.utc).isoformat(),
        kind=kind,task='commit-0/'+task,src_dir=relative,test_dir=test_dir,condition=condition,guidance=guidance,
        total_agent_capacity=total,model='gpt-6.1-sol',effort='low',minutes=minutes,tool_budget=budget,
        observed_token_stop_threshold=token_limit,token_threshold_overshoot='In-flight native requests and auxiliary compaction can exceed threshold; full usage retained',
        sources={str(p.resolve()):sha(p) for p in files},base=entry,
        source_manifest=str(source_manifest.resolve()),runtime=str(runtime.resolve()),image=IMAGE,
        private_capture='/tmp/ttgl-team-knowledge-20261110/native-capture-002',
        automatic_assignment_retries=0,provider_request_retries=0,provider_stream_retries=0,
        notes='Codex native orchestration; constrained common terminal profile. No claim of unmodified product defaults.'))


def preflight(root):
    m=json.loads((root/'manifest.json').read_text())
    name='ttgl-team-'+root.name
    cmd=['run','--rm','-d','--name',name,'--network=none','--read-only','--cap-drop=ALL',
        '--security-opt=no-new-privileges','--user','1000:1000','--pids-limit','128','--memory','2g','--cpus','2',
        '--tmpfs','/tmp:rw,nosuid,size=512m','--mount',f'type=bind,src={root/"actor"},dst=/task',
        '--mount',f'type=bind,src={m["runtime"]},dst=/runtime,readonly',
        '--env','PYTHONPATH=/runtime:/task/src:/task','--env','PYTHONDONTWRITEBYTECODE=1',
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


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('action',choices=['prepare','preflight','run'])
    p.add_argument('--root',type=Path,required=True)
    p.add_argument('--source-manifest',type=Path)
    p.add_argument('--runtime',type=Path)
    p.add_argument('--total',type=int,default=1)
    p.add_argument('--condition',choices=['native','mcp_memory'],default='native')
    p.add_argument('--guidance',choices=['standard','explicit'],default='standard')
    p.add_argument('--minutes',type=int,default=30)
    p.add_argument('--tool-budget',type=int,default=120)
    p.add_argument('--memory-entry',type=Path)
    p.add_argument('--task',required=True)
    p.add_argument('--kind',default='reserved_factoring_knowledge_protocol')
    p.add_argument('--token-limit',type=int,default=4000000)
    a=p.parse_args();os.umask(0o077);root=a.root.resolve()
    if a.action=='prepare':prepare(root,a.source_manifest,a.runtime,a.total,a.condition,a.minutes,a.tool_budget,a.memory_entry,a.task,a.kind,a.token_limit,a.guidance)
    elif a.action=='preflight':preflight(root)
    else:run(root)
