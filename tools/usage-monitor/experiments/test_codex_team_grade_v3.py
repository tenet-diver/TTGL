import unittest
from codex_team_grade_v3 import satisfies_reference_counts


class CollectionGuard(unittest.TestCase):
    def test_full_reference_and_extra_tests(self):
        reference = dict(tests=100, skipped=2, errors=0, failures=0)
        self.assertTrue(satisfies_reference_counts(reference, reference))
        self.assertTrue(satisfies_reference_counts(dict(reference, tests=102), reference))

    def test_early_skip_collection_cannot_count_as_resolution(self):
        reference = dict(tests=100, skipped=2, errors=0, failures=0)
        for candidate in [dict(tests=1, skipped=1, errors=0, failures=0),
                          dict(reference, skipped=3), dict(reference, failures=1),
                          dict(reference, errors=1)]:
            with self.subTest(candidate=candidate):
                self.assertFalse(satisfies_reference_counts(candidate, reference))


if __name__ == '__main__':
    unittest.main()
