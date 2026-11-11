"""Counter pitfalls that would invalidate a team-cost comparison."""
import unittest

from codex_team_evidence import FIELDS, counters


def sample(value, last=None):
    def values(n):
        result = dict.fromkeys(FIELDS, 0)
        result.update(inputTokens=n, totalTokens=n, cachedInputTokens=n // 2)
        return result
    return dict(total=values(value), last=values(value if last is None else last))


class CounterAuditTests(unittest.TestCase):
    def test_repeated_snapshot_not_charged_again(self):
        result = counters([sample(20), sample(20), sample(40, 20)])
        self.assertTrue(result['complete'])
        self.assertEqual(result['total']['totalTokens'], 40)
        self.assertEqual(result['distinct_snapshots'], 2)

    def test_inherited_usage_cannot_be_called_new_child_usage(self):
        self.assertFalse(counters([sample(40, 20)])['complete'])

    def test_counter_reset_is_not_free_inference(self):
        self.assertFalse(counters([sample(40), sample(20)])['complete'])

    def test_missing_and_all_zero_are_unknown(self):
        for snapshots in ([], [sample(0)], [{'total': {}, 'last': {}}]):
            self.assertIsNone(counters(snapshots)['total'])

    def test_cached_and_reasoning_are_subsets(self):
        row = sample(20)
        row['total']['cachedInputTokens'] = row['last']['cachedInputTokens'] = 21
        self.assertFalse(counters([row])['complete'])
        row = sample(20)
        row['total']['reasoningOutputTokens'] = row['last']['reasoningOutputTokens'] = 1
        self.assertFalse(counters([row])['complete'])


if __name__ == '__main__':
    unittest.main()
