"""Selection must prioritize quality and reject a different task population."""
import json
from pathlib import Path
import subprocess
import sys

from ttgl.benchmark import digest

ROOT = Path(__file__).resolve().parents[1]


def fixture(tmp_path, wrong_tasks=False):
    panel = json.loads((ROOT/'experiments/delegation-development-001/tasks.json').read_text())
    panel['tasks'] = panel['tasks'][:2]
    task_path = tmp_path/'tasks.json'
    task_path.write_text(json.dumps(panel))
    protocol = tmp_path/'protocol.json'
    protocol.write_text(json.dumps({'shared_tasks_sha256':digest(task_path)}))
    candidates = []
    for mode, outcomes, cost in [('adaptive',[True,False],.01),('fallback',[True,True],.2)]:
        directory = tmp_path/mode;directory.mkdir()
        rows = []
        for i, task in enumerate(panel['tasks']):
            key = 'unregistered-'+str(i) if wrong_tasks else task['instance_id']
            rows.extend([{'arm':'personal','task_id':key,'resolved':outcomes[i],'cost_usd':cost},
                         {'arm':'large','task_id':key,'resolved':True,'cost_usd':1.}])
        records = directory/'published-rate-records.json';records.write_text(json.dumps(rows))
        (directory/'validation.json').write_text(json.dumps({
            'status':'completed_officially_graded_engineering_panel',
            'published_rate_records_sha256':digest(records),
            'published_rate_scenario_sha256':'synthetic-test-scenario'}))
        candidates.extend(['--candidate',mode+'='+str(directory)])
    output = tmp_path/'selected.json'
    command = [sys.executable,str(ROOT/'scripts/select_delegation_policy.py'),*candidates,
               '--protocol',str(protocol),'--output',str(output)]
    return command, output


def test_highest_quality_wins_over_cheaper_inaccurate_candidate(tmp_path):
    command, output = fixture(tmp_path)
    result = subprocess.run(command,capture_output=True,text=True)
    assert result.returncode == 0, result.stderr
    selection = json.loads(output.read_text())
    assert selection['selected_mode'] == 'fallback'
    assert selection['held_out_outcomes_used'] is False


def test_unregistered_task_outcomes_cannot_select_policy(tmp_path):
    command, output = fixture(tmp_path,wrong_tasks=True)
    result = subprocess.run(command,capture_output=True,text=True)
    assert result.returncode != 0
    assert 'registered development task set' in result.stderr
    assert not output.exists()
