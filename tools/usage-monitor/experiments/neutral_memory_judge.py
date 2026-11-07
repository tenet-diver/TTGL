#!/usr/bin/env python3
"""Condition-neutral-directory audit; never replace the frozen original grades."""
import argparse,hashlib,json,os
from pathlib import Path
import secrets,sys
from datetime import datetime,timezone
from longmemeval_codex_trial import judge_prompt,native_command,validate_native_completion,run_process,meter_cell
from json_corpus import select_records
from continue_longmemeval_validation import check as frozen_validation
from native_jsonl import validate_native_completion,meter_cell
from workspace import Store
from cost_context_study import PRICING,REPO
HERE=Path(__file__).resolve().parent;ROOT=REPO/'work/security/context-memory-20261107'
def write(path,data):path.write_text(json.dumps(data,indent=2)+'\n')
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def prepare():
    os.umask(0o077);original=ROOT/'longmemeval-validation-003'
    if list(original.glob('case-*/*/grade.json')):raise ValueError('Cannot claim pre-grade registration after grades exist')
    root=ROOT/'longmemeval-neutral-judge-audit-002';root.mkdir(mode=0o700)
    reservation=json.loads((original/'reservation.json').read_text())['heldout_reserved']
    plan=json.loads((ROOT/'longmemeval-neutral-judge-audit-001/plan.json').read_text());write(root/'plan.json',plan)
    protocol=HERE.parent/'studies/longmemeval-neutral-judge-audit-protocol-002.json'
    if json.loads(protocol.read_text())['id']!=root.name:raise ValueError('Protocol/root identity mismatch')
    (root/'protocol.json').write_bytes(protocol.read_bytes())
    files=[Path(__file__),HERE/'native_jsonl.py',HERE/'continue_longmemeval_validation.py',HERE/'longmemeval_codex_trial.py',HERE/'longmemeval_codex_validation.py',HERE/'json_corpus.py',HERE/'longitudinal_memory_trial.py',HERE/'cost_context_study.py']
    write(root/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),validation_grades_at_registration=0,plan_sha256=sha(root/'plan.json'),protocol_sha256=sha(root/'protocol.json'),sources={str(f.relative_to(REPO)):sha(f) for f in files}))
    print('Prepared72 anonymous assessments before any validation grades.')
def run():
    root=ROOT/'longmemeval-neutral-judge-audit-002';original=ROOT/'longmemeval-validation-003';m=json.loads((root/'manifest.json').read_text());p=json.loads((root/'protocol.json').read_text())
    if (root/'started.json').exists():raise ValueError('Never repeat a started audit')
    if not (original/'results.json').exists():raise ValueError('Original study must finish and reconcile before audit')
    frozen_validation()
    if sha(root/'plan.json')!=m['plan_sha256'] or sha(root/'protocol.json')!=m['protocol_sha256']:raise ValueError('Frozen audit plan changed')
    if any(sha(REPO/f)!=h for f,h in m['sources'].items()):raise ValueError('Frozen audit source changed')
    plan=json.loads((root/'plan.json').read_text());rows=select_records(ROOT/'longmemeval_s_cleaned.json',[c['question_id'] for c in plan]);inputs=[]
    sources={(c['case'],c['condition']):Path(c['reader_artifact']) for c in json.loads((original/'results.json').read_text())['cells'] if c['role']=='reader'}
    for item in plan:
        answer=sources[(item['case'],item['condition'])]/'answer.txt';cell=root/item['assessment'];cell.mkdir(mode=0o700)
        prompt=judge_prompt(rows[item['question_id']],answer.read_text());(cell/'prompt.txt').write_text(prompt)
        inputs.append(dict(**item,source_answer_sha256=sha(answer),prompt_sha256=sha(cell/'prompt.txt')))
    write(root/'inputs.json',inputs);write(root/'started.json',dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid(),inputs_sha256=sha(root/'inputs.json')))
    for n,item in enumerate(inputs):
        cell=root/item['assessment']
        if sha(cell/'prompt.txt')!=item['prompt_sha256']:raise ValueError('Changed audit input')
        run_process(native_command(cell,cell,p['model']),(cell/'prompt.txt').read_text(),cell,p['timeout_seconds']);validate_native_completion(cell,no_tools=True)
        label=(cell/'answer.txt').read_text().strip().lower()
        if label not in ('yes','no'):raise ValueError('Invalid label, preserve and stop')
        write(cell/'grade.json',dict(passed=label=='yes',kind='Same-model rubric in condition-neutral cwd; not programmatic ground truth'))
        print('anonymous assessment',n+1,'complete',flush=True)
    write(root/'complete.json',dict(processes=len(inputs),at=datetime.now(timezone.utc).isoformat()))
def measure():
    root=ROOT/'longmemeval-neutral-judge-audit-002';original=ROOT/'longmemeval-validation-003'
    if not (root/'complete.json').exists():raise ValueError('Audit incomplete')
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan();rates=json.loads(PRICING.read_text())['primary_scenario'];cells=[]
    for item in json.loads((root/'inputs.json').read_text()):
        cell=root/item['assessment'];grade=json.loads((cell/'grade.json').read_text());previous=json.loads((original/item['case']/item['condition']/'grade.json').read_text())
        cells.append(meter_cell(store,cell,validate_native_completion(cell,no_tools=True),dict(case=item['case'],condition=item['condition'],role='judge_overhead',grade=grade,original_grade=previous,disagrees=grade['passed']!=previous['passed']),rates))
    write(root/'results.json',dict(protocol=json.loads((root/'protocol.json').read_text()),cells=cells,research_credit_rate_scenario=sum(c['cost'] for c in cells),disagreements=sum(c['disagrees'] for c in cells),cash_cost=None))
    print('Measured',len(cells),'audit judgments.')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run','measure']);a=ap.parse_args();globals()[a.action]()
