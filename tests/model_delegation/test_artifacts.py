import tempfile
import unittest
from pathlib import Path
from ttgl.model_delegation.artifacts import retain_base, retain_delta, restore_delta
from ttgl.experience_routing.checkpoints import manifest
from ttgl.experience_routing.io import digest


class MemoryS3:
    """Fixture transport; production uses verified literal-loopback S3."""
    def __init__(self): self.objects = {}
    def retain_file(self, path, *, kind, identity):
        data = Path(path).read_bytes(); key = digest(data); self.objects[key] = data
        return {'sha256': key, 'artifactId': key, 'bytes': len(data)}


class ArtifactTests(unittest.TestCase):
    def test_exact_replay_of_add_delete_modify_mode_and_link(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = root/'source'; source.mkdir(); out = root/'out'; out.mkdir()
            (source/'edit.py').write_text('old\n'); (source/'delete.py').write_text('delete\n')
            (source/'mode.sh').write_text('mode\n'); (source/'mode.sh').chmod(0o644)
            before = manifest(source); client = MemoryS3(); base = retain_base(source, out, client)
            (source/'edit.py').write_text('new\n'); (source/'delete.py').unlink()
            (source/'new.py').write_bytes(b'exact\x00\r\nbytes'); (source/'mode.sh').chmod(0o755)
            (source/'link').symlink_to('edit.py')
            artifact = retain_delta(source, before, base, out, client)
            state = restore_delta(client.objects[base['archive']['sha256']], client.objects[artifact['sha256']], root/'replay', artifact=artifact)
            self.assertEqual(state, manifest(source))
            self.assertFalse(list(out.glob('*.gz')))
            self.assertEqual((root/'replay/new.py').read_bytes(), b'exact\x00\r\nbytes')

    def test_identical_bases_are_content_addressed_and_small_delta(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = root/'source'; source.mkdir(); out = root/'out'; out.mkdir()
            (source/'unchanged.txt').write_text('a lot of unchanged source\n'*1000)
            (source/'edit.py').write_text('a\n')
            before = manifest(source); client = MemoryS3()
            first = retain_base(source, out, client); second = retain_base(source, out, client)
            self.assertEqual(first, second)
            (source/'edit.py').write_text('b\n')
            artifact = retain_delta(source, before, first, out, client)
            self.assertEqual(artifact['updated_files'], 1)

    def test_modified_base_delta_receipt_and_nonempty_destination_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = root/'source'; source.mkdir(); (source/'app.py').write_text('old\n'); out = root/'out'; out.mkdir()
            client = MemoryS3(); before = manifest(source); base = retain_base(source, out, client)
            (source/'app.py').write_text('new\n'); artifact = retain_delta(source, before, base, out, client)
            b, delta = client.objects[base['archive']['sha256']], client.objects[artifact['sha256']]
            with self.assertRaises(ValueError): restore_delta(b, delta+b'x', root/'one', artifact=artifact)
            with self.assertRaises(ValueError): restore_delta(b, delta, root/'two', artifact={**artifact, 'candidate_state_hash': 'other'})
            with self.assertRaises(ValueError): restore_delta(b, delta, source, artifact=artifact)

    def test_archival_failure_keeps_original_spool(self):
        with tempfile.TemporaryDirectory() as d:
            root = Path(d); source = root/'source'; source.mkdir(); (source/'app.py').write_text('source\n')
            class Failing:
                def retain_file(self, *args, **kwargs): raise RuntimeError('offline')
            with self.assertRaises(RuntimeError): retain_base(source, root, Failing())
            self.assertTrue((root/'base-source.tar.gz').exists())
