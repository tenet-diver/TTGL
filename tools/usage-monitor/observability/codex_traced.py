#!/usr/bin/env python3
"""Launch Codex through the local HTTP/SSE capture adapter; global config unchanged."""
import os
import sys

arguments = sys.argv[1:]
if arguments[:1] == ['--']:
    arguments = arguments[1:]
settings = {
    'model_provider': 'ttgl_capture',
    'model_providers.ttgl_capture.name': 'TTGL Capture',
    'model_providers.ttgl_capture.base_url': 'http://127.0.0.1:8317',
    'model_providers.ttgl_capture.wire_api': 'responses',
    'model_providers.ttgl_capture.requires_openai_auth': True,
    'model_providers.ttgl_capture.supports_websockets': False,
}
command = ['codex']
for key, value in settings.items():
    import json
    command += ['-c', key + '=' + json.dumps(value)]
command += ['--disable', 'enable_request_compression'] + arguments
os.execvp(command[0], command)
