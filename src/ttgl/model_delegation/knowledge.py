"""Public-only construction interpretation and independently replayed support.

The annotator is source-bound Luna; teacher attribution is preserved. A procedure
is not evidence of competence until its bounded public reproduction fails on the
base and passes on the integrated candidate. Official grades never enter here.
"""
from __future__ import annotations
import ast
import json
import shutil
from dataclasses import asdict
from pathlib import Path
from .transport import SubscriptionBackend
from .actor import ExactModeActor
from .retention import LocalS3Retention
from .admission import admit, claim
from ..experience_routing.backend import source_binding
from ..experience_routing.checkpoints import manifest
from ..experience_routing.io import read,write_new,file_digest,digest,now
from ..experience_routing.ledger import UsageLedger
from ..personal import Request

FIELDS={'goal':{'type':'string'},'subtask_type':{'type':'string'},
        'procedure':{'type':'array','items':{'type':'string'}},
        'acceptance_criteria':{'type':'array','items':{'type':'string'}},'check_code':{'type':'string'}}
SCHEMA={'type':'object','additionalProperties':False,'required':['records'],
        'properties':{'records':{'type':'array','items':{'type':'object','additionalProperties':False,
                       'required':list(FIELDS),'properties':FIELDS}}}}


def validate_check(code, *, project_modules=('sympy',)):
    if not isinstance(code,str) or len(code)>12000:raise ValueError('Bounded public check required')
    tree=ast.parse(code)
    if not any(isinstance(node,ast.Assert) for node in ast.walk(tree)):
        raise ValueError('Explicit public behavior assertion required')
    # Narrow reproduction language: arithmetic, SymPy, strings, containers and
    # assertions. No dynamic execution, IO/process access or unrelated packages.
    denied=(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef,ast.With,ast.AsyncWith,
            ast.Raise,ast.While,ast.Global,ast.Nonlocal,ast.Delete)
    banned={'open','exec','eval','compile','getattr','setattr','delattr','globals','locals','vars','input','breakpoint'}
    for node in ast.walk(tree):
        if isinstance(node,denied):raise ValueError('Unsupported reproduction statement')
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            names=[a.name for a in node.names] if isinstance(node,ast.Import) else [node.module or '']
            if getattr(node,'level',0) or any(n.split('.')[0] not in (*project_modules,'math','fractions','decimal','itertools','functools') for n in names):
                raise ValueError('Reproduction import outside reviewed graph')
        if isinstance(node,ast.Try):
            if node.finalbody or any(not isinstance(h.type,ast.Name) or h.type.id not in
                ('TypeError','ValueError','AttributeError','ZeroDivisionError','NotImplementedError','RuntimeError','AssertionError') for h in node.handlers):
                raise ValueError('Only explicit public behavior exceptions may be checked')
        if isinstance(node,ast.Name) and (node.id in banned or node.id.startswith('__')):
            raise ValueError('Dynamic/IO reproduction access')
        if isinstance(node,ast.Attribute) and node.attr.startswith('_'):
            raise ValueError('Private reproduction attribute access')
    return code


def verify_public_reproduction(code,*,base,candidate,output,image_review,project_modules=('sympy',)):
    code=validate_check(code,project_modules=project_modules);output=Path(output);output.mkdir(parents=True,exist_ok=False)
    wrapper="try:\n"+'\n'.join('    '+line for line in code.splitlines())+"\nexcept AssertionError:\n    raise SystemExit(17)\n"
    outcomes={}
    for label,original in [('base',base),('candidate',candidate)]:
        source=output/label
        shutil.copytree(original,source,ignore=shutil.ignore_patterns('.git'))
        check=source/'__observatory_public_proof__.py';check.write_text(wrapper);check.chmod(0o644)
        before=manifest(source)
        actor=ExactModeActor(image=image_review['image_id'],review=image_review,root=output/(label+'-actor'),identity=str(source),base_commit=before['state_hash'])
        result=actor.public_check(['python3','-B',check.name],source,30,raw_output=output/(label+'.raw'))
        client=LocalS3Retention(Path(__file__).resolve().parents[3],output/'raw-retention')
        client.retain_file(output/(label+'.raw'),kind='public-proof-raw',identity=str(output.resolve())+':'+label)
        outcomes[label]={k:v for k,v in result.items() if k!='output'}
        if result['infrastructure_error']:raise ValueError('Public proof infrastructure unresolved')
    return {'supported_positive':outcomes['base']['returncode']==17 and outcomes['candidate']['returncode']==0,
            'supported_negative':outcomes['base']['returncode']==17 and outcomes['candidate']['returncode']==17,
            'checks':outcomes,'scope':'Public generated assertion reproduction; not hidden task success or independent semantic oracle'}


def extract(*,root,output,base,candidate,episode,task,source_home,image_review,registration,scope):
    root,output,episode=Path(root),Path(output),Path(episode)
    parent=read(episode/'completion.json')
    if parent['status'] not in ('completed','public_failure') or parent['invalid_paths']:
        raise ValueError('Uncertain/out-of-scope parent cannot supply construction competence')
    binding=source_binding(source_home)
    frozen,spool,pin=admit(root,output,'gpt-6-luna',task['task_id'],binding,image_review['image_id'],120,registration)
    executable=str(Path(shutil.which('codex')).resolve())
    if file_digest(executable)!=frozen['codex_executable_sha256']:raise ValueError('Registered interpreter executable differs')
    client=LocalS3Retention(root,output/'retention')
    evidence=[]
    for path in sorted((episode/'tools').glob('*/started.json')):
        result=path.parent/'result.json'
        if result.exists():
            evidence.append({'id':path.parent.name,'arguments':read(path)['arguments'],
                             'exit_code':read(result)['exit_code'],'stdout':read(result)['stdout'][-6000:],
                             'stderr':read(result)['stderr'][-1000:]})
    public={'request':task['prompt'],'executor_model':parent['model'],'public_model_report':parent['model_report'],
            'public_tools':evidence,'public_pristine_check_passed':parent['public_check_passed']}
    payload=json.dumps(public)
    if len(payload.encode())>80000:raise ValueError('Public annotation evidence exceeds finite budget')
    prompt=('Interpret only this public construction attempt. Propose at most three bounded reusable subtask procedures supported by its observable attempts. Do not claim success, use private expected solutions or invent unseen checks. For each, supply a small standalone Python assertion reproduction of a behavior explicitly required by the public request, using SymPy/standard arithmetic imports only. The host will check it on the original base and final candidate. Use only subtask types implementation, exploration, verification, integration or planning. Procedures should explain transferable decisions and checks, without copying the candidate solution or embedding task identities. Return an empty records list if unsupported.\n'+payload)
    workspace=output/'empty-workspace';workspace.mkdir(parents=True,mode=0o700)
    backend=SubscriptionBackend(executable=executable,executable_sha256=file_digest(executable),source_home=source_home,
        source_account_hash=binding['account_hash'],output=output/'native',client=client)
    request=Request('public-annotation','gpt-6-luna','knowledge_construction',prompt,workspace,SCHEMA,120,read_only=True,reasoning_effort='low')
    client.retain_file(registration,kind='annotation-registration',identity=str(output))
    claim(spool,pin,str(output),frozen['maximum_invocations'])
    write_new(output/'model-started.json',{'request_hash':digest(prompt),'automatic_retries':0})
    response=backend.complete(request);write_new(output/'response.json',asdict(response))
    usage=UsageLedger(output/'accounting').record(request,response,'extraction','seed_construction',backend.last_native_artifact_hash,response_ids=backend.last_response_ids)
    if response.status!='completed' or response.tool_events or not usage['delta'].get('total_tokens'):
        raise ValueError('Uncertain annotation; no retry')
    proposals=json.loads(response.text)['records']
    if len(proposals)>3:raise ValueError('Annotation proposal count exceeds cap')
    admitted=[];excluded=[]
    for i,proposal in enumerate(proposals):
        try:
            if proposal['subtask_type'] not in ('implementation','exploration','verification','integration','planning'):
                raise ValueError('Unknown public subtask type')
            proof=verify_public_reproduction(proposal['check_code'],base=base,candidate=candidate,
                output=output/('proof-'+str(i)),image_review=image_review)
            receipt=write_new(output/('proof-'+str(i))/'verification.json',proof)
            client.retain_file(receipt,kind='public-proof',identity=str(output)+':'+str(i))
            if not (proof['supported_positive'] or proof['supported_negative']):raise ValueError('No supported public differential')
            stamp=now();ref=file_digest(receipt);model=parent['model']
            occurred=read(episode/'model-started.json')['started_at']
            identifier=digest([str(output),i,ref])
            record={**scope,'id':identifier,'task_id':task['task_id'],'goal':proposal['goal'],
                'subtask_type':proposal['subtask_type'],'category':task['features']['category'],
                'language':task['features']['language'],'constraints':task['features']['constraints'],
                'actions':task['features']['actions'],'visibility':'runtime_public','granularity':'subtask',
                'model':model,'executor_model':model,'assistance':'none','outcome_target':'public_integrated_completion',
                'verified':True,'verification_ref':ref,'source_current':True,'support_scope':'public_integrated',
                'outcome':'pass' if proof['supported_positive'] else 'fail','occurred_at':occurred,'verified_at':stamp,
                'available_at':stamp,'available_sequence':scope['available_sequence'],
                'interpretation':'Luna proposed public assertion; host differential replay supports only this check scope, not full task success',
                'guidance':{'id':identifier+'-procedure','supported':proof['supported_positive'],'source_model':model,
                    'procedure':proposal['procedure'],'preconditions':[],'acceptance_criteria':proposal['acceptance_criteria'],
                    'evidence_refs':[ref],'target_models':[]}}
            admitted.append(record)
        except ValueError as error:excluded.append({'index':i,'reason':str(error)})
    result={'records':admitted,'excluded':excluded,'native_usage':usage['delta'],'official_grades_used':False}
    write_new(output/'completion.json',result);return result
