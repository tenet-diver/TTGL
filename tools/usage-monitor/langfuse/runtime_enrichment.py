"""Native reported runtime and conservative operation labels; never executes commands."""
import math,re,shlex
from pathlib import PurePosixPath

PROGRAMS=set('rg grep find cat sed head tail ls git pytest py.test python python3 node npm npx pnpm yarn docker swift xcodebuild cargo go curl wget sleep ps stat wc du df zstd codex bash sh zsh make cmake ninja tsc vitest jest'.split())

def native_ns(value):
 # The retained Codex item.duration is a Rust Duration, not epoch milliseconds.
 if not isinstance(value,dict):return None
 secs,nanos=value.get('secs'),value.get('nanos')
 if not isinstance(secs,int) or isinstance(secs,bool) or not isinstance(nanos,int) or isinstance(nanos,bool):return None
 if secs<0 or not 0<=nanos<1_000_000_000:return None
 return secs*1_000_000_000+nanos

def command_segments(command):
 words=command if isinstance(command,list) else None
 if words and PurePosixPath(str(words[0])).name not in ['bash','sh','zsh']:return [[str(x) for x in words]]
 if words and PurePosixPath(str(words[0])).name in ['bash','sh','zsh']:
  for idx,w in enumerate(words[1:],1):
   if str(w).startswith('-') and 'c' in str(w) and idx+1<len(words):command=str(words[idx+1]);break
 else:command=' '.join(map(str,words)) if words else str(command or '')
 # Ignore here-document bodies, but retain subsequent shell commands. If
 # quoted multi-line syntax is ambiguous, shlex fails and we keep it unclassified.
 text=str(command)
 if len(text)>65536:return []
 kept=[];terminator=None
 for line in text.splitlines():
  if terminator:
   if line.strip()==terminator:terminator=None
   continue
  if line.strip().endswith('\\'):return []
  kept.append(line)
  match=re.search(r"<<-?\s*['\"]?([A-Za-z_][A-Za-z0-9_]*)['\"]?",line)
  if match:terminator=match.group(1)
 if terminator:return []
 first=' ; '.join(kept)
 try:
  lexer=shlex.shlex(first,posix=True,punctuation_chars=';&|');lexer.whitespace_split=True;tokens=list(lexer)
 except ValueError:return []
 groups=[];group=[]
 for token in tokens:
  if token and set(token)<=set(';&|'):
   if group:groups.append(group);group=[]
  else:group.append(token)
 if group:groups.append(group)
 return groups

def shell_operation(item):
 operations=[]
 for words in command_segments(item.get('command')):
  while words and (re.fullmatch(r'[A-Za-z_][A-Za-z0-9_]*=.*',words[0]) or words[0] in ['env','time','nohup']):words=words[1:]
  if not words:continue
  prog=PurePosixPath(words[0]).name;args=words[1:]
  if prog=='cd':continue
  if prog not in PROGRAMS:operations.append('other commands');continue
  if prog in ['rg','grep','find']:op='search ('+prog+')'
  elif prog in ['cat','sed','head','tail','ls','stat','wc','du','df']:op=('file writes' if any(a.startswith('>') for a in args) else 'file inspection')+' ('+prog+')'
  elif prog in ['pytest','py.test','jest','vitest'] or prog in ['python','python3'] and len(args)>=2 and args[:2]==['-m','pytest']:op='tests ('+('pytest' if prog in ['python','python3'] else prog)+')'
  elif prog=='xcodebuild':op=('tests' if any(a in ['test','test-without-building','build-for-testing'] for a in args) else 'build')+' (xcodebuild)'
  elif prog in ['npm','pnpm','yarn']:
   action=args[1] if len(args)>1 and args[0]=='run' else args[0] if args else ''
   group='tests' if action in ['test','test:unit','test:integration','vitest','jest'] else 'build' if action in ['build','compile','typecheck'] else 'dev servers' if action in ['dev','start','serve','preview'] else 'dependency install' if action in ['install','ci','add','update'] else 'package commands'
   op=group+' ('+prog+')'
  elif prog in ['cargo','go','swift'] and args and args[0] in ['test','build','run']:op={'test':'tests','build':'build','run':'program run'}[args[0]]+' ('+prog+')'
  elif prog in ['make','cmake','ninja','tsc']:op='build ('+prog+')'
  elif prog=='git':
   clean=[];skip=False
   for a in args:
    if skip:skip=False;continue
    if a in ['-C','--git-dir','--work-tree']:skip=True;continue
    if not a.startswith('-'):clean.append(a)
   action=clean[0] if clean else ''
   op='git '+action if action in ['status','diff','log','show','fetch','pull','push','commit','checkout','switch','worktree','clone','add'] else 'git other'
  elif prog in ['curl','wget']:op='network requests ('+prog+')'
  elif prog=='sleep':op='intentional wait (sleep)'
  elif prog=='ps':op='process inspection (ps)'
  elif prog in ['python','python3']:op='python inline scripts' if '-' in args or '-c' in args else 'python scripts'
  elif prog=='node':op='node inline scripts' if '-e' in args or '--eval' in args else 'node programs'
  elif prog=='docker':op='container commands'
  else:op='program run ('+prog+')'
  if op not in operations:operations.append(op)
 # Multi-command batches have one shared duration; do not allocate it to each part.
 if len(operations)>1:return 'batch: '+' + '.join(operations[:3])+(' + other' if len(operations)>3 else '')
 if operations:return operations[0]
 return 'unclassified shell'

def operation(item,name):
 if item.get('type')=='CommandExecution':return 'shell / '+shell_operation(item)
 suffix=name.rsplit('.',1)[-1]
 if 'thread' in suffix:
  labels={'list_threads':'Chats / list','read_thread':'Chats / read','wait_threads':'Chats / intentional wait','create_thread':'Chats / create','send_message_to_thread':'Chats / send message','wait_thread':'Chats / intentional wait'}
  return labels.get(suffix,'Chats / '+suffix)
 return name

def spans(meta,records,make_span):
 for r in records:
  duration=r.get('native_runtime_ns')
  if duration is None:continue
  sid=meta['id'];key='native-runtime-v2:'+sid+':'+r['id'];outcome='failed' if r['failed'] is True else 'completed' if r['failed'] is False else 'unknown outcome'
  md={'record_kind':'native_runtime','timing_basis':'item.duration (recorded runtime)','operation':r.get('operation',r['name']),'underlying_tool':r['name'],'outcome':outcome,'failed':r['failed'],'native_runtime_seconds':duration/1e9,'event_window_seconds':(r['end']-r['start'])/1e9 if r['timing_known'] else None,'start_is_reconstructed':True,'source_line':r['line'],'token_attribution':'not_measured','argument_pattern':r['argument_pattern'],'scope':'process/tool runtime, not agent-blocking or end-to-end task time','trace_name':'Native operation runtime'}
  yield make_span(key,key,md['operation']+' · '+outcome,'tool',r['end']-duration,r['end'],'usage-runtime-v2',md,sid)
