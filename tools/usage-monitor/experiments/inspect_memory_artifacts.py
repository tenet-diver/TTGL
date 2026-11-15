#!/usr/bin/env python3
"""Read-only generated-memory structural/lexical inspection, not new efficacy data."""
from collections import Counter
from datetime import datetime,timezone
import hashlib,json,re
from pathlib import Path
from cost_context_study import REPO
ROOT=REPO/'work/security/context-memory-20261107/memory-storage-ablation-001'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def inspect():
 corpora=json.loads((ROOT/'corpora.json').read_text());cases=[]
 for index,corpus in enumerate(corpora):
  directory=ROOT/f'corpus-{index:02d}';ingestion=directory/'mem0-build/ingestion.json';graph=directory/'mcp_graph_raw-build/knowledge.jsonl'
  extracted=json.loads(ingestion.read_text())['added']['results'];nodes=[json.loads(line) for line in graph.read_bytes().split(b'\n') if line]
  source={}
  for episode in corpus['episodes']:
   record=json.loads(episode['body']);text=record['messages'][0]['content'];service=re.search(r'\bsvc_\w+',text).group()
   source.setdefault(service,[]).append(dict(date=record['date'],text=text,tokens=set(re.findall(r'\b(?:team|gateway)_\w+',text))))
  checks=[]
  for memory in extracted:
   text=memory['memory'];services=set(re.findall(r'\bsvc_\w+',text));tokens=set(re.findall(r'\b(?:team|gateway)_\w+',text));known=set().union(*(e['tokens'] for s in services if s in source for e in source[s]))
   checks.append(dict(services=sorted(services),all_entity_values_from_same_service=bool(services) and services<=source.keys() and tokens<=known,both_versions_values_retained=bool(services) and known<=tokens))
  cases.append(dict(corpus=index,source_episodes=len(corpus['episodes']),services=len(source),extracted_memories=len(extracted),extracted_characters=sum(len(m['memory']) for m in extracted),mcp_records=dict(Counter(n['type'] for n in nodes)),mcp_relation_types=dict(Counter(n['relationType'] for n in nodes if n['type']=='relation')),lexical_checks=checks,source_hashes={str(p.relative_to(REPO)):sha(p) for p in (ingestion,graph)}))
 return dict(at=datetime.now(timezone.utc).isoformat(),cases=cases,scope='Existing synthetic development records only; lexical value coverage is not semantic correctness, temporal reasoning, benchmark efficacy or embedding relevance. Agent notes verification statements are self-reports unless separately graded.',model_calls=0)
if __name__=='__main__':
 result=inspect();out=ROOT.parent/'memory-artifact-inspection-001.json'
 with out.open('x') as stream:json.dump(result,stream,indent=2);stream.write('\n')
 for c in result['cases']:print({k:c[k] for k in ('corpus','source_episodes','services','extracted_memories','mcp_records','mcp_relation_types')},'supported',sum(x['all_entity_values_from_same_service'] for x in c['lexical_checks']),'both_versions',sum(x['both_versions_values_retained'] for x in c['lexical_checks']))
