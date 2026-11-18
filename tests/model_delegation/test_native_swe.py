import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from ttgl.model_delegation.native_swe import normalize_git_modes, _test_body, _patch_paths


class NativeSWETests(unittest.TestCase):
    def test_git_modes_override_host_umask_without_changing_bytes(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)
            subprocess.run(['git', 'init', '-q', d], check=True)
            for name, mode in [('plain.py', 0o644), ('runner', 0o755)]:
                q = p/name; q.write_bytes(b'original\n'); q.chmod(mode)
            subprocess.run(['git', 'add', '.'], cwd=d, check=True)
            (p/'runner').chmod(0o756); (p/'plain.py').chmod(0o666)
            normalize_git_modes(p)
            self.assertEqual((p/'runner').stat().st_mode & 0o777, 0o755)
            self.assertEqual((p/'plain.py').stat().st_mode & 0o777, 0o644)
            self.assertEqual((p/'runner').read_bytes(), b'original\n')

    def test_script_requires_single_official_boundary_and_keeps_command(self):
        script = 'setup\necho ">>>>> Start Test Output"\npython3 original.py --flag\necho ">>>>> End Test Output"\n'
        body = _test_body(script)
        self.assertIn('\npython3 original.py --flag\n', body)
        self.assertNotIn('setup', body)
        with self.assertRaises(ValueError): _test_body(script+script)
        with self.assertRaises(ValueError): _patch_paths('+++ b/../private')
