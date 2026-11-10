"""Graph tools through the existing metered, no-replay task RPC boundary."""
import json

import task_terminal_mcp_v2 as base
from repository_task_bridge import RepositoryBridge
from repository_challenge_graph import ChallengeGraph

GRAPH_TOOLS = [
    base.tool('graph_claim', 'Add a fallible evidence-linked graph claim or a new version. Old claims and raw evidence are retained. A claim is not verified by assertion.', dict(
        kind=dict(type='string', enum=['requirement', 'component', 'hypothesis', 'observation', 'procedure', 'check']),
        text=dict(type='string'), source_refs=dict(type='array', items=dict(type='string')),
        supersedes=dict(type='string'), related=dict(type='array', items=dict(type='string'))), ('kind', 'text', 'source_refs')),
    base.tool('search_graph', 'Search active fallible graph claims and their one-hop relationships. Verify relevance to the current revision and read source evidence.', dict(query=dict(type='string'), limit=dict(type='integer', minimum=1, maximum=8)), ('query',)),
]


class GraphMemory:
    def __init__(self, ledger, graph, revision):
        self.ledger, self.graph, self.revision = ledger, graph, revision

    def __getattr__(self, name):
        return getattr(self.ledger, name)

    def append(self, kind, body, refs=(), supersedes=(), record_id=None):
        if kind == 'agent_note' and body.startswith('{"ttgl_graph_claim":'):
            payload = json.loads(body)['ttgl_graph_claim']
            try:
                return self.graph.add(payload['kind'], payload['text'], refs, self.revision,
                                      payload.get('supersedes'), payload.get('related', []))
            except Exception as error:
                raise RuntimeError('Graph operation may have started; preserve and stop: ' + str(error)) from error
        return self.ledger.append(kind, body, refs, supersedes, record_id)

    def search(self, query, limit=8, budget=12000):
        if query.startswith('ttgl_graph_query:'):
            return self.graph.search(query.split(':', 1)[1], limit, budget)
        return self.ledger.search(query, limit, budget)


class GraphBridge(RepositoryBridge):
    def __init__(self, config):
        super().__init__(config)
        ledger = self.memory
        self.graph = ChallengeGraph(self.config['graph_root'], ledger, self.config['repository'])
        self.memory = GraphMemory(ledger, self.graph, self.config['revision'])

    def handle(self, request):
        if request.get('method') == 'tools/list':
            return dict(tools=base.TOOLS + GRAPH_TOOLS)
        if request.get('method') == 'tools/call':
            params = request.get('params', {})
            name, args = params.get('name'), params.get('arguments', {})
            definition = next((t for t in GRAPH_TOOLS if t['name'] == name), None)
            if definition:
                schema = definition['inputSchema']
                if not isinstance(args, dict) or set(args) - set(schema['properties']) or any(k not in args for k in schema['required']):
                    return dict(isError=True, content=[dict(type='text', text='Invalid graph arguments')])
                if name == 'graph_claim':
                    translated = dict(name='remember', arguments=dict(
                        text=json.dumps({'ttgl_graph_claim': args}), source_refs=args['source_refs']))
                else:
                    translated = dict(name='search_records', arguments=dict(
                        query='ttgl_graph_query:' + args['query'], limit=args.get('limit', 8)))
                request = dict(request, params=translated)
        return super().handle(request)


if __name__ == '__main__':
    base.TaskBridge = GraphBridge
    base.main()
