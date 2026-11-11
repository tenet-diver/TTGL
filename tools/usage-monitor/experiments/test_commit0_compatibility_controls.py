import io
from pathlib import Path
import tarfile
import tempfile
import unittest

from commit0_compatibility_controls import extract


class ExtractionBoundary(unittest.TestCase):
    def archive(self, root, entries):
        path = root / 'input.tar'
        with tarfile.open(path, 'w') as out:
            for name, text, target in entries:
                info = tarfile.TarInfo(name)
                if target is not None:
                    info.type, info.linkname = tarfile.SYMTYPE, target
                    out.addfile(info)
                else:
                    body = text.encode()
                    info.size = len(body)
                    out.addfile(info, io.BytesIO(body))
        return path

    def test_internal_readme_link(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            archive = self.archive(root, [('repo/README.md', 'public', None),
                                          ('repo/README.rst', '', 'README.md')])
            hashes = extract(archive, root / 'source')
            self.assertEqual((root / 'source/README.rst').read_text(), 'public')
            self.assertEqual(hashes['README.md'], hashes['README.rst'])

    def test_escaping_members_and_links(self):
        for entry in [('/outside', 'bad', None), ('repo/../outside', 'bad', None),
                      ('repo/link', '', '../../outside'), ('repo/link', '', '/etc/passwd')]:
            with self.subTest(entry=entry), tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                archive = self.archive(root, [entry])
                with self.assertRaises((ValueError, tarfile.FilterError)):
                    extract(archive, root / 'source')
                self.assertFalse((root / 'outside').exists())


if __name__ == '__main__':
    unittest.main()
