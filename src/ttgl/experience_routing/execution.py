"""Owned offline Docker actors and pristine public-check workers, no auto installs."""
from __future__ import annotations
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
from .io import digest,file_digest,write_new,inside
from .checkpoints import manifest


def docker(*args,timeout=120,input=None):
    result=subprocess.run(['docker',*map(str,args)],input=input,stdout=subprocess.PIPE,stderr=subprocess.PIPE,timeout=timeout)
    if result.returncode:raise RuntimeError('Owned Docker operation failed: '+result.stderr.decode(errors='replace')[-1000:])
    return result.stdout


def approve_image(image,receipt):
    if not image.startswith('sha256:') or receipt.get('image_id')!=image or receipt.get('approved') is not True:
        raise ValueError('Actor image needs an exact approved local image receipt')
    if receipt.get('findings') or receipt.get('publisher_compromised'):
        raise ValueError('Known vulnerability or publisher compromise blocks this actor image')
    observed=json.loads(docker('image','inspect',image))[0]
    if observed['Id']!=image:raise ValueError('Actor image differs from the frozen reviewed artifact')
    return observed


def source_tar(root):
    state=manifest(root);stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w') as tar:
        for key,row in state['files'].items():
            info=tarfile.TarInfo(key);info.mode=row['mode'];info.mtime=0
            if row['type']=='symlink':info.type=tarfile.SYMTYPE;info.linkname=row['target'];tar.addfile(info)
            else:
                data=(Path(root)/key).read_bytes();info.size=len(data);tar.addfile(info,io.BytesIO(data))
    return stream.getvalue()


def unpack_public_source(raw,destination):
    destination=Path(destination)
    if len(raw)>270*1024*1024:raise ValueError('Actor source export exceeds checkpoint byte bound')
    with tarfile.open(fileobj=io.BytesIO(raw)) as tar:
        members=[m for m in tar if m.name not in ('.','./')]
        for m in members:
            key=m.name.removeprefix('./')
            if '.git' in Path(key).parts or not(m.isfile() or m.issym() or m.isdir()):raise ValueError('Unsafe actor source export')
            inside(destination,key)
            if m.issym() and (Path(m.linkname).is_absolute() or not ((destination/key).parent/m.linkname).resolve().is_relative_to(destination.resolve())):
                raise ValueError('Actor source link escapes')
        for p in destination.iterdir():
            if p.name=='.git':continue
            if p.is_dir() and not p.is_symlink():shutil.rmtree(p)
            else:p.unlink()
        for m in sorted(members,key=lambda x:x.issym()):
            key=m.name.removeprefix('./');path=inside(destination,key)
            if m.isdir():path.mkdir(parents=True,exist_ok=True);continue
            path.parent.mkdir(parents=True,exist_ok=True)
            if m.issym():path.symlink_to(m.linkname)
            else:path.write_bytes(tar.extractfile(m).read());path.chmod(m.mode&0o777)
    return manifest(destination)


class DockerWorkspace:
    fixture_only=False
    def __init__(self,*,image,review,root,identity,base_commit,memory_bytes=2*1024**3,cpus=1):
        approve_image(image,review)
        self.image=image;self.root=Path(root);self.base=base_commit
        self.name='ttgl-worker-'+digest(identity)[:24]
        self.memory=memory_bytes;self.cpus=cpus;self.created=False
        self.root.mkdir(parents=True,exist_ok=True)
        if (self.root/'actor-started.json').exists():raise ValueError('Actor identity already owned; reconcile instead of replacing')

    def _create(self,name):
        # No host filesystem/credential/evaluator mounts. Only bounded ephemeral
        # source/tmp mounts are writable; the reviewed runtime stays read-only.
        docker('create','--name',name,'--network','none','--cap-drop','ALL','--security-opt','no-new-privileges',
          '--read-only','--user','1000:1000','--pids-limit','128','--memory',str(self.memory),'--cpus',str(self.cpus),
          '--tmpfs','/testbed:rw,nosuid,nodev,size=536870912,uid=1000,gid=1000',
          '--tmpfs','/tmp:rw,nosuid,nodev,size=134217728,uid=1000,gid=1000',
          '--env','HOME=/tmp/home','--workdir','/testbed','--label','observatory.experience=true',
          '--entrypoint','sleep',self.image,'infinity')
        try:
            docker('start',name)
            info=json.loads(docker('inspect',name))[0]
            if info['HostConfig']['NetworkMode']!='none' or info['Mounts']:
                # Docker lists tmpfs in HostConfig.Tmpfs, not host-backed Mounts.
                raise ValueError('Actor has unexpected network or host-backed mounts')
            return info
        except BaseException:
            docker('rm','-f',name)
            raise

    def start(self,workspace):
        write_new(self.root/'actor-started.json',{'container':self.name,'image':self.image,'base_commit':self.base})
        info=self._create(self.name);self.created=True
        self.before_attempt(workspace)
        canary='/tmp/observatory-isolation-sentinel-'+digest(self.name)[:12]
        Path(canary).write_text('Host-only boundary witness')
        try:
            probe=docker('exec',self.name,'sh','-c',f'test ! -e {canary} && test ! -e /root/.codex/auth.json && test ! -e /tests/test.sh && test ! -e /solution/solve.sh')
            write_new(self.root/'runtime-isolation.json',{'container':self.name,'image':self.image,'host_mounts':info['Mounts'],
                'network':'none','root_read_only':True,'user':'1000:1000','host_canary_hidden':True,'private_grader_paths_hidden':True,
                'native_client_home':'fresh source-bound private home outside actor','native_memory':'empty per invocation','limited_check':True})
        finally:Path(canary).unlink(missing_ok=True)
        return self.name

    def before_attempt(self,workspace):
        archive=source_tar(workspace)
        docker('exec',self.name,'sh','-c','find /testbed -mindepth 1 -maxdepth 1 -exec rm -rf {} +')
        docker('exec','-i',self.name,'tar','-xf','-','-C','/testbed',input=archive)

    def after_attempt(self,workspace):
        raw=docker('exec',self.name,'tar','--exclude=.git','-cf','-','-C','/testbed','.')
        return unpack_public_source(raw,workspace)

    def public_check(self,argv,workspace,timeout):
        name='ttgl-worker-'+digest([self.name,'verify',os.urandom(16).hex()])[:24]
        created=False
        try:
            self._create(name);created=True
            docker('exec','-i',name,'tar','-xf','-','-C','/testbed',input=source_tar(workspace))
            result=subprocess.run(['docker','exec',name,*argv],stdout=subprocess.PIPE,stderr=subprocess.STDOUT,timeout=timeout)
            return {'returncode':result.returncode,'output':result.stdout.decode(errors='replace'),'infrastructure_error':False,
                    'pristine_image':self.image,'agent_runtime_changes_excluded':True}
        except (OSError,RuntimeError,subprocess.TimeoutExpired) as error:
            return {'returncode':None,'output':type(error).__name__,'infrastructure_error':True}
        finally:
            if created:docker('rm','-f',name)

    def close(self):
        if self.created:docker('rm','-f',self.name);self.created=False
