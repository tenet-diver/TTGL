"""Owned zero-inference native-hook observer; invocation-local private journal."""
import json
import os
from pathlib import Path
import sys
import time


if __name__ == '__main__':
    root = Path(os.environ['TTGL_NATIVE_HOOK_OBSERVER'])
    root.mkdir(parents=True, exist_ok=True, mode=0o700)
    payload = json.load(sys.stdin)
    with (root / (str(time.time_ns()) + '-' + str(os.getpid()) + '.json')).open('x') as handle:
        json.dump(payload, handle)
    print('{}')
