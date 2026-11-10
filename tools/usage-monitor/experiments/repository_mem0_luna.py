"""Self-hosted stock Mem0 extraction/search with audited native Luna transport."""
import json
import os
from pathlib import Path
import sys
from mem0.configs.llms.base import BaseLlmConfig
from mem0.llms.base import LLMBase
from mem0.embeddings.base import EmbeddingBase
from repository_memory_native import Calls
from smallville_local_embeddings import LocalEmbeddings

HERE = Path(__file__).resolve().parent
GLOBAL = HERE.parents[2] / 'work/security/context-memory-20261107'


class NativeLuna(LLMBase):
    def __init__(self, config=None):
        super().__init__(config)
        self.calls = Calls(Path(os.environ['TTGL_MEMORY_CALL_ROOT']), cap=256)

    def generate_response(self, messages, tools=None, tool_choice='auto', **kwargs):
        if tools:
            raise ValueError('This registered Mem0 configuration uses text/JSON extraction, not tool extraction')
        return json.dumps(self.calls.json(messages, 'mem0_extraction_or_update'))


class BGE(EmbeddingBase):
    def __init__(self, config=None):
        super().__init__(config)
        self.config.embedding_dims = 384
        self.encoder = LocalEmbeddings(GLOBAL, Path(os.environ['TTGL_MEMORY_EMBED_RECEIPTS']))

    def embed(self, text, memory_action=None):
        return self.encoder(text)


def engine(root):
    if os.environ.get('MEM0_TELEMETRY') != 'false' or os.environ.get('HF_HUB_OFFLINE') != '1':
        raise ValueError('Telemetry and model downloads must be disabled')
    from mem0 import Memory
    from mem0.configs.base import MemoryConfig
    from mem0.utils.factory import LlmFactory, EmbedderFactory
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    os.environ['TTGL_MEMORY_CALL_ROOT'] = str(root / 'maintenance')
    os.environ['TTGL_MEMORY_EMBED_RECEIPTS'] = str(root / 'embedding-inferences.jsonl')
    # Stock config validator uses provider names; process-local factory mapping
    # adapts only transport/embedding interfaces. No installed source is patched.
    LlmFactory.register_provider('openai', 'repository_mem0_luna.NativeLuna', BaseLlmConfig)
    EmbedderFactory.provider_to_class['fastembed'] = 'repository_mem0_luna.BGE'
    return Memory(MemoryConfig(
        llm=dict(provider='openai', config=dict(model='gpt-6-luna')),
        embedder=dict(provider='fastembed', config=dict(model='BAAI/bge-small-en-v1.5', embedding_dims=384)),
        vector_store=dict(provider='qdrant', config=dict(path=str(root / 'qdrant'),
                          collection_name='repository_memory', embedding_model_dims=384)),
        history_db_path=str(root / 'history.sqlite')))


def preflight(root):
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    memory = engine(root)
    try:
        added = memory.add([dict(role='user', content='The cedar repository runs public checks with python -m unittest. Its configuration parser lives in cedar/config.py. These are documentation observations, not proof that tests passed.')], user_id='cedar')
        hits = memory.search('How does cedar run public checks?', filters={'user_id': 'cedar'}, limit=8)
        other = memory.search('How does cedar run public checks?', filters={'user_id': 'other'}, limit=8)
        result = dict(added=added, hits=hits, other_scope_hits=other,
              native_calls=len(memory.llm.calls.registry),
              passed=bool(hits.get('results')) and not other.get('results'),
              scope='Actual adapted Mem0/Luna ingestion/retrieval/isolation; not coding efficacy')
        (root / 'complete.json').write_text(json.dumps(result, indent=2))
        print(json.dumps(dict(passed=result['passed'], native_calls=result['native_calls'])), flush=True)
        if not result['passed']:
            raise ValueError('Mechanism failed; preserve, never silently rerun')
    except BaseException as error:
        (root / 'stopped.json').write_text(json.dumps(dict(error=str(error), no_retry=True)))
        raise
    finally:
        memory.vector_store.client.close()
        memory.db.close()


if __name__ == '__main__':
    preflight(Path(sys.argv[1]))
