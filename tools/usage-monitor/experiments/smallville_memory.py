"""Local Smallville memory using pinned Apache-2.0 author storage/ranking/reflection.

Original prompts and algorithm bodies live in smallville_vendor. Native model
and reviewed local embedding callbacks replace obsolete provider/simulation glue.
No provider, embedding, installation, network or background inference is implicit.
"""
import ast
import contextlib
from datetime import datetime
import importlib.util
import io
import json
import math
from pathlib import Path
import re
from types import SimpleNamespace
import uuid
from smallville_vendor.memory import AssociativeMemory

VENDOR=Path(__file__).with_name('smallville_vendor')


def render(template,values):
    """Same substitution/comment removal order as upstream generate_prompt."""
    if isinstance(values,str):values=[values]
    text=(VENDOR/'prompts'/template).read_text()
    for index,value in enumerate(values):text=text.replace(f'!<INPUT {index}>!',str(value))
    marker='<commentblockmarker>###</commentblockmarker>'
    if marker in text:text=text.split(marker)[1]
    return text.strip()


def chat_wrapper(prompt,example,instruction):
    # Verbatim upstream ChatGPT_safe_generate_response prompt construction.
    prompt='"""\n'+prompt+'\n"""\n'
    prompt+=f'Output the response to the prompt above in json. {instruction}\n'
    prompt+='Example output json:\n'
    prompt+='{"output": "'+str(example)+'"}'
    return prompt


def identity_text(s):
    # Scratch.get_str_iss output format, including terminal-agent identity values.
    return (f'Name: {s.name}\nAge: {s.age}\nInnate traits: {s.innate}\n'
            f'Learned traits: {s.learned}\nCurrently: {s.currently}\n'
            f'Lifestyle: {s.lifestyle}\nDaily plan requirement: {s.daily_plan_req}\n'
            f"Current Date: {s.curr_time.strftime('%A %B %d')}\n")


def load_module(name):
    spec=importlib.util.spec_from_file_location('ttgl_smallville_'+name+'_'+uuid.uuid4().hex,VENDOR/(name+'.py'))
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


class SmallvilleMemory:
    def __init__(self,root,embed,complete,identity,*,restore_last_access=False):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True,mode=0o700)
        self.embed_callback=embed;self.complete_callback=complete
        self.restore_last_access=restore_last_access
        self.retrieval=load_module('retrieval');self.reflection=load_module('reflection')
        initial=self.root/'initial'
        if not initial.exists():
            initial.mkdir()
            for filename,data in [('nodes.json',{}),('embeddings.json',{}),('kw_strength.json',{'kw_strength_event':{},'kw_strength_thought':{}})]:
                (initial/filename).write_text(json.dumps(data))
        current=self.root/'current.json';state=None
        if current.exists():
            pointer=json.loads(current.read_text())['checkpoint']
            if not re.fullmatch(r'checkpoint-[a-f0-9]{32}',pointer):raise ValueError('Invalid checkpoint pointer')
            initial=self.root/pointer;state=json.loads((initial/'adapter-state.json').read_text())
        self.memory=AssociativeMemory(str(initial))
        defaults=dict(name='TTGL agent',age='not applicable',innate='careful, curious',learned='An assistant that solves terminal tasks.',currently='Working on the assigned task.',lifestyle='not applicable',daily_plan_req='Complete the assigned task and verify its outcome.')
        defaults.update(identity)
        self.scratch=SimpleNamespace(**defaults,curr_time=datetime(2026,1,1),recency_w=1,relevance_w=1,importance_w=1,recency_decay=.99,importance_trigger_max=150,importance_trigger_curr=150,importance_ele_n=0)
        self.scratch.get_str_iss=lambda:identity_text(self.scratch)
        if state:
            for k in ('importance_trigger_curr','importance_ele_n'):setattr(self.scratch,k,state[k])
            if restore_last_access:
                for ident,value in state['last_accessed'].items():self.memory.id_to_node[ident].last_accessed=datetime.fromisoformat(value)
        self.persona=SimpleNamespace(name=self.scratch.name,scratch=self.scratch,a_mem=self.memory)
        self.retrieval.get_embedding=self.embedding
        self.reflection.__dict__.update(debug=False,get_embedding=self.embedding,new_retrieve=self._retrieve,
            run_gpt_prompt_event_poignancy=self._poignancy,run_gpt_prompt_chat_poignancy=self._chat_poignancy,
            run_gpt_prompt_focal_pt=self._focal,run_gpt_prompt_insight_and_guidance=self._insights,
            run_gpt_prompt_event_triple=self._triple)

    def audit(self,kind,**values):
        with (self.root/'audit.jsonl').open('a') as f:f.write(json.dumps(dict(kind=kind,**values),ensure_ascii=False)+'\n')

    def embedding(self,text):
        values=list(self.embed_callback(text))
        if not values or any(not isinstance(x,(float,int)) or not math.isfinite(x) for x in values) or sum(x*x for x in values)==0:raise ValueError('Invalid local embedding')
        dims={len(v) for v in self.memory.embeddings.values()}
        if dims and dims!={len(values)}:raise ValueError('Embedding dimension mismatch')
        self.audit('embedding',characters=len(text),dimensions=len(values))
        return values

    def call(self,prompt,role):
        self.audit('model_requested',role=role,prompt=prompt)
        try:answer=self.complete_callback(prompt,role)
        except BaseException as error:
            self.audit('model_error',role=role,error=type(error).__name__);raise
        if not isinstance(answer,str):raise ValueError('Model callback must return raw text')
        self.audit('model_returned',role=role,answer=answer)
        return answer.strip()

    def _poignancy(self,persona,description):
        prompt=render('v3_ChatGPT/poignancy_event_v1.txt',[self.scratch.name,self.scratch.get_str_iss(),self.scratch.name,description])
        answer=self.call(chat_wrapper(prompt,'5','The output should ONLY contain ONE integer value on the scale of 1 to 10.'),'importance')
        # Same upstream JSON output and integer conversion; fail closed on invalid
        # values rather than repeat uncertain calls or substitute an invented4.
        raw=json.loads(answer[:answer.rfind('}')+1])['output'];value=int(raw)
        if isinstance(raw,bool) or not 1<=value<=10:raise ValueError('Invalid importance rating')
        return value,None

    def _chat_poignancy(self,*args):raise ValueError('Chat perception is outside this registered terminal adapter')

    def _focal(self,persona,statements,n):
        prompt=render('v3_ChatGPT/generate_focal_pt_v1.txt',[statements,str(n)])
        example='["What should Jane do for lunch", "Does Jane like strawberry", "Who is Jane"]'
        answer=self.call(chat_wrapper(prompt,example,'Output must be a list of str.'),'reflection_questions')
        raw=json.loads(answer[:answer.rfind('}')+1])['output']
        questions=ast.literal_eval(raw)
        if not isinstance(questions,list) or len(questions)!=n or any(not isinstance(q,str) or not q.strip() for q in questions):raise ValueError('Invalid focal questions')
        return questions,None

    def _insights(self,persona,statements,n):
        # Upstream calls v2, not the superficially similar v3 template.
        answer=self.call(render('v2/insight_and_evidence_v1.txt',[statements,str(n)]),'reflection_insights')
        answer='1. '+answer.strip();out={}
        for line in answer.split('\n'):
            row=line.split('. ')[-1];thought=row.split('(because of ')[0].strip()
            evidence=row.split('(because of ')[1].split(')')[0].strip()
            indices=[int(x.strip()) for x in re.findall(r'\d+',evidence)]
            if not thought or not indices:raise ValueError('Missing insight/evidence')
            count=sum(1 for line in statements.splitlines() if re.match(r'^\d+\. ',line))
            if any(i<0 or i>=count for i in indices):raise ValueError('Invalid reflection evidence index')
            out[thought]=indices
        if len(out)!=n:raise ValueError('Unexpected insight count')
        return out,None

    def _triple(self,description,persona):
        if '(' in description:description=description.split('(')[-1].split(')')[0]
        answer=self.call(render('v2/generate_event_triple_v1.txt',[self.persona.name,description,self.persona.name]),'reflection_triple')
        values=[x.strip() for x in answer.split(')')[0].split(',')]
        if len(values)!=2:raise ValueError('Invalid original completion-style predicate/object pair')
        return (self.persona.name,values[0],values[1]),None

    def observe(self,description,subject,predicate,object_,when):
        self.scratch.curr_time=when
        text=description
        if '(' in text:text=text.split('(')[1].split(')')[0].strip()
        vector=self.memory.embeddings.get(text)
        if vector is None:vector=self.embedding(text)
        rating=1 if 'is idle' in text else self._poignancy(self.persona,text)[0]
        node=self.memory.add_event(when,None,subject,predicate,object_,description,{subject,object_},rating,(text,vector),[])
        self.scratch.importance_trigger_curr-=rating;self.scratch.importance_ele_n+=1
        self.audit('observation_added',node_id=node.node_id,poignancy=rating,description=node.description)
        self.checkpoint();return node

    def _retrieve(self,persona,questions,n_count=30):
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            result=self.retrieval.new_retrieve(persona,questions,n_count)
        self.audit('retrieval',questions=questions,selected={q:[n.node_id for n in nodes] for q,nodes in result.items()},upstream_score_log=printed.getvalue())
        return result

    def retrieve(self,question,when,n_count=30):
        if not isinstance(n_count,int) or not 1<=n_count<=100:raise ValueError('Invalid retrieval count')
        self.scratch.curr_time=when;result=self._retrieve(self.persona,[question],n_count)[question];self.checkpoint();return result

    def reflect_if_due(self,when):
        self.scratch.curr_time=when
        with contextlib.redirect_stdout(io.StringIO()) as printed:
            due=self.reflection.reflection_trigger(self.persona)
        self.audit('reflection_trigger',due=due,remaining=self.scratch.importance_trigger_curr,log=printed.getvalue())
        if not due:return []
        before=set(self.memory.id_to_node)
        try:
            with contextlib.redirect_stdout(io.StringIO()) as printed:
                self.reflection.run_reflect(self.persona)
            self.reflection.reset_reflection_counter(self.persona)
            self.audit('reflection_completed',log=printed.getvalue())
        except BaseException as error:
            self.audit('reflection_failed',error=type(error).__name__);self.checkpoint();raise
        added=[node for ident,node in self.memory.id_to_node.items() if ident not in before]
        self.checkpoint();return added

    def checkpoint(self):
        # Preserve original three-file export unmodified. Adapter pointer gives a
        # completed snapshot boundary; sidecar records optional access persistence.
        name='checkpoint-'+uuid.uuid4().hex;directory=self.root/name;directory.mkdir()
        self.memory.save(str(directory))
        state=dict(importance_trigger_curr=self.scratch.importance_trigger_curr,importance_ele_n=self.scratch.importance_ele_n,
            last_accessed={i:n.last_accessed.isoformat() for i,n in self.memory.id_to_node.items()},restore_last_access=self.restore_last_access)
        (directory/'adapter-state.json').write_text(json.dumps(state,indent=2)+'\n')
        temporary=self.root/('pointer-'+uuid.uuid4().hex+'.tmp');temporary.write_text(json.dumps(dict(checkpoint=name))+'\n');temporary.replace(self.root/'current.json')
        return directory
