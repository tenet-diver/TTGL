import asyncio
import contextvars
from dataclasses import replace
import json
from pathlib import Path
import shutil
import subprocess
from types import SimpleNamespace

import pytest

pytest.importorskip('harbor', reason='Separate Harbor runtime required')
from ttgl import personal
from ttgl.harbor_bridge import EnvironmentBridge, HarborBackend
from ttgl.harbor_routing_agent import DiagnosticBackend
from ttgl import harbor_routing_agent
from harbor.models.agent.context import AgentContext


def request(cooperative=True, kind='controller'):
    task = {'prompt': 'Repair the provided artifact.', 'allowed_paths': ['.'], 'memory': []}
    return personal.Request('handoff-test', 'fixture-model', kind,
                            personal._task_prompt(task, cooperative=cooperative, expert_limit=2),
                            Path('/tmp/empty-fixture-context'), {}, 30,
                            read_only=kind == 'expert')


def test_required_review_does_not_grant_expert_actions_to_standalone(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(HarborBackend, 'complete', lambda self, r: calls.append(r) or 'fixture-result')
    backend = DiagnosticBackend(SimpleNamespace(), diagnostic='required_review', records=tmp_path)
    assert backend.complete(request(False)) == 'fixture-result'
    assert 'must make at least one consultation' not in calls[-1].prompt
    assert backend.complete(request()) == 'fixture-result'
    assert 'must make at least one consultation' in calls[-1].prompt
    assert 'Verification treatment v3' in calls[-1].prompt
    followup = replace(request(), thread_id='existing', prompt='Expert reply: check the candidate.')
    backend.complete(followup)
    assert calls[-1].prompt == followup.prompt


def test_handoff_snapshots_new_and_staged_files_before_expert_without_changing_index(tmp_path, monkeypatch):
    repo = tmp_path/'repo with spaces'
    repo.mkdir()
    def git(*args):
        return subprocess.check_output(['git', '-C', str(repo), *args], text=True)
    git('init', '-q')
    (repo/'tracked.txt').write_text('base\n')
    git('add', '.')
    git('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid', 'commit', '-qm', 'fixture')
    (repo/'tracked.txt').write_text('staged candidate\n')
    git('add', 'tracked.txt')
    (repo/'new.txt').write_text('new candidate\n')
    before = git('diff', '--cached', '--binary')
    phase = contextvars.ContextVar('fixture-phase', default='setup')
    records = tmp_path/'unmounted-records'
    records.mkdir()

    class Environment:
        async def exec(self, command, **kwargs):
            assert phase.get() == 'agent'
            proc = await asyncio.create_subprocess_shell(command, stdout=asyncio.subprocess.PIPE,
                                                         stderr=asyncio.subprocess.PIPE)
            stdout, stderr = await proc.communicate()
            return SimpleNamespace(return_code=proc.returncode, stdout=stdout.decode(), stderr=stderr.decode())

        async def download_file(self, source_path, target_path):
            shutil.copyfile(source_path, target_path)

    def native_fixture(self, r):
        assert (records/'pre-handoff.json').is_file()  # must precede expert invocation
        if r.request_id == 'handoff-test':
            assert 0 < r.timeout_seconds < 30  # capture consumes the same task budget
        return personal.Response(text='fixture', thread_id='expert-fixture')
    monkeypatch.setattr(HarborBackend, 'complete', native_fixture)

    async def scenario():
        phase.set('agent')
        bridge = EnvironmentBridge(Environment(), str(repo), records/'trace.jsonl').start()
        try:
            backend = DiagnosticBackend(bridge, diagnostic='verification', records=records)
            await asyncio.to_thread(backend.complete, request(kind='expert'))
            initial = (records/'pre-handoff.json').read_bytes()
            await asyncio.to_thread(backend.complete, replace(request(kind='expert'), request_id='second'))
            assert (records/'pre-handoff.json').read_bytes() == initial
        finally:
            await bridge.close()
    asyncio.run(scenario())
    patch = (records/'pre-handoff.patch').read_text()
    assert 'new candidate' in patch and 'staged candidate' in patch
    assert git('diff', '--cached', '--binary') == before
    assert json.loads((records/'pre-handoff.json').read_text())['independent_regrade_required']


@pytest.mark.parametrize('condition,mode', [('small','verification'), ('large','verification'),
                                         ('personal','verification'), ('personal','required_review')])
def test_actual_callbacks_export_snapshot_only_after_generation(tmp_path, monkeypatch, condition, mode):
    logs = tmp_path/'trial/agent'
    logs.mkdir(parents=True)
    (logs.parent/'config.json').write_text(json.dumps({'task': {'path': '/private/instance_fixture'}}))

    class Environment:
        async def exec(self, command, **kwargs):
            return SimpleNamespace(return_code=0, stdout='/app\n' if '--show-toplevel' in command else 'f'*40+'\n', stderr='')

        async def download_file(self, source_path, target_path):
            Path(target_path).write_text('final fixture patch\n')

    class Backend:
        def __init__(self, bridge, diagnostic, records):
            self.records, self.asked = records, False

        def complete(self, r):
            if r.kind == 'expert':
                assert not (logs/'pre-handoff.patch').exists()
                (self.records/'pre-handoff.patch').write_text('candidate fixture patch\n')
                (self.records/'pre-handoff.json').write_text('{}')
                value = {'action':'answer', 'message':'fixture diagnosis'}
            elif condition == 'personal' and not self.asked:
                self.asked = True
                value = {'action':'ask_expert','question':'Review this candidate','context':'fixture evidence','summary':''}
            else:
                value = {'action':'complete','question':'','context':'','summary':'fixture completion'}
            return personal.Response(text=json.dumps(value), thread_id='fixture-'+r.kind,
                usage={k:100 if k=='input_tokens' else 0 for k in personal.USAGE_FIELDS}, usage_scope='turn')

    monkeypatch.setattr(harbor_routing_agent, 'DiagnosticBackend', Backend)
    agent = harbor_routing_agent.RoutingDiagnosticCodex(logs_dir=logs, model_name='native-alias',
        private_records_root=str(tmp_path/'unmounted'), condition=condition, policy=mode)
    context = AgentContext()
    async def scenario():
        env = Environment()
        await agent.setup(env)
        await agent.run('Model-free callback fixture.', env, context)
    asyncio.run(scenario())
    assert context.n_input_tokens == (300 if condition == 'personal' else 100)
    assert context.metadata['policy'] == mode
    assert (logs/'pre-handoff.patch').exists() == (condition == 'personal')
    if condition == 'personal':
        assert (logs/'pre-handoff.patch').read_text() == 'candidate fixture patch\n'
    assert context.metadata['required_review_observed'] == (True if mode == 'required_review' else None)
