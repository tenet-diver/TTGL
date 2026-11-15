import json
from pathlib import Path
import tempfile
import unittest

from repository_tokeneconomizer_hook import bridge_result, compatible_records, native_compatible_trace, install_adapter


class IntegrationChecks(unittest.TestCase):
    def frame(self, code=2):
        return dict(content=[dict(type='text', text=json.dumps(dict(id='event_fixture_1', kind='tool_result',
                    command='false', exit_code=code, stdout='', stderr='observed failure')))], isError=False)

    def test_real_host_adapter_handles_only_own_terminal(self):
        host = install_adapter()()
        p = dict(tool_name='mcp__ttgl_task__terminal', tool_input=dict(command='false'), tool_response=self.frame())
        name, args, text, code = host.tool_call(p)
        self.assertEqual((name, args['command'], text, code), ('bash', 'false', 'observed failure', 2))
        p['tool_name'] = 'mcp__foreign__terminal'
        self.assertEqual(host.tool_call(p)[0], 'mcp__foreign__terminal')
        with self.assertRaises(ValueError):
            bridge_result(dict(stdout='fake', exit_code=0))

    def test_historical_trace_preserves_id_and_observed_exit(self):
        messages = [dict(role='assistant', tool_calls=[dict(id='original-call', function=dict(name='bash', arguments='{"command":"false"}'))]),
                    dict(role='tool', tool_call_id='original-call', content='observed failure', extra=dict(returncode=2))]
        rows = compatible_records(messages, 'original-source-sha')
        self.assertEqual(rows[0]['message']['content'][0]['id'], 'original-call')
        self.assertTrue(rows[1]['message']['content'][0]['is_error'])
        self.assertIn('not a Claude', rows[0]['ttgl_derivation']['schema'])
        messages[1]['extra']['returncode'] = None
        with self.assertRaises(ValueError):
            compatible_records(messages, 'source')

    def test_native_semantic_trace_preserves_underlying_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, dest = root / 'original.jsonl', root / 'derived.jsonl'
            item = dict(type='mcp_tool_call', id='native-item', server='ttgl_task', tool='terminal',
                        arguments=dict(command='false'), result=self.frame())
            original = json.dumps(dict(type='item.completed', item=item)) + '\n'
            source.write_text(original)
            self.assertEqual(native_compatible_trace(source, dest), 1)
            self.assertEqual(source.read_text(), original)
            rows = [json.loads(s) for s in dest.read_text().splitlines()]
            self.assertEqual(rows[0]['ttgl_derivation']['source_item'], 'native-item')
            self.assertTrue(rows[1]['message']['content'][0]['is_error'])
            self.assertNotIn('usage', dest.read_text())


if __name__ == '__main__':
    unittest.main()
