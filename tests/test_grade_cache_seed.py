import json
from pathlib import Path
import subprocess
import sys

from ttgl.benchmark import digest

ROOT = Path(__file__).resolve().parents[1]


def fixture(tmp_path, different_timeout=False, corrupt_report=False):
    source, target = tmp_path/'source', tmp_path/'target'
    for p in (source,target):
        p.mkdir()
        environment = {'evaluator_image_id':'fixture-image',
                       'private_grading_dataset_sha256':'fixture-dataset',
                       'grading_timeout_seconds':600 if different_timeout and p==target else 1200}
        (p/'environment.json').write_text(json.dumps(environment))
        (p/'environment.sha256').write_text(digest(p/'environment.json'))
    report = source/'report.json';report.write_text('{}')
    (source/'grade-cache.json').write_text(json.dumps({'fixture-cache-key':{
        'report':str(report),'report_sha256':digest(report)}}))
    if corrupt_report:
        report.write_text('{"changed":true}')
    command = [sys.executable,str(ROOT/'scripts/seed_grade_cache.py'),
               '--source-study',str(source),'--target-study',str(target)]
    return command,target


def test_different_evaluation_timeout_prevents_grade_reuse(tmp_path):
    command,target = fixture(tmp_path,different_timeout=True)
    result = subprocess.run(command,capture_output=True,text=True)
    assert result.returncode != 0
    assert 'timeout differs' in result.stderr
    assert not (target/'grade-cache.json').exists()


def test_changed_original_report_prevents_grade_reuse(tmp_path):
    command,target = fixture(tmp_path,corrupt_report=True)
    result = subprocess.run(command,capture_output=True,text=True)
    assert result.returncode != 0
    assert 'report changed' in result.stderr
    assert not (target/'grade-cache.json').exists()
