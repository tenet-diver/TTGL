#!/usr/bin/env python3
"""Build a read-only Langfuse audit input for unique resumed sessions."""
import argparse,collections,json
from pathlib import Path
KEYS=('input_tokens','cached_input_tokens','output_tokens','total_tokens')
def aggregate(cells):
    grouped={};seen=set()
    for cell in cells:
        sid=cell['session_id'];identity=(cell.get('case'),cell.get('condition'),cell.get('role'))
        if sid not in grouped:grouped[sid]=dict(session_id=sid,identity=identity,usage={k:0 for k in KEYS},native_response_ids=[])
        item=grouped[sid]
        if item['identity']!=identity:raise ValueError('Session crosses condition/case/role')
        ids=cell['native_response_ids']
        if not ids or len(set(ids))!=len(ids) or seen.intersection(ids):raise ValueError('Missing or duplicate native response')
        seen.update(ids);item['native_response_ids']+=ids
        for k in KEYS:item['usage'][k]+=cell['usage'][k]
    return list(grouped.values())
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('destination',type=Path);a=p.parse_args()
    cells=aggregate(json.loads((a.source/'results.json').read_text())['cells'])
    a.destination.mkdir();(a.destination/'results.json').write_text(json.dumps(dict(cells=cells,source=str(a.source.resolve()),note='Aggregate by exact session for read-only reconciliation; never re-ingest or add cumulative CLI snapshots.'),indent=2)+'\n')
    print(json.dumps(dict(sessions=len(cells),unique_responses=sum(len(c['native_response_ids']) for c in cells))))
if __name__=='__main__':main()
