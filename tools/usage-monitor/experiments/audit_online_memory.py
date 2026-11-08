"""Session-grouped read-only Langfuse audit, including continued native turns."""
import argparse,json
from pathlib import Path
from audit_langfuse_study import audit
from cost_context_study import REPO
def main(root):
 result=json.loads((root/'results.json').read_text());grouped={};seen=set()
 for cell in result['cells']:
  sid=cell['session_id'];target=grouped.setdefault(sid,dict(session_id=sid,native_response_ids=[],usage={k:0 for k in cell['usage']}))
  for ident in cell['native_response_ids']:
   if ident in seen:raise ValueError('Duplicate response in source results')
   seen.add(ident);target['native_response_ids'].append(ident)
  for k,v in cell['usage'].items():target['usage'][k]+=v
 directory=root/'langfuse-session-accounting-001';directory.mkdir();(directory/'results.json').write_text(json.dumps(dict(cells=list(grouped.values())),indent=2))
 receipt=audit(directory,REPO/'work/security/langfuse-stack/local-access.json','2026-11-08T00:00:00Z','2026-11-10T00:00:00Z')
 with (root/'langfuse-audit-001.json').open('x') as f:json.dump(receipt,f,indent=2)
 print(json.dumps(dict(sessions=len(grouped),all_reconciled=receipt['all_reconciled'])),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('root',type=Path);main(p.parse_args().root)
