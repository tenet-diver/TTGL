#!/usr/bin/env python3
"""Publish synthetic component evidence to native Langfuse datasets, never usage charts."""
import argparse,json,pathlib,urllib.request,urllib.error,base64,hashlib
parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--report',type=pathlib.Path,required=True);parser.add_argument('--credentials',type=pathlib.Path,required=True);parser.add_argument('--state',type=pathlib.Path,required=True);args=parser.parse_args()
p=args.state;p.mkdir(parents=True,exist_ok=True);p.chmod(0o700);c=json.loads(args.credentials.read_text())
if c['base_url'] not in ['http://localhost:3000','http://127.0.0.1:3000']:raise ValueError('Only local Langfuse is allowed')
op=urllib.request.build_opener(urllib.request.ProxyHandler({}));h={'Authorization':'Basic '+base64.b64encode((c['public_key']+':'+c['secret_key']).encode()).decode(),'Content-Type':'application/json'}
def api(path,body=None,method=None):
 req=urllib.request.Request(c['base_url']+path,data=None if body is None else json.dumps(body).encode(),headers=h,method=method)
 with op.open(req,timeout=20) as r:return json.load(r)
name='context-offline-diagnostics-20261105'
try:api('/api/public/datasets/'+name)
except urllib.error.HTTPError as e:
 if e.code!=404:raise
 api('/api/public/datasets',{'name':name,'description':'Executed synthetic offline checks and oracle-guided recovery comparisons. NOT model trials, task-quality or token/cost-savings evidence.','metadata':{'model_calls':0,'headroom_executed':False}})
r=json.loads(args.report.read_text())
if r.get('model_calls')!=0 or r.get('headroom_executed') is not False:raise ValueError('Offline component evidence only')
for row in r['results']:
 ident=hashlib.sha256((name+row['case']+row['arm']).encode()).hexdigest()[:24]
 api('/api/public/dataset-items',{'id':ident,'datasetName':name,'input':{'case':row['case'],'configuration':row['arm']},'expectedOutput':{'oracle_checks_required':5},'metadata':{'evidence_type':'offline synthetic, oracle-guided retrieval; no agent','observed_result':row}})
f=p/'offline-dashboard.json'
if f.exists():d=json.loads(f.read_text())
else:
 d=api('/api/public/unstable/dashboards',{'name':'Context experiments: 9/9 adapter checks; 10 offline comparisons; live blocked','description':'46/50 deterministic oracle checks across 10 synthetic comparisons. NOT model success or savings. Results are in Datasets > context-offline-diagnostics-20261105. Live trials blocked: provider/advisory proxy 403; no approved Headroom runtime; 32 GB disk exhausted. Observation ingestion is pending reconciliation and capacity; empty charts must not be interpreted as zero usage.'});f.write_text(json.dumps(d))
api('/api/public/unstable/dashboards/'+d['id'],{'description':'46/50 offline oracle checks passed. Projection without recovery fails 2/5 checks per fixture; all other arms pass 5/5. Open Datasets > '+name+' for the ten observed rows. These are synthetic component checks, NOT model-task quality, measured tokens or savings. Live trials are blocked by proxy 403, runtime review and insufficient disk. Trace ingestion is pending; empty charts are not zero usage.'},'PATCH')
print(json.dumps({'dataset':name,'dataset_items':10,'dashboard':c['base_url']+'/project/'+c['project_id']+'/dashboards/'+d['id']}))
