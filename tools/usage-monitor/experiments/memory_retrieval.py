#!/usr/bin/env python3
"""SQLite FTS5 research control over explicitly supplied chronological episodes.

Not a replacement for Mem0/Graphiti. No embeddings, models, network or packages.
The frozen corpus contains only this arm's earlier public agent episodes.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import sqlite3
import time


def search(episodes, query, limit=3, budget=12000):
    terms = list(dict.fromkeys(re.findall(r'[\w]+', query)))[:24]
    if not terms:
        return []
    with sqlite3.connect(':memory:') as db:
        db.execute('CREATE VIRTUAL TABLE memory USING fts5(body, episode UNINDEXED, chunk UNINDEXED)')
        for episode in episodes:
            # Nonoverlapping exact chunks; no text dropped or generated summaries.
            text = episode['body']
            for offset in range(0, len(text), 3000):
                db.execute('INSERT INTO memory VALUES(?,?,?)',
                           (text[offset:offset+3000], episode['id'], offset))
        expression = ' OR '.join('"' + t.replace('"', '""') + '"' for t in terms)
        rows = db.execute('SELECT body,episode,chunk,bm25(memory) FROM memory WHERE memory MATCH ? ORDER BY bm25(memory),episode,chunk LIMIT ?',
                          (expression, min(max(int(limit), 1), 10))).fetchall()
    result, used = [], 0
    for body, episode, offset, score in rows:
        if used + len(body) > budget:
            continue
        result.append(dict(episode=episode, offset=offset, body=body, score=score,
                           sha256=hashlib.sha256(body.encode()).hexdigest()))
        used += len(body)
    return result


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('query')
    p.add_argument('--limit', type=int, default=3)
    args = p.parse_args()
    root = Path(__file__).resolve().parent
    corpus = json.loads((root / 'memory-corpus.json').read_text())
    start = time.perf_counter()
    result = search(corpus['episodes'], args.query, args.limit)
    record = dict(query=args.query, results=result, elapsed_seconds=time.perf_counter()-start,
                  corpus_sha256=hashlib.sha256((root/'memory-corpus.json').read_bytes()).hexdigest())
    with (root/'memory-queries.jsonl').open('a') as f:
        f.write(json.dumps(record)+'\n')
    print(json.dumps(dict(results=result, note='Prior visible episodes are fallible evidence. Verify against current source.')))


if __name__ == '__main__':
    main()
