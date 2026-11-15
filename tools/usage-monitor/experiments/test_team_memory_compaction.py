import hashlib,json,lzma,tarfile,tempfile,unittest
from pathlib import Path
from compact_team_memory_evidence import compact


class ArchiveGuardTests(unittest.TestCase):
    def fixture(self,root):
        (root/'captures').mkdir();(root/'captures/body.json').write_text('original evidence')
        (root/'auth.json').write_text('do not touch');(root/'completed.json').write_text('{}')
        with tarfile.open(root/'raw.tar','w') as t:t.add(root/'captures/body.json',arcname='captures/body.json')
        archive=root/'snapshot.tar.xz';archive.write_bytes(lzma.compress((root/'raw.tar').read_bytes()))
        (root/'archive.json').write_text(json.dumps(dict(verified=True,file_hashes={'captures/body.json':hashlib.sha256(b'original evidence').hexdigest(),'auth.json':hashlib.sha256(b'do not touch').hexdigest()})))
        (root/'recompression-001.json').write_text(json.dumps(dict(exact_raw_tar_roundtrip=True,xz_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())))

    def test_only_exact_duplicate_removed_and_archive_auth_retained(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.fixture(root);r=compact(root,'001',True)
            self.assertEqual(r['removed'],['captures/body.json'])
            self.assertEqual((root/'auth.json').read_text(),'do not touch')
            with tarfile.open(root/'snapshot.tar.xz') as t:self.assertEqual(t.extractfile('captures/body.json').read(),b'original evidence')

    def test_changed_source_or_bad_archive_never_deleted(self):
        with tempfile.TemporaryDirectory() as temp:
            root=Path(temp);self.fixture(root);(root/'captures/body.json').write_text('new evidence')
            self.assertEqual(compact(root,'001')['candidates'],{})
            (root/'snapshot.tar.xz').write_bytes(b'corrupt')
            with self.assertRaises(ValueError):compact(root,'001',True)
            self.assertEqual((root/'captures/body.json').read_text(),'new evidence')


if __name__=='__main__':unittest.main()
