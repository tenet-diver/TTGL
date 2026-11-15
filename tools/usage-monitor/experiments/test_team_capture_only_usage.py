import unittest
from audit_team_memory_usage_v2 import capture_only_record


class CaptureOnlyTests(unittest.TestCase):
    def response(self,**kw):
        return dict(id='r',model='gpt-6.1-sol',usage=dict(input_tokens=10,output_tokens=2,total_tokens=12,
            input_tokens_details=dict(cached_tokens=4)),**kw)

    def test_positive_usage_is_separate_and_deduplicated(self):
        sessions={'s':dict(model='gpt-6.1-sol')};owners={};rows={}
        self.assertTrue(capture_only_record(self.response(),'s',sessions,owners,rows))
        self.assertFalse(capture_only_record(self.response(),'s',sessions,owners,rows))
        self.assertEqual(len(rows),1);self.assertEqual(rows['r']['usage']['total_tokens'],12)

    def test_foreign_owner_or_model_is_rejected(self):
        with self.assertRaises(ValueError):capture_only_record(self.response(),'s',{'s':dict(model='gpt-6-luna')},{},{})
        with self.assertRaises(ValueError):capture_only_record(self.response(),'s',{'s':dict(model='gpt-6.1-sol')},{'r':'other'},{})

    def test_conflicting_duplicate_and_invalid_subsets_are_rejected(self):
        sessions={'s':dict(model='gpt-6.1-sol')};owners={};rows={};r=self.response()
        capture_only_record(r,'s',sessions,owners,rows)
        r=self.response();r['usage']['output_tokens']=3;r['usage']['total_tokens']=13
        with self.assertRaises(ValueError):capture_only_record(r,'s',sessions,owners,rows)
        r=self.response();r['usage']['input_tokens_details']['cached_tokens']=11
        with self.assertRaises(ValueError):capture_only_record(r,'s',sessions,owners,{})

    def test_all_zero_usage_is_not_positive_measurement(self):
        r=self.response();r['usage']=dict(input_tokens=0,output_tokens=0,total_tokens=0)
        with self.assertRaises(ValueError):capture_only_record(r,'s',{'s':dict(model='gpt-6.1-sol')},{},{})


if __name__=='__main__':unittest.main()
