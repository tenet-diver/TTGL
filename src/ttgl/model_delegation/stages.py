"""Finite construction/development endpoint collection before frozen transfer.

Host controls and sealed grading remain separate from public generation and
annotation. A started/uncertain phase cannot be re-entered or silently retried.
"""
from pathlib import Path
import shutil
import time
from .episode import run_episode
from .knowledge import extract
from .native_swe import EvaluationInfrastructureFailure, grade_candidate, public_contract
from .accumulation import retrieve
from .retention import LocalS3Retention
from ..experience_routing.checkpoints import manifest
from ..experience_routing.io import read,write_new,file_digest,digest


def run(config_path):
    config_path=Path(config_path).resolve();config=read(config_path)
    if config['stage'] not in ('construction','development') or not config['allow_model_execution']:
        raise ValueError('Explicit endpoint collection stage required')
    root=Path(config['root']);output=Path(config['private_output_root'])
    if (output/'stage-started.json').exists():raise ValueError('Started phase requires audit, never automatic replay')
    if config.get('require_source_archive') is not True:
        raise ValueError('Endpoint stages require acknowledged exact source archival')
    archived=read(output/'source-archive-ready.json')
    if archived['protocol_sha256']!=file_digest(config_path) or not archived['archive'].get('artifactId'):
        raise ValueError('Exact source archive must be acknowledged before inference')
    for pin in config.get('grader_source_pins',[]):
        if file_digest(Path(config['grader_subset'])/pin['path'])!=pin['sha256']:
            raise ValueError('Original grader source drift')
    review=read(config['image_review']);sources={}
    for task in config['tasks']:
        folder=Path(task.get('control_root',config['eligibility_root']))/task['task_id']
        receipt=read(folder/'completion.json')
        if receipt['eligible'] is not True or file_digest(folder/'completion.json')!=task['control_sha256']:
            raise ValueError('Own frozen controls required')
        public=public_contract(folder/'private-task',folder/'base')
        if public['source_state_hash']!=receipt['base_state_hash']:raise ValueError('Pristine source drift')
        sources[task['task_id']]=(public,folder)
    write_new(output/'stage-started.json',{'registration_sha256':file_digest(config_path),'grades_sealed':True,'automatic_retries':0})
    client=LocalS3Retention(root,output/'registration-retention')
    client.retain_file(config_path,kind='endpoint-stage-registration',identity=config['stage'])
    started=time.monotonic();tokens=0;results=[];records=[];sequence=0
    def gate():
        if (tokens>=config['maximum_observed_total_tokens'] or
            time.monotonic()-started+config['per_call_seconds']>config['maximum_elapsed_seconds']):
            raise ValueError('Shared finite native stage budget exhausted')
    try:
        for task in config['tasks']:
            public,folder=sources[task['task_id']]
            packet={'experiences':[],'scope':'construction; no future experience'}
            if config['stage']=='development':
                snapshot=read(config['snapshot'])
                packet=retrieve(snapshot,{**public['features'],'task_id':public['task_id'],'goal':public['prompt']},maximum_bytes=config['maximum_packet_bytes'])
            # Task-blocked, deterministic alternating model order frozen before
            # observations. Both models always start from the same pristine base.
            order=list(config['models'])
            if int(digest(config['order_seed']+task['task_id'])[:8],16)%2:order.reverse()
            for model in order:
                gate();sequence+=1
                source=Path(config['candidate_root'])/task['task_id']/model/'source'
                shutil.copytree(folder/'base',source,ignore=shutil.ignore_patterns('.git'))
                episode=output/task['task_id']/model
                result=run_episode(root=root,output=episode,source=source,source_home=config['source_home'],
                    model=model,image_review=review,task=public,packet=packet,timeout_seconds=config['per_call_seconds'],
                    maximum_tool_calls=config['maximum_tool_calls'],registration=config_path)
                if result['status'] not in ('completed','public_failure'):raise ValueError('Uncertain native endpoint; phase stopped')
                if result['total_native_usage']['total_tokens'] is None:raise ValueError('Unknown endpoint usage')
                tokens+=result['total_native_usage']['total_tokens']
                row={'task_id':task['task_id'],'model':model,'episode':str(episode),'source':str(source),
                     'native_usage':result['total_native_usage'],'public_result':result['status'],
                     'invalid_paths':result['invalid_paths'],'packet_hash':result['packet_hash']}
                results.append(row)
                if config['stage']=='construction' and not result['invalid_paths']:
                    gate()
                    annotation=extract(root=root,output=output/task['task_id']/(model+'-annotation'),base=folder/'base',
                        candidate=source,episode=episode,task=public,source_home=config['source_home'],image_review=review,
                        registration=config_path,scope={**config['knowledge_scope'],'available_sequence':sequence})
                    tokens+=annotation['native_usage']['total_tokens'];records.extend(annotation['records'])
                write_new(output/task['task_id']/(model+'-collected.json'),row)
        # No hidden result is read until every public generation/annotation in
        # this registered phase finishes. Nothing from grades is sent to models.
        write_new(output/'generation-complete.json',{'results':results,'native_tokens':tokens,'records':records})
        graded=[]
        for result in results:
            _,folder=sources[result['task_id']]
            evaluation = Path(config['evaluation_root']) / result['task_id'] / result['model']
            try:
                grade = grade_candidate(
                    task_directory=folder / 'private-task', base_source=folder / 'base',
                    candidate_source=result['source'], output=evaluation,
                    image_review=review, grader_subset=config['grader_subset'],
                )
            except EvaluationInfrastructureFailure as error:
                graded.append({
                    **result, 'resolved': None, 'official_grade_sha256': None,
                    'grade_issue': type(error).__name__,
                })
            else:
                graded.append({
                    **result, 'resolved': grade['resolved'],
                    'official_grade_sha256': file_digest(evaluation / 'grade.json'),
                })
        final={'stage':config['stage'],'results':graded,'public_records':records,'native_tokens':tokens,
               'elapsed_seconds':time.monotonic()-started,'grades_supplied_to_models':False,'automatic_retries':0}
        write_new(output/'completion.json',final);return final
    except BaseException as error:
        write_new(output/'stopped.json',{'reason':type(error).__name__,'completed_results':results,'public_records':records,
            'native_tokens_lower_bound':tokens,'automatic_retries':0,'uncertain_assignment_must_not_repeat':True})
        raise


if __name__=='__main__':
    import sys
    run(sys.argv[1])
