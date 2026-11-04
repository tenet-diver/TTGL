from pathlib import Path
import json,hashlib,importlib.util,copy,sys
sys.dont_write_bytecode=True
from jsonschema import Draft202012Validator
P=Path(__file__).resolve().parent
schemas={p.name.split('.')[0]:json.loads(p.read_text()) for p in (P/'schemas').glob('*.json')}
for s in schemas.values():Draft202012Validator.check_schema(s)
for typ in ['telemetry','suggestion','decision','history','comparison-plan']:Draft202012Validator(schemas[typ]).validate(json.loads((P/'examples'/f'{typ}.json').read_text()))
recipes=json.loads((P/'skill/codex-usage-optimizer/references/recipes.json').read_text())
assert len(recipes)==100 and len({r['id'] for r in recipes})==100 and len({r['title'] for r in recipes})==100
for r in recipes:Draft202012Validator(schemas['recipe']).validate(r);assert r['expected_effect']['default_savings_percent'] is None
spec=importlib.util.spec_from_file_location('detector',P/'skill/codex-usage-optimizer/scripts/analyze_fixture.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
data=json.loads((P/'examples/telemetry.json').read_text())
a=m.analyze(data);assert len(a['suggestions'])==1 and a['suggestions'][0]['expected']['payload_tokens_saved'] is None
b=m.analyze(data,reduction=.6);p=b['suggestions'][0];assert p['observed']['payload_tokens_estimate']==30000 and p['observed']['eligible_calls']==3
assert p['expected']['payload_tokens_saved']==18000 and p['expected']['cost_saved_usd'] is None and p['concrete_change'] is None
assert b==json.loads((P/'examples/analysis.json').read_text())
c=copy.deepcopy(data);c['tool_calls'].append(c['tool_calls'][0]);assert m.analyze(c)==a
c=copy.deepcopy(data);c['tool_calls'][0]['success']=False;assert not m.analyze(c)['suggestions']
c=copy.deepcopy(data);c['tool_calls'][0]['model_facing_output_tokens_estimate']=-1
try:m.analyze(c);raise AssertionError('negative value accepted')
except ValueError:pass
for invalid in [-.1,1.1,float('nan')]:
 try:m.analyze(data,reduction=invalid);raise AssertionError('invalid fraction accepted')
 except ValueError:pass
assert m.analyze(data,reduction=0)['suggestions'][0]['expected']['payload_tokens_saved']==0

# Execute the real parameterized reference query against in-memory synthetic SQLite.
import sqlite3,math
conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
conn.executescript((P/'examples/history-schema.sql').read_text());conn.executescript((P/'examples/history-fixture.sql').read_text())
params=json.loads((P/'examples/comparison-parameters.json').read_text());sql=(P/'examples/before-after.sql').read_text()
r=dict(conn.execute(sql,params).fetchone())
assert r['before_calls']==2 and r['after_calls']==3
assert r['after_known_payload']==2 and r['after_known_duration']==2 and r['after_known_outcome']==2
assert r['before_payload_total']==20000 and r['after_payload_total']==4000
assert math.isclose(r['payload_reduction_fraction'],.8) and math.isclose(r['duration_reduction_fraction'],-.1)
assert r==json.loads((P/'examples/before-after-result.json').read_text())['result']
assert conn.execute("SELECT count(*) FROM optimization_history WHERE decision='declined'").fetchone()[0]==1
conn.execute("UPDATE comparison_tool_calls SET model_facing_payload_tokens_estimate=16000 WHERE effective_profile_hash='profile-quiet'")
assert math.isclose(conn.execute(sql,params).fetchone()['payload_reduction_fraction'],-.6)
conn.execute("UPDATE comparison_tool_calls SET model_facing_payload_tokens_estimate=0 WHERE effective_profile_hash='profile-original'")
assert conn.execute(sql,params).fetchone()['payload_reduction_fraction'] is None
p2=dict(params);p2['repo_id']='no-such-repo';zero=conn.execute(sql,p2).fetchone()
assert zero['before_calls']==0 and zero['before_payload_total'] is None and zero['payload_reduction_fraction'] is None
try:
 conn.execute("INSERT INTO optimization_events SELECT * FROM optimization_events WHERE event_id='event-1'");raise AssertionError('duplicate accepted')
except sqlite3.IntegrityError:pass
plan=json.loads((P/'examples/comparison-plan.json').read_text());assert hashlib.sha256((P/'examples/before-after.sql').read_bytes()).hexdigest()==plan['query_sha256']
conn.close()

for n,digest in json.loads((P/'CHECKSUMS.json').read_text()).items():assert hashlib.sha256((P/n).read_bytes()).hexdigest()==digest,n
print('PASS: 100 recipes; 6 schemas; 5 typed examples; detector and SQL cohorts, missingness, zero baseline, signed regressions and scenarios; file hashes. No private logs imported or live settings changed.')
