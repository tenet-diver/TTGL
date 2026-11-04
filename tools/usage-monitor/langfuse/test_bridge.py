import importlib.util,json,tempfile,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('bridge',Path(__file__).with_name('bridge.py'));b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
class BridgeTests(unittest.TestCase):
 def parse(self,rows):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'r.jsonl';p.write_text(''.join(json.dumps(r)+'\n' for r in rows));return b.tool_records(p)
 def test_patterns_drop_values_and_allow_safe_options(self):
  p=b.arg_summary({'query':'secret customer data','api_key':'sk-secret','view':'compact','limit':20},'curl https://secret.invalid -H "Authorization: secret"')
  text=json.dumps(p);self.assertNotIn('customer',text);self.assertNotIn('sk-secret',text);self.assertNotIn('secret.invalid',text);self.assertIn('view=compact',text);self.assertIn('limit=20',text)
 def test_native_excludes_parent_duplicate_and_wrapper(self):
  meta={'type':'session_meta','payload':{'id':'s','timestamp':'2026-11-04T12:00:00Z'}}
  def tool(ident,thread='s',ts='2026-11-04T12:01:00Z'):
   return {'type':'event_msg','timestamp':ts,'payload':{'type':'item_completed','thread_id':thread,'started_at_ms':1793793660000,'completed_at_ms':1793793661000,'item':{'id':ident,'type':'McpToolCall','server':'atlassian','tool':'getJiraIssue','arguments':{'view':'compact'},'status':'completed','result':{'isError':False}}}}
  rows=[meta,tool('old','parent'),tool('replay',ts='2026-11-04T11:00:00Z'),tool('own'),tool('own'),{'type':'response_item','timestamp':'2026-11-04T12:01:01Z','payload':{'type':'custom_tool_call_output','call_id':'wrapper','output':'done'}}]
  m,records,bad=self.parse(rows);self.assertEqual(len(records),1);self.assertEqual(records[0]['name'],'atlassian.getJiraIssue');self.assertEqual(records[0]['end']-records[0]['start'],10**9)
  spans=list(b.tool_spans(m,records));self.assertEqual(spans,list(b.tool_spans(m,records)));self.assertNotIn('usage_details',json.dumps(spans))
 def test_unknown_timing_is_explicit_not_response_latency(self):
  rows=[{'type':'session_meta','payload':{'id':'s','timestamp':'2026-11-04T12:00:00Z'}},{'type':'response_item','timestamp':'2026-11-04T12:01:00Z','payload':{'type':'function_call','call_id':'c','name':'exec','arguments':'secret'}},{'type':'response_item','timestamp':'2026-11-04T12:02:00Z','payload':{'type':'function_call_output','call_id':'c','output':'done'}}]
  r=self.parse(rows)[1][0];self.assertFalse(r['timing_known']);self.assertEqual(r['start'],r['end'])
 def test_usage_disjoint_buckets_and_reconciliation(self):
  r={'inputTokens':10,'cacheReadTokens':80,'cacheCreationTokens':0,'outputTokens':10,'reasoningOutputTokens':4,'totalTokens':100};u=b.usage_buckets(r)
  self.assertEqual(sum(v for k,v in u.items() if k!='total'),100);self.assertEqual(u['output'],6)
  with self.assertRaises(ValueError):b.usage_buckets({**r,'totalTokens':101})
  invalid=b.usage_buckets({**r,'reasoningOutputTokens':14});self.assertEqual(invalid['output'],10);self.assertNotIn('output_reasoning_tokens',invalid)
 def exporter(self,path):
  cfg=path/'c.json';cfg.write_text(json.dumps({'base_url':'http://localhost:3000','public_key':'p','secret_key':'s'}));return b.Exporter(cfg,path)
 def test_immutable_receipts_skip_changed_payload(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   e=self.exporter(Path(d));s=b.span('trace','key','name','tool',10,20,'usage-tools',{})
   e.add(s)
   with patch.object(e,'request',return_value={}):e.flush()
   e.add({**s,'name':'changed'});self.assertEqual(e.skipped,1);self.assertFalse(e.buffer);e.db.close()
 def test_partial_rejection_blocks_replay(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   e=self.exporter(Path(d));s=b.span('trace','key','name','tool',10**18,10**18+1,'usage-tools',{});e.add(s)
   with patch.object(e,'request',return_value={'partialSuccess':{'rejectedSpans':'1'}}):
    with self.assertRaises(ValueError):e.flush()
   self.assertEqual(e.db.execute('SELECT count(*) FROM sent').fetchone()[0],0)
   self.assertEqual(e.db.execute('SELECT count(*) FROM outbox').fetchone()[0],1)
   with patch.object(e,'request',return_value={'data':[]}):
    with self.assertRaises(RuntimeError):e.reconcile()
   with patch.object(e,'request',return_value={'data':[{'id':s['spanId']}]}):e.reconcile()
   self.assertEqual(e.db.execute('SELECT count(*) FROM sent').fetchone()[0],1);e.db.close()
 def test_backend_not_started_can_retry_without_ambiguous_receipt(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   e=self.exporter(Path(d));e.add(b.span('t','k','n','tool',10,20,'usage-tools',{}))
   with patch.object(e,'request',side_effect=b.urllib.error.URLError(ConnectionRefusedError())):
    with self.assertRaises(b.urllib.error.URLError):e.flush()
   self.assertEqual(e.db.execute('SELECT count(*) FROM outbox').fetchone()[0],0)
   with patch.object(e,'request',return_value={}):e.flush()
   self.assertEqual(e.db.execute('SELECT count(*) FROM sent').fetchone()[0],1);e.db.close()
 def test_usage_increment_ledger_and_no_double_count(self):
  from unittest.mock import patch
  with tempfile.TemporaryDirectory() as d:
   e=self.exporter(Path(d));report={'daily':[{'date':'2026-11-04','totalTokens':100,'models':{'m':{'inputTokens':10,'cacheReadTokens':80,'outputTokens':10,'totalTokens':100}}}]};sent=[]
   def request(path,data):
    sent.extend(data['resourceSpans'][0]['scopeSpans'][0]['spans']);return {}
   with patch.object(e,'request',side_effect=request):
    e.usage(report,'daily');e.usage(report,'daily')
    u=report['daily'][0]['models']['m'];u.update(inputTokens=15,totalTokens=105);report['daily'][0]['totalTokens']=105;e.usage(report,'daily')
   self.assertEqual(len(sent),2)
   usage=[json.loads(next(a['value']['stringValue'] for a in s['attributes'] if a['key']=='langfuse.observation.usage_details')) for s in sent]
   self.assertEqual([u['total'] for u in usage],[100,5]);self.assertNotEqual(sent[0]['spanId'],sent[1]['spanId'])
   self.assertIn('usage-daily-v3',json.dumps(sent))
   self.assertEqual(b.iso(int(sent[0]['startTimeUnixNano']))[:10],'2026-11-04')
   session={'sessions':[{'sessionId':'s','lastActivity':'2026-11-04T12:00:00Z','models':{'m':u},'totalTokens':105}]}
   # Use source-style counters, not the exported usage bucket dict.
   session['sessions'][0]['models']['m']=report['daily'][0]['models']['m']
   with patch.object(e,'request',side_effect=request):e.usage(session,'sessions')
   self.assertIn('usage-sessions-v2',json.dumps(sent));self.assertEqual(len(sent),3);e.db.close()
if __name__=='__main__':unittest.main()
