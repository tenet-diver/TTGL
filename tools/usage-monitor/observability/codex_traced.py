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
config = Path(__file__).resolve().parents[1] / 'config/codex-provider.toml'
settings = tomllib.loads(config.read_text())
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
