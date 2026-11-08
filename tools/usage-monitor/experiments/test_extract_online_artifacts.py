import base64,json,tempfile,unittest
from pathlib import Path
from extract_online_artifacts import extract,sha
class PrivateArchiveView(unittest.TestCase):
 def fixture(self,root,complete=True,unsafe=False):
  cell=root/'assignments/one';cell.mkdir(parents=True);work=root/'graded';work.mkdir();sealed=work/'sealed-cfg';sealed.mkdir();engine='def normalize(value): return dict(value)\n';(sealed/'engine.py').write_text(engine)
  values={'engine.py':base64.b64encode(engine.encode()).decode(),'cfgd_data.json':base64.b64encode(b'PRIVATE_ORACLE_SENTINEL').decode(),'.key':base64.b64encode(b'PRIVATE_KEY_SENTINEL').decode()}
  if unsafe:values['../escape.py']=base64.b64encode(b'unsafe').decode()
  archive=cell/'sealed-cfg.json';archive.write_text(json.dumps(values));(cell/'manifest.json').write_text(json.dumps(dict(work=str(work))));(cell/'sealed-state.json').write_text(json.dumps(dict(archive_sha256=sha(archive))));(root/'protocol.json').write_text(json.dumps(dict(assignments=[dict(id='one',task='unknown')])))
  if complete:(cell/'complete.json').write_text(json.dumps(dict(full_horizon_elapsed=True)))
  return cell
 def test_only_submitted_engine_is_exposed_and_matches_graded_copy(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);cell=self.fixture(root);extract(root,'one');paths=[p for p in (cell/'artifact-view-001').rglob('*') if p.is_file()];self.assertEqual([p.name for p in paths],['engine.py']);all_bytes=b''.join(p.read_bytes() for p in paths);self.assertNotIn(b'PRIVATE_ORACLE_SENTINEL',all_bytes);self.assertNotIn(b'PRIVATE_KEY_SENTINEL',all_bytes);self.assertTrue((cell/'artifact-view-001-provenance.json').exists())
 def test_live_assignment_cannot_create_a_review_view(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);cell=self.fixture(root,False)
   with self.assertRaisesRegex(ValueError,'still live'):extract(root,'one')
   self.assertFalse((cell/'artifact-view-001').exists())
 def test_unsafe_path_is_rejected_before_output(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);cell=self.fixture(root,unsafe=True)
   with self.assertRaisesRegex(ValueError,'Unsafe archive'):extract(root,'one')
   self.assertFalse((cell/'artifact-view-001').exists())
 def test_changed_sealed_source_is_not_reviewed_as_original(self):
  with tempfile.TemporaryDirectory() as tmp:
   root=Path(tmp);cell=self.fixture(root);(root/'graded/sealed-cfg/engine.py').write_text('changed')
   with self.assertRaisesRegex(ValueError,'sealed grading source differ'):extract(root,'one')
   self.assertFalse((cell/'artifact-view-001').exists())
if __name__=='__main__':unittest.main()
