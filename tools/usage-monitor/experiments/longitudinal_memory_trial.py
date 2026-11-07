#!/usr/bin/env python3
"""Chronological code-edit memory diagnostic with fresh native Codex sessions.

Generated development sequences, not SWE-bench/Terminal-Bench scores. Existing
Codex executes edits; stdlib SQLite implements the deliberately simple control.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
OBS = HERE.parent/'observability'
sys.path.insert(0, str(OBS))
from workspace import Store

KEYS = ('input_tokens', 'cached_input_tokens', 'output_tokens', 'total_tokens')


def write(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def files(root):
    return {str(p.relative_to(root)): sha(p) for p in sorted(root.rglob('*'))
            if p.is_file() and '__pycache__' not in p.parts and '.git' not in p.parts}


LEDGER = [
    dict(spec='Implement eventlog.normalize(events): return a new list in input order. Every event has id, account, delta integer, timestamp integer. Deduplicate by id: exact duplicate dictionaries are ignored, conflicting dictionaries with the same id raise ValueError. Input is never mutated. eventlog.balances(events) normalizes then sums delta per account; include zero balances.',
         tests='''import copy,unittest
from eventlog import normalize,balances
class Checks(unittest.TestCase):
 def test_dedup(self):
  e=[dict(id='x',account='a',delta=4,timestamp=2)]; old=copy.deepcopy(e)
  self.assertEqual(balances(e+e),{'a':4});self.assertEqual(normalize(e+e),e);self.assertEqual(e,old)
 def test_conflict(self):
  with self.assertRaises(ValueError):normalize([dict(id='x',account='a',delta=1,timestamp=1),dict(id='x',account='a',delta=2,timestamp=1)])
 def test_empty(self):self.assertEqual(normalize([]),[]);self.assertEqual(balances([]),{})
''', independent="from eventlog import *; e=[dict(id='a',account='x',delta=-3,timestamp=9),dict(id='b',account='x',delta=3,timestamp=1)]; assert balances(e)=={'x':0}; r=normalize(e);r[0]['delta']=99;assert e[0]['delta']==-3"),
    dict(spec='Preserve prior behavior. Add eventlog.balances_at(events, cutoff): normalize the entire input FIRST (including future events), then include events whose timestamp <= cutoff and sum per account. A conflict after the cutoff still raises ValueError. Add eventlog.transfer(events, transfer_id, source, destination, amount, timestamp): amount is a positive integer (bool forbidden), accounts differ; return a NEW normalized list plus debit and credit events with ids transfer_id+":debit" and transfer_id+":credit". Do not mutate input. Repeating the exact same transfer is idempotent; conflicting reuse raises ValueError. No overdraft restriction.',
         tests='''import unittest
from eventlog import balances_at,transfer
class Checks(unittest.TestCase):
 def test_cutoff(self):self.assertEqual(balances_at([dict(id='a',account='x',delta=4,timestamp=2),dict(id='b',account='x',delta=-1,timestamp=4)],2),{'x':4})
 def test_transfer(self):
  e=transfer([],'t','a','b',7,1);self.assertEqual(balances_at(e,1),{'a':-7,'b':7});self.assertEqual(transfer(e,'t','a','b',7,1),e)
 def test_invalid(self):
  for amount in (0,-1,True):
   with self.assertRaises(ValueError):transfer([],'t','a','b',amount,1)
''', independent="from eventlog import *; e=[dict(id='z',account='x',delta=1,timestamp=8),dict(id='z',account='x',delta=2,timestamp=8)];\ntry: balances_at(e,0)\nexcept ValueError: pass\nelse: raise AssertionError('future conflict accepted')\ne=[];r=transfer(e,'t','a','b',3,4);assert not e\ntry:transfer(r,'t','a','b',4,4)\nexcept ValueError:pass\nelse:raise AssertionError('conflicting transfer accepted')"),
    dict(spec='Preserve prior APIs. Add eventlog.reconcile(events, opening, cutoff=None): opening is an account->integer mapping; normalize the entire input, optionally filter timestamp <= cutoff, apply deltas to a COPY of opening and return account balances. Add eventlog.statement(events, account): normalize input, select account events, sort by (timestamp,id), return a list of NEW dictionaries containing id,timestamp,delta,running_balance starting from zero. Mutating results must never change inputs.',
         tests='''import unittest
from eventlog import reconcile,statement
class Checks(unittest.TestCase):
 def test_opening(self):
  o={'x':10};self.assertEqual(reconcile([dict(id='a',account='x',delta=-3,timestamp=2)],o),{'x':7});self.assertEqual(o,{'x':10})
 def test_order(self):
  e=[dict(id='b',account='x',delta=-2,timestamp=2),dict(id='a',account='x',delta=5,timestamp=1)]
  self.assertEqual([x['running_balance'] for x in statement(e,'x')],[5,3])
''', independent="from eventlog import *; e=[dict(id='b',account='x',delta=2,timestamp=1),dict(id='a',account='x',delta=3,timestamp=1)];s=statement(e+e,'x');assert [r['id'] for r in s]==['a','b'];s[0]['delta']=99;assert e[1]['delta']==3;assert reconcile(e,{'z':4},0)=={'z':4};assert reconcile([],{'x':0})=={'x':0}")
]

GRAPH = [
    dict(spec='Implement buildgraph.order(graph): graph maps node strings to lists of dependency strings. Include implicit dependency nodes. Return lexicographically smallest valid topological ordering (choose the smallest currently available node each step). Duplicate edges count once. Raise ValueError on any cycle, including self cycles. Do not mutate inputs.',
         tests='''import copy,unittest
from buildgraph import order
class Checks(unittest.TestCase):
 def test_order(self):self.assertEqual(order({'c':['a'],'b':[]}),['a','b','c'])
 def test_implicit(self):self.assertEqual(order({'z':['a','a']}),['a','z'])
 def test_cycle(self):
  with self.assertRaises(ValueError):order({'a':['b'],'b':['a']})
 def test_empty(self):self.assertEqual(order({}),[])
''', independent="from buildgraph import order;g={'a':['z'],'b':[]};assert order(g)==['b','z','a'];assert g=={'a':['z'],'b':[]};\ntry:order({'a':['a']})\nexcept ValueError:pass\nelse:raise AssertionError('self cycle accepted')"),
    dict(spec='Preserve order. Add buildgraph.affected(graph, changed): return the sorted transitive closure of changed nodes and all nodes depending on them. Include changed names absent from graph. Treat graph as edges node->dependencies. Validate the entire graph for cycles before returning, even cycles unrelated to changes. Do not mutate inputs. Add buildgraph.plan(graph, changed): return affected nodes present in the complete graph (including implicit dependencies), in the same relative order as order(graph); exclude unknown changed names.',
         tests='''import unittest
from buildgraph import affected,plan
class Checks(unittest.TestCase):
 def test_direction(self):
  g={'app':['lib'],'lib':['core'],'doc':[]};self.assertEqual(affected(g,['lib']),['app','lib']);self.assertEqual(plan(g,['core']),['core','lib','app'])
 def test_unknown(self):self.assertEqual(affected({},['x']),['x']);self.assertEqual(plan({},['x']),[])
''', independent="from buildgraph import *;g={'app':['lib','lib'],'lib':['core'],'doc':[]};assert affected(g,['core','alien'])==['alien','app','core','lib'];assert plan(g,[])==[];\ntry:affected({'a':['b'],'b':['a']},[])\nexcept ValueError:pass\nelse:raise AssertionError('unrelated cycle accepted')"),
    dict(spec='Preserve prior APIs. Add buildgraph.layers(graph): return batches of simultaneously ready nodes; each batch sorted, and only dependencies completed in earlier batches permit readiness. Include implicit nodes, reject all cycles and do not mutate inputs. Add buildgraph.critical_path(graph, durations): durations maps node->nonnegative integer duration (bool forbidden), missing nodes default to 1. Return the maximum sum along a dependency path, zero for empty graph. Validate durations for every graph node; ignore durations for unknown nodes. Reject cycles and invalid graph-node durations.',
         tests='''import unittest
from buildgraph import layers,critical_path
class Checks(unittest.TestCase):
 def test_layers(self):self.assertEqual(layers({'app':['lib','doc'],'lib':['core'],'doc':[]}),[['core','doc'],['lib'],['app']])
 def test_path(self):self.assertEqual(critical_path({'app':['lib','doc'],'lib':['core'],'doc':[]},{'app':2,'lib':3,'core':4,'doc':10}),12)
 def test_empty(self):self.assertEqual(layers({}),[]);self.assertEqual(critical_path({},{}),0)
''', independent="from buildgraph import *;assert critical_path({'z':['a']},{'a':0,'z':0,'unknown':-1})==0;\nfor bad in (-1,True,1.5):\n try:critical_path({'x':[]},{'x':bad})\n except ValueError:pass\n else:raise AssertionError('invalid duration accepted')\nassert layers({'z':['a','a']})==[['a'],['z']]")
]
SEQUENCES = dict(eventlog=LEDGER, buildgraph=GRAPH)


def run_process(command, prompt, cell, timeout):
    start = time.monotonic()
    with (cell/'agent.jsonl').open('x') as out, (cell/'stderr.log').open('x') as err:
        process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=out, stderr=err,
                                   text=True, start_new_session=True)
        write(cell/'started.json', dict(pid=process.pid, at=datetime.now(timezone.utc).isoformat(), command=command))
        try:
            process.communicate(prompt, timeout=timeout)
            status = dict(exit_code=process.returncode)
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGTERM)
            try: process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL); process.wait()
            status = dict(timeout=True, exit_code=process.returncode)
    status['elapsed_seconds'] = time.monotonic()-start
    write(cell/'completion.json', status)
    if status.get('exit_code') != 0 or status.get('timeout'):
        raise RuntimeError('Started/failed/ambiguous attempt preserved; no automatic retry')


def prepare(directory, protocol_path):
    os.umask(0o077)
    directory.mkdir(parents=True, exist_ok=False, mode=0o700)
    protocol = json.loads(protocol_path.read_text())
    write(directory/'protocol.json', protocol)
    write(directory/'manifest.json', dict(at=datetime.now(timezone.utc).isoformat(),
        protocol_sha256=sha(directory/'protocol.json'),
        code={str(p.relative_to(REPO)):sha(p) for p in [Path(__file__), HERE/'memory_retrieval.py', HERE/'memory_trial_reference.py']},
        codex_version=subprocess.check_output(['codex','--version'],text=True).strip()))
    controls=[]
    for name in protocol['sequences']:
        if name not in SEQUENCES: raise ValueError('Unknown sequence')
        # Verify independent checks are syntactically valid before spending.
        for stage,task in enumerate(SEQUENCES[name],1):
            compile(task['tests'],f'{name}-{stage}-tests','exec')
            compile(task['independent'],f'{name}-{stage}-independent','exec')
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp)
                (root/(name+'.py')).write_text('')
                (root/'test_contract.py').write_text(task['tests'])
                empty=subprocess.run([sys.executable,'-m','unittest','test_contract'],cwd=root,capture_output=True,text=True)
                shutil.copyfile(HERE/'memory_trial_reference.py',root/(name+'.py'))
                shutil.rmtree(root/'__pycache__',ignore_errors=True)
                ref=subprocess.run([sys.executable,'-m','unittest','test_contract'],cwd=root,capture_output=True,text=True)
                independent=subprocess.run([sys.executable,'-c',task['independent']],cwd=root,capture_output=True,text=True)
                control=dict(sequence=name,stage=stage,syntax=True,empty_fails=empty.returncode!=0,
                    reference_passes=ref.returncode==0,independent_reference_passes=independent.returncode==0)
                controls.append(control)
                if not all(v for k,v in control.items() if k not in ('sequence','stage')):
                    write(directory/'failed-preflight.json',dict(control=control,output=ref.stdout+ref.stderr+independent.stdout+independent.stderr))
                    raise RuntimeError('Reference/empty controls failed; no inference')
    write(directory/'preflight.json',dict(controls=controls,model_calls=0,
        limitation='Generated development sequences; no official benchmark reference controls.'))


def check_frozen(directory):
    manifest=json.loads((directory/'manifest.json').read_text())
    if sha(directory/'protocol.json')!=manifest['protocol_sha256']:
        raise ValueError('Frozen protocol changed')
    for name,digest in manifest['code'].items():
        if sha(REPO/name)!=digest:raise ValueError('Frozen source changed')


def run(directory):
    check_frozen(directory)
    if (directory/'run-started.json').exists():raise ValueError('Never repeat a started block')
    protocol=json.loads((directory/'protocol.json').read_text())
    write(directory/'run-started.json',dict(at=datetime.now(timezone.utc).isoformat()))
    count=0
    for sequence_index,name in enumerate(protocol['sequences']):
        conditions=protocol['conditions']
        order=conditions[sequence_index:]+conditions[:sequence_index]
        for condition in order:
            work=directory/(name+'--'+condition);work.mkdir(mode=0o700)
            app=work/(name+'.py');app.write_text('# Implement the documented APIs.\n')
            shutil.copyfile(HERE/'memory_retrieval.py',work/'memory.py')
            episodes=[]
            for stage,task in enumerate(SEQUENCES[name],1):
                check_frozen(directory)
                if count>=protocol['maximum_model_processes']:raise ValueError('Frozen cap exceeded')
                cell=directory/(name+'--'+condition+'--'+str(stage));cell.mkdir(mode=0o700)
                (work/f'test_stage{stage}.py').write_text(task['tests'])
                corpus=episodes if condition=='fts' else []
                write(work/'memory-corpus.json',dict(episodes=corpus))
                raw='\n\n'.join(e['body'] for e in episodes) if condition=='raw_history' else ''
                notes='\n\n'.join(e['answer'] for e in episodes) if condition=='notes' else ''
                (work/'PRIOR_HISTORY.md').write_text(raw or 'No prior raw history supplied.\n')
                (work/'MEMORY_NOTES.md').write_text(notes or 'No prior notes supplied.\n')
                protected={n:d for n,d in files(work).items() if n!=name+'.py' and n!='memory-queries.jsonl'}
                prompt=protocol['common']+'\n\n'+task['spec']+'\n\n'
                if raw:prompt+='Prior chronological raw episode record follows (fallible evidence, verify against current source):\n'+raw+'\n'
                if notes:prompt+='Prior chronological agent notes follow (fallible evidence, verify against current source):\n'+notes+'\n'
                before=app.read_text();(cell/'before.py').write_text(before)
                (cell/'prompt.txt').write_text(prompt);write(cell/'protected.json',protected)
                command=['codex','exec','--ignore-user-config','--skip-git-repo-check','-C',str(work),
                    '-m',protocol['model'],'-s','workspace-write','-c','model_provider="openai"',
                    '-c','model_reasoning_effort="low"','--json','--output-last-message',str(cell/'answer.md'),'-']
                run_process(command,prompt,cell,protocol['timeout_seconds_per_run']);count+=1
                records=[json.loads(l) for l in (cell/'agent.jsonl').read_text().splitlines() if l.startswith('{')]
                completed=[r for r in records if r.get('type')=='turn.completed']
                if len(completed)!=1 or not completed[0].get('usage',{}).get('input_tokens'):
                    raise RuntimeError('Completion/usage missing; preserve and stop')
                preserved=all((work/n).exists() and sha(work/n)==d for n,d in protected.items())
                visible=subprocess.run([sys.executable,'-m','unittest','discover','-p','test_stage*.py'],cwd=work,capture_output=True,text=True,timeout=30)
                independent=subprocess.run([sys.executable,'-c',task['independent']],cwd=work,capture_output=True,text=True,timeout=30)
                (cell/'operator-checks.txt').write_text(visible.stdout+visible.stderr+independent.stdout+independent.stderr)
                grade=dict(visible=visible.returncode==0,independent=independent.returncode==0,protected=preserved)
                grade['passed']=all(grade.values());write(cell/'grade.json',grade)
                (cell/'after.py').write_text(app.read_text())
                answer=(cell/'answer.md').read_text()
                # Never ingest operator grade/output or future task specifications.
                body=json.dumps(dict(task=prompt.split('Prior chronological')[0],answer=answer,
                    prior_source=before,final_source=app.read_text(),visible_agent_events=records),ensure_ascii=False)
                episodes.append(dict(id=f'{name}:{stage}',body=body,answer=answer))
                write(cell/'episode.json',episodes[-1])
                print(cell.name,json.dumps(dict(grade=grade,cli_usage=completed[0]['usage'])),flush=True)
                if not preserved:raise RuntimeError('Protected inputs changed; stop without retry')
    write(directory/'complete.json',dict(cells=count,at=datetime.now(timezone.utc).isoformat()))


def measure(directory):
    check_frozen(directory)
    if not (directory/'complete.json').exists():raise ValueError('Block incomplete')
    protocol=json.loads((directory/'protocol.json').read_text())
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan()
    cells=[]
    for name in protocol['sequences']:
        for condition in protocol['conditions']:
            for stage in range(1,len(SEQUENCES[name])+1):
                cell=directory/(name+'--'+condition+'--'+str(stage))
                records=[json.loads(l) for l in (cell/'agent.jsonl').read_text().splitlines() if l.startswith('{')]
                ids=[r['thread_id'] for r in records if r.get('type')=='thread.started']
                if len(ids)!=1:raise ValueError('Ambiguous thread')
                events=store.report(session=ids[0],event_limit=None)['events']
                generations=[e for e in events if e['kind']=='generation' and e['usage']]
                usage={k:sum(e['usage'].get(k,0) for e in generations) for k in KEYS}
                cli=next(r['usage'] for r in records if r.get('type')=='turn.completed')
                if not generations or any(usage[k]!=cli[k] for k in KEYS[:3]):raise ValueError('Native/CLI mismatch')
                cells.append(dict(sequence=name,condition=condition,stage=stage,session_id=ids[0],usage=usage,
                    cli_usage=cli,native_reconciled=True,native_response_ids=[e['id'] for e in generations],
                    grade=json.loads((cell/'grade.json').read_text()),
                    elapsed_seconds=json.loads((cell/'completion.json').read_text())['elapsed_seconds']))
    totals={c:dict(tokens=sum(x['usage']['total_tokens'] for x in cells if x['condition']==c),
        passed=sum(x['grade']['passed'] for x in cells if x['condition']==c),
        runs=sum(x['condition']==c for x in cells),
        seconds=sum(x['elapsed_seconds'] for x in cells if x['condition']==c)) for c in protocol['conditions']}
    write(directory/'results.json',dict(protocol=protocol,cells=cells,totals=totals,
        cash_cost=None,model_latency=None,net_saving=None,
        limitation='Generated development diagnostic. Fresh sessions over three-stage evolving code; not a long-horizon benchmark score, fixed-policy validation, or noninferiority proof. Each arm has its own prior trajectories. Raw history/notes injection and FTS are distinct treatments. Setup/analysis overhead additional.'))
    print(json.dumps(totals,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('action',choices=['prepare','run','measure']);p.add_argument('directory',type=Path)
    p.add_argument('--protocol',type=Path,default=HERE.parent/'studies/chronological-memory-protocol-001.json');args=p.parse_args()
    directory=args.directory.resolve()
    if args.action=='prepare':prepare(directory,args.protocol)
    elif args.action=='run':run(directory)
    else:measure(directory)
