"""Call the unchanged official evaluator and retain auditable per-patch grades."""
from __future__ import annotations
import json
import hashlib
from pathlib import Path
import shutil
import subprocess
import time
import uuid

from . import benchmark
from .isolated import docker


class OfficialEvaluator:
    def __init__(self, study: Path, private_root: Path, image: str, dataset: Path,
                 timeout_seconds: int = 1200):
        self.study, self.private, self.image, self.dataset = study, private_root, image, dataset
        self.index_path = study / 'grades.json'
        self.index = json.loads(self.index_path.read_text()) if self.index_path.exists() else {}
        self.timeout_seconds = timeout_seconds
        self.cache_path = study / 'grade-cache.json'
        self.cache = json.loads(self.cache_path.read_text()) if self.cache_path.exists() else {}

    @staticmethod
    def checkpoint(path: Path, value):
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(value, indent=2) + '\n')
        temporary.replace(path)

    def __call__(self, arm: str, instance: str):
        patch_path = self.study / 'patches' / arm / (instance + '.json')
        prediction = json.loads(patch_path.read_text())
        if hashlib.sha256(prediction['model_patch'].encode()).hexdigest() != prediction['patch_sha256']:
            raise ValueError('Exported patch bytes changed before grading')
        cache_key = hashlib.sha256(benchmark.canonical({
            'instance_id': instance, 'patch_sha256': prediction['patch_sha256'],
            'evaluator_image_id': self.image, 'dataset_sha256': benchmark.digest(self.dataset),
            'timeout_seconds': self.timeout_seconds,
        }).encode()).hexdigest()
        if instance in self.index.get(arm, {}):
            report = Path(self.index[arm][instance])
            cached = self.cache.get(cache_key)
            if not cached or str(report) != cached['report'] or benchmark.digest(report) != cached['report_sha256']:
                raise ValueError('Previously indexed official grade or its provenance changed')
            benchmark.read_grade(report, instance, prediction['patch_sha256'])
            return
        if cache_key in self.cache:
            cached = self.cache[cache_key]
            report = Path(cached['report'])
            if benchmark.digest(report) != cached['report_sha256']:
                raise ValueError('Cached original official report changed')
            resolved, _, _ = benchmark.read_grade(report, instance, prediction['patch_sha256'])
            receipt = self.study / 'grading' / arm / instance / uuid.uuid4().hex[:12]
            benchmark.write_new(receipt / 'reuse.json', {
                'kind': 'reuse_exact_program_and_evaluator', 'cache_key': cache_key,
                'report': str(report), 'report_sha256': cached['report_sha256'],
                'patch_record_sha256': benchmark.digest(patch_path),
                'new_evaluation_executed': False,
            })
            self.index.setdefault(arm, {})[instance] = str(report)
            self.checkpoint(self.index_path, self.index)
            print(json.dumps({'event': 'official_grade_reused', 'arm': arm,
                              'instance_id': instance, 'resolved': resolved}), flush=True)
            return
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
                   '--instance', instance, '--run-id', run_id, '--workers', '1',
                   '--timeout', str(self.timeout_seconds)]
        benchmark.write_new(attempt / 'request.json', {
            'run_id': run_id, 'prediction_sha256': benchmark.digest(predicted),
            'model_patch_sha256': prediction['patch_sha256'],
            'patch_record_sha256': benchmark.digest(patch_path),
            'evaluator_image_id': self.image, 'dataset_sha256': benchmark.digest(self.dataset),
            'timeout_seconds': self.timeout_seconds,
        })
        started = time.monotonic()
        with (attempt / 'stdout.txt').open('x') as stream:
            process = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT,
                                     timeout=self.timeout_seconds + 1200)
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
        self.cache[cache_key] = {'report': str(report), 'report_sha256': benchmark.digest(report)}
        self.checkpoint(self.cache_path, self.cache)
        self.checkpoint(self.index_path, self.index)
        print(json.dumps({'event': 'official_grade', 'arm': arm, 'instance_id': instance,
                          'resolved': resolved}), flush=True)
