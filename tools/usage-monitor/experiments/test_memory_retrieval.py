import unittest
from memory_retrieval import search


class MemoryContracts(unittest.TestCase):
    def test_empty_namespace_and_query_have_no_history(self):
        self.assertEqual(search([], 'account'), [])
        self.assertEqual(search([dict(id='past', body='account')], '!!!'), [])

    def test_exact_evidence_and_no_sql_query_execution(self):
        body='Prior account normalization rejects conflicting identifiers.'
        hit=search([dict(id='past:1',body=body)], 'account OR "; DROP TABLE memory; --')[0]
        self.assertEqual(hit['body'],body)
        self.assertEqual(hit['episode'],'past:1')
        self.assertEqual(hit['offset'],0)

    def test_budget_and_chronological_corpus_boundary(self):
        self.assertEqual(search([dict(id='past',body='account '*800)],'account',budget=100), [])
        hits=search([dict(id='past',body='account '*800)],'account',limit=10)
        self.assertEqual(''.join(x['body'] for x in sorted(hits,key=lambda x:x['offset'])),'account '*800)
        self.assertTrue(all(x['episode']=='past' for x in hits))


if __name__=='__main__':unittest.main()
