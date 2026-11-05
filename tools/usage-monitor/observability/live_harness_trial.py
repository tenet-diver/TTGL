#!/usr/bin/env python3
"""Matched code-edit-and-test tasks using normal Codex shell tools and live proxy compression."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
REPO=HERE.parents[2]


def fixture(case, root):
    root.mkdir(parents=True,exist_ok=False,mode=0o700)
    if case=='search-calculation':
        (root/'app.py').write_text('def total_payable(lines):\n    return sum(line["unit_cents"] for line in lines)\n')
        nested=root/'checks/integration/customer_checkout/discounts/line_item_accounting/regression_examples'
        nested.mkdir(parents=True)
        rows=['import unittest\nfrom app import total_payable\n\nclass Totals(unittest.TestCase):\n    def test_examples(self):\n']
        for i in range(1,121):
            unit,quantity,discount=i*37,i%5,i%4*1250
            expected=(unit*quantity*(10000-discount)+5000)//10000
            line=dict(unit_cents=unit,quantity=quantity,discount_bps=discount,active=True)
            rows.append('        self.assertEqual(total_payable('+repr([line])+'), '+str(expected)+')\n')
        rows.append('        self.assertEqual(total_payable([{\"unit_cents\":999,\"quantity\":5,\"active\":False}]), 0)\n')
        for folder in [root/'checks',*nested.parents]:
            if folder==root or root not in folder.parents:continue
            (folder/'__init__.py').touch()
        (nested/'__init__.py').touch();(nested/'test_totals.py').write_text(''.join(rows))
        spec='total_payable sums active lines only; active defaults true. Each line contributes unit_cents * quantity, discounted by optional integer discount_bps (default 0). Round each discounted line half-up to whole cents using integer arithmetic, then sum. Empty lists and zero quantities return zero. Inputs are nonnegative integer money/quantities and discount 0..10000.'
        first="rg -n 'assertEqual' checks"
        test='python3 -m unittest discover -s checks -p "test_*.py"'
        verify='from app import total_payable as f; assert f([])==0; assert f([dict(unit_cents=1,quantity=1,discount_bps=5000)])==1; assert f([dict(unit_cents=100,quantity=3),dict(unit_cents=999,quantity=5,active=False)])==300; assert f([dict(unit_cents=99,quantity=2,discount_bps=10000)])==0'
    elif case=='repeated-worker-log':
        (root/'app.py').write_text('def retry_delay(status, attempt, retry_after=None):\n    return None\n')
        (root/'test_retry.py').write_text('''import unittest
from app import retry_delay
class Retry(unittest.TestCase):
    def test_retry_statuses(self):
        for status in (408,429,500,502,503,504):
            self.assertEqual(retry_delay(status,0),1)
            self.assertEqual(retry_delay(status,3),8)
    def test_headers_and_cap(self):
        self.assertEqual(retry_delay(429,0,10),10)
        self.assertEqual(retry_delay(503,12),60)
    def test_nonretry(self):
        self.assertIsNone(retry_delay(200,2))
        self.assertIsNone(retry_delay(400,2))
''')
        (root/'diagnose.py').write_text('import unittest\nfor index in range(400):\n    print("INFO retry worker waiting for connection handshake completion; state unchanged",flush=True)\nunittest.main(module="test_retry",verbosity=2)\n')
        spec='retry_delay returns None for statuses other than 408,429,500,502,503,504. For retryable statuses and a nonnegative attempt index, exponential delay is 2**attempt capped at 60. A supplied nonnegative numeric retry_after raises the delay to at least that value, with the final value still capped at 60. Ignore negative retry_after. Return numeric seconds. Do not change diagnostic logging.'
        first='python3 diagnose.py'
        test='python3 -m unittest test_retry'
        verify='from app import retry_delay as f; assert f(418,0) is None; assert f(408,2)==4; assert f(429,1,-2)==2; assert f(503,1,2.5)==2.5; assert f(500,100)==60; assert f(504,0,100)==60'
    else:raise ValueError('Unknown case')
    prompt=f'''Fix app.py to meet this specification: {spec}
Start by running `{first}` with your normal shell tool and max_output_tokens=12000 to inspect the current examples/diagnostics.
Then inspect the source, edit app.py, and verify using `{test}`. Only app.py may be changed; do not change tests, fixtures, logs or instructions.
Use normal shell/edit tools; no analytics MCP or evidence-view tools. Finish with a concise explanation and verification result.
If output uses reversible grouping/repetition markers, interpret the provided representation; request the original retained source only if needed.
'''
    return prompt,verify,test


def run(directory,protocol_path):
    directory.mkdir(parents=True,exist_ok=False,mode=0o700)
    protocol=json.loads(protocol_path.read_text())
    (directory/'protocol.json').write_text(json.dumps(protocol,indent=2))
    manifest=dict(protocol_sha256=hashlib.sha256(protocol_path.read_bytes()).hexdigest(),
        implementation={name:hashlib.sha256((HERE/name).read_bytes()).hexdigest() for name in ('live_compression.py','progress_output.py','capture_proxy.py','live_harness_trial.py')},
        headroom=json.loads((HERE.parent/'config/headroom-subset.lock.json').read_text()),created=time.time())
    (directory/'manifest.json').write_text(json.dumps(manifest,indent=2))
    for case in protocol['cases']:
        for condition in case['order']:
            cell=directory/(case['id']+'--'+condition)
            prompt,verify,test=fixture(case['id'],cell)
            frozen={str(path.relative_to(cell)):hashlib.sha256(path.read_bytes()).hexdigest() for path in cell.rglob('*.py') if path.name!='app.py'}
            (cell/'prompt.txt').write_text(prompt);(cell/'frozen.json').write_text(json.dumps(frozen))
            policy='off' if condition=='raw' else 'headroom-lossless'
            command=[sys.executable,str(HERE/'codex_traced.py'),'--ttgl-compression',policy,'exec','--ignore-user-config',
                '--skip-git-repo-check','-C',str(cell),'-m',protocol['model'],'-s','workspace-write',
                '-c','model_providers.ttgl_capture.request_max_retries=0','-c','model_providers.ttgl_capture.stream_max_retries=0',
                '--json','--output-last-message',str(cell/'answer.md'),'-']
            (cell/'command.json').write_text(json.dumps(command));started=time.monotonic()
            with (cell/'agent.jsonl').open('w') as output:
                try:
                    result=subprocess.run(command,input=prompt,text=True,stdout=output,stderr=subprocess.STDOUT,timeout=420)
                    status=dict(exit_code=result.returncode)
                except subprocess.TimeoutExpired:status=dict(timeout=True)
            status.update(elapsed_seconds=time.monotonic()-started,policy=policy)
            (cell/'completion.json').write_text(json.dumps(status,indent=2));print(cell.name,json.dumps(status),flush=True)
            if status.get('timeout') or status.get('exit_code')!=0:
                raise RuntimeError('Stopped on failed/ambiguous invocation; no automatic repeat')
            preserved=all((cell/path).exists() and hashlib.sha256((cell/path).read_bytes()).hexdigest()==digest for path,digest in frozen.items())
            visible=subprocess.run(test,shell=True,cwd=cell,text=True,capture_output=True,timeout=30)
            independent=subprocess.run([sys.executable,'-c',verify],cwd=cell,text=True,capture_output=True,timeout=30)
            (cell/'operator-tests.txt').write_text(visible.stdout+visible.stderr+independent.stdout+independent.stderr)
            grade=dict(checks=dict(fixtures_unchanged=preserved,visible_tests=visible.returncode==0,independent_checks=independent.returncode==0),passed=preserved and visible.returncode==0 and independent.returncode==0)
            (cell/'grade.json').write_text(json.dumps(grade,indent=2))
    (directory/'complete.json').write_text(json.dumps(dict(cells=4,completed=time.time())))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory',type=Path)
    parser.add_argument('--protocol',type=Path,default=HERE.parent/'studies/live-harness-protocol-001.json')
    args=parser.parse_args();run(args.directory.resolve(),args.protocol)
