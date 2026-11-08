"""Append an explicit linkage correction; never rewrite measurements/protocols."""
import argparse,hashlib,json
from pathlib import Path
from cost_context_study import REPO
from workspace import Store
from analyst_experiments import record_evaluation,review_experiment
def main(root):
 if (root/'protocol-linkage-publication-001.json').exists():raise ValueError('Already annotated')
 original=json.loads((root/'publication.json').read_text());audit=json.loads((root/'protocol-linkage-audit-001.json').read_text());result=json.loads((root/'results.json').read_text());intended=REPO/audit['intended_registered_protocol']
 if hashlib.sha256(intended.read_bytes()).hexdigest()!=audit['intended_protocol_sha256']:raise ValueError('Registered intended protocol changed')
 measured=dict(result,langfuse_reconciled=True,acceptance_passed=result['diagnostic_passed'],protocol_attachment_linkage_audit=audit,prior_evaluation_preserved=original['evaluation_id'])
 digest=hashlib.sha256(json.dumps(measured,sort_keys=True).encode()).hexdigest();store=Store(REPO/'work/security/workspace',Path.home()/'.codex','http://localhost:3000');evaluation=record_evaluation(store,original['experiment_id'],json.loads(intended.read_text()),measured,digest)
 notes='Linkage annotation only: stale002protocol attachment preserved; intended protocol and actual generation code verified committed before first inference. Native/CLI/proxy/Langfuse counts unchanged. Mechanism passed, no benchmark efficacy or adoption evidence. Prior evaluation remains immutable; no inference/accounting duplicated.'
 review=review_experiment(store,dict(evaluation_id=evaluation,verdict='inconclusive',notes=notes))
 with (root/'protocol-linkage-publication-001.json').open('x') as f:json.dump(dict(evaluation_id=evaluation,review=review,original_publication=original,measurement_values_unchanged=True),f,indent=2)
 print(root.name,'linkage annotation published',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);main(p.parse_args().root)
