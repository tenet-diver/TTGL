"""Check vendored definitions and templates against pinned upstream fingerprints."""
import ast,hashlib,json
from pathlib import Path
import unittest
from smallville_memory import VENDOR


class FidelityTests(unittest.TestCase):
    def test_original_definitions_and_template_bytes(self):
        manifest=json.loads((VENDOR/'SOURCE_MAP.json').read_text())
        self.assertEqual(manifest['commit'],'fe05a71d3e4ed7d10bf68aa4eda6dd995ec070f4')
        for item in manifest['files']:
            path=VENDOR/item['file'];raw=path.read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),item['vendored_sha256'])
            if 'definitions' not in item:
                self.assertEqual(item['upstream_sha256'],item['vendored_sha256']);continue
            text=raw.decode();definitions={n.name:n for n in ast.parse(text).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
            for original in item['definitions']:
                segment=ast.get_source_segment(text,definitions[original['name']])
                self.assertEqual(hashlib.sha256(segment.encode()).hexdigest(),original['source_sha256'])


if __name__=='__main__':unittest.main()
