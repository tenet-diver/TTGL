#!/usr/bin/env python3
"""Validate current native resume counter semantics before amortized-memory trials."""
from pathlib import Path
import json,hashlib,os
from datetime import datetime,timezone
from longmemeval_codex_trial import native_command,run_process,Store
from native_jsonl import records,validate_native_completion
from cost_context_study import PRICING,REPO,price
HERE=Path(__file__).resolve().parent;ROOT=REPO/'work/security/context-memory-20261107/native-resume-metering-001'
def write(p,v):p.write_text(json.dumps(v,indent=2)+'\n')
def main():
    os.umask(0o077);ROOT.mkdir(mode=0o700);work=ROOT/'work';work.mkdir();protocol=HERE.parent/'studies/native-resume-metering-protocol-001.json';p=json.loads(protocol.read_text());(ROOT/'protocol.json').write_bytes(protocol.read_bytes())
    write(ROOT/'manifest.json',dict(at=datetime.now(timezone.utc).isoformat(),sources={str(f.relative_to(REPO)):hashlib.sha256(f.read_bytes()).hexdigest() for f in (Path(__file__),HERE/'native_jsonl.py',HERE/'longmemeval_codex_trial.py',HERE/'longitudinal_memory_trial.py',PRICING)}))
    sid=None;clis=[]
    try:
        for i,marker in enumerate(('METER_ONE','METER_TWO')):
            cell=ROOT/f'call-{i+1}';cell.mkdir();prompt='Reply exactly '+marker+'. Do not use tools, read files or make changes.';(cell/'prompt.txt').write_text(prompt);command=native_command(work,cell,p['model'])
            if sid:command[-1:]=['resume',sid,'-']
            run_process(command,prompt,cell,p['timeout_seconds']);actual=validate_native_completion(cell,no_tools=True)
            if sid and sid!=actual:raise ValueError('Resume changed thread identity')
            sid=actual
            if (cell/'answer.txt').read_text().strip()!=marker:raise ValueError('Wrong marker')
            clis.append(next(r['usage'] for r in records(cell) if r.get('type')=='turn.completed'))
        store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan()
        with store.connection() as db:
            turns=[r['turn_id'] for r in db.execute('SELECT turn_id FROM turns WHERE session_id=? ORDER BY start,turn_id',(sid,))]
            native=[dict(r) for r in db.execute("SELECT id,turn_id,usage FROM events WHERE session_id=? AND kind='generation'",(sid,))]
        if len(turns)!=2 or not native or len({r['id'] for r in native})!=len(native):raise ValueError('Ambiguous native turns/responses')
        for r in native:r['usage']=json.loads(r['usage'])
        keys=('input_tokens','cached_input_tokens','output_tokens','total_tokens');per=[{k:sum(r['usage'].get(k,0) for r in native if r['turn_id']==turn) for k in keys} for turn in turns];total={k:sum(u[k] for u in per) for k in keys}
        same=lambda a,b:all(a[k]==b[k] for k in keys[:3])
        if not same(clis[0],per[0]):raise ValueError('First CLI/native mismatch')
        semantics='cumulative-thread' if same(clis[1],total) else 'per-turn' if same(clis[1],per[1]) else None
        if semantics is None:raise ValueError('Unresolved current resume usage semantics')
        cost=sum(price(r['usage'],json.loads(PRICING.read_text())['primary_scenario']) for r in native)
        public=dict(id=p['id'],acceptance_passed=True,model_processes=2,cli_snapshots=clis,native_per_turn=per,unique_native_responses=len(native),native_total=total,resume_cli_semantics=semantics,credit_rate_scenario=cost,cash_cost=None,note='Transport/metering only; not task performance, cache efficiency or saving evidence. Deduplicate native responses; never add cumulative CLI snapshots.')
        write(ROOT/'results.json',dict(**public,session_id=sid,native_response_ids=[r['id'] for r in native]));write(ROOT/'complete.json',dict(acceptance_passed=True));write(HERE.parent/'studies/native-resume-metering-results-001.json',public);print(json.dumps(public,indent=2))
    except BaseException as e:write(ROOT/'stopped.json',dict(error=type(e).__name__,message=str(e),no_retry=True));raise
if __name__=='__main__':main()
