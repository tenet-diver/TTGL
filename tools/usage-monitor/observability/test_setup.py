import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import tomllib
import unittest
from urllib.parse import urlsplit

import setup_local


class SetupTests(unittest.TestCase):
    def test_repeated_prepare_preserves_credentials_and_pins_full_stack(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with contextlib.redirect_stdout(io.StringIO()):
                setup_local.prepare_configs(root, root / 'workspace', root / 'codex', 'http://localhost:3000', 'http://localhost:9090')
                credentials = (root / 'local-access.json').read_bytes()
                setup_local.prepare_configs(root, root / 'workspace', root / 'codex', 'http://localhost:3000', 'http://localhost:9090')
            self.assertEqual(credentials, (root / 'local-access.json').read_bytes())
            stack = json.loads((root / 'compose.json').read_text())
            lock = json.loads((setup_local.CONFIG / 'deployment.lock.json').read_text())
            self.assertEqual(set(stack['services']), set(lock['images']))
            for name, service in stack['services'].items():
                self.assertEqual(service['image'], lock['images'][name]['image'])
                self.assertIn('@sha256:', service['image'])
                self.assertEqual(service['pull_policy'], 'never')
                for port in service.get('ports', []):
                    self.assertTrue(port.startswith('127.0.0.1:'))
            self.assertEqual(os.stat(root / 'compose.json').st_mode & 0o777, 0o600)
            self.assertTrue('${' not in (root / 'compose.json').read_text(), 'Unresolved template variable')
            self.assertEqual(stack['services']['langfuse-web']['environment']['NEXTAUTH_URL'], 'http://localhost:3000')
            profile = tomllib.loads((root / 'ttgl-observability.config.toml').read_text())
            self.assertEqual(profile['model_provider'], 'openai')
            self.assertFalse(profile['features']['enable_request_compression'])
            self.assertEqual(profile['mcp_servers']['ttgl-analyst']['args'][2], str(root / 'workspace'))

    def test_template_missing_variable_fails(self):
        with self.assertRaises(KeyError):
            setup_local.render('${UNDEFINED}', {})

    def test_generated_paths_are_escaped_for_toml(self):
        with tempfile.TemporaryDirectory(prefix='ttgl setup ') as directory:
            root = Path(directory)
            with contextlib.redirect_stdout(io.StringIO()):
                setup_local.prepare_configs(root, root / 'workspace "quoted"', root / 'codex', 'http://localhost:3000')
            profile = tomllib.loads((root / 'ttgl-observability.config.toml').read_text())
            self.assertIn(str(root / 'workspace "quoted"'), profile['mcp_servers']['ttgl-analyst']['args'])

    def test_provider_and_compose_ports_match_recorded_defaults(self):
        config = setup_local.CONFIG
        defaults = json.loads((config / 'defaults.json').read_text())
        provider = tomllib.loads((config / 'codex-provider.toml').read_text())
        self.assertEqual(urlsplit(provider['model_providers']['ttgl_capture']['base_url']).port, defaults['ports']['capture'])
        compose = json.loads((config / 'compose.template.json').read_text())
        self.assertEqual(compose['services']['langfuse-web']['ports'], [f"127.0.0.1:{defaults['ports']['langfuse']}:3000"])
        self.assertEqual(compose['services']['minio']['ports'], [f"127.0.0.1:{defaults['ports']['s3']}:9000", f"127.0.0.1:{defaults['ports']['s3_console']}:9001"])


if __name__ == '__main__':
    unittest.main()


class LiveConfigTests(unittest.TestCase):
    def test_provider_install_preserves_unrelated_config_and_has_real_profile(self):
        from install_live_codex import install
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); config=root/'config.toml'
            config.write_text('model = "my-existing-model"\n[features]\nother_feature = true\n[mcp_servers.other]\ncommand = "unchanged"\n')
            import contextlib,io
            with contextlib.redirect_stdout(io.StringIO()): install(config,'progress',root/'private')
            parsed=tomllib.loads(config.read_text())
            self.assertEqual(parsed['model'],'my-existing-model')
            self.assertTrue(parsed['features']['other_feature'])
            self.assertEqual(parsed['mcp_servers']['other']['command'],'unchanged')
            self.assertEqual(parsed['model_provider'],'openai')
            self.assertEqual(tomllib.loads((config.parent/'ttgl-observability.config.toml').read_text())['model_provider'],'openai')
            self.assertEqual(tomllib.loads((config.parent/'ttgl-capture-experimental.config.toml').read_text())['model_provider'],'ttgl_capture')
            self.assertTrue(parsed['model_providers']['ttgl_capture']['base_url'].endswith('/compress/progress'))
            self.assertEqual(len(list((root/'private').glob('codex-config-before-live-*'))),1)

    def test_existing_global_capture_is_migrated_without_removing_analyst(self):
        from install_live_codex import install
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = root / 'config.toml'
            config.write_text('model_provider = "ttgl_capture"\n[mcp_servers.ttgl-analyst]\ncommand = "python3"\n[profiles.ttgl-observability]\nmodel_provider = "ttgl_capture"\n')
            with contextlib.redirect_stdout(io.StringIO()):
                install(config, 'headroom-lossless', root / 'private')
            parsed = tomllib.loads(config.read_text())
            self.assertEqual(parsed['model_provider'], 'openai')
            self.assertEqual(tomllib.loads((config.parent/'ttgl-observability.config.toml').read_text())['model_provider'], 'openai')
            self.assertEqual(parsed['mcp_servers']['ttgl-analyst']['command'], 'python3')
            self.assertIn('ttgl_capture', parsed['model_providers'])
            self.assertNotIn('ttgl-observability', parsed.get('profiles', {}))
