"""Reuse stock Mem0/Graphiti and pinned Smallville with native Luna callbacks.

No imports of third-party runtime code occur for the searchable-log control.
No dependency installation or service startup is implicit.
"""
import asyncio
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
GLOBAL = HERE.parents[2] / 'work/security/context-memory-20261107'


def native_calls(root, cap, port):
    from repository_memory_native import Calls

    class CapturedLuna(Calls):
        def command(self, cell):
            command = super().command(cell)
            # Versioned provider boundary; do not change frozen earlier adapters.
            settings = {
                'model_provider': 'ttgl-memory-study',
                'model_providers.ttgl-memory-study.name': 'Captured Luna memory',
                'model_providers.ttgl-memory-study.base_url': f'http://127.0.0.1:{port}/backend-api/codex',
                'model_providers.ttgl-memory-study.wire_api': 'responses',
                'model_providers.ttgl-memory-study.requires_openai_auth': True,
                'model_providers.ttgl-memory-study.request_max_retries': 0,
                'model_providers.ttgl-memory-study.stream_max_retries': 0,
                'model_providers.ttgl-memory-study.supports_websockets': False,
            }
            for key, value in settings.items():
                command[-1:-1] = ['-c', key + '=' + json.dumps(value)]
            return command

    return CapturedLuna(root, cap=cap)


class Backend:
    def __init__(self, kind, root, port=8452, cap=128):
        self.kind, self.root = kind, Path(root)
        self.namespace = 'team_' + hashlib.sha256(str(self.root.resolve()).encode()).hexdigest()[:32]
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        self.calls = None
        if kind == 'searchable_logs':
            return
        self.calls = native_calls(self.root / 'maintenance', cap, port)
        if kind == 'mem0_luna':
            from repository_mem0_luna import engine
            self.engine = engine(self.root / 'engine')
            self.engine.llm.calls = self.calls
        elif kind == 'graphiti_luna':
            import repository_graphiti_luna as adapter
            self.loop = asyncio.new_event_loop()
            self.engine, self.embedder, llm = adapter.engine(self.root / 'engine', cap=cap)
            llm.calls = self.calls
            self.loop.run_until_complete(self.engine.build_indices_and_constraints())
        elif kind == 'smallville_luna':
            from smallville_compat_v4 import CompatibleMemoryV4
            from smallville_local_embeddings import LocalEmbeddings
            embed = LocalEmbeddings(GLOBAL, self.root / 'embedding-inferences.jsonl')
            self.engine = CompatibleMemoryV4(self.root / 'engine', embed, self.calls,
                dict(name='Repository team', currently='Maintaining source-backed shared coding findings.'),
                restore_last_access=True)
        else:
            raise ValueError('Unknown registered backend')

    def publish(self, record):
        body = json.dumps(record, ensure_ascii=False)
        if self.kind == 'mem0_luna':
            return self.engine.add([dict(role='user', content=body)], user_id='repository-team')
        if self.kind == 'graphiti_luna':
            from graphiti_core.nodes import EpisodeType
            result = self.loop.run_until_complete(self.engine.add_episode(name=record['id'],
                episode_body=body, source_description='Fallible agent publication with original evidence reference',
                reference_time=datetime.utcnow(), source=EpisodeType.text, group_id=self.namespace))
            return dict(nodes=len(result.nodes), edges=len(result.edges))
        if self.kind == 'smallville_luna':
            when = datetime.utcnow()
            # Observation text is retained; Luna assigns importance and creates
            # reflections when the original threshold is naturally reached.
            node = self.engine.observe(body, record['author'], 'reported', record['id'], when)
            thoughts = self.engine.reflect_if_due(when)
            return dict(node_id=node.node_id, reflections=[n.node_id for n in thoughts])
        return dict(indexed=True, auxiliary_model_calls=0)

    def search(self, query, limit):
        if self.kind == 'mem0_luna':
            return self.engine.search(query, filters={'user_id':'repository-team'}, limit=limit)
        if self.kind == 'graphiti_luna':
            # Stock combined RRF includes original episodes as well as extracted
            # facts. Fact-only search cannot recover an episode with zero edges.
            # This is a versioned interface candidate; earlier empty native
            # retrievals are preserved, never overwritten or retried.
            from graphiti_core.search.search_config_recipes import COMBINED_HYBRID_SEARCH_RRF
            config=COMBINED_HYBRID_SEARCH_RRF.model_copy(deep=True)
            config.limit=limit
            hits = self.loop.run_until_complete(self.engine.search_(query,config=config,
                group_ids=[self.namespace]))
            return dict(facts=[h.model_dump(mode='json',exclude={'fact_embedding'}) for h in hits.edges],
                episodes=[dict(record_id=e.name,episode_id=e.uuid,preview=e.content[:1600],
                               characters=len(e.content)) for e in hits.episodes],
                method='stock Graphiti combined RRF over facts/entities/episodes; original record_id is pageable')
        if self.kind == 'smallville_luna':
            # Upstream ranking normalizes min/max and has no empty-store case.
            # An empty fresh store has no memories to rank or model call to make.
            if not self.engine.memory.id_to_node:
                return []
            return [dict(node_id=n.node_id, text=n.description, evidence=n.filling, kind=n.type)
                    for n in self.engine.retrieve(query, datetime.utcnow(), limit)]
        return []

    def close(self):
        if self.kind == 'mem0_luna':
            self.engine.vector_store.client.close()
            self.engine.db.close()
        elif self.kind == 'graphiti_luna':
            # Seal the cell's graph data outside ephemeral Neo4j storage.
            nodes,_,_=self.loop.run_until_complete(self.engine.driver.execute_query(
                'MATCH (n {group_id: $group}) RETURN labels(n) AS labels, properties(n) AS properties',
                params={'group':self.namespace}))
            edges,_,_=self.loop.run_until_complete(self.engine.driver.execute_query(
                'MATCH (a)-[r]->(b) WHERE a.group_id=$group AND b.group_id=$group RETURN a.uuid AS source, b.uuid AS target, type(r) AS type, properties(r) AS properties',
                params={'group':self.namespace}))
            with (self.root/'graph-snapshot.json').open('x') as stream:
                json.dump(dict(namespace=self.namespace,nodes=[dict(n) for n in nodes],
                    edges=[dict(e) for e in edges],model_calls=0),stream,default=str)
            self.loop.run_until_complete(self.engine.close())
            self.embedder.close()
            self.loop.close()
