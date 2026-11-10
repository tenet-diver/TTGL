"""Real maintained MCP persistence/tool checks; no model or Docker calls."""
import json
from pathlib import Path
import tempfile
import time
import unittest

from online_task_memory import OnlineMemory
from repository_challenge_graph import ChallengeGraph
from repository_challenge_bridge import GraphBridge


class GraphPolicyChecks(unittest.TestCase):
    def test_namespace_and_versioned_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            ledger = OnlineMemory(root / 'ledger.sqlite')
            source = ledger.append('instruction', 'Public source says use python -m pytest.')
            graph = ChallengeGraph(root / 'graph', ledger, 'fixture/repo')
            try:
                first = graph.add('procedure', 'Source documents pytest; execution unobserved.', [source['id']], 'base1')
                second = graph.add('hypothesis', 'Recheck pytest at the new revision.', [source['id']], 'base2', supersedes=first['id'])
                hits = graph.search('pytest')['hits']
                self.assertEqual([n['name'] for n in hits], [second['id']])
                self.assertEqual(len(graph.snapshot()['entities']), 2)
                with self.assertRaises(ValueError):
                    graph.add('check', 'Unsupported success claim', ['foreign'], 'base2')
                self.assertEqual(ledger.read(source['id'])['body'], 'Public source says use python -m pytest.')
            finally:
                graph.close()
            with self.assertRaises(ValueError):
                ChallengeGraph(root / 'graph', ledger, 'foreign/repo')
            reopened = ChallengeGraph(root / 'graph', ledger, 'fixture/repo')
            try:
                self.assertEqual(len(reopened.snapshot()['entities']), 2)
            finally:
                reopened.close()

    def test_graph_tools_use_common_budget_and_preserve_sources(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            config = dict(records=str(root / 'records'), phase_directory=str(root / 'phase'),
                          mode='files', container='never-used', instruction='Common public instructions',
                          tool_budget=2, close_at_ns=time.time_ns() + 30 * 10**9,
                          graph_root=str(root / 'graph'), repository='fixture/repo', revision='base')
            path = root / 'server.json'
            path.write_text(json.dumps(config))
            bridge = GraphBridge(path)
            source = bridge.memory.append('instruction', 'Observed command was unavailable.')
            def invoke(ident, name, args):
                result = bridge.handle(dict(id=ident, method='tools/call', params=dict(name=name, arguments=args)))
                self.assertFalse(result['isError'])
                return json.loads(result['content'][0]['text'])
            try:
                node = invoke(1, 'graph_claim', dict(kind='observation', text='Command was unavailable; environment may change.', source_refs=[source['id']]))
                self.assertTrue(node['id'].startswith('claim_'))
                hits = invoke(2, 'search_graph', dict(query='command unavailable'))
                self.assertEqual(len(hits['hits']), 1)
                closed = invoke(3, 'search_graph', dict(query='command unavailable'))
                self.assertTrue(closed['phase_tools_closed'])
                self.assertEqual(bridge.memory.read(source['id'])['body'], 'Observed command was unavailable.')
            finally:
                bridge.graph.close()


if __name__ == '__main__':
    unittest.main()
