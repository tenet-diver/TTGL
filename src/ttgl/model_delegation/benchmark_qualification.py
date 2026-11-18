"""One explicitly registered benchmark transport/evaluation qualification pair.

No retries, policy tuning or inference from private grader feedback. Both
candidates finish before grading; this task is excluded from later transfer.
"""
from pathlib import Path
import shutil
from .episode import run_episode
from .native_swe import public_contract, grade_candidate
from .retention import LocalS3Retention
from ..experience_routing.checkpoints import manifest
from ..experience_routing.io import read, write_new, file_digest


def run(config_path):
    config_path = Path(config_path).resolve()
    config = read(config_path)
    root = Path(config['root'])
    output = Path(config['private_output_root'])
    if (output/'pair-started.json').exists():
        raise ValueError('Started qualification cannot be retried')
    for name, receipt in config['controls'].items():
        if file_digest(receipt['path']) != receipt['sha256']:
            raise ValueError('Own frozen control differs')
        record = read(receipt['path'])
        if record['resolved'] != (name == 'reference') or record['tests_observed'] < 1:
            raise ValueError('Own controls did not qualify')
    review = read(config['image_review'])
    task = public_contract(config['task_directory'], config['base_source'])
    if task['task_id'] not in config['task_ids'] or task['source_state_hash'] != config['source_state_hash']:
        raise ValueError('Registered benchmark source/task differs')
    write_new(output/'pair-started.json', {'registration_sha256': file_digest(config_path),
        'stage': 'qualification only; excluded from future transfer', 'automatic_retries': 0})
    archive = LocalS3Retention(root, output/'registration-retention')
    archive.retain_file(config_path, kind='benchmark-pair-registration', identity=config['stage'])
    results = []
    for model in config['models']:
        source = Path(config['candidate_root'])/model/'source'
        shutil.copytree(config['base_source'], source, ignore=shutil.ignore_patterns('.git'))
        result = run_episode(root=root, output=output/model, source=source,
            source_home=config['source_home'], model=model, image_review=review, task=task,
            packet={'experiences': [], 'scope': 'empty knowledge; matched public contract'},
            timeout_seconds=config['per_call_seconds'], maximum_tool_calls=config['maximum_tool_calls'],
            registration=config_path)
        if result['status'] not in ('completed', 'public_failure'):
            raise ValueError('Qualification uncertain; no fallback or retry')
        results.append((model,source,result))
    grades = []
    for model, source, result in results:
        grade = grade_candidate(task_directory=config['task_directory'],base_source=config['base_source'],
            candidate_source=source,output=Path(config['evaluation_root'])/model,image_review=review,
            grader_subset=config['grader_subset'])
        grades.append({'model':model,'resolved':grade['resolved'],'public_check_passed':result['public_check_passed'],
            'invalid_paths':result['invalid_paths'],'native_usage':result['total_native_usage'],
            'model_report':result['model_report'],'grade':grade})
    write_new(output/'pair-completion.json',{'scope':'one benchmark qualification pair; not main accumulation or baseline comparison',
        'results':grades,'model_invocations':len(results),'automatic_retries':0})
    return grades


if __name__ == '__main__':
    import sys
    run(sys.argv[1])
