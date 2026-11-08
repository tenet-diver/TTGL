#!/usr/bin/env python3
"""Preserve the canonical Codex backend URL suffix through the capture adapter.

The installed provider recognizes this suffix for native backend capabilities.
Only the fixed backend prefix is normalized; bodies/authentication stay on the
existing fixed-upstream forwarding path. Normal services are untouched.
"""
import urllib.parse
import capture_proxy_longhorizon as capture


class Handler(capture.Handler):
    def proxy(self):
        self.downstream_path=self.path
        parsed=urllib.parse.urlsplit(self.path)
        prefix='/backend-api/codex/'
        if not parsed.scheme and not parsed.netloc and parsed.path.startswith(prefix):
            self.path='/'+parsed.path[len(prefix):]
            if parsed.query:self.path+='?'+parsed.query
        return super().proxy()

    def persist(self,record):
        record={**record,'downstream_path':capture.base.safe_content(self.downstream_path)[0]}
        return super().persist(record)


if __name__=='__main__':
    capture.base.Handler=Handler
    capture.base.DEFAULTS['ports']['capture']=8337
    capture.base.main()
