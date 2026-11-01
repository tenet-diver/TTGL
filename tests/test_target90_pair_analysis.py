"""Audit joins must retain losing tasks and reject altered sealed artifacts."""
import importlib.util
import json
from pathlib import Path

import pytest

ROOT=Path(__file__).parents[1]
spec=importlib.util.spec_from_file_location('target90_analysis',ROOT/'scripts/analyze_target90_pair.py')
analysis=importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


def save(p,value):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(value))


@pytest.fixture(params=['v7','v8','v9'])
def complete_pair(tmp_path,request):
    version=request.param
    module={'v7':'src/ttgl/cost_quality_router.py','v8':'src/ttgl/completion_review_router.py','v9':'src/ttgl/evidence_decision_router.py'}[version]
    study=tmp_path/'study';rows=[];private=tmp_path/'private'
    common=ROOT/f'prompts/controller-{version}-common.txt';common_hash=analysis.pipeline.digest(common)
    rate_path=tmp_path/'rates.json'
    save(rate_path,{'models':{
        'gpt-6.1-sol':{'input_per_million':1,'cached_input_per_million':0.1,'output_per_million':2},
        'gpt-6-luna':{'input_per_million':0.1,'cached_input_per_million':0.01,'output_per_million':0.2}}})
    for arm,model,grade,cost in [('large','gpt-6.1-sol',1,0.00011),('optional','gpt-6-luna',0,0.000011)]:
        records=private/arm;usage={k:0 for k in analysis.pipeline.personal.USAGE_FIELDS}
        usage.update(input_tokens=100,output_tokens=5)
        manifest={'status':'completed_ungraded','expert_calls':0,'elapsed_seconds':1,
                  'usage':usage,'usage_by_model':{model:{'usage':usage}},'usage_accounting_issues':[],
                  'backend':{'controller_policy':{'mode':'consolidated-'+version,'common_sha256':common_hash}}}
        if version=='v9':manifest['backend']['controller_policy']['completion_evidence_schema_sha256']=analysis.pipeline.personal._digest(analysis.EVIDENCE_FIELDS)
        save(records/'controller/manifest.json',manifest)
        events=[{'event':'request','request_id':arm,'model':model,'kind':'controller'},
                {'event':'response','request_id':arm,'model':model,'kind':'controller',
                 'thread_id':arm+'-thread','status':'completed','usage_scope':'thread_cumulative',
                 'usage':usage,'usage_delta':usage,'usage_accounting_issues':[],'tool_events':[],
                 'text':json.dumps({'action':'complete','question':'','context':'','summary':'fixture'})}]
        if version=='v9':
            import hashlib
            decision={**json.loads(events[-1]['text']),'verification_status':'incomplete',
                      'acceptance_evidence':'existing checks','attempt_evidence':'candidate checked',
                      'material_gaps':'new behavior untested','escalation_reason':'unverified completion'}
            text=json.dumps(decision)
            save(records/'decision-evidence'/(analysis.pipeline.personal._digest(arm)+'.json'),
                 {'request_id':arm,'controller_policy':manifest['backend']['controller_policy'],
                  'decision':decision,'native_text':text,
                  'native_output_sha256':hashlib.sha256(text.encode()).hexdigest()})
        (records/'controller/events.jsonl').write_text('\n'.join(map(json.dumps,events)))
        (records/'visible-tool-trace.jsonl').write_text('')
        (records/'final.patch').write_text('sealed fixture patch')
        sealed=records/'sealed-replay-source'/'task';(sealed/'agent').mkdir(parents=True)
        (sealed/'agent/model.patch').write_text('sealed fixture patch')
        meta={'private_records_path':str(records),
              'manifest_sha256':analysis.pipeline.digest(records/'controller/manifest.json'),
              'final_patch_sha256':analysis.pipeline.digest(records/'final.patch'),
              'fresh_actor_boundary':{'status':'fresh_actor_boundary_passed_before_router_inference'}}
        native={'task_name':'swebench-pro/task','exception_info':None,'agent_result':{'metadata':meta},
                'verifier_result':{'rewards':{'reward':grade}},
                'started_at':'2026-10-31T00:00:00Z','finished_at':'2026-10-31T00:00:02Z',
                'agent_execution':{'started_at':'2026-10-31T00:00:00Z','finished_at':'2026-10-31T00:00:01Z'}}
        native_path=study/'jobs'/('first-block-'+arm)/'trial/result.json';save(native_path,native)
        save(sealed/'seal.json',{'native_result_sha256':analysis.pipeline.digest(native_path)})
        fresh=study/'jobs'/('first-block-'+arm+'-fresh')/'trial/result.json';save(fresh,native)
        save(fresh.parent/'agent/replay.json',{'patch':str(sealed/'agent/model.patch'),'apply_rc':0})
        rows.append({'task_id':'task','arm':arm,'resolved':bool(grade),'expert_requests_attempted':0,
                     'expert_calls':0,'pre_handoff_resolved':None,'cost_scenario_usd':cost,
                     'native_result':str(native_path),'private_manifest_sha256':meta['manifest_sha256']})
    save(study/'records.json',rows);save(study/'completion.json',{'development_assignments':2})
    protocol=tmp_path/'protocol.json'
    save(protocol,{'controller_policy_version':version,'task_id':'task','matched_pair_development':True,'scored_assignment_cap':2,
                   'first_block_order':['large','optional'],'assignment_claims':{
                       'large':str(tmp_path/'sol-claim'),'optional':str(tmp_path/'router-claim')},
                   'rate_scenario':str(rate_path),'source_sha256':{str(ROOT/p):analysis.pipeline.digest(ROOT/p) for p in
                       [module,f'prompts/controller-{version}-common.txt',
                        f'prompts/controller-{version}-routing.txt','src/ttgl/harbor_bridge.py']}})
    return study,protocol,private


def test_pair_audit_counts_all_cost_and_retains_quality_loss(complete_pair):
    study,protocol,_=complete_pair
    result,_=analysis.analyze(study,protocol)
    assert result['comparison']['sol_success_lost'] is True
    assert result['comparison']['scenario_saving']==pytest.approx(0.9)
    assert result['arms']['optional']['resolved']==0
    assert result['arms']['optional']['cost_per_resolved_usd'] is None
    assert result['arms']['optional']['cost_scenario_usd']==pytest.approx(0.000011)
    assert result['status']=='audited_development_pair_not_final_target_evidence'


def test_pair_audit_rejects_altered_final_patch(complete_pair):
    study,protocol,private=complete_pair
    (private/'optional/final.patch').write_text('changed after grading')
    with pytest.raises(ValueError,match='provenance'):
        analysis.analyze(study,protocol)


def test_pair_audit_rejects_wrong_registered_policy(complete_pair):
    study,protocol,_=complete_pair
    d=json.loads(protocol.read_text());d['controller_policy_version']='v8' if d['controller_policy_version']=='v7' else 'v7'
    # Supply the alternate files so rejection is a policy-mode check, not a missing key.
    v=d['controller_policy_version'];module={'v7':'src/ttgl/cost_quality_router.py','v8':'src/ttgl/completion_review_router.py','v9':'src/ttgl/evidence_decision_router.py'}[v]
    for name in [module,f'prompts/controller-{v}-common.txt',f'prompts/controller-{v}-routing.txt']:
        d['source_sha256'][str(ROOT/name)]=analysis.pipeline.digest(ROOT/name)
    save(protocol,d)
    with pytest.raises(ValueError,match='common guidance'):
        analysis.analyze(study,protocol)


def test_structured_evidence_is_exported_and_tampering_rejected(complete_pair):
    study,protocol,private=complete_pair
    if json.loads(protocol.read_text())['controller_policy_version']!='v9':pytest.skip('Only v9 has structured decision evidence')
    result,exports=analysis.analyze(study,protocol)
    assert result['arms']['optional']['structured_decisions'][0]['verification_status']=='incomplete'
    assert any(k.startswith('decision-evidence/') for k in exports['optional'])
    path=next((private/'optional/decision-evidence').glob('*.json'));d=json.loads(path.read_text())
    d['decision']['material_gaps']='changed';save(path,d)
    with pytest.raises(ValueError,match='native text changed'):
        analysis.analyze(study,protocol)
