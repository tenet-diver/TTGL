"""Public UID1000 worker; sends only parser inputs, never owns coverage state."""
import importlib.util,json,os,sys
def main():
 # Match the reviewed PYTHONPATH available to the public harness. Isolation
 # still excludes unreviewed global site packages and all root verifier state.
 sys.path.insert(0,'/opt/ttgl/python')
 channel=os.fdopen(os.dup(sys.stdout.fileno()),'w',buffering=1);sys.stdout=sys.stderr
 init=json.loads(sys.stdin.readline());spec=importlib.util.spec_from_file_location('fuzzer','/app/workspace/fuzzer.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
 def parse(value):
  if type(value)is not str:
   channel.write(json.dumps(dict(kind='rejected'))+'\n');channel.flush();reply=json.loads(sys.stdin.readline());raise TypeError('fuzz inputs must be str')
  channel.write(json.dumps(dict(kind='input',value=value))+'\n');channel.flush();reply=json.loads(sys.stdin.readline())
  if reply.get('error')=='TimeoutError':raise TimeoutError()
  return None
 try:mod.fuzz(parse,grammar_text=init['grammar_text'],target_name=init['target_name'])
 except TimeoutError:pass
 except Exception as error:channel.write(json.dumps(dict(kind='error',message=type(error).__name__+': '+str(error)[:500]))+'\n');channel.flush()
 channel.write(json.dumps(dict(kind='done'))+'\n');channel.flush()
if __name__=='__main__':main()
