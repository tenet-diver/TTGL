"""Frozen-history backend ingestion/search in separate reviewed runtime graphs."""
import argparse
import asyncio
from datetime import datetime, timezone
import json
from pathlib import Path
import time


async def graphiti(root, data):
    from repository_graphiti_luna import engine
    from graphiti_core.nodes import EpisodeType
    graph, embedder, llm = engine(root, cap=128)
    try:
        # Indices were actually built/probed once in preflight; each target has
        # its own group_id, never a new global drop/recreate of shared indices.
        additions = []
        for episode in data['episodes']:
            result = await graph.add_episode(name=episode['id'], episode_body=episode['body'],
                    source_description='Earlier same-repository ordinal trajectory; recorded time is ingestion clock, NOT historical PR date. Fallible model work, not hidden grader evidence.',
                    reference_time=datetime.now(timezone.utc), source=EpisodeType.text,
                    group_id=data['namespace'])
            additions.append(dict(id=episode['id'], nodes=len(result.nodes), edges=len(result.edges)))
            (root / 'add-progress.json').write_text(json.dumps(additions, indent=2))
        hits = await graph.search(data['query'], group_ids=[data['namespace']], num_results=8)
        keys = ('uuid', 'fact', 'name', 'episodes', 'valid_at', 'invalid_at', 'expired_at')
        return dict(additions=additions, native_calls=len(llm.calls.registry),
                    hits=[{k: h.model_dump(mode='json').get(k) for k in keys} for h in hits])
    finally:
        await graph.close()
        embedder.close()


def mem0(root, data):
    from repository_mem0_luna import engine
    memory = engine(root)
    memory.llm.calls.cap = 128
    try:
        additions = []
        for episode in data['episodes']:
            result = memory.add([dict(role='user', content=episode['body'])],
                    user_id=data['namespace'], metadata={'source_episode': episode['id']})
            additions.append(dict(id=episode['id'], added=result))
            (root / 'add-progress.json').write_text(json.dumps(additions, indent=2))
        hits = memory.search(data['query'], filters={'user_id': data['namespace']}, limit=8)
        return dict(additions=additions, native_calls=len(memory.llm.calls.registry), hits=hits['results'])
    finally:
        memory.vector_store.client.close()
        memory.db.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backend', choices=['mem0', 'graphiti'])
    parser.add_argument('root', type=Path)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=False)
    data = json.loads(args.input.read_text())
    start = time.perf_counter()
    try:
        value = asyncio.run(graphiti(args.root, data)) if args.backend == 'graphiti' else mem0(args.root, data)
        value.update(backend=args.backend, seconds=time.perf_counter() - start,
                     scope='Stock engine with disclosed native/local adapters; no hosted memory service')
        (args.root / 'complete.json').write_text(json.dumps(value, indent=2))
        print(json.dumps(dict(backend=args.backend, hits=len(value['hits']), native_calls=value['native_calls'])), flush=True)
    except BaseException as error:
        (args.root / 'stopped.json').write_text(json.dumps(dict(error=str(error), no_retry=True), indent=2))
        raise


if __name__ == '__main__':
    main()
