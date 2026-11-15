"""Remove only an owned dead Unix-socket pathname before fresh preparation."""
import errno
import hashlib
import os
from pathlib import Path
import socket
import stat


def expected_socket(cell):
    return Path('/tmp')/('ttgl-team-memory-'+hashlib.sha256(str(cell.resolve()).encode()).hexdigest()[:24]+'.sock')


def clear_dead_socket(cell,spec):
    path=Path(spec['socket']);expected=expected_socket(cell)
    if path!=expected:raise ValueError('Socket does not belong to this assignment')
    if not path.exists():return dict(removed=False,reason='no prior socket',model_calls=0)
    before=path.lstat()
    if not stat.S_ISSOCK(before.st_mode) or before.st_uid!=os.getuid():
        raise ValueError('Refuse non-socket or differently owned path')
    # A bound endpoint is live even in the interval before listen().
    if any(line.split() and line.split()[-1]==str(path) for line in Path('/proc/net/unix').read_text().splitlines()):
        raise RuntimeError('An active kernel socket exists; audit, do not unlink')
    with socket.socket(socket.AF_UNIX) as client:code=client.connect_ex(str(path))
    if code!=errno.ECONNREFUSED:raise RuntimeError('Socket death not established')
    now=path.lstat()
    if (now.st_dev,now.st_ino,now.st_uid)!=(before.st_dev,before.st_ino,before.st_uid):
        raise RuntimeError('Socket pathname changed during check')
    path.unlink()
    return dict(removed=True,reason='owned pathname, no kernel endpoint, connection refused, inode unchanged',
                prior_inode=before.st_ino,model_calls=0,unique_record_data_deleted=False)
