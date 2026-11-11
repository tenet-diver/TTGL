#!/usr/bin/env python3
"""Bounded real Graphiti ingestion/retrieval diagnostic; no coding outcome."""
import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import time


async def run(root):
    from openai import AsyncOpenAI, DefaultAsyncHttpxClient
    from graphiti_core import Graphiti
    from graphiti_core.nodes import EpisodeType
    from graphiti_core.llm_client.config import LLMConfig
    from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient
    from graphiti_core.embedder.openai import OpenAIEmbedder, OpenAIEmbedderConfig
    from graphiti_core.cross_encoder.openai_reranker_client import OpenAIRerankerClient
    root.mkdir(exist_ok=False)
    body = 'Project cedar uses the verified test command "pytest tests/test_cache.py -q". Worker Ada executed that command successfully at revision r1.'
    query = 'What verified test command does project cedar use?'
    plan = dict(kind='synthetic real Graphiti mechanism diagnostic', episode=body, query=query,
        group=root.name.replace('-', '_'), request_limit=16, total_timeout_seconds=600,
        max_output_tokens=512, sdk_retries=0,
        pass_rule='Ingest and retrieve at least one fact retaining the exact command and project identity',
        source_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest())
    (root / 'plan.json').write_text(json.dumps(plan, indent=2))
    requests = 0
    async def before(request):
        nonlocal requests
        if requests >= plan['request_limit']:
            raise RuntimeError('Diagnostic HTTP call limit reached; no further inference')
        requests += 1
        with (root / 'http.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(event='request', number=requests, body=json.loads(request.content))) + '\n')
    async def after(response):
        await response.aread()
        with (root / 'http.jsonl').open('a') as stream:
            stream.write(json.dumps(dict(event='response', status=response.status_code, body=response.json())) + '\n')
    transport = DefaultAsyncHttpxClient(event_hooks={'request': [before], 'response': [after]}, timeout=120)
    llm_sdk = AsyncOpenAI(api_key='local-only', base_url='http://127.0.0.1:8450/v1', max_retries=0, http_client=transport)
    embed_sdk = AsyncOpenAI(api_key='local-only', base_url='http://127.0.0.1:8451/v1', max_retries=0, timeout=60)
    config = LLMConfig(api_key='local-only', model='local-knowledge', small_model='local-knowledge', temperature=0, max_tokens=512)
    graph = Graphiti('bolt://127.0.0.1:8767', '', '',
        llm_client=OpenAIGenericClient(config, client=llm_sdk, max_tokens=512, structured_output_mode='json_schema'),
        embedder=OpenAIEmbedder(OpenAIEmbedderConfig(embedding_model='local-embedding', embedding_dim=384), client=embed_sdk),
        cross_encoder=OpenAIRerankerClient(config, client=llm_sdk), max_coroutines=1)
    started = time.perf_counter()
    try:
        async with asyncio.timeout(600):
            await graph.build_indices_and_constraints()
            episode = await graph.add_episode(name='verified-procedure-r1', episode_body=body,
                source_description='Synthetic public diagnostic observation; no benchmark content',
                reference_time=datetime(2026, 11, 11, tzinfo=timezone.utc),
                source=EpisodeType.text, group_id=plan['group'])
            (root / 'ingested.json').write_text(episode.model_dump_json(indent=2))
            facts = await graph.search(query, group_ids=[plan['group']], num_results=5)
            values = [f.model_dump(mode='json') for f in facts]
            passed = any('pytest tests/test_cache.py -q' in f['fact'] and 'cedar' in f['fact'].lower() for f in values)
            result = dict(passed=passed, facts=values, elapsed_seconds=time.perf_counter()-started, llm_http_calls=requests,
                scope='One synthetic ingestion and query, not stale-fact handling, MCP visibility or coding efficacy')
            (root / 'result.json').write_text(json.dumps(result, indent=2))
            print(json.dumps(result), flush=True)
    except BaseException as error:
        (root / 'failed.json').write_text(json.dumps(dict(error=repr(error), elapsed_seconds=time.perf_counter()-started,
            llm_http_calls=requests, no_assignment_retry=True), indent=2))
        raise
    finally:
        await graph.close()
        await llm_sdk.close()
        await embed_sdk.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    args = parser.parse_args()
    os.environ['GRAPHITI_TELEMETRY_ENABLED'] = 'false'
    asyncio.run(run(args.root))
