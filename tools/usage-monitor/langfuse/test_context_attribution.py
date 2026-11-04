import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('context_estimate',Path(__file__).with_name('context_attribution.py'));m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class Tokens:
 def count(self,s):return len(s)
class AttributionTests(unittest.TestCase):
 def test_prefix_intersection_and_unknown_residual_reconcile(self):
  c=m.Context();c.add('instructions',40);c.add('tool output',60);snap=c.snapshot()
  a=m.allocate(snap,150,90);self.assertEqual(a[m.UNKNOWN],(0,50));self.assertEqual(a['instructions'],(0,40));self.assertEqual(a['tool output'],(60,0))
  a=m.allocate(snap,150,140);self.assertEqual(a['tool output'],(10,50))
 def test_snapshot_does_not_include_current_generation_or_new_tool_result(self):
  c=m.Context();c.add('old',20);snap=c.snapshot();c.add('new output',100)
  self.assertNotIn('new output',m.allocate(snap,50,20));self.assertEqual(sum(sum(x) for x in m.allocate(snap,50,20).values()),50)
 def test_oversized_visible_history_is_unallocated(self):
  c=m.Context();c.add('tool',200);self.assertEqual(m.allocate(c.snapshot(),100,80),{m.UNRESOLVED:(20,80)})
 def test_native_usage_and_legacy_counter_are_not_double_charged(self):
  u={'input_tokens':10,'cached_input_tokens':6,'output_tokens':2,'total_tokens':12};rows=[{'type':'session_meta','timestamp':'2026-11-04T00:00:00Z','payload':{'id':'s','timestamp':'2026-11-04T00:00:00Z'}},{'type':'turn_context','payload':{'model':'model'}},{'type':'response_item','payload':{'type':'message','role':'user','content':[{'type':'input_text','text':'task'}]}},{'type':'response_item','payload':{'type':'function_call','call_id':'c','name':'read','arguments':'{}'}},{'type':'token_usage_record','payload':{'thread_id':'s','response_id':'r','usage':u,'thread_token_usage':u}},{'type':'response_item','payload':{'type':'function_call_output','call_id':'c','output':'new tool output'}},{'type':'event_msg','payload':{'type':'token_count','info':{'total_token_usage':u}}}]
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'r.jsonl';p.write_text(''.join(json.dumps(x)+'\n' for x in rows));parser=m.Parser(Tokens(),{'models':{'model':{}}}).parse(p)
  self.assertEqual(parser.metered,1);self.assertEqual(parser.measured['model']['cached'],6);self.assertFalse(any(k.startswith('Tool output') for k in parser.allocated['model']))
 def test_mismatch_stays_unknown_instead_of_fabricating_tool_cost(self):
  p=m.Parser(Tokens(),{'lastActivity':'2026-11-04T12:00:00Z','models':{'model':{'inputTokens':4,'cacheReadTokens':6,'outputTokens':2}}});policy={};rows,known=m.result_rows(p,policy)
  self.assertEqual(known,[]);self.assertEqual(rows['model'][('2026-11-04',m.UNRESOLVED)]['cached'],6);self.assertEqual(rows['model'][('2026-11-04',m.OUTPUT)]['output'],2)
 def test_unreconciled_day_does_not_move_and_double_count_on_new_activity(self):
  p=m.Parser(Tokens(),{'lastActivity':'2026-11-03T12:00:00Z','models':{'model':{'inputTokens':4,'cacheReadTokens':6,'outputTokens':2}}});policy={}
  m.result_rows(p,policy);p.expected['lastActivity']='2026-11-04T12:00:00Z';rows,_=m.result_rows(p,policy)
  self.assertIn(('2026-11-03',m.UNRESOLVED),rows['model'])
 def test_fragment_partition_preserves_text_and_rejects_ambiguous_owners(self):
  a='a'*1100;b='b'*1100;text='header'+a+'middle'+b+'end'
  parts=m.split_sources(text,[('toolA',[a]),('toolB',[b])])
  self.assertEqual(''.join(v for k,v in parts),text)
  self.assertEqual([k for k,v in parts if 'exact retained' in k],['Tool output / toolA (exact retained fragment)','Tool output / toolB (exact retained fragment)'])
  self.assertEqual(m.split_sources(a,[('toolA',[a]),('toolB',[a])]),[])
 def test_prefix_query_handles_interleaved_groups(self):
  c=m.Context();c.add('a',10);c.add('b',20);c.add('a',10)
  self.assertEqual(c.prefix('a',25),10);self.assertEqual(c.prefix('a',35),15);self.assertEqual(c.prefix('b',35),20)
if __name__=='__main__':unittest.main()
