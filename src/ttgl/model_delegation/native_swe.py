"""Private preparation and official-parser replay on the reviewed offline actor.

Original task tests and test-command body are unchanged. Host Git performs the
test reset/patch setup instead of installing Git/Conda in the actor. This patched
runtime adaptation must be labelled; it is not the full upstream image/CLI.
Nothing in this module returns private tests, reference code or test names to a
live controller. Reports stay in the host-owned evaluation directory.
"""
from __future__ import annotations
import json
import os
import shutil
import subprocess
import tarfile
from pathlib import Path
from ..experience_routing.io import read, write_new, file_digest, inside, digest
from ..experience_routing.checkpoints import manifest
from .actor import ExactModeActor
from .retention import LocalS3Retention

TASK_ARCHIVE_SHA256 = 'ff31aa1f8d2bb78f16559524264a99b868b7218ca82b390dc750bbc59538aa20'
START = '>>>>> Start Test Output'
END = '>>>>> End Test Output'


class EvaluationInfrastructureFailure(ValueError):
    """The prescribed check could not finish reliably in the evaluator."""


def git(args, cwd, *, timeout=120):
    env = dict(os.environ, GIT_CONFIG_GLOBAL='/dev/null', GIT_CONFIG_SYSTEM='/dev/null',
               GIT_TERMINAL_PROMPT='0', GIT_LFS_SKIP_SMUDGE='1')
    result = subprocess.run(['git', '-c', 'core.hooksPath=/dev/null', *args], cwd=cwd, env=env,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if result.returncode:
        raise RuntimeError('Private benchmark Git preparation failed; no model retry')
    return result.stdout


def extract_task(archive, task_id, output):
    if file_digest(archive) != TASK_ARCHIVE_SHA256 or '/' in task_id or '..' in task_id:
        raise ValueError('Pinned official task source and exact identity required')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    with tarfile.open(archive) as tar:
        selected = [(m, m.name.split('/tasks/'+task_id+'/', 1)[1]) for m in tar
                    if '/tasks/'+task_id+'/' in m.name and m.isfile()]
        if not selected:
            raise ValueError('Unknown official task')
        for member, key in selected:
            path = inside(output, key)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(tar.extractfile(member).read()); path.chmod(0o600)
    if (output/'test_assets').exists():
        raise ValueError('Binary test assets require separate actor qualification')
    return output


def checkout_source(repo, base_commit, output):
    if repo != 'sympy/sympy' or len(base_commit) != 40:
        raise ValueError('This prepared actor profile is restricted to the registered SymPy subset')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    git(['init', '--quiet'], output)
    git(['remote', 'add', 'origin', 'https://github.com/'+repo+'.git'], output)
    git(['fetch', '--quiet', '--depth=1', 'origin', base_commit], output)
    git(['checkout', '--quiet', '--detach', 'FETCH_HEAD'], output)
    if git(['rev-parse', 'HEAD'], output).decode().strip() != base_commit:
        raise ValueError('Benchmark base differs')
    normalize_git_modes(output)
    return manifest(output)


def normalize_git_modes(source):
    """Use Git's canonical executable bit, independent of host umask/ACLs."""
    source = Path(source)
    for row in git(['ls-files', '--stage', '-z'], source).split(b'\0'):
        if not row:
            continue
        metadata, key = row.split(b'\t', 1)
        mode = metadata.split()[0]
        path = inside(source, os.fsdecode(key))
        if mode in (b'100644', b'100755'):
            path.chmod(0o755 if mode == b'100755' else 0o644)
    for directory in source.rglob('*'):
        if directory.is_dir() and '.git' not in directory.relative_to(source).parts:
            directory.chmod(0o755)


def public_contract(task_directory, source):
    import yaml
    directory, source = Path(task_directory), Path(source)
    meta = yaml.safe_load((directory/'task.yaml').read_text())
    return {'task_id': meta['instance_id'], 'repo': meta['repo'], 'base_commit': meta['base_commit'],
            'prompt': (directory/'problem_statement.md').read_text(),
            'source': str(source.resolve()), 'source_state_hash': manifest(source)['state_hash'],
            'features': {'subtask_type': 'implementation', 'category': 'repair', 'language': 'python',
                         'constraints': ['python', 'preserve public tests'], 'actions': ['read', 'edit', 'verify']},
            'allowed_write_paths': ['sympy'],
            'protected_paths': ['sympy/testing']+[k for k in manifest(source)['files'] if '/tests/' in k],
            'public_check': ['python3', '-B', 'bin/test', 'sympy/core/tests/test_basic.py']}


def _test_body(script):
    lines = script.splitlines()
    starts = [i for i, line in enumerate(lines) if START in line]
    ends = [i for i, line in enumerate(lines) if END in line]
    if len(starts) != 1 or len(ends) != 1 or ends[0] <= starts[0]+1:
        raise ValueError('Unsupported prescribed test-script boundary')
    body = '\n'.join(lines[starts[0]+1:ends[0]])
    # Environment/test-patch setup is host-owned. The original command body
    # between the official markers is copied byte-for-byte, never inferred from
    # hidden expected test names or replaced by a custom suite.
    return 'set +e\ncd /testbed\necho '+repr(START)+'\n'+body+'\n'+\
           'observatory_status=${TEST_EXIT_CODE:-$?}\necho '+repr(END)+'\n'+\
           'echo ">>>>> TestExitCode: $observatory_status"\n'


def _patch_paths(patch):
    result = []
    for line in patch.splitlines():
        if line.startswith('+++ b/'):
            key = line[6:].split('\t')[0]
            if not key or Path(key).is_absolute() or '..' in Path(key).parts or '"' in key:
                raise ValueError('Unsupported private test patch path')
            result.append(key)
    return result


def grade_candidate(*, task_directory, base_source, candidate_source, output, image_review,
                    grader_subset, reference=False, timeout=180):
    """Run after generation, or as a pristine empty/reference eligibility control."""
    import yaml
    directory, output = Path(task_directory), Path(output)
    meta = yaml.safe_load((directory/'task.yaml').read_text())
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    source = output/'source'
    shutil.copytree(candidate_source, source, ignore=shutil.ignore_patterns('.git'))
    before_grading = manifest(source)
    write_new(output/'started.json', {'task_id': meta['instance_id'], 'candidate_state_hash': before_grading['state_hash'],
        'reference_control': reference, 'image': image_review['image_id'], 'automatic_retries': 0})
    if reference:
        git(['apply', '--whitespace=nowarn', '--binary', str((directory/'gold.patch').resolve())], source)
    test_patch = directory/'test.patch'
    # Restore public tests exactly as the prescribed harness does before adding
    # the official private test patch. Generation never sees this directory.
    for key in _patch_paths(test_patch.read_text()):
        original, path = inside(base_source, key), inside(source, key)
        if original.is_file():
            path.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(original, path)
        elif path.is_file() or path.is_symlink():
            path.unlink()
    git(['apply', '--whitespace=nowarn', '--binary', str(test_patch.resolve())], source)
    script = _test_body((directory/'eval.sh').read_text())
    runner = source/'__observatory_private_eval__.sh'
    runner.write_text(script); runner.chmod(0o644)
    actor = ExactModeActor(image=image_review['image_id'], review=image_review, root=output/'actor',
                           identity=str(output), base_commit=meta['base_commit'])
    try:
        # public_check creates a fresh isolated actor even when no model actor
        # was started; no evaluator/source mounts or model process are involved.
        log = output/'test-output.log'
        executed = actor.public_check(['bash', '__observatory_private_eval__.sh'], source, timeout, raw_output=log)
        client = LocalS3Retention(Path(__file__).resolve().parents[3], output/'retention')
        archive = client.retain_file(log, kind='sealed-evaluation-log', identity=digest(str(output.resolve())))
        write_new(output/'execution.json', {k: v for k, v in executed.items() if k != 'output'})
        write_new(output/'raw-retention.json', archive)
        if executed['infrastructure_error']:
            raise EvaluationInfrastructureFailure('Prescribed tests did not execute reliably')
        tests = read(directory/'tests.json')
        specification = {k: meta[k] for k in ('instance_id', 'repo', 'version', 'log_parser', 'eval_type')}
        specification.update(image=image_review['image_id'], eval_script_list=[],
            FAIL_TO_PASS=tests['FAIL_TO_PASS'], PASS_TO_PASS=tests['PASS_TO_PASS'])
        if not specification['FAIL_TO_PASS']:
            raise ValueError('Empty official target set cannot qualify a task')
        write_new(output/'private-specification.json', specification)
        # The child imports only the reviewed namespace subset and unidiff.
        code = """import sys,json\nfrom pathlib import Path\nsys.path.insert(0,sys.argv[1])\nfrom swebench.types import TestSpec\nfrom swebench.harness.grading import get_eval_report,get_logs_eval\np=Path(sys.argv[2]);d=json.loads((p/'private-specification.json').read_text());s=TestSpec(**d)\nm,found=get_logs_eval(s,str(p/'test-output.log'))\nif not found or not m:raise ValueError('No prescribed tests observed')\nr=get_eval_report(s,{'instance_id':s.instance_id,'model_name_or_path':'observatory-native-adaptation','model_patch':'sealed-source-checkpoint'},str(p/'test-output.log'),True)\n(p/'official-report.json').write_text(json.dumps(r))\n(p/'parser-receipt.json').write_text(json.dumps({'tests_observed':len(m),'report_sha256':__import__('hashlib').sha256((p/'official-report.json').read_bytes()).hexdigest()}))\n"""
        result = subprocess.run(['python3', '-B', '-S', '-c', code, str(Path(grader_subset).resolve()), str(output.resolve())],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=60)
        if result.returncode:
            (output/'parser-error.log').write_bytes(result.stderr)
            raise ValueError('Unmodified official grader did not qualify this execution')
        report = read(output/'official-report.json')[meta['instance_id']]
        if report.get('infra_failure') or type(report.get('resolved')) is not bool:
            raise ValueError('Official grading infrastructure unresolved')
        receipt = {'task_id': meta['instance_id'], 'resolved': report['resolved'],
                   'candidate_state_hash': before_grading['state_hash'],
                   'official_report_sha256': file_digest(output/'official-report.json'),
                   'tests_observed': read(output/'parser-receipt.json')['tests_observed'],
                   'scope': 'Official prescribed tests and grading/parser code on patched offline actor; host test preparation; not full upstream image/CLI',
                   'visibility': 'evaluation_sealed', 'reference_control': reference}
        write_new(output/'grade.json', receipt)
        return receipt
    finally:
        actor.close()
