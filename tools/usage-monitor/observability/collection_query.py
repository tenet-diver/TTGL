"""Apply shared table controls before HTTP pagination; never evaluate client code."""
import json
import math
import re
import unicodedata
from functools import cmp_to_key


def normalized(value):
    if value is None:return 'unknown'
    if isinstance(value,list):value=', '.join(map(str,value))
    return ''.join(c for c in unicodedata.normalize('NFKD',str(value)) if not unicodedata.combining(c)).casefold().strip()


def apply(rows, state, fields):
    if not state:return list(rows)
    if isinstance(state,str):
        if len(state)>16000:raise ValueError('Table query too long')
        state=json.loads(state)
    if not isinstance(state,dict) or set(state)-{'search','sort','direction','filters'}:raise ValueError('Invalid table query')
    search=state.get('search','');filters=state.get('filters',{});sort=state.get('sort');direction=state.get('direction',1)
    if not isinstance(search,str) or len(search)>2000 or not isinstance(filters,dict) or len(filters)>50 or sort is not None and sort not in fields or direction not in (1,-1):raise ValueError('Invalid table controls')
    for key,value in filters.items():
        if key not in fields or not isinstance(value,str) or len(value)>2000:raise ValueError('Invalid column filter')
    def match(value,query):
        comparison=re.fullmatch(r'\s*(<=|>=|!=|=|<|>)\s*(-?\d[\d,]*(?:\.\d+)?)\s*',query)
        if comparison:
            if type(value) not in (int,float) or not math.isfinite(value):return False
            op,number=comparison.groups();number=float(number.replace(',',''))
            return {'<':value<number,'>':value>number,'<=':value<=number,'>=':value>=number,'=':value==number,'!=':value!=number}[op]
        return normalized(query) in normalized(value)
    terms=normalized(search).split() if search else []
    result=[]
    for row in rows:
        values={key:get(row) for key,get in fields.items()}
        if not all(match(values[key],query) for key,query in filters.items() if query.strip()):continue
        text=' '.join(normalized(value) for value in values.values())
        if all(term in text for term in terms):result.append(row)
    if sort:
        def compare(a,b):
            left,right=fields[sort](a),fields[sort](b)
            if left is None or right is None:return (left is None)-(right is None)
            if type(left) in (int,float) and type(right) in (int,float):return direction*((left>right)-(left<right))
            def natural(value):return [(0,int(p)) if p.isdigit() else (1,p) for p in re.split(r'(\d+)',normalized(value))]
            left,right=natural(left),natural(right)
            return direction*((left>right)-(left<right))
        result.sort(key=cmp_to_key(compare))
    return result


def fields(names, metrics=None):
    result={key:lambda row,key=key:row.get(key) for key in names}
    result.update({key:lambda row,name=name:row['metrics'].get(name) for key,name in (metrics or {}).items()})
    return result
