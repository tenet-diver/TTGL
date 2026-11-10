"""Use Codex's supported output-schema option for cheap challenge-graph calls.

No text cleanup, semantic repair, regenerated answer or invocation retry.
The two earlier prompt-only failures remain preserved development evidence.
"""
import json
from repository_memory_native import Calls


class GraphCalls(Calls):
    def command(self, cell):
        cmd = super().command(cell)
        cmd[-1:-1] = ['--output-schema', str(self.schema_path)]
        return cmd

    def json(self, messages, role, schema=None):
        if not schema:
            raise ValueError('Challenge graph requires a native output schema')
        self.schema_path = self.root / ('schema-' + str(len(self.registry) + 1) + '.json')
        with self.schema_path.open('x') as handle:
            json.dump(schema, handle)
        return super().json(messages, role, schema)
