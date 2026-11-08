"""Versioned modern-output compatibility; no ranking or prompt changes."""
import ast,json
from smallville_memory import SmallvilleMemory,render,chat_wrapper
class CompatibleMemory(SmallvilleMemory):
 def _focal(self,persona,statements,n):
  prompt=render('v3_ChatGPT/generate_focal_pt_v1.txt',[statements,str(n)])
  example='["What should Jane do for lunch", "Does Jane like strawberry", "Who is Jane"]'
  answer=self.call(chat_wrapper(prompt,example,'Output must be a list of str.'),'reflection_questions')
  raw=json.loads(answer[:answer.rfind('}')+1])['output'];questions=ast.literal_eval(raw) if isinstance(raw,str) else raw
  if not isinstance(questions,list) or len(questions)!=n or any(not isinstance(q,str) or not q.strip() for q in questions):raise ValueError('Invalid focal questions')
  return questions,None
