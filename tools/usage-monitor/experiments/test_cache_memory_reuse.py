import json,unittest
from cache_memory_reuse import corpus,grade_answer
class ReuseDataTests(unittest.TestCase):
    def test_latest_source_oracle_and_no_future_answer_in_question(self):
        data=corpus(24,0,20261107)
        self.assertEqual(data,corpus(24,0,20261107))
        self.assertEqual(len(data['episodes']),48)
        for q in data['queries']:
            self.assertNotIn(q['expected'],q['question'])
            self.assertTrue(grade_answer(json.dumps(dict(value=q['expected'])),q['expected']))
            self.assertFalse(grade_answer(json.dumps(dict(value=q['old_value'])),q['expected']))
            self.assertFalse(grade_answer('{}',q['expected']))
            self.assertFalse(grade_answer('not JSON',q['expected']))
    def test_actor_record_schema_has_no_question_or_gold_fields(self):
        for episode in corpus(24,1,20261107)['episodes']:
            row=json.loads(episode['body']);self.assertEqual(set(row),{'date','messages'})
            self.assertEqual(set(row['messages'][0]),{'role','content'})
if __name__=='__main__':unittest.main()
