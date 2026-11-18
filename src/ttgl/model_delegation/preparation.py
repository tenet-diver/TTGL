"""Finite metadata-only eligibility controls; no model execution or retries."""
from pathlib import Path
import time
from .native_swe import extract_task, checkout_source, grade_candidate
from ..experience_routing.io import read, write_new, file_digest


def run(protocol):
    protocol = Path(protocol).resolve(); config=read(protocol)
    if config.get('allow_model_execution') is not False or config.get('automatic_retries') != 0:
        raise ValueError('Preparation-only registration required')
    for pin in config['source_pins']:
        if file_digest(Path(config['root'])/pin['path']) != pin['sha256']:
            raise ValueError('Frozen preparation source differs')
    output=Path(config['output']); output.mkdir(parents=True,exist_ok=False,mode=0o700)
    write_new(output/'started.json',{'protocol_sha256':file_digest(protocol),'native_model_calls':0})
    started=time.monotonic();results=[]
    review=read(config['image_review'])
    for task in config['tasks']:
        if time.monotonic()-started >= config['maximum_elapsed_seconds']:
            write_new(output/'stopped.json',{'reason':'finite preparation deadline','results':results,'native_model_calls':0})
            return
        folder=output/task['task_id']; folder.mkdir(mode=0o700)
        write_new(folder/'started.json',{'task_id':task['task_id'],'automatic_retries':0})
        record={'task_id':task['task_id'],'eligible':False,'model_calls':0,'controls':{}}
        try:
            assets=extract_task(config['task_archive'],task['task_id'],folder/'private-task')
            base=folder/'base';state=checkout_source(task['metadata']['repo'],task['metadata']['base_commit'],base)
            record['base_state_hash']=state['state_hash']
            for name in ('empty','reference'):
                grade=grade_candidate(task_directory=assets,base_source=base,candidate_source=base,
                    output=folder/name,image_review=review,grader_subset=config['grader_subset'],
                    reference=name=='reference',timeout=config['per_control_timeout'])
                record['controls'][name]={'resolved':grade['resolved'],'tests_observed':grade['tests_observed'],
                                         'grade_sha256':file_digest(folder/name/'grade.json')}
                if grade['resolved'] != (name=='reference'):
                    record['reason']='invalid_'+name+'_control';break
            record['eligible']=len(record['controls'])==2 and all(
                r['resolved']==(name=='reference') for name,r in record['controls'].items())
        except Exception as error:
            record['reason']=type(error).__name__
        write_new(folder/'completion.json',record);results.append(record)
        print({'task':task['task_id'],'eligible':record['eligible'],'completed':len(results),'total':len(config['tasks'])},flush=True)
    write_new(output/'completion.json',{'results':results,'native_model_calls':0,'elapsed_seconds':time.monotonic()-started})


if __name__=='__main__':
    import sys
    run(sys.argv[1])
