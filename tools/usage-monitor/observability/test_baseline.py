import json
from pathlib import Path
import tempfile
import unittest

import baseline


class BaselineTests(unittest.TestCase):
    def report(self, records):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'session.jsonl'
            path.write_text(''.join(json.dumps(r) + '\n' for r in records))
            return baseline.summarize(path)

    def test_deduplicates_response_ids_and_excludes_other_threads(self):
        counts = dict(input_tokens=100, cached_input_tokens=80, output_tokens=10, reasoning_output_tokens=3, total_tokens=110)
        meta = {'type': 'session_meta', 'payload': {'id': 's', 'timestamp': '2026-11-05T00:00:00Z'}}
        row = {'type': 'token_usage_record', 'payload': {'thread_id': 's', 'response_id': 'r', 'usage': counts}}
        other = {'type': 'token_usage_record', 'payload': {'thread_id': 'other', 'response_id': 'other', 'usage': counts}}
        counter = {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {'total_token_usage': counts}}}
        result = self.report([meta, row, row, other, counter])
        self.assertEqual(result['unique_responses'], 1)
        self.assertEqual(result['usage']['total_tokens'], 110)
        self.assertEqual(result['fresh_input_tokens'], 20)
        self.assertEqual(set(result['cumulative_residual'].values()), {0})
        self.assertIsNone(result['actual_cost'])

    def test_conflicting_usage_stays_unaccounted(self):
        counts = dict(input_tokens=100, cached_input_tokens=80, output_tokens=10, reasoning_output_tokens=3, total_tokens=110)
        rows = [{'type': 'session_meta', 'payload': {'id': 's'}}]
        for usage in [counts, dict(counts, input_tokens=101)]:
            rows.append({'type': 'token_usage_record', 'payload': {'response_id': 'r', 'usage': usage}})
        result = self.report(rows)
        self.assertEqual(result['unique_responses'], 0)
        self.assertEqual(result['conflicting_response_ids'], ['r'])

    def test_native_thread_counter_reconciles_when_legacy_counter_lags(self):
        counts = dict(input_tokens=100, cached_input_tokens=80, output_tokens=10, reasoning_output_tokens=3, total_tokens=110)
        rows = [
            {'type': 'session_meta', 'payload': {'id': 's'}},
            {'type': 'event_msg', 'payload': {'type': 'token_count', 'info': {'total_token_usage': dict.fromkeys(counts, 0)}}},
            {'type': 'token_usage_record', 'payload': {'response_id': 'r', 'usage': counts, 'thread_token_usage': counts}},
        ]
        result = self.report(rows)
        self.assertEqual(set(result['cumulative_residual'].values()), {0})
        self.assertEqual(result['legacy_counter_residual']['total_tokens'], 110)
        self.assertEqual(result['reconciliation_basis'], 'token_usage_record.thread_token_usage')


if __name__ == '__main__':
    unittest.main()
