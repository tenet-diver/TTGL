import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from exact_source_archive import ExactSourceArchive
from context_archive_policy import rewrite
from analyst_mcp import handle
from workspace import Store
from capture_proxy import sanitized


class ExactArchiveContracts(unittest.TestCase):
    def test_persisted_recovery_and_idempotent_no_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=ExactSourceArchive(Path(tmp)/'sources',lambda text:text)
            text='Observed line: λ\n'*100;digest=hashlib.sha256(text.encode()).hexdigest()
            store(digest,text);before=(store.root/(digest+'.json')).read_bytes()
            store(digest,text)
            self.assertEqual(store.read(digest),text)
            self.assertEqual((store.root/(digest+'.json')).read_bytes(),before)
            self.assertFalse(list(store.root.glob('*.tmp')))

    def test_redaction_size_or_hash_failure_never_creates_false_exact_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            store=ExactSourceArchive(tmp,lambda text:text.replace('planted-secret','[REDACTED]'),max_source_bytes=100)
            for text,digest in [('planted-secret',hashlib.sha256(b'planted-secret').hexdigest()),('x'*101,hashlib.sha256(b'x'*101).hexdigest()),('text','0'*64)]:
                with self.assertRaises(ValueError):store(digest,text)
            self.assertFalse(list(Path(tmp).glob('*.json')))

    def test_existing_redacted_record_is_preserved_and_transform_fails_open(self):
        with tempfile.TemporaryDirectory() as tmp:
            text='value '*300;digest=hashlib.sha256(text.encode()).hexdigest();path=Path(tmp)/(digest+'.json')
            path.write_text(json.dumps(dict(source_sha256=digest,retained_sha256='0'*64,content='[REDACTED]')))
            before=path.read_bytes();store=ExactSourceArchive(tmp,lambda text:text)
            doc=dict(input=[dict(type='function_call_output',call_id='one',output=text)])
            updated,meta=rewrite(doc,'reversible-handles',store)
            self.assertEqual(updated,doc);self.assertEqual(meta['changes'],[])
            self.assertEqual(path.read_bytes(),before)

    def test_existing_mcp_handler_recovers_actual_archive_and_raw_bypasses_mask(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);captures=root/'captures';source=ExactSourceArchive(captures/'compression_sources',sanitized)
            original='Verified diagnostic row λ, no credentials.\n'*100
            digest=hashlib.sha256(original.encode()).hexdigest();source(digest,original)
            store=Store(root/'data',root/'empty-native-source','http://localhost:3000',captures)
            reply=handle(store,dict(method='tools/call',params=dict(name='read_compression_source',arguments=dict(sha256=digest,limit=16000))))
            self.assertFalse(reply.get('isError'))
            recovered=json.loads(reply['content'][0]['text'])
            self.assertEqual(recovered['content'],original)
            self.assertEqual(recovered['retained_sha256'],digest)
            self.assertTrue(recovered['TTGL_RAW_EVIDENCE'])
            doc=dict(input=[dict(type='function_call_output',call_id='retrieval',output=reply)])
            self.assertEqual(rewrite(doc,'reversible-handles',source)[0],doc)


if __name__=='__main__':unittest.main()
