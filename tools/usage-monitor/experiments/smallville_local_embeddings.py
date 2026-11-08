"""Reviewed local BGE runtime bridge; no hosted embedding or memory API."""
import hashlib,json,os,time
from pathlib import Path


class LocalEmbeddings:
    def __init__(self,root,receipts):
        if os.environ.get('HF_HUB_OFFLINE')!='1':raise ValueError('Offline model loading required')
        root=Path(root);receipt=json.loads((root/'embedding-model-receipt.json').read_text())
        for item in receipt['files']:
            if hashlib.sha256((root/'embedding-model'/item['file']).read_bytes()).hexdigest()!=item['sha256']:raise ValueError('Pinned embedding source changed')
        from fastembed import TextEmbedding
        self.model=TextEmbedding(model_name='BAAI/bge-small-en-v1.5',specific_model_path=str(root/'embedding-model'),local_files_only=True,threads=2)
        self.receipts=Path(receipts)
    def __call__(self,text):
        start=time.perf_counter();result=list(self.model.embed([text.replace('\n',' ')]))[0].tolist()
        with self.receipts.open('a') as stream:stream.write(json.dumps(dict(sha256=hashlib.sha256(text.encode()).hexdigest(),characters=len(text),dimensions=len(result),local_embedding_inferences=1,seconds=time.perf_counter()-start))+'\n')
        return result
