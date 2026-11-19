"""Bound temporary replay exports using verified retained artifacts.

Only plain owned /tmp exports may be released. Git checkouts, raw logs, receipts
and persistent service/history volumes are never candidates for this function.
"""
from pathlib import Path
import shutil
import tempfile
import time
from .artifacts import restore_delta
from ..experience_routing.checkpoints import manifest
from ..experience_routing.io import file_digest,write_new,digest


def relocate_closed_native(source,destination,*,receipt_root):
    """Move a finished private client spool, keeping its original path valid."""
    source,destination=Path(source),Path(destination)
    if source.is_symlink():return {'already_relocated':True}
    if source.name!='native' or list(source.rglob('auth.json')):
        raise ValueError('Finished credential-free native spool required')
    before=manifest(source)
    destination.parent.mkdir(parents=True,exist_ok=True,mode=0o700)
    shutil.copytree(source,destination,symlinks=True)
    if manifest(destination)['state_hash']!=before['state_hash'] or manifest(source)['state_hash']!=before['state_hash']:
        raise ValueError('Native spool changed; preserve original and copied evidence')
    receipt=write_new(Path(receipt_root)/(digest(str(source))+'.json'),{
        'source':str(source),'destination':str(destination),'state_hash':before['state_hash'],
        'files':len(before['files']),'native_calls':0,'operation':'Lossless relocation of finished private spool'})
    backup=source.with_name('native.verified-move-backup');source.rename(backup)
    source.symlink_to(destination,target_is_directory=True)
    if manifest(source)['state_hash']!=before['state_hash']:
        raise ValueError('Relocated native spool differs; original backup preserved')
    shutil.rmtree(backup)
    return {'receipt':str(receipt),'files':len(before['files']),'state_hash':before['state_hash']}


def release_candidate(source,artifact,*,owned_root,cache,receipts,client):
    source=Path(source)
    boundary=Path(owned_root).resolve()
    if (source.is_symlink() or not boundary.is_relative_to(Path('/tmp')) or
        not source.resolve().is_relative_to(boundary) or source.name!='source' or (source/'.git').exists()):
        raise ValueError('Only registered owned temporary exports may be released')
    expected=artifact['candidate_state_hash']
    if manifest(source)['state_hash']!=expected:raise ValueError('Export differs from retained candidate; preserve it')
    cache=Path(cache);cache.mkdir(parents=True,exist_ok=True)
    def restored_file(receipt):
        path=cache/(receipt['sha256']+'.gz')
        if not path.exists():client.restore_file(receipt,path)
        if file_digest(path)!=receipt['sha256']:raise ValueError('Retained compressed artifact differs')
        return path
    started=time.monotonic()
    base=restored_file(artifact['base']['archive']);delta=restored_file(artifact)
    # Existing exact replay handles modes, links and deletion/addition semantics.
    with tempfile.TemporaryDirectory(prefix='observatory-retirement-',dir=boundary) as temporary:
        state=restore_delta(base.read_bytes(),delta.read_bytes(),Path(temporary)/'source',artifact=artifact)
        if state['state_hash']!=expected or manifest(source)['state_hash']!=expected:
            raise ValueError('Independent retained-artifact replay differs; original export preserved')
        receipt=write_new(Path(receipts)/(digest(str(source))+'.json'),{
            'source':str(source),'candidate_state_hash':expected,'artifact':artifact,
            'independent_s3_readback_replay_verified':True,'native_calls':0,
            'scope':'Redundant owned temporary export; retained exact bytes and receipts remain authoritative',
            'validation_seconds':time.monotonic()-started})
        client.retain_file(receipt,kind='verified-scratch-release',identity=str(source))
        shutil.rmtree(source)
    return {'released':True,'receipt':str(receipt),'validation_seconds':time.monotonic()-started}
