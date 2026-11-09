"""No-inference controls for output contracts and refusing uncertain dispatches."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from memory_native_calls import MemoryNativeCalls
from smallville_compat_v4 import parse_triple


class LunaMemoryAdapters(unittest.TestCase):
    def test_refusal_is_not_invented_as_a_memory(self):
        with self.assertRaises(ValueError):
            parse_triple('Please clarify the intended sentence.', 'TTGL agent')

    def test_triple_preserves_unicode_and_commas(self):
        raw = ['TTGL agent', 'observed', 'α, β, and CRLF']
        self.assertEqual(parse_triple(json.dumps(raw), raw[0]), tuple(raw))

    def test_wrong_subject_and_empty_parts_are_rejected(self):
        for raw in [['another agent', 'saw', 'x'], ['TTGL agent', '', 'x'], ['TTGL agent', 'saw']]:
            with self.assertRaises(ValueError):
                parse_triple(json.dumps(raw), 'TTGL agent')

    def test_started_cell_cannot_be_dispatched_again(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            calls = MemoryNativeCalls(root, 'gpt-6-luna')
            (root / 'call-001').mkdir()
            with patch('memory_native_calls.run_process') as backend:
                with self.assertRaises(FileExistsError):
                    calls('new request', 'importance')
                backend.assert_not_called()

    def test_cap_refuses_before_creating_any_model_cell(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            calls = MemoryNativeCalls(root, 'gpt-6-luna', cap=0)
            with patch('memory_native_calls.run_process') as backend:
                with self.assertRaises(ValueError):
                    calls('new request', 'importance')
                backend.assert_not_called()
            self.assertEqual(list(root.glob('call-*')), [])


if __name__ == '__main__':
    unittest.main()
