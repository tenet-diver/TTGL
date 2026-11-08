"""Check canonical backend routing without contacting a model."""
import unittest
from unittest.mock import patch
import capture_proxy_native_routes as routes


class RoutesTests(unittest.TestCase):
    def test_fixed_prefix_only_and_query_preservation(self):
        cases={
            '/backend-api/codex/responses':'/responses',
            '/backend-api/codex/responses/compact?probe=1':'/responses/compact?probe=1',
            '/backend-api/codex-neighbor/responses':'/backend-api/codex-neighbor/responses',
            'https://untrusted.invalid/backend-api/codex/responses':'https://untrusted.invalid/backend-api/codex/responses',
            '/responses':'/responses',
        }
        for original,expected in cases.items():
            with self.subTest(path=original):
                handler=object.__new__(routes.Handler);handler.path=original
                with patch.object(routes.capture.Handler,'proxy',autospec=True,side_effect=lambda obj:obj.path):
                    self.assertEqual(handler.proxy(),expected)
                    self.assertEqual(handler.downstream_path,original)


if __name__=='__main__':unittest.main()
