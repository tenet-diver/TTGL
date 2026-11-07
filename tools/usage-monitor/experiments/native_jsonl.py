"""Strict physical-newline JSONL parsing; Unicode separators belong inside strings."""
import json


def records(cell):
    return [json.loads(line) for line in (cell/'agent.jsonl').read_bytes().split(b'\n') if line.startswith(b'{')]


def validate_native_completion(cell,no_tools=False):
    rows=records(cell);done=[r for r in rows if r.get('type')=='turn.completed'];ids=[r['thread_id'] for r in rows if r.get('type')=='thread.started']
    if len(done)!=1 or len(ids)!=1 or not done[0].get('usage',{}).get('input_tokens') or any(r.get('type')=='turn.failed' for r in rows):raise ValueError('Ambiguous completion or missing usage')
    if no_tools and any(r.get('type')=='item.completed' and r.get('item',{}).get('type') not in ('agent_message','reasoning') for r in rows):raise ValueError('Forbidden judge tools')
    return ids[0]


def meter_cell(store,cell,sid,metadata,rates):
    from cost_context_study import price
    with store.connection() as db:
        rows=[dict(r) for r in db.execute("SELECT * FROM events WHERE session_id=? AND kind='generation'",(sid,))]
    for row in rows:row['usage']=json.loads(row['usage'])
    usage={k:sum(r['usage'].get(k,0) for r in rows) for k in ('input_tokens','cached_input_tokens','output_tokens','total_tokens')}
    cli=next(r['usage'] for r in records(cell) if r.get('type')=='turn.completed')
    if not rows or any(usage[k]!=cli[k] for k in ('input_tokens','cached_input_tokens','output_tokens')):raise ValueError('Native/CLI mismatch')
    return dict(metadata,session_id=sid,usage=usage,native_reconciled=True,native_response_ids=[r['id'] for r in rows],cost=sum(price(r['usage'],rates) for r in rows))
