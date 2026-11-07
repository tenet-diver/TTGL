import unittest
from aggregate_session_audit import aggregate
class SessionAudit(unittest.TestCase):
    def cell(self,sid,ident,**kw):
        return dict(session_id=sid,case='one',condition='continued_full',role='reader',usage=dict(input_tokens=10,cached_input_tokens=8,output_tokens=1,total_tokens=11),native_response_ids=[ident],**kw)
    def test_continued_turns_sum_once(self):
        rows=aggregate([self.cell('s','a'),self.cell('s','b')]);self.assertEqual(len(rows),1);self.assertEqual(rows[0]['usage']['total_tokens'],22);self.assertEqual(rows[0]['native_response_ids'],['a','b'])
    def test_duplicate_response_rejected_across_sessions(self):
        with self.assertRaises(ValueError):aggregate([self.cell('s','a'),self.cell('t','a')])
    def test_cross_condition_thread_rejected(self):
        other=self.cell('s','b');other['condition']='fts'
        with self.assertRaises(ValueError):aggregate([self.cell('s','a'),other])
if __name__=='__main__':unittest.main()
