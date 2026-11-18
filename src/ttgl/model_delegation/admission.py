"""Exact finite native registration and process-shared, non-resettable claims."""
from __future__ import annotations
import fcntl
import json
import os
from pathlib import Path
from ..experience_routing.io import file_digest, read, canonical, digest


def admit(root, output, model, task_id, binding, image_id, timeout, registration):
    if registration is None:
        raise ValueError('An explicit enabled finite native registration is required')
    path = Path(registration).resolve(strict=True)
    frozen = read(path)
    if frozen.get('allow_model_execution') is not True or frozen.get('automatic_retries') != 0:
        raise ValueError('Native registration is disabled or permits retries')
    if (frozen.get('native_source_account_hash') != binding['account_hash'] or model not in frozen.get('models', [])
            or task_id not in frozen.get('task_ids', []) or frozen.get('image_id') != image_id):
        raise ValueError('Registered native source/model/task/actor differs')
    for pin in frozen['source_pins']:
        if file_digest(Path(root)/pin['path']) != pin['sha256']:
            raise ValueError('Frozen native source drift')
    for key in ('maximum_invocations', 'maximum_elapsed_seconds', 'maximum_observed_total_tokens'):
        value = frozen.get(key)
        if type(value) is not int or value <= 0:
            raise ValueError('Positive finite registered native cap required: '+key)
    if not 0 < timeout <= frozen['maximum_elapsed_seconds']:
        raise ValueError('Episode time exceeds the registered shared cap')
    spool = Path(frozen['private_output_root']).resolve(strict=True)
    if not Path(output).resolve().is_relative_to(spool) or not spool.is_relative_to(Path(root).resolve()/'work/security'):
        raise ValueError('Registered private native spool required')
    return frozen, spool, file_digest(path)


def claim(spool, registration_hash, identity, maximum_invocations):
    """A failed or uncertain started call still consumes its registered slot."""
    spool = Path(spool)
    lock = spool/'native-claims.lock'
    lock.touch(mode=0o600, exist_ok=True)
    with lock.open('r+') as stream:
        fcntl.flock(stream, fcntl.LOCK_EX)
        path = spool/'native-claims.jsonl'
        rows = [json.loads(l) for l in path.read_text().splitlines()] if path.exists() else []
        if any(r['registration_hash'] != registration_hash for r in rows):
            raise ValueError('Different native registration cannot reset a spent campaign')
        if any(r['identity'] == identity for r in rows) or len(rows) >= maximum_invocations:
            raise ValueError('Started/uncertain native identity or exhausted shared invocation cap')
        with path.open('a') as out:
            os.chmod(path, 0o600)
            out.write(canonical({'registration_hash': registration_hash, 'identity': identity})+'\n')
            out.flush()
            os.fsync(out.fileno())
