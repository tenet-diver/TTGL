import json
from pathlib import Path
import tempfile
import unittest
from json_corpus import array_records,select_records

class CorpusTests(unittest.TestCase):
    def read(self,text,**kw):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'data.json';p.write_text(text);return list(array_records(p,chunk_size=3,**kw))
    def test_chunk_boundaries_and_unicode(self):
        rows=[{'question_id':'one','body':'é \\" ] , '+('x'*100)}, {'question_id':'two'}]
        self.assertEqual(self.read(json.dumps(rows,ensure_ascii=False)),rows)
        self.assertEqual(self.read(' [ ] '),[])
    def test_malformed_corpus_fails(self):
        for text in ('[{},]','[{}','[{} {}]','[{}] {}','{}','[1]'):
            with self.subTest(text=text),self.assertRaises(ValueError):self.read(text)
        with self.assertRaises(ValueError):self.read('[{"a":"'+'x'*100+'"}]',max_record_characters=20)
    def test_selection_requires_exact_unique_ids(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'d.json';p.write_text('[{"question_id":"a"},{"question_id":"b"}]')
            self.assertEqual(set(select_records(p,['b'])),{'b'})
            with self.assertRaises(ValueError):select_records(p,['c'])
            p.write_text('[{"question_id":"b"},{"question_id":"b"}]')
            with self.assertRaises(ValueError):select_records(p,['b'])
if __name__=='__main__':unittest.main()
