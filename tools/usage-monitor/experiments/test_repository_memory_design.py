"""Leakage and reservation controls, not model-quality tests."""
import unittest
from repository_memory_design import audit, earlier_history, validate_targets


def target(repo='org/alpha', n=5):
    return dict(instance_id=repo.replace('/', '__') + '-' + str(n), repo=repo,
                base_commit='a' * 40, language='python', image_name='example.invalid/image',
                created_at='2026-01-01', license='MIT')


def trajectory(repo, n):
    ident = repo.replace('/', '__') + '-' + str(n)
    return 'history/python/' + repo.replace('/', '__') + '/' + ident + '/' + ident + '.traj.json'


class TemporalControls(unittest.TestCase):
    def test_current_and_future_excluded(self):
        self.assertEqual(earlier_history(target(), [trajectory('org/alpha', n)
                         for n in (4, 5, 6)]), [trajectory('org/alpha', 4)])

    def test_other_repo_excluded(self):
        self.assertEqual(earlier_history(target(), [trajectory('org/beta', 1)]), [])

    def test_numeric_order(self):
        self.assertEqual(earlier_history(target(n=100), [trajectory('org/alpha', n)
                         for n in (20, 3)]), [trajectory('org/alpha', n) for n in (3, 20)])

    def test_hidden_fields_fail_closed(self):
        for field in ('patch', 'test_patch', 'FAIL_TO_PASS', 'problem_statement', 'install_config'):
            with self.subTest(field=field), self.assertRaises(ValueError):
                validate_targets([dict(target(), **{field: 'hidden'})])

    def test_duplicate_target_rejected(self):
        with self.assertRaises(ValueError):
            validate_targets([target(), target()])

    def test_repository_mismatch_rejected(self):
        with self.assertRaises(ValueError):
            validate_targets([dict(target(), repo='other/repo')])

    def test_unpinned_commit_rejected(self):
        with self.assertRaises(ValueError):
            validate_targets([dict(target(), base_commit='main')])

    def test_missing_license_preserved_but_not_selected(self):
        rows = [target(repo, n) for repo in ('org/alpha', 'org/beta', 'org/gamma') for n in (5, 6)]
        rows[0]['license'] = None
        self.assertEqual(audit(rows, [])['partitions']['development']['repo'], 'org/beta')

    def test_path_spoof_rejected(self):
        with self.assertRaises(ValueError):
            earlier_history(target(), ['history/python/org__alpha/other-1/other-1.traj.json'])

    def test_deterministic_repository_disjoint_split(self):
        rows = [target(repo, n) for repo in ('org/beta', 'org/alpha') for n in (5, 6)]
        result = audit(rows, [])
        self.assertEqual(result['partitions']['development']['repo'], 'org/alpha')
        self.assertEqual(result['partitions']['reserved_validation']['repo'], 'org/beta')
        self.assertEqual(result, audit(list(reversed(rows)), []))

    def test_ambiguous_license_not_selected(self):
        rows = [target(repo, n) for repo in ('org/alpha', 'org/beta', 'org/gamma') for n in (5, 6)]
        for row in rows:
            if row['repo'] == 'org/alpha':
                row['license'] = 'custom-check-github'
        self.assertEqual(audit(rows, [])['partitions']['development']['repo'], 'org/beta')

    def test_history_cap_and_prefix_stability(self):
        rows = [target(repo, n) for repo in ('org/alpha', 'org/beta') for n in (20, 21)]
        paths = [trajectory('org/alpha', n) for n in range(1, 25)]
        data = audit(rows, paths)['partitions']['development']['targets'][0]
        self.assertEqual(data['eligible_history_count'], 19)
        self.assertEqual(data['bounded_history_ids'], ['org__alpha-' + str(n) for n in range(12, 20)])

    def test_duplicate_paths_rejected(self):
        rows = [target(repo, n) for repo in ('org/alpha', 'org/beta') for n in (5, 6)]
        with self.assertRaises(ValueError):
            audit(rows, [trajectory('org/alpha', 1)] * 2)


if __name__ == '__main__':
    unittest.main()
