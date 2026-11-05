#!/usr/bin/env python3
"""Launch Codex through the local HTTP/SSE capture adapter; global config unchanged."""
import os
import sys
import json
from pathlib import Path
import tomllib

arguments = sys.argv[1:]
if arguments[:1] == ['--']:
    arguments = arguments[1:]
policy = None
if '--ttgl-compression' in arguments:
    index = arguments.index('--ttgl-compression')
    if index + 1 >= len(arguments) or arguments[index + 1] not in ('off', 'progress', 'headroom-lossless'):
        raise SystemExit('--ttgl-compression requires off, progress or headroom-lossless')
    policy = arguments[index + 1]
    del arguments[index:index + 2]
config = Path(__file__).resolve().parents[1] / 'config/codex-provider.toml'
settings = tomllib.loads(config.read_text())
if policy is not None:
    base = settings['model_providers']['ttgl_capture']['base_url'].split('/compress/')[0].rstrip('/')
    settings['model_providers']['ttgl_capture']['base_url'] = base if policy == 'off' else base + '/compress/' + policy
def flatten(values, prefix=''):
    for key, value in values.items():
        key = prefix + key
        if isinstance(value, dict):
            yield from flatten(value, key + '.')
        else:
            yield key, value
command = ['codex']
for key, value in flatten(settings):
    command += ['-c', key + '=' + json.dumps(value)]
command += arguments
os.execvp(command[0], command)
