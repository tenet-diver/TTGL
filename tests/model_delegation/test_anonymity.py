import json,tempfile,unittest,shutil
from pathlib import Path
from ttgl.model_delegation.anonymity import client_paths,audit_environment


class AnonymityTests(unittest.TestCase):
    def test_physical_cwd_and_home_do_not_reveal_registered_case_or_condition(self):
        with tempfile.TemporaryDirectory() as d:
            output=Path(d)/'secret-benchmark-123'/'sol-condition'
            native,workspace=client_paths(output)
            try:
                for path in (native,workspace):
                    self.assertNotIn('secret-benchmark-123',str(path.resolve()))
                    self.assertNotIn('sol-condition',str(path.resolve()))
                self.assertEqual((output/'native').resolve(),native)
                self.assertEqual((output/'client-workspace').resolve(),workspace)
                self.assertEqual(workspace.stat().st_mode & 0o777,0o700)
            finally:shutil.rmtree(native.parent)

    def test_audit_checks_recorded_visible_environment_not_only_user_prompt(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d);f=p/'coding/client-home/sessions/session.jsonl';f.parent.mkdir(parents=True)
            f.write_text(json.dumps({'type':'response_item','payload':{'type':'message','role':'user','content':[{'text':'<environment_context>cwd: /private/secret-benchmark-123</environment_context>'}]}})+'\n')
            audit=audit_environment(p,['secret-benchmark-123'])
            self.assertEqual(audit['environment_messages_observed'],1)
            self.assertTrue(audit['forbidden_identity_exposed'])

    def test_model_route_view_hides_benchmark_parent_ids_without_mutating_host_evidence(self):
        from ttgl.model_delegation.live_delegation import model_decision_view
        host={'decision_id':'host-hash','candidates':[{'evidence':[{'id':'evidence-ref','task_id':'sympy__sympy-secret','weight':1}]}]}
        public=model_decision_view(host)
        self.assertNotIn('sympy__sympy-secret',json.dumps(public))
        self.assertEqual(host['candidates'][0]['evidence'][0]['task_id'],'sympy__sympy-secret')
        self.assertEqual(public['decision_id'],'host-hash')
        self.assertEqual(len(public['candidates'][0]['evidence'][0]['source_parent_ref']),64)
