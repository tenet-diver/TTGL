#!/usr/bin/env python3
"""Create native Langfuse widgets for the direct Codex transcript exporter."""
import argparse
import base64
import json
from pathlib import Path
import urllib.request


def configure(credentials, state):
    c = json.loads(credentials.read_text())
    if c['base_url'] not in ('http://localhost:3000', 'http://127.0.0.1:3000'):
        raise ValueError('Expected local Langfuse')
    auth = base64.b64encode((c['public_key'] + ':' + c['secret_key']).encode()).decode()
    def api(path, data, method='POST'):
        request = urllib.request.Request(c['base_url'] + path, data=json.dumps(data).encode(), method=method,
            headers={'Authorization': 'Basic ' + auth, 'Content-Type': 'application/json'})
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    cache = json.loads(state.read_text()) if state.exists() else {}
    if 'dashboard' not in cache:
        cache['dashboard'] = api('/api/public/unstable/dashboards', dict(name='Codex: Tokens and Runtime',
            description='Native transcripts. Model latency and actual charges unknown.', definition={'widgets': []}, filters=[]))['id']
        state.write_text(json.dumps(cache))
    common = [dict(column='environment', operator='=', type='string', value='codex-native')]
    generation = common + [dict(column='type', operator='any of', type='stringOptions', value=['GENERATION'])]
    tools = common + [dict(column='type', operator='any of', type='stringOptions', value=['TOOL'])]
    timed = tools + [dict(column='metadata', key='native_runtime_known', operator='=', type='stringObject', value='true')]
    transport = [dict(column='environment', operator='=', type='string', value='codex-transport'),
                 dict(column='name', operator='=', type='string', value='Codex model request / response')]
    definitions = [
        ('Measured token buckets', 'usageType', 'usageByType', 'sum', 'HORIZONTAL_BAR', generation,
         'Cached input is separate from fresh input. Total is a reference, not an additional bucket.'),
        ('Tokens by model', 'providedModelName', 'totalTokens', 'sum', 'HORIZONTAL_BAR', generation,
         'Deduplicated measured response usage. Repeated context is counted on each model call.'),
        ('Model responses over time', 'providedModelName', 'count', 'count', 'LINE_TIME_SERIES', generation,
         'Response completions from native transcripts; not wire attempts or retries.'),
        ('Tool frequency by operation', 'name', 'count', 'count', 'HORIZONTAL_BAR', tools,
         'Native completions only. Tool runtime and model tokens are separate measurements.'),
        ('Native tool runtime distribution', 'name', 'latency', 'p50', 'PIVOT_TABLE', timed,
         'Native item.duration only. Parallel operations overlap; sums are not task elapsed time. Unknown runtimes excluded.'),
        ('API-equivalent model cost', 'providedModelName', 'totalCost', 'sum', 'HORIZONTAL_BAR', generation,
         'Langfuse model-price scenarios where available. Not subscription cash expense; missing price means unknown.'),
        ('Captured HTTP request duration', 'name', 'latency', 'p50', 'PIVOT_TABLE', transport,
         'Explicitly proxied model HTTP exchanges only. Includes transport and streaming; not pure inference time. Native usage is counted separately.'),
        ('Captured HTTP requests over time', 'name', 'count', 'count', 'LINE_TIME_SERIES', transport,
         'Captured exchanges only. Existing sessions do not retroactively route through the proxy. No token usage is added from these records.'),
    ]
    placements = []
    for index, (name, dimension, measure, aggregate, chart, filters, description) in enumerate(definitions):
        definition = dict(name=name, description=description, view='observations', dimensions=[{'field': dimension}],
            metrics=[dict(measure=measure, agg=aggregate)], filters=filters, chartType=chart, chartConfig={'row_limit': 20})
        if chart == 'PIVOT_TABLE':
            definition['metrics'] = [dict(measure='count', agg='count')] + [dict(measure='latency', agg=agg) for agg in ('p50', 'p95', 'p99', 'max')]
        if name in cache:
            widget = api('/api/public/unstable/dashboard-widgets/' + cache[name], definition, 'PATCH')
        else:
            widget = api('/api/public/unstable/dashboard-widgets', definition)
            cache[name] = widget['id']
            state.write_text(json.dumps(cache))
        placements.append(dict(id='native-' + str(index), type='widget', widgetId=widget['id'],
                               x=(index % 2) * 6, y=(index // 2) * 7, width=6, height=7))
    api('/api/public/unstable/dashboards/' + cache['dashboard'], dict(name='Codex: Tokens and Runtime',
        description='Real native Codex records. Model latency, raw wire captures, cash charges and task success remain unknown.',
        definition={'widgets': placements}, filters=[]), 'PATCH')
    print('/project/' + c['project_id'] + '/dashboards/' + cache['dashboard'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--credentials', type=Path, required=True)
    parser.add_argument('--state', type=Path, required=True)
    args = parser.parse_args()
    configure(args.credentials, args.state)
