import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from ttgl.experience_routing.io import write_new, file_digest
from ttgl.model_delegation.admission import admit, claim


class AdmissionTests(unittest.TestCase):
    def fixture(self, d):
        root = Path(d)
        spool = root/'work/security/native'
        spool.mkdir(parents=True)
        source = root/'worker.py'; source.write_text('pass\n')
        cfg = {'allow_model_execution': True, 'automatic_retries': 0, 'native_source_account_hash': 'source',
               'models': ['gpt-6-luna', 'gpt-6.1-sol'], 'task_ids': ['task'], 'image_id': 'image',
               'source_pins': [{'path': 'worker.py', 'sha256': file_digest(source)}],
               'maximum_invocations': 2, 'maximum_elapsed_seconds': 300, 'maximum_observed_total_tokens': 200000,
               'private_output_root': str(spool)}
        path = write_new(root/'registration.json', cfg)
        return root, spool, source, path

    def test_exact_registration_required_before_native_start(self):
        with tempfile.TemporaryDirectory() as d:
            root, spool, source, registration = self.fixture(d)
            args = [root, spool/'episode', 'gpt-6-luna', 'task', {'account_hash': 'source'}, 'image', 100]
            self.assertEqual(admit(*args, registration)[0]['maximum_invocations'], 2)
            with self.assertRaises(ValueError): admit(*args, None)
            for index, value in [(2, 'other-model'), (3, 'other-task'), (4, {'account_hash': 'other'}),
                                 (5, 'other-image'), (6, 301), (1, root/'outside')]:
                bad = list(args); bad[index] = value
                with self.subTest(index=index), self.assertRaises(ValueError): admit(*bad, registration)
            source.write_text('changed\n')
            with self.assertRaises(ValueError): admit(*args, registration)

    def test_concurrent_parent_worker_claims_share_one_nonresettable_budget(self):
        with tempfile.TemporaryDirectory() as d:
            _, spool, _, _ = self.fixture(d)
            def attempt(i):
                try: claim(spool, 'registration', str(i), 2); return True
                except ValueError: return False
            with ThreadPoolExecutor(max_workers=8) as pool:
                results = list(pool.map(attempt, range(8)))
            self.assertEqual(sum(results), 2)
            with self.assertRaises(ValueError): claim(spool, 'new-registration', 'new-id', 20)

    def test_uncertain_claim_never_repeated(self):
        with tempfile.TemporaryDirectory() as d:
            _, spool, _, _ = self.fixture(d)
            claim(spool, 'hash', 'started-native', 2)
            with self.assertRaises(ValueError): claim(spool, 'hash', 'started-native', 2)
