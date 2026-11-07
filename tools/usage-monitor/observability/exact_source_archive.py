"""Exact eligible tool-text archive, compatible with read_compression_source.

The existing capture archive may redact text, which cannot satisfy an exact
handle's recovery contract. This narrow writer rejects changed/redacted or
oversize text and never overwrites a conflicting record. It is experiment-only;
the normal running proxy is unchanged.
"""
from datetime import datetime,timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile


class ExactSourceArchive:
    def __init__(self,root,sanitizer,max_source_bytes=1048576):
        self.root=Path(root)
        if not callable(sanitizer):raise ValueError('Explicit existing privacy sanitizer required')
        if type(max_source_bytes) is not int or max_source_bytes<1:raise ValueError('Invalid source bound')
        self.sanitize=sanitizer;self.maximum=max_source_bytes

    def read(self,digest):
        self.validate(digest)
        row=json.loads((self.root/(digest+'.json')).read_text())
        text=row['content']
        if (row.get('source_sha256')!=digest or row.get('retained_sha256')!=digest
                or hashlib.sha256(text.encode()).hexdigest()!=digest):
            raise ValueError('Existing archive record is not exact; preserve it and pass through')
        return text

    @staticmethod
    def validate(digest):
        if not isinstance(digest,str) or len(digest)!=64 or any(c not in '0123456789abcdef' for c in digest):
            raise ValueError('Invalid SHA256')

    def __call__(self,digest,text):
        self.validate(digest)
        if not isinstance(text,str) or hashlib.sha256(text.encode()).hexdigest()!=digest:
            raise ValueError('Source hash mismatch')
        if len(text.encode())>self.maximum:raise ValueError('Source exceeds exact retention bound; no clipping')
        if self.sanitize(text)!=text:raise ValueError('Privacy redaction changes source; exact archival refused')
        self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        target=self.root/(digest+'.json')
        if target.exists():
            self.read(digest);return
        fd,temporary=tempfile.mkstemp(prefix=digest+'.',suffix='.tmp',dir=self.root)
        try:
            with os.fdopen(fd,'w') as f:
                json.dump(dict(source_sha256=digest,retained_sha256=digest,content=text,
                    archived_at=datetime.now(timezone.utc).isoformat(),
                    retention='Exact tool text accepted unchanged by configured privacy filter; hash verified. Not a secret-free guarantee. Experiment-owned archive.'),f,ensure_ascii=False)
                f.flush();os.fsync(f.fileno())
            try:os.link(temporary,target)  # Atomic create; never replace an existing record.
            except FileExistsError:self.read(digest)
            directory=os.open(self.root,os.O_RDONLY)
            try:os.fsync(directory)
            finally:os.close(directory)
            self.read(digest)
        finally:
            Path(temporary).unlink(missing_ok=True)
