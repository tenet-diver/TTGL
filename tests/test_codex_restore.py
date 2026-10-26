"""Restore integrity and control replay; these are not model-quality tests."""
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tarfile

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('restore_codex_pilot', ROOT / 'scripts/restore_codex_pilot.py')
restore_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(restore_module)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, sort_keys=True) + '\n')


def make_archive(contents):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w:gz') as archive:
        root = tarfile.TarInfo('fixture')
        root.type = tarfile.DIRTYPE
        archive.addfile(root)
        for path, body in contents.items():
            entry = tarfile.TarInfo('fixture/' + path)
            entry.size = len(body)
            archive.addfile(entry, io.BytesIO(body))
    return output.getvalue()


def tree_hash(contents):
    return sha(json.dumps({name: sha(body) for name, body in contents.items()}, sort_keys=True).encode())


@pytest.fixture
def frozen_fixture(tmp_path):
    plan = tmp_path / 'plan'
    plan.mkdir()
    test = b'from pkg import answer\n\ndef test_answer():\n    assert answer() == 1\n'
    base = {'pkg/__init__.py': b'def answer():\n    return 0\n', 'tests/test_behavior.py': test}
    fixed = {'pkg/__init__.py': b'def answer():\n    return 1\n', 'tests/test_behavior.py': test}
    base_revision, fixed_revision = 'a' * 40, 'b' * 40
    base_url = 'https://codeload.github.com/fixture/project/tar.gz/' + base_revision
    fixed_url = 'https://codeload.github.com/fixture/project/tar.gz/' + fixed_revision
    downloads = {base_url: make_archive(base), fixed_url: make_archive(fixed)}
    task = {'task_id': 'fixture-1', 'repo': 'fixture/project', 'base_commit': base_revision,
            'fixed_commit': fixed_revision, 'test_file': 'tests/test_behavior.py', 'source_dir': 'pkg',
            'statement': 'Return the documented value.', 'base_tree_sha256': tree_hash(base),
            'evaluation_test_tree_sha256': tree_hash({'test_behavior.py': test})}
    arms = ['luna', 'sol', 'precall', 'personal']
    registry = {'tasks': [task], 'arms': arms}
    provenance = {'sources': [{'url': url, 'sha256': sha(body)} for url, body in downloads.items()],
                  'feasibility_screen': [{'task_id': 'fixture-1',
                    'buggy': {'returncode': 1, 'counts': {'tests': 1, 'failures': 1, 'errors': 0, 'skipped': 0}},
                    'fixed': {'returncode': 0, 'counts': {'tests': 1, 'failures': 0, 'errors': 0, 'skipped': 0}}}]}
    write_json(plan / 'tasks.json', registry)
    write_json(plan / 'provenance.json', provenance)
    grader_spec = importlib.util.spec_from_file_location('frozen_fixture_grader', restore_module.GRADER)
    grader = importlib.util.module_from_spec(grader_spec)
    grader_spec.loader.exec_module(grader)
    protocol = {'task_ids': ['fixture-1'], 'arms': arms,
                'tasks_sha256': sha((plan / 'tasks.json').read_bytes()),
                'provenance_sha256': sha((plan / 'provenance.json').read_bytes()),
                'grader_sha256': sha(restore_module.GRADER.read_bytes()),
                'memory_sha256': sha(grader.MEMORY.encode())}
    write_json(plan / 'protocol.json', protocol)
    return {'plan': plan, 'work': tmp_path / 'workers', 'evaluator': tmp_path / 'evaluator',
            'downloads': downloads, 'protocol': protocol, 'provenance': provenance,
            'base_url': base_url, 'base': base}


def run_restore(fixture):
    return restore_module.restore(plan=fixture['plan'], work=fixture['work'],
                                  evaluator=fixture['evaluator'], python=Path(sys.executable),
                                  download=fixture['downloads'].__getitem__)


def test_restore_replays_real_tests_and_preserves_protocol(frozen_fixture):
    fixture = frozen_fixture
    protocol_bytes = (fixture['plan'] / 'protocol.json').read_bytes()
    report = run_restore(fixture)
    assert report['status'] == 'restored_and_controls_verified'
    assert report['worker_count'] == 4
    assert report['checks'][0]['controls']['buggy']['counts']['failures'] == 1
    assert report['checks'][0]['controls']['fixed']['returncode'] == 0
    for arm in fixture['protocol']['arms']:
        worker = fixture['work'] / arm / 'fixture-1'
        assert (worker / 'TASK.md').is_file()
        assert (worker / 'USER_MEMORY.md').is_file()
        assert (worker / 'pkg/__init__.py').read_bytes() == fixture['base']['pkg/__init__.py']
        assert not (worker / '.git').exists()
    assert (fixture['plan'] / 'protocol.json').read_bytes() == protocol_bytes
    assert restore_module.verify_integrity(fixture['plan'], fixture['evaluator'])['status'] == 'verified'


def test_existing_destination_is_not_overwritten(frozen_fixture):
    fixture = frozen_fixture
    fixture['work'].mkdir()
    marker = fixture['work'] / 'existing-user-file'
    marker.write_text('preserve me')
    with pytest.raises(FileExistsError, match='Refusing to overwrite'):
        run_restore(fixture)
    assert marker.read_text() == 'preserve me'
    assert not fixture['evaluator'].exists()


def test_download_tampering_is_rejected(frozen_fixture):
    fixture = frozen_fixture
    fixture['downloads'][fixture['base_url']] += b'tampering'
    with pytest.raises(ValueError, match='Download hash mismatch'):
        run_restore(fixture)
    report = json.loads((fixture['evaluator'] / 'restore-report.json').read_text())
    assert report['status'] == 'failed'
    assert not (fixture['work'] / 'luna').exists()


@pytest.mark.parametrize('relative', ['base/pkg/__init__.py', 'fixed/tests/test_behavior.py'])
def test_changed_evaluator_tree_is_rejected(frozen_fixture, relative):
    fixture = frozen_fixture
    run_restore(fixture)
    path = fixture['evaluator'] / 'fixture-1' / relative
    path.write_text(path.read_text() + '\n# altered after restoration\n')
    with pytest.raises(ValueError, match='Evaluator tree hash mismatch'):
        restore_module.verify_integrity(fixture['plan'], fixture['evaluator'])


def test_untrusted_tar_paths_are_rejected_even_with_matching_download_hash(frozen_fixture):
    fixture = frozen_fixture
    malicious = make_archive({'../escape': b'do not write outside the archive root'})
    fixture['downloads'][fixture['base_url']] = malicious
    for source in fixture['provenance']['sources']:
        if source['url'] == fixture['base_url']:
            source['sha256'] = sha(malicious)
    write_json(fixture['plan'] / 'provenance.json', fixture['provenance'])
    fixture['protocol']['provenance_sha256'] = sha((fixture['plan'] / 'provenance.json').read_bytes())
    write_json(fixture['plan'] / 'protocol.json', fixture['protocol'])
    with pytest.raises(ValueError, match='unsafe member'):
        run_restore(fixture)
    assert not (fixture['evaluator'] / 'fixture-1' / 'escape').exists()


def test_frozen_task_metadata_cannot_be_changed(frozen_fixture):
    fixture = frozen_fixture
    path = fixture['plan'] / 'tasks.json'
    path.write_text(path.read_text() + ' ')
    with pytest.raises(ValueError, match='Frozen input hash mismatch'):
        run_restore(fixture)
    assert not fixture['work'].exists()
    assert not fixture['evaluator'].exists()
