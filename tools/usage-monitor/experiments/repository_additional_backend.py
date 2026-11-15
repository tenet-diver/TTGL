"""Bounded historical Smallville/TokenEconomizer initialization and retrieval.

Public history only. No target issue enters build, and no hidden grade enters
either phase. Stock algorithms with disclosed coding/transport adapters.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

from repository_memory_native import Calls
from repository_tokeneconomizer_hook import compatible_records, REVIEW

REPO = Path(__file__).resolve().parents[3]
GLOBAL = REPO / 'work/security/context-memory-20261107'


def now():
    # Upstream stores naive timestamps. These represent actual UTC ingestion,
    # never invented historical dates or artificially advanced reflection clocks.
    return datetime.now(timezone.utc).replace(tzinfo=None)


def observations(data):
    events = []
    for episode in data['episodes']:
        calls = {}
        for index, message in enumerate(json.loads(episode['body'])):
            if message.get('role') == 'assistant':
                for call in message.get('tool_calls') or []:
                    args = call['function'].get('arguments')
                    args = json.loads(args) if isinstance(args, str) else args
                    calls[call['id']] = dict(name=call['function']['name'], arguments=args)
            elif message.get('role') == 'tool' and message.get('tool_call_id') in calls:
                content = message.get('content') or ''
                if not isinstance(content, str):
                    raise ValueError('Unsupported historical result text')
                call = calls[message['tool_call_id']]
                events.append(dict(source_episode=episode['id'], source_message_index=index,
                    original_source_sha256=episode['downloaded_source_sha256'],
                    tool=call['name'], arguments_text=json.dumps(call['arguments'])[:2000],
                    visible_output=content[:2500], output_original_characters=len(content),
                    output_view_truncated=len(content) > 2500,
                    observed_command_exit=message.get('extra', {}).get('returncode'),
                    status='Visible historical command evidence, not verified task success'))
    return events


def smallville(root, action, data):
    from smallville_compat_v4 import CompatibleMemoryV4
    from smallville_local_embeddings import LocalEmbeddings
    calls = Calls(root / 'maintenance', cap=256)
    embed = LocalEmbeddings(GLOBAL, root / 'embedding-inferences.jsonl')
    memory = CompatibleMemoryV4(root / 'memory', embed, calls,
        dict(name='TTGL repository agent', currently='Learning fallible procedures from earlier public repository work.'),
        restore_last_access=True)
    before = len(calls.registry)
    if action == 'build':
        events = observations(data)
        selected = events[-64:]
        (root / 'perception-loss.json').write_text(json.dumps(dict(total_events=len(events), selected_events=len(selected),
            max_events=64, rule='Latest64 actual completed tool-result messages in admitted history, original order; args2000/output2500chars; full originals retained',
            literal_encoding='JSON unicode escapes for parentheses avoid upstream human-event parenthesis extraction. JSON decoding restores exact rendered record; no source/prompt parity claim.'), indent=2))
        thoughts = 0
        for event in selected:
            description = json.dumps(event, ensure_ascii=False).replace('(', '\\u0028').replace(')', '\\u0029')
            if json.loads(description) != event:
                raise ValueError('Nonlossless source rendering')
            memory.observe(description, 'TTGL repository agent', 'observed', event['source_episode'], now())
            thoughts += len(memory.reflect_if_due(now()))
        value = dict(observations=len(selected), natural_thoughts=thoughts,
                     importance_remaining=memory.scratch.importance_trigger_curr,
                     forced_reflections=0, native_call_start=before, native_call_end=len(calls.registry))
    else:
        hits = memory.retrieve(data['query'], now(), 8)
        value = dict(hits=[dict(id=n.node_id, kind=n.type, text=n.embedding_key,
                               evidence=n.filling, importance=n.poignancy) for n in hits],
                     native_call_start=before, native_call_end=len(calls.registry))
    memory.checkpoint()
    return value


def tokeneconomizer(root, action, data):
    import sys
    for entry in json.loads((REVIEW / 'download-manifest.json').read_text())['files']:
        if hashlib.sha256((REVIEW / 'source' / entry['path']).read_bytes()).hexdigest() != entry['sha256']:
            raise ValueError('Reviewed source changed')
    sys.path.insert(0, str(REVIEW / 'source'))
    from tokeneconomizer.config import InjectionConfig
    from tokeneconomizer.microskills import PrefixStage
    from native_jsonl import records
    calls = Calls(root / 'maintenance', cap=32)
    def runner(prompt, model):
        if model != 'gpt-6-luna':
            raise ValueError('Unregistered optimizer model')
        text = calls(prompt, 'tokeneconomizer_stock_proposer')
        cell = calls.root / calls.registry[-1]['cell']
        usage = next(r['usage'] for r in records(cell) if r.get('type') == 'turn.completed')
        # Internal upstream token tally only. Actual economics uses reconciled
        # per-response counters; never treat this count as cash or inferred cost.
        return text, usage['input_tokens'] + usage['output_tokens']
    cfg = InjectionConfig(enabled=True, profile='envfacts+distiller', propose_every=3,
                          max_facts=4, max_tokens=150)
    stage = PrefixStage(cfg, data['repository'], str(root / 'mechanisms'), action == 'build',
                        runner=runner, optimizer_model='gpt-6-luna')
    before = len(calls.registry)
    if action == 'build':
        # Validate every interchange before the first potentially paid update.
        rows = [(episode, compatible_records(json.loads(episode['body']), episode['downloaded_source_sha256']))
                for episode in data['episodes']]
        updates = []
        for episode, messages in rows:
            run = root / 'derived-history' / episode['id']
            run.mkdir(parents=True, exist_ok=False)
            with (run / 'transcript.jsonl').open('x') as handle:
                for message in messages:
                    handle.write(json.dumps(message) + '\n')
            srow = {}  # Deliberately no resolved/hidden-grade label.
            stage.after_task(dict(instance_id=episode['id']), {}, str(run), srow)
            updates.append(dict(source_episode=episode['id'], derived_records=len(messages), telemetry=srow))
        value = dict(updates=updates, native_call_start=before, native_call_end=len(calls.registry),
                     settings=dict(profile='envfacts+distiller', propose_every=3, max_facts=4, max_tokens=150),
                     no_hidden_resolution_labels=True)
    else:
        text = stage.render(dict(instance_id='current-public-task', problem_statement=data['query']))
        value = dict(hits=[dict(kind='stock_micro_skills', text=text)] if text else [],
                     injected_ids=stage.injected_ids(), native_call_start=before, native_call_end=len(calls.registry))
    return value


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('backend', choices=['smallville', 'tokeneconomizer'])
    parser.add_argument('action', choices=['build', 'query'])
    parser.add_argument('root', type=Path)
    parser.add_argument('input', type=Path)
    args = parser.parse_args()
    args.root.mkdir(parents=True, exist_ok=args.action != 'build')
    data = json.loads(args.input.read_text())
    output = args.root / (args.action + '-started.json')
    with output.open('x') as handle:
        json.dump(dict(at=datetime.now(timezone.utc).isoformat(), no_retry=True), handle)
    try:
        value = globals()[args.backend](args.root, args.action, data)
        with (args.root / (args.action + '-complete.json')).open('x') as handle:
            json.dump(value, handle, indent=2)
        print(args.backend, args.action, 'complete', flush=True)
    except BaseException as error:
        with (args.root / (args.action + '-stopped.json')).open('x') as handle:
            json.dump(dict(error=str(error), no_retry=True), handle)
        raise
