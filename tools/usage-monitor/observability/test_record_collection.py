"""Full-cohort list controls must survive bounded dashboard transport."""
import unittest
from record_collection import query_records


class RecordCollectionTests(unittest.TestCase):
    def setUp(self):
        self.rows=[dict(title='Café repair',workspace='/hidden/project',cost=3),dict(title='Other',workspace='/other',cost=None),dict(title='Cheap repair',workspace='/hidden/project',cost=.5)]
        self.columns={key:(lambda row,key=key:row[key],key=='cost') for key in ('title','workspace','cost')}

    def test_search_normalizes_and_includes_hidden_columns_with_all_terms(self):
        rows,query=query_records(self.rows,self.columns,dict(search='CAFE hidden'))
        self.assertEqual([r['title'] for r in rows],['Café repair'])
        self.assertEqual(query['search'],'CAFE hidden')

    def test_numeric_filters_and_sort_keep_unknowns_last_both_directions(self):
        rows,_=query_records(self.rows,self.columns,dict(filters={'cost':'>= 1'},sort='cost',direction=-1))
        self.assertEqual([r['cost'] for r in rows],[3])
        for direction,expected in [(1,[.5,3,None]),(-1,[3,.5,None])]:
            rows,_=query_records(self.rows,self.columns,dict(sort='cost',direction=direction))
            self.assertEqual([r['cost'] for r in rows],expected)
        rows,_=query_records(self.rows,self.columns,dict(filters={'title':'repair','cost':'!= 3'}))
        self.assertEqual([r['cost'] for r in rows],[.5])

    def test_text_sort_uses_natural_numeric_order(self):
        rows=[dict(title='Task 10'),dict(title='Task 2'),dict(title='Task 1')]
        rows,_=query_records(rows,{'title':(lambda row:row['title'],False)},dict(sort='title'))
        self.assertEqual([r['title'] for r in rows],['Task 1','Task 2','Task 10'])

    def test_invalid_queries_are_bounded_and_rejected(self):
        for query in ('[]','{',dict(sort='not-a-column'),dict(filters={'unknown':'yes'}),dict(filters={'cost':123}),dict(search='x'*1001),dict(direction=7)):
            with self.subTest(query=str(query)[:30]),self.assertRaises(ValueError):query_records(self.rows,self.columns,query)
