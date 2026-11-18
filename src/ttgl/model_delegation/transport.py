"""Current CLI provider configuration, without changing frozen legacy adapters."""
import json
import sys
from pathlib import Path
from ..experience_routing.backend import RecordedCodexBackend
from ..experience_routing.io import file_digest


class SubscriptionBackend(RecordedCodexBackend):
    def command(self, request, schema):
        old = super().command(request, schema)
        command, i = [], 0
        while i < len(old):
            if old[i] == '--config' and (old[i+1].startswith('model_providers.openai.')
                                         or old[i+1].startswith('model_provider=')):
                i += 2
                continue
            command.append(old[i])
            i += 1
        assert command.pop() == '-'
        provider = 'observatory_subscription'
        settings = {
            'model_provider': provider,
            'model_providers.'+provider+'.name': 'Observatory source subscription',
            'model_providers.'+provider+'.base_url': 'https://chatgpt.com/backend-api/codex',
            'model_providers.'+provider+'.wire_api': 'responses',
            'model_providers.'+provider+'.requires_openai_auth': True,
            'model_providers.'+provider+'.request_max_retries': 0,
            'model_providers.'+provider+'.stream_max_retries': 0,
        }
        for key, value in settings.items():
            command += ['--config', key+'='+json.dumps(value)]
        return command+['-']


class ActorSubscriptionBackend(SubscriptionBackend):
    """Qualifies the stdlib MCP bridge instead of the absent legacy Node SDK."""
    def __init__(self, *, bridge_config, **kwargs):
        super().__init__(node_executable=sys.executable, **kwargs)
        self.bridge_config = str(Path(bridge_config).resolve(strict=True))

    def preflight(self, request):
        from ..experience_routing.backend import source_binding
        if request.thread_id is not None:
            raise ValueError('Fresh source-bound attempt required')
        if file_digest(self.executable) != self.executable_sha256 or source_binding(self.binding['codex_home']) != self.binding:
            raise ValueError('Native executable/source identity drift')
        if request.read_only or not self.container:
            raise ValueError('Actor adapter requires its registered coding container')

    def command(self, request, schema):
        old = super().command(request, schema)
        command, i = [], 0
        while i < len(old):
            if old[i] == '--config' and any(old[i+1].startswith(k+'=') for k in
                ('mcp_servers.worker.command', 'mcp_servers.worker.args')):
                i += 2
                continue
            command.append(old[i])
            i += 1
        assert command.pop() == '-'
        settings = {'mcp_servers.worker.command': sys.executable,
                    'mcp_servers.worker.args': ['-m', 'ttgl.model_delegation.worker_bridge', '--config', self.bridge_config],
                    'mcp_servers.worker.env': {'PYTHONPATH': str(Path(__file__).resolve().parents[2])},
                    'mcp_servers.worker.required': True}
        from ..experience_routing.io import read
        if read(self.bridge_config).get('delegation'):
            settings['mcp_servers.worker.enabled_tools'] = ['shell', 'route_subtask', 'delegate_subtask']
            settings['mcp_servers.worker.tool_timeout_sec'] = 250
            for tool in ('route_subtask', 'delegate_subtask'):
                settings['mcp_servers.worker.tools.'+tool+'.approval_mode'] = 'approve'
        for feature in ('apply_patch_freeform', 'goals'):
            command += ['--disable', feature]
        for key, value in settings.items():
            encoded = '{'+','.join(json.dumps(k)+'='+json.dumps(v) for k, v in value.items())+'}' if isinstance(value, dict) else json.dumps(value)
            command += ['--config', key+'='+encoded]
        return command+['-']
