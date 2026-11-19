"""Frozen five-system generation, then sealed independent artifact replay.

No scorer reads heldout outcomes; no grading starts until all registered native
assignments finish. Infeasible development points remain explicitly unrun.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
from .accumulation import run_campaign
from .campaign import NativeCampaignRunner
from .baseline_process import LocalBaselineProcess
from .baselines import RouteLLMNative,FrugalGPTNative
from .retention import LocalS3Retention
from .artifacts import restore_delta
from .scratch import release_candidate
from .native_swe import public_contract,grade_candidate
from ..experience_routing.io import read,write_new,file_digest,digest


class RecordedBaselineProcess(LocalBaselineProcess):
    def __init__(self,*args,evidence,client,**kwargs):
        self.evidence=Path(evidence);self.client=client;self.sequence=0
        super().__init__(*args,**kwargs)
        path=write_new(self.evidence/'setup.json',self.setup)
        self.client.retain_file(path,kind='local-baseline-setup',identity=str(self.evidence))

    def request(self,operation,**values):
        self.sequence+=1
        folder=self.evidence/str(self.sequence)
        request=write_new(folder/'request.json',{'operation':operation,**values})
        self.client.retain_file(request,kind='local-baseline-request',identity=str(folder))
        result=super().request(operation,**values)
        response=write_new(folder/'response.json',result)
        self.client.retain_file(response,kind='local-baseline-response',identity=str(folder))
        return result


def recorded_parent_deadline(folder):
    """Confirm a retained parent deadline before continuing another assignment."""
    attempts = sorted(Path(folder).glob('candidate-*/run'), key=lambda p: int(p.parent.name.split('-')[-1]))
    if not attempts:
        return None
    episode = attempts[-1]
    response_path = episode / 'response.json'
    stopped_path = episode / 'stopped.json'
    if not all(p.is_file() for p in (response_path, stopped_path, episode / 'model-started.json',
                                    episode / 'accounting/usage-ledger.jsonl')):
        return None
    response = read(response_path)
    stopped = read(stopped_path)
    if (response.get('status') != 'timeout' or response.get('error_type') != 'deadline'
            or not (stopped.get('quarantined_candidate') or {}).get('artifactId')
            or any((episode / 'tools/delegations').glob('*/worker/model-started.json'))):
        return None
    return {
        'status': 'native_timeout', 'verified_parent_deadline': True, 'usage': None,
        'episode_response_sha256': file_digest(response_path), 'episode_stopped_sha256': file_digest(stopped_path),
        'automatic_retry': False,
    }


def run(config_path):
    config_path=Path(config_path).resolve();config=read(config_path)
    root=Path(config['root']);output=Path(config['private_output_root'])
    if (output/'heldout-started.json').exists():raise ValueError('Started heldout unit cannot be repeated')
    ready=read(output/'source-archive-ready.json')
    if ready['protocol_sha256']!=file_digest(config_path) or not ready['archive'].get('artifactId'):
        raise ValueError('Acknowledged exact source archive required')
    for pin in config['source_pins']:
        if file_digest(root/pin['path'])!=pin['sha256']:raise ValueError('Frozen heldout source drift')
    for key in ('campaign', 'campaign_qualification', 'split', 'baseline_receipts',
                'snapshots', 'baseline_parameters', 'image_review'):
        if file_digest(config[key]) != config[key + '_sha256']:
            raise ValueError('Frozen held-out input differs: ' + key)
    campaign = read(config['campaign'])
    qualification = read(config['campaign_qualification'])
    if campaign['campaign_id']!=config['campaign_id']:raise ValueError('Frozen finite manifest differs')
    registered_policies = {
        'frugalgpt_native': config['frugalgpt_strategies'],
        'routellm_native': config['runtime']['routellm_thresholds'],
        'observatory': config['runtime'].get('delegation_by_point', {}),
    }
    for system, policy_pin in campaign['baseline_pins'].items():
        for point, expected in policy_pin.get('point_policy_sha256', {}).items():
            if digest(registered_policies[system][point]) != expected:
                raise ValueError('Runtime policy differs from its frozen point identity')
    scratch = Path(config['runtime']['candidate_root']).resolve()
    if not scratch.is_relative_to('/tmp'):
        raise ValueError('Owned held-out candidate scratch must be under /tmp')
    split=read(config['split']);evaluation_ids=[t['task_id'] for t in split['partitions']['heldout']]
    receipts=read(config['baseline_receipts'])
    if any(set(receipt['training_ids'])&set(evaluation_ids) for receipt in receipts.values()):
        raise ValueError('Heldout material in baseline training')
    snapshots={s['snapshot_id']:s for s in read(config['snapshots'])['snapshots']}
    tasks={}
    for task in split['partitions']['heldout']:
        folder=Path(config['eligibility_root'])/task['task_id']
        receipt = read(folder / 'completion.json')
        if receipt['eligible'] is not True or receipt != task['control_result']:
            raise ValueError('Own frozen controls required')
        public = public_contract(folder / 'private-task', folder / 'base')
        if public['source_state_hash'] != receipt['base_state_hash']:
            raise ValueError('Pristine held-out source drift')
        tasks[task['task_id']] = public
    scratch.mkdir(parents=True, exist_ok=True)
    if any(scratch.iterdir()):
        raise ValueError('Held-out scratch must be empty before the first admission')
    write_new(output/'heldout-started.json',{'registration_sha256':file_digest(config_path),'campaign_id':campaign['campaign_id'],
        'grades_sealed':True,'automatic_retries':0})
    client=LocalS3Retention(root,output/'retention')
    process=RecordedBaselineProcess(config['baseline_parameters'],config_sha256=config['baseline_parameters_sha256'],
        site=config['numeric_site'],native_libraries=config['native_libraries'],root=root,evidence=output/'local-baseline',client=client)
    try:
        router=RouteLLMNative(process.router(),receipts['routellm_native'],evaluation_ids=evaluation_ids)
        pins=read(config['baseline_parameters'])['pins']
        def cascade(point):
            strategy=config['frugalgpt_strategies'][point]
            if strategy is None:raise ValueError('Development-infeasible point cannot invoke a model')
            return FrugalGPTNative(process.cascade(pins,strategy),receipts['frugalgpt_native'],evaluation_ids=evaluation_ids)
        runtime={**config['runtime'],'registration':str(config_path),'source_home':config['source_home'],
                 'image_review':read(config['image_review'])}
        runner=NativeCampaignRunner(root=root,tasks=tasks,snapshots=snapshots,config=runtime,
                                   routellm=router,frugalgpt_factory=cascade)
        def execute(assignment, folder):
            before = len(process.measurements)
            try:
                result = runner(assignment, folder)
            except ValueError:
                deadline = recorded_parent_deadline(folder) if qualification.get('retain_recorded_timeouts') is True else None
                if deadline is None:
                    raise
                result = deadline
            result['local_scorer_operations'] = process.measurements[before:]
            return result

        def release_completed(assignment, folder, result):
            release = {
                'owned_root': scratch, 'cache': Path(config['replay_root']) / 'scratch-release-cache',
                'receipts': Path(folder) / 'scratch-release', 'client': client,
            }
            for index, attempt in enumerate(result['native_attempts']):
                release_candidate(runner.candidate_source(assignment, folder, index),
                                  attempt['candidate_archive'], **release)
            for worker in Path(folder).glob('candidate-*/run/tools/delegations/*/worker/completion.json'):
                checkpoint = scratch / digest(assignment) / 'workers' / worker.parent.parent.name / 'source'
                release_candidate(checkpoint, read(worker)['candidate_archive'], **release)

        run_campaign(campaign, output / 'generation', execute, qualification=qualification,
                     after_completion=release_completed)
        write_new(output/'all-generation-sealed.json',{'campaign_id':campaign['campaign_id'],
                  'native_assignments':read(output/'generation/completion.json'),'official_grades_read':False})
    except BaseException as error:
        write_new(output/'stopped.json',{'reason':type(error).__name__,'automatic_retry':False,
                  'started_or_uncertain_assignments_must_not_repeat':True})
        raise
    finally:
        process.close()
        client.retain_file(process.stderr_path,kind='local-baseline-stderr',identity=campaign['campaign_id'])
    # Restore exact retained bytes, independently of mutable working copies.
    cache=Path(config['replay_root'])/'archive-cache';cache.mkdir(parents=True,exist_ok=False)
    grades = {}
    for assignment in campaign['assignments']:
        ident = assignment['assignment_id']
        result = read(output / 'generation' / ident / 'completion.json')
        if result['status'] in ('unrun_infeasible', 'native_timeout'):
            grades[ident] = {'assignment_id': ident, 'status': result['status'],
                             'official_resolved': None, 'protocol_resolved': None}
            continue
        if result['status'] == 'duplicate_policy':
            original_grade = grades[result['shared_assignment_id']]
            grades[ident] = {**original_grade, 'assignment_id': ident, 'status': 'duplicate_policy',
                             'shared_assignment_id': result['shared_assignment_id']}
            continue
        archive = result['candidate_artifact']
        base = archive['base']['archive']
        base_path = cache / (base['sha256'] + '.gz')
        if not base_path.exists():
            client.restore_file(base, base_path)
        elif file_digest(base_path) != base['sha256']:
            raise ValueError('Retained base replay cache drift')
        folder = Path(config['eligibility_root']) / assignment['task_id']
        with TemporaryDirectory(prefix='sealed-replay-', dir=cache.parent) as directory:
            working = Path(directory)
            delta_path = client.restore_file(archive, working / 'candidate.delta.tar.gz')
            source = working / 'restored'
            restored = restore_delta(base_path.read_bytes(), delta_path.read_bytes(), source, artifact=archive)
            if restored['state_hash'] != result['candidate_hash']:
                raise ValueError('Independent replay source differs')
            evaluation = Path(config['evaluation_root']) / ident
            try:
                grade = grade_candidate(
                    task_directory=folder / 'private-task', base_source=folder / 'base',
                    candidate_source=source, output=evaluation, image_review=runtime['image_review'],
                    grader_subset=config['grader_subset'], scratch_source=working / 'grading-copy',
                )
            except Exception as error:
                grades[ident] = {'assignment_id': ident, 'status': 'evaluation_uncertain', 'reason': type(error).__name__,
                                 'official_resolved': None, 'protocol_resolved': None, 'automatic_retry': False}
            else:
                artifacts = {
                    name: client.retain_file(evaluation / name, kind='sealed-heldout-grade', identity=ident + ':' + name)
                    for name in ('grade.json', 'official-report.json')
                }
                last = result['native_attempts'][-1]
                grades[ident] = {
                    'assignment_id': ident, 'status': 'graded', 'official_resolved': grade['resolved'],
                    'protocol_resolved': bool(grade['resolved'] and not last['invalid_paths'] and last['public_check_passed']),
                    'scope_flags': last['invalid_paths'], 'public_check_passed': last['public_check_passed'],
                    'grade_sha256': file_digest(evaluation / 'grade.json'), 'grade_archives': artifacts,
                }
    final = {'campaign_id': campaign['campaign_id'], 'grades': list(grades.values()),
             'all_native_generation_finished_before_grading': True, 'cash_expense': None, 'automatic_retries': 0}
    completion = write_new(output / 'completion.json', final)
    client.retain_file(completion, kind='heldout-completion', identity=campaign['campaign_id'])
    return final


if __name__=='__main__':
    import sys
    run(sys.argv[1])
