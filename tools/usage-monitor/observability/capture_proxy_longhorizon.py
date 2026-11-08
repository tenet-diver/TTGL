#!/usr/bin/env python3
"""Capture-only long-horizon adapter using existing HTTP code and SQLite/gzip.

Normal proxies and frozen source remain unchanged. Redacted decoded bodies are
retained without the old262144-character string clip; opaque reasoning is omitted.
No context transformation route is enabled by this storage-readiness version.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import tempfile
import time
import types
import uuid
from capture_objects import CaptureObjects

spec=importlib.util.spec_from_file_location('ttgl_long_private_proxy',Path(__file__).with_name('capture_proxy_compaction.py'))
base=importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
base.MAX_BODY=16*1024*1024
base.MAX_CAPTURE=4*1024*1024
base.DEFAULTS['ports']['capture']=8336
base.DEFAULTS['capture']['retained_capture_quota_bytes']=512*1024*1024
# Reuse the exact existing redaction function with an isolated globals dictionary.
# Other services/tests keep their original limit and globals.
base.safe_content=types.FunctionType(base.safe_content.__code__,
    {**base.safe_content.__globals__,'LIMIT':base.MAX_BODY},'safe_content')
original_sanitized=base.sanitized


def sanitized(value):
    if isinstance(value,dict):
        value={k:'[OMITTED]' if k.lower() in ('password','secret_key','client_secret','signing_key') else v for k,v in value.items()}
    return original_sanitized(value)


base.sanitized=sanitized


class Handler(base.Handler):
    def proxy(self):
        self.ingress_id=uuid.uuid4().hex
        self.accepted=False
        if self.path.startswith('/compress/'):
            return self.error(404,'This capture-only version does not enable context transformations')
        size=0
        for path in self.server.destination.rglob('*'):
            try:
                if path.is_file():size+=path.stat().st_size
            except FileNotFoundError:
                pass  # A completed SQLite connection may remove its WAL/shm file.
        if size>512*1024*1024 or shutil.disk_usage(self.server.destination).free<576*1024*1024:
            return self.error(507,'Private capture quota or free-space reserve reached before upstream submission')
        return super().proxy()

    def error(self,code,message):
        self.persist(dict(id=uuid.uuid4().hex,state='rejected',status=code,
            path=base.safe_content(self.path)[0],method=self.command,ended_ns=time.time_ns(),
            event_type='http_error',reason=message,
            upstream_submission='not_attempted' if not getattr(self,'accepted',False) else 'attempted_or_unknown',
            headers_persisted=False))
        return super().error(code,message)

    def persist(self,record):
        self.accepted=self.accepted or record.get('state')=='pending'
        record={**record,'capture_schema':4,'capture_content_layout':'sqlite-cas-json-v1',
                'ingress_id':self.ingress_id,'content_scope':'Decoded redacted JSON; opaque protocol fields omitted. Original wire hashes are separate.'}
        store=CaptureObjects(self.server.destination/'capture-objects.sqlite')
        db=store.connect()
        try:
            with db:
                for key in ('request','forwarded_request','response'):
                    if key in record:
                        record[key]=store.pack(record[key],db)
        finally:
            db.close()
        folder=self.server.destination
        if record['state'] in ('pending','rejected'):
            folder=folder/('pending' if record['state']=='pending' else 'rejections')
        folder.mkdir(mode=0o700,parents=True,exist_ok=True)
        fd,temporary=tempfile.mkstemp(dir=folder,prefix=record['id']+'.',suffix='.tmp')
        target=folder/(record['id']+'.json')
        try:
            with os.fdopen(fd,'w') as stream:
                json.dump(record,stream,ensure_ascii=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.link(temporary,target)
            directory=os.open(folder,os.O_RDONLY)
            try:os.fsync(directory)
            finally:os.close(directory)
        finally:
            Path(temporary).unlink(missing_ok=True)


base.Handler=Handler


if __name__=='__main__':
    base.main()
