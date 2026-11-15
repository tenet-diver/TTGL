#!/usr/bin/env python3
"""Inventory public study files and local Python imports without executing them.

No archives, credentials, private results, runtime binaries or model weights are
copied. Regenerate after final editorial changes; a manifest is not raw evidence.
"""
import argparse
import ast
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path
import subprocess


def build(repo,config_path,output):
    config=json.loads(config_path.read_text());roots=[repo/'tools/usage-monitor'/name for name in ['experiments','observability','langfuse']]
    listed=subprocess.check_output(['rg','--files',*[str(p) for p in roots]],text=True).splitlines()
    python=[Path(p).resolve() for p in listed if p.endswith('.py')]
    files={Path(p).resolve() for p in config['frozen_sources'] if str(p).startswith(str(repo/'tools')+'/')}
    here=Path(__file__).resolve().parent
    names=['finalize_team_memory_results.py','finish_team_memory_study.py','update_team_memory_paper.py',
        'plot_team_memory_extension.py','inspect_team_memory_trace.py','inspect_team_official_memory.py',
        'compact_team_memory_evidence.py','export_team_memory_appendix.py','build_team_memory_port_manifest.py']
    files.update(here/n for n in names)
    files.update(here.glob('test_team_memory_*.py'));files.update(here/n for n in ['test_team_official_memory.py','test_team_startup_transport.py','test_team_socket_guard.py'])
    files.update([repo/'tools/usage-monitor/observability/capture_proxy_native_routes.py'])
    ambiguous={};todo=list(files);visited=set()
    while todo:
        source=todo.pop()
        if source in visited or source.suffix!='.py':continue
        visited.add(source);tree=ast.parse(source.read_text());modules=[]
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):modules.extend(n.name for n in node.names)
            elif isinstance(node,ast.ImportFrom):
                if node.level:
                    base=source.parent
                    for _ in range(node.level-1):base=base.parent
                    if node.module:
                        direct=base.joinpath(*node.module.split('.')).with_suffix('.py')
                        if direct.is_file() and direct.is_relative_to(repo):files.add(direct);todo.append(direct)
                elif node.module:
                    modules.append(node.module)
                    modules.extend(node.module+'.'+n.name for n in node.names if n.name!='*')
        for module in modules:
            suffix=module.replace('.','/')
            matches=[p for p in python if str(p).endswith('/'+suffix+'.py') or str(p).endswith('/'+suffix+'/__init__.py')]
            nearby=[p for p in matches if p.parent==source.parent]
            if len(nearby)==1:matches=nearby
            if len(matches)>1:ambiguous[module]=[str(p.relative_to(repo)) for p in matches];continue
            if matches and matches[0] not in files:files.add(matches[0]);todo.append(matches[0])
    vendor=here/'smallville_vendor'
    files.update(p for p in vendor.rglob('*') if p.is_file() and '__pycache__' not in p.parts)
    files.add(repo/'tools/usage-monitor/config/defaults.json')
    for folder in [repo/'docs/paper/codex-team-knowledge',repo/'experiments/codex-team-knowledge-001']:
        files.update(p for p in folder.rglob('*') if p.is_file() and p.resolve()!=output.resolve())
    files.add(repo/'docs/research/team-memory-extension.md')
    rows=[]
    for path in sorted(files):
        path=path.resolve()
        if not path.is_relative_to(repo):raise ValueError('External file refused')
        relative=path.relative_to(repo)
        if relative.parts[:2]==('work','security') or path.name in ('auth.json','config.local.json') or path.suffix in ('.sqlite','.db','.sqlite3'):
            raise ValueError('Private/runtime data refused: '+str(relative))
        body=path.read_bytes();rows.append(dict(path=str(relative),sha256=hashlib.sha256(body).hexdigest(),bytes=len(body)))
    result=dict(at=datetime.now(timezone.utc).isoformat(),kind='Public source/report migration inventory; no model calls or file copies',
        based_on_scoring_config_sha256=hashlib.sha256(config_path.read_bytes()).hexdigest(),files=rows,
        unresolved_ambiguous_imports=ambiguous,
        caveats=['Static import closure cannot resolve every dynamic factory or package data reference. Review before creating a destination environment.',
            'Current working-tree files included; source commit alone may omit them. Regenerate after final results/editorial changes.',
            'Raw private evidence, OAuth, runtime binaries/weights and service volumes excluded. Destination security review required.'])
    output.write_text(json.dumps(result,indent=2)+'\n');return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for n in ['repo','config','output']:p.add_argument('--'+n,type=Path,required=True)
    a=p.parse_args();r=build(a.repo.resolve(),a.config.resolve(),a.output.resolve());print(json.dumps(dict(files=len(r['files']),ambiguous_imports=r['unresolved_ambiguous_imports'],model_calls=0)))
