"""Call the unchanged official evaluator and retain auditable per-patch grades."""
from __future__ import annotations
import json
from pathlib import Path
import shutil
import subprocess
import time
import uuid

from . import benchmark
from .isolated import docker


class OfficialEvaluator:
    def __init__(self, study: Path, private_root: Path, image: str, dataset: Path):
        self.study, self.private, self.image, self.dataset = study, private_root, image, dataset
        self.index_path = study / 'grades.json'
        self.index = json.loads(self.index_path.read_text()) if self.index_path.exists() else {}

    def __call__(self, arm: str, instance: str):
        patch_path = self.study / 'patches' / arm / (instance + '.json')
        prediction = json.loads(patch_path.read_text())
        if instance in self.index.get(arm, {}):
            # The existing analyzer checks patch/report joins again. Avoid
            # repeating a completed grader just because generation resumed.
            report = Path(self.index[arm][instance])
            if report.exists():
                return
            raise ValueError('Previously indexed official grade is missing')
        nonce = uuid.uuid4().hex[:12]
        run_id = f'ttgl-{arm}-{instance}-{prediction["patch_sha256"][:8]}-{nonce}'
        attempt = self.study / 'grading' / arm / instance / nonce
        attempt.mkdir(parents=True)
        one = {k: prediction[k] for k in ('instance_id', 'model_name_or_path', 'model_patch')}
        predicted = self.private / (run_id + '.jsonl')
        with predicted.open('x') as stream:
            stream.write(benchmark.canonical(one) + '\n')
        command = ['docker', 'run', '--rm', '-v', '/var/run/docker.sock:/var/run/docker.sock',
                   '-v', f'{self.private}:{self.private}', '-w', str(self.private), self.image,
                   'eval', str(self.dataset), '--predictions', str(predicted),
                   '--instance', instance, '--run-id', run_id, '--workers', '1', '--timeout', '600']
        benchmark.write_new(attempt / 'request.json', {
            'run_id': run_id, 'prediction_sha256': benchmark.digest(predicted),
            'model_patch_sha256': prediction['patch_sha256'],
            'patch_record_sha256': benchmark.digest(patch_path),
            'evaluator_image_id': self.image, 'dataset_sha256': benchmark.digest(self.dataset),
        })
        started = time.monotonic()
        with (attempt / 'stdout.txt').open('x') as stream:
            process = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=1200)
        source = self.private / 'logs/evaluation' / run_id
        if source.exists():
            shutil.copytree(source, attempt / 'logs')
        reports = list((attempt / 'logs').glob('**/report.json'))
        if len(reports) == 1:
            report = reports[0]
        else:
            # Official v5 skips exactly empty patches; retain its original
            # aggregate report so the existing importer can prove that case.
            report = attempt / 'logs/results.json'
        benchmark.write_new(attempt / 'execution.json', {
            'returncode': process.returncode, 'elapsed_seconds': time.monotonic()-started,
            'report': str(report), 'report_sha256': benchmark.digest(report) if report.exists() else None,
        })
        if not report.exists():
            raise RuntimeError('Official grader produced no report; retain attempt and reconcile')
        # Reuse the strict importer: no self-reports or synthetic failures.
        entry = json.loads(report.read_text()).get(instance, {})
        if entry.get('infra_failure') is True:
            raise RuntimeError('Official grader reported infrastructure failure; preserve and reconcile')
        resolved, _, _ = benchmark.read_grade(report, instance, prediction['patch_sha256'])
        self.index.setdefault(arm, {})[instance] = str(report)
        temporary = self.index_path.with_suffix('.tmp')
        temporary.write_text(json.dumps(self.index, indent=2) + '\n')
        temporary.replace(self.index_path)
        print(json.dumps({'event': 'official_grade', 'arm': arm, 'instance_id': instance,
                          'resolved': resolved}), flush=True)
