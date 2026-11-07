#!/usr/bin/env python3
"""Install owned live provider settings while preserving unrelated Codex TOML."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tomllib

HERE=Path(__file__).resolve().parent


def set_key(text,section,key,value):
    lines=text.splitlines(keepends=True)
    header='['+section+']' if section else None
    start=0
    if section:
        found=next((i for i,line in enumerate(lines) if line.strip()==header),None)
        if found is None:
            text=text.rstrip()+'\n\n'+header+'\n'+key+' = '+json.dumps(value)+'\n'
            tomllib.loads(text)
            return text
        start=found+1
    end=next((i for i in range(start,len(lines)) if lines[i].lstrip().startswith('[')),len(lines))
    matching=[i for i in range(start,end) if re.match(r'^\s*'+re.escape(key)+r'\s*=',lines[i])]
    rendered=key+' = '+json.dumps(value)+'\n'
    if matching:lines[matching[0]]=rendered
    else:lines.insert(end,rendered)
    result=''.join(lines);tomllib.loads(result);return result


def install(config,policy,state):
    lock=json.loads((HERE.parent/'config/headroom-subset.lock.json').read_text())
    if any(hashlib.sha256((HERE/'vendor/headroom'/name).read_bytes()).hexdigest()!=digest for name,digest in lock['vendored_files'].items()):
        raise ValueError('Vendored Headroom subset differs from reviewed source pin')
    config=config.expanduser();state.mkdir(parents=True,exist_ok=True,mode=0o700)
    original=config.read_text() if config.exists() else ''
    parsed=tomllib.loads(original)
    provider=parsed.get('model_provider')
    if provider not in (None,'openai','ttgl_capture'):
        raise ValueError('An unrelated custom default provider exists; refuse to replace it')
    settings=tomllib.loads((HERE.parent/'config/codex-provider.toml').read_text())
    base=settings['model_providers']['ttgl_capture']['base_url'].split('/compress/')[0].rstrip('/')
    base=base if policy=='off' else base+'/compress/'+policy
    text=set_key(original,'','model_provider','openai')
    text=set_key(text,'features','enable_request_compression',False)
    for key,value in {**settings['model_providers']['ttgl_capture'],'base_url':base,'request_max_retries':0,'stream_max_retries':0}.items():
        text=set_key(text,'model_providers.ttgl_capture',key,value)
    # Codex 0.166 rejects a named profile file alongside its legacy table.
    for name in ('ttgl-observability', 'ttgl-capture-experimental'):
        text=re.sub(r'(?m)^\[profiles\.'+re.escape(name)+r'\]\s*\n(?:(?!\[).*(?:\n|$))*', '', text)
    for name, selected in (('ttgl-observability', 'openai'), ('ttgl-capture-experimental', 'ttgl_capture')):
        profile=config.parent/(name+'.config.toml')
        existing=profile.read_text() if profile.exists() else ''
        config.parent.mkdir(parents=True,exist_ok=True)
        profile.write_text(set_key(existing,'','model_provider',selected))
        profile.chmod(0o600)
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup=state/('codex-config-before-live-'+stamp+'.toml')
    fd=os.open(backup,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as output:output.write(original)
    config.parent.mkdir(parents=True,exist_ok=True)
    temporary=config.with_suffix('.ttgl-tmp')
    fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_TRUNC,0o600)
    with os.fdopen(fd,'w') as output:output.write(text)
    temporary.replace(config)
    result=dict(at=stamp,config=str(config),backup=str(backup),first_backup=str(sorted(state.glob('codex-config-before-live-*.toml'))[0]),policy=policy,base_url=base,
                before_sha256=hashlib.sha256(original.encode()).hexdigest(),after_sha256=hashlib.sha256(text.encode()).hexdigest(),
                scope='Built-in OpenAI default and analyst profile; capture/compression only via explicit ttgl-capture-experimental profile or codex_traced.py')
    (state/'live-codex-install.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--config',type=Path,default=Path.home()/'.codex/config.toml')
    parser.add_argument('--state',type=Path,default=HERE.parents[2]/'work/security/langfuse-stack')
    parser.add_argument('--policy',choices=['off','progress','headroom-lossless'],default='progress')
    args=parser.parse_args();install(args.config,args.policy,args.state)
