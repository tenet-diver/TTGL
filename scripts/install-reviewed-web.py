#!/usr/bin/env python3
"""Materialize the audited npm lock without running package-manager/lifecycle code.

The available npm distributions contain known advisory matches. This deliberately
small installer supports this repository's lock v3 registry packages/workspace
links only. It verifies the dated review and every archive before extraction.
"""
import base64,concurrent.futures,hashlib,io,json,os,platform,tarfile,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def main():
    receipt=json.loads((ROOT/'docs/security/next-stack-20261115.json').read_text())
    lock_path=ROOT/'package-lock.json';lock=json.loads(lock_path.read_text())
    if hashlib.sha256(lock_path.read_bytes()).hexdigest()!=receipt['lock_sha256'] or receipt['npm_audit_findings']!=0:raise SystemExit('Review the changed dependency graph before installation')
    approved={(p['name'],p['version']):p['integrity'] for p in receipt['packages']}
    candidates=[(path,pkg) for path,pkg in lock['packages'].items() if pkg.get('version') and str(pkg.get('resolved','')).startswith('https://registry.npmjs.org/')]
    current_os={'Linux':'linux','Darwin':'darwin','Windows':'win32'}.get(platform.system(),platform.system().lower());cpu={'x86_64':'x64','aarch64':'arm64'}.get(platform.machine(),platform.machine())
    def install(item):
        path,pkg=item;name=pkg.get('name',path.split('node_modules/')[-1])
        if approved.get((name,pkg['version']))!=pkg['integrity']:raise ValueError('Unreviewed package '+name)
        if pkg.get('os') and current_os not in pkg['os'] or pkg.get('cpu') and cpu not in pkg['cpu']:return 0
        target=ROOT/path
        if not target.resolve().is_relative_to(ROOT):raise ValueError('Invalid lock target')
        raw=urllib.request.urlopen(pkg['resolved'],timeout=90).read();alg,expected=pkg['integrity'].split('-',1)
        if base64.b64encode(hashlib.new(alg,raw).digest()).decode()!=expected:raise ValueError('Integrity mismatch '+name)
        target.mkdir(parents=True,exist_ok=True)
        with tarfile.open(fileobj=io.BytesIO(raw),mode='r:gz') as archive:
            for member in archive.getmembers():
                parts=Path(member.name).parts
                if len(parts)<2:continue
                relative=Path(*parts[1:])
                if relative.is_absolute() or '..' in relative.parts or member.issym() or member.islnk():raise ValueError('Unsafe archive '+name)
                destination=target/relative
                if member.isdir():destination.mkdir(parents=True,exist_ok=True)
                elif member.isfile():
                    destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(archive.extractfile(member).read());destination.chmod(0o755 if member.mode&0o111 else 0o644)
        return 1
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:count=sum(pool.map(install,candidates))
    for path,pkg in lock['packages'].items():
        if pkg.get('link'):
            target=ROOT/path;target.parent.mkdir(parents=True,exist_ok=True)
            if not target.exists():target.symlink_to(os.path.relpath(ROOT/pkg['resolved'],target.parent),target_is_directory=True)
    bins=ROOT/'node_modules/.bin';bins.mkdir(exist_ok=True)
    for path,pkg in candidates:
        manifest=ROOT/path/'package.json'
        if not manifest.exists():continue
        package=json.loads(manifest.read_text());commands=package.get('bin',{})
        if isinstance(commands,str):commands={package['name'].split('/')[-1]:commands}
        for name,entry in commands.items():
            link=bins/name
            if not link.exists():link.symlink_to(os.path.relpath(manifest.parent/entry,bins))
    print(f'Installed {count} reviewed packages; no lifecycle scripts executed.')

if __name__=='__main__':main()
