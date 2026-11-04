import unittest
from offline_context_probe import probe

class OfflineMechanisms(unittest.TestCase):
    def test_adapter_mechanisms(self):
        result = probe()
        for check in result['checks']:
            with self.subTest(check=check['name']):
                self.assertTrue(check['passed'])
        self.assertFalse(result['headroom_executed'])
        self.assertFalse(result['live_intervention_validated'])
        self.assertEqual(result['model_calls'], 0)
        self.assertIsNone(result['provider_usage'])
