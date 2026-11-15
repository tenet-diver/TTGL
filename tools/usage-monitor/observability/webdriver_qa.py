"""Opt-in W3C WebDriver client using Python stdlib; driver/runtime reviewed separately."""
import urllib.request,json,time,base64,os,socket,struct
from urllib.parse import urlparse
class Browser:
 def __init__(self,endpoint,binary):
  self.base=endpoint.rstrip('/')
  result=self.request('/session',{'capabilities':{'alwaysMatch':{'browserName':'firefox','webSocketUrl':True,'moz:firefoxOptions':{'binary':binary,'args':['-headless'],'prefs':{'datareporting.policy.dataSubmissionEnabled':False,'toolkit.telemetry.enabled':False}}}}})
  self.base+='/session/'+result['sessionId']
  self.bidi=BiDi(result['capabilities']['webSocketUrl']);self.context=self.bidi.call('browsingContext.getTree',{})['contexts'][0]['context']
 def close(self):
  try:self.request('',method='DELETE')
  finally:self.bidi.sock.close()
 def ready(self):self.wait('document.querySelector("#content")?.getAttribute("aria-busy")==="false" && document.querySelector("nav [aria-current=page]")!==null',60)
 def nav(self,view):
  self.click('nav [data-view="'+view+'"]');self.wait('document.querySelector("nav [data-view='+view+']")?.getAttribute("aria-current")==="page"',60);self.ready()
 def text(self,css):return self.js('return document.querySelector(arguments[0])?.innerText',css)
 def count(self,css):return self.js('return document.querySelectorAll(arguments[0]).length',css)
 def button(self,title,scope=''):
  eid=self.js('return [...document.querySelectorAll(arguments[0]+" button")].find(e=>(e.getAttribute("aria-label")||e.textContent.trim())===arguments[1]&&e.getClientRects().length)',scope,title)
  if not eid:raise AssertionError('No visible button '+title)
  self.request('/element/'+eid['element-6066-11e4-a52e-4f735466cecf']+'/click',{})
 def closed(self):self.wait('!document.querySelector("#modal").open')
 def request(self,path,body=None,method=None):
  req=urllib.request.Request(self.base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'},method=method)
  try:
   with urllib.request.urlopen(req,timeout=90) as response:r=json.load(response)['value']
  except urllib.error.HTTPError as e:raise RuntimeError(e.read().decode())
  if isinstance(r,dict) and r.get('error'):raise RuntimeError(r)
  return r
 def js(self,script,*args):return self.request('/execute/sync',{'script':script,'args':list(args)})
 def goto(self,url):
  marker=str(time.monotonic_ns());self.js('window.__qaNavigation=arguments[0]',marker)
  result=self.request('/refresh',{}) if self.request('/url')==url else self.request('/url',{'url':url})
  self.wait('window.__qaNavigation!=='+json.dumps(marker)+' && document.readyState==="complete"',60)
  return result
 def wait(self,script,timeout=30):
  end=time.monotonic()+timeout;last=None
  while time.monotonic()<end:
   try:
    last=self.js('return '+script)
    if last:return last
   except RuntimeError as e:last=str(e)
   time.sleep(.15)
  raise AssertionError((script,last,self.js('return document.body.innerText.slice(-3000)')))
 def element(self,css):return self.request('/element',{'using':'css selector','value':css})['element-6066-11e4-a52e-4f735466cecf']
 def click(self,css):
  eid=self.element(css)
  if self.js('return document.querySelector(arguments[0]).namespaceURI',css)=='http://www.w3.org/2000/svg':
   self.js('document.querySelector(arguments[0]).focus()',css);return self.request('/element/'+eid+'/value',{'text':'\ue007'})
  return self.request('/element/'+eid+'/click',{})
 def fill(self,css,text):
  # Atomic fill, like browser automation SDKs: typing can replace the input
  # node on every character in reactive tables, invalidating a cached element.
  self.js('const e=document.querySelector(arguments[0]);e.focus();Object.getOwnPropertyDescriptor(e.tagName==="TEXTAREA"?HTMLTextAreaElement.prototype:HTMLInputElement.prototype,"value").set.call(e,arguments[1]);e.dispatchEvent(new InputEvent("input",{bubbles:true,inputType:"insertText",data:arguments[1]}));',css,text)
 def select(self,css,value):return self.js('const e=document.querySelector(arguments[0]);e.value=arguments[1];e.dispatchEvent(new Event("change",{bubbles:true}));',css,value)
 def size(self,w,h=1000):
  self.request('/window/rect',{'width':max(550,w),'height':h});self.bidi.call('browsingContext.setViewport',{'context':self.context,'viewport':{'width':w,'height':h}})
 def shot(self,path):
  with open(path,'wb') as target:target.write(base64.b64decode(self.request('/screenshot')))

class BiDi:
 """Small synchronous transport for standard browser viewport commands."""
 def __init__(self,url):
  parsed=urlparse(url);self.sock=socket.create_connection((parsed.hostname,parsed.port),timeout=30);self.counter=0
  key=base64.b64encode(os.urandom(16)).decode();self.sock.sendall((f'GET {parsed.path} HTTP/1.1\r\nHost: {parsed.netloc}\r\nUpgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\nSec-WebSocket-Version: 13\r\n\r\n').encode())
  headers=b''
  while not headers.endswith(b'\r\n\r\n'):headers+=self.sock.recv(1)
  if not headers.startswith(b'HTTP/1.1 101'):raise RuntimeError(headers)
 def read(self,n):
  result=b''
  while len(result)<n:
   chunk=self.sock.recv(n-len(result))
   if not chunk:raise RuntimeError('WebSocket closed')
   result+=chunk
  return result
 def call(self,method,params):
  self.counter+=1;payload=json.dumps({'id':self.counter,'method':method,'params':params}).encode();mask=os.urandom(4);size=len(payload)
  header=bytes([129,128|size]) if size<126 else bytes([129,254])+struct.pack('!H',size)
  self.sock.sendall(header+mask+bytes(c^mask[i%4] for i,c in enumerate(payload)))
  while True:
   opcode,size=self.read(2);size=size&127
   if size==126:size=struct.unpack('!H',self.read(2))[0]
   elif size==127:size=struct.unpack('!Q',self.read(8))[0]
   response=json.loads(self.read(size))
   if response.get('id')==self.counter:
    if response.get('type')=='error':raise RuntimeError(response)
    return response['result']
