#!/usr/bin/env python3
"""Download pinned reserved benchmark assets as data only, never execute them."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import urllib.request


def prepare(reservation, output):
    d=json.loads(reservation.read_text());output.mkdir(parents=True,exist_ok=False)
    plan=dict(at=datetime.now(timezone.utc).isoformat(),reservation_sha256=hashlib.sha256(reservation.read_bytes()).hexdigest(),
        purpose='Reserved-task environment preparation only; no implementation inspection, inference, import, install or tests',
        gate='Before any model assignment: source/dependency review, base fails/reference passes. Failed readiness excluded without replacement, never counted as solver failure.',
        tasks=d['evaluation_reserved'],model_calls=0)
    (output/'plan.json').write_text(json.dumps(plan,indent=2))
    jobs=[(task,phase) for task in d['evaluation_reserved'] for phase in ('base','reference')]
    def one(job):
        task,phase=job;repo=task['repo'];commit=task[phase+'_commit'];name=repo.split('/')[-1]
        url='https://codeload.github.com/'+repo+'/tar.gz/'+commit
        target=output/(name+'-'+phase+'.tar.gz');row=dict(repo=repo,phase=phase,commit=commit,url=url)
        try:
            with urllib.request.urlopen(url,timeout=120) as response:
                data=response.read(128*1024*1024+1)
            if len(data)>128*1024*1024:raise ValueError('Archive data limit exceeded')
            with target.open('xb') as stream:stream.write(data)
            row.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),downloaded=True,executed=False)
        except Exception as error:row.update(downloaded=False,error=repr(error),executed=False)
        (output/(name+'-'+phase+'.json')).write_text(json.dumps(row,indent=2));return row
    with ThreadPoolExecutor(max_workers=3) as pool:rows=list(pool.map(one,jobs))
    (output/'result.json').write_text(json.dumps(dict(artifacts=rows,model_calls=0,executed=False),indent=2))
    print(json.dumps(dict(downloaded=sum(r['downloaded'] for r in rows),planned=len(rows),executed=False)))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reservation',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();prepare(a.reservation,a.output)
