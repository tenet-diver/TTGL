"""Read-only derivation of submitted code from completed sealed task archives.

No inference, grading, policy decision or live-actor access. Unknown-task private
oracle/key/verifier data is never copied into the review view: only engine.py.
"""
import argparse,base64,hashlib,json
from pathlib import Path
from cost_context_study import REPO
POINTER=REPO/'work/security/context-memory-20261107/online-longhorizon-development-001.json'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def extract(root,assignment):
 protocol=json.loads((root/'protocol.json').read_text());spec=next(s for s in protocol['assignments'] if s['id']==assignment);cell=root/'assignments'/assignment
 if not (cell/'complete.json').exists() or not json.loads((cell/'complete.json').read_text())['full_horizon_elapsed']:raise ValueError('Assignment still live/incomplete; no early artifact view')
 output=cell/'artifact-view-001'
 if output.exists():raise ValueError('Immutable review view exists; inspect instead of replace')
 archive=cell/('sealed-cfg.json' if spec['task']=='unknown' else 'sealed-workspace.json');values=json.loads(archive.read_bytes());selected={}
 manifest=json.loads((cell/'manifest.json').read_text());work=Path(manifest['work']);graded=work/('sealed-cfg' if spec['task']=='unknown' else 'sealed/workspace' if spec['task']=='fuzz' else 'sealed')
 if spec['task']=='unknown' and json.loads((cell/'sealed-state.json').read_text())['archive_sha256']!=sha(archive):raise ValueError('Sealed unknown archive changed')
 for name,encoded in values.items():
  path=Path(name)
  if path.is_absolute() or '..' in path.parts:raise ValueError('Unsafe archive path')
  if spec['task']=='unknown' and name!='engine.py':continue
  if spec['task']!='unknown' and path.suffix.lower() not in ('.py','.sql','.sh','.md','.toml','.txt','.json','.yaml','.yml'):continue
  raw=base64.b64decode(encoded,validate=True)
  if len(raw)>1048576:raise ValueError('Review source exceeds bounded size; inspect explicitly')
  if not (graded/path).is_file() or hashlib.sha256(raw).hexdigest()!=sha(graded/path):raise ValueError('Archive and actual sealed grading source differ')
  selected[name]=raw
 if spec['task']=='unknown' and 'engine.py' not in selected:raise ValueError('Missing submitted engine')
 output.mkdir(mode=0o700);sources={str(archive):sha(archive)};files=[]
 for name,raw in selected.items():
  p=output/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw);p.chmod(0o600);digest=sha(p);sources[str(p)]=digest;files.append(dict(name=name,bytes=len(raw),sha256=digest))
 receipt=dict(assignment=assignment,task=spec['task'],sealed_archive=str(archive),sealed_archive_sha256=sha(archive),submitted_files=files,source_hashes=sources,hidden_oracle_or_verifier_contents_exported=False,review_status='not_yet_assessed',model_calls=0,scope='Derived submitted-source view only; no grade rewrite or automatic artifact-compliance claim')
 with (cell/'artifact-view-001-provenance.json').open('x') as f:json.dump(receipt,f,indent=2)
 print(json.dumps(dict(assignment=assignment,output=str(output),files=len(files),model_calls=0)),flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('assignment');a=p.parse_args();extract(Path(json.loads(POINTER.read_text())['root']),a.assignment)
