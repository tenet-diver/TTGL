"""Team-scoped evidence journal using SQLite FTS5, with optional existing engines.

This is integration glue, not a replacement memory algorithm. Original submitted
records remain authoritative alongside fallible engine-generated memories. One
broker serializes engine calls for all native parents/children in an assignment.
"""
import hashlib
from contextlib import contextmanager
import json
from pathlib import Path
import re
import sqlite3
import time


class Journal:
    def __init__(self, path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
        with self.connect() as db:
            db.execute('CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, author TEXT, kind TEXT, body TEXT, source TEXT, created_ns INTEGER)')
            db.execute("CREATE VIRTUAL TABLE IF NOT EXISTS records_fts USING fts5(id UNINDEXED,body,author,kind)")

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.path, timeout=30)
        db.row_factory = sqlite3.Row
        try:
            with db:
                yield db
        finally:
            db.close()

    def add(self, author, kind, body, source, ident=None):
        if not all(isinstance(x, str) for x in (author, kind, body, source)):
            raise ValueError('Text fields required')
        if not 0 < len(body) <= 60000 or len(author) > 200 or len(source) > 1000:
            raise ValueError('Record exceeds registered bounds')
        ident = ident or hashlib.sha256(json.dumps([author, kind, body, source], ensure_ascii=False).encode()).hexdigest()
        with self.connect() as db:
            prior = db.execute('SELECT * FROM records WHERE id=?', (ident,)).fetchone()
            if prior:
                if (prior['author'], prior['kind'], prior['body'], prior['source']) != (author, kind, body, source):
                    raise ValueError('Evidence identity collision')
                return dict(prior)
            db.execute('INSERT INTO records VALUES(?,?,?,?,?,?)', (ident, author, kind, body, source, time.time_ns()))
            db.execute('INSERT INTO records_fts VALUES(?,?,?,?)', (ident, body, author, kind))
            return dict(db.execute('SELECT * FROM records WHERE id=?', (ident,)).fetchone())

    def get(self, ident, offset=0, limit=8000):
        if type(offset) is not int or offset < 0 or type(limit) is not int or not 1 <= limit <= 16000:
            raise ValueError('Invalid paging')
        with self.connect() as db:
            row = db.execute('SELECT * FROM records WHERE id=?', (ident,)).fetchone()
        if row is None:
            raise ValueError('Unknown record in this assignment')
        value = dict(row)
        body = value.pop('body')
        value.update(body=body[offset:offset+limit], characters=len(body), offset=offset,
                     next_offset=offset+limit if offset+limit < len(body) else None,
                     sha256=hashlib.sha256(body.encode()).hexdigest())
        return value

    def search(self, query, limit=8):
        if not isinstance(query, str) or not 0 < len(query) <= 2000 or type(limit) is not int or not 1 <= limit <= 20:
            raise ValueError('Invalid search')
        words = re.findall(r'\w+', query, flags=re.UNICODE)[:32]
        if not words:
            return []
        # Natural language is data; do not accept arbitrary FTS operators.
        expression = ' OR '.join('"' + w.replace('"', '""') + '"' for w in words)
        with self.connect() as db:
            rows = db.execute('SELECT r.*,bm25(records_fts) AS rank FROM records_fts JOIN records r ON r.id=records_fts.id WHERE records_fts MATCH ? ORDER BY rank,r.created_ns,r.id LIMIT ?', (expression, limit)).fetchall()
        return [dict(id=r['id'], author=r['author'], kind=r['kind'], source=r['source'],
                     preview=r['body'][:1600], characters=len(r['body'])) for r in rows]


def public_item(message):
    """Allowlist visible completed items; never expose reasoning/opaque state.

    The source RPC is private and unchanged. No arbitrary directory/log search,
    grader record, system prompt, auth or historical session is ingested.
    """
    if message.get('method') != 'item/completed':
        return None
    p = message.get('params', {})
    item = p.get('item', {})
    kind = item.get('type')
    if kind == 'agentMessage':
        body = item.get('text')
    elif kind == 'userMessage':
        body = '\n'.join(x['text'] for x in item.get('content', []) if x.get('type') == 'text' and isinstance(x.get('text'), str))
    elif kind == 'mcpToolCall':
        # Do not recursively ingest memory retrievals or memory calls themselves.
        if item.get('server') != 'repository':
            return None
        body = json.dumps({k: item[k] for k in ('server', 'tool', 'arguments', 'result', 'error') if k in item}, ensure_ascii=False)
    elif kind == 'commandExecution':
        body = json.dumps({k:item[k] for k in ('command','aggregatedOutput','exitCode','status') if k in item},ensure_ascii=False)
    elif kind in ('collabAgentToolCall', 'collabAgentSpawnToolCall', 'collabAgentInteractionToolCall', 'collabAgentSendMessageToolCall'):
        body = json.dumps({k: item[k] for k in ('tool', 'prompt', 'message', 'receiverThreadIds', 'senderThreadId', 'status') if k in item}, ensure_ascii=False)
    else:
        return None
    if not isinstance(body, str) or not body.strip():
        return None
    return dict(author=p.get('threadId', 'unattributed'), kind=kind, body=body,
                source='rpc:item/' + str(item.get('id', 'unidentified')))
