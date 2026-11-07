#!/usr/bin/env python3
"""Explicit unstarted-only continuation; frozen original generation is preserved."""
import argparse,fcntl,hashlib,json,os
from pathlib import Path
import time
from datetime import datetime,timezone
import longmemeval_codex_validation as base
from native_jsonl import records,validate_native_completion,meter_cell
from json_corpus import select_records
from cost_context_study import PRICING,REPO
from workspace import Store
HERE=Path(__file__).resolve().parent;ROOT=REPO/'work/security/context-memory-20261107';OLD=ROOT/'longmemeval-validation-002';NEW=ROOT/'longmemeval-validation-003'
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def check():
    base.frozen(OLD);m=json.loads((NEW/'manifest.json').read_text())
    if any(sha(REPO/f)!=h for f,h in m['sources'].items()):raise ValueError('Frozen continuation source changed')
    for name in ('plan','protocol','reservation'):
        if sha(NEW/(name+'.json'))!=m[name+'_sha256']:raise ValueError('Frozen continuation plan changed')
    for item in json.loads((NEW/'plan.json').read_text()):
        if item['reused']:
            p=Path(item['reader_artifact'])
            if sha(p/'agent.jsonl')!=item['stdout_sha256'] or sha(p/'answer.txt')!=item['answer_sha256']:raise ValueError('Reused answer/counters changed')
def prepare():
    os.umask(0o077);base.frozen(OLD)
    if list(OLD.glob('case-*/*/grade.json')):raise ValueError('Unexpected prior grading')
    NEW.mkdir(mode=0o700);protocol=HERE.parent/'studies/longmemeval-codex-validation-protocol-003.json';(NEW/'protocol.json').write_bytes(protocol.read_bytes());(NEW/'reservation.json').write_bytes((OLD/'reservation.json').read_bytes())
    p=json.loads(protocol.read_text());reservation=json.loads((NEW/'reservation.json').read_text())['heldout_reserved'];plan=[];seen=set();recovery=[]
    rates=json.loads(PRICING.read_text())['primary_scenario'];store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan()
    for index,c in enumerate(reservation):
        arms=p['conditions'];order=arms[index%3:]+arms[:index%3]
        for arm in order:
            old=OLD/f'case-{index:02d}'/arm;started=(old/'started.json').exists();item=dict(case=f'case-{index:02d}',index=index,question_id=c['id'],condition=arm,reused=started,reader_artifact=str(old if started else NEW/f'case-{index:02d}'/arm))
            if started:
                sid=validate_native_completion(old)
                if sid in seen:raise ValueError('Duplicate native thread')
                seen.add(sid)
                if json.loads((old/'completion.json').read_text()).get('exit_code')!=0:raise ValueError('Started reader not successful')
                if [r['item']['text'] for r in records(old) if r.get('type')=='item.completed' and r.get('item',{}).get('type')=='agent_message'][-1].strip()!=(old/'answer.txt').read_text().strip():raise ValueError('Final message mismatch')
                hist=old/'work/history'
                if any(sha(hist/f)!=h for f,h in json.loads((old/'history-sha256.json').read_text()).items()):raise ValueError('Raw corpus changed')
                item.update(stdout_sha256=sha(old/'agent.jsonl'),answer_sha256=sha(old/'answer.txt'),session_id=sid)
                recovery.append(meter_cell(store,old,sid,dict(case=item['case'],condition=arm,role='reader'),rates))
            elif (old/'agent.jsonl').exists() or (old/'answer.txt').exists():raise ValueError('Uncertain invocation without start marker')
            plan.append(item)
    if len(seen)!=61 or sum(not i['reused'] for i in plan)!=11:raise ValueError('Unexpected continuation boundary')
    if sha(ROOT/'longmemeval_s_cleaned.json')!=json.loads((OLD/'manifest.json').read_text())['data_sha256']:raise ValueError('Dataset changed')
    write(NEW/'plan.json',plan);write(NEW/'recovered-native.json',dict(cells=recovery,all_reconciled=True,model_calls=0))
    files=[Path(__file__),HERE/'native_jsonl.py',HERE/'longmemeval_codex_validation.py',HERE/'longmemeval_codex_trial.py',HERE/'longitudinal_memory_trial.py',HERE/'memory_retrieval.py',HERE/'json_corpus.py',HERE/'cost_context_study.py',PRICING]
    write(NEW/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),sources={str(f.relative_to(REPO)):sha(f) for f in files},**{name+'_sha256':sha(NEW/(name+'.json')) for name in ('plan','protocol','reservation')},reused_completed_readers=61,unstarted_readers=11,unstarted_judges=72))
    print('Registered61 reconciled existing readers;11 readers and72 judges unstarted.',flush=True)
def run():
    check();lock=(NEW/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    with (NEW/'started.json').open('x') as f:json.dump(dict(at=datetime.now(timezone.utc).isoformat(),pid=os.getpid()),f)
    p=json.loads((NEW/'protocol.json').read_text());plan=json.loads((NEW/'plan.json').read_text());rows=select_records(ROOT/'longmemeval_s_cleaned.json',[i['question_id'] for i in plan]);calls=0
    try:
        for item in plan:
            if item['reused']:continue
            check();cell=Path(item['reader_artifact']);cell.mkdir(parents=True,mode=0o700);work=cell/'work';work.mkdir();hist=work/'history';hist.mkdir();row=rows[item['question_id']];episodes=base.history(row)
            for e in episodes:(hist/(e['id']+'.txt')).write_text(e['body'])
            prompt=p['reader_common']+'\n\n'+json.dumps(dict(question_date=row['question_date'],question=row['question']),ensure_ascii=False)+'\n'
            if item['condition']=='full_history':prompt+='\nComplete supplied history follows:\n'+'\n\n'.join(e['body'] for e in episodes)
            elif item['condition']=='fts':
                t=time.perf_counter();hits=base.search(episodes,row['question'],limit=10,budget=12000);write(cell/'retrieval.json',dict(hits=hits,seconds=time.perf_counter()-t));prompt+='\nAutomatically retrieved exact prior-history excerpts (fallible, full files remain available):\n'+json.dumps(hits,ensure_ascii=False)
            (cell/'prompt.txt').write_text(prompt);write(cell/'history-sha256.json',{f.name:sha(f) for f in hist.iterdir()});base.run_process(base.native_command(work,cell,p['model']),prompt,cell,p['timeout_seconds_per_run']);calls+=1;validate_native_completion(cell)
            if any(sha(hist/f)!=h for f,h in json.loads((cell/'history-sha256.json').read_text()).items()):raise ValueError('Raw corpus changed')
            print('unstarted reader',item['index'],item['condition'],'complete',flush=True)
        write(NEW/'readers-complete.json',dict(cells=plan,model_processes_new=calls))
        for item in plan:
            check();cell=NEW/item['case']/item['condition']/'judge';cell.mkdir(parents=True,mode=0o700);prompt=base.judge_prompt(rows[item['question_id']],(Path(item['reader_artifact'])/'answer.txt').read_text());(cell/'prompt.txt').write_text(prompt)
            if calls>=p['maximum_new_model_processes']:raise ValueError('New model-process cap')
            base.run_process(base.native_command(cell,cell,p['judge_model']),prompt,cell,p['timeout_seconds_per_run']);calls+=1;validate_native_completion(cell,no_tools=True);label=(cell/'answer.txt').read_text().strip().lower()
            if label not in ('yes','no'):raise ValueError('Invalid judge label')
            write(cell.parent/'grade.json',dict(passed=label=='yes',kind='Local rubric prompt blinded; condition-coded cwd limitation; not programmatic truth'));print('registered rubric judge',calls-11,'complete',flush=True)
        write(NEW/'complete.json',dict(model_processes_new=calls,reused_completed_readers=61,total_model_processes=144,at=datetime.now(timezone.utc).isoformat()))
    except BaseException as e:write(NEW/'stopped.json',dict(error=type(e).__name__,message=str(e),new_completed_processes=calls,no_retries=True));raise

def measure():
    check()
    if not (NEW/'complete.json').exists():raise ValueError('Incomplete continuation')
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan();rates=json.loads(PRICING.read_text())['primary_scenario'];cells=[];p=json.loads((NEW/'protocol.json').read_text())
    for item in json.loads((NEW/'plan.json').read_text()):
        reader=Path(item['reader_artifact']);judge=NEW/item['case']/item['condition']/'judge';grade=json.loads((judge.parent/'grade.json').read_text());meta=dict(case=item['case'],condition=item['condition'])
        cells.append(meter_cell(store,reader,validate_native_completion(reader),dict(**meta,role='reader',grade=grade,reader_artifact=str(reader),reader_reused=item['reused']),rates));cells.append(meter_cell(store,judge,validate_native_completion(judge,no_tools=True),dict(**meta,role='judge_overhead'),rates))
    totals={arm:dict(task_credit_rate_scenario=sum(c['cost'] for c in cells if c['condition']==arm and c['role']=='reader'),task_native_tokens=sum(c['usage']['total_tokens'] for c in cells if c['condition']==arm and c['role']=='reader'),reader_successes=sum(c['grade']['passed'] for c in cells if c['condition']==arm and c['role']=='reader'),reader_count=24,judge_overhead_credits=sum(c['cost'] for c in cells if c['condition']==arm and c['role']=='judge_overhead')) for arm in p['conditions']}
    write(NEW/'results.json',dict(protocol=p,cells=cells,totals=totals,cash_cost=None,quota_saving=None,limitation='Original condition-coded grading paths disclosed; separately registered neutral audit required. Reused native response IDs counted once. Published-rate scenarios, not official scores/cash.'));print(json.dumps(totals,indent=2))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('action',choices=['prepare','run','measure']);a=ap.parse_args();globals()[a.action]()
