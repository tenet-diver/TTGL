import unittest
from ttgl.model_delegation.freeze import qualified_split


class FreezeTests(unittest.TestCase):
    def fixture(self,n):
        tasks=[{'task_id':str(i),'lineage_ids':['base-'+str(i)]} for i in range(n)]
        reservation={'partitions':{'construction':tasks[:12],'development':tasks[12:24],'heldout':tasks[24:56]},'spares_before_any_assignment':tasks[56:]}
        prep={'native_model_calls':0,'results':[{'task_id':str(i),'eligible':True} for i in range(n)]}
        return reservation,prep,{'minimum_viable_eligible_tasks':24,'allocation':[
            {'eligible_count_at_least':56,'construction':12,'development':12,'heldout':32,'prefixes':[0,4,8,12]},
            {'eligible_count_at_least':32,'eligible_count_below':56,'construction':12,'development':12,'heldout':'eligible_count minus24','prefixes':[0,4,8,12]},
            {'eligible_count_at_least':24,'eligible_count_below':32,'construction':8,'development':8,'heldout':'eligible_count minus16','prefixes':[0,4,8]}]}
    def test_metadata_order_allocation_preserves_reserved_test_exclusion(self):
        for n,counts,total in [(71,(12,12,32),640),(40,(12,12,16),320),(24,(8,8,8),136)]:
            with self.subTest(n=n):
                result=qualified_split(*self.fixture(n))
                self.assertEqual(tuple(map(len,result['partitions'].values())),counts)
                self.assertEqual(result['heldout_assignments_expected'],total)
                self.assertFalse(result['allow_model_execution'])
    def test_incomplete_duplicate_or_post_model_controls_do_not_freeze_split(self):
        r,p,s=self.fixture(40)
        p['results'].pop()
        with self.assertRaises(ValueError):qualified_split(r,p,s)
        r,p,s=self.fixture(40);p['results']+=p['results'][:1]
        with self.assertRaises(ValueError):qualified_split(r,p,s)
        r,p,s=self.fixture(40);p['native_model_calls']=1
        with self.assertRaises(ValueError):qualified_split(r,p,s)
        self.assertFalse(qualified_split(*self.fixture(23))['execution_ready'])
