#!/usr/bin/env python3
"""Read-only retrospective coverage audit of the already-vendored transforms.

Retained output bytes are not model tokens. Repeated historical presentations
and unique outputs are reported separately. No model calls or source writes.
"""
import argparse
import collections
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sqlite3

from workspace import bridge
from live_compression import transform_text


def audit(database, cutoff):
    with sqlite3.connect(database.resolve().as_uri() + '?mode=ro', uri=True) as connection:
        connection.row_factory = sqlite3.Row
        events = {r['id']: dict(r) for r in connection.execute(
            "SELECT * FROM events WHERE kind='tool' AND ts<=?", (cutoff,))}
        paths = [Path(r['path']) for r in connection.execute('SELECT path FROM files')]
        assigned = {r['session_id'] + ':' + r['turn_id']: r['title'] for r in connection.execute(
            'SELECT a.session_id,a.turn_id,t.title FROM assignments a JOIN tasks t ON t.id=a.task_id')}
    rows, contents, seen = [], {}, set()
    for path in paths:
        meta = None
        for line, record in bridge.monitor.lines(path):
            if not record:
                continue
            payload = record.get('payload') or {}
            if record.get('type') == 'session_meta':
                meta = payload
            if not meta or record.get('type') != 'event_msg' or payload.get('type') != 'item_completed':
                continue
            item = payload.get('item') or {}
            ident = str(meta.get('id')) + ':tool:' + str(item.get('id'))
            if ident not in events or ident in seen:
                continue
            seen.add(ident)
            text = item.get('aggregated_output')
            if not isinstance(text, str):
                continue
            digest = hashlib.sha256(text.encode()).hexdigest()
            if digest not in contents:
                transformed, change = transform_text(text, 'headroom-lossless')
                contents[digest] = dict(source_sha256=digest, original_bytes=len(text.encode()),
                    forwarded_bytes=len(transformed.encode()), transform=change['kind'] if change else None,
                    reversible=change['reversible'] if change else None)
            task = assigned.get(events[ident]['session_id'] + ':' + str(events[ident]['turn_id']))
            # Classification is an interpretation from assigned task names, not a
            # claim that unassigned activity represents ordinary customer work.
            known_trial = bool(task and any(marker in task.lower() for marker in ('progress-replay', 'live-harness', 'usability', 'evaluate measured')))
            rows.append(dict(id=ident, source_sha256=digest, source_line=line,
                native_persistence_truncated='command output truncated for persistence' in text,
                assigned_known_trial=known_trial, **{k: v for k, v in contents[digest].items() if k != 'source_sha256'}))
    counts = collections.Counter(r['source_sha256'] for r in rows)
    def totals(values):
        return dict(outputs=len(values), original_bytes=sum(r['original_bytes'] for r in values),
            transformed_outputs=sum(bool(r['transform']) for r in values),
            forwarded_bytes=sum(r['forwarded_bytes'] for r in values))
    result = dict(at=datetime.now(timezone.utc).isoformat(), cutoff=cutoff,
        scope='Indexed native tool events with retained aggregated_output, before cutoff; excludes opaque MCP result bodies and unavailable source records.',
        indexed_tool_events=len(events), matched_native_items=len(seen),
        unique_outputs=totals(list(contents.values())), event_presentations=totals(rows),
        outside_assigned_known_trials=totals([r for r in rows if not r['assigned_known_trial']]),
        repeated_unique_outputs=sum(n > 1 for n in counts.values()),
        extra_identical_presentations=sum(max(n - 1, 0) for n in counts.values()),
        persistence_truncated_outputs=sum(r['native_persistence_truncated'] for r in rows),
        transforms=dict(collections.Counter(r['transform'] for r in rows if r['transform'])),
        events=rows, limitations=['Retrospective retained bytes, not forwarded model inputs or measured token savings.',
            'Repeated reads may be necessary; do not suppress without freshness and task-quality evidence.',
            'Unassigned activity may include research. The task-name subset is not an ordinary-work control.',
            'Native CLI clipping may precede this retained text; no claim of full stdout coverage.',
            'Existing transform includes Docker transient-line filtering and reversible search/log folds; not all transforms are reversible.'])
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', type=Path, required=True)
    parser.add_argument('--cutoff', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError('Preserve the existing audit; choose a new snapshot path')
    result = audit(args.database, args.cutoff)
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'events'}, indent=2))
