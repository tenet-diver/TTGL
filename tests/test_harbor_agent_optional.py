"""Actual Harbor API wiring with scripted responses; never model-quality data."""
import json
from pathlib import Path
from types import SimpleNamespace
import asyncio

import pytest

pytest.importorskip('harbor', reason='Requires the separately pinned Harbor runtime')
from harbor.models.agent.context import AgentContext
from ttgl import harbor_agent, personal


@pytest.mark.parametrize('condition', ['small', 'large', 'personal'])
def test_framework_callbacks_preserve_usage_and_keep_records_outside_worker_logs(tmp_path, monkeypatch, condition):
    logs = tmp_path/'trial'/'agent'
    logs.mkdir(parents=True)
    (logs.parent/'config.json').write_text(json.dumps({'task':{'path':'/private/instance_fixture'}}))

    class Environment:
        async def exec(self, command, **kwargs):
            if '--show-toplevel' in command:
                return SimpleNamespace(return_code=0, stdout='/app\n', stderr='')
            return SimpleNamespace(return_code=0, stdout='f'*40+'\n', stderr='')

        async def download_file(self, source_path, target_path):
            assert source_path == '/logs/agent/model.patch'
            Path(target_path).write_text('synthetic patch fixture; not a benchmark submission\n')

    class Backend:
        def __init__(self, *args, **kwargs):
            self.asked = False

        def complete(self, request):
            if request.kind == 'expert':
                response = {'action':'answer','message':'synthetic expert fixture'}
            elif condition == 'personal' and not self.asked:
                self.asked = True
                response = {'action':'ask_expert','question':'fixture question','context':'fixture observation','summary':''}
            else:
                response = {'action':'complete','question':'','context':'','summary':'synthetic fixture'}
            return personal.Response(text=json.dumps(response),
                thread_id='fixture-'+request.kind, usage={'input_tokens':100,'cached_input_tokens':40,'output_tokens':5,
                    'cache_write_input_tokens':0,'reasoning_output_tokens':0}, usage_scope='turn')

    monkeypatch.setattr(harbor_agent, 'HarborBackend', Backend)
    agent = harbor_agent.ConversationalCodex(logs_dir=logs, model_name='native-alias',
        private_records_root=str(tmp_path/'unmounted-records'), condition=condition)
    context = AgentContext()

    async def scenario():
        environment = Environment()
        await agent.setup(environment)
        await agent.run('Synthetic fixture only.', environment, context)

    asyncio.run(scenario())
    assert agent.skip_model_parsing
    expected = (300,120,15) if condition=='personal' else (100,40,5)
    assert (context.n_input_tokens,context.n_cache_tokens,context.n_output_tokens)==expected
    if condition == 'personal':
        assert context.model_usage['gpt-6-luna'].n_input_tokens == 200
        assert context.model_usage['gpt-6.1-sol'].n_input_tokens == 100
        assert context.metadata['expert_calls'] == 1
    assert context.cost_usd is None
    assert context.metadata['condition']==condition
    records = Path(context.metadata['private_records_path'])
    assert not records.is_relative_to(logs)
    assert (records/'controller/manifest.json').is_file()
    assert not (logs/'controller').exists()
    assert (logs/'model.patch').read_text().startswith('synthetic patch fixture')
