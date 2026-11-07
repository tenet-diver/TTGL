import unittest
from longmemeval_codex_trial import history,judge_prompt
import json


class BenchmarkBoundaryTests(unittest.TestCase):
    def test_history_excludes_all_gold_labels(self):
        row=dict(haystack_dates=['2025-01-01'],haystack_sessions=[[dict(role='user',content='A visible fact',has_answer=True,answer='secret')]],
                 answer='hidden reference',answer_session_ids=['hidden-id'],question_type='knowledge-update')
        result=history(row)
        self.assertEqual(json.loads(result[0]['body']),dict(date='2025-01-01',messages=[dict(role='user',content='A visible fact')]))
        self.assertNotIn('hidden',result[0]['body'])

    def test_mismatched_history_dates_blocks_execution(self):
        with self.assertRaises(ValueError):history(dict(haystack_dates=[],haystack_sessions=[[dict(role='user',content='x')]]))

    def test_judge_uses_correct_rubric_and_blinds_methods(self):
        row=dict(question='q',answer='gold',question_id='case_abs',question_type='multi-session')
        prompt=judge_prompt(row,'insufficient information')
        self.assertIn('unanswerable',prompt)
        self.assertNotIn('case_abs',prompt)
        self.assertNotIn('mem0',prompt)


if __name__=='__main__':unittest.main()
