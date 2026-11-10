"""Actual Git isolation and complete-history-group selection checks."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from repository_memory_wave_a import history_view, git_command, git_env


class HistoryIntegrity(unittest.TestCase):
    def test_tool_result_group_not_split(self):
        data = [dict(role='user', content='problem'),
                dict(role='assistant', tool_calls=[dict(id='one')]),
                dict(role='tool', tool_call_id='one', content='x' * 200),
                dict(role='assistant', content='final')]
        selected, _ = history_view(data, 120)
        self.assertFalse(any(m.get('tool_calls') for m in selected))
        self.assertFalse(any(m.get('tool_call_id') for m in selected))

    def test_legacy_observation_group_not_split(self):
        data = [dict(role='assistant', content='command'),
                dict(role='user', content='observation' * 30)]
        selected, loss = history_view(data, 100)
        self.assertEqual(selected, [])
        self.assertEqual(loss['dropped_group_indices'], [0])

    def test_exact_record_order_preserved(self):
        data = [dict(role='user', content=str(i)) for i in range(12)]
        selected, loss = history_view(data, 180)
        positions = [data.index(m) for m in selected]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(len(selected), len(positions))
        self.assertTrue(loss['dropped_group_indices'])
        self.assertLessEqual(loss['selected_characters'], 180)

    def test_no_loss_when_fits(self):
        data = [dict(role='user', content='task'), dict(role='assistant', content='answer')]
        selected, loss = history_view(data)
        self.assertEqual(selected, data)
        self.assertEqual(loss['dropped_group_indices'], [])


class HostGitIsolation(unittest.TestCase):
    def test_actor_git_and_external_diff_cannot_control_host(self):
        with tempfile.TemporaryDirectory(prefix='ttgl-private-git-test-') as root:
            root = Path(root)
            work, index = root / 'actor', root / 'unmounted-index'
            work.mkdir()
            (work / '.gitignore').write_text('generated/\n')
            (work / 'generated').mkdir()
            tracked = work / 'generated/tracked.txt'
            tracked.write_text('base\n')
            subprocess.run(['git', 'init', '-q', '--separate-git-dir=' + str(index), str(work)], check=True)
            git = git_command(index, work)
            subprocess.run(git + ['add', '--force', '.'], check=True, env=git_env())
            subprocess.run(git + ['-c', 'user.name=fixture', '-c', 'user.email=fixture@example.invalid',
                                  'commit', '-qm', 'base'], check=True, env=git_env())
            (work / '.git').unlink()
            (work / '.git').mkdir()
            marker = root / 'must-not-run'
            (work / '.git/config').write_text('[diff]\n external = touch ' + str(marker) + '\n')
            tracked.write_text('changed\n')
            with patch.dict(os.environ, {'GIT_EXTERNAL_DIFF': 'touch ' + str(marker)}):
                result = subprocess.run(git + ['diff', '--no-ext-diff', '--no-textconv', 'HEAD'],
                    env=git_env(), check=True, capture_output=True, text=True)
            self.assertIn('+changed', result.stdout)
            self.assertIn('generated/tracked.txt', result.stdout)
            self.assertFalse(marker.exists())
            config = subprocess.run(git + ['config', '--get', 'diff.external'],
                                    env=git_env(), capture_output=True, text=True)
            self.assertEqual(config.returncode, 1)


if __name__ == '__main__':
    unittest.main()
