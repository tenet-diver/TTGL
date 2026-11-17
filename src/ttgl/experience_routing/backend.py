"""Retained Codex transport over existing parser and isolated worker command builder.

Credentials stay in a private fresh client home, outside the unmounted actor.
The canonical source binding remains the authority. No API key/provider fallback.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import time
from dataclasses import replace
from ..personal import CodexBackend,parse_codex_events
from .io import file_digest,read,write_new,digest


def source_binding(home):
    home=Path(home).resolve(strict=True);auth=read(home/'auth.json')
    if auth.get('auth_mode')!='chatgpt' or auth.get('OPENAI_API_KEY') or any(not auth.get('tokens',{}).get(k) for k in ('account_id','access_token','refresh_token')):
        raise ValueError('Canonical source ChatGPT subscription required; API-key billing disabled')
    import hashlib
    return {'codex_home':str(home),'account_hash':hashlib.sha256(auth['tokens']['account_id'].encode()).hexdigest(),'auth_mode':'chatgpt'}


class RecordedCodexBackend(CodexBackend):
    fixture_only=False
    def __init__(self, *, executable, executable_sha256, source_home, source_account_hash, output, client, container=None, node_executable=None):
        super().__init__(executable)
        if file_digest(Path(executable).resolve())!=executable_sha256:
            raise ValueError('Codex executable differs from the audited pin')
        self.binding=source_binding(source_home)
        if self.binding['account_hash']!=source_account_hash:raise ValueError('Source subscription identity changed')
        self.output=Path(output);self.client=client;self.container=container;self.node_executable=node_executable
        self.artifacts={};self.last_response_ids=[];self.rollout_artifacts=[]

    def command(self,request,schema):
        if not request.read_only:
            if not self.container or not self.node_executable:raise ValueError('Executor requires an isolated owned worker')
            # Same tool boundary as isolated.ContainerBackend, without importing
            # its unrelated NumPy/benchmark stack. Existing MCP server is reused.
            server=Path(__file__).resolve().parents[3]/'tools/worker-mcp/server.mjs'
            command=[self.executable,'exec','--json','--ignore-user-config','--ignore-rules','--skip-git-repo-check',
                     '--model',request.model,'--cd',str(request.workspace),'--output-schema',str(schema)]
            for feature in ('shell_tool','unified_exec','multi_agent','plugins','apps','browser_use','computer_use','image_generation','workspace_dependencies','view_image'):
                command+=['--disable',feature]
            settings={'approval_policy':'never','web_search':'disabled','project_doc_max_bytes':0,
                      'model_reasoning_effort':request.reasoning_effort,'default_permissions':'observatory-experience',
                      'permissions.observatory-experience.network.enabled':False,'features.skip_host_skill_discovery':True,
                      'mcp_servers.worker.command':self.node_executable,'mcp_servers.worker.args':[str(server),self.container],
                      'mcp_servers.worker.tool_timeout_sec':130,'mcp_servers.worker.enabled_tools':['shell'],
                      'mcp_servers.worker.tools.shell.approval_mode':'approve'}
            for key,value in settings.items():command+=['--config',key+'='+json.dumps(value)]
            command+=['--config','permissions.observatory-experience.filesystem={":root"="deny",":minimal"="read"}','-']
        else:
            command=[self.executable,'exec','--json','--ignore-user-config','--ignore-rules','--skip-git-repo-check','--ephemeral',
                     '--cd',str(request.workspace),'--model',request.model,'--sandbox','read-only','--output-schema',str(schema)]
            for feature in ('shell_tool','unified_exec','multi_agent','plugins','apps','browser_use','computer_use','image_generation','workspace_dependencies','view_image'):
                command+=['--disable',feature]
            command+=['--config','project_doc_max_bytes=0','--config','web_search="disabled"',
                      '--config','model_reasoning_effort='+json.dumps(request.reasoning_effort),'-']
        # Options must precede stdin's '-' marker; all initial requests are fresh.
        if command[-1]=='-':command.pop()
        for setting in ('model_provider="openai"','forced_login_method="chatgpt"','cli_auth_credentials_store="file"',
                        'model_providers.openai.request_max_retries=0','model_providers.openai.stream_max_retries=0'):
            command+=['--config',setting]
        return command+['-']

    def complete(self,request):
        if request.thread_id is not None:raise ValueError('Each registered attempt starts a fresh model thread')
        current=source_binding(self.binding['codex_home'])
        if current!=self.binding:raise ValueError('Canonical source authentication changed')
        folder=self.output/request.request_id;folder.mkdir(parents=True,exist_ok=False,mode=0o700)
        home=folder/'client-home';home.mkdir(mode=0o700)
        shutil.copyfile(Path(self.binding['codex_home'])/'auth.json',home/'auth.json');(home/'auth.json').chmod(0o600)
        schema=folder/'schema.json';write_new(schema,request.schema)
        write_new(folder/'source-binding.json',self.binding)
        prompt=request.prompt
        if not request.read_only:prompt+='\nUse only the assigned worker MCP shell for repository actions. The task repository is /testbed in that worker. No host files or network are available.'
        prompt_file=folder/'prompt.txt';prompt_file.write_text(prompt);prompt_file.chmod(0o600)
        self.client.retain_file(prompt_file,kind='model-request',identity=request.request_id+':prompt')
        allowed=('PATH','LANG','LC_ALL','SSL_CERT_FILE','SSL_CERT_DIR','HTTPS_PROXY','HTTP_PROXY','ALL_PROXY','NO_PROXY','https_proxy','http_proxy','all_proxy','no_proxy')
        env={k:os.environ[k] for k in allowed if k in os.environ};env.update(CODEX_HOME=str(home),HOME=str(home))
        stdout=folder/'events.jsonl';stderr=folder/'stderr.log';started=time.monotonic();timed_out=False
        try:
            with stdout.open('xb') as out,stderr.open('xb') as err:
                os.chmod(stdout,0o600);os.chmod(stderr,0o600)
                process=subprocess.Popen(self.command(request,schema),stdin=subprocess.PIPE,stdout=out,stderr=err,
                                         cwd=request.workspace,env=env,start_new_session=True)
                try:process.communicate(prompt.encode(),timeout=request.timeout_seconds)
                except subprocess.TimeoutExpired:
                    timed_out=True
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    process.wait()
                except BaseException:
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    process.wait()
                    raise
            self.last_response_ids=[]
            for p in (home/'sessions').rglob('*.jsonl') if (home/'sessions').exists() else []:
                with p.open() as lines:
                    for line in lines:
                        try:r=json.loads(line)
                        except ValueError:continue
                        if r.get('type')=='token_usage_record' and r.get('payload',{}).get('response_id'):
                            self.last_response_ids.append(r['payload']['response_id'])
                retained=self.client.retain_file(p,kind='native-rollout',identity=request.request_id+':'+p.name)
                self.rollout_artifacts.append(retained)
            for path in (stdout,stderr,schema):
                self.artifacts[path.name]=self.client.retain_file(path,kind='native-'+path.name,identity=request.request_id+':'+path.name)
            self.last_native_artifact_hash=file_digest(stdout)
            response=parse_codex_events(stdout.read_text(errors='replace').splitlines(),returncode=process.returncode)
            response.elapsed_seconds=time.monotonic()-started
            if timed_out:response.status='timeout';response.error_type='deadline'
            return response
        finally:
            # Private spool remains on archival failure; never discard uncertain
            # evidence. Auth is credential material and is never archived.
            try:
                for evidence in (stdout,stderr):
                    if evidence.is_file() and evidence.name not in self.artifacts:
                        try:self.client.retain_file(evidence,kind='native-'+evidence.name,identity=request.request_id+':'+evidence.name)
                        except Exception:pass # Private spool remains authoritative on archival failure.
            finally:(home/'auth.json').unlink(missing_ok=True)
