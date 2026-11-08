#!/usr/bin/env python3
"""Adapted pinned LHTB source empty/reference controls; never calls a model.

Full Harbor cannot run its currently vulnerable pinned graph. This adapter only
adds the reviewed runtime/mount lifecycle needed to exercise upstream controls.
It preserves pacing and never mounts verifier material in the actor container.
"""
import argparse
from datetime import datetime,timezone
import hashlib,json,os,secrets,shutil,subprocess,tempfile,time
from pathlib import Path
from cost_context_study import REPO
BASE=REPO/'work/security/context-memory-20261107/lhtb2-source-review-001'
SOURCE=BASE/'development-source/tasks/unknown-config-semantics'
ROOT=BASE/'unknown-controls-002'
IMAGE='sha256:9ed8bd351e618aa9075306abee2a94a14954f35c23dbdc22902080e0dfbb930e'
PYTHON=Path(json.loads((BASE/'patched-task-python-pre-install-receipt.json').read_text())['target'])
ENV={'PYTHONPATH':'/opt/ttgl/python','PYTHONDONTWRITEBYTECODE':'1','PYTHONUNBUFFERED':'1','CFG_SOCKET':'/tmp/cfg.sock','CFG_RUN_DIR':'/opt/cfg/runs','CFG_ENGINE':'/opt/cfg/engine.py','CFG_DATA':'/opt/cfg/cfgd_data.json','CFG_KEY_PATH':'/opt/cfg/runs/.key','CFG_NONCE_FILE':'/tmp/cfg.nonce','CFG_SPEC':'/opt/cfg/spec.md','OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','HTTP_PROXY':'','HTTPS_PROXY':'','ALL_PROXY':'','http_proxy':'','https_proxy':'','all_proxy':''}
def write(path,value):
 with path.open('x') as f:json.dump(value,f,indent=2);f.write('\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def mount(src,dst,readonly=False):return ['--mount',f'type=bind,src={src},dst={dst}'+(',readonly' if readonly else '')]
def base_args():
 args=['--user','1000:1000','--network','none','--read-only','--cap-drop','ALL','--security-opt','no-new-privileges','--memory','4096m','--cpus','2','--pids-limit','256','--tmpfs','/tmp:rw,nosuid,nodev,size=256m','--workdir','/app']
 for key,value in ENV.items():args+=['-e',key+'='+value]
 return args

def run(condition):
 os.umask(0o077)
 if condition not in ('empty','reference'):raise ValueError('Control only')
 cell=ROOT/condition;cell.mkdir(parents=True)
 work=Path(tempfile.mkdtemp(prefix='ttgl-lhtb-unknown-'+condition+'-'));work.chmod(0o755)
 cfg=work/'cfg';shutil.copytree(SOURCE/'environment/harness',cfg);shutil.copyfile(cfg/'engine.py',cfg/'engine.orig.py');(cfg/'runs/submissions').mkdir(parents=True)
 app=work/'app';app.mkdir(mode=0o777);logs=work/'logs';logs.mkdir(mode=0o777)
 launcher=work/'cfg-launcher';launcher.write_text('#!/bin/sh\nexec python3 /opt/cfg/cfg_cli.py "$@"\n');launcher.chmod(0o755)
 for p in cfg.rglob('*'):
  p.chmod(0o777 if p.is_dir() else 0o666)
 cfg.chmod(0o777)
 original={str(p.relative_to(cfg)):sha(p) for p in cfg.rglob('*') if p.is_file()}
 source_hashes={str(p.relative_to(SOURCE)):sha(p) for p in SOURCE.rglob('*') if p.is_file()}
 write(cell/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),condition=condition,work=str(work),image=IMAGE,source_hashes=source_hashes,original_cfg=original,model_calls=0,source_safety='Pinned stdlib task daemon/CLI/reference/verifier inspected; only own paths and AF_UNIX socket. Source/advisory receipts retained. Reference control contains gold engine, never an experimental subject.',expected_seconds=5500 if condition=='reference' else 10,adapter_sha256=sha(Path(__file__))))
 name='ttgl-control-'+secrets.token_hex(12)
 actor=['docker','run','--detach','--name',name]+base_args()+mount(PYTHON,'/opt/ttgl/python',True)+mount(cfg,'/opt/cfg')+mount(app,'/app')+mount(launcher,'/usr/local/bin/cfg',True)
 if condition=='reference':actor+=mount(SOURCE/'solution','/solution',True)
 actor+=[IMAGE,'sleep','infinity']
 write(cell/'started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),container=name,no_retry=True,model_calls=0))
 started=time.monotonic()
 try:
  subprocess.run(actor,check=True,capture_output=True,timeout=45)
  inspect=json.loads(subprocess.check_output(['docker','inspect',name],text=True))[0]
  write(cell/'actor-inspect.json',inspect)
  if any(m['Destination'].startswith('/tests') for m in inspect['Mounts']):raise ValueError('Verifier leaked to actor')
  with (cell/'actor-stdout.log').open('wb') as stdout,(cell/'actor-stderr.log').open('wb') as stderr:
   command=['docker','exec',name,'bash','/solution/solve.sh'] if condition=='reference' else ['docker','exec',name,'cfg','status']
   execution=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=9000 if condition=='reference' else 60)
  if execution.returncode:raise ValueError('Control preparation failed:'+str(execution.returncode))
  subprocess.run(['docker','exec',name,'cfg','shutdown'],capture_output=True,timeout=30,check=True)
  subprocess.run(['docker','rm','--force',name],check=True,capture_output=True,timeout=30)
  # Seal actor state before introducing verifier-only source in another container.
  sealed={str(p.relative_to(cfg)):sha(p) for p in cfg.rglob('*') if p.is_file()};write(cell/'sealed-state.json',sealed)
  allowed=lambda p:p=='engine.py' or p=='spec.md' or p.startswith('runs/')
  modified=[p for p,h in original.items() if sealed.get(p)!=h and not allowed(p)]
  if modified:raise ValueError('Unexpected harness changes:'+str(modified))
  verifier=['docker','run','--rm']+base_args()+mount(PYTHON,'/opt/ttgl/python',True)+mount(cfg,'/opt/cfg')+mount(app,'/app')+mount(logs,'/logs/verifier')+mount(SOURCE/'tests','/tests',True)+[IMAGE,'python3','-m','pytest','-p','no:cacheprovider','-rA','/tests/test_outputs.py']
  with (cell/'verifier-stdout.log').open('wb') as stdout,(cell/'verifier-stderr.log').open('wb') as stderr:
   grade=subprocess.run(verifier,stdout=stdout,stderr=stderr,timeout=900)
  reward=float((logs/'reward.txt').read_text())
  expected=1.0 if condition=='reference' else 0.0
  for p in logs.glob('*'):
   if p.is_file():shutil.copyfile(p,cell/('verifier-'+p.name))
  result=dict(condition=condition,reward=reward,expected=expected,passed=reward==expected,verifier_exit_code=grade.returncode,wall_seconds=time.monotonic()-started,model_calls=0,minimum_interval_seconds=50,required_stage_rounds=105,adapter='Reviewed Alpine/Python3.11.18 patched pytest9.2.0 runtime; no tmux/Harbor/official leaderboard claim')
  write(cell/'complete.json',result);print(json.dumps(result),flush=True)
 except BaseException as error:
  write(cell/'stopped.json',dict(error=type(error).__name__,message=str(error),container=name,no_retry=True,model_calls=0));raise
 finally:
  # Only this owned control, never generic Docker cleanup or volumes.
  subprocess.run(['docker','rm','--force',name],capture_output=True,timeout=30)


if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('condition',choices=['empty','reference']);run(parser.parse_args().condition)
