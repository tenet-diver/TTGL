#!/usr/bin/env python3
"""Remove only proven duplicate bytes from sealed study cells.

The XZ archive and original archive/recompression receipts stay unchanged.
Authentication, summaries, embedding receipts and unarchived/changed files stay.
This is outside generation/evaluation and never starts, stops or retries models.
"""
import argparse
from datetime import datetime,timezone
import hashlib
import json
from pathlib import Path,PurePosixPath
import tarfile


def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream,'sha256').hexdigest()


def compact(cell,tag,apply=False):
    cell=cell.resolve()
    archive=cell/'snapshot.tar.xz'
    original=json.loads((cell/'archive.json').read_text())
    receipt=json.loads((cell/'recompression-001.json').read_text())
    if not original.get('verified') or not receipt.get('exact_raw_tar_roundtrip') or sha(archive)!=receipt['xz_sha256']:
        raise ValueError('Verified lossless archive required')
    if not any((cell/n).exists() for n in ('completed.json','stopped.json')):
        raise ValueError('Generation must have ended')
    if (cell/'container-stopped.json').exists() and json.loads((cell/'container-stopped.json').read_text())['exit_code']:
        raise ValueError('Container not sealed')
    keep_suffixes=('embedding-inferences.jsonl','inferences.jsonl','graph-snapshot.json')
    candidates={};changed=[]
    for name,expected in original['file_hashes'].items():
        rel=PurePosixPath(name)
        if rel.is_absolute() or '..' in rel.parts:raise ValueError('Unsafe archived name')
        if rel.name=='auth.json' or 'credential' in rel.name.lower():continue
        eligible=(name.startswith(('captures/','maintenance-owned-sessions/','memory/requests/','memory/backend/maintenance/'))
                  or name=='home/models_cache.json')
        if not eligible or name.endswith(keep_suffixes):continue
        path=cell/name
        if not path.exists():continue
        if path.is_symlink() or not path.is_file() or sha(path)!=expected:
            changed.append(name);continue
        candidates[name]=dict(sha256=expected,bytes=path.stat().st_size)
    # Verify the original member bytes, not just a receipt referring to them.
    with tarfile.open(archive) as tar:
        for name,item in candidates.items():
            stream=tar.extractfile(name)
            if stream is None or hashlib.file_digest(stream,'sha256').hexdigest()!=item['sha256']:
                raise ValueError('Archived member mismatch: '+name)
    result=dict(at=datetime.now(timezone.utc).isoformat(),archive_sha256=receipt['xz_sha256'],
                candidates=candidates,changed_or_unarchived_retained=changed,bytes=sum(r['bytes'] for r in candidates.values()),
                model_calls=0,authentication_touched=False,unique_evidence_deleted=False,applied=apply)
    if apply:
        plan=cell/f'duplicate-compaction-{tag}-plan.json'
        with plan.open('x') as stream:json.dump(result,stream,indent=2)
        removed=[]
        for name,item in candidates.items():
            path=cell/name
            if path.is_symlink() or sha(path)!=item['sha256']:
                raise ValueError('Duplicate changed after plan; cleanup stopped')
            path.unlink();removed.append(name)
        result['removed']=removed
        with (cell/f'duplicate-compaction-{tag}-completed.json').open('x') as stream:json.dump(result,stream,indent=2)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--cell',type=Path,required=True);p.add_argument('--tag',required=True);p.add_argument('--apply',action='store_true')
    a=p.parse_args();r=compact(a.cell,a.tag,a.apply);print(json.dumps(dict(cell=a.cell.name,bytes=r['bytes'],files=len(r['candidates']),applied=r['applied'])))
