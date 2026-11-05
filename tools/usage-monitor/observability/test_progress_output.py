import unittest
from progress_output import compact


class ProgressTests(unittest.TestCase):
    def test_drops_only_recognized_transient_lines(self):
        text = (' abcdef012345 Downloading 1.2MB/4MB\n abcdef012345 Extracting 3B\n'
                ' abcdef012345 Pull complete 0B\n Image pinned@sha256:123 Pulled\n'
                ' abcdef012345 Downloading error: quota\nWarning: disk full\n'
                '... command output truncated for persistence ...\n')
        result = compact(text)
        self.assertEqual(result['removed_lines'], 2)
        self.assertIn('Pull complete', result['output'])
        self.assertIn('Image pinned', result['output'])
        self.assertIn('Downloading error: quota', result['output'])
        self.assertIn('Warning: disk full', result['output'])
        self.assertIn('truncated', result['output'])
        self.assertEqual(compact(result['output'])['output'], result['output'])

    def test_unknown_output_is_preserved_exactly(self):
        text = 'Downloading is blocked\r\n\x1b[31m abcdef012345 Downloading 1B\nsource code\n'
        self.assertEqual(compact(text)['output'], text)
