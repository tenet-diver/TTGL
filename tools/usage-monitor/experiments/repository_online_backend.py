"""Incremental stock Mem0/Graphiti, one own visible episode per completed task.

Operations have unique output directories; persistent namespaces never ingest
another arm's experience. No re-ingestion, repair retry or hidden grade feedback.
"""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path


async def graphiti(root, data):
    from repository_graphiti_luna import engine
    from graphiti_core.nodes import EpisodeType
    graph, embedder, llm = engine(root, cap=256)
    before = len(llm.calls.registry)
    try:
        if data['action'] == 'update':
            e = data['episode']
            result = await graph.add_episode(name=e['id'], episode_body=e['body'],
                source_description='Own preceding public coding attempt. Fallible observations and claims, no hidden test/grade feedback. Time is actual ingestion clock.',
                reference_time=datetime.now(timezone.utc), source=EpisodeType.text, group_id=data['namespace'])
            value = dict(nodes=len(result.nodes), edges=len(result.edges))
        else:
            hits = await graph.search(data['query'], group_ids=[data['namespace']], num_results=8)
            value = dict(hits=[h.model_dump(mode='json') for h in hits])
        return dict(value, call_start=before, call_end=len(llm.calls.registry))
    finally:
        await graph.close()
        embedder.close()


def mem0(root, data):
    from repository_mem0_luna import engine
    memory = engine(root)
    before = len(memory.llm.calls.registry)
    try:
        if data['action'] == 'update':
            e = data['episode']
            value = dict(added=memory.add([dict(role='user', content=e['body'])],
                user_id=data['namespace'], metadata={'source_episode': e['id']}))
        else:
            value = dict(hits=memory.search(data['query'], filters={'user_id': data['namespace']}, limit=8)['results'])
        return dict(value, call_start=before, call_end=len(memory.llm.calls.registry))
    finally:
        memory.vector_store.client.close()
        memory.db.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backend', choices=['mem0', 'graphiti'])
    parser.add_argument('root', type=Path)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=False)
    data = json.loads(args.input.read_text())
    (args.output / 'started.json').write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(), no_retry=True)))
    try:
        value = asyncio.run(graphiti(args.root, data)) if args.backend == 'graphiti' else mem0(args.root, data)
        (args.output / 'complete.json').write_text(json.dumps(value, indent=2))
    except BaseException as error:
        (args.output / 'stopped.json').write_text(json.dumps(dict(error=str(error), no_retry=True)))
        raise
