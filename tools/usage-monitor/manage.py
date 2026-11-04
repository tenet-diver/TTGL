#!/usr/bin/env python3
"""Install/start, inspect, or stop the macOS local usage companion."""
import argparse,os,plistlib,shutil,subprocess,sys
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('action',choices=['install','status','stop']);a=p.parse_args()
label='local.ttgl.usage-monitor';domain=f'gui/{os.getuid()}';base=Path.home()/'Library/Application Support/TTGL Usage Monitor';agent=Path.home()/'Library/LaunchAgents'/f'{label}.plist'
if a.action=='status':raise SystemExit(subprocess.call(['launchctl','print',f'{domain}/{label}']))
if a.action=='stop':raise SystemExit(subprocess.call(['launchctl','bootout',f'{domain}/{label}']))
if sys.platform!='darwin':raise SystemExit('macOS installer; run server.py directly elsewhere')
for cmd in ['npx','zstd']:
 if not shutil.which(cmd):raise SystemExit(f'Required existing executable missing: {cmd}')
subprocess.run(['launchctl','bootout',f'{domain}/{label}'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
base.mkdir(parents=True,exist_ok=True);os.chmod(base,0o700);data=base/'data';data.mkdir(exist_ok=True);os.chmod(data,0o700)
shutil.copytree(Path(__file__).parent,base/'app',dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__'))
skill=Path.home()/'.codex/skills/ttgl-usage-monitor';shutil.copytree(Path(__file__).parent/'skill/ttgl-usage-monitor',skill,dirs_exist_ok=True)
agent.parent.mkdir(exist_ok=True);agent.write_bytes(plistlib.dumps({'Label':label,'ProgramArguments':[sys.executable,str(base/'app/server.py'),'--data',str(data),'--port','8766'],'RunAtLoad':True,'KeepAlive':True,'WorkingDirectory':str(base),'StandardOutPath':str(base/'service.log'),'StandardErrorPath':str(base/'service-error.log'),'EnvironmentVariables':{'PATH':os.environ['PATH']},'ThrottleInterval':15}));os.chmod(agent,0o600)
subprocess.run(['launchctl','bootstrap',domain,str(agent)],check=True)
print('Running: http://127.0.0.1:8766 · local data:',data)
