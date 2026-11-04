#!/usr/bin/env python3
"""Load a bounded subset of the optimizer recipe pack (standard library only)."""
import argparse,json
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--id');p.add_argument('--category');p.add_argument('--query');p.add_argument('--limit',type=int,default=5);a=p.parse_args()
if not 1<=a.limit<=100:p.error('limit must be 1..100')
rs=json.loads((Path(__file__).resolve().parents[1]/'references/recipes.json').read_text())
if a.id:rs=[r for r in rs if r['id']==a.id]
if a.category:rs=[r for r in rs if r['category']==a.category]
if a.query:
 terms=a.query.lower().split()
 def score(r):return sum(t in (r['title']+' '+r['trigger']+' '+r['proposed_change']+' '+' '.join(r['tags'])).lower() for t in terms)
 rs=sorted((r for r in rs if score(r)>0),key=lambda r:(-score(r),r['id']))
print(json.dumps(rs[:a.limit],indent=2))
