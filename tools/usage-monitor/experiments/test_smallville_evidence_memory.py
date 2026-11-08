import hashlib,json,sqlite3,tempfile,unittest
from pathlib import Path
from smallville_evidence_memory import EvidenceMemory
class EvidenceTests(unittest.TestCase):
 def test_exact_archive_restart_and_retrieval_provenance(self):
  episodes=[dict(id='a',body='earlier route north. '+('unrelated record. '*130)),dict(id='b',body='latest route south. '+('another record. '*130))]
  def embed(s):return [1.,float('south' in s)]
  with tempfile.TemporaryDirectory() as t:
   path=Path(t)/'memory.sqlite';m=EvidenceMemory(path,embed);m.build(episodes)
   with sqlite3.connect(path) as db:
    for e in episodes:
     chunks=db.execute('SELECT body FROM chunks WHERE episode=? ORDER BY offset',(e['id'],)).fetchall()
     self.assertEqual(''.join(x[0] for x in chunks),e['body'])
   hits=EvidenceMemory(path,embed).query('latest south route')['hits'];self.assertTrue(hits)
   for h in hits:
    e=next(e for e in episodes if e['id']==h['episode']);self.assertEqual(e['body'][h['offset']:h['offset']+len(h['body'])],h['body']);self.assertEqual(hashlib.sha256(h['body'].encode()).hexdigest(),h['sha256'])
   with self.assertRaises(ValueError):m.build(episodes)
 def test_namespace_separation(self):
  with tempfile.TemporaryDirectory() as t:
   a=EvidenceMemory(Path(t)/'a.sqlite',lambda s:[1.,1.]);b=EvidenceMemory(Path(t)/'b.sqlite',lambda s:[1.,1.]);a.build([dict(id='one',body='private alpha')]);b.build([dict(id='one',body='private beta')]);self.assertNotIn('alpha',json.dumps(b.query('private')['hits']))
if __name__=='__main__':unittest.main()
