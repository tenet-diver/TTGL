"""Content snapshots include cumulative changes, untracked files, modes and links."""
from __future__ import annotations
import base64
import fnmatch
import io
import os
from pathlib import Path
import shutil
import stat
import tarfile
from .io import digest,file_digest,write_new,read,inside


def manifest(root, maximum_bytes=256*1024*1024):
    root=Path(root).resolve();rows={};size=0
    for directory,dirs,files in os.walk(root,followlinks=False):
        dirs[:]=sorted(d for d in dirs if d!='.git')
        for name in sorted([f for f in files if f!='.git']+[d for d in dirs if (Path(directory)/d).is_symlink()]):
            path=Path(directory)/name;key=path.relative_to(root).as_posix();info=path.lstat()
            if path.is_symlink():
                target=os.readlink(path)
                if Path(target).is_absolute() or not (path.parent/target).resolve().is_relative_to(root):
                    raise ValueError('Source symlink escapes the task workspace')
                rows[key]={'type':'symlink','target':target,'mode':stat.S_IMODE(info.st_mode)}
            elif path.is_file():
                size+=info.st_size
                if size>maximum_bytes:raise ValueError('Checkpoint exceeds frozen source byte limit')
                rows[key]={'type':'file','bytes':info.st_size,'sha256':file_digest(path),'mode':stat.S_IMODE(info.st_mode)}
            else:raise ValueError('Unsupported source object')
    return {'files':rows,'bytes':size,'state_hash':digest(rows)}


class CheckpointStore:
    def __init__(self, root, workspace, *, base_commit, environment_digest, maximum_bytes=256*1024*1024):
        self.root=Path(root).resolve();self.workspace=Path(workspace).resolve()
        project=Path(__file__).resolve().parents[3]
        if self.workspace==project or project.is_relative_to(self.workspace) or self.workspace==Path.home():
            raise ValueError('Refuse to checkpoint/restore a shared project or home')
        if self.root.is_relative_to(self.workspace):raise ValueError('Checkpoint evidence cannot live inside actor workspace')
        self.base=base_commit;self.environment=environment_digest;self.maximum_bytes=maximum_bytes
        self.root.mkdir(parents=True,exist_ok=True)
        owner=self.root/'workspace-owner.json'
        value={'workspace':str(self.workspace),'base_commit':base_commit,'environment':environment_digest}
        if owner.exists():
            if read(owner)!=value:raise ValueError('Checkpoint store belongs to another workspace')
        else:write_new(owner,value)

    def capture(self, task, node, contract, dependency_artifacts=(), tool_hash=None,context_hash=None):
        before=manifest(self.workspace,self.maximum_bytes)
        identity=digest([task,node,before['state_hash'],digest(contract),list(dependency_artifacts)])
        folder=self.root/identity
        if folder.exists():
            saved=read(folder/'manifest.json')
            if saved['repositoryStateHash']!=before['state_hash']:raise ValueError('Checkpoint identity conflict')
            return saved
        folder.mkdir()
        archive=folder/'source.tar'
        with tarfile.open(archive,'x') as tar:
            for key,row in before['files'].items():
                info=tarfile.TarInfo(key);info.mode=row['mode'];info.mtime=0
                if row['type']=='symlink':info.type=tarfile.SYMTYPE;info.linkname=row['target'];tar.addfile(info)
                else:
                    data=(self.workspace/key).read_bytes();info.size=len(data);tar.addfile(info,io.BytesIO(data))
        after=manifest(self.workspace,self.maximum_bytes)
        if after!=before:raise ValueError('Source changed during checkpoint capture')
        value={'checkpointId':identity,'taskInstanceId':task,'planNodeId':node,'baseCommit':self.base,
               'repositoryStateHash':before['state_hash'],'contractHash':digest(contract),
               'environmentDigest':self.environment,'sourceManifestHash':digest(before),
               'artifactArchiveId':file_digest(archive),'dependencyArtifactIds':list(dependency_artifacts),
               'toolConfigurationHash':tool_hash or digest({}),'visibleContextHash':context_hash or digest({}),
               'source_manifest':before,'archive_path':str(archive)}
        write_new(folder/'manifest.json',value)
        return value

    def restore(self,checkpoint):
        folder=self.root/checkpoint['checkpointId'];saved=read(folder/'manifest.json')
        archive=folder/'source.tar'
        if saved!=checkpoint or file_digest(archive)!=checkpoint['artifactArchiveId']:
            raise ValueError('Checkpoint artifact or manifest changed')
        # Inspect all members before changing the owned workspace.
        with tarfile.open(archive) as audit:
            members=audit.getmembers()
            if len(members)!=len(saved['source_manifest']['files']) or {m.name for m in members}!=set(saved['source_manifest']['files']):raise ValueError('Archive source membership changed')
            for m in members:
                if not m.isfile() and not m.issym():raise ValueError('Unsafe checkpoint member')
                if '.git' in Path(m.name).parts or Path(m.name).is_absolute() or '..' in Path(m.name).parts:raise ValueError('Unsafe checkpoint path')
                if m.issym() and (Path(m.linkname).is_absolute() or not (self.workspace/m.name).parent.joinpath(m.linkname).resolve().is_relative_to(self.workspace)):raise ValueError('Unsafe checkpoint link')
        # Existing task Git identity remains; only this owned source tree changes.
        for p in self.workspace.iterdir():
            if p.name=='.git':continue
            if p.is_dir() and not p.is_symlink():shutil.rmtree(p)
            else:p.unlink()
        with tarfile.open(archive) as tar:
            members=tar.getmembers()
            if set(m.name for m in members)!=set(saved['source_manifest']['files']):
                raise ValueError('Archive source membership changed')
            # Regular files first, then validated links; never follow source links
            # while writing an extracted file or restore device/hardlink entries.
            for m in members:
                if not m.isfile() and not m.issym():raise ValueError('Unsafe checkpoint member')
                if '.git' in Path(m.name).parts:raise ValueError('Checkpoint cannot replace Git ownership')
            for m in sorted(members,key=lambda x:x.issym()):
                target=inside(self.workspace,m.name);target.parent.mkdir(parents=True,exist_ok=True)
                if m.issym():
                    link=m.linkname
                    if Path(link).is_absolute() or not (target.parent/link).resolve().is_relative_to(self.workspace):raise ValueError('Unsafe source link')
                    target.symlink_to(link)
                else:
                    target.write_bytes(tar.extractfile(m).read());target.chmod(m.mode&0o777)
        if manifest(self.workspace,self.maximum_bytes)!=saved['source_manifest']:
            raise ValueError('Restored source/dependency hashes differ')
        return saved

    def admissible(self,checkpoint,allowed_paths,protected_paths):
        before=checkpoint['source_manifest']['files'];after=manifest(self.workspace,self.maximum_bytes)['files']
        changes=[p for p in sorted(set(before)|set(after)) if before.get(p)!=after.get(p)]
        def matches(path,pattern):
            return path==pattern or (pattern.endswith('/') and path.startswith(pattern)) or fnmatch.fnmatchcase(path,pattern)
        invalid=[p for p in changes if '.git' in Path(p).parts or any(matches(p,x) for x in protected_paths) or not any(matches(p,x) for x in allowed_paths)]
        return {'passed':not invalid,'changed_paths':changes,'invalid_paths':invalid,
                'repository_state_hash':digest(after),'includes_adds_deletes_modes_and_links':True}


def replay_snapshot(checkpoint,destination):
    """Source-only independent replay into a new empty evaluator workspace."""
    target=Path(destination)
    if target.exists() and any(target.iterdir()):raise ValueError('Independent replay requires an empty destination')
    target.mkdir(parents=True,exist_ok=True)
    archive=Path(checkpoint['archive_path'])
    if file_digest(archive)!=checkpoint['artifactArchiveId']:raise ValueError('Sealed source archive changed')
    with tarfile.open(archive) as tar:
        members=tar.getmembers()
        if {m.name for m in members}!=set(checkpoint['source_manifest']['files']):raise ValueError('Artifact membership differs')
        for m in members:
            if not m.isfile() and not m.issym():raise ValueError('Unsafe replay member')
            inside(target,m.name)
        for m in sorted(members,key=lambda x:x.issym()):
            path=inside(target,m.name);path.parent.mkdir(parents=True,exist_ok=True)
            if m.issym():
                if Path(m.linkname).is_absolute() or not (path.parent/m.linkname).resolve().is_relative_to(target.resolve()):raise ValueError('Replay link escapes')
                path.symlink_to(m.linkname)
            else:path.write_bytes(tar.extractfile(m).read());path.chmod(m.mode&0o777)
    if manifest(target)!=checkpoint['source_manifest']:raise ValueError('Independent replay source differs')
    return target
