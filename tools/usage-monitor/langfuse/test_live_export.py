import json
from pathlib import Path
import tempfile
import unittest

import live_export


class LiveExportTests(unittest.TestCase):
    def test_native_usage_and_turn_content_exclude_reasoning(self):
        records = [
            dict(type='session_meta', payload=dict(id='s', timestamp='2026-11-05T00:00:00Z', cwd='/repo')),
            dict(type='event_msg', payload=dict(type='task_started', turn_id='t')),
            dict(type='event_msg', payload=dict(type='item_completed', turn_id='t', item=dict(type='UserMessage', content=[dict(type='text', text='hello')]))),
            dict(type='event_msg', payload=dict(type='item_completed', turn_id='t', item=dict(type='Reasoning', raw_content='PRIVATE_REASONING'))),
            dict(type='token_usage_record', payload=dict(turn_id='t', response_id='r', usage=dict(input_tokens=10, cached_input_tokens=8, output_tokens=2, total_tokens=12))),
            dict(type='event_msg', payload=dict(type='item_completed', turn_id='t', item=dict(type='AgentMessage', content='world'))),
            dict(type='event_msg', payload=dict(type='task_complete', turn_id='t')),
        ]
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 's.jsonl'
            path.write_text(''.join(json.dumps(dict(r, timestamp='2026-11-05T00:00:01Z')) + '\n' for r in records))
            spans = list(live_export.native_spans(path))
        self.assertEqual(len(spans), 2)
        raw = json.dumps(spans)
        self.assertIn('hello', raw)
        self.assertIn('world', raw)
        self.assertNotIn('PRIVATE_REASONING', raw)
        attributes = {a['key']: a['value'] for a in spans[0]['attributes']}
        usage = json.loads(attributes['langfuse.observation.usage_details']['stringValue'])
        self.assertEqual(usage, dict(input=2, input_cached_tokens=8, output=2, total=12))
        self.assertEqual(spans[0]['startTimeUnixNano'], spans[0]['endTimeUnixNano'])

    def test_redaction_and_truncation(self):
        text, truncated = live_export.safe_content('Authorization: Bearer planted-secret ' + 'x' * (live_export.LIMIT + 1))
        self.assertNotIn('planted-secret', text)
        self.assertTrue(truncated)


if __name__ == '__main__':
    unittest.main()
