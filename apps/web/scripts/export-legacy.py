#!/usr/bin/env python3
"""Read-only SQLite export. Originals are never migrated in place or modified."""
import argparse, base64, hashlib, json, pathlib, sqlite3, sys
p=argparse.ArgumentParser();p.add_argument('source',type=pathlib.Path);args=p.parse_args()
source=args.source.resolve(strict=True)
if not source.is_file():raise SystemExit('Expected a SQLite file')
def encode(value):
    if isinstance(value,bytes):return {'__base64__':base64.b64encode(value).decode()}
    return value
connection=sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)
connection.execute('PRAGMA query_only=ON');connection.execute('BEGIN')
schema=connection.execute("SELECT name,sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name").fetchall()
print(json.dumps({'type':'manifest','source':str(source),'schema':schema}))
for table,_ in schema:
    quoted='"'+table.replace('"','""')+'"'
    cursor=connection.execute('SELECT * FROM '+quoted);keys=[c[0] for c in cursor.description]
    for index,row in enumerate(cursor):print(json.dumps({'type':'row','table':table,'number':index,'record':{key:encode(value) for key,value in zip(keys,row)}}))
connection.rollback();connection.close()
