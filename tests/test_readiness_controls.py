"""Public probes follow completed native control pairs, including safe resume."""
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest

ROOT=Path(__file__).resolve().parents[1]


def setup(tmp_path,monkeypatch,timeout=None):
    spec=importlib.util.spec_from_file_location('control_test_driver',ROOT/'scripts/run_swe_controls.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    private=tmp_path/'private';private.mkdir()
    (private/'selected.dataset.json').write_text(json.dumps([{'instance_id':'fixture-1','image':'fixture:task'}]))
    public=tmp_path/'tasks.json'
    public.write_text(json.dumps({'schema_version':1,'dataset_id':'fixture','dataset_revision':'fixture',
        'harness_commit':'f'*40,'tasks':[{'instance_id':'fixture-1','repo':'fixture/repo',
        'base_commit':'a'*40,'problem_statement':'Synthetic software fixture.'}]}))
    output=tmp_path/'controls'
    argv=['controls','--private-root',str(private),'--output',str(output),'--tasks',str(public)]
    if timeout is not None:argv.extend(['--timeout',str(timeout)])
    monkeypatch.setattr(sys,'argv',argv)
    events=[]
    def docker(*args,**kwargs):
        if args[:2]==('image','inspect'):
            return json.dumps([{'Id':'sha256:fixture','RepoDigests':['fixture@sha256:digest'],'Size':1}])
        assert args[:2]==('image','rm')
        events.append('remove-image');return ''
    def run(command,**kwargs):
        kind='gold' if '--gold' in command else 'base'
        native_timeout=command[command.index('--timeout')+1]
        assert kwargs['timeout']==max(1200,2*int(native_timeout))
        events.append('native-'+kind+'-'+native_timeout)
        run_id=command[command.index('--run-id')+1]
        directory=private/'logs/evaluation'/run_id/kind/'fixture-1';directory.mkdir(parents=True)
        (directory/'report.json').write_text(json.dumps({'fixture-1':{
            'resolved':kind=='gold','infra_failure':False}}))
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr(module,'docker',docker)
    monkeypatch.setattr(module.subprocess,'run',run)
    return module,output,events,argv


def test_probe_runs_after_both_native_controls_and_before_image_removal(tmp_path,monkeypatch):
    module,output,events,_=setup(tmp_path,monkeypatch,timeout=1200)
    def probe(task,row):
        assert row['eligible'] is True
        assert (output/'fixture-1.json').exists()
        events.append('probe')
    module.main(after_pair=probe,callback_description={'driver':'synthetic-test'})
    assert events==['native-base-1200','native-gold-1200','probe','remove-image']
    assert json.loads((output/'protocol.json').read_text())['timeout_seconds']==1200


def test_failed_probe_preserves_closed_pair_and_resume_does_not_repeat_grading(tmp_path,monkeypatch):
    module,output,events,argv=setup(tmp_path,monkeypatch)
    def fail_probe(task,row):
        events.append('failed-probe');raise RuntimeError('synthetic public probe failure')
    with pytest.raises(RuntimeError,match='public probe failure'):
        module.main(after_pair=fail_probe,callback_description={'driver':'synthetic-test'})
    assert (output/'fixture-1.json').exists()
    assert 'remove-image' not in events
    monkeypatch.setattr(sys,'argv',[*argv,'--resume'])
    module.main(after_pair=lambda task,row:events.append('repaired-probe'),
                callback_description={'driver':'synthetic-test'})
    assert events==['native-base-600','native-gold-600','failed-probe','repaired-probe']
    assert (output/'summary.json').exists()
