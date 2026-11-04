"""Native widgets for explicitly estimated context contributions."""
import base64,json,urllib.request

def configure(credentials,state,coverage=None,force=False):
 c=json.loads(credentials.read_text());auth=base64.b64encode((c['public_key']+':'+c['secret_key']).encode()).decode()
 if c['base_url'] not in ['http://localhost:3000','http://127.0.0.1:3000']:raise ValueError('Local Langfuse required')
 def api(path,data=None,method=None):
  req=urllib.request.Request(c['base_url']+path,data=json.dumps(data).encode() if data is not None else None,headers={'Authorization':'Basic '+auth,'Content-Type':'application/json'},method=method)
  with urllib.request.urlopen(req,timeout=60) as r:return json.load(r)
 cache=json.loads(state.read_text()) if state.exists() else {}
 if not force and cache.get('version')==2 and cache.get('coverage')==coverage:return cache
 filters=[{'column':'environment','operator':'=','type':'string','value':'usage-context-estimates-v2'},{'column':'type','operator':'any of','type':'stringOptions','value':['GENERATION']}]
 description='ESTIMATE, not per-tool billing. Dollar totals cover matched model prices only; unmatched models have unknown cost. Visible text is token-weighted and suffix-aligned to recorded model input; hidden/unlogged input stays unknown. Cache membership per tool is not provider-verified. Raw content is not exported. Table totals cover displayed rows only. The top 1,000 bucket rows can omit small buckets; use the CSV for complete side-by-side values. Input Tokens includes cache reads. Bucket-table subtotals include a duplicate total reference; do not interpret them as additional usage. Calendar-day estimates for reconciled model calls. Unreconciled transcript totals use a fixed first-import last-activity day and stay explicitly unattributed.'
 if coverage:description+=' Coverage: '+str(coverage.get('represented_sessions',0))+' / '+str(coverage.get('expected_sessions',464))+' retained usage sessions processed.'
 widgets=[('cost',{'name':'Top 30 context sources — estimated API-price contribution','view':'observations','dimensions':[{'field':'name'}],'metrics':[{'measure':'totalCost','agg':'sum'},{'measure':'inputTokens','agg':'sum'},{'measure':'outputTokens','agg':'sum'}],'filters':filters,'chartType':'PIVOT_TABLE','chartConfig':{'row_limit':30,'defaultSort':{'column':'sum_totalCost','order':'DESC'}}}),('buckets',{'name':'Estimated cached and other input by source — total is a reference','view':'observations','dimensions':[{'field':'name'},{'field':'usageType'}],'metrics':[{'measure':'usageByType','agg':'sum'}],'filters':filters+[{'column':'name','operator':'does not contain','type':'string','value':'Model response output'}],'chartType':'PIVOT_TABLE','chartConfig':{'row_limit':1000}})]
 for key,w in widgets:
  w['description']=description
  if key in cache:api('/api/public/unstable/dashboard-widgets/'+cache[key],w if cache.get('version')!=2 or force else {'description':description},'PATCH')
  else:cache[key]=api('/api/public/unstable/dashboard-widgets',w)['id'];state.write_text(json.dumps(cache))
 path='/api/public/unstable/dashboards/cmw2k9kd90003p61tatyoxvn6';current=api(path)
 if not all(cache[k] in [p.get('widgetId') for p in current['definition']['widgets']] for k in ['cost','buckets']):
  path='/api/public/unstable/dashboards/cmw2k9kd90003p61tatyoxvn6';d=api(path);placements=d['definition']['widgets']
  for p in placements:p['y']=p.get('y',0)+16
  for i,key in enumerate(['cost','buckets']):placements.append({'id':'context-'+key,'type':'widget','widgetId':cache[key],'x':0,'y':i*8,'width':12,'height':8})
  api(path,{'definition':{'widgets':placements}},'PATCH');cache['placed']=True;state.write_text(json.dumps(cache))
 if force:
  d=api(path);placements=sorted(d['definition']['widgets'],key=lambda p:(p.get('y',0),p.get('x',0)))
  api(path,{'definition':{'widgets':placements}},'PATCH')
 cache.update(version=2,coverage=coverage);state.write_text(json.dumps(cache));return cache
