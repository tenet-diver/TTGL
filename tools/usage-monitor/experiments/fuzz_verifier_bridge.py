"""Root-owned verifier proxy; untrusted fuzzer executes in another UID process.

Unlike upstream same-process loading, the candidate cannot mutate the parent's
coverage or parser objects. IPC affects throughput; report adapted scores only.
"""
import json,os,selectors,subprocess,sys,time
class RemoteFuzzer:
 def fuzz(self,parse,grammar_text=None,target_name=None):
  p=subprocess.Popen([sys.executable,'-I','-S','/opt/ttgl/fuzz_worker.py'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.DEVNULL,user=1000,group=1000,extra_groups=[],bufsize=0)
  sel=selectors.DefaultSelector();sel.register(p.stdout,selectors.EVENT_READ);buf=b'';os.set_blocking(p.stdin.fileno(),False)
  try:
   initial=(json.dumps(dict(grammar_text=grammar_text,target_name=target_name))+'\n').encode()
   if os.write(p.stdin.fileno(),initial)!=len(initial):raise ValueError('Initial IPC message too large')
   while time.time()<parse._dl:
    ready=sel.select(min(.2,max(0,parse._dl-time.time())))
    if not ready:
     if p.poll() is not None:break
     continue
    data=os.read(p.stdout.fileno(),65536)
    if not data:break
    buf+=data
    if len(buf)>1048576:raise ValueError('Fuzzer protocol output limit')
    while b'\n' in buf:
     line,buf=buf.split(b'\n',1)
     try:r=json.loads(line)
     except ValueError:continue
     if not isinstance(r,dict):continue
     if r.get('kind')=='done':return
     if r.get('kind')=='error':raise RuntimeError(str(r.get('message'))[:500])
     if r.get('kind') not in ('input','rejected'):continue
     value=r.get('value') if r['kind']=='input' else None
     if r['kind']=='input' and type(value)is not str:raise TypeError('Protocol input must be plain str')
     reply={}
     try:parse(value)
     except TypeError:reply={'error':'TypeError'}
     except TimeoutError:reply={'error':'TimeoutError'}
     try:os.write(p.stdin.fileno(),(json.dumps(reply)+'\n').encode())
     except (BrokenPipeError,BlockingIOError):return
     if reply.get('error')=='TimeoutError':return
   raise TimeoutError()
  finally:
   sel.close()
   if p.poll() is None:p.kill()
   p.wait(timeout=5);p.stdin.close();p.stdout.close()
