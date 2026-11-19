import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ttgl.experience_routing.io import read,write_new,file_digest
from ttgl.model_delegation.native_swe import EvaluationInfrastructureFailure
from ttgl.model_delegation.stages import run


class StageTests(unittest.TestCase):
    def fixture(self,p,cap=100):
        controls=p/'controls/task';(controls/'base').mkdir(parents=True)
        (controls/'base/app.py').write_text('a=1\n')
        control=write_new(controls/'completion.json',{'eligible':True,'base_state_hash':'base'})
        review=write_new(p/'review.json',{'image_id':'image'})
        cfg={'stage':'construction','allow_model_execution':True,'root':str(p),
             'private_output_root':str(p/'output'),'image_review':str(review),'tasks':[{'task_id':'task','control_sha256':file_digest(control)}],
             'eligibility_root':str(p/'controls'),'maximum_observed_total_tokens':cap,'per_call_seconds':60,
             'maximum_elapsed_seconds':600,'models':['gpt-6-luna','gpt-6.1-sol'],'order_seed':'frozen',
             'candidate_root':str(p/'candidates'),'source_home':str(p),'maximum_tool_calls':4,
             'knowledge_scope':{'project':'Observatory'},'evaluation_root':str(p/'evaluation'),'grader_subset':str(p/'grader')}
        cfg['require_source_archive']=True
        path=write_new(p/'registration.json',cfg)
        write_new(p/'output/source-archive-ready.json',{'protocol_sha256':file_digest(path),'archive':{'artifactId':'fixture'}})
        return path

    def test_missing_source_archive_stops_before_model_or_started_assignment(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);config=self.fixture(p)
            (p/'output/source-archive-ready.json').unlink()
            with patch('ttgl.model_delegation.stages.run_episode') as model:
                with self.assertRaises(FileNotFoundError):run(config)
                model.assert_not_called()
            self.assertFalse((p/'output/stage-started.json').exists())

    def test_no_grading_until_every_public_endpoint_and_annotation_finishes(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);config=self.fixture(p);events=[]
            def solve(**kwargs):
                events.append('generation')
                return {'status':'completed','invalid_paths':[],'total_native_usage':{'total_tokens':10},'packet_hash':'common'}
            def annotate(**kwargs):events.append('annotation');return {'records':[],'native_usage':{'total_tokens':5}}
            def grade(**kwargs):
                events.append('grade');write_new(Path(kwargs['output'])/'grade.json',{'resolved':False});return {'resolved':False}
            with patch('ttgl.model_delegation.stages.public_contract',return_value={'task_id':'task','source_state_hash':'base'}), \
                 patch('ttgl.model_delegation.stages.LocalS3Retention'), \
                 patch('ttgl.model_delegation.stages.run_episode',side_effect=solve), \
                 patch('ttgl.model_delegation.stages.extract',side_effect=annotate), \
                 patch('ttgl.model_delegation.stages.grade_candidate',side_effect=grade):
                result=run(config)
                with self.assertRaises(ValueError):run(config)
            self.assertEqual(events,['generation','annotation','generation','annotation','grade','grade'])
            self.assertEqual(result['native_tokens'],30)
            self.assertFalse(result['grades_supplied_to_models'])

    def test_shared_budget_stops_before_another_annotation_or_model_call(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);config=self.fixture(p,cap=10)
            with patch('ttgl.model_delegation.stages.public_contract',return_value={'task_id':'task','source_state_hash':'base'}), \
                 patch('ttgl.model_delegation.stages.LocalS3Retention'), \
                 patch('ttgl.model_delegation.stages.run_episode',return_value={'status':'completed','invalid_paths':[],
                     'total_native_usage':{'total_tokens':10},'packet_hash':'common'}) as model, \
                 patch('ttgl.model_delegation.stages.extract') as annotation, \
                 patch('ttgl.model_delegation.stages.grade_candidate') as grader:
                with self.assertRaises(ValueError):run(config)
            self.assertEqual(model.call_count,1);annotation.assert_not_called();grader.assert_not_called()
            self.assertEqual(read(p/'output/stopped.json')['native_tokens_lower_bound'],10)

    def test_evaluation_infrastructure_failure_preserves_later_grade(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self.fixture(root)
            episode = {'status': 'completed', 'invalid_paths': [],
                       'total_native_usage': {'total_tokens': 10}, 'packet_hash': 'common'}
            seen = []

            def grade(**kwargs):
                seen.append(kwargs['output'])
                if len(seen) == 1:
                    raise EvaluationInfrastructureFailure('deadline')
                write_new(kwargs['output'] / 'grade.json', {'resolved': True})
                return {'resolved': True}

            with (
                patch('ttgl.model_delegation.stages.public_contract',
                      return_value={'task_id': 'task', 'source_state_hash': 'base'}),
                patch('ttgl.model_delegation.stages.LocalS3Retention'),
                patch('ttgl.model_delegation.stages.run_episode', return_value=episode),
                patch('ttgl.model_delegation.stages.extract',
                      return_value={'records': [], 'native_usage': {'total_tokens': 5}}),
                patch('ttgl.model_delegation.stages.grade_candidate', side_effect=grade),
            ):
                result = run(config)

            self.assertEqual(len(seen), 2)
            self.assertIsNone(result['results'][0]['resolved'])
            self.assertIsNone(result['results'][0]['official_grade_sha256'])
            self.assertTrue(result['results'][1]['resolved'])
