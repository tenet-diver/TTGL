"""Benchmark field projection and independent evaluator adapters, no new grader."""
from __future__ import annotations
from pathlib import Path
import json
import subprocess
import time
from .io import digest,file_digest,write_new,read

PUBLIC_FIELDS={'task_id','repo','base_commit','prompt','family','published_at','leakage_group','public_check_catalog','protected_paths'}
FORBIDDEN_FIELDS={'patch','test_patch','gold_patch','reference_solution','solution','hidden_tests','FAIL_TO_PASS','PASS_TO_PASS','resolved','reward','grade'}


def public_task(record):
    # Project known fields; never pass source dataset dictionaries to an actor.
    source=dict(record)
    if 'problem_statement' in source and 'prompt' not in source:source['prompt']=source['problem_statement']
    if 'instance_id' in source and 'task_id' not in source:source['task_id']=source['instance_id']
    missing=[k for k in ('task_id','repo','base_commit','prompt') if not isinstance(source.get(k),str) or not source[k]]
    if missing:raise ValueError('Public task requires '+', '.join(missing))
    return {k:v for k,v in source.items() if k in PUBLIC_FIELDS}


def assert_exposure(task,registry):
    if task['task_id'] in registry.get('task_ids',[]):raise ValueError('Historical/reserved instance is not a fresh task')
    if task.get('leakage_group') in registry.get('leakage_groups',[]):raise ValueError('Excluded issue, commit or synthetic-source family')
    return True


def pinned_evaluator(command,*,command_hash,patch_manifest,output,timeout):
    """Invoke an operator-frozen existing official/pristine replay command.

    The evaluator owns private tests and returns its original JSON receipt. Runtime
    publication APIs never receive this output. Regrades require a new output ID.
    """
    if digest(command)!=command_hash or not isinstance(command,list) or not command:
        raise ValueError('Evaluator command pin mismatch')
    manifest=read(patch_manifest)
    artifact=Path(manifest['artifact_path'])
    if file_digest(artifact)!=manifest['artifact_sha256']:raise ValueError('Sealed candidate bytes changed')
    output=Path(output)
    if output.exists():raise ValueError('Existing evaluator attempt must not be overwritten')
    output.mkdir(parents=True)
    write_new(output/'started.json',{'command_hash':command_hash,'artifact_hash':manifest['artifact_sha256'],
                                     'evaluator_revision':manifest['evaluator_revision'],'automatic_retries':0})
    started=time.monotonic()
    with (output/'stdout.json').open('xb') as stdout,(output/'stderr.log').open('xb') as stderr:
        result=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=timeout)
    if result.returncode:raise RuntimeError('Evaluator infrastructure error; original output retained')
    raw=read(output/'stdout.json')
    if raw.get('tests_collected',0)<=0 or raw.get('artifact_sha256')!=manifest['artifact_sha256'] or raw.get('evaluator_revision')!=manifest['evaluator_revision']:
        raise ValueError('A grade requires nonempty prescribed checks and matching artifact/evaluator identities')
    if type(raw.get('passed')) is not bool:raise ValueError('Independent verdict is missing')
    receipt={'original_report':str(output/'stdout.json'),'original_report_sha256':file_digest(output/'stdout.json'),
             'artifact_sha256':manifest['artifact_sha256'],'passed':raw['passed'],'tests_collected':raw['tests_collected'],
             'evaluator_revision':raw['evaluator_revision'],'elapsed_seconds':time.monotonic()-started,
             'visibility':'evaluation_sealed','scope':manifest.get('score_label','Observatory-derived diagnostic')}
    write_new(output/'grade.json',receipt);return receipt


def official_swe_grade(study,private_root,image,dataset,arm,instance,timeout=1200):
    # Lazy import avoids installing the old NumPy research stack for model-free
    # experience commands. A qualified official-evaluator environment supplies it.
    from ..evaluation import OfficialEvaluator
    evaluator=OfficialEvaluator(Path(study),Path(private_root),image,Path(dataset),timeout)
    evaluator(arm,instance)
    return read(evaluator.index_path)[arm][instance]
