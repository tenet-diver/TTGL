"""Draft validation and immutable execution freeze, with no model side effects."""
from __future__ import annotations
import math
from pathlib import Path
from .io import read,digest,file_digest,write_new

REQUIRED_PINS=('source_commit','model_catalog','task_manifest','exclusion_registry','runtime_isolation_manifest',
 'execution_fairness_manifest','readiness_manifest','rate_scenario','source_hashes','selection_rule')
REQUIRED_GATES=('dependency_review','source_binding','capture_roundtrip','native_metering','actor_boundary',
 'empty_control','reference_control','pristine_replay','reservation_audit')
CORE_ARMS=('L0','S0','LP0','LPM','SFM','HRM')


def load(path):
    path=Path(path)
    if path.suffix=='.json':return read(path)
    import yaml
    value=yaml.safe_load(path.read_text())
    if not isinstance(value,dict):raise ValueError('Study configuration must be an object')
    return value


def validate_config(config, *, root=None,execution=False):
    if config.get('schema_version')!=1 or not isinstance(config.get('study_id'),str):raise ValueError('Unsupported study configuration')
    if config.get('mode') not in ('frozen_memory','online','exact_repeat_diagnostic'):raise ValueError('Explicit study mode required')
    if config.get('automatic_retries')!=0:raise ValueError('Automatic invocation retries must remain zero')
    if config.get('models',{}).get('annotator')!='gpt-6-luna':raise ValueError('Source-bound Luna annotation is required')
    arms=config.get('arms',[])
    if not arms or any(a not in CORE_ARMS for a in arms) or len(set(arms))!=len(arms):raise ValueError('Unknown or duplicate core arm')
    missing=[];pins=config.get('pins',{})
    for key in REQUIRED_PINS:
        pin=pins.get(key)
        if not pin:missing.append('pin:'+key);continue
        if key=='source_commit':continue
        if not isinstance(pin,dict) or not pin.get('path') or not pin.get('sha256'):
            missing.append('pin:'+key);continue
        p=Path(pin['path'])
        if root and not p.is_absolute():p=Path(root)/p
        if not p.is_file() or file_digest(p)!=pin['sha256']:missing.append('changed_or_missing:'+key)
    budgets=config.get('budgets',{})
    for key in ('maximum_parent_assignments','maximum_invocations','maximum_model_tokens','maximum_elapsed_seconds'):
        n=budgets.get(key)
        if isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) or n<=0:missing.append('budget:'+key)
        elif key!='maximum_elapsed_seconds' and type(n) is not int:missing.append('integer_budget:'+key)
    for key in ('maximum_invocations','maximum_model_tokens','maximum_elapsed_seconds'):
        n=config.get('per_parent',{}).get(key)
        if isinstance(n,bool) or not isinstance(n,(int,float)) or not math.isfinite(n) or n<=0 or (key!='maximum_elapsed_seconds' and type(n) is not int):missing.append('per_parent_budget:'+key)
    for limits in (budgets,config.get('per_parent',{})):
        cost=limits.get('maximum_scenario_cost')
        if cost is not None and (isinstance(cost,bool) or not isinstance(cost,(int,float)) or not math.isfinite(cost) or cost<=0):missing.append('invalid_scenario_cost_cap')
    if config.get('maximum_large_fallbacks_per_node',1) not in (0,1) or config.get('maximum_parent_replans',1) not in (0,1):raise ValueError('Reference policy allows at most one fallback and one replan')
    if config.get('active_workers',1) not in (1,2,4,8):raise ValueError('Unsupported worker capacity')
    if root and isinstance(pins.get('readiness_manifest'),dict):
        p=Path(pins['readiness_manifest'].get('path',''))
        if not p.is_absolute():p=Path(root)/p
        if p.is_file():
            ready=read(p)
            for gate in REQUIRED_GATES:
                g=ready.get('gates',{}).get(gate)
                if not isinstance(g,dict) or g.get('passed') is not True or not g.get('receipt_sha256') or not g.get('receipt_path'):
                    missing.append('gate:'+gate);continue
                receipt=Path(g['receipt_path'])
                if not receipt.is_absolute():receipt=Path(root)/receipt
                if not receipt.is_file() or file_digest(receipt)!=g['receipt_sha256']:missing.append('gate_receipt:'+gate)
    elif execution:missing.extend('gate:'+g for g in REQUIRED_GATES)
    if root and isinstance(pins.get('source_hashes'),dict):
        manifest_path=Path(pins['source_hashes'].get('path',''))
        if not manifest_path.is_absolute():manifest_path=Path(root)/manifest_path
        if manifest_path.is_file():
            sources=read(manifest_path).get('files',{})
            if not sources:missing.append('empty_source_hashes')
            for name,expected in sources.items():
                path=Path(name)
                if not path.is_absolute():path=Path(root)/path
                if not path.is_file() or file_digest(path)!=expected:missing.append('source_changed:'+name)
    if execution and not config.get('allow_model_execution'):missing.append('model_execution_disabled')
    result={'valid_draft':True,'execution_ready':not missing,'missing':sorted(set(missing)),
            'configuration_hash':digest(config),'model_calls':0}
    if execution and missing:raise ValueError('Execution not qualified: '+', '.join(result['missing']))
    return result


def freeze(config_path,output):
    config=load(config_path);root=Path(config_path).resolve().parent
    validate_config(config,root=root,execution=True)
    repository=Path(__file__).resolve().parents[3]
    sources=[*Path(__file__).parent.glob('*.py'),repository/'src/ttgl/personal.py',
             repository/'tools/worker-mcp/server.mjs',repository/'tools/worker-mcp/package-lock.json',
             repository/'experiments/experience-routing-001/contracts.schema.json']
    source_hashes={str(p):file_digest(p) for p in sources}
    receipt={'schema_version':1,'study_id':config['study_id'],'config':config,'configuration_hash':digest(config),
             'configuration_file_sha256':file_digest(config_path),'implementation_hashes':source_hashes,'root':str(root),
             'automatic_retries':0,'model_calls':0}
    write_new(output,receipt);return receipt


def verify_freeze(frozen):
    if digest(frozen['config'])!=frozen['configuration_hash']:raise ValueError('Frozen configuration changed')
    for p,expected in frozen['implementation_hashes'].items():
        if file_digest(p)!=expected:raise ValueError('Frozen generation source changed: '+p)
    validate_config(frozen['config'],root=frozen['root'],execution=True)
    return frozen['config']
