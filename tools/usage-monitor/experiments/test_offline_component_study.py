import unittest
from offline_component_study import study

class ComponentStudy(unittest.TestCase):
    def test_oracle_recovery_and_accounting(self):
        result=study()
        self.assertEqual(len(result['results']),10)
        for row in result['results']:
            with self.subTest(case=row['case'],arm=row['arm']):
                self.assertEqual(row['checks_passed'],3 if row['arm']=='deterministic_projection' else 5)
                self.assertGreater(row['constructed_context_exposure_bytes'],0)
                self.assertIsNone(row['provider_tokens'])
                self.assertIsNone(row['model_task_quality'])
                self.assertIsNone(row['cost_saving'])
                if row['arm'] in ('baseline','deterministic_projection'):
                    self.assertEqual(row['oracle_recovery_calls'],0)
                else:
                    self.assertGreater(row['oracle_recovery_calls'],0)
                    self.assertGreater(row['oracle_recovery_bytes'],0)
