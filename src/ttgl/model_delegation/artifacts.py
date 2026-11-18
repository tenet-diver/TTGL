"""Content-addressed base plus file deltas, using existing checkpoint manifests.

Tar/gzip preserve exact file bytes, modes and links. Shared bases avoid retaining
hundreds of almost-identical full repository archives in the local S3 volume.
"""
from __future__ import annotations
import gzip
import io
import json
import shutil
import tarfile
from pathlib import Path
from ..experience_routing.checkpoints import manifest
from ..experience_routing.execution import source_tar, unpack_public_source
from ..experience_routing.io import canonical, digest, inside

MAX_BYTES = 270*1024*1024


def _store(raw, path, client, kind, identity):
    path = Path(path)
    with path.open('xb') as stream:
        path.chmod(0o600)
        stream.write(gzip.compress(raw, mtime=0))
    receipt = client.retain_file(path, kind=kind, identity=identity)
    # This newly created duplicate is removed only after exact S3 read-back;
    # the immutable delivery receipt and source manifest stay on disk.
    path.unlink()
    return receipt


def retain_base(source, output, client):
    before = manifest(source)
    receipt = _store(source_tar(source), Path(output)/'base-source.tar.gz', client,
                     'base-source', before['state_hash'])
    return {'format': 'base-tar-gzip-v1', 'state_hash': before['state_hash'], 'archive': receipt}


def retain_delta(source, before, base, output, client, *, name='candidate'):
    if base['state_hash'] != before['state_hash']:
        raise ValueError('Delta base differs from frozen checkpoint')
    source = Path(source)
    after = manifest(source)
    updated = {k: v for k, v in after['files'].items() if before['files'].get(k) != v}
    removed = sorted(set(before['files'])-set(after['files']))
    header = {'format': 'source-file-delta-v1', 'base': base,
              'candidate_state_hash': after['state_hash'], 'updated': updated, 'removed': removed}
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode='w') as tar:
        raw = canonical(header).encode()
        info = tarfile.TarInfo('checkpoint.json'); info.size = len(raw); info.mode = 0o600
        tar.addfile(info, io.BytesIO(raw))
        for key, row in sorted(updated.items()):
            info = tarfile.TarInfo('files/'+key); info.mode = row['mode']
            if row['type'] == 'symlink':
                info.type = tarfile.SYMTYPE; info.linkname = row['target']; tar.addfile(info)
            else:
                raw = (source/key).read_bytes(); info.size = len(raw); tar.addfile(info, io.BytesIO(raw))
    archive = _store(buffer.getvalue(), Path(output)/(name+'.delta.tar.gz'), client,
                     'quarantined-source-delta' if name == 'quarantine' else 'candidate-source-delta', after['state_hash'])
    return {**archive, 'format': 'source-file-delta-v1', 'base': base,
            'candidate_state_hash': after['state_hash'], 'updated_files': len(updated), 'removed_files': len(removed)}


def _decompress(raw):
    with gzip.GzipFile(fileobj=io.BytesIO(raw)) as stream:
        value = stream.read(MAX_BYTES+1)
    if len(value) > MAX_BYTES:
        raise ValueError('Checkpoint exceeds the replay byte cap')
    return value


def restore_delta(base_gzip, delta_gzip, destination, *, artifact):
    """Restore into a fresh owned directory and verify the complete state hash."""
    destination = Path(destination)
    if digest(delta_gzip) != artifact['sha256']:
        raise ValueError('Delta archive differs from its immutable receipt')
    if destination.exists() and list(destination.iterdir()):
        raise ValueError('Replay destination must be fresh and empty')
    destination.mkdir(parents=True, exist_ok=True)
    unpack_public_source(_decompress(base_gzip), destination)
    with tarfile.open(fileobj=io.BytesIO(_decompress(delta_gzip))) as tar:
        members = tar.getmembers()
        if len({m.name for m in members}) != len(members):
            raise ValueError('Duplicate delta member')
        header = json.load(tar.extractfile('checkpoint.json'))
        if header['format'] != 'source-file-delta-v1':
            raise ValueError('Unknown delta format')
        if header['candidate_state_hash'] != artifact['candidate_state_hash'] or header['base'] != artifact['base']:
            raise ValueError('Delta manifest differs from its immutable receipt')
        if digest(base_gzip) != header['base']['archive']['sha256']:
            raise ValueError('Base artifact hash differs')
        if manifest(destination)['state_hash'] != header['base']['state_hash']:
            raise ValueError('Base source state differs')
        expected = {'checkpoint.json', *('files/'+k for k in header['updated'])}
        if {m.name for m in members} != expected:
            raise ValueError('Delta members differ from the sealed manifest')
        keys = set(header['removed']) | set(header['updated'])
        for key in keys:
            inside(destination, key)
        for key in sorted(keys, key=lambda k: (-len(Path(k).parts), k)):
            path = inside(destination, key)
            if path.is_symlink() or path.is_file(): path.unlink()
            elif path.is_dir(): shutil.rmtree(path)
        for key, row in sorted(header['updated'].items(), key=lambda kv: (kv[1]['type'] == 'symlink', kv[0])):
            path = inside(destination, key); path.parent.mkdir(parents=True, exist_ok=True)
            member = tar.getmember('files/'+key)
            if row['type'] == 'symlink':
                target = (path.parent/row['target']).resolve()
                if not target.is_relative_to(destination.resolve()) or not member.issym() or member.linkname != row['target']:
                    raise ValueError('Invalid delta link')
                path.symlink_to(row['target'])
            elif row['type'] == 'file' and member.isfile():
                raw = tar.extractfile(member).read()
                if len(raw) != row['bytes'] or digest(raw) != row['sha256']:
                    raise ValueError('Changed file differs from sealed bytes')
                path.write_bytes(raw); path.chmod(row['mode'])
            else:
                raise ValueError('Invalid delta file type')
    state = manifest(destination)
    if state['state_hash'] != header['candidate_state_hash']:
        raise ValueError('Replayed candidate differs from sealed source')
    return state
