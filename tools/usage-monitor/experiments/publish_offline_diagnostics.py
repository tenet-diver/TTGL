#!/usr/bin/env python3
"""Publish finalized OFFLINE checks to native Langfuse; never invent usage or quality."""
import argparse,base64,importlib.util,json,pathlib,urllib.request,urllib.parse
from datetime import datetime,timezone

HERE=pathlib.Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('existing_bridge',HERE.parent/'langfuse/bridge.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)

def publish(report,credentials,state):
    data=json.loads(report.read_text());c=json.loads(credentials.read_text())
    if c['base_url'] not in ['http://localhost:3000','http://127.0.0.1:3000']:raise ValueError('Local only')
    urllib.request.install_opener(urllib.request.build_opener(urllib.request.ProxyHandler({})))
    state.mkdir(parents=True,exist_ok=True);state.chmod(0o700)
    env='context-offline-diagnostics-v1';trace='offline-context:'+data['adapter_sha256']+':'+data['checked_at']
    ts=b.nanos(data['checked_at'])
    auth=base64.b64encode((c['public_key']+':'+c['secret_key']).encode()).decode()
    def api(path,body=None,method=None):
        req=urllib.request.Request(c['base_url']+path,data=None if body is None else json.dumps(body).encode(),headers={'Authorization':'Basic '+auth,'Content-Type':'application/json'},method=method)
        with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
    f=state/'dashboard.json'
    if not f.exists():
        dashboard=api('/api/public/unstable/dashboards',{'name':'Context experiments — offline diagnostics; live trials blocked','description':'Actual executed offline adapter checks only. No Headroom execution, coding-task quality, measured token usage or savings. Native trial and runtime review remain gated.'})
        f.write_text(json.dumps(dashboard))
    else:dashboard=json.loads(f.read_text())
    wf=state/'widget.json'
    if wf.exists():w=json.loads(wf.read_text())
    else:
        w=api('/api/public/unstable/dashboard-widgets',{'name':'Executed adapter checks by result — offline only','description':'Counts are diagnostic events, not tasks or model calls.','view':'observations','dimensions':[{'field':'name'}],'metrics':[{'measure':'count','agg':'count'}],'filters':[{'column':'environment','operator':'=','type':'string','value':env},{'column':'type','operator':'any of','type':'stringOptions','value':['EVENT']}],'chartType':'PIVOT_TABLE','chartConfig':{'row_limit':30}});wf.write_text(json.dumps(w))
    api('/api/public/unstable/dashboards/'+dashboard['id'],{'definition':{'widgets':[{'id':'offline-checks','type':'widget','widgetId':w['id'],'x':0,'y':0,'width':12,'height':12}]}},'PATCH')
    e=b.Exporter(credentials,state)
    for check in data['checks']:
        name=('PASS | ' if check['passed'] else 'FAIL | ')+check['name']
        md={'trace_name':'Offline context adapter checks — NOT model trials','record_kind':'offline_mechanism_check',
            'passed':check['passed'],'headroom_executed':False,'model_trials':False,'usage_unknown':True,
            'limitation':data['limitation'],'adapter_sha256':data['adapter_sha256']}
        e.add(b.span(trace,trace+':'+check['name'],name,'event',ts,ts,env,md))
    try:
        e.flush();exported=e.exported
    finally:e.db.close()
    url=c['base_url']+'/project/'+c['project_id']+'/dashboards/'+dashboard['id']
    result={'dashboard':url,'new_exported_events':exported,'expected_checks':len(data['checks']),'environment':env}
    (state/'publication.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--report',type=pathlib.Path,required=True);p.add_argument('--credentials',type=pathlib.Path,required=True);p.add_argument('--state',type=pathlib.Path,required=True)
    a=p.parse_args();publish(a.report,a.credentials,a.state)
