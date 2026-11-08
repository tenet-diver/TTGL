import unittest,tempfile,json
from pathlib import Path
from smallville_compat import CompatibleMemory
from smallville_compat_v2 import CompatibleMemoryV2
class Compatibility(unittest.TestCase):
 def test_modern_and_legacy_focal(self):
  for output in (['why','what','how'],"['why', 'what', 'how']"):
   with tempfile.TemporaryDirectory() as t:
    m=CompatibleMemory(Path(t),lambda s:[1.,0.],lambda p,r:json.dumps({'output':output}),{})
    self.assertEqual(m._focal(m.persona,'observed',3)[0],['why','what','how'])
 def test_comma_in_completion_object(self):
  with tempfile.TemporaryDirectory() as t:
   m=CompatibleMemoryV2(Path(t),lambda s:[1.,0.],lambda p,r:'observed, input, with commas)',{})
   self.assertEqual(m._triple('input',m.persona)[0],('TTGL agent','observed','input, with commas'))
 def test_invalid_focal_rejected(self):
  with tempfile.TemporaryDirectory() as t:
   m=CompatibleMemory(Path(t),lambda s:[1.,0.],lambda p,r:'{"output":["incomplete"]}',{})
   with self.assertRaises(ValueError):m._focal(m.persona,'observed',3)
if __name__=='__main__':unittest.main()
