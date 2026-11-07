import json
from pathlib import Path
import tempfile,unittest
from native_jsonl import records,validate_native_completion
class NativeJsonlTests(unittest.TestCase):
    def test_unicode_separators_do_not_create_extra_records(self):
        with tempfile.TemporaryDirectory() as d:
            cell=Path(d);rows=[dict(type='thread.started',thread_id='unique'),dict(type='item.completed',item=dict(type='agent_message',text='a\u2028b\u0085c\u2029d')),dict(type='turn.completed',usage=dict(input_tokens=10,cached_input_tokens=0,output_tokens=2))]
            (cell/'agent.jsonl').write_text('\n'.join(json.dumps(r,ensure_ascii=False) for r in rows)+'\n')
            self.assertEqual(records(cell),rows);self.assertEqual(validate_native_completion(cell,no_tools=True),'unique')
            rows.insert(1,dict(type='thread.started',thread_id='duplicate'));(cell/'agent.jsonl').write_text('\n'.join(json.dumps(r) for r in rows)+'\n')
            with self.assertRaises(ValueError):validate_native_completion(cell)
    def test_actual_truncation_remains_an_error(self):
        with tempfile.TemporaryDirectory() as d:
            cell=Path(d);(cell/'agent.jsonl').write_bytes(b'{"type":"thread.started","thread_id":"unfinished')
            with self.assertRaises(ValueError):records(cell)
if __name__=='__main__':unittest.main()
