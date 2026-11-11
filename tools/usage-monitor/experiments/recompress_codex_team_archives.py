#!/usr/bin/env python3
"""Losslessly recompress owned verified tar streams with standard-library XZ.

All raw member bytes, names and metadata are retained. Original receipts remain;
a new receipt links original container hash, exact tar-stream hash and XZ hash.
Authentication is outside these archives and is never touched.
"""
import argparse
from datetime import datetime, timezone
import gzip
import hashlib
import json
import lzma
from pathlib import Path
import time


def recompress(cell):
    original=cell/'snapshot.tar.gz';target=cell/'snapshot.tar.xz'
    receipt=json.loads((cell/'archive.json').read_text())
    if not receipt['verified'] or hashlib.sha256(original.read_bytes()).hexdigest()!=receipt['archive_sha256']:
        raise ValueError('Original verified archive required')
    raw=gzip.decompress(original.read_bytes());start=time.perf_counter()
    encoded=lzma.compress(raw,preset=9)
    with target.open('xb') as stream:stream.write(encoded)
    if lzma.decompress(target.read_bytes())!=raw:
        raise ValueError('Recompression verification failed; original retained')
    result=dict(at=datetime.now(timezone.utc).isoformat(),original_gzip_sha256=receipt['archive_sha256'],
        original_gzip_bytes=original.stat().st_size,raw_tar_sha256=hashlib.sha256(raw).hexdigest(),
        xz_sha256=hashlib.sha256(encoded).hexdigest(),xz_bytes=len(encoded),
        seconds=time.perf_counter()-start,exact_raw_tar_roundtrip=True,authentication_touched=False)
    with (cell/'recompression-001.json').open('x') as stream:json.dump(result,stream,indent=2)
    original.unlink()
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--root',required=True,type=Path);a=p.parse_args()
    if not (a.root/'completion.json').exists():raise ValueError('Finish model generation before recompression')
    for cell in sorted(p.parent for p in a.root.glob('*/archive.json')):
        result=recompress(cell)
        print(json.dumps(dict(cell=cell.name,original=result['original_gzip_bytes'],xz=result['xz_bytes'],verified=True)),flush=True)
