"""Stock Graphiti with native Luna JSON and isolated offline BGE adapters.

No hosted Zep, cloud embedding, cross-encoder fallback, automatic model repair,
or upstream LLM retry. Stock prompts, graph extraction and RRF search remain.
Run only with the reviewed Graphiti runtime and local Neo4j derivative.
"""
import asyncio
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import selectors
import signal
import subprocess
import sys
import threading
import time

from graphiti_core import Graphiti
from graphiti_core.cross_encoder.client import CrossEncoderClient
from graphiti_core.embedder.client import EmbedderClient, EmbedderConfig
from graphiti_core.llm_client.client import LLMClient
from graphiti_core.llm_client.config import LLMConfig, ModelSize
from graphiti_core.nodes import EpisodeType
from repository_memory_native import Calls

HERE = Path(__file__).resolve().parent
GLOBAL = HERE.parents[2] / 'work/security/context-memory-20261107'


class Luna(LLMClient):
    def __init__(self, root, cap=256):
        super().__init__(LLMConfig(model='gpt-6-luna', small_model='gpt-6-luna'), cache=False)
        self.calls = Calls(root, cap=cap)

    async def _generate_response_with_retry(self, *args, **kwargs):
        # Override only the provider's retry boundary; base generate_response
        # retains its schema/language/attribute instructions and cleaning.
        return await self._generate_response(*args, **kwargs)

    async def _generate_response(self, messages, response_model=None, max_tokens=None,
                                 model_size=ModelSize.medium, *, model=None):
        if model is not None and model != 'gpt-6-luna':
            raise ValueError('Unregistered model override')
        schema = response_model.model_json_schema() if response_model else None
        role = 'graphiti_' + (response_model.__name__ if response_model else 'json')
        value = await asyncio.to_thread(self.calls.json,
                    [m.model_dump() for m in messages], role, schema)
        if response_model:
            value = response_model.model_validate(value).model_dump(mode='json')
        return value


class Embeddings(EmbedderClient):
    def __init__(self, root):
        self.config = EmbedderConfig(embedding_dim=384)
        self.root = Path(root)
        self.root.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.ident = 0
        self.buffer = b''
        self.env = os.environ.copy()
        self.env.update(PYTHONPATH=str(HERE) + ':' + str(GLOBAL / 'memory-runtime'),
                        HF_HUB_OFFLINE='1', HF_HUB_DISABLE_TELEMETRY='1')
        self.err = (self.root / ('worker-' + str(time.time_ns()) + '.log')).open('x')
        self.p = subprocess.Popen([sys.executable, '-S', str(HERE / 'repository_embedding_worker.py'),
                    '--model-root', str(GLOBAL), '--receipts', str(self.root / 'inferences.jsonl')],
                    env=self.env, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=self.err, start_new_session=True)
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.p.stdout, selectors.EVENT_READ)

    def batch(self, texts):
        with self.lock:
            self.ident += 1
            self.p.stdin.write((json.dumps({'id': self.ident, 'texts': texts}) + '\n').encode())
            self.p.stdin.flush()
            deadline = time.monotonic() + 120
            while time.monotonic() < deadline:
                if b'\n' in self.buffer:
                    line, self.buffer = self.buffer.split(b'\n', 1)
                    value = json.loads(line)
                    if value['id'] != self.ident:
                        raise ValueError('Embedding response identity mismatch')
                    if len(value['vectors']) != len(texts) or any(len(v) != 384 for v in value['vectors']):
                        raise ValueError('Embedding dimensionality/cardinality mismatch')
                    return value['vectors']
                if not self.selector.select(max(0.001, deadline - time.monotonic())):
                    break
                data = os.read(self.p.stdout.fileno(), 65536)
                if not data:
                    raise RuntimeError('Embedding worker exited; no fallback')
                self.buffer += data
            raise TimeoutError('Embedding worker timed out; no retry')

    async def create(self, input_data):
        if isinstance(input_data, list) and len(input_data) == 1:
            input_data = input_data[0]
        if not isinstance(input_data, str):
            raise ValueError('Unsupported embedding input; no implicit token conversion')
        return (await asyncio.to_thread(self.batch, [input_data]))[0]

    async def create_batch(self, input_data_list):
        return await asyncio.to_thread(self.batch, input_data_list)

    def close(self):
        if self.p.poll() is None:
            os.killpg(self.p.pid, signal.SIGTERM)
            self.p.wait(timeout=10)
        self.selector.close()
        self.p.stdin.close()
        self.p.stdout.close()
        self.err.close()


class NoCrossEncoder(CrossEncoderClient):
    async def rank(self, query, passages):
        raise ValueError('Registered RRF search must not invoke an unmetered reranker')


def engine(root, cap=256):
    if os.environ.get('GRAPHITI_TELEMETRY_ENABLED') != 'false':
        raise ValueError('Telemetry must be disabled before Graphiti construction')
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    embedder = Embeddings(root / 'embeddings')
    llm = Luna(root / 'maintenance', cap=cap)
    graph = Graphiti('bolt://127.0.0.1:17687', '', '', llm_client=llm,
                     embedder=embedder, cross_encoder=NoCrossEncoder(), max_coroutines=1)
    return graph, embedder, llm


async def preflight(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    graph, embedder, llm = engine(root, cap=24)
    try:
        await graph.build_indices_and_constraints()
        result = await graph.add_episode(name='public environment observation',
            episode_body='The cedar repository runs its public checks using python -m unittest. Its configuration parser lives in cedar/config.py. These are documentation observations, not successful test execution.',
            source_description='Synthetic mechanism fixture; never a benchmark result',
            reference_time=datetime.now(timezone.utc), source=EpisodeType.text,
            group_id='ttgl_repository_memory_preflight_001')
        hits = await graph.search('How does cedar run public checks?',
                    group_ids=['ttgl_repository_memory_preflight_001'], num_results=8)
        other = await graph.search('How does cedar run public checks?',
                    group_ids=['ttgl_repository_memory_preflight_other_001'], num_results=8)
        receipt = dict(nodes=len(result.nodes), edges=len(result.edges),
            hits=[h.model_dump(mode='json') for h in hits], other_scope_hits=len(other),
            native_calls=len(llm.calls.registry), passed=bool(hits) and not other,
            scope='Actual Graphiti ingestion/retrieval/namespace check only; not coding efficacy')
        (root / 'complete.json').write_text(json.dumps(receipt, indent=2))
        print(json.dumps({k: receipt[k] for k in ['nodes', 'edges', 'other_scope_hits', 'native_calls', 'passed']}), flush=True)
        if not receipt['passed']:
            raise ValueError('Graphiti mechanism check failed; preserve, never silently rerun')
    except BaseException as error:
        (root / 'stopped.json').write_text(json.dumps(dict(error=str(error), no_retry=True)))
        raise
    finally:
        await graph.close()
        embedder.close()


if __name__ == '__main__':
    asyncio.run(preflight(Path(sys.argv[1])))
