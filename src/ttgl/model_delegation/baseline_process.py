"""Separate reviewed numerical runtime; JSON only, no API clients or pickle.

A persistent child fits once on development and reports both setup and finite
prediction CPU/wall time. Native Codex/Node never inherits its loader overrides.
"""
from __future__ import annotations
import json
import abc
import os
from pathlib import Path
import subprocess
import selectors
import sys
import time
from .released_baselines import _selected
from ..experience_routing.io import file_digest


class LocalBaselineProcess:
    def __init__(self, config_path, *, config_sha256, site, native_libraries, root):
        if file_digest(config_path) != config_sha256:
            raise ValueError('Frozen local baseline configuration differs')
        self.pins = json.loads(Path(config_path).read_text())['pins']
        self.stderr_path = Path(config_path).with_suffix('.runtime-stderr.log')
        self.stderr = self.stderr_path.open('x')
        self.stderr_path.chmod(0o600)
        env = dict(os.environ, LD_LIBRARY_PATH=str(native_libraries), OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1')
        code = "import sys;sys.path[:0]=sys.argv[1:3];from ttgl.model_delegation.baseline_process import serve;serve(sys.argv[3])"
        self.process = subprocess.Popen([sys.executable, '-B', '-S', '-c', code,
            str(Path(root)/'src'), str(site), str(config_path)], env=env,
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=self.stderr, text=True)
        self.measurements = []
        ready = self._read()
        if ready.get('ready') is not True:
            self.close(); raise ValueError('Reviewed local baseline runtime did not initialize')
        self.setup = ready

    def _read(self):
        with selectors.DefaultSelector() as selector:
            selector.register(self.process.stdout, selectors.EVENT_READ)
            if not selector.select(timeout=60):
                self.process.terminate()
                self.process.wait(timeout=10)
                raise ValueError('Finite local baseline deadline exceeded; no retry')
        line = self.process.stdout.readline()
        if not line:
            raise ValueError('Local baseline runtime stopped; no alternate scorer')
        result = json.loads(line)
        if 'error' in result:
            raise ValueError('Local baseline runtime rejected request: '+result['error'])
        return result

    def request(self, operation, **values):
        self.process.stdin.write(json.dumps({'operation': operation, **values})+'\n')
        self.process.stdin.flush()
        result = self._read(); self.measurements.append(result['timing'])
        return result

    def close(self):
        if self.process.poll() is None:
            self.process.stdin.close()
            try: self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.process.terminate(); self.process.wait(timeout=10)
        self.process.stdout.close()
        self.stderr.close()

    def router(self):
        owner = self
        pin = self.pins['routellm_routers']
        namespace = _selected(pin['path'], pin['sha256'], {'Router'}, {'abc': abc})
        class Router(namespace['Router']):
            def calculate_strong_win_rate(self, prompt):
                return owner.request('route_score', text=prompt)['score']
        return Router()

    def cascade(self, pins, strategy):
        from .released_baselines import make_frugalgpt
        cascade = _selected(pins['frugalgpt_cascade']['path'], pins['frugalgpt_cascade']['sha256'], {'scorer_text'}, {})
        _selected(pins['frugalgpt_cascade']['path'], pins['frugalgpt_cascade']['sha256'], set(), cascade,
                  class_methods={'LLMCascade': {'get_completion'}})
        chain = _selected(pins['frugalgpt_chain']['path'], pins['frugalgpt_chain']['sha256'], set(), {},
                          class_methods={'LLMChain': {'reset', 'nextAPIandScore'}})
        owner = self
        class Scorer:
            def __init__(self, model): self.model = model
            def get_score(self, text): return owner.request('quality', model=self.model, text=text)['score']
        return make_frugalgpt((None,cascade,chain), {m:Scorer(m) for m in ('gpt-6-luna','gpt-6.1-sol')}, strategy)


def serve(config_path):
    from .released_baselines import load_cores, make_routellm, train_quality
    config = json.loads(Path(config_path).read_text())
    def clock(): return time.process_time(), time.monotonic()
    def elapsed(start): return {'cpu_seconds':time.process_time()-start[0], 'wall_seconds':time.monotonic()-start[1],
                                'scope':'local feature/scorer computation; no generative model inference'}
    started = clock()
    try:
        cores = load_cores(config['pins'])
        router = make_routellm(cores, config['pairs'])
        scorers, stats = train_quality(cores, config['records'])
        print(json.dumps({'ready':True,'statistics':stats,'timing':elapsed(started)}),flush=True)
    except Exception as error:
        print(json.dumps({'error':type(error).__name__}),flush=True); return
    for line in sys.stdin:
        started = clock()
        try:
            request = json.loads(line)
            if request['operation']=='route_score': score=float(router.calculate_strong_win_rate(request['text']))
            elif request['operation']=='quality': score=scorers[request['model']].get_score(request['text'])
            else: raise ValueError('Unsupported operation')
            print(json.dumps({'score':score,'timing':elapsed(started)}),flush=True)
        except Exception as error:
            print(json.dumps({'error':type(error).__name__}),flush=True)
