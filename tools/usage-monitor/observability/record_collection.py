"""Shared full-cohort query semantics for bounded record-list transports."""
import json
import math
import re
import unicodedata


def normalize(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',str(value)) if not unicodedata.combining(c)).lower().strip()


def text(value):
    if value is None:return 'unknown'
    if isinstance(value,(list,tuple)):return ', '.join(map(str,value))
    if isinstance(value,(int,float)):
        compact=next((f'{value/scale:.2f}'.rstrip('0').rstrip('.')+suffix for scale,suffix in ((1e9,'b'),(1e6,'m'),(1e3,'k')) if abs(value)>=scale),'')
        return f'{value} {value:,.2f} {compact}'
    return str(value)


def query_records(rows,columns,query=''):
    """Columns map stable keys to (accessor, numeric); unknowns always sort last."""
    if isinstance(query,str):
        if len(query)>16000:raise ValueError('List query too large')
        try:query=json.loads(query) if query else {}
        except json.JSONDecodeError as exc:raise ValueError('Invalid list query') from exc
    if not isinstance(query,dict):raise ValueError('Invalid list query')
    search=query.get('search','');filters=query.get('filters',{});sort=query.get('sort');direction=query.get('direction',1)
    if not isinstance(search,str) or len(search)>1000 or not isinstance(filters,dict) or len(filters)>len(columns):raise ValueError('Invalid list query')
    if sort is not None and sort not in columns:raise ValueError('Unknown sort column')
    if direction not in (1,-1):raise ValueError('Invalid sort direction')
    for key,value in filters.items():
        if key not in columns or not isinstance(value,str) or len(value)>8000:raise ValueError('Invalid column filter')
    terms=normalize(search).split()
    def matches(row):
        values={key:columns[key][0](row) for key in (columns if terms else filters)}
        if terms and not all(term in normalize(' '.join(text(v) for v in values.values())) for term in terms):return False
        for key,needle in filters.items():
            needle=needle.strip()
            if not needle:continue
            value=values[key]
            exact=re.fullmatch(r'is( not)? (.+)',needle,re.S)
            if exact:
                try:expected=json.loads(exact.group(2))
                except (ValueError,TypeError) as exc:raise ValueError('Invalid exact value filter') from exc
                comparable=lambda v:', '.join(map(str,v)) if isinstance(v,(list,tuple)) else v
                actual,expected=comparable(value),comparable(expected)
                numbers=type(actual) in (int,float) and type(expected) in (int,float)
                equal=(numbers or type(actual) is type(expected)) and actual==expected
                if equal==bool(exact.group(1)):return False
                continue
            match=re.fullmatch(r'(<=|>=|!=|=|<|>)\s*(-?\d[\d,]*(?:\.\d+)?)',needle) if columns[key][1] else None
            if match:
                if not isinstance(value,(int,float)) or not math.isfinite(value):return False
                op,limit=match.group(1),float(match.group(2).replace(',',''))
                if not {'<':value<limit,'>':value>limit,'<=':value<=limit,'>=':value>=limit,'=':value==limit,'!=':value!=limit}[op]:return False
            elif normalize(needle) not in normalize(text(value)):return False
        return True
    result=[row for row in rows if matches(row)] if terms or any(filters.values()) else list(rows)
    if sort:
        getter,numeric=columns[sort];known=[r for r in result if getter(r) is not None];unknown=[r for r in result if getter(r) is None]
        known.sort(key=lambda row:getter(row) if numeric else tuple((1,int(part)) if part.isdigit() else (0,part) for part in re.split(r'(\d+)',normalize(text(getter(row))))),reverse=direction==-1);result=known+unknown
    return result,dict(search=search,filters=filters,sort=sort,direction=direction)
