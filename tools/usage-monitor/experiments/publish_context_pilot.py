#!/usr/bin/env python3
"""Publish actual pilot calls and completed fixture trials to local Langfuse."""
import argparse, base64, collections, importlib.util, json, pathlib, re, time, urllib.request
P=pathlib.Path(__file__).resolve().parent.parent/'langfuse/bridge.py'
spec=importlib.util.spec_from_file_location('pilot_bridge',P);b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
ENV='context-experiments-v1'

def grade(stage):
    answer=stage['answer'];expected=stage['expected']
    if stage['stage']<3:return expected in answer and 'item-117' in answer
    return re.findall(r'\b[0-9a-f]{16}\b',answer.lower())==[expected]

def publish(root,credentials):
    global ENV
    ENV='context-pilot-'+root.name
    if not ((root/'completion.json').exists() or (root/'stopped.json').exists()):raise ValueError('Finalize trial journal before publication; immutable names must not change')
    state=root/'langfuse';state.mkdir(exist_ok=True);e=b.Exporter(credentials,state)
    c=json.loads(credentials.read_text());auth=base64.b64encode((c['public_key']+':'+c['secret_key']).encode()).decode()
    def api(path,data=None,method=None):
        req=urllib.request.Request(c['base_url']+path,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Basic '+auth,'Content-Type':'application/json'},method=method)
        with urllib.request.urlopen(req,timeout=45) as r:return json.load(r)
    records=[json.loads(x) for x in (root/'requests.jsonl').read_text().splitlines()]
    completed=collections.defaultdict(list)
    complete_runs={p.stem for p in root.glob('r[0-9]-*.json') if len(json.loads(p.read_text()))==5 and all(s['completed'] for s in json.loads(p.read_text()))}
    held=(root/'security-gate.json').exists()
    for i,r in enumerate(records):
        run=r['run'];trace=root.name+':'+run;usage=r.get('usage')
        md={'record_kind':'live_context_pilot','trace_name':'Context pilot | '+run,'arm':r['arm'],'scope':'synthetic fixture mechanism pilot, not general benchmark','measurement':'provider response usage','proxy_status':r['status'],'comparison_status':'completed fixture trial' if run in complete_runs else 'incomplete/setup; not comparable','security_hold':held,'upstream_http_status':r.get('http_status'),'experimental':True,'compression_adapter':'offline Headroom 0.42.0 agent/lossless insertion or older-output masking; no production settings changed'}
        start=b.nanos(r['started']);end=start+int(r['elapsed_seconds']*1e9)
        if usage:
            I=usage['input_tokens'];C=usage.get('input_tokens_details',{}).get('cached_tokens',0);O=usage['output_tokens']
            if not 0<=C<=I:raise ValueError('Invalid measured cache split')
            buckets={'input':I-C,'input_cached_tokens':C,'output':O,'total':I+O}
            md.update(provider_response_id=r.get('response_id'),input_bytes_before=r['input_bytes_before'],input_bytes_after=r['input_bytes_after'])
            e.add(b.span(trace,trace+':response:'+str(i),('preflight' if run=='preflight' else r['arm'] if run in complete_runs else r['arm']+' / incomplete; not comparable'),'generation',start,end,ENV,md,trace,trace+':root',buckets,r['model']))
            completed[run].append(r)
        else:
            md['usage_unknown']=True
            e.add(b.span(trace,trace+':unmetered:'+str(i),r['arm']+' / unmetered request','event',start,end,ENV,md,trace,trace+':root'))
    score_state=state/'scores.json';scores=json.loads(score_state.read_text()) if score_state.exists() else []
    summary=[]
    for path in sorted(root.glob('r[0-9]-*.json')):
        stages=json.loads(path.read_text())
        if len(stages)!=5:continue
        run=path.stem;arm=run.split('-',2)[2];trace=root.name+':'+run;passed=sum(grade(s) for s in stages);elapsed=sum(s['elapsed_seconds'] for s in stages)
        end=int(path.stat().st_mtime*1e9);start=end-int(elapsed*1e9)
        md={'trace_name':'Context pilot | '+run,'record_kind':'completed_fixture_trial','arm':arm,'quality_checks_passed':passed,'quality_checks_total':5,'quality_pass':passed==5,'timing_scope':'sum of observed CLI stage elapsed seconds; display interval reconstructed','scope':'synthetic fixtures only; partial pilot, four assignments per arm originally planned','security_hold':held,'native_thread_id':stages[-1]['thread_id'],'grading':'failed-row identity AND message; exact requested checksum among returned checksum values'}
        e.add(b.span(trace,trace+':root',arm,'agent',start,end,ENV,md,trace))
        if run not in scores:
            api('/api/public/scores',[{'id':b.digest(trace+':correctness'),'traceId':b.digest(trace),'name':'Fixture correctness','value':int(passed==5),'dataType':'BOOLEAN','environment':ENV,'metadata':{'checks_passed':passed,'checks_total':5,'synthetic_pilot_only':True}}])
            scores.append(run);score_state.write_text(json.dumps(scores))
        totals=collections.Counter()
        for r in completed[run]:
            u=r['usage'];I=u['input_tokens'];C=u.get('input_tokens_details',{}).get('cached_tokens',0)
            totals.update(input=I,cached=C,fresh=I-C,output=u['output_tokens'],model_calls=1)
        # Price scenario frozen from the existing local model mapping, not invoices.
        cost=totals['fresh']*4e-6+totals['cached']*.2e-6+totals['output']*15e-6
        summary.append({'run':run,'arm':arm,'quality_checks_passed':passed,'quality_checks_total':5,'quality_pass':passed==5,'elapsed_seconds':elapsed,**dict(totals),'api_price_scenario_usd':cost,'trace_id':b.digest(trace)})
    e.flush();e.db.close();(root/'summary.json').write_text(json.dumps(summary,indent=2))
    dashboard_state=state/'dashboard.json'
    if not dashboard_state.exists():
        d=api('/api/public/unstable/dashboards',{'name':'Context Compression Pilot — partial, security blocked' if held else 'Context Compression Pilot — measured','description':'PARTIAL PILOT: execution stopped by security policy. Completed fixture trials only are comparable; incomplete/setup calls have separate names. Older-output masking failed its mechanism gate. No general savings or quality claim. Provider tokens measured; dollars are API-price scenarios. Correctness is scored on traces. Never add this projection to normal usage totals.' if held else 'Synthetic fixture mechanism pilot; provider counters measured, prices are scenarios.'})
        placements=[]
        for i,(name,typ,metrics) in enumerate([
            ('Measured model calls, input/output tokens and API-price scenario','GENERATION',[('count','count'),('inputTokens','sum'),('outputTokens','sum'),('totalCost','sum')]),
            ('Completed trials: count and total task time distribution','AGENT',[('count','count'),('latency','avg'),('latency','p50'),('latency','p95'),('latency','max')])]):
            w=api('/api/public/unstable/dashboard-widgets',{'name':name,'description':'Separate experimental dataset. Quality and cache buckets are recorded on each trace. No estimated token attribution is used.','view':'observations','dimensions':[{'field':'name'}],'metrics':[{'measure':measure,'agg':agg} for measure,agg in metrics],'filters':[{'column':'environment','operator':'=','type':'string','value':ENV},{'column':'type','operator':'any of','type':'stringOptions','value':[typ]}],'chartType':'PIVOT_TABLE','chartConfig':{'row_limit':20}})
            placements.append({'id':'pilot-'+str(i),'type':'widget','widgetId':w['id'],'x':0,'y':i*8,'width':12,'height':8})
        api('/api/public/unstable/dashboards/'+d['id'],{'definition':{'widgets':placements}},'PATCH');dashboard_state.write_text(json.dumps(d))
    d=json.loads(dashboard_state.read_text());print(json.dumps({'dashboard':c['base_url']+'/project/ttgl-codex/dashboards/'+d['id'],'completed_trials':len(summary),'exported_records':e.exported}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=pathlib.Path,required=True);p.add_argument('--credentials',type=pathlib.Path,required=True);a=p.parse_args();publish(a.root,a.credentials)
