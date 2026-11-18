"""Host-owned public check catalogues; planner suggestions never become commands."""
from __future__ import annotations
import subprocess
import time
from pathlib import Path
from .io import digest,write_new,now
from .checkpoints import manifest
from .contracts import validate


class PublicVerifier:
    def __init__(self,catalog,protected_paths,root,*,executor=None):
        self.catalog=catalog;self.protected=protected_paths;self.root=Path(root)
        self.executor=executor

    def verify(self,node,attempt,workspace,*,scope='subtask',timeout=60,contract_hash=None):
        started=time.monotonic();checks=[];outputs=[]
        if timeout<=0:raise ValueError('Public verification needs positive remaining time')
        if not node['acceptanceCriteria']:raise ValueError('No public acceptance contract')
        for criterion in node['acceptanceCriteria']:
            remaining=timeout-(time.monotonic()-started)
            if remaining<=0:
                artifact=digest([attempt,scope,criterion['id'],'verification-deadline'])
                write_new(self.root/(artifact+'.json'),{'criterion':criterion['id'],'infrastructure_error':True,'reason':'Aggregate public-check deadline exhausted'})
                checks.append({'criterionId':criterion['id'],'verdict':'unknown','evidenceArtifactRefs':[artifact]})
                continue
            definition=self.catalog.get(criterion['id'])
            if not definition:
                artifact=digest([attempt,scope,criterion['id'],'missing-host-check'])
                write_new(self.root/(artifact+'.json'),{'criterion':criterion['id'],'infrastructure_error':True,'reason':'Missing host check definition'})
                checks.append({'criterionId':criterion['id'],'verdict':'unknown','evidenceArtifactRefs':[artifact]})
                continue
            command=definition['argv']
            if not isinstance(command,list) or not command or any(not isinstance(x,str) for x in command):raise ValueError('Host checks require pinned argv arrays')
            if self.executor:
                result=self.executor(command,workspace,min(remaining,definition.get('timeout_seconds',remaining)))
            else:
                # Only fixture workspaces use a host subprocess. Live adapters
                # run these definitions in a pristine, independently owned worker.
                try:
                    p=subprocess.run(command,cwd=workspace,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=min(remaining,definition.get('timeout_seconds',remaining)))
                    result={'returncode':p.returncode,'output':p.stdout.decode(errors='replace'),'infrastructure_error':False}
                except (OSError,subprocess.TimeoutExpired) as exc:
                    result={'returncode':None,'output':type(exc).__name__,'infrastructure_error':True}
            artifact=digest([attempt,scope,criterion['id'],result]);write_new(self.root/(artifact+'.json'),{'argv':command,**result})
            checks.append({'criterionId':criterion['id'],'verdict':'unknown' if result['infrastructure_error'] else 'pass' if result['returncode']==0 else 'fail','evidenceArtifactRefs':[artifact]})
            outputs.append(result)
        verdict='pass' if checks and all(c['verdict']=='pass' for c in checks) else 'fail' if any(c['verdict']=='fail' for c in checks) else 'infrastructure_error'
        identity=digest([attempt,scope,checks])
        receipt={'verificationId':identity,'workItemId':node['nodeId'],'attemptId':attempt,'scope':scope,'visibility':'runtime_public',
                 'verdict':verdict,'contractHash':contract_hash or digest(node),'verifierVersion':digest(self.catalog),
                 'repositoryStateHash':manifest(workspace)['state_hash'],'criterionResults':checks,'observedAt':now()}
        validate('verification',receipt);write_new(self.root/(identity+'.json'),receipt)
        return receipt,{'elapsed_seconds':time.monotonic()-started,'outputs':outputs}
