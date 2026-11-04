import importlib.util,json,pathlib,tempfile,unittest
from datetime import datetime,timedelta,timezone
spec=importlib.util.spec_from_file_location('pilot',pathlib.Path(__file__).with_name('context_pilot.py'));p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class SecurityGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.path=pathlib.Path(self.tmp.name)/'receipt.json';self.now=datetime.now(timezone.utc);self.image='sha256:'+'a'*64
        self.receipt={'decision':'pass','image_id':self.image,'known_findings':[],**{k:True for k in ['full_graph_reviewed','os_image_scan_complete','malicious_release_review_complete','artifact_integrity_verified','scripts_reviewed']},'checked_at':self.now.isoformat(),'valid_until':(self.now+timedelta(hours=1)).isoformat()}
    def check(self):
        self.path.write_text(json.dumps(self.receipt));return p.validate_receipt(self.path,self.image,self.now)
    def test_complete_current_exact_image_receipt_is_required(self):
        self.check()
        with self.assertRaises(ValueError):p.validate_receipt(None,self.image,self.now)
    def test_any_finding_or_incomplete_review_blocks(self):
        for key,value in [('known_findings',['UNSCORED-ADVISORY']),('os_image_scan_complete',False),('scripts_reviewed',False),('decision','blocked')]:
            old=self.receipt[key];self.receipt[key]=value
            with self.assertRaises(ValueError):self.check()
            self.receipt[key]=old
    def test_receipt_for_different_artifact_cannot_be_reused(self):
        self.receipt['image_id']='sha256:'+'b'*64
        with self.assertRaises(ValueError):self.check()
    def test_expired_or_overlong_receipt_blocks(self):
        for delta in [timedelta(seconds=-1),timedelta(days=30)]:
            self.receipt['valid_until']=(self.now+delta).isoformat()
            with self.assertRaises(ValueError):self.check()

if __name__=='__main__':unittest.main()
