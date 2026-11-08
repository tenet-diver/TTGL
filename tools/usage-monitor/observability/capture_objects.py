"""Private SQLite/gzip storage for repeated redacted request objects.

This changes capture storage only, never model requests. SQLite supplies the
durable transactions; this glue splits repeated history items into hashed blobs.
Original wire hashes remain separate: redacted JSON is not exact wire evidence.
"""
import gzip
import hashlib
import io
import json
from pathlib import Path
import re
import sqlite3

MAX_OBJECT = 32*1024*1024


class CaptureObjects:
    def __init__(self, path):
        self.path=Path(path)

    def connect(self):
        db=sqlite3.connect(self.path,timeout=30)
        db.execute('PRAGMA journal_mode=WAL')
        db.execute('PRAGMA synchronous=FULL')
        version=db.execute('PRAGMA user_version').fetchone()[0]
        if version not in (0,1):
            db.close()
            raise ValueError('Unsupported private capture object schema')
        db.execute('CREATE TABLE IF NOT EXISTS objects(digest TEXT PRIMARY KEY, payload BLOB NOT NULL)')
        db.execute('PRAGMA user_version=1')
        return db

    @staticmethod
    def get(digest, db):
        if not isinstance(digest,str) or not re.fullmatch('[0-9a-f]{64}',digest):
            raise ValueError('Invalid capture object digest')
        row=db.execute('SELECT payload FROM objects WHERE digest=?',(digest,)).fetchone()
        if row is None:
            raise ValueError('Missing capture object')
        with gzip.GzipFile(fileobj=io.BytesIO(row[0])) as stream:
            raw=stream.read(MAX_OBJECT+1)
        if len(raw)>MAX_OBJECT or hashlib.sha256(raw).hexdigest()!=digest:
            raise ValueError('Corrupt or oversized capture object')
        return json.loads(raw)

    def put(self, value, db):
        raw=json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
        if len(raw)>MAX_OBJECT:
            raise ValueError('Capture object exceeds retention bound')
        digest=hashlib.sha256(raw).hexdigest()
        db.execute('INSERT OR IGNORE INTO objects(digest,payload) VALUES(?,?)',
                   (digest,gzip.compress(raw,compresslevel=1,mtime=0)))
        # Existing entries must still be intact; never silently replace evidence.
        if self.get(digest,db)!=value:
            raise ValueError('Capture object round trip mismatch')
        return digest

    def pack(self, value, db):
        if not isinstance(value,dict):
            return dict(layout='ttgl-cas-value-v1',value=self.put(value,db))
        fields=[]
        for key,item in value.items():
            descriptor={'items':[self.put(v,db) for v in item]} if key=='input' and isinstance(item,list) else {'value':self.put(item,db)}
            fields.append([key,descriptor])
        return dict(layout='ttgl-cas-fields-v1',fields=fields)

    def unpack(self, value, db):
        if value.get('layout')=='ttgl-cas-value-v1':
            return self.get(value['value'],db)
        if value.get('layout')!='ttgl-cas-fields-v1':
            raise ValueError('Unsupported capture layout')
        result={}
        for key,descriptor in value['fields']:
            if key in result:
                raise ValueError('Duplicate capture field')
            result[key]=[self.get(d,db) for d in descriptor['items']] if 'items' in descriptor else self.get(descriptor['value'],db)
        return result


def read_capture(path):
    path=Path(path)
    record=json.loads(path.read_text())
    if record.get('capture_content_layout')!='sqlite-cas-json-v1':
        return record
    directory=path.parent.parent if path.parent.name in ('pending','rejections') else path.parent
    store=CaptureObjects(directory/'capture-objects.sqlite')
    # Read-only decoding must never create or migrate a missing database.
    db=sqlite3.connect(store.path.resolve().as_uri()+'?mode=ro',uri=True)
    try:
        for key in ('request','forwarded_request','response'):
            if key in record:
                record[key]=store.unpack(record[key],db)
    finally:
        db.close()
    return record
