import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from ttgl.model_delegation.accumulation import build_snapshots
from ttgl.model_delegation.campaign import NativeCampaignRunner, scenario_cost
from ttgl.experience_routing.checkpoints import manifest
from ttgl.experience_routing.io import write_new, read


class NativeCampaignTests(unittest.TestCase):
    def fixture(self, d):
        source = Path(d)/'source'; source.mkdir(); (source/'app.py').write_text('old = 1\n')
        task = {'task_id': 'dev', 'lineage_ids': ['dev'], 'prompt': 'Repair the collection utility',
                'features': {'subtask_type': 'implementation'}, 'source': str(source),
                'source_state_hash': manifest(source)['state_hash']}
        parts = {'construction': [], 'development': [task]}
        snapshot = build_snapshots(parts, [], prefixes=(0,), scope={'project': 'p', 'study': 's', 'account_hash': 'a'},
                                   watermark='2026-11-18T00:00:00Z')['snapshots'][0]
        config = {'maximum_packet_bytes': 8000, 'maximum_tool_calls': 8, 'per_call_timeout': 100,
                  'source_home': '/private/source', 'image_review': {}, 'registration': '/private/registration',
                  'delegation': {'context': {}}, 'publication_watermark': 0,
                  'rates': {m: {'input': .1, 'cached': .01, 'output': .5} for m in ('gpt-6-luna', 'gpt-6.1-sol')},
                  'routellm_thresholds': {'balanced': .5}}
        runner = NativeCampaignRunner(root=d, tasks={'dev': task}, snapshots={snapshot['snapshot_id']: snapshot}, config=config)
        assignment = {'task_id': 'dev', 'snapshot_id': snapshot['snapshot_id'], 'point': 'balanced',
                      'limits': {'maximum_invocations': 4, 'maximum_tokens': 1000, 'maximum_elapsed_seconds': 200}}
        return runner, assignment

    def solve(self, **kwargs):
        source = kwargs['source']; (source/'app.py').write_text('new = 2\n')
        write_new(Path(kwargs['output'])/'public-check.json', {'output': 'public checks pass'})
        worker = kwargs.get('delegation') is not None
        return {'status': 'completed', 'candidate_archive': {'sha256': 'artifact'}, 'candidate_hash': 'candidate',
                'changed_paths': ['app.py'], 'model_report': {'complete': True}, 'public_check_passed': True,
                'usage': {'maximum_invocations': 2 if worker else 1, 'maximum_tokens': 200 if worker else 100,
                          'maximum_elapsed_seconds': 2},
                'total_native_usage': {'input_tokens': 90, 'cached_input_tokens': 10, 'output_tokens': 10, 'total_tokens': 100}}

    def test_standalone_and_our_router_receive_equal_information(self):
        with tempfile.TemporaryDirectory() as d:
            runner, assignment = self.fixture(d)
            with patch('ttgl.model_delegation.campaign.run_episode', side_effect=self.solve) as execute:
                for system in ('luna', 'sol', 'observatory'):
                    runner({**assignment, 'system': system}, Path(d)/system)
                packets = [c.kwargs['packet'] for c in execute.call_args_list]
                self.assertEqual(packets[0], packets[1]); self.assertEqual(packets[1], packets[2])
                self.assertIsNotNone(execute.call_args_list[-1].kwargs['delegation'])
                self.assertEqual(read(Path(d)/'observatory/common-packet.json'), packets[0])

    def test_missing_released_baseline_never_falls_back(self):
        with tempfile.TemporaryDirectory() as d:
            runner, assignment = self.fixture(d)
            with patch('ttgl.model_delegation.campaign.run_episode') as execute:
                for system in ('routellm_native', 'frugalgpt_native'):
                    with self.assertRaises(ValueError): runner({**assignment, 'system': system}, Path(d)/system)
                execute.assert_not_called()

    def test_frugal_charges_both_candidates_with_same_packet_and_remaining_cap(self):
        with tempfile.TemporaryDirectory() as d:
            runner, assignment = self.fixture(d)
            class Cascade:
                def run(self, query, execute, limits):
                    import json
                    assert json.loads(query)['knowledge']['snapshot_id'] == assignment['snapshot_id']
                    first = execute('gpt-6-luna', query, limits)
                    second = execute('gpt-6.1-sol', query, {**limits, 'maximum_tokens': limits['maximum_tokens']-first['usage']['tokens']})
                    assert 'new = 2' in first['candidate_text']
            runner.frugalgpt_factory = lambda _: Cascade()
            with patch('ttgl.model_delegation.campaign.run_episode', side_effect=self.solve) as execute:
                result = runner({**assignment, 'system': 'frugalgpt_native'}, Path(d)/'frugal')
                self.assertEqual(result['usage']['maximum_tokens'], 200)
                self.assertEqual(result['usage']['maximum_invocations'], 2)
                self.assertEqual(execute.call_args_list[0].kwargs['packet'], execute.call_args_list[1].kwargs['packet'])

    def test_scratch_candidate_and_private_episode_paths_are_separate(self):
        with tempfile.TemporaryDirectory() as d:
            runner, assignment = self.fixture(d)
            runner.config['candidate_root'] = str(Path(d)/'scratch')
            with patch('ttgl.model_delegation.campaign.run_episode', side_effect=self.solve) as execute:
                runner({**assignment, 'system': 'luna'}, Path(d)/'private')
            self.assertTrue(execute.call_args.kwargs['source'].is_relative_to(Path(d)/'scratch'))
            self.assertTrue(execute.call_args.kwargs['output'].is_relative_to(Path(d)/'private'))

    def test_operating_point_without_distinct_frozen_policy_is_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            runner, assignment = self.fixture(d)
            with patch('ttgl.model_delegation.campaign.run_episode') as execute:
                with self.assertRaises(ValueError):
                    runner({**assignment, 'system': 'observatory', 'point': 'cost'}, Path(d)/'cost')
                execute.assert_not_called()

    def test_frozen_task_source_drift_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            runner, assignment = self.fixture(d)
            Path(runner.tasks['dev']['source'], 'app.py').write_text('changed\n')
            with self.assertRaises(ValueError): runner({**assignment, 'system': 'luna'}, Path(d)/'attempt')

    def test_scenario_rates_count_cached_input_once_and_preserve_unknown(self):
        rates = {'input': 2, 'cached': .1, 'output': 10}
        self.assertAlmostEqual(scenario_cost({'input_tokens': 100, 'cached_input_tokens': 50, 'output_tokens': 10}, rates), .000205)
        self.assertIsNone(scenario_cost({'input_tokens': None}, rates))
