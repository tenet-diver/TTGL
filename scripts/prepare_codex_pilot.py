#!/usr/bin/env python3
"""Prepare and grade a sealed, adapted BugsInPy feasibility pilot (no model calls)."""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tarfile
import time
import urllib.request
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'experiments/codex-pilot-001'
WORK = Path('/workspace/scratch/ttgl-codex-pilot')
EVALUATOR = Path('/workspace/scratch/ttgl-codex-pilot-evaluator')
PYTHON = Path('/workspace/.tools/ttgl-codex-pilot/bin/python')
DATASET_REV = '11c5f1eea954a42132cfd06bf257766a7963e0fd'
ARMS = ['luna', 'sol', 'precall', 'personal']
CANDIDATES = [('PySnooper', i) for i in range(1, 4)] + [('tqdm', i) for i in range(1, 10)]
REPOS = {'PySnooper': 'cool-RR/PySnooper', 'tqdm': 'tqdm/tqdm'}
PACKAGES = {'PySnooper': 'pysnooper', 'tqdm': 'tqdm'}
STATEMENTS = {
 ('PySnooper',1): 'Tracing a function whose source contains non-ASCII Chinese text should work, and writing the trace to a file should preserve that text as UTF-8. Fix source decoding and trace file writing while preserving existing tracing behavior.',
 ('PySnooper',2): 'The snoop decorator must support custom_repr as either one (condition, formatter) pair or an ordered sequence of such pairs. A condition may be a type (matching instances) or a predicate callable. Use the formatter for the first matching condition when rendering local values; otherwise keep the default representation. A single pair such as custom_repr=(list, lambda value: str(len(value))) must work. Preserve the existing tracing API and default behavior.',
 ('PySnooper',3): 'Using a file path as the output destination of the tracing decorator raises a NameError instead of writing the trace. Make path-based trace output work and preserve stream and default stderr output.',
 ('tqdm',1): 'The tqdm.contrib.tenumerate helper should preserve Python enumerate semantics, including an explicitly supplied nonzero start index, while showing progress. A call such as tenumerate(range(9), 42) currently fails or produces incorrect behavior. Fix it without changing other contrib helpers.',
 ('tqdm',2): 'Custom progress-bar formatting should return the formatted output both with and without an explicit column width. When trimming ANSI-coloured output to a width, preserve terminal-reset behavior without redundant reset sequences. Fix formatting while preserving existing custom-format semantics.',
 ('tqdm',3): 'Boolean conversion of a progress bar should reflect whether its total or iterable is nonempty. Handle known totals, unsized iterables, and the undefined case where neither total nor iterable exists, instead of relying on an invalid length conversion. Preserve Python compatibility and existing iteration behavior.',
 ('tqdm',4): 'Progress formatting with a custom numeric unit scale should work when the total is unknown. It currently attempts arithmetic on the absent total. Preserve the correct scaling of current progress and rate.',
 ('tqdm',5): 'A disabled progress bar should still expose the same total and Boolean behavior as an enabled one. Preserve inferred iterable lengths and explicit totals even when progress display is disabled.',
 ('tqdm',6): 'Wrapping an imap iterator in a progress bar can trigger premature length access before all fields have been initialized. Make length handling robust without changing ordinary iteration.',
 ('tqdm',7): 'The command-line option parser should recognize option prefixes only at valid token boundaries. Hyphens embedded within a value should remain part of that value. Preserve existing option syntax.',
 ('tqdm',8): 'Custom bar formats containing the bar placeholder should preserve and format the user-provided left and right portions. Fix incorrect handling without changing the default bar format.',
 ('tqdm',9): 'SI size formatting should round correctly near unit boundaries, and progress bars should provide their explicit total when no iterable supplies a length. Preserve ordinary update behavior.'
}
MEMORY = '''# User project preferences\n\n- Preserve the public API and behavior outside the reported bug.\n- Keep this project compatible with its existing supported Python versions.\n- Add no runtime dependencies.\n- Prefer a small maintainable fix and verify it with focused tests.\n- Existing tests must not be deleted, weakened or skipped to obtain a pass.\n'''

def sha(data: bytes) -> str:
 return hashlib.sha256(data).hexdigest()
def dump(path: Path, obj):
 path.parent.mkdir(parents=True,exist_ok=True)
 path.write_text(json.dumps(obj,indent=2,sort_keys=True)+'\n')
def fetch(url: str) -> bytes:
 with urllib.request.urlopen(url,timeout=60) as response: return response.read()
def files(root: Path):
 return {str(p.relative_to(root)):sha(p.read_bytes()) for p in sorted(root.rglob('*')) if p.is_file() and '__pycache__' not in p.parts and '.pytest_cache' not in p.parts and p.suffix != '.pyc'}
def archive(repo: str, revision: str, dest: Path, provenance: list):
 url=f'https://codeload.github.com/{repo}/tar.gz/{revision}'
 data=fetch(url)
 provenance.append({'url':url,'sha256':sha(data),'bytes':len(data)})
 dest.mkdir(parents=True,exist_ok=False)
 with tarfile.open(fileobj=io.BytesIO(data),mode='r:gz') as tf:
  members=tf.getmembers()
  prefix=members[0].name.split('/')[0]+'/'
  for member in members:
   if not member.name.startswith(prefix): continue
   relative=member.name[len(prefix):]
   if not relative: continue
   path=Path(relative)
   if path.is_absolute() or '..' in path.parts or member.issym() or member.islnk():
    raise ValueError('Archive contains an unsafe member')
   target=dest/path
   if member.isdir(): target.mkdir(parents=True,exist_ok=True)
   elif member.isfile():
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_bytes(tf.extractfile(member).read())

def run_tests(repo: Path, task: dict, dest: Path):
 dest.mkdir(parents=True,exist_ok=True)
 xml=dest/'junit.xml'
 command=[str(PYTHON),'-m','pytest','-q','-o','addopts=',task['test_file'],f'--junitxml={xml}']
 if task['task_id']=='pysnooper-2': command += ['-k','not test_disable']
 env=os.environ.copy();env.update(PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',PYTHONPATH=str(repo),PYTEST_ADDOPTS='')
 start=time.monotonic()
 try:
  result=subprocess.run(command,cwd=repo,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=90)
  code=result.returncode; output=result.stdout
 except subprocess.TimeoutExpired as exc:
  code=124;output=(exc.stdout or b'').decode(errors='replace') if isinstance(exc.stdout,bytes) else (exc.stdout or '')
 (dest/'stdout.txt').write_text(output)
 counts={'tests':0,'failures':0,'errors':0,'skipped':0}
 if xml.exists():
  tree=ET.parse(xml)
  suites=list(tree.getroot().iter('testsuite'))
  for name in counts: counts[name]=sum(int(x.attrib.get(name,0)) for x in suites)
 return {'returncode':code,'counts':counts,'elapsed_seconds':time.monotonic()-start,'command':command,'stdout_path':str(dest/'stdout.txt'),'stdout_sha256':sha((dest/'stdout.txt').read_bytes()),'junit_path':str(xml),'junit_sha256':sha(xml.read_bytes()) if xml.exists() else None}

def overlay_tests(src: Path, dest: Path, task: dict):
 testdir=Path(task['test_file']).parent
 shutil.rmtree(dest/testdir,ignore_errors=True)
 shutil.copytree(src/testdir,dest/testdir)

def prepare(count: int):
 if (OUTPUT/'protocol.json').exists(): raise RuntimeError('Existing frozen protocol; use its workspaces, do not silently reselect tasks')
 EVALUATOR.mkdir(parents=True,exist_ok=True)
 provenance=[];screen=[];selected=[]
 for project,number in CANDIDATES:
  task_id=f'{project.lower()}-{number}'
  info_url=f'https://raw.githubusercontent.com/soarsmu/BugsInPy/{DATASET_REV}/projects/{project}/bugs/{number}/bug.info'
  info=fetch(info_url);provenance.append({'url':info_url,'sha256':sha(info),'bytes':len(info)})
  meta=dict(re.findall(r'(\w+)="([^"]*)"',info.decode()))
  task={'task_id':task_id,'project':project,'bug_id':number,'repo':REPOS[project],'base_commit':meta['buggy_commit_id'],'fixed_commit':meta['fixed_commit_id'],'test_file':meta['test_file'],'original_python':meta['python_version'],'source_dir':PACKAGES[project],'statement':STATEMENTS[(project,number)]}
  taskroot=EVALUATOR/task_id
  if taskroot.exists(): shutil.rmtree(taskroot)
  archive(task['repo'],task['base_commit'],taskroot/'base',provenance)
  archive(task['repo'],task['fixed_commit'],taskroot/'fixed',provenance)
  shutil.copytree(taskroot/'base',taskroot/'buggy-eval')
  overlay_tests(taskroot/'fixed',taskroot/'buggy-eval',task)
  base=run_tests(taskroot/'buggy-eval',task,taskroot/'control-buggy')
  fixed=run_tests(taskroot/'fixed',task,taskroot/'control-fixed')
  eligible=base['returncode']==1 and base['counts']['failures']>0 and base['counts']['errors']==0 and fixed['returncode']==0 and fixed['counts']['tests']>0
  screen.append({'task_id':task_id,'eligible':eligible,'buggy':base,'fixed':fixed,'rule':'buggy has assertion/test failures without collection errors; fixed full selected module passes'})
  print(json.dumps({'task_id':task_id,'eligible':eligible,'buggy':base['counts'],'fixed':fixed['counts']}),flush=True)
  if eligible:
   task['base_tree_sha256']=sha(json.dumps(files(taskroot/'base'),sort_keys=True).encode())
   task['evaluation_test_tree_sha256']=sha(json.dumps(files(taskroot/'fixed'/Path(task['test_file']).parent),sort_keys=True).encode())
   selected.append(task)
  if len(selected)==count: break
 if len(selected)<count:
  dump(OUTPUT/'feasibility-screen-incomplete.json',screen)
  raise RuntimeError(f'Only {len(selected)} eligible tasks')
 for task in selected:
  for arm in ARMS:
   dest=WORK/arm/task['task_id']
   if dest.exists(): raise RuntimeError(f'Worker directory already exists: {dest}')
   shutil.copytree(EVALUATOR/task['task_id']/'base',dest,ignore=shutil.ignore_patterns('.git','__pycache__','.pytest_cache','*.pyc'))
   (dest/'USER_MEMORY.md').write_text(MEMORY)
   (dest/'TASK.md').write_text('# Repository repair\n\n'+task['statement']+'\n\nRead USER_MEMORY.md. Work only in this checkout. Do not access network, sibling workspaces, benchmark metadata, gold patches, or evaluator files. You may run public tests and add your own tests. Preserve existing tests. Do not use git history.\n\nPython: '+str(PYTHON)+'\n')
 tasks={'tasks':selected,'arms':ARMS,'workspace_root':str(WORK),'evaluator_root':str(EVALUATOR)}
 dump(OUTPUT/'tasks.json',tasks)
 dump(OUTPUT/'provenance.json',{'dataset':'BugsInPy','dataset_revision':DATASET_REV,'sources':provenance,'feasibility_screen':screen,'adaptations':['CPython 3.8.20 replaces patch versions 3.8.1/3.6.9 for compatibility','All tests in designated official fixed test module are used, including regression guards','Fixed-version test directory is overlaid on buggy/submitted source only in evaluator','Task descriptions are investigator-written behavioral specifications based on published regression intent; no official issue text supplied by BugsInPy','No test semantics were modified'],'environment_python':subprocess.check_output([str(PYTHON),'--version'],text=True).strip()})
 protocol={'status':'frozen_before_model_trials','task_ids':[t['task_id'] for t in selected],'arms':ARMS,'attempts_per_arm_task':1,'candidate_order':[f'{p.lower()}-{n}' for p,n in CANDIDATES],'selection':'first four eligible by frozen feasibility order; no model outcomes used','test_policy':'official fixed test module, all cases, plus no prohibited edits','reasoning_effort':'medium','model_ids':{'luna':'gpt-6-luna','sol':'gpt-6.1-sol'},'limitations':['small convenience feasibility subset, no frontier or statistical superiority claim','shared filesystem provides soft isolation only','no complete token or dollar cost telemetry','historical public tasks may be training-contaminated'],'tasks_sha256':sha((OUTPUT/'tasks.json').read_bytes()),'provenance_sha256':sha((OUTPUT/'provenance.json').read_bytes()),'grader_sha256':sha(Path(__file__).read_bytes()),'memory_sha256':sha(MEMORY.encode()),'seed':1729}
 dump(OUTPUT/'protocol.json',protocol)
 print(json.dumps({'status':'ready','task_ids':protocol['task_ids'],'protocol_sha256':sha((OUTPUT/'protocol.json').read_bytes())}),flush=True)

def grade(arm: str, task_id: str, out: Path | None):
 registry=json.loads((OUTPUT/'tasks.json').read_text())
 task=next(t for t in registry['tasks'] if t['task_id']==task_id)
 protocol=json.loads((OUTPUT/'protocol.json').read_text())
 if sha((OUTPUT/'tasks.json').read_bytes())!=protocol['tasks_sha256'] or sha(Path(__file__).read_bytes())!=protocol['grader_sha256']:
  raise RuntimeError('Frozen task or grader changed')
 base=EVALUATOR/task_id/'base';fixed=EVALUATOR/task_id/'fixed';worker=WORK/arm/task_id
 before=files(base);after=files(worker)
 changed=sorted(p for p in set(before)|set(after) if before.get(p)!=after.get(p) and p not in ['TASK.md','USER_MEMORY.md'])
 allowed_prefix=task['source_dir']+'/'
 test_prefix=str(Path(task['test_file']).parent)+'/'
 prohibited=[]
 for path in changed:
  is_test=path.startswith(test_prefix) or path.startswith('tests/')
  if is_test and path in before: prohibited.append(path)
  elif not path.startswith(allowed_prefix) and not (is_test and path not in before): prohibited.append(path)
 dest=out or OUTPUT/'grades'/arm/task_id
 if dest.exists(): raise RuntimeError('Grade directory exists; use a distinct output directory')
 dest.mkdir(parents=True)
 checkout=EVALUATOR/'grading'/arm/task_id
 if checkout.exists(): shutil.rmtree(checkout)
 shutil.copytree(base,checkout,ignore=shutil.ignore_patterns('__pycache__','.pytest_cache','*.pyc'))
 patch_records=[]
 for path in changed:
  if path in prohibited or path.startswith(test_prefix) or path.startswith('tests/'): continue
  target=checkout/path
  if path not in after: target.unlink(missing_ok=True)
  else:
   target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(worker/path,target)
  patch_records.append({'path':path,'before_sha256':before.get(path),'after_sha256':after.get(path)})
 overlay_tests(fixed,checkout,task)
 test=run_tests(checkout,task,dest)
 patch_hash=sha(json.dumps(patch_records,sort_keys=True).encode())
 report={'task_id':task_id,'arm':arm,'resolved':test['returncode']==0 and test['counts']['tests']>0 and not prohibited,'base_commit':task['base_commit'],'testcounts':test['counts'],'returncode':test['returncode'],'patch_sha256':patch_hash,'changed_files':patch_records,'prohibited_edits':prohibited,'test':test,'protocol_sha256':sha((OUTPUT/'protocol.json').read_bytes())}
 dump(dest/'report.json',report)
 subprocess.run(['diff','-ruN','--exclude=__pycache__','--exclude=.pytest_cache',str(base/task['source_dir']),str(worker/task['source_dir'])],stdout=(dest/'submission.patch').open('w'),stderr=subprocess.DEVNULL)
 print(json.dumps({'task_id':task_id,'arm':arm,'resolved':report['resolved'],'report_path':str(dest/'report.json'),'grader_report_sha256':sha((dest/'report.json').read_bytes()),'patch_sha256':patch_hash,'testcounts':test['counts']}))

def main():
 parser=argparse.ArgumentParser(description=__doc__)
 sub=parser.add_subparsers(dest='command',required=True)
 p=sub.add_parser('prepare');p.add_argument('--count',type=int,default=4)
 g=sub.add_parser('grade');g.add_argument('--arm',choices=ARMS,required=True);g.add_argument('--task-id',required=True);g.add_argument('--output',type=Path)
 args=parser.parse_args()
 if args.command=='prepare':prepare(args.count)
 else:grade(args.arm,args.task_id,args.output)
if __name__=='__main__':main()
