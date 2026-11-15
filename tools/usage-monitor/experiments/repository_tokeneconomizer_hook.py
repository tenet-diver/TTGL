"""Thin semantic adapter for the reviewed TokenEconomizer Codex hooks.

Upstream does not recognize this harness's MCP terminal as a shell, and its
offline reader drops MCP items. Keep original events/usage; derive explicitly
labeled Claude-compatible tool records solely for stock memory mechanisms.
These derived records are not claimed to be Claude or native execution logs.
No upstream source, prompt, detector or threshold is changed. Tool pruning is
proposal-only for the fixed sandbox capability contract, a disclosed adaptation.
"""
import hashlib
import json
import os
from pathlib import Path
import sys
import time

REPO = Path(__file__).resolve().parents[3]
REVIEW = REPO / 'work/security/tokeneconomizer-review-20261109'
TERMINALS = {'mcp__ttgl_task__terminal', 'mcp__ttgl_task.terminal', 'ttgl_task.terminal'}


def bridge_result(value):
    if isinstance(value, str):
        value = json.loads(value)
    if isinstance(value, dict) and 'content' in value:
        texts = [x['text'] for x in value['content'] if x.get('type') == 'text']
        if len(texts) != 1:
            raise ValueError('Ambiguous MCP terminal response')
        value = json.loads(texts[0])
    if not isinstance(value, dict) or value.get('kind') != 'tool_result' or not str(value.get('id', '')).startswith('event_') or type(value.get('exit_code')) is not int:
        raise ValueError('Unrecognized trusted task bridge frame')
    return value


def compatible_records(messages, provenance):
    """Semantic interchange for real historical OpenAI-style calls/results."""
    result, calls = [], set()
    for index, message in enumerate(messages):
        blocks = []
        if message.get('role') == 'assistant':
            for call in message.get('tool_calls') or []:
                function = call.get('function', {})
                args = function.get('arguments')
                args = json.loads(args) if isinstance(args, str) else args
                if not isinstance(args, dict) or not call.get('id'):
                    raise ValueError('Unrecognized historical tool arguments')
                blocks.append(dict(type='tool_use', id=call['id'], name=function['name'], input=args))
                calls.add(call['id'])
            if message.get('content'):
                blocks.append(dict(type='text', text=message['content']))
            kind = 'assistant'
        elif message.get('role') == 'tool' and message.get('tool_call_id') in calls:
            code = message.get('extra', {}).get('returncode')
            if type(code) is not int:
                raise ValueError('Historical command outcome unknown; do not invent success')
            blocks.append(dict(type='tool_result', tool_use_id=message['tool_call_id'],
                               content=message.get('content', ''), is_error=code != 0))
            kind = 'user'
        else:
            continue
        if blocks:
            result.append(dict(type=kind, message=dict(content=blocks),
                               ttgl_derivation=dict(source=provenance, message_index=index,
                                    schema='Claude-compatible semantic interchange; not a Claude execution log')))
    return result


def native_compatible_trace(source, destination):
    output = []
    for index, line in enumerate(Path(source).read_text().splitlines()):
        entry = json.loads(line)
        if entry.get('type') != 'item.completed':
            continue
        item = entry.get('item', {})
        if item.get('type') != 'mcp_tool_call' or item.get('server') != 'ttgl_task' or item.get('tool') != 'terminal':
            continue
        frame = bridge_result(item.get('result'))
        args = item.get('arguments') or {}
        if isinstance(args, str):
            args = json.loads(args)
        provenance = dict(source=str(source), source_item=item['id'], source_line=index,
                          source_kind='Actual Codex MCP terminal; semantic interchange only')
        output += [dict(type='assistant', message=dict(content=[dict(type='tool_use',
            id=item['id'], name='bash', input=args)]), ttgl_derivation=provenance),
            dict(type='user', message=dict(content=[dict(type='tool_result', tool_use_id=item['id'],
                content=frame['stdout'] + frame['stderr'], is_error=frame['exit_code'] != 0)]),
                ttgl_derivation=provenance)]
    with Path(destination).open('x') as handle:
        for entry in output:
            handle.write(json.dumps(entry) + '\n')
    return len(output) // 2


def install_adapter():
    sys.path.insert(0, str(REVIEW / 'source'))
    from tokeneconomizer.plugin import hosts

    class RepositoryCodex(hosts.Codex):
        def tool_call(self, payload):
            name, args, text, code = super().tool_call(payload)
            if name not in TERMINALS:
                return name, args, text, code
            response = payload.get('tool_response')
            if response is not None:
                frame = bridge_result(response)
                text, code = frame['stdout'] + frame['stderr'], frame['exit_code']
            return 'bash', args, text, code

        def mechanism_trace(self, transcript_path, workdir):
            native_path = super().mechanism_trace(transcript_path, workdir)
            if native_path is None:
                return None
            target = Path(workdir) / ('ttgl-semantic-' + str(time.time_ns()) + '.jsonl')
            native_compatible_trace(native_path, target)
            return str(target)

    hosts.HOSTS['codex'] = RepositoryCodex
    return RepositoryCodex


def main():
    receipt = json.loads((REVIEW / 'pre-execution-receipt.json').read_text())
    refresh = json.loads((REPO / 'work/security/repository-memory-20261110/tokeneconomizer-refresh-001.json').read_text())
    if receipt['confirmed_findings'] or refresh['known_findings'] or refresh['current_lookup'].get('vulns'):
        raise ValueError('Confirmed findings block execution')
    for entry in json.loads((REVIEW / 'download-manifest.json').read_text())['files']:
        if hashlib.sha256((REVIEW / 'source' / entry['path']).read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Reviewed upstream source changed')
    install_adapter()
    from tokeneconomizer.plugin.hook import main as upstream
    return upstream(['--host', 'codex'])


if __name__ == '__main__':
    main()
