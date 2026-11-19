"""Frozen five-system generation, then sealed independent artifact replay.

No scorer reads heldout outcomes; no grading starts until all registered native
assignments finish. Infeasible development points remain explicitly unrun.
"""
from pathlib import Path
import json
from .accumulation import run_campaign
from .campaign import NativeCampaignRunner
from .baseline_process import LocalBaselineProcess
from .baselines import RouteLLMNative,FrugalGPTNative
from .retention import LocalS3Retention
from .artifacts import restore_delta
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


def run(config_path):
    config_path=Path(config_path).resolve();config=read(config_path)
    root=Path(config['root']);output=Path(config['private_output_root'])
    if (output/'heldout-started.json').exists():raise ValueError('Started heldout unit cannot be repeated')
    ready=read(output/'source-archive-ready.json')
    if ready['protocol_sha256']!=file_digest(config_path) or not ready['archive'].get('artifactId'):
        raise ValueError('Acknowledged exact source archive required')
    for pin in config['source_pins']:
        if file_digest(root/pin['path'])!=pin['sha256']:raise ValueError('Frozen heldout source drift')
    campaign=read(config['campaign']);qualification=read(config['campaign_qualification'])
    if campaign['campaign_id']!=config['campaign_id']:raise ValueError('Frozen finite manifest differs')
    split=read(config['split']);evaluation_ids=[t['task_id'] for t in split['partitions']['heldout']]
    receipts=read(config['baseline_receipts'])
    if any(set(receipt['training_ids'])&set(evaluation_ids) for receipt in receipts.values()):
        raise ValueError('Heldout material in baseline training')
    snapshots={s['snapshot_id']:s for s in read(config['snapshots'])['snapshots']}
    tasks={}
    for task in split['partitions']['heldout']:
        folder=Path(config['eligibility_root'])/task['task_id']
        if read(folder/'completion.json')['eligible'] is not True:raise ValueError('Own controls required')
        tasks[task['task_id']]=public_contract(folder/'private-task',folder/'base')
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
        def execute(assignment,folder):
            before=len(process.measurements)
            result=runner(assignment,folder)
            result['local_scorer_operations']=process.measurements[before:]
            return result
        run_campaign(campaign,output/'generation',execute,qualification=qualification)
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
    grades=[]
    for assignment in campaign['assignments']:
        ident=assignment['assignment_id'];result=read(output/'generation'/ident/'completion.json')
        if result['status']=='unrun_infeasible':
            grades.append({'assignment_id':ident,'status':'unrun_infeasible','official_resolved':None,'protocol_resolved':None})
            continue
        archive=result['candidate_artifact']
        base=archive['base']['archive'];bp=cache/(base['sha256']+'.gz')
        if not bp.exists():client.restore_file(base,bp)
        elif file_digest(bp)!=base['sha256']:raise ValueError('Retained base replay cache drift')
        dp=cache/(archive['sha256']+'.gz')
        if not dp.exists():client.restore_file(archive,dp)
        source=Path(config['replay_root'])/ident/'source'
        restored=restore_delta(bp.read_bytes(),dp.read_bytes(),source,artifact=archive)
        if restored['state_hash']!=result['candidate_hash']:raise ValueError('Independent replay source differs')
        folder=Path(config['eligibility_root'])/assignment['task_id']
        try:
            grade=grade_candidate(task_directory=folder/'private-task',base_source=folder/'base',candidate_source=source,
                output=Path(config['evaluation_root'])/ident,image_review=read(config['image_review']),grader_subset=config['grader_subset'])
            final=result['native_attempts'][-1]
            grades.append({'assignment_id':ident,'status':'graded','official_resolved':grade['resolved'],
                'protocol_resolved':bool(grade['resolved'] and not final['invalid_paths'] and final['public_check_passed']),
                'scope_flags':final['invalid_paths'],'public_check_passed':final['public_check_passed'],
                'grade_sha256':file_digest(Path(config['evaluation_root'])/ident/'grade.json')})
        except Exception as error:
            grades.append({'assignment_id':ident,'status':'evaluation_uncertain','reason':type(error).__name__,
                           'official_resolved':None,'protocol_resolved':None,'automatic_retry':False})
    final={'campaign_id':campaign['campaign_id'],'grades':grades,'all_native_generation_finished_before_grading':True,
           'cash_expense':None,'automatic_retries':0}
    write_new(output/'completion.json',final);return final


if __name__=='__main__':
    import sys
    run(sys.argv[1])
