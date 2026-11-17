"""Versioned literal-loopback service client. No request/model automatic retries."""
from __future__ import annotations
import base64
import hashlib
import json
import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, build_opener, HTTPRedirectHandler
from .io import canonical, file_digest, digest


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, *args, **kwargs):
        raise ValueError('Experience service redirects are disabled')


class ExperienceClient:
    def __init__(self, project, experiment, endpoint='http://127.0.0.1:3333/api/experience', token=None, timeout=60):
        u = urlparse(endpoint)
        if u.scheme not in ('http','https') or u.hostname not in ('127.0.0.1','::1') or u.username or u.password or u.query or u.fragment or u.path != '/api/experience':
            raise ValueError('Experience service must use a literal-loopback endpoint')
        self.scope = {'projectId':project,'experimentId':experiment}
        self.endpoint, self.timeout = endpoint, timeout
        self.token = token if token is not None else os.environ.get('OBS_EXPERIENCE_TOKEN')
        if not self.token:
            raise ValueError('Source-local experience service token required')
        self.opener = build_opener(NoRedirect())

    def call(self, operation, payload):
        body = canonical({'apiVersion':1, **self.scope,'operation':operation,'payload':payload}).encode()
        if len(body)>2_000_000:
            raise ValueError('Bounded service request exceeds 2 MB')
        request = Request(self.endpoint, data=body, headers={'Authorization':'Bearer '+self.token,'Content-Type':'application/json'})
        with self.opener.open(request, timeout=self.timeout) as response:
            result = json.load(response)
        if result.get('apiVersion') != 1:
            raise ValueError('Unknown experience API version')
        return result['result']

    def search(self, query):
        return self.call('search',query)

    def read(self, query, version_ids):
        return self.call('read',{'query':query,'versionIds':version_ids})

    def record(self, kind, value):
        return self.call(kind,value)

    def retain_file(self, path, *, kind, identity):
        path = Path(path)
        parts = []
        with path.open('rb') as source:
            while chunk := source.read(700_000):
                part = self.call('artifact',{'identity':identity+':'+str(len(parts)), 'kind':kind,
                    'base64':base64.b64encode(chunk).decode(),'sha256':hashlib.sha256(chunk).hexdigest()})
                parts.append({'archiveId':part['archiveId'],'sha256':part['sha256'],'bytes':len(chunk)})
        manifest = {'artifactId':digest([identity,file_digest(path)]),'identity':identity,'kind':kind,
                    'sha256':file_digest(path),'bytes':path.stat().st_size,'chunks':parts}
        self.call('artifact-manifest',manifest)
        return manifest
