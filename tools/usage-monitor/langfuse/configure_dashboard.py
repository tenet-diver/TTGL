#!/usr/bin/env python3
"""Configure native Langfuse dashboards; no custom UI or runtime dependencies."""
import argparse,base64,json,urllib.request,urllib.error
from pathlib import Path

def definitions():
 def env(name):return [{'column':'environment','operator':'=','type':'string','value':name}]
 def typ(name):return [{'column':'type','operator':'any of','type':'stringOptions','value':[name]}]
 daily=env('usage-daily-v3')+typ('GENERATION');sessions=env('usage-sessions-v2')+typ('GENERATION')
 tools=env('usage-tools')+typ('TOOL');timed=tools+[{'column':'metadata','key':'timing_known','operator':'=','type':'stringObject','value':'true'}]
 patterns=env('usage-tools')+typ('EVENT')+[{'column':'metadata','key':'record_kind','operator':'=','type':'stringObject','value':'argument_pattern'}]
 return [
 ('Measured token buckets — total is a reference','usageType','usageByType','sum','HORIZONTAL_BAR',daily),
 ('API-equivalent cost buckets — total is a reference','costType','costByType','sum','HORIZONTAL_BAR',daily),
 ('Tokens by model — measured','providedModelName','totalTokens','sum','HORIZONTAL_BAR',daily),
 ('API-equivalent cost by model — current prices','providedModelName','totalCost','sum','HORIZONTAL_BAR',daily),
 ('Total native tool time — overlaps are not elapsed time','name','latency','sum','HORIZONTAL_BAR',timed),
 ('Slow native tools — p95 known durations','name','latency','p95','HORIZONTAL_BAR',timed),
 ('Most frequent native tools','name','count','count','HORIZONTAL_BAR',tools),
 ('Typical argument patterns — derived shape occurrences','name','count','count','HORIZONTAL_BAR',patterns),
 ('Session lifetime tokens — last active in selected range','sessionId','totalTokens','sum','HORIZONTAL_BAR',sessions),
 ('Measured tokens per day — Europe/Amsterdam','providedModelName','totalTokens','sum','LINE_TIME_SERIES',daily),
 ]

def configure(credentials,dashboard_id,state):
 c=json.loads(credentials.read_text());auth=base64.b64encode((c['public_key']+':'+c['secret_key']).encode()).decode()
 if c['base_url'] not in ['http://localhost:3000','http://127.0.0.1:3000']:raise ValueError('Expected local Langfuse')
 def api(path,data=None,method=None):
  req=urllib.request.Request(c['base_url']+path,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Basic '+auth,'Content-Type':'application/json'},method=method)
  try:
   with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
  except urllib.error.HTTPError as e:raise RuntimeError(str(e.code)+' '+e.read().decode()[:1600])
 # Re-running configuration reuses its owned widgets, instead of duplicating them.
 cache=json.loads(state.read_text()) if state.exists() else {};placements=[]
 descriptions=[
  'Cached input, uncached input and output are separate buckets. The total bar is their sum; do not add it again.',
  'Langfuse model-price estimates. The total bar summarizes the other bars. These are not subscription charges.',
  'Measured model token totals for selected calendar days, including cache reads.',
  'API price scenario, not invoices. Models without a price match have unknown cost.',
  'Sum of known tool execution durations. Parallel calls overlap; this is not elapsed session time.',
  '95% of measured calls finish within this duration. Unknown timings are excluded.',
  'Completed native operations. Parent batch wrappers are excluded when child events are available.',
  'One summary per tool call. Private values are omitted; safe options such as result limits and compact/full remain.',
  'Lifetime session tokens selected by last activity. This is an alternative view of daily usage; do not add them.',
  'Calendar-day totals from retained logs using Europe/Amsterdam source days. This is not an hourly usage chart.']
 for i,(name,dim,measure,agg,chart,filters) in enumerate(definitions()):
  definition={'name':name,'description':descriptions[i],'view':'observations','dimensions':[{'field':dim}],'metrics':[{'measure':measure,'agg':agg}],'filters':filters,'chartType':chart,'chartConfig':{'row_limit':15}}
  if name in cache:w=api('/api/public/unstable/dashboard-widgets/'+cache[name],definition,'PATCH')
  else:
   w=api('/api/public/unstable/dashboard-widgets',definition);cache[name]=w['id'];state.write_text(json.dumps(cache))
  placements.append({'id':'analytics-'+str(i),'type':'widget','widgetId':w['id'],'x':(i%2)*6,'y':(i//2)*6,'width':6,'height':6})
 api('/api/public/unstable/dashboards/'+dashboard_id,{'name':'Codex Token and Time Breakdown','description':'Retained Codex history. Model tokens are measured; dollar values are API price scenarios. Tool times can overlap and are not elapsed session time. Argument summaries omit private values. Choose a date range to compare periods.','definition':{'widgets':placements},'filters':[]},'PATCH')
 print(c['base_url']+'/project/ttgl-codex/dashboards/'+dashboard_id)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--credentials',type=Path,required=True);p.add_argument('--dashboard',required=True);p.add_argument('--state',type=Path,required=True);a=p.parse_args();configure(a.credentials,a.dashboard,a.state)
