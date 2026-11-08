"""Completion parser compatibility: object text may contain commas."""
from smallville_memory import render
from smallville_compat import CompatibleMemory
class CompatibleMemoryV2(CompatibleMemory):
 def _triple(self,description,persona):
  if '(' in description:description=description.split('(')[-1].split(')')[0]
  answer=self.call(render('v2/generate_event_triple_v1.txt',[self.persona.name,description,self.persona.name]),'reflection_triple')
  values=[x.strip() for x in answer.split(')')[0].split(',',1)]
  if len(values)!=2 or not all(values):raise ValueError('Invalid completion predicate/object pair')
  return (self.persona.name,values[0],values[1]),None
