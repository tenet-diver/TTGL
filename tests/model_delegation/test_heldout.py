import tempfile
import unittest
from pathlib import Path

from ttgl.experience_routing.io import write_new
from ttgl.model_delegation.heldout import run


class HeldoutRegistrationTests(unittest.TestCase):
    def test_disabled_registration_stops_before_storage_preparation(self):
        with tempfile.TemporaryDirectory() as directory:
            path = write_new(Path(directory) / 'registration.json', {
                'allow_model_execution': False,
                'automatic_retries': 0,
            })
            with self.assertRaisesRegex(ValueError, 'enabled held-out registration'):
                run(path)
