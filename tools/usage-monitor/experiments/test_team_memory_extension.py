"""Behavioral evidence boundaries, concurrency and no-repeat maintenance tests."""
from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import unittest

from team_memory_service import Broker
from team_memory_store import Journal, public_item


class FakeBackend:
    def __init__(self, fails=False):
        self.calls, self.fails = 0, fails

    def publish(self, record):
        self.calls += 1
        if self.fails:
            raise RuntimeError('preserved failed native call')
        return dict(stored=True)

    def search(self, query, limit):
        return []


class MemoryBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def broker(self, kind='searchable_logs', fails=False):
        return Broker(dict(kind=kind,root=str(self.root)),FakeBackend(fails))

    def request(self, ident='request-1', **changes):
        result = dict(id=ident,operation='publish_finding',arguments=dict(author='parent',text='The exact command is python -m unittest; not executed yet.',source='docs/checks.md:4'))
        result.update(changes)
        return result

    def test_peers_share_records_and_raw_paging(self):
        journal = Journal(self.root/'one.sqlite')
        record = journal.add('parent','publication','Exact command ' + 'x'*9000,'source:1')
        peer = Journal(self.root/'one.sqlite')
        self.assertEqual(peer.search('command')[0]['id'],record['id'])
        page = peer.get(record['id'],0,3000)
        self.assertEqual(page['next_offset'],3000)
        self.assertEqual(peer.get(record['id'],page['next_offset'],16000)['body'],record['body'][3000:])

    def test_different_assignment_cannot_read_or_search(self):
        first = Journal(self.root/'one.sqlite')
        record = first.add('a','publication','unique_secret_marker','public source')
        second = Journal(self.root/'two.sqlite')
        self.assertEqual(second.search('unique_secret_marker'),[])
        with self.assertRaises(ValueError):
            second.get(record['id'])

    def test_concurrent_authors_keep_all_records(self):
        journal = Journal(self.root/'one.sqlite')
        with ThreadPoolExecutor(max_workers=8) as pool:
            rows=list(pool.map(lambda n:journal.add('worker'+str(n),'publication','scheduling witness '+str(n),'src:'+str(n)),range(32)))
        self.assertEqual(len({r['id'] for r in rows}),32)
        with journal.connect() as db:
            self.assertEqual(db.execute('SELECT COUNT(*) FROM records').fetchone()[0],32)

    def test_duplicate_request_does_not_repeat_model_work(self):
        broker=self.broker('mem0_luna')
        request=self.request()
        a=broker.invoke(request);b=broker.invoke(request)
        self.assertEqual(a,b)
        self.assertEqual(broker.backend.calls,1)

    def test_identity_collision_is_rejected(self):
        broker=self.broker()
        broker.invoke(self.request())
        with self.assertRaises(ValueError):
            broker.invoke(self.request(arguments=dict(author='a',text='different',source='b')))

    def test_uncertain_intent_cannot_be_replayed(self):
        import hashlib
        broker=self.broker('graphiti_luna')
        request=self.request()
        key=hashlib.sha256(request['id'].encode()).hexdigest()
        fingerprint=hashlib.sha256(json.dumps(request,sort_keys=True).encode()).hexdigest()
        (broker.receipts/(key+'.intent.json')).write_text(json.dumps(dict(fingerprint=fingerprint)))
        with self.assertRaises(RuntimeError):
            broker.invoke(request)
        self.assertEqual(broker.backend.calls,0)

    def test_failed_maintenance_preserves_record_and_never_falls_back(self):
        broker=self.broker('smallville_luna',True)
        result=broker.invoke(self.request())
        self.assertIn('error',result)
        self.assertEqual(broker.backend.calls,1)
        repeated=broker.invoke(self.request())
        self.assertEqual(result,repeated)
        broker.invoke(self.request('another'))
        self.assertEqual(broker.backend.calls,1)
        self.assertTrue(broker.journal.search('exact command'))

    def test_search_validation_precedes_backend_work(self):
        broker=self.broker('mem0_luna')
        result=broker.invoke(self.request(operation='search_memory',arguments=dict(query='q',limit=True)))
        self.assertIn('error',result)
        self.assertIsNone(broker.poisoned)

    def test_original_evidence_is_not_replaced_by_model_memory(self):
        broker=self.broker('graphiti_luna')
        result=broker.invoke(self.request())['result']
        original=broker.execute('read_record',dict(id=result['record_id']))
        self.assertIn('not executed yet',original['body'])

    def test_log_auto_ingestion_is_only_in_log_arm(self):
        broker=self.broker('mem0_luna')
        with self.assertRaises(ValueError):
            broker.execute('ingest_visible',dict(author='a',kind='agentMessage',body='public',source='rpc:1'))

    def test_fts_operators_and_sql_are_query_data(self):
        journal=Journal(self.root/'one.sqlite')
        journal.add('a','publication','check result','source')
        self.assertEqual(len(journal.search('check OR "result"; DROP TABLE records; --')),1)
        self.assertEqual(len(journal.search('check')),1)

    def test_only_visible_allowed_items_are_exposed(self):
        def event(kind,**extra):
            return dict(method='item/completed',params=dict(threadId='child',item=dict(type=kind,id='1',**extra)))
        for kind in ('reasoning','encryptedContent','fileChange','unknown'):
            self.assertIsNone(public_item(event(kind,text='private')))
        self.assertIsNone(public_item(event('mcpToolCall',server='team_memory',result='recursive memory dump')))
        self.assertEqual(public_item(event('agentMessage',text='public report'))['author'],'child')
        self.assertIsNone(public_item(dict(method='turn/completed',params=dict(secret='not a public item'))))

    def test_current_native_coordination_and_command_shapes(self):
        base=dict(method='item/completed',params=dict(threadId='worker',item=dict(type='collabAgentToolCall',id='call',tool='send_message',prompt='checked interface',encrypted_content='never expose')))
        value=public_item(base)
        self.assertIn('checked interface',value['body'])
        self.assertNotIn('never expose',value['body'])
        base['params']['item']=dict(type='commandExecution',id='shell',command='python -m unittest',aggregatedOutput='passed',exitCode=0,encrypted_content='secret')
        self.assertIn('passed',public_item(base)['body'])
        self.assertNotIn('secret',public_item(base)['body'])

    def test_response_accounting_deduplicates_and_rejects_conflicts(self):
        from audit_team_memory_usage import unique_records,usage
        response=dict(usage=dict(input_tokens=10,output_tokens=2,total_tokens=12,input_tokens_details=dict(cached_tokens=4),output_tokens_details=dict(reasoning_tokens=1)))
        measured=usage(response)
        row=dict(type='token_usage_record',payload=dict(thread_id='t',response_id='r',usage=measured))
        self.assertEqual(len(unique_records([row,row],'t')),1)
        other=json.loads(json.dumps(row));other['payload']['usage']['input_tokens']=11
        with self.assertRaises(ValueError):unique_records([row,other],'t')
        response['usage']['input_tokens_details']['cached_tokens']=11
        with self.assertRaises(ValueError):usage(response)

    def test_each_arm_explicitly_describes_shared_tools_to_workers(self):
        from codex_team_memory_extension import guidance,ARMS
        for arm in ARMS:
            text=guidance(arm)
            self.assertIn('every delegated worker',text)
            if arm.endswith('_luna') or arm=='searchable_logs':
                for tool in ('publish_finding','search_memory','read_record','coverage'):
                    self.assertIn(tool,text)
                self.assertIn('Every parent and child',text)

    def test_empty_smallville_store_returns_no_memories_without_ranking(self):
        from types import SimpleNamespace
        from team_memory_backends import Backend
        backend=Backend.__new__(Backend)
        backend.kind='smallville_luna'
        backend.engine=SimpleNamespace(memory=SimpleNamespace(id_to_node={}))
        self.assertEqual(backend.search('Any prior findings?',8),[])


if __name__=='__main__':
    unittest.main()
