import importlib.util
from pathlib import Path
import json
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('benchmark_http', Path(__file__).parents[1] / 'scripts/benchmark_http.py')
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class BenchmarkChecks(unittest.TestCase):
    def test_http_200_error_page_is_not_success(self):
        self.assertFalse(bench.inspect_response('/tasks', 200, b'Observatory data services are unavailable')['ok'])
        self.assertFalse(bench.inspect_response('/api/records/tasks', 503, b'{}')['ok'])

    def test_record_identity_and_pagination_are_checked(self):
        for rows in [[{'id': 'a'}, {'id': 'a'}], [{'id': str(n)} for n in range(21)], [{}]]:
            self.assertFalse(bench.inspect_response('/api/records/tasks', 200, json.dumps({'total': 30, 'rows': rows}).encode())['ok'])

    def test_empty_application_cannot_pass_readiness(self):
        def fake(base, path, timeout):
            check = {'ok': True, 'total': 0, 'identity_sha256': 'empty'} if '/api/records/' in path else {'ok': True}
            return {'latency_ms': 1, 'status': 200, 'response_bytes': 1, 'check': check}
        with patch.object(bench, 'request', side_effect=fake):
            result = bench.benchmark('http://127.0.0.1:3333', samples=2)
        self.assertFalse(result['data_ready'])
        self.assertFalse(result['checks_passed'])

    def test_changing_corpus_does_not_become_matched_evidence(self):
        counter = 0
        def fake(base, path, timeout):
            nonlocal counter
            counter += 1
            check = {'ok': True, 'total': 10, 'identity_sha256': str(counter)} if '/api/records/' in path else {'ok': True}
            return {'latency_ms': 1, 'status': 200, 'response_bytes': 1, 'check': check}
        with patch.object(bench, 'request', side_effect=fake):
            result = bench.benchmark('http://127.0.0.1:3333', samples=2)
        self.assertTrue(result['data_ready'])
        self.assertFalse(result['checks_passed'])

    def test_no_timing_samples_stays_unknown_and_remote_endpoints_are_rejected(self):
        self.assertIsNone(bench.percentile([], .95))
        with self.assertRaises(ValueError):
            bench.benchmark('https://example.com')


if __name__ == '__main__':
    unittest.main()
