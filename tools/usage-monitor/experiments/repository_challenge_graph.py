"""Evidence policy over the maintained MCP memory server, not a new database.

Claims are fallible, source-linked versions. Updating a claim preserves its old
node and raw evidence. Only this repository's visible ledger is admissible.
Single-writer callers must hold the experiment's repository/arm lock.
"""
import json
from pathlib import Path
import time
import uuid

from raw_memory_backends import initialize

REPO = Path(__file__).resolve().parents[3]
ENTRY = REPO / 'work/security/context-memory-20261107/mcp-memory-review/node_modules/@modelcontextprotocol/server-memory/dist/index.js'
TYPES = {'requirement', 'component', 'hypothesis', 'observation', 'procedure', 'check'}


class ChallengeGraph:
    def __init__(self, root, ledger, repository):
        self.root, self.ledger, self.repository = Path(root), ledger, repository
        self.root.mkdir(parents=True, exist_ok=True)
        identity = self.root / 'namespace.json'
        expected = dict(repository=repository, ledger=str(ledger.path.resolve()), schema=1)
        if identity.exists():
            if json.loads(identity.read_text()) != expected:
                raise ValueError('Graph namespace/ledger identity mismatch')
        else:
            with identity.open('x') as handle:
                json.dump(expected, handle)
        refresh = json.loads((REPO / 'work/security/repository-memory-20261110/mcp-graph-refresh-001.json').read_text())
        if refresh['known_findings']:
            raise ValueError('Dependency findings block execution')
        self.client = initialize(ENTRY, self.root / 'knowledge.jsonl',
                                 self.root / ('server-' + str(time.time_ns()) + '.log'))

    def close(self):
        self.client.close()

    def snapshot(self):
        return self.client.tool('read_graph', {})

    def add(self, kind, text, refs, revision, supersedes=None, related=()):
        if kind not in TYPES or not isinstance(text, str) or not 1 <= len(text) <= 4000:
            raise ValueError('Invalid bounded graph claim')
        if not isinstance(revision, str) or not revision or not refs or len(refs) > 16:
            raise ValueError('Revision and visible evidence are required')
        evidence = []
        for ref in refs:
            source = self.ledger.read(ref)
            evidence.append(dict(id=ref, sha256=source['sha256']))
        graph = self.snapshot()
        known = {n['name'] for n in graph['entities']}
        if any(n not in known for n in related) or (supersedes and supersedes not in known):
            raise ValueError('Graph relation outside this namespace')
        ident = 'claim_' + uuid.uuid4().hex
        body = dict(repository=self.repository, revision=revision, text=text,
                    evidence=evidence, status='fallible_agent_claim',
                    supersedes=supersedes, created_ns=time.time_ns())
        self.client.tool('create_entities', dict(entities=[dict(
            name=ident, entityType=kind, observations=[json.dumps(body, sort_keys=True)])]))
        relations = [{'from': ident, 'to': n, 'relationType': 'related_to'} for n in related]
        if supersedes:
            relations.append({'from': ident, 'to': supersedes, 'relationType': 'supersedes'})
        if relations:
            self.client.tool('create_relations', dict(relations=relations))
        return dict(id=ident, **body)

    def search(self, query, limit=8, budget=12000):
        # Maintained lexical node search plus one-hop graph neighbors. No claim
        # of learned graph reasoning, semantic truth, or embedding superiority.
        import re
        if not isinstance(query, str) or not query.strip() or len(query) > 6000 or type(limit) is not int or not 1 <= limit <= 8:
            raise ValueError('Invalid bounded graph query')
        graph = self.snapshot()
        inactive = {r['to'] for r in graph['relations'] if r['relationType'] == 'supersedes'}
        scores = {}
        for word in list(dict.fromkeys(re.findall(r'\w+', query.lower())))[:24]:
            if len(word) < 3:
                continue
            hits = self.client.tool('search_nodes', dict(query=word))['entities']
            for n in hits:
                if n['name'] not in inactive:
                    scores[n['name']] = scores.get(n['name'], 0) + 1 / max(1, len(hits))
        for r in graph['relations']:
            if r['relationType'] == 'supersedes':
                continue
            if r['from'] in scores and r['to'] not in inactive:
                scores.setdefault(r['to'], .01)
            if r['to'] in scores and r['from'] not in inactive:
                scores.setdefault(r['from'], .01)
        by_id = {n['name']: n for n in graph['entities']}
        hits, used = [], 0
        for name in sorted(scores, key=lambda n: (-scores[n], n)):
            node = by_id[name]
            size = len(json.dumps(node))
            if used + size <= budget:
                hits.append(node)
                used += size
            if len(hits) >= min(limit, 8):
                break
        return dict(hits=hits, active_nodes=len(by_id) - len(inactive),
                    retrieval='Lexical union and one-hop relations; source-linked fallible claims')

    def prepare(self, calls, sources, revision):
        # Full raw evidence remains in the ledger. This bounded model view is
        # explicit and identical for graph/reset variants in a future protocol.
        admitted, used = [], 0
        for ident in sources:
            record = self.ledger.read(ident, limit=8000)
            if used + len(record['body']) <= 24000:
                admitted.append(record)
                used += len(record['body'])
        if not admitted:
            raise ValueError('No visible public evidence')
        schema = dict(type='object', required=['claims'], additionalProperties=False,
                      properties=dict(claims=dict(type='array', maxItems=8, items=dict(
                          type='object', required=['kind', 'text', 'source_refs'], additionalProperties=False,
                          properties=dict(kind=dict(type='string', enum=sorted(TYPES)),
                                          text=dict(type='string', minLength=1, maxLength=4000),
                                          source_refs=dict(type='array', minItems=1, maxItems=16,
                                                           items=dict(type='string', enum=[r['id'] for r in admitted])))))))
        value = calls.json([dict(role='user', content=json.dumps(dict(
            instruction='Prepare up to eight reusable challenge claims. Use exactly the enumerated kinds and supplied evidence IDs. Preserve uncertainty; use kind=check for check-related claims. Never claim an unexecuted check passed. Follow the supplied JSON schema exactly.',
            repository=self.repository, revision=revision, evidence=admitted)))],
            'challenge_graph_preparation_v2', schema)
        claims = value.get('claims')
        if not isinstance(claims, list) or len(claims) > 8:
            raise ValueError('Invalid claim response; no repair retry')
        # Validate every response before the first graph write.
        allowed = {r['id'] for r in admitted}
        for c in claims:
            if c.get('kind') not in TYPES or not c.get('source_refs') or not set(c['source_refs']) <= allowed or not isinstance(c.get('text'), str) or not 1 <= len(c['text']) <= 4000:
                raise ValueError('Invalid or foreign claim; no partial response admission')
        return [self.add(c['kind'], c['text'], c['source_refs'], revision) for c in claims]
