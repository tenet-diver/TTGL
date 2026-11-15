from pathlib import Path
import socket
import tempfile
import unittest

from team_memory_socket_guard import expected_socket,clear_dead_socket


class SocketGuardTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.cell=Path(self.tmp.name)/'cell'
        self.path=expected_socket(self.cell);self.addCleanup(lambda:self.path.unlink(missing_ok=True));self.spec=dict(socket=str(self.path))

    def test_dead_endpoint_is_removed_without_record_deletion(self):
        s=socket.socket(socket.AF_UNIX);s.bind(str(self.path));s.close()
        value=clear_dead_socket(self.cell,self.spec);self.assertTrue(value['removed']);self.assertFalse(self.path.exists())

    def test_bound_live_endpoint_is_preserved_even_before_listen(self):
        with socket.socket(socket.AF_UNIX) as s:
            s.bind(str(self.path))
            with self.assertRaises(RuntimeError):clear_dead_socket(self.cell,self.spec)
            self.assertTrue(self.path.exists())

    def test_ordinary_file_is_never_removed(self):
        self.path.write_text('retained')
        with self.assertRaises(ValueError):clear_dead_socket(self.cell,self.spec)
        self.assertEqual(self.path.read_text(),'retained')

    def test_other_assignment_path_is_rejected(self):
        with self.assertRaises(ValueError):clear_dead_socket(self.cell,dict(socket='/tmp/unrelated.sock'))


if __name__=='__main__':unittest.main()
