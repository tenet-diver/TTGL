import gzip
from pathlib import Path
import sqlite3
import tempfile
import unittest
from capture_objects import CaptureObjects,read_capture


class CaptureObjectTests(unittest.TestCase):
    def test_repeated_history_is_shared_and_values_round_trip(self):
        with tempfile.TemporaryDirectory() as directory:
            store=CaptureObjects(Path(directory)/'capture-objects.sqlite')
            db=store.connect()
            try:
                with db:
                    for i in range(10):
                        value=dict(model='fixture',input=[dict(text='x'*300000+'\u2028tail'),dict(text=str(i),literal={'layout':'ttgl-cas-value-v1','value':'not-a-reference'})])
                        encoded=store.pack(value,db)
                        self.assertEqual(store.unpack(encoded,db),value)
                    self.assertEqual(db.execute('SELECT count(*) FROM objects').fetchone()[0],12)
            finally:db.close()

    def test_corruption_is_rejected_without_replacing_prior_blob(self):
        with tempfile.TemporaryDirectory() as directory:
            store=CaptureObjects(Path(directory)/'capture-objects.sqlite')
            db=store.connect()
            try:
                with db:
                    digest=store.put({'text':'original'},db)
                    broken=gzip.compress(b'corrupt')
                    db.execute('UPDATE objects SET payload=? WHERE digest=?',(broken,digest))
                    with self.assertRaises(ValueError):store.put({'text':'original'},db)
                    self.assertEqual(db.execute('SELECT payload FROM objects WHERE digest=?',(digest,)).fetchone()[0],broken)
            finally:db.close()

    def test_read_only_missing_database_is_not_created(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'capture.json'
            path.write_text('{"capture_content_layout":"sqlite-cas-json-v1","request":{}}')
            with self.assertRaises(sqlite3.OperationalError):read_capture(path)
            self.assertFalse((Path(directory)/'capture-objects.sqlite').exists())


if __name__=='__main__':unittest.main()
