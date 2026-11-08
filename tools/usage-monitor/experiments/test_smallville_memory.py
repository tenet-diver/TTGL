"""Semantic controls for original-style memory; all callbacks here are stubs."""
from datetime import datetime,timedelta
import json
from pathlib import Path
import tempfile
import unittest
from smallville_memory import SmallvilleMemory,render


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.directory=tempfile.TemporaryDirectory();self.root=Path(self.directory.name);self.calls=[];self.when=datetime(2026,1,1)
    def tearDown(self):self.directory.cleanup()
    def llm(self,prompt,role):
        self.calls.append((prompt,role))
        if role=='importance':return '{"output":"8"}'
        if role=='reflection_questions':return json.dumps({'output':repr(['What failed?','What worked?','What remains?'])})
        if role=='reflection_insights':return '\n'.join(f'{i+1}. Lesson {i} (because of 0, 1)' for i in range(5))
        if role=='reflection_triple':return 'learn, lesson)'
        raise AssertionError(role)
    def memory(self,root=None,**kwargs):return SmallvilleMemory(root or self.root/'memory',lambda text:[1.,0.],self.llm,{},**kwargs)
    def add(self,m,text='TTGL agent learned a useful fact',index=0):return m.observe(text,'TTGL agent','learn','fact',self.when+timedelta(minutes=index))

    def test_original_description_embedding_and_storage_fields(self):
        m=self.memory();n=self.add(m,'TTGL agent is working (tests passed)')
        self.assertEqual(n.embedding_key,'tests passed');self.assertEqual(n.poignancy,8)
        self.assertEqual(m.scratch.importance_trigger_curr,142)
        p=m.checkpoint();row=json.loads((p/'nodes.json').read_text())['node_1']
        self.assertEqual(row['type'],'event');self.assertEqual(row['filling'],[])
        self.assertEqual(set(row),{'node_count','type_count','type','depth','created','expiration','subject','predicate','object','description','embedding_key','poignancy','keywords','filling'})

    def test_released_code_recency_order_is_preserved_and_access_updates(self):
        m=self.memory();old=self.add(m,'old record',0);new=self.add(m,'new record',60)
        # Released code sorts access ascending then assigns descending decay.
        # Preserve this surprising oldest-first outcome when other scores tie.
        chosen=m.retrieve('query',self.when+timedelta(days=1),1)
        self.assertEqual([n.node_id for n in chosen],[old.node_id])
        self.assertEqual(old.last_accessed,self.when+timedelta(days=1))
        self.assertNotEqual(new.last_accessed,old.last_accessed)

    def test_normalized_relevance_weight_can_overcome_recency(self):
        m=self.memory();old=self.add(m,'old unrelated',0);new=self.add(m,'new relevant',1)
        m.memory.embeddings[old.embedding_key]=[0.,1.]
        self.assertEqual(m.retrieve('query',self.when+timedelta(days=1),1)[0].node_id,new.node_id)

    def test_restart_preserves_facts_and_documents_original_access_reset(self):
        m=self.memory();node=self.add(m);m.retrieve('query',self.when+timedelta(days=1),1)
        original=self.memory();self.assertEqual(original.memory.id_to_node[node.node_id].last_accessed,node.created)
        extended=self.memory(restore_last_access=True)
        self.assertEqual(extended.memory.id_to_node[node.node_id].last_accessed,self.when+timedelta(days=1))
        self.assertEqual(len(self.calls),1)

    def test_natural_threshold_reflection_and_evidence_depth_with_stub_models(self):
        m=self.memory()
        for i in range(19):self.add(m,f'observed repair attempt {i}',i)
        self.assertEqual(m.scratch.importance_trigger_curr,-2)
        thoughts=m.reflect_if_due(self.when+timedelta(days=1))
        self.assertEqual(len(thoughts),15);self.assertTrue(all(n.type=='thought' and n.depth==1 and n.filling for n in thoughts))
        self.assertTrue(all(all(i in m.memory.id_to_node for i in n.filling) for n in thoughts))
        self.assertEqual(m.scratch.importance_trigger_curr,150);self.assertEqual(m.scratch.importance_ele_n,0)
        self.assertEqual(sum(role=='reflection_questions' for _,role in self.calls),1)
        self.assertEqual(sum(role=='reflection_insights' for _,role in self.calls),3)
        self.assertEqual(sum(role=='reflection_triple' for _,role in self.calls),15)

    def test_no_automatic_reflection_below_threshold(self):
        m=self.memory();self.add(m);before=len(self.calls)
        self.assertEqual(m.reflect_if_due(self.when),[]);self.assertEqual(len(self.calls),before)

    def test_invalid_importance_stops_without_substituting_or_repeating(self):
        m=self.memory();count=[]
        def invalid(*args):count.append(1);return '{"output":"99"}'
        m.complete_callback=invalid
        with self.assertRaises(ValueError):self.add(m)
        self.assertEqual(len(count),1);self.assertEqual(len(m.memory.id_to_node),0)

    def test_invalid_evidence_is_rejected_before_thought_write(self):
        m=self.memory();self.add(m)
        m.complete_callback=lambda *args:'A claimed lesson (because of 999)'
        with self.assertRaises(ValueError):m._insights(m.persona,'0. An observation',1)
        self.assertEqual(len(m.memory.seq_thought),0)

    def test_namespace_and_embedding_boundaries(self):
        a=self.memory(self.root/'a');self.add(a)
        b=self.memory(self.root/'b');self.assertEqual(b.memory.id_to_node,{})
        a.embed_callback=lambda text:[1.,0.,0.]
        with self.assertRaises(ValueError):a.retrieve('query',self.when)

    def test_original_template_comment_removal_and_substitution(self):
        text=render('v3_ChatGPT/poignancy_event_v1.txt',['Agent','Identity','Agent','Actual event'])
        self.assertNotIn('<commentblockmarker>',text);self.assertNotIn('!<INPUT',text)
        self.assertIn('Event: Actual event',text);self.assertIn('break up, college acceptance',text)


if __name__=='__main__':unittest.main()
