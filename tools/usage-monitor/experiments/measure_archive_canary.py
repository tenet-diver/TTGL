#!/usr/bin/env python3
"""Read-only source/transport/usage audit; filename derives from registered identity."""
import argparse,hashlib,json
from pathlib import Path
from native_jsonl import records,validate_native_completion,meter_cell
from cost_context_study import PRICING,REPO
from longmemeval_codex_trial import Store

def audit(root,store):
    protocol=json.loads((root/'protocol.json').read_text())
    if protocol['id']!=root.name:raise ValueError('Protocol/artifact identity mismatch')
    cell=root/'reader';sid=validate_native_completion(cell);rates=json.loads(PRICING.read_text())['primary_scenario'];arm='reversible-shell-handles' if int(root.name.rsplit('-',1)[1])>=4 else 'reversible-handles'
    meter=meter_cell(store,cell,sid,dict(case='single-native-mechanism',condition=arm),rates);changes=[];raw_bypasses=0
    for path in (root/'captures').glob('*.json'):
        record=json.loads(path.read_text());request=record.get('request',{});forwarded=record.get('forwarded_request',request)
        for change in record.get('compression',{}).get('changes',[]):
            original=request
            for key in change['path']:original=json.loads(original) if key=='json' else original[key]
            digest=change['source_sha256'];source=json.loads((root/'captures/compression_sources'/(digest+'.json')).read_text())
            exact=hashlib.sha256(original.encode()).hexdigest()==digest==source['source_sha256']==source['retained_sha256']==hashlib.sha256(source['content'].encode()).hexdigest()
            if not exact:raise ValueError('Archive/source hash mismatch')
            changes.append(digest)
        for index,item in enumerate(request.get('input',[])):
            if item.get('type') in ('custom_tool_call_output','function_call_output') and 'TTGL_RAW_EVIDENCE' in json.dumps(item.get('output')):
                if item!=forwarded['input'][index]:raise ValueError('Raw retrieval changed')
                raw_bypasses+=1
    commands=[r['item'] for r in records(cell) if r.get('type')=='item.completed' and r.get('item',{}).get('type')=='command_execution'];recovery=[c for c in commands if 'read_compression_source' in c['command']];exits=[c.get('exit_code') for c in recovery]
    correct=json.loads((root/'complete.json').read_text())['answer_correct'];basic=bool(changes) and raw_bypasses>0 and correct and 0 in exits;clean=basic and exits==[0]
    passed=clean if root.name.endswith('-005') else basic
    public=dict(id=root.name,acceptance_passed=passed,answer_correct=correct,transformations=len(changes),unique_archived_sources=len(set(changes)),all_archived_sources_exact=bool(changes),raw_bypasses=raw_bypasses,recovery_attempts=len(recovery),recovery_exit_codes=exits,clean_installation_gate_passed=clean,native_reconciled=True,usage=meter['usage'],credit_rate_scenario=meter['cost'],cash_cost=None,note='Mechanism-only research expense, not quality/cost saving evidence.001–003 pass through without observable recovery schemas;004 needs path repair;005 uses fixed absolute scope. Preserve every failure and all added inference.')
    meter['quality']=dict(passed=passed,kind='Programmatic actual-request/source-hash/raw-recovery gate; not coding performance',clean_installation_gate_passed=clean)
    return dict(protocol=protocol,cells=[meter],mechanism=public,cash_cost=None),public

def measure(root,store):
    root=root.resolve()
    if (root/'measurement-001.json').exists():raise ValueError('Preserve completed measurement; no duplicate publication')
    private,public=audit(root,store)
    encoded=json.dumps(private,indent=2)+'\n';(root/'measurement-001.json').write_text(encoded)
    results=root/'results.json'
    if results.exists():
        backup=root/'results-before-canonical-001.json'
        if backup.exists():raise ValueError('Preserve earlier canonicalization')
        backup.write_bytes(results.read_bytes())
    results.write_text(encoded)
    output=REPO/'tools/usage-monitor/studies'/(root.name.replace('canary-','canary-results-')+'.json')
    if output.exists():
        prior=json.loads(output.read_text())
        if prior.get('id')!=root.name:raise ValueError('Public receipt identity mismatch; restore from owned private receipt before canonicalization')
    output.write_text(json.dumps(public,indent=2)+'\n');return public

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('directory',type=Path);args=ap.parse_args()
    store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');store.scan();print(json.dumps(measure(args.directory,store)))
if __name__=='__main__':main()
