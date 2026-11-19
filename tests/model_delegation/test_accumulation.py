import copy
import tempfile
import unittest
from pathlib import Path
from ttgl.model_delegation.accumulation import build_snapshots, retrieve, build_campaign, run_campaign


class AccumulationTests(unittest.TestCase):
    def setUp(self):
        self.partitions = {name: [{'task_id': name+str(i), 'lineage_ids': [name+'-lineage-'+str(i)]}
                                 for i in range(count)]
                           for name, count in [('construction', 4), ('development', 2), ('heldout', 2)]}
        self.scope = {'project': 'p', 'study': 's', 'account_hash': 'source'}
        self.records = [{**self.scope, 'id': str(i), 'task_id': 'construction'+str(i),
            'goal': 'repair parser edge cases', 'subtask_type': 'repair', 'constraints': ['python'],
            'actions': ['test'], 'visibility': 'runtime_public', 'verified': True, 'source_current': True,
            'verification_ref': 'check-'+str(i), 'support_scope': 'public_integrated',
            'outcome': 'fail' if i == 1 else 'pass', 'executor_model': 'luna',
            'occurred_at': '2026-11-01T00:00:00Z', 'verified_at': '2026-11-02T00:00:00Z',
            'available_at': '2026-11-03T00:00:00Z'} for i in range(4)]
        self.limits = {'maximum_invocations': 4, 'maximum_tokens': 100000, 'maximum_elapsed_seconds': 300}
        self.pins = {k: 'a'*64 for k in ('source_binding', 'actor', 'models', 'rates', 'controls', 'exclusions')}

    def snapshots(self, **kwargs):
        return build_snapshots(self.partitions, self.records, prefixes=(0, 2, 4), scope=self.scope,
                               watermark='2026-11-04T00:00:00Z', **kwargs)

    def campaign(self):
        return build_campaign(self.partitions, self.snapshots()['snapshots'], systems=('luna', 'sol', 'observatory'),
                              points=('cheap', 'balanced', 'quality'), limits=self.limits,
                              source_pins=self.pins, baseline_pins={})

    def test_nested_prefixes_count_failed_parents(self):
        snapshots = self.snapshots()['snapshots']
        self.assertEqual([s['construction_prefix'] for s in snapshots], [0, 2, 4])
        self.assertEqual([s['supporting_parents'] for s in snapshots], [0, 2, 4])
        self.assertEqual([s['failed_records'] for s in snapshots], [0, 1, 1])
        self.assertLess(set(r['id'] for r in snapshots[1]['experiences']), set(r['id'] for r in snapshots[2]['experiences']))

    def test_test_publications_never_enter_prefix(self):
        self.records.append({**self.records[0], 'id': 'heldout-record', 'task_id': 'heldout0'})
        result = self.snapshots()
        self.assertIn({'id': 'heldout-record', 'reason': 'not_construction'}, result['excluded'])

    def test_private_unverified_unintegrated_wrong_source_future_records_excluded(self):
        changes = [('visibility', 'private'), ('verified', False), ('support_scope', 'local_only'),
                   ('account_hash', 'other'), ('available_at', '2026-12-01T00:00:00Z')]
        for key, value in changes:
            with self.subTest(key=key):
                original = copy.deepcopy(self.records)
                self.records[0][key] = value
                self.assertEqual(len(self.snapshots()['snapshots'][-1]['experiences']), 3)
                self.records = original

    def test_duplicate_evidence_rejected(self):
        self.records.append(self.records[0])
        with self.assertRaises(ValueError): self.snapshots()

    def test_alias_and_lineage_leakage_rejected(self):
        for field, value in [('aliases', ['construction0']), ('lineage_ids', ['construction-lineage-0'])]:
            with self.subTest(field=field):
                before = copy.deepcopy(self.partitions)
                self.partitions['heldout'][0][field] = value
                with self.assertRaises(ValueError): self.snapshots()
                self.partitions = before

    def test_common_retrieval_is_identical_and_bounded(self):
        snapshot = self.snapshots()['snapshots'][-1]
        query = {'task_id': 'heldout0', 'goal': 'repair parser', 'subtask_type': 'repair'}
        a = retrieve(snapshot, query, maximum_bytes=1500)
        b = retrieve(snapshot, query, maximum_bytes=1500)
        self.assertEqual(a, b)
        from ttgl.experience_routing.io import canonical
        self.assertLessEqual(len(canonical(a).encode()), 1500)
        self.assertNotIn('selected_model', a)
        public = retrieve(snapshot, query, maximum_bytes=8000)
        self.assertTrue(public['experiences'])
        for record in public['experiences']:
            self.assertNotIn('task_id', record)
            self.assertEqual(len(record['source_parent_ref']), 64)

    def test_retrieval_refuses_self_and_drift(self):
        s = self.snapshots()['snapshots'][-1]
        with self.assertRaises(ValueError): retrieve(s, {'task_id': 'construction0'})
        s['experiences'][0]['outcome'] = 'fail'
        with self.assertRaises(ValueError): retrieve(s, {'task_id': 'heldout0'})

    def test_campaign_expands_points_without_duplicating_endpoints(self):
        c = self.campaign()
        self.assertEqual(len(c['assignments']), 30)
        self.assertEqual(c['maximum_totals']['maximum_invocations'], 120)
        self.assertEqual(len({a['assignment_id'] for a in c['assignments']}), 30)
        self.assertTrue(c['grades_sealed'])

    def test_named_baselines_cannot_be_silently_unqualified(self):
        with self.assertRaisesRegex(ValueError, 'baseline'):
            build_campaign(self.partitions, self.snapshots()['snapshots'], limits=self.limits,
                           source_pins=self.pins, baseline_pins={})

    def test_complete_comparison_expands_final_snapshot_points_once(self):
        from ttgl.model_delegation.accumulation import build_comparison_campaign
        pins = {k: {'qualified': True, 'implementation_sha256': 'b'*64, 'calibration_sha256': 'c'*64,
                    'training_partition': 'development', 'sufficiency_passed': True}
                for k in ('frugalgpt_native', 'routellm_native')}
        c = build_comparison_campaign(self.partitions, self.snapshots()['snapshots'], limits=self.limits,
            source_pins=self.pins, baseline_pins=pins, stage='heldout')
        self.assertEqual(len(c['assignments']), 34)
        self.assertEqual(len({r['assignment_id'] for r in c['assignments']}), 34)
        final = self.snapshots()['snapshots'][-1]['snapshot_id']
        self.assertTrue(all(r['snapshot_id'] == final for r in c['assignments'] if r['system'] in pins))

    def test_missing_and_unbounded_limits_rejected(self):
        for value in [None, 0, -1, True, float('inf')]:
            self.limits['maximum_tokens'] = value
            with self.assertRaises(ValueError): self.campaign()

    def test_infeasible_points_stay_registered_without_inference_or_invented_quality(self):
        from ttgl.model_delegation.accumulation import build_comparison_campaign
        from ttgl.experience_routing.io import read
        pins = {k: {'qualified': True, 'implementation_sha256': 'b'*64, 'calibration_sha256': 'c'*64,
                    'training_partition': 'development', 'sufficiency_passed': True,
                    'point_feasibility': {'cost': False}}
                for k in ('frugalgpt_native', 'routellm_native')}
        c = build_comparison_campaign(self.partitions, self.snapshots()['snapshots'], limits=self.limits,
            source_pins=self.pins, baseline_pins=pins, stage='heldout')
        calls=[]
        def execute(a,_):calls.append(a);return {'status':'public_failure','usage':a['limits']}
        q={'campaign_id':c['campaign_id'],'source_pins':c['source_pins'],'execution_ready':True}
        with tempfile.TemporaryDirectory() as d:
            run_campaign(c,d,execute,qualification=q)
            summary=read(Path(d)/'completion.json')
            self.assertEqual(summary['assignments_unrun_infeasible'],4)
            self.assertEqual(summary['assignments_completed'],len(c['assignments'])-4)
            for a in c['assignments']:
                if a.get('execution_disposition'):
                    result=read(Path(d)/a['assignment_id']/'completion.json')
                    self.assertIsNone(result['quality']);self.assertIsNone(result['scenario_cost'])

    def test_identical_points_reference_one_native_assignment_per_task(self):
        from ttgl.model_delegation.accumulation import build_comparison_campaign
        from ttgl.experience_routing.io import read
        pins = {system: {'qualified': True, 'implementation_sha256': 'b' * 64,
                         'calibration_sha256': 'c' * 64, 'training_partition': 'development',
                         'sufficiency_passed': True,
                         'point_policy_sha256': {point: 'd' * 64 for point in ('cost', 'balanced', 'quality')}}
                for system in ('frugalgpt_native', 'routellm_native')}
        campaign = build_comparison_campaign(
            self.partitions, self.snapshots()['snapshots'], limits=self.limits,
            source_pins=self.pins, baseline_pins=pins, stage='heldout',
        )
        by_id = {row['assignment_id']: row for row in campaign['assignments']}
        shared = [row for row in by_id.values() if row.get('execution_disposition') == 'duplicate_policy']
        self.assertEqual(len(by_id), 34)
        self.assertEqual(len(shared), 8)
        self.assertEqual(campaign['assignments_scheduled_for_native_execution'], 26)
        for row in shared:
            original = by_id[row['shared_assignment_id']]
            self.assertNotIn('execution_disposition', original)
            fields = ('task_id', 'snapshot_id', 'system')
            self.assertEqual([row[field] for field in fields], [original[field] for field in fields])
        with tempfile.TemporaryDirectory() as directory:
            calls = []
            def execute(assignment, _):
                calls.append(assignment['assignment_id'])
                return {'status': 'completed', 'usage': assignment['limits']}
            run_campaign(campaign, directory, execute, qualification={
                'execution_ready': True, 'campaign_id': campaign['campaign_id'], 'source_pins': campaign['source_pins'],
            })
            self.assertEqual(len(calls), 26)
            for row in shared:
                result = read(Path(directory) / row['assignment_id'] / 'completion.json')
                self.assertEqual(result['shared_assignment_id'], row['shared_assignment_id'])
                self.assertEqual(result['native_invocations'], 0)

    def test_native_campaign_requires_exact_qualification(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): run_campaign(self.campaign(), d, lambda *_: None, qualification={})
            self.assertFalse((Path(d)/'owner.json').exists())

    def test_started_assignment_never_retried(self):
        c = self.campaign()
        q = {'campaign_id': c['campaign_id'], 'source_pins': c['source_pins'], 'execution_ready': True}
        calls = []
        def uncertain(a, _):
            calls.append(a['assignment_id'])
            return {'status': 'uncertain'}
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError): run_campaign(c, d, uncertain, qualification=q)
            with self.assertRaises(FileExistsError): run_campaign(c, d, uncertain, qualification=q)
            self.assertEqual(len(calls), 1)
            self.assertEqual(len(list(Path(d).glob('*/stopped.json'))), 1)

    def test_registered_recorded_deadline_leaves_later_assignments_runnable(self):
        from ttgl.experience_routing.io import read
        campaign = self.campaign()
        qualification = {'campaign_id': campaign['campaign_id'], 'execution_ready': True,
                         'source_pins': campaign['source_pins'], 'retain_recorded_timeouts': True}
        seen = []

        def execute(assignment, _):
            seen.append(assignment['assignment_id'])
            if len(seen) == 1:
                return {'status': 'native_timeout', 'verified_parent_deadline': True, 'usage': None}
            return {'status': 'completed', 'usage': assignment['limits']}

        with tempfile.TemporaryDirectory() as directory:
            run_campaign(campaign, directory, execute, qualification=qualification)
            self.assertEqual(len(seen), len(campaign['assignments']))
            self.assertEqual(len(seen), len(set(seen)))
            first = read(Path(directory) / seen[0] / 'completion.json')
            self.assertIsNone(first['usage'])
            summary = read(Path(directory) / 'completion.json')
            self.assertEqual(summary['assignments_native_timeout'], 1)
            self.assertEqual(summary['assignments_completed'], len(seen) - 1)

    def test_metered_elapsed_overrun_keeps_usage_and_allows_next_assignment(self):
        from ttgl.experience_routing.io import read
        campaign = self.campaign()
        qualification = {'campaign_id': campaign['campaign_id'], 'execution_ready': True,
                         'source_pins': campaign['source_pins'], 'retain_metered_wall_overruns': True}
        seen = []

        def execute(assignment, _):
            seen.append(assignment['assignment_id'])
            usage = dict(assignment['limits'])
            if len(seen) == 1:
                usage['maximum_elapsed_seconds'] += 1
            return {'status': 'completed', 'usage': usage}

        with tempfile.TemporaryDirectory() as directory:
            run_campaign(campaign, directory, execute, qualification=qualification)
            self.assertEqual(len(seen), len(campaign['assignments']))
            result = read(Path(directory) / seen[0] / 'completion.json')
            self.assertEqual(result['status'], 'budget_rejected')
            cap = campaign['assignments'][0]['limits']['maximum_elapsed_seconds']
            self.assertEqual(result['usage']['maximum_elapsed_seconds'], cap + 1)
            self.assertEqual(read(Path(directory) / 'completion.json')['assignments_budget_rejected'], 1)

    def test_complete_campaign_retains_public_failures_without_grading(self):
        c = self.campaign()
        q = {'campaign_id': c['campaign_id'], 'source_pins': c['source_pins'], 'execution_ready': True}
        with tempfile.TemporaryDirectory() as d:
            run_campaign(c, d, lambda a, _: {'status': 'public_failure', 'usage': a['limits']}, qualification=q)
            self.assertTrue((Path(d)/'completion.json').exists())

    def test_hidden_grades_and_missing_usage_stop_execution(self):
        c = self.campaign()
        q = {'campaign_id': c['campaign_id'], 'source_pins': c['source_pins'], 'execution_ready': True}
        for result in [{'status': 'completed', 'usage': self.limits, 'resolved': True},
                       {'status': 'completed', 'usage': {}}]:
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ValueError): run_campaign(c, d, lambda *_: result, qualification=q)
