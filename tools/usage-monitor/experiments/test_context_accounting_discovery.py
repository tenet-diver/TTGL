import json
from pathlib import Path
import tempfile
import unittest
from account_context_memory import long_history_sessions

class DiscoveryTests(unittest.TestCase):
    def test_preserves_partial_threads_and_separates_roles(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for rel,sid in [('case-00/fts','reader'),('case-00/fts/judge','judge'),('case-00/mem0-build/extractions/extract-001','failed-extractor')]:
                p=root/'longmemeval-001'/rel;p.mkdir(parents=True)
                (p/'agent.jsonl').write_text(json.dumps(dict(type='thread.started',thread_id=sid))+'\n'+('{"partial"' if sid=='failed-extractor' else ''))
            self.assertEqual(long_history_sessions(root),{'reader':'long_history_readers','judge':'evaluation_judges','failed-extractor':'memory_extraction'})
    def test_duplicate_thread_artifacts_are_not_silently_added(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for arm in ('fts','file_search'):
                p=root/'longmemeval-001'/'case-00'/arm;p.mkdir(parents=True)
                (p/'agent.jsonl').write_text(json.dumps(dict(type='thread.started',thread_id='duplicate'))+'\n')
            with self.assertRaises(ValueError):long_history_sessions(root)
if __name__=='__main__':unittest.main()
