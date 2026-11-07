"""Use reviewed Mem0 infer=False and maintained MCP graph server; no LLM calls."""
import json,re,time
from pathlib import Path
from mcp_memory_probe import Client

def initialize(entry,store,log):
    c=Client(entry,store,log);c.request('initialize',dict(protocolVersion='2025-06-18',capabilities={},clientInfo=dict(name='ttgl-raw-memory',version='1')));c.p.stdin.write(b'{"jsonrpc":"2.0","method":"notifications/initialized"}\n');c.p.stdin.flush();return c

def run(root,backend,action):
    global_root=root.parents[2];data=json.loads((root/'input.json').read_text());started=time.monotonic();result={}
    if backend=='mem0_raw':
        from mem0_codex_adapter import memory
        m=memory(root/'engine')
        def forbidden(*args,**kwargs):raise RuntimeError('infer=False arm forbids LLM calls')
        m.llm.generate_response=forbidden
        try:
            if action=='build':
                added=m.add([dict(role='user',content=e['body']) for e in data['episodes']],user_id='case',infer=False);result=dict(stored=len(added['results']))
            else:result=dict(hits=m.search((root/'question.txt').read_text(),filters={'user_id':'case'},limit=10))
        finally:m.vector_store.client.close();m.db.close()
    elif backend=='mcp_graph_raw':
        entry=global_root/'mcp-memory-review/node_modules/@modelcontextprotocol/server-memory/dist/index.js';c=initialize(entry,root/'knowledge.jsonl',root/(action+'-'+str(time.time_ns())+'-stderr.log'))
        try:
            if action=='build':
                entities=[dict(name=e['id'],entityType='dated_record',observations=[e['body']]) for e in data['episodes']];created=c.tool('create_entities',dict(entities=entities));c.tool('create_relations',dict(relations=[dict(**{'from':a['id'],'to':b['id']},relationType='followed_by') for a,b in zip(data['episodes'],data['episodes'][1:]) ]));result=dict(stored=len(created['entities']) if isinstance(created,dict) else len(created))
            else:
                tokens=list(dict.fromkeys(t.lower() for t in re.findall(r'[\w-]+',(root/'question.txt').read_text()) if len(t)>=3));found={};receipts=[]
                for token in tokens:
                    hit=c.tool('search_nodes',dict(query=token));entities=hit['entities'];receipts.append(dict(token=token,count=len(entities)))
                    for e in entities:
                        prior=found.setdefault(e['name'],dict(entity=e,score=0));prior['score']+=1/max(1,len(entities))
                ranked=sorted(found.values(),key=lambda v:(-v['score'],v['entity']['name']));hits=[];used=0
                for v in ranked:
                    text=json.dumps(v['entity'],ensure_ascii=False)
                    if len(hits)>=10 or used+len(text)>12000:break
                    hits.append(v['entity']);used+=len(text)
                result=dict(hits=hits,queries=receipts,ranking='Generic inverse-hit-frequency lexical union over maintained search_nodes,10 nodes/12000 chars; not graph reasoning efficacy.')
        finally:c.close()
    else:raise ValueError('Unknown backend')
    result.update(seconds=time.monotonic()-started,LLM_calls=0,action=action,backend=backend,local_monetary_cost=None);return result
if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('backend',choices=['mem0_raw','mcp_graph_raw']);p.add_argument('action',choices=['build','query']);p.add_argument('output',type=Path);a=p.parse_args();a.output.write_text(json.dumps(run(a.root,a.backend,a.action),indent=2)+'\n')
