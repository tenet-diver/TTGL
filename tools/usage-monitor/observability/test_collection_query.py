import json
import unittest
import collection_query as cq

class CollectionQueryTests(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(title=f'Row {i}',amount=None if i==14 else i,notes='résumé marker' if i==42 else '') for i in range(55)]
        self.fields=cq.fields(['title','amount','notes'])
    def test_global_numeric_filter_sort_nulls_and_hidden_search(self):
        rows=cq.apply(self.rows,json.dumps(dict(filters={'amount':'>= 50'},sort='amount',direction=-1)),self.fields)
        self.assertEqual([r['amount'] for r in rows],[54,53,52,51,50])
        for direction in (1,-1):self.assertIsNone(cq.apply(self.rows,dict(sort='amount',direction=direction),self.fields)[-1]['amount'])
        self.assertEqual(cq.apply(self.rows,dict(search='resume marker'),self.fields)[0]['amount'],42)
        self.assertEqual(cq.apply(self.rows,dict(sort='title'),self.fields)[2]['title'],'Row 2')
    def test_rejects_invalid_and_unbounded_control_data(self):
        for value in ('x'*16001, '[]',dict(sort='not_a_column'),dict(filters={'amount':123}),dict(direction=3),dict(search=[])):
            with self.subTest(value=str(value)[:80]),self.assertRaises((ValueError,TypeError)):cq.apply(self.rows,value,self.fields)
    def test_unknown_numeric_values_do_not_become_zero(self):
        self.assertEqual(len(cq.apply(self.rows,dict(filters={'amount':'= 0'}),self.fields)),1)
        self.assertEqual(len(cq.apply(self.rows,dict(filters={'amount':'unknown'}),self.fields)),1)

if __name__=='__main__':unittest.main()
