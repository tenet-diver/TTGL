import copy
import json
from pathlib import Path
import tempfile
import threading
import unittest
import urllib.request
import urllib.error
from http.server import ThreadingHTTPServer
import test_workspace
from workspace import Handler
import steering as live
import steering_hook as hook


class SteeringTests(unittest.TestCase):
    def setUp(self):
        self.fixture=test_workspace.WorkspaceTests();self.fixture.setUp();self.addCleanup(self.fixture.directory.cleanup)
        self.store=self.fixture.store;self.clock=1800000000;self.counter=0

    def event(self,event='pre_tool',**extra):
        self.counter+=1
        return dict(session_id='live',event_id=str(self.counter),event=event,workspace='/repo',**extra)

    def receive(self,event='pre_tool',**extra):
        self.clock+=1
        return live.receive(self.store,self.event(event,**extra),self.clock)

    def test_defaults_crud_and_builtin_protection(self):
        self.assertEqual(len(live.state(self.store,clock=self.clock)['rules']),11)
        ident=live.save_rule(self.store,dict(name='No production deploy',kind='command',mode='block',config={'tool':'Bash','pattern':'deploy production'},message='Review the deployment'))['id']
        self.assertEqual(self.receive(tool='Bash',command='deploy production')['decision'],'block')
        live.save_rule(self.store,dict(id=ident,enabled=False))
        self.assertEqual(self.receive(tool='Bash',command='deploy production')['decision'],'allow')
        live.save_rule(self.store,dict(id=ident,delete=True))
        with self.assertRaises(ValueError):live.save_rule(self.store,dict(id='context',delete=True))
        with self.assertRaises(ValueError):live.save_rule(self.store,dict(name='Unsafe',message='x',config={'matcher':'regex','pattern':'(a+)+$'}))
        with self.assertRaises(ValueError):live.save_rule(self.store,dict(id='context',config={'threshold':0}))

    def test_duplicate_event_is_exactly_once_with_notes(self):
        self.receive('start')
        live.control(self.store,{'session_id':'live','note':'Please inspect the before screenshot'})
        event=self.event(tool='Bash',command='true')
        first=live.receive(self.store,event,self.clock)
        self.assertIn('Please inspect',first['messages'][0])
        self.assertEqual(live.receive(self.store,event,self.clock+5),first)
        self.assertEqual(self.receive(tool='Bash',command='true')['messages'],[])
        with self.assertRaises(ValueError):live.receive(self.store,{**event,'command':'changed'},self.clock)
        state=live.state(self.store,clock=self.clock)
        self.assertEqual(len([l for l in state['log'] if l['rule_name']=='Session note']),1)
        self.assertEqual(state['sessions'][0]['pending_notes'],0)

    def test_pause_modes_and_log_only(self):
        self.receive('start');live.control(self.store,dict(session_id='live',paused=True))
        self.assertEqual(self.receive(tool='Bash',command='true')['decision'],'ask')
        live.control(self.store,dict(session_id='live',paused=False))
        live.save_rule(self.store,dict(id='shell-exploration',mode='log'))
        r=self.receive(tool='Bash',command='cat README.md')
        self.assertEqual(r['decision'],'allow');self.assertEqual(r['messages'],[])
        self.assertEqual(r['rules'][0]['mode'],'log')

    def test_failure_loops_context_once_and_stop_checks(self):
        self.assertEqual(self.receive(context_tokens=200001)['decision'],'warn')
        self.assertEqual(self.receive(context_tokens=200001)['decision'],'allow')
        for _ in range(2):self.assertEqual(self.receive('post_tool',tool='Bash',command='pytest',failed=True)['decision'],'allow')
        result=self.receive('post_tool',tool='Bash',command='pytest',failed=True)
        self.assertIn('failure-loop',[r['rule_id'] for r in result['rules']])
        self.receive('post_tool',tool='Edit',failed=False,operation='edit')
        self.assertIn('stop-check',[r['rule_id'] for r in self.receive('stop')['rules']])
        self.receive('post_tool',tool='Bash',command='pytest',failed=False,operation='check')
        self.assertEqual(self.receive('stop')['decision'],'allow')

    def test_idle_break_and_budget_threshold_crossing(self):
        self.receive('start',cost_usd=0,task_id='one')
        self.clock+=3601
        self.assertIn('break',[r['rule_id'] for r in self.receive('prompt')['rules']])
        self.assertEqual(self.receive(cost_usd=5.1)['decision'],'ask')
        self.assertEqual(self.receive(cost_usd=5.2)['decision'],'allow')
        self.assertEqual(self.receive(cost_usd=10.1)['decision'],'ask')
        self.assertEqual(self.receive(cost_usd=10.1,task_id='two')['decision'],'allow')
        self.assertEqual(self.receive(cost_usd=15.2,task_id='two')['decision'],'ask')
        with self.assertRaises(ValueError):self.receive(cost_usd=1)
        with self.assertRaises(ValueError):self.receive(cost_usd=float('nan'))

    def test_http_auth_browser_rejection_and_same_origin_crud(self):
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler);server.store=self.store
        origin=f'http://127.0.0.1:{server.server_port}';server.allowed_hosts={f'127.0.0.1:{server.server_port}'};server.allowed_origins={origin}
        threading.Thread(target=server.serve_forever,daemon=True).start();self.addCleanup(server.server_close);self.addCleanup(server.shutdown)
        token=(self.store.data/'steering-token').read_text()
        def request(path,body,headers):
            req=urllib.request.Request(origin+path,json.dumps(body).encode(),{'Content-Type':'application/json',**headers})
            return json.load(urllib.request.urlopen(req))
        payload=self.event('start')
        with self.assertRaises(urllib.error.HTTPError) as error:request('/api/steering-hook',payload,{})
        self.assertEqual(error.exception.code,403)
        with self.assertRaises(urllib.error.HTTPError):request('/api/steering-hook',payload,{'Authorization':'Bearer '+token,'Origin':origin})
        self.assertEqual(request('/api/steering-hook',payload,{'Authorization':'Bearer '+token})['decision'],'allow')
        self.assertTrue(request('/api/live-control',{'session_id':'live','paused':True},{'Origin':origin})['ok'])
        self.assertEqual(hook.send(self.store.data,origin,self.event(tool='Bash',command='true'))['decision'],'ask')

    def test_claude_install_backup_uninstall_and_mapping(self):
        settings=Path(self.fixture.root)/'claude/settings.json';settings.parent.mkdir();settings.write_text(json.dumps({'hooks':{'Stop':[{'hooks':[{'type':'command','command':'my-existing-hook'}]}]},'other':'keep'}))
        hook.configure(settings,self.store.data,'http://127.0.0.1:8766')
        hook.configure(settings,self.store.data,'http://127.0.0.1:8766')
        installed=json.loads(settings.read_text());self.assertEqual(installed['other'],'keep');self.assertEqual(len(installed['hooks']['PreToolUse']),1)
        self.assertEqual(len(list(settings.parent.glob('*.ttgl-backup-*'))),2)
        hook.configure(settings,self.store.data,'http://127.0.0.1:8766',True)
        self.assertEqual(json.loads(settings.read_text())['hooks']['Stop'][0]['hooks'][0]['command'],'my-existing-hook')
        self.assertNotIn(hook.MARK,settings.read_text())
        raw={'hook_event_name':'PreToolUse','session_id':'s','tool_name':'Bash','tool_input':{'command':'cat a'},'cwd':'/repo'}
        self.assertEqual(hook.normalize(raw)['event'],'pre_tool')
        self.assertEqual(hook.claude_result(raw,{'decision':'ask','messages':['Approve']})['hookSpecificOutput']['permissionDecision'],'ask')
        self.assertEqual(hook.claude_result({'hook_event_name':'Stop','stop_hook_active':True},{'decision':'block','messages':['Review']})['systemMessage'],'Review')
